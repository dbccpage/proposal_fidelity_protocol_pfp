# Pilots for WF20 (derivation loop with lift grants)

Moved here from the top-level `pilots/llm_mechanism/` folder on 2026-11-06.
They need a model and the private runtime, so their tests do not all run in
this repository.

| Folder or file | What it tried |
| --- | --- |
| `finite_qm_derivation_pfp/` | Operad mining, prompt compilation and gate checks for a multi-stage finite-QM derivation campaign |
| `finite_qm_derivation_pfp/theory_of_finite_qm_campaign/` | The finite-QM repository's retired prompt programme: generator, model ladder, batch runs and cohort scores |
| `derivation_dag_pfp_staged_benchmark.py` | One-shot versus staged derivation certificates on slices of the finite-QM derivation graph |

Python import path: `workflows.wf20_derivation_loop_with_lift_grants.pilots.<name>`.
