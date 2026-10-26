import Derivation.PrimDiff

/-!
# Categories of primitive difference

The morphism-level continuation of `PrimDiff`.  Objects are *pointed
witnessed relations*: a carrier, one binary relation, two designated
points, and one asserted edge between them.  Morphisms preserve the
points and the relation.  This module proves which of the two-element
candidates (`D2`, `S2`) are initial, in which subcategory, and exactly
how uniqueness fails (only up to isomorphism, never up to presentation
identity); it then studies the faithful-presentation categories of a
three-point and a two-point source, where a branching non-uniqueness
appears exactly when a third occurrence exists.

Metatheory used (declared): structures, functions, propositional
logic, finite case analysis, function extensionality, and definitional
proof irrelevance.  No quotient machinery, no choice or
preimage-selection principle anywhere (one scoped obstruction is
recorded as an explicit OPEN cell instead).

Distinctions maintained: presentation identity (`two_initials_not_identical`),
internal identity of morphisms (`hom_ext`), and isomorphism
(`initials_iso`) are separate throughout; absence of a morphism is
proved positively (`s2_no_hom_to_d2`, `no_phom_mergeA_mergeB`), never
inferred from absence of a construction.
-/

namespace PrimitiveCats

/-! ## Objects and morphisms -/

/-- A pointed witnessed relation: carrier `X`, relation `r`, designated
points `a`, `b`, and one asserted edge `w : r a b`.  This is exactly the
data a `PrimDiff` A1-structure supplies, packaged as an object. -/
structure PtdRel where
  X : Type
  r : X → X → Prop
  a : X
  b : X
  w : r a b

/-- A morphism of pointed witnessed relations: a carrier map preserving
both designated points and the relation. -/
structure Hom (P Q : PtdRel) where
  f : P.X → Q.X
  ha : f P.a = Q.a
  hb : f P.b = Q.b
  hr : ∀ x y, P.r x y → Q.r (f x) (f y)

/-- Internal identity of morphisms is determined by the carrier map:
the three remaining fields are propositions (definitional proof
irrelevance). -/
theorem hom_ext {P Q : PtdRel} {h1 h2 : Hom P Q} (h : h1.f = h2.f) :
    h1 = h2 := by
  cases h1 with
  | mk f1 ha1 hb1 hr1 =>
    cases h2 with
    | mk f2 ha2 hb2 hr2 =>
      have h' : f1 = f2 := h
      subst h'
      rfl

/-- Identity morphism. -/
def idH (P : PtdRel) : Hom P P :=
  ⟨fun x => x, rfl, rfl, fun _ _ hxy => hxy⟩

/-- Composition (`g` after `h`). -/
def comp {P Q R : PtdRel} (g : Hom Q R) (h : Hom P Q) : Hom P R :=
  ⟨fun x => g.f (h.f x),
   (congrArg g.f h.ha).trans g.ha,
   (congrArg g.f h.hb).trans g.hb,
   fun x y hxy => g.hr _ _ (h.hr x y hxy)⟩

theorem comp_id {P Q : PtdRel} (h : Hom P Q) : comp h (idH P) = h :=
  hom_ext rfl

theorem id_comp {P Q : PtdRel} (h : Hom P Q) : comp (idH Q) h = h :=
  hom_ext rfl

theorem comp_assoc {P Q R S : PtdRel} (k : Hom R S) (g : Hom Q R)
    (h : Hom P Q) : comp (comp k g) h = comp k (comp g h) :=
  hom_ext rfl

/-- Membership predicate for the full subcategory of irreflexive
objects (morphisms unchanged). -/
def IrreflObj (P : PtdRel) : Prop := PrimDiff.Irrefl P.r

/-- Membership predicate for the full subcategory of symmetric objects
(morphisms unchanged). -/
def SymObj (P : PtdRel) : Prop := ∀ x y, P.r x y → P.r y x

/-! ## The two-element objects -/

/-- The oriented two-element object: carrier `Bool`, relation `D2`,
points `false`, `true`, edge `D2 false true`. -/
def d2Obj : PtdRel :=
  ⟨Bool, PrimDiff.D2, false, true, PrimDiff.D2_witness⟩

/-- The symmetric two-element object: same carrier and points, relation
`S2`. -/
def s2Obj : PtdRel :=
  ⟨Bool, PrimDiff.S2, false, true, Or.inl PrimDiff.D2_witness⟩

