# Claim ledger: Paper 034

| # | Claim | Scope | Checked by |
| --- | --- | --- | --- |
| 1 | WF1–WF5 are implemented offline-verified runners | This repository | `workflows/library/migration_validation.json`; `pfp/workflows` tests |
| 2 | WF6–WF23 are derived designs, not runners | This paper and `workflows/dag/` | No runner module exists for them |
| 3 | Each derived family cites the pilots it was read from | Pilot directory numbers in the source estate | `source_pilots` in `workflow_dag.json`, read 2026-11-05 |
| 4 | Pilots 52–187 are mostly planned capsules without reply bytes | Source estate | Each pilot's `README.md` "Disposition" line |
| 5 | Pilots 199–203 each ran five provider trials and twenty host stages | Source estate | Each pilot's `spec.yaml` and `README.md` |
| 6 | The graph is acyclic and every dependency precedes its dependant | `workflow_dag.json` | Generator assertion; node order |
| 7 | Seat counts: 23 Sonnet, 14 Opus, 13 Fable across WF6–WF23 | Team designs | Count over `team.roles` (variable seats as one) |
| 8 | The mathematical statements are standard results quoted as acceptance rules | Finite instances only | Not re-proved here |

No claim in this paper is a model-performance result.
