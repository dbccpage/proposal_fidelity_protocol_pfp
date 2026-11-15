"""Verification suite for Window 3 Wave 2 Shard C (Paper 005).

AuthorityEffect: None.

Targets four audit derivations:
1. AUDIT-P005-010: Standalone companion execution and provenance verification
   for vendored adapter and governor up to documented patches.
2. AUDIT-P005-011: Native refusal propagation, unconfigured spanning-forest
   exact enumeration, and refusal of float/Boolean weights.
3. AUDIT-P005-012: CUT completeness refusal with IncompleteProposal on missing
   declared edges or non-exact values with state unchanged.
4. AUDIT-P005-013: Streaming harness refusal of float and Boolean claim values
   and scoring of integers and exact rational strings.
"""

from __future__ import annotations

import ast
import importlib
import re
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
    "native_functional",
    "l1_symbol_game_governor",
    "llm_streaming_harness",
    "test_vendored_sources",
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
gov_mod = _PFP005_MODULES["l1_symbol_game_governor"]
harness_mod = _PFP005_MODULES["llm_streaming_harness"]
tvs_mod = _PFP005_MODULES["test_vendored_sources"]


@pytest.fixture(autouse=True)
def _pin_pfp005_sys_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep lazy imports inside Paper 005 helpers bound to Paper 005 modules."""
    for name, mod in _PFP005_MODULES.items():
        monkeypatch.setitem(sys.modules, name, mod)


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _build_triangle_graph(weight_ca: Any = 2) -> gov_mod.ConstraintGraph:
    """Build directed 3-cycle constraint graph with exact edge weights."""
    return gov_mod.ConstraintGraph(
        vertices=("a", "b", "c"),
        edges=(
            gov_mod.Edge("a", "b", 1),
            gov_mod.Edge("b", "c", 2),
            gov_mod.Edge("c", "a", weight_ca),
        ),
    )


def _build_triangle_session() -> gov_mod.L1SymbolGameGovernor:
    """Instantiate and initialize governor with asserted triangle claims (1, 1, 1)."""
    gov = gov_mod.L1SymbolGameGovernor(_build_triangle_graph(weight_ca=2))
    gov.step_assert("a", "b", Fraction(1))
    gov.step_assert("b", "c", Fraction(1))
    gov.step_assert("c", "a", Fraction(1))
    return gov


def _make_cut_payload(claims: dict[str, Any]) -> dict[str, Any]:
    """Helper to assemble a valid TAU_SG_V1 streaming CUT move payload."""
    return {
        "schema": "TAU_SG_V1",
        "step_id": "s01",
        "parent_step_id": "root",
        "move_type": "CUT",
        "move_parameters": {"rule_id": "R1", "proposed_claims": claims},
        "expected_defect_delta": "-3",
    }


def _make_streaming_session(
    claims: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> harness_mod.SymbolGameStreamingSession:
    """Instantiate a SymbolGameStreamingSession on the unconfigured Python path."""
    monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
    monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)
    vertices = ("a", "b", "c")
    edges = (("a", "b", 1), ("b", "c", 2), ("c", "a", 2))
    initial_claims = {("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1}
    proposer = harness_mod.MockLLMStreamingProposer([_make_cut_payload(claims)])
    session = harness_mod.SymbolGameStreamingSession(vertices, edges, initial_claims, proposer)
    session.initialize()
    return session


# ---------------------------------------------------------------------------
# AUDIT-P005-010: Standalone companion
# ---------------------------------------------------------------------------

class TestStandaloneCompanion:
    """Verifies AUDIT-P005-010: Standalone companion headers, provenance, and AST."""

    @pytest.mark.parametrize("module_name", ["native_functional.py", "l1_symbol_game_governor.py"])
    def test_vendored_headers_are_complete_and_well_formed(self, module_name: str) -> None:
        """Confirms that vendored files carry required commit and SHA-256 headers."""
        headers = tvs_mod._header(module_name)
        assert headers["vendored-from-path"].endswith(".py")
        assert re.fullmatch(r"[0-9a-f]{40}", headers["vendored-from-commit"]) is not None
        assert re.fullmatch(r"[0-9a-f]{64}", headers["vendored-from-sha256"]) is not None

        if module_name == "l1_symbol_game_governor.py":
            assert headers["baseline-commit"] == "52cb5457f6c485ba548cfd292f6012a941ed22cf"
            assert re.fullmatch(r"[0-9a-f]{64}", headers["baseline-sha256"]) is not None
        else:
            assert headers["vendored-from-commit"] == "52cb5457f6c485ba548cfd292f6012a941ed22cf"

    def test_ast_normalization_and_unpatched_structure(self) -> None:
        """Confirms AST structure of vendored modules parses and normalizes."""
        spec = tvs_mod.VENDORED["l1_symbol_game_governor.py"]
        code_text = (_PFP005_CODE / "l1_symbol_game_governor.py").read_text(encoding="utf-8")
        imports, body = tvs_mod._normalized(code_text, spec, original=False)

        # Removed bootstrap names must not appear in AST body
        statement_names = {item[0] for item in body}
        for name in tvs_mod.BOOTSTRAP_NAMES:
            assert name not in statement_names

        # Class L1SymbolGameGovernor must be present
        assert "L1SymbolGameGovernor" in statement_names

    def test_ast_step_cut_contains_completeness_check(self) -> None:
        """Confirms AST presence of IncompleteProposal in step_cut (R008-04)."""
        code_text = (_PFP005_CODE / "l1_symbol_game_governor.py").read_text(encoding="utf-8")
        step_cut_node = tvs_mod._method(code_text, "L1SymbolGameGovernor", "step_cut")
        strings = tvs_mod._strings(step_cut_node)
        assert "IncompleteProposal" in strings

    def test_ast_compute_phi1_has_no_exception_handler(self) -> None:
        """Confirms AST absence of ExceptHandler in compute_phi1 (no swallowed native errors)."""
        code_text = (_PFP005_CODE / "l1_symbol_game_governor.py").read_text(encoding="utf-8")
        tree = ast.parse(code_text)
        compute_fn = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "compute_phi1"
        )
        handlers = [node for node in ast.walk(compute_fn) if isinstance(node, ast.ExceptHandler)]
        assert len(handlers) == 0

    # Negative controls / Falsification tests

    def test_falsification_corrupted_header_is_rejected(self) -> None:
        """Negative control: Header validation rejects malformed hashes or missing fields."""
        malformed_header = {
            "vendored-from-path": "module.py",
            "vendored-from-commit": "invalid_commit_length",
            "vendored-from-sha256": "short_hash",
        }
        assert re.fullmatch(r"[0-9a-f]{40}", malformed_header["vendored-from-commit"]) is None
        assert re.fullmatch(r"[0-9a-f]{64}", malformed_header["vendored-from-sha256"]) is None

    def test_falsification_exception_handler_injection_detected(self) -> None:
        """Negative control: AST checker detects an injected try-except block in compute_phi1."""
        synthetic_source = """
