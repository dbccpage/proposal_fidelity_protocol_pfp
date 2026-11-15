"""Verification suite for Window 4 Wave 1 Shard A (Paper 003).

AuthorityEffect: None.

Targets four audit derivations:
1. AUDIT-P003-024: Historical commit 30609de2c floating-point allostery gate
   activating at default sum 2 on a single sensor, unenforced two-signal
   comment, and empty-list activation at t = 0.
2. AUDIT-P003-025: Historical commit 30609de2c thymic regex screen versus
   three of four non-regex AntigenMatcher adapters, including pharmacy rules
   screened by escaped failure-class name.
3. AUDIT-P003-029: Exact threshold and panel helper refusals of Boolean and
   inexact coefficients or masks and predicate bits outside declared universe.
4. AUDIT-P003-030: Examiner companion census (24 scoped problems across eight
   levels, worked study material, separate instructor key, and numerical replay).
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from eis.domain.allostery import AllostericConsensusGate
from eis.domain.ports import bound_rules
from eis.domain.thymus import ThymusGate
from eis.domain.value_objects import (
    AllosteryRefusal,
    DetectorRule,
    HillParameters,
    Signal1Match,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PFP003_DIR = _REPO_ROOT / "atlas" / "archive" / "pfp" / "003_pfp_host_admitted_failure_detectors"
_PFP003_CODE = _PFP003_DIR / "code"
_COMPANION_DIR = _PFP003_DIR / "_lev_examiner_theoretical_minimum_quiz"
_ISOLATED_NAMES = ("detector_lemmas",)

_EXPECTED_COMPANION_LF_SHA256 = {
    "00_preface_at_apartment_50.md": "ad76e553f2cc0211f9205ed4d070ec502a1e7e0ada151104e202043911e24da1",
    "quiz.md": "67c738d9a1b1551a8b1215e6deb11edd63a14e4104e0b90d1c75452ccbfa8d48",
    "study_guide.md": "a4aeeabfe84fc00aca136c2dbcf9d8c35166d3fbe1a7c1a34a99c1c6b8651e4b",
    "instructor_key.md": "adfb974c730a156678d12f306e9fd45f6ba33f3e74949abcb4d145f77cd51be9",
}


def _load_isolated_pfp003_modules() -> dict[str, Any]:
    """Import Paper 003 code modules without polluting global sys.path or writing bytecode."""
    saved_modules = {name: sys.modules.pop(name) for name in _ISOLATED_NAMES if name in sys.modules}
    saved_path = list(sys.path)
    saved_dont_write = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        sys.path[:0] = [str(_PFP003_CODE)]
        return {name: importlib.import_module(name) for name in _ISOLATED_NAMES}
    finally:
        sys.path[:] = saved_path
        sys.dont_write_bytecode = saved_dont_write
        for name in _ISOLATED_NAMES:
            sys.modules.pop(name, None)
        sys.modules.update(saved_modules)


_PFP003_MODULES = _load_isolated_pfp003_modules()
lemmas = _PFP003_MODULES["detector_lemmas"]


@pytest.fixture(autouse=True)
def _pin_pfp003_sys_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bind Paper 003 isolated modules inside each test scope via monkeypatch."""
    for name, mod in _PFP003_MODULES.items():
        monkeypatch.setitem(sys.modules, name, mod)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lf_sha256(path: Path) -> str:
    """Compute cross-OS SHA-256 after normalizing CRLF line endings to LF."""
    normalized = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def _historical_30609de2c_float_hill(
    signals: Sequence[float],
    n: float = 2.5,
    k: float = 2.0,
    activation_threshold: float = 0.5,
) -> tuple[bool, float, float]:
    """Evaluate the commit 30609de2c floating-point Hill gate documented in Appendix A.3/A.5."""
    theta = sum(val for val in signals if val > 0.0)
    hill = 0.0 if theta <= 0.0 else (theta**n) / (k**n + theta**n)
    return hill >= activation_threshold, hill, theta


