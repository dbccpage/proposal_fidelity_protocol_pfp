# PFP migration and integration execution plan

AuthorityEffect: None. Reconciled 2026-10-13 against remote main
`4a64d451606294c404e3298d4a2bff4974343004`.

The Python consolidation and rename are complete: `omega_engine_pfp` owns PFP
and Symbol Game. Retain the `pfp`, `symbol-game` and `level-engine` commands,
native crate names, wire IDs and frozen evidence. The only active planning
successor is [PFP-010](../../omega_engine_product_planning_office/plans/epics/oepfp/epic_oe_pfp_010_consolidated_residual_plan.md).
The [earlier closeout](pfp_epic_closeout.md) records previous deliveries and their
bounded evidence; its counts are not a fresh result for this change.

## Architecture and enforced boundaries

| Owner | Responsibility | Relevant code |
| --- | --- | --- |
| PFP | Prepare the public typed prompt; bind task, attempt and input; check actual reply bytes; replay | [task turn](../infrastructure/task_turn.py), [prompt](../use_cases/pfp_prompt.py), [reply](../use_cases/pfp_proposal.py) |
| Providers | Allowlist, prices, maximum liability, reservations, persistent spend and trusted settlement | [gateway](../../omega_engine_providers/infrastructure/gateway.py), [SQLite ledger](../../omega_engine_providers/infrastructure/budget_ledger.py) |
| Woland | Roles, repair limits, workflow state, independent file readback and host commands | [role profile](../../omega_engine_woland/infrastructure/teamwork_pfp.py), [CLI](../../omega_engine_woland/entrypoints/teamwork_cli.py) |
| Workflows/Agents/Skills | Typed instruction contracts, procedural anti-ops and instruction admission | [prompt gates](../../omega_engine_operads/domain/prompt_hierarchy/evaluator.py) |
| Epistemic Immune System | Candidate pharmacy, reviewed admission and independent danger evidence | [catalog](../../omega_engine_epistemic_immune_system/domain/pharmacy_catalog.py) |
| Education | Teaching documents, papers and explanatory lessons | [learning route](../../omega_engine_education/documentation/004_oepfp/README.md) |

Schema-valid prose remains UNVERIFIED. Workflow completion is not mathematical
acceptance, host execution, instruction admission or antibody activation. The
existing PFP mode 4 exercises OEWAS prompt gates; mode 5 checks bound instruction
composition. Ordinary role turns do not automatically acquire either permission.

## Execute from top to bottom

1. **Refresh and reconcile.** Start from remote main in an isolated worktree.
   Compare current owners and reuse landed APIs. Done for the base above;
   duplicate local adapters were removed rather than layered over main.
2. **Harden typed ingress.** Resolve local schema references offline. Refuse
   nonproductive cycles before dispatch; retain productive recursive schemas.
   Preserve literal ordinary task inputs; research-only oracle projection stays
   in its stage profile. Refuse invalid Unicode with retained completion and
   vendor-wire custody. Target `test_pfp_task_turn` and `test_task_turn_adapter`.
3. **Close supported IDE ingress.** Emit the existing prepared role prompt and
   accept actual `--raw-reply` bytes. Refuse unchecked `--result` and forged PFP
   metadata. An optional `--host-result` supplies only matching artifact
   paths/digests, independently read by Python. Recheck retained files on later
   actions. Keep host `recheck` and `digest` commands distinct. Target the IDE
   gate, teamwork CLI, continuation and digestion tests.
4. **Persist one financial scope.** Use `DurableRunGateway` in the existing
   [accounting composition](../infrastructure/estimated_gateway.py). A hard run
   has immutable run ID, objective digest, allowance and call limit. All roles,
   repairs and model switches use the same Providers SQLite state. Claim each
   bound action atomically before dispatch; a restart never resends it. Fsync
   original vendor bytes before decoding or application. Unknown sends/costs
   retain holds and stop continuing work. Trusted generation reconciliation is
   bound and idempotent. Target `test_durable_run_budget` and provider controls.
