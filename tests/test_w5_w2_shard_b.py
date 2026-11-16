"""Verification suite for Window 5 Wave 2 Shard B (Paper 010 Part 1).

AuthorityEffect: None.

Covers:
- AUDIT-P010-001 -> ATL-P010-001 (Initial-draft filter stages are unmeasured)
- AUDIT-P010-002 -> ATL-P010-002 (Package S3 and Q8 tables; complements PAPER010-FINITE-GROUP-ADMISSION)
- AUDIT-P010-004 -> ATL-P010-004 (Lattice shape admission)
- AUDIT-P010-005 -> ATL-P010-005 (Link-list refusal)
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import itertools
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_P010_DIR = _REPO_ROOT / "atlas" / "archive" / "pfp" / "010_pfp_holonomy_checks_and_model_pilots"
_P010_CODE_DIR = _P010_DIR / "code"
_P010_DATA_DIR = _P010_CODE_DIR / "data" / "c017"
_REVIEW_JSON = _REPO_ROOT / "dag" / "reviews" / "additional_w5_w2_shard_b.json"
_DERIVATION_FILES = (
    _REPO_ROOT / "dag" / "derivations" / "audit_p010_001.md",
    _REPO_ROOT / "dag" / "derivations" / "audit_p010_002.md",
    _REPO_ROOT / "dag" / "derivations" / "audit_p010_004.md",
    _REPO_ROOT / "dag" / "derivations" / "audit_p010_005.md",
)


@pytest.fixture(autouse=True)
def _isolate_runtime_and_modules(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[None]:
    """Enforce zero bytecode emission, temp redirection, and sys.modules cleanup."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    tmp_str = str(tmp_path)
    for env_var in ("TMPDIR", "TEMP", "TMP"):
        monkeypatch.setenv(env_var, tmp_str)
    monkeypatch.setattr(tempfile, "tempdir", tmp_str)

    pre_modules = dict(sys.modules)
    before_sys_path = list(sys.path)
    try:
        yield
    finally:
        sys.path[:] = before_sys_path
        for mod_name in list(sys.modules):
            if mod_name not in pre_modules:
                sys.modules.pop(mod_name, None)
        for mod_name, orig_mod in pre_modules.items():
            if mod_name not in sys.modules or sys.modules[mod_name] is not orig_mod:
                sys.modules[mod_name] = orig_mod