/-- The oriented two-element object with the opposite pointing: the
edge runs `true → false` and the designated points follow it.  As a
presentation it differs from `d2Obj`; as an object of the category it
is initial for the same reason (`d2Swap_initial`). -/
def d2SwapObj : PtdRel :=
  ⟨Bool, fun x y => x = true ∧ y = false, true, false, ⟨rfl, rfl⟩⟩

theorem d2Obj_irrefl : IrreflObj d2Obj := PrimDiff.D2_irrefl

theorem s2Obj_irrefl : IrreflObj s2Obj := PrimDiff.S2_irrefl

theorem s2Obj_sym : SymObj s2Obj := by
  intro x y h
  cases h with
  | inl h => exact Or.inr h
  | inr h => exact Or.inl h

/-- `d2Obj` is not a symmetric object: its initiality result cannot even
be *stated* inside the symmetric subcategory, because membership fails. -/
theorem d2_not_obj_sym : ¬ SymObj d2Obj := by
  intro h
  have h2 : PrimDiff.D2 true false := h false true PrimDiff.D2_witness
  exact Bool.noConfusion h2.1

/-! ## Initiality -/

/-- Initiality: exactly one morphism to every object. -/
def Initial (R : PtdRel) : Prop :=
  ∀ T : PtdRel, ∃ h : Hom R T, ∀ h' : Hom R T, h' = h

/-- Weak initiality: at least one morphism to every object. -/
def WeaklyInitial (R : PtdRel) : Prop :=
  ∀ T : PtdRel, Nonempty (Hom R T)

theorem weaklyInitial_of_initial {R : PtdRel} (h : Initial R) :
    WeaklyInitial R :=
  fun T => (h T).elim fun u _ => ⟨u⟩

/-- `d2Obj` is initial in the category of ALL pointed witnessed
relations: the map sends `false ↦ T.a`, `true ↦ T.b`; the only edge is
the witnessed one, so edge preservation needs only `T.w`; uniqueness is
by `ha`/`hb`, since `Bool` is exhausted by the two designated points.
Scope note (review pass): `PtdRel` requires NO irreflexivity, so this
universal property characterizes the bare-witness reading (candidate
W of `PrimitiveCore`) — the free pointed object on one witnessed
arrow.  Initiality restricts to the irreflexive subcategory
(`d2_initial_irrefl`) but does not itself select irreflexivity; the
separate, independent reason for preferring candidate A is
`PrimitiveCore.imp_a_d` (A forces distinct endpoints) against
`PrimitiveCore.nimp_w_d` (W does not).  The two arguments are not to
be merged. -/
theorem d2_initial : Initial d2Obj := by
  intro T
  refine ⟨⟨fun t => cond t T.b T.a, rfl, rfl, ?_⟩, ?_⟩
  · intro x y hxy
    have hx : x = false := hxy.1
    have hy : y = true := hxy.2
    subst hx; subst hy
    exact T.w
  · intro h'
    apply hom_ext
    funext t
    cases t with
    | false => exact h'.ha
    | true => exact h'.hb

/-- The same statement restricted to irreflexive targets: `d2Obj` is
initial in the irreflexive full subcategory.  Immediate corollary of
`d2_initial`; stated separately so the subcategory claim is explicit. -/
theorem d2_initial_irrefl (P : PtdRel) (_ : IrreflObj P) :
    ∃ h : Hom d2Obj P, ∀ h' : Hom d2Obj P, h' = h :=
  d2_initial P

/-- **The unique map out of `d2Obj` is injective into every
irreflexive pointed witnessed presentation**: the designated images
are forced apart by the target's own witness and irreflexivity
(`PrimDiff.irrefl_witness_ne`), and `Bool` has no other points.  For
a general (non-irreflexive) target injectivity can fail — the
one-point self-difference receives the collapsing map — so this is
exactly where irreflexivity is spent on the morphism side. -/
theorem d2_map_injective (P : PtdRel) (hP : IrreflObj P)
    (h : Hom d2Obj P) :
    ∀ x y : Bool, h.f x = h.f y → x = y := by
  have hne : P.a ≠ P.b := PrimDiff.irrefl_witness_ne hP P.w
  intro x y hxy
  cases x <;> cases y
  · rfl
  · exact absurd ((h.ha.symm.trans hxy).trans h.hb) hne
  · exact absurd ((h.hb.symm.trans hxy).trans h.ha) (fun e => hne e.symm)
  · rfl

