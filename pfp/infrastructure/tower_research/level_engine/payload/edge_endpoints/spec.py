# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Every arc of a hosted directed graph names two present nodes, and the
protected pair stays separated.

Claim-only: no witness form, no fresh form.  The claim is frozen, so a
failed requirement is final.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.kinds import Closure, Req, Separate
from operations.use_cases.level_engine.research_engine.level import Compiled, Fixture

CHALLENGE_ID = "edge_endpoints"
ANSWER_TYPE = "D"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    arc, node = e.form("arc"), e.form("node")
    reqs: list[Req] = [
        Closure("endpoint_source", ((arc, ("x", "y")),), ((node, ("x",)),)),
        Closure("endpoint_target", ((arc, ("x", "y")),), ((node, ("y",)),)),
    ]
    for i, j in fx.protected:
        reqs.append(Separate("protect", min(i, j), max(i, j)))
    return Compiled(tuple(reqs))
