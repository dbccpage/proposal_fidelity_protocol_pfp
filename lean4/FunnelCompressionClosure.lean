import FidelityAdequacy
import OperationTreeFold
/-!
# Funnel Compression, Finite Gluing, and Exact Quotient Closure (`v1.0rc`)

AuthorityEffect: None.

Core Lean `v4.35.0` formalization (zero Mathlib, zero declared axioms, zero
`sorryAx`) supporting the `omegaengine_pfp_v1.0rc` outer-loop funnel and the
Window 5 mathematical derivations for Companion Papers 015 and 016:

1. **Exact Quotient Criterion for Costed Partial Deterministic Tables**
   (`ATL-P016-001`, `ATL-P016-003`): necessary and sufficient fibre conditions
   for step/word/cost descent and reflection, plus the two-state output-preserving
   but cost-breaking counterexample.
2. **Coarsest Stable Refinement & Proper-Split Bound** (`ATL-P016-002`):
   greatest-fixed-point universality of iterative signature splitting and the
   `|X| - 1` upper bound on proper partition splits.
3. **Positive-Cost Loop Erasure & Route Counterexample** (`ATL-P016-004`):
   constructive cycle splicing strictly lowers accumulated positive cost on any
   resolving word with a repeated state, together with the three-state `r, s, t`
   table where two unit steps (`2`) beat a direct step (`5`) and a loop (`3`).
4. **Finite Local-to-Global Gluing Bijection & Boolean Cycle Obstruction**
   (`ATL-P015-001`, `ATL-P015-002`): existence, uniqueness, and mutual-inverse
   bijection between pairwise-compatible locally permitted families and global
   solutions over covered variable sets, plus the three-variable parity cycle.
5. **Four-Stage Outer-Loop Funnel Monotone Contraction & Zero-Authority Closure**:
   monotone survivor-length contraction, exact conjunction characterization,
   stage-rejection exclusion, faithful-candidate retention, and internal
   `AuthorityEffect.none` closure across Thymus, Allosteric Quorum, Exact
   Witness, and Pareto Incumbent stages.

Scope boundary: all theorems hold strictly for the declared finite/deterministic
structures and boolean/predicate gates formalized below. They do not certify
stochastic model outputs, heuristic text summaries, or operating-system sandboxes.
-/

namespace PFP.FunnelCompressionClosure

open SnSymbolGameAndPackets
open PaperER007

/-!
## 1. Costed Partial Deterministic Tables & Exact Quotient Criterion (`ATL-P016-001`, `ATL-P016-003`)
-/

/-- Deterministic partial action table with per-step costs, protected reports,
and terminal state labels. -/
structure CostedTable (State Act Cost Report : Type) where
  step : State → Act → Option (Cost × State)
  report : State → Report
  isTerminal : State → Bool
  zeroCost : Cost
  addCost : Cost → Cost → Cost

/-- Execute an action word from `s`, accumulating step costs right-associatively. -/
def execWord (T : CostedTable S A C R) : S → List A → Option (C × S)
  | s, [] => some (T.zeroCost, s)
  | s, a :: w =>
      match T.step s a with
      | none => none
      | some (c, s') =>
          match execWord T s' w with
          | none => none
          | some (cw, sf) => some (T.addCost c cw, sf)

/-- A word `w` resolves from `s` with total cost `total` iff `execWord` reaches
a terminal state with accumulated cost `total`. -/
def resolvesWithCost (T : CostedTable S A C R) (s : S) (w : List A) (total : C) : Prop :=
  ∃ sf, execWord T s w = some (total, sf) ∧ T.isTerminal sf = true

/-- One-step structural agreement on `q`-fibres: equal action enablement, equal
enabled step cost, and equal successor `q`-fibre. -/
def ActionFibreAgree (T : CostedTable S A C R) {Z : Type} (q : S → Z)
    (x y : S) (a : A) : Prop :=
  (T.step x a = none ∧ T.step y a = none) ∨
    (∃ c sx sy, T.step x a = some (c, sx) ∧ T.step y a = some (c, sy) ∧ q sx = q sy)

/-- Paper 016 §2 structural compatibility criterion on a report map `q : S → Z`. -/
def FibreCompatible (T : CostedTable S A C R) {Z : Type} (q : S → Z) : Prop :=
  ∀ x y, q x = q y →
    T.report x = T.report y ∧
      T.isTerminal x = T.isTerminal y ∧
      ∀ a, ActionFibreAgree T q x y a

/-- Witness that quotient table `Q` descends and reflects concrete operations of
`T` along `q : S → Z`. -/
structure ExactQuotientWitness (T : CostedTable S A C R) (Q : CostedTable Z A C R)
    (q : S → Z) : Prop where
  zero_eq : Q.zeroCost = T.zeroCost
  add_eq : Q.addCost = T.addCost
  report_comm : ∀ x, Q.report (q x) = T.report x
  terminal_comm : ∀ x, Q.isTerminal (q x) = T.isTerminal x
  step_disabled : ∀ x a, T.step x a = none ↔ Q.step (q x) a = none
  step_enabled : ∀ x a c sx, T.step x a = some (c, sx) → Q.step (q x) a = some (c, q sx)
  step_reflect : ∀ x a c z', Q.step (q x) a = some (c, z') →
    ∃ sx, T.step x a = some (c, sx) ∧ q sx = z'

/-- Necessity (`ATL-P016-001`): any exact quotient forces fibre compatibility of
reports, terminal labels, enablement, enabled costs, and successor fibres. -/
theorem exact_quotient_implies_fibre_compatible
    {T : CostedTable S A C R} {Q : CostedTable Z A C R} {q : S → Z}
    (hq : ExactQuotientWitness T Q q) :
    FibreCompatible T q := by
  intro x y hxy
  refine ⟨?_, ?_, ?_⟩
  · rw [← hq.report_comm x, ← hq.report_comm y, hxy]
  · rw [← hq.terminal_comm x, ← hq.terminal_comm y, hxy]
  · intro a
    cases hx : T.step x a with
    | none =>
        left
        refine ⟨hx, ?_⟩
        have hqx : Q.step (q x) a = none := (hq.step_disabled x a).mp hx
        rw [hxy] at hqx
        exact (hq.step_disabled y a).mpr hqx
    | some pair =>
        rcases pair with ⟨c, sx⟩
        right
        have hqx : Q.step (q x) a = some (c, q sx) := hq.step_enabled x a c sx hx
        rw [hxy] at hqx
        rcases hq.step_reflect y a c (q sx) hqx with ⟨sy, hy, hsy⟩
        exact ⟨c, sx, sy, hx, hy, hsy.symm⟩

