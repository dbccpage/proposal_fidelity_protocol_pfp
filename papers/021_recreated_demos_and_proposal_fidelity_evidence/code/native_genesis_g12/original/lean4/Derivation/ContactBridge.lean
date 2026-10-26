import Derivation.ObsDescent
import Derivation.PrimitiveCore
import Derivation.PrimitiveCats
import Derivation.Apartness
import Derivation.PrimitivePassage

/-!
# The contact bridge: the observer's complement against the native strata

The native corpus carries two independent presentations of asserted
difference: the *observer* stratum (`DiffInterface.DiffObs`, a valued
difference map with a zero relation whose three laws are proof
fields), and the *relational* strata of `PrimitiveCore` (the nine
candidate readings over `Setting`) and `Apartness` (the three
separately admitted apartness laws).  This module builds the bridge
between them, in both directions, at the exact grade each direction
earns:

1. **The complement** (`obsApart`): the negation of the zero relation
   is the strongest difference relation an observer yields by itself.
   Irreflexivity, symmetry, and double-negation stability are free —
   each is a law field contraposed (`obsApart_irrefl`,
   `obsApart_symm`, `obsApart_stable`, `zeroRel_indist`).
2. **Observer-stratum cells** (`obsSetting`, given a chosen
   complement-witnessed pair): the candidate readings W, A, Bs, D,
   and E-at-empty-stores hold outright (`obsSetting_w`,
   `obsSetting_a`, `obsSetting_bs`, `obsSetting_d`, `obsSetting_e`);
   Bc and Bl hold under an explicitly hypothesized pointwise
   decidability of the zero relation (`obsApart_cotrans`,
   `obsSetting_bc`, `obsSetting_bl`) — the decidability is the honest
   price, stated as a `Decidable` hypothesis, never obtained from a
   classical principle.
3. **The meet at apartness grade**: a positive apartness with
   decidable relation presents an observer whose complement is that
   relation back (`apartObs`, `apartObs_roundtrip`, `isApart_repr`),
   and the complement of a decidable zero relation is a positive
   apartness whose indistinguishability is the zero relation back
   (`obsApart_isApart`, `indist_obsApart_iff`).  Under pointwise
   decidability the two presentations are inter-constructible with
   matching relations in both composites.  The necessity of each of
   the three apartness admissions is already priced by the sealed
   finite countermodels (`Apartness.bare_breaks_refl`,
   `Apartness.irrefl_alone_breaks_symm`,
   `Apartness.symm_without_cotrans_breaks_trans`).
4. **Negative observer-stratum cells**: no observer complement ever
   yields protection or retention (`obsSetting_not_c`,
   `obsSetting_not_f`), while protection is freely declarable over it
   (`kernel_prot_independent`) — demands are declarations, never
   consequences.
5. **Representability, characterized and refuted**
   (`obsApart_repr_iff` and its instantiations): a relation is an
   observer complement exactly when its complement is an equivalence
   and the relation is double-negation stable.  The total relation on
   one point, the oriented two-point witness (over *every* value
   type), the symmetric three-point relation, and the endpoint
   witness over the empty relation each fail
   (`unit_total_not_repr`, `d2_not_obs_complement`,
   `triSym_not_obs_complement`, `d_not_witnessed_repr`); on the
   two-point carrier witness + irreflexivity + symmetry already force
   representability (`bool_bs_repr`), so the three-point refutation
   is minimal.
6. **Pricing the dropped decidability** (`Tri`, `wlemZero`): the
   unconditional cotransitivity schema for observer complements is
   exactly the weak law of excluded middle
   (`cotrans_schema_iff_wlem`), the unconditional stability schema is
   exactly double-negation elimination (`stability_schema_iff_dne`),
   and the unconditional locatedness schema implies the weak law
   (`located_schema_implies_wlem`) — each classical principle occurs
   only as a quantified statement inside a theorem, never as a proof
   step.  No internal countermodel can exist for these schemas; the
   two remaining cells are recorded OPEN with their exact prices
   (`open_bridge_cotrans`, `open_bridge_located`).
7. **Placement in the passage** (`colView`,
   `declared_zero_as_view`, `observation_stage_realizes_observer`,
   `kernelStage`, `kernel_stage_no_obstruction`): the declared
   observation stage of the passage *proves* — at the sealed
   `kernelObs`, equality-grade — the three laws an arriving observer
   carries as proof fields, and a stage carrying only an observer
   admits no active obstruction: the observer stratum sits at the
   zero-relation stage, after nothing.
