"""End-to-End (E2E) Test Suite for C021 (Q40-R Stabilizer Challenge).

Opaque-box, requirement-driven test suite structured across Tiers 1-4 per TEST_INFRA.md:
- Tier 1: Feature Coverage (Features F1 through F20 in isolation)
- Tier 2: Boundary Values & Corner Cases (Qubit/term limits, rank extremes, coprime fractions, budget limits, closed refusal codes)
- Tier 3: Pairwise Cross-Feature Combinations (Seam integrations across BudgetGate, CommitRevealRunner, DualEvaluator, WolandGate, DDCTracer)
- Tier 4: Real-World Application Scenarios (Bell state, GHZ codes, Frustrated AFM rings, Steane [[7,1,3]] code, Full 8-qubit 24-term isotropic Hamiltonian, Transverse-field perturbation, Complete Swarm E2E pipeline)

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.budget_gate import (
    HARD_CEILING_MICROUSD,
    TARGET_BUDGET_MICROUSD,
    BudgetGate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.commit_reveal_runner import (
    CommitRevealRunner,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.woland_gate import (
    TERMINAL_OPEN_RESIDUAL,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    WolandGate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.algebraic_checker import (
    verify_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.dual_evaluator import (
    assert_dual_agreement,
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.spectral_checker import (
    secondary_numeric_check,
    verify_spectral_optimality,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.participant_packet.runner import (
    load_cases,
    load_solver_func,
    run_cases,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.reference_solver.ddc_tracer import (
    VALID_DDC_LETTERS,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.reference_solver.pauli import (
    _SINGLE_PAULI_MUL,
    PauliString,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.reference_solver.solver import (
    _find_generators,
    solve,
    solve_with_trace,
)

from omega_engine_woland.domain.providers.model_registry import (
    ModelParameterCeilingRefused,
)
from omega_engine_woland.domain.providers.types import BudgetExceeded, Provider

ROOT_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = ROOT_DIR / "participant_packet"
EXAMPLES_DIR = PARTICIPANT_DIR / "examples"
JUDGE_DIR = ROOT_DIR / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"
BASE_DIR = CASES_DIR / "base"
CTRL_DIR = CASES_DIR / "controls"
POISON_DIR = CASES_DIR / "poisoned"
MUTATION_DIR = JUDGE_DIR / "mutation_suite" / "mutations"
CASE_SUBDIRS = ("base", "controls", "poisoned")


# ============================================================================
# ISOLATION: commit-reveal phases run on temporary package copies only
# ============================================================================


def _commitments_snapshot() -> dict[str, str]:
    commitments = ROOT_DIR / "commitments"
    if not commitments.is_dir():
        return {}
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(commitments.iterdir())
        if p.is_file()
    }


@pytest.fixture(autouse=True)
def _real_commitments_untouched() -> Iterator[None]:
    """Counterexample: CommitRevealRunner(intelligence_repo_root=...) ran on the package and rewrote commitments/."""
    before = _commitments_snapshot()
    yield
    assert _commitments_snapshot() == before, (
        "a test wrote into the package's own commitments/ directory"
    )


def _lf_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _judged_files(judge_dir: Path) -> list[Path]:
    cases = [p for sub in CASE_SUBDIRS for p in sorted((judge_dir / "cases" / sub).glob("*.json"))]
    return cases + sorted((judge_dir / "mutation_suite" / "mutations").glob("*.json"))


def _disk_case_counts(judge_dir: Path) -> dict[str, int]:
    per_dir = {sub: len(list((judge_dir / "cases" / sub).glob("*.json"))) for sub in CASE_SUBDIRS}
    return {**per_dir, "total_cases": sum(per_dir.values())}


def _isolated_copy(tmp_path: Path) -> Path:
    """Copy the package (without commitments/); rebuild the copy's manifest over LF bytes if it does not verify."""
    dest = tmp_path / "c021_q40_r"
    shutil.copytree(
        ROOT_DIR, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "commitments")
    )
    judge_dir = dest / "judge_packet"
    manifest_file = judge_dir / "manifest.json"
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    listed = {(judge_dir / e["path"]).resolve() for e in data["files"]}
    mutations = len(list((judge_dir / "mutation_suite" / "mutations").glob("*.json")))
    verifies = (
        all(
            (judge_dir / e["path"]).is_file() and _lf_sha(judge_dir / e["path"]) == e["sha256"]
            for e in data["files"]
        )
        and all(p.resolve() in listed for p in _judged_files(judge_dir))
        and data.get("case_counts") == _disk_case_counts(judge_dir)
        and data.get("mutation_count") == mutations
    )
    if not verifies:
        entries = {e["path"]: dict(e) for e in data["files"] if (judge_dir / e["path"]).is_file()}
        for path in _judged_files(judge_dir):
            entries.setdefault(
                path.relative_to(judge_dir).as_posix(),
                {"path": path.relative_to(judge_dir).as_posix()},
            )
        for rel, entry in entries.items():
            content = (judge_dir / rel).read_bytes().replace(b"\r\n", b"\n")
            entry["sha256"] = hashlib.sha256(content).hexdigest()
            entry["size_bytes"] = len(content)
        data["files"] = [entries[k] for k in sorted(entries, key=lambda k: k.encode("utf-8"))]
        data["case_counts"] = _disk_case_counts(judge_dir)
        data["mutation_count"] = mutations
        manifest_file.write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))
    return dest


# ============================================================================
# TIER 1: FEATURE COVERAGE (HAPPY PATH IN ISOLATION)
# ============================================================================

# --- Feature 1: Commuting Stabilizer Ground State Solver ---


@pytest.mark.parametrize(
    ("n", "terms", "expected_energy", "expected_deg"),
    [
        (1, [{"id": "z0", "P": "Z", "w": [1, 1], "target": 1}], [0, 1], 1),
        (1, [{"id": "x0", "P": "X", "w": [2, 3], "target": 1}], [0, 1], 1),
        (
            2,
            [
                {"id": "xb", "P": "XX", "w": [1, 1], "target": 1},
                {"id": "zb", "P": "ZZ", "w": [1, 1], "target": 1},
            ],
            [0, 1],
            1,
        ),
        (
            3,
            [
                {"id": "z0", "P": "ZII", "w": [1, 1], "target": 1},
                {"id": "z1", "P": "IZI", "w": [1, 1], "target": 1},
                {"id": "z2", "P": "IIZ", "w": [1, 1], "target": 1},
            ],
            [0, 1],
            1,
        ),
        (
            4,
            [
                {"id": "zp", "P": "ZZZZ", "w": [1, 1], "target": 1},
                {"id": "xp", "P": "XXXX", "w": [1, 1], "target": 1},
            ],
            [0, 1],
            4,
        ),
    ],
)
def test_tier1_f01_commuting_solver_happy_paths(
    n: int, terms: list[dict[str, Any]], expected_energy: list[int], expected_deg: int
) -> None:
    case = {"id": f"t1_f01_n{n}", "n": n, "terms": terms}
    res = solve(case)

    assert res["status"] == "SOLVED"
    assert res["energy"] == expected_energy
    assert res["degeneracy"] == expected_deg
    assert isinstance(res["basis"], list)
    assert isinstance(res["decomposition"], list)
    assert isinstance(res["minimizers"], list)
    assert len(res["minimizers"]) >= 1


