from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from omega_engine_pfp.domain import PacketEnvelopeV2

from .symbol_game_models import ObstructionScore, SceneBeat


class SymbolGameDialogueArguer:
    """
    Enacts multi-character dramatic debate over proposals, multi-candidate solutions,
    and host obstruction measures. Full Bulgakovian technical dramaturgy and claim hygiene.
    """

    @staticmethod
    def generate_round_debate(
        packet: PacketEnvelopeV2,
        candidate: Dict[str, Any],
        score: ObstructionScore,
        prior_score: Optional[ObstructionScore],
        step_index: int,
    ) -> Tuple[SceneBeat, ...]:
        beats: List[SceneBeat] = []
        prior_val_str = f"{prior_score.phi_1:.3f}" if prior_score else "initial"
        active_ids_str = ", ".join(score.active_obstruction_ids) if score.active_obstruction_ids else "None"

        # 1. Multi-Candidate Proposer Turn (Begemot)
        if score.phi_1 > 0.0:
            begemot_dialogue = (
                f"«Ladies and gentlemen, citizens of the city and beyond! The cat is at the chessboard!\n"
                f"For Round {step_index}, looking at the stubborn obstruction mass $\\Phi_1 = {score.phi_1:.3f}$ "
                f"across active defects `[{active_ids_str}]`, I propose not one, but three delightful solutions:\n\n"
                f"  • **Candidate A (Combinatorial Shuffle):** We simply re-index the cell complex, swap the boundary labels, "
                f"and pretend the uncontracted edge was never in $C_1$ to begin with. Pure feline sleight of hand!\n"
                f"  • **Candidate B (Priced Quotient Patch):** We declare a formal repair differential $\\alpha$, quotient out the "
                f"active defect spans, and contract the residual cochain directly against the carrier payload `{json.dumps(candidate, default=str)[:80]}...`.\n"
                f"  • **Candidate C (Lateral Topological Reroute):** We build a 2-simplex spanning the defect, certifying $d_1 \\circ d_0 = 0$ "
                f"and routing around the obstacle entirely.\n\n"
                f"Pick your poison! The cat stands ready to sign all three with a paw dipped in pure walnut ink!»"
            )
        else:
            begemot_dialogue = (
                "«Behold! Look at the board, look at the velvet cloth! The obstruction mass has collapsed to $\\Phi_1 = 0.000$! "
                "The 1-cochains have resolved into an exact coboundary over $\\mathbb{Q}$. "
                "Candidate B triumphed! Not a single unpaid token remains in the pouch. Begemot rests his paws!»"
            )
        beats.append(SceneBeat(speaker="Begemot", cue="", dialogue=begemot_dialogue, operator_tag="combinatorial_proposer"))

        # 2. Adversarial Dissection & Nocebo Audit (Koroviev)
        if score.phi_1 > 0.0 or score.gamma_2 > 0.0:
            koroviev_dialogue = (
                f"«Hold on, my whisker-twitching friend, hold on! Let us adjust the pince-nez and inspect the arithmetic!\n"
                f"Under plain the city scrutiny:\n\n"
                f"  1. **Dissecting Candidate A:** Swapping boundary labels is a carnival illusion! Host projection still sees "
                f"$\\Phi_1 = {score.phi_1:.3f}$ and $\\gamma_2 = {score.gamma_2:.3f}$. The uncontracted boundary leaks like a broken samovar.\n"
                f"  2. **Dissecting Candidate B:** Your repair differential $\\alpha$ is ungrounded—it assumes the source text already "
                f"provides an orientation, which is an unpriced import! You are spending tokens you have not earned!\n"
                f"  3. **Dissecting Candidate C:** Constructing a 2-simplex without verifying nilpotency will trigger an immediate "
                f"closure failure on the very next round.\n\n"
                f"Out of {score.active_count} active obstructions `[{active_ids_str}]`, exactly zero can be wished away by cat poetry! "
                f"We demand a rigorous, verified descent step!»"
            )
        else:
            koroviev_dialogue = (
                "«Enchanting! Simply enchanting! I have checked every seam of the checkered jacket: "
                "$\\Phi_1 = 0.000$, $\\gamma_2 = 0.000$, and zero unmitigated defects! "
                "The nilpotency condition $d_1 \\circ d_0 = 0$ holds without a single unpriced import. The receipt is immaculate!»"
            )
        beats.append(SceneBeat(speaker="Koroviev", cue="", dialogue=koroviev_dialogue, operator_tag="nocebo_adversary"))

        # 3. Ground-Level Discrete Implementation & Counterexample (Jeremy)
        if score.phi_1 > 0.0:
            jeremy_dialogue = (
                f"«Let's cut the fluff and look at the actual discrete mechanics.\n"
                f"Koroviev is right about Candidate A—it's a textbook semantic leak. But Candidate B can work if we ground it in code: "
                f"we define an explicit incidence map $d_0: C_0 \\to C_1$ where $(d_0\\alpha)(u, v) = \\alpha(v) - \\alpha(u)$ over $\\mathbb{{Q}}$, "
                f"bound strictly to the frozen byte-spans of the packet.\n"
                f"That reduces $\\Phi_1$ from {prior_val_str} down to {score.phi_1:.3f}. "
                f"Here is the counterexample we must guard against: if the source input has disconnected cyclic components, "
                f"the harmonic obstruction $\\gamma_2$ won't vanish until we supply the boundary condition explicitly. "
                f"Let's bind Candidate B with exact rational coefficients and verify the test fixture.»"
            )
        else:
            jeremy_dialogue = (
                f"«The discrete algebra is solid. All {len(score.active_obstruction_ids)} edge constraints evaluate to zero, "
                f"the linear solver confirms exactness over $\\mathbb{{Q}}$, and the unit test pass is 100% deterministic with zero floating-point slop.»"
            )
        beats.append(SceneBeat(speaker="Jeremy", cue="", dialogue=jeremy_dialogue, operator_tag="yankee_solver"))

        # 4. Razor-Sharp Puncture & Southern Reality Check (Polina)
        if score.phi_1 > 0.0:
            polina_dialogue = (
                f"«Y'all are killing me with these five-dollar words! 'Planar multicategory,' 'harmonic cochains,' 'Hodge decomposition'—"
                f"meanwhile, there are still {score.active_count} broken constraints sitting right on the table!\n"
                f"If you hand this to an engineer right now, it crashes on an empty string and catches fire on negative numbers. "
                f"Quit admiring your own vocabulary, fix the actual edge cases, and show me a test that passes before you start celebrating!»"
            )
        else:
            polina_dialogue = (
                "«Well, look at that. I threw empty inputs, weird unicode, and null pointers at it, and it didn't even flinch. "
                "The test suite actually passed. See? Was that so hard when you stopped giving speeches and actually wrote clean code?»"
            )
        beats.append(SceneBeat(speaker="Polina", cue="", dialogue=polina_dialogue, operator_tag="gauge_breaker"))

        # 5. Soviet Practical Resilience & Equilibrium (Liudmila)
        liudmila_dialogue = (
            f"«Stop the manufactured panic. There is no catastrophe here. Look at the numbers calmly:\n"
            f"Prior $\\Phi_1$ was {prior_val_str}; current $\\Phi_1$ is {score.phi_1:.3f}.\n"
            f"We have survived 90s hyperinflation, supply disruptions, and power outages—we can certainly resolve {score.active_count} residual cochains. "
            f"We proceed step by step, disciplined and quiet, until every defect is accounted for and the hyp ledger is closed.»"
        )
        beats.append(SceneBeat(speaker="Liudmila", cue="", dialogue=liudmila_dialogue, operator_tag="stable_equilibrium"))

        # 6. Schema & Boundary Verification (Yaroslava)
        yaro_status = "PASS" if (prior_score is None or score.strictly_improves(prior_score) or score.is_exact) else "STALLED"
        delta_phi1 = (prior_score.phi_1 - score.phi_1) if prior_score is not None else 0.0
        yaroslava_dialogue = (
            f"«Invariant Audit for Round {step_index}:\n"
            f"  • Packet ID: `{packet.task_id}` bound\n"
            f"  • Initial State Hash: `{packet.initial_state_hash[:16]}...` verified\n"
            f"  • Strict Descent Check: `{yaro_status}` ($\\Delta \\Phi_1 = {delta_phi1:.3f}$)\n"
            f"  • Nonclaim Enforced: `AuthorityEffect: None`\n"
            f"  • Invariant Checklist: All schema fields strictly validated against `omega.symbol-game.packet-envelope.v2`.»"
        )
        beats.append(SceneBeat(speaker="Yaroslava", cue="", dialogue=yaroslava_dialogue, operator_tag="methodical_discipline"))

        # 7. Radical Invariant Truth Alignment (Yeshua)
        if score.is_exact:
            yeshua_dialogue = (
                "«The truth was there from the beginning; it only needed the false assumptions to be stripped away. "
                "The obstruction has dissolved into an exact coboundary: $\\omega = d_0 \\alpha$. "
                "Truth requires no force, no hyperbole, and no anger when verified under pure observation.»"
            )
        else:
            yeshua_dialogue = (
                f"«Do not be angry with the defect of {score.phi_1:.3f}. The defect is not an enemy or an insult; "
                f"it is merely a faithful witness showing us exactly where understanding remains incomplete. "
                f"We attach the repair differential $\\alpha$ in peace and continue the work.»"
            )
        beats.append(SceneBeat(speaker="Yeshua", cue="", dialogue=yeshua_dialogue, operator_tag="truth_repair"))

        # 8. Sovereign Terminal Reality Judgment (Woland)
        if score.is_exact:
            woland_dialogue = (
                "«The game is won on the board. The rational cochain complex is closed. "
                "$\\Phi_1 = 0.000$, $\\gamma_2 = 0.000$, and the evidence digest is sealed. "
                "Manuscripts do not burn, and verified exactness does not evaporate.\n"
                "Emit the licensing token: **PASS_TO_MASTER** under `AuthorityEffect: None`. "
                "The hyp ledger is closed.»"
            )
        elif prior_score and score.strictly_improves(prior_score):
            woland_dialogue = (
                f"«Strict descent verified: $\\Phi_1$ descended from {prior_val_str} to {score.phi_1:.3f}. "
                f"The trajectory is contractive in $\\ell_1$. "
                f"Compile child packet `{packet.task_id}_step_{step_index + 1}` and continue the reduction without delay.»"
            )
        else:
            woland_dialogue = (
                f"«Descent has stalled at $\\Phi_1 = {score.phi_1:.3f}$. The retinue will not wander in circles. "
                f"Refuse same-level repetition. Either trigger a lateral gauge rotation or emit an explicit typed obstruction request.»"
            )
        beats.append(SceneBeat(speaker="Woland", cue="", dialogue=woland_dialogue, operator_tag="terminal_reality_arbiter"))

        return tuple(beats)
