# NATIVE-EIS-001: Native Thymus Screening Boundary

AuthorityEffect: None.

- Archive claim: [ATL-P006-009](atl_p006_009.md) (partially covered, `narrows`)
- Audit derivation node: `NATIVE-EIS-001` (`ATL-D-NATIVE-EIS-001`)
- Review verdict: `partial` (`narrows` `ATL-P006-009` in [`atlas/atlas_claim_matches.json`](../../atlas/atlas_claim_matches.json))

## 1. Statement under review

`ThymusGate::screen` in `code/rust/core_epistemic_immune_system/src/thymus.rs:66-97` enforces negative selection on a proposed `AntiSkillSpecV2` over a caller-supplied finite `self_panel`:

1. Non-`Proposed` specifications are refused with `ThymusVerdict::InvalidPattern { error: "SPEC_NOT_PROPOSED" }`.
2. Invalid regular expressions return `ThymusVerdict::InvalidPattern { error: e.to_string() }` via `Regex::new(&spec.pattern)`.
3. Any match against an element of `self.self_panel` calls `spec.retire()` and returns `ThymusVerdict::SelfReactive { matched_sample, sample_index }`.
4. Passing all elements promotes the spec only to `Candidate` (`spec.promote_to_candidate()`) and returns `ThymusVerdict::Survived { samples_tested, self_panel_hash }`.

## 2. Verified codebase evidence

- `code/rust/core_epistemic_immune_system/src/thymus.rs:34-62`: `ThymusGate::new` hashes `self_samples` with newline separators into `self_panel_hash`, and `ThymusGate::standard_baseline` constructs a fixed 10-sample panel.
- `code/rust/core_epistemic_immune_system/src/thymus.rs:66-97`: `ThymusGate::screen` implements the `InvalidPattern`, `SelfReactive` (`spec.retire()`), and `Survived` (`spec.promote_to_candidate()`) transitions.
- Companion host integration (Draft PR `#113`, branch `gemini/eis-pciv-m5`): `code/rust/pfp_immune screen` exposes `ThymusGate::screen` as a typed CLI check.

## 3. Why it narrows `ATL-P006-009`

`ATL-P006-009` in Paper 006 states that an invalid detector regex yields a typed refusal and a benign-panel match yields a kill-condition record in the Python `clonal_selection` flow. `NATIVE-EIS-001` shows the corresponding native Rust separation in `ThymusGate::screen`: typed `InvalidPattern` refusal for unproposed specs or invalid regexes, and `SelfReactive` retirement on a benign self-panel hit, while keeping `Candidate` status non-admitting.

## 4. Bounds and open obligations

- Empty panels (`self_panel.is_empty()`) pass vacuously with `samples_tested: 0`.
- Passing a finite self panel does not establish a population false-positive rate or semantic completeness.
- `ThymusGate::new` joins samples with `b"\n"` (`thymus.rs:37-40`), so element boundaries containing `\n` share hashes across distinct splits.
- Direct replay of the finite Paper 006 Python `clonal_selection` kill-condition check remains open on `ATL-P006-009`.
