"""Prompt families: a prompt is a relation to a reader, and a problem to repair.

Pure domain types (no I/O, no providers). Everything here is a typed record:

* ``ReaderV1``      who read the prompt: model, router, seat, tier, sampling, config.
* ``PromptNodeV1``  one prompt as read by one reader; the same bytes read by a
                    different reader are a different node.
* ``CallRecordV1``  one model call, including failed ones (failures are data).
* ``RepairStepV1``  input node -> output node with a DDC letter, residual before
                    and after, the call ids, and a fitness vector.
* ``TerminalV1``    exactly one of Repaired / BudgetExhausted / TypedResidual.
* ``PromptFamilyV1`` the DAG, checked by ``validate_family``.

Honesty rules enforced by ``validate_family``:

* Unknown stays unknown (``None``); nothing is filled in on a model's behalf.
* A domain label is ``proposed`` until a host check receipt confirms it.
* A checker verdict (ACCEPT/REJECT) needs a checker id, and that checker may not
  be one of the readers that proposed the step (no circular fitness).
* ``Repaired`` needs an external ACCEPT and an ``Exact`` final residual.

Nothing here supports a claim about model quality. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

from .ddc_program import DdcProgramBinding as DdcProgramBinding
from .native import NativeOperationPort, invoke
from .native import value as native_value

DDC_LETTERS = ("E", "R", "C", "I", "Λ", "D", "M", "T")
RESIDUAL_COLOURS = ("Open", "Closed", "Exact")
RELATIONS = ("root", "contains", "repaired_from")
VERDICTS = ("ACCEPT", "REJECT", "NOT_MEASURED")
TERMINAL_KINDS = ("Repaired", "BudgetExhausted", "TypedResidual")
LABEL_STATUS = ("proposed", "checked")
FAILURE_OUTCOMES_NOT_REPLIES = frozenset({"OK", "MALFORMED"})


def canonical_digest(obj: Any) -> str:
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def text_digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _refuse(code: str, message: str) -> Err[Refusal]:
    return Err(Refusal(code, message, "omega_engine_woland.domain.prompt_family"))


@dataclass(frozen=True)
class ReaderV1:
    """The reader a prompt is relative to. ``None`` means unknown, never a guess."""

    model: str
    router: str
    seat_id: str
    tier: str
    config_digest: str
    temperature: str | None = None  # decimal string actually sent; None = provider default
    params_billion: int | None = None
    open_weights: bool | None = None

    def digest(self) -> str:
        return canonical_digest(self.__dict__)


@dataclass(frozen=True)
class ShapeV1:
    """Syntactic shape only. It says nothing about meaning."""

    byte_bucket: int
    line_bucket: int
    fence_count: int
    question_count: int

    @staticmethod
    def from_text(text: str, *, native_support: NativeOperationPort) -> "ShapeV1":
        return ShapeV1(**native_value(native_support, "family_shape", text=text))

    def digest(self) -> str:
        return canonical_digest(self.__dict__)


@dataclass(frozen=True)
class DomainLabelV1:
    label: str
    proposer_reader: str
    status: Literal["proposed", "checked"] = "proposed"
    check_receipt: str | None = None


@dataclass(frozen=True)
class PromptNodeV1:
    prompt_digest: str
    relation: str
    shape: ShapeV1 | None
    parent_id: str | None = None
    reader_digest: str | None = None
    domain_labels: tuple[DomainLabelV1, ...] = ()

    @property
    def node_id(self) -> str:
        return canonical_digest(
            [self.prompt_digest, self.relation, self.parent_id, self.reader_digest]
        )


@dataclass(frozen=True)
class CallRecordV1:
    bout_id: str
    request_digest: str
    reader_digest: str
    leg_index: int
    outcome: str
    cost_microusd: int
    cost_source: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    max_tokens: int | None = None
    finish_reason: str | None = None
    ddc_letter: str | None = None
    residual_colour: str | None = None
    reply_digest: str | None = None

    @property
    def call_id(self) -> str:
        return canonical_digest(
            [self.bout_id, self.request_digest, self.reader_digest, self.leg_index, self.outcome]
        )

    @property
    def truncated(self) -> bool | None:
        return None if self.finish_reason is None else self.finish_reason == "length"

    @property
    def defect(self) -> str | None:
        return None if self.outcome == "OK" else self.outcome


@dataclass(frozen=True)
class FitnessV1:
    cost_microusd: int
    input_tokens: int
    output_tokens: int
    checker_verdict: str = "NOT_MEASURED"
    checker_id: str | None = None
    obstruction_removed: bool | None = None


@dataclass(frozen=True)
class RepairStepV1:
    input_node_id: str
    output_node_id: str
    ddc_letter: str | None
    residual_before: str | None
    residual_after: str | None
    call_ids: tuple[str, ...]
    fitness: FitnessV1


@dataclass(frozen=True)
class TerminalV1:
    kind: str
    detail: str


@dataclass(frozen=True)
class PromptFamilyV1:
    readers: tuple[ReaderV1, ...]
    nodes: tuple[PromptNodeV1, ...]
    calls: tuple[CallRecordV1, ...]
    steps: tuple[RepairStepV1, ...]
    terminal: TerminalV1 | None


def validate_family(family: PromptFamilyV1, *, native_support: NativeOperationPort) -> Result[PromptFamilyV1, Refusal]:
    result = invoke(native_support, "family_validate", family_json=json.dumps(asdict(family), ensure_ascii=False))
    if isinstance(result, Err):
        return result
    return Ok(family)
