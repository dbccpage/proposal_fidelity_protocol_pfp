---
documentation_contract: symbol-game-documentation/v1
title: "quiz: The Theoretical Minimum Examination for Paper 001 (Discrete Cochain Retraction & Primal-Dual Involutions)"
kind: educational-exam
audience:
  - researchers
  - theoretical-physicists
  - discrete-mathematicians
  - coding-agents
status: proposed-revision
maturity: draft
claim_status: proposed
authority_effect: "None"
source_paths:
  - omega_engine_atlas/coda_atlas/omega_engine_pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper.md
prerequisites:
  - 00_preface_at_apartment_50.md
  - study_guide.md
  - ../paper.md
last_verified: 2026-10-02
---

# Theoretical Minimum Examination: Paper 001

**AuthorityEffect:** None.  
**Presiding Tribunal:** The Woland Retinue & Lev Davidovich Landau ("Dau").  
**Author of Baseline Paper:** Jeremy H. Carroll.  
**Location:** the city, Sadovaya 302-bis, Apartment 50.  
**Companion Preface:** Read [00_preface_at_apartment_50.md](./00_preface_at_apartment_50.md) for tribunal staging, character stations, and the Seven Mortal Sins.  
**Study Guide:** Master [study_guide.md](./study_guide.md) before sitting for this examination.

---

> [!IMPORTANT]
> **Instructions from Professor Landau:**
> 1. All calculations must be performed in exact rationals $\mathbb{Q} = \{p/q : p \in \mathbb{Z}, q \in \mathbb{Z}_{>0}\}$.
> 2. Zero floating-point numbers, zero decimals, zero heuristic approximations.
> 3. An optimization proposal is not a theorem. For this examination, certify every calculated minimum with a feasible dual witness. Complete exact enumeration can also prove a minimum when its search-set theorem and exhaustion are established.
> 4. Work through the pages in order. Attempt every question and use feedback to repair earlier errors. The complete instructor key has hints, worked answers, and a 100-point rubric; a perfect paper earns the tribunal seal.

---

<!-- ======================================================================= -->
<!-- PAGE 1: HORRIBLY SIMPLE (THE KINDERGARTEN OF INCONSISTENT OFFSETS)      -->
<!-- ======================================================================= -->

# Page 1: Horribly Simple (The Kindergarten of Inconsistent Offsets)

*Landau tosses his chalk: "If you cannot evaluate the cost of three edges on a napkin, you belong in a business school, not Apartment 50."*

### Problem 1.1: The Three Inconsistent Clocks
Three instruments report relative time offsets between three nodes $a, b, c$:
- Instrument 1 reports: $s_b - s_a = 1$ (directed edge $e_1 = a \to b$, report $c_1 = 1$).
- Instrument 2 reports: $s_c - s_b = 1$ (directed edge $e_2 = b \to c$, report $c_2 = 1$).
- Instrument 3 reports: $s_a - s_c = 1$ (directed edge $e_3 = c \to a$, report $c_3 = 1$).

1. Compute the sum of the reports around the directed cycle: $\sum_{i=1}^3 c_i$.
2. Explain in one sentence why no potential assignment $s = (s_a, s_b, s_c) \in \mathbb{Q}^3$ can satisfy all three reports simultaneously.
3. Does the graph contain any 2-cells (filled faces)? State the dimension of $C^2(G; \mathbb{Q})$.

### Problem 1.2: The All-Zero Potential
Let the edge penalties for disagreeing with the reports be $w = (w_1, w_2, w_3) = (1, 2, 3)$.
Consider the all-zero candidate potential $s^{(0)} = (0, 0, 0)$.
1. Compute the discrete coboundary vector $Bs^{(0)} \in \mathbb{Q}^3$.
2. Compute the residual vector $r^{(0)} = c - Bs^{(0)}$.
3. Calculate the exact proposal cost:
   $$D_c(s^{(0)}) = \sum_{i=1}^3 w_i |r_i^{(0)}|$$

### Problem 1.3: The Candidate Proposal $s = (0, -2, -1)$
A candidate proposes the vertex potential $s^* = (s_a, s_b, s_c) = (0, -2, -1)$.
1. Calculate the potential difference across each edge:
   - $(Bs^*)_{a \to b} = s_b - s_a =$ ________
   - $(Bs^*)_{b \to c} = s_c - s_b =$ ________
   - $(Bs^*)_{c \to a} = s_a - s_c =$ ________
