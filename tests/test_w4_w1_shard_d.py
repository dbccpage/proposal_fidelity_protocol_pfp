"""Verification suite for Window 4 Wave 1 Shard D (Papers 007 and 008).

AuthorityEffect: None.

Targets four audit derivations:
1. AUDIT-P007-011: Legacy pedagogical test module checks chosen rational
   thresholds on supplied fixtures and counts supplied status strings without
   executing notebooks or measuring learner attention.
2. AUDIT-P007-013: Examiner study guide runs an exact standard-library
   Fraction worksheet as printed, and the quiz plus separate instructor key
   define 24 four-point problems (96 points) across eight instructional levels.
3. AUDIT-P008-003: Existence of a left inverse implies injectivity over
   general carriers without establishing deductive or semantic conservativity
   of an extended theory.
4. AUDIT-P008-004: Eight-wide integer opcode blocks b(N) = 128 + 8(N - 22) for
   N >= 22 are pairwise disjoint and lie above source opcodes (< 128), while
   fixed-width w-bit wire encodings overflow when b(N) + 7 >= 2^w.
"""

from __future__ import annotations

import ast
import contextlib
import importlib
import importlib.util
import io
import itertools
import re
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PFP007_ROOT = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "007_pfp_executable_lessons_and_evidence_boundaries"
)
_PFP007_TESTS = _PFP007_ROOT / "code" / "tests"
_PFP007_QUIZ_DIR = _PFP007_ROOT / "_lev_examiner_theoretical_minimum_quiz"

_PFP008_ROOT = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "008_pfp_mssn_tower_challenges_and_retraction_benchmarks"
)
_PFP008_CODE = _PFP008_ROOT / "code"
_PFP008_TESTS = _PFP008_CODE / "tests"
_TOWER_REGISTRY_PATH = _REPO_ROOT / "pfp" / "domain" / "tower" / "registry.py"

_ISOLATED_ARCHIVE_NAMES = (
    "test_007_pedagogical_transmission",
    "test_007_evidence_boundaries",
    "retraction_benchmark_runner",
    "test_008_mssn_tower_retraction",
)
_SYNTHETIC_REGISTRY_MOD = "_w4_w1_shard_d_tower_registry"


