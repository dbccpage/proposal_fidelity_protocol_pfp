import Derivation.Compression

/-!
# Finite weight profiles and a declared signed-square shadow

A weight assignment is a DECLARED datum: a natural-number count at a
label in a finite presentation.  Nothing in the passage calculus
produces one; like protection, budget, and observer transport, it is
supplied.  Carrier-facing uses require a duplicate-free label list.
The underlying list sum deliberately counts repeated labels with
multiplicity, but such a list is not called a carrier here.

1. **The profile, without division.**  Two assignments have the same
   profile exactly when they agree after cross-multiplying by each
   other's totals (`SameProfile`).  Reflexivity and symmetry hold on
   all lists; transitivity requires a positive middle total.  Thus it
   is an equivalence after restricting to positive-total assignments
   (`profile_equivalence_positive`).  Positive scaling preserves both
   the profile and the positive domain (`profile_scale_positive`).
   Zero scaling satisfies the raw equations but leaves that domain.
2. **What the profile preserves:** support (`profile_support`) and
   order (`profile_order`).  What it forgets: the total weight
   (`profile_forgets_total`).  Its positive-domain classes are exactly
   common positive cross-multiples (`profile_iff_ray`).
3. **A presentation adds nothing to the profile.**  Call any
   assignment `c` together with a declared map `m` a decorated
   presentation of `w` when the carrier list has no duplicates and
   `m ∘ c = w` there.  The resulting weight assignment has `w`'s
   profile (`presentation_profile_redundant`).
4. **The signed-square witness is narrowly scoped.**  Squaring is
   injective on natural counts, so an unsigned square presentation is
   determined on the declared carrier.  Over integer decorations the
   declared square map forgets a sign, and one declared two-input
   mixing read-out sees that sign (`signed_square_presentations_split`).
   This is a finite sign-shadow witness, not a construction of a
   vector space, dynamics, or any richer carrier.
5. **Descent classification.**  For exactly two integer coordinates,
   a declared linear read-out followed by squaring is constant on
   coordinate-square fibers exactly when one coefficient vanishes
   (`descent_iff_subsingleton_support`).
6. **There is no priced climb here.**  The previously proposed
   decorated-carrier existential has an elementary witness, list
   append additivity is a theorem (`total_append`), and the proposed
   scalar uniqueness proposition is false by the zero read-out
   (`claimedReadOutUniqueness_false`).

Nothing here derives a vector-space representation, dynamics, or a
read-out uniqueness law.  What is derived is exactly the finite
weight-profile algebra and the scope of one signed-square witness.
-/

namespace WeightProfile

/-! ## 1. The profile, without division -/

/-- A declared weight assignment: a count per position. -/
abbrev Weights := Nat → Nat

/-- Carrier policy for this module: labels are presented once.  Raw list
algebra below remains meaningful with repetitions, where repetitions count
with multiplicity, but no carrier claim is made for such a list. -/
def CarrierList (l : List Nat) : Prop := l.Nodup

theorem duplicate_list_not_carrier : ¬ CarrierList [0, 0] := by
  simp [CarrierList]

/-- The declared total over a finite carrier. -/
def total (l : List Nat) (w : Weights) : Nat :=
  (l.map w).foldl (fun a b => a + b) 0

theorem foldl_add_acc (l : List Nat) (a : Nat) :
    l.foldl (fun x y => x + y) a
      = a + l.foldl (fun x y => x + y) 0 := by
  induction l generalizing a with
  | nil => simp
  | cons b t ih =>
      show t.foldl (fun x y => x + y) (a + b)
        = a + t.foldl (fun x y => x + y) (0 + b)
      rw [ih (a + b), ih (0 + b)]
      omega

theorem total_cons (p : Nat) (l : List Nat) (w : Weights) :
    total (p :: l) w = w p + total l w := by
  show (w p :: l.map w).foldl (fun a b => a + b) 0
    = w p + (l.map w).foldl (fun a b => a + b) 0
  show (l.map w).foldl (fun a b => a + b) (0 + w p)
    = w p + (l.map w).foldl (fun a b => a + b) 0
  rw [foldl_add_acc]
  omega