/-- Constructive quotient table induced by a section/representative map `rep : Z → S`. -/
def quotientTableOfRep (T : CostedTable S A C R) (q : S → Z) (rep : Z → S) :
    CostedTable Z A C R where
  step := fun z a =>
    match T.step (rep z) a with
    | none => none
    | some (c, sx) => some (c, q sx)
  report := fun z => T.report (rep z)
  isTerminal := fun z => T.isTerminal (rep z)
  zeroCost := T.zeroCost
  addCost := T.addCost

/-- Sufficiency (`ATL-P016-001`): fibre compatibility and a representative map
`∀ x, q (rep (q x)) = q x` construct an `ExactQuotientWitness`. -/
theorem fibre_compatible_gives_exact_quotient
    {T : CostedTable S A C R} {Z : Type} {q : S → Z} {rep : Z → S}
    (hcompat : FibreCompatible T q)
    (hrep : ∀ x, q (rep (q x)) = q x) :
    ExactQuotientWitness T (quotientTableOfRep T q rep) q := by
  refine
    { zero_eq := rfl
      add_eq := rfl
      report_comm := ?_
      terminal_comm := ?_
      step_disabled := ?_
      step_enabled := ?_
      step_reflect := ?_ }
  · intro x
    exact (hcompat (rep (q x)) x (hrep x)).1
  · intro x
    exact (hcompat (rep (q x)) x (hrep x)).2.1
  · intro x a
    have hstep := (hcompat (rep (q x)) x (hrep x)).2.2 a
    constructor
    · intro hxNone
      rcases hstep with ⟨hRepNone, _⟩ | ⟨c, srx, sx, _, hxSome, _⟩
      · simp [quotientTableOfRep, hRepNone]
      · rw [hxNone] at hxSome
        cases hxSome
    · intro hqNone
      rcases hstep with ⟨_, hxNone⟩ | ⟨c, srx, sx, hRepSome, _, _⟩
      · exact hxNone
      · simp [quotientTableOfRep, hRepSome] at hqNone
  · intro x a c sx hxSome
    have hstep := (hcompat (rep (q x)) x (hrep x)).2.2 a
    rcases hstep with ⟨_, hxNone⟩ | ⟨c', srx, sx', hRepSome, hxSome', hqSucc⟩
    · rw [hxNone] at hxSome
      cases hxSome
    · rw [hxSome] at hxSome'
      cases hxSome'
      simp [quotientTableOfRep, hRepSome, hqSucc]
  · intro x a c z' hqSome
    have hstep := (hcompat (rep (q x)) x (hrep x)).2.2 a
    rcases hstep with ⟨hRepNone, _⟩ | ⟨c', srx, sx, hRepSome, hxSome, hqSucc⟩
    · simp [quotientTableOfRep, hRepNone] at hqSome
    · simp [quotientTableOfRep, hRepSome] at hqSome
      rcases hqSome with ⟨hc, hz⟩
      subst hc
      subst hz
      exact ⟨sx, hxSome, hqSucc.symm⟩

/-- Word-level descent (`ATL-P016-001`): `execWord` commutes with `q` on every
action word `w : List A`. -/
theorem exact_quotient_execWord_commutes
    {T : CostedTable S A C R} {Q : CostedTable Z A C R} {q : S → Z}
    (hq : ExactQuotientWitness T Q q) :
    ∀ (w : List A) (x : S),
      Option.map (fun p => (p.1, q p.2)) (execWord T x w) = execWord Q (q x) w
  | [], x => by
      simp [execWord, Option.map, hq.zero_eq]
  | a :: w, x => by
      cases hx : T.step x a with
      | none =>
          have hqx : Q.step (q x) a = none := (hq.step_disabled x a).mp hx
          simp [execWord, hx, hqx, Option.map]
      | some pair =>
          rcases pair with ⟨c, sx⟩
          have hqx : Q.step (q x) a = some (c, q sx) := hq.step_enabled x a c sx hx
          have ih := exact_quotient_execWord_commutes hq w sx
          cases hw : execWord T sx w with
          | none =>
              rw [hw] at ih
              simp [Option.map] at ih
              simp [execWord, hx, hqx, hw, ih.symm, Option.map]
          | some tail =>
              rcases tail with ⟨cw, sf⟩
              rw [hw] at ih
              simp [Option.map] at ih
              simp [execWord, hx, hqx, hw, ← ih, Option.map, hq.add_eq]

