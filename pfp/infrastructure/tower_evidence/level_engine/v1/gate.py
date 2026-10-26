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

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

PY = sys.executable
MIN_TESTS = 90
COVERAGE_LINE = 95.0
COVERAGE_BRANCH = 95.0
FORBIDDEN_LEAN = re.compile(r"\bsorry\b|\badmit\b|\bunsafe\b|\bpartial\b|\bnative_decide\b|^\s*axiom\s", re.M)
# Sealed entry points no engine source may name: the tree builder and the
# closure orbits (growth), and the automorphism and pair-orbit routines, whose
# use along a history is the running rung's question (``history_symmetry``).
FORBIDDEN_SEALED = re.compile(r"\b(build_tree|closure_challenge_orbits|automorphisms|pair_orbits)\b")
EMBARGO_DIGEST = "db0305cb640326aecbd96bc0e7484abe60f4237a5a896b2ec0554ddafa11fd23"
RECORD_DIRS = ("bundles", "bindings/generated")


def _run(argv: list[str]) -> int:
    print(f"  $ {' '.join(argv)}", flush=True)
    proc = subprocess.run(argv, cwd=ROOT, check=False)
    print(f"  exit {proc.returncode}", flush=True)
    return proc.returncode


def step_pins() -> bool:
    a = _run([PY, "tools/vendor.py", "--check"])
    b = _run([PY, "tools/bind.py", "--check"])
    return a == 0 and b == 0


