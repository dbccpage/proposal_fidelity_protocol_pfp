# C019: Degree-2 Obstructions at Scale

## Problem Statement

Given an oriented 2-complex $K = (V, E, F)$ with integer boundary maps $\partial_1: C_1 \to C_0$ and $\partial_2: C_2 \to C_1$, a target 2-cochain $B \in \mathbb{Q}^F$, face weights $\omega_f > 0$, and mode $\in \{Q, Z\}$:
1. Verify boundary nilpotency: $\partial_1 \circ \partial_2 = 0$. If violated, return `OUT_OF_SCOPE` with witness.
2. In mode Q:
   - If $B = d_1 A$ for some $A \in \mathbb{Q}^E$, return `EXTENDS` with potential $A$ and $\Phi_2 = 0$.
   - If obstructed, return `OBSTRUCTED` with a 2-cycle $Z \in \mathbb{Q}^F$ ($\partial_2 Z = 0$) such that $\langle B, Z \rangle \ne 0$, and exact dual witness $y$ attaining $\Phi_2(B) = \langle B, y \rangle$.
3. In mode Z:
   - If $B = d_1 A$ with $A \in \mathbb{Z}^E$, return `EXTENDS_INTEGRAL`.
   - If obstructed over $\mathbb{Z}$, return `OBSTRUCTED_INTEGRAL` with modulus $m \ge 2$ and integer chain $Z$ such that $\partial_2 Z \equiv 0 \pmod m$ and $\langle B, Z \rangle \not\equiv 0 \pmod m$.

## Output Contract

```json
{"status": "SOLVED", "mode": "Q", "verdict": "EXTENDS", "A": {"e01": "1"}, "phi2": "0"}
{"status": "SOLVED", "mode": "Q", "verdict": "OBSTRUCTED", "cycle": {"f0": "1", "f1": "-1", "f2": "1", "f3": "-1"}, "pairing": "1", "phi2": "1", "primal_A": {}, "dual_y": {"f0": "1", "f1": "-1", "f2": "1", "f3": "-1"}}
{"status": "SOLVED", "mode": "Z", "verdict": "OBSTRUCTED_INTEGRAL", "modulus": "2", "chain": {"f0": "1"}, "pairing_mod": "1"}
{"status": "OUT_OF_SCOPE", "witness": {"reason": "BOUNDARY_NOT_NILPOTENT", "face": "f0"}}
```