8. **The flagship obstruction at passage grade**
   (`pair_blocked_is_collapse_collision`,
   `collapse_collision_is_pair_blocked`,
   `pair_blocked_iff_collapse_collision`): a zero-pair separated by a
   view is a collapse collision at the quotient projection, and
   conversely — proved in both directions, so at *this* grade the
   descent obstruction and the native collision are the same event in
   two vocabularies.  The sealed passage obstruction predicate adds
   retention, protection, and declaration conditions on top, and is
   strictly finer than both.

The stores of `obsSetting` are empty by construction: an observer
carries no retention, protection, or operation content, so its
faithful image in the candidate matrix declares none.  The scope of
`obsSetting_e` is the empty admitted family only; one admitted merger
erases irreducibility (the sealed `PrimDiff.merger_erases`).

Metatheory used (declared): types, functions, propositional logic,
case analysis on explicitly hypothesized `Decidable` instances,
finite case analysis discharged by `decide`, and — in the placement
section only — the quotient projection of `ObsDescent` and list
induction.  No choice, no excluded middle.
-/

namespace ContactBridge

open DiffInterface

variable {X R : Type}

/-! ## The complement of the zero relation -/

/-- Observer apartness: the complement of the zero relation.  This is
refutation-grade difference — no endpoint data, no positive
witness. -/
def obsApart (O : DiffObs X R) (x y : X) : Prop := ¬ ZeroRel O x y

/-- Irreflexivity is free: the reflexivity law field, contraposed. -/
theorem obsApart_irrefl (O : DiffObs X R) :
    PrimDiff.Irrefl (obsApart O) :=
  fun x h => h (O.zero_refl x)

/-- Symmetry is free: the symmetry law field, contraposed. -/
theorem obsApart_symm (O : DiffObs X R) :
    ∀ x y, obsApart O x y → obsApart O y x :=
  fun _ _ hxy hz => hxy (O.zero_symm hz)

/-- Double-negation stability is free: triple negation collapses
constructively. -/
theorem obsApart_stable (O : DiffObs X R) :
    ∀ x y, ¬ ¬ obsApart O x y → obsApart O x y :=
  fun _ _ h3 hz => h3 fun hn => hn hz

/-- Zero-pairs are indistinguishable in the complement. -/
theorem zeroRel_indist (O : DiffObs X R) :
    ∀ x y, ZeroRel O x y → Apartness.Indist (obsApart O) x y :=
  fun _ _ hz hn => hn hz

/-- The setting an observer presents to the native candidate matrix:
carrier, complement relation, a chosen pair, and empty stores — the
faithful image of a structure carrying no retention, protection, or
operation content. -/
def obsSetting (O : DiffObs X R) (a b : X) : PrimitiveCore.Setting where
  X := X
  r := obsApart O
  a := a
  b := b
  ret := fun _ _ => False
  prot := fun _ _ => False
  Ops := fun _ => False

/-! ## Observer-stratum cells: what a complement-witnessed pair
yields in the candidate matrix -/

/-- W: the chosen pair is the witness. -/
theorem obsSetting_w (O : DiffObs X R) (a b : X)
    (hab : obsApart O a b) : PrimitiveCore.W (obsSetting O a b) :=
  hab

/-- A: witness plus free irreflexivity. -/
theorem obsSetting_a (O : DiffObs X R) (a b : X)
    (hab : obsApart O a b) : PrimitiveCore.A (obsSetting O a b) :=
  ⟨hab, obsApart_irrefl O⟩

/-- Bs: witness plus free symmetry. -/
theorem obsSetting_bs (O : DiffObs X R) (a b : X)
    (hab : obsApart O a b) : PrimitiveCore.Bs (obsSetting O a b) :=
  ⟨obsSetting_a O a b hab, obsApart_symm O⟩

/-- Cotransitivity of the complement under pointwise decidability of
the zero relation: decide `ZeroRel O x z`; the no-branch gives the
left disjunct, the yes-branch transfers the difference right through
the transitivity law field.  Without the decidability admission this
cell is priced, not free. -/
theorem obsApart_cotrans (O : DiffObs X R)
    [inst : ∀ x y, Decidable (ZeroRel O x y)] :
    PrimitiveCore.Cotrans (obsApart O) :=
  fun x _ hxy z =>
    match inst x z with
    | isTrue hxz => Or.inr fun hzy => hxy (O.zero_trans hxz hzy)
    | isFalse hxz => Or.inl hxz

/-- Bc, under the decidability admission. -/
theorem obsSetting_bc (O : DiffObs X R) (a b : X)
    (hab : obsApart O a b)
    [∀ x y, Decidable (ZeroRel O x y)] :
    PrimitiveCore.Bc (obsSetting O a b) :=
  ⟨obsSetting_a O a b hab, obsApart_cotrans O⟩

