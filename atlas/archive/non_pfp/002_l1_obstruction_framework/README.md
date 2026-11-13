# Finite ℓ¹ Coboundary Obstructions: Primal–Dual Certificates, Operator-Valued Extensions, and Spectral Comparisons

**Author:** Jeremy H. Carroll  
**Date:** 2026-10-15  
**Version:** 5.5.3  
**DOI:** 10.5281/zenodo.23406596  
**Zenodo Record:** <https://zenodo.org/records/23406596>  
**Status:** research monograph  
**License:** Creative Commons Attribution 4.0 International (text and documentation) and PolyForm Noncommercial 1.0.0 (code, Lean proofs, deposit tooling)  

## Epistemic Scope & Nonclaims

- **Prose mathematics vs. formalization:** The general real $L^p$ and Schatten-$p$ discussion is classical convex analysis and operator theory in prose; it is not a completed general Lean formalization. Lean 4 modules provide integer three-cycle cochain fixtures, power norms, and weak duality under explicit hypotheses. Valid written proofs (Theorem 2.1, Theorem 4.2, Theorem 5.1, Proposition E.7e) are maintained as classical mathematical theorems in text, distinguished from mechanized rows.
- **Exact vs. numerical solvers:** Python $p=1, 2, \infty$ solvers use exact rational arithmetic (`fractions.Fraction`). Interior-$p$ iterations and matrix singular value evaluations use float64; `numerical_checks_passed` reports tolerance checks, and `is_certified` is set to `False` for interior-$p$ iterations, reserving exact certification for the rational solvers.
- **Withdrawn candidate iterator:** The formerly proposed three-step primal--dual candidate update (historical Definition 4.1) is withdrawn and refuted by a single-edge counterexample with non-optimal fixed points and step-size-dependent exits from the dual unit ball. It provides neither a descent theorem nor a convergence guarantee under the declared assumptions. Shipped code and retained theory verify independently supplied finite KKT certificates via linear programming duality.
- **Provenance:** Withdrawn pre-review drafts and historical claims are archived in [`docs/withdrawn_pre_review.md`](docs/withdrawn_pre_review.md).

---

## Cold Reproduction Instructions

This package is self-contained and operates within its local directory tree.

### 1. Python Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 2. Verify Deposit Integrity & Run Tests

```bash
# Verify checksums, the shipped test file, and the Lean build
python verify_deposit.py --test code/tests/test_004_l1_obstruction_framework.py --lean

# Or run pytest directly
pytest code/tests/ -v
```

### 3. Lean 4 Formalization Verification

Requires [Lean 4](https://leanprover.github.io/) (`elan` and `lake`):

```bash
cd lean4
lake build
cd ..
python verify_deposit.py --lean
```

### 4. Checksum & Release Validation

```bash
python tools/rebuild_release.py --check
```

---

## Package Structure

- `l1_obstruction_framework.md`: Canonical research monograph.
- `l1_obstruction_framework.tex`: Typeset LaTeX source generated from canonical Markdown.
- `l1_obstruction_framework.pdf`: Compiled monograph PDF.
- `code/`: Standalone Python reference implementation (`mod_004_l1_obstruction_framework_core.py`).
- `code/tests/`: Automated pytest verification suite for exact solvers, duality checks, and operator presheaves.
- `lean4/`: Lean 4 formalization modules.
- `docs/`: Supplementary documentation, descriptions, references, and historical archives.
- `tools/`: Deterministic release and manifest validation utilities.

## Toolchain Pinning

- **Python:** 3.12 (`fractions.Fraction`, `numpy>=1.24.0`, `pytest>=7.0.0`)
- **Lean 4:** `leanprover/lean4:v4.33.1` (lake toolchain)
- **Typesetting:** XeLaTeX with standard AMS and math fonts via Pandoc
