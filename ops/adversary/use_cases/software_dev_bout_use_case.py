"""Software-Dev Shop Bout Use Case & the novelist Panel-to-Techne Mapping.

Under swarm_type="software-dev", the Techne Council exercises complete authority
over all code generation, testing, refactoring, architecture, and code review.
the novelistian Panel characters map directly to operational techne* skills.

AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Sequence

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
    EMPTY_RESIDUAL,
    Residual,
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

_LOCUS = "adversary.use_cases.software_dev_bout_use_case"


@dataclass(frozen=True)
class PanelRoleMappingV1:
    """Mapping of a the novelistian Panel persona to its cognitive operator and operational skills."""

    persona: str
    cognitive_operator: str
    residual_sort: str
    software_dev_role: str
    mapped_skills: tuple[str, ...]
    description: str


SOFTWARE_DEV_PANEL_MAP: dict[str, PanelRoleMappingV1] = {
    "adversary": PanelRoleMappingV1(
        persona="Adversary",
        cognitive_operator="E_terminal",
        residual_sort="exactness_witness",
        software_dev_role="Sovereign Gatekeeper & Terminal Judge",
        mapped_skills=(),
        description="Evaluates evidence receipt; issues PASS_TO_MASTER, REFUSE, or OPEN_RESIDUAL.",
    ),
    "defect_hunter": PanelRoleMappingV1(
        persona="Defect Hunter",
        cognitive_operator="E_nocebo",
        residual_sort="isolation_residual",
        software_dev_role="Senior Adversarial Architect & Code Reviewer",
        mapped_skills=(
            "techne-code-inspector",
            "github",
            "techne-code-contracts-adversary",
        ),
        description="Plunges code into nocebo failure; exposes local-green test illusions.",
    ),
    "gauge_breaker": PanelRoleMappingV1(
        persona="Gauge Breaker",
        cognitive_operator="E_surprise",
        residual_sort="presentation_gauge",
        software_dev_role="Chaos Monkey & 9-Dot Surprise Solver",
        mapped_skills=(
            "techne-code-search-solver-developer",
            "ow-bureau-gauge-breaks",
            "techne-code-normal-forms-developer",
        ),
        description="Repairs primus stoves; injects lateral reframing when stuck.",
    ),
    "scope_guard": PanelRoleMappingV1(
        persona="Scope Guard",
        cognitive_operator="E_scope",
        residual_sort="scope_violation",
        software_dev_role="Scope Muscle & Crate Firewall Assassin",
        mapped_skills=(
            "techne-base-swarm-inward-purity-auditor",
            "techne-uncalled-module-detector",
            "techne-test-silent-skip-detector",
        ),
        description="Enforces 10-round cap; eliminates zombie modules and uncalled code.",
    ),
    "syntax_prefilter": PanelRoleMappingV1(
        persona="Syntax Prefilter",
        cognitive_operator="E_hygiene",
        residual_sort="syntax_hygiene",
        software_dev_role="Cold Syntax Vampire & Pre-Filter",
        mapped_skills=(
            "techne-docs-lint-hunter-killer",
            "techne-comment-slop-hunter-killer",
            "auto-anti-pattern-lint",
        ),
        description="Stateless deterministic hygiene; eliminates whitespace, slop, and linter warnings.",
    ),
    "master": PanelRoleMappingV1(
        persona="Manuscript Truth",
        cognitive_operator="E_formal",
        residual_sort="exactness_witness",
        software_dev_role="Deep Core Mechanizer & Rust/Lean Builder",
        mapped_skills=(
            "techne-code-rust-principal-developer",
            "techne-code-builder",
        ),
        description="Dispatched after PASS_TO_MASTER; writes sovereign zero-allocation Rust and Lean 4.",
    ),
    "primal_dual": PanelRoleMappingV1(
        persona="Primal Dual",
        cognitive_operator="E_placebo",
        residual_sort="prior_lock_residual",
        software_dev_role="Refactoring Savior & High-Agency Architect",
        mapped_skills=(
            "techne-code-principal-architect",
            "techne-code-clean-arch",
        ),
        description="Converts nocebo despair into structural refactoring and clean decoupling.",
    ),
    "scar_chronicler": PanelRoleMappingV1(
        persona="Scar Chronicler",
        cognitive_operator="E_predictive",
        residual_sort="prediction_error",
        software_dev_role="Converted Scribe & Regression Chronicler",
        mapped_skills=(
            "techne-code-rust-tester",
            "techne-code-python-tester",
            "auto-docs",
        ),
        description="Chronicler of run journals and past trauma; writes regression tests against scars.",
    ),
    "anti_hype": PanelRoleMappingV1(
        persona="Anti-Hype",
        cognitive_operator="E_anti_hype",
        residual_sort="claim_hygiene",
        software_dev_role="Anti-Hype Master of Ceremonies Target",
        mapped_skills=(
            "techne-comment-slop-hunter-killer",
            "glossa-claim-hygiene-linter",
        ),
        description="Head is severed whenever promotional words, vanity comments, or unearned claims appear.",
    ),
    "bare_metal_anchor": PanelRoleMappingV1(
        persona="Bare Metal Anchor",
        cognitive_operator="E_yankee_solver",
        residual_sort="executable_runtime",
        software_dev_role="Yankee Physicist & Ground Reality Anchor",
        mapped_skills=(
            "panep-math-and-physics-prof",
            "techne-code-math-search-solver-leader",
        ),
        description="Fast math checker; hyperbole-intolerant executable runtime filter.",
    ),
    "resilience": PanelRoleMappingV1(
        persona="Resilience",
        cognitive_operator="E_luda_resilience",
        residual_sort="stable_equilibrium",
        software_dev_role="Strict Resilience & Engineering VP",
        mapped_skills=(
            "techne-svp",
            "techne-vp",
        ),
        description="Calm crisis management; controls risk escalation above 0.7.",
    ),
    "overconfidence_probe": PanelRoleMappingV1(
        persona="Overconfidence Probe",
        cognitive_operator="E_overconfidence_probe_gauge_breaker",
        residual_sort="gauge_break",
        software_dev_role="Southern Wit & Overconfidence Puncturer",
        mapped_skills=(
            "techne-code-python-anti-patterns",
            "techne-code-rust-anti-patterns",
        ),
        description="Punctures hubris and over-complicated abstractions with razor-sharp zingers.",
    ),
    "punchlist": PanelRoleMappingV1(
        persona="Punchlist",
        cognitive_operator="E_punchlist_discipline",
        residual_sort="methodical_completion",
        software_dev_role="Punctual Precision & Custody Officer",
        mapped_skills=(
            "techne-mutation-evidence-custody",
            "techne-generated-artifact-custody-auditor",
            "techne-oeops-evidence-receipt-harness",
        ),
        description="Punchlists, byte custody, and verification receipts.",
    ),
    "quarantine": PanelRoleMappingV1(
        persona="Quarantine",
        cognitive_operator="E_flow",
        residual_sort="quarantine",
        software_dev_role="Epistemic Sanatorium Director",
        mapped_skills=(
            ".agents/quarantine",
            "techne-silent-failure-hunter",
        ),
        description="Quarantines non-converging loops, circular imports, and infinite retries.",
    ),
    "hardware_constraint": PanelRoleMappingV1(
        persona="Hardware Constraint",
        cognitive_operator="E_hardware_constraint",
        residual_sort="physical_constraint",
        software_dev_role="Hardware Constraint Enforcer",
        mapped_skills=(),
        description="Enforces memory ceilings, stack depth bounds, and timeout limits.",
    ),
    "integrity_auditor": PanelRoleMappingV1(
        persona="Integrity Auditor",
        cognitive_operator="E_integrity_auditor",
        residual_sort="governance_audit",
        software_dev_role="Governance Cowardice Auditor",
        mapped_skills=("techne-adversarial-refusal-bypass-auditor",),
        description="Exposes hand-washing and unhandled edge cases.",
    ),
}


@dataclass(frozen=True)
class SoftwareDevBeatExecutionV1:
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


class DefaultObstructionValuator:
    """Default deterministic valuator computing exact ValuationReceipt from cochains."""

    def value_cochain(
        self,
        cochain: Residual1Cochain,
        *,
        gamma_2: float = 0.0,
        phi_ret: float = 0.0,
        phi_claim: float = 0.0,
        is_exact_rational: bool = False,
    ) -> ValuationReceipt:
        return ValuationReceipt(
            residual_sort=cochain.residual_sort,
            phi_1=float(cochain.mass),
            gamma_2=float(gamma_2),
            phi_ret=float(phi_ret),
            phi_claim=float(phi_claim),
            is_exact_rational=is_exact_rational,
            diagnostics={"defects": list(cochain.defects)},
            authority_effect="None",
        )

    def value_cochains(
        self,
        cochains: Sequence[Residual1Cochain],
    ) -> ValuationReceipt:
        masses = [c.mass for c in cochains]
        max_mass = max(masses) if masses else 0.0
        total_mass = sum(masses)
        all_defects = tuple(d for c in cochains for d in c.defects)
        return ValuationReceipt(
            residual_sort="exactness_witness",
            phi_1=float(max_mass),
            gamma_2=float(total_mass),
            is_exact_rational=True,
            diagnostics={"defects": list(all_defects)},
            authority_effect="None",
        )


class SoftwareDevBoutUseCase:
    """Theatrical and technical 7-Act software development shop bout under Techne Council."""

    def __init__(
        self,
        repo_root: Path | str | None = None,
        *,
        synthesizer: DialogueSynthesizer | None = None,
        valuator: ObstructionValuatorProtocol | None = None,
        native_support: NativeOperationPort,
    ) -> None:
        self._native_support = native_support
        self.repo_root = Path(repo_root).resolve() if repo_root is not None else Path.cwd()
        self.synthesizer = synthesizer or DialogueSynthesizer()
        self.valuator = valuator or DefaultObstructionValuator()

    def execute_bout(
        self,
        request: AdversaryBoutRequestV1,
        *,
        output_dir: Path | str | None = None,
    ) -> Result[AdversaryBoutOutcomeV1, Refusal]:
        """Execute the 7-Act software dev shop bout across the 16 the novelistian panel characters."""
        target_root = (
            Path(output_dir)
            if output_dir is not None
            else self.repo_root / canonical_intelligence_route("_intelligence/_adversary")
        )
        run_folder = target_root / "runs" / run_directory_name(request.task_key, native_support=self._native_support)

        # Build initial carrier
        carrier: dict[str, Any] = {
            "task_key": request.task_key,
            "objective": request.objective,
            "swarm_type": SwarmTypeV1.SOFTWARE_DEV.value,
            "authority_effect": "None",
            "fixture_mode": request.fixture_mode,
            "initial_status": "unverified",
            "acts_completed": 0,
        }
        if request.carrier_context:
            carrier.update(request.carrier_context)

        # Declarative 7-Act script for the Software Development Shop
        act_scripts: list[dict[str, Any]] = [
            {
                "act_index": 1,
                "act_title": "Act I: Syntax & Claim Pre-Filter (The Variety Theatre Antechamber)",
                "beats": [
                    {
                        "speaker_key": "syntax_prefilter",
                        "cue": "sanitize whitespace and scrub CP1252 mojibake from objective",
                    },
                    {
                        "speaker_key": "anti_hype",
                        "cue": "announce glorious unverified code to the eager Moscow public",
                    },
                ],
            },
            {
                "act_index": 2,
                "act_title": "Act II: Adversarial Code Audit & Nocebo Challenge (The Black Magic Seance)",
                "beats": [
                    {
                        "speaker_key": "defect_hunter",
                        "cue": "expose local-green test illusions and mock missing edge cases",
                    },
                    {
                        "speaker_key": "overconfidence_probe",
                        "cue": "puncture over-engineered class abstractions with sharp southern wit",
                    },
                    {
                        "speaker_key": "integrity_auditor",
                        "cue": "diagnose hemicrania over hand-washing cowardice in silent error handling",
                    },
                ],
            },
            {
                "act_index": 3,
                "act_title": "Act III: Lateral Reframing & 9-Dot Problem Solving (Apartment 50 on Sadovaya)",
                "beats": [
                    {
                        "speaker_key": "gauge_breaker",
                        "cue": "drink kerosene and swap chessboards to escape linear solver deadlock",
                    },
                    {
                        "speaker_key": "bare_metal_anchor",
                        "cue": "cut theoretical bloat and bind real executable runtime cochains",
                    },
                ],
            },
            {
                "act_index": 4,
                "act_title": "Act IV: Structural Architecture & Decoupling (The Flight Over Moscow)",
                "beats": [
                    {
                        "speaker_key": "primal_dual",
                        "cue": "refactor monolithic tangle into cleanly decoupled clean architecture ports",
                    },
                    {
                        "speaker_key": "quarantine",
                        "cue": "quarantine recursive loops and circular dependency hallucinations",
                    },
                ],
            },
            {
                "act_index": 5,
                "act_title": "Act V: Formal Core Mechanization & Implementation (The Basement in the Lane)",
                "beats": [
                    {
                        "speaker_key": "master",
                        "cue": "write zero-allocation sovereign Rust and exact Lean 4 kernels; manuscripts don't burn",
                    },
                ],
            },
            {
                "act_index": 6,
                "act_title": "Act VI: Regression Testing, Scope Ceilings & Custody (The Great Ball of Satan)",
                "beats": [
                    {
                        "speaker_key": "scar_chronicler",
                        "cue": "record bitter past scars and write permanent regression tests into journal",
                    },
                    {
                        "speaker_key": "scope_guard",
                        "cue": "enforce 10-round scope cap and eliminate zombie uncalled modules",
                    },
                    {
                        "speaker_key": "hardware_constraint",
                        "cue": "enforce physical hardware memory ceilings and CPU limits",
                    },
                    {
                        "speaker_key": "punchlist",
                        "cue": "verify punchlist items, compute sha256 digests, and seal byte custody",
                    },
                    {
                        "speaker_key": "resilience",
                        "cue": "stabilize team equilibrium and maintain calm Strict resilience",
                    },
                ],
            },
            {
                "act_index": 7,
                "act_title": "Act VII: Sovereign Gatekeeper Evaluation & Reality Sealing (Sparrow Hills Sunset)",
                "beats": [
                    {
                        "speaker_key": "adversary",
                        "cue": "weigh exact cochain measurements and seal the terminal reality verdict",
                    },
                ],
            },
        ]

        executed_beats: list[SoftwareDevBeatExecutionV1] = []
        all_cochains: list[Residual1Cochain] = []
        absorbed_res = EMPTY_RESIDUAL
        dda_steps: list[dict[str, Any]] = []

        step_idx = 0
        for act in act_scripts:
            act_idx = act["act_index"]
            act_title = act["act_title"]

            for beat_spec in act["beats"]:
                spk_key = beat_spec["speaker_key"]
                cue = beat_spec["cue"]
                mapping = SOFTWARE_DEV_PANEL_MAP.get(
                    spk_key,
                    PanelRoleMappingV1(
                        persona=spk_key.capitalize(),
                        cognitive_operator="E_generic",
                        residual_sort="product_edge_residual",
                        software_dev_role="Panel Participant",
                        mapped_skills=(),
                        description="Generic participant.",
                    ),
                )

                # 1. Transform carrier and extract residual cochain via operator
                pkg = CharacterOperatorRegistry.get_operator_package(spk_key)
                carrier_prev = dict(carrier)
                carrier = pkg.apply_transform(carrier)
                cochain = pkg.extract_residual(carrier_prev, carrier)
                all_cochains.append(cochain)
                absorbed_res = absorbed_res.absorb(Residual(cochain.defects, cochain.mass))

                # 2. Synthesize theatrical dialogue
                dialogue_res = self.synthesizer.render_dialogue(mapping.persona, cue)
                dialogue = dialogue_res.value if dialogue_res.is_ok else f"[{mapping.persona}]: «{cue}.»"

                delta = {
                    k: v
                    for k, v in carrier.items()
                    if k not in carrier_prev or carrier_prev[k] != v
                }

                executed_beat = SoftwareDevBeatExecutionV1(
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

                # 3. Record DDA deformation action
                step_idx += 1
                dda_steps.append({
                    "step_index": step_idx,
                    "act": act_idx,
                    "character": mapping.persona,
                    "operator": mapping.cognitive_operator,
                    "skills_declared": list(mapping.mapped_skills),
                    "skills_executed": [],
                    "residual_sort": mapping.residual_sort,
                    "delta": delta,
                })

            carrier["acts_completed"] = act_idx

        # Value obstruction
        valuation = self.valuator.value_cochains(tuple(all_cochains))

        # Licensing boundary verdict
        evidence_payload = {
            "task_key": request.task_key,
            "objective": request.objective,
            "swarm_type": SwarmTypeV1.SOFTWARE_DEV.value,
            "beats_count": len(executed_beats),
            "cochains_count": len(all_cochains),
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

        if request.fixture_mode:
            verdict = "PASS_TO_MASTER"
            status = "BOUNDED_RESIDUAL"
            disposition = "HOLD"
            consecration_state = "PROPOSED_FOR_ADMISSION" if request.request_external_admission else "FIXTURE_EVALUATION"
            terminal_verdict = "FIXTURE_PASS_TO_MASTER"
        else:
            if is_licensed:
                verdict = "PASS_TO_MASTER"
                status = "AUTHORIZED"
                disposition = "SELECT"
                consecration_state = "PROPOSED_FOR_EXTERNAL_ADMISSION" if request.request_external_admission else "CONSECRATED_TOWER"
                terminal_verdict = "PASS_TO_MASTER"
            else:
                verdict = "REFUSE" if valuation.has_defects() else "OPEN_RESIDUAL"
                status = "REFUSED" if valuation.has_defects() else "BOUNDED_RESIDUAL"
                disposition = "COMPOSTED"
                consecration_state = "COMPOSTED_WITH_REENTRY_GUIDANCE"
                terminal_verdict = verdict

        # Render full 7-act the novelistian novella
        novella_md = self._render_novella(
            request=request,
            executed_beats=executed_beats,
            verdict=verdict,
            terminal_verdict=terminal_verdict,
            valuation=valuation,
        )

        # Build summary and receipt
        summary: dict[str, Any] = {
            "task_key": request.task_key,
            "objective": request.objective,
            "swarm_type": SwarmTypeV1.SOFTWARE_DEV.value,
            "status": status,
            "disposition": disposition,
            "terminal_verdict": terminal_verdict,
            "licensing_verdict": verdict,
            "licensing_token": token,
            "authority_effect": "None",
            "fixture_mode": request.fixture_mode,
            "panel_characters_invoked": list({b.persona for b in executed_beats}),
            "techne_skills_declared": sorted({s for b in executed_beats for s in b.mapped_skills}),
            "techne_skills_invoked": [],
            "executed_operations": [
                {'speaker': b.speaker_key, 'operation': 'CharacterOperatorRegistry.get_operator_package',
                 'effects': ['apply_transform', 'extract_residual']} for b in executed_beats],
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
            "schema": "core.adversary.software-dev-bout.v1",
            "task_key": request.task_key,
            "swarm_type": SwarmTypeV1.SOFTWARE_DEV.value,
            "status": status,
            "disposition": disposition,
            "terminal_verdict": terminal_verdict,
            "licensing_verdict": verdict,
            "licensing_token": token,
            "authority_effect": "None",
            "evidence_sha256": evidence_sha256,
        }

        # Persist to disk
        folder_key = run_directory_name(request.task_key, native_support=self._native_support)
        persist_res = persist_bout_run_folder(
            target_root, folder_key, receipt, novella_md, dda_steps, summary
        , native_support=self._native_support)
        if persist_res.is_err:
            return Err(persist_res.unwrap_err())

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
            is_authorized=(status == "AUTHORIZED"),
            measurement_status=meas_status,
            checker_verdict="NOT_MEASURED",
            checker_receipt_sha256=None,
            authorization_blockers=(),
            authorization_evidence=None,
            swarm_type=SwarmTypeV1.SOFTWARE_DEV.value,
        )

        return Ok(outcome)

    def _render_novella(
        self,
        request: AdversaryBoutRequestV1,
        executed_beats: Sequence[SoftwareDevBeatExecutionV1],
        verdict: str,
        terminal_verdict: str,
        valuation: Any,
    ) -> str:
        """Render an authentic 7-act the novelistian theatrical novella in markdown."""
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines: list[str] = [
            "# Novella: The Moscow Software Development Shop",
            f"**Task Key:** `{request.task_key}`  ",
            "**Swarm Type:** `software-dev` (Techne Council Sovereign Execution)  ",
            f"**Date:** `{now_str}`  ",
            "**AuthorityEffect:** `None`  ",
            f"**Terminal Verdict:** `{terminal_verdict}`  ",
            "",
            "> *«Manuscripts don't burn!»* — the novelist  ",
            "> *«Cowardice is the most terrible vice.»*  ",
            "> *«Freshness is only one: the first, and it is also the last.»*  ",
            "",
            "---",
            "",
            "## Objective",
            f"{request.objective}",
            "",
            "---",
        ]

        current_act = 0
        for beat in executed_beats:
            if beat.act_index != current_act:
                current_act = beat.act_index
                lines.append(f"\n### {beat.act_title}\n")

            skills_str = ", ".join(f"`{s}`" for s in beat.mapped_skills) if beat.mapped_skills else "*none (direct operator)*"
            lines.append(
                f"**{beat.persona}** (*{beat.operator_tag}* / `{beat.residual_sort}` | Skills: {skills_str}):  \n"
                f"{beat.dialogue}\n"
            )

        lines.extend([
            "---",
            "",
            "## Act VII Resolution: The Grand Terminal Seal",
            f"The sovereign gatekeeper Adversary reviewed the accumulated cochains: maximum mass $\\Phi_1 = {valuation.phi_1}$, "
            f"total mass $\\Gamma_2 = {valuation.gamma_2}$, and defect count $= {len(valuation.diagnostics.get('defects', []))}$.",
            "",
            f"Adversary waved a long, pale hand: *«{verdict}!»*",
            "The manuscript was bound, verified against structural reality, and handed to Manuscript Truth.",
            "All ephemeral traces were accounted for by Backdoor Auditor, and the immutable receipt was sealed without promotional words or vanity.",
            "",
            "```machine",
            f"STATUS={verdict}",
            f"TERMINAL_VERDICT={terminal_verdict}",
            "AUTHORITY_EFFECT=None",
            f"TASK_KEY={request.task_key}",
            "```",
        ])

        return "\n".join(lines)


__all__ = [
    "PanelRoleMappingV1",
    "SOFTWARE_DEV_PANEL_MAP",
    "SoftwareDevBeatExecutionV1",
    "SoftwareDevBoutUseCase",
]
