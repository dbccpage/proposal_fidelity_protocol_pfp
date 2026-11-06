# PFP LLM ladder: design

AuthorityEffect: None. This package adds provider calls to the PFP workflow; it accepts no theorem.
Source of the method: the Proposal Fidelity Protocol / symbol-host reference system
(`the external PFP package`, `external:git-tree:a9ee45ce1419980890e0ce9f59c5e35706e48f96`, and the teaching
corpus `external:git-tree:d84b8a68db4ee594888c56bd2ccd659cb1d54842`). Everything below was read, not executed.

Goal: a derivation that a free or small model can find for about a dollar must never cost a thousand.
Cheap models mine operads and propose lemmas. The host checks every claim locally, at once. Refused claims
are kept as negative operad entries so that the next call, at any tier, does not repeat them. A large
Claude model is used only for a step the cheap tiers failed to close, under a hard weekly budget.

## 1. The OEPFP method in one page

1. **A model's answer is an untrusted proposal.** Every reference module states `AuthorityEffect: None`.
   Authority belongs to the host checker, never to a reply and never to a model's statement about itself
   (`use_cases/pfp_stages.py`: `RunPfpPipelineUseCase.terminal_after`, `finish`; "the terminal is recomputed
   from host facts; no model field is read as a terminal").
2. **The prompt is a compiled packet, not prose.** `use_cases/pfp_prompt.py` builds the public task input
   (`public_task_input`), strips judge-only keys (`stimulus()` / `HIDDEN_KEYS`: `expected_*`, `ground_truth`,
   `oracle_answer`, `host_diagnostics`, ...), replaces worked example blocks by a "wire field shape (values
   withheld)" schema (`task_contract`), and wraps the task's answer schema in a reply envelope whose
   `task_id`, `attempt_id` and `input_sha256` are `const`s (`task_turn_response_schema`). A reply that does not
   carry the binding cannot be checked against a different input. `domain/prompts/compression.py` stores
   shared system text and schema once per environment (storage only; the provider still receives every byte).
3. **The reply is a typed slot-fill.** The grammar `grammar/pfp.ebnf` has a 6-slot frozen envelope (schema,
   task, protected boundary, budget, candidate, witness), a cochain receipt and typed refusals
   (`ERR_UNDECLARED_CARRIER`, `ERR_COCHAIN_DEFECT`, `ERR_BUDGET_EXHAUSTED`, `NON_DESCENT`). The finite-QM
   profile (`infrastructure/yaml/prompts/finite_qm/`) asks the model to fill four *missions*: M1 carrier, M2
   typed operations and the shortest composition tree, M3 relations, traps and near misses, M4 the certificate,
   checker and anchors. "An inventory, a plan, or a recital of terminology is not a completed derivation."
4. **Operads are the primary research output.** Each stage returns an `operad_delta`: generators with ordered
   input colours, output colour, arity, carrier, ring, hypotheses, source pins and a semantic predicate;
   relations with their typing conditions; checked compositions (outer, slot, inner, colour match, licensing
   relation); *failed compositions and counterexamples are kept*; unresolved obligations are kept
   (`dag/pfp/stage_contracts.yaml` here, `finite_qm/workflow.yaml` there). Matching colour labels alone does not
   license a composition.
5. **Stages are bounded and mostly host work.** P0 mine, P1 derive, P2 verify (host), P3 repair, P4 challenge
   (near miss plus a valid control), P5 record. Repair is a fresh request carrying the original public inputs
   and *whitelisted, answer-free* failure classes (`REPAIR_RULES`, `PfpStagePolicy.feedback_after`): no
   expected value, no raw judge diagnostic, no chat history.
6. **Cost is a first-class, enforced quantity.** Money is exact (integer micro-USD, `Fraction` prices), the
   worst case is admitted *before* dispatch (`seat_transport/routing.py` `BudgetPolicy` / `admit_spend`), an
   ambiguous outcome keeps its reservation, an unreported cost is unknown rather than zero, and there are no
   silent retries or model substitutions (`pfp_stages.py`, `openrouter_seat_gateway.py` `CallLedger`).
