"""Honesty and custody tests for the copied challenge harnesses.

AuthorityEffect: None.

The harness copies (``governance/*.py`` and ``commit_reveal*.py`` in every
challenge package) score the frozen reference solver against the package's own
judge packet. These tests prove, on representative copies and by scanning all of
them, that:

* file digests are taken over bytes with CRLF normalised to LF, so they equal
  git-blob content on every platform;
* an empty suite (0 cases, or 0 mutations) is never labelled consistent;
* the label is REFERENCE_SELF_CONSISTENT / REFERENCE_SELF_INCONSISTENT, and no
  PASS_TO_MASTER string remains in gate-writing code;
* Phase 3 verifies every manifest entry, not only the manifest file;
* a failed bundle write leaves a failure receipt and deletes nothing;
* Phi_1 / Gamma_2 are exact (floats refused, no tolerance);
* run roots come from the resolver, never from ``parents[N]`` arithmetic.

Every write goes to pytest's temporary directories; the challenges conftest
points CORE_INTELLIGENCE_ROOT at one as well.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import re
import shutil
import sys
from fractions import Fraction
from pathlib import Path
from types import ModuleType

import pytest

from operations.use_cases.cicd import challenge_harness_lints as lints

CHALLENGES = Path(__file__).resolve().parents[1]
REPO_ROOT = CHALLENGES.parents[2]
PKG_PREFIX = "projects.mssn_sn_symgam.challenges"

C011 = f"{PKG_PREFIX}.b_cohomology.c011_cycle_rank_ladder_coboundary_repair"
C015 = f"{PKG_PREFIX}.b_cohomology.c015_persistent_homology_barcodes"
C018 = f"{PKG_PREFIX}.b_cohomology.c018_signed_graph_frustration_index"
C032 = f"{PKG_PREFIX}.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation"
FLAT = {
    "c047": f"{PKG_PREFIX}.e_formal_math.c047_sequence_law_discovery.commit_reveal_c047",
    "c052": f"{PKG_PREFIX}.f_program_synthesis.c052_maxflow_mincut_certificates.commit_reveal_c052",
    "w13": f"{PKG_PREFIX}.m_witnessed_difference_programme.w13_lggr_chromatic_obstruction_adjoint_probing.commit_reveal_w13",
}
C052_DIR = CHALLENGES / "f_program_synthesis" / "c052_maxflow_mincut_certificates"

CONSISTENT = "REFERENCE_SELF_CONSISTENT"
INCONSISTENT = "REFERENCE_SELF_INCONSISTENT"

# Representative copies from each harness family, with the name of their LF digest function.
DIGEST_FUNCTIONS = (
    (f"{C011}.governance.commit_reveal_runner", "sha256_of_file"),
    (f"{C015}.governance.commit_reveal_runner", "sha256_of_file"),
    (f"{C018}.governance.commit_reveal_runner", "sha256_of_file"),
    (f"{PKG_PREFIX}.c_quantum.c021_q40_r.governance.commit_reveal_runner", "sha256_of_file"),
    (
        f"{PKG_PREFIX}.d_physics_mtheory.c031_anomaly_free_u1_charges.governance.commit_reveal_runner",
        "sha256_of_file",
    ),
    (
        f"{PKG_PREFIX}.d_physics_mtheory.c036_quintic_gromov_witten_mirror.governance.commit_reveal_runner",
        "sha256_file",
    ),
    (
        f"{PKG_PREFIX}.e_formal_math.c041_lean4_finite_lemma_proofs.governance.commit_reveal_runner",
        "sha256_file",
    ),
    (FLAT["c047"], "hash_file"),
    (FLAT["c052"], "hash_file"),
    (FLAT["w13"], "hash_file"),
)


def _harness_files() -> list[Path]:
    files = {*CHALLENGES.rglob("commit_reveal*.py"), *CHALLENGES.rglob("governance/*.py")}
    return sorted(
        p for p in files if "l_symbol_game" not in p.parts and "harness_tests" not in p.parts
    )


def _package_dir(path: Path) -> Path:
    return path.parent.parent if path.parent.name == "governance" else path.parent


def _load_from_file(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------- static scans


def test_no_pass_to_master_string_remains_in_gate_writing_code() -> None:
    """Counterexample: every copy emitted PASS_TO_MASTER for a reference self-score."""
    files = _harness_files()
    assert len(files) >= 100, f"harness scan found only {len(files)} files"
    offenders = [
        p.relative_to(CHALLENGES).as_posix()
        for p in files
        if "PASS_TO_MASTER" in p.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_every_module_that_names_a_challenge_names_its_own_package() -> None:
    """Counterexample: c012-c014 gates wrote challenge_id c011_cycle_rank_ladder_coboundary_repair."""
    pattern = re.compile(r'^CHALLENGE_ID\s*=\s*"([^"]+)"', re.MULTILINE)
    wrong = []
    for path in _harness_files():
        match = pattern.search(path.read_text(encoding="utf-8"))
        if match and match.group(1) != _package_dir(path).name:
            wrong.append((path.relative_to(CHALLENGES).as_posix(), match.group(1)))
    assert wrong == []


def test_harness_code_deletes_nothing() -> None:
    """Counterexample: c021 rmtree'd partial run folders; c023-c035 rmtree'd existing run folders."""
    deletion = re.compile(r"\brmtree\(|\.unlink\(|\bos\.remove\(|\bos\.rmdir\(")
    offenders = [
        p.relative_to(CHALLENGES).as_posix()
        for p in _harness_files()
        if deletion.search(p.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_harness_run_roots_never_come_from_parent_arithmetic() -> None:
    """Counterexample: commit_reveal_c05x.py used Path(__file__).parents[5] / '_intelligence'."""
    rel = [p.relative_to(REPO_ROOT).as_posix() for p in _harness_files()]
    findings = lints.lint_run_roots(REPO_ROOT, rel)
    assert [f.key for f in findings] == []


def test_harness_files_are_lf_utf8_without_bom() -> None:
    bad = []
    for path in _harness_files():
        data = path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf") or b"\r\n" in data:
            bad.append(path.relative_to(CHALLENGES).as_posix())
    assert bad == []


# ------------------------------------------------------------ LF normalisation


@pytest.mark.parametrize(("module_name", "function_name"), DIGEST_FUNCTIONS)
def test_file_digests_are_taken_over_lf_normalised_bytes(
    module_name: str, function_name: str, tmp_path: Path
) -> None:
    """Counterexample: manifests hashed over CRLF bytes (C012-C019, C041, C042) never match a checkout."""
    digest = getattr(importlib.import_module(module_name), function_name)
    lf_bytes = b'{\n  "case_id": "h01",\n  "value": 3\n}\n'
    crlf_bytes = lf_bytes.replace(b"\n", b"\r\n")
    lf_file, crlf_file = tmp_path / "lf.json", tmp_path / "crlf.json"
    lf_file.write_bytes(lf_bytes)
    crlf_file.write_bytes(crlf_bytes)
    git_blob_content_digest = hashlib.sha256(lf_bytes).hexdigest()
    assert digest(crlf_file) == digest(lf_file) == git_blob_content_digest
    assert hashlib.sha256(crlf_bytes).hexdigest() != git_blob_content_digest, (
        "raw-byte hashing differs"
    )


def test_a_lone_carriage_return_is_not_normalised(tmp_path: Path) -> None:
    """Git text normalisation rewrites CRLF only; a bare CR is content and must change the digest."""
    digest = importlib.import_module(f"{C011}.governance.commit_reveal_runner").sha256_of_file
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_bytes(b"x\ry\n")
    b.write_bytes(b"x\ny\n")
    assert digest(a) != digest(b)


# ----------------------------------------------------- empty suites and labels


def test_family_a_gate_refuses_an_empty_suite_and_labels_a_consistent_one() -> None:
    gate_mod = importlib.import_module(f"{C011}.governance.adversary_gate")
    gate = gate_mod.AdversaryGate()
    assert gate.determine_terminal_verdict([]) == INCONSISTENT
    assert gate.determine_terminal_verdict([{"verdict": "PASS", "agreement": True}]) == CONSISTENT
    assert (
        gate.determine_terminal_verdict([{"verdict": "PASS", "agreement": "yes"}]) == INCONSISTENT
    )


def test_count_gates_refuse_zero_of_zero_mutations() -> None:
    """Counterexample (C054): the gate passed with 0 of 0 mutations killed."""
    family_b = importlib.import_module(
        f"{C015}.governance.adversary_gate"
    ).evaluate_adversary_terminal_gate
    family_c = importlib.import_module(f"{C018}.governance.adversary_gate").evaluate_adversary_gate
    full = {"total_cases": 5, "passed_cases": 5, "mutations_total": 4, "mutations_killed": 4}
    assert family_b(full, True)[0] == CONSISTENT
    assert family_b({**full, "mutations_total": 0, "mutations_killed": 0}, True)[0] == INCONSISTENT
    assert family_b({**full, "total_cases": 0, "passed_cases": 0}, True)[0] == INCONSISTENT
    assert (
        family_b({"total_cases": 5, "passed_cases": 5, "mutation_kill_rate": 1.0}, True)[0]
        == INCONSISTENT
    )
    assert family_c({**full, "budget_passed": True})["verdict"] == CONSISTENT
    assert (
        family_c({**full, "mutations_total": 0, "mutations_killed": 0, "budget_passed": True})[
            "verdict"
        ]
        == INCONSISTENT
    )
    c032 = importlib.import_module(f"{C032}.governance.adversary_gate").determine_terminal_verdict
    assert c032(0, 0, 0) == INCONSISTENT
    assert c032(3, 3, 3) == CONSISTENT


@pytest.mark.parametrize("key", sorted(FLAT))
def test_flat_scripts_label_from_exact_counts(key: str) -> None:
    label_run = importlib.import_module(FLAT[key]).label_run
    assert label_run(64, 64, 48, 48, 0) == CONSISTENT
    assert label_run(64, 64, 0, 0, 0) == INCONSISTENT, "0 of 0 mutations is an empty suite"
    assert label_run(0, 0, 48, 48, 0) == INCONSISTENT, "0 of 0 cases is an empty suite"
    assert label_run(64, 64, 48, 48, 1) == INCONSISTENT, "a checker crash is not a rejection"
    with pytest.raises(TypeError):
        label_run(64, 64, 48, True, 0)


# ------------------------------------------------------------- exact defects


def test_family_a_defect_values_are_exact_without_tolerance() -> None:
    """Counterexample (c021): phi1 = 1e-6 passed under a float tolerance."""
    gate = importlib.import_module(f"{C011}.governance.adversary_gate").AdversaryGate()
    cases = [{"verdict": "PASS", "agreement": True}]
    assert gate.determine_terminal_verdict(cases, phi1=Fraction(1, 10**9)) == INCONSISTENT
    assert gate.determine_terminal_verdict(cases, phi1=0, gamma2=Fraction(0)) == CONSISTENT
    for bad in (0.0, 1e-9, True):
        with pytest.raises(TypeError):
            gate.determine_terminal_verdict(cases, phi1=bad)
    with pytest.raises(TypeError):
        gate.determine_terminal_verdict(cases, defect_count=0.0)


# ------------------------------------------------ run folders: nothing deleted


def test_failed_bundle_write_leaves_a_failure_receipt_and_deletes_nothing(tmp_path: Path) -> None:
    """Counterexample (c021 adversary_gate.py:274-276): a failed write rmtree'd the staged folder."""
    gate_mod = importlib.import_module(f"{C011}.governance.adversary_gate")
    target = tmp_path / "_intelligence" / "_adversary" / "runs" / "failing_run"
    with pytest.raises(TypeError):
        gate_mod.persist_single_bundle(
            target_dir=target,
            novella_md="# report\n",
            dda_steps=[],
            summary_data={"not_json": {1, 2}},
            receipt_data={},
        )
    assert sorted(p.name for p in target.iterdir()) == [
        "dda_actions.jsonl",
        "failure_receipt.json",
        "novella.md",
    ]
    failure = json.loads((target / "failure_receipt.json").read_text(encoding="utf-8"))
    assert failure["status"] == "RUN_FAILED" and failure["error_type"] == "TypeError"
    with pytest.raises(gate_mod.RunFolderExistsError):
        gate_mod.persist_single_bundle(target, "# again\n", [], {}, {})


