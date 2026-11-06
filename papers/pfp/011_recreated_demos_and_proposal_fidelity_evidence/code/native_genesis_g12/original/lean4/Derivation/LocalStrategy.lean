import Derivation.CapacityBound

/-!
# A local finite-alphabet repair-strategy class

This module declares the class used for the G1 consequence.  A strategy
has one fixed radius, a colour family, a repair-view family, and an import
discipline.  Locality is the load-bearing factorization through
`CapacityBound.colourBall`; `FiniteDeclaration` separately requires one
alphabet bound that is independent of the chain length.

`Fires` concerns the inherited depth-one obstruction before repair.
`Clears` concerns the strategy view after repair.  Thus the two predicates
do not conflate the live challenge with its proposed response.
-/

namespace LocalFiniteAlphabet

open RefusalFrontier Generator SeparationCapacity CapacityBound

inductive ImportDiscipline where
  | oneTime
  | recurring
  deriving DecidableEq

/-- A radius-`d` strategy.  Its repair view must factor through the
radius-`d` ball for each chain length. -/
structure LocalStrategy (d : Nat) where
  importDiscipline : ImportDiscipline
  colour : Nat → Nat → Nat
  view : Nat → Nat → Nat
  locality : ∀ n, ViewLocal (view n) (colour n) d

/-- One fixed `k` bounds every colour at every chain length. -/
def FiniteDeclaration {d : Nat} (k : Nat) (S : LocalStrategy d) : Prop :=
  ∀ n x, S.colour n x < k

/-- The strategy explicitly requests fresh response data per repair. -/
def RecurringImport {d : Nat} (S : LocalStrategy d) : Prop :=
  S.importDiscipline = .recurring

/-- Two distinct carrier points have the same inherited depth-one
profile before a proposed repair is applied. -/
structure BaseObstructed (n i j : Nat) : Prop where
  left_mem : i ≤ n
  right_mem : j ≤ n
  distinct : i ≠ j
  same_profile : profile1 (reflState n) i = profile1 (reflState n) j

/-- Arbitrarily long reflective chains retain a pre-repair obstruction. -/
def Fires {d : Nat} (_S : LocalStrategy d) : Prop :=
  ∃ n0, ∀ n, n0 ≤ n → ∃ i j, BaseObstructed n i j

/-- The proposed repair view separates every inherited obstructed pair
at one chain length. -/
def ClearsOn {d : Nat} (S : LocalStrategy d) (n : Nat) : Prop :=
  ∀ i j, BaseObstructed n i j → S.view n i ≠ S.view n j

/-- The proposed repair view clears at every chain length. -/
def Clears {d : Nat} (S : LocalStrategy d) : Prop :=
  ∀ n, ClearsOn S n

/-- The repair view separates every distinct carrier pair. -/
def IdentityGrade {d : Nat} (S : LocalStrategy d) : Prop :=
  ∀ n i j, i ≤ n → j ≤ n → i ≠ j → S.view n i ≠ S.view n j

/-- Identity-grade observation supplied by one declared rule, not by
per-repair response data. -/
def OneTimeIdentity {d : Nat} (S : LocalStrategy d) : Prop :=
  S.importDiscipline = .oneTime ∧ IdentityGrade S

theorem fires_every_strategy {d : Nat} (S : LocalStrategy d) : Fires S := by
  refine ⟨3, ?_⟩
  intro n hn
  have hgenerated := generation_never_dries n hn
  exact ⟨1, 2, ⟨by omega, by omega, hgenerated.1, hgenerated.2⟩⟩

theorem identityGrade_implies_clears {d : Nat} {S : LocalStrategy d}
    (h : IdentityGrade S) : Clears S := by
  intro n i j hij
  exact h n i j hij.left_mem hij.right_mem hij.distinct

/-- The existing capacity theorem applied to one member of the class. -/
theorem strategy_capacity_collision {d : Nat} (S : LocalStrategy d) (k n : Nat)
    (hfinite : FiniteDeclaration k S)
    (hn : k ^ (2 * d + 1) + 2 * d + 2 ≤ n) :
    ∃ i j, i ≠ j ∧ d < i ∧ i + d < n ∧ d < j ∧ j + d < n ∧
      S.view n i = S.view n j :=
  capacity_bound (S.colour n) (S.view n) k d n (hfinite n) (S.locality n) hn

