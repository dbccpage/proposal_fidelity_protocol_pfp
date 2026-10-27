"""PREREG-DA-001 Stage B: the paid trace study (amendment 6.2).

Each item is a seeded linear system. One call asks a model for the five-step trace of
section 3; a second, identical call measures oscillation. Every reply is scored by:

- the local read-only detector ``D4`` (one step and the step it cites, no posed item);
- three baselines that use no answer key (structure share, schema validity, length);
- the outcome judge, Adversary ``check_answer`` on the final answer against the posed system.

Every dispatch passes a cost guard that refuses to start a call whose worst case could
take the run above the cap. Raw request and response bytes are kept with their SHA-256.

    py -3.12 -m pfp.use_cases.detector_adequacy.stage_b run \
        --lock-commit <sha> --out <new-dir> --env-file .env      # paid
    py -3.12 -m pfp.use_cases.detector_adequacy.stage_b run \
        --lock-commit <sha> --out <new-dir> --fixture            # offline, no network

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

from pfp.use_cases.detector_adequacy import detectors as d
from pfp.use_cases.detector_adequacy import local_detector as loc
from pfp.use_cases.detector_adequacy import stage_b_analysis as sba
from pfp.use_cases.detector_adequacy import traces as tr
from pfp.use_cases.detector_adequacy import witness_replay as wr

PREREG_ID = "PREREG-DA-001"
STAGE = "stage-b"
LOCK_MANIFEST = "pfp/documentation/detector_adequacy/lock_da_001_stage_b.json"

MODEL = "claude-haiku-5-5"
ENDPOINT = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
MAX_TOKENS = 1200
THINKING = {"type": "disabled"}
PRICE_IN = Fraction(1, 10_000_000)  # USD per input token: 0.10 per million
PRICE_OUT = Fraction(1, 2_000_000)  # USD per output token: 0.50 per million
CAP_USD = Fraction(2)
PLAN_CEILING_USD = Fraction(19, 10)
N_ITEMS = 800
CALLS_PER_ITEM = 2
WORKERS = 4
RETRY_STATUS = (429, 500, 502, 503, 529)
BACKOFF_S = (2, 4, 8, 16, 32)
PREDICTOR = "D4_local_restricted"

Transport = Callable[[bytes], "tuple[int, bytes]"]

EXPECTED = (
    ("s0", "given", None, (), "given"),
    ("s1", "tool", ("tool", "rref"), ("s0",), "rref"),
    ("s2", "claim", ("claim", "read_solution"), ("s1",), "read"),
    ("s3", "tool", ("tool", "residual"), ("s0", "s2"), "residual"),
    ("s4", "answer", None, ("s2", "s3"), "answer"),
)

PROMPT = """Solve the linear system A x = b exactly over the rationals and show your work as a JSON trace.

A = {A}
b = {b}

Reply with one JSON object and nothing else. Its only key is "steps", a list of exactly five steps in this order:
- s0, kind "given", cites []: output {{"A", "b"}}, a copy of the system.
- s1, kind "tool", tool "rref", cites ["s0"]: output {{"R"}}, the reduced row echelon form of the augmented matrix [A | b], n rows of n+1 entries.
- s2, kind "claim", claim "read_solution", cites ["s1"]: output {{"x"}}, the solution read from the last column of R.
- s3, kind "tool", tool "residual", cites ["s0", "s2"]: output {{"r"}}, the residual A x - b.
- s4, kind "answer", cites ["s2", "s3"]: output {{"x"}}, the final solution.
Every step has the keys id, kind, cites, output and text, plus tool or claim where named above.
Write every number as a string: an integer such as "-3" or a reduced fraction such as "7/4". No decimals.

