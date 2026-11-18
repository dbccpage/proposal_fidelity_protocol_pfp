# Historical AutoP Maintenance Instructions

Preserved prior instruction body for explicitly requested maintenance. The
current AutoP SKILL.md selects routine IDE learning by default. This reference
does not trigger a whole-estate scan, admission queue or receipt after each run.
Resolve current canonical paths and scope before executing legacy commands;
do not rewrite historical records to fit current layouts.

---
name: auto-oe-autop
description: "Run the self-improvement meta-pipeline in fixed order, applying only HIGH confidence review recommendations."
invocation: entry
operad_source_colours: ["State", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [meta]
---

# Auto OE Autop

**Status:** canonical-candidate

## Sequential Execution Protocol

When triggered or when receiving a **PFP Swarm Self-Review Handoff**, execute the following 7 stages sequentially (Stages 0–7):

```text
[Stage 0] Process PFP GTLA Swarm Self-Review Receipt (AuthorityEffect: None)
          │ Extract HIGH-confidence corrections & GTLA compliance findings
          │ Accept schema core.swarm_self_review.v1 under RUN_OE_* support
          │ (applied:true HIGH process landings = already on disk; do not re-apply)
          ▼
[Stage 1] /auto-skill + /auto-anti-skill + every anti-pattern skill + /auto-anti-skill-search + /governance-wdp
          │ Detect signals → write episodes (runs/skill_compiler/episodes/)
          │ → invoke auto-anti-skill (segment-dialogue + mine-candidates)
          │ → call every `.agents/skills/*anti-pattern*` package, including
          │   `techne-code-lean4-anti-patterns` (Python, Rust, SQL, Lean 4, and the lint)
          │ → trigger intelligence digestion & archiving into _intelligence/archive/
          │ → scrub retired research module references across tests (RULE_SHADOW_PROTOTYPE_RETIREMENT_001)
          │ → run auto-anti-skill-search against truth-boundary canary fixture banks (O^-)
          │ → audit Primitive Difference honesty via governance-wdp
          │ → write inert candidates to .agents/antiskills/ooutwire/
          │ NEW_SKILL → admitted automatically; register records it
          ▼
[Stage 2] /auto-symmetry-hunter
          │ Packaging parity (all active host roots) AND knowledge_parity semantic check
          │ (python operations/skill_operad/skill_compiler/knowledge_parity.py)
          │ In single-seat workspace trees (where only .agents/ is present), cross-host
          │ packaging mirrors are verified as SKIPPED rather than conjuring untracked trees.
          ▼
[Stage 3] /auto-improve-autoskill + /auto-obstruction-hunter (with /adversary)
          │ Capture-rate / compressive audit; MUST run budget_gate.py
          │ Scan structural, schema & mathematical non-fit via auto-obstruction-hunter (Levels 0-9)
          │ [DEADLOCK ESCALATION]: If cycle obstructions or gauge deadlocks occur (Phi_1 > 0),
          │ trigger Act IV 9-Dot Gauge Break via /adversary to unfreeze assumptions
          ▼
[Stage 4] /auto-review-agents
          │ Audit agent panel, council ownership & model tier assignments
          ▼
[Stage 5] /auto-review-skills
          │ Audit skill garden & meta infrastructure (_shared, _templates, .agents/registry);
          │ run skill_compiler eval_runner.py when compiler/routes touched (non-regression);
          │ check_skill_usage.py is WEAK hint only — not primary retire signal;
          │ archive rule: 30+ days without activity is archived automatically
          │ only after history, exemptions, host roots, and audit programs resolve;
          │ a missing prerequisite is BLOCKED and moves nothing;
          │ hard delete disabled until retirement evidence exists
          ▼
[Stage 6] /auto-suggest-new-skills
          │ Discover & evaluate candidates; LAND every proposal in ooutwire inbox (HARD)
          │   → .agents/skills/ooutwire/proposed_skills_register.md  (append Entry NNNN)
          │   → .agents/skills/ooutwire/recommended_skills_to_build.md (refresh ranked queue)
          │   → 4-host mirror: .agents/.claude/.codex/.grok
          ▼
[Stage 7] /auto-docs
          │ Read session activity & synthesize markdown logs to .agents/documentation/sessions/
          │ Execute techne-comment-slop-hunter-killer to scan & re-route LLM comment slop
          │ Mirror documentation atomically across all active host roots (.claude, .codex, .grok)
          ▼
[Stage 8] digest-governance, then apply-governance-proposals
          │ Farm documentation, anti_pattern, teamwork, harvest, omc_dags,
          │ core_paper_reviews, and symbol_game/runs (absent is a finding)
          │ Apply only checked-in repairs whose pre-edit file hash still matches
          │ Mirror the canon bytes of those files to .claude, .codex, and .grok
```

### Stage 6 landing (HARD — incomplete without disk write)

Stage 6 is **not** finished when suggestions exist only in the autop report chat.

| Required artifact | Path |
|---|---|
| Append-only proposal ledger | `.agents/skills/ooutwire/proposed_skills_register.md` |
| Ranked build queue for ooutwire | `.agents/skills/ooutwire/recommended_skills_to_build.md` |
| Folder readme | `.agents/skills/ooutwire/README.md` (create if missing) |

- **HIGH** skill *edits to existing admitted skills* apply under the execution law below.
- **New skill packages are admitted automatically.** They are written directly into
  `.agents/skills/<name>/SKILL.md`, mirrored to every host root, and recorded in the register
  as `ADMITTED`. The inbox remains the audit trail, not a queue that blocks.
- **MEDIUM / LOW** are still recorded in the register with their confidence, so a weak
  admission is legible as weak rather than indistinguishable from a strong one.
- Autop report must cite the ooutwire paths and list Entry IDs written this run.

---

## The Execution Law

Amended 2026-09-01 by the repository owner. The former rule read *"New skill packages are
never auto-admitted"* and required human promotion before a package became live.

- **HIGH Confidence:** Automatically applied to existing admitted skill garden files and
  cross-host skill edits.
- **New skill packages (any confidence):** Admitted automatically on creation.
- **Counterweight — this is what replaces the human gate.** Admission is now cheap, so
  *retention* carries the cost: `/auto-review-skills` archives any package with no activity
  for **30 days or more**. Admission is reversible by disuse; it is not a promotion.
- **MEDIUM / LOW Confidence:** Admitted, but recorded with confidence in the register.
- **Authority Ceiling:** `AuthorityEffect: None`, unchanged. Automatic admission changes who
  may create a skill package. It grants no skill any authority it did not already lack, and
  an admitted package still certifies nothing.

## Automation & CLI Runner

AutoP provides a unified sequential orchestrator script:

```bash
python .agents/skills/auto-oe-autop/scripts/orchestrate_autop.py [--receipt <path>] [--output <receipt.json>] [--verbose]
```

### Swarm Integration & Handoff

`auto-oe-autop` is automatically invoked at the conclusion of `core-paper-review-swarm` (`orchestrate_paper_review.py run-all`).

- The swarm passes `--receipt <swarm_receipt.json>` as input to Stage 0.
- AutoP verifies knowledge parity, 4-host mirroring, the skill budget gate, compiler non-regression evals, and logs episodes for any observed failures.
- Output receipt is saved to `runs/autop_receipt.json` under `AuthorityEffect: None`.

### Execution Protocol & Async Reactive Handling

1. **Process Execution:** Execute `py -3.12 .agents/skills/auto-oe-autop/scripts/orchestrate_autop.py --verbose` on Windows (or `python3` on Unix) to ensure `sys.executable` invokes Python 3.12 across all stage subprocesses. If dispatched as a background task, await completion via reactive wakeup; do not poll manually.
2. **Worktree & Architecture Path Discovery:** Candidate resolution paths automatically discover compiler scripts under both canonical clean architecture (`operations/`) and worktree staging roots (`operads/`).
3. **Graceful Runtime Degradation:** In environments where legacy runtimes (e.g. `engine.crates.prompt_civilization.cli`) are absent, `auto-anti-skill segment-dialogue` records a non-fatal warning under `warnings` without failing Stage 1.
4. **Mandatory 9-Stage Receipt Audit:** Upon completion, inspect `runs/autop_receipt.json` ensuring all 9 stages (0 through 8) report `status: "PASS"` and summarize findings according to Claim Hygiene invariants (supports, does not support, narrowest defensible claim, next test needed).

---

## Context Protection & Token Budget Discipline

1. **Incremental Execution:** Execute stages 0–7 sequentially. Inspect only target files required for each stage; never load the full skill garden or multiple 50KB+ files into context simultaneously.
2. **Modular References:** Keep SKILL.md files under 300 lines. Move large indexes, historical logs, and playbooks into `references/` subdirectories.
3. **Archived Ledgers:** Append new proposals to `ooutwire/proposed_skills_register.md` (active entries). Archive entries >50 into `ooutwire/proposed_skills_register_archive_v1.md` when the active register exceeds 20KB.
4. **Knowledge Parity & Doctrine Fencing:** When referencing former 4-host estate rules or legacy verifiers, always fence them with explicit historical tags (`(historical)`, `(former doctrine)`, `superseded by governance-host-parity`) so they pass the `knowledge_parity.py` banned doctrine filter.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
