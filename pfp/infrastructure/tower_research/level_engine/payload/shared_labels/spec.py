# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Replay of research-tree evidence: contexts that overlap on shared items,
a rule per context, and one local choice of labels per context; the choices
must keep their rules and agree on every shared item.

The witness is ``research/natural_sections`` (read only, through the
vendored clone at its pin; admitted by the author's ruling of 2026-09-25):
its two-label configuration families.  An item is one of the tree's
configurations (two occupied sites of a site graph, written by their site
numbers); a context is one of the tree's undirected arrows between two
configurations, with the rule ``differ`` when the arrow's transport
exchanges the two labels and ``equal`` when it keeps them.  The positive is
the tree's own re-presented four-site chain (its instance
``chain_P4_r0_repres``, one exchanging arrow), which its decider finds
carries a section; each context's choice is that section read on its two
items.  The refused case is the tree's four-site square (instance
``square_2x2_r0``), which its decider finds carries none: every family of
choices that keeps the rules disagrees somewhere.

Clauses, each decided on the packet:

* ``one_choice_each``: every declared context gets exactly one choice, one
  label per item;
* ``rule_kept``: every choice uses declared labels and keeps its context's
  rule;
* ``overlaps_agree``: any two contexts that share an item give it the same
  label (every pair of contexts, not only neighbours in list order);
* ``family_exists``: the tree's decider finds a section on the declared
  contexts read as its two-label arrows (two labels, contexts of two items).

AuthorityEffect: None
"""

from __future__ import annotations

from collections import deque
from types import ModuleType
from typing import Any, Literal

from operations.use_cases.level_engine.research_engine.level import LevelResult
from operations.use_cases.level_engine.research_engine.replay import Packet, Row, packets as replay_packets, result, tree_module

CHALLENGE_ID = "shared_labels"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
TREE = "natural_sections"
# budget_meter is read directly; it imports the other three from the tree.
SOURCES = tuple(f"research/{TREE}/{m}.py" for m in ("budget_meter", "holonomy_fixture", "refinement",
                                                      "representation"))
CLAUSES = ("one_choice_each", "rule_kept", "overlaps_agree", "family_exists")
POSITIVE = "chain_P4_r0_repres"
LABELS = [0, 1]


def tree() -> ModuleType:
    return tree_module(TREE, "budget_meter")


def instance(name: str) -> tuple[list[Any], list[tuple[tuple[Any, Any], bool]], bool]:
    """One of the tree's own instances: objects, two-label arrows with their
    exchange bits, and the verdict the tree expects."""
    found = [(objs, arrows, want) for n, objs, arrows, want in tree().instances() if n == name]
    assert len(found) == 1
    return found[0]


def item(obj: Any) -> str:
    x, y = obj
    return f"{x}{y}"


def spread(objs: list[Any], arrows: list[tuple[tuple[Any, Any], bool]]) -> dict[Any, int]:
    """The label at each object carried out from the least object of each
    component along a breadth-first tree, as the tree's decider builds it."""
    nbrs: dict[Any, list[tuple[Any, bool]]] = {o: [] for o in objs}
    for (a, b), bit in arrows:
        nbrs[a].append((b, bit))
        nbrs[b].append((a, bit))
    label: dict[Any, int] = {}
    for base in objs:
        if base in label:
            continue
        label[base] = 0
        queue = deque([base])
        while queue:
            x = queue.popleft()
            for y, bit in nbrs[x]:
                if y not in label:
                    label[y] = label[x] ^ int(bit)
                    queue.append(y)
    return label


def contexts_of(arrows: list[tuple[tuple[Any, Any], bool]]) -> list[list[object]]:
    return [[f"c{k}", [item(a), item(b)], "differ" if bit else "equal"] for k, ((a, b), bit) in enumerate(arrows)]


def positive() -> Packet:
    objs, arrows, want = instance(POSITIVE)
    assert want
    label = spread(objs, arrows)
    return {"contexts": contexts_of(arrows), "family": [[f"c{k}", [label[a], label[b]]]
                                                         for k, ((a, b), _) in enumerate(arrows)],
            "labels": list(LABELS)}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _family_exists(labels: list[int], contexts: dict[str, tuple[list[str], str]]) -> bool:
    """The tree's decider on the declared contexts read as two-label arrows."""
    if len(labels) != 2 or any(len(items) != 2 for items, _ in contexts.values()):
        return False
    objs = sorted({x for items, _ in contexts.values() for x in items})
    arrows = [((items[0], items[1]), rule == "differ") for items, rule in contexts.values()]
    ok, _ = tree().decide_section_steps(objs, arrows)
    return bool(ok)


def decide(pk: Packet) -> tuple[str, ...]:
    labels, raw_contexts, raw_family = pk["labels"], pk["contexts"], pk["family"]
    assert isinstance(labels, list) and isinstance(raw_contexts, list) and isinstance(raw_family, list)
    contexts = {str(name): ([str(x) for x in items], str(rule)) for name, items, rule in raw_contexts}
    failed: list[str] = []
    family: dict[str, list[int]] = {}
    whole = True
    for name, choice in raw_family:
        if name not in contexts or name in family:
            whole = False
            continue
        family[name] = [int(x) for x in choice]
    if not whole or set(family) != set(contexts) or any(len(family[c]) != len(contexts[c][0]) for c in family):
        failed.append("one_choice_each")
    chosen = {c: v for c, v in family.items() if len(v) == len(contexts[c][0])}
    for c, choice in chosen.items():
        rule = contexts[c][1]
        if any(x not in labels for x in choice) or (rule == "differ" and len(set(choice)) != len(choice)) \
                or (rule == "equal" and len(set(choice)) != 1):
            failed.append("rule_kept")
            break
    seen: dict[str, set[int]] = {}
    for c, choice in chosen.items():
        for x, v in zip(contexts[c][0], choice):
            seen.setdefault(x, set()).add(v)
    if any(len(v) > 1 for v in seen.values()):
        failed.append("overlaps_agree")
    if not _family_exists(labels, contexts):
        failed.append("family_exists")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    objs, arrows, _ = instance(POSITIVE)
    extra = {"contexts": len(arrows), "exchanging_contexts": sum(1 for _, bit in arrows if bit), "items": len(objs)}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, (), SOURCES, extra, trees=(TREE,))
