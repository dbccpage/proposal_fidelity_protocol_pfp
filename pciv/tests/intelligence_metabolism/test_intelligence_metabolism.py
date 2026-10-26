"""Tests for Intelligence Metabolism bounded context (U02).

Invariants tested:
- Mining is strictly read-only: source tree SHA-256 is identical before and after.
- Mined records have valid (path, sha256, offset).
- Daily digest produces claim-disciplined 4-part evaluation and AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from omega_engine_prompt_civilization.infrastructure.intelligence_metabolism import (
    IntelligenceMiner,
)
from omega_engine_prompt_civilization.use_cases.intelligence_metabolism.digest import (
    DailyDigestGenerator,
)


def compute_dir_tree_hash(dir_path: Path) -> str:
    """Computes a deterministic hash over all file paths and contents in a directory tree."""
    hasher = hashlib.sha256()
    for p in sorted(dir_path.rglob("*")):
        if p.is_file():
            hasher.update(str(p.relative_to(dir_path)).encode("utf-8"))
            hasher.update(p.read_bytes())
    return hasher.hexdigest()


@pytest.fixture
def intelligence_fixture(tmp_path: Path):
    """Sets up a mock 3-source intelligence fixture."""
    root = tmp_path / "intel_root"
    root.mkdir()

    from omega_engine_prompt_civilization.infrastructure.intelligence_metabolism.sources import (
        SOURCE_REGISTRY,
    )

    # Source 1: sealed run folders
    runs_dir = SOURCE_REGISTRY["symbol_game_runs"].resolve_path(root) / "run_001"
    runs_dir.mkdir(parents=True)
    receipt_data = {
        "schema_version": "v1.0.0",
        "run_id": "run_001",
        "status": "COMPLETED",
        "authority_effect": "None",
    }
    (runs_dir / "receipt.json").write_text(json.dumps(receipt_data), encoding="utf-8")

    # Source 2: DDC traces (jsonl)
    dda_dir = root / ".agents" / "dda_traces"
    dda_dir.mkdir(parents=True)
    trace_lines = [
        json.dumps({"seq": 0, "letter": "C", "actor": "init"}),
        json.dumps({"seq": 1, "letter": "D", "actor": "step"}),
        json.dumps({"seq": 2, "letter": "E", "actor": "repair"}),
    ]
    (dda_dir / "trace_001.jsonl").write_text("\n".join(trace_lines) + "\n", encoding="utf-8")

    # Source 3: Benchmark results (json)
    bench_dir = SOURCE_REGISTRY["bench_results"].resolve_path(root)
    bench_dir.mkdir(parents=True)
    bench_data = {
        "schema": "benchmark_result_v1",
        "benchmark_id": "bench_001",
        "accuracy": 1.0,
    }
    (bench_dir / "result_001.json").write_text(json.dumps(bench_data), encoding="utf-8")

    return root


def test_intelligence_miner_read_only_and_provenance(intelligence_fixture: Path):
    root = intelligence_fixture

    # 1. Capture tree hash before mining
    tree_hash_before = compute_dir_tree_hash(root)

    # 2. Mine all records
    miner = IntelligenceMiner(repo_root=root)
    records = list(miner.mine_all())

    # 3. Assert tree hash is IDENTICAL (zero in-place mutation)
    tree_hash_after = compute_dir_tree_hash(root)
    assert tree_hash_before == tree_hash_after, "Mining must be strictly read-only!"

    # 4. Verify record provenance invariants
    assert len(records) == 5  # 1 receipt + 3 trace rows + 1 bench result

    for rec in records:
        assert rec.source_id in {"symbol_game_runs", "dda_traces", "bench_results"}
        assert rec.file_path
        assert len(rec.file_sha256) == 64  # valid sha256 hex
        assert rec.offset >= 0
        assert rec.authority_effect == "None"
        assert isinstance(rec.payload, dict)

    # 5. Verify Daily Digest Generator and Claim Hygiene
    generator = DailyDigestGenerator(records)
    md = generator.render_markdown("2026-09-30")

    assert "AuthorityEffect**: None" in md
    assert "### What this supports:" in md
    assert "### What this does not support:" in md
    assert "### Narrowest defensible claim:" in md
    assert "### Next test needed:" in md
    assert "`symbol_game_runs` | 1" in md
    assert "`dda_traces` | 3" in md
    assert "`bench_results` | 1" in md

    # Write digest to output directory
    digest_dir = root / "_intelligence" / "metabolism" / "digests"
    digest_dir.mkdir(parents=True)
    digest_path = digest_dir / "2026-09-30.md"
    digest_path.write_text(generator.render_markdown("2026-09-30"), encoding="utf-8")
    assert digest_path.exists()
    assert "Daily Intelligence Metabolism Digest — 2026-09-30" in digest_path.read_text(
        encoding="utf-8"
    )
