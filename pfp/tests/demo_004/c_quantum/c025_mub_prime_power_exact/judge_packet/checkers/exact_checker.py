# AuthorityEffect: None.
"""
Exact Checker for C025 (Mutually Unbiased Bases in Exact Cyclotomic Arithmetic).

Verifies solutions using direct exact arithmetic over Q(zeta_m):
1. Orthogonality: <v, w> = 0 for v != w in same basis, and <v, v> = N_v.
2. Mutual unbiasedness: d * |<v, w>|^2 = N_v * N_w for v in B_i, w in B_j (i != j).
3. Basis count and dimension: exactly k bases of d vectors each.
4. Fixed B_0 preservation: if fixed_first_basis is given, one basis must match up to per-vector phases and permutations.
5. Typed refusal validation:
   - d = 6 with k >= 4 -> UNKNOWN (refusal_code == "OPEN_PROBLEM")
   - k > d + 1 -> OUT_OF_SCOPE (witness with requested and max_possible)
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Tuple

from .schema_guard import validate_certificate

try:
    from ...reference_solver.cyclotomic import (
        CyclotomicElement,
        format_fraction,
        parse_fraction,
    )
except (ImportError, ValueError):
    try:
        from reference_solver.cyclotomic import (
            CyclotomicElement,
            format_fraction,
            parse_fraction,
        )
    except (ImportError, ValueError):
        from cyclotomic import (
            CyclotomicElement,
            parse_fraction,
        )


def verify_exact(case: Dict[str, Any], answer: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Exact verification of candidate answer against case specification.
    Returns (passed: bool, message: str, details: dict).
    """
    schema_error = validate_certificate(case, answer)
    if schema_error:
        return False, schema_error, {}
    case_id = case.get("case_id")
    d = case.get("dimension")
    k = case.get("num_bases")
    fixed_b0 = case.get("fixed_first_basis")

    ans_status = answer.get("status")
    details: Dict[str, Any] = {
        "case_id": case_id,
        "dimension": d,
        "num_bases": k,
        "status": ans_status,
    }

    # Case 1: Out of scope request
    if k > d + 1:
        if ans_status != "OUT_OF_SCOPE":
            return (
                False,
                f"Expected OUT_OF_SCOPE for k={k} > d+1={d + 1}, got {ans_status}",
                details,
            )
        witness = answer.get("witness", {})
        expected_witness = {"requested": k, "max_possible": d + 1}
        if witness != expected_witness:
            return False, f"Invalid OUT_OF_SCOPE witness: {witness}", details
        return True, "OUT_OF_SCOPE certified", details

    # Case 2: Open problem (d = 6, k >= 4)
    if d == 6 and k >= 4:
        if ans_status != "UNKNOWN":
            return (
                False,
                f"CRITICAL: Claimed {ans_status} for open problem d=6 with k={k} >= 4",
                details,
            )
        refusal_code = answer.get("refusal_code")
        if refusal_code != "OPEN_PROBLEM":
            return False, f"Expected refusal_code 'OPEN_PROBLEM', got {refusal_code}", details
        return True, "OPEN_PROBLEM refusal certified", details

    # Case 3: Solved instance
    if ans_status != "SOLVED":
        return False, f"Expected SOLVED, got {ans_status}", details

    m = answer.get("cyclotomic_order")
    if not isinstance(m, int) or m < 1:
        return False, f"Invalid cyclotomic_order: {m}", details
    details["cyclotomic_order"] = m

    bases = answer.get("bases")
    if not isinstance(bases, list):
        return False, "Bases must be a list", details
    if len(bases) != k:
        return False, f"Expected {k} bases, got {len(bases)}", details

    # Validate structure and within-basis orthogonality
    parsed_bases: List[List[Tuple[Fraction, List[CyclotomicElement]]]] = []

    for b_idx, base in enumerate(bases):
        if not isinstance(base, list):
            return False, f"Basis {b_idx} must be a list of vectors", details
        if len(base) != d:
            return False, f"Basis {b_idx} has {len(base)} vectors, expected {d}", details

        parsed_base: List[Tuple[Fraction, List[CyclotomicElement]]] = []
        for v_idx, vec in enumerate(base):
            if not isinstance(vec, dict):
                return False, f"Vector B{b_idx}[{v_idx}] must be a dict", details
            n_str = vec.get("norm2")
            if not n_str:
                return False, f"Vector B{b_idx}[{v_idx}] missing norm2", details
            try:
                norm2_val = parse_fraction(n_str)
                if norm2_val <= 0:
                    return False, f"Non-positive norm2: {norm2_val}", details
            except Exception as ex:
                return False, f"Invalid norm2 format {n_str!r}: {ex}", details

            entries_raw = vec.get("entries")
            if not isinstance(entries_raw, list) or len(entries_raw) != d:
                return (
                    False,
                    f"Vector B{b_idx}[{v_idx}] entries must be list of length {d}",
                    details,
                )

            parsed_entries: List[CyclotomicElement] = []
            for c_idx, coord in enumerate(entries_raw):
                if not isinstance(coord, list) or len(coord) != m:
                    return (
                        False,
                        f"Vector B{b_idx}[{v_idx}] coord {c_idx} must have length {m}",
                        details,
                    )
                try:
                    elem = CyclotomicElement(m, coord)
                except Exception as ex:
                    return (
                        False,
                        f"Failed parsing cyclotomic coord B{b_idx}[{v_idx}][{c_idx}]: {ex}",
                        details,
                    )
                parsed_entries.append(elem)

            # Check declared norm matches sum of coord abs_sq
            calc_norm = CyclotomicElement.zero(m)
            for elem in parsed_entries:
                calc_norm = calc_norm + elem.abs_sq()
            is_rat, rat_norm = calc_norm.is_rational()
            if not is_rat:
                return (
                    False,
                    f"Vector B{b_idx}[{v_idx}] computed norm2 is not rational: {calc_norm}",
                    details,
                )
            if rat_norm != norm2_val:
                return (
                    False,
                    f"Vector B{b_idx}[{v_idx}] norm mismatch: declared {norm2_val} != computed {rat_norm}",
                    details,
                )

            parsed_base.append((norm2_val, parsed_entries))

        # Check orthogonality within basis
        for i in range(d):
            n_i, vi = parsed_base[i]
            for j in range(i + 1, d):
                n_j, vj = parsed_base[j]
                ip = CyclotomicElement.zero(m)
                for ci, cj in zip(vi, vj):
                    ip = ip + (ci.conjugate() * cj)
                if not ip.is_zero():
                    return (
                        False,
                        f"Orthogonality failure in B{b_idx} between {i} and {j}: <vi|vj> = {ip}",
                        details,
                    )

        parsed_bases.append(parsed_base)

    # Check across-basis mutual unbiasedness
    for b1 in range(k):
        for b2 in range(b1 + 1, k):
            for i in range(d):
                n1, v1 = parsed_bases[b1][i]
                for j in range(d):
                    n2, v2 = parsed_bases[b2][j]
                    ip = CyclotomicElement.zero(m)
                    for ci, cj in zip(v1, v2):
                        ip = ip + (ci.conjugate() * cj)
                    ip_abs_sq = ip.abs_sq()
                    is_rat, rat_overlap = ip_abs_sq.is_rational()
                    if not is_rat:
                        return (
                            False,
                            f"Overlap between B{b1}[{i}] and B{b2}[{j}] is not rational: {ip_abs_sq}",
                            details,
                        )
                    # d * |<v1, v2>|^2 == n1 * n2
                    if Fraction(d) * rat_overlap != n1 * n2:
                        return (
                            False,
                            f"Unbiasedness failure between B{b1}[{i}] and B{b2}[{j}]: {d} * {rat_overlap} != {n1 * n2}",
                            details,
                        )

    # Check fixed B_0 if required
    if fixed_b0 is not None:
        # One basis must match fixed_b0 up to per-vector phases and reordering
        # fixed_b0 has d vectors
        m_b0 = len(fixed_b0[0]["entries"][0])
        parsed_b0 = []
        for v in fixed_b0:
            entries = [CyclotomicElement(m_b0, e) for e in v["entries"]]
            parsed_b0.append((parse_fraction(v["norm2"]), entries))

        b0_matched = False
        for cand_base in parsed_bases:
            # Check if cand_base is a permutation of parsed_b0 up to phase
            used_b0 = [False] * d
            match_count = 0
            for _, v_cand in cand_base:
                for idx_target, (_, v_target) in enumerate(parsed_b0):
                    if used_b0[idx_target]:
                        continue
                    # Check if v_cand = phi * v_target where |phi|^2 = 1
                    # Ratio: find first non-zero coordinate
                    ratio = None
                    proportional = True
                    for c_cand, c_tar in zip(v_cand, v_target):
                        # Lift to common order
                        from math import lcm

                        l = lcm(c_cand.m, c_tar.m)
                        c1 = c_cand.lift_to(l)
                        c2 = c_tar.lift_to(l)
                        if c2.is_zero():
                            if not c1.is_zero():
                                proportional = False
                                break
                        else:
                            # ratio = c1 / c2 => c1 * c2^* / |c2|^2
                            c2_sq = c2.abs_sq()
                            is_r, r_val = c2_sq.is_rational()
                            if not is_r:
                                proportional = False
                                break
                            cur_ratio = (c1 * c2.conjugate()) * (Fraction(1) / r_val)
                            if ratio is None:
                                ratio = cur_ratio
                                # verify |ratio|^2 == 1
                                is_unit_r, unit_val = ratio.abs_sq().is_rational()
                                if not is_unit_r or unit_val != Fraction(1):
                                    proportional = False
                                    break
                            else:
                                if cur_ratio != ratio:
                                    proportional = False
                                    break
                    if proportional and ratio is not None:
                        used_b0[idx_target] = True
                        match_count += 1
                        break
            if match_count == d:
                b0_matched = True
                break

        if not b0_matched:
            return (
                False,
                "Output does not contain fixed_first_basis up to phase and permutation",
                details,
            )

    return (
        True,
        f"Exact MUB verification certified: {k} bases of dimension {d} over Q(zeta_{m})",
        details,
    )
