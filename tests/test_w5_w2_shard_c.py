"""Verification suite for Window 5 Wave 2 Shard C (Paper 010 Part 2).

AuthorityEffect: None.

Targets four audit derivations in Paper 010 (code/holonomy.py):
1. AUDIT-P010-006 (ATL-P010-006): Plaquette orientation identities (reversal
   inverts W -> W^{-1}, starting-vertex shift conjugates W -> P_k^{-1} W P_k,
   and order >= 3 witnesses W != W^{-1} in S_3 and Q_8).
2. AUDIT-P010-007 (ATL-P010-007): Gauge covariance of plaquette products
   (W'_{r,c} = g_{v_0} W_{r,c} g_{v_0}^{-1} at first vertex v_0 = (r, c),
   preserving local flatness W_{r,c} = e iff W'_{r,c} = e).
3. AUDIT-P010-011 (ATL-P010-011): Single interior non-identity link defect
   gives NOT_FLAT with nonflat_plaquettes == 2, contrasted with open-boundary
   1-plaquette defects and torus surface cancellation into [G, G].
4. AUDIT-P010-013 (ATL-P010-013): 3x4 torus seam family over S_3 x S_3 and
   Q_8 x Q_8 is flat iff ab = ba, with cycle products (a, b) conjugated
   simultaneously by g_{(0,0)} and corner commutator b a b^{-1} a^{-1}.
"""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PFP010_ROOT = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "010_pfp_holonomy_checks_and_model_pilots"
)
_HOLONOMY_PATH = _PFP010_ROOT / "code" / "holonomy.py"
_CHECKER_TEST_PATH = _PFP010_ROOT / "code" / "tests" / "test_holonomy_checker.py"
_RECOUNT_PILOTS_PATH = _PFP010_ROOT / "code" / "recount_pilots.py"
_REPLAY_C017_PATH = _PFP010_ROOT / "code" / "replay_c017.py"
_STUDY_CAPSTONE_PATH = _PFP010_ROOT / "tools" / "study_capstone.py"

_REVIEW_JSON_PATH = _REPO_ROOT / "dag" / "reviews" / "additional_w5_w2_shard_c.json"
_INVENTORY_JSON_PATH = _REPO_ROOT / "dag" / "file_inventory.json"
_DERIVATION_PATHS = (
    _REPO_ROOT / "dag" / "derivations" / "audit_p010_006.md",
    _REPO_ROOT / "dag" / "derivations" / "audit_p010_007.md",
    _REPO_ROOT / "dag" / "derivations" / "audit_p010_011.md",
    _REPO_ROOT / "dag" / "derivations" / "audit_p010_013.md",
)

_HOLONOMY_MOD_KEY = "holonomy"
_CHECKER_MOD_KEY = "_w5_w2_shard_c_holonomy_checker"


def _exec_file_module(module_name: str, file_path: Path) -> Any:
    """Load a Python module from disk without writing bytecode."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to build module spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _isolated_shard_c_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[None]:
    """Enforce bytecode suppression, tmp_path isolation, and zero sys.modules leaks."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    tmp_str = str(tmp_path)
    monkeypatch.setenv("TMPDIR", tmp_str)
    monkeypatch.setenv("TEMP", tmp_str)
    monkeypatch.setenv("TMP", tmp_str)
    monkeypatch.setattr(tempfile, "tempdir", tmp_str)

    orig_sys_path = list(sys.path)
    orig_sys_modules = dict(sys.modules)
    try:
        _exec_file_module(_HOLONOMY_MOD_KEY, _HOLONOMY_PATH)
        _exec_file_module(_CHECKER_MOD_KEY, _CHECKER_TEST_PATH)
        # Restore sys.path immediately after test_holonomy_checker's sys.path.insert
        sys.path[:] = orig_sys_path
        yield
    finally:
        sys.path[:] = orig_sys_path
        for added_key in list(sys.modules.keys()):
            if added_key not in orig_sys_modules:
                sys.modules.pop(added_key, None)
        for key, prev_mod in orig_sys_modules.items():
            if sys.modules.get(key) is not prev_mod:
                sys.modules[key] = prev_mod


def _hol() -> Any:
    return sys.modules[_HOLONOMY_MOD_KEY]


def _chk() -> Any:
    return sys.modules[_CHECKER_MOD_KEY]


def _format_cycle(cycle: tuple[tuple[int, int], ...]) -> list[str]:
    return [f"{r},{c}" for r, c in cycle]


def _interior_positive_edges(lattice: Any) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Return all non-boundary positive edges of an open or periodic lattice."""
    if lattice.periodic:
        return list(lattice.positive_edges())
    interior: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for u, v in lattice.positive_edges():
        if u[0] == v[0] and 1 <= u[0] <= lattice.rows - 2:
            # Horizontal edge (r, c) -> (r, c + 1): interior iff 1 <= r <= L - 2
            interior.append((u, v))
        elif u[0] != v[0] and 1 <= u[1] <= lattice.cols - 2:
            # Vertical edge (r, c) -> (r + 1, c): interior iff 1 <= c <= M - 2
            interior.append((u, v))
    return interior


def _boundary_positive_edges(lattice: Any) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Return all boundary positive edges of a lattice (empty when periodic=True)."""
    interior_set = set(_interior_positive_edges(lattice))
    return [edge for edge in lattice.positive_edges() if edge not in interior_set]


# ---------------------------------------------------------------------------
# 1. AUDIT-P010-006: Plaquette orientation identities
# ---------------------------------------------------------------------------


def _eight_dihedral_listings(
    cycle: tuple[tuple[int, int], ...],
) -> set[tuple[tuple[int, int], ...]]:
    """Return the 8 dihedral boundary listings of a single plaquette cycle."""
    out: set[tuple[tuple[int, int], ...]] = set()
    for turned in (cycle, tuple(reversed(cycle))):
        for k in range(4):
            out.add(turned[k:] + turned[:k])
    return out


