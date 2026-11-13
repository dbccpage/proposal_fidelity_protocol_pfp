# Research committee report, 2026-11-05

AuthorityEffect: None. This is a review and a plan. No model was called,
nothing was moved or deleted, and nothing here is a measured result.

**Committee.** Eleven read-only reviewers: two on WF1–WF5 (code, and
docs versus evidence), seven inventories (the pilot estate in two halves,
the rest of the adversary research repo, the PFP research repo, the immune
research repo, the prompt-evolution research repo, the operads research
repo), one on research material inside the engine repo, and one
adversarial gap scan against current practice. Ten ran on Sonnet, the gap
scan on Run O.

## 1. Verdict on WF1–WF5

| WF | Code verdict | What the evidence really shows |
| --- | --- | --- |
| WF1 typed answer | Solid | One live accepted call on integer addition |
| WF2 full slots | Usable with fixes; slot checks are structural only | One live call; 3.5× WF1's tokens; repair moves never exercised |
| WF3 mine, then solve | Weak: its grounding check cannot fail | "2 calls" is stitched from two runs; real cost 10 actions, 7 failures |
| WF4 five agents + global check | Usable with fixes | One live run; the global check adds nothing beyond five local checks; wrong-answer path only tested with scripts |
| WF5 checked rewrite | Weak: one hard-coded sentence template behind heavy machinery | One accepted run after 4 failed miners |

Across all five: one task (integer addition), about one accepted run each,
no workflow beat WF1 on cost or accuracy, and the shipped v0.2 runners have
**zero** live runs; every cost figure comes from older, unshipped code.
`pfp/workflows` passes 201 offline tests (with `PYTHONPATH="ops;."`).

**Defects to fix first** (file:line in `pfp/`):

1. WF3 L2 grounding is tautological: the schema pins the slots to host
   constants (`workflows/wf0003/structured.py:392-430`) and `assess_l2`
   compares them to the same constants (`workflows/wf0003/workflow.py:321-357`).
2. WF4/WF5 per-agent receipts say `HOST_ACCEPTED` / `TASK_CHECKED` even when
   the total is wrong (`workflows/wf0004/workflow.py:138-146`).
3. WF4/WF5 `capture()` can crash after a charged call and lose the reply
   (`workflows/wf0004/runner.py:139-163`); WF3 already guards this.
4. Replay never checks `response.raw` against the stored wire body
   (`infrastructure/workflow_runtime.py:231-246`).
5. WF3 mining reuse is not self-contained (`workflows/wf0003/runner.py:65-79`).
6. WF5 preservation obligations are mostly round trips (`workflows/wf0005/rewrite.py:324-336`).
7. Batch dispatch leaves reservations "reserved" if the barrier breaks
   (`infrastructure/workflow_accounting.py:79`).

**Docs to fix:** add an evidence column ("1 run, 1 task") to the Workflows
table; give WF3's true cost; remove the stale branch from Workflow-Running;
reconcile Workflow-Library with `catalog.json`; label WF6–WF23 as
proposals on their own page.

## 2. How many real workflows are there?

Counting procedures, not tasks, the whole estate holds **about six**:

| Real procedure | Where it appears | Live data? |
| --- | --- | --- |
| Typed answer + host check | Pilots 0–4, 51, 52–191, dossier, ladder arm A0, the clarification contract | Yes: ~770 capsules, mostly a free Nemotron tier and DeepSeek V4.1 Flash |
| Typed refusal | Pilots 3, 7, 11, 13, 15, 19, 34; mode 14 | Yes (pilot 3, 30 replies) |
| Pre-stage before solving (mine, rewrite, workpad) | WF3, WF5, scratchpad arms, operad mining | Small |
| Ensemble + global check | WF4, frozen role submissions, debate mode | One WF4 run |
| Bounded check-and-repair loop | Pilots 49, 192–203, ladder M3–M6, code repair, critique loops | Yes: 199–203 (25 calls, 0 accepted), demo004 learning (35 replies) |
| Staged sealed packets | 8-stage seed run, mode trials, pilot 20 | Yes: one 7-call verified seed run |

Everything else is a **setting** (task family, checker, dialect, model,
temperature, rung, antibodies, stage count, attempt limit, replicate count)
or an **experiment design** wrapped around one of the six. Pilots 52–187
(136 folders) are planned capsules that differ only in task and checker
id; none was sent to a model.

### The proposed shape: a base class and extensions

- **Base: `TaskTurn`** (WF1): frozen task, one typed reply, independent
  host check, replay, accounting.
- **Procedure extensions** (each adds one thing to the base):
  `Contract` (WF2), `PreStage.mine` (WF3), `PreStage.rewrite` (WF5),
  `Ensemble` (WF4, to be rebuilt as best-of-n with a verifier),
  `RepairLoop` (WF9/WF20), `Staged` (WF8).
- **Experiment designs** (wrap any workflow): `Sweep` (WF6, WF12, WF18,
  WF22 are one design with different arm sets), `HeldOutTransfer` (WF19),
  `PreRegisteredKillTest` (from the detector-adequacy study).
