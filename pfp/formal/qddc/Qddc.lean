import Mathlib.Tactic.Abel
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Linarith

/-!
Finite triangle cochains with additive coefficients, including operator entries.
The rational Hodge theorem below is for the filled oriented triangle with the
Euclidean star. It does not claim a formal proof of the Rust implementation or
of Hodge decomposition for every finite simplicial complex. AuthorityEffect: None.
-/
namespace Qddc

inductive Vertex | v0 | v1 | v2 deriving DecidableEq
inductive Edge | e01 | e02 | e12 deriving DecidableEq
inductive Face | f012 deriving DecidableEq

abbrev C0 (A : Type*) := Vertex → A
abbrev C1 (A : Type*) := Edge → A
abbrev C2 (A : Type*) := Face → A

def d0 {A : Type*} [AddCommGroup A] (f : C0 A) : C1 A
  | .e01 => f .v1 - f .v0
  | .e02 => f .v2 - f .v0
  | .e12 => f .v2 - f .v1

def d1 {A : Type*} [AddCommGroup A] (g : C1 A) : C2 A
  | .f012 => g .e12 - g .e02 + g .e01

def delta1 {A : Type*} [AddCommGroup A] (g : C1 A) : C0 A
  | .v0 => -g .e01 - g .e02
  | .v1 => g .e01 - g .e12
  | .v2 => g .e02 + g .e12

def delta2 {A : Type*} [AddCommGroup A] (h : C2 A) : C1 A
  | .e01 => h .f012
  | .e02 => -h .f012
  | .e12 => h .f012

theorem d_squared_zero {A : Type*} [AddCommGroup A] (f : C0 A) : d1 (d0 f) = 0 := by
  funext face
  cases face
  simp only [d0, d1, Pi.zero_apply]
  abel

theorem delta_squared_zero {A : Type*} [AddCommGroup A] (h : C2 A) :
    delta1 (delta2 h) = 0 := by
  funext vertex
  cases vertex <;> simp [delta1, delta2]

def laplacian (g : C1 ℚ) : C1 ℚ := d0 (delta1 g) + delta2 (d1 g)

theorem laplacian_triangle (g : C1 ℚ) (e : Edge) : laplacian g e = 3 * g e := by
  cases e <;> simp [laplacian, d0, d1, delta1, delta2] <;> ring

def alpha (g : C1 ℚ) : C0 ℚ := fun v => delta1 g v / 3
def beta (g : C1 ℚ) : C2 ℚ := fun f => d1 g f / 3

inductive Component | exact | coexact | harmonic deriving DecidableEq

def split (g : C1 ℚ) : Component → C1 ℚ
  | .exact => d0 (alpha g)
  | .coexact => delta2 (beta g)
  | .harmonic => 0

theorem hodge_reconstruction (g : C1 ℚ) :
    split g .exact + split g .coexact + split g .harmonic = g := by
  funext e
  cases e <;> simp [split, alpha, beta, d0, d1, delta1, delta2] <;> ring

theorem exact_is_closed (g : C1 ℚ) : d1 (split g .exact) = 0 :=
  d_squared_zero (alpha g)

theorem coexact_is_coclosed (g : C1 ℚ) : delta1 (split g .coexact) = 0 :=
  delta_squared_zero (beta g)

theorem potential_zero_mean (g : C1 ℚ) : alpha g .v0 + alpha g .v1 + alpha g .v2 = 0 := by
  simp [alpha, delta1]
  ring

theorem harmonic_vanishes (g : C1 ℚ) (closed : d1 g = 0) (coclosed : delta1 g = 0) : g = 0 := by
  have h0 := congrFun coclosed Vertex.v0
  have h1 := congrFun coclosed Vertex.v1
  have h2 := congrFun closed Face.f012
  simp only [delta1, d1, Pi.zero_apply] at h0 h1 h2
  funext e
  cases e <;> simp only [Pi.zero_apply] <;> linarith

def dot (a b : C1 ℚ) : ℚ := a .e01 * b .e01 + a .e02 * b .e02 + a .e12 * b .e12

theorem hodge_orthogonal (g : C1 ℚ) : dot (split g .exact) (split g .coexact) = 0 := by
  simp [dot, split, alpha, beta, d0, d1, delta1, delta2]
  ring

theorem hodge_components_unique (g : C1 ℚ) (a : C0 ℚ) (b : C2 ℚ) (h : C1 ℚ)
    (closed : d1 h = 0) (coclosed : delta1 h = 0)
    (reconstruct : d0 a + delta2 b + h = g) :
    d0 a = split g .exact ∧ delta2 b = split g .coexact ∧ h = 0 := by
  have hz := harmonic_vanishes h closed coclosed
  subst h
  have h01 := congrFun reconstruct Edge.e01
  have h02 := congrFun reconstruct Edge.e02
  have h12 := congrFun reconstruct Edge.e12
  simp [d0, delta2] at h01 h02 h12
  refine ⟨?_, ?_, rfl⟩
  · funext e
    cases e <;> simp [split, alpha, d0, delta1] <;> linarith
  · funext e
    cases e <;> simp [split, beta, d1, delta2] <;> linarith

#print axioms d_squared_zero
#print axioms delta_squared_zero
#print axioms hodge_reconstruction
#print axioms harmonic_vanishes
#print axioms hodge_components_unique
end Qddc
