---
name: thanatos-public-claim-bs-firewall
description: "Check public math posts keep Lean toy, mechanized and prose claims distinct; no toy sold as a paper theorem."

operad_source_colours: ["Contract", "Code"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
---

# thanatos-public-claim-bs-firewall

**Status:** `ADMITTED` (ooutwire Entry 0016)  
**AuthorityEffect:** `None`  
**Council:** `L3_logos_thanatos` (reuse patterns from `thanatos-anti-dime`)

## When to use

On every public math draft that cites Lean, a paper theorem, or “proved” language.

## Claim status table (mandatory)

For each claim in the draft, classify exactly one:

| Status | Meaning |
| --- | --- |
| `MECHANIZED` | Lean theorem fully proved under stated typeclass hyps |
| `HYP_GATED` | Lean proves implication from explicit analytic hyps |
| `PROSE` | Paper-only proof |
| `LEAN_TOY` | Residual toy (e.g. ℝ commutator); **forbidden** to sell as paper theorem |
| `OPEN` | Not claimed proved |

## Hard refuses

1. LEAN_TOY presented as Theorem 5.1 / quantum short-time bound  
2. “Fully formalized QM / finite QM foundations”  
3. Hype verbs: proves universally, guarantees, revolutionary, never before  
4. Citation to monorepo path as proof of truth  
5. Silent upgrade of hyp-gated product lemma to unconditional Mathlib fact  

## Protocol

1. Extract claims from draft.  
2. Bind each to Lean path or paper section if cited.  
3. Build status table.  
4. Scan hype / persona leaks (pair with Glossa).  
5. Emit terminal + required patches.

## PO-000 default ledger (public)

| Object | Status |
| --- | --- |
| `ProjectionTransfer.transfer` | `MECHANIZED` |
| `transfer_product_KPi_three` | `HYP_GATED` |
| Thm 5.1 \(D_e\ge\nu t-24g^2t^2\) | `PROSE` |
| `po000_l003_double_commutator_rate` | `LEAN_TOY` |

## Terminals

`THANATOS_PUBLIC: ACCEPT` | `THANATOS_PUBLIC: REJECT UNTIL PATCHED`

## Nonclaims

Does not post, promote papers, or mint AuthorityEffect.
