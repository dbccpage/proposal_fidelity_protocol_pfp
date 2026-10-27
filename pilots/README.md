# Pilots

Experiments that ran language models against a task. Unlike [`demos/`](../demos/README.md),
these need a model and the private runtime (the `adversary`, `operations` and
`operating_system` packages), which are not published here, so their tests do
not run in this repository. They are kept for their task definitions, cases
and checkers, and as the record of what was tried. Live runs happen in the
private repository.

Model scores from these runs are exploratory. Where a pilot's notes and a paper
in `papers/` disagree, the paper is authoritative.

## `llm_mechanism/`

Experiments on how a model attends, decodes and spends compute.

| Folder or file | What it tried |
| --- | --- |
| `c001_attention_distractor_mask/` | Masking attention to distractor keys at task level, with a McNemar comparison of arms (needs a local model with attention hooks) |
| `c005_hosted_decode_controls/` | A bake-off of hosted decoding controls (budgets, scratchpads, hybrids) on checkable cases |
| `consistency_teaching/` | Rank-difference constraint tasks, clean or poisoned, with direct and chain-of-thought prompts; used by an Education scene |
| `derivation_dag_pfp_staged_benchmark.py` | One-shot versus staged derivation certificates on slices of the finite-QM derivation graph |
| `finite_qm_derivation_pfp/` | Operad mining, prompt compilation and gate checks for a multi-stage finite-QM derivation campaign |
| `planned/` | Eight write-ups (C002 to C004, C006 to C010) for mechanism experiments that were planned but never built |

`pfp/infrastructure/challenge_execution.py`, `pfp/infrastructure/consistency_teaching.py`
and the challenge suite under `ops/adversary/tests/pilots/` import from here.
