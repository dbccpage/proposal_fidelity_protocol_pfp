# ℓ¹-Native Cohomology of Finite Defect Fields

**Subtitle:** Quotient Norms, Dual Circulations, Sparse Representatives, and the L^p Geometric Family
**Author:** Jeremy H. Carroll
**Date:** 2026-10-15
**Version:** 6.5.2  
**DOI:** 10.5281/zenodo.23406558  
**Zenodo Record:** <https://zenodo.org/records/23406558>  
**License:** Creative Commons Attribution 4.0 International (text) and PolyForm Noncommercial 1.0.0 (code and Lean proofs)

## Epistemic Scope & Nonclaims

The general real $L^p$ and Schatten discussion is classical finite-dimensional convex analysis and operator theory with proofs supplied in the manuscript. Lean 4 formalizations mechanize the finite matrix certificate theorem (L1C-TG) and model lemmas over finite integer complexes. The calculus operates strictly on declared finite discrete cell complexes with exact arithmetic.

This package contains the complete self-contained research monograph, scoped finite integer Lean 4 formalization, Python property test suite, and companion reproduction scripts for ℓ¹-Native Cohomology of Finite Defect Fields.

## Cold Reproduction Instructions

This package is completely isolated and self-contained. It uses no repository-relative imports outside this directory. Install the declared Python dependencies and the pinned Lean toolchain before replay.

### 1. Python Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 2. Verify Deposit & Run Test Suite
```bash
# Verify checksums, execute test suite (91 functions, 110 cases), and verify Lean proofs
python verify_deposit.py --run-tests --lean

# Or run specific test suites directly
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

### 4. Headless Figure & Artifact Generation
```bash
python code/generate_figures.py
```
Output figures are saved in `public_export/`.

### 5. Checksum & Release Validation
```bash
python tools/rebuild_release.py --check
```

## Toolchain Pinning
- **Python:** 3.12 (standard library `fractions.Fraction`, `numpy>=1.24.0`, `pytest>=7.0.0`)
- **Lean 4:** `leanprover/lean4:v4.33.1` (lake toolchain)
- **Typesetting:** XeLaTeX with standard AMS and math fonts

Exact rational feasibility, stationarity, and PSD decisions are separated from numerical output: coherence is exact when its complex moduli are rational and binary64 otherwise; continuous-$p$ and Schatten singular-value calculations are binary64 diagnostics. The historical `HighPrecisionLpConvexSolver` class name is retained for compatibility.

The software distribution metadata declares PolyForm Noncommercial 1.0.0, matching `LICENSE-CODE`; manuscript, figures, and documentation remain CC BY 4.0.