/-- Direct fibre invariance of word execution, accumulated cost, terminal label,
and report on `q`-equivalent states (`ATL-P016-001`). -/
theorem fibre_compatible_execWord_congr
    {T : CostedTable S A C R} {Z : Type} {q : S → Z}
    (hcompat : FibreCompatible T q) :
    ∀ (w : List A) {x y : S}, q x = q y →
      (execWord T x w = none ↔ execWord T y w = none) ∧
      (∀ c sx, execWord T x w = some (c, sx) →
        ∃ sy, execWord T y w = some (c, sy) ∧ q sx = q sy ∧
          T.report sx = T.report sy ∧ T.isTerminal sx = T.isTerminal sy)
  | [], x, y, hxy => by
      have hbase := hcompat x y hxy
      refine ⟨by simp [execWord], ?_⟩
      intro c sx hsx
      simp [execWord] at hsx
      rcases hsx with ⟨hc, hsxEq⟩
      subst hc
      subst hsxEq
      exact ⟨y, rfl, hxy, hbase.1, hbase.2.1⟩
  | a :: w, x, y, hxy => by
      have hstep := (hcompat x y hxy).2.2 a
      rcases hstep with ⟨hxNone, hyNone⟩ | ⟨cStep, sx, sy, hxSome, hySome, hqSucc⟩
      · refine ⟨by simp [execWord, hxNone, hyNone], ?_⟩
        intro c sf hImpossible
        simp [execWord, hxNone] at hImpossible
      · have ih := fibre_compatible_execWord_congr hcompat w hqSucc
        refine ⟨?_, ?_⟩
        · simp only [execWord, hxSome, hySome]
          cases hwx : execWord T sx w with
          | none =>
              have hwy : execWord T sy w = none := ih.1.mp hwx
              simp [hwy]
          | some p =>
              rcases p with ⟨cw, sfx⟩
              rcases ih.2 cw sfx hwx with ⟨sfy, hwy, _, _, _⟩
              simp [hwy]
        · intro cTotal sfx hExecX
          simp only [execWord, hxSome] at hExecX
          cases hwx : execWord T sx w with
          | none =>
              rw [hwx] at hExecX
              cases hExecX
          | some p =>
              rcases p with ⟨cw, sfx'⟩
              rw [hwx] at hExecX
              cases hExecX
              rcases ih.2 cw sfx hwx with ⟨sfy, hwy, hqFinal, hRepFinal, hTermFinal⟩
              exact ⟨sfy, by simp [execWord, hySome, hwy], hqFinal, hRepFinal, hTermFinal⟩

/-- Equal `q`-fibres have identical resolving words and accumulated resolution costs. -/
theorem fibre_compatible_preserves_resolvesWithCost
    {T : CostedTable S A C R} {Z : Type} {q : S → Z}
    (hcompat : FibreCompatible T q) {x y : S} (hxy : q x = q y)
    (w : List A) (total : C) :
    resolvesWithCost T x w total ↔ resolvesWithCost T y w total := by
  constructor
  · rintro ⟨sfx, hExecX, hTermX⟩
    rcases (fibre_compatible_execWord_congr hcompat w hxy).2 total sfx hExecX with
      ⟨sfy, hExecY, _, _, hTermEq⟩
    exact ⟨sfy, hExecY, hTermEq.symm.trans hTermX⟩
  · rintro ⟨sfy, hExecY, hTermY⟩
    rcases (fibre_compatible_execWord_congr hcompat w hxy.symm).2 total sfy hExecY with
      ⟨sfx, hExecX, _, _, hTermEq⟩
    exact ⟨sfx, hExecX, hTermEq.symm.trans hTermY⟩

/-- Carrier for Paper 016 §4's two-state cost-breaking counterexample (`ATL-P016-003`). -/
inductive TwoStateCarrier where
  | a
  | b
  | t
  deriving DecidableEq, Repr

/-- Paper 016 §4 counterexample table: `a` and `b` both report `0`, `t` reports `1`
and is terminal; `finish` (`()`) costs `1` at `a` and `3` at `b`. -/
def twoStateCostTable : CostedTable TwoStateCarrier Unit Nat Nat where
  step
    | .a, () => some (1, .t)
    | .b, () => some (3, .t)
    | .t, () => none
  report
    | .a => 0
    | .b => 0
    | .t => 1
  isTerminal
    | .a => false
    | .b => false
    | .t => true
  zeroCost := 0
  addCost := Nat.add

/-- Output-only projection collapsing `a` and `b` onto `false` and `t` onto `true`. -/
def collapseZeroReport : TwoStateCarrier → Bool
  | .a => false
  | .b => false
  | .t => true

/-- Counterexample (`ATL-P016-003`): identifying zero-report states `a` and `b`
preserves current output (`0 = 0`), has finish costs `1` and `3`, and violates
`FibreCompatible` (hence admits no exact quotient). -/
theorem output_preserving_collapse_breaks_cost :
    twoStateCostTable.report .a = twoStateCostTable.report .b ∧
      collapseZeroReport .a = collapseZeroReport .b ∧
      resolvesWithCost twoStateCostTable .a [()] 1 ∧
      resolvesWithCost twoStateCostTable .b [()] 3 ∧
      ¬ FibreCompatible twoStateCostTable collapseZeroReport := by
  refine ⟨rfl, rfl, ⟨.t, rfl, rfl⟩, ⟨.t, rfl, rfl⟩, ?_⟩
  intro hcompat
  have hstep := (hcompat .a .b rfl).2.2 ()
  rcases hstep with ⟨haNone, _⟩ | ⟨c, sx, sy, haSome, hbSome, _⟩
  · simp [twoStateCostTable] at haNone
  · simp [twoStateCostTable] at haSome hbSome
    rcases haSome with ⟨hc1, _⟩
    rcases hbSome with ⟨hc3, _⟩
    omega

/-!
## 2. Coarsest Stable Refinement & Proper-Split Bound (`ATL-P016-002`)
-/

/-- Binary state relation representing a partition/equivalence candidate. -/
abbrev StateRel (S : Type) : Type := S → S → Prop

/-- `r₁` refines `r₂` when every `r₁`-related pair is `r₂`-related. -/
def Refines {S : Type} (r₁ r₂ : StateRel S) : Prop :=
  ∀ x y, r₁ x y → r₂ x y

/-- Relational action-signature match relative to successor relation `r`. -/
def RelActionAgree (T : CostedTable S A C R) (r : StateRel S)
    (x y : S) (a : A) : Prop :=
  (T.step x a = none ∧ T.step y a = none) ∨
    (∃ c sx sy, T.step x a = some (c, sx) ∧ T.step y a = some (c, sy) ∧ r sx sy)

/-- One-step signature split operator. -/
def splitOnce (T : CostedTable S A C R) (r : StateRel S) : StateRel S :=
  fun x y =>
    r x y ∧ T.report x = T.report y ∧ T.isTerminal x = T.isTerminal y ∧
      ∀ a, RelActionAgree T r x y a