class _StructuralMissingWitnessMatcher:
    """Minimal structural matcher mirroring PharmacyMatcher code selection on MISSING_WITNESS."""

    matcher_id = "pharmacy"
    detector_predicates: frozenset[str] = frozenset()
    reports_content_offsets = False

    def match_antigen(self, content: str, rules: Sequence[DetectorRule]) -> tuple[Signal1Match, ...]:
        active = bound_rules(self.matcher_id, rules)
        emitted_codes = ("MISSING_WITNESS",) if '"witness"' not in content else ()
        return tuple(
            Signal1Match(rule.target_epitope, code, 1.0, 0)
            for code in emitted_codes
            for rule in active
            if rule.match_pattern == code
        )


def _extract_problem_ids_by_level(markdown_text: str) -> dict[int, list[int]]:
    """Parse ## Level k sections and extract ordered **Qnn.** numbers within each level."""
    levels: dict[int, list[int]] = {}
    current_level: int | None = None
    for line in markdown_text.splitlines():
        level_match = re.match(r"^## Level (\d+)\b", line)
        if level_match is not None:
            current_level = int(level_match.group(1))
            if current_level in levels:
                raise ValueError(f"duplicate level heading: {current_level}")
            levels[current_level] = []
            continue
        q_match = re.match(r"^\*\*Q(\d{2})\.\*\*(?:\s+\S|\s*$)", line)
        if q_match is not None:
            if current_level is None:
                raise ValueError("problem prompt found before any Level heading")
            levels[current_level].append(int(q_match.group(1)))
    return levels


def _extract_instructor_worksheet(key_text: str) -> str:
    """Extract the standalone Python numerical replay block from instructor_key.md."""
    section_idx = key_text.index("## Replay the numerical answers")
    tail = key_text[section_idx:]
    match = re.search(r"```python\r?\n(.*?)```", tail, flags=re.DOTALL)
    if match is None:
        raise ValueError("missing python worksheet block in instructor_key.md")
    return match.group(1)


# ---------------------------------------------------------------------------
# 1. AUDIT-P003-024: Historical allostery gate
# ---------------------------------------------------------------------------


