"""Current discovery, scoped selection and the retained audit boundaries."""

import json
from argparse import Namespace
from pathlib import Path

import pytest

from pfp.tests.judge_audit import fake_packages as fp
from adversary.tests.pilots.judge_packet_audit import audit, layout, special_checks


def test_real_c014_descriptor_uses_current_owner_and_original_checker_contract():
    root = Path(__file__).resolve().parents[3]
    packages = layout.discover_packages(root)
    package = next(p for p in packages if layout.package_id(p) == "C014")
    descriptor = layout.build_descriptor(root, package)
    assert descriptor["rel_path"].startswith("pfp/tests/demo_004/")
    assert descriptor["import_prefix"] == (
        "pfp.tests.demo_004.b_cohomology.c014_discrete_hodge_decomposition."
    )
    assert descriptor["gate"] == dict(kind="function",
        module="judge_packet.checkers.dual_evaluator", function="evaluate_dual")
    assert len(descriptor["checkers"]) == 2
    assert descriptor["solver"] == dict(module="reference_solver.solver", function="solve")
    assert descriptor["cases"]


def test_tree_checksum_detects_change_under_current_challenge_owner(tmp_path):
    case = tmp_path / "pfp/tests/demo_004/z_fake/c999/judge_packet/cases/a.json"
    case.parent.mkdir(parents=True)
    case.write_bytes(b'{"n":1}')
    before = audit._tree_state(tmp_path)
    case.write_bytes(b'{"n":2}')
    assert audit._tree_state(tmp_path) != before


@pytest.mark.parametrize("selected", ([], ["UNKNOWN"], ["C901", "UNKNOWN"]))
def test_empty_or_unknown_explicit_selection_refuses_before_output(tmp_path, selected):
    root = fp.repo(tmp_path / "repo")
    fp.light_package(root, "c901_sound", fp.SOUND_EXACT, fp.INDEPENDENT_SOUND)
    out = tmp_path / "out"
    with pytest.raises(SystemExit) as refused:
        audit.run(["--repo-root", str(root), "--out", str(out), "--work-dir",
                   str(tmp_path / "work"), "--skip-execution", "--packages", *selected])
    assert refused.value.code == 2
    assert not out.exists()


def test_no_discovered_or_special_packages_cannot_succeed(tmp_path):
    root = fp.repo(tmp_path / "repo")
    with pytest.raises(SystemExit) as refused:
        audit.run(["--repo-root", str(root), "--out", str(tmp_path / "out"),
                   "--work-dir", str(tmp_path / "work"), "--skip-execution"])
    assert refused.value.code == 2
    assert not (tmp_path / "out").exists()


def test_selection_does_not_run_other_package_special_checks(tmp_path, monkeypatch):
    root = fp.repo(tmp_path / "repo")
    source = root / fp.CHALLENGES
    (source / "a_mechanism/c001_attention_distractor_mask").mkdir(parents=True)
    (source / "a_mechanism/c001_attention_distractor_mask/pipeline.json").write_text("{}")
    (source / "a_mechanism/c005_hosted_decode_controls").mkdir()
    (source / "d_physics_mtheory/c032_trace").mkdir(parents=True)
    task = source / "d_physics_mtheory/c036_values/participant_packet/TASK.md"
    task.parent.mkdir(parents=True)
    task.write_text("Unselected reference-value task")
    def forbidden(*args, **kwargs):
        pytest.fail("An unselected package check ran")
    monkeypatch.setattr(special_checks, "c005_constant_verdict", forbidden)
    monkeypatch.setattr(special_checks, "c032_trace_identities", forbidden)
    monkeypatch.setattr(special_checks.reference_values, "compare_gv_table", forbidden)
    options = Namespace(packages=["C901"], skip_execution=False)
    assert special_checks.special_cases(root, options) == {"theme_answer_files": {}}
    assert special_checks.reference_value_checks(root, options) == {}


def test_existing_special_only_c001_selection_is_preserved_and_recorded(tmp_path):
    root = fp.repo(tmp_path / "repo")
    source = root / fp.CHALLENGES / "a_mechanism/c001_attention_distractor_mask/pipeline.json"
    source.parent.mkdir(parents=True)
    source.write_text("{}")
    out = tmp_path / "out"
    assert audit.run(["--repo-root", str(root), "--out", str(out), "--work-dir",
                      str(tmp_path / "work"), "--packages", "C001", "--skip-execution"]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["special_cases"]["C001"]["path"] == source.relative_to(root).as_posix()
    info = json.loads((out / "run_info.json").read_text())
    assert info["packages"] == ["C001"]
    assert "adversary.tests.pilots.judge_packet_audit.audit" in info["command"]
    assert "projects" not in info["command"]
    assert info["audited_tree_state_unchanged"]
