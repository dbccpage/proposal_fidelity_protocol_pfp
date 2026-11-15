"""Verification suite for Window 4 Wave 1 Shard C (Papers 005 and 006).

AuthorityEffect: None.

Targets four audit derivations:
1. AUDIT-P005-017: Projection error after candidate scoring restores pre-CUT
   claims and propagates instead of partially committing a replacement.
2. AUDIT-P005-018: Stationary quotient score with changed claims (2, 1, 0) and
   Level 7 capstone trajectory (refusals, 3 -> 2 -> 0 descent, restore to 3).
3. AUDIT-P006-014: Paper-local toy classes in test_006_epistemic_immune.py
   import zero production modules and diverge from production contracts.
4. AUDIT-P006-018: Non-consumption of catalog negative_fixture/positive_fixture
   for proposal matching or repair derivation, and literal substring screening
   on target_pattern in cemetery_regression.
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from adversary.stage.domain import CandidateProposalV1
from adversary.use_cases import cemetery_regression
from operations.domain.rop.result import Err, Ok

from eis.domain.allostery import AllostericConsensusGate
from eis.domain.pharmacy_search import RULE_CONTENT_KEYS, PharmacyMatch, rule_content_sha256
from eis.domain.value_objects import AllosteryRefusal
from pfp.domain.immune.clonal_selection import (
    ClonalCandidate,
    ClonalSelectionEngine,
    KillConditionReceipt,
    KillConditionRefusal,
)

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
_PFP006_DIR = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "006_pfp_epistemic_immune_system_and_cemetery_dag_mining"
)
_PFP006_TESTS = _PFP006_DIR / "code" / "tests"

_PFP005_NAMES = (
    "native_functional",
    "l1_symbol_game_governor",
    "study_capstone",
    "test_manual_contracts",
)
_PFP006_NAMES = (
    "test_006_epistemic_immune",
    "test_006_catalog_file",
)
_ALL_ISOLATED_NAMES = _PFP005_NAMES + _PFP006_NAMES

_PRODUCTION_ROOT_PACKAGES = frozenset({"pfp", "eis", "adversary", "operations", "operads"})
_FIXTURE_FIELD_NAMES = frozenset({"negative_fixture", "positive_fixture"})


def _load_isolated_archive_modules() -> dict[str, Any]:
    """Import Paper 005 and Paper 006 archive modules without permanent sys mutation."""
    saved_modules = {
        name: sys.modules.pop(name) for name in _ALL_ISOLATED_NAMES if name in sys.modules
    }
    saved_path = list(sys.path)
    try:
        sys.path[:0] = [str(_PFP006_TESTS), str(_PFP005_TESTS), str(_PFP005_CODE)]
        return {name: importlib.import_module(name) for name in _ALL_ISOLATED_NAMES}
    finally:
        sys.path[:] = saved_path
        for name in _ALL_ISOLATED_NAMES:
            sys.modules.pop(name, None)
        sys.modules.update(saved_modules)


def _load_isolated_cemetery_sink() -> Any:
    """Import pfp.infrastructure.persistence.cemetery_sink without permanent sys mutation."""
    saved_modules = dict(sys.modules)
    saved_path = list(sys.path)
    try:
        sys.path.insert(0, str(_REPO_ROOT / "ops"))
        for mod_name in list(sys.modules):
            if mod_name == "governance" or mod_name.startswith("governance."):
                sys.modules.pop(mod_name, None)
        return importlib.import_module("pfp.infrastructure.persistence.cemetery_sink")
    finally:
        sys.path[:] = saved_path
        for mod_name in list(sys.modules):
            if mod_name not in saved_modules:
                sys.modules.pop(mod_name, None)
        sys.modules.update(saved_modules)


_ARCHIVE_MODULES = _load_isolated_archive_modules()
cemetery_sink_mod = _load_isolated_cemetery_sink()
nf_mod = _ARCHIVE_MODULES["native_functional"]
gov_mod = _ARCHIVE_MODULES["l1_symbol_game_governor"]
capstone_mod = _ARCHIVE_MODULES["study_capstone"]
tmc_mod = _ARCHIVE_MODULES["test_manual_contracts"]
toy006_mod = _ARCHIVE_MODULES["test_006_epistemic_immune"]
cat006_mod = _ARCHIVE_MODULES["test_006_catalog_file"]


@pytest.fixture(autouse=True)
def _pin_archive_sys_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep lazy imports inside Paper 005/006 helpers bound to isolated modules."""
    for name, mod in _ARCHIVE_MODULES.items():
        monkeypatch.setitem(sys.modules, name, mod)


