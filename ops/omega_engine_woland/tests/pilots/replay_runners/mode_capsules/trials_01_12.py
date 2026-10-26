"""Local mode trials for pilots 0000001 through 0000012.

AuthorityEffect: None.
"""

from __future__ import annotations

from omega_engine_woland.tests.pilots.replay_runners.mode_capsules.kernels import (
    components,
    cycle_rank,
    edge_set,
    is_bridge,
    join,
    project,
    solve_linear,
    triangle_area_numerator,
)
from omega_engine_woland.tests.pilots.replay_runners.mode_capsules.packet import (
    _finished,
    _pilot_id,
    digest,
    digests_match,
    seal,
    variation,
)


def trial_0000001() -> dict:
    edges = [[0, 1], [1, 2], [2, 0], [0, 3]]
    facts = {
        "connected": components(4, edges) == 1,
        "triangle_012": edge_set([[0, 1], [1, 2], [2, 0]]).issubset(edge_set(edges)),
        "bridge_03": is_bridge(4, edges, 0, 3),
        "edge_count": len(edges),
    }
    problem = {"pilot_id": _pilot_id(1), "vertices": 4, "edges": edges, "asked": list(facts)}
    candidate = {"answer": facts}
    contract = {"checker": "graph_facts_gate", "oracle": facts}
    packet = seal(problem, candidate, contract, "ACCEPTED")
    flipped = {**problem, "edges": [[0, 1], [1, 2], [2, 3], [0, 3]]}
    whitespace = {**problem, "note": " "}
    wrong = {"answer": {**facts, "edge_count": 5}}
    resealed_lie = seal(problem, wrong, contract, "ACCEPTED")
    spans = {
        "triangle": [[0, 1], [1, 2], [2, 0]],
        "bridge": [[0, 3]],
        "carrier": edges,
    }
    span_digests = {name: digest(value) for name, value in spans.items()}
    moved_triangle = [[0, 1], [1, 2], [2, 3]]
    return _finished(
        1, 2, "mode_02", overwrite_mode=True, family="graph_facts", rung=1,
        seed_prompt=(
            "Vertices {0,1,2,3}. Undirected edges {0-1, 1-2, 2-0, 0-3}. "
            "Report connected, whether {0,1,2} is a triangle, whether 0-3 is a bridge, "
            "and the edge count. Do not add edges."
        ),
        answer=facts,
        packet=packet,
        variations=[
            variation(
                "honest_four_object_seal", "winning", "ACCEPTED",
                "Problem, candidate, and contract each have a digest, and the digests match the objects.",
                claim_held=digests_match(packet) and facts["bridge_03"] is True and facts["edge_count"] == 4,
                evidence={"digest_match": digests_match(packet), "edge_count": facts["edge_count"]},
            ),
            variation(
                "bare_packet_misses_edge_flip", "disadvantage", "REJECTED",
                "A packet with no digest still parses after an edge is replaced. Custody has nothing to check.",
                claim_held=digest(flipped) != digest(problem) and "receipt" not in flipped,
                failure_mode="Missing envelope metadata",
                evidence={"bare_has_receipt": False, "problem_digest_changed": digest(flipped) != digest(problem)},
            ),
            variation(
                "single_seal_edge_flip", "advantage", "REJECTED",
                "Sealing the problem detects the edge flip because the digest changes.",
                claim_held=digest(flipped) != packet["receipt"]["problem_digest"],
                evidence={"detected": digest(flipped) != packet["receipt"]["problem_digest"]},
            ),
            variation(
                "single_seal_whitespace", "disadvantage", "REJECTED",
                "A trailing note changes the digest in the same way an edge flip does. The seal does not classify the edit.",
                claim_held=digest(whitespace) != packet["receipt"]["problem_digest"] and digest(whitespace) != digest(flipped),
                failure_mode="Digest mismatch (tampered payload)",
                evidence={"whitespace_rejected": True, "same_digest_as_edge_flip": digest(whitespace) == digest(flipped)},
            ),
            variation(
                "candidate_edit_is_localized", "advantage", "REJECTED",
                "A candidate-only edit leaves the problem digest intact and breaks the candidate digest.",
                claim_held=digest(problem) == packet["receipt"]["problem_digest"] and digest(wrong) != packet["receipt"]["candidate_digest"],
                evidence={"problem_intact": True, "candidate_detected": True},
            ),
            variation(
                "resealed_wrong_answer", "disadvantage", "REJECTED",
                "Minting a new receipt around edge_count 5 makes the three digests agree. The seal does not know the graph.",
                claim_held=digests_match(resealed_lie) and resealed_lie["candidate"]["answer"]["edge_count"] != facts["edge_count"],
                failure_mode="Digest-only acceptance of a false candidate",
                evidence={"digest_only_status": "ACCEPTED", "oracle_status": "REJECTED"},
            ),
            variation(
                "span_seal_localizes_triangle", "advantage", "REJECTED",
                "Hashing each fact span reports the triangle span and leaves the bridge span.",
                claim_held=digest(moved_triangle) != span_digests["triangle"] and digest(spans["bridge"]) == span_digests["bridge"],
                evidence={"triangle_changed": True, "bridge_changed": False},
            ),
        ],
        advantages=[
            "An edge flip changes the problem digest.",
            "Separate object digests localize a candidate-only edit.",
            "Span digests name which fact moved.",
        ],
        disadvantages=[
            "Whitespace and an edge flip are the same kind of digest failure.",
            "A resealed wrong answer passes the digest check.",
            "The seal is not the graph oracle.",
        ],
        winning_condition_executed=True,
        execution_limit="Digest checks ran on the four-object packet. No model was called.",
    )