def _load_isolated_shard_d_modules() -> dict[str, Any]:
    """Import Paper 007, Paper 008, and tower registry modules without mutating global state."""
    tracked_names = (*_ISOLATED_ARCHIVE_NAMES, _SYNTHETIC_REGISTRY_MOD)
    saved_modules = {
        name: sys.modules.pop(name) for name in tracked_names if name in sys.modules
    }
    saved_path = list(sys.path)
    try:
        sys.path[:0] = [str(_PFP007_TESTS), str(_PFP008_TESTS), str(_PFP008_CODE)]
        loaded: dict[str, Any] = {
            name: importlib.import_module(name) for name in _ISOLATED_ARCHIVE_NAMES
        }
        spec = importlib.util.spec_from_file_location(
            _SYNTHETIC_REGISTRY_MOD, _TOWER_REGISTRY_PATH
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to build module spec for {_TOWER_REGISTRY_PATH}")
        reg_module = importlib.util.module_from_spec(spec)
        sys.modules[_SYNTHETIC_REGISTRY_MOD] = reg_module
        spec.loader.exec_module(reg_module)
        loaded[_SYNTHETIC_REGISTRY_MOD] = reg_module
        return loaded
    finally:
        sys.path[:] = saved_path
        for name in tracked_names:
            sys.modules.pop(name, None)
        sys.modules.update(saved_modules)


_SHARD_D_MODULES = _load_isolated_shard_d_modules()
ped_mod = _SHARD_D_MODULES["test_007_pedagogical_transmission"]
eb_mod = _SHARD_D_MODULES["test_007_evidence_boundaries"]
runner_mod = _SHARD_D_MODULES["retraction_benchmark_runner"]
t008_mod = _SHARD_D_MODULES["test_008_mssn_tower_retraction"]
tower_reg_mod = _SHARD_D_MODULES[_SYNTHETIC_REGISTRY_MOD]


@pytest.fixture(autouse=True)
def _pin_shard_d_sys_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep isolated archive and registry modules bound during each test."""
    for name, mod in _SHARD_D_MODULES.items():
        monkeypatch.setitem(sys.modules, name, mod)


# ---------------------------------------------------------------------------
# Helpers for Quiz Census and Finite Deductive Systems
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeductiveTheory:
    """Finite propositional deductive system (language, Horn-style inference rules)."""

    language: frozenset[str]
    rules: tuple[tuple[frozenset[str], str], ...]

    def theorems(self) -> frozenset[str]:
        """Compute exact least-fixed-point deductive closure Thm(T)."""
        derived: set[str] = set()
        changed = True
        while changed:
            changed = False
            for premises, conclusion in self.rules:
                if conclusion not in self.language or not premises.issubset(self.language):
                    raise ValueError("Rule references symbol outside declared language")
                if premises.issubset(derived) and conclusion not in derived:
                    derived.add(conclusion)
                    changed = True
        return frozenset(derived)

    def boolean_models(self) -> list[dict[str, int]]:
        """Enumerate all Boolean valuations v : language -> {0, 1} satisfying all rules."""
        atoms = sorted(self.language)
        models: list[dict[str, int]] = []
        for bits in itertools.product((0, 1), repeat=len(atoms)):
            valuation = dict(zip(atoms, bits, strict=True))
            satisfies_all = all(
                not all(valuation[p] == 1 for p in premises) or valuation[conclusion] == 1
                for premises, conclusion in self.rules
            )
            if satisfies_all:
                models.append(valuation)
        return models


def _parse_quiz_levels_and_problems(quiz_text: str) -> dict[int, list[int]]:
    """Parse ## Level k headings and numbered problem indices from quiz.md."""
    levels: dict[int, list[int]] = {}
    current_level: int | None = None
    for line in quiz_text.splitlines():
        header_match = re.match(r"^## Level (\d+):\s+\S+", line)
        if header_match:
            level_idx = int(header_match.group(1))
            if level_idx in levels:
                raise ValueError(f"Duplicate level heading: {level_idx}")
            levels[level_idx] = []
            current_level = level_idx
            continue
        if line.startswith("## "):
            current_level = None
            continue
        if current_level is not None:
            prob_match = re.match(r"^(\d+)\.\s+\*\*", line)
            if prob_match:
                levels[current_level].append(int(prob_match.group(1)))
    return levels


def _parse_instructor_key_rubric(key_text: str) -> dict[int, dict[int, tuple[int, ...]]]:
    """Parse ## Level k headings, **n.** entries, and (1)..(4) point items from instructor_key.md."""
    rubric: dict[int, dict[int, tuple[int, ...]]] = {}
    current_level: int | None = None
    for line in key_text.splitlines():
        header_match = re.match(r"^## Level (\d+)\s*$", line)
        if header_match:
            level_idx = int(header_match.group(1))
            if level_idx in rubric:
                raise ValueError(f"Duplicate key level heading: {level_idx}")
            rubric[level_idx] = {}
            current_level = level_idx
            continue
        if line.startswith("## "):
            current_level = None
            continue
        if current_level is not None:
            entry_match = re.match(r"^\*\*(\d+)\.\*\*\s+(.*)$", line)
            if entry_match:
                prob_num = int(entry_match.group(1))
                body = entry_match.group(2)
                items = tuple(int(tok) for tok in re.findall(r"(?:^|\s)\((\d+)\)\s", body))
                rubric[current_level][prob_num] = items
    return rubric


def _execute_worksheet_module(
    source_code: str,
    tmp_path: Path,
    module_name: str = "_shard_d_study_guide_ws",
) -> tuple[Any, str]:
    """Execute a worksheet code block via isolated importlib module loading and capture stdout."""
    script_path = tmp_path / f"{module_name}.py"
    script_path.write_text(source_code, encoding="utf-8", newline="\n")
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to build module spec for {script_path}")
    module = importlib.util.module_from_spec(spec)
    had_prev = module_name in sys.modules
    prev_mod = sys.modules.get(module_name)
    sys.modules[module_name] = module
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            spec.loader.exec_module(module)
        return module, buf.getvalue()
    finally:
        if had_prev and prev_mod is not None:
            sys.modules[module_name] = prev_mod
        else:
            sys.modules.pop(module_name, None)


# ---------------------------------------------------------------------------
# 1. AUDIT-P007-011: Legacy test scope
# ---------------------------------------------------------------------------


class TestLegacyTestScope:
    """Verifies AUDIT-P007-011: supplied thresholds and status-string counting in legacy tests."""

    def test_ast_structure_and_import_isolation(self) -> None:
        """AST inspection confirms stdlib-only imports and zero notebook/subprocess calls."""
        source_path = _PFP007_TESTS / "test_007_pedagogical_transmission.py"
        source_text = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source_text)

        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.add(node.module)

        assert imported_modules == {"__future__", "dataclasses", "fractions", "typing"}

        # Ensure zero calls to exec, eval, compile, open, read_text, or subprocess helpers
        forbidden_calls = {"exec", "eval", "compile", "open", "read_text", "read_bytes", "run"}
        called_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert called_names.isdisjoint(forbidden_calls)

        # Ensure zero float literals appear in the module AST
        float_literals = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and type(node.value) is float
        ]
        assert float_literals == []

    def test_micro_attention_pulse_window_and_boundaries(self) -> None:
        """Replays test_micro_attention_pulse_half_life and checks exact 3..5 boundaries."""
        ped_mod.test_micro_attention_pulse_half_life()

        for exact_pass in (Fraction(3, 1), Fraction(4, 1), Fraction(5, 1)):
            pulse = ped_mod.MicroAttentionPulse(
                pulse_index=1,
                duration_minutes=exact_pass,
                concept_id="c01",
                target_tier="tangible",
            )
            assert pulse.is_within_half_life() is True

        for exact_fail in (Fraction(299, 100), Fraction(501, 100)):
            pulse_out = ped_mod.MicroAttentionPulse(
                pulse_index=2,
                duration_minutes=exact_fail,
                concept_id="c02",
                target_tier="algorithmic",
            )
            assert pulse_out.is_within_half_life() is False

    def test_learning_metrics_thresholds_and_exact_boundaries(self) -> None:
        """Replays test_learning_metrics_threshold and checks exact (9/10, 17/20, 4/5) cutoffs."""
        ped_mod.test_learning_metrics_threshold()

        at_threshold = ped_mod.LearningCheckMetrics(
            diagnostic_pass_rate=Fraction(9, 10),
            transfer_index=Fraction(17, 20),
            teaching_efficiency=Fraction(4, 5),
        )
        assert at_threshold.meets_certification_standards() is True

    def test_headless_notebook_grading_counts_supplied_status_fields(self) -> None:
        """Replays test_headless_notebook_automated_grading and checks exact Fraction outputs."""
        ped_mod.test_headless_notebook_automated_grading()

        assert ped_mod.evaluate_headless_notebook_grade([]) == Fraction(0, 1)
        no_assert_cells = [
            {"cell_type": "markdown", "source": "assert nothing"},
            {"cell_type": "code", "source": "x = 1 + 1", "execution_status": "ok"},
        ]
        assert ped_mod.evaluate_headless_notebook_grade(no_assert_cells) == Fraction(0, 1)

    def test_falsification_non_assertions_and_unexecuted_code_cells(self) -> None:
        """Negative control: comments/strings with 'assert' and 'assert False' with 'ok' are not executed."""
        eb_mod.test_legacy_status_grade_counts_non_assertions_without_execution()

        # If code were executed, 1 / 0 and assert False would raise; instead supplied 'ok' gives 1/1
        unexecuted_cells = [
            {
                "cell_type": "code",
                "source": "1 / 0\nassert False",
                "execution_status": "ok",
            }
        ]
        grade_unexecuted = ped_mod.evaluate_headless_notebook_grade(unexecuted_cells)
        assert grade_unexecuted == Fraction(1, 1)
        assert isinstance(grade_unexecuted, Fraction)

        # Conversely, valid Python assertion with supplied 'error' status scores 0/1
        false_error_cells = [
            {
                "cell_type": "code",
                "source": "assert 1 + 1 == 2",
                "execution_status": "error",
            }
        ]
        assert ped_mod.evaluate_headless_notebook_grade(false_error_cells) == Fraction(0, 1)

    @pytest.mark.parametrize(
        ("pass_rate", "transfer", "efficiency"),
        [
            (Fraction(899, 1000), Fraction(17, 20), Fraction(4, 5)),
            (Fraction(9, 10), Fraction(849, 1000), Fraction(4, 5)),
            (Fraction(9, 10), Fraction(17, 20), Fraction(799, 1000)),
        ],
        ids=["below-pass-rate", "below-transfer", "below-efficiency"],
    )
    def test_falsification_perturbing_any_single_metric_below_threshold_fails(
        self, pass_rate: Fraction, transfer: Fraction, efficiency: Fraction
    ) -> None:
        """Negative control: dropping any single supplied metric by 1/1000 below threshold fails."""
        metrics = ped_mod.LearningCheckMetrics(
            diagnostic_pass_rate=pass_rate,
            transfer_index=transfer,
            teaching_efficiency=efficiency,
        )
        assert metrics.meets_certification_standards() is False


