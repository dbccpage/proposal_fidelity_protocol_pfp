import Mathlib.Tactic.NoncommRing
import Mathlib.Tactic.Abel

/-! Algebraic kernels of protected comparison, split quotient descent and
arbitrary finite path telescoping. The observed 2-category's endpoint typing,
kernel-preserving admission, RREF minimality and norm estimates are established
separately in prose and exact runtime controls, not assumed to follow from a
ring identity. -/
namespace Paper001Transport
variable {R : Type*} [Ring R]

def horizontal (f g a b : R) := (g+b)*(f+a)-g*f

theorem horizontal_mixed (f g a b : R) :
    horizontal f g a b = g*a+b*f+b*a := by
  unfold horizontal
  noncomm_ring

theorem horizontal_interchange (f g a₁ a₂ b₁ b₂ : R) :
    horizontal f g a₁ b₁ + horizontal (f+a₁) (g+b₁) a₂ b₂ =
      horizontal f g (a₁+a₂) (b₁+b₂) := by
  unfold horizontal
  noncomm_ring

theorem compositor_associativity (a b c d e f : R) :
    (d-a*b)*c+(f-d*c) = a*(e-b*c)+(f-a*e) := by
  noncomm_ring

theorem compositor_units (a : R) : (a-1*a=0) ∧ (a-a*1=0) := by simp

theorem split_descent (b s c t : R) (h : c*t*(1-s*b)=0) :
    (c*t*s)*b=c*t := by
  have hh : c*t-(c*t*s)*b=0 := by
    calc c*t-(c*t*s)*b = c*t*(1-s*b) := by noncomm_ring
         _ = 0 := h
  exact (sub_eq_zero.mp hh).symm

theorem split_unique (b s c t d : R) (right_inverse : b*s=1) (replay : d*b=c*t) :
    d=c*t*s := by
  calc d = d*(b*s) := by rw [right_inverse]; simp
       _ = (d*b)*s := by noncomm_ring
       _ = c*t*s := by rw [replay]

def firstWord : List (R×R) → R
  | [] => 1
  | p::l => firstWord l*p.1
def secondWord : List (R×R) → R
  | [] => 1
  | p::l => secondWord l*p.2
def telescoping : List (R×R) → R
  | [] => 0
  | p::l => firstWord l*(p.1-p.2)+telescoping l*p.2

theorem finite_path_telescoping (l : List (R×R)) :
    firstWord l-secondWord l=telescoping l := by
  induction l with
  | nil => simp [firstWord,secondWord,telescoping]
  | cons p l ih =>
    simp only [firstWord,secondWord,telescoping]
    rw [←ih]
    noncomm_ring

#print axioms horizontal_mixed
#print axioms horizontal_interchange
#print axioms compositor_associativity
#print axioms compositor_units
#print axioms split_descent
#print axioms split_unique
#print axioms finite_path_telescoping
end Paper001Transport