class TestHistoricalAllosteryGate:
    """Verifies AUDIT-P003-024: Historical commit 30609de2c float Hill gate behavior."""

    def test_historical_float_gate_activates_at_sum_two_with_single_sensor(self) -> None:
        """Default (n=2.5, K=2.0, t=0.5) gate activates at positive sum 2 on [2.0]."""
        activated_single, hill_single, theta_single = _historical_30609de2c_float_hill([2.0])
        assert activated_single is True
        assert theta_single == 2.0
        assert hill_single == 0.5

        # Negative values are ignored in the positive sum, matching Lemma B aggregation
        activated_mixed, hill_mixed, theta_mixed = _historical_30609de2c_float_hill([2.0, -9.0, 0.0])
        assert activated_mixed is True
        assert theta_mixed == 2.0
        assert hill_mixed == 0.5

        # Just below positive sum 2 does not activate
        activated_below, hill_below, _ = _historical_30609de2c_float_hill([1.999])
        assert activated_below is False
        assert hill_below < 0.5

        # Exact Lemma B(2) agrees at half-activation t = 1/2 for every positive integer n
        for n_int in (1, 2, 3, 5):
            assert lemmas.hill_activates([Fraction(2)], n_int, Fraction(2), Fraction(1, 2)) is True
            assert lemmas.hill_activates([Fraction(1999, 1000)], n_int, Fraction(2), Fraction(1, 2)) is False

    def test_historical_two_signal_comment_unenforced_without_cap_or_keying(self) -> None:
        """Without a per-sensor bound or sensor keying, [2.0] and [1.0, 1.0] both activate."""
        # Single uncapped entry reaches sum 2
        assert _historical_30609de2c_float_hill([2.0])[0] is True
        # Duplicate entries from one caller in an unkeyed list reach sum 2
        assert _historical_30609de2c_float_hill([1.0, 1.0])[0] is True

        # Exact contributor bound confirms m >= 2 holds when bound <= 1, whereas bound = 2 gives m = 1
        assert lemmas.minimum_contributors(2, Fraction(2), Fraction(1, 2), Fraction(1)) == 2
        assert lemmas.minimum_contributors(2, Fraction(2), Fraction(1, 2), Fraction(2)) == 1

    def test_historical_zero_threshold_activates_on_empty_list(self) -> None:
        """At t = 0, H([]) = 0 >= 0 activates on an empty list in float and exact Hill ratio."""
        activated_empty, hill_empty, theta_empty = _historical_30609de2c_float_hill(
            [], activation_threshold=0.0
        )
        assert activated_empty is True
        assert theta_empty == 0.0
        assert hill_empty == 0.0

        assert lemmas.hill_activates([], 2, Fraction(2), Fraction(0)) is True
        assert lemmas.hill_activates([-5, 0], 2, Fraction(2), Fraction(0)) is True

    def test_paper_and_regression_suite_record_pinned_30609de2c_counterexamples(self) -> None:
        """Audit trail in paper.md, paper_claim_ledger.md, and test_allostery_exact.py matches."""
        paper_text = (_PFP003_DIR / "paper.md").read_text(encoding="utf-8")
        ledger_text = (_PFP003_DIR / "paper_claim_ledger.md").read_text(encoding="utf-8")
        reg_text = (_REPO_ROOT / "eis" / "tests" / "unit" / "test_allostery_exact.py").read_text(
            encoding="utf-8"
        )

        assert "30609de2c3928238715375a9bac608256fa381d8" in paper_text
        assert "requires 2 equivalent unit signals" in paper_text
        assert "P3-24" in ledger_text and "30609de2c" in ledger_text
        assert "HillParameters(2.5, 2.0) used to be the default" in reg_text
        assert "activation_threshold=0 activated with zero signals" in reg_text

    # Negative controls / Falsification tests

    def test_falsification_repaired_gate_refuses_float_exponent_zero_threshold_and_list(self) -> None:
        """Negative control: Repaired SYS-EIS-002 gate refuses every historical 30609de2c defect."""
        with pytest.raises(AllosteryRefusal) as exc_float_n:
            HillParameters(hill_coefficient=2.5, half_maximal_constant=2)  # type: ignore[arg-type]
        assert exc_float_n.value.code == "NOT_EXACT"

        with pytest.raises(AllosteryRefusal) as exc_zero_t:
            AllostericConsensusGate(activation_threshold=0)
        assert exc_zero_t.value.code == "THRESHOLD_OUT_OF_RANGE"

        repaired = AllostericConsensusGate()
        with pytest.raises(AllosteryRefusal) as exc_list:
            repaired.evaluate_quorum([2])  # type: ignore[arg-type]
        assert exc_list.value.code == "SIGNALS_NOT_KEYED"

        with pytest.raises(AllosteryRefusal) as exc_cap:
            repaired.evaluate_quorum({"s1": 2})
        assert exc_cap.value.code == "SIGNAL_ABOVE_SENSOR_CAP"

    def test_falsification_positive_threshold_rejects_empty_list_and_threshold_one_never_activates(
        self,
    ) -> None:
        """Negative control: Positive threshold rejects [] and t = 1 rejects finite sums."""
        assert _historical_30609de2c_float_hill([], activation_threshold=0.5)[0] is False
        assert lemmas.hill_activates([], 2, Fraction(2), Fraction(1, 1000)) is False
        assert lemmas.hill_activates([Fraction(1000)], 2, Fraction(2), Fraction(1)) is False
        with pytest.raises(lemmas.LemmaInputError):
            lemmas.sum_threshold_activates([], 2, Fraction(2), Fraction(0))


# ---------------------------------------------------------------------------
# 2. AUDIT-P003-025: Historical screen/execution mismatch
# ---------------------------------------------------------------------------


