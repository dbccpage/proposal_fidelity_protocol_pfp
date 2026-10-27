"""Verify historical reach records; new certifications require the Rust path.

The CLI needs an explicit history repository, never the Level Engine vendor.
Legacy callable names remain available for scoped verification and refusals.
AuthorityEffect: None.
"""

from __future__ import annotations

import subprocess

if __name__ == "__main__":
    import runpy
    import sys

    sys.argv = [sys.argv[0], "reach_replay", *sys.argv[1:]]
    raise SystemExit(runpy.run_module(
        "operations.infrastructure.level_engine_ports",
        run_name="__main__",
    ))

from operations.domain.level_engine_context import (
    LevelEngineOperationPorts,
    current_context,
)


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(current_context().require_repository()), *args], capture_output=True, check=False)


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


def source_paths(level: int, challenge_id: str, tag: str | None = None, *,
                 ports: LevelEngineOperationPorts) -> list[str]:
    bundles, reach = ports.bundles, ports.reach
    rels = [f"{reach.ENGINE_REL}/{e['path']}" for e in bundles.harness_sources(challenge_id)]
    # The stub is not a source: it carries the receipt schema's name, and a
    # source that does is refused as a chained receipt (K13).  Its content is
    # the record itself.
    rels += ["governance/contracts/level_engine/v2/PINS.json", reach.adapter_path(level, tag).relative_to(current_context().require_repository()).as_posix(),
             reach.positive_rel(level, tag)]
    return sorted(set(rels))


def replay_level(level: int, commit: str | None, store: bool, tag: str | None = None, *,
                 ports: LevelEngineOperationPorts) -> tuple[str, str]:
    """One record: the level's first (``L``), or its research-tree replay (``T``)."""
    from .bind import record_tag
    reach = ports.reach
    tag = tag or record_tag(level)
    found = reach.checker_for(level)
    if found is None:
        return "AWAITING_CHECKER", "no checker of record for this level"
    checker_id, entry = found
    adapter = reach.load_adapter(reach.adapter_path(level, tag))
    if adapter is None:
        return "AWAITING_ADAPTER", f"checker {checker_id} is registered; no adapter states the fixtures in its schema"
    if adapter.CHECKER_ID != checker_id:
        return "AWAITING_ADAPTER", f"the adapter is written for {adapter.CHECKER_ID}, not the registered {checker_id}"
    if commit is None:
        return "NOT_REPLAYED", "the tree is not clean or HEAD is not on origin"
    return "NOT_REPLAYED", "REACH_V2_GENERATION_UNAVAILABLE: historical reach-receipt/1 is verification-only"


def regenerate_ledger() -> int:
    raise ValueError("REACH_V2_GENERATION_UNAVAILABLE: historical reach-receipt/1 is verification-only")


def main(argv: list[str] | None = None, ports: LevelEngineOperationPorts | None = None) -> int:
    if ports is None:
        raise ValueError("LEVEL_ENGINE_PORTS_REQUIRED")
    arguments = list(argv or [])
    return ports.reach_main(["replay", "--workspace", str(current_context().require_repository()), *arguments])
