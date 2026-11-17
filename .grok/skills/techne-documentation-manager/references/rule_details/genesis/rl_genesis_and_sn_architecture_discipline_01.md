# Detailed definition: Genesis & S(n) Epistemic Architecture (1)

**AuthorityEffect:** None.

Parent: [Genesis & S(n) Epistemic Architecture](../../../../../rules/genesis/rl_genesis_and_sn_architecture_discipline.md). Load for the matching predicate, not every task.

# Rule: Genesis & S(n) Epistemic Architecture Discipline

**AuthorityEffect:** None.

This rule enforces the Four-Layer Architecture, Two Boxed Laws, realization provenance, and relational substrate discipline across Genesis and $S(n)$ specifications. For S(n) presentation, obstruction registers, and mathematical hygiene invariants, see [`rl_sn_presentation_and_mathematical_hygiene.md`](../../../../../rules/genesis/rl_sn_presentation_and_mathematical_hygiene.md). Full procedural details reside in [`governance-pfp`](../../../../governance-pfp/SKILL.md).

---

## 1. Genesis & S(n) Four-Layer Architecture & Epistemic Boundaries

- **The Governing Directives**:
  > **Mathematics may describe or verify an $S(n)$ structure, but mathematics cannot be the reason that the next $S(n)$ structure exists unless Genesis itself forces it.** Physics is an application or interpretation only.
  $$\boxed{S(n+1) \text{ may contain only structure forced by an unresolved Genesis obstruction at } S(n).}$$
  $$\boxed{\text{A mathematical realization } R(S(n)) \text{ has no authority to extend } S(n).}$$
- **The Epistemic One-Way Arrow**: $S(n) \xrightarrow{\rho} R(S(n))$. Genesis states may map to mathematical models $\rho(S(n))$, but properties proved in a model return to Genesis *only through an explicitly proved faithful reflection bridge*. Structures discovered in $R(S(n))$ confer zero authority to extend Genesis.
- **The Four-Layer Separation**:
  1. *Layer 1 (Genesis Core)*: Structures forced by Genesis derivation from `<>` (opaque tokens, admission events, observational profiles, collapsed pairs, cost-2 separation floor, retraction down-maps $r_N$).
  2. *Layer 2 (Formal Shadows $R(S(n))$)*: Mathematical representations (graphs, simplices, categories, transfer operators) encoding core states without defining them.
  3. *Layer 3 (Downstream Applications)*: Domain analogies (QM, Regge gravity, neural nets); *zero authority to extend Genesis*.
  4. *Layer 4 (Verification & Receipts)*: Machine-checked Lean 4 kernels, native Rust crates, Python execution kernels, deterministic receipts.
- **Four-Directory Filesystem Architecture**: $S(n)$ documentation is physically partitioned into `core/` (Genesis derivations $S(0)$–$S(6)$), `realizations/<domain>/` (formal shadows), `applications/<domain>/` (downstream applications, e.g. `applications/physics/`), and `verification/` (Layer 4 execution engines). Shadows must never use `level_XX` stage identities or pose as Genesis stages.
- **Ground Presentation vs. Carrier Demarcation**: Stage 0 presentation token `<>` (one presentation lexeme, two ASCII bytes, 1 token) is strictly distinct from carrier elements ($|V_0|=0$, $s_0=0$, proved inertia under `CL-0-INERTIA` and `supply_no_op`).
- **Supplied Inscription vs. Admitted Carrier**: A supplied mark `<a>` records a token but does not force carrier admission ($|V_1|=1$) under quiescent equilibrium; admission requires an explicit consumer or retention receipt. Pair inscription `<ab>` records marks without asserting a relation ($|V_2|=2$); the distinguishing directed cut is postponed to Stage 3 (`<a->b>`).
- **Binary Germ & Delta-Support Separation**: In an irreflexive relation $R$, $R(a,b) \implies a \neq b$, so every admitted primitive cut has exactly two distinct endpoints: $\Delta_{\mathrm{support}}(a,b) := |\{a, b\}| = 2$. Agents must strictly separate:
  1. Distinct endpoints of a primitive cut: exactly 2 ($\Delta_{\mathrm{support}} = 2$, `PrimDiff.irrefl_witness_ne`).
  2. Minimum carrier size supporting it: 2 (`PrimDiff.no_witness_on_subsingleton`).
  3. Witness occurrences/certificates: may be 1, 2, or more (`PrimDiff.single_oriented_witness_consistent`).
  4. Newly supplied carrier elements: may be 0 when both endpoints exist.
  Agents must never assert "two witness occurrences everywhere" or conflate endpoint count with total carrier growth.