class TestHistoricalScreenExecutionMismatch:
    """Verifies AUDIT-P003-025: Historical commit 30609de2c regex screen vs matchers."""

    def test_mssn_ports_ast_confirms_one_regex_matcher_and_three_non_regex_matchers(self) -> None:
        """AST inspection of mssn_ports.py confirms 1 regex matcher and 3 code-selecting matchers."""
        ports_source = (_REPO_ROOT / "eis" / "infrastructure" / "mssn_ports.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(ports_source)
        class_nodes = {
            node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
        }
        expected_classes = ("PatternMatcher", "PharmacyMatcher", "FarmMatcher", "ProtocolMatcher")
        for cls_name in expected_classes:
            assert cls_name in class_nodes

        call_names_by_class: dict[str, set[str]] = {}
        offsets_flag_by_class: dict[str, bool] = {}
        for cls_name in expected_classes:
            cls_node = class_nodes[cls_name]
            for stmt in cls_node.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                    and stmt.targets[0].id == "reports_content_offsets"
                    and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, bool)
                ):
                    offsets_flag_by_class[cls_name] = stmt.value.value
            match_fn = next(
                stmt
                for stmt in cls_node.body
                if isinstance(stmt, ast.FunctionDef) and stmt.name == "match_antigen"
            )
            calls: set[str] = set()
            for sub in ast.walk(match_fn):
                if isinstance(sub, ast.Call):
                    if isinstance(sub.func, ast.Name):
                        calls.add(sub.func.id)
                    elif isinstance(sub.func, ast.Attribute):
                        calls.add(sub.func.attr)
            call_names_by_class[cls_name] = calls

        assert offsets_flag_by_class == {
            "PatternMatcher": True,
            "PharmacyMatcher": False,
            "FarmMatcher": False,
            "ProtocolMatcher": False,
        }
        assert "compile_safe_pattern" in call_names_by_class["PatternMatcher"]
        assert "_select" not in call_names_by_class["PatternMatcher"]

        for non_regex_cls in ("PharmacyMatcher", "FarmMatcher", "ProtocolMatcher"):
            assert "compile_safe_pattern" not in call_names_by_class[non_regex_cls]
            assert "_select" in call_names_by_class[non_regex_cls]

    def test_pharmacy_class_name_regex_admits_rule_that_fires_on_self_fixture(self) -> None:
        """Screening re.escape(failure_class) admits rules whose structural check fires on self."""
        # Case 1: MISSING_WITNESS over the 4-element universe from test_two_signals_one_detector.py
        universe_mw = (
            '{"claim": "x", "witness": "w"}',
            '{"claim": "y", "evidence": []}',
            '{"claim": "z"}',
            "MISSING_WITNESS reported",
        )
        escaped_mw = re.escape("MISSING_WITNESS")
        screened_mw = lemmas.predicate_mask(
            lambda s: re.search(escaped_mw, s, re.IGNORECASE) is not None,
            universe_mw,
        )
        executed_mw = lemmas.predicate_mask(lambda s: '"witness"' not in s, universe_mw)
        panel_mw = (1 << 0) | (1 << 1)

        assert lemmas.admitted(screened_mw, panel_mw) is True
        assert lemmas.fires_on_self(executed_mw, panel_mw) is True
        assert lemmas.sound_for_every_panel(executed_mw, screened_mw, len(universe_mw)) is False

        # Case 2: UNGROUNDED_SELF_CERTIFICATION over JSON self fixture with verified: true
        universe_sc = (
            '{"move_type": "ASSERT", "payload": {"verified": false}}',
            '{"move_type": "ASSERT", "payload": {"verified": true}}',
            "UNGROUNDED_SELF_CERTIFICATION log line",
        )
        escaped_sc = re.escape("UNGROUNDED_SELF_CERTIFICATION")
        screened_sc = lemmas.predicate_mask(
            lambda s: re.search(escaped_sc, s, re.IGNORECASE) is not None,
            universe_sc,
        )
        executed_sc = lemmas.predicate_mask(
            lambda s: s.startswith("{") and json.loads(s).get("payload", {}).get("verified") is True,
            universe_sc,
        )
        panel_sc = (1 << 0) | (1 << 1)

        assert lemmas.admitted(screened_sc, panel_sc) is True
        assert lemmas.fires_on_self(executed_sc, panel_sc) is True
        assert lemmas.sound_for_every_panel(executed_sc, screened_sc, len(universe_sc)) is False

    # Negative controls / Falsification tests

    def test_falsification_screening_executed_predicate_purges_self_reactive_rule(self) -> None:
        """Negative control: When screened == executed, the self-reactive rule is rejected."""
        universe = (
            '{"claim": "x", "witness": "w"}',
            '{"claim": "y", "evidence": []}',
            '{"claim": "z"}',
            "MISSING_WITNESS reported",
        )
        executed = lemmas.predicate_mask(lambda s: '"witness"' not in s, universe)
        panel = (1 << 0) | (1 << 1)

        assert lemmas.admitted(executed, panel) is False
        assert lemmas.sound_for_every_panel(executed, executed, len(universe)) is True
        assert lemmas.rejects_no_harmless_rule(executed, executed, len(universe)) is True

    def test_falsification_repaired_thymus_refuses_unbound_and_purges_bound_matcher(self) -> None:
        """Negative control: Current ThymusGate refuses unbound non-regex rule and purges on self hit."""
        clean_with_witness = '{"claim": "x", "witness": "w"}'
        clean_without_witness = '{"claim": "y", "evidence": []}'
        rule = DetectorRule(
            rule_id="r-mw",
            target_epitope="missing-witness",
            match_pattern="MISSING_WITNESS",
            matcher_id="pharmacy",
        )
        thymus = ThymusGate([clean_with_witness, clean_without_witness])

        unbound = thymus.evaluate_rule(rule)
        assert unbound.is_admitted is False
        assert "THYMUS_MATCHER_UNBOUND" in unbound.rationale

        matcher = _StructuralMissingWitnessMatcher()
        purged = thymus.evaluate_rule(rule, matcher)
        assert purged.is_admitted is False
        assert purged.autoimmune_violations == 1

        admitted_clean = ThymusGate([clean_with_witness]).evaluate_rule(rule, matcher)
        assert admitted_clean.is_admitted is True


