import json
from fractions import Fraction


def refine(table, labels):
    colors = dict(labels)
    while True:
        signatures = {s: (colors[s], tuple(sorted((a, c, colors[t]) for a, (c, t) in table[s].items()))) for s in table}
        keys = {sig: i for i, sig in enumerate(sorted(set(signatures.values())))}
        new = {s: keys[signatures[s]] for s in table}
        if all((colors[x] == colors[y]) == (new[x] == new[y]) for x in table for y in table):
            return new
        colors = new

def path_cost(table, start, moves, terminals):
    cost = Fraction(0)
    state = start
    for action in moves:
        if action not in table[state]:
            return None
        price, state = table[state][action]
        cost += price
    return cost if state in terminals else None

def minimum_cost(table, start, terminals):
    # Positive cycles can be erased. Enumerate the finite simple paths,
    # independently of the submitted route checked by path_cost.
    if any(price <= 0 for row in table.values() for price, _ in row.values()):
        raise ValueError("positive operation costs required")
    def routes(state, seen):
        if state in terminals:
            yield Fraction(0)
        else:
            for price, target in table[state].values():
                if target not in seen:
                    for tail in routes(target, seen | {target}):
                        yield price + tail
    return min(routes(start, {start}), default=None)

def check_route(table, start, moves, terminals, claimed_cost):
    if type(claimed_cost) is not Fraction:
        return False
    actual = path_cost(table, start, moves, terminals)
    return actual is not None and actual == claimed_cost == minimum_cost(table, start, terminals)

def main():
    table = {"a": {"finish": (Fraction(1), "t")}, "b": {"finish": (Fraction(3), "t")}, "t": {}}
    initial = {"a": 0, "b": 0, "t": 1}
    colors = refine(table, initial)
    routes = {"r": {"direct": (Fraction(5), "t"), "next": (Fraction(1), "s"), "loop": (Fraction(1), "r")},
              "s": {"finish": (Fraction(1), "t")}, "t": {}}
    direct = path_cost(routes, "r", ("direct",), {"t"})
    cheap = path_cost(routes, "r", ("next", "finish"), {"t"})
    loop = path_cost(routes, "r", ("loop", "next", "finish"), {"t"})
    results = {"same_current_report": initial["a"] == initial["b"],
               "future_cost_requires_split": colors["a"] != colors["b"],
               "two_steps_cheaper_than_one": cheap < direct,
               "positive_loop_cannot_improve": loop > cheap,
               "submitted_route_is_independently_optimal": cheap == minimum_cost(routes, "r", {"t"}),
               "submitted_cost_checked": check_route(routes, "r", ("next", "finish"), {"t"}, Fraction(2)),
               "wrong_claimed_cost_refused": not check_route(routes, "r", ("next", "finish"), {"t"}, Fraction(1)),
               "expensive_route_is_not_optimal": not check_route(routes, "r", ("direct",), {"t"}, Fraction(5)),
               "unfinished_route_refused": path_cost(routes, "r", ("next",), {"t"}) is None,
               "unknown_operation_refused": path_cost(routes, "r", ("teleport",), {"t"}) is None,
               "stable_refinement": refine(table, colors) == colors}
    if not all(results.values()):
        raise ValueError(results)
    print(json.dumps({"status": "PASS", "checks": results, "optimal_example_cost": str(cheap), "provider_calls": 0}))

if __name__ == "__main__":
    main()