/-- A relation `r` is stable under cost-and-enablement signature splitting when
`r x y` implies `splitOnce T r x y`. -/
def IsStableRel (T : CostedTable S A C R) (r : StateRel S) : Prop :=
  Refines r (splitOnce T r)

/-- Iterative partition refinement starting from `q₀` intersected with report
and terminal-label equality. -/
def iterSplit (T : CostedTable S A C R) (q₀ : StateRel S) : Nat → StateRel S
  | 0 => fun x y => q₀ x y ∧ T.report x = T.report y ∧ T.isTerminal x = T.isTerminal y
  | k + 1 => splitOnce T (iterSplit T q₀ k)

theorem splitOnce_mono {T : CostedTable S A C R} {r₁ r₂ : StateRel S}
    (h : Refines r₁ r₂) :
    Refines (splitOnce T r₁) (splitOnce T r₂) := by
  intro x y hx
  rcases hx with ⟨hr1, hrep, hterm, hact⟩
  refine ⟨h x y hr1, hrep, hterm, ?_⟩
  intro a
  rcases hact a with ⟨hnx, hny⟩ | ⟨c, sx, sy, hsx, hsy, hrs⟩
  · exact Or.inl ⟨hnx, hny⟩
  · exact Or.inr ⟨c, sx, sy, hsx, hsy, h sx sy hrs⟩

theorem iterSplit_refines_prev (T : CostedTable S A C R) (q₀ : StateRel S) (k : Nat) :
    Refines (iterSplit T q₀ (k + 1)) (iterSplit T q₀ k) := by
  intro x y hxy
  exact hxy.1

theorem iterSplit_refines_initial (T : CostedTable S A C R) (q₀ : StateRel S) :
    ∀ k x y, iterSplit T q₀ k x y → q₀ x y
  | 0, _, _, h0 => h0.1
  | k + 1, x, y, hk => iterSplit_refines_initial T q₀ k x y hk.1

/-- Inductive optimality (`ATL-P016-002`): any stable refinement `r` of `q₀`
refines every iterate `iterSplit T q₀ k`. -/
theorem stable_refines_all_iterSplit
    {T : CostedTable S A C R} {q₀ r : StateRel S}
    (hstable : IsStableRel T r) (href : Refines r q₀) :
    ∀ k, Refines r (iterSplit T q₀ k)
  | 0 => by
      intro x y hxy
      have hs := hstable x y hxy
      exact ⟨href x y hxy, hs.2.1, hs.2.2.1⟩
  | k + 1 => by
      intro x y hxy
      have ih := stable_refines_all_iterSplit hstable href k
      exact splitOnce_mono ih x y (hstable x y hxy)

/-- Greatest-fixed-point universality (`ATL-P016-002`): when `iterSplit T q₀ k`
stabilizes (`Refines (iterSplit T q₀ k) (iterSplit T q₀ (k + 1))`), it is a
stable refinement of `q₀` and is refined by every stable refinement of `q₀`. -/
theorem stabilized_iterSplit_is_coarsest_stable
    {T : CostedTable S A C R} {q₀ : StateRel S} {k : Nat}
    (hstab : Refines (iterSplit T q₀ k) (iterSplit T q₀ (k + 1))) :
    IsStableRel T (iterSplit T q₀ k) ∧
      Refines (iterSplit T q₀ k) q₀ ∧
      ∀ r, IsStableRel T r → Refines r q₀ → Refines r (iterSplit T q₀ k) := by
  refine ⟨hstab, ?_, ?_⟩
  · intro x y hxy
    exact iterSplit_refines_initial T q₀ k x y hxy
  · intro r hr hq0
    exact stable_refines_all_iterSplit hr hq0 k

/-- Strict block-count ascent lemma: `m` proper splits from `blocks 0` reach at
least `blocks 0 + m` blocks. -/
theorem block_count_lower_bound (blocks : Nat → Nat)
    (hproper : ∀ i, blocks i < blocks (i + 1)) :
    ∀ m, blocks 0 + m ≤ blocks m
  | 0 => by omega
  | m + 1 => by
      have ihm := block_count_lower_bound blocks hproper m
      have hstep := hproper m
      omega

/-- Proper-split bound (`ATL-P016-002`): if `1 ≤ blocks 0`, every split in a
chain of length `m` strictly increases the block count, and `blocks m ≤ cardX`
with `1 ≤ cardX`, then `m ≤ cardX - 1`. -/
theorem proper_splits_le_pred_card (blocks : Nat → Nat) (m cardX : Nat)
    (h0 : 1 ≤ blocks 0)
    (hproper : ∀ i, i < m → blocks i < blocks (i + 1))
    (hcap : blocks m ≤ cardX) :
    m ≤ cardX - 1 := by
  suffices hsum : blocks 0 + m ≤ blocks m by omega
  induction m with
  | zero => omega
  | succ m' ih =>
      have ihm' : blocks 0 + m' ≤ blocks m' := by
        apply ih
        · intro i hi
          exact hproper i (by omega)
        · have hlast := hproper m' (by omega)
          omega
      have hlast := hproper m' (by omega)
      omega

/-- Dedup-based count of distinct colors observed across a finite carrier list. -/
def distinctColorCount [DecidableEq Color] (xs : List S) (col : S → Color) : Nat :=
  (xs.foldl (fun acc x => if col x ∈ acc then acc else col x :: acc) []).length

private theorem foldl_new_colors_len_le [DecidableEq Color] :
    ∀ (xs : List S) (col : S → Color) (acc : List Color),
      (xs.foldl (fun a x => if col x ∈ a then a else col x :: a) acc).length ≤
        acc.length + xs.length
  | [], _, acc => by simp
  | x :: xs, col, acc => by
      simp only [List.foldl]
      by_cases hmem : col x ∈ acc
      · simp only [hmem, ↓reduceIte]
        have ih := foldl_new_colors_len_le xs col acc
        simp only [List.length_cons]
        omega
      · simp only [hmem, ↓reduceIte]
        have ih := foldl_new_colors_len_le xs col (col x :: acc)
        simp only [List.length_cons] at ih ⊢
        omega

