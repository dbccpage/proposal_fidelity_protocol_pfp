# Injection record: the reach checker

**AuthorityEffect:** `None`.

A check is not proved by being green. It is proved by failing on the defect it
exists to catch, and by recovering when that defect is reversed.

## Per-code fixtures (standing, in the test suite)

Every refusal code has a fixture injection in the test suite, and each fails
with exactly its code:

- `tests/test_reach_receipt.py::INJECTIONS` covers the 36 `RR-*` codes;
- `tests/test_reach_transport.py::INJECTIONS` covers the 15 `TC-*` codes.

A census test in each file refuses a registered code that has no injection.

Injections that are not exact are marked `exact=False`. For these the code is
present, but other refusals cascade from the same defect:

- `RR-NO-POSITIVE`: its mutations lose their repair;
- `RR-EMPTY-PAYLOAD` and `RR-FLAG-ONLY`: the replay also refuses the positive.

## Source injections (2026-09-25, branch `claude/p1-reach-ledger`)

Each injection broke one guard in the checker's own source. The three reach test
files then ran, and the file was restored with `git checkout`.

| # | injected into | defect | tests that failed |
|---|---|---|---|
| I1 | `receipt.py` | the K3 verdict scan returns nothing (`verdicts: list[str] = []`) | 7: `test_grade_is_computed_never_read_a_declared_grade_is_refused`, `test_any_producer_verdict_field_is_refused[terminal, outcome, verdict, computed]`, `test_nested_producer_verdict_is_refused`, `test_injection_fails_with_its_exact_code[RR-PRODUCER-VERDICT]` |
| I2 | `targets.py` | `is_flag_only` always returns `False` | 2: `test_injection_fails_with_its_exact_code[RR-FLAG-ONLY]`, `test_flag_only_payload_refused_even_by_a_checker_that_accepts_it` |
| I3 | `ledger.py` | stored receipts are not re-verified (`result.codes = ()`) | 2: `test_hand_edited_stored_receipt_is_refused`, `test_refused_receipt_cannot_be_filed` |
| I4 | `transport.py` | the standing-entry loop iterates over `()` | 6: `TC-UNBOOKED-STANDING-ENTRY`, the four families (ties, readings, bounds, blindness), and `test_blind_rung_missing_blindness_entry_is_unbooked` |
| I5 | `receipt.py` | the per-clause bite check is skipped (`if False:`) | 1: `test_injection_fails_with_its_exact_code[RR-NO-FLIP]` |

**Recovery:** after all five were reverted, `98 passed`, and `git status` was
clean.

**What this does not prove:** that the clause split of any real level is the
right one. A perfect check of the wrong clause set still checks the wrong set.
The clause split is reviewed once per checker when that checker is registered.

## Round P2: the stage 0-21 target checkers (2026-09-25, branch `claude/p2-checkers`)

### Standing injections (in the test suite)

- **Bite, per clause, by source injection.**
  `tests/test_target_checkers.py::test_source_injection_each_clause_guard_is_load_bearing`
  runs 100 cases, one per claimed clause of the 22 checkers. Each appends to the
  checker's own bytes a `_refuse` that turns that clause's code into a no-op,
  and loads the result through `targets.load_checker`. The injected checker
  still accepts the positive, and no longer refuses the clause's decisive
  mutation with the clause's code. The uninjected checker refuses it with that
  code. All 100 hold.
- **Stage binding.** `test_checker_bound_to_another_rows_digest_is_refused`
  rewrites stage 004's `ROW_SHA256` to row 3's digest and re-pins it. The
  record is refused with exactly `RR-PIN`, naming the row digest.
- **The probe fix.** `test_stage_000_record_was_refused_as_hollow_before_the_probe_fix`
  replays stage 000's record twice. With the fix, the record is clean and
  `lists_emptied` is recorded as `INAPPLICABLE` with code
  `PROBE-IDENTICAL-TO-POSITIVE`. With `same_payload` patched to always say
  "different" (the old behaviour), the same record is refused with exactly
  `RR-HOLLOW-CHECKER`, naming `lists_emptied`.
