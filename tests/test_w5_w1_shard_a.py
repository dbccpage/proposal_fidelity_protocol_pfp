"""Verification and falsification suite for Window 5 Wave 1 Shard A (Paper 008 Part 1).

Covers:
- AUDIT-P008-005 (ATL-P008-005): Stage grade basis (stage_status.py, checks.py, reach/targets.py)
- AUDIT-P008-009 (ATL-P008-009): Resolver no-fallback (level_engine/resolver.py)
- AUDIT-P008-010 (ATL-P008-010): 150/150 label insufficiency (retained audit + C005 custody)
- AUDIT-P008-011 (ATL-P008-011): Challenge census partition at commit a623568e

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import types
from collections.abc import Callable, Iterator
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from pfp.domain.tower import checks, stage_status
from pfp.domain.tower.wire import (
    Atom,
    Diff,
    WireError,
    application,
    emit_wire,
    parse_wire,
)
from pfp.infrastructure.tower_evidence.level_engine.resolver import (
    EvidenceRefusal,
    LevelEngineEvidenceResolver,
)
from pfp.infrastructure.tower_research.reach import targets

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_008_DIR = (
    REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "008_pfp_mssn_tower_challenges_and_retraction_benchmarks"
)


@pytest.fixture(autouse=True)
def _disable_bytecode_writing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent Python from writing .pyc or __pycache__ artifacts during tests."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)


def _load_c005_bakeoff_module(
    monkeypatch: pytest.MonkeyPatch, tmp_root: Path
) -> tuple[types.ModuleType, Callable[[], None]]:
    """Load run_adversary_bakeoff.py and return (module, cleanup) with sys.modules/sys.path snapshot."""
    pre_modules = set(sys.modules)
    pre_sys_path = list(sys.path)

    def _cleanup() -> None:
        sys.path[:] = pre_sys_path
        for key in list(sys.modules):
            if key not in pre_modules:
                sys.modules.pop(key, None)

    os_pkg = types.ModuleType("operating_system")
    adapters_pkg = types.ModuleType("operating_system.adapters")
    custody_pkg = types.ModuleType("operating_system.adapters.intelligence_custody")
    root_mod = types.ModuleType(
        "operating_system.adapters.intelligence_custody.intelligence_root"
    )
    root_mod.resolve_intelligence_repo_root = lambda: tmp_root  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "operating_system", os_pkg)
    monkeypatch.setitem(sys.modules, "operating_system.adapters", adapters_pkg)
    monkeypatch.setitem(
        sys.modules, "operating_system.adapters.intelligence_custody", custody_pkg
    )
    monkeypatch.setitem(
        sys.modules,
        "operating_system.adapters.intelligence_custody.intelligence_root",
        root_mod,
    )

    bakeoff_path = (
        REPO_ROOT
        / "workflows"
        / "wf12_mechanism_control_arms"
        / "pilots"
        / "c005_hosted_decode_controls"
        / "run_adversary_bakeoff.py"
    )
    module_name = "_shard_a_c005_bakeoff"
    spec = importlib.util.spec_from_file_location(module_name, bakeoff_path)
    if spec is None or spec.loader is None:
        _cleanup()
        raise RuntimeError(f"Unable to build module spec for {bakeoff_path}")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    try:
        spec.loader.exec_module(module)
    except BaseException:
        _cleanup()
        raise
    return module, _cleanup


def _evaluate_three_fixture_binding(
    run_fn: Callable[[Any], Any],
    positive: Any,
    stage_negative: Any,
    empty: Any,
) -> str:
    """Evaluate the documented 3-fixture COMPUTED gate (positive pass, negative/empty WireError)."""
    try:
        run_fn(positive)
    except WireError:
        return "NONE"
    for bad_fixture in (stage_negative, empty):
        try:
            run_fn(bad_fixture)
        except WireError:
            continue
        return "NONE"
    return "COMPUTED"


def _init_git_repo_with_blobs(repo_dir: Path, files: dict[str, bytes]) -> str:
    """Create a deterministic local Git commit in repo_dir and return its 40-hex commit SHA."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Shard A Test",
        "GIT_AUTHOR_EMAIL": "shard-a@example.invalid",
        "GIT_COMMITTER_NAME": "Shard A Test",
        "GIT_COMMITTER_EMAIL": "shard-a@example.invalid",
    }
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, env=env, check=True)
    subprocess.run(
        ["git", "config", "core.autocrlf", "false"],
        cwd=repo_dir,
        env=env,
        check=True,
    )
    for rel_path, content in files.items():
        dest = repo_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
    subprocess.run(["git", "add", "."], cwd=repo_dir, env=env, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "fixture commit"],
        cwd=repo_dir,
        env=env,
        check=True,
    )
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    commit_sha = proc.stdout.strip()
    assert re.fullmatch(r"[0-9a-f]{40}", commit_sha) is not None
    return commit_sha


# ============================================================================
# Claim 1: AUDIT-P008-005 (ATL-P008-005) — Stage grade basis
# ============================================================================


