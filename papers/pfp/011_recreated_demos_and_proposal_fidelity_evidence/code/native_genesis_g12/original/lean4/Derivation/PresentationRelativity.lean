import Derivation.Compression
import Derivation.NoOutside
import Derivation.Generator

/-!
# Comparison-forced refinement and presentation-relative classification

This module composes three already proved parts of the development:

* `Compression` supplies finite signatures, fibers, factorization, and
  exact class counting.
* `NoOutside` supplies the operational support projection and the
  represented certification panel.
* `Generator` supplies one horizon-free obstruction family under its
  declared depth-one profile.

Identity is the equality of induced fiber relations. Mutual
factorization is proved equivalent to that identity. A directional
residual carries the exact pair identified by one presentation and
separated by another. If a comparison map `q` does not factor through
a compression `p`, finite represented search extracts such a residual.
Every map `r` that both refines `p` and carries `q` must split the pair,
and its represented class count is strictly larger. The comparison
forces the split. The necessity theorem selects no refinement; a later
theorem constructs one ordered-first-match joint refinement from the
supplied `D`, `p`, and `q`, without claiming it is natural or preferred.

The operational examples are likewise indexed by supplied
presentations. The support projection identifies records that a
support-plus-notes view separates; extending a represented panel can
change its certificate while leaving the stored world unchanged; and
two declared generator profiles classify one pair differently.

## Scope and nonclaims

* The forced-split theorem is a finite common-carrier result over a
  represented list of natural numbers. The heterogeneous transport
  version remains separate.
* The comparison `q` is supplied. Nothing here generates a first
  presentation, a physical time, or a distinguished external fact.
* A required split does not make the complete repair unique, natural,
  or preferred.
* `supportNotesView` is complete only for the seven fields of the
  declared `World` record. It is not an observer-complete view.
* The `Metatheory` namespace diagnoses an attempted all-view predicate
  by using ambient Lean functions. Those functions are not stored in
  `World`, admitted to `CWorld`, or produced by replay.
* The module does not turn `ABSOLUTE_NO_OUTSIDE_UNFORMULABLE` into a
  theorem that an absolute outside is either present or absent.
* No self-evaluation interface is defined, so no general self-cutting
  or self-certification theorem is claimed.
-/

namespace PresentationRelativity

open Compression Represented NoOutside Generator RefusalFrontier

/-! ## 1. Relative identity is mutual factorization -/

/-- Two presentations induce the same identity relation on `D` exactly
when their fiber equalities agree at every represented pair. -/
def FiberIdentityOn (D : List Nat) (p q : Nat → Nat) : Prop :=
  ∀ x, x ∈ D → ∀ y, y ∈ D → (p x = p y ↔ q x = q y)

/-- Presentation identity on `D`: each presentation factors through
the other. This is relative identity, not equality of function bytes or
an unindexed identity claim. -/
def PresentationIdentityOn (D : List Nat) (p q : Nat → Nat) : Prop :=
  FactorsOn D p q ∧ FactorsOn D q p

theorem presentationIdentity_iff_fiberIdentity
    (D : List Nat) (p q : Nat → Nat) :
    PresentationIdentityOn D p q ↔ FiberIdentityOn D p q := by
  constructor
  · rintro ⟨hpq, hqp⟩ x hx y hy
    have hpq' := (factors_iff_fiberConstant D p q).mp hpq
    have hqp' := (factors_iff_fiberConstant D q p).mp hqp
    exact ⟨hpq' x hx y hy, hqp' x hx y hy⟩
  · intro h
    constructor
    · apply (factors_iff_fiberConstant D p q).mpr
      intro x hx y hy hp
      exact (h x hx y hy).mp hp
    · apply (factors_iff_fiberConstant D q p).mpr
      intro x hx y hy hq
      exact (h x hx y hy).mpr hq

/-- A typed directional residual: `p` identifies the represented pair
while `q` separates it. The witness is the relative non-identity; no
spatial inside or outside predicate occurs. -/
structure DirectionalResidual
    (D : List Nat) (p q : Nat → Nat) where
  left : Nat
  right : Nat
  left_mem : left ∈ D
  right_mem : right ∈ D
  identified : p left = p right
  separated : q left ≠ q right

