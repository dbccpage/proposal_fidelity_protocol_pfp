# Paper 005: PFP V: A practitioner's guide to checked proposals

**Status:** Published preprint, v0.1.0 (2026-10-02)  
**Folder:** [`papers/005_pfp_practitioners_field_manual`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/papers/005_pfp_practitioners_field_manual)  
**Record:** [Zenodo 23114578](https://zenodo.org/records/23114578)

## In brief

A hands-on workflow on a three-edge directed graph with exact rational claims (1,1,1) and weights (1,2,3), whose weighted minimum of three can be checked by hand.

## What it covers

- Separates minimising the residual of unchanged claims from admitting a consistent replacement.
- Follows refusals and the restoration of a saved state.
- A Landau-style quiz (32 questions in eight levels), study guide and executable capstone.
- No new theorem or model-performance result is claimed.

## Reading and running it

Start with the package [README](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/papers/005_pfp_practitioners_field_manual/README.md), which lists the manuscript, claim ledger and change log.

From the package folder, with plain Python:

```bash
python code/play_demo.py
python code/study_capstone.py
```

**Related code:** [pfp package](PFP-Package.md)

---

Previous: [Paper 004](Paper-004.md) · [Papers](Papers.md) · Next: [Paper 006](Paper-006.md)
