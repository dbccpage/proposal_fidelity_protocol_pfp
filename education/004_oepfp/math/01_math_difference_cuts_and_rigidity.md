---
documentation_contract: symbol-game-documentation/v1
title: 'Chapter 01: Primitive Difference, Directed Cuts, and Rigidity'
kind: mathematical-reference
audience:
- researchers
- engineers
- coding-agents
status: active
maturity: canonical
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - formal_ground_void
    - primitive_difference_witness
    - directed_cut_d2
    - symmetric_link_s2
    - relational_width_two
  prose_theorems:
    - irreflexivity_forces_inequality
    - subsingleton_refuses_witness
    - directed_cut_rigidity
    - symmetric_link_automorphism
    - invariant_boolean_classifier_constant
  lean_theorems:
    - SymbolGame.irrefl_witness_ne
    - SymbolGame.no_witness_on_subsingleton
    - SymbolGame.oriented_rigid
    - SymbolGame.swap_is_S2_automorphism
    - SymbolGame.symmetric_no_equivariant_classifier
  finite_computations: []
  declared_policies: []
  applications: []
  open_conjectures: []
coefficient_domain: "Discrete Logic / Bool"
runtime_dependency: "Chapter 00 (Mathematical Scope, Provenance, and Notation)"
governance_dependency: "None"
---

# Chapter 01: Primitive Difference, Directed Cuts, and Rigidity

**Status:** Canonical Mathematics Specification (Spine Chapter 01)
**Authority:** None. Discrete logic, relational combinatorics, and verified Lean 4 theorems.
**Lean 4 Mechanization:** namespace `SymbolGame` in [`lean4/SnTower.lean`](../../../../lean4/SnTower.lean) (library `MssnSnTower` in [`lean4/lakefile.lean`](../../../../lean4/lakefile.lean)). Source-visible statements checked by reading on 2026-10-20 at `c419cc6beb`; no Lean build was run in that check.

---

## 1. Formal Ground vs. Primitive Difference

In formalizing the initial distinction, we maintain a strict boundary between the formal ground token and the witnessed relation:

```text
<>                  = Formal ground / empty boundary presentation (the inert initial boundary)

PrimitiveDifference = Witnessed irreflexive relation (an explicit distinction connecting distinct loci)
```

> **Pedagogical Analogy Note (`[Model]`):**
> Drawing a circle in the sand provides an intuitive geometric model of Spencer-Brown's primary distinction, illustrating how a closed curve separates interior from exterior. However, this geometric canvas does **not** prove that the formal ground token `<>` already contains two named, ordered endpoints. In the formal grammar, `<>` contains zero interior characters; naming distinct endpoints and assigning orientation are explicit structural operations that require relational construction.

---

## 2. Irreflexivity Forces Inequality

Let $\alpha$ be a type, and let $R: \alpha \to \alpha \to \operatorname{Prop}$ be a binary relation. We say that $R$ is **irreflexive** if no element is related to itself:
$$\forall x \in \alpha, \quad \neg (x \, R \, x)$$

### 2.1 The Fundamental Relational Theorem

Suppose an irreflexive relation is witnessed between two elements $a$ and $b$:
$$a \, R \, b$$

What can be deduced about $a$ and $b$?

$$\boxed{a \, R \, b \;\wedge\; \operatorname{Irrefl}(R) \implies a \neq b}$$

*Proof:* If $a = b$, substituting $a$ for $b$ in $a \, R \, b$ yields $a \, R \, a$, which directly contradicts the hypothesis $\neg (a \, R \, a)$. Therefore, $a \neq b$.

### 2.2 Subsingletone Carriers Refuse Witnesses

Suppose a carrier $\alpha$ has at most one element (a subsingleton: $\forall x, y \in \alpha, x = y$). Can an irreflexive relation ever be witnessed on $\alpha$?

If $a, b \in \alpha$ satisfy $a \, R \, b$, then subsingleton structure forces $a = b$, giving $a \, R \, a$, a contradiction.

$$\boxed{\text{A universe with only 1 element cannot host any witnessed irreflexive relation.}}$$

The minimal non-empty carrier capable of hosting a witnessed irreflexive distinction is therefore a set of size 2, such as the Booleans:
$$\mathbb{B} = \{\mathrm{false}, \mathrm{true}\}$$

---

## 3. Directed Cuts ($D_2$) vs. Symmetric Links ($S_2$)

On the minimal carrier $\mathbb{B} = \{\mathrm{false}, \mathrm{true}\}$, there are two elementary distinction relations:

### 3.1 The Directed Cut $D_2$
The directed cut is defined as the single oriented, irreflexive transition:
$$D_2(x, y) \iff (x = \mathrm{false} \;\wedge\; y = \mathrm{true})$$

