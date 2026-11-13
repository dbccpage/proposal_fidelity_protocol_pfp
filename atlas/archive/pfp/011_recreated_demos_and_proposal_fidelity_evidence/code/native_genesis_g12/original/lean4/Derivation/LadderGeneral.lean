import Derivation.HigherStructure

/-!
# The uniform guarded filler at arbitrary finite dimension

Generalization of the hard-coded `HigherStructure` cell calculus
(dimensions 0–3) to every finite dimension: a dimension-indexed
complex, one WELL-FORMED shell guard uniform in the dimension —
exact arity, strict ascent (no repeated vertices), complete
unfilled boundary — one admission step, and the **uniform guarded
filler theorem** (`uniform_guarded_filler`) for all `k ≥ 1`: a
complete well-formed unfilled boundary admits its filler, and the
admission strictly extends the complex.

Scope, exactly: this is a theorem about the declared guarded step —
dimension-uniform filler admission and strict extension — and
nothing more.  It is NOT a homology claim.  The review-pass
conjecture GENERAL_DIMENSIONAL_LADDER is settled only in this
narrowed sense.

The general vanishing of the composite boundary is a SEPARATE
question, and it is now settled elsewhere: `BoundaryCancellation`
proves it for every finite cell and every face
(`d2_zero_unrestricted`), by pairing the two deletion orders of each
codimension-two face and cancelling their signs.  The
dimension-bounded computation below (`d2_zero_dims_2_3_4`) is
therefore a corollary spot-check, not the evidence.  Nothing about
the filler rule forces the coefficients or the signs: without the
signs the composite is nonzero
(`BoundaryCancellation.signless_countermodel`).

The repair over the review draft: the legacy guard had no
well-formedness conjunct and admitted the repeated-vertex
pseudo-cell `[0, 0]` (`pseudo_cell_countermodel`, required); the
repaired guard refuses it, and well-formedness is proved to be an
invariant of every replay from the empty complex (`wf_nreplay`).

Imported (declared, not derived) inputs, per the standing
discipline: fresh vertex supply, the ascending-list cell encoding,
integer coefficients and the boundary sign convention, and the
metatheoretic iteration of any driver.  Protection, observer
transport, budget, and activation do not appear in this module at
all — the calculus is the declared realization layer, not the
passage.
-/

namespace LadderGeneral

/-- A dimension-indexed complex: dimension `k` carries its cells,
each a `(k+1)`-vertex ascending list. -/
structure ComplexN where
  cells : Nat → List (List Nat)

def emptyN : ComplexN := ⟨fun _ => []⟩

/-- The facets of a cell: drop one vertex each. -/
def facets (σ : List Nat) : List (List Nat) :=
  (List.range σ.length).map σ.eraseIdx

/-- Strict ascent: each vertex strictly below the next.  Ascent
excludes repeats; exact arity is the guard's separate conjunct. -/
def ascB : List Nat → Bool
  | [] => true
  | [_] => true
  | a :: b :: t => (decide (a < b)) && ascB (b :: t)

/-- The dimension-`k` shell guard, uniform in `k`: the candidate has
the right vertex count, is strictly ascending (well-formed), every
facet is present one dimension down, and the cell itself is absent —
the complete-unfilled-boundary condition at every dimension. -/
def shellN (C : ComplexN) (k : Nat) (σ : List Nat) : Bool :=
  (decide (σ.length = k + 1)) && (decide (1 ≤ k)) && ascB σ
    && (facets σ).all (fun τ => decide (τ ∈ C.cells (k - 1)))
    && !(decide (σ ∈ C.cells k))

/-- The retired guard, kept only as the countermodel's exhibit: no
well-formedness conjunct. -/
def shellNLegacy (C : ComplexN) (k : Nat) (σ : List Nat) : Bool :=
  (decide (σ.length = k + 1)) && (decide (1 ≤ k))
    && (facets σ).all (fun τ => decide (τ ∈ C.cells (k - 1)))
    && !(decide (σ ∈ C.cells k))

/-- Vertex admission (dimension 0), dedup-guarded. -/
def stepV (C : ComplexN) (v : Nat) : ComplexN :=
  if [v] ∈ C.cells 0 then C
  else ⟨fun j => if j = 0 then C.cells 0 ++ [[v]] else C.cells j⟩

/-- Cell admission at any dimension `k ≥ 1`, shell-guarded. -/
def stepN (C : ComplexN) (k : Nat) (σ : List Nat) : ComplexN :=
  if shellN C k σ then
    ⟨fun j => if j = k then C.cells k ++ [σ] else C.cells j⟩
  else C

