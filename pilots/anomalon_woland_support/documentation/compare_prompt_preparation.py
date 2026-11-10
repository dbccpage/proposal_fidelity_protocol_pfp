"""Offline comparison of an actual `teamwork next` report; no model dispatch."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from omega_engine_woland.infrastructure.native import value
from omega_engine_woland.infrastructure.prompt_geometry import observe_text
from omega_engine_woland.use_cases.teamwork import TeamworkAction
from omega_engine_woland.use_cases.teamwork_pfp import prepare_teamwork_turn


def compare(report: dict) -> dict:
    action = TeamworkAction.model_validate(report["next_action"])
    preparation = action.brief.forge_preparation
    seed = action.objective
    organized = preparation["organized_text"]
    if not organized.encode("utf-8").startswith(seed.encode("utf-8")):
        raise ValueError("FORGE_SEED_CHANGED")
    measurements = []
    for dimension in (28, 128, 1024):
        observations, times = [], []
        for source in (seed, organized):
            started = perf_counter()
            observation = observe_text(source, dimension=dimension, role_id="hella",
                                       field="seed", trust_level="user-seed")
            times.append(perf_counter() - started)
            if observation["status"] != "OBSERVED":
                raise ValueError("OBSERVATION_UNAVAILABLE: " + observation["status"])
            observations.append(observation)
        divergence = value("prompt_density_compare", left=observations[0], right=observations[1])
        if divergence["status"] != "COMPARED":
            raise ValueError("COMPARISON_UNAVAILABLE: " + divergence["status"])
        fields = ("source_sha256", "source_bytes", "entropy_bits", "purity",
                  "effective_rank", "numerical_rank")
        measurements.append({
            "dimension": dimension,
            "original": {key: observations[0][key] for key in fields},
            "organized": {key: observations[1][key] for key in fields},
            "quantum_jensen_shannon_bits": divergence["quantum_jensen_shannon_bits"],
            "single_observation_wall_seconds_including_native_bridge": times,
        })
    without_forge = action.model_copy(update={"brief": action.brief.model_copy(update={
        "forge_organization": False, "forge_preparation": None})})
    rendered = []
    for candidate in (without_forge, action):
        started = perf_counter()
        turn = prepare_teamwork_turn(candidate, observe=False)
        rendered.append({"system_utf8_bytes": len(turn.prompt.system.encode("utf-8")),
                         "user_utf8_bytes": len(turn.prompt.user.encode("utf-8")),
                         "wall_seconds": perf_counter() - started,
                         "input_sha256": turn.binding["input_sha256"]})
    return {
        "scope": "Offline single measurements on an actual prepared IDE prompt; no provider or accuracy experiment.",
        "original_seed_preserved_verbatim": True,
        "organization_operation": preparation["operation_id"],
        "profile": "ordered-sha256-density-v1",
        "provider_tokens": None, "provider_tokens_status": "UNOBSERVED",
        "density": measurements, "preparation_off_then_on": rendered,
        "interpretation": "Rendered byte overhead and diagnostic geometry do not establish accuracy, semantic health or token savings.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare(json.loads(args.report.read_bytes()))
    raw = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output is not None:
        args.output.write_text(raw, encoding="utf-8")
    print(raw, end="")


if __name__ == "__main__":
    main()
