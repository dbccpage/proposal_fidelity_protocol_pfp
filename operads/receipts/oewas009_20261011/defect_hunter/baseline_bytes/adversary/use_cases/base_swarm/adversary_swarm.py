"""AdversarySwarm: the one base class every swarm specialises.

The base owns no adapters. It receives a ``AdversarySpineV1`` of estate ports from the
composition root (``adversary.runtime.build_adversary_swarm``) and declares a
``SwarmSpecializationV1``. A non-fixture bout first needs bound CLEAR at
PRE_DISPATCH, then runs the native seven-act circuit through the bout port and
screens the bout's claim at PRE_SEAL (OEWAS
anti-skill gate), emits the outcome as a Symbol Game trace turn, composts live-bout
blockers into OEEIS as CANDIDATE antibodies, and records the task-to-bout lineage in
Prompt Civilization. A REFUSE from the anti-skill gate routes the result to Refused;
the bout outcome itself is kept. A failing estate call is kept as a typed residual on
the result and never changes the outcome.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any, ClassVar

from adversary.domain.topology import SwarmCompositionV1
from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.connection import ConnectionReceiptV1
from adversary.domain.estate_ports import (
    ROUTING_TERMINAL_BY_BOUT_STATUS,
    AntiSkillDecisionV1,
    AntiSkillGatePort,
    BoutExecutionPort,
    CodaEvaluationPort,
    EnvelopeStorePort,
    EstateProbePort,
    ImmuneAntibodyPort,
    LggrGluingPort,
    PromptGenealogyPort,
    SgtTurnPort,
)
from adversary.domain.evidence import is_sha256_ref
from adversary.domain.instruction_ingress import instruction_request_digest
from adversary.domain.models import AdversaryBoutOutcomeV1, AdversaryBoutRequestV1
from adversary.domain.specialization import (
    ADVERSARY_BASE_SPECIALIZATION_V1,
    PortName,
    SpecializationError,
    SwarmSpecializationV1,
    SwarmTypeV1,
)
from adversary.domain.swarm_models import (
    CodaEvaluationResult,
    LggrGluingResult,
    ResearchEvidenceEnvelopeV1,
    ResearchTaskContractV1,
    AdversarySwarmDeliberation,
)
from adversary.use_cases.anti_skill_predispatch import (
    require_pre_dispatch_clear,
)
from workflows_agents_skills.domain.anti_skills.anti_skill_v2 import (
    AntiSkillSubjectV1,
)

_LOCUS = "adversary.use_cases.base_swarm.adversary_swarm"
SGT_TURN_SCHEMA = "core.adversary.sgt-bout-turn.v1"


@dataclass(frozen=True)
class AdversarySpineV1:
    """The estate ports one Adversary swarm runs on. Built only by the composition root."""

    bout: BoutExecutionPort
    coda: CodaEvaluationPort
    lggr: LggrGluingPort
    immune: ImmuneAntibodyPort
    genealogy: PromptGenealogyPort
    anti_skill: AntiSkillGatePort
    sgt: SgtTurnPort
    envelopes: EnvelopeStorePort
    #: Probe-only ports (the city runtime, seat transport, OEWAS learning, native host).
    extra_probes: tuple[EstateProbePort, ...] = ()
    swarm_type: SwarmTypeV1 = SwarmTypeV1.OPEN_TOPIC
    specialization: SwarmSpecializationV1 = ADVERSARY_BASE_SPECIALIZATION_V1

    def probes(self) -> tuple[EstateProbePort, ...]:
        return (
            self.bout,
            self.coda,
            self.lggr,
            self.immune,
            self.genealogy,
            self.anti_skill,
            self.sgt,
            self.envelopes,
            *self.extra_probes,
        )


@dataclass(frozen=True)
class SwarmBoutResultV1:
    specialization_id: str
    outcome: AdversaryBoutOutcomeV1
    routing_terminal: str
    seal_decision: AntiSkillDecisionV1 | None
    composted_antibody_ids: tuple[str, ...]
    estate_residuals: tuple[Refusal, ...]
    dispatch_decision: AntiSkillDecisionV1 | None = None
    authority_effect: str = "None"


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()


def deliberation_from_bout(outcome: AdversaryBoutOutcomeV1) -> AdversarySwarmDeliberation:
    """Project a native bout outcome; no narrative is invented beyond the receipt."""
    return AdversarySwarmDeliberation(
        scene_id=outcome.receipt_id,
        characters_invoked=[],
        divergent_proposals=[
            {
                "selected_candidate_id": outcome.selected_candidate_id,
                "disposition": outcome.disposition,
                "status": outcome.status,
            }
        ],
        nocebo_plunge_critique=None,
        surprise_gauge_break=None,
        red_team_fireproof_findings=[{"blocker": b} for b in outcome.authorization_blockers],
        terminal_verdict=outcome.terminal_verdict,
    )


def bout_claim_subject(
    producer_id: str,
    outcome: AdversaryBoutOutcomeV1,
    request: AdversaryBoutRequestV1,
) -> AntiSkillSubjectV1:
    """The bout's result as a typed OEWAS anti-skill subject.

    The native host verified the bout, so the verifier differs from the producing swarm.
    A fixture bout, or one that did not authorize, is only a proposal.
    """
    if not request.fixture_mode and not is_sha256_ref(outcome.receipt_id):
        raise ValueError("live bout receipt must be content-addressed")
    bounded = outcome.status == "AUTHORIZED" and not request.fixture_mode
    return AntiSkillSubjectV1(
        claim_scope=("candidate_result",),
        evidence_scope=(
            f"request:{instruction_request_digest(request)}",
            f"adversary_bout_receipt:{outcome.receipt_id}",
        ),
        producer_identity=producer_id,
        verifier_identity="core_symbol_game.adversary_bout",
        claim_mode="BOUNDED" if bounded else "PROPOSAL",
        requested_effect="ACTION_LICENSE" if request.request_external_admission else "NONE",
        nonclaims=("A Adversary bout result carries no authority.",),
    )


def seal_evidence_envelope(
    contract: ResearchTaskContractV1,
    coda: CodaEvaluationResult,
    lggr: LggrGluingResult,
    deliberation: AdversarySwarmDeliberation,
) -> ResearchEvidenceEnvelopeV1:
    body = {
        "contract": contract.to_dict(),
        "coda_evaluation": coda.to_dict(),
        "lggr_gluing": lggr.to_dict(),
        "adversary_deliberation": deliberation.to_dict(),
    }
    digest = _digest(body)
    return ResearchEvidenceEnvelopeV1(
        envelope_id=f"ENV_{contract.task_id}_{digest[:12]}",
        contract=contract,
        coda_evaluation=coda,
        lggr_gluing=lggr,
        adversary_deliberation=deliberation,
        envelope_digest=digest,
    )


class AdversarySwarm:
    """Base swarm. Subclasses override ``SPECIALIZATION`` and nothing else is required."""

    SPECIALIZATION: ClassVar[SwarmSpecializationV1] = ADVERSARY_BASE_SPECIALIZATION_V1

    def __init__(
        self, spine: AdversarySpineV1, *, specialization: SwarmSpecializationV1 | None = None
    ) -> None:
        if type(spine) is not AdversarySpineV1:
            raise TypeError("spine must be an exact AdversarySpineV1 from the composition root")
        if specialization is not None:
            if type(self) is not AdversarySwarm:
                raise TypeError("only the Adversary base accepts an instance workload profile")
            if type(specialization) is not SwarmSpecializationV1:
                raise TypeError("workload profile must be an exact SwarmSpecializationV1")
            self.SPECIALIZATION = specialization
        if type(self.SPECIALIZATION) is not SwarmSpecializationV1:
            raise TypeError(f"{type(self).__name__}.SPECIALIZATION must be SwarmSpecializationV1")
        self.spine = spine

    def get_composition(self) -> SwarmCompositionV1:
        return self.SPECIALIZATION.composition

    def _licensed(self, port: PortName) -> bool:
        return port in self.SPECIALIZATION.licensed_ports

    def _unlicensed(self, port: PortName) -> Refusal:
        return Refusal(
            "PORT_NOT_LICENSED",
            f"{self.SPECIALIZATION.specialization_id} does not license {port.value}",
            _LOCUS,
        )

    def connection_matrix(self, scratch_root: str) -> tuple[ConnectionReceiptV1, ...]:
        """Probe every estate port once, each in its own scratch subdirectory."""
        return tuple(
            probe.probe(f"{scratch_root}/{index:02d}_{probe.port.value}")
            for index, probe in enumerate(self.spine.probes())
        )

    def run_bout(
        self,
        objective: str,
        task_key: str,
        *,
        fixture_mode: bool = True,
        carrier_context: Mapping[str, Any] | None = None,
        request_external_admission: bool = False,
    ) -> Result[SwarmBoutResultV1, Refusal]:
        spec = self.SPECIALIZATION
        residuals: list[Refusal] = []
        try:
            request = AdversaryBoutRequestV1(
                objective=objective,
                task_key=task_key,
                max_rounds=spec.budget.max_rounds,
                fixture_mode=fixture_mode,
                request_external_admission=request_external_admission,
                carrier_context=dict(carrier_context or {}),
                compute_budget=spec.budget.compute_budget,
            )
        except (TypeError, ValueError) as exc:
            return Err(Refusal("BOUT_REQUEST_INVALID", str(exc), _LOCUS))
        if not self._licensed(PortName.NATIVE_BOUT):
            return Err(self._unlicensed(PortName.NATIVE_BOUT))
        dispatch_decision: AntiSkillDecisionV1 | None = None
        if not fixture_mode:
            if not self._licensed(PortName.OEWAS_ANTI_SKILL):
                return Err(self._unlicensed(PortName.OEWAS_ANTI_SKILL))
            dispatch = require_pre_dispatch_clear(
                self.spine.anti_skill, spec.specialization_id, request
            )
            if isinstance(dispatch, Err):
                return dispatch
            dispatch_decision = dispatch.value
        executed = self.spine.bout.execute_bout(request)
        if isinstance(executed, Err):
            return executed
        outcome = executed.value
        terminal = ROUTING_TERMINAL_BY_BOUT_STATUS[outcome.status]
        decision: AntiSkillDecisionV1 | None = None
        seal_bound = False
        if self._licensed(PortName.OEWAS_ANTI_SKILL):
            try:
                subject = bout_claim_subject(spec.specialization_id, outcome, request)
            except (TypeError, ValueError) as exc:
                screened = Err(Refusal(
                    "ANTI_SKILL_PRE_SEAL_SUBJECT_INVALID",
                    f"pre-seal subject could not bind exact bout evidence: {type(exc).__name__}",
                    _LOCUS,
                ))
            else:
                try:
                    screened = self.spine.anti_skill.evaluate("PRE_SEAL", subject.to_dict())
                except Exception as exc:
                    screened = Err(Refusal(
                        "ANTI_SKILL_PRE_SEAL_FAILED",
                        f"anti-skill gate raised {type(exc).__name__}",
                        _LOCUS,
                    ))
            if isinstance(screened, Err):
                residuals.append(screened.error)
            elif not isinstance(screened, Ok) or type(screened.value) is not AntiSkillDecisionV1:
                residuals.append(Refusal(
                    "ANTI_SKILL_PRE_SEAL_INVALID",
                    "anti-skill gate returned no typed pre-seal decision",
                    _LOCUS,
                ))
            else:
                decision = screened.value
                if decision.disposition == "REFUSE":
                    terminal = "Refused"
                seal_bound = (
                    decision.stage == "PRE_SEAL"
                    and decision.subject_id == subject.subject_id
                    and bool(decision.registry_id)
                    and bool(decision.activation_profile_digest)
                    and bool(decision.receipt_id)
                )
                if not seal_bound and not fixture_mode:
                    residuals.append(Refusal(
                        "ANTI_SKILL_PRE_SEAL_UNBOUND",
                        "pre-seal decision lacks stage, subject, registry, profile, or receipt binding",
                        _LOCUS,
                    ))
                elif dispatch_decision is not None and (
                    decision.registry_id != dispatch_decision.registry_id
                    or decision.activation_profile_digest
                    != dispatch_decision.activation_profile_digest
                ):
                    seal_bound = False
                    residuals.append(Refusal(
                        "ANTI_SKILL_PROFILE_DRIFT",
                        "pre-seal registry or activation profile differs from pre-dispatch",
                        _LOCUS,
                    ))
        if terminal == "CheckPassed" and (
            decision is None or decision.disposition != "CLEAR" or not seal_bound
        ):
            # A native checker may accept its own bounded candidate, but a
            # missing/held anti-skill gate cannot be silently promoted to the
            # outer Adversary routing pass.
            terminal = "RequiresLift"
            residuals.append(Refusal(
                "ANTI_SKILL_CLEARANCE_MISSING",
                "pre-seal anti-skill clearance is not a bound CLEAR",
                _LOCUS,
            ))
        if terminal not in spec.routing_terminals:
            residuals.append(
                Refusal(
                    "ROUTING_TERMINAL_NOT_LICENSED",
                    f"{terminal} is outside {spec.specialization_id}'s routing terminals",
                    _LOCUS,
                )
            )
        if self._licensed(PortName.SGT_EMISSION):
            turn = {
                "schema": SGT_TURN_SCHEMA,
                "specialization_id": spec.specialization_id,
                "task_key": task_key,
                "receipt_id": outcome.receipt_id,
                "status": outcome.status,
                "terminal_verdict": outcome.terminal_verdict,
                "routing_terminal": terminal,
                "fixture_mode": fixture_mode,
                "authority_effect": "None",
            }
            emitted = self.spine.sgt.record_turn(task_key, turn)
            if isinstance(emitted, Err):
                residuals.append(emitted.error)
        composted: tuple[str, ...] = ()
        if self._licensed(PortName.IMMUNE_ANTIBODIES) and not fixture_mode:
            defects = tuple(outcome.authorization_blockers)
            if defects:
                recorded = self.spine.immune.record_candidates(
                    defects, run_id=outcome.receipt_id, task_id=task_key
                )
                if isinstance(recorded, Err):
                    residuals.append(recorded.error)
                else:
                    composted = recorded.value
        if self._licensed(PortName.PROMPT_GENEALOGY):
            lineage = self.spine.genealogy.record_lineage(
                f"task:{task_key}",
                f"bout:{outcome.receipt_id}",
                tuple(dict.fromkeys(outcome.authorization_blockers)),
                f"{outcome.status}: {outcome.terminal_verdict}".strip(),
            )
            if isinstance(lineage, Err):
                residuals.append(lineage.error)
        return Ok(
            SwarmBoutResultV1(
                specialization_id=spec.specialization_id,
                outcome=outcome,
                routing_terminal=terminal,
                seal_decision=decision,
                composted_antibody_ids=composted,
                estate_residuals=tuple(residuals),
                dispatch_decision=dispatch_decision,
            )
        )

    def evaluate_coda(
        self,
        task_id: str,
        x_vector: Sequence[Fraction],
        coboundary_d0: Sequence[Sequence[Fraction]] | None = None,
        coboundary_d1: Sequence[Sequence[Fraction]] | None = None,
        cert_name: str | None = None,
    ) -> Result[CodaEvaluationResult, Refusal]:
        if not self._licensed(PortName.CODA_EVALUATION):
            return Err(self._unlicensed(PortName.CODA_EVALUATION))
        return self.spine.coda.evaluate(task_id, x_vector, coboundary_d0, coboundary_d1, cert_name)

    def evaluate_lggr(
        self,
        local_evaluators: Mapping[str, int],
        global_evaluator: int,
        corpus_samples: Sequence[tuple[Mapping[str, int], int]] | None = None,
        realizable_defects_in_blind_spot: bool = False,
    ) -> Result[LggrGluingResult, Refusal]:
        if not self._licensed(PortName.LGGR_GLUING):
            return Err(self._unlicensed(PortName.LGGR_GLUING))
        return self.spine.lggr.evaluate(
            local_evaluators, global_evaluator, corpus_samples, realizable_defects_in_blind_spot
        )

    def run_research_envelope(
        self,
        contract: ResearchTaskContractV1,
        *,
        x_vector: Sequence[Fraction],
        local_evaluators: Mapping[str, int],
        global_evaluator: int,
        coboundary_d0: Sequence[Sequence[Fraction]] | None = None,
        coboundary_d1: Sequence[Sequence[Fraction]] | None = None,
        corpus_samples: Sequence[tuple[Mapping[str, int], int]] | None = None,
        realizable_defects_in_blind_spot: bool = False,
        fixture_mode: bool = True,
        output_dir: str | None = None,
    ) -> Result[ResearchEvidenceEnvelopeV1, Refusal]:
        """CODA and LGGR through their ports, a native bout, then a sealed envelope."""
        for port in (PortName.NATIVE_BOUT, PortName.ENVELOPE_STORE):
            # Checked before any work: an unlicensed envelope must not cost a bout.
            if not self._licensed(port):
                return Err(self._unlicensed(port))
        coda = self.evaluate_coda(
            contract.task_id, x_vector, coboundary_d0, coboundary_d1, f"witness_{contract.task_id}"
        )
        if isinstance(coda, Err):
            return coda
        lggr = self.evaluate_lggr(
            local_evaluators, global_evaluator, corpus_samples, realizable_defects_in_blind_spot
        )
        if isinstance(lggr, Err):
            return lggr
        bout = self.run_bout(contract.objective, contract.task_id, fixture_mode=fixture_mode)
        if isinstance(bout, Err):
            return bout
        envelope = seal_evidence_envelope(
            contract, coda.value, lggr.value, deliberation_from_bout(bout.value.outcome)
        )
        persisted = self.spine.envelopes.persist(envelope, output_dir)
        if isinstance(persisted, Err):
            return persisted
        return Ok(replace(envelope, persisted_path=persisted.value))


def bind_adversary(adversary: object, specialization: SwarmSpecializationV1) -> AdversarySwarm:
    """Check that a held swarm is the specialisation its holder declares, and return it.

    Orchestrators that compose a Adversary swarm (rather than subclass it) call this in
    their constructor, so a holder cannot run on a swarm licensed for other ports.
    """
    if not isinstance(adversary, AdversarySwarm):
        raise TypeError("adversary must be an AdversarySwarm built by the composition root")
    held = adversary.SPECIALIZATION.specialization_id
    if held != specialization.specialization_id:
        raise SpecializationError(
            "SPECIALIZATION_MISMATCH",
            f"expected {specialization.specialization_id}, got {held}",
        )
    return adversary


__all__ = [
    "SGT_TURN_SCHEMA",
    "AdversarySwarm",
    "SwarmBoutResultV1",
    "AdversarySpineV1",
    "bind_adversary",
    "bout_claim_subject",
    "deliberation_from_bout",
    "seal_evidence_envelope",
]
