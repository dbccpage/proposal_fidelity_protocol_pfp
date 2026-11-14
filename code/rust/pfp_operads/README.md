# pfp_operads

The operad host for PFP workflows, in Rust. A workflow hands it typed JSON; it
answers with one typed outcome. Nothing here calls a model, and no Python
checks anything. AuthorityEffect: None.

## What it checks

| Command | Question it answers |
| --- | --- |
| `pfp_operad check REQUEST.json` | Are the model's proposed operations typed by the canon's colours, and do the ones with a body give the host's expected answers? |
| `pfp_operad laws REQUEST.json` | Do these operations obey the operad laws on this panel of inputs? |
| `pfp_operad ledger append LEDGER.jsonl RECORD.json` | Is this record lawful? If so, add it to the failure ledger. |
| `pfp_operad ledger verify LEDGER.jsonl` | Has the ledger been edited, reordered or cut? |
| `pfp_operad ledger admitted LEDGER.jsonl` | Which learned rules may the next run load? |

Each command prints one JSON object with `"status"`: `PASS`, `FAIL` (the check
ran and did not hold) or `REFUSED` (the input was not acceptable). Exit code 0
is `PASS`, 1 is `FAIL` or `REFUSED`, 2 is a bad command line or unreadable file.

## Try it

From `code/rust`:

```
cargo run -p pfp_operads -- check pfp_operads/examples/check.json
cargo run -p pfp_operads -- laws pfp_operads/examples/laws.json
cargo run -p pfp_operads -- ledger append my_ledger.jsonl pfp_operads/examples/failure.json
cargo run -p pfp_operads -- ledger verify my_ledger.jsonl
```

## The pieces

- **Colours** are values of the canon's `prompt_colour` or `operad_colour`
  (`core_operad_canon`). Any other name is refused.
- **Operations** have ordered source colours, a target colour, an exact cost,
  a variant (`Planar` or `Symmetric`) and a body from a closed list:
  `identity`, `sum`, `product`, `difference`, `pack`, `sum_list`. No body means
  the operation is a signature only. Values are integers and lists; there is
  no float.
- **Laws**: sequential and parallel associativity, unit, "running a composite
  equals running its parts in order, and costs add", and declared symmetry.
  Each is checked on values, cost and tree shape over the panel.
- **Dispositions** for a proposed operation: `HOST_VERIFIED` (it has a body and
  every host check passed), `UNVERIFIED_CANDIDATE` (well typed, nothing run),
  `REFUSED`.
- **Failure ledger**: `failure` → `candidate` rule → `trial` on held-out cases
  → `admission` → optional `retirement`. A rule is admitted only on its latest
  trial, when it beat the baseline and fired on no clean case. Each entry
  carries the hash of the one before it.

## Limits

- A law pass covers the supplied operations on the supplied panel. It is not a
  proof for all terms; that belongs in Lean.
- The ledger checks that a trial's numbers are well formed and held out. It
  does not rerun the trial.
- Admission means "may be loaded", not "is correct".

Plan and status: [`docs/plans/operads_redesign.md`](../../../docs/plans/operads_redesign.md).
