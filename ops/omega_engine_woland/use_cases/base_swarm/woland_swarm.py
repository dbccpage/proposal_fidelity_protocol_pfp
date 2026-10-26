"""OmegaEngineWolandSwarm: the one base class every swarm specialises.

The base owns no adapters. It receives a ``WolandSpineV1`` of estate ports from the
composition root (``omega_engine_woland.runtime.build_woland_swarm``) and declares a
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

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.connection import ConnectionReceiptV1
from omega_engine_woland.domain.estate_ports import (
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
from omega_engine_woland.domain.evidence import is_sha256_ref
from omega_engine_woland.domain.instruction_ingress import instruction_request_digest
from omega_engine_woland.domain.models import WolandBoutOutcomeV1, WolandBoutRequestV1
from omega_engine_woland.domain.specialization import (
    WOLAND_BASE_SPECIALIZATION_V1,
    PortName,
    SpecializationError,
    SwarmSpecializationV1,
    SwarmTypeV1,
)
from omega_engine_woland.domain.swarm_models import (
    CodaEvaluationResult,
    LggrGluingResult,
    ResearchEvidenceEnvelopeV1,
    ResearchTaskContractV1,
    WolandSwarmDeliberation,
)
from omega_engine_woland.stage.domain.topology import SwarmCompositionV1
from omega_engine_woland.use_cases.anti_skill_predispatch import (
    require_pre_dispatch_clear,
)
from omega_engine_operads.domain.anti_skills.anti_skill_v2 import (
    AntiSkillSubjectV1,
)

_LOCUS = "omega_engine_woland.use_cases.base_swarm.woland_swarm"
SGT_TURN_SCHEMA = "omega.woland.sgt-bout-turn.v1"


@dataclass(frozen=True)
class WolandSpineV1:
    """The estate ports one Woland swarm runs on. Built only by the composition root."""

    bout: BoutExecutionPort
    coda: CodaEvaluationPort
    lggr: LggrGluingPort
    immune: ImmuneAntibodyPort
    genealogy: PromptGenealogyPort
    anti_skill: AntiSkillGatePort
    sgt: SgtTurnPort
    envelopes: EnvelopeStorePort
    #: Probe-only ports (stage runtime, seat transport, OEWAS learning, native host).
    extra_probes: tuple[EstateProbePort, ...] = ()
    swarm_type: SwarmTypeV1 = SwarmTypeV1.OPEN_TOPIC
    specialization: SwarmSpecializationV1 = WOLAND_BASE_SPECIALIZATION_V1

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
    outcome: WolandBoutOutcomeV1
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


def deliberation_from_bout(outcome: WolandBoutOutcomeV1) -> WolandSwarmDeliberation:
    """Project a native bout outcome; no narrative is invented beyond the receipt."""
    return WolandSwarmDeliberation(
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
        old_man_fireproof_findings=[{"blocker": b} for b in outcome.authorization_blockers],
        terminal_verdict=outcome.terminal_verdict,
    )


def bout_claim_subject(
    producer_id: str,
    outcome: WolandBoutOutcomeV1,
    request: WolandBoutRequestV1,
) -> AntiSkillSubjectV1:
    """The bout's result as a typed OEWAS anti-skill subject.

    The native host verified the bout, so the verifier differs from the producing swarm.
    A fixture bout, or one that did not authorize, is only a proposal.
    """
    if not request.fixture_mode and outcome.task_key != request.task_key:
        raise ValueError("live bout outcome belongs to another task")
    if not request.fixture_mode and not is_sha256_ref(outcome.receipt_id):
        raise ValueError("live bout receipt must be content-addressed")
    bounded = outcome.status == "AUTHORIZED" and not request.fixture_mode
    return AntiSkillSubjectV1(
        claim_scope=("candidate_result",),
        evidence_scope=(
            f"task:{request.task_key}",
            f"request:{instruction_request_digest(request)}",
            f"woland_bout_receipt:{outcome.receipt_id}",
        ),
        producer_identity=producer_id,
        verifier_identity="omega_symbol_game.woland_bout",
        claim_mode="BOUNDED" if bounded else "PROPOSAL",
        requested_effect="ACTION_LICENSE" if request.request_external_admission else "NONE",
        nonclaims=("A Woland bout result carries no authority.",),
    )


def seal_evidence_envelope(
    contract: ResearchTaskContractV1,
    coda: CodaEvaluationResult,
    lggr: LggrGluingResult,
    deliberation: WolandSwarmDeliberation,
) -> ResearchEvidenceEnvelopeV1:
    body = {
        "contract": contract.to_dict(),
        "coda_evaluation": coda.to_dict(),
        "lggr_gluing": lggr.to_dict(),
        "woland_deliberation": deliberation.to_dict(),
    }
    digest = _digest(body)
    return ResearchEvidenceEnvelopeV1(
        envelope_id=f"ENV_{contract.task_id}_{digest[:12]}",
        contract=contract,
        coda_evaluation=coda,
        lggr_gluing=lggr,
        woland_deliberation=deliberation,
        envelope_digest=digest,
    )


class OmegaEngineWolandSwarm:
    """Base swarm. Subclasses override ``SPECIALIZATION`` and nothing else is required."""

    SPECIALIZATION: ClassVar[SwarmSpecializationV1] = WOLAND_BASE_SPECIALIZATION_V1

    def __init__(
        self, spine: WolandSpineV1, *, specialization: SwarmSpecializationV1 | None = None
    ) -> None:
        if type(spine) is not WolandSpineV1:
            raise TypeError("spine must be an exact WolandSpineV1 from the composition root")
        if specialization is not None:
            if type(self) is not OmegaEngineWolandSwarm:
                raise TypeError("only the Woland base accepts an instance workload profile")
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
        max_rounds: int | None = None,
        compute_budget: int | None = None,
    ) -> Result[SwarmBoutResultV1, Refusal]:
        spec = self.SPECIALIZATION
        residuals: list[Refusal] = []
        rounds = spec.budget.max_rounds if max_rounds is None else max_rounds
        compute = spec.budget.compute_budget if compute_budget is None else compute_budget
        if (
            type(rounds) is not int
            or not 1 <= rounds <= spec.budget.max_rounds
            or type(compute) is not int
            or not 1 <= compute <= spec.budget.compute_budget
        ):
            return Err(
                Refusal(
                    "BOUT_BUDGET_EXCEEDS_PROFILE",
                    "request must narrow the workload profile round and compute ceilings",
                    _LOCUS,
                )
            )
        if not fixture_mode:
            live = (carrier_context or {}).get("live_execution", {})
            cap = live.get("max_cost_microusd") if isinstance(live, Mapping) else None
            if type(cap) is not int or not 1 <= cap <= spec.budget.max_cost_microusd:
                return Err(
                    Refusal(
                        "BOUT_PAID_BUDGET_UNADMITTED",
                        "live request needs an explicit signed cap within its workload ceiling",
                        _LOCUS,
                    )
                )
        try:
            request = WolandBoutRequestV1(
                objective=objective,
                task_key=task_key,
                max_rounds=rounds,
                fixture_mode=fixture_mode,
                request_external_admission=request_external_admission,
                carrier_context=dict(carrier_context or {}),
                compute_budget=compute,
                swarm_type=self.spine.swarm_type,
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
        if not fixture_mode and outcome.task_key != request.task_key:
            return Err(
                Refusal(
                    "BOUT_OUTCOME_TASK_MISMATCH",
                    "bout outcome belongs to another task; no estate writes were attempted",
                    _LOCUS,
                )
            )
        terminal = ROUTING_TERMINAL_BY_BOUT_STATUS[outcome.status]
        decision: AntiSkillDecisionV1 | None = None
        seal_bound = False
        if self._licensed(PortName.OEWAS_ANTI_SKILL):
            try:
                subject = bout_claim_subject(spec.specialization_id, outcome, request)
            except (TypeError, ValueError) as exc:
                screened = Err(
                    Refusal(
                        "ANTI_SKILL_PRE_SEAL_SUBJECT_INVALID",
                        f"pre-seal subject could not bind exact bout evidence: {type(exc).__name__}",
                        _LOCUS,
                    )
                )
            else:
                try:
                    screened = self.spine.anti_skill.evaluate("PRE_SEAL", subject.to_dict())
                except Exception as exc:
                    screened = Err(
                        Refusal(
                            "ANTI_SKILL_PRE_SEAL_FAILED",
                            f"anti-skill gate raised {type(exc).__name__}",
                            _LOCUS,
                        )
                    )
            if isinstance(screened, Err):
                residuals.append(screened.error)
            elif not isinstance(screened, Ok) or type(screened.value) is not AntiSkillDecisionV1:
                residuals.append(
                    Refusal(
                        "ANTI_SKILL_PRE_SEAL_INVALID",
                        "anti-skill gate returned no typed pre-seal decision",
                        _LOCUS,
                    )
                )
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
                    residuals.append(
                        Refusal(
                            "ANTI_SKILL_PRE_SEAL_UNBOUND",
                            "pre-seal decision lacks stage, subject, registry, profile, or receipt binding",
                            _LOCUS,
                        )
                    )
                elif dispatch_decision is not None and (
                    decision.registry_id != dispatch_decision.registry_id
                    or decision.activation_profile_digest
                    != dispatch_decision.activation_profile_digest
                ):
                    seal_bound = False
                    residuals.append(
                        Refusal(
                            "ANTI_SKILL_PROFILE_DRIFT",
                            "pre-seal registry or activation profile differs from pre-dispatch",
                            _LOCUS,
                        )
                    )
        if terminal == "CheckPassed" and (
            decision is None or decision.disposition != "CLEAR" or not seal_bound
        ):
            # A native checker may accept its own bounded candidate, but a
            # missing/held anti-skill gate cannot be silently promoted to the
            # outer Woland routing pass.
            terminal = "RequiresLift"
            residuals.append(
                Refusal(
                    "ANTI_SKILL_CLEARANCE_MISSING",
                    "pre-seal anti-skill clearance is not a bound CLEAR",
                    _LOCUS,
                )
            )
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
        *, binding=None,
    ) -> Result[CodaEvaluationResult, Refusal]:
        if not self._licensed(PortName.CODA_EVALUATION):
            return Err(self._unlicensed(PortName.CODA_EVALUATION))
        options = {"binding": binding} if binding is not None else {}
        return self.spine.coda.evaluate(task_id, x_vector, coboundary_d0, coboundary_d1, cert_name, **options)

    def evaluate_lggr(
        self,
        local_evaluators: Mapping[str, int],
        global_evaluator: int,
        corpus_samples: Sequence[tuple[Mapping[str, int], int]] | None = None,
        *, carrier=None, binding=None, soundness=None,
    ) -> Result[LggrGluingResult, Refusal]:
        if not self._licensed(PortName.LGGR_GLUING):
            return Err(self._unlicensed(PortName.LGGR_GLUING))
        options = {key: value for key, value in (("carrier", carrier), ("binding", binding),
                                                 ("soundness", soundness)) if value is not None}
        return self.spine.lggr.evaluate(local_evaluators, global_evaluator, corpus_samples, **options)

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
        lggr_soundness=None,
        fixture_mode: bool = True,
        output_dir: str | None = None,
        lggr_carrier=None,
        math_binding=None,
    ) -> Result[ResearchEvidenceEnvelopeV1, Refusal]:
        """CODA and LGGR through their ports, a native bout, then a sealed envelope."""
        for port in (PortName.NATIVE_BOUT, PortName.ENVELOPE_STORE):
            # Checked before any work: an unlicensed envelope must not cost a bout.
            if not self._licensed(port):
                return Err(self._unlicensed(port))
        binding = math_binding or {"source_id": contract.contract_digest(),
            "candidate_id": hashlib.sha256(json.dumps({"x": list(map(str, x_vector)),
                "d0": [[str(cell) for cell in row] for row in coboundary_d0] if coboundary_d0 is not None else None,
                "d1": [[str(cell) for cell in row] for row in coboundary_d1] if coboundary_d1 is not None else None,
                "lggr": lggr_carrier}, sort_keys=True).encode()).hexdigest(),
            "question": contract.objective, "operation_id": "woland.research-envelope.finite.v1",
            "checker_id": "independent-rational-replay.v1"}
        coda = self.evaluate_coda(
            contract.task_id, x_vector, coboundary_d0, coboundary_d1, f"witness_{contract.task_id}",
            binding=binding,
        )
        if isinstance(coda, Err):
            return coda
        lggr = self.evaluate_lggr(
            local_evaluators, global_evaluator, corpus_samples,
            carrier=lggr_carrier, binding=binding, soundness=lggr_soundness,
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


def bind_woland(woland: object, specialization: SwarmSpecializationV1) -> OmegaEngineWolandSwarm:
    """Check that a held swarm is the specialisation its holder declares, and return it.

    Orchestrators that compose a Woland swarm (rather than subclass it) call this in
    their constructor, so a holder cannot run on a swarm licensed for other ports.
    """
    if not isinstance(woland, OmegaEngineWolandSwarm):
        raise TypeError("woland must be an OmegaEngineWolandSwarm built by the composition root")
    held = woland.SPECIALIZATION.specialization_id
    if held != specialization.specialization_id:
        raise SpecializationError(
            "SPECIALIZATION_MISMATCH",
            f"expected {specialization.specialization_id}, got {held}",
        )
    return woland


__all__ = [
    "SGT_TURN_SCHEMA",
    "OmegaEngineWolandSwarm",
    "SwarmBoutResultV1",
    "WolandSpineV1",
    "bind_woland",
    "bout_claim_subject",
    "deliberation_from_bout",
    "seal_evidence_envelope",
]
