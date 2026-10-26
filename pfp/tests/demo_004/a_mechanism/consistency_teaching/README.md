# Consistency teaching task

AuthorityEffect: None.

This is the original task used by Education's `naked_prompt_launder.py` scene:
integer rank-difference constraints, clean or poisoned graph generation, exact
potential propagation, and direct/CoT verdict prompts. It is not a new challenge
or a model-performance certificate. Transport and recording belong to
`omega_engine_pfp.infrastructure.consistency_teaching`; video display remains in
Education.

The original files remain in Git at
`bc42aa0a7156fcdf2122f0c8c43a52268e9eac84`, immediately before the deleted benchmark.

| Original Git path | SHA-256 of original bytes |
| --- | --- |
| `bench/head_to_head/tasks.py` | `562315f08f9298354c1e1bec05e10a1bf692ac1872fce5d2b9d04301ea4b36a7` |
| `bench/head_to_head/conditions.py` | `933572840c3639b38bb110c755244e51777a784b39b3fc0e3cc9fb3f7fdef82e` |
| `bench/head_to_head/host.py` | `efad1238f7e4a05712a581c174e8d749255f853fb45a28af23f31cd91e42e437` |

Current generator and condition modules use package-relative imports. The used
`host_verdict` function retains the original exact algorithm; the unused
exponential `phi1` minimizer and its import-time paper-path discovery remain only
in the original historical source. No alternate minimizer is substituted.

The parser accepts a whole verdict or the required final verdict line; other
prose remains `UNKNOWN`. A PFP-valid wrong answer is still wrong under this host.
Recovering the task and testing synthetic replies does not reproduce an old
provider response, prove a universal LLM failure, or measure PFP improvement.

See [current recording and offline rendering](../../../../../omega_engine_education/documentation/004_oepfp/docs/17_runtime_ownership_and_replay.md#consistency-teaching-scene-through-pfp).
