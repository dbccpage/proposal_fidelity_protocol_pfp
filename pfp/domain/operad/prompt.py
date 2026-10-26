"""Categorical Coloured Operad Prompt Domain Models & Facades.

Mathematical representation: Planar Coloured Operad over text spans
and semantic sorts (C, [i, j], O^+, \\circ_i, I, O^-, 1).

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any


class PromptColour(str, Enum):
    RawTextSpan = "RawTextSpan"
    Equation = "Equation"
    IsolatedVariable = "IsolatedVariable"
    SubstitutionStep = "SubstitutionStep"
    RationalValue = "RationalValue"
    InvariantWitness = "InvariantWitness"
    TargetResult = "TargetResult"

    @classmethod
    def from_str(cls, val: str) -> PromptColour:
        for member in cls:
            if member.value == val or member.name == val:
                return member
        return PromptColour(val)


@dataclass(frozen=True)
class LeafTextSpan:
    id: str
    colour: PromptColour
    content: str
    source_offsets: tuple[int, int]
    document_id: str | None = None
    digest_sha256: str | None = None

    def __post_init__(self) -> None:
        start, end = self.source_offsets
        if start > end:
            raise ValueError(
                f"Start offset {start} exceeds end offset {end} in span '{self.id}'"
            )

    def verify_against_document(self, doc_text: str) -> None:
        start, end = self.source_offsets
        if end > len(doc_text):
            raise ValueError(
                f"End offset {end} exceeds document length {len(doc_text)}"
            )
        slice_text = doc_text[start:end]
        if slice_text != self.content:
            raise ValueError(
                f"Span content mismatch for '{self.id}': expected {self.content!r}, got {slice_text!r}"
            )


@dataclass(frozen=True)
class PromptOperator:
    id: str
    source_colours: tuple[PromptColour, ...]
    target_colour: PromptColour
    arity: int
    description: str = ""

    def __post_init__(self) -> None:
        if len(self.source_colours) != self.arity:
            raise ValueError(
                f"Operator '{self.id}' arity mismatch: declared {self.arity}, got {len(self.source_colours)} source colours"
            )


@dataclass(frozen=True)
class NullTree:
    ideal_id: str
    reason: str
    target_colour: PromptColour

    @property
    def is_null(self) -> bool:
        return True

    @property
    def output_colour(self) -> PromptColour:
        return self.target_colour


@dataclass(frozen=True)
class OperadTreeNode:
    operator: PromptOperator
    children: tuple[OperadTreeNode | LeafTextSpan | NullTree, ...]

    @property
    def is_null(self) -> bool:
        return False

    @property
    def output_colour(self) -> PromptColour:
        return self.operator.target_colour

    def graft(
        self, slot: int, child: OperadTreeNode | LeafTextSpan | NullTree
    ) -> OperadTreeNode | NullTree:
        if isinstance(child, NullTree):
            return NullTree(
                ideal_id=child.ideal_id,
                reason=f"grafted child is null tree: {child.reason}",
                target_colour=child.target_colour,
            )
        if slot < 0 or slot >= self.operator.arity:
            raise IndexError(
                f"Slot {slot} out of bounds for operator '{self.operator.id}' (arity {self.operator.arity})"
            )

        expected_colour = self.operator.source_colours[slot]
        actual_colour = (
            child.colour if isinstance(child, LeafTextSpan) else child.output_colour
        )
        if expected_colour != actual_colour:
            raise TypeError(
                f"Boundary colour mismatch at slot {slot}: expected {expected_colour.value}, got {actual_colour.value}"
            )

        new_children = list(self.children)
        while len(new_children) < self.operator.arity:
            new_children.append(
                LeafTextSpan(
                    id=f"open_slot_{len(new_children)}",
                    colour=self.operator.source_colours[len(new_children)],
                    content="",
                    source_offsets=(0, 0),
                )
            )
        new_children[slot] = child
        return OperadTreeNode(operator=self.operator, children=tuple(new_children))


@dataclass(frozen=True)
class CongruenceIdeal:
    id: str
    target_colour: PromptColour
    assertion: str
    on_violation: str = "null_tree"

    def evaluate_rational_domain(self, val: Any) -> NullTree | None:
        if self.target_colour != PromptColour.RationalValue:
            return None
        if isinstance(val, bool):
            return NullTree(
                ideal_id=self.id,
                reason=f"boolean value disallowed in rational domain: {val!r}",
                target_colour=PromptColour.RationalValue,
            )
        if isinstance(val, (float, complex)):
            return NullTree(
                ideal_id=self.id,
                reason=f"float/decimal approximation disallowed: {val!r}",
                target_colour=PromptColour.RationalValue,
            )
        if isinstance(val, str):
            if "." in val or "e" in val.lower():
                return NullTree(
                    ideal_id=self.id,
                    reason=f"float/decimal string approximation disallowed: {val!r}",
                    target_colour=PromptColour.RationalValue,
                )
            try:
                Fraction(val)
            except Exception as e:
                return NullTree(
                    ideal_id=self.id,
                    reason=f"malformed rational representation {val!r}: {e}",
                    target_colour=PromptColour.RationalValue,
                )
            return None
        if not isinstance(val, (int, Fraction)):
            return NullTree(
                ideal_id=self.id,
                reason=f"unsupported rational value type: {type(val).__name__}",
                target_colour=PromptColour.RationalValue,
            )
        return None

    def evaluate_span_immutability(
        self, span: LeafTextSpan, source_doc: str
    ) -> NullTree | None:
        if self.target_colour != span.colour:
            return None
        try:
            span.verify_against_document(source_doc)
        except Exception as e:
            return NullTree(
                ideal_id=self.id,
                reason=f"leaf span token mutation detected: {e}",
                target_colour=span.colour,
            )
        return None

    def evaluate_witness_precedence(self, witness_is_valid: bool) -> NullTree | None:
        if self.target_colour not in (
            PromptColour.TargetResult,
            PromptColour.InvariantWitness,
        ):
            return None
        if not witness_is_valid:
            return NullTree(
                ideal_id=self.id,
                reason="composite evaluation emitted without verified substitution witness",
                target_colour=self.target_colour,
            )
        return None


@dataclass(frozen=True)
class AnnihilatorDecoy:
    id: str
    description: str
    decoy_candidate_bindings: Mapping[str, str]
    refutation_witness: Mapping[str, str]

    def evaluate(
        self,
        candidate_bindings: Mapping[str, str],
        provided_refutation: Mapping[str, str] | None,
    ) -> dict[str, Any]:
        matches_decoy = all(
            str(candidate_bindings.get(k, "")).strip() == str(v).strip()
            for k, v in self.decoy_candidate_bindings.items()
        )
        if not matches_decoy:
            return {"disposition": "Irrelevant"}

        if not provided_refutation:
            raise ValueError(
                f"DECOY_TRAP_UNREFUTED for '{self.id}': candidate matches decoy bindings {self.decoy_candidate_bindings} without refutation"
            )

        eval_str = provided_refutation.get("evaluation", "")
        if not eval_str or "!=" not in eval_str:
            raise ValueError(
                f"DECOY_TRAP_UNREFUTED for '{self.id}': refutation witness must demonstrate inequality (!=), got {eval_str!r}"
            )

        return {
            "disposition": "Neutralized",
            "decoy_id": self.id,
            "witness_evaluation": eval_str,
        }


@dataclass(frozen=True)
class ColouredOperadPrompt:
    schema_id: str
    family_name: str
    prompt_id: str
    colours: tuple[PromptColour, ...]
    operands: tuple[LeafTextSpan, ...]
    operators: tuple[PromptOperator, ...]
    congruence_ideals: tuple[CongruenceIdeal, ...] = ()
    annihilators: tuple[AnnihilatorDecoy, ...] = ()
    occurrences: tuple[Mapping[str, Any], ...] = ()
    composition_tree: Mapping[str, Any] | None = None
    source_document: Mapping[str, Any] | None = None

    def validate(self, source_text: str | None = None) -> bool:
        if self.schema_id not in (
            "omega.coda.categorical-operad-prompt.v2",
            "omega.coda.categorical-operad-prompt.v1",
        ):
            raise ValueError(f"Unsupported schema_id '{self.schema_id}'")

        declared = set(self.colours)
        for op in self.operands:
            if op.colour not in declared:
                raise ValueError(
                    f"Operand '{op.id}' uses undeclared colour '{op.colour}'"
                )
            if source_text is not None:
                op.verify_against_document(source_text)

        operator_ids = {opr.id for opr in self.operators}
        for opr in self.operators:
            for sc in opr.source_colours:
                if sc not in declared:
                    raise ValueError(
                        f"Operator '{opr.id}' uses undeclared input colour '{sc}'"
                    )
            if opr.target_colour not in declared:
                raise ValueError(
                    f"Operator '{opr.id}' uses undeclared target colour '{opr.target_colour}'"
                )

        for occ in self.occurrences:
            op_ref = occ.get("operator_ref")
            if op_ref is not None and op_ref not in operator_ids:
                raise ValueError(
                    f"Occurrence '{occ.get('occurrence_id')}' references undeclared operator '{op_ref}'"
                )

        return True
