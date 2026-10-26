---
name: techne-operadic-cemetery-retriever
description: "Retrieve falsified hypotheses and negative witnesses from past retractions so deadlocks do not repeat dead paths."
families: [oecog, memory_retrieval]
operad_source_colours: ["State", "Ledger"]
operad_target_colour: "State"
operad_arity: 2
operad_residual: "unknown"
---

# techne-operadic-cemetery-retriever

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L3_logos_techne`

## When to use

Use when an agent reasoning loop encounters an impasse or deadlock ($\Phi_1 > 0$),
or prior to initiating a new proof or refactoring path, to review previously falsified approaches.

## Inputs

- Active context state and failure signature ($\Phi_1, \Gamma_2, \text{defect_count}$).
- Historical retraction store in `_intelligence/symbol_game/` and `CemeterySink`.
- Search query terms or topological obstruction tags.

## Protocol

1. Ingest the active problem formulation and failure coordinates.
2. Query indexed historical retraction records and negative result ledgers using lexical and trigram matching.
3. Extract relevant falsification witnesses, disproven candidate premises, and recorded 9-dot gauge break transformations.
4. Filter out obsolete or superseded traces.
5. Formulate a structured negative prior dossier informing the agent of dead-end branches and orthogonal alternative angles.

## Terminals

`RETRACTION_MATCH_FOUND`, `NO_PRIOR_FAILURE_RECORDED`, `INDEX_REFRESHED`.

## Nonclaims

Historical retrieval surfaces recorded prior retractions within the repository corpus;
it does not assert that unattempted or unindexed failure modes cannot occur.
