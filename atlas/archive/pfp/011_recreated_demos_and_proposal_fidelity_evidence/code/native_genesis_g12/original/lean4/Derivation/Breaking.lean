/-!
# A fixed-point-free reflection, and the two-cycle through each element

This module has NO EXPLICIT IMPORTS.  It is not dependency-free: with
no `prelude` command Lean implicitly imports `Init`, and
`lake env lean --deps` reports an `Init.olean` dependency accordingly.
That dependency is real and is not denied here.  An earlier version
said the module "imports NOTHING", which was false; the claim is
WITHDRAWN.

What IS claimed is narrower, and is about USE rather than dependency:
nothing below uses arithmetic, lists, indexing, succession, ordering,
counting or magnitude.

## The exact ceiling, stated before anything else

A declared fixed-point-free involution gives **a two-cycle through each
supplied element**.  That is all.  In particular:

* `Break` carries NO inhabitance law.  `emptyBreak` satisfies every
  field over an empty carrier, so nothing here asserts that anything
  exists.
* `Break` carries NO single-orbit law.  `SingleOrbit` is defined, and
  `fourBreak_not_singleOrbit` refutes it for a four-element model while
  `boolBreak_singleOrbit` confirms it for a two-element one, so nothing
  here asserts that there are exactly two things.

Both are exhibited below rather than described.  An earlier version of
this module said "two-ness is not a field, `two_arises` derives it".
That was FALSE twice over: the theorem was the fixed-point-free field
restated in the other direction, and the carrier admits both zero
elements and four.  The claim is WITHDRAWN and replaced by the ceiling
above.

## Weight

The STRUCTURAL results — `ne_image`, `two_cycle`,
`no_orbit_constant_equivariant_endomap` — are immediate consequences of
the fields.  The EXAMPLES are not: `constFalse_represents`,
`constFalse_not_equivariant`, `boolBreak_singleOrbit`,
`fourBreak_not_singleOrbit` and the two countermodels are finite case
analyses over `Bool` and `Bool × Bool`, using definitional reduction
and composition of earlier results.  An earlier version said every
proof was "an immediate corollary of a field", which was false of the
examples; that claim is WITHDRAWN.

The content is the choice of primitive, not the difficulty, and the
primitive assumes the distinction it is sometimes said to produce.

## Verification boundary

`lean4/Derivation.lean` imports this module and prints an axiom report
for each of its exported theorems, so they appear in
`artifacts/lean_axioms.txt` and are covered by the whitelist in
`ci/check_lean_audit.py`.  Every one of them reports NO axiom
dependency at all -- not `propext`, not `Quot.sound`.

An earlier version of this section said the module was PARKED: that the
root did not import it, that it therefore contributed no `#print
axioms` report and appeared in no axiom inventory, and that a
dependency on `Classical.choice` here would consequently fail no gate.
All three sentences were true when written and became false together
when the import landed.  They are WITHDRAWN.

The parked-module residual recorded in `CLAUDE.md` is closed FOR THIS
MODULE and remains open for every other module the root does not
import.  Closing it here does not close it there, and this module is
not evidence about those.

