# EIS and Woland implementation checkpoint

AuthorityEffect: None.

This checkpoint repairs three bounded behaviors from the OEEIS/OEWOLAND epics.
It does not complete the full epic suites. One Codex worker performed the edits,
source review and local checks; no independent worker or paid provider ran.

| Epic | Delivered or verified scope | Remaining obligation |
| --- | --- | --- |
| EIS-001 | Twelve native detector mappings, literal finite loci, separate Python persona provenance, complete detector inventory and raw-input binding before caching. | Structural matches do not establish semantic completeness or admission. |
| EIS-002 | Existing executed tolerance and four-conjunct activation controls pass against the rebuilt host. | Configure an authenticated health observer, subject/scope binding, expiry and trust root before adding the required health adapter. |
| EIS-003 | Exact FP/(TP+FP), strict default 1/10, widened totals and arbitrary-size cross products, custom threshold validation, detector identity/state fences. Python toxicity remains separate. | Authenticated decisions, revocation/replay custody and externally authorized reinstatement require operator trust configuration. Legacy Formulary remains a metadata API. |
| OEEIS-004 | Reviewed the existing eligibility/observation seam; it retains CANDIDATE status. | Authenticate and bind ledger observations to candidate/source/fixture identities before running the full negative-selection experiment. Distinct IDs alone do not authenticate observations. |
| OEWOLAND-002 | Existing shared coordinator and local callback/CLI seams retained; finite review/repair controls pass. | No paid OpenRouter demonstration or generalized remote-tool execution is claimed. The existing bounded transport refusal remains. |
| OEWOLAND-003 | Learning can apply bound outputs; changes require a fresh original-task check and digestion. A seeded learning regression returns to repair, then a benign learned descendant terminates. | General autonomous closure, broad semantic deduplication and remote resumption remain outside this finite correction. |
| OEWOLAND prior-art/consolidated | Existing native source-custody controls run after correcting stale include paths. | Source-theorem correspondence, trusted external observations, concurrency and checkpoint/resume retain their existing owners/holds. |

The native host initially failed to build because five includes still used
`.agents/anti_skills`. They now reference the existing `.agents/antiskills`
specifications and fixture bank. Specification bytes were not edited.

The historical inventory reader also now accepts absolute recorded roots from
Windows and POSIX independently of the current OS. Its existing migration
execution check still requires the exact local root. Frozen inventory and source
bytes remain unchanged.

## Verification

[validation.json](validation.json) contains reproduction command arguments, tool versions,
exit statuses, output bytes as UTF-8 text with hashes, source hashes and the original
failures. [software_qa_receipt.json](software_qa_receipt.json) uses the existing
SoftwareQaReceiptV1 type for the three scoped mutation controls. The broader QA verdict remains BLOCKED by outstanding dependencies and failed
global checks; the three mutation controls passed. The receipt binds
the recorded dirty source tree at the stated base commit; it does not claim that
the base commit alone contains these changes. Test-portion durations include
command startup and, for Cargo, compilation.

- Native regulation/state checks: 9 passed; native anti-skill custody: 12 passed.
- Native EIS Python integration: 94 passed, zero skips.
- Adapter/definition controls: 23 passed; distinct Python policy controls: 5 passed.
- Shared Woland digestion/continuation/coordinator: 44 passed.
- Portable-history and historical-source controls: 27 passed; the exhaustive
  Unicode 15.1 oracle explicitly skipped on the installed Unicode 15.0 runtime.
- Three production mutants were detected: inclusive native threshold, omitted raw
  payload binding, and completion without the post-learning recheck. Exact original
  bytes were restored and each targeted control passed again.

The pharmacy boundary tests inject malformed host replies deliberately. They are
boundary fault controls; the separate 94-test run uses the actual rebuilt host.
The learning test uses real temporary files and the operator-bound Python acceptance
command. Its second-generation defect is intentionally seeded, not a model result.

The wider IC recovery run recorded 42 passes, that same Unicode skip and one
environment failure: its Windows junction test invokes unavailable `cmd` on Linux.
The global prior-art audit passes the repaired inventory parser but still refuses
the absent `omega_engine_projects/fsp/meron_sign_problem/paper.pdf`. Neither result
is reported as a pass. The new epic-walk successor preserves historical receipts, records the three
behavior-plan updates, repairs Woland navigation and reconciles five pre-existing
merged-main digest drifts. All eight scoped plans pass hash/structure/link checks.
The global TDD audit still refuses a missing OEPFP education-directory link; its
focused test file records 14 passes and one repository-fixture failure.

## Reproduction

Use the canonical workspace manifest, a shared Cargo target directory and one
package at a time. Build the host before the Python native checks and set
`OMEGA_SYMBOL_GAME_HOST` to the resulting `omega_symbol_game` binary.

```sh
cargo test --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_epistemic_immune_system -j 1 --test regulation_exact_boundaries --test legacy_state_fences
cargo build --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game --bin omega_symbol_game -j 1
cargo test --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game -j 1 --test anti_skill_host
python -m pytest -q omega_engine_epistemic_immune_system/tests/unit/test_pharmacy_parity.py omega_engine_epistemic_immune_system/tests/unit/test_thymus_binds_executed_matcher.py omega_engine_epistemic_immune_system/tests/unit/test_immune_admission_use_cases.py
python -m pytest -q omega_engine_epistemic_immune_system/tests/unit/test_native_pharmacy_adapter.py omega_engine_epistemic_immune_system/tests/unit/test_oeeis_definitions_yaml.py
python -m pytest -q omega_engine_epistemic_immune_system/tests/unit/test_treg_policy_boundaries.py omega_engine_epistemic_immune_system/tests/unit/test_treg_supervisor.py
python -m pytest -q omega_engine_woland/tests/test_teamwork_digestion.py omega_engine_woland/tests/test_teamwork_continuation.py omega_engine_woland/tests/test_teamwork.py
```

No GitHub Actions, new provider calls, detector admission, deployment or publication
was performed. Historical receipts and the original dirty checkout were preserved.