- **Categorical Binary Germ ($D_2$) & Collision Tagging**: $D_2$ has carrier $\{0, 1\}$ and single directed edge $0 \to 1$. Any admitted pair $R(a,b)$ admits a unique point-preserving function $f: D_2 \to (A, R)$ with $f(0)=a, f(1)=b$ (`D2_initial_pointed`). Observational distinction collisions $q(a)=q(b)$ are resolved by binary tagging $t: A \to \{0,1\}$ where $q'(x) = (q(x), t(x))$ preserves the prior observation while separating the pair.
- **Exact Typed Retraction Law & Homotopy Truncation Disambiguation**: Retractions must satisfy $\widehat{r}_n \circ u_n = \mathrm{inl}$ on $\operatorname{im}(u_n)$ and emit $\mathrm{inr}(\mathrm{NON\_DESCENT})$ for novel terms $y \notin \operatorname{im}(u_n)$. Do not conflate discrete construction stage $n$ with Postnikov homotopy truncation depth $j$; successive truncations $P_j X$ of a fixed space preserve $\pi_0$, so empty space followed by a point cannot be successive Postnikov truncations of the same space.
- **S(2) Collapse vs. S(3) Cut Invariant**: $S(2)$ consists of uninstantiated retention and observational collapse ($W_2^{\mathrm{active}} = \{\mathrm{obs\_collapse}\} \implies s_2 = 1$; shadow $S_2 \curvearrowright \mathbb{Q}^2$ by basis swap). Inhabited relational cuts belong to the formal shadow of the separation demand forced at $S(3)$, not $S(2)$ core.
- **S(6) Section/Retraction & Independent Lift Rank**: $\{u_N, r_N\}$ is a section/retraction pair ($r_N \circ u_N = \mathrm{id}$, $u_N \circ r_N \neq \mathrm{id}$), never an involution pair. Lift rank $\delta_n := \#\{\text{newly adjoined operators}\}$ is defined independently from survivor delta $s_{n+1} - s_n$. Predecessors resolve strictly from native Genesis ($D_6 \subset W_5^{\mathrm{Genesis}}$).
- **Pure Relational Substrate & Zero Forcing**: The native carrier contains only primitive distinctions, terms, binary relations (`a r b`), irreflexivity (`not x r x`), atomic transformations, obstructions, and survivor resistance ($s_n$). Never project physical or continuous concepts onto Genesis as native properties.
- **Realization Provenance & Candidate Representation Discipline**: Every shadow document must declare `realizes: "S(?)"` (or `null`), `authority_effect: "None"`, and `genesis_effect: "None"`. Candidate models beyond $S(6)$ declare `realizes: null`, `candidate_bridge_from: "S(6)"`, and `legacy_level: XX` (solely as a historical locator). Candidate realizations must never include $S(n)$ stage numbers in their titles (e.g. `(Realizes S(18))`), nor use $R(S(n))$ or naked $s_n$ notation ($R_{\mathrm{name}}^{\mathrm{candidate}}(S(6)), s^{\mathrm{name}}$).

---

## 2. Presentation Hygiene, Objections & Cross-References

- **Presentation & Mathematical Hygiene**: For active obstruction registers ($W_n^{\mathrm{active}}$ vs. $H_n$), discrete 4D Bianchi identities, spectral laws, retraction down-maps, Postnikov realization obligations, and normal form validation invariants, see [`.agents/rules/genesis/rl_sn_presentation_and_mathematical_hygiene.md`](../../../../../rules/genesis/rl_sn_presentation_and_mathematical_hygiene.md).
- **Foundational Primitives & Relational Substrate**: For the dual-implementation parity invariant (Lean 4 and Python), the complete enumeration of the 19 canonical primitive categories extracted from `19L57G1`, and relational grounding rules, see [`.agents/rules/genesis/rl_genesis_primitive_categories_and_relational_substrate.md`](../../../../../rules/genesis/rl_genesis_primitive_categories_and_relational_substrate.md).
- **Semiotic & Submodule Layout**: For semiotic and directory separation across Prompt, Packet, Stage, and Mode (`RULE_PROMPT_PACKET_STAGE_MODE_001`), see [`.agents/rules/docs/rl_pilot_estate_decoupling.md`](../../../../../rules/docs/rl_pilot_estate_decoupling.md).
