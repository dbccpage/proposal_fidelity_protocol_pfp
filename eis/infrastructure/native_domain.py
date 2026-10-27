"""DTO adapters for native exact consensus and detector lifecycle operations."""

from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction
from typing import Any, Mapping, Sequence

from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from operations.domain.rop.result import Err

from ..domain.allostery import DEFAULT_PARAMETERS, AllostericDecision
from ..domain.external_admission import (
    AdmissionError,
    AntibodyObservationV1,
    ExternalAdmissionRequestV1,
    FixturePolarityMapV1,
    FixtureValidationResult,
    HumanAntiSkillAdmissionDecisionV1,
    OperationalBindingV1,
    ReplayResult,
)
from ..domain.guard_activation import (
    REFUSAL_CODES,
    ActivationRefusal,
    DangerSignalReceiptV1,
    DetectorHitRefV1,
    GuardActivationReceiptV1,
)
from ..domain.provisional_promotion import PromotionResult, RawObservationV1, SupportResult
from ..domain.value_objects import AllosteryRefusal, DetectorRule, HillParameters


class NativePolicyUnavailable(RuntimeError):
    """Typed operational refusal when the native host cannot serve a policy."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _invoke(action: str, payload: Mapping[str, Any]) -> Any:
    reply = RustSymbolGameHost().invoke_runtime(action, payload)
    if isinstance(reply, Err):
        raise NativePolicyUnavailable(reply.error.code, reply.error.message)
    if not reply.value["success"]:
        raise NativePolicyUnavailable(
            "NATIVE_POLICY_EXECUTION_FAILED", str(reply.value["error"])
        )
    wire = reply.value["result"]
    if wire["refusal"] is not None:
        _raise_native_refusal(action, wire["refusal"])
    return wire["outcome"]


def _raise_native_refusal(action: str, refusal: Mapping[str, str]) -> None:
    code = refusal["code"]
    message = refusal["message"]
    detail = message.removeprefix(f"{code}: ")
    if action == "immune_clonal":
        raise ValueError(detail)
    if action == "immune_admission":
        _raise_admission_refusal(code, message, detail)
    if action == "immune_activation":
        _raise_activation_refusal(code, detail)
    raise AllosteryRefusal(code, detail)


def _raise_admission_refusal(code: str, message: str, detail: str) -> None:
    if code in {
        "PROPAGATED_REFERENCE_CANNOT_BE_OBSERVATION",
        "DECISION_BINDING_MISMATCH",
    }:
        raise ValueError(message)
    if code == "FIXTURE_POLARITY_UNDECLARED":
        raise LookupError(message)
    if code == "EIS_INDEX_ERROR":
        raise IndexError(detail)
    if code == "EIS_TYPE_ERROR":
        raise TypeError(detail)
    raise AdmissionError(code, detail)


def _raise_activation_refusal(code: str, detail: str) -> None:
    if code in REFUSAL_CODES:
        raise ActivationRefusal(code, detail)
    if code == "EIS_TYPE_ERROR":
        raise TypeError(detail)
    raise ValueError(detail)


class NativeAllostericConsensusGate:
    """Rust owns exact aggregation, threshold comparison and minimum quorum."""

    def __init__(
        self,
        parameters: HillParameters | None = None,
        activation_threshold: Fraction = Fraction(1, 2),
        per_sensor_cap: Fraction | None = Fraction(1),
    ) -> None:
        self.parameters = parameters if parameters is not None else DEFAULT_PARAMETERS
        self.activation_threshold = activation_threshold
        self.per_sensor_cap = per_sensor_cap
        self.quorum_size = self._evaluate({})["quorum_size"]

    def _evaluate(self, signals: Mapping[str, object]) -> dict[str, Any]:
        def wire(value: object) -> object:
            return str(value) if type(value) is Fraction else value

        return _invoke(
            "immune_allostery",
            {
                "parameters": {
                    "hill_coefficient": self.parameters.hill_coefficient,
                    "half_maximal_constant": wire(self.parameters.half_maximal_constant),
                },
                "activation_threshold": wire(self.activation_threshold),
                "per_sensor_cap": wire(self.per_sensor_cap),
                "sensor_signals": {key: wire(value) for key, value in signals.items()},
            },
        )

    def evaluate_quorum(self, sensor_signals: Mapping[str, object]) -> AllostericDecision:
        outcome = self._evaluate(sensor_signals)
        return AllostericDecision(
            is_activated=outcome["is_activated"],
            hill_value=Fraction(outcome["hill_value"]),
            aggregate_signal=Fraction(outcome["aggregate_signal"]),
            threshold=Fraction(outcome["threshold"]),
            parameters=self.parameters,
            rationale=outcome["rationale"],
            positive_sensors=outcome["positive_sensors"],
            quorum_size=outcome["quorum_size"],
            per_sensor_cap=None
            if outcome["per_sensor_cap"] is None
            else Fraction(outcome["per_sensor_cap"]),
        )


class NativeClonalSelectionEngine:
    @staticmethod
    def _execute(operation: str, rule: DetectorRule, **kwargs: Any) -> DetectorRule:
        wire = _invoke("immune_clonal", {"operation": operation, "rule": asdict(rule), **kwargs})
        return DetectorRule(**wire)

    @classmethod
    def mutate_rule(
        cls, parent_rule: DetectorRule, mutation_variant: str, new_rule_id: str
    ) -> DetectorRule:
        return cls._execute(
            "mutate", parent_rule, mutation_variant=mutation_variant, new_rule_id=new_rule_id
        )

    @classmethod
    def stimulate(cls, rule: DetectorRule, affinity_boost: Any = 1) -> DetectorRule:
        return cls._execute("stimulate", rule, affinity_boost=affinity_boost)

    @classmethod
    def apply_decay(cls, rule: DetectorRule) -> DetectorRule:
        return cls._execute("apply_decay", rule)


def native_admission(operation: str, **payload: Any) -> Any:
    """Marshal external review and observation-support requests to Rust."""
    return _invoke("immune_admission", {"operation": operation, **payload})


def native_activation(**payload: Any) -> Any:
    """Evaluate the receipt-bound four-conjunct law in Rust."""
    return _invoke("immune_activation", payload)


class NativeExternalAdmissionPolicy:
    """Native outer adapter for the domain's external-admission policy port."""

    def distinct_observations(
        self, observations: tuple[AntibodyObservationV1, ...]
    ) -> tuple[str, ...]:
        return tuple(
            native_admission(
                "distinct", observations=[asdict(item) for item in observations]
            )
        )

    def is_promotable(
        self,
        request: ExternalAdmissionRequestV1,
        observations: tuple[AntibodyObservationV1, ...],
        *,
        required_distinct: int,
    ) -> bool:
        return native_admission(
            "promotable",
            required_distinct=required_distinct,
            observations=[asdict(item) for item in observations],
        )

    def verify_replay(
        self,
        candidate_id: str,
        use_legacy_verifier: bool,
        registered_candidates: frozenset[str],
    ) -> ReplayResult:
        wire = native_admission(
            "replay",
            candidate_id=candidate_id,
            use_legacy_verifier=use_legacy_verifier,
            registered_candidates=sorted(registered_candidates),
        )
        return ReplayResult(**wire)

    def apply_human_admission(
        self,
        decision: HumanAntiSkillAdmissionDecisionV1,
        target_rule_bytes: bytes,
    ) -> dict[str, str]:
        return native_admission(
            "human_admit",
            decision=asdict(decision),
            target_rule_bytes_hex=target_rule_bytes.hex(),
        )

    def resolve_polarity(
        self,
        producer: str,
        schema_version: str,
        registry: tuple[FixturePolarityMapV1, ...],
    ) -> FixturePolarityMapV1:
        wire = native_admission(
            "resolve_polarity",
            producer=producer,
            schema_version=schema_version,
            registry=[asdict(item) for item in registry],
        )
        return FixturePolarityMapV1(**wire)

    def validate_binding(
        self,
        binding: OperationalBindingV1,
        detector_matches: list[bool],
    ) -> FixtureValidationResult:
        wire = native_admission(
            "validate_binding", matches=detector_matches, custody=binding.custody
        )
        wire.pop("custody")
        return FixtureValidationResult(**wire)

    def decide_custody(self, evidence: Mapping[str, Any]) -> str:
        return native_admission("custody", evidence=dict(evidence))


