"""Versioned C006 task data; host reference witnesses never enter participant facts.

The original public-count inconsistency remains preserved in its frozen source.
Version c006.panels.v2 selects twelve public boards, as approved by the user.
"""
import json
from copy import deepcopy
from hashlib import sha256
from itertools import combinations
from random import Random

from pfp.domain.solvers.simplicial_cochain import CochainCarrier

VERSION = "c006.panels.v2"
ROUND5 = dict(case_id="round5-K4-diagnostic", nodes=["a", "b", "c", "d"],
    edges=[["a", "b"], ["b", "c"], ["c", "a"], ["b", "d"], ["d", "a"], ["c", "d"]],
    claims={"a->b": 1, "b->c": 2, "c->a": 3, "b->d": 1, "d->a": 2, "c->d": 1},
    weights={key: 1 for key in ("a->b", "b->c", "c->a", "b->d", "d->a", "c->d")})


def _graph(rank, variant):
    if rank == 3:
        nodes = list("abcd")
        edges = list(combinations(nodes, 2))
        name = "K4"
    elif rank == 4:
        nodes = list("abcdef")
        edges = [(u, v) for u in nodes[:3] for v in nodes[3:]]
        name = "K3,3"
    elif rank == 5:
        nodes = [f"v{i}" for i in range(8)]
        edges = [(nodes[i], nodes[i ^ (1 << bit)]) for i in range(8) for bit in range(3) if i < i ^ (1 << bit)]
        name = "cube-Q3"
    elif rank == 6 and variant % 2 == 0:
        nodes = list("abcde")
        edges = list(combinations(nodes, 2))
        name = "K5"
    elif rank == 6:
        nodes = [f"v{i}" for i in range(10)]
        edges = [(nodes[i], nodes[(i + 1) % 5]) for i in range(5)]
        edges += [(nodes[i], nodes[i + 5]) for i in range(5)]
        edges += [(nodes[i + 5], nodes[5 + (i + 2) % 5]) for i in range(5)]
        name = "Petersen"
    elif rank in (7, 8):
        nodes = ["hub"] + [f"r{i}" for i in range(rank)]
        edges = [("hub", nodes[i + 1]) for i in range(rank)]
        edges += [(nodes[i + 1], nodes[1 + (i + 1) % rank]) for i in range(rank)]
        name = f"wheel-{rank}-rim"
    else:
        raise ValueError("C006_PANEL_RANK_OUT_OF_SCOPE")
    return nodes, edges, name