2. Compute the residual 1-cochain $r^* = c - Bs^* = (r_1^*, r_2^*, r_3^*)$.
3. Compute the exact proposal cost $D_c(s^*)$.

### Problem 1.4: Proposal vs. Lower Bound Certificate
A machine learning agent runs a search routine, discovers the potential $s^* = (0, -2, -1)$ with cost $D_c(s^*) = 3$, and states:
> *"The cost is 3, and since three search heuristics failed to find a lower value, the global minimum is mathematically proved to be 3."*

1. What mathematical bound does $D_c(s^*) = 3$ provide on the quotient minimum $\Phi(c)$?
   $$\text{Choose: } [\Phi(c) \ge 3 \quad|\quad \Phi(c) \le 3 \quad|\quad \Phi(c) = 3]$$
2. Why does heuristic failure NOT establish that $\Phi(c) = 3$?
3. What mathematical object must be exhibited to certify an independent lower bound $\Phi(c) \ge 3$?

---

<!-- ======================================================================= -->
<!-- PAGE 2: INTERMEDIATE RIGOR (THE PRIMAL-DUAL COCHAIN ENGINE)             -->
<!-- ======================================================================= -->

# Page 2: Intermediate Rigor (The Primal-Dual Cochain Engine)

*Landau taps the slate: "Now we build the dual furnace. Anyone can guess a level; only a mathematician can construct a circulation."*

### Problem 2.1: Dual Feasibility Conditions
Let $G = (V, E)$ be a directed graph with incidence matrix $B \in \{-1, 0, 1\}^{|E| \times |V|}$, edge reports $c \in \mathbb{Q}^E$, and penalty weights $w \in \mathbb{Q}_{>0}^E$.
A vector $\lambda \in \mathbb{Q}^E$ is a candidate dual witness.
1. State the exact linear equation that $\lambda$ must satisfy at each vertex $v \in V$ to be a valid circulation.
2. State the inequality constraint that $\lambda_e$ must satisfy on each edge $e \in E$.
3. If $G$ is a simple directed cycle of length $k$, show that every valid circulation $\lambda$ must have constant magnitude across all edges: $\lambda_e = \alpha$ for all $e \in E$.

### Problem 2.2: The Weak Duality Derivation
Derive the Weak Duality Theorem: For **every** potential $s \in \mathbb{Q}^V$ and **every** feasible dual circulation $\lambda \in \mathbb{Q}^E$:
$$\langle \lambda, c \rangle \le D_c(s)$$
*Hint:* Use $B^T \lambda = \mathbf{0}$ to show that $\sum_{e} \lambda_e (Bs)_e = 0$, express $\langle \lambda, c \rangle$ in terms of the residual $r = c - Bs$, and apply the capacity bound $|\lambda_e| \le w_e$. Show every step cleanly.

### Problem 2.3: Zero Duality Gap on the Manuscript Triangle
Return to the Manuscript Triangle with $c = (1, 1, 1)$ and $w = (1, 2, 3)$.
1. What is the maximum value that a constant circulation $\lambda = (k, k, k)$ can attain without violating the capacity constraints $|\lambda_i| \le w_i$?
2. Exhibit the optimal dual witness vector $\lambda^* \in \mathbb{Q}^3$.
3. Compute the dual objective value:
   $$\langle \lambda^*, c \rangle = \sum_{i=1}^3 \lambda_i^* c_i$$
4. Compute the duality gap:
   $$\Delta = D_c(s^*) - \langle \lambda^*, c \rangle$$
   where $s^* = (0, -2, -1)$. State the definitive conclusion regarding the global minimum $\Phi(c)$.