# ---------------------------------------------------------------------------
# 3. AUDIT-P003-029: Exact helper input boundaries
# ---------------------------------------------------------------------------


class TestExactHelperInputBoundaries:
    """Verifies AUDIT-P003-029: LemmaInputError boundaries in detector_lemmas.py."""

    def test_threshold_helpers_reject_boolean_and_inexact_coefficients_and_signals(self) -> None:
        """Threshold and count helpers reject bool, float, fractional n, and non-positive scales."""
        bad_signals: tuple[list[object], ...] = ([0.5], [1.0], [True], [False], ["1"])
        for signals in bad_signals:
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.positive_sum(signals)
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.hill_activates(signals, 2, 2, Fraction(1, 2))
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.sum_threshold_activates(signals, 2, 2, Fraction(1, 2))

        for bad_n in (True, False, 1.5, 2.0, Fraction(3, 2), 0, -1):
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.hill_activates([1], bad_n, 2, Fraction(1, 2))  # type: ignore[arg-type]
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.sum_threshold_activates([1], bad_n, 2, Fraction(1, 2))  # type: ignore[arg-type]

        for bad_k in (True, False, 2.0, 0.5, 0, -2, Fraction(0), Fraction(-1, 2)):
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.hill_activates([1], 2, bad_k, Fraction(1, 2))
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.sum_threshold_activates([1], 2, bad_k, Fraction(1, 2))

        for bad_t in (True, False, 0.5, "1/2"):
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.hill_activates([1], 2, 2, bad_t)
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.sum_threshold_activates([1], 2, 2, bad_t)

        for endpoint_t in (0, 1, Fraction(0), Fraction(1)):
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.sum_threshold_activates([1], 2, 2, endpoint_t)

        for bad_bound in (True, False, 1.0, 0.5, 0, -1, Fraction(0)):
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.minimum_contributors(2, 2, Fraction(1, 2), bad_bound)

        with pytest.raises(lemmas.LemmaInputError):
            lemmas.gate(True, None)  # type: ignore[arg-type]
        with pytest.raises(lemmas.LemmaInputError):
            lemmas.gate(1, ("HIGH", True))  # type: ignore[arg-type]

    def test_panel_helpers_reject_boolean_float_and_negative_masks(self) -> None:
        """Bitmask helpers reject bool, float, Fraction, and negative integer masks."""
        bad_masks: tuple[object, ...] = (True, False, 0.0, 1.5, Fraction(1, 2), -1)
        for bad in bad_masks:
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.admitted(bad, 1)  # type: ignore[arg-type]
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.admitted(1, bad)  # type: ignore[arg-type]
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.fires_on_self(bad, 1)  # type: ignore[arg-type]
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.fires_on_self(1, bad)  # type: ignore[arg-type]
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.sound_for_every_panel(bad, 0, 2)  # type: ignore[arg-type]
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.rejects_no_harmless_rule(0, bad, 2)  # type: ignore[arg-type]
            with pytest.raises(lemmas.LemmaInputError):
                lemmas.sound_for_every_panel(0, 0, bad)  # type: ignore[arg-type]

    def test_panel_soundness_helpers_reject_bits_outside_declared_universe(self) -> None:
        """sound_for_every_panel and rejects_no_harmless_rule reject masks >= (1 << universe_bits)."""
        for universe_bits in (0, 1, 2, 3):
            out_of_range = 1 << universe_bits
            for fn in (lemmas.sound_for_every_panel, lemmas.rejects_no_harmless_rule):
                with pytest.raises(lemmas.LemmaInputError, match="bits outside the declared universe"):
                    fn(out_of_range, 0, universe_bits)
                with pytest.raises(lemmas.LemmaInputError, match="bits outside the declared universe"):
                    fn(0, out_of_range, universe_bits)

    # Negative controls / Falsification tests

    def test_falsification_valid_exact_inputs_and_in_range_masks_succeed(self) -> None:
        """Negative control: Exact int/Fraction values and max in-universe masks succeed."""
        assert lemmas.positive_sum([1, Fraction(1, 2), -3, 0]) == Fraction(3, 2)
        assert lemmas.hill_activates([Fraction(3, 2), Fraction(1, 2)], 2, 2, Fraction(1, 2)) is True
        assert (
            lemmas.sum_threshold_activates([Fraction(3, 2), Fraction(1, 2)], 2, 2, Fraction(1, 2))
            is True
        )
        assert lemmas.minimum_contributors(2, 2, Fraction(1, 2), Fraction(3, 4)) == 3

        max_mask = (1 << 3) - 1  # 7 in a 3-bit universe
        assert lemmas.admitted(0, max_mask) is True
        assert lemmas.fires_on_self(max_mask, 1) is True
        assert lemmas.sound_for_every_panel(max_mask, max_mask, 3) is True
        assert lemmas.rejects_no_harmless_rule(max_mask, max_mask, 3) is True

    def test_falsification_naive_isinstance_int_guard_admits_booleans(self) -> None:
        """Negative control: Python isinstance(True, int) is True while _count/_exact reject bool."""
        assert isinstance(True, int) is True
        assert isinstance(False, int) is True
        with pytest.raises(lemmas.LemmaInputError):
            lemmas._count(True, "flag")
        with pytest.raises(lemmas.LemmaInputError):
            lemmas._exact(False, "flag")


