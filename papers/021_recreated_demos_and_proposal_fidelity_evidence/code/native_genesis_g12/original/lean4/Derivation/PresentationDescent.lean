import Derivation.PresentationNaturality

/-!
# Premetric presentation descent

This module starts with two presentation carriers `P` and `Q`.  They
are not assumed to be views of a prior common carrier.

Scoped typed translations are the 1-cells.  When both translations
are totalized, their two round-trip equations are the coherence
2-cell.  A faithful common descent is not primitive: it is a proposed
carrier together with injective presentation maps that identify the
two translations.

The central result is exact:

* coherent round trips produce a faithful common descent;
* any faithful common descent forces both round trips to cohere;
* therefore a failed round trip for this declared translation pair
  forbids faithful elimination of its presentation index.

Nothing discovers a new object or decides which distinctions matter.
When coherence fails, the former identification simply cannot descend
through the declared arrows without collapsing one of the presentations
internally.  The two presentations must remain typed separately at this
interface.  Another translation pair may still be coherent; no universal
impossibility over all possible or admissible arrows is claimed.

No metric, addition, scalar, magnitude, observer, truth predicate,
global world, preferred quotient, or authority is introduced.
-/

namespace PresentationDescent

open PresentationNaturality

/-! ## 1. Scoped translations and totalization -/

/-- Two typed scoped translations. Neither carrier is declared to be
the substrate of the other. -/
structure TranslationAttempt (P Q : Type) where
  forward : P -> Option Q
  backward : Q -> Option P

/-- A supplied total realization of both scoped translations. The
realizing equations bind the total maps to the original scoped
arrows; totality is not inferred from their types. -/
structure Totalization {P Q : Type} (t : TranslationAttempt P Q) where
  forward : P -> Q
  backward : Q -> P
  forward_realizes : forall p, t.forward p = some (forward p)
  backward_realizes : forall q, t.backward q = some (backward q)

/-- An explicit failure of one scoped arrow to be defined. -/
inductive TranslationGap {P Q : Type} (t : TranslationAttempt P Q)
    where
  | forward (p : P) (missing : t.forward p = none)
  | backward (q : Q) (missing : t.backward q = none)

/-- An undefined translation prevents any totalization that preserves
the exact declared scoped-arrow equations. This says nothing about a
different arrow obtained by overwriting or extending those constraints. -/
theorem translation_gap_refuses_totalization
    {P Q : Type} {t : TranslationAttempt P Q}
    (gap : TranslationGap t) :
    Not (Nonempty (Totalization t)) := by
  rintro ⟨u⟩
  cases gap with
  | forward p missing =>
      have hreal := u.forward_realizes p
      rw [missing] at hreal
      simp at hreal
  | backward q missing =>
      have hreal := u.backward_realizes q
      rw [missing] at hreal
      simp at hreal

/-! ## 2. Coherence as a 2-cell -/

/-- The two triangle equations for a supplied totalization.  This is
the coherence 2-cell; it is data/proof between the two composites, not
an observation made from another presentation. -/
structure RoundTripCoherent
    {P Q : Type} {t : TranslationAttempt P Q}
    (u : Totalization t) : Prop where
  left : forall p, u.backward (u.forward p) = p
  right : forall q, u.forward (u.backward q) = q

/-- A round-trip failure.  It is internal to the two supplied arrows. -/
inductive CoherenceResidual
    {P Q : Type} {t : TranslationAttempt P Q}
    (u : Totalization t) : Type where
  | left (p : P) (not_closed : u.backward (u.forward p) ≠ p)
  | right (q : Q) (not_closed : u.forward (u.backward q) ≠ q)

theorem coherence_residual_refutes_round_trip
    {P Q : Type} {t : TranslationAttempt P Q}
    {u : Totalization t} (residual : CoherenceResidual u) :
    Not (RoundTripCoherent u) := by
  intro h
  cases residual with
  | left p hfail => exact hfail (h.left p)
  | right q hfail => exact hfail (h.right q)

/-- A closed pair of typed translations is exactly sufficient to
enter the repository's existing presentation-isomorphism carrier
layer.  This bridge does not add observations or residual values. -/
def coherent_to_bij
    {P Q : Type} {t : TranslationAttempt P Q}
    {u : Totalization t} (h : RoundTripCoherent u) : Bij P Q where
  fwd := u.forward
  bwd := u.backward
  fwd_bwd := h.right
  bwd_fwd := h.left

/-! ## 3. Faithful common descent is equivalent to coherence -/

