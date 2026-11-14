# pfp_operads

The operad host for PFP workflows, in Rust. A workflow hands it typed JSON; it
answers with one typed outcome. Nothing here calls a model. WF1 to WF5 call it
through `pfp/infrastructure/operad_host.py`, which carries the request and the
outcome and decides nothing. AuthorityEffect: None.

## What it checks

| Command | Question it answers |
| --- | --- |
| `pfp_operad check REQUEST.json` | Are the model's proposed operations typed by the canon's colours, and do the ones with a body give the expected answers the request lists? |
| `pfp_operad run REQUEST.json` | Does a reply's candidate, run by the host on the task's own input, give the result of the host's judge? The request carries no expected value. |
| `pfp_operad envelope REQUEST.json` | Does a full-slot reply (WF2 to WF5) report every slot once, and do its operad candidates and DDC moves quote real sources and cite known things? Which candidates are typed by the canon, and which have the licensed operation's signature? |
| `pfp_operad judge REQUEST.json` | Does the reply's task result equal the host's own exact answer? (Integer sum, on unbounded integers.) |
| `pfp_operad mining REQUEST.json` | Is a mining reply (WF3 to WF5) free of digits outside its source quotes, are its candidates well formed and grounded, and does its guidance cover every grounded slot? |
| `pfp_operad grounding REQUEST.json` | Do the grounded slots of a solver reply restate the task's public input exactly, and name a licensed candidate? |
| `pfp_operad typing REQUEST.json` | Which candidates in a list are typed by the canon, and which have the licensed signature? |
| `pfp_operad reuse REQUEST.json` | Which emitted candidates have the signature of a mined candidate? |
| `pfp_operad witness REQUEST.json` | Is this answer a failure? The host judges it itself and, if it is wrong, writes the failure record for the ledger. |
| `pfp_operad trial REQUEST.json` | How did a rule do on held-out cases? The host judges each baseline and treated answer and writes the trial record. |
| `pfp_operad witness-turn REQUEST.json` | Did this stored turn of a WF1 to WF5 run fail? The host reads the turn's `task.json` and `receipt.json` itself, judges the task result and writes the failure record, named after its case. |
| `pfp_operad repair SOURCE_DIR RUN_DIR REQUEST.json` | Does a supplied patch make the failing checks pass without breaking a passing one? The host copies the declared sources to a new run folder, runs the request's check commands before and after the patch, and keeps a record. The sources are never written. |
| `pfp_operad version` | Which host and which canon is this? Workflows record it in every run. |
| `pfp_operad laws REQUEST.json` | Do these operations obey the operad laws on this panel of inputs? |
| `pfp_operad ledger append LEDGER.jsonl RECORD.json` | Is this record lawful? If so, add it to the failure ledger. |
| `pfp_operad ledger verify LEDGER.jsonl` | Has the ledger been edited, reordered or cut? |
| `pfp_operad ledger admitted LEDGER.jsonl` | Which learned rules may the next run load? |
| `pfp_operad ledger load LEDGER.jsonl REQUEST.json` | What seed does a run load? The task's seed with the admitted rules written after it, and the same seed byte for byte when there is none. |
| `pfp_operad ledger loaded LEDGER.jsonl REQUEST.json` | Is this seed exactly what the ledger loaded onto that base seed, at that ledger state? |
| `pfp_operad ledger trial LEDGER.jsonl REQUEST.json` | How did a rule do on paired stored turns? A pair counts only when both turns are the same case and their seeds differ by exactly the rule under trial. |

Each command prints one JSON object with `"status"`: `PASS`, `FAIL` (the check
ran and did not hold) or `REFUSED` (the input was not acceptable). Exit code 0
is `PASS`, 1 is `FAIL` or `REFUSED`, 2 is a bad command line or unreadable file.
Two commands write: `ledger append` adds one line to a ledger, and `repair`
fills a run folder that must not exist yet. `repair` is also the only command
that starts other programs: the checks its request names.