/-- **The uniform guarded filler theorem, arbitrary finite
dimension**: at every `k`, a complete well-formed unfilled boundary
admits its filling cell, and the admission strictly extends the
complex — the two-rule shape (obstruction-shaped precondition,
structure-creating response), uniform in the dimension.  A theorem
about the declared guarded step, not a homology claim. -/
theorem uniform_guarded_filler (C : ComplexN) (k : Nat)
    (σ : List Nat) (h : shellN C k σ = true) :
    σ ∈ (stepN C k σ).cells k ∧ stepN C k σ ≠ C := by
  have hproj : (stepN C k σ).cells k = C.cells k ++ [σ] := by
    unfold stepN
    rw [if_pos h]
    show (if k = k then C.cells k ++ [σ] else C.cells k)
      = C.cells k ++ [σ]
    rw [if_pos rfl]
  constructor
  · rw [hproj]
    exact List.mem_append.mpr (Or.inr List.mem_cons_self)
  · intro heq
    rw [heq] at hproj
    have hlen := congrArg List.length hproj
    simp only [List.length_append, List.length_cons,
      List.length_nil] at hlen
    omega

/-- The shell guard is load-bearing at every dimension: without it
(any failing conjunct — wrong arity, missing facet, duplicate), the
step is inert. -/
theorem shell_refuses_general (C : ComplexN) (k : Nat)
    (σ : List Nat) (h : shellN C k σ = false) :
    stepN C k σ = C := by
  unfold stepN
  rw [if_neg (by rw [h]; exact fun hc => Bool.noConfusion hc)]

/-- The shell does not fill itself at any dimension: admission
requires the step event. -/
theorem shell_no_self_fill (C : ComplexN) (k : Nat) (σ : List Nat)
    (h : shellN C k σ = true) : ¬ (σ ∈ C.cells k) := by
  intro hmem
  unfold shellN at h
  simp only [Bool.and_eq_true, Bool.not_eq_true',
    decide_eq_false_iff_not] at h
  exact h.2 hmem

/-! ## Well-formedness: the invariant and the required countermodel -/

def oneVertex : ComplexN := stepV emptyN 0

/-- **Countermodel (required): the pseudo-cell `[0, 0]`.**  With one
vertex admitted, the LEGACY guard accepts the repeated-vertex list
`[0, 0]` as a 1-cell — both facets are the one vertex — while the
repaired guard refuses it and the repaired step is inert on it. -/
theorem pseudo_cell_countermodel :
    shellNLegacy oneVertex 1 [0, 0] = true ∧
    shellN oneVertex 1 [0, 0] = false ∧
    stepN oneVertex 1 [0, 0] = oneVertex := by
  refine ⟨by decide, by decide,
    shell_refuses_general oneVertex 1 [0, 0] (by decide)⟩

/-- Well-formedness of a complex: every admitted cell has exact
arity and strict ascent. -/
def WFComplex (C : ComplexN) : Prop :=
  ∀ k σ, σ ∈ C.cells k → σ.length = k + 1 ∧ ascB σ = true

theorem wf_empty : WFComplex emptyN := by
  intro k σ h
  cases h

theorem wf_stepV (C : ComplexN) (v : Nat) (h : WFComplex C) :
    WFComplex (stepV C v) := by
  intro k σ hm
  unfold stepV at hm
  by_cases hv : [v] ∈ C.cells 0
  · rw [if_pos hv] at hm
    exact h k σ hm
  · rw [if_neg hv] at hm
    have hm' : σ ∈ (if k = 0 then C.cells 0 ++ [[v]]
        else C.cells k) := hm
    by_cases hk : k = 0
    · subst hk
      rw [if_pos rfl] at hm'
      rcases List.mem_append.mp hm' with hmem | hmem
      · exact h 0 σ hmem
      · cases List.mem_singleton.mp hmem
        exact ⟨rfl, rfl⟩
    · rw [if_neg hk] at hm'
      exact h k σ hm'

theorem wf_stepN (C : ComplexN) (k : Nat) (σ : List Nat)
    (h : WFComplex C) : WFComplex (stepN C k σ) := by
  intro j τ hm
  unfold stepN at hm
  by_cases hs : shellN C k σ = true
  · rw [if_pos hs] at hm
    have hm' : τ ∈ (if j = k then C.cells k ++ [σ]
        else C.cells j) := hm
    by_cases hj : j = k
    · subst hj
      rw [if_pos rfl] at hm'
      rcases List.mem_append.mp hm' with hmem | hmem
      · exact h j τ hmem
      · cases List.mem_singleton.mp hmem
        unfold shellN at hs
        simp only [Bool.and_eq_true, decide_eq_true_eq] at hs
        exact ⟨hs.1.1.1.1, hs.1.1.2⟩
    · rw [if_neg hj] at hm'
      exact h j τ hm'
  · rw [if_neg hs] at hm
    exact h j τ hm

/-! ## The dimension-4 demonstration: the boundary of the
five-vertex cell, filled

The complete replay: 5 vertices, 10 edges, 10 triangles, 5
tetrahedra (each over its complete boundary), then the single
4-cell over its 5 tetrahedral facets — every admission
shell-guarded, in creation order. -/

inductive NEvent where
  | addV (v : Nat)
  | addC (k : Nat) (σ : List Nat)

def nstep (C : ComplexN) : NEvent → ComplexN
  | .addV v => stepV C v
  | .addC k σ => stepN C k σ

