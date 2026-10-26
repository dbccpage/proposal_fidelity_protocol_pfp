"""Replay the level records through the receiving side and regenerate its
reach ledger.  The one command to run once checkers of record exist.

    python tools/reach_replay.py              # replay, store receipts, regenerate the ledger
    python tools/reach_replay.py --dry-run    # replay and report; write nothing

For each bound record (a level's first record, tagged ``L``, and any
research-tree replay, tagged ``T``):

* no checker of record for the level: ``AWAITING_CHECKER``;
* a checker but no adapter in ``bindings/adapters/``: ``AWAITING_ADAPTER``;
* otherwise the record is completed at the harness commit (``HEAD``: the
  tree must be clean and ``HEAD`` on ``origin``), checked by the receiving
  side's own ``check_record``, and stored where its CLI stores receipts
  unless the terminal is ``REFUSED``.

When anything was stored, the ledger is regenerated with the receiving
side's CLI (``ledger --write``) and C is read from its computed numbers.  In
Mode E the carrier commit is a commit of this repository; the carrier
registry declares that (``harness_host``), so the receiving side's own
context resolves it with no clone argument.  Nothing here writes a grade.

AuthorityEffect: None
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.level import run_level  # noqa: E402
from outward import bundles as B  # noqa: E402
from outward import reach as R  # noqa: E402
from tools.bind import LEVELS, TREE_REPLAYS, record_tag, records  # noqa: E402


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(R.REPO), *args], capture_output=True, check=False)


def harness_commit() -> str | None:
    """HEAD, if the tree is clean and HEAD is on origin; else None."""
    if _git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        return None
    head = _git("rev-parse", "HEAD").stdout.decode().strip()
    remote = _git("branch", "-r", "--contains", head).stdout.decode().strip()
    return head if remote else None


def blob(commit: str, rel: str) -> bytes | None:
    proc = _git("show", f"{commit}:{rel}")
    return proc.stdout if proc.returncode == 0 else None


def source_paths(level: int, challenge_id: str, tag: str | None = None) -> list[str]:
    rels = [f"{R.ENGINE_REL}/{e['path']}" for e in B.harness_sources(challenge_id)]
    # The stub is not a source: it carries the receipt schema's name, and a
    # source that does is refused as a chained receipt (K13).  Its content is
    # the record itself.
    rels += [f"{R.ENGINE_REL}/PINS.json", R.adapter_path(level, tag).relative_to(R.REPO).as_posix(),
             R.positive_rel(level, tag)]
    return sorted(set(rels))


def replay_level(level: int, commit: str | None, store: bool, tag: str | None = None) -> tuple[str, str]:
    """One record: the level's first (``L``), or its research-tree replay (``T``)."""
    tag = tag or record_tag(level)
    found = R.checker_for(level)
    if found is None:
        return "AWAITING_CHECKER", "no checker of record for this level"
    checker_id, entry = found
    adapter = R.load_adapter(R.adapter_path(level, tag))
    if adapter is None:
        return "AWAITING_ADAPTER", f"checker {checker_id} is registered; no adapter states the fixtures in its schema"
    if adapter.CHECKER_ID != checker_id:
        return "AWAITING_ADAPTER", f"the adapter is written for {adapter.CHECKER_ID}, not the registered {checker_id}"
    if commit is None:
        return "NOT_REPLAYED", "the tree is not clean or HEAD is not on origin"
    checker_source = blob(str(entry["commit"]), str(entry["path"]))
    if checker_source is None:
        return "NOT_REPLAYED", "the checker is absent at its pinned commit"
    cid = str((TREE_REPLAYS if tag.startswith("T") else LEVELS)[level]["challenge_id"])
    result = run_level(cid)
    inputs = B.fixture_inputs(cid)
    stub = R.stub(level, result, inputs, tag)
    canonical = R.reach("canonical")
    sources = []
    for rel in source_paths(level, cid, tag):
        data = blob(commit, rel)
        if data is None:
            return "NOT_REPLAYED", f"{rel} is not committed at {commit[:8]}"
        sources.append({"path": rel, "sha256": canonical.digest(data)})
    record = R.complete(stub, result, inputs, adapter, checker_id, entry, checker_source, commit, sources,
                        R.lean_block(lambda rel: blob(commit, rel), list(stub["lean_theorems"])), tag)
    out = R.preflight(record, R.reach("cli").load_context(R.REACH_DIR, {}).resolver)
    if out.terminal == "REFUSED":
        return "REFUSED", ",".join(out.codes)
    if store:
        receipt = R.reach("receipt")
        ledger = R.reach("ledger")
        data = receipt.receipt_bytes(out)
        folder = R.REACH_DIR / "receipts" / ledger.carrier_key(R.CARRIER, stub["carrier_part"]) / f"{level:03d}"
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.json"):
            old.unlink()  # one live row per carrier and level: this replay supersedes the last
        (folder / (canonical.digest(data).split(":", 1)[1] + ".json")).write_bytes(data)
    return out.terminal, f"grades {json.dumps(out.grades, sort_keys=True)}"


def regenerate_ledger() -> int:
    cli = "research.mssn_sn_tower.code.python.reach.cli"
    proc = subprocess.run([sys.executable, "-m", cli, "ledger", "--write"], cwd=R.REPO, check=False)
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    commit = harness_commit()
    stored = 0
    for tag, level, _ in records():
        status, detail = replay_level(level, commit, not args.dry_run, tag)
        print(f"{tag}: {status} ({detail})")
        stored += status in ("EVIDENCE_ONLY", "SELF_CONSISTENT_ONLY", "UNRESOLVED")
    if not stored or args.dry_run:
        print("no receipt stored; the ledger is not regenerated")
        return 0
    rc = regenerate_ledger()
    numbers = json.loads((R.REACH_DIR / "derived" / "numbers.json").read_bytes())
    for key in (R.CARRIER, f"{R.CARRIER}+harness"):
        row = numbers["carriers"][key]
        print(f"{key}: C = {row['C']}, D = {row['D']}, A = {row['A']}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