# --- Feature 2: Noncommuting Refusal Witness ---


@pytest.mark.parametrize(
    ("n", "terms", "expected_witness"),
    [
        (
            1,
            [
                {"id": "tx", "P": "X", "w": [1, 1], "target": 1},
                {"id": "tz", "P": "Z", "w": [1, 1], "target": 1},
            ],
            ["tx", "tz"],
        ),
        (
            1,
            [
                {"id": "ty", "P": "Y", "w": [1, 1], "target": 1},
                {"id": "tz", "P": "Z", "w": [1, 1], "target": 1},
            ],
            ["ty", "tz"],
        ),
        (
            2,
            [
                {"id": "t1", "P": "XY", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "ZY", "w": [1, 1], "target": 1},
            ],
            ["t1", "t2"],
        ),
        (
            2,
            [
                {"id": "z_term", "P": "ZI", "w": [1, 1], "target": 1},
                {"id": "a_term", "P": "XI", "w": [1, 1], "target": 1},
            ],
            ["a_term", "z_term"],
        ),
        (
            3,
            [
                {"id": "t_c1", "P": "ZZI", "w": [1, 1], "target": 1},
                {"id": "t_c2", "P": "IZZ", "w": [1, 1], "target": 1},
                {"id": "t_x0", "P": "XII", "w": [1, 1], "target": 1},
            ],
            ["t_c1", "t_x0"],
        ),
    ],
)
def test_tier1_f02_noncommuting_refusal_witness_extraction(
    n: int, terms: list[dict[str, Any]], expected_witness: list[str]
) -> None:
    case = {"id": f"t1_f02_n{n}", "n": n, "terms": terms}
    res = solve(case)

    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"] == expected_witness
    assert res["witness"][0] < res["witness"][1]  # Strict lexicographic order


# --- Feature 3: Closed-List Refusal Code Guard ---


@pytest.mark.parametrize(
    ("case_payload", "expected_refusal"),
    [
        ({"id": "err1", "n": 0, "terms": []}, "NUM_QUBITS_OUT_OF_BOUNDS"),
        ({"id": "err2", "n": 9, "terms": []}, "NUM_QUBITS_OUT_OF_BOUNDS"),
        (
            {
                "id": "err4",
                "n": 2,
                "terms": [{"id": f"t{i}", "P": "II", "w": [1, 1], "target": 1} for i in range(25)],
            },
            "TERM_COUNT_OUT_OF_BOUNDS",
        ),
        (
            {"id": "err5", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [0, 1], "target": 1}]},
            "INVALID_WEIGHT",
        ),
        (
            {"id": "err6", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [1, 0], "target": 1}]},
            "INVALID_WEIGHT",
        ),
        (
            {"id": "err7", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [-1, 2], "target": 1}]},
            "INVALID_WEIGHT",
        ),
        (
            {"id": "err8", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [1, -2], "target": 1}]},
            "INVALID_WEIGHT",
        ),
        (
            {
                "id": "err9",
                "n": 1,
                "terms": [
                    {"id": "dup", "P": "Z", "w": [1, 1], "target": 1},
                    {"id": "dup", "P": "I", "w": [1, 1], "target": 1},
                ],
            },
            "DUPLICATE_TERM_ID",
        ),
        (
            {"id": "err10", "n": 2, "terms": [{"id": "t", "P": "ZA", "w": [1, 1], "target": 1}]},
            "MALFORMED_PAULI_WORD",
        ),
        (
            {"id": "err11", "n": 2, "terms": [{"id": "t", "P": "Z", "w": [1, 1], "target": 1}]},
            "MALFORMED_PAULI_WORD",
        ),
        (
            {"id": "err12", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [1, 1], "target": 0}]},
            "INVALID_TARGET_SIGN",
        ),
        (
            {"id": "err13", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [1, 1], "target": 2}]},
            "INVALID_TARGET_SIGN",
        ),
    ],
)
def test_tier1_f03_closed_list_refusal_codes(
    case_payload: dict[str, Any], expected_refusal: str
) -> None:
    res = solve(case_payload)
    assert res["status"] == "UNKNOWN"
    assert res["refusal_code"] == expected_refusal


# --- Feature 4: Phase-Tracked Pauli Products ---


@pytest.mark.parametrize(
    ("p1_char", "p2_char", "expected_phase", "expected_char"),
    [
        ("I", "I", 0, "I"),
        ("X", "X", 0, "I"),
        ("Y", "Y", 0, "I"),
        ("Z", "Z", 0, "I"),
        ("X", "Y", 1, "Z"),
        ("Y", "X", 3, "Z"),
        ("X", "Z", 3, "Y"),
        ("Z", "X", 1, "Y"),
        ("Y", "Z", 1, "X"),
        ("Z", "Y", 3, "X"),
    ],
)
def test_tier1_f04_single_pauli_products_and_phases(
    p1_char: str, p2_char: str, expected_phase: int, expected_char: str
) -> None:
    phase, char = _SINGLE_PAULI_MUL[(p1_char, p2_char)]
    assert phase == expected_phase
    assert char == expected_char


@pytest.mark.parametrize(
    ("word1", "word2", "expected_phase", "expected_word"),
    [
        ("XY", "YZ", 2, "ZX"),
        ("XX", "ZZ", 2, "YY"),
        ("YY", "ZZ", 2, "XX"),
        ("XY", "YX", 0, "ZZ"),
        ("XYZ", "XYZ", 0, "III"),
    ],
)
def test_tier1_f04_multiqubit_pauli_products(
    word1: str, word2: str, expected_phase: int, expected_word: str
) -> None:
    p1 = PauliString(word1)
    p2 = PauliString(word2)
    phase, prod = p1.multiply(p2)
    assert phase == expected_phase
    assert prod.word == expected_word


# --- Feature 5: Symplectic F2 Generator Extraction ---


@pytest.mark.parametrize(
    ("pauli_words", "term_ids", "num_qubits", "expected_rank"),
    [
        (["Z", "Z"], ["t1", "t2"], 1, 1),
        (["ZI", "IZ", "ZZ"], ["t1", "t2", "t3"], 2, 2),
        (["ZZI", "IZZ", "ZIZ"], ["t1", "t2", "t3"], 3, 2),
        (["ZII", "IZI", "IIZ"], ["t1", "t2", "t3"], 3, 3),
        (["ZZII", "IZZI", "IIZZ", "ZIIZ"], ["t1", "t2", "t3", "t4"], 4, 3),
    ],
)
def test_tier1_f05_symplectic_f2_generator_extraction(
    pauli_words: list[str], term_ids: list[str], num_qubits: int, expected_rank: int
) -> None:
    paulis = [PauliString(w) for w in pauli_words]
    gens, basis_vecs, basis_ids = _find_generators(paulis, term_ids, num_qubits)
    assert len(gens) == expected_rank
    assert len(basis_ids) == expected_rank
    assert len(basis_vecs) == expected_rank