5. **Verify the installed distribution.** Build a wheel, install with no source
   fallback outside the checkout, run Python with `-I`, and assert every imported
   Omega production module originates in the installed target. Execute the
   [installed probe](../tests/installed_package_probe.py): CLI/resources, typed
   answer/replay/mutations, PFP-to-OEWAS gate, all Woland public exports and an
   actual Woland synthetic workflow. Its durable-budget control requires an
   explicit native binary, identified by SHA-256. The wheel does not bundle or
   attest that native build. Third-party dependencies come from the invoking
   environment; no Omega production modules may come from the source checkout.
6. **Protect route closure.** Exercise teamwork, dialogue, research HTTP, critique
   and native retirement/parity controls. Ban new direct network imports,
   including standard-library HTTP. Retained provider import exceptions require
   their actual route checks; namespace markers alone are insufficient. Codex,
   Claude Code, Grok and Antigravity use the same host-neutral prepare/raw-submit
   handoff. Python cannot intercept hidden IDE networking or bill subscriptions.
7. **Review and land.** Independent adversarial, architecture and billing agents
   review fixes. Run only affected local tests, required small precommit gates,
   Ruff and Markdown lint. Commit explicit paths, push the feature branch,
   attach a PR, merge the reviewed head and sync this worktree to remote main.
8. **Select the next practical residual.** OpenRouter CLI continuation remains
   refused until it can recover saved replies and the original budget binding;
   reopening SQLite through an embedding host is tested. A model/session hook
   without those guarantees stays unavailable. Native source/checker research
   and exploratory prompt offshoots remain conditional under PFP-009. The
   historical [derivation replay reader](../infrastructure/adapters/pfp_derivation.py)
   now closes its read-only connection on success and failure, alongside the
   continuing billing ledger's existing initialization/commit/rollback closure.
   Preserve those byte-custody controls when changing either reader.

## Billing contract

The complete run allowance is at most **50,000 microUSD ($0.05)**, shared across
all roles, stages and retries. It is never replenished for a repair or resume.
The hard gateway requires an enforceable transport maximum liability. Current
OpenRouter HTTP transport does not supply one and therefore refuses before
dispatch. Durable accounting must preserve that refusal. No paid trial in this
change uses estimated or unbounded mode to evade the cap.

The pre-existing `--max-estimated-cost-microusd` mode is explicitly an estimate,
not a hard vendor bill guarantee. Hidden IDE cost remains unknown. A stronger
live provider capability or explicit user agreement to another financial policy
is required before calling either a hard-cap live demonstration.

## Targeted evidence

All new model wire replies in automated controls are labelled synthetic. The
[retained current-IDE example](../../omega_engine_woland/tests/pilots/evidence/pfp_app_integration_20261012/ide_handoff/README.md)
is a finite signed matrix calculation, not an independent model comparison.
Replay reconstructs consumed state from actual reply bytes and rejects changed
answers, inputs, consumed content and verdicts. New failures enter EIS as
candidates, without self-admission.

Test receipts for this delivery are summarized in the PR and the execution
record below. Earlier overlapping totals must not be added. No full canonical
CI and no new paid provider calls are part of this verification.

## Execution record

Independent adversarial, architecture and billing reviews found schema-reference,
Unicode-custody, IDE-artifact, transport-admission and packaging gaps. Those
findings are repaired. The installed durable probe also exposed a Windows
SQLite initialization handle leak; its repair has a focused regression.

The [scoped verification record](../../omega_engine_woland/tests/pilots/evidence/pfp_app_integration_20261012/verification.json)
records **289 distinct passing targeted checks**, the required 52/52 republication
and 6/6 education gates, and the installed wheel's digest. The isolated probe
resolved 19 Woland root and two controller exports, checked 682 imported Omega
production modules against the installed target, exercised typed replies,
replay mutations, OEWAS controls and a synthetic Woland file workflow, then
exercised native-backed durable holds, restart refusal and trusted settlement.
Its two workflow and five accounting fixture calls made no external sends.

