---
name: episteme-dossier-basis-provenance
description: "Use before citing a dossier's sources. Resolves dossier concept refs to basis corpus uids; reports unresolved share."
families: [oecog]
operad_source_colours: ["Ledger", "State"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
---

# episteme-dossier-basis-provenance

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L3_logos_episteme`

## When to use

Before any dossier's `provenance.source_basis` is treated as a citation. The
dossiers declare which corpora they draw on; nothing has ever checked that the
concepts they name are in those corpora.

## Inputs

- `.../_docs/_sap/ana_000_forms_council_members/*.yaml` (317 files, **read-only**)
- all 22 `basis_*.jsonl`

## Protocol

1. Extract `catalog_bindings.*.concept_refs` **only**. A coarse scan that also
   sweeps `tags:` over-counts; scoping the denominator correctly is this
   skill's first deliverable, not an afterthought.
2. Resolve each ref against every corpus uid and label.
3. Report resolved / unresolvable per dossier and per corpus.

## The fence

`RULE_DOSSIER_IMMUTABILITY_001`: no automated script or agent may reformat or
overwrite a dossier. This skill opens them and never writes. The apparatus is
`fictional: true` with `authority_effect: None`, and Prime Rule Zero holds:
zero external or human targeting, internal synthetic DEV seams only.

## Expected first finding

A coarse scan over the dossiers found 280 distinct scalar refs and 11,093
occurrences, of which **273 (98%) match no uid or label in any corpus** --
including `bounded_rationality`, `salience_network` and
`metacognitive_monitoring`, all declared under `source_basis: [cognitive_science]`.
That figure is an upper bound until the `catalog_bindings` scoping above is
applied, which is precisely why the scoping is step one.

## Terminals

`RESOLVED`, `UNRESOLVABLE`, `AMBIGUOUS`, `OUT_OF_SCOPE_REF`.

## Nonclaims

A resolvable ref is not a substantiated one. This checks that a named concept
exists in a declared corpus, not that the dossier's use of it is sound. Nothing
here claims anything about a real person.
