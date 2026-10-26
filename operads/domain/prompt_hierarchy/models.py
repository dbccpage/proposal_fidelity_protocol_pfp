"""Prompt Hierarchy Domain Models.

Establishes the typed addressable URI taxonomy and binding models for attaching
OEWAS Anti-Ops and OEEIS Admitted Antibodies to individual prompts.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

# Canonical prompt URI regex: prompt://<domain>/<subdomain>/<task>/<stage>/<prompt_id>[/<subprompt_id>]
PROMPT_URI_PATTERN = re.compile(
    r"^prompt://(?P<domain>[a-z0-9_-]+)/(?P<subdomain>[a-z0-9_-]+)/(?P<task>[a-z0-9_-]+)/(?P<stage>[a-z0-9_-]+)/(?P<prompt_id>[A-Za-z0-9_-]+)(?:/(?P<subprompt_id>[A-Za-z0-9_-]+))?$"
)


@dataclass(frozen=True)
class PromptUri:
    """Strongly-typed, canonical prompt address URI."""

    raw_uri: str
    domain: str
    subdomain: str
    task: str
    stage: str
    prompt_id: str
    subprompt_id: str | None = None

    @classmethod
    def parse(cls, uri_str: str) -> "PromptUri":
        match = PROMPT_URI_PATTERN.match(uri_str)
        if not match:
            raise ValueError(
                f"Invalid prompt URI format: {uri_str!r}. "
                "Expected: prompt://<domain>/<subdomain>/<task>/<stage>/<prompt_id>[/<subprompt_id>]"
            )
        gd = match.groupdict()
        return cls(
            raw_uri=uri_str,
            domain=gd["domain"],
            subdomain=gd["subdomain"],
            task=gd["task"],
            stage=gd["stage"],
            prompt_id=gd["prompt_id"],
            subprompt_id=gd.get("subprompt_id"),
        )

    def ancestor_uris(self) -> tuple[str, ...]:
        """Return the sequence of hierarchical ancestor prefixes from root to leaf."""
        chain = [
            f"prompt://{self.domain}",
            f"prompt://{self.domain}/{self.subdomain}",
            f"prompt://{self.domain}/{self.subdomain}/{self.task}",
            f"prompt://{self.domain}/{self.subdomain}/{self.task}/{self.stage}",
            f"prompt://{self.domain}/{self.subdomain}/{self.task}/{self.stage}/{self.prompt_id}",
        ]
        if self.subprompt_id:
            chain.append(self.raw_uri)
        return tuple(chain)

    def __str__(self) -> str:
        return self.raw_uri


@dataclass(frozen=True)
class AntiOpBinding:
    """Binding reference to an OEWAS procedural Anti-Op / Anti-Skill."""

    op_id: str
    inspects_slot: str
    refusal_code: str
    description: str = ""


@dataclass(frozen=True)
class AntibodyBinding:
    """Binding reference to an OEEIS empirical failure detector (Antibody)."""

    antibody_id: str
    signal1_epitope: str
    signal2_required_danger: str
    minimum_status: str = "admitted"
    description: str = ""


@dataclass(frozen=True)
class ImmuneFenceBinding:
    """Opt-in retrieval scope and renderer limits for a prompt template."""

    template_id: str
    template_version: str
    domain: str
    tags: tuple[str, ...]
    stage: str
    prompt_field: str
    required_antibody_ids: tuple[str, ...] = ()
    max_antibodies: int = 3
    max_bytes: int = 2048

    def __post_init__(self) -> None:
        for name in ("template_id", "template_version", "domain", "stage", "prompt_field"):
            value = getattr(self, name)
            if type(value) is not str or not value.strip():
                raise ValueError(f"IMMUNE_BINDING_INVALID: {name}")
        for name in ("tags", "required_antibody_ids"):
            values = getattr(self, name)
            if not isinstance(values, (tuple, list)) or any(type(v) is not str or not v.strip() for v in values):
                raise ValueError(f"IMMUNE_BINDING_INVALID: {name}")
            if len(set(values)) != len(values):
                raise ValueError(f"IMMUNE_BINDING_DUPLICATE: {name}")
            object.__setattr__(self, name, tuple(values))
        if type(self.max_antibodies) is not int or not 1 <= self.max_antibodies <= 3:
            raise ValueError("IMMUNE_FENCE_LIMIT_INVALID")
        if type(self.max_bytes) is not int or not 33 <= self.max_bytes <= 2048:
            raise ValueError("IMMUNE_FENCE_LIMIT_INVALID")


from omega_engine_operads.domain.operad.colours import ADMITTED_FINITE_COLOURS


@dataclass(frozen=True)
class OperadPromptBinding:
    """Binds a prompt node to a coloured operad operation and degree-of-freedom locks.

    Eliminates degrees of freedom per prompt by enforcing:
    1. Typed source/target colours from ADMITTED_FINITE_COLOURS.
    2. Independent sub-channel pins (`required_slot_pins`) with zero free tuning parameters.
    3. Cross-slot canonical witness equality (`cross_slot_equality_groups`) across Paper, Code, and Proof.
    4. Boundary/counterexample falsifier slots (`required_boundary_witness_slots`) preventing scalar proxy substitution.
    """

    operation_id: str
    source_colours: tuple[str, ...]
    target_colour: str
    slot_to_colour: Mapping[str, str] = field(default_factory=dict)
    required_slot_pins: tuple[str, ...] = ()
    cross_slot_equality_groups: tuple[tuple[str, ...], ...] = ()
    required_boundary_witness_slots: tuple[str, ...] = ()
    equivariant: bool = False
    residual_effect: str = "contractive"

    def __post_init__(self) -> None:
        if type(self.operation_id) is not str or not self.operation_id.strip():
            raise ValueError("OPERAD_BINDING_INVALID: operation_id must be a non-empty string")
        object.__setattr__(self, "source_colours", tuple(str(c) for c in self.source_colours))
        for c in (*self.source_colours, self.target_colour):
            if c not in ADMITTED_FINITE_COLOURS:
                raise ValueError(f"OPERAD_BINDING_INVALID_COLOUR: {c!r} not in {ADMITTED_FINITE_COLOURS}")
        object.__setattr__(self, "required_slot_pins", tuple(str(s) for s in self.required_slot_pins))
        object.__setattr__(
            self,
            "cross_slot_equality_groups",
            tuple(tuple(str(s) for s in grp) for grp in self.cross_slot_equality_groups),
        )
        object.__setattr__(
            self,
            "required_boundary_witness_slots",
            tuple(str(s) for s in self.required_boundary_witness_slots),
        )

    @property
    def locked_constraint_count(self) -> int:
        """Total number of explicit degree-of-freedom locks enforced by this operad binding."""
        return (
            len(self.source_colours)
            + len(self.required_slot_pins)
            + len(self.cross_slot_equality_groups)
            + len(self.required_boundary_witness_slots)
        )


@dataclass(frozen=True)
class PromptTreeNode:
    """A node in the prompt hierarchy tree with attached negative-governance fences."""

    uri: PromptUri
    title: str
    description: str = ""
    anti_ops: tuple[AntiOpBinding, ...] = ()
    antibodies: tuple[AntibodyBinding, ...] = ()
    source_file: str | None = None
    authority_effect: str = "None"
    immune_fence: ImmuneFenceBinding | None = None
    operad_binding: OperadPromptBinding | None = None

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")


@dataclass(frozen=True)
class PromptGateReceipt:
    """Typed evaluation receipt recording prompt gate clearance or refusal."""

    prompt_uri: str
    status: str  # "PASS" or "REFUSED"
    anti_ops_evaluated: tuple[str, ...] = ()
    anti_ops_fired: tuple[str, ...] = ()
    antibodies_evaluated: tuple[str, ...] = ()
    antibodies_fired: tuple[str, ...] = ()
    operad_operation_id: str | None = None
    residual_degrees_of_freedom: int = 0
    refusal_code: str | None = None
    refusal_message: str | None = None
    authority_effect: str = "None"

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "omega.prompt_hierarchy.gate_receipt.v1",
            "prompt_uri": self.prompt_uri,
            "status": self.status,
            "anti_ops_evaluated": list(self.anti_ops_evaluated),
            "anti_ops_fired": list(self.anti_ops_fired),
            "antibodies_evaluated": list(self.antibodies_evaluated),
            "antibodies_fired": list(self.antibodies_fired),
            "operad_operation_id": self.operad_operation_id,
            "residual_degrees_of_freedom": self.residual_degrees_of_freedom,
            "refusal_code": self.refusal_code,
            "refusal_message": self.refusal_message,
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class DerivationMapOperadReport:
    """Summary receipt for a multi-prompt PFP derivation map collected into a ColouredOperad."""

    prompt_uris: tuple[str, ...]
    operation_ids: tuple[str, ...]
    composite_signature: str
    total_locked_constraints: int
    residual_degrees_of_freedom: int
    collected_antibody_ids: tuple[str, ...]
    collected_anti_op_ids: tuple[str, ...]
    status: str  # "PASS" or "REFUSED"
    refusal_code: str | None = None
    refusal_message: str | None = None
    authority_effect: str = "None"