What is still NOT claimed: the audit's reach is the enumerated `#print
axioms` inventory.  "Axiom-free" here means those enumerated reports,
not a proof that the inventory names every declaration in this file.
-/

namespace Breaking

/-- A carrier and a reflection with no fixed point.  The reflection has
no index, no provenance, no order and no cause: nothing records why it
holds and no theorem depends on why.

What it does NOT carry: any inhabitance law, and any law forcing a
single orbit.  Both omissions are load-bearing and are witnessed
below. -/
structure Break where
  Whole : Type
  e : Whole → Whole
  e_involutive : ∀ w, e (e w) = w
  e_no_fixed : ∀ w, e w ≠ w

/-- Nothing is its own reflection, in the other direction.  This is the
`e_no_fixed` FIELD restated, not a derivation of distinctness from
anything weaker.  The content sits in the field; citing this result as
though distinction were derived would misreport it. -/
theorem ne_image (B : Break) (w : B.Whole) : w ≠ B.e w :=
  fun h => B.e_no_fixed w h.symm

/-- Each supplied element sits on a two-cycle: the reflection carries
its image back. -/
theorem two_cycle (B : Break) (w : B.Whole) : B.e (B.e w) = w :=
  B.e_involutive w

/-! ## The two omissions, exhibited -/

/-- Everything lies on one reflected pair: any two elements are equal
or reflections of each other.  Stated without counting — no numeral,
no cardinality, no enumeration appears. -/
def SingleOrbit (B : Break) : Prop :=
  ∀ w w' : B.Whole, w' = w ∨ w' = B.e w

/-- **No inhabitance.**  Every field holds vacuously over an empty
carrier, so `Break` does not assert that anything exists. -/
def emptyBreak : Break where
  Whole := Empty
  e := Empty.elim
  e_involutive := fun w => w.elim
  e_no_fixed := fun w => w.elim

/-- **No single orbit.**  Flipping only the first coordinate is
fixed-point-free and involutive on four elements, giving two disjoint
reflected pairs.  So `Break` does not assert that there are two
things. -/
def fourBreak : Break where
  Whole := Bool × Bool
  e p := (!p.1, p.2)
  e_involutive := by
    intro w
    cases w with
    | mk a b => cases a <;> rfl
  e_no_fixed := by
    intro w h
    cases w with
    | mk a b => cases a <;> exact Bool.noConfusion (congrArg Prod.fst h)

/-- `fourBreak` really does fail the single-orbit law: the second
coordinate is untouched by the reflection, so elements differing in it
are neither equal nor reflections.  This is the theorem the module's
ceiling depends on; an earlier version asserted it in prose only. -/
theorem fourBreak_not_singleOrbit : ¬ SingleOrbit fourBreak := by
  intro h
  rcases h (false, false) (false, true) with heq | hrefl
  · exact Bool.noConfusion (congrArg Prod.snd heq)
  · exact Bool.noConfusion (congrArg Prod.snd hrefl)

/-! ## Selectors -/

def Selector (B : Break) : Type := B.Whole → B.Whole

/-- What it picks is one of the two reflected things. -/
def Represents (B : Break) (s : Selector B) : Prop :=
  ∀ w, s w = w ∨ s w = B.e w

/-- It is constant on each reflected pair. -/
def OrbitConstant (B : Break) (s : Selector B) : Prop :=
  ∀ w, s (B.e w) = s w

/-- It commutes with the reflection. -/
def Equivariant (B : Break) (s : Selector B) : Prop :=
  ∀ w, s (B.e w) = B.e (s w)

/-- **No endomap is both orbit-constant and equivariant**, given an
inhabitant.

Named for exactly what it proves.  An earlier version called this
`no_global_section`, which named a quotient, a projection and a section
law that this module does not define — that name is WITHDRAWN.  A
section-of-the-quotient reading is not formalized here.

Two further honesty notes.  The proof does NOT spend `Represents`, so
carrying that hypothesis would overstate what is needed.  And it DOES
need an inhabitant: over `emptyBreak` a selector is vacuously both, and
there is no obstruction. -/
theorem no_orbit_constant_equivariant_endomap
    (B : Break) (w : B.Whole) (s : Selector B)
    (hconst : OrbitConstant B s) (hequi : Equivariant B s) : False :=
  B.e_no_fixed (s w) ((hequi w).symm.trans (hconst w))

/-! ## Both halves on a two-element carrier -/

def boolBreak : Break where
  Whole := Bool
  e := not
  e_involutive := by intro w; cases w <;> rfl
  e_no_fixed := by intro w h; cases w <;> exact Bool.noConfusion h

/-- The two-element carrier DOES satisfy the single-orbit law, so
`SingleOrbit` is a real condition separating the two models rather than
a predicate nothing meets. -/
theorem boolBreak_singleOrbit : SingleOrbit boolBreak := by
  intro w w'
  cases w <;> cases w'
  · exact Or.inl rfl
  · exact Or.inr rfl
  · exact Or.inr rfl
  · exact Or.inl rfl

def constFalse : Selector boolBreak := fun _ => false

theorem constFalse_represents : Represents boolBreak constFalse := by
  intro w
  cases w
  · exact Or.inl rfl
  · exact Or.inr rfl

theorem constFalse_orbitConstant : OrbitConstant boolBreak constFalse :=
  fun _ => rfl

/-- The obstruction is not vacuous: an orbit-constant representative
selector exists and fails exactly at equivariance.  A side can be
imposed; it cannot commute with the reflection. -/
theorem constFalse_not_equivariant :
    ¬ Equivariant boolBreak constFalse :=
  fun h => Bool.noConfusion (h false)

theorem imposable_but_not_equivariant :
    (Represents boolBreak constFalse ∧ OrbitConstant boolBreak constFalse) ∧
    ¬ Equivariant boolBreak constFalse :=
  ⟨⟨constFalse_represents, constFalse_orbitConstant⟩,
   constFalse_not_equivariant⟩

/-! ## The general case: a family of transformations, not one involution

`Break` fixes a single involution, and that restriction is not free.
`no_fixed_point_free_involution_on_Tri` below proves that the
three-point carrier admits NO fixed-point-free involution at all, so
`Break` cannot be instantiated over `Tri`.

That is a theorem about `Tri` and about nothing wider.  An earlier
version of this paragraph asserted the general fact behind it -- that a
fixed-point-free involution pairs any finite carrier into two-cycles,
so EVERY finite `Break` carrier has even cardinality, putting
three-fold and five-fold situations outside `Break` for an arithmetic
reason.  That statement is plausible and is **not proved here**: it
needs counting, which this module deliberately does not use, and no
declaration below establishes it.  It is WITHDRAWN as an assertion and
downgraded to OPEN rather than kept on the strength of the `Tri` case.
Nothing in this module or in the paper depends on it.

`Symmetry` asks for less.  There is no involution law, no group law, no
identity, no inverses, and no composition -- only a family of
transformations with no point that all of them fix.  The obstruction
never used more than that. -/

structure Symmetry where
  Whole : Type
  Sym : Type
  act : Sym → Whole → Whole
  no_common_fixed : ∀ w, ∃ g, act g w ≠ w

def SymSelector (S : Symmetry) : Type := S.Whole → S.Whole

/-- Constant on each orbit: the selector ignores the symmetry. -/
def SymOrbitConstant (S : Symmetry) (s : SymSelector S) : Prop :=
  ∀ g w, s (S.act g w) = s w

/-- Commutes with the symmetry. -/
def SymEquivariant (S : Symmetry) (s : SymSelector S) : Prop :=
  ∀ g w, s (S.act g w) = S.act g (s w)

/-- **The premise the obstruction actually spends.**  It is not that
every point is moved by SOME symbol; it is only that NO point is fixed
by EVERY symbol.  That asks for strictly less, and it is exactly what
the two selector laws contradict: composed, they force the selected
value to be fixed by every symbol, so a carrier with no such point
admits no such value.

Stated over a bare action rather than over `Symmetry`, because the
premise is weaker than that structure's field and stating it there
would hide the difference. -/
theorem no_selector_of_no_common_fixed_point
    {W Sym : Type} (act : Sym → W → W) (w : W) (s : W → W)
    (hnone : ¬ ∃ p, ∀ g, act g p = p)
    (hconst : ∀ g w, s (act g w) = s w)
    (hequi : ∀ g w, s (act g w) = act g (s w)) : False :=
  hnone ⟨s w, fun g => (hequi g w).symm.trans (hconst g w)⟩

/-- `Symmetry`'s field implies that weaker premise.

The converse is NOT proved here and is not constructively available:
recovering `∀ w, ∃ g, act g w ≠ w` from `¬ ∃ p, ∀ g, act g p = p`
requires deciding a proposition for which this module assumes no
decidability.  The two are therefore related in one direction only, and
the proved direction is the one the obstruction uses. -/
theorem no_common_fixed_point (S : Symmetry) :
    ¬ ∃ p, ∀ g, S.act g p = p :=
  fun h => h.elim (fun p hp => (S.no_common_fixed p).elim (fun g hg => hg (hp g)))

/-- **No selector is both orbit-constant and equivariant**, given an
inhabitant, for any family of transformations with no common fixed
point.

The proof is two equations composed.  Orbit-constancy says the value
does not move when the argument does; equivariance says the value moves
exactly as the argument does; together they say the value does not move
at all, under any symbol.  A carrier where no point is fixed by
everything admits no such value, hence no such selector.

This is now a COROLLARY of `no_selector_of_no_common_fixed_point`
rather than a direct proof from the field.  An earlier version proved
it directly by extracting a moving symbol at `s w`, which spent more of
the field than the argument needs.

The same two honesty notes as the involution case apply.  No
`Represents` hypothesis is spent, so carrying one would overstate what
is needed.  An inhabitant IS needed: over an empty carrier every
selector is vacuously both and there is no obstruction. -/
theorem no_orbit_constant_equivariant_selector
    (S : Symmetry) (w : S.Whole) (s : SymSelector S)
    (hconst : SymOrbitConstant S s) (hequi : SymEquivariant S s) : False :=
  no_selector_of_no_common_fixed_point S.act w s
    (no_common_fixed_point S) hconst hequi

/-- `Break` is the one-symbol case, so the general theorem SUBSUMES
`no_orbit_constant_equivariant_endomap` rather than sitting beside it. -/
def ofBreak (B : Break) : Symmetry where
  Whole := B.Whole
  Sym := Unit
  act _ := B.e
  no_common_fixed w := ⟨(), B.e_no_fixed w⟩

/-! ### The smallest carrier the involution form cannot reach -/

inductive Tri where
  | t0 | t1 | t2
  deriving DecidableEq

def rot : Tri → Tri
  | .t0 => .t1
  | .t1 => .t2
  | .t2 => .t0

/-- A three-point carrier under a three-fold rotation.  Witness that
the generalization is not cosmetic: the theorem applies here, and
`Break` cannot be instantiated here at all. -/
def triSymmetry : Symmetry where
  Whole := Tri
  Sym := Unit
  act _ := rot
  no_common_fixed w := ⟨(), by cases w <;> decide⟩

/-- **Parity, exhibited rather than described.**  No fixed-point-free
involution exists on the three-point carrier.

Stated concretely for `Tri` instead of in general, because a general
statement would need counting and this module uses none.  The case
analysis is the whole content: fixing where `t0` goes forces where its
image goes, and the remaining point is left fixed. -/
theorem no_fixed_point_free_involution_on_Tri
    (e : Tri → Tri) (hinv : ∀ w, e (e w) = w) (hfix : ∀ w, e w ≠ w) :
    False := by
  cases h0 : e .t0 with
  | t0 => exact hfix .t0 h0
  | t1 =>
      have h1 : e .t1 = .t0 := by
        have hb := hinv .t0
        rw [h0] at hb
        exact hb
      cases h2 : e .t2 with
      | t0 =>
          have hb := hinv .t2
          rw [h2] at hb
          rw [h0] at hb
          exact Tri.noConfusion hb
      | t1 =>
          have hb := hinv .t2
          rw [h2] at hb
          rw [h1] at hb
          exact Tri.noConfusion hb
      | t2 => exact hfix .t2 h2
  | t2 =>
      have h1 : e .t2 = .t0 := by
        have hb := hinv .t0
        rw [h0] at hb
        exact hb
      cases h2 : e .t1 with
      | t0 =>
          have hb := hinv .t1
          rw [h2] at hb
          rw [h0] at hb
          exact Tri.noConfusion hb
      | t1 => exact hfix .t1 h2
      | t2 =>
          have hb := hinv .t1
          rw [h2] at hb
          rw [h1] at hb
          exact Tri.noConfusion hb

/-- The hypothesis is spent, not decorative.  Where some point IS fixed
by every symbol, the constant selector at it is both orbit-constant and
equivariant.

An earlier version of this comment added that `Symmetry.no_common_fixed`
is therefore "exactly the field that fails and exactly what the
obstruction costs".  That is WITHDRAWN: the field is SUFFICIENT but
strictly more than the argument spends, as
`no_selector_of_no_common_fixed_point` shows.  The exact condition is
recorded in `selector_iff_common_fixed_point` below, where it is proved
in both directions instead of asserted. -/
theorem selector_exists_at_common_fixed_point
    {W Sym : Type} (act : Sym → W → W) (p : W) (hp : ∀ g, act g p = p) :
    ∃ s : W → W,
      (∀ g w, s (act g w) = s w) ∧ (∀ g w, s (act g w) = act g (s w)) :=
  ⟨fun _ => p, fun _ _ => rfl, fun g _ => (hp g).symm⟩

/-- **The exact characterization**, given an inhabitant: an
orbit-constant equivariant selector exists precisely when some point is
fixed by every symbol.

Both directions are proved, so this is a statement of what the
obstruction costs rather than a claim about it.  The forward direction
needs the inhabitant and is the obstruction; the backward direction is
the constant selector above.  Nothing here is about `Symmetry`: the
condition is a property of the action alone, and `Symmetry`'s field is
one way -- not the only way, and more than is needed -- to secure its
negation. -/
theorem selector_iff_common_fixed_point
    {W Sym : Type} (act : Sym → W → W) (w : W) :
    (∃ s : W → W,
        (∀ g w, s (act g w) = s w) ∧ (∀ g w, s (act g w) = act g (s w)))
      ↔ (∃ p, ∀ g, act g p = p) :=
  ⟨fun h => h.elim (fun s hs =>
      ⟨s w, fun g => (hs.2 g w).symm.trans (hs.1 g w)⟩),
   fun h => h.elim (fun p hp =>
      selector_exists_at_common_fixed_point act p hp)⟩

/-! ## What this does NOT claim

* It does not claim `Break` is forced.  It is a declared shape.
* It does not claim `Symmetry` is forced either, nor that the tied
  minimal responses of this repository form one of its orbits.  They do
  NOT: those classes are separated by an isomorphism invariant, and an
  invariant measure already selects among them.  The obstruction here
  bites WITHIN a class, not across classes.
* It does not derive distinctness, two-ness, or existence.  `ne_image`
  restates a field; `emptyBreak` and `fourBreak` show the carrier
  admits zero and four elements.
* It does not define a quotient, a projection, or a section, and
  proves nothing about any.
* It does not claim the reflection has a cause, a source, or a place in
  any order.
* It introduces no counting, magnitude, norm, or observer.
* It proves nothing about `DiffObs`, `PresIso`, `NonZeroPair`, or any
  other structure in this repository.  No bridge is proved.
-/

end Breaking
