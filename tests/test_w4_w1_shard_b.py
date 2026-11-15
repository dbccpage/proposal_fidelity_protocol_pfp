"""Verification suite for Window 4 Wave 1 Shard B (Paper 004 & Paper 005).

AuthorityEffect: None.

Targets four audit derivations:
1. AUDIT-P004-016: Six package Lean modules Lake configuration, deterministic
   86-theorem census bijection, axiom whitelist enforcement, and v4.34.0-rc1 vs
   v4.35.0 replay boundary checks (without toolchain downloads during pytest).
2. AUDIT-P005-014: Offline scoring refusals on undeclared claim edges and
   duplicate carrier entries, plus Edge-object key normalization before scoring.
3. AUDIT-P005-015: ASSERT and section CUT non-exact value refusals, unknown
   vertex refusal, and dual-payload CUT mutual exclusion with state invariance.
4. AUDIT-P005-016: EDGE_MATCH declared-edge enforcement, non-discharge of global
   cycle obstruction by local edge equality, and separation between
   ZERO_OBSTRUCTION and ZERO_DEFECT.
"""

from __future__ import annotations

import hashlib
import importlib
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PFP004_ROOT = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "004_pfp_native_verification_and_evidence_custody"
)
_PFP004_TOOLS = _PFP004_ROOT / "tools"
_PFP005_CODE = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "005_pfp_practitioners_field_manual"
    / "code"
)

_PFP004_MODULE_NAMES = ("replay_lean_axiom_census",)
_PFP005_MODULE_NAMES = (
    "native_functional",
    "l1_symbol_game_governor",
    "symbol_game_toolkit",
)


def _load_isolated_modules(
    search_dir: Path, module_names: tuple[str, ...]
) -> dict[str, Any]:
    """Import archive modules in isolation without mutating global sys.path/sys.modules."""
    saved_modules = {
        name: sys.modules.pop(name) for name in module_names if name in sys.modules
    }
    saved_path = list(sys.path)
    try:
        sys.path[:0] = [str(search_dir)]
        return {name: importlib.import_module(name) for name in module_names}
    finally:
        sys.path[:] = saved_path
        for name in module_names:
            sys.modules.pop(name, None)
        sys.modules.update(saved_modules)


_PFP004_MODULES = _load_isolated_modules(_PFP004_TOOLS, _PFP004_MODULE_NAMES)
_PFP005_MODULES = _load_isolated_modules(_PFP005_CODE, _PFP005_MODULE_NAMES)

census_mod = _PFP004_MODULES["replay_lean_axiom_census"]
nf_mod = _PFP005_MODULES["native_functional"]
gov_mod = _PFP005_MODULES["l1_symbol_game_governor"]
toolkit_mod = _PFP005_MODULES["symbol_game_toolkit"]