7. **Management policies are measured, not assumed.** The management-ladder design
   (`external:sha256:f307f6810f0b8d6446eea469294a2bd3c10be2d9f12ac69ddd53a0b2f4aa84c5`, `infrastructure/management_ladder.py`)
   compares M0 plain, M1 typed objectives/obligations, M2 enforced structured output, M3 staged carry-over,
   M4 a training-derived correction, M5 a checked planar PFP/check/report operation tree (at most four ops),
   M6 one extra repair with failure-class feedback; paired exact sign tests, Wilson intervals, "descriptive
   small sample". `rewriting/README.md`: "a clearer prompt remains a heuristic until evaluated under a
   declared comparison."
8. **Cheap models pre-mine before dear tokens are spent.** `external:unlocated`:
   ten narrowly scoped mining roles (environment ring, finite fixtures, forward and obstruction morphism
   trees, antibodies, anti-patterns, helpful lemmas, SpanTable invariants, symmetries, a pre-mortem) run on
   free OpenRouter models, then are folded into a 3-layer operad prompt for the stronger stage. Providers are
   selected by `ANOMALON_LLM_PROVIDER` (`adapters/model_backends.py: get_backend`).

## 2. "Communicate more directly with LLMs", concretely

| OEPFP device | What the model sees / returns | In this ladder |
|---|---|---|
| Compact typed packet | Line-oriented sections `@TARGET @SRC @KNOWN+ @KNOWN- @FILL`; `@SRC` columns (`path \| decl \| kind`) are the same fields the reply schema asks for (`ref.path`, `ref.decl`) | `packets.py: compile_p0` |
| Closed answer grammar | A JSON schema with `additionalProperties:false`; generators, relations, compositions, lemmas, near misses, numeric claims | `packets.py: P0_SCHEMA`, sent as `response_format` (OpenAI-compatible) or `output_config.format` (Anthropic) |
| Operad-slot filling | The model fills typed slots; it may cite a declaration as existing only from the `@SRC` list the host built | `source_candidates`, `Verifier.check_ref` |
| Answer-free, whitelisted feedback | `@KNOWN-` lines carry a class, the refused name and a fixed "do not" sentence; never an expected value | `memory.py: forbidden_move` |
| Binding by digest | `in=<sha8>` in the packet header, full `input_sha256` in the request record | `CompiledPacket.input_sha256` |
| Typed refusals | `model_refusal`, `unparseable_reply`, `schema_violation` are classes, not exceptions | `verify.py` |
| Host verification of every claim | grep for declarations, exact recomputation, Lean elaboration, statement-vs-source check | `verify.py` |
| One bounded call, no hidden retry | SDK `max_retries=0`, `max_tokens` bound, worst case reserved | `providers.py`, `gateway.py` |

Measured here (dry run, `ladder.py ... --dry-run`): the compiled packet plus schema is 55 to 75 per cent of the
token estimate of the packet `prepare_stage.py` builds for the same node. That is a modest saving; the larger
effect is that the reply is 50 to 1,400 tokens of checkable JSON from a free model (450 to 2,900 from Claude at
low or medium effort) rather than an essay.

## 3. Mapping of OEPFP concepts onto this repository

