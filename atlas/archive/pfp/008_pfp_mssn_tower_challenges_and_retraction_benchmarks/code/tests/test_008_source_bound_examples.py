"""Replay admitted archive bytes and exact teaching calculations, without provider calls."""

from __future__ import annotations

import hashlib
import importlib
import itertools
import json
import math
import sys
from fractions import Fraction
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "docs" / "source_archive"
sys.path.insert(0, str(ROOT / "code"))


@pytest.fixture(scope="module")
def pinned_maps():
    name = "pfp008_mss0_mss1_52cb5457"
    package = ModuleType(name)
    package.__path__ = [str(ARCHIVE / "mss0_mss1_52cb5457")]
    sys.modules[name] = package
    try:
        yield importlib.import_module(name + ".grammar"), importlib.import_module(name + ".updown_maps")
    finally:
        for module_name in list(sys.modules):
            if module_name == name or module_name.startswith(name + "."):
                del sys.modules[module_name]


def test_source_archive_matches_all_admitted_byte_and_git_blob_identities() -> None:
    payload = json.loads((ARCHIVE / "source_index.json").read_text())
    assert len(payload["entries"]) == 13
    for item in payload["entries"]:
        data = (ROOT / item["path"]).read_bytes()
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        assert hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == item["git_blob_sha"]


@pytest.mark.parametrize(("wire", "active0", "active1"), [
    ("<>", True, True), ("<0>", False, True),
    ("<2>", False, False), ("op<<1><0>>", False, True),
])
def test_actual_parser_and_level_admission_are_separate(pinned_maps, wire: str, active0: bool, active1: bool) -> None:
    grammar, _ = pinned_maps
    packet = grammar.parse(wire)
    assert grammar.serialize(packet) == wire
    assert grammar.is_active_at_level(packet, 0) is active0
    assert grammar.is_active_at_level(packet, 1) is active1


def test_actual_old_image_round_trip_and_typed_foreign_refusal(pinned_maps) -> None:
    grammar, maps = pinned_maps
    old = grammar.parse("<>")
    assert maps.d_1(maps.u_0(old)) == old
    foreign = grammar.parse("<1>")
    refused = maps.d_1(foreign)
    assert isinstance(refused, maps.NonDescentReceipt)
    assert refused.original == foreign and refused != old
    with pytest.raises(ValueError):
        maps.u_0(foreign)


def test_down_map_refusal_does_not_certify_upper_level_admission(pinned_maps) -> None:
    grammar, maps = pinned_maps
    foreign = grammar.parse("<2>")
    assert not grammar.is_active_at_level(foreign, 1)
    assert isinstance(maps.d_1(foreign), maps.NonDescentReceipt)


def test_eight_bit_wire_ceiling_is_a_separate_opcode_obligation() -> None:
    def block(level: int) -> range:
        base = 128 + 8 * (level - 22)
        return range(base, base + 8)

    assert list(block(22)) == list(range(128, 136))
    assert list(block(23)) == list(range(136, 144))
    assert list(block(100)) == list(range(752, 760))
    assert max(block(37)) == 255 and min(block(38)) == 256


def test_zero_gap_fixture_still_needs_flow_balance() -> None:
    loads = (1, 0, 0)
    for flows, expected_balanced in (((1, 0, 0), False), ((1, 1, 1), True)):
        dual = sum(c * y for c, y in zip(loads, flows))
        divergence = (flows[2] - flows[0], flows[0] - flows[1], flows[1] - flows[2])
        assert dual == 1 and 1 - dual == 0
        assert all(abs(y) <= 1 for y in flows)
        assert all(value == 0 for value in divergence) is expected_balanced


def test_exact_mcnemar_arithmetic_keeps_the_two_runs_separate() -> None:
    rows = [
        (25, 36, 6, 17, Fraction(145499, 4194304)),
        (25, 19, 6, 0, Fraction(1, 32)),
        (36, 19, 20, 3, Fraction(1, 2048)),
        (38, 4, 34, 0, Fraction(1, 2**33)),
    ]
    for first, second, b, c, expected in rows:
        n = b + c
        p = min(Fraction(1), Fraction(2 * sum(math.comb(n, k) for k in range(min(b, c) + 1)), 2**n))
        assert first - b + c == second
        assert p == expected


def test_graph_certificates_agree_with_an_independent_bounded_potential_search() -> None:
    import retraction_benchmark_runner as runner

    # A connected three-vertex graph with edge claims in [-2,2] needs at most
    # two tree steps from the zero-gauged root, so [-4,4] is a complete bound.
    for claims in itertools.product(range(-2, 3), repeat=3):
        instance = runner.GraphInstance("bounded_triangle", ["A", "B", "C"],
                                        [("A", "B", claims[0]), ("B", "C", claims[1]), ("A", "C", claims[2])], "", "")
        exists = any(b == claims[0] and c - b == claims[1] and c == claims[2]
                     for b, c in itertools.product(range(-4, 5), repeat=2))
        certificate = runner.host_certificate(instance)
        assert (certificate["verdict"] == "CONSISTENT") is exists
        if exists:
            assert runner.verify_potential(instance, certificate["potential"])
        else:
            assert runner.verify_inconsistency_witness(instance, certificate["dual_witness_walk"])
