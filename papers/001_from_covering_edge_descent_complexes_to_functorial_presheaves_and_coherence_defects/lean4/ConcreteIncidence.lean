import Mathlib.Tactic.NoncommRing
import Mathlib.Tactic.Abel
import Mathlib.Data.List.Basic
import Mathlib.Algebra.Module.Defs
import Mathlib.Data.List.Pairwise

/-!
Concrete internal-deletion algebra on endpoint-labelled words. Restricting to
strict chains in any poset gives its incidence cochains: internal deletion and
overlapping cuts retain strictness and endpoints. A degree n>=1 component is
evaluated on an interior list of length n-1. Coefficients may be a noncommutative
ring, for example endomorphism matrices. No differential laws are assumed.
-/
namespace Paper001Concrete

section Additive
variable {P R : Type*} [AddCommGroup R]

def alternating (f : List P → R) : List P → R
  | [] => 0
  | a :: l => f l - alternating (fun t => f (a :: t)) l

theorem alternating_add (f g : List P → R) (l : List P) :
    alternating (fun t => f t + g t) l = alternating f l + alternating g l := by
  induction l generalizing f g with
  | nil => simp [alternating]
  | cons a l ih => simp only [alternating, ih]; abel

theorem alternating_neg (f : List P → R) (l : List P) :
    alternating (fun t => -f t) l = -alternating f l := by
  induction l generalizing f with
  | nil => simp [alternating]
  | cons a l ih => simp only [alternating, ih]; abel

theorem alternating_sub (f g : List P → R) (l : List P) :
    alternating (fun t => f t - g t) l = alternating f l - alternating g l := by
  simp only [sub_eq_add_neg, alternating_add, alternating_neg]

theorem alternating_congr (f g : List P → R) (l : List P)
    (h : ∀ t, t.Sublist l → t.length+1=l.length → f t=g t) :
    alternating f l = alternating g l := by
  induction l generalizing f g with
  | nil => rfl
  | cons a l ih =>
    simp only [alternating]
    have head : f l = g l := h l (List.Sublist.cons a (List.Sublist.refl l)) (by simp)
    rw [head]
    congr 1
    apply ih
    intro t ht hn
    apply h (a::t) (ht.cons_cons a)
    simp only [List.length_cons] at hn ⊢
    omega

theorem alternating_square (f : List P → R) (l : List P) :
    alternating (alternating f) l = 0 := by
  induction l generalizing f with
  | nil => rfl
  | cons a l ih =>
    simp only [alternating]
    change alternating f l - alternating (fun t => f t - alternating (fun u => f (a :: u)) t) l = 0
    rw [alternating_sub, ih]
    abel

theorem alternating_map {S : Type*} [AddCommGroup S] (φ : R →+ S)
    (f : List P → R) (l : List P) :
    alternating (fun t => φ (f t)) l = φ (alternating f l) := by
  induction l generalizing f with
  | nil => simp [alternating]
  | cons a l ih => simp [alternating,ih,map_sub]

end Additive
variable {P R : Type*} [Ring R]

theorem alternating_mul_left (c : R) (f : List P → R) (l : List P) :
    alternating (fun t => c * f t) l = c * alternating f l := by
  induction l generalizing f with
  | nil => simp [alternating]
  | cons a l ih => simp only [alternating, ih]; noncomm_ring

theorem alternating_mul_right (c : R) (f : List P → R) (l : List P) :
    alternating (fun t => f t * c) l = alternating f l * c := by
  induction l generalizing f with
  | nil => simp [alternating]
  | cons a l ih => simp only [alternating, ih]; noncomm_ring

abbrev Cochain := P → List P → P → R

def shift (f : Cochain (P:=P) (R:=R)) (a : P) : Cochain (P:=P) (R:=R) :=
  fun x l z => f x (a :: l) z

@[simp] theorem shift_add (f g : Cochain (P:=P) (R:=R)) (a : P) :
    shift (f+g) a = shift f a + shift g a := rfl

@[simp] theorem shift_neg (f : Cochain (P:=P) (R:=R)) (a : P) :
    shift (-f) a = -shift f a := rfl

def b (f : Cochain (P:=P) (R:=R)) : Cochain (P:=P) (R:=R) :=
  fun x l z => -alternating (fun t => f x t z) l

theorem b_cons (f : Cochain (P:=P) (R:=R)) (a x z : P) (l : List P) :
    b f x (a :: l) z = -f x l z - b (shift f a) x l z := by
  simp only [b, alternating, shift]
  abel

