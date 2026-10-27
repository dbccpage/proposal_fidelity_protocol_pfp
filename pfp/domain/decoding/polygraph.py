"""Tarski 2-polygraph term rewriting, critical pairs, and confluent 2-cells.

Zero outward dependencies.
AuthorityEffect: None.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from pfp.domain.mssn_research.shared_kernel.result import Result, err, ok
from .errors import DecodingError, DecodingRefusalCode


@dataclass(frozen=True)
class RewriteStep:
    """A 1-cell reduction step in a 2-polygraph."""

    rule_name: str
    redex_loc: str
    source_term: str
    result_term: str

    def __post_init__(self) -> None:
        if type(self.rule_name) is not str or type(self.redex_loc) is not str:
            raise TypeError("Rule names and redex locations must be strings")
        if not self.rule_name:
            raise ValueError("rule_name cannot be empty")
        if type(self.source_term) is not str or type(self.result_term) is not str:
            raise TypeError("Terms must be strings")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, RewriteStep)
        return (
            self.rule_name == other.rule_name
            and self.redex_loc == other.redex_loc
            and self.source_term == other.source_term
            and self.result_term == other.result_term
        )

    def __hash__(self) -> int:
        return hash((type(self), self.rule_name, self.redex_loc, self.source_term, self.result_term))


@dataclass(frozen=True)
class CriticalPair:
    """A divergent critical peak in a term rewriting system: left <- apex -> right."""

    apex: str
    step_left: RewriteStep
    step_right: RewriteStep

    def __post_init__(self) -> None:
        if self.step_left.source_term != self.apex or self.step_right.source_term != self.apex:
            raise ValueError(f"Both critical pair rewrite steps must originate from apex '{self.apex}'")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, CriticalPair)
        return self.apex == other.apex and self.step_left == other.step_left and self.step_right == other.step_right

    def __hash__(self) -> int:
        return hash((type(self), self.apex, self.step_left, self.step_right))


@dataclass(frozen=True)
class Confluence2Cell:
    """A 2-cell filling a critical divergent peak with confluent reduction paths."""

    peak_apex: str
    target_left: str
    target_right: str
    left_path: tuple[RewriteStep, ...]
    right_path: tuple[RewriteStep, ...]
    join_term: str

    def __post_init__(self) -> None:
        if not isinstance(self.left_path, tuple):
            object.__setattr__(self, "left_path", tuple(self.left_path))
        if not isinstance(self.right_path, tuple):
            object.__setattr__(self, "right_path", tuple(self.right_path))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, Confluence2Cell)
        return (
            self.peak_apex == other.peak_apex
            and self.target_left == other.target_left
            and self.target_right == other.target_right
            and self.left_path == other.left_path
            and self.right_path == other.right_path
            and self.join_term == other.join_term
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.peak_apex,
            self.target_left,
            self.target_right,
            self.left_path,
            self.right_path,
            self.join_term,
        ))


@dataclass(frozen=True)
class TarskiPolygraph:
    """Check supplied joins against registered, location-bound ground steps.

    This finite registry does not supply variable substitution, match search or
    a theorem that the entire rewriting system is confluent.
    """

    rules: tuple[RewriteStep, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.rules, tuple):
            object.__setattr__(self, "rules", tuple(self.rules))
        for rule in self.rules:
            self._check_ground_step(rule)

    @staticmethod
    def _check_ground_step(step: RewriteStep) -> None:
        if type(step) is not RewriteStep or any(type(value) is not str for value in (
            step.rule_name, step.redex_loc, step.source_term, step.result_term,
        )) or not step.rule_name:
            raise DecodingError(
                "Ground steps require exact RewriteStep values and exact string fields",
                code=DecodingRefusalCode.REGISTERED_REWRITE_MISMATCH,
            )

    @staticmethod
    def check_continuity(path: Sequence[RewriteStep], start_term: str) -> str:
        """Verify that a path of rewrite steps forms a continuous reduction chain."""
        current = start_term
        for step in path:
            TarskiPolygraph._check_ground_step(step)
            if step.source_term != current:
                raise DecodingError(
                    f"Discontinuous rewrite step: expected source '{current}', got '{step.source_term}'",
                    code=DecodingRefusalCode.DISCONTINUOUS_REWRITE_CHAIN,
                )
            current = step.result_term
        return current

    def validate_confluence(self, cell: Confluence2Cell) -> bool:
        """Check continuity, joining endpoints and exact registered ground steps."""
        if type(cell) is not Confluence2Cell or any(type(value) is not str for value in (
            cell.peak_apex, cell.target_left, cell.target_right, cell.join_term,
        )):
            raise DecodingError(
                "Joining cells require exact Confluence2Cell values and exact string terms",
                code=DecodingRefusalCode.REGISTERED_REWRITE_MISMATCH,
            )
        for registered in self.rules:
            self._check_ground_step(registered)
        term_left = self.check_continuity(cell.left_path, cell.target_left)
        term_right = self.check_continuity(cell.right_path, cell.target_right)

        if term_left != cell.join_term or term_right != cell.join_term:
            raise DecodingError(
                f"Confluence join mismatch: left branch joins to '{term_left}', right branch joins to '{term_right}', expected '{cell.join_term}'",
                code=DecodingRefusalCode.DIVERGENT_JOIN_MISMATCH,
            )
        for step in (*cell.left_path, *cell.right_path):
            same_name = tuple(rule for rule in self.rules if rule.rule_name == step.rule_name)
            if not same_name:
                raise DecodingError(
                    f"Unregistered rewrite rule: '{step.rule_name}'",
                    code=DecodingRefusalCode.UNREGISTERED_REWRITE_RULE,
                )
            fields = (step.rule_name, step.redex_loc, step.source_term, step.result_term)
            if not any(fields == (rule.rule_name, rule.redex_loc, rule.source_term, rule.result_term)
                for rule in same_name):
                raise DecodingError(
                    f"Registered rule '{step.rule_name}' does not permit this ground step",
                    code=DecodingRefusalCode.REGISTERED_REWRITE_MISMATCH,
                )
        return True

    def validate_confluence_result(self, cell: Confluence2Cell) -> Result[bool, DecodingError]:
        """ROP Result envelope for confluence validation."""
        try:
            val = self.validate_confluence(cell)
            return ok(val)
        except DecodingError as exc:
            return err(exc)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, TarskiPolygraph)
        return self.rules == other.rules

    def __hash__(self) -> int:
        return hash((type(self), self.rules))


__all__ = [
    "Confluence2Cell",
    "CriticalPair",
    "RewriteStep",
    "TarskiPolygraph",
]
