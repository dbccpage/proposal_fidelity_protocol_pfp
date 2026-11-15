"""Verification suite for Window 3 Wave 1 Shard C (Paper 005).

Targets four audit derivations:
1. AUDIT-P005-004: Worked session refusal of (5,0,0), admission of (-2,1,1),
   and snapshot restoration.
2. AUDIT-P005-005: Quickstart native delegation to compute_graph_phi1 and
   strict refusal of missing pins and non-exact inputs.
3. AUDIT-P005-006: step_cut admission gating requiring defect_after <= defect_before,
   explicitly permitting stationary moves.
4. AUDIT-P005-009: Test fixture native_functional isolation, skipping only dependent
   tests with declared SKIP_REASON when unconfigured.
"""

from __future__ import annotations

import hashlib
import importlib
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PFP005_CODE = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "005_pfp_practitioners_field_manual"
    / "code"
)
_PFP005_TESTS = _PFP005_CODE / "tests"
_ISOLATED_NAMES = (
    "conftest",
    "native_functional",
    "l1_symbol_game_governor",
    "play_demo",
    "quickstart",
)


def _load_isolated_pfp005_modules() -> dict[str, Any]:
    """Import Paper 005 modules without colliding with earlier Paper 004 imports."""
    saved_modules = {name: sys.modules.pop(name) for name in _ISOLATED_NAMES if name in sys.modules}
    saved_path = list(sys.path)
    try:
        sys.path[:0] = [str(_PFP005_TESTS), str(_PFP005_CODE)]
        return {name: importlib.import_module(name) for name in _ISOLATED_NAMES}
    finally:
        sys.path[:] = saved_path
        for name in _ISOLATED_NAMES:
            sys.modules.pop(name, None)
        sys.modules.update(saved_modules)


_PFP005_MODULES = _load_isolated_pfp005_modules()
conftest = _PFP005_MODULES["conftest"]
gov_mod = _PFP005_MODULES["l1_symbol_game_governor"]
nf_mod = _PFP005_MODULES["native_functional"]
play_demo = _PFP005_MODULES["play_demo"]
qs_mod = _PFP005_MODULES["quickstart"]


