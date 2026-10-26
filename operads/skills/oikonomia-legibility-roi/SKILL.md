---
name: oikonomia-legibility-roi
description: "Decide where and when to post public math (MO, Zulip, Math.SE, LinkedIn), and when not to post."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# oikonomia-legibility-roi

**Status:** `ADMITTED` (ooutwire Entry 0018)  
**AuthorityEffect:** `None`  
**Council:** `L3_nous_oikonomia` (pairs with `oikonomia-promote-ooutwire`)

## When to use

Stage 0 of public-math pipeline — before drafting spend.

## Decision inputs

- Goal: `lean_collab` | `math_prior_art` | `job_signal` | `essay_brand`
- Object readiness: Lean status, paper nonclaims
- Cadence: last public post date

## Default venue order

| Goal | First venue |
| --- | --- |
| Lean lemma / Mathlib home | Lean Zulip `#Is there code for X?` |
| Prior art / references | MathOverflow |
| Proof-check / constants | Math.SE |
| Career narrative (after math posts exist) | LinkedIn essay |

## HOLD rules

- Same calendar day multi-venue dump → `HOLD`  
- Object still LEAN_TOY sold as theorem → `HOLD` until Thanatos clear  
- No clear classical question → `HOLD`

## Terminals

`ROI: PROCEED` + venue list | `ROI: HOLD` + reason

## Nonclaims

Does not authorize content truth or posting.
