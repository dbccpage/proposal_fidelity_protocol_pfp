"""Strict Tier S (Gamma38) Hodge arm for P1, from omega_codex. AuthorityEffect: None.

Source: omega_codex `education/3_minimal_symbol_systems/rewriting/rewriting_strategies_mssn_wire.md`
(origin/main, read 2026-11-17). It uses:
- the alphabet Gamma38 = a-z, 0-9, `<` and `>`, with no whitespace or punctuation (Tier S, AP-01 and AP-03);
- the packet grammar `packet ::= <> | <w> | <p1..pk>` (Definition 2.2);
- R1 carrier declaration, the five-slot `<<decl>...>`;
- R7 role wrapping (assume, derive, check);
- the signed-integer codec `<<neg><n>>`;
- a terminal stamp `<<terminal><<qed><exact>>>`, which nf.mssn.bqnf.yaml treats as a claim that stays UNVERIFIED until the host replays it.

The existing `wire` and `wire_qed` arms are a Tier H style (head words, commas, `=`, `-`, parentheses).
This arm is the strict form of the same content plus the wire_qed skeleton. The answer contract (the system
message) is unchanged, so only the presentation differs.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAMMA38 = frozenset("abcdefghijklmnopqrstuvwxyz0123456789<>")


def a(word: str) -> str:
    return f"<{word}>"


def c(*parts: str) -> str:
    return "<" + "".join(parts) + ">"


def num(n: int) -> str:
    return c(a("neg"), a(str(-n))) if n < 0 else a(str(n))


def tier_s_qed(inst: dict) -> str:
    n, edges, tris, flow = inst["vertices"], inst["edges"], inst["triangles"], inst["flow"]
    eq = lambda x, y: c(a("eq"), x, y)  # noqa: E731
    return c(
        a("hodge"),
        c(a("decl"), c(a("alph"), a("gamma38")), c(a("dom"), a("rat")), c(a("rules"), a("hodgesplit")),
          c(a("obst"), a("harmonic")), c(a("goal"), a("exact"))),
        c(a("vert"), *(a(str(v)) for v in range(n))),
        c(a("edges"), *(c(a("e"), a(str(u)), a(str(v))) for u, v in edges)),
        c(a("faces"), *(c(a("f"), a(str(x)), a(str(y)), a(str(z))) for x, y, z in tris)),
        c(a("orient"), c(a("e"), a("lowtohigh")), c(a("f"), a("increasing"))),
        c(a("flow"), *(num(x) for x in flow)),
        c(a("assume"), eq(c(a("d0"), a("p"), c(a("e"), a("u"), a("v"))),
                          c(a("sub"), c(a("p"), a("v")), c(a("p"), a("u"))))),
        c(a("assume"), eq(c(a("d1"), a("x"), c(a("f"), a("a"), a("b"), a("c"))),
                          c(a("sub"), c(a("add"), c(a("x"), a("a"), a("b")), c(a("x"), a("b"), a("c"))),
                            c(a("x"), a("a"), a("c"))))),
        c(a("goal"), eq(a("f"), c(a("add"), c(a("d0"), a("p")), c(a("d1t"), a("q")), a("h")))),
        c(a("assume"), eq(c(a("d0t"), a("h")), a("0"))),
        c(a("assume"), eq(c(a("d1"), a("h")), a("0"))),
        c(a("assume"), c(a("inner"), a("standard"))),
        c(a("assume"), eq(c(a("p"), a("0")), a("0"))),
        c(a("derive"), a("p"), eq(c(a("d0t"), c(a("d0"), a("p"))), c(a("d0t"), a("f")))),
        c(a("derive"), a("q"), eq(c(a("d1"), c(a("d1t"), a("q"))), c(a("d1"), a("f")))),
        c(a("derive"), a("h"), c(a("sub"), a("f"), c(a("add"), c(a("d0"), a("p")), c(a("d1t"), a("q"))))),
        c(a("check"), eq(c(a("d0t"), a("h")), a("0")), eq(c(a("d1"), a("h")), a("0"))),
        c(a("derive"), a("b0"), a("b1"), a("euler")),
        c(a("terminal"), c(a("qed"), a("exact"))),
    )


def parse(text: str, i: int = 0):
    """Parse one Definition 2.2 packet; return (tree, next index). Words are str, composites lists."""
    if text[i] != "<":
        raise ValueError(f"expected < at {i}")
    j = i + 1
    if text[j] == ">":
        return [], j + 1
    if text[j] != "<":
        k = text.index(">", j)
        word = text[j:k]
        if not word or not set(word) <= GAMMA38 - {"<", ">"}:
            raise ValueError(f"bad atom at {i}")
        return word, k + 1
    kids = []
    while text[j] == "<":
        kid, j = parse(text, j)
        kids.append(kid)
    if text[j] != ">":
        raise ValueError(f"expected > at {j}")
    return kids, j + 1


def parse_all(text: str):
    """The whole text must be exactly one packet over Gamma38."""
    tree, end = parse(text)
    if end != len(text):
        raise ValueError(f"trailing text at {end}")
    return tree


def build(tasks_path: Path = HERE / "tasks.jsonl") -> list[dict]:
    rows = []
    for line in tasks_path.read_text(encoding="utf-8").splitlines():
        t = json.loads(line)
        if t["family"] != "H":
            continue
        text = tier_s_qed(t["instance"])
        rows.append(dict(task_id=t["task_id"], family="H", instance=t["instance"], expected=t["expected"],
                         arms={"tier_s_qed": text}, arm_sha256={"tier_s_qed": hodge_sha(text)},
                         system=t["system"], system_sha256=t["system_sha256"],
                         max_completion_tokens=t["max_completion_tokens"]))
    return rows


def hodge_sha(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    rows = build()
    body = "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows)
    (HERE / "tasks_tier_s.jsonl").write_bytes(body.encode("utf-8"))
    print(f"wrote tasks_tier_s.jsonl: {len(rows)} tasks, sha256 {hodge_sha(body)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
