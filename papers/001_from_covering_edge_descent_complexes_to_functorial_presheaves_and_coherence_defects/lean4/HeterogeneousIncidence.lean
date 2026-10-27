import ConcreteIncidence
import Mathlib.LinearAlgebra.Pi

/-!
Actual varying endpoint-Hom cochains, faithfully lifted to corners in End of
the product of all fibers. With finitely many finite-dimensional rational
fibers this is the familiar finite block-matrix representation. No cochain
laws are assumptions; they transfer through proved faithful maps.
-/
namespace Paper001Heterogeneous

variable {P R : Type*} [CommRing R] [DecidableEq P]
variable (F : P → Type*) [∀ x, AddCommGroup (F x)] [∀ x, Module R (F x)]

abbrev Total := ∀ x, F x
abbrev End := Module.End R (Total F)
abbrev Hom (x z : P) := F z →ₗ[R] F x

def lift (x z : P) (f : Hom (R:=R) F x z) : End (R:=R) F :=
  (LinearMap.single R F x).comp (f.comp (LinearMap.proj z))

theorem extract_lift (x z : P) (f : Hom (R:=R) F x z) :
    (LinearMap.proj x).comp ((lift F x z f).comp (LinearMap.single R F z)) = f := by
  simp only [lift,←LinearMap.comp_assoc,LinearMap.proj_comp_single_same,LinearMap.id_comp]
  simp only [LinearMap.comp_assoc,LinearMap.proj_comp_single_same,LinearMap.comp_id]

theorem lift_injective (x z : P) : Function.Injective (lift (R:=R) F x z) := by
  intro f g h
  have hh := congrArg (fun a : End (R:=R) F => (LinearMap.proj x).comp (a.comp (LinearMap.single R F z))) h
  simpa only [extract_lift] using hh

theorem lift_comp (x y z : P) (f : Hom (R:=R) F x y) (g : Hom (R:=R) F y z) :
    lift F x y f * lift F y z g = lift F x z (f.comp g) := by
  ext v i
  simp [lift,Module.End.mul_eq_comp]

def liftAdd (x z : P) : Hom (R:=R) F x z →+ End (R:=R) F where
  toFun := lift F x z
  map_zero' := by simp [lift]
  map_add' f g := by simp [lift,LinearMap.add_comp,LinearMap.comp_add]

abbrev Cochain := ∀ x : P, List P → ∀ z : P, Hom (R:=R) F x z

def embed (f : Cochain (R:=R) F) : Paper001Concrete.Cochain (P:=P) (R:=End (R:=R) F) :=
  fun x l z => lift F x z (f x l z)

theorem embed_injective : Function.Injective (embed (R:=R) F) := by
  intro f g h
  funext x l z
  apply lift_injective F x z
  exact congrFun (congrFun (congrFun h x) l) z

def b (f : Cochain (R:=R) F) : Cochain (R:=R) F :=
  fun x l z => -Paper001Concrete.alternating (fun t => f x t z) l

def shift (f : Cochain (R:=R) F) (a : P) : Cochain (R:=R) F :=
  fun x l z => f x (a::l) z

def cup : ℕ → Cochain (R:=R) F → Cochain (R:=R) F → Cochain (R:=R) F
  | _,_,_,_,[],_ => 0
  | 0,f,g,x,a::l,z => (f x [] a).comp (g a l z)
  | n+1,f,g,x,a::l,z => cup n (shift F f a) g x l z

@[simp] theorem embed_add (f g : Cochain (R:=R) F) : embed F (f+g)=embed F f+embed F g := by
  funext x l z
  exact (liftAdd F x z).map_add _ _

@[simp] theorem embed_neg (f : Cochain (R:=R) F) : embed F (-f) = -embed F f := by
  funext x l z
  exact (liftAdd F x z).map_neg _

@[simp] theorem embed_sub (f g : Cochain (R:=R) F) : embed F (f-g)=embed F f-embed F g := by
  simp [sub_eq_add_neg]

@[simp] theorem embed_zero : embed (R:=R) F 0 = 0 := by
  funext x l z
  exact (liftAdd F x z).map_zero

theorem embed_b (f : Cochain (R:=R) F) : embed F (b F f) = Paper001Concrete.b (embed F f) := by
  funext x l z
  change (liftAdd F x z) (-Paper001Concrete.alternating (fun t => f x t z) l) = _
  rw [map_neg,←Paper001Concrete.alternating_map]
  rfl