def test_persisted_bundle_carries_the_label_scope_and_measured_values(tmp_path: Path) -> None:
    gate = importlib.import_module(f"{C011}.governance.adversary_gate").AdversaryGate(
        base_repo_root=tmp_path
    )
    verdict, adversary_dir, sg_dir, _ = gate.evaluate_and_persist(
        task_key="t1",
        run_id="r1",
        case_results=[
            {"verdict": "PASS", "agreement": True},
            {"verdict": "FAIL", "agreement": True},
        ],
        claim_hygiene={
            "supports": "s",
            "does_not_support": "d",
            "narrowest_defensible_claim": "n",
            "next_test_needed": "x",
        },
        defect_count=1,
    )
    assert verdict == INCONSISTENT
    assert adversary_dir == tmp_path / "_intelligence" / "_adversary" / "runs" / "t1"
    receipt = json.loads((adversary_dir / "receipt.json").read_text(encoding="utf-8"))
    assert (
        receipt["verdict"] == INCONSISTENT
        and receipt["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"
    )
    assert (receipt["case_count"], receipt["passed_count"], receipt["phi1"]) == (2, 1, None)
    report = (adversary_dir / "novella.md").read_text(encoding="utf-8")
    for templated in ("100% concordance", "$0.05", "70B", "cost = 26", "Act IV"):
        assert templated not in report
    steps = [
        json.loads(line)
        for line in (adversary_dir / "dda_actions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert steps[-1]["payload"]["label"] == INCONSISTENT
    assert all("repaired" not in json.dumps(step) for step in steps)
    assert (sg_dir / "receipt.json").is_file()


# ------------------------------------------- Phase 3 verifies every manifest entry


@pytest.fixture()
def c011_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A temporary C011 package with an LF manifest rebuilt over its current files and stubbed scoring."""
    runner_mod = importlib.import_module(f"{C011}.governance.commit_reveal_runner")
    source = CHALLENGES / "b_cohomology" / "c011_cycle_rank_ladder_coboundary_repair"
    root = tmp_path / "c011"
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(source / "judge_packet", root / "judge_packet", ignore=ignore)
    shutil.copytree(source / "reference_solver", root / "reference_solver", ignore=ignore)
    manifest_file = root / "judge_packet" / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        entry["sha256"] = runner_mod.sha256_of_file(root / "judge_packet" / entry["path"])
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(runner_mod, "solve", lambda case: {"status": "SOLVED"})
    monkeypatch.setattr(
        runner_mod, "evaluate_dual", lambda case, res: {"verdict": "PASS", "agreement": True}
    )
    runner = runner_mod.CommitRevealRunner(challenge_root=root, base_repo_root=tmp_path / "store")
    runner.run_phase1_commit_judge()
    runner.run_phase2_freeze_solver()
    return runner_mod, runner, root


def test_phase3_labels_a_verified_copy_consistent(c011_copy) -> None:
    _runner_mod, runner, _root = c011_copy
    receipt = runner.run_phase3_reveal_and_score(task_key="ok_task", run_id="ok_run")
    assert receipt["verdict"] == CONSISTENT
    assert receipt["judge_manifest_entries_verified"] >= receipt["case_count"] > 0
    assert receipt["digest_normalization"] == "CRLF_TO_LF"


def test_phase3_refuses_an_edited_case_file_even_when_the_manifest_file_is_unchanged(
    c011_copy,
) -> None:
    """Counterexample: the old Phase 3 compared only the manifest file digest, so an edited case passed."""
    runner_mod, runner, root = c011_copy
    case_file = sorted((root / "judge_packet" / "cases" / "base").glob("*.json"))[0]
    case_file.write_text(
        case_file.read_text(encoding="utf-8") + " ", encoding="utf-8", newline="\n"
    )
    with pytest.raises(runner_mod.ManifestCustodyError) as caught:
        runner.run_phase3_reveal_and_score(task_key="tamper_task", run_id="tamper_run")
    assert caught.value.code == "MANIFEST_ENTRY_MISMATCH"
    failure = json.loads(runner.failure_file.read_text(encoding="utf-8"))
    assert failure["error_code"] == "MANIFEST_ENTRY_MISMATCH"
    assert not runner.phase3_file.exists(), "no scoring receipt may be written for a refused run"


def test_phase3_refuses_a_case_file_the_manifest_does_not_list(c011_copy) -> None:
    runner_mod, runner, root = c011_copy
    (root / "judge_packet" / "cases" / "base" / "zz_unlisted.json").write_text(
        '{"case_id": "x"}\n', encoding="utf-8"
    )
    with pytest.raises(runner_mod.ManifestCustodyError) as caught:
        runner.run_phase3_reveal_and_score(task_key="unlisted_task", run_id="unlisted_run")
    assert caught.value.code == "CASE_FILE_NOT_IN_MANIFEST"


# ------------------------------------------------------------- flat scripts


def _flat_copy(tmp_path: Path, *, mutations: int) -> ModuleType:
    """Copy commit_reveal_c052.py with one case and ``mutations`` mutation files into a temp package."""
    pkg = tmp_path / "c052_copy"
    (pkg / "reference_solver").mkdir(parents=True)
    (pkg / "judge_packet" / "cases").mkdir(parents=True)
    (pkg / "judge_packet" / "hostile_mutations").mkdir(parents=True)
    for solver_file in sorted((C052_DIR / "reference_solver").glob("*.py")):
        shutil.copy2(solver_file, pkg / "reference_solver" / solver_file.name)
    for checker in sorted((C052_DIR / "judge_packet").glob("*.py")):
        shutil.copy2(checker, pkg / "judge_packet" / checker.name)
    first_case = sorted((C052_DIR / "judge_packet" / "cases").glob("*.json"))[0]
    shutil.copy2(first_case, pkg / "judge_packet" / "cases" / first_case.name)
    for mutation in sorted((C052_DIR / "judge_packet" / "hostile_mutations").glob("*.json"))[
        :mutations
    ]:
        shutil.copy2(mutation, pkg / "judge_packet" / "hostile_mutations" / mutation.name)
    shutil.copy2(C052_DIR / "commit_reveal_c052.py", pkg / "commit_reveal_c052.py")
    return _load_from_file(
        pkg / "commit_reveal_c052.py", f"_harness_copy_c052_{mutations}_{tmp_path.name}"
    )


def test_flat_script_with_no_mutations_refuses_and_leaves_a_failure_receipt(tmp_path: Path) -> None:
    """Counterexample (C054): an empty mutation suite passed as 0 of 0; the old script also left empty folders."""
    module = _flat_copy(tmp_path, mutations=0)
    store = tmp_path / "store"
    with pytest.raises(module.ReferenceRunError) as caught:
        module.run_gate(intelligence_repo_root=store)
    assert caught.value.code == "EMPTY_MUTATION_SUITE"
    run_dirs = [
        p
        for p in (store / "_intelligence" / "_adversary" / "runs").iterdir()
        if not p.name.startswith(".")
    ]
    assert len(run_dirs) == 1
    assert sorted(p.name for p in run_dirs[0].iterdir()) == ["failure_receipt.json"]


def test_flat_script_writes_under_the_resolved_intelligence_root(
    tmp_path: Path, isolated_intelligence_root: Path
) -> None:
    module = _flat_copy(tmp_path, mutations=1)
    module.run_gate()
    runs = isolated_intelligence_root / "_intelligence" / "_adversary" / "runs"
    (run_dir,) = [p for p in runs.iterdir() if not p.name.startswith(".")]
    receipt = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["pre_run_commitment"] is False
    assert receipt["commitment_timing"] == "COMPUTED_AT_REVEAL"
    assert receipt["verdict"] in (CONSISTENT, INCONSISTENT)
    assert set(receipt["judge_files_sha256"]) >= {
        "judge_packet/hostile_mutations/" + p.name
        for p in (tmp_path / "c052_copy" / "judge_packet" / "hostile_mutations").iterdir()
    }
    assert sorted(p.name for p in run_dir.iterdir()) == [
        "dda_actions.jsonl",
        "novella.md",
        "receipt.json",
        "summary.json",
    ]