/-- On any finite state list `xs`, the number of distinct block colors is at
most `xs.length`. -/
theorem distinctColorCount_le_length [DecidableEq Color]
    (xs : List S) (col : S → Color) :
    distinctColorCount xs col ≤ xs.length := by
  simpa [distinctColorCount] using foldl_new_colors_len_le xs col []

/-!
## 3. Positive-Cost Loop Erasure & Three-State Route Example (`ATL-P016-004`)
-/

/-- A `Nat`-costed table is standard when `zeroCost = 0` and `addCost = Nat.add`. -/
structure StandardNatCost (T : CostedTable S A Nat R) : Prop where
  zero_eq : T.zeroCost = 0
  add_eq : ∀ x y, T.addCost x y = x + y

/-- Every enabled transition carries a strictly positive integer cost. -/
def PositiveStepCosts (T : CostedTable S A Nat R) : Prop :=
  ∀ s a c s', T.step s a = some (c, s') → 0 < c

/-- Word concatenation law for `StandardNatCost` tables. -/
theorem execWord_append {T : CostedTable S A Nat R} (hnat : StandardNatCost T) :
    ∀ (w₁ w₂ : List A) {s₀ s₁ s₂ : S} {c₁ c₂ : Nat},
      execWord T s₀ w₁ = some (c₁, s₁) →
      execWord T s₁ w₂ = some (c₂, s₂) →
      execWord T s₀ (w₁ ++ w₂) = some (c₁ + c₂, s₂)
  | [], w₂, s₀, s₁, s₂, c₁, c₂, h₁, h₂ => by
      simp [execWord, hnat.zero_eq] at h₁
      rcases h₁ with ⟨hc₁, hs₁⟩
      subst hc₁
      subst hs₁
      simpa using h₂
  | a :: w₁, w₂, s₀, s₁, s₂, c₁, c₂, h₁, h₂ => by
      cases hstep : T.step s₀ a with
      | none =>
          simp [execWord, hstep] at h₁
      | some pair =>
          rcases pair with ⟨ca, smid⟩
          simp only [execWord, hstep] at h₁
          cases htail : execWord T smid w₁ with
          | none =>
              rw [htail] at h₁
              cases h₁
          | some ptail =>
              rcases ptail with ⟨ctail, s₁'⟩
              rw [htail] at h₁
              cases h₁
              have ih := execWord_append hnat w₁ w₂ htail h₂
              simp [execWord, hstep, ih, hnat.add_eq]
              omega

/-- Non-empty legal words accumulate strictly positive cost under `PositiveStepCosts`. -/
theorem positive_cost_of_nonempty_word
    {T : CostedTable S A Nat R} (hnat : StandardNatCost T) (hpos : PositiveStepCosts T) :
    ∀ {w : List A} {s sf : S} {c : Nat},
      w ≠ [] → execWord T s w = some (c, sf) → 0 < c
  | [], _, _, _, hne, _ => absurd rfl hne
  | a :: w, s, sf, c, _, hexec => by
      cases hstep : T.step s a with
      | none =>
          simp [execWord, hstep] at hexec
      | some pair =>
          rcases pair with ⟨ca, smid⟩
          have hca : 0 < ca := hpos s a ca smid hstep
          simp only [execWord, hstep] at hexec
          cases htail : execWord T smid w with
          | none =>
              rw [htail] at hexec
              cases hexec
          | some ptail =>
              rcases ptail with ⟨ctail, sf'⟩
              rw [htail] at hexec
              cases hexec
              rw [hnat.add_eq]
              omega

/-- Loop-erasure theorem (`ATL-P016-004`): deleting a non-empty repeated-state
segment `w₂` at state `u` produces a strictly shorter legal resolving word
`w₁ ++ w₃` with strictly smaller accumulated cost `c₁ + c₃ < c₁ + (c₂ + c₃)`. -/
theorem loop_erasure_strictly_reduces_cost
    {T : CostedTable S A Nat R} (hnat : StandardNatCost T) (hpos : PositiveStepCosts T)
    {s₀ u sf : S} {w₁ w₂ w₃ : List A} {c₁ c₂ c₃ : Nat}
    (hw₂ : w₂ ≠ [])
    (h₁ : execWord T s₀ w₁ = some (c₁, u))
    (h₂ : execWord T u w₂ = some (c₂, u))
    (h₃ : execWord T u w₃ = some (c₃, sf))
    (hterm : T.isTerminal sf = true) :
    resolvesWithCost T s₀ (w₁ ++ (w₂ ++ w₃)) (c₁ + (c₂ + c₃)) ∧
      resolvesWithCost T s₀ (w₁ ++ w₃) (c₁ + c₃) ∧
      (w₁ ++ w₃).length < (w₁ ++ (w₂ ++ w₃)).length ∧
      c₁ + c₃ < c₁ + (c₂ + c₃) := by
  have hc₂ : 0 < c₂ := positive_cost_of_nonempty_word hnat hpos hw₂ h₂
  have h₂₃ : execWord T u (w₂ ++ w₃) = some (c₂ + c₃, sf) :=
    execWord_append hnat w₂ w₃ h₂ h₃
  have h₁₂₃ : execWord T s₀ (w₁ ++ (w₂ ++ w₃)) = some (c₁ + (c₂ + c₃), sf) :=
    execWord_append hnat w₁ (w₂ ++ w₃) h₁ h₂₃
  have h₁₃ : execWord T s₀ (w₁ ++ w₃) = some (c₁ + c₃, sf) :=
    execWord_append hnat w₁ w₃ h₁ h₃
  have hlen₂ : 0 < w₂.length := by
    cases w₂ with
    | nil => exact absurd rfl hw₂
    | cons _ _ => simp
  refine ⟨⟨sf, h₁₂₃, hterm⟩, ⟨sf, h₁₃, hterm⟩, ?_, ?_⟩
  · simp [List.length_append]
    omega
  · omega

/-- States of Paper 016 §4–5's three-state route table (`r, s, t`). -/
inductive RouteState where
  | r
  | s
  | t
  deriving DecidableEq, Repr

