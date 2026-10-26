import Derivation.PresentationDescent

/-!
# Retained multiplicity under failed quotient identification

Let `coarse` be a former presentation-index equivalence and `fine` a
refinement: every `fine` identification was already a `coarse`
identification.  There is then a canonical collapse map

`Quotient fine -> Quotient coarse`.

The map is always surjective.  It is injective exactly when every
`coarse` identification is still available in `fine`.  Therefore, if
`coarse` identifies `x` with a symmetry-related presentation
`sigma x` while `fine` does not, two distinct refined classes survive
and collapse to one former class.

No class is manufactured by the theorem.  A previous identification
simply ceases to descend.  The result uses no finite carrier, counting,
metric, observer, evaluator, global world, or preferred representative.
It is a theorem about supplied equivalence relations and their quotient
universal property.
-/

namespace QuotientRetention

/-- `fine` refines `coarse`: every identification available after the
refinement was already available before it. -/
structure RelationRefinement {I : Type} (fine coarse : Setoid I) : Prop where
  relates : forall {x y}, fine.r x y -> coarse.r x y

theorem RelationRefinement.refl {I : Type} (s : Setoid I) :
    RelationRefinement s s :=
  ⟨fun h => h⟩

theorem RelationRefinement.trans
    {I : Type} {fine middle coarse : Setoid I}
    (hfm : RelationRefinement fine middle)
    (hmc : RelationRefinement middle coarse) :
    RelationRefinement fine coarse :=
  ⟨fun h => hmc.relates (hfm.relates h)⟩

/-- The quotient map induced by forgetting distinctions introduced by
the finer relation.  It chooses no representatives. -/
def collapseMap
    {I : Type} {fine coarse : Setoid I}
    (h : RelationRefinement fine coarse) :
    Quotient fine -> Quotient coarse :=
  Quotient.lift (fun x => Quotient.mk coarse x)
    (fun _ _ hxy => Quotient.sound (h.relates hxy))

theorem collapseMap_mk
    {I : Type} {fine coarse : Setoid I}
    (h : RelationRefinement fine coarse) (x : I) :
    collapseMap h (Quotient.mk fine x) = Quotient.mk coarse x :=
  rfl

/-- Every former quotient class still has a refined preimage. -/
theorem collapseMap_surjective
    {I : Type} {fine coarse : Setoid I}
    (h : RelationRefinement fine coarse) :
    Function.Surjective (collapseMap h) := by
  intro z
  exact Quotient.inductionOn z fun x => ⟨Quotient.mk fine x, rfl⟩

/-- A failed former identification leaves two distinct refined classes
that have the same image in the former quotient. -/
theorem failed_identification_retains_two_classes
    {I : Type} {fine coarse : Setoid I}
    (h : RelationRefinement fine coarse)
    {x y : I} (hcoarse : coarse.r x y)
    (hfine : Not (fine.r x y)) :
    Quotient.mk fine x ≠ Quotient.mk fine y ∧
      collapseMap h (Quotient.mk fine x) =
        collapseMap h (Quotient.mk fine y) := by
  constructor
  · intro heq
    exact hfine (Quotient.exact heq)
  · exact Quotient.sound hcoarse

/-- Consequently the collapse from the refined quotient back to the
former quotient is not injective. -/
theorem failed_identification_makes_collapse_noninjective
    {I : Type} {fine coarse : Setoid I}
    (h : RelationRefinement fine coarse)
    {x y : I} (hcoarse : coarse.r x y)
    (hfine : Not (fine.r x y)) :
    Not (Function.Injective (collapseMap h)) := by
  intro hinjective
  have hsame :
      collapseMap h (Quotient.mk fine x) =
        collapseMap h (Quotient.mk fine y) :=
    Quotient.sound hcoarse
  exact hfine (Quotient.exact (hinjective hsame))

/-- Injectivity is recovered exactly when no former identification was
lost.  This is the quotient-level fidelity criterion. -/
theorem collapseMap_injective_iff_reverse_refinement
    {I : Type} {fine coarse : Setoid I}
    (h : RelationRefinement fine coarse) :
    Function.Injective (collapseMap h) ↔
      (forall {x y}, coarse.r x y -> fine.r x y) := by
  constructor
  · intro hinjective x y hcoarse
    have hsame :
        collapseMap h (Quotient.mk fine x) =
          collapseMap h (Quotient.mk fine y) :=
      Quotient.sound hcoarse
    exact Quotient.exact (hinjective hsame)
  · intro hreverse a
    refine Quotient.inductionOn a ?_
    intro x b
    refine Quotient.inductionOn b ?_
    intro y hxy
    exact Quotient.sound (hreverse (Quotient.exact hxy))

/-- The user's symmetry form: a former exchange identification that
fails after refinement leaves two surviving classes over one former
class. -/
theorem symmetry_failure_retains_multiplicity
    {I : Type} {fine coarse : Setoid I}
    (h : RelationRefinement fine coarse)
    (sigma : I -> I) (x : I)
    (hbefore : coarse.r x (sigma x))
    (hafter : Not (fine.r x (sigma x))) :
    exists a b : Quotient fine,
      a ≠ b ∧ collapseMap h a = collapseMap h b := by
  exact ⟨Quotient.mk fine x, Quotient.mk fine (sigma x),
    (failed_identification_retains_two_classes h hbefore hafter).1,
    (failed_identification_retains_two_classes h hbefore hafter).2⟩

/-- Successive refinements compose without selecting representatives.
This is the algebraic basis for recursive failures of identification:
each stage maps to every earlier coarser stage. -/
theorem collapseMap_compose
    {I : Type} {fine middle coarse : Setoid I}
    (hfm : RelationRefinement fine middle)
    (hmc : RelationRefinement middle coarse) :
    collapseMap (hfm.trans hmc) = collapseMap hmc ∘ collapseMap hfm := by
  funext z
  exact Quotient.inductionOn z fun _ => rfl

end QuotientRetention
