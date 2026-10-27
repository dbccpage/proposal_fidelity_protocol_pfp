"""Build and run local mode trials for pilots 0000001 through 0000025.

AuthorityEffect: None.

Pilot 0000001 takes mode 02, pilot 0000002 takes mode 03, and each following
spec-only pilot takes the next mode through mode 20. Pilots 0000020 and
0000021 are staged and overlapping-span variations of mode 02. Pilots
0000022 through 0000025 keep the mode already written on their spec.

The canonical prompt template in pilot_0000000 is an empty generated shell.
These trials use a four-object sealed packet instead. No provider is called.
"""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

from adversary.tests.pilots.replay_runners._paths import repository_root
from adversary.tests.pilots.replay_runners.mode_capsules.packet import (
    MODE_DIRS,
    MODES,
    PILOTS,
    NoAliasDumper,
    digests_match,
)
from adversary.tests.pilots.replay_runners.mode_capsules.trials_01_12 import (
    trial_0000001,
    trial_0000002,
    trial_0000003,
    trial_0000004,
    trial_0000005,
    trial_0000006,
    trial_0000007,
    trial_0000008,
    trial_0000009,
    trial_0000010,
    trial_0000011,
    trial_0000012,
)
from adversary.tests.pilots.replay_runners.mode_capsules.trials_13_25 import (
    trial_0000013,
    trial_0000014,
    trial_0000015,
    trial_0000016,
    trial_0000017,
    trial_0000018,
    trial_0000019,
    trial_0000020,
    trial_0000021,
    trial_0000022,
    trial_0000023,
    trial_0000024,
    trial_0000025,
)

__all__ = ["build_trials", "digests_match", "write_trials"]


BUILDERS = [
    trial_0000001, trial_0000002, trial_0000003, trial_0000004, trial_0000005,
    trial_0000006, trial_0000007, trial_0000008, trial_0000009, trial_0000010,
    trial_0000011, trial_0000012, trial_0000013, trial_0000014, trial_0000015,
    trial_0000016, trial_0000017, trial_0000018, trial_0000019, trial_0000020,
    trial_0000021, trial_0000022, trial_0000023, trial_0000024, trial_0000025,
]


def build_trials() -> list[dict]:
    trials = [builder() for builder in BUILDERS]
    if [trial["pilot_index"] for trial in trials] != list(range(1, 26)):
        raise RuntimeError("pilot index sequence is not 1..25")
    return trials


def _dump(payload: dict) -> str:
    text = yaml.dump(payload, Dumper=NoAliasDumper, sort_keys=False, allow_unicode=True, width=100)
    if not text.endswith("\n"):
        text += "\n"
    return text


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def _render_seed(trial: dict) -> dict:
    return {
        "schema": "pfp.seed-prompt.v1",
        "authority_effect": "None",
        "pilot_id": trial["pilot_id"],
        "task_family": trial["task_family"],
        "difficulty_rung": trial["difficulty_rung"],
        "request_id": f"{trial['pilot_id']}_req_0",
        "input_typing": {
            "lexical_alphabet": "UTF-8",
            "syntactic_category": "ModeTrialSeed",
            "semantic_carrier": trial["task_family"],
            "dialect_tier": trial["mode_coordinate"],
            "boundary_format": "pfp.sealed-packet.v1",
        },
        "seed_prompt": trial["seed_prompt"],
        "expected_outcome": {"answer": trial["answer"], "status": "ACCEPTED"},
    }


def _render_plan(trial: dict) -> dict:
    return {
        "schema": "pfp.mode-trial-plan.v1",
        "authority_effect": "None",
        "pilot_id": trial["pilot_id"],
        "spec": "spec.yaml",
        "mode_id": trial["mode_id"],
        "mode_coordinate": trial["mode_coordinate"],
        "mode_contract": trial["mode_contract"],
        "packet": "packet.yaml",
        "seed": "seed.yaml",
        "responses": "results",
        "canonical_template": (
            "pilot_0000000/prompt_template.yaml is a generated empty shell and is not copied here."
        ),
        "provider_calls": 0,
        "winning_condition_executed": trial["winning_condition_executed"],
        "execution_limit": trial["execution_limit"],
        "advantages": trial["advantages"],
        "disadvantages": trial["disadvantages"],
        "variations": [
            {
                "variation_id": item["variation_id"],
                "role": item["role"],
                "status": item["status"],
                "failure_mode": item["failure_mode"],
            }
            for item in trial["variations"]
        ],
    }


def _render_execution(trial: dict) -> dict:
    return {
        "schema": "pfp.mode-trial-execution.v1",
        "authority_effect": "None",
        "pilot_id": trial["pilot_id"],
        "mode_id": trial["mode_id"],
        "mode_contract": trial["mode_contract"],
        "provider_calls": 0,
        "target_spend_usd": 0.0,
        "winning_condition_executed": trial["winning_condition_executed"],
        "execution_limit": trial["execution_limit"],
        "advantages": trial["advantages"],
        "disadvantages": trial["disadvantages"],
        "variations": trial["variations"],
    }


