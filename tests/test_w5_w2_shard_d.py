"""Verification and falsification suite for Window 5 Wave 2 Shard D (Paper 010 Part 3).

Covers:
- AUDIT-P010-017 (ATL-P010-017, partial / narrows): C017 case custody (LF Git/ZIP & CRLF digests)
- AUDIT-P010-018 (ATL-P010-018): Table 1 recount (lattice sizes, link ratios, plaquettes, skippables, verdicts)
- AUDIT-P010-019 (ATL-P010-019): base_03 link census (49 interior + 11 seam links, 10 of 30 active plaquettes)
- AUDIT-P010-020 (ATL-P010-020): Case group identification (6 S3 isomorphisms, exact Q8 table, C2/C3/V4/C6/D4 controls)

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
import re
import subprocess
import sys
import tempfile
import types
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SOURCE_COMMIT = "78bc23b35"
_PAPER_010_DIR = (
    _REPO_ROOT / "atlas" / "archive" / "pfp" / "010_pfp_holonomy_checks_and_model_pilots"
)
_PAPER_010_CODE_DIR = _PAPER_010_DIR / "code"
_PAPER_010_C017_DIR = _PAPER_010_CODE_DIR / "data" / "c017"
_CHALLENGES_DIR = _REPO_ROOT / "workflows" / "tasks" / "certified_challenges"
_C017_PKG_DIR = _CHALLENGES_DIR / "c017_nonabelian_lattice_holonomy"
_C017_JUDGE_DIR = _C017_PKG_DIR / "judge_packet"

_RETAINED_CASES: tuple[str, ...] = ("pois_01", "base_01", "base_02", "base_03", "base_13")

_EXPECTED_CUSTODY: dict[str, tuple[str, str, int, int, str, str]] = {
    "pois_01.json": (
        "pois_01_inv_mismatch_S3",
        "pois_01_s3_commutator_trap",
        1742,
        1844,
        "35cda630cb5aaf93a3e16b5eb39a1a30fe899097756e7754ab9b518899ba7234",
        "b85672dcdd8bc6788356a8b7d071cbccd00eda4dcad44d5a5a7c20cbade9a7f3",
    ),
    "base_01.json": (
        "base_01_s3",
        "base_01_s3_open_nonflat",
        1938,
        2050,
        "890d2bfe3311b2f609db9fd7152cbc0b9d47a7bae49ee22bf452e24bd5461684",
        "754bf7956c08e3cce6d9511d1cec2d7052850d4ea06616356d10f96f1987633a",
    ),
    "base_02.json": (
        "base_02_s3",
        "base_02_s3_open_puregauge",
        2577,
        2717,
        "1ea12f8f60b0d28177faf9255ddab84234d4bcd0ac49715fa3d11605d445223c",
        "300f09e2cd91af9f0de88a1f6194d3626077c32f29bb2659162efb5d02101286",
    ),
    "base_03.json": (
        "base_03_s3",
        "base_03_s3_periodic_torus",
        3759,
        3957,
        "1e22ed7d22dd8130f6da6e41487c1be385f41fd315d6e05a24fc4af6f624e4c6",
        "2677b2723eb49d551541dbb9826b6b3d0a429e4d83d2cdbf4f3839c452be9957",
    ),
    "base_13.json": (
        "base_13_q8",
        "base_13_q8_open_nonflat",
        3143,
        3319,
        "dc3438254b883ca6e882650974bc52707c2ef455ea49be268276b029022a2f8e",
        "59bb4a2659fc1507616a953e9476e5f906eada3eabffcc3ce6acd29f55b93cb0",
    ),
}


@pytest.fixture(autouse=True)
def _hermetic_runtime_isolation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[None]:
    """Enforce zero bytecode emission, tmp_path temp redirection, and zero sys.modules/sys.path leaks."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    isolated_tmp = tmp_path / "_isolated_tmp"
    isolated_tmp.mkdir(parents=True, exist_ok=True)
    for env_key in ("TMPDIR", "TEMP", "TMP"):
        monkeypatch.setenv(env_key, str(isolated_tmp))
    monkeypatch.setattr(tempfile, "tempdir", str(isolated_tmp))

    pre_modules = dict(sys.modules)
    pre_sys_path = list(sys.path)
    try:
        yield
    finally:
        sys.path[:] = pre_sys_path
        for mod_name in list(sys.modules):
            if mod_name not in pre_modules:
                sys.modules.pop(mod_name, None)
        for k, orig_mod in pre_modules.items():
            if sys.modules.get(k) is not orig_mod:
                sys.modules[k] = orig_mod


def _git_source_bytes(rel_posix_path: str, commit: str = _SOURCE_COMMIT) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{rel_posix_path}"],
        cwd=_REPO_ROOT,
    )


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_module_from_path(module_name: str, file_path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to build module spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_paper010_modules() -> tuple[types.ModuleType, types.ModuleType, types.ModuleType]:
    """Load Paper 010 holonomy.py, replay_c017.py, and test_c017_replay.py inside isolated sys.modules."""
    if str(_PAPER_010_CODE_DIR) not in sys.path:
        sys.path.insert(0, str(_PAPER_010_CODE_DIR))
    holonomy_mod = _load_module_from_path("holonomy", _PAPER_010_CODE_DIR / "holonomy.py")
    replay_mod = _load_module_from_path("replay_c017", _PAPER_010_CODE_DIR / "replay_c017.py")
    test_replay_mod = _load_module_from_path(
        "_shard_d_test_c017_replay",
        _PAPER_010_CODE_DIR / "tests" / "test_c017_replay.py",
    )
    return holonomy_mod, replay_mod, test_replay_mod


def _load_upstream_c017_modules() -> tuple[
    types.ModuleType, types.ModuleType, types.ModuleType, types.ModuleType
]:
    """Load upstream C017 groups, solver, dual_evaluator, and Arm 6 prompt decimation module."""
    if str(_CHALLENGES_DIR) not in sys.path:
        sys.path.insert(0, str(_CHALLENGES_DIR))
    groups_mod = importlib.import_module("c017_nonabelian_lattice_holonomy.reference_solver.groups")
    solver_mod = importlib.import_module("c017_nonabelian_lattice_holonomy.reference_solver.solver")
    dual_mod = importlib.import_module(
        "c017_nonabelian_lattice_holonomy.judge_packet.checkers.dual_evaluator"
    )

    stub_transfer = types.ModuleType(
        "c017_nonabelian_lattice_holonomy.eval_epistemic_immune_transfer"
    )
    for stub_attr in ("_main", "_model_slug", "_query", "_run_cases"):
        setattr(
            stub_transfer,
            stub_attr,
            lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("offline audit stub")),
        )
    sys.modules["c017_nonabelian_lattice_holonomy.eval_epistemic_immune_transfer"] = stub_transfer
    arm6_mod = importlib.import_module(
        "c017_nonabelian_lattice_holonomy.eval_arm6_hierarchical_decimation"
    )
    return groups_mod, solver_mod, dual_mod, arm6_mod


