# Paper 023 claim ledger

Author-review preprint, version 0.1.0, 2026-10-05.

"Prose proof" means the argument stated in the manuscript. A Python reference
names an executable check in `code/replay.py`. Whether a check passed for
this revision is recorded by the dated review receipt, not by this ledger.

| ID | Claim and hypotheses | Evidence | Falsifier or boundary |
| --- | --- | --- | --- |
| PFP023-01 | A receipt admitting only \(J_{\rm checked}\) establishes \(\bigwedge_{j\in J_{\rm checked}} R_j(P,w)\) under checker soundness \(C_j(P,w)=\mathsf{accept}\Rightarrow R_j(P,w)\). | Prose proof, Section 2; `code/replay.py` (`valid_witness`) | A checker failure or unsound checker premise. |
| PFP023-02 | A receipt for \(J_{\rm checked}\) does not establish an uninvoked index \(k\notin J_{\rm checked}\) or an unchecked universal sentence without an explicit checked implication. | Countermodel, Section 3; `code/replay.py` (`false_prose_claim_refused`) | Explicit logical entailment between declared predicates. |
| PFP023-03 | A correct witness for a declared task cannot validate an invented source quotation without supplied source bytes and span verification. | Analysis, Section 3; `code/replay.py` (`unbound_quote_refused`) | Explicit source bytes and certified span matching. |
| PFP023-04 | Mandatory task claim checking is retained fail-closed on malformed submissions or task mismatches. | Protocol, Section 4; `code/replay.py` (`wrong_witness_refused`, `wrong_task_refused`, `mandatory_task_claim_retained`) | Malformed witness evaluation bypass. |

## Current validation

The local package replay and verification checks are executable via `python code/replay.py`.
The replay checks valid witnesses, wrong-task submissions, false prose statements, and
unbound source quotations without network or provider calls.

## Historical material

Shelves 023–027 are author-review teaching drafts. No external deposit, DOI,
or model performance measurement is claimed.

## 2026-10-23 harness extension

| Claim | Evidence | Limit |
| --- | --- | --- |
| New research mechanism | Paper 029 source manifest and focused checks | Implemented adaptation; historical evidence remains separately pinned |
| New model effects | Replayed campaign report | NOT_MEASURED; live campaign NOT_RUN |
| External AIDE2 findings | Versioned PDF and page-level source map | Attribution, not replication |
| Formal results above | Existing proofs and finite examples | No additional formal theorem or Lean claim |