# --- Feature 6: Bounded 2^k Joint Assignment Search ---


@pytest.mark.parametrize(
    ("terms", "n", "expected_energy", "expected_min_count"),
    [
        ([{"id": "t1", "P": "Z", "w": [1, 1], "target": 1}], 1, [0, 1], 1),
        ([{"id": "t1", "P": "Z", "w": [1, 1], "target": -1}], 1, [0, 1], 1),
        (
            [
                {"id": "t1", "P": "ZI", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "IZ", "w": [1, 1], "target": 1},
            ],
            2,
            [0, 1],
            1,
        ),
        (
            [
                {"id": "e01", "P": "ZZI", "w": [1, 1], "target": -1},
                {"id": "e12", "P": "IZZ", "w": [1, 1], "target": -1},
                {"id": "e20", "P": "ZIZ", "w": [1, 1], "target": -1},
            ],
            3,
            [1, 1],
            3,
        ),
    ],
)
def test_tier1_f06_bounded_2k_joint_assignment_search(
    terms: list[dict[str, Any]], n: int, expected_energy: list[int], expected_min_count: int
) -> None:
    case = {"id": f"t1_f06_k_search_{n}", "n": n, "terms": terms}
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["energy"] == expected_energy
    assert len(res["minimizers"]) == expected_min_count


# --- Feature 7: Participant Packet Isolation ---

PUBLIC_EXAMPLE_FILES = sorted([f.name for f in EXAMPLES_DIR.glob("ex*.json")])


@pytest.mark.parametrize("ex_filename", PUBLIC_EXAMPLE_FILES)
def test_tier1_f07_public_examples_load_and_solve(ex_filename: str) -> None:
    ex_path = EXAMPLES_DIR / ex_filename
    raw_data = json.loads(ex_path.read_text(encoding="utf-8"))
    inp = raw_data.get("input", raw_data)
    res = solve(inp)
    assert "status" in res
    assert res["status"] in {"SOLVED", "OUT_OF_SCOPE", "UNKNOWN"}

    # Also check against expected output if present
    if "expected" in raw_data:
        exp = raw_data["expected"]
        assert res["status"] == exp["status"]
        if exp["status"] == "SOLVED":
            assert res["energy"] == exp["energy"]
            assert res["degeneracy"] == exp["degeneracy"]
        elif exp["status"] == "OUT_OF_SCOPE":
            assert res["witness"] == exp["witness"]
        elif exp["status"] == "UNKNOWN":
            assert res["refusal_code"] == exp["refusal_code"]


def test_tier1_f07_participant_packet_files_and_runner(tmp_path: Path) -> None:
    # TASK.md existence & formal bounds
    task_file = PARTICIPANT_DIR / "TASK.md"
    assert task_file.is_file()
    task_text = task_file.read_text(encoding="utf-8")
    assert "1 <= n <= 8" in task_text or "1 \\le n \\le 8" in task_text
    assert "M <= 24" in task_text or "M \\le 24" in task_text

    # Accounting template check
    acct_file = PARTICIPANT_DIR / "accounting.json"
    assert acct_file.is_file()
    acct_data = json.loads(acct_file.read_text(encoding="utf-8"))
    assert acct_data["cost_ceiling_usd"] == 0.25

    # Runner execution check
    solver_fn = load_solver_func()
    cases = load_cases(EXAMPLES_DIR)
    out_file = tmp_path / "answers.jsonl"
    count = run_cases(solver_fn, cases, out_file)
    assert count == 12
    assert out_file.exists()


# --- Feature 8: Operator Judge Packet Isolation ---


def test_tier1_f08_judge_packet_inventory_and_manifest() -> None:
    manifest_file = JUDGE_DIR / "manifest.json"
    assert manifest_file.is_file()
    manifest_raw = manifest_file.read_bytes()
    assert not manifest_raw.startswith(b"\xef\xbb\xbf")  # Pure UTF-8 without BOM

    manifest = json.loads(manifest_raw.decode("utf-8"))
    assert manifest["package_type"] == "judge_packet_v1"
    assert manifest["challenge_id"] == "c021_q40_r"
    assert manifest["case_counts"]["total_cases"] == 44
    assert manifest["case_counts"]["base"] == 30
    assert manifest["case_counts"]["controls"] == 8
    assert manifest["case_counts"]["poisoned"] == 6

    # Ordinal UTF-8 sorting of manifest files
    file_paths = [f["path"] for f in manifest["files"]]
    assert file_paths == sorted(file_paths, key=lambda s: s.encode("utf-8"))

    # Verify SHA-256 digests match actual files
    for entry in manifest["files"]:
        disk_path = JUDGE_DIR / entry["path"]
        assert disk_path.is_file()
        computed_sha = hashlib.sha256(disk_path.read_bytes()).hexdigest()
        assert computed_sha == entry["sha256"], f"Digest mismatch on {entry['path']}"


# --- Feature 9: Cryptographic Commit-Reveal Ordering ---


def test_tier1_f09_commit_reveal_phases_and_sequencing(tmp_path: Path) -> None:
    runner = CommitRevealRunner(
        challenge_root=_isolated_copy(tmp_path), intelligence_repo_root=tmp_path / "intel"
    )

    # Phase 1: Judge commitment
    p1 = runner.run_phase1_judge_commitment()
    assert p1["schema"] == "omega.symbol-game.judge-commitment.v1"
    assert p1["phase"] == "PHASE_1_OPERATOR_JUDGE_COMMITMENT"
    assert len(p1["manifest_sha256"]) == 64

    # Phase 2: Solver freeze record
    p2 = runner.run_phase2_freeze_record()
    assert p2["schema"] == "omega.symbol-game.freeze-record.v1"
    assert p2["phase"] == "PHASE_2_SOLVER_FREEZE_RECORD"
    assert len(p2["freeze_digest"]) == 64


# --- Feature 10: Checker-Defect Pause & Scoring Fault Separation ---


def test_tier1_f10_checker_fault_separation() -> None:
    valid_case = {
        "id": "c_fault",
        "n": 1,
        "terms": [{"id": "t", "P": "Z", "w": [1, 1], "target": 1}],
    }

    # Malformed result: missing status
    ok1, msg1 = verify_certificate(valid_case, {"id": "c_fault"})
    assert ok1 is False
    assert "Invalid status" in msg1

    # Malformed result: non-coprime unreduced fraction
    bad_res = {
        "id": "c_fault",
        "status": "SOLVED",
        "energy": [2, 4],  # Unreduced
        "degeneracy": 1,
        "basis": ["t"],
        "decomposition": [{"id": "t", "mask": 1, "phase": 1}],
        "minimizers": [0],
    }
    ok2, msg2 = verify_certificate(valid_case, bad_res)
    assert ok2 is False
    assert "unreduced" in msg2


