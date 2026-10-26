import Derivation.ContactKernel

/-!
# Natural selection of an admissible pair, across presentations

`ContactKernel.no_equivariant_pair_valued_map` rules out one relabelling
-equivariant map, on one carrier, for one action: total maps
`DiffObs Bool Bool → Bool × Bool` commuting with Bool negation.  Its own
docstring says it is not a general refutation of a preferred choice.
This module does NOT subsume that theorem, and does not claim to.  It
supplies a PARALLEL obstruction — arguably the same phenomenon, but
over different objects — together with the transport machinery that
makes natural selection a well-typed question across presentations at
all.  The derivation that would make the sealed theorem an instance of
the general obstruction is OPEN.  Until it is proved, the sealed
theorem stands on its own scope and nothing here licenses it.

The construction is:

1. `Bij` — an explicit bijection, both round trips given as data.
2. `PresIso` — a presentation isomorphism between observers: bijections
   on the carrier and on the residual type that transport `delta` and
   `Zero`.  `zeroRel_transport` proves the induced zero relation
   transports, which is the law-level content.
3. `PresIso.refl`, `.symm`, `.trans` with their component laws proved
   BEFORE any groupoid or functor vocabulary is used.  No categorical
   object is claimed anywhere in this module; see the non-claims.
4. `Viable` — an observer together with evidence that its admissible
   pairs are inhabited.
5. `PresIso.mapPair` — the transported bundle `O` to `NonZeroPair O`.
6. `Family`, `Sec`, `IsNatural` — a declared collection of observers and
   isomorphisms, a dependent section of the pair bundle over it, and
   naturality of that section with respect to every isomorphism the
   family declares.
7. `no_natural_section_of_fixed_point_free` — the general obstruction.
8. Both boundaries, so the theorem is neither vacuous nor a universal
   refusal: `selection_is_possible_naturality_is_not` exhibits a raw
   section where no natural one exists, and `card4_natural_section`
   exhibits a presentation whose declared automorphism DOES carry a
   natural section.

## Non-claims, stated exactly

* No categorical structure is claimed.  `refl`, `symm` and `trans` are
  given with pointwise component laws only; this module never proves
  `PresIso` equalities and never asserts a groupoid, category, or
  functor.
* The obstruction is relative to the DECLARED family.  `autoFamily O F`
  contains exactly one object and one isomorphism, the exhibited `F`.
  Nothing is claimed about families this module does not construct.
* Everything proved here is over ONE-OBJECT families.  `Family` itself
  is general, and it deliberately requires neither composition nor
  inverses — naturality is with respect to exactly the arrows listed.
  Multi-object families, naturality under a generating set, and
  coherence of `mapPair` with `trans` and `symm` beyond the one-object
  case are FUTURE WORK, not results of this module.  Both fixtures
  below, negative and positive, are one-object; they separate two
  one-object situations, not two presentation theories.
* No claim that selection is impossible.  A raw section exists in the
  very case where no natural one does; the obstruction concerns natural
  selection only.
* No claim of a choice principle, of a quotient, or of anything
  downstream of either.
* `bool_obstruction_and_sealed_selector` states this module's
  obstruction and the sealed selector theorem TOGETHER.  It does not
  derive either from the other: they quantify over different objects —
  maps out of the observer type, versus sections of the pair bundle.
  Deriving the sealed statement from the general one is OPEN.
-/

namespace PresentationNaturality

open DiffInterface ContactKernel

variable {A B C X R X' R' X'' R'' : Type}

/-! ## 1. Explicit bijections

Both round trips are data, so nothing here needs a choice principle to
invert a function. -/

structure Bij (A B : Type) where
  fwd : A → B
  bwd : B → A
  fwd_bwd : ∀ b, fwd (bwd b) = b
  bwd_fwd : ∀ a, bwd (fwd a) = a

def Bij.rfl' (A : Type) : Bij A A where
  fwd a := a
  bwd a := a
  fwd_bwd _ := rfl
  bwd_fwd _ := rfl

def Bij.symm (f : Bij A B) : Bij B A where
  fwd := f.bwd
  bwd := f.fwd
  fwd_bwd := f.bwd_fwd
  bwd_fwd := f.fwd_bwd

