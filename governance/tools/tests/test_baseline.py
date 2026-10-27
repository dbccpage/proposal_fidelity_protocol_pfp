"""The baseline command and the Rust and Lean 4 languages.

AuthorityEffect: None.
Contract: urn:pfp-governance:tests:baseline:v1
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from governance.tools import checker
from governance.tools.checker import Artifact, Repository
from governance.tools.tests.helpers import digest, records_for, write_records


def run(repo: Path, *argv: str) -> tuple[int, str]:
    out = io.StringIO()
    return checker.main(["--root", str(repo), *argv], out), out.getvalue()


def baseline(repo: Path) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = json.loads(
        (repo / "governance" / "baseline.json").read_text(encoding="utf-8")
    )["entries"]
    return entries


def test_rust_and_lean_artifacts_are_admitted() -> None:
    for language in ("Rust", "Lean 4"):
        artifact = Artifact.model_validate_json(json.dumps({"path": "x", "language": language, "sha256": "0" * 64}))
        assert artifact.language == language


def test_baseline_adds_only_with_a_reason(repo: Path) -> None:
    code, out = run(repo, "baseline", "--write", "--allow-add")
    assert (code, out) == (checker.USAGE_ERROR, "governance-check: --allow-add needs a --reason\n")
    assert run(repo, "baseline") == (0, "baseline: 0 entries (0 added, 0 dropped)\n")
    assert baseline(repo) == {}
    code, out = run(repo, "baseline", "--write", "--allow-add", "--reason", "imported tree")
    assert (code, out) == (0, "baseline: 2 entries (2 added, 0 dropped)\n")
    entries = baseline(repo)
    assert entries["pfp_lab/mod.py"] == {"sha256": digest(repo / "pfp_lab" / "mod.py"), "reason": "imported tree"}
    assert run(repo, "check")[0] == 0
    text = (repo / "governance" / "baseline.json").read_text(encoding="utf-8")
    assert text.startswith('{\n  "schema_version": "pfp.governance-baseline.v1",\n  "AuthorityEffect": "None"')


def test_baseline_only_shrinks_without_allow_add(repo: Path) -> None:
    run(repo, "baseline", "--write", "--allow-add", "--reason", "imported tree")
    contract, score = records_for(repo, "pfp_lab/mod.py")
    contract_file, score_file = write_records(repo, contract, score)
    run(repo, "record", "pfp_lab/mod.py", "--contract", str(contract_file), "--score", str(score_file))
    (repo / "pfp_lab" / "tests" / "test_mod.py").write_text("def test_y() -> None:\n    pass\n", encoding="utf-8")
    (repo / "pfp_lab" / "new.py").write_text("X = 2\n", encoding="utf-8")
    code, out = run(repo, "baseline", "--write")
    assert (
        out
        == "baseline: 0 entries (0 added, 2 dropped)\n  dropped pfp_lab/mod.py\n  dropped pfp_lab/tests/test_mod.py\n"
    )
    assert baseline(repo) == {}
    assert not Repository(repo).grandfathered("pfp_lab/new.py", digest(repo / "pfp_lab" / "new.py"))