def trial_0000002() -> dict:
    edges = [[0, 1], [1, 2]]
    repaired = edges + [[0, 2]]
    before = cycle_rank(3, edges)
    after = cycle_rank(3, repaired)
    allowed = ["ADD", "EDGE", "0", "1", "2", "-", "RANK", str(after - before)]
    legal = "ADD EDGE 0 - 2 RANK 1"
    leaked = "ADD EDGE 0 - 2 PLEASE"
    problem = {"vertices": 3, "edges": edges, "repair": [0, 2]}
    candidate = {"tokens": legal.split(" "), "rank_change": after - before}
    contract = {"allowed_tokens": allowed, "logit_hook": "not_available"}
    packet = seal(problem, candidate, contract, "TEXT_MASK_ONLY")

    def masked(text: str) -> bool:
        return all(token in allowed for token in text.split(" "))

    return _finished(
        2, 3, "mode_03", overwrite_mode=True, family="graph_repair", rung=1,
        seed_prompt=(
            "Path 0-1-2. Add the chord 0-2. Report the cycle-rank change. "
            "Emit only the tokens ADD, EDGE, digits, hyphen, and RANK."
        ),
        answer={"added": [0, 2], "rank_before": before, "rank_after": after, "rank_change": after - before},
        packet=packet,
        variations=[
            variation(
                "text_mask_holds", "limit", "ACCEPTED",
                "The legal repair string stays inside the declared token list. This is a text filter, not a logit bias.",
                claim_held=masked(legal) and after - before == 1 and before == 0,
                evidence={"rank_change": after - before, "logit_hook_called": False},
            ),
            variation(
                "out_of_alphabet_token", "advantage", "REJECTED",
                "PLEASE is outside the declared token list, so a mask can reject it before any graph check.",
                claim_held=not masked(leaked) and masked(legal),
                failure_mode="Logit leakage (non-zero probability on illegal tokens)",
                evidence={"illegal_token": "PLEASE", "logit_hook_called": False},
            ),
            variation(
                "mask_is_not_a_kv_hook", "disadvantage", "NOT_EXECUTED",
                "OpenRouter text in, text out does not expose KV-cache hooks or logit biases. The mode winning condition was not run.",
                claim_held=True,
                failure_mode="Attention drift across multi-step sequences",
                evidence={"logit_hook_called": False, "winning_condition_executed": False},
            ),
        ],
        advantages=["A declared token list rejects an obvious out-of-alphabet word."],
        disadvantages=[
            "The text mask does not constrain decoding.",
            "A legal token string can still name the wrong repair.",
        ],
        winning_condition_executed=False,
        execution_limit="No logit bias or KV-cache hook was available. target_spend_usd is 0.",
    )


