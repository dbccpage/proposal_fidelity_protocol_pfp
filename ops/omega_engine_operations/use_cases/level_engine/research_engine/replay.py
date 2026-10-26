# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Shared plumbing for the replays of sealed evidence: a positive computed
from the pinned clone, fixtures stated as fields replaced in it, and the
level result built from a per-packet decision.

A replay level's spec supplies the positive, a ``decide`` that returns the
clauses a packet fails (each decided on the replayed sealed facts), its
clause names, the sealed Lean it cites and the sealed sources it reads.

Research-tree witnesses (the author's ruling of 2026-09-25) are read the
same way, read-only through the vendored clone at its pin: ``tree_module``
loads one module of ``research/<tree>/`` under a private name and
``tree_json`` reads one committed file.  A result built with ``trees`` books
its custody (``witness_custody``): the witness is research-tree evidence,
not sealed, and every record built from it says so in its loss ledger.

AuthorityEffect: None
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType

from .canon import load_path
from .components import ROOT
from .errors import Refusal
from .level import FixtureVerdict, LevelResult
from .sealed import vendored
from .sealed_evidence import lean_citation

Packet = dict[str, object]
Row = tuple[str, str, Packet, str | None]


def packets(challenge_id: str, positive: Mapping[str, object]) -> list[Row]:
    """The positive, then each declared fixture as the fields it replaces in
    the positive, then the mutation."""
    d = ROOT / "payload" / challenge_id
    inst = load_path(d / "instance.json")
    assert isinstance(inst, dict) and isinstance(inst["fixtures"], list)
    out: list[Row] = [("pos", "positive", dict(positive), None)]
    for f in inst["fixtures"]:
        out.append((str(f["id"]), str(f["role"]), {**positive, **f["set"]}, f.get("violates")))
    m = load_path(d / "mutation.json")
    assert isinstance(m, dict)
    out.append((str(m["id"]), "mutation", {**positive, **m["set"]}, str(m["violates"])))
    return out


def tree_rel(tree: str, rel: str) -> str:
    """The clone-relative path of one research-tree file.  A tree name is one
    plain path segment; the second derivation's trees are refused by
    ``vendored`` before anything is read."""
    if not tree or "/" in tree or "\\" in tree or tree.startswith("."):
        raise Refusal("RR-TREE", f"{tree!r} is not a research tree name")
    if ".." in rel.replace("\\", "/").split("/"):
        raise Refusal("RR-TREE", f"{rel!r} leaves research/{tree}")
    return f"research/{tree}/{rel}"


@contextmanager
def _on_path(folder: str) -> Iterator[None]:
    """Load one evidence tree with a scoped finder and discard its sibling cache."""
    from omega_engine_operations.domain.level_engine_context import vendor_import_scope

    known = set(sys.modules)
    root = Path(folder).resolve()
    try:
        with vendor_import_scope()(root):
            yield
    finally:
        for name in set(sys.modules) - known:
            file = getattr(sys.modules[name], "__file__", None)
            if not name.startswith("_tree_") and file and Path(file).resolve().is_relative_to(root):
                del sys.modules[name]


def tree_module(tree: str, module: str) -> ModuleType:
    """One module of a research tree, loaded read-only from the vendored clone
    under a private name, with the tree's folder on the path while it loads
    (for its own sibling imports)."""
    path = vendored(tree_rel(tree, module.replace(".", "/") + ".py"))
    name = f"_tree_{tree}_{module.replace('.', '_')}"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None or not path.is_file():
        raise Refusal("RR-TREE", f"no module {module} in research/{tree} at the pin")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        with _on_path(str(vendored(tree_rel(tree, "")))):
            spec.loader.exec_module(mod)
    except BaseException:
        # A module that failed to load is not cached as if it had loaded.
        del sys.modules[name]
        raise
    return mod


def tree_json(tree: str, rel: str) -> object:
    """One committed file of a research tree, read from the vendored clone."""
    return load_path(vendored(tree_rel(tree, rel)))


def result(challenge_id: str, answer_type: str, rows: Sequence[Row], decide: Callable[[Packet], tuple[str, ...]],
           clauses: Sequence[str], lean: Sequence[str], sources: Sequence[str],
           extra: Mapping[str, object], trees: Sequence[str] = ()) -> LevelResult:
    """Decide every packet and cite the sealed Lean from the pinned report.
    With ``trees``, the witness is research-tree evidence: its sources must
    all lie in those trees, no sealed Lean is cited, and the custody is
    booked in the result."""
    if trees:
        roots = tuple(tree_rel(t, "") for t in trees)
        if lean or not sources or not all(s.startswith(roots) for s in sources):
            raise Refusal("RR-TREE", f"{challenge_id}: a research-tree replay reads only its trees and cites no "
                                     "sealed Lean")
        extra = {**extra, "witness_custody": {"custody": "research_tree", "trees": sorted(trees)}}
    verdicts = []
    for fid, role, pk, _ in rows:
        failed = tuple(sorted(decide(pk)))
        verdicts.append(FixtureVerdict(fid, role, True, not failed,
                                       "ACCEPT" if not failed else "FAILS:" + ",".join(failed), failed))
    census = tuple((c, "decoded", ()) for c in clauses)
    claims = tuple({"id": n.split(".")[-1], "lean": [lean_citation(n)], "status": "PROVED_THEOREM"} for n in lean)
    return LevelResult(challenge_id, answer_type, tuple(verdicts), census, None, (), dict(extra),
                       "repo_content", claims, tuple(sources))