theorem directionalResidual_refutes_identity
    {D : List Nat} {p q : Nat → Nat}
    (residual : DirectionalResidual D p q) :
    ¬ PresentationIdentityOn D p q := by
  intro hid
  have hpq := (factors_iff_fiberConstant D p q).mp hid.1
  exact residual.separated
    (hpq residual.left residual.left_mem residual.right
      residual.right_mem residual.identified)

/-- Relative identity has empty residual in both directions. Emptiness
means that neither presentation merges a represented pair separated by
the other. -/
def ResidualEmptyOn (D : List Nat) (p q : Nat → Nat) : Prop :=
  (¬ Nonempty (DirectionalResidual D p q)) ∧
    (¬ Nonempty (DirectionalResidual D q p))

theorem presentationIdentity_iff_residualEmpty
    (D : List Nat) (p q : Nat → Nat) :
    PresentationIdentityOn D p q ↔ ResidualEmptyOn D p q := by
  constructor
  · intro hid
    constructor
    · rintro ⟨residual⟩
      exact directionalResidual_refutes_identity residual hid
    · rintro ⟨residual⟩
      exact directionalResidual_refutes_identity residual ⟨hid.2, hid.1⟩
  · rintro ⟨hpqEmpty, hqpEmpty⟩
    constructor
    · apply (factors_iff_fiberConstant D p q).mpr
      intro x hx y hy hp
      cases hq : decide (q x = q y) with
      | true => exact of_decide_eq_true hq
      | false =>
        exact False.elim (hpqEmpty ⟨⟨x, y, hx, hy, hp,
          of_decide_eq_false hq⟩⟩)
    · apply (factors_iff_fiberConstant D q p).mpr
      intro x hx y hy hq
      cases hp : decide (p x = p y) with
      | true => exact of_decide_eq_true hp
      | false =>
        exact False.elim (hqpEmpty ⟨⟨x, y, hx, hy, hq,
          of_decide_eq_false hp⟩⟩)

/-- Relative presentation identity is itself an equivalence relation.
No external equality of presentations is required. -/
theorem presentationIdentity_equivalence (D : List Nat) :
    Equivalence (PresentationIdentityOn D) := by
  refine ⟨?_, ?_, ?_⟩
  · intro p
    apply (presentationIdentity_iff_fiberIdentity D p p).mpr
    intro x hx y hy
    exact Iff.rfl
  · intro p q hpq
    apply (presentationIdentity_iff_fiberIdentity D q p).mpr
    intro x hx y hy
    exact ((presentationIdentity_iff_fiberIdentity D p q).mp hpq
      x hx y hy).symm
  · intro p q r hpq hqr
    apply (presentationIdentity_iff_fiberIdentity D p r).mpr
    intro x hx y hy
    exact ((presentationIdentity_iff_fiberIdentity D p q).mp hpq
      x hx y hy).trans
        ((presentationIdentity_iff_fiberIdentity D q r).mp hqr
          x hx y hy)

/-- A presentation compared only with itself has empty residual. This
is the exact self-comparison statement; it is not a general theorem
about evaluators certifying their own completeness. -/
theorem self_comparison_has_empty_residual
    (D : List Nat) (p : Nat → Nat) :
    ResidualEmptyOn D p p :=
  (presentationIdentity_iff_residualEmpty D p p).mp
    ((presentationIdentity_equivalence D).refl p)

/-- Identity relative to a declared question family means having
exactly the same fibers as the family's ordered first-match signature
presentation. The encoding is relative to the supplied `D` and `Q`; it
is not a natural representative selector. -/
def IdentityRelativeToQuestions
    (D : List Nat) (Q : List (Nat → Nat)) (p : Nat → Nat) : Prop :=
  PresentationIdentityOn D p (pQ D Q)

theorem identityRelativeToQuestions_iff
    (D : List Nat) (Q : List (Nat → Nat)) (p : Nat → Nat) :
    IdentityRelativeToQuestions D Q p ↔
      ∀ x, x ∈ D → ∀ y, y ∈ D →
        (p x = p y ↔ SigEq Q x y) := by
  constructor
  · intro h x hx y hy
    have hfib :=
      (presentationIdentity_iff_fiberIdentity D p (pQ D Q)).mp h
    exact (hfib x hx y hy).trans (pQ_exact D Q x hx y hy)
  · intro h
    apply (presentationIdentity_iff_fiberIdentity D p (pQ D Q)).mpr
    intro x hx y hy
    exact (h x hx y hy).trans (pQ_exact D Q x hx y hy).symm