/-- Bl, under the decidability admission: the locating boolean is
`decide` on the complement, via the sealed
`PrimitiveCore.located_of_decidable`. -/
theorem obsSetting_bl (O : DiffObs X R) (a b : X)
    (hab : obsApart O a b)
    [∀ x y, Decidable (ZeroRel O x y)] :
    PrimitiveCore.Bl (obsSetting O a b) :=
  ⟨obsSetting_a O a b hab,
   PrimitiveCore.located_of_decidable (obsApart O)
     (inst := fun x y =>
       inferInstanceAs (Decidable (¬ ZeroRel O x y)))⟩

/-- D: endpoint inequality, through the sealed A → D implication. -/
theorem obsSetting_d (O : DiffObs X R) (a b : X)
    (hab : obsApart O a b) : PrimitiveCore.D (obsSetting O a b) :=
  PrimitiveCore.imp_a_d (obsSetting O a b) (obsSetting_a O a b hab)

/-- E at the empty admitted family — the only family the observer
carries.  Scope: for a nonempty admitted merger family E dies (the
sealed `PrimDiff.merger_erases`); nothing here claims E beyond the
empty-store translation. -/
theorem obsSetting_e (O : DiffObs X R) (a b : X)
    (hab : obsApart O a b) : PrimitiveCore.E (obsSetting O a b) :=
  (PrimitiveCore.e_empty_iff_d (obsSetting O a b) rfl).mpr
    (obsSetting_d O a b hab)

/-! ## The meet at apartness grade -/

/-- The observer presented by a positive apartness: the difference
value is the apartness proposition itself, zero is its negation, and
the three law fields are exactly the three admissions, spent
one-for-one (irreflexivity for reflexivity, symmetry for symmetry,
cotransitivity for transitivity — the `Apartness.indist_refl` /
`indist_symm` / `indist_trans` shapes, inlined). -/
def apartObs (r : X → X → Prop) (h : Apartness.IsApart r) :
    DiffObs X Prop where
  delta x y := r x y
  Zero := Not
  zero_refl x := h.irrefl x
  zero_symm := fun {x y} hxy hyx => hxy (h.symm y x hyx)
  zero_trans := fun {x y z} hxy hyz hxz =>
    match h.cotrans x z hxz y with
    | Or.inl h1 => hxy h1
    | Or.inr h2 => hyz h2

/-- Its zero relation is exactly indistinguishability. -/
theorem apartObs_zeroRel (r : X → X → Prop)
    (h : Apartness.IsApart r) :
    ∀ x y, ZeroRel (apartObs r h) x y ↔ Apartness.Indist r x y :=
  fun _ _ => Iff.rfl

/-- Round trip at the relation: under pointwise decidability, the
complement of the constructed observer's zero relation is the
original apartness. -/
theorem apartObs_roundtrip (r : X → X → Prop)
    (h : Apartness.IsApart r) [inst : ∀ x y, Decidable (r x y)] :
    ∀ x y, obsApart (apartObs r h) x y ↔ r x y :=
  fun x y =>
    ⟨fun hnn =>
      match inst x y with
      | isTrue hr => hr
      | isFalse hn => absurd hn hnn,
     fun hr hn => hn hr⟩

/-- Every decidable positive apartness is the complement of some
observer's zero relation. -/
theorem isApart_repr (r : X → X → Prop)
    (h : Apartness.IsApart r) [∀ x y, Decidable (r x y)] :
    ∃ O : DiffObs X Prop, ∀ x y, obsApart O x y ↔ r x y :=
  ⟨apartObs r h, apartObs_roundtrip r h⟩

/-- The complement of a decidable zero relation is a positive
apartness: the other construction direction of the meet.
Irreflexivity and symmetry need no decidability; cotransitivity
spends it. -/
theorem obsApart_isApart (O : DiffObs X R)
    [∀ x y, Decidable (ZeroRel O x y)] :
    Apartness.IsApart (obsApart O) :=
  { irrefl := obsApart_irrefl O
    symm := obsApart_symm O
    cotrans := obsApart_cotrans O }

/-- Round trip at the zero relation: indistinguishability of the
complement recovers the zero relation, under decidability. -/
theorem indist_obsApart_iff (O : DiffObs X R)
    [inst : ∀ x y, Decidable (ZeroRel O x y)] :
    ∀ x y, Apartness.Indist (obsApart O) x y ↔ ZeroRel O x y :=
  fun x y =>
    ⟨fun hnn =>
      match inst x y with
      | isTrue hz => hz
      | isFalse hn => absurd hn hnn,
     fun hz hn => hn hz⟩