class TestPlaquetteOrientationIdentities:
    """Verifies AUDIT-P010-006 (ATL-P010-006): reversal, shift conjugation, S_3/Q_8."""

    def test_exhaustive_2x2_s3_and_q8_dihedral_plaquette_identities_and_counts(
        self,
    ) -> None:
        """Exhaust all 1,296 S_3 and 4,096 Q_8 2x2 connections across 8 listings."""
        hol = _hol()
        chk = _chk()
        lattice = hol.Lattice(2, 2, False)
        pos_edges = lattice.positive_edges()
        assert len(pos_edges) == 4

        canonical_cycle = lattice.plaquette(0, 0)
        v0, v1, v2, v3 = canonical_cycle
        reversed_base_cycle = (v0, v3, v2, v1)
        dihedral_listings = _eight_dihedral_listings(canonical_cycle)
        assert len(dihedral_listings) == 8
        assert hol._plaquette_listings(lattice) == dihedral_listings

        expected_census = {
            "S3": (hol.symmetric_group_s3(), 1296, 216, 648, 432),
            "Q8": (hol.quaternion_group_q8(), 4096, 512, 512, 3072),
        }

        for label, (group, exp_total, exp_flat, exp_order2, exp_nonself) in (
            expected_census.items()
        ):
            total = 0
            flat_count = 0
            order2_nonflat_count = 0
            nonself_inverse_count = 0

            for values in itertools.product(group.elements, repeat=4):
                total += 1
                links = dict(zip(pos_edges, values, strict=True))
                conn = hol.Connection(group, lattice, links)

                w = conn.plaquette_holonomy(0, 0)
                w_inv = group.inv(w)
                step_factors = conn.plaquette_links(0, 0)

                # 1. Basepoint-preserving orientation reversal gives W^{-1}
                w_rev = conn.cycle_holonomy(reversed_base_cycle)
                assert w_rev == w_inv, f"{label}: reversal mismatch on {values}"

                # 2. Every k-step forward shift conjugates W by prefix P_k
                prefix = group.identity
                forward_shifts: list[str] = []
                for k in range(4):
                    shifted_cycle = canonical_cycle[k:] + canonical_cycle[:k]
                    w_k = conn.cycle_holonomy(shifted_cycle)
                    expected_wk = group.mul(group.mul(group.inv(prefix), w), prefix)
                    assert w_k == expected_wk
                    forward_shifts.append(w_k)
                    prefix = group.mul(prefix, step_factors[k])

                # Special case k = 1: u_0^{-1} W u_0
                u0 = conn.link(v0, v1)
                assert forward_shifts[1] == chk.conjugate(group, group.inv(u0), w)

                # 3. All 8 dihedral listings evaluate to e iff W == e
                for listed in dihedral_listings:
                    listed_hol = conn.cycle_holonomy(listed)
                    assert (listed_hol == group.identity) is (w == group.identity)

                # 4. Census partition: flat (ord 1), order-2 self-inverse, ord >= 3
                if w == group.identity:
                    flat_count += 1
                elif w == w_inv:
                    order2_nonflat_count += 1
                else:
                    nonself_inverse_count += 1

            assert total == exp_total
            assert flat_count == exp_flat
            assert order2_nonflat_count == exp_order2
            assert nonself_inverse_count == exp_nonself

    def test_periodic_3x3_s3_and_q8_all_eight_listings_and_verify_claim_acceptance(
        self,
    ) -> None:
        """Verify all 8 dihedral listings and verify_claim acceptance on 3x3 tori."""
        hol = _hol()
        torus = hol.Lattice(3, 3, True)
        all_torus_listings = hol._plaquette_listings(torus)
        assert len(all_torus_listings) == 9 * 8

        cases = (
            (hol.symmetric_group_s3(), "021", "120"),
            (hol.quaternion_group_q8(), "j", "i"),
        )
        for group, u0_val, u1_val in cases:
            links = {edge: group.identity for edge in torus.positive_edges()}
            links[((1, 2), (2, 2))] = u0_val
            links[((2, 2), (2, 0))] = u1_val
            if group.name == "S3":
                links[((2, 2), (2, 0))] = "021"
                links[((1, 0), (2, 0))] = "201"
            conn = hol.Connection(group, torus, links)

            origin_cycle = torus.plaquette(1, 2)
            w = conn.plaquette_holonomy(1, 2)
            assert w != group.identity
            assert w != group.inv(w)
            shifted_1 = origin_cycle[1:] + origin_cycle[:1]
            assert conn.cycle_holonomy(shifted_1) != w

            eight_listings = _eight_dihedral_listings(origin_cycle)
            assert len(eight_listings) == 8
            assert eight_listings.issubset(all_torus_listings)
            for listed in eight_listings:
                expected_hol = conn.cycle_holonomy(listed)
                accepted, reason = hol.verify_claim(
                    conn,
                    {
                        "verdict": hol.NOT_FLAT,
                        "plaquette": _format_cycle(listed),
                        "holonomy": expected_hol,
                    },
                )
                assert accepted is True, reason

    def test_falsification_verify_claim_rejects_uninverted_reversal_and_unconjugated_shift(
        self,
    ) -> None:
        """Negative controls: verify_claim rejects uninverted/unconjugated products."""
        hol = _hol()
        chk = _chk()
        lattice = hol.Lattice(2, 2, False)
        canonical = lattice.plaquette(0, 0)
        v0, v1, v2, v3 = canonical
        reversed_cycle = (v0, v3, v2, v1)
        shifted_cycle = (v1, v2, v3, v0)
        crossed_non_plaquette = (v0, v2, v1, v3)

        # 1. Reversal negative control on S_3 ("120" != "201") and Q_8 ("i" != "-i")
        for group, edge_elem in (
            (hol.symmetric_group_s3(), "120"),
            (hol.quaternion_group_q8(), "i"),
        ):
            links = {edge: group.identity for edge in lattice.positive_edges()}
            links[(v0, v1)] = edge_elem
            conn = hol.Connection(group, lattice, links)
            w = conn.plaquette_holonomy(0, 0)
            assert w == edge_elem
            assert group.inv(w) != w

            ok_rev, msg_rev = hol.verify_claim(
                conn,
                {
                    "verdict": hol.NOT_FLAT,
                    "plaquette": _format_cycle(reversed_cycle),
                    "holonomy": w,
                },
            )
            assert ok_rev is False
            assert "stated holonomy" in msg_rev

        # 2. Shift directionality control in S_3: u_0 = "120" (order 3), u_1 = "021"
        s3 = hol.symmetric_group_s3()
        s3_links = {edge: s3.identity for edge in lattice.positive_edges()}
        s3_links[(v0, v1)] = "120"
        s3_links[(v1, v2)] = "021"
        s3_conn = hol.Connection(s3, lattice, s3_links)
        w_s3 = s3_conn.plaquette_holonomy(0, 0)
        right_conj = chk.conjugate(s3, s3.inv("120"), w_s3)
        wrong_dir_conj = chk.conjugate(s3, "120", w_s3)
        assert len({w_s3, right_conj, wrong_dir_conj}) == 3

        for wrong_hol in (w_s3, wrong_dir_conj):
            accepted, reason = hol.verify_claim(
                s3_conn,
                {
                    "verdict": hol.NOT_FLAT,
                    "plaquette": _format_cycle(shifted_cycle),
                    "holonomy": wrong_hol,
                },
            )
            assert accepted is False
            assert "stated holonomy" in reason

        accepted_good, reason_good = hol.verify_claim(
            s3_conn,
            {
                "verdict": hol.NOT_FLAT,
                "plaquette": _format_cycle(shifted_cycle),
                "holonomy": right_conj,
            },
        )
        assert accepted_good is True, reason_good

        # 3. Shift negative control in Q_8: u_0 = "j", u_1 = "k" -> W = "i", shifted = "-i"
        q8 = hol.quaternion_group_q8()
        q8_links = {edge: q8.identity for edge in lattice.positive_edges()}
        q8_links[(v0, v1)] = "j"
        q8_links[(v1, v2)] = "k"
        q8_conn = hol.Connection(q8, lattice, q8_links)
        w_q8 = q8_conn.plaquette_holonomy(0, 0)
        assert w_q8 == "i"
        assert q8_conn.cycle_holonomy(shifted_cycle) == "-i"

        ok_shift_q8, msg_shift_q8 = hol.verify_claim(
            q8_conn,
            {
                "verdict": hol.NOT_FLAT,
                "plaquette": _format_cycle(shifted_cycle),
                "holonomy": w_q8,
            },
        )
        assert ok_shift_q8 is False
        assert "stated holonomy" in msg_shift_q8

        # 4. Crossed 4-vertex walk is rejected as non-plaquette
        ok_cross, msg_cross = hol.verify_claim(
            q8_conn,
            {
                "verdict": hol.NOT_FLAT,
                "plaquette": _format_cycle(crossed_non_plaquette),
                "holonomy": "-i",
            },
        )
        assert ok_cross is False
        assert "not a plaquette boundary" in msg_cross