def Bij.trans (f : Bij A B) (g : Bij B C) : Bij A C where
  fwd a := g.fwd (f.fwd a)
  bwd c := f.bwd (g.bwd c)
  fwd_bwd c := by rw [f.fwd_bwd, g.fwd_bwd]
  bwd_fwd a := by rw [g.bwd_fwd, f.bwd_fwd]

/-- A bijection separates what it distinguishes: the forward map is
injective, with no appeal to a choice principle. -/
theorem Bij.fwd_injective (f : Bij A B) {a a' : A} (h : f.fwd a = f.fwd a') :
    a = a' := by
  have := congrArg f.bwd h
  rwa [f.bwd_fwd, f.bwd_fwd] at this

/-! ## 2. Presentation isomorphisms -/

/-- A presentation isomorphism carries one observer to another: a
bijection of carriers, a bijection of residual values, and the two
transport laws that make `delta` and `Zero` agree across them. -/
structure PresIso (O : DiffObs X R) (O' : DiffObs X' R') where
  car : Bij X X'
  res : Bij R R'
  delta_transport : ∀ x y, res.fwd (O.delta x y) = O'.delta (car.fwd x) (car.fwd y)
  zero_transport : ∀ r, O.Zero r ↔ O'.Zero (res.fwd r)

/-- **The zero relation transports.**  This is the law-level content of
a presentation isomorphism: the relation `ZeroRel` induced by `O` and
the one induced by `O'` correspond along the carrier bijection.  Both
endpoint observers are named. -/
theorem zeroRel_transport {O : DiffObs X R} {O' : DiffObs X' R'}
    (F : PresIso O O') (x y : X) :
    ZeroRel O x y ↔ ZeroRel O' (F.car.fwd x) (F.car.fwd y) := by
  show O.Zero (O.delta x y) ↔ O'.Zero (O'.delta (F.car.fwd x) (F.car.fwd y))
  rw [← F.delta_transport x y]
  exact F.zero_transport (O.delta x y)

/-! ## 3. Identity, inverse, composition — with their component laws

The laws are proved on components.  No categorical vocabulary is used
here or anywhere below. -/

def PresIso.refl (O : DiffObs X R) : PresIso O O where
  car := Bij.rfl' X
  res := Bij.rfl' R
  delta_transport _ _ := rfl
  zero_transport _ := Iff.rfl

def PresIso.symm {O : DiffObs X R} {O' : DiffObs X' R'} (F : PresIso O O') :
    PresIso O' O where
  car := F.car.symm
  res := F.res.symm
  delta_transport x' y' := by
    have h := F.delta_transport (F.car.bwd x') (F.car.bwd y')
    rw [F.car.fwd_bwd, F.car.fwd_bwd] at h
    have h2 := congrArg F.res.bwd h
    rw [F.res.bwd_fwd] at h2
    show F.res.bwd (O'.delta x' y') = O.delta (F.car.bwd x') (F.car.bwd y')
    exact h2.symm
  zero_transport r' := by
    have h := F.zero_transport (F.res.bwd r')
    rw [F.res.fwd_bwd] at h
    exact h.symm

def PresIso.trans {O : DiffObs X R} {O' : DiffObs X' R'} {O'' : DiffObs X'' R''}
    (F : PresIso O O') (G : PresIso O' O'') : PresIso O O'' where
  car := F.car.trans G.car
  res := F.res.trans G.res
  delta_transport x y := by
    show G.res.fwd (F.res.fwd (O.delta x y)) = _
    rw [F.delta_transport x y, G.delta_transport]
    rfl
  zero_transport r := by
    show O.Zero r ↔ O''.Zero (G.res.fwd (F.res.fwd r))
    exact (F.zero_transport r).trans (G.zero_transport (F.res.fwd r))

theorem refl_car (O : DiffObs X R) (x : X) :
    (PresIso.refl O).car.fwd x = x := rfl

theorem trans_car {O : DiffObs X R} {O' : DiffObs X' R'} {O'' : DiffObs X'' R''}
    (F : PresIso O O') (G : PresIso O' O'') (x : X) :
    (F.trans G).car.fwd x = G.car.fwd (F.car.fwd x) := rfl

theorem symm_car_left {O : DiffObs X R} {O' : DiffObs X' R'}
    (F : PresIso O O') (x : X) : F.symm.car.fwd (F.car.fwd x) = x :=
  F.car.bwd_fwd x

theorem symm_car_right {O : DiffObs X R} {O' : DiffObs X' R'}
    (F : PresIso O O') (x' : X') : F.car.fwd (F.symm.car.fwd x') = x' :=
  F.car.fwd_bwd x'

theorem symm_symm_car {O : DiffObs X R} {O' : DiffObs X' R'}
    (F : PresIso O O') (x : X) : F.symm.symm.car.fwd x = F.car.fwd x := rfl

/-! ## 4. Viable observers and the transported pair bundle -/

/-- A viable observer: one whose admissible pairs are inhabited.  This
is the domain over which selecting a pair is even a question. -/
structure Viable (X R : Type) where
  obs : DiffObs X R
  pairs_inhabited : Nonempty (NonZeroPair obs)

/-- **The bundle transports.**  A presentation isomorphism carries an
admissible pair of `O` to an admissible pair of `O'`; admissibility is
preserved because the zero relation transports.  Both endpoint
observers are named. -/
def PresIso.mapPair {O : DiffObs X R} {O' : DiffObs X' R'}
    (F : PresIso O O') (p : NonZeroPair O) : NonZeroPair O' :=
  ⟨(F.car.fwd p.val.1, F.car.fwd p.val.2), fun h =>
    p.property ((zeroRel_transport F p.val.1 p.val.2).mpr h)⟩

/-- Viability transports.  `Nonempty` is a `Prop`, so eliminating it
into another `Prop` needs no choice principle. -/
theorem viable_transport {O : DiffObs X R} {O' : DiffObs X' R'}
    (F : PresIso O O') (h : Nonempty (NonZeroPair O)) :
    Nonempty (NonZeroPair O') :=
  h.elim fun p => ⟨F.mapPair p⟩

/-! ## 5. Declared families, sections, naturality -/

/-- A DECLARED presentation family: observers indexed by `Obj`, and a
collection of isomorphisms `Arr` between them.  Nothing is assumed
about closure under composition or inverses; the family is exactly what
it lists. -/
structure Family (X R : Type) where
  Obj : Type
  obs : Obj → DiffObs X R
  Arr : Type
  src : Arr → Obj
  tgt : Arr → Obj
  iso : (f : Arr) → PresIso (obs (src f)) (obs (tgt f))

/-- A section of the admissible-pair bundle: a pair chosen at every
observer of the family, dependently typed in that observer. -/
def Sec (D : Family X R) : Type := ∀ a : D.Obj, NonZeroPair (D.obs a)

/-- Naturality: the section commutes with every isomorphism the family
declares. -/
def IsNatural (D : Family X R) (s : Sec D) : Prop :=
  ∀ f : D.Arr, (D.iso f).mapPair (s (D.src f)) = s (D.tgt f)

/-- The one-object, one-isomorphism family generated by a presentation
automorphism.  This is the "explicitly defined family containing the
exhibited automorphism" that the obstruction below is relative to. -/
def autoFamily (O : DiffObs X R) (F : PresIso O O) : Family X R where
  Obj := Unit
  obs _ := O
  Arr := Unit
  src _ := ()
  tgt _ := ()
  iso _ := F

/-! ## 6. The general fixed-point obstruction -/

/-- **The obstruction.**  If a presentation automorphism fixes the
observer but fixes no admissible pair of it, then the pair bundle has
no natural section over the family that automorphism generates.

Scope, exactly: this is a statement about `autoFamily O F`.  It says
nothing about other families, other automorphisms, or non-natural
sections — a raw section may exist, and `selection_is_possible_
naturality_is_not` exhibits one.

**Weight of this theorem, recorded honestly.**  Over a one-object
family `IsNatural` unfolds to "the selected pair is fixed", so this
statement is NEAR-DEFINITIONAL and its proof is one line.  It must not
be cited as though the proof were the substance.  The substance is
elsewhere and is cited with it: the transport machinery — `PresIso`,
`zeroRel_transport`, `PresIso.mapPair`, `viable_transport` — which is
what makes natural selection a well-typed question across
presentations at all; and the two boundary theorems, of which
`card4_has_natural_section` is not definitional, since it required
exhibiting an automorphism with a fixed admissible pair.  Without that
positive boundary the statement would be an unfalsifiable refusal. -/
theorem no_natural_section_of_fixed_point_free
    (O : DiffObs X R) (F : PresIso O O)
    (hfree : ∀ p : NonZeroPair O, F.mapPair p ≠ p) :
    ¬ ∃ s : Sec (autoFamily O F), IsNatural (autoFamily O F) s := by
  rintro ⟨s, hs⟩
  exact hfree (s ()) (hs ())

/-- Contrapositive form: a natural section over `autoFamily O F` hands
back a pair the automorphism fixes.  This is the direction the positive
fixture below uses. -/
theorem fixed_pair_of_natural_section
    (O : DiffObs X R) (F : PresIso O O)
    (s : Sec (autoFamily O F)) (hs : IsNatural (autoFamily O F) s) :
    ∃ p : NonZeroPair O, F.mapPair p = p :=
  ⟨s (), hs ()⟩

/-! ## 7. The Bool-negation instance

The sealed observer `ContactKernel.boolEqObs` with the negation
relabelling, recovered as one instance of the general theorem. -/

def notBij : Bij Bool Bool where
  fwd := not
  bwd := not
  fwd_bwd := by decide
  bwd_fwd := by decide

/-- Negation is a presentation automorphism of `boolEqObs`: it permutes
the carrier and leaves the residual and the zero predicate alone. -/
def negIso : PresIso boolEqObs boolEqObs where
  car := notBij
  res := Bij.rfl' Bool
  delta_transport := by decide
  zero_transport _ := Iff.rfl

/-- Negation fixes no admissible pair of `boolEqObs`: it fixes no
element of `Bool` at all. -/
theorem negIso_fixed_point_free (p : NonZeroPair boolEqObs) :
    negIso.mapPair p ≠ p := by
  intro h
  have hv : ((!p.val.1), (!p.val.2)) = p.val := congrArg Subtype.val h
  have h1 : (!p.val.1) = p.val.1 := congrArg Prod.fst hv
  exact (by decide : ∀ b : Bool, (!b) ≠ b) p.val.1 h1

/-- **The Bool instance.**  No natural section over the family
generated by negation at `boolEqObs`. -/
theorem no_natural_section_boolEq :
    ¬ ∃ s : Sec (autoFamily boolEqObs negIso),
        IsNatural (autoFamily boolEqObs negIso) s :=
  no_natural_section_of_fixed_point_free boolEqObs negIso negIso_fixed_point_free

/-! ## 8. First boundary: selection is possible, naturality is not -/

def boolEqPair : NonZeroPair boolEqObs :=
  ⟨(false, true), fun h => Bool.noConfusion (h : (true : Bool) = false)⟩

def boolEqRawSection : Sec (autoFamily boolEqObs negIso) := fun _ => boolEqPair

/-- **The obstruction is about naturality, not about selection.**  Over
the very family where no natural section exists, a raw section is
exhibited explicitly.  So the theorem does not say a pair cannot be
picked; it says a pair cannot be picked compatibly with the declared
relabelling. -/
theorem selection_is_possible_naturality_is_not :
    Nonempty (Sec (autoFamily boolEqObs negIso)) ∧
    ¬ ∃ s : Sec (autoFamily boolEqObs negIso),
        IsNatural (autoFamily boolEqObs negIso) s :=
  ⟨⟨boolEqRawSection⟩, no_natural_section_boolEq⟩

/-! ## 9. Second boundary: a presentation that DOES carry a natural
section

Four elements, with a declared automorphism that transposes two of them
and fixes the other two.  The fixed pair is admissible, so the constant
section at it is natural.  The obstruction is therefore not a universal
refusal. -/

inductive Card4 where
  | e1 | e2 | e3 | e4
  deriving DecidableEq, Repr

/-- Transpose the first two, fix the last two. -/
def tw : Card4 → Card4
  | .e1 => .e2
  | .e2 => .e1
  | .e3 => .e3
  | .e4 => .e4

theorem tw_involutive : ∀ x, tw (tw x) = x := by
  intro x; cases x <;> rfl

def twBij : Bij Card4 Card4 where
  fwd := tw
  bwd := tw
  fwd_bwd := tw_involutive
  bwd_fwd := tw_involutive

/-- The identity-view kernel observer on four elements: its zero
relation is carrier equality. -/
def card4Obs : DiffObs Card4 (Card4 × Card4) := kernelObs (fun x => x)

def twPairBij : Bij (Card4 × Card4) (Card4 × Card4) where
  fwd p := (tw p.1, tw p.2)
  bwd p := (tw p.1, tw p.2)
  fwd_bwd p := by
    have h1 := tw_involutive p.1
    have h2 := tw_involutive p.2
    show (tw (tw p.1), tw (tw p.2)) = p
    rw [h1, h2]
  bwd_fwd p := by
    have h1 := tw_involutive p.1
    have h2 := tw_involutive p.2
    show (tw (tw p.1), tw (tw p.2)) = p
    rw [h1, h2]

/-- The transposition is a presentation automorphism of `card4Obs`. -/
def twIso : PresIso card4Obs card4Obs where
  car := twBij
  res := twPairBij
  delta_transport _ _ := rfl
  zero_transport r := by
    show r.1 = r.2 ↔ tw r.1 = tw r.2
    constructor
    · intro h; rw [h]
    · intro h; exact twBij.fwd_injective h

/-- The pair of the two fixed elements is admissible. -/
def card4Pair : NonZeroPair card4Obs :=
  ⟨(.e3, .e4), fun h => Card4.noConfusion (h : Card4.e3 = Card4.e4)⟩

def card4Section : Sec (autoFamily card4Obs twIso) := fun _ => card4Pair

/-- **A natural section exists here.**  The declared automorphism fixes
the admissible pair `(e3, e4)`, so the constant section at it commutes
with the automorphism.  Together with `no_natural_section_boolEq` this
shows the general theorem separates presentations rather than refusing
all of them. -/
theorem card4_natural_section :
    IsNatural (autoFamily card4Obs twIso) card4Section := by
  intro _
  apply Subtype.ext
  rfl

/-- The same fact in existential form, matching the shape the
obstruction negates. -/
theorem card4_has_natural_section :
    ∃ s : Sec (autoFamily card4Obs twIso),
      IsNatural (autoFamily card4Obs twIso) s :=
  ⟨card4Section, card4_natural_section⟩

/-- **The separation, stated as one theorem.**  Under the same
definitions of `Sec` and `IsNatural`, one declared presentation carries
a natural section and another does not.  Multiplicity of admissible
pairs is therefore not what decides it — `boolEqObs` and `card4Obs`
both have several. -/
theorem naturality_separates_presentations :
    (∃ s : Sec (autoFamily card4Obs twIso),
        IsNatural (autoFamily card4Obs twIso) s) ∧
    ¬ ∃ s : Sec (autoFamily boolEqObs negIso),
        IsNatural (autoFamily boolEqObs negIso) s :=
  ⟨card4_has_natural_section, no_natural_section_boolEq⟩

/-! ## 10. Relation to the sealed Bool selector theorem -/

/-- Both obstructions hold at `boolEqObs`, stated together so the two
endpoint statements are named in one place: this module's section-level
obstruction, and the sealed
`ContactKernel.no_equivariant_pair_valued_map`.

This is a CO-STATEMENT, not a derivation.  The two quantify over
different objects — maps out of the observer type, versus sections of
the admissible-pair bundle — and neither is obtained from the other
here.  Deriving the sealed statement from the general obstruction is
OPEN. -/
theorem bool_obstruction_and_sealed_selector :
    (∀ p : NonZeroPair boolEqObs, negIso.mapPair p ≠ p) ∧
    (¬ ∃ s : Sec (autoFamily boolEqObs negIso),
        IsNatural (autoFamily boolEqObs negIso) s) ∧
    (¬ ∃ sel : DiffObs Bool Bool → Bool × Bool,
        ∀ O : DiffObs Bool Bool,
          sel (swapObs O) = (!((sel O).1), !((sel O).2))) :=
  ⟨negIso_fixed_point_free, no_natural_section_boolEq,
   no_equivariant_pair_valued_map⟩

/-! ## 11. Coherence of the transported bundle

How `mapPair` interacts with identity, composition and inverse.  These
are the lemmas §3 deferred: §3 gave component laws for the carrier
bijection, these give them for the bundle map itself. -/

theorem mapPair_refl (O : DiffObs X R) (p : NonZeroPair O) :
    (PresIso.refl O).mapPair p = p := by
  apply Subtype.ext
  rfl

theorem mapPair_trans {O : DiffObs X R} {O' : DiffObs X' R'}
    {O'' : DiffObs X'' R''} (F : PresIso O O') (G : PresIso O' O'')
    (p : NonZeroPair O) :
    (F.trans G).mapPair p = G.mapPair (F.mapPair p) := by
  apply Subtype.ext
  rfl

theorem mapPair_symm_left {O : DiffObs X R} {O' : DiffObs X' R'}
    (F : PresIso O O') (p : NonZeroPair O) :
    F.symm.mapPair (F.mapPair p) = p := by
  apply Subtype.ext
  show (F.car.bwd (F.car.fwd p.val.1), F.car.bwd (F.car.fwd p.val.2)) = p.val
  rw [F.car.bwd_fwd, F.car.bwd_fwd]

theorem mapPair_symm_right {O : DiffObs X R} {O' : DiffObs X' R'}
    (F : PresIso O O') (q : NonZeroPair O') :
    F.mapPair (F.symm.mapPair q) = q := by
  apply Subtype.ext
  show (F.car.fwd (F.car.bwd q.val.1), F.car.fwd (F.car.bwd q.val.2)) = q.val
  rw [F.car.fwd_bwd, F.car.fwd_bwd]

/-! ## 12. Heterogeneous families over many objects

`Family` above fixes ONE carrier `X` and ONE residual type `R` for
every object, because its arrows are a flat `Arr` with `src`/`tgt`
functions.  `HFamily` indexes arrows as `Hom a b`, which makes an
endomorphism definitionally an inhabitant of `Hom a a`, and that in
turn lets the carrier and the residual type vary with the object.  No
dependent transport is needed anywhere below. -/

structure HFamily where
  Obj : Type
  car : Obj → Type
  res : Obj → Type
  obs : (a : Obj) → DiffObs (car a) (res a)
  Hom : Obj → Obj → Type
  iso : (a b : Obj) → Hom a b → PresIso (obs a) (obs b)

def HSec (D : HFamily) : Type := ∀ a : D.Obj, NonZeroPair (D.obs a)

def HIsNatural (D : HFamily) (s : HSec D) : Prop :=
  ∀ (a b : D.Obj) (h : D.Hom a b), (D.iso a b h).mapPair (s a) = s b

/-- **The obstruction over many objects.**  A declared endomorphism at
ANY object of the family, fixing no admissible pair there, already
rules out a natural section of the whole family.  The one-object case
is `no_natural_section_of_fixed_point_free`; this is the same argument
with the endpoints supplied by `Hom a a` rather than by a one-object
restriction, so the carrier and residual type may differ from object to
object. -/
theorem no_natural_section_of_endo (D : HFamily) (a : D.Obj)
    (h : D.Hom a a)
    (hfree : ∀ p : NonZeroPair (D.obs a), (D.iso a a h).mapPair p ≠ p) :
    ¬ ∃ s : HSec D, HIsNatural D s := by
  rintro ⟨s, hs⟩
  exact hfree (s a) (hs a a h)

/-- The one-object heterogeneous family generated by an automorphism. -/
def hAutoFamily (O : DiffObs X R) (F : PresIso O O) : HFamily where
  Obj := Unit
  car _ := X
  res _ := R
  obs _ := O
  Hom _ _ := Unit
  iso _ _ _ := F

/-- **Bridge between the two family notions at one object.**  Both
endpoint structures are named: a natural section over the flat
homogeneous `autoFamily` exists exactly when one exists over the
indexed heterogeneous `hAutoFamily`.  This is stated only for the
one-object case; see the non-claims. -/
theorem hAuto_iff_auto (O : DiffObs X R) (F : PresIso O O) :
    (∃ s : HSec (hAutoFamily O F), HIsNatural (hAutoFamily O F) s) ↔
    (∃ s : Sec (autoFamily O F), IsNatural (autoFamily O F) s) := by
  constructor
  · rintro ⟨s, hs⟩
    exact ⟨fun _ => s (), fun _ => hs () () ()⟩
  · rintro ⟨s, hs⟩
    exact ⟨fun _ => s (), fun _ _ _ => hs ()⟩

/-! ## 13. A genuinely heterogeneous two-object fixture

Two objects with DIFFERENT carriers and different residual types:
`Bool` with `boolEqObs`, and `Card4` with `card4Obs`.  One declared
automorphism at each object, none between them.  Changing only the
automorphism at the `Bool` object flips the family between having no
natural section and having one, which shows the obstruction is carried
by the declared arrows rather than by heterogeneity itself. -/

inductive Two where
  | bool | four
  deriving DecidableEq, Repr

def twoCar : Two → Type
  | .bool => Bool
  | .four => Card4

def twoRes : Two → Type
  | .bool => Bool
  | .four => Card4 × Card4

def twoObs : (a : Two) → DiffObs (twoCar a) (twoRes a)
  | .bool => boolEqObs
  | .four => card4Obs

/-- One declared arrow at each object, none across. -/
def twoHom : Two → Two → Type
  | .bool, .bool => Unit
  | .four, .four => Unit
  | .bool, .four => Empty
  | .four, .bool => Empty

def twoIsoNeg : (a b : Two) → twoHom a b → PresIso (twoObs a) (twoObs b)
  | .bool, .bool, _ => negIso
  | .four, .four, _ => twIso
  | .bool, .four, e => Empty.elim e
  | .four, .bool, e => Empty.elim e

def twoFamilyNeg : HFamily where
  Obj := Two
  car := twoCar
  res := twoRes
  obs := twoObs
  Hom := twoHom
  iso := twoIsoNeg

/-- **Negative, heterogeneous, two objects.**  The negation
automorphism at the `Bool` object fixes no admissible pair, so the
whole family has no natural section — even though the `Card4`
component, taken alone, does. -/
theorem twoFamilyNeg_no_section :
    ¬ ∃ s : HSec twoFamilyNeg, HIsNatural twoFamilyNeg s :=
  no_natural_section_of_endo twoFamilyNeg .bool () negIso_fixed_point_free

def twoIsoPos : (a b : Two) → twoHom a b → PresIso (twoObs a) (twoObs b)
  | .bool, .bool, _ => PresIso.refl boolEqObs
  | .four, .four, _ => twIso
  | .bool, .four, e => Empty.elim e
  | .four, .bool, e => Empty.elim e

def twoFamilyPos : HFamily where
  Obj := Two
  car := twoCar
  res := twoRes
  obs := twoObs
  Hom := twoHom
  iso := twoIsoPos

def twoSectionPos : HSec twoFamilyPos
  | .bool => boolEqPair
  | .four => card4Pair

theorem twIso_fixes_card4Pair : twIso.mapPair card4Pair = card4Pair := by
  apply Subtype.ext
  rfl

/-- **Positive, heterogeneous, two objects.**  Replace the `Bool`
automorphism by the identity and keep the `Card4` transposition; both
declared arrows now fix an admissible pair, and the section picking
`(false, true)` and `(e3, e4)` is natural. -/
theorem twoFamilyPos_natural : HIsNatural twoFamilyPos twoSectionPos := by
  intro a b h
  match a, b with
  | .bool, .bool => exact mapPair_refl boolEqObs boolEqPair
  | .four, .four => exact twIso_fixes_card4Pair
  | .bool, .four => exact Empty.elim h
  | .four, .bool => exact Empty.elim h

theorem twoFamilyPos_has_section :
    ∃ s : HSec twoFamilyPos, HIsNatural twoFamilyPos s :=
  ⟨twoSectionPos, twoFamilyPos_natural⟩

/-- **The separation, over heterogeneous many-object families.**  Same
objects, same carriers, same residual types, same admissible pairs —
only the declared automorphism at one object differs, and that alone
decides whether a natural section exists. -/
theorem heterogeneous_naturality_separates :
    (∃ s : HSec twoFamilyPos, HIsNatural twoFamilyPos s) ∧
    ¬ ∃ s : HSec twoFamilyNeg, HIsNatural twoFamilyNeg s :=
  ⟨twoFamilyPos_has_section, twoFamilyNeg_no_section⟩

/-! ## 14. Non-claims for §11-§13

* `HFamily` still declares its arrows and assumes NOTHING about
  closure: no composition, no inverses, no identities.  `Hom a b` is a
  list of declared isomorphisms, not a hom-set of a category.  The
  coherence lemmas of §11 are about `mapPair` and `PresIso`, not about
  `HFamily`, and no categorical structure is claimed for either.
* The flat `Family` of §5 is RETAINED and is not superseded.
  `hAuto_iff_auto` bridges the two only at ONE object.  A general
  embedding of `Family` into `HFamily` is NOT proved and is OPEN.
* §13 exhibits two objects with no arrow between them.  Naturality
  under arrows that genuinely CROSS objects with different carriers is
  therefore not exercised by these fixtures, and remains OPEN.
* Nothing here derives `ContactKernel.no_equivariant_pair_valued_map`.
  That derivation is still OPEN, exactly as recorded in §10.
-/

end PresentationNaturality
