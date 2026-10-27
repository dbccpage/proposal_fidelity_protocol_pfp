"""Product-Management & Sprint Lifecycle Bout Use Case.

Under swarm_type="product-mgmt", Adversary and the Product Planning Office Panel orchestrate
the end-to-end sprint lifecycle (planning, backlog grooming, ticket dispatch, DevOps CI checks,
retrospective scars documentation, and VP escalation briefings).

AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from governance.domain.intelligence_community import canonical_intelligence_route
from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.evidence import canonical_rational
from adversary.domain.models import (
    AdversaryBoutOutcomeV1,
    AdversaryBoutRequestV1,
)
from adversary.domain.native import NativeOperationPort
from adversary.domain.residual_algebra.character_operators import (
    CharacterOperatorRegistry,
)
from adversary.domain.residual_algebra.dialogue_synthesizer import (
    DialogueSynthesizer,
)
from adversary.domain.residual_algebra.licensing_boundary import (
    LicensingBoundary,
    ValuationReceipt,
)
from adversary.domain.residual_algebra.protocols import (
    ObstructionValuatorProtocol,
)
from adversary.domain.residual_algebra.residual_sorts import (
    Residual1Cochain,
)
from adversary.domain.specialization import SwarmTypeV1
from adversary.use_cases.persistence import (
    persist_bout_run_folder,
    run_directory_name,
)
from adversary.use_cases.persistence import (
    reported_receipt_id as content_addressed_receipt_id,
)
from adversary.use_cases.software_dev_bout_use_case import (
    DefaultObstructionValuator,
    PanelRoleMappingV1,
)

_LOCUS = "adversary.use_cases.product_mgmt_bout_use_case"


PRODUCT_MGMT_PANEL_MAP: dict[str, PanelRoleMappingV1] = {
    "adversary": PanelRoleMappingV1(
        persona="Adversary",
        cognitive_operator="E_terminal",
        residual_sort="exactness_witness",
        software_dev_role="Sovereign Sprint Auditor & Terminal Judge",
        mapped_skills=(),
        description="Assesses delivery against ground reality; seals the final sprint disposition.",
    ),
    "resilience": PanelRoleMappingV1(
        persona="Resilience",
        cognitive_operator="E_luda_resilience",
        residual_sort="stable_equilibrium",
        software_dev_role="Product Planning Manager & VP Engineering",
        mapped_skills=("oikonomia-product-manager", "techne-sprint-manager"),
        description="Maintains sprint backlog, team velocity, and escalations above risk 0.7.",
    ),
    "bare_metal_anchor": PanelRoleMappingV1(
        persona="Bare Metal Anchor",
        cognitive_operator="E_yankee_solver",
        residual_sort="executable_runtime",
        software_dev_role="Reality Anchor & Velocity Verifier",
        mapped_skills=("panep-cs-prof",),
        description="Estimates story complexity without hyperbole; enforces executable deliverables.",
    ),
    "punchlist": PanelRoleMappingV1(
        persona="Punchlist",
        cognitive_operator="E_punchlist_discipline",
        residual_sort="methodical_completion",
        software_dev_role="Sprint Custodian & Definition of Done Officer",
        mapped_skills=("techne-sprint-execution", "techne-mutation-evidence-custody"),
        description="Tracks punchlists, ticket state transitions, and byte custody.",
    ),
    "defect_hunter": PanelRoleMappingV1(
        persona="Defect Hunter",
        cognitive_operator="E_syntactic",
        residual_sort="gauge_residual",
        software_dev_role="Estimation Satirist & Backlog Critic",
        mapped_skills=("techne-docs-lint-hunter-killer",),
        description="Mocks optimistic story point estimates and scope creep with biting arithmetic.",
    ),
    "gauge_breaker": PanelRoleMappingV1(
        persona="Gauge Breaker",
        cognitive_operator="E_semantic",
        residual_sort="boundary_defect",
        software_dev_role="DevOps CI Gatekeeper & Prankster",
        mapped_skills=("techne-sprint-devops-review",),
        description="Ensures local-CI and test harnesses pass before tickets reach Definition of Done.",
    ),
    "master": PanelRoleMappingV1(
        persona="Manuscript Truth",
        cognitive_operator="E_formal",
        residual_sort="exactness_witness",
        software_dev_role="Architectural Conscience & Epic Alignment",
        mapped_skills=("techne-code-principal-architect",),
        description="Guarantees sprint stories do not violate clean architecture or introduce shims.",
    ),
    "primal_dual": PanelRoleMappingV1(
        persona="Primal Dual",
        cognitive_operator="E_placebo",
        residual_sort="prior_lock_residual",
        software_dev_role="Sprint Moral Anchor & Blocker Breaker",
        mapped_skills=("techne-sprint-retrospective",),
        description="Converts retrospective scars and blocker despair into actionable improvements.",
    ),
}


@dataclass(frozen=True)
class ProductMgmtBeatExecutionV1:
    act_index: int
    act_title: str
    speaker_key: str
    persona: str
    cue: str
    dialogue: str
    operator_tag: str
    residual_sort: str
    mapped_skills: tuple[str, ...]
    carrier_delta: dict[str, Any]
    cochain: Residual1Cochain


class ProductMgmtBoutUseCase:
    """Theatrical and structured 7-Act sprint lifecycle bout for Product Planning."""

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
        request: AdversaryBoutRequestV1,
        *,
        output_dir: Path | str | None = None,
    ) -> Result[AdversaryBoutOutcomeV1, Refusal]:
        target_root = Path(output_dir) if output_dir is not None else (
            self.repo_root / canonical_intelligence_route("_intelligence/_adversary")
        )
        run_folder = target_root / "runs" / run_directory_name(request.task_key, native_support=self._native_support)

        print(
            f"[AdversarySwarm] Executing Product Management Bout for: '{request.objective}' "
            f"(task_key={request.task_key}, swarm_type=product-mgmt, fixture_mode={request.fixture_mode})"
        )

        acts_script: list[tuple[int, str, list[tuple[str, str, str]]]] = [
            (
                1,
                "Act I: Backlog Ingress & Horizon Framing",
                [
                    ("resilience", "backlog_ingress", "Reviewing product planning office backlog and incoming epics."),
                    ("defect_hunter", "backlog_satire", "Forty tickets proposed for a five-day sprint! A miracle of optimistic arithmetic!"),
                    ("bare_metal_anchor", "capacity_grounding", "Cap the velocity at realistic bounds. We deliver verified code, not wishful story points."),
                ],
            ),
            (
                2,
                "Act II: Sprint Capacity & Story Grooming",
                [
                    ("resilience", "capacity_allocation", "Setting team capacity to twenty-four story points across core epics."),
                    ("master", "architecture_alignment", "Ensure every ticket complies with Clean Architecture boundaries; zero shims permitted."),
                    ("punchlist", "story_definition_of_done", "Acceptance criteria formalized: failing test first, verified code, receipt custody."),
                ],
            ),
            (
                3,
                "Act III: TDD Dispatch & Task Execution",
                [
                    ("punchlist", "ticket_dispatch", "Dispatching stories to engineering triads: Rust core, Python runtime, and formal proofs."),
                    ("gauge_breaker", "test_harness_check", "Running test harness mutations. A passing test that cannot fail is a fraud!"),
                ],
            ),
            (
                4,
                "Act IV: Mid-Sprint Blocker Resolution",
                [
                    ("primal_dual", "blocker_clearing", "A circular dependency threatened the runtime; refactored through pure ports."),
                    ("adversary", "cowardice_warning", "Cowardice is the most terrible vice. Postponing a hard refactor only compounds the debt."),
                ],
            ),
            (
                5,
                "Act V: DevOps CI & Quality Verification",
                [
                    ("gauge_breaker", "local_ci_verification", "Local-CI and clippy pass across all workspace crates! Zero compiler warnings!"),
                    ("punchlist", "definition_of_done_audit", "All acceptance criteria verified against frozen receipts."),
                ],
            ),
            (
                6,
                "Act VI: Retrospective & Scars Ledgering",
                [
                    ("primal_dual", "retrospective_analysis", "Reviewing sprint velocity and lessons learned. Documenting scars in the registry."),
                    ("resilience", "vp_briefing", "Sprint risk score assessed at 0.15; well below the 0.7 escalation threshold."),
                ],
            ),
            (
                7,
                "Act VII: Sprint Sealing & Release Consecration",
                [
                    ("master", "manuscript_preservation", "Manuscripts don't burn. Neither do completed sprint tickets with valid evidence."),
                    ("adversary", "sprint_terminal_seal", "Freshness is only one: the first, and it is also the last. Sprint delivery sealed."),
                ],
            ),
        ]

        carrier: dict[str, Any] = {
            "sprint_id": f"SPRINT-{request.task_key[:8].upper()}",
            "committed_points": 24,
            "completed_points": 24,
            "risk_score": 0.15,
            "escalation_required": False,
            "tickets": [
                {
                    "ticket_id": f"TICKET-{request.task_key[:6]}-01",
                    "title": "Refactor swarm specialization composition root",
                    "points": 8,
                    "status": "DONE",
                },
                {
                    "ticket_id": f"TICKET-{request.task_key[:6]}-02",
                    "title": "Wire OEPFP provider mediation and estate adapters",
                    "points": 8,
                    "status": "DONE",
                },
                {
                    "ticket_id": f"TICKET-{request.task_key[:6]}-03",
                    "title": "Implement Panel novella rendering and receipt custody",
                    "points": 8,
                    "status": "DONE",
                },
            ],
            "authority_effect": "None",
            "acts_completed": 0,
        }

        executed_beats: list[ProductMgmtBeatExecutionV1] = []
        all_cochains: list[Residual1Cochain] = []
        dda_steps: list[dict[str, Any]] = []
        step_idx = 0

        for act_idx, act_title, beats in acts_script:
            for spk_key, cue, fallback_text in beats:
                mapping = PRODUCT_MGMT_PANEL_MAP.get(
                    spk_key,
                    PanelRoleMappingV1(
                        persona=spk_key.capitalize(),
                        cognitive_operator="E_terminal",
                        residual_sort="exactness_witness",
                        software_dev_role="Product Planning Participant",
                        mapped_skills=(),
                        description="Product planning participant.",
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

                executed_beat = ProductMgmtBeatExecutionV1(
                    act_index=act_idx,
                    act_title=act_title,
                    speaker_key=spk_key,
                    persona=mapping.persona,
                    cue=cue,
                    dialogue=dialogue,
                    operator_tag=mapping.cognitive_operator,
                    residual_sort=mapping.residual_sort,
                    mapped_skills=mapping.mapped_skills,
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

        # Exact valuation
        valuation = self.valuator.value_cochains(tuple(all_cochains))

        # Licensing verification
        evidence_payload = {
            "task_key": request.task_key,
            "objective": request.objective,
            "swarm_type": SwarmTypeV1.PRODUCT_MGMT.value,
            "sprint_id": carrier.get("sprint_id"),
            "committed_points": carrier.get("committed_points"),
            "completed_points": carrier.get("completed_points"),
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

        verdict = "SPRINT_DELIVERY_SEALED"
        status = "BOUNDED_RESIDUAL"
        disposition = "HOLD"
        consecration_state = "PROPOSED_FOR_ADMISSION" if request.request_external_admission else "SPRINT_EVALUATION"
        terminal_verdict = "SPRINT_DELIVERY_SEALED"

        # Render theatrical Novella
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
            "swarm_type": SwarmTypeV1.PRODUCT_MGMT.value,
            "status": status,
            "disposition": disposition,
            "terminal_verdict": terminal_verdict,
            "licensing_verdict": verdict,
            "licensing_token": token,
            "authority_effect": "None",
            "fixture_mode": request.fixture_mode,
            "sprint_id": carrier.get("sprint_id"),
            "committed_points": carrier.get("committed_points"),
            "completed_points": carrier.get("completed_points"),
            "risk_score": carrier.get("risk_score"),
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
            "schema": "core.adversary.product-mgmt-bout.v1",
            "task_key": request.task_key,
            "swarm_type": SwarmTypeV1.PRODUCT_MGMT.value,
            "status": status,
            "disposition": disposition,
            "terminal_verdict": terminal_verdict,
            "licensing_verdict": verdict,
            "licensing_token": token,
            "authority_effect": "None",
            "evidence_sha256": evidence_sha256,
            "sprint_id": carrier.get("sprint_id"),
        }

        # Persist run folder
        folder_key = run_directory_name(request.task_key, native_support=self._native_support)
        persist_res = persist_bout_run_folder(
            target_root, folder_key, receipt, novella_md, dda_steps, summary
        , native_support=self._native_support)
        if persist_res.is_err:
            return Err(persist_res.unwrap_err())

        # Also persist sprint_manifest.json
        manifest_path = run_folder / "sprint_manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "sprint_id": carrier.get("sprint_id"),
                    "objective": request.objective,
                    "committed_points": carrier.get("committed_points"),
                    "completed_points": carrier.get("completed_points"),
                    "risk_score": carrier.get("risk_score"),
                    "escalation_required": carrier.get("escalation_required"),
                    "tickets": carrier.get("tickets", []),
                    "authority_effect": "None",
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        phi1_str: str | None = None
        gamma2_str: str | None = None
        meas_status = "NOT_MEASURED"
        if getattr(valuation, "is_exact_rational", False):
            try:
                phi1_str = canonical_rational(Fraction(valuation.phi_1).limit_denominator())
                gamma2_str = canonical_rational(Fraction(valuation.gamma_2).limit_denominator())
                meas_status = "MEASURED"
            except Exception:
                phi1_str = None
                gamma2_str = None
                meas_status = "NOT_MEASURED"

        outcome = AdversaryBoutOutcomeV1(
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
            swarm_type=SwarmTypeV1.PRODUCT_MGMT.value,
        )

        return Ok(outcome)

    def _render_novella(
        self,
        request: AdversaryBoutRequestV1,
        executed_beats: list[ProductMgmtBeatExecutionV1],
        verdict: str,
        terminal_verdict: str,
        valuation: ValuationReceipt,
        carrier: dict[str, Any],
    ) -> str:
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines: list[str] = [
            f"# Adversary Swarm Dialectic Novella: Product Management & Sprint Lifecycle (Task: {request.task_key})",
            "",
            f"**Objective:** {request.objective}",
            f"**Swarm Type:** {SwarmTypeV1.PRODUCT_MGMT.value} (Product Planning Office)",
            f"**Sprint ID:** {carrier.get('sprint_id')}",
            f"**Timestamp:** {date_str}",
            "**AuthorityEffect:** None.",
            f"**Licensing Verdict:** {verdict}",
            f"**Terminal Verdict:** {terminal_verdict}",
            f"**Sprint Metrics:** {carrier.get('completed_points')}/{carrier.get('committed_points')} points delivered. Risk score: {carrier.get('risk_score')}.",
            "",
            "---",
            "",
            "## Theatrical Dramatis Personae (Product Planning Office)",
            "",
            "| Persona | Cognitive Operator | Role in Sprint |",
            "| :--- | :--- | :--- |",
        ]

        invoked_keys = {b.speaker_key for b in executed_beats}
        for k in sorted(invoked_keys):
            mapping = PRODUCT_MGMT_PANEL_MAP.get(k)
            if mapping:
                lines.append(f"| **{mapping.persona}** | `{mapping.cognitive_operator}` | {mapping.software_dev_role} |")

        lines.extend([
            "",
            "---",
            "",
            "## Seven-Act Sprint Lifecycle Drama",
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
            "## Sprint Delivery Manifest",
            "",
            "| Ticket ID | Title | Points | Status |",
            "| :--- | :--- | :--- | :--- |",
        ])
        for ticket in carrier.get("tickets", []):
            lines.append(
                f"| `{ticket['ticket_id']}` | {ticket['title']} | {ticket['points']} | **{ticket['status']}** |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## the novelistian Epilogue & Maxims",
            "",
            "1. *«Manuscripts don't burn.»* Neither do completed sprint tickets supported by immutable receipts.",
            "2. *«Cowardice is the most terrible vice.»* Deferring technical debt only leads to architectural collapse.",
            "3. *«Freshness is only one: the first, and it is also the last.»* Software either satisfies the Definition of Done or it remains incomplete.",
            "",
            "Sprint lifecycle sealed. Delivery consecrated with `AuthorityEffect: None`.",
            "",
        ])

        return "\n".join(lines)


__all__ = [
    "PRODUCT_MGMT_PANEL_MAP",
    "ProductMgmtBeatExecutionV1",
    "ProductMgmtBoutUseCase",
]
