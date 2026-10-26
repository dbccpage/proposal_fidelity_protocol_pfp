"""Replayable fixture bouts with observed-checker-guided prompt revisions.

No model/provider is called. Candidate guidance is experimental; neither a
fixture pass nor a mutation grants admission or establishes live efficacy.
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import (
    read_activation,
    safe_path,
)
from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
    resolve_intelligence_repo_root,
)
from omega_engine_prompt_civilization.domain.models import ProtectedSpanV1
from omega_engine_prompt_civilization.infrastructure.cas import ContentAddressedStorageV1
from omega_engine_prompt_civilization.use_cases.fitness import PromptFitnessCalculatorV1
from omega_engine_prompt_civilization.use_cases.forge import PromptMutationEngineV1
from omega_engine_woland.domain.evidence import CheckerVerdict, sha256_ref
from omega_engine_woland.domain.models import SymbolGameRequestV1
from omega_engine_woland.infrastructure.native import DefaultNativeOperationPort
from omega_engine_woland.infrastructure.symbol_game_checker import SymbolGameCandidateChecker
from omega_engine_woland.runtime import build_woland_runtime
from omega_engine_woland.stage.domain import WorkPacketV1
from omega_engine_woland.use_cases.bout_service import execute_7act_woland_bout

CORE = b"# Immutable core: exact arithmetic; AuthorityEffect: None.\n"
AGENTS = ("agent_alpha", "agent_beta", "agent_gamma")


def _json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _case(seed: int, agent_index: int) -> dict[str, Any]:
    return {"challenge": "c011", "nodes": ["a", "b"], "edges": [["a", "b"]],
            "claims": {"a->b": f"{(seed + agent_index) % 7 + 1}/10"}}


def replay_observation(observation: dict[str, Any]) -> bool:
    """Re-execute the independent checker on retained exact task/candidate bytes."""
    checker = SymbolGameCandidateChecker(SymbolGameRequestV1(observation["case_json"]))
    candidate = bytes.fromhex(observation["candidate_hex"])
    checked = checker.check_candidate(
        run_key=observation["run_key"], objective=observation["objective"],
        candidate_id=observation["candidate_id"], candidate_bytes=candidate,
        carrier_context=None,
    )
    if checked.is_err:
        return False
    check = checked.unwrap()
    return (
        check.candidate_content_sha256 == observation["candidate_content_sha256"]
        and check.checker_receipt_bytes.hex() == observation["checker_receipt_hex"]
        and check.checker_receipt_sha256 == observation["checker_receipt_sha256"]
        and check.verdict.value == observation["verdict"]
    )


def run_stress_test(
    num_generations: int = 50, output_dir: Path | None = None, *, seed: int = 0,
) -> dict[str, Any]:
    """Run bounded real fixture bouts; only observed rejections add new hints."""
    if type(num_generations) is not int or not 1 <= num_generations <= 50:
        raise ValueError("generations must be an integer in [1, 50]")
    if type(seed) is not int or not 0 <= seed <= 1_000_000:
        raise ValueError("seed must be an integer in [0, 1000000]")
    if output_dir is None:
        root = resolve_intelligence_repo_root()
        read_activation(root)
        output_dir = safe_path(root, f"_ic/darpa/prompt_civ/evolutionary_stress_seed_{seed}")
    output_dir = Path(output_dir).absolute()
    if "_ic" in output_dir.parts:
        boundary = output_dir.parts.index("_ic")
        owner = Path(*output_dir.parts[:boundary])
        read_activation(owner)
        output_dir = safe_path(owner, "/".join(output_dir.parts[boundary:]))
    output_dir.mkdir(parents=True, exist_ok=True)
    cas = ContentAddressedStorageV1(output_dir / "cas")
    genomes = {agent: CORE + f"# Lineage: {agent}\nReturn a C011 certificate.\n".encode() for agent in AGENTS}
    learned: dict[str, set[str]] = {agent: set() for agent in AGENTS}
    rounds: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    for generation in range(1, num_generations + 1):
        for index, agent in enumerate(AGENTS):
            parent = genomes[agent]
            parent_digest = cas.store(parent)
            case_json = _json(_case(seed, index)).decode()
            objective = (
                f"Prompt genome {parent_digest}\n{parent.decode('utf-8')}\n"
                f"Finite task: {case_json}\nReturn a complete exact JSON certificate."
            )
            task_key = f"stress_s{seed}_g{generation:02d}_{agent}"
            packet = WorkPacketV1(
                task_key=task_key, scene_id="act1_perception", objective=objective,
                input_artifact_refs=(parent_digest,), acceptance_criteria=("Independent C011 check",),
                budget_units=50, evaluator_epoch_id=sha256_ref(case_json.encode()),
            )
            fitness = PromptFitnessCalculatorV1(
                candidate_checker=SymbolGameCandidateChecker(SymbolGameRequestV1(case_json)),
            )
            runtime = build_woland_runtime(output_dir=output_dir, fixture_mode=True)
            bout = execute_7act_woland_bout(
                runtime.profile, runtime, packet, candidate_checker=fitness,
                output_dir=output_dir / "_woland", fixture_seats=True,
                native_support=DefaultNativeOperationPort(),
            )
            if bout.is_err:
                raise RuntimeError(f"Fixture bout refused: {bout.unwrap_err()}")
            failures = []
            for inputs, check in zip(fitness.observed_inputs, fitness.observed_checks, strict=True):
                run_key, checked_objective, candidate_id, candidate_bytes = inputs
                record = {
                    "run_key": run_key, "objective": checked_objective, "candidate_id": candidate_id,
                    "candidate_hex": candidate_bytes.hex(), "candidate_content_sha256": sha256_ref(candidate_bytes),
                    "parent_genome_sha256": parent_digest,
                    "case_json": case_json, **check.to_dict(),
                }
                if not replay_observation(record):
                    raise RuntimeError("CHECKER_REPLAY_MISMATCH")
                observations.append(record)
                if check.verdict is CheckerVerdict.REJECTED:
                    failures.append({"checker_id": check.checker_id, "reason": check.reason})
            hints = sorted({_json(failure).decode() for failure in failures} - learned[agent])
            child = parent
            if hints:
                addition = ("\n# Experimental hints from actual rejected checker receipts:\n"
                            + "\n".join("# " + hint for hint in hints) + "\n").encode()
                child = PromptMutationEngineV1().apply_mutation(
                    original_bytes=parent, protected_spans=(ProtectedSpanV1("core", 0, len(CORE)),),
                    edit_start_byte=len(parent), edit_end_byte=len(parent), replacement_bytes=addition,
                )
                learned[agent].update(hints)
            child_digest = cas.store(child)
            genomes[agent] = child
            rounds.append({
                "generation": generation, "agent": agent, "task_key": task_key,
                "parent_genome_sha256": parent_digest, "child_genome_sha256": child_digest,
                "input_packet_sha256": packet.packet_id, "bout_receipt_sha256": bout.unwrap().receipt_id,
                "checker_verdicts": [check.verdict.value for check in fitness.observed_checks],
                "checker_receipt_refs": [check.checker_receipt_sha256 for check in fitness.observed_checks],
                "new_hints": hints, "learning_status": "UPDATED" if hints else "NO_NEW_HINT",
                "cochain_status": "NOT_MEASURED", "authority_effect": "None",
            })
    semantic = [{key: value for key, value in row.items()
                 if key not in {"bout_receipt_sha256", "checker_receipt_refs", "input_packet_sha256"}}
                for row in rounds]
    summary = {
        "schema": "omega.prompt_civ.fixture_evolution.v2", "authority_effect": "None",
        "source_sha256": sha256_ref(Path(__file__).read_bytes()), "seed": seed,
        "total_generations": num_generations, "total_agents": len(AGENTS),
        "total_bouts_executed": len(rounds), "learning_updates": sum(bool(row["new_hints"]) for row in rounds),
        "checked_candidates": len(observations),
        "accepted_candidates": sum(row["verdict"] == "ACCEPTED" for row in observations),
        "rejected_candidates": sum(row["verdict"] == "REJECTED" for row in observations),
        "openrouter_live_calls": 0, "openrouter_cost_usd": "0.00",
        "efficacy": "NOT_MEASURED", "replay_sha256": sha256_ref(_json(semantic)),
        "scope": "Finite C011 fixture transport/checker/rewrite custody; no live model efficacy or admission",
        "rounds": rounds, "observations": observations,
    }
    (output_dir / "summary.json").write_bytes(_json(summary) + b"\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    summary = run_stress_test(args.generations, args.output_dir, seed=args.seed)
    print(json.dumps({key: value for key, value in summary.items() if key not in {"rounds", "observations"}}, indent=2))


if __name__ == "__main__":
    main()
