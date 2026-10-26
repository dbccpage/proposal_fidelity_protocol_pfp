"""Replay of five retained C017 cases and of the model certificates recorded for them."""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import replay_c017  # noqa: E402
from holonomy import (  # noqa: E402
    FLAT_NONTRIVIAL,
    FLAT_TRIVIAL,
    NOT_FLAT,
    check_flatness,
    connection_from_case,
    quaternion_group_q8,
    symmetric_group_s3,
    verify_claim,
)

DATA = Path(__file__).resolve().parents[1] / "data" / "c017"
CASES = ("pois_01", "base_01", "base_02", "base_03", "base_13")
EXPECTED = {
    "pois_01": ("S3", 3, 3, False, NOT_FLAT, 4, 3),
    "base_01": ("S3", 3, 4, False, NOT_FLAT, 6, 5),
    "base_02": ("S3", 4, 5, False, FLAT_TRIVIAL, 12, 0),
    "base_03": ("S3", 5, 6, True, FLAT_NONTRIVIAL, 30, 20),
    "base_13": ("Q8", 4, 5, False, NOT_FLAT, 12, 11),
}


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def label(verdict: str | None) -> str | None:
    return FLAT_TRIVIAL if verdict == "PURE_GAUGE" else verdict


def test_case_files_match_recorded_digests() -> None:
    provenance = load("provenance.json")
    assert [entry["file"] for entry in provenance["cases"]] == [f"{n}.json" for n in CASES]
    for entry in provenance["cases"]:
        data = (DATA / entry["file"]).read_bytes()
        assert b"\r\n" not in data  # The packaged copies are the original Git LF bytes.
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        crlf = data.replace(b"\n", b"\r\n")
        assert hashlib.sha256(crlf).hexdigest() == entry["judge_manifest_sha256_crlf"]


def test_host_verdicts_for_the_five_cases() -> None:
    for name, (group, rows, cols, periodic, verdict, plaquettes, skipped) in EXPECTED.items():
        connection = connection_from_case(load(f"{name}.json"))
        lattice = connection.lattice
        assert (connection.group.name, lattice.rows, lattice.cols, lattice.periodic) == (
            group,
            rows,
            cols,
            periodic,
        )
        report = check_flatness(connection)
        assert (report.verdict, report.plaquettes) == (verdict, plaquettes)
        assert report.skipped_identity_plaquettes == skipped
        assert check_flatness(connection, skip_identity_links=False).verdict == verdict


def test_torus_case_has_ten_plaquettes_with_a_non_identity_link() -> None:
    connection = connection_from_case(load("base_03.json"))
    report = check_flatness(connection)
    assert (report.hol_a, report.hol_b, report.nonflat_plaquettes) == ("r", "r2", 0)
    active = [
        (r, c)
        for r, c in connection.lattice.plaquette_origins()
        if any(x != "e" for x in connection.plaquette_links(r, c))
    ]
    assert sorted(active) == sorted({(r, 5) for r in range(5)} | {(4, c) for c in range(6)})
    assert len(active) == 10


def test_case_groups_are_s3_and_q8() -> None:
    assert connection_from_case(load("base_13.json")).group == quaternion_group_q8()
    s3_case = connection_from_case(load("base_03.json")).group
    for name in ("pois_01", "base_01", "base_02"):
        assert connection_from_case(load(f"{name}.json")).group == s3_case
    s3 = symmetric_group_s3()
    isomorphisms = [
        image
        for image in itertools.permutations(s3.elements)
        if all(
            image[s3_case.elements.index(s3_case.mul(a, b))] == s3.mul(image[i], image[j])
            for (i, a), (j, b) in itertools.product(enumerate(s3_case.elements), repeat=2)
        )
    ]
    assert len(isomorphisms) == 6


def test_retained_certificates_agree_with_recorded_outcomes() -> None:
    connections = {name: connection_from_case(load(f"{name}.json")) for name in CASES}
    accepted: dict[str, int] = {}
    checked = 0
    parsed = errors = 0
    for run in load("model_claims.json")["runs"]:
        assert [entry["case"] for entry in run["cases"]] == list(CASES)
        for entry in run["cases"]:
            host = check_flatness(connections[entry["case"]]).verdict
            assert label(entry["harness_expected_verdict"]) == host
            if entry["claim"] is None:
                continue
            errors += int(entry["claim"].get("status") == "PARSE_ERROR")
            parsed += int(entry["claim"].get("status") != "PARSE_ERROR")
            ok, _ = verify_claim(connections[entry["case"]], entry["claim"])
            assert ok is entry["recorded_passed"]
            accepted[run["run"]] = accepted.get(run["run"], 0) + int(ok)
            checked += 1
    assert checked == 15
    assert (parsed, errors) == (13, 2)
    assert accepted == {"arm5_70b": 3, "arm5_sba": 3, "arm6_sba": 4}


def test_recorded_outcomes_for_arms_1_and_2() -> None:
    connections = {name: connection_from_case(load(f"{name}.json")) for name in CASES}
    runs = {run["run"]: run for run in load("model_claims.json")["runs"]}
    summary = {}
    for key in ("arm1", "arm2"):
        entries = runs[key]["cases"]
        assert all(entry["claim"] is None for entry in entries)
        summary[key] = (
            sum(entry["recorded_passed"] for entry in entries),
            sum(
                label(entry["recorded_verdict"])
                == check_flatness(connections[entry["case"]]).verdict
                for entry in entries
            ),
            sum(
                "not a valid canonical elementary plaquette" in entry["recorded_reason"]
                for entry in entries
            ),
        )
    assert summary == {"arm1": (0, 4, 3), "arm2": (0, 2, 2)}


def test_completion_lengths_recorded_for_the_torus_case() -> None:
    runs = {run["run"]: run for run in load("model_claims.json")["runs"]}
    arm5 = next(e for e in runs["arm5_sba"]["cases"] if e["case"] == "base_03")
    arm6 = next(e for e in runs["arm6_sba"]["cases"] if e["case"] == "base_03")
    assert (arm5["completion_tokens"], arm5["claim"], arm5["recorded_passed"]) == (
        8000,
        {"status": "PARSE_ERROR"},
        False,
    )
    assert (arm6["completion_tokens"], arm6["recorded_passed"]) == (2810, True)


def test_replay_script_prints_both_tables(capsys) -> None:
    assert replay_c017.main() == 0
    out = capsys.readouterr().out
    assert "base_03  S3 5x6 periodic" in out and "hol_a=r, hol_b=r2" in out
    assert out.count("not retained") == 10
