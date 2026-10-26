---
name: techne-paper-deposit-preflight-gate
description: "Preflight verification gate for paper deposits, build scripts, rendering parity, path limits, and witness certificates."
status: canonical
operad_source_colours: ["Paper", "Contract"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [governance, gate, packaging, techne]
---

# techne-paper-deposit-preflight-gate

**AuthorityEffect:** None. This gate refuses. It does not mint, promote, or alter doctrine.

## The Single Rule

> Every research paper package submitted for republication or review must pass preflight deposit envelope checks verifying standalone release verifiers, LaTeX/PDF rendering parity, discrete dual-witness certificates, and strict filesystem depth boundaries before entering review swarms.

## Invariants

1. **Standalone Release Verifier (`UNVERIFIED_RELEASE_SCRIPT`)**:
   - The paper repository must contain an executable, self-contained rebuild and verification script (`tools/rebuild_release.py` or `verify_deposit.py`) matching SHA-256 payload manifests.
   - Releases lacking a hermetic verification script cannot be certified.

2. **TeX/PDF Rendering Parity (`TEX_PDF_HASH_DESYNCHRONIZATION`)**:
   - LaTeX source edits must not be committed without compiling and verifying matching PDF artifacts, page geometry, title rendering, and table-of-contents alignment.
   - Any desynchronization between TeX and rendered PDF triggers immediate preflight refusal.

3. **Discrete Dual-Witness Certification (`EXACTNESS_WITHOUT_DUAL_WITNESS_CERTIFICATE`)**:
   - Mathematical papers asserting coboundary vanishing, exactness, or zero curvature must provide both primal and dual cochain certificates ($\Phi_1 = 0$, $\Gamma_2 = 0$) backed by deterministic solver receipts.

4. **Deposit Envelope Purity & MAX_PATH Boundaries (`DEPOSIT_MAXPATH_OVERFLOW_AND_DIR_POLLUTION`)**:
   - File paths must strictly remain $< 250$ characters to guarantee portability across Windows workstations.
   - Packages must not contain transient scratch directories (`evidence/`, `tmp/`, `__pycache__`) or unindexed build outputs.

## Verification

```bash
# Lightweight self-check
py -3.12 omega_engine_operads/skills/techne-paper-deposit-preflight-gate/scripts/check_paper_deposit_preflight.py

# Evaluate an active preprint package
py -3.12 omega_engine_operads/skills/techne-paper-deposit-preflight-gate/scripts/check_paper_deposit_preflight.py --paper-path omega_engine_atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_witnessed_difference_programme

# Or invoke the unified paper review CLI preflight subcommand
py -3.12 -m omega_engine_research_papers.use_cases.paper_review.cli preflight --paper-path <paper_path>
```
