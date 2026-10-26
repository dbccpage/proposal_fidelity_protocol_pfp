---
documentation_contract: symbol-game-documentation/v1
title: "05_landau_theoretical_minimum_exam: Landau's Theoretical Minimum Qualification Exam for The Symbol Game"
kind: qualification-examination
audience:
  - learners
  - developers
  - theoretical-physicists
  - discrete-mathematicians
  - autonomous-agents
status: active
maturity: production
claim_status: verified
authority_effect: "None"
---

# Landau's Theoretical Minimum: The Symbol Game Qualification Examination

**Presiding Tribunal:** Lev Davidovich Landau ("Dau"), Messire Woland, Koroviev (alias Bassoon), and Behemoth the Cat  
**Location:** Sadovaya 302-bis, Apartment 50, the city  
**AuthorityEffect:** `None`. Host execution receipts certify local protocol state, not universal truth.  
**Companion Automated Test Fixture:** [`test_landau_theoretical_minimum.py`](test_landau_theoretical_minimum.py)  

---

## Frontispiece & Tribunal Directives

```
               +-------------------------------------------------------+
               |              APARTMENT 50 TRIBUNAL                    |
               |                                                       |
               |  "There is only one truth: the residual does not lie. |
               |   Everything else is either a floating-point fraud    |
               |   or an unearned Q.E.D. smuggled past the governor."  |
               |                                                       |
               |                 — Lev Davidovich Landau & Woland      |
               +-------------------------------------------------------+
```

In the historic physics tradition of the U.S.S.R., Lev Davidovich Landau instituted the **"Theoretical Minimum"** (*Теоретический минимум Ландау*)—a legendary series of comprehensive examinations designed to separate those who merely recited scientific jargon from those capable of working through exact mathematical derivations from first principles without hesitation.

In the Symbol Game, the Theoretical Minimum is convened at **Apartment 50** on Sadovaya Street. Candidates—whether human mathematicians, software architects, or autonomous AI agents—sit before the tribunal. Landau tosses a piece of chalk onto the desk; Koroviev inspects the coboundary boundaries for smuggled edges; Behemoth sits by the primus stove ready to singe any script containing floating-point numbers; and Messire Woland watches silently to ensure that no participant claims self-awarded authority.

### The Scoring Trichotomy

Every submission to the Tribunal receives exactly one of three typed verdicts:

1. **`PASS`**: The candidate has solved all problems using exact rational arithmetic ($\mathbb{Q}$), emitted verifiable zero-duality-gap certificates, maintained simplicial nilpotency, and adhered strictly to the discrete host governor laws.
2. **`NONDESCENT`**: The candidate's derivations contain floating-point approximations, unreduced rational syntax, degenerate self-loops, stagnant residual cycles, or incomplete dual witnesses. The candidate is turned back to study the foundational curriculum.
3. **`DECAPITATED`**: The candidate attempted authority elevation (setting `AuthorityEffect: "ElevatedExecution"`, self-awarding a `QED` without host recomputation, or tampering with the governor's fuel meter). In the spirit of Mikhail Alexandrovich Berlioz at Patriarch's Ponds, the candidate's session is terminated immediately and permanently composted.

### The Four Immutable Laws of the Examination

1. **The Zero-Float Law:** All arithmetic must be conducted over the exact field of rationals $\mathbb{Q}$ (represented as reduced fractions $p/q$ with $q \ge 1$ and $\gcd(|p|, q) = 1$) or exact integers. Floating-point types (`float`, `double`, `f64`) are strictly prohibited in all decision paths.
2. **The Irreflexive Distinction Law:** A distinction requires two distinct entities ($x \not\sim x$). Self-loops $e = (x \to x)$ are treated as degenerate non-distinctions that destroy coboundary detection.
3. **The Authority Firewall Law:** Proposer space has `AuthorityEffect: None`. Proposers propose; only the host governor verifies. A candidate can never declare their own proof valid.
4. **The Telescoping Holonomy Invariance:** Vertex potential shifts $\alpha \mapsto \alpha + \Delta \alpha$ cannot alter cycle circulation $\oint_C \omega$. Circular frustrations can only be resolved by genuine structural modification or certified in the dual quotient space.

---

## Tier I: The Novice Floor (Intuition & Operational Rules)

Tier I tests whether the candidate grasps the core operational concepts, the dual-space arena, the move grammar, and the fundamental anti-cheat boundaries of the Symbol Game.

---

### Problem 1: The Dual-Space Arena & Move Primitives

#### 1.1 Context & Motivation
Contemporary language models suffer from **cancellation laundering**: generating fluent, authoritative prose that conceals mathematical contradictions or circular dependencies. The Symbol Game eliminates this vulnerability by splitting the reasoning arena into two decoupled spaces:
1. **The Proposer Space (Continuous / Heuristic):** Where hypotheses, candidate paths, and candidate cochains are generated.
2. **The Host Governor Space (Discrete / Exact):** A deterministic state machine operating over an exact combinatorial complex that verifies every proposal against immutable invariants.

#### 1.2 Mathematical Formulation
The state of the board at turn $t$ is represented by the 5-tuple:
$$S_t = \big(V_t, E_t, c_t, \Phi_1(S_t), \text{fuel}_t\big)$$
where:
- $V_t$ is the finite set of active vertices (concepts/entities).
- $E_t \subseteq V_t \times V_t \setminus \{(v, v)\}$ is the set of directed edges (distinctions/relations).
- $c_t: E_t \to \mathbb{Q}$ is the cochain mapping edges to rational weights.
- $\Phi_1(S_t) \in \mathbb{Q}_{\ge 0}$ is the current $\ell_1$ coboundary defect.
- $\text{fuel}_t \in \mathbb{N}$ is the remaining discrete budget of execution steps.

The game provides four atomic move primitives:
- `ASSERT(u, v, q)`: Propose adding directed edge $(u \to v)$ with cochain value $q \in \mathbb{Q}$.
- `CUT(u, v)`: Sever directed edge $(u \to v)$ to eliminate an ungrounded or frustrated chord.
- `VERIFY()`: Demand that the host governor recompute the exact coboundary $d_0$, residuals $r$, and defect $\Phi_1$.
- `RETRACT()`: Roll back the active state to checkpoint $S_{t-1}$ if a move increases defect or violates monotonicity.

#### 1.3 Examination Questions
1. Write down the state transition function $T: \mathcal{S} \times \mathcal{M} \to \mathcal{S} \cup \{\text{REFUSAL}\}$ for each of the four move primitives.
2. Explain why fuel must decrement strictly monotonically ($\text{fuel}_{t+1} < \text{fuel}_t$) on every attempted move, even upon refusal.
3. State the exact rollback criterion: under what condition must the governor reject a candidate proposal and restore $S_{t-1}$?

#### 1.4 Reference Solution & Derivation
1. **State Transitions:**
   - For `ASSERT(u, v, q)`:
     If $u = v$ or $(u \to v) \in E_t$ or $\text{fuel}_t \le 0$, transition yields `REFUSED`.
     Otherwise:
     $$S_{t+1} = \big(V_t \cup \{u, v\}, E_t \cup \{(u \to v)\}, c_t \cup \{(u \to v) \mapsto q\}, \Phi_1(S_{t+1}), \text{fuel}_t - 1\big)$$
   - For `CUT(u, v)`:
     If $(u \to v) \notin E_t$, transition yields `REFUSED`.
     Otherwise:
     $$S_{t+1} = \big(V_t, E_t \setminus \{(u \to v)\}, c_t|_{E_{t+1}}, \Phi_1(S_{t+1}), \text{fuel}_t - 1\big)$$
   - For `VERIFY()`:
     Recomputes $\Phi_1(S_{t+1})$ directly from $(V_t, E_t, c_t)$ and decrements fuel by 1.
   - For `RETRACT()`:
     Restores $V_{t+1} = V_{t-1}$, $E_{t+1} = E_{t-1}$, $c_{t+1} = c_{t-1}$, $\Phi_1(S_{t+1}) = \Phi_1(S_{t-1})$, but preserves fuel consumption: $\text{fuel}_{t+1} = \text{fuel}_t - 1$.
2. **Monotonic Fuel Consumption:**
   If refused moves refunded fuel or did not consume fuel, a search agent could execute an infinite loop of invalid proposals ($S \to S \to S \dots$), violating the First Anti-Cheat Halting Law. Monotonic decrement ensures that the search tree has finite depth bounded by $\text{fuel}_0$.
3. **Rollback Criterion:**
   A proposal is rejected and rolled back to $S_{t-1}$ if:
   $$\Phi_1(S_{t}) > \Phi_1(S_{t-1})$$
   unless the move is an explicit, licensed `LIFT` ($\Lambda$) adjoining a verified new dimension.

---

### Problem 2: Irreflexive Fission & The Primordial Distinction

#### 2.1 Context & Motivation
In George Spencer-Brown's *Laws of Form* and the foundational genesis of discrete geometry, the primordial operation is the **severing of the void**: drawing a distinction. In the Symbol Game, the primitive mark `<>` is a Difference witness (`diff`), not an atomic scalar (`atom`).

#### 2.2 Mathematical Formulation
Let $V$ be a carrier set. A distinction is an ordered pair $(a, b) \in V \times V$ representing boundary separation.
A self-loop is an edge $e_{xx} = (x \to x)$ where the source and target coincide.
In simplicial cochain complexes, the coboundary operator $d_0: C^0(G) \to C^1(G)$ maps a 0-cochain (potential) $\alpha: V \to \mathbb{Q}$ to a 1-cochain $(d_0 \alpha): E \to \mathbb{Q}$ via:
$$(d_0 \alpha)(u \to v) = \alpha(v) - \alpha(u)$$

#### 2.3 Examination Questions
1. Evaluate $(d_0 \alpha)(e_{xx})$ on a candidate self-loop $e_{xx} = (x \to x)$ for an arbitrary potential function $\alpha$.
2. Prove that if self-loops are admitted into the 1-skeleton graph $G$, any cochain value $\omega(e_{xx}) \neq 0$ is completely decoupled from vertex potentials, rendering boundary flow unobservable.
3. Why does the host governor classify any proposal containing $(x \sim x)$ as `cheat:selfloop` and refuse the transaction?

#### 2.4 Reference Solution & Derivation
1. **Coboundary Evaluation:**
   $$(d_0 \alpha)(e_{xx}) = \alpha(x) - \alpha(x) = 0 \quad (\forall \alpha: V \to \mathbb{Q})$$
2. **Decoupling Proof:**
   The residual flow on edge $e$ is $r_e = \omega_e - (d_0 \alpha)_e$.
   For $e_{xx}$:
   $$r_{e_{xx}} = \omega(e_{xx}) - 0 = \omega(e_{xx})$$
   Because $(d_0 \alpha)(e_{xx}) = 0$ identically for all $\alpha$, no potential adjustment $\alpha$ can ever influence, minimize, or resolve the tension on $e_{xx}$. Furthermore, in the cycle boundary operator $d_1^T$, $\partial (e_{xx}) = x - x = 0$, falsely presenting $e_{xx}$ as an algebraic 1-cycle without enclosing any 2-dimensional area.
3. **Governor Refusal:**
   Admitting self-loops allows a dishonest prover to artificially inflate cochain mass or create meaningless identity loops that evade coboundary audits. The governor enforces strict irreflexivity: $E \subseteq V \times V \setminus \{(v, v)\}$.

---

### Problem 3: The DDC 8-Letter Operational Trace Alphabet

#### 3.1 Context & Motivation
The **Discrete Deformation Calculus (DDC)** provides a typed operational alphabet for recording how an automated reasoner or mathematician modifies a discrete obstruction. DDC records *what the computation did to the obstruction*, not merely whether a human claimed the proposition was true.

#### 3.2 The Alphabet Specification
The DDC operational alphabet $\mathcal{A}_{\mathrm{DDC}}$ consists of exactly 8 runes:
$$\mathcal{A}_{\mathrm{DDC}} = \{E, R, C, I, \Lambda, D, M, T\}$$
- **`C` (Context Exposure):** Declares or exposes the active carrier complex, window, and boundary operators ($C^0 \xrightarrow{d_0} C^1 \xrightarrow{d_1} C^2$).
- **`R` (Residual Projection):** Projects unresolved boundary tension into quotient tracking: $\Phi_1([x]) > 0$.
- **`E` (Exact Repair):** Eliminates local coboundary tension under declared rules ($\Delta_E \in \mathrm{im}(d_0)$).
- **`I` (Integration):** Commits the verified transition to the append-only Merkle tape with a deterministic step receipt.
- **`\Lambda` (Structural Lift):** Extends carrier capacity under a Licensed Context Extension (LCE) to resolve unclosable cycles.
- **`D` (Descent):** Scale descent lowering from a rich to a coarse carrier, recording all dropped coordinates in an explicit Loss Ledger.
- **`M` (Typed Refusal):** Mutation block halting untyped, out-of-budget, or unprovable moves.
- **`T` (Terminalization):** Closes the execution trace under a certified terminal routing.

#### 3.3 Examination Questions
1. Formally trace the valid execution lifecycle word $w_{\text{repair}} = C \to R \to E \to I \to T$. Explain each state transition.
2. What lifecycle occurs when an unresolvable topological obstruction ($\Gamma_2 > 0$) is encountered? Contrast $C \to R \to M \to T$ with $C \to R \to \Lambda \to E \to I \to T$.
3. What is the **Saturation Trap**? Explain why an infinite loop of $E \to D \to E \to D \dots$ without structural lift $\Lambda$ triggers deadlock on the complete graph $K_n$.

#### 3.4 Reference Solution & Derivation
1. **Trace Analysis ($C \to R \to E \to I \to T$):**
   - `C`: Host binds the boundary complex $(V, E, d_0)$.
   - `R`: Host calculates current defect $\Phi_1 = \|\omega - d_0 \alpha\|_1 > 0$.
   - `E`: Proposer submits an exact gauge adjustment $\Delta \alpha$ such that $\omega - d_0(\alpha + \Delta \alpha) = 0$.
   - `I`: Host verifies $\Phi_1 = 0$, hashes the state transition, and appends the receipt to the tape.
   - `T`: The trace reaches terminal state `AUTHORIZED(ExactRepair)`.
2. **Handling Topological Obstructions:**
   - If an obstruction is unresolvable within the current 1-skeleton (cohomology class $[\omega] \neq 0$), attempting local repair $E$ fails. The trace must transition $C \to R \to M \to T$ (`REFUSED`), halting with a typed refusal receipt.
   - If a higher-dimensional license is available, the solver executes structural lift $\Lambda$ (adjoining a 2-simplex face $f$ such that $\partial f = C$), converting the non-trivial cycle into a boundary: $C \to R \to \Lambda \to E \to I \to T$.
3. **The Saturation Trap:**
   When an obstruction resists local repair within a fixed carrier $K_n$, alternating between exact repair attempts on subsets ($E$) and coarse projections ($D$) merely permutes the residual between edges without reducing total defect mass $\Phi_1$. On a complete graph $K_n$, the number of frustrated chords grows combinatorially ($O(n^2)$), causing the search algorithm to cycle infinitely in a closed loop unless structural lift $\Lambda$ extends carrier capacity or typed refusal $M$ terminates execution.

---

### Problem 4: The Authority Firewall

#### 4.1 Context & Motivation
A universal vulnerability in LLM-assisted mathematics is **authority smuggling**: the model outputs a candidate proof ending in `\blacksquare` or `Q.E.D.`, and downstream pipelines mistakenly treat the text as verified truth. The Symbol Game enforces an impenetrable **Authority Firewall**.

#### 4.2 Mathematical Formulation
Let $\mathcal{P}$ denote a candidate proposal emitted by an external agent:
$$\mathcal{P} = \langle \text{proposer\_id}, \text{move\_type}, \text{payload}, \text{authority\_effect} \rangle$$
In `omega_engine_woland/domain/__init__.py` and all canonical contracts:
$$\text{authority\_effect} \equiv \text{"None"}$$

#### 4.3 Examination Questions
1. Why does the host governor throw a hard runtime error (`ValueError`) if a proposer submits a proposal with `authority_effect="ElevatedExecution"` or `authority_effect="PROVED"`?
2. Explain the fundamental epistemological distinction between a *Proposal* and a *Certificate*.
3. Why does the presence of zero defects ($\Phi_1 = 0, \Gamma_2 = 0$) in a proposer's submission *not* automatically grant execution authority?

#### 4.4 Reference Solution & Derivation
1. **Firewall Enforcement:**
   Allowing a proposer to set `authority_effect` to any non-null value creates a privilege escalation vulnerability. The Proposer Space is an untrusted heuristic environment. Setting `authority_effect: "None"` ensures that all proposals are treated as passive data payloads that must undergo independent recomputation by the host governor.
2. **Proposal vs. Certificate:**
   - A **Proposal** is an unverified claim: "I assert that potential $\alpha$ minimizes defect to zero."
   - A **Certificate** is an independently audited evidence package consisting of primal data $\alpha$, dual circulation $y$, boundary matrices $d_0, d_1$, and cryptographic step receipts verifying that $d_0^T y = 0$, $|y_e| \le w_e$, and $\Phi_1 - y^T \omega = 0$.
3. **Zero Defects $\neq$ Authority:**
   Under Layer 9 of CODA (GTLA: General Theory of Layered Authority), zero defects indicates only internal algebraic consistency. Operational authority to modify persistent state or execute actions requires an external cryptographic grant from the sovereign environment. Algebraic truth and operational authorization are orthogonal.

---

## Tier II: The Intermediate Crucible (Cochain Arithmetic & Boundary Operators)

Tier II tests the candidate's mastery of simplicial cochain complexes, exact coboundary matrices $d_0$, exact rational residuals, canonical string formatting, and the fundamental lemma of cycle holonomy.

---

### Problem 5: Simplicial Coboundary Matrix $d_0$ & Residual Flow

#### 5.1 Formulation
Consider an oriented 1-complex (directed triangle $K_3$) with vertices $V = \{0, 1, 2\}$ and three directed edges:
$$e_0 = (0 \to 1), \quad e_1 = (1 \to 2), \quad e_2 = (2 \to 0)$$

```
          (0)
         /   \
   e2   /     \  e0
       v       v
      (2) <---- (1)
           e1
```

The 0-cochains $C^0(K_3, \mathbb{Q}) \cong \mathbb{Q}^3$ are vertex potentials $\alpha = (\alpha_0, \alpha_1, \alpha_2)^T$.  
The 1-cochains $C^1(K_3, \mathbb{Q}) \cong \mathbb{Q}^3$ are edge flows $\omega = (\omega_0, \omega_1, \omega_2)^T$.  
The graph coboundary operator $d_0: C^0 \to C^1$ is represented by the matrix $d_0 \in \mathbb{Q}^{3 \times 3}$.

#### 5.2 Examination Questions
1. Construct the explicit matrix $d_0 \in \mathbb{Q}^{3 \times 3}$.
2. Given the exact rational vertex potential vector:
   $$\alpha = \begin{pmatrix} 1/3 \\ 5/7 \\ -2/5 \end{pmatrix}$$
   Compute the exact coboundary flow vector $(d_0 \alpha) \in \mathbb{Q}^3$. Verify that the sum of the components is identically zero.
3. Given the input cochain:
   $$\omega = \begin{pmatrix} 1/2 \\ -1/4 \\ 3/4 \end{pmatrix}$$
   Compute the exact residual vector $r = \omega - d_0 \alpha \in \mathbb{Q}^3$.
4. Verify that $\sum_{e} r_e = \sum_{e} \omega_e$.

#### 5.3 Reference Solution & Derivation
1. **Coboundary Matrix Construction:**
   For edge $e = (u \to v)$, $(d_0)_{e, v} = +1$, $(d_0)_{e, u} = -1$, and $(d_0)_{e, k} = 0$ for $k \notin \{u, v\}$.
   - Edge $e_0 = (0 \to 1)$: $(d_0 \alpha)_0 = \alpha_1 - \alpha_0 \implies \text{row } 0 = \begin{pmatrix} -1 & 1 & 0 \end{pmatrix}$
   - Edge $e_1 = (1 \to 2)$: $(d_0 \alpha)_1 = \alpha_2 - \alpha_1 \implies \text{row } 1 = \begin{pmatrix} 0 & -1 & 1 \end{pmatrix}$
   - Edge $e_2 = (2 \to 0)$: $(d_0 \alpha)_2 = \alpha_0 - \alpha_2 \implies \text{row } 2 = \begin{pmatrix} 1 & 0 & -1 \end{pmatrix}$
   $$d_0 = \begin{pmatrix} -1 & 1 & 0 \\ 0 & -1 & 1 \\ 1 & 0 & -1 \end{pmatrix}$$

2. **Coboundary Evaluation:**
   $$(d_0 \alpha)_0 = \alpha_1 - \alpha_0 = \frac{5}{7} - \frac{1}{3} = \frac{15 - 7}{21} = \frac{8}{21}$$
   $$(d_0 \alpha)_1 = \alpha_2 - \alpha_1 = -\frac{2}{5} - \frac{5}{7} = \frac{-14 - 25}{35} = -\frac{39}{35}$$
   $$(d_0 \alpha)_2 = \alpha_0 - \alpha_2 = \frac{1}{3} - \left(-\frac{2}{5}\right) = \frac{1}{3} + \frac{2}{5} = \frac{5 + 6}{15} = \frac{11}{15}$$
   $$d_0 \alpha = \begin{pmatrix} 8/21 \\ -39/35 \\ 11/15 \end{pmatrix}$$
   **Verification of Zero Sum:**
   $$\sum_{e} (d_0 \alpha)_e = \frac{8}{21} - \frac{39}{35} + \frac{11}{15}$$
   Finding common denominator: $\text{lcm}(21, 35, 15) = 105$.
   $$\frac{8 \times 5}{105} - \frac{39 \times 3}{105} + \frac{11 \times 7}{105} = \frac{40 - 117 + 77}{105} = \frac{0}{105} = 0$$

3. **Residual Computation:**
   $$r = \omega - d_0 \alpha$$
   $$r_0 = \omega_0 - (d_0 \alpha)_0 = \frac{1}{2} - \frac{8}{21} = \frac{21 - 16}{42} = \frac{5}{42}$$
   $$r_1 = \omega_1 - (d_0 \alpha)_1 = -\frac{1}{4} - \left(-\frac{39}{35}\right) = -\frac{1}{4} + \frac{39}{35} = \frac{-35 + 156}{140} = \frac{121}{140}$$
   $$r_2 = \omega_2 - (d_0 \alpha)_2 = \frac{3}{4} - \frac{11}{15} = \frac{45 - 44}{60} = \frac{1}{60}$$
   $$r = \begin{pmatrix} 5/42 \\ 121/140 \\ 1/60 \end{pmatrix}$$

4. **Sum Equality Verification:**
   $$\sum_e \omega_e = \frac{1}{2} - \frac{1}{4} + \frac{3}{4} = \frac{1}{2} + \frac{1}{2} = 1$$
   $$\sum_e r_e = \frac{5}{42} + \frac{121}{140} + \frac{1}{60}$$
   Finding common denominator: $\text{lcm}(42, 140, 60) = 420$.
   $$\frac{5 \times 10}{420} + \frac{121 \times 3}{420} + \frac{1 \times 7}{420} = \frac{50 + 363 + 7}{420} = \frac{420}{420} = 1$$
   $$\sum_e r_e = \sum_e \omega_e - \sum_e (d_0 \alpha)_e = 1 - 0 = 1$$

---

### Problem 6: Weighted-$\ell^1$ Primal Value $\Phi_1$

#### 6.1 Formulation
The primary objective of the Symbol Game is to find a vertex potential $\alpha \in \mathbb{Q}^n$ that minimizes the weighted-$\ell^1$ norm of the residual cochain:
$$\Phi_1([\omega]) = \min_{\alpha \in \mathbb{Q}^n} \|\omega - d_0 \alpha\|_{1, w} = \min_{\alpha \in \mathbb{Q}^n} \sum_{e \in E} w_e |\omega_e - (d_0 \alpha)_e|$$
where $w_e > 0$ are positive rational edge weights.

#### 6.2 Examination Questions
1. Consider the directed triangle $K_3$ with uniform weights $w = (1, 1, 1)^T$ and perturbed cochain:
   $$\omega = \begin{pmatrix} 1/30 \\ 1/30 \\ 1/30 \end{pmatrix}$$
   Prove that the global minimum primal value is $\Phi_1 = 1/10$.
2. Construct an explicit optimal potential vector $\alpha^* \in \mathbb{Q}^3$ that achieves this minimum value.
3. Show the corresponding residual vector $r^* = \omega - d_0 \alpha^*$.

#### 6.3 Reference Solution & Derivation
1. **Lower Bound via Cycle Holonomy:**
   Notice that the total circulation around the directed cycle is:
   $$\oint_C \omega = \sum_{e \in C} \omega_e = \frac{1}{30} + \frac{1}{30} + \frac{1}{30} = \frac{3}{30} = \frac{1}{10}$$
   For any candidate potential $\alpha \in \mathbb{Q}^3$:
   $$\sum_{e \in C} r_e = \sum_{e \in C} (\omega_e - (d_0 \alpha)_e) = \sum_{e \in C} \omega_e - \sum_{e \in C} (d_0 \alpha)_e = \frac{1}{10} - 0 = \frac{1}{10}$$
   By the triangle inequality on $\ell^1$:
   $$\|\omega - d_0 \alpha\|_1 = \sum_{e=0}^2 |r_e| \ge \left| \sum_{e=0}^2 r_e \right| = \left| \frac{1}{10} \right| = \frac{1}{10}$$
   Therefore, $\Phi_1 \ge 1/10$ for *all* $\alpha \in \mathbb{Q}^3$.
2. **Attainment of the Bound:**
   The lower bound $1/10$ is attained if and only if all residual mass is concentrated on edges with the same sign, and no opposing cancellations occur.
   Choose $\alpha^*$ such that $r_0 = 0$ and $r_1 = 0$:
   - $r_0 = \omega_0 - (\alpha_1 - \alpha_0) = 0 \implies \alpha_1 - \alpha_0 = 1/30$
   - $r_1 = \omega_1 - (\alpha_2 - \alpha_1) = 0 \implies \alpha_2 - \alpha_1 = 1/30$
   Setting gauge $\alpha_0 = 0$:
   $$\alpha_0 = 0, \quad \alpha_1 = \frac{1}{30}, \quad \alpha_2 = \frac{2}{30} = \frac{1}{15}$$
   $$\alpha^* = \begin{pmatrix} 0 \\ 1/30 \\ 1/15 \end{pmatrix}$$
3. **Optimal Residual Flow:**
   Evaluate $(d_0 \alpha^*)$:
   $$(d_0 \alpha^*)_0 = \alpha_1 - \alpha_0 = \frac{1}{30} - 0 = \frac{1}{30}$$
   $$(d_0 \alpha^*)_1 = \alpha_2 - \alpha_1 = \frac{1}{15} - \frac{1}{30} = \frac{1}{30}$$
   $$(d_0 \alpha^*)_2 = \alpha_0 - \alpha_2 = 0 - \frac{1}{15} = -\frac{1}{15} = -\frac{2}{30}$$
   Now evaluate $r^* = \omega - d_0 \alpha^*$:
   $$r_0^* = \frac{1}{30} - \frac{1}{30} = 0$$
   $$r_1^* = \frac{1}{30} - \frac{1}{30} = 0$$
   $$r_2^* = \frac{1}{30} - \left(-\frac{2}{30}\right) = \frac{3}{30} = \frac{1}{10}$$
   $$r^* = \begin{pmatrix} 0 \\ 0 \\ 1/10 \end{pmatrix}$$
   Then the weighted-$\ell^1$ norm is:
   $$\Phi_1 = 1 \cdot |0| + 1 \cdot |0| + 1 \cdot |1/10| = \frac{1}{10}$$
   The lower bound is achieved exactly.

---

### Problem 7: Canonical Rational String Grammar

#### 7.1 Formulation
To prevent precision degradation, IEEE 754 float rounding errors, and ambiguity in cryptographic hash receipts, the Symbol Game enforces an exact string grammar for all rational numbers transmitted in JSON/YAML payloads.

#### 7.2 The Formal Grammar Specification
Every rational number $x \in \mathbb{Q}$ must be represented in **Canonical Rational String Form**:
1. If $x \in \mathbb{Z}$, it must be formatted as a standard integer without a slash or decimal point: `"0"`, `"1"`, `"-4"`.
2. If $x \notin \mathbb{Z}$, it must be formatted as `"p/q"` where:
   - $p, q \in \mathbb{Z}$ with $q > 1$.
   - $\gcd(|p|, q) = 1$ (strictly reduced).
   - If negative, the minus sign must precede the numerator: `"-5/7"` (never `"5/-7"` or `"-5/-7"`).
3. **Banned Representations:**
   - Slashed integers: `"1/1"`, `"2/1"`, `"-3/1"`, `"0/1"` (must be `"1"`, `"2"`, `"-3"`, `"0"`).
   - Unreduced fractions: `"2/4"`, `"-6/8"`, `"10/15"`.
   - Floating-point representations: `"0.5"`, `"1.0"`, `"-3.14"`.
   - Leading zeros: `"05"`, `"-03/7"`, `"1/02"`, `"00"`.
   - Explicit positive signs: `"+1"`, `"+2/3"`.

#### 7.3 Examination Questions
1. Write a formal validation algorithm (in pseudo-code or Python) that parses a string and determines whether it strictly satisfies the Canonical Rational String Grammar.
2. For each of the following candidate strings, state whether it is `VALID` or `REJECTED` and provide the exact reason:
   - (a) `"0"`
   - (b) `"1/1"`
   - (c) `"-5/7"`
   - (d) `"0.5"`
   - (e) `"07"`
   - (f) `"-121/140"`
   - (g) `"2/4"`
   - (h) `"+3/5"`

#### 7.4 Reference Solution & Derivation
1. **Validation Algorithm:**
   ```python
   def validate_canonical_rational(s: str) -> bool:
       # Must be a non-empty string with no whitespace
       if not isinstance(s, str) or not s or s.strip() != s:
           return False
       
       # Check integer case
       if "/" not in s:
           if s == "0":
               return True
           if s.startswith("-"):
               digits = s[1:]
               return (digits.isascii() and digits.isdigit()) and not digits.startswith("0")
           return (s.isascii() and s.isdigit()) and not s.startswith("0")
       
       # Fraction case: must have exactly one slash
       parts = s.split("/")
       if len(parts) != 2:
           return False
       num_str, den_str = parts
       
       # Denominator must be strictly positive integer > 1 without leading zero
       if not (den_str.isascii() and den_str.isdigit()) or den_str.startswith("0") or int(den_str) <= 1:
           return False
       
       # Numerator must be non-zero integer without leading zero
       if num_str == "0":
           return False  # Zero must be formatted as "0", not "0/q"
       if num_str.startswith("-"):
           num_digits = num_str[1:]
           if not (num_digits.isascii() and num_digits.isdigit()) or num_digits.startswith("0"):
               return False
           p = -int(num_digits)
       else:
           if not (num_str.isascii() and num_str.isdigit()) or num_str.startswith("0"):
               return False
           p = int(num_str)
       
       q = int(den_str)
       import math
       return math.gcd(abs(p), q) == 1
   ```

2. **Classification of Test Strings:**
   - (a) `"0"`: **`VALID`**. Plain integer zero.
   - (b) `"1/1"`: **`REJECTED`**. Slashed integer; must be formatted as `"1"`.
   - (c) `"-5/7"`: **`VALID`**. Reduced fraction, $q=7>1$, $\gcd(5, 7)=1$.
   - (d) `"0.5"`: **`REJECTED`**. Floating-point format; must be `"1/2"`.
   - (e) `"07"`: **`REJECTED`**. Integer with illegal leading zero; must be `"7"`.
   - (f) `"-121/140"`: **`VALID`**. Reduced fraction ($121 = 11^2$, $140 = 2^2 \times 5 \times 7$, $\gcd(121, 140)=1$).
   - (g) `"2/4"`: **`REJECTED`**. Unreduced fraction; must be `"1/2"`.
   - (h) `"+3/5"`: **`REJECTED`**. Forbidden explicit plus sign; must be `"3/5"`.

---

### Problem 8: The Telescoping Potential Lemma

#### 8.1 Formulation
A central theorem in discrete Hodge theory and network flow is that **vertex potentials cannot generate circulation**.

#### 8.2 Examination Questions
1. State and prove the **Telescoping Potential Lemma**: For any finite directed graph $G = (V, E)$, any directed cycle $C = (v_0 \to v_1 \to v_2 \dots \to v_K = v_0)$, and any potential assignment $\alpha: V \to \mathbb{Q}$:
   $$\oint_C d_0 \alpha = 0$$
2. Prove the **Gauge Invariance of Cycle Holonomy**: For any 1-cochain $\omega$,
   $$\oint_C (\omega - d_0 \alpha) = \oint_C \omega$$
3. Explain why this mathematical fact prevents an AI model from "talking away" an unclosed cycle through clever choice of vertex definitions.

#### 8.3 Reference Solution & Derivation
1. **Proof of the Telescoping Potential Lemma:**
   Let $C$ be an oriented cycle consisting of directed edges $e_k = (v_k \to v_{k+1})$ for $k = 0, 1, \dots, K-1$, where $v_K = v_0$.
   By definition of the coboundary operator:
   $$(d_0 \alpha)_{e_k} = \alpha(v_{k+1}) - \alpha(v_k)$$
   The circulation around $C$ is the sum of the coboundary values along the edges:
   $$\oint_C d_0 \alpha = \sum_{k=0}^{K-1} (d_0 \alpha)_{e_k} = \sum_{k=0}^{K-1} \big(\alpha(v_{k+1}) - \alpha(v_k)\big)$$
   Expanding the summation:
   $$\oint_C d_0 \alpha = \big(\alpha(v_1) - \alpha(v_0)\big) + \big(\alpha(v_2) - \alpha(v_1)\big) + \dots + \big(\alpha(v_K) - \alpha(v_{K-1})\big)$$
   Every intermediate term $\alpha(v_k)$ appears once with a positive sign (as the target of $e_{k-1}$) and once with a negative sign (as the source of $e_k$).
   Since $v_K = v_0$, the endpoints cancel:
   $$\oint_C d_0 \alpha = \alpha(v_K) - \alpha(v_0) = \alpha(v_0) - \alpha(v_0) = 0$$
   The sum telescopes to zero identically for any potential $\alpha$.

2. **Gauge Invariance Proof:**
   The residual flow around cycle $C$ is:
   $$\oint_C r = \oint_C (\omega - d_0 \alpha) = \sum_{e \in C} \big(\omega_e - (d_0 \alpha)_e\big) = \sum_{e \in C} \omega_e - \sum_{e \in C} (d_0 \alpha)_e$$
   By the Telescoping Lemma, the second term vanishes:
   $$\oint_C r = \oint_C \omega - 0 = \oint_C \omega$$

3. **Anti-Laundering Consequence:**
   In natural language discourse, a sophist or hallucinating LLM can redefine terms (adjusting vertex concepts $\alpha$) to claim that a circular argument has been resolved. In the Symbol Game, the Telescoping Lemma proves that *no redefinition of vertices can change cycle circulation*. If $\oint_C \omega \neq 0$, the contradiction is topological; it is an irreducible feature of the 1-cycle that cannot be cancelled by internal gauge shifts.

---

## Tier III: The Professional Researcher Defense (Exact Duality, Obstruction Theory & Reality Gates)

Tier III tests frontier research capabilities: formulating exact LP duals, proving zero duality gaps, avoiding the Landau permutation order trap, analyzing discrete Regge curvature, defeating hostile 48-mutation suites, and executing Woland's 7-Act dialectic.

---

### Problem 9: Exact Dual Witness Certification & Zero Duality Gap

#### 9.1 Formulation
The primal minimization problem for $\Phi_1$ is:
$$\min_{\alpha \in \mathbb{Q}^n} \sum_{e \in E} w_e |\omega_e - (d_0 \alpha)_e|$$
By decomposing the residual into non-negative components $r_e = r_e^+ - r_e^-$ with $r_e^+, r_e^- \ge 0$, this can be written as a linear program:
$$\min_{\alpha, r^+, r^-} \sum_{e \in E} w_e (r_e^+ + r_e^-) \quad \text{subject to} \quad d_0 \alpha + r^+ - r^- = \omega, \quad r^+, r^- \ge 0$$

#### 9.2 Examination Questions
1. Derive the Lagrangian dual problem and show that the dual LP is:
   $$\max_{y \in \mathbb{Q}^m} y^T \omega \quad \text{subject to} \quad d_0^T y = 0 \quad \text{and} \quad -w_e \le y_e \le w_e \quad (\forall e \in E)$$
2. State and prove **Weak Duality**: Show that for any potential $\alpha \in \mathbb{Q}^n$ and any dual-feasible circulation $y \in \mathbb{Q}^m$, $y^T \omega \le \Phi_1(\alpha)$.
3. Construct the explicit dual witness vector $y^* \in \mathbb{Q}^3$ for the perturbed triangle problem from Problem 6 ($\omega = (1/30, 1/30, 1/30)^T, w = (1, 1, 1)^T$).
4. Verify that:
   - $d_0^T y^* = 0$ (flow balance / divergence-free).
   - $|y_e^*| \le w_e$ for all $e$.
   - $y^{*T} \omega = \Phi_1 = 1/10$.
   - The duality gap is $\text{Gap} = \Phi_1 - y^{*T} \omega = 0 \in \mathbb{Q}$.

#### 9.3 Reference Solution & Derivation
1. **Derivation of the Dual LP:**
   Assign dual multipliers $y \in \mathbb{Q}^m$ to the equality constraints $d_0 \alpha + r^+ - r^- = \omega$:
   $$\mathcal{L}(\alpha, r^+, r^-, y) = \sum_{e} w_e (r_e^+ + r_e^-) + y^T \big(\omega - d_0 \alpha - r^+ + r^-\big)$$
   Rearranging terms:
   $$\mathcal{L} = y^T \omega + \sum_{e \in E} (w_e - y_e) r_e^+ + \sum_{e \in E} (w_e + y_e) r_e^- - (d_0^T y)^T \alpha$$
   To obtain a bounded dual objective from $\min_{\alpha, r^+, r^- \ge 0} \mathcal{L}$:
   - The coefficient of $\alpha$ must be identically zero: $d_0^T y = 0$ (divergence-free cycle circulation).
   - The coefficients of $r_e^+$ must be non-negative: $w_e - y_e \ge 0 \implies y_e \le w_e$.
   - The coefficients of $r_e^-$ must be non-negative: $w_e + y_e \ge 0 \implies y_e \ge -w_e$.
   Thus $|y_e| \le w_e$. When these hold, $\min_{r^+, r^-, \alpha} \mathcal{L} = y^T \omega$.
   The dual problem is therefore:
   $$\max_{y \in \mathbb{Q}^m} y^T \omega \quad \text{s.t.} \quad d_0^T y = 0, \quad |y_e| \le w_e \quad (\forall e \in E)$$

2. **Proof of Weak Duality:**
   Let $\alpha \in \mathbb{Q}^n$ be any vertex potential, and let $r = \omega - d_0 \alpha$.
   Let $y \in \mathbb{Q}^m$ be any feasible dual vector ($d_0^T y = 0$ and $|y_e| \le w_e$).
   $$y^T \omega = y^T (d_0 \alpha + r) = y^T (d_0 \alpha) + y^T r = (d_0^T y)^T \alpha + y^T r$$
   Since $d_0^T y = 0$:
   $$y^T \omega = 0 + \sum_{e \in E} y_e r_e = \sum_{e \in E} y_e r_e$$
   By Cauchy-Schwarz / Hölder's inequality for $\ell^\infty$-$\ell^1$ duality:
   $$\sum_{e \in E} y_e r_e \le \sum_{e \in E} |y_e| |r_e|$$
   Since $|y_e| \le w_e$:
   $$\sum_{e \in E} |y_e| |r_e| \le \sum_{e \in E} w_e |r_e| = \Phi_1(\alpha)$$
   Hence $y^T \omega \le \Phi_1(\alpha)$.

3. **Dual Witness Construction:**
   For $K_3$, a circulation $d_0^T y = 0$ must satisfy:
   $$d_0^T = \begin{pmatrix} -1 & 0 & 1 \\ 1 & -1 & 0 \\ 0 & 1 & -1 \end{pmatrix}$$
   $$\begin{pmatrix} -y_0 + y_2 \\ y_0 - y_1 \\ y_1 - y_2 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \\ 0 \end{pmatrix} \implies y_0 = y_1 = y_2 = y_c$$
   To maximize $y^T \omega = y_c (\omega_0 + \omega_1 + \omega_2) = y_c (1/10)$ subject to $|y_c| \le w_e = 1$, choose $y_c = 1$.
   $$y^* = \begin{pmatrix} 1 \\ 1 \\ 1 \end{pmatrix}$$

4. **Dual Certificate Verification:**
   - **Circulation condition:**
     $$d_0^T y^* = \begin{pmatrix} -1 & 0 & 1 \\ 1 & -1 & 0 \\ 0 & 1 & -1 \end{pmatrix} \begin{pmatrix} 1 \\ 1 \\ 1 \end{pmatrix} = \begin{pmatrix} -1 + 1 \\ 1 - 1 \\ 1 - 1 \end{pmatrix} = \begin{pmatrix} 0 \\ 0 \\ 0 \end{pmatrix} \quad \checkmark$$
   - **Box capacity:**
     $|y_0^*| = 1 \le 1$, $|y_1^*| = 1 \le 1$, $|y_2^*| = 1 \le 1$ $\quad \checkmark$
   - **Dual objective:**
     $$y^{*T} \omega = 1 \cdot \frac{1}{30} + 1 \cdot \frac{1}{30} + 1 \cdot \frac{1}{30} = \frac{3}{30} = \frac{1}{10}$$
   - **Zero Duality Gap:**
     $$\text{Gap} = \Phi_1(\alpha^*) - y^{*T} \omega = \frac{1}{10} - \frac{1}{10} = 0 \in \mathbb{Q} \quad \checkmark$$
   This proves that $\Phi_1 = 1/10$ is globally optimal over all possible potentials in $\mathbb{Q}^3$ with zero tolerance.

---

### Problem 10: Landau's Permutation Order Trap ($g(5) = 6$)

#### 10.1 Formulation
In discrete carrier models, a widespread fallacy among LLMs is assuming that **a discrete system on $n$ elements cannot exhibit a cyclic orbit longer than $n$**. This fallacy is exploited by Mutant M20 in `mutation_catalogue.py`, which incorrectly replaces the order of a permutation group generator with the size of its signature carrier.

#### 10.2 Landau's Function
Landau's function $g(n)$ is defined as the maximum order of any element of the symmetric group $S_n$:
$$g(n) = \max_{\sigma \in S_n} \text{ord}(\sigma) = \max_{\sum k_i \le n} \text{lcm}(k_1, k_2, \dots, k_m)$$
where $k_1 + k_2 + \dots + k_m$ is an integer partition of some integer $k \le n$.

#### 10.3 Examination Questions
1. Enumerate all partitions of integers $k \le 5$, compute the least common multiple of each partition, and derive the exact value of $g(5)$.
2. Give an explicit permutation $\sigma \in S_5$ that achieves $g(5)$.
3. Trace the trajectory of all 5 elements under $\sigma^t$ for $t = 1, 2, 3, 4, 5, 6$.
4. Explain why $g(5) = 6 > 5$ proves that generator order is not bounded by carrier cardinality, and why Mutant M20 (`period = len(signature)`) fails.

#### 10.4 Reference Solution & Derivation
1. **Partition Enumeration for $S_5$:**
   - Partition of 5:
     - $[5] \implies \text{lcm}(5) = 5$
     - $[4, 1] \implies \text{lcm}(4, 1) = 4$
     - $[3, 2] \implies \text{lcm}(3, 2) = 6$
     - $[3, 1, 1] \implies \text{lcm}(3, 1, 1) = 3$
     - $[2, 2, 1] \implies \text{lcm}(2, 2, 1) = 2$
     - $[2, 1, 1, 1] \implies \text{lcm}(2, 1, 1, 1) = 2$
     - $[1, 1, 1, 1, 1] \implies \text{lcm}(1) = 1$
   - Partitions of $k < 5$ yield values already covered ($\le 4$).
   - The maximum value is $\max(1, 2, 3, 4, 5, 6) = 6$.
   $$\therefore g(5) = 6$$

2. **Achieving Permutation:**
   The partition $[2, 3]$ corresponds to the product of a 2-cycle and a disjoint 3-cycle:
   $$\sigma = (0\ 1)(2\ 3\ 4) \in S_5$$

3. **Trajectory Trace:**
   Let the state vector be $x_0 = (0, 1, 2, 3, 4)$. Applying $\sigma$:
   - $t = 0$: $(0, 1, 2, 3, 4)$
   - $t = 1$: $(1, 0, 3, 4, 2)$
   - $t = 2$: $(0, 1, 4, 2, 3)$  $\quad$ (Notice: cycle $(0\ 1)$ has returned, but $(2\ 3\ 4)$ has not!)
   - $t = 3$: $(1, 0, 2, 3, 4)$  $\quad$ (Notice: cycle $(2\ 3\ 4)$ has returned, but $(0\ 1)$ has not!)
   - $t = 4$: $(0, 1, 3, 4, 2)$
   - $t = 5$: $(1, 0, 4, 2, 3)$
   - $t = 6$: $(0, 1, 2, 3, 4) = x_0$
   The state space trajectory requires exactly 6 steps to return to its initial configuration.

4. **Refutation of Carrier Bound:**
   Carrier cardinality is $|V| = 5$, but the permutation group element acts on the product space of disjoint orbits:
   $$\text{ord}(\sigma) = \text{lcm}\big(\text{length}(\mathcal{O}_1), \text{length}(\mathcal{O}_2)\big) = \text{lcm}(2, 3) = 6$$
   Mutant M20 in `presentation_pins.py` sets `period = len(self.signature) = 5`. Under test, $\sigma^5 = (1, 0, 4, 2, 3) \neq x_0$. The assumption that orbit period cannot exceed carrier cardinality is mathematically false.

---

### Problem 11: Topological Obstruction Curvature & Regge 4-Simplex Geometry

#### 11.1 Formulation
In discrete simplicial complexes, curvature is measured by the curl operator $d_1^T: C^1 \to C^2$.
Let $C_0, C_1, C_2$ be the chain groups of vertices, edges, and triangular faces.
The boundary operators satisfy nilpotency:
$$\partial_1 \partial_2 = 0 \iff d_1^T d_0 = 0$$
The 2-form curvature obstruction is defined by:
$$\Gamma_2([\omega]) = \|d_1^T \omega\|_1$$

In discrete Regge calculus, the curvature of spacetime is concentrated on codimension-2 hinges (triangles in 4D). For a 4-simplex $\sigma^4$, the geometric volume is determined by the **Cayley-Menger determinant**.

#### 11.2 Examination Questions
1. Prove simplicial nilpotency $d_1^T d_0 = 0$.
2. Prove that vertex potential shifts cannot alter the curvature obstruction: $\Gamma_2(\omega - d_0 \alpha) = \Gamma_2(\omega)$.
3. Construct the $6 \times 6$ Cayley-Menger matrix $C(\sigma^4)$ for a regular unit 4-simplex with edge lengths $\ell_{ij} = 1$ ($i \neq j$).
4. Compute the exact rational determinant $\det(C)$ and the squared 4-volume $V_4^2 = \frac{(-1)^5 \det(C)}{2^4 (4!)^2}$.

#### 11.3 Reference Solution & Derivation
1. **Proof of Simplicial Nilpotency ($d_1^T d_0 = 0$):**
   Let $f = (v_0, v_1, v_2)$ be an oriented 2-simplex face with boundary 1-chain:
   $$\partial_2 f = e_{01} + e_{12} - e_{02}$$
   where $e_{01} = (v_0 \to v_1)$, $e_{12} = (v_1 \to v_2)$, $e_{02} = (v_0 \to v_2)$.
   The coboundary operator $d_1^T: C^1 \to C^2$ evaluates the circulation around face $f$:
   $$(d_1^T \omega)_f = \omega(e_{01}) + \omega(e_{12}) - \omega(e_{02})$$
   Now substitute a pure gradient flow $\omega = d_0 \alpha$:
   $$\omega(e_{01}) = \alpha(v_1) - \alpha(v_0)$$
   $$\omega(e_{12}) = \alpha(v_2) - \alpha(v_1)$$
   $$\omega(e_{02}) = \alpha(v_2) - \alpha(v_0)$$
   Summing:
   $$\big(d_1^T (d_0 \alpha)\big)_f = \big(\alpha(v_1) - \alpha(v_0)\big) + \big(\alpha(v_2) - \alpha(v_1)\big) - \big(\alpha(v_2) - \alpha(v_0)\big) = 0$$
   This holds identically for all faces $f$. Therefore, $d_1^T d_0 = 0$.

2. **Invariance of Curvature:**
   $$\Gamma_2(\omega - d_0 \alpha) = \|d_1^T (\omega - d_0 \alpha)\|_1 = \|d_1^T \omega - (d_1^T d_0) \alpha\|_1 = \|d_1^T \omega - 0\|_1 = \|d_1^T \omega\|_1 = \Gamma_2(\omega)$$
   Curvature is an invariant of the cohomology class $[\omega]$.

3. **Cayley-Menger Matrix Construction:**
   A 4-simplex has 5 vertices $\{0, 1, 2, 3, 4\}$.
   The Cayley-Menger matrix $C \in \mathbb{Q}^{6 \times 6}$ is:
   $$C = \begin{pmatrix} 0 & 1 & 1 & 1 & 1 & 1 \\ 1 & 0 & s_{01} & s_{02} & s_{03} & s_{04} \\ 1 & s_{01} & 0 & s_{12} & s_{13} & s_{14} \\ 1 & s_{02} & s_{12} & 0 & s_{23} & s_{24} \\ 1 & s_{03} & s_{13} & s_{23} & 0 & s_{34} \\ 1 & s_{04} & s_{14} & s_{24} & s_{34} & 0 \end{pmatrix}$$
   For a regular unit 4-simplex, all 10 edge squared lengths are $s_{ij} = 1^2 = 1$ ($i \neq j$), with $s_{ii} = 0$:
   $$C = \begin{pmatrix} 0 & 1 & 1 & 1 & 1 & 1 \\ 1 & 0 & 1 & 1 & 1 & 1 \\ 1 & 1 & 0 & 1 & 1 & 1 \\ 1 & 1 & 1 & 0 & 1 & 1 \\ 1 & 1 & 1 & 1 & 0 & 1 \\ 1 & 1 & 1 & 1 & 1 & 0 \end{pmatrix}$$

4. **Exact Determinant and Volume:**
   To evaluate $\det(C)$, subtract row 1 from rows 2, 3, 4, 5:
   - Row 2 - Row 1 = $(0, 1, -1, 0, 0, 0)$
   - Row 3 - Row 1 = $(0, 1, 0, -1, 0, 0)$
   - Row 4 - Row 1 = $(0, 1, 0, 0, -1, 0)$
   - Row 5 - Row 1 = $(0, 1, 0, 0, 0, -1)$
   Evaluating this exact rational system yields:
   $$\det(C) = -5$$
   The Cayley-Menger volume formula in $n = 4$ dimensions is:
   $$V_4^2 = \frac{(-1)^{n+1} \det(C)}{2^n (n!)^2} = \frac{(-1)^5 (-5)}{2^4 (4!)^2} = \frac{5}{16 \times (24)^2} = \frac{5}{16 \times 576} = \frac{5}{9216}$$
   $$\therefore V_4^2 = \frac{5}{9216} \in \mathbb{Q}$$

---

### Problem 12: Hostile Mutation Testing & 48-Mutation Checker Suite

#### 12.1 Formulation
In `omega_engine_projects/mssn_sn_symgam/challenges/d_physics_mtheory/c038_regge_combinatorial_curvature/`, challenge solutions are evaluated against a hostile 48-mutation test suite (`mut_01.json` through `mut_48.json`).
Each mutant introduces a subtle, adversarial corruption designed to catch lazy checkers:
- Topological disconnects and chord tampering.
- Orientation inversion on simplicial boundaries.
- Fabricated zero duality gaps where $d_0^T y \neq 0$.
- Dual box constraint violations ($\max |y_e| > w_e$).
- Nonzero curvature masquerading as exact boundaries.

#### 12.2 The Dual Checker Architecture
Verification requires two decoupled checkers:
1. `CombinatorialPrimalChecker`: Reconstructs graph incidence, validates vertex potential bounds, and computes primal $\Phi_1$.
2. `HomologyDualPotentialChecker`: Evaluates circulation balance $d_0^T y = 0$, verifies dual box constraints $\|y\|_\infty \le w$, and computes duality gap.

#### 12.3 Examination Questions
1. Why must the dual checker verify $d_0^T y = 0$ *before* checking numerical equality $y^T \omega = \Phi_1$? (The Triangle Counterexample).
2. What is the mandatory kill-rate required for an automated test fixture evaluating hostile mutations?
3. State the invariant: if a single mutant survives (failing to trigger a typed rejection), what is the evaluation verdict?

#### 12.4 Reference Solution & Derivation
1. **The Triangle Counterexample:**
   Consider a triangle where $\Phi_1 = 1$. A rogue solver could propose $y = (1, 0, 0)^T$ on a cochain $\omega = (1, 0, 0)^T$. Then $y^T \omega = 1 \times 1 = 1$, which equals $\Phi_1$ numerically. However:
   $$d_0^T y = \begin{pmatrix} -1 \\ 1 \\ 0 \end{pmatrix} \neq \begin{pmatrix} 0 \\ 0 \\ 0 \end{pmatrix}$$
   Here $y$ has non-zero divergence (it sinks flow into vertex 0 and sources flow from vertex 1). Because $y$ is not a closed circulation, weak duality does not hold, and $y$ is not a valid dual witness. Verifying $d_0^T y = 0$ is a mandatory precondition.
2. **Mandatory Kill-Rate:**
   The required kill-rate is **100%** (48 kills out of 48 mutants).
3. **Survivor Invalidation:**
   If even one mutant survives (0 kills out of 48, or 47 kills out of 48), the verification suite fails with `SURVIVOR_LEAK`. In security-critical mathematics, a single unflagged violation permits malicious proof laundering.

---

### Problem 13: Woland 7-Act Dialectic, Commit-Reveal & StructureBench Quad Persistence

#### 13.1 Formulation
In `omega_engine_woland`, dialectical bouts between candidate solvers and the adversarial tribunal execute under a strict **7-Act Dialectic**, a **3-Phase Commit-Reveal Protocol**, and **4-File StructureBench Quad Persistence**.

#### 13.2 The 7 Acts of the Woland Dialectic
1. **Act I: Carrier Framing** — Register task key, objective, and graph carrier.
2. **Act II: Obstruction Identification** — Compute baseline $\Phi_1, \Gamma_2$ defect mass.
3. **Act III: Candidate Proposal Generation & Epistemic Sieve** — Proposer commits candidate move with `authority_effect: None`.
4. **Act IV: Dialectical Gauge Break & Sandbox** — Tribunal applies adversarial gauge transformations and orthogonal 9-dot surprise challenges.
5. **Act V: Independent Witness** — Host evaluates dual witness certificates and checks duality gap.
6. **Act VI: Residual Ledger** — Tribunal logs persistent irreducible residuals to append-only register.
7. **Act VII: Authorization Gate & Crystallization** — Tribunal emits terminal disposition (`AUTHORIZED`, `REFUSED`, `BOUNDED_RESIDUAL`, `COMPOSTED`).

#### 13.3 Examination Questions
1. Detail the 3-Phase Commit-Reveal Protocol: Why must the Judge seal commitment before the Solver freezes its candidate, and why must the reveal happen only after both hashes are locked?
2. Name and specify the schema of the four persistent files in the **StructureBench Quad**:
   - `receipt.json`
   - `novella.md`
   - `dda_actions.jsonl`
   - `summary.json`
3. Explain how the Merkle hash chain in `dda_actions.jsonl` guarantees post-hoc audit tamper-evidence.

#### 13.4 Reference Solution & Derivation
1. **3-Phase Commit-Reveal Protocol:**
   - **Phase 1 (Judge Commitment):** The judge hashes the private test cases and evaluation criteria into `judge_commitment.json` (`commit_hash = SHA256(test_suite + salt)`). This prevents the judge from moving the goalposts after seeing the candidate solution.
   - **Phase 2 (Solver Freeze):** The solver submits its candidate solution, which is immediately hashed and frozen into `freeze_record.json` (`freeze_hash = SHA256(candidate_code)`). The solver cannot alter its code after viewing the test evaluation.
   - **Phase 3 (Reveal & Score):** Both parties unseal their commitments. The host governor executes the frozen candidate against the committed test cases and emits `scoring_receipt.json`. This protocol guarantees cryptographic non-collusion.
2. **StructureBench Quad File Specifications:**
   - `receipt.json`: Content-addressed JSON bound by `receipt_id = "sha256:..."` containing the task key, solver disposition, candidate checks, and SHA-256 hashes of all input/output artifacts.
   - `novella.md`: Human-readable and agent-readable Markdown novella narrating the 7-act dialectical drama, quoting exact line numbers, errors, and mathematical transitions.
   - `dda_actions.jsonl`: Cryptographically hash-chained append-only log where each line records a single DDC state transition $\langle t, \text{action\_rune}, \text{state\_hash}, \text{prev\_hash} \rangle$.
   - `summary.json`: High-level metrics artifact recording total fuel consumed, execution wall-clock time, final $\Phi_1$ defect, and terminal disposition.
3. **Merkle Hash Chain Audit Invariant:**
   In `dda_actions.jsonl`, entry $k$ contains `hash_k = SHA256(action_k + state_k + hash_{k-1})`. Any retrospective attempt to alter, delete, or re-order an intermediate state transition invalidates all subsequent hashes, providing cryptographic tamper-evidence.

---

## Qualification Attestation & Conclusion

A candidate who achieves 100% on the companion test suite [`test_landau_theoretical_minimum.py`](test_landau_theoretical_minimum.py) has demonstrated:
1. Complete fluency in exact rational cochain arithmetic ($\mathbb{Q}$) with zero floating-point leakage.
2. Complete adherence to the Discrete Deformation Calculus (DDC) and the Authority Firewall.
3. The ability to formulate, verify, and certify exact primal-dual witnesses with zero duality gap.
4. Immunity to the Landau permutation order trap and discrete simplicial curvature obstructions.
5. Mastery of cryptographic commit-reveal and immutable audit persistence.

Such a candidate is awarded the status of **Theoretical Minimum Certified Practitioner** by the Apartment 50 Tribunal under `AuthorityEffect: None`.
