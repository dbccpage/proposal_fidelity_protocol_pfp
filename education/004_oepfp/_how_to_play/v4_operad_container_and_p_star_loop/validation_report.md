# Prompt-template revision: validation

AuthorityEffect: None. Revised 2026-10-18 after the initial registry dump was
rejected. The deliverables are now the actual
[prompt_template.yaml](../../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm/prompt_template.yaml),
[workflow.yaml](../../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm/workflow.yaml)
and [mode.yaml](../../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm/mode.yaml).

The renderer uses the new prompt and stage instructions. Six workflow stages
connect mining, derivation, host verification, repair, challenge and recording.
One derivation mode attaches six LLM techniques with activation conditions and
checks. The separate 584-entry catalog is never appended to a prompt.

Validation for this revision: **77 Python tests passed, zero failures or skips**,
including actual Python-to-native certificate checks. The controls cover
configuration links, stage transitions, technique references, derivation versus
repair bindings, whitelisted residual guidance, host-only stage refusal, absence
of the registry dump, strict ingress, source pins, native witness mutations and
a valid gauge transformation. No provider calls were made.

The native source is unchanged. Its 11 cochain-related Rust tests and host build
passed during the first revision; they were not rerun for these prompt/configuration
changes. Initial Python validation used the repository environment (3.13.11).
The release recheck passed all 77 tests under Python 3.12.10; its launcher works
outside the filesystem sandbox. General live effectiveness and a
new automatic six-stage provider runner are not claimed.

The [machine receipt](validation_receipt.json) lists the current file hashes and
exact test command. The [NO_LLM control bundle](c4_no_llm_control.json) contains
actual checks under the revised prompt binding. The broader workflow is a
research runbook; P1 derivation and P3 repair are integrated with the existing
shared task-turn boundary and offline CLI.

Supports: the requested usable prompt, stage/mode/technique configuration and
focused integration. Does not support: measured optimality or general QM closure.
Narrowest claim: these artifacts prepare and independently check the submitted
finite certificate. Next test: an unpaid finite-QM obligation with its own judge.
