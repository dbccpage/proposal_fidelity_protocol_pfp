import Derivation.DiffInterface
import Derivation.Compression

/-!
# Observer descent: the quotient-descent layer over the native observer

The native `DiffInterface.DiffObs` already carries the typed difference
operation, the zero relation, its equivalence proof, and the quotient
(`ObsQuotient`) with the soundness half (`obsQuotient_eq_of_zero`).
This module completes that layer with the descent theory the quotient
earns, and nothing more:

1. **Exactness**: the quotient identifies *exactly* the zero-pairs
   (`obsQuotient_exact`, `obsQuotient_mk_eq_iff`), and every class is
   the class of a point (`obsQuotient_mk_surjective`) — the projection
   is epi by quotient induction, which is why every uniqueness
   statement below is global rather than image-scoped.
2. **Unary descent**: a view `f : X → Y` factors through the quotient
   iff it is constant on zero-classes (`ClassConstant`,
   `descend_exists_iff`), uniquely (`descend_unique`); a zero-pair on
   which the view disagrees blocks descent
   (`descend_blocked_of_witness`).
3. **Binary descent of the difference map itself** (`DeltaConstant`,
   `deltaDescend_exists_iff`, `deltaDescend_unique`,
   `deltaDescend_blocked_of_witness`).
4. **Pairing**: a pair view is compatible exactly componentwise
   (`classConstant_pair_iff`, `pair_descend_exists_iff`); a
   compatible view paired with a component that disagrees on a
   zero-pair descends alone and is blocked jointly
   (`view_descends_pair_blocked`).
5. **The mod-setoid layer, collapsed**: descent into a further
   quotient of the value side reduces to the equality layer at
   `Quotient.mk S ∘ f` (`classConstant_comp_mk_iff`), with the
   existence forms (`descendMod_exists_iff`,
   `deltaDescendMod_exists_iff`), coarsening transport (`coarsenMap`,
   `descendMod_exists_of_coarsen`), and the product setoid
   (`pairSetoid`, `pairSetoid_mk_eq_iff`).
6. **Tag realization**: a tag-augmented view observer is the native
   `kernelObs` of the view composed with the second projection
   (`tag_view_zeroRel`) — the tag component adds no observational
   content, definitionally.
7. **The integer tail**: the subtraction observer on `Int`
   (`intDiffObs`) with the one-line arithmetic lemmas that subsume
   value-difference reasoning, and the record that difference values
   carry orientation while the zero relation cannot
   (`value_orientation_survives`).
8. **The all-zero countermodel** (`collapseAllObs`): a two-point
   observer whose declared zero relation identifies everything while
   its difference map still separates — the difference map is not
   class-constant, so neither it nor the identity view descends
   (`collapseAllObs_not_deltaConstant`,
   `collapseAllObs_no_delta_descend`,
   `collapseAllObs_id_not_classConstant`,
   `collapseAllObs_no_view_descend`).  `Bool` is minimal — METATHEORY,
   not a Lean theorem: on a subsingleton every map is class-constant
   (`Subsingleton.elim`), so no descent obstruction can live there.
9. **The factorization dictionary**: global quotient descent for a
   kernel observer is exactly the native list-scoped factorization
   quantified over *every* represented domain
   (`classConstant_iff_fiberConstant_all`,
   `descend_iff_factorsOn_all`); at any one fixed domain the native
   notion is strictly weaker (`fiberConstant_fixed_D_not_classConstant`);
   the question-family form of the pairing law is signature splitting
   over list append (`sigEq_append_iff`).

Metatheory used (declared): types, functions, propositional logic,
the quotient machinery of the metalanguage (`Quotient.lift`,
`Quotient.lift₂`, `Quotient.sound`, `Quotient.exact`), function
extensionality, and linear integer arithmetic (`omega`).  No choice,
no excluded middle.
-/

namespace ObsDescent

open DiffInterface

variable {X R Y Z : Type}

/-! ## Exactness of the observer quotient -/

/-- The quotient identifies only zero-pairs: the exactness half,
converse to the sealed `obsQuotient_eq_of_zero`. -/
theorem obsQuotient_exact (O : DiffObs X R) {x y : X}
    (h : ObsQuotient.mk O x = ObsQuotient.mk O y) : ZeroRel O x y :=
  Quotient.exact h

/-- Classes are equal exactly on zero-pairs. -/
theorem obsQuotient_mk_eq_iff (O : DiffObs X R) (x y : X) :
    ObsQuotient.mk O x = ObsQuotient.mk O y ↔ ZeroRel O x y :=
  ⟨obsQuotient_exact O, obsQuotient_eq_of_zero O⟩