## Try it

From `code/rust`:

```
cargo run -p pfp_operads -- check pfp_operads/examples/check.json
cargo run -p pfp_operads -- envelope pfp_operads/examples/envelope.json
cargo run -p pfp_operads -- judge pfp_operads/examples/judge.json
cargo run -p pfp_operads -- mining pfp_operads/examples/mining.json
cargo run -p pfp_operads -- grounding pfp_operads/examples/grounding.json
cargo run -p pfp_operads -- laws pfp_operads/examples/laws.json
cargo run -p pfp_operads -- witness pfp_operads/examples/witness.json
cargo run -p pfp_operads -- trial pfp_operads/examples/trial.json
cargo run -p pfp_operads -- run pfp_operads/examples/run.json
cargo run -p pfp_operads -- witness-turn pfp_operads/examples/witness_turn.json
cargo run -p pfp_operads -- ledger load ../../workflows/wf55_failure_ledger_with_trial_gated_rules/examples/ledger_after_first_run.jsonl pfp_operads/examples/load.json
cargo run -p pfp_operads -- ledger loaded ../../workflows/wf55_failure_ledger_with_trial_gated_rules/examples/ledger_after_first_run.jsonl pfp_operads/examples/loaded.json
cargo run -p pfp_operads -- ledger append my_ledger.jsonl pfp_operads/examples/failure.json
cargo run -p pfp_operads -- ledger verify my_ledger.jsonl
```

The repair example's two checks are the host itself (`pfp_operad judge` on a
stored answer), so the binary must be on `PATH`:

```
cargo build --release -p pfp_operads
PATH="$PWD/target/release:$PATH" pfp_operad repair pfp_operads/examples/repair/source my_run pfp_operads/examples/repair/request.json
```

It prints `PASS` with `"outcome":"REPAIRED"`, check exits `[1, 0]` before the
patch and `[0, 0]` after it, and leaves `request.json`, `candidate.patch`,
`record.json` and the patched `workspace/` in `my_run`.

## The pieces

- **Colours** are values of the canon's `prompt_colour`, `operad_colour` or
  `task_value_colour` (`core_operad_canon`). Any other name is refused.
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
- **Host-written records**: `witness` and `trial` judge the answers they are
  given and return the record to append, so a workflow never states that a
  reply failed or how a trial went. A failure's DDC word is the reply's own
  word followed by `M`, the host's refusal. A clean-panel hit is a held-out
  case the baseline answered correctly and the treated run did not.
  [WF55](../../../workflows/wf55_failure_ledger_with_trial_gated_rules/README.md)
  runs the whole loop.
- **Stored turns**: every WF1 to WF5 run keeps each model turn as a folder
  with `task.json` and `receipt.json`. `witness-turn` and `ledger trial` take
  those two files as they are and find the checker, the public input, the
  task result and the DDC moves themselves. A failure from a stored turn is
  named `c<16 hex>@<run>`, where the hex is a hash of the checker and the
  case's integers. The ledger refuses a trial whose held-out case is the case
  of a failure the rule came from, whatever the run or the task id.
- **Loaded seeds**: `ledger load` is the only place a seed gets its rules. It
  appends one line per rule under a line naming the first 16 hex digits of
  the ledger's head hash. A rule whose id or constraint has a line break is
  refused, so a rule cannot forge another rule's line. `--on-trial`
  (`"on_trial"` in the request) adds one proposed rule for the treated arm of
  its trial. `python -m pfp.workflows.failure_ledger` carries run folders and
  task files to these commands.
- **Candidates the host runs**: `run` takes candidates typed by
  `task_value_colour`, each with a body from the closed list, and the public
  input of one or more cases. A candidate's inputs take a case as one
  `IntegerList` or as one `Integer` per value. The host runs the body and
  compares with its judge: `HOST_VERIFIED` when it agrees on every case,
  `REFUSED` when it is ill typed or differs on one, `UNVERIFIED_CANDIDATE`
  when it has no body or does not fit. The outcome is `PASS` when at least one
  candidate is verified and none is refused.
  [WF56](../../../workflows/wf56_host_run_operad_candidates/README.md) uses it.

