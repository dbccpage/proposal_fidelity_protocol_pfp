---
name: aletheia-corpus-integrity-ledger
description: "Use before citing a corpus figure. Ledger of duplicate uids, dangling edges and missing domains in basis jsonl corpora."
operad_source_colours: ["Ledger", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
---

# aletheia-corpus-integrity-ledger

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L3_nous_aletheia`

## When to use

Before any figure drawn from the basis corpora is quoted in a paper, a spec, or
a gate. The corpora are 21,466 lines that no skill has ever read.

## Inputs

- `cognitive_operations/ooutwire/_docs/basis_*.jsonl` (22 files)
- `.../cognitive_warfare_defense_registry.json`
- helpers in `governance/frontend/cli/basis_corpus_wave_cli.py`

## Protocol

1. Parse all three record dialects: doc-import, structured wave, table-import.
2. Count uid collisions per corpus.
3. Resolve every `edges` target and every `countermeasure_uids` entry.
4. Compare the declared domain set in `basis_registry.md` against the files on
   disk, both directions.
5. Append findings to `_ooutwire/ledgers/basis_integrity.jsonl`. **Append only.**

## Why this is a ledger and never a repair

The CWGATE spec puts corpus rewriting explicitly out of scope, and
`basis_corpus_wave.py` states it "does not rewrite the 12k-line exploit dump".
Deduplicating would also make the governance spec's own cited figures
unreproducible, which converts a measurable corpus into an unfalsifiable one.

## Findings the first run is expected to reproduce

- `basis_cognitive_exploits.jsonl`: 12,398 records, 5,847 distinct uids --
  1,877 uids repeat, 6,551 excess rows.
- Across all 22 corpora: 3,971 distinct edge targets, **3,670 dangling (92%)**.
- The corpora name 12 distinct `defense:*` countermeasures; the registry holds
  6; **the two sets are disjoint**, so every countermeasure reference in a
  12,398-record catalog resolves to nothing.
- `basis_semiotics.jsonl` is 12 records that are 6 records duplicated verbatim.

## Terminals

`INTEGRAL`, `DUPLICATE_UIDS`, `DANGLING_EDGES`, `UNRESOLVABLE_COUNTERMEASURE`,
`DECLARED_ABSENT`.

## Nonclaims

Integrity is not truth. A corpus can be perfectly self-consistent and still
describe nothing real. This measures the graph, not the claims in it.