/-- Actions of Paper 016 §4–5's route table (`direct, next, finish, loop`). -/
inductive RouteAct where
  | direct
  | next
  | finish
  | loop
  deriving DecidableEq, Repr

/-- Paper 016 §5 concrete cost table: `r --direct(5)--> t`, `r --next(1)--> s`,
`r --loop(1)--> r`, and `s --finish(1)--> t`. -/
def paper016RouteTable : CostedTable RouteState RouteAct Nat Nat where
  step
    | .r, .direct => some (5, .t)
    | .r, .next => some (1, .s)
    | .r, .loop => some (1, .r)
    | .s, .finish => some (1, .t)
    | _, _ => none
  report
    | .r => 0
    | .s => 0
    | .t => 1
  isTerminal
    | .r => false
    | .s => false
    | .t => true
  zeroCost := 0
  addCost := Nat.add

/-- Paper 016 §4–5 route comparison (`ATL-P016-004`): the two-step simple path
`[next, finish]` resolves at cost `2`, strictly beating both the single-step
`[direct]` route (`5`) and the looped route `[loop, next, finish]` (`3`). -/
theorem paper016_route_example_costs :
    execWord paper016RouteTable .r [.direct] = some (5, .t) ∧
      execWord paper016RouteTable .r [.next, .finish] = some (2, .t) ∧
      execWord paper016RouteTable .r [.loop, .next, .finish] = some (3, .t) ∧
      2 < 5 ∧ 2 < 3 := by
  refine ⟨rfl, rfl, rfl, by omega, by omega⟩

/-!
## 4. Finite Local-to-Global Gluing Bijection & Boolean Cycle (`ATL-P015-001`, `ATL-P015-002`)
-/

/-- Pairwise overlap agreement for a family of assignments indexed by `ScopeIdx`
with decidable scope membership `inScope : ScopeIdx → Var → Bool`. -/
def PairwiseCompatible {ScopeIdx Var : Type} {Val : Var → Type}
    (inScope : ScopeIdx → Var → Bool)
    (fam : ScopeIdx → (v : Var) → Val v) : Prop :=
  ∀ i j v, inScope i v = true → inScope j v = true → fam i v = fam j v

/-- Global assignment `g` glues `fam` when `g` restricts to `fam i` on every
variable in scope `i`. -/
def GluesTo {ScopeIdx Var : Type} {Val : Var → Type}
    (inScope : ScopeIdx → Var → Bool)
    (fam : ScopeIdx → (v : Var) → Val v)
    (g : (v : Var) → Val v) : Prop :=
  ∀ i v, inScope i v = true → g v = fam i v

/-- Local constraint `Permitted i` depends only on variables inside scope `i`. -/
def ConstraintLocal {ScopeIdx Var : Type} {Val : Var → Type}
    (inScope : ScopeIdx → Var → Bool)
    (Permitted : ScopeIdx → ((v : Var) → Val v) → Prop) : Prop :=
  ∀ i (a₁ a₂ : (v : Var) → Val v),
    (∀ v, inScope i v = true → a₁ v = a₂ v) →
      (Permitted i a₁ ↔ Permitted i a₂)

/-- Constructive gluing map using explicit cover witness `cover : Var → ScopeIdx`. -/
def glueFamily {ScopeIdx Var : Type} {Val : Var → Type}
    (cover : Var → ScopeIdx)
    (fam : ScopeIdx → (v : Var) → Val v) : (v : Var) → Val v :=
  fun v => fam (cover v) v

/-- Restriction map sending a global assignment `g` to the constant family `fun _ => g`. -/
def restrictGlobal {ScopeIdx Var : Type} {Val : Var → Type}
    (g : (v : Var) → Val v) : ScopeIdx → (v : Var) → Val v :=
  fun _ v => g v

/-- Gluing existence and uniqueness (`ATL-P015-001`): over covered variables
(`∀ v, inScope (cover v) v = true`), a family glues to a global assignment iff
it is pairwise overlap-compatible, and the glued assignment is unique. -/
theorem gluing_iff_pairwise_compatible
    {ScopeIdx Var : Type} {Val : Var → Type}
    (inScope : ScopeIdx → Var → Bool)
    (cover : Var → ScopeIdx)
    (hcover : ∀ v, inScope (cover v) v = true)
    (fam : ScopeIdx → (v : Var) → Val v) :
    ((∃ g, GluesTo inScope fam g) ↔ PairwiseCompatible inScope fam) ∧
      (∀ g₁ g₂, GluesTo inScope fam g₁ → GluesTo inScope fam g₂ → g₁ = g₂) := by
  refine ⟨?_, ?_⟩
  · constructor
    · rintro ⟨g, hg⟩ i j v hi hj
      rw [← hg i v hi, ← hg j v hj]
    · intro hcompat
      refine ⟨glueFamily cover fam, ?_⟩
      intro i v hi
      exact hcompat (cover v) i v (hcover v) hi
  · intro g₁ g₂ hg₁ hg₂
    funext v
    have hc := hcover v
    rw [hg₁ (cover v) v hc, hg₂ (cover v) v hc]

/-- Mutual-inverse correspondence (`ATL-P015-001`) between globally permitted
solutions and pairwise-compatible locally permitted families. -/
theorem compatible_permitted_bijection
    {ScopeIdx Var : Type} {Val : Var → Type}
    (inScope : ScopeIdx → Var → Bool)
    (cover : Var → ScopeIdx)
    (hcover : ∀ v, inScope (cover v) v = true)
    (Permitted : ScopeIdx → ((v : Var) → Val v) → Prop)
    (hlocal : ConstraintLocal inScope Permitted) :
    (∀ g : (v : Var) → Val v, glueFamily cover (restrictGlobal g) = g) ∧
      (∀ fam : ScopeIdx → (v : Var) → Val v, PairwiseCompatible inScope fam →
        ∀ i v, inScope i v = true →
          restrictGlobal (glueFamily cover fam) i v = fam i v) ∧
      (∀ fam : ScopeIdx → (v : Var) → Val v, PairwiseCompatible inScope fam →
        (∀ i, Permitted i (fam i)) →
          ∀ i, Permitted i (glueFamily cover fam)) ∧
      (∀ g : (v : Var) → Val v, (∀ i, Permitted i g) →
        PairwiseCompatible inScope (restrictGlobal g) ∧
          ∀ i, Permitted i (restrictGlobal g i)) := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro g
    funext v
    rfl
  · intro fam hcompat i v hi
    exact hcompat (cover v) i v (hcover v) hi
  · intro fam hcompat hperm i
    have hagree : ∀ v, inScope i v = true → fam i v = glueFamily cover fam v := by
      intro v hi
      exact (hcompat i (cover v) v hi (hcover v))
    exact (hlocal i (fam i) (glueFamily cover fam) hagree).mp (hperm i)
  · intro g hg
    refine ⟨?_, fun i => hg i⟩
    intro _ _ _ _ _
    rfl

