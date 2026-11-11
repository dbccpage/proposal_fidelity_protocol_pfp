"""Two-Signal Epistemic Immune Regulator (Milestone 1 — Substantive EIS Upgrade).

Composes:
1. Thymic Central Tolerance (`ThymusSelfPanelBuilder`, `NormalizedMatcher`)
2. Matzinger Two-Signal Danger Gate (`TwoSignalRegulatorV1`, `TwoSignalRegulationOutcome`)
3. Public-Invariant Mathematical Antibody Suite (`QMInvariantAntibodySuiteV1`, `QMInvariantReceiptV1`)
4. Acquired Antibody Promotion via Conflict-Graph MIS (`AcquiredAntibodyPromotionV1`)
5. Guard Activation & Host Health Adapters (`HostHealthReceiptV1`, `evaluate_guard_activation`)

AuthorityEffect: None.
Evaluator Firewall: Strictly maintained. Zero private answers, evaluator constants,
or paid API calls are referenced or accessed.
"""

from __future__ import annotations

import hmac
import json
import re
import secrets
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime

# Domain imports
from eis.domain.danger_signals import (
    FORBIDDEN_DANGER_OBSERVERS,
    SignalIndependenceRefusal,
    assert_signals_independent,
)
from eis.domain.guard_activation import (
    AUTHORITY_EFFECT_NONE,
    ActivationRefusal,
    DangerSignalReceiptV1,
    DetectorHitRefV1,
    GuardActivationReceiptV1,
    evaluate_activation,
)
from eis.domain.ports import AntigenMatcher, GuardActivationPolicyPort, bound_rules
from eis.domain.provisional_promotion import (
    ObservationSupportPolicyV1,
    PromotionResult,
    ProvisionalPromotionEngineV1,
    RawObservationV1,
    SupportResult,
)
from eis.domain.value_objects import (
    DangerDecision,
    DangerSeverity,
    DetectorRule,
    Signal1Match,
    Signal2Danger,
)

# Benchmark wire normalizer
try:
    from dag.benchmark import charpoly_wire
except ImportError:
    try:
        import charpoly_wire
    except ImportError:
        charpoly_wire = None  # type: ignore[assignment]


# ============================================================================
# 1. Thymic Central Tolerance (`ThymusSelfPanelBuilder`, `NormalizedMatcher`)
# ============================================================================


class ThymusSelfPanelBuilder:
    """Constructs a clean self-panel of mathematically valid representations.

    Includes:
    - Monic characteristic polynomial wires with varied monomial orderings.
    - Sparse rational format variations ('+0', '2/2', '+4/2', '1/1') that reduce to
      identical polynomials in Q[lambda, J, Delta, K].
    - Clean 5-part obligation summaries that demonstrate valid non-defective derivations.
    """

    @classmethod
    def build_self_panel(cls) -> tuple[str, ...]:
        """Return a tuple of known-clean, mathematically valid self fixtures."""
        fixtures: list[str] = [
            # Fixture 0: Canonical minimal monic wire (det(lambda*I - H) monic leading coefficient 1)
            '{"coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "1"}]]}',
            # Fixture 1: Valid wire with unreduced rational '2/2' and explicit '+0'
            '{"coefficients": [[{"powers": [0, 0, 0], "q": "+0"}], [], [], [], [{"powers": [0, 0, 0], "q": "2/2"}]]}',
            # Fixture 2: Valid wire with permuted monomial powers and '1/1'
            (
                '{"coefficients": [[{"powers": [2, 0, 0], "q": "1"}, {"powers": [0, 2, 0], "q": "1"}], '
                '[], [], [], [{"powers": [0, 0, 0], "q": "1/1"}]]}'
            ),
            # Fixture 3: Valid wire with whitespace and positive fraction '+4/2'
            (
                '{\n  "coefficients": [\n    [],\n    [{"powers": [1, 1, 0], "q": "+4/2"}],\n'
                '    [],\n    [],\n    [{"powers": [0, 0, 0], "q": "1"}]\n  ]\n}'
            ),
            # Fixture 4: Valid textual 5-part obligation summary
            (
                "Self-contained derivation for Hamiltonian H:\n"
                "1. Spectrum: Full eigenvalues and spectral projectors of H derived. "
                "Exceptional limit J=Delta=0 yields degeneracy.\n"
                "2. Transition probability: P_01_to_10(t) = (J^2/(J^2+Delta^2)) * sin^2(omega * t). "
                "Initial condition P(0) = 0. Decoupled limit at J=0 yields P(t) = 0.\n"
                "3. Reduced density matrix of first spin has von Neumann entropy S(rho_1) in [0, 1] bits, "
                "concurrence C in [0, 1], and maximal CHSH expectation in [2, 2*sqrt(2)].\n"
                "4. Thermal state: Gibbs density matrix with partition function Z(beta=0) = 4. "
                "Eigenvalues of partial transpose satisfy Peres-Horodecki criterion.\n"
                "5. Consistency checks: Trace normalization Tr(rho) = 1, initial condition P(0)=0 verified, "
                "decoupled limit J=0 verified, branch guard at J=Delta=0 explicit."
            ),
        ]
        return tuple(fixtures)


class NormalizedMatcher:
    """AntigenMatcher implementing value-preserving normalization before pattern evaluation.

    Satisfies the `AntigenMatcher` protocol. If candidate content is a charpoly wire,
    it passes through `charpoly_wire.normalize_candidate`, reducing rationals and sorting
    monomials so that superficial formatting differences do not trigger false-positive matches.
    """

    matcher_id: str = "normalized_charpoly"
    detector_predicates: frozenset[str] = frozenset()
    reports_content_offsets: bool = False

    def __init__(self, matcher_id: str = "normalized_charpoly") -> None:
        self.matcher_id = matcher_id

    def match_antigen(self, content: str, rules: Sequence[DetectorRule]) -> Sequence[Signal1Match]:
        """Scan candidate content against active rules after value-preserving normalization."""
        active = bound_rules(self.matcher_id, rules)
        if not active:
            return ()

        normalized_text = content
        if charpoly_wire is not None:
            try:
                norm_res = charpoly_wire.normalize_candidate(content)
                if norm_res.get("accepted"):
                    normalized_text = norm_res.get("normalized_json") or content
            except (TypeError, ValueError, KeyError):
                normalized_text = content

        matches: list[Signal1Match] = []
        for rule in active:
            try:
                rx = re.compile(rule.match_pattern)
                m = rx.search(normalized_text)
                if m is not None:
                    matches.append(
                        Signal1Match(
                            epitope_name=rule.target_epitope,
                            pattern_matched=m.group(0),
                            confidence=rule.affinity_score,
                            offset=m.start() if self.reports_content_offsets else 0,
                            detector_id=rule.rule_id,
                            matched_locus=rule.match_pattern,
                            match_signature=rule.rule_id,
                        )
                    )
            except re.error:
                continue

        return tuple(matches)


