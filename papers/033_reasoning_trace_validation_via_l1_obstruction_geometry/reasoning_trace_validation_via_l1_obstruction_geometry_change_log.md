# Change Log: Path-Additive Coboundary Defects for Reasoning Trace Validation (Paper 033)

All notable changes to this research package are documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

---

## [2.0.1] - 2026-10-07

### Changed
- `TraceValidator.validate_trace` decides exact repairability by an exact rational coboundary solve; the floating-point LP is now a proposal only, certified by an exact upper bound from an exact potential and an exact lower bound from an exactly feasible dual circulation, with the exact gap reported in `diagnostics` (`certified`, `phi_1_lower_bound`, `duality_gap`). The `step_budget` argument now bounds the carrier size and emits `BudgetExceeded`; inexact cochain values, duplicate edges and undeclared edges are refused as `CarrierFailure`.
- The nested directory `032_witnessed_difference_finite_distinction_carriers_and_history_escape/` was moved out of this package to its own sibling directory; it is no longer bundled into this deposit.
- `verify_deposit.py` no longer requires a `*_claim_ledger.md` (aligned with the paper template); `scripts/regen_sha256sums.py` is the template version and shares the deposit walker and exclusion sets with `verify_deposit.py` and `tools/rebuild_release.py`; `tools/rebuild_release.py` registers `deposit_paths` in `sys.modules` before executing it.
- Import blocks sorted and unused imports removed (ruff F401/F841/I).

## [2.0.0] - 2026-10-07

### Added
- Standardized academic research package layout conforming to local local-first verification standards.
- Sovereign reference implementation `code/mod_reasoning_trace_validation_core.py` modeling carrier graph extraction, coboundary operator d_0, primal-dual l^1 repair optimization in exact rational arithmetic, dual witness circulation generation, and path-additive commutativity defect bounds.
- Unit test suite `code/tests/test_reasoning_trace_validation.py` validating exact repair on trees, cycle inconsistency detection, dual circulation certificate verification, and path commutativity bounds.
- Comprehensive 8-section Unicode documentation standard `docs/descriptions.md`.
- Formatted bibliography in `docs/references.md`.
- Automated manifest generator `scripts/regen_sha256sums.py`, release builder `tools/rebuild_release.py`, and fail-closed deposit verifier `verify_deposit.py`.

### Changed
- Promoted manuscript to publication-grade monograph `reasoning_trace_validation_via_l1_obstruction_geometry_monograph.md`.
- Harmonized title with Zenodo record 20214112 (*Path-Additive Coboundary Defects for Reasoning Trace Validation*).
- Purged internal omnibus references, mechanism inventories, and house acronyms.
- Enforced strict claim hygiene (`RULE[user_global]`).

## [1.0.1] - 2026-07-17

### Added
- Initial pre-print specification of trace realization boundaries and typed refusal taxonomy.
