#!/usr/bin/env python3
"""Produce a scoped offline Paper 010 exercise packet with the deposited host."""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import recount_pilots  # noqa: E402
import replay_c017  # noqa: E402
from holonomy import (  # noqa: E402
    FLAT_TRIVIAL,
    Connection,
    Lattice,
    LatticeError,
    check_flatness,
    connection_from_case,
    connection_from_directed_links,
    gauge_transform,
    quaternion_group_q8,
    symmetric_group_s3,
    trivial_connection,
    verify_claim,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def packet() -> dict:
    q8, s3 = quaternion_group_q8(), symmetric_group_s3()
    ordered = q8.product(("i", "j", "-i", "-j"))
    permuted = q8.product(("i", "-i", "j", "-j"))
    require((ordered, permuted) == ("-e", "e"), "Q8 order control failed")

    case = json.loads((ROOT / "code/data/c017/pois_01.json").read_text())
    connection = connection_from_case(case)
    report = check_flatness(connection)
    require(report.witness_plaquette is not None, "C017 non-flat witness missing")
    cycle = report.witness_plaquette
    reverse = (cycle[0], *reversed(cycle[1:]))
    backwards = connection.cycle_holonomy(reverse)
    positive = {"verdict": "NOT_FLAT", "plaquette": [f"{r},{c}" for r, c in reverse],
                "holonomy": backwards}
    negative = {**positive, "holonomy": report.witness_holonomy}
    require(verify_claim(connection, positive)[0], "reversed certificate rejected")
    require(not verify_claim(connection, negative)[0], "wrong product was accepted")

    lattice = Lattice(3, 4, True)
    counts: Counter[str] = Counter()
    by_group = {}
    for group in (s3, q8):
        commuting = 0
        for a, b in itertools.product(group.elements, repeat=2):
            links = {}
            for u, v in lattice.positive_edges():
                value = group.identity
                if u[1] == lattice.cols - 1 and v[1] == 0:
                    value = a
                elif u[0] == lattice.rows - 1 and v[0] == 0:
                    value = b
                links[(u, v)] = value
            verdict = check_flatness(Connection(group, lattice, links)).verdict
            counts[verdict] += 1
            commuting += int(group.commute(a, b))
        by_group[group.name] = {"pairs": len(group.elements) ** 2, "commuting": commuting}
    require(dict(counts) == {"FLAT_TRIVIAL": 2, "FLAT_NONTRIVIAL": 56, "NOT_FLAT": 42},
            "finite seam-family control failed")

    torus = Lattice(4, 5, True)
    trivial = trivial_connection(q8, torus)
    gauge = {(r, c): q8.elements[(r + 2 * c) % 8] for r, c in torus.vertices()}
    moved = gauge_transform(trivial, gauge)
    before, after = check_flatness(trivial), check_flatness(moved)
    require(before.verdict == after.verdict == FLAT_TRIVIAL, "gauge verdict changed")
    require((before.skipped_identity_plaquettes, after.skipped_identity_plaquettes) == (20, 0),
            "gauge-dependent skipping control failed")

    small = Lattice(2, 2, False)
    directed = {f"{u[0]},{u[1]}->{v[0]},{v[1]}": q8.identity
                for u, v in small.positive_edges() for u, v in ((u, v), (v, u))}
    refused = []
    for name, data in (("duplicate_edge", {**directed, "00,0->0,1": "e"}),
                       ("unknown_element", {**directed, "0,0->0,1": "unknown"})):
        try:
            connection_from_directed_links(q8, small, data)
        except LatticeError as error:
            refused.append({"control": name, "type": type(error).__name__, "reason": str(error)})
        else:
            raise ValueError(f"malformed input accepted: {name}")
    identity_gauge = {f"{r},{c}": "e" for r, c in small.vertices()}
    bad_gauge = {**identity_gauge, "0,0": "i", "00,0": "e"}
    accepted, reason = verify_claim(trivial_connection(q8, small),
                                    {"verdict": FLAT_TRIVIAL, "gauge": bad_gauge})
    require(not accepted, "duplicate gauge vertex accepted")
    refused.append({"control": "duplicate_gauge", "accepted": accepted, "reason": reason})

    sources = recount_pilots.verify_source_bytes()
    extracted = recount_pilots.verify_c017_extraction()
    rows = replay_c017.certificate_rows()
    retained = [row[-1] for row in rows if row[-1] is not None]
    require((len(rows), len(retained), sum(retained)) == (25, 15, 10), "C017 replay changed")
    error_records = sum(entry["claim"] is not None
                        and entry["claim"].get("status") == "PARSE_ERROR"
                        for run in replay_c017.load("model_claims.json")["runs"]
                        for entry in run["cases"])
    return {
        "schema": "paper010-study-capstone/v1",
        "scope": "Finite local exercises, C017 payload replay and historical recount; "
                 "no provider, Lean, or C045-C050 checker execution; no learner assessment result.",
        "q8_order": {"ordered": ordered, "permuted": permuted},
        "s3_reversal": {"canonical": report.witness_holonomy, "reversed": backwards,
                        "correct_certificate_accepted": True, "wrong_product_accepted": False},
        "seam_family": {"by_group": by_group, "verdict_counts": dict(counts)},
        "gauge_skipping": {"before": 20, "after": 0, "verdict": after.verdict},
        "malformed_controls": refused,
        "historical_evidence": {"source_files_verified": sources,
                                "c017_extracted_entries_verified": extracted,
                                "table3_recorded_counts": recount_pilots.table3(),
                                "table4_author_annotation_and_prior_baselines":
                                    recount_pilots.table4()},
        "c017_solution_scope": {"recorded_responses": len(rows),
                               "retained_solution_records": len(retained),
                               "parsed_certificates": len(retained) - error_records,
                               "parser_error_records": error_records,
                               "fresh_replay_accepted": sum(retained),
                               "fresh_replay_rejected": len(retained) - sum(retained),
                               "missing_payloads": len(rows) - len(retained),
                               "source": "code/replay_c017.py and code/tests/test_c017_replay.py"},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON path outside the deposit")
    args = parser.parse_args()
    result = packet()
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
        print(f"PASS: scoped capstone packet written to {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
