# pilot_0000001

**AuthorityEffect:** None.
**Task family:** `graph_facts`
**Checker id:** `PFP-02-GRAPH-FACTS`

## 3. Mode trial

The sealed packet and the zero-call execution record are in `tests/test_00/`. Provider calls: 0.

## Description

This directory is a 50-capsule layout for the retained seed. Plain surfaces come first in the free indexes, and the stage-2 P* baseline is `tests/test_11/` when that index was free. Historical response bytes were moved, not rewritten.

## Claim hygiene

### What the files support

- The tree has `test_00` through `test_49`, each with `input.yaml`, `response.yaml`, and `test_spec.yaml`.
- 3 response files are preserved historical records. Their statuses are the statuses already in those files.
- 47 capsules have `trial_status: PLANNED` and an empty `raw_reply`.

### What the files do not support

- They do not support a claim that a provider answered the planned dialects.
- They do not support a pass count over the planned capsules.
- File presence is not a measurement.

### Narrowest claim

- 3 historical responses remain on disk with their recorded statuses, and 47 capsules are unsent plans.

### Next test

- Dispatch one planned capsule and record that provider reply in its own `response.yaml` without editing the other capsules.

## Preserved material

- `packet.yaml` moved to `tests/test_00/packet.yaml` (host seal, not a participant prompt).
- `testplan.yaml` mode-trial bytes moved to `tests/test_00/testplan_mode_trial_v0.yaml`.
- Previous README bytes moved to `tests/test_00/README_mode_trial_v0.md`.
- `results/execution.yaml` moved to `tests/test_00/mode_trial_execution.yaml`.
- Live `mistralai_mistral-7b-instruct_free` preserved beside `tests/test_00/response.yaml`.
- Live `deepseek_deepseek-v4.1-flash` preserved beside `tests/test_01/response.yaml`.
- Live `deepseek_deepseek-v4.1-flash.attempt2` preserved beside `tests/test_02/response.yaml`.
- `results/` removed after every file had a destination.
- `p_star.yaml` bytes are `tests/test_11/p_star.yaml` and `input.yaml`. No response was on disk, so the response is PLANNED.
- spec.yaml models list removed so the file matches the strict pilot spec: ['mistralai/mistral-7b-instruct:free', 'deepseek/deepseek-v4.1-flash'].

## Catalog

| index | test_id | dialect | measurement |
|---|---|---|---|
| 00 | test_00 | Mode 02 - Sealed Envelope Seed | historical |
| 01 | test_01 | Mode 02 - Sealed Envelope Seed | historical |
| 02 | test_02 | Mode 02 - Sealed Envelope Seed | historical |
| 03 | tier_h_headword | Tier H - Head-Word Presentation | PLANNED |
| 04 | tier_d_directive | Tier D - Directive Form | PLANNED |
| 05 | tier_s_strict | Tier S - Strict Boundary Wire | PLANNED |
| 06 | tier_s_carrier | Tier S - Carrier-Declared Role-Typed Packet | PLANNED |
| 07 | tier_s_quarantine | Tier S - Quarantined Proposal Envelope | PLANNED |
| 08 | sn_obfuscated | S(n) Obfuscated | PLANNED |
| 09 | matrix_vector | Matrix/Vector Presentation | PLANNED |
| 10 | retraction_downmap | Retraction Down-Map | PLANNED |
| 11 | pstar_baseline | Stage-2 P* baseline | PLANNED |
| 12 | operator_licensing | Operator Licensing | PLANNED |
| 13 | pregenesis | Pre-Genesis Inscription | PLANNED |
| 14 | genesis_delta | Genesis Delta Candidate | PLANNED |
| 15 | cross_cosmos | Cross-Cosmos Passage | PLANNED |
| 16 | operator_licensing_scoped | Operator Licensing Scoped To The Carrier | PLANNED |
| 17 | matrix_columns | Matrix/Vector Column Presentation | PLANNED |
| 18 | retraction_composed | Retraction Down-Map Composed Twice | PLANNED |
| 19 | tier_h_record | Tier H - Record Form | PLANNED |
| 20 | tier_d_goalsplit | Tier D - Split Goals | PLANNED |
| 21 | sn_named_cut | S(n) Named Cut | PLANNED |
| 22 | tier_s_codebook_v2 | Tier S - Codebook Generation 2 | PLANNED |
| 23 | adjacency_vector | Matrix/Vector Upper Triangle | PLANNED |
| 24 | retraction_quotient | Retraction Quotient Down-Map | PLANNED |
| 25 | plain_sentence_order_b | Plain prose sentence order B | PLANNED |
| 26 | operator_witness_slots | Operator Licensing With Witness Slots | PLANNED |
| 27 | span_witness_names | Span Witness Names | PLANNED |
| 28 | pstar_tier_h_headword | Stage-2 P* - Tier H - Head-Word Presentation | PLANNED |
| 29 | pstar_tier_d_directive | Stage-2 P* - Tier D - Directive Form | PLANNED |
| 30 | pstar_tier_s_strict | Stage-2 P* - Tier S - Strict Boundary Wire | PLANNED |
| 31 | pstar_tier_s_carrier | Stage-2 P* - Tier S - Carrier-Declared Role-Typed Packet | PLANNED |
| 32 | pstar_tier_s_quarantine | Stage-2 P* - Tier S - Quarantined Proposal Envelope | PLANNED |
| 33 | pstar_sn_obfuscated | Stage-2 P* - S(n) Obfuscated | PLANNED |
| 34 | pstar_matrix_vector | Stage-2 P* - Matrix/Vector Presentation | PLANNED |
| 35 | pstar_retraction_downmap | Stage-2 P* - Retraction Down-Map | PLANNED |
| 36 | pstar_operator_licensing | Stage-2 P* - Operator Licensing | PLANNED |
| 37 | pstar_pregenesis | Stage-2 P* - Pre-Genesis Inscription | PLANNED |
| 38 | pstar_genesis_delta | Stage-2 P* - Genesis Delta Candidate | PLANNED |
| 39 | pstar_cross_cosmos | Stage-2 P* - Cross-Cosmos Passage | PLANNED |
| 40 | pstar_operator_licensing_scoped | Stage-2 P* - Operator Licensing Scoped To The Carrier | PLANNED |
| 41 | pstar_matrix_columns | Stage-2 P* - Matrix/Vector Column Presentation | PLANNED |
| 42 | pstar_retraction_composed | Stage-2 P* - Retraction Down-Map Composed Twice | PLANNED |
| 43 | pstar_tier_h_record | Stage-2 P* - Tier H - Record Form | PLANNED |
| 44 | pstar_tier_d_goalsplit | Stage-2 P* - Tier D - Split Goals | PLANNED |
| 45 | pstar_sn_named_cut | Stage-2 P* - S(n) Named Cut | PLANNED |
| 46 | pstar_tier_s_codebook_v2 | Stage-2 P* - Tier S - Codebook Generation 2 | PLANNED |
| 47 | pstar_adjacency_vector | Stage-2 P* - Matrix/Vector Upper Triangle | PLANNED |
| 48 | pstar_retraction_quotient | Stage-2 P* - Retraction Quotient Down-Map | PLANNED |
| 49 | pstar_plain_sentence_order_b | Stage-2 P* - Plain prose sentence order B | PLANNED |
