# Paper 001: PFP I: Exact graph repair and the boundary between a proposal and a certificate

**Status:** Published preprint, v0.1.0 (2026-10-02)  
**Folder:** [`papers/001_pfp_discrete_cochain_retraction_and_toy_involutions`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/papers/001_pfp_discrete_cochain_retraction_and_toy_involutions)  
**Record:** [Zenodo 23114044](https://zenodo.org/records/23114044)

## In brief

A worked example with inconsistent differences on a small graph. A proposer supplies a candidate potential; the host checks a declared predicate before changing accepted state.

## What it covers

- Weighted absolute residuals measure a proposed potential; a separate quotient minimum measures the inconsistency of the fixed edge data. The paper derives how they relate.
- Matching primal and dual witnesses, and a proof of the weighted cycle formula.
- Shows that strict rational descent alone does not guarantee termination.
- A paper-local Python reference builds and checks the full certificate on small graphs.

## Reading and running it

Start with the package [README](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/papers/001_pfp_discrete_cochain_retraction_and_toy_involutions/README.md), which lists the manuscript, claim ledger and change log.

**Related code:** [pfp package](PFP-Package.md)

---

Previous: [Paper 000](Paper-000.md) · [Papers](Papers.md) · Next: [Paper 002](Paper-002.md)
