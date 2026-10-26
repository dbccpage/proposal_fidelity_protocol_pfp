# Detailed definition: Claim-Disciplined Compaction (1)

**AuthorityEffect:** None.

Parent: [Claim-Disciplined Compaction](../../../../../rules/claims/rl_claim_disciplined_compaction.md). Load for the matching predicate, not every task.

# Claim-Disciplined Compaction Invariant

**AuthorityEffect:** None.

Whenever an agent summarizes, compacts, or hands off a conversation turn, session context, or plan execution state, the compaction MUST adhere to the **Claim Hygiene Rule**.

## Core Invariants

1. **Mandatory 5-Point Envelope:** Every compaction summary must explicitly include:
   - What the current state supports.
   - What the current state does NOT support.
   - The narrowest defensible claim.
   - The exact next test needed (with runnable local command).
   - The exact git changeset shape (branch, upstream, HEAD commit, uncommitted files).

2. **Negative Evidence Retention:** Rejected hypotheses, failed experiments, and invalid assumptions must be prominently recorded to prevent downstream turns or successor agents from re-traversing failed state spaces.

3. **Forbidden Language:** Compaction records must never promote toy model tests into universal theorems, nor describe implementation tests as mathematical proofs. Words such as "proves", "guarantees", "flawless", "universal", and "weaponized" are forbidden unless formally justified.

4. **Bound Direction & Premise Distinction:** Summaries and claim records must strictly distinguish lower bounds from upper bounds (e.g., lower bound $\ge 3$ versus upper bound $\le 7$) and distinguish arithmetic evaluations on hypotheses from proved consequences. Paraphrase drift that alters the quantifier or conditional status of a theorem is prohibited.