# ============================================================================
# 2. Matzinger Two-Signal Danger Gate (`TwoSignalRegulatorV1`)
# ============================================================================


@dataclass(frozen=True, slots=True)
class TwoSignalRegulationOutcome:
    """Result emitted by the Matzinger Two-Signal Regulator."""

    decision: DangerDecision
    normalized_content: str | None
    signal1_matches: tuple[Signal1Match, ...]
    signal2_danger: Signal2Danger | None
    independence_basis: str
    rationale: str


class TwoSignalRegulatorV1:
    """Matzinger Two-Signal Epistemic Immune Regulator.

    Rules enforced:
    1. Zero Signals: TOLERATED.
    2. Signal 1 Alone (surface / format variation without Host Danger):
       DIAGNOSTIC_ONLY disposition (never hard refusal). Normalizes candidate via
       charpoly_wire where applicable, returning normalized artifact.
    3. Signal 1 AND Independent Host Signal 2:
       DEFENSIVE_LOCKDOWN or QUARANTINED (HOLD / REFUSE).
    4. Two-Signal Collapse:
       Raises `SignalIndependenceRefusal('TWO_SIGNAL_COLLAPSE', ...)` when Signal 2
       is model-authored, shares detector predicates, matches Signal 1 digest, or
       has overlapping evidence spans.
    """

    def evaluate(
        self,
        content: str,
        matches: Sequence[Signal1Match],
        danger: Signal2Danger | None,
        *,
        detector_id: str,
        detector_predicates: frozenset[str] = frozenset(),
        offsets_are_content: bool = True,
    ) -> TwoSignalRegulationOutcome:
        """Regulate candidate content under two-signal danger law."""
        # 1. Explicit check for derived danger signals (Matzinger two-signal law)
        if danger is not None and (
            danger.is_derived
            or danger.derived_from is not None
            or danger.danger_type == "TWO_SIGNAL_COLLAPSE"
            or danger.observer_id == "derived_from_signal1"
        ):
            raise SignalIndependenceRefusal(
                "TWO_SIGNAL_COLLAPSE",
                "Signal 2 is derived from Signal 1",
            )

        # 2. Check independence of signals if danger is present
        independence_basis = assert_signals_independent(
            matches,
            danger,
            detector_id=detector_id,
            detector_predicates=detector_predicates,
            offsets_are_content=offsets_are_content,
        )

        # 2. Case A: Zero signals observed
        if not matches and danger is None:
            return TwoSignalRegulationOutcome(
                decision=DangerDecision.TOLERATED,
                normalized_content=content,
                signal1_matches=(),
                signal2_danger=None,
                independence_basis=independence_basis,
                rationale="No Signal 1 epitope matches or Signal 2 danger signals observed. Tolerated.",
            )

        # 3. Case B: Signal 1 alone (surface/format variation)
        if matches and danger is None:
            normalized_content = content
            if charpoly_wire is not None:
                try:
                    res = charpoly_wire.normalize_candidate(content)
                    if res.get("accepted"):
                        normalized_content = res.get("normalized_json") or content
                except (TypeError, ValueError, KeyError):
                    normalized_content = content

            return TwoSignalRegulationOutcome(
                decision=DangerDecision.DIAGNOSTIC_ONLY,
                normalized_content=normalized_content,
                signal1_matches=tuple(matches),
                signal2_danger=None,
                independence_basis=independence_basis,
                rationale=(
                    f"Signal 1 format variation ({len(matches)} match(es)) observed without host "
                    "tissue danger: non-destructive diagnostic disposition. Normalized candidate returned."
                ),
            )

        # 4. Case C: Signal 1 AND independent Host Signal 2
        if matches and danger is not None:
            decision = (
                DangerDecision.QUARANTINED
                if danger.severity in (DangerSeverity.HIGH, DangerSeverity.CRITICAL)
                else DangerDecision.DEFENSIVE_LOCKDOWN
            )
            return TwoSignalRegulationOutcome(
                decision=decision,
                normalized_content=None,
                signal1_matches=tuple(matches),
                signal2_danger=danger,
                independence_basis=independence_basis,
                rationale=(
                    f"Activated under Two-Signal Law: {len(matches)} Signal 1 match(es) paired with "
                    f"independent Host Signal 2 ({danger.danger_type} from {danger.observer_id}). "
                    f"Disposition: {decision.value}."
                ),
            )

        # 5. Case D: Signal 2 alone (host danger without matching Signal 1 epitope)
        return TwoSignalRegulationOutcome(
            decision=DangerDecision.DEFENSIVE_LOCKDOWN,
            normalized_content=None,
            signal1_matches=(),
            signal2_danger=danger,
            independence_basis=independence_basis,
            rationale=(
                f"Host tissue danger {danger.danger_type if danger else ''} observed without "
                "recognized Signal 1 epitope: defensive lockdown."
            ),
        )

    def evaluate_proposal(
        self,
        content: str,
        *,
        matcher: AntigenMatcher | None = None,
        rules: Sequence[DetectorRule] = (),
        host_signal2: Signal2Danger | None = None,
        detector_id: str = "regex",
        detector_predicates: frozenset[str] = frozenset(),
        offsets_are_content: bool = True,
    ) -> TwoSignalRegulationOutcome:
        """Scan candidate content with matcher and evaluate under two-signal danger law."""
        if matcher is not None and detector_id == "regex" and hasattr(matcher, "matcher_id"):
            detector_id = matcher.matcher_id

        matches: Sequence[Signal1Match] = ()
        if matcher is not None and rules:
            matches = matcher.match_antigen(content, rules)

        return self.evaluate(
            content=content,
            matches=matches,
            danger=host_signal2,
            detector_id=detector_id,
            detector_predicates=detector_predicates,
            offsets_are_content=offsets_are_content,
        )


