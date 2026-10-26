# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""The supplied inscription is exactly the two-byte opaque datum the sealed
genesis supplies first.  The object language does not read glyphs, so the
byte check is apparatus; the native content is inertia (supply alone changes
no admitted state).

A replay of sealed evidence: the carrier part is repository content.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine.canon import load_path
from omega_engine_operations.use_cases.level_engine.research_engine.components import ROOT
from omega_engine_operations.use_cases.level_engine.research_engine.level import FixtureVerdict, LevelResult
from omega_engine_operations.use_cases.level_engine.research_engine.sealed import EMPTY, Supply, replay, sealed_observe
from omega_engine_operations.use_cases.level_engine.research_engine.sealed_evidence import lean_citation
from derivation.engine import GENESIS_F, GENESIS_L

CHALLENGE_ID = "bare_inscription"
ANSWER_TYPE = "A"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("Derivation.supply_no_op", "Derivation.genesis_underivable", "Derivation.underivable_of_empty")
SOURCES = (
    "code/derivation/engine.py",
    "code/derivation/model.py",
    "ci/check_prompt_hashes.py",
    "prompt/prompt.md",
    "prompt/seed_prompt.md",
)


def pinned() -> str:
    first = GENESIS_L[0]
    assert isinstance(first, Supply)
    return first.token


def packets() -> list[tuple[str, str, str, str | None]]:
    d = ROOT / "payload" / CHALLENGE_ID
    inst = load_path(d / "instance.json")
    assert isinstance(inst, dict) and isinstance(inst["fixtures"], list)
    out = [(str(f["id"]), str(f["role"]), str(f["packet"]), f.get("violates")) for f in inst["fixtures"]]
    m = load_path(d / "mutation.json")
    assert isinstance(m, dict)
    base = next(p for fid, _, p, _ in out if fid == m["of"])
    k = int(str(m["insert_at"]))
    out.append((str(m["id"]), "mutation", base[:k] + str(m["text"]) + base[k:], str(m["violates"])))
    return out


def bytes_exact(packet: str) -> bool:
    return packet.encode("ascii") == pinned().encode("ascii")


def evaluate(have: frozenset[str]) -> LevelResult:
    verdicts = []
    for fid, role, packet, _ in packets():
        ok = bytes_exact(packet)
        verdicts.append(FixtureVerdict(fid, role, True, ok, "ACCEPT" if ok else "FAILS:bytes_exact",
                                       () if ok else ("bytes_exact",)))
    after = replay((Supply(pinned()),))
    admitted_l = list(replay(GENESIS_L).data)
    extra = {
        "native": {
            "contexts_after_supply": len(sealed_observe.contexts(after)),
            "supply_is_inert": after == EMPTY,
        },
        "anti_aligned": {
            "note": "the target refuses an interior glyph at this stage; the sealed genesis admits "
                    "such inscriptions as opaque wholes",
            "sealed_admitted_data_L": admitted_l,
            "sealed_admitted_data_F": list(replay(GENESIS_F).data),
        },
        "clause_inputs": {"bytes_exact": "bytes of the presented packet (apparatus)"},
    }
    census = (("bytes_exact", "apparatus", ()),)
    claims = tuple({"id": n.split(".")[-1], "lean": [lean_citation(n)], "status": "PROVED_THEOREM"} for n in LEAN)
    return LevelResult(CHALLENGE_ID, ANSWER_TYPE, tuple(verdicts), census, None, (), extra,
                       "repo_content", claims, SOURCES)