def _load_holonomy_module() -> ModuleType:
    """Load Paper 010's holonomy.py under bytecode-suppressed test isolation."""
    mod_name = "_paper010_holonomy_sut"
    existing = sys.modules.get(mod_name)
    if existing is not None:
        return existing
    target = _P010_CODE_DIR / "holonomy.py"
    spec = importlib.util.spec_from_file_location(mod_name, target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from {target}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def _load_c017_case(name: str) -> dict[str, Any]:
    """Load a retained C017 JSON fixture from Paper 010's package data."""
    payload = json.loads((_P010_DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object in {name}.json")
    return payload


def _bidirectional_identity_links(hol: ModuleType, group: Any, lattice: Any) -> dict[str, str]:
    """Build a valid bidirectional identity link dictionary for an admitted lattice."""
    directed: dict[str, str] = {}
    for u, v in lattice.positive_edges():
        directed[f"{u[0]},{u[1]}->{v[0]},{v[1]}"] = group.identity
        directed[f"{v[0]},{v[1]}->{u[0]},{u[1]}"] = hol.FiniteGroup.inv(group, group.identity)
    return directed


class TestInitialDraftFilterUnmeasured:
    """Tests for AUDIT-P010-001 (ATL-P010-001)."""

    def test_paper010_withdrawals_and_absence_of_removed_filter_test_and_receipts(self) -> None:
        paper_md = (_P010_DIR / "paper.md").read_text(encoding="utf-8")
        paper_tex = (_P010_DIR / "paper.tex").read_text(encoding="utf-8")
        ledger_md = (_P010_DIR / "paper_claim_ledger.md").read_text(encoding="utf-8")
        changelog_md = (_P010_DIR / "paper_change_log.md").read_text(encoding="utf-8")

        for phrase in (
            '"MHC peptide decomposition" split an edge list into\nradius-one neighbourhoods.',
            '"Thymic selection" tested membership in a supplied\nlist.',
            '"Kinetic proofreading" compared two supplied fractions with two thresholds.',
            'The "Treg scratchpad" check tested that four labelled lines appear in order.',
            (
                'The\n"allosteric quorum" counted how many of five listed Unicode symbols '
                "occur in the\nprompt and compared the count with three."
            ),
            "No effect of any of them on model\nanswers was measured.",
        ):
            assert phrase in paper_md

        assert "five-stage prompt filter" in paper_tex
        assert "PFP10-00" in ledger_md
        assert "35e3d7ba2e0e20904d17a79cc395980f50a1a0f1" in ledger_md
        assert "decimate_and_evaluate_holonomy" in changelog_md
        assert "Removed `code/tests/test_010_adversarial_refusals_and_decimation.py`" in changelog_md

        removed_test = _P010_CODE_DIR / "tests" / "test_010_adversarial_refusals_and_decimation.py"
        assert not removed_test.exists()

        inventory = json.loads((_REPO_ROOT / "dag" / "file_inventory.json").read_text(encoding="utf-8"))
        inv_paths = {entry["path"] for entry in inventory["files"]}
        assert not any("test_010_adversarial_refusals_and_decimation" in p for p in inv_paths)

        # Retained C017 Arm 1 / Arm 2 report records 0/5 passes and written prompt constraints only.
        immune_report = json.loads(
            (_P010_DIR / "docs" / "historical_evidence" / "immune_transfer_report.json").read_text(
                encoding="utf-8"
            )
        )
        cases = immune_report["cases_evaluated"]
        assert len(cases) == 5
        assert all(entry["baseline"]["passed"] is False for entry in cases)
        assert all(entry["immune_assisted"]["passed"] is False for entry in cases)

        # Pre-split commit 35e3d7ba... is outside this standalone Git repository,
        # while source_commit 78bc23b35 has a 400-commit ancestry with zero copies of the removed test.
        probe = subprocess.run(
            ["git", "cat-file", "-t", "35e3d7ba2e0e20904d17a79cc395980f50a1a0f1"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert probe.returncode != 0

        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", "78bc23b35", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert ancestry.returncode == 0
        rev_count = int(
            subprocess.check_output(
                ["git", "rev-list", "--count", "78bc23b35"],
                cwd=_REPO_ROOT,
                text=True,
            ).strip()
        )
        assert rev_count == 400
        log_probe = subprocess.check_output(
            ["git", "log", "78bc23b35", "--oneline", "--", "*test_010_adversarial*"],
            cwd=_REPO_ROOT,
            text=True,
        ).strip()
        assert log_probe == ""

    def test_paper010_code_ast_isolation_from_pfp_domain_biochem_and_ensemble(self) -> None:
        py_files = sorted(_P010_CODE_DIR.rglob("*.py"))
        assert len(py_files) >= 8
        forbidden_roots = {"pfp", "eis", "adversary", "operations", "operads"}
        forbidden_symbols = {
            "AllostericConsensusGate",
            "HillParameters",
            "HopfieldNinioProofreader",
            "EnsembleSpec",
        }
        for py_path in py_files:
            source = py_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name.split(".")[0] not in forbidden_roots
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    assert node.module.split(".")[0] not in forbidden_roots
                elif isinstance(node, ast.Name):
                    assert node.id not in forbidden_symbols

    def test_pfp_domain_biochem_and_ensemble_contracts_diverge_from_prompt_symbol_counts(
        self,
    ) -> None:
        if str(_REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(_REPO_ROOT))
        from pfp.domain.biochem.allostery import AllostericConsensusGate, HillParameters
        from pfp.domain.biochem.proofreading import HopfieldNinioProofreader
        from pfp.domain.ensemble.models import EnsembleRole, EnsembleSpec, ModelRef

        gate = AllostericConsensusGate(HillParameters(Kd=Fraction(2, 1), n=4))
        d0 = gate.evaluate_signals([])
        assert (d0.theta, d0.hill_value, d0.status, d0.disposition) == (
            Fraction(0, 1),
            Fraction(0, 1),
            "QUIESCENT",
            "TOLERATE",
        )
        d2 = gate.evaluate_signals([Fraction(1, 1), Fraction(1, 1)])
        assert (d2.theta, d2.hill_value, d2.status, d2.is_activated) == (
            Fraction(2, 1),
            Fraction(1, 2),
            "SUB_THRESHOLD",
            False,
        )
        d3 = gate.evaluate_signals([1, 1, 1])
        assert (d3.theta, d3.hill_value, d3.status, d3.disposition) == (
            Fraction(3, 1),
            Fraction(81, 97),
            "ACTIVATED",
            "REFUSE",
        )

        proofreader = HopfieldNinioProofreader(energy_per_delay=Fraction(1, 1))
        dissociated = proofreader.proofread(
            "cand-buzz",
            "By symmetry and topological protection the claim holds",
        )
        assert dissociated.status == "DISSOCIATED_DURING_DELAY"
        assert dissociated.delta_phi1 == Fraction(1, 1)

        admitted = proofreader.proofread(
            "cand-eq",
            "By symmetry, U_01 * U_10 = e",
            initial_phi1=Fraction(0, 1),
        )
        assert admitted.status == "CATALYTIC_ADMISSION"
        assert admitted.deformed_phi1 == Fraction(0, 1)

        defect = proofreader.proofread(
            "cand-defect",
            "U_01 * U_10 = e",
            initial_phi1=Fraction(2, 3),
        )
        assert defect.status == "DISSOCIATED_DURING_DELAY"
        assert defect.deformed_phi1 == Fraction(2, 3)

        spec = EnsembleSpec(
            members=(
                ModelRef("llama-3.3-70b", 70.0, "llama"),
                ModelRef("qwen-2.5-32b", 32.0, "qwen"),
            ),
            role=EnsembleRole.VERIFY,
        )
        assert spec.evaluate_quorum(0) == ("QUIESCENT", Fraction(0, 1))
        assert spec.evaluate_quorum(2) == ("UNKNOWN", Fraction(1, 2))
        assert spec.evaluate_quorum(3) == ("ACTIVATE", Fraction(81, 97))

    def test_falsification_biochem_and_ensemble_gates_refuse_floats_and_invalid_parameters(
        self,
    ) -> None:
        if str(_REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(_REPO_ROOT))
        from pfp.domain.biochem.allostery import AllostericConsensusGate, HillParameters
        from pfp.domain.biochem.errors import ZeroFloatViolationError
        from pfp.domain.biochem.proofreading import DissociationReceipt, HopfieldNinioProofreader
        from pfp.domain.ensemble.models import EnsembleRole, EnsembleSpec, ModelRef

        with pytest.raises(ZeroFloatViolationError):
            HillParameters(Kd=2.0)  # type: ignore[arg-type]
        with pytest.raises(ZeroFloatViolationError):
            HillParameters(n=4.0)  # type: ignore[arg-type]
        with pytest.raises(ZeroFloatViolationError):
            HillParameters(activation_threshold=0.7)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="must be integer in \\{2, 4\\}"):
            HillParameters(n=3)
        with pytest.raises(ValueError, match="strictly positive"):
            HillParameters(Kd=Fraction(0, 1))

        gate = AllostericConsensusGate()
        with pytest.raises(ZeroFloatViolationError):
            gate.compute_hill(1.5)  # type: ignore[arg-type]
        with pytest.raises(ZeroFloatViolationError):
            gate.evaluate_signals([Fraction(1, 1), 0.5])  # type: ignore[list-item]
        with pytest.raises(ValueError, match="non-negative"):
            gate.compute_hill(Fraction(-1, 2))
        with pytest.raises(ValueError):
            gate.compute_hill("unicode-prompt-symbols")  # type: ignore[arg-type]

        with pytest.raises(ZeroFloatViolationError):
            HopfieldNinioProofreader(energy_per_delay=1.0)  # type: ignore[arg-type]
        proofreader = HopfieldNinioProofreader()
        with pytest.raises(ZeroFloatViolationError):
            proofreader.proofread("cand", "x = 1", initial_phi1=0.0)  # type: ignore[arg-type]
        with pytest.raises(ZeroFloatViolationError):
            DissociationReceipt("cand", 0.0, Fraction(0, 1), Fraction(0, 1), Fraction(1, 1), "S", "R")  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="at least one member"):
            EnsembleSpec(members=(), role=EnsembleRole.VERIFY)
        with pytest.raises(ValueError, match="parameter ceiling"):
            EnsembleSpec(
                members=(ModelRef("oversized", 70.5, "lineage_a"),),
                role=EnsembleRole.VERIFY,
            )
        with pytest.raises(ValueError, match="exceeding the cap"):
            EnsembleSpec(
                members=(
                    ModelRef("m1", 8.0, "Llama"),
                    ModelRef("m2", 70.0, "llama"),
                ),
                role=EnsembleRole.VERIFY,
            )
        with pytest.raises(ValueError, match="authority_effect"):
            EnsembleSpec(
                members=(ModelRef("m1", 8.0, "llama"),),
                role=EnsembleRole.VERIFY,
                authority_effect="Elevated",
            )
        valid_ensemble = EnsembleSpec(
            members=(ModelRef("m1", 8.0, "llama"),),
            role=EnsembleRole.VERIFY,
        )
        with pytest.raises(ValueError, match="non-negative"):
            valid_ensemble.evaluate_quorum(-1)


class TestPackageS3AndQ8Tables:
    """Tests for AUDIT-P010-002 (ATL-P010-002), complementing PAPER010-FINITE-GROUP-ADMISSION."""

    def test_s3_order_spectrum_nonabelian_witnesses_center_and_c017_isomorphisms(self) -> None:
        hol = _load_holonomy_module()
        s3 = hol.symmetric_group_s3()

        assert s3.name == "S3"
        assert s3.elements == ("012", "021", "102", "120", "201", "210")
        assert len(s3.elements) == 6
        assert s3.identity == "012"
        assert not s3.is_abelian()

        orders = {g: s3.order_of(g) for g in s3.elements}
        assert sorted(orders.values()) == [1, 2, 2, 2, 3, 3]
        assert [g for g, n in orders.items() if n == 1] == ["012"]
        assert sorted(g for g, n in orders.items() if n == 2) == ["021", "102", "210"]
        assert sorted(g for g, n in orders.items() if n == 3) == ["120", "201"]
        assert s3.inv("120") == "201" and s3.inv("201") == "120"

        # Explicit non-abelian witness and full 36-pair commuting census.
        assert s3.mul("021", "102") == "201"
        assert s3.mul("102", "021") == "120"
        assert not s3.commute("021", "102")
        commuting_pairs = [
            (a, b) for a, b in itertools.product(s3.elements, repeat=2) if s3.commute(a, b)
        ]
        assert len(commuting_pairs) == 18
        center = {a for a in s3.elements if all(s3.commute(a, b) for b in s3.elements)}
        assert center == {"012"}
        commutators = {
            s3.product([a, b, s3.inv(a), s3.inv(b)])
            for a, b in itertools.product(s3.elements, repeat=2)
        }
        assert commutators == {"012", "120", "201"}

        # All four S3 C017 fixtures share the same dihedral presentation and have 6 isomorphisms to s3.
        case_groups = [
            hol.connection_from_case(_load_c017_case(name)).group
            for name in ("pois_01", "base_01", "base_02", "base_03")
        ]
        s3_case = case_groups[0]
        assert all(g == s3_case for g in case_groups[1:])
        isomorphisms = [
            perm
            for perm in itertools.permutations(s3.elements)
            if all(
                perm[s3_case.elements.index(s3_case.mul(a, b))] == s3.mul(perm[i], perm[j])
                for (i, a), (j, b) in itertools.product(enumerate(s3_case.elements), repeat=2)
            )
        ]
        assert len(isomorphisms) == 6

    def test_q8_order_spectrum_unique_involution_subgroups_and_base13_equality(self) -> None:
        hol = _load_holonomy_module()
        q8 = hol.quaternion_group_q8()

        assert q8.name == "Q8"
        assert q8.elements == ("e", "-e", "i", "-i", "j", "-j", "k", "-k")
        assert len(q8.elements) == 8
        assert q8.identity == "e"
        assert not q8.is_abelian()

        orders = {g: q8.order_of(g) for g in q8.elements}
        assert sorted(orders.values()) == [1, 2, 4, 4, 4, 4, 4, 4]
        assert [g for g in q8.elements if q8.order_of(g) == 2] == ["-e"]
        assert [g for g in q8.elements if g != "e" and q8.mul(g, g) == "e"] == ["-e"]
        for imag in ("i", "-i", "j", "-j", "k", "-k"):
            assert q8.mul(imag, imag) == "-e"
            assert q8.inv(imag) == (imag[1:] if imag.startswith("-") else f"-{imag}")

        # Hamilton non-commuting witnesses and 64-pair commuting census.
        assert (q8.mul("i", "j"), q8.mul("j", "i")) == ("k", "-k")
        assert (q8.mul("j", "k"), q8.mul("k", "j")) == ("i", "-i")
        assert (q8.mul("k", "i"), q8.mul("i", "k")) == ("j", "-j")

        commuting = [
            (a, b) for a, b in itertools.product(q8.elements, repeat=2) if q8.commute(a, b)
        ]
        non_commuting = [
            (a, b) for a, b in itertools.product(q8.elements, repeat=2) if not q8.commute(a, b)
        ]
        assert len(commuting) == 40
        assert len(non_commuting) == 24
        assert {q8.product([a, b, q8.inv(a), q8.inv(b)]) for a, b in non_commuting} == {"-e"}
        center = {a for a in q8.elements if all(q8.commute(a, b) for b in q8.elements)}
        assert center == {"e", "-e"}

        # Every nontrivial cyclic subgroup <g> contains the unique involution '-e' and is normal.
        for g in q8.elements:
            if g == "e":
                continue
            cyclic = {q8.product([g] * k) for k in range(1, q8.order_of(g) + 1)}
            assert "-e" in cyclic
            for h in q8.elements:
                assert {q8.product([h, x, q8.inv(h)]) for x in cyclic} == cyclic

        assert hol.connection_from_case(_load_c017_case("base_13")).group == q8

    def test_falsification_finite_group_refuses_mutated_s3_and_q8_tables(self) -> None:
        hol = _load_holonomy_module()
        s3 = hol.symmetric_group_s3()
        q8 = hol.quaternion_group_q8()
        s3_inv = {g: s3.inv(g) for g in s3.elements}
        q8_inv = {g: q8.inv(g) for g in q8.elements}

        # Carrier, name, and identity refusals.
        with pytest.raises(hol.GroupTableError, match="nonempty sequence"):
            hol.FiniteGroup("empty", [], "e", {}, {})
        with pytest.raises(hol.GroupTableError, match="nonempty sequence"):
            hol.FiniteGroup("str-carrier", "012", "0", {}, {})
        with pytest.raises(hol.GroupTableError, match="distinct"):
            hol.FiniteGroup("dup", ["e", "e"], "e", {"e": {"e": "e"}}, {"e": "e"})
        with pytest.raises(hol.GroupTableError, match="group name"):
            hol.FiniteGroup(123, s3.elements, s3.identity, s3.as_table(), s3_inv)  # type: ignore[arg-type]
        with pytest.raises(hol.GroupTableError, match="identity is not an element"):
            hol.FiniteGroup("bad-id", s3.elements, "999", s3.as_table(), s3_inv)

        # Closure, identity law, inverse law, and associativity refusals on S3 and Q8 mutations.
        unclosed = q8.as_table()
        unclosed["i"]["j"] = "2i"
        with pytest.raises(hol.GroupTableError, match="total and closed"):
            hol.FiniteGroup("Q8-unclosed", q8.elements, q8.identity, unclosed, q8_inv)

        broken_id = q8.as_table()
        broken_id["e"]["i"] = "-i"
        with pytest.raises(hol.GroupTableError, match="identity law fails"):
            hol.FiniteGroup("Q8-bad-id-law", q8.elements, q8.identity, broken_id, q8_inv)

        with pytest.raises(hol.GroupTableError, match="inverse law fails"):
            hol.FiniteGroup("Q8-bad-inv", q8.elements, q8.identity, q8.as_table(), {**q8_inv, "i": "i"})

        swapped_s3 = s3.as_table()
        swapped_s3["120"]["021"], swapped_s3["120"]["102"] = (
            swapped_s3["120"]["102"],
            swapped_s3["120"]["021"],
        )
        with pytest.raises(hol.GroupTableError, match="associativity fails"):
            hol.FiniteGroup("S3-nonassoc", s3.elements, s3.identity, swapped_s3, s3_inv)

        bad_case = _load_c017_case("base_13")
        del bad_case["group"]["inverses"]
        with pytest.raises(hol.GroupTableError, match="missing a required field"):
            hol.connection_from_case(bad_case)


class TestLatticeShapeAdmission:
    """Tests for AUDIT-P010-004 (ATL-P010-004)."""

    def test_admitted_open_and_periodic_grids_satisfy_cell_counts_and_disjoint_orientations(
        self,
    ) -> None:
        hol = _load_holonomy_module()

        for rows, cols in itertools.product((2, 3, 4, 5), repeat=2):
            open_lat = hol.Lattice(rows, cols, False)
            v_count = len(open_lat.vertices())
            e_pos = open_lat.positive_edges()
            p_count = len(open_lat.plaquette_origins())
            assert v_count == rows * cols
            assert len(e_pos) == rows * (cols - 1) + (rows - 1) * cols
            assert p_count == (rows - 1) * (cols - 1)
            assert v_count - len(e_pos) + p_count == 1
            e_rev = {(v, u) for u, v in e_pos}
            assert len(set(e_pos)) == len(e_pos)
            assert set(e_pos).isdisjoint(e_rev)

        for rows, cols in itertools.product((3, 4, 5), repeat=2):
            torus = hol.Lattice(rows, cols, True)
            v_count = len(torus.vertices())
            e_pos = torus.positive_edges()
            p_count = len(torus.plaquette_origins())
            assert v_count == rows * cols
            assert len(e_pos) == 2 * rows * cols
            assert p_count == rows * cols
            assert v_count - len(e_pos) + p_count == 0
            e_rev = {(v, u) for u, v in e_pos}
            assert len(set(e_pos) | e_rev) == 4 * rows * cols
            assert len(torus.loop_a()) == cols + 1
            assert len(torus.loop_b()) == rows + 1

    def test_torus_size_two_endpoint_collision_vs_size_three_injectivity(self) -> None:
        hol = _load_holonomy_module()

        # Arithmetic demonstration of why periodic length 2 collides forward wraparound with reversal.
        length_two_steps = [((0, c), (0, (c + 1) % 2)) for c in range(2)]
        assert length_two_steps[0] == ((0, 0), (0, 1))
        assert length_two_steps[1] == ((0, 1), (0, 0))
        assert length_two_steps[1] == (length_two_steps[0][1], length_two_steps[0][0])

        # At length 3, Lattice(3, 3, True) admits independent links on interior and wraparound 1-cells.
        torus = hol.Lattice(3, 3, True)
        q8 = hol.quaternion_group_q8()
        links = {edge: q8.identity for edge in torus.positive_edges()}
        for r in range(3):
            links[((r, 2), (r, 0))] = "i"
        conn = hol.Connection(q8, torus, links)
        assert conn.link((0, 0), (0, 1)) == "e"
        assert conn.link((0, 1), (0, 0)) == "e"
        assert conn.link((0, 2), (0, 0)) == "i"
        assert conn.link((0, 0), (0, 2)) == "-i"
        report = hol.check_flatness(conn)
        assert report.verdict == hol.FLAT_NONTRIVIAL
        assert (report.hol_a, report.hol_b) == ("i", "e")

    def test_falsification_lattice_and_case_loader_refuse_invalid_sizes_types_and_boundaries(
        self,
    ) -> None:
        hol = _load_holonomy_module()

        # Exhaustive finite grid over (-1..4) x (-1..4) for open and periodic bounds.
        for rows, cols in itertools.product(range(-1, 5), repeat=2):
            if rows < 2 or cols < 2:
                with pytest.raises(hol.LatticeError, match="need at least 2 rows and columns"):
                    hol.Lattice(rows, cols, False)
            else:
                assert hol.Lattice(rows, cols, False).rows == rows

            if rows < 3 or cols < 3:
                with pytest.raises(hol.LatticeError, match="need at least 3 rows and columns"):
                    hol.Lattice(rows, cols, True)
            else:
                assert hol.Lattice(rows, cols, True).rows == rows

        # Exact runtime type guards: bool (subclass of int), float, Fraction, str, None, int subclass.
        class _IntSubclass(int):
            pass

        for bad_dim in (True, False, 3.0, Fraction(3, 1), "3", None, (3,), _IntSubclass(3)):
            with pytest.raises(hol.LatticeError, match="rows and cols must be int"):
                hol.Lattice(bad_dim, 3, False)
            with pytest.raises(hol.LatticeError, match="rows and cols must be int"):
                hol.Lattice(3, bad_dim, True)

        for bad_periodic in (0, 1, "open", "periodic", None, [True]):
            with pytest.raises(hol.LatticeError, match="periodic must be bool"):
                hol.Lattice(3, 3, bad_periodic)

        # Open lattices refuse torus cycle queries.
        open_lat = hol.Lattice(3, 4, False)
        with pytest.raises(hol.LatticeError, match="no non-contractible cycle"):
            open_lat.loop_a()
        with pytest.raises(hol.LatticeError, match="no non-contractible cycle"):
            open_lat.loop_b()

        # connection_from_case refuses unknown boundary labels and degenerate torus dimensions.
        base_case = _load_c017_case("pois_01")
        for bad_boundary in ("torus", "closed", "", None, True):
            with pytest.raises(hol.LatticeError, match="unknown boundary"):
                hol.connection_from_case({**base_case, "boundary": bad_boundary})
        with pytest.raises(hol.LatticeError, match="need at least 3 rows and columns"):
            hol.connection_from_case({**base_case, "L": 2, "M": 3, "boundary": "periodic"})


class TestLinkListRefusal:
    """Tests for AUDIT-P010-005 (ATL-P010-005)."""

    def test_unmutated_c017_fixtures_admitted_with_exact_bidirectional_edge_counts(self) -> None:
        hol = _load_holonomy_module()
        expected = (
            ("pois_01", 24, hol.NOT_FLAT),
            ("base_01", 34, hol.NOT_FLAT),
            ("base_02", 62, hol.FLAT_TRIVIAL),
            ("base_03", 120, hol.FLAT_NONTRIVIAL),
            ("base_13", 62, hol.NOT_FLAT),
        )
        total_directed = 0
        for name, directed_count, verdict in expected:
            case = _load_c017_case(name)
            assert len(case["edges"]) == directed_count
            total_directed += directed_count
            conn = hol.connection_from_case(case)
            assert len(conn.links()) * 2 == directed_count
            assert hol.check_flatness(conn).verdict == verdict
        assert total_directed == 302

    def test_falsification_loader_refuses_inverse_mismatch_missing_direction_and_out_of_lattice_edges(
        self,
    ) -> None:
        hol = _load_holonomy_module()

        # 1. Inverse mismatches on non-involutive S3 ('r' vs 'r2'), transposition, and Q8 ('i' vs '-i').
        pois_case = _load_c017_case("pois_01")
        pois_conn = hol.connection_from_case(pois_case)
        pois_edges = dict(pois_case["edges"])
        assert pois_edges["0,0->0,1"] == "r" and pois_edges["0,1->0,0"] == "r2"

        with pytest.raises(hol.LatticeError, match="inverse mismatch"):
            hol.connection_from_directed_links(
                pois_conn.group, pois_conn.lattice, {**pois_edges, "0,1->0,0": "r"}
            )
        with pytest.raises(hol.LatticeError, match="inverse mismatch"):
            hol.connection_from_directed_links(
                pois_conn.group, pois_conn.lattice, {**pois_edges, "0,0->0,1": "s", "0,1->0,0": "e"}
            )

        q8_case = _load_c017_case("base_13")
        q8_conn = hol.connection_from_case(q8_case)
        q8_edges = dict(q8_case["edges"])
        assert q8_edges["0,0->0,1"] == "i" and q8_edges["0,1->0,0"] == "-i"
        with pytest.raises(hol.LatticeError, match="inverse mismatch"):
            hol.connection_from_directed_links(
                q8_conn.group, q8_conn.lattice, {**q8_edges, "0,1->0,0": "i"}
            )

        # 2. Missing forward or reverse directions on open and periodic lattices.
        with pytest.raises(hol.LatticeError, match="not listed in both directions"):
            hol.connection_from_directed_links(
                pois_conn.group,
                pois_conn.lattice,
                {k: v for k, v in pois_edges.items() if k != "0,0->0,1"},
            )
        with pytest.raises(hol.LatticeError, match="not listed in both directions"):
            hol.connection_from_directed_links(
                pois_conn.group,
                pois_conn.lattice,
                {k: v for k, v in pois_edges.items() if k != "0,1->0,0"},
            )

        torus_case = _load_c017_case("base_03")
        torus_conn = hol.connection_from_case(torus_case)
        torus_edges = dict(torus_case["edges"])
        with pytest.raises(hol.LatticeError, match="not listed in both directions"):
            hol.connection_from_directed_links(
                torus_conn.group,
                torus_conn.lattice,
                {k: v for k, v in torus_edges.items() if k != "0,5->0,0"},
            )

        # 3. Extraneous out-of-lattice edges (diagonal, self-loop, jump, open wraparound, out-of-bounds).
        for extra_edges in (
            {"0,0->1,1": "e"},
            {"0,0->0,0": "e"},
            {"0,0->2,2": "e", "2,2->0,0": "e"},
            {"0,2->0,0": "r", "0,0->0,2": "r2"},
            {"3,0->3,1": "e", "3,1->3,0": "e"},
        ):
            with pytest.raises(hol.LatticeError, match="not in the lattice"):
                hol.connection_from_directed_links(
                    pois_conn.group, pois_conn.lattice, {**pois_edges, **extra_edges}
                )

    def test_falsification_loader_and_connection_refuse_malformed_keys_aliases_and_unknown_elements(
        self,
    ) -> None:
        hol = _load_holonomy_module()
        s3 = hol.symmetric_group_s3()
        lattice = hol.Lattice(2, 2, False)
        valid = _bidirectional_identity_links(hol, s3, lattice)
        assert hol.check_flatness(
            hol.connection_from_directed_links(s3, lattice, valid)
        ).verdict == hol.FLAT_TRIVIAL

        # Malformed vertex strings and edge keys.
        for bad_vertex in ("-1,0", "0,-1", " 0,0", "0, 0", "0,0,0", "0", "a,0", "\uff10,0", None):
            with pytest.raises(hol.LatticeError, match="malformed vertex name"):
                hol.parse_vertex(bad_vertex)  # type: ignore[arg-type]

        for bad_key in ("0,0-0,1", "0,0->0,1->0,2", "0,0", 42):
            with pytest.raises(hol.LatticeError, match="malformed edge key"):
                hol.connection_from_directed_links(s3, lattice, {**valid, bad_key: "012"})  # type: ignore[dict-item]

        # Canonicalized alias duplicates (both matching and conflicting values).
        for alias in ("00,0->0,1", "0,0->00,1"):
            for assigned in ("012", "120"):
                with pytest.raises(hol.LatticeError, match="duplicate parsed edge"):
                    hol.connection_from_directed_links(s3, lattice, {**valid, alias: assigned})

        # Unknown or non-str group elements.
        class _StrSubclass(str):
            pass

        for bad_val in ("unknown", "", None, 0, ["012"], _StrSubclass("012")):
            with pytest.raises(hol.LatticeError, match="unknown group element"):
                hol.connection_from_directed_links(
                    s3, lattice, {**valid, "0,0->0,1": bad_val}  # type: ignore[dict-item]
                )

        # Direct Connection constructor and connection_from_case mapping guards.
        pos_links = {edge: s3.identity for edge in lattice.positive_edges()}
        missing_one = dict(list(pos_links.items())[:-1])
        with pytest.raises(hol.LatticeError, match="exactly the positive edges"):
            hol.Connection(s3, lattice, missing_one)
        with pytest.raises(hol.LatticeError, match="exactly the positive edges"):
            hol.Connection(s3, lattice, {**pos_links, ((0, 0), (1, 1)): s3.identity})
        with pytest.raises(hol.LatticeError, match="every link must be a group element"):
            hol.Connection(s3, lattice, {**pos_links, ((0, 0), (0, 1)): "not-in-s3"})

        pois_case = _load_c017_case("pois_01")
        with pytest.raises(hol.LatticeError, match="case edges must be a mapping"):
            hol.connection_from_case({**pois_case, "edges": ["0,0->0,1"]})


class TestShardBReviewAndArtifactIntegrity:
    """Self-verification of Shard B review JSON pins and derivation files."""

    _HYGIENE_RE = re.compile(
        r"\b("
        + "|".join(
            [
                "pr" + "ove",
                "pr" + "oves",
                "pr" + "oved",
                "pr" + "oven",
                "pr" + "oving",
                "guar" + r"antee\w*",
                "mathe" + r"matically\s+verifies",
                "funda" + "mentally",
                "tr" + r"ue\s+intelligence",
                "impos" + "sible",
                "univ" + r"ersal\w*",
                "flaw" + r"less\w*",
                "perf" + "ectly",
                "cle" + "arly",
                "obvi" + "ously",
                "sim" + "ply",
                "mer" + "ely",
                "weap" + "onized",
            ]
        )
        + r")\b",
        re.IGNORECASE,
    )

    _INTERNAL_NAMES_RE = re.compile(
        r"\b("
        + "|".join(
            [
                "Ome" + "ga",
                "ome" + r"ga_\w+",
                "Anom" + "alon",
                "Wol" + "and",
                "OE" + "EIS",
            ]
        )
        + r")\b"
    )

    def test_owned_files_use_pure_lf_and_expected_metadata(self) -> None:
        owned = (*_DERIVATION_FILES, _REVIEW_JSON, Path(__file__).resolve())
        for path in owned:
            raw = path.read_bytes()
            assert b"\r" not in raw, f"CR byte found in {path}"
            assert raw.endswith(b"\n"), f"Missing trailing LF in {path}"
            content = raw.decode("utf-8")
            hygiene_hits = self._HYGIENE_RE.findall(content)
            assert hygiene_hits == [], f"Claim Hygiene hits in {path.name}: {hygiene_hits}"
            name_hits = self._INTERNAL_NAMES_RE.findall(content)
            assert name_hits == [], f"Unscrubbed internal names in {path.name}: {name_hits}"

        for deriv_path in _DERIVATION_FILES:
            text = deriv_path.read_text(encoding="utf-8")
            assert "AuthorityEffect: None." in text
            for heading in (
                "## 1. Claim Statement",
                "## 2. Context & Hypotheses",
                "## 3. Derivation / Evidence",
                "## 4. Limits and Non-Claims",
                "## 5. Claim Hygiene Summary",
                "## 6. Cross-References & Provenance",
            ):
                assert heading in text, f"Missing {heading} in {deriv_path.name}"

        p010_002_text = (_REPO_ROOT / "dag" / "derivations" / "audit_p010_002.md").read_text(
            encoding="utf-8"
        )
        assert "Complements `PAPER010-FINITE-GROUP-ADMISSION`" in p010_002_text

    def test_review_json_matches_inventory_and_source_commit_blobs(self) -> None:
        review = json.loads(_REVIEW_JSON.read_text(encoding="utf-8"))
        assert review["schema_version"] == "1.0"
        assert review["status"] == "scope_complete"
        assert review["source_commit"] == "78bc23b35"

        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", "78bc23b35", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert ancestry.returncode == 0

        rev_count = int(
            subprocess.check_output(
                ["git", "rev-list", "--count", "78bc23b35"],
                cwd=_REPO_ROOT,
                text=True,
            ).strip()
        )
        assert rev_count == 400

        inventory = json.loads((_REPO_ROOT / "dag" / "file_inventory.json").read_text(encoding="utf-8"))
        inv_sha_by_path = {entry["path"]: entry["sha256"] for entry in inventory["files"]}

        reviewed_paths: set[str] = set()
        for entry in review["file_reviews"]:
            rel_path = entry["path"]
            assert not rel_path.startswith("dag/derivations/audit_")
            assert not rel_path.startswith("tests/test_w5_")
            assert rel_path in inv_sha_by_path
            assert entry["sha256"] == inv_sha_by_path[rel_path]
            assert entry["full_source_read"] is True

            disk_bytes = (_REPO_ROOT / rel_path).read_bytes()
            line_count = len(disk_bytes.decode("utf-8").splitlines())
            assert entry["reviewed_lines"] == [[1, line_count]]

            source_blob = subprocess.check_output(
                ["git", "show", f"{review['source_commit']}:{rel_path}"],
                cwd=_REPO_ROOT,
            )
            source_sha = hashlib.sha256(source_blob).hexdigest()
            if source_sha == entry["sha256"]:
                assert "git_blob_sha256" not in entry
            else:
                assert entry["git_blob_sha256"] == source_sha
                crlf_sha = hashlib.sha256(source_blob.replace(b"\n", b"\r\n")).hexdigest()
                assert crlf_sha == entry["sha256"]
            assert "pin_note" not in entry
            reviewed_paths.add(rel_path)

        claims = {claim["id"]: claim for claim in review["claims"]}
        assert set(claims) == {
            "AUDIT-P010-001",
            "AUDIT-P010-002",
            "AUDIT-P010-004",
            "AUDIT-P010-005",
        }
        assert "Complements PAPER010-FINITE-GROUP-ADMISSION" in claims["AUDIT-P010-002"]["limits"]

        for claim in claims.values():
            assert claim["dependencies"], f"Empty dependencies on {claim['id']}"
            for dep in claim["dependencies"]:
                assert " " in dep and len(dep) > 25, f"Bare or short dependency {dep!r}"
            assert claim["evidence"], f"Empty evidence on {claim['id']}"
            for ev_path in claim["evidence"]:
                assert ev_path in reviewed_paths
