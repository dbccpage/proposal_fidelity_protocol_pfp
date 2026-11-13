# Idea packs

AuthorityEffect: None.

Five scenario packs in the `pfp-lab.scenario.v1` format. Each one is a small,
exact demonstration of one idea about claims on a graph. They contain no code.

| Pack | Idea |
|---|---|
| `arbitrage-cycle` | Price gaps quoted around a loop that do not sum to zero leave a nonzero obstruction. Retracting to before the stale quote and asserting a fresh one removes it. |
| `ledger-reconciliation` | Two ledgers disagree around a loop. The obstruction is the mismatch times the weight of the least trusted entry, and a relational CUT that edits only that entry reaches zero. |
| `every-edge-not-all` | Every claim on an odd loop can be met by some assignment, but no single assignment meets all three. |
| `cheapest-repair` | Fitting a section that puts the whole mismatch on a heavy edge is refused, since the defect would rise. Putting it on the lightest edge is admitted. |
| `retract-stale-claim` | A revision breaks consistency. RETRACT restores the state saved at the last consistent step, and both steps stay in the receipt. |

They are listed by `pfp-lab packs` and run like any built-in pack:

```bash
python -m pfp_lab.cli.main run --pack arbitrage-cycle
```

`pfp_lab/tests/test_packs.py` checks the outcome each title states.
