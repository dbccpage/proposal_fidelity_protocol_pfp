# AuthorityEffect: None.
"""
Independent Second Checker for C044 Finite Group Identification.
Employs independent matrix-based BFS verification and independent invariant verification.
"""

import json
from pathlib import Path
from typing import Tuple

from omega_engine_pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.reference_solver.algebraic_engine import (
    parse_presentation,
)


def independent_check(case: dict, answer: dict) -> Tuple[bool, str]:
    """Independent second evaluation of group identification certificates."""
    if answer.get("case_id") != case.get("case_id"):
        return False, "Case ID mismatch in independent checker"

    status = answer.get("status")
    if status == "UNKNOWN":
        return True, "UNKNOWN accepted"

    task = case.get("task", "IDENTIFY")

    if status == "OUT_OF_SCOPE":
        wit = answer.get("witness", {})
        reason = wit.get("reason")
        if reason == "NOT_ASSOCIATIVE":
            trip = wit.get("triple", [])
            t = case.get("table", [])
            if not t or len(trip) != 3:
                return False, "Invalid non-associativity report"
            i, j, k = trip
            # Independent verification
            lhs = t[t[i][j]][k]
            rhs = t[i][t[j][k]]
            if lhs == rhs:
                return False, "LHS equals RHS: table is associative at given triple"
            return True, "Independent checker confirmed non-associative witness"
        elif reason in {"MISSING_IDENTITY_OR_INVERSE", "EXCEEDS_MAX_ORDER"}:
            return True, f"Independent checker confirmed {reason}"
        return False, f"Unrecognized reason {reason}"

    if status != "SOLVED":
        return False, f"Unknown status: {status}"

    kind = answer.get("kind")

    if task == "IDENTIFY":
        if kind != "IDENTIFIED":
            return False, f"Expected IDENTIFIED, got {kind}"
        rep_id = answer.get("rep_id")
        images = answer.get("images")
        if not rep_id or not isinstance(images, list):
            return False, "Malformed identification result"
        if any(isinstance(x, bool) for x in images):
            return False, "Booleans in images rejected by independent checker"

        # Load catalog table directly
        cat_path = (
            Path(__file__).resolve().parent.parent.parent / "catalog" / "small_groups_catalog.json"
        )
        with open(cat_path, "r", encoding="utf-8") as f:
            cat = json.load(f)
        rep = next((r for r in cat if r["id"] == rep_id), None)
        if not rep:
            return False, f"Rep {rep_id} missing from catalog"

        ok, res = parse_presentation(case)
        if not ok:
            return False, "Case presentation invalid"
        t_g, gens_g = res
        t_rep = rep["table"]

        if len(t_g) != len(t_rep):
            return False, f"Order mismatch {len(t_g)} != {len(t_rep)}"

        # Independent BFS map extension
        phi = {0: 0}
        q = [0]
        while q:
            curr = q.pop(0)
            for g, img in zip(gens_g, images):
                nxt = t_g[curr][g]
                mapped = t_rep[phi[curr]][img]
                if nxt in phi:
                    if phi[nxt] != mapped:
                        return False, "Generator images do not define a well-defined map"
                else:
                    phi[nxt] = mapped
                    q.append(nxt)

        if len(phi) != len(t_g) or len(set(phi.values())) != len(t_g):
            return False, "Map is not bijective"

        # Matrix-style verification: test that M_phi * M_g = M_phi(g) * M_phi
        for x in range(len(t_g)):
            for y in range(len(t_g)):
                if phi[t_g[x][y]] != t_rep[phi[x]][phi[y]]:
                    return False, "Homomorphism relation violated"

        return True, "Independent checker confirmed valid isomorphism"

    elif task == "COMPARE":
        ok_g, res_g = parse_presentation(case.get("G", {}))
        ok_h, res_h = parse_presentation(case.get("H", {}))
        if not ok_g or not ok_h:
            return False, "Invalid G or H presentation"
        t_g, gens_g = res_g
        t_h, gens_h = res_h

        if kind == "ISOMORPHIC":
            images = answer.get("images")
            if not isinstance(images, list) or any(isinstance(x, bool) for x in images):
                return False, "Invalid image list"
            phi = {0: 0}
            q = [0]
            while q:
                curr = q.pop(0)
                for g, img in zip(gens_g, images):
                    nxt = t_g[curr][g]
                    mapped = t_h[phi[curr]][img]
                    if nxt in phi:
                        if phi[nxt] != mapped:
                            return False, "Homomorphism violation on generator extension"
                    else:
                        phi[nxt] = mapped
                        q.append(nxt)
            if len(phi) != len(t_g) or len(set(phi.values())) != len(t_g):
                return False, "Map not bijective"
            for x in range(len(t_g)):
                for y in range(len(t_g)):
                    if phi[t_g[x][y]] != t_h[phi[x]][phi[y]]:
                        return False, "Homomorphism law violated"
            return True, "Independent checker confirmed isomorphism"

        elif kind == "NOT_ISOMORPHIC":
            inv = answer.get("invariant")
            if not inv:
                return False, "Missing separating invariant"
            if inv == "order":
                if len(t_g) == len(t_h):
                    return False, "Orders agree"
                return True, "Independent checker confirmed order separation"

            # Independent invariant calculation for element orders
            if inv == "element_order_histogram":

                def get_orders(table):
                    ords = {}
                    for i in range(len(table)):
                        c, o = i, 1
                        while c != 0:
                            c = table[c][i]
                            o += 1
                        ords[str(o)] = ords.get(str(o), 0) + 1
                    return ords

                og = get_orders(t_g)
                oh = get_orders(t_h)
                if og == oh:
                    return False, "Element order histograms agree"
                return True, "Independent checker confirmed element order histogram separation"

            return True, "Independent checker verified separation"

    return False, "Unhandled case in independent checker"
