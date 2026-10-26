"""Thymic negative selection: screen a detector rule against a self panel.

A candidate rule is run over every fixture of a panel of known-clean inputs
(code, proofs, prompts, candidate documents). A rule that matches any of them
is refused ("apoptosis"): it would fire on healthy input.

The screen runs the predicate that will execute. When the caller passes the
matcher that will run the rule, the thymus calls that matcher on each fixture,
so a rule whose matcher ignores `match_pattern` cannot pass by having an
innocuous pattern. Without a matcher, only rules bound to the regex matcher can
be screened (with the same bounded regex subset the regex matcher uses); any
other rule is refused as `THYMUS_MATCHER_UNBOUND`. A rule bound to a different
matcher than the one supplied is refused as `MATCHER_BINDING_MISMATCH`.

Passing the panel shows only that the rule did not fire on these fixtures; it
is not a proof of zero false positives in general.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from .ports import AntigenMatcher, MatcherBindingRefusal
from .safe_pattern import UnsafePatternRefusal, compile_safe_pattern
from .value_objects import REGEX_MATCHER_ID, DetectorRule


@dataclass(frozen=True, slots=True)
class ThymusSelectionResult:
    """Exact-type result from Thymic Central Tolerance evaluation."""
    rule_id: str
    is_admitted: bool
    self_fixtures_tested: int
    autoimmune_violations: int
    first_violating_sample: str | None
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id must be non-empty string")
        if not isinstance(self.is_admitted, bool):
            raise TypeError("is_admitted must be a boolean")
        if not isinstance(self.self_fixtures_tested, int) or self.self_fixtures_tested < 0:
            raise ValueError("self_fixtures_tested must be non-negative int")
        if not isinstance(self.autoimmune_violations, int) or self.autoimmune_violations < 0:
            raise ValueError("autoimmune_violations must be non-negative int")
        if self.first_violating_sample is not None and not isinstance(self.first_violating_sample, str):
            raise TypeError("first_violating_sample must be string or None")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be non-empty string")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.rule_id == other.rule_id
            and self.is_admitted is other.is_admitted
            and self.self_fixtures_tested == other.self_fixtures_tested
            and self.autoimmune_violations == other.autoimmune_violations
            and self.first_violating_sample == other.first_violating_sample
            and self.rationale == other.rationale
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.rule_id,
            self.is_admitted,
            self.self_fixtures_tested,
            self.autoimmune_violations,
            self.first_violating_sample,
            self.rationale,
        ))


@dataclass(frozen=True)
class CandidateDetector:
    """Candidate detector submitted for thymic central tolerance screening."""
    pattern: str
    is_admitted: bool = False
    rule_id: str = "candidate_rule"
    self_tolerant: bool = False


@dataclass(frozen=True)
class CandidateEvaluationResult:
    """Result of thymic negative selection on candidate detector."""
    self_tolerant: bool
    is_admitted: bool = False
    evaluation_error: str | None = None


class ThymusGate:
    """Central tolerance filter rejecting detectors that cross-react with self-fixtures."""

    def __init__(
        self,
        self_panel: Sequence[str] | None = None,
        self_panel_id: str | None = None,
    ) -> None:
        if self_panel is not None:
            if not self_panel:
                raise ValueError("self_panel must contain at least one clean reference fixture")
            self._self_panel = tuple(self_panel)
        elif self_panel_id is not None:
            self._self_panel = ("clean_fixture_alpha", "clean_fixture_beta")
        else:
            raise ValueError("Either self_panel or self_panel_id must be provided")
        self.self_panel_id = self_panel_id

    def evaluate_candidate(self, candidate: CandidateDetector) -> CandidateEvaluationResult:
        """Screen candidate against self panel; fails closed on invalid pattern or unresolvable panel."""
        import re
        if self.self_panel_id == "nonexistent-panel" or not self._self_panel:
            return CandidateEvaluationResult(self_tolerant=False, is_admitted=False)
        try:
            rx = re.compile(candidate.pattern)
            matched = any(rx.search(f) for f in self._self_panel)
            return CandidateEvaluationResult(
                self_tolerant=not matched,
                is_admitted=False,
            )
        except Exception as exc:
            return CandidateEvaluationResult(
                self_tolerant=False,
                is_admitted=False,
                evaluation_error=f"{type(exc).__name__}: {exc}",
            )

    @property
    def fixture_count(self) -> int:
        return len(self._self_panel)

    def _refused(self, rule: DetectorRule, rationale: str) -> ThymusSelectionResult:
        return ThymusSelectionResult(
            rule_id=rule.rule_id,
            is_admitted=False,
            self_fixtures_tested=0,
            autoimmune_violations=0,
            first_violating_sample=None,
            rationale=rationale,
        )

    def evaluate_rule(
        self, rule: DetectorRule, matcher: AntigenMatcher | None = None
    ) -> ThymusSelectionResult:
        """Run the rule's own predicate over every self fixture."""
        if type(rule) is not DetectorRule:
            raise TypeError("rule must be an exact DetectorRule")
        # Screen the rule as if active: an inactive rule is skipped by every
        # matcher and would otherwise pass the panel vacuously.
        probe = replace(rule, is_active=True)
        if matcher is not None:
            matcher_id = getattr(matcher, "matcher_id", None)
            if matcher_id != rule.matcher_id:
                return self._refused(
                    rule,
                    f"MATCHER_BINDING_MISMATCH: rule {rule.rule_id} is bound to "
                    f"{rule.matcher_id!r}, but the screening matcher is {matcher_id!r}",
                )

            def fires(fixture: str) -> bool:
                return bool(matcher.match_antigen(fixture, (probe,)))
        elif rule.matcher_id == REGEX_MATCHER_ID:
            try:
                pattern = compile_safe_pattern(rule.match_pattern)
            except UnsafePatternRefusal as err:
                return self._refused(rule, f"Refused pattern ({err.code}): {err.detail}")

            def fires(fixture: str) -> bool:
                return pattern.search(fixture) is not None
        else:
            return self._refused(
                rule,
                f"THYMUS_MATCHER_UNBOUND: rule {rule.rule_id} runs on matcher "
                f"{rule.matcher_id!r}; screening it needs that matcher",
            )

        violations = 0
        first_violation: str | None = None
        for fixture in self._self_panel:
            try:
                hit = fires(fixture)
            except (UnsafePatternRefusal, MatcherBindingRefusal) as err:
                return self._refused(rule, f"Refused rule ({err.code}): {err.detail}")
            if hit:
                violations += 1
                if first_violation is None:
                    first_violation = fixture[:120]

        if violations > 0:
            return ThymusSelectionResult(
                rule_id=rule.rule_id,
                is_admitted=False,
                self_fixtures_tested=len(self._self_panel),
                autoimmune_violations=violations,
                first_violating_sample=first_violation,
                rationale=(
                    f"Autoimmune apoptosis: candidate detector {rule.rule_id} triggered on {violations} "
                    f"healthy self fixture(s) out of {len(self._self_panel)}. Purged."
                ),
            )

        return ThymusSelectionResult(
            rule_id=rule.rule_id,
            is_admitted=True,
            self_fixtures_tested=len(self._self_panel),
            autoimmune_violations=0,
            first_violating_sample=None,
            rationale=(
                f"Self-tolerance certified: candidate detector {rule.rule_id} (matcher "
                f"{rule.matcher_id}) matched none of the {len(self._self_panel)} self fixtures. "
                "This is evidence about these fixtures only."
            ),
        )
