"""Exact educational replay for the Paper 006 quiz; no production sink or JCS claim."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path


def main() -> None:
    # These intentionally mirror the manuscript's declared storage conversions,
    # not a complete encoder, parser, or production implementation.
    rational = Fraction(2, 6)
    normalized_fraction = f"{rational.numerator}/{rational.denominator}"
    assert normalized_fraction == "1/3"
    normalized_keys = {str(key): value for key, value in {1: "numeric", "1": "text"}.items()}
    assert normalized_keys == {"1": "text"}
    keys = ["\ufb33", "\U0001f600"]
    assert sorted(keys) == keys
    assert sorted(keys, key=lambda key: key.encode("utf-16-be")) == keys[::-1]

    snapshot = Path(__file__).parent / "fixtures/pharmacy_catalog_52cb5457f6c4.json"
    raw = snapshot.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == (
        "b95ce7c1338867cc680abffcc3f2fb9da634c7a7ec2f4c00e0d67391e91b4acb"
    )
    entries = list(json.loads(raw)["antibodies"].values())
    statuses = Counter(entry["pharmacy_status"] for entry in entries)
    placeholders = sum(
        entry["negative_fixture"] == f"# Triggering defect: {entry['target_pattern']}\n"
        and entry["positive_fixture"] == "# Repaired exact state\n"
        for entry in entries
    )
    assert (len(entries), statuses["candidate"], statuses["active"], placeholders) == (61, 56, 5, 49)
    assert len(entries) - placeholders == 12

    pairs = [(True, False)] + [(True, True)] * 2 + [(False, False)] * 3
    pattern_only = sum(s1 and not s2 for s1, s2 in pairs)
    toxicity = Fraction(pattern_only, len(pairs))
    conditional = Fraction(pattern_only, sum(s1 for s1, _ in pairs))
    assert toxicity == Fraction(1, 6) < Fraction(1, 5) < conditional == Fraction(1, 3)
    assert Fraction(1, 1) >= Fraction(1, 5)  # one match / one corpus-mode trigger

    idle_before, idle_after, tau = 4, 12, 5
    intervals = idle_after // tau - idle_before // tau
    score = Fraction(4, 5) / 2**intervals
    assert (intervals, score, idle_after < 10) == (2, Fraction(1, 5), False)
    idle = 0
    batch_score = Fraction(1)
    increments = []
    for elapsed in (3, 4, 5):
        after = idle + elapsed
        increment = after // 5 - idle // 5
        increments.append(increment)
        batch_score /= 2**increment
        idle = after
    assert increments == [0, 1, 1]
    assert batch_score == Fraction(1, 4) == Fraction(1) / 2 ** (12 // 5)
    assert Fraction(1, 4) + Fraction(1, 5) == Fraction(9, 20)
    assert Fraction(3, 7) / 2 ** (17 // 4) == Fraction(3, 112)
    assert Fraction(3, 112) + Fraction(1, 5) == Fraction(127, 560)
    accumulated_bytes = 1000 * 100 * 101 // 2
    assert accumulated_bytes == 5_050_000

    print(json.dumps({
        "scope": "exact educational calculations and pinned catalog census only",
        "normalization_key_result": normalized_keys,
        "catalog_entries": len(entries),
        "non_placeholder_entries": len(entries) - placeholders,
        "active_label_fraction": str(Fraction(statuses["active"], len(entries))),
        "placeholder_fraction": str(Fraction(placeholders, len(entries))),
        "explicit_toxicity": str(toxicity),
        "conditional_pattern_only": str(conditional),
        "decayed_score": str(score),
        "batch_interval_increments": increments,
        "batch_score": str(batch_score),
        "stimulated_score": str(Fraction(9, 20)),
        "accumulated_entry_bytes": accumulated_bytes,
        "final_entry_bytes": 100_000,
    }, indent=2))


if __name__ == "__main__":
    main()
