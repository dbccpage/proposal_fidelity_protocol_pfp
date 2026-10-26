import Derivation.FidelityClosure

/-!
# The endogenous fidelity generator

`FidelityClosure.fidelitySetoid N` is the least equivalence relation on
presentation indices containing every attempted translation whose exact
scoped arrows totalize and whose round trips cohere.

This universal property removes the supplied `fine` relation from the
retained-multiplicity theorem.  Compare the generated fidelity quotient
with the attempted indiscrete quotient in which every presentation index
is erased.  If no coherent path connects two indices, their generated
fidelity classes are distinct even though the indiscrete quotient collapses
them.

Structure is therefore retained multiplicity produced by closure under
coherent translations: nothing creates a class, and no observer chooses a
distinction.  The maximal attempted identification simply fails to descend
faithfully through the internally generated relation.

The translation network is still supplied.  `NoCoherentPath` is a
proposition, not a claimed decision procedure.  This is an endogenous
closure relative to declared presentations and attempts, not an absolute
origin of the first presentation.
-/

namespace EndogenousFidelityGenerator

open PresentationDescent FidelityClosure QuotientRetention

/-- A direct edge admitted by the fidelity rule. -/
def AdmittedStep (N : TranslationNetwork) (i j : N.Index) : Prop :=
  exists (a : N.Attempt i j)
    (u : Totalization (N.pair a)), RoundTripCoherent u

theorem admitted_step_has_fidelity_path
    {N : TranslationNetwork} {i j : N.Index}
    (h : AdmittedStep N i j) : FidelityRel N i j := by
  rcases h with ⟨a, u, hcoherent⟩
  exact ⟨FidelityPath.step a u hcoherent⟩

/-- **Least generated equivalence.**  Every equivalence relation that
contains each internally admitted direct step also contains every generated
fidelity path. -/
theorem fidelity_is_least_equivalence_containing_admitted_steps
    (N : TranslationNetwork) (S : Setoid N.Index)
    (hadmit : forall {i j}, AdmittedStep N i j -> S.r i j) :
    forall {i j}, FidelityRel N i j -> S.r i j := by
  intro i j hpath
  rcases hpath with ⟨path⟩
  induction path with
  | refl x => exact S.iseqv.refl x
  | step a u hcoherent =>
      exact hadmit ⟨a, u, hcoherent⟩
  | symm _ ih => exact S.iseqv.symm ih
  | trans _ _ ih₁ ih₂ => exact S.iseqv.trans ih₁ ih₂

/-- The indiscrete attempted relation erases every presentation index.  It
is a comparison ceiling, not a claim that all presentations are identical. -/
def indiscreteSetoid (I : Type) : Setoid I where
  r _ _ := True
  iseqv :=
    { refl := fun _ => True.intro
      symm := fun _ => True.intro
      trans := fun _ _ => True.intro }

/-- The generated fidelity relation always refines the attempted universal
collapse. -/
theorem fidelity_refines_indiscrete (N : TranslationNetwork) :
    RelationRefinement (fidelitySetoid N) (indiscreteSetoid N.Index) :=
  ⟨fun _ => True.intro⟩

abbrev GeneratedMultiplicity (N : TranslationNetwork) := FidelityQuotient N

/-- Forget every generated distinction and return to the attempted
indiscrete quotient. -/
def universalCollapse (N : TranslationNetwork) :
    GeneratedMultiplicity N -> Quotient (indiscreteSetoid N.Index) :=
  collapseMap (fidelity_refines_indiscrete N)

theorem universalCollapse_surjective (N : TranslationNetwork) :
    Function.Surjective (universalCollapse N) :=
  collapseMap_surjective (fidelity_refines_indiscrete N)

/-- **Endogenous retained multiplicity.**  No coherent path means that two
generated classes survive even though the attempted universal quotient
would erase their indices. -/
theorem no_coherent_path_retains_multiplicity
    (N : TranslationNetwork) {i j : N.Index}
    (hno : NoCoherentPath N i j) :
    classOf N i ≠ classOf N j ∧
      universalCollapse N (classOf N i) =
        universalCollapse N (classOf N j) := by
  exact failed_identification_retains_two_classes
    (fidelity_refines_indiscrete N) True.intro hno

/-- Existential form: the generated quotient contains multiplicity over one
indiscrete class. -/
theorem generated_structure_is_failed_erasure
    (N : TranslationNetwork) {i j : N.Index}
    (hno : NoCoherentPath N i j) :
    exists a b : GeneratedMultiplicity N,
      a ≠ b ∧ universalCollapse N a = universalCollapse N b :=
  ⟨classOf N i, classOf N j,
    (no_coherent_path_retains_multiplicity N hno).1,
    (no_coherent_path_retains_multiplicity N hno).2⟩

end EndogenousFidelityGenerator