@[simp] theorem b_add (f g : Cochain (P:=P) (R:=R)) : b (f+g)=b f+b g := by
  funext x l z
  simp [b, alternating_add]; abel

@[simp] theorem b_neg (f : Cochain (P:=P) (R:=R)) : b (-f) = -b f := by
  funext x l z
  simp [b, alternating_neg]

@[simp] theorem b_sub (f g : Cochain (P:=P) (R:=R)) : b (f-g)=b f-b g := by
  simp [sub_eq_add_neg]

theorem b_square (f : Cochain (P:=P) (R:=R)) : b (b f) = 0 := by
  funext x l z
  simp [b, alternating_neg, alternating_square]

theorem shift_b (f : Cochain (P:=P) (R:=R)) (a : P) :
    shift (b f) a = -f - b (shift f a) := by
  funext x l z
  exact b_cons f a x z l

/-- Positive-degree overlapping cup: n is the left interior length, so its
left factor has degree n+1. At its pivot, endpoint labels match exactly. -/
def cup : ℕ → Cochain (P:=P) (R:=R) → Cochain (P:=P) (R:=R) → Cochain (P:=P) (R:=R)
  | _, _, _, _, [], _ => 0
  | 0, f, g, x, a :: l, z => f x [] a * g a l z
  | n+1, f, g, x, a :: l, z => cup n (shift f a) g x l z

@[simp] theorem cup_add_left (n : ℕ) (f g h : Cochain (P:=P) (R:=R)) :
    cup n (f+g) h = cup n f h + cup n g h := by
  induction n generalizing f g h with
  | zero => funext x l z; cases l <;> simp [cup, add_mul]
  | succ n ih => funext x l z; cases l <;> simp [cup, ih]

@[simp] theorem cup_add_right (n : ℕ) (f g h : Cochain (P:=P) (R:=R)) :
    cup n f (g+h) = cup n f g + cup n f h := by
  induction n generalizing f g h with
  | zero => funext x l z; cases l <;> simp [cup, mul_add]
  | succ n ih => funext x l z; cases l <;> simp [cup, ih]

@[simp] theorem cup_neg_left (n : ℕ) (f g : Cochain (P:=P) (R:=R)) :
    cup n (-f) g = -cup n f g := by
  induction n generalizing f g with
  | zero => funext x l z; cases l <;> simp [cup]
  | succ n ih => funext x l z; cases l <;> simp [cup, ih]

@[simp] theorem cup_neg_right (n : ℕ) (f g : Cochain (P:=P) (R:=R)) :
    cup n f (-g) = -cup n f g := by
  induction n generalizing f g with
  | zero => funext x l z; cases l <;> simp [cup]
  | succ n ih => funext x l z; cases l <;> simp [cup, ih]

def signed (n : ℕ) (f : Cochain (P:=P) (R:=R)) : Cochain (P:=P) (R:=R) :=
  fun x l z => (-1 : ℤ)^n • f x l z

@[simp] theorem signed_zero (f : Cochain (P:=P) (R:=R)) : signed 0 f = f := by
  funext x l z; simp [signed]

theorem signed_succ (n : ℕ) (f : Cochain (P:=P) (R:=R)) :
    signed (n+1) f = -signed n f := by
  funext x l z
  simp [signed, pow_succ]

@[simp] theorem b_signed (n : ℕ) (f : Cochain (P:=P) (R:=R)) :
    b (signed n f) = signed n (b f) := by
  induction n with
  | zero => simp
  | succ n ih => simp [signed_succ, ih]

@[simp] theorem cup_signed_left (m n : ℕ) (f g : Cochain (P:=P) (R:=R)) :
    cup m (signed n f) g = signed n (cup m f g) := by
  induction n with
  | zero => simp
  | succ n ih => simp [signed_succ, ih]

@[simp] theorem cup_signed_right (m n : ℕ) (f g : Cochain (P:=P) (R:=R)) :
    cup m f (signed n g) = signed n (cup m f g) := by
  induction n with
  | zero => simp
  | succ n ih => simp [signed_succ, ih]