# ---------------------------------------------------------------------------
# 2. AUDIT-P010-007: Gauge covariance of plaquette products
# ---------------------------------------------------------------------------


class TestGaugeCovariancePlaquetteProducts:
    """Verifies AUDIT-P010-007 (ATL-P010-007): W'_{r,c} = g_{v_0} W_{r,c} g_{v_0}^{-1}."""

    def test_exhaustive_s3_and_q8_plaquette_and_path_gauge_covariance(self) -> None:
        """Exhaust 2x2 S_3 and Q_8 connections across basepoint gauges and full S_3^4 gauges."""
        hol = _hol()
        chk = _chk()
        lattice = hol.Lattice(2, 2, False)
        pos_edges = lattice.positive_edges()
        vertices = lattice.vertices()
        open_path = ((0, 0), (1, 0), (1, 1), (0, 1))

        s3 = hol.symmetric_group_s3()
        q8 = hol.quaternion_group_q8()

        # Part A: All 1,296 S_3 connections x all 6 basepoint values (with non-constant neighbors)
        for values in itertools.product(s3.elements, repeat=4):
            conn = hol.Connection(s3, lattice, dict(zip(pos_edges, values, strict=True)))
            w = conn.plaquette_holonomy(0, 0)
            p_hol = conn.path_holonomy(open_path)
            for idx, g0 in enumerate(s3.elements):
                gauge = {
                    (0, 0): g0,
                    (1, 0): s3.elements[(idx + 1) % 6],
                    (1, 1): s3.elements[(idx + 3) % 6],
                    (0, 1): s3.elements[(idx + 5) % 6],
                }
                moved = hol.gauge_transform(conn, gauge)
                assert moved.plaquette_holonomy(0, 0) == chk.conjugate(s3, g0, w)
                assert moved.path_holonomy(open_path) == s3.mul(
                    s3.mul(g0, p_hol),
                    s3.inv(gauge[(0, 1)]),
                )

        # Part B: Exhaust all 6^4 = 1,296 full vertex gauges in S_3^V on representative connections
        rep_s3_link_tuples = (
            ("012", "012", "012", "012"),
            ("021", "012", "012", "012"),
            ("120", "021", "210", "201"),
        )
        for link_tuple in rep_s3_link_tuples:
            conn = hol.Connection(s3, lattice, dict(zip(pos_edges, link_tuple, strict=True)))
            w = conn.plaquette_holonomy(0, 0)
            for gauge_tuple in itertools.product(s3.elements, repeat=4):
                gauge = dict(zip(vertices, gauge_tuple, strict=True))
                moved = hol.gauge_transform(conn, gauge)
                # Verify reversed-edge covariance U'_{vu} = g_v U_{vu} g_u^{-1}
                for u, v in pos_edges:
                    expected_rev = s3.mul(
                        s3.mul(gauge[v], conn.link(v, u)),
                        s3.inv(gauge[u]),
                    )
                    assert moved.link(v, u) == expected_rev
                assert moved.plaquette_holonomy(0, 0) == chk.conjugate(s3, gauge[(0, 0)], w)

        # Part C: All 4,096 Q_8 connections x all 8 basepoint values (32,768 pairs)
        for values in itertools.product(q8.elements, repeat=4):
            conn = hol.Connection(q8, lattice, dict(zip(pos_edges, values, strict=True)))
            w = conn.plaquette_holonomy(0, 0)
            p_hol = conn.path_holonomy(open_path)
            for idx, g0 in enumerate(q8.elements):
                gauge = {
                    (0, 0): g0,
                    (1, 0): q8.elements[(idx + 2) % 8],
                    (1, 1): q8.elements[(idx + 5) % 8],
                    (0, 1): q8.elements[(idx + 7) % 8],
                }
                moved = hol.gauge_transform(conn, gauge)
                assert moved.plaquette_holonomy(0, 0) == chk.conjugate(q8, g0, w)
                assert moved.path_holonomy(open_path) == q8.mul(
                    q8.mul(g0, p_hol),
                    q8.inv(gauge[(0, 1)]),
                )

    def test_periodic_torus_s3_and_q8_flatness_invariance_and_noncentral_conjugation(
        self,
    ) -> None:
        """Verify W=e <=> W'=e, FlatnessReport invariance, and non-central conjugation on tori."""
        hol = _hol()
        chk = _chk()
        torus = hol.Lattice(3, 4, True)

        for group in (hol.symmetric_group_s3(), hol.quaternion_group_q8()):
            elems = group.elements
            gauge = {
                (r, c): elems[(2 * r + 3 * c + 1) % len(elems)]
                for r, c in torus.vertices()
            }

            # Build trivial, flat-nontrivial, single-defect, and seam-defect connections
            nontrivial_elem = "120" if group.name == "S3" else "i"
            other_noncomm = "021" if group.name == "S3" else "j"

            single_defect_links = {edge: group.identity for edge in torus.positive_edges()}
            single_defect_links[((1, 1), (1, 2))] = other_noncomm

            connections = (
                hol.trivial_connection(group, torus),
                chk.seam_connection(group, torus, nontrivial_elem, nontrivial_elem),
                hol.Connection(group, torus, single_defect_links),
                chk.seam_connection(group, torus, nontrivial_elem, other_noncomm),
            )

            for conn in connections:
                moved = hol.gauge_transform(conn, gauge)
                rep_before = hol.check_flatness(conn)
                rep_after = hol.check_flatness(moved)

                assert rep_before.verdict == rep_after.verdict
                assert rep_before.nonflat_plaquettes == rep_after.nonflat_plaquettes
                assert rep_before.witness_plaquette == rep_after.witness_plaquette

                for r, c in torus.plaquette_origins():
                    w_before = conn.plaquette_holonomy(r, c)
                    w_after = moved.plaquette_holonomy(r, c)
                    assert w_after == chk.conjugate(group, gauge[(r, c)], w_before)
                    assert (w_before == group.identity) is (w_after == group.identity)

            # Confirm non-central plaquette value changes when g_{v_0} does not commute with W
            defect_conn = hol.Connection(group, torus, single_defect_links)
            # Plaquette (0, 1) has product other_noncomm ("021" in S_3, "j" in Q_8)
            assert defect_conn.plaquette_holonomy(0, 1) == other_noncomm
            noncomm_gauge = {v: group.identity for v in torus.vertices()}
            noncomm_gauge[(0, 1)] = nontrivial_elem
            moved_defect = hol.gauge_transform(defect_conn, noncomm_gauge)
            assert moved_defect.plaquette_holonomy(0, 1) != other_noncomm
            assert moved_defect.plaquette_holonomy(0, 1) == chk.conjugate(
                group,
                nontrivial_elem,
                other_noncomm,
            )

        # Confirm skipped_identity_plaquettes is NOT gauge-invariant (20 -> 0 on 4x5 Q_8)
        q8 = hol.quaternion_group_q8()
        torus_4x5 = hol.Lattice(4, 5, True)
        triv_4x5 = hol.trivial_connection(q8, torus_4x5)
        pure_gauge = {
            (r, c): q8.elements[(r + 2 * c) % 8] for r, c in torus_4x5.vertices()
        }
        moved_4x5 = hol.gauge_transform(triv_4x5, pure_gauge)
        assert hol.check_flatness(triv_4x5).skipped_identity_plaquettes == 20
        assert hol.check_flatness(moved_4x5).skipped_identity_plaquettes == 0
        assert hol.check_flatness(moved_4x5).verdict == hol.FLAT_TRIVIAL

    def test_falsification_malformed_gauge_unconjugated_witness_and_uninverted_right_factor(
        self,
    ) -> None:
        """Negative controls: malformed gauge, unconjugated witness, and missing inverse."""
        hol = _hol()
        chk = _chk()
        lattice = hol.Lattice(3, 3, True)

        for group, w_elem, g0_elem, g1_elem in (
            (hol.symmetric_group_s3(), "021", "120", "012"),
            (hol.quaternion_group_q8(), "i", "j", "e"),
        ):
            triv = hol.trivial_connection(group, lattice)

            # 1. Incomplete gauge and unknown group symbol raise LatticeError
            partial_gauge = {v: group.identity for v in lattice.vertices() if v != (0, 0)}
            with pytest.raises(hol.LatticeError, match="gauge must assign"):
                hol.gauge_transform(triv, partial_gauge)

            bad_symbol_gauge = {v: group.identity for v in lattice.vertices()}
            bad_symbol_gauge[(0, 0)] = "INVALID_ELEMENT"
            with pytest.raises(hol.LatticeError, match="group element"):
                hol.gauge_transform(triv, bad_symbol_gauge)

            # 2. verify_claim rejects untransformed W and wrong-vertex conjugation after gauge
            links = {edge: group.identity for edge in lattice.positive_edges()}
            links[((0, 0), (1, 0))] = w_elem
            conn = hol.Connection(group, lattice, links)
            assert conn.plaquette_holonomy(0, 0) == w_elem

            gauge = {v: group.identity for v in lattice.vertices()}
            gauge[(0, 0)] = g0_elem
            gauge[(1, 0)] = g1_elem
            moved = hol.gauge_transform(conn, gauge)
            conj_w = chk.conjugate(group, g0_elem, w_elem)
            assert conj_w != w_elem

            plaq_str = _format_cycle(lattice.plaquette(0, 0))
            ok_raw, msg_raw = hol.verify_claim(
                moved,
                {"verdict": hol.NOT_FLAT, "plaquette": plaq_str, "holonomy": w_elem},
            )
            assert ok_raw is False
            assert "stated holonomy" in msg_raw

            ok_conj, msg_conj = hol.verify_claim(
                moved,
                {"verdict": hol.NOT_FLAT, "plaquette": plaq_str, "holonomy": conj_w},
            )
            assert ok_conj is True, msg_conj

            # 3. Corrupting U'_{uv} = g_u U_{uv} g_v^{-1} to uninverted g_u U_{uv} g_v
            # breaks telescoping on trivial_connection when ord(g_v) >= 3 (g_v^2 != e)
            corrupt_gauge = {v: group.identity for v in lattice.vertices()}
            corrupt_gauge[(1, 0)] = g0_elem  # order 3 in S_3, order 4 in Q_8 -> g^2 != e
            corrupted_links = {
                (u, v): group.mul(
                    group.mul(corrupt_gauge[u], triv.link(u, v)),
                    corrupt_gauge[v],
                )
                for u, v in lattice.positive_edges()
            }
            corrupted_conn = hol.Connection(group, lattice, corrupted_links)
            corrupted_report = hol.check_flatness(corrupted_conn)
            assert corrupted_report.verdict == hol.NOT_FLAT
            assert corrupted_report.nonflat_plaquettes > 0