| OEPFP concept | Reference | This repository's PFP file | Ladder module |
|---|---|---|---|
| Prompt template / mode / workflow | `yaml/prompts/finite_qm/{prompt_template,mode,workflow}.yaml` | `dag/pfp/{prompt_template,mode,workflow}.yaml`, `dag/prompts/*.yaml` | read through `prepare_stage.py` for the baseline; replaced by a compiled packet |
| Stage contracts, `operad_delta` | `workflow.yaml` stage outputs | `dag/pfp/stage_contracts.yaml` | `records.py: build_delta` writes this shape |
| Four missions M1-M4 | `prompt_template.yaml` | `operad_slots` in `dag/operads/<node>.yaml`; `prepare_stage.SLOTS` | `records.mission_patch` (status `PROPOSED_HOST_PARTIAL`, never `FILLED`) |
| Per-target operad collection | `domain/` operad types, `pfp_operad.py` | `dag/operads/<node>.yaml`, `dag/operads/index.json` | `packets.source_candidates` reads the candidates |
| Shared operad memory / immune system | `docs/07` Operator Memory, antibodies, consecration | *new* `dag/operads/_hallucination_index.json` | `memory.py` |
| Host stage (P2) / terminal from host facts | `pfp_stages.py` | `dag/pfp/batch_tools/stages.py` P2, `*_checker.py` | `verify.py` (P0 claims only) |
| Failure classes `G1_SCHEMA..G5_SCOPE` | `prepare_stage.FAILURE_CODES` | `dag/pfp/prepare_stage.py` | `verify.G_CODES` maps each class to a G code |
| Answer-free repair feedback | `REPAIR_RULES` | P3 `bounded_failure_codes` | `@KNOWN-` injection |
| Budget policy per bout/day/tier | `routing.py BudgetPolicy`, `admit_spend` | `mode.yaml bounds` ("explicit caller reservation") | `budget.py`, `gateway.py` |
| Cheap/strong tiers, ordered legs | `routing.py` `LLM_TIERS = (cheap, strong)`, `RouteLeg` | - | `config.DEFAULT_TIERS`, `runner.py` |
| Management policies M0-M6 | `management_ladder.py` | - | `runner.run(fixed_attempts=N)` measurement mode; M6 = guided retry; M5 = composition type-check |
| Operad pre-miner | `operad_pre_miner.py` | P0 mining | one typed P0 call instead of ten prose calls |
| Provider selection | `get_backend`, `ANOMALON_LLM_PROVIDER`, `OPENROUTER_MODEL` | - | `config.load_tiers(env=...)` |
| Credential resolution | `credential_source.py` | - | `llm_common.load_env` (same order; main-checkout `.env` via git pointer files) |
| Replay / custody of raw replies | `task_turn.replay`, retained bytes with sha256 | `dag/results/<node>/runs/*/pN/raw_response.*` | `records.py`: `raw_response.txt` per attempt, `request.json` with `input_sha256` |
| Historical `external_provider_calls: 0` | - | `dag/pfp/batch_tools/{selection,finalize,stages}.py` | `ladder_receipt.json` states the difference explicitly |

## 4. How a prompt is compiled

`compile_p0(root, node, attempt_id, policy)`:

1. Read the node's row in `dag/operads/index.json`, its operad collection and its DAG node
   (`dag/derivation_dag.json`: status, `lean`/`rust` anchors, parents and children).
2. `@SRC`: declarations the **host** found, in this order of trust: the operad record's own candidates;
   identifiers quoted verbatim in the target statement; declarations of the node's anchor files whose names
   share distinctive words with the statement; declarations of source files whose *file name* does. The model
   may cite as `existing` only from this list (or `@KNOWN+`). Anything else must be `proposed_new`.
3. `@KNOWN+`: verified generators/relations from earlier ladder runs of the node and its DAG neighbours.
   `@KNOWN-`: negative entries (section 5) for the node, its neighbours, or a declaration offered in `@SRC`.
4. `@FILL` plus the schema (not repeated in the text; it travels as `response_format`).

Example (TFQ-0028, `ladder.py --node TFQ-0028 --dry-run` prints it): header
`@PFP/1 task=TFQ-0028 stage=P0 attempt=plan in=db80dfbf guided=yes`, then the statement, the bottleneck, the
assumptions, the `@SRC` lines (`lean4/FiniteQM.lean::FiniteQM.qcd_beta0_asymptotic_freedom_window theorem | ...`)
and `@FILL`. Lean, Rust and Python declarations are indexed with the pattern of `dag/pfp/generate_prompts.py`
(Lean: namespace-aware; Rust: `fn|struct|enum|trait|type|const|static|mod`; Python: `ast`).

## 5. How operads guide the search

* **Positive memory.** A verified generator or relation is written to the run's `p0/operad_delta.yaml` with
  `host_evidence` (path, declaration, line, language) and `evidence_status: declaration_exists_semantics_unreviewed`.
  Later packets show it under `@KNOWN+`. A model may reuse it inside its scope; it is not a theorem.
* **Negative memory.** Every refused claim becomes a *failed_composition* (a move that does not ground or
  compose) or a *counterexample* (a concrete host fact against the claim: a recomputed value, a numeral the
  source does not contain, a wrong arity). They are written to the run's operad delta and merged into
  `dag/operads/_hallucination_index.json`, keyed by declaration and by normalised claim pattern, with model,
  provider, tier, node, run and occurrence count. An entry about a name that exists *now* is dropped at injection
  time, so the index cannot freeze a later-fixed repository.
