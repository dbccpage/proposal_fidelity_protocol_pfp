"""Properties of the exact holonomy checker in code/holonomy.py."""

from __future__ import annotations

import itertools
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from holonomy import (  # noqa: E402
    FLAT_NONTRIVIAL,
    FLAT_TRIVIAL,
    NOT_FLAT,
    Connection,
    FiniteGroup,
    GroupTableError,
    Lattice,
    LatticeError,
    check_flatness,
    connection_from_case,
    connection_from_directed_links,
    gauge_transform,
    gauge_trivializes,
    quaternion_group_q8,
    symmetric_group_s3,
    trivial_connection,
    verify_claim,
)

GROUPS = (symmetric_group_s3(), quaternion_group_q8())


def seam_connection(group: FiniteGroup, lattice: Lattice, a: str, b: str) -> Connection:
    """Links (r, M-1) -> (r, 0) carry a, links (L-1, c) -> (0, c) carry b, all others e."""
    links = {}
    for u, v in lattice.positive_edges():
        if u[1] == lattice.cols - 1 and v[1] == 0:
            links[(u, v)] = a
        elif u[0] == lattice.rows - 1 and v[0] == 0:
            links[(u, v)] = b
        else:
            links[(u, v)] = group.identity
    return Connection(group, lattice, links)


def random_connection(group: FiniteGroup, lattice: Lattice, rng: random.Random) -> Connection:
    return Connection(
        group, lattice, {edge: rng.choice(group.elements) for edge in lattice.positive_edges()}
    )


def random_gauge(group: FiniteGroup, lattice: Lattice, rng: random.Random) -> dict:
    return {v: rng.choice(group.elements) for v in lattice.vertices()}


def conjugate(group: FiniteGroup, g: str, x: str) -> str:
    return group.mul(group.mul(g, x), group.inv(g))


def test_package_groups_are_nonabelian_of_orders_6_and_8() -> None:
    s3, q8 = GROUPS
    assert len(s3.elements) == 6 and not s3.is_abelian()
    assert sorted(s3.order_of(a) for a in s3.elements) == [1, 2, 2, 2, 3, 3]
    assert len(q8.elements) == 8 and not q8.is_abelian()
    assert [a for a in q8.elements if q8.order_of(a) == 2] == ["-e"]


def test_constructor_rejects_tables_that_are_not_groups() -> None:
    s3 = symmetric_group_s3()
    inverse = {a: s3.inv(a) for a in s3.elements}
    r3 = next(a for a in s3.elements if s3.order_of(a) == 3)
    swapped = s3.as_table()
    x, y = [b for b in s3.elements if b != s3.identity][:2]
    swapped[r3][x], swapped[r3][y] = swapped[r3][y], swapped[r3][x]
    with pytest.raises(GroupTableError):
        FiniteGroup("swapped", s3.elements, s3.identity, swapped, inverse)
    with pytest.raises(GroupTableError):
        FiniteGroup("bad inverse", s3.elements, s3.identity, s3.as_table(), {**inverse, r3: r3})
    open_table = s3.as_table()
    open_table[r3][r3] = "not an element"
    with pytest.raises(GroupTableError):
        FiniteGroup("not closed", s3.elements, s3.identity, open_table, inverse)


def test_lattice_rejects_degenerate_shapes() -> None:
    with pytest.raises(LatticeError):
        Lattice(2, 5, True)
    with pytest.raises(LatticeError):
        Lattice(1, 5, False)
    with pytest.raises(LatticeError):
        Lattice(True, 3, False)  # type: ignore[arg-type]


def test_trivial_connection_is_flat_trivial() -> None:
    for group in GROUPS:
        for lattice in (Lattice(3, 4, False), Lattice(4, 5, True)):
            report = check_flatness(trivial_connection(group, lattice))
            assert report.verdict == FLAT_TRIVIAL
            assert report.plaquettes == len(lattice.plaquette_origins())
            assert report.skipped_identity_plaquettes == report.plaquettes
            assert report.gauge is not None
            assert all(g == group.identity for _, g in report.gauge)


