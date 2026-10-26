# Active Obstruction Registers vs Persistent History Ledgers

AuthorityEffect: None.

This reference formalizes the dual-register semantics and mathematical realization invariants for $S(n)$ stages.

## 1. Dual-Register Invariant: $W_n^{\mathrm{active}}$ vs $H_n$

1. **Active Obstruction Register ($W_n^{\mathrm{active}}, s_n$):**
   Cardinality of the finite typed set of currently surviving unresolved Genesis obstruction receipts:
   $$W_n^{\mathrm{active}} := \text{unresolved Genesis obstruction receipts}, \qquad s_n := |W_n^{\mathrm{active}}|$$
2. **Cumulative History Ledger ($H_n$):**
   Persistent certificate ledger recording all resolved receipts, cost floors, and orbit closures:
   $$H_0 \subset H_1 \subset H_2 \subset \dots \subset H_n$$
3. **Anti-Pattern Notice:** Never merge $W_n^{\mathrm{active}}$ and $H_n$ merely to mechanically force $s_n = n$. Closed receipts belong strictly to $H_n$.

## 2. Normative Genesis Core Sequence ($S(0)$ to $S(6)$)

The normative Genesis sequence is strictly: $s_0=0, \; s_1=1, \; s_2=1, \; s_3=1, \; s_4=0, \; s_5=1, \; s_6=1$.

| Stage | Name | Active Register ($W_n^{\mathrm{active}}$) | $s_n$ | History Ledger Additions ($H_n$) |
| :--- | :--- | :--- | :---: | :--- |
| **S(0)** | Ground | $\emptyset$ (empty carrier $V_0 = \emptyset$, token `<>`) | 0 | $\mathrm{receipt}_{\mathrm{ground}}$ |
| **S(1)** | Supply | $\{\mathrm{demand}_{\mathrm{action}}\}$ (lone mark admitted) | 1 | $\mathrm{receipt}_{\mathrm{supply}}$ |
| **S(2)** | Retention | $\{\mathrm{demand}_{\mathrm{collapse}}\}$ (collapsed under $S_2$) | 1 | $\mathrm{receipt}_{\mathrm{retention}}$ |
| **S(3)** | Separation | $\{\mathrm{demand}_{\mathrm{unclosed\_orbits}}\}$ | 1 | Cost-2 separation floor |
| **S(4)** | Closure | $\emptyset$ (`terminal_all_separated`, fixpoint) | 0 | Full automorphism closure |
| **S(5)** | Continuation | $\{\mathrm{demand}_{\mathrm{continuation}}\}$ (external continuation) | 1 | Fixpoint exit witness |
| **S(6)** | Extension | $\{\mathrm{gap}_{\mathrm{stabilization}}\}$ (descent down-map $r_N$) | 1 | Section/retraction $\{u_N, r_N\}$ |

## 3. Retraction Down-Map Notation ($r_N$) & Lift Rank ($\delta_n$)

- **Down-Map Symbol:** Retraction down-maps must use $r_N$, never $d_N$ (avoiding collision with death counts $d_n$ and coboundaries $d_k$):
  $$r_N: S(N+1) \to S(N) \sqcup \{\mathrm{NON\_DESCENT}\}, \qquad r_N(u_N(x)) = x$$
- **Pair Typing:** $\{u_N, r_N\}$ is a **section/retraction pair** ($r_N \circ u_N = \mathrm{id}$, $u_N \circ r_N \neq \mathrm{id}$)$, never an involution pair.
- **Lift Rank:** $\delta_n := \#\{\text{newly adjoined operators}\}$ is defined independently from survivor delta $s_{n+1} - s_n$.
- **Dual Pair Visibility ($n \ge 6$):** Regular lifts adjoin dual involution pairs ($\delta_n = 2$), visibly declared at each stage (e.g. $\{u_6, r_6\}$, $\{d_0, d_0^T\}$, $\{P_\parallel, P_\perp\}$).

## 4. Mathematical Realization Invariants & Anti-Patterns

| Domain | Invariant Rule | Violation / Anti-Pattern |
| :--- | :--- | :--- |
| **Simplicial** | $\partial_0 [v] = 0$ in unaugmented homology; augmented requires $\widetilde{\partial}_0 [v] = [\emptyset]$. | Writing $\partial \langle v \rangle = \langle \rangle$ without declaring augmented complex. |
| **Skeletons** | $k$-simplex $\Delta_k$ has $k+1$ vertices and 1-skeleton $K_{k+1}$. $K_4$ has 4 vertices (3-simplex). | Calling $K_4$ a "4-simplex skeleton". |
| **Metric / Regge** | Exact rational squared edge lengths $\ell_e^2 \in \mathbb{Q}^+$. Deficits $\delta_h$ require $0 \notin [\delta_h^{\mathrm{lo}}, \delta_h^{\mathrm{hi}}]$. | Relying on floating point zero or uncertified transcendental angles. |
| **Adjunction** | Categorical $F \dashv G$ requires functorial natural isomorphism. Cochain $d_0 \leftrightarrow d_0^T$ is a linear transpose. | Conflating matrix transpose $\langle d_0 g, y \rangle = \langle g, d_0^T y \rangle$ with categorical adjunction. |
| **Dagger** | Purely algebraic involution $(f^\dagger)^\dagger = f$, $(g \circ f)^\dagger = f^\dagger \circ g^\dagger$. | Asserting physical time-reversal or CPT symmetry from algebraic dagger. |