# ---------------------------------------------------------------------------
# Shared Helpers
# ---------------------------------------------------------------------------


def _normalize_lf(raw_bytes: bytes) -> bytes:
    """Normalize CRLF line endings to LF before hashing text fixtures."""
    return raw_bytes.replace(b"\r\n", b"\n")


def _build_weighted_triangle() -> Any:
    """Build Paper 005 directed 3-cycle (a->b, b->c, c->a) with weights (1, 2, 3)."""
    return gov_mod.ConstraintGraph(
        vertices=("a", "b", "c"),
        edges=(
            gov_mod.Edge("a", "b", 1),
            gov_mod.Edge("b", "c", 2),
            gov_mod.Edge("c", "a", 3),
        ),
    )


def _build_asserted_governor() -> Any:
    """Initialize Paper 005 governor with asserted claims (1, 1, 1) on weights (1, 2, 3)."""
    governor = gov_mod.L1SymbolGameGovernor(_build_weighted_triangle())
    for edge in governor.graph.edges:
        verdict = governor.step_assert(*edge.key, Fraction(1))
        assert verdict.admitted is True
    return governor


def _snapshot_governor_state(governor: Any) -> tuple[dict[Any, Any], dict[str, Any], list[Any]]:
    """Capture active edge_claims, section, and admitted history snapshot."""
    return dict(governor.edge_claims), dict(governor.section), list(governor.history)


