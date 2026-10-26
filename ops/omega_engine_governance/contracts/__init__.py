"""Canonical, lightweight entry point for Omega governance contracts.

The root-used kinds, binding records, and no-authority guard are standalone
standard-library definitions.  Importing or resolving those symbols does not
traverse ``omega_engine`` or optional scientific/document runtimes.  The small
remaining lazy surface points only at independently lightweight canonical
modules.  The deleted ``omega_contracts`` namespace is never restored.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from importlib import import_module
from typing import Any, ClassVar, Protocol, runtime_checkable


class Refusal(Exception):
    """A local contract refusal carrying a stable code and message."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class ContractTrait:
    """A named invariant predicate used by the lightweight facade."""

    def __init__(self, name: str, validator: Callable[[Any], object] | object) -> None:
        self.name = name
        self.validator = validator

    def validate(self, data: Any) -> bool:
        if callable(self.validator):
            return bool(self.validator(data))
        return True


class SchemaValidator:
    """Fail closed when a required top-level field is absent."""

    def __init__(self, required_fields: Iterable[str]) -> None:
        self.required_fields = tuple(required_fields)

    def validate_schema(self, document: Mapping[str, Any]) -> bool | Refusal:
        for required_field in self.required_fields:
            if required_field not in document:
                return Refusal(
                    "SchemaValidationError",
                    f"Missing required field {required_field!r}",
                )
        return True


LAYER_OBLIGATIONS: Mapping[int, tuple[ContractTrait, ...]] = {
    0: (ContractTrait("grammar_match", lambda _: True),),
    1: (ContractTrait("local_replay_valid", lambda _: True),),
    2: (ContractTrait("boundary_signature_valid", lambda _: True),),
}


@dataclass(frozen=True, slots=True)
class SchemaHash:
    """Exactly one SHA-256-sized schema identity."""

    hash_bytes: bytes

    def __post_init__(self) -> None:
        if len(self.hash_bytes) != 32:
            raise ValueError("SchemaHash must be exactly 32 bytes")

    def __str__(self) -> str:
        return self.hash_bytes.hex()

    def __repr__(self) -> str:
        return f"SchemaHash({self.hash_bytes.hex()})"


class ContractCategory(Enum):
    Constitution = "Constitution"
    State = "State"
    Evidence = "Evidence"
    Obstruction = "Obstruction"
    Action = "Action"
    OperatorCandidate = "OperatorCandidate"
    OperatorAlgebra = "OperatorAlgebra"
    Governance = "Governance"
    Execution = "Execution"
    Representation = "Representation"
    Product = "Product"
    Lifts = "Lifts"
    Math = "Math"


class ComponentRole(Enum):
    BaseType = "BaseType"
    Carrier = "Carrier"
    Packet = "Packet"
    CheckedPacket = "CheckedPacket"
    Certificate = "Certificate"
    CertificateKernel = "CertificateKernel"
    CertificateStore = "CertificateStore"
    CertificateApiInterface = "CertificateApiInterface"
    Witness = "Witness"
    Diagnostic = "Diagnostic"
    HealthModel = "HealthModel"
    Measurement = "Measurement"
    Observable = "Observable"
    Evaluator = "Evaluator"
    Validator = "Validator"
    Terminalizer = "Terminalizer"
    TerminalMapper = "TerminalMapper"
    Engine = "Engine"
    Kernel = "Kernel"
    Pipeline = "Pipeline"
    Runtime = "Runtime"
    Policy = "Policy"
    Search = "Search"
    Solver = "Solver"
    Replay = "Replay"
    Lift = "Lift"
    LiftLicense = "LiftLicense"
    LlmAdapter = "LlmAdapter"
    WebsiteApi = "WebsiteApi"
    SymbolGame = "SymbolGame"
    Packetization = "Packetization"
    StructureSweep = "StructureSweep"
    ProductKernelIntake = "ProductKernelIntake"
    FixedLayerOperatorAlgebra = "FixedLayerOperatorAlgebra"
    DeclaredActionCandidate = "DeclaredActionCandidate"
    RepresentationBoundary = "RepresentationBoundary"
    IntakeConstructor = "IntakeConstructor"
    ProposalGenerator = "ProposalGenerator"
    Trace = "Trace"
    AnalysisUnit = "AnalysisUnit"
    Boundary = "Boundary"
    AuthInterface = "AuthInterface"
    MathObject = "MathObject"
    MathComputation = "MathComputation"
    PublicVerifyService = "PublicVerifyService"
    SearchKernel = "SearchKernel"
    SolverKernel = "SolverKernel"
    CounterfeitDetector = "CounterfeitDetector"
    Constitution = "Constitution"