/-! ## Negative observer-stratum cells: demands are never
consequences -/

/-- C never holds at the empty-store translation: an observer carries
no protected demand (the observer-stratum echo of the sealed
`PrimitiveCore.prot_not_from_witness`). -/
theorem obsSetting_not_c (O : DiffObs X R) (a b : X) :
    ¬ PrimitiveCore.C (obsSetting O a b) :=
  fun h => h.2

/-- F never holds at the empty-store translation: an observer carries
no retention (the sealed `PrimitiveCore.ret_not_from_witness`,
replayed at the observer stratum). -/
theorem obsSetting_not_f (O : DiffObs X R) (a b : X) :
    ¬ PrimitiveCore.F (obsSetting O a b) :=
  fun h => h.2.1

/-- Protection is freely declarable over an observer and never
derivable from it: the same complement-witnessed pair supports C
after one declaration and refutes C without it. -/
theorem kernel_prot_independent (O : DiffObs X R) (a b : X)
    (hab : obsApart O a b) :
    PrimitiveCore.C
        { obsSetting O a b with prot := fun _ _ => True } ∧
      ¬ PrimitiveCore.C (obsSetting O a b) :=
  ⟨⟨hab, trivial⟩, obsSetting_not_c O a b⟩

/-! ## Native→observer representability: the characterization and
its countermodels -/

/-- **The representability crown**: a relation is the complement of
some observer's zero relation exactly when its complement is an
equivalence and it is double-negation stable.  Both directions are
fully constructive; the observer built in the reverse direction is
Prop-valued with `Not` as its zero predicate. -/
theorem obsApart_repr_iff (r : X → X → Prop) :
    (∃ O : DiffObs X Prop, ∀ x y, obsApart O x y ↔ r x y) ↔
      (Equivalence (fun x y => ¬ r x y) ∧
        ∀ x y, ¬ ¬ r x y → r x y) := by
  constructor
  · rintro ⟨O, hO⟩
    refine ⟨⟨?_, ?_, ?_⟩, ?_⟩
    · intro x hr
      exact (hO x x).mpr hr (O.zero_refl x)
    · intro x y hn hr
      exact hn ((hO x y).mp
        fun hz => (hO y x).mpr hr (O.zero_symm hz))
    · intro x y z hnxy hnyz hr
      exact (fun hnz : ¬ ZeroRel O x y => hnxy ((hO x y).mp hnz))
        fun hzxy =>
          (fun hnz : ¬ ZeroRel O y z => hnyz ((hO y z).mp hnz))
            fun hzyz => (hO x z).mpr hr (O.zero_trans hzxy hzyz)
    · intro x y hnn
      exact (hO x y).mp fun hz => hnn fun hr => (hO x y).mpr hr hz
  · rintro ⟨heq, hstab⟩
    refine ⟨{ delta := fun x y => r x y
              Zero := Not
              zero_refl := fun x => heq.refl x
              zero_symm := fun h => heq.symm h
              zero_trans := fun h1 h2 => heq.trans h1 h2 }, ?_⟩
    exact fun x y => ⟨fun hnn => hstab x y hnn, fun hr hn => hn hr⟩

/-- The total relation on the one-point carrier is not an observer
complement: irreflexivity of the complement is free, so bare
self-difference is unrepresentable (minimum carrier one — METATHEORY,
not proved here; readings W and C, models `unitBare`, `unitFull`). -/
theorem unit_total_not_repr :
    ¬ ∃ O : DiffObs Unit Prop,
        ∀ x y, obsApart O x y ↔ (fun _ _ : Unit => True) x y := by
  rintro ⟨O, hO⟩
  exact obsApart_irrefl O () ((hO () ()).mpr trivial)

/-- **Orientation cannot arrive as a complement, over any value
type**: no observer on the two-point carrier has the oriented witness
as its zero-complement — symmetry of the complement is free and the
oriented relation refuses it.  Minimum carrier two — METATHEORY
(subsingleton ⇒ symmetric), not proved here.  This is the
signature-level refutation of native→observer at the sealed object. -/
theorem d2_not_obs_complement :
    ¬ ∃ (R : Type) (O : DiffObs Bool R),
        ∀ x y, obsApart O x y ↔ PrimDiff.D2 x y := by
  rintro ⟨R, O, hO⟩
  have h1 : obsApart O false true :=
    (hO false true).mpr PrimDiff.D2_witness
  have h2 : PrimDiff.D2 true false :=
    (hO true false).mp (obsApart_symm O false true h1)
  exact absurd h2 (by decide)

