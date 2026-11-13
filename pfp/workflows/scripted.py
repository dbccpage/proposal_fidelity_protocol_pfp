"""Public finite task shared by the scripted WF4 and WF5 runs; no expected answer.

AuthorityEffect: None.
"""

SPEC = {
    "answer_schema": {
        "additionalProperties": False,
        "properties": {"total": {"type": "integer"}},
        "required": ["total"],
        "type": "object",
    },
    "checker": "integer_sum_v1",
    "input": {"values": [17, 25, -4]},
    "seed_prompt": "Calculate the exact sum of 17, 25, and -4.",
    "task_id": "common-integer-sum-seed-v1",
}
