---
name: panep-lean-snippet-export
description: "Export a public Lean 4 snippet (80 lines max) from a lake module with hypothesis ledger and axiom report."
invocation: discipline
operad_source_colours: ["Proof", "Code"]
operad_target_colour: "Proof"
operad_arity: 2
operad_residual: "unknown"
---

# panep-lean-snippet-export

**Status:** `ADMITTED` (ooutwire Entry 0019)  
**AuthorityEffect:** `None`  
**Council:** `L3_nous_panepistimion`  
**Related goo:** `goo-lean-public-snippet-export` (thin twin; prefer this admitted package)

## When to use

When preparing Zulip follow-up code or packaging a public Lean object.

## Default showcase (PO-000)

Path: `engine/lean4/research_programs/004_projection_obstruction/000_projection_obstruction/po000_l001_projection_transfer.lean`

1. First reply: abstract `C` + `transfer` only.  
2. Second reply if asked: product `tensor_subadd` + `transfer_product_KPi_three` with hyps.  
3. Never export `po000_l003_double_commutator_rate` as Thm 5.1.

## Protocol

1. Name theorem + file.  
2. Extract ≤80 lines (or minimal import set + theorem).  
3. Status: MECHANIZED | HYP_GATED | LEAN_TOY.  
4. Strip estate comments/brands.  
5. Optional: `lake build` / `#print axioms` note if environment allows.  
6. Terminal: `SNIPPET_READY` | `REJECT_TOY_AS_THEOREM` | `NEED_HUMAN_TRIM`

## Nonclaims

Does not claim Mathlib merge readiness. Does not mint authority.
