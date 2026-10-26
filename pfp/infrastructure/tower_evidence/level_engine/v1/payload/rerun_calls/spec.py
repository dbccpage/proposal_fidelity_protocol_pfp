"""Calls to pinned tools, each accepted only when the tool is one of the four
pinned here, its arguments meet the tool's declared contract, and the digest
the caller claims for the result is the digest of the result this level
computes by running the tool itself.  A result is never taken on trust.

The tools, with their declared contracts (supplied, and classified in the
restatement), each run here by its own implementation:

- ``gcd``: arguments ``a`` and ``b``, naturals not both zero; the result is
  their greatest common divisor, a natural;
- ``sort``: argument ``items``, a list of naturals; the result is the list
  in nondecreasing order;
- ``sum``: argument ``terms``, a list of rationals; the result is their
  exact sum, written as a canonical rational text ``p/q``;
- ``count``: arguments ``text`` and ``needle``, texts, the needle not
  empty; the result is the number of occurrences of the needle, scanning
  left to right without overlap.

A result's digest is the SHA-256 of its canonical JSON: a declared
convention.

The claim: calls (each carrying its claimed result digest, in declared
order), tools (each carrying its name, a text), numbers (each carrying an
exact rational) and words (each carrying a text); ``uses(c, t)`` and one
relation per argument, ``arg_a``, ``arg_b``, ``arg_items``, ``arg_terms``,
``arg_text`` and ``arg_needle`` (a list argument's entries are read in
declared order).

Relational clauses, carried by derivability over the hosted claim:
``tool_named``, ``one_tool``, ``uses_typed``, ``one_a``, ``one_b``,
``one_text``, ``one_needle`` and the typing of every argument relation.

Decoded clauses, decided outside the grammar: ``tools_known`` (every call's
tool is pinned), ``arguments_valid`` (every call to a pinned tool has
exactly its tool's arguments, of the declared kinds and ranges) and
``results_recomputed`` (the refused case: a guessed result; every call that
the tool can run claims the digest of the result the tool gives here).

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from engine.encoding import Encoding
from engine.exact.digest import digest_of
from engine.exact.q import ZERO, Q, fmt_q
from engine.kinds import Closure, Functional, Oracle, Total
from engine.level import Compiled, DecodedClause, Fixture
from engine.structure import FiniteStructure
from payload.shared import rows

CHALLENGE_ID = "rerun_calls"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
EXACT = ("py.exact.q", "py.exact.digest")
CLAUSES = ("tools_known", "arguments_valid", "results_recomputed")

# name -> (single arguments, list arguments), each read from ``arg_<name>``.
CONTRACTS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "gcd": (("a", "b"), ()),
    "sort": ((), ("items",)),
    "sum": ((), ("terms",)),
    "count": (("text", "needle"), ()),
}
ARGS = ("a", "b", "items", "terms", "text", "needle")
NUMBER_ARGS = ("a", "b", "items", "terms")
Arg = Q | str | None


def _natural(x: Arg) -> int | None:
    return x.num if isinstance(x, Q) and x.den == 1 and x.num >= 0 else None


def _gcd(args: dict[str, list[Arg]]) -> object | None:
    a, b = _natural(args["a"][0]), _natural(args["b"][0])
    if a is None or b is None or (a == 0 and b == 0):
        return None
    while b:
        a, b = b, a % b
    return a


def _sort(args: dict[str, list[Arg]]) -> object | None:
    items = [_natural(x) for x in args["items"]]
    if any(x is None for x in items):
        return None
    out: list[int] = []
    for x in items:
        assert x is not None
        k = len(out)
        while k > 0 and out[k - 1] > x:
            k -= 1
        out.insert(k, x)
    return out


def _sum(args: dict[str, list[Arg]]) -> object | None:
    terms = args["terms"]
    if not all(isinstance(x, Q) for x in terms):
        return None
    acc = ZERO
    for x in terms:
        assert isinstance(x, Q)
        acc = acc + x
    return fmt_q(acc)


def _count(args: dict[str, list[Arg]]) -> object | None:
    text, needle = args["text"][0], args["needle"][0]
    if not isinstance(text, str) or not isinstance(needle, str) or not needle:
        return None
    found, i = 0, 0
    while i + len(needle) <= len(text):
        if text[i:i + len(needle)] == needle:
            found, i = found + 1, i + len(needle)
        else:
            i += 1
    return found


RUN: dict[str, Callable[[dict[str, list[Arg]]], object | None]] = {
    "gcd": _gcd, "sort": _sort, "sum": _sum, "count": _count}


def tool_of(fs: FiniteStructure, c: int) -> str | None:
    got = [t for cc, t in rows(fs, "uses") if cc == c]
    return fs.text(got[0]) if len(got) == 1 else None


def args_of(fs: FiniteStructure, c: int) -> dict[str, list[Arg]]:
    """Each argument's entries, in declared order of the entries' elements."""
    out: dict[str, list[Arg]] = {}
    for name in ARGS:
        mine = {v for cc, v in rows(fs, "arg_" + name) if cc == c}
        entries = sorted(mine)
        if entries:
            out[name] = [fs.value(v) if name in NUMBER_ARGS else fs.text(v) for v in entries]
    return out


def _shaped(fs: FiniteStructure, c: int) -> bool:
    """The call names exactly its tool's arguments, one entry for a single one."""
    tool = tool_of(fs, c)
    singles, lists = CONTRACTS[tool] if tool in CONTRACTS else ((), ())
    args = args_of(fs, c)
    lists_present = set(args) - set(singles)
    return (all(len(args.get(a, [])) == 1 for a in singles) and lists_present <= set(lists)
            and set(singles) <= set(args))


