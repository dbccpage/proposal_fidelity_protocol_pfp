---
name: nous-clinical-formulation-sandbox
description: "Four-P case formulation for one fictional dossier actor. Refuses any real person or real model."
families: [oecog]
operad_source_colours: ["Ledger", "Paper"]
operad_target_colour: "Paper"
operad_arity: 2
operad_residual: "unknown"
---

# nous-clinical-formulation-sandbox

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L2_nous`

## When to use

When a simulated council actor's behaviour needs a structured account rather
than an adjective. The Adversary panel has an Epistemic Sanatorium Director seat
(Quarantine) with prose, a YAML record, and no skill.

## Inputs

One dossier from `.../ana_000_forms_council_members/`, specifically its
`developmental_model`, `epistemic_profile`, and
`cognitive_security.biases_and_vulnerabilities` sections. **Read-only.**

## Protocol

1. Confirm the subject is a `kind: fictional_cognitive_actor` record. If it is
   not, refuse.
2. Build the four-P formulation from the dossier's own fields, citing the field
   each element comes from.
3. State what the formulation does not explain. A formulation that explains
   everything is a horoscope.
4. Emit a memo stamped `fictional: true`, `authority_effect: None`.

## The fence, which is the whole point

- Subjects are synthetic records in a `fictional: true` apparatus.
- **Zero external or human targeting.** Internal synthetic DEV seams only, no PROD.
- No claim that any formulation predicts a real person's or a real model's
  behaviour. The CWGATE spec puts that explicitly out of scope.
- The output is a description of a fiction. It is not a diagnosis, it does not
  describe anyone, and it may not be applied to anyone.

## Terminals

`FORMULATED`, `INSUFFICIENT_DOSSIER_DATA`, `REFUSED_NON_FICTIONAL_SUBJECT`.

## Nonclaims

This is not clinical practice, not assessment, and not advice. It is a
structured reading of a synthetic personnel record, and its only use is making
a simulation legible to its own operators.
