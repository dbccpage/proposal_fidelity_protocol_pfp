"""Checker 1 for C019: Exact verification of H2 obstruction & cochain extension certificates."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from omega_engine_pfp.tests.demo_004.b_cohomology.c019_h2_obstruction_extension.reference_solver.exact_linalg import (
    parse_rational,
)


def check_h2_certificate(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a dict"

    status = result.get("status")

    faces = list(case.get("faces", []))
    edges = list(case.get("edges", []))
    vertices = list(case.get("vertices", []))
    d2_raw = case.get("d2", {})
    d1_raw = case.get("d1", {})
    target_b_raw = case.get("B", {})
    weights_raw = case.get("weights", {})
    mode = case.get("mode", "Q")

    # 1. Nilpotency check d1 * d2 == 0
    is_nilpotent = True
    for f in faces:
        boundary_f = d2_raw.get(f, {})
        for v in vertices:
            comp = sum(boundary_f.get(e, 0) * d1_raw.get(e, {}).get(v, 0) for e in boundary_f)
            if comp != 0:
                is_nilpotent = False
                break
        if not is_nilpotent:
            break

    if not is_nilpotent:
        if status != "OUT_OF_SCOPE":
            return False, "Expected OUT_OF_SCOPE due to boundary not nilpotent"
        witness = result.get("witness", {})
        if witness.get("reason") != "BOUNDARY_NOT_NILPOTENT":
            return False, "Missing BOUNDARY_NOT_NILPOTENT witness reason"
        return True, "Valid OUT_OF_SCOPE verified for non-nilpotent boundary"

    if status != "SOLVED":
        return False, f"Unexpected status: {status}"

    verdict = result.get("verdict")
    try:
        B = {f: parse_rational(target_b_raw.get(f, 0)) for f in faces}
        weights = {f: parse_rational(weights_raw.get(f, 1)) for f in faces}
    except ValueError as e:
        return False, f"REFUSED_FLOAT_DETECTED: {e}"

    if mode == "Q":
        try:
            if verdict == "EXTENDS":
                # Verify d1_cob A == B
                raw_A = result.get("A", {})
                A = {e: parse_rational(raw_A.get(e, 0)) for e in edges}
                for f in faces:
                    cob_f = sum(Fraction(d2_raw.get(f, {}).get(e, 0)) * A[e] for e in edges)
                    if cob_f != B[f]:
                        return False, f"d1 A != B on face {f}: computed {cob_f} != {B[f]}"
                phi2 = parse_rational(result.get("phi2", -1))
                if phi2 != 0:
                    return False, f"EXTENDS certificate reported nonzero phi2={phi2}"
                return True, "Valid EXTENDS certificate verified over Q"

            elif verdict == "OBSTRUCTED":
                # Verify cycle: d2 Z == 0
                raw_cycle = result.get("cycle", {})
                Z = {f: parse_rational(raw_cycle.get(f, 0)) for f in faces}
                for e in edges:
                    bnd_e = sum(Fraction(d2_raw.get(f, {}).get(e, 0)) * Z[f] for f in faces)
                    if bnd_e != 0:
                        return False, f"Cycle Z is not closed on edge {e}: d2 Z = {bnd_e} != 0"

                # Verify pairing <B, Z> != 0
                pairing_actual = sum(B[f] * Z[f] for f in faces)
                claimed_pairing = parse_rational(result.get("pairing", 0))
                if pairing_actual != claimed_pairing or pairing_actual == 0:
                    return (
                        False,
                        f"Pairing mismatch: computed {pairing_actual} != claimed {claimed_pairing}",
                    )

                # Verify dual y: d2 y == 0 and |y_f| <= w_f
                raw_dual = result.get("dual_y", {})
                y = {f: parse_rational(raw_dual.get(f, 0)) for f in faces}
                for e in edges:
                    bnd_e = sum(Fraction(d2_raw.get(f, {}).get(e, 0)) * y[f] for f in faces)
                    if bnd_e != 0:
                        return False, f"Dual y is not closed on edge {e}: d2 y = {bnd_e} != 0"

                for f in faces:
                    if abs(y[f]) > weights[f]:
                        return False, f"Dual y exceeds weight on face {f}: |{y[f]}| > {weights[f]}"

                phi2_dual = sum(B[f] * y[f] for f in faces)
                claimed_phi2 = parse_rational(result.get("phi2", -1))
                if phi2_dual != claimed_phi2 or phi2_dual <= 0:
                    return (
                        False,
                        f"Phi2 mismatch: dual evaluates to {phi2_dual} != claimed {claimed_phi2}",
                    )

                return True, "Valid OBSTRUCTED certificate verified over Q"

            else:
                return False, f"Unknown Q verdict: {verdict}"
        except ValueError as e:
            return False, f"REFUSED_FLOAT_DETECTED: {e}"

    elif mode == "Z":
        if verdict == "EXTENDS_INTEGRAL":
            raw_A = result.get("A", {})
            for e in edges:
                val = raw_A.get(e, "0")
                if "." in str(val) or "/" in str(val):
                    return False, f"Potential A on edge {e} is not integral: {val}"
            A = {e: int(raw_A.get(e, 0)) for e in edges}
            for f in faces:
                cob_f = sum(d2_raw.get(f, {}).get(e, 0) * A[e] for e in edges)
                if cob_f != int(B[f]):
                    return False, f"d1 A != B on face {f}"
            return True, "Valid EXTENDS_INTEGRAL verified"

        elif verdict == "OBSTRUCTED_INTEGRAL":
            modulus = int(result.get("modulus", 0))
            if modulus < 2:
                return False, f"Invalid modulus: {modulus} < 2"
            raw_chain = result.get("chain", {})
            Z = {f: int(raw_chain.get(f, 0)) for f in faces}
            # Verify d2 Z = 0 mod m
            for e in edges:
                bnd_e = sum(d2_raw.get(f, {}).get(e, 0) * Z[f] for f in faces) % modulus
                if bnd_e != 0:
                    return False, f"Chain Z not closed mod {modulus} on edge {e}: {bnd_e}"
            # Verify pairing <B, Z> != 0 mod m
            pair_mod = sum(int(B[f]) * Z[f] for f in faces) % modulus
            claimed_pair_mod = int(result.get("pairing_mod", 0))
            if pair_mod != claimed_pair_mod or pair_mod == 0:
                return (
                    False,
                    f"Pairing mod {modulus} mismatch: actual {pair_mod} != claimed {claimed_pair_mod}",
                )
            return True, "Valid OBSTRUCTED_INTEGRAL verified"

        else:
            return False, f"Unknown Z verdict: {verdict}"

    return False, "Unhandled branch"