# ---------------------------------------------------------------------------
# 2. AUDIT-P007-013: Worksheet and quiz census
# ---------------------------------------------------------------------------


class TestWorksheetAndQuizCensus:
    """Verifies AUDIT-P007-013: study guide exact worksheet and 24-problem 8-level quiz census."""

    def test_study_guide_contains_single_stdlib_worksheet_and_runs_as_printed(
        self, tmp_path: Path
    ) -> None:
        """Confirms single Python worksheet in study_guide.md runs cleanly as printed."""
        eb_mod.test_study_guide_worksheet_runs_exactly_as_printed()

        guide_text = (_PFP007_QUIZ_DIR / "study_guide.md").read_text(encoding="utf-8")
        blocks = re.findall(r"```python\n(.*?)```", guide_text, flags=re.S)
        assert len(blocks) == 1

        # Verify AST imports only fractions.Fraction
        worksheet_tree = ast.parse(blocks[0])
        imports = [
            (node.module, [alias.name for alias in node.names])
            for node in ast.walk(worksheet_tree)
            if isinstance(node, ast.ImportFrom)
        ]
        assert imports == [("fractions", ["Fraction"])]
        assert not any(isinstance(node, ast.Import) for node in ast.walk(worksheet_tree))

        _, stdout_text = _execute_worksheet_module(blocks[0], tmp_path)
        assert stdout_text.strip() == "triangle, changed-input probes, and wrong-sign control pass"

    def test_worksheet_exact_fraction_values_and_wrong_sign_control(
        self, tmp_path: Path
    ) -> None:
        """Inspects exact Fraction namespace produced by executing the study guide worksheet."""
        guide_text = (_PFP007_QUIZ_DIR / "study_guide.md").read_text(encoding="utf-8")
        block = re.findall(r"```python\n(.*?)```", guide_text, flags=re.S)[0]
        ws_mod, _ = _execute_worksheet_module(block, tmp_path)

        assert ws_mod.df == (Fraction(1, 3), Fraction(1, 3), Fraction(-2, 3))
        assert ws_mod.r == (Fraction(0), Fraction(0), Fraction(1))
        assert ws_mod.negated == (Fraction(-2, 3), Fraction(-2, 3), Fraction(1, 3))
        assert ws_mod.wrong_df == (Fraction(-1, 3), Fraction(-1, 3), Fraction(2, 3))
        assert ws_mod.wrong_r == (Fraction(2, 3), Fraction(2, 3), Fraction(-1, 3))
        assert sum(ws_mod.wrong_df, Fraction(0)) == Fraction(0)
        assert sum(ws_mod.wrong_r, Fraction(0)) == Fraction(1)
        assert ws_mod.wrong_df != ws_mod.df
        assert ws_mod.completed == ws_mod.df

    def test_quiz_has_twenty_four_four_point_problems_across_eight_levels(self) -> None:
        """Verifies 8 instructional levels (0..7), 3 problems per level, 24 problems, 96 points."""
        quiz_text = (_PFP007_QUIZ_DIR / "quiz.md").read_text(encoding="utf-8")
        assert (
            "eight instructional levels, three problems per level, four points per problem: 96 points total."
            in quiz_text
        )

        levels = _parse_quiz_levels_and_problems(quiz_text)
        assert list(levels.keys()) == list(range(8))

        all_problem_numbers: list[int] = []
        for level_idx in range(8):
            probs = levels[level_idx]
            assert len(probs) == 3
            assert probs == [3 * level_idx + 1, 3 * level_idx + 2, 3 * level_idx + 3]
            all_problem_numbers.extend(probs)

        assert len(all_problem_numbers) == 24
        assert all_problem_numbers == list(range(1, 25))
        assert Fraction(len(all_problem_numbers), len(levels)) == Fraction(3, 1)
        assert len(all_problem_numbers) * 4 == 96

    def test_separate_instructor_key_scores_all_ninety_six_points_and_declares_scope(self) -> None:
        """Verifies separate instructor_key.md has 24 four-item rubrics (96 points) and scope boundaries."""
        quiz_path = _PFP007_QUIZ_DIR / "quiz.md"
        key_path = _PFP007_QUIZ_DIR / "instructor_key.md"
        assert quiz_path.resolve() != key_path.resolve()

        key_text = key_path.read_text(encoding="utf-8")
        assert "four per problem, 96 total" in key_text
        assert "eight level subtotals (12 points each)" in key_text
        assert "no calibrated cutoff" in key_text

        rubric = _parse_instructor_key_rubric(key_text)
        assert list(rubric.keys()) == list(range(8))

        total_points = 0
        for level_idx in range(8):
            level_entries = rubric[level_idx]
            assert list(level_entries.keys()) == [
                3 * level_idx + 1,
                3 * level_idx + 2,
                3 * level_idx + 3,
            ]
            level_points = 0
            for prob_num, item_indices in level_entries.items():
                assert 1 <= prob_num <= 24
                assert item_indices == (1, 2, 3, 4)
                level_points += len(item_indices)
            assert level_points == 12
            total_points += level_points

        assert total_points == 96

    def test_falsification_corrupted_worksheet_assertion_fails_execution(
        self, tmp_path: Path
    ) -> None:
        """Negative control: mutating exact vs float inequality in worksheet raises AssertionError."""
        guide_text = (_PFP007_QUIZ_DIR / "study_guide.md").read_text(encoding="utf-8")
        block = re.findall(r"```python\n(.*?)```", guide_text, flags=re.S)[0]
        mutated = block.replace("Q(1 / 3) != Q(1, 3)", "Q(1 / 3) == Q(1, 3)")
        assert mutated != block

        with pytest.raises(AssertionError):
            _execute_worksheet_module(mutated, tmp_path, module_name="_shard_d_mutated_ws")

    def test_falsification_altered_quiz_or_rubric_counts_fail_census(self) -> None:
        """Negative control: dropping a problem or rubric item is caught by census parsers."""
        quiz_text = (_PFP007_QUIZ_DIR / "quiz.md").read_text(encoding="utf-8")
        truncated_quiz = "\n".join(
            line for line in quiz_text.splitlines() if not line.startswith("24. **")
        )
        parsed_trunc = _parse_quiz_levels_and_problems(truncated_quiz)
        assert len(parsed_trunc[7]) == 2
        assert sum(len(v) for v in parsed_trunc.values()) == 23

        key_text = (_PFP007_QUIZ_DIR / "instructor_key.md").read_text(encoding="utf-8")
        damaged_key = key_text.replace("(4) No filled face", "No filled face", 1)
        parsed_key = _parse_instructor_key_rubric(damaged_key)
        assert parsed_key[0][1] == (1, 2, 3)


