# PFP Fixtures (`fixtures`)

**AuthorityEffect:** `None`

## 1. Role

YAML task-packet and negative mutation fixtures for the Proposal Fidelity Protocol (PFP). Carries `authority_effect: None`, `evidence_ceiling: ReplayableLabEvidence`, and `oracle_policy: IndependentGateReceiptsAndExternalPromotionRequired`.

## 2. Directory Inventory

| Item | Type | Purpose |
|---|---|---|
| [`fix_fable_long_horizon_task_packet.yaml`](fix_fable_long_horizon_task_packet.yaml) | YAML packet (v2 canonical with v1 predecessor) | Unified bootstrap fixture: carrier `core-repository-pathset-v2`, `packet_family: code_change_proposal.bootstrap.v2`, step budget 64, payload a `BOOTSTRAP_REFUSED` task statement with blockers and milestone specifications, preserving v1 predecessor lineage. |
| [`fix_negative_mutation_fixtures.yaml`](fix_negative_mutation_fixtures.yaml) | YAML fixtures | Catalog of negative mutation and perturbation test cases for fail-closed verification. |

## 3. Scope

- Fixtures are inputs, not receipts, and carry no authority.
