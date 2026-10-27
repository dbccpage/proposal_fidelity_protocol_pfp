# Authenticated custody and recovery checkpoint

AuthorityEffect: None. This is a bounded implementation checkpoint on top of
`9fb52d239ecfd0abf533734901803e3050a75d8d`, with remote main
`3e4861aeb1f9b9b09f10175d6ac9830205d3c16b` incorporated. It supplements the
[earlier checkpoint](../epic_boundary_repair_20261012/README.md) without rewriting
its historical claims or hashes. All work and review here used one Codex worker;
no independent reviewer or paid provider call is claimed.

## Implemented changes

- EIS002: the operational activation port now refuses missing or unusable
  authenticated host health. Real signed-report controls cover health recovery
  and suspension through persisted admission state.
- EIS003: explicit-key Ed25519 verification, exact rule/source/scope/context
  binding, expiry/revocation, replay protection, signed suspension and fresh
  reinstatement, reusing the existing SQLite/BLAKE3 receipt ledger.
- EIS004: a finite serialized detector, malformed-receipt canary and healthy
  control feed the existing Thymus and eligibility paths. Authenticated views
  bind the full candidate/source/fixture request. Expired observations remain
  in history but do not count; fresh signed evidence restores eligibility.
  Eligible candidates remain unadmitted.
- Adversary consolidated SAGA4: native reconciliation now refuses unreadable
  journal lines before writing, matching Python. Actual damaged bytes survive;
  explicit repair allows idempotent CRASHED_UNKNOWN closure.

The [contract](../../documentation/authenticated_custody.md) specifies exact
signed bytes, configured trust, validity windows, external tip retention and
single-writer assumptions. Python signs fixture evidence independently;
sovereign Rust owns cryptographic and transition verification. No production
private key, human identity, actual host measurement or admission is invented.

## Recorded verification

The [validation record](validation.json) binds commands, outcomes, runtime
versions, source inventory and selected log output. The
[SoftwareQaReceiptV1](software_qa_receipt.json) records the bounded mutation
evidence. These certify neither the full epic suites nor unrestricted research.

| Focused check | Result |
| --- | --- |
| New authenticated admission, host health and finite-observation controls, three pytest files | 40 passed |
| Existing EIS admission/activation controls, three pytest files | 84 passed |
| Adversary journal, teamwork and digestion controls, three pytest files | 53 passed |
| Native authenticated custody, admission support and activation-port parity | 8 passed |
| Native Adversary journal acceptance and parity | 5 passed; one subprocess helper is marked ignored at top level and is explicitly executed by its parent crash test |
| Existing epic manifest, traversal and non-regular-file controls | 55 passed |
| Remove health requirement; remove full-request binding; remove native signature verification | All three mutations were detected; exact sources restored and controls passed |

The original missing-health and native corrupt-journal tests were genuinely
RED before implementation. A later expiry control exposed retained stale rows
blocking fresh-evidence recovery; that production issue was repaired and its
control passed. One early fixture constructor omitted `target_epitope`; that
test-authoring error was fixed and is not counted as a production defect.

Native compilation used Rust/Cargo 1.99 and `-j 1`. Python used 3.12.14 and the
rebuilt native host. `blake3` is now declared for the reused ledger;
`cryptography` is a development dependency for independent fixture signing.
Both Cargo and uv lockfiles are updated. Existing historical fixture archives
and prior receipts are preserved; no publication archive or paper was changed.

Example focused reproduction, after building the native host and installing
the project's development dependencies:

```bash
cargo test --manifest-path engine/crates_rs/Cargo.toml -p core_epistemic_immune_system -j 1 --test authenticated_custody --test admission_support --test activation_use_case_parity
cargo test --manifest-path engine/crates_rs/Cargo.toml -p core_adversary -j 1 --test journal_acceptance --test journal_parity
python -m pytest -q eis/tests/integration/test_authenticated_admission.py eis/tests/unit/test_activation_host_health.py eis/tests/test_prior_art_negative_selection_fixtures.py
```

Set `CORE_SYMBOL_GAME_HOST` to the rebuilt `core_symbol_game` executable for
Python reproduction. No GitHub Actions were used or changed.

## Full epic disposition

All eight target plans were inspected. The updated byte manifest and walk
successor keep executed slices separate from their prospective full test plans.

| Epic | Current disposition |
| --- | --- |
| EIS001 | Earlier twelve-class native pharmacy and candidate-binding work retained; no semantic completeness claim. |
| EIS002 | Signed health delivered; actual observer deployment and generalized tolerance remain external/empirical obligations. |
| EIS003 | Signed custody and reinstatement delivered; operator key enrollment, durable pin storage, key rollover and automated regulation/learning composition remain separate. |
| EIS004 | Finite production-bound experiment delivered; broad source-theorem adoption and empirical independence remain research. |
| Adversary prior-art001 | Existing finite gate predicates/application retained; source assumptions and trusted measurement collection remain open. |
| Adversary002 | Existing shared coordinator and bounded text-file executor retained; paid OpenRouter demonstration, generalized remote tools and dynamic routing remain unclaimed. |
| Adversary003 | Existing D1–D5 delivery and fresh original-task recheck retained; broad autonomous/generalization claims remain open. |
| Adversary consolidated | Native corrupt-journal refusal repaired; multi-worker coordination, seamless checkpoint resume and mathematical saga claims remain deferred. |

A caller must supply real trust configuration and retain ledger pins outside
the database. A hash chain alone cannot establish a human authorization,
physical storage integrity or atomic persistence across two stores. Distinct
signed reports do not prove statistically independent experiments.

Global planning checks still encounter unrelated missing FSP publication and
OEPFP education paths; scoped target-plan checks and the complete byte-manifest
audit are reported separately. The draft PR does not claim a globally clean
repository or merge authorization. The original checkout's unrelated changes
are preserved.