# ---------------------------------------------------------------------------
# 3. AUDIT-P008-003: Left inverse vs conservativity
# ---------------------------------------------------------------------------


class TestLeftInverseVsConservativity:
    """Verifies AUDIT-P008-003: general left-inverse injectivity vs theory conservativity."""

    def test_general_left_inverse_characterizes_injectivity_on_finite_carriers(self) -> None:
        """Exhaustively checks all 4^3 = 64 maps u : {0,1,2} -> {0,1,2,3} for left inverses."""
        domain_a = (0, 1, 2)
        codomain_b = (0, 1, 2, 3)

        injective_count = 0
        left_invertible_count = 0

        for image_tuple in itertools.product(codomain_b, repeat=len(domain_a)):
            u_map = dict(zip(domain_a, image_tuple, strict=True))
            is_injective = len(set(image_tuple)) == len(domain_a)

            # Check whether any total retraction d : B -> A satisfies d(u(a)) == a for all a in A
            has_left_inverse = any(
                all(d_tuple[u_map[a]] == a for a in domain_a)
                for d_tuple in itertools.product(domain_a, repeat=len(codomain_b))
            )

            assert has_left_inverse is is_injective
            if is_injective:
                injective_count += 1
            if has_left_inverse:
                left_invertible_count += 1

        assert injective_count == 24
        assert left_invertible_count == 24

    def test_partial_retraction_with_refusal_sum_preserves_injectivity_without_right_inverse(
        self,
    ) -> None:
        """Checks d : B -> A + Refusal gives u injective while failing right-invertibility on B \\ u(A)."""
        domain_a = ("term_0", "term_1", "term_2")
        codomain_b = ("term_0", "term_1", "term_2", "foreign_3", "foreign_4")
        refusal_sentinel = ("REFUSAL",)

        def u_embed(a: str) -> str:
            if a not in domain_a:
                raise ValueError("Outside domain A")
            return a

        def d_retract(b: str) -> str | tuple[str, str]:
            if b not in codomain_b:
                raise ValueError("Outside codomain B")
            if b in domain_a:
                return b
            return (refusal_sentinel[0], b)

        # Left-inverse law d(u(a)) == a holds on every element of multi-element carrier A
        for a in domain_a:
            assert u_embed(a) in codomain_b
            assert d_retract(u_embed(a)) == a

        # Pairwise distinctness u(a) == u(a') => a == a'
        for a1, a2 in itertools.product(domain_a, repeat=2):
            if u_embed(a1) == u_embed(a2):
                assert a1 == a2

        # Out-of-image elements yield typed refusal outside domain(u), so no right inverse holds
        foreign_elements = tuple(b for b in codomain_b if b not in domain_a)
        assert foreign_elements == ("foreign_3", "foreign_4")
        for b_foreign in foreign_elements:
            out = d_retract(b_foreign)
            assert isinstance(out, tuple)
            with pytest.raises(ValueError, match="Outside domain A"):
                u_embed(out)  # type: ignore[arg-type]

    def test_deductive_counterexample_direct_old_axiom_breaks_conservativity(self) -> None:
        """Counterexample 1 (Paper 008 Sec 3): adding old-language axiom phi breaks conservativity."""
        lang_a = frozenset({"top_a", "phi"})
        lang_b = frozenset({"top_a", "phi", "psi_new"})

        theory_a = DeductiveTheory(
            language=lang_a,
            rules=((frozenset(), "top_a"),),
        )
        theory_b = DeductiveTheory(
            language=lang_b,
            rules=(
                (frozenset(), "top_a"),
                (frozenset(), "phi"),
            ),
        )

        u_map = {x: x for x in lang_a}
        d_map = {"top_a": "top_a", "phi": "phi", "psi_new": "top_a"}

        # Left inverse d o u = id_A holds and u is injective on 2-element L_A
        assert all(d_map[u_map[a]] == a for a in lang_a)
        assert len({u_map[a] for a in lang_a}) == len(lang_a) == 2

        thm_a = theory_a.theorems()
        thm_b = theory_b.theorems()
        assert thm_a == frozenset({"top_a"})
        assert thm_b == frozenset({"top_a", "phi"})

        # Old-language formula phi is derived in T_B while underivable in T_A
        assert u_map["phi"] in thm_b
        assert "phi" not in thm_a

    def test_deductive_counterexample_new_symbol_bridge_breaks_conservativity(self) -> None:
        """Counterexample 2: new symbol psi_new + bridge rule psi_new |- phi breaks conservativity."""
        lang_a = frozenset({"top_a", "phi"})
        lang_b = frozenset({"top_a", "phi", "psi_new"})

        theory_a = DeductiveTheory(
            language=lang_a,
            rules=((frozenset(), "top_a"),),
        )
        theory_b = DeductiveTheory(
            language=lang_b,
            rules=(
                (frozenset(), "top_a"),
                (frozenset(), "psi_new"),
                (frozenset({"psi_new"}), "phi"),
            ),
        )

        u_map = {x: x for x in lang_a}
        d_partial = {"top_a": "top_a", "phi": "phi", "psi_new": None}
        assert all(d_partial[u_map[a]] == a for a in lang_a)

        thm_a = theory_a.theorems()
        thm_b = theory_b.theorems()
        assert thm_a == frozenset({"top_a"})
        assert thm_b == frozenset({"top_a", "psi_new", "phi"})

        reflected = {a for a in lang_a if u_map[a] in thm_b}
        assert reflected != thm_a
        assert reflected - thm_a == {"phi"}

    def test_semantic_valuation_counterexample_breaks_model_conservativity(self) -> None:
        """Semantic check: Boolean model v0(top_a)=1, v0(phi)=0 of T_A has zero extensions to T_B."""
        lang_a = frozenset({"top_a", "phi"})
        lang_b = frozenset({"top_a", "phi", "psi_new"})

        theory_a = DeductiveTheory(
            language=lang_a,
            rules=((frozenset(), "top_a"),),
        )
        theory_b = DeductiveTheory(
            language=lang_b,
            rules=(
                (frozenset(), "top_a"),
                (frozenset(), "psi_new"),
                (frozenset({"psi_new"}), "phi"),
            ),
        )

        models_a = theory_a.boolean_models()
        models_b = theory_b.boolean_models()

        # T_A has 2 models: phi=0 and phi=1, so T_A does not entail phi
        assert len(models_a) == 2
        assert any(m["phi"] == 0 for m in models_a)

        # T_B has 1 model where top_a=1, psi_new=1, phi=1, so T_B entails phi
        assert models_b == [{"phi": 1, "psi_new": 1, "top_a": 1}]
        assert all(m["phi"] == 1 for m in models_b)

    def test_positive_control_conservative_extension_preserves_old_theorems(self) -> None:
        """Positive control: extending T_A with rule top_a |- psi_new is conservative over L_A."""
        lang_a = frozenset({"top_a", "phi"})
        lang_b = frozenset({"top_a", "phi", "psi_new"})

        theory_a = DeductiveTheory(
            language=lang_a,
            rules=((frozenset(), "top_a"),),
        )
        theory_b_conservative = DeductiveTheory(
            language=lang_b,
            rules=(
                (frozenset(), "top_a"),
                (frozenset({"top_a"}), "psi_new"),
            ),
        )

        u_map = {x: x for x in lang_a}
        thm_a = theory_a.theorems()
        thm_b = theory_b_conservative.theorems()
        assert thm_b == frozenset({"top_a", "psi_new"})
        assert {a for a in lang_a if u_map[a] in thm_b} == thm_a

    def test_falsification_non_injective_map_admits_no_left_inverse(self) -> None:
        """Negative control: collapsing map u(top_a) = u(phi) cannot have any left inverse d."""
        domain_a = ("top_a", "phi")
        codomain_b = ("collapsed", "psi_new")
        u_collapsing = {"top_a": "collapsed", "phi": "collapsed"}

        for d_tuple in itertools.product(domain_a, repeat=len(codomain_b)):
            d_candidate = dict(zip(codomain_b, d_tuple, strict=True))
            assert not all(d_candidate[u_collapsing[a]] == a for a in domain_a)


