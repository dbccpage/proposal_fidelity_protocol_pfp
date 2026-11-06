"""Evidence-bound candidate guidance and a bounded matched follow-up; no admission."""
from __future__ import annotations

from collections import Counter
import copy
import json

import yaml

from omega_engine_education.pfp.domain.pilots.checker_registry import strict_json

from .cases import PILOTS, canonical, sha
from .checking import StrictValidator, check_answer
from .prepare import CAMPAIGN, write_once
from .run import load_case, replay_one

GUIDANCE = (
    "Response-contract checkpoint: summary is an OBJECT, never a string. Its required string fields are "
    "narrowest_defensible_thesis, evidence_scope, and next_concrete_test. process_integrity is an OBJECT "
    "containing the boolean fields seed_allows_theory_refutation and should_continue; detected_prompt_biases "
    "is an array of strings. Place the mathematical witness only in answer, using exactly the fields and "
    "types in its schema. Before emitting, substitute the proposed witness into the original carrier and "
    "recompute its target or residual. A summary cannot override a conflicting witness. "
    "Supply only the requested JSON envelope. Do not print your private reasoning."
)


def diagnostics(row):
    folder, case = load_case(row)
    if not (folder / "provider_response.json").exists():
        return None
    raw = (folder / "provider_response.json").read_bytes()
    response = strict_json(raw.decode("utf-8"))
    try:
        payload = strict_json(response["choices"][0]["message"]["content"])
    except (ValueError, KeyError, TypeError):
        return dict(capsule=row["capsule"], response_sha256=sha(raw), signature="invalid_json", answer_valid=None)
    schema = yaml.safe_load(case["prompt"]["response_schema"])
    errors = list(StrictValidator(schema).iter_errors(payload))
    signature = "summary_string" if isinstance(payload, dict) and type(payload.get("summary")) is str else "other_schema" if errors else "schema_valid"
    try:
        answer_valid = check_answer(case["task"], payload["answer"])
    except (ValueError, TypeError, KeyError, __import__("jsonschema").ValidationError):
        answer_valid = False
    return dict(capsule=row["capsule"], response_sha256=sha(raw), signature=signature,
                schema_error_paths=[list(e.path) for e in errors], answer_valid=answer_valid,
                note="Answer-only diagnostic is never a full-envelope acceptance.")


