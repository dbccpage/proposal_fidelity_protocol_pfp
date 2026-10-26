# AuthorityEffect: None.
"""
Exact Checker for C044 Finite Group Identification.
Recomputes invariants, checks homomorphism laws, and verifies out-of-scope witnesses.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from omega_engine_pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.reference_solver.algebraic_engine import (
    parse_presentation,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.reference_solver.invariants import (
    compute_all_invariants,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.reference_solver.isomorphism_search import (
    extend_and_verify_isomorphism,
)

_CATALOG_MAP: Optional[Dict[str, Dict[str, Any]]] = None


def get_catalog_map() -> Dict[str, Dict[str, Any]]:
    global _CATALOG_MAP
    if _CATALOG_MAP is None:
        cat_path = (
            Path(__file__).resolve().parent.parent.parent / "catalog" / "small_groups_catalog.json"
        )
        with open(cat_path, "r", encoding="utf-8") as f:
            cat = json.load(f)
        _CATALOG_MAP = {f"{r['id'][0]}_{r['id'][1]}": r for r in cat}
    return _CATALOG_MAP


def check_exact(case: dict, answer: dict) -> Tuple[bool, str]:
    if answer.get("case_id") != case.get("case_id"):
        return False, f"Case ID mismatch: {answer.get('case_id')} vs {case.get('case_id')}"

    status = answer.get("status")
    if status == "UNKNOWN":
        return True, "UNKNOWN accepted"

    task = case.get("task", "IDENTIFY")

    if status == "OUT_OF_SCOPE":
        witness = answer.get("witness", {})
        reason = witness.get("reason")
        if reason == "NOT_ASSOCIATIVE":
            triple = witness.get("triple", [])
            if len(triple) != 3:
                return False, "Malformed NOT_ASSOCIATIVE witness"
            # Verify non-associativity directly
            table = case.get("table", [])
            if not table:
                return False, "NOT_ASSOCIATIVE claimed but case has no table"
            i, j, k = triple
            if table[table[i][j]][k] == table[i][table[j][k]]:
                return False, f"Triple {triple} is actually associative"
            return True, "Valid NOT_ASSOCIATIVE witness"

        elif reason == "MISSING_IDENTITY_OR_INVERSE":
            return True, "Valid MISSING_IDENTITY_OR_INVERSE witness"

        elif reason == "EXCEEDS_MAX_ORDER":
            order = witness.get("order", 0)
            if order <= 64:
                return False, f"Order {order} does not exceed max order 64"
            return True, "Valid EXCEEDS_MAX_ORDER witness"

        return False, f"Unknown OUT_OF_SCOPE reason: {reason}"

    if status != "SOLVED":
        return False, f"Invalid status: {status}"

    kind = answer.get("kind")

    if task == "IDENTIFY":
        if kind != "IDENTIFIED":
            return False, f"Expected IDENTIFIED, got {kind}"
        rep_id = answer.get("rep_id")
        if not rep_id or len(rep_id) != 2:
            return False, f"Invalid rep_id format: {rep_id}"
        images = answer.get("images")
        if not isinstance(images, list):
            return False, "Images must be a list of integer element indices"
        # Check that images are not booleans
        if any(isinstance(x, bool) for x in images):
            return False, "Images cannot be Booleans"

        cat_map = get_catalog_map()
        key = f"{rep_id[0]}_{rep_id[1]}"
        if key not in cat_map:
            return False, f"Representative ID {rep_id} not found in catalog"
        rep = cat_map[key]

        ok, res = parse_presentation(case)
        if not ok:
            return False, f"Input presentation is invalid: {res}"
        t_g, gens_g = res

        if len(t_g) != rep["order"]:
            return False, f"Order mismatch: group has {len(t_g)}, rep has {rep['order']}"

        # Verify images extend to isomorphism
        ok_iso, phi = extend_and_verify_isomorphism(t_g, gens_g, rep["table"], images)
        if not ok_iso or phi is None:
            return False, f"Images {images} do not extend to a valid isomorphism to rep {rep_id}"

        return True, f"Verified isomorphism to {rep['name']} {rep_id}"

    elif task == "COMPARE":
        g_pres = case.get("G", {})
        h_pres = case.get("H", {})
        ok_g, res_g = parse_presentation(g_pres)
        if not ok_g:
            return False, f"G presentation invalid: {res_g}"
        ok_h, res_h = parse_presentation(h_pres)
        if not ok_h:
            return False, f"H presentation invalid: {res_h}"
        t_g, gens_g = res_g
        t_h, gens_h = res_h

        if kind == "ISOMORPHIC":
            images = answer.get("images")
            if not isinstance(images, list):
                return False, "Images must be a list"
            if any(isinstance(x, bool) for x in images):
                return False, "Images cannot be Booleans"
            ok_iso, phi = extend_and_verify_isomorphism(t_g, gens_g, t_h, images)
            if not ok_iso or phi is None:
                return False, f"Claimed isomorphism images {images} invalid"
            return True, "Verified isomorphism between G and H"

        elif kind == "NOT_ISOMORPHIC":
            inv_name = answer.get("invariant")
            if not inv_name:
                return False, "Missing separating invariant"

            if inv_name == "order":
                if len(t_g) == len(t_h):
                    return (
                        False,
                        f"Orders agree ({len(t_g)}) but order claimed as separating invariant",
                    )
                return True, f"Verified order separation: {len(t_g)} != {len(t_h)}"

            inv_g = compute_all_invariants(t_g)
            inv_h = compute_all_invariants(t_h)

            if inv_name not in inv_g:
                return False, f"Unknown invariant name: {inv_name}"

            val_g = inv_g[inv_name]
            val_h = inv_h[inv_name]

            if val_g == val_h:
                return False, f"Invariant {inv_name} actually agrees on both groups: {val_g}"

            return True, f"Verified separation by {inv_name}: {val_g} != {val_h}"

        return False, f"Unknown COMPARE kind: {kind}"

    return False, f"Unknown task: {task}"
