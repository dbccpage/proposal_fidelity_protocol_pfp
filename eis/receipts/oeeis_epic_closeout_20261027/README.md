# OEEIS epic closeout

> Moved here on 2026-11-06 from the immune research repo. Paths and package names follow this repository's rename map; the recorded commands ran in the source repository and are kept as history.

AuthorityEffect: None. Bounded implementation checkpoint on top of
`origin/main` at `82eab88b4b7ec3cd88367796971b3cda174ef0d5`. One Claude worker
implemented and checked this; no independent reviewer or paid provider call is
claimed. It supplements the
[2026-10-12 boundary checkpoint](../epic_boundary_repair_20261012/README.md) and
the [authenticated custody checkpoint](../authenticated_custody_20261012/README.md)
without rewriting them.

## What was open

Reading the four plans against the code at the base commit left these code
slices without execution evidence. Everything else in the plans was either
delivered by the two earlier checkpoints or is an operator, deployment or
research obligation (now in
[oeeis_residual_obligations.md](../../documentation/oeeis_residual_obligations.md)).

| Epic | Open slice | Result |
| --- | --- | --- |
| EIS-001 | 2: persona host check keeps separate provenance; duplicate or mislabeled provenance refused | Implemented. Duplicate native findings were accepted (RED); finding sources were unchecked (RED). Now refused. |
| EIS-001 | 4: a clean report injected into an admission request must not admit | Implemented. Native `parse_request` silently dropped an attached `pharmacy_report` field (RED). It now refuses undeclared request fields with `BAD_PAYLOAD`. Status never left CANDIDATE before or after. |
| EIS-001 | Plan mutations (disable a shared class; unavailable host to empty findings) | Executed; both detected. |
| EIS-002 | 4: subject transplant after a successful activation, then recovery | Characterization control: it passed on the base code (no new RED claimed). The old-hit case is pinned to `SUBJECT_MISMATCH`, so it bites independently of the health check. |
| EIS-003 | Residual 4: learning and regulator composition on a finite fixture bank | Implemented in Rust. Native `DetectorRule` carried any extra field, so `mutate`/`stimulate` propagated a smuggled `"status": "ADMITTED"` to a learned child (RED). It now refuses fields outside the nine declared rule fields. |
| EIS-003 | Prospective mutations (minimum samples; denominator; suspension removal) | Executed; all detected. |
| 004 | Finite slices | Already executed at the custody checkpoint; broad claims stay RESEARCH_HOLD. |

## Changed files

- `crates_rs/core_epistemic_immune_system/src/admission.rs`: closed request field set.
- `crates_rs/core_epistemic_immune_system/src/clonal_selection.rs`: `RULE_FIELDS`, closed rule field set.
- `eis/infrastructure/native_pharmacy.py`: `FINDING_SOURCES`, duplicate-finding refusal.
- `eis/infrastructure/mssn_ports.py`: `PharmacyMatcher` refuses non-native provenance from the native port.
- New tests: `tests/unit/test_pharmacy_role_partition.py`, `tests/unit/test_activation_receipt_transplant.py`, `crates_rs/tests/core_epistemic_immune_system/learning_regulation_composition.rs`.
- `crates_rs/tests/core_epistemic_immune_system/activation_use_case_parity.rs`: two-line lifetime/borrow fix. On rustc 1.97 the target did not compile at the base commit, which blocked the whole crate's test run.

## Recorded verification

Python 3.12.3, pytest 9.1.1, rustc/cargo 1.97.0, Linux. Host binary rebuilt
from this tree and passed as `CORE_SYMBOL_GAME_HOST`.

| Check | Result |
| --- | --- |
| `cargo test -p core_epistemic_immune_system -j 3` | 70 passed, 0 failed |
| `pytest eis/tests` | 506 passed, 3 skipped, 1 failed. The failure, `test_pilot_candidate_publication.py::test_selected_definitions_have_actual_controls_and_exact_historical_sources`, runs `git show 6430d647...`, an object absent from this shallow clone. It does not touch changed code. |
| `python -m ppo.use_cases.epic_manifest_audit` | `EPIC_MANIFEST_OK epics=16` |
| `pytest ppo/tests/test_epic_suite_upgrades.py test_epic_manifest_audit.py test_product_planning_manifest.py` | all passed |
| Ten source mutations, one at a time ([mutations.json](mutations.json)) | 10 of 10 detected by the named controls, 10 of 10 recovered after exact restoration (source SHA-256 rechecked) |

Not run: the full repository suite, Windows/`py -3.12`, hosted CI. In the wider
`ppo` and `pfp` suites, `test_epic_tdd_plan_audit`,
`test_review_remediation_ledger_audit` and `test_grade_a_lean_inventory` fail
identically on the base commit; `test_symbol_game_release_gate::test_host_parity_is_verified_inside_the_harness`
fails on `.agents` skill-root parity for Techne and Adversary skills, which this
change does not touch (not rechecked on the base commit).

## Plan retirement

The four plans and the `oeeis/` register were deleted; `EXPECTED_EPIC_COUNT`
went from 20 to 16 and the byte manifest was regenerated. Links in the
planning READMEs, two OEGOV plans and the Adversary app-integration prompt now
point at the residual-obligations file or the authenticated-custody contract.
Historical receipts that name the old paths are unchanged.