theorem b_leibniz (n : ℕ) (f g : Cochain (P:=P) (R:=R)) :
    b (cup n f g) = cup (n+1) (b f) g + signed (n+1) (cup n f (b g)) := by
  induction n generalizing f g with
  | zero =>
    funext x l z
    cases l with
    | nil => simp [b,cup,alternating,signed,smul_zero]
    | cons a l =>
      rw [b_cons]
      have h : b (shift (cup 0 f g) a) x l z = f x [] a * b g a l z := by
        simp only [b,shift,cup,alternating_mul_left]
        noncomm_ring
      rw [h]
      cases l <;> simp [cup,b,alternating,shift,signed]
      all_goals noncomm_ring
  | succ n ih =>
    funext x l z
    cases l with
    | nil => simp [b,cup,alternating,signed,smul_zero]
    | cons a l =>
      rw [b_cons]
      change -cup (n+1) f g x l z - b (cup n (shift f a) g) x l z = _
      rw [ih]
      simp only [Pi.add_apply, cup, shift_b, sub_eq_add_neg, cup_add_left,
        cup_neg_left, signed_succ, Pi.neg_apply]
      abel

theorem cup_fixed_left (n : ℕ) (c : P → R) (a : P) (g h : Cochain (P:=P) (R:=R)) :
    cup n (fun x l z => c x * g a l z) h = fun x l z => c x * cup n g h a l z := by
  induction n generalizing g h with
  | zero => funext x l z; cases l <;> simp [cup,mul_assoc]
  | succ n ih =>
    funext x l z
    cases l with
    | nil => simp [cup]
    | cons v l =>
      change cup n (fun x t z => c x * shift g v a t z) h x l z = c x * cup n (shift g v) h a l z
      rw [ih]

theorem cup_assoc (n m : ℕ) (f g h : Cochain (P:=P) (R:=R)) :
    cup (n+m+1) (cup n f g) h = cup n f (cup m g h) := by
  induction n generalizing f g h with
  | zero =>
    funext x l z
    cases l with
    | nil => simp [cup]
    | cons a l =>
      simp only [Nat.zero_add]
      change cup m (fun x t z => f x [] a * g a t z) h x l z = f x [] a * cup m g h a l z
      rw [cup_fixed_left]
  | succ n ih =>
    funext x l z
    cases l with
    | nil => simp [cup]
    | cons a l =>
      have hn : n+1+m+1 = (n+m+1)+1 := by omega
      rw [hn]
      change cup (n+m+1) (cup n (shift f a) g) h x l z = cup n (shift f a) (cup m g h) x l z
      rw [ih]

@[simp] theorem signed_neg (n : ℕ) (f : Cochain (P:=P) (R:=R)) :
    signed n (-f) = -signed n f := by
  funext x l z; simp [signed]

@[simp] theorem signed_add (n : ℕ) (f g : Cochain (P:=P) (R:=R)) :
    signed n (f+g) = signed n f + signed n g := by
  induction n with
  | zero => simp
  | succ n ih => simp [signed_succ,ih]; abel

@[simp] theorem signed_twice (n : ℕ) (f : Cochain (P:=P) (R:=R)) :
    signed n (signed n f) = f := by
  induction n with
  | zero => simp
  | succ n ih => simp [signed_succ,ih]

def curvature (a : Cochain (P:=P) (R:=R)) := b a + cup 0 a a

def covariant (n : ℕ) (a f : Cochain (P:=P) (R:=R)) :=
  b f + cup 0 a f - signed (n+1) (cup n f a)

theorem covariant_square (n : ℕ) (a f : Cochain (P:=P) (R:=R)) :
    covariant (n+1) a (covariant n a f) = cup 1 (curvature a) f - cup n f (curvature a) := by
  simp only [covariant, curvature, sub_eq_add_neg, b_add, b_neg, b_signed,
    b_square, b_leibniz, cup_add_left, cup_add_right, cup_neg_left, cup_neg_right,
    cup_signed_left, cup_signed_right, signed_add, signed_neg, signed_twice]
  have h₁ := cup_assoc 0 0 a a f
  have h₂ := cup_assoc 0 n a f a
  have h₃ := cup_assoc n 0 f a a
  simp only [Nat.zero_add,Nat.add_zero] at h₁ h₂ h₃
  rw [← h₁,h₂,h₃]
  simp only [signed_succ, signed_zero, signed_neg, signed_twice]
  abel

def left (u : P → R) (f : Cochain (P:=P) (R:=R)) : Cochain (P:=P) (R:=R) :=
  fun x l z => u x * f x l z

def right (f : Cochain (P:=P) (R:=R)) (u : P → R) : Cochain (P:=P) (R:=R) :=
  fun x l z => f x l z * u z

