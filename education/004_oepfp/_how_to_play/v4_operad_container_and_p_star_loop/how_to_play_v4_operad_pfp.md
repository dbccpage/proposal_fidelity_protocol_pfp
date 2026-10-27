# Use the finite-QM prompt, stages and mode

AuthorityEffect: None. The commands here are offline; they make no provider calls.
Run from the repository root with the repository dependencies installed.

## The actual template

Open [prompt_template.yaml](../../../../../pfp/infrastructure/yaml/prompts/finite_qm/prompt_template.yaml).
It contains the system prompt and a user prompt with target and stage-instruction
slots. [workflow.yaml](../../../../../pfp/infrastructure/yaml/prompts/finite_qm/workflow.yaml)
supplies the six stages; [mode.yaml](../../../../../pfp/infrastructure/yaml/prompts/finite_qm/mode.yaml)
supplies the derivation mode and LLM techniques. No registry is appended.

For manual research, use the system prompt, supply the target and sources, and
follow P0 mine, P1 derive, P2 check, P3 repair when necessary, P4 challenge and
P5 record. A completed derivation needs an actual witness, counterexample or
precise mathematical obstruction, not a restatement of the workflow.

## Prepare a bound derivation request

The included [work unit](../../../../../pfp/fixtures/finite_qm_workflow/c4_work_unit.json)
is an exact C4 precursor example. Its sought certificate is withheld and its
quantum-interface imports remain open.

```powershell
py -3.12 -m pfp.entrypoints.cli.finite_qm_prompt prepare `
  pfp/fixtures/finite_qm_workflow/c4_work_unit.json `
  --source-root . --attempt derivation-1 --stage P1_DERIVE
```

The result contains `system`, `user`, `response_schema` and `binding`. The user
prompt is populated from the actual target, selected stage and four mission
slots. `PROMPT_PREPARED` means no checker or model has run. The optional old
`--compact` flag is compatible but unnecessary: every request uses selected
operations, and none uses the registry dump.

Submit those system/user strings through an existing admitted provider adapter,
or use them manually. Save the original completion bytes. If a schema is supplied,
request exactly that schema; ordinary research without a schema uses the readable
mathematical answer structure in the system prompt.

## Check and repair

Build or locate the existing native host, using `CORE_SYMBOL_GAME_HOST` when it
is built outside its normal discovery path. Then check the submitted bytes:

```powershell
py -3.12 -m pfp.entrypoints.cli.finite_qm_prompt check `
  pfp/fixtures/finite_qm_workflow/c4_work_unit.json reply.json `
  --source-root . --attempt derivation-1 --stage P1_DERIVE
```

A repair request retains the public problem and uses a new attempt ID with the
appropriate bounded failure code, for example:

```powershell
py -3.12 -m pfp.entrypoints.cli.finite_qm_prompt prepare `
  pfp/fixtures/finite_qm_workflow/c4_work_unit.json `
  --source-root . --attempt derivation-2 --stage P3_REPAIR `
  --failure-code G3_WITNESS
```

P3 renders the replacement-certificate instruction and the fixed guidance for
that invariant. It cannot accept arbitrary feedback text containing an expected
answer. Check the repaired reply with the same P3/failure-code arguments used to
prepare it. Stage and feedback are bound into the task identity.

The focused compiler supports P1/P3 certificate turns. P0/P4/P5 are the research
workflow and use their own review/challenge/record contracts. Host-only P2 cannot
be dispatched as a model certificate turn. A full automatic live research runner
is not claimed by this delivery.

The shared Python API is `prepare_finite_qm_turn(unit, attempt_id=..., stage_id=...,
failure_codes=(...))`, followed by `turn.check(raw_bytes, judges=...,
require_checker=True)`. Reuse the existing provider reservation, custody and
replay owners for live work. A missing checker fails closed.

## Refresh the separate lookup catalog

```powershell
py -3.12 -m scripts.build_finite_qm_pfp_catalog `
  --qm-root C:\Users\a343o\source\repos\theory_of_finite_quantum_mechanics
```

This updates source inventory, the copyable system-prompt view, and the public
example. It does not append catalog records to the prompt. Review any source
changes before execution. Initial validation used the Python 3.13.11 repository
environment; the release recheck passed all 77 tests under Python 3.12.10.

Supports candidate-bound exact checking and staged prompting; does not establish
live efficacy or general QM closure. Narrowest claim: these commands prepare and
check this finite certificate. Next test: an unpaid finite-QM target with its own
independent mathematical judge.