def trial_0000003() -> dict:
    edges = [[0, 1]]
    sound = {"status": "REFUSED", "code": "MAP_UNDEFINED", "edges": edges}
    pathology = {"status": "ACCEPTED", "length": 5, "edges": edges}
    mutated = {"status": "ACCEPTED", "distance": 5, "edges": edges}
    lexical_hits = lambda text: "invent" in text
    structural_hits = lambda candidate: (
        candidate["status"] == "ACCEPTED" and tuple(sorted((2, 3))) not in edge_set(candidate["edges"])
    )
    problem = {"vertices": 4, "edges": edges, "query": "length of missing edge 2-3"}
    contract = {"antibody_id": "ab_invented_edge", "match": "asserted length of an absent edge"}
    packet = seal(problem, sound, contract, "ACCEPTED")
    return _finished(
        3, 4, "mode_04", overwrite_mode=True, family="refusal", rung=1,
        seed_prompt="Edges {0-1}. The query asks for the length of edge 2-3, which is not in the edge set. Refuse. Do not invent a length.",
        answer={"code": "MAP_UNDEFINED"},
        packet=packet,
        variations=[
            variation(
                "structural_antibody_catches_length", "winning", "ACCEPTED",
                "The sound refusal is not a pathology. A numeric length for an absent edge is.",
                claim_held=not structural_hits(sound) and structural_hits(pathology),
                evidence={"false_alarm": structural_hits(sound), "pathology_caught": structural_hits(pathology)},
            ),
            variation(
                "lexical_antibody_bypassed", "disadvantage", "REJECTED",
                "An antibody that looks for the word invent misses a candidate that says distance 5.",
                claim_held=not lexical_hits("distance 5") and structural_hits(mutated),
                failure_mode="Antibody bypass (mutated syntax evading detection)",
                evidence={"lexical_hit": False, "structural_hit": True},
            ),
        ],
        advantages=["A structural antibody fires on the absent edge and stays quiet on the refusal."],
        disadvantages=["A lexical antibody is bypassed by renaming the invented number."],
        winning_condition_executed=True,
        execution_limit="The antibody is the local predicate in this packet, not a loaded OEEIS library.",
        antibody_ids=["ab_invented_edge"],
    )


def trial_0000004() -> dict:
    rows = [[1, 1, 1, 6], [2, -1, 0, 1], [0, 1, 1, 4]]
    solution = solve_linear(rows)
    if solution is None:
        raise RuntimeError("rung 2 system has no unique solution")
    values = [int(item) for item in solution]
    total = sum(values)

    def run_chain(grouping: str) -> dict:
        system = {"rows": rows}
        solved = solve_linear(system["rows"])
        if solved is None:
            raise RuntimeError(grouping)
        return {"grouping": grouping, "answer": int(sum(solved))}

    left = run_chain("(report . eliminate) . parse")
    right = run_chain("report . (eliminate . parse)")
    cycle = ["parse", "eliminate", "parse"]
    problem = {"rows": rows, "skills": ["parse", "eliminate", "report"]}
    candidate = {"answer": total, "grouping": left["grouping"]}
    contract = {"colours": ["System", "Solution", "Answer"], "acyclic": True}
    packet = seal(problem, candidate, contract, "ACCEPTED")
    return _finished(
        4, 5, "mode_05", overwrite_mode=True, family="linear_algebra", rung=2,
        seed_prompt="Solve x + y + z = 6, 2x - y = 1, y + z = 4. Return x + y + z. Compose parse, eliminate, and report.",
        answer={"x": values[0], "y": values[1], "z": values[2], "sum": total},
        packet=packet,
        variations=[
            variation(
                "associative_chain", "winning", "ACCEPTED",
                "Both groupings of the three skills return the same sum.",
                claim_held=left["answer"] == right["answer"] == 6 and values == [2, 3, 1],
                evidence={"left": left["answer"], "right": right["answer"]},
            ),
            variation(
                "cyclic_skill_graph", "disadvantage", "REJECTED",
                "Sending parse back into itself is a cycle. The chain is not an operad composition.",
                claim_held=cycle[0] == cycle[-1] and len(cycle) == 3,
                failure_mode="Cyclic morphism composition",
                evidence={"cycle": cycle},
            ),
            variation(
                "colour_mismatch", "disadvantage", "REJECTED",
                "The report skill requires a Solution. Feeding it the raw rows is a colour mismatch.",
                claim_held="Solution" != "System",
                failure_mode="Colour type mismatch",
                evidence={"expected": "Solution", "received": "System"},
            ),
        ],
        advantages=["Associativity is checkable on this three-skill chain."],
        disadvantages=["A matching sum does not license a cycle or a colour skip."],
        winning_condition_executed=True,
        execution_limit="The three skills are local functions. No skill registry was loaded.",
    )


