"""Evidence-bound candidate guidance and a bounded matched follow-up; no admission."""
from __future__ import annotations

from collections import Counter
import json

import yaml

from omega_engine_pfp.domain.pilots.checker_registry import strict_json

from .cases import sha
from .checking import StrictValidator, check_answer
from .prepare import historical_bytes, historical_plan
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
    return historical_plan("_guidance")


def report():
    baseline = historical_plan("_free")
    followup = historical_plan("_guidance")
    config = yaml.safe_load(historical_bytes("matrix/replay_custody_20261011/free_followup/authorization.yaml"))
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
    return summary


if __name__ == "__main__":
    print(json.dumps({k: v for k, v in report().items() if k != "rows"}, indent=2))
