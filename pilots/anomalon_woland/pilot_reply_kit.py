"""Shared reply plumbing for PFP pilots: wire, strict parsing, capped reply files, evaluation, CLI, check.

AuthorityEffect: None. Stdlib and pydantic only. A pilot's run.py loads this file by path and keeps only
its task data, prompt builder and checker. Replies are caller-supplied and unauthenticated.
"""
import argparse
from collections import Counter
from collections.abc import Callable
import contextlib
from dataclasses import dataclass, field
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from typing import Annotated, Any
import xml.etree.ElementTree as ET

from pydantic import BaseModel, ConfigDict, Field, StrictStr, TypeAdapter

MAX_INPUT_BYTES = 16384
MAX_REPLIES = 64
MIN_COVERAGE = 98.0
MUTANT_TEST_PREFIX = "test_checker_mutant_killed["
KIT_STATUSES = ("NOT_RUN", "SOURCE_MISMATCH", "MALFORMED")
FOREIGN_ID = "FOREIGN_ID"


class Strict(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class SuppliedReply(Strict):
    request_id: Annotated[StrictStr, Field(min_length=1, max_length=128)]
    source_sha256: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    raw_reply: Annotated[StrictStr, Field(max_length=1024)]


REPLIES = TypeAdapter(Annotated[list[SuppliedReply], Field(max_length=MAX_REPLIES)])


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(value):
    return hashlib.sha256(wire(value)).hexdigest()


def unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique_pairs)


def read_capped(path, limit=MAX_INPUT_BYTES):
    """Read a UTF-8 JSON file of at most `limit` bytes; larger files raise ValueError."""
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f"Input exceeds {limit} bytes")
    return parse(raw.decode("utf-8"))


def load_module(path, name):
    """Load a Python file as module `name`, registered in sys.modules before execution."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def load_mutant(path, old, new, directory, name):
    """Load a copy of `path` with the single occurrence of `old` replaced by `new`."""
    text = Path(path).read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise ValueError(f"Mutation anchor must occur exactly once: {old!r}")
    target = Path(directory) / f"{name}.py"
    target.write_text(text.replace(old, new), encoding="utf-8")
    try:
        return load_module(target, name)
    finally:
        sys.modules.pop(name, None)


def run_cli(main, argv):
    """Call a pilot main(argv); return (exit code, parsed JSON stdout)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(argv)
    return code, json.loads(buffer.getvalue())


def run_script(path, argv=()):
    """Execute a pilot file as __main__; return (SystemExit code or None, parsed JSON stdout)."""
    saved, code, buffer = sys.argv, None, io.StringIO()
    sys.argv = [str(path), *argv]
    try:
        with contextlib.redirect_stdout(buffer):
            runpy.run_path(str(path), run_name="__main__")
    except SystemExit as exit_:
        code = exit_.code
    finally:
        sys.argv = saved
    return code, json.loads(buffer.getvalue())


def verdict(pilot, request_id, raw_reply):
    """Status `pilot` assigns to `raw_reply` bound to the current source hash of `request_id`."""
    request = {request.request_id: request for request in pilot.requests}[request_id]
    supplied = SuppliedReply(request_id=request_id, source_sha256=request.sha, raw_reply=raw_reply)
    return pilot.check(request, supplied)["status"]


def label_leaks(requests, labels):
    """Return (request_id, label) pairs where a label appears in the prompt messages."""
    return [(request.request_id, label) for request in requests for label in labels
            if any(label in message["content"] for message in request.messages())]


@dataclass(frozen=True)
class Request:
    """One exported request. `source` is the prompt-visible content and never carries an arm label."""
    request_id: str
    instruction: str
    source: dict
    meta: dict = field(default_factory=dict)

    @property
    def sha(self):
        return sha256_hex(self.source)

    def messages(self):
        return [{"role": "system", "content": self.instruction},
                {"role": "user", "content": wire(self.source).decode("utf-8")}]

    def export(self):
        payload = {"request_id": self.request_id, "source_sha256": self.sha, "messages": self.messages()}
        return {"request": payload, "request_utf8_bytes": len(wire(payload)), "trial_status": "NOT_RUN"}