- **Stage status falls by computation.**
  `test_stage_status_computes_every_registered_stage_and_drops_it_on_drift`
  shows every registered stage computes as `COMPUTED`, then injects twice into
  stage 007's binding: a registered SHA-256 that no longer matches the bytes
  (failure names the pin), and bytes that stop refusing the own negative
  (failures name the own negative and the stage-negative fixture).

### The anti-evidence sites: before and after

`tests/test_anti_evidence.py` was committed together with the fixes. It was run
on the tree without them (`git stash` of the fixed files; the test file kept),
and then restored.

| test | before | after |
|---|---|---|
| `test_demo_verifier_recomputes_through_the_target_checker[4, 9, 10, 17, 19, 21]` | 6 FAILED | 6 passed |
| `test_demo_verifier_refuses_the_flag_or_label_it_used_to_trust[4, 9, 10, 19, 21]` | 5 FAILED: each flag or label payload was accepted | 5 passed |
| `test_lean_docs_cite_only_theorems_that_exist[4.4 Level 9, 4.5 Level 10]` | 2 FAILED: four cited theorems exist in no Lean file | 2 passed |
| `test_lean_docs_cite_only_theorems_that_exist[5.7 Level 21]` | passed (a drift guard: it fails if the doc keeps citing the withdrawn theorem) | passed |
| `test_level21_lean_no_longer_proves_the_scalar_deficit_sum` | FAILED | passed |
| `test_packet_17_checksum_is_sha256_as_grammar_17_specifies` | FAILED: CRC32 | passed |
| `test_packet_19_example_recomputes` | FAILED: P(2) = 2 for the declared radius 2 | passed |
| `test_packet_21_example_recomputes` | FAILED: declared 5/288, recomputed -5 | passed |

Totals: 17 failed and 1 passed before; 18 passed after.

**Lean build, unfiltered.** `lean Level21DiscreteRegge.lean` from `lean4/`
exited 0 and printed, in full:

```
'MSSN.Level21.rotYZ_orthogonal' depends on axioms: [propext]
'MSSN.Level21.rotXZ_orthogonal' depends on axioms: [propext]
'MSSN.Level21.scalar_sum_does_not_certify_closure' depends on axioms: [propext]
```

The whole `lean4` Lake project was not rebuilt. `TowerLadder.lean` imports this
module but uses none of its names.

## The declared harness host (round P2, branch `claude/p2-engine-replay`)

`carriers.json` declares 19L57G1's `harness_host` as `the_symbol_game`, and
`GitResolver` tries that host after any clone of the carrier's own. The test
`test_a_declared_harness_host_resolves_only_commits_in_its_history` covers
three cases: a host commit resolves, a carrier commit outside the host's
history does not, and a missing clone falls through to the host.

As injection I36 in `research/level_engine/INJECTIONS.md`, the declaration was
deleted on disk. `ledger --check`, in its default context, then failed with
`stored receipt ... does not verify: RR-PRODUCER-VERDICT` (exit 1). The
recomputed block refuses `RR-PIN`, so it differs from the stored one. With the
declaration restored, the check passes (exit 0).

**What this does not prove:** that each checker's clause split is the right
reading of its row. The split is written in each checker's docstring and is
reviewed once, at registration.

## Round P3: the stage 22-46 target checkers (2026-09-25, branch `claude/p3-checkers`)

### Standing injections (in the test suite)

- **Bite, per clause, by source injection.**
  `tests/test_target_checkers.py::test_source_injection_each_clause_guard_is_load_bearing`
  now runs 195 cases, 95 of them for the 25 new checkers (one per claimed
  clause). As in P2, each appends to the checker's own bytes a `_refuse` that
  turns one clause's code into a no-op. The injected checker still accepts the
  positive and no longer refuses that clause's decisive mutation with the
  clause's code; the uninjected checker does. All 95 hold.