* **Neighbours.** Retrieval uses the node and its DAG parents and children, plus any entry whose declaration
  key is among the `@SRC` offers. A failure on `TFQ-0027` therefore warns the call for `TFQ-0028`.
* **Composition check (M5 in spirit).** A composition counts only if both generators are host-verified, the
  inner output colour equals the outer input colour at that slot, and a host-verified relation licenses it.
* **Escalation is decided by host-classified failure, not by a model's confidence** (section 7).

## 6. How a step is decomposed into lemmas

P0's `lemmas` slot is the decomposition: each lemma states `relation_to_target` (restates, implies,
auxiliary, strengthens, weakens), `depends_on` (relation/generator ids), an optional Lean skeleton and
`claims_proved`. The host checks: numerals against the target and the cited source (statement drift); a
`strengthens` lemma needs a cited existing declaration (else *unjustified generalisation*); a proof claim with
`sorry`, an axiom or a tautological statement is a *vacuous proof*; the skeleton must elaborate when Lean is
usable. Verified generators and relations fill M2/M3, the lemma list is the "smaller lemma that advances the
target" the OEPFP system prompt asks for, and the unverified rest goes to `open_obligations`. P1 onward is the
existing pipeline: `prepare_stage.py` still requires a *host review* before any mission slot becomes `FILLED`.

## 7. Ladder policy and budget

* Tiers: 0 free (Groq `openai/gpt-oss-120b`, OpenRouter free models, Groq Qwen and gpt-oss-20b; Cerebras and
  NVIDIA adapters exist but both keys on file were refused on 2026-10-21, 402 and 403, so they are disabled
  with the reason recorded), 1 paid OpenRouter (`OPENROUTER_MODEL`, gpt-4o-mini), 2 `claude-haiku-5-5`,
  3 `claude-sonnet-5-5`, 4 `claude-opus-5-5`, 5 `claude-fable-5-1` (only with `--allow-fable`, the final hard step).
* An attempt that was *answered* and rejected by the host (schema, too few verified entries, or refused-claim
  rate over 0.5) counts toward escalation; N = 3 free, 2 cheap, 2 Haiku, 1 each above. Rate limits, timeouts,
  unavailable models and authentication errors never count: the model rotates, a bounded number of times.
* Effort (Anthropic): P0 mining `low` (Haiku) / `medium` (Sonnet, Opus, Fable); the P1 table (`high`, `max`) is
  defined for the final hard step. Adaptive thinking, never `budget_tokens`; no sampling parameters; `max_retries=0`;
  streaming above 16,000 `max_tokens`; `stop_reason == "refusal"` is a typed failure. Server-side `fallbacks` are
  **not** used: they would bill a model the guard did not admit, which the no-silent-substitution rule forbids.
* Budget (`budget.py`): the worst case (`count_tokens` + `max_tokens` x output price; thinking is output) is
  reserved in `budget_ledger.json` before dispatch. Limits: Anthropic 150 USD per ISO week (configurable),
  paid non-Anthropic 10 USD per week, and the run cap `--max-cost-usd`. Ambiguous outcomes keep the worst case as
  unreconciled spend; an unreported cost on a paid tier keeps the reservation. `set_external_adjustment` records
  spend made elsewhere (other worktrees, the console) so the weekly figure stays honest: **the ledger knows only
  what passes through it.**

## 8. Host verification and failure classes

| Class | Trigger | Entry type |
|---|---|---|
| `nonexistent_declaration` | cited existing name absent from the cited file and from the index; backticked name that exists nowhere; Lean `unknown identifier` | failed_composition |
| `wrong_source_location` | name exists, but not at the cited path | failed_composition |
| `wrong_signature` | stated arity differs from the Python/Rust/Lean declaration (Lean count is heuristic, marked so) | counterexample |
| `statement_drift` | a restating relation or lemma carries a numeral absent from its source and the target (heuristic, marked) | counterexample |
| `false_numeric_claim` | exact `Fraction` recomputation differs | counterexample |
| `vacuous_proof` | `claims_proved` with `sorry`/`admit`/axiom/no Lean text, or a tautological statement | failed_composition |
| `unjustified_generalisation` | `strengthens` with no cited verified declaration | failed_composition |
| `lean_elaboration_failure` | skeleton fails to elaborate | failed_composition |
| `composition_type_mismatch`, `composition_unlicensed` | colours differ / no verified licensing relation | failed_composition |
| `schema_violation`, `unparseable_reply`, `model_refusal` | reply outside the grammar / refusal | failed_composition |

