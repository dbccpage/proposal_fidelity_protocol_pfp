---
name: adversary-digests
description: "Digest old files into useful code and agent contracts; carry applicable lessons and unresolved work into the next brief."
operad_source_colours: ["State", "Paper", "Code", "Contract", "Receipt"]
operad_target_colour: "Contract"
operad_arity: 5
operad_residual: "unknown"
families: [governance, adversary, meta]
---

# Adversary Digests

**AuthorityEffect:** `None`.

Use `/adversary-digests <file-or-directory> [more paths] [focus]` for arbitrary old
repository files, reports or intelligence. The current IDE reads and reasons;
the existing Adversary `teamwork` backend remains the shared Python coordinator.
No provider call, fixed Panel roster or new framework is required.

Use the [Adversary PFP handoff](../adversary/SKILL.md#default-drive-the-shared-backend-in-the-host)
for model-authored digestion and learning: read the shared `pfp_turn` brief,
then submit the actual bound reply with `teamwork submit --raw-reply`.
Deterministic intake, file reading and host-tool observations remain host
operations. A bare shell returns a pending IDE action, with no paid fallback;
IDE cost is unavailable. Do not force mathematical stages on ordinary prose.

Use the [review-to-structure pattern](references/review_to_structure.md) when
turning a corpus review into reusable repairs. It carries original invariants,
concrete witnesses, the digester's own corrections and the next worker brief.

## Recall, Read and Learn

1. Read [/auto-learn](../auto-learn/SKILL.md) and recall relevant existing lessons
   before starting. Every spawned worker reads it and the applicable lesson paths
   in its brief. Reuse existing catalog owners rather than parallel skills.
2. Resolve the requested paths and focus; use relevant Panel lenses or actual
   scoped helpers. Read the actual source/code, decisive objections, failures and
   contrary evidence. Keep missing/unsupported sources and coverage gaps explicit.
   Choose unread work using the old inventory together with current typed source
   bindings and documented read scope; an old `INDEXED_ONLY` label may predate a
   later digestion. Do not rewrite the historical ledger to hide that distinction.
   A filename, extracted finding or reported PASS does not establish correctness.
   Compare the narrative with raw observations and explicit later corrections.
   Check every affected claim projection and keep each bound's own domain.
   Separate quantitative margins, qualitative consequences and endpoint status.
   Carry the corrected scope and unresolved premise into the next worker brief;
   preserve conflicting historical bytes. Bounded PASS checks leave unrelated
   UNKNOWN obligations open. Explain concrete conflicts without voting by file
   type or assuming the newest prose is authoritative.
3. Identify the concrete failed assumption, witness, supported cause, correction,
   actual verification, applicability and exceptions. Separate historical reports
   from reproduced observations and hypotheses from demonstrated failures.
4. Apply the smallest justified HIGH-confidence correction within the authorized
   digestion scope: improve the existing code, skill or rule, or land a tangible
   anti/helpful pattern. A digest can finish with an honest residual when its next
   implementation needs new input; do not invent a lesson or unrelated work.
5. Recheck the original need against the changed artifact. Honor testing limits,
   name checks actually performed and carry unresolved work into the next brief.

The useful output is applied structure in the existing estate. Routine IDE
digestion does not require new intake files, `lessons.json`, `learning.json`,
novellas, receipts or run folders. Temporary working/backend state is fine.
Preserve historical evidence already present and reference it when useful.

## Exclusive Output Destination Invariant

Every `/adversary-digests` and `/adversary` run will write their output directly to `_ic/adversary/` and nowhere else:
- All digestion analysis outputs, reports, extracted lesson proposals, and state files must be written directly under `_ic/adversary/` (e.g. `_ic/adversary/<task_key>_digestion.md`, `_ic/adversary/<task_key>_digestion.json`).
- When explicit machine packets or exchange states are needed, use paths directly within `_ic/adversary/`:
  - `--output _ic/adversary/intake.json`
  - `--lessons _ic/adversary/lessons.json`
  - `--output _ic/adversary/learned.json`
  - `--state _ic/adversary/task.json`
- Digestion runs must never write output files or intermediate notes to other agency folders, active research paths, scratch directories, or arbitrary locations outside `_ic/adversary/`.

## Choose the Structure That Helps

| Form | Concrete content | Existing canonical estate |
| --- | --- | --- |
| Skill | Input, reusable procedure, output and deciding check | `.agents/skills/` |
| Anti-skill | Forbidden procedure, trigger and falsifier | `.agents/antiskills/` |
| Anti/helpful pattern | Harmful approach or supported alternative with limits | `operads/patterns/anti/`, `operads/patterns/helpful/` and existing pairs |
| Antibody | Actual detector/prompt/fixture binding, harmful and benign controls | `.agents/antibodies/` |
| Rule | Narrow invariant with an owner and enforcement status | `.agents/rules/` |

Inspect existing entries and the applicable typed catalog first. Amend an owner
before creating a duplicate. Do not manufacture one artifact of every form.
When portable typed guidance is useful, reuse the existing OEWAS compiler:
author a reviewed entry in `operads/catalog/contracts/v1/lessons/`
with its exact owner source, excerpt, correction, applicability and exceptions.
Rules separate trigger/predicate/response; helpful patterns separate conditions,
construction and example; anti-patterns separate failure/witness/repair.
Prompt-attached antibodies also bind the real prompt and harmful/benign controls.
Run `python -m operads.infrastructure.typed_contract_compiler --repo-root . --write`
then the same command with `--check`. The existing projector preserves conflicting
host-owned files. These are on-demand IDE instruction packages, not ambient rules
or activated detectors. Carry the relevant generated package or typed instruction
operand into the next worker brief; corrections and exceptions must survive both.
See the [typed guidance guide](../../../operads/documentation/typed_canonical_contracts_v1.md#digested-guidance-extension).
An antibody requires a tangible prompt, fixture or detector; a slogan or detached
report is insufficient. Existing OEEIS admission/two-signal checks govern
activation. A new sighting never activates a detector. Prose without a checker
retains its policy-candidate limit.

Use these generated corpus lessons when the next task matches their conditions:

| Task branch | Selectable guidance |
| --- | --- |
| Report task-success rates | `/adversary-assigned-outcome-rule`: preserve all assigned outcomes and retry identity. |
| Plan another query or worker | `/adversary-free-information-pattern`: inspect admitted initial information first. |
| Review strict exact parsers | `/adversary-parser-work-antipattern` and `/adversary-parser-work-antibody`: lexical admission before arithmetic, with the attached review prompt and valid-cost control. |
| Summarize formal results | `/adversary-proof-scope-rule`: retain supplied premises and the actual formal scope. |
| Recheck a repaired candidate | `/adversary-scoped-reuse-pattern`: recheck changed dependencies and label reused evidence historical. |
| Reuse a learned rejection rule | `/adversary-stale-task-antibody`: check the current task and exact carrier with harmful and benign controls. |
| Transfer a proof or numerical bound | `/adversary-proof-premise-rule`: carry used hypotheses into the claim and consuming input contract. |
| Design or interpret a check | `/adversary-check-sensitivity-pattern`: bind the checked candidate to its components and test a property-changing mutation through the actual consumer. |

The retained research reports support these lessons at their stated scope; the
generated instructions do not claim that old defects persist in current code.
For composed checks, inspect support, auxiliary sources and assembly as well as
pairwise components; name the structural argument or bounded check actually used.
Later repairs of one role leave other roles open until checked. Value equality
and byte-identical replay are different claims; inspect the claimed comparison.
For numerical attacks, retain precision, truncation, sampled parameters and the
violation scale. An empty search or a very loose bound cannot supply the missing
proof. Identify a standalone check's gap separately from a downstream check that
already catches it; do not transfer that gap into a refutation of the model.

Mirror only selected canonical changes through the existing admission/generation
and host-parity path. Preserve other hosts' independently maintained packages.
Never copy credentials, environment dumps or private provider secrets into
learned artifacts.

## Finish Every Run

On completed, partial or failed outer digestion, invoke
[/auto-oe-autop](../auto-oe-autop/SKILL.md), which invokes `auto-learn` once in the
current IDE. It consumes the observations and learning already performed; it
does not repeat the work or launch the full maintenance sweep. Inner helpers
return observations to this outer finish and never recurse through more hooks.

Report what was read, the actual applied paths, recheck results and the remaining
next task. Guidance in the normal response/next worker brief is enough. In
accordance with the active vs terminal estate demarcation, no digested source
file may remain in the active `_ic/` tree once digestion completes: remove fully
processed files via `git rm` (pruning any now-empty directory branches) or relocate
non-reproducible historical records to immutable archive storage so that completed
files do not linger to be repeatedly re-digested across sessions. All newly codified
rules must immediately be synchronized across the four host roots (`.agents/`,
`.claude/`, `.codex/`, `.grok/`) with invariant ownership registered in
`rules_registry.yaml`. Historical bytes remain preserved in Git object history and
immutable custody.

## Optional Typed Interchange and Custody

When the task needs a source-bound machine packet, use the existing commands;
the format and backend remain compatible. Output paths must resolve directly to `_ic/adversary/`.

```bash
python -m adversary.entrypoints.cli teamwork intake --repo-root . --source path/to/report.md --output _ic/adversary/intake.json
python -m adversary.entrypoints.cli teamwork learn --repo-root . --intake _ic/adversary/intake.json --lessons _ic/adversary/lessons.json --output _ic/adversary/learned.json
python -m adversary.entrypoints.cli teamwork start --objective "<next task>" --brief _ic/adversary/learned.json --state _ic/adversary/next-task.json
```

The optional `lessons.json` uses the existing nine fields: `source_path`,
`source_revision`, `failed_claim`, `counterexample`, `cause`, `correction`,
`verification`, `applicability`, `exceptions`, plus a literal `evidence_excerpt`.
Use exact intake bindings. Optional `kind`, `target_path`, `artifact_content`
reuse typed proposals; an antibody also names an actual `binding_path`.
Source binding attests which bytes were read, not the causal/mathematical claim.
The CLI's proposal output does not install or activate candidates. Keep existing
receipts when used for native execution, explicit interchange or historical
cleanup; routine learning does not create another packet by default.
