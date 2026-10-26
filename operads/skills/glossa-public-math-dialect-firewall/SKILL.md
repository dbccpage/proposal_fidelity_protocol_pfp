---
name: glossa-public-math-dialect-firewall
description: "Strip in-house jargon from public math posts (MO, Zulip, Math.SE, LinkedIn); require standard vocabulary."

operad_source_colours: ["Proof", "Code"]
operad_target_colour: "Proof"
operad_arity: 2
operad_residual: "unknown"
---

# glossa-public-math-dialect-firewall

**Status:** `ADMITTED` (ooutwire Entry 0015)  
**AuthorityEffect:** `None`  
**Council:** `L3_nous_glossa` (+ peer `L3_nous_aletheia` for claim wording honesty)

## When to use

Before any external math/forum draft is RGB-gated or human-posted.

## Inputs

- Draft post text (title + body + tags/stream)
- Optional venue: `zulip` | `mathoverflow` | `mathse` | `linkedin`

## Hard fail tokens (forum channels)

Refuse until removed (case-insensitive whole-token / brand scan):

- Programme brands: Anomalon, Omega Engine (as product pitch), GTOC, GTLA, PrimDiff, AuthorityEffect, IsAuth, FDA/GTFDA, CODA (forum), Q-membrane, Anomalon councils
- Persona / internal: Thanatos, Woland, Blackrod, Dianoia, Panepistimion, Procurator, OOUTWIRE, Bulgakov cast
- Soft hype as *post framing*: never combined before, finite QM foundations (unless pure classical math statement)

**Preprint exception does not apply** on MO/Zulip/Math.SE/LinkedIn forum posts (stricter than `thanatos-anti-dime` Gate 7 preprint permit list).

## Protocol

1. Scan draft for hard-fail tokens; list line hits.  
2. Rewrite to classical Mathlib / QI / analysis vocabulary.  
3. Ensure one mathematical object; definitions before claims.  
4. Emit `GLOSSA: ACCEPT` | `GLOSSA: REJECT UNTIL PATCHED` + rewritten text.

## Terminals

| Terminal | Meaning |
| --- | --- |
| `GLOSSA: ACCEPT` | Classical; no secret language |
| `GLOSSA: REJECT UNTIL PATCHED` | Hits remain |

## Nonclaims

Does not authorize posting, mint authority, or certify mathematical truth.