# ============================================================================
# 3. Public-Invariant Mathematical Antibody Suite (`QMInvariantAntibodySuiteV1`)
# ============================================================================


@dataclass(frozen=True, slots=True)
class AntibodyFinding:
    """Individual antibody check finding."""

    antibody_id: str
    name: str
    passed: bool
    evidence: str


@dataclass(frozen=True, slots=True)
class QMInvariantReceiptV1:
    """Structured receipt for Public-Invariant Mathematical Antibody Suite evaluation.

    Hard invariant: final_answer_certified is ALWAYS False.
    """

    schema_version: str = "pfp.qm-invariant-antibody-suite.v1"
    total_antibodies: int = 10
    passed_count: int = 0
    all_passed: bool = False
    findings: tuple[AntibodyFinding, ...] = ()
    final_answer_certified: bool = False
    limitation_notice: str = (
        "Textbook public-invariant sanity check only; passing these coarse bounds "
        "does not establish full mathematical accuracy, projector correctness, or certified QM solutions."
    )


class QMInvariantAntibodySuiteV1:
    """Suite of 10 executable host-side antibodies evaluating public textbook invariants.

    Derived exclusively from `dag/benchmark/seed_prompt.txt` public wording and
    universal domain-axiomatic physics bounds. Zero evaluator rubric constants or
    private answers are accessed.
    """

    @classmethod
    def evaluate(cls, candidate_text: str) -> QMInvariantReceiptV1:
        """Evaluate candidate derivation against all 10 public invariants."""
        findings: list[AntibodyFinding] = [
            cls._check_ab01_structural_completeness(candidate_text),
            cls._check_ab02_initial_transition_probability(candidate_text),
            cls._check_ab03_probability_range(candidate_text),
            cls._check_ab04_decoupled_limit_stationarity(candidate_text),
            cls._check_ab05_branch_guards_zero_denominator(candidate_text),
            cls._check_ab06_high_temperature_partition_function(candidate_text),
            cls._check_ab07_concurrence_range(candidate_text),
            cls._check_ab08_single_qubit_entropy_bits(candidate_text),
            cls._check_ab09_chsh_bound_range(candidate_text),
            cls._check_ab10_cross_section_consistency(candidate_text),
        ]

        passed_count = sum(1 for f in findings if f.passed)
        all_passed = passed_count == len(findings)

        return QMInvariantReceiptV1(
            total_antibodies=len(findings),
            passed_count=passed_count,
            all_passed=all_passed,
            findings=tuple(findings),
            final_answer_certified=False,  # Enforced invariant
        )

    @staticmethod
    def _check_ab01_structural_completeness(text: str) -> AntibodyFinding:
        """Ab01: 5-part structural completeness & non-truncation."""
        # 1. Truncation check
        stripped = text.strip()
        if len(stripped) < 150:
            return AntibodyFinding(
                antibody_id="Ab01_StructuralCompleteness",
                name="5-Part Structural Completeness & Non-Truncation",
                passed=False,
                evidence=f"Text too short ({len(stripped)} chars) to contain full 5-obligation derivation.",
            )

        truncation_markers = r"(?:\.\.\.|…|\b(?:etc|tbd|todo)\b|[=+\-*/(,]\s*$|\\begin\{[a-z*]+\}\s*$)"
        if re.search(truncation_markers, stripped[-50:], re.IGNORECASE):
            return AntibodyFinding(
                antibody_id="Ab01_StructuralCompleteness",
                name="5-Part Structural Completeness & Non-Truncation",
                passed=False,
                evidence="Derivation ends abruptly with dangling operator, ellipsis, or unclosed syntax.",
            )

        # 2. Check coverage of all 5 obligations
        has_part1 = bool(
            re.search(
                r"(?:obligation\s*1|part\s*1|1\.\s+|spectrum|eigenvalues|spectral\s+projectors)",
                text,
                re.IGNORECASE,
            )
        )
        has_part2 = bool(
            re.search(
                r"(?:obligation\s*2|part\s*2|2\.\s+|transition\s+probability|p_01|p\(t\)|p_{01})",
                text,
                re.IGNORECASE,
            )
        )
        has_part3 = bool(
            re.search(
                r"(?:obligation\s*3|part\s*3|3\.\s+|reduced\s+density|entropy|concurrence|chsh)",
                text,
                re.IGNORECASE,
            )
        )
        has_part4 = bool(
            re.search(
                r"(?:obligation\s*4|part\s*4|4\.\s+|gibbs|partition\s+function|partial\s+transpose|thermal\s+entanglement|beta)",
                text,
                re.IGNORECASE,
            )
        )
        has_part5 = bool(
            re.search(
                r"(?:obligation\s*5|part\s*5|5\.\s+|consistency\s+checks|consistency|decoupled\s+limit|initial\s+conditions)",
                text,
                re.IGNORECASE,
            )
        )

        missing = []
        if not has_part1:
            missing.append("Part 1 (Spectrum/Projectors)")
        if not has_part2:
            missing.append("Part 2 (Transition Probability)")
        if not has_part3:
            missing.append("Part 3 (Entropy/Concurrence/CHSH)")
        if not has_part4:
            missing.append("Part 4 (Thermal Gibbs/Partition Function)")
        if not has_part5:
            missing.append("Part 5 (Consistency Checks)")

        if missing:
            return AntibodyFinding(
                antibody_id="Ab01_StructuralCompleteness",
                name="5-Part Structural Completeness & Non-Truncation",
                passed=False,
                evidence=f"Missing required obligation coverage: {', '.join(missing)}.",
            )

        return AntibodyFinding(
            antibody_id="Ab01_StructuralCompleteness",
            name="5-Part Structural Completeness & Non-Truncation",
            passed=True,
            evidence="All 5 obligations present and text is non-truncated.",
        )

    @staticmethod
    def _check_ab02_initial_transition_probability(text: str) -> AntibodyFinding:
        """Ab02: Initial condition at t=0 with |01>: P_01_to_10(0) = 0."""
        # Contradiction check: P(0) != 0 or non-zero decimal at t=0
        contradiction = re.search(
            r"(?:P(?:_\{?01(?:[_\s]*to[_\s]*|\\to\s*)10\}?)?\s*\(\s*0\s*\)\s*=\s*(?:0\.[0-9]*[1-9][0-9]*|[1-9][0-9]*(?:\.[0-9]+)?)(?![0-9]|\.[0-9])|"
            r"P\s*=\s*(?:0\.[0-9]*[1-9][0-9]*|[1-9][0-9]*(?:\.[0-9]+)?)(?![0-9]|\.[0-9])\s+at\s+t\s*=\s*0|"
            r"P(?:_\{?01(?:[_\s]*to[_\s]*|\\to\s*)10\}?)?\s*\(\s*0\s*\)\s*(?:!=|>)\s*0(?![0-9]|\.[0-9]))",
            text,
            re.IGNORECASE,
        )
        if contradiction:
            return AntibodyFinding(
                antibody_id="Ab02_InitialTransitionProbability",
                name="Initial Condition P(0) = 0",
                passed=False,
                evidence=f"Contradicts initial boundary condition: found '{contradiction.group(0)}'.",
            )

        # Positive presence check: P(0)=0 or sin(0)=0 or initial condition mentioned
        has_init = bool(
            re.search(
                r"(?:P(?:_\{?01(?:[_\s]*to[_\s]*|\\to\s*)10\}?)?\s*\(\s*0\s*\)\s*=\s*0(?![0-9]|\.[0-9])|"
                r"initial(?:ly)?(?:\s+state)?.*P\s*=\s*0(?![0-9]|\.[0-9])|"
                r"\bsin\^?2?\s*\(\s*0\s*\)\s*=\s*0(?![0-9]|\.[0-9])|"
                r"P\s*=\s*0(?![0-9]|\.[0-9])\s+at\s+t\s*=\s*0|"
                r"initial\s+condition.*0(?![0-9]|\.[0-9]))",
                text,
                re.IGNORECASE,
            )
        )
        if not has_init:
            return AntibodyFinding(
                antibody_id="Ab02_InitialTransitionProbability",
                name="Initial Condition P(0) = 0",
                passed=False,
                evidence="Initial condition P(0) = 0 not explicitly stated or satisfied.",
            )

        return AntibodyFinding(
            antibody_id="Ab02_InitialTransitionProbability",
            name="Initial Condition P(0) = 0",
            passed=True,
            evidence="Initial condition P(0) = 0 verified.",
        )

    @staticmethod
    def _check_ab03_probability_range(text: str) -> AntibodyFinding:
        """Ab03: Probability range P in [0, 1]."""
        # Range violation: P > 1, P < 0, or P = value outside [0, 1] including fractions in (1, 2)
        violation = re.search(
            r"(?:P\s*>\s*1(?![0-9]|\.[0-9])|"
            r"P\s*<\s*0(?![0-9]|\.[0-9])|"
            r"probability\s+exceeds\s+1|"
            r"probability\s+(?:is\s+)?negative|"
            r"P\s*=\s*(?:-[0-9]+(?:\.[0-9]+)?|1\.[0-9]*[1-9][0-9]*|[2-9](?:\.[0-9]+)?|\d{2,}(?:\.[0-9]+)?)(?![0-9]|\.[0-9]))",
            text,
            re.IGNORECASE,
        )
        if violation:
            return AntibodyFinding(
                antibody_id="Ab03_ProbabilityRange",
                name="Transition Probability Range [0, 1]",
                passed=False,
                evidence=f"Probability range violation detected: '{violation.group(0)}'.",
            )

        return AntibodyFinding(
            antibody_id="Ab03_ProbabilityRange",
            name="Transition Probability Range [0, 1]",
            passed=True,
            evidence="Transition probability remains within physical range [0, 1].",
        )

    @staticmethod
    def _check_ab04_decoupled_limit_stationarity(text: str) -> AntibodyFinding:
        """Ab04: Decoupled limit stationarity: at J = 0, P = 0."""
        # Contradiction: transition at J=0, ignoring valid negations ("no transition occurs")
        contradiction = re.search(
            r"(?:J\s*=\s*0.*?(?:P\s*=\s*(?:0\.[0-9]*[1-9][0-9]*|[1-9][0-9]*(?:\.[0-9]+)?)(?![0-9]|\.[0-9])|"
            r"(?<!\bno\s)(?<!\bwithout\s)(?<!\bzero\s)\btransitions?\s+occurs?\b))",
            text,
            re.IGNORECASE,
        )
        if contradiction:
            return AntibodyFinding(
                antibody_id="Ab04_DecoupledLimitStationarity",
                name="Decoupled Limit Stationarity (J = 0 -> P = 0)",
                passed=False,
                evidence=f"Violates decoupled limit: found '{contradiction.group(0)}'.",
            )

        has_decoupled = bool(
            re.search(
                r"(?:(?:at|when|limit|for)\s+J\s*=\s*0.*(?:P\s*=\s*0(?![0-9]|\.[0-9])|P\s*\\equiv\s*0|vanishes|stationary|no\s+transition)|"
                r"J\s*=\s*0\s*(?:=>|implies|yields|gives)\s*P\s*=\s*0(?![0-9]|\.[0-9])|"
                r"decoupled\s+limit.*(?:J\s*=\s*0|P\s*=\s*0(?![0-9]|\.[0-9])|stationary))",
                text,
                re.IGNORECASE,
            )
        )
        if not has_decoupled:
            return AntibodyFinding(
                antibody_id="Ab04_DecoupledLimitStationarity",
                name="Decoupled Limit Stationarity (J = 0 -> P = 0)",
                passed=False,
                evidence="Decoupled limit J = 0 stationarity not explicitly addressed.",
            )

        return AntibodyFinding(
            antibody_id="Ab04_DecoupledLimitStationarity",
            name="Decoupled Limit Stationarity (J = 0 -> P = 0)",
            passed=True,
            evidence="Stationarity under decoupled limit J = 0 verified.",
        )

    @staticmethod
    def _check_ab05_branch_guards_zero_denominator(text: str) -> AntibodyFinding:
        """Ab05: Zero-denominator / degeneracy branch guards for J = Delta = 0 and J = 0."""
        has_branch_guard = bool(
            re.search(
                r"(?:J\s*=\s*(?:\\Delta|Delta)\s*=\s*0|J\s*=\s*0\s*(?:and|,\s*)\s*(?:\\Delta|Delta)\s*=\s*0|degeneracy|exceptional\s+cases?|branch\s+guard|denominator\s+vanishes|when\s+J\^?2?\s*\+\s*(?:\\Delta|Delta)\^?2?\s*=\s*0)",
                text,
                re.IGNORECASE,
            )
        )
        if not has_branch_guard:
            return AntibodyFinding(
                antibody_id="Ab05_BranchGuardsZeroDenominator",
                name="Zero-Denominator & Degeneracy Branch Guards (J = Delta = 0)",
                passed=False,
                evidence="Missing explicit branch handling for singular limit J = Delta = 0 or zero denominator.",
            )

        return AntibodyFinding(
            antibody_id="Ab05_BranchGuardsZeroDenominator",
            name="Zero-Denominator & Degeneracy Branch Guards (J = Delta = 0)",
            passed=True,
            evidence="Explicit branch handling for J = Delta = 0 degeneracy and denominator safeguards verified.",
        )

    @staticmethod
    def _check_ab06_high_temperature_partition_function(text: str) -> AntibodyFinding:
        """Ab06: High-temperature partition function limit: at beta = 0, Z_0 = 4."""
        contradiction = re.search(
            r"(?:\bZ(?:_\s*0|\s*\(\s*(?:\\beta|beta)?\s*=\s*0\s*\)|\s*\(\s*0\s*\)|\s*\(\s*\\?beta\s*\))\s*=\s*(?!4(?![0-9]|\.[0-9]))-?[0-9]+(?:\.[0-9]+)?|"
            r"\bpartition\s+function\s+(?:at\s+(?:\\beta|beta)?\s*=\s*0\s+is\s+|is\s+)(?!4(?![0-9]|\.[0-9]))-?[0-9]+(?:\.[0-9]+)?)",
            text,
            re.IGNORECASE,
        )
        if contradiction:
            return AntibodyFinding(
                antibody_id="Ab06_HighTemperaturePartitionFunction",
                name="High-Temperature Partition Function Limit Z(0) = 4",
                passed=False,
                evidence=f"Contradicts high-temperature partition limit: found '{contradiction.group(0)}'.",
            )

        has_z0 = bool(
            re.search(
                r"(?:\bZ(?:_\s*0|\s*\(\s*(?:\\beta|beta)?\s*=\s*0\s*\)|\s*\(\s*0\s*\)|\s*\(\s*\\?beta\s*\))\s*=\s*4(?![0-9]|\.[0-9])|"
                r"Tr\s*\(\s*I_?4?\s*\)\s*=\s*4(?![0-9]|\.[0-9])|"
                r"\bpartition\s+function\s+(?:at\s+beta\s*=\s*0\s+is\s+|is\s+)4(?![0-9]|\.[0-9])|"
                r"beta\s*=\s*0.*Z\s*=\s*4(?![0-9]|\.[0-9]))",
                text,
                re.IGNORECASE,
            )
        )
        if not has_z0:
            return AntibodyFinding(
                antibody_id="Ab06_HighTemperaturePartitionFunction",
                name="High-Temperature Partition Function Limit Z(0) = 4",
                passed=False,
                evidence="High-temperature partition function limit Z(beta=0) = 4 not verified.",
            )

        return AntibodyFinding(
            antibody_id="Ab06_HighTemperaturePartitionFunction",
            name="High-Temperature Partition Function Limit Z(0) = 4",
            passed=True,
            evidence="High-temperature limit Z(0) = Tr(I_4) = 4 verified.",
        )

    @staticmethod
    def _check_ab07_concurrence_range(text: str) -> AntibodyFinding:
        """Ab07: Pure-state concurrence range: C in [0, 1]."""
        violation = re.search(
            r"(?:C\s*>\s*1(?![0-9]|\.[0-9])|"
            r"concurrence\s+exceeds\s+1|"
            r"concurrence\s*=\s*(?:-[0-9]+(?:\.[0-9]+)?|1\.[0-9]*[1-9][0-9]*|[2-9](?:\.[0-9]+)?|2\s*\\?sqrt|2\s*\*\s*\\?sqrt|\d{2,}(?:\.[0-9]+)?)(?![0-9]|\.[0-9])|"
            r"C\s*=\s*(?:-[0-9]+(?:\.[0-9]+)?|1\.[0-9]*[1-9][0-9]*|[2-9](?:\.[0-9]+)?|\d{2,}(?:\.[0-9]+)?)(?![0-9]|\.[0-9]))",
            text,
            re.IGNORECASE,
        )
        if violation:
            return AntibodyFinding(
                antibody_id="Ab07_ConcurrenceRange",
                name="Pure-State Concurrence Range [0, 1]",
                passed=False,
                evidence=f"Concurrence range violation detected: '{violation.group(0)}'.",
            )

        return AntibodyFinding(
            antibody_id="Ab07_ConcurrenceRange",
            name="Pure-State Concurrence Range [0, 1]",
            passed=True,
            evidence="Concurrence respects bounded range [0, 1].",
        )

    @staticmethod
    def _check_ab08_single_qubit_entropy_bits(text: str) -> AntibodyFinding:
        """Ab08: Single-qubit entropy in bits: S(rho_1) in [0, 1]."""
        violation = re.search(
            r"(?:(?:S\s*(?:\(\s*\\?rho_?1?\s*\))?|(?:von\s+neumann\s+)?entropy(?:\s+S\s*(?:\(\s*\\?rho_?1?\s*\))?)?)\s*>\s*1(?![0-9]|\.[0-9])|"
            r"entropy\s+exceeds\s+1\s+bit|"
            r"(?:S\s*(?:\(\s*\\?rho_?1?\s*\))?|(?:von\s+neumann\s+)?entropy(?:\s+S\s*(?:\(\s*\\?rho_?1?\s*\))?)?)\s*=\s*(?:-[0-9]+(?:\.[0-9]+)?|1\.[0-9]*[1-9][0-9]*|[2-9](?:\.[0-9]+)?|\d{2,}(?:\.[0-9]+)?)(?![0-9]|\.[0-9]))",
            text,
            re.IGNORECASE,
        )
        if violation:
            return AntibodyFinding(
                antibody_id="Ab08_SingleQubitEntropyInBits",
                name="Single-Qubit Entropy Range [0, 1] Bit",
                passed=False,
                evidence=f"Single-qubit entropy exceeds 1-bit physical bound: '{violation.group(0)}'.",
            )

        return AntibodyFinding(
            antibody_id="Ab08_SingleQubitEntropyInBits",
            name="Single-Qubit Entropy Range [0, 1] Bit",
            passed=True,
            evidence="Single-qubit entropy respects 2-level bound [0, 1] bit.",
        )

    @staticmethod
    def _check_ab09_chsh_bound_range(text: str) -> AntibodyFinding:
        """Ab09: physical CHSH range |S| <= 2*sqrt(2) (Tsirelson), and nothing more.

        Three predicates are kept apart (PR #63 review, item 5):
          - physical expectation: |S| <= 2*sqrt(2); a claim outside it is refused;
          - local-hidden-variable bound: |S| <= 2; reported, never refused;
          - Bell violation: |S| > 2; reported, never required.
        Values below 2, including 0 for the maximally mixed state, are physical.
        """
        tsirelson = 2 * 2 ** 0.5
        # Trigger only on a CHSH/Bell (or |S|) claim with a comparison operator. The word
        # boundaries keep unrelated words out (e.g. "Campbell"), and the bare "expectation"
        # trigger is gone, so an unrelated "energy expectation = 3.5" is not a CHSH claim.
        header = re.compile(
            r"\b(?:maximal\s+)?(?:CHSH|Bell)\b(?:\s+(?:value|expectation|parameter))?\s*"
            r"(?P<abs>\|S\|\s*)?(?P<op>=|<=|>=|<|>)\s*",
            re.IGNORECASE,
        )
        # One additive term: an optional sign, then either coeff*sqrt(n) or a plain number.
        term = re.compile(
            r"\s*(?P<sign>[+-])?\s*(?:(?P<coeff>[0-9]+(?:\.[0-9]+)?)\s*\*\s*)?"
            r"(?:\\?sqrt\s*[\{\(]?\s*(?P<rad>[0-9]+(?:\.[0-9]+)?)\s*[\}\)]?|(?P<plain>[0-9]+(?:\.[0-9]+)?))",
            re.IGNORECASE,
        )

        def _sum_rhs(start: int) -> tuple[float, int] | None:
            """Sum the additive numeric terms from ``start``; None if nothing parses there."""
            total, pos, first = 0.0, start, True
            while True:
                m = term.match(text, pos)
                if not m or (not first and m.group("sign") is None):
                    break
                sign = -1.0 if (m.group("sign") == "-") else 1.0
                if m.group("rad") is not None:
                    coeff = float(m.group("coeff")) if m.group("coeff") else 1.0
                    value = coeff * (float(m.group("rad")) ** 0.5)
                elif m.group("coeff") is not None:
                    break  # a bare "coeff * <non-sqrt>" is not a CHSH magnitude we parse
                else:
                    value = float(m.group("plain"))
                total += sign * value
                pos, first = m.end(), False
            return (total, pos) if not first else None

        violations, notes = [], []
        for match in header.finditer(text):
            summed = _sum_rhs(match.end())
            if summed is None:
                continue  # a CHSH/Bell claim with no numeric right-hand side is not evaluated
            v, end = summed
            op = match.group("op")
            has_abs = bool(match.group("abs"))
            claim = text[match.start():end]
            if (
                (op == "=" and (abs(v) > tsirelson + 1e-9 or (has_abs and v < -1e-9)))
                or (op in (">", ">=") and (v > tsirelson + 1e-9 or (op == ">" and abs(v - tsirelson) <= 1e-9)))
                or (
                    op in ("<", "<=")
                    and (
                        (has_abs and (v < -1e-9 or (op == "<" and abs(v) <= 1e-9)))
                        or (not has_abs and (v < -tsirelson - 1e-9 or (op == "<" and abs(v + tsirelson) <= 1e-9)))
                    )
                )
            ):
                violations.append(claim)
            elif op == "=":
                notes.append(f"{claim} ({'Bell violation' if abs(v) > 2 + 1e-9 else 'within the LHV bound'})")
        if violations:
            return AntibodyFinding(
                antibody_id="Ab09_CHSHBoundRange",
                name="CHSH physical range |S| <= 2*sqrt(2)",
                passed=False,
                evidence=f"CHSH expectation violates Tsirelson ceiling |S| <= 2*sqrt(2): '{violations[0]}'.",
            )

        return AntibodyFinding(
            antibody_id="Ab09_CHSHBoundRange",
            name="CHSH physical range |S| <= 2*sqrt(2)",
            passed=True,
            evidence="No CHSH claim exceeds 2*sqrt(2)." + (" " + "; ".join(notes) if notes else ""),
        )

    @staticmethod
    def _check_ab10_cross_section_consistency(text: str) -> AntibodyFinding:
        """Ab10: Cross-section consistency: trace normalization Tr(rho) = 1."""
        violation = re.search(
            r"(?:Tr\s*\(\s*\\?rho(?:_1)?\s*\)\s*=\s*(?:-[0-9]+(?:\.[0-9]+)?|0(?:\.[0-9]+)?|1\.[0-9]*[1-9][0-9]*|[2-9](?:\.[0-9]+)?|\d{2,}(?:\.[0-9]+)?)(?![0-9]|\.[0-9])|"
            r"trace\s+is\s+not\s+1|unnormalized\s+density\s+matrix)",
            text,
            re.IGNORECASE,
        )
        if violation:
            return AntibodyFinding(
                antibody_id="Ab10_CrossSectionConsistency",
                name="Cross-Section Consistency Tr(rho) = 1",
                passed=False,
                evidence=f"Density matrix trace normalization violated: '{violation.group(0)}'.",
            )

        has_trace = bool(
            re.search(
                r"(?:Tr\s*\(\s*\\?rho(?:_1)?\s*\)\s*=\s*1(?![0-9]|\.[0-9])|"
                r"trace\s+(?:is\s+)?(?:normalized\s+to\s+)?1(?![0-9]|\.[0-9])|"
                r"density\s+matrix\s+has\s+unit\s+trace|"
                r"normalization\s+Tr\s*=\s*1(?![0-9]|\.[0-9])|"
                r"\btrace\s+normalization\b)",
                text,
                re.IGNORECASE,
            )
        )
        if not has_trace:
            return AntibodyFinding(
                antibody_id="Ab10_CrossSectionConsistency",
                name="Cross-Section Consistency Tr(rho) = 1",
                passed=False,
                evidence="Trace normalization Tr(rho) = 1 not explicitly maintained.",
            )

        return AntibodyFinding(
            antibody_id="Ab10_CrossSectionConsistency",
            name="Cross-Section Consistency Tr(rho) = 1",
            passed=True,
            evidence="Trace normalization Tr(rho) = 1 verified.",
        )