Lean: `lake env lean` in `lean4/` runs only when `lean --version` names the version in `lean4/lean-toolchain`
(the toolkit's own check). The ladder names no version in code: `LeanRunner.availability` reads `lean4/lean-toolchain`,
which is `leanprover/lean4:v4.35.0` since the repository moved to Lean 4.35.0 (at the time of the pilot it named 4.33.1 while
4.35.0 was installed, so elaboration was skipped). When the installed Lean differs from the file, elaboration is *skipped with
that reason recorded*. Without Lean (also with `--no-lean`), a lemma that cites a verified existing declaration counts as
`ref-verified, not Lean-checked`, at the evidence level of a relation; a lemma with no citation stays `unverifiable`.
Round 2 ran with `--no-lean`; nothing was elaborated.

## 9. Records

`dag/results/<NODE>/runs/<ts>_ladder/` follows the batch toolkit's P0 layout (`p0/request.json`,
`candidate.json`, `raw_response.json`, `host_check.json`, `operad_delta.yaml`) so accepted candidates can go to the
normal P1-P5 pipeline after the host review, plus `p0/attempts/<id>/` for every answered attempt and
`ladder_receipt.json` with every provider call (provider, requested and served model, tokens, rated cost, cost
source, request id, stop reason, backoff events). Mission slots are `PROPOSED_HOST_PARTIAL`, never `FILLED`.
Keys are redacted from every field before writing; `test_ladder.py` re-scans the files.

## 10. Ported from the reference, and what was not

Nothing from `the external repository` was copied byte for byte: its provider and budget layers sit on a Rust native
host (`RustSymbolGameHost`), pydantic domain types and SQLite accounting, none of which this standard-library
package can import. The following designs and algorithms were re-implemented, with attribution in the module
docstrings:

* `credential_source.py` -> `llm_common.py` (resolution order, `.env` parsing, no mutation of `os.environ`,
  main-checkout lookup from git pointer files).
* `routing.py` `BudgetPolicy` / `admit_spend`, `openrouter_seat_gateway.py` `CallLedger`, outcome-unknown keeps the
  reservation, unreported cost is unknown -> `budget.py`, `gateway.py`.
* `openai_compat.py`, `http.py`, `ollama_local.py` -> `providers.py` (classified failures, bounded reply read,
  loopback Ollama probe; Ollama is unreachable on this machine so it is not configured).
* `operad_pre_miner.py` -> the typed P0 call; `management_ladder.py` -> measurement mode and the guided retry;
  `REPAIR_RULES` -> `forbidden_move`; `get_backend` / `ANOMALON_LLM_PROVIDER` -> `config.load_tiers`.

Not ported: the Rust Anthropic transport (the official SDK is used), the PFP envelope's pydantic types, the
SQLite ledger, the 2-second dispatch spacing (replaced by per-provider minimum intervals and 429 handling).

## 11. Limits

* Verification confirms existence, consistency and arithmetic. It does not confirm that a generator's
  *semantic predicate* is the intended mathematics, and it cannot see a hallucination that is merely vague.
* Statement-drift and the Lean arity count are heuristics and are labelled `confidence: heuristic`.
* Only P0 is wired. P1-P5 need `prepare_stage.py`'s reviewed missions and domain checkers.
* The free-tier model list and limits change; `config.DEFAULT_TIERS` records what worked on 2026-10-21.

## 12. Usage

