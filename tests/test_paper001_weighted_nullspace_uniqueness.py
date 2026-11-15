"""
Executable verification for Derivation ATL-P001-006 (PFP001-06).

Checks:
1. Positive witness where the weighted null-space property on support S
   is satisfied, and the optimal residual is unique.
2. Boundary / negative control showing that failure of the sufficient condition
   is not a nonuniqueness certificate (Challenge A on K4).
3. Counterexample witness where failure of the condition coincides with
   multiple minimizers (equal-weight triangle).
4. Strict triangle-inequality decomposition on support.
"""

from fractions import Fraction
import itertools


def test_positive_witness_wnsp_implies_unique_residual():
    """
    On a 3-cycle with strictly distinct weights, WNSP holds on S={e0},
    and the optimal residual is unique.
    """
    weights = {"ab": Fraction(1), "bc": Fraction(2), "ca": Fraction(3)}
    reports = {"ab": Fraction(1), "bc": Fraction(1), "ca": Fraction(1)}
    r_star = {"ab": Fraction(3), "bc": Fraction(0), "ca": Fraction(0)}
    support_s = {"ab"}
    support_sc = {"bc", "ca"}

    cost_star = sum(weights[e] * abs(r_star[e]) for e in weights)
    assert cost_star == Fraction(3)

    # Check WNSP and uniqueness over non-trivial potential perturbations
    for sa, sb, sc in itertools.product(range(-4, 5), repeat=3):
        if sa == sb == sc:
            continue
        z = {
            "ab": Fraction(sb - sa),
            "bc": Fraction(sc - sb),
            "ca": Fraction(sa - sc),
        }
        # WNSP strictly holds
        norm_zs = sum(weights[e] * abs(z[e]) for e in support_s)
        norm_zsc = sum(weights[e] * abs(z[e]) for e in support_sc)
        assert norm_zs < norm_zsc, f"WNSP violated for z={z}"

        # Strict cost increase
        cost_perturbed = sum(weights[e] * abs(r_star[e] + z[e]) for e in weights)
        lower_bound = cost_star - norm_zs + norm_zsc
        assert cost_perturbed >= lower_bound
        assert lower_bound > cost_star
        assert cost_perturbed > cost_star


def test_boundary_failure_of_wnsp_is_not_nonuniqueness_certificate():
    """
    Challenge A on K4: WNSP fails on S, yet the optimal residual is strictly unique.
    Demonstrates that failure of the sufficient condition is not a nonuniqueness certificate.
    """
    edges = ("ab", "ac", "ad", "bc", "bd", "cd")
    weights = {e: Fraction(1) for e in edges}
    reports = {
        "ab": Fraction(1),
        "ac": Fraction(-1),
        "ad": Fraction(0),
        "bc": Fraction(0),
        "bd": Fraction(0),
        "cd": Fraction(0),
    }
    r_star = {
        "ab": Fraction(1),
        "ac": Fraction(-1),
        "ad": Fraction(0),
        "bc": Fraction(0),
        "bd": Fraction(0),
        "cd": Fraction(0),
    }
    support_s = {"ab", "ac"}
    support_sc = {"ad", "bc", "bd", "cd"}

    cost_star = sum(weights[e] * abs(r_star[e]) for e in edges)
    assert cost_star == Fraction(2)

    # 1. Dual circulation certificate establishing strict uniqueness
    dual = {
        "ab": Fraction(1),
        "ac": Fraction(-1),
        "ad": Fraction(0),
        "bc": Fraction(1, 2),
        "bd": Fraction(1, 2),
        "cd": Fraction(-1, 2),
    }
    # Vertex divergences balance
    assert dual["ab"] + dual["ac"] + dual["ad"] == 0
    assert dual["bc"] + dual["bd"] - dual["ab"] == 0
    assert dual["cd"] - (dual["ac"] + dual["bc"]) == 0
    assert -(dual["ad"] + dual["bd"] + dual["cd"]) == 0

    # Strict capacity slack on Sc
    for e in support_sc:
        assert abs(dual[e]) < weights[e]

    dual_value = sum(reports[e] * dual[e] for e in edges)
    assert dual_value == cost_star == Fraction(2)

    # 2. Exhibit perturbation in im B where WNSP fails
    h_viol = {"a": Fraction(1), "b": Fraction(0), "c": Fraction(0), "d": Fraction(0)}
    z_viol = {
        "ab": h_viol["b"] - h_viol["a"],
        "ac": h_viol["c"] - h_viol["a"],
        "ad": h_viol["d"] - h_viol["a"],
        "bc": h_viol["c"] - h_viol["b"],
        "bd": h_viol["d"] - h_viol["b"],
        "cd": h_viol["d"] - h_viol["c"],
    }
    norm_zs = sum(weights[e] * abs(z_viol[e]) for e in support_s)
    norm_zsc = sum(weights[e] * abs(z_viol[e]) for e in support_sc)
    assert norm_zs == Fraction(2) and norm_zsc == Fraction(1)
    assert norm_zs > norm_zsc  # WNSP strictly fails

    # 3. Verify that every non-constant potential has strictly higher cost
    for sa, sb, sc, sd in itertools.product(range(-2, 3), repeat=4):
        if sa == sb == sc == sd:
            continue
        z = {
            "ab": Fraction(sb - sa),
            "ac": Fraction(sc - sa),
            "ad": Fraction(sd - sa),
            "bc": Fraction(sc - sb),
            "bd": Fraction(sd - sb),
            "cd": Fraction(sd - sc),
        }
        cost_perturbed = sum(weights[e] * abs(r_star[e] + z[e]) for e in edges)
        assert cost_perturbed > cost_star