@dataclass(frozen=True)
class Pilot:
    """`decode` raises ValueError/RecursionError for a malformed reply; `grade` errors propagate."""
    pilot_id: str
    expansion_ordinal: int
    description: str
    requests: tuple
    decode: Callable[[Request, Any], Any]
    grade: Callable[[Request, Any], dict]
    statuses: tuple
    record_foreign: bool = False
    missing_status: str = "NOT_RUN"

    def __post_init__(self):
        ids = [request.request_id for request in self.requests]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate request_id in request matrix")

    def exports(self):
        return {"live_trial": "PENDING", "pilot_id": self.pilot_id, "expansion_ordinal": self.expansion_ordinal,
                "provider_calls": 0, "requests": [request.export() for request in self.requests]}

    def check(self, request, supplied):
        row = {"request_id": request.request_id, "status": self.missing_status,
               "raw_reply": None if supplied is None else supplied.raw_reply}
        if supplied is None:
            return row
        if supplied.source_sha256 != request.sha:
            return {**row, "status": "SOURCE_MISMATCH"}
        try:
            value = self.decode(request, parse(supplied.raw_reply))
        except (ValueError, RecursionError) as error:
            return {**row, "status": "MALFORMED", "detail": str(error)}
        verdict = self.grade(request, value)
        if verdict.get("status") not in self.statuses:
            raise RuntimeError(f"Undeclared status from grade: {verdict.get('status')!r}")
        return {**row, **verdict}

    def evaluate(self, value):
        by_id = {}
        for reply in REPLIES.validate_python(value):
            if reply.request_id in by_id:
                raise ValueError("Duplicate request_id: " + reply.request_id)
            by_id[reply.request_id] = reply
        foreign = sorted(set(by_id) - {request.request_id for request in self.requests})
        if foreign and not self.record_foreign:
            raise ValueError("Unknown request_id: " + ", ".join(foreign))
        rows = [self.check(request, by_id.get(request.request_id)) for request in self.requests]
        rows += [{"request_id": key, "status": FOREIGN_ID, "raw_reply": by_id[key].raw_reply} for key in foreign]
        tally = Counter(row["status"] for row in rows)
        names = (*KIT_STATUSES, self.missing_status, *self.statuses, *((FOREIGN_ID,) if self.record_foreign else ()))
        return {"counts": {"total": len(rows), **{name.lower(): tally[name] for name in dict.fromkeys(names)}},
                "rows": rows, "live_trial": "PENDING", "evidence": "CALLER_SUPPLIED_UNAUTHENTICATED",
                "provider_calls": 0}

    def main(self, argv=None):
        parser = argparse.ArgumentParser(description=self.description)
        parser.add_argument("--replies", type=Path, help=f"UTF-8 JSON reply list, at most {MAX_INPUT_BYTES} bytes")
        args = parser.parse_args(argv)
        try:
            result = self.exports() if args.replies is None else self.evaluate(read_capped(args.replies))
        except (OSError, ValueError, RecursionError) as error:
            print(json.dumps({"status": "INVALID", "reason": str(error)}, ensure_ascii=True))
            return 2
        print(json.dumps(result, sort_keys=True))
        return 0


def assess(pilot, codes, artefacts, exports_stdout, run_path):
    """Explicit checks over one replay's artefacts; counts come from the pilot's declared request matrix."""
    junit_path, coverage_path = Path(artefacts) / "junit.xml", Path(artefacts) / "coverage.json"
    checks = {"exit_codes_zero": codes == [0, 0, 0]}
    cases = ET.parse(junit_path).getroot().findall(".//testcase") if junit_path.is_file() else []
    clean = [case for case in cases if not any(case.find(tag) is not None for tag in ("failure", "error", "skipped"))]
    mutants = sum(case.attrib["name"].startswith(MUTANT_TEST_PREFIX) for case in clean)
    checks.update(tests_ran=bool(cases), tests_clean=len(clean) == len(cases), mutants_killed=mutants > 0)
    files = json.loads(coverage_path.read_bytes())["files"] if coverage_path.is_file() else {}
    percent = {Path(name).name: data["summary"]["percent_covered"] for name, data in files.items()}
    checks["run_py_coverage"] = percent.get(Path(run_path).name, 0.0) >= MIN_COVERAGE
    try:
        exported = json.loads(exports_stdout)
    except ValueError:
        exported = {}
    declared = [request.request_id for request in pilot.requests]
    rows = exported.get("requests", [])
    checks["requests_match_matrix"] = [row["request"]["request_id"] for row in rows] == declared
    checks["requests_not_run"] = all(row["trial_status"] == "NOT_RUN" for row in rows)
    checks["live_trial_pending"] = exported.get("live_trial") == "PENDING" and exported.get("provider_calls") == 0
    return {"pilot_id": pilot.pilot_id, "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "tests": len(cases), "mutants_killed": mutants, "requests": len(declared), "coverage_percent": percent,
            "exit_codes": codes, "provider_calls": 0}


def check_pilot(here, pilot, python=sys.executable):
    """Replay one pilot's tests under branch coverage and its export in a temporary directory; 0 on PASS."""
    here = Path(here).resolve()
    run_path, kit_path = here / "run.py", here.parent / "pilot_reply_kit.py"
    with tempfile.TemporaryDirectory(prefix="pilot_check_") as temporary:
        tmp = Path(temporary)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", NO_COLOR="1",
                   COVERAGE_FILE=str(tmp / "coverage.data"))
        commands = [
            [python, "-B", "-m", "coverage", "run", "--branch", f"--include={run_path},{kit_path}", "-m", "pytest",
             str(here / "tests"), "-q", "-p", "no:cacheprovider", "-c", str(here / "pytest.ini"), "--rootdir",
             str(here), "--basetemp", str(tmp / "pytest"), "--junitxml", str(tmp / "junit.xml"), "--color=no"],
            [python, "-B", "-m", "coverage", "json", "-o", str(tmp / "coverage.json")],
            [python, "-B", str(run_path)],
        ]
        processes = [subprocess.run(command, cwd=here, env=env, capture_output=True, check=False) for command in commands]
        report = assess(pilot, [process.returncode for process in processes], tmp, processes[2].stdout, run_path)
        if report["status"] != "PASS":
            report["stdout_tail"] = processes[0].stdout.decode("utf-8", "replace")[-2000:]
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1
