import json


def check_step(parent, child):
    # This example uses the exact nonnegative integer, unit-cost profile.
    if any(type(packet[key]) is not int or packet[key] < 0
           for packet in (parent, child) for key in ("used", "budget")):
        return False
    if type(child["cost"]) is not int:
        return False
    return (child["task"] == parent["task"] and child["parent"] == parent["receipt"]
            and child["checker"] == parent["checker"]
            and child["budget"] == parent["budget"]
            and child["used"] == parent["used"] + child["cost"]
            and child["cost"] > 0 and child["used"] <= parent["budget"])

def main():
    parent = {"task": "p0", "receipt": "r0", "checker": "c0", "used": 0, "budget": 2}
    first = {"task": "p0", "receipt": "r1", "parent": "r0", "checker": "c0", "used": 1, "cost": 1, "budget": 2}
    second = {**first, "receipt": "r2", "parent": "r1", "used": 2}
    source, target = {0}, {1}
    rejects = lambda w: w == 1
    results = {"two_charged_steps": check_step(parent, first) and check_step(first, second),
               "changed_task_refused": not check_step(first, {**second, "task": "p1"}),
               "stale_parent_refused": not check_step(first, {**second, "parent": "r0"}),
               "fuel_reset_refused": not check_step(first, {**second, "used": 0}),
               "budget_reset_refused": not check_step(first, {**second, "budget": 200}),
               "changed_checker_refused": not check_step(first, {**second, "checker": "c1"}),
               "boolean_cost_refused": not check_step(parent, {**first, "cost": True}),
               "negative_prior_fuel_refused": not check_step({**parent, "used": -1}, {**first, "used": 0}),
               "source_antibody_sound": all(not rejects(w) for w in source),
               "target_antibody_unsound": any(rejects(w) for w in target),
               "empty_target_loses_coverage": bool(source) and not set()}
    if not all(results.values()):
        raise ValueError(results)
    print(json.dumps({"status": "PASS", "checks": results, "provider_calls": 0}))

if __name__ == "__main__":
    main()
