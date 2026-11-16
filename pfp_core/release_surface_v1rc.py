"""Additive release surface for the v1.0rc funnel, six-arm receipts, and guest replay.

AuthorityEffect: None.

What this supports: deterministic Tier-1 enumeration over in-memory workflow blocks,
USD 0.00 rejection of port, budget, and self-intolerant candidates, offline role
adapters, and exact rational comparisons of six sealed arms.

What this does not support: a live model spend, a positive held-out transfer claim
when the sealed delta is zero or negative, or any edit inside frozen workflow folders.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from eis.domain.thymus import ThymusGate
from eis.domain.value_objects import REGEX_MATCHER_ID, DetectorRule
from operads.skill_operad.ddc_operad_parser import require_operad_colour
from pfp_core.fidelity import WholeRunBudget, sha256_hex
from pfp_core.funnel_v1rc import generate_python_workflow_permutations
from pfp_core.operad_pipe import TypedOp, compose
from pfp_core.sequential_ablation_v1rc import exact_mcnemar_fraction, holm_bonferroni_adjust

AUTHORITY_NONE = "None"
CAMPAIGN_CAP_MICROUSD = 5_000_000
ROLE_OPUS = "opus-5.5-xhigh"
ROLE_FABLE = "fable-5.2"
ROLES = frozenset({ROLE_OPUS, ROLE_FABLE})
STRUCTURAL_BLOCKS = (
    "staged_packet",
    "coboundary_scratchpad",
    "am4_stationary_loop",
    "lggr_local_to_global",
    "decode_trie_mask",
    "hinted_retraction",
    "checker_synthesis_gate",
)
LEARNING_TASKS = ("C011", "C012", "C014", "C018", "C028", "C041")
HOLDOUT_TASKS = ("H_JORDAN_WIGNER", "H_BRAVYI_KITAEV", "H_CONTEXTUALITY", "H_WF52", "H_WF53")
ARM_IDS = (
    "arm1_direct",
    "arm2_best_of_k",
    "arm3_pfp_only",
    "arm4_naive_memory",
    "arm5_pfp_eis_operads_no_compression",
    "arm6_full_allopoietic_v1rc",
)
CLEAN_PANEL = ("CLEAN_SELF_FIXTURE_ALPHA", "CLEAN_SELF_FIXTURE_BETA")
_ATLAS_MATCHES = Path(__file__).resolve().parents[1] / "atlas" / "atlas_claim_matches.json"


def _canon(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canon(payload).encode("utf-8")).hexdigest()


def require_canon_colour_name(name: str) -> str:
    """Refuse a colour name the DDC parser would not admit. Delegates to the parser."""
    return require_operad_colour(name).value


def pciv_strict_pareto_admits(
    baseline_pass_rate: Fraction,
    treated_pass_rate: Fraction,
    baseline_tokens: int,
    treated_tokens: int,
    baseline_calls: int,
    treated_calls: int,
) -> bool:
    """Admit a replacement only on a strict pass-rate rise, or a strict cost drop at a non-inferior rate.

    Cost is the sum of token count and call count. A tie on both axes is a rejection.
    """
    if type(baseline_pass_rate) is not Fraction or type(treated_pass_rate) is not Fraction:
        raise TypeError("pass rates must be exact Fraction values")
    for name, value in (
        ("baseline_tokens", baseline_tokens),
        ("treated_tokens", treated_tokens),
        ("baseline_calls", baseline_calls),
        ("treated_calls", treated_calls),
    ):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a nonnegative int")
    if treated_pass_rate > baseline_pass_rate:
        return True
    if treated_pass_rate < baseline_pass_rate:
        return False
    baseline_cost = baseline_tokens + baseline_calls
    treated_cost = treated_tokens + treated_calls
    return treated_cost < baseline_cost


@dataclass(frozen=True)
class DeterministicRejectV1:
    candidate_id: str
    reason: str
    usd_cost: Fraction

    def __post_init__(self) -> None:
        if self.reason not in {"port_mismatch", "budget_exceeded", "self_intolerant"}:
            raise ValueError(f"unknown reject reason {self.reason!r}")
        if self.usd_cost != Fraction(0):
            raise ValueError("deterministic rejects are recorded at USD 0")


def clean_panel_false_refusals() -> int:
    """Count ThymusGate refusals of a rule that matches nothing on the clean self-panel.

    The probe pattern is absent from every clean fixture, so a correct screen admits it.
    """
    probe = DetectorRule(
        rule_id="clean_panel_nonmatch",
        target_epitope="absent_marker",
        match_pattern="NO_SUCH_CLEAN_MARKER",
        matcher_id=REGEX_MATCHER_ID,
    )
    screen = ThymusGate(self_panel=CLEAN_PANEL).evaluate_rule(probe)
    return 0 if screen.is_admitted else 1


def collect_deterministic_rejects(*, token_budget: int = 64) -> tuple[DeterministicRejectV1, ...]:
    """Build three illegal candidates and reject them before any provider call."""
    if type(token_budget) is not int or token_budget < 1:
        raise ValueError("token_budget must be a positive int")
    rejects: list[DeterministicRejectV1] = []

    mismatched = [
        TypedOp("gen_proof", "State", "Proof", "generate", prompt_digest="proof", cost_tokens=4),
        TypedOp("chk_code", "Code", "Receipt", "check", checker_id="host.public_smoke", cost_tokens=2),
    ]
    try:
        compose(mismatched)
    except TypeError:
        rejects.append(DeterministicRejectV1("reject_port_mismatch", "port_mismatch", Fraction(0)))
    else:
        raise RuntimeError("PORT_MISMATCH_NOT_REJECTED")

    over_budget = TypedOp(
        "ctx_over_budget",
        "State",
        "State",
        "context",
        prompt_digest="budget",
        cost_tokens=token_budget + 1,
    )
    if over_budget.cost_tokens > token_budget:
        rejects.append(DeterministicRejectV1("reject_budget", "budget_exceeded", Fraction(0)))

    broad = DetectorRule(
        rule_id="self_intolerant_probe",
        target_epitope="clean_panel_cross_reaction",
        match_pattern="CLEAN_SELF_FIXTURE",
        matcher_id=REGEX_MATCHER_ID,
    )
    screen = ThymusGate(self_panel=CLEAN_PANEL).evaluate_rule(broad)
    if not screen.is_admitted:
        rejects.append(DeterministicRejectV1("reject_self_intolerant", "self_intolerant", Fraction(0)))
    else:
        raise RuntimeError("SELF_INTOLERANT_RULE_ADMITTED")
    return tuple(rejects)


@dataclass(frozen=True)
class PopulationPolicyV1:
    """Ecological reserve plus a cross-family holdout split.

    The reserve keeps one structural block from each family even when that family
    is rare. Holdout families are withheld from strand extraction.
    """

    reserve_per_family: int = 1
    holdout_families: tuple[str, ...] = ("wf52", "wf53", "contextuality", "fermion_mapping")

    def __post_init__(self) -> None:
        if type(self.reserve_per_family) is not int or self.reserve_per_family < 1:
            raise ValueError("reserve_per_family must be a positive int")


def assign_structural_family(index: int) -> str:
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative int")
    return STRUCTURAL_BLOCKS[index % len(STRUCTURAL_BLOCKS)]


def apply_novelty_policy(
    family_by_id: Mapping[str, str],
    policy: PopulationPolicyV1 | None = None,
) -> dict[str, Any]:
    """Keep an ecological reserve and drop holdout-family ids from the extraction set."""
    chosen = policy or PopulationPolicyV1()
    reserve: list[str] = []
    seen: dict[str, int] = {}
    extraction: list[str] = []
    withheld: list[str] = []
    for candidate_id in sorted(family_by_id):
        family = family_by_id[candidate_id]
        if family in chosen.holdout_families:
            withheld.append(candidate_id)
            continue
        count = seen.get(family, 0)
        if count < chosen.reserve_per_family:
            reserve.append(candidate_id)
        extraction.append(candidate_id)
        seen[family] = count + 1
    return {
        "authority_effect": AUTHORITY_NONE,
        "reserve_ids": tuple(reserve),
        "extraction_ids": tuple(extraction),
        "withheld_holdout_ids": tuple(withheld),
        "families_in_reserve": tuple(sorted({family_by_id[item] for item in reserve})),
    }


class RoleAdapterV1:
    """Budget-capped adapter. Replay is the default. Live calls need a manifest digest."""

    def __init__(self, role: str, replay_log: Mapping[str, str] | None = None) -> None:
        if role not in ROLES:
            raise ValueError(f"unknown role {role!r}")
        self.role = role
        self.replay_log = dict(replay_log or {})
        self.live_calls = 0

    def complete(
        self,
        prompt: str,
        *,
        live: bool = False,
        budget: WholeRunBudget | None = None,
        manifest_digest: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if live:
            self._admit_live(budget, manifest_digest)
            self.live_calls += 1
            raise RuntimeError("LIVE_PROVIDER_NOT_CONFIGURED")
        body = self.replay_log.get(prompt)
        if body is None:
            body = f"replay:{self.role}:{sha256_hex(prompt)[:16]}"
        return {
            "authority_effect": AUTHORITY_NONE,
            "role": self.role,
            "live": False,
            "provider_calls": 0,
            "body": body,
            "prompt_sha256": sha256_hex(prompt),
        }

    def _admit_live(self, budget: WholeRunBudget | None, manifest_digest: str | None) -> None:
        if budget is None or not manifest_digest:
            raise ValueError("LIVE_CALL_REQUIRES_WHOLE_RUN_BUDGET_MANIFEST")
        if len(manifest_digest) != 64:
            raise ValueError("manifest_digest must be a SHA-256 hex string")
        if os.environ.get("PFP_LIVE_PROVIDER") != "1" or not os.environ.get("PFP_PROVIDER_API_KEY"):
            raise RuntimeError("LIVE_CREDENTIALS_ABSENT")


def assert_holdout_disjoint(
    train_task_ids: Sequence[str],
    holdout_task_ids: Sequence[str],
    train_prompts: Sequence[str],
    holdout_prompts: Sequence[str],
) -> str:
    """Return the holdout seal, or raise HOLDOUT_CONTAMINATION_REFUSAL.

    Delegates to ``ReceiptToWeightPipelineV1.assert_disjoint_holdout`` when that
    module imports. The same predicate runs here when the weight stack is absent,
    so a missing ``torch`` install does not open the holdout.
    """
    try:
        from pfp_core.llm_mechanisms import ReceiptToWeightPipelineV1  # noqa: PLC0415
    except ModuleNotFoundError as exc:
        if exc.name not in {"torch", "torch.nn", "torch.nn.functional"}:
            raise
        return _holdout_seal(train_task_ids, holdout_task_ids, train_prompts, holdout_prompts)
    return ReceiptToWeightPipelineV1.assert_disjoint_holdout(
        train_prompts,
        holdout_prompts,
        train_task_ids=train_task_ids,
        holdout_task_ids=holdout_task_ids,
    )


def _holdout_seal(
    train_task_ids: Sequence[str],
    holdout_task_ids: Sequence[str],
    train_prompts: Sequence[str],
    holdout_prompts: Sequence[str],
) -> str:
    """Same overlap refusal as ``ReceiptToWeightPipelineV1.assert_disjoint_holdout``."""
    if not holdout_prompts:
        raise ValueError("NONEMPTY_HOLDOUT_SET_REQUIRED")
    train_hashes = {sha256_hex(prompt) for prompt in train_prompts}
    holdout_hashes = {sha256_hex(prompt) for prompt in holdout_prompts}
    overlap_hashes = train_hashes & holdout_hashes
    if overlap_hashes:
        raise ValueError(f"HOLDOUT_CONTAMINATION_REFUSAL: overlapping prompt_sha256 {sorted(overlap_hashes)}")
    overlap_ids = set(train_task_ids) & set(holdout_task_ids)
    if overlap_ids:
        raise ValueError(f"HOLDOUT_CONTAMINATION_REFUSAL: overlapping task_id {sorted(overlap_ids)}")
    body = json.dumps({"holdout_prompt_hashes": sorted(holdout_hashes)}, sort_keys=True, separators=(",", ":"))
    return sha256_hex(body.encode("utf-8"))


def run_tier1_release_batch(*, target_count: int = 1000) -> dict[str, Any]:
    """Enumerate at least ``target_count`` in-memory permutations and quotient them.

    Workflow folders are not written. Deterministic rejects stay at USD 0.00.
    """
    if type(target_count) is not int or target_count < 1000:
        raise ValueError("target_count must be an int >= 1000")
    batch = generate_python_workflow_permutations(max_depth=4, target_count=target_count)
    rejects = collect_deterministic_rejects()
    family_by_id = {
        proposal.proposal_id: assign_structural_family(index)
        for index, proposal in enumerate(batch.python_candidates)
    }
    novelty = apply_novelty_policy(family_by_id)
    holdout_refusal = _planted_holdout_refusal()
    payload = {
        "authority_effect": AUTHORITY_NONE,
        "total_generated": batch.total_generated,
        "lean4_candidates": len(batch.lean4_candidates),
        "unique_quotient_classes": batch.unique_quotient_classes,
        "usd_reject_total": str(sum((item.usd_cost for item in rejects), Fraction(0))),
        "reject_reasons": [item.reason for item in rejects],
        "holdout_refusal": holdout_refusal,
        "reserve_count": len(novelty["reserve_ids"]),
        "provider_calls": 0,
    }
    payload["digest"] = _digest(payload)
    return payload


def _planted_holdout_refusal() -> str:
    try:
        assert_holdout_disjoint(
            LEARNING_TASKS,
            ("C011",),
            ("train-prompt-c011",),
            ("train-prompt-c011",),
        )
    except ValueError as exc:
        text = str(exc)
        if "HOLDOUT_CONTAMINATION_REFUSAL" not in text:
            raise
        return text
    raise RuntimeError("HOLDOUT_OVERLAP_WAS_NOT_REFUSED")


def _arm_outcomes() -> dict[str, dict[str, bool]]:
    """Sealed offline outcomes. Holdout accuracy of arm6 matches arm3 (a null delta)."""
    learn_pass = {
        "arm1_direct": (True, False, True, False, False, True),
        "arm2_best_of_k": (True, True, False, True, False, True),
        "arm3_pfp_only": (True, True, True, False, True, False),
        "arm4_naive_memory": (True, False, False, True, False, False),
        "arm5_pfp_eis_operads_no_compression": (True, True, True, False, True, True),
        "arm6_full_allopoietic_v1rc": (True, True, True, True, False, True),
    }
    holdout_pass = {
        "arm1_direct": (False, False, True, False, False),
        "arm2_best_of_k": (True, False, True, False, True),
        "arm3_pfp_only": (True, False, False, True, False),
        "arm4_naive_memory": (False, False, False, True, False),
        "arm5_pfp_eis_operads_no_compression": (True, False, False, True, False),
        "arm6_full_allopoietic_v1rc": (True, False, False, True, False),
    }
    outcomes: dict[str, dict[str, bool]] = {}
    for arm in ARM_IDS:
        row: dict[str, bool] = {}
        for task, passed in zip(LEARNING_TASKS, learn_pass[arm], strict=True):
            row[task] = passed
        for task, passed in zip(HOLDOUT_TASKS, holdout_pass[arm], strict=True):
            row[task] = passed
        outcomes[arm] = row
    return outcomes


def _tokens_for(arm: str, task: str) -> int:
    base = {
        "arm1_direct": 40,
        "arm2_best_of_k": 160,
        "arm3_pfp_only": 70,
        "arm4_naive_memory": 220,
        "arm5_pfp_eis_operads_no_compression": 110,
        "arm6_full_allopoietic_v1rc": 55,
    }[arm]
    return base + (sum(ord(ch) for ch in task) % 7)


def _paired_delta(left: Mapping[str, bool], right: Mapping[str, bool], tasks: Sequence[str]) -> dict[str, Any]:
    only_left = sum(1 for task in tasks if left[task] and not right[task])
    only_right = sum(1 for task in tasks if right[task] and not left[task])
    both = sum(1 for task in tasks if left[task] and right[task])
    neither = sum(1 for task in tasks if not left[task] and not right[task])
    left_acc = Fraction(sum(1 for task in tasks if left[task]), len(tasks))
    right_acc = Fraction(sum(1 for task in tasks if right[task]), len(tasks))
    return {
        "only_left": only_left,
        "only_right": only_right,
        "both_correct": both,
        "both_incorrect": neither,
        "accuracy_delta": str(left_acc - right_acc),
        "raw_mcnemar_p": str(exact_mcnemar_fraction(only_left, only_right)),
    }


def run_six_arm_offline_campaign() -> dict[str, Any]:
    """Replay six arms from sealed outcomes. Null deltas stay null."""
    outcomes = _arm_outcomes()
    comparisons = {
        "arm6_minus_arm3": _paired_delta(
            outcomes["arm6_full_allopoietic_v1rc"],
            outcomes["arm3_pfp_only"],
            HOLDOUT_TASKS,
        ),
        "arm6_minus_arm2": _paired_delta(
            outcomes["arm6_full_allopoietic_v1rc"],
            outcomes["arm2_best_of_k"],
            HOLDOUT_TASKS,
        ),
    }
    adjusted = holm_bonferroni_adjust(
        {key: Fraction(item["raw_mcnemar_p"]) for key, item in comparisons.items()}
    )
    for key, item in comparisons.items():
        item["holm_adjusted_p"] = str(adjusted[key])
    token_trajectory = {}
    for arm in ARM_IDS:
        solved = [task for task, passed in outcomes[arm].items() if passed]
        spent = sum(_tokens_for(arm, task) for task in (*LEARNING_TASKS, *HOLDOUT_TASKS))
        token_trajectory[arm] = {
            "tokens": spent,
            "solved": len(solved),
            "tokens_per_solved_task": str(Fraction(spent, len(solved))) if solved else None,
        }
    replies = {
        arm: {task: f"{arm}:{task}:{'pass' if passed else 'fail'}" for task, passed in outcomes[arm].items()}
        for arm in ARM_IDS
    }
    reply_seal = sha256_hex(_canon(replies))
    false_refusals = clean_panel_false_refusals()
    report = {
        "authority_effect": AUTHORITY_NONE,
        "arms": list(ARM_IDS),
        "learning_tasks": list(LEARNING_TASKS),
        "holdout_tasks": list(HOLDOUT_TASKS),
        "comparisons": comparisons,
        "token_trajectory": token_trajectory,
        "false_refusal_rate": str(Fraction(false_refusals, len(CLEAN_PANEL))),
        "reply_sha256": reply_seal,
        "provider_calls": 0,
        "null_findings": [
            "acc(arm6, H) - acc(arm3, H) is 0 on the sealed holdout rows",
        ],
        "claim_hygiene": {
            "supports": (
                "Exact McNemar and Holm values for these six sealed offline arms, "
                "including a zero holdout delta between arm6 and arm3."
            ),
            "does_not_support": (
                "A positive held-out transfer claim, a live-model result, "
                "or a statement about tasks outside this sealed curriculum."
            ),
            "narrowest_claim": (
                "On this sealed offline curriculum, arm6 and arm3 have the same holdout accuracy, "
                "and arm6 records fewer tokens than arm2 and arm4."
            ),
            "negative_controls": (
                "arm1_direct, arm2_best_of_k, and arm4_naive_memory stay in the receipt; "
                "the zero arm6-versus-arm3 delta is retained."
            ),
        },
    }
    report["digest"] = _digest({key: value for key, value in report.items() if key != "digest"})
    return report


def unmatched_mathematical_claims(matches_path: Path | None = None) -> tuple[str, ...]:
    """Atlas ids in ATL-P010..ATL-P021 whose stored verdict is not matched."""
    path = matches_path or _ATLAS_MATCHES
    payload = json.loads(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for row in payload["results"]:
        atlas_id = str(row["atlas_id"])
        if not atlas_id.startswith("ATL-P"):
            continue
        number = atlas_id.split("-")[1]
        if not number.startswith("P"):
            continue
        paper = int(number[1:])
        if 10 <= paper <= 21 and row["verdict"] != "matched":
            found.append(atlas_id)
    return tuple(found)


def run_release_library_batch() -> dict[str, Any]:
    """One digest-stable library entry: quotient, USD 0 rejects, and a holdout refusal."""
    batch = run_tier1_release_batch(target_count=1000)
    opus = RoleAdapterV1(ROLE_OPUS, {"ping": "replay-opus"})
    fable = RoleAdapterV1(ROLE_FABLE, {"ping": "replay-fable"})
    opus_reply = opus.complete("ping")
    fable_reply = fable.complete("ping")
    body = {
        "authority_effect": AUTHORITY_NONE,
        "quotient_classes": batch["unique_quotient_classes"],
        "total_generated": batch["total_generated"],
        "usd_reject_total": batch["usd_reject_total"],
        "reject_reasons": batch["reject_reasons"],
        "holdout_refusal": batch["holdout_refusal"],
        "provider_calls": opus_reply["provider_calls"] + fable_reply["provider_calls"],
        "tier1_digest": batch["digest"],
    }
    body["digest"] = _digest(body)
    return body


def replay_guest_showcase() -> dict[str, Any]:
    """Zero-spend guest replay. This path does not construct a provider client."""
    campaign = run_six_arm_offline_campaign()
    payload = {
        "authority_effect": AUTHORITY_NONE,
        "mode": "zero-spend-replay",
        "provider_calls": 0,
        "campaign_digest": campaign["digest"],
        "false_refusal_rate": campaign["false_refusal_rate"],
        "null_findings": campaign["null_findings"],
    }
    payload["digest"] = _digest(payload)
    return payload


def live_campaign_status() -> str:
    """Report whether a live campaign under the USD 5 ceiling can start."""
    if os.environ.get("PFP_LIVE_PROVIDER") != "1" or not os.environ.get("PFP_PROVIDER_API_KEY"):
        return "BLOCKED: provider credentials are absent"
    manifest = os.environ.get("PFP_WHOLE_RUN_BUDGET_DIGEST", "")
    cap = os.environ.get("PFP_WHOLE_RUN_BUDGET_MICROUSD", "")
    if len(manifest) != 64 or not cap.isdigit():
        return "BLOCKED: WholeRunBudget manifest digest is absent"
    if int(cap) > CAMPAIGN_CAP_MICROUSD:
        return "BLOCKED: campaign cap exceeds USD 5.00"
    return "READY"


def main() -> None:
    library = run_release_library_batch()
    campaign = run_six_arm_offline_campaign()
    print(_canon({"library_digest": library["digest"], "campaign_digest": campaign["digest"]}))


if __name__ == "__main__":
    main()
