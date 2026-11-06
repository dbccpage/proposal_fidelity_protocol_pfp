"""Checker 2: Combinatorial Fusion & Ring Axiom Verifier.

Independent verification engine for Challenge C037.
Derives fusion rules purely via the truncated Clebsch-Gordan rule for SU(2)_k
and the product of two SU(2) rules at levels p'-2 and p-2 with Kac identification
for Virasoro minimal models. Explicitly audits all three Fusion Ring Axioms:
commutativity, associativity, and vacuum identity.

Completely self-contained. Shares ZERO code with Checker 1.
AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping

# -------------------------------------------------------------------------
# Checker 2 Private Type Guards
# -------------------------------------------------------------------------


def _c2_is_int(val: Any) -> bool:
    """Strict check for int, rejecting bool."""
    return type(val) is int and not isinstance(val, bool)


def _c2_is_integer_str(val: Any) -> bool:
    if type(val) is not str:
        return False
    if "." in val or "e" in val.lower() or "/" in val:
        return False
    s = val.lstrip("-")
    return s.isdigit() and len(s) > 0


def _c2_is_reduced_rational_str(val: Any) -> bool:
    if type(val) is not str:
        return False
    if "." in val or "e" in val.lower():
        return False
    if "/" in val:
        parts = val.split("/")
        if len(parts) != 2:
            return False
        num_s, den_s = parts
        if not _c2_is_integer_str(num_s) or not den_s.isdigit():
            return False
        den = int(den_s)
        if den <= 1:
            return False
        num = int(num_s)
        if math.gcd(abs(num), den) != 1:
            return False
        return True
    return _c2_is_integer_str(val)


def _c2_to_reduced_str(frac: Fraction) -> str:
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def _c2_canonical_kac_label(p: int, p_prime: int, r: int, s: int) -> tuple[int, int]:
    if (s, r) <= (p - s, p_prime - r):
        return (r, s)
    return (p_prime - r, p - s)


# -------------------------------------------------------------------------
# Checker 2 Combinatorial Fusion Rules
# -------------------------------------------------------------------------


def _c2_su2_cg_coeff(k: int, a: int, b: int, c: int) -> int:
    """Truncated Clebsch-Gordan rule for SU(2)_k."""
    if abs(a - b) <= c <= min(a + b, 2 * k - a - b) and (a + b + c) % 2 == 0:
        return 1
    return 0


def _c2_compute_su2_combinatorial(
    k: int,
) -> tuple[str, list[dict[str, Any]], list[list[Any]]]:
    """Computes ground truth for SU(2)_k via combinatorial Clebsch-Gordan rule."""
    c_str = _c2_to_reduced_str(Fraction(3 * k, k + 2))
    primaries = []
    for a in range(k + 1):
        h_frac = Fraction(a * (a + 2), 4 * (k + 2))
        primaries.append({"label": [a], "h": _c2_to_reduced_str(h_frac)})

    fusion = []
    for a in range(k + 1):
        for b in range(a, k + 1):
            for c in range(k + 1):
                coeff = _c2_su2_cg_coeff(k, a, b, c)
                if coeff > 0:
                    fusion.append([[a], [b], [c], coeff])

    return c_str, primaries, fusion


def _c2_compute_minimal_combinatorial(
    p: int, p_prime: int
) -> tuple[str, list[dict[str, Any]], list[list[Any]]]:
    """Computes ground truth for minimal model M(p, p') via product of two SU(2) rules."""
    c_frac = Fraction(1) - Fraction(6 * (p - p_prime) ** 2, p * p_prime)
    c_str = _c2_to_reduced_str(c_frac)

    k1 = p_prime - 2
    k2 = p - 2

    prim_reps = []
    for r in range(1, p_prime):
        for s in range(1, p):
            rep = _c2_canonical_kac_label(p, p_prime, r, s)
            if rep not in prim_reps:
                prim_reps.append(rep)
    prim_reps.sort()

    primaries = []
    for r, s in prim_reps:
        h_frac = Fraction((p * r - p_prime * s) ** 2 - (p - p_prime) ** 2, 4 * p * p_prime)
        primaries.append({"label": [r, s], "h": _c2_to_reduced_str(h_frac)})

    fusion = []
    for i_idx, p1 in enumerate(prim_reps):
        r1, s1 = p1
        a1, b1 = r1 - 1, s1 - 1
        for j_idx in range(i_idx, len(prim_reps)):
            p2 = prim_reps[j_idx]
            r2, s2 = p2
            a2, b2 = r2 - 1, s2 - 1

            counts = {rep: 0 for rep in prim_reps}
            for a3 in range(abs(a1 - a2), min(a1 + a2, 2 * k1 - a1 - a2) + 1, 2):
                r3 = a3 + 1
                for b3 in range(abs(b1 - b2), min(b1 + b2, 2 * k2 - b1 - b2) + 1, 2):
                    s3 = b3 + 1
                    rep = _c2_canonical_kac_label(p, p_prime, r3, s3)
                    counts[rep] += 1

            for p3 in prim_reps:
                if counts[p3] > 0:
                    fusion.append([list(p1), list(p2), list(p3), counts[p3]])

    return c_str, primaries, fusion


# -------------------------------------------------------------------------
# Checker 2 Fusion Ring Axiom Auditor
# -------------------------------------------------------------------------


def _c2_audit_fusion_ring_axioms(
    labels: list[Any],
    fusion_rules: list[list[Any]],
    identity_label: Any,
) -> tuple[bool, str]:
    """Audits the three fusion ring axioms on the candidate fusion table."""
    n = len(labels)
    label_to_idx = {
        tuple(lbl) if isinstance(lbl, list) else lbl: idx for idx, lbl in enumerate(labels)
    }

    id_key = tuple(identity_label) if isinstance(identity_label, list) else identity_label
    if id_key not in label_to_idx:
        return False, f"Identity label {identity_label} not found in primaries"
    id_idx = label_to_idx[id_key]

    # Build full 3D tensor N[a][b][c]
    N = [[[0] * n for _ in range(n)] for _ in range(n)]
    for item in fusion_rules:
        p1, p2, p3, val = item
        k1 = tuple(p1) if isinstance(p1, list) else p1
        k2 = tuple(p2) if isinstance(p2, list) else p2
        k3 = tuple(p3) if isinstance(p3, list) else p3
        if k1 not in label_to_idx or k2 not in label_to_idx or k3 not in label_to_idx:
            return False, f"Fusion rule contains unlisted primary: {item}"
        i1 = label_to_idx[k1]
        i2 = label_to_idx[k2]
        i3 = label_to_idx[k3]
        N[i1][i2][i3] = val
        N[i2][i1][i3] = val  # enforce symmetry for lookup

    # Axiom 1: Commutativity
    for a in range(n):
        for b in range(n):
            for c in range(n):
                if N[a][b][c] != N[b][a][c]:
                    return (
                        False,
                        f"Commutativity violation: N[{labels[a]}][{labels[b]}][{labels[c]}] != N[{labels[b]}][{labels[a]}][{labels[c]}]",
                    )

    # Axiom 3: Identity
    for j in range(n):
        for k in range(n):
            expected = 1 if j == k else 0
            if N[id_idx][j][k] != expected:
                return (
                    False,
                    f"Identity violation: N[0][{labels[j]}][{labels[k]}] = {N[id_idx][j][k]}, expected {expected}",
                )

    # Axiom 2: Associativity (commutation of fusion matrices M_a M_c == M_c M_a)
    for a in range(n):
        for c in range(a + 1, n):
            for b in range(n):
                for d in range(n):
                    lhs = sum(N[a][b][m] * N[m][c][d] for m in range(n))
                    rhs = sum(N[b][c][m] * N[a][m][d] for m in range(n))
                    if lhs != rhs:
                        return (
                            False,
                            f"Associativity violation at ({labels[a]}, {labels[b]}, {labels[c]}, {labels[d]}): {lhs} != {rhs}",
                        )

    return True, "Axioms satisfied"


# -------------------------------------------------------------------------
# Checker 2 Certificate Verifier
# -------------------------------------------------------------------------


def verify_combinatorial_fusion_certificate(
    case: Mapping[str, Any],
    answer: Mapping[str, Any],
) -> tuple[bool, str]:
    """Verifies candidate answer using Checker 2 (combinatorial Clebsch-Gordan pipeline)."""
    if not isinstance(case, Mapping) or not isinstance(answer, Mapping):
        return False, "FAIL (C2): case and answer must be Mappings"

    status = answer.get("status")
    if type(status) is not str or status not in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}:
        return False, f"FAIL (C2): invalid status '{status}'"

    # Anti-bypass: boolean injection guards on case
    for k_field in ("k", "p", "p_prime", "model", "case_id", "id"):
        if k_field in case and isinstance(case[k_field], bool):
            if status != "UNKNOWN":
                return False, "FAIL (C2): boolean injection in case must be refused with UNKNOWN"
            return True, "PASS (C2): boolean injection correctly refused"

    # Schema Whitelist
    answer_keys = set(answer.keys())
    if "id" not in answer_keys and "case_id" not in answer_keys:
        return False, "FAIL (C2): missing mandatory id field"

    if status == "SOLVED":
        allowed = {"id", "case_id", "status", "central_charge", "primaries", "fusion"}
        if not answer_keys.issubset(allowed):
            return (
                False,
                f"FAIL (C2): phantom keys in SOLVED answer: {answer_keys - allowed}",
            )
        if not {"status", "central_charge", "primaries", "fusion"}.issubset(answer_keys):
            return False, "FAIL (C2): missing mandatory SOLVED keys"
    elif status == "OUT_OF_SCOPE":
        allowed = {"id", "case_id", "status", "witness"}
        if not answer_keys.issubset(allowed):
            return (
                False,
                f"FAIL (C2): phantom keys in OUT_OF_SCOPE answer: {answer_keys - allowed}",
            )
        if "witness" not in answer:
            return False, "FAIL (C2): witness missing in OUT_OF_SCOPE answer"
    elif status == "UNKNOWN":
        allowed = {"id", "case_id", "status", "refusal_code", "refusal"}
        if not answer_keys.issubset(allowed):
            return (
                False,
                f"FAIL (C2): phantom keys in UNKNOWN answer: {answer_keys - allowed}",
            )
        if "refusal_code" not in answer and "refusal" not in answer:
            return False, "FAIL (C2): refusal_code missing in UNKNOWN answer"

    model = case.get("model")
    if model not in {"su2", "minimal"}:
        if status != "UNKNOWN":
            return False, "FAIL (C2): invalid model must be refused with UNKNOWN"
        return True, "PASS (C2): invalid model refused"

    if model == "su2":
        k = case.get("k")
        if not _c2_is_int(k):
            if status != "UNKNOWN":
                return False, "FAIL (C2): non-int level must be refused"
            return True, "PASS (C2): non-int level refused"
        if k < 1 or k > 20:
            if status != "UNKNOWN":
                return False, "FAIL (C2): level out of bounds must be refused with UNKNOWN"
            ref = answer.get("refusal_code") or answer.get("refusal")
            if ref != "LEVEL_OUT_OF_BOUNDS":
                return False, f"FAIL (C2): expected LEVEL_OUT_OF_BOUNDS, got '{ref}'"
            return True, "PASS (C2): out-of-bounds level correctly refused"

        if status != "SOLVED":
            return False, f"FAIL (C2): unwarranted refusal on valid SU(2)_{k} case"

        exp_c, exp_prim, exp_fus = _c2_compute_su2_combinatorial(k)

        act_c = answer.get("central_charge")
        if not _c2_is_reduced_rational_str(act_c):
            return False, f"FAIL (C2): central_charge is not reduced rational string: {act_c}"
        if act_c != exp_c:
            return False, f"FAIL (C2): central_charge mismatch: expected '{exp_c}', got '{act_c}'"

        act_prim = answer.get("primaries")
        if not isinstance(act_prim, list) or len(act_prim) != len(exp_prim):
            return (
                False,
                f"FAIL (C2): primaries count mismatch: expected {len(exp_prim)}, got {len(act_prim) if isinstance(act_prim, list) else None}",
            )
        seen_prim_labels = set()
        for idx, (exp_p, act_p) in enumerate(zip(exp_prim, act_prim)):
            if not isinstance(act_p, Mapping):
                return False, f"FAIL (C2): primary at {idx} must be a Mapping"
            if set(act_p.keys()) != {"label", "h"}:
                return False, f"FAIL (C2): primary {idx} has invalid keys: {set(act_p.keys())}"
            lbl = act_p.get("label")
            if not isinstance(lbl, list) or len(lbl) != 1 or not _c2_is_int(lbl[0]):
                return False, f"FAIL (C2): primary {idx} label must be a 1-element integer list"
            tup_lbl = tuple(lbl)
            if tup_lbl in seen_prim_labels:
                return False, f"FAIL (C2): duplicate primary label {lbl}"
            seen_prim_labels.add(tup_lbl)

            if lbl != exp_p["label"]:
                return (
                    False,
                    f"FAIL (C2): primary {idx} label mismatch: expected {exp_p['label']}, got {lbl}",
                )
            h_val = act_p.get("h")
            if not _c2_is_reduced_rational_str(h_val):
                return False, f"FAIL (C2): primary {idx} h is not reduced rational string: {h_val}"
            if h_val != exp_p["h"]:
                return (
                    False,
                    f"FAIL (C2): primary {idx} h mismatch: expected '{exp_p['h']}', got '{h_val}'",
                )

        act_fus = answer.get("fusion")
        if not isinstance(act_fus, list):
            return False, "FAIL (C2): fusion must be a list"
        if len(act_fus) != len(exp_fus):
            return (
                False,
                f"FAIL (C2): fusion rules count mismatch: expected {len(exp_fus)}, got {len(act_fus)}",
            )

        def _to_su2_tuple(item: list[Any]) -> tuple:
            return (tuple(item[0]), tuple(item[1]), tuple(item[2]), item[3])

        exp_fus_set = {_to_su2_tuple(item) for item in exp_fus}
        act_fus_set = set()
        for idx, item in enumerate(act_fus):
            if not isinstance(item, list) or len(item) != 4:
                return False, f"FAIL (C2): fusion rule at {idx} must be a 4-element list"
            p1, p2, p3, n = item
            if (
                not (isinstance(p1, list) and len(p1) == 1 and _c2_is_int(p1[0]))
                or not (isinstance(p2, list) and len(p2) == 1 and _c2_is_int(p2[0]))
                or not (isinstance(p3, list) and len(p3) == 1 and _c2_is_int(p3[0]))
                or not _c2_is_int(n)
            ):
                return False, "FAIL (C2): fusion rule elements must be integer lists and int coeff"
            if p1[0] > p2[0]:
                return (
                    False,
                    f"FAIL (C2): fusion rule [{p1}, {p2}, {p3}, {n}] violates canonical ordering a <= b",
                )
            if n <= 0:
                return False, "FAIL (C2): fusion coefficient must be strictly positive"
            tup = (tuple(p1), tuple(p2), tuple(p3), n)
            if tup in act_fus_set:
                return False, f"FAIL (C2): duplicate fusion rule: {item}"
            act_fus_set.add(tup)

        if act_fus_set != exp_fus_set:
            diff_missing = exp_fus_set - act_fus_set
            diff_spurious = act_fus_set - exp_fus_set
            return (
                False,
                f"FAIL (C2): fusion mismatch. Missing: {diff_missing}, Spurious: {diff_spurious}",
            )

        # Audit Ring Axioms
        labels = [p["label"] for p in act_prim]
        ok_axioms, msg_axioms = _c2_audit_fusion_ring_axioms(labels, act_fus, [0])
        if not ok_axioms:
            return False, f"FAIL (C2): Fusion ring axiom violation: {msg_axioms}"

        return True, "PASS (C2): valid SU(2)_k combinatorial certificate"

    elif model == "minimal":
        p = case.get("p")
        p_prime = case.get("p_prime")
        if not (_c2_is_int(p) and _c2_is_int(p_prime)):
            if status != "UNKNOWN":
                return False, "FAIL (C2): non-int p/p_prime must be refused"
            return True, "PASS (C2): non-int parameters refused"

        if p_prime < 2:
            if status != "OUT_OF_SCOPE":
                return False, "FAIL (C2): p_prime < 2 must be refused with OUT_OF_SCOPE"
            wit = answer.get("witness")
            if not isinstance(wit, Mapping) or wit.get("kind") != "invalid_p_prime":
                return False, f"FAIL (C2): expected invalid_p_prime witness: {wit}"
            return True, "PASS (C2): valid OUT_OF_SCOPE invalid_p_prime witness"

        gcd_val = math.gcd(p, p_prime)
        if gcd_val != 1:
            if status != "OUT_OF_SCOPE":
                return False, "FAIL (C2): non-coprime (p, p') must be refused with OUT_OF_SCOPE"
            wit = answer.get("witness")
            if not isinstance(wit, Mapping):
                return False, "FAIL (C2): witness must be a Mapping"
            if wit.get("kind") != "not_coprime" or wit.get("gcd") != gcd_val:
                return False, f"FAIL (C2): invalid not_coprime witness: {wit}"
            return True, "PASS (C2): valid OUT_OF_SCOPE witness"

        if p <= p_prime or p > 13:
            if status != "UNKNOWN":
                return (
                    False,
                    f"FAIL (C2): p={p}, p_prime={p_prime} out of bounds must be refused with UNKNOWN",
                )
            ref = answer.get("refusal_code") or answer.get("refusal")
            if ref not in ("LEVEL_OUT_OF_BOUNDS", "P_OUT_OF_BOUNDS"):
                return False, f"FAIL (C2): expected LEVEL_OUT_OF_BOUNDS, got '{ref}'"
            return True, "PASS (C2): parameters out of bounds correctly refused"

        if status != "SOLVED":
            return False, f"FAIL (C2): unwarranted refusal on valid minimal model M({p}, {p_prime})"

        exp_c, exp_prim, exp_fus = _c2_compute_minimal_combinatorial(p, p_prime)

        act_c = answer.get("central_charge")
        if not _c2_is_reduced_rational_str(act_c):
            return False, f"FAIL (C2): central_charge is not reduced rational string: {act_c}"
        if act_c != exp_c:
            return False, f"FAIL (C2): central_charge mismatch: expected '{exp_c}', got '{act_c}'"

        act_prim = answer.get("primaries")
        if not isinstance(act_prim, list) or len(act_prim) != len(exp_prim):
            return (
                False,
                f"FAIL (C2): primaries count mismatch: expected {len(exp_prim)}, got {len(act_prim) if isinstance(act_prim, list) else None}",
            )

        seen_labels = set()
        for idx, (exp_p, act_p) in enumerate(zip(exp_prim, act_prim)):
            if not isinstance(act_p, Mapping):
                return False, f"FAIL (C2): primary at {idx} must be a Mapping"
            if set(act_p.keys()) != {"label", "h"}:
                return False, f"FAIL (C2): primary {idx} has invalid keys: {set(act_p.keys())}"
            lbl = act_p.get("label")
            if not (
                isinstance(lbl, list)
                and len(lbl) == 2
                and _c2_is_int(lbl[0])
                and _c2_is_int(lbl[1])
            ):
                return False, f"FAIL (C2): primary {idx} label must be a 2-element integer list"
            r, s = lbl
            rep = _c2_canonical_kac_label(p, p_prime, r, s)
            if (r, s) != rep:
                return (
                    False,
                    f"FAIL (C2): primary label [{r}, {s}] is not canonical representative (expected [{rep[0]}, {rep[1]}])",
                )
            if tuple(lbl) in seen_labels:
                return False, f"FAIL (C2): duplicate primary label [{r}, {s}]"
            seen_labels.add(tuple(lbl))

            if lbl != exp_p["label"]:
                return (
                    False,
                    f"FAIL (C2): primary {idx} label mismatch: expected {exp_p['label']}, got {lbl}",
                )
            h_val = act_p.get("h")
            if not _c2_is_reduced_rational_str(h_val):
                return False, f"FAIL (C2): primary {idx} h is not reduced rational string: {h_val}"
            if h_val != exp_p["h"]:
                return (
                    False,
                    f"FAIL (C2): primary {idx} h mismatch: expected '{exp_p['h']}', got '{h_val}'",
                )

        act_fus = answer.get("fusion")
        if not isinstance(act_fus, list):
            return False, "FAIL (C2): fusion must be a list"
        if len(act_fus) != len(exp_fus):
            return (
                False,
                f"FAIL (C2): fusion rules count mismatch: expected {len(exp_fus)}, got {len(act_fus)}",
            )

        def _to_tuple_fus(item: list[Any]) -> tuple:
            return (tuple(item[0]), tuple(item[1]), tuple(item[2]), item[3])

        exp_fus_set = {_to_tuple_fus(item) for item in exp_fus}
        act_fus_set = set()
        for idx, item in enumerate(act_fus):
            if not isinstance(item, list) or len(item) != 4:
                return False, f"FAIL (C2): fusion rule at {idx} must be a 4-element list"
            p1, p2, p3, n = item
            if not (
                isinstance(p1, list)
                and len(p1) == 2
                and _c2_is_int(p1[0])
                and _c2_is_int(p1[1])
                and isinstance(p2, list)
                and len(p2) == 2
                and _c2_is_int(p2[0])
                and _c2_is_int(p2[1])
                and isinstance(p3, list)
                and len(p3) == 2
                and _c2_is_int(p3[0])
                and _c2_is_int(p3[1])
                and _c2_is_int(n)
            ):
                return False, f"FAIL (C2): malformed fusion rule structure: {item}"
            if p1 > p2:
                return (
                    False,
                    f"FAIL (C2): fusion rule violates canonical ordering {p1} <= {p2}",
                )
            if n <= 0:
                return False, "FAIL (C2): fusion coefficient must be strictly positive"
            tup = (tuple(p1), tuple(p2), tuple(p3), n)
            if tup in act_fus_set:
                return False, f"FAIL (C2): duplicate fusion entry {item}"
            act_fus_set.add(tup)

        if act_fus_set != exp_fus_set:
            diff_missing = exp_fus_set - act_fus_set
            diff_spurious = act_fus_set - exp_fus_set
            return (
                False,
                f"FAIL (C2): fusion mismatch. Missing: {diff_missing}, Spurious: {diff_spurious}",
            )

        # Audit Ring Axioms
        labels = [p["label"] for p in act_prim]
        ok_axioms, msg_axioms = _c2_audit_fusion_ring_axioms(labels, act_fus, [1, 1])
        if not ok_axioms:
            return False, f"FAIL (C2): Fusion ring axiom violation: {msg_axioms}"

        return True, "PASS (C2): valid minimal model combinatorial certificate"

    return False, "FAIL (C2): unreachable model branch"


# Alias for backward compatibility
verify_combinatorial_fusion_checker = verify_combinatorial_fusion_certificate
