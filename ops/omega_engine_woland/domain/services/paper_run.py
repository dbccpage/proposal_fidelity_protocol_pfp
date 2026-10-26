"""Domain services for PaperRunGraph research repair calculus.

AuthorityEffect: None.
Stateless domain calculations, obligation policy derivation, stage planning,
and fail-closed ROP transition validation. Zero host I/O.
"""

from __future__ import annotations

from typing import Any, Iterable

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.research.enums import AUTHORITY_EFFECT
from omega_engine_woland.domain.research.errors import PaperRunGraphError
from omega_engine_woland.domain.research.obligation_node import ObligationNode
from omega_engine_woland.domain.research.stage_spec import RIP_PAPERS_STAGE_PIPELINE
from omega_engine_woland.domain.research.transition_event import TransitionEvent

# Allowed events per role
ROLE_ALLOWED_EVENTS: dict[str, frozenset[str]] = {
    "proposer": frozenset(
        {
            "candidate_patch",
            "new_obligation",
            "proof_attempt",
            "countermodel_candidate",
        }
    ),
    "evaluator": frozenset(
        {
            "finding",
            "measurement",
            "local_gate_disposition",
            "evaluation_receipt",
        }
    ),
    "witness": frozenset(
        {
            "correspondence_admitted",
            "correspondence_refused",
            "witness_receipt",
        }
    ),
    "authorizer": frozenset(
        {
            "human_accept",
            "human_reject",
            "human_hold",
            "promotion_decision",
        }
    ),
}

GLOBAL_FORBIDDEN = frozenset(
    {
        "global_green",
        "authority_mint",
        "self_authorize",
        "fabricate_evidence",
    }
)


class ObligationPolicyService:
    """Pure domain service for claim-to-obligation policy derivation."""

    @staticmethod
    def kind_from_mechanization_class(mech: str) -> str:
        m = (mech or "").upper()
        if "LEAN" in m and "TOY" not in m:
            return "mechanization"
        if "LEAN_TOY" in m or "TOY" in m:
            return "theorem"
        if "PYTHON" in m or "NUMERICAL" in m or "INSTANCE" in m or "EXACT" in m:
            return "computational"
        if "SCOPE" in m or "FENCE" in m or "NONCLAIM" in m:
            return "scope_fence"
        if "PROSE" in m:
            return "theorem"
        if "CITATION" in m or "LITERATURE" in m:
            return "literature"
        return "unknown"

    @staticmethod
    def obligations_for_kind(kind: str) -> list[str]:
        k = str(getattr(kind, "value", kind)).lower()
        table: dict[str, list[str]] = {
            "definition": ["prose_consistency"],
            "theorem": ["prose_proof", "countermodel"],
            "mechanization": ["lean_kernel", "prose_lean_binding", "prose_proof"],
            "computational": ["code_test", "replay"],
            "empirical": ["replay", "citation"],
            "literature": ["citation"],
            "release": ["package_build", "hash_audit"],
            "scope_fence": ["nonclaim_fence"],
            "unknown": ["prose_consistency"],
        }
        return list(table.get(k, ["prose_consistency"]))

    @classmethod
    def derive_obligations(cls, claims: Iterable[Any]) -> list[Any]:
        obligations: list[ObligationNode] = []
        for c in claims:
            kind_str = str(getattr(c, "kind", "unknown"))
            mech_class = str(getattr(c, "mechanization_class", "") or "")
            lean_na = str(getattr(c, "lean_na_reason", "") or "")
            claim_id = str(getattr(c, "claim_id", ""))

            for ok in cls.obligations_for_kind(kind_str):
                if ok in ("lean_kernel", "prose_lean_binding"):
                    if lean_na or "TOY" in mech_class.upper():
                        obligations.append(
                            ObligationNode(
                                obligation_id=f"{claim_id}:{ok}",
                                claim_id=claim_id,
                                kind=ok,
                                disposition="not_applicable",
                            )
                        )
                        continue
                obligations.append(
                    ObligationNode(
                        obligation_id=f"{claim_id}:{ok}",
                        claim_id=claim_id,
                        kind=ok,
                        disposition="unchecked",
                    )
                )
        return obligations


class StagePipelinePlanningService:
    """Pure domain service for mapping active obligations to host stage pipelines."""

    @staticmethod
    def stages_for_obligations(obs: Iterable[Any]) -> list[str]:
        needed: set[str] = {
            "stage_0_redteam",
            "stage_4_release_preflight",
            "stage_omega_omc",
        }
        obs_set = {str(getattr(o, "value", getattr(o, "kind", o))) for o in obs}
        if obs_set & {
            "prose_proof",
            "prose_consistency",
            "countermodel",
            "nonclaim_fence",
            "citation",
        }:
            needed.update({"stage_1_improver", "stage_2_adversary"})
        if obs_set & {
            "lean_kernel",
            "prose_lean_binding",
        }:
            needed.add("stage_3_proof_signoff")
        if obs_set & {
            "code_test",
            "mutation",
            "replay",
            "package_build",
            "hash_audit",
        }:
            needed.update({"stage_4_release_preflight", "stage_5_build_public_object"})

        order = {s.stage_id: s.order for s in RIP_PAPERS_STAGE_PIPELINE}
        return sorted(needed, key=lambda sid: order.get(sid, 99))

    @classmethod
    def recompute_stages(
        cls,
        obligations: Iterable[Any],
        dev_only: bool = False,
    ) -> tuple[list[str], list[str], list[str]]:
        active_kinds = [
            str(getattr(o, "kind", o))
            for o in obligations
            if str(getattr(o, "disposition", "unchecked")) != "not_applicable"
        ]
        required = cls.stages_for_obligations(active_kinds)
        all_ids = [s.stage_id for s in RIP_PAPERS_STAGE_PIPELINE]
        notes: list[str] = []
        if dev_only:
            dev_excluded = {"stage_5_build_public_object", "stage_omega_omc"}
            required = [s for s in required if s not in dev_excluded]
            notes.append(
                "dev-only mode active: skipping paper-build (stage 5) and OMC red team (stage Ω)."
            )
        skipped = [s for s in all_ids if s not in required]
        return required, skipped, notes