/-- The symmetric three-point relation is not an observer complement,
over any value type: transitivity of the zero relation collapses
double negations along the chain through the third point, against the
sealed `Apartness.symm_without_cotrans_breaks_trans` data.  Minimum
carrier three — PROVED, by the positive `bool_bs_repr` below. -/
theorem triSym_not_obs_complement :
    ¬ ∃ (R : Type) (O : DiffObs (Fin 3) R),
        ∀ x y, obsApart O x y ↔ Apartness.triSymRel x y := by
  rintro ⟨R, O, hO⟩
  obtain ⟨h02, h21, h01⟩ :=
    Apartness.symm_without_cotrans_breaks_trans
  have hz02 : ¬ ¬ ZeroRel O 0 2 :=
    fun hnz => h02 ((hO 0 2).mp hnz)
  have hz21 : ¬ ¬ ZeroRel O 2 1 :=
    fun hnz => h21 ((hO 2 1).mp hnz)
  have hap01 : obsApart O 0 1 :=
    obsApart_stable O 0 1
      fun hna => h01 fun ht => hna ((hO 0 1).mpr ht)
  exact hz02 fun hzxy =>
    hz21 fun hzyz => hap01 (O.zero_trans hzxy hzyz)

/-- On the two-point carrier, a witnessed irreflexive symmetric
relation is always an observer complement — with *no* decidability
hypothesis: finite case analysis routes every double negation through
the witness or ex falso.  The three-point countermodel above is
therefore minimal. -/
theorem bool_bs_repr (r : Bool → Bool → Prop) (hw : r false true)
    (hi : PrimDiff.Irrefl r) (hs : ∀ x y, r x y → r y x) :
    ∃ O : DiffObs Bool Prop, ∀ x y, obsApart O x y ↔ r x y := by
  refine (obsApart_repr_iff r).mpr ⟨⟨hi, ?_, ?_⟩, ?_⟩
  · exact fun {x y} hn hr => hn (hs y x hr)
  · intro x y z hxy hyz
    cases x <;> cases y <;> cases z
    · exact hyz
    · exact hyz
    · exact hi false
    · exact hxy
    · exact hxy
    · exact hi true
    · exact hyz
    · exact hi true
  · intro x y hnn
    cases x <;> cases y
    · exact (hnn (hi false)).elim
    · exact hw
    · exact hs false true hw
    · exact (hnn (hi true)).elim

/-- The empty relation is an observer complement (the all-zero
shape), but no observer over it carries the endpoint witness: the
native `PrimDiff.meta_diff_without_assertion` gap survives contact —
metatheoretic endpoint distinctness transports into no complement
witness.  Serves the D- and E-readings (native models
`boolEmpty_d` / `boolEmpty_e`). -/
theorem d_not_witnessed_repr :
    ¬ ∃ (R : Type) (O : DiffObs Bool R),
        (∀ x y, obsApart O x y ↔ (fun _ _ : Bool => False) x y) ∧
          obsApart O false true := by
  rintro ⟨R, O, hO, hw⟩
  exact (hO false true).mp hw

/-! ## Pricing the dropped decidability: the classical principles as
quantified statements

The three schemas below quantify over all observers; each is
classically true, so no internal countermodel can exist.  Their exact
prices are proved as equivalences and an implication.  The classical
principles occur only *inside* the stated propositions — no proof
below uses any classical step. -/

/-- The three-point carrier used by the pricing observer. -/
inductive Tri where
  | t0
  | t1
  | t2
deriving DecidableEq

