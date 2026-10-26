---
name: oikonomia-product-manager
description: "Plan products, epics, sagas and sprints in the product planning office; keep the dev-goals plan register."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# Omega Engine Product Manager

**Hosts:** mirror to `.claude`, `.codex`, `.agents`, `.grok`.

## Related Workflows & Council Integration

## Verdict shape

## Council note (Techne)

## Forbidden claims

## Operating loop

**Class vocabulary:** `LIVE` · `ORPHAN` · `RESEARCH_HOLD` · `BLOCKED` · `SPEC_ONLY` · **`SUNSET`** · **`PROTOTYPE`**

## Ship matrix (emit every session)

## Track D → product map

### EPIC-OE-LIB-001 fence (autoskill 2026-07-31 HIGH)

**Planning mode:** when the operator says review-only / no implementation -- **write plans and maps only**; do not implement code or delete product trees. Prefer promoting durable goal changes into the **dev_goals paper + ledger + change log** so they remain algorithm-visible.
**Honest history:** before the planning office existed, this skill only emitted ad-hoc files under `runs/product/` and Track D disposition under `published/100_.../_support/`. It did **not** create epic/saga/sprint plans. The published goals paper is the coalescence of those residual ops surfaces into a register that Omega pipelines can consume.
**Idea sources (read, do not silently rewrite):**

### Mandatory Saga-Epic-Sprint Hierarchy & Audit Law

**Controlling home for drafts/receipts:** `omega_engine/omega_engine_product_planning_office/`
**Published plan register (must stay in sync):** the fundamental paper trio under `008_engine_runtime` -- see **Fundamental paper: plans → Omega algorithms** above. Office drafts implement and refine that register; they do not supersede it.

## Planning office (where plans are written)

**Consequences for planning:**

### Product stack law (operator 2026-07-26) -- controlling

**Product-manager duties w.r.t. this paper:**
**Why the product manager must load this first:**
**paper_id:** `000_omega_engine_dev_goals` · **series:** `008_engine_runtime` · **status:** `ENGINEERING_SPEC / INTERNAL_DRAFT` · **AuthorityEffect:** `None`
**This is the paper where we list exactly the plans we have** -- development goals, Prime-000 binding order, contract↔crate inventory, readiness hedges, and open obligations -- as an **engineering specification paper**, not an ad-hoc wiki.

### Fundamental paper: plans → Omega algorithms (controlling)

## Controlling doctrine

**Do not replace:** paper-adversary, Blackrod enforcement, or human release.

## When to use

**AuthorityEffect: None.** You plan, track, and refuse false-green. Humans promote.

## council: L3_nous_oikonomia (Council of Oikonomia -- Management, Allocation, Economics, PPO)

## Master Planning Document Layout (`goo-master-planning-office-reorg-guard`)

1. **Single-Level Layout:** Enforce single-level planning document layout under `_0_master_planning_documents/`.
2. **Manifest Indexing:** Keep `plans/readme.md` as the sole human epic index,
   keep exact direct-epic bytes in `plans/epics/epic_manifest.json`, and leave
   `_master_plan_manifest.md` pointer-only for epics outside
   `_master_documents/`.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
