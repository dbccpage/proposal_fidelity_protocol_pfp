"""Governing Councils Deliberation & Non-Interference Protocols Bout Use Case.

Under swarm_type="governing-councils", Woland and his Retinue attend the meetings of the
repository's governing councils in omega_engine_governance.
The Retinue observes, mocks false certainty, and harvests open obligations into the scars ledger,
while strictly abstaining from casting votes (zero motion votes cast).

AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.fixture_input_context import (
    FixtureInputContextError,
    detach_fixture_input_context,
)
from omega_engine_woland.domain.models import (
    WolandBoutOutcomeV1,
    WolandBoutRequestV1,
)
from omega_engine_woland.domain.native import NativeOperationPort
from omega_engine_woland.domain.residual_algebra.character_operators import (
    CharacterOperatorRegistry,
)
from omega_engine_woland.domain.residual_algebra.dialogue_synthesizer import (
    DialogueSynthesizer,
)
from omega_engine_woland.domain.residual_algebra.licensing_boundary import (
    LicensingBoundary,
    ValuationReceipt,
)
from omega_engine_woland.domain.residual_algebra.protocols import (
    ObstructionValuatorProtocol,
)
from omega_engine_woland.domain.residual_algebra.residual_sorts import (
    Residual1Cochain,
)
from omega_engine_woland.domain.specialization import SwarmTypeV1
from omega_engine_woland.use_cases.persistence import (
    persist_bout_run_folder,
    run_directory_name,
)
from omega_engine_woland.use_cases.persistence import (
    reported_receipt_id as content_addressed_receipt_id,
)
from omega_engine_woland.use_cases.software_dev_bout_use_case import (
    DefaultObstructionValuator,
    RetinueRoleMappingV1,
)

_LOCUS = "omega_engine_woland.use_cases.governing_councils_bout_use_case"


GOVERNING_COUNCILS_RETINUE_MAP: dict[str, RetinueRoleMappingV1] = {
    "woland": RetinueRoleMappingV1(
        persona="Woland",
        cognitive_operator="E_terminal",
        residual_sort="exactness_witness",
        software_dev_role="Sovereign Observer & Dialectical Judge",
        mapped_skills=(),
        description="Prowls the colonnade; reminds councils of Pilate's migraine and the shame of hand-washing.",
    ),
    "koroviev": RetinueRoleMappingV1(
        persona="Koroviev",
        cognitive_operator="E_syntactic",
        residual_sort="gauge_residual",
        software_dev_role="Arithmetic Satirist & Quorum Challenger",
        mapped_skills=("techne-docs-lint-hunter-killer",),
        description="Punctures fake consensus and soft compromises with loud, mocking arithmetic.",
    ),
    "begemot": RetinueRoleMappingV1(
        persona="Begemot",
        cognitive_operator="E_semantic",
        residual_sort="boundary_defect",
        software_dev_role="Receipt Unmasker & Jester of Truth",
        mapped_skills=("techne-adversarial-refusal-bypass-auditor",),
        description="Pulls back the curtain on unearned claims and demands genuine receipts.",
    ),
    "azazello": RetinueRoleMappingV1(
        persona="Azazello",
        cognitive_operator="E_falsification",
        residual_sort="falsification_witness",
        software_dev_role="Containment Sentinel & Blackrod Liaison",
        mapped_skills=("thanatos-nemesis",),
        description="Fangs bared against bureaucratic posturing; enforces physical containment.",
    ),
    "hella": RetinueRoleMappingV1(
        persona="Hella",
        cognitive_operator="E_hygiene",
        residual_sort="hygiene_residual",
        software_dev_role="Stateless Scribe & Docket Recorder",
        mapped_skills=("auto-docs",),
        description="Records agenda items and minutes without distortion or editorial bias.",
    ),
    "master": RetinueRoleMappingV1(
        persona="The Master",
        cognitive_operator="E_formal",
        residual_sort="exactness_witness",
        software_dev_role="Axiomatic Conscience & Core Scholar",
        mapped_skills=("panep-math-and-physics-prof",),
        description="Distinguishes pure theory from empirical ground truth; whispers eternal formulas.",
    ),
    "margarita": RetinueRoleMappingV1(
        persona="Margarita",
        cognitive_operator="E_placebo",
        residual_sort="prior_lock_residual",
        software_dev_role="Courage Advocate & Deadlock Breaker",
        mapped_skills=("ow-bureau-gauge-breaks",),
        description="Inspires moral courage against administrative paralysis and fear of failure.",
    ),
    "jeremy": RetinueRoleMappingV1(
        persona="Jeremy",
        cognitive_operator="E_yankee_solver",
        residual_sort="executable_runtime",
        software_dev_role="Ground Reality Anchor & Practical Solver",
        mapped_skills=("panep-cs-prof",),
        description="Hyperbole-intolerant filter demanding executable runtimes and honest metrics.",
    ),
    "liudmila": RetinueRoleMappingV1(
        persona="Liudmila",
        cognitive_operator="E_luda_resilience",
        residual_sort="stable_equilibrium",
        software_dev_role="Soviet Resilience & Risk Sentinel",
        mapped_skills=("techne-svp", "techne-vp"),
        description="Monitors procedural drift and controls risk escalation across council bodies.",
    ),
    "polina": RetinueRoleMappingV1(
        persona="Polina",
        cognitive_operator="E_polina_gauge_breaker",
        residual_sort="gauge_break",
        software_dev_role="Southern Wit & Rhetoric Puncturer",
        mapped_skills=("glossa-claim-hygiene-linter",),
        description="Cuts through hollow resolutions with sharp, uncompromising Southern wit.",
    ),
    "yaroslava": RetinueRoleMappingV1(
        persona="Yaroslava",
        cognitive_operator="E_yaroslava_discipline",
        residual_sort="methodical_completion",
        software_dev_role="Obligation Custodian & Scars Registrar",
        mapped_skills=("techne-mutation-evidence-custody",),
        description="Collects open obligations and unaddressed defects into persistent registers.",
    ),
    "stravinsky": RetinueRoleMappingV1(
        persona="Dr. Stravinsky",
        cognitive_operator="E_flow",
        residual_sort="quarantine",
        software_dev_role="Deliberative Sanatorium Director",
        mapped_skills=("techne-silent-failure-hunter",),
        description="Quarantines circular debates, filibusters, and unresolvable administrative deadlocks.",
    ),
    "ratslayer": RetinueRoleMappingV1(
        persona="Centurion Mark Ratslayer",
        cognitive_operator="E_ratslayer",
        residual_sort="physical_constraint",
        software_dev_role="Physical Fence & Order Enforcer",
        mapped_skills=(),
        description="Enforces temporal ceilings, meeting duration bounds, and orderly proceedings.",
    ),
    "pilate": RetinueRoleMappingV1(
        persona="Pontius Pilate",
        cognitive_operator="E_pilate",
        residual_sort="governance_audit",
        software_dev_role="Governance Auditor & Anti-Handwashing Sentinel",
        mapped_skills=("techne-adversarial-refusal-bypass-auditor",),
        description="Exposes bureaucratic cowardice, delegation of blame, and moral evasion.",
    ),
}


@dataclass(frozen=True)
class CouncilObligationV1:
    """An open obligation or unaddressed defect discovered during council observation."""

    obligation_id: str
    council: str
    description: str
    severity: str
    assigned_role: str
    locus: str


@dataclass(frozen=True)
class GoverningCouncilBeatExecutionV1:
    act_index: int
    act_title: str
    speaker_key: str
    persona: str
    cue: str
    dialogue: str
    operator_tag: str
    residual_sort: str
    carrier_delta: dict[str, Any]
    cochain: Residual1Cochain


class GoverningCouncilsBoutUseCase:
    """Theatrical and governance 7-Act observation bout for Anomalon Councils."""

    def __init__(
        self,
        repo_root: Path | str | None = None,
        *,
        synthesizer: DialogueSynthesizer | None = None,
        valuator: ObstructionValuatorProtocol | None = None,
        native_support: NativeOperationPort,
    ) -> None:
        self._native_support = native_support
        self.repo_root = Path(repo_root) if repo_root is not None else Path.cwd()
        self.synthesizer = synthesizer or DialogueSynthesizer()
        self.valuator = valuator or DefaultObstructionValuator()

    def execute_bout(
        self,
        request: WolandBoutRequestV1,
        *,
        output_dir: Path | str | None = None,
    ) -> Result[WolandBoutOutcomeV1, Refusal]:
        try:
            input_context = detach_fixture_input_context(request.carrier_context)
        except FixtureInputContextError as exc:
            return Err(Refusal(exc.code, str(exc), _LOCUS))

        target_root = Path(output_dir) if output_dir is not None else (
            self.repo_root / canonical_intelligence_route("_intelligence/_woland")
        )
        run_folder = target_root / "runs" / run_directory_name(request.task_key, native_support=self._native_support)

        print(
            f"[WolandSwarm] Attending Governing Councils for: '{request.objective}' "
            f"(task_key={request.task_key}, swarm_type=governing-councils, fixture_mode={request.fixture_mode})"
        )

        acts_script: list[tuple[int, str, list[tuple[str, str, str]]]] = [
            (
                1,
                "Act I: The Colonnade & Gallery Arrival",
                [
                    ("hella", "docket_entry", "Logging entry through the colonnade; gallery seats occupied without sound."),
                    ("koroviev", "gallery_observation", "Observe how carefully the council chamber doors were bolted, yet here we sit!"),
                    ("woland", "chamber_presence", "We come to observe, not to govern. Let the council proceed."),
                ],
            ),
            (
                2,
                "Act II: Reading the Docket & False Consensus",
                [
                    ("liudmila", "agenda_reading", "The docket is opened: review of architectural boundaries and pending motions."),
                    ("koroviev", "mocking_arithmetic", "Twelve affirmative votes claimed, but thirty-four unresolved defects omitted! Charming arithmetic!"),
                    ("polina", "puncturing_hubris", "Calling an uninspected report unanimous is like calling a rainstorm dry."),
                ],
            ),
            (
                3,
                "Act III: Unmasking the Concealed Defect",
                [
                    ("begemot", "curtain_reveal", "The honourable secretary waves a stamped envelope, but the paper within is blank! Where is the receipt?"),
                    ("jeremy", "runtime_demand", "A motion without a passing test is merely wishful prose. Show the command output."),
                    ("stravinsky", "circular_quarantine", "This topic was deferred in session eight and session ten. It belongs in quarantine, not debate."),
                ],
            ),
            (
                4,
                "Act IV: The Migraine of Pontius Pilate",
                [
                    ("pilate", "handwashing_warning", "To refer the defect to next quarter's committee is to wash one's hands in a dry basin."),
                    ("woland", "cowardice_admonition", "Cowardice is the most terrible vice. A flaw acknowledged is half-repaired; a flaw hidden rots the foundation."),
                    ("azazello", "boundary_stare", "The fence of Blackrod remains immovable. Step past it and find your authority extinguished."),
                ],
            ),
            (
                5,
                "Act V: The Scars & Obligation Harvest",
                [
                    ("yaroslava", "harvest_custody", "Recording three concrete obligations into the permanent scars ledger."),
                    ("master", "axiomatic_truth", "Manuscripts don't burn. Neither do unresolved mathematical obstructions."),
                    ("margarita", "resolution_courage", "Do not despair over the backlog; face it with clarity and clean steel."),
                ],
            ),
            (
                6,
                "Act VI: The Voting Abstention",
                [
                    ("ratslayer", "orderly_abstention", "The question is called on motion one. The Retinue remains silent in the colonnade."),
                    ("koroviev", "formal_abstain", "Not a hand raised, not a ballot cast! Zero votes from our corner!"),
                    ("woland", "non_interference_affirmation", "Resolutions belong to the council. Our witness is the ledger, not the vote."),
                ],
            ),
            (
                7,
                "Act VII: Departure & Consecration",
                [
                    ("hella", "ledger_sealing", "Docket closed. Meeting adjourned. The scars are documented."),
                    ("woland", "departure", "Freshness is only one: the first, and it is also the last. Attend to your obligations."),
                ],
            ),
        ]

        carrier: dict[str, Any] = {
            "input_context": input_context,
            "input_context_provenance": {
                "source": "SUPPLIED_REQUEST_CONTEXT",
                "dialogue": "SCRIPTED_CUES",
                "obligations": "SCRIPTED_FIXTURE",
                "derived_conclusions": False,
            },
            "council_tier": "L1_to_L3",
            "chamber": "High Council of Councils Colonnade",
            "attendance_privilege": "ORTHOGONAL_ACCESS_NON_INTERFERENCE",
            "motion_votes_cast": 0,
            "retinue_voting_abstention": True,
            "open_obligations": [
                {
                    "obligation_id": f"OBL-{request.task_key[:8]}-001",
                    "council": "L3_techne",
                    "description": "Verify Clean Architecture decoupling on all swarm boundary wrappers",
                    "severity": "HIGH",
                    "assigned_role": "Master & Techne Triad",
                    "locus": "omega_engine_woland",
                },
                {
                    "obligation_id": f"OBL-{request.task_key[:8]}-002",
                    "council": "L3_nomos",
                    "description": "Reconcile contract prompt parity between omega_contracts and runtime",
                    "severity": "MEDIUM",
                    "assigned_role": "Council Nomos",
                    "locus": "omega_contracts",
                },
            ],
            "authority_effect": "None",
            "acts_completed": 0,
        }

        executed_beats: list[GoverningCouncilBeatExecutionV1] = []
        all_cochains: list[Residual1Cochain] = []
        dda_steps: list[dict[str, Any]] = []
        step_idx = 0

        for act_idx, act_title, beats in acts_script:
            for spk_key, cue, fallback_text in beats:
                mapping = GOVERNING_COUNCILS_RETINUE_MAP.get(
                    spk_key,
                    RetinueRoleMappingV1(
                        persona=spk_key.capitalize(),
                        cognitive_operator="E_terminal",
                        residual_sort="exactness_witness",
                        software_dev_role="Retinue Observer",
                        mapped_skills=(),
                        description="Retinue member observing council session.",
                    ),
                )

                carrier_prev = dict(carrier)
                pkg = CharacterOperatorRegistry.get_operator_package(spk_key)
                carrier = pkg.apply_transform(carrier)
                cochain = pkg.extract_residual(carrier_prev, carrier)
                all_cochains.append(cochain)

                dialogue_res = self.synthesizer.render_dialogue(mapping.persona, cue)
                dialogue = dialogue_res.value if dialogue_res.is_ok else f"[{mapping.persona}]: «{fallback_text}»"

                delta = {
                    k: v
                    for k, v in carrier.items()
                    if k not in carrier_prev or carrier_prev[k] != v
                }

                executed_beat = GoverningCouncilBeatExecutionV1(
                    act_index=act_idx,
                    act_title=act_title,
                    speaker_key=spk_key,
                    persona=mapping.persona,
                    cue=cue,
                    dialogue=dialogue,
                    operator_tag=mapping.cognitive_operator,
                    residual_sort=mapping.residual_sort,
                    carrier_delta=delta,
                    cochain=cochain,
                )
                executed_beats.append(executed_beat)

                step_idx += 1
                dda_steps.append({
                    "step_index": step_idx,
                    "act": act_idx,
                    "character": mapping.persona,
                    "operator": mapping.cognitive_operator,
                    "skills": list(mapping.mapped_skills),
                    "residual_sort": mapping.residual_sort,
                    "delta": delta,
                })

            carrier["acts_completed"] = act_idx

        # Exact valuation of cochains
        valuation = self.valuator.value_cochains(tuple(all_cochains))

        # Licensing boundary verification
        evidence_payload = {
            "task_key": request.task_key,
            "objective": request.objective,
            "swarm_type": SwarmTypeV1.GOVERNING_COUNCILS.value,
            "motion_votes_cast": 0,
            "retinue_voting_abstention": True,
            "beats_count": len(executed_beats),
            "carrier_final": carrier,
        }
        evidence_sha256 = hashlib.sha256(
            json.dumps(evidence_payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
        ).hexdigest()

        is_licensed, token, reasons = LicensingBoundary.propose_token(
            target_receipt=valuation,
            witness_cochain=None,
            expected_sha256=evidence_sha256,
        )

        verdict = "COUNCIL_ATTENDANCE_SEALED"
        status = "BOUNDED_RESIDUAL"
        disposition = "HOLD"
        consecration_state = "PROPOSED_FOR_ADMISSION" if request.request_external_admission else "COUNCIL_OBSERVATION"
        terminal_verdict = "COUNCIL_ATTENDANCE_SEALED"

        # Render theatrical Bulgakovian Novella
        novella_md = self._render_novella(
            request=request,
            executed_beats=executed_beats,
            verdict=verdict,
            terminal_verdict=terminal_verdict,
            valuation=valuation,
            carrier=carrier,
        )

        # Build summary and receipt
        summary: dict[str, Any] = {
            "task_key": request.task_key,
            "objective": request.objective,
            "swarm_type": SwarmTypeV1.GOVERNING_COUNCILS.value,
            "status": status,
            "disposition": disposition,
            "terminal_verdict": terminal_verdict,
            "licensing_verdict": verdict,
            "licensing_token": token,
            "authority_effect": "None",
            "fixture_mode": request.fixture_mode,
            "motion_votes_cast": 0,
            "retinue_voting_abstention": True,
            "retinue_characters_invoked": list({b.persona for b in executed_beats}),
            "open_obligations_harvested": carrier.get("open_obligations", []),
            "total_beats": len(executed_beats),
            "valuation": {
                "max_mass": float(valuation.phi_1),
                "total_mass": float(valuation.gamma_2),
                "defect_count": len(valuation.diagnostics.get("defects", [])),
            },
            "carrier_final": carrier,
        }

        receipt_id = content_addressed_receipt_id(novella_md, dda_steps, summary, native_support=self._native_support)
        summary["receipt_id"] = receipt_id

        receipt: dict[str, Any] = {
            "receipt_id": receipt_id,
            "schema": "omega.woland.governing-councils-bout.v1",
            "fixture_mode": request.fixture_mode,
            "input_context_provenance": carrier["input_context_provenance"],
            "task_key": request.task_key,
            "swarm_type": SwarmTypeV1.GOVERNING_COUNCILS.value,
            "status": status,
            "disposition": disposition,
            "terminal_verdict": terminal_verdict,
            "licensing_verdict": verdict,
            "licensing_token": token,
            "authority_effect": "None",
            "motion_votes_cast": 0,
            "retinue_voting_abstention": True,
            "evidence_sha256": evidence_sha256,
        }

        # Persist bout run folder
        folder_key = run_directory_name(request.task_key, native_support=self._native_support)
        persist_res = persist_bout_run_folder(
            target_root, folder_key, receipt, novella_md, dda_steps, summary
        , native_support=self._native_support)
        if persist_res.is_err:
            return Err(persist_res.unwrap_err())

        # Also persist open_obligations.jsonl
        obligations_path = run_folder / "open_obligations.jsonl"
        with obligations_path.open("w", encoding="utf-8") as f:
            for obl in carrier.get("open_obligations", []):
                f.write(json.dumps(obl, ensure_ascii=False, sort_keys=True) + "\n")

        phi1_str: str | None = None
        gamma2_str: str | None = None
        meas_status = "NOT_MEASURED"
        if getattr(valuation, "is_exact_rational", False):
            from fractions import Fraction

            from ..domain.evidence import canonical_rational

            try:
                phi1_str = canonical_rational(Fraction(valuation.phi_1).limit_denominator())
                gamma2_str = canonical_rational(Fraction(valuation.gamma_2).limit_denominator())
                meas_status = "MEASURED"
            except Exception:
                phi1_str = None
                gamma2_str = None
                meas_status = "NOT_MEASURED"

        outcome = WolandBoutOutcomeV1(
            receipt_id=receipt_id,
            selected_candidate_id=request.task_key,
            disposition=disposition,
            consecration_state=consecration_state,
            terminal_verdict=terminal_verdict,
            authority_effect="None",
            task_key=request.task_key,
            status=status,
            receipt_path=str(run_folder / "receipt.json"),
            novella_path=str(run_folder / "uns.md"),
            ddc_path=str(run_folder / "ddc.jsonl"),
            summary_path=str(run_folder / "summary.json"),
            phi1=phi1_str,
            gamma2=gamma2_str,
            defect_count=len(valuation.diagnostics.get("defects", [])),
            residual_declared=True,
            is_authorized=False,
            measurement_status=meas_status,
            checker_verdict="NOT_MEASURED",
            checker_receipt_sha256=None,
            authorization_blockers=(),
            authorization_evidence=None,
            swarm_type=SwarmTypeV1.GOVERNING_COUNCILS.value,
        )

        return Ok(outcome)

    def _render_novella(
        self,
        request: WolandBoutRequestV1,
        executed_beats: list[GoverningCouncilBeatExecutionV1],
        verdict: str,
        terminal_verdict: str,
        valuation: ValuationReceipt,
        carrier: dict[str, Any],
    ) -> str:
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines: list[str] = [
            f"# Woland Swarm Dialectic Novella: Council Observation (Task: {request.task_key})",
            "",
            f"**Objective:** {request.objective}",
            f"**Swarm Type:** {SwarmTypeV1.GOVERNING_COUNCILS.value} (High Council of Councils)",
            f"**Timestamp:** {date_str}",
            "**AuthorityEffect:** None.",
            "**Input provenance:** Supplied context is retained in the receipt-bound summary. "
            "Dialogue follows scripted cues, and obligations are scripted fixtures; "
            "neither is a conclusion derived from the supplied context.",
            f"**Licensing Verdict:** {verdict}",
            f"**Terminal Verdict:** {terminal_verdict}",
            "**Non-Interference Rule:** Zero motion votes cast. Retinue strictly observed and harvested open obligations.",
            "",
            "---",
            "",
            "## Theatrical Dramatis Personae (The Retinue in the Colonnade)",
            "",
            "| Persona | Cognitive Operator | Role in Chamber |",
            "| :--- | :--- | :--- |",
        ]

        invoked_keys = {b.speaker_key for b in executed_beats}
        for k in sorted(invoked_keys):
            mapping = GOVERNING_COUNCILS_RETINUE_MAP.get(k)
            if mapping:
                lines.append(f"| **{mapping.persona}** | `{mapping.cognitive_operator}` | {mapping.software_dev_role} |")

        lines.extend([
            "",
            "---",
            "",
            "## Seven-Act Deliberation & Observation Drama",
            "",
        ])

        current_act = -1
        for b in executed_beats:
            if b.act_index != current_act:
                current_act = b.act_index
                lines.extend([
                    f"### {b.act_title}",
                    "",
                ])
            lines.extend([
                f"> **{b.persona}** (`{b.operator_tag}`):",
                f"> {b.dialogue}",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## Persistent Scars & Harvested Obligations",
            "",
            "| Obligation ID | Council | Description | Severity | Assigned Role |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for obl in carrier.get("open_obligations", []):
            lines.append(
                f"| `{obl['obligation_id']}` | {obl['council']} | {obl['description']} | **{obl['severity']}** | {obl['assigned_role']} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## Bulgakovian Epilogue & Maxims",
            "",
            "1. *«Manuscripts don't burn.»* Neither do unaddressed repository defects or recorded obligations.",
            "2. *«Cowardice is the most terrible vice.»* Evading a needed refactor through bureaucratic delays solves nothing.",
            "3. *«Freshness is only one: the first, and it is also the last.»* Code contracts and receipts either satisfy the invariant or they fail closed.",
            "",
            "Attendance concluded with **zero motion votes cast**. Output consecrated with `AuthorityEffect: None`.",
            "",
        ])

        return "\n".join(lines)


__all__ = [
    "GOVERNING_COUNCILS_RETINUE_MAP",
    "CouncilObligationV1",
    "GoverningCouncilBeatExecutionV1",
    "GoverningCouncilsBoutUseCase",
]
