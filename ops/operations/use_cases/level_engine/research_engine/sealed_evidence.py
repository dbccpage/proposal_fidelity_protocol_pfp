# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Citations of sealed evidence, read from the vendored clone at its pin.

A Lean citation is accepted only when the vendored axiom report names the
declaration (``RR-STATEMENT`` otherwise) and its axioms lie within
``{propext, Quot.sound, Classical.choice}`` (``RR-AXIOM`` otherwise). Nothing is rebuilt: the
report is the sealed repository's own gated artifact.

AuthorityEffect: None
"""

from __future__ import annotations

import re
from functools import lru_cache

from pfp.domain.lean_bridge.models import STANDARD_LEAN_AXIOMS

from .canon import git_blob_id, sha256_tag
from .errors import Refusal
from .sealed import vendored

POLICY = frozenset(STANDARD_LEAN_AXIOMS)
_LINE = re.compile(r"^.*'(?P<name>[^']+)' (?:depends on axioms: \[(?P<ax>[^\]]*)\]|does not depend on any axioms)")


@lru_cache(maxsize=1)
def axiom_report() -> dict[str, tuple[str, ...]]:
    out: dict[str, tuple[str, ...]] = {}
    for line in vendored("artifacts/lean_axioms.txt").read_text(encoding="utf-8").splitlines():
        m = _LINE.match(line)
        if m:
            ax = m.group("ax")
            out[m.group("name")] = tuple(a.strip() for a in ax.split(",")) if ax else ()
    return out


def lean_citation(name: str, report: dict[str, tuple[str, ...]] | None = None) -> dict[str, object]:
    rep = axiom_report() if report is None else report
    if name not in rep:
        raise Refusal("RR-STATEMENT", f"{name} has no axiom report at the pin")
    axioms = rep[name]
    if not set(axioms) <= POLICY:
        raise Refusal("RR-AXIOM", f"{name} depends on an axiom outside the policy")
    return {"axioms": list(axioms), "name": name}


def source(rel: str) -> dict[str, str]:
    data = vendored(rel).read_bytes()
    return {"blob": git_blob_id(data), "path": rel, "sha256": sha256_tag(data)}