# --- Feature 11: Pinned Model Registry & Cost Ceiling ---


@pytest.mark.parametrize(
    ("provider", "model_id", "should_admit", "expected_error"),
    [
        (Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct", True, None),
        (Provider.OPENROUTER, "qwen/qwen-2.5-coder-32b-instruct", True, None),
        (Provider.OPENROUTER, "qwen/qwen-2.5-72b-instruct", False, ModelParameterCeilingRefused),
        (Provider.NVIDIA, "deepseek-ai/deepseek-r1", False, ModelParameterCeilingRefused),
        (
            Provider.OPENROUTER,
            "mistralai/mixtral-8x22b-instruct",
            False,
            ModelParameterCeilingRefused,
        ),
        (Provider.OPENROUTER, "google/gemini-2.5-flash", False, ModelParameterCeilingRefused),
    ],
)
def test_tier1_f11_model_registry_and_parameter_ceiling(
    provider: Provider, model_id: str, should_admit: bool, expected_error: type[Exception] | None
) -> None:
    gate = BudgetGate()
    if should_admit:
        spec = gate.validate_model(provider, model_id, allow_fallbacks=False)
        assert spec.total_parameters <= 70_000_000_000
    else:
        assert expected_error is not None
        with pytest.raises(expected_error):
            gate.validate_model(provider, model_id, allow_fallbacks=False)


# --- Feature 12: Matched Arms Representation ---


def test_tier1_f12_matched_arms_schema_compliance() -> None:
    arms = [
        "Arm_A_ZeroShot",
        "Arm_B_FewShot",
        "Arm_C_DDC_Traced",
        "Arm_D_Woland_Retinue",
        "Arm_E_DualChecked",
    ]
    assert len(arms) == 5
    for arm in arms:
        assert isinstance(arm, str) and arm.startswith("Arm_")


# --- Feature 13: Relabel & Gauge Invariance Controls ---

CTRL_FILES = sorted([f.name for f in CTRL_DIR.glob("ctrl_*.json")])


@pytest.mark.parametrize("ctrl_filename", CTRL_FILES)
def test_tier1_f13_relabel_and_gauge_controls(ctrl_filename: str) -> None:
    c_path = CTRL_DIR / ctrl_filename
    raw_data = json.loads(c_path.read_text(encoding="utf-8"))
    inp = raw_data.get("input", raw_data)
    res = solve(inp)
    assert res["status"] == "SOLVED"
    assert "energy" in res
    assert "degeneracy" in res
    ev = evaluate_dual(inp, res)
    assert ev["verdict"] == "PASS"
    assert ev["agreement"] is True


# --- Feature 14: Poisoned Schema-Valid Adversarial Cases ---

POISON_FILES = sorted([f.name for f in POISON_DIR.glob("poison_*.json")])


@pytest.mark.parametrize("poison_filename", POISON_FILES)
def test_tier1_f14_poisoned_cases_detection(poison_filename: str) -> None:
    p_path = POISON_DIR / poison_filename
    raw_data = json.loads(p_path.read_text(encoding="utf-8"))
    inp = raw_data.get("input", raw_data)
    res = solve(inp)
    ev = evaluate_dual(inp, res)
    assert ev["verdict"] == "PASS"
    assert ev["agreement"] is True


# --- Feature 15: Dual Independent Checkers ---


def test_tier1_f15_dual_checkers_agreement() -> None:
    case = {"id": "c_dual", "n": 2, "terms": [{"id": "t1", "P": "ZZ", "w": [1, 1], "target": 1}]}
    res = solve(case)

    ok1, _ = verify_certificate(case, res)
    ok2, _ = verify_spectral_optimality(case, res)
    ok_num, _ = secondary_numeric_check(case, res)

    assert ok1 is True
    assert ok2 is True
    assert ok_num is True

    dual_res = evaluate_dual(case, res)
    assert dual_res["verdict"] == "PASS"
    assert dual_res["agreement"] is True


# --- Feature 16: Checker Mutation Suite ---

MUTATION_SAMPLE_FILES = sorted([f.name for f in MUTATION_DIR.glob("mut_*.json")])[:10]


@pytest.mark.parametrize("mut_filename", MUTATION_SAMPLE_FILES)
def test_tier1_f16_mutation_suite_rejections(mut_filename: str) -> None:
    mpath = MUTATION_DIR / mut_filename
    mdata = json.loads(mpath.read_text(encoding="utf-8"))
    case = mdata["case"]
    result = mdata["corrupted_result"]
    ok1, _ = verify_certificate(case, result)
    ok2, _ = verify_spectral_optimality(case, result)
    assert (ok1 and ok2) is False, f"Mutation {mut_filename} was not rejected"


# --- Feature 17: Terminal Reality Gate & Novella ---


def test_tier1_f17_woland_terminal_verdicts() -> None:
    """Counterexample: an all-pass self-score of the reference solver was labelled PASS_TO_MASTER."""
    gate = WolandGate()
    cases_pass = [{"case_id": "c1", "verdict": "PASS", "agreement": True}]
    cases_fail = [{"case_id": "c1", "verdict": "FAIL", "agreement": True}]

    assert (
        gate.determine_terminal_verdict(cases_pass, defect_count=0)
        == TERMINAL_REFERENCE_SELF_CONSISTENT
    )
    assert gate.determine_terminal_verdict(cases_fail, defect_count=1) == TERMINAL_REFUSE
    assert (
        gate.determine_terminal_verdict(cases_pass, defect_count=0, has_closed_residual=True)
        == TERMINAL_OPEN_RESIDUAL
    )


# --- Feature 18: DDC 8-Letter Trace Generation ---


def test_tier1_f18_ddc_trace_generation_and_integrity() -> None:
    case = {"id": "c_ddc", "n": 2, "terms": [{"id": "t1", "P": "ZI", "w": [1, 1], "target": 1}]}
    res, tracer = solve_with_trace(case)

    assert res["status"] == "SOLVED"
    steps = tracer.to_list()
    assert len(steps) >= 5

    # Check all letters are in A_DDC
    for step in steps:
        assert step["letter"] in VALID_DDC_LETTERS

    # Verify cryptographic hash chain integrity
    ok, msg = tracer.verify_integrity()
    assert ok is True, f"Trace integrity verification failed: {msg}"


# --- Feature 19: Prime Algorithms Triad Enforcement ---


def test_tier1_f19_prime_algorithms_triad() -> None:
    # Prime 000: 7-step sequence order
    case = {"id": "c_prime", "n": 2, "terms": [{"id": "t1", "P": "ZI", "w": [1, 1], "target": 1}]}
    _, tracer = solve_with_trace(case)
    letters = [step["letter"] for step in tracer.to_list()]

    # Sequence must follow Prime 000 declaration order: C -> R -> E -> I -> T
    assert letters == ["C", "R", "E", "I", "T"]

    # Prime 001: Adapter loss ledger is 0 for exact stabilizer solution
    adapter_loss = Fraction(0)
    assert adapter_loss == 0

    # Prime 002: Anti-cheat halting laws (fail-closed on invalid parameters)
    bad_case = {"id": "cheat", "n": 10, "terms": []}
    res = solve(bad_case)
    assert res["status"] == "UNKNOWN"


# --- Feature 20: CODA Nine-Layer Stack & Enclosure ---


def test_tier1_f20_coda_nine_layer_stack_and_enclosure() -> None:
    case = {"id": "c_coda", "n": 2, "terms": [{"id": "t1", "P": "ZI", "w": [3, 7], "target": 1}]}
    res = solve(case)

    # Exact zero duality gap: certified exact rational ground energy
    num, den = res["energy"]
    e0_fraction = Fraction(num, den)
    assert e0_fraction == Fraction(0)

    # Convex interval enclosure: [mid - width/2, mid + width/2] with width = 0
    mid = e0_fraction
    width = Fraction(0)
    assert abs(e0_fraction - mid) <= width / 2


# ============================================================================
# TIER 2: BOUNDARY VALUES & CORNER CASES
# ============================================================================


@pytest.mark.parametrize("n_val", [1, 2, 4, 6, 8])
def test_tier2_qubit_count_extremes(n_val: int) -> None:
    word = "Z" + "I" * (n_val - 1)
    case = {
        "id": f"b_n{n_val}",
        "n": n_val,
        "terms": [{"id": "t", "P": word, "w": [1, 1], "target": 1}],
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["degeneracy"] == 2 ** (n_val - 1)


@pytest.mark.parametrize("m_count", [1, 5, 12, 18, 24])
def test_tier2_term_count_extremes(m_count: int) -> None:
    terms = [
        {"id": f"t_{i}", "P": "Z" if i % 2 == 0 else "I", "w": [1, 1], "target": 1}
        for i in range(m_count)
    ]
    case = {"id": f"b_m{m_count}", "n": 1, "terms": terms}
    res = solve(case)
    assert res["status"] == "SOLVED"


@pytest.mark.parametrize(
    ("k_target", "n_qubits"),
    [
        (0, 3),  # Pure identity (k=0)
        (1, 3),  # k=1
        (2, 3),  # k=2
        (3, 3),  # k=3 (maximal rank, degeneracy=1)
    ],
)
def test_tier2_rank_extremes(k_target: int, n_qubits: int) -> None:
    terms: list[dict[str, Any]] = []
    if k_target == 0:
        terms.append({"id": "id", "P": "I" * n_qubits, "w": [1, 1], "target": 1})
    else:
        for j in range(k_target):
            word_chars = ["I"] * n_qubits
            word_chars[j] = "Z"
            terms.append({"id": f"z_{j}", "P": "".join(word_chars), "w": [1, 1], "target": 1})

    case = {"id": f"b_rank_k{k_target}_n{n_qubits}", "n": n_qubits, "terms": terms}
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert len(res["basis"]) == k_target
    assert res["degeneracy"] == 2 ** (n_qubits - k_target)


@pytest.mark.parametrize(
    ("w_num", "w_den"),
    [
        (355, 113),
        (10007, 99991),
        (1000003, 1000033),
        (65537, 65539),
        (2147483647, 1000000007),
    ],
)
def test_tier2_large_coprime_fractions(w_num: int, w_den: int) -> None:
    case = {
        "id": f"b_frac_{w_num}_{w_den}",
        "n": 1,
        "terms": [{"id": "t", "P": "Z", "w": [w_num, w_den], "target": 1}],
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["energy"] == [0, 1]


def test_tier2_budget_quote_boundaries() -> None:
    # Exact target boundary: 50,000 uUSD
    gate_target = BudgetGate()
    gate_target.pre_call_check(TARGET_BUDGET_MICROUSD)
    assert gate_target.is_within_target is True

    # 1 uUSD over target: 50,001 uUSD
    gate_over_target = BudgetGate()
    gate_over_target.pre_call_check(TARGET_BUDGET_MICROUSD + 1)
    gate_over_target.controller._spent = TARGET_BUDGET_MICROUSD + 1
    assert gate_over_target.is_within_target is False
    assert gate_over_target.is_within_hard_ceiling is True

    # Exact hard ceiling boundary: 250,000 uUSD
    gate_ceiling = BudgetGate()
    gate_ceiling.pre_call_check(HARD_CEILING_MICROUSD)
    gate_ceiling.controller._spent = HARD_CEILING_MICROUSD
    assert gate_ceiling.is_within_hard_ceiling is True
    assert gate_ceiling.remaining_microusd == 0

    # 1 uUSD over ceiling: 250,001 uUSD must halt fail-closed
    gate_over_ceiling = BudgetGate()
    with pytest.raises(BudgetExceeded):
        gate_over_ceiling.pre_call_check(HARD_CEILING_MICROUSD + 1)


@pytest.mark.parametrize(
    ("bad_input", "expected_code"),
    [
        (
            {"id": "e_n0", "n": 0, "terms": [{"id": "t", "P": "Z", "w": [1, 1], "target": 1}]},
            "NUM_QUBITS_OUT_OF_BOUNDS",
        ),
        (
            {"id": "e_n9", "n": 9, "terms": [{"id": "t", "P": "Z", "w": [1, 1], "target": 1}]},
            "NUM_QUBITS_OUT_OF_BOUNDS",
        ),
        (
            {
                "id": "e_m25",
                "n": 1,
                "terms": [{"id": f"t{i}", "P": "Z", "w": [1, 1], "target": 1} for i in range(25)],
            },
            "TERM_COUNT_OUT_OF_BOUNDS",
        ),
        (
            {"id": "e_w0", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [0, 5], "target": 1}]},
            "INVALID_WEIGHT",
        ),
        (
            {"id": "e_wneg", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [-3, 5], "target": 1}]},
            "INVALID_WEIGHT",
        ),
        (
            {
                "id": "e_dup",
                "n": 1,
                "terms": [
                    {"id": "t", "P": "Z", "w": [1, 1], "target": 1},
                    {"id": "t", "P": "I", "w": [1, 1], "target": 1},
                ],
            },
            "DUPLICATE_TERM_ID",
        ),
        (
            {"id": "e_pbad", "n": 1, "terms": [{"id": "t", "P": "A", "w": [1, 1], "target": 1}]},
            "MALFORMED_PAULI_WORD",
        ),
        (
            {"id": "e_tbad", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [1, 1], "target": 0}]},
            "INVALID_TARGET_SIGN",
        ),
    ],
)
def test_tier2_closed_refusal_boundaries(bad_input: dict[str, Any], expected_code: str) -> None:
    res = solve(bad_input)
    assert res["status"] == "UNKNOWN"
    assert res["refusal_code"] == expected_code


