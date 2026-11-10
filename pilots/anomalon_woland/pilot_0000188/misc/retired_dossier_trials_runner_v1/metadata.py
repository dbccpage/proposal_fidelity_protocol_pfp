"""Publish standard pilot metadata from immutable campaign inputs and observations."""
import json

import yaml

from omega_engine_education.pfp.domain import PilotSpec, SeedPrompt
from omega_engine_education.pfp.domain.types.test_spec import TestSpec
from omega_engine_education.pfp.domain.types.rewrite_test_plan import RewriteTestPlan

from .cases import FAMILIES, INSTRUCTIONS, PILOTS, SOURCES, carrier
from .prepare import CAMPAIGN

CHECKERS = {188: "PFP-188-BINARY-SPIN-FRUSTRATION", 189: "PFP-189-WEIGHTED-CYCLE-DUALITY",
            190: "PFP-190-DEGREE4-PRIMAL-DUAL", 191: "PFP-191-CHAIN-TOPOLOGY-SCOPE"}


def save(path, document):
    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")


def standardize():
    for pilot in SOURCES:
        folder = PILOTS / f"pilot_{pilot:07d}"
        capsules = sorted((folder / "tests").glob("test_[0-9][0-9]"))
        spec = dict(schema="pfp.pilot-spec.v1", authority_effect="None", pilot_id=folder.name,
            prompt_id=f"prompt_{pilot:07d}", generation_id=1, phase="dossier_replay_campaign", split="development",
            coordinates=dict(task_family=FAMILIES[pilot], difficulty_rung=3,
                representation_rewrite="structured_spans", rewrite_count=1, legend_present=True,
                mode="none", stage_count=1, pass_count=1, single_shot=True, antibody_active=False,
                antibody_ids=[], model_class="open_weights", model_id="nvidia/nemotron-3.5-lightning:free",
                temperature=0.0, target_spend_usd=0.05),
            ingress=dict(task_mode_fidelity="finite_deduction", variable_identifier_permutation="canonical",
                floating_point_approximation_risk="exact_rational", arm_template="A0", missing_premise="mixed",
                cohomology_defect_class="finite", magma_associativity_type="none"),
            host_gate=dict(checker_id=CHECKERS[pilot], response_schema="PromptResponse.v1 with task-specific answer",
                residual_logging=True, structure_delta_metric="exact_rational_delta", expected_outcome="HOST_CHECKED_WITNESS"),
            test_plan=dict(path="testplan.yaml", tests=len(capsules), cases=5, seed="seed.yaml", prompt_template="prompt_template.yaml"),
            responses=dict(directory="tests"))
        PilotSpec.model_validate(spec)
        save(folder / "spec.yaml", spec)
        task = carrier(pilot, 1)
        seed = dict(schema="pfp.seed-prompt.v1", authority_effect="None", pilot_id=folder.name,
            task_family=FAMILIES[pilot], difficulty_rung=1, request_id=folder.name+"_dossier_seed",
            input_typing=dict(lexical_alphabet="UTF-8", syntactic_category="FiniteWitnessCarrier",
                semantic_carrier=FAMILIES[pilot], dialect_tier="SPK-001", boundary_format="JSON within wrapped prompt"),
            seed_prompt=INSTRUCTIONS[task["kind"]]+"\n"+json.dumps(task),
            expected_outcome=dict(answer=None, status="HOST_CHECKED_WITNESS"))
        SeedPrompt.model_validate(seed)
        save(folder / "seed.yaml", seed)
        testplan = dict(schema="pfp.rewrite-test-plan.v1", authority_effect="None", pilot_id=folder.name,
            spec="spec.yaml", responses="tests", description="Five carrier blocks by five wrapped representations, plus five matched guidance follow-ups. Every capsule is a separate provider call; rewrites are not independent mathematical problems.",
            prompt_template=dict(path="prompt_template.yaml", shared_by_all_tests=True),
            seed=dict(path="seed.yaml", seed_prompt=seed["seed_prompt"]),
            expected_outcome=dict(status="HOST_CHECKED_WITNESS"), counts=dict(unique_cases=5, tests=len(capsules)),
            tests=[dict(test_id=c.name, kind="wrapped_provider_trial", artifact=f"tests/{c.name}/input.yaml") for c in capsules])
        RewriteTestPlan.model_validate(testplan)
        save(folder / "testplan.yaml", testplan)
    for pattern in (f"{CAMPAIGN}.yaml", f"{CAMPAIGN}_free.yaml", f"{CAMPAIGN}_guidance.yaml"):
        path = PILOTS / "matrix" / pattern
        if not path.exists():
            continue
        plan = yaml.safe_load(path.read_text(encoding="utf-8"))
        for row in plan["cases"]:
            folder = PILOTS / row["capsule"]
            case = yaml.safe_load((folder / "input.yaml").read_text(encoding="utf-8"))
            response = folder / "response.yaml"
            receipt = yaml.safe_load(response.read_text(encoding="utf-8")) if response.exists() else {}
            failure = folder / "infrastructure_failure.yaml"
            status = receipt.get("status", "INFRASTRUCTURE_ERROR" if failure.exists() else "PLANNED")
            spec = dict(schema="pfp.test-spec.v1", authority_effect="None", pilot_id=case["pilot_id"],
                test_id=f"{CAMPAIGN}_{case['test_index']:02d}", case_id=case["carrier_sha256"],
                test_index=case["test_index"], generation_id=case["prompt"]["lineage"]["generation_id"],
                dialect_name=case["representation"], input_source_file="input.yaml", response_file="response.yaml",
                model_id=receipt.get("model_id", "deepseek/deepseek-v4.1-flash" if failure.exists() else "nvidia/nemotron-3.5-lightning:free"),
                expected_outcome=dict(status="HOST_CHECKED_WITNESS"),
                actual_outcome=dict(status=status, gate_status=status, refusal_code=receipt.get("code") if status == "TYPED_REFUSAL" else None,
                    witness_verified=None if status in ("PLANNED", "INFRASTRUCTURE_ERROR") else status == "HOST_ACCEPTED"),
                notes="Fresh wrapped experiment; retained earlier capsules are not reclassified. input.yaml and raw provider bytes are hash-bound by response.yaml.")
            if receipt:
                spec["metrics"] = dict(duration_seconds=receipt["latency_seconds"],
                    prompt_tokens=receipt["usage"]["prompt_tokens"], completion_tokens=receipt["usage"]["completion_tokens"],
                    total_tokens=receipt["usage"]["total_tokens"], cost_usd=receipt["cost_microusd"]/1_000_000, provider_calls=1)
            TestSpec.model_validate(spec)
            save(folder / "test_spec.yaml", spec)


if __name__ == "__main__":
    standardize()
