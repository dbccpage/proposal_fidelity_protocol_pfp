---
name: governance-literature-catalog
description: "Consolidated literature ingestion, YAML spine catalog reconciliation, and hybrid search retrieval gate."
operad_source_colours: ["State", "Ledger"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [governance, literature-catalog]
---

# governance-literature-catalog

AuthorityEffect: None.

## The single rule

> Ingestion pipelines must stream Markdown without disk bloating, YAML spine catalogs must maintain strict bijection with FTS5 indices, and book chapters must adhere to declared 6-section structure.

## Consolidated Invariants

1. **Resilient arXiv Streaming**: Stream conversion from PDF to Markdown with immediate raw PDF deletion and FTS5 indexing without disk bloat (`goo-arxiv-resilient-stream-ingestion-gate`).
2. **Spine-to-Index Reconciliation**: Mechanical bijection between disk YAML spines, `master_spine_index.yaml`, and SQLite FTS5/vector indices (`goo-spine-batch-catalog-synchronizer`).
3. **FastMCP Retrieval Standards**: Contracts over SQLite FTS5 BM25 + dense vector cosine similarity with RRF and cross-encoder reranking (`goo-fastmcp-cross-encoder-hybrid-retrieval-gate`).
4. **Library & Chapter Layout Linter**: Goal prompts require custody ledgers, and book chapters must strictly implement the declared 6 section headers (`goo-prompts-university-library-custody`, `goo-book-chapter-six-section-linter`).

## Verification Requirements

Run the literature catalog reconciliation check:

```bash
python operads/skills/governance-literature-catalog/scripts/check_literature_catalog.py
```
