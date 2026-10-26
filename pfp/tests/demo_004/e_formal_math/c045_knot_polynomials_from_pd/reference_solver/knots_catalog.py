# AuthorityEffect: None.
"""
Canonical Catalog of Knots up to 7 Crossings for C045.
Precomputed invariant signatures (writhe, Jones polynomial, Alexander polynomial, chirality).
"""

from typing import Any, Dict, Tuple

CANONICAL_KNOTS: Dict[str, Dict[str, Any]] = {
    "0_1": {
        "name": "Unknot",
        "crossings": 0,
        "writhe": 0,
        "chirality": "ACHIRAL",
        "pd": [],
        "jones": {"0": 1},
        "alexander": {"0": 1},
    },
    "unknot": {
        "name": "Unknot",
        "crossings": 0,
        "writhe": 0,
        "chirality": "ACHIRAL",
        "pd": [],
        "jones": {"0": 1},
        "alexander": {"0": 1},
    },
    "3_1": {
        "name": "Trefoil",
        "crossings": 3,
        "writhe": 3,
        "chirality": "CHIRAL",
        "pd": [[1, 5, 2, 4], [3, 1, 4, 6], [5, 3, 6, 2]],
        "jones": {"1": 1, "3": 1, "4": -1},
        "alexander": {"-1": 1, "0": -1, "1": 1},
    },
    "4_1": {
        "name": "Figure-eight knot",
        "crossings": 4,
        "writhe": 0,
        "chirality": "ACHIRAL",
        "pd": [[4, 2, 5, 1], [8, 6, 1, 5], [6, 3, 7, 4], [2, 7, 3, 8]],
        "jones": {"-2": 1, "-1": -1, "0": 1, "1": -1, "2": 1},
        "alexander": {"-1": -1, "0": 3, "1": -1},
    },
    "5_1": {
        "name": "Cinquefoil knot",
        "crossings": 5,
        "writhe": 5,
        "chirality": "CHIRAL",
        "pd": [[1, 7, 2, 6], [3, 9, 4, 8], [5, 1, 6, 10], [7, 3, 8, 2], [9, 5, 10, 4]],
        "jones": {"2": 1, "4": 1, "5": -1, "6": 1, "7": -1},
        "alexander": {"-2": 1, "-1": -1, "0": 1, "1": -1, "2": 1},
    },
    "5_2": {
        "name": "Three-twist knot",
        "crossings": 5,
        "writhe": -5,
        "chirality": "CHIRAL",
        "pd": [[1, 4, 2, 5], [3, 8, 4, 9], [5, 10, 6, 1], [9, 6, 10, 7], [7, 2, 8, 3]],
        "jones": {"-6": -1, "-5": 1, "-4": -1, "-3": 2, "-2": -1, "-1": 1},
        "alexander": {"-1": 2, "0": -3, "1": 2},
    },
    "6_1": {
        "name": "Stevedore knot",
        "crossings": 6,
        "writhe": -2,
        "chirality": "CHIRAL",
        "pd": [
            [1, 4, 2, 5],
            [7, 10, 8, 11],
            [3, 9, 4, 8],
            [9, 3, 10, 2],
            [5, 12, 6, 1],
            [11, 6, 12, 7],
        ],
        "jones": {"-4": 1, "-3": -1, "-2": 1, "-1": -2, "0": 2, "1": -1, "2": 1},
        "alexander": {"-1": -2, "0": 5, "1": -2},
    },
    "6_2": {
        "name": "6_2 knot",
        "crossings": 6,
        "writhe": -2,
        "chirality": "CHIRAL",
        "pd": [
            [1, 4, 2, 5],
            [5, 10, 6, 11],
            [3, 9, 4, 8],
            [9, 3, 10, 2],
            [7, 12, 8, 1],
            [11, 6, 12, 7],
        ],
        "jones": {"-5": 1, "-4": -2, "-3": 2, "-2": -2, "-1": 2, "0": -1, "1": 1},
        "alexander": {"-2": -1, "-1": 3, "0": -3, "1": 3, "2": -1},
    },
    "6_3": {
        "name": "6_3 knot",
        "crossings": 6,
        "writhe": 0,
        "chirality": "ACHIRAL",
        "pd": [
            [4, 2, 5, 1],
            [8, 4, 9, 3],
            [12, 9, 1, 10],
            [10, 5, 11, 6],
            [6, 11, 7, 12],
            [2, 8, 3, 7],
        ],
        "jones": {"-3": -1, "-2": 2, "-1": -2, "0": 3, "1": -2, "2": 2, "3": -1},
        "alexander": {"-2": 1, "-1": -3, "0": 5, "1": -3, "2": 1},
    },
    "7_1": {
        "name": "Septafoil knot",
        "crossings": 7,
        "writhe": 7,
        "chirality": "CHIRAL",
        "pd": [
            [1, 9, 2, 8],
            [3, 11, 4, 10],
            [5, 13, 6, 12],
            [7, 1, 8, 14],
            [9, 3, 10, 2],
            [11, 5, 12, 4],
            [13, 7, 14, 6],
        ],
        "jones": {"3": 1, "5": 1, "6": -1, "7": 1, "8": -1, "9": 1, "10": -1},
        "alexander": {"-3": 1, "-2": -1, "-1": 1, "0": -1, "1": 1, "2": -1, "3": 1},
    },
}


def invert_jones(jones: Dict[str, int]) -> Dict[str, int]:
    """Inverts t -> t^-1 in Jones polynomial (mirror image operation)."""
    return {str(-int(p)): c for p, c in sorted(jones.items(), key=lambda kv: -int(kv[0]))}


def match_knot_in_catalog(jones: Dict[str, int], alexander: Dict[str, int]) -> Tuple[str, str]:
    """
    Matches computed polynomials against catalog.
    Returns (knot_id, chirality) where chirality in {"RIGHT_HANDED", "LEFT_HANDED", "ACHIRAL", "UNKNOWN"}.
    """
    for kid, entry in CANONICAL_KNOTS.items():
        if entry["alexander"] == alexander:
            if entry["jones"] == jones:
                chirality = "ACHIRAL" if entry["chirality"] == "ACHIRAL" else "RIGHT_HANDED"
                return kid, chirality
            inv_j = invert_jones(entry["jones"])
            if inv_j == jones:
                return kid, "LEFT_HANDED"

    return "UNKNOWN", "UNKNOWN"
