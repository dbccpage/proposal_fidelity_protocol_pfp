---
name: techne-base-swarm-inward-purity-auditor
description: "Check adversary.stage stays a generic runtime with no character lore or domain-specific branching."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [swarm, clean-architecture, purity]
---

# Base Swarm Inward Purity Auditor

**Status:** `ADMITTED`
**AuthorityEffect:** `None` (Architectural auditor; emits layer compliance receipts)
**Governance Council:** `L3_logos_techne`

---

## 1. Prime Directive

The **Base Swarm Inward Purity Auditor** enforces architectural generality and decoupling between generic agentic scheduling runtimes and specialized narrative swarms.

---

## 2. Invariants & Rules

1. **Base Engine Generality:**
   - `adversary.stage` is a pure generic base framework containing generic scheduling, typed sink protocols (`UtsSink`, `UnsSink`, `DdaSink`, `SgtSink`, `CemeterySink`, `AntibodySink`, `GenealogySink`), and telemetry.
   - It must NEVER contain character lore, dramatic novella rendering, or domain-specific dialectic branching.
2. **Bounded Swarm Isolation:**
   - Specific swarms (such as the 7-Act Master & Primal Dual dialectic) must be isolated in dedicated bounded contexts (e.g. `adversary`) with standard Clean Architecture layer boundaries.
3. **Canonical Output Emission:**
   - Bounded run executions must emit exactly 4 canonical output files (`receipt.json`, `novella.md`, `dda_actions.jsonl`, `summary.json`) into isolated run folders under `_intelligence/_<swarm>/runs/<task_key>/`.

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Ensure pure UTF-8 without BOM (`\xef\xbb\xbf`) with 0 linter errors and 0 warnings.
