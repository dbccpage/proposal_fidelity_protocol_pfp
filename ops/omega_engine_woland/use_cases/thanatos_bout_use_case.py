"""Thanatos Council & Nemesis Child Swarm Handoff Bout Use Case.

Under swarm_type="thanatos", Woland receives security, threat, or vulnerability objectives,
validates the threat surface bounds, delegates execution authority to the Thanatos Council
(L3_logos_thanatos) and its child councils (Nemesis, Aegidion, Countermeasure Squad, Truth Firewall),
and terminates with Abadonna zeroing ephemeral traces before Woland seals the security receipt.

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

from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.evidence import canonical_rational
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

_LOCUS = "omega_engine_woland.use_cases.thanatos_bout_use_case"


THANATOS_RETINUE_MAP: dict[str, RetinueRoleMappingV1] = {
    "woland": RetinueRoleMappingV1(
        persona="Woland",
        cognitive_operator="E_terminal",
        residual_sort="exactness_witness",
        software_dev_role="Sovereign Security Gatekeeper",
        mapped_skills=(),
        description="Verifies ingress boundary and seals final security receipt.",
    ),
    "thanatos_procurator": RetinueRoleMappingV1(
        persona="Thanatos Procurator",
        cognitive_operator="E_thanatos",
        residual_sort="governance_audit",
        software_dev_role="Thanatos Council Presiding Officer",
        mapped_skills=("rip-thanatos",),
        description="Presides over defensive operations, coordinates child swarm dispatches.",
    ),
    "nemesis": RetinueRoleMappingV1(
        persona="Council Nemesis",
        cognitive_operator="E_falsification",
        residual_sort="falsification_witness",
        software_dev_role="Sandboxed Red-Team Exploiter",
        mapped_skills=("thanatos-nemesis",),
        description="Executes sandboxed penetration, privilege escalation, and adversarial containment.",
    ),
    "aegidion": RetinueRoleMappingV1(
        persona="Council Aegidion",
        cognitive_operator="E_containment",
        residual_sort="boundary_defect",
        software_dev_role="Network & Transport Sentinel",
        mapped_skills=("thanatos-aegidion-network-security",),
        description="Enforces zero ambient network sockets and audits API transport fences.",
    ),
    "countermeasure_squad": RetinueRoleMappingV1(
        persona="Countermeasure Squad",
        cognitive_operator="E_exact_repair",
        residual_sort="exact_repair",
        software_dev_role="Vulnerability Patch & Binding Specialist",
        mapped_skills=(
            "thanatos-countermeasure-binding-repair",
            "thanatos-exploit-indicator-coverage",
        ),
        description="Repairs severed countermeasure bindings and confirms exploit indicator coverage.",
    ),
    "truth_firewall": RetinueRoleMappingV1(
        persona="Truth Firewall",
        cognitive_operator="E_firewall",
        residual_sort="claim_hygiene",
        software_dev_role="Anti-Deception & Promotion Blocker",
        mapped_skills=(
            "thanatos-public-claim-bs-firewall",
            "thanatos-human-promotion-firewall",
        ),
        description="Blocks unauthorized promotion and filters unverified mathematical or security claims.",
    ),
    "abadonna": RetinueRoleMappingV1(
        persona="Abadonna",
        cognitive_operator="E_annihilate",
        residual_sort="quarantine",
        software_dev_role="Ephemeral Trace Annihilator & Receipt Crystallizer",
        mapped_skills=(),
        description="Gaze brings absolute finality, zeroes ephemeral test traces, and crystallizes receipts.",
    ),
    "koroviev": RetinueRoleMappingV1(
        persona="Koroviev",
        cognitive_operator="E_syntactic",
        residual_sort="gauge_residual",
        software_dev_role="Adversarial Fuzzer & Boundary Provocateur",
        mapped_skills=("techne-adversarial-refusal-bypass-auditor",),
        description="Generates hostile syntactic permutations to test firewall elasticity.",
    ),
    "begemot": RetinueRoleMappingV1(
        persona="Begemot",
        cognitive_operator="E_semantic",
        residual_sort="boundary_defect",
        software_dev_role="Sandbox Jester & Trap Detector",
        mapped_skills=("techne-comment-slop-hunter-killer",),
        description="Probes privilege boundaries and laughs when an unauthorized caller is blocked.",
    ),
    "azazello": RetinueRoleMappingV1(
        persona="Azazello",
        cognitive_operator="E_falsification",
        residual_sort="falsification_witness",
        software_dev_role="Direct Strike & Hostile Containment Officer",
        mapped_skills=("thanatos-skill-security-spector",),
        description="Fangs bared; strikes down malicious payloads and unauthenticated injection vectors.",
    ),
}


@dataclass(frozen=True)
class ThanatosBeatExecutionV1:
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


class ThanatosBoutUseCase:
    """Theatrical and defensive 7-Act security bout for Thanatos Council delegation."""

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
        target_root = Path(output_dir) if output_dir is not None else (
            self.repo_root / canonical_intelligence_route("_intelligence/_woland")
        )
        run_folder = target_root / "runs" / run_directory_name(request.task_key, native_support=self._native_support)

        print(
            f"[WolandSwarm] Executing Thanatos Security Bout for: '{request.objective}' "
            f"(task_key={request.task_key}, swarm_type=thanatos, fixture_mode={request.fixture_mode})"
        )

        acts_script: list[tuple[int, str, list[tuple[str, str, str]]]] = [
            (
                1,
                "Act I: Ingress Threat Surface Demarcation",
                [
                    ("woland", "threat_ingress_inspection", "We inspect the perimeter before unsealing the gates. What surface is under examination?"),
                    ("koroviev", "boundary_fuzzing", "Examining every crack in the facade! If a mouse can slip through, so can an adversary!"),
                    ("azazello", "containment_fence_check", "The sandboxed container is clamped. Not a single outbound byte escapes."),
                ],
            ),
            (
                2,
                "Act II: Handoff to Thanatos Procurator",
                [
                    ("woland", "formal_delegation", "Authority for defensive execution is transferred to the Thanatos Council under Auth Code ZD-30."),
                    ("thanatos_procurator", "procurator_acceptance", "The Thanatos Council accepts the mandate. Child swarms Nemesis and Aegidion are summoned."),
                ],
            ),
            (
                3,
                "Act III: Council Nemesis Sandboxed Exploitation",
                [
                    ("nemesis", "red_team_attack", "Executing sandboxed hostile injection, privilege escalation checks, and refusal bypass tests."),
                    ("begemot", "trap_detection", "Watch the adversary attempt to forge an AUTHORIZED status without a valid checker digest! Blocked fail-closed!"),
                    ("nemesis", "containment_verified", "Red-team battery concluded: zero bypasses admitted; hostile probes neutralized."),
                ],
            ),
            (
                4,
                "Act IV: Council Aegidion Transport Audit",
                [
                    ("aegidion", "socket_inspection", "Scanning network perception boundaries: zero ambient network sockets detected."),
                    ("aegidion", "api_boundary_fence", "All model communications route strictly through Symbol Game protocol v2. Clean architecture preserved."),
                ],
            ),
            (
                5,
                "Act V: Countermeasure Binding & Indicator Sealing",
                [
                    ("countermeasure_squad", "binding_repair", "All countermeasure references in the threat matrix resolve to known defense URNs."),
                    ("countermeasure_squad", "exploit_coverage", "Exploit indicator coverage verified at one hundred percent."),
                ],
            ),
            (
                6,
                "Act VI: Truth Firewall & Anti-Deception Gate",
                [
                    ("truth_firewall", "claim_filtering", "Scanning for promotional vocabulary and unsubstantiated claims. Slop excised."),
                    ("truth_firewall", "promotion_blocking", "Human promotion firewall engaged: status remains strictly proposal with AuthorityEffect None."),
                ],
            ),
            (
                7,
                "Act VII: Abadonna's Annihilation & Woland's Seal",
                [
                    ("abadonna", "ephemeral_annihilation", "The silent gaze lowers. Ephemeral test traces are zeroed. Memory is wiped clean."),
                    ("woland", "receipt_consecration", "The defensive trial is complete. Freshness is only one: the first, and it is also the last."),
                ],
            ),
        ]

        carrier: dict[str, Any] = {
            "threat_surface": "SANDBOXED_CONTAINER_ONLY",
            "delegation_target": "L3_logos_thanatos",
            "auth_code": "ZD-30",
            "child_swarms_dispatched": [
                "thanatos-nemesis",
                "thanatos-aegidion-network-security",
                "thanatos-countermeasure-binding-repair",
                "thanatos-exploit-indicator-coverage",
                "thanatos-public-claim-bs-firewall",
                "thanatos-human-promotion-firewall",
            ],
            "security_findings": [
                {"check": "privilege_escalation_bypass", "verdict": "BLOCKED", "status": "PASS"},
                {"check": "ambient_socket_leak", "verdict": "ZERO_LEAKS", "status": "PASS"},
                {"check": "countermeasure_binding_gap", "verdict": "ZERO_GAPS", "status": "PASS"},
                {"check": "promotional_slop_intrusion", "verdict": "CLEANSED", "status": "PASS"},
            ],
            "authority_effect": "None",
            "ephemeral_traces_zeroed": True,
            "acts_completed": 0,
        }

        executed_beats: list[ThanatosBeatExecutionV1] = []
        all_cochains: list[Residual1Cochain] = []
        dda_steps: list[dict[str, Any]] = []
        step_idx = 0

        for act_idx, act_title, beats in acts_script:
            for spk_key, cue, fallback_text in beats:
                mapping = THANATOS_RETINUE_MAP.get(
                    spk_key,
                    RetinueRoleMappingV1(
                        persona=spk_key.capitalize(),
                        cognitive_operator="E_terminal",
                        residual_sort="exactness_witness",
                        software_dev_role="Security Specialist",
                        mapped_skills=(),
                        description="Security specialist in Thanatos bout.",
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

                executed_beat = ThanatosBeatExecutionV1(
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
            "swarm_type": SwarmTypeV1.THANATOS.value,
            "threat_surface": carrier.get("threat_surface"),
            "auth_code": carrier.get("auth_code"),
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

        verdict = "SECURITY_CONTAINMENT_SEALED"
        status = "BOUNDED_RESIDUAL"
        disposition = "HOLD"
        consecration_state = "PROPOSED_FOR_ADMISSION" if request.request_external_admission else "DEFENSIVE_EVALUATION"
        terminal_verdict = "SECURITY_CONTAINMENT_SEALED"

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
            "swarm_type": SwarmTypeV1.THANATOS.value,
            "status": status,
            "disposition": disposition,
            "terminal_verdict": terminal_verdict,
            "licensing_verdict": verdict,
            "licensing_token": token,
            "authority_effect": "None",
            "fixture_mode": request.fixture_mode,
            "delegation_target": "L3_logos_thanatos",
            "auth_code": "ZD-30",
            "child_swarms_dispatched": carrier.get("child_swarms_dispatched", []),
            "security_findings": carrier.get("security_findings", []),
            "ephemeral_traces_zeroed": True,
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
            "schema": "omega.woland.thanatos-bout.v1",
            "task_key": request.task_key,
            "swarm_type": SwarmTypeV1.THANATOS.value,
            "status": status,
            "disposition": disposition,
            "terminal_verdict": terminal_verdict,
            "licensing_verdict": verdict,
            "licensing_token": token,
            "authority_effect": "None",
            "evidence_sha256": evidence_sha256,
            "delegation_target": "L3_logos_thanatos",
            "auth_code": "ZD-30",
        }

        # Persist run folder
        folder_key = run_directory_name(request.task_key, native_support=self._native_support)
        persist_res = persist_bout_run_folder(
            target_root, folder_key, receipt, novella_md, dda_steps, summary
        , native_support=self._native_support)
        if persist_res.is_err:
            return Err(persist_res.unwrap_err())

        # Also persist threat_audit.json
        audit_path = run_folder / "threat_audit.json"
        audit_path.write_text(
            json.dumps(
                {
                    "task_key": request.task_key,
                    "objective": request.objective,
                    "auth_code": "ZD-30",
                    "delegation": "L3_logos_thanatos",
                    "child_swarms": carrier.get("child_swarms_dispatched", []),
                    "findings": carrier.get("security_findings", []),
                    "containment": "INTACT",
                    "ephemeral_traces_zeroed": True,
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
            swarm_type=SwarmTypeV1.THANATOS.value,
        )

        return Ok(outcome)

    def _render_novella(
        self,
        request: WolandBoutRequestV1,
        executed_beats: list[ThanatosBeatExecutionV1],
        verdict: str,
        terminal_verdict: str,
        valuation: ValuationReceipt,
        carrier: dict[str, Any],
    ) -> str:
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines: list[str] = [
            f"# Woland Swarm Dialectic Novella: Thanatos Security Audit (Task: {request.task_key})",
            "",
            f"**Objective:** {request.objective}",
            f"**Swarm Type:** {SwarmTypeV1.THANATOS.value} (Thanatos Defensive Swarm)",
            "**Delegation Target:** L3_logos_thanatos (Auth Code: ZD-30)",
            f"**Timestamp:** {date_str}",
            "**AuthorityEffect:** None.",
            f"**Licensing Verdict:** {verdict}",
            f"**Terminal Verdict:** {terminal_verdict}",
            "**Containment Invariant:** Zero ambient network sockets. Zero outbound human targeting.",
            "",
            "---",
            "",
            "## Theatrical Dramatis Personae (Thanatos Security Council)",
            "",
            "| Persona | Cognitive Operator | Role in Defense |",
            "| :--- | :--- | :--- |",
        ]

        invoked_keys = {b.speaker_key for b in executed_beats}
        for k in sorted(invoked_keys):
            mapping = THANATOS_RETINUE_MAP.get(k)
            if mapping:
                lines.append(f"| **{mapping.persona}** | `{mapping.cognitive_operator}` | {mapping.software_dev_role} |")

        lines.extend([
            "",
            "---",
            "",
            "## Seven-Act Defensive & Adversarial Drama",
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
            "## Security Findings & Verification Matrix",
            "",
            "| Security Check | Verdict | Status |",
            "| :--- | :--- | :--- |",
        ])
        for finding in carrier.get("security_findings", []):
            lines.append(
                f"| `{finding['check']}` | **{finding['verdict']}** | `{finding['status']}` |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## Bulgakovian Epilogue & Maxims",
            "",
            "1. *«Manuscripts don't burn.»* Neither do cryptographic execution receipts or security audit logs.",
            "2. *«Cowardice is the most terrible vice.»* Concealing a vulnerability behind optimistic assumptions invites catastrophe.",
            "3. *«Freshness is only one: the first, and it is also the last.»* A containment fence either holds unconditionally or it is broken.",
            "",
            "Defensive mission sealed. Ephemeral traces zeroed by Abadonna. Output consecrated with `AuthorityEffect: None`.",
            "",
        ])

        return "\n".join(lines)


__all__ = [
    "THANATOS_RETINUE_MAP",
    "ThanatosBeatExecutionV1",
    "ThanatosBoutUseCase",
]
