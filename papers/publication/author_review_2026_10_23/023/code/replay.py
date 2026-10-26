import json
from itertools import product

TASK = "binary-sum-one/v1"
SOLUTIONS = {p for p in product((0, 1), repeat=2) if sum(p) == 1}

def check(task, witness, required):
    if task != TASK or not isinstance(witness, tuple) or len(witness) != 2:
        return False
    if any(type(x) is not int or x not in (0, 1) for x in witness):
        return False
    if type(required) is not tuple or "equation" not in required:
        return False
    claims = {"equation": sum(witness) == 1,
              "all_solutions_x_one": all(x == 1 for x, _ in SOLUTIONS),
              "source_quote": False}
    return all(j in claims and claims[j] for j in required)

def main():
    results = {"valid_witness": check(TASK, (1, 0), ("equation",)),
               "wrong_witness_refused": not check(TASK, (0, 0), ("equation",)),
               "wrong_task_refused": not check("another-task", (1, 0), ("equation",)),
               "false_prose_claim_refused": not check(TASK, (1, 0), ("equation", "all_solutions_x_one")),
               "unbound_quote_refused": not check(TASK, (1, 0), ("equation", "source_quote")),
               "mandatory_task_claim_retained": not check(TASK, (0, 0), ())}
    if not all(results.values()):
        raise ValueError(results)
    print(json.dumps({"status": "PASS", "checks": results, "provider_calls": 0}))

if __name__ == "__main__":
    main()