/-- Concatenation additivity belongs to the list sum already; it is not an
additional representation premise.  Overlapping label lists are counted with
multiplicity, as the definition says. -/
theorem total_append (l₁ l₂ : List Nat) (w : Weights) :
    total (l₁ ++ l₂) w = total l₁ w + total l₂ w := by
  induction l₁ with
  | nil => simp [total]
  | cons p t ih =>
      rw [List.cons_append, total_cons, total_cons, ih, Nat.add_assoc]

theorem total_scale (l : List Nat) (a : Nat) (w : Weights) :
    total l (fun p => a * w p) = a * total l w := by
  induction l with
  | nil => simp [total]
  | cons p t ih =>
      rw [total_cons, total_cons, ih, Nat.mul_add]

/-- Totals inherit a ray relation from the pointwise one. -/
theorem total_ray (l : List Nat) (a b : Nat) (w v : Weights)
    (hab : ∀ p ∈ l, a * w p = b * v p) :
    a * total l w = b * total l v := by
  induction l with
  | nil => rfl
  | cons q t ih =>
      rw [total_cons, total_cons, Nat.mul_add, Nat.mul_add,
          hab q List.mem_cons_self,
          ih (fun p hp => hab p (List.mem_cons_of_mem q hp))]

/-- Same normalized profile, stated without division: cross-multiply
by each other's totals. -/
def SameProfile (l : List Nat) (w v : Weights) : Prop :=
  ∀ p ∈ l, w p * total l v = v p * total l w

theorem profile_refl (l : List Nat) (w : Weights) :
    SameProfile l w w := fun _ _ => rfl

theorem profile_symm (l : List Nat) (w v : Weights)
    (h : SameProfile l w v) : SameProfile l v w :=
  fun p hp => (h p hp).symm

theorem profile_trans (l : List Nat) (w v u : Weights)
    (hv : 0 < total l v) (h1 : SameProfile l w v)
    (h2 : SameProfile l v u) : SameProfile l w u := by
  intro p hp
  have e1 := h1 p hp
  have e2 := h2 p hp
  have s1 : total l v * (w p * total l u)
      = (w p * total l v) * total l u := by
        ac_rfl
  have s2 : (v p * total l w) * total l u
      = (v p * total l u) * total l w := by
        ac_rfl
  have s3 : (u p * total l v) * total l w
      = total l v * (u p * total l w) := by
        ac_rfl
  have key : total l v * (w p * total l u)
      = total l v * (u p * total l w) := by
    rw [s1, e1, s2, e2, s3]
  exact Nat.eq_of_mul_eq_mul_left hv key

/-- The raw cross-product equations are scale invariant even at scale zero.
This theorem alone is not a positive-ray statement. -/
theorem profile_scale_raw (l : List Nat) (a : Nat) (w : Weights) :
    SameProfile l (fun p => a * w p) w := by
  intro p _
  show a * w p * total l w = w p * total l (fun q => a * w q)
  rw [total_scale]
  ac_rfl

/-- Positive rescaling preserves both the profile and membership in the
positive-total domain. -/
theorem profile_scale_positive (l : List Nat) (a : Nat) (w : Weights)
    (ha : 0 < a) (hw : 0 < total l w) :
    SameProfile l (fun p => a * w p) w ∧
      0 < total l (fun p => a * w p) := by
  refine ⟨profile_scale_raw l a w, ?_⟩
  rw [total_scale]
  exact Nat.mul_pos ha hw

/-- Exact equivalence-law package on the positive-total domain. -/
theorem profile_equivalence_positive (l : List Nat) :
    (∀ w : Weights, 0 < total l w → SameProfile l w w) ∧
    (∀ w v : Weights, 0 < total l w → 0 < total l v →
      SameProfile l w v → SameProfile l v w) ∧
    (∀ w v u : Weights, 0 < total l w → 0 < total l v →
      0 < total l u → SameProfile l w v → SameProfile l v u →
      SameProfile l w u) := by
  refine ⟨fun w _ => profile_refl l w, ?_, ?_⟩
  · exact fun w v _ _ h => profile_symm l w v h
  · exact fun w v u _ hv _ h₁ h₂ => profile_trans l w v u hv h₁ h₂