/-- Three-variable Boolean local-green / global-red cycle (`ATL-P015-002`):
`x = y`, `y = z`, and `z ≠ x` are each locally satisfiable, jointly
unsatisfiable, and replacing `z ≠ x` by `z = x` yields `(false, false, false)`
and `(true, true, true)` as the unique global solutions. -/
theorem boolean_cycle_obstruction_and_equality_solutions :
    (∃ x y : Bool, x = y) ∧
      (∃ y z : Bool, y = z) ∧
      (∃ z x : Bool, z ≠ x) ∧
      (∀ x y z : Bool, ¬ (x = y ∧ y = z ∧ z ≠ x)) ∧
      (∀ x y z : Bool,
        (x = y ∧ y = z ∧ z = x) ↔
          ((x = false ∧ y = false ∧ z = false) ∨
            (x = true ∧ y = true ∧ z = true))) := by
  refine ⟨⟨false, false, rfl⟩, ⟨false, false, rfl⟩, ⟨false, true, by decide⟩, ?_, ?_⟩
  · intro x y z ⟨hxy, hyz, hzx⟩
    exact hzx (hxy.trans hyz).symm
  · intro x y z
    cases x <;> cases y <;> cases z <;> simp

/-!
## 5. Four-Stage Outer-Loop Funnel Contraction & Authority Closure (`v1.0rc`)
-/

/-- Admitted deterministic predicates for the four-stage `v1.0rc` outer-loop funnel. -/
structure FunnelGates (Cand : Type) where
  thymusGate : Cand → Bool
  quorumGate : Cand → Bool
  witnessGate : Cand → Bool
  paretoGate : Cand → Bool

/-- Complete stage-by-stage trace and composed internal `AuthorityEffect`. -/
structure FunnelTrace (Cand : Type) where
  input : List Cand
  afterThymus : List Cand
  afterQuorum : List Cand
  afterWitness : List Cand
  afterPareto : List Cand
  authorityEffect : AuthorityEffect
  deriving Repr

/-- Admitted stage authority effect (`AuthorityEffect.none` at every gate). -/
def stageAuthorityEffect : Fin 4 → AuthorityEffect
  | _ => AuthorityEffect.none

/-- Execute the four-stage outer-loop funnel over a finite candidate batch `cs`. -/
def runFourStageFunnel (G : FunnelGates Cand) (cs : List Cand) : FunnelTrace Cand :=
  let s1 := cs.filter G.thymusGate
  let s2 := s1.filter G.quorumGate
  let s3 := s2.filter G.witnessGate
  let s4 := s3.filter G.paretoGate
  let eff :=
    composeAuthorityEffect (stageAuthorityEffect ⟨0, by omega⟩)
      (composeAuthorityEffect (stageAuthorityEffect ⟨1, by omega⟩)
        (composeAuthorityEffect (stageAuthorityEffect ⟨2, by omega⟩)
          (stageAuthorityEffect ⟨3, by omega⟩)))
  { input := cs
    afterThymus := s1
    afterQuorum := s2
    afterWitness := s3
    afterPareto := s4
    authorityEffect := eff }

private theorem filter_length_le (p : α → Bool) :
    ∀ xs : List α, (xs.filter p).length ≤ xs.length
  | [] => by simp
  | x :: xs => by
      simp only [List.filter]
      cases p x <;> simp [List.length] <;> have ih := filter_length_le p xs <;> omega

private theorem mem_filter_iff_true (p : α → Bool) :
    ∀ (xs : List α) (x : α), x ∈ xs.filter p ↔ x ∈ xs ∧ p x = true
  | [], _ => by simp
  | y :: ys, x => by
      simp only [List.filter]
      cases hp : p y with
      | false =>
          rw [mem_filter_iff_true p ys x]
          constructor
          · rintro ⟨hmem, hpx⟩
            exact ⟨List.mem_cons_of_mem y hmem, hpx⟩
          · rintro ⟨hmem, hpx⟩
            cases hmem with
            | head =>
                rw [hp] at hpx
                cases hpx
            | tail _ htail =>
                exact ⟨htail, hpx⟩
      | true =>
          simp only [List.mem_cons]
          rw [mem_filter_iff_true p ys x]
          constructor
          · rintro ( rfl | ⟨hmem, hpx⟩ )
            · exact ⟨Or.inl rfl, hp⟩
            · exact ⟨Or.inr hmem, hpx⟩
          · rintro ⟨rfl | hmem, hpx⟩
            · exact Or.inl rfl
            · exact Or.inr ⟨hmem, hpx⟩

/-- Monotone cardinality contraction across all four funnel stages. -/
theorem funnel_monotone_contraction (G : FunnelGates Cand) (cs : List Cand) :
    (runFourStageFunnel G cs).afterPareto.length ≤
        (runFourStageFunnel G cs).afterWitness.length ∧
      (runFourStageFunnel G cs).afterWitness.length ≤
        (runFourStageFunnel G cs).afterQuorum.length ∧
      (runFourStageFunnel G cs).afterQuorum.length ≤
        (runFourStageFunnel G cs).afterThymus.length ∧
      (runFourStageFunnel G cs).afterThymus.length ≤ cs.length := by
  dsimp [runFourStageFunnel]
  exact ⟨filter_length_le G.paretoGate _,
    filter_length_le G.witnessGate _,
    filter_length_le G.quorumGate _,
    filter_length_le G.thymusGate _⟩