- **Stage binding.** `test_checker_bound_to_another_rows_digest_is_refused`
  also runs on stage 029: its `ROW_SHA256` rewritten to row 28's digest and
  re-pinned. The record is refused with exactly `RR-PIN`, naming the row digest.
- **Stage status falls by computation.**
  `test_stage_status_computes_every_registered_stage_and_drops_it_on_drift`
  also runs on stage 040: a registered SHA-256 that no longer matches the bytes
  (failure names the pin), and bytes that stop refusing the own negative
  (failures name the own negative and the stage-negative fixture).

### A live injection through the `target-checkers` step

The guard `R030_RESURRECTED` was deleted from `targets/stage_030.py` in the
working tree, and the step's two test files were run. 8 failed:

| test | why |
|---|---|
| `test_four_fixture_rule_with_exact_codes[30]` | the own negative is no longer refused with its code |
| `test_every_clause_has_a_single_edit_mutation_refused_with_its_code[30]` | C5's mutation is refused `R030_PAGE`, not `R030_RESURRECTED` |
| `test_source_injection_each_clause_guard_is_load_bearing[30-C5]` | the uninjected checker no longer bites on C5 |
| `test_full_record_on_the_checker_is_clean_and_earns_r1[30]` | the record's bite check fails |
| `test_registered_checkers_of_record_match_their_files` | the bytes differ from the registered pin |
| `test_stage_status_computes_every_registered_stage_and_drops_it_on_drift[7, 40]` | stage 030 no longer holds, so it drops out of COMPUTED |
| `test_anti_evidence.py::test_demo_verifier_recomputes_through_the_target_checker[30]` | the demo verifier, which delegates, now passes the own negative |

**Recovery:** `git checkout` of the file; the step passes again.

### The demo verifiers: before and after

`tests/test_anti_evidence.py` extends both demo tests to the 24 delegated
stages (22-46 except 35). Run against the previous `demos/mssn/verifiers.py`
(the test file kept), then restored:

| test | before | after |
|---|---|---|
| `test_demo_verifier_recomputes_through_the_target_checker[22..46 except 35]` | 24 FAILED | 24 passed |
| `test_demo_verifier_refuses_the_flag_or_label_it_used_to_trust[22..46 except 35]` | 24 FAILED: each flag, number or label payload was accepted | 24 passed |

Totals: 48 failed and 18 passed before; 66 passed after.

**What this does not prove:** that each checker's clause split is the right
reading of its row, or that its declared input class is the right one. Both
are written in each checker's docstring (and the class in
`registry/checkers.json`), and are reviewed once, at registration.

## Round P4: the stage 47-73 target checkers (2026-09-25, branch `claude/p4-checkers`)

### Standing injections (in the test suite)

- **Bite, per clause, by source injection.**
  `tests/test_target_checkers.py::test_source_injection_each_clause_guard_is_load_bearing`
  now runs 304 cases, 109 of them for the 27 new checkers (one per claimed
  clause). As in P2 and P3, each appends to the checker's own bytes a
  `_refuse` that turns one clause's code into a no-op. The injected checker
  still accepts the positive and no longer refuses that clause's decisive
  mutation with the clause's code; the uninjected checker does. All 109 hold.
- **Stage binding.** `test_checker_bound_to_another_rows_digest_is_refused`
  also runs on stage 060: its `ROW_SHA256` rewritten to row 59's digest and
  re-pinned. The record is refused with exactly `RR-PIN`, naming the row digest.
- **Stage status falls by computation.**
  `test_stage_status_computes_every_registered_stage_and_drops_it_on_drift`
  also runs on stage 069: a registered SHA-256 that no longer matches the bytes
  (failure names the pin), and bytes that stop refusing the own negative
  (failures name the own negative and the stage-negative fixture). Before the
  band was registered this case failed with `KeyError: 'stage_069'`; after
  registration it passes.

### A live injection through the `target-checkers` step

