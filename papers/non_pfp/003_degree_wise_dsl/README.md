# Degree-Wise Obstruction Calculus and Symbolic DSL

**Subtitle:** Graded Cochain Complexes, Degree Separation, and Local-Global Gate Non-Factorization  
**Author:** Jeremy H. Carroll  
**Date:** 2026-09-30  
**Version:** 2.1.0  
**Canonical Identity:** `EA:F004.001.009` (`FOC-006`)  
**License:** Creative Commons Attribution 4.0 International (text; `LICENSE`) and Apache-2.0 (code; `LICENSE-CODE`)  

## Nonclaims & Epistemic Scope

This monograph assigns no authorization and changes no jurisdiction. It carries no operational authority or institutional standing. The calculus operates strictly on declared finite discrete carriers with exact rational arithmetic.

This package contains the complete self-contained research monograph, mechanized Lean 4 formalization, Python property test suite, and companion reproduction scripts for Degree-Wise Obstruction Calculus and Symbolic DSL.

## Cold Reproduction Instructions

This package is completely isolated and self-contained. It requires zero repository escapes or external ambient dependencies.

### 1. Python Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 2. Verify Deposit & Run Test Suite
```bash
# Verify checksums and run deposit verification
python verify_deposit.py

# Run specific test suites
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
