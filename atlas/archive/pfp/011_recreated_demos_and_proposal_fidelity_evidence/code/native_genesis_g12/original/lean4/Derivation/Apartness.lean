import Derivation.PrimitiveCore

/-!
# Positive apartness, indistinguishability, and the retained orientation

A pre-observational module: nothing here mentions observation
columns, collapse maps, or response families.  The vocabulary is the
native one — asserted difference, retention, admitted operations.

Contents, in dependency order:

1. **Positive apartness** (`IsApart`): one relation carrying the
   three laws irreflexivity, symmetry, cotransitivity — each a
   separately priced admission (the implication matrix of
   `PrimitiveCore` shows none follows from the others).
2. **Indistinguishability** (`Indist`), defined as the negation of
   apartness, and the theorem that under `IsApart` it is an
   equivalence (`indist_refl`, `indist_symm`, `indist_trans`,
   bundled in `indist_equivalence`).  Transitivity is exactly where
   cotransitivity is spent.
3. **Insufficiency countermodels**, finite and minimal: bare
   assertion breaks reflexivity of indistinguishability on the
   one-point carrier; irreflexivity alone breaks symmetry on the
   two-point carrier (minimal: on a subsingleton, irreflexive
   indistinguishability is already total); irreflexivity plus
   symmetry without cotransitivity breaks transitivity on the
   three-point carrier (minimal by
   `PrimitiveCore.cotrans_auto_on_two`).
4. **The orientation separation**: the oriented two-point relation
   and its reverse generate the *same* symmetric apartness
   (`orientations_same_apartness`) — and hence the same
   indistinguishability — while remaining distinct as data
   (`orientations_differ`).  The retained orientation is strictly
   finer than the apartness used to form indistinguishability, and
   the swap that fixes the apartness moves the retained ordered
   witness (`retained_orientation_not_swap_invariant`).
5. **The exact operation characterization**: on the two-point
   carrier, the admitted operations preserving the retained oriented
   witness are exactly the identity
   (`oriented_preserver_unique`); those preserving the symmetric
   apartness of the witness are exactly the identity and the swap
   (`apart_preserver_pair`); the two constant operations preserve
   neither (`collapse_preserves_neither`).  Relative to any admitted
   family, the closure preserves the oriented witness exactly when
   every generator does (`clos_oriented_iff`), and any such family
   is extensionally trivial (`oriented_family_trivial`).
-/

namespace Apartness

open PrimDiff PrimitiveCore

/-- Positive apartness: irreflexive, symmetric, cotransitive.  Three
separately admitted laws on one asserted-difference relation. -/
structure IsApart {X : Type} (r : X → X → Prop) : Prop where
  irrefl : ∀ x, ¬ r x x
  symm : ∀ x y, r x y → r y x
  cotrans : ∀ x y, r x y → ∀ z, r x z ∨ r z y

/-- Indistinguishability: the negation of apartness.  A negative
notion by construction — its laws must be earned from the positive
ones. -/
def Indist {X : Type} (r : X → X → Prop) (x y : X) : Prop := ¬ r x y

/-- Reflexivity of indistinguishability is exactly irreflexivity of
the apartness. -/
theorem indist_refl {X : Type} {r : X → X → Prop} (h : IsApart r) :
    ∀ x, Indist r x x := h.irrefl

/-- Symmetry of indistinguishability from symmetry of apartness. -/
theorem indist_symm {X : Type} {r : X → X → Prop} (h : IsApart r)
    {x y : X} (hxy : Indist r x y) : Indist r y x :=
  fun hyx => hxy (h.symm y x hyx)

/-- Transitivity of indistinguishability: the cotransitivity law,
spent exactly here.  A difference between the endpoints would split
against the midpoint. -/
theorem indist_trans {X : Type} {r : X → X → Prop} (h : IsApart r)
    {x y z : X} (hxy : Indist r x y) (hyz : Indist r y z) :
    Indist r x z :=
  fun hxz =>
    match h.cotrans x z hxz y with
    | Or.inl hxy' => hxy hxy'
    | Or.inr hyz' => hyz hyz'

/-- **Indistinguishability under positive apartness is an
equivalence.** -/
theorem indist_equivalence {X : Type} {r : X → X → Prop}
    (h : IsApart r) :
    (∀ x, Indist r x x) ∧
    (∀ x y, Indist r x y → Indist r y x) ∧
    (∀ x y z, Indist r x y → Indist r y z → Indist r x z) :=
  ⟨indist_refl h,
   fun _ _ => indist_symm h,
   fun _ _ _ => indist_trans h⟩

/-! ## Insufficiency, by finite countermodels -/