# ---------------------------------------------------------------------------
# 3. AUDIT-P010-011: Single interior defect
# ---------------------------------------------------------------------------


class TestSingleInteriorDefect:
    """Verifies AUDIT-P010-011 (ATL-P010-011): interior single-link coboundary == 2."""

    def test_exhaustive_interior_single_link_defects_open_and_periodic_s3_and_q8(
        self,
    ) -> None:
        """Exhaust every interior edge and every a != e across open and periodic lattices."""
        hol = _hol()
        lattices = (
            hol.Lattice(3, 4, False),  # 7 interior positive edges
            hol.Lattice(4, 4, False),  # 12 interior positive edges
            hol.Lattice(3, 3, True),   # 18 interior positive edges
            hol.Lattice(3, 4, True),   # 24 interior positive edges
            hol.Lattice(4, 5, True),   # 40 interior positive edges
        )
        expected_interior_counts = (7, 12, 18, 24, 40)

        for lattice, exp_int_count in zip(lattices, expected_interior_counts, strict=True):
            int_edges = _interior_positive_edges(lattice)
            assert len(int_edges) == exp_int_count
            total_plaquettes = len(lattice.plaquette_origins())

            for group in (hol.symmetric_group_s3(), hol.quaternion_group_q8()):
                non_identity = [a for a in group.elements if a != group.identity]
                for edge_0 in int_edges:
                    u, v = edge_0
                    is_horizontal = u[0] == v[0]
                    if is_horizontal:
                        r, c = u
                        p_plus = ((r - 1) % lattice.rows, c)
                        p_minus = (r, c)
                    else:
                        r, c = u
                        p_plus = (r, c)
                        p_minus = (r, (c - 1) % lattice.cols)
                    assert p_plus != p_minus

                    first_origin = min(p_plus, p_minus)

                    for a in non_identity:
                        links = {e: group.identity for e in lattice.positive_edges()}
                        links[edge_0] = a
                        conn = hol.Connection(group, lattice, links)
                        report = hol.check_flatness(conn)

                        assert report.verdict == hol.NOT_FLAT
                        assert report.nonflat_plaquettes == 2
                        assert report.skipped_identity_plaquettes == total_plaquettes - 2
                        assert conn.plaquette_holonomy(*p_plus) == a
                        assert conn.plaquette_holonomy(*p_minus) == group.inv(a)

                        expected_first_hol = (
                            a if first_origin == p_plus else group.inv(a)
                        )
                        assert report.witness_plaquette == lattice.plaquette(*first_origin)
                        assert report.witness_holonomy == expected_first_hol

                        nonflat_found = [
                            origin
                            for origin in lattice.plaquette_origins()
                            if conn.plaquette_holonomy(*origin) != group.identity
                        ]
                        assert set(nonflat_found) == {p_plus, p_minus}

    def test_torus_abelianized_surface_cancellation_excludes_noncommutator_sole_defect(
        self,
    ) -> None:
        """Verify torus surface cancellation in G/[G, G] across S_3, Q_8, and abelian Z_3."""
        hol = _hol()
        s3 = hol.symmetric_group_s3()
        q8 = hol.quaternion_group_q8()
        z3 = hol.FiniteGroup(
            name="Z3",
            elements=("0", "1", "2"),
            identity="0",
            table={
                "0": {"0": "0", "1": "1", "2": "2"},
                "1": {"0": "1", "1": "2", "2": "0"},
                "2": {"0": "2", "1": "0", "2": "1"},
            },
            inverse={"0": "0", "1": "2", "2": "1"},
        )
        assert z3.is_abelian() is True

        # Homomorphisms onto G / [G, G]
        s3_sign = {"012": 1, "120": 1, "201": 1, "021": -1, "102": -1, "210": -1}
        q8_klein = {
            "e": (0, 0),
            "-e": (0, 0),
            "i": (1, 0),
            "-i": (1, 0),
            "j": (0, 1),
            "-j": (0, 1),
            "k": (1, 1),
            "-k": (1, 1),
        }

        torus = hol.Lattice(3, 3, True)
        pos_edges = torus.positive_edges()

        # 1. Zero single-link torus connections produce nonflat_plaquettes == 1
        for group in (s3, q8, z3):
            for edge_0 in pos_edges:
                for a in group.elements:
                    if a == group.identity:
                        continue
                    links = {e: group.identity for e in pos_edges}
                    links[edge_0] = a
                    rep = hol.check_flatness(hol.Connection(group, torus, links))
                    assert rep.nonflat_plaquettes == 2

        # 2. Multi-link sweep: abelianized product of all 9 plaquettes is always trivial
        for seed_idx in range(64):
            s3_links = {
                edge: s3.elements[(seed_idx + 5 * idx + idx * idx) % 6]
                for idx, edge in enumerate(pos_edges)
            }
            s3_conn = hol.Connection(s3, torus, s3_links)
            parity_prod = 1
            for r, c in torus.plaquette_origins():
                parity_prod *= s3_sign[s3_conn.plaquette_holonomy(r, c)]
            assert parity_prod == 1

            q8_links = {
                edge: q8.elements[(seed_idx + 3 * idx + 2 * idx * idx) % 8]
                for idx, edge in enumerate(pos_edges)
            }
            q8_conn = hol.Connection(q8, torus, q8_links)
            coset_xor = [0, 0]
            for r, c in torus.plaquette_origins():
                kx, ky = q8_klein[q8_conn.plaquette_holonomy(r, c)]
                coset_xor[0] ^= kx
                coset_xor[1] ^= ky
            assert tuple(coset_xor) == (0, 0)

            z3_links = {
                edge: z3.elements[(seed_idx + 2 * idx + idx * idx) % 3]
                for idx, edge in enumerate(pos_edges)
            }
            z3_conn = hol.Connection(z3, torus, z3_links)
            z3_rep = hol.check_flatness(z3_conn)
            mod_sum = sum(
                int(z3_conn.plaquette_holonomy(r, c))
                for r, c in torus.plaquette_origins()
            )
            assert mod_sum % 3 == 0
            # On an abelian torus, nonflat_plaquettes == 1 can never occur
            assert z3_rep.nonflat_plaquettes != 1

        # 3. Exhaustive 3^6 = 729 6-edge active patch on Z_3 3x3 torus confirms nonflat != 1
        active_edges = pos_edges[:6]
        for vals in itertools.product(z3.elements, repeat=6):
            links = {e: "0" for e in pos_edges}
            for edge, val in zip(active_edges, vals, strict=True):
                links[edge] = val
            rep = hol.check_flatness(hol.Connection(z3, torus, links))
            assert rep.nonflat_plaquettes != 1

    def test_falsification_open_boundary_single_link_gives_one_plaquette_and_identity_gives_flat(
        self,
    ) -> None:
        """Negative controls: open boundary edges affect 1 plaquette (not 2); e gives flat."""
        hol = _hol()

        # 1. Open 2x2 has 0 interior edges and 4 boundary edges; open 3x4 has 10 boundary edges
        lat_2x2 = hol.Lattice(2, 2, False)
        lat_3x4 = hol.Lattice(3, 4, False)
        assert _interior_positive_edges(lat_2x2) == []
        assert len(_boundary_positive_edges(lat_2x2)) == 4
        assert len(_boundary_positive_edges(lat_3x4)) == 10

        for lattice in (lat_2x2, lat_3x4):
            for group in (hol.symmetric_group_s3(), hol.quaternion_group_q8()):
                realized_sole_defects: set[str] = set()
                for b_edge in _boundary_positive_edges(lattice):
                    for a in group.elements:
                        if a == group.identity:
                            continue
                        links = {e: group.identity for e in lattice.positive_edges()}
                        links[b_edge] = a
                        conn = hol.Connection(group, lattice, links)
                        rep = hol.check_flatness(conn)
                        assert rep.verdict == hol.NOT_FLAT
                        assert rep.nonflat_plaquettes == 1
                        assert rep.witness_holonomy is not None
                        realized_sole_defects.add(rep.witness_holonomy)

                # Every non-identity element (including non-commutators "021" and "i")
                # is realized as a sole plaquette defect on the open grid!
                assert realized_sole_defects == {
                    a for a in group.elements if a != group.identity
                }

        # 2. Setting an interior edge to identity produces FLAT_TRIVIAL (0 non-flat plaquettes)
        s3 = hol.symmetric_group_s3()
        triv_3x4 = hol.trivial_connection(s3, lat_3x4)
        rep_triv = hol.check_flatness(triv_3x4)
        assert rep_triv.verdict == hol.FLAT_TRIVIAL
        assert rep_triv.nonflat_plaquettes == 0

        # 3. verify_claim rejects FLAT_TRIVIAL and FLAT_NONTRIVIAL on an interior defect
        defect_links = {e: s3.identity for e in lat_3x4.positive_edges()}
        defect_links[((1, 1), (1, 2))] = "120"
        defect_conn = hol.Connection(s3, lat_3x4, defect_links)

        ok_triv, msg_triv = hol.verify_claim(
            defect_conn,
            {
                "verdict": hol.FLAT_TRIVIAL,
                "gauge": {f"{r},{c}": "012" for r, c in lat_3x4.vertices()},
            },
        )
        assert ok_triv is False
        assert "gauge does not make every link the identity" in msg_triv

        ok_nt, msg_nt = hol.verify_claim(
            defect_conn,
            {"verdict": hol.FLAT_NONTRIVIAL, "hol_a": "012", "hol_b": "012"},
        )
        assert ok_nt is False
        assert "open lattice has no non-contractible cycle" in msg_nt

        torus_3x4 = hol.Lattice(3, 4, True)
        torus_defect_links = {e: s3.identity for e in torus_3x4.positive_edges()}
        torus_defect_links[((1, 1), (1, 2))] = "120"
        torus_defect_conn = hol.Connection(s3, torus_3x4, torus_defect_links)
        ok_torus_nt, msg_torus_nt = hol.verify_claim(
            torus_defect_conn,
            {"verdict": hol.FLAT_NONTRIVIAL, "hol_a": "012", "hol_b": "012"},
        )
        assert ok_torus_nt is False
        assert "a plaquette is not flat" in msg_torus_nt