def _parse_sha256_manifest_file(manifest_path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        digest, rel_name = stripped.split(None, 1)
        entries[rel_name.strip()] = digest
    return entries


def _upstream_case_path(filename: str) -> Path:
    subdir = "poisoned" if filename.startswith("pois_") else "base"
    return _C017_JUDGE_DIR / "cases" / subdir / filename


def _enumerate_group_isomorphisms(
    source_group: Any, target_group: Any
) -> list[dict[str, str]]:
    """Enumerate all bijections phi: source_group -> target_group satisfying phi(ab) = phi(a)phi(b)."""
    src_elems: tuple[str, ...] = tuple(source_group.elements)
    tgt_elems: tuple[str, ...] = tuple(target_group.elements)
    if len(src_elems) != len(tgt_elems):
        return []

    src_non_id = [x for x in src_elems if x != source_group.identity]
    tgt_non_id = [y for y in tgt_elems if y != target_group.identity]
    src_orders = {x: source_group.order_of(x) for x in src_non_id}
    tgt_orders = {y: target_group.order_of(y) for y in tgt_non_id}

    isomorphisms: list[dict[str, str]] = []
    for perm in itertools.permutations(tgt_non_id):
        if any(src_orders[a] != tgt_orders[b] for a, b in zip(src_non_id, perm, strict=True)):
            continue
        phi = {source_group.identity: target_group.identity}
        phi.update(zip(src_non_id, perm, strict=True))
        if _is_homomorphism(source_group, target_group, phi):
            isomorphisms.append(phi)
    return isomorphisms


def _is_homomorphism(source_group: Any, target_group: Any, phi: dict[str, str]) -> bool:
    for a in source_group.elements:
        for b in source_group.elements:
            if phi[source_group.mul(a, b)] != target_group.mul(phi[a], phi[b]):
                return False
    return True


def _cyclic_group(holonomy_mod: types.ModuleType, n: int) -> Any:
    elems = tuple(f"c{i}" for i in range(n))
    table = {
        f"c{i}": {f"c{j}": f"c{(i + j) % n}" for j in range(n)}
        for i in range(n)
    }
    inverses = {f"c{i}": f"c{(-i) % n}" for i in range(n)}
    return holonomy_mod.FiniteGroup(f"C{n}", elems, "c0", table, inverses)


def _klein_four_group_v4(holonomy_mod: types.ModuleType) -> Any:
    pairs = [(0, 0), (0, 1), (1, 0), (1, 1)]
    name_of = {(a, b): f"v{a}{b}" for a, b in pairs}
    elems = tuple(name_of[p] for p in pairs)
    table = {
        name_of[(a1, b1)]: {
            name_of[(a2, b2)]: name_of[((a1 ^ a2), (b1 ^ b2))] for a2, b2 in pairs
        }
        for a1, b1 in pairs
    }
    inverses = {el: el for el in elems}
    return holonomy_mod.FiniteGroup("V4", elems, "v00", table, inverses)


def _dihedral_group_d4(holonomy_mod: types.ModuleType) -> Any:
    """Construct order-8 dihedral group D4 = <r, s | r^4 = s^2 = e, s r s = r^3>."""
    pairs = [(s_bit, r_exp) for s_bit in (0, 1) for r_exp in range(4)]

    def _label(s_bit: int, r_exp: int) -> str:
        if s_bit == 0 and r_exp == 0:
            return "e"
        prefix = "s" if s_bit == 1 else ""
        suffix = "" if r_exp == 0 else ("r" if r_exp == 1 else f"r{r_exp}")
        return f"{prefix}{suffix}"

    elems = tuple(_label(s_bit, r_exp) for s_bit, r_exp in pairs)
    table: dict[str, dict[str, str]] = {}
    inverses: dict[str, str] = {}
    for s1, r1 in pairs:
        u = _label(s1, r1)
        table[u] = {}
        inv_r = (-r1) % 4 if s1 == 0 else r1
        inverses[u] = _label(s1, inv_r)
        for s2, r2 in pairs:
            v = _label(s2, r2)
            prod_s = s1 ^ s2
            prod_r = (r1 + r2) % 4 if s2 == 0 else ((-r1 + r2) % 4)
            table[u][v] = _label(prod_s, prod_r)
    return holonomy_mod.FiniteGroup("D4", elems, "e", table, inverses)


class TestC017CaseCustody:
    """AUDIT-P010-017 (ATL-P010-017): C017 five-case byte custody and LF/CRLF manifest digests."""

    def test_git_head_and_deposit_zip_case_files_are_lf_byte_copies_of_upstream_judge_cases(
        self,
    ) -> None:
        zip_path = _PAPER_010_DIR / "010_pfp_holonomy_checks_and_model_pilots_2026-10-02.zip"
        assert zip_path.is_file()

        with zipfile.ZipFile(zip_path) as deposit_zip:
            zip_members = {
                Path(member).name: deposit_zip.read(member)
                for member in deposit_zip.namelist()
                if "code/data/c017/" in member and member.endswith(".json")
            }

        for filename, (
            json_id,
            _harness_case_id,
            lf_size,
            _crlf_size,
            lf_sha,
            _crlf_sha,
        ) in _EXPECTED_CUSTODY.items():
            rel_arch = (
                f"atlas/archive/pfp/010_pfp_holonomy_checks_and_model_pilots/code/data/c017/{filename}"
            )
            git_lf_bytes = _git_source_bytes(rel_arch)
            upstream_bytes = _upstream_case_path(filename).read_bytes()
            zip_bytes = zip_members[filename]

            assert b"\r\n" not in git_lf_bytes
            assert len(git_lf_bytes) == lf_size
            assert git_lf_bytes == upstream_bytes == zip_bytes
            assert _sha256_hex(git_lf_bytes) == lf_sha
            parsed = json.loads(git_lf_bytes.decode("utf-8"))
            assert parsed["id"] == json_id

    def test_lf_and_crlf_digests_match_provenance_and_manifest_commitments(self) -> None:
        provenance = json.loads((_PAPER_010_C017_DIR / "provenance.json").read_text(encoding="utf-8"))
        manifest_sha256 = _parse_sha256_manifest_file(_PAPER_010_DIR / "MANIFEST.sha256")
        sha256sums = _parse_sha256_manifest_file(_PAPER_010_DIR / "SHA256SUMS")
        judge_manifest = json.loads((_C017_JUDGE_DIR / "manifest.json").read_text(encoding="utf-8"))

        assert judge_manifest["digest_normalization"] == "CRLF_TO_LF"
        assert judge_manifest["manifest_status"] == "CURRENT_REGENERATED_NOT_A_PRE_RUN_COMMITMENT"

        prov_by_file = {entry["file"]: entry for entry in provenance["cases"]}
        assert set(prov_by_file) == set(_EXPECTED_CUSTODY)

        # Historical commit 3d3492f20d839a3c032bbf15eb803733b12599fe is outside this split repo
        ext_commit = provenance["cases"][0]["commit"]
        assert ext_commit == "3d3492f20d839a3c032bbf15eb803733b12599fe"
        cat_proc = subprocess.run(
            ["git", "cat-file", "-t", ext_commit],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert cat_proc.returncode != 0

        for filename, (
            _json_id,
            harness_case_id,
            lf_size,
            crlf_size,
            lf_sha,
            crlf_sha,
        ) in _EXPECTED_CUSTODY.items():
            entry = prov_by_file[filename]
            assert entry["harness_case_id"] == harness_case_id
            assert entry["sha256"] == lf_sha
            assert entry["judge_manifest_sha256_crlf"] == crlf_sha

            rel_code_path = f"code/data/c017/{filename}"
            assert manifest_sha256[rel_code_path] == lf_sha
            assert sha256sums[rel_code_path] == lf_sha

            subdir = "poisoned" if filename.startswith("pois_") else "base"
            assert judge_manifest["files"][f"judge_packet/cases/{subdir}/{filename}"] == lf_sha

            lf_bytes = _upstream_case_path(filename).read_bytes()
            crlf_bytes = lf_bytes.replace(b"\n", b"\r\n")
            assert not lf_bytes.endswith(b"\n")
            assert lf_bytes.count(b"\n") == crlf_size - lf_size
            assert len(lf_bytes.splitlines()) == lf_bytes.count(b"\n") + 1
            assert len(lf_bytes) == lf_size
            assert len(crlf_bytes) == crlf_size
            assert _sha256_hex(crlf_bytes) == crlf_sha

    def test_working_tree_crlf_materialization_matches_file_inventory_and_gitattributes_boundary(
        self,
    ) -> None:
        file_inv = {
            item["path"]: item["sha256"]
            for item in json.loads(
                (_REPO_ROOT / "dag" / "file_inventory.json").read_text(encoding="utf-8")
            )["files"]
        }
        gitattributes_text = (_REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
        assert "workflows/** text eol=lf" in gitattributes_text
        assert "atlas/archive/**" not in gitattributes_text

        for filename, (
            _jid,
            _cid,
            _lf_sz,
            crlf_size,
            lf_sha,
            crlf_sha,
        ) in _EXPECTED_CUSTODY.items():
            rel_arch = (
                f"atlas/archive/pfp/010_pfp_holonomy_checks_and_model_pilots/code/data/c017/{filename}"
            )
            subdir = "poisoned" if filename.startswith("pois_") else "base"
            rel_up = (
                f"workflows/tasks/certified_challenges/c017_nonabelian_lattice_holonomy/"
                f"judge_packet/cases/{subdir}/{filename}"
            )

            assert file_inv[rel_up] == lf_sha
            assert file_inv[rel_arch] == crlf_sha

            wt_arch_bytes = (_REPO_ROOT / rel_arch).read_bytes()
            if b"\r\n" in wt_arch_bytes:
                assert len(wt_arch_bytes) == crlf_size
                assert _sha256_hex(wt_arch_bytes) == crlf_sha
                assert _sha256_hex(wt_arch_bytes.replace(b"\r\n", b"\n")) == lf_sha

    def test_falsification_replay_custody_check_passes_on_lf_tmp_copy_and_rejects_crlf_or_tampered_bytes(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _hol, _rep, test_replay_mod = _load_paper010_modules()

        lf_data_dir = tmp_path / "c017_lf"
        lf_data_dir.mkdir(parents=True, exist_ok=True)
        prov_rel = (
            "atlas/archive/pfp/010_pfp_holonomy_checks_and_model_pilots/"
            "code/data/c017/provenance.json"
        )
        (lf_data_dir / "provenance.json").write_bytes(_git_source_bytes(prov_rel))
        for filename in _EXPECTED_CUSTODY:
            (lf_data_dir / filename).write_bytes(_upstream_case_path(filename).read_bytes())

        # Positive execution of Paper 010's SUT digest gate on pure LF copies
        monkeypatch.setattr(test_replay_mod, "DATA", lf_data_dir)
        test_replay_mod.test_case_files_match_recorded_digests()

        # Negative control 1: CRLF conversion on a single case triggers SUT line-ending refusal
        crlf_dir = tmp_path / "c017_crlf"
        crlf_dir.mkdir(parents=True, exist_ok=True)
        for src in lf_data_dir.iterdir():
            crlf_dir.joinpath(src.name).write_bytes(src.read_bytes())
        pois_lf = (crlf_dir / "pois_01.json").read_bytes()
        (crlf_dir / "pois_01.json").write_bytes(pois_lf.replace(b"\n", b"\r\n"))
        monkeypatch.setattr(test_replay_mod, "DATA", crlf_dir)
        with pytest.raises(AssertionError):
            test_replay_mod.test_case_files_match_recorded_digests()

        # Negative control 2: Single-byte LF content mutation triggers SUT sha256 mismatch
        tampered_dir = tmp_path / "c017_tampered"
        tampered_dir.mkdir(parents=True, exist_ok=True)
        for src in lf_data_dir.iterdir():
            tampered_dir.joinpath(src.name).write_bytes(src.read_bytes())
        base01_mut = (tampered_dir / "base_01.json").read_bytes().replace(
            b'"0,1->0,2": "s"', b'"0,1->0,2": "r"', 1
        )
        assert b"\r\n" not in base01_mut
        (tampered_dir / "base_01.json").write_bytes(base01_mut)
        monkeypatch.setattr(test_replay_mod, "DATA", tampered_dir)
        with pytest.raises(AssertionError):
            test_replay_mod.test_case_files_match_recorded_digests()

        # Negative control 3: Tampering with judge_manifest_sha256_crlf triggers CRLF digest refusal
        bad_manifest_dir = tmp_path / "c017_bad_crlf_pin"
        bad_manifest_dir.mkdir(parents=True, exist_ok=True)
        for src in lf_data_dir.iterdir():
            bad_manifest_dir.joinpath(src.name).write_bytes(src.read_bytes())
        prov_obj = json.loads((bad_manifest_dir / "provenance.json").read_text(encoding="utf-8"))
        prov_obj["cases"][3]["judge_manifest_sha256_crlf"] = "0" * 64
        (bad_manifest_dir / "provenance.json").write_bytes(
            (json.dumps(prov_obj, indent=2) + "\n").encode("utf-8")
        )
        monkeypatch.setattr(test_replay_mod, "DATA", bad_manifest_dir)
        with pytest.raises(AssertionError):
            test_replay_mod.test_case_files_match_recorded_digests()


class TestTable1Recount:
    """AUDIT-P010-018 (ATL-P010-018): Table 1 structural counts and harness expected-verdict parity."""

    _EXPECTED_HOST_ROWS: list[tuple[str, str, str, int, int, str]] = [
        ("pois_01", "S3 3x3 open", "NOT_FLAT", 4, 3, "witness holonomy r2"),
        ("base_01", "S3 3x4 open", "NOT_FLAT", 6, 5, "witness holonomy s"),
        (
            "base_02",
            "S3 4x5 open",
            "FLAT_TRIVIAL",
            12,
            0,
            "tree gauge makes every link the identity",
        ),
        ("base_03", "S3 5x6 periodic", "FLAT_NONTRIVIAL", 30, 20, "hol_a=r, hol_b=r2"),
        ("base_13", "Q8 4x5 open", "NOT_FLAT", 12, 11, "witness holonomy -i"),
    ]

    _EXPECTED_LINK_COUNTS: dict[str, tuple[int, int]] = {
        "pois_01": (1, 12),
        "base_01": (1, 17),
        "base_02": (28, 31),
        "base_03": (11, 60),
        "base_13": (1, 31),
    }

    _EXPECTED_WITNESS_PLAQUETTES: dict[str, tuple[tuple[int, int], ...] | None] = {
        "pois_01": ((0, 0), (1, 0), (1, 1), (0, 1)),
        "base_01": ((0, 1), (1, 1), (1, 2), (0, 2)),
        "base_02": None,
        "base_03": None,
        "base_13": ((0, 0), (1, 0), (1, 1), (0, 1)),
    }

    def test_table1_lattice_sizes_link_ratios_plaquettes_skippables_and_host_verdicts(
        self,
    ) -> None:
        holonomy_mod, replay_mod, test_replay_mod = _load_paper010_modules()

        rows = replay_mod.host_rows()
        assert rows == self._EXPECTED_HOST_ROWS
        assert {
            r[0]: (
                r[1].split()[0],
                int(r[1].split()[1].split("x")[0]),
                int(r[1].split()[1].split("x")[1]),
                r[1].split()[2] == "periodic",
                r[2],
                r[3],
                r[4],
            )
            for r in rows
        } == test_replay_mod.EXPECTED

        total_pos_edges = 0
        total_non_id_edges = 0
        total_plaquettes = 0
        total_skippable = 0
        expected_nonflat = {"pois_01": 1, "base_01": 1, "base_02": 0, "base_03": 0, "base_13": 1}

        for case_name in _RETAINED_CASES:
            case_obj = json.loads((_PAPER_010_C017_DIR / f"{case_name}.json").read_text("utf-8"))
            conn = holonomy_mod.connection_from_case(case_obj)
            report = holonomy_mod.check_flatness(conn)

            pos_edges = conn.lattice.positive_edges()
            non_id = sum(1 for u, v in pos_edges if conn.link(u, v) != conn.group.identity)
            assert (non_id, len(pos_edges)) == self._EXPECTED_LINK_COUNTS[case_name]
            assert report.witness_plaquette == self._EXPECTED_WITNESS_PLAQUETTES[case_name]

            total_pos_edges += len(pos_edges)
            total_non_id_edges += non_id
            total_plaquettes += report.plaquettes
            total_skippable += report.skipped_identity_plaquettes
            assert len(case_obj["edges"]) == 2 * len(pos_edges)
            assert report.nonflat_plaquettes == expected_nonflat[case_name]

        assert total_pos_edges == 151
        assert total_non_id_edges == 42
        assert total_plaquettes == 64
        assert total_skippable == 39

    def test_identity_skipping_invariance_and_harness_expected_verdict_agreement(self) -> None:
        holonomy_mod, replay_mod, test_replay_mod = _load_paper010_modules()
        model_claims = json.loads(
            (_PAPER_010_C017_DIR / "model_claims.json").read_text(encoding="utf-8")
        )

        host_verdicts: dict[str, str] = {}
        for case_name in _RETAINED_CASES:
            case_obj = json.loads((_PAPER_010_C017_DIR / f"{case_name}.json").read_text("utf-8"))
            conn = holonomy_mod.connection_from_case(case_obj)
            fast = holonomy_mod.check_flatness(conn, skip_identity_links=True)
            full = holonomy_mod.check_flatness(conn, skip_identity_links=False)

            assert full.skipped_identity_plaquettes == 0
            assert fast.verdict == full.verdict
            assert fast.nonflat_plaquettes == full.nonflat_plaquettes
            assert fast.witness_plaquette == full.witness_plaquette
            assert fast.witness_holonomy == full.witness_holonomy
            assert fast.hol_a == full.hol_a
            assert fast.hol_b == full.hol_b
            assert fast.gauge == full.gauge
            host_verdicts[case_name] = fast.verdict

        entry_count = 0
        for run in model_claims["runs"]:
            for item in run["cases"]:
                entry_count += 1
                mapped_expected = test_replay_mod.label(item["harness_expected_verdict"])
                assert mapped_expected == host_verdicts[item["case"]]
        assert entry_count == 25

        cert_rows = replay_mod.certificate_rows()
        assert len(cert_rows) == 25
        retained_with_solution = [row for row in cert_rows if row[4] is not None]
        assert len(retained_with_solution) == 15
        assert sum(1 for row in retained_with_solution if row[4] is True) == 10
        assert sum(1 for row in retained_with_solution if row[4] is False) == 5

    def test_upstream_reference_solver_and_dual_evaluator_consensus_across_retained_and_base_cases(
        self,
    ) -> None:
        holonomy_mod, _replay_mod, test_replay_mod = _load_paper010_modules()
        _groups_mod, solver_mod, dual_mod, _arm6_mod = _load_upstream_c017_modules()

        for case_name in _RETAINED_CASES:
            case_obj = json.loads(_upstream_case_path(f"{case_name}.json").read_text("utf-8"))
            solved, _tracer = solver_mod.solve(case_obj)
            assert solved["status"] == "SOLVED"
            dual_ok, _reason, details = dual_mod.evaluate_dual(case_obj, solved)
            assert dual_ok is True
            assert details["algebraic_checker"]["passed"] is True
            assert details["independent_checker"]["passed"] is True

            host_report = holonomy_mod.check_flatness(holonomy_mod.connection_from_case(case_obj))
            assert test_replay_mod.label(solved["verdict"]) == host_report.verdict

        base_files = sorted((_C017_JUDGE_DIR / "cases" / "base").glob("base_*.json"))
        assert len(base_files) == 30
        for base_path in base_files:
            case_obj = json.loads(base_path.read_text(encoding="utf-8"))
            solved, _tracer = solver_mod.solve(case_obj)
            assert solved["status"] == "SOLVED"
            dual_ok, _reason, _details = dual_mod.evaluate_dual(case_obj, solved)
            assert dual_ok is True
            host_report = holonomy_mod.check_flatness(holonomy_mod.connection_from_case(case_obj))
            assert test_replay_mod.label(solved["verdict"]) == host_report.verdict

    def test_falsification_mutated_case_jsons_flip_verdicts_or_raise_typed_errors_and_dual_evaluator_kills_mutations(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        holonomy_mod, replay_mod, _test_rep = _load_paper010_modules()
        _groups_mod, solver_mod, dual_mod, _arm6_mod = _load_upstream_c017_modules()

        # Copy all 5 retained cases to tmp_path and mutate base_02 (breaking pure gauge on 1 edge)
        mut_data_dir = tmp_path / "c017_table1_mut"
        mut_data_dir.mkdir(parents=True, exist_ok=True)
        for case_name in _RETAINED_CASES:
            src_bytes = _upstream_case_path(f"{case_name}.json").read_bytes()
            (mut_data_dir / f"{case_name}.json").write_bytes(src_bytes)

        base02_mut = json.loads((mut_data_dir / "base_02.json").read_text(encoding="utf-8"))
        assert base02_mut["edges"]["0,0->1,0"] == "e"
        base02_mut["edges"]["0,0->1,0"] = "s"
        base02_mut["edges"]["1,0->0,0"] = "s"
        (mut_data_dir / "base_02.json").write_text(json.dumps(base02_mut), encoding="utf-8")

        mut_conn = holonomy_mod.connection_from_case(base02_mut)
        mut_non_id = sum(1 for u, v in mut_conn.lattice.positive_edges() if mut_conn.link(u, v) != "e")
        assert (mut_non_id, len(mut_conn.lattice.positive_edges())) == (29, 31)

        monkeypatch.setattr(replay_mod, "DATA", mut_data_dir)
        mut_rows = dict((r[0], r) for r in replay_mod.host_rows())
        assert mut_rows["base_02"][2] == "NOT_FLAT"
        assert mut_rows["base_02"][5].startswith("witness holonomy ")

        # Mutating inverse symmetry on base_01 raises LatticeError in holonomy.py and OUT_OF_SCOPE in solver.py
        base01_bad_inv = json.loads((mut_data_dir / "base_01.json").read_text(encoding="utf-8"))
        base01_bad_inv["edges"]["0,1->0,2"] = "r"
        base01_bad_inv["edges"]["0,2->0,1"] = "r"  # r * r = r2 != e
        (mut_data_dir / "base_01.json").write_text(json.dumps(base01_bad_inv), encoding="utf-8")
        with pytest.raises(holonomy_mod.LatticeError, match="inverse"):
            replay_mod.host_rows()
        oos_res, _tr = solver_mod.solve(base01_bad_inv)
        assert oos_res["status"] == "OUT_OF_SCOPE"
        assert oos_res["witness"]["reason"] == "INVERSE_MISMATCH"

        # Verify all 12 hostile certificate mutations in judge_packet/mutation_suite/mutations/ are killed
        mut_files = sorted((_C017_JUDGE_DIR / "mutation_suite" / "mutations").glob("mut_*.json"))
        assert len(mut_files) == 12
        for mut_file in mut_files:
            payload = json.loads(mut_file.read_text(encoding="utf-8"))
            ok, _reason, _details = dual_mod.evaluate_dual(
                payload["case"], payload["corrupted_result"]
            )
            assert ok is False


class TestBase03LinkCensus:
    """AUDIT-P010-019 (ATL-P010-019): base_03 60-link and 30-plaquette seam census."""

    def test_base03_sixty_positive_links_partition_into_49_identity_interior_and_11_seam_links(
        self,
    ) -> None:
        holonomy_mod, _replay_mod, _test_rep = _load_paper010_modules()
        base03 = json.loads(_upstream_case_path("base_03.json").read_text(encoding="utf-8"))
        conn = holonomy_mod.connection_from_case(base03)

        assert conn.lattice.rows == 5
        assert conn.lattice.cols == 6
        assert conn.lattice.periodic is True

        pos_edges = conn.lattice.positive_edges()
        assert len(pos_edges) == 60
        assert len(base03["edges"]) == 120

        interior_edges = []
        col_seam_edges = []
        row_seam_edges = []
        for u, v in pos_edges:
            val = conn.link(u, v)
            rev = conn.link(v, u)
            if u[1] == 5 and v[1] == 0 and u[0] == v[0]:
                col_seam_edges.append((u, v))
                assert val == "r" and rev == "r2"
            elif u[0] == 4 and v[0] == 0 and u[1] == v[1]:
                row_seam_edges.append((u, v))
                assert val == "r2" and rev == "r"
            else:
                interior_edges.append((u, v))
                assert val == "e" and rev == "e"

        assert len(interior_edges) == 49
        assert len(col_seam_edges) == 5
        assert len(row_seam_edges) == 6
        assert len(col_seam_edges) + len(row_seam_edges) == 11

    def test_base03_thirty_plaquettes_partition_into_20_four_identity_and_10_active_seam_plaquettes(
        self,
    ) -> None:
        holonomy_mod, _replay_mod, _test_rep = _load_paper010_modules()
        base03 = json.loads(_upstream_case_path("base_03.json").read_text(encoding="utf-8"))
        conn = holonomy_mod.connection_from_case(base03)

        origins = conn.lattice.plaquette_origins()
        assert len(origins) == 30

        interior_plaqs: list[tuple[int, int]] = []
        col_strip_plaqs: list[tuple[int, int]] = []
        row_strip_plaqs: list[tuple[int, int]] = []
        corner_plaqs: list[tuple[int, int]] = []

        for r, c in origins:
            factors = conn.plaquette_links(r, c)
            assert conn.plaquette_holonomy(r, c) == "e"
            if r < 4 and c < 5:
                assert factors == ["e", "e", "e", "e"]
                interior_plaqs.append((r, c))
            elif r < 4 and c == 5:
                assert factors == ["e", "r", "e", "r2"]
                col_strip_plaqs.append((r, c))
            elif r == 4 and c < 5:
                assert factors == ["r2", "e", "r", "e"]
                row_strip_plaqs.append((r, c))
            else:
                assert (r, c) == (4, 5)
                assert factors == ["r2", "r", "r", "r2"]
                corner_plaqs.append((r, c))

        assert len(interior_plaqs) == 20
        assert len(col_strip_plaqs) == 4
        assert len(row_strip_plaqs) == 5
        assert len(corner_plaqs) == 1
        active_union = set(col_strip_plaqs) | set(row_strip_plaqs) | set(corner_plaqs)
        assert len(active_union) == 10

    def test_base03_torus_cycle_holonomies_arm6_prompt_decimation_and_gauge_noninvariance_of_skip_count(
        self,
    ) -> None:
        holonomy_mod, _replay_mod, _test_rep = _load_paper010_modules()
        _groups_mod, _solver_mod, _dual_mod, arm6_mod = _load_upstream_c017_modules()

        base03 = json.loads(_upstream_case_path("base_03.json").read_text(encoding="utf-8"))
        conn = holonomy_mod.connection_from_case(base03)
        report = holonomy_mod.check_flatness(conn)

        assert conn.lattice.loop_a() == [(0, c) for c in range(6)] + [(0, 0)]
        assert conn.lattice.loop_b() == [(r, 0) for r in range(5)] + [(0, 0)]
        assert report.verdict == holonomy_mod.FLAT_NONTRIVIAL
        assert report.plaquettes == 30
        assert report.skipped_identity_plaquettes == 20
        assert report.hol_a == "r"
        assert report.hol_b == "r2"
        assert report.gauge is None
        assert conn.group.commute(report.hol_a, report.hol_b)

        prompt_text = arm6_mod.build_c017_arm6_prompt(base03)
        assert "- 20 elementary plaquettes consist ENTIRELY of identity edges (U = 'e')." in prompt_text
        assert "Only the following 10 elementary plaquette(s) touch non-identity edges:" in prompt_text
        assert "24 elementary plaquettes" not in prompt_text

        # Non-constant vertex gauge shifts skipped_identity_plaquettes from 20 -> 0 while keeping FLAT_NONTRIVIAL
        elems = conn.group.elements
        dense_gauge = {
            (r, c): elems[(1 + r + 2 * c) % len(elems)] for r, c in conn.lattice.vertices()
        }
        dense_gauge[(0, 0)] = "s"
        transformed = holonomy_mod.gauge_transform(conn, dense_gauge)
        moved_report = holonomy_mod.check_flatness(transformed)
        assert moved_report.verdict == holonomy_mod.FLAT_NONTRIVIAL
        assert moved_report.skipped_identity_plaquettes == 0
        # Conjugation by s inverts r -> r2 and r2 -> r
        assert (moved_report.hol_a, moved_report.hol_b) == ("r2", "r")

    def test_falsification_single_seam_link_or_cycle_claim_mutation_breaks_flatness_or_certificate_admission(
        self, tmp_path: Path
    ) -> None:
        holonomy_mod, _replay_mod, _test_rep = _load_paper010_modules()
        base03 = json.loads(_upstream_case_path("base_03.json").read_text(encoding="utf-8"))
        conn = holonomy_mod.connection_from_case(base03)

        # Mutate a single seam link in tmp_path/base_03_seam_defect.json: (0,5)->(0,0) from r to s
        broken_seam = copy.deepcopy(base03)
        broken_seam["edges"]["0,5->0,0"] = "s"
        broken_seam["edges"]["0,0->0,5"] = "s"
        mut_file = tmp_path / "base_03_seam_defect.json"
        mut_file.write_text(json.dumps(broken_seam), encoding="utf-8")

        loaded_mut = holonomy_mod.connection_from_case(
            json.loads(mut_file.read_text(encoding="utf-8"))
        )
        mut_report = holonomy_mod.check_flatness(loaded_mut)
        assert mut_report.verdict == holonomy_mod.NOT_FLAT
        assert mut_report.nonflat_plaquettes == 2
        assert mut_report.skipped_identity_plaquettes == 20

        # Replacing column-seam 'r' with non-commuting 's' across all 5 rows breaks flatness solely at corner P_{4,5}
        noncommuting_seam = copy.deepcopy(base03)
        for row_idx in range(5):
            noncommuting_seam["edges"][f"{row_idx},5->{row_idx},0"] = "s"
            noncommuting_seam["edges"][f"{row_idx},0->{row_idx},5"] = "s"
        nc_file = tmp_path / "base_03_noncommuting_seam.json"
        nc_file.write_text(json.dumps(noncommuting_seam), encoding="utf-8")
        nc_conn = holonomy_mod.connection_from_case(
            json.loads(nc_file.read_text(encoding="utf-8"))
        )
        nc_report = holonomy_mod.check_flatness(nc_conn)
        assert nc_report.verdict == holonomy_mod.NOT_FLAT
        assert nc_report.nonflat_plaquettes == 1
        assert nc_report.witness_plaquette == ((4, 5), (0, 5), (0, 0), (4, 0))

        # SUT certificate verifier rejects swapped hol_a/hol_b and contractible loops on genuine base_03
        loop_a = ["0,0", "0,1", "0,2", "0,3", "0,4", "0,5", "0,0"]
        loop_b = ["0,0", "1,0", "2,0", "3,0", "4,0", "0,0"]
        assert holonomy_mod.verify_claim(
            conn,
            {
                "verdict": holonomy_mod.FLAT_NONTRIVIAL,
                "loop_a": loop_a,
                "hol_a": "r",
                "loop_b": loop_b,
                "hol_b": "r2",
            },
        )[0]
        ok_swapped, _msg_swapped = holonomy_mod.verify_claim(
            conn,
            {
                "verdict": holonomy_mod.FLAT_NONTRIVIAL,
                "loop_a": loop_a,
                "hol_a": "r2",
                "loop_b": loop_b,
                "hol_b": "r",
            },
        )
        assert ok_swapped is False


class TestCaseGroupIdentification:
    """AUDIT-P010-020 (ATL-P010-020): S3 six-isomorphism census, Q8 table equality, and small-group controls."""

    def test_four_s3_case_tables_have_six_isomorphisms_onto_symmetric_group_s3(self) -> None:
        holonomy_mod, _replay_mod, _test_rep = _load_paper010_modules()
        groups_mod, _solver_mod, _dual_mod, _arm6_mod = _load_upstream_c017_modules()

        s3_pkg = holonomy_mod.symmetric_group_s3()
        upstream_s3 = groups_mod.make_s3()

        loaded_s3_groups = []
        for case_name in ("pois_01", "base_01", "base_02", "base_03"):
            case_obj = json.loads(_upstream_case_path(f"{case_name}.json").read_text("utf-8"))
            assert case_obj["group"] == upstream_s3
            loaded_s3_groups.append(holonomy_mod.connection_from_case(case_obj).group)

        case_s3 = loaded_s3_groups[0]
        for other in loaded_s3_groups[1:]:
            assert other == case_s3

        isomorphisms = _enumerate_group_isomorphisms(case_s3, s3_pkg)
        assert len(isomorphisms) == 6

        expected_pairs = {
            ("120", "021"),
            ("120", "102"),
            ("120", "210"),
            ("201", "021"),
            ("201", "102"),
            ("201", "210"),
        }
        observed_pairs = {(phi["r"], phi["s"]) for phi in isomorphisms}
        assert observed_pairs == expected_pairs

        # Verify all 6 explicit bijections recorded in audit_p010_020.md Section 3.1
        by_pair = {(phi["r"], phi["s"]): phi for phi in isomorphisms}
        assert by_pair[("120", "021")] == {
            "e": "012",
            "r": "120",
            "r2": "201",
            "s": "021",
            "sr": "102",
            "sr2": "210",
        }
        assert by_pair[("120", "102")] == {
            "e": "012",
            "r": "120",
            "r2": "201",
            "s": "102",
            "sr": "210",
            "sr2": "021",
        }
        assert by_pair[("120", "210")] == {
            "e": "012",
            "r": "120",
            "r2": "201",
            "s": "210",
            "sr": "021",
            "sr2": "102",
        }
        assert by_pair[("201", "021")] == {
            "e": "012",
            "r": "201",
            "r2": "120",
            "s": "021",
            "sr": "210",
            "sr2": "102",
        }
        assert by_pair[("201", "102")] == {
            "e": "012",
            "r": "201",
            "r2": "120",
            "s": "102",
            "sr": "021",
            "sr2": "210",
        }
        assert by_pair[("201", "210")] == {
            "e": "012",
            "r": "201",
            "r2": "120",
            "s": "210",
            "sr": "102",
            "sr2": "021",
        }

    def test_base13_q8_table_equals_package_quaternion_group_and_has_24_automorphisms(
        self,
    ) -> None:
        holonomy_mod, _replay_mod, _test_rep = _load_paper010_modules()
        groups_mod, _solver_mod, _dual_mod, _arm6_mod = _load_upstream_c017_modules()

        base13 = json.loads(_upstream_case_path("base_13.json").read_text(encoding="utf-8"))
        assert base13["group"] == groups_mod.make_q8()

        case_q8 = holonomy_mod.connection_from_case(base13).group
        q8_pkg = holonomy_mod.quaternion_group_q8()

        assert case_q8 == q8_pkg
        assert case_q8.elements == ("e", "-e", "i", "-i", "j", "-j", "k", "-k")
        assert case_q8.identity == "e"
        assert case_q8.as_table() == q8_pkg.as_table()
        assert {x: case_q8.inv(x) for x in case_q8.elements} == {
            x: q8_pkg.inv(x) for x in q8_pkg.elements
        }
        assert [el for el in case_q8.elements if case_q8.order_of(el) == 2] == ["-e"]
        assert len([el for el in case_q8.elements if case_q8.order_of(el) == 4]) == 6

        q8_automorphisms = _enumerate_group_isomorphisms(case_q8, q8_pkg)
        assert len(q8_automorphisms) == 24

    def test_small_group_isomorphism_discrimination_across_c2_c3_v4_c6_s3_d4_q8(self) -> None:
        holonomy_mod, _replay_mod, _test_rep = _load_paper010_modules()

        c2 = _cyclic_group(holonomy_mod, 2)
        c3 = _cyclic_group(holonomy_mod, 3)
        v4 = _klein_four_group_v4(holonomy_mod)
        c6 = _cyclic_group(holonomy_mod, 6)
        d4 = _dihedral_group_d4(holonomy_mod)

        case_s3 = holonomy_mod.connection_from_case(
            json.loads(_upstream_case_path("pois_01.json").read_text(encoding="utf-8"))
        ).group
        case_q8 = holonomy_mod.connection_from_case(
            json.loads(_upstream_case_path("base_13.json").read_text(encoding="utf-8"))
        ).group

        assert len(_enumerate_group_isomorphisms(c2, c2)) == 1
        assert len(_enumerate_group_isomorphisms(c3, c3)) == 2
        assert len(_enumerate_group_isomorphisms(v4, v4)) == 6
        assert len(_enumerate_group_isomorphisms(c6, c6)) == 2
        assert len(_enumerate_group_isomorphisms(d4, d4)) == 8
        assert not d4.is_abelian()
        assert len([el for el in d4.elements if d4.order_of(el) == 2]) == 5

        for non_s3 in (c2, c3, v4, c6, d4, case_q8):
            assert _enumerate_group_isomorphisms(case_s3, non_s3) == []
        for non_q8 in (c2, c3, v4, c6, case_s3, d4):
            assert _enumerate_group_isomorphisms(case_q8, non_q8) == []

    def test_falsification_mutated_or_substituted_case_group_tables_fail_admission_or_isomorphism_identification(
        self, tmp_path: Path
    ) -> None:
        holonomy_mod, _replay_mod, _test_rep = _load_paper010_modules()
        _groups_mod, _solver_mod, dual_mod, _arm6_mod = _load_upstream_c017_modules()

        # Negative control 1: Swapping two entries in pois_01's S3 table written to tmp_path raises GroupTableError
        pois_corrupt = json.loads(_upstream_case_path("pois_01.json").read_text(encoding="utf-8"))
        pois_corrupt["group"]["table"]["r"]["s"], pois_corrupt["group"]["table"]["r"]["sr"] = (
            pois_corrupt["group"]["table"]["r"]["sr"],
            pois_corrupt["group"]["table"]["r"]["s"],
        )
        corrupt_path = tmp_path / "pois_01_corrupt_table.json"
        corrupt_path.write_text(json.dumps(pois_corrupt), encoding="utf-8")

        with pytest.raises(holonomy_mod.GroupTableError):
            holonomy_mod.connection_from_case(
                json.loads(corrupt_path.read_text(encoding="utf-8"))
            )
        # Dual evaluator rejects any SOLVED claim on an invalid group table
        ok_dual, _reason, _det = dual_mod.evaluate_dual(
            pois_corrupt,
            {
                "status": "SOLVED",
                "verdict": "NOT_FLAT",
                "plaquette": ["0,0", "1,0", "1,1", "0,1"],
                "holonomy": "r2",
            },
        )
        assert ok_dual is False

        # Negative control 2: Relabelling C6 onto ('e','r','r2','s','sr','sr2') passes FiniteGroup admission
        # as a valid 6-element group, yet has 0 isomorphisms to symmetric_group_s3()
        s3_labels = ("e", "r", "r2", "s", "sr", "sr2")
        c6_on_s3_labels = {
            "name": "S3",
            "elements": list(s3_labels),
            "identity": "e",
            "table": {
                s3_labels[i]: {s3_labels[j]: s3_labels[(i + j) % 6] for j in range(6)}
                for i in range(6)
            },
            "inverses": {s3_labels[i]: s3_labels[(-i) % 6] for i in range(6)},
        }
        pois_c6 = json.loads(_upstream_case_path("pois_01.json").read_text(encoding="utf-8"))
        pois_c6["group"] = c6_on_s3_labels
        pois_c6["edges"]["0,0->0,1"] = "r"
        pois_c6["edges"]["0,1->0,0"] = "sr2"  # inverse of index 1 mod 6 is index 5
        c6_case_path = tmp_path / "pois_01_abelian_c6.json"
        c6_case_path.write_text(json.dumps(pois_c6), encoding="utf-8")

        loaded_c6_conn = holonomy_mod.connection_from_case(
            json.loads(c6_case_path.read_text(encoding="utf-8"))
        )
        assert loaded_c6_conn.group.is_abelian() is True
        assert (
            _enumerate_group_isomorphisms(loaded_c6_conn.group, holonomy_mod.symmetric_group_s3())
            == []
        )

        # Negative control 3: Relabelling D4 onto Q8's 8 symbols passes FiniteGroup admission as nonabelian
        # order-8 group, yet fails both equality and isomorphism to quaternion_group_q8()
        d4 = _dihedral_group_d4(holonomy_mod)
        q8_labels = ("e", "-e", "i", "-i", "j", "-j", "k", "-k")
        d4_to_q8_label = dict(zip(d4.elements, q8_labels, strict=True))
        d4_on_q8_labels = {
            "name": "Q8",
            "elements": list(q8_labels),
            "identity": "e",
            "table": {
                d4_to_q8_label[a]: {
                    d4_to_q8_label[b]: d4_to_q8_label[d4.mul(a, b)] for b in d4.elements
                }
                for a in d4.elements
            },
            "inverses": {
                d4_to_q8_label[a]: d4_to_q8_label[d4.inv(a)] for a in d4.elements
            },
        }
        base13_d4 = json.loads(_upstream_case_path("base_13.json").read_text(encoding="utf-8"))
        base13_d4["group"] = d4_on_q8_labels
        inv_i = d4_on_q8_labels["inverses"]["i"]
        base13_d4["edges"]["0,0->0,1"] = "i"
        base13_d4["edges"]["0,1->0,0"] = inv_i
        d4_case_path = tmp_path / "base_13_d4_substituted.json"
        d4_case_path.write_text(json.dumps(base13_d4), encoding="utf-8")

        loaded_d4_conn = holonomy_mod.connection_from_case(
            json.loads(d4_case_path.read_text(encoding="utf-8"))
        )
        pkg_q8 = holonomy_mod.quaternion_group_q8()
        assert loaded_d4_conn.group.is_abelian() is False
        assert loaded_d4_conn.group != pkg_q8
        assert _enumerate_group_isomorphisms(loaded_d4_conn.group, pkg_q8) == []


class TestShardDSelfAudit:
    """Self-audit over the 6 Shard D deliverables for LF line endings, hygiene, scrubbing, and inventory pins."""

    _OWNED_FILES: tuple[str, ...] = (
        "dag/derivations/audit_p010_017.md",
        "dag/derivations/audit_p010_018.md",
        "dag/derivations/audit_p010_019.md",
        "dag/derivations/audit_p010_020.md",
        "dag/reviews/additional_w5_w2_shard_d.json",
        "tests/test_w5_w2_shard_d.py",
    )

    _HYGIENE_PATTERN = re.compile(
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

    _INTERNAL_NAMES_PATTERN = re.compile(
        r"\b("
        + "|".join(["Ome" + "ga", "ome" + "ga_\\w+", "Anom" + "alon", "Wol" + "and", "OE" + "EIS"])
        + r")\b"
    )

    def test_owned_files_use_pure_lf_and_pass_claim_hygiene_and_internal_name_scrub(
        self,
    ) -> None:
        for rel_path in self._OWNED_FILES:
            full_path = _REPO_ROOT / rel_path
            raw_bytes = full_path.read_bytes()
            assert b"\r" not in raw_bytes, f"CR byte found in {rel_path}"
            assert raw_bytes.endswith(b"\n"), f"Missing trailing LF in {rel_path}"
            text = raw_bytes.decode("utf-8")

            hygiene_hits = self._HYGIENE_PATTERN.findall(text)
            assert hygiene_hits == [], f"Claim Hygiene hits in {rel_path}: {hygiene_hits}"
            name_hits = self._INTERNAL_NAMES_PATTERN.findall(text)
            assert name_hits == [], f"Unscrubbed internal name in {rel_path}: {name_hits}"

    def test_review_json_pins_match_file_inventory_and_git_head_blobs(self) -> None:
        review_path = _REPO_ROOT / "dag" / "reviews" / "additional_w5_w2_shard_d.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))

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

        inventory = {
            entry["path"]: entry["sha256"]
            for entry in json.loads(
                (_REPO_ROOT / "dag" / "file_inventory.json").read_text(encoding="utf-8")
            )["files"]
        }

        reviewed_paths: set[str] = set()
        for entry in review["file_reviews"]:
            path = entry["path"]
            assert not path.startswith("dag/derivations/audit_")
            assert not path.startswith("tests/test_w5_")
            assert path in inventory, f"{path} missing from dag/file_inventory.json"
            assert entry["sha256"] == inventory[path]
            assert entry["full_source_read"] is True

            wt_bytes = (_REPO_ROOT / path).read_bytes()
            assert entry["reviewed_lines"] == [[1, len(wt_bytes.splitlines())]]

            blob_bytes = _git_source_bytes(path, review["source_commit"])
            blob_sha = _sha256_hex(blob_bytes)
            if blob_sha == entry["sha256"]:
                assert "git_blob_sha256" not in entry
                assert "pin_note" not in entry
            else:
                assert entry["git_blob_sha256"] == blob_sha
                crlf_sha = _sha256_hex(blob_bytes.replace(b"\n", b"\r\n"))
                if crlf_sha == entry["sha256"]:
                    assert "pin_note" not in entry
                else:
                    assert isinstance(entry.get("pin_note"), str) and entry["pin_note"]
            reviewed_paths.add(path)

        claim_ids = [claim["id"] for claim in review["claims"]]
        assert claim_ids == [
            "AUDIT-P010-017",
            "AUDIT-P010-018",
            "AUDIT-P010-019",
            "AUDIT-P010-020",
        ]
        bare_id_re = re.compile(r"^[A-Z0-9-]+$")
        for claim in review["claims"]:
            assert claim["dependencies"], f"Empty dependencies on {claim['id']}"
            for dep in claim["dependencies"]:
                assert len(dep) > 25 and not bare_id_re.match(dep)
            for ev_path in claim["evidence"]:
                assert ev_path in inventory
                assert ev_path in reviewed_paths

        c017_claim = next(c for c in review["claims"] if c["id"] == "AUDIT-P010-017")
        assert c017_claim["limits"].startswith("Narrows ATL-P010-017 (partial, relation: narrows):")
        assert 'provenance.json["cases"][i]["sha256"]' in c017_claim["statement"]
        assert (
            'provenance.json["cases"][i]["judge_manifest_sha256_crlf"]'
            in c017_claim["statement"]
        )

        audit_017_md = (_REPO_ROOT / "dag" / "derivations" / "audit_p010_017.md").read_text(
            encoding="utf-8"
        )
        assert "- Review verdict: `partial` (`relation: narrows`)" in audit_017_md

        for partial_id in ("AUDIT-P010-018", "AUDIT-P010-019", "AUDIT-P010-020"):
            claim_obj = next(c for c in review["claims"] if c["id"] == partial_id)
            assert claim_obj["limits"].startswith("Complements PAPER010-")
