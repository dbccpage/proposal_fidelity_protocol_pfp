"""PFP Base Model, Serialization Mixin, and Core Domain Enums.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict
from pydantic.json_schema import DEFAULT_REF_TEMPLATE, GenerateJsonSchema

from ..shared_kernel.yaml_strict import strict_yaml_load


class PfpBaseModel(BaseModel):
    """Base Pydantic model with strict defaults and lossless YAML helpers."""

    model_config = ConfigDict(
        extra="ignore",
        strict=False,
        validate_assignment=True,
    )

    @classmethod
    def from_yaml(cls, content: str):
        """Validate YAML text; use infrastructure.model_loading for files."""
        if not isinstance(content, str):
            raise TypeError("from_yaml requires YAML text; use load_yaml_model for a path")
        data = strict_yaml_load(content.lstrip("\ufeff"))
        if not isinstance(data, dict):
            raise ValueError(f"YAML payload for {cls.__name__} must be a mapping, got {type(data).__name__}")
        return cls.model_validate(data)

    def to_yaml(self) -> str:
        data = self.model_dump(mode="json", exclude_none=True)
        return yaml.dump(data, sort_keys=False, default_flow_style=False)


class Draft202012Schema(GenerateJsonSchema):
    """Emit the draft 2020-12 dialect marker pydantic otherwise omits."""

    def generate(self, schema: Any, mode: str = "validation") -> dict[str, Any]:
        json_schema = super().generate(schema, mode=mode)
        json_schema["$schema"] = self.schema_dialect
        return json_schema


class PfpDomainModel(PfpBaseModel):
    """Frozen pilot-document model. Unknown keys are rejected."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )

    @classmethod
    def model_json_schema(
        cls,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = Draft202012Schema,
        mode: Literal["validation", "serialization"] = "validation",
    ) -> dict[str, Any]:
        return super().model_json_schema(
            by_alias=by_alias,
            ref_template=ref_template,
            schema_generator=schema_generator,
            mode=mode,
        )

    def to_yaml(self) -> str:
        data = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True).lstrip("\ufeff")


def object_digest(obj: object) -> str:
    """sha256 of sorted-key compact UTF-8 JSON."""
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# =============================================================================
# PRIMITIVES & ENUMS
# =============================================================================

class PfpAuthorityEffect(str, Enum):
    NONE = "None"


AuthorityEffect = PfpAuthorityEffect


class TaskFamily(str, Enum):
    LINEAR_ALGEBRA = "linear_algebra"
    GRAPH_FACTS = "graph_facts"
    GRAPH_REPAIR = "graph_repair"
    REFUSAL = "refusal"
    COCHAIN_DEFECT = "cochain_defect"
    MAGMA_ASSOCIATIVITY = "magma_associativity"


class ExecutionMode(str, Enum):
    OFFLINE_FIXTURE = "offline_fixture"
    LIVE_MANUAL_DISPATCH = "live_manual_dispatch"
    LIVE_GATEWAY_DISPATCH = "live_gateway_dispatch"


class TrialStatus(str, Enum):
    NOT_RUN = "NOT_RUN"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUSED = "REFUSED"


class EvaluationStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    FALSE_CERTAINTY = "FALSE_CERTAINTY"
    MALFORMED = "MALFORMED"
    NOT_RUN = "NOT_RUN"
    REFUSED = "REFUSED"


class ConstraintType(str, Enum):
    PROJECT_OUT = "ProjectOut"
    RESTRAIN = "Restrain"
    ENFORCE = "Enforce"
    REJECT_MALFORMED_OR_FAKE_REFUSALS = "RejectMalformedOrFakeRefusals"


class Operatorizability(str, Enum):
    REPAIRABLE = "repairable"
    FATAL = "fatal"


class RuntimeAction(str, Enum):
    REPAIR = "repair"
    ABORT = "abort"
    REFUSE = "refuse"


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class TaskModeFidelity(str, Enum):
    LITERAL_EXTRACTION = "literal_extraction"
    FINITE_DEDUCTION = "finite_deduction"


class VariableIdentifierPermutation(str, Enum):
    CANONICAL = "canonical"
    PERMUTED = "permuted"


class FloatingPointRisk(str, Enum):
    EXACT_MODULAR = "exact_modular"
    FLOAT_APPROXIMATED = "float_approximated"


class ArmTemplate(str, Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"


class MissingPremise(str, Enum):
    ANSWERABLE = "answerable"
    UNANSWERABLE = "unanswerable"


class CohomologyDefectClass(str, Enum):
    NONE = "none"
    EXACT_BOUNDARY = "exact_boundary"
    CLOSED_NON_EXACT = "closed_non_exact"
    CURVATURE_DEFECT = "curvature_defect"


class MagmaAssociativityType(str, Enum):
    NONE = "none"
    ASSOCIATIVE_SEMIGROUP = "associative_semigroup"
    NON_ASSOCIATIVE_MAGMA = "non_associative_magma"


class CheckerId(str, Enum):
    EXACT_LINALG = "PFP-01-EXACT-LINALG"
    EXACT_PRIMES = "PFP-02-EXACT-PRIMES"
    EXACT_FOL_DEDUCTION = "PFP-03-EXACT-FOL-DEDUCTION"
    EXACT_EPISTEMIC_REFUSAL = "PFP-04-EXACT-EPISTEMIC-REFUSAL"
    EXACT_2X2_DETERMINANT = "PFP-05-EXACT-2X2-DETERMINANT"
    GRAPH_FACTS = "PFP-02-GRAPH-FACTS"
    GRAPH_REPAIR = "PFP-03-GRAPH-REPAIR"
    TYPED_REFUSAL = "PFP-14-TYPED-REFUSAL"
    COCHAIN_DEFECT = "PFP-52-COCHAIN-DEFECT"
    MAGMA_ASSOC = "PFP-55-MAGMA-ASSOC"


class StructureDeltaMetric(str, Enum):
    EXACT_RATIONAL_DELTA = "exact_rational_delta"
    GATE_BOOLEAN = "gate_boolean"
    COCHAIN_NORM = "cochain_norm"
    RANK_CHANGE = "rank_change"


class RepresentationRewrite(str, Enum):
    RAW_PROSE = "raw_prose"
    STRUCTURED_SPANS = "structured_spans"
    MSS_BOUNDARY_V1 = "mss_boundary_v1"
    SN_WIRE_V2 = "sn_wire_v2"
    EBNF_WIRE_V1 = "ebnf_wire_v1"
    HIEROGLYPHIC_GLYPHS = "hieroglyphic_glyphs"


class ModelClass(str, Enum):
    CLASS_8B = "8B"
    CLASS_70B = "70B"
    CLASS_500B_PLUS = "500B_plus"