# ---------------------------------------------------------------------------
# 4. AUDIT-P010-013: Seam-pair flatness criterion
# ---------------------------------------------------------------------------


class TestSeamPairFlatnessCriterion:
    """Verifies AUDIT-P010-013 (ATL-P010-013): 3x4 torus seam family over S_3 and Q_8."""

    def test_exhaustive_s3_and_q8_seam_pairs_3x4_and_4x3_commutator_and_gauge_conjugation(
        self,
    ) -> None:
        """Exhaust all 36 S_3^2 and 64 Q_8^2 seam pairs on 3x4 and 4x3 tori."""
        hol = _hol()
        chk = _chk()

        for rows, cols in ((3, 4), (4, 3)):
            lattice = hol.Lattice(rows, cols, True)
            corner = (rows - 1, cols - 1)
            corner_cycle = lattice.plaquette(*corner)

            for group in (hol.symmetric_group_s3(), hol.quaternion_group_q8()):
                elems = group.elements
                for a, b in itertools.product(elems, repeat=2):
                    conn = chk.seam_connection(group, lattice, a, b)
                    report = hol.check_flatness(conn)
                    commutator_ba = group.mul(
                        group.mul(group.mul(b, a), group.inv(b)),
                        group.inv(a),
                    )

                    # 1. Check all four plaquette regions explicitly
                    for r, c in lattice.plaquette_origins():
                        w_rc = conn.plaquette_holonomy(r, c)
                        if (r, c) == corner:
                            assert w_rc == commutator_ba
                        else:
                            assert w_rc == group.identity

                    # 2. Check biconditional flatness iff ab == ba
                    commutes = group.commute(a, b)
                    if commutes:
                        assert commutator_ba == group.identity
                        assert report.nonflat_plaquettes == 0
                        assert (report.hol_a, report.hol_b) == (a, b)
                        if a == group.identity and b == group.identity:
                            assert report.verdict == hol.FLAT_TRIVIAL
                            assert report.gauge is not None
                            assert hol.gauge_trivializes(conn, dict(report.gauge)) is True
                        else:
                            assert report.verdict == hol.FLAT_NONTRIVIAL

                        # 3. Exhaust every basepoint gauge element g_0 in G
                        for idx, g0 in enumerate(elems):
                            gauge = {
                                (r, c): elems[(idx + 2 * r + 3 * c) % len(elems)]
                                for r, c in lattice.vertices()
                            }
                            gauge[(0, 0)] = g0
                            moved_conn = hol.gauge_transform(conn, gauge)
                            moved_rep = hol.check_flatness(moved_conn)
                            assert moved_rep.verdict == report.verdict
                            assert moved_rep.hol_a == chk.conjugate(group, g0, a)
                            assert moved_rep.hol_b == chk.conjugate(group, g0, b)
                    else:
                        assert commutator_ba != group.identity
                        assert report.verdict == hol.NOT_FLAT
                        assert report.nonflat_plaquettes == 1
                        assert report.witness_plaquette == corner_cycle
                        assert report.witness_holonomy == commutator_ba

    def test_study_capstone_seam_census_matches_burnside_conjugacy_class_counts(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify k(G)|G| commuting counts (18 in S_3^2, 40 in Q_8^2) and study_capstone."""
        hol = _hol()
        chk = _chk()
        lattice = hol.Lattice(3, 4, True)
        s3 = hol.symmetric_group_s3()
        q8 = hol.quaternion_group_q8()

        def conjugacy_classes(group: Any) -> set[frozenset[str]]:
            return {
                frozenset(chk.conjugate(group, g, x) for g in group.elements)
                for x in group.elements
            }

        assert len(conjugacy_classes(s3)) == 3
        assert len(conjugacy_classes(q8)) == 5
        assert sum(
            sum(1 for b in s3.elements if s3.commute(a, b)) for a in s3.elements
        ) == 3 * 6 == 18
        assert sum(
            sum(1 for b in q8.elements if q8.commute(a, b)) for a in q8.elements
        ) == 5 * 8 == 40

        s3_commutators: Counter[str] = Counter()
        for a, b in itertools.product(s3.elements, repeat=2):
            if not s3.commute(a, b):
                conn = chk.seam_connection(s3, lattice, a, b)
                s3_commutators[conn.plaquette_holonomy(2, 3)] += 1
        assert dict(s3_commutators) == {"120": 9, "201": 9}

        q8_commutators: Counter[str] = Counter()
        for a, b in itertools.product(q8.elements, repeat=2):
            if not q8.commute(a, b):
                conn = chk.seam_connection(q8, lattice, a, b)
                q8_commutators[conn.plaquette_holonomy(2, 3)] += 1
        assert dict(q8_commutators) == {"-e": 24}

        # Execute study_capstone.packet() with historical evidence byte check stubbed
        recount_mod = _exec_file_module("recount_pilots", _RECOUNT_PILOTS_PATH)
        _exec_file_module("replay_c017", _REPLAY_C017_PATH)

        def _stub_verify_source_bytes() -> int:
            return 15

        def _stub_verify_c017_extraction() -> int:
            return 25

        monkeypatch.setattr(recount_mod, "verify_source_bytes", _stub_verify_source_bytes)
        monkeypatch.setattr(
            recount_mod,
            "verify_c017_extraction",
            _stub_verify_c017_extraction,
        )
        orig_path = list(sys.path)
        capstone_mod = _exec_file_module("_w5_w2_shard_c_capstone", _STUDY_CAPSTONE_PATH)
        sys.path[:] = orig_path

        pkt = capstone_mod.packet()
        assert pkt["seam_family"] == {
            "by_group": {
                "S3": {"pairs": 36, "commuting": 18},
                "Q8": {"pairs": 64, "commuting": 40},
            },
            "verdict_counts": {
                "FLAT_TRIVIAL": 2,
                "FLAT_NONTRIVIAL": 56,
                "NOT_FLAT": 42,
            },
        }

    def test_falsification_noncommuting_seam_swapped_commutator_and_unconjugated_loop_claims(
        self,
    ) -> None:
        """Negative controls: verify_claim rejects noncommuting flat, swapped [a,b], and split conjugation."""
        hol = _hol()
        chk = _chk()
        lattice = hol.Lattice(3, 4, True)
        corner_str = _format_cycle(lattice.plaquette(2, 3))
        s3 = hol.symmetric_group_s3()
        q8 = hol.quaternion_group_q8()

        noncommuting_checked = 0
        nontrivial_flat_checked = 0

        for group in (s3, q8):
            for a, b in itertools.product(group.elements, repeat=2):
                conn = chk.seam_connection(group, lattice, a, b)
                if not group.commute(a, b):
                    noncommuting_checked += 1
                    ok_flat, msg_flat = hol.verify_claim(
                        conn,
                        {"verdict": hol.FLAT_NONTRIVIAL, "hol_a": a, "hol_b": b},
                    )
                    assert ok_flat is False
                    assert "a plaquette is not flat" in msg_flat

                    if group.name == "S3":
                        # In S_3, [b, a] and [a, b] = [b, a]^{-1} are distinct 3-cycles!
                        comm_ba = group.mul(
                            group.mul(group.mul(b, a), group.inv(b)),
                            group.inv(a),
                        )
                        comm_ab = group.mul(
                            group.mul(group.mul(a, b), group.inv(a)),
                            group.inv(b),
                        )
                        assert comm_ab != comm_ba

                        ok_swap, msg_swap = hol.verify_claim(
                            conn,
                            {
                                "verdict": hol.NOT_FLAT,
                                "plaquette": corner_str,
                                "holonomy": comm_ab,
                            },
                        )
                        assert ok_swap is False
                        assert "stated holonomy" in msg_swap

                        ok_right, msg_right = hol.verify_claim(
                            conn,
                            {
                                "verdict": hol.NOT_FLAT,
                                "plaquette": corner_str,
                                "holonomy": comm_ba,
                            },
                        )
                        assert ok_right is True, msg_right
                elif (a, b) != (group.identity, group.identity):
                    nontrivial_flat_checked += 1
                    tree_gauge = hol.spanning_tree_gauge(conn)
                    assert hol.gauge_trivializes(conn, tree_gauge) is False
                    ok_triv, msg_triv = hol.verify_claim(
                        conn,
                        {
                            "verdict": hol.FLAT_TRIVIAL,
                            "gauge": {f"{r},{c}": val for (r, c), val in tree_gauge.items()},
                        },
                    )
                    assert ok_triv is False
                    assert "gauge does not make every link the identity" in msg_triv

        assert noncommuting_checked == 42
        assert nontrivial_flat_checked == 56

        # Simultaneous single-element conjugation negative control on flat non-central pairs
        loop_a_str = _format_cycle(lattice.loop_a())
        loop_b_str = _format_cycle(lattice.loop_b())
        for group, a, b, g0, g_wrong in (
            (s3, "120", "201", "021", "012"),
            (q8, "i", "-i", "j", "e"),
        ):
            conn = chk.seam_connection(group, lattice, a, b)
            gauge = {v: group.identity for v in lattice.vertices()}
            gauge[(0, 0)] = g0
            moved = hol.gauge_transform(conn, gauge)

            # Unconjugated (a, b) is rejected
            ok_unconj, msg_unconj = hol.verify_claim(
                moved,
                {
                    "verdict": hol.FLAT_NONTRIVIAL,
                    "loop_a": loop_a_str,
                    "hol_a": a,
                    "loop_b": loop_b_str,
                    "hol_b": b,
                },
            )
            assert ok_unconj is False
            assert "stated hol_a" in msg_unconj

            # Conjugating hol_a by g0 and hol_b by a different element g_wrong is rejected
            ok_split, msg_split = hol.verify_claim(
                moved,
                {
                    "verdict": hol.FLAT_NONTRIVIAL,
                    "loop_a": loop_a_str,
                    "hol_a": chk.conjugate(group, g0, a),
                    "loop_b": loop_b_str,
                    "hol_b": chk.conjugate(group, g_wrong, b),
                },
            )
            assert ok_split is False
            assert "stated hol_b" in msg_split

            # Simultaneous conjugation by g_{(0,0)} is accepted
            ok_sim, msg_sim = hol.verify_claim(
                moved,
                {
                    "verdict": hol.FLAT_NONTRIVIAL,
                    "loop_a": loop_a_str,
                    "hol_a": chk.conjugate(group, g0, a),
                    "loop_b": loop_b_str,
                    "hol_b": chk.conjugate(group, g0, b),
                },
            )
            assert ok_sim is True, msg_sim


# ---------------------------------------------------------------------------
# 5. Shard C review JSON pins, line endings, and hygiene checks
# ---------------------------------------------------------------------------


class TestShardCMetadataAndCustody:
    """Verifies review JSON inventory/git pins, LF endings, and hygiene across Shard C."""

    def test_review_json_inventory_and_git_blob_pins(self) -> None:
        """Verify all file_reviews and evidence paths against file_inventory.json and 78bc23b35."""
        review = json.loads(_REVIEW_JSON_PATH.read_text(encoding="utf-8"))
        inventory = json.loads(_INVENTORY_JSON_PATH.read_text(encoding="utf-8"))
        inv_map = {row["path"]: row["sha256"] for row in inventory["files"]}

        assert review["schema_version"] == "1.0"
        assert review["status"] == "scope_complete"
        assert review["source_commit"] == "78bc23b35"
        anc_proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", "78bc23b35", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert anc_proc.returncode == 0

        reviewed_paths: set[str] = set()
        for entry in review["file_reviews"]:
            rel_path = entry["path"]
            assert not rel_path.startswith("dag/derivations/audit_")
            assert not rel_path.startswith("tests/test_w5_")
            assert rel_path in inv_map
            assert entry["sha256"] == inv_map[rel_path]
            assert entry["full_source_read"] is True
            assert "pin_note" not in entry

            git_blob = subprocess.check_output(
                ["git", "show", f"{review['source_commit']}:{rel_path}"],
                cwd=_REPO_ROOT,
            )
            git_blob_sha = hashlib.sha256(git_blob).hexdigest()
            disk_bytes = (_REPO_ROOT / rel_path).read_bytes()

            if git_blob_sha != entry["sha256"]:
                assert entry["git_blob_sha256"] == git_blob_sha
                assert disk_bytes.replace(b"\r\n", b"\n") == git_blob
            else:
                assert "git_blob_sha256" not in entry

            line_count = len(git_blob.decode("utf-8").splitlines())
            assert entry["reviewed_lines"] == [[1, line_count]]
            reviewed_paths.add(rel_path)

        claims_by_id = {c["id"]: c for c in review["claims"]}
        assert list(claims_by_id.keys()) == [
            "AUDIT-P010-006",
            "AUDIT-P010-007",
            "AUDIT-P010-011",
            "AUDIT-P010-013",
        ]

        assert "Complements PAPER010-WITNESS-ACCEPTANCE" in claims_by_id["AUDIT-P010-006"]["limits"]
        assert (
            "Complements PAPER010-RECTANGULAR-HOLONOMY-CLASSIFIER"
            in claims_by_id["AUDIT-P010-011"]["limits"]
        )
        assert (
            "Complements PAPER010-RECTANGULAR-HOLONOMY-CLASSIFIER"
            in claims_by_id["AUDIT-P010-013"]["limits"]
        )

        bare_id_re = re.compile(r"^[A-Z0-9_-]+$")
        for claim in review["claims"]:
            assert len(claim["dependencies"]) >= 2
            for dep in claim["dependencies"]:
                assert len(dep.split()) >= 5
                assert bare_id_re.match(dep.strip()) is None
            for ev in claim["evidence"]:
                assert ev in inv_map
                assert ev in reviewed_paths
                assert not ev.startswith("dag/derivations/audit_")
                assert not ev.startswith("tests/test_w5_")

    def test_pure_lf_and_claim_hygiene_across_owned_files(self) -> None:
        """Verify pure LF line endings and absence of forbidden terms on all 6 Shard C files."""
        owned_files = (*_DERIVATION_PATHS, _REVIEW_JSON_PATH, Path(__file__).resolve())
        assert len(owned_files) == 6

        # Build patterns from hex escapes so this test file contains zero literal trigger tokens
        hygiene_patterns = (
            r"\b(?:\x70rove|\x70roves|\x70roved|\x70roven|\x70roving)\b",
            r"\b\x67uarantee[a-z]*\b",
            r"\b\x6dathematically\s+\x76erifies\b",
            r"\b\x66undamentally\b",
            r"\b\x74rue\s+\x69ntelligence\b",
            r"\b\x69mpossible\b",
            r"\b\x75niversal[a-z]*\b",
            r"\b\x66lawless[a-z]*\b",
            r"\b\x70erfectly\b",
            r"\b\x63learly\b",
            r"\b\x6fbviously\b",
            r"\b\x73imply\b",
            r"\b\x6derely\b",
            r"\b\x77eaponized\b",
        )
        internal_patterns = (
            r"\b\x4fmega\b",
            r"\b\x6fmega_[A-Za-z0-9_]*\b",
            r"\b\x41nomalon\b",
            r"\b\x57oland\b",
            r"\b\x4fEEIS\b",
        )
        compiled_hygiene = [re.compile(pat, re.IGNORECASE) for pat in hygiene_patterns]
        compiled_internal = [re.compile(pat) for pat in internal_patterns]

        for path in owned_files:
            raw = path.read_bytes()
            assert b"\r" not in raw, f"CR byte found in {path}"
            assert raw.endswith(b"\n"), f"Missing trailing LF in {path}"
            text = raw.decode("utf-8")
            for rx in compiled_hygiene:
                match = rx.search(text)
                assert match is None, f"Claim hygiene hit {match.group(0)!r} in {path.name}"
            for rx in compiled_internal:
                match = rx.search(text)
                assert match is None, f"Internal term hit {match.group(0)!r} in {path.name}"
