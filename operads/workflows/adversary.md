# Adversary Shared Work Workflow (WF_ADVERSARY)

**Entry point:** `/adversary <request>`
**AuthorityEffect:** `None`
**Document ID:** `OE-WF-ADVERSARY-001`
**Backend:** `adversary.use_cases.teamwork`
**Host guide:** [Adversary skill](../skills/adversary/SKILL.md)

## Frozen Full-Panel Orchestration

Before work and every worker spawn, read
[/auto-learn](../skills/auto-learn/SKILL.md), search relevant existing lessons and
put their paths/applicability into the worker brief. The actual worker reads them
before acting. Every new run requires all 22 governed Panel roles, with
source version, roster digest and stage order carried in state. A role name
is not an independent worker or a verification result.

The current IDE and Python use one coordinator. The IDE performs real edits,
tool calls and scoped delegation; the backend returns build, review and bounded
repair actions. Syntax Prefilter runs deterministic intake; four PFP intake roles prepare
Jeremy's build; fifteen PFP reviewers ending with Adversary preserve their findings;
Scar Chronicler supplies the final PFP learning contribution. Every reviewer runs
before bounded repair and again after repair. Temporary exchange paths suffice.

For ordinary software work, declare applicability before intake:

```bash
python -m adversary.entrypoints.cli teamwork start --objective "<request>" --state task.json --native-gate-scope adversary/config/software_gate_scope_v1.json --native-gate-policy require_pass --checker-id original-checker-v1 --checker-source checker.py --check-command python checker.py
python -m adversary.entrypoints.cli teamwork check --state task.json
python -m adversary.entrypoints.cli teamwork submit --state task.json --raw-reply reply.json
```

Read the returned `pfp_turn` system/user brief and response schema before
each model-authored action. Submit its actual response instance, preserving
the supplied task/attempt/input bindings. Build/repair answers are text;
review answers contain `summary`/`findings`; learning adds `lessons`.
All these roles use PFP; schema-only prose remains UNVERIFIED.

Run each returned `native_gates` action with `teamwork native-gates --state task.json`.
V4 checks intake, pre/post acceptance and post learning. Retain raw process bytes,
source-bound receipts and native residuals. Diagnostic attempts are distinct from
admitted edges; default diagnostics do not grant authority. `require_pass` stops
on any required non-PASS. Keep task-specific scientific gates when needed;
excluded/deferred gates are listed explicitly, never passed by omission. Select
the native host/witness policy before `--check-command`;
see the shared workflow guide for the exact binding options.

Give each model worker the exact prepared system/user/schema and consume its
actual bound raw reply. `--result` alone is refused; use separate `--host-result`
artifact readback alongside raw replies, or dedicated host commands. IDE billing
is unavailable and Python cannot intercept the host's hidden model transport.
Python callbacks undergo the same retained-byte replay as CLI submissions.
Historical v1/v2/v3 states retain their original bytes and semantics. New v4
runs require host-selected independent acceptance before model work.
The original durable episode ledger admits at most ten evaluations across
resumes; failed/interrupted checks count and reviews do not. Stop before
episode eleven. Fresh semantic feedback reserves five stopped finish actions: `ddc-store`, Scar Chronicler PFP
learning, actual digestion, native gates, then `ddc-complete`. Scar Chronicler consumes the actual checked procedure
root/digest from `learning_reply_binding`, including on partial runs, without clearing the stopped reason,
candidate or unresolved findings. Storage/readback and reuse are required
for completion. Fresh `semantic_digestion_v2` rechecks the original task after
learning, digests the current run and asks Defect Hunter to review the actual learned
reply and digestion, including unchanged learning. A finding requires new DDC
storage and an appended correction; Defect Hunter reviews it before fresh original-task
recheck/digestion and review. Preserve earlier raw replies and the original
deliverable. Unavailable paid review remains `REVIEW_PENDING` with no further
dispatch; a favorable artifact checker does not erase a learning finding.
Historical `semantic_digestion_v1` bindings and wire remain unchanged.
Successful current native checks are revalidated at final seal; stopped work
retains its reason. Fresh native intergates use `pfp-intergates-source-v1` with
host-pinned evidence/trust and explicit legacy compatibility. Future procedure
reuse obligations remain separate from current admitted task checks. C/R/I/T
storage asserts no E step or mathematical acceptance.