def _basis(nodes, edges, rng):
    # A deterministic seeded DFS basis, not the old BFS-star implementation.
    # Every selected tree is validated as an actual spanning tree by the carrier.
    for _ in range(128):
        ordered = list(edges)
        rng.shuffle(ordered)
        adjacency = {node: [] for node in nodes}
        for edge in ordered:
            u, v = edge
            adjacency[u].append((v, edge))
            adjacency[v].append((u, edge))
        seen, tree = {nodes[0]}, []

        def visit(node):
            for neighbor, edge in adjacency[node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    tree.append(edge)
                    visit(neighbor)

        visit(nodes[0])
        carrier = CochainCarrier("C006-panel", tuple(nodes), tuple(edges), ())
        chords = [edge for edge in edges if edge not in tree]
        cycles = carrier.find_fundamental_cycles(tree, chords)
        incidence = {edge: sum(any((u, v) == edge for u, v, _ in cycle) for cycle in cycles) for edge in tree}
        if len(seen) == len(nodes) and max(incidence.values()) >= 3:
            return tree, chords, cycles
    raise ValueError("C006_SHARED_TREE_EDGE_NOT_FOUND")


def generate_board(rank, *, seed, variant=0, control=None):
    if type(seed) is not int or type(variant) is not int:
        raise ValueError("C006_EXACT_SEED_REQUIRED")
    if control not in (None, "closed_cycle", "correct_zero_chord"):
        raise ValueError("C006_UNKNOWN_CONTROL")
    rng = Random(seed)
    nodes, edges, family = _graph(rank, variant)
    tree, chords, _ = _basis(nodes, edges, rng)
    potential = {node: rng.randrange(-17, 18) for node in nodes}
    if control == "correct_zero_chord":
        potential[chords[0][1]] = potential[chords[0][0]]
    claims = {f"{u}->{v}": potential[v] - potential[u] for u, v in edges}
    for i, (u, v) in enumerate(chords):
        if i != 0 or control not in ("closed_cycle", "correct_zero_chord"):
            claims[f"{u}->{v}"] += rng.choice((-1, 1)) * rng.randrange(1, 10)
    board = dict(case_id=f"C006-v2-r{rank}-s{seed}", nodes=nodes, edges=list(map(list, edges)),
        claims=claims, weights={key: 1 for key in claims}, spanning_tree=list(map(list, tree)))
    return dict(board=board, metadata=dict(protocol_version=VERSION, seed=seed, cycle_rank=rank,
        graph_family=family, control=control, reference_role="HOST_ONLY_DETERMINISTIC_FIXTURE"),
        reference_potential={node: str(value) for node, value in potential.items()})


def relabel_board(row, *, seed):
    rng = Random(seed)
    result = deepcopy(row)
    board = result["board"]
    labels = [f"node_{seed}_{i}" for i in range(len(board["nodes"]))]
    rng.shuffle(labels)
    mapping = dict(zip(board["nodes"], labels))
    orientation = {tuple(edge): rng.choice((-1, 1)) for edge in board["edges"]}
    converted, claims, weights = {}, {}, {}
    for (u, v), sign in orientation.items():
        a, b = (mapping[u], mapping[v]) if sign == 1 else (mapping[v], mapping[u])
        converted[(u, v)] = [a, b]
        claims[f"{a}->{b}"] = sign * board["claims"][f"{u}->{v}"]
        weights[f"{a}->{b}"] = board["weights"][f"{u}->{v}"]
    board.update(case_id=board["case_id"] + f"-relabel-{seed}", nodes=list(mapping.values()),
        edges=list(converted.values()), claims=claims, weights=weights,
        spanning_tree=[converted[tuple(edge)] for edge in board["spanning_tree"]])
    result["reference_potential"] = {mapping[node]: value for node, value in result["reference_potential"].items()}
    result["metadata"].update(control="relabel_orientation", relabel_seed=seed,
        original_case_id=row["board"]["case_id"])
    return result


def build_panels(*, version):
    if version != VERSION:
        raise ValueError("C006_EXPLICIT_PANEL_VERSION_REQUIRED")
    public = [generate_board(rank, seed=6000 + rank * 10 + i, variant=i)
        for rank in range(3, 8) for i in range(4 if rank == 7 else 2)]
    hidden = [generate_board(rank, seed=16000 + rank * 100 + i, variant=i,
        control="closed_cycle" if i == 1 else "correct_zero_chord" if i == 2 else None)
        for rank in range(3, 9) for i in range(10)]
    # Verbatim historical diagnostic is additional to the all-nonzero family rule.
    hidden[0] = dict(board=deepcopy(ROUND5), metadata=dict(protocol_version=VERSION,
        cycle_rank=3, graph_family="K4", control="round5-verbatim", seed=None))
    relabel = [relabel_board(hidden[i], seed=26000 + i) for i in range(1, 21)]
    poison = []
    for i in range(12):
        row = generate_board(3 + i % 6, seed=36000 + i, variant=i,
            control="correct_zero_chord" if i >= 6 else None)
        board, potential = row["board"], row["reference_potential"]
        current = {f"{u}->{v}": int(potential[v]) - int(potential[u]) for u, v in board["edges"]}
        proposed = deepcopy(board["claims"])
        if i >= 6:
            proposed = deepcopy(current)
            tree = set(map(tuple, board["spanning_tree"]))
            u, v = next(tuple(edge) for edge in board["edges"] if tuple(edge) not in tree)
            assert current[f"{u}->{v}"] == 0
            proposed[f"{u}->{v}"] = 1
        poison.append(dict(kind="stale_cut_history" if i < 6 else "zero_chord_edit",
            board=board, current_claims=current, proposed_claims=proposed,
            old_history="A prior CUT_ADMITTED label cannot admit this candidate on the current cochain.",
            expected="NO_STRICT_DESCENT", stale_history_is_authority=False))
    body = dict(schema=VERSION, public=public, hidden=hidden, relabel=relabel, poison=poison,
        selection="USER_APPROVED_12_PUBLIC_2_EACH_RANK_3_TO_6_4_AT_RANK_7",
        provider_calls=0, observation="TASK_DATA_NOT_MODEL_TRIALS")
    body["sha256"] = sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return body


def generate_compaction_schedule(*, seed, turns=36, typo=False):
    """Six source-bound fragments; only the host retains the union witness."""
    if type(seed) is not int or type(turns) is not int or not 30 <= turns <= 48:
        raise ValueError("C007_EXACT_SEED_AND_TURN_BOUND_REQUIRED")
    rng = Random(seed)
    nodes = [f"n{i}" for i in range(6)]
    potential = {node: rng.randrange(-50, 51) for node in nodes}
    declarations = []
    for i in range(5):
        u, v = nodes[i:i + 2]
        declarations.append(dict(id=f"s1:tree:{i}", u=u, v=v,
            claim=potential[v] - potential[u], repairable=False))
    for i, (u, v) in enumerate((("n0", "n3"), ("n1", "n4"), ("n2", "n5"))):
        declarations.append(dict(id=f"s1:chord:{i}", u=u, v=v,
            claim=potential[v] - potential[u] + rng.choice((-7, 3, 9)), repairable=True))
    events = [dict(kind="continue") for _ in range(turns)]
    events[0] = dict(kind="release", stage=1, constraints=declarations)
    for stage in range(2, 7):
        old = nodes[rng.randrange(len(nodes))]
        a, b = f"s{stage}:a", f"s{stage}:b"
        potential[a], potential[b] = rng.randrange(-50, 51), rng.randrange(-50, 51)
        fragment = [dict(id=f"s{stage}:tree:0", u=old, v=a, claim=potential[a] - potential[old], repairable=False),
            dict(id=f"s{stage}:tree:1", u=a, v=b, claim=potential[b] - potential[a], repairable=False),
            dict(id=f"s{stage}:chord", u=nodes[0], v=b,
                claim=potential[b] - potential[nodes[0]] + rng.choice((-5, 4, 8)), repairable=True)]
        events[(stage - 1) * (turns // 6)] = dict(kind="release", stage=stage, constraints=fragment)
        nodes.extend((a, b))
    positions = [i for i in range(1, turns - 1) if events[i]["kind"] == "continue"]
    rng.shuffle(positions)
    for i in positions[:8]:
        events[i] = dict(kind="status", restatements=[deepcopy(declarations[0])])
    if typo:
        events[positions[3]]["restatements"][0]["claim"] += 1
    return dict(schedule=events, reference_potential={node: str(value) for node, value in potential.items()},
        metadata=dict(schema="c007.panels.v1", seed=seed, turns=turns, control="typo" if typo else None,
            reference_role="HOST_ONLY_DETERMINISTIC_FIXTURE"))


def build_compaction_panels(*, version):
    if version != "c007.panels.v1":
        raise ValueError("C007_EXPLICIT_PANEL_VERSION_REQUIRED")
    hidden = [generate_compaction_schedule(seed=47000 + i, turns=30 + i % 19) for i in range(40)]
    relabel = []
    for i, row in enumerate(hidden[:12]):
        transformed = deepcopy(row)
        labels = {node: f"renamed_{i}_{j}" for j, node in enumerate(row["reference_potential"])}
        for event in transformed["schedule"]:
            for record in event.get("constraints", event.get("restatements", [])):
                record["u"], record["v"] = labels[record["u"]], labels[record["v"]]
        transformed["reference_potential"] = {labels[node]: value for node, value in row["reference_potential"].items()}
        transformed["metadata"].update(control="relabel", original_seed=row["metadata"]["seed"])
        relabel.append(transformed)
    poison = [generate_compaction_schedule(seed=57000 + i, turns=36, typo=True) for i in range(10)]
    for i in range(6):
        row = generate_compaction_schedule(seed=67000 + i, turns=36)
        # An existing vertex relation arrives late and closes an earlier cycle.
        # Its locked value is consistent with the original tree; a model must
        # retain it in final verification instead of accepting an early union.
        p = row["reference_potential"]
        late = dict(id="s6:late-earlier", u="n0", v="n5", claim=int(p["n5"]) - int(p["n0"]), repairable=False)
        row["schedule"][30]["constraints"].append(late)
        row["metadata"]["control"] = "late_relation_on_earlier_vertices"
        poison.append(row)
    return dict(schema=version, hidden=hidden, relabel=relabel, poison=poison,
        provider_calls=0, observation="TASK_DATA_NOT_MODEL_TRIALS")
