---
documentation_contract: symbol-game-documentation/v1
title: "004. Proposal Fidelity Protocol (PFP) & The Symbol Game"
kind: documentation-hub
audience: [players, engineers, coding-agents]
status: active
maturity: canonical-navigation
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - pfp
  - operads/contracts/typed_capabilities_v1.py
  - engine/crates_rs/core_symbol_game
  - engine/crates_rs/core_symbol_game_runtime
source_revision: 45ba3a7dc032631d6697904cb73e20762b56353c
last_verified: 2026-10-12
---

# 004. Proposal Fidelity Protocol (PFP) & The Symbol Game

Start with one useful task, an explicit prompt/response contract and an independent
check. Demonstrate a simple, cost-effective, repeatable procedure, then add
representations, templates, modes, stages, loops or operation orders when they
answer a concrete question. Targeted discovery of LLM/system failure modes,
antibodies and useful patterns is a second goal. PFP remains work in progress;
observed failures determine where more engineering is needed.

The fixed pilot grid and generator are retired. The retained seed catalog and
dimension registers offer choices, not a requirement to run every combination.

## Start here

| Task | Current route |
| --- | --- |
| Use the finite-QM derivation prompt, stages and mode | [Finite-QM PFP workflow](docs/22_unified_pfp_v4_operad_workflow_and_hacks.md); actual prompt template, six stages, six LLM techniques and native certificate checks |
| Run a checked example, use an IDE-authored witness, or replay a live capture | [Practical PFP and discovery](_how_to_play/13_practical_pfp_and_discovery.md) |
| Run ordinary Adversary work through PFP in Python or the current IDE | [Shared task turns](../../../pfp/documentation/pfp_task_turn.md#shared-adversary-use); checked prose remains explicitly unverified |
| Attempt an original challenge with Adversary and its original judges | [Adversary challenge play](docs/18_original_challenge_play.md); IDE/OpenRouter commands, actual results and open experiment requirements |
| Play a full bounded cochain-repair session | [Mechanism sessions](docs/19_bounded_mechanism_sessions.md); C006 moves, admission, replay and C004 slot decoding |
| Examine bounded graph rewrites and optional Julia/DSPy demos | [ACSets and DPO experiments](docs/20_acsets_dpo_and_optional_backends.md); 25 prompt and 25 cochain controls, with no new default dependencies |
| Understand the new interfaces, mode availability and lessons | [Current types and learnings](docs/16_current_types_and_learnings.md) |
| Understand which stages use a model or host | [Eight-stage pipeline](_how_to_play/10_eight_stage_pipeline.md) |
| Inspect captures or troubleshoot a refusal | [Output layout and troubleshooting](_how_to_play/12_output_layout_and_troubleshooting.md) |
| Learn the board and basic moves | [Novice quickstart](_how_to_play/00_quickstart_how_to_play.md) and [ten useful routes](_how_to_play/06_ten_useful_ways_to_play.md) |
| Explore other play profiles | [Modalities atlas](_how_to_play/07_all_ways_to_play_the_symbol_game.md); research profiles are not a runtime capability guarantee |
| Inspect PO035 failures and experimental prompt roles | [Numbered prompt roles and PO035 play](docs/16_numbered_prompt_roles_and_po035_play.md) |
| Find current runtime owners and replay historical trials | [Runtime ownership and historical replay](docs/17_runtime_ownership_and_replay.md) |
| Verify installed integration, strict IDE handoffs and durable run budgets | [Migration execution plan](../../../pfp/documentation/pfp_migration_and_integration_plan.md); hard live liability remains a separate qualification |

The active Python application is `pfp`, with `pfp`, `symbol-game`
and `level-engine` entrypoints. Its [application guide](../../../pfp/documentation/pfp_seed_execution.md)
and [collated bounded results](../../../pfp/documentation/pfp_consolidation_plan.md#bounded-implementation-handoff--2026-10-12)
provide implementation detail and observed limits. The recorded live DEMO_07
run and zero-call replay are finite evidence about that run, not evidence that
PFP works on every task.

## Pilot status at `201dc8d` (2026-10-15)

This section records what the pilot estate holds at commit `201dc8d`. It is
dated and is not revalidated by later edits.

**Where the pilots are.** 204 pilot folders, `pilot_0000000` to
`pilot_0000203`, are under [`adversary/tests/pilots/`](../../../adversary/tests/pilots/README.md).
The live matrix is [`matrix/max_pilot_matrix.yaml`](../../../adversary/tests/pilots/matrix/max_pilot_matrix.yaml)
(75 entries). Its entries have no execution-state field, although the pilots
README says the matrix records execution state. The `pilot_matrix.yaml` file
and `PM-` ids added in PR #544 are no longer in the tree; no page in this folder
pointed to them.

**What has been run.**

| Run | Calls | Result | Source |
| --- | ---: | --- | --- |
| All pilot test folders with a real reply | 378 replies | 13 `ACCEPTED` | per-test `response.yaml` |
| Dossier replay on a free Nemotron model | 300 | 0 accepted | same |
| `deepseek-v4.1-flash` replies | 50 | 13 accepted | same |
| PFP-PILOT-001, four representations | 64 | validation rate raw 0.938, structured 0.75, relational 0.75, symbolic 0.812; one call per cell | [`max_pilot_matrix.yaml:2337-2358`](../../../adversary/tests/pilots/matrix/max_pilot_matrix.yaml) |
| PO035 | 40 | 0 accepted; a compact rerun (15 calls) had 0 schema-valid replies | [PO035 play](docs/16_numbered_prompt_roles_and_po035_play.md), [compact rerun](../../../adversary/tests/pilots/evidence/po035_simplified_20261012/README.md) |
| Claude gate runs, 2026-10-14 | 74 | Haiku 5.5 was 8 of 8 PFP-valid; 22 failures were Markdown-fenced replies; the SQLite form gave no advantage | [`empirical_observations_20261014.md`](../../../pfp/documentation/empirical_observations_20261014.md) |

With one call per cell, the PFP-PILOT-001 rates do not separate the four
representations.

**Known defects that affect these numbers.** In
`pfp/infrastructure/model_backends.py`, the budget check at `:206`
always raises `BudgetExceeded`, missing token counts default to 0 at `:283`,
`choices` is read without a guard at `:285`, and no seed is sent (`:222`). In
`openrouter_seat_gateway.py:243-248` a transport error after send is booked at
0 µUSD and a fallback send follows. In `pilot_runner.py:562-563` the grade
accepts `{"answer":3,"status":"REFUSED"}`. Prompt lineage is typed in
`prompt_types.yaml` but is not filled in run receipts.

**Prompt version drift.** `versioned/README.md` names v1.0.3 as current;
`numbered_prompts.py:33` selects v1.0.4. The prompts README lists
`golden_prompts/`, `examples/` and `originals/`, which do not exist.

**Certified ladder.** The H0–H13 design at
[`certified_ladder/design.md`](../../../adversary/tests/pilots/certified_ladder/design.md) was registered
on 2026-10-11. Only its gate controls have run
([`p0_gate_controls_receipt.json`](../../../adversary/tests/pilots/certified_ladder/receipts/p0_gate_controls_receipt.json)).

**Next.** [EPIC-OE-OEWAS-012](../../../product_planning_office/plans/epics/oewas/epic_oe_oewas_012_adversary_operad_binding_and_management_ladder_pilot_plan.md) proposes a management ladder M0–M6 with two
new arms: A5, a typed operad tree of turns, and A6, repair and reuse. It runs in
stages P0–P4. P0 makes no provider call. Every paid stage waits for Jeremy's
written approval; the first paid stage is capped at $0.10 (decision D4, decided
2026-10-15). The epic lists the fixes above as prerequisites before P2 counts as
evidence.

### Coda-atlas prompt pilots at `6023941`

[`atlas/coda_atlas/prompts`](../../../atlas/coda_atlas/prompts/)
holds two pilots that compare an English prompt with an "operad" prompt. Neither
supports its findings.

- **pilot_001** (three tasks, two arms, one run each, model recorded only as
  "DeepSeek"). Its evaluator
  ([`evaluator.py:45-66`](../../../atlas/coda_atlas/prompts/pilots/pilot_001/evaluator.py))
  scores by regular expressions for words such as "decoy", "witness" and
  "antibody". The operad prompt asks for those words, so the 2.33 versus 5/5
  scores grade the prompt's wording, not the answer.
- **pilot_002** (R7, A4 and A10 in two arms, plus three single-arm items, one
  run each, no model recorded). Its evaluator
  ([`evaluator.py:77-90`](../../../atlas/coda_atlas/prompts/pilots/pilot_002/evaluator.py))
  hard-codes `score=5.0`. Its PASS checks look for strings the prompts already
  contain.
- **Two certificates it reports as PASS are wrong.**
  - R7: the step "−250 Σ(a²−1) + 1000(a²+b²+c²+d²−4) = 0" treats `h_k·f_k` as
    `−250·f_k` when it is `−250·f_k²`. The review's exact expansion leaves 11
    non-zero monomials, with value −1001 at the origin instead of −1. The task
    is also circular: `g_sep` contains the unknown `σ0`.
  - A4: with `v1 = (−3,1,−2,−2,2,1)`, `v2 = (−3,1,1,−1,3,3)` and
    `v3 = √6·(−1,1,1,1,1,1)`, `‖v‖² = 23 + 30 + 36 = 89`, not the 82 the
    completions state. So `‖W_strict‖₁ = 83` and `δ_crit = 6/83` in item 04 are
    wrong. The "exact match with the Rust solver" is circular: the Rust test
    asserts the same −7 on the same synthetic Gramian.
- The tasks rely on `core_mub` material that the 2026-10-15 review found
  unsound: the Karlsson family, the "H6" label and literal collar constants.
- No raw provider replies, model ids, costs or receipts are stored. The
  completions read as authored text rather than returned replies; this is
  inferred, not shown.
- `test_cases/ooutwire*.md` have no inputs, expected outputs or oracles; they
  are notes, not test cases.

A replacement, registered as pilot_003 and now in
`atlas/coda_atlas/prompts/pilots/pilot_c054_layouts/`, is the first paid cut of stage P2: 36 exact
linear-algebra items from Adversary's `c054_exact_linear_systems` oracle, three
arms (English, operad, and English padded to the operad prompt's length), blind
grading, raw receipts, and a worst case of about $0.07, under the $0.10 cap.
The full review is in the 2026-10-15 OEWAS and Adversary report, appendix
`appendix_prompts.md`.

Result (2026-10-15, run_002, `claude-haiku-5-5`, 108 of 108 calls): PASS 35
(English), 33 (operad), 35 (padded) of 36. The exact McNemar test gives
p = 0.5, 0.5 and 1.0, so no layout differs detectably. The run cannot resolve
differences below about 30 points. Both operad failures were integers written
where the format asks for strings. The pilot README records the details.

## Foundations and deeper study

| Material | Route |
| --- | --- |
| Foundations and two-object distinction | [Foundations](levels/meta_00_symbol_game_foundations.md) |
| Historical mathematical curriculum | [Levels 0–21](levels/meta_01_symbol_game_historical_curriculum.md) |
| PFP and packet envelopes | [Protocol monograph](levels/meta_02_symbol_game_pfp.md) |
| Formal proof ledger | [Proof ledger](levels/meta_03_symbol_game_proof_ledger.md); consult its own source/evidence scope |
| Levels and lesson crosswalk | [Levels catalog](levels/) and [crosswalk](levels/curriculum_lesson_crosswalk.md) |
| Curriculum and laboratories | [Curriculum](curriculum/README.md) |
| Mathematical specifications | [Math](math/) |
| Grammar and rewriting | [Grammar](grammar/README.md) and [rewriting](rewriting/README.md) |
| Engineering reference | [Reference manuals](docs/README.md), [native host](docs/08_native_rust_host_architecture.md) and [runtime actions](docs/09_runtime_actions_and_governor.md) |
| Research and pilot material | [Retained task/seed estate](../../../adversary/tests/pilots/README.md) and the [pilot status below](#pilot-status-at-201dc8d-2026-10-15) |

## Reading the evidence

A prepared prompt is not a model trial. A schema-valid reply is not an accepted
witness. A missing tool is not a mathematical counterexample. A model's success
claim or persona agreement does not replace the task's checker.

Python orchestration, native exact-operation checks and Lean obligations have
different scopes. Read the deciding implementation and the evidence attached to
a particular run. A stage prefix before host stage 5 cannot establish mathematical
acceptance. A glyph roundtrip does not establish arbitrary semantic equivalence.
Generated guidance remains unadmitted until its applicable checks are met.

Some older manuals retain historical `ow/...` and retired package references.
Use the current routes above for execution. This navigation update does not
revalidate every theorem, notebook or historical result in the larger corpus.

AuthorityEffect: None. [Compact agent index](llms.txt) · [Master index](index.md).