def test_pure_gauge_connection_is_flat_trivial_with_no_identity_plaquettes() -> None:
    for group in GROUPS:
        lattice = Lattice(4, 5, True)
        n = len(group.elements)
        gauge = {(r, c): group.elements[(r + 2 * c) % n] for r, c in lattice.vertices()}
        connection = gauge_transform(trivial_connection(group, lattice), gauge)
        report = check_flatness(connection)
        assert report.verdict == FLAT_TRIVIAL
        assert report.skipped_identity_plaquettes == 0
        assert report.hol_a == report.hol_b == group.identity
        assert report.gauge is not None
        assert gauge_trivializes(connection, dict(report.gauge))
        assert not gauge_trivializes(connection, {v: group.identity for v in lattice.vertices()})


def test_flat_nontrivial_torus_with_constant_holonomy_around_one_cycle() -> None:
    for group in GROUPS:
        lattice = Lattice(3, 4, True)
        for a in group.elements:
            if a == group.identity:
                continue
            report = check_flatness(seam_connection(group, lattice, a, group.identity))
            assert report.verdict == FLAT_NONTRIVIAL
            assert (report.hol_a, report.hol_b) == (a, group.identity)
            assert report.gauge is None


def test_single_non_identity_link_is_not_flat() -> None:
    for group in GROUPS:
        for lattice in (Lattice(3, 4, False), Lattice(4, 5, True)):
            for a in group.elements:
                if a == group.identity:
                    continue
                links = trivial_connection(group, lattice).links()
                links[((1, 1), (1, 2))] = a
                report = check_flatness(Connection(group, lattice, links))
                assert report.verdict == NOT_FLAT
                assert report.nonflat_plaquettes == 2
                assert report.witness_plaquette == ((0, 1), (1, 1), (1, 2), (0, 2))
                assert report.witness_holonomy == a


def test_flat_cycle_holonomies_commute_on_every_seam_pair() -> None:
    """Exhaustive over G x G: the seam connection is flat exactly when a and b commute."""
    rng = random.Random(10)
    for group in GROUPS:
        lattice = Lattice(3, 4, True)
        gauge = random_gauge(group, lattice, rng)
        g0 = gauge[(0, 0)]
        for a, b in itertools.product(group.elements, repeat=2):
            plain = seam_connection(group, lattice, a, b)
            report = check_flatness(plain)
            moved = check_flatness(gauge_transform(plain, gauge))
            if not group.commute(a, b):
                commutator = group.mul(group.mul(group.mul(b, a), group.inv(b)), group.inv(a))
                assert report.verdict == moved.verdict == NOT_FLAT
                assert report.nonflat_plaquettes == moved.nonflat_plaquettes == 1
                assert report.witness_plaquette == ((2, 3), (0, 3), (0, 0), (2, 0))
                assert report.witness_holonomy == commutator
                continue
            expected = FLAT_TRIVIAL if a == b == group.identity else FLAT_NONTRIVIAL
            assert report.verdict == moved.verdict == expected
            assert (report.hol_a, report.hol_b) == (a, b)
            assert (moved.hol_a, moved.hol_b) == (conjugate(group, g0, a), conjugate(group, g0, b))


def test_orientation_reversal_inverts_plaquette_holonomy() -> None:
    rng = random.Random(17)
    seen_order_sensitive = False
    for group in GROUPS:
        for lattice in (Lattice(3, 4, False), Lattice(3, 3, True)):
            for _ in range(20):
                connection = random_connection(group, lattice, rng)
                for r, c in lattice.plaquette_origins():
                    v0, v1, v2, v3 = lattice.plaquette(r, c)
                    forward = connection.cycle_holonomy((v0, v1, v2, v3))
                    assert forward == connection.plaquette_holonomy(r, c)
                    assert connection.cycle_holonomy((v0, v3, v2, v1)) == group.inv(forward)
                    first = connection.link(v0, v1)
                    rotated = connection.cycle_holonomy((v1, v2, v3, v0))
                    assert rotated == conjugate(group, group.inv(first), forward)
                    seen_order_sensitive |= forward != group.inv(forward)
    assert seen_order_sensitive