def test_boundary_failure_of_wnsp_with_nonunique_minima():
    """
    Equal-weight triangle: WNSP fails on S={ab, bc}, and alternative minimizers exist.
    """
    weights = {"ab": Fraction(2), "bc": Fraction(2), "ca": Fraction(2)}
    reports = {"ab": Fraction(1), "bc": Fraction(1), "ca": Fraction(1)}

    r1 = {"ab": Fraction(3), "bc": Fraction(0), "ca": Fraction(0)}
    r2 = {"ab": Fraction(0), "bc": Fraction(3), "ca": Fraction(0)}
    r_split = {"ab": Fraction(3, 2), "bc": Fraction(3, 2), "ca": Fraction(0)}

    cost1 = sum(weights[e] * abs(r1[e]) for e in weights)
    cost2 = sum(weights[e] * abs(r2[e]) for e in weights)
    cost_split = sum(weights[e] * abs(r_split[e]) for e in weights)
    assert cost1 == cost2 == cost_split == Fraction(6)

    # Difference perturbation z = r2 - r1 is in im B: z = B(0, 1, -1) - B(0, -2, -1)
    z = {"ab": Fraction(-3), "bc": Fraction(3), "ca": Fraction(0)}
    support_s = {"ab", "bc"}
    support_sc = {"ca"}
    norm_zs = sum(weights[e] * abs(z[e]) for e in support_s)
    norm_zsc = sum(weights[e] * abs(z[e]) for e in support_sc)
    assert norm_zs == Fraction(12) and norm_zsc == Fraction(0)
    assert norm_zs > norm_zsc  # WNSP fails


def test_strict_triangle_inequality_decomposition():
    """
    Verifies the algebraic decomposition:
    ||r + z||_{1, w} >= ||r||_{1, w} - ||z_S||_{1, w} + ||z_{S^c}||_{1, w}
    with exact equality on S^c and reverse triangle inequality on S.
    """
    weights = {"e1": Fraction(3), "e2": Fraction(4), "e3": Fraction(5)}
    r = {"e1": Fraction(2), "e2": Fraction(-3), "e3": Fraction(0)}
    support_s = {"e1", "e2"}
    support_sc = {"e3"}
    norm_r = sum(weights[e] * abs(r[e]) for e in weights)

    for z1, z2, z3 in itertools.product(range(-5, 6), repeat=3):
        z = {"e1": Fraction(z1), "e2": Fraction(z2), "e3": Fraction(z3)}
        norm_zs = sum(weights[e] * abs(z[e]) for e in support_s)
        norm_zsc = sum(weights[e] * abs(z[e]) for e in support_sc)
        norm_rz = sum(weights[e] * abs(r[e] + z[e]) for e in weights)

        # 1. Exact equality on Sc
        assert sum(weights[e] * abs(r[e] + z[e]) for e in support_sc) == norm_zsc

        # 2. Reverse triangle inequality on S
        assert sum(weights[e] * abs(r[e] + z[e]) for e in support_s) >= norm_r - norm_zs

        # 3. Overall lower bound
        assert norm_rz >= norm_r - norm_zs + norm_zsc
