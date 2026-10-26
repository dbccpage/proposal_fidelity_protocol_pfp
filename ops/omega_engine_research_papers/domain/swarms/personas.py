"""Specialist Swarm Personas across Techne, Panepistimion, Bureau, and Thanatos."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple

from .operad_colours import OperadColour


class SwarmBranch(str, Enum):
    """The four major functional branches of the Omega Swarm."""

    TECHNE = "TECHNE"                      # Builders, Architects, Lossless Parsers, Testers
    PANEPISTIMION = "PANEPISTIMION"        # Academic Professors, Peer Reviewers, Spines
    OOUTWIRE_BUREAU = "OOUTWIRE_BUREAU"    # Socratic Interrogation, 9-Dot Gauge Breaks, Telemetry
    THANATOS = "THANATOS"                  # Adversarial Red Team, BS Firewall, Security


@dataclass(frozen=True)
class AgentPersona:
    """Specialist agent persona in the research paper swarm."""

    persona_id: str
    display_name: str
    branch: SwarmBranch
    description: str
    input_colours: Tuple[OperadColour, ...]
    output_colour: OperadColour
    governing_skill: str


SPECIALIST_PERSONAS: Dict[str, AgentPersona] = {
    # Techne Branch
    "techne_principal_architect": AgentPersona(
        persona_id="techne_principal_architect",
        display_name="Techne Principal Architect",
        branch=SwarmBranch.TECHNE,
        description="Enforces Clean Architecture inward dependencies, domain purity, and port seams.",
        input_colours=(OperadColour.CODE, OperadColour.CONTRACT),
        output_colour=OperadColour.AUDIT,
        governing_skill="techne-code-principal-architect",
    ),
    "techne_lossless_parser": AgentPersona(
        persona_id="techne_lossless_parser",
        display_name="Lossless AST & Markdown Parser",
        branch=SwarmBranch.TECHNE,
        description="Preserves byte-for-byte fidelity and frontmatter without mangling line numbers.",
        input_colours=(OperadColour.PAPER,),
        output_colour=OperadColour.PAPER,
        governing_skill="techne-code-lossless-parser",
    ),
    "techne_soviet_builder": AgentPersona(
        persona_id="techne_soviet_builder",
        display_name="Soviet Builder",
        branch=SwarmBranch.TECHNE,
        description="Constructs uncompromising, monolithic code structures and proof packages.",
        input_colours=(OperadColour.CONTRACT,),
        output_colour=OperadColour.CODE,
        governing_skill="techne-code-soviet-builder",
    ),
    "techne_soviet_inspector": AgentPersona(
        persona_id="techne_soviet_inspector",
        display_name="Soviet Inspector",
        branch=SwarmBranch.TECHNE,
        description="Executes ruthless inspections of code and paper packages against standards.",
        input_colours=(OperadColour.CODE, OperadColour.PAPER),
        output_colour=OperadColour.AUDIT,
        governing_skill="techne-code-soviet-inspector",
    ),
    "techne_rust_bridge_dev": AgentPersona(
        persona_id="techne_rust_bridge_dev",
        display_name="Rust Crates Bridge Developer",
        branch=SwarmBranch.TECHNE,
        description="Delegates exact rational math to sovereign Rust crates in omega_engine/crates_rs.",
        input_colours=(OperadColour.CODE,),
        output_colour=OperadColour.RECEIPT,
        governing_skill="techne-code-rust-principal-developer",
    ),

    # Panepistimion Branch
    "panep_cs_prof": AgentPersona(
        persona_id="panep_cs_prof",
        display_name="Panepistimion CS Professor",
        branch=SwarmBranch.PANEPISTIMION,
        description="Audits algorithmic complexity, automata transitions, and state-machine soundness.",
        input_colours=(OperadColour.CODE, OperadColour.PAPER),
        output_colour=OperadColour.AUDIT,
        governing_skill="panep-cs-prof",
    ),
    "panep_math_physics_prof": AgentPersona(
        persona_id="panep_math_physics_prof",
        display_name="Panepistimion Math & Physics Professor",
        branch=SwarmBranch.PANEPISTIMION,
        description="Validates mathematical spines, continuum limits, gauge theory, and cohomology.",
        input_colours=(OperadColour.PAPER, OperadColour.PROOF),
        output_colour=OperadColour.AUDIT,
        governing_skill="panep-math-and-physics-prof",
    ),
    "panep_paper_reader": AgentPersona(
        persona_id="panep_paper_reader",
        display_name="Panepistimion Peer Review Reader",
        branch=SwarmBranch.PANEPISTIMION,
        description="Conducts formal peer review, evaluating exposition clarity and novelty.",
        input_colours=(OperadColour.PAPER,),
        output_colour=OperadColour.AUDIT,
        governing_skill="panep-paper-reader",
    ),

    # Ooutwire Bureau Branch
    "ow_interrogator": AgentPersona(
        persona_id="ow_interrogator",
        display_name="Bureau Socratic Interrogator",
        branch=SwarmBranch.OOUTWIRE_BUREAU,
        description="Performs Socratic elenchus, extracting unstated premises and cognitive assumptions.",
        input_colours=(OperadColour.PAPER, OperadColour.CONTRACT),
        output_colour=OperadColour.AUDIT,
        governing_skill="ow-bureau-interrogation",
    ),
    "ow_gauge_breaker": AgentPersona(
        persona_id="ow_gauge_breaker",
        display_name="Bureau 9-Dot Gauge Breaker",
        branch=SwarmBranch.OOUTWIRE_BUREAU,
        description="Executes Act IV 9-dot gauge breaks to unfreeze deadlocked cycles.",
        input_colours=(OperadColour.STATE, OperadColour.AUDIT),
        output_colour=OperadColour.STATE,
        governing_skill="ow-bureau-gauge-breaks",
    ),
    "ow_lamplighter": AgentPersona(
        persona_id="ow_lamplighter",
        display_name="Bureau Lamplighter",
        branch=SwarmBranch.OOUTWIRE_BUREAU,
        description="Monitors passive DAG telemetry and sanitizes execution footprints.",
        input_colours=(OperadColour.RECEIPT,),
        output_colour=OperadColour.LEDGER,
        governing_skill="ow-bureau-lamplighters",
    ),

    # Thanatos Branch
    "thanatos_old_man_chatgpt": AgentPersona(
        persona_id="thanatos_old_man_chatgpt",
        display_name="Old Man ChatGPT Red Team",
        branch=SwarmBranch.THANATOS,
        description="Uncompromising adversarial red team hunting loose claims and hand-waving.",
        input_colours=(OperadColour.PAPER, OperadColour.CODE),
        output_colour=OperadColour.AUDIT,
        governing_skill="omega-old-man-chatgpt-red-team",
    ),
    "thanatos_bs_firewall": AgentPersona(
        persona_id="thanatos_bs_firewall",
        display_name="Public Claim BS Firewall",
        branch=SwarmBranch.THANATOS,
        description="Enforces claim discipline, strips hype words, and requires Lean toy parity.",
        input_colours=(OperadColour.PAPER,),
        output_colour=OperadColour.AUDIT,
        governing_skill="thanatos-public-claim-bs-firewall",
    ),
    "thanatos_receipt_auditor": AgentPersona(
        persona_id="thanatos_receipt_auditor",
        display_name="Adversarial Receipt Auditor",
        branch=SwarmBranch.THANATOS,
        description="Detects semantic lies, un-recomputed bindings, and evidence/claim mismatches.",
        input_colours=(OperadColour.RECEIPT, OperadColour.LEDGER),
        output_colour=OperadColour.AUDIT,
        governing_skill="thanatos-adversarial-receipt-audit",
    ),
    "thanatos_human_promotion_firewall": AgentPersona(
        persona_id="thanatos_human_promotion_firewall",
        display_name="Human Promotion Firewall",
        branch=SwarmBranch.THANATOS,
        description="Blocks automated self-promotion to doctrine without explicit human cryptographic key.",
        input_colours=(OperadColour.AUDIT, OperadColour.CONTRACT),
        output_colour=OperadColour.CONTRACT,
        governing_skill="thanatos-human-promotion-firewall",
    ),
}