Notice that $D_2(\mathrm{false}, \mathrm{true})$ holds, but $D_2(\mathrm{true}, \mathrm{false})$ is false. We write the directed cut as the pointed transition:
$$\mathrm{false} \longrightarrow \mathrm{true}$$
*(Orientation is denoted $a \to b$; the symbol $>$ is avoided unless an explicit order relation has been declared on the carrier).*

### 3.2 The Symmetric Link $S_2$
The symmetric link checks mutual distinction without orientation:
$$S_2(x, y) \iff (x \neq y)$$
Here, $S_2(\mathrm{false}, \mathrm{true}) = S_2(\mathrm{true}, \mathrm{false}) = \mathrm{true}$.

---

## 4. Rigidity and Permutation Symmetry

An automorphism of a relational structure $(\mathbb{B}, R)$ is a bijection $g: \mathbb{B} \to \mathbb{B}$ preserving and reflecting $R$:
$$\forall x, y \in \mathbb{B}, \quad R(x, y) \iff R(g(x), g(y))$$

### 4.1 Rigidity of $D_2$
Suppose $g: \mathbb{B} \to \mathbb{B}$ preserves and reflects $D_2$. Then:
$$D_2(g(\mathrm{false}), g(\mathrm{true})) \iff D_2(\mathrm{false}, \mathrm{true}) = \mathrm{true}$$
By definition of $D_2$, this forces $g(\mathrm{false}) = \mathrm{false}$ and $g(\mathrm{true}) = \mathrm{true}$. Thus, $g = \mathrm{id}_{\mathbb{B}}$.

$$\boxed{\operatorname{Aut}(D_2) = \{\mathrm{id}\}}$$

The directed cut $D_2$ is **rigid**: it eliminates all non-trivial permutation symmetry. Source and sink are structurally distinguishable.

### 4.2 Symmetries of $S_2$
For the symmetric link $S_2$, the Boolean negation map $\tau(x) = \neg x$ swaps $\mathrm{false}$ and $\mathrm{true}$ while preserving inequality:
$$x \neq y \iff \neg x \neq \neg y$$
Thus, $\tau \in \operatorname{Aut}(S_2)$, giving:
$$\operatorname{Aut}(S_2) \cong \mathbb{Z}_2$$

Consequently, any Boolean classifier $f: \mathbb{B} \to \mathbb{B}$ invariant under the swap $\tau$ ($f(\neg x) = f(x)$) must satisfy $f(\mathrm{false}) = f(\mathrm{true})$ and is therefore **constant**.

> **Invariance vs. Equivariance Invariant:**
> An **invariant** Boolean classifier cannot distinguish swapped inputs when the target carries the trivial action ($f(\tau x) = f(x)$). In contrast, an **equivariant** map satisfies $f(\tau x) = \tau f(x)$. If the target carrier $\mathbb{B}$ also carries the non-trivial swap action, non-constant equivariant maps exist (for example, the identity map $\mathrm{id}_{\mathbb{B}}$ satisfies $\neg x = \neg x$ and is equivariant, but is non-constant and non-invariant since $\mathrm{id}(\neg x) \ne \mathrm{id}(x)$). The structural obstruction is that a symmetric link cannot host a non-constant *invariant* distinction.

---

## 5. Formal Mechanization in Lean 4

All theorems of this chapter have Lean 4 statements without third-party dependencies. The block below is a lightly edited transcription. The source file [`lean4/SnTower.lean`](../../../../lean4/SnTower.lean) differs in two details: the relation `r` is an explicit argument in `irrefl_witness_ne` and `no_witness_on_subsingleton`, and Theorem 1.4b is named `symmetric_no_equivariant_classifier` there (its statement is about classifiers *invariant* under the swap, as below). Cite the source names.

