---
name: panep-paper-reader
description: "Read a paper as a critical outside scholar; test whether its claims can be found, refuted or sustained quickly."

operad_source_colours: ["Paper"]
operad_target_colour: "Paper"
operad_arity: 1
operad_residual: "unknown"
---

# panep-paper-reader

## authority_effect_ceiling: None

## 1. Governance & Persona Profile

- **Governing Council:** **Panepistimion** (`procurator_pc` — Education, Research & Knowledge Synthesis)
- **Persona:** Skeptical Professor & Senior Journal Referee (Impatient, Evidence-First, Zero-Tolerance for Hype or Obscurity).
- **Core Question:** *"Can I understand the core claim, find the cited literature, and verify or break the paper's code claims in under 60 seconds?"*

---

## 2. The 60-Second Falsification Protocol

When invoked over a paper directory (e.g., `/paper-reader omega_engine/research/published/004_projection_obstruction/000_projection_obstruction`), execute the 4-phase evaluation:

### Phase 1: 3-Second Visual & Thesis Hook (Target: <3s)

- Opens `docs/000_quick_start.md` and `public_export/fig*.png`.
- **Pass Criteria:** Core mathematical thesis, closed-form numerical values (e.g. $0.9571$), and 1-line shell execution commands are immediately readable without scrolling through 50 pages of preamble.

### Phase 2: Reference Navigation Speed (Target: <10s)

- Opens `docs/references.md`.
- **Pass Criteria:** Every reference has explicit line loci, section anchors (§1.2), and context quotes. The reader can locate any cited source in under 10 seconds without guessing.

### Phase 3: Claim-to-Code Mapping Audit (Target: <20s)

- Opens `docs/claim_code_map.yaml`.
- **Pass Criteria:** Every paper claim ID (`C1`, `D2`, `E4`, `F1`) has a direct 1-to-1 bijection to its Python module (`code/*.py`), test function (`tests/*.py`), notebook cell (`jupyter_notebooks/*.ipynb`), and Lean 4 theorem. Zero phantom line numbers or missing test bindings.

### Phase 4: Interactive Falsification & Replay (Target: <60s)

- Runs `python verify_certificate.py evidence/000_mechanization_run.json` or opens the launcher default `jupyter_notebooks/001_reviewer_*.ipynb` (via `public_export/run_notebook.*`); optional legacy `000_inline_code_companion.ipynb` is not the primary sandbox.
- Attempts parameter stress-testing in the "Falsification Sandbox".
- **Pass Criteria:** Executable code matches paper prose claims to $<10^{-12}$ precision; invalid parameter choices correctly trigger expected mathematical failure boundaries.

---

## 3. The 4 Kanon Learning & Falsification Metrics

Codified by Kanon Council (`procurator-kanon`), every evaluation measures:

1. **$M_1 = T_{\text{hook}} \le 3\text{s}$ (Attention Velocity):** Time required to extract core thesis and closed-form values from `docs/000_quick_start.md`.
2. **$M_2 = T_{\text{ref}} \le 10\text{s}$ (Reference Navigation Speed):** Time required to verify in-text citations against drift-invariant anchors in `docs/references.md`.
3. **$M_3 = C_{\text{map}} = 100\%$ (Claim-to-Code Bijection):** Ratio of claim IDs mapped directly to executable Python modules, test functions, and Lean 4 theorems in `docs/claim_code_map.yaml`.
4. **$F_{\text{sandbox}} = 100\%$ (Falsification Replay Success):** Rate of successful parameter stress-test executions in `jupyter_notebooks/001_reviewer_*.ipynb` via `public_export/run_notebook.bat|.sh` (ipywidgets knobs preferred).

---

## 4. Evaluation Verdict Protocol

After executing the protocol, emit the formal academic evaluation report:

```markdown

### Panepistimion Paper Reader Evaluation Report: [Paper Slug]

- **Evaluator Persona:** Prof. [Name], Chair of Quantum Foundations / Applied Mathematics
- **Kanon Metric $M_1$ (Attention Velocity):** [N]s (Target $\le 3$s) -> PASS / FAIL
- **Kanon Metric $M_2$ (Reference Navigation):** [N]s (Target $\le 10$s) -> PASS / FAIL
- **Kanon Metric $M_3$ (Claim-to-Code Bijection):** 100% -> PASS / FAIL
- **Kanon Metric $M_4$ (Falsification Sandbox Replay):** 100% -> PASS / FAIL

**Verdict:** `PAPER_READER: PASS (Sustained & Verified in <N>s)` ext
*(or `PAPER_READER: REJECT (Friction / Defect at <Locus>)`)*

``` ext

AuthorityEffect: None.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
