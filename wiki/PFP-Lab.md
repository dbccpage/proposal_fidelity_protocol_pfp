# PFP Lab

PFP Lab is a small tool for trying ideas against the protocol: you load a
scenario of claims on a graph, apply operations, and watch the obstruction and
the receipt change. It is under active development, and only its scenario packs
are on `main` so far.

## Operations

| Operation | What it does |
| --- | --- |
| ASSERT | Add or change a claim on an edge |
| CUT | Edit claims to remove an inconsistency; refused if it would raise the defect |
| VERIFY | Recompute the obstruction independently and record it |
| RETRACT | Restore the state saved at the last consistent step |

Every step, admitted or refused, stays in the receipt.

## Idea packs

Five example scenarios live in
[`pfp_lab/core/packs/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_lab/core/packs).
Each is a small, exact demonstration of one idea.

| Pack | Idea |
| --- | --- |
| `arbitrage-cycle` | Price gaps around a loop that do not sum to zero leave an obstruction; retracting the stale quote and asserting a fresh one removes it. |
| `ledger-reconciliation` | Two ledgers disagree around a loop; a CUT that edits only the least trusted entry reaches zero. |
| `every-edge-not-all` | Every claim on an odd loop can be met alone, but no single assignment meets all three. |
| `cheapest-repair` | Putting the whole mismatch on a heavy edge is refused; putting it on the lightest edge is admitted. |
| `retract-stale-claim` | A revision breaks consistency; RETRACT restores the last consistent state. |

Once the Lab's command line is merged, a pack runs as a file:

```bash
python -m pfp_lab.cli.main run pfp_lab/core/packs/arbitrage-cycle.json
```

## Planned front ends

The Lab is designed as one Python core with three front ends: a command line, a
local web page and a desktop app, all speaking to the same core so that results
agree. This page will be updated as those pieces land.
