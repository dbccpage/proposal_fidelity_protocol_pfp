# Run Output Custody for `/adversary`

**AuthorityEffect:** `None`. Persistence records work and evidence; it does not
grant admission, prove a claim or authorize a provider call.

## Host Work Completion

For an ordinary `/adversary <request>`, use the host tools to finish the work, then
persist a concise report through the existing writer. The report can be practical
prose; the writer's `novella` name does not require fictional dialogue.

```bash
python -m adversary.entrypoints.cli persist-run --objective "Fix the parser and review error handling" --novella report.md --summary summary.json --work-status completed --no-digest
```

`--work-status` accepts `completed`, `partial` or `blocked`. It reports practical
completion, independently of the evidence verdict. `--verdict` defaults to
`OPEN_RESIDUAL`; completed code or prose need not establish a mathematical PASS.
Use `partial` for remaining requested work and `blocked` for a concrete obstacle.
Keep existing validation guards when supplying an explicit checker verdict.

The optional summary is a JSON object. Record observations, not desired results:

```json
{"work_status":"completed","artifacts":["path/to/changed_file.py"],"verification":[{"command":"<actual targeted command>","exit_code":0,"scope":"<what it checked>"}],"open_obligations":[{"claim":"<remaining claim>","next_step":"<deciding check>"}]}
```

Replace the example fields with actual results; omit checks that did not run.
Name real subagents only when they ran. A single agent's review perspectives are
not independent reviewers. `work_status` is descriptive metadata, not proof,
provider evidence, checker acceptance or authority. The native writer binds the
summary bytes in its existing receipt. Do not contradict reserved summary fields.

`--task-key` is optional; otherwise a unique key is generated. `--source` defaults
to `adversary_skill`; the Adversary agent may use `adversary_agent`. `--no-digest` leaves
the sealed run available for later digestion. Persistence failure is reported
separately from work completion; keep the artifact and do not invent a receipt.

## Windows worker temporary directories

Before starting a Python/native worker on a restricted Windows host, select an
existing writable absolute directory for both `TEMP` and `TMP`. Set them in the
same process or shell that starts the worker. Variables set by an earlier,
separate tool call do not configure a later worker process. The large-file native
bridge can require this even when smaller stdin requests already succeeded.

An access-denied checkpoint is an operational failure. Preserve its state and
raw failure, correct the worker environment, and retry reporting independently.
If a required action stopped the workflow, complete its retained finish before
explicit continuation; keep the failed action and spent allowances. Do not
reinterpret this failure as a mathematical defect or fabricate an accepting check.

## Destination and Bundle

Every `/adversary` and `/adversary-digests` run will write their output directly to `_ic/adversary/` and nowhere else:

```text
<durable repository>/_ic/adversary/runs/<task_key>/
```

The existing [root resolver](../../../../operating_system/adapters/intelligence_custody/intelligence_root.py)
uses `CORE_INTELLIGENCE_ROOT` when set, otherwise the main git checkout.
Outside git without that setting it returns `INTELLIGENCE_ROOT_UNRESOLVED`.
Canonical `_ic` routing needs no activation marker. Historical bindings and NARA
copies preserve old receipt resolution; historical receipt bytes are not rewritten.
A repeated task key is refused with `RUN_FOLDER_EXISTS`.

The [existing writer](../../../../adversary/use_cases/persistence.py)
seals these five bound files, plus the `mam/` story folder, and atomically
renames the completed bundle:

| File | Content |
| --- | --- |
| `uns.md` | The report or full captured narrative, verbatim. |
| `ddc.jsonl` | The single hash-chained DDA action tape, with sequence, parent, payload and record digest. |
| `uts.jsonl` | Ordered trace projection of the same history, referencing retained captures. |
| `summary.json` | Work metadata, evidence verdict, task/source identifiers and supplied results; native bouts also retain seat turns, candidate findings and evidence references. |
| `receipt.json` | Existing receipt schema, content-addressed ID, verdict, bound checker information, authority effect, file digests and DDA chain head. |

