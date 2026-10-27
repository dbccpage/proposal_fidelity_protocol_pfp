import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Matrix.Mul
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Tactic.FinCases
import Mathlib.Tactic.NormNum

/-! A positive, normalized, flat projection that loses a protected question.
These exact matrices instantiate a three-vertex constant-fiber chain. -/
namespace Paper001FlatLoss

def projection : Matrix (Fin 3) (Fin 3) ℚ :=
  Matrix.of (fun i j => if i.val < 2 ∧ j.val < 2 then 1/2
    else if i.val = 2 ∧ j.val = 2 then 1 else 0)

def first : Fin 3 → ℚ := fun i => if i.val = 0 then 1 else 0
def second : Fin 3 → ℚ := fun i => if i.val = 1 then 1 else 0

@[simp] theorem projection_apply (i j : Fin 3) :
    projection i j = (if i.val < 2 ∧ j.val < 2 then 1/2
    else if i.val=2 ∧ j.val=2 then 1 else 0) := rfl

theorem projection_idempotent : projection * projection = projection := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    norm_num [Matrix.mul_apply,projection_apply,Fin.sum_univ_succ]

theorem curvature_zero : projection * projection - projection = 0 := by
  rw [projection_idempotent,sub_self]

theorem protected_difference : first 0 - second 0 = 1 := by
  norm_num [first,second]

theorem collapsed_difference : projection.mulVec first = projection.mulVec second := by
  ext i
  fin_cases i <;> norm_num [projection_apply,first,second,Matrix.mulVec,dotProduct,Fin.sum_univ_succ]

theorem positive_normalized :
    (∀ i j, 0 ≤ projection i j) ∧ (∀ j, ∑ i, projection i j = 1) := by
  constructor
  · intro i j
    fin_cases i <;> fin_cases j <;> norm_num [projection_apply]
  · intro j
    fin_cases j <;> norm_num [projection_apply,Fin.sum_univ_succ]
    all_goals decide

#print axioms projection_idempotent
#print axioms curvature_zero
#print axioms protected_difference
#print axioms collapsed_difference
#print axioms positive_normalized
end Paper001FlatLoss