/-- The injectivity hypothesis is not removable: into the one-point
self-difference target the unique map collapses the two points. -/
theorem d2_map_not_injective_without_irrefl :
    ∃ (P : PtdRel) (h : Hom d2Obj P) (x y : Bool),
      h.f x = h.f y ∧ x ≠ y := by
  refine ⟨⟨Unit, fun _ _ => True, (), (), trivial⟩,
    ⟨fun _ => (), rfl, rfl, fun _ _ _ => trivial⟩,
    false, true, rfl, by decide⟩

/-- `s2Obj` is initial in the symmetric full subcategory: the oriented
half of the edge maps to `T.w`, the reversed half to its image under
the symmetry of the target — which is exactly where the hypothesis
`SymObj T` is spent. -/
theorem s2_initial_sym (T : PtdRel) (hsym : SymObj T) :
    ∃ h : Hom s2Obj T, ∀ h' : Hom s2Obj T, h' = h := by
  refine ⟨⟨fun t => cond t T.b T.a, rfl, rfl, ?_⟩, ?_⟩
  · intro x y hxy
    cases hxy with
    | inl h =>
      have hx : x = false := h.1
      have hy : y = true := h.2
      subst hx; subst hy
      exact T.w
    | inr h =>
      have hy : y = false := h.1
      have hx : x = true := h.2
      subst hx; subst hy
      exact hsym _ _ T.w
  · intro h'
    apply hom_ext
    funext t
    cases t with
    | false => exact h'.ha
    | true => exact h'.hb

/-- There is no morphism from `s2Obj` to `d2Obj`: the reversed half of
the symmetric edge would have to map to a `D2`-edge from `true`'s image
to `false`'s image, forcing `f true = false` against `hb`. -/
theorem s2_no_hom_to_d2 : ¬ Nonempty (Hom s2Obj d2Obj) := by
  intro ⟨h⟩
  have hrev : s2Obj.r true false := Or.inr PrimDiff.D2_witness
  have hedge := h.hr true false hrev
  have h1 : h.f true = false := hedge.1
  have h2 : h.f true = true := h.hb
  rw [h1] at h2
  exact Bool.noConfusion h2

/-- Hence `s2Obj` is not weakly initial in the full category: its
initiality (`s2_initial_sym`) is strictly a subcategory phenomenon. -/
theorem s2_not_weakly_initial : ¬ WeaklyInitial s2Obj :=
  fun h => s2_no_hom_to_d2 (h d2Obj)

theorem s2_not_initial : ¬ Initial s2Obj :=
  fun h => s2_not_weakly_initial (weaklyInitial_of_initial h)

/-! ## Initiality transfers only up to isomorphism -/

/-- The oppositely pointed oriented object is initial in the full
category too — same proof shape as `d2_initial` with the roles of the
two points exchanged. -/
theorem d2Swap_initial : Initial d2SwapObj := by
  intro T
  refine ⟨⟨fun t => cond t T.a T.b, rfl, rfl, ?_⟩, ?_⟩
  · intro x y hxy
    have hx : x = true := hxy.1
    have hy : y = false := hxy.2
    subst hx; subst hy
    exact T.w
  · intro h'
    apply hom_ext
    funext t
    cases t with
    | false => exact h'.hb
    | true => exact h'.ha

/-- Two initial objects that are NOT identical as presentations: the
carriers are literally the same `Bool`, but the designated points
differ (`false` versus `true` in the `a` slot).  Initiality therefore
cannot single out one presentation. -/
theorem two_initials_not_identical : d2Obj ≠ d2SwapObj := by
  intro h
  have h2 : HEq d2Obj.a d2SwapObj.a := by rw [h]
  have h3 : (false : Bool) = true := eq_of_heq h2
  exact Bool.noConfusion h3

/-- Any two initial objects are isomorphic: the unique morphisms in
both directions compose to the unique endomorphism, which is the
identity.  Together with `two_initials_not_identical` this fixes the
exact strength of the uniqueness: up to isomorphism, not up to
presentation identity. -/
theorem initials_iso (P Q : PtdRel) (hP : Initial P) (hQ : Initial Q) :
    ∃ (u : Hom P Q) (v : Hom Q P),
      comp v u = idH P ∧ comp u v = idH Q := by
  obtain ⟨u, _⟩ := hP Q
  obtain ⟨v, _⟩ := hQ P
  obtain ⟨iP, hiP⟩ := hP P
  obtain ⟨iQ, hiQ⟩ := hQ Q
  exact ⟨u, v, (hiP (comp v u)).trans (hiP (idH P)).symm,
    (hiQ (comp u v)).trans (hiQ (idH Q)).symm⟩