class NativeGuardActivationPolicy:
    """Native outer adapter for the learned-guard activation policy port."""

    def evaluate_activation(
        self,
        profile_digest: str,
        hit: DetectorHitRefV1 | None,
        danger: DangerSignalReceiptV1 | None,
        *,
        externally_admitted: bool,
        suspended: bool,
        disposition: str,
    ) -> GuardActivationReceiptV1:
        wire = native_activation(
            profile_digest=profile_digest,
            hit=None if hit is None else asdict(hit),
            danger=None if danger is None else asdict(danger),
            externally_admitted=externally_admitted,
            suspended=suspended,
            disposition=disposition,
        )
        return GuardActivationReceiptV1(**wire)


class NativeProvisionalPromotionPolicy:
    """Native outer adapter for exact observation support and promotion policy."""

    def promote(
        self,
        candidate_id: str,
        support_count: int | str,
        diagnostic_scope: list[str],
    ) -> PromotionResult:
        wire = native_admission(
            "promote",
            candidate_id=candidate_id,
            support_count=support_count,
            diagnostic_scope=diagnostic_scope,
        )
        return PromotionResult(**wire)

    def register_observation(self, observation: RawObservationV1) -> None:
        native_admission("support", observations=[asdict(observation)])

    def compute_support(self, observations: Sequence[RawObservationV1]) -> SupportResult:
        wire = native_admission(
            "support", observations=[asdict(observation) for observation in observations]
        )
        return SupportResult(**wire)
