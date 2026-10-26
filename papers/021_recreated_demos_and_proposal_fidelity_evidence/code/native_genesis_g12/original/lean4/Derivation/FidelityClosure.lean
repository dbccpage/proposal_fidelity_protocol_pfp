import Derivation.QuotientRetention

/-!
# Endogenous fidelity closure

A translation network supplies presentation indices, their heterogeneous
carriers, and scoped translation attempts. It does not supply an
equivalence relation on the indices.

The index-fidelity relation is generated internally.  A single step is admitted
only when its declared scoped arrows have a totalization and the two
round trips cohere.  Reflexive, symmetric, and transitive path constructors
then generate every permitted identification.  Every generated path
composes to an actual carrier bijection.

Thus no observer decides which indices are connected.  Coherence proofs
generate the relation.  A failed direct attempt does not prove two indices
distinct, because another coherent path may connect them.  Index retention
requires the stronger statement that no coherent path exists.

Path reachability alone is not a global carrier descent.  Parallel paths may
act differently, and an admitted loop may act nontrivially on the carrier.  A
separate faithful-network-descent structure below requires every path action
to agree after embedding.  A loop that moves one carrier element refutes such
a descent.

An attempted index label descends to the fidelity quotient exactly when it
is invariant along every coherent path.  Therefore an `inside`/`outside`
polarity that changes under a coherent translation is a presentation label,
not a property of the descended object.

The network itself, its carriers, and its attempted arrows remain supplied.
This module derives their fidelity closure; it does not derive the first
presentation or claim an absolute origin.
-/

namespace FidelityClosure

open PresentationNaturality PresentationDescent

/-! ## 1. A heterogeneous network of attempted translations -/

structure TranslationNetwork where
  Index : Type
  Carrier : Index -> Type
  Attempt : Index -> Index -> Type
  pair : {i j : Index} -> Attempt i j ->
    TranslationAttempt (Carrier i) (Carrier j)

/-- A fidelity path contains only translation attempts whose exact scoped
arrows totalize and whose two round trips cohere.  Symmetry is justified by
the mutual translations inside each admitted step, not by assuming a reverse
network arrow. -/
inductive FidelityPath (N : TranslationNetwork) : N.Index -> N.Index -> Type
  | refl (i : N.Index) : FidelityPath N i i
  | step {i j : N.Index} (a : N.Attempt i j)
      (u : Totalization (N.pair a))
      (h : RoundTripCoherent u) : FidelityPath N i j
  | symm {i j : N.Index} : FidelityPath N i j -> FidelityPath N j i
  | trans {i j k : N.Index} :
      FidelityPath N i j -> FidelityPath N j k -> FidelityPath N i k

/-- Every generated fidelity path carries an actual heterogeneous carrier
bijection. -/
def FidelityPath.toBij {N : TranslationNetwork} {i j : N.Index}
    (path : FidelityPath N i j) : Bij (N.Carrier i) (N.Carrier j) :=
  match path with
  | .refl i => Bij.rfl' (N.Carrier i)
  | .step _ _ h => coherent_to_bij h
  | .symm p => p.toBij.symm
  | .trans p q => p.toBij.trans q.toBij

/-! ## 2. Coherence generates the fidelity equivalence -/

def FidelityRel (N : TranslationNetwork) (i j : N.Index) : Prop :=
  Nonempty (FidelityPath N i j)

theorem fidelity_refl (N : TranslationNetwork) (i : N.Index) :
    FidelityRel N i i :=
  ⟨FidelityPath.refl i⟩

theorem fidelity_symm {N : TranslationNetwork} {i j : N.Index}
    (h : FidelityRel N i j) : FidelityRel N j i := by
  rcases h with ⟨path⟩
  exact ⟨path.symm⟩

theorem fidelity_trans {N : TranslationNetwork} {i j k : N.Index}
    (hij : FidelityRel N i j) (hjk : FidelityRel N j k) :
    FidelityRel N i k := by
  rcases hij with ⟨p⟩
  rcases hjk with ⟨q⟩
  exact ⟨p.trans q⟩

/-- The index-fidelity setoid is derived from coherent paths.  It is not an
operator-supplied classification and does not assert path-independent carrier
transport. -/
def fidelitySetoid (N : TranslationNetwork) : Setoid N.Index where
  r := FidelityRel N
  iseqv :=
    { refl := fidelity_refl N
      symm := fidelity_symm
      trans := fidelity_trans }

abbrev FidelityQuotient (N : TranslationNetwork) := Quotient (fidelitySetoid N)

def classOf (N : TranslationNetwork) (i : N.Index) : FidelityQuotient N :=
  Quotient.mk (fidelitySetoid N) i

theorem class_eq_iff_coherent_path
    (N : TranslationNetwork) (i j : N.Index) :
    classOf N i = classOf N j ↔ FidelityRel N i j := by
  constructor
  · exact Quotient.exact
  · intro h
    exact Quotient.sound h

/-- The universal retention condition: no coherent path through any
admissible sequence of attempts connects the two indices. -/
def NoCoherentPath (N : TranslationNetwork) (i j : N.Index) : Prop :=
  Not (FidelityRel N i j)