/-! ## Initiality versus minimum cardinality -/

/-- A witnessed irreflexive object exists on every carrier
`Fin (n + 2)` (the morphism-level restatement of
`PrimDiff.witnessed_irrefl_on_every_larger_carrier`): being an object
of the (irreflexive) category does not bound the carrier. -/
def wideObj (n : Nat) : PtdRel :=
  ⟨Fin (n + 2),
   fun x y => x = ⟨0, by omega⟩ ∧ y = ⟨1, by omega⟩,
   ⟨0, by omega⟩, ⟨1, by omega⟩, ⟨rfl, rfl⟩⟩

theorem wideObj_irrefl (n : Nat) : IrreflObj (wideObj n) := by
  intro x hx
  have h : (⟨0, by omega⟩ : Fin (n + 2)) = ⟨1, by omega⟩ :=
    hx.1.symm.trans hx.2
  have hval : (0 : Nat) = 1 := congrArg Fin.val h
  omega

theorem ptd_on_every_larger_carrier (n : Nat) :
    ∃ P : PtdRel, P.X = Fin (n + 2) ∧ IrreflObj P :=
  ⟨wideObj n, rfl, wideObj_irrefl n⟩

/-- A three-or-more-point object: one edge `0 → 1`, the point with
index `2` unconstrained. -/
def bigObj (n : Nat) : PtdRel :=
  ⟨Fin (n + 3),
   fun x y => x = ⟨0, by omega⟩ ∧ y = ⟨1, by omega⟩,
   ⟨0, by omega⟩, ⟨1, by omega⟩, ⟨rfl, rfl⟩⟩

/-- First morphism `bigObj n → d2Obj`: the free third point goes to
`false`. -/
def bigHomA (n : Nat) : Hom (bigObj n) d2Obj :=
  ⟨fun x => x.val == 1, rfl, rfl, by
    intro x y hxy
    rw [hxy.1, hxy.2]
    exact PrimDiff.D2_witness⟩

/-- Second morphism `bigObj n → d2Obj`: the free third point goes to
`true`.  Both points and the single edge are preserved either way. -/
def bigHomB (n : Nat) : Hom (bigObj n) d2Obj :=
  ⟨fun x => !(x.val == 0), rfl, rfl, by
    intro x y hxy
    rw [hxy.1, hxy.2]
    exact PrimDiff.D2_witness⟩

theorem bigHomA_ne_bigHomB (n : Nat) : bigHomA n ≠ bigHomB n := by
  intro h
  have h2 := congrArg
    (fun k : Hom (bigObj n) d2Obj => k.f ⟨2, by omega⟩) h
  have h3 : (false : Bool) = true := h2
  exact Bool.noConfusion h3

/-- No carrier with a third point is initial: the third point can be
sent to either value of `d2Obj`, producing two distinct morphisms to
the same target, against uniqueness.  Initiality and minimum
cardinality are therefore distinct properties: `wideObj`/`bigObj` are
objects of every size, but only the two-point pointings are initial. -/
theorem larger_not_initial (n : Nat) : ¬ Initial (bigObj n) := by
  intro hinit
  obtain ⟨u, huniq⟩ := hinit d2Obj
  exact bigHomA_ne_bigHomB n
    ((huniq (bigHomA n)).trans (huniq (bigHomB n)).symm)

/-! ## The orientation fork at the automorphism level

Conclusion recorded here: orientation data lives in the *pointing*.
The swap symmetry of `S2` exists only unpointed
(`s2_swap_isRelAuto`); as soon as the two points are designated, both
`d2Obj` and `s2Obj` are rigid (`pointed_rigid`).  Neither branch is
prior — the oriented and the symmetric two-element objects are both
retained, each initial in its own regime (`d2_initial`,
`s2_initial_sym`), with the fork visible only at the unpointed
automorphism level. -/

/-- Bijectivity of an endofunction on `Bool`, spelled out (injective
and surjective); declared here because the ambient metatheory is plain
core. -/
def BoolBijective (f : Bool → Bool) : Prop :=
  (∀ x y, f x = f y → x = y) ∧ ∀ z, ∃ x, f x = z