theorem embed_cup (n : ℕ) (f g : Cochain (R:=R) F) :
    embed F (cup F n f g) = Paper001Concrete.cup n (embed F f) (embed F g) := by
  induction n generalizing f g with
  | zero =>
    funext x l z
    cases l with
    | nil => simp [embed,cup,Paper001Concrete.cup,lift]
    | cons a l => exact (lift_comp F x a z _ _).symm
  | succ n ih =>
    funext x l z
    cases l with
    | nil => simp [embed,cup,Paper001Concrete.cup,lift]
    | cons a l =>
      change embed F (cup F n (shift F f a) g) x l z = _
      rw [ih]
      rfl

def signed (n : ℕ) (f : Cochain (R:=R) F) : Cochain (R:=R) F :=
  fun x l z => (-1:ℤ)^n • f x l z

theorem embed_signed (n : ℕ) (f : Cochain (R:=R) F) :
    embed F (signed F n f) = Paper001Concrete.signed n (embed F f) := by
  funext x l z
  exact (liftAdd F x z).map_zsmul _ _

def curvature (a : Cochain (R:=R) F) := b F a + cup F 0 a a
def covariant (n : ℕ) (a f : Cochain (R:=R) F) :=
  b F f + cup F 0 a f - signed F (n+1) (cup F n f a)

theorem embed_curvature (a : Cochain (R:=R) F) :
    embed F (curvature F a) = Paper001Concrete.curvature (embed F a) := by
  simp only [curvature,embed_add,embed_b,embed_cup,Paper001Concrete.curvature]

theorem embed_covariant (n : ℕ) (a f : Cochain (R:=R) F) :
    embed F (covariant F n a f) = Paper001Concrete.covariant n (embed F a) (embed F f) := by
  simp only [covariant,embed_sub,embed_add,embed_b,embed_cup,embed_signed,Paper001Concrete.covariant]

theorem b_square (f : Cochain (R:=R) F) : b F (b F f)=0 := by
  apply embed_injective F
  simp only [embed_b,Paper001Concrete.b_square,embed_zero]

theorem b_leibniz (n : ℕ) (f g : Cochain (R:=R) F) :
    b F (cup F n f g) = cup F (n+1) (b F f) g + signed F (n+1) (cup F n f (b F g)) := by
  apply embed_injective F
  simp only [embed_b,embed_cup,embed_add,embed_signed,Paper001Concrete.b_leibniz]

theorem covariant_square (n : ℕ) (a f : Cochain (R:=R) F) :
    covariant F (n+1) a (covariant F n a f) = cup F 1 (curvature F a) f - cup F n f (curvature F a) := by
  apply embed_injective F
  simp only [embed_covariant,Paper001Concrete.covariant_square,embed_sub,embed_cup,embed_curvature]

def corner (x : P) : End (R:=R) F := lift F x x LinearMap.id

theorem corner_idempotent (x : P) : corner (R:=R) F x * corner F x = corner F x := by
  simp only [corner,lift_comp,LinearMap.id_comp]

theorem right_corner (x z : P) (f : Hom (R:=R) F x z) :
    lift F x z f * corner F z = lift F x z f := by
  simp only [corner,lift_comp,LinearMap.comp_id]

theorem corner_orthogonal (x z : P) (h : x≠z) : corner (R:=R) F x * corner F z = 0 := by
  ext v i
  simp [corner,lift,Module.End.mul_eq_comp,h]

def selector (z : P) : P → End (R:=R) F := fun x => if x=z then corner F z else 0

theorem vertex_selector_detector (x z : P) (h : x≠z) (k : Hom (R:=R) F x z) :
    lift F x z k * selector F z z - selector F z x * lift F x z k = lift F x z k := by
  simp [selector,h,right_corner]

theorem covariant_selector_detector (a : Cochain (R:=R) F) (x z : P)
    (l : List P) (h : x≠z) :
    Paper001Concrete.covariant 0 (embed F a)
      (Paper001Concrete.covariant_zero (embed F a) (selector F z)) x l z =
      lift F x z (curvature F a x l z) := by
  rw [Paper001Concrete.covariant_square_zero,←embed_curvature]
  change lift F x z (curvature F a x l z) * selector F z z -
    selector F z x * lift F x z (curvature F a x l z) = _
  exact vertex_selector_detector F x z h _

section Poset
variable [PartialOrder P]
abbrev PosetCochain (n : ℕ) :=
  ∀ x z : P, Paper001Concrete.StrictInterior P x z n → Hom (R:=R) F x z

def embedPoset (n : ℕ) (f : PosetCochain (R:=R) F n) :
    Paper001Concrete.PosetCochain P (End (R:=R) F) n :=
  fun x z l => lift F x z (f x z l)

theorem embedPoset_injective (n : ℕ) : Function.Injective (embedPoset (R:=R) F n) := by
  intro f g h
  funext x z l
  apply lift_injective F x z
  exact congrFun (congrFun (congrFun h x) z) l

def restrict (n : ℕ) (f : Cochain (R:=R) F) : PosetCochain (R:=R) F n :=
  fun x z l => f x l.val z
