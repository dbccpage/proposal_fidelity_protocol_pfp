"""Historical freeze-order checks; no active record is rewritten."""
import json
import subprocess
from pathlib import Path

from omega_engine_operations.domain.level_engine_context import (
    current_context,
)


def _git(*args: str, repo: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo or current_context().require_repository()), *args], capture_output=True, text=True, check=False)


def _ancestor(a: str, b: str, repo: Path | None = None) -> bool:
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
        local = current_context().historical_path(rel)
        if shown.returncode != 0 or not local.is_file() or shown.stdout != local.read_bytes():
            print(f"  {name}: FROZEN FILE DIFFERS FROM THE SOURCE: {rel}")
            same = False
    print(f"  {name}: predictions {p[:8]} < specs {s_[:8]} < first records {r[:8]} in {src.name}: {order}")
    return order and same


def _check_local_round(path: Path) -> bool:
    """A round frozen here: its predictions commit changes no record, and the
    records it predicts arrive in a later commit."""
    rel = "research/level_engine/" + path.relative_to(current_context().historical_path("predictions").parent).as_posix()
    # Full history: a round built on a branch reaches main through a merge
    # whose result no longer holds the pre-relocation path, and the default
    # simplification would drop the branch that added it.
    added = _git("log", "--full-history", "--diff-filter=A", "--format=%H", "--", rel).stdout.split()
    if not added:
        print(f"  {rel}: NOT CHECKABLE: not committed")
        return False
    p = added[-1]
    touched = _git("show", "--name-only", "--format=", p).stdout.split()
    leaks = [t for t in touched if "/bundles/" in f"/{t}" or "/bindings/generated/" in f"/{t}"]
    later = _git("log", "--full-history", "--format=%H", f"{p}..HEAD", "--", "research/level_engine/bundles").stdout.split()
    ok = not leaks and bool(later)
    print(f"  {rel}: frozen at {p[:8]}, no record in that commit: {not leaks}; records after it: {bool(later)}")
    return ok


def step_freeze() -> bool:
    hist = json.loads(current_context().governance_path("HISTORY.json").read_text(encoding="utf-8"))
    ok = all(_check_imported(name, rec) for name, rec in sorted(hist["imported_rounds"].items()))
    for path in sorted(current_context().historical_path("predictions").glob("FROZEN_*.json")):
        ok = _check_local_round(path) and ok
    return ok