def nreplay (h : List NEvent) (C : ComplexN) : ComplexN :=
  h.foldl nstep C

theorem wf_nstep (C : ComplexN) (e : NEvent) (h : WFComplex C) :
    WFComplex (nstep C e) := by
  cases e with
  | addV v => exact wf_stepV C v h
  | addC k σ => exact wf_stepN C k σ h

/-- **The well-formedness invariant replays**: every complex grown
from the empty complex by guarded admissions carries only
exact-arity, strictly ascending cells — no pseudo-cell is ever
admitted. -/
theorem wf_nreplay (h : List NEvent) :
    ∀ C, WFComplex C → WFComplex (nreplay h C) := by
  induction h with
  | nil =>
      intro C hC
      exact hC
  | cons e t ih =>
      intro C hC
      show WFComplex (nreplay t (nstep C e))
      exact ih (nstep C e) (wf_nstep C e hC)

/-- Ascending selections: all `m`-element ascending sublists of a
list. -/
def combsAux : Nat → List Nat → List (List Nat)
  | 0, _ => [[]]
  | _ + 1, [] => []
  | m + 1, x :: xs =>
      (combsAux m xs).map (fun l => x :: l) ++ combsAux (m + 1) xs

/-- All `(m+1)`-vertex ascending cells over the first `n` vertices. -/
def combs (n m : Nat) : List (List Nat) :=
  combsAux (m + 1) (List.range n)

def d4Events : List NEvent :=
  ((List.range 5).map .addV)
    ++ ((combs 5 1).map (.addC 1))
    ++ ((combs 5 2).map (.addC 2))
    ++ ((combs 5 3).map (.addC 3))
    ++ [.addC 4 [0, 1, 2, 3, 4]]

def d4Complex : ComplexN := nreplay d4Events emptyN

set_option maxRecDepth 4096 in
/-- The dimension-4 instance of the ladder, replayed: every guarded
admission fired, and the top cell is present exactly over its
complete boundary. -/
theorem d4_demo :
    (d4Complex.cells 0).length = 5 ∧
    (d4Complex.cells 1).length = 10 ∧
    (d4Complex.cells 2).length = 10 ∧
    (d4Complex.cells 3).length = 5 ∧
    d4Complex.cells 4 = [[0, 1, 2, 3, 4]] := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> decide

/-- The demonstration complex is well-formed — the replayed
invariant at work at dimension 4. -/
theorem d4_wf : WFComplex d4Complex :=
  wf_nreplay d4Events emptyN wf_empty

/-- Without one tetrahedral facet the 4-shell is not complete and
the 4-cell is refused — the guard is load-bearing at dimension 4. -/
def d4MissingEvents : List NEvent :=
  ((List.range 5).map .addV)
    ++ ((combs 5 1).map (.addC 1))
    ++ ((combs 5 2).map (.addC 2))
    ++ (((combs 5 3).drop 1).map (.addC 3))
    ++ [.addC 4 [0, 1, 2, 3, 4]]

set_option maxRecDepth 4096 in
theorem d4_guard_load_bearing :
    (nreplay d4MissingEvents emptyN).cells 4 = [] := by decide

/-! ## The generalized boundary calculus (declared) and its
composite at dimensions 2–4 -/

/-- Alternating sign, declared. -/
def sgn (i : Nat) : Int := if i % 2 = 0 then 1 else -1

/-- The generalized boundary of one cell. -/
def bdN (σ : List Nat) : List (Int × List Nat) :=
  (List.range σ.length).map (fun i => (sgn i, σ.eraseIdx i))

/-- Pushforward of a chain one dimension down. -/
def pushN (ch : List (Int × List Nat)) : List (Int × List Nat) :=
  ch.flatMap (fun p => (bdN p.2).map (fun q => (p.1 * q.1, q.2)))

/-- Coefficient collection. -/
def coeffN (τ : List Nat) (ch : List (Int × List Nat)) : Int :=
  (ch.filter (fun p => p.2 == τ)).foldl (fun acc p => acc + p.1) 0

/-- The composite boundary vanishes on the demonstration cells of
dimensions 2, 3, and 4 (decided).  `BoundaryCancellation` proves the
general coefficientwise theorem; this older computation is retained
as a corollary spot-check.  Declared coefficients and signs still
carry the content. -/
theorem d2_zero_dims_2_3_4 :
    ((combs 5 2).all fun t =>
      (facets t).all fun e => coeffN e (pushN (bdN t)) == 0) = true ∧
    ((combs 5 3).all fun q =>
      (facets q).all fun t2 =>
        coeffN t2 (pushN (bdN q)) == 0) = true ∧
    ((facets [0, 1, 2, 3, 4]).all fun q =>
      (facets q).all fun t2 =>
        coeffN t2 (pushN (bdN [0, 1, 2, 3, 4])) == 0) = true := by
  refine ⟨?_, ?_, ?_⟩ <;> decide

end LadderGeneral
