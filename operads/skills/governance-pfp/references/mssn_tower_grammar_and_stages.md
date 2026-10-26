# MSS-N Tower Grammar & Stage Retraction

AuthorityEffect: None.

## 1. Grammars of the MSS-N Tower (Levels 0–21)

The MSS-N tower organizes structural and mathematical expressiveness across stratified levels from Level 0 (the mark) through Level 21:

- **Level 0 (The Mark):** The primal distinction `<>` and empty void.
- **Levels 1–5 (Atoms and Free Monoids):** Self-delimiting words over $\Sigma_{36}$, string expressions, prefix composition.
- **Levels 6–10 (Operads & Trees):** Application brackets `op<...>`, operadic tree nodes, recursive arity trees.
- **Levels 11–15 (Graphs & 1-Chains):** Directed graph edges, 1-chains, cochains, and boundary difference operators.
- **Levels 16–20 (Cycles & Cohomology):** Graph cycles, holonomy loops, CUT transformations, and survivor cohomology classes.
- **Level 21 (Simplicial Geometry):** 2-simplices, face boundary relations ($d \circ d = 0$), and deficit angles.

## 2. Internal Evaluator Dispatch Offset Allocation Formula ($N \ge 22$)

MSS wire syntax consists strictly of pure boundary expressions and contains **zero primitive opcodes**.

For host evaluator implementations managing trans-base extension stages beyond the base block ($N \ge 22$), internal dispatch targets are indexed by the affine offset formula:

$$\mathrm{base}(N) = 128 + 8 \times (N - 22)$$

Each stage $N$ allocates 8 consecutive evaluator dispatch slots $[\mathrm{base}(N), \mathrm{base}(N) + 7]$.

> [!IMPORTANT]
> **Dispatch Metadata Demarcation:**
> This formula represents **internal host evaluator dispatch metadata only**. It is never serialized into MSS wire packets, packet envelopes, or external transmission streams. Every trans-base level file must explicitly include the non-serialization disclaimer:
> `**Internal Evaluator Dispatch Offset:** $\operatorname{base}(N) = 128 + 8 \times (N - 22) = \dots$ *(Internal evaluator dispatch metadata only; MSS wire syntax contains zero primitive opcodes; never serialized into MSS wire packets)*`

### Evaluator Dispatch Offset Table (Sample)

| Stage | Name / Scope | Dispatch Base | Offset Range |
| :--- | :--- | :--- | :--- |
| **MSS-022** | Non-trivial Homology & Cycles | 128 | 128–135 |
| **MSS-023** | Metric Embeddings & Gram Minors | 136 | 136–143 |
| **MSS-024** | Simplicial Curvature & Regge Deficits | 144 | 144–151 |
| **MSS-025** | Connection Laplacians & Gauge Fields | 152 | 152–159 |

## 3. Retraction and Down-Map Invariants

### 3.1 The Boxed Conditional Lift Obligation Law

Whenever an atlas row has not been licensed by a machine-checked proof, the retraction law $d_N(u_N(x)) = x$ is an **obligation**, not an established property:

$$\boxed{\texttt{lift\_status=unproved} \lor \texttt{lift\_status=unlicensed} \implies \text{retraction is an obligation, not an established property}}$$

**Universal Phrasing:**
> *Any future accepted lift into MSS-N must exhibit $(u_N, d_N)$ satisfying $d_N(u_N(x)) = x$. No predecessor lift is currently claimed.*

### 3.2 Two-Part Decoupled Level Architecture

To maintain absolute claim hygiene, every level specification document across the research atlas (`omega_engine_education/documentation/1_minimal_symbol_system_n_mssn/levels/`) must be decoupled into two distinct structural parts:

1. **`## Part I: Row Contract`**:
   - Carrier Grammar & Syntactic Forms (pure boundary expressions, typed inputs).
   - Locally Checkable Verification Obligations & Deterministic Falsifiers.
   - Negative Counterexamples / Falsifier Boundary (concrete failure instances).
   - Claim Hygiene Quadrant (*What this supports*, *What this does not support*, *The narrowest defensible claim*, *Next test needed*).
2. **`## Part II: Lift Record from Predecessor`**:
   - Declared Lift Status (`unlicensed` / `unproved`).
   - Predecessor Stage identifier.
   - Declared Design Successor Rationale (curricular explanation for row introduction).
   - Conditional Lift Obligation (as defined in §3.1).

### 3.3 Semantic Verification Standards

