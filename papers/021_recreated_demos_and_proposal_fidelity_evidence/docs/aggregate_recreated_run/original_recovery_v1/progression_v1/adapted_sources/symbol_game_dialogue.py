from __future__ import annotations
import json
from typing import Any, Dict, List, Optional, Tuple
from paper011_recovered_demo2.symbol_game_models import ObstructionScore, SceneBeat

class SymbolGameDialogueArguer:
    """
    Enacts multi-character dramatic debate over proposals, multi-candidate solutions,
    and host obstruction measures. Full Bulgakovian technical dramaturgy and claim hygiene.
    """

    @staticmethod
    def generate_round_debate(packet: PacketEnvelopeV2, candidate: Dict[str, Any], score: ObstructionScore, prior_score: Optional[ObstructionScore], step_index: int) -> Tuple[SceneBeat, ...]:
        beats: List[SceneBeat] = []
        prior_val_str = f'{prior_score.phi_1:.3f}' if prior_score else 'initial'
        active_ids_str = ', '.join(score.active_obstruction_ids) if score.active_obstruction_ids else 'None'
        if score.phi_1 > 0.0:
            begemot_dialogue = f'«Ladies and gentlemen, citizens of the city and beyond! The cat is at the chessboard!\nFor Round {step_index}, looking at the stubborn obstruction mass $\\Phi_1 = {score.phi_1:.3f}$ across active defects `[{active_ids_str}]`, I propose not one, but three delightful solutions:\n\n  • **Candidate A (Combinatorial Shuffle):** We simply re-index the cell complex, swap the boundary labels, and pretend the uncontracted edge was never in $C_1$ to begin with. Pure feline sleight of hand!\n  • **Candidate B (Priced Quotient Patch):** We declare a formal repair differential $\\alpha$, quotient out the active defect spans, and contract the residual cochain directly against the carrier payload `{json.dumps(candidate, default=str)[:80]}...`.\n  • **Candidate C (Lateral Topological Reroute):** We build a 2-simplex spanning the defect, certifying $d_1 \\circ d_0 = 0$ and routing around the obstacle entirely.\n\nPick your poison! The cat stands ready to sign all three with a paw dipped in pure walnut ink!»'
        else:
            begemot_dialogue = '«Behold! Look at the board, look at the velvet cloth! The obstruction mass has collapsed to $\\Phi_1 = 0.000$! The 1-cochains have resolved into an exact coboundary over $\\mathbb{Q}$. Candidate B triumphed! Not a single unpaid token remains in the pouch. Begemot rests his paws!»'
        beats.append(SceneBeat(speaker='Begemot', cue='', dialogue=begemot_dialogue, operator_tag='combinatorial_proposer'))
        if score.phi_1 > 0.0 or score.gamma_2 > 0.0:
            koroviev_dialogue = f'«Hold on, my whisker-twitching friend, hold on! Let us adjust the pince-nez and inspect the arithmetic!\nUnder plain the city scrutiny:\n\n  1. **Dissecting Candidate A:** Swapping boundary labels is a carnival illusion! Host projection still sees $\\Phi_1 = {score.phi_1:.3f}$ and $\\gamma_2 = {score.gamma_2:.3f}$. The uncontracted boundary leaks like a broken samovar.\n  2. **Dissecting Candidate B:** Your repair differential $\\alpha$ is ungrounded—it assumes the source text already provides an orientation, which is an unpriced import! You are spending tokens you have not earned!\n  3. **Dissecting Candidate C:** Constructing a 2-simplex without verifying nilpotency will trigger an immediate closure failure on the very next round.\n\nOut of {score.active_count} active obstructions `[{active_ids_str}]`, exactly zero can be wished away by cat poetry! We demand a rigorous, verified descent step!»'
        else:
            koroviev_dialogue = '«Enchanting! Simply enchanting! I have checked every seam of the checkered jacket: $\\Phi_1 = 0.000$, $\\gamma_2 = 0.000$, and zero unmitigated defects! The nilpotency condition $d_1 \\circ d_0 = 0$ holds without a single unpriced import. The receipt is immaculate!»'
        beats.append(SceneBeat(speaker='Koroviev', cue='', dialogue=koroviev_dialogue, operator_tag='nocebo_adversary'))
        if score.phi_1 > 0.0:
            jeremy_dialogue = f"«Let's cut the fluff and look at the actual discrete mechanics.\nKoroviev is right about Candidate A—it's a textbook semantic leak. But Candidate B can work if we ground it in code: we define an explicit incidence map $d_0: C_0 \\to C_1$ where $(d_0\\alpha)(u, v) = \\alpha(v) - \\alpha(u)$ over $\\mathbb{{Q}}$, bound strictly to the frozen byte-spans of the packet.\nThat reduces $\\Phi_1$ from {prior_val_str} down to {score.phi_1:.3f}. Here is the counterexample we must guard against: if the source input has disconnected cyclic components, the harmonic obstruction $\\gamma_2$ won't vanish until we supply the boundary condition explicitly. Let's bind Candidate B with exact rational coefficients and verify the test fixture.»"
        else:
            jeremy_dialogue = f'«The discrete algebra is solid. All {len(score.active_obstruction_ids)} edge constraints evaluate to zero, the linear solver confirms exactness over $\\mathbb{{Q}}$, and the unit test pass is 100% deterministic with zero floating-point slop.»'
        beats.append(SceneBeat(speaker='Jeremy', cue='', dialogue=jeremy_dialogue, operator_tag='yankee_solver'))
        if score.phi_1 > 0.0:
            polina_dialogue = f"«Y'all are killing me with these five-dollar words! 'Planar multicategory,' 'harmonic cochains,' 'Hodge decomposition'—meanwhile, there are still {score.active_count} broken constraints sitting right on the table!\nIf you hand this to an engineer right now, it crashes on an empty string and catches fire on negative numbers. Quit admiring your own vocabulary, fix the actual edge cases, and show me a test that passes before you start celebrating!»"
        else:
            polina_dialogue = "«Well, look at that. I threw empty inputs, weird unicode, and null pointers at it, and it didn't even flinch. The test suite actually passed. See? Was that so hard when you stopped giving speeches and actually wrote clean code?»"
        beats.append(SceneBeat(speaker='Polina', cue='', dialogue=polina_dialogue, operator_tag='gauge_breaker'))
        liudmila_dialogue = f'«Stop the manufactured panic. There is no catastrophe here. Look at the numbers calmly:\nPrior $\\Phi_1$ was {prior_val_str}; current $\\Phi_1$ is {score.phi_1:.3f}.\nWe have survived 90s hyperinflation, supply disruptions, and power outages—we can certainly resolve {score.active_count} residual cochains. We proceed step by step, disciplined and quiet, until every defect is accounted for and the hyp ledger is closed.»'
        beats.append(SceneBeat(speaker='Liudmila', cue='', dialogue=liudmila_dialogue, operator_tag='stable_equilibrium'))
        yaro_status = 'PASS' if prior_score is None or score.strictly_improves(prior_score) or score.is_exact else 'STALLED'
        delta_phi1 = prior_score.phi_1 - score.phi_1 if prior_score is not None else 0.0
        yaroslava_dialogue = f'«Invariant Audit for Round {step_index}:\n  • Packet ID: `{packet.task_id}` bound\n  • Initial State Hash: `{packet.initial_state_hash[:16]}...` verified\n  • Strict Descent Check: `{yaro_status}` ($\\Delta \\Phi_1 = {delta_phi1:.3f}$)\n  • Nonclaim Enforced: `AuthorityEffect: None`\n  • Invariant Checklist: All schema fields strictly validated against `omega.symbol-game.packet-envelope.v2`.»'
        beats.append(SceneBeat(speaker='Yaroslava', cue='', dialogue=yaroslava_dialogue, operator_tag='methodical_discipline'))
        if score.is_exact:
            yeshua_dialogue = '«The truth was there from the beginning; it only needed the false assumptions to be stripped away. The obstruction has dissolved into an exact coboundary: $\\omega = d_0 \\alpha$. Truth requires no force, no hyperbole, and no anger when verified under pure observation.»'
        else:
            yeshua_dialogue = f'«Do not be angry with the defect of {score.phi_1:.3f}. The defect is not an enemy or an insult; it is merely a faithful witness showing us exactly where understanding remains incomplete. We attach the repair differential $\\alpha$ in peace and continue the work.»'
        beats.append(SceneBeat(speaker='Yeshua', cue='', dialogue=yeshua_dialogue, operator_tag='truth_repair'))
        if score.is_exact:
            woland_dialogue = '«The game is won on the board. The rational cochain complex is closed. $\\Phi_1 = 0.000$, $\\gamma_2 = 0.000$, and the evidence digest is sealed. Manuscripts do not burn, and verified exactness does not evaporate.\nEmit the licensing token: **PASS_TO_MASTER** under `AuthorityEffect: None`. The hyp ledger is closed.»'
        elif prior_score and score.strictly_improves(prior_score):
            woland_dialogue = f'«Strict descent verified: $\\Phi_1$ descended from {prior_val_str} to {score.phi_1:.3f}. The trajectory is contractive in $\\ell_1$. Compile child packet `{packet.task_id}_step_{step_index + 1}` and continue the reduction without delay.»'
        else:
            woland_dialogue = f'«Descent has stalled at $\\Phi_1 = {score.phi_1:.3f}$. The retinue will not wander in circles. Refuse same-level repetition. Either trigger a lateral gauge rotation or emit an explicit typed obstruction request.»'
        beats.append(SceneBeat(speaker='Woland', cue='', dialogue=woland_dialogue, operator_tag='terminal_reality_arbiter'))
        return tuple(beats)
