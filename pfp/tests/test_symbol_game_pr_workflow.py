from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "symbol-game-pr.yml"
CONTAINMENT_SOURCES = (
    "operads/controllers/router.py",
    "operads/controllers/wire_dtos.py",
    "operads/frontend/api/app.py",
)


def _workflow() -> dict:
    loaded = yaml.load(
        WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    assert isinstance(loaded, dict)
    return loaded


def _code_change_steps() -> list[dict]:
    steps = _workflow()["jobs"]["code-change"]["steps"]
    assert isinstance(steps, list)
    return steps


def _assert_native_order(steps: list[dict]) -> None:
    """Validate the shipped split Cargo jobs and bounded Python runner."""
    names = [step.get("name") for step in steps]
    required = (
        "Generated contract census is current",
        "Pinned attack-surface census is current",
        "Attack-surface census tests",
        "Evidence freshness sweep",
        "Stopping-point battery",
        "Fail-closed cadence and evidence tests",
        "Local request containment tests",
        "Build native Symbol Game host",
        "Rust Symbol Game runtime suite",
        "Rust Symbol Game host suite",
        "Symbol Game suites (sequential source-bound batches)",
    )
    for name in required:
        assert names.count(name) == 1, f"MISSING_OR_DUPLICATE_WORKFLOW_STEP: {name}"
    generated_index = names.index("Generated contract census is current")
    census_index = names.index("Pinned attack-surface census is current")
    census_tests_index = names.index("Attack-surface census tests")
    freshness_index = names.index("Evidence freshness sweep")
    stopping_index = names.index("Stopping-point battery")
    defense_index = names.index("Fail-closed cadence and evidence tests")
    build_index = names.index("Build native Symbol Game host")
    local_http_index = names.index("Local request containment tests")
    rust_index = names.index("Rust Symbol Game runtime suite")
    host_index = names.index("Rust Symbol Game host suite")
    suite_index = names.index("Symbol Game suites (sequential source-bound batches)")

    assert (
        generated_index
        < census_index
        < census_tests_index
        < freshness_index
        < stopping_index
        < defense_index
        < local_http_index
        < build_index
        < rust_index
        < host_index
        < suite_index
    )
    assert steps[census_index]["run"] == (
        "python operations/use_cases/verification/"
        "symbol_game_attack_surface.py --check "
        "operations/evidence/"
        "symbol_game_attack_surface_20260903.jsonl"
    )
    assert steps[census_tests_index]["run"] == (
        "python -m pytest -q -n 8 --import-mode=importlib "
        '--basetemp "${{ runner.temp }}/symgam-census" '
        "operations/tests/unit/test_symbol_game_attack_surface.py"
    )
    assert steps[freshness_index]["run"] == (
        "python -m operations.use_cases.verification.evidence_freshness"
    )
    assert steps[stopping_index]["run"] == (
        "python -m operations.use_cases.verification.stopping_point"
    )
    assert steps[defense_index]["run"] == (
        "python -m pytest -q -n 8 --import-mode=importlib "
        '--basetemp "${{ runner.temp }}/symgam-defense" '
        "operations/tests/unit/test_fail_closed_audit.py "
        "operations/tests/unit/test_stopping_point_register.py "
        "operations/tests/unit/test_evidence_freshness.py"
    )
    assert steps[build_index]["working-directory"] == "engine/crates_rs"
    assert steps[local_http_index]["run"] == (
        "python -m pytest -q -n 8 --import-mode=importlib "
        '--basetemp "${{ runner.temp }}/symgam-local-http" '
        "operations/tests/unit/test_http_local_containment.py "
        "operads/tests/contract/test_http_request_boundary.py"
    )
    assert steps[build_index]["run"] == "cargo build -j 1 -p core_symbol_game"
    assert steps[rust_index]["working-directory"] == "engine/crates_rs"
    assert steps[rust_index]["run"] == ("cargo test -j 1 -p core_symbol_game_runtime")
    assert steps[host_index]["working-directory"] == "engine/crates_rs"
    assert steps[host_index]["run"] == "cargo test -j 1 -p core_symbol_game"
    suite = steps[suite_index]
    assert suite["shell"] == "pwsh"
    for guard in (
        "$campaignSource = git rev-parse HEAD",
        "'git', 'ls-tree', '-r', '--name-only', '-z', 'HEAD'",
        "EMPTY_SYMBOL_GAME_TEST_SCOPE",
        "MISSING_PACKET_SUITE",
        "$campaignIndex += 3",
        "[Math]::Min($campaignIndex + 2, $campaignFiles.Count - 1)",
        "TEST_SOURCE_CHANGED",
        "engine/_tests_unit/test_code_change_proposal_packets.py",
        "engine/_tests_unit/test_llm_turn_packets.py",
        "python -m operations.use_cases.verification.windows_python_campaign_batch",
        '--basetemp "${{ runner.temp }}/symgam-tests-$campaignIndex" @campaignBatch',
        "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }",
    ):
        assert guard in suite["run"], f"MISSING_BATCH_GUARD: {guard}"
    lines = [line.strip() for line in suite["run"].splitlines() if line.strip()]
    source_guard = (
        'if ((git rev-parse HEAD) -ne $campaignSource) { throw "TEST_SOURCE_CHANGED" }'
    )
    assert source_guard in lines, "SOURCE_COMPARISON_CHANGED"
    runner = (
        "python -m operations.use_cases.verification."
        "windows_python_campaign_batch --root . "
        '--report-dir "${{ runner.temp }}/symgam-evidence-$campaignIndex" '
        '--basetemp "${{ runner.temp }}/symgam-tests-$campaignIndex" @campaignBatch'
    )
    assert lines.count(runner) == 1, "CAMPAIGN_RUNNER_CHANGED"
    runner_index = lines.index(runner)
    assert lines[runner_index + 1] == (
        "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }"
    ), "CAMPAIGN_FAILURE_NOT_PROPAGATED"


def test_symbol_game_pr_builds_native_host_before_full_python_suite() -> None:
    _assert_native_order(_code_change_steps())


@pytest.mark.parametrize(
    "missing",
    [
        "Build native Symbol Game host",
        "Rust Symbol Game runtime suite",
        "Rust Symbol Game host suite",
    ],
)
def test_native_order_oracle_names_missing_steps(missing: str) -> None:
    steps = [step for step in _code_change_steps() if step.get("name") != missing]
    with pytest.raises(AssertionError, match="MISSING_OR_DUPLICATE_WORKFLOW_STEP"):
        _assert_native_order(steps)


def test_native_order_oracle_rejects_build_after_python() -> None:
    steps = _code_change_steps()
    build = next(
        step for step in steps if step.get("name") == "Build native Symbol Game host"
    )
    steps.remove(build)
    steps.append(build)
    with pytest.raises(AssertionError):
        _assert_native_order(steps)


def test_native_order_oracle_rejects_duplicate_host_step() -> None:
    steps = _code_change_steps()
    steps.append(
        next(
            step for step in steps if step.get("name") == "Rust Symbol Game host suite"
        )
    )
    with pytest.raises(AssertionError, match="MISSING_OR_DUPLICATE_WORKFLOW_STEP"):
        _assert_native_order(steps)


@pytest.mark.parametrize(
    "guard",
    ["$campaignIndex += 3", "TEST_SOURCE_CHANGED", "EMPTY_SYMBOL_GAME_TEST_SCOPE"],
)
def test_native_order_oracle_rejects_missing_batch_guards(guard: str) -> None:
    steps = _code_change_steps()
    suite = next(
        step
        for step in steps
        if step.get("name") == "Symbol Game suites (sequential source-bound batches)"
    )
    assert suite["run"].count(guard) == 1
    suite["run"] = suite["run"].replace(guard, "REMOVED_GUARD")
    with pytest.raises(AssertionError, match="MISSING_BATCH_GUARD"):
        _assert_native_order(steps)


@pytest.mark.parametrize("mutation", ["last_exit", "inverted_source"])
def test_native_order_oracle_rejects_unbound_success(mutation: str) -> None:
    steps = _code_change_steps()
    suite = next(
        step
        for step in steps
        if step.get("name") == "Symbol Game suites (sequential source-bound batches)"
    )
    if mutation == "last_exit":
        guard = "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }"
        before, separator, after = suite["run"].rpartition(guard)
        assert separator and before.count(guard) == 2
        suite["run"] = before + after
        expected = "CAMPAIGN_FAILURE_NOT_PROPAGATED"
    else:
        guard = "(git rev-parse HEAD) -ne $campaignSource"
        assert suite["run"].count(guard) == 1
        suite["run"] = suite["run"].replace(guard, guard.replace("-ne", "-eq"))
        expected = "SOURCE_COMPARISON_CHANGED"
    with pytest.raises(AssertionError, match=expected):
        _assert_native_order(steps)


def _assert_containment_source_trigger(workflow: dict, source_path: str) -> None:
    triggers = workflow.get("on", workflow.get(True))
    # The nightly pass runs on a schedule with no path filter, so a change to
    # any source is covered by the next run. A trigger that carries a path
    # filter must list the source literally, with no exclusions.
    assert "schedule" in triggers, "MISSING_CONTAINMENT_TRIGGER: no schedule"
    for spec in triggers.values():
        if isinstance(spec, dict) and ("paths" in spec or "paths-ignore" in spec):
            paths = spec.get("paths", [])
            assert paths.count(source_path) == 1, (
                f"MISSING_CONTAINMENT_TRIGGER: {source_path}"
            )
            assert "paths-ignore" not in spec
            assert not any(pattern.startswith("!") for pattern in paths)
    job = workflow["jobs"]["code-change"]
    step = next(
        step
        for step in job["steps"]
        if step["name"] == "Local request containment tests"
    )
    assert "if" not in job and "if" not in step
    assert (
        "operads/tests/contract/test_http_request_boundary.py"
        in step["run"].split()
    )


@pytest.mark.parametrize("source_path", CONTAINMENT_SOURCES)
def test_each_boundary_source_triggers_pr_containment_tests(source_path: str) -> None:
    assert (REPO_ROOT / source_path).is_file()
    _assert_containment_source_trigger(_workflow(), source_path)


@pytest.mark.parametrize("source_path", CONTAINMENT_SOURCES)
def test_containment_trigger_oracle_rejects_removed_source(source_path: str) -> None:
    workflow = _workflow()
    workflow["on"] = {
        "schedule": [{"cron": "17 3 * * *"}],
        "push": {"paths": [p for p in CONTAINMENT_SOURCES if p != source_path]},
    }
    with pytest.raises(AssertionError, match="MISSING_CONTAINMENT_TRIGGER"):
        _assert_containment_source_trigger(workflow, source_path)


def test_symbol_game_pr_installs_parallel_runner_and_tracks_all_inputs() -> None:
    workflow = _workflow()
    steps = workflow["jobs"]["code-change"]["steps"]
    install = next(step for step in steps if step.get("name") == "Install dependencies")
    assert "networkx" in install["run"].split()
    assert "pytest-xdist" in install["run"].split()
    assert "fastapi" in install["run"].split()
    assert "httpx" in install["run"].split()

    triggers = workflow.get("on", workflow.get(True))
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    # No path filter: every input the per-PR filter used to list is covered by
    # each nightly run.
    assert all(not isinstance(spec, dict) or "paths" not in spec for spec in triggers.values())
