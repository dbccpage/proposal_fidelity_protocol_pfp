"""Current pilot imports and read-only participant entrypoints after relocation."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHALLENGES = (
    "c051_exact_lp_solver_with_duals",
    "c052_maxflow_mincut_certificates",
    "c053_bareiss_fraction_free_matrix_inversion",
    "c054_exact_linear_systems",
    "c055_assignment_with_potentials",
)
PILOTS = ROOT / "adversary/tests/pilots"


def outside(tmp_path, arguments, *, module=False):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)
    if module:
        env["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [sys.executable, "-B", *arguments],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )


def test_direct_participant_help_bootstraps_current_owner(tmp_path):
    path = PILOTS / CHALLENGES[1] / "participant_packet/runner.py"
    result = outside(tmp_path, [str(path), "--help"])
    assert result.returncode == 0, result.stderr
    assert "--all-examples" in result.stdout


@pytest.mark.parametrize("folder", CHALLENGES)
def test_canonical_active_modules_load_without_retired_owners(tmp_path, folder):
    root = PILOTS / folder
    paths = [
        root / ("commit_reveal_" + folder[:4] + ".py"),
        root / "participant_packet/runner.py",
        root / "judge_packet/generate_mutations.py",
    ]
    paths.append(
        root
        / (
            "participant_packet/generate_examples.py"
            if folder[:4] in ("c051", "c052", "c053")
            else "generate_examples.py"
        )
    )
    matrix = root / ("run_" + folder[:4] + "_matrix.py")
    if matrix.is_file():
        paths.append(matrix)
    names = [path.relative_to(ROOT).with_suffix("").as_posix().replace("/", ".") for path in paths]
    driver = "import importlib,json,sys; [importlib.import_module(name) for name in json.loads(sys.argv[1])]"
    result = outside(tmp_path, ["-c", driver, json.dumps(names)], module=True)
    assert result.returncode == 0, result.stderr


def test_commit_script_bootstrap_loads_without_running_gate(tmp_path):
    folder = CHALLENGES[1]
    path = PILOTS / folder / ("commit_reveal_" + folder[:4] + ".py")
    driver = "import runpy,sys; runpy.run_path(sys.argv[1],run_name='bootstrap_probe')"
    result = outside(tmp_path, ["-c", driver, str(path)])
    assert result.returncode == 0, result.stderr
    assert not list(tmp_path.iterdir())


def test_direct_participant_examples_keep_original_solver_and_checkers(tmp_path):
    folder = CHALLENGES[3]
    root = PILOTS / folder
    arguments = [str(root / "participant_packet/runner.py")]
    examples = sorted((root / "participant_packet/examples").glob("*.json"))
    assert examples
    result = outside(tmp_path, arguments)
    assert result.returncode == 0, result.stderr + result.stdout
    assert f"{len(examples)}/{len(examples)}" in result.stdout
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("module", [False, True])
def test_matrix_help_keeps_both_entry_styles_without_dispatch(tmp_path, module):
    folder = CHALLENGES[2]
    name = "run_" + folder[:4] + "_matrix"
    arguments = (
        ["-m", "adversary.tests.pilots." + folder + "." + name]
        if module
        else [str(PILOTS / folder / (name + ".py"))]
    )
    result = outside(tmp_path, [*arguments, "--help"], module=module)
    assert result.returncode == 0, result.stderr
    assert "--output-dir" in result.stdout
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("challenge_id", ("C051", "C052", "C053", "C054", "C055", "C059"))
def test_catalog_rows_reach_current_pilots_without_rewriting_identity(challenge_id):
    from pfp.infrastructure.challenge_live import choose_case
    from adversary.infrastructure import challenge_play
    from adversary.tests.pilots.challenge_suite import catalog

    row = choose_case(challenge_id, "development", 0)
    before = dict(row)
    state = challenge_play.start(row)
    assert row == before
    assert row["source"].startswith("education/pilots/demo_004/")
    assert catalog.load_case(row)
    assert any(p.startswith("adversary/tests/pilots/") for p in state["sources"])
    assert not any("/tests/" in p.split("/pilots/", 1)[-1] for p in state["sources"])
    assert challenge_play.report(state)["pfp_turn"]


def test_relocated_case_still_requires_original_bytes(monkeypatch, tmp_path):
    from pfp.infrastructure.challenge_live import choose_case
    from adversary.tests.pilots.challenge_suite import catalog

    row = choose_case("C054", "development", 0)
    destination = tmp_path / "adversary/tests/pilots" / row["source"].split("f_program_synthesis/", 1)[1]
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b'{"altered":true}')
    monkeypatch.setattr(catalog, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="CASE_SOURCE_DRIFT"):
        catalog.load_case(row)
