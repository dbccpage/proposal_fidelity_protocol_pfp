"""H1: typed turn vs orchestrator-style prose prompt, same 30 tasks. AuthorityEffect: None.

Two arms per task, both carrying the same task text (the P1 `prose` arm: for sums it includes the
trigger sentence) and the same answer contract (P1 sums contract; Hodge v2 contract):

  orchestrator  system: a common multi-agent "worker" persona + the answer contract.
                user: the task prose.
  typed         system: a typed-turn handler + the same answer contract, wrapped in a typed reply.
                user: one `llm_turn_v1` request as JSON. It validates against
                pfp/infrastructure/yaml/schemas/llm_turn_v1.schema.yaml (checked in test_h1.py):
                objective = the task prose, content_sha256/byte_count of it, required_reply_fields
                [CANDIDATE, AUTHORITY_EFFECT], authority_effect None.
                The reply must be {"task_id": <copied>, "CANDIDATE": <answer>, "AUTHORITY_EFFECT": "None"}.

grade.py unwraps the typed reply (any wrapper fault is MALFORMED) and grades CANDIDATE with the
same exact rules as P1. Writes tasks_h1.jsonl (60 calls).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hodge_v2  # noqa: E402

SUM_CONTRACT = ("{\"total\": \"<integer>\"}, where the total is written as a decimal integer string.")
ORCHESTRATOR = (
    "You are SolverAgent, a specialist worker in a multi-agent orchestration pipeline. The Orchestrator "
    "has delegated the task below to you. Read it carefully, reason step by step, double-check your "
    "work, and return only your final answer in the required format.\n\n"
)
TYPED = (
    "You are a typed turn handler. The user message is one llm_turn_v1 request as JSON; its objective "
    "field is the task. Reply with one JSON object only, with no code fence and no other text, with "
    "exactly three fields: task_id, copied from the request; CANDIDATE, the answer object described "
    "below; and AUTHORITY_EFFECT, the string \"None\". Your reply is a proposal; the host checks it.\n\n"
)
SUM_ANSWER_ORCH = "Answer with one JSON object only, with no code fence and no other text: " + SUM_CONTRACT
SUM_ANSWER_TYPED = "The answer object is " + SUM_CONTRACT
HODGE_HEAD = "Answer with one JSON object only, with no code fence and no other text. Fields: "


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def llm_turn(task_id: str, objective: str) -> dict:
    return {
        "schema_version": "core.symbol-game.llm-turn.v1",
        "family": "llm_turn",
        "objective": objective,
        "role": "user",
        "turn_kind": "claimed_result",
        "content_sha256": sha(objective),
        "content_byte_count": len(objective.encode("utf-8")),
        "candidate_budget": 1,
        "operation_budget": 1,
        "required_reply_fields": ["CANDIDATE", "AUTHORITY_EFFECT"],
        "terminal_target": "TypedTurnOrProsePromptRefused",
        "evidence_ceiling": "ReplayableLabEvidence",
        "parent_packet_id": None,
        "conversation_root_id": None,
        "authority_effect": "None",
        "task_id": task_id,
    }


def build(tasks_path: Path = HERE / "tasks.jsonl") -> list[dict]:
    hodge_body = hodge_v2.SYSTEM_V2.removeprefix(HODGE_HEAD)
    rows = []
    for line in tasks_path.read_text(encoding="utf-8").splitlines():
        t = json.loads(line)
        text = t["arms"]["prose"]
        if t["family"] == "S":
            orch_sys, typed_sys = ORCHESTRATOR + SUM_ANSWER_ORCH, TYPED + SUM_ANSWER_TYPED
        else:
            orch_sys = ORCHESTRATOR + hodge_v2.SYSTEM_V2
            typed_sys = TYPED + "The answer object has these fields: " + hodge_body
        turn = json.dumps(llm_turn(t["task_id"], text), sort_keys=True, ensure_ascii=False)
        arms = {"orchestrator": text, "typed": turn}
        row = {k: v for k, v in t.items() if k not in ("arms", "arm_sha256", "system", "system_sha256")}
        row.update(arms=arms, arm_sha256={a: sha(x) for a, x in arms.items()},
                   arm_system={"orchestrator": orch_sys, "typed": typed_sys},
                   arm_system_sha256={"orchestrator": sha(orch_sys), "typed": sha(typed_sys)},
                   system=orch_sys, wrapper={"typed": "typed_reply_v1"}, kit="h1")
        rows.append(row)
    return rows


def main() -> int:
    rows = build()
    body = "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows)
    (HERE / "tasks_h1.jsonl").write_bytes(body.encode("utf-8"))
    print(f"wrote tasks_h1.jsonl: {len(rows)} tasks, {sum(len(r['arms']) for r in rows)} calls, sha256 {sha(body)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
