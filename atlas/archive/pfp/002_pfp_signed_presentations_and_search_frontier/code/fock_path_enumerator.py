"""
Standalone Fock-Space Path Enumerator and Weight Bound Verifier.
Triangular Hubbard Plaquette (C3) at t=1, U=2, beta=1/4.

Verifies the restricted proposition:
  In the declared continuous-time 64-state Fock-space path carrier,
  there are exactly 192 rooted closed 3-hop paths (96 negative, 96 positive).
  The negative path A=|110;111> -> B=|101;111> -> C=|011;111> -> A has weight -exp(-1)/384.
  Every positive path has weight strictly outside the interval containing exp(-1)/384,
  excluding any equal-magnitude individual positive path partner for a weight-preserving involution.

This is a floating-point display of the same proposition; the exact rational
check is exact_fock_gap.verify_exact_gap.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class FockState:
    """Occupation of 3 sites by up and down electrons: (n_0u, n_1u, n_2u, n_0d, n_1d, n_2d)."""
    occ: Tuple[int, int, int, int, int, int]

    @property
    def n_up(self) -> Tuple[int, int, int]:
        return self.occ[0:3]

    @property
    def n_dn(self) -> Tuple[int, int, int]:
        return self.occ[3:6]

    @property
    def total_particles(self) -> int:
        return sum(self.occ)

    def interaction_energy(self, U: float = 2.0) -> float:
        """E_U = U * sum_{i=0}^2 n_{i,up} * n_{i,dn}."""
        double_occ = sum(self.occ[i] * self.occ[i + 3] for i in range(3))
        return U * double_occ

    def __repr__(self) -> str:
        u_str = "".join(str(x) for x in self.n_up)
        d_str = "".join(str(x) for x in self.n_dn)
        return f"|{u_str};{d_str}>"


def build_all_64_states() -> List[FockState]:
    """Generates all 2^6 = 64 Fock states in standard binary order."""
    states = []
    for occ in itertools.product([0, 1], repeat=6):
        states.append(FockState(occ))
    return states


def hopping_matrix_element(s1: FockState, s2: FockState, t: float = 1.0) -> float:
    """
    Computes off-diagonal matrix element <s2 | (-H_hop) | s1>.
    H_hop = -t sum_sigma sum_<i,j> (c_{j,sigma}^dag c_{i,sigma} + c_{i,sigma}^dag c_{j,sigma}).
    Therefore -H_hop has hopping amplitude +t.
    Includes Jordan-Wigner / fermion anticommutation signs under ordering:
      (0_up, 1_up, 2_up, 0_dn, 1_dn, 2_dn).
    """
    # Count differences
    diffs = [(i, s1.occ[i], s2.occ[i]) for i in range(6) if s1.occ[i] != s2.occ[i]]
    if len(diffs) != 2:
        return 0.0

    (i, s1_i, s2_i), (j, s1_j, s2_j) = diffs
    # Must be one creation and one annihilation in the SAME spin sector
    if (i < 3 and j >= 3) or (i >= 3 and j < 3):
        return 0.0

    # Ensure i is annihilation (1 -> 0) and j is creation (0 -> 1)
    if s1_i == 1 and s2_i == 0 and s1_j == 0 and s2_j == 1:
        ann_site, cre_site = i, j
    elif s1_j == 1 and s2_j == 0 and s1_i == 0 and s2_i == 1:
        ann_site, cre_site = j, i
    else:
        return 0.0

    # Check that spatial sites are adjacent on C3 triangle: (0,1), (1,2), (2,0)
    site_a = ann_site % 3
    site_b = cre_site % 3
    bonds = {(0, 1), (1, 0), (1, 2), (2, 1), (2, 0), (0, 2)}
    if (site_a, site_b) not in bonds:
        return 0.0

    # Fermionic sign: count occupied modes between min(ann, cre) and max(ann, cre)
    low, high = min(ann_site, cre_site), max(ann_site, cre_site)
    intervening_particles = sum(s1.occ[m] for m in range(low + 1, high))
    sign = (-1) ** intervening_particles

    return float(sign * t)


@dataclass(frozen=True)
class ClosedPath3Hop:
    s0: FockState
    s1: FockState
    s2: FockState
    hop_product: float
    energies: Tuple[float, float, float]
    max_energy: float
    integrated_weight: float


def compute_path_weight_3hop(energies: Tuple[float, float, float], hop_product: float, beta: float = 0.25) -> float:
    """
    Computes time-ordered integral:
      int_0^beta dt3 int_0^t3 dt2 int_0^t2 dt1 exp(-E0*(beta - t3 + t1) - E1*(t2 - t1) - E2*(t3 - t2)) * hop_product
    If E0 == E1 == E2 = E, simplifies to:
      hop_product * (beta^3 / 6) * exp(-E * beta).
    """
    if len(energies) != 3 or not all(math.isfinite(x) for x in (*energies, hop_product, beta)) or beta < 0:
        raise ValueError("Finite energies, amplitude and nonnegative beta required")
    # Dirichlet simplex integral: after factoring exp(-M beta), its analytic
    # series is beta^3 sum_k h_k(beta*(M-E0), ..., beta*(M-E0))/(k+3)!.
    # All terms are nonnegative; h_k is the complete homogeneous polynomial.
    # Decimal evaluation is numerical; the proposition uses analytic bounds.
    with localcontext() as ctx:
        ctx.prec = 60
        es = [Decimal(str(x)) for x in (energies[0], energies[1], energies[2], energies[0])]
        b = Decimal(str(beta))
        maximum = max(es)
        deltas = [b * (maximum - e) for e in es]
        h = [Decimal(1)] + [Decimal(0)] * 400
        for delta in deltas:
            for k in range(1, len(h)):
                h[k] += delta * h[k - 1]
        total = Decimal(0)
        factorial = Decimal(6)
        for k, coefficient in enumerate(h):
            if k:
                factorial *= k + 3
            term = coefficient / factorial
            total += term
            if k > 0 and term <= abs(total) * Decimal("1e-50"):
                break
        else:
            raise ArithmeticError("Path integral series did not converge within the declared budget")
        return float(Decimal(str(hop_product)) * b**3 * (-maximum * b).exp() * total)


def enumerate_3hop_paths(beta: float = 0.25, U: float = 2.0, t: float = 1.0) -> List[ClosedPath3Hop]:
    """Enumerates all rooted closed 3-hop sequences on the 64-state Fock space."""
    states = build_all_64_states()

    # Build adjacency
    adj: Dict[FockState, List[Tuple[FockState, float]]] = {s: [] for s in states}
    for s1 in states:
        for s2 in states:
            m = hopping_matrix_element(s1, s2, t=t)
            if m != 0.0:
                adj[s1].append((s2, m))

    paths = []
    for s0 in states:
        for s1, m1 in adj[s0]:
            for s2, m2 in adj[s1]:
                # Must close back to s0
                for s_close, m3 in adj[s2]:
                    if s_close == s0:
                        hop_prod = m1 * m2 * m3
                        e0 = s0.interaction_energy(U)
                        e1 = s1.interaction_energy(U)
                        e2 = s2.interaction_energy(U)
                        wt = compute_path_weight_3hop((e0, e1, e2), hop_prod, beta=beta)
                        paths.append(ClosedPath3Hop(
                            s0=s0,
                            s1=s1,
                            s2=s2,
                            hop_product=hop_prod,
                            energies=(e0, e1, e2),
                            max_energy=max(e0, e1, e2),
                            integrated_weight=wt,
                        ))
    return paths


def verify_fock_path_proposition() -> Dict[str, object]:
    """
    Executes the full proof of the restricted Fock path proposition:
      1. Total rooted 3-hop paths = 192 (96 negative, 96 positive).
      2. The cited negative path A->B->C->A has weight -exp(-1)/384.
      3. Positive paths have max interaction energy <= 2 along their paths.
      4. Weight gap certifies exclusion of any equal-magnitude individual pairing.
    """
    paths = enumerate_3hop_paths(beta=0.25, U=2.0, t=1.0)

    neg_paths = [p for p in paths if p.hop_product < 0]
    pos_paths = [p for p in paths if p.hop_product > 0]

    # Verify counts
    assert len(paths) == 192, f"Expected 192 paths, got {len(paths)}"
    assert len(neg_paths) == 96, f"Expected 96 negative paths, got {len(neg_paths)}"
    assert len(pos_paths) == 96, f"Expected 96 positive paths, got {len(pos_paths)}"

    # Identify the target path: |110;111> -> |101;111> -> |011;111> -> |110;111>
    target_s0 = FockState((1, 1, 0, 1, 1, 1))
    target_s1 = FockState((1, 0, 1, 1, 1, 1))
    target_s2 = FockState((0, 1, 1, 1, 1, 1))

    target_path = None
    for p in neg_paths:
        if p.s0 == target_s0 and p.s1 == target_s1 and p.s2 == target_s2:
            target_path = p
            break

    assert target_path is not None, "Target negative path not found in enumeration"
    assert target_path.energies == (4.0, 4.0, 4.0), f"Target path energies must be (4,4,4), got {target_path.energies}"

    # Target path analytic weight: -exp(-1) / 384
    analytic_target_wt = -math.exp(-1.0) / 384.0
    abs_target_wt = abs(analytic_target_wt)  # approx 0.0009580

    # Check maximum interaction energy of all positive 3-hop paths
    pos_energies = [p.max_energy for p in pos_paths]
    max_pos_energy = max(pos_energies)

    # Every positive path has max energy <= 2.0
    assert max_pos_energy <= 2.0, f"Expected max positive path energy <= 2.0, got {max_pos_energy}"

    # Smallest positive 3-hop weight occurs when energy is highest (E=2.0 throughout)
    # which gives weight >= exp(-2 * 0.25) / 384 = exp(-0.5) / 384 approx 0.0015795
    min_pos_3hop_wt = min(p.integrated_weight for p in pos_paths)

    # Each individual hopping matrix element has magnitude t=1. This is NOT
    # an operator-norm bound and NOT a bound on the sum over all paths.
    # For n>=4, beta^n/n! decreases since beta/(n+1)<1.
    states = build_all_64_states()
    max_energy = max(s.interaction_energy(2) for s in states)
    assert max_energy == 6
    assert all(abs(hopping_matrix_element(a, b)) <= 1 for a in states for b in states)
    assert all(hopping_matrix_element(s, s) == 0 for s in states)  # no 1-hop path
    zero_hop_lower_bound = math.exp(-6 * 0.25)
    two_hop_lower_bound = math.exp(-6 * 0.25) * 0.25**2 / 2
    # Every allowed 2-hop closed sequence has product +1 by real symmetry.
    assert all(hopping_matrix_element(a, b) * hopping_matrix_element(b, a) == 1
               for a in states for b in states if hopping_matrix_element(a, b))
    assert math.isclose(target_path.integrated_weight, analytic_target_wt, rel_tol=1e-14)
    assert zero_hop_lower_bound > abs_target_wt and two_hop_lower_bound > abs_target_wt
    analytic_positive_3hop_lower_bound = math.exp(-0.5) / 384
    assert min_pos_3hop_wt >= analytic_positive_3hop_lower_bound - 1e-16
    # Strict separation also follows without floating point from 2<e<3:
    # 1/6144 < 1/(3*384) < e^-1/384;
    # e^-3/2/32 > 1/(9*32) > 1/(2*384) > e^-1/384.
    assert Fraction(1, 6144) < Fraction(1, 3*384)
    assert Fraction(1, 9*32) > Fraction(1, 2*384)

    four_hop_upper_bound = (0.25 ** 4 / 24.0)  # 1 / 6144

    # Verify strict gap separation:
    # 4-hop bound < |target_wt| < min_pos_3hop_wt
    assert four_hop_upper_bound < abs_target_wt < min_pos_3hop_wt, (
        f"Gap violated: {four_hop_upper_bound} < {abs_target_wt} < {min_pos_3hop_wt}"
    )

    return {
        "total_paths": len(paths),
        "neg_paths": len(neg_paths),
        "pos_paths": len(pos_paths),
        "target_weight": analytic_target_wt,
        "abs_target_weight": abs_target_wt,
        "max_positive_path_energy": max_pos_energy,
        "min_positive_3hop_weight": min_pos_3hop_wt,
        "four_hop_upper_bound": four_hop_upper_bound,
        "zero_hop_lower_bound": zero_hop_lower_bound,
        "two_hop_lower_bound": two_hop_lower_bound,
        "one_hop_paths": 0,
        "analytic_positive_3hop_lower_bound": analytic_positive_3hop_lower_bound,
        "carrier": "rooted discrete hopping sequences with all ordered hop times integrated out",
        "weight_evaluation": "60-digit Decimal analytic series; proof uses analytic energy/amplitude bounds",
        "gap_certified": True,
    }


if __name__ == "__main__":
    res = verify_fock_path_proposition()
    print("=" * 75)
    print("FOCK-SPACE PATH ENUMERATION (FLOATING-POINT DISPLAY)")
    print("=" * 75)
    print(f"Total Rooted 3-Hop Paths: {res['total_paths']}")
    print(f"  - Negative Paths: {res['neg_paths']}")
    print(f"  - Positive Paths: {res['pos_paths']}")
    print("Target Path: |110;111> -> |101;111> -> |011;111> -> |110;111>")
    print(f"  - Exact Weight: -exp(-1) / 384 = {res['target_weight']:.7f}")
    print(f"  - Absolute Magnitude: {res['abs_target_weight']:.7f}")
    print("Positive Path Weight Bounds:")
    print(f"  - Max Interaction Energy in Positive Paths: E_U = {res['max_positive_path_energy']:.1f}")
    print(f"  - Minimum Positive 3-Hop Weight: >= exp(-1/2)/384 = {res['min_positive_3hop_weight']:.7f}")
    print(f"  - 4-or-more-Hop Path Weight Upper Bound: <= 1/6144 = {res['four_hop_upper_bound']:.7f}")
    print("Strict Disjoint Gap Separation:")
    print(f"  1/6144 ({res['four_hop_upper_bound']:.7f}) < |w_target| ({res['abs_target_weight']:.7f}) < exp(-1/2)/384 ({res['min_positive_3hop_weight']:.7f})")
    print("Displayed separation holds; the exact rational check is exact_fock_gap.py.")
    print("=" * 75)
