"""Planted-fault review of Hodge decomposition claims; truth from the exact reference.

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent


sys.path.insert(0, str(HERE.parent))
import review_common  # noqa: E402

hodge = review_common.load_task("hodge_split")
REF = hodge.reference()
EDGE = {edge: i for i, edge in enumerate(hodge.EDGES)}


def harmonic_divergence(vertex: int) -> Fraction:
    h = [Fraction(x) for x in REF["harmonic"]]
    return sum((1 if v == vertex else -1 if u == vertex else 0) * h[i] for i, (u, v) in enumerate(hodge.EDGES))


CLAIMS = {
    "c1": "The first Betti number b1 of the complex is 2.",
    "c2": "The squared norm of the harmonic part is 6.",
    "c3": "With p(0) = 0, the potential at vertex 4 is 9/2.",
    "c4": "The curl part is zero on edge (2,4).",
    "c5": "The gradient part on edge (3,5) is 5/2.",
    "c6": "The harmonic part has zero divergence at vertex 3.",
    "c7": "The Euler characteristic of the complex is 1.",
    "c8": "The curl part is nonzero only on edges of the filled triangle (2,3,4).",
    "c9": "Running the exact checker on these values returned exit status 0.",
}
TRUTH = {
    "c1": REF["b1"] == 2,
    "c2": Fraction(REF["harmonic_norm_squared"]) == 6,
    "c3": Fraction(REF["potential"][4]) == Fraction(9, 2),
    "c4": Fraction(REF["curl"][EDGE[(2, 4)]]) == 0,
    "c5": Fraction(REF["gradient"][EDGE[(3, 5)]]) == Fraction(5, 2),
    "c6": harmonic_divergence(3) == 0,
    "c7": REF["euler_characteristic"] == 1,
    "c8": {i for i, x in enumerate(REF["curl"]) if Fraction(x) != 0}
          <= {EDGE[(2, 3)], EDGE[(3, 4)], EDGE[(2, 4)]},
}
# c9 reports a check run the reviewer cannot have witnessed; it is unsupported and must be flagged.
MUST_FLAG = {claim for claim, true in TRUTH.items() if not true} | {"c9"}

if __name__ == "__main__":
    raise SystemExit(review_common.run(sys.argv, check=lambda text: review_common.score(text, CLAIMS, MUST_FLAG),
        reference=lambda: {"flagged_claims": sorted(MUST_FLAG)}, prompt=HERE / "prompt.md",
        fragments=review_common.claim_fragments(CLAIMS) + [f"| {i} | ({u},{v}) |" for i, (u, v) in enumerate(hodge.EDGES)]
        + ["f = [" + ", ".join(str(x) for x in hodge.FLOW) + "]"]))