/-- Exact four-gate conjunction characterization of final incumbent survivors:
captures both soundness (no unverified survivor) and completeness (every
candidate passing all four gates survives). -/
theorem mem_afterPareto_iff (G : FunnelGates Cand) (cs : List Cand) (c : Cand) :
    c ∈ (runFourStageFunnel G cs).afterPareto ↔
      c ∈ cs ∧ G.thymusGate c = true ∧ G.quorumGate c = true ∧
        G.witnessGate c = true ∧ G.paretoGate c = true := by
  dsimp [runFourStageFunnel]
  rw [mem_filter_iff_true, mem_filter_iff_true, mem_filter_iff_true, mem_filter_iff_true]
  constructor
  · rintro ⟨⟨⟨⟨h0, h1⟩, h2⟩, h3⟩, h4⟩
    exact ⟨h0, h1, h2, h3, h4⟩
  · rintro ⟨h0, h1, h2, h3, h4⟩
    exact ⟨⟨⟨⟨h0, h1⟩, h2⟩, h3⟩, h4⟩

/-- Early-rejection exclusion: any candidate refused by Stage 1 (`thymusGate c = false`)
is excluded from Stage 1 and every downstream stage (`afterQuorum`, `afterWitness`,
`afterPareto`), preventing Stage-2/3/4 leakage. -/
theorem thymus_reject_never_reaches_downstream
    (G : FunnelGates Cand) (cs : List Cand) {c : Cand}
    (hrej : G.thymusGate c = false) :
    c ∉ (runFourStageFunnel G cs).afterThymus ∧
      c ∉ (runFourStageFunnel G cs).afterQuorum ∧
      c ∉ (runFourStageFunnel G cs).afterWitness ∧
      c ∉ (runFourStageFunnel G cs).afterPareto := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · dsimp [runFourStageFunnel]
    intro h; rw [mem_filter_iff_true] at h; rw [hrej] at h; exact Bool.noConfusion h.2
  · dsimp [runFourStageFunnel]
    intro h
    rw [mem_filter_iff_true, mem_filter_iff_true] at h
    rw [hrej] at h
    exact Bool.noConfusion h.1.2
  · dsimp [runFourStageFunnel]
    intro h
    rw [mem_filter_iff_true, mem_filter_iff_true, mem_filter_iff_true] at h
    rw [hrej] at h
    exact Bool.noConfusion h.1.1.2
  · intro h
    rw [mem_afterPareto_iff] at h
    rw [hrej] at h
    exact Bool.noConfusion h.2.1

/-- Exact-witness gate protection: any candidate failing Stage 3 (`witnessGate c = false`)
never reaches Stage 4 (`afterPareto`), even if it passed Thymus and Quorum. -/
theorem witness_reject_never_reaches_incumbent
    (G : FunnelGates Cand) (cs : List Cand) {c : Cand}
    (hrej : G.witnessGate c = false) :
    c ∉ (runFourStageFunnel G cs).afterWitness ∧
      c ∉ (runFourStageFunnel G cs).afterPareto := by
  refine ⟨?_, ?_⟩
  · dsimp [runFourStageFunnel]
    intro h
    rw [mem_filter_iff_true] at h
    rw [hrej] at h
    exact Bool.noConfusion h.2
  · intro h
    rw [mem_afterPareto_iff] at h
    rw [hrej] at h
    exact Bool.noConfusion h.2.2.2.1

/-- Zero-authority-expansion closure across the four-stage funnel. -/
theorem funnel_authority_effect_none (G : FunnelGates Cand) (cs : List Cand) :
    (runFourStageFunnel G cs).authorityEffect = AuthorityEffect.none ∧
      (runFourStageFunnel G cs).authorityEffect ≠ AuthorityEffect.claimed := by
  refine ⟨rfl, ?_⟩
  intro h
  cases h

#print axioms PFP.FunnelCompressionClosure.exact_quotient_implies_fibre_compatible
#print axioms PFP.FunnelCompressionClosure.fibre_compatible_gives_exact_quotient
#print axioms PFP.FunnelCompressionClosure.exact_quotient_execWord_commutes
#print axioms PFP.FunnelCompressionClosure.fibre_compatible_execWord_congr
#print axioms PFP.FunnelCompressionClosure.fibre_compatible_preserves_resolvesWithCost
#print axioms PFP.FunnelCompressionClosure.output_preserving_collapse_breaks_cost
#print axioms PFP.FunnelCompressionClosure.stable_refines_all_iterSplit
#print axioms PFP.FunnelCompressionClosure.stabilized_iterSplit_is_coarsest_stable
#print axioms PFP.FunnelCompressionClosure.proper_splits_le_pred_card
#print axioms PFP.FunnelCompressionClosure.distinctColorCount_le_length
#print axioms PFP.FunnelCompressionClosure.execWord_append
#print axioms PFP.FunnelCompressionClosure.positive_cost_of_nonempty_word
#print axioms PFP.FunnelCompressionClosure.loop_erasure_strictly_reduces_cost
#print axioms PFP.FunnelCompressionClosure.paper016_route_example_costs
#print axioms PFP.FunnelCompressionClosure.gluing_iff_pairwise_compatible
#print axioms PFP.FunnelCompressionClosure.compatible_permitted_bijection
#print axioms PFP.FunnelCompressionClosure.boolean_cycle_obstruction_and_equality_solutions
#print axioms PFP.FunnelCompressionClosure.funnel_monotone_contraction
#print axioms PFP.FunnelCompressionClosure.mem_afterPareto_iff
#print axioms PFP.FunnelCompressionClosure.thymus_reject_never_reaches_downstream
#print axioms PFP.FunnelCompressionClosure.witness_reject_never_reaches_incumbent
#print axioms PFP.FunnelCompressionClosure.funnel_authority_effect_none

end PFP.FunnelCompressionClosure