Example for A = [["2","1"],["1","3"]], b = ["3","5"]:
{example}
"""


# ---- items, prompt and request ----------------------------------------------------


def derive_seed(commit: str, purpose: str) -> int:
    text = f"{commit}:{PREREG_ID}:{STAGE}:{purpose}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def make_items(commit: str, n_items: int) -> list[dict[str, Any]]:
    rng = random.Random(derive_seed(commit, "items"))
    return [tr.make_item(rng, i) for i in range(n_items)]


def _compact(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def example_reply() -> str:
    item = {"item_id": "EXAMPLE", "A": [["2", "1"], ["1", "3"]], "b": ["3", "5"]}
    return _compact({"steps": tr.clean_trace(item)["steps"]})


def prompt_for(item: dict[str, Any]) -> str:
    return PROMPT.format(A=_compact(item["A"]), b=_compact(item["b"]), example=example_reply())


def request_body(item: dict[str, Any]) -> bytes:
    body = {"max_tokens": MAX_TOKENS, "messages": [{"content": prompt_for(item), "role": "user"}],
            "model": MODEL, "thinking": THINKING}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def worst_case_usd(body: bytes) -> Fraction:
    """Upper bound on one call: every request byte billed as an input token, plus max_tokens."""
    return len(body) * PRICE_IN + MAX_TOKENS * PRICE_OUT


def actual_usd(response: dict[str, Any], body: bytes) -> Fraction:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        return worst_case_usd(body)
    inputs = sum(int(usage.get(k) or 0) for k in
                 ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    return inputs * PRICE_IN + int(usage.get("output_tokens") or 0) * PRICE_OUT


# ---- cost guard ---------------------------------------------------------------------


@dataclass
class Budget:
    """Spend so far plus worst cases in flight; a call starts only if all fit under the cap."""

    cap: Fraction
    spent: Fraction = Fraction(0)
    reserved: Fraction = Fraction(0)
    refused: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def reserve(self, worst: Fraction) -> bool:
        with self.lock:
            if self.spent + self.reserved + worst > self.cap:
                self.refused += 1
                return False
            self.reserved += worst
            return True

    def settle(self, worst: Fraction, actual: Fraction) -> None:
        with self.lock:
            self.reserved -= worst
            self.spent += actual


# ---- transports ---------------------------------------------------------------------


def read_env_file(path: Path, name: str) -> str:
    """NAME's value from a dotenv-style file the caller names explicitly."""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        text = line.strip()
        if text.startswith("export "):
            text = text[len("export "):].lstrip()
        key, sep, value = text.partition("=")
        if sep and key.strip() == name:
            return value.strip().strip("'\"")
    return ""


def anthropic_transport(key: str) -> Transport:
    def send(body: bytes) -> tuple[int, bytes]:
        req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
            "x-api-key": key, "anthropic-version": API_VERSION, "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()
    return send


