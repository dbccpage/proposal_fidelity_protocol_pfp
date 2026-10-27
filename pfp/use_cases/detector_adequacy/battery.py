"""Stage A of PREREG-DA-001: the detector adequacy battery (no model calls, no network).

Run from the repository root:

    python -m pfp.use_cases.detector_adequacy.battery \
        --lock-commit <sha> --n 300 --out <dir>

The run refuses (exit 1) unless every locked file matches the lock manifest both in the
working tree and at ``--lock-commit``. The mutant seed is derived from the lock commit,
so it is fixed only after the detectors are. AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import random
import subprocess
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from pfp.use_cases.detector_adequacy import detectors, traces, witness_replay

PREREG_ID = "PREREG-DA-001"
LOCK_MANIFEST = "pfp/documentation/detector_adequacy/lock_da_001.json"
HELDOUT_MODULE = "pfp.use_cases.detector_adequacy.heldout"

# Pre-registered thresholds (section 4 of the pre-registration).
FALSE_GREEN_FAMILY_MAX = 0.02
FALSE_GREEN_POOLED_MAX = 0.01
FALSE_RED_FAMILY_MAX = 0.02
CLEAN_NONCERT_FAMILY_MAX = 0.02
MIN_N = 300

Family = Callable[[traces.Trace, random.Random], traces.Trace]


def upper_bound_95(k: int, n: int) -> float:
    """Exact one-sided 95% Clopper-Pearson upper bound on a binomial rate."""
    if n == 0:
        return 1.0
    if k >= n:
        return 1.0

    def cdf(p: float) -> float:
        if p <= 0.0:
            return 1.0
        lp, lq = math.log(p), math.log1p(-p)
        return sum(math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                            + i * lp + (n - i) * lq) for i in range(k + 1))

    lo, hi = k / n, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if cdf(mid) > 0.05:
            lo = mid
        else:
            hi = mid
    return hi


def _git_blob(root: Path, commit: str, path: str) -> Optional[bytes]:
    out = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{path}"],
                         capture_output=True, check=False)
    return out.stdout if out.returncode == 0 else None


def verify_lock(root: Path, commit: str) -> Dict[str, Any]:
    manifest = json.loads((root / LOCK_MANIFEST).read_text(encoding="utf-8"))
    problems = []
    for key, entry in manifest["files"].items():
        path, digest = entry["path"], entry["sha256"]
        tree = root / path
        if not tree.is_file() or detectors.sha256_file(tree) != digest:
            problems.append(f"{key}:WORKTREE_MISMATCH")
        blob = _git_blob(root, commit, path)
        if blob is None or hashlib.sha256(blob).hexdigest() != digest:
            problems.append(f"{key}:LOCK_COMMIT_MISMATCH")
    if set(manifest["files"]) != set(detectors.locked_files()):
        problems.append("LOCKED_FILE_SET_MISMATCH")
    return {"manifest": manifest, "problems": problems}


def derive_seed(commit: str) -> int:
    return int(hashlib.sha256(f"{commit}:{PREREG_ID}".encode()).hexdigest()[:16], 16)


def heldout_families() -> Dict[str, Family]:
    try:
        module = importlib.import_module(HELDOUT_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != HELDOUT_MODULE:
            raise
        return {}
    return dict(module.HELDOUT_FAMILIES)


CRASH = "CRASH"


def _judge(trace: traces.Trace) -> Optional[bool]:
    """The outcome judge; None when it rejects the trace as malformed (counted as not correct)."""
    try:
        return witness_replay.answer_is_correct(trace)
    except Exception:  # noqa: BLE001 - a judge rejection is an outcome, recorded as None
        return None


def _replays(trace: traces.Trace, witness: Tuple[Tuple[str, Fraction], ...]) -> bool:
    try:
        return witness_replay.replay_witness(trace, witness)
    except Exception:  # noqa: BLE001 - a witness the replay cannot evaluate does not replay
        return False


def _evaluate(trace: traces.Trace) -> Dict[str, Any]:
    row: Dict[str, Any] = {"answer_correct": _judge(trace)}
    for name in detectors.EXTRACTORS:
        try:
            v = detectors.run_detector(name, trace)
        except Exception as exc:  # noqa: BLE001 - a detector crash is recorded, never read as green
            row[name] = {"status": CRASH, "error": type(exc).__name__}
            continue
        cell: Dict[str, Any] = {"status": v.status, "pi": v.pi_status}
        if v.refusal:
            cell["refusal"] = v.refusal
        if v.status == detectors.RED:
            cell["witness"] = [sid for sid, _ in v.witness]
            cell["replayed"] = _replays(trace, v.witness)
            cell["certified"] = v.certified
        row[name] = cell
    return row


def _local_vector(trace: traces.Trace) -> Dict[str, int]:
    try:
        defects = detectors.relation_defects(trace, lenient=True)
    except Exception:  # noqa: BLE001 - no local vector for a trace the extractor cannot read
        return {}
    return {sid: int(d == 0) for sid, d in defects.items()}


def run(n: int, seed: int, families: Dict[str, Tuple[str, Family]]) -> Dict[str, Any]:
    rng = random.Random(seed)
    rows: List[Dict[str, Any]] = []
    lggr_samples: List[Tuple[Dict[str, int], int]] = []
    index = 0
    for fam, (role, fn) in families.items():
        for _ in range(n):
            item = traces.make_item(rng, index)
            index += 1
            trace = fn(traces.clean_trace(item), rng)
            row = _evaluate(trace)
            row.update(family=fam, role=role, item_id=item["item_id"])
            rows.append(row)
            if role == "mutant" or fam == "C0_canonical":
                lggr_samples.append((_local_vector(trace), int(row["answer_correct"] is True)))
    return {"rows": rows, "lggr_samples": lggr_samples}


def summarise(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    table: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for name in detectors.EXTRACTORS:
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in rows:
            groups[r["family"]].append(r)
        for fam, rs in groups.items():
            c = Counter(r[name]["status"] for r in rs)
            reds = [r[name] for r in rs if r[name]["status"] == detectors.RED]
            cell = {
                "role": rs[0]["role"], "n": len(rs), "green": c[detectors.GREEN], "red": c[detectors.RED],
                "noncertifying": c[detectors.NONCERTIFYING], "crash": c[CRASH],
                "red_witness_replayed": sum(1 for x in reds if x["replayed"]),
                "red_uncertified_dual": sum(1 for x in reds if x.get("certified") is not True),
                "answer_correct": sum(1 for r in rs if r["answer_correct"] is True),
                "judge_rejected": sum(1 for r in rs if r["answer_correct"] is None),
                "refusals": dict(Counter(r[name].get("refusal") for r in rs if r[name].get("refusal"))),
            }
            key = "green" if cell["role"] == "mutant" else "red"
            cell["ub95_" + ("false_green" if key == "green" else "false_red")] = round(
                upper_bound_95(cell[key], cell["n"]), 5)
            if cell["role"] == "clean":
                cell["ub95_noncertifying"] = round(upper_bound_95(cell["noncertifying"], cell["n"]), 5)
            table[name][fam] = cell
    return table


def certificate(table: Dict[str, Dict[str, Any]], lock_ok: bool) -> Dict[str, Any]:
    out = {}
    for name, fams in table.items():
        reasons = []
        if not lock_ok:
            reasons.append("A4_LOCK")
        mutants = [c for c in fams.values() if c["role"] == "mutant"]
        cleans = [c for c in fams.values() if c["role"] == "clean"]
        for fam, c in fams.items():
            if c["n"] < MIN_N:
                reasons.append(f"N_BELOW_{MIN_N}:{fam}")
            if c["role"] == "mutant" and c["ub95_false_green"] > FALSE_GREEN_FAMILY_MAX:
                reasons.append(f"A1_FALSE_GREEN:{fam}")
            if c["role"] == "clean" and c["ub95_false_red"] > FALSE_RED_FAMILY_MAX:
                reasons.append(f"A2_FALSE_RED:{fam}")
            if c["role"] == "clean" and c["crash"]:
                reasons.append(f"A5_CLEAN_CRASH:{fam}")
            if c["role"] == "clean" and c["ub95_noncertifying"] > CLEAN_NONCERT_FAMILY_MAX:
                reasons.append(f"A5_CLEAN_NOT_CERTIFIED:{fam}")
            if c["red_witness_replayed"] != c["red"]:
                reasons.append(f"A3_WITNESS_NOT_REPLAYED:{fam}")
        pooled_k = sum(c["green"] for c in mutants)
        pooled_n = sum(c["n"] for c in mutants)
        pooled = upper_bound_95(pooled_k, pooled_n)
        if pooled > FALSE_GREEN_POOLED_MAX:
            reasons.append("A1_FALSE_GREEN_POOLED")
        out[name] = {"issued": not reasons, "reasons": reasons,
                     "pooled_false_green": [pooled_k, pooled_n, round(pooled, 5)],
                     "clean_n": sum(c["n"] for c in cleans)}
    return out


def lggr_report(samples: List[Tuple[Dict[str, int], int]], adapter_factory: Callable[[], Any]) -> Dict[str, Any]:
    """Run a gluing adapter over the local vectors. The caller supplies the adapter, so this
    package does not import Adversary (``test_symbol_game_production_code_does_not_import_adversary``)."""
    usable = [s for s in samples if s[0]]
    keys = sorted({k for s in usable for k in s[0]})
    corpus = [({k: s[0].get(k, 1) for k in keys}, s[1]) for s in usable]
    result = adapter_factory().evaluate_boundary(corpus[0][0], corpus[0][1], corpus_samples=corpus)
    verdicts = Counter(adapter_factory().evaluate_boundary(lv, g).verdict_name for lv, g in corpus)
    return {
        "samples": len(corpus),
        "local_evaluators": keys,
        "detector_adequacy_certified": bool(getattr(result, "detector_adequacy_certified", None)),
        "verdict_counts": dict(verdicts),
        "adequacy_failures": list(getattr(result, "adequacy_failures", []) or []),
    }


def _jsonable(x: Any) -> Any:
    if isinstance(x, Fraction):
        return str(x)
    raise TypeError(type(x).__name__)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lock-commit", required=True)
    ap.add_argument("--n", type=int, default=MIN_N)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-heldout", action="store_true")
    args = ap.parse_args(argv)

    root = detectors.repo_root()
    lock = verify_lock(root, args.lock_commit)
    if lock["problems"]:
        print(json.dumps({"status": "REFUSED", "lock_problems": lock["problems"]}))
        return 1
    families: Dict[str, Tuple[str, Family]] = {k: ("clean", f) for k, f in traces.CLEAN_FAMILIES.items()}
    families.update({k: ("mutant", f) for k, f in traces.MUTANT_FAMILIES.items()})
    held = {} if args.no_heldout else heldout_families()
    families.update({k: ("mutant", f) for k, f in held.items()})

    seed = derive_seed(args.lock_commit)
    result = run(args.n, seed, families)
    table = summarise(result["rows"])
    report = {
        "prereg": PREREG_ID,
        "authority_effect": "None",
        "lock_commit": args.lock_commit,
        "lock_manifest": lock["manifest"],
        "seed": seed,
        "n_per_family": args.n,
        "families": {k: role for k, (role, _) in families.items()},
        "heldout_sha256": (detectors.sha256_file(root / (HELDOUT_MODULE.replace(".", "/") + ".py"))
                           if held else None),
        "python": sys.version.split()[0],
        "table": table,
        "certificate": certificate(table, lock_ok=True),
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "stage_a_summary.json").write_text(
        json.dumps(report, indent=1, sort_keys=True, default=_jsonable) + "\n", encoding="utf-8")
    with (out / "stage_a_rows.jsonl").open("w", encoding="utf-8") as fh:
        for r in result["rows"]:
            fh.write(json.dumps(r, sort_keys=True, default=_jsonable) + "\n")
    sums = [f"{detectors.sha256_file(out / f)}  {f}" for f in ("stage_a_rows.jsonl", "stage_a_summary.json")]
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    print(json.dumps({name: c["issued"] for name, c in report["certificate"].items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
