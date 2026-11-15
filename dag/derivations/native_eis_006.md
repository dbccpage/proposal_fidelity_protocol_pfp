# NATIVE-EIS-006: Two-Signal Independence and Disposition Boundary

AuthorityEffect: None.

- Archive claim: [ATL-P003-008](atl_p003_008.md) (partially covered, `narrows`)
- Audit derivation node: `NATIVE-EIS-006` (`ATL-D-NATIVE-EIS-006`)
- Review verdict: `partial` (`narrows` `ATL-P003-008` in [`atlas/atlas_claim_matches.json`](../../atlas/atlas_claim_matches.json))

## 1. Statement under review

Native two-signal screening separates Signal 2 danger observation from Signal 1 detector hits before computing a five-way `DangerDecision`:

1. `(false, None)` -> `Tolerated`
2. `(true, None)` -> `DiagnosticOnly`
3. `(false, Some(_))` -> `DiagnosticOnly`
4. `(true, Some(Low | Medium))` -> `DefensiveLockdown`
5. `(true, Some(High | Critical))` -> `Quarantined`

In addition, `evaluate_independent` enforces structural independence before calling `evaluate_signals`.

## 2. Verified codebase evidence

- `code/rust/core_epistemic_immune_system/src/independence.rs:254-315`: `validate_observer_identity` and `assert_signals_independent` refuse empty `detector_id`, empty `observer_id` (`UNWITNESSED_DANGER_SIGNAL`), model/detector/matching observer names (`TWO_SIGNAL_COLLAPSE`), unregistered danger kinds (`UNREGISTERED_DANGER_KIND`), duplicate predicate names, digest equality with Signal 1 matches, and overlapping content spans.
- `code/rust/core_epistemic_immune_system/src/signal_gate.rs:73-114`: `TwoSignalDangerGate::evaluate_signals` implements the five-branch disposition table; `evaluate_independent` invokes `assert_signals_independent` first.
- `code/rust/core_epistemic_immune_system/src/activation_use_case.rs:41-69`: `activate_learned_guard` checks `DetectorHitRefV1` `spec_id`, reads admission/suspension state via `GuardStatePort`, runs `DangerSensorPort::detect_danger` on subject `content`, and calls `evaluate_activation`.
- Companion host integration (Draft PRs `#113` and `#121`, branches `gemini/eis-pciv-m5` and `gemini/eis-pciv-m7`): `code/rust/pfp_immune decide` exposes native typed two-signal disposition via CLI JSON.

## 3. Why it narrows `ATL-P003-008`

Paper 003 (`ATL-P003-008`) states that `pfp/domain/immune/danger_gate.py` maps `(S1 only)->diagnostic`, `(S2 low/medium only)->diagnostic`, `(S2 high/critical only)->refuse`, and `(S1 and S2)->refuse`. In native Rust (`signal_gate.rs:85-93`), `(false, Some(_))` returns `DiagnosticOnly` for all severities (leaving any direct refusal to the host check that observed Signal 2), and `(true, Some(_))` splits by severity between `DefensiveLockdown` and `Quarantined`. `NATIVE-EIS-006` therefore narrows rather than replicates the archived Python table row-for-row.

## 4. Bounds and open obligations

- Structural observer/digest/span checks do not establish statistical or causal independence of real observers.
- `evaluate_signals` alone trusts already-projected `MatchEvidence` and `CategorizedDangerEvidence`; callers must use `evaluate_independent` to run `assert_signals_independent`.
- Exhaustive Python-package table comparison and severity-dependence review remain open on `ATL-P003-008`.
