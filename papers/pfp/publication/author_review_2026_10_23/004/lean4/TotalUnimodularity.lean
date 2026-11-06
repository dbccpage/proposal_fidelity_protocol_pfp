/-!
# Total Unimodularity and Simplicial Coboundary Operators for Paper 032

Formalizes:
1. Directed edges over a finite vertex set with irreflexivity (u ≠ v).
2. Simplicial boundary operator entries: +1 at target, -1 at source, 0 elsewhere.
3. Total unimodularity signed column-sum criterion: for any row subset J, the column sum
   is in {-1, 0, 1}.
4. Coboundary operator and zero defect equivalence.
-/

namespace SymbolGame

/-- Directed edge in a finite relational constraint graph with strict irreflexivity. -/
structure DirectedEdge (V : Type) where
  source : V
  target : V
  irreflexive : source ≠ target

/-- Value of the node-edge incidence operator ∂₁ at vertex v and edge e. -/
def incidenceEntry {V : Type} [DecidableEq V] (v : V) (e : DirectedEdge V) : Int :=
  if v = e.target then 1
  else if v = e.source then -1
  else 0

/-- An incidence column has exactly one +1 and one -1, and zeroes elsewhere. -/
theorem incidenceEntry_target {V : Type} [DecidableEq V] (e : DirectedEdge V) :
    incidenceEntry e.target e = 1 := by
  unfold incidenceEntry
  split
  · rfl
  · contradiction

theorem incidenceEntry_source {V : Type} [DecidableEq V] (e : DirectedEdge V) :
    incidenceEntry e.source e = -1 := by
  unfold incidenceEntry
  split
  · rename_i h
    exact (e.irreflexive h).elim
  · split
    · rfl
    · contradiction

theorem incidenceEntry_other {V : Type} [DecidableEq V] (v : V) (e : DirectedEdge V)
    (h_not_tgt : v ≠ e.target) (h_not_src : v ≠ e.source) :
    incidenceEntry v e = 0 := by
  unfold incidenceEntry
  have ht : ¬(v = e.target) := h_not_tgt
  have hs : ¬(v = e.source) := h_not_src
  simp [ht, hs]


/-- Total Unimodularity Signed Column-Sum Criterion:
For any subset J of rows, the sum of column entries belongs to {-1, 0, 1}.
We formalize this membership for any indicator function `inJ : V → Bool`. -/
def columnSumOnSubset {V : Type} [DecidableEq V] (inJ : V → Bool) (e : DirectedEdge V) : Int :=
  (if inJ e.target then 1 else 0) + (if inJ e.source then -1 else 0)

theorem columnSum_bounded {V : Type} [DecidableEq V] (inJ : V → Bool) (e : DirectedEdge V) :
    columnSumOnSubset inJ e = 1 ∨ columnSumOnSubset inJ e = 0 ∨ columnSumOnSubset inJ e = -1 := by
  unfold columnSumOnSubset
  cases inJ e.target <;> cases inJ e.source
  · right; left; rfl
  · right; right; rfl
  · left; rfl
  · right; left; rfl

/-- Discrete simplicial coboundary on vertex potential: (δ c₀)(e) = c₀(target) - c₀(source). -/
def coboundary {V : Type} (c₀ : V → Int) (e : DirectedEdge V) : Int :=
  c₀ e.target - c₀ e.source

/-- Primary obstruction vanishing condition: coboundary equals edge weight vector. -/
theorem zero_defect_iff_exact {V : Type} (c₀ : V → Int) (W_E : DirectedEdge V → Int) :
    (∀ e : DirectedEdge V, coboundary c₀ e - W_E e = 0) ↔
    (∀ e : DirectedEdge V, coboundary c₀ e = W_E e) := by
  constructor
  · intro h e
    have he := h e
    exact Int.eq_of_sub_eq_zero he
  · intro h e
    have he := h e
    exact Int.sub_eq_zero_of_eq he

end SymbolGame