@[simp] theorem b_left (u : P → R) (f : Cochain (P:=P) (R:=R)) :
    b (left u f) = left u (b f) := by
  funext x l z
  simp [b,left,alternating_mul_left]

@[simp] theorem b_right (u : P → R) (f : Cochain (P:=P) (R:=R)) :
    b (right f u) = right (b f) u := by
  funext x l z
  simp [b,right,alternating_mul_right]

@[simp] theorem cup_left (n : ℕ) (u : P → R) (f g : Cochain (P:=P) (R:=R)) :
    cup n (left u f) g = left u (cup n f g) := by
  induction n generalizing f g with
  | zero => funext x l z; cases l <;> simp [cup,left,mul_assoc]
  | succ n ih =>
    funext x l z
    cases l with
    | nil => simp [cup,left]
    | cons a l =>
      change cup n (left u (shift f a)) g x l z = u x * cup n (shift f a) g x l z
      rw [ih]; rfl

@[simp] theorem cup_right (n : ℕ) (u : P → R) (f g : Cochain (P:=P) (R:=R)) :
    cup n f (right g u) = right (cup n f g) u := by
  induction n generalizing f g with
  | zero => funext x l z; cases l <;> simp [cup,right,mul_assoc]
  | succ n ih => funext x l z; cases l <;> simp [cup,right,ih]

theorem cup_middle (n : ℕ) (u : P → R) (f g : Cochain (P:=P) (R:=R)) :
    cup n (right f u) g = cup n f (left u g) := by
  induction n generalizing f g with
  | zero => funext x l z; cases l <;> simp [cup,right,left,mul_assoc]
  | succ n ih =>
    funext x l z
    cases l with
    | nil => simp [cup]
    | cons a l =>
      change cup n (right (shift f a) u) g x l z = cup n (shift f a) (left u g) x l z
      rw [ih]

def covariant_zero (a : Cochain (P:=P) (R:=R)) (u : P → R) := right a u - left u a

theorem covariant_square_zero (a : Cochain (P:=P) (R:=R)) (u : P → R) :
    covariant 0 a (covariant_zero a u) = right (curvature a) u - left u (curvature a) := by
  simp only [covariant,covariant_zero,curvature,sub_eq_add_neg,b_add,b_neg,
    b_right,b_left,cup_add_left,cup_add_right,cup_neg_left,cup_neg_right,
    cup_right,cup_left,cup_middle,signed_succ,signed_zero]
  funext x l z
  simp only [right,left,Pi.add_apply,Pi.neg_apply]
  noncomm_ring

