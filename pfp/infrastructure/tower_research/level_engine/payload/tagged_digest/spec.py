# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Replay of sealed evidence: sealed answers carried in tagged containers,
each decoded by its own tag and bound to the SHA-256 of its exact canonical
bytes.

The sealed compression instance (``derivation.compression``, read from the
pinned clone): the domain ``0, 1, 2`` and the family made of the indicator
question of ``0``.  Its signature classes are counted before and after the
family is duplicated; duplicating refines nothing (sealed ``dup_no_refine``),
so both counts are equal.  Each element's signature under the duplicated
family is a binary word.  The counts travel under the tag ``t0`` (a natural)
and the words under ``t1`` (a binary word).  A digest of existing answers adds
no question (sealed ``postcompose_no_refine``), so the digest is a function
of the body: a changed body under an unchanged digest is refused.

The digest is SHA-256 over the canonical bytes of ``{"body": ..., "tag":
...}``: sorted keys, no whitespace, ASCII.

Clauses, each decided on the replayed sealed facts:

* ``bodies_replayed``: the bodies are the sealed counts and words, in order;
* ``tags_known``: every tag has a decoder (``t0`` or ``t1``);
* ``bodies_decode``: every body decodes under its tag and re-encodes to itself;
* ``digests_bound``: every digest is the SHA-256 of its container's
  canonical bytes.

AuthorityEffect: None
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.level import LevelResult
from omega_engine_operations.use_cases.level_engine.research_engine.replay import Packet, Row, packets as replay_packets, result
from derivation.compression import Family, Fn, class_count, sig_list

CHALLENGE_ID = "tagged_digest"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("Compression.dup_no_refine", "Compression.postcompose_no_refine", "Compression.refinement_tie")
SOURCES = ("code/derivation/compression.py",)
CLAUSES = ("bodies_replayed", "tags_known", "bodies_decode", "digests_bound")
DOMAIN = [0, 1, 2]
INDICATOR: Fn = (1, 0, 0)
WORD = re.compile(r"[01]+")


def family() -> Family:
    return (INDICATOR,)


def bodies() -> list[tuple[str, dict[str, object]]]:
    once, twice = family(), family() + family()
    out: list[tuple[str, dict[str, object]]] = [("t0", {"n": class_count(DOMAIN, q)}) for q in (once, twice)]
    out += [("t1", {"word": "".join(str(v) for v in sig_list(twice, x))}) for x in DOMAIN]
    return out


def canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def digest(tag: str, body: object) -> str:
    return "sha256:" + hashlib.sha256(canonical({"body": body, "tag": tag})).hexdigest()


def positive() -> Packet:
    return {"containers": [{"body": body, "digest": digest(tag, body), "tag": tag} for tag, body in bodies()]}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def decodes(tag: str, body: object) -> bool:
    if not isinstance(body, dict):
        return False
    if tag == "t0":
        n = body.get("n")
        return set(body) == {"n"} and isinstance(n, int) and not isinstance(n, bool) and n >= 0
    word = body.get("word")
    return set(body) == {"word"} and isinstance(word, str) and WORD.fullmatch(word) is not None


def decide(pk: Packet) -> tuple[str, ...]:
    failed: list[str] = []
    containers = pk["containers"]
    assert isinstance(containers, list)
    if [(c["tag"], c["body"]) for c in containers] != bodies():
        failed.append("bodies_replayed")
    known = [c for c in containers if c["tag"] in ("t0", "t1")]
    if len(known) != len(containers):
        failed.append("tags_known")
    if not all(decodes(str(c["tag"]), c["body"]) for c in known):
        failed.append("bodies_decode")
    if any(c["digest"] != digest(str(c["tag"]), c["body"]) for c in containers):
        failed.append("digests_bound")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    extra = {"counts": [b["n"] for t, b in bodies() if t == "t0"],
             "words": [b["word"] for t, b in bodies() if t == "t1"]}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, LEAN, SOURCES, extra)