/-- Every class is the class of a point: the projection is epi, by
quotient induction.  This is the exact reason descent uniqueness in
this module is global where image-scoped presentation uniqueness is
not. -/
theorem obsQuotient_mk_surjective (O : DiffObs X R)
    (q : ObsQuotient O) : ∃ x, ObsQuotient.mk O x = q :=
  Quotient.inductionOn q fun x => ⟨x, rfl⟩

/-! ## Unary descent -/

/-- Compatibility of a view with the observer: constant on
zero-classes. -/
def ClassConstant (O : DiffObs X R) (f : X → Y) : Prop :=
  ∀ x y, ZeroRel O x y → f x = f y

/-- The descended view on the quotient. -/
def descend (O : DiffObs X R) (f : X → Y)
    (hf : ClassConstant O f) : ObsQuotient O → Y :=
  Quotient.lift f hf

/-- The descended view computes on classes. -/
theorem descend_mk (O : DiffObs X R) (f : X → Y)
    (hf : ClassConstant O f) (x : X) :
    descend O f hf (ObsQuotient.mk O x) = f x := rfl

/-- **Existence iff compatibility**: a view factors through the
quotient exactly when it is constant on zero-classes. -/
theorem descend_exists_iff (O : DiffObs X R) (f : X → Y) :
    (∃ F : ObsQuotient O → Y, ∀ x, F (ObsQuotient.mk O x) = f x) ↔
      ClassConstant O f := by
  constructor
  · intro h x y hxy
    obtain ⟨F, hF⟩ := h
    calc f x = F (ObsQuotient.mk O x) := (hF x).symm
      _ = F (ObsQuotient.mk O y) := by
            rw [obsQuotient_eq_of_zero O hxy]
      _ = f y := hF y
  · intro hf
    exact ⟨descend O f hf, fun _ => rfl⟩

/-- **Global uniqueness**: two factorizations agreeing on classes are
equal on the whole quotient, because the projection is epi. -/
theorem descend_unique (O : DiffObs X R) (f : X → Y)
    (F G : ObsQuotient O → Y)
    (hF : ∀ x, F (ObsQuotient.mk O x) = f x)
    (hG : ∀ x, G (ObsQuotient.mk O x) = f x) : F = G :=
  funext fun q =>
    Quotient.inductionOn q fun x => (hF x).trans (hG x).symm

/-- A zero-pair on which the view disagrees blocks descent. -/
theorem descend_blocked_of_witness (O : DiffObs X R) (f : X → Y)
    {x y : X} (hxy : ZeroRel O x y) (hne : f x ≠ f y) :
    ¬ ∃ F : ObsQuotient O → Y, ∀ z, F (ObsQuotient.mk O z) = f z :=
  fun h => hne ((descend_exists_iff O f).mp h x y hxy)

/-! ## Binary descent of the difference map -/

/-- Compatibility of the difference map with its own zero relation:
constant on zero-classes in both arguments. -/
def DeltaConstant (O : DiffObs X R) : Prop :=
  ∀ x x' y y', ZeroRel O x x' → ZeroRel O y y' →
    O.delta x y = O.delta x' y'

/-- The descended difference map on the quotient. -/
def deltaDescend (O : DiffObs X R) (h : DeltaConstant O) :
    ObsQuotient O → ObsQuotient O → R :=
  Quotient.lift₂ O.delta fun x y x' y' hx hy => h x x' y y' hx hy

/-- The descended difference map computes on classes. -/
theorem deltaDescend_mk (O : DiffObs X R) (h : DeltaConstant O)
    (x y : X) :
    deltaDescend O h (ObsQuotient.mk O x) (ObsQuotient.mk O y) =
      O.delta x y := rfl

/-- **Existence iff compatibility, binary form**: the difference map
factors through the quotient in both arguments exactly when it is
constant on zero-classes in both. -/
theorem deltaDescend_exists_iff (O : DiffObs X R) :
    (∃ F : ObsQuotient O → ObsQuotient O → R,
        ∀ x y, F (ObsQuotient.mk O x) (ObsQuotient.mk O y) =
          O.delta x y) ↔
      DeltaConstant O := by
  constructor
  · intro h x x' y y' hx hy
    obtain ⟨F, hF⟩ := h
    calc O.delta x y
        = F (ObsQuotient.mk O x) (ObsQuotient.mk O y) :=
          (hF x y).symm
      _ = F (ObsQuotient.mk O x') (ObsQuotient.mk O y') := by
            rw [obsQuotient_eq_of_zero O hx,
                obsQuotient_eq_of_zero O hy]
      _ = O.delta x' y' := hF x' y'
  · intro h
    exact ⟨deltaDescend O h, fun _ _ => rfl⟩

