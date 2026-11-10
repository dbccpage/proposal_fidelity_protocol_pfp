# Lean claim map: PFP X, version 0.1.0

The package's Lean project (`lean4/`, one root module) formalizes one statement,
used as a remark in Section 2.3 of the manuscript. The flatness check itself is
tested in Python, not formalized.

| Claim ID | Lean declaration | File | Status | Axioms |
| --- | --- | --- | --- | --- |
| PFP10-15 | `SymbolGame010.identity_links_give_identity_product` | `lean4/LatticeDecimation.lean` | Proved | none (see `lean4/axiom_report.txt`) |

The lemma is stated for a structure that carries all group laws. Its proof uses
only the identity law and the fact that the inverse of the identity is the
identity. `lean4/Census.lean` is generated from `lean4/axiom_report.txt` by
`tools/replay_lean_axiom_census.py`, which also replays it.

## Current versus historical verification

The named report dates from 2026-09-28 and the full-module report from 2026-10-02.
The latter lists 26 declarations: 25 axiom-free and one generated `mk.injEq` using
`propext`. The current review checks these records statically and does not execute
the pinned Lean 4.34.0-rc1 compiler. Neither census verifies the Python host.