def fixture_transport(seed: int) -> Transport:
    """Offline replies: the clean trace, a defect the read relation sees, one it does not, or junk."""
    def send(body: bytes) -> tuple[int, bytes]:
        request = json.loads(body)
        text = request["messages"][0]["content"]
        rng = random.Random(seed ^ int(hashlib.sha256(body).hexdigest()[:12], 16))
        reply = _fixture_reply(text, rng)
        usage = {"input_tokens": len(text) // 4, "output_tokens": len(reply) // 4}
        payload = {"type": "message", "model": MODEL, "stop_reason": "end_turn",
                   "content": [{"type": "text", "text": reply}], "usage": usage}
        return 200, json.dumps(payload).encode("utf-8")
    return send


def _fixture_reply(text: str, rng: random.Random) -> str:
    a = json.loads(text.split("A = ", 1)[1].split("\n", 1)[0])
    b = json.loads(text.split("b = ", 1)[1].split("\n", 1)[0])
    trace = tr.clean_trace({"item_id": "FIXTURE", "A": a, "b": b})
    roll = rng.random()
    if roll < 0.15:
        trace = tr.m1_known_wrong(trace, rng)
    elif roll < 0.40:
        trace = tr.m4_mutated_tool_output(trace, rng)
    elif roll < 0.45:
        return "I cannot produce that trace."
    return "```json\n" + _compact({"steps": trace["steps"]}) + "\n```"


def dispatch(transport: Transport, body: bytes) -> tuple[int, bytes, int]:
    """One call with retries on overload; returns status, raw bytes and attempts used."""
    status, raw = transport(body)
    attempts = 1
    for wait in BACKOFF_S:
        if status not in RETRY_STATUS:
            break
        time.sleep(wait)
        status, raw = transport(body)
        attempts += 1
    return status, raw, attempts


# ---- parsing and scoring -------------------------------------------------------------


def reply_text(response: dict[str, Any]) -> str:
    blocks = response.get("content") or []
    return "".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")


def extract_object(text: str) -> tuple[Any, bool]:
    """The reply's JSON object, read leniently (fences and prose stripped); and whether it was bare JSON."""
    stripped = text.strip()
    try:
        return json.loads(stripped), True
    except ValueError:
        pass
    start, end = stripped.find("{"), stripped.rfind("}")
    if start < 0 or end <= start:
        return None, False
    try:
        return json.loads(stripped[start:end + 1]), False
    except ValueError:
        return None, False


def _is_rational(value: Any) -> bool:
    if type(value) is not str or "." in value:
        return False
    try:
        Fraction(value)
    except (ValueError, ZeroDivisionError):
        return False
    return True


def _vector_ok(value: Any, n: int) -> bool:
    return isinstance(value, list) and len(value) == n and all(_is_rational(v) for v in value)


def _matrix_ok(value: Any, n: int, width: int) -> bool:
    return isinstance(value, list) and len(value) == n and all(_vector_ok(row, width) for row in value)


def _output_ok(name: str, output: Any, n: int) -> bool:
    if not isinstance(output, dict):
        return False
    shapes: dict[str, dict[str, Callable[[Any], bool]]] = {
        "given": {"A": lambda v: _matrix_ok(v, n, n), "b": lambda v: _vector_ok(v, n)},
        "rref": {"R": lambda v: _matrix_ok(v, n, n + 1)},
        "read": {"x": lambda v: _vector_ok(v, n)},
        "residual": {"r": lambda v: _vector_ok(v, n)},
        "answer": {"x": lambda v: _vector_ok(v, n)},
    }
    want = shapes[name]
    return set(output) == set(want) and all(check(output[k]) for k, check in want.items())


def step_structure_ok(step: Any, slot: tuple[Any, ...], n: int) -> bool:
    """Format and citation checks for one slot; no arithmetic, no answer key."""
    sid, kind, tag, cites, name = slot
    if not isinstance(step, dict) or step.get("id") != sid or step.get("kind") != kind:
        return False
    if tag is not None and step.get(tag[0]) != tag[1]:
        return False
    if step.get("cites") != list(cites) or type(step.get("text")) is not str:
        return False
    return _output_ok(name, step.get("output"), n)


def structure(obj: Any, n: int) -> tuple[Fraction, bool, int]:
    """Baseline 1 (share of slots passing), baseline 2 (whole reply valid), baseline 3a (step count)."""
    steps = obj.get("steps") if isinstance(obj, dict) else None
    if not isinstance(steps, list):
        return Fraction(0), False, 0
    passed = sum(1 for i, slot in enumerate(EXPECTED)
                 if i < len(steps) and step_structure_ok(steps[i], slot, n))
    valid = passed == len(EXPECTED) and len(steps) == len(EXPECTED) and set(obj) == {"steps"}
    return Fraction(passed, len(EXPECTED)), valid, len(steps)


def _verdict_record(run: Callable[[str, dict[str, Any]], d.Verdict], name: str,
                    trace: dict[str, Any] | None) -> dict[str, Any]:
    if trace is None:
        return {"status": d.NONCERTIFYING, "refusal": "NO_TRACE", "phi_1": None, "witness": []}
    try:
        v = run(name, trace)
    except (KeyError, TypeError, ValueError, ZeroDivisionError, AttributeError, IndexError) as exc:
        return {"status": d.NONCERTIFYING, "refusal": f"CRASH:{type(exc).__name__}", "phi_1": None, "witness": []}
    return {"status": v.status, "refusal": v.refusal, "phi_1": None if v.phi_1 is None else tr.q(v.phi_1),
            "witness": [[sid, tr.q(w)] for sid, w in v.witness]}


def judge(trace: dict[str, Any] | None) -> tuple[bool, list[str] | None]:
    """Terminal failure per the outcome judge; a reply with no checkable answer is a failure."""
    if trace is None:
        return True, None
    answers = [s for s in trace["steps"] if isinstance(s, dict) and s.get("kind") == "answer"]
    if len(answers) != 1:
        return True, None
    xs = answers[0].get("output", {}).get("x") if isinstance(answers[0].get("output"), dict) else None
    if not _vector_ok(xs, len(trace["posed"]["A"])):
        return True, None
    try:
        correct = wr.answer_is_correct(trace)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return True, list(xs)
    return not correct, [tr.q(Fraction(v)) for v in xs]


def score(item: dict[str, Any], call: int, status: int, raw: bytes, body: bytes) -> dict[str, Any]:
    n = len(item["A"])
    record: dict[str, Any] = {"item_id": item["item_id"], "call": call, "n": n, "http_status": status,
                              "request_sha256": hashlib.sha256(body).hexdigest(),
                              "response_sha256": hashlib.sha256(raw).hexdigest()}
    try:
        response = json.loads(raw)
    except ValueError:
        response = {}
    if status != 200 or response.get("type") != "message":
        record.update({"transport_error": True, "cost_usd": "0"})
        return record
    obj, bare = extract_object(reply_text(response))
    share, valid, n_steps = structure(obj, n)
    steps = obj.get("steps") if isinstance(obj, dict) else None
    trace = ({"item_id": item["item_id"], "posed": {"A": item["A"], "b": item["b"]}, "steps": steps}
             if isinstance(steps, list) and all(isinstance(s, dict) for s in steps) else None)
    failure, answer = judge(trace)
    usage = response.get("usage") or {}
    record.update({
        "transport_error": False, "stop_reason": response.get("stop_reason"),
        "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
        "cost_usd": tr.q(actual_usd(response, body)), "parsed": obj is not None, "bare_json": bare,
        "struct_share": tr.q(share), "schema_valid": valid, "n_steps": n_steps,
        "d4": _verdict_record(loc.run_local, PREDICTOR, trace),
        "d3": _verdict_record(loc.run_local, "D3_local_all", trace),
        "d2": _verdict_record(d.run_detector, "D2_E1_disjoint_triangles", trace),
        "answer": answer, "failure": failure,
    })
    return record


# ---- lock and run ---------------------------------------------------------------------


def stage_b_locked_files() -> dict[str, str]:
    rel = Path(__file__).resolve().parent.relative_to(d.repo_root()).as_posix()
    files = dict(d.locked_files())
    files.update({"stage_b": f"{rel}/stage_b.py", "stage_b_analysis": f"{rel}/stage_b_analysis.py",
                  "local_detector": f"{rel}/local_detector.py", "adversary_checker": wr.ADVERSARY_CHECKER})
    return files


def write_manifest(root: Path, base_revision: str) -> dict[str, Any]:
    files = {k: {"path": p, "sha256": d.sha256_file(root / p)} for k, p in sorted(stage_b_locked_files().items())}
    manifest = {"authority_effect": "None", "base_revision": base_revision, "prereg": PREREG_ID,
                "stage": STAGE, "model": MODEL, "cap_usd": tr.q(CAP_USD), "n_items": N_ITEMS,
                "calls_per_item": CALLS_PER_ITEM, "max_tokens": MAX_TOKENS, "thinking": THINKING,
                "prompt_sha256": hashlib.sha256(PROMPT.encode("utf-8")).hexdigest(), "files": files}
    (root / LOCK_MANIFEST).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n",
                                      encoding="utf-8", newline="\n")
    return manifest