def test_identity_skipping_never_changes_the_result() -> None:
    rng = random.Random(23)
    for group in GROUPS:
        for lattice in (Lattice(3, 4, False), Lattice(4, 5, True)):
            candidates = [trivial_connection(group, lattice)]
            for _ in range(10):
                sparse = trivial_connection(group, lattice).links()
                sparse[rng.choice(sorted(sparse))] = rng.choice(group.elements)
                one_link = Connection(group, lattice, sparse)
                candidates += [
                    one_link,
                    gauge_transform(one_link, random_gauge(group, lattice, rng)),
                    random_connection(group, lattice, rng),
                ]
            for connection in candidates:
                fast = check_flatness(connection)
                full = check_flatness(connection, skip_identity_links=False)
                assert full.skipped_identity_plaquettes == 0
                assert fast.nonflat_plaquettes == full.nonflat_plaquettes
                assert fast.verdict == full.verdict
                assert (fast.witness_plaquette, fast.witness_holonomy) == (
                    full.witness_plaquette,
                    full.witness_holonomy,
                )
                assert (fast.hol_a, fast.hol_b, fast.gauge) == (full.hol_a, full.hol_b, full.gauge)


def test_gauge_transformation_conjugates_plaquette_holonomy() -> None:
    rng = random.Random(29)
    for group in GROUPS:
        lattice = Lattice(3, 4, True)
        connection = random_connection(group, lattice, rng)
        gauge = random_gauge(group, lattice, rng)
        moved = gauge_transform(connection, gauge)
        for r, c in lattice.plaquette_origins():
            expected = conjugate(group, gauge[(r, c)], connection.plaquette_holonomy(r, c))
            assert moved.plaquette_holonomy(r, c) == expected


def test_loader_refuses_inconsistent_or_incomplete_links() -> None:
    group = symmetric_group_s3()
    lattice = Lattice(3, 3, False)
    r3 = next(a for a in group.elements if group.order_of(a) == 3)
    directed = {}
    for u, v in lattice.positive_edges():
        directed[f"{u[0]},{u[1]}->{v[0]},{v[1]}"] = group.identity
        directed[f"{v[0]},{v[1]}->{u[0]},{u[1]}"] = group.identity
    loaded = connection_from_directed_links(group, lattice, directed)
    assert check_flatness(loaded).verdict == FLAT_TRIVIAL
    for broken in (
        {**directed, "0,0->0,1": r3},
        {k: v for k, v in directed.items() if k != "0,1->0,0"},
        {**directed, "0,0->2,2": group.identity},
    ):
        with pytest.raises(LatticeError):
            connection_from_directed_links(group, lattice, broken)


def test_verify_claim_checks_certificates_not_labels() -> None:
    group = symmetric_group_s3()
    lattice = Lattice(3, 3, False)
    r3 = next(a for a in group.elements if group.order_of(a) == 3)
    links = trivial_connection(group, lattice).links()
    links[((0, 0), (0, 1))] = r3
    connection = Connection(group, lattice, links)
    canonical = ["0,0", "1,0", "1,1", "0,1"]
    reverse = ["0,0", "0,1", "1,1", "1,0"]
    hol = group.inv(r3)
    assert verify_claim(connection, {"verdict": NOT_FLAT, "plaquette": canonical, "holonomy": hol})[
        0
    ]
    assert verify_claim(connection, {"verdict": NOT_FLAT, "plaquette": reverse, "holonomy": r3})[0]
    assert not verify_claim(
        connection, {"verdict": NOT_FLAT, "plaquette": reverse, "holonomy": hol}
    )[0]
    flat_square = ["1,1", "2,1", "2,2", "1,2"]
    assert not verify_claim(
        connection, {"verdict": NOT_FLAT, "plaquette": flat_square, "holonomy": hol}
    )[0]
    identity_gauge = {f"{r},{c}": group.identity for r, c in lattice.vertices()}
    assert not verify_claim(connection, {"verdict": FLAT_TRIVIAL, "gauge": identity_gauge})[0]
    assert not verify_claim(connection, {"verdict": FLAT_NONTRIVIAL, "loop_a": canonical})[0]
    assert not verify_claim(connection, {"status": "PARSE_ERROR"})[0]
    assert not verify_claim(connection, "NOT_FLAT")[0]

    torus = Lattice(4, 3, True)
    ring = ["0,0", "1,0", "2,0", "3,0"]
    claim = {"verdict": NOT_FLAT, "plaquette": ring, "holonomy": group.identity}
    assert not verify_claim(trivial_connection(group, torus), claim)[0]

    seam = seam_connection(group, torus, r3, group.identity)
    loop_a = ["0,0", "0,1", "0,2", "0,0"]
    assert verify_claim(seam, {"verdict": FLAT_NONTRIVIAL, "loop_a": loop_a, "hol_a": r3})[0]
    assert not verify_claim(seam, {"verdict": FLAT_NONTRIVIAL, "loop_a": loop_a, "hol_a": hol})[0]
    contractible = ["0,0", "1,0", "1,1", "0,1", "0,0"]
    assert not verify_claim(
        seam, {"verdict": FLAT_NONTRIVIAL, "loop_a": contractible, "hol_a": group.identity}
    )[0]


