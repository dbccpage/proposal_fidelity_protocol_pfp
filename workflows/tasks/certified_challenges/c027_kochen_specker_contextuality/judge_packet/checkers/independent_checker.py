# AuthorityEffect: None.
"""
Independent Checker for C027: Kochen-Specker Contextuality.

Implements an independent verification path:
- Independent dot product evaluation over Q(sqrt(2))
- Independent maximal clique search for contexts
- Independent colouring/parity verification and bounded exhaustive refutation

Non-parity refutations above the fixed enumeration bound are unavailable,
not accepted proofs or mathematical refusals. Historical non-SOLVED input
refusals retain their existing exact-checker delegation.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Set, Tuple

from .exact_checker import verify_exact
from .schema_guard import validate_certificate


MAX_ENUMERATION_RAYS = 20


class IndependentVerificationUnavailable(RuntimeError):
    """The host cannot independently verify this refutation within its bound."""

    code = "C027_INDEPENDENT_ENUMERATION_UNAVAILABLE"

    def __init__(self, merged_rays: int) -> None:
        self.merged_rays = merged_rays
        self.limit = MAX_ENUMERATION_RAYS
        super().__init__(f"{self.code}: merged_rays={merged_rays} limit={self.limit}")


def _independent_dot(v1: List[List[Any]], v2: List[List[Any]]) -> Tuple[Fraction, Fraction]:
    """Computes dot product (a + b*sqrt(2)) for two vectors."""
    sum_a = Fraction(0, 1)
    sum_b = Fraction(0, 1)
    for c1, c2 in zip(v1, v2):
        a1, b1 = Fraction(c1[0]), Fraction(c1[1])
        a2, b2 = Fraction(c2[0]), Fraction(c2[1])
        # (a1 + b1*s)(a2 + b2*s) = (a1*a2 + 2*b1*b2) + (a1*b2 + b1*a2)*s
        sum_a += a1 * a2 + Fraction(2, 1) * b1 * b2
        sum_b += a1 * b2 + b1 * a2
    return sum_a, sum_b


def verify_independent(
    case: Dict[str, Any], answer: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    schema_error = validate_certificate(case, answer)
    if schema_error:
        return False, schema_error, {}
    cid = case.get("case_id")
    dimension = case.get("dimension")
    raw_vectors = case.get("vectors")

    if answer.get("status") != "SOLVED":
        return verify_exact(case, answer)

    details: Dict[str, Any] = {"case_id": cid}

    if not isinstance(raw_vectors, list) or len(raw_vectors) > 60 or dimension not in (3, 4):
        # Match expected refusal status
        status = answer.get("status")
        if status in ("OUT_OF_SCOPE", "UNKNOWN"):
            return True, "Independent refusal confirmed", details
        return False, f"Expected refusal, got {status}", details

    # Check zero vectors
    for idx, vec in enumerate(raw_vectors):
        if not isinstance(vec, list) or len(vec) != dimension:
            return answer.get("status") == "OUT_OF_SCOPE", "Vector dimension mismatch", details
        if all(Fraction(c[0]) == 0 and Fraction(c[1]) == 0 for c in vec):
            if answer.get("status") == "OUT_OF_SCOPE":
                return True, f"Independent zero vector confirmed at index {idx}", details
            return False, "Expected OUT_OF_SCOPE for zero vector", details

    if answer.get("status") != "SOLVED":
        return False, f"Expected SOLVED, got {answer.get('status')}", details

    # Merge parallel vectors independently
    norm_rays: List[List[List[Fraction]]] = []
    ray_map: List[int] = []

    for vec in raw_vectors:
        # Find first non-zero coordinate
        piv = None
        for c in vec:
            a, b = Fraction(c[0]), Fraction(c[1])
            if a != 0 or b != 0:
                piv = (a, b)
                break
        if piv is None:
            continue

        # Invert pivot (a + b*s)^(-1) = (a - b*s) / (a^2 - 2*b^2)
        pa, pb = piv
        denom = pa * pa - Fraction(2, 1) * pb * pb
        inv_a = pa / denom
        inv_b = -pb / denom

        canon = []
        for c in vec:
            ca, cb = Fraction(c[0]), Fraction(c[1])
            ra = ca * inv_a + Fraction(2, 1) * cb * inv_b
            rb = ca * inv_b + cb * inv_a
            canon.append((ra, rb))

        # Check existing
        found_id = None
        for rid, ex in enumerate(norm_rays):
            if all(ex[k] == canon[k] for k in range(dimension)):
                found_id = rid
                break

        if found_id is not None:
            ray_map.append(found_id)
        else:
            new_id = len(norm_rays)
            norm_rays.append(canon)
            ray_map.append(new_id)

    # Build orthogonality graph
    n_rays = len(norm_rays)
    adj: List[Set[int]] = [set() for _ in range(n_rays)]
    for i in range(n_rays):
        for j in range(i + 1, n_rays):
            da, db = _independent_dot(norm_rays[i], norm_rays[j])
            if da == 0 and db == 0:
                adj[i].add(j)
                adj[j].add(i)

    # Enumerate contexts
    contexts: List[List[int]] = []
    if dimension == 3:
        for i in range(n_rays):
            for j in sorted(adj[i]):
                if j <= i:
                    continue
                for k in sorted(adj[i].intersection(adj[j])):
                    if k > j:
                        contexts.append([i, j, k])
    elif dimension == 4:
        for i in range(n_rays):
            for j in sorted(adj[i]):
                if j <= i:
                    continue
                common_ij = adj[i].intersection(adj[j])
                for k in sorted(common_ij):
                    if k <= j:
                        continue
                    for l in sorted(common_ij.intersection(adj[k])):
                        if l > k:
                            contexts.append([i, j, k, l])

    is_colourable = answer.get("colourable")
    if is_colourable:
        colouring = answer.get("colouring")
        if not isinstance(colouring, list):
            return False, "Independent checker: colouring is not a list", details

        if len(colouring) == n_rays:
            c_rays = colouring
        elif len(colouring) == len(raw_vectors):
            c_rays = [0] * n_rays
            for inp_i, rid in enumerate(ray_map):
                c_rays[rid] = colouring[inp_i]
        else:
            return False, "Independent checker: colouring length mismatch", details

        # Verify orthogonality
        for i in range(n_rays):
            if c_rays[i] == 1:
                for j in adj[i]:
                    if c_rays[j] == 1:
                        return False, f"Independent: orthogonal rays {i}, {j} both 1", details

        # Verify contexts
        for ctx in contexts:
            if sum(c_rays[r] for r in ctx) != 1:
                return False, f"Independent: context {ctx} sum is not 1", details

        return True, "Independent non-contextual colouring verified", details

    else:
        # Verify uncolourability
        cert = answer.get("certificate", {})
        subset = answer.get("subset")
        if (
            not isinstance(cert, dict)
            or not isinstance(subset, list)
            or not subset
            or any(type(r) is not int or not 0 <= r < n_rays for r in subset)
            or len(set(subset)) != len(subset)
        ):
            return False, "Independent: malformed certificate or ray subset", details
        subset_set = set(subset)
        if cert.get("kind") == "parity":
            p_ctxs = cert.get("contexts", [])
            if not isinstance(p_ctxs, list) or len(p_ctxs) % 2 != 1:
                return False, "Independent: parity context count is not odd", details
            actual_contexts = {tuple(context) for context in contexts}
            for context in p_ctxs:
                if (
                    not isinstance(context, list)
                    or len(context) != dimension
                    or any(type(r) is not int or r not in subset_set for r in context)
                    or len(set(context)) != dimension
                    or tuple(sorted(context)) not in actual_contexts
                ):
                    return False, "Independent: parity names a non-context in the subset", details
            # Check context degrees
            degs: Dict[int, int] = {}
            for c in p_ctxs:
                for r in c:
                    degs[r] = degs.get(r, 0) + 1
            if any(d % 2 != 0 for d in degs.values()):
                return False, "Independent: parity certificate has odd ray degree", details
            return True, "Independent parity proof confirmed", details
        if cert.get("kind") not in ("refutation", "unsat_core"):
            return False, "Independent: unsupported certificate kind", details
        if n_rays > MAX_ENUMERATION_RAYS:
            raise IndependentVerificationUnavailable(n_rays)

        # Enumerate the claimed subset using only this checker's own graph and
        # contexts. No reference solver or first-checker verdict is reused.
        bit = {ray: 1 << index for index, ray in enumerate(subset)}
        pair_masks = [
            bit[u] | bit[v]
            for u in subset
            for v in adj[u]
            if v in subset_set and u < v
        ]
        context_masks = [
            sum(bit[ray] for ray in context)
            for context in contexts
            if all(ray in subset_set for ray in context)
        ]
        assignments = 1 << len(subset)
        details.update(verification_method="independent_exhaustive", assignments=assignments)
        for assignment in range(assignments):
            if any(assignment & pair == pair for pair in pair_masks):
                continue
            if all((assignment & context).bit_count() == 1 for context in context_masks):
                return False, "Independent: claimed subset has a valid colouring", details
        return True, "Independent bounded exhaustive refutation confirmed", details
