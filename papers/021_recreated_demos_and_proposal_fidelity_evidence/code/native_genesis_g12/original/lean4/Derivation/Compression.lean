import Derivation.PrimitiveCore

/-!
# Target-relative presentation compression

A represented finite domain `D : List Nat` (membership is the domain),
a declared question family `Q : List (Nat → Nat)` (the family is
represented data — a list, not a view from nowhere), and presentations
`p : Nat → Nat`.

Results, each scoped exactly:

* **A — factorization.**  A question factors through a presentation on
  `D` iff the presentation's fibers over `D` are question-constant
  (`factors_iff_fiberConstant`).  The factoring map is unique on the
  image of `D` (`factor_unique_on_image`) and provably not unique off
  it (`factor_not_unique_off_image`).
* **B — the signature quotient.**  `pQ D Q` sends each point to the
  first element of `D` carrying the same `Q`-signature.  Its fibers
  over `D` are exactly the signature classes (`pQ_exact`); it is
  `Q`-adequate (`pQ_adequate`); it factors through every `Q`-adequate
  presentation (`pQ_coarsest`), uniquely on that presentation's image
  over `D` (`pQ_unique_on_image`).  Nothing is claimed off-image or
  for undeclared question families.
* **C — descent failure.**  If a presentation merges two points that
  some declared question separates, a witnessing question is
  constructed (list recursion, no choice principle):
  `descent_witness`.
* **D — enlargement.**  Enlarging the family only refines agreement
  (`enlarge_refines`); a class splits exactly when the enlarged family
  carries a new separator across an old agreement
  (`splits_iff_new_separator`).
* **E — no absolute adequacy.**  A presentation is adequate for
  *every* family iff it is injective on `D`
  (`absolute_adequacy_iff_injective`): absolute adequacy is exactly
  no-compression.  Every genuine compression is adequate only
  *relative to* a declared, represented question family — the family,
  its source, and its revisions are represented data, never a view
  from nowhere.
* **F — repetition and digests add no questions.**  Duplicating the
  family (`dup_no_refine`) or appending a digest of existing answers
  (`postcompose_no_refine`) separates nothing new; a genuine split
  requires a question that is not signature-determined
  (`refine_requires_separator`).  Replay is evidential only when it
  carries a new represented separator.
* **Countermodels.**  Refinement is not unique
  (`refinement_not_unique`) and equal-cost refinements tie
  (`refinement_tie`): both recorded on `D = [0,1,2]`.
* **Bound.**  The class count never exceeds `D.length`
  (`refine_bounded`); a strict split strictly increases it
  (`strict_split_increases`); hence any chain of strictly-refining
  families over a nonempty `D` has length at most `D.length`
  (`chain_bounded`, `strict_steps_lt`).

Metatheory used (declared): types, functions, lists, propositional
logic, structural recursion, and the decidability apparatus of the
metalanguage (`Decidable`, `decide`).  No choice principles.
-/

namespace Compression

/-! ## Signatures and agreement -/

/-- The answer signature of `x` under the declared family `Q`: the
list of answers, in family order.  The family is represented data. -/
def sigList (Q : List (Nat → Nat)) (x : Nat) : List Nat :=
  Q.map (fun q => q x)

