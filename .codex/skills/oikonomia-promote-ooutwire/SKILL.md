---
name: oikonomia-promote-ooutwire
description: "Job search help for the project author. Resumes, cover letters, interview prep, application tracking, branding."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# oikonomia-promote-ooutwire

**AuthorityEffect:** `None`. Governed jointly by **`L3_nous_oikonomia`** (Council of Economy, Career & Value Realization) and **`L3_nous_mimesis`** (Council of Media, Marketing & Aesthetics). Enforces claim discipline (`[user_global]`), lowercase snake_case naming, zero markdown linter defects, and mandatory investigation logging.

## invariance_level: Tier 10

## Governing Councils

| Council | Jurisdiction | Key Responsibilities |
| --- | --- | --- |
| **`L3_nous_oikonomia`** | Economy, Career & Strategy | Career positioning, resume optimization, interview prep, job hunt tracking, business model strategy. |
| **`L3_nous_mimesis`** | Media, Marketing & Presentation | Branding, visual/textual poiesis, product marketing, pitch decks, LinkedIn presentation, external messaging. |

---

## Core Capabilities & Workflows

### 1. Resume & Career Asset Optimization

- **Data Source:** Reviews all master career assets under `job_hunt/resumes/` (`cv_master_updated_2026.md`, `career_objective_resume_versions.md`, `sentinel_supporting_document.md`, `cover_letter_io_associates_2026.md`).
- **Tailored Resumes:** Generates position-specific markdown/LaTeX resumes highlighting senior software architecture, AI/ML engineering, Rust/Python production development, and Clean Architecture leadership.
- **LinkedIn & Portfolio Alignment:** Synchronizes LinkedIn summary, work experience highlights, and GitHub portfolio showcases with `job_hunt/resumes/linkedin/`.

### 2. Job Hunt Application Tracking (`job_hunt/`)

- Manages application pipelines, company target lists, compensation goals, recruiter contacts, and interview follow-up schedules.
- Integrates with local tools in `job_hunt/job_hunt_app/` and `job_hunt/content_jobs/`.

### 3. Interview Simulation & Technical Defense Sandbox

- **Behavioral STAR Framing:** Formulates STAR (Situation, Task, Action, Result) narratives highlighting high-impact technical delivery and leadership.
- **Technical & System Design Defense:** Simulates deep-dive interview questioning across Rust performance, Clean Architecture, Pydantic v2 validation, database indexing, and LLM agentic orchestration.

### 4. Sentinel & Engine Marketing Strategy

- **Product Positioning:** Translates complex theoretical research (CODA, GTLA, FOC, DIME, 5-morphism pipelines) into accessible executive summaries, investor pitches, and public product landing pages.
- **Media & Content Factory (`mimesis`):** Collaborates with `L3_nous_mimesis` to design visual diagrams, interactive demo launcher cards, blog posts, and technical whitepapers.
- **Public math legibility (forums):** For MathOverflow, Lean Zulip, Math.SE, and LinkedIn math essays, route through the `public-math-legibility` RGB pipeline (proposed skills Entry 0015–0021). Ops home: `atlas/coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction/docs/lean_zulip_legibility_ops.md` and `mo_mathse_question_pack.md`. **Hard rules:** no house dialect on forum posts; no LEAN_TOY-as-theorem; agents draft, human posts; Thanatos+Glossa veto override marketing.

---

## Skill Expansion Protocol

Whenever `oikonomia-promote-ooutwire` identifies new marketing, business, or career workflow requirements:

1. Formulate candidate skill proposals (e.g. `mimesis-brand-storyteller`, `oikonomia-interview-simulator`).
2. Land proposals directly in `operads/skills/ooutwire/proposed_skills_register.md` and `operads/skills/ooutwire/recommended_skills_to_build.md` for human review.

---

## Mandatory Defect Investigation Logging (`RULE_DEFECT_INVESTIGATION_LOGGING_001`)

Whenever `oikonomia-promote-ooutwire` encounters missing resume data, unaligned career records, application tracking defects, or marketing presentation errors:

1. Automatically create a formal investigation report under:
   `engine/sentinel_councils/councils/blackrod/investigations/investigation_{YYYYMMDD}_oikonomia_promote_{defect_id}.md`
2. Include error context, root cause analysis, affected files, and recommended workflow remediation plan for Blackrod review.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
