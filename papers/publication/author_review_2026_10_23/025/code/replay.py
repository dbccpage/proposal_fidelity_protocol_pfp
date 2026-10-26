import json
from itertools import product

SCOPES = ((0, 1), (1, 2), (2, 0))
EQ = {(0, 0), (1, 1)}
NE = {(0, 1), (1, 0)}

def solutions(relations):
    return {a for a in product((0, 1), repeat=3)
            if all(tuple(a[v] for v in scope) in relation for scope, relation in zip(SCOPES, relations))}

def check_family(rows, relations):
    if len(rows) != 3 or any(row not in relation for row, relation in zip(rows, relations)):
        return None
    values = {}
    for scope, row in zip(SCOPES, rows):
        for v, value in zip(scope, row):
            if v in values and values[v] != value:
                return None
            values[v] = value
    return tuple(values[v] for v in range(3))

def main():
    bad, good = (EQ, EQ, NE), (EQ, EQ, EQ)
    results = {"every_local_relation_nonempty": all(bad),
               "incompatible_cycle_has_no_global_solution": solutions(bad) == set(),
               "submitted_disagreement_refused": check_family(((0, 0), (0, 0), (0, 1)), bad) is None,
               "compatible_family_decoded": check_family(((0, 0),) * 3, good) == (0, 0, 0),
               "two_original_solutions": solutions(good) == {(0, 0, 0), (1, 1, 1)}}
    if not all(results.values()):
        raise ValueError(results)
    print(json.dumps({"status": "PASS", "checks": results, "provider_calls": 0}))

if __name__ == "__main__":
    main()