/-- Symmetric two-map uniqueness for the descended difference map. -/
theorem deltaDescend_unique (O : DiffObs X R)
    (F G : ObsQuotient O → ObsQuotient O → R)
    (hF : ∀ x y, F (ObsQuotient.mk O x) (ObsQuotient.mk O y) =
      O.delta x y)
    (hG : ∀ x y, G (ObsQuotient.mk O x) (ObsQuotient.mk O y) =
      O.delta x y) : F = G :=
  funext fun q₁ => funext fun q₂ =>
    Quotient.inductionOn₂ q₁ q₂ fun x y =>
      (hF x y).trans (hG x y).symm

/-- A pair of zero-pairs on which the difference values disagree
blocks descent of the difference map. -/
theorem deltaDescend_blocked_of_witness (O : DiffObs X R)
    {x x' y y' : X} (hx : ZeroRel O x x') (hy : ZeroRel O y y')
    (hne : O.delta x y ≠ O.delta x' y') :
    ¬ ∃ F : ObsQuotient O → ObsQuotient O → R,
        ∀ x y, F (ObsQuotient.mk O x) (ObsQuotient.mk O y) =
          O.delta x y :=
  fun h => hne ((deltaDescend_exists_iff O).mp h x x' y y' hx hy)

/-! ## Pairing and the flagship obstruction -/

/-- A pair view is class-constant exactly when both components
are. -/
theorem classConstant_pair_iff (O : DiffObs X R) (f : X → Y)
    (g : X → Z) :
    ClassConstant O (fun x => (f x, g x)) ↔
      ClassConstant O f ∧ ClassConstant O g := by
  constructor
  · intro h
    exact ⟨fun x y hxy => congrArg Prod.fst (h x y hxy),
           fun x y hxy => congrArg Prod.snd (h x y hxy)⟩
  · intro h x y hxy
    show (f x, g x) = (f y, g y)
    rw [h.1 x y hxy, h.2 x y hxy]

/-- The pair view descends exactly when both components descend. -/
theorem pair_descend_exists_iff (O : DiffObs X R) (f : X → Y)
    (g : X → Z) :
    (∃ F : ObsQuotient O → Y × Z,
        ∀ x, F (ObsQuotient.mk O x) = (f x, g x)) ↔
      (∃ Fy : ObsQuotient O → Y,
          ∀ x, Fy (ObsQuotient.mk O x) = f x) ∧
        (∃ Fz : ObsQuotient O → Z,
            ∀ x, Fz (ObsQuotient.mk O x) = g x) := by
  constructor
  · intro h
    have hc := (classConstant_pair_iff O f g).mp
      ((descend_exists_iff O fun x => (f x, g x)).mp h)
    exact ⟨(descend_exists_iff O f).mpr hc.1,
           (descend_exists_iff O g).mpr hc.2⟩
  · intro h
    exact (descend_exists_iff O fun x => (f x, g x)).mpr
      ((classConstant_pair_iff O f g).mpr
        ⟨(descend_exists_iff O f).mp h.1,
         (descend_exists_iff O g).mp h.2⟩)

/-- **The flagship obstruction, in witness form**: a class-constant
view descends alone, while pairing it with a component that disagrees
on a zero-pair blocks the joint descent. -/
theorem view_descends_pair_blocked (O : DiffObs X R) (f : X → Y)
    (g : X → Z) (hf : ClassConstant O f) {x y : X}
    (hxy : ZeroRel O x y) (hg : g x ≠ g y) :
    (∃ F : ObsQuotient O → Y, ∀ z, F (ObsQuotient.mk O z) = f z) ∧
      ¬ ∃ F : ObsQuotient O → Y × Z,
          ∀ z, F (ObsQuotient.mk O z) = (f z, g z) :=
  ⟨(descend_exists_iff O f).mpr hf,
   descend_blocked_of_witness O (fun z => (f z, g z)) hxy
     fun he => hg (congrArg Prod.snd he)⟩

/-! ## The mod-setoid layer, collapsed to the equality layer -/

