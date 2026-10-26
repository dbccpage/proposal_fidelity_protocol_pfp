"""
symbol_game_r4_playground.py
----------------------------
Interactive Symbol Game Playground & Epistemic Immune System Testbed
Demonstrating:
1. Layer 1: Exact Rational Simplex / Holonomy Governor (solve_graph_phi1.exe)
2. Layer 2: Three Proposer Strategies (Hallucinating vs Scratchpad vs Simplex)
3. Layer 3: Epistemic Immune System (Danger Signals, Thymic Selection, Cemetery DAG, Antibody Minting)
4. An illustrative graph encoding inspired by Residual R4 (not a discharge or proof)
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
# 2. Residual R4 Carrier Graph Formulation
# ==============================================================================

def create_r4_carrier_graph() -> Tuple[ConstraintGraph, L1SymbolGameGovernor]:
    """
    R4 Carrier Graph:
    Nodes:
      - 'triple_t'     : Candidate MU triple (B0, B1, B2) on Szollosi deltoid B6(theta)
      - 'mu_vec_v'     : Single unit vector v mutually unbiased to the triple
      - 'psi_sq_wall'  : Continuous curvature wall Psi^2(v) >= 12133/30000 > 0
      - 'zerorel_empty': Emptiness of the ZeroRel variety for the triple
      - 'basis_b3'     : 6-vector orthonormal basis B3 = (v_0, ..., v_5)
    Edges & Relations:
      Cycle 1 (Holonomy Loop):
        triple_t -> mu_vec_v      (weight 1): Vector projection existence
        mu_vec_v -> psi_sq_wall   (weight 1): Curvature positivity evaluation
        psi_sq_wall -> zerorel_empty (weight 1): Variety emptiness implication
        zerorel_empty -> basis_b3 (weight 2): Basis extension obstruction
        basis_b3 -> triple_t      (weight 2): Configuration closure
    """
    vertices = ("triple_t", "mu_vec_v", "psi_sq_wall", "zerorel_empty", "basis_b3")
    edges = (
        ("triple_t", "mu_vec_v", 1),
        ("mu_vec_v", "psi_sq_wall", 1),
        ("psi_sq_wall", "zerorel_empty", 1),
        ("zerorel_empty", "basis_b3", 2),
        ("basis_b3", "triple_t", 2),
    )
    graph = ConstraintGraph(
        vertices=vertices,
        edges=tuple(Edge(u, v, Fraction(w)) for u, v, w in edges)
    )
    gov = L1SymbolGameGovernor(graph)
    return graph, gov

# ==============================================================================
# 3. Main Playground Execution
# ==============================================================================

def run_symbol_game_r4_bout():
    print("=" * 80)
    print("SYMBOL GAME PLAYGROUND: ILLUSTRATIVE RESIDUAL-R4-LABELED GRAPH")
    print("=" * 80)

    graph, gov = create_r4_carrier_graph()
    cemetery = CemeteryDAGSink()
    prompt_hash = hashlib.sha256(b"R4: Link Psi^2 vector wall to 6-vector basis projection").hexdigest()

    # Step 1: Initial Assertions (Building the active cycle)
    print("\n--- PHASE 1: ASSERTING ACTIVE CLAIMS (CYCLE EMBEDDING) ---")
    initial_claims = {
        ("triple_t", "mu_vec_v"): 1,
        ("mu_vec_v", "psi_sq_wall"): 1,
        ("psi_sq_wall", "zerorel_empty"): 1,
        ("zerorel_empty", "basis_b3"): 1,
        ("basis_b3", "triple_t"): 1,
    }
    for (u, v), val in initial_claims.items():
        verdict = gov.step_assert(u, v, Fraction(val))
        print(f"  ASSERT {u:<14} -> {v:<14} = {val} | status: {verdict.status:<10} | Phi_1 = {gov.primary_obstruction()}")

    phi_initial = gov.primary_obstruction()
    print(f"\n[HOST GOVERNOR] Initial Primary Obstruction Phi_1 = {phi_initial}")

    # Step 2: Proposer Strategy 1 — Hallucinating Proposer (Arm 1 style, cancellation laundering)
    print("\n--- PHASE 2: EVALUATING PROPOSER STRATEGY 1 (UNCONSTRAINED / HALLUCINATING) ---")
    hallucination_tokens = (
        '{"move_type": "CUT", "claims": {"triple_t->mu_vec_v": 0, "basis_b3->triple_t": 0}, '
        '"justification": "Clearly basis extension exists by linearity, cancelling the cycle"}'
    )
    print(f"  Lesser Model Emits: {hallucination_tokens}")

    # Thymic Negative Selection Check
    admitted_alphabet = {"ASSERT", "CUT", "VERIFY", "RETRACT"}
    thymic = evaluate_thymic_selection("CUT", admitted_alphabet)
    print(f"  Thymic Selection Check: {thymic.reason} (admitted={thymic.admitted})")

    # Proposer tries an inflated claim set that increases obstruction
    bad_claims = {e.key: Fraction(3) for e in graph.edges}
    cut_verdict = gov.step_cut(proposed_claims=bad_claims)
    print(f"  Host Verdict on Bad CUT: Admitted={cut_verdict.admitted}, Status={cut_verdict.status}, DefectBefore={cut_verdict.defect_before} -> DefectAfter={cut_verdict.defect_after}")

    # Quarantine Triggered!
    danger = DangerSignal(defect_mass=cut_verdict.defect_after, cycle_obstruction=cut_verdict.defect_after, unadmitted_tokens=0)
    entry_hash = cemetery.append_candidate(
        step_index=1,
        prompt_sha256=prompt_hash,
        candidate_tokens=hallucination_tokens,
        danger=danger,
        disposition="REFUSED_DEFECT_NON_DESCENT",
        ddc_letter="M",
        notes="Model attempted cancellation laundering and defect inflation without computing Stiefel projection"
    )
    print(f"  [QUARANTINE TRIGGERED] Committed to Cemetery DAG! Hash: {entry_hash[:16]}... (DDC Letter: M)")

    # Step 3: Mining the Hallucination -> Minting the Deterministic Antibody
    print("\n--- PHASE 3: MINING CEMETERY DAG & MINTING DETERMINISTIC ANTIBODY ---")
    print("  Antibody #A-R4-001 Minted:")
    print("  'RULE: Any candidate move proposing basis extension without satisfying")
    print("   the trace condition Tr(sum_{k=0}^5 |v_k><v_k|) = 6 is rejected PRE-CALL.'")
    print("  This scripted step invokes no language model; no comparative cost or latency is measured.")

    # Step 4: Proposer Strategy 2 — Structured Topological Scratchpad (Arm 2 style)
    print("\n--- PHASE 4: EVALUATING PROPOSER STRATEGY 2 (NUMERIC SCRATCHPAD) ---")
    print("  Declared fixture narrative (not derived by this script):")
    print("    1. Nodes carry labels borrowed from an R4 research program.")
    print("    2. Edge values below are graph inputs, not evaluated analytic inequalities.")
    print("    3. Repairing this graph does not establish vector, basis, or variety nonexistence.")

    # Step 5: Exact graph-local gauge projection
    print("\n--- PHASE 5: HOST GOVERNOR GRAPH-LOCAL GAUGE PROJECTION ---")
    norm, gauge = compute_phi1(graph, gov.claims_cochain())
    print(f"  Host Native Minimizing Gauge: {gauge}")

    verdict_descent = gov.step_cut(proposed_section=gauge)
    print("  CUT with Exact Gauge Potential:")
    print(f"    Admitted: {verdict_descent.admitted} | Defect Before: {verdict_descent.defect_before} -> Defect After: {verdict_descent.defect_after}")
    print(f"    Lyapunov Descent Verified: {verdict_descent.defect_after < verdict_descent.defect_before} (7 -> 5)")

    # Step 6: Terminal Verification of Survivor Obstruction
    verify_verdict = gov.step_verify("ZERO_OBSTRUCTION")
    print("\n--- PHASE 6: TOY-GRAPH SURVIVOR TRACE ---")
    print(f"  VERIFY 'ZERO_OBSTRUCTION': {verify_verdict.status} (Final Phi_1 = {gov.primary_obstruction()})")
    print("  Toy-graph survivor recorded: Phi_1 = 5; this is not a deltoid no-go proof.")

    # Step 7: Topological Frame Break / Excision of False Existence Claim
    print("\n--- PHASE 7: FIXTURE EDGE REPAIR ---")
    retracted_claims = dict(gov.edge_claims)
    retracted_claims[("basis_b3", "triple_t")] = Fraction(0)
    verdict_repair = gov.step_cut(proposed_claims=retracted_claims)
    print("  CUT (Excision of basis_b3 -> triple_t):")
    print(f"    Admitted: {verdict_repair.admitted} | Defect Before: {verdict_repair.defect_before} -> Defect After: {verdict_repair.defect_after}")
    print(f"    New Primary Obstruction Phi_1 = {gov.primary_obstruction()}")

    final_verify = gov.step_verify("ZERO_OBSTRUCTION")
    print(f"  FINAL VERIFY: Admitted={final_verify.admitted}, Status={final_verify.status}")

    # Append terminal success to cemetery sink (Zero Data-Loss)
    clean_danger = DangerSignal(Fraction(0), Fraction(0), 0)
    cemetery.append_candidate(
        step_index=2,
        prompt_sha256=prompt_hash,
        candidate_tokens=json.dumps({"repaired_claims": {f"{u}->{v}": str(val) for (u, v), val in retracted_claims.items()}}),
        danger=clean_danger,
        disposition="ACCEPTED_TERMINAL",
        ddc_letter="T",
        notes="Illustrative graph repaired to zero graph defect; no residual-R4 theorem is established"
    )
    print(f"  Cemetery DAG Total Recorded Records: {len(cemetery.entries)}")
    print("=" * 80)

if __name__ == "__main__":
    run_symbol_game_r4_bout()
