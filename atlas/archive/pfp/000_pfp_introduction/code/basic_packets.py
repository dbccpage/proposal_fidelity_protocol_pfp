"""Finite teaching checker; not a Genesis derivation or native host port."""

FIELDS = {"schema", "carrier", "relation_label", "goal", "candidate"}


def check(packet):
    def refused(reason):
        return {"status": "REFUSED", "reason": reason,
                "scope": "symbol-game-basic-packet/v1"}

    if type(packet) is not dict or set(packet) != FIELDS:
        return refused("SCHEMA")
    if packet["schema"] != "symbol-game-basic-packet/v1":
        return refused("SCHEMA")
    carrier = packet["carrier"]
    if (type(carrier) is not list or not carrier
            or any(type(mark) is not str or not mark for mark in carrier)
            or len(set(carrier)) != len(carrier)):
        return refused("CARRIER")
    label = packet["relation_label"]
    if type(label) is not str or not label:
        return refused("RELATION_LABEL")
    goal, candidate = packet["goal"], packet["candidate"]
    if (type(goal) is not list or len(goal) != 2
            or type(candidate) is not list or len(candidate) != 3
            or any(type(value) is not str for value in goal + candidate)):
        return refused("SCHEMA")
    left, relation, right = candidate
    if any(mark not in carrier for mark in goal + [left, right]):
        return refused("OUTSIDE_CARRIER")
    if goal[0] == goal[1] or left == right:
        return refused("SELF_RELATION")
    if relation != label:
        return refused("RELATION_LABEL")
    if [left, right] != goal:
        return refused("GOAL_UNMET")
    return {"status": "CHECKED", "property": "declared-directed-separation",
            "scope": "symbol-game-basic-packet/v1"}


def example(candidate=None):
    return {"schema": "symbol-game-basic-packet/v1", "carrier": ["a", "b"],
            "relation_label": "separates", "goal": ["a", "b"],
            "candidate": ["a", "separates", "b"] if candidate is None else candidate}


def main():
    import json

    cases = [(example(), "CHECKED"),
             (example(["a", "separates", "a"]), "SELF_RELATION"),
             (example(["a", "separates", "c"]), "OUTSIDE_CARRIER"),
             (example(["b", "separates", "a"]), "GOAL_UNMET")]
    passed = True
    for packet, expected in cases:
        receipt = check(packet)
        print(json.dumps(receipt, sort_keys=True))
        passed = passed and receipt.get("reason", receipt["status"]) == expected
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