@pytest.mark.parametrize("value", ["unknown", None, [], {}])
@pytest.mark.parametrize("key", ["0,0->0,1", "0,1->0,0"])
def test_unknown_link_values_are_typed_refusals(key: str, value: object) -> None:
    group = symmetric_group_s3()
    lattice = Lattice(2, 2, False)
    directed = {
        f"{u[0]},{u[1]}->{v[0]},{v[1]}": group.identity
        for u, v in lattice.positive_edges()
        for u, v in ((u, v), (v, u))
    }
    directed[key] = value  # type: ignore[assignment]
    with pytest.raises(LatticeError, match="unknown group element"):
        connection_from_directed_links(group, lattice, directed)


@pytest.mark.parametrize("alias", ["00,0->0,1", "0,0->00,1"])
def test_duplicate_parsed_edges_cannot_overwrite_links(alias: str) -> None:
    group = symmetric_group_s3()
    lattice = Lattice(2, 2, False)
    directed = {
        f"{u[0]},{u[1]}->{v[0]},{v[1]}": group.identity
        for u, v in lattice.positive_edges()
        for u, v in ((u, v), (v, u))
    }
    for value in (group.identity, next(a for a in group.elements if a != group.identity)):
        with pytest.raises(LatticeError, match="duplicate parsed edge"):
            connection_from_directed_links(group, lattice, {**directed, alias: value})


def test_duplicate_gauge_vertices_cannot_hide_conflicting_values() -> None:
    group = quaternion_group_q8()
    lattice = Lattice(2, 2, False)
    connection = trivial_connection(group, lattice)
    correct = {f"{r},{c}": group.identity for r, c in lattice.vertices()}
    assert verify_claim(connection, {"verdict": FLAT_TRIVIAL, "gauge": correct})[0]
    # Previously the later spelling silently replaced the conflicting first one.
    bad = {**correct, "0,0": "i", "00,0": group.identity}
    ok, reason = verify_claim(connection, {"verdict": FLAT_TRIVIAL, "gauge": bad})
    assert not ok and "duplicate parsed gauge vertex" in reason


@pytest.mark.parametrize("part", ["elements", "identity", "row", "entry", "inverse"])
def test_malformed_group_shapes_raise_group_table_error(part: str) -> None:
    group = quaternion_group_q8()
    spec: dict = {"name": "Q8", "elements": group.elements, "identity": group.identity,
            "table": group.as_table(), "inverses": {a: group.inv(a) for a in group.elements}}
    if part in ("elements", "identity"):
        spec[part] = None
    elif part == "row":
        spec["table"]["e"] = []  # type: ignore[index]
    elif part == "entry":
        spec["table"]["e"]["e"] = []  # type: ignore[index]
    else:
        spec["inverses"]["e"] = []  # type: ignore[index]
    with pytest.raises(GroupTableError):
        connection_from_case({"group": spec, "boundary": "open", "L": 2, "M": 2, "edges": {}})


def test_missing_case_fields_and_empty_cycle_raise_lattice_error() -> None:
    with pytest.raises(LatticeError):
        connection_from_case({})
    with pytest.raises(LatticeError, match="cycle needs"):
        trivial_connection(quaternion_group_q8(), Lattice(2, 2, False)).cycle_holonomy([])
