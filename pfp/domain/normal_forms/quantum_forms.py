"""Exact fermion and quantile-sketch normal forms.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping, Optional, Sequence

# =============================================================================
# Part 4: Fermion Sign Problem (FSP) Normal Forms (BSS-NF and MIC-NF)
# =============================================================================


@dataclass(frozen=True)
class BssnfResult:
    """Verification result for Binary Sign-Switching Normal Form."""

    terminal: str
    gaugeable: bool
    gauge: tuple[int, ...] | None
    odd_cycle: tuple[int, ...] | None
    transformed_matrix: tuple[tuple[Fraction, ...], ...] | None


def _parse_symmetric_fraction_matrix(matrix: Sequence[Sequence[object]]) -> list[list[Fraction]]:
    n = len(matrix)
    if n == 0:
        raise ValueError("Matrix cannot be empty")

    frac_matrix: list[list[Fraction]] = []
    for i in range(n):
        if len(matrix[i]) != n:
            raise ValueError(f"Matrix must be square: row {i} has length {len(matrix[i])} != {n}")
        row: list[Fraction] = []
        for j in range(n):
            val = matrix[i][j]
            if isinstance(val, (float, complex)):
                raise ValueError(f"FloatContaminationRefusal at H[{i}][{j}]: floats forbidden")
            row.append(Fraction(val))
        frac_matrix.append(row)

    for i in range(n):
        for j in range(i + 1, n):
            if frac_matrix[i][j] != frac_matrix[j][i]:
                raise ValueError(f"NonSymmetricRefusal: H[{i}][{j}] != H[{j}][{i}]")

    return frac_matrix


def _build_bssnf_adj(frac_matrix: list[list[Fraction]], n: int) -> list[list[tuple[int, int]]]:
    adj: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            val = frac_matrix[i][j]
            if val != Fraction(0):
                bit = 1 if val > 0 else 0
                adj[i].append((j, bit))
                adj[j].append((i, bit))
    return adj


def _extract_odd_cycle(u: int, v: int, parent: list[tuple[int, int] | None]) -> tuple[int, ...]:
    path_u = [u]
    curr = u
    while parent[curr] is not None:
        p_u = parent[curr]
        assert p_u is not None
        curr = p_u[0]
        path_u.append(curr)

    path_v = [v]
    curr = v
    while parent[curr] is not None:
        p_v = parent[curr]
        assert p_v is not None
        curr = p_v[0]
        path_v.append(curr)

    # Find lowest common ancestor
    set_u = set(path_u)
    lca = None
    for node in path_v:
        if node in set_u:
            lca = node
            break

    cycle: list[int] = []
    curr = u
    while curr != lca:
        cycle.append(curr)
        p_c = parent[curr]
        assert p_c is not None
        curr = p_c[0]
    cycle.append(lca)

    v_branch: list[int] = []
    curr = v
    while curr != lca:
        v_branch.append(curr)
        p_vb = parent[curr]
        assert p_vb is not None
        curr = p_vb[0]
    cycle.extend(reversed(v_branch))
    cycle.append(u)
    return tuple(cycle)


def _solve_bssnf_gauge_or_frustration(
    adj: list[list[tuple[int, int]]], n: int
) -> tuple[tuple[int, ...] | None, tuple[int, ...] | None]:
    gauge: list[int | None] = [None] * n
    parent: list[tuple[int, int] | None] = [None] * n
    depth: list[int] = [0] * n

    for root in range(n):
        if gauge[root] is not None:
            continue
        cycle = _propagate_bssnf_component(root, adj, gauge, parent, depth)
        if cycle is not None:
            return None, cycle

    final_gauge = tuple(gauge[i] if gauge[i] is not None else 0 for i in range(n))
    return final_gauge, None


def _propagate_bssnf_component(
    root: int,
    adjacency: list[list[tuple[int, int]]],
    gauge: list[int | None],
    parent: list[tuple[int, int] | None],
    depth: list[int],
) -> tuple[int, ...] | None:
    gauge[root] = 0
    queue = deque([root])
    while queue:
        source = queue.popleft()
        for target, bit in adjacency[source]:
            cycle, discovered = _visit_bssnf_edge(source, target, bit, gauge, parent)
            if discovered:
                depth[target] = depth[source] + 1
                queue.append(target)
            if cycle is not None:
                return cycle
    return None


def _visit_bssnf_edge(
    source: int,
    target: int,
    bit: int,
    gauge: list[int | None],
    parent: list[tuple[int, int] | None],
) -> tuple[tuple[int, ...] | None, bool]:
    source_gauge = gauge[source]
    assert source_gauge is not None
    required = source_gauge ^ bit
    if gauge[target] is None:
        gauge[target] = required
        parent[target] = (source, bit)
        return None, True
    if gauge[target] != required:
        return _extract_odd_cycle(source, target, parent), False
    return None, False


def _build_stoquastic_transformed_matrix(
    frac_matrix: list[list[Fraction]], final_gauge: tuple[int, ...], n: int
) -> tuple[tuple[Fraction, ...], ...]:
    transformed: list[tuple[Fraction, ...]] = []
    for i in range(n):
        row_t: list[Fraction] = []
        sign_i = -1 if final_gauge[i] == 1 else 1
        for j in range(n):
            sign_j = -1 if final_gauge[j] == 1 else 1
            row_t.append(sign_i * frac_matrix[i][j] * sign_j)
        transformed.append(tuple(row_t))
    return tuple(transformed)


def verify_bssnf(matrix: Sequence[Sequence[object]]) -> BssnfResult:
    """BSS-NF: Binary Sign-Switching Normal Form verifier for real symmetric matrices.

    Checks:
    1. Rejects float inputs (FloatContaminationRefusal).
    2. Rejects non-symmetric matrices (NonSymmetricRefusal).
    3. Finds gauge potential alpha in {0, 1}^N converting H to stoquastic (off-diagonal <= 0).
    4. If frustrated, returns certified odd cycle obstruction.
    """
    frac_matrix = _parse_symmetric_fraction_matrix(matrix)
    n = len(frac_matrix)
    adj = _build_bssnf_adj(frac_matrix, n)
    final_gauge, odd_cycle = _solve_bssnf_gauge_or_frustration(adj, n)
    if odd_cycle is not None:
        return BssnfResult(
            terminal="OddCycleFrustratedObstruction",
            gaugeable=False,
            gauge=None,
            odd_cycle=odd_cycle,
            transformed_matrix=None,
        )

    assert final_gauge is not None
    transformed = _build_stoquastic_transformed_matrix(frac_matrix, final_gauge, n)
    terminal = "StoquasticExactRepair" if any(final_gauge) else "RestrictedSignGaugeRepair"
    return BssnfResult(
        terminal=terminal,
        gaugeable=True,
        gauge=final_gauge,
        odd_cycle=None,
        transformed_matrix=transformed,
    )


@dataclass(frozen=True)
class MicnfResult:
    """Verification result for Meron Involutive Cancellation Normal Form."""

    terminal: str
    pairs: tuple[tuple[str, str], ...]
    survivors: tuple[str, ...]
    signed_sum: Fraction
    survivor_sum: Fraction


def verify_micnf(
    sectors: Sequence[Mapping[str, Any]],
    cancellation_ids: Sequence[str],
    involution_map: Mapping[str, str],
) -> MicnfResult:
    """MIC-NF: Meron Involutive Cancellation Normal Form verifier.

    Verifies:
    1. Involution law: Xi(Xi(x)) == x.
    2. Fixed-point free: Xi(x) != x.
    3. Sign reversal: sgn(Xi(x)) == -sgn(x).
    4. Weight preservation: w(Xi(x)) == w(x).
    5. Non-negative survivors: sgn(y) == +1 for all y in S \\ S0.
    """
    sector_by_id = _parse_micnf_sectors(sectors)

    c_set = set(cancellation_ids)
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()

    for x in cancellation_ids:
        y, refusal = _validate_micnf_pair(x, c_set, sector_by_id, involution_map)
        if refusal is not None:
            return refusal

        if x not in seen and y not in seen:
            pairs.append((x, y))
            seen.add(x)
            seen.add(y)

    # Check survivor sector
    survivors, survivor_sum = _micnf_survivors(sector_by_id, c_set)
    if survivors is None:
        return MicnfResult("NegativeSurvivorRefusal", (), (), Fraction(0), Fraction(0))

    signed_sum = sum(w * sgn for w, sgn in sector_by_id.values())
    if signed_sum != survivor_sum:
        raise ValueError(
            f"Arithmetic contradiction: signed_sum ({signed_sum}) != survivor_sum ({survivor_sum})"
        )

    return MicnfResult(
        terminal="MeronExactCancellation",
        pairs=tuple(pairs),
        survivors=tuple(survivors),
        signed_sum=signed_sum,
        survivor_sum=survivor_sum,
    )


def _parse_micnf_sectors(
    sectors: Sequence[Mapping[str, Any]],
) -> dict[str, tuple[Fraction, int]]:
    parsed: dict[str, tuple[Fraction, int]] = {}
    for sector in sectors:
        path_id = str(sector["path_id"])
        raw_weight = sector["weight"]
        if isinstance(raw_weight, (float, complex)):
            raise ValueError(f"FloatContaminationRefusal: weight for {path_id} must be rational")
        sign = int(sector["sign"])
        if sign not in (-1, 1):
            raise ValueError(f"Sign must be +1 or -1, got {sign}")
        parsed[path_id] = Fraction(raw_weight), sign
    return parsed


def _validate_micnf_pair(
    path_id: str,
    cancellation_ids: set[str],
    sectors: Mapping[str, tuple[Fraction, int]],
    involution: Mapping[str, str],
) -> tuple[str, MicnfResult | None]:
    if path_id not in sectors:
        raise ValueError(f"Cancellation path {path_id!r} not in declared sectors")
    partner = involution.get(path_id)
    if partner is None or partner not in cancellation_ids:
        raise ValueError(
            f"Involution map must map cancellation set into itself: {path_id} -> {partner}"
        )
    if path_id == partner:
        return partner, MicnfResult("FixedPointViolationRefusal", (), (), Fraction(0), Fraction(0))
    if involution.get(partner) != path_id:
        raise ValueError(
            f"Involution property violated: Xi(Xi({path_id})) = {involution.get(partner)} != {path_id}"
        )
    weight, sign = sectors[path_id]
    partner_weight, partner_sign = sectors[partner]
    if sign != -partner_sign:
        return partner, MicnfResult("SignPreservingPairRefusal", (), (), Fraction(0), Fraction(0))
    if weight != partner_weight:
        return partner, MicnfResult("WeightMismatchRefusal", (), (), Fraction(0), Fraction(0))
    return partner, None


def _micnf_survivors(
    sectors: Mapping[str, tuple[Fraction, int]], cancellation_ids: set[str]
) -> tuple[list[str] | None, Fraction]:
    survivors: list[str] = []
    total = Fraction(0)
    for path_id, (weight, sign) in sectors.items():
        if path_id not in cancellation_ids:
            if sign != 1:
                return None, Fraction(0)
            survivors.append(path_id)
            total += weight
    return survivors, total


@dataclass(frozen=True)
class QuantileRepairResult:
    """Verification result for epsilon-BQNF Quantile Sketch Cochain repair."""

    terminal: str
    estimated_quantile: Optional[float]
    true_quantile: Optional[float]
    error_delta: Optional[float]
    tolerance: float
    within_tolerance: bool
    reason: str


class QuantileSketchCochain:
    """Auxiliary piecewise-linear quantile sketch cochain for non-linear aggregate repair.

    Maintains frequency counts across fixed-width buckets under dynamic streaming insertions
    and deletions.
    """

    def __init__(self, bucket_width: float = 10.0):
        self.bucket_width = bucket_width
        self.buckets: dict[int, int] = {}
        self.total_count: int = 0

    def add(self, value: float) -> None:
        b = int(math.floor(value / self.bucket_width))
        self.buckets[b] = self.buckets.get(b, 0) + 1
        self.total_count += 1

    def remove(self, value: float) -> None:
        b = int(math.floor(value / self.bucket_width))
        if b in self.buckets and self.buckets[b] > 0:
            self.buckets[b] -= 1
            if self.buckets[b] == 0:
                del self.buckets[b]
            self.total_count -= 1

    def estimate_quantile(self, q: float = 0.5) -> Optional[float]:
        if self.total_count == 0 or not self.buckets:
            return None
        target_rank = q * self.total_count
        cum = 0
        sorted_buckets = sorted(self.buckets.items(), key=lambda kv: kv[0])
        for b_id, cnt in sorted_buckets:
            if cum + cnt >= target_rank:
                lower = b_id * self.bucket_width
                upper = (b_id + 1) * self.bucket_width
                frac = (target_rank - cum) / cnt if cnt > 0 else 0.0
                return lower + frac * (upper - lower)
            cum += cnt
        last_b_id = sorted_buckets[-1][0]
        return (last_b_id + 1) * self.bucket_width


def verify_quantile_sketch_repair(
    sketch: Optional[QuantileSketchCochain],
    true_values: Sequence[float],
    q: float = 0.5,
    tolerance: float = 15.0,
) -> QuantileRepairResult:
    """Verifies epsilon-BQNF Quantile Sketch Cochain repair under streaming deletions.

    Matches lean4/NormalFormsCore.lean (quantile_sketch_repair_routing):
    1. If sketch is None: routes to Recompute (missing_quantile_sketch_forces_recompute).
    2. If sketch count == 0: routes to Recompute (empty_quantile_sketch_forces_recompute).
    3. If |estimated - true| <= tolerance: routes to Repair (quantile_within_tolerance_repairs).
    4. If |estimated - true| > tolerance: routes to Recompute (quantile_exceeding_tolerance_forces_recompute).
    """
    if not true_values:
        return _quantile_recompute(None, tolerance, "EmptyPartitionValues")
    if not (0.0 <= q <= 1.0):
        raise ValueError(f"Quantile parameter q must be in [0, 1], got {q}")
    true_q = _linear_quantile(true_values, q)
    if sketch is None:
        return _quantile_recompute(true_q, tolerance, "MissingQuantileSketch")
    if sketch.total_count == 0:
        return _quantile_recompute(true_q, tolerance, "EmptyQuantileSketch")
    est_q = sketch.estimate_quantile(q)
    if est_q is None:
        return _quantile_recompute(true_q, tolerance, "UncomputableSketchQuantile")
    return _quantile_repair_outcome(est_q, true_q, tolerance)


def _linear_quantile(values: Sequence[float], q: float) -> float:
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = q * (len(sorted_values) - 1)
    low = int(math.floor(position))
    high = int(math.ceil(position))
    fraction = position - low
    if low == high:
        return float(sorted_values[low])
    return float((1.0 - fraction) * sorted_values[low] + fraction * sorted_values[high])


def _quantile_recompute(
    true_quantile: float | None, tolerance: float, reason: str
) -> QuantileRepairResult:
    return QuantileRepairResult(
        terminal="Recompute",
        estimated_quantile=None,
        true_quantile=true_quantile,
        error_delta=None,
        tolerance=tolerance,
        within_tolerance=False,
        reason=reason,
    )


def _quantile_repair_outcome(
    estimated: float, true_quantile: float, tolerance: float
) -> QuantileRepairResult:
    err = abs(estimated - true_quantile)
    within_tol = err <= tolerance
    terminal = "Repair" if within_tol else "Recompute"
    reason = (
        f"Quantile error {err:.4f} within tolerance {tolerance}"
        if within_tol
        else f"Quantile error {err:.4f} exceeds tolerance {tolerance}"
    )

    return QuantileRepairResult(
        terminal=terminal,
        estimated_quantile=estimated,
        true_quantile=true_quantile,
        error_delta=err,
        tolerance=tolerance,
        within_tolerance=within_tol,
        reason=reason,
    )