class TransitionValidatorService:
    """Pure domain service enforcing fail-closed research state transitions under ROP."""

    @staticmethod
    def validate_transition(ev: Any) -> Result[None, Refusal]:
        ae = str(getattr(ev, "authority_effect", "None") or "None")
        if ae not in ("None", ""):
            return Err(
                Refusal(
                    code="ILLEGAL_AUTHORITY_EFFECT",
                    message=f"illegal authority_effect {ae!r}; machine ceiling is None",
                    locus="TransitionValidatorService",
                )
            )

        et = (str(getattr(ev, "event_type", "")) or "").strip()
        if not et:
            return Err(
                Refusal(
                    code="EVENT_TYPE_REQUIRED",
                    message="event_type required",
                    locus="TransitionValidatorService",
                )
            )

        if et.lower() in GLOBAL_FORBIDDEN or et in GLOBAL_FORBIDDEN:
            return Err(
                Refusal(
                    code="GLOBALLY_FORBIDDEN_EVENT",
                    message=f"globally forbidden event: {et}",
                    locus="TransitionValidatorService",
                )
            )

        role_str = str(getattr(ev, "role", "")).lower()
        if role_str not in ROLE_ALLOWED_EVENTS:
            return Err(
                Refusal(
                    code="UNKNOWN_ROLE",
                    message=f"unknown role {role_str!r}",
                    locus="TransitionValidatorService",
                )
            )

        if bool(getattr(ev, "post_build", False)) and bool(
            getattr(ev, "source_mutated_after_build", False)
        ):
            return Err(
                Refusal(
                    code="POST_BUILD_MUTATION_REFUSED",
                    message="post-build source mutation without rebuild/new digest is refused",
                    locus="TransitionValidatorService",
                )
            )

        claims_pass = bool(getattr(ev, "claims_pass", False))
        if role_str == "proposer" and (
            claims_pass or et in ("evaluation_pass", "PASS", "evaluator_pass")
        ):
            return Err(
                Refusal(
                    code="PROPOSER_PASS_REFUSED",
                    message="proposer cannot emit evaluator PASS",
                    locus="TransitionValidatorService",
                )
            )

        if role_str == "evaluator" and et in (
            "candidate_patch",
            "source_edit",
            "claim_promotion",
        ):
            return Err(
                Refusal(
                    code="EVALUATOR_MUTATION_REFUSED",
                    message="evaluator cannot mutate candidate or promote claims",
                    locus="TransitionValidatorService",
                )
            )

        if et in ("promotion_decision", "human_accept") and role_str != "authorizer":
            return Err(
                Refusal(
                    code="UNAUTHORIZED_PROMOTION",
                    message="only authorizer (human/host) may promote or ACCEPT",
                    locus="TransitionValidatorService",
                )
            )

        if role_str == "witness" and et in ("candidate_patch", "source_edit"):
            return Err(
                Refusal(
                    code="WITNESS_MUTATION_REFUSED",
                    message="witness cannot produce candidate patches",
                    locus="TransitionValidatorService",
                )
            )

        allowed = ROLE_ALLOWED_EVENTS[role_str]
        if et not in allowed:
            return Err(
                Refusal(
                    code="ROLE_EVENT_NOT_ALLOWED",
                    message=f"role {role_str} may not emit event {et!r}; allowed={sorted(allowed)}",
                    locus="TransitionValidatorService",
                )
            )

        carrier_hash = str(getattr(ev, "carrier_hash", "") or "").strip()
        if not carrier_hash:
            return Err(
                Refusal(
                    code="CARRIER_HASH_REQUIRED",
                    message="carrier_hash required on every transition",
                    locus="TransitionValidatorService",
                )
            )

        return Ok(None)

    @classmethod
    def validate_transition_dict(cls, d: dict[str, Any]) -> Result[None, Refusal]:
        ev = TransitionEvent(
            role=str(d.get("role") or ""),
            event_type=str(d.get("event_type") or ""),
            carrier_hash=str(d.get("carrier_hash") or ""),
            candidate_hash=str(d.get("candidate_hash") or ""),
            post_build=bool(d.get("post_build")),
            source_mutated_after_build=bool(d.get("source_mutated_after_build")),
            claims_pass=bool(d.get("claims_pass")),
            authority_effect=str(d.get("authority_effect") or AUTHORITY_EFFECT),
        )
        return cls.validate_transition(ev)

    @classmethod
    def validate_transition_or_raise(cls, ev: Any) -> None:
        res = cls.validate_transition(ev)
        if res.is_err:
            ref = res.unwrap_err()
            raise PaperRunGraphError(ref.message)


__all__ = [
    "GLOBAL_FORBIDDEN",
    "ObligationPolicyService",
    "ROLE_ALLOWED_EVENTS",
    "StagePipelinePlanningService",
    "TransitionValidatorService",
]