/-- Transport along a coarsening of setoids on the value side. -/
def coarsenMap (S T : Setoid Y)
    (h : ∀ a b, S.r a b → T.r a b) : Quotient S → Quotient T :=
  Quotient.lift (fun a => Quotient.mk T a)
    fun a b hab => Quotient.sound (h a b hab)

/-- The coarsening transport computes on classes. -/
theorem coarsenMap_mk (S T : Setoid Y)
    (h : ∀ a b, S.r a b → T.r a b) (a : Y) :
    coarsenMap S T h (Quotient.mk S a) = Quotient.mk T a := rfl

/-- **The key reduction**: a view into a value quotient is
class-constant exactly when the underlying view is compatible up to
the value setoid.  Every mod-setoid descent statement is the
corresponding equality-layer statement at `Quotient.mk S ∘ f`,
through this lemma. -/
theorem classConstant_comp_mk_iff (O : DiffObs X R) (f : X → Y)
    (S : Setoid Y) :
    ClassConstant O (fun x => Quotient.mk S (f x)) ↔
      ∀ x y, ZeroRel O x y → S.r (f x) (f y) :=
  ⟨fun h x y hxy => Quotient.exact (h x y hxy),
   fun h x y hxy => Quotient.sound (h x y hxy)⟩

/-- Existence form of mod-setoid descent for views. -/
theorem descendMod_exists_iff (O : DiffObs X R) (f : X → Y)
    (S : Setoid Y) :
    (∃ F : ObsQuotient O → Quotient S,
        ∀ x, F (ObsQuotient.mk O x) = Quotient.mk S (f x)) ↔
      ∀ x y, ZeroRel O x y → S.r (f x) (f y) :=
  (descend_exists_iff O fun x => Quotient.mk S (f x)).trans
    (classConstant_comp_mk_iff O f S)

/-- Existence form of mod-setoid descent for the difference map. -/
theorem deltaDescendMod_exists_iff (O : DiffObs X R) (S : Setoid R) :
    (∃ F : ObsQuotient O → ObsQuotient O → Quotient S,
        ∀ x y, F (ObsQuotient.mk O x) (ObsQuotient.mk O y) =
          Quotient.mk S (O.delta x y)) ↔
      ∀ x x' y y', ZeroRel O x x' → ZeroRel O y y' →
        S.r (O.delta x y) (O.delta x' y') := by
  constructor
  · intro h x x' y y' hx hy
    obtain ⟨F, hF⟩ := h
    have he : Quotient.mk S (O.delta x y) =
        Quotient.mk S (O.delta x' y') := by
      calc Quotient.mk S (O.delta x y)
          = F (ObsQuotient.mk O x) (ObsQuotient.mk O y) :=
            (hF x y).symm
        _ = F (ObsQuotient.mk O x') (ObsQuotient.mk O y') := by
              rw [obsQuotient_eq_of_zero O hx,
                  obsQuotient_eq_of_zero O hy]
        _ = Quotient.mk S (O.delta x' y') := hF x' y'
    exact Quotient.exact he
  · intro h
    exact ⟨Quotient.lift₂ (fun x y => Quotient.mk S (O.delta x y))
        (fun x y x' y' hx hy => Quotient.sound (h x x' y y' hx hy)),
      fun _ _ => rfl⟩

/-- The product setoid on a pair of value types. -/
def pairSetoid (S : Setoid Y) (T : Setoid Z) : Setoid (Y × Z) where
  r p q := S.r p.1 q.1 ∧ T.r p.2 q.2
  iseqv :=
    { refl := fun p => ⟨S.iseqv.refl p.1, T.iseqv.refl p.2⟩
      symm := fun h => ⟨S.iseqv.symm h.1, T.iseqv.symm h.2⟩
      trans := fun h1 h2 =>
        ⟨S.iseqv.trans h1.1 h2.1, T.iseqv.trans h1.2 h2.2⟩ }

/-- Product-setoid classes are equal exactly componentwise. -/
theorem pairSetoid_mk_eq_iff (S : Setoid Y) (T : Setoid Z)
    (p q : Y × Z) :
    Quotient.mk (pairSetoid S T) p = Quotient.mk (pairSetoid S T) q ↔
      S.r p.1 q.1 ∧ T.r p.2 q.2 :=
  ⟨fun h => Quotient.exact h, fun h => Quotient.sound h⟩