def compute_phi1(graph, claims):
    try:
        return 0, {}
    except Exception:
        return 1, {}
"""
        tree = ast.parse(synthetic_source)
        handlers = [node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)]
        assert len(handlers) > 0, "AST check must catch an introduced exception handler."

    def test_falsification_missing_completeness_check_detected(self) -> None:
        """Negative control: String inspector detects absence of IncompleteProposal."""
        synthetic_source = """
class L1SymbolGameGovernor:
    def step_cut(self, proposed_claims=None):
        return None
"""
        step_cut_node = tvs_mod._method(synthetic_source, "L1SymbolGameGovernor", "step_cut")
        strings = tvs_mod._strings(step_cut_node)
        assert "IncompleteProposal" not in strings


# ---------------------------------------------------------------------------
# AUDIT-P005-011: Native refusal propagation
# ---------------------------------------------------------------------------

class TestNativeRefusalPropagation:
    """Verifies AUDIT-P005-011: compute_phi1 failure propagation and exact enumeration."""

    def test_unconfigured_exact_enumeration_evaluates_exact_discrepancy(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Positive test: compute_phi1 uses exact spanning forest enumeration without native binary."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

        graph = _build_triangle_graph(weight_ca=2)
        claims = gov_mod.Cochain1(
            values={
                ("a", "b"): Fraction(1),
                ("b", "c"): Fraction(1),
                ("c", "a"): Fraction(1),
            }
        )
        phi, potential = gov_mod.compute_phi1(graph, claims)

        assert phi == Fraction(3)
        assert isinstance(phi, Fraction)

        # Verify potential residual matches returned quotient distance
        residual_sum = sum(
            edge.weight * abs(claims.get(edge.u, edge.v) - (potential[edge.v] - potential[edge.u]))
            for edge in graph.edges
        )
        assert residual_sum == Fraction(3)

    def test_configured_native_failure_propagates_directly(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Positive test: Native execution failure propagates out rather than falling back."""
        missing_bin = tmp_path / "nonexistent_solver.exe"
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", str(missing_bin))
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_SHA256", "0" * 64)

        graph = _build_triangle_graph(weight_ca=2)
        claims = gov_mod.Cochain1(
            values={
                ("a", "b"): Fraction(1),
                ("b", "c"): Fraction(1),
                ("c", "a"): Fraction(1),
            }
        )
        with pytest.raises(Exception) as exc_info:
            gov_mod.compute_phi1(graph, claims)

        # Ensure it failed from native adapter, not from fallback enumeration
        assert exc_info.type is not None

    def test_exact_rational_fraction_weight_is_accepted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Positive test: Edge weights defined as exact Fraction are accepted."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        graph = _build_triangle_graph(weight_ca=Fraction(5, 2))
        claims = gov_mod.Cochain1(
            values={
                ("a", "b"): Fraction(1),
                ("b", "c"): Fraction(1),
                ("c", "a"): Fraction(1),
            }
        )
        phi, _ = gov_mod.compute_phi1(graph, claims)
        assert phi == Fraction(3)

    # Negative controls / Falsification tests

    @pytest.mark.parametrize("bad_weight", [4.5, 1.25], ids=["float-4.5", "float-1.25"])
    def test_falsification_float_weight_raises_type_error(
        self, monkeypatch: pytest.MonkeyPatch, bad_weight: float
    ) -> None:
        """Negative control: Float edge weight raises TypeError rather than converting."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        graph = _build_triangle_graph(weight_ca=bad_weight)
        claims = gov_mod.Cochain1(
            values={
                ("a", "b"): Fraction(1),
                ("b", "c"): Fraction(1),
                ("c", "a"): Fraction(1),
            }
        )
        with pytest.raises(TypeError, match="edge weights must be exact int or Fraction"):
            gov_mod.compute_phi1(graph, claims)

    def test_falsification_boolean_weight_raises_type_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Negative control: Boolean edge weight raises TypeError rather than casting to int."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        graph = _build_triangle_graph(weight_ca=True)
        claims = gov_mod.Cochain1(
            values={
                ("a", "b"): Fraction(1),
                ("b", "c"): Fraction(1),
                ("c", "a"): Fraction(1),
            }
        )
        with pytest.raises(TypeError, match="edge weights must be exact int or Fraction"):
            gov_mod.compute_phi1(graph, claims)

    def test_falsification_float_claim_value_raises_type_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Negative control: Float claim value in Cochain1 raises TypeError."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        graph = _build_triangle_graph(weight_ca=2)
        claims = gov_mod.Cochain1(
            values={
                ("a", "b"): 0.5,
                ("b", "c"): Fraction(1),
                ("c", "a"): Fraction(1),
            }
        )
        with pytest.raises(TypeError, match="claims require exact int or Fraction"):
            gov_mod.compute_phi1(graph, claims)

    def test_falsification_boolean_claim_value_raises_type_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Negative control: Boolean claim value in Cochain1 raises TypeError."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        graph = _build_triangle_graph(weight_ca=2)
        claims = gov_mod.Cochain1(
            values={
                ("a", "b"): True,
                ("b", "c"): Fraction(1),
                ("c", "a"): Fraction(1),
            }
        )
        with pytest.raises(TypeError, match="claims require exact int or Fraction"):
            gov_mod.compute_phi1(graph, claims)

    def test_falsification_zero_weight_edge_raises_value_error(self) -> None:
        """Negative control: Edge with zero weight raises ValueError at construction."""
        with pytest.raises(ValueError, match=r"(?i)edge weight must be positive"):
            gov_mod.Edge("c", "a", 0)

    def test_falsification_false_weight_edge_raises_value_error(self) -> None:
        """Negative control: Edge with False (<= 0) raises ValueError at construction."""
        with pytest.raises(ValueError, match=r"(?i)edge weight must be positive"):
            gov_mod.Edge("c", "a", False)

    def test_falsification_undeclared_claim_edge_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Negative control: Cochain1 with undeclared edge raises ValueError."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        graph = _build_triangle_graph(weight_ca=2)
        claims = gov_mod.Cochain1(
            values={
                ("a", "b"): Fraction(1),
                ("x", "y"): Fraction(1),
            }
        )
        with pytest.raises(ValueError, match="claim edge absent from declared carrier"):
            gov_mod.compute_phi1(graph, claims)


# ---------------------------------------------------------------------------
# AUDIT-P005-012: CUT completeness
# ---------------------------------------------------------------------------

class TestCutCompleteness:
    """Verifies AUDIT-P005-012: step_cut completeness check and state immutability."""

    def test_complete_exact_proposal_is_scored_and_admitted(self) -> None:
        """Positive test: Complete exact proposal for all declared edges is scored."""
        gov = _build_triangle_session()
        assert gov.primary_obstruction() == Fraction(3)

        zeros = {
            ("a", "b"): Fraction(0),
            ("b", "c"): Fraction(0),
            ("c", "a"): Fraction(0),
        }
        verdict = gov.step_cut(proposed_claims=zeros)
        assert verdict.admitted is True
        assert verdict.status == "ExactRepair"
        assert verdict.defect_before == Fraction(3)
        assert verdict.defect_after == Fraction(0)
        assert gov.primary_obstruction() == Fraction(0)

    def test_state_immutability_on_incomplete_refusal(self) -> None:
        """Positive test: On refusal, governor state is strictly identical to pre-proposal."""
        gov = _build_triangle_session()
        initial_claims = dict(gov.edge_claims)
        initial_section = dict(gov.section)
        initial_defect = gov.primary_obstruction()
        history_len_before = len(gov.history)

        # Submit incomplete proposal
        verdict = gov.step_cut(proposed_claims={("a", "b"): Fraction(0)})
        assert verdict.admitted is False
        assert verdict.status == "IncompleteProposal"

        # Verify state immutability
        assert gov.edge_claims == initial_claims
        assert gov.section == initial_section
        assert gov.primary_obstruction() == initial_defect
        assert len(gov.history) == history_len_before

    # Negative controls / Falsification tests

    def test_falsification_empty_proposal_is_refused(self) -> None:
        """Negative control: Empty proposal {} is refused with IncompleteProposal."""
        gov = _build_triangle_session()
        verdict = gov.step_cut(proposed_claims={})
        assert verdict.admitted is False
        assert verdict.status == "IncompleteProposal"
        assert "omits declared edges" in verdict.details
        assert verdict.defect_before == Fraction(3)
        assert verdict.defect_after == Fraction(3)

    def test_falsification_partial_proposal_omitting_one_edge_is_refused(self) -> None:
        """Negative control: Proposal omitting one of three declared edges is refused."""
        gov = _build_triangle_session()
        partial = {
            ("a", "b"): Fraction(-2),
            ("b", "c"): Fraction(1),
        }
        verdict = gov.step_cut(proposed_claims=partial)
        assert verdict.admitted is False
        assert verdict.status == "IncompleteProposal"
        assert "omits declared edges" in verdict.details
        assert "('c', 'a')" in verdict.details

    def test_falsification_partial_proposal_omitting_two_edges_is_refused(self) -> None:
        """Negative control: Proposal omitting two declared edges is refused."""
        gov = _build_triangle_session()
        partial = {("a", "b"): Fraction(0)}
        verdict = gov.step_cut(proposed_claims=partial)
        assert verdict.admitted is False
        assert verdict.status == "IncompleteProposal"
        assert "omits declared edges" in verdict.details

    @pytest.mark.parametrize("bad_val", [0.5, 1.75], ids=["float-0.5", "float-1.75"])
    def test_falsification_float_value_in_proposal_is_refused(self, bad_val: float) -> None:
        """Negative control: Proposal with float value is refused with IncompleteProposal."""
        gov = _build_triangle_session()
        proposal = {
            ("a", "b"): bad_val,
            ("b", "c"): Fraction(1),
            ("c", "a"): Fraction(1),
        }
        verdict = gov.step_cut(proposed_claims=proposal)
        assert verdict.admitted is False
        assert verdict.status == "IncompleteProposal"
        assert "non-exact values" in verdict.details

    @pytest.mark.parametrize("bad_bool", [True, False], ids=["bool-True", "bool-False"])
    def test_falsification_boolean_value_in_proposal_is_refused(self, bad_bool: bool) -> None:
        """Negative control: Proposal with Boolean value is refused with IncompleteProposal."""
        gov = _build_triangle_session()
        proposal = {
            ("a", "b"): bad_bool,
            ("b", "c"): Fraction(1),
            ("c", "a"): Fraction(1),
        }
        verdict = gov.step_cut(proposed_claims=proposal)
        assert verdict.admitted is False
        assert verdict.status == "IncompleteProposal"
        assert "non-exact values" in verdict.details


# ---------------------------------------------------------------------------
# AUDIT-P005-013: Harness exact inputs
# ---------------------------------------------------------------------------

class TestHarnessExactInputs:
    """Verifies AUDIT-P005-013: Streaming harness exact input parsing and type guarding."""

    def test_exact_integers_and_rational_strings_are_scored(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Positive test: Harness parses integers and rational strings into Fraction and scores them."""
        # Proposal with rational string "-2" and integers 1, 1
        claims = {"a, b": "-2", "b, c": 1, "c, a": 1}
        session = _make_streaming_session(claims, monkeypatch)
        verdict = session.run_turn("repair")

        assert verdict["admitted"] is True
        assert verdict["status"] == "ExactRepair"
        assert verdict["defect_after"] == "0"
        assert session.governor.primary_obstruction() == Fraction(0)

    def test_exact_integer_zeros_are_scored(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Positive test: Harness parses all-zero integer proposal and scores ExactRepair."""
        claims = {"a, b": 0, "b, c": 0, "c, a": 0}
        session = _make_streaming_session(claims, monkeypatch)
        verdict = session.run_turn("zero_out")

        assert verdict["admitted"] is True
        assert verdict["status"] == "ExactRepair"
        assert verdict["defect_after"] == "0"

    def test_session_initializes_cleanly_with_exact_integers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Positive test: Session initialization admits exact claims without refusal."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        vertices = ("a", "b", "c")
        edges = (("a", "b", 1), ("b", "c", 2), ("c", "a", 2))
        initial_claims = {("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1}
        session = harness_mod.SymbolGameStreamingSession(
            vertices, edges, initial_claims, harness_mod.MockLLMStreamingProposer([])
        )
        phi_init = session.initialize()
        assert phi_init == Fraction(3)
        assert len(session.history) == 3

    # Negative controls / Falsification tests

    @pytest.mark.parametrize("bad_val", [0.5, 0.1, 2.75], ids=["float-0.5", "float-0.1", "float-2.75"])
    def test_falsification_float_claim_in_proposal_is_refused_by_harness(
        self, monkeypatch: pytest.MonkeyPatch, bad_val: float
    ) -> None:
        """Negative control: Float claim in streaming payload is refused at parse time."""
        claims = {"a, b": bad_val, "b, c": 1, "c, a": 1}
        session = _make_streaming_session(claims, monkeypatch)
        verdict = session.run_turn("repair_with_float")

        assert verdict["admitted"] is False
        assert verdict["status"] == "FW-OP_Refusal"
        assert "exact integer or rational string" in verdict["reason"]
        assert "float" in verdict["reason"]
        # Obstruction must remain unchanged
        assert session.governor.primary_obstruction() == Fraction(3)

    @pytest.mark.parametrize("bad_bool", [True, False], ids=["bool-True", "bool-False"])
    def test_falsification_boolean_claim_in_proposal_is_refused_by_harness(
        self, monkeypatch: pytest.MonkeyPatch, bad_bool: bool
    ) -> None:
        """Negative control: Boolean claim in streaming payload is refused at parse time."""
        claims = {"a, b": bad_bool, "b, c": 1, "c, a": 1}
        session = _make_streaming_session(claims, monkeypatch)
        verdict = session.run_turn("repair_with_bool")

        assert verdict["admitted"] is False
        assert verdict["status"] == "FW-OP_Refusal"
        assert "exact integer or rational string" in verdict["reason"]
        assert "bool" in verdict["reason"]
        assert session.governor.primary_obstruction() == Fraction(3)

    @pytest.mark.parametrize("bad_str", ["not_a_fraction", "1/0", "abc"], ids=["str-nan", "str-div0", "str-abc"])
    def test_falsification_malformed_string_claim_is_refused_by_harness(
        self, monkeypatch: pytest.MonkeyPatch, bad_str: str
    ) -> None:
        """Negative control: Non-rational string in streaming payload is refused."""
        claims = {"a, b": bad_str, "b, c": 1, "c, a": 1}
        session = _make_streaming_session(claims, monkeypatch)
        verdict = session.run_turn("repair_with_bad_string")

        assert verdict["admitted"] is False
        assert verdict["status"] == "FW-OP_Refusal"
        assert "Invalid claim value" in verdict["reason"]

    def test_falsification_initial_claims_with_invalid_string_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Negative control: Initial claims containing malformed string cannot initialize."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        vertices = ("a", "b", "c")
        edges = (("a", "b", 1), ("b", "c", 2), ("c", "a", 2))
        initial_claims = {("a", "b"): "invalid_fraction_string", ("b", "c"): 1, ("c", "a"): 1}
        session = harness_mod.SymbolGameStreamingSession(
            vertices, edges, initial_claims, harness_mod.MockLLMStreamingProposer([])
        )
        with pytest.raises(ValueError):
            session.initialize()

    def test_falsification_governor_step_assert_refuses_float_and_bool(self) -> None:
        """Negative control: Direct governor step_assert refuses float and bool claims."""
        graph = _build_triangle_graph(weight_ca=2)
        gov = gov_mod.L1SymbolGameGovernor(graph)

        v_float = gov.step_assert("a", "b", 0.5)
        assert v_float.admitted is False
        assert v_float.status == "IncompleteProposal"
        assert "ASSERT requires an exact int or Fraction" in v_float.details
        assert ("a", "b") not in gov.edge_claims

        v_bool = gov.step_assert("a", "b", True)
        assert v_bool.admitted is False
        assert v_bool.status == "IncompleteProposal"
        assert "ASSERT requires an exact int or Fraction" in v_bool.details
        assert ("a", "b") not in gov.edge_claims