`mam/` holds `mam.md`, `mam.tex` and `mam.pdf`: a plain-English story, in the
manner of the source novel, retold only from the Panel's captured
words (`summary.json` and `ddc.jsonl`). It is our own wording, not a quotation
of any translation, and it is not evidence. The receipt records
`mam_schema_version` and the three digests; readback re-renders the story and
refuses any byte that differs. The story is outside the receipt identity, so
earlier folders without `mam/` still verify. The `.tex` is supplied, not
compiled; the PDF comes from a built-in deterministic writer.

New bundles use `core.adversary.reported-run-bundle.v2`. DDA records live once in
`ddc.jsonl`; no separate `dda*` file is emitted. This storage consolidation does
not add DDC procedure steps or mathematical acceptance. Teamwork summaries retain
references to their existing checked DDC procedure. The `--novella` and
`--dda-actions` input options remain compatible aliases.

Historical five-file and six-file bundles retain their original `novella.md`,
`dda_actions.jsonl`, digests and readers, including the old byte-identical DDC
copy. Do not rename frozen files or rewrite receipts. Skill runs retain their
`core.adversary.skill-run-receipt.v1` receipt identity independently of the new
bundle layout. Outputs exist only after the writer succeeds (CLI exit `0`).

## Explicit Paid Native Bouts

Use `/adversary run-live <arguments>` only for an authorized paid native run. It
invokes `python -m adversary.entrypoints.cli run-live` with the same
arguments. Ordinary host work does not enter this path automatically.

```text
/adversary run-live --template /operator/deployment/live_config.json --objective "Check the supplied finite case" --task-key fresh_task_001 --max-cost-microusd 500000 --max-output-tokens 8192 --native-host-sha256 <reviewed-sha256> --signing-key /operator/existing_key --reviewer operator --scene-plan adversary/config/scene_plan_example.json
```

The [operator guide](../../../../adversary/documentation/live_cli.md) describes
the configured roles, case, routing, native pin and external signature. `run-live`
prepares and signs a fresh request; `--prepare-only` signs without dispatch.
An already prepared request can use `run-bout --live --live-config <path>
--no-digest`. No path reuses a prior signature or silently falls back to fixtures.
Scene fallback retains failures and paid spend; skill attachments come from the
same signed typed plan. `--fixture` is explicitly a local fixture run.

A native bout refused after its first seat turn retains a separate
`<task_key>--refused-<digest>/` bundle, including seat turns, refusal and act reached.
It never overwrites an existing run. A refusal before any turn writes no bundle.
Report the actual persisted path, failed replies and costs when observed.

## Checker Evidence

`PASS_TO_MASTER` needs a real receipt stating `ACCEPTED` and binding the exact
candidate. A native bout additionally needs the native terminal authorization
checks. Routine work completion does not require or imply that verdict.

```json
{"verdict":"ACCEPTED","candidate_content_sha256":"sha256:<64 lowercase hex>","checker_id":"c1_exact_checker"}
```

```bash
python -m adversary.entrypoints.cli persist-run --objective "Solve case c1" --novella report.md --work-status completed --verdict PASS_TO_MASTER --checker-receipt checker_receipt.json --no-digest
```

A supplied receipt with `REFUSE` must state `REJECTED`; `OPEN_RESIDUAL` may cite
any well-formed receipt. A bare hash is insufficient. A reference scored by its
own checker uses `REFERENCE_SELF_CONSISTENT` or `REFERENCE_SELF_INCONSISTENT`,
not `PASS_TO_MASTER`. Fixture and ablation results never authorize.

## Optional Action Rows and Failures

`--dda-actions actions.jsonl` (also `--ddc-actions`) accepts JSON objects, including
failed candidates and abandoned routes. Use only observed actions:

```json
{"actor":"Defect Hunter","action":"Found an unhandled malformed input"}
{"actor":"Primal Dual","action":"Repaired the parser and replayed the boundary check"}
```

The optional `letter` must be `E R C I Λ D M T` (`Lambda` also means `Λ`). No DDC
letter or imaginary dramatic act is needed for an ordinary action record.

CLI exit `2` reports a typed refusal. Blank inputs, unreadable files, malformed
action rows or summaries, unknown DDC letters, reserved summary conflicts,
missing/malformed/mismatched checker receipts and an existing run folder retain
their existing refusal codes. Keep the completed source artifact and report the
actual failure; do not relabel a failed writer or checker as a successful run.