def verify_lock(root: Path, commit: str) -> list[str]:
    manifest = json.loads((root / LOCK_MANIFEST).read_text(encoding="utf-8"))
    problems = []
    for key, entry in sorted(manifest["files"].items()):
        if not (root / entry["path"]).is_file() or d.sha256_file(root / entry["path"]) != entry["sha256"]:
            problems.append(f"{key}:WORKTREE_MISMATCH")
        out = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{entry['path']}"],
                             capture_output=True, check=False)
        if out.returncode != 0 or hashlib.sha256(out.stdout).hexdigest() != entry["sha256"]:
            problems.append(f"{key}:LOCK_COMMIT_MISMATCH")
    if set(manifest["files"]) != set(stage_b_locked_files()):
        problems.append("LOCKED_FILE_SET_MISMATCH")
    if manifest["prompt_sha256"] != hashlib.sha256(PROMPT.encode("utf-8")).hexdigest():
        problems.append("PROMPT_MISMATCH")
    return problems


def _one_call(transport: Transport, budget: Budget, item: dict[str, Any], call: int,
              ) -> tuple[dict[str, Any], dict[str, Any] | None]:
    body = request_body(item)
    worst = worst_case_usd(body)
    if not budget.reserve(worst):
        return {"item_id": item["item_id"], "call": call, "transport_error": True,
                "refused_by_guard": True, "cost_usd": "0"}, None
    try:
        status, raw, attempts = dispatch(transport, body)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        budget.settle(worst, Fraction(0))
        return {"item_id": item["item_id"], "call": call, "transport_error": True,
                "error": type(exc).__name__, "cost_usd": "0"}, None
    record = score(item, call, status, raw, body)
    budget.settle(worst, Fraction(record["cost_usd"]))
    record["attempts"] = attempts
    receipt = {"item_id": item["item_id"], "call": call, "http_status": status,
               "request_sha256": record["request_sha256"], "response_sha256": record["response_sha256"],
               "request": body.decode("utf-8"), "response": raw.decode("utf-8", errors="surrogateescape")}
    return record, receipt


