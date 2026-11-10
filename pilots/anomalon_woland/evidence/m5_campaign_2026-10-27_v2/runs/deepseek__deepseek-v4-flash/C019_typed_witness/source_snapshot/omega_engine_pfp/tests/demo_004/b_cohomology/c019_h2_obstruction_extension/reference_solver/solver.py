"""Solver for C019: Degree-2 Obstructions and Cochain Extension."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from .ddc_tracer import DdcOperationalTracer
from .exact_linalg import format_rational, nullspace_rational, parse_rational, solve_linear_rational


def solve(case: dict[str, Any]) -> tuple[dict[str, Any], DdcOperationalTracer]:
    tracer = DdcOperationalTracer(challenge_id=case.get("id", "c019"))
    tracer.record("C", "INIT", "Parsed 2-complex case", case_id=case.get("id"))

    faces = list(case.get("faces", []))
    edges = list(case.get("edges", []))
    vertices = list(case.get("vertices", []))

    d2_raw = case.get("d2", {})  # face -> dict of edges: coeff (d2 is boundary d_2: C_2 -> C_1)
    d1_raw = case.get("d1", {})  # edge -> dict of vertices: coeff (d1 is boundary d_1: C_1 -> C_0)
    target_b_raw = case.get("B", {})
    weights_raw = case.get("weights", {})
    mode = case.get("mode", "Q")

    # 1. Verify Nilpotency d_1 d_2 = 0
    tracer.record("R", "VERIFY_NILPOTENT", "Checking d1 * d2 == 0")
    for f in faces:
        boundary_f = d2_raw.get(f, {})
        for v in vertices:
            # sum over e: d2(f, e) * d1(e, v)
            comp = 0
            for e, coeff_fe in boundary_f.items():
                coeff_ev = d1_raw.get(e, {}).get(v, 0)
                comp += coeff_fe * coeff_ev
            if comp != 0:
                tracer.record(
                    "M", "REFUSAL", "Boundary not nilpotent", face=f, vertex=v, residual=comp
                )
                res = {
                    "id": case.get("id", "unknown"),
                    "status": "OUT_OF_SCOPE",
                    "witness": {"reason": "BOUNDARY_NOT_NILPOTENT", "face": f},
                }
                tracer.record("T", "TERMINAL", "Terminated with OUT_OF_SCOPE")
                return res, tracer

    # Parse target B and weights
    B: dict[str, Fraction] = {}
    weights: dict[str, Fraction] = {}
    for f in faces:
        B[f] = parse_rational(target_b_raw.get(f, 0))
        weights[f] = parse_rational(weights_raw.get(f, 1))

    # Build matrix for d_2: rows are edges, cols are faces
    # d_2(f) = sum_e M_{e, f} e
    # Coboundary d_1: C^1 -> C^2 is transpose: (d_1 A)_f = sum_e M_{e, f} A_e
    M_d2: list[list[Fraction]] = []
    for e in edges:
        row = []
        for f in faces:
            row.append(Fraction(d2_raw.get(f, {}).get(e, 0)))
        M_d2.append(row)

    # Coboundary matrix d1_cob: rows are faces, cols are edges
    # (d1_cob A)_f = sum_e M_{e, f} A_e
    M_d1_cob: list[list[Fraction]] = []
    for f in faces:
        row = []
        for e in edges:
            row.append(Fraction(d2_raw.get(f, {}).get(e, 0)))
        M_d1_cob.append(row)

    # 2. Check Extension over Q: d1_cob A = B
    b_vec = [B[f] for f in faces]
    sol_A = solve_linear_rational(M_d1_cob, b_vec)

    if mode == "Q":
        if sol_A is not None:
            # Extends over Q!
            tracer.record("E", "EXTENDS_Q", "Found exact 1-cochain potential", num_edges=len(edges))
            a_dict = {
                edges[i]: format_rational(sol_A[i]) for i in range(len(edges)) if sol_A[i] != 0
            }
            res = {
                "id": case.get("id", "unknown"),
                "status": "SOLVED",
                "mode": "Q",
                "verdict": "EXTENDS",
                "A": a_dict,
                "phi2": "0",
            }
            tracer.record("T", "TERMINAL", "Terminated with EXTENDS")
            return res, tracer

        # Obstructed over Q: find 2-cycle Z in ker(d_2) with <B, Z> != 0
        tracer.record("Lambda", "KERNEL_SEARCH", "Computing 2-cycles in ker(d2)")
        cycles = nullspace_rational(M_d2)
        obstructing_cycle = None
        pairing_val = Fraction(0)
        for c_vec in cycles:
            val = sum(c_vec[i] * B[faces[i]] for i in range(len(faces)))
            if val != 0:
                obstructing_cycle = c_vec
                pairing_val = val
                break

        # Compute exact Phi_2 dual witness y
        # In a 2-complex, dual y in ker(d_2) with |y_f| <= w_f maximizing <B, y>
        # For single cavity or independent cavities: scale cycle to max |y_f| <= w_f
        # y = alpha * Z where |alpha * Z_f| <= w_f
        if obstructing_cycle is not None:
            max_ratio = max(
                abs(obstructing_cycle[i]) / weights[faces[i]]
                for i in range(len(faces))
                if obstructing_cycle[i] != 0
            )
            alpha = (Fraction(1) if pairing_val > 0 else Fraction(-1)) / max_ratio
            dual_y = [obstructing_cycle[i] * alpha for i in range(len(faces))]
            phi2_val = sum(dual_y[i] * B[faces[i]] for i in range(len(faces)))
        else:
            phi2_val = Fraction(0)
            dual_y = [Fraction(0)] * len(faces)
            obstructing_cycle = [Fraction(0)] * len(faces)

        cycle_dict = {
            faces[i]: format_rational(obstructing_cycle[i])
            for i in range(len(faces))
            if obstructing_cycle[i] != 0
        }
        dual_dict = {
            faces[i]: format_rational(dual_y[i]) for i in range(len(faces)) if dual_y[i] != 0
        }

        tracer.record(
            "D",
            "OBSTRUCTED_Q",
            "Found H2 obstruction",
            phi2=str(phi2_val),
            pairing=str(pairing_val),
        )
        res = {
            "id": case.get("id", "unknown"),
            "status": "SOLVED",
            "mode": "Q",
            "verdict": "OBSTRUCTED",
            "cycle": cycle_dict,
            "pairing": format_rational(pairing_val),
            "phi2": format_rational(phi2_val),
            "primal_A": {},
            "dual_y": dual_dict,
        }
        tracer.record("T", "TERMINAL", "Terminated with OBSTRUCTED")
        return res, tracer

    elif mode == "Z":
        # Mode Z: check if integral solution exists
        is_integral = False
        if sol_A is not None and all(x.denominator == 1 for x in sol_A):
            is_integral = True

        if is_integral:
            a_dict = {edges[i]: str(sol_A[i].numerator) for i in range(len(edges)) if sol_A[i] != 0}
            res = {
                "id": case.get("id", "unknown"),
                "status": "SOLVED",
                "mode": "Z",
                "verdict": "EXTENDS_INTEGRAL",
                "A": a_dict,
                "phi2": "0",
            }
            tracer.record("T", "TERMINAL", "Terminated with EXTENDS_INTEGRAL")
            return res, tracer

        # Torsion / integral obstruction: find modulus m and chain Z such that d2 Z = 0 mod m and <B, Z> != 0 mod m
        tracer.record("Lambda", "TORSION_SEARCH", "Searching for modular obstruction (m >= 2)")
        # Check standard moduli 2, 3, 5
        found_mod = None
        for m in (2, 3, 5, 7):
            # Check integer cycles mod m
            # We look for integer chain Z in {0, 1, ..., m-1}^F
            # With b2 small or torsion shell: try RP2 standard cycle or nullspace mod m
            # For 2-complex, search simple chains
            # E.g. Z = (1, 1, ...) mod 2
            # Check candidate chains:
            candidates = [
                [1] * len(faces),
                [1 if i % 2 == 0 else -1 for i in range(len(faces))],
            ]
            for c_cand in candidates:
                # Check d2 * c_cand mod m
                d2_cand = [
                    sum(int(M_d2[e_idx][f_idx]) * c_cand[f_idx] for f_idx in range(len(faces))) % m
                    for e_idx in range(len(edges))
                ]
                if all(val == 0 for val in d2_cand):
                    # It is a cycle mod m! Check pairing
                    pair = sum(int(B[faces[i]]) * c_cand[i] for i in range(len(faces))) % m
                    if pair != 0:
                        found_mod = (m, c_cand, pair)
                        break
            if found_mod is not None:
                break

        if found_mod is not None:
            m_val, z_cand, pair_val = found_mod
            chain_dict = {faces[i]: str(z_cand[i]) for i in range(len(faces)) if z_cand[i] != 0}
            res = {
                "id": case.get("id", "unknown"),
                "status": "SOLVED",
                "mode": "Z",
                "verdict": "OBSTRUCTED_INTEGRAL",
                "modulus": str(m_val),
                "chain": chain_dict,
                "pairing_mod": str(pair_val),
            }
            tracer.record("T", "TERMINAL", "Terminated with OBSTRUCTED_INTEGRAL")
            return res, tracer

        # Fallback if no simple modular cycle: return refusal
        res = {
            "id": case.get("id", "unknown"),
            "status": "UNKNOWN",
            "refusal": "TORSION_UNCERTIFIED",
        }
        tracer.record("T", "TERMINAL", "Terminated with UNKNOWN")
        return res, tracer

    else:
        raise ValueError(f"Unknown mode: {mode}")