# ---------------------------------------------------------------------------
# 4. AUDIT-P008-004: Opcode block disjointness
# ---------------------------------------------------------------------------


class TestOpcodeBlockDisjointness:
    """Verifies AUDIT-P008-004: disjointness of 8-wide integer opcode blocks and fixed-width bounds."""

    def test_algebraic_gap_identity_and_source_namespace_separation(self) -> None:
        """Verifies b(N) >= 128 > max(SOURCE_OPCODE_SET) and b(M) - (b(N) + 7) == 8(M - N) - 7 >= 1."""
        source_opcodes = tower_reg_mod.SOURCE_OPCODE_SET
        assert len(source_opcodes) == 39
        assert min(source_opcodes) == 0
        max_source_opcode = max(source_opcodes)
        assert max_source_opcode == 45
        assert max_source_opcode < tower_reg_mod.PROPOSAL_START
        assert tower_reg_mod.PROPOSAL_START == 128

        # Verify exact gap formula across a wide range of integer stage pairs 22 <= n < m <= 250
        for n in range(22, 251):
            base_n = runner_mod.compute_opcode_base(n)
            assert base_n == 128 + 8 * (n - 22)
            assert base_n >= 128
            for m in range(n + 1, 251):
                base_m = runner_mod.compute_opcode_base(m)
                gap = base_m - (base_n + 7)
                assert gap == 8 * (m - n) - 7
                assert gap >= 1

    def test_runner_and_domain_registry_agree_across_stages_0_to_100(self) -> None:
        """Verifies runner compute_opcode_base matches pfp/domain/tower/registry.py across 0..100."""
        tower_reg_mod.check_registry()
        stages = tower_reg_mod.load_stages()
        assert len(stages) == 101
        assert [s.level for s in stages] == list(range(101))

        for stage in stages:
            if stage.level < 22:
                assert runner_mod.compute_opcode_base(stage.level) == 0
                assert stage.reserved_opcodes == ()
                if stage.primary_opcode is not None:
                    assert stage.primary_opcode in tower_reg_mod.SOURCE_OPCODE_SET
                    assert stage.primary_opcode < 128
            else:
                expected_base = 128 + 8 * (stage.level - 22)
                assert runner_mod.compute_opcode_base(stage.level) == expected_base
                assert stage.primary_opcode == expected_base
                assert stage.reserved_opcodes == tuple(range(expected_base, expected_base + 8))

    def test_exhaustive_pairwise_disjointness_for_stages_22_to_100(self) -> None:
        """Replays Paper 008 opcode test and checks exact union cardinality 79 * 8 == 632."""
        t008_mod.test_opcode_base_progression()
        t008_mod.test_opcode_blocks_are_disjoint_for_stages_22_to_100()

        blocks = {
            n: frozenset(
                range(runner_mod.compute_opcode_base(n), runner_mod.compute_opcode_base(n) + 8)
            )
            for n in range(22, 101)
        }
        assert len(blocks) == 79
        assert min(blocks[22]) == 128 and max(blocks[22]) == 135
        assert min(blocks[100]) == 752 and max(blocks[100]) == 759

        for n, m in itertools.combinations(range(22, 101), 2):
            assert blocks[n].isdisjoint(blocks[m])

        union_opcodes = frozenset().union(*blocks.values())
        assert len(union_opcodes) == 79 * 8 == 632
        assert union_opcodes == frozenset(range(128, 760))
        assert union_opcodes.isdisjoint(tower_reg_mod.SOURCE_OPCODE_SET)

    def test_falsification_eight_bit_wire_overflows_at_stage_38_and_collides_mod_256(self) -> None:
        """Negative control: w = 8 unsigned wire fits stage 37 (max 255) and overflows at stage 38 (256..263)."""
        block_37 = tuple(
            range(runner_mod.compute_opcode_base(37), runner_mod.compute_opcode_base(37) + 8)
        )
        block_38 = tuple(
            range(runner_mod.compute_opcode_base(38), runner_mod.compute_opcode_base(38) + 8)
        )
        assert block_37 == tuple(range(248, 256))
        assert max(block_37) == 255 < 2**8

        assert block_38 == tuple(range(256, 264))
        assert min(block_38) == 256 >= 2**8
        assert max(block_38) == 263 >= 2**8

        # Modulo-256 truncation wraps stage 38 onto {0..7}, colliding with SOURCE_OPCODE_SET
        wrapped_38 = {op % 256 for op in block_38}
        assert wrapped_38 == set(range(8))
        assert len(wrapped_38 & tower_reg_mod.SOURCE_OPCODE_SET) == 8

        # Stage 54 has base 128 + 8 * 32 = 384, wrapping mod 256 onto stage 22 [128..135]
        block_22 = {
            op % 256
            for op in range(
                runner_mod.compute_opcode_base(22), runner_mod.compute_opcode_base(22) + 8
            )
        }
        block_54 = {
            op % 256
            for op in range(
                runner_mod.compute_opcode_base(54), runner_mod.compute_opcode_base(54) + 8
            )
        }
        assert block_54 == block_22 == set(range(128, 136))

    @pytest.mark.parametrize(
        ("bit_width", "expected_max_stage"),
        [(8, 37), (9, 69), (10, 133), (12, 517), (16, 8197)],
    )
    def test_falsification_general_fixed_width_wire_ceilings(
        self, bit_width: int, expected_max_stage: int
    ) -> None:
        """Negative control: exact fixed-width ceiling N_max(w) = 5 + 2^(w - 3) for w >= 8."""
        limit = 2**bit_width
        computed_max_stage = 5 + 2 ** (bit_width - 3)
        assert computed_max_stage == expected_max_stage

        # Last valid stage ends right at 2^w - 1
        assert runner_mod.compute_opcode_base(expected_max_stage) + 7 == limit - 1
        # Next stage immediately overflows 2^w
        assert runner_mod.compute_opcode_base(expected_max_stage + 1) == limit
        assert runner_mod.compute_opcode_base(expected_max_stage + 1) + 7 == limit + 7 >= limit

    def test_falsification_sub_eight_stride_causes_adjacent_block_overlap(self) -> None:
        """Negative control: reducing stride from 8 to 7 with width 8 creates overlap at stage 23."""
        def faulty_block(stage: int, stride: int = 7, width: int = 8) -> set[int]:
            base = 128 + stride * (stage - 22)
            return set(range(base, base + width))

        overlap = faulty_block(22) & faulty_block(23)
        assert overlap == {135}
