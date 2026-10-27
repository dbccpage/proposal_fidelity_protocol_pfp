# Path-Additive Coboundary Defects for Reasoning Trace Validation

**Monograph 033** | Finite Obstruction Calculus Program  
**DOI:** 10.5281/zenodo.20214112 | **Version:** 2.0.0

## Abstract
This paper specifies a realization boundary, a typed refusal taxonomy, and a certificate format for reasoning-trace diagnosis. Until PL-014-2 is discharged, an `Exact` verdict is a statement about $\pi$'s image and nothing more. An `Exact` verdict diagnoses the declared extractor. Certificate Soundness and Witness Soundness stay `[OPEN]`. The Python gap check is not a proof of certificate soundness.

## Quick Start
```bash
py -3.12 -m pytest code/tests/
py -3.12 verify_deposit.py --test code/tests/test_reasoning_trace_validation.py
```
