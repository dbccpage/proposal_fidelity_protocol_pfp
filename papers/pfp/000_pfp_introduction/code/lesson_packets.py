"""Typed prompt/answer/return-packet teaching examples, entirely local.

The natural-language prompt is retained as text, never executed or trusted as
a checking rule. These finite contracts are not native runtime wire schemas.
"""
import hashlib
import json
from copy import deepcopy

from basic_packets import check, example

SCHEMA = "symbol-game-lesson-prompt/v1"
TYPES = {
    "ground_count": ("presentation_and_carrier", "counts"),
    "profile_distinction": ("finite_observation_table", "observation_index"),
    "directed_relation": ("basic_relation_board", "relation_triple"),
}


def identity(value):
    """A sorted-key JSON teaching identity, not an RFC 8785 claim."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def problem(task_type, text, inputs):
    input_type, answer_type = TYPES[task_type]
    return {"schema": SCHEMA, "packet_type": "problem_prompt", "prompt": {
        "text": text, "task_type": task_type, "input_type": input_type,
        "input": deepcopy(inputs), "answer_type": answer_type}}


def proposal(prompt_packet, value, *, answer_type=None):
    return {"packet_type": "candidate", "problem_id": identity(prompt_packet),
            "answer_type": prompt_packet["prompt"]["answer_type"] if answer_type is None else answer_type,
            "value": deepcopy(value)}


def evaluate(prompt_packet, candidate):
    """Return a bound result with a typed reason; never mutate inputs."""
    def returned(status, reason, checked_value=None):
        return {"schema": "symbol-game-lesson-return/v1", "packet_type": "checked_result",
                "problem": deepcopy(prompt_packet), "candidate": deepcopy(candidate),
                "receipt": {"status": status, "reason": reason,
                            "scope": "finite-teaching-contract-only", "checked_value": checked_value}}

    if (type(prompt_packet) is not dict or set(prompt_packet) != {"schema", "packet_type", "prompt"}
            or prompt_packet["schema"] != SCHEMA or prompt_packet["packet_type"] != "problem_prompt"):
        return returned("REFUSED", "PROMPT_SCHEMA")
    p = prompt_packet["prompt"]
    if (type(p) is not dict or set(p) != {"text", "task_type", "input_type", "input", "answer_type"}
            or type(p["text"]) is not str or not p["text"].strip()
            or type(p["task_type"]) is not str or p["task_type"] not in TYPES):
        return returned("REFUSED", "PROMPT_SCHEMA")
    expected_input, expected_answer = TYPES[p["task_type"]]
    if p["input_type"] != expected_input or p["answer_type"] != expected_answer:
        return returned("REFUSED", "PROMPT_TYPE")
    if (type(candidate) is not dict or set(candidate) != {"packet_type", "problem_id", "answer_type", "value"}
            or candidate["packet_type"] != "candidate"):
        return returned("REFUSED", "CANDIDATE_SCHEMA")
    try:
        problem_id = identity(prompt_packet)
    except (TypeError, ValueError):
        return returned("REFUSED", "PROMPT_SCHEMA")
    if candidate["problem_id"] != problem_id:
        return returned("REFUSED", "PROBLEM_BINDING")
    if candidate["answer_type"] != expected_answer:
        return returned("REFUSED", "ANSWER_TYPE")
    data, value = p["input"], candidate["value"]
    if p["task_type"] == "ground_count":
        if data != {"presentation": ["<>"], "carrier": []}:
            return returned("REFUSED", "GROUND_INPUT")
        if (type(value) is not dict or set(value) != {"presentation_count", "carrier_count"}
                or any(type(v) is not int for v in value.values())):
            return returned("REFUSED", "ANSWER_TYPE")
        counts = {"presentation_count": 1, "carrier_count": 0}
        if value != counts:
            return returned("REFUSED", "COUNT_MISMATCH")
        return returned("CHECKED", "EXACT_COUNTS", deepcopy(counts))
    if p["task_type"] == "profile_distinction":
        if (type(data) is not dict or set(data) != {"carrier", "observations"}
                or data["carrier"] != ["a", "b"] or type(data["observations"]) is not list
                or any(type(row) is not list or len(row) != 2
                       or any(type(v) is not str for v in row) for row in data["observations"])):
            return returned("REFUSED", "OBSERVATION_TABLE")
        if type(value) is not int:
            return returned("REFUSED", "ANSWER_TYPE")
        separators = [i for i, row in enumerate(data["observations"]) if row[0] != row[1]]
        if not separators:
            return returned("BLOCKED", "NO_DECLARED_SEPARATOR")
        if value not in separators:
            return returned("REFUSED", "NOT_A_SEPARATOR")
        return returned("CHECKED", "DECLARED_OBSERVATION_SEPARATES", value)
    if type(data) is not dict or set(data) != {"carrier", "relation_label", "goal"}:
        return returned("REFUSED", "RELATION_BOARD")
    packet = {"schema": "symbol-game-basic-packet/v1", **deepcopy(data), "candidate": value}
    receipt = check(packet)
    return returned(receipt["status"], receipt.get("reason", "DECLARED_GOAL_MET"),
                    deepcopy(value) if receipt["status"] == "CHECKED" else None)


def bounded_session(prompt_packet, values, fuel):
    if type(fuel) is not int or fuel < 0:
        raise ValueError("Fuel must be a nonnegative integer")
    returns = []
    iterator = iter(values)
    for _ in range(fuel):
        try:
            value = next(iterator)
        except StopIteration:
            break
        result = evaluate(prompt_packet, proposal(prompt_packet, value))
        returns.append(result)
        if result["receipt"]["status"] == "CHECKED":
            return {"status": "CHECKED", "attempts": len(returns), "returns": returns}
    return {"status": "UNKNOWN", "attempts": len(returns), "returns": returns}


def replay_return(result):
    """Check the result against the retained problem and candidate, not its label."""
    if (type(result) is not dict
            or set(result) != {"schema", "packet_type", "problem", "candidate", "receipt"}
            or type(result.get("receipt")) is not dict
            or set(result["receipt"]) != {"status", "reason", "scope", "checked_value"}
            or type(result["receipt"]["status"]) is not str
            or type(result["receipt"]["reason"]) is not str
            or type(result["receipt"]["scope"]) is not str):
        return False
    try:
        expected = evaluate(result["problem"], result["candidate"])
        return (expected == result
                and identity(expected) == identity(result)
                and type(result["receipt"]["checked_value"]) is type(expected["receipt"]["checked_value"]))
    except (TypeError, ValueError):
        return False


def rename_edges(carrier, edges, mapping):
    if (set(mapping) != set(carrier) or len(set(mapping.values())) != len(carrier)
            or any(type(v) is not str or not v for v in mapping.values())
            or any(u not in mapping or v not in mapping or u == v for u, v in edges)):
        raise ValueError("A bijective rename on a declared loopless carrier is required")
    return [mapping[v] for v in carrier], [(mapping[u], mapping[v]) for u, v in edges]


def examples():
    ground = problem("ground_count", "Count presentations and admitted marks separately.",
                     {"presentation": ["<>"], "carrier": []})
    collapsed = problem("profile_distinction", "Name a declared observation that separates a and b.",
                        {"carrier": ["a", "b"], "observations": [["same", "same"]]})
    distinguished = problem("profile_distinction", "Name a declared observation that separates a and b.",
                            {"carrier": ["a", "b"], "observations": [["same", "same"], ["left", "right"]]})
    relation = problem("directed_relation", "Supply a relation triple for the declared directed goal.",
                       {k: v for k, v in example().items() if k in {"carrier", "relation_label", "goal"}})
    return ground, collapsed, distinguished, relation


def main():
    ground, collapsed, distinguished, relation = examples()
    cases = [(ground, {"presentation_count": 1, "carrier_count": 0}, "CHECKED"),
             (ground, {"presentation_count": 1, "carrier_count": 1}, "REFUSED"),
             (collapsed, 0, "BLOCKED"), (distinguished, 1, "CHECKED"),
             (relation, ["a", "separates", "b"], "CHECKED"),
             (relation, ["a", "separates", "a"], "REFUSED")]
    passed = True
    for packet, value, expected in cases:
        receipt = evaluate(packet, proposal(packet, value))["receipt"]
        print(json.dumps(receipt, sort_keys=True))
        passed = passed and receipt["status"] == expected
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
