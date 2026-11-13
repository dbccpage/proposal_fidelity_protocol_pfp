"""Exact finite bounds for the integrated rooted hopping carrier of the triangle Fock example.

This checks the restricted single-path gap; regroupings and time-labelled maps
are outside its carrier.
"""
import json
from fractions import Fraction
from itertools import product


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def exp_minus_bounds(x: Fraction, pairs: int = 16) -> tuple[Fraction, Fraction]:
    """Alternating-series enclosure of exp(-x), with 0 <= x <= 1.

    For this interval the successive term magnitudes decrease. The odd partial
    sum is a lower bound and the preceding even partial sum is an upper bound.
    """
    if type(x) not in (int, Fraction) or not 0 <= x <= 1:
        raise ValueError("Exact x in [0, 1] required")
    if type(pairs) is not int or pairs < 1:
        raise ValueError("A positive integer pair budget is required")
    term = Fraction(1)
    total = term
    upper = total
    for n in range(1, 2 * pairs + 2):
        term *= -Fraction(x, n)
        total += term
        if n % 2 == 0:
            upper = total
    return total, upper


def hopping_amplitude(source: tuple[int, ...], target: tuple[int, ...]) -> int:
    """Matrix element of -H_hop at t=1 in the stated six-mode ordering."""
    changed = [i for i in range(6) if source[i] != target[i]]
    if len(changed) != 2:
        return 0
    a, b = changed
    if a // 3 != b // 3 or source[a] + source[b] != 1:
        return 0
    return -1 if sum(source[a + 1:b]) % 2 else 1


def verify_exact_gap() -> dict:
    """Enumerate the finite 3-hop carrier and check rational strict separation."""
    states = tuple(product((0, 1), repeat=6))
    energy = {s: 2 * sum(s[i] * s[i + 3] for i in range(3)) for s in states}
    adjacency = {
        a: {b: hopping_amplitude(a, b) for b in states if hopping_amplitude(a, b)}
        for a in states
    }
    positive = []
    negative = []
    for a in states:
        for b, ab in adjacency[a].items():
            for c, bc in adjacency[b].items():
                ca = adjacency[c].get(a, 0)
                if ca:
                    (positive if ab * bc * ca > 0 else negative).append((a, b, c))
    target = ((1, 1, 0, 1, 1, 1), (1, 0, 1, 1, 1, 1), (0, 1, 1, 1, 1, 1))
    _require(len(positive) == len(negative) == 96, "Unexpected signed path counts")
    _require(target in negative and tuple(energy[s] for s in target) == (4, 4, 4), "Target path mismatch")
    _require(max(energy[s] for path in positive for s in path) == 2, "Positive path energy bound failed")
    _require(max(energy.values()) == 6, "Global occupation energy bound failed")
    _require(all(adjacency[b].get(a) == value for a in states for b, value in adjacency[a].items()), "Hopping symmetry failed")
    _require(all(a not in adjacency[a] for a in states), "Unexpected diagonal hop")

    e1_lo, e1_hi = exp_minus_bounds(Fraction(1))
    ehalf_lo, _ = exp_minus_bounds(Fraction(1, 2))
    ethreequarter_lo, _ = exp_minus_bounds(Fraction(3, 4))
    target_lo, target_hi = e1_lo / 384, e1_hi / 384
    zero_hop_lower = ethreequarter_lo ** 2
    two_hop_lower = zero_hop_lower / 32
    three_hop_lower = ehalf_lo / 384
    long_hop_upper = Fraction(1, 6144)
    _require(long_hop_upper < target_lo <= target_hi < three_hop_lower, "Long/three-hop gap failed")
    _require(target_hi < two_hop_lower < zero_hop_lower, "Zero/two-hop gap failed")
    return {
        "authority_effect": "None",
        "scope": "rooted hopping sequences after ordered times are integrated out",
        "total_3hop_paths": len(positive) + len(negative),
        "positive_3hop_paths": len(positive),
        "negative_3hop_paths": len(negative),
        "target_absolute_weight_symbolic": "exp(-1)/384",
        "target_lower": str(target_lo),
        "target_upper": str(target_hi),
        "zero_hop_lower": str(zero_hop_lower),
        "two_hop_lower": str(two_hop_lower),
        "positive_three_hop_lower": str(three_hop_lower),
        "four_or_more_hop_upper": str(long_hop_upper),
        "gap_certified": True,
        "physical_sign_problem_classification": False,
    }


if __name__ == "__main__":
    print(json.dumps(verify_exact_gap(), indent=2, sort_keys=True))