def _extract_imported_root_packages(source_text: str) -> set[str]:
    """Return top-level root package names imported by a Python module."""
    tree = ast.parse(source_text)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _extract_referenced_fixture_fields(func_node: ast.FunctionDef) -> set[str]:
    """Find string literals or attribute accesses naming negative_fixture or positive_fixture."""
    found: set[str] = set()
    for node in ast.walk(func_node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in _FIXTURE_FIELD_NAMES:
                found.add(node.value)
        elif isinstance(node, ast.Attribute) and node.attr in _FIXTURE_FIELD_NAMES:
            found.add(node.attr)
    return found


def _make_candidate_proposal() -> CandidateProposalV1:
    """Build a valid CandidateProposalV1 value object for regression screening tests."""
    return CandidateProposalV1(
        producer_agent_id="seat_proposer",
        work_packet_id="sha256:" + ("1" * 64),
        artifact_refs=("sha256:" + ("2" * 64),),
        prediction_receipt_id="sha256:" + ("3" * 64),
        nonclaims=("Does not claim external domain validity.",),
    )


# ---------------------------------------------------------------------------
# AUDIT-P005-017: Projection error rollback
# ---------------------------------------------------------------------------


class TestProjectionErrorRollback:
    """Verifies AUDIT-P005-017: projection failure after scoring restores pre-CUT claims."""

    def test_projection_failure_on_third_call_restores_pre_cut_claims_and_propagates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Positive test: third compute_graph_phi1 failure rolls back edge_claims and propagates."""
        governor = _build_asserted_governor()
        before = _snapshot_governor_state(governor)
        counter_before = governor._step_counter
        calls: list[dict[tuple[str, str], Fraction]] = []

        def mocked_calculator(
            vertices: Any, edges: Any, claims: dict[tuple[str, str], Fraction]
        ) -> tuple[Fraction, dict[str, Fraction]]:
            del vertices, edges
            calls.append(dict(claims))
            if len(calls) == 3:
                raise nf_mod.NativeFunctionalUnavailable("projection refused")
            score = Fraction(3) if len(calls) == 1 else Fraction(0)
            return score, {"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1)}

        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", "configured-for-boundary-test")
        monkeypatch.setattr(nf_mod, "compute_graph_phi1", mocked_calculator)

        replacement = {
            ("a", "b"): Fraction(-2),
            ("b", "c"): Fraction(1),
            ("c", "a"): Fraction(1),
        }
        with pytest.raises(nf_mod.NativeFunctionalUnavailable, match="projection refused"):
            governor.step_cut(proposed_claims=replacement)

        assert len(calls) == 3
        assert calls[0] == {("a", "b"): Fraction(1), ("b", "c"): Fraction(1), ("c", "a"): Fraction(1)}
        assert calls[1] == replacement
        assert calls[2] == replacement
        assert _snapshot_governor_state(governor) == before
        # Attempt counter advances on entry while active state is preserved (paper.md:183)
        assert governor._step_counter == counter_before + 1

    def test_upstream_manual_contract_projection_error_test_passes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Positive test: Paper 005 test_native_projection_error_preserves_pre_cut_state passes."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)
        tmc_mod.test_native_projection_error_preserves_pre_cut_state(None, monkeypatch)

    def test_ast_step_cut_wraps_project_in_try_finally_without_except_handler(self) -> None:
        """Positive test: step_cut AST wraps self.project in try...finally restoring edge_claims."""
        source = (_PFP005_CODE / "l1_symbol_game_governor.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        gov_cls = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "L1SymbolGameGovernor"
        )
        step_cut_fn = next(
            node for node in gov_cls.body
            if isinstance(node, ast.FunctionDef) and node.name == "step_cut"
        )
        try_nodes = [node for node in ast.walk(step_cut_fn) if isinstance(node, ast.Try)]
        assert len(try_nodes) == 1
        try_node = try_nodes[0]
        assert len(try_node.handlers) == 0
        assert len(try_node.finalbody) == 1
        finally_dump = ast.dump(try_node.finalbody[0])
        assert "edge_claims" in finally_dump
        assert "old_claims" in finally_dump

    # Negative controls / Falsification tests

    def test_falsification_successful_third_call_commits_claims_section_and_history(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Negative control: when Call 3 succeeds, replacement claims and section commit."""
        governor = _build_asserted_governor()
        history_len_before = len(governor.history)
        calls: list[dict[tuple[str, str], Fraction]] = []

        def succeeding_calculator(
            vertices: Any, edges: Any, claims: dict[tuple[str, str], Fraction]
        ) -> tuple[Fraction, dict[str, Fraction]]:
            del vertices, edges
            calls.append(dict(claims))
            score = Fraction(3) if len(calls) == 1 else Fraction(0)
            return score, {"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1)}

        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", "configured-for-boundary-test")
        monkeypatch.setattr(nf_mod, "compute_graph_phi1", succeeding_calculator)

        replacement = {
            ("a", "b"): Fraction(-2),
            ("b", "c"): Fraction(1),
            ("c", "a"): Fraction(1),
        }
        verdict = governor.step_cut(proposed_claims=replacement)
        assert len(calls) == 3
        assert verdict.admitted is True
        assert verdict.status == "ExactRepair"
        assert governor.edge_claims == replacement
        assert governor.section == {"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1)}
        assert len(governor.history) == history_len_before + 1

    def test_falsification_second_call_scoring_failure_aborts_before_projection(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Negative control: failure on Call 2 (candidate scoring) never enters project."""
        governor = _build_asserted_governor()
        before = _snapshot_governor_state(governor)
        calls: list[dict[tuple[str, str], Fraction]] = []

        def fail_on_second_call(
            vertices: Any, edges: Any, claims: dict[tuple[str, str], Fraction]
        ) -> tuple[Fraction, dict[str, Fraction]]:
            del vertices, edges
            calls.append(dict(claims))
            if len(calls) == 2:
                raise nf_mod.NativeFunctionalUnavailable("candidate scoring refused")
            return Fraction(3), {"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1)}

        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", "configured-for-boundary-test")
        monkeypatch.setattr(nf_mod, "compute_graph_phi1", fail_on_second_call)

        replacement = {
            ("a", "b"): Fraction(-2),
            ("b", "c"): Fraction(1),
            ("c", "a"): Fraction(1),
        }
        with pytest.raises(nf_mod.NativeFunctionalUnavailable, match="candidate scoring refused"):
            governor.step_cut(proposed_claims=replacement)

        assert len(calls) == 2
        assert _snapshot_governor_state(governor) == before


# ---------------------------------------------------------------------------
# AUDIT-P005-018: Stationary score with changed claims & capstone replay
# ---------------------------------------------------------------------------


class TestCapstoneAndStationaryClaims:
    """Verifies AUDIT-P005-018: stationary score claim change and capstone 3->2->0->3 replay."""

    def test_stationary_quotient_score_admits_changed_claims_vector(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Positive test: (1,1,1) -> (2,1,0) keeps Phi_w == 3 while mutating edge_claims."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

        governor = _build_asserted_governor()
        initial_claims = dict(governor.edge_claims)
        stationary_replacement = {
            ("a", "b"): Fraction(2),
            ("b", "c"): Fraction(1),
            ("c", "a"): Fraction(0),
        }
        assert stationary_replacement != initial_claims

        # Check exact coboundary lower bound and attainment for both claim vectors
        phi_init, pot_init = gov_mod.compute_phi1(
            governor.graph, gov_mod.Cochain1(values=initial_claims)
        )
        phi_next, pot_next = gov_mod.compute_phi1(
            governor.graph, gov_mod.Cochain1(values=stationary_replacement)
        )
        assert phi_init == Fraction(3)
        assert phi_next == Fraction(3)
        assert sum(
            Fraction(e.weight) * abs(stationary_replacement[e.key] - (pot_next[e.v] - pot_next[e.u]))
            for e in governor.graph.edges
        ) == Fraction(3)
        assert pot_init != pot_next or initial_claims != stationary_replacement

        verdict = governor.step_cut(proposed_claims=stationary_replacement)
        assert verdict.admitted is True
        assert verdict.status == "IdempotentStationary"
        assert verdict.defect_before == Fraction(3)
        assert verdict.defect_after == Fraction(3)
        assert governor.edge_claims == stationary_replacement

    def test_capstone_trajectory_refusals_descent_and_snapshot_restore(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Positive test: run_capstone refuses invalid CUTs, descends 3->2->0, and restores 3."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

        result = capstone_mod.run_capstone(verbose=False)
        assert result["calculation_path"] == "python-enumeration"
        assert result["weights"] == (1, 2, 3)
        assert result["snapshot_id"] == "step_003"
        assert result["original_minimum"] == Fraction(3)
        assert result["restored_minimum"] == Fraction(3)
        assert isinstance(result["original_minimum"], Fraction)
        assert isinstance(result["restored_minimum"], Fraction)
        assert result["refused_state_preserved"] is True
        assert result["restored_claims"] == {
            ("a", "b"): Fraction(1),
            ("b", "c"): Fraction(1),
            ("c", "a"): Fraction(1),
        }

        outcomes = result["outcomes"]
        assert len(outcomes) == 6
        assert [row["status"] for row in outcomes] == [
            "IncompleteProposal",
            "DefectIncrease",
            "MonotonicDescent",
            "ExactRepair",
            "Verified",
            "Retracted",
        ]
        assert [row["admitted"] for row in outcomes] == [False, False, True, True, True, True]
        assert [row["metric"] for row in outcomes] == [
            "Phi_w",
            "Phi_w",
            "Phi_w",
            "Phi_w",
            "D_c",
            "D_c",
        ]
        assert [(row["before"], row["after"]) for row in outcomes] == [
            (Fraction(3), Fraction(3)),
            (Fraction(3), Fraction(5)),
            (Fraction(3), Fraction(2)),
            (Fraction(2), Fraction(0)),
            (Fraction(0), Fraction(0)),
            (Fraction(0), Fraction(6)),
        ]

    # Negative controls / Falsification tests

    def test_falsification_strict_cycle_sum_increase_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Negative control: perturbing (2, 1, 0) to (2, 2, 0) raises Phi_w to 4 and is refused."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        governor = _build_asserted_governor()
        before_claims = dict(governor.edge_claims)

        increasing_claims = {
            ("a", "b"): Fraction(2),
            ("b", "c"): Fraction(2),
            ("c", "a"): Fraction(0),
        }
        verdict = governor.step_cut(proposed_claims=increasing_claims)
        assert verdict.admitted is False
        assert verdict.status == "DefectIncrease"
        assert verdict.defect_before == Fraction(3)
        assert verdict.defect_after == Fraction(4)
        assert governor.edge_claims == before_claims

    def test_falsification_unknown_snapshot_id_is_refused_and_retract_reopens_obstruction(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Negative control: unknown snapshot is refused, and retracting step_003 fails ZERO_OBSTRUCTION."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        governor = _build_asserted_governor()

        repair = {("a", "b"): Fraction(-2), ("b", "c"): Fraction(1), ("c", "a"): Fraction(1)}
        assert governor.step_cut(proposed_claims=repair).status == "ExactRepair"
        assert governor.step_verify("ZERO_OBSTRUCTION").admitted is True

        unknown = governor.step_retract("step_999", reason="nonexistent")
        assert unknown.admitted is False
        assert unknown.status == "Refused"
        assert governor.primary_obstruction() == Fraction(0)

        retracted = governor.step_retract("step_003", reason="restore inconsistent baseline")
        assert retracted.admitted is True
        assert retracted.status == "Retracted"
        assert governor.primary_obstruction() == Fraction(3)

        post_retract_verify = governor.step_verify("ZERO_OBSTRUCTION")
        assert post_retract_verify.admitted is False
        assert post_retract_verify.status == "VerificationFailed"


# ---------------------------------------------------------------------------
# AUDIT-P006-014: Paper-local toy classes do not verify production integration
# ---------------------------------------------------------------------------


class TestPaperLocalToyClasses:
    """Verifies AUDIT-P006-014: test_006_epistemic_immune.py isolates from and diverges from production."""

    def test_ast_toy_module_imports_stdlib_only_and_defines_local_classes(self) -> None:
        """Positive test: test_006_epistemic_immune.py imports zero production modules."""
        toy_path = _PFP006_TESTS / "test_006_epistemic_immune.py"
        source = toy_path.read_text(encoding="utf-8")
        imported_roots = _extract_imported_root_packages(source)

        assert imported_roots == {
            "__future__",
            "hashlib",
            "json",
            "dataclasses",
            "fractions",
            "typing",
        }
        assert imported_roots & _PRODUCTION_ROOT_PACKAGES == set()

        tree = ast.parse(source)
        local_classes = {
            node.name for node in tree.body if isinstance(node, ast.ClassDef)
        }
        local_functions = {
            node.name for node in tree.body if isinstance(node, ast.FunctionDef)
        }
        assert local_classes == {"DangerSignal", "ThymicCheckResult", "CemeteryDAGSink"}
        assert "evaluate_thymic_selection" in local_functions

        # Execute the three toy tests directly to confirm self-contained toy behavior
        toy006_mod.test_danger_signal_threshold()
        toy006_mod.test_thymic_selection_exact_type_equality()
        toy006_mod.test_toy_chain_links_predecessor_digests()

    def test_toy_danger_signal_diverges_from_production_allosteric_quorum(self) -> None:
        """Positive test: single-sensor Fraction(1, 2) triggers toy DangerSignal, not production gate."""
        toy_signal = toy006_mod.DangerSignal(Fraction(1, 2), Fraction(0, 1), 0)
        assert toy_signal.is_quarantine_triggered() is True

        gate = AllostericConsensusGate()
        assert gate.quorum_size == 2
        decision = gate.evaluate_quorum(
            {"defect_mass": Fraction(1, 2), "cycle_obstruction": Fraction(0, 1)}
        )
        assert decision.is_activated is False
        assert decision.positive_sensors == 1
        assert decision.aggregate_signal == Fraction(1, 2)
        # H(1/2) = (1/2)^2 / (2^2 + (1/2)^2) = (1/4) / (17/4) = 1/17 < 1/2
        assert decision.hill_value == Fraction(1, 17)

    def test_toy_sink_and_thymus_diverge_from_production_contracts(
        self, tmp_path: Path
    ) -> None:
        """Positive test: toy CemeteryDAGSink and thymic check differ from CemeterySink and ClonalSelectionEngine."""
        toy_sink = toy006_mod.CemeteryDAGSink()
        danger = toy006_mod.DangerSignal(Fraction(1, 1), Fraction(0, 1), 0)
        toy_sink.append_candidate(0, "0" * 64, "TOK", danger, "REFUSED", "M")
        assert toy_sink.entries[0]["prev_hash"] == "GENESIS_ROOT"
        assert not hasattr(toy_sink, "emit_tail_receipt")
        assert not hasattr(toy_sink, "verify_integrity")
        assert list(tmp_path.iterdir()) == []

        ledger_file = tmp_path / "production_cemetery.jsonl"
        prod_sink = cemetery_sink_mod.CemeterySink(ledger_file)
        entry = prod_sink.record_refusal({"turn": 1}, "TEST_REFUSAL")
        receipt = prod_sink.emit_tail_receipt()
        assert ledger_file.is_file()
        assert entry.prev_digest == cemetery_sink_mod.GENESIS_DIGEST
        assert receipt.entry_count == 1
        assert prod_sink.verify_integrity() is True

        parent = ClonalCandidate("rule_parent", "epitope", r"defect_token")
        invalid_clone = ClonalCandidate("rule_bad", "epitope", "[", parent_id="rule_parent", generation=2)
        killed_bad, refusal_bad = ClonalSelectionEngine.check_kill_condition(
            invalid_clone, parent, ("benign sample",)
        )
        assert killed_bad is False
        assert isinstance(refusal_bad, KillConditionRefusal)

        self_reactive_clone = ClonalCandidate(
            "rule_self", "epitope", r"benign\s+sample", parent_id="rule_parent", generation=2
        )
        killed_self, receipt_self = ClonalSelectionEngine.check_kill_condition(
            self_reactive_clone, parent, ("benign sample",)
        )
        assert killed_self is True
        assert isinstance(receipt_self, KillConditionReceipt)

    # Negative controls / Falsification tests

    def test_falsification_ast_detector_flags_production_owner_imports(self) -> None:
        """Negative control: AST import inspector detects production pfp and eis imports."""
        synthetic_integration_test = """
from eis.domain.allostery import AllostericConsensusGate
import pfp.infrastructure.persistence.cemetery_sink as sink_mod
"""
        roots = _extract_imported_root_packages(synthetic_integration_test)
        assert roots & _PRODUCTION_ROOT_PACKAGES == {"eis", "pfp"}

    def test_falsification_production_allosteric_gate_activates_at_two_sensor_quorum_and_caps_single(
        self,
    ) -> None:
        """Negative control: production gate activates with two cap-1 sensors and refuses uncapped single sensor."""
        gate = AllostericConsensusGate()
        activated = gate.evaluate_quorum(
            {"defect_mass": Fraction(1, 1), "cycle_obstruction": Fraction(1, 1)}
        )
        assert activated.is_activated is True
        assert activated.positive_sensors == 2
        assert activated.hill_value == Fraction(1, 2)

        with pytest.raises(AllosteryRefusal, match="exceeds the per-sensor cap"):
            gate.evaluate_quorum({"defect_mass": Fraction(2, 1)})


# ---------------------------------------------------------------------------
# AUDIT-P006-018: Non-consumption of catalog fixtures & substring consumer
# ---------------------------------------------------------------------------


class TestCatalogNonConsumptionAndSubstringConsumer:
    """Verifies AUDIT-P006-018: catalog fixtures unused for matching/repairs; substring screening."""

    def test_baseline_validation_bindings_and_lf_normalized_catalog_digest(self) -> None:
        """Positive test: baseline validation JSON binds catalog and repair_service.py hashes."""
        catalog_path = _PFP006_DIR / "code" / "fixtures" / "pharmacy_catalog_52cb5457f6c4.json"
        lf_bytes = _normalize_lf(catalog_path.read_bytes())
        expected_catalog_sha = "b95ce7c1338867cc680abffcc3f2fb9da634c7a7ec2f4c00e0d67391e91b4acb"
        assert hashlib.sha256(lf_bytes).hexdigest() == expected_catalog_sha
        assert expected_catalog_sha == cat006_mod.CATALOG_SHA256

        validation_path = _PFP006_DIR / "docs" / "first_publication_validation_2026_10_02.json"
        validation = json.loads(_normalize_lf(validation_path.read_bytes()).decode("utf-8"))
        assert validation["implementation_audit_commit"] == "52cb5457f6c485ba548cfd292f6012a941ed22cf"

        bindings = validation["audit_source_bindings"]
        assert bindings["_intelligence/_antibodies/pharmacy_catalog.json"] == {
            "git_blob_sha": "e4984047231091caca6e5b0b7810f20c705e4970",
            "sha256": expected_catalog_sha,
        }
        assert bindings["external_application/prompt_doctor/use_cases/repair_service.py"] == {
            "git_blob_sha": "6e0e3e50a6e329156fa5f32a7e61f47e60e90199",
            "sha256": "3cb51a89116ff59463f14fc64907b0d0f31005f169c7ebb2249b9db6410c13b6",
        }
        assert not (_REPO_ROOT / "external_application" / "prompt_doctor").exists()

    def test_ast_screening_consumers_never_read_negative_or_positive_fixture(self) -> None:
        """Positive test: proposal-screening functions never reference negative_fixture or positive_fixture."""
        reg_source = (_REPO_ROOT / "ops" / "adversary" / "use_cases" / "cemetery_regression.py").read_text(
            encoding="utf-8"
        )
        reg_tree = ast.parse(reg_source)
        screening_fns = {
            node.name: node
            for node in reg_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name in {"_pattern_of", "_validate_catalog", "_screen_antibodies", "screen_known_regressions"}
        }
        assert set(screening_fns) == {
            "_pattern_of",
            "_validate_catalog",
            "_screen_antibodies",
            "screen_known_regressions",
        }
        for fn_node in screening_fns.values():
            assert _extract_referenced_fixture_fields(fn_node) == set()

        oeeis_source = (
            _REPO_ROOT / "ops" / "adversary" / "infrastructure" / "estates" / "oeeis_immune.py"
        ).read_text(encoding="utf-8")
        oeeis_tree = ast.parse(oeeis_source)
        adapter_cls = next(
            node for node in oeeis_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "OeeisImmuneAdapter"
        )
        validate_fn = next(
            node for node in adapter_cls.body
            if isinstance(node, ast.FunctionDef) and node.name == "validate_candidate_against_yaml_specs"
        )
        assert _extract_referenced_fixture_fields(validate_fn) == set()

        # Pharmacy search hashes fixtures in RULE_CONTENT_KEYS, while omitting them from PharmacyMatch
        assert "negative_fixture" in RULE_CONTENT_KEYS
        assert "positive_fixture" in RULE_CONTENT_KEYS
        assert "negative_fixture" not in PharmacyMatch.__annotations__
        assert "positive_fixture" not in PharmacyMatch.__annotations__

    def test_cemetery_regression_screens_target_pattern_as_literal_substring_ignoring_fixtures(
        self,
    ) -> None:
        """Positive test: _screen_antibodies checks literal target_pattern substring and ignores fixtures."""
        catalog_path = _PFP006_DIR / "code" / "fixtures" / "pharmacy_catalog_52cb5457f6c4.json"
        catalog = json.loads(_normalize_lf(catalog_path.read_bytes()).decode("utf-8"))
        sample_row = dict(catalog["antibodies"]["ab_q40_weight_type_error"])

        candidate = _make_candidate_proposal()

        # 1. Proposal matching negative_fixture or positive_fixture verbatim (without target_pattern) is NOT refused
        neg_only_res = cemetery_regression._screen_antibodies(
            candidate, sample_row["negative_fixture"], (sample_row,)
        )
        pos_only_res = cemetery_regression._screen_antibodies(
            candidate, sample_row["positive_fixture"], (sample_row,)
        )
        assert isinstance(neg_only_res, Ok)
        assert isinstance(pos_only_res, Ok)

        # 2. Proposal containing target_pattern as substring IS refused, and mutating fixtures changes nothing
        prompt_with_target = f"Observed runtime failure: {sample_row['target_pattern']} in candidate"
        hit_original = cemetery_regression._screen_antibodies(
            candidate, prompt_with_target, (sample_row,)
        )
        mutated_row = {
            **sample_row,
            "negative_fixture": "COMPLETELY_DIFFERENT_NEGATIVE_FIXTURE",
            "positive_fixture": "SYNTHETIC_REPAIR_TEMPLATE_UNUSED",
        }
        hit_mutated = cemetery_regression._screen_antibodies(
            candidate, prompt_with_target, (mutated_row,)
        )
        assert isinstance(hit_original, Err)
        assert isinstance(hit_mutated, Err)
        assert hit_original.error.code == "REGRESSION_AGAINST_ANTIBODY_REFUSED"
        assert hit_original.error == hit_mutated.error
        assert "SYNTHETIC_REPAIR_TEMPLATE_UNUSED" not in hit_mutated.error.message

        # 3. Regex metacharacters in target_pattern are tested as literal substrings, not regexes
        meta_antibody = {
            "antibody_id": "ab_literal_substring_check",
            "target_pattern": "claim[0].*repair",
            "failure_class": "meta_failure_label",
            "negative_fixture": "claim0_xyz_repair",
            "positive_fixture": "repaired_claim_state",
        }
        regex_like_text = "candidate has claim0_xyz_repair inside body"
        literal_text = "candidate has claim[0].*repair inside body"
        assert isinstance(
            cemetery_regression._screen_antibodies(candidate, regex_like_text, (meta_antibody,)),
            Ok,
        )
        literal_hit = cemetery_regression._screen_antibodies(
            candidate, literal_text, (meta_antibody,)
        )
        assert isinstance(literal_hit, Err)
        assert literal_hit.error.code == "REGRESSION_AGAINST_ANTIBODY_REFUSED"

    # Negative controls / Falsification tests

    def test_falsification_ast_fixture_reader_detector_catches_synthetic_repair_consumer(
        self,
    ) -> None:
        """Negative control: AST detector flags functions reading positive_fixture or negative_fixture."""
        synthetic_consumer = """
def derive_repair_from_catalog(proposal_text: str, row: dict) -> str:
    if row.get("negative_fixture") in proposal_text:
        return row["positive_fixture"]
    return proposal_text
"""
        tree = ast.parse(synthetic_consumer)
        fn_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
        assert _extract_referenced_fixture_fields(fn_node) == {
            "negative_fixture",
            "positive_fixture",
        }

    def test_falsification_rule_content_sha256_changes_when_fixture_changes(self) -> None:
        """Negative control: rule_content_sha256 binds fixture strings even though screening ignores them."""
        base_record = {
            "failure_class": "defect:0",
            "target_pattern": "defect:0",
            "constraint_type": "ProjectOut",
            "operatorizability": "repairable",
            "action": "repair",
            "severity": "P1",
            "negative_fixture": "# Triggering defect: defect:0\n",
            "positive_fixture": "# Repaired exact state\n",
            "scope": {"domain": "pfp"},
            "guidance_text": "Inspect boundary defect.",
        }
        altered_record = {**base_record, "positive_fixture": "x = Fraction(1, 2)\n"}
        assert rule_content_sha256(base_record) != rule_content_sha256(altered_record)
