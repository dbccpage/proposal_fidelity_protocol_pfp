# Paper 003: PFP III: Admitting failure detectors and testing their effects

**Status:** Published preprint, v0.1.0 (2026-10-02)  
**Folder:** [`papers/003_pfp_host_admitted_failure_detectors`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/papers/003_pfp_host_admitted_failure_detectors)  
**Record:** [Zenodo 23114331](https://zenodo.org/records/23114331)

## In brief

A failure detector decides whether a recurring pattern should change how later proposals are handled. That can prevent a known mistake, or suppress a valid but unfamiliar answer.

## What it covers

- Specifies detector admission and separates diagnostic findings from route verification.
- Proposes a study protocol for effectiveness and false suppression (blocking an answer an independent checker judges valid).
- Four unadmitted phrase detectors as worked examples; one, as first written, matched a true statement.
- Version 1.2.0 adds exact lemmas on two-signal gates, quorum thresholds and negative selection, each with an exhaustive test.

## Reading and running it

Start with the package [README](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/papers/003_pfp_host_admitted_failure_detectors/README.md), which lists the manuscript, claim ledger and change log.

**Related code:** [Epistemic Immune System](EIS.md)

---

Previous: [Paper 002](Paper-002.md) · [Papers](Papers.md) · Next: [Paper 004](Paper-004.md)
