import Derivation.FidelityClosure
import Derivation.PresentationRelativity

/-!
# The operational outside is a noninvertible presentation projection

`NoOutside.supp : World -> Supp` forgets exactly the represented `notes`
coordinate.  This module places that existing theorem in the premetric
translation calculus.

For every proposed backward translation `Supp -> World`, the two exact
round trips fail to cohere.  The proof is universal over the backward map:
two worlds with the same operational support and different notes refute
injectivity of `supp`, while any coherent inverse would make `supp`
injective.

Consequently no faithful coincident-image descent can erase the
`World`/`Supp` presentation index while preserving this forward projection.
The result does not assert an absolute outside or an ontological full world.
It identifies the repository's operational use of “outside” with the fiber
of a declared, noninvertible presentation map.
-/

namespace NoOutsideFidelity

open Represented NoOutside PresentationRelativity PresentationDescent

/-- The exact support fiber used by the obstruction: changing only notes
does not change support, but does change the represented record. -/
theorem support_fiber_contains_distinct_notes :
    exists w w' : World,
      supp w = supp w' ∧ w.notes ≠ w'.notes ∧ w ≠ w' := by
  refine ⟨genesis, { genesis with notes := [0] }, rfl, ?_, ?_⟩
  · decide
  · intro heq
    have hnotes := congrArg World.notes heq
    simp [genesis] at hnotes

/-- Therefore operational support is not injective. -/
theorem support_projection_not_injective :
    Not (Function.Injective supp) := by
  intro hinjective
  obtain ⟨w, w', hsupp, _, hne⟩ := support_fiber_contains_distinct_notes
  exact hne (hinjective hsupp)

/-- The scoped translation pair associated with a proposed inverse. Both
arrows are total as functions, but coherence remains a separate obligation. -/
def supportTranslationPair (backward : Supp -> World) :
    TranslationAttempt World Supp where
  forward w := some (supp w)
  backward s := some (backward s)

def supportTotalization (backward : Supp -> World) :
    Totalization (supportTranslationPair backward) where
  forward := supp
  backward := backward
  forward_realizes _ := rfl
  backward_realizes _ := rfl

/-- No proposed backward translation can close both round trips.  The proof
does not privilege the empty-notes section or any other section. -/
theorem support_translation_never_round_trip_coherent
    (backward : Supp -> World) :
    Not (RoundTripCoherent (supportTotalization backward)) := by
  intro hcoherent
  apply support_projection_not_injective
  intro w w' hsupp
  calc
    w = backward (supp w) := (hcoherent.left w).symm
    _ = backward (supp w') := congrArg backward hsupp
    _ = w' := hcoherent.left w'

/-- Hence no choice of backward translation produces a faithful common
descent compatible with the operational support projection. -/
theorem support_translation_never_faithfully_erases_index
    (backward : Supp -> World) :
    Not (Nonempty
      (FaithfulCommonDescent (supportTotalization backward))) :=
  incoherence_forces_index_retention
    (support_translation_never_round_trip_coherent backward)

/-- The universal form quantifies over every possible proposed inverse. -/
theorem no_support_inverse_faithfully_erases_index :
    Not (exists backward : Supp -> World,
      Nonempty (FaithfulCommonDescent (supportTotalization backward))) := by
  rintro ⟨backward, hdescent⟩
  exact support_translation_never_faithfully_erases_index backward hdescent

/-- Despite the failed index erasure, every enumerated operational result
still factors through support.  This is the exact existing no-outside
dichotomy, restated without spatial polarity. -/
theorem notes_fiber_has_no_operational_authority
    (w : World) (newNotes : List Nat)
    (history : List Event) (requirement : Req) :
    supp (replay history { w with notes := newNotes }) =
        supp (replay history w) ∧
      repairFamily (replay history { w with notes := newNotes }) requirement =
        repairFamily (replay history w) requirement ∧
      obstructedB (replay history { w with notes := newNotes }) requirement =
        obstructedB (replay history w) requirement ∧
      quiescentB (replay history { w with notes := newNotes }) =
        quiescentB (replay history w) :=
  notes_update_kernel_results_agree w newNotes history requirement

end NoOutsideFidelity
