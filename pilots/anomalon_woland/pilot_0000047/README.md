# Pilot 000022: typed document-span transport

New-series experiment **1/100**, separate from the 21 migrated implementations.

## Question

Can a typed representation change preserve a declared executable answer while
retaining exact source spans and refusing incompatible composition?

This pilot binds eight nodes: source, source span, document, request span,
decoded request, checker, test and result. Its checker is the exact pinned
`pilot_0000046` implementation and that implementation's `pilot_0000042` dependency.
Inputs, reports and receipts have strict Pydantic models and JSON/YAML twins.

The permitted constructor changes document framing and JSON whitespace. Span
positions are UTF-8 byte offsets, not character indices. Each endpoint is checked
against the actual complete answer, including exact rational coefficients.
Composition requires the same typed intermediate graph version. Identity and
associativity are compared at canonical endpoint-and-span-map records; derivation
histories are deliberately not part of that equality.

## Controls and replay

Current replay prerequisite: the available `pilot_0000046` checker does not
match the frozen checker SHA. This dependency was already unavailable at the
pre-move revision `ad49ca44b04c39ba07427c9dc79a24695e1ccd52`. The corrected locator
now finds the checker and refuses `Pinned pilot21 changed`. Its historical pin
is preserved; the entry point below does not imply a fresh successful replay.

- Positive: unchanged query under formatting, multibyte framing, identity and
  compatible triple composition.
- Negative: stale versions/spans, wrong types, missing edges or obligations,
  duplicate wire keys, and a valid target that keeps its summary but changes the
  answer. The latter must fail the answer comparison, not an unrelated hash check.
- Delivery replay targets 78 new tests and the 243 unchanged dependency tests,
  with 16 new and 35 reused compiled mutation controls. Reused tests are not new
  experiment counts. Coverage includes all three called project production
  modules; external library internals are outside that measurement.

From the repository root, run:

```powershell
py -3.12 -B omega_engine_woland/tests/pilots/pilot_0000047/run.py
```

Pass `--input <file> --format json` or `--format yaml` to replay a supplied job.
Examples and generated schemas are colocated in `examples/` and `schemas/`.
The default output is `pilots/pilot_output/pilot_0000047/<run-id>/`.

The fresh worktree and main-checkout delivery records are respectively
`../pilot_output/pilot_0000047/verification_work1/replay.json` and
`../pilot_output/pilot_0000047/verification_main1/replay.json`, with YAML twins.
Raw commands, stdout, stderr, coverage and mutations are retained alongside them.
`candidate_history/` preserves earlier test evidence, including the failed first
test-harness attempt; it is not presented as a new delivery run.

## Scope

This is one finite interface and its executable controls, not a whole-engine
algebra, arbitrary semantic-equivalence decision, improved LLM reasoning,
physics result or Lean theorem. Preserving one declared query does not preserve
every possible query. Summaries, hashes and schema acceptance confer no authority.
No model/provider call occurs; cost is zero. Human adoption is separate.

Inputs are bounded for evaluation. Complete raw capture is streamed, but has no
total disk quota. Operational I/O failures can leave incomplete artifacts; a
completed receipt is not promised for an interrupted or failed write.
Ordinary input rejection uses a bounded public error excerpt and preserves the
complete diagnostic separately in `diagnostic.txt`, with its size and digest
bound into the rejection report and artifact hashes. The long-key regression
retains the original review failure and checks completion of this rejection path.

The frozen research candidate is retained in `reviewed_snapshot/`. Its file
manifest uses original repository-relative locations for historical custody;
the canonical delivery is separately bound by its fresh source pins and replay.
The inactive deep-researcher-v0.1 workflow is not activated by this pilot.

The current delivery pins were migrated during PR review after pilot_0000042
added source-fact checks and a location-independent output directory. Pilot_000021
now binds that exact source; this pilot binds the updated checker and core.
The JSON/YAML demonstration twins were regenerated from those dependencies.
Historical receipts and the frozen research snapshot retain their original pins.
Fresh dependency-tampering tests remain required for the current delivery.