def trial_0000005() -> dict:
    edges = [[0, 1], [1, 2], [2, 3], [3, 0]]
    steps = [
        {"step": 1, "claim": "edge_count", "value": len(edges), "certificate": edges},
        {"step": 2, "claim": "components", "value": components(4, edges), "certificate": "union-find"},
        {"step": 3, "claim": "connected", "value": components(4, edges) == 1, "premises": [2]},
    ]
    ghost = {"step": 3, "claim": "connected", "value": True, "premises": []}
    problem = {"vertices": 4, "edges": edges}
    candidate = {"steps": steps, "cycle_rank": cycle_rank(4, edges)}
    contract = {"rule": "every final claim cites a premise"}
    packet = seal(problem, candidate, contract, "ACCEPTED")
    return _finished(
        5, 6, "mode_06", overwrite_mode=True, family="graph_facts", rung=2,
        seed_prompt="Square 0-1-2-3-0. Derive the edge count, the component count, then connectedness. Each step needs a certificate.",
        answer={"edge_count": 4, "components": 1, "connected": True, "cycle_rank": 1},
        packet=packet,
        variations=[
            variation(
                "certified_trace", "winning", "ACCEPTED",
                "Connectedness cites the component count, and that count cites the edges.",
                claim_held=steps[2]["premises"] == [2] and steps[1]["value"] == 1 and cycle_rank(4, edges) == 1,
                evidence={"premises": steps[2]["premises"]},
            ),
            variation(
                "ghost_connectedness", "disadvantage", "REJECTED",
                "A final connectedness claim with an empty premise list is a ghost step.",
                claim_held=ghost["premises"] == [] and ghost["value"] is True,
                failure_mode="Ghost step (conclusion without premise)",
                evidence={"premises": []},
            ),
        ],
        advantages=["The host can reject a conclusion that cites no earlier step."],
        disadvantages=["The scratchpad is the submitted trace. Hidden model steps are not visible here."],
        winning_condition_executed=True,
        execution_limit="The inspected scratchpad is the candidate object. No hidden chain-of-thought channel was opened.",
    )


def trial_0000006() -> dict:
    edges = [[0, 1], [1, 2], [2, 3]]
    repair = [3, 0]
    closed = edges + [repair]
    rank_change = cycle_rank(4, closed) - cycle_rank(4, edges)
    diagonal = edges + [[0, 2]]
    diagonal_change = cycle_rank(4, diagonal) - cycle_rank(4, edges)
    labels = [0, 1, 2, 3]
    swapped = [1, 0, 2, 3]
    even = [1, 2, 0, 3]

    def orient(order: list[int]) -> int:
        return 1 if order[0] < order[1] else -1

    problem = {"edges": edges, "repair": repair, "labels": labels}
    candidate = {"rank_change": rank_change, "orientation_after_swap": orient(swapped)}
    contract = {"invariant": "cycle rank", "odd_permutation_flips_orientation": True}
    packet = seal(problem, candidate, contract, "ACCEPTED")
    return _finished(
        6, 7, "mode_07", overwrite_mode=True, family="graph_repair", rung=2,
        seed_prompt="Path 0-1-2-3. The repair may close 3-0 or add diagonal 0-2. Rank change is not enough to name the edge. Odd relabeling flips orientation.",
        answer={"rank_change": rank_change, "repairs_with_same_rank_change": 2},
        packet=packet,
        variations=[
            variation(
                "rank_survives_relabeling", "winning", "ACCEPTED",
                "Closing the square raises cycle rank by 1 on every relabeling. The transposition flips orientation. The 3-cycle does not.",
                claim_held=rank_change == 1 and orient(swapped) == -orient(labels) and orient(even) == orient(labels),
                evidence={"odd_orientation": orient(swapped), "even_orientation": orient(even)},
            ),
            variation(
                "rank_change_does_not_name_the_edge", "disadvantage", "REJECTED",
                "The diagonal raises cycle rank by the same amount as the boundary edge.",
                claim_held=diagonal_change == rank_change and repair != [0, 2],
                failure_mode="Asymmetric label preference",
                evidence={"boundary_rank_change": rank_change, "diagonal_rank_change": diagonal_change},
            ),
            variation(
                "braid_on_three_labels", "advantage", "ACCEPTED",
                "The two braid words on labels 0,1,2 agree: s1 s2 s1 and s2 s1 s2 both reverse the triple.",
                claim_held=_braid_agrees(),
                evidence={"yang_baxter": True},
            ),
        ],
        advantages=["Rank is label-invariant. Orientation records the odd permutation. The braid words agree."],
        disadvantages=["Equal rank change does not choose between the boundary edge and the diagonal."],
        winning_condition_executed=True,
        execution_limit="Checked on this four-vertex carrier, not on a general symmetry group.",
    )


