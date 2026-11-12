"""One focused replay; the measured production scope is run.py only.

Exit 0 when every gate holds, 1 with a printed reason otherwise. Logs go to a temporary directory
that is removed afterwards unless --out names a new directory to keep them in.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Literal
import xml.etree.ElementTree as ET

from pydantic import BaseModel, ConfigDict, Field
import yaml

HERE = Path(__file__).resolve().parent
TEST = HERE / "tests/glyph_packet/test_new002_glyph_packet.py"
TESTS = 77
MUTATIONS = 15
MIN_COVERAGE = 98.0


class CheckResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    pilot_id: Literal["pilot_0000048"]
    runner_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    tests_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    tests_passed: Literal[77]
    mutations_killed: Literal[15]
    coverage_percent: float = Field(ge=MIN_COVERAGE, le=100)
    elapsed_seconds: float = Field(ge=0)
    default_output: str
    provider_calls: Literal[0]
    cost_microusd: Literal[0]


def commands(output, scratch):
    return [
        [sys.executable, "-B", "-m", "coverage", "run", "--rcfile=coverage.ini", "-m", "pytest",
         "-c", "pytest.ini", str(TEST), "-q", "-p", "no:cacheprovider", "--import-mode=importlib",
         "--basetemp", str(scratch), "--junitxml", str(output / "tests.xml")],
        [sys.executable, "-B", "-m", "coverage", "json", "--rcfile=coverage.ini", "-o", str(output / "coverage.json")],
        [sys.executable, "-B", str(HERE / "run.py"), "--output-root", str(output / "default_run")],
    ]


def verify(output, scratch, codes):
    """Return the first failed gate as text, or None when every gate holds."""
    if any(codes):
        index = next(i for i, code in enumerate(codes) if code)
        tail = (output / f"{index}.stderr").read_bytes()[-2000:] + (output / f"{index}.stdout").read_bytes()[-2000:]
        return f"command {index} exited {codes[index]}: " + tail.decode("utf-8", "replace")
    suites = list(ET.parse(output / "tests.xml").getroot().iter("testsuite"))
    tests = sum(int(s.attrib["tests"]) for s in suites)
    if tests != TESTS:
        return f"expected {TESTS} tests, found {tests}"
    if any(int(s.attrib.get(k, 0)) for s in suites for k in ("errors", "failures", "skipped")):
        return "a test failed, errored or was skipped"
    coverage = json.loads((output / "coverage.json").read_bytes())
    if len(coverage["files"]) != 1 or coverage["totals"]["excluded_lines"] != 0:
        return f"coverage scope is {sorted(coverage['files'])} with {coverage['totals']['excluded_lines']} excluded lines"
    if coverage["totals"]["percent_covered"] < MIN_COVERAGE:
        return f"coverage {coverage['totals']['percent_covered']:.2f}% is below {MIN_COVERAGE}%"
    mutations = json.loads((scratch / "test_compiled_mutations0/mutations.json").read_bytes())
    if len(mutations) != MUTATIONS or not all(m["killed"] for m in mutations):
        return f"expected {MUTATIONS} killed mutations, found {sum(m['killed'] for m in mutations)} of {len(mutations)}"
    try:
        status = json.loads((output / "2.stdout").read_bytes())["status"]
    except (ValueError, KeyError, TypeError) as error:
        return f"run.py output is not the expected JSON: {error!r}"
    if status != "PRESERVED":
        return f"run.py default status is {status}, expected PRESERVED"
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="New directory that keeps the logs; default is a removed temporary directory")
    args = parser.parse_args(argv)
    start = time.perf_counter()
    temporary = Path(tempfile.mkdtemp(prefix="pfp23-"))
    try:
        output = args.out if args.out is not None else temporary / "output"
        output.mkdir(parents=True, exist_ok=False)
        scratch = temporary / "pytest"
        env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1",
                   COVERAGE_FILE=str(output / ".coverage"))
        (output / "commands.json").write_text(json.dumps(commands(output, scratch), indent=2), encoding="utf-8")
        codes = []
        for index, command in enumerate(commands(output, scratch)):
            child = subprocess.run(command, cwd=HERE, env=env, capture_output=True, check=False)
            (output / f"{index}.stdout").write_bytes(child.stdout)
            (output / f"{index}.stderr").write_bytes(child.stderr)
            codes.append(child.returncode)
        reason = verify(output, scratch, codes)
        if reason is not None:
            print(json.dumps({"status": "FAILED", "reason": reason}))
            return 1
        mutations = json.loads((scratch / "test_compiled_mutations0/mutations.json").read_bytes())
        (output / "mutations.json").write_text(json.dumps(mutations, indent=2), encoding="utf-8")
        coverage = json.loads((output / "coverage.json").read_bytes())
        process = json.loads((output / "2.stdout").read_bytes())
        result = CheckResult(pilot_id=HERE.name, runner_sha256=hashlib.sha256((HERE / "run.py").read_bytes()).hexdigest(),
                             tests_sha256=hashlib.sha256(TEST.read_bytes()).hexdigest(), tests_passed=TESTS,
                             mutations_killed=MUTATIONS, coverage_percent=float(coverage["totals"]["percent_covered"]),
                             elapsed_seconds=time.perf_counter()-start, default_output=process["output"],
                             provider_calls=0, cost_microusd=0)
        data = result.model_dump(mode="json")
        (output / "result.json").write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")
        (output / "result.yaml").write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")
        print(json.dumps({"status": "PASSED", "output": str(output) if args.out is not None else None, **data}))
        return 0
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