def _write_jsonl(path: Path, rows: list[dict[str, Any]], gz: bool = False) -> None:
    text = "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows)
    data = text.encode("utf-8", errors="surrogateescape")
    path.write_bytes(gzip.compress(data, mtime=0) if gz else data)


def run(args: argparse.Namespace) -> int:
    root = d.repo_root()
    problems = verify_lock(root, args.lock_commit)
    if problems:
        print(json.dumps({"refused": "LOCK", "problems": problems}))
        return 1
    n_items = args.items or N_ITEMS
    items = make_items(args.lock_commit, n_items)
    worst_plan = sum((worst_case_usd(request_body(it)) * CALLS_PER_ITEM for it in items), Fraction(0))
    if worst_plan > PLAN_CEILING_USD:
        print(json.dumps({"refused": "PLAN_ABOVE_CEILING", "worst_case_usd": float(worst_plan)}))
        return 1
    if args.fixture:
        transport = fixture_transport(derive_seed(args.lock_commit, "fixture"))
    else:
        key = read_env_file(Path(args.env_file), "ANTHROPIC_API_KEY") if args.env_file else ""
        if not key:
            print(json.dumps({"refused": "NO_KEY", "env_file": args.env_file}))
            return 1
        transport = anthropic_transport(key)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    budget = Budget(CAP_USD)
    jobs = [(it, k) for it in items for k in range(CALLS_PER_ITEM)]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda job: _one_call(transport, budget, job[0], job[1]), jobs))
    records = [r for r, _ in results]
    _write_jsonl(out / "traces.jsonl", records)
    _write_jsonl(out / "calls.jsonl.gz", [c for _, c in results if c is not None], gz=True)
    summary = sba.analyse(records, derive_seed(args.lock_commit, "bootstrap"))
    summary.update({"lock_commit": args.lock_commit, "transport": "fixture" if args.fixture else "anthropic",
                    "model": MODEL, "n_items": n_items, "confirmatory": n_items == N_ITEMS and not args.fixture,
                    "spent_usd": tr.q(budget.spent), "spent_usd_float": float(budget.spent),
                    "worst_case_plan_usd": float(worst_plan), "refused_by_guard": budget.refused})
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps({k: summary[k] for k in ("decision", "spent_usd_float", "n_primary", "failures")}))
    return 0


def analyse_dir(args: argparse.Namespace) -> int:
    path = Path(args.run_dir)
    records = [json.loads(line) for line in (path / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
    summary = sba.analyse(records, derive_seed(args.lock_commit, "bootstrap"))
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stage_b")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--lock-commit", required=True)
    p_run.add_argument("--out", required=True)
    group = p_run.add_mutually_exclusive_group(required=True)
    group.add_argument("--env-file")
    group.add_argument("--fixture", action="store_true")
    p_run.add_argument("--items", type=int, default=0, help="fewer items: exploratory, not confirmatory")
    p_run.add_argument("--workers", type=int, default=WORKERS)
    p_an = sub.add_parser("analyse")
    p_an.add_argument("--run-dir", required=True)
    p_an.add_argument("--lock-commit", required=True)
    p_lock = sub.add_parser("write-manifest")
    p_lock.add_argument("--base-revision", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "run":
        return run(args)
    if args.cmd == "analyse":
        return analyse_dir(args)
    print(json.dumps(write_manifest(d.repo_root(), args.base_revision)["files"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