class AuthorityEffect(Enum):
    None_ = "none"
    EvidenceOnly = "evidence_only"
    FactOnly = "fact_only"
    RequiresEvaluator = "requires_evaluator"
    RequestsDecision = "requests_decision"
    AuthorizesTransition = "authorizes_transition"
    StateTransition = "state_transition"

    def is_execution(self) -> bool:
        return self is AuthorityEffect.StateTransition

    def is_license(self) -> bool:
        return self is AuthorityEffect.AuthorizesTransition

    def is_decision(self) -> bool:
        return self in {
            AuthorityEffect.RequiresEvaluator,
            AuthorityEffect.RequestsDecision,
        }

    def is_evidence_layer(self) -> bool:
        return self in {
            AuthorityEffect.None_,
            AuthorityEffect.EvidenceOnly,
            AuthorityEffect.FactOnly,
        }

    def is_certified(self) -> bool:
        return self is not AuthorityEffect.None_

    def is_none(self) -> bool:
        return self is AuthorityEffect.None_


class ContractStatus(Enum):
    Canonical = "Canonical"
    Staged = "Staged"
    Archived = "Archived"
    Deprecated = "Deprecated"


class LawBinding:
    """Required or forbidden law binding with the established root semantics."""

    def __init__(self, value: Any | None = None) -> None:
        self.value = value

    def is_required(self) -> bool:
        return self.value is not None

    def is_forbidden(self) -> bool:
        return self.value is None

    @classmethod
    def required(cls, value: Any) -> LawBinding:
        return cls(value)

    @classmethod
    def forbidden(cls) -> LawBinding:
        return cls(None)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, LawBinding) and self.value == other.value

    def __repr__(self) -> str:
        return f"Required({self.value!r})" if self.is_required() else "Forbidden"


class TypeBinding:
    """Concrete, not-applicable, or forbidden Python type identity."""

    def __init__(self, concrete_type: type[Any] | None = None, name: str | None = None):
        self.concrete_type = concrete_type
        self.name = name

    def is_concrete(self) -> bool:
        return self.concrete_type is not None

    def is_not_applicable(self) -> bool:
        return self.concrete_type is None and self.name == "NotApplicable"

    def is_forbidden(self) -> bool:
        return self.concrete_type is None and self.name == "Forbidden"

    @classmethod
    def concrete(cls, concrete_type: type[Any], name: str) -> TypeBinding:
        return cls(concrete_type, name)

    @classmethod
    def not_applicable(cls) -> TypeBinding:
        return cls(None, "NotApplicable")

    @classmethod
    def forbidden(cls) -> TypeBinding:
        return cls(None, "Forbidden")

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TypeBinding)
            and self.concrete_type == other.concrete_type
            and self.name == other.name
        )

    def __repr__(self) -> str:
        if self.concrete_type is not None:
            return f"Concrete({self.concrete_type.__name__}, {self.name!r})"
        return str(self.name)


@dataclass(slots=True)
class ContractDescriptor:
    id: str
    category: ContractCategory
    role: ComponentRole
    status: ContractStatus
    authority_effect: AuthorityEffect
    phi_law: LawBinding = field(default_factory=LawBinding.forbidden)
    structure_law: LawBinding = field(default_factory=LawBinding.forbidden)
    effect_law: LawBinding = field(default_factory=LawBinding.forbidden)
    input_type: TypeBinding = field(default_factory=TypeBinding.not_applicable)
    output_type: TypeBinding = field(default_factory=TypeBinding.not_applicable)
    subject_type: TypeBinding = field(default_factory=TypeBinding.not_applicable)
    runtime_state_type: TypeBinding = field(default_factory=TypeBinding.not_applicable)
    evidence_requirements: list[str] = field(default_factory=list)
    forbidden_authority: list[AuthorityEffect] = field(default_factory=list)
    schema_hash: SchemaHash = field(default_factory=lambda: SchemaHash(bytes(32)))


class BoundContract:
    DESCRIPTOR: ClassVar[ContractDescriptor | None] = None
    Input: ClassVar[type[Any]] = type(None)
    Output: ClassVar[type[Any]] = type(None)
    Subject: ClassVar[type[Any]] = type(None)
    RuntimeState: ClassVar[type[Any]] = type(None)


class ContractAuditError(Exception):
    """A mismatch between a descriptor and its bound Python type surface."""