/-- A directional residual based at `x`: `p` identifies `x` with one
represented point that `q` separates from it. -/
def DirectionalResidualAt
    (D : List Nat) (p q : Nat → Nat) (x : Nat) : Prop :=
  ∃ y, y ∈ D ∧ p x = p y ∧ q x ≠ q y

/-- The existing family split characterization is exactly a
directional relative non-identity between the declared signature
presentations of the source and extended question families. -/
theorem splitsAt_iff_directionalResidualAt
    (D : List Nat) (Q Q' : List (Nat → Nat))
    (x : Nat) (hx : x ∈ D) :
    SplitsAt D Q Q' x ↔
      DirectionalResidualAt D (pQ D Q) (pQ D Q') x := by
  constructor
  · rintro ⟨y, hy, hQ, hQ'⟩
    refine ⟨y, hy, (pQ_exact D Q x hx y hy).mpr hQ, ?_⟩
    intro hp
    exact hQ' ((pQ_exact D Q' x hx y hy).mp hp)
  · rintro ⟨y, hy, hp, hp'⟩
    refine ⟨y, hy, (pQ_exact D Q x hx y hy).mp hp, ?_⟩
    intro hQ'
    exact hp' ((pQ_exact D Q' x hx y hy).mpr hQ')

/-- Enlarging a question family makes its declared signature
presentation refine the source presentation. The direction is
`new → old`: the old map factors through the new map. -/
theorem family_enlargement_refines
    (D : List Nat) (Q Q' : List (Nat → Nat))
    (hsub : ∀ q, q ∈ Q → q ∈ Q') :
    FactorsOn D (pQ D Q') (pQ D Q) := by
  apply (factors_iff_fiberConstant D (pQ D Q') (pQ D Q)).mpr
  intro x hx y hy hnew
  apply (pQ_exact D Q x hx y hy).mpr
  apply enlarge_refines Q Q' hsub x y
  exact (pQ_exact D Q' x hx y hy).mp hnew

/-- A class split is precisely a failure of the second family to factor
through the first family. Hence the two declared signature presentations
are not relatively identical. This theorem does not by itself assert
that either family contains the other. -/
theorem family_split_refuses_relative_identity
    (D : List Nat) (Q Q' : List (Nat → Nat))
    (x : Nat) (hx : x ∈ D) (hs : SplitsAt D Q Q' x) :
    ¬ PresentationIdentityOn D (pQ D Q) (pQ D Q') := by
  obtain ⟨y, hy, hp, hp'⟩ :=
    (splitsAt_iff_directionalResidualAt D Q Q' x hx).mp hs
  exact directionalResidual_refutes_identity
    ⟨x, y, hx, hy, hp, hp'⟩

/-- When `Q'` actually contains `Q`, a witnessed split makes the
enlargement a strict refinement: the new declared signature presentation
carries the old one, while mutual factorization fails. -/
theorem family_enlargement_split_is_strict
    (D : List Nat) (Q Q' : List (Nat → Nat))
    (hsub : ∀ q, q ∈ Q → q ∈ Q')
    (x : Nat) (hx : x ∈ D) (hs : SplitsAt D Q Q' x) :
    FactorsOn D (pQ D Q') (pQ D Q) ∧
      ¬ PresentationIdentityOn D (pQ D Q) (pQ D Q') :=
  ⟨family_enlargement_refines D Q Q' hsub,
    family_split_refuses_relative_identity D Q Q' x hx hs⟩

/-! ## 2. A factorization failure forces every adequate repair to split -/

/-- Strict class growth for an arbitrary map refinement. The premise
`FactorsOn D r p` says that the coarser presentation `p` factors through
the finer presentation `r`. -/
theorem classCount_lt_of_refinement_split
    (D : List Nat) (p r : Nat → Nat)
    (hrp : FactorsOn D r p)
    (x y : Nat) (hx : x ∈ D) (hy : y ∈ D)
    (hpxy : p x = p y) (hrxy : r x ≠ r y) :
    classCount D [p] < classCount D [r] := by
  have hfc := (factors_iff_fiberConstant D r p).mp hrp
  have hdet : ∀ a, a ∈ D → ∀ b, b ∈ D →
      sigList [r] a = sigList [r] b → sigList [p] a = sigList [p] b := by
    intro a ha b hb hab
    have hrab : r a = r b := by
      simpa [sigList] using hab
    have hpab := hfc a ha b hb hrab
    simpa [sigList] using hpab
  apply count_lt_of_split (sigList [r]) (sigList [p]) D hdet x y hx hy
  · simpa [sigList] using hpxy
  · intro h
    apply hrxy
    simpa [sigList] using h

/-- A failed finite comparison forces a fiber split in every adequate
repair. The output contains the exact collapsed/separated pair. For
every `r`, carrying both the old presentation and the comparison makes
that pair distinct and strictly increases the represented class count.
No particular `r` is selected. -/
theorem forced_split_of_factorization_failure
    (D : List Nat) (p q : Nat → Nat)
    (hfail : ¬ FactorsOn D p q) :
    ∃ x, x ∈ D ∧
      ∃ y, y ∈ D ∧
        p x = p y ∧ q x ≠ q y ∧
          ∀ r : Nat → Nat,
            FactorsOn D r p → FactorsOn D r q →
              r x ≠ r y ∧ classCount D [p] < classCount D [r] := by
  have hw :
      ∃ x, x ∈ D ∧
        ∃ y, y ∈ D ∧ p x = p y ∧ q x ≠ q y := by
    cases hd : decide (∃ x, x ∈ D ∧
        ∃ y, y ∈ D ∧ p x = p y ∧ q x ≠ q y) with
    | true => exact of_decide_eq_true hd
    | false =>
      have hnone := of_decide_eq_false hd
      have hfc : FiberConstant D p q := by
        intro x hx y hy hpxy
        cases hq : decide (q x = q y) with
        | true => exact of_decide_eq_true hq
        | false =>
          exact False.elim
            (hnone ⟨x, hx, y, hy, hpxy, of_decide_eq_false hq⟩)
      exact absurd ((factors_iff_fiberConstant D p q).mpr hfc) hfail
  obtain ⟨x, hx, y, hy, hpxy, hqxy⟩ := hw
  refine ⟨x, hx, y, hy, hpxy, hqxy, ?_⟩
  intro r hrp hrq
  have hfc := (factors_iff_fiberConstant D r q).mp hrq
  have hrxy : r x ≠ r y := fun h => hqxy (hfc x hx y hy h)
  exact ⟨hrxy,
    classCount_lt_of_refinement_split D p r hrp x y hx hy hpxy hrxy⟩

/-- A concrete joint presentation for two supplied comparisons. It is
the first-match signature presentation relative to ordered `D` and the
supplied pair `p`, `q`; no naturality or preferred-selection claim is
made. -/
def jointPresentation
    (D : List Nat) (p q : Nat → Nat) : Nat → Nat :=
  pQ D [p, q]

/-- The joint presentation carries its left comparison. -/
theorem jointPresentation_factors_left
    (D : List Nat) (p q : Nat → Nat) :
    FactorsOn D (jointPresentation D p q) p := by
  apply (factors_iff_fiberConstant D (jointPresentation D p q) p).mpr
  intro x hx y hy hjoint
  have hsig : SigEq [p, q] x y :=
    (pQ_exact D [p, q] x hx y hy).mp hjoint
  exact hsig p (by simp)

/-- The joint presentation carries its right comparison. -/
theorem jointPresentation_factors_right
    (D : List Nat) (p q : Nat → Nat) :
    FactorsOn D (jointPresentation D p q) q := by
  apply (factors_iff_fiberConstant D (jointPresentation D p q) q).mpr
  intro x hx y hy hjoint
  have hsig : SigEq [p, q] x y :=
    (pQ_exact D [p, q] x hx y hy).mp hjoint
  exact hsig q (by simp)

/-- Once a comparison `q` is supplied, its failure to factor through
`p` constructively yields a strictly finer joint presentation carrying
both maps. This produces one declared refinement relative to ordered
`D` and the supplied pair; it does not generate `q` or select a natural
repair. -/
theorem jointPresentation_strict_of_factorization_failure
    (D : List Nat) (p q : Nat → Nat)
    (hfail : ¬ FactorsOn D p q) :
    FactorsOn D (jointPresentation D p q) p ∧
      FactorsOn D (jointPresentation D p q) q ∧
        classCount D [p] <
          classCount D [jointPresentation D p q] := by
  obtain ⟨x, hx, y, hy, hp, hq, hall⟩ :=
    forced_split_of_factorization_failure D p q hfail
  have hleft := jointPresentation_factors_left D p q
  have hright := jointPresentation_factors_right D p q
  have hstrict := hall (jointPresentation D p q) hleft hright
  exact ⟨hleft, hright, hstrict.2⟩

/-- The finite failure theorem returns a typed relative non-identity
witness before it constrains repairs. -/
theorem directionalResidual_of_factorization_failure
    (D : List Nat) (p q : Nat → Nat)
    (hfail : ¬ FactorsOn D p q) :
    Nonempty (DirectionalResidual D p q) := by
  obtain ⟨x, hx, y, hy, hp, hq, _⟩ :=
    forced_split_of_factorization_failure D p q hfail
  exact ⟨⟨x, y, hx, hy, hp, hq⟩⟩

/-! ## 3. Presented polarity, and the ambient all-view diagnostic -/

def ViewIdentifies {X Y : Type} (view : X → Y) (x y : X) : Prop :=
  view x = view y

def ViewSeparates {X Y : Type} (view : X → Y) (x y : X) : Prop :=
  view x ≠ view y

namespace Metatheory

/-! These declarations diagnose what happens if the ambient language
tries to quantify over every view. They do not give the represented
kernel an all-view observer. -/

def AllViewsIdentify {X : Type} (x y : X) : Prop :=
  ∀ (Y : Type) (view : X → Y), ViewIdentifies view x y

/-- An attempted absolute identification predicate collapses to
metatheoretic equality because its ambient quantifier includes `id`. -/
theorem attempted_absolute_identification_collapses_to_equality
    {X : Type} (x y : X) :
    AllViewsIdentify x y ↔ x = y := by
  constructor
  · intro h
    exact h X id
  · intro h
    subst y
    intro Y view
    rfl

/-- The ambient constant and identity functions refute both attempted
universal polarities for a distinct pair. This is a diagnostic of the
absolutizing quantifier, not an object-level survey of views. -/
theorem attempted_absolute_polarities_are_refuted
    {X : Type} {x y : X} (hne : x ≠ y) :
    (¬ ∀ (Y : Type) (view : X → Y), ViewSeparates view x y) ∧
      (¬ ∀ (Y : Type) (view : X → Y), ViewIdentifies view x y) := by
  constructor
  · intro h
    exact (h Unit (fun _ => ())) rfl
  · intro h
    exact hne (h X id)

end Metatheory

/-! ## 4. `notes` is exactly the coordinate omitted by `supp` -/

def supportNotesView (w : World) : Supp × List Nat :=
  (supp w, w.notes)

/-- Within the declared seven-field `World` record, operational support
and notes together determine the record. This is record extensionality,
not completeness beyond the declared schema. -/
theorem world_eq_iff_support_eq_and_notes_eq (w w' : World) :
    w = w' ↔ supp w = supp w' ∧ w.notes = w'.notes := by
  constructor
  · intro h
    subst w'
    exact ⟨rfl, rfl⟩
  · intro h
    rcases w with ⟨d, v, r, f, b, a, n⟩
    rcases w' with ⟨d', v', r', f', b', a', n'⟩
    simp only [supp, Supp.mk.injEq] at h
    rcases h with ⟨⟨rfl, rfl, rfl, rfl, rfl, rfl⟩, rfl⟩
    rfl

theorem supportNotesView_injective :
    Function.Injective supportNotesView := by
  intro w w' h
  apply (world_eq_iff_support_eq_and_notes_eq w w').mpr
  exact ⟨congrArg Prod.fst h, congrArg Prod.snd h⟩

/-- Two supplied records can be identified by operational support and
separated by the explicitly larger record view. Neither classification
is asserted without its view. -/
theorem support_identifies_while_supportNotes_separates
    {w w' : World}
    (hs : supp w = supp w') (hn : w.notes ≠ w'.notes) :
    ViewIdentifies supp w w' ∧
      ViewSeparates supportNotesView w w' := by
  exact ⟨hs, fun h => hn (congrArg Prod.snd h)⟩

/-- Changing only the represented-but-inert notes field cannot change
the enumerated operational results, for any supplied world and history.
The theorem compares two presentations of one declared record schema;
it does not name either one as an intrinsic inside or outside. -/
theorem notes_update_kernel_results_agree
    (w : World) (newNotes : List Nat)
    (history : List Event) (r : Req) :
    supp (replay history { w with notes := newNotes }) =
        supp (replay history w) ∧
      repairFamily (replay history { w with notes := newNotes }) r =
        repairFamily (replay history w) r ∧
      obstructedB (replay history { w with notes := newNotes }) r =
        obstructedB (replay history w) r ∧
      quiescentB (replay history { w with notes := newNotes }) =
        quiescentB (replay history w) := by
  exact effectual_outside_dichotomy
    { w with notes := newNotes } w rfl history r

/-! ## 5. Panel extension refines a represented joint quotient -/

/-- Joint non-separation is contravariant in panel inclusion: agreement
under a larger panel implies agreement under every supplied subpanel. -/
theorem panelEquiv_antitone
    {small large : List Evaluator} {i j : Nat}
    (hsub : ∀ E, E ∈ small → E ∈ large)
    (hlarge : PanelEquiv large i j) : PanelEquiv small i j := by
  intro E hE c hc
  exact hlarge E (hsub E hE) c hc

/-- A represented evaluator-extension event never removes a source
panel member. The statement is algebraic, not temporal. -/
theorem panel_members_preserved_by_extension (cw : CWorld) (E : Evaluator) :
    ∀ A, A ∈ cw.panel → A ∈ (stepC cw (.admitEvaluator E)).panel := by
  intro A hA
  simp only [stepC]
  split
  · exact hA
  · exact List.mem_append_left [E] hA

/-- The joint equivalence of the extended panel refines the source
equivalence. -/
theorem panel_extension_refines_equivalence
    (cw : CWorld) (E : Evaluator) (i j : Nat)
    (hextended : PanelEquiv (stepC cw (.admitEvaluator E)).panel i j) :
    PanelEquiv cw.panel i j :=
  panelEquiv_antitone (panel_members_preserved_by_extension cw E) hextended

/-- For a nonempty source panel, a negative certificate under the
extension was already valid under the source panel. The converse is
not claimed and the fixture below refutes it. -/
theorem certNeg_extension_implies_source
    (cw : CWorld) (E : Evaluator) (i j : Nat)
    (hne : cw.panel ≠ [])
    (hextended : certNegC (stepC cw (.admitEvaluator E)) i j = true) :
    certNegC cw i j = true := by
  change certNegB (stepC cw (.admitEvaluator E)).panel i j = true at hextended
  change certNegB cw.panel i j = true
  rw [certNeg_iff_panelEquiv] at hextended ⊢
  exact ⟨hne, panel_extension_refines_equivalence cw E i j hextended.2⟩

def coarsePanel : List Evaluator := [[[0, 1]], [[0, 1]]]

def separatingEvaluator : Evaluator := [[0]]

def sourcePanelWorld (w : World) : CWorld :=
  ⟨w, coarsePanel⟩

def extendedPanelWorld (w : World) : CWorld :=
  stepC (sourcePanelWorld w) (.admitEvaluator separatingEvaluator)

/-- For every supplied base record, extending the represented panel
changes only the observation apparatus. The same pair loses its
negative certificate while the stored world remains equal. This is a
presentation comparison, not discovery of an intrinsic classification. -/
theorem panel_extension_changes_verdict_not_world (w : World) :
    (extendedPanelWorld w).base = (sourcePanelWorld w).base ∧
      certNegC (sourcePanelWorld w) 0 1 = true ∧
      certNegC (extendedPanelWorld w) 0 1 = false := by
  constructor
  · exact admitEvaluator_base_inert (sourcePanelWorld w) separatingEvaluator
  · simp [extendedPanelWorld, sourcePanelWorld, stepC, coarsePanel,
      separatingEvaluator, certNegC, certNegB, verdictB, sepB]

/-! ## 6. The declared generator witness under two supplied profiles -/

def boolBit : Bool → Nat
  | false => 0
  | true => 1

/-- An injective finite code for the declared depth-one profile. The
code changes representation but adds no observational distinction. -/
def encodeDepthOneProfile (v : Bool × Bool × Bool) : Nat :=
  4 * boolBit v.1 + 2 * boolBit v.2.1 + boolBit v.2.2

theorem encodeDepthOneProfile_injective :
    Function.Injective encodeDepthOneProfile := by
  intro a b h
  rcases a with ⟨a1, a2, a3⟩
  rcases b with ⟨b1, b2, b3⟩
  cases a1 <;> cases a2 <;> cases a3 <;>
    cases b1 <;> cases b2 <;> cases b3 <;>
      simp_all [encodeDepthOneProfile, boolBit]

def depthOnePresentation (s : PState) (i : Nat) : Nat :=
  encodeDepthOneProfile (profile1 s i)

theorem depthOnePresentation_eq_iff (s : PState) (i j : Nat) :
    depthOnePresentation s i = depthOnePresentation s j ↔
      profile1 s i = profile1 s j := by
  exact ⟨fun h => encodeDepthOneProfile_injective h,
    fun h => congrArg encodeDepthOneProfile h⟩

def generatorDomain (n : Nat) : List Nat :=
  List.range (n + 1)

/-- On the represented carrier window, the explicitly supplied index
presentation does not factor through the declared depth-one presentation.
The obstruction is the already-proved pair `1,2`. The identity-grade
index comparison is an imported demand; it is not generated by the
depth-one profile. -/
theorem declared_generator_index_comparison_does_not_factor
    (n : Nat) (h : 3 ≤ n) :
    ¬ FactorsOn (generatorDomain n)
      (depthOnePresentation (reflState n)) id := by
  intro hf
  have hfc := (factors_iff_fiberConstant
    (generatorDomain n) (depthOnePresentation (reflState n)) id).mp hf
  have h1 : 1 ∈ generatorDomain n := by
    simp [generatorDomain]
    omega
  have h2 : 2 ∈ generatorDomain n := by
    simp [generatorDomain]
    omega
  have hp : depthOnePresentation (reflState n) 1 =
      depthOnePresentation (reflState n) 2 :=
    (depthOnePresentation_eq_iff (reflState n) 1 2).mpr
      (generation_never_dries n h).2
  have hid := hfc 1 h1 2 h2 hp
  simp at hid

/-- Conditional on the supplied index comparison, the declared generator
is a concrete instance of comparison-forced refinement. Every presentation
that carries both the depth-one profile and that comparison must split a
witnessed old fiber and strictly increase the represented class count. The
theorem selects no repair and does not generate the comparison demand. -/
theorem declared_generator_index_comparison_forces_refinement
    (n : Nat) (h : 3 ≤ n) :
    ∃ x, x ∈ generatorDomain n ∧
      ∃ y, y ∈ generatorDomain n ∧
        depthOnePresentation (reflState n) x =
            depthOnePresentation (reflState n) y ∧
          id x ≠ id y ∧
            ∀ r : Nat → Nat,
              FactorsOn (generatorDomain n) r
                  (depthOnePresentation (reflState n)) →
                FactorsOn (generatorDomain n) r id →
                  r x ≠ r y ∧
                    classCount (generatorDomain n)
                        [depthOnePresentation (reflState n)] <
                      classCount (generatorDomain n) [r] :=
  forced_split_of_factorization_failure
    (generatorDomain n) (depthOnePresentation (reflState n)) id
      (declared_generator_index_comparison_does_not_factor n h)

/-- The existing generator pair is identified by the declared
depth-one profile and separated by the explicitly index-enriched
profile. This reclassifies an existing witness; it neither derives the
profiles nor strengthens the scoped generation theorem. -/
theorem declared_generator_profiles_disagree_at_pair
    (n : Nat) (h : 3 ≤ n) :
    ViewIdentifies (profile1 (reflState n)) 1 2 ∧
      ViewSeparates (profileV (reflState n)) 1 2 := by
  exact ⟨(generation_never_dries n h).2,
    valued_marks_collapse_generation n 1 2 (by omega)⟩

end PresentationRelativity