/-- The pricing observer: its zero relation is an equivalence for
*every* proposition `P` — the two chains through `t2` carry the
contradictory labels `P` and `¬ P`, so transitivity closes by ex
falso — while cotransitivity of its complement at `(t0, t1)` against
`t2` decides `¬ P ∨ ¬ ¬ P`. -/
def wlemZero (P : Prop) : DiffObs Tri Prop where
  delta x y :=
    (x = y) ∨ (x = .t0 ∧ y = .t2 ∧ P) ∨ (x = .t2 ∧ y = .t0 ∧ P) ∨
      (x = .t1 ∧ y = .t2 ∧ ¬ P) ∨ (x = .t2 ∧ y = .t1 ∧ ¬ P)
  Zero p := p
  zero_refl _ := Or.inl rfl
  zero_symm := by
    intro x y h
    rcases h with h | ⟨hx, hy, hP⟩ | ⟨hx, hy, hP⟩ |
      ⟨hx, hy, hP⟩ | ⟨hx, hy, hP⟩
    · exact Or.inl h.symm
    · exact Or.inr (Or.inr (Or.inl ⟨hy, hx, hP⟩))
    · exact Or.inr (Or.inl ⟨hy, hx, hP⟩)
    · exact Or.inr (Or.inr (Or.inr (Or.inr ⟨hy, hx, hP⟩)))
    · exact Or.inr (Or.inr (Or.inr (Or.inl ⟨hy, hx, hP⟩)))
  zero_trans := by
    intro x y z hxy hyz
    rcases hxy with h | ⟨hx, hy, hP⟩ | ⟨hx, hy, hP⟩ |
      ⟨hx, hy, hP⟩ | ⟨hx, hy, hP⟩
    · subst h; exact hyz
    · -- x = t0, y = t2, label P
      subst hx; subst hy
      rcases hyz with h | ⟨hy', hz, hP'⟩ | ⟨hy', hz, hP'⟩ |
        ⟨hy', hz, hP'⟩ | ⟨hy', hz, hP'⟩
      · subst h; exact Or.inr (Or.inl ⟨rfl, rfl, hP⟩)
      · cases hy'
      · subst hz; exact Or.inl rfl
      · cases hy'
      · exact absurd hP hP'
    · -- x = t2, y = t0, label P
      subst hx; subst hy
      rcases hyz with h | ⟨hy', hz, hP'⟩ | ⟨hy', hz, hP'⟩ |
        ⟨hy', hz, hP'⟩ | ⟨hy', hz, hP'⟩
      · subst h; exact Or.inr (Or.inr (Or.inl ⟨rfl, rfl, hP⟩))
      · subst hz; exact Or.inl rfl
      · cases hy'
      · cases hy'
      · cases hy'
    · -- x = t1, y = t2, label ¬ P
      subst hx; subst hy
      rcases hyz with h | ⟨hy', hz, hP'⟩ | ⟨hy', hz, hP'⟩ |
        ⟨hy', hz, hP'⟩ | ⟨hy', hz, hP'⟩
      · subst h
        exact Or.inr (Or.inr (Or.inr (Or.inl ⟨rfl, rfl, hP⟩)))
      · cases hy'
      · exact absurd hP' hP
      · cases hy'
      · subst hz; exact Or.inl rfl
    · -- x = t2, y = t1, label ¬ P
      subst hx; subst hy
      rcases hyz with h | ⟨hy', hz, hP'⟩ | ⟨hy', hz, hP'⟩ |
        ⟨hy', hz, hP'⟩ | ⟨hy', hz, hP'⟩
      · subst h
        exact Or.inr (Or.inr (Or.inr (Or.inr ⟨rfl, rfl, hP⟩)))
      · cases hy'
      · cases hy'
      · subst hz; exact Or.inl rfl
      · cases hy'

/-- **The cotransitivity schema is exactly the weak law of excluded
middle.**  Forward: cotransitivity of `wlemZero P`'s complement at
`(t0, t1)` against `t2` yields `¬ P ∨ ¬ ¬ P`.  Backward: decide the
weak law at `ZeroRel O x z`; the negative branch is the left
disjunct, the doubly-negated branch pushes the difference right
through the transitivity law field. -/
theorem cotrans_schema_iff_wlem :
    (∀ (X R : Type) (O : DiffObs X R),
        PrimitiveCore.Cotrans (obsApart O)) ↔
      ∀ P : Prop, ¬ P ∨ ¬ ¬ P := by
  constructor
  · intro hs P
    have hap : obsApart (wlemZero P) Tri.t0 Tri.t1 := by
      intro hz
      have hz' : (Tri.t0 = Tri.t1) ∨
          (Tri.t0 = Tri.t0 ∧ Tri.t1 = Tri.t2 ∧ P) ∨
          (Tri.t0 = Tri.t2 ∧ Tri.t1 = Tri.t0 ∧ P) ∨
          (Tri.t0 = Tri.t1 ∧ Tri.t1 = Tri.t2 ∧ ¬ P) ∨
          (Tri.t0 = Tri.t2 ∧ Tri.t1 = Tri.t1 ∧ ¬ P) := hz
      rcases hz' with h | ⟨_, h, _⟩ | ⟨h, _⟩ | ⟨h, _⟩ | ⟨h, _⟩ <;>
        cases h
    rcases hs Tri Prop (wlemZero P) Tri.t0 Tri.t1 hap Tri.t2 with
      hl | hr
    · exact Or.inl fun hP => hl (Or.inr (Or.inl ⟨rfl, rfl, hP⟩))
    · exact Or.inr fun hnP =>
        hr (Or.inr (Or.inr (Or.inr (Or.inr ⟨rfl, rfl, hnP⟩))))
  · intro hwlem X R O
    exact fun x y hxy z =>
      (hwlem (ZeroRel O x z)).elim Or.inl fun hnn =>
        Or.inr fun hzy => hnn fun hxz => hxy (O.zero_trans hxz hzy)

