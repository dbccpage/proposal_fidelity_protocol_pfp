"""Test that all hostile mutations are killed (100% kill rate) by the checkers."""

from __future__ import annotations

import json
from pathlib import Path

from c020_spectral_sequence_double_complex.judge_packet.checkers.exact_checker import (
    check_certificate,
)
from c020_spectral_sequence_double_complex.judge_packet.checkers.independent_checker import (
    independent_check_certificate,
)

MUTATIONS_DIR = Path(__file__).resolve().parent / "mutations"


def test_all_mutations_killed():
    mut_files = sorted(MUTATIONS_DIR.glob("mut_*.json"))
    assert len(mut_files) == 41, f"Expected 41 mutations, found {len(mut_files)}"

    killed = 0
    for mf in mut_files:
        with mf.open(encoding="utf-8") as f:
            data = json.load(f)
        case = data["case"]
        cert = data["certificate"]

        res1 = check_certificate(case, cert)
        res2 = independent_check_certificate(case, cert)

        # Both checkers must reject the corrupt certificate
        assert res1.get("verdict") == "FAIL", f"Checker 1 accepted mutation {mf.name}"
        assert res2.get("verdict") == "FAIL", f"Checker 2 accepted mutation {mf.name}"
        killed += 1

    assert killed == 41


def test_mutation_payloads_are_pairwise_distinct():
    """Padding with copies overstated coverage (2026-09-29 correction removed them)."""
    payloads = [
        json.dumps([data["case"], data["certificate"]], sort_keys=True)
        for data in (
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(MUTATIONS_DIR.glob("mut_*.json"))
        )
    ]
    assert len(payloads) == len(set(payloads)) == 41