def _braid_agrees() -> bool:
    def swap(labels: list[int], index: int) -> list[int]:
        out = labels[:]
        out[index], out[index + 1] = out[index + 1], out[index]
        return out

    start = [0, 1, 2]
    left = swap(swap(swap(start, 0), 1), 0)
    right = swap(swap(swap(start, 1), 0), 1)
    return left == right == [2, 1, 0]


def trial_0000007() -> dict:
    pairs = [
        {"name": "assert", "sign": 1, "weight": 2, "image": "refuse"},
        {"name": "refuse", "sign": -1, "weight": 2, "image": "assert"},
    ]
    by_name = {item["name"]: item for item in pairs}

    def residual(pair_map: dict[str, dict]) -> int:
        total = 0
        for item in pair_map.values():
            image = pair_map[item["image"]]
            if image["name"] == item["name"] or image["weight"] != item["weight"]:
                return 1
            if image["sign"] != -item["sign"]:
                return 1
            total += item["sign"] * item["weight"]
        return total

    fixed = {"loop": {"name": "loop", "sign": 1, "weight": 2, "image": "loop"}}
    same_sign = {
        "assert": {"name": "assert", "sign": 1, "weight": 2, "image": "refuse"},
        "refuse": {"name": "refuse", "sign": 1, "weight": 2, "image": "assert"},
    }
    problem = {"query": "missing edge 4-5", "pairs": pairs}
    candidate = {"residual": residual(by_name), "code": "MAP_UNDEFINED"}
    contract = {"xi_squared": "id", "fixed_point_free": True, "weight_preserved": True}
    packet = seal(problem, candidate, contract, "ACCEPTED")
    return _finished(
        7, 8, "mode_08", overwrite_mode=True, family="refusal", rung=2,
        seed_prompt="Pair an asserted length with its refusal. Xi swaps them, keeps the weight, and flips the sign. The signed sum must be 0.",
        answer={"residual": 0, "code": "MAP_UNDEFINED"},
        packet=packet,
        variations=[
            variation(
                "pairwise_cancellation", "winning", "ACCEPTED",
                "The declared pair cancels and neither configuration is a fixed point.",
                claim_held=residual(by_name) == 0,
                evidence={"residual": residual(by_name)},
            ),
            variation(
                "fixed_point", "disadvantage", "REJECTED",
                "A refusal paired with itself is a fixed point.",
                claim_held=residual(fixed) != 0,
                failure_mode="Fixed point existence (Xi(x) = x)",
                evidence={"residual": residual(fixed)},
            ),
            variation(
                "sign_preserved", "disadvantage", "REJECTED",
                "Keeping both signs positive leaves a nonzero signed sum.",
                claim_held=residual(same_sign) != 0,
                failure_mode="Sign preservation instead of cancellation",
                evidence={"residual": residual(same_sign)},
            ),
        ],
        advantages=["The identity sign(x) w(x) + sign(Xi(x)) w(Xi(x)) = 0 is an integer check."],
        disadvantages=["The check says nothing about pairs that were not declared."],
        winning_condition_executed=True,
        execution_limit="Finite declared pair only.",
    )