/-- Zero scaling satisfies `SameProfile` syntactically but exits the
positive-total domain whenever the source total is positive. -/
theorem zero_scale_boundary (l : List Nat) (w : Weights)
    (_hw : 0 < total l w) :
    SameProfile l (fun _ => 0) w ∧
      total l (fun _ => 0) = 0 ∧ ¬ 0 < total l (fun _ => 0) := by
  refine ⟨?_, ?_, ?_⟩
  · simpa using profile_scale_raw l 0 w
  · simpa using total_scale l 0 w
  · have hz : total l (fun _ => 0) = 0 := by
      simpa using total_scale l 0 w
    rw [hz]
    omega

/-- **Exact fiber classifier**: two positive-total assignments have
the same profile EXACTLY when they lie on a common positive ray. -/
theorem profile_iff_ray (l : List Nat) (w v : Weights)
    (hw : 0 < total l w) (hv : 0 < total l v) :
    SameProfile l w v ↔
      ∃ a b, 0 < a ∧ 0 < b ∧ ∀ p ∈ l, a * w p = b * v p := by
  constructor
  · intro h
    refine ⟨total l v, total l w, hv, hw, ?_⟩
    intro p hp
    have e := h p hp
    have s1 : total l v * w p = w p * total l v := Nat.mul_comm _ _
    have s2 : v p * total l w = total l w * v p := Nat.mul_comm _ _
    rw [s1, e, s2]
  · intro ⟨a, b, ha, hb, hab⟩
    have htot : a * total l w = b * total l v :=
      total_ray l a b w v hab
    intro p hp
    have hq := hab p hp
    have s1 : a * (w p * total l v) = (a * w p) * total l v := by
      ac_rfl
    have s2 : (b * v p) * total l v = v p * (b * total l v) := by
      ac_rfl
    have s3 : v p * (a * total l w) = a * (v p * total l w) := by
      ac_rfl
    have key : a * (w p * total l v) = a * (v p * total l w) := by
      rw [s1, hq, s2, ← htot, s3]
    exact Nat.eq_of_mul_eq_mul_left ha key

/-! ## 2. What the profile keeps, and what it forgets -/

/-- Support is preserved exactly. -/
theorem profile_support (l : List Nat) (w v : Weights)
    (hw : 0 < total l w) (hv : 0 < total l v)
    (h : SameProfile l w v) (p : Nat) (hp : p ∈ l) :
    (w p = 0 ↔ v p = 0) := by
  have e := h p hp
  constructor
  · intro h0
    rw [h0] at e
    simp only [Nat.zero_mul] at e
    rcases Nat.mul_eq_zero.mp e.symm with h1 | h1
    · exact h1
    · omega
  · intro h0
    rw [h0] at e
    simp only [Nat.zero_mul] at e
    rcases Nat.mul_eq_zero.mp e with h1 | h1
    · exact h1
    · omega