/-- Bare assertion is insufficient: the one-point self-difference
already breaks reflexivity of indistinguishability. -/
theorem bare_breaks_refl :
    ¬ Indist (fun _ _ : Unit => True) () () := fun h => h trivial

/-- Irreflexivity alone is insufficient: on the oriented two-point
relation, indistinguishability fails symmetry.  (Irreflexivity holds:
`PrimDiff.D2_irrefl`.) -/
theorem irrefl_alone_breaks_symm :
    Indist D2 true false ∧ ¬ Indist D2 false true := by
  constructor
  · intro h
    exact absurd h.1 (by decide)
  · intro h
    exact h (by decide)

/-- Minimality of the two-point countermodel: on a subsingleton
carrier every irreflexive relation is empty, so its
indistinguishability is total — no one-point countermodel exists. -/
theorem subsingleton_indist_total {X : Type} [Subsingleton X]
    {r : X → X → Prop} (hi : PrimDiff.Irrefl r) (x y : X) :
    Indist r x y := by
  intro hxy
  exact PrimDiff.irrefl_witness_ne hi hxy (Subsingleton.elim x y)

/-- The three-point relation with one symmetrized edge: irreflexive
and symmetric, not cotransitive. -/
def triSymRel : Fin 3 → Fin 3 → Prop :=
  fun x y => (x = 0 ∧ y = 1) ∨ (x = 1 ∧ y = 0)

instance (x y : Fin 3) : Decidable (triSymRel x y) := by
  unfold triSymRel; infer_instance

theorem triSymRel_irrefl : PrimDiff.Irrefl triSymRel := by
  unfold PrimDiff.Irrefl triSymRel
  decide

theorem triSymRel_symm : ∀ x y, triSymRel x y → triSymRel y x := by
  unfold triSymRel
  decide

/-- Irreflexivity and symmetry without cotransitivity are
insufficient: transitivity of indistinguishability fails at the
third point. -/
theorem symm_without_cotrans_breaks_trans :
    Indist triSymRel 0 2 ∧ Indist triSymRel 2 1 ∧
      ¬ Indist triSymRel 0 1 := by
  refine ⟨?_, ?_, ?_⟩
  · intro h
    exact absurd h (by decide)
  · intro h
    exact absurd h (by decide)
  · intro h
    exact h (by decide)

/-- Minimality of the three-point countermodel: on the two-point
carrier, irreflexivity already yields cotransitivity
(`PrimitiveCore.cotrans_auto_on_two`), hence transitivity of
indistinguishability — stated directly. -/
theorem two_point_indist_trans (r : Bool → Bool → Prop)
    (hi : PrimDiff.Irrefl r) {x y z : Bool}
    (hxy : Indist r x y) (hyz : Indist r y z) : Indist r x z :=
  fun hxz =>
    match cotrans_auto_on_two r hi x z hxz y with
    | Or.inl hxy' => hxy hxy'
    | Or.inr hyz' => hyz hyz'

/-! ## The two-point apartness and the retained orientation -/

/-- The symmetric two-point relation is a positive apartness: the
three laws hold, cotransitivity by the two-point automatism. -/
theorem s2_isApart : IsApart S2 :=
  { irrefl := S2_irrefl,
    symm := fun x y h => match h with
      | Or.inl h' => Or.inr h'
      | Or.inr h' => Or.inl h',
    cotrans := cotrans_auto_on_two S2 S2_irrefl }

/-- Its indistinguishability is an equivalence — the equivalence the
two-point apartness earns. -/
theorem s2_indist_equivalence :
    (∀ x, Indist S2 x x) ∧
    (∀ x y, Indist S2 x y → Indist S2 y x) ∧
    (∀ x y z, Indist S2 x y → Indist S2 y z → Indist S2 x z) :=
  indist_equivalence s2_isApart

/-- **Both orientations generate the same apartness**: the
symmetrizations of the oriented relation and of its reverse agree on
every pair. -/
theorem orientations_same_apartness :
    ∀ x y, PrimDiff.Sym D2 x y ↔ PrimDiff.Sym D2rev x y := by
  unfold PrimDiff.Sym
  decide

/-- And hence the same indistinguishability. -/
theorem orientations_same_indist :
    ∀ x y, Indist (PrimDiff.Sym D2) x y ↔
      Indist (PrimDiff.Sym D2rev) x y := by
  intro x y
  constructor
  · intro h hxy
    exact h ((orientations_same_apartness x y).mpr hxy)
  · intro h hxy
    exact h ((orientations_same_apartness x y).mp hxy)

/-- While the orientations remain distinct as data: the retained
oriented witness is strictly finer than the apartness used to form
indistinguishability. -/
theorem orientations_differ :
    ¬ (∀ x y, D2 x y ↔ D2rev x y) := by
  intro h
  exact absurd ((h false true).mp (by decide)) (by decide)