/-- An unpointed relational automorphism on `Bool`: a bijective
endofunction preserving and reflecting the relation. -/
def IsRelAuto (r : Bool → Bool → Prop) (f : Bool → Bool) : Prop :=
  BoolBijective f ∧ ∀ x y, r x y ↔ r (f x) (f y)

/-- Unpointed rigidity of the oriented relation: any endofunction
preserving and reflecting `D2` fixes both elements (restatement of
`PrimDiff.oriented_rigid`). -/
theorem d2_autos (f : Bool → Bool)
    (hiff : ∀ x y, PrimDiff.D2 x y ↔ PrimDiff.D2 (f x) (f y)) :
    f false = false ∧ f true = true :=
  ⟨PrimDiff.oriented_rigid f hiff false,
   PrimDiff.oriented_rigid f hiff true⟩

/-- The swap preserves and reflects `S2` (reused from `PrimDiff`). -/
theorem s2_swap_auto :
    ∀ x y, PrimDiff.S2 x y ↔ PrimDiff.S2 (Bool.not x) (Bool.not y) :=
  PrimDiff.swap_is_S2_automorphism

/-- The identity preserves and reflects `S2`. -/
theorem s2_id_auto :
    ∀ x y, PrimDiff.S2 x y ↔ PrimDiff.S2 (id x) (id y) :=
  fun _ _ => Iff.rfl

theorem not_bijective : BoolBijective Bool.not := by
  constructor
  · intro a b h
    have h2 := congrArg Bool.not h
    rw [Bool.not_not, Bool.not_not] at h2
    exact h2
  · intro b
    exact ⟨Bool.not b, Bool.not_not b⟩

/-- The swap is an unpointed relational automorphism of `S2`. -/
theorem s2_swap_isRelAuto : IsRelAuto PrimDiff.S2 Bool.not :=
  ⟨not_bijective, PrimDiff.swap_is_S2_automorphism⟩

/-- The swap does not preserve/reflect `D2`. -/
theorem not_not_d2_auto :
    ¬ ∀ x y, PrimDiff.D2 x y ↔ PrimDiff.D2 (Bool.not x) (Bool.not y) := by
  decide

/-- Hence the swap is not an unpointed relational automorphism of `D2`. -/
theorem d2_swap_not_isRelAuto : ¬ IsRelAuto PrimDiff.D2 Bool.not :=
  fun h => not_not_d2_auto h.2

/-- Pointed rigidity: every endomorphism of `d2Obj` and every
endomorphism of `s2Obj` fixes both points — directly from `ha`/`hb`.
The pointed automorphism monoid on the carrier is trivial for BOTH
objects; the `S2` swap symmetry is destroyed by the pointing alone. -/
theorem pointed_rigid :
    (∀ h : Hom d2Obj d2Obj, h.f false = false ∧ h.f true = true) ∧
    (∀ h : Hom s2Obj s2Obj, h.f false = false ∧ h.f true = true) :=
  ⟨fun h => ⟨h.ha, h.hb⟩, fun h => ⟨h.ha, h.hb⟩⟩

/-! ## The faithful-presentation category of a three-point source

The fixed source is the three-point object `bigObj3` (one edge
`0 → 1`, third point `2` unconstrained).  A *presentation* is a map
out of its carrier that keeps the witnessed pair apart; a presentation
morphism is a factorization commuting with the presentations. -/

/-- The fixed three-point source: one edge `0 → 1`, third point free. -/
def bigObj3 : PtdRel :=
  ⟨Fin 3, fun x y => x = 0 ∧ y = 1, 0, 1, ⟨rfl, rfl⟩⟩

/-- A faithful presentation of the three-point source: a carrier map
that keeps the two witnessed occurrences apart.  Faithfulness
constrains only the pair `0`, `1`; the third occurrence `2` is where
the branching below happens. -/
structure Pres where
  Q : Type
  q : Fin 3 → Q
  faithful : q 0 ≠ q 1

/-- A morphism of presentations: a map commuting with the two
presentations at every occurrence. -/
structure PHom (P R : Pres) where
  h : P.Q → R.Q
  comm : ∀ x, h (P.q x) = R.q x