/-- Agreement of `x` and `x'` on every question of the declared
family. -/
def SigEq (Q : List (Nat → Nat)) (x x' : Nat) : Prop :=
  ∀ q, q ∈ Q → q x = q x'

/-- Family agreement is exactly signature equality. -/
theorem sigEq_iff_sigList (Q : List (Nat → Nat)) (x x' : Nat) :
    SigEq Q x x' ↔ sigList Q x = sigList Q x' := by
  induction Q with
  | nil => exact ⟨fun _ => rfl, fun _ q hq => by cases hq⟩
  | cons q T ih =>
    constructor
    · intro h
      show q x :: sigList T x = q x' :: sigList T x'
      rw [h q List.mem_cons_self,
        ih.mp (fun q' hq' => h q' (List.mem_cons_of_mem _ hq'))]
    · intro h q' hq'
      have hh : q x :: sigList T x = q x' :: sigList T x' := h
      injection hh with h1 h2
      cases hq' with
      | head => exact h1
      | tail _ hm => exact ih.mpr h2 q' hm

/-- `p` is adequate for the declared family on `D`: points merged by
`p` agree on every declared question.  Adequacy is target-relative by
construction. -/
def Adequate (D : List Nat) (Q : List (Nat → Nat))
    (p : Nat → Nat) : Prop :=
  ∀ x, x ∈ D → ∀ x', x' ∈ D → p x = p x' → SigEq Q x x'

/-- The fibers of `p` over `D` are `q`-constant. -/
def FiberConstant (D : List Nat) (p q : Nat → Nat) : Prop :=
  ∀ x, x ∈ D → ∀ x', x' ∈ D → p x = p x' → q x = q x'

/-- `q` factors through `p` on `D`. -/
def FactorsOn (D : List Nat) (p q : Nat → Nat) : Prop :=
  ∃ g : Nat → Nat, ∀ x, x ∈ D → g (p x) = q x

/-! ## First-match selection (replaces any library search) -/

/-- First element of `D` satisfying the boolean test, if any. -/
def pick (D : List Nat) (P : Nat → Bool) : Option Nat :=
  match D with
  | [] => none
  | a :: t => if P a then some a else pick t P

theorem pick_cons (a : Nat) (t : List Nat) (P : Nat → Bool) :
    pick (a :: t) P = if P a then some a else pick t P := rfl

theorem pick_mem (D : List Nat) (P : Nat → Bool) :
    ∀ r, pick D P = some r → r ∈ D := by
  induction D with
  | nil =>
    intro r h
    have h' : (none : Option Nat) = some r := h
    cases h'
  | cons a t ih =>
    intro r h
    rw [pick_cons] at h
    split at h
    · injection h with h1
      subst h1
      exact List.mem_cons_self
    · exact List.mem_cons_of_mem _ (ih r h)

theorem pick_holds (D : List Nat) (P : Nat → Bool) :
    ∀ r, pick D P = some r → P r = true := by
  induction D with
  | nil =>
    intro r h
    have h' : (none : Option Nat) = some r := h
    cases h'
  | cons a t ih =>
    intro r h
    rw [pick_cons] at h
    split at h
    · rename_i hp
      injection h with h1
      subst h1
      exact hp
    · exact ih r h

theorem pick_some_of_mem (D : List Nat) (P : Nat → Bool) :
    ∀ x, x ∈ D → P x = true → ∃ r, pick D P = some r := by
  induction D with
  | nil => intro x hx; cases hx
  | cons a t ih =>
    intro x hx hP
    rw [pick_cons]
    split
    · exact ⟨a, rfl⟩
    · rename_i hpa
      cases hx with
      | head => exact absurd hP hpa
      | tail _ hm => exact ih x hm hP

/-! ## A — factorization -/

/-- A question factors through a presentation on `D` exactly when the
presentation's fibers over `D` are question-constant.  The factoring
map is built by first-match selection over the represented `D`; no
choice principle. -/
theorem factors_iff_fiberConstant (D : List Nat) (p q : Nat → Nat) :
    FactorsOn D p q ↔ FiberConstant D p q := by
  constructor
  · intro hf x hx x' hx' hp
    obtain ⟨g, hg⟩ := hf
    rw [← hg x hx, ← hg x' hx', hp]
  · intro hfc
    refine ⟨fun y => q ((pick D (fun z => decide (p z = y))).getD 0),
      ?_⟩
    intro x hx
    obtain ⟨r, hr⟩ :=
      pick_some_of_mem D (fun z => decide (p z = p x)) x hx
        (decide_eq_true rfl)
    have hrD := pick_mem D (fun z => decide (p z = p x)) r hr
    have hpr : p r = p x :=
      of_decide_eq_true (pick_holds D _ r hr)
    show q ((pick D (fun z => decide (p z = p x))).getD 0) = q x
    rw [hr]
    exact hfc r hrD x hx hpr

/-- On the image of `D`, any two factoring maps agree. -/
theorem factor_unique_on_image (D : List Nat) (p q g g' : Nat → Nat)
    (h : ∀ x, x ∈ D → g (p x) = q x)
    (h' : ∀ x, x ∈ D → g' (p x) = q x) :
    ∀ x, x ∈ D → g (p x) = g' (p x) :=
  fun x hx => (h x hx).trans (h' x hx).symm

/-- Off the image of `D`, factoring maps are not unique: a concrete
witness. -/
theorem factor_not_unique_off_image :
    ∃ (D : List Nat) (p q g g' : Nat → Nat),
      (∀ x, x ∈ D → g (p x) = q x) ∧
      (∀ x, x ∈ D → g' (p x) = q x) ∧ g ≠ g' := by
  refine ⟨[0], id, id, id, fun n => if n = 5 then 6 else n,
    fun x _ => rfl, ?_, ?_⟩
  · intro x hx
    cases hx with
    | head => decide
    | tail _ hm => cases hm
  · intro h
    exact absurd (congrFun h 5) (by decide)

/-! ## B — the signature quotient -/

/-- The signature quotient presentation: each point goes to the first
element of `D` carrying the same signature (the class representative;
`0` off `D`).

Universal property (exact scope): `pQ` is `Q`-adequate, and factors
through every `Q`-adequate presentation, uniquely on that
presentation's image over `D`; nothing is claimed off-image or for
undeclared question families. -/
def pQ (D : List Nat) (Q : List (Nat → Nat)) : Nat → Nat :=
  fun x =>
    (pick D (fun z => decide (sigList Q z = sigList Q x))).getD 0

/-- On `D`, the representative is in `D` and carries the point's
signature. -/
theorem pQ_spec (D : List Nat) (Q : List (Nat → Nat)) (x : Nat)
    (hx : x ∈ D) :
    pQ D Q x ∈ D ∧ sigList Q (pQ D Q x) = sigList Q x := by
  obtain ⟨r, hr⟩ :=
    pick_some_of_mem D
      (fun z => decide (sigList Q z = sigList Q x)) x hx
      (decide_eq_true rfl)
  have hval : pQ D Q x = r := by
    show (pick D
      (fun z => decide (sigList Q z = sigList Q x))).getD 0 = r
    rw [hr]
    rfl
  constructor
  · rw [hval]
    exact pick_mem D _ r hr
  · rw [hval]
    exact of_decide_eq_true (pick_holds D _ r hr)

/-- The fibers of `pQ` over `D` are exactly the signature classes. -/
theorem pQ_exact (D : List Nat) (Q : List (Nat → Nat)) :
    ∀ x, x ∈ D → ∀ x', x' ∈ D →
      (pQ D Q x = pQ D Q x' ↔ SigEq Q x x') := by
  intro x hx x' hx'
  constructor
  · intro h
    apply (sigEq_iff_sigList Q x x').mpr
    have s1 := (pQ_spec D Q x hx).2
    have s2 := (pQ_spec D Q x' hx').2
    rw [← s1, ← s2, h]
  · intro h
    have hs := (sigEq_iff_sigList Q x x').mp h
    show (pick D
        (fun z => decide (sigList Q z = sigList Q x))).getD 0 =
      (pick D
        (fun z => decide (sigList Q z = sigList Q x'))).getD 0
    rw [hs]

/-- `pQ` is adequate for its family (corollary of exactness). -/
theorem pQ_adequate (D : List Nat) (Q : List (Nat → Nat)) :
    Adequate D Q (pQ D Q) :=
  fun x hx x' hx' hp => (pQ_exact D Q x hx x' hx').mp hp

/-- `pQ` factors through every `Q`-adequate presentation: adequacy
says the presentation's fibers sit inside the signature classes, and
`pQ` is class-constant.  This is the sense — and the only sense
claimed — in which `pQ` is the coarsest adequate presentation. -/
theorem pQ_coarsest (D : List Nat) (Q : List (Nat → Nat))
    (p : Nat → Nat) (hp : Adequate D Q p) :
    FactorsOn D p (pQ D Q) := by
  apply (factors_iff_fiberConstant D p (pQ D Q)).mpr
  intro x hx x' hx' hpx
  exact (pQ_exact D Q x hx x' hx').mpr (hp x hx x' hx' hpx)

/-- The factoring of `pQ` through an adequate presentation is unique
on that presentation's image over `D` (instance of
`factor_unique_on_image`); off-image values are unconstrained
(`factor_not_unique_off_image`). -/
theorem pQ_unique_on_image (D : List Nat) (Q : List (Nat → Nat))
    (p : Nat → Nat) (_hp : Adequate D Q p) (g g' : Nat → Nat)
    (hg : ∀ x, x ∈ D → g (p x) = pQ D Q x)
    (hg' : ∀ x, x ∈ D → g' (p x) = pQ D Q x) :
    ∀ x, x ∈ D → g (p x) = g' (p x) :=
  factor_unique_on_image D p (pQ D Q) g g' hg hg'

/-! ## C — descent failure, witnessed -/

/-- Disagreement with a cons family decomposes: the head question
fails or the tail family disagrees.  Decided by `decide` on the head
answers; no choice principle. -/
theorem sigEq_decompose (q : Nat → Nat) (T : List (Nat → Nat))
    (x x' : Nat) (h : ¬ SigEq (q :: T) x x') :
    q x ≠ q x' ∨ ¬ SigEq T x x' := by
  cases hd : decide (q x = q x') with
  | false => exact Or.inl (of_decide_eq_false hd)
  | true =>
    refine Or.inr (fun ht => h ?_)
    intro q' hq'
    cases hq' with
    | head => exact of_decide_eq_true hd
    | tail _ hm => exact ht q' hm

/-- From disagreement, a witnessing question is constructed by list
recursion. -/
theorem exists_separator_of_not_sigEq (Q : List (Nat → Nat))
    (x x' : Nat) (h : ¬ SigEq Q x x') :
    ∃ q, q ∈ Q ∧ q x ≠ q x' := by
  induction Q with
  | nil => exact absurd (fun q hq => by cases hq) h
  | cons q T ih =>
    cases sigEq_decompose q T x x' h with
    | inl hq => exact ⟨q, List.mem_cons_self, hq⟩
    | inr ht =>
      obtain ⟨q', hm, hne⟩ := ih ht
      exact ⟨q', List.mem_cons_of_mem _ hm, hne⟩

/-- If a presentation merges two points of `D` that the declared
family separates, some declared question witnesses the failure: it
answers differently on the merged pair, so the presentation's fibers
are not constant for it. -/
theorem descent_witness (D : List Nat) (Q : List (Nat → Nat))
    (p : Nat → Nat) (x x' : Nat) (hx : x ∈ D) (hx' : x' ∈ D)
    (hp : p x = p x') (hne : ¬ SigEq Q x x') :
    ∃ q, q ∈ Q ∧ q x ≠ q x' ∧ ¬ FiberConstant D p q := by
  obtain ⟨q, hm, hqne⟩ := exists_separator_of_not_sigEq Q x x' hne
  exact ⟨q, hm, hqne, fun hfc => hqne (hfc x hx x' hx' hp)⟩

/-! ## D — enlargement refines; exact split characterization -/

/-- Enlarging the declared family only refines agreement. -/
theorem enlarge_refines (Q Q' : List (Nat → Nat))
    (hsub : ∀ q, q ∈ Q → q ∈ Q') (x x' : Nat) :
    SigEq Q' x x' → SigEq Q x x' :=
  fun h q hq => h q (hsub q hq)

/-- The class of `x` splits under the enlargement: some point of `D`
agrees with `x` on the old family but not on the new one. -/
def SplitsAt (D : List Nat) (Q Q' : List (Nat → Nat))
    (x : Nat) : Prop :=
  ∃ x', x' ∈ D ∧ SigEq Q x x' ∧ ¬ SigEq Q' x x'

/-- A class splits exactly when the enlarged family carries a
separator across an old agreement.  The witnessing question is
automatically outside the old agreement, since the pair agrees on all
of `Q`. -/
theorem splits_iff_new_separator (D : List Nat)
    (Q Q' : List (Nat → Nat)) (x : Nat)
    (_hsub : ∀ q, q ∈ Q → q ∈ Q') :
    SplitsAt D Q Q' x ↔
      ∃ x', x' ∈ D ∧ SigEq Q x x' ∧
        ∃ q', q' ∈ Q' ∧ q' x ≠ q' x' := by
  constructor
  · intro h
    obtain ⟨x', hx', hsig, hnot⟩ := h
    obtain ⟨q', hm, hne⟩ := exists_separator_of_not_sigEq Q' x x' hnot
    exact ⟨x', hx', hsig, q', hm, hne⟩
  · intro h
    obtain ⟨x', hx', hsig, q', hm, hne⟩ := h
    exact ⟨x', hx', hsig, fun hs => hne (hs q' hm)⟩

/-! ## E — no absolute adequacy without a declared family -/

/-- Absolute adequacy — adequacy for *every* family — is exactly
injectivity on `D`, i.e. exactly no-compression.  Every genuine
compression is adequate only relative to a declared, represented
question family: the family, its source, and its revisions are
represented data, never a view from nowhere. -/
theorem absolute_adequacy_iff_injective (D : List Nat)
    (p : Nat → Nat) :
    (∀ Q : List (Nat → Nat), Adequate D Q p) ↔
      (∀ x, x ∈ D → ∀ x', x' ∈ D → p x = p x' → x = x') := by
  constructor
  · intro h x hx x' hx' hp
    have hsig := h [fun z => if z = x then 1 else 0] x hx x' hx' hp
    have h1 : (if x = x then (1 : Nat) else 0) =
        (if x' = x then (1 : Nat) else 0) :=
      hsig (fun z => if z = x then (1 : Nat) else 0)
        List.mem_cons_self
    rw [if_pos rfl] at h1
    cases hd : decide (x' = x) with
    | true => exact (of_decide_eq_true hd).symm
    | false =>
      rw [if_neg (of_decide_eq_false hd)] at h1
      exact absurd h1 (by decide)
  · intro h Q x hx x' hx' hp q _
    rw [h x hx x' hx' hp]

/-! ## F — repetition, digests, and replay add no questions -/

/-- Repeating the family separates nothing new. -/
theorem dup_no_refine (Q : List (Nat → Nat)) (x x' : Nat) :
    SigEq (Q ++ Q) x x' ↔ SigEq Q x x' := by
  constructor
  · intro h q hq
    exact h q (List.mem_append.mpr (Or.inl hq))
  · intro h q hq
    cases List.mem_append.mp hq with
    | inl h1 => exact h q h1
    | inr h2 => exact h q h2

/-- Appending a digest of the existing answers — any function of the
signature, e.g. a hash or a replay record — separates nothing new. -/
theorem postcompose_no_refine (Q : List (Nat → Nat))
    (f : List Nat → Nat) (x x' : Nat) :
    SigEq (Q ++ [fun z => f (sigList Q z)]) x x' ↔
      SigEq Q x x' := by
  constructor
  · intro h q hq
    exact h q (List.mem_append.mpr (Or.inl hq))
  · intro h q hq
    cases List.mem_append.mp hq with
    | inl h1 => exact h q h1
    | inr h2 =>
      cases h2 with
      | head =>
        show f (sigList Q x) = f (sigList Q x')
        rw [(sigEq_iff_sigList Q x x').mp h]
      | tail _ h3 => cases h3

/-- A genuine split requires a question that is not
signature-determined: the split witness separates points with equal
old signatures, so no function of the old signature can express it.
This is the exact sense in which replay is evidential only when it
carries a new represented separator. -/
theorem refine_requires_separator (D : List Nat)
    (Q Q' : List (Nat → Nat)) (x : Nat) (h : SplitsAt D Q Q' x) :
    ∃ q', q' ∈ Q' ∧
      ¬ (∃ f : List Nat → Nat, ∀ z, q' z = f (sigList Q z)) := by
  obtain ⟨x', hx', hsig, hnot⟩ := h
  obtain ⟨q', hm, hne⟩ := exists_separator_of_not_sigEq Q' x x' hnot
  refine ⟨q', hm, ?_⟩
  intro hdet
  obtain ⟨f, hf⟩ := hdet
  apply hne
  rw [hf x, hf x', (sigEq_iff_sigList Q x x').mp hsig]

/-! ## Countermodels to refinement uniqueness -/

/-- Indicator question of the point `a`. -/
def ind (a : Nat) : Nat → Nat :=
  fun z => if z = a then 1 else 0

/-- Refinement is not unique: from the trivial family on
`D = [0,1,2]`, two distinct one-question enlargements (indicators of
`0` and of `1`) both split the single class, with different resulting
class structures (`1` and `2` agree under the first, not under the
second). -/
theorem refinement_not_unique :
    ∃ (D : List Nat) (Q Q1 Q2 : List (Nat → Nat)) (x : Nat),
      x ∈ D ∧ (∀ q, q ∈ Q → q ∈ Q1) ∧ (∀ q, q ∈ Q → q ∈ Q2) ∧
      SplitsAt D Q Q1 x ∧ SplitsAt D Q Q2 x ∧
      ∃ y, y ∈ D ∧ ∃ y', y' ∈ D ∧
        SigEq Q1 y y' ∧ ¬ SigEq Q2 y y' := by
  refine ⟨[0, 1, 2], [], [ind 0], [ind 1], 0,
    List.mem_cons_self, ?_, ?_, ?_, ?_, ?_⟩
  · intro q hq; cases hq
  · intro q hq; cases hq
  · refine ⟨1, List.mem_cons_of_mem _ List.mem_cons_self, ?_, ?_⟩
    · intro q hq; cases hq
    · intro hs
      exact absurd (hs (ind 0) List.mem_cons_self) (by decide)
  · refine ⟨1, List.mem_cons_of_mem _ List.mem_cons_self, ?_, ?_⟩
    · intro q hq; cases hq
    · intro hs
      exact absurd (hs (ind 1) List.mem_cons_self) (by decide)
  · refine ⟨1, List.mem_cons_of_mem _ List.mem_cons_self,
      2, List.mem_cons_of_mem _
        (List.mem_cons_of_mem _ List.mem_cons_self), ?_, ?_⟩
    · intro q hq
      cases hq with
      | head => decide
      | tail _ hm => cases hm
    · intro hs
      exact absurd (hs (ind 1) List.mem_cons_self) (by decide)

/-- Equal-cost refinements tie: the two splitting enlargements above
have families of equal length, both split the same class, and induce
different agreement relations on `D`.  The tie is recorded; neither
refinement is unique-minimum. -/
theorem refinement_tie :
    ∃ (D : List Nat) (Q Q1 Q2 : List (Nat → Nat)) (x : Nat),
      Q1.length = Q2.length ∧ x ∈ D ∧
      SplitsAt D Q Q1 x ∧ SplitsAt D Q Q2 x ∧
      ¬ (∀ y, y ∈ D → ∀ y', y' ∈ D →
          (SigEq Q1 y y' ↔ SigEq Q2 y y')) := by
  refine ⟨[0, 1, 2], [], [ind 0], [ind 1], 0, rfl,
    List.mem_cons_self, ?_, ?_, ?_⟩
  · refine ⟨1, List.mem_cons_of_mem _ List.mem_cons_self, ?_, ?_⟩
    · intro q hq; cases hq
    · intro hs
      exact absurd (hs (ind 0) List.mem_cons_self) (by decide)
  · refine ⟨1, List.mem_cons_of_mem _ List.mem_cons_self, ?_, ?_⟩
    · intro q hq; cases hq
    · intro hs
      exact absurd (hs (ind 1) List.mem_cons_self) (by decide)
  · intro hall
    have h12 : SigEq [ind 0] 1 2 := by
      intro q hq
      cases hq with
      | head => decide
      | tail _ hm => cases hm
    have h21 :=
      (hall 1 (List.mem_cons_of_mem _ List.mem_cons_self)
        2 (List.mem_cons_of_mem _
          (List.mem_cons_of_mem _ List.mem_cons_self))).mp h12
    exact absurd (h21 (ind 1) List.mem_cons_self) (by decide)

/-! ## The class-count measure and the refinement bound -/

/-- Boolean membership test for signature lists (self-contained; no
library search). -/
def memB (s : List Nat) : List (List Nat) → Bool
  | [] => false
  | a :: t => if s = a then true else memB s t

theorem memB_cons (s a : List Nat) (t : List (List Nat)) :
    memB s (a :: t) = if s = a then true else memB s t := rfl

theorem memB_iff (s : List Nat) (l : List (List Nat)) :
    memB s l = true ↔ s ∈ l := by
  induction l with
  | nil =>
    constructor
    · intro h; exact Bool.noConfusion h
    · intro h; cases h
  | cons a t ih =>
    rw [memB_cons]
    split
    · rename_i hsa
      subst hsa
      exact ⟨fun _ => List.mem_cons_self, fun _ => rfl⟩
    · rename_i hsa
      constructor
      · intro h
        exact List.mem_cons_of_mem _ (ih.mp h)
      · intro h
        cases h with
        | head => exact absurd rfl hsa
        | tail _ hm => exact ih.mpr hm

/-- Deduplication keeping last occurrences (self-contained). -/
def dedupL : List (List Nat) → List (List Nat)
  | [] => []
  | s :: t => bif memB s t then dedupL t else s :: dedupL t

theorem dedupL_cons (s : List Nat) (t : List (List Nat)) :
    dedupL (s :: t) =
      bif memB s t then dedupL t else s :: dedupL t := rfl

theorem length_dedupL_le (l : List (List Nat)) :
    (dedupL l).length ≤ l.length := by
  induction l with
  | nil => exact Nat.le_refl 0
  | cons s t ih =>
    rw [dedupL_cons]
    cases hm : memB s t with
    | true => exact Nat.le_succ_of_le ih
    | false => exact Nat.succ_le_succ ih

theorem dedupL_ne_nil (l : List (List Nat)) :
    l ≠ [] → dedupL l ≠ [] := by
  induction l with
  | nil => intro h; exact absurd rfl h
  | cons s t ih =>
    intro _
    rw [dedupL_cons]
    cases hm : memB s t with
    | true =>
      refine ih ?_
      intro he
      subst he
      exact Bool.noConfusion hm
    | false => exact List.cons_ne_nil _ _

/-- The number of distinct signatures over `D`: the class count of
`pQ D Q` on `D`. -/
def classCount (D : List Nat) (Q : List (Nat → Nat)) : Nat :=
  (dedupL (D.map (sigList Q))).length

/-- If the coarse value is determined by the fine value on `d :: t`,
then a repeated fine head-value forces a repeated coarse
head-value. -/
theorem memG_of_memF {F G : Nat → List Nat} {d : Nat} {t : List Nat}
    (h : ∀ a, a ∈ d :: t → ∀ b, b ∈ d :: t → F a = F b → G a = G b)
    (hm : memB (F d) (t.map F) = true) :
    memB (G d) (t.map G) = true := by
  obtain ⟨e, he, hFe⟩ := List.mem_map.mp ((memB_iff _ _).mp hm)
  have hGe : G e = G d :=
    h e (List.mem_cons_of_mem _ he) d List.mem_cons_self hFe
  exact (memB_iff _ _).mpr (List.mem_map.mpr ⟨e, he, hGe⟩)

/-- Distinct-value counting is monotone under determination: if the
`G`-value of every point of `D` is determined by its `F`-value, then
`G` takes no more distinct values on `D` than `F`. -/
theorem count_le_of_determines (F G : Nat → List Nat) :
    ∀ D : List Nat,
      (∀ a, a ∈ D → ∀ b, b ∈ D → F a = F b → G a = G b) →
      (dedupL (D.map G)).length ≤ (dedupL (D.map F)).length := by
  intro D
  induction D with
  | nil => intro _; exact Nat.le_refl 0
  | cons d t ih =>
    intro h
    have ht : ∀ a, a ∈ t → ∀ b, b ∈ t → F a = F b → G a = G b :=
      fun a ha b hb =>
        h a (List.mem_cons_of_mem _ ha) b (List.mem_cons_of_mem _ hb)
    have iht := ih ht
    show (dedupL (G d :: t.map G)).length ≤
      (dedupL (F d :: t.map F)).length
    rw [dedupL_cons, dedupL_cons]
    cases hcF : memB (F d) (t.map F) with
    | true =>
      rw [memG_of_memF h hcF]
      exact iht
    | false =>
      cases hcG : memB (G d) (t.map G) with
      | true => exact Nat.le_succ_of_le iht
      | false => exact Nat.succ_le_succ iht

/-- Distinct-value counting is *strictly* monotone under
determination with a merged pair: if additionally some pair of `D`
shares its `G`-value but not its `F`-value, then `F` takes strictly
more distinct values on `D` than `G`. -/
theorem count_lt_of_split (F G : Nat → List Nat) :
    ∀ D : List Nat,
      (∀ a, a ∈ D → ∀ b, b ∈ D → F a = F b → G a = G b) →
      ∀ x y, x ∈ D → y ∈ D → G x = G y → F x ≠ F y →
        (dedupL (D.map G)).length < (dedupL (D.map F)).length := by
  intro D
  induction D with
  | nil => intro _ x y hx; cases hx
  | cons d t ih =>
    intro h x y hx hy hGxy hFxy
    have ht : ∀ a, a ∈ t → ∀ b, b ∈ t → F a = F b → G a = G b :=
      fun a ha b hb =>
        h a (List.mem_cons_of_mem _ ha) b (List.mem_cons_of_mem _ hb)
    show (dedupL (G d :: t.map G)).length <
      (dedupL (F d :: t.map F)).length
    rw [dedupL_cons, dedupL_cons]
    cases hcF : memB (F d) (t.map F) with
    | true =>
      rw [memG_of_memF h hcF]
      obtain ⟨e, he, hFe⟩ :=
        List.mem_map.mp ((memB_iff _ _).mp hcF)
      have hGe : G e = G d :=
        h e (List.mem_cons_of_mem _ he) d List.mem_cons_self hFe
      cases hx with
      | head =>
        cases hy with
        | head => exact absurd rfl hFxy
        | tail _ hy' =>
          exact ih ht e y he hy' (hGe.trans hGxy)
            (fun hc => hFxy (hFe.symm.trans hc))
      | tail _ hx' =>
        cases hy with
        | head =>
          exact ih ht x e hx' he (hGxy.trans hGe.symm)
            (fun hc => hFxy (hc.trans hFe))
        | tail _ hy' => exact ih ht x y hx' hy' hGxy hFxy
    | false =>
      cases hcG : memB (G d) (t.map G) with
      | true => exact Nat.lt_succ_of_le (count_le_of_determines F G t ht)
      | false =>
        cases hx with
        | head =>
          cases hy with
          | head => exact absurd rfl hFxy
          | tail _ hy' =>
            have hmem : memB (G d) (t.map G) = true :=
              (memB_iff _ _).mpr
                (List.mem_map.mpr ⟨y, hy', hGxy.symm⟩)
            rw [hmem] at hcG
            exact Bool.noConfusion hcG
        | tail _ hx' =>
          cases hy with
          | head =>
            have hmem : memB (G d) (t.map G) = true :=
              (memB_iff _ _).mpr
                (List.mem_map.mpr ⟨x, hx', hGxy⟩)
            rw [hmem] at hcG
            exact Bool.noConfusion hcG
          | tail _ hy' =>
            exact Nat.succ_lt_succ (ih ht x y hx' hy' hGxy hFxy)

/-- The class count never exceeds the domain length. -/
theorem refine_bounded (D : List Nat) (Q : List (Nat → Nat)) :
    classCount D Q ≤ D.length := by
  have h1 := length_dedupL_le (D.map (sigList Q))
  have h2 : (D.map (sigList Q)).length = D.length := by simp
  show (dedupL (D.map (sigList Q))).length ≤ D.length
  omega

/-- On a nonempty domain the class count is at least one. -/
theorem classCount_pos (D : List Nat) (Q : List (Nat → Nat))
    (hD : D ≠ []) : 1 ≤ classCount D Q := by
  have hmap : D.map (sigList Q) ≠ [] := by
    cases D with
    | nil => exact absurd rfl hD
    | cons d t => exact List.cons_ne_nil _ _
  have hne := dedupL_ne_nil _ hmap
  show 1 ≤ (dedupL (D.map (sigList Q))).length
  cases hd : dedupL (D.map (sigList Q)) with
  | nil => exact absurd hd hne
  | cons a u => exact Nat.succ_le_succ (Nat.zero_le _)

/-- A split under an enlargement strictly increases the class
count. -/
theorem strict_split_increases (D : List Nat)
    (Q Q' : List (Nat → Nat)) (hsub : ∀ q, q ∈ Q → q ∈ Q')
    (x : Nat) (hx : x ∈ D) (hs : SplitsAt D Q Q' x) :
    classCount D Q < classCount D Q' := by
  obtain ⟨x', hx', hsig, hnot⟩ := hs
  have hdet : ∀ a, a ∈ D → ∀ b, b ∈ D →
      sigList Q' a = sigList Q' b → sigList Q a = sigList Q b :=
    fun a _ b _ hab =>
      (sigEq_iff_sigList Q a b).mp
        (enlarge_refines Q Q' hsub a b
          ((sigEq_iff_sigList Q' a b).mpr hab))
  exact count_lt_of_split (sigList Q') (sigList Q) D hdet x x' hx hx'
    ((sigEq_iff_sigList Q x x').mp hsig)
    (fun he => hnot ((sigEq_iff_sigList Q' x x').mpr he))

/-- One strictly-refining step: an enlargement that splits some class
of the represented domain. -/
def StrictRefine (D : List Nat) (Q Q' : List (Nat → Nat)) : Prop :=
  (∀ q, q ∈ Q → q ∈ Q') ∧ ∃ x, x ∈ D ∧ SplitsAt D Q Q' x

/-- A chain of families in which each consecutive pair is a
strictly-refining step. -/
def StrictChain (D : List Nat) : List (List (Nat → Nat)) → Prop
  | [] => True
  | [_] => True
  | Q :: Q' :: t => StrictRefine D Q Q' ∧ StrictChain D (Q' :: t)

/-- Along a strict chain the class count strictly increases, so the
head count plus the number of steps is bounded by the domain
length. -/
theorem chain_count (D : List Nat) :
    ∀ (t : List (List (Nat → Nat))) (Q : List (Nat → Nat)),
      StrictChain D (Q :: t) →
      classCount D Q + t.length ≤ D.length := by
  intro t
  induction t with
  | nil => intro Q _; exact refine_bounded D Q
  | cons Q' t' ih =>
    intro Q hc
    obtain ⟨hr, hrest⟩ := hc
    obtain ⟨hsub, x, hx, hs⟩ := hr
    have h1 := strict_split_increases D Q Q' hsub x hx hs
    have h2 := ih Q' hrest
    simp only [List.length_cons]
    omega

/-- Any chain of strictly-refining families over a nonempty domain
has length at most the domain length: the class count is a strictly
monotone `Nat` measure between `1` and `D.length`.  Scope: this bounds
chains over the represented `D` under the declared step relation;
nothing is claimed for other step relations. -/
theorem chain_bounded (D : List Nat) (hD : D ≠ [])
    (L : List (List (Nat → Nat))) (hc : StrictChain D L) :
    L.length ≤ D.length := by
  cases L with
  | nil => exact Nat.zero_le _
  | cons Q t =>
    have h1 := chain_count D t Q hc
    have h2 := classCount_pos D Q hD
    simp only [List.length_cons]
    omega

/-- At most `D.length - 1` strict splits are possible from any
starting family (in particular from the trivial one): the number of
steps of a strict chain is strictly below the domain length. -/
theorem strict_steps_lt (D : List Nat) (hD : D ≠ [])
    (Q : List (Nat → Nat)) (t : List (List (Nat → Nat)))
    (hc : StrictChain D (Q :: t)) : t.length < D.length := by
  have h1 := chain_count D t Q hc
  have h2 := classCount_pos D Q hD
  omega

end Compression
