# First live QM workflow pilot — November 10, 2026

**None of the six attempts produced a complete solution.** The first five recipes and one targeted repair scored 1–13/100. Five final answers exhausted their output limits; the untruncated fixed-panel v1 response described a solution without providing it. All four panel attempts failed their artifact contract, so none reached a useful rational-claim check.

| Plan | Reviewed score /100 | Recorded model cost | Input / output tokens | Wall seconds | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| `direct` | 1 | $0.001239 | 432 / 4,000 | 83.5 | Truncated |
| `self_critique` | 7 | $0.002840 | 4,882 / 8,000 | 176.6 | Truncated |
| `rational_blind_panel_v1` | 13 | $0.001337 | 2,708 / 3,641 | 126.0 | Truncated; invalid artifact |
| `rational_visible_panel_v1` | 8 | $0.001746 | 5,727 / 4,100 | 92.4 | Truncated; invalid artifact |
| `rational_fixed_panel_v1` | 3 | $0.000202 | 1,366 / 262 | 6.6 | Prose non-solution; invalid artifact |
| `rational_fixed_panel_v2` | 10 | $0.001034 | 1,485 / 3,000 | 113.2 | Truncated; invalid artifact |

Total recorded OpenRouter cost: **USD 0.008398**. Amounts conservatively round each reported call charge up to the next microdollar. The first five runs shared a USD 0.50 campaign ceiling; the separate exploratory repair had a USD 0.10 ceiling. Every run remained below the user's USD 0.10 cap, all accounts settled, and there were no retries or paid judges. These amounts are provider-run costs, not the cost of the repository audit or coding work.

## What actually happened

- Direct solving spent its output budget in contradictory tensor-product calculations.
- Self-critique returned a different, incorrect Hamiltonian and also stopped before finishing the spectrum section.
- The blind and visible panels retained partial spectrum work with algebraic errors; later requested sections were missing.
- Fixed-panel v1 returned a nested wrapper and a promise of a derivation rather than a mathematical answer.
- Fixed-panel v2 clarified the five root JSON fields and allocated answer length. It began with the intended fields but still truncated mid-answer and made a Hamiltonian coefficient error. This repair did not establish an improvement.

The original instructions and failures remain frozen. V2 is a revision of the fixed-panel implementation, not a new mathematical mechanism. It was selected from operational failures before its grading; no reference answer or evaluator correction entered a provider request.

## How to interpret the comparison

All runs used the exact committed QM seed and `qwen/qwen3-30b-a3b-instruct-2507` through `siliconflow/fp8`. The five original runs were shuffled before dispatch. Controls allowed 4,000 output tokens per call; panel solvers allowed 3,000 and model challengers 1,500. Sampling parameters used endpoint defaults. These are recipe-level observations with unequal total token allowances, not a matched-resource causal comparison.

An independent evaluator derived criteria from the public seed, froze a 100-point rubric before reading outputs, and reviewed the final retained text after execution. Readable mathematics received partial credit even when JSON was invalid; intermediate drafts and challenges received none. The parent reviewer checked key counterexamples and grade bindings. Scores are a documented mathematical assessment, not a formal proof or an independent human evaluation. The original private answer key was not accessed. One evaluator metadata inspection over-expanded intermediate context; that material was excluded from scoring, so this was not a fully blinded evaluation.

The rubric allocates spectrum20, dynamics20, pure entanglement25, thermal entanglement25 and checks10. Detailed criterion evidence, omissions, counterexamples and hash bindings are retained locally in `dag/benchmark/pilot_20261110/grades.json`, `criterion_evidence.json`, `evaluation.md` and `evaluation_validation.json`. The implementation is available in [draft PR #58](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/58); raw run artifacts remain in the working checkout and are not yet on main.

One sample per recipe cannot establish a reproducible ranking. In particular, partial scores of 7 or13 versus1 do not show that self-critique or panels solve the task reliably. Passing the 121 focused software tests established useful runner properties, but did not establish model quality. The panel's rational-only language also cannot directly check most of this QM task.

## Next useful experiment

Keep a direct baseline, test a model/response budget that can finish the task, and require small typed intermediate artifacts with public mathematical checks before a final synthesis. Compare those changes at matched resources with repeated samples. Prioritize complete answers and checks that expose the observed Hamiltonian errors before expanding workflow permutations or performing more peripheral source review.

Return to the [benchmark](Workflow-QM-Benchmark.md), [controls](Workflow-QM-Controls.md), or [panel implementations](Workflow-QM-Rational-Panels.md).