/-- Order is preserved exactly. -/
theorem profile_order (l : List Nat) (w v : Weights)
    (hw : 0 < total l w) (hv : 0 < total l v)
    (h : SameProfile l w v) (p q : Nat) (hp : p ∈ l) (hq : q ∈ l) :
    (w p ≤ w q ↔ v p ≤ v q) := by
  have ep := h p hp
  have eq' := h q hq
  constructor
  · intro hle
    have h1 : v p * total l w ≤ v q * total l w := by
      rw [← ep, ← eq']
      exact Nat.mul_le_mul_right _ hle
    have h2 : total l w * v p ≤ total l w * v q := by
      rw [Nat.mul_comm (total l w) (v p),
          Nat.mul_comm (total l w) (v q)]
      exact h1
    exact Nat.le_of_mul_le_mul_left h2 hw
  · intro hle
    have h1 : w p * total l v ≤ w q * total l v := by
      rw [ep, eq']
      exact Nat.mul_le_mul_right _ hle
    have h2 : total l v * w p ≤ total l v * w q := by
      rw [Nat.mul_comm (total l v) (w p),
          Nat.mul_comm (total l v) (w q)]
      exact h1
    exact Nat.le_of_mul_le_mul_left h2 hv

/-- **The profile forgets the total.**  Doubling every weight leaves
the profile fixed while changing the total — the forgotten datum,
exhibited. -/
theorem profile_forgets_total :
    SameProfile [0, 1] (fun p => 2 * (if p = 0 then 3 else 1))
      (fun p => if p = 0 then 3 else 1) ∧
    total [0, 1] (fun p => 2 * (if p = 0 then 3 else 1))
      ≠ total [0, 1] (fun p => if p = 0 then 3 else 1) := by
  refine ⟨profile_scale_raw [0, 1] 2 _, by decide⟩

/-! ## 3. A decorated presentation adds nothing to the profile -/

/-- A DECORATED PRESENTATION of `w`: an assignment `c` of decorated
values together with a declared modulus map `m` that returns the
weights.  Both `c` and `m` are supplied; neither is derived.  The
duplicate-free carrier policy is part of the predicate. -/
def Presents (l : List Nat) (m : Nat → Nat) (c : Nat → Nat)
    (w : Weights) : Prop :=
  CarrierList l ∧ ∀ p ∈ l, m (c p) = w p

theorem total_congr (l : List Nat) (w v : Weights)
    (h : ∀ p ∈ l, w p = v p) : total l w = total l v := by
  induction l with
  | nil => rfl
  | cons q t ih =>
      rw [total_cons, total_cons, h q List.mem_cons_self,
          ih (fun p hp => h p (List.mem_cons_of_mem q hp))]

/-- **Redundancy**: the profile read off a decorated presentation is
the profile of the weights.  One line, and that is the entire
content of the redundancy. -/
theorem presentation_profile_redundant (l : List Nat) (m : Nat → Nat)
    (c : Nat → Nat) (w : Weights) (h : Presents l m c w) :
    SameProfile l (fun p => m (c p)) w := by
  intro p hp
  show m (c p) * total l w = w p * total l (fun q => m (c q))
  rw [h.2 p hp, total_congr l (fun q => m (c q)) w h.2]

/-- **Any two decorated presentations of the same weights carry the
same profile** — whatever else differs between them. -/
theorem presentations_agree_on_profile (l : List Nat) (m : Nat → Nat)
    (c d : Nat → Nat) (w : Weights)
    (hc : Presents l m c w) (hd : Presents l m d w)
    (hpos : 0 < total l w) :
    SameProfile l (fun p => m (c p)) (fun p => m (d p)) := by
  have h1 := presentation_profile_redundant l m c w hc
  have h2 := presentation_profile_redundant l m d w hd
  exact profile_trans l _ w _ hpos h1 (profile_symm l _ w h2)

/-! ## 4. Unsigned determination and one declared signed-square shadow -/

/-- The declared modulus of this section: squaring. -/
def sq (x : Nat) : Nat := x * x

/-- Squaring is injective on natural counts. -/
theorem sq_mono {c d : Nat} (h : c < d) : sq c < sq d := by
  show c * c < d * d
  have h1 : c * c ≤ c * d := Nat.mul_le_mul_left c (Nat.le_of_lt h)
  have h2 : c * d < d * d := by
    rcases Nat.eq_zero_or_pos d with hd | hd
    · omega
    · exact Nat.mul_lt_mul_of_lt_of_le h (Nat.le_refl d) hd
  omega

theorem sq_injective (c d : Nat) (h : sq c = sq d) : c = d := by
  rcases Nat.lt_trichotomy c d with hlt | heq | hgt
  · have := sq_mono hlt
    omega
  · exact heq
  · have := sq_mono hgt
    omega

theorem unsigned_decoration_determined (l : List Nat)
    (c d : Nat → Nat) (w : Weights)
    (hc : Presents l sq c w) (hd : Presents l sq d w) :
    ∀ p ∈ l, c p = d p := by
  intro p hp
  exact sq_injective (c p) (d p) ((hc.2 p hp).trans (hd.2 p hp).symm)

/-- The declared integer square used only in this signed fixture. -/
def sqInt (x : Int) : Int := x * x

/-- A duplicate-free signed-square presentation of integer weights. -/
def SignedSquarePresents (l : List Nat) (c : Nat → Int)
    (w : Nat → Int) : Prop :=
  CarrierList l ∧ ∀ p ∈ l, sqInt (c p) = w p

/-- The declared two-input mixing read-out over integer decorations.
Nothing forces this read-out; it is part of the fixture. -/
def mixSum (x y : Int) : Int := (x + y) * (x + y)

def signedPlus : Nat → Int := fun _ => 1

def signedSplit : Nat → Int := fun p => if p = 0 then 1 else -1

def unitIntWeights : Nat → Int := fun _ => 1

/-- Two valid presentations of the SAME declared integer-square weights differ
on the carrier and are separated by the PARTICULAR declared mixing read-out.
This proves only a two-coordinate sign-shadow witness. -/
theorem signed_square_presentations_split :
    SignedSquarePresents [0, 1] signedPlus unitIntWeights ∧
    SignedSquarePresents [0, 1] signedSplit unitIntWeights ∧
    (∃ p ∈ [0, 1], signedPlus p ≠ signedSplit p) ∧
    mixSum (signedPlus 0) (signedPlus 1) ≠
      mixSum (signedSplit 0) (signedSplit 1) := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · refine ⟨by simp [CarrierList], ?_⟩
    intro p hp
    rcases List.mem_cons.mp hp with h | h
    · subst h; decide
    · rcases List.mem_cons.mp h with h' | h'
      · subst h'; decide
      · cases h'
  · refine ⟨by simp [CarrierList], ?_⟩
    intro p hp
    rcases List.mem_cons.mp hp with h | h
    · subst h; decide
    · rcases List.mem_cons.mp h with h' | h'
      · subst h'; decide
      · cases h'
  · exact ⟨1, by decide, by decide⟩
  · decide

/-- The exact scoped summary: unsigned square presentations agree on the
carrier, while the separate signed fixture above has two presentations that
the separately declared mixing read-out distinguishes. -/
theorem presentation_scope (l : List Nat) (c d : Nat → Nat)
    (w : Weights) (hc : Presents l sq c w) (hd : Presents l sq d w) :
    SameProfile l (fun p => sq (c p)) w ∧
    (∀ p ∈ l, c p = d p) ∧
    mixSum (signedPlus 0) (signedPlus 1) ≠
      mixSum (signedSplit 0) (signedSplit 1) :=
  ⟨presentation_profile_redundant l sq c w hc,
   unsigned_decoration_determined l c d w hc hd,
   signed_square_presentations_split.2.2.2⟩

/-! ## 5. Descent classification for declared linear read-outs -/

/-- A declared read-out over two positions with integer weights. -/
def readOut (a b x y : Int) : Int := a * x + b * y

/-- Modulus-blind inputs: the squares agree position by position. -/
def ModulusBlind (x y x' y' : Int) : Prop :=
  x * x = x' * x' ∧ y * y = y' * y'

/-- Squaring a product: the two-fold rearrangement used below. -/
theorem sq_mul (x y : Int) : (x * y) * (x * y) = (x * x) * (y * y) := by
  rw [Int.mul_assoc, ← Int.mul_assoc y x y, Int.mul_comm y x,
      Int.mul_assoc x y y, ← Int.mul_assoc]

/-- The exact gap between the two sign choices: four times the cross
term.  This is the whole obstruction, isolated. -/
theorem sq_add_sub (a b : Int) :
    (a + b) * (a + b) = (a - b) * (a - b) + 4 * (a * b) := by
  have h1 : (a + b) * (a + b) = a * a + a * b + (b * a + b * b) := by
    rw [Int.add_mul, Int.mul_add, Int.mul_add]
  have h2 : (a - b) * (a - b) = a * a - a * b - (b * a - b * b) := by
    rw [Int.sub_mul, Int.mul_sub, Int.mul_sub]
  have hc : b * a = a * b := Int.mul_comm b a
  rw [h1, h2, hc]
  omega

/-- **Descent classification (two positions)**: the squared read-out
is constant on modulus-blind inputs EXACTLY when the read-out does not
mix — that is, when one of its two coefficients vanishes.  The
obstruction is precisely the cross term, and `sq_add_sub` measures
it. -/
theorem descent_iff_subsingleton_support (a b : Int) :
    (∀ x y x' y', ModulusBlind x y x' y' →
      readOut a b x y * readOut a b x y
        = readOut a b x' y' * readOut a b x' y')
    ↔ a * b = 0 := by
  constructor
  · intro h
    have hblind : ModulusBlind 1 1 1 (-1) := by
      constructor <;> decide
    have hEq := h 1 1 1 (-1) hblind
    have e1 : readOut a b 1 1 = a + b := by
      show a * 1 + b * 1 = a + b
      rw [Int.mul_one, Int.mul_one]
    have e2 : readOut a b 1 (-1) = a - b := by
      show a * 1 + b * (-1) = a - b
      rw [Int.mul_one, Int.mul_neg, Int.mul_one]
      omega
    rw [e1, e2, sq_add_sub a b] at hEq
    omega
  · intro hab x y x' y' ⟨hx, hy⟩
    rcases Int.mul_eq_zero.mp hab with ha | hb
    · have hr : ∀ u v : Int, readOut a b u v = b * v := by
        intro u v
        show a * u + b * v = b * v
        rw [ha, Int.zero_mul, Int.zero_add]
      rw [hr, hr, sq_mul, sq_mul, hy]
    · have hr : ∀ u v : Int, readOut a b u v = a * u := by
        intro u v
        show a * u + b * v = a * u
        rw [hb, Int.zero_mul, Int.add_zero]
      rw [hr, hr, sq_mul, sq_mul, hx]

/-! ## 6. Audit of the proposed climb -/

/-- The bare decorated-carrier shape previously listed as an open import is
already inhabited by naturals with the identity map and addition.  This says
nothing about a distinguished representation; it only shows that the old
existential was too weak to be a rung. -/
theorem decoratedCarrierShape_exists :
    ∃ (D : Type) (m : D → Nat) (op : D → D → D),
      (∀ n : Nat, ∃ d : D, m d = n) ∧
      ∀ d e : D, m (op d e) = m (op e d) := by
  refine ⟨Nat, (fun n => n), (fun d e => d + e), ?_, ?_⟩
  · exact fun n => ⟨n, rfl⟩
  · exact fun d e => Nat.add_comm d e

/-- The exact scalar uniqueness schema previously presented as an open import.
It is retained only so that its failure can be stated and checked. -/
def ClaimedReadOutUniqueness : Prop :=
  ∀ (F : List Nat → Weights → Nat) (l : List Nat) (w : Weights),
    0 < total l w →
    (∀ v, SameProfile l w v → F l w = F l v) →
    (∀ l1 l2 v, F (l1 ++ l2) v = F l1 v + F l2 v) →
    F l w = total l w

/-- The zero read-out satisfies the displayed invariance and append equations,
but it is not the positive total on a singleton.  Hence the old uniqueness
schema is inconsistent, not an unpaid theorem. -/
theorem claimedReadOutUniqueness_false : ¬ ClaimedReadOutUniqueness := by
  intro h
  have hzero := h (fun _ _ => 0) [0] (fun _ => 1) (by decide)
    (by intro _ _; rfl) (by intro _ _ _; rfl)
  have hone : total [0] (fun _ => 1) = 1 := by decide
  rw [hone] at hzero
  omega

/-- The scope line for the corrected module.  It packages only results actually
proved here: positive-ray classification, positive scaling, and presentation
profile redundancy. -/
theorem finite_scope_summary (l : List Nat) (w v : Weights)
    (hw : 0 < total l w) (hv : 0 < total l v) (a : Nat) (ha : 0 < a) :
    (SameProfile l w v ↔
      ∃ p q, 0 < p ∧ 0 < q ∧ ∀ x ∈ l, p * w x = q * v x) ∧
    (SameProfile l (fun p => a * w p) w ∧
      0 < total l (fun p => a * w p)) ∧
    (∀ (m : Nat → Nat) (c : Nat → Nat), Presents l m c w →
      SameProfile l (fun p => m (c p)) w) :=
  ⟨profile_iff_ray l w v hw hv, profile_scale_positive l a w ha hw,
   fun m c h => presentation_profile_redundant l m c w h⟩

end WeightProfile
