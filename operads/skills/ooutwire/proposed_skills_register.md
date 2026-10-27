---
title: proposed_skills_register
file_name: proposed_skills_register.md
file_location: .agents/skills/ooutwire/
status: live_register
owner: ooutwire
version: v3.6.0
---

## authority_effect: None

## Proposed Skills Register (ooutwire) — Active Proposals

**Last refresh:** 2026-10-08

| Status | Count |
| --- | --- |
| `ADMITTED packages` | 306 |
| `PENDING_ADMISSION` | 0 |

### Run 2026-10-08 (Adversary Intelligence Digestion)

#### Entry 0306: `techne-paper-deposit-preflight-gate`

* **Proposed By:** Adversary Intelligence Digestion run 2026-10-08 (Mining of 74 paper reviews, 1,748 failure obstructions)
* **Confidence:** HIGH
* **Target Folder:** `.agents/skills/techne-paper-deposit-preflight-gate/`
* **Signal:** Paper review swarms repeatedly fail on basic preflight packaging defects: missing `rebuild_release.py` / `verify_deposit.py`, LaTeX/PDF hash and rendering desynchronization, MAX_PATH overflow (>250 chars) on Windows hosts, and missing dual witness certificates.
* **Evidence:** Digestion of 74 paper reviews into `paper_reviews_digest.jsonl`, 335 candidate antibodies farmed in `.agents/antibodies/`, 4 anti-skill candidates in `.agents/antiskills/ooutwire/evidence_mined_candidates.json`, and verified execution over active preprints in `atlas/coda_atlas/F004_papers/`.
* **Implementation Status:** `RETIRED & MERGED INTO PYTHON ENGINE` 2026-10-08. Merged directly into `research_papers` (`use_cases/deposit_preflight.py`, `domain/rules/packaging_rules.py`, `latex_pdf_rules.py`) with full test coverage. Invoked via `py -3.12 -m research_papers preflight`. Text skill folders removed across all hosts.

#### Retirement Notice: `governance-research-paper-edit-publish`
* **Status:** `RETIRED & CONSOLIDATED` 2026-10-08.
* **Replacement:** Consolidated into `research_papers.use_cases.paper_edition` and unified CLI `py -3.12 -m research_papers edition <scaffold|align|rebuild|verify|republication-gate|publish>`. Prose skill directory removed across all hosts.

#### Retirement Notice: `rip-papers`
* **Status:** `RETIRED & DELETED` 2026-10-08.
* **Replacement:** Superseded by deterministic Python gate suites in `research_papers.use_cases.paper_review.cli`. Prompt-guessing agent markdown files and skill directories removed across all hosts.

### Entry 0307: `techne-adversarial-refusal-bypass-auditor`
* **Title:** Adversarial Refusal Bypass Auditor
* **Lead Council:** `L3_logos_techne`
* **Status:** `PENDING_REVIEW`
* **Confidence:** `HIGH`
* **Origin Role:** `challenger`
* **Scope:** Generates hostile permutations of refusal codes and keys (refusal, refusal_code, empty, bogus) across evaluator suites asserting strictly 0 false-pass admissions.
* **AuthorityEffect:** None

### Entry 0308: `techne-ast-anti-mock-and-facade-auditor`
* **Title:** AST Anti-Mock and Facade Auditor
* **Lead Council:** `L3_logos_techne`
* **Status:** `PENDING_REVIEW`
* **Confidence:** `HIGH`
* **Origin Role:** `victory_auditor`
* **Scope:** AST static analysis scanner inspecting test files for MagicMock/patch calls and dummy stub functions (pass, return True) that masquerade as trait implementations.
* **AuthorityEffect:** None

### Entry 0309: `techne-commit-reveal-manifest-resealer`
* **Title:** Commit-Reveal Manifest Resealer
* **Lead Council:** `L3_logos_techne`
* **Status:** `PENDING_REVIEW`
* **Confidence:** `HIGH`
* **Origin Role:** `explorer`
* **Scope:** Simulates commit-reveal cycles across test and judge manifests, recomputes Merkle digests from on-disk case files, and generates lossless synchronization diffs.
* **AuthorityEffect:** None

### Entry 0310: `techne-forensic-pedagogical-parity-auditor`
* **Title:** Forensic Pedagogical Parity Auditor
* **Lead Council:** `L3_nous_panepistimion`
* **Status:** `PENDING_REVIEW`
* **Confidence:** `HIGH`
* **Origin Role:** `auditor`
* **Scope:** Validates byte-level triple parity across lesson prose, runnable Jupyter notebooks, and video scripts, ensuring zero shape failures and zero empty learning checks.
* **AuthorityEffect:** None