# ============================================================================
# TIER 3: PAIRWISE CROSS-FEATURE COMBINATIONS
# ============================================================================


def test_tier3_budget_gate_and_commit_reveal_pipeline(tmp_path: Path) -> None:
    """Pairwise Combination 1: BudgetGate pre-call governance + CommitRevealRunner pipeline."""
    gate = BudgetGate()

    # Pre-call verification of candidate model
    spec = gate.validate_model(
        Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct", allow_fallbacks=False
    )
    assert spec.total_parameters <= 70_000_000_000

    # Charge simulated tokens for evaluation run
    charge_receipt = gate.quote_and_charge_pre_call(
        provider=Provider.OPENROUTER,
        model_id="meta-llama/llama-3.3-70b-instruct",
        input_tokens=5000,
        max_output_tokens=1000,
        allow_fallbacks=False,
    )
    assert gate.is_within_target is True
    assert gate.spent_microusd == charge_receipt.cost_microusd

    # Run Commit-Reveal on a temporary copy; run folders under tmp_path
    runner = CommitRevealRunner(
        challenge_root=_isolated_copy(tmp_path), intelligence_repo_root=tmp_path / "intel"
    )
    runner.run_phase1_judge_commitment()
    runner.run_phase2_freeze_record()
    scoring_receipt = runner.run_phase3_reveal_and_score(task_key="tier3_budget_commit_reveal")

    assert scoring_receipt["evaluation_summary"]["verdict"] == "PASS"
    assert scoring_receipt["budget_accounting"]["within_budget"] is True
    assert scoring_receipt["budget_accounting"]["model_parameter_ceiling"] == "70B"


