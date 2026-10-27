---
pattern_id: AP_MD_005
name: wrong_degree_cochain_quotient
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_005_induced_cochain_quotient
language: markdown
authority_effect: None
---

# Anti-Pattern: Wrong-Degree Cochain Quotient (`AP_MD_005`)

## Description

A markdown claim writes a cochain quotient, evaluation, or cohomology name at a degree the differential does not inhabit. The sentence is ill-typed. It is not a narrow theorem waiting on an extra premise.

## Detection Signature

- A quotient `C^k / im(d^j)` whose image does not land in `C^k`. The reviewed shape is `C2/im(d0)` while `im(d0)` lies in `C1`.
- A k-cochain evaluated on a chain whose dimension is not k. The reviewed shape evaluates a 2-cochain on the 1-chain `boundary(St(h))`.
- `C1/im(d0)` named as first cohomology, or `d1(delta)` named as a nonzero `H2` class, in a complex that also has `d1: C1 -> C2`.

## Witness

Historical review report. This digest did not reopen the manuscript and did not rerun the replay. Quoted from `_ic/inr/core_paper_reviews/po035_2026-10-11/review.md`:

> There are accompanying type errors. `im(d0)` lies in `C1`, so `C2/im(d0)` in line 206 is undefined. A 2-cochain cannot be evaluated on the 1-chain `boundary(St(h))` as in line 220. Also `C1/im(d0)` in line 66 is the quotient cochain space; it is `ker(d1)/im(d0)` that is first cohomology. For scalar cochains the sound map is `bar(d1): C1/im(d0) -> C2`, with kernel `H1`. Its value `d1(delta)` is an exact 2-cochain, not a nonzero `H2` class.

`evidence.json` in that folder binds other exact and numerical witnesses. It does not record these notation lines. Do not treat this quote as evidence that the current manuscript still contains them.

## Hazard

- An ill-typed quotient is later used as an obstruction class.
- An exact value `d1(delta)` is cited as nonzero `H2`. A coboundary is not that class.
- A degree repair is mistaken for a length, angle, connection, or Regge identification.

## Dual Healthy Pattern

See [HP_MD_005_induced_cochain_quotient](../../helpful/markdown/HP_MD_005_induced_cochain_quotient.md).
