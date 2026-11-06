"""Original exact potential-propagation checker; unused phi1 stays in Git history."""

from fractions import Fraction


def host_verdict(instance) -> str:
    """CONTRADICTION iff no global potential exists (Phi_1 > 0), else CONSISTENT."""
    adjacency = {item: [] for item in instance.items}
    if len(adjacency) != len(instance.items):
        raise ValueError("carrier items must be distinct")
    edge_keys = {(u, v) for u, v, _weight in instance.edges}
    if set(instance.claims) != edge_keys:
        raise ValueError("claims must match the declared edges")
    for u, v, weight in instance.edges:
        if u not in adjacency or v not in adjacency or weight <= 0:
            raise ValueError("edges require declared endpoints and positive weights")
        delta = Fraction(instance.claims[(u, v)])
        adjacency[u].append((v, delta))
        adjacency[v].append((u, -delta))

    potentials = {}
    for root in instance.items:
        if root in potentials:
            continue
        potentials[root] = Fraction(0)
        pending = [root]
        while pending:
            u = pending.pop()
            for v, delta in adjacency[u]:
                expected = potentials[u] + delta
                if v not in potentials:
                    potentials[v] = expected
                    pending.append(v)
                elif potentials[v] != expected:
                    return "CONTRADICTION"
    return "CONSISTENT"
