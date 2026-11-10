# AuthorityEffect: None.
"""
Exact MUB constructions across prime-power and composite dimensions.

Implements exact construction of Mutually Unbiased Bases (MUBs):
- Odd primes d in {3, 5, 7}: Quadratic chirp bases over F_p in Q(zeta_p).
- Odd prime power d = 9: Quadratic chirp bases over GF(9) in Q(zeta_3).
- Characteristic 2 d in {2, 4, 8}: Galois ring GR(4, r) characters in Q(zeta_4) = Q(i).
- Composite d = 6, 10: Tensor product of prime factor MUBs in Q(zeta_{lcm(m1, m2)}).
- Refusal handling:
  * d = 6 with k >= 4 -> UNKNOWN (OPEN_PROBLEM)
  * Any k > d + 1 -> OUT_OF_SCOPE
- Fixed B_0 support via unitary / monomial rotation.
"""

from fractions import Fraction
from math import lcm
from typing import Any, Dict, List, Tuple

from .cyclotomic import (
    CyclotomicElement,
    format_fraction,
)
from .finite_field import FiniteFieldGF9, GaloisRingGR4


def construct_mub_odd_prime(p: int) -> Tuple[int, List[List[Dict[str, Any]]]]:
    """
    Construct complete set of p + 1 MUBs for odd prime p in Q(zeta_p).
    Returns (m, bases) where m = p.
    """
    m = p
    inv2 = pow(2, -1, p)
    bases: List[List[Dict[str, Any]]] = []

    # Basis 0: Computational basis
    b0: List[Dict[str, Any]] = []
    for k in range(p):
        ent = []
        for coord in range(p):
            coeffs = [Fraction(0)] * m
            if coord == k:
                coeffs[0] = Fraction(1)
            ent.append([format_fraction(c) for c in coeffs])
        b0.append({"norm2": "1", "entries": ent})
    bases.append(b0)

    # Bases 1..=p: Slopes s in 0..p-1
    for s in range(p):
        bs: List[Dict[str, Any]] = []
        for k in range(p):
            ent = []
            for j in range(p):
                pow_val = (inv2 * s * j * j + k * j) % p
                coeffs = [Fraction(0)] * m
                coeffs[pow_val] = Fraction(1)
                ent.append([format_fraction(c) for c in coeffs])
            bs.append({"norm2": str(p), "entries": ent})
        bases.append(bs)

    return m, bases


def construct_mub_gf9() -> Tuple[int, List[List[Dict[str, Any]]]]:
    """
    Construct complete set of 10 MUBs for d = 9 over GF(9) in Q(zeta_3).
    Returns (m, bases) where m = 3.
    """
    d = 9
    m = 3
    gf9 = FiniteFieldGF9()
    elements = gf9.elements  # 9 elements in GF(9)
    bases: List[List[Dict[str, Any]]] = []

    # Basis 0: Computational basis
    b0: List[Dict[str, Any]] = []
    for k in range(d):
        ent = []
        for coord in range(d):
            coeffs = [Fraction(0)] * m
            if coord == k:
                coeffs[0] = Fraction(1)
            ent.append([format_fraction(c) for c in coeffs])
        b0.append({"norm2": "1", "entries": ent})
    bases.append(b0)

    # 9 chirp bases indexed by a in GF(9)
    # In GF(9), 2^{-1} = 2
    for a in elements:
        ba: List[Dict[str, Any]] = []
        for b in elements:
            ent = []
            for x in elements:
                # 2 * a * x^2 + b * x
                x2 = gf9.mul(x, x)
                ax2 = gf9.mul(a, x2)
                two_ax2 = ((2 * ax2[0]) % 3, (2 * ax2[1]) % 3)
                bx = gf9.mul(b, x)
                val = gf9.add(two_ax2, bx)
                tr_val = gf9.trace(val)  # in {0, 1, 2}
                coeffs = [Fraction(0)] * m
                coeffs[tr_val] = Fraction(1)
                ent.append([format_fraction(c) for c in coeffs])
            ba.append({"norm2": "9", "entries": ent})
        bases.append(ba)

    return m, bases


