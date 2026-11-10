"""Run the actual finite host operations and PFP fixture checks, without sends."""

from __future__ import annotations

import base64
import hashlib
import json
from fractions import Fraction
from pathlib import Path

from omega_engine_pfp.domain.rewriting.finite_dpo import graph_digest
from omega_engine_woland.tests.pilots.acset_prompt_rewriting.pilot import (
    insertion_rules,
    judge_preserved_prompt,
    operation_receipt,
    prepared_turn,
    prompt_state,
    replay_fixture_record,
    rewrite_prompt,
)


def run() -> dict:
    state = prompt_state()
    rules = insertion_rules(state)
    outcomes = []
    for rule in rules:
        result = rewrite_prompt(
            state, rules, rule.rule_id, {"s0": "s0"}, {}, source_sha256=graph_digest(state)
        )
        judge_preserved_prompt(state, result.rewrite.state)
        turn = prepared_turn(result.rewrite.state, rewrite=result)
        fixture = {
            "status": "PROPOSE",
            "potentials": {
                "a": "0",
                "b": str(Fraction(3, 2)),
                "c": str(Fraction(3, 2) - Fraction(7, 3)),
            },
        }
        raw = json.dumps(
            {
                **{key: turn.binding[key] for key in ("task_id", "attempt_id", "input_sha256")},
                "answer": fixture,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        checked = turn.check(raw)
        if (
            not checked["schema_valid"]
            or checked["answer"] != fixture
            or checked["evidence_grade"] != "UNVERIFIED"
        ):
            raise RuntimeError("PFP_FIXTURE_CHECK_FAILED")
        outcomes.append(
            {
                "rule_id": rule.rule_id,
                "rule_sha256": result.rule_sha256,
                "before_sha256": result.rewrite.before_digest,
                "after_sha256": result.rewrite.after_digest,
                "fuel_remaining": result.rewrite.fuel_remaining,
                "operation_receipt": operation_receipt(result),
                "terminal": "FIXTURE_VERIFIED",
                "semantic_scope": "exact protected query and source identity",
                "pfp_turn": {
                    "system": turn.prompt.system,
                    "user": turn.prompt.user,
                    "response_schema": turn.prompt.response_schema,
                },
                "binding": turn.binding,
                "raw_reply_base64": base64.b64encode(raw).decode("ascii"),
                "raw_reply_sha256": hashlib.sha256(raw).hexdigest(),
                "checked": checked,
            }
        )
        replayed = replay_fixture_record(state, rules, outcomes[-1])
        if replayed["checked"]["raw_reply_sha256"] != checked["raw_reply_sha256"]:
            raise RuntimeError("PFP_REPLAY_MISMATCH")
    source_paths = [
        Path(__file__),
        Path(__file__).with_name("pilot.py"),
        Path(__file__).parents[4] / "omega_engine_pfp/domain/rewriting/finite_dpo.py",
    ]
    return {
        "pilot": "acset_prompt_rewriting.v001",
        "source_mode": "FIXTURE_ONLY",
        "authority_effect": "None",
        "provider_sends": 0,
        "billing": "NOT_APPLICABLE_NO_PROVIDER_CALLS",
        "scope": "restricted finite attributed graph DPO; no efficacy or prose-equivalence claim",
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths
        },
        "outcomes": outcomes,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=True, sort_keys=True, indent=2))