/-- No fixed finite-alphabet local strategy clears every inherited
depth-one obstruction. -/
theorem finite_local_not_clears {d : Nat} (S : LocalStrategy d) (k : Nat)
    (hfinite : FiniteDeclaration k S) : ¬ Clears S := by
  intro hclears
  let n := k ^ (2 * d + 1) + 2 * d + 2
  obtain ⟨i, j, hij, hi0, hi1, hj0, hj1, hview⟩ :=
    strategy_capacity_collision S k n hfinite (by simp [n])
  have hprofile : profile1 (reflState n) i = profile1 (reflState n) j := by
    rw [middle_profile n i (by omega) (by omega),
        middle_profile n j (by omega) (by omega)]
  exact (hclears n i j ⟨by omega, by omega, hij, hprofile⟩) hview

theorem finite_local_not_identityGrade {d : Nat} (S : LocalStrategy d) (k : Nat)
    (hfinite : FiniteDeclaration k S) : ¬ IdentityGrade S := by
  intro hidentity
  exact finite_local_not_clears S k hfinite (identityGrade_implies_clears hidentity)

/-- **G1, class-relative form.**  Every strategy in the declared class
fires on the inherited reflective family and fails to clear all of it.
Consequently the full fire/clear/no-recurring-import cycle is excluded.
The conclusion is only about this class. -/
theorem g1_local_finite_alphabet_class {d : Nat} (S : LocalStrategy d) (k : Nat)
    (hfinite : FiniteDeclaration k S) :
    Fires S ∧ ¬ Clears S ∧
      ¬ (Fires S ∧ Clears S ∧ ¬ RecurringImport S) := by
  have hfires := fires_every_strategy S
  have hnot := finite_local_not_clears S k hfinite
  exact ⟨hfires, hnot, fun hcycle => hnot hcycle.2.1⟩

/-! ## Concrete members and boundary witnesses -/

def zeroRadiusStrategy (discipline : ImportDiscipline)
    (f : Nat → Nat → Nat) : LocalStrategy 0 where
  importDiscipline := discipline
  colour := f
  view := f
  locality := by
    intro n
    refine ⟨fun xs => xs.headD 0, ?_⟩
    intro i
    simp [colourBall, ball]

def boolCode : Bool → Nat
  | false => 0
  | true => 1

def profileCode (p : Bool × Bool × Bool) : Nat :=
  boolCode p.1 + 2 * boolCode p.2.1 + 4 * boolCode p.2.2

theorem profileCode_lt_eight (p : Bool × Bool × Bool) : profileCode p < 8 := by
  rcases p with ⟨a, b, c⟩
  cases a <;> cases b <;> cases c <;> decide

/-- No added repair view: the inherited depth-one profile remains the
whole view. -/
def bare : LocalStrategy 0 :=
  zeroRadiusStrategy .oneTime
    (fun n i => profileCode (profile1 (reflState n) i))

/-- A one-time presence-valued automark.  Presence is already the first
bit of the inherited profile, so this view is definitionally the bare
view. -/
def presence : LocalStrategy 0 := bare

/-- Radius-one structural observation encoded over the eight depth-one
profile colours. -/
def depthTwo : LocalStrategy 1 where
  importDiscipline := .oneTime
  colour := fun n i => profileCode (profile1 (reflState n) i)
  view := fun n i =>
    encode 8 (colourBall (fun x => profileCode (profile1 (reflState n) x)) i 1)
  locality := by
    intro n
    exact ⟨encode 8, fun _ => rfl⟩

/-- Fresh per-pair marks, represented by an unbounded point code and an
explicit recurring-import discipline. -/
def perPairFreshMark : LocalStrategy 0 :=
  zeroRadiusStrategy .recurring (fun _ i => i)