def construct_mub_char_two(d: int) -> Tuple[int, List[List[Dict[str, Any]]]]:
    """
    Construct complete set of d + 1 MUBs for d in {2, 4, 8} over GR(4, r) in Q(zeta_4) = Q(i).
    Returns (m, bases) where m = 4.
    """
    m = 4
    r_map = {2: 1, 4: 2, 8: 3}
    r = r_map[d]
    gr = GaloisRingGR4(r)
    teich = gr.teichmuller_set  # d elements
    bases: List[List[Dict[str, Any]]] = []

    # Basis 0: Computational basis
    b0: List[Dict[str, Any]] = []
    for k in range(d):
        ent = []
        for coord in range(d):
            coeffs = [Fraction(0)] * m
            if coord == k:
                coeffs[0] = Fraction(1)
            ent.append([format_fraction(c) for c in coeffs])
        b0.append({"norm2": "1", "entries": ent})
    bases.append(b0)

    # d chirp bases indexed by a in T_r
    for a in teich:
        ba: List[Dict[str, Any]] = []
        for b in teich:
            ent = []
            for x in teich:
                # Tr(a * x^2 + 2 * b * x) mod 4
                x2 = gr.mul(x, x)
                ax2 = gr.mul(a, x2)
                bx = gr.mul(b, x)
                two_bx = gr.scale_int(bx, 2)
                val = gr.add(ax2, two_bx)
                power = gr.trace(val)  # in {0, 1, 2, 3}
                coeffs = [Fraction(0)] * m
                coeffs[power] = Fraction(1)
                ent.append([format_fraction(c) for c in coeffs])
            ba.append({"norm2": str(d), "entries": ent})
        bases.append(ba)

    return m, bases


def construct_mub_composite_tensor(
    d1: int,
    m1: int,
    bases1: List[List[Dict[str, Any]]],
    d2: int,
    m2: int,
    bases2: List[List[Dict[str, Any]]],
) -> Tuple[int, List[List[Dict[str, Any]]]]:
    """
    Construct tensor product MUBs for d = d1 * d2.
    Number of bases is min(len(bases1), len(bases2)).
    Resulting field is Q(zeta_m) where m = lcm(m1, m2).
    """
    d1 * d2
    m = lcm(m1, m2)
    m // m1
    m // m2
    num_bases = min(len(bases1), len(bases2))
    composite_bases: List[List[Dict[str, Any]]] = []

    for b_idx in range(num_bases):
        b1 = bases1[b_idx]
        b2 = bases2[b_idx]
        cb: List[Dict[str, Any]] = []
        for v1 in b1:
            n1 = Fraction(v1["norm2"])
            for v2 in b2:
                n2 = Fraction(v2["norm2"])
                norm2_prod = format_fraction(n1 * n2)
                ent: List[List[str]] = []
                # Kronecker product of entries
                for c1_wire in v1["entries"]:
                    e1 = CyclotomicElement(m1, c1_wire).lift_to(m)
                    for c2_wire in v2["entries"]:
                        e2 = CyclotomicElement(m2, c2_wire).lift_to(m)
                        prod = e1 * e2
                        ent.append(prod.to_wire())
                cb.append({"norm2": norm2_prod, "entries": ent})
        composite_bases.append(cb)

    return m, composite_bases


def get_standard_mubs(d: int) -> Tuple[int, List[List[Dict[str, Any]]]]:
    """Retrieve standard MUB system for dimension d."""
    if d in (3, 5, 7):
        return construct_mub_odd_prime(d)
    elif d in (2, 4, 8):
        return construct_mub_char_two(d)
    elif d == 9:
        return construct_mub_gf9()
    elif d == 6:
        m1, b1 = construct_mub_char_two(2)
        m2, b2 = construct_mub_odd_prime(3)
        return construct_mub_composite_tensor(2, m1, b1, 3, m2, b2)
    elif d == 10:
        m1, b1 = construct_mub_char_two(2)
        m2, b2 = construct_mub_odd_prime(5)
        return construct_mub_composite_tensor(2, m1, b1, 5, m2, b2)
    else:
        raise ValueError(f"Unsupported dimension d={d}")