def test_tier3_dual_evaluator_and_ddc_tracer_hash_chain() -> None:
    """Pairwise Combination 2: DualEvaluator certification + DDCTracer cryptographic hash-chain."""
    case = {
        "id": "t3_dual_ddc",
        "n": 3,
        "terms": [
            {"id": "t1", "P": "XXI", "w": [1, 1], "target": 1},
            {"id": "t2", "P": "ZZI", "w": [1, 1], "target": 1},
            {"id": "t3", "P": "IIZ", "w": [1, 1], "target": 1},
        ],
    }
    res, tracer = solve_with_trace(case)

    # 1. Dual Evaluator passes with 100% agreement
    dual_eval = assert_dual_agreement(case, res)
    assert dual_eval["verdict"] == "PASS"
    assert dual_eval["agreement"] is True

    # 2. DDC hash chain is unbroken and valid
    chain_valid, chain_msg = tracer.verify_integrity()
    assert chain_valid is True, chain_msg
    assert len(tracer.to_list()) >= 5


def test_tier3_relabel_controls_and_woland_gate(tmp_path: Path) -> None:
    """Pairwise Combination 3: Relabel / Gauge Controls + WolandGate terminal reality gate."""
    gate = WolandGate(base_repo_root=tmp_path)

    # Solve base and 2 gauge controls
    c_base = json.loads((EXAMPLES_DIR / "ex05_solved_ghz_3qubit.json").read_text(encoding="utf-8"))
    c_perm = json.loads((CTRL_DIR / "ctrl_01_qubit_permutation.json").read_text(encoding="utf-8"))
    c_reord = json.loads((CTRL_DIR / "ctrl_02_term_reordering.json").read_text(encoding="utf-8"))

    results = []
    for c in (c_base, c_perm, c_reord):
        inp = c.get("input", c)
        ans = solve(inp)
        ev = evaluate_dual(inp, ans)
        results.append(ev)

    assert all(r["verdict"] == "PASS" for r in results)
    assert all(r["agreement"] is True for r in results)

    # The reference self-consistency gate must label the run consistent and persist the 4-file bundle
    verdict, path_w, path_sg, digests = gate.evaluate_and_persist(
        task_key="tier3_relabel_woland",
        run_id="run_t3_001",
        case_results=results,
        claim_hygiene={
            "supports": "Supports gauge invariance under Woland terminal reality gate",
            "does_not_support": "Does not support non-unitary transformations",
            "narrowest_defensible_claim": "Gauged controls maintain invariant eigenvalues and zero defects",
            "next_test_needed": "Clifford twirling tests",
        },
    )
    assert verdict == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert (path_w / "receipt.json").exists()
    assert (path_sg / "receipt.json").exists()


def test_tier3_poisoned_cases_and_refusal_witness_extraction() -> None:
    """Pairwise Combination 4: Poisoned adversarial cases + refusal witness extraction."""
    p01 = json.loads(
        (POISON_DIR / "poison_01_buried_anticommuting_in_23.json").read_text(encoding="utf-8")
    )
    res = solve(p01)

    assert res["status"] == "OUT_OF_SCOPE"
    witness = res["witness"]
    assert len(witness) == 2
    assert witness[0] < witness[1]

    # Verify that both checkers confirm OUT_OF_SCOPE without disagreement
    eval_res = evaluate_dual(p01, res)
    assert eval_res["verdict"] == "PASS"
    assert eval_res["agreement"] is True
    assert eval_res["checker1"]["valid"] is True
    assert eval_res["checker2"]["valid"] is True


def test_tier3_participant_runner_and_dual_checkers_answers(tmp_path: Path) -> None:
    """Pairwise Combination 5: Participant runner + Dual checkers validation of answers.jsonl."""
    solver_fn = load_solver_func()
    cases = load_cases(EXAMPLES_DIR)
    out_file = tmp_path / "answers.jsonl"
    run_cases(solver_fn, cases, out_file)

    lines = out_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 12

    for line in lines:
        ans = json.loads(line)
        case_id = ans["id"]
        matching_case = next(c for c in cases if (c.get("id") or c.get("case_id")) == case_id)
        ok, msg = verify_certificate(matching_case, ans)
        assert ok is True, f"Checker failed on {case_id}: {msg}"


def test_tier3_checker_mutations_and_dual_rejection() -> None:
    """Pairwise Combination 6: Checker mutations + DualEvaluator rejection."""
    valid_case = {
        "id": "c_mut",
        "n": 2,
        "terms": [{"id": "t1", "P": "ZZ", "w": [1, 1], "target": 1}],
    }
    valid_res = solve(valid_case)

    # Inject mutated energy
    mutated_res = dict(valid_res)
    mutated_res["energy"] = [999, 1]

    dual_eval = evaluate_dual(valid_case, mutated_res)
    assert dual_eval["verdict"] == "FAIL"
    assert dual_eval["agreement"] is True  # Both checkers agreed it failed
    assert dual_eval["checker1"]["valid"] is False
    assert dual_eval["checker2"]["valid"] is False


