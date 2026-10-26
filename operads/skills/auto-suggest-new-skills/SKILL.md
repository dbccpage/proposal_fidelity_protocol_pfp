---
name: auto-suggest-new-skills
description: "Suggest new skills from session context, receipts, papers and external repos; evaluate and admit them to the register."
invocation: discipline
operad_source_colours: ["Paper", "Audit"]
operad_target_colour: "Code"
operad_arity: 2
operad_residual: "unknown"
families: [meta]
---

# Auto Suggest New Skills

**Admission:** experimental

## 1. Prime Directive & Nonclaim Fence

$$\bbox[5px,border:2px solid #4CAF50]{\text{Discover, type, audit, and package new skills using Algorithm Prime 000. AuthorityEffect: None.}}$$

> [!IMPORTANT]
> **Authority Ceiling**: Creating a skill does **not** grant `AuthorityEffect`
> or certify model output. Since 2026-09-01 admission is automatic: Stage 6
> writes the live package, mirrors it to all active host roots, and records it in
> the register as `ADMITTED`. What that buys is a file in a directory. It grants
> the package no authority it did not already lack, and retention is earned
> separately — `/auto-review-skills` archives anything idle 30+ days.

---

## 2. Algorithm Prime 000 Skill-Discovery Protocol (12 Steps)

Every skill suggestion pass evaluates the 12-step declaration order:

| Step | Protocol Phase | Operational Skill-Discovery Mapping |
| ---: | --- | --- |
| **1** | **Declare Carrier** | Active session history, God runs (`_god/runs/`), external registries (`k-dense-ai/scientific-agent-skills`). |
| **2** | **Declare Primitive Difference** | Capability gap: $\delta_{\text{skill}} = \text{RequiredWork} \setminus \text{AdmittedSkillGarden}$. |
| **3** | **Declare ZeroRel** | Equivalence relation ($\sim_{\text{skill}}$) identifying duplicate or overlapping skills across existing skills. |
| **4** | **Construct Cochains** | Skill lifecycle progression: $C^0 \text{ (Raw Idea)} \xrightarrow{d_0} C^1 \text{ (Draft SKILL.md)} \xrightarrow{d_1} C^2 \text{ (Cross-Host Sync)}$. |
| **5** | **Compute Quotient Residual** | $Q_{\text{skill}}^1 = C^1 / \operatorname{im}(d_0)$ — true novel capabilities needed after deduplication. |
| **6** | **Separate $\Phi_1$ from $\Gamma_2$** | Diagnostic gap ($\Phi_1$: missing capability) vs Invariant compliance ($\Gamma_2$: security/authority violation). |
| **7** | **Declare Observer Profile** | Target environment audit ($J = \{\text{.agents}, \text{.claude}, \text{.codex}, \text{.grok}\}$). |
| **8** | **Identify Witness Certificates** | Replayable session logs, tool error tracebacks, or external repo commit SHA receipts. |
| **9** | **Search Operator Lifts** | External repositories (`k-dense-ai/scientific-agent-skills`, arXiv, OpenAlex, GitHub). |
| **10** | **Route Survivors** | Pass candidates through `lib-skill-admission-hygiene` (secrets scan, authority ceiling, license check). |
| **11** | **Terminalize** | Write the live package, mirror across active host roots, append the register record, refresh the queue. |
| **12** | **Compare to Literature** | Benchmark against open-agent skill standards and state-of-the-art co-scientist architectures. |

---

## 3. Inputs & Sources

1. **Active Session Context & Tool Errors:** MCP failures, repetitive complex multi-step commands, domain-specific research needs.
2. **Recent God Run Receipts:** `omega_engine/_god/runs/` (e.g. `brg_campaign`, `paper_repair_and_skill_panel_sweep`, `qmcoda-hott-frontier`).
3. **Foundational Research Series:** `100_mathematical_foundations` and `008_omega_engine_master.md`.
4. **External Registries:** `https://github.com/k-dense-ai/scientific-agent-skills`, arXiv, PyPI, OpenAlex.

---

## 4. Discovery & Suggestion Workflow

### Phase 1: Scan Active Session & God Runs

1. Scan `_god/runs/` for recurring manual patterns, un-automated paper-repair tasks, or missing domain tools.
2. Identify repeated user prompts or complex multi-turn workflows that lack a dedicated skill.

### Phase 2: Query External Registries & Web

1. Search external scientific and AI agent registries (e.g. `k-dense-ai/scientific-agent-skills`, Cisco AI Defense Skill Scanner, Agent Skills Standard).
2. Evaluate candidates for data analysis, hypothesis tree refinement, scientific plotting, and formal verification.

### Phase 3: Admission landing

1. **Deduplicate:** Compare the candidate with admitted skills and pending
   ooutwire entries. Prefer extending an existing skill or code gate.
2. **Fence authority:** Reject candidates that waive evidence or claim
   promotion. Every proposal states `AuthorityEffect: None`.
3. **Admit and record:** Write the live package, mirror it across active host
   roots, then append a record marked `ADMITTED` and refresh the
   ranked queue. The register is the audit trail, not a gate.
4. **Suggest retirement, never delete:** A stale or redundant package may
   receive a retirement-review suggestion. This stage never culls or deletes a
   live skill; age-based archive belongs to `/auto-review-skills`.

---

## 4b. Mandatory landing zone: ooutwire inbox

Every suggestion pass, including `/auto-oe-autop` Stage 6:

1. Appends one record per surviving candidate, marked `ADMITTED`.
2. Refreshes the ranked build queue.
3. Mirrors the live package and the ooutwire inbox across active host roots.
4. Leaves retirement and hard deletion to a separate workflow; age-based
   archive is automatic under `/auto-review-skills`.

### Canonical paths (write here)

| File | Action |
| --- | --- |
| `omega_engine_operads/skills/ooutwire/proposed_skills_register.md` | **APPEND** one `### Entry NNNN:` block per candidate |
| `omega_engine_operads/skills/ooutwire/recommended_skills_to_build.md` | **REFRESH** the ranked "Build next" table |

### Host root mirror (after write)

Copy the new package directory **and** the `omega_engine_operads/skills/ooutwire/` inbox to
every other host root. Derive this list from the filesystem (`ls -d .*/skills`):

```text
.claude/skills/
.codex/skills/
.grok/skills/
```

### Entry template (append to register)

```markdown
### Entry NNNN: `/goo-skill-name`

* **Date Proposed:** YYYY-MM-DD
* **Source Session:** <short label>
* **Proposed Target Path:** `omega_engine_operads/skills/goo-<skill-name>/SKILL.md`
* **Confidence Level:** **HIGH** | **MEDIUM** | **LOW**
* **Category / Family:** `<category>` / `<family>`
* **Description:** <one paragraph; nonclaims explicit>
* **Implementation Status:** `ADMITTED`
```

### Ranking rules (recommended_skills_to_build.md)

1. Sort: HIGH before MEDIUM before LOW; within band, prefer leverage / session demand.
2. Superseded rows leave the build table but remain in the append-only register.
3. Set **Last refresh:** date at top of the queue file.

### Nonclaims

Admitting a package creates a file and mirrors it. It does **not** retire
another skill, mint authority, or make the package's claims true. An admitted
skill that has never run is an admitted skill that has never run, and the
register records confidence so a weak admission stays legible as weak.

---

## 5. Paper Outline Proposal: Omega Skill Lifecycle Management System

```markdown
# Paper 011: Omega Skill-Capture, Agent Discovery, and Lifecycle Management

## A Typed 12-Step Audit Protocol for Autonomous Agent Evolution

### Abstract
We present a typed, replayable protocol for autonomous AI agent skill discovery, validation, and lifecycle management based on Algorithm Prime 000. Rather than allowing un-audited skill growth or context bloat, the system applies a 12-step Quotient Residual Filter ($Q^1$) to extract novel durable capabilities, enforce multi-host synchronization, and prevent authority laundering.

### Key Architectural Sections
1. **The Skill Derivation Problem:** Context rot and prompt bloat in multi-agent environments.
2. **Algorithm Prime 000 Mapping:** Transforming 12-step mathematical cochains into skill discovery gates.
3. **The Multi-Host Parity Invariant:** Guaranteeing byte-identical skill trees across heterogeneous LLM runtimes.
4. **Empirical Evaluation:** Token reduction, precision metrics, and security boundary enforcement.
```

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