/-- **The stability schema is exactly double-negation elimination.**
Forward: a two-point observer whose zero relation is `x = y ∨ P`
turns `¬ ¬ P` into indistinguishability of the two points; the schema
returns the disjunction and constructor discrimination kills the left
disjunct.  Backward: instantiate elimination at the zero
proposition. -/
theorem stability_schema_iff_dne :
    (∀ (X R : Type) (O : DiffObs X R) (x y : X),
        Apartness.Indist (obsApart O) x y → ZeroRel O x y) ↔
      ∀ P : Prop, ¬ ¬ P → P := by
  constructor
  · intro hs P hnnP
    have hz := hs Bool Prop
      { delta := fun x y => x = y ∨ P
        Zero := fun p => p
        zero_refl := fun x => Or.inl rfl
        zero_symm := fun h =>
          h.elim (fun e => Or.inl e.symm) Or.inr
        zero_trans := fun h1 h2 =>
          h1.elim
            (fun e1 =>
              h2.elim (fun e2 => Or.inl (e1.trans e2)) Or.inr)
            Or.inr }
      false true
      (fun hna => hnnP fun hP => hna (Or.inr hP))
    rcases hz with he | hP
    · cases he
    · exact hP
  · exact fun hdne X R O x y h => hdne (ZeroRel O x y) h

/-- **The locatedness schema implies the weak law of excluded
middle**: the locating boolean of the same two-point observer at
`(false, true)` decides `¬ P ∨ ¬ ¬ P` by a `Bool` case split.  The
converse is not claimed (`open_bridge_located`). -/
theorem located_schema_implies_wlem :
    (∀ (X R : Type) (O : DiffObs X R),
        PrimitiveCore.Located (obsApart O)) →
      ∀ P : Prop, ¬ P ∨ ¬ ¬ P := by
  intro hs P
  let O : DiffObs Bool Prop :=
    { delta := fun x y => x = y ∨ P
      Zero := fun p => p
      zero_refl := fun x => Or.inl rfl
      zero_symm := fun h => h.elim (fun e => Or.inl e.symm) Or.inr
      zero_trans := fun h1 h2 =>
        h1.elim
          (fun e1 => h2.elim (fun e2 => Or.inl (e1.trans e2)) Or.inr)
          Or.inr }
  obtain ⟨f, hf⟩ := hs Bool Prop O
  cases hb : f false true with
  | true =>
      exact Or.inl fun hP => (hf false true).mpr hb (Or.inr hP)
  | false =>
      refine Or.inr fun hnP => ?_
      have hnap : ¬ obsApart O false true := fun hap => by
        have hft := (hf false true).mp hap
        rw [hb] at hft
        exact Bool.noConfusion hft
      exact hnap fun hz =>
        hz.elim (fun e => Bool.noConfusion e) hnP

/-- OPEN cell: the unconditional cotransitivity schema.  No internal
countermodel can exist; the exact price is recorded. -/
def open_bridge_cotrans : String :=
  "OPEN: no internal countermodel exists (the schema quantified over all observers is classically true); the schema is exactly the weak law of excluded middle (cotrans_schema_iff_wlem); pointwise decidability of the zero relation discharges it (obsApart_cotrans); cotransitivity of an observer complement is admitted as separate data, matching the sealed open_cell_*_bl discipline"

/-- OPEN cell: the unconditional locatedness schema.  No internal
countermodel can exist; only the forward price is proved. -/
def open_bridge_located : String :=
  "OPEN: no internal countermodel exists (the schema quantified over all observers is classically true); the schema implies the weak law of excluded middle (located_schema_implies_wlem); the converse is not claimed - it would need a function-comprehension principle beyond the weak law; pointwise decidability discharges the schema (obsSetting_bl); Located remains admitted as separate data"

/-! ## Placement: the observer stratum at the passage's declared
observation stage -/

/-- The column view of a declared observation: the membership
signature of an occurrence across the declared columns. -/
def colView (cols : List (List Nat)) : Nat → List Bool :=
  fun i => cols.map fun c => decide (i ∈ c)

