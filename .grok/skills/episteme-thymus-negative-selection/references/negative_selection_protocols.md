# Thymic Negative Selection Protocols & Algorithmic Background

## Biological Mechanism
In the human thymus, immature thymocytes undergo two selection processes:
1. **Positive selection (cortex):** Tests whether TCR can bind self-MHC.
2. **Negative selection (medulla):** Medullary thymic epithelial cells (mTECs) express the AIRE
   transcription factor, presenting tissue-restricted self-antigens (insulin, myelin, etc.).
   Any T-cell with high affinity for self-antigen undergoes programmed cell death (apoptosis).

## Computational Algorithm (Forrest et al., 1994)
Stephanie Forrest, Alan Perelson, and Lawrence Allen adapted this into the Negative Selection
Algorithm (NSA) for computer security:
1. Define a set $S$ of normal/self strings representing legitimate system state.
2. Generate candidate detectors $R$.
3. For each $r \in R$, if $r$ matches any $s \in S$, discard $r$.
4. The surviving repertoire $R^*$ detects non-self anomalies without triggering false alarms.

In the Symbol Game, $S$ consists of canonical Lean 4 proof kernels, Clean Architecture domain ports,
and gold-standard prompt completions.