def _ensure_type_eq(
    descriptor: ContractDescriptor,
    field_name: str,
    expected: TypeBinding,
    actual_type: type[Any],
) -> None:
    mismatch = (
        (expected.is_forbidden() or expected.is_not_applicable())
        and actual_type is not type(None)
    ) or (expected.is_concrete() and actual_type is not expected.concrete_type)
    if mismatch:
        raise ContractAuditError(
            f"CONTRACT VIOLATION [{descriptor.id}] {field_name} type identity "
            f"mismatch, schema_hash={descriptor.schema_hash}"
        )


def audit_contract(contract_cls: type[BoundContract]) -> ContractDescriptor:
    """Return the descriptor only after all type and authority fences pass."""

    descriptor = contract_cls.DESCRIPTOR
    if descriptor is None:
        raise ContractAuditError("Contract has no DESCRIPTOR defined")
    _ensure_type_eq(descriptor, "input_type", descriptor.input_type, contract_cls.Input)
    _ensure_type_eq(
        descriptor, "output_type", descriptor.output_type, contract_cls.Output
    )
    _ensure_type_eq(
        descriptor, "subject_type", descriptor.subject_type, contract_cls.Subject
    )
    _ensure_type_eq(
        descriptor,
        "runtime_state_type",
        descriptor.runtime_state_type,
        contract_cls.RuntimeState,
    )
    if descriptor.authority_effect in descriptor.forbidden_authority:
        raise ContractAuditError(
            f"CONTRACT VIOLATION [{descriptor.id}] forbidden authority effect "
            f"{descriptor.authority_effect}"
        )
    return descriptor


@runtime_checkable
class AuthorityTagged(Protocol):
    def authority_effect(self) -> Any: ...

    def artifact_id(self) -> str: ...


@dataclass(slots=True)
class AuthorityViolation(Exception):
    artifact_id: str
    artifact_name: str
    effect: Any

    def __str__(self) -> str:
        return (
            f"AuthorityViolation: artifact {self.artifact_id} ({self.artifact_name}) "
            f"has certified/unauthorized authority effect: {self.effect}"
        )


def _is_none_effect(effect: Any) -> bool:
    if effect is None:
        return True
    if isinstance(effect, str):
        return effect in {"none", "None", "None_"}
    return (
        getattr(effect, "name", None) in {"None", "None_"}
        or getattr(effect, "value", None) == "none"
    )


class NoAuthorityGuard:
    @staticmethod
    def validate(artifact: AuthorityTagged, artifact_name: str) -> None:
        effect = artifact.authority_effect()
        if _is_none_effect(effect):
            return
        raise AuthorityViolation(
            artifact_id=artifact.artifact_id(),
            artifact_name=artifact_name,
            effect=effect,
        )


# These two modules use only Pydantic and standard-library dependencies.  They
# remain lazy so importing the facade itself stays standard-library-only.
_LAZY_EXPORTS: dict[str, str] = {
    "CochainComplexData": "omega_engine_governance.contracts.ddc_packets",
    "DDAPacketTypeError": "omega_engine_governance.contracts.dda_packets",
    "DDATapeDFA": "omega_engine_governance.contracts.dda_packets",
    "DDATapeValidationError": "omega_engine_governance.contracts.dda_packets",
    "DDCPacketTypeError": "omega_engine_governance.contracts.ddc_packets",
    "DDCTapeDFA": "omega_engine_governance.contracts.ddc_packets",
    "DDCTapeValidationError": "omega_engine_governance.contracts.ddc_packets",
    "FidelityPacket": "omega_engine_governance.contracts.ddc_packets",
    "ObstructionDescentPacket": "omega_engine_governance.contracts.ddc_packets",
    "ProposalEnvelope": "omega_engine_governance.contracts.ddc_packets",
    "assert_packet_type_separation": "omega_engine_governance.contracts.ddc_packets",
    "require_proposal_envelope": "omega_engine_governance.contracts.ddc_packets",
    "validate_python_contract_mirror": "omega_engine_governance.contracts.validate",
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(target), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_EXPORTS))


__all__ = tuple(
    sorted(
        {
            "AuthorityEffect",
            "AuthorityTagged",
            "AuthorityViolation",
            "BoundContract",
            "ComponentRole",
            "ContractAuditError",
            "ContractCategory",
            "ContractDescriptor",
            "ContractStatus",
            "ContractTrait",
            "LAYER_OBLIGATIONS",
            "LawBinding",
            "NoAuthorityGuard",
            "Refusal",
            "SchemaHash",
            "SchemaValidator",
            "TypeBinding",
            "audit_contract",
            *_LAZY_EXPORTS,
        }
    )
)