# ---------------------------------------------------------------------------
# 4. AUDIT-P003-030: Examiner companion census
# ---------------------------------------------------------------------------


class TestExaminerCompanionCensus:
    """Verifies AUDIT-P003-030: Examiner 24-problem quiz, study guide, and separate key."""

    def test_companion_files_exist_with_pinned_lf_digests_and_metadata(self) -> None:
        """All four companion Markdown files exist with expected LF digests and zero authority."""
        for filename, expected_lf_sha in _EXPECTED_COMPANION_LF_SHA256.items():
            path = _COMPANION_DIR / filename
            assert path.is_file(), f"missing companion file: {filename}"
            assert _lf_sha256(path) == expected_lf_sha
            text = path.read_text(encoding="utf-8")
            assert 'authority_effect: "None"' in text
            assert "**AuthorityEffect:** None." in text

    def test_quiz_contains_twenty_four_scoped_problems_across_eight_levels(self) -> None:
        """quiz.md contains Q01..Q24 partitioned across Level 0..Level 7 (3 per level, 96 pts)."""
        quiz_text = (_COMPANION_DIR / "quiz.md").read_text(encoding="utf-8")
        levels = _extract_problem_ids_by_level(quiz_text)

        assert list(levels.keys()) == list(range(8))
        all_problem_ids = [qid for lvl in range(8) for qid in levels[lvl]]
        assert len(all_problem_ids) == 24
        assert all_problem_ids == list(range(1, 25))
        for lvl in range(8):
            expected_slice = [3 * lvl + 1, 3 * lvl + 2, 3 * lvl + 3]
            assert levels[lvl] == expected_slice

        assert "## Grading and advancement" in quiz_text
        assert "Maximum: 96." in quiz_text
        assert 24 * 4 == 96

    def test_study_guide_and_separate_instructor_key_bijection(self) -> None:
        """study_guide.md has worked material without Q01..Q24 answers; instructor_key.md is separate."""
        quiz_path = _COMPANION_DIR / "quiz.md"
        guide_path = _COMPANION_DIR / "study_guide.md"
        key_path = _COMPANION_DIR / "instructor_key.md"

        assert quiz_path.resolve() != key_path.resolve()
        assert guide_path.resolve() != key_path.resolve()
        assert _lf_sha256(quiz_path) != _lf_sha256(key_path)
        assert _lf_sha256(guide_path) != _lf_sha256(key_path)

        guide_text = guide_path.read_text(encoding="utf-8")
        key_text = key_path.read_text(encoding="utf-8")

        # Study guide has 8 worked sections + Local replay, and zero **Qnn.** answer entries
        worked_headings = re.findall(r"^## ([1-8])\.\s+\S", guide_text, flags=re.MULTILINE)
        assert worked_headings == [str(i) for i in range(1, 9)]
        assert "## Local replay" in guide_text
        assert re.findall(r"^\*\*Q\d{2}\.\*\*", guide_text, flags=re.MULTILINE) == []

        # Instructor key has exact 1-to-1 bijection across Level 0..7 and Q01..Q24
        quiz_levels = _extract_problem_ids_by_level(quiz_path.read_text(encoding="utf-8"))
        key_levels = _extract_problem_ids_by_level(key_text)
        assert key_levels == quiz_levels

    def test_instructor_key_numerical_worksheet_replays_cleanly(self) -> None:
        """Standalone Python numerical worksheet in instructor_key.md executes with exit code 0."""
        key_text = (_COMPANION_DIR / "instructor_key.md").read_text(encoding="utf-8")
        worksheet = _extract_instructor_worksheet(key_text)
        assert worksheet.count("assert ") == 8

        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", "-B", "-c", worksheet],
            cwd=str(_PFP003_DIR),
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr

    # Negative controls / Falsification tests

    def test_falsification_perturbed_worksheet_assertion_fails_replay(self) -> None:
        """Negative control: Perturbing 299 -> 298 in the Clopper-Pearson check fails closed."""
        key_text = (_COMPANION_DIR / "instructor_key.md").read_text(encoding="utf-8")
        worksheet = _extract_instructor_worksheet(key_text)
        target = "assert F(99, 100) ** 299 < F(1, 20)"
        assert target in worksheet
        perturbed = worksheet.replace(target, "assert F(99, 100) ** 298 < F(1, 20)", 1)

        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", "-B", "-c", perturbed],
            cwd=str(_PFP003_DIR),
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode != 0
        assert "AssertionError" in completed.stderr

    def test_falsification_census_validator_rejects_missing_problem_or_merged_key(self) -> None:
        """Negative control: Problem-census parser detects dropped Q24 or leaked answers in guide."""
        quiz_text = (_COMPANION_DIR / "quiz.md").read_text(encoding="utf-8")
        truncated_quiz = "\n".join(
            line for line in quiz_text.splitlines() if not line.startswith("**Q24.**")
        )
        parsed = _extract_problem_ids_by_level(truncated_quiz)
        flat_ids = [qid for lvl in sorted(parsed) for qid in parsed[lvl]]
        assert len(flat_ids) == 23
        assert flat_ids != list(range(1, 25))

        leaked_guide = "## 1. Worked section\n\n**Q01.** Leaked answer text.\n"
        assert re.findall(r"^\*\*Q\d{2}\.\*\*", leaked_guide, flags=re.MULTILINE) == ["**Q01.**"]