def step_tests() -> bool:
    for f in (ROOT / ".coverage", ROOT / "coverage.json"):
        f.unlink(missing_ok=True)
    collected = subprocess.run([PY, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT,
                               capture_output=True, text=True, check=False)
    m = re.search(r"(\d+) tests? collected", collected.stdout)
    per_file = re.findall(r"^\S+\.py: (\d+)$", collected.stdout, re.M)
    n = int(m.group(1)) if m else sum(int(x) for x in per_file)
    print(f"  collected {n} tests (declared minimum {MIN_TESTS})")
    rc = _run([PY, "-m", "coverage", "run", "-m", "pytest", "-q", "-p", "no:cacheprovider"])
    rc2 = _run([PY, "-m", "coverage", "json", "-q", "-o", "coverage.json"])
    if rc != 0 or rc2 != 0:
        return False
    totals = json.loads((ROOT / "coverage.json").read_text(encoding="utf-8"))["totals"]
    line = 100.0 * totals["covered_lines"] / max(totals["num_statements"], 1)
    branch = 100.0 * totals["covered_branches"] / max(totals["num_branches"], 1)
    print(f"  line coverage {line:.2f}% (min {COVERAGE_LINE}), branch coverage {branch:.2f}% (min {COVERAGE_BRANCH})")
    return n >= MIN_TESTS and line >= COVERAGE_LINE and branch >= COVERAGE_BRANCH


def step_types() -> bool:
    return _run([PY, "-m", "mypy"]) == 0


def step_lean() -> bool:
    files = [p for p in ROOT.rglob("*.lean") if not {"vendor", ".lake", "_scratch"} & set(p.relative_to(ROOT).parts)]
    bad = [p for p in files if FORBIDDEN_LEAN.search(p.read_text(encoding="utf-8"))]
    print(f"  {len(files)} Lean files outside vendor/; {len(bad)} with a forbidden token")
    for p in bad:
        print(f"  FORBIDDEN TOKEN: {p.relative_to(ROOT).as_posix()}")
    gen = _run([PY, "tools/lean_gen.py", "--check"])
    print("  $ lake build")
    proc = subprocess.run(["lake", "build"], cwd=ROOT, capture_output=True, text=True, check=False)
    (ROOT / "_scratch").mkdir(exist_ok=True)
    (ROOT / "_scratch" / "lake_build.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    print(f"  exit {proc.returncode}")
    if proc.returncode != 0:
        print("  LEAN_BUILD_FAILED; the log is _scratch/lake_build.log")
        for line in (proc.stdout + proc.stderr).splitlines():
            if "error" in line:
                print(f"    {line.strip()[:200]}")
        return False
    audit = _run([PY, "tools/lean_audit.py"])
    return not bad and gen == 0 and audit == 0


def _tree(base: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for d in RECORD_DIRS:
        for p in sorted((base / d).rglob("*")):
            if p.is_file():
                out[p.relative_to(base).as_posix()] = p.read_bytes()
    return out


def step_records() -> bool:
    with tempfile.TemporaryDirectory(dir=ROOT / "_scratch" if (ROOT / "_scratch").exists() else None) as tmp:
        rc = _run([PY, "run_bootstrap.py", "--out", tmp])
        if rc != 0:
            return False
        fresh, committed = _tree(Path(tmp)), _tree(ROOT)
    missing = sorted(set(fresh) - set(committed))
    extra = sorted(set(committed) - set(fresh))
    changed = sorted(k for k in set(fresh) & set(committed) if fresh[k] != committed[k])
    for k in missing:
        print(f"  RECORD NOT COMMITTED: {k}")
    for k in extra:
        print(f"  RECORD NOT REGENERATED: {k}")
    for k in changed:
        print(f"  RECORD DRIFT: {k}")
    print(f"  {len(fresh)} records regenerated")
    return not (missing or extra or changed)


def step_lifts() -> bool:
    return _run([PY, "tools/lift_check.py"]) == 0


def step_hygiene() -> bool:
    from engine.hygiene import report, scan

    counts = scan()
    total, lines = report(counts)
    for line in lines:
        print(f"  {line}")
    print(f"  {len(counts)} files scanned, {total} hits (count only)")
    return total == 0


def step_embargo() -> bool:
    from engine.guards import embargo_digest

    ok = True
    if embargo_digest() != EMBARGO_DIGEST:
        print("  EMBARGO LIST DRIFT: the pinned digest does not match")
        ok = False
    sources = [p for layer in ("engine", "outward", "payload", "tools") for p in (ROOT / layer).rglob("*.py")]
    sources += [ROOT / "run_bootstrap.py"]
    for p in sources:
        if FORBIDDEN_SEALED.search(p.read_text(encoding="utf-8")):
            print(f"  EMBARGOED ENTRY POINT NAMED: {p.relative_to(ROOT).as_posix()}")
            ok = False
    print(f"  {len(sources)} sources scanned for embargoed sealed entry points")
    return ok


def _git(*args: str, repo: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)


def _ancestor(a: str, b: str, repo: Path = ROOT) -> bool:
    return _git("merge-base", "--is-ancestor", a, b, repo=repo).returncode == 0


def _check_imported(name: str, rec: dict[str, str]) -> bool:
    """An imported round's freeze order, checked in the repository where it
    happened; the imported files must equal that repository's files at its head."""
    src = Path(rec["source_repo"])
    if not (src / ".git").exists():
        print(f"  {name}: NOT CHECKABLE: the source repository {src} is absent")
        return False
    p, s_, r, head = rec["predictions_frozen"], rec["specs_frozen"], rec["first_records"], rec["head"]
    order = _ancestor(p, s_, src) and _ancestor(s_, r, src) and p != s_ != r and _ancestor(r, head, src)
    same = True
    # The round's frozen files are the ones the source holds at its head: its
    # predictions and its payloads' expectations.  A payload added by a later
    # round is not part of it.
    listed = subprocess.run(["git", "-C", str(src), "ls-tree", "-r", "--name-only", head, "payload"],
                            capture_output=True, text=True, check=False).stdout.split()
    expects = sorted(rel for rel in listed if rel.endswith("/expect.json"))
    if not expects:
        print(f"  {name}: NO FROZEN EXPECTATIONS LISTED AT THE SOURCE HEAD")
        same = False
    for rel in ["predictions/FROZEN.json"] + expects:
        shown = subprocess.run(["git", "-C", str(src), "show", f"{head}:{rel}"], capture_output=True, check=False)
        local = ROOT / rel
        if shown.returncode != 0 or not local.is_file() or shown.stdout != local.read_bytes():
            print(f"  {name}: FROZEN FILE DIFFERS FROM THE SOURCE: {rel}")
            same = False
    print(f"  {name}: predictions {p[:8]} < specs {s_[:8]} < first records {r[:8]} in {src.name}: {order}")
    return order and same


def _check_local_round(path: Path) -> bool:
    """A round frozen here: its predictions commit changes no record, and the
    records it predicts arrive in a later commit."""
    rel = path.relative_to(ROOT).as_posix()
    added = _git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split()
    if not added:
        print(f"  {rel}: NOT CHECKABLE: not committed")
        return False
    p = added[-1]
    touched = _git("show", "--name-only", "--format=", p).stdout.split()
    leaks = [t for t in touched if "/bundles/" in f"/{t}" or "/bindings/generated/" in f"/{t}"]
    later = _git("log", "--format=%H", f"{p}..HEAD", "--", "bundles").stdout.split()
    ok = not leaks and bool(later)
    print(f"  {rel}: frozen at {p[:8]}, no record in that commit: {not leaks}; records after it: {bool(later)}")
    return ok


def step_freeze() -> bool:
    hist = json.loads((ROOT / "HISTORY.json").read_text(encoding="utf-8"))
    ok = all(_check_imported(name, rec) for name, rec in sorted(hist["imported_rounds"].items()))
    for path in sorted((ROOT / "predictions").glob("FROZEN_*.json")):
        ok = _check_local_round(path) and ok
    return ok


def step_preflight() -> bool:
    ok = True
    for p in sorted((ROOT / "bindings" / "generated" / "checker_input").glob("*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        from outward.bundles import intake_ok

        positive = next(f["input"] for f in doc["fixtures"] if f["target_role"] == "pos")
        if not intake_ok(doc["harness_intake"], positive):
            print(f"  INTAKE DOES NOT REFUSE THE PROBE BATTERY: {p.name}")
            ok = False
        for name, why in sorted(doc["probes_left_to_target_schema"].items()):
            print(f"  {p.name}: probe {name} left to the target schema ({why})")
        print(f"  {p.name}: target {doc['target']}")
    grades = json.loads((ROOT / "bindings" / "generated" / "grade_table.json").read_text(encoding="utf-8"))
    for row in grades["rows"]:
        if row["status"] not in ("EXPECTED", "UNRESOLVED"):
            print(f"  STATUS {row['status']}: {row['challenge_id']}")
            ok = False
    return ok


STEPS: dict[str, Callable[[], bool]] = {
    "pins": step_pins,
    "tests": step_tests,
    "types": step_types,
    "lean": step_lean,
    "records": step_records,
    "lifts": step_lifts,
    "hygiene": step_hygiene,
    "embargo": step_embargo,
    "freeze": step_freeze,
    "preflight": step_preflight,
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--step", action="append", choices=sorted(STEPS))
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    chosen = args.step or list(STEPS)
    if args.list:
        print("\n".join(chosen))
        return 0
    results: list[tuple[str, bool]] = []
    for name in chosen:
        print(f"== {name}", flush=True)
        try:
            ok = STEPS[name]()
        except Exception as exc:  # noqa: BLE001 - a crashing step is a failing step, named
            print(f"  STEP RAISED: {type(exc).__name__}: {exc}")
            ok = False
        results.append((name, ok))
    print("\n== summary")
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main())
