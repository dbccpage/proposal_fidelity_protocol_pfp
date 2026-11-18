---
name: panep-pedagogy-improvement
description: "Evaluate lessons and preprints against a pedagogy rubric and submit teaching recommendations."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# panep-pedagogy-improvement

## authority_effect_ceiling: None

## 1. Integration with `/rip-papers` Workflow

At Stage 4.4 of `/rip-papers` (after `/panep-paper-reader`), this skill is automatically invoked to:

1. **Audit the 3-Tier Pedagogical Ladder** for the released paper:
   - **Tier 1 (The Hook - 3 Seconds):** `docs/000_quick_start.md` & high-resolution figures (`public_export/fig*.png`).
   - **Tier 2 (The Sandbox - 60 Seconds):** `public_export/run_notebook.bat|.sh` zero-install launcher opening **`jupyter_notebooks/001_reviewer_*.ipynb`** (ipywidgets continuous knobs + Interactive Falsification Sandbox). Legacy `000_inline_code_companion.ipynb` is optional scaffolding only.
   - **Tier 3 (The Monograph - Deep Study):** Monograph paper (`.md`), 7-class typed claim ledger, and Lean 4 formalizations.
2. **Generate Teaching & Learning Recommendations**: Submit a formal report to the **Didaskalia Council** (`L3_nous_didaskalia`) and **Panepistimion Council** (`L3_nous_panepistimion`) outlining new pedagogical techniques, interactive visualization ideas, and curriculum bridges derived from the paper's mathematical discoveries.

---

## 2. 5-Dimension Evaluation Rubric

| Dimension | Weight | Focus |
| ----------- | -------- | ------- |
| **Clarity** | 30% | Can target audience understand without external lookups? |
| **Accuracy** | 25% | Are claims factually correct, physics-safe, and claim-typed? |
| **Prerequisites** | 20% | Are all terms introduced before use? |
| **Engagement** | 15% | Does content have 3-tier anchors + actionable exercises? |
| **Atomicity** | 10% | Is section <= 15 min and micro-segment ready? |

### Thresholds

- **Pass**: Overall >= 3.0 AND no dimension < 2.0
- **Excellence**: Overall >= 4.0 AND all dimensions >= 3.0
- **Reject**: Overall < 2.5 OR any dimension = 1

---

## 3. Definition of Done (Hard Gates)

1. **Learning objectives** are stated (3 max) and measurable.
2. **Objective → practice alignment** exists (each objective is assessed by at least one exercise/check).
3. **Interactive Falsification Sandbox** is present in companion notebooks (Tier 2).
4. **Exercises include feedback** (expected answer or rubric + at least one common wrong answer).
5. **No PREREQUISITE_VIOLATION** (or explicitly marked as preview).
6. **Micro-check cadence**: inline check every 2–5 minutes.
7. **Claim hygiene**: non-trivial claims are tagged (`Definition`, `Empirical`, `Derivation`, `Interpretation-dependent`, `Metaphor`, `Speculative`).
8. **Stable alignment references**: alignment maps refer to section headings/anchors, not line numbers.
9. **For math/physics**: worked example → faded example → independent attempt sequence.

---

## 4. Council Reporting & Recommendations Format

At the end of a paper review or lesson audit, emit:

```markdown

# Panepistimion Pedagogy Review & Council Briefing

**Paper / Target Path**: {path}
**Council Target**: L3_nous_didaskalia / L3_nous_panepistimion
**Status**: PASS | NEEDS WORK

## 1. 3-Tier Pedagogical Ladder Evaluation
- **Tier 1 (Hook)**: `docs/000_quick_start.md` present & score: {1-5}
- **Tier 2 (Sandbox)**: `run_notebook.bat` + Falsification Sandbox score: {1-5}
- **Tier 3 (Monograph)**: `.md` monograph + Lean 4 formalization score: {1-5}

## 2. Didaskalia Council Innovations & Recommendations
1. **Curriculum Bridge**: How this paper's core theorem maps into the physics/math curriculum.
2. **Interactive Visualization**: Proposed DIME interactive figure / notebook widgets for student engagement.
3. **Falsification Probe**: Exact parameter perturbation that breaks the theorem for student learning.

``` ext

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