class TestStageGradeBasis:
    """Verify stage-status grade taxonomy, executed checks.py fixtures, and stub divergence."""

    def test_grades_taxonomy_excludes_lean_and_gated_and_census_sums_to_101(self) -> None:
        assert stage_status.GRADES == ("NONE", "SYNTAX", "COMPUTED")
        assert "LEAN" not in stage_status.GRADES
        assert "GATED" not in stage_status.GRADES

        bound_levels = tuple(b.level for b in stage_status.BINDINGS)
        assert bound_levels == (0, 1, 23, 35, 36, 48)
        computed_levels = stage_status.COMPUTED_LEVELS
        assert computed_levels == frozenset({0, 1, 23, 35, 36, 48})

        summary = stage_status.census()
        assert tuple(summary.keys()) == ("NONE", "SYNTAX", "COMPUTED")
        counts = {grade: len(levels) for grade, levels in summary.items()}
        assert counts == {"NONE": 75, "SYNTAX": 20, "COMPUTED": 6}
        assert sum(counts.values()) == 101

        computed_set = set(summary["COMPUTED"])
        syntax_set = set(summary["SYNTAX"])
        none_set = set(summary["NONE"])

        assert computed_set == {0, 1, 23, 35, 36, 48}
        assert syntax_set == set(range(2, 22))
        assert none_set == set(range(22, 101)) - {23, 35, 36, 48}
        assert computed_set.isdisjoint(syntax_set)
        assert computed_set.isdisjoint(none_set)
        assert syntax_set.isdisjoint(none_set)

    def test_checks_module_executes_syntax_roundtrip_and_stage_early_refusals(self) -> None:
        # Stage 0 admits only Diff() (<>), round-tripping on wire
        diff_node = Diff()
        assert parse_wire(emit_wire(diff_node)) == diff_node
        assert checks.validate_stage(diff_node, 0) == "STRUCTURAL_ONLY"

        # Stage 1 admits binary atoms and opcode 0 lift, refused one stage early at stage 0
        lift_0_to_1 = application(0, Diff(), Atom("0"), Atom("1"))
        assert parse_wire(emit_wire(lift_0_to_1)) == lift_0_to_1
        assert checks.validate_stage(Atom("0"), 1) == "STRUCTURAL_ONLY"
        assert checks.validate_stage(lift_0_to_1, 1) == "STRUCTURAL_ONLY"

        with pytest.raises(WireError, match="MSS-0 admits only <>"):
            checks.validate_stage(Atom("0"), 0)
        with pytest.raises(WireError, match="MSS-0 admits only <>"):
            checks.validate_stage(lift_0_to_1, 0)

        # Stage 2 admits general alphanumeric atoms and directed edges (opcode 2), refused at stage 1
        edge_ab = application(2, Atom("a"), Atom("b"))
        assert parse_wire(emit_wire(edge_ab)) == edge_ab
        assert checks.validate_stage(Atom("a"), 2) == "STRUCTURAL_ONLY"
        assert checks.validate_stage(edge_ab, 2) == "STRUCTURAL_ONLY"

        with pytest.raises(WireError, match="inactive MSS-1 data atom"):
            checks.validate_stage(Atom("a"), 1)
        with pytest.raises(WireError, match="opcode not admitted at this stage"):
            checks.validate_stage(edge_ab, 1)

        # Proposal constructors (stages 22..100) pass at stage N and fail at N - 1
        for level in (22, 23, 35, 36, 48, 100):
            prop_node = checks.proposed_stage_fixture(level)
            assert parse_wire(emit_wire(prop_node)) == prop_node
            assert checks.validate_stage(prop_node, level) == "PROPOSED_STRUCTURAL_ONLY"
            with pytest.raises(WireError, match="premature extension opcode"):
                checks.validate_stage(prop_node, level - 1)

        # Empty wire input fails closed
        with pytest.raises(WireError):
            parse_wire("")

    def test_checks_module_executes_six_computed_stage_checkers_with_negatives_and_empties(
        self,
    ) -> None:
        # Stage 23: finite_sheaf_gluing
        glued = checks.glue_finite_sections(
            [{"a", "b"}, {"b", "c"}],
            [{"a": "0", "b": "1"}, {"b": "1", "c": "0"}],
        )
        assert glued == {"a": "0", "b": "1", "c": "0"}
        with pytest.raises(WireError, match="overlap disagreement"):
            checks.glue_finite_sections(
                [{"a", "b"}, {"b", "c"}],
                [{"a": "0", "b": "1"}, {"b": "0", "c": "0"}],
            )
        with pytest.raises(WireError, match="cover data mismatch"):
            checks.glue_finite_sections([], [])

        # Stage 35: markov_chain
        kernel = checks.check_markov([["1/2", "1/2"], ["1/3", "2/3"]])
        assert kernel == (
            (Fraction(1, 2), Fraction(1, 2)),
            (Fraction(1, 3), Fraction(2, 3)),
        )
        with pytest.raises(WireError, match="probability distribution"):
            checks.check_markov([["1/2", "1/3"], ["0/1", "1/1"]])
        with pytest.raises(WireError, match="noncanonical rational"):
            checks.check_markov([["2/4", "1/2"], ["0/1", "1/1"]])
        with pytest.raises(WireError, match="finite square Markov kernel required"):
            checks.check_markov([])

        # Stage 36: bayesian_update
        posterior = checks.check_bayes(["1/2", "1/2"], ["3/4", "1/4"])
        assert posterior == ("3/4", "1/4")
        with pytest.raises(WireError, match="zero evidence"):
            checks.check_bayes(["1/2", "1/2"], ["0/1", "0/1"])
        with pytest.raises(WireError, match="Bayes domain mismatch"):
            checks.check_bayes([], [])

        # Stage 48: spin_1_2_z
        spin = checks.check_spin_z(("3/5", "4/5"))
        assert spin == {
            "up": "9/25",
            "down": "16/25",
            "expectation_z": "-7/25",
            "authority_effect": "None",
        }
        assert Fraction(spin["up"]) + Fraction(spin["down"]) == Fraction(1, 1)
        assert Fraction(spin["up"]) - Fraction(spin["down"]) == Fraction(-7, 25)
        with pytest.raises(WireError, match="not normalized"):
            checks.check_spin_z(("1/2", "1/2"))
        with pytest.raises(WireError, match="not normalized"):
            checks.check_spin_z(("0/1", "0/1"))
        with pytest.raises(WireError, match="two basis components"):
            checks.check_spin_z(())  # type: ignore[arg-type]

    def test_reach_targets_probe_battery_and_exception_refusal_contract(self) -> None:
        positive = {"edges": [[0, 1]], "label": "witness"}
        probes = {
            name: (payload, code)
            for name, payload, code in targets.probe_battery(positive)
        }
        assert probes["empty_object"] == ({}, "R_EMPTY_INPUT")
        assert probes["empty_list"] == ([], "R_EMPTY_INPUT")
        assert probes["null"] == (None, "R_EMPTY_INPUT")
        assert probes["verdict_only"] == ({"verified": True}, "R_VERDICT_FIELD")
        assert probes["data_plus_verdict"][1] == "R_VERDICT_FIELD"
        assert targets.is_empty_payload({}) is True
        assert targets.is_flag_only({"verified": True}) is True

        def crashing_checker(_payload: Any) -> tuple[str, str | None]:
            raise KeyError("missing_key")

        verdict = targets.run(crashing_checker, positive, ("R_EMPTY_INPUT", "R_VERDICT_FIELD"))
        assert verdict == ("REFUSED", "R_EXCEPTION:KeyError")

    def test_falsification_current_stage_status_stub_does_not_invoke_binding_and_uses_level_threshold(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Confirm unarchived historical baseline script is absent from source_index.json
        source_index = json.loads(
            (PAPER_008_DIR / "docs" / "source_archive" / "source_index.json").read_text(
                encoding="utf-8"
            )
        )
        archived_paths = {
            item["path"] for item in source_index["entries"]
        } | {item["origin_path"] for item in source_index["entries"]}
        assert all("stage_status.py" not in p for p in archived_paths)

        # Falsification of dynamic execution in current pfp/domain/tower/stage_status.py:
        # replacing BINDINGS with a raising callback leaves call_count == 0 and still returns COMPUTED.
        call_count = 0

        def raising_checker(_payload: Any) -> Any:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("binding callback was invoked")

        patched_bindings = tuple(
            stage_status.CheckerBinding(b.level, b.checker, run=raising_checker)
            for b in stage_status.BINDINGS
        )
        monkeypatch.setattr(stage_status, "BINDINGS", patched_bindings)

        res_35 = stage_status.stage_status(35)
        assert res_35.grade == "COMPUTED"
        assert call_count == 0

        # Negative level threshold probe: elif level <= 21 classifies -1 as SYNTAX without bounds check
        res_neg = stage_status.stage_status(-1)
        assert res_neg.grade == "SYNTAX"

    def test_falsification_three_fixture_gate_rejects_hollow_checker_accepting_negative(
        self,
    ) -> None:
        # Genuine 3-fixture evaluator passes real glue_finite_sections wrapper
        def real_gluing_runner(
            pair: tuple[list[set[str]], list[dict[str, str]]],
        ) -> dict[str, str]:
            return checks.glue_finite_sections(pair[0], pair[1])

        pos_gluing = ([{"a", "b"}, {"b", "c"}], [{"a": "0", "b": "1"}, {"b": "1", "c": "0"}])
        neg_gluing = ([{"a", "b"}, {"b", "c"}], [{"a": "0", "b": "1"}, {"b": "0", "c": "0"}])
        emp_gluing: tuple[list[set[str]], list[dict[str, str]]] = ([], [])

        assert (
            _evaluate_three_fixture_binding(
                real_gluing_runner, pos_gluing, neg_gluing, emp_gluing
            )
            == "COMPUTED"
        )

        # Study Guide Q06 changed-input control: a hollow checker that accepts negative or empty
        # fixtures fails the 3-fixture gate and drops to NONE.
        def hollow_accept_negative(
            pair: tuple[list[set[str]], list[dict[str, str]]],
        ) -> dict[str, str]:
            if not pair[0]:
                raise WireError("empty")
            return {"a": "0"}

        assert (
            _evaluate_three_fixture_binding(
                hollow_accept_negative, pos_gluing, neg_gluing, emp_gluing
            )
            == "NONE"
        )
        assert (
            _evaluate_three_fixture_binding(
                lambda _x: {"a": "0"}, pos_gluing, neg_gluing, emp_gluing
            )
            == "NONE"
        )


# ============================================================================
# Claim 2: AUDIT-P008-009 (ATL-P008-009) — Resolver no-fallback
# ============================================================================


class TestResolverNoFallback:
    """Verify bidirectional v1/v2 isolation, path refusals, and optional sha256 pin."""

    def test_v1_reads_exact_pinned_git_blob_bytes_and_ignores_working_tree_mutations(
        self, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        raw_v1 = b"line1\r\nline2\x00binary_tail\n"
        rev1 = _init_git_repo_with_blobs(repo, {"bundles/sample.bin": raw_v1})

        # Mutate working tree and create a second commit; rev1 must still return raw_v1
        (repo / "bundles" / "sample.bin").write_bytes(b"mutated working tree bytes")
        resolver = LevelEngineEvidenceResolver(repository=repo)
        got = resolver.read_bytes("v1", "bundles/sample.bin", revision=rev1)
        assert got == raw_v1

        # Delete file from working tree entirely; rev1 blob lookup still succeeds
        (repo / "bundles" / "sample.bin").unlink()
        assert resolver.read_bytes("v1", "bundles/sample.bin", revision=rev1) == raw_v1

    def test_v1_miss_never_falls_back_to_v2_package_resource_or_working_tree(
        self, tmp_path: Path
    ) -> None:
        # "manifest.json" exists in installed v2 package resources; commit a repo WITHOUT manifest.json,
        # then write an untracked "manifest.json" in the working tree to test both fallback vectors at once.
        repo = tmp_path / "repo_without_manifest"
        rev = _init_git_repo_with_blobs(repo, {"other.txt": b"committed"})
        (repo / "manifest.json").write_bytes(b'{"working_tree": true}')

        resolver = LevelEngineEvidenceResolver(repository=repo)
        # Confirm v2 actually has manifest.json on this same resolver instance
        v2_manifest = resolver.read_bytes("v2", "manifest.json")
        assert len(v2_manifest) > 0

        # Requesting manifest.json under v1 at rev MUST refuse rather than reading v2 or working tree
        with pytest.raises(EvidenceRefusal) as exc_info:
            resolver.read_bytes("v1", "manifest.json", revision=rev)
        assert exc_info.value.code == "HISTORICAL_BYTES_UNAVAILABLE"

        # Unconfigured repository (repository=None) also refuses v1 immediately
        no_repo_resolver = LevelEngineEvidenceResolver(repository=None)
        with pytest.raises(EvidenceRefusal) as exc_no_repo:
            no_repo_resolver.read_bytes("v1", "manifest.json", revision=rev)
        assert exc_no_repo.value.code == "HISTORICAL_BYTES_UNAVAILABLE"

    def test_v2_reads_package_resource_and_miss_never_falls_back_to_v1_git_or_working_tree(
        self, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo_with_v1_only_artifact"
        v1_only_path = "historical_only/v1_blob.json"
        v1_payload = b'{"historical": 1}\n'
        rev = _init_git_repo_with_blobs(repo, {v1_only_path: v1_payload})

        resolver = LevelEngineEvidenceResolver(repository=repo)
        # Confirm v1 resolves the committed path
        assert resolver.read_bytes("v1", v1_only_path, revision=rev) == v1_payload
        assert (repo / v1_only_path).exists()

        # Requesting that same path under v2 MUST raise ACTIVE_RESOURCE_UNAVAILABLE without falling back to v1 or disk
        with pytest.raises(EvidenceRefusal) as exc_info:
            resolver.read_bytes("v2", v1_only_path)
        assert exc_info.value.code == "ACTIVE_RESOURCE_UNAVAILABLE"

    def test_version_and_revision_contract_refusals(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        rev = _init_git_repo_with_blobs(repo, {"a.txt": b"alpha"})
        resolver = LevelEngineEvidenceResolver(repository=repo)

        # v1 requires a 40-char lowercase hex revision
        for bad_rev in (None, "", "HEAD", rev[:12], rev.upper(), "g" * 40):
            with pytest.raises(EvidenceRefusal) as exc_v1:
                resolver.read_bytes("v1", "a.txt", revision=bad_rev)
            assert exc_v1.value.code == "HISTORICAL_BYTES_UNAVAILABLE"

        # v2 forbids passing any revision
        with pytest.raises(EvidenceRefusal) as exc_v2_rev:
            resolver.read_bytes("v2", "manifest.json", revision=rev)
        assert exc_v2_rev.value.code == "EVIDENCE_VERSION_INVALID"

        # Unknown version strings fail closed
        for bad_ver in ("", "v0", "v3", "latest"):
            with pytest.raises(EvidenceRefusal) as exc_ver:
                resolver.read_bytes(bad_ver, "manifest.json")
            assert exc_ver.value.code == "EVIDENCE_VERSION_INVALID"

    @pytest.mark.parametrize(
        "unsafe_path",
        [
            "",
            "../escape.json",
            "sub/../../escape.json",
            "/etc/passwd",
            "C:/outside.json",
            "sub\\backslash.json",
            "CON.json",
            "sub/nul.txt",
            "lpt1.dat",
        ],
    )
    def test_path_security_and_windows_reserved_device_refusals(
        self, tmp_path: Path, unsafe_path: str
    ) -> None:
        resolver = LevelEngineEvidenceResolver(repository=tmp_path)
        for ver, rev in (("v1", "0" * 40), ("v2", None)):
            with pytest.raises(EvidenceRefusal) as exc_info:
                resolver.read_bytes(ver, unsafe_path, revision=rev)
            assert exc_info.value.code == "EVIDENCE_PATH_INVALID"

    def test_optional_sha256_digest_obligation_enforced_when_present_and_skipped_when_none(
        self, tmp_path: Path
    ) -> None:
        repo = tmp_path / "repo"
        payload = b"exact pinned content\n"
        true_digest = hashlib.sha256(payload).hexdigest()
        wrong_digest = "0" * 64
        rev = _init_git_repo_with_blobs(repo, {"item.txt": payload})
        resolver = LevelEngineEvidenceResolver(repository=repo)

        # When sha256 is omitted (None), bytes return without SHA-256 comparison
        assert resolver.read_bytes("v1", "item.txt", revision=rev, sha256=None) == payload

        # Bare 64-hex and "sha256:<64-hex>" both succeed when matching
        assert resolver.read_bytes("v1", "item.txt", revision=rev, sha256=true_digest) == payload
        assert (
            resolver.read_bytes("v1", "item.txt", revision=rev, sha256=f"sha256:{true_digest}")
            == payload
        )

        # Wrong or malformed sha256 fails closed with EVIDENCE_DIGEST_MISMATCH on both v1 and v2
        for bad_sha in (wrong_digest, f"sha256:{wrong_digest}", "not-a-hex-digest", true_digest.upper()):
            with pytest.raises(EvidenceRefusal) as exc_v1:
                resolver.read_bytes("v1", "item.txt", revision=rev, sha256=bad_sha)
            assert exc_v1.value.code == "EVIDENCE_DIGEST_MISMATCH"

            with pytest.raises(EvidenceRefusal) as exc_v2:
                resolver.read_bytes("v2", "manifest.json", sha256=bad_sha)
            assert exc_v2.value.code == "EVIDENCE_DIGEST_MISMATCH"


# ============================================================================
# Claim 3: AUDIT-P008-010 (ATL-P008-010) — 150/150 label insufficiency
# ============================================================================


class TestRunnerLabelInsufficiency:
    """Verify 150/150 non-identifiability under VERIFIED fallback and C005 custody guards."""

    _bakeoff: types.ModuleType

    @pytest.fixture(autouse=True)
    def _inject_bakeoff(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> Iterator[None]:
        monkeypatch.setattr(sys, "dont_write_bytecode", True)
        module, cleanup = _load_c005_bakeoff_module(monkeypatch, tmp_path)
        self._bakeoff = module
        try:
            yield
        finally:
            cleanup()

    def test_archived_records_document_withdrawal_and_ten_live_queries_in_150_suite(
        self,
    ) -> None:
        ledger_text = (PAPER_008_DIR / "paper_claim_ledger.md").read_text(encoding="utf-8")
        supplement_text = (PAPER_008_DIR / "docs" / "completion_supplement.md").read_text(
            encoding="utf-8"
        )
        c005_report_text = (
            PAPER_008_DIR / "docs" / "source_archive" / "c005_working_report.md"
        ).read_text(encoding="utf-8")

        assert "PFP008-10" in ledger_text
        assert "run_150_tests_suite.py" in ledger_text
        assert "VERIFIED" in ledger_text
        assert "150/150" in ledger_text

        assert "withdrawal note" in supplement_text
        assert "recorded 150/150 benchmark\nlabels are not validated model results" in supplement_text

        # Section 4.4 accounting table in c005_working_report.md records "10 live" queries for the 150-Test Full Suite
        assert "| 150-Test Full Suite (Tracks 01–15) | 10 live |" in c005_report_text

    def test_algebraic_non_identifiability_of_150_over_150_under_verified_fallback(
        self,
    ) -> None:
        total_cases = 150

        def permissive_numerator(n_pass: int, n_missing: int, n_exc: int, n_fail: int) -> int:
            assert n_pass + n_missing + n_exc + n_fail == total_cases
            # PASSED = n_pass; VERIFIED = n_missing + n_exc; headline counts PASSED + VERIFIED
            return n_pass + n_missing + n_exc

        def strict_numerator(n_pass: int, n_missing: int, n_exc: int, n_fail: int) -> int:
            assert n_pass + n_missing + n_exc + n_fail == total_cases
            # Missing -> NOT_RUN; exception -> FAILED; only genuine pass counts as PASSED
            return n_pass

        # Enumerate all non-negative triples (n_pass, n_missing, n_exc) with n_fail == 0 summing to 150
        triples_giving_150_permissive = 0
        triples_giving_150_strict = 0
        for n_pass in range(total_cases + 1):
            for n_missing in range(total_cases - n_pass + 1):
                n_exc = total_cases - n_pass - n_missing
                if permissive_numerator(n_pass, n_missing, n_exc, 0) == total_cases:
                    triples_giving_150_permissive += 1
                if strict_numerator(n_pass, n_missing, n_exc, 0) == total_cases:
                    triples_giving_150_strict += 1

        expected_simplex_size = math.comb(total_cases + 2, 2)
        assert expected_simplex_size == 11476
        assert triples_giving_150_permissive == 11476
        assert triples_giving_150_strict == 1
        assert triples_giving_150_permissive - triples_giving_150_strict == 11475

        # Concrete 10-live-query scenario: 10 passed, 130 missing receipts, 10 exceptions
        # -> 150/150 permissive vs 1/15 actual
        assert permissive_numerator(10, 130, 10, 0) == 150
        assert Fraction(strict_numerator(10, 130, 10, 0), total_cases) == Fraction(1, 15)

    def test_bakeoff_not_adjudicated_and_failure_receipt_custody_guards(
        self, tmp_path: Path
    ) -> None:
        bakeoff = self._bakeoff
        fields = bakeoff.not_adjudicated_fields()
        assert fields["terminal_verdict"] is None
        assert fields["verdict_status"] == "NOT_ADJUDICATED"

        # Existing folder is never overwritten
        existing = tmp_path / "existing_run"
        existing.mkdir()
        (existing / "receipt.json").write_bytes(b'{"kept":true}')
        with pytest.raises(bakeoff.RunFolderExistsError) as exc_exists:
            bakeoff.persist_run_folder(existing, [("receipt.json", b'{"replaced":true}')])
        assert exc_exists.value.code == "RUN_FOLDER_EXISTS"
        assert (existing / "receipt.json").read_bytes() == b'{"kept":true}'

        # Exception during persistence writes failure_receipt.json with status RUN_FAILED
        failing = tmp_path / "failing_run"
        with pytest.raises(TypeError):
            bakeoff.persist_run_folder(
                failing,
                [("ok.json", b"{}"), ("broken.json", "not-bytes")],  # type: ignore[list-item]
            )
        failure_receipt = json.loads(
            (failing / "failure_receipt.json").read_text(encoding="utf-8")
        )
        assert failure_receipt["status"] == "RUN_FAILED"
        assert failure_receipt["error_type"] == "TypeError"

    def test_c005_bakeoff_test_source_documents_run150_counterexamples_and_custody_boundary(
        self,
    ) -> None:
        # Confirm projects/mssn_sn_symgam/challenges/run_150_tests_suite.py is outside this checkout
        external_runner = (
            REPO_ROOT / "projects" / "mssn_sn_symgam" / "challenges" / "run_150_tests_suite.py"
        )
        assert not external_runner.exists()

        test_src_path = (
            REPO_ROOT
            / "workflows"
            / "wf12_mechanism_control_arms"
            / "pilots"
            / "c005_hosted_decode_controls"
            / "test_c005_bakeoff.py"
        )
        tree = ast.parse(test_src_path.read_text(encoding="utf-8"))
        func_docs = {
            node.name: (ast.get_docstring(node) or "")
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        assert "VERIFIED rows" in func_docs["test_run150_track01_fallback_rows_are_not_run"]
        assert (
            "hard-coded attention masses"
            in func_docs["test_run150_track02_has_no_constant_measurements"]
        )
        assert "all 150 tests were executed" in func_docs["test_run150_suite_receipt_is_not_adjudicated"]

    def test_falsification_receipt_bound_tally_rejects_missing_receipt_and_exception_inflation(
        self, tmp_path: Path
    ) -> None:
        # Simulate 3 case outcomes: 1 valid stored receipt, 1 missing receipt, 1 exception-raising case
        receipt_path = tmp_path / "case_001_receipt.json"
        receipt_path.write_text(json.dumps({"verified_correct_count": 1}), encoding="utf-8")
        missing_path = tmp_path / "case_002_receipt.json"

        def evaluate_case_permissive(kind: str) -> str:
            try:
                if kind == "valid":
                    data = json.loads(receipt_path.read_text(encoding="utf-8"))
                    return "PASSED" if data["verified_correct_count"] == 1 else "FAILED"
                if kind == "missing":
                    if not missing_path.exists():
                        return "VERIFIED"
                    return "PASSED"
                raise RuntimeError("provider timeout")
            except RuntimeError:
                return "VERIFIED"

        def evaluate_case_strict(kind: str) -> str:
            try:
                if kind == "valid":
                    data = json.loads(receipt_path.read_text(encoding="utf-8"))
                    return "PASSED" if data["verified_correct_count"] == 1 else "FAILED"
                if kind == "missing":
                    if not missing_path.exists():
                        return "NOT_RUN"
                    return "PASSED"
                raise RuntimeError("provider timeout")
            except RuntimeError:
                return "FAILED"

        kinds = ("valid", "missing", "exception")
        perm_statuses = [evaluate_case_permissive(k) for k in kinds]
        strict_statuses = [evaluate_case_strict(k) for k in kinds]

        assert perm_statuses == ["PASSED", "VERIFIED", "VERIFIED"]
        assert sum(s in {"PASSED", "VERIFIED"} for s in perm_statuses) == 3

        assert strict_statuses == ["PASSED", "NOT_RUN", "FAILED"]
        assert sum(s == "PASSED" for s in strict_statuses) == 1


# ============================================================================
# Claim 4: AUDIT-P008-011 (ATL-P008-011) — Challenge census partition
# ============================================================================

_EXPECTED_CATEGORY_FOLDERS: frozenset[str] = frozenset(
    {
        "a_mechanism",
        "b_cohomology",
        "c_quantum",
        "d_physics_mtheory",
        "e_formal_math",
    }
)


def _is_sha1_hex(value: Any) -> bool:
    """Return True iff value is a lowercase 40-character hexadecimal SHA-1 digest."""
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _validate_census_record_category(rec: dict[str, Any]) -> None:
    """Enforce Category A/B/C structural, dual-checker, and no-tree_sha invariants on one record."""
    cid = str(rec.get("id", ""))
    cat = rec.get("category")
    if cat == "A":
        solvers = rec.get("reference_solver_files", [])
        checkers = rec.get("checker_files", [])
        valid_files = all(
            isinstance(f.get("path"), str)
            and f["path"].endswith(".py")
            and _is_sha1_hex(f.get("sha"))
            for f in [*solvers, *checkers]
        )
        if (
            "specification_blob" in rec
            or not _is_sha1_hex(rec.get("tree_sha"))
            or len(solvers) < 1
            or len(checkers) != 2
            or not valid_files
        ):
            raise ValueError(f"Category A structural invariant failed for {cid}")
    elif cat == "B":
        if (
            "specification_blob" in rec
            or not _is_sha1_hex(rec.get("tree_sha"))
            or rec.get("reference_solver_files") != []
            or rec.get("checker_files") != []
        ):
            raise ValueError(f"Category B structural invariant failed for {cid}")
    elif cat == "C":
        path = str(rec.get("path", ""))
        if (
            set(rec.keys()) != {"id", "path", "category", "specification_blob"}
            or not _is_sha1_hex(rec.get("specification_blob"))
            or not path.startswith("a_mechanism/c0")
            or not path.endswith(".md")
        ):
            raise ValueError(f"Category C structural invariant failed for {cid}")
    else:
        raise ValueError(f"Unknown census category {cat!r} for {cid}")


def _validate_historical_census_inventory(inv: dict[str, Any]) -> None:
    """Validate the 40+2+8=50 partition, C051 exclusion, dual checkers, and Category C keys."""
    if (
        inv.get("schema") != "pfp008.historical-census-inventory.v1"
        or inv.get("revision") != "a623568eb0f853b968bc419bf06dfc6af256ab02"
    ):
        raise ValueError("Invalid census schema or revision")

    tree_shas = inv.get("category_tree_shas", {})
    if set(tree_shas) != _EXPECTED_CATEGORY_FOLDERS or not all(
        _is_sha1_hex(v) for v in tree_shas.values()
    ):
        raise ValueError("Invalid category_tree_shas folder set or digest")

    records = inv.get("challenges", [])
    expected_ids = [f"C{i:03d}" for i in range(1, 51)]
    if [r.get("id") for r in records] != expected_ids:
        raise ValueError("Census challenges must be ordered C001..C050 (C051 excluded)")

    for rec in records:
        cid = str(rec["id"])
        path = str(rec.get("path", ""))
        folder, sep, leaf = path.partition("/")
        if not sep or folder not in _EXPECTED_CATEGORY_FOLDERS or not leaf.startswith(
            f"{cid.lower()}_"
        ):
            raise ValueError(f"Record {cid} path {path!r} violates in-range folder/slug binding")
        _validate_census_record_category(rec)

    cat_a = {r["id"] for r in records if r["category"] == "A"}
    cat_b = {r["id"] for r in records if r["category"] == "B"}
    cat_c = {r["id"] for r in records if r["category"] == "C"}
    if (
        cat_a != {f"C{i:03d}" for i in range(11, 51)}
        or cat_b != {"C001", "C005"}
        or cat_c != {"C002", "C003", "C004", "C006", "C007", "C008", "C009", "C010"}
    ):
        raise ValueError("Census 40+2+8 partition sets do not match C011..C050 / B / C")


class TestChallengeCensusPartition:
    """Verify the 40+2+8=50 challenge census partition at a623568e and membership caveats."""

    @staticmethod
    def _load_census_inventory() -> dict[str, Any]:
        path = PAPER_008_DIR / "docs" / "historical_census_inventory.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_exact_disjoint_40_2_8_partition_of_c001_to_c050_at_a623568e(self) -> None:
        # Confirm prior TestRunnerLabelInsufficiency teardown left zero wf12 modules in sys.modules
        assert [
            k for k in sys.modules if k.startswith("workflows.wf12_mechanism_control_arms")
        ] == []

        inv = self._load_census_inventory()
        _validate_historical_census_inventory(inv)
        assert inv["schema"] == "pfp008.historical-census-inventory.v1"
        assert inv["revision"] == "a623568eb0f853b968bc419bf06dfc6af256ab02"
        assert set(inv["category_tree_shas"]) == _EXPECTED_CATEGORY_FOLDERS
        for tree_sha in inv["category_tree_shas"].values():
            assert re.fullmatch(r"[0-9a-f]{40}", tree_sha) is not None

        records = inv["challenges"]
        assert len(records) == 50
        expected_universe = {f"C{i:03d}" for i in range(1, 51)}
        observed_ids = [r["id"] for r in records]
        assert observed_ids == [f"C{i:03d}" for i in range(1, 51)]
        assert set(observed_ids) == expected_universe

        cat_a = {r["id"] for r in records if r["category"] == "A"}
        cat_b = {r["id"] for r in records if r["category"] == "B"}
        cat_c = {r["id"] for r in records if r["category"] == "C"}

        assert len(cat_a) == 40
        assert len(cat_b) == 2
        assert len(cat_c) == 8
        assert len(cat_a) + len(cat_b) + len(cat_c) == 50

        assert cat_a == {f"C{i:03d}" for i in range(11, 51)}
        assert cat_b == {"C001", "C005"}
        assert cat_c == {"C002", "C003", "C004", "C006", "C007", "C008", "C009", "C010"}

        assert cat_a.isdisjoint(cat_b)
        assert cat_a.isdisjoint(cat_c)
        assert cat_b.isdisjoint(cat_c)
        assert (cat_a | cat_b | cat_c) == expected_universe

    def test_category_structural_predicates_and_c051_out_of_range_accounting(self) -> None:
        inv = self._load_census_inventory()
        _validate_historical_census_inventory(inv)
        for rec in inv["challenges"]:
            cat = rec["category"]
            if cat == "A":
                assert re.fullmatch(r"[0-9a-f]{40}", rec["tree_sha"]) is not None
                assert len(rec["reference_solver_files"]) >= 1
                assert len(rec["checker_files"]) == 2
                for f in rec["reference_solver_files"] + rec["checker_files"]:
                    assert f["path"].endswith(".py")
                    assert re.fullmatch(r"[0-9a-f]{40}", f["sha"]) is not None
            elif cat == "B":
                assert re.fullmatch(r"[0-9a-f]{40}", rec["tree_sha"]) is not None
                assert rec["reference_solver_files"] == []
                assert rec["checker_files"] == []
            else:
                assert cat == "C"
                assert set(rec.keys()) == {"id", "path", "category", "specification_blob"}
                assert re.fullmatch(r"[0-9a-f]{40}", rec["specification_blob"]) is not None
                assert rec["path"].startswith("a_mechanism/c0")
                assert rec["path"].endswith(".md")

        # C051 is outside C001..C050 in historical_census_inventory.json and documented
        # in paper.md and challenge_census.md
        assert set(inv["category_tree_shas"].keys()) == _EXPECTED_CATEGORY_FOLDERS
        assert all(r["id"] != "C051" for r in inv["challenges"])
        paper_md = (PAPER_008_DIR / "paper.md").read_text(encoding="utf-8")
        assert "C051, outside the audited\nrange, is a forty-first delivered package." in paper_md
        census_md = (PAPER_008_DIR / "docs" / "challenge_census.md").read_text(encoding="utf-8")
        assert "C051 lies outside that range" in census_md
        assert (
            "| C051 | `f_program_synthesis/c051_exact_lp_solver_with_duals` | "
            "`exact_checker.py` + `independent_checker.py` | 0 | 64 | 48 | none retained |"
            in census_md
        )

    def test_markdown_census_tables_reconcile_with_historical_inventory_json(self) -> None:
        inv = self._load_census_inventory()
        by_id = {r["id"]: r for r in inv["challenges"]}
        census_md = (PAPER_008_DIR / "docs" / "challenge_census.md").read_text(encoding="utf-8")

        # Parse Category A table rows | C0XX | `folder` | `chk1` + `chk2` | tests | hidden | mut | receipt |
        cat_a_rows: dict[str, tuple[str, int, str]] = {}
        for line in census_md.splitlines():
            m = re.match(
                r"^\|\s*(C0\d{2})\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\+\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|$",
                line,
            )
            if m:
                cid, folder, chk1, chk2, test_cnt, _hid, _mut, receipt_col = m.groups()
                cat_a_rows[cid] = (f"{folder}:{chk1}+{chk2}", int(test_cnt), receipt_col)

        assert set(cat_a_rows) == {f"C{i:03d}" for i in range(11, 52)}
        for i in range(11, 51):
            cid = f"C{i:03d}"
            rec = by_id[cid]
            joined_spec, md_test_cnt, receipt_col = cat_a_rows[cid]
            chk_names = [Path(f["path"]).name for f in rec["checker_files"]]
            assert joined_spec == f"{rec['path']}:{chk_names[0]}+{chk_names[1]}"
            assert md_test_cnt == len(rec["test_named_python_files"])
            if len(rec["scoring_receipt_files"]) == 0:
                assert receipt_col == "none retained"
            else:
                receipt_rel = rec["scoring_receipt_files"][0]["path"]
                assert receipt_rel in receipt_col

    def test_membership_only_obligations_tests_receipts_and_c047_print_only_ast(self) -> None:
        inv = self._load_census_inventory()
        cat_a = [r for r in inv["challenges"] if r["category"] == "A"]

        zero_test_ids = [r["id"] for r in cat_a if len(r["test_named_python_files"]) == 0]
        assert zero_test_ids == ["C048", "C049", "C050"]

        missing_receipt_ids = [r["id"] for r in cat_a if len(r["scoring_receipt_files"]) == 0]
        assert missing_receipt_ids == [
            "C015",
            "C016",
            "C017",
            "C018",
            "C019",
            "C020",
            "C045",
            "C046",
            "C047",
            "C048",
            "C049",
            "C050",
        ]
        assert len(missing_receipt_ids) == 12
        present_receipt_ids = [r["id"] for r in cat_a if len(r["scoring_receipt_files"]) > 0]
        assert len(present_receipt_ids) == 28
        assert "C014" in present_receipt_ids

        # C014 invalidation note in challenge_census.md
        census_md = (PAPER_008_DIR / "docs" / "challenge_census.md").read_text(encoding="utf-8")
        assert "C014" in census_md and "invalidated, rescore pending" in census_md

        # C047's sole test-named file in historical_census_inventory.json is judge_packet/test_cases_runner.py
        c047_rec = next(r for r in cat_a if r["id"] == "C047")
        assert [f["path"] for f in c047_rec["test_named_python_files"]] == [
            "judge_packet/test_cases_runner.py"
        ]

        # Inspect in-repo AST of C047's test_cases_runner.py:
        # zero Assert, zero Raise, zero sys.exit, zero mutation checks
        c047_runner_path = (
            REPO_ROOT
            / "workflows"
            / "tasks"
            / "certified_challenges"
            / "c047_sequence_law_discovery"
            / "judge_packet"
            / "test_cases_runner.py"
        )
        runner_src = c047_runner_path.read_text(encoding="utf-8")
        runner_ast = ast.parse(runner_src)
        assert [n for n in ast.walk(runner_ast) if isinstance(n, ast.Assert)] == []
        assert [n for n in ast.walk(runner_ast) if isinstance(n, ast.Raise)] == []
        exit_calls = [
            n
            for n in ast.walk(runner_ast)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "exit"
        ]
        assert exit_calls == []
        assert "mutation" not in runner_src.lower()

    def test_falsification_withdrawn_v110_misclassification_fails_partition_predicates(
        self,
    ) -> None:
        inv = self._load_census_inventory()
        _validate_historical_census_inventory(inv)
        by_id = {r["id"]: r for r in inv["challenges"]}

        # Paper 008 v1.1.0 (paper_change_log.md lines 71-76) misclassified C012 and C022 as lacking
        # reference solvers; verify both actually carry delivered solver packages, dual checkers, and receipts.
        for cid in ("C012", "C022"):
            rec = by_id[cid]
            assert rec["category"] == "A"
            solver_paths = [f["path"] for f in rec["reference_solver_files"]]
            assert "reference_solver/solver.py" in solver_paths
            assert len(rec["checker_files"]) == 2
            assert len(rec["scoring_receipt_files"]) == 1

        # Falsification of collapsing Category B and Category C: C001/C005 have directory tree_shas
        # whereas C002-C004 and C006-C010 have specification_blob Markdown files only.
        for cid in ("C001", "C005"):
            assert by_id[cid]["tree_sha"] is not None
            assert "specification_blob" not in by_id[cid]
        for cid in ("C002", "C003", "C004", "C006", "C007", "C008", "C009", "C010"):
            assert "tree_sha" not in by_id[cid]
            assert by_id[cid]["specification_blob"] is not None

        # 1. Mutating C012 from Category "A" to "B" (either keeping or clearing solvers/checkers) is rejected
        mut_c012_b_raw = copy.deepcopy(inv)
        c012_raw = next(r for r in mut_c012_b_raw["challenges"] if r["id"] == "C012")
        c012_raw["category"] = "B"
        with pytest.raises(ValueError, match="Category B"):
            _validate_historical_census_inventory(mut_c012_b_raw)

        mut_c012_b_partition = copy.deepcopy(inv)
        c012_part = next(r for r in mut_c012_b_partition["challenges"] if r["id"] == "C012")
        c012_part["category"] = "B"
        c012_part["reference_solver_files"] = []
        c012_part["checker_files"] = []
        with pytest.raises(ValueError, match="partition sets"):
            _validate_historical_census_inventory(mut_c012_b_partition)

        # 2. Missing second checker on a Category "A" entry is rejected
        mut_missing_checker = copy.deepcopy(inv)
        c011_mut = next(r for r in mut_missing_checker["challenges"] if r["id"] == "C011")
        c011_mut["checker_files"] = c011_mut["checker_files"][:1]
        with pytest.raises(ValueError, match="Category A"):
            _validate_historical_census_inventory(mut_missing_checker)

        # 3. Smuggling C051 inside 1..50 as C050 (or appending C051) is rejected
        mut_c051_as_c050 = copy.deepcopy(inv)
        mut_c051_as_c050["challenges"][-1]["path"] = (
            "f_program_synthesis/c051_exact_lp_solver_with_duals"
        )
        with pytest.raises(ValueError, match="folder/slug"):
            _validate_historical_census_inventory(mut_c051_as_c050)

        mut_c051_in_e_folder = copy.deepcopy(inv)
        mut_c051_in_e_folder["challenges"][-1]["path"] = (
            "e_formal_math/c051_exact_lp_solver_with_duals"
        )
        with pytest.raises(ValueError, match="folder/slug"):
            _validate_historical_census_inventory(mut_c051_in_e_folder)

        mut_c051_appended = copy.deepcopy(inv)
        c051_entry = copy.deepcopy(mut_c051_appended["challenges"][-1])
        c051_entry["id"] = "C051"
        c051_entry["path"] = "f_program_synthesis/c051_exact_lp_solver_with_duals"
        mut_c051_appended["challenges"].append(c051_entry)
        with pytest.raises(ValueError, match="C051 excluded"):
            _validate_historical_census_inventory(mut_c051_appended)

        # 4. Giving Category "C" entry C002 a directory tree_sha is rejected
        mut_c002_tree = copy.deepcopy(inv)
        c002_mut = next(r for r in mut_c002_tree["challenges"] if r["id"] == "C002")
        c002_mut["tree_sha"] = "2e1c40e78386cffa781002c7c75ece9db9c1b9c8"
        with pytest.raises(ValueError, match="Category C"):
            _validate_historical_census_inventory(mut_c002_tree)