The closure guard `R064_NOT_CLOSED` was deleted from `targets/stage_064.py` in
the working tree. It is the guard the vacuity warning of W2-DC section 2.18
names: edge-derived faces always close, so only supplied face data can fail.
The step's two test files were run. 9 failed:

| test | why |
|---|---|
| `test_four_fixture_rule_with_exact_codes[64]` | the own negative (supplied faces t1, t2, t1, t2) is accepted |
| `test_every_clause_has_a_single_edit_mutation_refused_with_its_code[64]` | C4's mutation (face order A, B, D, C) is accepted |
| `test_source_injection_each_clause_guard_is_load_bearing[64-C4]` | the uninjected checker no longer bites on C4 |
| `test_full_record_on_the_checker_is_clean_and_earns_r1[64]` | the record's own-negative and bite checks fail |
| `test_registered_checkers_of_record_match_their_files` | the bytes differ from the registered pin |
| `test_stage_status_computes_every_registered_stage_and_drops_it_on_drift[7, 40, 69]` | stage 064 no longer holds, so it drops out of COMPUTED |
| `test_anti_evidence.py::test_demo_verifier_recomputes_through_the_target_checker[64]` | the demo verifier, which delegates, now passes the own negative |

**Recovery:** `git checkout` of the file; the step passes again.

### The demo verifiers: before and after

