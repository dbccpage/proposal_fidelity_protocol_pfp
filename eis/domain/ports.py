"""Domain ports and protocols for the Epistemic Immune System (OEEIS).

Defines inward-facing interfaces with zero outward infrastructure coupling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Protocol, Sequence

from .value_objects import (
    DangerDecision,
    DetectorRule,
    Signal1Match,
    Signal2Danger,
)

if TYPE_CHECKING:
    from .external_admission import (
        AntibodyObservationV1,
        ExternalAdmissionRequestV1,
        FixturePolarityMapV1,
        FixtureValidationResult,
        HumanAntiSkillAdmissionDecisionV1,
        OperationalBindingV1,
        ReplayResult,
    )
    from .guard_activation import (
        DangerSignalReceiptV1,
        DetectorHitRefV1,
        GuardActivationReceiptV1,
    )
    from .provisional_promotion import PromotionResult, RawObservationV1, SupportResult

MATCHER_BINDING_CODES = frozenset(
    {"RULE_MATCHER_MISMATCH", "UNKNOWN_DETECTOR_CODE", "THYMUS_MATCHER_MISMATCH"}
)


class MatcherBindingRefusal(ValueError):
    """A rule handed to a matcher it is not bound to, or naming a code it lacks."""

    def __init__(self, code: str, detail: str) -> None:
        if code not in MATCHER_BINDING_CODES:
            raise ValueError(f"unknown matcher binding code: {code}")
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def bound_rules(
    matcher_id: str, rules: Sequence[DetectorRule]
) -> tuple[DetectorRule, ...]:
    """The active rules, after refusing any rule bound to a different matcher."""
    for rule in rules:
        if rule.matcher_id != matcher_id:
            raise MatcherBindingRefusal(
                "RULE_MATCHER_MISMATCH",
                f"rule {rule.rule_id} is bound to {rule.matcher_id!r}, not {matcher_id!r}",
            )
    return tuple(rule for rule in rules if rule.is_active is True)


class AntigenMatcher(Protocol):
    """Port for scanning content to detect Signal 1 epitope patterns.

    `matcher_id` is the id rules bind to (`DetectorRule.matcher_id`).
    `detector_predicates` names the host danger kinds this matcher itself
    evaluates, so a Signal 2 of the same kind can be refused as the same
    predicate counted twice. `reports_content_offsets` says whether each
    match's offset and matched text locate it in the content, so that a match
    overlapping Signal 2's evidence spans can be refused.
    """

    matcher_id: str
    detector_predicates: frozenset[str]
    reports_content_offsets: bool

    def match_antigen(self, content: str, rules: Sequence[DetectorRule]) -> Sequence[Signal1Match]:
        """Return matches found for candidate content across active rules."""
        ...


class DangerSensor(Protocol):
    """Port for Signal 2: host checks on the checked payload itself.

    A sensor sees the payload, never the detector's matches; `observer_id`
    names the host check.
    """

    observer_id: str

    def detect_danger(self, content: str) -> Signal2Danger | None:
        """Return host-observed damage in `content`, or None."""
        ...


class SelfPanelStore(Protocol):
    """Port providing access to the sealed Self-Panel for Thymic Negative Selection."""

    def get_self_fixtures(self) -> Sequence[str]:
        """Return collection of verified clean, non-pathogenic self fixtures."""
        ...


class ImmuneQuarantineSink(Protocol):
    """Port for sinking quarantined pathogens and mutated antibodies."""

    def record_quarantine(
        self,
        rule: DetectorRule,
        match: Signal1Match,
        danger: Signal2Danger,
        disposition: DangerDecision,
    ) -> str:
        """Persist quarantine entry into append-only cryptographic ledger."""
        ...


class ExternalAdmissionPolicyPort(Protocol):
    """Inward port for admission decisions that may have a native implementation."""

    def distinct_observations(
        self, observations: tuple[AntibodyObservationV1, ...]
    ) -> tuple[str, ...]: ...

    def is_promotable(
        self,
        request: ExternalAdmissionRequestV1,
        observations: tuple[AntibodyObservationV1, ...],
        *,
        required_distinct: int,
    ) -> bool: ...

    def verify_replay(
        self,
        candidate_id: str,
        use_legacy_verifier: bool,
        registered_candidates: frozenset[str],
    ) -> ReplayResult: ...

    def apply_human_admission(
        self,
        decision: HumanAntiSkillAdmissionDecisionV1,
        target_rule_bytes: bytes,
    ) -> dict[str, str]: ...

    def resolve_polarity(
        self,
        producer: str,
        schema_version: str,
        registry: tuple[FixturePolarityMapV1, ...],
    ) -> FixturePolarityMapV1: ...

    def validate_binding(
        self,
        binding: OperationalBindingV1,
        detector_matches: list[bool],
    ) -> FixtureValidationResult: ...

    def decide_custody(self, evidence: Mapping[str, Any]) -> str: ...


class GuardActivationPolicyPort(Protocol):
    """Inward port for the receipt-bound learned-guard activation law."""

    def evaluate_activation(
        self,
        profile_digest: str,
        hit: DetectorHitRefV1 | None,
        danger: DangerSignalReceiptV1 | None,
        *,
        externally_admitted: bool,
        suspended: bool,
        disposition: str,
    ) -> GuardActivationReceiptV1: ...


class ProvisionalPromotionPolicyPort(Protocol):
    """Inward port for observation support and provisional review eligibility."""

    def promote(
        self,
        candidate_id: str,
        support_count: int | str,
        diagnostic_scope: list[str],
    ) -> PromotionResult: ...

    def register_observation(self, observation: RawObservationV1) -> None: ...

    def compute_support(self, observations: Sequence[RawObservationV1]) -> SupportResult: ...


class CatalogByteSource(Protocol):
    """Catalog bytes the caller already located. No filesystem import."""

    def read_text(self, path: str) -> str: ...

    def read_bytes(self, path: str) -> bytes: ...

    def is_file(self, path: str) -> bool: ...

    def exists(self, path: str) -> bool: ...