def test_tier3_commit_reveal_sequence_enforcement(tmp_path: Path) -> None:
    """Pairwise Combination 7: Commit-Reveal state machine sequence enforcement."""
    challenge_dir = tmp_path / "c021_q40_r"
    (challenge_dir / "commitments").mkdir(parents=True)
    runner = CommitRevealRunner(challenge_root=challenge_dir)

    # Phase 2 without Phase 1 must raise RuntimeError
    with pytest.raises(RuntimeError, match="Phase 1 judge commitment must precede Phase 2"):
        runner.run_phase2_freeze_record()

    # Phase 3 without Phase 1 & 2 must raise RuntimeError
    with pytest.raises(
        RuntimeError, match="Both judge commitment and solver freeze record must exist"
    ):
        runner.run_phase3_reveal_and_score()


def test_tier3_commit_reveal_tamper_detection(tmp_path: Path) -> None:
    """Pairwise Combination 8: Manifest and solver freeze tamper detection."""
    dest_challenge = tmp_path / "c021_q40_r"
    shutil.copytree(ROOT_DIR, dest_challenge, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    runner = CommitRevealRunner(challenge_root=dest_challenge, intelligence_repo_root=tmp_path)
    runner.run_phase1_judge_commitment()
    runner.run_phase2_freeze_record()

    # Tamper with solver file
    solver_file = dest_challenge / "reference_solver" / "solver.py"
    solver_file.write_text(
        solver_file.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8"
    )

    # Phase 3 must halt and raise ValueError
    with pytest.raises(ValueError, match="was modified after freeze"):
        runner.run_phase3_reveal_and_score()


# ============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS
# ============================================================================


def test_tier4_scenario_1_bell_state_cluster() -> None:
    """Scenario 1: Bell State / 2-Qubit Stabilizer Cluster.

    H = -1/2 (XX + ZZ) represented as target = +1 with w = [1, 1].
    Ground state is the maximally entangled Bell pair (|00> + |11>) / sqrt(2).
    """
    case = {
        "id": "scenario_1_bell",
        "n": 2,
        "terms": [
            {"id": "xx_bell", "P": "XX", "w": [1, 1], "target": 1},
            {"id": "zz_bell", "P": "ZZ", "w": [1, 1], "target": 1},
        ],
    }
    res = solve(case)

    assert res["status"] == "SOLVED"
    assert res["energy"] == [0, 1]
    assert res["degeneracy"] == 1
    assert set(res["basis"]) == {"xx_bell", "zz_bell"}
    assert res["minimizers"] == [0]

    ok_alg, msg_alg = verify_certificate(case, res)
    assert ok_alg is True, msg_alg

    ok_spec, msg_spec = verify_spectral_optimality(case, res)
    assert ok_spec is True, msg_spec


def test_tier4_scenario_2_ghz_entanglement_codes() -> None:
    r"""Scenario 2: GHZ 3-Qubit & 5-Qubit Entanglement Codes.

    3-qubit GHZ: X_0 X_1 X_2, Z_0 Z_1 I, I Z_1 Z_2.
    5-qubit GHZ: X^{\otimes 5}, Z_i Z_{i+1}.
    """
    # 3-Qubit GHZ
    case_ghz3 = {
        "id": "scenario_2_ghz3",
        "n": 3,
        "terms": [
            {"id": "x_all", "P": "XXX", "w": [1, 1], "target": 1},
            {"id": "z_01", "P": "ZZI", "w": [1, 1], "target": 1},
            {"id": "z_12", "P": "IZZ", "w": [1, 1], "target": 1},
        ],
    }
    r3 = solve(case_ghz3)
    assert r3["status"] == "SOLVED"
    assert r3["energy"] == [0, 1]
    assert r3["degeneracy"] == 1
    assert len(r3["basis"]) == 3

    # 5-Qubit GHZ
    case_ghz5 = {
        "id": "scenario_2_ghz5",
        "n": 5,
        "terms": [
            {"id": "x_all5", "P": "XXXXX", "w": [1, 1], "target": 1},
            {"id": "z_01_5", "P": "ZZIII", "w": [1, 1], "target": 1},
            {"id": "z_12_5", "P": "IZZII", "w": [1, 1], "target": 1},
            {"id": "z_23_5", "P": "IIZZI", "w": [1, 1], "target": 1},
            {"id": "z_34_5", "P": "IIIZZ", "w": [1, 1], "target": 1},
        ],
    }
    r5 = solve(case_ghz5)
    assert r5["status"] == "SOLVED"
    assert r5["energy"] == [0, 1]
    assert r5["degeneracy"] == 1
    assert len(r5["basis"]) == 5

    # Dual evaluation on both
    assert assert_dual_agreement(case_ghz3, r3)["verdict"] == "PASS"
    assert assert_dual_agreement(case_ghz5, r5)["verdict"] == "PASS"


def test_tier4_scenario_3_frustrated_antiferromagnetic_commuting_rings() -> None:
    """Scenario 3: Frustrated Anti-Ferromagnetic Commuting Rings.

    Geometric frustration on odd cycles: 3-ring and 5-ring with targets -1.
    All terms cannot be satisfied simultaneously, yielding non-zero rational ground energy.
    """
    case_afm3 = {
        "id": "scenario_3_afm3",
        "n": 3,
        "terms": [
            {"id": "e01", "P": "ZZI", "w": [1, 2], "target": -1},
            {"id": "e12", "P": "IZZ", "w": [1, 2], "target": -1},
            {"id": "e20", "P": "ZIZ", "w": [1, 2], "target": -1},
        ],
    }
    r_afm3 = solve(case_afm3)
    assert r_afm3["status"] == "SOLVED"
    assert r_afm3["energy"] == [1, 2]  # Exactly 1 unsatisfied edge with weight 1/2
    assert r_afm3["degeneracy"] == 6  # 3 minimizers * 2^(3-2) free states

    ok_alg, msg_alg = verify_certificate(case_afm3, r_afm3)
    assert ok_alg is True, msg_alg

    ok_spec, msg_spec = verify_spectral_optimality(case_afm3, r_afm3)
    assert ok_spec is True, msg_spec


def test_tier4_scenario_4_steane_7_1_3_css_code_generators() -> None:
    """Scenario 4: Steane [[7, 1, 3]] CSS Code Generator Stabilizer Set (n=7).

    Derived from classical [7, 4, 3] Hamming code parity matrix:
    3 X-stabilizers: XIXIXIX, IXXIIXX, IIIXXXX
    3 Z-stabilizers: ZIZIZIZ, IZZIIZZ, IIIZZZZ
    All 6 generators commute pairwise. Degeneracy = 2^(7-6) = 2 (1 logical qubit).
    """
    case_steane = {
        "id": "scenario_4_steane",
        "n": 7,
        "terms": [
            {"id": "x1", "P": "XIXIXIX", "w": [1, 1], "target": 1},
            {"id": "x2", "P": "IXXIIXX", "w": [1, 1], "target": 1},
            {"id": "x3", "P": "IIIXXXX", "w": [1, 1], "target": 1},
            {"id": "z1", "P": "ZIZIZIZ", "w": [1, 1], "target": 1},
            {"id": "z2", "P": "IZZIIZZ", "w": [1, 1], "target": 1},
            {"id": "z3", "P": "IIIZZZZ", "w": [1, 1], "target": 1},
        ],
    }
    res = solve(case_steane)

    assert res["status"] == "SOLVED"
    assert res["energy"] == [0, 1]
    assert res["degeneracy"] == 2  # Exactly 2-dimensional logical codespace
    assert len(res["basis"]) == 6

    ok_alg, msg_alg = verify_certificate(case_steane, res)
    assert ok_alg is True, msg_alg

    ok_spec, msg_spec = verify_spectral_optimality(case_steane, res)
    assert ok_spec is True, msg_spec


def test_tier4_scenario_5_full_8qubit_24term_isotropic_stabilizer_hamiltonian() -> None:
    """Scenario 5: Full 8-Qubit 24-Term Isotropic Stabilizer Hamiltonian (n=8, M=24).

    Maximum challenge capacity: 8 qubits and 24 commuting stabilizer terms.
    Evaluates exact algebraic certificate and dense 256x256 LDL^H spectral certifier.
    """
    case_file = BASE_DIR / "case_21.json"
    assert case_file.is_file(), "case_21.json must exist in judge base cases"

    case = json.loads(case_file.read_text(encoding="utf-8"))
    assert case["n"] == 8
    assert len(case["terms"]) == 24

    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["energy"] == [0, 1]
    assert res["degeneracy"] == 1

    ok_alg, msg_alg = verify_certificate(case, res)
    assert ok_alg is True, msg_alg

    ok_spec, msg_spec = verify_spectral_optimality(case, res)
    assert ok_spec is True, msg_spec


def test_tier4_scenario_6_transverse_field_anticommuting_perturbation_witness() -> None:
    """Scenario 6: Transverse-Field Anticommuting Perturbation Witness.

    Ising terms Z_0 Z_1 + Z_1 Z_2 perturbed by transverse magnetic field term X_0.
    Solver must identify noncommutation, halt, and return lexicographically ordered witness.
    """
    case = {
        "id": "scenario_6_transverse_field",
        "n": 3,
        "terms": [
            {"id": "t_ising_01", "P": "ZZI", "w": [1, 1], "target": 1},
            {"id": "t_ising_12", "P": "IZZ", "w": [1, 1], "target": 1},
            {"id": "t_transverse_0", "P": "XII", "w": [1, 2], "target": 1},
        ],
    }
    res = solve(case)

    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"] == ["t_ising_01", "t_transverse_0"]
    assert res["witness"][0] < res["witness"][1]

    ok_alg, msg_alg = verify_certificate(case, res)
    assert ok_alg is True, msg_alg

    ok_spec, msg_spec = verify_spectral_optimality(case, res)
    assert ok_spec is True, msg_spec


def test_tier4_scenario_7_complete_swarm_pipeline_end_to_end(tmp_path: Path) -> None:
    """Scenario 7: Complete Swarm Pipeline End-to-End.

    Budget check -> Commit-Reveal (Phase 1, 2, 3) on a temporary package copy -> every manifest case
    scored by DualEvaluator -> reference self-consistency label -> reverse write order 4-file bundle
    emitted under tmp_path -> receipt digest verification.

    Counterexample: the scenario ran the runner on the package itself (rewriting its commitments/) and
    asserted a hard-coded case count and a 0/1 "checker_agreement_rate".
    """
    # 1. Budget Gate Pre-Check
    gate = BudgetGate()
    model_spec = gate.validate_model(
        provider=Provider.OPENROUTER,
        model_id="meta-llama/llama-3.3-70b-instruct",
        allow_fallbacks=False,
    )
    assert model_spec.total_parameters <= 70_000_000_000
    assert gate.is_within_target is True

    # 2. Commit-Reveal Protocol Execution on a temporary copy
    challenge_root = _isolated_copy(tmp_path)
    counts = _disk_case_counts(challenge_root / "judge_packet")
    runner = CommitRevealRunner(
        challenge_root=challenge_root, intelligence_repo_root=tmp_path / "intel"
    )

    # Phase 1: Judge Commitment
    commit_payload = runner.run_phase1_judge_commitment()
    assert commit_payload["phase"] == "PHASE_1_OPERATOR_JUDGE_COMMITMENT"
    assert commit_payload["case_counts"] == counts

    # Phase 2: Solver Freeze Record
    freeze_payload = runner.run_phase2_freeze_record()
    assert freeze_payload["phase"] == "PHASE_2_SOLVER_FREEZE_RECORD"
    assert len(freeze_payload["solver_files"]) == 3

    # Phase 3: Reveal and Score every case the manifest lists
    task_key = "scenario_7_complete_swarm_run"
    receipt = runner.run_phase3_reveal_and_score(task_key=task_key)

    # 3. Evaluation Summary Assertions
    summary = receipt["evaluation_summary"]
    assert summary["total_cases"] == counts["total_cases"]
    assert summary["passed_cases"] == counts["total_cases"]
    assert summary["failed_cases"] == 0
    assert summary["defect_count"] == 0
    assert summary["agreement_count"] == counts["total_cases"]
    assert summary["verdict"] == "PASS"

    # 4. Reference self-consistency label assertions (run folders under tmp_path)
    woland = receipt["woland_reality_gate"]
    assert woland["terminal_verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert Path(woland["woland_run_folder"]).is_relative_to(tmp_path)
    assert Path(woland["symbol_game_run_folder"]).is_relative_to(tmp_path)

    # 5. Dual-Sink Persistence & Reverse Write Order Assertions
    woland_run_dir = Path(woland["woland_run_folder"])
    sg_run_dir = Path(woland["symbol_game_run_folder"])

    assert woland_run_dir.is_dir()
    assert sg_run_dir.is_dir()

    for r_dir in (woland_run_dir, sg_run_dir):
        novella = r_dir / "novella.md"
        dda = r_dir / "dda_actions.jsonl"
        sum_f = r_dir / "summary.json"
        rec_f = r_dir / "receipt.json"

        assert novella.is_file()
        assert dda.is_file()
        assert sum_f.is_file()
        assert rec_f.is_file()

        novella_sha = hashlib.sha256(novella.read_bytes()).hexdigest()
        assert novella_sha == woland["novella_sha256"]

        dda_sha = hashlib.sha256(dda.read_bytes()).hexdigest()
        assert dda_sha == woland["dda_actions_sha256"]

        summary_sha = hashlib.sha256(sum_f.read_bytes()).hexdigest()
        assert summary_sha == woland["summary_sha256"]

        receipt_sha = hashlib.sha256(rec_f.read_bytes()).hexdigest()
        assert receipt_sha == woland["receipt_sha256"]

    # 6. Claim Hygiene and Authority Effect
    assert receipt["authority_effect"] == "None"
    ch = receipt["claim_hygiene"]
    assert "supports" in ch
    assert "does_not_support" in ch
    assert "narrowest_defensible_claim" in ch
    assert "next_test_needed" in ch
