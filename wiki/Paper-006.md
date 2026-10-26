# Paper 006: PFP VI: Retained failure evidence and controlled reuse

**Status:** Published preprint, v0.1.0 (2026-10-02)  
**Folder:** [`papers/006_pfp_epistemic_immune_system_and_cemetery_dag_mining`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/papers/006_pfp_epistemic_immune_system_and_cemetery_dag_mining)  
**Record:** [Zenodo 23114681](https://zenodo.org/records/23114681)

## In brief

Keeping rejected proposals is useful, but the record must stay interpretable and checkable, and reuse must not turn a rejection into authority.

## What it covers

- A JSONL failure ledger that chains entry digests, verifies restart state and emits a count-and-head receipt.
- Explains exactly which edits the checks detect, and why an independent anchor is needed if an attacker can rewrite the whole file.
- A controlled reuse procedure with benign-example checks, downgrade thresholds and affinity decay.

## Reading and running it

Start with the package [README](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/papers/006_pfp_epistemic_immune_system_and_cemetery_dag_mining/README.md), which lists the manuscript, claim ledger and change log.

**Related code:** [Epistemic Immune System](EIS.md)

---

Previous: [Paper 005](Paper-005.md) · [Papers](Papers.md) · Next: [Paper 007](Paper-007.md)
