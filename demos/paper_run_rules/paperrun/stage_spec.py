"""Pure domain stage specifications and pipeline definitions.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ExecutionMode = Literal["receipts_only", "panel", "human_skill"]


@dataclass(frozen=True)
class StageSpec:
    stage_id: str
    order: int
    skill_id: str
    title: str
    description: str
    execution: ExecutionMode = "receipts_only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "order": self.order,
            "skill_id": self.skill_id,
            "title": self.title,
            "description": self.description,
            "execution": self.execution,
            "authority_effect": "None",
        }


# Research core graph (charter-aligned). Optional --deep / --check-readiness stages
# live only in the interactive skill, not as default host catalog rows.
RIP_PAPERS_STAGE_PIPELINE: tuple[StageSpec, ...] = (
    StageSpec(
        stage_id="stage_0_redteam",
        order=0,
        skill_id="paper-redteam-dialogue",
        title="Freeze carrier + residual inventory",
        description="Frozen-carrier dialogue; inventory open residuals before edits.",
    ),
    StageSpec(
        stage_id="stage_1_improver",
        order=1,
        skill_id="paper-improver",
        title="Improver pass",
        description="Rubric + claim ledger repairs (proposal only until human ACCEPT).",
    ),
    StageSpec(
        stage_id="stage_2_adversary",
        order=2,
        skill_id="paper-adversary",
        title="Adversary pass",
        description="Read-only recompute gates on producer diff; refuse illegal lift.",
    ),
    StageSpec(
        stage_id="stage_3_proof_signoff",
        order=3,
        skill_id="paper-proof-signoff",
        title="Proof sign-off pass",
        description="Math/physics/formal gates; Lean snippet check; honest claim ceiling.",
    ),
    StageSpec(
        stage_id="stage_4_release_preflight",
        order=4,
        skill_id="paper-release",
        title="Release preflight pass",
        description="PDF build dry run, hash inventory, publication gate checks.",
    ),
    StageSpec(
        stage_id="stage_5_build_public_object",
        order=5,
        skill_id="paper-build",
        title="Build public object",
        description="Deterministic PDF + SHA256SUMS + lean public zip artifact build.",
    ),
    StageSpec(
        stage_id="stage_final_red_team",
        order=6,
        skill_id="core-red-team-audit",
        title="Red Team audit",
        description="Post-build adversarial audit; blocks promotion on hallucination or hype.",
    ),
)

# SCALE-006: ODASDS / rip-code host twin (software specialization). No paper stage_5.
CODE_STAGE_PIPELINE: tuple[StageSpec, ...] = (
    StageSpec(
        stage_id="code_stage_0_lint",
        order=0,
        skill_id="techne-docs-lint-hunter-killer",
        title="Code lint preflight",
        description="Format/docs/lint audit before code propose.",
    ),
    StageSpec(
        stage_id="code_stage_1_rust_propose",
        order=1,
        skill_id="techne-code-rust-principal-developer",
        title="Rust PROD propose",
        description="Rust principal propose (via /rip-rust). Proposal only until human ACCEPT.",
        execution="panel",
    ),
    StageSpec(
        stage_id="code_stage_2_python_propose",
        order=2,
        skill_id="techne-code-python-principal-developer",
        title="Python PROTO propose",
        description="Python principal propose (via /rip-python). Proposal only until human ACCEPT.",
        execution="panel",
    ),
    StageSpec(
        stage_id="code_stage_3_strict_inspect",
        order=3,
        skill_id="techne-code-strict-inspector",
        title="Strict test inspect",
        description="Hardline test quality veto (host judge).",
    ),
    StageSpec(
        stage_id="code_stage_4_parity_manager",
        order=4,
        skill_id="techne-software-dev-manager",
        title="Dual-home parity audit",
        description="Rust/Python parity + CA audit (host judge).",
    ),
    StageSpec(
        stage_id="code_stage_5_contracts_adversary",
        order=5,
        skill_id="techne-code-contracts-adversary",
        title="Contracts adversary",
        description="Contract layer firewall (evaluator).",
    ),
    StageSpec(
        stage_id="code_stage_final_red_team",
        order=6,
        skill_id="core-red-team-audit",
        title="Red Team residual audit",
        description="Mandatory Red Team residual audit. Not promotion.",
    ),
)

# Panel-default CODE stage for SCALE-006 S2 (rust propose)
CODE_PANEL_DEFAULT_STAGE_ID = "code_stage_1_rust_propose"


def code_catalog() -> list[dict[str, Any]]:
    """SCALE-006 CODE_STAGE_PIPELINE rows (ODASDS twin)."""
    return [s.to_dict() for s in CODE_STAGE_PIPELINE]