- **Meta-workflows** that act on prompts or detectors rather than tasks:
  prompt evolution (mutate and select, crossover, retrieval, islands) and
  the immune lifecycle (mine detectors from failures, negative selection,
  two-signal admission, regulation, retirement, autoimmunity audit).
- **Harness gates on every run**, not research nodes: seal chain (WF8),
  replay (WF18), custody and leakage audit (WF23), commit-reveal,
  reserve/settle accounting.

In operad terms (the operads repo already defines this): a workflow is a
typed term; an extension is context substitution, slot filling, or an
operation swap with identical ports. WF4's shared miner needs fan-out,
which the current compiler refuses; that is a concrete gap.

**Effect on the DAG:** WF6–WF23 collapse from 18 nodes into three
procedure extensions, three experiment designs, two meta families and the
harness gates. WF11, WF13–WF17 become task/checker parameters of
`TaskTurn`; WF20 is a `RepairLoop` setting; WF23 and WF18 become gates.

## 3. Live data that already exists

| Source | Calls | Outcome |
| --- | --- | --- |
| Pilot capsules 0–51 | ~770 with token counts | Mostly typed-answer sweeps |
| Dossier campaign 188–191 | 120 (free Nemotron) | All refused: schema invalid |
| Derivation loops 199–203 | 25 (free Nemotron) | 0 certificates accepted |
| M5 campaigns | ~218 DeepSeek V4 Flash, ~205 Run G 2.5 Flash | v4: 79 calls, 4 accepted |
| Cost ladder v2 | 44 (34 Haiku, 7 Sonnet, 3 Run O), $0.067 | Arm data on 35 cases |
| PFP learning (demo004) | 35 replies, $0.019 | 3 accepted one-shot witnesses |
| Detector adequacy | ~1,600 Haiku, $1.00 | Pre-registered kill: dropped |
| Empirical gates | 74 Anthropic, $0.11 | Token and injection comparison |
| Claim-hygiene comparison | 106 attempts | 43 comparable pairs, 29 agree |
| Prompt evolution, immune system | 0 | Mechanisms fixture-tested only |

The prompt-evolution and immune systems are well built and tested offline,
but **neither has ever run against a model**.

## 4. What we are missing (gap scan)

Ranked by value per dollar on one cheap model:

1. Best-of-n with a verifier versus sequential repair at matched spend (pass@k).
2. Attacking the host checker itself (reward hacking; two independent checkers).
3. Calibration and abstention scoring (confidence, Brier/ECE, selective accuracy).
4. The format tax: free text versus schema-constrained output versus JSON in the prompt.
5. A prompt-optimisation baseline (GEPA, MIPROv2) against our prompt evolution.
6. Contamination checks with isomorphic twins of each task.
7. Clustered error bars and power analysis on every comparison.
8. Weak-judge debate, so the tribunal design can mean something.
9. Steering, refusal-direction ablation and probes: **local open-weights GPU
   only**; hosted OpenRouter endpoints do not expose activations or weights.
10. Lean as the host check for proof-shaped tasks.

The adversarial critique: on most of our tasks the host already computes
the answer, so the model adds nothing. Shift the item mix to tasks that are
easy to check but hard to solve (LP certificates, minimal repair, Lean).

## 5. Moving research data

The engine repo is already lean: it is a Rust workspace with no pilots or
papers. Its research material is about 60 MB that can move now (test
fixtures 34 MB, scoring ledgers, the symbol-game crate, unused domain
crates), plus 10–12 MB of science crates that `wdp` depends on and cannot
move without splitting it. The real research mass is in the sibling repos:

| From | Missing from this repo |
| --- | --- |
| PFP research repo | ~74 MB: level engine, per-challenge commit-reveal and accounting, reach data, 22 gate files |
| Operads research repo | Workflow planner, claim-hygiene family and receipts v1–v5, comparison contracts, ~200 tests |
| Immune research repo | Residual obligations, closeout receipts, 15 antibody specs, 3 tests |
| Prompt-evolution research repo | Rust crossover, convergence, island and prompt-family crates; the experiment layer it imports |
| Adversary research repo | Harness-evolution campaign shell, calibration task banks, research notes |

Before any move: a full secret scan (one evidence folder holds local
paths), and the naming scrub this repo already uses.

## 6. Proposed plan

1. **Fix WF1–WF5** (defects 1–7 and the docs), no spend.
2. **Restructure the DAG** into base, extensions, experiment designs, meta
   families and gates; keep WF6–WF23 as labelled proposals until each has a
   run.
3. **Move research material** into this repo in stages, one source repo per PR.
4. **One-model test round** on a DeepSeek Flash tier through OpenRouter
   (confirm the current version and price first): the five cheapest
   experiments from §4 (about $2), then rerun the pilot capsules that have
   live data on that one model (about $1–2). Proposed hard cap: **$5**.
5. **First runs of the two never-tested systems**: prompt evolution
   (mutate and select under a fixed checker, against a GEPA baseline) and
   the immune lifecycle (mine detectors from the round-4 failures, then
   negative selection).

Steps 3 and 4 wait for the owner's approval.
