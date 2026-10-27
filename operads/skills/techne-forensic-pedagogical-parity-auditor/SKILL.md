---
name: techne-forensic-pedagogical-parity-auditor
description: "Check lesson prose, Jupyter notebooks and video scripts stay in parity, with no empty learning checks."
operad_source_colours:
  - Paper
  - Code
operad_target_colour: Receipt
operad_arity: 2
operad_residual: diagnostic
families:
  - techne
  - pedagogy
  - education
  - audit
---

# Techne Forensic Pedagogical Parity Auditor

**AuthorityEffect:** None.  
**Council:** `L3_nous_panepistimion`  
**Status:** Active.

## Mission & Governance Invariants

The **Forensic Pedagogical Parity Auditor** audits educational curriculum tracks across `education/` to ensure that every lesson is completely and harmoniously instantiated across its three media formats: theoretical prose, executable code notebook, and companion presentation script.

In accordance with repository pedagogical engineering standards (`governance-pedagogy`):

1. **Triple-Artifact Parity:** Every numbered-track lesson `NNN_<slug>` must maintain matched components across `concepts/<slug>.md`, `notebooks/<slug>.ipynb`, and `videos/<slug>.md` (or `scripts/<slug>.py`). A missing or misnamed component constitutes a structural shape defect.
2. **Mandatory Executable Learning Checks:** Notebooks must contain executable `assert` statements. Headless notebook execution (`nbclient`) must execute every cell without error and verify that asserts pass. An empty notebook or a notebook without assertions is flagged as an open check.
3. **Prose Decoupling Ceilings:** Word overlap between the prose concept document and the notebook markdown cells must not exceed 35%. Notebooks must focus on code, execution, and empirical calculation rather than duplicating theoretical exposition.
4. **Markdown Cell Budget Ceiling:** Markdown cells within notebooks must remain strictly $\le 25$ lines each to prevent prose bloat and maintain focus on interactive computation.

---

## Pedagogical Parity Audit Rules

| Rule ID | Surface | Failure Condition | Required Action |
|---|---|---|---|
| `FPP-SHP-001` | Track Directory | Missing one of `concepts/`, `notebooks/`, `scripts/`, `videos/` | Create missing directory or relocate misplaced files. |
| `FPP-CHK-001` | Jupyter Notebook | Notebook contains zero executable `assert` statements | Add deterministic assertions checking cell outputs. |
| `FPP-DCP-001` | Prose Overlap | Markdown overlap between prose and notebook > 35% | Trim conceptual prose from notebook; link to concept doc. |
| `FPP-BGT-001` | Cell Length | Notebook markdown cell > 25 lines | Split or condense markdown cell; move theory to concepts. |
| `FPP-LNK-001` | Cross-Reference | Concept markdown fails to link to companion notebook | Add direct relative link to companion notebook. |

---

## Operational Workflow

### 1. Executing the Parity Audit

Run the pedagogical check suite:

```console
# Run lesson folder shape check
py -3.12 operads/skills/governance-pedagogy/scripts/check_lesson_folders.py

# Enforce strict assertion checks across all notebooks
py -3.12 operads/skills/governance-pedagogy/scripts/check_lesson_folders.py --strict-checks
```

### 2. Remediating Mismatched Slugs

When a track has mismatched filenames:
1. Identify canonical lesson slug from `concepts/<slug>.md`.
2. Rename companion notebook to `notebooks/<slug>.ipynb` and video script to `videos/<slug>.md`.
3. Verify that the concept document contains a relative link to `../notebooks/<slug>.ipynb`.
4. Re-run `check_lesson_folders.py` to confirm zero open shape issues.

### 3. Claim Hygiene & Learner Evidence

- State that the lesson structure conforms to the triple-artifact standard.
- Do NOT claim that passing code cells or executed notebooks demonstrate that a human learner has achieved understanding or that general mathematical conjectures are established.
