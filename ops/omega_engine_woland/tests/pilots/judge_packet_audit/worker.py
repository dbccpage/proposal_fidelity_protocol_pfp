"""Subprocess worker for the judge-packet audit harness.

This file is executed as a standalone script (``python worker.py JOB.json``)
inside the repository tree under audit. It imports only the standard library
and the modules of the one challenge package named in the job, so it never
depends on the harness package being importable from the audited tree.

The worker processes the job's items in order and writes one JSON line per
item to stdout. A per-call watchdog thread bounds every checker and solver
call; when a call overruns, the worker writes a TIMEOUT record for that item
and exits with status 3 so the parent can restart it at the next item.

Network access is disabled inside the worker by replacing the socket
constructors before any package module is imported.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import re
import socket
import sys
import threading
import traceback
from fractions import Fraction
from typing import Any

EXIT_TIMEOUT = 3
MESSAGE_LIMIT = 240
REF_JSON_LIMIT = 20000

ACCEPT_WORDS = frozenset(
    {"PASS", "PASSED", "ACCEPT", "ACCEPTED", "VALID", "OK", "VERIFIED", "TRUE"}
)
REJECT_WORDS = frozenset(
    {
        "FAIL",
        "FAILED",
        "REJECT",
        "REJECTED",
        "INVALID",
        "FALSE",
        "ERROR",
        "REFUSE",
        "REFUSED",
        "CHECKER_DISAGREEMENT",
        "DISAGREEMENT",
    }
)
BOOL_RESULT_KEYS = ("valid", "ok", "passed", "accepted", "is_valid", "success", "verified")
MESSAGE_KEYS = ("reason", "message", "msg", "detail", "details", "error")
ID_KEYS = ("id", "case_id")
NUMERIC_STRING = re.compile(r"^-?\d+(/\d+)?$")


class _NetworkBlocked(OSError):
    pass


def _blocked(*_args: Any, **_kwargs: Any) -> Any:
    raise _NetworkBlocked("network access is disabled in the judge-audit worker")


def block_network() -> None:
    socket.socket = _blocked  # type: ignore[assignment,misc]
    socket.create_connection = _blocked  # type: ignore[assignment]
    socket.getaddrinfo = _blocked  # type: ignore[assignment]


RECORD_STREAM = sys.stdout


def emit(record: dict[str, Any]) -> None:
    """Writes one record line to the saved stdout; package prints go to stderr instead."""
    RECORD_STREAM.write(json.dumps(record, sort_keys=True, ensure_ascii=False, default=str) + "\n")
    RECORD_STREAM.flush()


def short(text: Any) -> str:
    value = text if isinstance(text, str) else repr(text)
    value = value.replace("\r", " ").replace("\n", " ")
    return value[:MESSAGE_LIMIT]


def call_with_timeout(fn: Any, args: tuple[Any, ...], timeout_s: float) -> dict[str, Any]:
    box: dict[str, Any] = {}

    def run() -> None:
        try:
            box["ret"] = fn(*args)
        except BaseException as exc:  # noqa: BLE001 - a checker crash is data
            box["exc"] = exc
            box["tb"] = traceback.format_exc(limit=3)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(timeout_s)
    if thread.is_alive():
        return {"timeout": True}
    return box


def normalize(ret: Any) -> tuple[str, str, str]:
    """Maps a checker return value to (outcome, shape, message)."""
    if type(ret) is bool:
        return ("ACCEPT" if ret else "REJECT", "bool", "")
    if isinstance(ret, (tuple, list)) and ret and type(ret[0]) is bool:
        message = ret[1] if len(ret) > 1 else ""
        return (
            "ACCEPT" if ret[0] else "REJECT",
            f"{type(ret).__name__}[{len(ret)}]",
            short(message),
        )
    if isinstance(ret, dict):
        message = ""
        for key in MESSAGE_KEYS:
            if key in ret:
                message = short(ret[key])
                break
        verdict = ret.get("verdict")
        if isinstance(verdict, str):
            word = verdict.strip().upper()
            if word in ACCEPT_WORDS:
                return ("ACCEPT", "dict.verdict", message)
            if word in REJECT_WORDS:
                return ("REJECT", "dict.verdict", message or short(verdict))
            return ("UNINTERPRETABLE", "dict.verdict", short(verdict))
        for key in BOOL_RESULT_KEYS:
            if type(ret.get(key)) is bool:
                return ("ACCEPT" if ret[key] else "REJECT", f"dict.{key}", message)
        return ("UNINTERPRETABLE", "dict", short(sorted(ret.keys())))
    verdict_attr = getattr(ret, "verdict", None)
    if isinstance(verdict_attr, str):
        word = verdict_attr.strip().upper()
        if word in ACCEPT_WORDS:
            return ("ACCEPT", f"{type(ret).__name__}.verdict", "")
        if word in REJECT_WORDS:
            return ("REJECT", f"{type(ret).__name__}.verdict", short(verdict_attr))
    for key in BOOL_RESULT_KEYS:
        value = getattr(ret, key, None)
        if type(value) is bool:
            return ("ACCEPT" if value else "REJECT", f"{type(ret).__name__}.{key}", "")
    return ("UNINTERPRETABLE", type(ret).__name__, short(ret))


def load_function(module_name: str, function_name: str) -> Any:
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def load_cases(package_dir: str, case_refs: list[dict[str, Any]], unwrap_input: bool) -> list[Any]:
    cache: dict[str, Any] = {}
    cases = []
    for ref in case_refs:
        path = os.path.join(package_dir, ref["path"])
        if path not in cache:
            with open(path, encoding="utf-8") as handle:
                cache[path] = json.load(handle)
        data = cache[path]
        index = ref.get("index")
        if index is not None:
            items = data["cases"] if isinstance(data, dict) else data
            case = items[index]
        else:
            case = data
        if unwrap_input and isinstance(case, dict) and isinstance(case.get("input"), dict):
            case = case["input"]
        cases.append(case)
    return cases


def case_identifier(case: Any) -> str | None:
    if isinstance(case, dict):
        for key in ID_KEYS:
            if isinstance(case.get(key), str):
                return case[key]
    return None


def instantiate(template: Any, case: Any) -> Any:
    answer = copy.deepcopy(template)
    cid = case_identifier(case)
    if isinstance(answer, dict) and cid is not None:
        for key in ID_KEYS:
            if key in answer:
                answer[key] = cid
    return answer


def jsonable(value: Any) -> tuple[Any, bool]:
    """Returns (json_value, exact) where exact is False when a conversion was needed."""
    exact = [True]

    def conv(v: Any) -> Any:
        if v is None or isinstance(v, (str, bool, int)):
            return v
        if isinstance(v, float):
            exact[0] = False
            return repr(v)
        if isinstance(v, Fraction):
            exact[0] = False
            return str(v)
        if isinstance(v, dict):
            return {str(k): conv(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            if isinstance(v, tuple):
                exact[0] = False
            return [conv(x) for x in v]
        if isinstance(v, (set, frozenset)):
            exact[0] = False
            return sorted(
                (conv(x) for x in v), key=lambda x: json.dumps(x, sort_keys=True, default=str)
            )
        exact[0] = False
        return repr(v)

    return conv(value), exact[0]


def answer_tokens(value: Any, echo: str | None = None) -> list[str]:
    """Word tokens of an answer's categorical strings, identifiers and ID echoes removed.

    ``echo`` is the case identifier; occurrences of it inside answer strings
    (for example a trace line naming the case) are removed before
    tokenizing, so a case ID is not credited with naming what it echoes.
    """
    tokens: set[str] = set()

    def walk(v: Any, key: str | None) -> None:
        if isinstance(v, dict):
            for k, x in v.items():
                if k in ID_KEYS:
                    continue
                walk(x, str(k))
        elif isinstance(v, (list, tuple)):
            for x in v:
                walk(x, key)
        elif isinstance(v, str):
            if echo:
                v = v.replace(echo, " ")
            if NUMERIC_STRING.match(v) or len(v) > 64:
                return
            for tok in re.split(r"[^A-Za-z0-9]+", v):
                if len(tok) >= 3 and not tok.isdigit():
                    tokens.add(tok.lower())

    walk(value, None)
    return sorted(tokens)


def variant(value: Any, kind: str) -> tuple[Any, int]:
    """Builds a type-confusion variant; returns (variant, number_of_replacements)."""
    count = [0]

    def conv(v: Any, key: str | None) -> Any:
        if key in ID_KEYS:
            return v
        if isinstance(v, dict):
            return {k: conv(x, k) for k, x in v.items()}
        if isinstance(v, list):
            return [conv(x, key) for x in v]
        if isinstance(v, tuple):
            return tuple(conv(x, key) for x in v)
        if kind == "float_for_int" and type(v) is int:
            count[0] += 1
            return float(v)
        if kind == "bool_for_01" and type(v) is int and v in (0, 1):
            count[0] += 1
            return v == 1
        if kind == "float_for_numeric_string" and isinstance(v, str) and NUMERIC_STRING.match(v):
            count[0] += 1
            return float(Fraction(v))
        if kind == "float_for_fraction" and isinstance(v, Fraction):
            count[0] += 1
            return float(v)
        if kind == "float_truncating_to_int" and type(v) is int and abs(v) < 2**52:
            # a non-integral float that int() truncates back to v
            count[0] += 1
            return v + 0.3 if v >= 0 else v - 0.3
        return v

    return conv(value, None), count[0]


VARIANT_KINDS = (
    "float_for_int",
    "float_truncating_to_int",
    "bool_for_01",
    "float_for_numeric_string",
    "float_for_fraction",
)


class Evaluator:
    def __init__(self, job: dict[str, Any]) -> None:
        self.job = job
        self.call_timeout = float(job.get("call_timeout_s", 20))
        prefix = job.get("import_prefix", "")
        self.checkers = []
        for spec in job["checkers"]:
            fn = load_function(prefix + spec["module"], spec["function"])
            self.checkers.append((spec["role"], fn))
        gate = job["gate"]
        self.gate_fn = None
        if gate["kind"] == "function":
            self.gate_fn = load_function(prefix + gate["module"], gate["function"])
        self.solver_fn = None
        solver = job.get("solver")
        if solver and job["mode"] == "reference":
            self.solver_fn = load_function(prefix + solver["module"], solver["function"])

    def evaluate(self, case: Any, answer: Any) -> tuple[dict[str, Any], bool]:
        """Returns (calls, timed_out)."""
        calls: dict[str, Any] = {}
        for role, fn in self.checkers:
            record = self._call(fn, case, answer)
            calls[role] = record
            if record["outcome"] == "TIMEOUT":
                return calls, True
        if self.gate_fn is not None:
            record = self._call(self.gate_fn, case, answer)
            calls["gate"] = record
            if record["outcome"] == "TIMEOUT":
                return calls, True
        else:
            accepted = all(calls[role]["outcome"] == "ACCEPT" for role, _ in self.checkers)
            calls["gate"] = {
                "outcome": "ACCEPT" if accepted else "REJECT",
                "shape": "all_accept",
                "message": "",
            }
        return calls, False

    def _call(self, fn: Any, case: Any, answer: Any) -> dict[str, Any]:
        box = call_with_timeout(fn, (copy.deepcopy(case), copy.deepcopy(answer)), self.call_timeout)
        if box.get("timeout"):
            return {"outcome": "TIMEOUT", "shape": "", "message": f"exceeded {self.call_timeout}s"}
        if "exc" in box:
            exc = box["exc"]
            return {"outcome": "EXCEPTION", "shape": type(exc).__name__, "message": short(str(exc))}
        outcome, shape, message = normalize(box.get("ret"))
        return {"outcome": outcome, "shape": shape, "message": message}


def run_reference(job: dict[str, Any], ev: Evaluator, cases: list[Any], start: int) -> None:
    solver_timeout = float(job.get("solver_timeout_s", 60))
    for index in range(start, len(cases)):
        case = cases[index]
        box = call_with_timeout(ev.solver_fn, (copy.deepcopy(case),), solver_timeout)
        record: dict[str, Any] = {"i": index}
        if box.get("timeout"):
            record["solver"] = {"outcome": "TIMEOUT", "message": f"exceeded {solver_timeout}s"}
            emit(record)
            os._exit(EXIT_TIMEOUT)
        if "exc" in box:
            record["solver"] = {
                "outcome": "EXCEPTION",
                "message": short(f"{type(box['exc']).__name__}: {box['exc']}"),
            }
            emit(record)
            continue
        ref = box.get("ret")
        shape = type(ref).__name__
        if isinstance(ref, tuple) and ref and isinstance(ref[0], dict):
            ref = ref[0]
            shape = "tuple[0]"
        ref_json, exact = jsonable(ref)
        text = json.dumps(ref_json, sort_keys=True, ensure_ascii=False)
        record["solver"] = {
            "outcome": "RETURNED",
            "shape": shape,
            "exact_json": exact,
            "status": ref.get("status")
            if isinstance(ref, dict) and isinstance(ref.get("status"), str)
            else None,
            "id_keys": [k for k in ID_KEYS if isinstance(ref, dict) and k in ref],
            "tokens": answer_tokens(ref, case_identifier(case)),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "json": ref_json if len(text) <= REF_JSON_LIMIT else None,
        }
        calls, timed_out = ev.evaluate(case, ref)
        record["reference"] = calls
        if timed_out:
            emit(record)
            os._exit(EXIT_TIMEOUT)
        variants: dict[str, Any] = {}
        candidates = [(kind, *variant(ref, kind)) for kind in VARIANT_KINDS]
        if not exact:
            # the reference answer in JSON wire form (Fractions as strings, tuples as lists)
            candidates.append(("json_roundtrip", json.loads(json.dumps(ref_json)), 1))
        for kind, var, replaced in candidates:
            if replaced == 0:
                continue
            vcalls, timed_out = ev.evaluate(case, var)
            variants[kind] = {"replacements": replaced, "calls": vcalls}
            if timed_out:
                record["variants"] = variants
                emit(record)
                os._exit(EXIT_TIMEOUT)
        record["variants"] = variants
        emit(record)


def run_responders(job: dict[str, Any], ev: Evaluator, cases: list[Any], start: int) -> None:
    responders = job["responders"]
    items = job["items"]
    for index in range(start, len(items)):
        case_index, responder_index = items[index]
        case = cases[case_index]
        strategy = responders[responder_index]
        if strategy.get("per_case") is not None:
            answer = copy.deepcopy(strategy["per_case"][case_index])
        else:
            answer = instantiate(strategy["template"], case)
        calls, timed_out = ev.evaluate(case, answer)
        emit({"i": index, "calls": calls})
        if timed_out:
            os._exit(EXIT_TIMEOUT)


def run_mutations(job: dict[str, Any], ev: Evaluator, start: int) -> None:
    package_dir = job["package_dir"]
    entries = job["mutations"]
    cache: dict[str, Any] = {}
    for index in range(start, len(entries)):
        ref = entries[index]
        path = os.path.join(package_dir, ref["path"])
        if path not in cache:
            with open(path, encoding="utf-8") as handle:
                cache[path] = json.load(handle)
        data = cache[path]
        if ref.get("index") is None:
            item = data
        elif isinstance(data, dict):
            item = data["mutations"][ref["index"]]
        else:
            item = data[ref["index"]]
        case = item[ref["case_key"]]
        answer = item[ref["answer_key"]]
        calls, timed_out = ev.evaluate(case, answer)
        emit({"i": index, "calls": calls})
        if timed_out:
            os._exit(EXIT_TIMEOUT)


def run_probe(job: dict[str, Any]) -> None:
    prefix = job.get("import_prefix", "")
    fn = load_function(prefix + job["probe"]["module"], job["probe"]["function"])
    calls = job["probe"]["calls"]
    for index in range(int(job.get("start", 0)), len(calls)):
        box = call_with_timeout(fn, tuple(calls[index]), float(job.get("call_timeout_s", 20)))
        if box.get("timeout"):
            emit({"i": index, "outcome": "TIMEOUT"})
            os._exit(EXIT_TIMEOUT)
        if "exc" in box:
            emit(
                {
                    "i": index,
                    "outcome": "EXCEPTION",
                    "message": short(f"{type(box['exc']).__name__}: {box['exc']}"),
                }
            )
            continue
        value, _ = jsonable(box.get("ret"))
        emit({"i": index, "outcome": "RETURNED", "value": value})


def main(argv: list[str]) -> int:
    with open(argv[1], encoding="utf-8") as handle:
        job = json.load(handle)
    block_network()
    sys.stdout = sys.stderr
    threading.stack_size(64 * 1024 * 1024)
    sys.setrecursionlimit(20000)
    for entry in reversed(job["sys_path"]):
        if entry not in sys.path:
            sys.path.insert(0, entry)
    start = int(job.get("start", 0))
    try:
        if job["mode"] == "probe":
            emit({"ready": True})
            run_probe(job)
            return 0
        ev = Evaluator(job)
        cases = load_cases(job["package_dir"], job.get("cases", []), bool(job.get("unwrap_input")))
    except BaseException as exc:  # noqa: BLE001 - reported to the parent as data
        emit(
            {
                "import_error": short(f"{type(exc).__name__}: {exc}"),
                "traceback": traceback.format_exc(limit=4)[-2000:],
            }
        )
        return 2
    emit({"ready": True})
    if job["mode"] == "reference":
        run_reference(job, ev, cases, start)
    elif job["mode"] == "responders":
        run_responders(job, ev, cases, start)
    elif job["mode"] == "mutations":
        run_mutations(job, ev, start)
    else:
        emit({"import_error": f"unknown mode {job['mode']!r}"})
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
