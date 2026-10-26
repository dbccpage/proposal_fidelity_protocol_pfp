# Rulings in force for the level engine

AuthorityEffect: None. These are the author's acts, recorded here; the file
itself grants nothing. Numbering follows `W2-C02_level_engine.md` §13.

| id | ruling (author, 2026-09-25) | how the engine applies it |
| --- | --- | --- |
| placement | The engine lives in the_symbol_game at `research/level_engine/`, not in 19L57G1. MSS-shaped work stays out of 19L57G1 until the second derivation freezes. | 19L57G1 is a gitignored, read-only clone in `vendor/19L57G1`, pinned in `PINS.json`. |
| D3 | Apparatus does not count toward coverage. It is booked in its own column. | A row whose computed answer type is A (level 000 today) is reported, but never as coverage. |
| D4 | A supplied-demand lift counts toward depth only when C04's R2 holds in full, context witness included. By default, engine lifts are recorded, not counted; depth stays with the ascent track. | `StageProposal` and the lift certificate carry `context_witness`; no engine record claims depth. |
| D8 | The embargo guard's scope is C05 §2.5's list, as in W2-C02 §3.2. It lifts when the second derivation freezes, by a later author act. | `engine/guards.py`; the list is pinned by digest in `gate.py` and in the tests. |
| D9 | Claude merges engine pull requests on the engine's own green gate. | `python gate.py`, run from this directory, is that gate. |
| tree-witness | "Yes, admit all 13." A witness from a 19L57G1 research tree, read only through the vendored pinned clone, is admissible evidence for a replay under the `19L57G1` key. | Each admitted level gets a second record, its research-tree replay (tag `T0NN`, `payload/<id>/`, `bindings/adapters/T0NN.py`), beside its harness record. The registration's `witness_custody` is `research_tree` and names the tree files read (`tree_sources`, digests checked at the pin). Every such record books `source.witness_custody` (WEAKENED: research-tree evidence, not sealed) in its loss ledger and says so in its non-claims, because the receiving side's grading has no mark that tells a research-tree witness from a sealed one; a record without it is refused (`UNBOOKED_CUSTODY`). The blocker `witness_not_sealed` is retired (`RULED_ADMISSIBLE`); a tree witness that does not meet its checker is blocked by name (`tree_witness_off_class`). |

Also ruled on 2026-09-25:

- 19L57G1 is repinned to its then-current `origin/main` (`630622da`), and the
  bootstrap is re-run.
- The draft checker-input schema stays until the symbol game publishes its own.
- The `named_sign_uneven` fixture stays, labelled as added after the result.
- Next round (E0.5): the Lean exact-rational library with full field laws,
  then deciding level 005's value clauses with it. Delivered as a separate
  pull request after the move; see the README.

Applied in round P7A (the author's instructions of 2026-09-25):

- The admission ruling says "all 13"; the list it answered names fourteen
  levels (023, 027, 041, 044, 055, 058, 059, 060, 061, 062, 065, 066, 071,
  072), exactly the registrations then blocked by `witness_not_sealed`. The
  ruling is applied to all fourteen as listed; the count is recorded here as
  a discrepancy for the author, not resolved by the engine.
- 19L57G1 is repinned to its then-current `origin/main`: first `35e680ec`
  (only `CLAUDE.md` moved since `535fb553`), then, when rung eight merged,
  `ff584d44` (only `research/second*`, `ci`, `docs`, `.claude`, `.github` and
  the research README moved), then, when rung nine merged, `77ad2a78` (research
  trees' READMEs, manifests and verifiers, `research/second_profile`, `ci`,
  `docs` and one test). No sealed path moved, and no research-tree file the
  engine reads.
- Rung eight of the second derivation is running. Its leftover candidate Y-1,
  the shortest class-matched witnesses over stakes (`research/second_iso`),
  joins the embargo list as `shortest_class_matched_witnesses`, pinned by
  digest; nothing about it is computed.
- Rung eight merged (`ff584d44`) and rung nine is running. It takes X-6, the
  undecided rows of the second derivation's census (two-ness, observational
  classes, adjacency, reach, branching and exhaustion, as `research/second_index`
  and `research/second_class` name them). They join the embargo list as
  `census_undecided_rows_x6`, pinned by digest: none of them is computed for
  the second derivation's regimes, histories or stakes. Replaying a sealed or
  research-tree witness a stage checker requires stays in scope when it is not
  such a computation; a level that would need one is blocked by name. None
  does this round. Rung ten, now running, takes X-6 again (adjacency, reach,
  branching and exhaustion); those rows stay under the same item.
