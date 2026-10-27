"""The installed research context resolves explicit namespaces and refuses escapes."""
from pathlib import Path
from typing import Any

import pytest

from operations.domain.level_engine_context import (
    ContextRefusal,
)
from pfp.infrastructure.tower_research.level_engine.context import LevelEngineContext


def test_namespaces_keep_historical_evidence_separate(tmp_path: Path) -> None:
    ctx = LevelEngineContext(tmp_path / "runtime", tmp_path / "evidence", tmp_path / "governance")
    assert ctx.historical_path("bundles/a.json") == tmp_path / "evidence/v1/bundles/a.json"
    assert ctx.current_path("bundles/a.json") == tmp_path / "evidence/v2/bundles/a.json"
    assert ctx.source("bindings/adapters/L000.py") == tmp_path / "runtime/adapters/L000.py"
    assert ctx.governance_path("HISTORY.json") == tmp_path / "governance/historical/HISTORY.json"
    with pytest.raises(ContextRefusal, match="HISTORICAL_BYTES_UNAVAILABLE"):
        ctx.require_repository()


@pytest.mark.parametrize("path", ["../outside", "/absolute", "C:/outside", "bindings/../../outside"])
def test_resource_path_refuses_escape(tmp_path: Path, path: str) -> None:
    ctx = LevelEngineContext(tmp_path, tmp_path, tmp_path)
    with pytest.raises(ContextRefusal, match="INVALID_RESOURCE_PATH"):
        ctx.resource(path)


@pytest.mark.parametrize("head,tree,dirty", [("other", "tree", ""), ("head", "other", ""), ("head", "tree", " M code/model.py")])
def test_vendor_pin_refuses_mismatched_or_dirty_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                      head: str, tree: str, dirty: str) -> None:
    import json
    import subprocess
    from types import SimpleNamespace
    governance = tmp_path / "governance"
    governance.mkdir()
    (governance / "PINS.json").write_text(json.dumps({"vendored": {"19L57G1": {"commit": "head", "tree": "tree"}}}))
    ctx = LevelEngineContext(tmp_path, tmp_path, governance, vendor_root=tmp_path / "vendor")
    def execute(argv: list[str], **kwargs: object) -> SimpleNamespace:
        stdout = head + "\n" + tree + "\n" if "rev-parse" in argv else dirty
        return SimpleNamespace(returncode=0, stdout=stdout)
    monkeypatch.setattr(subprocess, "run", execute)
    with pytest.raises(ContextRefusal, match="RR-PIN"):
        ctx.require_vendor()


def test_research_adapter_runs_through_domain_port() -> None:
    from operations.domain.level_engine_context import (
        current_context,
    )
    from pfp.domain.tower.level_engine import LevelEngineOutcome, LevelEngineRunner
    from pfp.infrastructure.tower_research.level_engine import (
        ResearchLevelEngineRunner,
    )
    runner: LevelEngineRunner = ResearchLevelEngineRunner(current_context())
    assert runner.run("edge_endpoints") == LevelEngineOutcome(
        "edge_endpoints", "FIXTURE_EXPECTATIONS_MATCHED", "RESEARCH_FIXTURE_REPLAY")


def test_research_adapter_does_not_hide_fixture_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    from operations.domain.level_engine_context import (
        current_context,
    )
    from operations.use_cases.level_engine.research_engine import level
    from pfp.domain.tower.level_engine import LevelEngineRunner
    from pfp.infrastructure.tower_research.level_engine import (
        ResearchLevelEngineRunner,
    )
    monkeypatch.setattr(level, "check_expectations", lambda cid, verdicts: ("EXPECTATION_MISMATCH:positive",))
    runner: LevelEngineRunner = ResearchLevelEngineRunner(current_context())
    result = runner.run("edge_endpoints")
    assert result.terminal == "FIXTURE_EXPECTATIONS_MISMATCHED"
    assert result.authority_effect == "None"


@pytest.mark.parametrize("tamper", [None, "source", "receipt", "closure"])
def test_packaged_lean_snapshot_requires_matching_successful_receipts(tmp_path: Path, tamper: str | None) -> None:
    import hashlib
    import json
    evidence = tmp_path / "evidence"
    root = evidence / "v2/lean/sources"
    root.mkdir(parents=True)
    def digest(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
    lean = b"theorem x : True := True.intro\n"
    report = b"x: (none)\n"
    (root / "Example.lean").write_bytes(lean)
    (root / "axioms.txt").write_bytes(report)
    sources = {"research_programs/level_engine/Example.lean": digest(lean)}
    build = {"returncode": 0, "sources_stable": True, "sources": sources, "toolchain": "test-toolchain"}
    audit = {"returncode": 0, "elaboration_returncode": 0, "sources": sources,
             "toolchain": "test-toolchain", "missing": [], "extra": [], "duplicates": [],
             "outside_policy": {}, "declarations": 1, "census": 1, "report_sha256": digest(report)}
    receipt_digests = {}
    for name, body in (("build_receipt.json", build), ("axiom_audit_receipt.json", audit)):
        data = json.dumps(body).encode()
        (root.parent / name).write_bytes(data)
        receipt_digests[name] = digest(data)
    manifest: dict[str, Any] = {"schema": "level-engine.lean-read-resources.v2", "authority_effect": "None",
                "canonical_root": "lean4", "toolchain": "test-toolchain", "receipt_sha256": receipt_digests,
                "sources": {"research_programs/level_engine/Example.lean": {"snapshot": "Example.lean", "sha256": digest(lean)},
                            "research_programs/level_engine/axioms.txt": {"snapshot": "axioms.txt", "sha256": digest(report)}}}
    if tamper == "source":
        (root / "Example.lean").write_bytes(b"changed source")
    elif tamper == "receipt":
        (root.parent / "axiom_audit_receipt.json").write_text('{"returncode": 1}')
    elif tamper == "closure":
        del manifest["sources"]["research_programs/level_engine/Example.lean"]
    (root / "manifest.json").write_text(json.dumps(manifest))
    ctx = LevelEngineContext(tmp_path, evidence, tmp_path, lean_root=root)
    if tamper is None:
        assert ctx.lean_path("axioms.txt").read_bytes() == report
    else:
        with pytest.raises(ContextRefusal, match="LEAN_SNAPSHOT_INVALID"):
            ctx.lean_path("axioms.txt")