1. **Anti-Default Guard:** Any newly introduced term in $S_N$ lacking an established preimage in $S_{N-1}$ must evaluate to typed `NON_DESCENT` rather than defaulting to self-assignment.
2. **Candidate Tags vs. Domain Witnesses:** Candidate syntax tags carry `AuthorityEffect: None`. Semantic validity requires an independent domain verifier (`checker.py`), complete witness data (incidence lists, Gram matrices, basis orderings), positive/negative fixture pairs, and Lean 4 proof kernels with zero ungrounded axioms.
3. **Open Semantic Obligations:** Unverified stages carry the computed status `SYNTAX` or `NONE` (from `research/mssn_sn_tower/code/python/stage_status.py`, never hardcoded from a level band) and remain open obligations until fully witnessed.

## 4. The 22-Level Genesis Decomposition & Epistemic Fences (Levels 0–21)

The Genesis derivations (`19L57G1` sealed derivation and `H3V7N5QF` 21 blind runs) form a 22-level evolutionary sequence from creation. Post-hoc crosswalks map conceptual correspondences to MSS-N atlas rows without asserting that Genesis derived the external atlas rows:

1. **Primordial Seed to Relation Closure (Levels 00–07):**
   - **Level 00 (Genesis S(0) / Crosswalk MSS-0):** Primordial seed (`Terms = {a, b}`, void relations, 2 legal initial states).
   - **Level 01 (Genesis S(1) / Crosswalk MSS-1):** Definitional relation embedding (`proj_ofR9_false`).
   - **Level 02 (Genesis S(2) / Crosswalk MSS-2):** Native self-loop ban (`identification_obstructed_iff`).
   - **Level 03 (Genesis S(3) / Crosswalk MSS-3):** Factor-of-2 edge destruction penalty ($\Delta = |V|+|E|-(|V_0|+|E_0|) + 2\cdot D_\text{dest}$).
   - **Level 04 (Genesis S(4) / Crosswalk MSS-32):** State/step mathematical theorems vs side-record `rfl` logging bifurcation.
   - **Level 05 (Genesis S(5) / Crosswalk MSS-41):** Monotone mass growth (`Reach4.mult_le`).
   - **Level 06 (Genesis S(6) / Crosswalk MSS-6):** Inter-derivation stage morphisms (`Step2.toStep3`).
   - **Level 07 (Genesis S(7) / Crosswalk MSS-7):** Universal loop-free digraph expressibility up to structural ceilings.

2. **Duality, Symmetries, and Ceilings (Levels 08–15):**
   - **Level 08 (Genesis S(8) / Crosswalk MSS-8):** Discrete primal-dual lower bound matched by constructive path witness.
   - **Level 09 (Genesis S(9) / Crosswalk MSS-9):** $\mathbb{Z}_2$ involution term swap (`swap9_swap`).
   - **Level 10 (Genesis S(10) / Crosswalk MSS-10):** Five structural capacity ceilings (N5, D9, T2, P3, F4).
   - **Level 11 (Genesis S(11) / Crosswalk MSS-11):** Positioned confluence and joined peaks.
   - **Level 12 (Genesis S(12) / Crosswalk MSS-12):** Meta-layer apparatus (14 metrics, 3 OEWAS gate detectors).
   - **Level 13 (Genesis S(13) / Crosswalk MSS-13):** Cycle classification and frontier tracking (`Reach*.cycles`).
   - **Level 14 (Genesis S(14) / Crosswalk MSS-14):** Declared search horizons (budget exhaustion vs proved obstruction).
   - **Level 15 (Genesis S(15) / Crosswalk MSS-15):** Admission record boundary (passive log vs active state mutation).

3. **Poset Lattice, Leftovers, and Higher Horizons (Levels 16–21):**
   - **Level 16 (Genesis S(16) / Crosswalk MSS-16):** 21-derivation commuting diamond poset.
   - **Level 17 (Genesis S(17) / Crosswalk MSS-17):** Hermetic cell packaging and prompt sandbox isolation.
   - **Level 18 (Genesis S(18) / Crosswalk MSS-18 / Negative Firewall):** Admitted leftovers dynamic (`Reach16.unbounded`) and the **Negative Epistemic Continua Firewall**: absolute refusal to import continuous Hilbert spaces $\mathcal{H}$ or differential manifolds into discrete relational regimes without mechanical derivation.
   - **Level 19 (Genesis S(19) / Crosswalk MSS-66 / Round R1):** Single-sentence demand injection yielding pairwise signed token annihilation ($+t + -t \mapsto \emptyset$).
   - **Level 20 (Genesis S(20) / Crosswalk MSS-20 / Round R2):** State raising and quotient lifting where term addition produces degenerate minimal-cost survivors ($|\text{Survivors}| = 2$).
   - **Level 21 (Genesis S(21) / Crosswalk MSS-21 / Round R3):** Twin fills and the **2-Cell Simplicial Horizon**: bifurcation between Variant 3A (1-term self-loop collapse) and Variant 3B (3-term oriented 2-cell boundary $\partial \sigma_2 = e_1 + e_2 - e_3$).