noncomputable def extend (n : ℕ) (f : PosetCochain (R:=R) F n) : Cochain (R:=R) F := by
  classical
  exact fun x l z => if h : l.length=n ∧ List.Pairwise (· < ·) (x::l++[z])
    then f x z ⟨l,h⟩ else 0

theorem embed_restrict (n : ℕ) (f : Cochain (R:=R) F) :
    embedPoset F n (restrict F n f) = Paper001Concrete.restrict n (embed F f) := rfl

theorem embed_extend (n : ℕ) (f : PosetCochain (R:=R) F n) :
    embed F (extend F n f) = Paper001Concrete.extend n (embedPoset F n f) := by
  classical
  funext x l z
  by_cases h : l.length=n ∧ List.Pairwise (· < ·) (x::l++[z])
  · simp only [extend,embed,Paper001Concrete.extend,dite_eq_left h,embedPoset]
  · simp only [extend,embed,Paper001Concrete.extend,dite_eq_right h]
    exact (liftAdd F x z).map_zero

noncomputable def poset_b (n : ℕ) (f : PosetCochain (R:=R) F n) :=
  restrict F (n+1) (b F (extend F n f))
noncomputable def poset_cup (n m : ℕ) (f : PosetCochain (R:=R) F n) (g : PosetCochain (R:=R) F m) :=
  restrict F (n+m+1) (cup F n (extend F n f) (extend F m g))
noncomputable def poset_d (n : ℕ) (a : PosetCochain (R:=R) F 0) (f : PosetCochain (R:=R) F n) :=
  restrict F (n+1) (covariant F n (extend F 0 a) (extend F n f))
noncomputable def poset_curvature (a : PosetCochain (R:=R) F 0) :=
  restrict F 1 (curvature F (extend F 0 a))

theorem embed_poset_b (n : ℕ) (f : PosetCochain (R:=R) F n) :
    embedPoset F (n+1) (poset_b F n f) = Paper001Concrete.poset_b n (embedPoset F n f) := by
  simp only [poset_b,embed_restrict,embed_b,embed_extend,Paper001Concrete.poset_b]
theorem embed_poset_cup (n m : ℕ) (f : PosetCochain (R:=R) F n) (g : PosetCochain (R:=R) F m) :
    embedPoset F (n+m+1) (poset_cup F n m f g) =
      Paper001Concrete.poset_cup n m (embedPoset F n f) (embedPoset F m g) := by
  simp only [poset_cup,embed_restrict,embed_cup,embed_extend,Paper001Concrete.poset_cup]
theorem embed_poset_d (n : ℕ) (a : PosetCochain (R:=R) F 0) (f : PosetCochain (R:=R) F n) :
    embedPoset F (n+1) (poset_d F n a f) =
      Paper001Concrete.poset_d n (embedPoset F 0 a) (embedPoset F n f) := by
  simp only [poset_d,embed_restrict,embed_covariant,embed_extend,Paper001Concrete.poset_d]
theorem embed_poset_curvature (a : PosetCochain (R:=R) F 0) :
    embedPoset F 1 (poset_curvature F a) = Paper001Concrete.poset_curvature (embedPoset F 0 a) := by
  simp only [poset_curvature,embed_restrict,embed_curvature,embed_extend,Paper001Concrete.poset_curvature]

theorem poset_b_nilpotent (n : ℕ) (f : PosetCochain (R:=R) F n) :
    poset_b F (n+1) (poset_b F n f) = 0 := by
  apply embedPoset_injective F (n+2)
  rw [embed_poset_b,embed_poset_b,Paper001Concrete.poset_b_nilpotent]
  funext x z l
  simp [embedPoset,lift]

theorem poset_d_square (n : ℕ) (a : PosetCochain (R:=R) F 0) (f : PosetCochain (R:=R) F n) :
    poset_d F (n+1) a (poset_d F n a f) =
    restrict F (n+2) (cup F 1 (extend F 1 (poset_curvature F a)) (extend F n f) -
      cup F n (extend F n f) (extend F 1 (poset_curvature F a))) := by
  apply embedPoset_injective F (n+2)
  simp only [embed_poset_d,embed_restrict,embed_sub,embed_cup,embed_extend,
    embed_poset_curvature,Paper001Concrete.poset_d_square]
end Poset

#print axioms extract_lift
#print axioms lift_comp
#print axioms embed_b
#print axioms embed_cup
#print axioms b_square
#print axioms b_leibniz
#print axioms covariant_square
#print axioms vertex_selector_detector
#print axioms covariant_selector_detector
#print axioms embed_poset_cup
#print axioms poset_b_nilpotent
#print axioms poset_d_square
end Paper001Heterogeneous