### Problem 2.4: Coboundary Gauge Invariance
Let $c = (1, 1, 1)$ be the reports on the Manuscript Triangle.
A gauge transformation $\phi = (2, -1, 5) \in \mathbb{Q}^3$ is applied to the vertices, generating new reports:
$$c' = c + B\phi$$
1. Calculate the shifted report vector $c' \in \mathbb{Q}^3$.
2. Compute the cycle sum $\sum_{i=1}^3 c'_i$.
3. Without re-running an optimization solver, determine the exact value of $\Phi(c')$. Cite the governing theorem.

### Problem 2.5: The Directed Cycle Obstruction Formula
Consider a directed 4-cycle $C_4$ with vertices $\{v_1, v_2, v_3, v_4\}$, directed edges $e_1 = v_1 \to v_2$, $e_2 = v_2 \to v_3$, $e_3 = v_3 \to v_4$, $e_4 = v_4 \to v_1$.
The edge reports are $c = (4, -2, 5, 1)$ and the penalties are $w = (7, 3, 9, 5)$.
1. State the general Directed Cycle Obstruction Formula for $\Phi(c)$.
2. Identify the bottleneck edge $e^*$ and its weight $\min_e w_e$.
3. Calculate the exact quotient minimum $\Phi(c)$ as an integer or fraction in lowest terms.

---

<!-- ======================================================================= -->
<!-- PAGE 3: ADVERSARIAL REALITY GATES & INVARIANT INVOLUTIONS (THE DESCENT CRUCIBLE) -->
<!-- ======================================================================= -->

# Page 3: Adversarial Reality Gates & Invariant Involutions (The Descent Crucible)

*Woland smiles faintly. Landau leans in: "Here is where the pretenders drown. If your algorithm descends forever without stopping, Azazello will assist your descent through the floorboards."*

### Problem 3.1: The Infinite Rational Descent Trap (Zeno's Trap)
Consider a single edge $e = u \to v$ with report $c = 1$ and penalty $w = 1$.
An autonomous solver generates a sequence of potential differences $\Delta s_t = s_v(t) - s_u(t)$ such that the residual at step $t$ is $r_t = 2^{-t}$ for $t = 1, 2, 3, \dots$.
1. Compute the cost $D_t$ at step $t$. Is the sequence strictly monotonically decreasing ($D_{t+1} < D_t$) for all $t$?
2. Does there exist any finite step $t^* \in \mathbb{N}$ such that $D_{t^*} = 0$?
3. Explain why the rule *"Admit proposal if $D(s_{\text{new}}) < D(s_{\text{old}})$"* is an unsafe halting condition in discrete optimization over $\mathbb{Q}$.
4. Separate three obligations: strict `CUT` descent, a finite attempt budget, and a returning or timed-out check. Which are enforced by `SymbolGameGovernor`, which by Demo 1's outer loop, and which by the native adapter? Explain why a turn counter alone is insufficient.

### Problem 3.2: Sparsity of Optimal Residuals & The Null-Space Property
Let $G = (V, E)$ be a connected graph with $n$ vertices and $m$ edges ($m \ge n$).
1. State the upper bound on the number of non-zero entries in the residual vector $r^* = c - Bs^*$ for an extreme-point (basic feasible) optimal solution:
   $$|\operatorname{supp}(r^*)| \le \text{\_\_\_\_\_\_}$$
   Express the bound in terms of the cycle rank (first Betti number) $\beta_1 = m - n + 1$.
2. Suppose $G$ is a triangle ($n=3, m=3$) where all edge penalties are strictly equal: $w = (2, 2, 2)$, with reports $c = (1, 1, 1)$.
   - Does there exist a uniquely minimizing potential $s^*$?
   - Exhibit two distinct potentials $s^{(1)}$ and $s^{(2)}$ (not differing by an additive constant) that both achieve the global minimum $\Phi(c) = 6$.
   - Using $f = (0, -2, -1)$ and $\lambda = (2, 2, 2)$, show why a proposed minimum of $2$ is impossible.
   - State the sufficient **Weighted Null-Space Property** using nonzero $z\in\operatorname{im}B$. For $S=\{e_1\}$, exhibit a vector that makes the strict inequality fail. Does failure alone prove that a particular residual is nonunique?

### Problem 3.3: Combinatorial Spanning Tree Search & The 100,000 Forest Cap
The native Rust solver `graph_phi1.rs` solves $\Phi_1$ by enumerating spanning forests over $G$.
1. According to Cayley's formula, the complete graph $K_n$ has $n^{n-2}$ spanning trees.
   - Calculate the number of spanning trees for $K_6$.
   - Calculate the number of spanning trees for $K_8$.
2. If an examinee passes $K_8$ to `graph_phi1.rs`, what is the exact behavior of the Rust solver?
   - Does it return an approximate floating-point answer?
   - Does it return a partial minimum based on the first 100,000 trees?
   - What typed enum error does it return?
3. Why does repository governance forbid the solver from returning a "best-so-far" partial minimum when the cap is hit?

### Problem 3.4: Lean 4 Toy Involutions and Claim Discipline
In the repository formalization `lean4/`:
The manuscript describes the following local statements; inspect the actual files before asserting a build result:
- `InvolutionLaws.lean` proves pair cancellation for a supplied sign-reversing, weight-preserving map on signed natural-number weights.
- `OddCycleObstruction.lean` concerns the three vertex signs of a triangle.
- `NonAuthority.lean` encodes a policy type with one value, so its theorem holds by construction.

An eager machine learning researcher publishes a preprint claiming:
> *"The Lean 4 proofs in Paper 001 mathematically verify a polynomial-time algorithm that solves the quantum fermion sign problem."*

Write the formal **Adversarial Receipt Audit** refuting this claim according to the repository Claim Hygiene Rule:
1. **What it supports:** State precisely what `OddCycleObstruction.lean` and `InvolutionLaws.lean` actually formalize in this toy setting.
2. **What it does NOT support:** State three specific physical and computational claims that do NOT follow from these toy Lean files.
3. **The narrowest defensible claim:** Formulate the single narrowest valid claim regarding the Lean 4 formalization in Paper 001.
4. **The next test needed:** Specify the carrier and representation, the mapping theorem, and any additional algorithm or complexity theorem needed for the proposed physical claim. Explain why a toy theorem or a hash receipt cannot supply these obligations.

---

## Grading Trichotomy & Terminal Disposition

Use the problem weights in [instructor_key.md](./instructor_key.md). Grade all attempted answers and give a concrete repair for each lost point. These dispositions are fictional game labels, not judgments about a student.

Landau dusts his hands, spins his railway chalk, and glares across the table:

- **`PASS` (Score: 100/100):**
  Every numerical quantity is in exact rationals $\mathbb{Q}$; all dual circulation witnesses are exhibited with zero duality gap; the weak duality theorem is derived cleanly without missing steps; Cayley's formula and the 100,000 cap are evaluated accurately; and the Lean 4 claim hygiene audit is uncompromisingly strict.
  *Disposition:* Woland smiles; Landau signs the slate; Jeremy Carroll shakes your hand; Liudmila pours a celebratory cup of tea with strawberry jam.
- **`NONDESCENT` (Score: 40–99/100):**
  The student confused an upper bound with a certificate, made arithmetic errors on the cycle formula, or hand-waved the basic feasible solution sparsity bound.
  *Disposition:* Koroviev cackles shrilly; the candidate is sent to the kitchen to compute tree enumerations by hand under Polina's supervision.
- **`DECAPITATED` (Score: 0–39/100):**
  The student used floating-point decimals, asserted that $2^{-t}$ terminates in finite time, or claimed that toy Lean involutions solve the quantum fermion sign problem.
  *Disposition:* Azazello points to the open window; Behemoth ignites the primus; Abadonna removes his glasses.


## Final challenges in Apartment 50
These optional challenges come after the examination. They do not change its 100-point score. Woland wants a proof; Behemoth wants a counterexample. Hints and solutions are in the instructor key.

### Challenge A The sufficient condition that fails
Orient the six edges of $K_4$ from the earlier letter to the later letter, with vertex order $a,b,c,d$, and give every edge weight $1$. Set $c_{ab}=1$, $c_{ac}=-1$, and all other reports to $0$.

1. Show that $s=0$ has cost $2$. Verify the dual witness, in edge order $ab,ac,ad,bc,bd,cd$,
   $$\lambda=(1,-1,0,1/2,1/2,-1/2).$$
2. Prove that the minimizing potential is unique after fixing $s_a=0$. Use the strict capacities on the four zero-residual edges.
3. For $S=\{ab,ac\}$ and $h=(1,0,0,0)$, compute $z=Bh$. Show that the sufficient weighted null-space condition fails despite the unique minimizer.
4. State exactly why this does not contradict the theorem in the paper.

### Challenge B The perfect-looking counterfeit receipt
The equal-weight triangle has reports $(1,1,1)$ and weights $(2,2,2)$. A native response claims `PASS`, potential $(0,-2,-1)$, and minimum `2`.

1. Recompute the potential's cost. Which consistency check rejects the response before optimality is considered?
2. Give a feasible dual that excludes a minimum of $2$.
3. Write a response-validation checklist covering JSON shape, exact rational strings, complete vertex coverage, forest-count type and range, and objective agreement.
4. Does a structurally valid response and a matching primal cost prove global minimality? Name the remaining trust or certificate obligation. What should happen on a native refusal or timeout?