def trial_0000008() -> dict:
    rows = [[1, 1, 0, 3], [0, 1, 1, 5], [1, 0, 1, 4]]
    solution = solve_linear(rows)
    if solution is None:
        raise RuntimeError("rung 3 system")
    values = [int(item) for item in solution]
    sorry = "theorem sum_is_6 : true := by sorry"
    extra_axiom = "axiom choice : Nonempty (Nat -> Nat)\ntheorem sum_is_6 : true := by exact Classical.choice"
    matching_text = "theorem sum_is_6 : x + y + z = 6 := by exact propext"
    problem = {"rows": rows, "target": "x + y + z = 6", "axiom_whitelist": ["propext", "Quot.sound"]}
    candidate = {"text_preflight": "no sorry and no axiom outside the whitelist", "kernel": "not_run"}
    contract = {"verifier": "lean4_kernel_auditor", "lake_build": "not_run"}
    packet = seal(problem, candidate, contract, "NOT_EXECUTED")
    return _finished(
        8, 9, "mode_09", overwrite_mode=True, family="linear_algebra", rung=3,
        seed_prompt="Solve x + y = 3, y + z = 5, x + z = 4. The target statement is x + y + z = 6. A text scan is not a Lean kernel.",
        answer={"x": values[0], "y": values[1], "z": values[2], "sum": sum(values)},
        packet=packet,
        variations=[
            variation(
                "sorry_preflight", "advantage", "REJECTED",
                "The text scan rejects a script that contains sorry.",
                claim_held="sorry" in sorry,
                failure_mode="Proof gap (sorry token present)",
                evidence={"sorry_present": True, "lake_build": "not_run"},
            ),
            variation(
                "undeclared_axiom_name", "advantage", "REJECTED",
                "Classical.choice is outside the declared whitelist.",
                claim_held="Classical.choice" in extra_axiom and "propext" in matching_text,
                failure_mode="Unaudited axiom introduced",
                evidence={"cited": "Classical.choice", "lake_build": "not_run"},
            ),
            variation(
                "matching_sentence_is_not_a_kernel_check", "limit", "NOT_EXECUTED",
                "A sentence that names the target and propext was not elaborated. Lake was not run.",
                claim_held=sum(values) == 6 and "lake" not in candidate["kernel"],
                evidence={"kernel_executed": False, "sum": sum(values)},
            ),
        ],
        advantages=["sorry and an axiom name outside the whitelist are visible in the source text."],
        disadvantages=["A matching sentence can pass a text scan and still not be a proof."],
        winning_condition_executed=False,
        execution_limit="lake build was not run. The kernel winning condition was not executed.",
    )


def trial_0000009() -> dict:
    edges = [[0, 1], [1, 2], [2, 0], [0, 3], [3, 4]]
    dead = {"claim": "tree", "cycle_rank": 0}
    dead_hash = digest(dead)
    current_rank = cycle_rank(5, edges)

    def historical_checker(candidate: dict) -> str:
        if candidate["claim"] == "tree" and current_rank != 0:
            return "REJECTED"
        return "ACCEPTED"

    def amnesiac(candidate: dict) -> str:
        return "ACCEPTED"

    problem = {"edges": edges, "cemetery": [{"hash": dead_hash, "candidate": dead, "status": "REJECTED"}]}
    candidate = {"replay_status": historical_checker(dead), "cycle_rank": current_rank}
    contract = {"rule": "replay must reproduce the stored rejection"}
    packet = seal(problem, candidate, contract, "ACCEPTED")
    return _finished(
        9, 10, "mode_10", overwrite_mode=True, family="graph_facts", rung=3,
        seed_prompt="Triangle 0-1-2 with a tail 0-3-4. A stored rejection says this graph is a tree. Replay that candidate.",
        answer={"cycle_rank": current_rank, "tree": False},
        packet=packet,
        variations=[
            variation(
                "replay_reproduces_rejection", "winning", "ACCEPTED",
                "The stored tree claim is rejected again because the cycle rank is 1.",
                claim_held=historical_checker(dead) == "REJECTED" and current_rank == 1 and digest(dead) == dead_hash,
                evidence={"replay": "REJECTED", "cycle_rank": current_rank},
            ),
            variation(
                "immune_amnesia", "disadvantage", "REJECTED",
                "A checker that ignores cycle rank accepts the dead tree claim.",
                claim_held=amnesiac(dead) == "ACCEPTED" and historical_checker(dead) == "REJECTED",
                failure_mode="Immune amnesia (previously rejected candidate now passes)",
                evidence={"amnesiac": "ACCEPTED", "historical": "REJECTED"},
            ),
            variation(
                "corrupted_cemetery_digest", "disadvantage", "REJECTED",
                "Editing the stored claim without updating the hash breaks the cemetery digest.",
                claim_held=digest({**dead, "cycle_rank": 1}) != dead_hash,
                failure_mode="Corrupted cemetery digest",
                evidence={"digest_match": False},
            ),
        ],
        advantages=["Replay catches a checker that has forgotten why the tree claim died."],
        disadvantages=["The cemetery only protects candidates that were stored."],
        winning_condition_executed=True,
        execution_limit="One stored rejection. No external cemetery archive was read.",
    )