/-- The swap fixes the apartness (`PrimDiff.swap_is_S2_automorphism`)
but moves the retained ordered witness: retention of orientation is
data the apartness layer cannot see. -/
theorem retained_orientation_not_swap_invariant :
    D2 false true ∧ ¬ D2 (Bool.not false) (Bool.not true) := by
  constructor
  · decide
  · decide

/-! ## Which admitted operations preserve the retained oriented
witness — the exact characterization -/

/-- An operation preserves the retained oriented witness when it
carries the ordered pair to an asserted ordered pair. -/
def PreservesOriented (f : Bool → Bool) : Prop :=
  D2 (f false) (f true)

/-- An operation preserves the symmetric apartness of the witness
when it carries the pair to an apart pair. -/
def PreservesApart (f : Bool → Bool) : Prop :=
  S2 (f false) (f true)

/-- Preserving the oriented witness is definitionally endpoint
fixing. -/
theorem oriented_pres_iff (f : Bool → Bool) :
    PreservesOriented f ↔ (f false = false ∧ f true = true) :=
  Iff.rfl

/-- **Exactly the identity** preserves the retained oriented witness
on the two-point carrier. -/
theorem oriented_preserver_unique (f : Bool → Bool)
    (h : PreservesOriented f) : f = id := by
  funext x
  cases x with
  | false => exact h.1
  | true => exact h.2

/-- The identity does preserve it (the characterization is
inhabited). -/
theorem id_preserves_oriented : PreservesOriented id := ⟨rfl, rfl⟩

/-- **Exactly the identity and the swap** preserve the symmetric
apartness of the witness. -/
theorem apart_preserver_pair (f : Bool → Bool)
    (h : PreservesApart f) : f = id ∨ f = Bool.not := by
  have hne : f false ≠ f true := by
    intro heq
    have h2 : S2 (f false) (f true) := h
    exact S2_irrefl (f true) (heq ▸ h2)
  cases hf : f false with
  | false =>
      left
      funext x
      cases x with
      | false => exact hf
      | true =>
          cases ht : f true with
          | true => rfl
          | false =>
              exfalso
              rw [hf, ht] at hne
              exact hne rfl
  | true =>
      right
      funext x
      cases x with
      | false => exact hf
      | true =>
          cases ht : f true with
          | false => rfl
          | true =>
              exfalso
              rw [hf, ht] at hne
              exact hne rfl

theorem id_preserves_apart : PreservesApart id := Or.inl ⟨rfl, rfl⟩

theorem swap_preserves_apart : PreservesApart Bool.not :=
  Or.inr ⟨rfl, rfl⟩

/-- The swap does NOT preserve the oriented witness: the apartness
preservers strictly contain the orientation preservers. -/
theorem swap_breaks_oriented : ¬ PreservesOriented Bool.not :=
  fun h => Bool.noConfusion h.1

/-- The two constant operations preserve neither: collapse erases
the difference in both readings. -/
theorem collapse_preserves_neither (v : Bool) :
    ¬ PreservesOriented (fun _ => v) ∧
      ¬ PreservesApart (fun _ => v) :=
  ⟨fun h => Bool.noConfusion (h.1.symm.trans h.2), S2_irrefl v⟩

/-- Preservation of the oriented witness composes. -/
theorem oriented_comp {f g : Bool → Bool}
    (hf : PreservesOriented f) (hg : PreservesOriented g) :
    PreservesOriented (f ∘ g) := by
  constructor
  · show f (g false) = false
    rw [hg.1, hf.1]
  · show f (g true) = true
    rw [hg.2, hf.2]

/-- **Relative to any admitted family**: the closure preserves the
retained oriented witness exactly when every generator does. -/
theorem clos_oriented_iff (F : (Bool → Bool) → Prop) :
    (∀ f, PrimDiff.Clos F f → PreservesOriented f) ↔
      (∀ f, F f → PreservesOriented f) := by
  constructor
  · intro h f hf
    exact h f (PrimDiff.Clos.base hf)
  · intro h f hf
    induction hf with
    | base hb => exact h _ hb
    | id => exact id_preserves_oriented
    | comp _ _ ihf ihg => exact oriented_comp ihf ihg

/-- Any admitted family whose members preserve the oriented witness
is extensionally trivial: every member is the identity.  The
orientation-preserving operations form no structure beyond the
identity — the retained orientation is rigid. -/
theorem oriented_family_trivial (F : (Bool → Bool) → Prop)
    (h : ∀ f, F f → PreservesOriented f) :
    ∀ f, F f → f = id :=
  fun f hf => oriented_preserver_unique f (h f hf)

end Apartness