@pytest.fixture(autouse=True)
def _pin_pfp005_sys_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep lazy imports inside Paper 005 helpers bound to Paper 005 modules."""
    for name, mod in _PFP005_MODULES.items():
        monkeypatch.setitem(sys.modules, name, mod)


class TestWorkedSession:
    """Verifies AUDIT-P005-004: Worked session on the enumeration path."""

    def test_worked_session_enumeration_rejection_admission_and_retract(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Confirms refusal of (5,0,0), admission of (-2,1,1), and state restoration."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

        graph = gov_mod.ConstraintGraph(
            vertices=("a", "b", "c"),
            edges=(
                gov_mod.Edge("a", "b", 1),
                gov_mod.Edge("b", "c", 2),
                gov_mod.Edge("c", "a", 3),
            ),
        )
        gov = gov_mod.L1SymbolGameGovernor(graph)

        # 1. ASSERT initial claims (1, 1, 1)
        gov.step_assert("a", "b", Fraction(1))
        gov.step_assert("b", "c", Fraction(1))
        v_last = gov.step_assert("c", "a", Fraction(1))
        snapshot = v_last.step_id

        phi_initial = gov.primary_obstruction()
        assert phi_initial == Fraction(3)
        assert gov.edge_claims[("a", "b")] == Fraction(1)
        assert gov.edge_claims[("b", "c")] == Fraction(1)
        assert gov.edge_claims[("c", "a")] == Fraction(1)

        # 2. CUT (rejected): proposing (5, 0, 0) increases discrepancy to 5
        bad = {
            ("a", "b"): Fraction(5),
            ("b", "c"): Fraction(0),
            ("c", "a"): Fraction(0),
        }
        v_bad = gov.step_cut(proposed_claims=bad)
        assert v_bad.admitted is False
        assert v_bad.status == "DefectIncrease"
        assert v_bad.defect_before == Fraction(3)
        assert v_bad.defect_after == Fraction(5)
        # Active claims must remain untouched
        assert gov.edge_claims[("a", "b")] == Fraction(1)
        assert gov.edge_claims[("b", "c")] == Fraction(1)
        assert gov.edge_claims[("c", "a")] == Fraction(1)

        # 3. CUT (admitted): proposing (-2, 1, 1) reduces discrepancy to 0
        repaired = {
            ("a", "b"): Fraction(-2),
            ("b", "c"): Fraction(1),
            ("c", "a"): Fraction(1),
        }
        v_good = gov.step_cut(proposed_claims=repaired)
        assert v_good.admitted is True
        assert v_good.status == "ExactRepair"
        assert v_good.defect_before == Fraction(3)
        assert v_good.defect_after == Fraction(0)
        assert gov.primary_obstruction() == Fraction(0)
        assert gov.edge_claims[("a", "b")] == Fraction(-2)

        # 4. VERIFY: ZERO_OBSTRUCTION confirmed
        v_verify = gov.step_verify("ZERO_OBSTRUCTION")
        assert v_verify.admitted is True

        # 5. RETRACT: rollback to post-assertion snapshot restores obstruction to 3
        gov.step_retract(snapshot, reason="demonstrate rollback")
        assert gov.primary_obstruction() == Fraction(3)
        assert gov.edge_claims[("a", "b")] == Fraction(1)
        assert gov.edge_claims[("b", "c")] == Fraction(1)
        assert gov.edge_claims[("c", "a")] == Fraction(1)

    def test_run_session_enumeration_table_parity(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Checks that play_demo.run_session outputs the expected table dictionary."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

        res = play_demo.run_session(verbose=False)
        assert res["calculation_path"] == "python-enumeration"
        assert res["weights"] == (1, 2, 3)
        assert res["phi_after_assert"] == Fraction(3)
        assert res["bad_status"] == "DefectIncrease"
        assert res["bad_admitted"] is False
        assert res["repair_status"] == "ExactRepair"
        assert res["repair_before"] == Fraction(3)
        assert res["repair_after"] == Fraction(0)
        assert res["verify_admitted"] is True
        assert res["phi_after_retract"] == Fraction(3)

    def test_worked_session_refusal_negative_controls(self) -> None:
        """Negative controls: non-exact inputs, incomplete cuts, and bad retractions."""
        graph = gov_mod.ConstraintGraph(
            vertices=("a", "b", "c"),
            edges=(
                gov_mod.Edge("a", "b", 1),
                gov_mod.Edge("b", "c", 2),
                gov_mod.Edge("c", "a", 3),
            ),
        )
        gov = gov_mod.L1SymbolGameGovernor(graph)
        gov.step_assert("a", "b", Fraction(1))
        gov.step_assert("b", "c", Fraction(1))
        gov.step_assert("c", "a", Fraction(1))

        # Incomplete proposal (omitting declared edge)
        v_incomplete = gov.step_cut(
            proposed_claims={
                ("a", "b"): Fraction(0),
                ("b", "c"): Fraction(0),
            }
        )
        assert v_incomplete.admitted is False
        assert v_incomplete.status == "IncompleteProposal"

        # Non-exact proposal containing float
        v_float = gov.step_cut(
            proposed_claims={
                ("a", "b"): 0.5,  # type: ignore[dict-item]
                ("b", "c"): Fraction(0),
                ("c", "a"): Fraction(0),
            }
        )
        assert v_float.admitted is False
        assert v_float.status == "IncompleteProposal"

        # Retracting to a nonexistent snapshot ID returns refused verdict fail-closed
        v_retract = gov.step_retract("nonexistent_snapshot_id")
        assert v_retract.admitted is False
        assert v_retract.status == "Refused"
        assert "not found in derivation history" in v_retract.details


class TestQuickstartNativeDelegation:
    """Verifies AUDIT-P005-005: Quickstart native delegation and input rejection."""

    def test_quickstart_requires_native_pin_and_digest(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """compute_discrete_l1_projection raises NativeFunctionalUnavailable when unpinned."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

        graph, claims = qs_mod.build_default_meeting_conflict().to_graph_and_cochain()
        with pytest.raises(nf_mod.NativeFunctionalUnavailable) as exc_info:
            qs_mod.compute_discrete_l1_projection(graph, claims)
        assert "pinned native graph executable required" in str(exc_info.value)

    def test_quickstart_refuses_malformed_sha256(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Rejects non-64-hex SHA-256 strings with NativeFunctionalUnavailable."""
        dummy_bin = tmp_path / "dummy.exe"
        dummy_bin.write_bytes(b"dummy")

        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", str(dummy_bin))
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_SHA256", "invalid_hash_string")

        graph, claims = qs_mod.build_default_meeting_conflict().to_graph_and_cochain()
        with pytest.raises(nf_mod.NativeFunctionalUnavailable) as exc_info:
            qs_mod.compute_discrete_l1_projection(graph, claims)
        assert "pinned native graph executable required" in str(exc_info.value)

    def test_quickstart_refuses_digest_mismatch(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Rejects mismatched SHA-256 digests with NativeFunctionalUnavailable."""
        dummy_bin = tmp_path / "dummy.exe"
        dummy_bin.write_bytes(b"dummy_executable_content")

        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", str(dummy_bin))
        # Provide valid 64-hex string that differs from the file's actual digest
        wrong_digest = "0" * 64
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_SHA256", wrong_digest)

        graph, claims = qs_mod.build_default_meeting_conflict().to_graph_and_cochain()
        with pytest.raises(nf_mod.NativeFunctionalUnavailable) as exc_info:
            qs_mod.compute_discrete_l1_projection(graph, claims)
        assert "native graph executable digest mismatch" in str(exc_info.value)

    def test_quickstart_retires_candidate_enumeration(self) -> None:
        """Historical candidate enumeration raises RuntimeError."""
        graph, claims = qs_mod.build_default_meeting_conflict().to_graph_and_cochain()
        with pytest.raises(RuntimeError, match="RUST_FUNCTIONAL_REQUIRED"):
            qs_mod.find_spanning_forest_potentials(graph, claims)

    def test_quickstart_refuses_approximate_and_boolean_inputs(self) -> None:
        """Edge and Cochain1 enforce exact integer or Fraction types."""
        # Floating point edge weight
        with pytest.raises(TypeError):
            qs_mod.Edge("Alice", "Bob", weight=1.5)  # type: ignore[arg-type]

        # Boolean edge weight
        with pytest.raises(TypeError):
            qs_mod.Edge("Alice", "Bob", weight=True)  # type: ignore[arg-type]

        # Non-positive edge weight
        with pytest.raises(ValueError):
            qs_mod.Edge("Alice", "Bob", weight=0)
        with pytest.raises(ValueError):
            qs_mod.Edge("Alice", "Bob", weight=-1)

        # Self-loop edge
        with pytest.raises(ValueError, match="violates irreflexivity"):
            qs_mod.Edge("Alice", "Alice", weight=1)

        # Floating point cochain value
        with pytest.raises(TypeError):
            qs_mod.Cochain1(values={("Alice", "Bob"): 2.5})  # type: ignore[dict-item]

        # Boolean cochain value
        with pytest.raises(TypeError):
            qs_mod.Cochain1(values={("Alice", "Bob"): False})  # type: ignore[dict-item]

        # Adapter internal exact check
        with pytest.raises(TypeError):
            nf_mod._exact(1.23)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            nf_mod._exact(True)  # type: ignore[arg-type]


class TestCutNonIncrease:
    """Verifies AUDIT-P005-006: step_cut weak monotonic descent and stationary moves."""

    @pytest.fixture
    def governor(self) -> gov_mod.L1SymbolGameGovernor:
        graph = gov_mod.ConstraintGraph(
            vertices=("a", "b", "c"),
            edges=(
                gov_mod.Edge("a", "b", 1),
                gov_mod.Edge("b", "c", 2),
                gov_mod.Edge("c", "a", 3),
            ),
        )
        gov = gov_mod.L1SymbolGameGovernor(graph)
        gov.step_assert("a", "b", Fraction(1))
        gov.step_assert("b", "c", Fraction(1))
        gov.step_assert("c", "a", Fraction(1))
        return gov

    def test_cut_admits_strict_descent(
        self, governor: gov_mod.L1SymbolGameGovernor
    ) -> None:
        """Proposals yielding defect_after < defect_before are admitted."""
        # Initial defect is 3
        assert governor.primary_obstruction() == Fraction(3)

        # Exact repair brings defect to 0 (< 3)
        v = governor.step_cut(
            proposed_claims={
                ("a", "b"): Fraction(-2),
                ("b", "c"): Fraction(1),
                ("c", "a"): Fraction(1),
            }
        )
        assert v.admitted is True
        assert v.status == "ExactRepair"
        assert v.defect_before == Fraction(3)
        assert v.defect_after == Fraction(0)

    def test_cut_admits_stationary_move(
        self, governor: gov_mod.L1SymbolGameGovernor
    ) -> None:
        """Proposals yielding defect_after == defect_before are admitted with IdempotentStationary."""
        assert governor.primary_obstruction() == Fraction(3)

        # Relational CUT: claims (2, 1, 0) also produce primary obstruction = 3
        v_rel = governor.step_cut(
            proposed_claims={
                ("a", "b"): Fraction(2),
                ("b", "c"): Fraction(1),
                ("c", "a"): Fraction(0),
            }
        )
        assert v_rel.admitted is True
        assert v_rel.status == "IdempotentStationary"
        assert v_rel.defect_before == Fraction(3)
        assert v_rel.defect_after == Fraction(3)
        # Verify claims were indeed updated to the new configuration
        assert governor.edge_claims[("a", "b")] == Fraction(2)
        assert governor.edge_claims[("b", "c")] == Fraction(1)
        assert governor.edge_claims[("c", "a")] == Fraction(0)

        # Section CUT: proposing current section preserves section defect
        sec_before = governor.section_defect()
        v_sec = governor.step_cut(proposed_section=dict(governor.section))
        assert v_sec.admitted is True
        assert v_sec.status == "IdempotentStationary"
        assert v_sec.defect_before == sec_before
        assert v_sec.defect_after == sec_before

    def test_cut_refuses_strict_increase(
        self, governor: gov_mod.L1SymbolGameGovernor
    ) -> None:
        """Proposals yielding defect_after > defect_before are refused with DefectIncrease."""
        assert governor.primary_obstruction() == Fraction(3)

        # Proposed claims yielding Phi_1 = 5 (> 3)
        v_bad = governor.step_cut(
            proposed_claims={
                ("a", "b"): Fraction(5),
                ("b", "c"): Fraction(0),
                ("c", "a"): Fraction(0),
            }
        )
        assert v_bad.admitted is False
        assert v_bad.status == "DefectIncrease"
        assert v_bad.defect_before == Fraction(3)
        assert v_bad.defect_after == Fraction(5)
        # Active claims remain untouched
        assert governor.edge_claims[("a", "b")] == Fraction(1)

    def test_boundary_exact_rational_comparison(
        self, governor: gov_mod.L1SymbolGameGovernor
    ) -> None:
        """Boundary test: new == old is admitted; new == old + epsilon is refused."""
        current = governor.primary_obstruction()
        assert current == Fraction(3)

        # Stationary proposal (exact equality)
        v_equal = governor.step_cut(
            proposed_claims={
                ("a", "b"): Fraction(2),
                ("b", "c"): Fraction(1),
                ("c", "a"): Fraction(0),
            }
        )
        assert v_equal.admitted is True

        # Any increase above 3 (e.g. cycle sum 3 + 1/1000 = 3001/1000) is refused
        v_incr = governor.step_cut(
            proposed_claims={
                ("a", "b"): Fraction(2) + Fraction(1, 1000),
                ("b", "c"): Fraction(1),
                ("c", "a"): Fraction(0),
            }
        )
        assert v_incr.admitted is False
        assert v_incr.status == "DefectIncrease"


class TestNativeFixtureSkip:
    """Verifies AUDIT-P005-009: Fixture skip behavior and isolation."""

    def test_unconfigured_fixture_skips_with_declared_reason(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without configuration, invoking native_functional raises Skipped with SKIP_REASON."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

        fn = conftest.native_functional.__wrapped__
        with pytest.raises(pytest.skip.Exception) as exc_info:
            fn()

        assert conftest.SKIP_REASON in str(exc_info.value)
        assert "native graph calculator not configured" in str(exc_info.value)

    def test_tests_not_requesting_fixture_do_not_skip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Tests that do not declare native_functional run and pass without skipping."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

        # Calling run_session runs entirely on Python enumeration
        session_result = play_demo.run_session(verbose=False)
        assert session_result["calculation_path"] == "python-enumeration"

        # Calling quickstart pin check runs and raises expected exception without skipping
        graph, claims = qs_mod.build_default_meeting_conflict().to_graph_and_cochain()
        with pytest.raises(nf_mod.NativeFunctionalUnavailable):
            qs_mod.compute_discrete_l1_projection(graph, claims)

    def test_malformed_pin_fails_rather_than_skips(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """When configuration is malformed, fixture calls pytest.fail rather than pytest.skip."""
        dummy_bin = tmp_path / "solve_graph_phi1"
        dummy_bin.write_bytes(b"content")

        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", str(dummy_bin))
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_SHA256", "too_short")

        fn = conftest.native_functional.__wrapped__
        with pytest.raises(pytest.fail.Exception) as exc_info:
            fn()
        assert "CORE_FUNCTIONAL_GRAPH_SHA256 must contain exactly 64 hex digits" in str(
            exc_info.value
        )

    def test_missing_binary_file_fails_rather_than_skips(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """When binary cannot be read, fixture calls pytest.fail rather than pytest.skip."""
        nonexistent = tmp_path / "nonexistent_solver.exe"
        valid_digest = "a" * 64

        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", str(nonexistent))
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_SHA256", valid_digest)

        fn = conftest.native_functional.__wrapped__
        with pytest.raises(pytest.fail.Exception) as exc_info:
            fn()
        assert "could not be read" in str(exc_info.value)

    def test_digest_mismatch_fails_rather_than_skips(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """When binary digest diverges from expected pin, fixture calls pytest.fail."""
        dummy_bin = tmp_path / "solver.exe"
        dummy_bin.write_bytes(b"test_binary_payload")
        actual_digest = hashlib.sha256(b"test_binary_payload").hexdigest()
        different_digest = (
            "b" * 64 if actual_digest != "b" * 64 else "c" * 64
        )

        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", str(dummy_bin))
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_SHA256", different_digest)

        fn = conftest.native_functional.__wrapped__
        with pytest.raises(pytest.fail.Exception) as exc_info:
            fn()
        assert "digest mismatch" in str(exc_info.value)
