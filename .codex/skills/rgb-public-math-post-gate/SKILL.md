---
name: rgb-public-math-post-gate
description: "Gate a public math post through ROI, Lean export, dialect, claim and voice checks to ACCEPT or REJECT."

operad_source_colours: ["Proof", "Code"]
operad_target_colour: "Proof"
operad_arity: 2
operad_residual: "unknown"
---

# rgb-public-math-post-gate

**Status:** `ADMITTED` (ooutwire Entry 0021)  
**AuthorityEffect:** `None`  
**Councils:** joint — see pipeline  
**Related goo:** `goo-public-math-legibility-rgb`  
**Workflow:** `public-math-legibility` (`.grok/workflows/public-math-legibility.rhai`)

## Pipeline (strict order)

```text
0  oikonomia-legibility-roi              → HOLD or PROCEED
1  panep-lean-snippet-export             → if Lean cited
2  glossa-public-math-dialect-firewall   → Green language
3  thanatos-public-claim-bs-firewall     → Red no-BS
4  mimesis-external-forum-voice          → Blue voice
5  kybernesis-public-post-cadence        → schedule
6  RGB synthesize                        → ACCEPT | REJECT | HOLD
7  HUMAN posts                           (never agent)
8  Record URL in lean_zulip_legibility_ops.md §8
```

## Veto law

Thanatos or Glossa `REJECT` **cannot** be overridden by Mimesis or Oikonomia.

## RGB checklist

### Red

- [ ] Claim status table honest  
- [ ] No hype / LEAN_TOY fraud  
- [ ] No secret language residual  

### Green

- [ ] Classical parse in 60s  
- [ ] Stream/tags/title set  
- [ ] One object  

### Blue

- [ ] Professional voice  
- [ ] Legibility not spam  
- [ ] Cadence clear  

## Terminals

`RGB: ACCEPT` | `RGB: REJECT UNTIL PATCHED` | `RGB: HOLD`

## Ops home

`atlas/coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction/docs/lean_zulip_legibility_ops.md`

## Nonclaims

Does not post, mint AuthorityEffect, or GlobalGreen anything.