theorem phom_ext {P R : Pres} {u v : PHom P R} (h : u.h = v.h) :
    u = v := by
  cases u with
  | mk h1 c1 =>
    cases v with
    | mk h2 c2 =>
      have h' : h1 = h2 := h
      subst h'
      rfl

def pid (P : Pres) : PHom P P :=
  ⟨fun z => z, fun _ => rfl⟩

def pcomp {P R S : Pres} (g : PHom R S) (u : PHom P R) : PHom P S :=
  ⟨fun z => g.h (u.h z),
   fun x => (congrArg g.h (u.comm x)).trans (g.comm x)⟩

theorem pcomp_pid {P R : Pres} (u : PHom P R) : pcomp u (pid P) = u :=
  phom_ext rfl

theorem pid_pcomp {P R : Pres} (u : PHom P R) : pcomp (pid R) u = u :=
  phom_ext rfl

theorem pcomp_assoc {P R S T : Pres} (w : PHom S T) (g : PHom R S)
    (u : PHom P R) : pcomp (pcomp w g) u = pcomp w (pcomp g u) :=
  phom_ext rfl

/-- The identity presentation. -/
def idPres3 : Pres := ⟨Fin 3, id, by decide⟩

/-- The identity presentation is initial: `h := R.q` commutes, and any
commuting map is determined at every point of `Fin 3` — which is the
whole carrier of the identity presentation, so uniqueness is total. -/
theorem pres_initial (R : Pres) :
    ∃ u : PHom idPres3 R, ∀ v : PHom idPres3 R, v = u := by
  refine ⟨⟨R.q, fun _ => rfl⟩, ?_⟩
  intro v
  apply phom_ext
  funext x
  exact v.comm x

/-! ### The branching theorem -/

/-- Maximal faithful collapse, cut A: identifies occurrences `{0, 2}`
against `{1}`. -/
def mergeA : Pres := ⟨Bool, fun x => decide (x = 1), by decide⟩

/-- Maximal faithful collapse, cut B: identifies occurrences `{1, 2}`
against `{0}`. -/
def mergeB : Pres := ⟨Bool, fun x => decide (x = 0), by decide⟩

/-- No presentation morphism from cut A to cut B: `mergeA` identifies
the occurrences `0` and `2`, but `mergeB` separates them, and a
commuting map would have to do both. -/
theorem no_phom_mergeA_mergeB : ¬ Nonempty (PHom mergeA mergeB) := by
  intro ⟨u⟩
  have h0 := u.comm 0
  have h2 := u.comm 2
  have h02 : mergeA.q 0 = mergeA.q 2 := rfl
  rw [h02] at h0
  have hcontra : mergeB.q 0 = mergeB.q 2 := h0.symm.trans h2
  have hb : (true : Bool) = false := hcontra
  exact Bool.noConfusion hb

/-- Symmetrically, no presentation morphism from cut B to cut A. -/
theorem no_phom_mergeB_mergeA : ¬ Nonempty (PHom mergeB mergeA) := by
  intro ⟨u⟩
  have h1 := u.comm 1
  have h2 := u.comm 2
  have h12 : mergeB.q 1 = mergeB.q 2 := rfl
  rw [h12] at h1
  have hcontra : mergeA.q 1 = mergeA.q 2 := h1.symm.trans h2
  have hb : (true : Bool) = false := hcontra
  exact Bool.noConfusion hb

/-- THE BRANCHING THEOREM: the faithful-presentation category of the
three-point source has no weakly terminal object — no presentation
receives even one morphism from every presentation.  Proof: a
receiver `T` of maps from both cuts would identify `T.q 0 = T.q 2`
(through cut A) and `T.q 1 = T.q 2` (through cut B), hence
`T.q 0 = T.q 1`, against faithfulness.

