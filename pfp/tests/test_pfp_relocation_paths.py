"""Relocation keeps package resources and educational corpus owners distinct."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

APPLICATION = Path(__file__).resolve().parents[1]
NAMESPACE = APPLICATION.name
REPOSITORY = APPLICATION.parent
EDUCATION = REPOSITORY / "education"


def module(relative):
    return importlib.import_module(f"{NAMESPACE}.{relative}")


def test_pilot_data_uses_the_adversary_test_owner():
    pilot = module("infrastructure.pilot_runner")
    assert pilot.SEED_CATALOG == REPOSITORY / "adversary/tests/pilots/matrix/seeds.yaml"
    assert pilot.CANONICAL_PROMPT_TEMPLATE == APPLICATION / "infrastructure/yaml/prompts/templates/template_single_slot.yaml"


def test_missing_external_corpus_does_not_become_a_package_resource(tmp_path):
    pilot = module("infrastructure.pilot_runner")
    with pytest.raises(FileNotFoundError, match="PILOT_SEED_CORPUS_UNAVAILABLE"):
        pilot.load_seed_catalog(tmp_path / "seeds.yaml")


def test_storage_defaults_to_the_moved_package_assets():
    storage = module("infrastructure.storage").PfpFileSystemStorageAdapter()
    assert storage.root == APPLICATION / "infrastructure/yaml"
    assert storage.load_stage_file(1).stage == 1


@pytest.mark.parametrize("location", ["infrastructure.type_register"])
def test_register_keeps_documentation_and_executable_roots_distinct(location):
    register = module(location)
    documents = EDUCATION / "documentation/004_oepfp"
    assert register.code_dir(documents) == APPLICATION
    assert register.resolve(documents, "infrastructure/type_register.py") == APPLICATION / "infrastructure/type_register.py"
    assert register.resolve(documents, "type_register/type_register.yaml") == APPLICATION / "type_register/type_register.yaml"
    assert APPLICATION / "infrastructure/yaml/prompts/templates/template_single_slot.yaml" in register.glob(
        documents, "infrastructure/yaml/prompts/templates/template_single_slot.yaml"
    )


@pytest.mark.parametrize("location", ["infrastructure.type_register"])
def test_register_does_not_mix_an_isolated_scan_with_the_application(location, tmp_path):
    register = module(location)
    assert register.code_dir(tmp_path) == tmp_path.resolve()


@pytest.mark.parametrize("repository_present", [False, True])
def test_historical_demo_refuses_missing_source_context_or_bytes(tmp_path, monkeypatch, repository_present):
    runner = module("infrastructure.pilot_runners.problem_declaration_suite")
    spec = module("domain.stages.demos").DemoSpec(id="DEMO_002", title="historical source", seed="unused")
    if repository_present:
        (tmp_path / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    source = tmp_path / "application/infrastructure/demo_runners/runner_002.py"
    monkeypatch.setattr(runner, "__file__", str(source))
    # A basetemp inside the checkout must not supply the real repository marker
    # to this deliberately isolated source-context fixture.
    real_exists = Path.exists
    monkeypatch.setattr(
        Path, "exists",
        lambda path: (repository_present and path == tmp_path / ".git")
        if path.name == ".git" else real_exists(path),
    )
    result = runner.run_demo_002(spec)
    expected = "HISTORICAL_SOURCE_BYTES_UNAVAILABLE" if repository_present else "HISTORICAL_SOURCE_CONTEXT_UNAVAILABLE"
    assert not result.all_passed
    assert result.terminal_status == "Refused"
    assert any(check.error_message and expected in check.error_message for check in result.checks)


def test_normal_forms_repository_discovery_accepts_git_worktree_files(tmp_path, monkeypatch):
    parser = module("infrastructure.normal_forms.nf_contract_parser")
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    source = checkout / "application/infrastructure/yaml/normal_forms/nf_contract_parser.py"
    monkeypatch.setattr(parser, "__file__", str(source))
    assert parser._repo_root() == checkout


def test_type_test_helpers_resolve_the_new_package_without_a_legacy_pfp_tree():
    source = APPLICATION / "tests/types/pfp_types_test_support.py"
    spec = importlib.util.spec_from_file_location("pfp_relocation_test_support", source)
    assert spec is not None and spec.loader is not None
    helper = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = helper
    try:
        spec.loader.exec_module(helper)
        loaded = helper.load_module("infrastructure/type_register.py", "pfp_relocation_register")
        assert Path(loaded.__file__) == APPLICATION / "infrastructure/type_register.py"
        assert "response_schema" in helper.load_yaml("prompts/templates/template_single_slot.yaml")
    finally:
        sys.modules.pop(spec.name, None)
        sys.modules.pop("pfp_relocation_register", None)


def test_replay_paths_find_adversary_pilots_from_the_combined_application():
    paths = importlib.import_module("adversary.tests.pilots.replay_runners._paths")
    assert paths.pilots_root(Path(__file__)) == REPOSITORY / "adversary/tests/pilots"
    assert paths.repository_root(Path(__file__)) == REPOSITORY


def test_replay_paths_accept_a_linked_worktree_file(tmp_path):
    paths = importlib.import_module("adversary.tests.pilots.replay_runners._paths")
    checkout = tmp_path / "checkout"
    estate = checkout / "adversary/tests/pilots"
    (estate / "matrix").mkdir(parents=True)
    (estate / "pilot_0000006").mkdir()
    (checkout / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    source = checkout / "application/tests/test_pilot.py"
    assert paths.pilots_root(source) == estate
    assert paths.repository_root(source) == checkout
