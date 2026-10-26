"""Master Operad Swarm Orchestrator.

Routes execution turns between specialist personas across Techne, Panepistimion,
Ooutwire Bureau, and Thanatos under 10-colour operadic composition laws. The persona
turns are local screens; a review closes at the Woland terminal gate. The orchestrator
holds a paper-review Woland swarm, and consensus requires both no screen objection and
a bout that reaches ``CheckPassed``.

The hand-waving lint and the unstated-premise questions are deterministic text checks.
Their findings go into the bout as evidence for the seats that own the criticism: the
critic (Act II, ``seat_koroviev``) and the gauge break (Act IV, ``seat_margarita``). They
travel in ``carrier_context["screen_evidence"]`` and in the objective, which the critic
reads.

AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import ClassVar, List, Optional, Sequence

from omega_engine_operations.domain.rop.result import Err
from omega_engine_woland.domain.specialization import SwarmSpecializationV1
from omega_engine_woland.use_cases.base_swarm.specializations import OmegaEnginePaperReviewSwarm
from omega_engine_woland.use_cases.base_swarm.woland_swarm import (
    OmegaEngineWolandSwarm,
    bind_woland,
)

from ..domain.models.claim_ledger import ClaimLedger
from ..domain.models.paper_spec import PaperSpecification
from ..domain.swarms.deliberation import (
    ConsensusStatus,
    DeliberationBout,
    PeerReviewWitnessRecord,
    SwarmDeliberationTurn,
)
from ..domain.swarms.operad_colours import OperadColour
from ..domain.swarms.personas import SPECIALIST_PERSONAS
from .claim_hygiene_auditor import ClaimHygieneAuditor
from .hand_waving_lint import HandWavingLint
from .unstated_premise_questions import UnstatedPremiseQuestions

CRITIC_SEAT = "seat_koroviev"
GAUGE_BREAK_SEAT = "seat_margarita"


class SwarmOrchestrator:
    """Coordinates multi-perspective review bouts across the specialist swarm."""

    SPECIALIZATION: ClassVar[SwarmSpecializationV1] = OmegaEnginePaperReviewSwarm.SPECIALIZATION

    def __init__(self, woland: OmegaEngineWolandSwarm) -> None:
        self.woland = bind_woland(woland, self.SPECIALIZATION)
        self.personas = SPECIALIST_PERSONAS

    def run_review_bout(
        self,
        paper: PaperSpecification,
        claim_ledger: Optional[ClaimLedger],
        monograph_markdown: str,
        *,
        fixture_mode: bool = True,
    ) -> DeliberationBout:
        bout_id = f"BOUT_{paper.paper_id}"
        turns: List[SwarmDeliberationTurn] = []
        objections: List[str] = []

        turn_idx = 0

        # Turn 1: Techne Principal Architect (Structure & Ports)
        p_arch = self.personas["techne_principal_architect"]
        arch_pass = bool(paper.monograph and len(paper.monograph.sections) >= 6)
        arch_findings = (
            ("Architecture conforms to 6-section atlas structure.",)
            if arch_pass
            else ("Monograph has fewer than 6 standard sections.",)
        )
        if not arch_pass:
            objections.append("Techne: Inadequate monograph structure.")
        turns.append(
            SwarmDeliberationTurn(
                persona_id=p_arch.persona_id,
                turn_index=turn_idx,
                input_colour=OperadColour.PAPER,
                output_colour=OperadColour.AUDIT,
                passed_checks=arch_pass,
                findings=arch_findings,
                authority_effect="None",
            )
        )
        turn_idx += 1

        # Turn 2: Thanatos Claim Hygiene & BS Firewall
        p_bs = self.personas["thanatos_bs_firewall"]
        ch_report = ClaimHygieneAuditor.audit_text(monograph_markdown)
        ch_findings = tuple(f"Line {v.line_number}: '{v.matched_word}' -> suggest '{v.suggested_replacement}'" for v in ch_report.violations)
        if not ch_report.passed:
            objections.append(f"Thanatos: {ch_report.total_violations} forbidden hype words detected.")
        turns.append(
            SwarmDeliberationTurn(
                persona_id=p_bs.persona_id,
                turn_index=turn_idx,
                input_colour=OperadColour.PAPER,
                output_colour=OperadColour.AUDIT,
                passed_checks=ch_report.passed,
                findings=ch_findings or ("Zero forbidden hype words found.",),
                authority_effect="None",
            )
        )
        turn_idx += 1

        # Turn 3: hand-waving lint (Old Man ChatGPT persona)
        p_red = self.personas["thanatos_old_man_chatgpt"]
        red_report = HandWavingLint.scan(monograph_markdown)
        red_findings = tuple(f"Line {f.line_number}: {f.objection}" for f in red_report.findings)
        if not red_report.passed:
            objections.append(f"Old Man ChatGPT: {red_report.blocking_count} hand-waving assertions detected.")
        turns.append(
            SwarmDeliberationTurn(
                persona_id=p_red.persona_id,
                turn_index=turn_idx,
                input_colour=OperadColour.PAPER,
                output_colour=OperadColour.AUDIT,
                passed_checks=red_report.passed,
                findings=red_findings or ("Zero hand-waving assertions detected.",),
                authority_effect="None",
            )
        )
        turn_idx += 1

        # Turn 4: Panepistimion Peer Review Reader
        p_reader = self.personas["panep_paper_reader"]
        reader_pass = bool(paper.abstract.strip())
        reader_findings = ("Monograph abstract provides scoped problem formulation.",) if reader_pass else ("Empty abstract.",)
        turns.append(
            SwarmDeliberationTurn(
                persona_id=p_reader.persona_id,
                turn_index=turn_idx,
                input_colour=OperadColour.PAPER,
                output_colour=OperadColour.AUDIT,
                passed_checks=reader_pass,
                findings=reader_findings,
                authority_effect="None",
            )
        )
        turn_idx += 1

        # Turn 5: unstated-premise questions (Ooutwire interrogator persona)
        p_soc = self.personas["ow_interrogator"]
        soc_questions = UnstatedPremiseQuestions.ask(paper.abstract, monograph_markdown)
        soc_findings = tuple(f"[{q.question_id}] {q.premise_under_attack}: {q.inquiry}" for q in soc_questions)
        turns.append(
            SwarmDeliberationTurn(
                persona_id=p_soc.persona_id,
                turn_index=turn_idx,
                input_colour=OperadColour.PAPER,
                output_colour=OperadColour.AUDIT,
                passed_checks=len(soc_questions) == 0,
                findings=soc_findings or ("No hidden unexamined premises identified.",),
                authority_effect="None",
            )
        )

        screen_evidence = {CRITIC_SEAT: list(red_findings), GAUGE_BREAK_SEAT: list(soc_findings)}
        gated = self.woland.run_bout(
            f"Review paper {paper.paper_id} ({paper.title}). "
            f"Screen objections: {'; '.join(objections) or 'none'}. "
            f"Hand-waving lint findings for the critic: {_listed(red_findings)}. "
            f"Unstated-premise questions for the gauge break: {_listed(soc_findings)}.",
            bout_id,
            fixture_mode=fixture_mode,
            carrier_context={"screen_evidence": screen_evidence},
        )
        terminal, receipt_id = "", ""
        if isinstance(gated, Err):
            objections.append(f"Woland: {gated.error.code}")
        else:
            terminal, receipt_id = gated.value.routing_terminal, gated.value.outcome.receipt_id
            if terminal != "CheckPassed":
                objections.append(f"Woland: the review bout ended on {terminal}")
        status = ConsensusStatus.CONSENSUS_REACHED if len(objections) == 0 else ConsensusStatus.DIALETHEIC_TENSION

        return DeliberationBout(
            bout_id=bout_id,
            paper_id=paper.paper_id,
            turns=tuple(turns),
            status=status,
            unresolved_objections=tuple(objections),
            routing_terminal=terminal,
            woland_receipt_id=receipt_id,
        )

    def audit_review_obligations(
        self,
        paper_dir: Path,
        monograph_path: Path,
        claim_ledger_path: Optional[Path] = None,
        paper_id: str = "coda_q",
        snapshot_sha256: str = "",
        emit_witnesses_dir: Optional[Path] = None,
        auto_remediate: bool = False,
        max_remediation_rounds: int = 0,
    ) -> DeliberationBout:
        """Screen semantic obligations without claiming independent peer review.

        File presence, keywords, a local test name, or a Lean source file cannot
        establish mathematical adequacy, proof validity, citation support, or
        claim-to-evidence parity. This method never edits a manuscript.
        """
        from .paper_review.checklist import identity, snapshot

        paper_dir = Path(paper_dir).resolve()
        monograph_path = Path(monograph_path).resolve()
        if not monograph_path.is_file() or not monograph_path.is_relative_to(paper_dir):
            raise ValueError("Monograph must be a file inside the reviewed package")
        if claim_ledger_path is not None:
            claim_ledger_path = Path(claim_ledger_path).resolve()
            if not claim_ledger_path.is_relative_to(paper_dir):
                raise ValueError("Claim ledger must be inside the reviewed package")
        actual_sha, _ = identity(snapshot(paper_dir))
        if snapshot_sha256 and snapshot_sha256 != actual_sha:
            raise ValueError("Supplied snapshot digest does not match current release bytes")
        if paper_id in ("coda_q", "P001") and paper_dir.name not in ("q", "P001"):
            paper_id = paper_dir.name
        if emit_witnesses_dir is not None:
            emit_witnesses_dir = Path(emit_witnesses_dir).resolve()
            if emit_witnesses_dir.is_relative_to(paper_dir):
                raise ValueError("Review records must be written outside the paper package")

        ledger = claim_ledger_path or next(iter(sorted(paper_dir.glob("*claim_ledger.md"))), None)
        context = (
            f"Screened exact package snapshot {actual_sha}; monograph present; "
            f"claim ledger {'present' if ledger and ledger.is_file() else 'missing'}. "
            "No semantic or execution conclusion follows from these presence checks."
        )
        obligations = (
            ("B01", "Definitions, domains and hypotheses are mathematically adequate", "panep_math_physics_prof", OperadColour.PAPER),
            ("B02", "Proof steps establish the stated conclusions", "panep_math_physics_prof", OperadColour.PROOF),
            ("B03", "Degenerate and adversarial mathematical cases were examined", "thanatos_old_man_chatgpt", OperadColour.CODE),
            ("B04", "Evidence ceilings match all substantive claims", "thanatos_bs_firewall", OperadColour.PAPER),
            ("B05", "Citations resolve to the claimed external works and support their use", "panep_paper_reader", OperadColour.PAPER),
            ("B06", "Limitations and open obligations remain explicit", "ow_interrogator", OperadColour.CONTRACT),
            ("D02", "Material claims and evidence map in both directions", "thanatos_receipt_auditor", OperadColour.LEDGER),
            ("D04", "Formal statements match prose and ledger scope", "techne_principal_architect", OperadColour.PAPER),
        )
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        turns: List[SwarmDeliberationTurn] = []
        records: List[PeerReviewWitnessRecord] = []
        objections: List[str] = []
        for index, (check_id, obligation, persona_id, colour) in enumerate(obligations):
            persona = self.personas[persona_id]
            finding = f"{context} {check_id} requires independent assessment: {obligation}."
            turns.append(SwarmDeliberationTurn(
                persona_id=persona.persona_id,
                turn_index=index,
                input_colour=colour,
                output_colour=OperadColour.AUDIT,
                passed_checks=False,
                findings=(finding,),
                authority_effect="None",
            ))
            records.append(PeerReviewWitnessRecord(
                schema="omega.peer_review_screen.v1",
                check_id=check_id,
                obligation=obligation,
                auditor_persona=persona.persona_id,
                governing_skill=persona.governing_skill,
                source_colour=colour.value,
                target_colour=OperadColour.AUDIT.value,
                paper_id=paper_id,
                snapshot_sha256=actual_sha,
                timestamp_utc=now_utc,
                status="NOT_VERIFIED",
                findings=(finding,),
                authority_effect="None",
            ))
            objections.append(f"{check_id}: independent assessment required")
        if emit_witnesses_dir is not None:
            emit_witnesses_dir.mkdir(parents=True, exist_ok=True)
            for record in records:
                with (emit_witnesses_dir / f"witness_{record.check_id}.json").open("x", encoding="utf-8") as stream:
                    json.dump(record.to_dict(), stream, indent=2)
                    stream.write("\n")
        return DeliberationBout(
            bout_id=f"BOUT_REVIEW_OBLIGATIONS_{paper_id.upper()}",
            paper_id=paper_id,
            turns=tuple(turns),
            status=ConsensusStatus.DIALETHEIC_TENSION,
            unresolved_objections=tuple(objections),
            witness_records=tuple(records),
        )


# The bout refuses an objective over its text ceiling; the full lists are in the carrier.
_LISTED_IN_OBJECTIVE = 12


def _listed(findings: Sequence[str]) -> str:
    shown = "; ".join(findings[:_LISTED_IN_OBJECTIVE]) or "none"
    more = len(findings) - _LISTED_IN_OBJECTIVE
    return f"{shown} (and {more} more in the carrier)" if more > 0 else shown
