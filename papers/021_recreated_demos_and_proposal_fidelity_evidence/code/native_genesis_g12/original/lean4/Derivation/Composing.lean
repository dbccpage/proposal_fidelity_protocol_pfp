/-!
# Composition as a relation that is not required to be total, single-valued,
or associative

This module has NO EXPLICIT IMPORTS.  It is not dependency-free: with
no `prelude` command Lean implicitly imports `Init`, and
`lake env lean --deps` reports an `Init.olean` dependency accordingly.
That dependency is real and is not denied here.  An earlier version
said the module "imports NOTHING", which was false; the claim is
WITHDRAWN.

What IS claimed is narrower, and is about USE rather than dependency:
nothing below uses arithmetic, lists, natural-number indexing,
succession, an order relation on a carrier, counting or magnitude.

It DOES use dependent indexing, and that is load-bearing rather than
incidental.  `Arr : Node → Node → Type` is a family indexed by two
nodes, and the source and target positions matter — `Composes` is
stated over `Arr a b`, `Arr b c`, `Arr a c` precisely so the endpoints
line up.  An earlier version of this header claimed "no indexing",
which is false of the defining shape; that claim is WITHDRAWN.

A category supplies composition as an OPERATION: `∘` takes two arrows
and delivers a third, for every composable pair, always, uniquely.
`Web` supplies it as a three-place RELATION instead, and each of those
three guarantees is exhibited failing.

## The exact ceiling, stated before anything else

`Web.Arr a c` is a declared type that exists BEFORE `Composes`, and
`Composes` is a predicate over it.  So the subtype of arrows satisfying
`Composes f g ·` is directly definable, and this module does NOT claim
that composites form no collection, or that no filtering carrier
exists.  What it claims is narrower and is what the theorems prove:
**no total or unique composition operator is imposed, and no path
closure is generated.**

An earlier version of this module said `Composes` "cannot be replaced
by any function" and that "no function could extract the composite".
Both are FALSE, and `selection_is_possible` below exhibits a total
selection function on the very `Web` that was cited against it.  The
claims are WITHDRAWN.  What non-uniqueness shows is that the relation
does not DETERMINE an operation, not that selection is impossible.

## Weight

The proofs are one to four lines each.  The content is the choice of
shape — a relation rather than an operator — not the difficulty.

## Verification boundary

This module is PARKED in one exact sense: `lean4/Derivation.lean` does
not import it, so it contributes no `#print axioms` report and appears
in no axiom inventory or claim ledger entry.

It is NOT unchecked.  The `lean` job's final step elaborates every
`lean4/Derivation/**/*.lean` as its own Lake target, so CI does
typecheck this file.  An earlier version of this paragraph said the
repository's `lake build` gate elaborates nothing here and that a green
run is therefore not evidence that this module compiles.  That was true
when written and became false when the elaboration gate landed; it is
WITHDRAWN.

But elaboration is not auditing, and the difference is the open
residual.  Because no `#print axioms` line names anything here, the
whitelist in `ci/check_lean_audit.py` never sees this module: a
dependency on `Classical.choice` in this file would fail no gate.  The
reports quoted above were taken by hand and are not enforced by CI.
Read "this module elaborates" as exactly that, and not as "this module
is audited".
-/

namespace Composing

/-- Nodes, declared arrows, and a three-place composition RELATION.
`Arr a b` may be empty.  `Composes a b c f g h` may hold for no `h`,
for one, or for several.  There is no operator, no identity, and no
associativity law. -/
structure Web where
  Node : Type
  Arr : Node → Node → Type
  Composes : (a b c : Node) → Arr a b → Arr b c → Arr a c → Prop

/-- A pair composes when some composite holds of it.  Nothing requires
this. -/
def Composable (W : Web) (a b c : W.Node)
    (f : W.Arr a b) (g : W.Arr b c) : Prop :=
  ∃ h : W.Arr a c, W.Composes a b c f g h

/-! ## 1. Existence may fail -/

def noneCompose : Web where
  Node := Unit
  Arr _ _ := Bool
  Composes _ _ _ _ _ _ := False

/-- **Nothing has to compose.**  Arrows are present and no composite
holds of any pair, so `Composable` is a real condition. -/
theorem composition_may_fail :
    ¬ Composable noneCompose () () () true true := by
  rintro ⟨_, hfalse⟩
  exact hfalse

/-- An identity at `a`: an arrow composing neutrally on both sides. -/
def HasIdentity (W : Web) (a : W.Node) : Prop :=
  ∃ i : W.Arr a a,
    (∀ (b : W.Node) (f : W.Arr a b), W.Composes a a b i f f) ∧
    (∀ (b : W.Node) (f : W.Arr b a), W.Composes b a a f i f)

/-- **Identities may fail too**, against a stated predicate rather than
by assertion.  Where nothing composes, nothing can be neutral. -/
theorem noneCompose_no_identity : ¬ HasIdentity noneCompose () := by
  rintro ⟨_, hleft, _⟩
  exact hleft () true

/-! ## 2. Uniqueness may fail — but selection remains possible -/

def allCompose : Web where
  Node := Unit
  Arr _ _ := Bool
  Composes _ _ _ _ _ _ := True