Perform each returned `next_action` before submitting its observation. Copy its
`action_id` exactly; report the real worker, artifacts, checks and findings.
Preserve the original objective, permissions and observations through repair or
continuation. A bare Python process returns a pending IDE action; it cannot
acquire this conversation or silently switch to a paid provider.

Work may be completed, partial or blocked independently of the evidence verdict.
`OPEN_RESIDUAL` can accompany a finished practical deliverable. Keep unavailable
checks and rejected approaches visible. `panel_coverage` reports actual checked
contributions and missing roles. A report, test count or persona agreement
does not issue a mathematical PASS.

## Applied Learning After Every Run

On every outer completed, partial or failed `/adversary` or `/adversary-digests` run,
invoke [/auto-oe-autop](../skills/auto-oe-autop/SKILL.md). Its default finish
invokes `/auto-learn` once in the current IDE. Read the actual obstruction,
deduplicate against an existing owner, apply a HIGH-confidence useful correction,
recheck the original need and carry unresolved work into the next brief.

Learned structure belongs in the existing code, skill, rule or concrete
anti/helpful pattern. An antibody binds an actual prompt, fixture or detector,
with harmful and benign controls; existing admission and activation rules apply.
Mirror selected canonical changes only, preserving independently maintained
host files. Do not invent a new lesson when the evidence supports none.

Inner AutoP/Adversary/learning helpers return findings to the outer finish, which
consumes them once. Learning edits and their recheck do not start another hook.
Routine learning needs no new receipt, intake, `learning.json`, novella or run
directory. Preserve historical evidence; temporary state is fine.

### Paper & Deposit Review Learning Discipline

When reviewing a paper, monograph, or deposit package (e.g. Zenodo republication reviews):
1. Every review finding must be mapped to an existing owner (rule in `research_papers/domain/rules/`, invariant in `.agents/rules/papers/`, or skill check).
2. For each defect class that can be evaluated deterministically, add an executable gate rule to `research_papers/domain/rules/` with a harmful fixture and a benign control test.
3. Historical byte-pinned files must never be silently edited to pass a new gate; use a `superseded_notice.md` to record withdrawn claims while preserving historical custody digests.
4. Gate verifiers must fail closed: never swallow missing tools or schemas with a silent `pass`.

Python can request the same host action without writing a receipt:

```bash
python .agents/skills/auto-oe-autop/scripts/orchestrate_autop.py --post-run --source task.json
```

That command returns an IDE handoff, not completed learning. The IDE follows it
with actual tools. The full nine-stage AutoP runner requires explicit
`--maintenance`; it is not the ordinary finish hook.

## Digestion and Automatic Run Reports

Use [/adversary-digests](../skills/adversary-digests/SKILL.md) for old repository files,
reports or intelligence. Read raw sources and decisive objections; the index is
navigation/provenance, not understanding. Apply useful learning and report the
actual recheck instead of automatically writing another packet.

When explicit source-bound interchange or cleanup needs a machine packet, retain
the existing typed `teamwork intake`, `learn`, `start --brief`, `recheck`, `digest`
and `resume` commands. Their existing lesson fields, literal excerpt and binding
checks remain compatible. The [shared guide](../../adversary/documentation/shared_teamwork.md)
documents these paths. Use the existing lifecycle/custody contract for explicitly
authorized cleanup, preserving exact historical bytes and receipt resolution.

