# pfp_operads

The operad host for PFP workflows, in Rust. A workflow hands it typed JSON; it
answers with one typed outcome. Nothing here calls a model. WF1 to WF5 call it
through `pfp/infrastructure/operad_host.py`, which carries the request and the
outcome and decides nothing. AuthorityEffect: None.

## What it checks

| Command | Question it answers |
| --- | --- |
| `pfp_operad check REQUEST.json` | Are the model's proposed operations typed by the canon's colours, and do the ones with a body give the host's expected answers? |
| `pfp_operad envelope REQUEST.json` | Does a full-slot reply (WF2 to WF5) report every slot once, and do its operad candidates and DDC moves quote real sources and cite known things? Which candidates are typed by the canon, and which have the licensed operation's signature? |
| `pfp_operad judge REQUEST.json` | Does the reply's task result equal the host's own exact answer? (Integer sum, on unbounded integers.) |
| `pfp_operad mining REQUEST.json` | Is a mining reply (WF3 to WF5) free of digits outside its source quotes, are its candidates well formed and grounded, and does its guidance cover every grounded slot? |
| `pfp_operad grounding REQUEST.json` | Do the grounded slots of a solver reply restate the task's public input exactly, and name a licensed candidate? |
| `pfp_operad typing REQUEST.json` | Which candidates in a list are typed by the canon, and which have the licensed signature? |
| `pfp_operad reuse REQUEST.json` | Which emitted candidates have the signature of a mined candidate? |
| `pfp_operad version` | Which host and which canon is this? Workflows record it in every run. |
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
cargo run -p pfp_operads -- envelope pfp_operads/examples/envelope.json
cargo run -p pfp_operads -- judge pfp_operads/examples/judge.json
cargo run -p pfp_operads -- mining pfp_operads/examples/mining.json
cargo run -p pfp_operads -- grounding pfp_operads/examples/grounding.json
cargo run -p pfp_operads -- laws pfp_operads/examples/laws.json
cargo run -p pfp_operads -- ledger append my_ledger.jsonl pfp_operads/examples/failure.json
cargo run -p pfp_operads -- ledger verify my_ledger.jsonl
```

## The pieces

- **Colours** are values of the canon's `prompt_colour` or `operad_colour`
  (`core_operad_canon`). Any other name is refused.
- **Task value colours** (`task_value_colour`: `Integer`, `IntegerList`) type
  the candidates in a workflow reply. A candidate with another colour is
  reported as untyped; that alone does not fail the reply.
- **Licensed operations** are the ones a task's checker allows, by signature.
  `integer_sum_v1` licenses `integer_list_sum: IntegerList -> Integer`, and
  the judge runs it. A candidate whose stated arity disagrees with its source
  colours has no signature and is never licensed.
- **Grounded slots** are the slots a checker requires to restate public facts
  (`integer_sum_v1`: `concrete_spans`, `instantiated_arguments`,
  `parameter_bindings`, `preservation_obligations`). Mining guidance must
  cover them, and `grounding` rechecks them with exact integers.
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
- `envelope`, `mining` and `typing` never verify a candidate. A candidate's
  meaning is free text; the host can only say it is well formed, typed, and
  has the licensed signature.
- The digit screen in `mining` reads decimal digits in any script. It does not
  catch a number written in words.

Plan and status: [`docs/plans/operads_redesign.md`](../../../docs/plans/operads_redesign.md).