/-- Actual strict poset-chain component of positive degree n+1. -/
def StrictInterior (P : Type*) [PartialOrder P] (x z : P) (n : ℕ) :=
  {l : List P // l.length = n ∧ List.Pairwise (· < ·) (x :: l ++ [z])}

abbrev PosetCochain (P R : Type*) [PartialOrder P] (n : ℕ) :=
  ∀ x z : P, StrictInterior P x z n → R

def restrict [PartialOrder P] (n : ℕ) (f : Cochain (P:=P) (R:=R)) : PosetCochain P R n :=
  fun x z l => f x l.val z

noncomputable def extend [PartialOrder P] (n : ℕ) (f : PosetCochain P R n) : Cochain (P:=P) (R:=R) := by
  classical
  exact fun x l z => if h : l.length=n ∧ List.Pairwise (· < ·) (x :: l ++ [z])
    then f x z ⟨l,h⟩ else 0

theorem restrict_extend [PartialOrder P] (n : ℕ) (f : PosetCochain P R n) :
    restrict n (extend n f) = f := by
  funext x z l
  simp only [restrict,extend,dite_eq_left l.property]
  rfl

theorem strict_subchain [PartialOrder P] (x z : P) (l t : List P)
    (hl : List.Pairwise (· < ·) (x :: l ++ [z])) (ht : t.Sublist l) :
    List.Pairwise (· < ·) (x :: t ++ [z]) := by
  exact hl.sublist ((ht.append_right [z]).cons_cons x)

noncomputable def poset_b [PartialOrder P] (n : ℕ) (f : PosetCochain P R n) : PosetCochain P R (n+1) :=
  restrict (n+1) (b (extend n f))

theorem poset_b_nilpotent [PartialOrder P] (n : ℕ) (f : PosetCochain P R n) :
    poset_b (n+1) (poset_b n f) = 0 := by
  classical
  funext x z l
  change -alternating (fun t => extend (n+1) (poset_b n f) x t z) l.val = 0
  have h := alternating_congr
    (fun t => extend (n+1) (poset_b n f) x t z)
    (fun t => b (extend n f) x t z) l.val (by
      intro t ht hlen
      have hn : t.length=n+1 := by have := l.property.1; omega
      have hv := strict_subchain x z l.val t l.property.2 ht
      have hh : t.length=n+1 ∧ List.Pairwise (· < ·) (x :: t ++ [z]) := ⟨hn,hv⟩
      simp only [extend,dite_eq_left hh,poset_b,restrict])
  rw [h]
  exact congrFun (congrFun (congrFun (b_square (extend n f)) x) l.val) z

theorem cup_split (f g : Cochain (P:=P) (R:=R)) (x a z : P) (l r : List P) :
    cup l.length f g x (l++a::r) z = f x l a * g a r z := by
  induction l generalizing f g with
  | nil => rfl
  | cons v l ih => simpa only [List.length_cons,List.cons_append,cup,shift] using ih (shift f v) g

def OnDegree [PartialOrder P] (n : ℕ) (f g : Cochain (P:=P) (R:=R)) : Prop :=
  ∀ x z l, l.length=n → List.Pairwise (· < ·) (x::l++[z]) → f x l z=g x l z

theorem extend_restrict_on [PartialOrder P] (n : ℕ) (f : Cochain (P:=P) (R:=R)) :
    OnDegree n (extend n (restrict n f)) f := by
  classical
  intro x z l hn hv
  have hh : l.length=n ∧ List.Pairwise (· < ·) (x::l++[z]) := ⟨hn,hv⟩
  simp only [extend,dite_eq_left hh,restrict]

theorem b_on [PartialOrder P] (n : ℕ) (f g : Cochain (P:=P) (R:=R))
    (h : OnDegree n f g) : OnDegree (n+1) (b f) (b g) := by
  intro x z l hn hv
  unfold b
  congr 1
  apply alternating_congr
  intro t ht hlen
  apply h x z t
  · omega
  · exact strict_subchain x z l t hv ht

theorem cup_on [PartialOrder P] (n m : ℕ) (f f' g g' : Cochain (P:=P) (R:=R))
    (hf : OnDegree n f f') (hg : OnDegree m g g') :
    OnDegree (n+m+1) (cup n f g) (cup n f' g') := by
  intro x z l hn hv
  have hnlt : n<l.length := by omega
  let left := l.take n
  let pivot := l[n]
  let right := l.drop (n+1)
  have split : l=left++pivot::right := by
    simpa only [left,pivot,right,List.drop_eq_getElem_cons hnlt] using (List.take_append_drop n l).symm
  have hleft : left.length=n := by simp [left,List.length_take,Nat.min_eq_left (by omega : n≤l.length)]
  have hright : right.length=m := by simp only [right,List.length_drop]; omega
  have vl : List.Pairwise (· < ·) (x::left++[pivot]) := by
    rw [split] at hv
    refine List.Pairwise.sublist ?_ hv
    simpa only [List.cons_append,List.append_assoc] using
      ((List.nil_sublist (right++[z])).cons_cons pivot |>.append_left left |>.cons_cons x)
  have vr : List.Pairwise (· < ·) (pivot::right++[z]) := by
    rw [split] at hv
    refine List.Pairwise.sublist ?_ hv
    simpa only [List.cons_append,List.append_assoc] using
      List.sublist_append_right (x::left) (pivot::right++[z])
  rw [split,←hleft,cup_split,cup_split,hf x pivot left hleft vl,hg pivot z right hright vr]

theorem covariant_on [PartialOrder P] (n : ℕ) (a f g : Cochain (P:=P) (R:=R))
    (h : OnDegree n f g) : OnDegree (n+1) (covariant n a f) (covariant n a g) := by
  have h₁ := b_on n f g h
  have h₂ := cup_on 0 n a a f g (by intro x z l hn hv; rfl) h
  have h₃ := cup_on n 0 f g a a h (by intro x z l hn hv; rfl)
  intro x z l hn hv
  have len₂ : l.length=0+n+1 := by omega
  have len₃ : l.length=n+0+1 := by omega
  simp only [covariant,Pi.add_apply,Pi.sub_apply,signed,h₁ x z l hn hv,h₂ x z l len₂ hv,h₃ x z l len₃ hv]

noncomputable def poset_cup [PartialOrder P] (n m : ℕ)
    (f : PosetCochain P R n) (g : PosetCochain P R m) : PosetCochain P R (n+m+1) :=
  restrict (n+m+1) (cup n (extend n f) (extend m g))

theorem poset_leibniz [PartialOrder P] (n m : ℕ)
    (f : PosetCochain P R n) (g : PosetCochain P R m) :
    poset_b (n+m+1) (poset_cup n m f g) =
    restrict (n+m+2) (cup (n+1) (extend (n+1) (poset_b n f)) (extend m g) +
      signed (n+1) (cup n (extend n f) (extend (m+1) (poset_b m g)))) := by
  have hb := b_on (n+m+1) _ _ (extend_restrict_on (n+m+1) (cup n (extend n f) (extend m g)))
  have hl := cup_on (n+1) m _ _ (extend m g) (extend m g)
    (extend_restrict_on (n+1) (b (extend n f))) (by intro x z l hn hv; rfl)
  have hr := cup_on n (m+1) (extend n f) (extend n f) _ _
    (by intro x z l hn hv; rfl) (extend_restrict_on (m+1) (b (extend m g)))
  funext x z l
  have hlen := l.property.1
  have hv := l.property.2
  change b (extend (n+m+1) (restrict (n+m+1) (cup n (extend n f) (extend m g)))) x l.val z = _
  rw [hb x z l.val hlen hv]
  rw [b_leibniz]
  have lp : l.val.length=(n+1)+m+1 := by omega
  have rp : l.val.length=n+(m+1)+1 := by omega
  simp only [restrict,Pi.add_apply,signed,poset_b]
  rw [hl x z l.val lp hv,hr x z l.val rp hv]

noncomputable def poset_d [PartialOrder P] (n : ℕ)
    (a : PosetCochain P R 0) (f : PosetCochain P R n) : PosetCochain P R (n+1) :=
  restrict (n+1) (covariant n (extend 0 a) (extend n f))

noncomputable def poset_curvature [PartialOrder P] (a : PosetCochain P R 0) : PosetCochain P R 1 :=
  restrict 1 (curvature (extend 0 a))

theorem poset_d_square [PartialOrder P] (n : ℕ)
    (a : PosetCochain P R 0) (f : PosetCochain P R n) :
    poset_d (n+1) a (poset_d n a f) =
    restrict (n+2) (cup 1 (extend 1 (poset_curvature a)) (extend n f) -
      cup n (extend n f) (extend 1 (poset_curvature a))) := by
  have hd := covariant_on (n+1) (extend 0 a) _ _
    (extend_restrict_on (n+1) (covariant n (extend 0 a) (extend n f)))
  have hk := extend_restrict_on 1 (curvature (extend 0 a))
  have hl := cup_on 1 n _ _ (extend n f) (extend n f) hk (by intro x z l hn hv; rfl)
  have hr := cup_on n 1 (extend n f) (extend n f) _ _ (by intro x z l hn hv; rfl) hk
  funext x z l
  have hn := l.property.1
  have hv := l.property.2
  change covariant (n+1) (extend 0 a)
    (extend (n+1) (restrict (n+1) (covariant n (extend 0 a) (extend n f)))) x l.val z = _
  rw [hd x z l.val hn hv,covariant_square]
  have lp : l.val.length=1+n+1 := by omega
  have rp : l.val.length=n+1+1 := by omega
  simp only [restrict,Pi.sub_apply,poset_curvature]
  rw [hl x z l.val lp hv,hr x z l.val rp hv]

theorem poset_b_square [PartialOrder P] (n : ℕ) (f : Cochain (P:=P) (R:=R)) :
    restrict n (b (b f)) = 0 := by rw [b_square]; rfl

theorem poset_covariant_square [PartialOrder P] (n : ℕ) (a f : Cochain (P:=P) (R:=R)) :
    restrict (n+2) (covariant (n+1) a (covariant n a f)) =
    restrict (n+2) (cup 1 (curvature a) f - cup n f (curvature a)) := by
  rw [covariant_square]

#print axioms alternating_square
#print axioms b_square
#print axioms b_leibniz
#print axioms cup_assoc
#print axioms covariant_square
#print axioms covariant_square_zero
#print axioms restrict_extend
#print axioms strict_subchain
#print axioms poset_covariant_square
#print axioms poset_b_nilpotent
#print axioms poset_leibniz
#print axioms poset_d_square
end Paper001Concrete