Every new shared-backend run, including digestion, observes Syntax Prefilter's original seed,
final PFP system/user prompts and all captured replies with ordered-feature density
at 128 dimensions. `--density-dimension 28..1024` changes the dimension;
`--forge-organization off` selects an explicit unorganized comparison. The checked
Forge operation preserves original bytes and copies only declared typed fields.
Measurement follows rendering and cannot change the PFP input digest or acceptance.

UNS `uns.md`, UTS `uts.jsonl` and the single DDA action tape `ddc.jsonl` project the
same captured history. Checkpoints live beside state in `<state-stem>.reports/`;
terminal bundles finalize through `_ic/adversary/` with these files, `summary.json`
and `receipt.json`. New bundles have no separate `dda*` file. Full contributions
are expandable, with actual worker identity, pending/failed actions, checks,
learning and measured or unobserved cost. No role or geometry verdict is invented.
Historical `novella.md`/DDA bundles retain their readers and bytes; DDC semantics
remain. Reporting failures retain state separately from task outcomes; retry
`teamwork persist --state <state>`.
Read-only replay does not create a run. See the
[geometry runbook](../../adversary/documentation/prompt_geometry.md).

## Explicit Provider and Research Modes

- Ordinary IDE work needs no provider key or paid call.
- `teamwork run --executor openrouter` uses the same coordinator with an explicit
  model, output/state paths and durable run-wide policy at most $0.05. The adapter writes designated
  text; it does not execute model-supplied commands. Read the shared guide's
  current financial-cap limitation. Unknown costs halt dispatch; estimated
  admission never promises a vendor-enforced bill ceiling. Unbounded mode is refused.
- `/adversary run-live <arguments>` uses native PFP for every live model-backed seat.
  Signed admission and independent gates still apply; use the current
  [native guide](../../adversary/documentation/live_cli.md).
  It is a specialized suboperation within the canonical full-panel workflow,
  not evidence that 22 independent model workers ran.
- `/adversary research` (`python -m adversary.entrypoints.cli research`) selects
  WF_RESEARCH_PFP; no separate `/research` skill exists. Preserve
  its mission packet, nine-stage research loop, dispositions and compaction
  procedure in the [specialized research reference](../skills/adversary/references/research_workflow.md).
  These stages are not mandatory for ordinary IDE work. Native/research evidence
  requirements remain scoped to those modes.

## Research Paper Remediation & Release Verification

When Adversary tasks touch formal research paper packages (`coda_atlas/F004_papers/` or `research_papers/`), the following strict verification sequence must be honored before certifying completion:
1. **Manuscript & Code Parity**: Rebuild reader formats (`build_paper.py`) and ensure canonical Markdown SHA256 matches the embedded TeX digest comment.
2. **Lean 4 Census Totality**: Build standalone Lean packages (`lake build`) and verify `#print axioms` via `Census.lean`.
3. **Mypy Zero-Error Gate**: Verify `py -3.12 -m mypy code --python-version 3.12` returns exit code 0 across all paper sources.
4. **Release ZIP Manifest Parity**: Release archives must contain strictly the files in `SHA256SUMS` (including `docs/descriptions.md` if present) with normalized bit-level timestamps `(2026, 9, 27, 12, 0, 0)`.
5. **Fail-Closed Verification**: Execute package verifiers (`verify_package.py` or `verify_deposit.py`) and confirm typed receipt `status: PASS`.
6. **Refinement Heuristics vs. Physical Transport**: Computational scheduling predicates or graph-radius envelopes establish only refinement selection policies, never physical propagation bounds or no-signalling guarantees.
7. **Machine-Checkable Evidence Closure**: Every declared machine-checkable evidence dependency must resolve to an included artifact or a pinned external URN with status `external_unverified`.
8. **Line-Ending Invariance & Byte Exactness**: All package text files must be normalized to LF line endings before checksum calculation, and release ZIP archives must match loose files byte-for-byte.