Scope notes.  (i) Only *existence* of morphisms into `T` is assumed —
no uniqueness — so this refutes weak terminality, which is a STRONGER
result than refuting terminality.  (ii) On the two-point source the
analogous branching obstruction vanishes (see `phom2_unique_of_epi`
and `no_terminal_pres2`): the cut-branching appears exactly
when a third occurrence exists.  (iii) The choice of a maximal
faithful collapse is the choice of an observer cut — cut A and cut B
are incomparable (`no_phom_mergeA_mergeB`, `no_phom_mergeB_mergeA`)
and both branches are retained. -/
theorem no_terminal_pres :
    ¬ ∃ T : Pres, ∀ P : Pres, Nonempty (PHom P T) := by
  intro ⟨T, hT⟩
  obtain ⟨uA⟩ := hT mergeA
  obtain ⟨uB⟩ := hT mergeB
  have hA0 := uA.comm 0
  have hA2 := uA.comm 2
  have h02 : mergeA.q 0 = mergeA.q 2 := rfl
  rw [h02] at hA0
  have hT02 : T.q 0 = T.q 2 := hA0.symm.trans hA2
  have hB1 := uB.comm 1
  have hB2 := uB.comm 2
  have h12 : mergeB.q 1 = mergeB.q 2 := rfl
  rw [h12] at hB1
  have hT12 : T.q 1 = T.q 2 := hB1.symm.trans hB2
  exact T.faithful (hT02.trans hT12.symm)

/-! ## The faithful-presentation category of the two-point source

Here the source is the two-point carrier (`false`, `true`) itself.  The
branching obstruction of the three-point source cannot arise (there is
no third occurrence to cut either way), but full terminality of the
identity-like presentation is NOT provable without a
preimage-selection principle: what is proved is uniqueness against
surjective presentations plus existence for the two concrete
presentations below, and the remainder is recorded as an explicit OPEN
closure `no_terminal_pres2`: unrestricted terminality fails
constructively at the free point; the positive fragment is scoped to
surjective presentations. -/

/-- A faithful presentation of the two-point source. -/
structure Pres2 where
  Q : Type
  q : Bool → Q
  faithful : q false ≠ q true

/-- A morphism of two-point presentations. -/
structure PHom2 (P R : Pres2) where
  h : P.Q → R.Q
  comm : ∀ x, h (P.q x) = R.q x

theorem phom2_ext {P R : Pres2} {u v : PHom2 P R} (h : u.h = v.h) :
    u = v := by
  cases u with
  | mk h1 c1 =>
    cases v with
    | mk h2 c2 =>
      have h' : h1 = h2 := h
      subst h'
      rfl

/-- The identity presentation of the two-point source. -/
def idPres2 : Pres2 := ⟨Bool, id, by decide⟩

/-- The swapped presentation of the two-point source. -/
def swapPres2 : Pres2 := ⟨Bool, Bool.not, by decide⟩

/-- Surjectivity of a presentation: every point of the carrier is an
occurrence.  (Off the image of `P.q`, a commuting map is unconstrained,
so uniqueness below is scoped to surjective presentations.) -/
def Epi2 (P : Pres2) : Prop := ∀ z : P.Q, ∃ x : Bool, P.q x = z

theorem idPres2_epi : Epi2 idPres2 := fun z => ⟨z, rfl⟩

theorem swapPres2_epi : Epi2 swapPres2 :=
  fun z => ⟨Bool.not z, Bool.not_not z⟩

/-- Uniqueness half of two-point observer-terminality, scoped to
surjective presentations: any two morphisms from a surjective
presentation into the identity presentation agree, because a commuting
map is determined on the image and the image is everything. -/
theorem phom2_unique_of_epi (P : Pres2) (he : Epi2 P)
    (u v : PHom2 P idPres2) : u = v := by
  apply phom2_ext
  funext z
  obtain ⟨x, hx⟩ := he z
  rw [← hx, u.comm, v.comm]

/-- Existence for the concrete identity presentation. -/
theorem phom2_exists_from_id : Nonempty (PHom2 idPres2 idPres2) :=
  ⟨⟨fun z => z, fun _ => rfl⟩⟩

/-- Existence for the concrete swapped presentation: the swap itself
commutes (`not ∘ not = id`). -/
theorem phom2_exists_from_swap : Nonempty (PHom2 swapPres2 idPres2) :=
  ⟨⟨Bool.not, fun x => Bool.not_not x⟩⟩

/-- Exactly one morphism from the identity presentation into itself. -/
theorem phom2_unique_exists_id :
    ∃ u : PHom2 idPres2 idPres2, ∀ v : PHom2 idPres2 idPres2, v = u :=
  ⟨⟨fun z => z, fun _ => rfl⟩,
   fun v => phom2_unique_of_epi idPres2 idPres2_epi v
     ⟨fun z => z, fun _ => rfl⟩⟩

