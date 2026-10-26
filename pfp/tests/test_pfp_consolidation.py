"""Integration checks for the final PFP owner, assets and callable entry points.

These checks complement seed/math/provider suites; they do not certify those
behaviors or execute provider calls.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from importlib import resources
from pathlib import Path

import pytest
import yaml

APPLICATION = Path(__file__).resolve().parents[1]
NAMESPACE = APPLICATION.name
REPOSITORY = next(p for p in APPLICATION.parents if (p / ".git").exists())


def test_one_final_application_owner_without_legacy_shadows():
    assert NAMESPACE == "omega_engine_pfp"
    old_application = "omega_engine_" + "symbol_game"
    assert not (REPOSITORY / old_application).exists()
    assert not list((REPOSITORY / "omega_engine_education" / "pfp").rglob("*.py"))
    pilot_tasks = REPOSITORY / "omega_engine_woland/tests/pilots/challenge_suite"
    assert not (REPOSITORY / "omega_engine_education/pilots").exists()
    assert all(not (pilot_tasks / name).exists()
               for name in ("execution.py", "live.py", "woland.py", "mechanism.py"))
    assert all((pilot_tasks / name).is_file()
               for name in ("catalog.py", "c001.py", "replay_snapshots.py"))


def test_resource_tree_contains_data_and_one_current_type_register():
    resources_root = APPLICATION / "infrastructure/yaml"
    assert not list(resources_root.rglob("*.py")), "Executable models belong outside resource data"
    assert not (resources_root / "type_register").exists(), "Retired path aliases must not shadow the current inventory"
    assert (APPLICATION / "type_register/type_register.yaml").is_file()


@pytest.mark.parametrize(
    "relative_module,public_name",
    [
        ("domain.stages.demos", "DemoSpec"),
        ("domain.contracts.pfp_runtime", "PfpPromptTemplate"),
        ("infrastructure.pilot_runners.mssn_checks", "evaluate_demo_n02"),
        ("infrastructure.pilot_runner", "load_seed_catalog"),
        ("infrastructure.challenge_execution", "isolated"),
        ("infrastructure.challenge_live", "choose_case"),
        ("entrypoints.cli.pfp", "main"),
        ("entrypoints.cli.pfp_normal_forms", "run_normal_forms_cli"),
        ("entrypoints.cli.pfp_view", "PfpConsoleView"),
        ("entrypoints.cli.symbol_game", "main"),
        ("infrastructure.tower_evidence.level_engine.resolver", "LevelEngineEvidenceResolver"),
    ],
)
def test_merged_public_modules_resolve_inside_the_active_owner(relative_module, public_name):
    name = f"{NAMESPACE}.{relative_module}"
    module = importlib.import_module(name)
    assert Path(module.__file__).resolve().is_relative_to(APPLICATION)
    assert callable(getattr(module, public_name))


@pytest.mark.parametrize(
    "relative",
    [
        "infrastructure/yaml/prompts/templates/template_single_slot.yaml",
        "infrastructure/yaml/taxonomy/task_families.yaml",
        "infrastructure/yaml/taxonomy/execution_modes.yaml",
        "infrastructure/yaml/stages/stage_models.yaml",
        "infrastructure/yaml/stages/stage_1_admit.yaml",
        "infrastructure/yaml/stages/stage_11_evidence_plan.yaml",
        "infrastructure/yaml/modes/modes_manifest.yaml",
        "infrastructure/yaml/pilots/pilot_spec_v1.schema.yaml",
    ],
)
def test_merged_yaml_is_available_through_package_resources(relative):
    raw = resources.files(NAMESPACE).joinpath(*relative.split("/")).read_bytes()
    assert isinstance(yaml.safe_load(raw), dict)


def test_prompt_template_can_construct_the_existing_runtime_contract():
    raw = resources.files(NAMESPACE).joinpath(
        "infrastructure", "yaml", "prompts", "templates", "template_single_slot.yaml"
    ).read_bytes()
    data = yaml.safe_load(raw)
    contract = importlib.import_module(f"{NAMESPACE}.domain.contracts.pfp_runtime")
    schema = data["response_schema"]
    if isinstance(schema, str):
        schema = yaml.safe_load(schema)
    template = contract.PfpPromptTemplate(
        system=data["system_prompt"], user=data["user_prompt"], response_schema=schema
    )
    assert "[USER PROMPT]" in template.user
    assert isinstance(template.response_schema, dict)


@pytest.mark.parametrize("entrypoint", ["pfp", "pfp_normal_forms", "symbol_game"])
def test_cli_help_runs_through_the_final_namespace(entrypoint):
    process = subprocess.run(
        [sys.executable, "-B", "-m", f"{NAMESPACE}.entrypoints.cli.{entrypoint}", "--help"],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    assert "usage:" in process.stdout.lower()


def test_packaging_routes_and_resource_declarations_name_the_final_owner():
    # Source declarations are checked here; installed-wheel smoke checks remain
    # necessary because a declaration alone cannot establish wheel contents.
    try:
        import tomllib
    except ModuleNotFoundError:
        pytest.skip("pyproject declaration parsing requires Python 3.11+")
    project = tomllib.loads((REPOSITORY / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = project["project"]["scripts"]
    assert scripts["pfp"] == f"{NAMESPACE}.entrypoints.cli.pfp:main"
    assert scripts["symbol-game"] == f"{NAMESPACE}.entrypoints.cli.symbol_game:main"
    assert scripts["level-engine"] == f"{NAMESPACE}.entrypoints.cli.level_engine_commands:main"
    setuptools = project["tool"]["setuptools"]
    assert f"{NAMESPACE}*" in setuptools["packages"]["find"]["include"]
    declarations = setuptools["package-data"]
    prompt = APPLICATION / "infrastructure/yaml/prompts/templates/template_single_slot.yaml"
    covered = False
    for package, patterns in declarations.items():
        if package == NAMESPACE or package.startswith(NAMESPACE + "."):
            directory = REPOSITORY.joinpath(*package.split("."))
            covered |= any(prompt in directory.glob(pattern) for pattern in patterns)
    assert covered, "PFP_PROMPT_MISSING_FROM_PACKAGE_DATA_DECLARATIONS"
