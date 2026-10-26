"""The harness gate.  Run before every harness merge:

    python gate.py                 # every step
    python gate.py --step records  # one step (repeatable)
    python gate.py --list

Each step prints its own real exit code on its own line; nothing is piped
through a filter.  The gate is green only when every selected step passes.

AuthorityEffect: None
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

if __name__ == "__main__":
    import runpy

    sys.argv = [sys.argv[0], "gate", *sys.argv[1:]]
    raise SystemExit(runpy.run_module(
        "omega_engine_operations.infrastructure.level_engine_ports",
        run_name="__main__",
    ))

from omega_engine_operations.domain.level_engine_context import (
    LevelEngineOperationPorts,
    current_context,
)

from .dispatch import command, environment

ROOT = current_context().runtime_root
TEST_FILES: list[Path] = []

PY = sys.executable
MIN_TESTS = 90
COVERAGE_LINE = 95.0
COVERAGE_BRANCH = 95.0
FORBIDDEN_LEAN = re.compile(r"\bsorry\b|\badmit\b|\bunsafe\b|\bpartial\b|\bnative_decide\b|^\s*axiom\s", re.M)
# Sealed entry points no engine source may name: the tree builder and the
# closure orbits (growth), and the automorphism and pair-orbit routines, whose
# use along a history is the running rung's question (``history_symmetry``).
FORBIDDEN_SEALED = re.compile(r"\b(build_tree|closure_challenge_orbits|automorphisms|pair_orbits)\b")
EMBARGO_DIGEST = "f71756beac69fb9b2c3181331ed56f99db6f7adf472dfe9d0d0be1e3cdb346a4"
RECORD_DIRS = ("bundles", "bindings/generated")


def _run(argv: list[str]) -> int:
    mapping = {"tools/vendor.py":"vendor", "tools/bind.py":"bind", "tools/lift_check.py":"lift_check", "run_bootstrap.py":"bootstrap"}
    if len(argv)>1 and argv[1] in mapping:
        argv = command(mapping[argv[1]], argv[2:])
    print(f"  $ {' '.join(argv)}", flush=True)
    proc = subprocess.run(argv, cwd=current_context().repository_root, check=False, env=environment())
    print(f"  exit {proc.returncode}", flush=True)
    return proc.returncode


def step_pins() -> bool:
    a = _run([PY, "tools/vendor.py", "--check"])
    b = _run([PY, "tools/bind.py", "--check"])
    return a == 0 and b == 0


def step_tests() -> bool:
    ctx = current_context()
    repo = ctx.require_repository()
    chosen = sorted((repo / "omega_engine_pfp/tests/level_engine").rglob("test_*.py"))
    if not chosen:
        raise ValueError("LEVEL_ENGINE_TESTS_UNAVAILABLE")
    count = 0
    with tempfile.TemporaryDirectory(prefix="level-engine-coverage-") as temporary:
        coverage = Path(temporary) / ".coverage"
        report = Path(temporary) / "coverage.json"
        codes = []
        for offset in range(0, len(chosen), 3):
            batch = list(map(str, chosen[offset:offset+3]))
            collection = subprocess.run([PY, "-B", "-m", "pytest", "-o", "addopts=", "--collect-only", "-q", *batch],
                                        cwd=repo, env=environment(), text=True, capture_output=True, check=False)
            matches = re.findall(r"(\d+) tests? collected", collection.stdout)
            count += int(matches[-1]) if matches else sum(map(int,re.findall(r"^\S+\.py: (\d+)$",collection.stdout,re.M)))
            codes.append(collection.returncode)
            codes.append(_run([PY, "-B", "-m", "coverage", "run", "--append", "--branch",
                               "--data-file",str(coverage), "--source",str(Path(__file__).parent / "research_engine")+","+str(ROOT/"outward"),
                               "-m", "pytest", "-o", "addopts=", "-q", "-p", "no:cacheprovider", *batch]))
        report_code = _run([PY, "-m", "coverage", "json", "--data-file",str(coverage), "-q", "-o",str(report)])
        if report_code or not report.is_file():
            return False
        totals = json.loads(report.read_text(encoding="utf-8"))["totals"]
        line = 100.0 * totals["covered_lines"] / max(totals["num_statements"], 1)
        branch = 100.0 * totals["covered_branches"] / max(totals["num_branches"], 1)
    print(f"  collected {count} tests (minimum {MIN_TESTS}); line {line:.2f}% (minimum {COVERAGE_LINE}); branch {branch:.2f}% (minimum {COVERAGE_BRANCH})")
    return all(code == 0 for code in codes) and count >= MIN_TESTS and line >= COVERAGE_LINE and branch >= COVERAGE_BRANCH


def step_tests_scoped() -> bool:
    if not TEST_FILES:
        raise ValueError("SCOPED_TEST_FILES_REQUIRED")
    print("  SCOPED_TESTS_ONLY: full test-count and coverage gate not evaluated")
    return all(_run([PY,"-B","-m","pytest","-o","addopts=","-q","-p","no:cacheprovider",*map(str,TEST_FILES[offset:offset+3])]) == 0
               for offset in range(0,len(TEST_FILES),3))


def step_types() -> bool:
    import os
    ctx = current_context()
    vendor = ctx.require_vendor()
    env = environment()
    env["MYPYPATH"] = os.pathsep.join((str(vendor/"code"),str(vendor/"research/partial_decide")))
    # Check every migrated research module explicitly; unrelated package imports
    # supply their types without turning this gate into a repository-wide audit.
    arguments = [PY,"-B","-m","mypy","--strict","--python-version","3.14",
                 "--explicit-package-bases","--follow-imports=silent",
                 "--exclude", "tests/level_engine/(checkers/|reach_draft/checker_L002.py)",
                 str(ROOT/"outward"),str(ROOT/"payload"),
                 str(ROOT/"context.py"),str(ROOT/"vendor_loading.py"),str(ROOT/"runner.py"),
                 str(ctx.require_repository()/"omega_engine_pfp/domain/tower/level_engine.py"),
                 str(ctx.require_repository()/"omega_engine_pfp/infrastructure/tower_evidence/level_engine/resolver.py"),
                 str(ctx.require_repository()/"omega_engine_pfp/infrastructure/tower_research/reach/resources.py"),
                 str(ctx.require_repository()/"omega_engine_pfp/tests/level_engine"),
                 str(ctx.require_repository()/"omega_engine_operations/use_cases/level_engine"),
                 str(ctx.require_repository()/"omega_engine_pfp/entrypoints/cli/level_engine_commands.py")]
    print("  $ " + " ".join(arguments),flush=True)
    result = subprocess.run(arguments,cwd=ctx.repository_root,env=env,check=False)
    print(f"  exit {result.returncode}",flush=True)
    return result.returncode == 0


def step_lean() -> bool:
    ctx = current_context()
    if ctx.lean_root is None or ctx.lean_root.resolve() == (ctx.evidence_root/"v2/lean/sources").resolve():
        raise ValueError("LEAN_RESOURCES_UNAVAILABLE: supply --lean-root")
    files = list(ctx.lean_root.glob("*.lean"))
    if not files:
        raise ValueError("LEAN_RESOURCES_UNAVAILABLE: no certificate sources")
    bad = [p for p in files if FORBIDDEN_LEAN.search(p.read_text(encoding="utf-8"))]
    for path in bad:
        print(f"  FORBIDDEN TOKEN: {path.name}")
    codes = [subprocess.run(command(name,args), cwd=ctx.repository_root, env=environment(), check=False).returncode
             for name,args in (("lean_gen",["--check"]),("lean_build",[]),("lean_audit",[]))]
    return not bad and all(code == 0 for code in codes)


def _tree(base: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for d in RECORD_DIRS:
        for p in sorted((base / d).rglob("*")):
            if p.is_file():
                out[p.relative_to(base).as_posix()] = p.read_bytes()
    return out


def step_records() -> bool:
    with tempfile.TemporaryDirectory(prefix="level-engine-records-") as tmp:
        output = Path(tmp) / "records"
        rc = _run([PY, "run_bootstrap.py", "--out", str(output)])
        if rc:
            return False
        ctx = current_context()
        fresh = _tree(output)
        committed = _tree(ctx.output_root or ctx.evidence_root / "v2")
    differences = sorted(k for k in fresh.keys() | committed.keys() if fresh.get(k) != committed.get(k))
    for name in differences:
        print(f"  RECORD DRIFT: {name}")
    print(f"  {len(fresh)} records regenerated")
    return bool(fresh) and not differences


def step_lifts() -> bool:
    return _run([PY, "tools/lift_check.py"]) == 0


def step_hygiene() -> bool:
    from omega_engine_operations.use_cases.level_engine.research_engine.hygiene import report, scan

    counts = scan()
    total, lines = report(counts)
    for line in lines:
        print(f"  {line}")
    print(f"  {len(counts)} files scanned, {total} hits (count only)")
    return total == 0


def step_embargo() -> bool:
    from omega_engine_operations.use_cases.level_engine.research_engine.guards import embargo_digest

    ok = True
    if embargo_digest() != EMBARGO_DIGEST:
        print("  EMBARGO LIST DRIFT: the pinned digest does not match")
        ok = False
    sources = [p for layer in ("outward", "payload", "tools") for p in (ROOT / layer).rglob("*.py")]
    operations_root = Path(__file__).parent
    # As in the original gate, exclude the scanner itself, which declares
    # the forbidden names; scan the relocated bootstrap and every helper.
    sources += [path for path in operations_root.rglob("*.py") if path.name != "gate.py" and "__pycache__" not in path.parts]
    for p in sources:
        if FORBIDDEN_SEALED.search(p.read_text(encoding="utf-8")):
            print(f"  EMBARGOED ENTRY POINT NAMED: {p}")
            ok = False
    print(f"  {len(sources)} sources scanned for embargoed sealed entry points")
    return ok


from .freeze import step_freeze


def step_preflight(ports: LevelEngineOperationPorts | None = None) -> bool:
    if ports is None:
        raise ValueError("LEVEL_ENGINE_PORTS_REQUIRED")
    ok = True
    for p in sorted(current_context().current_path("bindings/generated/checker_input").glob("*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        positive = next(f["input"] for f in doc["fixtures"] if f["target_role"] == "pos")
        if not ports.bundles.intake_ok(doc["harness_intake"], positive):
            print(f"  INTAKE DOES NOT REFUSE THE PROBE BATTERY: {p.name}")
            ok = False
        for name, why in sorted(doc["probes_left_to_target_schema"].items()):
            print(f"  {p.name}: probe {name} left to the target schema ({why})")
        print(f"  {p.name}: target {doc['target']}")
    grades = json.loads(current_context().current_path("bindings/generated/grade_table.json").read_text(encoding="utf-8"))
    for row in grades["rows"]:
        if row["status"] not in ("EXPECTED", "UNRESOLVED"):
            print(f"  STATUS {row['status']}: {row['challenge_id']}")
            ok = False
    return ok


STEPS: dict[str, Callable[..., bool]] = {
    "pins": step_pins,
    "tests": step_tests,
    "tests-scoped": step_tests_scoped,
    "types": step_types,
    "lean": step_lean,
    "records": step_records,
    "lifts": step_lifts,
    "hygiene": step_hygiene,
    "embargo": step_embargo,
    "freeze": step_freeze,
    "preflight": step_preflight,
}


def main(argv: list[str] | None = None, ports: LevelEngineOperationPorts | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--step", action="append", choices=sorted(STEPS))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--test-file", type=Path, action="append", default=[])
    args = ap.parse_args(argv)
    global TEST_FILES
    TEST_FILES = args.test_file
    chosen = args.step or [name for name in STEPS if name != "tests-scoped"]
    if args.test_file and "tests-scoped" not in chosen:
        ap.error("--test-file requires --step tests-scoped; it does not run the full coverage gate")
    if args.list:
        print("\n".join(chosen))
        return 0
    results: list[tuple[str, bool]] = []
    for name in chosen:
        print(f"== {name}", flush=True)
        try:
            ok = step_preflight(ports) if name == "preflight" else STEPS[name]()
        except Exception as exc:  # noqa: BLE001 - a crashing step is a failing step, named
            print(f"  STEP RAISED: {type(exc).__name__}: {exc}")
            ok = False
        results.append((name, ok))
    print("\n== summary")
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    return 0 if all(ok for _, ok in results) else 1
