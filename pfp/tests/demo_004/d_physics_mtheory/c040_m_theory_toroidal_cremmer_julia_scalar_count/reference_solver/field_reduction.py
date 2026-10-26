"""Field reduction and Hodge dualization module for 11D supergravity on T^k.

Calculates:
  - Metric components g_{ij} (scalars) and g_{mu i} (KK vectors).
  - 3-form components C_{ijk} (scalars), C_{mu ij} (1-forms), C_{mu nu i} (2-forms), C_{mu nu rho} (3-forms).
  - Exact Hodge dualization in D = 11 - k dimensions:
    * Dual to scalar (0-form): p = D - 2
    * Dual to vector (1-form): p = D - 3
  - Partition of scalars and vectors by origin with strict additive consistency.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from typing import Any


def compute_undualized_fields(k: int) -> dict[str, int]:
    """Computes raw un-dualized field counts from 11D SUGRA on T^k."""
    if not (1 <= k <= 8):
        raise ValueError(f"k must be in 1..8, got {k}")

    return {
        "D": 11 - k,
        "metric_scalars": k * (k + 1) // 2,
        "three_form_scalars": math.comb(k, 3),
        "kk_vectors": k,
        "one_forms": math.comb(k, 2),
        "two_forms": math.comb(k, 1),
        "three_forms": math.comb(k, 0),
    }


def compute_scalars_breakdown(k: int) -> dict[str, Any]:
    """Computes the exact scalar count breakdown by origin in D = 11 - k dimensions.

    A p-form potential dualizes to a (D - p - 2)-form potential.
    Dualization to a scalar (0-form) occurs iff p = D - 2:
      - In D=5 (k=6): C_{mu nu rho} (p=3) dualizes to 1 scalar.
      - In D=4 (k=7): C_{mu nu i} (p=2) dualize to 7 scalars.
      - In D=3 (k=8): vectors (g_{mu i} and C_{mu ij}, p=1) dualize to 8 + 28 = 36 scalars.
      - For k <= 5: no forms have p = D - 2.
    """
    if not (1 <= k <= 8):
        raise ValueError(f"k must be in 1..8, got {k}")

    metric = k * (k + 1) // 2
    three_form = math.comb(k, 3)

    if k in (1, 2, 3, 4, 5):
        return {
            "metric": metric,
            "three_form": three_form,
            "dual_forms": 0,
            "total": metric + three_form,
        }
    elif k == 6:
        # In D=5, D-2 = 3. 3-form C_{mu nu rho} (p=3) dualizes to 1 scalar.
        return {
            "metric": metric,
            "three_form": three_form,
            "dual_C_mu_nu_rho": 1,
            "total": metric + three_form + 1,
        }
    elif k == 7:
        # In D=4, D-2 = 2. 2-forms C_{mu nu i} (p=2, count 7) dualize to 7 scalars.
        return {
            "metric": metric,
            "three_form": three_form,
            "dual_C_mu_nu_i": 7,
            "total": metric + three_form + 7,
        }
    elif k == 8:
        # In D=3, D-2 = 1. Vectors (p=1): g_{mu i} (8) and C_{mu ij} (28) dualize to 36 scalars.
        return {
            "metric": metric,
            "three_form": three_form,
            "dual_kk_vectors": 8,
            "dual_C_mu_ij": 28,
            "total": metric + three_form + 8 + 28,
        }
    raise AssertionError("Unreachable")


def compute_vectors_breakdown(k: int) -> dict[str, Any]:
    """Computes the exact vector field count breakdown by origin in D = 11 - k dimensions.

    A p-form potential dualizes to a (D - p - 2)-form potential.
    Dualization to a vector (1-form) occurs iff p = D - 3:
      - In D=6 (k=5): C_{mu nu rho} (p=3) dualizes to 1 vector (5 + 10 + 1 = 16).
      - In D=5 (k=6): C_{mu nu i} (p=2) dualize to 6 vectors (6 + 15 + 6 = 27).
      - In D=4 (k=7): vectors have p=1, self-dual in D=4 (28 electric vectors).
      - In D=3 (k=8): 0 propagating vectors (all dualized to scalars).
      - For k <= 4: KK vectors (k) + C_{mu ij} (comb(k, 2)).
    """
    if not (1 <= k <= 8):
        raise ValueError(f"k must be in 1..8, got {k}")

    D = 11 - k
    if D == 3:
        return {
            "metric_kk": 0,
            "three_form": 0,
            "dual_forms": 0,
            "total": 0,
        }

    metric_kk = k
    three_form_vecs = math.comb(k, 2)
    dual_vecs = 0

    if D == 6:
        dual_vecs = 1
    elif D == 5:
        dual_vecs = 6

    total = metric_kk + three_form_vecs + dual_vecs
    return {
        "metric_kk": metric_kk,
        "three_form": three_form_vecs,
        "dual_forms": dual_vecs,
        "total": total,
    }