```lean
namespace SymbolGame

/-- Theorem 1.1 (`irrefl_witness_ne`): If `r` is irreflexive and `r a b` holds, then `a ≠ b`. -/
theorem irrefl_witness_ne {α : Type} {r : α → α → Prop} (hirr : ∀ x, ¬ r x x)
    {a b : α} (hab : r a b) : a ≠ b := by
  intro h
  subst h
  exact hirr a hab

/-- Theorem 1.2 (`no_witness_on_subsingleton`): A subsingleton carrier admits no
witnessed irreflexive relation. `Bool` is the minimal non-empty carrier. -/
theorem no_witness_on_subsingleton {α : Type} {r : α → α → Prop} (hirr : ∀ x, ¬ r x x)
    (hsub : ∀ x y : α, x = y) (a b : α) : ¬ r a b := by
  intro hab
  have h : a = b := hsub a b
  subst h
  exact hirr a hab

/-- The directed cut `D₂` on `Bool`: the oriented arc `false → true`. -/
def D2 (x y : Bool) : Prop := x = false ∧ y = true

/-- Theorem 1.3 (`oriented_rigid`): Every endomap preserving and reflecting `D₂`
is the identity. The directed cut breaks all permutation symmetry. -/
theorem oriented_rigid (g : Bool → Bool)
    (h : ∀ x y, D2 x y ↔ D2 (g x) (g y)) : ∀ x, g x = x := by
  have hft : D2 (g false) (g true) := (h false true).mp ⟨rfl, rfl⟩
  intro x
  cases x with
  | false => exact hft.1
  | true => exact hft.2

/-- The symmetric link `S₂` on `Bool`: the distinction `x ≠ y`. -/
def S2 (x y : Bool) : Prop := x ≠ y

/-- Theorem 1.4a (`swap_is_S2_automorphism`): Boolean negation is an automorphism of `S₂`. -/
theorem swap_is_S2_automorphism : ∀ x y, S2 x y ↔ S2 (!x) (!y) := by
  intro x y
  cases x <;> cases y <;> simp [S2]

/-- Theorem 1.4b (`symmetric_no_equivariant_classifier` in the source): Any Boolean function invariant
under the `S₂` transposition (trivial action on target) is constant. -/
theorem symmetric_no_equivariant_classifier (f : Bool → Bool)
    (hinv : ∀ x, f (!x) = f x) : f false = f true := by
  simpa using (hinv false).symm

end SymbolGame
```

---

## 6. Relational Arity and Width-Two Discipline

The designation **width two** refers to the **relational arity** of the binary relation constructor: every elementary distinction relation takes two arguments:
$$\langle a \, R \, b \rangle \quad \text{with } a \neq b$$

> **Discipline Invariant (Generators vs. Relations):**
> Binary relational arity does **not** force two new vertices to be created at every step of a graph complex. A binary relation can connect two already-admitted vertices (such as adding an edge or chord to an existing cycle) or attach a single new vertex to an existing node. The width-two property characterizes the arity of the predicate ($R \subseteq V \times V$). A sequence of disjoint generator pairs ($\{2n, 2n+1\}$) models only the specific free tower construction where each stage adjoins an independent minimal distinction.

---

## Appendix A: Embedding in Tarski Relation Algebras ($\mathcal{RA}$)

The primitive distinctions embed into Tarski's formal calculus of binary relations:
1. **Identity Element ($1'$):** The diagonal relation $\Delta = \{(x, x) : x \in \alpha\}$.
2. **Strict Diagonal Excision:** An irreflexive relation satisfies $R \land 1' = 0$ (empty intersection with the identity relation).
3. **Converse ($\breve{R}$):** Transposition $\breve{R}(x, y) \iff R(y, x)$.
4. **Relative Composition ($R ; S$):** $(R ; S)(x, z) \iff \exists y, R(x, y) \land S(y, z)$.
5. **Symmetrization:** The symmetric link decomposes into the join of a directed cut and its converse:
   $$S_2 = D_2 \lor \breve{D}_2$$

---

## Appendix B: Abstract Reduction Systems & Confluence

When directed transitions $a \to b$ represent computational rewrites, they form an Abstract Reduction System $(A, \to)$:
1. **Rewrite Step Determinism:** A redex position alone does not determine a rewrite outcome (for example, at position 0, rules $ab \to a$ and $ab \to b$ produce different terms from the same redex). Individual rewrite steps must be indexed by a complete step witness tuple:
   $$\sigma = (\mathtt{rule\_id}, \mathtt{position}, \mathtt{matching\_substitution}, \mathtt{ruleset\_version})$$
   If an operational evaluator chooses one legal step deterministically among competing redexes, declare and verify its selection policy (e.g., outermost-leftmost priority) separately from the underlying relational rewrite relation. Confluence remains a distinct global property.
2. **Well-Founded Termination:** Orientation $a \to b$ alone does not ensure termination if cycles exist. In our declared bounded-carrier setting, termination is established by a strictly decreasing natural ranking function $\mu: A \to (\mathbb{N}, <)$ such that $x \to y \implies \mu(y) < \mu(x)$. For arbitrary or infinitely-branching reduction systems, a more general well-founded poset $(W, \prec)$ is required. Step limits serve as host execution cutoffs, not as mathematical replacements for well-foundedness.
3. **Confluence via Newman's Lemma:** Under well-founded termination, local confluence implies global confluence. Divergent rewrite branches must have joinable peak completions.