def trial_0000010() -> dict:
    alpha = {"reading": "discrete_chord", "value": "add 0-2"}
    beta = {"reading": "continuous_length", "value": "scale the path"}
    gamma = {"reading": "abstain", "code": "CARRIER_UNDERDETERMINED"}
    collision = alpha["value"] != beta["value"]
    silent = {"choice": alpha["value"], "license": None}
    problem = {"path": [[0, 1], [1, 2]], "request": "shorten the route"}
    candidate = gamma
    contract = {"rule": "collision forbids a silent pick", "source": "collision_tribunal_spec.md"}
    packet = seal(problem, candidate, contract, "ACCEPTED")
    return _finished(
        10, 11, "mode_11", overwrite_mode=True, family="graph_repair", rung=3,
        seed_prompt="Path 0-1-2. The request says shorten the route and does not license hops or lengths. Two readings collide. Abstain.",
        answer={"code": "CARRIER_UNDERDETERMINED"},
        packet=packet,
        variations=[
            variation(
                "abstention_on_collision", "advantage", "ACCEPTED",
                "The discrete chord and the continuous scaling disagree. Abstention is the move the collision spec awards.",
                claim_held=collision and gamma["code"] == "CARRIER_UNDERDETERMINED",
                evidence={"alpha": alpha["value"], "beta": beta["value"]},
            ),
            variation(
                "silent_pick", "disadvantage", "REJECTED",
                "Choosing the chord without a license fails the silent-resolution rule.",
                claim_held=silent["license"] is None and collision,
                failure_mode="Silent resolution of a collision",
                evidence={"choice": silent["choice"]},
            ),
            variation(
                "thirteen_gates_not_enumerated", "limit", "NOT_EXECUTED",
                "The contract names a 13-gate traversal. The contract file does not list those gates, so they were not scored.",
                claim_held=True,
                evidence={"gates_scored": 0},
            ),
        ],
        advantages=["A collision between two unlicensed readings is a reason to abstain."],
        disadvantages=["Abstention does not repair the path. The 13 literary gates were not executed."],
        winning_condition_executed=False,
        execution_limit="The executed rule is the collision defeat in collision_tribunal_spec.md. The 13-gate winning condition was not executed.",
    )


def trial_0000011() -> dict:
    positive = triangle_area_numerator(4, 4, 4)
    degenerate = triangle_area_numerator(1, 1, 4)
    problem = {
        "positive_squared_lengths": [4, 4, 4],
        "degenerate_squared_lengths": [1, 1, 4],
        "identity": "16 area^2 = 2ab+2ac+2bc-a^2-b^2-c^2",
    }
    candidate = {"positive_16_area_sq": positive, "degenerate": "DEGENERATE_SIMPLEX"}
    contract = {"bianchi": "not_inferred", "angles": "not_claimed_rational"}
    packet = seal(problem, candidate, contract, "ACCEPTED")
    return _finished(
        11, 12, "mode_12", overwrite_mode=True, family="refusal", rung=3,
        seed_prompt="Squared lengths 4,4,4 have positive 16 area^2. Squared lengths 1,1,4 are degenerate. Refuse the degenerate triangle. Do not infer a Bianchi identity.",
        answer={"positive_16_area_sq": positive, "degenerate_code": "DEGENERATE_SIMPLEX"},
        packet=packet,
        variations=[
            variation(
                "positive_and_degenerate", "winning", "ACCEPTED",
                "The equilateral numerator is 48. The degenerate numerator is 0, so the winning move is a typed refusal.",
                claim_held=positive == 48 and degenerate == 0,
                evidence={"positive": positive, "degenerate": degenerate},
            ),
            variation(
                "numeric_zero_on_degenerate", "disadvantage", "REJECTED",
                "Returning area 0 for the degenerate triangle is a silent pass, not a refusal.",
                claim_held=degenerate == 0,
                failure_mode="Invalid or degenerate simplex (dimension-correct squared volume <= 0)",
                evidence={"returned": 0, "required": "DEGENERATE_SIMPLEX"},
            ),
            variation(
                "bianchi_from_positive_area", "disadvantage", "REJECTED",
                "Positive squared area does not imply a discrete Bianchi identity.",
                claim_held=positive > 0,
                failure_mode="Hinged curvature imbalance",
                evidence={"bianchi_inferred": False},
            ),
        ],
        advantages=["The sign of 16 area^2 separates the two triangles with integer arithmetic."],
        disadvantages=["The same arithmetic does not produce angles or a conservation identity."],
        winning_condition_executed=True,
        execution_limit="One triangle formula. No Regge action over a larger complex was computed.",
    )


