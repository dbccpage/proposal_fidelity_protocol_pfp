# PAPER000-TEACHING-CHECKER-REJECTIONS: Finite Teaching Checker Mutant Rejections

AuthorityEffect: None.

- Archive claim: [ATL-P000-003](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("The teaching checker rejects a self-relation, carrier escape, and reversed goal", [paper_claim_ledger.md:7](../../atlas/archive/pfp/000_pfp_introduction/paper_claim_ledger.md?plain=1#L7))
- Audit derivation node: [PAPER000-TEACHING-CHECKER-REJECTIONS](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER000-TEACHING-CHECKER-REJECTIONS`)
- Review verdict: `matched` (`states_same_claim_as`)

## Claim

The teaching checker rejects a self-relation, a carrier escape, and a reversed goal over the declared finite teaching carrier without mutating the candidate proposal.

## Hypotheses

- Declared teaching schema: `symbol-game-basic-packet/v1`.
- Declared finite carrier with distinct string marks.
- Fixed relation label and ordered 2-element goal.
- Candidate proposal supplied as a 3-element relation triple.

## Derivation / Evidence

Executable verification is implemented in `atlas/archive/pfp/000_pfp_introduction/code/basic_packets.py` and checked by `atlas/archive/pfp/000_pfp_introduction/code/tests/test_basic_packets.py`:

1. **Self-relation rejection**: A proposal where candidate elements coincide (e.g. `["a", "separates", "a"]`) or where the goal elements coincide is refused with reason `SELF_RELATION`.
2. **Carrier escape rejection**: A proposal introducing elements outside the declared carrier (e.g. `["a", "separates", "c"]` for carrier `["a", "b"]`) is refused with reason `OUTSIDE_CARRIER`.
3. **Reversed goal rejection**: A proposal where candidate order does not match the declared goal (e.g. `["b", "separates", "a"]` for goal `["a", "b"]`) is refused with reason `GOAL_UNMET`.
4. **Immutability control**: `test_check_does_not_mutate_proposal` asserts that `check(packet)` does not modify the proposal dictionary.

Test execution command:
```bash
python -m pytest atlas/archive/pfp/000_pfp_introduction/code/tests/test_basic_packets.py -v
```
All 13 test cases pass with zero failures.

## Limits

- Applies only to the declared finite teaching schema; this setup does not assert general language semantics.
- Rejection of specified mutants does not guarantee immunity to arbitrary invalid payloads outside the schema.
- Does not authenticate caller identity or producer signatures.
