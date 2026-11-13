# Degree-Wise Obstruction Calculus and Symbolic DSL: Graded Cochain Complexes, Degree Separation, and Local-Global Gate Non-Factorization

**Author:** Jeremy H. Carroll  
**Date:** 2026-09-30  
**Version:** 2.1.0  
**Canonical Identity:** `EA:F004.001.009` (`FOC-006`)  
**License:** Creative Commons Attribution 4.0 International (CC-BY-4.0)

\noindent\textbf{Nonclaims:} This monograph assigns no authorization and changes no jurisdiction. It carries no operational authority or institutional standing.\\[0.4em]

## Mechanism inventory

| Slot | Value / Description |
| --- | --- |
| **Primitive Differences** | $\delta c = \text{{defect mass}}$ |
| **Carriers / Structure** | Finite Graph 0-Cochain / Hilbert Space |
| **Cochain complex** | $C^0 \to C^1 \to C^2$ |
| **Coboundary maps** | $\delta^0, \delta^1$ |
| **ZeroRel** | Preserved under $L_1$ quotient |
| **Licensed repairs** | None |
| **Quotient / Q1** | Banach Quotient |
| **Residuals** | $\delta c \neq 0$ boundary defect |
| **Witnesses** | Replayable Python / Rust Certifiers |
| **Observers / profiles** | Operational Observer |
| **Anomalons** | None |
| **CompletionLaw** | Finite Cochain Completion |
| **Terminal / route** | Route to Anomalon Estate |
| **AuthorityEffect** | None; this monograph assigns no authorization and changes no jurisdiction. It carries no operational authority or institutional standing. |

## Scope

> **Specification Identity:** This paper is the finite obstruction DSL specification. Its theorem content is the ($k=1$) degree-separation witness and the local/global gate non-factorization result.

**Main result (informal).** The obstruction DSL is a typed graded symbolic system: $d_0:C^0\to C^1$ and $d_1:C^1\to C^2$ act on distinct cochain degrees, and the diagnostic carried by $d_1$ (the closure defect $\Gamma_2$) is provably invisible to any model that supplies only $C^1$ data with no explicit 2-cell structure. Valid expressions must respect degree typing and $\ell^1(E;g)$ aggregation; collapsing degrees or relaxing the norm destroys recoverable obstruction information.

The same finite replay now also has a composite LGGR form: even a local fingerprint that remembers both $C^1$ edge data and whether the DSL diagnostic is constructible does not determine the global gated pair consisting of $\Gamma_2$ and acceptance authorization.

This boundary is stable under context extension: adding arbitrary external metadata, including QM-facing operator/density payloads, does not repair the PrimitiveDifference non-factorization unless the missing global gate itself is supplied. This is factored through a reusable PrimitiveDifference theorem: any local fingerprint/global readout pair with a zero-related witness remains LGGR after arbitrary context is added around the core state.

This paper formalizes the graded algebraic structure underlying the obstruction engine. It defines:

* The cochain complex and its boundary operators as programmable primitives.
* Degree separation: why operations on $C^k$ cannot be faithfully reduced to $C^{k-1}$.
* The compositional grammar for expressing transformations over obstruction fields.

### Explicit exclusions

This paper does NOT contain:

* Operator dynamics or transport proposals (\to Paper 011).
* Trace metrics, density lifts, or Hilbert structures (\to Paper 013). The DSL *declares* `Density` and `trace_norm` slots but constructs neither — see the §8.1 import fence.
* Any physical interpretation or analogy.
* Any authority, acceptance, correctness, or semantic-truth claim. **Authority: none** — see the GTOC / GTLA Compliance Note.
* Probability semantics. The $\ell^1(E;g)$ aggregation here is a finite weighted tally, and no probabilistic adapter is supplied.
* A quantum-cohomology **admission classifier** or classical/quantum **non-selection** theorem (\to **QM_032** `CODAQMBridge` / `QM-032-C3`–`C5`). This paper remains the degree-wise complex **DSL declaration surface**; QM_032 consumes graded complex shape without duplicating the DSL.