/-- Mod-setoid descent transports along value-side coarsening. -/
theorem descendMod_exists_of_coarsen (O : DiffObs X R) (f : X → Y)
    (S T : Setoid Y) (h : ∀ a b, S.r a b → T.r a b) :
    (∃ F : ObsQuotient O → Quotient S,
        ∀ x, F (ObsQuotient.mk O x) = Quotient.mk S (f x)) →
      ∃ F : ObsQuotient O → Quotient T,
        ∀ x, F (ObsQuotient.mk O x) = Quotient.mk T (f x) :=
  fun ⟨F, hF⟩ =>
    ⟨fun q => coarsenMap S T h (F q),
     fun x => (congrArg (coarsenMap S T h) (hF x)).trans
       (coarsenMap_mk S T h (f x))⟩

/-! ## Tag-augmented views are kernel observers -/

/-- A tag-augmented view observer is the native `kernelObs` of the
view composed with the second projection: the tag component adds no
observational content, definitionally. -/
theorem tag_view_zeroRel {K X G : Type} (φ : X → G) (s t : K × X) :
    ZeroRel (kernelObs fun p : K × X => φ p.2) s t ↔
      φ s.2 = φ t.2 := Iff.rfl

/-! ## The integer subtraction observer and its tail -/

/-- The subtraction observer on the integers: difference is
subtraction, zero is the literal zero, and the three law fields are
proved (not admitted) by linear arithmetic. -/
def intDiffObs : DiffObs Int Int where
  delta a b := a - b
  Zero v := v = 0
  zero_refl x := by show x - x = 0; omega
  zero_symm := fun {x y} h => by
    have h' : x - y = 0 := h
    show y - x = 0
    omega
  zero_trans := fun {x y z} h1 h2 => by
    have h1' : x - y = 0 := h1
    have h2' : y - z = 0 := h2
    show x - z = 0
    omega

/-- Its zero relation is equality. -/
theorem intDiffObs_zeroRel (a b : Int) :
    ZeroRel intDiffObs a b ↔ a = b := by
  show a - b = 0 ↔ a = b
  constructor
  · intro h
    omega
  · intro h
    omega

/-- Nonzero subtraction is exactly value inequality: the one-line
subsumption lemma for inequality tails on the integers. -/
theorem int_sub_ne_zero_iff (a b : Int) : a - b ≠ 0 ↔ a ≠ b := by
  constructor
  · intro h he
    omega
  · intro h he
    omega

/-- Strict order gives nonzero subtraction. -/
theorem int_sub_ne_zero_of_gt (a b : Int) (h : b < a) : a - b ≠ 0 := by
  omega

/-- Shift cancellation: a common summand drops out of the
difference. -/
theorem int_shift_cancel (a c b : Int) :
    (a + c + 2 * b) - (a + c) = 2 * b := by
  omega

/-- Doubling detects zero on the integers. -/
theorem int_two_mul_eq_zero_iff (b : Int) : 2 * b = 0 ↔ b = 0 := by
  constructor
  · intro h
    omega
  · intro h
    omega

/-- Additive cancellation of a declared shift. -/
theorem int_add_sub_cancel (s d : Int) : (s + d) - s = d := by
  omega

/-- Difference values carry orientation; the zero relation cannot:
the two ordered difference values at a distinct pair differ, while
the zero relation holds of neither order and so agrees on both. -/
theorem value_orientation_survives :
    intDiffObs.delta 0 1 ≠ intDiffObs.delta 1 0 ∧
      (ZeroRel intDiffObs 0 1 ↔ ZeroRel intDiffObs 1 0) := by
  constructor
  · show (0 : Int) - 1 ≠ 1 - 0
    omega
  · show ((0 : Int) - 1 = 0) ↔ ((1 : Int) - 0 = 0)
    constructor
    · intro h
      omega
    · intro h
      omega

/-! ## The all-zero countermodel -/

/-- The all-zero observer on `Bool`: the difference map is the first
projection — it still separates the two points — while the declared
zero predicate accepts every value.  This is the observer incarnation
of the native quotient barrier: total collapse with surviving
value-level difference. -/
def collapseAllObs : DiffObs Bool Bool where
  delta x _ := x
  Zero _ := True
  zero_refl _ := trivial
  zero_symm _ := trivial
  zero_trans _ _ := trivial

/-- Every pair is a zero-pair: the quotient has a single class. -/
theorem collapseAllObs_all_zero :
    ∀ a b : Bool, ZeroRel collapseAllObs a b :=
  fun _ _ => trivial

/-- The difference map is not constant on zero-classes: the declared
zero relation destroys the compatibility of its own difference
map. -/
theorem collapseAllObs_not_deltaConstant :
    ¬ DeltaConstant collapseAllObs :=
  fun h => Bool.noConfusion (h true false true false trivial trivial)

