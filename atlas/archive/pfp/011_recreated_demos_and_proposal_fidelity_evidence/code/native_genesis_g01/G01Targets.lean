import ResearchG01
open Derivation ResearchG01

namespace G01Targets

def F1 : Prop :=
  validResponse R2F 1 2 (deltaF 1) ∧ validResponse R2F 1 2 (deltaF 2) ∧
  (deltaF 1).length = 2 ∧ (deltaF 2).length = 2 ∧
  (∀ δ, δ.length ≤ 1 → ¬ validResponse R2F 1 2 δ) ∧
  applyDelta R2F (deltaF 1) = some (markF 1) ∧
  applyDelta R2F (deltaF 2) = some (markF 2) ∧
  (Iso (markF 1) (markF 2) → False)

def F5 : Prop :=
  (∀ i, i < 5 → validResponse R2F 1 2 (delta (boundedArgs i)) ∧
    (delta (boundedArgs i)).length = 2 ∧ (boundedArgs i).length ≤ 2 ∧
    applyDelta R2F (delta (boundedArgs i)) = some (state (boundedArgs i))) ∧
  (∀ i j, i < j → j < 5 → Iso (state (boundedArgs i)) (state (boundedArgs j)) → False)

def FK : Prop :=
  (∀ k, 1 ≤ k → validResponse R2F 1 2 (deltaF k) ∧
    (deltaF k).length = 2 ∧ applyDelta R2F (deltaF k) = some (markF k)) ∧
  (∀ j k, j ≠ k → Iso (markF j) (markF k) → False)

def H01 : Prop :=
  (∀ i, i < 5 → validResponse relabelledBase 0 2 (delta (relabelledArgs i)) ∧
    (delta (relabelledArgs i)).length = 2 ∧ (relabelledArgs i).length ≤ 2 ∧
    applyDelta relabelledBase (delta (relabelledArgs i)) =
      some (relabelledState (relabelledArgs i))) ∧
  (∀ i j, i < j → j < 5 → Iso (relabelledState (relabelledArgs i))
    (relabelledState (relabelledArgs j)) → False)

def H02 : Prop := ∀ (k : Nat), 1 ≤ k → Iso (markF k) (state [0, 1]) → False
def H03 : Prop := ∀ (k : Nat), 1 ≤ k → Iso (markF k) (state [1, 0]) → False
def H04 : Prop := validResponse R2F 1 2 (deltaF 3) ∧ (deltaF 3).length = 2 ∧
  applyDelta R2F (deltaF 3) = some (markF 3)
def H05 : Prop :=
  markF 1 = state (boundedArgs 0) ∧ markF 2 = state (boundedArgs 1) ∧
  Nonempty (Iso (markF 1) (state (boundedArgs 0))) ∧
  Nonempty (Iso (markF 2) (state (boundedArgs 1)))
def H06 : Prop := ¬ validResponse R2F 1 2 (delta [0])
def H07 : Prop := ∀ (a b : Item), validResponse R2F 1 2 [a, b] → aritySum [a, b] ≤ 1 →
  ∃ s, applyDelta R2F [a, b] = some s ∧ Nonempty (Iso s U0F)
def H08 : Prop := ∀ (xs ys : List Nat),
  Iso (state xs) (⟨2, [ys.length], [(0, ys)], [], [(0, 1)]⟩ : Regime) → False

end G01Targets

example : G01Targets.F1 := F_1
example : G01Targets.F5 := F_5
example : G01Targets.FK := F_K
example : G01Targets.H01 := H01_relabelled_F5
example : G01Targets.H02 := H02_family_vs_genout
example : G01Targets.H03 := H03_family_vs_genin
example : G01Targets.H04 := H04_fixed_k3
example : G01Targets.H05 := H05_bounded_family_members
example : G01Targets.H06 := H06_genesis_mark_refuted
example : G01Targets.H07 := H07_mu2_unique_witness
example : G01Targets.H08 := H08_reading_identification_refuted