/-- **The relation is not single-valued.**  Two distinct arrows are
both composites of the same pair, so the relation does not determine an
operation. -/
theorem composite_may_be_nonunique :
    ∃ h h' : allCompose.Arr () (),
      h ≠ h' ∧
      allCompose.Composes () () () true true h ∧
      allCompose.Composes () () () true true h' :=
  ⟨true, false, fun c => Bool.noConfusion c, trivial, trivial⟩

/-- A total selection function on `allCompose`. -/
def allSelect (a b c : allCompose.Node)
    (_ : allCompose.Arr a b) (_ : allCompose.Arr b c) :
    allCompose.Arr a c := true

/-- **Selection is possible even where uniqueness fails.**  `allSelect`
picks a valid composite for every pair, so non-uniqueness does NOT
prohibit a composite-selection function.  This is stated as a theorem
precisely because the earlier prose claimed the opposite. -/
theorem selection_is_possible :
    ∀ (a b c : allCompose.Node)
      (f : allCompose.Arr a b) (g : allCompose.Arr b c),
      allCompose.Composes a b c f g (allSelect a b c f g) :=
  fun _ _ _ _ _ => trivial

/-! ## 3. Associativity may fail, against a stated predicate -/

/-- A result reachable by bracketing on the left. -/
def LeftReach (W : Web) (a b c d : W.Node)
    (f : W.Arr a b) (g : W.Arr b c) (k : W.Arr c d) (w : W.Arr a d) : Prop :=
  ∃ u : W.Arr a c, W.Composes a b c f g u ∧ W.Composes a c d u k w

/-- A result reachable by bracketing on the right. -/
def RightReach (W : Web) (a b c d : W.Node)
    (f : W.Arr a b) (g : W.Arr b c) (k : W.Arr c d) (w : W.Arr a d) : Prop :=
  ∃ v : W.Arr b d, W.Composes b c d g k v ∧ W.Composes a b d f v w

/-- **Full relational associativity**: the two bracketings reach exactly
the same results.  For a multivalued relation this is an equality of
reachable-result relations, so it is an `Iff` and not an implication. -/
def RelAssoc (W : Web) : Prop :=
  ∀ (a b c d : W.Node) (f : W.Arr a b) (g : W.Arr b c) (k : W.Arr c d)
    (w : W.Arr a d),
    LeftReach W a b c d f g k w ↔ RightReach W a b c d f g k w

/-- The one-way law: everything reachable on the left is reachable on
the right.  Named for what it is, since an earlier version defined only
this and called it relational associativity. -/
def RelAssocLeft (W : Web) : Prop :=
  ∀ (a b c d : W.Node) (f : W.Arr a b) (g : W.Arr b c) (k : W.Arr c d)
    (w : W.Arr a d),
    LeftReach W a b c d f g k w → RightReach W a b c d f g k w

theorem relAssocLeft_of_relAssoc (W : Web) (h : RelAssoc W) :
    RelAssocLeft W :=
  fun a b c d f g k w hl => (h a b c d f g k w).mp hl

/-- A composition relation that is not associative. -/
def skewCompose : Web where
  Node := Unit
  Arr _ _ := Bool
  Composes _ _ _ f g h := h = (f && !g)

/-- **Even the one-way law fails.**  The witness is a result reachable
on the left and not on the right. -/
theorem skew_not_relAssocLeft : ¬ RelAssocLeft skewCompose := by
  intro h
  obtain ⟨v, hv, hw⟩ :=
    h () () () () true false true false ⟨true, rfl, rfl⟩
  rw [hv] at hw
  exact Bool.noConfusion hw

/-- **Full relational associativity fails**, against the `Iff`
predicate rather than by exhibiting two results and calling it a
refutation. -/
theorem skew_not_relAssoc : ¬ RelAssoc skewCompose :=
  fun h => skew_not_relAssocLeft (relAssocLeft_of_relAssoc skewCompose h)

/-! ## What this does NOT claim

* It does not claim `Web` is forced.  It is a declared shape.
* It does not claim composites form no collection, or that no
  filtering carrier exists.  `Arr a c` is a declared type and the
  subtype cut out by `Composes` is definable.  The claim is only that
  no total or unique operator is imposed and no path closure is
  generated.
* It does not claim selection is impossible.  `selection_is_possible`
  proves the opposite where uniqueness fails.
* Totality, single-valuedness, associativity and identity each have a
  stated predicate and a negative result: `composition_may_fail`,
  `composite_may_be_nonunique`, `skew_not_relAssoc`, and
  `noneCompose_no_identity`.
* INVERSES are merely NOT SUPPLIED.  No inverse law is defined here and
  none is refuted, so nothing about inverses should be read off this
  module.  An earlier version said identities and inverses were "each
  exhibited failing", which was true of neither at the time and is now
  true only of identities; the claim is WITHDRAWN and replaced by the
  two bullets above.
* It supplies no magnitude, weight, measure or summing.  There is no
  integral, no norm and no scalar, so this is composition without the
  sum; anything numeric needs imports this module does not make.
* It proves nothing about `DiffObs`, `PresIso`, `HFamily` or `Break`.
  No bridge is proved.
-/

end Composing