/-- Exactly one morphism from the swapped presentation into the
identity presentation. -/
theorem phom2_unique_exists_swap :
    ∃ u : PHom2 swapPres2 idPres2, ∀ v : PHom2 swapPres2 idPres2, v = u :=
  ⟨⟨Bool.not, fun x => Bool.not_not x⟩,
   fun v => phom2_unique_of_epi swapPres2 swapPres2_epi v
     ⟨Bool.not, fun x => Bool.not_not x⟩⟩

/-! Former OPEN cell, closed below by `no_terminal_pres2`.  The
selection observation stands as scope context: unrestricted
terminality of `idPres2` over ALL two-point presentations `P` requires
producing `h : P.Q → Bool` with `h (P.q x) = x`, i.e. a retraction of
the injective map `P.q` out of an arbitrary carrier `P.Q`.  Without
decidable equality on `P.Q` or a preimage-selection principle no such
retraction is constructible, and off the image of a non-surjective
`P.q` a commuting map is not even determined, so uniqueness fails
there too.  Finding: even two-point observer-terminality is
selection-relative constructively; the proved fragment is
`phom2_unique_of_epi` + `phom2_unique_exists_id` +
`phom2_unique_exists_swap`.  No classical choice is smuggled to close
the gap. -/
/-- The three-point presentation of the two-point source with one
free point: `0` and `1` present the two occurrences; `2` is outside
the image of the presenting map. -/
def freePres2 : Pres2 :=
  ⟨Fin 3, fun x => cond x 1 0, by decide⟩

/-- **Unrestricted two-point observer-terminality fails,
constructively** (review-pass closure of the former OPEN cell): for
EVERY candidate target, the free-point presentation admits two
distinct commuting maps — they agree on the image and differ at the
free point, by the target's own faithfulness.  No choice principle
enters on either side.  The positive fragment survives exactly as
scoped: uniqueness against surjective presentations
(`phom2_unique_of_epi`), where no free point exists. -/
theorem no_terminal_pres2 :
    ¬ ∃ T : Pres2, ∀ P : Pres2,
      ∃ h : PHom2 P T, ∀ h' : PHom2 P T, h' = h := by
  intro ⟨T, hT⟩
  obtain ⟨h, huniq⟩ := hT freePres2
  have hcomm0 : ∀ x : Bool,
      (fun z : Fin 3 => if z.val = 1 then T.q true else T.q false)
        (freePres2.q x) = T.q x := by
    intro x
    cases x <;> rfl
  have hcomm1 : ∀ x : Bool,
      (fun z : Fin 3 => if z.val = 0 then T.q false else T.q true)
        (freePres2.q x) = T.q x := by
    intro x
    cases x <;> rfl
  have e0 := huniq ⟨fun z : Fin 3 =>
    if z.val = 1 then T.q true else T.q false, hcomm0⟩
  have e1 := huniq ⟨fun z : Fin 3 =>
    if z.val = 0 then T.q false else T.q true, hcomm1⟩
  have heq : (⟨fun z : Fin 3 =>
      if z.val = 1 then T.q true else T.q false, hcomm0⟩
      : PHom2 freePres2 T)
      = ⟨fun z : Fin 3 =>
        if z.val = 0 then T.q false else T.q true, hcomm1⟩ :=
    e0.trans e1.symm
  have hat2 := congrArg
    (fun u : PHom2 freePres2 T => u.h ⟨2, by omega⟩) heq
  exact T.faithful hat2

/-! ## Machine-readable findings -/

/-- Machine-readable tags for the findings of this module. -/
def catsFindings : List (String × String) :=
  [("D2_INITIAL_PTDWITREL", "THEOREM d2_initial"),
   ("S2_INITIAL_SYM", "THEOREM s2_initial_sym"),
   ("S2_NOT_WEAKLY_INITIAL_FULL", "THEOREM s2_not_weakly_initial"),
   ("INITIALS_ISO_NOT_IDENTICAL",
    "THEOREMS initials_iso, two_initials_not_identical"),
   ("NO_WEAKLY_TERMINAL_PRES_3", "THEOREM no_terminal_pres"),
   ("NO_UNRESTRICTED_TERMINAL_PRES_2",
    "THEOREM no_terminal_pres2; positive scope phom2_unique_of_epi"),
   ("POINTED_AUTOS_TRIVIAL", "THEOREM pointed_rigid"),
   ("S2_SWAP_UNPOINTED_ONLY", "reused PrimDiff.swap_is_S2_automorphism")]

end PrimitiveCats