```
python -I -X utf8 dag/pfp/llm_ladder/ladder.py --node TFQ-0028 --stage P0 --max-cost-usd 0.25 --dry-run
python -I -X utf8 dag/pfp/llm_ladder/ladder.py --node TFQ-0028 --stage P0 --max-cost-usd 0.25 --abstain-stop 2
python -I -X utf8 dag/pfp/llm_ladder/ladder.py --node TFQ-0028 --stage P0 --max-cost-usd 0 --max-tier 0 --measure-attempts 4 --no-feedback
python -I -X utf8 dag/pfp/llm_ladder/replay.py --report | --rebuild-index
python -I -X utf8 dag/pfp/llm_ladder/pilot.py --nodes A,B,C --k 4 --claude-cap-usd 3.5 [--calibrate-node A]
python -I -X utf8 dag/pfp/llm_ladder/test_ladder.py -v
```

Keys: `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `NVIDIA_API_KEY` are read at run
time from the environment, then `--env-file`, then the `.env` of this checkout and of the main checkout. They are
never printed, logged, written or copied. Ollama is used when `OEARS_OLLAMA_HOST` (default `http://127.0.0.1:11434`)
answers; it did not on the machine of this pilot.

## 13. Pilot of 2026-10-21 (what was measured)

Nodes: TFQ-0028 (small: beta0 arithmetic, anchors present), TFQ-0022 (medium: Fierz identity, Rust and Python twins
absent from this repository), TFQ-0031 (hard: an explicit GAP node with no source material). All numbers come from
`dag/pfp/llm_ladder/pilot/pilot_*.json`, the run folders under `dag/results/<NODE>/runs/*_ladder*`, and
`budget_ledger.json`. Anthropic spend of the whole task: **0.605 USD** (Haiku 0.0040, Sonnet 0.0641, Opus 0.2632,
Fable 0.2736); paid OpenRouter 0.0004 USD; 86 free calls answered (Groq 60, OpenRouter free 26).

* **Escalation behaved as designed.** TFQ-0028 and TFQ-0022 were accepted at tier 0 (free). TFQ-0031 went through
  every tier up to Opus under the default policy and ended with no accepted entry for 0.084 USD: the node has nothing
  to ground. With `--abstain-stop 2` the same node stops at tier 0 after two valid empty answers, for 0 USD.
* **Same packet, each Claude tier (one call each).** TFQ-0028: Haiku 7 verified / 0 refused for 0.0016 USD, Sonnet 9 / 0
  for 0.023, Opus 12 / 0 for 0.078. TFQ-0022: 1 / 0, 2 / 0, 2 / 0 for 0.0007, 0.016, 0.056. TFQ-0031: Haiku 0, Sonnet 0,
  Opus 4 verified / 1 refused for 0.059, Fable 4 / 2 for 0.274. Verified entries per dollar fall by about 10 times from
  Haiku to Sonnet and another 2.5 times to Opus.
* **Host catches** (all stored attempts, replayed through the current verifier): false numeric claims 9, composition
  type mismatches 6, unparseable or truncated replies 14, vacuous proofs 5, wrong signatures 4, nonexistent or relocated
  declarations 5, statement drift 1, schema violations 6. 32 negative entries are in `_hallucination_index.json`.
* **Two harness defects were found by the pilot and fixed.** (1) Free reasoning models burned the whole `max_tokens` on
  hidden reasoning (empty content); they now run with reasoning off or low. (2) Models copied the `path::decl` text of
  an `@SRC` line into one field, which the verifier judged "wrong location"; `@SRC` now has `path | decl | kind`
  columns and the verifier reads the plain meaning of a mis-laid citation (still checking it). The control arm's refused
  fraction on TFQ-0028 fell from 0.18 to 0.04 with the packet change alone. Earlier run records are sealed with the
  verifier of their day; `replay.py --report` shows the current verdicts and `--rebuild-index` rebuilt the index.
* **Did the guided retry improve on the first attempt?** Not reliably. Paired by model, four free attempts per arm,
  current verifier. TFQ-0028: refused fraction 0.11 -> 0.16 (round 1), 0.18 -> 0.16 with verified entries 18 -> 27
  (round 2), 0.04 -> 0.12 (round 3). TFQ-0022: no change in rounds 1 and 2; in round 3 the guided models answered with
  empty arrays (verified 2 -> 0): the injected refusals made them abstain. TFQ-0031: no claims in either arm. With
  n = 4 this is descriptive; there is no evidence that injection lowers the refusal rate, some that it raises
  abstention, and some that injected positives raise yield when the node has groundable material.