/-- **The declared zero relation is a kernel observer's zero
relation**: the passage's Boolean `zeroP` agrees with the sealed
`kernelObs` at the column view.  The three equivalence laws the
supplied stratum carries as admitted proof fields are *proved* here,
equality-grade, by the sealed kernel construction. -/
theorem declared_zero_as_view (cols : List (List Nat)) (i j : Nat) :
    PrimitivePassage.zeroP cols i j = true ↔
      ZeroRel (kernelObs (colView cols)) i j := by
  have hb : ∀ a b : Bool, ((!(a != b)) = true ↔ a = b) := by decide
  show PrimitivePassage.zeroP cols i j = true ↔
    colView cols i = colView cols j
  induction cols with
  | nil => exact ⟨fun _ => rfl, fun _ => rfl⟩
  | cons c rest ih =>
      rw [PrimitivePassage.zeroP_cons, Bool.and_eq_true]
      show _ ∧ _ ↔
        decide (i ∈ c) :: colView rest i =
          decide (j ∈ c) :: colView rest j
      rw [List.cons_eq_cons]
      exact and_congr (hb (decide (i ∈ c)) (decide (j ∈ c))) ih

/-- The declared observation stage realizes an observer outright: an
observer whose zero relation is the declared `zeroP` exists, with all
three laws proved.  (Shipped at the kernel observer's paired value
type, the same form as the tag realization above.) -/
theorem observation_stage_realizes_observer
    (cols : List (List Nat)) :
    ∃ O : DiffObs Nat (List Bool × List Bool),
      ∀ i j, (PrimitivePassage.zeroP cols i j = true) ↔
        ZeroRel O i j :=
  ⟨kernelObs (colView cols), fun i j => declared_zero_as_view cols i j⟩

/-- The stage an arriving observer determines by itself: everything
live, nothing retained, nothing guarded — observation content only. -/
def kernelStage (O : DiffObs X R) : DiffInterface.Stage X R where
  live _ := True
  retained _ _ := False
  guarded _ _ := False
  obs := O

/-- A stage carrying only an observer admits no active obstruction:
retention and guarding are separately priced declarations the
observer stratum never supplies. -/
theorem kernel_stage_no_obstruction (O : DiffObs X R) :
    ∀ x y, ¬ DiffInterface.ActiveObstruction (kernelStage O) x y :=
  fun _ _ h => h.1

/-! ## The flagship obstruction at passage grade -/

/-- The descent obstruction is collapse-collision at the quotient
projection: a zero-pair on which a view differs is exactly a
collision of the view-difference relation under the projection.  The
sealed passage obstruction predicate adds retention, protection, and
declaration conditions on top — proved independent there — so the
native obstruction is strictly finer at passage grade. -/
theorem pair_blocked_is_collapse_collision {Z : Type}
    (O : DiffObs X R) (ψ : X → Z) {x y : X}
    (hxy : ZeroRel O x y) (hne : ψ x ≠ ψ y) :
    PrimDiff.CollapseCollision (fun u v => ψ u ≠ ψ v)
      (ObsQuotient.mk O) :=
  ⟨x, y, hne, obsQuotient_eq_of_zero O hxy⟩

/-- The converse, by exactness of the quotient: every collapse
collision of the view-difference relation at the projection is a
zero-pair the view separates. -/
theorem collapse_collision_is_pair_blocked {Z : Type}
    (O : DiffObs X R) (ψ : X → Z)
    (h : PrimDiff.CollapseCollision (fun u v => ψ u ≠ ψ v)
      (ObsQuotient.mk O)) :
    ∃ x y, ZeroRel O x y ∧ ψ x ≠ ψ y := by
  obtain ⟨u, v, hne, hc⟩ := h
  exact ⟨u, v, (ObsDescent.obsQuotient_mk_eq_iff O u v).mp hc, hne⟩

/-- **Both directions**: blocked descent and collapse collision are
one event in two vocabularies, at this grade.  The sealed passage
obstruction predicate adds retention, protection, and declaration
conditions on top — proved independent there — so the passage-grade
notion is strictly finer than either side of this equivalence. -/
theorem pair_blocked_iff_collapse_collision {Z : Type}
    (O : DiffObs X R) (ψ : X → Z) :
    (∃ x y, ZeroRel O x y ∧ ψ x ≠ ψ y) ↔
      PrimDiff.CollapseCollision (fun u v => ψ u ≠ ψ v)
        (ObsQuotient.mk O) :=
  ⟨fun ⟨_, _, hz, hne⟩ =>
      pair_blocked_is_collapse_collision O ψ hz hne,
   collapse_collision_is_pair_blocked O ψ⟩

end ContactBridge
