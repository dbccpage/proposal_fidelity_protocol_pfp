"""Verification suite for Window 5 Wave 1 Shard C (Paper 009 Part 1).

AuthorityEffect: None.

Targets four audit derivations in Paper 009:
1. AUDIT-P009-003 (ATL-P009-003): SemioticAudit compares two supplied strings
   (signified != interpretant) without reading signifier, parsing code, or
   deciding semantic equivalence.
2. AUDIT-P009-004 (ATL-P009-004): StagnationRecord checks a supplied round
   count, gauge flag, and rational defect score via a three-way conjunction.
3. AUDIT-P009-005 (ATL-P009-005): evaluate_terminal_reality_gate branches on
   supplied scores and flags across 36 sign/boolean cells without computing
   scores or checking flag provenance.
4. AUDIT-P009-006 (ATL-P009-006): Under Level15AuthorityCalculus.lean
   definitions, proposal constructors (.proposal, .candidateTrace) are distinct
   from .terminalAuthority (axiom-free constructor disjointness), while runtime
   correspondence remains a separate implementation obligation.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib.util
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
from enum import Enum
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PFP009_ROOT = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "009_pfp_adversarial_dialectics_and_terminal_reality_gates"
)
_REALITY_GATE_PATH = _PFP009_ROOT / "code" / "tests" / "test_009_adversarial_reality_gate.py"
_CENSUS_TOOL_PATH = _PFP009_ROOT / "tools" / "replay_lean_axiom_census.py"
_LEAN_DIR = _PFP009_ROOT / "lean4"
_FALSIFIERS_JSON = _PFP009_ROOT / "docs" / "historical_evidence" / "adversary_gate_falsifiers.json"

_GATE_MOD_NAME = "_w5_w1_shard_c_reality_gate"
_CENSUS_MOD_NAME = "_w5_w1_shard_c_lean_census"

_CACHED_MODULES: dict[str, Any] = {}


def _load_archive_module(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    file_path: Path,
) -> Any:
    """Load an archived Python file via spec_from_file_location inside pytest scope."""
    if module_name in _CACHED_MODULES:
        mod = _CACHED_MODULES[module_name]
        monkeypatch.setitem(sys.modules, module_name, mod)
        return mod

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to create module spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    _CACHED_MODULES[module_name] = module
    return module


@pytest.fixture(autouse=True)
def _inject_isolated_archive_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bind Paper 009 archive modules into sys.modules per test without bytecode writes."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    _load_archive_module(monkeypatch, _GATE_MOD_NAME, _REALITY_GATE_PATH)
    _load_archive_module(monkeypatch, _CENSUS_MOD_NAME, _CENSUS_TOOL_PATH)


def _gate_mod() -> Any:
    return sys.modules[_GATE_MOD_NAME]


def _census_mod() -> Any:
    return sys.modules[_CENSUS_MOD_NAME]


def _lean_env() -> dict[str, str]:
    """Build subprocess environment with $HOME/.elan/bin prepended to PATH."""
    env = dict(os.environ)
    elan_bin = str(Path.home() / ".elan" / "bin")
    current_path = env.get("PATH", "")
    env["PATH"] = f"{elan_bin}:{current_path}" if current_path else elan_bin
    return env


@pytest.fixture(scope="module")
def _isolated_paper009_lean_build(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Compile an unmodified out-of-tree copy of Paper 009 Lean 4 sources."""
    build_root = tmp_path_factory.mktemp("pfp009_shard_c_lean")
    shutil.copytree(_PFP009_ROOT / "lean4", build_root / "lean4")
    shutil.copytree(_PFP009_ROOT / "tools", build_root / "tools")
    res = subprocess.run(
        ["lake", "build"],
        cwd=build_root / "lean4",
        env=_lean_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(f"Out-of-tree lake build failed:\n{res.stdout}\n{res.stderr}")
    return build_root


def _strip_lean_comments(source: str) -> str:
    """Strip nested /- ... -/ block comments and -- line comments from Lean 4 text."""
    pieces: list[str] = []
    pos = 0
    block_depth = 0
    in_line = False
    for match in re.finditer(r"/-|-/|--|\n", source):
        start, end = match.span()
        tok = match.group(0)
        if block_depth == 0 and not in_line:
            pieces.append(source[pos:start])
        if tok == "\n":
            in_line = False
            pieces.append("\n")
        elif not in_line:
            if tok == "/-":
                block_depth += 1
            elif tok == "-/" and block_depth > 0:
                block_depth -= 1
                if block_depth == 0:
                    pieces.append(" ")
            elif tok == "--" and block_depth == 0:
                in_line = True
        pos = end
    if block_depth == 0 and not in_line:
        pieces.append(source[pos:])
    return "".join(pieces)


def _extract_lean_theorems(lean_path: Path) -> list[str]:
    """Deterministically extract namespace-qualified theorem names from a Lean 4 source file."""
    ns_stack: list[str] = []
    theorems: list[str] = []
    stripped = _strip_lean_comments(lean_path.read_text(encoding="utf-8"))

    for raw_line in stripped.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        ns_match = re.match(r"^namespace\s+([A-Za-z0-9_.]+)$", line)
        if ns_match is not None:
            ns_stack.append(ns_match.group(1))
            continue

        end_match = re.match(r"^end\s+([A-Za-z0-9_.]+)$", line)
        if end_match is not None and ns_stack and ns_stack[-1] == end_match.group(1):
            ns_stack.pop()
            continue

        thm_match = re.match(r"^theorem\s+([A-Za-z0-9_']+)\b", line)
        if thm_match is not None:
            prefix = ".".join(ns_stack)
            name = thm_match.group(1)
            theorems.append(f"{prefix}.{name}" if prefix else name)

    return theorems


# ---------------------------------------------------------------------------
# 1. AUDIT-P009-003: Semiotic fixture scope check
# ---------------------------------------------------------------------------


class TestSemioticFixtureScope:
    """Verifies AUDIT-P009-003 (ATL-P009-003): SemioticAudit compares two supplied strings only."""

    def test_ast_imports_and_method_body_compare_two_strings_only(self) -> None:
        """Positive check: AST confirms stdlib-only imports and single signified != interpretant check."""
        tree = ast.parse(_REALITY_GATE_PATH.read_text(encoding="utf-8"))

        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.add(node.module)
        assert imported_modules == {"dataclasses", "fractions"}

        cls_nodes = [
            n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SemioticAudit"
        ]
        assert len(cls_nodes) == 1
        cls_node = cls_nodes[0]

        ann_fields = [
            (stmt.target.id, ast.unparse(stmt.annotation))
            for stmt in cls_node.body
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
        ]
        assert ann_fields == [
            ("signifier", "str"),
            ("signified", "str"),
            ("interpretant", "str"),
        ]

        methods = [stmt for stmt in cls_node.body if isinstance(stmt, ast.FunctionDef)]
        assert [m.name for m in methods] == ["is_drift_detected"]
        method = methods[0]

        non_doc_stmts = [
            stmt
            for stmt in method.body
            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
        ]
        assert len(non_doc_stmts) == 1
        ret_stmt = non_doc_stmts[0]
        assert isinstance(ret_stmt, ast.Return)
        assert isinstance(ret_stmt.value, ast.Compare)
        assert len(ret_stmt.value.ops) == 1
        assert isinstance(ret_stmt.value.ops[0], ast.NotEq)
        assert ast.unparse(ret_stmt.value) == "self.signified != self.interpretant"

        calls_in_method = [n for n in ast.walk(method) if isinstance(n, ast.Call)]
        assert calls_in_method == []
        attrs_read = {n.attr for n in ast.walk(method) if isinstance(n, ast.Attribute)}
        assert attrs_read == {"signified", "interpretant"}
        assert "signifier" not in attrs_read

    def test_named_fixture_and_equal_vs_drifted_string_pairs(self) -> None:
        """Positive check: named test passes and equal vs drifted string pairs behave as specified."""
        gate = _gate_mod()
        gate.test_semiotic_sign_drift_detection()

        equal_pair = gate.SemioticAudit(
            signifier="ExactCheck",
            signified="ZeroCycleSumOnDeclaredTriangle",
            interpretant="ZeroCycleSumOnDeclaredTriangle",
        )
        assert equal_pair.is_drift_detected() is False

        drifted_pair = gate.SemioticAudit(
            signifier="ExactCheck",
            signified="ZeroCycleSumOnDeclaredTriangle",
            interpretant="ZeroReplacedCochainOnLiftedCarrier",
        )
        assert drifted_pair.is_drift_detected() is True

    @pytest.mark.parametrize(
        ("signified", "interpretant"),
        [
            ("x + y", "y + x"),
            ("1/2", "2/4"),
            ("ExactRationalSimplex", "ExactRationalSimplex "),
            ("ExactRationalSimplex", "exactrationalsimplex"),
        ],
    )
    def test_falsification_semantic_equivalences_reported_as_drift(
        self, signified: str, interpretant: str
    ) -> None:
        """Negative control: algebraically or semantically equivalent distinct strings trigger drift."""
        gate = _gate_mod()
        audit = gate.SemioticAudit(
            signifier="EquivalenceProbe",
            signified=signified,
            interpretant=interpretant,
        )
        assert audit.is_drift_detected() is True

    def test_falsification_contradictory_signifier_and_unparsed_code_ignored(self) -> None:
        """Negative control: contradictory signifier and unexecuted '1 / 0' text do not trigger drift."""
        gate = _gate_mod()
        contradictory_signifier = gate.SemioticAudit(
            signifier="FloatApproximateHeuristic",
            signified="ExactRationalSimplex",
            interpretant="ExactRationalSimplex",
        )
        assert contradictory_signifier.is_drift_detected() is False

        unparsed_division_by_zero = gate.SemioticAudit(
            signifier="CodeText",
            signified="1 / 0",
            interpretant="1 / 0",
        )
        assert unparsed_division_by_zero.is_drift_detected() is False


# ---------------------------------------------------------------------------
# 2. AUDIT-P009-004: Stagnation fixture scope check
# ---------------------------------------------------------------------------


class TestStagnationFixtureScope:
    """Verifies AUDIT-P009-004 (ATL-P009-004): StagnationRecord checks count, gauge flag, and score."""

    def test_ast_conjunction_and_named_stagnation_test(self) -> None:
        """Positive check: AST confirms three-conjunct return and named test passes."""
        gate = _gate_mod()
        gate.test_stagnation_review_trigger()

        tree = ast.parse(_REALITY_GATE_PATH.read_text(encoding="utf-8"))
        cls_node = next(
            n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "StagnationRecord"
        )
        ann_fields = [
            (stmt.target.id, ast.unparse(stmt.annotation))
            for stmt in cls_node.body
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
        ]
        assert ann_fields == [
            ("consecutive_stagnant_rounds", "int"),
            ("current_defect_norm", "Fraction"),
            ("locked_gauge", "bool"),
        ]

        methods = [stmt for stmt in cls_node.body if isinstance(stmt, ast.FunctionDef)]
        assert [m.name for m in methods] == ["should_trigger_review"]
        method = methods[0]
        assert [ast.unparse(d) for d in method.args.defaults] == ["3"]

        non_doc_stmts = [
            stmt
            for stmt in method.body
            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
        ]
        assert len(non_doc_stmts) == 1
        ret_stmt = non_doc_stmts[0]
        assert isinstance(ret_stmt, ast.Return)
        assert isinstance(ret_stmt.value, ast.BoolOp)
        assert isinstance(ret_stmt.value.op, ast.And)
        conjuncts = [ast.unparse(val) for val in ret_stmt.value.values]
        assert conjuncts == [
            "self.consecutive_stagnant_rounds >= threshold_rounds",
            "self.locked_gauge",
            "self.current_defect_norm > Fraction(0, 1)",
        ]

    def test_independent_single_field_variations_and_exact_boundaries(self) -> None:
        """Positive + boundary checks: varying each of the three fields independently flips verdict."""
        gate = _gate_mod()
        cls = gate.StagnationRecord

        # Baseline passing state
        baseline = cls(
            consecutive_stagnant_rounds=3,
            current_defect_norm=Fraction(1, 7),
            locked_gauge=True,
        )
        assert baseline.should_trigger_review() is True

        # 1. Vary consecutive_stagnant_rounds alone (holding norm=1/7, locked_gauge=True)
        for below in (-1, 0, 1, 2):
            rec = cls(below, Fraction(1, 7), True)
            assert rec.should_trigger_review() is False
        for at_or_above in (3, 4, 25):
            rec = cls(at_or_above, Fraction(1, 7), True)
            assert rec.should_trigger_review() is True

        # Custom threshold_rounds boundary
        rec_four = cls(4, Fraction(1, 7), True)
        assert rec_four.should_trigger_review(threshold_rounds=5) is False
        assert rec_four.should_trigger_review(threshold_rounds=4) is True

        # 2. Vary locked_gauge alone (holding rounds >= 3, norm > 0)
        assert cls(3, Fraction(1, 7), False).should_trigger_review() is False
        assert cls(50, Fraction(100, 1), False).should_trigger_review() is False

        # 3. Vary current_defect_norm alone (holding rounds >= 3, locked_gauge=True)
        for non_positive in (Fraction(-3, 2), Fraction(-1, 1000), Fraction(0, 1)):
            assert cls(50, non_positive, True).should_trigger_review() is False
        for positive in (Fraction(1, 10**6), Fraction(1, 7), Fraction(9, 2)):
            assert cls(3, positive, True).should_trigger_review() is True

    def test_exhaustive_boolean_regime_cube(self) -> None:
        """Enumerates all 2 x 2 x 2 = 8 boundary cells; exactly (3, 1/3, True) returns True."""
        gate = _gate_mod()
        cls = gate.StagnationRecord
        true_cells: list[tuple[int, Fraction, bool]] = []
        for rounds, norm, locked in itertools.product(
            (2, 3),
            (Fraction(0, 1), Fraction(1, 3)),
            (False, True),
        ):
            if cls(rounds, norm, locked).should_trigger_review():
                true_cells.append((rounds, norm, locked))
        assert true_cells == [(3, Fraction(1, 3), True)]

    def test_falsification_trigger_performs_no_search_or_state_mutation(self) -> None:
        """Negative control: StagnationRecord is immutable and returns a bool with no state transition."""
        gate = _gate_mod()
        rec = gate.StagnationRecord(
            consecutive_stagnant_rounds=5,
            current_defect_norm=Fraction(3, 1),
            locked_gauge=True,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            rec.locked_gauge = False  # type: ignore[misc]

        out = rec.should_trigger_review()
        assert type(out) is bool
        assert out is True
        assert rec.consecutive_stagnant_rounds == 5
        assert rec.current_defect_norm == Fraction(3, 1)
        assert rec.locked_gauge is True


# ---------------------------------------------------------------------------
# 3. AUDIT-P009-005: Toy verdict function scope check
# ---------------------------------------------------------------------------


class TestToyVerdictFunctionScope:
    """Verifies AUDIT-P009-005 (ATL-P009-005): evaluate_terminal_reality_gate branch table and scope."""

    def test_ast_confirms_zero_score_computation_and_branch_only_routing(self) -> None:
        """Positive check: AST confirms zero arithmetic ops and calls restricted to Fraction/Verdict."""
        gate = _gate_mod()
        gate.test_terminal_reality_gate_verdicts()

        tree = ast.parse(_REALITY_GATE_PATH.read_text(encoding="utf-8"))
        fn_node = next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "evaluate_terminal_reality_gate"
        )

        bin_ops = [n for n in ast.walk(fn_node) if isinstance(n, (ast.BinOp, ast.AugAssign))]
        assert bin_ops == []

        call_names = {
            ast.unparse(n.func) for n in ast.walk(fn_node) if isinstance(n, ast.Call)
        }
        assert call_names == {"Fraction", "TerminalGateVerdict"}

        # Exact-type equality check on TerminalGateVerdict.__eq__
        verdict = gate.evaluate_terminal_reality_gate(
            Fraction(0, 1), Fraction(0, 1), semiotic_clean=True
        )
        assert verdict == gate.TerminalGateVerdict(
            verdict="PASS_TO_MASTER",
            phi1=Fraction(0, 1),
            gamma2=Fraction(0, 1),
            semiotic_clean=True,
        )
        assert (verdict == ("PASS_TO_MASTER", Fraction(0, 1), Fraction(0, 1), True)) is False

    def test_exhaustive_36_cell_branch_table_enumeration(self) -> None:
        """Enumerates all 3 x 3 x 2 x 2 = 36 sign/boolean cells and checks exact verdict counts."""
        gate = _gate_mod()
        phi1_reps = (Fraction(-1, 2), Fraction(0, 1), Fraction(3, 5))
        gamma2_reps = (Fraction(-1, 3), Fraction(0, 1), Fraction(2, 3))
        bool_vals = (False, True)

        counts = {"REFUSE": 0, "PASS_TO_MASTER": 0, "OPEN_RESIDUAL": 0}
        total_cells = 0

        for phi1, gamma2, clean, debt in itertools.product(
            phi1_reps, gamma2_reps, bool_vals, bool_vals
        ):
            total_cells += 1
            res = gate.evaluate_terminal_reality_gate(
                phi1=phi1,
                gamma2=gamma2,
                semiotic_clean=clean,
                unbudgeted_debt=debt,
            )
            assert res.phi1 == phi1
            assert res.gamma2 == gamma2
            assert res.semiotic_clean is clean

            if not clean:
                expected = "REFUSE"
            elif phi1 == Fraction(0, 1) and gamma2 == Fraction(0, 1):
                expected = "PASS_TO_MASTER"
            elif phi1 > Fraction(0, 1) and gamma2 == Fraction(0, 1) and not debt:
                expected = "OPEN_RESIDUAL"
            else:
                expected = "REFUSE"

            assert res.verdict == expected
            counts[res.verdict] += 1

        assert total_cells == 36
        assert counts == {
            "REFUSE": 33,
            "PASS_TO_MASTER": 2,
            "OPEN_RESIDUAL": 1,
        }

    def test_falsification_unverified_flag_provenance_and_debt_precedence(self) -> None:
        """Negative controls: spoofed clean flag passes without audit, and (0, 0, True) ignores debt."""
        gate = _gate_mod()

        # 1. Drifted SemioticAudit exists, yet caller passes semiotic_clean=True and spoofed 0 scores
        drifted = gate.SemioticAudit(
            signifier="Solver",
            signified="ExactSimplex",
            interpretant="ZeroedLiftedCochain",
        )
        assert drifted.is_drift_detected() is True
        spoofed = gate.evaluate_terminal_reality_gate(
            phi1=Fraction(0, 1),
            gamma2=Fraction(0, 1),
            semiotic_clean=True,
        )
        assert spoofed.verdict == "PASS_TO_MASTER"

        # 2. Branch 2 precedes unbudgeted_debt check when phi1 == 0 and gamma2 == 0
        zero_with_debt = gate.evaluate_terminal_reality_gate(
            phi1=Fraction(0, 1),
            gamma2=Fraction(0, 1),
            semiotic_clean=True,
            unbudgeted_debt=True,
        )
        assert zero_with_debt.verdict == "PASS_TO_MASTER"

        # By contrast, positive phi1 with gamma2 == 0 flips from OPEN_RESIDUAL to REFUSE under debt
        pos_without_debt = gate.evaluate_terminal_reality_gate(
            phi1=Fraction(1, 2),
            gamma2=Fraction(0, 1),
            semiotic_clean=True,
            unbudgeted_debt=False,
        )
        pos_with_debt = gate.evaluate_terminal_reality_gate(
            phi1=Fraction(1, 2),
            gamma2=Fraction(0, 1),
            semiotic_clean=True,
            unbudgeted_debt=True,
        )
        assert pos_without_debt.verdict == "OPEN_RESIDUAL"
        assert pos_with_debt.verdict == "REFUSE"


# ---------------------------------------------------------------------------
# 4. AUDIT-P009-006: Proposal constructors are not terminal
# ---------------------------------------------------------------------------


class _ModelStateKind(Enum):
    """Exact 5-constructor finite mirror of MSSN.Level15.StateKind."""

    PROPOSAL = "proposal"
    CANDIDATE_TRACE = "candidateTrace"
    QUOTIENT_WITNESS = "quotientWitness"
    TERMINAL_AUTHORITY = "terminalAuthority"
    IMMUTABLE_REFUSAL = "immutableRefusal"


def _model_is_proposal(k: _ModelStateKind) -> bool:
    return k in (_ModelStateKind.PROPOSAL, _ModelStateKind.CANDIDATE_TRACE)


def _model_is_terminal_authority(k: _ModelStateKind) -> bool:
    return k is _ModelStateKind.TERMINAL_AUTHORITY


class TestProposalNonAuthorityLeanScope:
    """Verifies AUDIT-P009-006 (ATL-P009-006): Level15 StateKind disjointness and census bindings."""

    EXPECTED_ROOTS = [
        "SLevel",
        "RuntimeLimits",
        "TriggerNotLicense",
        "Level15AuthorityCalculus",
    ]
    EXPECTED_MODULE_THEOREM_COUNTS = {
        "SLevel": 6,
        "RuntimeLimits": 13,
        "TriggerNotLicense": 4,
        "Level15AuthorityCalculus": 9,
    }

    def test_level15_source_inductive_and_theorem1_structure(self) -> None:
        """Positive check: Level15AuthorityCalculus defines 5 StateKind constructors and theorem1."""
        level15_path = _LEAN_DIR / "Level15AuthorityCalculus.lean"
        source = level15_path.read_text(encoding="utf-8")

        assert "namespace MSSN.Level15" in source
        inductive_match = re.search(
            r"inductive\s+StateKind\s+where\s*((?:\s*\|\s*[A-Za-z0-9_]+\s*:\s*StateKind)+)",
            source,
        )
        assert inductive_match is not None
        ctors = re.findall(r"\|\s*([A-Za-z0-9_]+)\s*:\s*StateKind", inductive_match.group(1))
        assert ctors == [
            "proposal",
            "candidateTrace",
            "quotientWitness",
            "terminalAuthority",
            "immutableRefusal",
        ]

        assert re.search(
            r"def\s+isProposal\s*\(k\s*:\s*StateKind\)\s*:\s*Prop\s*:=\s*"
            r"k\s*=\s*\.proposal\s*∨\s*k\s*=\s*\.candidateTrace",
            source,
        )
        assert re.search(
            r"def\s+isTerminalAuthority\s*\(k\s*:\s*StateKind\)\s*:\s*Prop\s*:=\s*"
            r"k\s*=\s*\.terminalAuthority",
            source,
        )
        assert re.search(
            r"theorem\s+theorem1_proposal_non_authority\s*\(k\s*:\s*StateKind\)\s*:\s*"
            r"isProposal\s+k\s*→\s*¬\s*isTerminalAuthority\s+k\s*:=\s*by",
            source,
        )

        # Verify comment stripper removes nested /- ... -/ block and -- line comments only
        sample_stripped = _strip_lean_comments(
            "/- outer /- inner sorry -/\naxiom hidden : False -/\n-- admit -- /-\ndef clean := 1\n"
        )
        assert (
            re.search(r"\bsorry\b|\badmit\b|^\s*axiom\s+", sample_stripped, flags=re.MULTILINE)
            is None
        )
        assert "def clean := 1" in sample_stripped

        # Confirm zero sorry/admit/custom axiom across all four root Lean modules
        for root_name in self.EXPECTED_ROOTS:
            mod_text = (_LEAN_DIR / f"{root_name}.lean").read_text(encoding="utf-8")
            stripped_code = _strip_lean_comments(mod_text)
            assert re.search(r"\bsorry\b", stripped_code) is None
            assert re.search(r"\badmit\b", stripped_code) is None
            assert re.search(r"^\s*axiom\s+", stripped_code, flags=re.MULTILINE) is None

    def test_lake_configuration_and_32_theorem_axiom_census(self, tmp_path: Path) -> None:
        """Positive check: Lake roots, 32-theorem Census.lean, and 516-declaration full census."""
        census = _census_mod()

        toolchain = (_LEAN_DIR / "lean-toolchain").read_text(encoding="utf-8").strip()
        assert toolchain == "leanprover/lean4:v4.35.0"

        roots = census.import_roots(_PFP009_ROOT)
        assert roots == self.EXPECTED_ROOTS

        # Copy lean4 unmodified (retaining CRLF files) into tmp_path and verify census directly
        shutil.copytree(_LEAN_DIR, tmp_path / "lean4")
        assert census.check_census(tmp_path) is None
        declarations = census.parse_report(tmp_path)
        assert len(declarations) == 32

        extracted: list[str] = []
        for root_name in self.EXPECTED_ROOTS:
            mod_thms = _extract_lean_theorems(_LEAN_DIR / f"{root_name}.lean")
            assert len(mod_thms) == self.EXPECTED_MODULE_THEOREM_COUNTS[root_name]
            extracted.extend(mod_thms)
        assert [d.name for d in declarations] == extracted

        axiom_free = [d for d in declarations if not d.axioms]
        axiom_used = [d for d in declarations if d.axioms]
        assert len(axiom_free) == 28
        assert len(axiom_used) == 4
        for decl in declarations:
            assert decl.axioms <= frozenset({"propext", "Quot.sound"})

        thm1 = next(
            d for d in declarations if d.name == "MSSN.Level15.theorem1_proposal_non_authority"
        )
        assert thm1.axioms == frozenset()

        # Verify full_axiom_report.txt 516-declaration census for StateKind and theorem1
        full_lines = (_LEAN_DIR / "full_axiom_report.txt").read_text(encoding="utf-8").splitlines()
        full_decls = census._declarations("\n".join(full_lines), "full_axiom_report.txt")
        assert len(full_decls) == 516
        full_map = {d.name: d.axioms for d in full_decls}
        for key in (
            "MSSN.Level15.StateKind",
            "MSSN.Level15.StateKind.proposal",
            "MSSN.Level15.StateKind.candidateTrace",
            "MSSN.Level15.StateKind.quotientWitness",
            "MSSN.Level15.StateKind.terminalAuthority",
            "MSSN.Level15.StateKind.immutableRefusal",
            "MSSN.Level15.StateKind.noConfusion",
            "MSSN.Level15.isProposal",
            "MSSN.Level15.isTerminalAuthority",
            "MSSN.Level15.theorem1_proposal_non_authority",
        ):
            assert key in full_map
            assert full_map[key] == frozenset()

    def test_out_of_tree_lean_kernel_build_and_negative_controls(
        self,
        _isolated_paper009_lean_build: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Positive + negative controls: live out-of-tree Lean 4 build, kernel probes, and census failures."""
        census = _census_mod()
        lean_cwd = _isolated_paper009_lean_build / "lean4"
        env = _lean_env()

        # 1. Positive: out-of-tree lake build + check_census + replay_census succeed with 0 axioms
        assert census.check_census(_isolated_paper009_lean_build) is None
        census_res = subprocess.run(
            ["lake", "env", "lean", "Census.lean"],
            cwd=lean_cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert census_res.returncode == 0, census_res.stderr
        assert (
            "'MSSN.Level15.theorem1_proposal_non_authority' does not depend on any axioms"
            in census_res.stdout
        )
        monkeypatch.setenv("PATH", env["PATH"])
        assert census.replay_census(_isolated_paper009_lean_build) is None
        assert not (_LEAN_DIR / ".lake").exists()

        # 2. Negative kernel probes: Lean rejects overlapping witness and false converse
        overlap_probe = tmp_path / "BadOverlapProbe.lean"
        overlap_probe.write_text(
            "import Level15AuthorityCalculus\n"
            "theorem bad_overlap : ∃ k : MSSN.Level15.StateKind,\n"
            "    MSSN.Level15.isProposal k ∧ MSSN.Level15.isTerminalAuthority k :=\n"
            "  ⟨.proposal, Or.inl rfl, rfl⟩\n",
            encoding="utf-8",
        )
        overlap_res = subprocess.run(
            ["lake", "env", "lean", str(overlap_probe)],
            cwd=lean_cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert overlap_res.returncode != 0

        raw_converse_probe = tmp_path / "BadConverseByDecide.lean"
        raw_converse_probe.write_text(
            "import Level15AuthorityCalculus\n"
            "theorem bad_converse_raw :\n"
            "    ∀ k : MSSN.Level15.StateKind,\n"
            "      ¬ MSSN.Level15.isTerminalAuthority k → MSSN.Level15.isProposal k := by\n"
            "  decide\n",
            encoding="utf-8",
        )
        raw_converse_res = subprocess.run(
            ["lake", "env", "lean", str(raw_converse_probe)],
            cwd=lean_cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert raw_converse_res.returncode != 0

        decidable_converse_probe = tmp_path / "BadConverseCaseDecide.lean"
        decidable_converse_probe.write_text(
            "import Level15AuthorityCalculus\n"
            "instance (k : MSSN.Level15.StateKind) : Decidable (MSSN.Level15.isProposal k) := by\n"
            "  unfold MSSN.Level15.isProposal; infer_instance\n"
            "instance (k : MSSN.Level15.StateKind) : Decidable (MSSN.Level15.isTerminalAuthority k) := by\n"
            "  unfold MSSN.Level15.isTerminalAuthority; infer_instance\n"
            "theorem bad_converse_cases :\n"
            "    ∀ k : MSSN.Level15.StateKind,\n"
            "      ¬ MSSN.Level15.isTerminalAuthority k → MSSN.Level15.isProposal k := by\n"
            "  intro k; cases k <;> decide\n",
            encoding="utf-8",
        )
        decidable_converse_res = subprocess.run(
            ["lake", "env", "lean", str(decidable_converse_probe)],
            cwd=lean_cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert decidable_converse_res.returncode != 0
        combined_diag = decidable_converse_res.stdout + decidable_converse_res.stderr
        assert "quotientWitness" in combined_diag
        assert "immutableRefusal" in combined_diag

        # 3. Negative census-tool probes: omitted declaration or injected Classical.choice / sorryAx
        omit_pkg = tmp_path / "omit_decl_pkg"
        shutil.copytree(_LEAN_DIR, omit_pkg / "lean4")
        census_file = omit_pkg / "lean4" / "Census.lean"
        census_lines = [
            ln
            for ln in census_file.read_text(encoding="utf-8").splitlines()
            if "theorem1_proposal_non_authority" not in ln
        ]
        census_file.write_text("\n".join(census_lines) + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="stale generated census"):
            census.check_census(omit_pkg)

        target_line = "'MSSN.Level15.theorem1_proposal_non_authority' does not depend on any axioms"
        for injected_axiom in ("Classical.choice", "sorryAx"):
            bad_pkg = tmp_path / f"inject_{injected_axiom.replace('.', '_')}"
            shutil.copytree(_LEAN_DIR, bad_pkg / "lean4")
            report_file = bad_pkg / "lean4" / "axiom_report.txt"
            mutated_report = report_file.read_text(encoding="utf-8").replace(
                target_line,
                f"'MSSN.Level15.theorem1_proposal_non_authority' depends on axioms: [{injected_axiom}]",
            )
            report_file.write_text(mutated_report, encoding="utf-8")
            with pytest.raises(ValueError, match="report counts disagree"):
                census.parse_report(bad_pkg)
            with pytest.raises(ValueError, match="report counts disagree"):
                census.check_census(bad_pkg)

    def test_finite_model_disjointness_and_non_exhaustive_complement_control(self) -> None:
        """Positive + negative control: proposal and terminal sets are disjoint, not exhaustive."""
        proposal_set = {k for k in _ModelStateKind if _model_is_proposal(k)}
        terminal_set = {k for k in _ModelStateKind if _model_is_terminal_authority(k)}
        neither_set = {
            k
            for k in _ModelStateKind
            if not _model_is_proposal(k) and not _model_is_terminal_authority(k)
        }

        assert proposal_set == {_ModelStateKind.PROPOSAL, _ModelStateKind.CANDIDATE_TRACE}
        assert terminal_set == {_ModelStateKind.TERMINAL_AUTHORITY}
        assert proposal_set.isdisjoint(terminal_set)

        for k in _ModelStateKind:
            if _model_is_proposal(k):
                assert not _model_is_terminal_authority(k)

        # Falsification of converse: ¬ isTerminalAuthority k does NOT imply isProposal k
        assert neither_set == {
            _ModelStateKind.QUOTIENT_WITNESS,
            _ModelStateKind.IMMUTABLE_REFUSAL,
        }

    def test_falsification_runtime_correspondence_gap_and_f1_probe(self) -> None:
        """Negative control: Lean StateKind has no FFI binding and historical gate F1 promoted (1,1,1)."""
        level15_source = (_LEAN_DIR / "Level15AuthorityCalculus.lean").read_text(encoding="utf-8")
        assert "@[extern" not in level15_source
        assert "@[export" not in level15_source

        falsifiers_payload = json.loads(_FALSIFIERS_JSON.read_text(encoding="utf-8"))
        assert falsifiers_payload["audited_commit"] == "30609de2c3928238715375a9bac608256fa381d8"
        f1 = next(row for row in falsifiers_payload["falsifiers"] if row["id"] == "F1")
        assert f1["defect"] == "input replacement"
        assert f1["observed"] == "AUTHORIZED"
        assert f1["is_authorized"] is True
        assert f1["trace"]["cochain_after_act4"] == [0.0]