`tests/test_anti_evidence.py` extends both demo tests to 47-73 (27 stages, all
delegated; 48's old recomputation was a real-only bilinear sum). Run against
the previous `demos/mssn/verifiers.py` (the test file kept), then restored:

| test | before | after |
|---|---|---|
| `test_demo_verifier_recomputes_through_the_target_checker[47..73]` | 27 FAILED | 27 passed |
| `test_demo_verifier_refuses_the_flag_or_label_it_used_to_trust[47..73]` | 27 FAILED: each flag, scalar or label payload was accepted | 27 passed |

Totals: 54 failed and 66 passed before; 120 passed after. Two flag payloads
(55, 67) first carried booleans only and were refused by the demo's own
admission, so they proved nothing; each now also carries a `note` string and
fails before the fix.

### Differential checks run once (not standing)

In a scratch script, not committed: the 069 Sturm decision against the known
roots of 300 random products of distinct rational linear factors; the 071
all-n decision against brute force up to n = 3000 on 300 random rational
sequences; the 073 all-depth decision against brute force up to k = 12 on 300
random polynomial integrands; the 070 trace-recurrence route against the
interpolated-determinant route on 200 random tables; the 056 elimination test
against 2 x 2 minors on 500 random self-mirrored tables. 0 disagreements.

**What this does not prove:** that each checker's clause split is the right
reading of its row, or that its declared input class is the right one. Both
are written in each checker's docstring and in `registry/checkers.json`
(`input_class`), and are reviewed once, at registration.

## Round P5: the stage 74-100 target checkers (2026-09-25, branch `claude/p5-checkers`)

### Standing injections (in the test suite)

- **Bite, per clause, by source injection.**
  `tests/test_target_checkers.py::test_source_injection_each_clause_guard_is_load_bearing`
  now runs 423 cases, 119 of them for the 27 new checkers (one per claimed
  clause). As in P2-P4, each appends to the checker's own bytes a `_refuse`
  that turns one clause's code into a no-op. The injected checker still
  accepts the positive and no longer refuses that clause's decisive mutation
  with the clause's code; the uninjected checker does. All 119 hold. Writing
  them found one hang: with its cycle refusal disabled, stage 077's
  topological loop never ended. Every loop in the band now computes its
  verdict first and refuses after, so a disabled guard falls through.
- **Stage binding.** `test_checker_bound_to_another_rows_digest_is_refused`
  also runs on stage 090, its `ROW_SHA256` rewritten to row 89's digest and
  re-pinned. The record is refused with exactly `RR-PIN`.
- **Stage status falls by computation.**
  `test_stage_status_computes_every_registered_stage_and_drops_it_on_drift`
  also runs on stage 080. Stage 097 was tried first and does not qualify: with
  `R097_SURVIVING_MUTANT` disabled, its own negative is still refused, by
  `R097_WRONG_INVARIANT`. 16 of the 27 own negatives are refused by a second
  guard when their own code is disabled, and the other 11 are accepted (76,
  77, 79, 80, 84-87, 89, 93, 100). The drift test needs an own negative that
  is accepted once its code is disabled.
- **Ruling D4 in the ledger.**
  `tests/test_reach_ledger.py::test_apparatus_checkers_count_in_a_never_in_c`
  works on the committed registry, in memory. Removing `provenance` from
  stage 090 moves the target from (C, A) = (80, 21) to (81, 20). Adding it to
  stage 050 moves it to (79, 22), and the 047-073 band drops to 26. An unknown
  provenance value raises `LedgerError`.
  `test_d4_apparatus_levels_are_exactly_the_registered_apparatus_checkers`
  pins the marked set to {012, 017, 082-100}.

### Two live injections

**1. Through the `target-checkers` step.** The guard `R075_DELETION_OMITTED`
(the level's negative) was deleted from `targets/stage_075.py` in the working
tree, and the step's two test files were run. 10 failed:

| test | why |
|---|---|
| `test_four_fixture_rule_with_exact_codes[75]` | the own negative (the deletion of b,1 omitted) is refused for the wrong reason, `R075_DELTA_MISMATCH` |
| `test_every_clause_has_a_single_edit_mutation_refused_with_its_code[75]` | C3's mutation is refused with `R075_DELTA_MISMATCH` |
| `test_source_injection_each_clause_guard_is_load_bearing[75-C3]` | the uninjected checker no longer bites on C3 |
| `test_full_record_on_the_checker_is_clean_and_earns_r1[75]` | `RR-NO-FLIP` for C3 and `RR-WRONG-REASON` for the own negative |
| `test_registered_checkers_of_record_match_their_files` | the bytes differ from the registered pin |
| `test_stage_status_computes_every_registered_stage_and_drops_it_on_drift[7, 40, 69, 80]` | stage 075 no longer holds, so it drops out of COMPUTED |
| `test_anti_evidence.py::test_demo_verifier_recomputes_through_the_target_checker[75]` | the delegating demo verifier refuses for the wrong reason |

The omitted deletion was still refused, by the delta check. The gate failed
because the reason was wrong: exact codes matter.

**Recovery:** `git checkout` of the file; the step passes again.

**2. Through the registry.** `provenance` was removed from `stage_090` in
`registry/checkers.json`. `ledger --check` exited 1 (`DIFFERS: ...
derived/numbers.json`), and three tests in `test_reach_ledger.py` failed:
`test_committed_ledger_regenerates_byte_identically`,
`test_d4_apparatus_levels_are_exactly_the_registered_apparatus_checkers` and
`test_apparatus_checkers_count_in_a_never_in_c`. **Recovery:** the file
restored; `ledger --check` exits 0.

### The demo verifiers: before and after

`tests/test_anti_evidence.py` extends both demo tests to 74-100. All 27 stages
are delegated. Each old verifier read one flag whose default was the passing
value, and 96 compared a declared trial count with 30. The tests were run
against the previous `demos/mssn/verifiers.py`, with the test file kept:

| test | before | after |
|---|---|---|
| `test_demo_verifier_recomputes_through_the_target_checker[74..100]` | 27 FAILED | 27 passed |
| `test_demo_verifier_refuses_the_flag_or_label_it_used_to_trust[74..100]` | 27 FAILED: each flag payload was accepted | 27 passed |

Totals for the two demo tests: 54 failed and 113 passed before, 167 passed
after. The whole file passes: 174. `demos/mssn/test_mssn.py` passes with 1596
subtests (1547 before).

**What this does not prove:** that each checker's clause split is the right
reading of its row, or that its declared input class is the right one. For the
19 apparatus rows, a checker deciding the row's obligation is not an
object-language witness. Ruling D4 keeps them out of C for that reason.