def result(fs: FiniteStructure, c: int) -> object | None:
    """The tool's own result on the call's arguments; ``None`` when the tool
    is not pinned or cannot run on them."""
    tool = tool_of(fs, c)
    if tool not in RUN or not _shaped(fs, c):
        return None
    _, lists = CONTRACTS[tool]
    args = args_of(fs, c)
    return RUN[tool]({**{a: [] for a in lists}, **args})


def tools_known(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(tool_of(fs, c) in CONTRACTS for c in fs.elements("call"))


def arguments_valid(fs: FiniteStructure, _o: Oracle) -> bool:
    return all(result(fs, c) is not None for c in fs.elements("call") if tool_of(fs, c) in CONTRACTS)


def results_recomputed(fs: FiniteStructure, _o: Oracle) -> bool:
    for c in fs.elements("call"):
        got = result(fs, c)
        if got is not None and fs.digest(c) != digest_of(got):
            return False
    return True


def describe(fs: FiniteStructure) -> dict[str, object]:
    return {"results": [result(fs, c) for c in fs.elements("call")]}


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    call, tool, number, word, uses = e.form("call"), e.form("tool"), e.form("number"), e.form("word"), e.form("uses")
    arg = {a: e.form("arg_" + a) for a in ARGS}
    return Compiled(
        (
            Total("tool_named", ((call, ("c",)),), ((uses, ("c", "t")),)),
            Functional("one_tool", uses, 1),
            Closure("uses_typed", ((uses, ("c", "t")),), ((call, ("c",)), (tool, ("t",)))),
            Functional("one_a", arg["a"], 1),
            Functional("one_b", arg["b"], 1),
            Functional("one_text", arg["text"], 1),
            Functional("one_needle", arg["needle"], 1),
            *(Closure(f"{a}_typed", ((arg[a], ("c", "v")),), ((call, ("c",)), (number if a in NUMBER_ARGS else word,
                                                                                ("v",))))
              for a in ARGS),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("tools_known", tools_known), ("arguments_valid", arguments_valid),
            ("results_recomputed", results_recomputed))),
    )