The wheel's 11 changed production Python files match the working source bytes.
It contains neither retired Python namespace nor the removed duplicate task-turn
adapter. This evidence verifies the selected routes and installed imports, not
every optional runtime factory. No native rebuild, paid trial or full canonical
CI was used.

## Active consumer ownership after the M1 source review

The five active runtime definitions below have one canonical owner. Current
callers use those modules directly; removed modules have no forwarding shim.
Historical source captures, judge bytes and original Git path identities remain
unchanged. The appended `current_python_source_dispositions` in
[migration_manifest.json](../migration_manifest.json) records these moves without
rewriting the earlier native/file accounting.

| Previous active module under Education pilots | Current owner |
| --- | --- |
| `challenge_suite/execution.py` | PFP `infrastructure/challenge_execution.py`: isolated trusted source judges, host execution and replay. |
| `challenge_suite/live.py` | PFP `infrastructure/challenge_live.py`: PFP campaign composition for original task profiles. |
| `challenge_suite/woland.py` | Woland `infrastructure/challenge_play.py`: shared challenge workflow and bounded proposal/review/repair. |
| `challenge_suite/mechanism.py` | Woland `infrastructure/mechanism_play.py`: original C006 session composition. |
| `relational_spacetime/compact_prompts.py` | PFP `infrastructure/numbered_prompts.py`: current v1.0.4 numbered-role construction; earlier versions remain literal. |

The retained task profiles now under Woland tests keep these responsibilities:

| Retained source group | Reason and boundary |
| --- | --- |
| `challenge_suite/catalog.py`, `c001.py`, `__main__.py` | Original problem inventory, public case projection, C001 schema/judge adapter and task/spec preparation. Current execution calls canonical PFP/Woland modules. |
| `challenge_suite/replay_snapshots.py` | Explicit historical source/revision replay tool; old module paths in its sealed inputs remain historical identities. |
| `relational_spacetime/tasks.py` | The five original derivation seeds, granted lifts and task-specific schemas. No shared sender or ledger. |
| `finite_checks.py`, `finite_fixtures.py`, `compact_checks.py` | Original exact fixture judges, witness controls and experiment-specific scoring. They consume canonical PFP contracts and current prompt construction. |
| `trial_prompts.py`, `final_prompts.py` | Original task/profile licenses, source context, historical recipe inputs and fixture-specific schemas. Current generic numbered-role assembly is canonical PFP. |
| `baseline.py`, `parameter_trials.py`, `compact_trials.py`, `typed_signals.py` | Named experiment selection, original task/checker wiring, results and historical campaign replay. Construction/execution delegates to existing PFP adapters/use cases; checkpoint/source requirements remain explicit. |
| `decoding_controls.py` | The pinned Qwen/PO035 experimental capability/tokenizer profile, not a second provider transport. |
| Formal-math/synthesis matrix helpers | Original cases/judge classifications stay beside their PFP/Woland test profiles. [PR #880](https://github.com/dbccpage/the_symbol_game/pull/880) moves their send path through the shared canonical PFP/accounting adapter; it is merged. |

Infrastructure composes these trusted task profiles explicitly. PFP
pure domain/use cases do not acquire a Woland dependency to obtain transport or
judges. This disposition does not turn the original scientific protocols into
generic finite certificates or retire their unimplemented requirements.

Installed verification now checks the five canonical runtime definitions,
absence of their old active modules, all fifteen current v1.0.3 pilot/role
renders, source/registry pins, the six original frozen prompt identities and
missing/tampered historical-byte refusals. It runs outside the checkout with
Python isolation and checks every imported Omega production module's origin.
The native budget probe requires an explicitly identified external binary; the
wheel neither bundles nor attests that binary's current build. These are offline
controls, not paid-provider or whole-original-protocol results.

Current-source validation for this ownership slice: the declared wheel built
successfully, included every selected production/data file, and the isolated
probe loaded 688 Omega production modules from the installed target. All fifteen
current roles rendered; frozen source lookup/mutation controls and synthetic
Woland/PFP plus native-backed durable budget controls passed. Zero external
provider calls were made. The external native binary was identified by SHA-256,
not rebuilt or attested as a build of this candidate.

## Current ownership, source custody and historical replay

Merged [#880](https://github.com/dbccpage/the_symbol_game/pull/880) and
[#881](https://github.com/dbccpage/the_symbol_game/pull/881) deliver the pilot
send-path repair and the five canonical Python moves above. The existing
architecture inventory now registers the two actual infrastructure consumers
(`code_change_checker.py` and `normal_forms/qm_classical.py`) by exact path and
rationale. New sibling importers still refuse; a removed importer must also
leave the allowlist. No process or provider fallback was added.

Use the existing migration checker with its explicit current Python scope:

```powershell
python -m omega_engine_pfp.infrastructure.migration_fitness --current-python
```

It checks the manifest's declared moves against original and introduction Git
blobs/ancestry, current tracked/package-eligible owners and static retired imports.
The introduction digest remains historical provenance: a legitimate later code
edit must not be forced back to those bytes. Missing history, forged provenance,
restored old owners and retired imports refuse. It uses setuptools discovery for
its active static scope; computed imports, excluded host scripts, native parity
and actual installed behavior need their separate checks. Alias possibilities
are conservatively retained, so later rebinding cannot hide an earlier literal
import; this is not Python execution or precise runtime name resolution.

The default command independently checks the current Rust migration byte map.
Its current reconciliation and preserved prior-map Git binding are documented in
[the map review](rust_migration/README.md). The scoped Python command does not
certify that map or establish migration completion. Earlier refusal counts are
historical; use the default command for current coverage and source digests.

New campaign runs capture the exact template, case and TASK files alongside
Python sources in their existing source snapshot. Replay refuses changes to any
of these inputs before grading. The Woland challenge adapter already binds TASK
bytes and validates the case digest; it constructs its own typed turn and does
not consume this campaign template.

The retained C005 v5 packet predates the TASK appendix. Replay it with its
recorded source revision rather than substituting today's prompt or rewriting
its request, judgments or receipts. The existing reader now accepts both old
captured entrypoint identities and the canonical `challenge_live.py` identity:

```powershell
git worktree add --detach <disposable-checkout> 69570b3e5fcf4b3799469f7d294ffee5899637fc
python -m omega_engine_woland.tests.pilots.challenge_suite.replay_snapshots --checkout <disposable-checkout> --evidence omega_engine_woland/tests/pilots/evidence/demo004_pfp_learning --run c005_dev_typed_witness_v5 --output <new-output.json>
git -C <disposable-checkout> status --porcelain
git worktree remove <disposable-checkout>
```

Use a Python environment with the replay dependencies installed, including in
its child processes. The current execution used Python 3.13.11, not the original
3.12.10 environment: both C005 stages replayed, exact request/reservation bytes,
original judgments and stop/summary semantics matched, zero provider calls were
made, and the disposable checkout was restored clean. The packet's original
config digest remains `fba81f9a900dc3f095bae359af8203c28827d581c8b9548ec4f57efbc06492b2`.
This is historical replay, not a new model response or current-task success.

The focused historical regression uses the recorded revision in a task-owned
worktree. Set `PFP_HISTORICAL_REPLAY_CHECKOUT` to an already clean detached checkout
at that exact revision to reuse it; the test never removes a supplied checkout.
Missing Git objects are an explicit failure. Captured sources and provider bytes
are never rewritten. Reader controls cover restoration after success and failure
for old and canonical entrypoints.

The gateway construction guard now checks the exact existing composition
functions: `trace.gateway_factories._confined_gateway` owns traced fixture/live
confinement; `estimated_gateway.create_accounted_openrouter_gateway` owns explicit
OpenRouter accounting policy. The accounting API does not claim fixture
confinement. Both retain their existing runtime APIs. Extra construction calls,
missing constructor paths and raw imports outside these owners refuse; static
source checks do not replace the budget, custody and confinement behavior tests.
Provider exception checks compare the actual canonical Woland types so an old
compatibility module name cannot misstate exception identity.

The next bounded slice closes two observed gaps:

- Derivation replay explicitly closes its SQLite reader after fetching the saved
  budget state, including query/database failures. Opening remains read-only;
  missing databases refuse without creating a replacement. Its provider imports
  use the current Woland owners. Replay does not rewrite historical packets or
  bypass source/configuration, request, reply or accounting checks.
- OpenRouter dialogue rejects an unbudgeted raw gateway before dispatch. It
  reuses the enclosing budgeted provider gateway, `EstimatedBudgetGateway` or
  `DurableRunGateway` without creating an allowance. Focused controls cover
  shared call exhaustion, unknown cost stopping continuation, and a reopened
  durable run retaining its action and original wire. Estimated accounting
  remains an estimate; these synthetic checks do not certify a live vendor cap.

PFP-009's formal-math/synthesis route entries now reflect their merged PFP
adapters. Their independent judges and original classifications remain in
their test profiles; the retired raw synthesis transport still refuses. Runtime route
coverage and mathematical task acceptance remain separate claims.

Main added 719 C051-C055 paths after the preceding Rust-map review. The
initial inventory found retired-owner references in 22 Python files. The active
imports and command examples now point to `omega_engine_woland.tests.pilots`;
script bootstrapping uses the current repository boundary instead of the retired
owner, a hardcoded checkout or the old directory depth. No compatibility package
or alternative sender is introduced. The shared matrix transport remains the
existing mediated PFP adapter.

The regression checks load the relocated entry points outside the checkout and
exercise the existing exact judges on retained inputs. Generators are only
loaded, never run against the tracked corpus. Cases, reference outputs, solver
and judge implementations, historical findings and old receipt bytes stay intact.
The map retains the original relocation revision/byte identity separately from
current edited source hashes. This closes the selected import repair, not
neural/model performance, native parity or the original C001-C030 obligations.

For a deterministic public-example run from the repository root:

```bash
python -m omega_engine_woland.tests.pilots.c052_maxflow_mincut_certificates.participant_packet.runner --all-examples
```

Inspect the existing PFP matrix CLI without dispatching a model:

```bash
python -m omega_engine_woland.tests.pilots.c052_maxflow_mincut_certificates.run_c052_matrix --help
```

That inherited repair was offline and did not claim model/native parity.

## OEV1RC bounded original-protocol execution, 2026-10-13

The current original-protocol collation records all thirty C001-C030 identities,
frozen task-source hashes, reported historical paid/IDE observations, actual
local-model raw replies and remaining original requirements. External historical
captures stay labelled external. Original selection, hidden, replication and
native obligations remain open wherever not executed.

C006 explicitly selects `c006.panels.v2`: twelve public boards (two each at
cycle ranks 3-6 and four at rank 7), sixty hidden boards (ten each at ranks 3-8),
twenty relabel/orientation controls and twelve actual stale-CUT/zero-chord
candidates. The original contradictory public-count wording is preserved.
Seeded nonstar spanning trees satisfy the original shared-cycle-edge condition;
old default boards retain their original BFS/session-v1 interpretation.

C007 now has the original six-stage 30-48-turn text driver, immutable constraint
IDs, false-restatement refusal, protected-edit rejection, final-union checking,
prompt/raw-reply retention and zero-send native/independent replay. Forty hidden,
twelve relabel and sixteen poison schedules retain nontrivial unions. Host
reference witnesses stay outside participant facts. Real finite KV probes are
separate from the still-open long-horizon KV comparison.

The existing HF adapter accepts an injected eager local model and supports
reversible attention bias, head capture/patch/scale, residual capture/addition,
output-logit bias, tokenizer offsets and finite token tries. Pinned SmolLM2-135M
CPU proposals test feasibility. The baseline and one versioned calculation-hint
arm each produced zero verified results across eight blind cases. Six per arm
were schema-valid but mathematically wrong; two cycle outputs copied schema and
hit the token cap. Initial target-conditioned residual rows are excluded and
preserved; affected-only replacements use task-independent fixed calibration.
This is a negative result, not evidence of model or prompt superiority.

The exact-byte manifest is checked before local checkpoint loading when supplied;
a caller's revision label alone is weaker declared metadata. Original Qwen7B/8B
selection, replication and full hidden campaigns remain open. The calculation
hint stays candidate guidance, not an admitted antibody or universal template.

C009/C010 provide original route/source pins, dropped-rung reporting,
duplicate-preserving raw two-judge rescoring and exact Coverage@k. Missing
authoritative C061/C071 sources prevent a complete original anchor packet.
No replacement chemistry/economics task is invented.

Formal, synthesis, finite challenge and mechanism callers supply actual
run/objective identity and bind each request to its PFP action. The existing
financial gateway owns continuing reservation, billing and no-resend decisions;
there is no second pilot budget implementation. Fresh native checks bind the
assembled host separately from historical-binary evidence. Targeted commands,
source hashes and the single collation live under
Git commit `0622e7e666877c61ae9330fe55b6a223965e23eb` at `_ic/woland/oev1rc_integration_closure`.

## Final Education pilot-owner move

The move from base `ad49ca44b04c39ba07427c9dc79a24695e1ccd52` places the
remaining 6,798 tracked Education pilot files under
`omega_engine_woland/tests/pilots`. Root custody verified their original bytes
before current caller/documentation repairs. Education now holds explanatory
material; `omega_engine_education/pilots` and `omega_engine_education/pfp` are
absent. The earlier `demo_004` and first-six-pilot move remains under PFP tests.

Current numbered prompting uses append-only `1.0.4` for relocated task/source
locators. Versions 1.0.0-1.0.3, original seeds, replies, registry/paper pins and
source manifests are not rewritten. A locator move or successful offline replay
does not establish model improvement or native parity. Current replay adapters
open moved evidence and reconstruct its original paths in isolated snapshots;
old identities inside sealed manifests are intentional.


## Every-turn closeout, 2026-10-16

Current supported Woland turns use PFP preparation and checked raw replies:
IDE/remote Retinue (including digestion, learning and repair), graph proposals,
dialogue, research stages/HTTP, critique, typed operations and the native
`PfpSeatExecutor`. Formal/synthesis helpers and the operad pre-miner reuse
`complete_pilot_turn`. The pre-miner now requires an injected accounted gateway,
one explicit model and task identity, executes serially, and stops on unknown
accounting. Proposed research/fences stay unverified and are not admitted antibodies.

`woland_pfp_route_violations` in the existing architecture fitness owner inventories
these call sites, checks their PFP hooks and confines direct HTTP/SDK construction
to explicit transport/metadata owners. Mutation tests cover removed prepare/check,
raw/aliased senders and native wrapper removal. This finite source check complements
runtime binding/accounting tests; it is not an arbitrary-code sandbox or an
interceptor for hidden IDE networking.

Graph replay now accepts the native bundle's optional digest-bound `mam/`
projection, still verifying its bytes and rejecting unknown files. Checkpoints
compare normalized JSON wire values so tuple metadata cannot spuriously become
`REPORT_SOURCE_CHANGED`. Historical layouts and receipt bytes are unchanged.

Current OpenRouter `resume` recovers saved results under the original ledger.
Hard policy retains `BUDGET_ENFORCEMENT_UNAVAILABLE` with this transport; explicit
estimated mode has a continuing allowance and stops on unreported cost. Neither
this closeout nor its current-IDE demonstration makes external provider calls.