(The *Explicit exclusions* list above is this paper's "what this does not claim" box.)

**Why a researcher should care.** Systems that flatten a graded diagnostic into a single scalar "score" silently discard exactly the information that distinguishes a first-order obstruction ($\Phi_1$) from a closure failure ($\Gamma_2$). This paper makes the degree structure a *typed* invariant: a statically-checked DSL rejects degree-confused expressions before execution, and the degree-separation theorem demonstrates why a $C^1$-only model cannot fake a $\Gamma_2$ computation. The payoff is an auditable boundary between what a diagnostic actually measured and what it asserted without construction.

## 1. Graded Cochain Complex

Let $P = (V, E)$ be a finite connected directed graph. This graph is a *declared* starting
structure: it is admitted, not derived, and nothing in this paper narrates a domain prior to it.

Construct the graded objects first. From $P$ alone:

* $C^0(P) = \mathbb{R}^{|V|}$ — scalar node assignments.
* $C^1(P) = \mathbb{R}^{|E|}$ — edge-level obstruction fields ($\omega$).

A third object exists only once an explicit finite set of 2-cells $\sigma_2$ is *attached* to $P$.
It is not induced by $(V,E)$:

* $C^2(P,\sigma_2) = \mathbb{R}^{|\sigma_2|}$ — 2-cell closure defects.

Only now that the objects exist may the operators between them be named. If $(P, \sigma_2)$ is
specified, the graded chain is
$$
C^0 \xrightarrow{\;d_0\;} C^1 \xrightarrow{\;d_1\;} C^2 .
$$
Otherwise: no $\sigma_2$, hence no $C^2$, hence no $d_1$ — and the calculus terminates at $C^1$.

**Definition (coboundary operators).**
$$
(d_0 f)(e_{ij}) = f(j) - f(i)
$$
$$
(d_1 \omega)(\sigma) = \sum_{e \in \partial\sigma} \mathrm{sign}(e, \sigma) \cdot \omega(e)
$$

**Fundamental property.**
$$
d_1 \circ d_0 = 0
$$

This identity assumes the $d_0$ and $d_1$ incidence conventions are compatible: every oriented boundary appears with canceling signs. A DSL implementation must test this invariant for each supplied `Complex2`.

This ensures that any exact form ($\omega = d_0 f$) is automatically closed under $d_1$.

**Implementation Registry.** Transient crate function names and module paths are decoupled from this paper specification and maintained in the companion claim ledger.

## 2. Degree Separation Theorem

**Theorem — Degree Separation for $\Gamma_2$**

The general $d_k:C^k\to C^{k+1}$ statement is schematic: it follows the same typing logic, but this paper establishes and replays only the $d_1:C^1\to C^2$ / $\Gamma_2$ instance.

In the presence of nontrivial higher-degree structure, the diagnostic information carried by $d_k:C^k\to C^{k+1}$ is not recoverable from $C^{k-1}$-data alone without additional structure.

**Proof sketch.**

* $d_0$ maps $C^0 \to C^1$. Its image $\mathrm{im}(d_0)$ is the space of exact 1-cochains. When a 2-complex is specified, $H^1$ is defined as $\ker(d_1)/\mathrm{im}(d_0)$. Otherwise, obstruction is measured operationally via $\Phi_1$.
* $d_1$ maps $C^1 \to C^2$. The closure defect $\Gamma_2=\|d_1h_1\|_1$ depends on the 2-cell incidence operator $d_1$. It is therefore invisible to a graph-only model that supplies $C^1$ but no explicit 2-cell structure.

**Consequence.** The diagnostic hierarchy $\Phi_1, \Gamma_2$ requires operating at multiple cochain degrees simultaneously. A system restricted to $C^0$ cannot represent arbitrary cycle obstruction. A system restricted to $C^1$ cannot evaluate closure failure unless an explicit 2-cell complex and $d_1$ are supplied.

### Worked Replay — $\Gamma_2$ Is Invisible Without a 2-Cell

Take $C_3$ (triangle) with $\omega=(1,0,0)$. A graph-only model (no 2-cell) computes the primary obstruction

$$
\Phi_1=\min_f\|\omega-d_0 f\|_1=1,
$$

but $\Gamma_2$ is *undefined* — there is no $d_1$ to apply. Now attach the single 2-cell $\sigma=(e_1,e_2,e_3)$ with incidence $d_1=[\,1\;\;1\;\;1\,]$. Adding a 2-cell does not change $\operatorname{im}(d_0)$, so $\Phi_1=1$ still, while the closure defect becomes visible on the residual $h_1=(1,0,0)$:

$$
\Gamma_2=\|d_1 h_1\|_1=|1+0+0|=1,\qquad R_{cl}=\Gamma_2/\Phi_1=1.
$$

The same edge data yields *no* $\Gamma_2$ in the graph-only model and $\Gamma_2=1$ once the 2-cell is supplied — a concrete instance of the degree-separation theorem, and the reason the DSL makes `gamma2` ill-typed without a `Complex2`.

**Lean support note (v2.0.7).** **[MECHANIZED-PARTIAL]** The integer $C_3$ instance is `PaperFOC006.c3_degree_separation_instance`: the $\ell^1$ distance from $(1,0,0)$ to the image of $d_0$ is $1$, that distance ignores the 2-cell flag, a missing 2-cell has no $\Gamma_2$ readout, and the attached 2-cell has $\Gamma_2=1$. `PaperFOC006.c3_d1_d0_zero` establishes the compatible $C_3$ coboundary identity, `PaperFOC006.gamma2_graphOnly_undefined` and `PaperFOC006.gamma2_withTwoCell_one` prove the graph-only/2-cell contrast, and `PaperFOC006.c1_local_green_not_gamma2_global` establishes the LGGR form: the $C^1$-only local quotient preserves the edge data, but it cannot also carry the global $\Gamma_2$ readout. The same file names the readout gate explicitly: `PaperFOC006.gamma2_readout_requires_twoCell`, `PaperFOC006.no_twoCell_blocks_gamma2_readout`, and `PaperFOC006.graphOnly_gamma2_not_zero_readout` state that a missing 2-cell does not provide a zero-valued $\Gamma_2$; it provides no $\Gamma_2$ readout. The composite theorem `PaperFOC006.degreeDsl_local_green_not_global_gate` strengthens the finite replay without widening the general-$k$ claim: preserving the local pair `(C1, diagnosticConstructible)` still does not factor the global pair `(Gamma2, acceptanceAuthorized)`. The context-extension theorem `PaperFOC006.contextual_local_green_not_global_gate` is an instance of `PaperFOC006.PrimitiveDifference.localGreenGlobalRed_context_obstruction_of_witness` in this package. The name `OmegaCore.PrimitiveDifference` is not a module here.

> **Mechanization scope (do not read past it).** `PaperFOC006.c3_degree_separation_instance` is an integer-valued shadow. Cochains in that file are `Int`. A minimization over real potentials, a real quotient $R_{cl}$, and the general-$k$ statement are outside this deposit. Within the integer shadow, `gamma2?` is a declared gate (`if hasTwoCell then some … else none`), so the readout theorems mechanize this paper's stipulation that a missing 2-cell yields no $\Gamma_2$. The non-factorization theorem `PaperFOC006.c1_local_green_not_gamma2_global` and its composites remain separate.

```python
import numpy as np
h1 = np.array([1., 0, 0]); d1 = np.array([[1., 1, 1]])   # one 2-cell over e1,e2,e3
print(np.abs(d1 @ h1).sum())                             # Gamma_2 = 1.0
```

Expected output: `1.0`.

## 3. Symbolic Primitives

The obstruction calculus admits a minimal set of programmable primitives:

| Symbol | Type | Meaning |
|:---|:---|:---|
| $\omega$ | $C^1(P)$ | Raw obstruction field |
| $d_0$ | $C^0 \to C^1$ | Coboundary (node \to edge) |
| $d_1$ | $C^1 \to C^2$ | Coboundary (edge \to face) |
| $\pi_Z$ | $C^1 \to C^1$ | solver-declared cycle-space/residual projection |
| $f^*$ | $C^1 \to C^0$ | Optimal scalar section (solver output) |
| $h_1$ | $C^1$ | Irreducible residual: $\omega - d_0 f^*$ |
| $|\cdot|_{1;g}$ | $C^k \to \mathbb{R}$ | $\ell^1(E; g)$ norm |

The $\ell^1$ norm is generalized to an edge-sum over a local gauge $g$ on channel space.

> **Note on $\pi_Z$:** This projection is not assumed to be the $\ell^2$ harmonic projection. It is a declared projection operator satisfying tested invariants such as $\pi_Z^2=\pi_Z$ and $\pi_Z(d_0f)=0$. It is a solver-declared residual/cycle-space projection induced by the chosen solver. It is not unique and depends on the chosen gauge and optimization procedure.

> **Note on $f^*$:** $f^*$ is an $\ell^1$-minimizing solution and may not be unique. Any minimizer defines a valid residual $h_1$.

**Code:** $\pi_Z$ is implemented in `cycle_space_projector.rs`.

## 4. Compositional Expressions

If no `Complex2` is supplied, $\Gamma_2$ is undefined. It is not zero, not accepted, and not eligible for $R_{\mathrm{cl}}$ computation.

**Typed Readout Semantics:**
To prevent silent degree confusion or treating missing 2-cell complexes as zero closure defects, $\Gamma_2$ readouts are explicitly typed:

```text
Gamma2Readout :=
  | NoComplex2
  | MalformedComplex2
  | Gamma2(value)
```

The closure ratio $R_{\mathrm{cl}} = \Gamma_2 / \Phi_1$ is defined and well-typed only when `Gamma2Readout` is `Gamma2(value)` and $\Phi_1 > \varepsilon$.

> **Architecture Split:** Rewrite rules (Section 5) belong to the symbolic layer. The solvers calculating $\pi_Z$ and $f^*$ belong to the numeric layer.

> **Evaluation Boundary:** This calculus defines expressions only. It does not define acceptance or correctness. Evaluation is handled externally (Paper 011).

Using the primitives above, the engine's diagnostic chain can be expressed as a composition.

**Compositional Typing:**

```text
ω \in C¹
f* \in C⁰
d_0f* \in C¹
h_1 \in C¹
d_1h_1 \in C^2
Φ_1 \in ℝ
Gamma2Readout
```

**Primary obstruction:**
$$
\Phi_1 = |h_1|_{1;g} = |\omega - d_0 f^*(\omega)|_{1;g}
$$

**Closure defect:**
$$
\Gamma_2 = |d_1 h_1|_{1;g} = |d_1(\omega - d_0 f^*(\omega))|_{1;g}
$$

**Closure ratio:**
$$
R_{cl} = \Gamma_2 / \Phi_1 \quad (\text{when } \Phi_1 > \varepsilon)
$$
If $\Phi_1 \le \varepsilon$ and $\Gamma_2 > \varepsilon$, the reading is *flagged* as inconsistent with the assumed cochain model. **[POLICY RULE]** The flag is a diagnostic trigger, not a proof of inconsistency. In exact arithmetic the implication is sound ($\Phi_1=0\Rightarrow h_1=0\Rightarrow\Gamma_2=0$); under $\varepsilon$-tolerances only $\Gamma_2\le\|d_1\|\,\Phi_1$ is available, so a $d_1$ of large operator norm can produce this pattern on well-formed data. The flag routes the packet for inspection. It does not authorize a verdict about the system.

**Canonical projection:**
$$
h_Z = \pi_Z(\omega)
$$

**Representative distortion (\to Paper 009; elaborated in Paper 013):**
$$
\Xi = \|\rho(h_1^*)-\rho(\phi^*)\|_1
$$
where $h_1^*$ is the tie-broken primal residual and $\phi^*$ is the tie-broken optimal dual witness. This paper treats $\rho$, $\phi^*$, and $\Xi$ as opaque external primitives.

> **Note.** The definition and justification of $\Xi$ belongs in Paper 009 (the Dual-Witness $\Xi$ construction), elaborated in Paper 013. It appears here only to show how it fits the compositional chain.

## 5. Rewrite Rules

The following algebraic identities hold in the obstruction calculus and may be used for symbolic simplification:

**Rule 1 (exactness kills closure).**
$$
d_1 \circ d_0 = 0
$$

Rules involving $\pi_Z$ are enabled only after the projection implementation has passed its invariants:
$$
\pi_Z^2=\pi_Z,\qquad \pi_Z(d_0f)=0.
$$
Without that certification, these are not sound rewrite rules.

**Lean support note (v2.0.3).** The certified-projection condition is captured by `PaperFOC006.DeclaredProjection`: `PaperFOC006.declaredProjection_idempotent` and `PaperFOC006.declaredProjection_kills_exact` expose exactly the two rewrite permissions above. These theorems are contract lemmas: they apply only to a projection whose idempotence and exact-killing fields have been supplied.

**Rule 2 (projection idempotence).**
$$
\pi_Z \circ \pi_Z = \pi_Z
$$

**Rule 3 (exact component vanishes under projection).**
$$
\pi_Z(d_0 f) = 0 \quad \forall f \in C^0
$$

**Rule 4 (closure deviation).**

$\Gamma_2$ measures failure of $h_1$ to lie in $\ker(d_1)$.

## 6. Coarse-Graining Asymmetry

**Core fact.** **[STANDARD — triangle inequality with equality case]** The $\ell^1$ norm forbids sign cancellation:
$$
\left|\sum_i x_i\right| \le \sum_i |x_i|
$$
with equality iff all $x_i$ share the same sign.

**Consequence.** Aggregation that retains only squared-norm or magnitude data generally loses sign, orientation, and edge-local decomposition information unless those data are carried separately. Fine combinatorial information (edge orientations, defect signs) is irreversibly destroyed.

**Corollary (reconstruction obstruction).** Recovery of the discrete representation from squared aggregate data generally requires additional combinatorial topology and orientation data. No canonical inverse exists from squared aggregate magnitudes alone.

## 7. Final Statement

$$
\boxed{
\text{The obstruction calculus is a graded symbolic system in which } d_0, d_1, \pi_Z \text{ operate on distinct cochain degrees, and valid expressions must respect degree typing and } \ell^1(E; g) \text{ aggregation. Collapsing degrees or relaxing the norm destroys recoverable obstruction information.}
}
$$

Formal Grammar and Evaluation Semantics

### 8. DSL Grammar

The obstruction DSL is a typed expression language over graded cochains.

#### 8.1 Types

```bnf
<Type> ::=
    Real
  | Bool
  | Graph
  | Complex2
  | C0
  | C1
  | C2
  | Gauge
  | Projection
  | Density
  | Decision
```

> **Import fence — `Density`, `trace_norm`, `rho`, `xi`.** These are **declared slots, not constructed objects**. This paper builds no density operator, trace norm, or Hilbert structure at its declared degree; the *Explicit exclusions* box routes all of them to Paper 013 (and `xi` to Paper 009). They are therefore **[IMPORTED / Q-gated placeholders]**: a well-typed program may *mention* them, but nothing here licenses reading `Density` as a quantum-mechanical density state, `trace_norm` as a trace-class norm on an operator algebra, or `rho` as a density lift. No result in this paper depends on their internal structure, and the degree-separation and typing results below are stated and proved without them. Instantiating any of these slots is an import, and it must be priced where it is constructed — not here.

Multi-channel types are written:

```bnf
<CType> ::=
    C0[g]
  | C1[g]
  | C2[g]
```

where `g` is the local observer gauge.

#### 8.2 Terms

```bnf
<Expr> ::=
    <Var>
  | <RealLiteral>
  | <Apply>
  | <Let>
  | <If>
  | <Norm>
  | <Subtract>
  | <Project>
  | <Solve>
  | <Ratio>
  | <DecisionExpr>
```

#### 8.3 Variables

```bnf
<Var> ::= identifier
```

Examples:

```text
omega
f
h1
phi1
gamma2
xi
```

#### 8.4 Function application

```bnf
<Apply> ::= <Op> "(" <ExprList> ")"

<ExprList> ::= <Expr> | <Expr> "," <ExprList>
```

#### 8.5 Core operators

```bnf
<Op> ::=
    d0
  | d1
  | solve_l1
  | residual
  | phi1
  | gamma2
  | r_cl
  | pi_Z
  | rho
  | xi
  | eval
```

#### 8.6 Let binding

```bnf
<Let> ::= "let" <Var> ":" <Type> "=" <Expr> "in" <Expr>
```

Example:

```text
let h1:C1 = residual(omega) in norm1(h1)
```

#### 8.7 Norms

```bnf
<Norm> ::=
    "norm1" "(" <Expr> ")"
  | "norm_g" "[" <Gauge> "]" "(" <Expr> ")"
  | "trace_norm" "(" <Expr> ")"
```

#### 8.8 Arithmetic

```bnf
<Subtract> ::= <Expr> "-" <Expr>

<Ratio> ::= "ratio" "(" <Expr> "," <Expr> "," <Expr> ")"
```

The ratio form is used for safe closure ratios:

```text
ratio(gamma2, phi1, eps)
```

#### 8.9 Projection

```bnf
<Project> ::= "project" "[" <Projection> "]" "(" <Expr> ")"
```

Example:

```text
project[pi_Z](omega)
```

#### 8.10 Solver expression

```bnf
<Solve> ::= "solve_l1" "(" <GraphExpr> "," <C1Expr> ")"
```

The solver returns a structured value:

```text
SolveResult {
    f_star : C0,
    h1     : C1,
    phi1   : Real
}
```

#### 8.11 Evaluation expression

```bnf
<DecisionExpr> ::=
    "eval" "(" <Coordinates> "," <Coordinates> "," <Config> ")"

<Coordinates> ::=
    "coords" "("
        "phi1" "=" <Expr> ","
        "gamma2" "=" <Expr> ","
        "rcl" "=" <Expr> ","
        "xi" "=" <Expr>
    ")"
```

### 9. Static Typing Rules

The DSL is statically typed. Invalid degree composition is rejected before execution.

#### 9.1 Coboundary typing

$$
d_0 : C^0 \to C^1
$$

```text
Γ ⊢ f : C0
────────────
Γ ⊢ d0(f) : C1
```

$$
d_1 : C^1 \to C^2
$$

```text
Γ ⊢ omega : C1
──────────────
Γ ⊢ d1(omega) : C2
```

Invalid:

```text
d0(omega:C1)
d1(f:C0)
```

#### 9.2 Residual typing

```text
Γ ⊢ omega : C1
Γ ⊢ f     : C0
──────────────
Γ ⊢ omega - d0(f) : C1
```

#### 9.3 Solver typing

```text
Γ ⊢ P     : Graph
Γ ⊢ omega : C1
────────────────────
Γ ⊢ solve_l1(P, omega) : SolveResult
```

With projections:

```text
solve_l1(P, omega).f_star : C0
solve_l1(P, omega).h1     : C1
solve_l1(P, omega).phi1   : Real
```

#### 9.4 Norm typing

```text
Γ ⊢ x : Ck
────────────
Γ ⊢ norm1(x) : Real
```

For multi-channel:

```text
Γ ⊢ x : Ck[g]
──────────────
Γ ⊢ norm_g[g](x) : Real
```

#### 9.5 Gamma typing

```text
Γ ⊢ K  : Complex2
Γ ⊢ h1 : C1
──────────────
Γ ⊢ gamma2(K, h1) : Real
```

If no 2-complex is supplied, `gamma2` is ill-typed.

#### 9.6 Projection typing

```text
Γ ⊢ omega : C1
Γ ⊢ pi_Z  : Projection(C1 \to C1)
──────────────────────────────
Γ ⊢ project[pi_Z](omega) : C1
```

#### 9.7 Xi typing

```text
Γ ⊢ h1_star : C1
Γ ⊢ phi_star : C1
────────────────────────
Γ ⊢ xi(rho(h1_star), rho(phi_star)) : Real
```

`rho` and `xi` are opaque in this paper. The internal definition of `rho` belongs to Paper 013, and the internal definition of `xi` belongs to Paper 009 (the Dual-Witness $\Xi$ construction), elaborated in Paper 013.

### 10. Operational Semantics

Evaluation is deterministic except where a solver has multiple minimizers. In that case the interpreter must either:

1. return a canonical minimizer, or
2. return a nondeterminism error, or
3. accept an explicit tie-breaking policy.

Silent arbitrary minimizer selection is forbidden.

#### 10.1 Environment

An evaluation environment contains:

```text
Env = {
    graph        : Graph,
    complex2?    : Complex2,
    gauge        : Gauge,
    projections  : ProjectionSet,
    config       : DescentConfig
}
```

#### 10.2 Values

```text
Value ::=
    Real(f64)
  | Bool(bool)
  | Cochain0(Vec<f64>)
  | Cochain1(Vec<f64>)
  | Cochain2(Vec<f64>)
  | SolveResult { f_star, h1, phi1 }
  | Coordinates { phi1, gamma2, rcl, xi }
  | Decision { Accept | Reject, reason }
```

#### 10.3 Evaluation relation

Write:

$$
\langle E, \rho \rangle \Downarrow v
$$

meaning expression $E$ evaluates under runtime environment $\rho$ to value $v$.

> **Notation warning.** This $\rho$ is the *runtime environment*, and is unrelated to the opaque density map $\rho$ of §4 and §9.7 (and the `rho` operator of §8.5). The collision is inherited from two source conventions; the two never occur in the same expression. A paper about typed degree discipline should not overload a symbol, and this one does — flagged rather than silently renamed, since the names are load-bearing in the cited code and Lean.

#### 10.4 Core evaluations

##### Coboundary

```text
⟨d0(f), ρ⟩ ⇓ apply_d0(ρ.graph, f)
```

##### Closure

```text
⟨d1(omega), ρ⟩ ⇓ apply_d1(ρ.complex2, omega)
```

If `complex2` is absent:

```text
error: d1 requires explicit 2-cell complex
```

##### Solver

```text
⟨solve_l1(P, omega), ρ⟩ ⇓ solve_l1_hodge(P, omega)
```

The implementation name `solve_l1_hodge` is historical. In this DSL it denotes an $\ell^1$ quotient solver returning a primal residual, not an $\ell^2$ Hodge projection.

Returns:

```text
{
  f_star,
  h1,
  phi1 = norm1(h1)
}
```

##### Primary obstruction

```text
⟨phi1(P, omega), ρ⟩ ⇓ solve_l1(P, omega).phi1
```

##### Closure defect

```text
⟨gamma2(K, h1), ρ⟩ ⇓ norm1(apply_d1(K, h1))
```

##### Closure ratio

```text
ratio(gamma, phi, eps):
    if phi > eps:
        return gamma / phi
    if gamma <= eps:
        return 0
    else:
        return +\infty
```

##### Projection

```text
project[pi_Z](omega):
    return pi_Z(omega)
```

Projection must satisfy:

```text
pi_Z(pi_Z(x)) = pi_Z(x)
pi_Z(d0(f)) = 0
```

If these invariants fail during tests, the projection implementation is invalid.

### 11. Evaluator Semantics

The DSL may construct coordinates but may not override evaluator law.

```text
coords_before = coords(phi1=..., gamma2=..., rcl=..., xi=...)
coords_after  = coords(phi1=..., gamma2=..., rcl=..., xi=...)
eval(coords_before, coords_after, config)
```

Evaluation delegates to the external evaluator.

#### 11.1 Guarded descent law

The $\varepsilon$-form is an implementation policy for numerical evaluation. In exact mathematics, the guarded order is strict lexicographic descent with $R_{cl}$ defined only when $\Phi_1>0$.

Let:

$$
old=(\Phi,\Gamma,R,\Xi),\quad new=(\Phi',\Gamma',R',\Xi')
$$

Accept iff:

1.

$$
\Phi' < \Phi - \varepsilon
\quad\text{and}\quad
R' \le R_{\max}+\varepsilon
$$

or 2.

$$
|\Phi'-\Phi|\le \varepsilon
\quad\text{and}\quad
\Gamma' < \Gamma-\varepsilon
\quad\text{and}\quad
R' \le R_{\max}+\varepsilon
$$

or 3.

$$
|\Phi'-\Phi|\le \varepsilon
\quad\text{and}\quad
|\Gamma'-\Gamma|\le \varepsilon
\quad\text{and}\quad
\Xi' < \Xi-\varepsilon
\quad\text{and}\quad
R' \le R_{\max}+\varepsilon
$$

Reject otherwise.

### 12. Example Programs

#### 12.1 Compute primary obstruction

```text
let s:SolveResult = solve_l1(P, omega) in
s.phi1
```

#### 12.2 Compute closure defect

```text
let s:SolveResult = solve_l1(P, omega) in
gamma2(K, s.h1)
```

#### 12.3 Full coordinate construction

```text
let s:SolveResult = solve_l1(P, omega) in
let hZ:C1 = project[pi_Z](omega) in
let gamma:Real = gamma2(K, s.h1) in
let r:Real = ratio(gamma, s.phi1, eps) in
let x:Real = xi(rho(h1_star), rho(phi_star)) in
coords(phi1=s.phi1, gamma2=gamma, rcl=r, xi=x)
```

#### 12.4 Candidate evaluation

```text
let before:Coordinates = compute_coords(P, K, omega_before) in
let after:Coordinates  = compute_coords(P, K, omega_after) in
eval(before, after, config)
```

### 13. Rewrite Rules

The interpreter may simplify expressions using sound rewrite rules.

#### Exactness

$$
d_1(d_0(f)) \to 0
$$

#### Projection idempotence

$$
\pi_Z(\pi_Z(x)) \to \pi_Z(x)
$$

#### Projection kills exact components

$$
\pi_Z(d_0(f)) \to 0
$$

#### Gamma simplification

$$
d_1(h_1)=0 \Rightarrow \gamma2(h_1)=0
$$

### 14. Rejected Programs

These must fail type checking.

```text
d0(omega)
```

Reason:

```text
d0 expects C0, got C1
```

```text
d1(f)
```

Reason:

```text
d1 expects C1, got C0
```

```text
gamma2(P, h1)
```

Reason:

```text
gamma2 requires Complex2, got Graph
```

```text
eval(phi1_before, phi1_after)
```

Reason:

```text
eval requires full Coordinates
```

### 15. Interpreter Safety Rules

The DSL interpreter must enforce:

1. No solver mutates the graph.
2. No expression computes acceptance except `eval`.
3. No transport operator may call `eval`.
4. No weighted scalar score may replace the evaluator.
5. No missing `Complex2` may be silently treated as $\Gamma_2=0$.
6. No nondeterministic solver minimizer may be silently accepted.
7. No projection may be called canonical unless its invariants are tested.

### 16. Final DSL Statement

$$
\boxed{
d_0 \text{ and } d_1 \text{ operate between distinct cochain degrees}; \pi_Z : C^1 \to C^1 \text{ is a declared degree-preserving } C^1 \text{ projection whose rewrite use requires certified idempotence and exact-killing invariants.}
}
$$

**Lean support note (v2.0.7).** The diagnostic/acceptance boundary is mechanized as `PaperFOC006.diagnostic_local_green_not_acceptance_authority`: a local quotient that preserves diagnostic constructibility does not also determine acceptance authority. `PaperFOC006.no_eval_no_acceptance` records the finite fail-closed gate: without `eval`, no acceptance is authorized. The composite theorem `PaperFOC006.degreeDsl_local_green_not_global_gate` packages the degree and DSL gates together: a local quotient preserving `(C1, diagnosticConstructible)` still cannot carry `(Gamma2, acceptanceAuthorized)`. The reusable primitive theorem elaborated in this package is `PaperFOC006.PrimitiveDifference.localGreenGlobalRed_context_obstruction_of_witness`: an arbitrary context coordinate does not create a quotient factor when the underlying local relation holds and the global readout differs. `PaperFOC006.contextual_local_green_not_global_gate` specializes that pattern to the PaperFOC006 local fingerprint and global gate. `PaperFOC006.contextual_local_fingerprint_ignores_context_replacement` and `PaperFOC006.contextual_global_gate_ignores_context_replacement` show that replacing the context does not change either reading. `QM.PaperFOC006DegreeBridge` is not a source in this package. Q admission, `QHeld`, and `TerminalWithinScope` are not theorems of this package. The package constructs no quantum mechanics, selects no Born rule, and mints no authority.

> **Scope of the word "QM" here.** This package does not contain `QM.PaperFOC006DegreeBridge`. Context metadata in the finite Python check is an opaque dictionary. Replacing it leaves the local fingerprint and the gated readout unchanged, and a complex with no 2-cell still has no $\Gamma_2$ readout. No Hilbert space, density operator, CPTP map, trace, or Born structure is constructed. Q admission is outside the proved statement.

## Implementation Note

Implementation names are registry pointers as of the v2.0.7 snapshot, and they are **unverified unless stated otherwise below**. Build status, conformance tests, and current API names must be checked separately. Known-stale at this snapshot: `apply_d1` (§1) and `apply_d0` (§10.4) do not exist in the active crates under those names; `solve_l1_hodge` (§10.4) exists only as `solve_l1_hodge_primal_dual`; and `cycle_space_projector.rs` (§3) is ambiguous between two crates. A stale pointer weakens the implementation claim it supports; it does not affect any mathematical statement in this paper, none of which depends on a code path.

**Mechanical conformance note (v2.0.4).** PL-012-1 is discharged by the companion conformance test suite (see claim ledger). The suite now pins the §14 rejected-program and §15 safety boundaries as executable checks: degree-confused `d0` rows/columns are rejected; missing `Complex2` is rejected by an explicit `Complex2InputQ::Missing` gate; a declared empty `C2` is distinguished from absence; malformed declared `d1` rows/columns are rejected; residuals at the wrong degree are rejected; the cochain invariant `d1 ∘ d0 = 0` is enforced; `Gamma2` is produced only through `Gamma2Functional::try_compute_exact_quotient` after validated complex/residual construction; and the guarded evaluator order refuses `Gamma2` or `Xi` improvements that worsen earlier coordinates. This is Rust conformance evidence only. It does not promote the DSL into an authority layer.

## GTOC / GTLA Compliance Note

**Role:** GTOC construction/specification paper. It builds a degree-wise obstruction calculus over a declared finite graph and a typed symbolic DSL over that calculus. It is not a foundations paper, not a physics paper, and not an authority/governance paper.

**Degree:** cochain degrees $k=0,1,2$ over a declared finite connected directed graph $P=(V,E)$, plus an *optionally* declared finite 2-cell set $\sigma_2$. The degree-separation result is proved and replayed **only** for the $d_1:C^1\to C^2$ / $\Gamma_2$ instance; the general $d_k$ statement is schematic (§2).

**Consumes:** a declared $P=(V,E)$; an optional declared $\sigma_2$ with incidence $d_1$; a declared gauge $g$; a solver-declared projection $\pi_Z$ with *tested* invariants; the $\ell^1(E;g)$ norm; $\varepsilon$ tolerances as numeric policy; the external evaluator of Paper 011.

**Produces:** the graded objects $C^0,C^1,C^2$ and operators $d_0,d_1$ in construction order; the $\Gamma_2$/$k{=}1$ degree-separation result; a typed grammar and static typing rules that make degree confusion ill-typed; operational semantics; the diagnostic coordinates $(\Phi_1,\Gamma_2,R_{cl},\Xi)$ **as constructed expressions**; rewrite rules conditional on tested $\pi_Z$ invariants.

**Does not produce:** acceptance, correctness, semantic truth, or authority; a general-$k$ theorem; a mechanization of $\Phi_1$ or $R_{cl}$; a density operator, trace norm, or Hilbert structure; probability semantics; any physical interpretation; a canonical $\pi_Z$; a canonical minimizer $f^*$; a `DetectorAdequacy` certificate; a lift.

**Authority status:** **none.**

**Declared imports:** $\mathbb{R}$-valued cochains (the calculus is stated over $\mathbb{R}$; every mechanization is `Int`- or `BigRational`-valued, never real); `Density`, `trace_norm`, `rho`, `xi` as opaque declared slots (→ Papers 009 / 013); $\rho$, $\phi^*$, $\Xi$ as opaque external primitives; Paper 011's evaluator law.

**OracleNeeded / Q-gated items:** instantiation of `Density` / `trace_norm` / `rho` / `xi`; any density lift or Hilbert/trace reading; the internal definitions of $\rho$, $\phi^*$, $\Xi$; the `Operator` / `DensityState` slots of `QM.PaperFOC006DegreeBridge` (opaque type variables — nothing quantum is constructed *or* imported there).

**GTLA boundary:** this paper diagnoses, types, and routes inside a declared obstruction regime. It mints no authority. `eval` (§11) *authorizes acceptance within the evaluator's own declared scope only* — that is a `ContractAuthority`-shaped, verifier-scoped gate owned by Paper 011, not a `SemanticAuthority` and not a claim about the world. Authority typing and `IsAuth` are owned by CODA-FDA; terminalization discipline by GTLA; this paper owns neither.

**Mechanization status:** **[MECHANIZED-PARTIAL]** — see the mechanization-scope note in §2 and the firewall below.

**Remaining open obligations:** general-$k$ degree separation (schematic, unproved); $\Phi_1$/$R_{cl}$ mechanization (absent); an $\mathbb{R}$-valued mechanization (all current artifacts are `Int`/$\mathbb{Q}$); a `DetectorAdequacy` certificate for the $(\Phi_1,\Gamma_2,R_{cl},\Xi)$ profile; re-verification of the stale code pointers listed in the Implementation Note.

### GTOC obstruction packet

| Field | Declaration |
|:---|:---|
| `ObstructionRegime(k)` | $k=1$: closure failure of $h_1\in C^1$ against a declared $\sigma_2$ (with $k=0$ available for $\Phi_1$). |
| $C^k, C^{k+1}, C^{k+2}$ | $C^0=\mathbb{R}^{\lvert V\rvert}$, $C^1=\mathbb{R}^{\lvert E\rvert}$, $C^2=\mathbb{R}^{\lvert\sigma_2\rvert}$ — the last existing **only** if $\sigma_2$ is declared. |
| $d_k, d_{k+1}$ | $d_0:C^0\to C^1$, $d_1:C^1\to C^2$ (§1). $d_1$ exists only with $\sigma_2$. |
| $d_1\circ d_0=0$ | **Assumption, tested per instance** — not a globally unconditioned theorem. It holds iff the supplied incidence conventions are compatible; a DSL implementation must test it for each `Complex2` (§1), and the Rust gate enforces it (`CochainIdentityViolation`). Mechanized for the compatible $C_3$ instance only (`PaperFOC006.c3_d1_d0_zero`). |
| ZeroRel / local sameness | The $C^1$-only local sameness relation $\delta(x,y) \equiv (x.c1 = y.c1)$ of `PaperFOC006.c1LocalPD`, and its composite/contextual refinements. These are the declared local fingerprints under which the LGGR non-factorization results are stated. |
| Observer / gauge / norm | Gauge $g$ declared on channel space; norm $\ell^1(E;g)$ declared and **load-bearing** (§6: relaxing it destroys sign/orientation data); $\pi_Z$ solver-declared, non-canonical, non-unique. |
| Lift policy | **Refused.** This paper considers no lift. A nonzero $\Gamma_2$ (active closure failure) or a $\Gamma_2=0$ closed survivor may *trigger* lift consideration elsewhere; neither licenses one. A lift additionally requires an obstruction witness, a preservation witness, a non-destruction check, a budget/authority boundary, and a terminalizer route — none supplied here. |
| Terminal policy | **Refused.** "This calculus defines expressions only. It does not define acceptance or correctness" (§4). Terminalization is external (Paper 011). |

**Classification mapping.** In GTOC vocabulary the coordinates route as: $\Phi_1=0$ → `ExactRepair`; $\Phi_1>0,\ \Gamma_2=0$ → `ClosedSurvivor`; $\Phi_1>0,\ \Gamma_2>0$ → `ActiveClosureFailure`; **no declared $\sigma_2$** → `NoRule / Refused` (*not* `ExactRepair`, and emphatically not $\Gamma_2=0$ — see §4 and §15 rule 5); instantiation of a `Density`/`trace_norm` slot → `OracleNeeded`. The cohomological part of this classification is three-way; `NoRule / Refused` is a fourth **routing** outcome, not a fourth cohomology class.

**Authority:** none. This paper may diagnose, price, route, or construct structure inside a declared obstruction regime. It does not mint authority. Any authority-bearing use requires a separate CODA-FDA / GTLA descent packet, terminalizer, evidence ceiling, replay witness, and `IsAuth` guard.

**Formalization-status firewall.** Any Lean, Rust, or replay artifact cited here supports only the exact finite statement it mechanizes. It does not automatically discharge PL-GTOC, Q, continuum, physical-realization, or GTLA authority obligations. A status upgrade requires an explicit theorem-ledger mapping, hypotheses check, build receipt, axiom/sorry audit, and adversary acceptance. Concretely for this paper: the Lean artifacts are `Int`-valued and cover the $\Gamma_2$ half of the $C_3$ replay only; $\Phi_1$, $R_{cl}$, the $\ell^1$ minimization, and every $\mathbb{R}$-valued statement in §1–§7 are **unmechanized**; and the Rust suite is conformance evidence for the implementation, not evidence for a theorem.

**Import / Oracle boundary.** Any use of Hilbert space, Born uniqueness, phase, continuum, probability semantics, dynamics, physical interpretation, tensor composition, or empirical realization is an imported representation structure unless explicitly constructed at this paper's declared degree. Imported structures are not DDA operations and do not produce authority. This paper constructs **none** of them: `Density`, `trace_norm`, `rho`, `xi`, $\rho$, $\phi^*$, and $\Xi$ are declared slots and opaque primitives (see the §8.1 import fence), and the $\mathbb{R}$-valued ambient of $C^k$ is itself declared, not constructed.

**Detector adequacy warning.** A replayable detector/profile is not automatically adequate for a claim. A collapsing detector can make every profile exact. Any authority-bearing GTLA use requires a `DetectorAdequacy` certificate naming the protected distinctions, adversarial cases, and known blind spots for the declared claim scope. This paper supplies **no** such certificate, and its own degree-separation theorem exhibits the paradigm blind spot: a $C^1$-only detector cannot see $\Gamma_2$ at all, so a profile that looks green under a $C^1$-only detector carries no information about closure failure. §15 rule 5 blocks the worst collapse (a missing `Complex2` must never read as $\Gamma_2=0$), but the adequacy of a *supplied* $(\Phi_1,\Gamma_2,R_{cl},\Xi)$ profile for any particular claim is neither established nor claimed here.

### Genesis-Bias Fence — No Prior State-Space

This paper does not begin with a global ambient state space, an ambient manifold, a physical system, a sample space, a Hilbert space, an observer, a temporal order, or a possibility domain. It begins with a **declared finite graph** $P=(V,E)$ and, separately and optionally, a **declared finite 2-cell attachment** $\sigma_2$ (§1).

The central object — the closure defect $\Gamma_2=\|d_1h_1\|_{1;g}$ — is defined from packet-local data only: a residual $h_1\in C^1$ obtained from a declared solver, and an incidence operator $d_1$ that exists **only because $\sigma_2$ was declared**. There is no prior 2-cell structure waiting to be discovered in $(V,E)$: attaching $\sigma_2$ is an admission, and the paper's central result is precisely that this admission is not recoverable from $C^1$ data (§2).

Common stronger readings, priced: (i) *"$\Gamma_2$ is a property of the graph"* — false; it is a property of the declared pair $(P,\sigma_2)$, and $\sigma_2$ is not induced by $P$. (ii) *"a missing 2-cell means there is no closure defect"* — refused; a missing $\sigma_2$ yields **no readout**, not a zero (§4, §15 rule 5). (iii) *"the cochain degrees are ontological levels"* — refused; they are declared grading positions in an admitted complex. (iv) *"the $\mathbb{R}$ ambient is given"* — no; it is a declared scalar specialization, and no mechanized artifact here uses it.

> **GENESIS-BIAS AUDIT.** Does this section explain degree-wise obstruction by presupposing a prior container, substrate, state-space, law, observer, temporal order, possibility domain, sample space, Hilbert space, physical system, or authority source? If so, declare and price that antecedent, replace it with packet-local data, or stop with an OBSTRUCTION.

## Falsifiability

The degree-separation claim is falsified by exhibiting a faithful reconstruction of $\Gamma_2=\|d_1 h_1\|_1$ from $C^1$ data alone, with no explicit 2-cell incidence $d_1$. The typing discipline is falsified by a well-typed DSL program that computes acceptance outside `eval`, or that treats a missing `Complex2` as $\Gamma_2=0$. The §6 information-loss claim is falsified only by a specified aggregation scheme that both departs from the $\ell^1$-edge decomposition and nevertheless preserves the sign, orientation, and edge-local decomposition data needed by the DSL.

## Related Work and Positioning

1. **Discrete exterior calculus / discrete de Rham** [1, 2]: the graded complex $C^0\to C^1\to C^2$ and $d_1\circ d_0=0$ are standard; the contribution is treating the operators as typed DSL primitives with degree-checked composition.
2. **Typed / graded term languages and static typing** [3]: invalid degree composition is rejected before execution, in the spirit of typed lambda calculi.
3. **Cellular sheaves and sheaf Laplacians** [4]: degree-wise diagnostics generalize to sheaf cochains; here the paper stays at the constant-sheaf graph level.
4. **Companion corpus papers** 006 ($\Phi_1$), 009 ($\Xi$ as external primitive), 011 (evaluator) [5].

## References

1. Carroll, J. H. (2026). *Primitive Axiomatics of Finite Obstruction Calculus.* Zenodo. <https://zenodo.org/records/20651224>

2. M. Desbrun, E. Kanso, and Y. Tong, "Discrete differential forms for computational modeling," in *Discrete Differential Geometry*, Birkhäuser, 2008.

3. B. C. Pierce, *Types and Programming Languages*, MIT Press, 2002.

4. J. Hansen and R. Ghrist, "Toward a spectral theory of cellular sheaves," *Journal of Applied and Computational Topology* **3** (2019), 315–358.

5. J. H. Carroll, "$\ell^1$-Native Cohomology of Defect Fields" (<https://zenodo.org/uploads/20186523>); "Conditional Density Lift and Dual-Witness Ξ Functional" (<https://zenodo.org/records/20192297>); "Operator Dynamics and Structural Constraints in $\ell^1$ Obstruction Systems" (<https://zenodo.org/records/20213064>). Zenodo, 2026.

## Document History

The full chronological revision history for this monograph is maintained in the companion change log: [degree_wise_dsl_change_log.md](degree_wise_dsl_change_log.md).

