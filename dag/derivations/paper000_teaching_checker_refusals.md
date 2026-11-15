# PAPER000-TEACHING-CHECKER-REFUSALS: Finite Teaching Checker Refusal Without Mutation

AuthorityEffect: None.

- Archive claim: [ATL-P000-004](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("Incomplete and ill-typed packets are refused without mutation", [paper_claim_ledger.md:8](../../atlas/archive/pfp/000_pfp_introduction/paper_claim_ledger.md?plain=1#L8))
- Audit derivation node: [PAPER000-TEACHING-CHECKER-REFUSALS](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER000-TEACHING-CHECKER-REFUSALS`)
- Review verdict: `matched` (`states_same_claim_as`)

## Claim

The teaching checker refuses an incomplete packet, malformed dictionary, or ill-typed carrier over the declared finite teaching carrier without mutating the candidate proposal.

## Hypotheses

- Declared teaching schema: `symbol-game-basic-packet/v1`.
- Declared packet input model: Python dictionary structure with the exact required field set `{"schema", "carrier", "relation_label", "goal", "candidate"}`.
- Declared finite carrier: non-empty list of unique, non-empty string marks.
- Declared relation label: non-empty string.
- Declared goal: 2-element list of carrier marks.
- Candidate proposal supplied as a 3-element list of strings `[left, relation, right]`.

## Derivation / Evidence

Executable verification is implemented in `atlas/archive/pfp/000_pfp_introduction/code/basic_packets.py` and checked by `atlas/archive/pfp/000_pfp_introduction/code/tests/test_basic_packets.py`:

1. **Incomplete packet refusal**: `test_incomplete_packets` checks that non-dict or incomplete payloads (`None`, `[]`, `{}`, and `{"schema": "other"}`) are refused with status `REFUSED` and reason `SCHEMA`.
2. **Malformed dictionary and field-level refusal**: `test_malformed_or_changed_inputs` checks that packets with malformed fields are refused under expected reasons:
   - Duplicate marks in carrier (`["a", "a"]`): refused with reason `CARRIER`.
   - Ill-typed elements in carrier (`["a", True]`): refused with reason `CARRIER`.
   - Ill-typed candidate element (`["a", "separates", []]`): refused with reason `SCHEMA`.
   - Empty relation label (`""`): refused with reason `RELATION_LABEL`.
   - Mismatched candidate relation label (`["a", "other", "b"]`): refused with reason `RELATION_LABEL`.
   - Goal mark outside carrier (`["a", "c"]`): refused with reason `OUTSIDE_CARRIER`.
   - Goal self-relation (`["a", "a"]`): refused with reason `SELF_RELATION`.
3. **Input proposal immutability control**: `test_check_does_not_mutate_proposal` records `repr(packet)` before calling `check(packet)` on an invalid proposal (`["a", "separates", "c"]`) and asserts `repr(packet) == before`. The checker operates by reading fields and emitting an independent receipt dictionary without modifying the input object.

Test execution command:
```bash
python -m pytest atlas/archive/pfp/000_pfp_introduction/code/tests/test_basic_packets.py -v
```
All 13 test cases pass with zero failures. Full test suite across `atlas/archive/pfp/000_pfp_introduction/code/tests/` executes 28 passing tests.

## Limits

- Applies only to the declared finite teaching schema; this setup does not assert general language semantics or open-domain dialogue parsing.
- Refusal of declared malformed inputs does not establish immunity to arbitrary host payloads outside the schema.
- Does not authenticate caller identity, network transport integrity, or cryptographic producer signatures.
- Does not evaluate large language model capabilities or general reasoning fidelity.

## Claim Hygiene Summary

1. **What it supports**: Demonstrates in this toy setting that `basic_packets.py` refuses incomplete packets, malformed dictionaries, and ill-typed carriers with explicit structured reason receipts (`SCHEMA`, `CARRIER`, `RELATION_LABEL`, `OUTSIDE_CARRIER`, `SELF_RELATION`), while leaving candidate proposal inputs unmodified.
2. **What it does not support**: Does not support claims of general runtime security, unconstrained schema validation, transport authentication, or LLM reasoning correctness.
3. **Narrowest defensible claim**: Under the declared finite schema `symbol-game-basic-packet/v1`, the Python teaching checker execution refuses incomplete packet payloads, malformed dictionaries, and ill-typed carriers, returning a refused receipt without mutating the input dictionary.
4. **Next test needed**: Derivation ATL-P001-001 (Paper 001 discrete cochain retraction and zero obstruction formal theorem verification).
