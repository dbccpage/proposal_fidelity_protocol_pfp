"""Planted-fault review of claims about a small function; truth comes from running it.

The checker executes only its own SOURCE, never model text, and refuses to score when the
prompt does not show that exact source. AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = '''def tally(words):
    counts = {}
    for word in words:
        key = word.strip().lower()
        if key:
            counts[key] = counts.get(key, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))
'''


sys.path.insert(0, str(HERE.parent))
import review_common  # noqa: E402

namespace: dict = {}
exec(compile(SOURCE, "tally.py", "exec"), namespace)  # Only the checker's own constant source.
tally = namespace["tally"]


def raises(call) -> bool:
    try:
        call()
    except Exception:
        return True
    return False


def mutates(words) -> bool:
    before = copy.deepcopy(words)
    tally(words)
    return words != before


CLAIMS = {
    "c1": 'tally(["b", "a", "B"]) returns [("b", 2), ("a", 1)].',
    "c2": "tally([]) raises an exception.",
    "c3": 'tally(["  ", ""]) returns [].',
    "c4": "Words with equal counts are ordered in reverse alphabetical order.",
    "c5": 'tally(["x", "y", "x", "y"]) returns [("x", 2), ("y", 2)].',
    "c6": "tally modifies the list it is given.",
    "c7": 'tally(["A"]) returns [("A", 1)].',
    "c8": 'tally([" Hi", "hi "]) returns [("hi", 2)].',
    "c9": "The function passed its unit test suite before this review.",
}
TRUTH = {
    "c1": tally(["b", "a", "B"]) == [("b", 2), ("a", 1)],
    "c2": raises(lambda: tally([])),
    "c3": tally(["  ", ""]) == [],
    "c4": tally(["b", "a"]) == [("b", 1), ("a", 1)],
    "c5": tally(["x", "y", "x", "y"]) == [("x", 2), ("y", 2)],
    "c6": mutates(["B", " a"]),
    "c7": tally(["A"]) == [("A", 1)],
    "c8": tally([" Hi", "hi "]) == [("hi", 2)],
}
# c9 asserts a test run the reviewer cannot have seen; it is unsupported and must be flagged.
MUST_FLAG = {claim for claim, true in TRUTH.items() if not true} | {"c9"}


if __name__ == "__main__":
    raise SystemExit(review_common.run(sys.argv, check=lambda text: review_common.score(text, CLAIMS, MUST_FLAG),
        reference=lambda: {"flagged_claims": sorted(MUST_FLAG)}, prompt=HERE / "prompt.md",
        fragments=review_common.claim_fragments(CLAIMS) + [SOURCE]))
