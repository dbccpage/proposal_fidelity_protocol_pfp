# Paper 023 claim ledger

Author-review preprint, version 0.1.0, 2026-10-05.

"Prose proof" means the argument stated in the manuscript. A Python
reference names an executable check in `code/replay.py`. Whether a check
passed for this revision is recorded by the dated review receipt, not by
this ledger.

  ------------------------------------------------------------------------------------------------------------------------
  ID                Claim and hypotheses                              Evidence                           Falsifier or
                                                                                                         boundary
  ----------------- ------------------------------------------------- ---------------------------------- -----------------
  PFP023-01         A receipt admitting only $J_{\rm checked}$        Prose proof, Section 2;            A checker failure
                    establishes                                       `code/replay.py` (`valid_witness`) or unsound
                    $\bigwedge_{j\in J_{\rm checked}} R_j(P,w)$ under                                    checker premise.
                    checker soundness
                    $C_j(P,w)=\mathsf{accept}\Rightarrow R_j(P,w)$.

  PFP023-02         A receipt for $J_{\rm checked}$ does not          Countermodel, Section 3;           Explicit logical
                    establish an uninvoked index                      `code/replay.py`                   entailment
                    $k\notin J_{\rm checked}$ or an unchecked         (`false_prose_claim_refused`)      between declared
                    universal sentence without an explicit checked                                       predicates.
                    implication.

  PFP023-03         A correct witness for a declared task cannot      Analysis, Section 3;               Explicit source
                    validate an invented source quotation without     `code/replay.py`                   bytes and
                    supplied source bytes and span verification.      (`unbound_quote_refused`)          certified span
                                                                                                         matching.

  PFP023-04         Mandatory task claim checking is retained         Protocol, Section 4;               Malformed witness
                    fail-closed on malformed submissions or task      `code/replay.py`                   evaluation
                    mismatches.                                       (`wrong_witness_refused`,          bypass.
                                                                      `wrong_task_refused`,
                                                                      `mandatory_task_claim_retained`)
  ------------------------------------------------------------------------------------------------------------------------

## Current validation

The local package replay and verification checks are executable via
`python code/replay.py`. The replay checks valid witnesses, wrong-task
submissions, false prose statements, and unbound source quotations
without network or provider calls.

## Historical material

Shelves 023--027 are author-review teaching drafts. No external deposit,
DOI, or model performance measurement is claimed.

## 2026-10-23 harness extension

  -----------------------------------------------------------------------
  Claim                   Evidence                Limit
  ----------------------- ----------------------- -----------------------
  New research mechanism  Paper 029 source        Implemented adaptation;
                          manifest and focused    historical evidence
                          checks                  remains separately
                                                  pinned

  New model effects       Replayed campaign       NOT_MEASURED; live
                          report                  campaign NOT_RUN

  External AIDE2 findings Versioned PDF and       Attribution, not
                          page-level source map   replication

  Formal results above    Existing proofs and     No additional formal
                          finite examples         theorem or Lean claim
  -----------------------------------------------------------------------