def apply_fixed_first_basis(
    d: int,
    std_m: int,
    std_bases: List[List[Dict[str, Any]]],
    fixed_b0: List[Dict[str, Any]],
    k: int,
) -> Tuple[int, List[List[Dict[str, Any]]]]:
    """
    Apply unitary transformation that maps the computational basis (basis 0) to fixed_b0.
    Rotates all subsequent bases so that the first basis is exactly fixed_b0.
    """
    # Detect cyclotomic order of fixed_b0
    m_b0 = len(fixed_b0[0]["entries"][0])
    target_m = lcm(std_m, m_b0)

    # Columns of U are the vectors of fixed_b0 (lifted to target_m)
    # U[row][col] = fixed_b0[col]["entries"][row]
    u_cols: List[List[CyclotomicElement]] = []
    for vec in fixed_b0:
        col = [CyclotomicElement(m_b0, entry).lift_to(target_m) for entry in vec["entries"]]
        u_cols.append(col)

    # Norm of fixed_b0 vectors
    n0 = Fraction(fixed_b0[0]["norm2"])

    transformed_bases: List[List[Dict[str, Any]]] = []

    # First basis is fixed_b0 lifted to target_m
    b0_lifted: List[Dict[str, Any]] = []
    for vec in fixed_b0:
        lifted_entries = [
            CyclotomicElement(m_b0, entry).lift_to(target_m).to_wire() for entry in vec["entries"]
        ]
        b0_lifted.append({"norm2": vec["norm2"], "entries": lifted_entries})
    transformed_bases.append(b0_lifted)

    # For subsequent bases b in 1..k-1
    for b_idx in range(1, k):
        base = std_bases[b_idx]
        new_base: List[Dict[str, Any]] = []
        for vec in base:
            std_norm = Fraction(vec["norm2"])
            new_norm = format_fraction(std_norm * n0)
            # vector coords in std basis
            v_coords = [
                CyclotomicElement(std_m, entry).lift_to(target_m) for entry in vec["entries"]
            ]
            # U * v = sum_{j=0}^{d-1} v_j * u_col[j]
            res_coords: List[CyclotomicElement] = [
                CyclotomicElement.zero(target_m) for _ in range(d)
            ]
            for j in range(d):
                v_j = v_coords[j]
                if v_j.is_zero():
                    continue
                for row in range(d):
                    res_coords[row] = res_coords[row] + (u_cols[j][row] * v_j)

            new_base.append({"norm2": new_norm, "entries": [elem.to_wire() for elem in res_coords]})
        transformed_bases.append(new_base)

    return target_m, transformed_bases


def build_mub_solution(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Core MUB solver pipeline.
    Handles known prime-power dimensions, composite dimensions, open problem refusal,
    out of scope requests, and fixed first basis constraints.
    """
    case_id = case.get("case_id") or case.get("id", "mub_case")
    d = case.get("dimension")
    k = case.get("num_bases")
    fixed_b0 = case.get("fixed_first_basis")

    if d is None or k is None:
        return {"id": case_id, "status": "ERROR", "message": "Missing dimension or num_bases"}

    # Refusal check: out of scope (k > d + 1)
    max_possible = d + 1
    if k > max_possible:
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"requested": k, "max_possible": max_possible},
        }

    # Refusal check: d = 6 with k >= 4 (Open problem)
    if d == 6 and k >= 4:
        return {"id": case_id, "status": "UNKNOWN", "refusal_code": "OPEN_PROBLEM"}

    # Generate standard bases
    std_m, all_bases = get_standard_mubs(d)

    # Check available bases count
    if k > len(all_bases):
        # E.g. composite dimensions where only 3 bases are known
        return {"id": case_id, "status": "UNKNOWN", "refusal_code": "COMPOSITE_BEYOND_TENSOR_BOUND"}

    # If fixed_b0 is specified, transform bases
    if fixed_b0 is not None:
        target_m, selected_bases = apply_fixed_first_basis(d, std_m, all_bases, fixed_b0, k)
    else:
        target_m = std_m
        selected_bases = all_bases[:k]

    return {
        "id": case_id,
        "status": "SOLVED",
        "cyclotomic_order": target_m,
        "bases": selected_bases,
    }
