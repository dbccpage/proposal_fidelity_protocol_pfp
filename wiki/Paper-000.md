# Paper 000: The Symbol Game: a first game with S(n), MSS-N and basic packets

**Status:** Published preprint, v0.1.0 (2026-10-02)  
**Folder:** [`papers/000_pfp_introduction`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/papers/000_pfp_introduction)  
**Record:** [Zenodo 23108137](https://zenodo.org/records/23108137)

## In brief

The beginner's entry. A reader declares a few marks, asks for a distinction, proposes a relation and has an independent checker test a stated rule. A packet records the proposal; a receipt records the check and its limits.

## What it covers

- Separates a Genesis stage, an atlas entry (MSS-N) and an actual run of the game.
- Eight gradual examples: ground counts, observational separation, compact notation, consistent renaming, typed prompts and answers, scoped returned packets, bounded sessions and extension round trips.
- A standard-library teaching checker and a Jupyter workbook make every example replayable.
- Appendix A previews the advanced routes.

## Reading and running it

Start with the package [README](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/papers/000_pfp_introduction/README.md), which lists the manuscript, claim ledger and change log.

From the package folder, with plain Python:

```bash
python code/basic_packets.py
python code/lesson_packets.py
```

**Related code:** [pfp package](PFP-Package.md)

---

[Papers](Papers.md) · Next: [Paper 001](Paper-001.md)
