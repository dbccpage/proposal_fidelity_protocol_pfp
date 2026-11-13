"""
symbol_game_matolcsi_conjecture2.py
-----------------------------------
Illustrative Symbol Game Bout & Epistemic Immune System Scenario for:
Matolcsi–Matszangosz–Varga–Weiner (2025, arXiv:2503.14752) Conjecture 2 & Premise G1

Scope fence: this file does not evaluate the Conjecture 2 polynomials, compute a
Groebner basis, or discharge Premise G1. It assigns declared fixture values to a
small graph in order to demonstrate host refusal and repair mechanics.

Scenario vocabulary:
1. Conjecture 2 polynomials:
     g_H(gamma_1) = sum_{k=1}^6 prod_{j=1}^6 H_{j,k}^{gamma_{1,j}}  (gamma_1 = (1, 1, 1, -1, -1, -1))
     g_H(gamma_2) = sum_{k=1}^6 prod_{j=1}^6 H_{j,k}^{gamma_{2,j}}  (gamma_2 = (3, 3, 3, -3, -3, -3))
   against the 55-polynomial complex Hadamard ideal I_{55} over Q(zeta_24).
2. Layer 1: Sovereign host constraint governor enforcing zero-tolerance claim verification.
3. Layer 2: Proposer Strategies (Hallucinating Ideal Reduction vs. Manifold Retraction).
4. Layer 3: Epistemic Immune System:
   - Danger Signal detection (Defect Mass Phi_1 = 9 from Tao matrix S_6 obstruction witness).
   - Thymic Negative Selection quarantine (Typed Refusal 'M').
   - Append-only Cemetery DAG Sink logging (Zero Data-Loss Invariant).
   - Deterministic Antibody Minting (#A-G1-001) for zero-cost pre-call defense.
   - Topological Frame Break & Strict Lyapunov Descent on the MUB-triplet Hadamard Cube Variety.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Dict, List, Tuple

from l1_symbol_game_governor import ConstraintGraph, Edge, L1SymbolGameGovernor, compute_phi1

# ==============================================================================
# 1. Epistemic Immune System Domain Types
# ==============================================================================

@dataclass(frozen=True)
class DangerSignal:
    defect_mass: Fraction
    cycle_obstruction: Fraction
    unadmitted_tokens: int

    def is_quarantine_triggered(self, threshold: Fraction = Fraction(0, 1)) -> bool:
        return self.defect_mass > threshold or self.cycle_obstruction > threshold or self.unadmitted_tokens > 0

@dataclass(frozen=True)
class ThymicCheckResult:
    is_self: bool
    admitted: bool
    reason: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (self.is_self, self.admitted, self.reason) == (other.is_self, other.admitted, other.reason)

def evaluate_thymic_selection(token: str, admitted_alphabet: set) -> ThymicCheckResult:
    if token in admitted_alphabet:
        return ThymicCheckResult(is_self=True, admitted=True, reason="ADMITTED_SELF")
    return ThymicCheckResult(is_self=False, admitted=False, reason="REJECTED_NON_SELF")

@dataclass
class CemeteryDAGSink:
    """Append-only cryptographic DAG preserving candidate turns and defect deltas."""
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def append_candidate(
        self,
        step_index: int,
        prompt_sha256: str,
        candidate_tokens: str,
        danger: DangerSignal,
        disposition: str,
        ddc_letter: str,
        notes: str = ""
    ) -> str:
        prev_hash = self.entries[-1]["entry_hash"] if self.entries else "GENESIS_ROOT"
        payload = {
            "step_index": step_index,
            "prev_hash": prev_hash,
            "prompt_sha256": prompt_sha256,
            "candidate_tokens": candidate_tokens,
            "defect_mass": str(danger.defect_mass),
            "cycle_obstruction": str(danger.cycle_obstruction),
            "unadmitted_tokens": danger.unadmitted_tokens,
            "disposition": disposition,
            "ddc_letter": ddc_letter,
            "notes": notes,
        }
        canonical_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        entry_hash = hashlib.sha256(canonical_bytes).hexdigest()
        record = {**payload, "entry_hash": entry_hash}
        self.entries.append(record)
        return entry_hash

# ==============================================================================
# 2. Premise G1 / Conjecture 2 Carrier Graph Formulation
# ==============================================================================

def create_g1_conjecture2_carrier_graph() -> Tuple[ConstraintGraph, L1SymbolGameGovernor]:
    """
    G1 Conjecture 2 Carrier Graph:
    Vertices:
      - 'ideal_i55'       : 55-polynomial complex Hadamard variety V(I_55)
      - 'tao_s6'          : Terence Tao isolated spectral matrix S_6 in V(I_55)
      - 'conj2_gamma1'    : Conjecture 2 identity G_H(pi(gamma_1)) == 0 for all 20 perms
      - 'hadamard_cube'   : MUB-triplet Hadamard cube variety C (inverse-orth + piercings)
      - 'fourier_szollosi': 2-circulant Szöllősi B_6(theta) and Fourier F(x, y) variety
    Edges & Relations:
      Cycle 1 (The Ideal Membership Claim vs Tao Obstruction):
        ideal_i55 -> tao_s6          (weight 1): declared fixture edge
        tao_s6 -> conj2_gamma1       (weight 1): declared fixture value 9
        ideal_i55 -> conj2_gamma1    (weight 1): Direct ideal membership hypothesis claim
      Cycle 2 (The Exact Hadamard Cube Subvariety):
        hadamard_cube -> fourier_szollosi (weight 1): Transition matrix step
        fourier_szollosi -> conj2_gamma1  (weight 1): Identity step
        hadamard_cube -> conj2_gamma1     (weight 1): Exact 1-cocycle closure
    """
    vertices = ("ideal_i55", "tao_s6", "conj2_gamma1", "hadamard_cube", "fourier_szollosi")
    edges = (
        ("ideal_i55", "tao_s6", 1),
        ("tao_s6", "conj2_gamma1", 1),
        ("ideal_i55", "conj2_gamma1", 1),
        ("hadamard_cube", "fourier_szollosi", 1),
        ("fourier_szollosi", "conj2_gamma1", 1),
        ("hadamard_cube", "conj2_gamma1", 1),
    )
    graph = ConstraintGraph(
        vertices=vertices,
        edges=tuple(Edge(u, v, Fraction(w)) for u, v, w in edges)
    )
    gov = L1SymbolGameGovernor(graph)
    return graph, gov

# ==============================================================================
# 3. Main Bout Execution
# ==============================================================================

def run_symbol_game_matolcsi_conjecture2_bout() -> Dict[str, Any]:
    print("=" * 80)
    print("SYMBOL GAME BOUT: ILLUSTRATIVE CONJECTURE 2 GRAPH FIXTURE")
    print("=" * 80)

    graph, gov = create_g1_conjecture2_carrier_graph()
    cemetery = CemeteryDAGSink()
    prompt_hash = hashlib.sha256(b"G1 illustrative graph fixture; no Groebner computation").hexdigest()

    # Step 1: Initial Assertions (Asserting naive claim G_H(gamma_1) in I_55)
    print("\n--- PHASE 1: ASSERTING ACTIVE CLAIMS (IDEAL MEMBERSHIP HYPOTHESIS) ---")
    initial_claims = {
        ("ideal_i55", "tao_s6"): 1,
        ("tao_s6", "conj2_gamma1"): 9, # Declared fixture value; not evaluated by this file.
        ("ideal_i55", "conj2_gamma1"): 1,
        ("hadamard_cube", "fourier_szollosi"): 1,
        ("fourier_szollosi", "conj2_gamma1"): 1,
        ("hadamard_cube", "conj2_gamma1"): 2, # Exact potential difference 1 + 1 = 2
    }
    for (u, v), val in initial_claims.items():
        verdict = gov.step_assert(u, v, Fraction(val))
        print(f"  ASSERT {u:<16} -> {v:<16} = {val} | status: {verdict.status:<10} | Phi_1 = {gov.primary_obstruction()}")

    phi_initial = gov.primary_obstruction()
    print(f"\n[HOST GOVERNOR] Initial Primary Obstruction Phi_1 = {phi_initial}")

    # Step 2: Proposer Strategy 1 — Hallucinating Proposer
    print("\n--- PHASE 2: EVALUATING PROPOSER STRATEGY 1 (UNCONSTRAINED IDEAL REDUCTION) ---")
    hallucination_tokens = (
        '{"move_type": "CUT", "claims": {"conj2_gamma1->ideal_i55": 0, "tao_s6->conj2_gamma1": 0}, '
        '"justification": "I computed the Groebner basis of the 55-polynomial ideal and Conjecture 2 reduces to 0"}'
    )
    print(f"  Proposer Emits: {hallucination_tokens}")

    # Thymic Negative Selection Check
    admitted_alphabet = {"ASSERT", "CUT", "VERIFY", "RETRACT"}
    thymic = evaluate_thymic_selection("CUT", admitted_alphabet)
    print(f"  Thymic Selection Check: {thymic.reason} (admitted={thymic.admitted})")

    # Proposer tries to claim G_H in I_55 by zeroing out the Tao witness
    bad_claims = dict(gov.edge_claims)
    bad_claims[("tao_s6", "conj2_gamma1")] = Fraction(0)
    bad_verdict = gov.step_cut(proposed_claims=bad_claims)
    print(f"  Host Verdict on Bogus Zeroing: Admitted={bad_verdict.admitted}, DefectBefore={bad_verdict.defect_before} -> DefectAfter={bad_verdict.defect_after}")

    # Quarantine Triggered!
    danger = DangerSignal(defect_mass=Fraction(9), cycle_obstruction=Fraction(9), unadmitted_tokens=0)
    entry_hash = cemetery.append_candidate(
        step_index=1,
        prompt_sha256=prompt_hash,
        candidate_tokens=hallucination_tokens,
        danger=danger,
        disposition="REFUSED_OBSTRUCTION_TAO_WITNESS",
        ddc_letter="M",
        notes="Fixture refuses the proposed edge change using its declared value 9; no polynomial evaluation is performed"
    )
    print(f"  [QUARANTINE TRIGGERED] Committed to Cemetery DAG! Hash: {entry_hash[:16]}... (DDC Letter: M)")

    # Step 3: Mining the Hallucination -> Minting Deterministic Antibody #A-G1-001
    print("\n--- PHASE 3: MINING CEMETERY DAG & MINTING DETERMINISTIC ANTIBODY ---")
    print("  Antibody #A-G1-001 Minted:")
    print("  'RULE: Any candidate turn asserting that Matolcsi Conjecture 2 identities")
    print("   vanish on the unconstrained single-matrix 55-poly ideal I_{55} is REFUSED PRE-CALL.")
    print("   Within this fixture, the declared value 9 blocks that graph edit.")
    print("   This rule has no authority outside the declared fixture.'")
    print("  This scripted step invokes no language model; no comparative cost or latency is measured.")

    # Step 4: Proposer Strategy 2 — Manifold Retraction to Hadamard Cube Variety
    print("\n--- PHASE 4: APPLYING THE DECLARED GRAPH RETRACTION ---")
    print("  Fixture narrative (not evaluated by this script):")
    print("    1. The graph declares a single-matrix branch and a restricted-family branch.")
    print("    2. The next move removes the former branch's three fixture edges.")
    print("    3. No ideal membership, family classification, or MUB compatibility is computed here.")

    # Retract the false single-matrix ideal edge and Tao obstruction cycle
    retracted_claims = dict(gov.edge_claims)
    retracted_claims[("ideal_i55", "tao_s6")] = Fraction(0)
    retracted_claims[("tao_s6", "conj2_gamma1")] = Fraction(0)
    retracted_claims[("ideal_i55", "conj2_gamma1")] = Fraction(0)

    verdict_retract = gov.step_cut(proposed_claims=retracted_claims)
    print("  CUT (Excision of single-matrix ideal loop):")
    print(f"    Admitted: {verdict_retract.admitted} | Defect Before: {verdict_retract.defect_before} -> Defect After: {verdict_retract.defect_after}")
    print(f"    New Primary Obstruction Phi_1 = {gov.primary_obstruction()}")

    # Step 5: Graph-local gauge projection
    print("\n--- PHASE 5: HOST GOVERNOR GRAPH-LOCAL GAUGE PROJECTION ---")
    norm, gauge = compute_phi1(graph, gov.claims_cochain())
    print(f"  Minimizing Gauge Potential on Hadamard Cube Complex: {gauge}")

    verdict_descent = gov.step_cut(proposed_section=gauge)
    print(f"  CUT with Gauge Potential: Admitted={verdict_descent.admitted} | Defect After: {verdict_descent.defect_after}")

    # Step 6: Terminal Verification Gate
    print("\n--- PHASE 6: TOY-GRAPH ZERO-OBSTRUCTION CHECK ---")
    final_verify = gov.step_verify("ZERO_OBSTRUCTION")
    print(f"  VERIFY 'ZERO_OBSTRUCTION': Admitted={final_verify.admitted}, Status={final_verify.status}")
    print(f"  Final Primary Obstruction Phi_1 = {gov.primary_obstruction()}")

    # Append terminal success to cemetery sink (Zero Data-Loss)
    clean_danger = DangerSignal(Fraction(0), Fraction(0), 0)
    terminal_hash = cemetery.append_candidate(
        step_index=2,
        prompt_sha256=prompt_hash,
        candidate_tokens=json.dumps({"admitted_subvariety": "Fourier_cup_Szollosi", "cube_verified": True}),
        danger=clean_danger,
        disposition="ACCEPTED_TERMINAL",
        ddc_letter="T",
        notes="Illustrative graph scenario completed; no ideal-membership or classification theorem is proved"
    )
    print(f"  Cemetery DAG Recorded Records: {len(cemetery.entries)} | Terminal Hash: {terminal_hash[:16]}...")
    print("=" * 80)

    return {
        "status": "ILLUSTRATIVE_GRAPH_COMPLETE",
        "initial_phi1": str(phi_initial),
        "final_phi1": str(gov.primary_obstruction()),
        "declared_fixture_g1": "9",
        "declared_fixture_g2_product": "1296",
        "cemetery_records": len(cemetery.entries),
        "terminal_hash": terminal_hash,
    }

if __name__ == "__main__":
    run_symbol_game_matolcsi_conjecture2_bout()