@pytest.fixture(autouse=True)
def _pin_isolated_sys_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep lazy runtime imports inside Paper 004/005 helpers bound to isolated modules."""
    for name, mod in _PFP004_MODULES.items():
        monkeypatch.setitem(sys.modules, name, mod)
    for name, mod in _PFP005_MODULES.items():
        monkeypatch.setitem(sys.modules, name, mod)


# ---------------------------------------------------------------------------
# Shared Helpers
# ---------------------------------------------------------------------------


def _lf_sha256(path: Path) -> str:
    """Compute SHA-256 over LF-normalized bytes for cross-platform text stability."""
    normalized = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def _extract_lean_theorems(lean_path: Path) -> list[str]:
    """Extract qualified theorem names from a Lean 4 module via namespace tracking."""
    ns_stack: list[tuple[str, int]] = []
    theorems: list[str] = []
    in_block_comment = 0

    for raw_line in lean_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("/-"):
            in_block_comment += line.count("/-") - line.count("-/")
            continue
        if in_block_comment > 0:
            in_block_comment += line.count("/-") - line.count("-/")
            continue
        if line.startswith("--") or not line:
            continue

        ns_match = re.match(r"^namespace\s+([A-Za-z0-9_.]+)$", line)
        if ns_match is not None:
            parts = ns_match.group(1).split(".")
            ns_stack.append((ns_match.group(1), len(parts)))
            continue

        end_match = re.match(r"^end\s+([A-Za-z0-9_.]+)$", line)
        if end_match is not None and ns_stack and ns_stack[-1][0] == end_match.group(1):
            ns_stack.pop()
            continue

        thm_match = re.match(r"^theorem\s+([A-Za-z0-9_']+)\b", line)
        if thm_match is not None:
            prefix = ".".join(seg for seg, _ in ns_stack)
            short_name = thm_match.group(1)
            theorems.append(f"{prefix}.{short_name}" if prefix else short_name)

    return theorems


def _manual_graph() -> gov_mod.ConstraintGraph:
    """Build Paper 005 canonical directed 3-cycle with weights (1, 2, 3)."""
    return gov_mod.ConstraintGraph(
        vertices=("a", "b", "c"),
        edges=(
            gov_mod.Edge("a", "b", 1),
            gov_mod.Edge("b", "c", 2),
            gov_mod.Edge("c", "a", 3),
        ),
    )


def _initialized_governor() -> gov_mod.L1SymbolGameGovernor:
    """Create governor on (1, 2, 3) 3-cycle with asserted unit claims (1, 1, 1)."""
    governor = gov_mod.L1SymbolGameGovernor(_manual_graph())
    for edge in governor.graph.edges:
        verdict = governor.step_assert(edge.u, edge.v, Fraction(1))
        assert verdict.admitted is True
    return governor


def _snapshot_state(
    governor: gov_mod.L1SymbolGameGovernor,
) -> tuple[dict[tuple[str, str], Fraction], dict[str, Fraction], list[Any]]:
    """Capture active claims, active section, and admitted history list."""
    return (
        dict(governor.edge_claims),
        dict(governor.section),
        list(governor.history),
    )


# ---------------------------------------------------------------------------
# 1. AUDIT-P004-016: Lean package build and 86-theorem census
# ---------------------------------------------------------------------------


class TestPaper004LeanCensus:
    """Verifies AUDIT-P004-016: Paper 004 six-module Lake roots and 86-theorem census."""

    EXPECTED_ROOTS = [
        "TotalUnimodularity",
        "IdentityTypes",
        "Topology50",
        "SparseLanding",
        "SnTower",
        "SparseLandingGeneral",
    ]
    EXPECTED_MODULE_THEOREM_COUNTS = {
        "TotalUnimodularity": 5,
        "IdentityTypes": 3,
        "Topology50": 60,
        "SparseLanding": 10,
        "SnTower": 5,
        "SparseLandingGeneral": 3,
    }

    def test_toolchain_pin_and_lake_import_roots(self) -> None:
        """Positive test: lean-toolchain pins v4.35.0 and lakefile declares all six roots."""
        toolchain_path = _PFP004_ROOT / "lean4" / "lean-toolchain"
        toolchain_text = toolchain_path.read_text(encoding="utf-8").strip()
        assert toolchain_text == "leanprover/lean4:v4.35.0"

        roots = census_mod.import_roots(_PFP004_ROOT)
        assert roots == self.EXPECTED_ROOTS
        for module_name in roots:
            mod_file = _PFP004_ROOT / "lean4" / f"{module_name}.lean"
            assert mod_file.is_file()
            assert len(_lf_sha256(mod_file)) == 64

    def test_parse_report_enumerates_86_theorems_within_axiom_whitelist(self) -> None:
        """Positive test: axiom_report.txt lists 86 theorems (47 axiom-free, 39 whitelisted)."""
        declarations = census_mod.parse_report(_PFP004_ROOT)
        assert len(declarations) == 86

        axiom_free = [d for d in declarations if not d.axioms]
        axiom_used = [d for d in declarations if d.axioms]
        assert len(axiom_free) == 47
        assert len(axiom_used) == 39

        for decl in declarations:
            assert decl.axioms <= census_mod.AXIOM_WHITELIST

        assert sum(d.axioms == frozenset({"propext"}) for d in declarations) == 3
        assert sum(d.axioms == frozenset({"Quot.sound"}) for d in declarations) == 1
        assert (
            sum(d.axioms == frozenset({"propext", "Quot.sound"}) for d in declarations)
            == 32
        )
        assert (
            sum(
                d.axioms
                == frozenset({"propext", "Classical.choice", "Quot.sound"})
                for d in declarations
            )
            == 3
        )

    def test_six_lean_modules_match_86_census_declarations_in_order(self) -> None:
        """Positive test: Every theorem in the six Lean files appears in Census.lean in order."""
        extracted_all: list[str] = []
        for module_name in self.EXPECTED_ROOTS:
            lean_file = _PFP004_ROOT / "lean4" / f"{module_name}.lean"
            mod_theorems = _extract_lean_theorems(lean_file)
            assert len(mod_theorems) == self.EXPECTED_MODULE_THEOREM_COUNTS[module_name]
            extracted_all.extend(mod_theorems)

        assert len(extracted_all) == 86
        reported_names = [d.name for d in census_mod.parse_report(_PFP004_ROOT)]
        assert extracted_all == reported_names

    def test_render_census_check_census_and_write_roundtrip(
        self, tmp_path: Path
    ) -> None:
        """Positive test: Census.lean matches render_census and round-trips via write_census."""
        census_mod.check_census(_PFP004_ROOT)
        rendered = census_mod.render_census(_PFP004_ROOT)
        actual_census = (_PFP004_ROOT / "lean4" / "Census.lean").read_text(
            encoding="utf-8"
        )
        assert rendered == actual_census
        assert rendered.count("#print axioms ") == 86

        # Copy report and lakefile into isolated tmp_path and verify write_census + check_census
        tmp_lean = tmp_path / "lean4"
        tmp_lean.mkdir(parents=True)
        (tmp_lean / "lakefile.lean").write_bytes(
            (_PFP004_ROOT / "lean4" / "lakefile.lean").read_bytes()
        )
        (tmp_lean / "axiom_report.txt").write_bytes(
            (_PFP004_ROOT / "lean4" / "axiom_report.txt").read_bytes()
        )
        census_mod.write_census(tmp_path)
        census_mod.check_census(tmp_path)
        assert (tmp_lean / "Census.lean").read_text(encoding="utf-8") == rendered

    def test_replay_census_accepts_matching_output_and_flags_v435_nsp_delta(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Positive + boundary test: replay_census passes on v4.34.0-rc1 lines and flags v4.35.0 delta."""
        report_lines = [
            line
            for line in (_PFP004_ROOT / "lean4" / "axiom_report.txt")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.startswith("'")
        ]
        assert len(report_lines) == 86

        def fake_run_rc1(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            if cmd == ["lake", "build"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="Built 6 modules\n", stderr="")
            assert cmd == ["lake", "env", "lean", "Census.lean"]
            return subprocess.CompletedProcess(
                cmd, 0, stdout="\n".join(report_lines) + "\n", stderr=""
            )

        monkeypatch.setattr(census_mod.subprocess, "run", fake_run_rc1)
        census_mod.replay_census(_PFP004_ROOT)

        # Simulate the exact v4.35.0 kernel output where SymbolGame.NSP.* adds Classical.choice
        v435_lines = [
            line.replace(
                "[propext, Quot.sound]", "[propext, Classical.choice, Quot.sound]"
            )
            if line.startswith("'SymbolGame.NSP.")
            else line
            for line in report_lines
        ]
        parsed_v435 = census_mod._declarations("\n".join(v435_lines), "v4.35.0-kernel")
        assert len(parsed_v435) == 86
        assert all(d.axioms <= census_mod.AXIOM_WHITELIST for d in parsed_v435)

        def fake_run_v435(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            if cmd == ["lake", "build"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            return subprocess.CompletedProcess(
                cmd, 0, stdout="\n".join(v435_lines) + "\n", stderr=""
            )

        monkeypatch.setattr(census_mod.subprocess, "run", fake_run_v435)
        with pytest.raises(ValueError, match="Lean replay declaration mismatch"):
            census_mod.replay_census(_PFP004_ROOT)

    # Negative controls / Falsification tests

    def test_falsification_mutated_header_count_is_rejected(self, tmp_path: Path) -> None:
        """Negative control: Header count disagreeing with declaration list raises ValueError."""
        tmp_lean = tmp_path / "lean4"
        tmp_lean.mkdir(parents=True)
        orig = (_PFP004_ROOT / "lean4" / "axiom_report.txt").read_text(encoding="utf-8")
        mutated = orig.replace("Declarations listed: 86", "Declarations listed: 85", 1)
        (tmp_lean / "axiom_report.txt").write_text(mutated, encoding="utf-8")

        with pytest.raises(ValueError, match="report counts disagree"):
            census_mod.parse_report(tmp_path)

    def test_falsification_duplicate_declaration_is_rejected(self) -> None:
        """Negative control: Duplicate declaration name in report raises ValueError."""
        dup_text = (
            "'SymbolGame.symm_symm' does not depend on any axioms\n"
            "'SymbolGame.symm_symm' depends on axioms: [propext]\n"
        )
        with pytest.raises(ValueError, match="duplicate declaration"):
            census_mod._declarations(dup_text, "synthetic_duplicate")

    def test_falsification_empty_axiom_brackets_rejected(self) -> None:
        """Negative control: Empty axiom dependency brackets raise ValueError."""
        bad_line = "'SymbolGame.symm_symm' depends on axioms: [   ]\n"
        with pytest.raises(ValueError, match="empty axiom list"):
            census_mod._declarations(bad_line, "synthetic_empty_axioms")

    def test_falsification_disallowed_axiom_detected_against_whitelist(self) -> None:
        """Negative control: sorryAx or custom axiom violates AXIOM_WHITELIST."""
        parsed = census_mod._declarations(
            "'SymbolGame.bad_thm' depends on axioms: [propext, sorryAx]\n",
            "synthetic_sorry",
        )
        assert len(parsed) == 1
        disallowed = parsed[0].axioms - census_mod.AXIOM_WHITELIST
        assert disallowed == frozenset({"sorryAx"})

    def test_falsification_stale_or_missing_census_raises(self, tmp_path: Path) -> None:
        """Negative control: Missing or edited Census.lean fails check_census."""
        tmp_lean = tmp_path / "lean4"
        tmp_lean.mkdir(parents=True)
        (tmp_lean / "lakefile.lean").write_bytes(
            (_PFP004_ROOT / "lean4" / "lakefile.lean").read_bytes()
        )
        (tmp_lean / "axiom_report.txt").write_bytes(
            (_PFP004_ROOT / "lean4" / "axiom_report.txt").read_bytes()
        )

        with pytest.raises(FileNotFoundError, match="Census.lean missing"):
            census_mod.check_census(tmp_path)

        census_mod.write_census(tmp_path)
        stale_text = (
            (tmp_lean / "Census.lean")
            .read_text(encoding="utf-8")
            .replace("#print axioms SymbolGame.NSP.dirDeriv_pos\n", "")
        )
        (tmp_lean / "Census.lean").write_text(stale_text, encoding="utf-8")
        with pytest.raises(ValueError, match="stale generated census"):
            census_mod.check_census(tmp_path)

    def test_falsification_lake_build_failure_propagates_in_replay(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Negative control: Nonzero exit from lake build raises ValueError in replay_census."""

        def fake_failed_build(
            cmd: list[str], **kwargs: Any
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="kernel error")

        monkeypatch.setattr(census_mod.subprocess, "run", fake_failed_build)
        with pytest.raises(ValueError, match="Lake build failed with exit 1"):
            census_mod.replay_census(_PFP004_ROOT)


# ---------------------------------------------------------------------------
# 2. AUDIT-P005-014: Offline scoring refusals and Edge-key normalization
# ---------------------------------------------------------------------------


class TestOfflineScoringRefusals:
    """Verifies AUDIT-P005-014: compute_phi1 carrier/edge refusals and Edge-key normalization."""

    @pytest.fixture(autouse=True)
    def _offline_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

    def test_edge_object_keys_normalize_to_exact_tuple_score(self) -> None:
        """Positive test: Edge-keyed Cochain1 normalizes and matches tuple-keyed score 3."""
        graph = _manual_graph()
        edge_keyed = gov_mod.Cochain1({edge: Fraction(1) for edge in graph.edges})
        tuple_keyed = gov_mod.Cochain1({edge.key: Fraction(1) for edge in graph.edges})

        phi_edge, pot_edge = gov_mod.compute_phi1(graph, edge_keyed)
        phi_tuple, pot_tuple = gov_mod.compute_phi1(graph, tuple_keyed)

        assert phi_edge == Fraction(3)
        assert isinstance(phi_edge, Fraction)
        assert phi_edge == phi_tuple
        assert pot_edge == pot_tuple

        weighted_residual = sum(
            Fraction(edge.weight)
            * abs(Fraction(1) - (pot_edge[edge.v] - pot_edge[edge.u]))
            for edge in graph.edges
        )
        assert weighted_residual == Fraction(3)

    def test_mixed_distinct_edge_and_tuple_keys_normalize_cleanly(self) -> None:
        """Positive test: Mixing Edge objects and tuple keys on distinct edges scores 5/2."""
        graph = _manual_graph()
        e0, e1, e2 = graph.edges
        mixed = gov_mod.Cochain1(
            {
                e0: Fraction(1, 2),
                e1.key: Fraction(1),
                e2: Fraction(1),
            }
        )
        phi, pot = gov_mod.compute_phi1(graph, mixed)
        assert phi == Fraction(5, 2)
        residual = sum(
            Fraction(edge.weight)
            * abs(
                (Fraction(1, 2) if edge == e0 else Fraction(1))
                - (pot[edge.v] - pot[edge.u])
            )
            for edge in graph.edges
        )
        assert residual == Fraction(5, 2)

    def test_toolkit_run_to_terminal_uses_normalized_offline_scoring(self) -> None:
        """Positive test: symbol_game_toolkit.run_to_terminal reaches ACCEPTED_ZERO_DEFECT."""
        outcome = toolkit_mod.run_to_terminal(
            vertices=["a", "b", "c"],
            edges=[("a", "b", 1), ("b", "c", 2), ("c", "a", 3)],
            claims={("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1},
        )
        assert outcome["terminal"] == "ACCEPTED_ZERO_DEFECT"
        assert outcome["final_phi1"] == "0"

    # Negative controls / Falsification tests

    @pytest.mark.parametrize(
        "undeclared_pair",
        [("d", "e"), ("a", "c"), ("b", "a"), ("a", "a")],
        ids=["outside-carrier", "reversed-chord-ac", "reversed-ba", "self-pair"],
    )
    def test_falsification_undeclared_tuple_claim_edge_refused(
        self, undeclared_pair: tuple[str, str]
    ) -> None:
        """Negative control: Undeclared tuple claim key raises ValueError."""
        graph = _manual_graph()
        with pytest.raises(ValueError, match="claim edge absent from declared carrier"):
            gov_mod.compute_phi1(graph, gov_mod.Cochain1({undeclared_pair: Fraction(9)}))

    def test_falsification_undeclared_edge_instance_key_refused(self) -> None:
        """Negative control: Undeclared Edge object key normalizes then fails carrier check."""
        graph = _manual_graph()
        undeclared_edge = gov_mod.Edge("a", "c", 1)
        with pytest.raises(ValueError, match="claim edge absent from declared carrier"):
            gov_mod.compute_phi1(graph, gov_mod.Cochain1({undeclared_edge: Fraction(4)}))

    def test_falsification_duplicate_vertex_in_carrier_refused(self) -> None:
        """Negative control: Duplicate vertex entry in ConstraintGraph raises ValueError."""
        base = _manual_graph()
        dup_vertex_graph = gov_mod.ConstraintGraph(
            vertices=base.vertices + ("a",),
            edges=base.edges,
        )
        claims = gov_mod.Cochain1({edge.key: Fraction(1) for edge in base.edges})
        with pytest.raises(ValueError, match="duplicate vertex in declared carrier"):
            gov_mod.compute_phi1(dup_vertex_graph, claims)

    @pytest.mark.parametrize(
        "extra_weight", [1, 7], ids=["identical-edge", "same-endpoints-different-weight"]
    )
    def test_falsification_duplicate_directed_edge_in_carrier_refused(
        self, extra_weight: int
    ) -> None:
        """Negative control: Duplicate directed edge (u, v) in carrier raises ValueError."""
        base = _manual_graph()
        dup_edge_graph = gov_mod.ConstraintGraph(
            vertices=base.vertices,
            edges=base.edges + (gov_mod.Edge("a", "b", extra_weight),),
        )
        claims = gov_mod.Cochain1({edge.key: Fraction(1) for edge in base.edges})
        with pytest.raises(
            ValueError, match="duplicate directed edge in declared carrier"
        ):
            gov_mod.compute_phi1(dup_edge_graph, claims)

    def test_falsification_colliding_edge_and_tuple_key_refused(self) -> None:
        """Negative control: Supplying both Edge(a, b) and ('a', 'b') raises ValueError."""
        graph = _manual_graph()
        colliding = gov_mod.Cochain1(
            {
                graph.edges[0]: Fraction(1),
                ("a", "b"): Fraction(1),
            }
        )
        with pytest.raises(ValueError, match="duplicate claim for a directed edge"):
            gov_mod.compute_phi1(graph, colliding)

    @pytest.mark.parametrize(
        "malformed_key",
        ["a->b", ("a",), ("a", "b", "c")],
        ids=["string-key", "singleton-tuple", "triple-tuple"],
    )
    def test_falsification_malformed_claim_key_shape_refused(
        self, malformed_key: Any
    ) -> None:
        """Negative control: Non-pair claim keys raise ValueError."""
        graph = _manual_graph()
        with pytest.raises(
            ValueError, match="claim keys must be declared directed edges"
        ):
            gov_mod.compute_phi1(
                graph, gov_mod.Cochain1({malformed_key: Fraction(1)})  # type: ignore[dict-item]
            )


# ---------------------------------------------------------------------------
# 3. AUDIT-P005-015: ASSERT and section CUT input guards
# ---------------------------------------------------------------------------


class TestAssertAndSectionCutGuards:
    """Verifies AUDIT-P005-015: Exactness, carrier, and dual-payload guards in governor."""

    @pytest.fixture(autouse=True)
    def _offline_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

    def test_exact_int_and_fraction_assert_and_section_cut_admitted(self) -> None:
        """Positive test: Exact int and Fraction inputs succeed on ASSERT and section CUT."""
        governor = gov_mod.L1SymbolGameGovernor(_manual_graph())
        assert governor.step_assert("a", "b", 1).admitted is True
        assert governor.step_assert("b", "c", Fraction(3, 2)).admitted is True
        assert governor.step_assert("c", "a", Fraction(1, 2)).admitted is True
        assert len(governor.history) == 3

        verdict = governor.step_cut(
            proposed_section={"a": 0, "b": Fraction(-2), "c": Fraction(-1, 2)}
        )
        assert verdict.admitted is True
        assert verdict.status == "MonotonicDescent"
        assert verdict.defect_before == Fraction(11, 2)
        assert verdict.defect_after == Fraction(3)
        assert len(governor.history) == 4

    # Negative controls / Falsification tests

    @pytest.mark.parametrize(
        "bad_value",
        [True, False, 0.1, 1.0, "1", None],
        ids=["bool-True", "bool-False", "float-0.1", "float-1.0", "str-1", "None"],
    )
    def test_falsification_non_exact_assert_refused_preserving_state(
        self, bad_value: Any
    ) -> None:
        """Negative control: Non-exact ASSERT returns IncompleteProposal; only _step_counter advances."""
        governor = _initialized_governor()
        before_state = _snapshot_state(governor)
        counter_before = governor._step_counter

        verdict = governor.step_assert("a", "b", bad_value)

        assert verdict.admitted is False
        assert verdict.status == "IncompleteProposal"
        assert verdict.defect_before == Fraction(6)
        assert verdict.defect_after == Fraction(6)
        assert _snapshot_state(governor) == before_state
        assert governor._step_counter == counter_before + 1

    @pytest.mark.parametrize(
        "bad_section",
        [
            {"a": True},
            {"a": False},
            {"a": 0.1},
            {"a": Fraction(0), "b": -2.0, "c": Fraction(-1)},
            {"c": "0"},
        ],
        ids=["bool-True", "bool-False", "float-0.1", "float-neg2", "str-0"],
    )
    def test_falsification_section_cut_non_exact_value_refused(
        self, bad_section: dict[str, Any]
    ) -> None:
        """Negative control: Non-exact section CUT returns IncompleteProposal with state preserved."""
        governor = _initialized_governor()
        before_state = _snapshot_state(governor)
        counter_before = governor._step_counter

        verdict = governor.step_cut(proposed_section=bad_section)

        assert verdict.admitted is False
        assert verdict.status == "IncompleteProposal"
        assert verdict.defect_before == verdict.defect_after == Fraction(6)
        assert _snapshot_state(governor) == before_state
        assert governor._step_counter == counter_before + 1

    @pytest.mark.parametrize(
        "unknown_section",
        [
            {"d": Fraction(9)},
            {"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1), "z": Fraction(0)},
            {"unknown": True},
        ],
        ids=["single-unknown", "valid-plus-unknown", "unknown-with-bool"],
    )
    def test_falsification_section_cut_unknown_vertex_refused(
        self, unknown_section: dict[str, Any]
    ) -> None:
        """Negative control: Unknown vertex in section CUT returns CarrierViolation."""
        governor = _initialized_governor()
        before_state = _snapshot_state(governor)
        counter_before = governor._step_counter

        verdict = governor.step_cut(proposed_section=unknown_section)

        assert verdict.admitted is False
        assert verdict.status == "CarrierViolation"
        assert _snapshot_state(governor) == before_state
        assert governor._step_counter == counter_before + 1

    @pytest.mark.parametrize(
        "sec_payload,claims_payload",
        [
            ({}, {}),
            (
                {"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1)},
                {
                    ("a", "b"): Fraction(-2),
                    ("b", "c"): Fraction(1),
                    ("c", "a"): Fraction(1),
                },
            ),
        ],
        ids=["both-empty-dicts", "both-valid-repairs"],
    )
    def test_falsification_dual_payload_cut_refused_without_choosing_either(
        self,
        sec_payload: dict[str, Fraction],
        claims_payload: dict[tuple[str, str], Fraction],
    ) -> None:
        """Negative control: Supplying both CUT payloads returns MoveViolation with state unchanged."""
        governor = _initialized_governor()
        before_state = _snapshot_state(governor)
        counter_before = governor._step_counter

        verdict = governor.step_cut(
            proposed_section=sec_payload,
            proposed_claims=claims_payload,
        )

        assert verdict.admitted is False
        assert verdict.status == "MoveViolation"
        assert "exactly one" in verdict.details
        assert _snapshot_state(governor) == before_state
        assert governor._step_counter == counter_before + 1

    def test_falsification_empty_cut_with_neither_payload_refused(self) -> None:
        """Negative control: Calling step_cut() with neither payload returns Refused."""
        governor = _initialized_governor()
        before_state = _snapshot_state(governor)
        verdict = governor.step_cut()
        assert verdict.admitted is False
        assert verdict.status == "Refused"
        assert _snapshot_state(governor) == before_state


# ---------------------------------------------------------------------------
# 4. AUDIT-P005-016: EDGE_MATCH scope and global obstruction vs current defect
# ---------------------------------------------------------------------------


class TestEdgeMatchAndObstructionScope:
    """Verifies AUDIT-P005-016: step_verify EDGE_MATCH guard and local vs global checks."""

    @pytest.fixture(autouse=True)
    def _offline_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

    def test_matching_declared_edges_locally_does_not_discharge_global_obstruction(
        self,
    ) -> None:
        """Positive test: Matching two of three cycle edges leaves ZERO_OBSTRUCTION false."""
        governor = _initialized_governor()
        cut_verdict = governor.step_cut(
            proposed_section={"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1)}
        )
        assert cut_verdict.admitted is True
        assert cut_verdict.status == "MonotonicDescent"
        assert governor.section_defect() == Fraction(3)
        assert governor.primary_obstruction() == Fraction(3)

        v_bc = governor.step_verify("EDGE_MATCH:b,c")
        v_ca = governor.step_verify("EDGE_MATCH:c,a")
        v_ab = governor.step_verify("EDGE_MATCH:a,b")
        v_obs = governor.step_verify("ZERO_OBSTRUCTION")
        v_def = governor.step_verify("ZERO_DEFECT")

        assert v_bc.admitted is True and v_bc.status == "Verified"
        assert v_ca.admitted is True and v_ca.status == "Verified"
        assert v_ab.admitted is False and v_ab.status == "VerificationFailed"
        assert v_obs.admitted is False and v_obs.status == "VerificationFailed"
        assert v_def.admitted is False and v_def.status == "VerificationFailed"

    def test_zero_obstruction_and_zero_current_defect_are_distinct_obligations(
        self,
    ) -> None:
        """Positive test: Coboundary (-2, 1, 1) at zero section satisfies ZERO_OBSTRUCTION, not ZERO_DEFECT."""
        governor = gov_mod.L1SymbolGameGovernor(_manual_graph())
        for edge, val in zip(governor.graph.edges, (-2, 1, 1), strict=True):
            assert governor.step_assert(edge.u, edge.v, Fraction(val)).admitted is True

        assert governor.primary_obstruction() == Fraction(0)
        assert governor.section_defect() == Fraction(7)

        v_obs = governor.step_verify("ZERO_OBSTRUCTION")
        v_def = governor.step_verify("ZERO_DEFECT")
        assert v_obs.admitted is True and v_obs.status == "Verified"
        assert v_def.admitted is False and v_def.status == "VerificationFailed"

        # Aligning the section to (0, -2, -1) then satisfies ZERO_DEFECT as well
        align = governor.step_cut(
            proposed_section={"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1)}
        )
        assert align.admitted is True
        assert align.status == "ExactRepair"
        assert governor.step_verify("ZERO_DEFECT").admitted is True

    # Negative controls / Falsification tests

    @pytest.mark.parametrize(
        "bad_obligation",
        [
            "EDGE_MATCH:d,e",
            "EDGE_MATCH:a,c",
            "EDGE_MATCH:b,a",
            "EDGE_MATCH:a,a",
            "EDGE_MATCH:a",
            "EDGE_MATCH:a,b,c",
            "EDGE_MATCH:,",
            "EDGE_MATCH:",
        ],
        ids=[
            "outside-vertices",
            "undeclared-chord-ac",
            "reversed-edge-ba",
            "self-edge-aa",
            "single-token",
            "three-tokens",
            "empty-pair",
            "empty-suffix",
        ],
    )
    def test_falsification_undeclared_or_malformed_edge_match_refused_even_at_zero_state(
        self, bad_obligation: str
    ) -> None:
        """Negative control: Undeclared/malformed EDGE_MATCH fails even when section and claims are 0."""
        # Fresh unasserted governor has default 0 claims and 0 section everywhere;
        # without declared-edge lookup, 0 == 0 - 0 would spuriously pass!
        zero_governor = gov_mod.L1SymbolGameGovernor(_manual_graph())
        zero_before = _snapshot_state(zero_governor)
        verdict_zero = zero_governor.step_verify(bad_obligation)
        assert verdict_zero.admitted is False
        assert verdict_zero.status == "VerificationFailed"
        assert _snapshot_state(zero_governor) == zero_before

        # Also check on initialized (1, 1, 1) governor
        active_governor = _initialized_governor()
        active_before = _snapshot_state(active_governor)
        verdict_active = active_governor.step_verify(bad_obligation)
        assert verdict_active.admitted is False
        assert verdict_active.status == "VerificationFailed"
        assert _snapshot_state(active_governor) == active_before

    def test_falsification_unknown_verify_obligation_refused(self) -> None:
        """Negative control: Unknown obligation string returns VerificationFailed."""
        governor = _initialized_governor()
        before = _snapshot_state(governor)
        verdict = governor.step_verify("UNKNOWN_OBLIGATION")
        assert verdict.admitted is False
        assert verdict.status == "VerificationFailed"
        assert _snapshot_state(governor) == before