/-- The two presentation maps have exactly the same image in a supplied
carrier.  This excludes the trivial claim that the coproduct `P ⊕ Q` is
already a descent merely because it is a common carrier. -/
def CoincidentImages {P Q C : Type} (left : P -> C) (right : Q -> C) : Prop :=
  (forall p, exists q, left p = right q) ∧
    (forall q, exists p, right q = left p)

/-- A proposed elimination of the presentation index.  `Carrier` is
existential output data, not a common world assumed before `P` and
`Q`.  Injectivity prevents the descent from manufacturing coherence by
collapsing either presentation internally. -/
structure FaithfulCommonDescent
    {P Q : Type} {t : TranslationAttempt P Q}
    (u : Totalization t) where
  Carrier : Type
  left : P -> Carrier
  right : Q -> Carrier
  left_injective : Function.Injective left
  right_injective : Function.Injective right
  forward_identified : forall p, left p = right (u.forward p)
  backward_identified : forall q, right q = left (u.backward q)

/-- The defining translation equalities make the two embedded images
coincident.  This is derived independently from round-trip coherence. -/
theorem faithful_common_descent_has_coincident_images
    {P Q : Type} {t : TranslationAttempt P Q}
    {u : Totalization t} (d : FaithfulCommonDescent u) :
    CoincidentImages d.left d.right := by
  constructor
  · intro p
    exact ⟨u.forward p, d.forward_identified p⟩
  · intro q
    exact ⟨u.backward q, d.backward_identified q⟩

/-- Coherent translations make the indices eliminable.  The witness
uses `P` as one possible descent carrier; it is not a preferred or
natural choice. -/
def coherent_to_faithful_descent
    {P Q : Type} {t : TranslationAttempt P Q}
    {u : Totalization t} (h : RoundTripCoherent u) :
    FaithfulCommonDescent u where
  Carrier := P
  left := id
  right := u.backward
  left_injective := Function.injective_id
  right_injective := by
    intro q q' heq
    have hf := congrArg u.forward heq
    simpa [h.right] using hf
  forward_identified p := (h.left p).symm
  backward_identified _ := rfl

/-- A faithful common descent forces both triangle equations.  The
proof uses only the two identification laws and injectivity of the
presentation maps. -/
theorem faithful_descent_to_coherent
    {P Q : Type} {t : TranslationAttempt P Q}
    {u : Totalization t} (d : FaithfulCommonDescent u) :
    RoundTripCoherent u where
  left p := by
    apply d.left_injective
    calc
      d.left (u.backward (u.forward p)) = d.right (u.forward p) :=
        (d.backward_identified (u.forward p)).symm
      _ = d.left p := (d.forward_identified p).symm
  right q := by
    apply d.right_injective
    calc
      d.right (u.forward (u.backward q)) = d.left (u.backward q) :=
        (d.forward_identified (u.backward q)).symm
      _ = d.right q := (d.backward_identified q).symm

/-- **Presentation indices are faithfully eliminable exactly when the
two translations close coherently.** -/
theorem faithful_descent_iff_round_trip_coherent
    {P Q : Type} {t : TranslationAttempt P Q}
    (u : Totalization t) :
    Nonempty (FaithfulCommonDescent u) ↔ RoundTripCoherent u := by
  constructor
  · rintro ⟨d⟩
    exact faithful_descent_to_coherent d
  · intro h
    exact ⟨coherent_to_faithful_descent h⟩

/-- Failure of coherence for this declared totalization forbids every
faithful common descent compatible with it.  A different translation
pair may still close.  A descent for this pair could be forced only by
dropping injectivity or one of the identification equations; that would
erase an internal distinction or cease to represent the declared
translations. -/
theorem incoherence_forces_index_retention
    {P Q : Type} {t : TranslationAttempt P Q}
    {u : Totalization t} (hfail : Not (RoundTripCoherent u)) :
    Not (Nonempty (FaithfulCommonDescent u)) := by
  intro hdescent
  exact hfail ((faithful_descent_iff_round_trip_coherent u).mp hdescent)

/-- A concrete residual for the declared arrows is therefore enough to
force retention of the two typed presentations at this interface.  It
does not quantify over alternative translation pairs. -/
theorem residual_forces_index_retention
    {P Q : Type} {t : TranslationAttempt P Q}
    {u : Totalization t} (residual : CoherenceResidual u) :
    Not (Nonempty (FaithfulCommonDescent u)) :=
  incoherence_forces_index_retention
    (coherence_residual_refutes_round_trip residual)

end PresentationDescent