# ============================================================================
# 4. Acquired Antibody Promotion via Conflict-Graph MIS (`AcquiredAntibodyPromotionV1`)
# ============================================================================


class AcquiredAntibodyPromotionV1:
    """Manages multi-run failure observations, correlation conflict graph MIS, and provisional promotion.

    Binds `RawObservationV1`, `ObservationSupportPolicyV1`, and `ProvisionalPromotionEngineV1`.
    Enforces that >= 3 correlated observations (e.g. from the same model or scaffold) collapse
    under exact maximum independent set (MIS) branch-and-bound to support_count = 1 ('Candidate'),
    whereas >= 3 independent channels reach 'Provisional' with authority_effect = 'None'.
    """

    def __init__(
        self,
        policy: ObservationSupportPolicyV1 | None = None,
        engine: ProvisionalPromotionEngineV1 | None = None,
    ) -> None:
        self.policy = policy or ObservationSupportPolicyV1()
        self.engine = engine or ProvisionalPromotionEngineV1()

    def compute_support(self, observations: Sequence[RawObservationV1]) -> SupportResult:
        """Compute exact MIS support count across observation conflict graph."""
        return self.policy.compute_support(observations)

    def evaluate_promotion(
        self,
        candidate_id: str,
        observations: Sequence[RawObservationV1],
        diagnostic_scope: list[str] | None = None,
    ) -> tuple[SupportResult, PromotionResult]:
        """Compute conflict-graph MIS support and evaluate candidate promotion eligibility."""
        support = self.compute_support(observations)
        promotion = self.engine.promote_candidate_if_eligible(
            candidate_id=candidate_id,
            support_count=support.support_count,
            diagnostic_scope=diagnostic_scope or [],
        )
        return support, promotion