/-- One declared identity-grade value rule.  It is not a fixed finite
alphabet declaration. -/
def valued : LocalStrategy 0 :=
  zeroRadiusStrategy .oneTime (fun _ i => i)

theorem bare_finite : FiniteDeclaration 8 bare := by
  intro n i
  exact profileCode_lt_eight _

theorem presence_finite : FiniteDeclaration 8 presence := bare_finite

theorem presence_eq_bare : presence = bare := rfl

theorem depthTwo_finite : FiniteDeclaration 8 depthTwo := by
  intro n i
  exact profileCode_lt_eight _

/-- The depth-two member really clears one nontrivial finite chain; the
class is not populated only by failures. -/
theorem depthTwo_clears_n4 : ClearsOn depthTwo 4 := by
  intro i j hij
  rcases hij with ⟨hi, hj, hne, hprofile⟩
  have hinterior :=
    (depth1_obstructions_are_exactly_middle_pairs 4 i j
      (by omega) hi hj hne).mp hprofile
  have hiCases : i = 1 ∨ i = 2 ∨ i = 3 := by omega
  have hjCases : j = 1 ∨ j = 2 ∨ j = 3 := by omega
  rcases hiCases with (rfl | rfl | rfl) <;>
    rcases hjCases with (rfl | rfl | rfl) <;>
      first | contradiction | decide

theorem perPair_recurring : RecurringImport perPairFreshMark := rfl

theorem perPair_identityGrade : IdentityGrade perPairFreshMark := by
  intro n i j _ _ hij
  simpa [perPairFreshMark, zeroRadiusStrategy] using hij

theorem perPair_not_finite (k : Nat) :
    ¬ FiniteDeclaration k perPairFreshMark := by
  intro h
  exact (Nat.lt_irrefl k) (h 0 k)

theorem valued_oneTimeIdentity : OneTimeIdentity valued := by
  constructor
  · rfl
  · intro n i j _ _ hij
    simpa [valued, zeroRadiusStrategy] using hij

theorem valued_not_finite (k : Nat) : ¬ FiniteDeclaration k valued := by
  intro h
  exact (Nat.lt_irrefl k) (h 0 k)

theorem valued_clears : Clears valued :=
  identityGrade_implies_clears valued_oneTimeIdentity.2

theorem class_nonvacuity :
    Fires bare ∧ ClearsOn depthTwo 4 ∧ IdentityGrade valued :=
  ⟨fires_every_strategy bare, depthTwo_clears_n4,
   valued_oneTimeIdentity.2⟩

theorem bare_not_identityGrade : ¬ IdentityGrade bare := by
  intro h
  exact (h 3 1 2 (by omega) (by omega) (by omega))
    (by
      change profileCode (profile1 (reflState 3) 1) =
        profileCode (profile1 (reflState 3) 2)
      rw [middle_profile 3 1 (by omega) (by omega),
          middle_profile 3 2 (by omega) (by omega)])

theorem bare_classification :
    FiniteDeclaration 8 bare ∧ Fires bare ∧ ¬ Clears bare ∧
      ¬ RecurringImport bare := by
  refine ⟨bare_finite, fires_every_strategy bare,
    finite_local_not_clears bare 8 bare_finite, ?_⟩
  simp [RecurringImport, bare, zeroRadiusStrategy]

theorem presence_classification :
    FiniteDeclaration 8 presence ∧ Fires presence ∧ ¬ Clears presence ∧
      ¬ RecurringImport presence := by
  refine ⟨presence_finite, fires_every_strategy presence,
    finite_local_not_clears presence 8 presence_finite, ?_⟩
  simp [RecurringImport, presence, bare, zeroRadiusStrategy]

theorem depthTwo_classification :
    FiniteDeclaration 8 depthTwo ∧ Fires depthTwo ∧ ¬ Clears depthTwo ∧
      ¬ RecurringImport depthTwo := by
  refine ⟨depthTwo_finite, fires_every_strategy depthTwo,
    finite_local_not_clears depthTwo 8 depthTwo_finite, ?_⟩
  simp [RecurringImport, depthTwo]

end LocalFiniteAlphabet