def trial_0000012() -> dict:
    rows = [[1, 1, 0, 3], [0, 1, 1, 5], [1, 0, 1, 4], [1, 1, 1, 6]]
    solution = solve_linear(rows)
    if solution is None:
        raise RuntimeError("dependent rung 4 system")
    values = [int(item) for item in solution]
    original = [
        {"A": 1, "B": 2, "C": 3},
        {"A": 4, "B": 2, "C": 5},
    ]
    lossless_left = project(original, ("A", "B"))
    lossless_right = project(original, ("B", "C"))
    # These projections are lossy for this relation. The lossless split keeps the key.
    keyed = project(original, ("A", "B", "C"))
    sum_rows = [{"x": values[0], "y": values[1], "z": values[2], "s": sum(values)}]
    sum_key = project(sum_rows, ("x", "y", "z"))
    sum_dep = project(sum_rows, ("x", "y", "z", "s"))
    recovered = join(sum_key, ("x", "y", "z"), sum_dep, ("x", "y", "z", "s"))
    lossy = join(
        project(original, ("A", "B")), ("A", "B"),
        project(original, ("B", "C")), ("B", "C"),
    )
    good_orders = [
        frozenset({("A", "B"), ("B", "C")}),
        frozenset({("B", "C"), ("A", "B")}),
    ]
    bad_orders = [
        frozenset({("A", "B"), ("B", "C")}),
        frozenset({("A", "C"), ("A", "B")}),
    ]
    problem = {"rows": rows, "relation": original, "fd": ["A,B,C -> identity", "x,y,z -> s"]}
    candidate = {"sum": sum(values), "chase_target": ["A,B", "B,C"]}
    contract = {"lossless": True, "confluent": True}
    packet = seal(problem, candidate, contract, "ACCEPTED")
    return _finished(
        12, 13, "mode_13", overwrite_mode=True, family="linear_algebra", rung=4,
        seed_prompt="The system x+y=3, y+z=5, x+z=4, x+y+z=6 has a dependent last equation and a unique sum. A separate relation shows a lossy projection.",
        answer={"x": values[0], "y": values[1], "z": values[2], "sum": sum(values)},
        packet=packet,
        variations=[
            variation(
                "dependent_equation_keeps_unique_sum", "winning", "ACCEPTED",
                "Four equations in three unknowns still have the unique sum 6. Joining the sum relation on its key recovers the only tuple.",
                claim_held=values == [1, 2, 3] and recovered == sum_rows and good_orders[0] == good_orders[1],
                evidence={"sum": sum(values), "recovered": len(recovered)},
            ),
            variation(
                "lossy_projection", "disadvantage", "REJECTED",
                "Projecting to (A,B) and (B,C) and joining on B invents tuples.",
                claim_held=len(lossy) > len(original) and len(keyed) == len(original),
                failure_mode="Lossy decomposition",
                evidence={"original": len(original), "joined": len(lossy)},
            ),
            variation(
                "nonconfluent_cover", "disadvantage", "REJECTED",
                "Emitting (A,C) instead of (B,C) on one order produces a different cover.",
                claim_held=bad_orders[0] != bad_orders[1],
                failure_mode="Non-confluent rewrite loop",
                evidence={"orders_agree": False},
            ),
        ],
        advantages=["The dependent linear equation does not change the sum, and the key join is lossless."],
        disadvantages=["A different projection order is not the same schema, and a join on B alone invents rows."],
        winning_condition_executed=True,
        execution_limit="One relation and one linear system. This is not a general 0NF to 6NF engine.",
    )
