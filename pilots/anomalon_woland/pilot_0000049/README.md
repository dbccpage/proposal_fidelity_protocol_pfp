# Pilot 24 — bounded mock check/repair

Expansion experiment **3/100**. Question: can a bounded checker reject schema-valid wrong replies, accept a supplied correction, and stop at its limit?

The task is integer addition with an explicit `task_id`. Operands are in `[-1000,1000]`; replies are strict typed answers or explicit abstentions. Booleans, numeric strings, unknown fields and duplicate JSON keys are not answers. A matching task ID is a data check, not authentication or action authority.

The caller supplies up to four raw JSON reply strings, each at most 2048 codepoints, and an attempt limit of 1–3. The runner checks at most that prefix, stopping immediately on the first correct answer. Malformed replies, wrong-task replies, wrong values **and abstentions consume an attempt**. Abstention is not successful and does not terminate the sequence: a later supplied correction may still pass. A short sequence stops at `sequence_end`; a used-up limit stops at `attempt_limit`. No later reply is parsed or counted as a mock call. The outer job's type/length constraints are still validated in full.

The default sequence supplies 41, then 42 for `19 + 23`. The expected result is `ACCEPTED`, answer 42, two mock calls and zero provider calls/cost. This is a deterministic mock experiment, not evidence that a model learns, improves or generates its own correction.

From the repository root:

```powershell
py -3.12 -B omega_engine_woland/tests/pilots/pilot_0000049/run.py
py -3.12 -B omega_engine_woland/tests/pilots/pilot_0000049/check.py
```

`run.py --input <job.json>` accepts a UTF-8 JSON job up to 32768 bytes; `--yaml` changes the runtime output format. Exit codes: 0 accepted answer, 1 bounded exhaustion, 2 invalid job or input error. The JSON/YAML example files contain the same job; YAML input is not a CLI feature.

The one scoped test file covers signed arithmetic, strict reply types, corrected replies, abstention, early stopping, exact limits, untouched input and CLI behavior. Five compiled mutations remove the value/task gates, promote abstention, ignore the limit or disable early success. `check.py` runs that file with isolated temporary storage and plugin autoload disabled, requires at least 98% coverage of **run.py only**, and writes compact logs, JUnit, coverage and the actual default CLI output to a temporary directory removed afterwards, or to a new directory named by `--out`. A failed gate prints `{"status":"FAILED","reason":...}` and exits 1. The checker script is test orchestration, not additional runtime production code.

`check.py` prints the current test count and coverage. Batch adversarial review is pending. The retained first run had one incorrect test expectation about invalid Unicode; the corrected test checks its outer-job refusal. Production code did not change between runs.

Local inspiration, not imported implementations or standards: [PFP prompt boundaries](../../prompts/README.md), section 1; [Level 98](../../levels/level_98_differential_checking.md), section 2's separation of candidate generation, syntax checks and deterministic checking. This pilot implements neither Level 98's Rust referee, dual-engine independence nor its eight-turn protocol. No workflow activation, adversarial batch-review completion, physical or formal theorem claim is made.
