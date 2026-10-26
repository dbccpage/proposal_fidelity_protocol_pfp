"""Current resources work without Git; historical campaigns require a checkout."""

from pathlib import Path

import pytest

from omega_engine_pfp.infrastructure import numbered_prompts as prompts
from omega_engine_pfp.infrastructure.adapters import pfp_evidence
from omega_engine_woland.tests.pilots.relational_spacetime import (
    baseline,
    compact_trials,
    parameter_trials,
    tasks,
    typed_signals,
)


def test_distribution_resource_root_is_independent_of_working_directory(tmp_path, monkeypatch):
    module = tmp_path / "installed/omega_engine_pfp/infrastructure/po035/cases.py"
    pilot = tmp_path / "installed/omega_engine_woland/tests/pilots/relational_spacetime/tasks.py"
    module.parent.mkdir(parents=True)
    pilot.parent.mkdir(parents=True)
    module.touch()
    pilot.touch()
    monkeypatch.chdir(tmp_path)
    assert pfp_evidence.resource_root(module) == tmp_path / "installed"
    assert pfp_evidence.resource_root(pilot) == tmp_path / "installed"
    assert pfp_evidence.repository_root(pilot) == tmp_path / "installed"
    with pytest.raises(ValueError, match="REPOSITORY_CONTEXT_REQUIRED"):
        pfp_evidence.require_checkout(tmp_path / "installed")


def test_current_numbered_renderer_uses_its_canonical_resource_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert prompts.ROOT == pfp_evidence.resource_root(Path(prompts.__file__))
    prompt = prompts.build_prompt("pilot_0000201", 1)
    assert prompt["construction_path"] == "omega_engine_pfp/infrastructure/numbered_prompts.py"
    assert prompt["provider_dispatches"] == 0


def test_missing_current_resource_refuses_instead_of_using_historical_bytes(monkeypatch):
    original = Path.read_bytes
    target = f"PFP-T0001-v{prompts.VERSION}.yaml"

    def missing(path):
        if path.name == target:
            raise FileNotFoundError(path)
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", missing)
    with pytest.raises(ValueError, match="VERSIONED_PROMPT_RESOURCE_UNAVAILABLE"):
        prompts.build_prompt("pilot_0000199", 1)


def test_distribution_probe_checks_public_task_and_current_ide_commands(tmp_path, monkeypatch):
    import socket
    import urllib.request

    from omega_engine_pfp.tests import installed_package_probe

    def forbidden(*args, **kwargs):
        pytest.fail("Offline installed command probe attempted network access.")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    controls = installed_package_probe.public_task_cli_probe()
    assert (
        "public PFP task CLI: synthetic binding controls, semantic acceptance not claimed"
        in controls
    )
    assert "public command malformed/wrong-binding refusals retain actual raw bytes" in controls
    assert not list(tmp_path.iterdir())


def test_current_ide_probe_requires_explicit_native_before_temp_io(tmp_path, monkeypatch):
    from omega_engine_pfp.tests import installed_package_probe

    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="^INSTALLED_NATIVE_HOST_REQUIRED$"):
        installed_package_probe.current_ide_cli_probe()
    assert not list(tmp_path.iterdir())


def test_distribution_probe_requires_current_challenge_resources_and_source_bindings(
    tmp_path, monkeypatch
):
    import socket

    from omega_engine_pfp.tests import installed_package_probe
    from omega_engine_woland.tests.pilots.challenge_suite.catalog import ROOT

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *_a, **_k: pytest.fail("challenge start attempted network"),
    )
    controls = installed_package_probe.installed_challenge_probe(ROOT)
    assert controls == [
        "ten installed historical-v3 challenge starts: full-Retinue intake/source bindings, zero model calls"
    ]
    assert not list(tmp_path.iterdir())


def test_distribution_probe_exercises_one_original_isolated_host_fixture():
    from omega_engine_pfp.tests import installed_package_probe
    from omega_engine_woland.tests.pilots.challenge_suite.catalog import ROOT

    assert installed_package_probe.installed_host_fixture_probe(ROOT) == [
        "installed C054 host fixture: isolated original dual-judge verification and empty-witness refusal; no model evidence"
    ]


def test_public_pfp_runner_preserves_canonical_identity_and_refusal(tmp_path, monkeypatch):
    from omega_engine_pfp.tests.installed_package_probe import public_pfp_api_probe

    monkeypatch.chdir(tmp_path)
    assert public_pfp_api_probe() == [
        "public PFP runner identity and unknown-demo refusal; no model or original-protocol evidence"
    ]
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "operation",
    [
        baseline.sources,
        baseline.prepare,
        baseline.replay,
        lambda: parameter_trials.run("scratchpad", ["pilot_0000199"]),
        lambda: parameter_trials.replay("scratchpad", ["pilot_0000199"]),
        compact_trials.prepare,
        lambda: compact_trials.run(["pilot_0000199"]),
        lambda: compact_trials.replay(["pilot_0000199"]),
        lambda: typed_signals.run("pilot_0000199"),
        typed_signals.replay,
    ],
)
def test_checkout_only_operations_refuse_before_io_or_network(tmp_path, monkeypatch, operation):
    monkeypatch.setattr(tasks, "ROOT", tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("A checkout-only operation attempted network or evidence writes.")

    for module in (baseline, parameter_trials, compact_trials, typed_signals):
        monkeypatch.setattr(module, "fetch_openrouter_catalog", forbidden)
        monkeypatch.setattr(module, "write_once", forbidden)
    with pytest.raises(ValueError, match="REPOSITORY_CONTEXT_REQUIRED"):
        operation()
    assert not list(tmp_path.iterdir())
