# pilot_0000047: typed span transport

Can a typed representation change preserve a declared executable answer while
keeping exact source spans and refusing incompatible composition?

## Status

Copied from the imported pilot estate. Offline tests only.

Left out: `reviewed_snapshot/` (hash-pinned frozen candidate), `examples/`
(self-hashed job twins that name old paths), the delivery script
`tests/typed_engine/verify_pilot.py` (it reads the snapshot), and the pinned
checker itself (`pilot_0000046` and its `pilot_0000042` core). The old bytes are
in git history at commit `90228464`. Schema files were renamed to lowercase and
regenerated from the models in `run.py`; no code opens them by name.

Without the pinned checker, `dependency()` refuses with `Pinned checker
unavailable`. The 54 tests that need the checker fail for that reason, as they
did in the source location. The 25 tests of wire rejection, recursion bounds,
reframing bounds and oversized or invalid input pass. The path strings that
rebuilt the historical checker bytes now say `the source repository`, so the
historical pin cannot be met until the checker is migrated and re-pinned.

## Mechanism

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

## Controls

- Positive: unchanged query under formatting, multibyte framing, identity and
  compatible triple composition.
- Negative: stale versions/spans, wrong types, missing edges or obligations,
  duplicate wire keys, and a valid target that keeps its summary but changes the
  answer. The latter must fail the answer comparison, not an unrelated hash check.
- Delivery replay targets 78 new tests and the 243 unchanged dependency tests,
  with 16 new and 35 reused compiled mutation controls. Reused tests are not new
  experiment counts. Coverage includes all three called project production
  modules; external library internals are outside that measurement.

## Run

From the repository root:

```powershell
python -m pytest workflows/wf16_substrate_crosswalk/pilots/pilot_0000047 -q -p no:cacheprovider
```

`python -B run.py --input <file> --format json` (or `yaml`) replays a supplied
job. The default output is `../pilot_output/pilot_0000047/<run-id>/`.

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