def _update_spec(path: Path, trial: dict) -> None:
    text = path.read_text(encoding="utf-8")
    if "\r" in text:
        raise RuntimeError(f"CRLF in {path}")
    mode_line = "\n  mode: "
    start = text.find(mode_line)
    if start < 0:
        raise RuntimeError(f"no mode line in {path}")
    end = text.find("\n", start + 1)
    current = text[start + len(mode_line):end]
    if trial["overwrite_mode"]:
        if current not in {"none", trial["mode_coordinate"]}:
            raise RuntimeError(f"{path} mode is {current}, refused to overwrite")
        text = text[: start + len(mode_line)] + trial["mode_coordinate"] + text[end:]
    elif current != trial["mode_coordinate"]:
        raise RuntimeError(f"{path} mode {current} does not match {trial['mode_coordinate']}")
    if trial["stage_count"] == 2:
        text = text.replace("\n  stage_count: 1\n", "\n  stage_count: 2\n", 1)
        text = text.replace("\n  single_shot: true\n", "\n  single_shot: false\n", 1)
    if trial["antibody_ids"]:
        text = text.replace("\n  antibody_active: false\n", "\n  antibody_active: true\n", 1)
        if "\n  antibody_ids: []\n" in text:
            rendered = "\n  antibody_ids:\n" + "".join(f"    - {item}\n" for item in trial["antibody_ids"])
            text = text.replace("\n  antibody_ids: []\n", rendered, 1)
    block = (
        "test_plan:\n"
        "  path: testplan.yaml\n"
        f"  mode_id: {trial['mode_id']}\n"
        "  packet: packet.yaml\n"
        "  seed: seed.yaml\n"
        f"  variations: {len(trial['variations'])}\n"
        "responses:\n"
        "  directory: results\n"
    )
    marker = "\n# Folder pointers. PilotSpec ignores unknown keys.\n"
    if marker in text:
        text = text[: text.index(marker)]
        if not text.endswith("\n"):
            text += "\n"
    text = text.rstrip("\n") + marker + block
    _write(path, text if text.endswith("\n") else text + "\n")


def _dimension_probe_section(folder: Path) -> str:
    """One README section taken from tests/dimension_testplan.yaml."""
    plan_path = folder / "tests" / "dimension_testplan.yaml"
    if not plan_path.is_file():
        return ""
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    counts = plan.get("counts") if isinstance(plan, dict) else None
    if not isinstance(counts, dict) or not isinstance(counts.get("tests"), int):
        return ""
    description = plan.get("description") if isinstance(plan, dict) else None
    prose = " ".join(description.split()) if isinstance(description, str) else ""
    body = f"`tests/dimension_testplan.yaml` records {counts['tests']} probes."
    if prose:
        body = f"{body} {prose}"
    return f"\n\n## 4. Dimension probes\n{body}\n"


def _replace_section(text: str, marker: str, section: str) -> str:
    if marker not in text:
        return text.rstrip("\n") + section
    start = text.index(marker)
    following = text[start + len(marker):]
    next_section = following.find("\n## ")
    suffix = following[next_section:] if next_section >= 0 else ""
    return text[:start].rstrip("\n") + section + suffix


def _update_readme(path: Path, trial: dict) -> None:
    text = path.read_text(encoding="utf-8")
    section = (
        "\n\n## 3. Mode trial\n"
        f"Local execution of `{trial['mode_coordinate']}` against `{trial['mode_contract']}`.\n"
        "The packet is the four-object seal in `packet.yaml`. "
        "`pilot_0000000/prompt_template.yaml` is a generated empty shell and is not copied into this pilot.\n"
        f"`results/execution.yaml` records {len(trial['variations'])} variations. "
        "Provider calls: 0. Spend: 0.\n"
        f"Winning condition executed: `{str(trial['winning_condition_executed']).lower()}`.\n"
        f"Limit: {trial['execution_limit']}\n"
    )
    text = _replace_section(text, "\n## 3. Mode trial\n", section)
    probe = _dimension_probe_section(path.parent)
    if probe:
        text = _replace_section(text, "\n## 4. Dimension probes\n", probe)
    _write(path, text if text.endswith("\n") else text + "\n")


def _capsule_layout(folder: Path) -> bool:
    spec_path = folder / "spec.yaml"
    if not spec_path.is_file() or not (folder / "tests" / "test_49").is_dir():
        return False
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    responses = spec.get("responses") if isinstance(spec, dict) else None
    return isinstance(responses, dict) and responses.get("directory") == "misc"


def pilot_folder(pilot_id: str) -> Path:
    direct = PILOTS / pilot_id
    if direct.is_dir():
        return direct
    relocated = repository_root(PILOTS) / "pfp" / "tests" / pilot_id
    if relocated.is_dir():
        return relocated
    return direct


def write_trials(trials: list[dict] | None = None) -> list[dict]:
    trials = build_trials() if trials is None else trials
    for trial in trials:
        folder = pilot_folder(trial["pilot_id"])
        spec_path = folder / "spec.yaml"
        if _capsule_layout(folder):
            continue
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        coordinates = spec["coordinates"]
        if coordinates["task_family"] != trial["task_family"] or coordinates["difficulty_rung"] != trial["difficulty_rung"]:
            raise RuntimeError(f"{trial['pilot_id']} family or rung does not match the spec")
        if not (MODES / MODE_DIRS[trial["mode_id"]] / "contract.yaml").is_file():
            raise RuntimeError(f"missing contract for mode {trial['mode_id']}")
        _write(folder / "seed.yaml", _dump(copy.deepcopy(_render_seed(trial))))
        _write(folder / "packet.yaml", _dump(copy.deepcopy(trial["packet"])))
        _write(folder / "testplan.yaml", _dump(copy.deepcopy(_render_plan(trial))))
        _write(folder / "results" / "execution.yaml", _dump(copy.deepcopy(_render_execution(trial))))
        _update_spec(spec_path, trial)
        _update_readme(folder / "README.md", trial)
    return trials


def main() -> None:
    trials = write_trials()
    executed = sum(1 for trial in trials if trial["winning_condition_executed"])
    print(f"pilots {len(trials)} winning_condition_executed {executed} provider_calls 0")


if __name__ == "__main__":
    main()