- **Bounded repair**: `repair` takes one supplied patch through six stages.
  `C` capture reads the declared sources, compares each SHA-256 and makes a
  working copy. `R` observe runs every check for a baseline. `E` evaluate
  applies the patch to the working copy and runs the checks again. `I`
  incorporate decides whether the candidate is at fault. `M` disposition
  compares the failing checks before and after. `T` terminal confirms the
  sources still have their declared hashes. The outcome is `REPAIRED`,
  `PARTIAL`, `INEFFECTIVE`, `REGRESSION`, `NO_REPAIR_NEEDED` or `REFUSED`; only
  `REPAIRED` is a `PASS`. The record's `trace` lists the stages that took
  effect, `CREIMT` for a full run.
- **A repair request** is closed JSON: `run_key`, `objective`, `sources` (path
  to SHA-256), `write_paths`, `checks` (`check_id`, `argv`, optional
  `timeout_seconds` up to 60, default 20), `candidate_patch` and an optional
  `workflow` name. The candidate id is the SHA-256 of the patch; the request
  digest covers the whole request; the case name covers the sources and the
  checks, so two patches for one task share a case.
- **Patches** are unified diffs of existing text files with `a/` and `b/`
  paths. A hunk applies at the line it names, with no offset or fuzz, and only
  to a file in the write set. Creating, deleting, renaming or re-moding a
  file, and binary data, are refused.
- **Checks** are commands the operator trusts. Each runs in the working copy,
  without a shell, with closed input, a deadline, and Git and Python cache
  variables removed. Exit 0 passes. A check that cannot start, overruns or
  rewrites a declared file refuses the run. Each output stream is hashed whole
  and its first 4096 bytes are kept.
- **A failed candidate is a ledger failure**: the record carries a `failure`
  for `ledger append` when the patch left a failing check failing
  (`CounterfeitExactness`), broke a passing one (`BoundaryLeakage`) or did
  not fit the sources or the write set (`StructuralNonFit`). A missing tool,
  a changed source or a full disk blames no candidate.

## Limits

- A law pass covers the supplied operations on the supplied panel. It is not a
  proof for all terms; that belongs in Lean.
- The ledger checks that a trial's numbers are well formed and held out. It
  does not rerun the trial. `trial` judges the answers it is handed; it cannot
  see whether the treated answers were produced with the rule loaded.
  `ledger trial` does check the stored seeds of both arms, but it trusts the
  stored `task.json` and `receipt.json`; the workflow's own `replay` is what
  ties those files to the reply bytes.
- A loaded rule is text in the seed. Nothing here shows that a model obeys it.
- Admission means "may be loaded", not "is correct".
- `envelope`, `mining` and `typing` never verify a candidate. A candidate's
  meaning is free text; the host can only say it is well formed, typed, and
  has the licensed signature.
- The digit screen in `mining` reads decimal digits in any script. It does not
  catch a number written in words.
- `run` verifies a candidate on the cases it is given, not on every input. It
  evaluates on 64-bit integers and refuses a case with a larger value.
- `repair` separates a working copy from the sources. It is not a sandbox:
  a check can do whatever the account running the host can. `REPAIRED` is a
  statement about the supplied checks; weak checks admit a wrong patch. The
  stage letters are spelled like DDC letters and are not the calculus; no
  descent law is claimed for the word. Nothing is applied to the sources,
  admitted or activated.
- `repair` notices a check that rewrites a declared file. It does not notice
  other files a check leaves in the working copy.
- When no check fails before the patch, the patch is not read or applied.

Plan and status: [`docs/plans/operads_redesign.md`](../../../docs/plans/operads_redesign.md).