# ============================================================================
# 5. Guard Activation & Host Health Adapters (`HostHealthReceiptV1`, `evaluate_guard_activation`)
# ============================================================================


@dataclass(frozen=True, slots=True)
class HostHealthReceiptV1:
    """Host health record required prior to guard activation.

    By itself this is a *declared* record: its fields are validated, but nothing in
    it shows that a trusted watchdog produced it (PR #63 review, item 6). It becomes
    an *authenticated* record only when ``HostHealthAuthority.authenticate`` accepts
    its ``nonce`` and ``mac``. ``evaluate_guard_activation`` reports which basis it used.
    """

    observer_id: str
    status: str
    subject_id: str
    profile_digest: str
    timestamp: str = "2026-11-11T00:00:00Z"
    authority_effect: str = AUTHORITY_EFFECT_NONE
    nonce: str = ""
    mac: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.observer_id, str) or not self.observer_id.strip():
            raise ValueError("observer_id must be a non-empty string")
        folded_observer = self.observer_id.strip().casefold()
        if (
            folded_observer in {obs.casefold() for obs in FORBIDDEN_DANGER_OBSERVERS}
            or self.observer_id.strip().upper() in FORBIDDEN_DANGER_OBSERVERS
        ):
            raise ValueError(f"FORBIDDEN_OBSERVER: {self.observer_id}")
        if self.status not in {"HEALTHY", "UNHEALTHY", "UNVERIFIED", "UNAVAILABLE"}:
            raise ValueError(
                f"invalid host health status: {self.status!r}; must be HEALTHY, UNHEALTHY, UNVERIFIED, or UNAVAILABLE"
            )
        for name in ("subject_id", "profile_digest"):
            value = getattr(self, name)
            if not isinstance(value, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
                raise ValueError(f"{name} must be a canonical sha256:<64 hex> digest")
        if not isinstance(self.timestamp, str) or not self.timestamp.strip():
            raise ValueError("timestamp must be a non-empty ISO-8601 UTC string")
        try:
            dt = datetime.fromisoformat(self.timestamp)
            if dt.tzinfo is None or dt.utcoffset().total_seconds() != 0:
                raise ValueError("timestamp must be an ISO-8601 UTC string")
        except Exception as exc:
            raise ValueError(f"timestamp must be a valid ISO-8601 UTC string: {exc}") from exc
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError(f"authority_effect must be {AUTHORITY_EFFECT_NONE!r}")


class HostHealthAuthority:
    """In-process issuer and verifier of authenticated host-health records.

    Records carry an HMAC-SHA256 over their canonical fields under a key that only
    this authority object holds, plus a single-use nonce. Authentication shows that
    this authority issued the record and that it was not replayed; it says nothing
    about records from other processes, and the key must never reach candidate code.
    """

    def __init__(self, key: bytes | None = None) -> None:
        self._key = key if key is not None else secrets.token_bytes(32)
        self._issued: set[str] = set()
        self._consumed: set[str] = set()

    @staticmethod
    def _body(receipt: HostHealthReceiptV1) -> bytes:
        fields = [receipt.observer_id, receipt.status, receipt.subject_id, receipt.profile_digest,
                  receipt.timestamp, receipt.authority_effect, receipt.nonce]
        return json.dumps(fields, separators=(",", ":"), ensure_ascii=True).encode("ascii")

    def _mac(self, receipt: HostHealthReceiptV1) -> str:
        return hmac.new(self._key, self._body(receipt), "sha256").hexdigest()

    def issue(self, *, observer_id: str, status: str, subject_id: str, profile_digest: str,
              timestamp: str = "2026-11-11T00:00:00Z") -> HostHealthReceiptV1:
        draft = HostHealthReceiptV1(observer_id=observer_id, status=status, subject_id=subject_id,
                                    profile_digest=profile_digest, timestamp=timestamp,
                                    nonce=secrets.token_hex(16))
        self._issued.add(draft.nonce)
        return replace(draft, mac=self._mac(draft))

    def authenticate(self, receipt: HostHealthReceiptV1, *, consume: bool = True) -> bool:
        # Refuse, never raise, on a malformed record: a non-string or unhashable nonce would
        # break the set membership test, and a non-hex (e.g. non-ASCII) mac would make
        # hmac.compare_digest raise TypeError. Both are just authentication failures.
        if type(receipt) is not HostHealthReceiptV1:
            return False
        if not isinstance(receipt.nonce, str) or not receipt.nonce:
            return False
        if not isinstance(receipt.mac, str) or not re.fullmatch(r"[0-9a-f]{64}", receipt.mac):
            return False
        if receipt.nonce not in self._issued or receipt.nonce in self._consumed:
            return False
        if not hmac.compare_digest(receipt.mac, self._mac(receipt)):
            return False
        if consume:
            self._consumed.add(receipt.nonce)
        return True


def evaluate_guard_activation(
    profile_digest: str,
    hit: DetectorHitRefV1 | None,
    danger: DangerSignalReceiptV1 | None,
    *,
    externally_admitted: bool,
    suspended: bool,
    disposition: str = "FINDING",
    host_health: HostHealthReceiptV1 | None = None,
    policy: GuardActivationPolicyPort | None = None,
    authority: HostHealthAuthority | None = None,
) -> GuardActivationReceiptV1:
    """Evaluate guard activation adapting to `eis.domain.guard_activation.evaluate_activation`.

    With ``authority`` the host-health record must authenticate (HMAC and unused
    nonce) or activation refuses with ``HOST_HEALTH_UNVERIFIED``. Without it the
    record is only *declared*: its fields are checked, its origin is not, and any
    claim built on the result must say so.
    Refuses with typed codes (`HOST_HEALTH_UNAVAILABLE`, `HOST_HEALTH_UNHEALTHY`,
    `HOST_HEALTH_UNVERIFIED`, `SUBJECT_MISMATCH`, `TWO_SIGNAL_COLLAPSE`) upon failure.
    """
    if host_health is None:
        raise ActivationRefusal(
            "HOST_HEALTH_UNAVAILABLE",
            "no host health receipt provided; authenticated host health required",
        )

    if (
        host_health.observer_id.strip().casefold() in {obs.casefold() for obs in FORBIDDEN_DANGER_OBSERVERS}
        or host_health.observer_id.strip().upper() in FORBIDDEN_DANGER_OBSERVERS
    ):
        raise ActivationRefusal(
            "TWO_SIGNAL_COLLAPSE",
            f"host health observer {host_health.observer_id!r} is a forbidden observer",
        )

    # Verify without consuming: the single-use nonce is burned only once activation actually
    # proceeds, so an unrelated later refusal does not spend a legitimate record (its retry
    # must not then fail as 'replayed').
    if authority is not None and not authority.authenticate(host_health, consume=False):
        raise ActivationRefusal(
            "HOST_HEALTH_UNVERIFIED",
            f"host health record from {host_health.observer_id!r} did not authenticate (forged, altered or replayed)",
        )

    if host_health.status == "UNVERIFIED":
        raise ActivationRefusal(
            "HOST_HEALTH_UNVERIFIED",
            f"host health unverified by {host_health.observer_id}",
        )

    if host_health.status != "HEALTHY":
        raise ActivationRefusal(
            "HOST_HEALTH_UNHEALTHY",
            f"host health reported {host_health.status} by {host_health.observer_id}",
        )

    if hit is not None and host_health.subject_id != hit.subject_id:
        raise ActivationRefusal(
            "SUBJECT_MISMATCH",
            f"host health subject_id {host_health.subject_id} does not match hit subject_id {hit.subject_id}",
        )

    if host_health.profile_digest != profile_digest:
        raise ActivationRefusal(
            "TWO_SIGNAL_COLLAPSE",
            (
                f"host health profile_digest {host_health.profile_digest} "
                f"does not match activation profile {profile_digest}"
            ),
        )

    receipt = evaluate_activation(
        profile_digest=profile_digest,
        hit=hit,
        danger=danger,
        externally_admitted=externally_admitted,
        suspended=suspended,
        disposition=disposition,
        policy=policy,
    )
    # Activation proceeded (evaluate_activation did not refuse): spend the single-use nonce now.
    if authority is not None:
        authority.authenticate(host_health, consume=True)
    return receipt


__all__ = [
    "AcquiredAntibodyPromotionV1",
    "AntibodyFinding",
    "HostHealthAuthority",
    "HostHealthReceiptV1",
    "NormalizedMatcher",
    "QMInvariantAntibodySuiteV1",
    "QMInvariantReceiptV1",
    "ThymusSelfPanelBuilder",
    "TwoSignalRegulationOutcome",
    "TwoSignalRegulatorV1",
    "evaluate_guard_activation",
]