def prepare_followup():
    original = yaml.safe_load((PILOTS / "matrix" / f"{CAMPAIGN}_free.yaml").read_text())
    path = PILOTS / "matrix" / f"{CAMPAIGN}_guidance.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text())
    evidence = [d for row in original["cases"] if (d := diagnostics(row)) and d["signature"] == "summary_string"]
    if len(evidence) < 5:
        raise ValueError("INSUFFICIENT_FAILURE_EVIDENCE")
    rows = []
    for row in original["cases"]:
        parent, case = load_case(row)
        if case["rung"] != 3:
            continue
        existing = [int(p.name[5:]) for p in parent.parent.glob("test_[0-9][0-9]")]
        index = max(existing)+1
        if index > 99:
            raise ValueError("PILOT_TEST_LIMIT")
        updated = copy.deepcopy(case)
        updated.update(test_index=index, guidance_arm="explicit_summary_and_substitution", parent_capsule=row["capsule"])
        updated["prompt"]["lineage"].update(generation_id=2, parent_id=case["prompt"]["lineage"]["prompt_id"],
            prompt_id=case["prompt"]["lineage"]["prompt_id"]+"_guidance")
        updated["prompt"]["guidance"]["rules"] = [dict(rule_id="candidate_typed_summary_and_witness", statement=GUIDANCE)]
        updated["prompt"]["user_prompt"] += "\nCandidate guidance derived from earlier observed failures:\n" + GUIDANCE
        target = parent.parent / f"test_{index:02d}"
        write_once(target / "input.yaml", updated)
        write_once(target / "test_spec.yaml", dict(schema="pfp.test-spec.v1", pilot_id=case["pilot_id"],
            test_id=f"guidance_{index:02d}", case_id=case["carrier_sha256"], test_index=index,
            model_id="nvidia/nemotron-3.5-lightning:free", dialect_name=case["representation"],
            input_source_file="input.yaml", response_file="response.yaml",
            expected_outcome=dict(status="HOST_CHECKED_WITNESS"), actual_outcome=dict(status="PLANNED"),
            notes="Exploratory matched guidance follow-up. Same carrier and representation; no changed oracle or answer disclosure.",
            authority_effect="None"))
        rows.append(dict(pilot_id=case["pilot_id"], capsule=target.relative_to(PILOTS).as_posix(),
                         input_sha256=sha((target / "input.yaml").read_bytes()), parent_capsule=row["capsule"]))
    plan = dict(schema="pfp.dossier-guidance-followup.v1", campaign=CAMPAIGN, cases=rows,
                tests=50, new_independent_problems=0, matched_pairs=50, status="PLANNED",
                limitations="Fixed-order exploratory follow-up, not randomized evidence of a causal improvement.")
    write_once(path, plan)
    candidate = dict(schema="pfp.evidence-derived-guidance.v1", authority_effect="None", admitted=False,
        status="candidate_pending_followup", signature="summary_string", evidence=evidence[:10],
        artifacts={
            "skill": dict(name="Preserve object-valued summary slots", procedure=GUIDANCE),
            "antiskill": dict(name="Do not compress a typed object into narrative", avoid="A summary string substituted for required nested fields."),
            "pattern": dict(name="Witness then typed envelope", apply="Validate the witness by substitution and the envelope independently."),
            "rule": dict(name="Field-type fidelity", statement="Do not coerce summary strings, numeric strings, floats or booleans into a successful response."),
            "prompt_family": dict(name="explicit_summary_and_substitution", parent="SPK-001 wrapped carrier", mutation=GUIDANCE),
            "antibody": dict(name="AB_DOSSIER_SUMMARY_STRING", detector="StrictValidator rejects a string at summary", action="typed refusal", auto_admitted=False,
                             positive_control="test_every_wrapped_case_and_strict_ingress", negative_control="observed summary_string responses")})
    write_once(PILOTS / "matrix" / CAMPAIGN / "candidate_guidance.yaml", candidate)
    return plan


def report():
    baseline = yaml.safe_load((PILOTS / "matrix" / f"{CAMPAIGN}_free.yaml").read_text())
    followup_path = PILOTS / "matrix" / f"{CAMPAIGN}_guidance.yaml"
    followup = yaml.safe_load(followup_path.read_text()) if followup_path.exists() else {"cases": []}
    config = yaml.safe_load((PILOTS / "matrix" / CAMPAIGN / "free_followup" / "authorization.yaml").read_text())
    rows = []
    for arm, plan in (("baseline", baseline), ("guidance", followup)):
        for row in plan["cases"]:
            folder, _ = load_case(row)
            if not (folder / "response.yaml").exists():
                rows.append(dict(arm=arm, capsule=row["capsule"], status="PLANNED"))
            else:
                rows.append(dict(arm=arm, **replay_one(row, config), diagnostics=diagnostics(row)))
    summary = dict(schema="pfp.dossier-results.v1", authority_effect="None", rows=rows,
                   statuses=dict(Counter(r["status"] for r in rows)), provider_completed=sum("generation_id" in r for r in rows),
                   cost_microusd=sum(r.get("cost_microusd", 0) for r in rows),
                   paid_failure=dict(status="INFRASTRUCTURE_ERROR", code="PROVIDER_HTTP_429", billed_cost=None,
                                     reservation_retained=True, automatic_retry=False))
    if summary["statuses"].get("PLANNED", 0) == 0:
        write_once(PILOTS / "matrix" / CAMPAIGN / "final_results.json", canonical(summary)+b"\n")
    return summary


if __name__ == "__main__":
    print(json.dumps({k: v for k, v in report().items() if k != "rows"}, indent=2))