theorem no_coherent_path_retains_indices
    (N : TranslationNetwork) {i j : N.Index}
    (h : NoCoherentPath N i j) :
    classOf N i ≠ classOf N j := by
  intro heq
  exact h ((class_eq_iff_coherent_path N i j).mp heq)

/-- A failed direct realization is deliberately not enough to establish
`NoCoherentPath`: the identity path still relates every index to itself,
regardless of an incoherent attempted endomorphism.  This is the smallest
counterexample to universalizing one failed round trip. -/
theorem failed_endomorphism_does_not_refute_self_fidelity
    {N : TranslationNetwork} {i : N.Index}
    {t : TranslationAttempt (N.Carrier i) (N.Carrier i)}
    {u : Totalization t} (_ : CoherenceResidual u) :
    FidelityRel N i i :=
  fidelity_refl N i

/-! ## 3. Loop action is the residual to global carrier descent -/

/-- A loop is trivial when its composed carrier bijection fixes every point. -/
def LoopTrivial {N : TranslationNetwork} {i : N.Index}
    (loop : FidelityPath N i i) : Prop :=
  forall x, loop.toBij.fwd x = x

/-- A represented failure of path coherence: an admitted loop moves one
carrier element. -/
structure HolonomyResidual (N : TranslationNetwork) where
  index : N.Index
  loop : FidelityPath N index index
  point : N.Carrier index
  moved : loop.toBij.fwd point ≠ point

/-- A genuine common descent for the heterogeneous network.  Each carrier
embeds faithfully, and transport along every admitted path becomes equality
in the descended carrier.  This is stronger than mere index reachability. -/
structure FaithfulNetworkDescent (N : TranslationNetwork) where
  Carrier : Type
  embed : (i : N.Index) -> N.Carrier i -> Carrier
  embed_injective : forall i, Function.Injective (embed i)
  path_identified : forall {i j} (path : FidelityPath N i j) (x : N.Carrier i),
    embed j (path.toBij.fwd x) = embed i x

/-- A nontrivial admitted loop forbids faithful global descent.  Forcing the
descent would identify two distinct points within one presentation. -/
theorem holonomy_residual_refuses_faithful_network_descent
    {N : TranslationNetwork} (residual : HolonomyResidual N) :
    Not (Nonempty (FaithfulNetworkDescent N)) := by
  rintro ⟨d⟩
  apply residual.moved
  apply d.embed_injective residual.index
  exact d.path_identified residual.loop residual.point

/-- Global path coherence requires every admitted endomorphism loop to act
as the identity. -/
def AllLoopsTrivial (N : TranslationNetwork) : Prop :=
  forall {i : N.Index} (loop : FidelityPath N i i), LoopTrivial loop

theorem faithful_network_descent_forces_trivial_loops
    {N : TranslationNetwork} (d : FaithfulNetworkDescent N) :
    AllLoopsTrivial N := by
  intro i loop x
  apply d.embed_injective i
  exact d.path_identified loop x

/-! ## 4. Presentation labels descend exactly when index-fidelity-invariant -/

def LabelInvariant {N : TranslationNetwork} {Y : Type}
    (label : N.Index -> Y) : Prop :=
  forall i j, FidelityRel N i j -> label i = label j

def LabelDescends {N : TranslationNetwork} {Y : Type}
    (label : N.Index -> Y) : Prop :=
  exists descended : FidelityQuotient N -> Y,
    forall i, descended (classOf N i) = label i

theorem label_descends_iff_fidelity_invariant
    {N : TranslationNetwork} {Y : Type}
    (label : N.Index -> Y) :
    LabelDescends label ↔ LabelInvariant label := by
  constructor
  · rintro ⟨descended, hdescended⟩ i j hpath
    calc
      label i = descended (classOf N i) := (hdescended i).symm
      _ = descended (classOf N j) :=
        congrArg descended (Quotient.sound hpath)
      _ = label j := hdescended j
  · intro hinvariant
    exact ⟨Quotient.lift label
      (fun i j hij => hinvariant i j hij), fun _ => rfl⟩

/-- Any attempted polarity that changes across a coherent translation
cannot be a predicate of the fidelity quotient. -/
theorem coherent_disagreement_refuses_label_descent
    {N : TranslationNetwork} {Y : Type}
    (label : N.Index -> Y) {i j : N.Index}
    (hpath : FidelityRel N i j) (hneq : label i ≠ label j) :
    Not (LabelDescends label) := by
  intro hdescends
  exact hneq ((label_descends_iff_fidelity_invariant label).mp hdescends
    i j hpath)

/-- Boolean `inside`/`outside` language is just one instance of the general
label theorem.  If the polarity flips along a coherent path, it does not
descend. -/
theorem polarity_flip_is_presentation_relative
    {N : TranslationNetwork} (polarity : N.Index -> Bool)
    {i j : N.Index} (hpath : FidelityRel N i j)
    (hflip : polarity i ≠ polarity j) :
    Not (LabelDescends polarity) :=
  coherent_disagreement_refuses_label_descent polarity hpath hflip

end FidelityClosure
