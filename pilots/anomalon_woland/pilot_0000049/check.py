"""One focused replay; compact logs only, no delivery or audit framework.

Exit 0 when every gate holds, 1 with a printed reason otherwise. Logs go to a temporary directory
that is removed afterwards unless --out names a new directory to keep them in.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
TEST = HERE / "tests/repair/test_pilot24_bounded_repair.py"
MUTANTS = 5
MIN_COVERAGE = 98.0


def expected_output(actual):
    return actual["status"] == "ACCEPTED" and actual["answer"] == 42 and actual["mock_calls"] == 2


def commands(output, temporary):
    return [
        [sys.executable, "-B", "-m", "coverage", "run", "--rcfile", str(HERE / "coverage.ini"), "-m", "pytest", "-q",
         "-p", "no:cacheprovider", "-c", str(HERE / "pytest.ini"), str(TEST),
         "--basetemp", str(temporary / "pytest"), "--junitxml", str(output / "junit.xml")],
        [sys.executable, "-B", "-m", "coverage", "json", "--rcfile", str(HERE / "coverage.ini"), "-o", str(output / "coverage.json")],
        [sys.executable, "-B", str(HERE / "run.py")],
    ]


def verify(output, codes):
    """Return the first failed gate as text, or None when every gate holds."""
    if codes != [0, 0, 0]:
        index = next(i for i, code in enumerate(codes) if code)
        tail = (output / f"stderr_{index}.bin").read_bytes()[-2000:] + (output / f"stdout_{index}.bin").read_bytes()[-2000:]
        return f"command {index} exited {codes[index]}: " + tail.decode("utf-8", "replace")
    cases = ET.parse(output / "junit.xml").getroot().findall(".//testcase")
    if any(case.find(name) is not None for case in cases for name in ("failure", "error", "skipped")):
        return "a test failed, errored or was skipped"
    mutants = sum(case.attrib["name"].startswith("test_compiled_semantic_mutants[") for case in cases)
    if mutants != MUTANTS:
        return f"expected {MUTANTS} killed mutants, found {mutants}"
    coverage = json.loads((output / "coverage.json").read_bytes())
    measured = {str((HERE / name).resolve()) for name in coverage["files"]}
    if measured != {str(HERE / "run.py")}:
        return f"coverage measured {sorted(measured)}, expected run.py only"
    totals = coverage["totals"]
    if totals["excluded_lines"] != 0:
        return f"{totals['excluded_lines']} lines excluded from coverage"
    if totals["percent_covered"] < MIN_COVERAGE:
        return f"coverage {totals['percent_covered']:.2f}% is below {MIN_COVERAGE}%"
    try:
        matches = expected_output(json.loads((output / "stdout_2.bin").read_bytes()))
    except (ValueError, KeyError, TypeError) as error:
        return f"run.py output is not the expected JSON: {error!r}"
    if not matches:
        return "run.py default output differs from the expected shape"
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="New directory that keeps the logs; default is a removed temporary directory")
    args = parser.parse_args(argv)
    temporary = Path(tempfile.mkdtemp(prefix="p24_"))
    try:
        output = args.out if args.out is not None else temporary / "output"
        output.mkdir(parents=True, exist_ok=False)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                   COVERAGE_FILE=str(output / "coverage.data"))
        codes = []
        for index, command in enumerate(commands(output, temporary)):
            (output / f"command_{index}.json").write_text(json.dumps(command), encoding="utf-8")
            process = subprocess.run(command, cwd=HERE, env=env, capture_output=True, check=False)
            (output / f"stdout_{index}.bin").write_bytes(process.stdout)
            (output / f"stderr_{index}.bin").write_bytes(process.stderr)
            codes.append(process.returncode)
        (output / "return_codes.json").write_text(json.dumps(codes), encoding="utf-8")
        reason = verify(output, codes)
        if reason is not None:
            print(json.dumps({"status": "FAILED", "reason": reason}))
            return 1
        coverage = json.loads((output / "coverage.json").read_bytes())
        report = {"status": "PASSED", "tests": len(ET.parse(output / "junit.xml").getroot().findall(".//testcase")),
                  "mutations": MUTANTS, "coverage_percent": coverage["totals"]["percent_covered"], "provider_calls": 0,
                  "output": str(output) if args.out is not None else None}
        (output / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report))
        return 0
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
