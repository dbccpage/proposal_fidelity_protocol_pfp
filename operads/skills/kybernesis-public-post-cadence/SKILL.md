---
name: kybernesis-public-post-cadence
description: "Schedule public math posts. One per fortnight by default; no same-day multi-venue dumps; bump policy."

operad_source_colours: ["Paper", "Proof"]
operad_target_colour: "Post"
operad_arity: 2
operad_residual: "unknown"
---

# kybernesis-public-post-cadence

**Status:** `ADMITTED` (ooutwire Entry 0020)  
**AuthorityEffect:** `None`  
**Council:** `L3_nous_kybernesis`

## Defaults

| Rule | Value |
| --- | --- |
| Max new public math objects | 1 per 14 days (default) |
| Same-day multi-venue | Forbidden |
| Zulip bump | ≥7 days silence; max 1 |
| MO after Zulip | Wait for signal or ≥3 days |

## Live ledger pointer

Ops: `omega_engine_atlas/coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction/docs/lean_zulip_legibility_ops.md` §8

## Terminals

`CADENCE: CLEAR` | `CADENCE: WAIT` + next_allowed_date | `CADENCE: BUMP_OK`

## Nonclaims

Does not evaluate math content.