/-- Hence the difference map does not descend to the quotient: the
value-level structure survives no total collapse. -/
theorem collapseAllObs_no_delta_descend :
    ¬ ∃ F : ObsQuotient collapseAllObs →
        ObsQuotient collapseAllObs → Bool,
        ∀ x y, F (ObsQuotient.mk collapseAllObs x)
          (ObsQuotient.mk collapseAllObs y) =
            collapseAllObs.delta x y :=
  fun h => collapseAllObs_not_deltaConstant
    ((deltaDescend_exists_iff collapseAllObs).mp h)

/-- The identity view is not class-constant over the total
collapse. -/
theorem collapseAllObs_id_not_classConstant :
    ¬ ClassConstant collapseAllObs (fun x => x) :=
  fun h => Bool.noConfusion (h true false trivial)

/-- Hence no factorization of the identity view exists: nothing on
the one-class quotient recovers the two points.  The carrier is
minimal — on a subsingleton carrier every view is class-constant. -/
theorem collapseAllObs_no_view_descend :
    ¬ ∃ F : ObsQuotient collapseAllObs → Bool,
        ∀ x, F (ObsQuotient.mk collapseAllObs x) = x :=
  fun h => collapseAllObs_id_not_classConstant
    ((descend_exists_iff collapseAllObs fun x => x).mp h)

/-! ## The factorization dictionary with target-relative compression

The native `Compression` layer factors questions through
presentations on a *represented* finite domain `D : List Nat`; the
quotient-descent layer above factors views through the observer
quotient *globally*.  The dictionary: for a kernel observer, global
descent is exactly factorization over every represented domain — the
same third notion, priced once by `Quot.sound` gluing and once by
representedness with first-match selection. -/

/-- Class-constancy for a kernel observer is fiber-constancy over
every represented domain. -/
theorem classConstant_iff_fiberConstant_all (p q : Nat → Nat) :
    ClassConstant (kernelObs p) q ↔
      ∀ D : List Nat, Compression.FiberConstant D p q := by
  constructor
  · intro h D x _ x' _ hp
    exact h x x' hp
  · intro h x y hp
    exact h [x, y] x List.mem_cons_self y
      (List.mem_cons_of_mem x List.mem_cons_self) hp

/-- **The dictionary headline**: a view descends to the observer
quotient of a kernel observer exactly when it factors through the
presentation on every represented domain. -/
theorem descend_iff_factorsOn_all (p q : Nat → Nat) :
    (∃ F : ObsQuotient (kernelObs p) → Nat,
        ∀ x, F (ObsQuotient.mk (kernelObs p) x) = q x) ↔
      ∀ D : List Nat, Compression.FactorsOn D p q :=
  (descend_exists_iff (kernelObs p) q).trans
    ((classConstant_iff_fiberConstant_all p q).trans
      ⟨fun h D => (Compression.factors_iff_fiberConstant D p q).mpr
          (h D),
       fun h D => (Compression.factors_iff_fiberConstant D p q).mp
          (h D)⟩)

/-- At a fixed represented domain the native notion is strictly
weaker: over the empty domain every question is vacuously
fiber-constant, while the identity view over the constant
presentation is not class-constant.  The `∀ D` quantifier in the
dictionary is not removable. -/
theorem fiberConstant_fixed_D_not_classConstant :
    Compression.FiberConstant [] (fun _ => 0) (fun x => x) ∧
      ¬ ClassConstant (kernelObs fun _ : Nat => 0) (fun x => x) :=
  ⟨fun _ hx => (nomatch hx),
   fun h => absurd (h 0 1 rfl) (by decide)⟩

/-- The question-family form of the pairing law: signature equality
over an appended family splits componentwise, exactly as pair descent
splits into component descents. -/
theorem sigEq_append_iff (Q₁ Q₂ : List (Nat → Nat)) (x x' : Nat) :
    Compression.SigEq (Q₁ ++ Q₂) x x' ↔
      Compression.SigEq Q₁ x x' ∧ Compression.SigEq Q₂ x x' :=
  ⟨fun h => ⟨fun s hs => h s (List.mem_append.mpr (Or.inl hs)),
     fun s hs => h s (List.mem_append.mpr (Or.inr hs))⟩,
   fun h s hs => (List.mem_append.mp hs).elim (h.1 s) (h.2 s)⟩

end ObsDescent
