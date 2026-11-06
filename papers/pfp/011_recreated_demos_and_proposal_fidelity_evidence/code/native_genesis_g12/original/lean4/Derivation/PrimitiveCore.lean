import Derivation.PrimDiff

/-!
# Primitive Core: one signature, nine candidate readings, full matrix

A single signature (`Setting`) carries every datum any of the nine
candidate readings of a primitive difference mentions: a carrier, an
asserted difference relation, two designated endpoints, a retention
store, a protected-demand store, and an admitted operation family.
Nine predicates on `Setting` formalize the candidate readings
(W, A, Bs, Bc, Bl, C, D, E, F).  Each of the 72 ordered cells (P, Q)
with P ≠ Q is settled by a named theorem — `imp_<src>_<tgt>`
(implication for every `Setting`) or `nimp_<src>_<tgt>` (a concrete
finite countermodel) — except four cells targeting the located axis
`Bl`, which are recorded OPEN with the reason (`open_cell_<src>_bl`).
Tally: 17 implications, 51 countermodels, 4 OPEN cells; the literal
table is exported as `matrixCells` for mechanical cross-checking.

Metatheory used (declared): types, functions, relations, propositional
logic, finite case analysis, and the decidability apparatus of the
metalanguage (`Decidable`, `decide`).  No quotients, no state.
-/

namespace PrimitiveCore

/-! ## The common signature -/

/-- The common signature.  Every candidate reading of a primitive
difference in this file is a predicate on this one structure, so that
implications and countermodels are stated over a single class of
models.  Fields: carrier `X`; asserted difference relation `r`;
designated endpoints `a`, `b`; retention store `ret` (which differences
are retained state); protected-demand store `prot` (deontic data);
admitted operation family `Ops`.  The signature has no observation
field. -/
structure Setting where
  X : Type
  r : X → X → Prop
  a : X
  b : X
  ret : X → X → Prop
  prot : X → X → Prop
  Ops : (X → X) → Prop

/-! ## Axis properties -/

/-- Cotransitivity: an asserted difference splits against every third
point. -/
def Cotrans {X : Type} (r : X → X → Prop) : Prop :=
  ∀ x y, r x y → ∀ z, r x z ∨ r z y

/-- Locatedness: the relation is realized by a boolean-valued function.
Locatedness is admitted as separate data; none of the propositional
candidate laws below yields it. -/
def Located {X : Type} (r : X → X → Prop) : Prop :=
  ∃ f : X → X → Bool, ∀ x y, r x y ↔ f x y = true

/-- Every pointwise-decidable relation is located: `decide` realizes
it.  Consequence for the matrix: every concrete countermodel in this
file uses a decidable relation, so no countermodel here can separate an
irreflexive-witness candidate from `Bl` on the locatedness conjunct;
those four cells are recorded OPEN (`open_cell_a_bl`,
`open_cell_bs_bl`, `open_cell_bc_bl`, `open_cell_f_bl`). -/
theorem located_of_decidable {X : Type} (r : X → X → Prop)
    [inst : ∀ x y, Decidable (r x y)] : Located r :=
  ⟨fun x y => decide (r x y), fun _x _y =>
    ⟨fun h => decide_eq_true h, fun h => of_decide_eq_true h⟩⟩

/-! ## The nine candidate predicates -/

/-- W — bare witnessed pair: the designated pair is asserted different.
No law. -/
def W (S : Setting) : Prop := S.r S.a S.b

/-- A — pointed witnessed irreflexive relation (PD-A). -/
def A (S : Setting) : Prop := S.r S.a S.b ∧ PrimDiff.Irrefl S.r

/-- Bs — the symmetric PD-B axis: A plus symmetry. -/
def Bs (S : Setting) : Prop := A S ∧ (∀ x y, S.r x y → S.r y x)

/-- Bc — the cotransitive PD-B axis: A plus cotransitivity. -/
def Bc (S : Setting) : Prop := A S ∧ Cotrans S.r

/-- Bl — the located PD-B axis: A plus locatedness. -/
def Bl (S : Setting) : Prop := A S ∧ Located S.r

/-- C — witnessed non-identification (PD-C): the asserted fact plus the
protected demand on the designated pair.  No irreflexivity. -/
def C (S : Setting) : Prop := S.r S.a S.b ∧ S.prot S.a S.b

/-- D — non-factorization through the point (PD-D): the selection of
the endpoints does not factor through the one-point carrier. -/
def D (S : Setting) : Prop :=
  ¬ ∃ p : Unit → S.X, p () = S.a ∧ p () = S.b

/-- E — irreducibility under the admitted family (PD-E): no admitted
composite identifies the designated pair.  E is always evaluated at
`S.Ops` as given. -/
def E (S : Setting) : Prop := PrimDiff.Irred S.Ops S.a S.b

/-- F — protected retained primitive difference (PD-F): A plus
retention plus the protected demand on the designated pair. -/
def F (S : Setting) : Prop := A S ∧ S.ret S.a S.b ∧ S.prot S.a S.b

/-- PD-D is exactly metatheoretic endpoint inequality
(`PrimDiff.factors_through_point_iff` at the `Setting` level). -/
theorem D_iff_ne : ∀ S : Setting, D S ↔ S.a ≠ S.b := fun S =>
  ⟨fun hd he => hd ((PrimDiff.factors_through_point_iff S.a S.b).mpr he),
   fun hne hex => hne ((PrimDiff.factors_through_point_iff S.a S.b).mp hex)⟩

/-! ## Key lemmas about the axes -/

/-- On the two-element carrier, irreflexivity already yields
cotransitivity: by `PrimDiff.irrefl_witness_ne` the endpoints of an
asserted pair are distinct, and on `Bool` any third point coincides
with one of them.  Scope of the minimality claims below: this theorem
shows that no countermodel to (A → Bc) or (Bs → Bc) or (F → Bc) exists
on the carrier `Bool`, and `PrimDiff.no_witness_on_subsingleton` shows
none exists on a subsingleton carrier; hence every three-element
cotransitivity countermodel in this file has minimum carrier size. -/
theorem cotrans_auto_on_two (r : Bool → Bool → Prop)
    (hi : PrimDiff.Irrefl r) : Cotrans r := by
  intro x y hxy z
  have hne : x ≠ y := PrimDiff.irrefl_witness_ne hi hxy
  cases x <;> cases y <;> cases z
  · exact absurd rfl hne
  · exact absurd rfl hne
  · exact Or.inr hxy
  · exact Or.inl hxy
  · exact Or.inl hxy
  · exact Or.inr hxy
  · exact absurd rfl hne
  · exact absurd rfl hne

/-! ## Conjunct transport helpers -/

theorem not_bs_of_not_a {S : Setting} (h : ¬ A S) : ¬ Bs S :=
  fun hb => h hb.1

theorem not_bc_of_not_a {S : Setting} (h : ¬ A S) : ¬ Bc S :=
  fun hb => h hb.1

theorem not_bl_of_not_a {S : Setting} (h : ¬ A S) : ¬ Bl S :=
  fun hb => h hb.1

theorem not_f_of_not_a {S : Setting} (h : ¬ A S) : ¬ F S :=
  fun hf => h hf.1

/-! ## Concrete models

Thirteen finite models witness every countermodel cell.  Carriers are
`Unit` (one point), `Bool` (two points), and `Fin 3` (three points);
each model is a full structure literal so every field is explicit. -/

/-- One-point self-difference, nothing protected, nothing retained,
no admitted operations: `r () ()` is asserted, so W holds while
irreflexivity, protection, retention, and endpoint inequality all
fail. -/
def unitBare : Setting where
  X := Unit
  r := fun _ _ => True
  a := ()
  b := ()
  ret := fun _ _ => False
  prot := fun _ _ => False
  Ops := fun _ => False

/-- One-point self-difference with universal retention and protection:
C holds (fact plus demand) while the endpoints are identical and
irreflexivity fails. -/
def unitFull : Setting where
  X := Unit
  r := fun _ _ => True
  a := ()
  b := ()
  ret := fun _ _ => True
  prot := fun _ _ => True
  Ops := fun _ => False

/-- Oriented two-element difference, nothing else admitted. -/
def d2Bare : Setting where
  X := Bool
  r := PrimDiff.D2
  a := false
  b := true
  ret := fun _ _ => False
  prot := fun _ _ => False
  Ops := fun _ => False

/-- Oriented two-element difference with one admitted merger (the
constant map to `false`). -/
def d2Merged : Setting where
  X := Bool
  r := PrimDiff.D2
  a := false
  b := true
  ret := fun _ _ => False
  prot := fun _ _ => False
  Ops := fun f => f = fun _ => false

/-- Oriented two-element difference, retained and protected. -/
def d2Protected : Setting where
  X := Bool
  r := PrimDiff.D2
  a := false
  b := true
  ret := fun _ _ => True
  prot := fun _ _ => True
  Ops := fun _ => False

/-- Oriented two-element difference, retained and protected, with one
admitted merger. -/
def d2ProtectedMerged : Setting where
  X := Bool
  r := PrimDiff.D2
  a := false
  b := true
  ret := fun _ _ => True
  prot := fun _ _ => True
  Ops := fun f => f = fun _ => false

/-- Symmetric two-element difference, nothing else admitted. -/
def s2Bare : Setting where
  X := Bool
  r := PrimDiff.S2
  a := false
  b := true
  ret := fun _ _ => False
  prot := fun _ _ => False
  Ops := fun _ => False

/-- Symmetric two-element difference with one admitted merger. -/
def s2Merged : Setting where
  X := Bool
  r := PrimDiff.S2
  a := false
  b := true
  ret := fun _ _ => False
  prot := fun _ _ => False
  Ops := fun f => f = fun _ => false

/-- The oriented edge on three points. -/
def triR : Fin 3 → Fin 3 → Prop := fun x y => x = 0 ∧ y = 1

instance (x y : Fin 3) : Decidable (triR x y) := by
  unfold triR; infer_instance

/-- The symmetrized edge on three points. -/
def triSymR : Fin 3 → Fin 3 → Prop := PrimDiff.Sym triR

/-- Three-point carrier with the oriented edge 0 → 1, nothing else
admitted. -/
def tri : Setting where
  X := Fin 3
  r := triR
  a := 0
  b := 1
  ret := fun _ _ => False
  prot := fun _ _ => False
  Ops := fun _ => False

/-- Three-point carrier with the oriented edge, retained and
protected. -/
def triProtected : Setting where
  X := Fin 3
  r := triR
  a := 0
  b := 1
  ret := fun _ _ => True
  prot := fun _ _ => True
  Ops := fun _ => False

/-- Three-point carrier with the symmetrized edge {0, 1}, nothing else
admitted. -/
def triSym : Setting where
  X := Fin 3
  r := triSymR
  a := 0
  b := 1
  ret := fun _ _ => False
  prot := fun _ _ => False
  Ops := fun _ => False

/-- Two-point carrier, distinct endpoints, empty relation, empty
admitted family: metatheoretic inequality (hence D and E) without any
asserted difference. -/
def boolEmpty : Setting where
  X := Bool
  r := fun _ _ => False
  a := false
  b := true
  ret := fun _ _ => False
  prot := fun _ _ => False
  Ops := fun _ => False

/-- Two-point carrier, distinct endpoints, empty relation, one admitted
merger: D holds while the merger erases irreducibility. -/
def boolEmptyMerged : Setting where
  X := Bool
  r := fun _ _ => False
  a := false
  b := true
  ret := fun _ _ => False
  prot := fun _ _ => False
  Ops := fun f => f = fun _ => false

/-! ## Model facts -/

theorem unitBare_w : W unitBare := True.intro

theorem unitBare_not_a : ¬ A unitBare := fun h => h.2 () True.intro

theorem unitBare_not_c : ¬ C unitBare := fun h => h.2

theorem unitBare_not_d : ¬ D unitBare :=
  fun h => (D_iff_ne unitBare).mp h rfl

theorem unitBare_not_e : ¬ E unitBare :=
  fun h => h id PrimDiff.Clos.id rfl

theorem unitFull_c : C unitFull := ⟨True.intro, True.intro⟩

theorem unitFull_not_a : ¬ A unitFull := fun h => h.2 () True.intro

theorem unitFull_not_d : ¬ D unitFull :=
  fun h => (D_iff_ne unitFull).mp h rfl

theorem unitFull_not_e : ¬ E unitFull :=
  fun h => h id PrimDiff.Clos.id rfl

theorem d2Bare_a : A d2Bare := ⟨PrimDiff.D2_witness, PrimDiff.D2_irrefl⟩

theorem d2Merged_a : A d2Merged :=
  ⟨PrimDiff.D2_witness, PrimDiff.D2_irrefl⟩

theorem d2Protected_f : F d2Protected :=
  ⟨⟨PrimDiff.D2_witness, PrimDiff.D2_irrefl⟩, True.intro, True.intro⟩

theorem d2ProtectedMerged_f : F d2ProtectedMerged :=
  ⟨⟨PrimDiff.D2_witness, PrimDiff.D2_irrefl⟩, True.intro, True.intro⟩

/-- The oriented two-element relation is not symmetric: the reverse
pair is not asserted. -/
theorem d2_not_symm : ¬ (∀ x y, PrimDiff.D2 x y → PrimDiff.D2 y x) :=
  fun h => absurd (h false true PrimDiff.D2_witness) (by decide)

theorem d2Bare_not_bs : ¬ Bs d2Bare := fun h => d2_not_symm h.2

theorem d2Protected_not_bs : ¬ Bs d2Protected := fun h => d2_not_symm h.2

theorem d2Bare_bc : Bc d2Bare :=
  ⟨d2Bare_a, cotrans_auto_on_two PrimDiff.D2 PrimDiff.D2_irrefl⟩

theorem d2Merged_bc : Bc d2Merged :=
  ⟨d2Merged_a, cotrans_auto_on_two PrimDiff.D2 PrimDiff.D2_irrefl⟩

theorem d2Bare_bl : Bl d2Bare :=
  ⟨d2Bare_a, located_of_decidable PrimDiff.D2⟩

theorem d2Merged_bl : Bl d2Merged :=
  ⟨d2Merged_a, located_of_decidable PrimDiff.D2⟩

theorem d2Bare_not_c : ¬ C d2Bare := fun h => h.2

theorem d2Bare_not_f : ¬ F d2Bare := fun h => h.2.1

theorem d2Merged_not_e : ¬ E d2Merged :=
  PrimDiff.merger_erases (F := fun f => f = fun _ => false)
    (v := false) rfl false true

theorem d2ProtectedMerged_not_e : ¬ E d2ProtectedMerged :=
  PrimDiff.merger_erases (F := fun f => f = fun _ => false)
    (v := false) rfl false true

theorem s2Bare_bs : Bs s2Bare :=
  ⟨⟨Or.inl PrimDiff.D2_witness, PrimDiff.S2_irrefl⟩,
   fun _ _ h => Or.symm h⟩

theorem s2Merged_bs : Bs s2Merged :=
  ⟨⟨Or.inl PrimDiff.D2_witness, PrimDiff.S2_irrefl⟩,
   fun _ _ h => Or.symm h⟩

theorem s2Bare_not_c : ¬ C s2Bare := fun h => h.2

theorem s2Bare_not_f : ¬ F s2Bare := fun h => h.2.1

theorem s2Merged_not_e : ¬ E s2Merged :=
  PrimDiff.merger_erases (F := fun f => f = fun _ => false)
    (v := false) rfl false true

theorem triR_edge : triR 0 1 := ⟨rfl, rfl⟩

theorem triR_irrefl : PrimDiff.Irrefl triR := by
  intro x hx
  have hx' : x = 0 ∧ x = 1 := hx
  exact absurd (hx'.1.symm.trans hx'.2) (by decide)

theorem tri_a : A tri := ⟨triR_edge, triR_irrefl⟩

theorem tri_bl : Bl tri := ⟨tri_a, located_of_decidable triR⟩

/-- Cotransitivity fails on the oriented three-point edge at the third
point: `triR 0 1` holds but neither `triR 0 2` nor `triR 2 1` does. -/
theorem tri_not_bc : ¬ Bc tri := by
  intro hbc
  have hsplit : triR 0 2 ∨ triR 2 1 :=
    hbc.2 (0 : Fin 3) (1 : Fin 3) triR_edge (2 : Fin 3)
  cases hsplit with
  | inl hl =>
      have hl' : (0 : Fin 3) = 0 ∧ (2 : Fin 3) = 1 := hl
      exact absurd hl'.2 (by decide)
  | inr hr =>
      have hr' : (2 : Fin 3) = 0 ∧ (1 : Fin 3) = 1 := hr
      exact absurd hr'.1 (by decide)

theorem triProtected_f : F triProtected :=
  ⟨⟨triR_edge, triR_irrefl⟩, True.intro, True.intro⟩

theorem triProtected_not_bc : ¬ Bc triProtected := by
  intro hbc
  have hsplit : triR 0 2 ∨ triR 2 1 :=
    hbc.2 (0 : Fin 3) (1 : Fin 3) triR_edge (2 : Fin 3)
  cases hsplit with
  | inl hl =>
      have hl' : (0 : Fin 3) = 0 ∧ (2 : Fin 3) = 1 := hl
      exact absurd hl'.2 (by decide)
  | inr hr =>
      have hr' : (2 : Fin 3) = 0 ∧ (1 : Fin 3) = 1 := hr
      exact absurd hr'.1 (by decide)

theorem triSymR_edge : triSymR 0 1 := Or.inl triR_edge

theorem triSymR_irrefl : PrimDiff.Irrefl triSymR := by
  intro x hx
  have hx' : triR x x ∨ triR x x := hx
  have hx'' : x = 0 ∧ x = 1 := hx'.elim id id
  exact absurd (hx''.1.symm.trans hx''.2) (by decide)

theorem triSymR_symm : ∀ x y, triSymR x y → triSymR y x := by
  intro x y h
  have h' : triR x y ∨ triR y x := h
  exact Or.symm h'

theorem triSym_bs : Bs triSym :=
  ⟨⟨triSymR_edge, triSymR_irrefl⟩, triSymR_symm⟩

/-- Cotransitivity fails on the symmetrized three-point edge at the
third point: `triSymR 0 1` holds but neither `triSymR 0 2` nor
`triSymR 2 1` does. -/
theorem triSym_not_bc : ¬ Bc triSym := by
  intro hbc
  have hsplit : triSymR 0 2 ∨ triSymR 2 1 :=
    hbc.2 (0 : Fin 3) (1 : Fin 3) triSymR_edge (2 : Fin 3)
  cases hsplit with
  | inl hl =>
      have hl' : triR 0 2 ∨ triR 2 0 := hl
      cases hl' with
      | inl h =>
          have h' : (0 : Fin 3) = 0 ∧ (2 : Fin 3) = 1 := h
          exact absurd h'.2 (by decide)
      | inr h =>
          have h' : (2 : Fin 3) = 0 ∧ (0 : Fin 3) = 1 := h
          exact absurd h'.1 (by decide)
  | inr hr =>
      have hr' : triR 2 1 ∨ triR 1 2 := hr
      cases hr' with
      | inl h =>
          have h' : (2 : Fin 3) = 0 ∧ (1 : Fin 3) = 1 := h
          exact absurd h'.1 (by decide)
      | inr h =>
          have h' : (1 : Fin 3) = 0 ∧ (2 : Fin 3) = 1 := h
          exact absurd h'.1 (by decide)

theorem boolEmpty_not_w : ¬ W boolEmpty := fun h => h

theorem boolEmpty_not_a : ¬ A boolEmpty := fun h => h.1

theorem boolEmpty_not_c : ¬ C boolEmpty := fun h => h.1

theorem boolEmpty_d : D boolEmpty :=
  (D_iff_ne boolEmpty).mpr (fun h => Bool.noConfusion h)

theorem boolEmpty_e : E boolEmpty :=
  (PrimDiff.irred_empty_iff_ne false true).mpr
    (fun h => Bool.noConfusion h)

theorem boolEmptyMerged_d : D boolEmptyMerged :=
  (D_iff_ne boolEmptyMerged).mpr (fun h => Bool.noConfusion h)

theorem boolEmptyMerged_not_e : ¬ E boolEmptyMerged :=
  PrimDiff.merger_erases (F := fun f => f = fun _ => false)
    (v := false) rfl false true

/-! ## Matrix row W (source: bare witnessed pair)

All eight cells are countermodels, all on the one-point carrier: bare
assertion is consistent with a self-difference, so no law, demand, or
inequality follows. -/

theorem nimp_w_a : ∃ S : Setting, W S ∧ ¬ A S :=
  ⟨unitBare, unitBare_w, unitBare_not_a⟩

theorem nimp_w_bs : ∃ S : Setting, W S ∧ ¬ Bs S :=
  ⟨unitBare, unitBare_w, not_bs_of_not_a unitBare_not_a⟩

theorem nimp_w_bc : ∃ S : Setting, W S ∧ ¬ Bc S :=
  ⟨unitBare, unitBare_w, not_bc_of_not_a unitBare_not_a⟩

/-- Countermodel on the A-conjunct of Bl: the one-point self-difference
is located (its relation is decidable) but not irreflexive, so Bl fails
through A.  Locatedness itself is not what fails here. -/
theorem nimp_w_bl : ∃ S : Setting, W S ∧ ¬ Bl S :=
  ⟨unitBare, unitBare_w, not_bl_of_not_a unitBare_not_a⟩

theorem nimp_w_c : ∃ S : Setting, W S ∧ ¬ C S :=
  ⟨unitBare, unitBare_w, unitBare_not_c⟩

/-- One-point self-difference: assertion without endpoint inequality. -/
theorem nimp_w_d : ∃ S : Setting, W S ∧ ¬ D S :=
  ⟨unitBare, unitBare_w, unitBare_not_d⟩

theorem nimp_w_e : ∃ S : Setting, W S ∧ ¬ E S :=
  ⟨unitBare, unitBare_w, unitBare_not_e⟩

theorem nimp_w_f : ∃ S : Setting, W S ∧ ¬ F S :=
  ⟨unitBare, unitBare_w, not_f_of_not_a unitBare_not_a⟩

/-! ## Matrix row A (source: pointed witnessed irreflexive relation) -/

theorem imp_a_w : ∀ S : Setting, A S → W S := fun _ h => h.1

/-- Countermodel at minimum carrier size two: a subsingleton carrier
hosts no A-witness (`PrimDiff.no_witness_on_subsingleton`). -/
theorem nimp_a_bs : ∃ S : Setting, A S ∧ ¬ Bs S :=
  ⟨d2Bare, d2Bare_a, d2Bare_not_bs⟩

/-- Countermodel at minimum carrier size three: by
`cotrans_auto_on_two` every irreflexive relation on `Bool` is
cotransitive, and no A-witness lives on a subsingleton carrier, so a
two-element (or smaller) countermodel cannot exist. -/
theorem nimp_a_bc : ∃ S : Setting, A S ∧ ¬ Bc S :=
  ⟨tri, tri_a, tri_not_bc⟩

/-- OPEN cell A → Bl. -/
def open_cell_a_bl : String :=
  "OPEN: no internal countermodel exists (every decidable relation is located, located_of_decidable); underivability of Located from the candidate laws is metatheoretic; Located is admitted as separate data"

theorem nimp_a_c : ∃ S : Setting, A S ∧ ¬ C S :=
  ⟨d2Bare, d2Bare_a, d2Bare_not_c⟩

/-- An irreflexive witness gives endpoint inequality
(`PrimDiff.irrefl_witness_ne`). -/
theorem imp_a_d : ∀ S : Setting, A S → D S := fun S h =>
  (D_iff_ne S).mpr (PrimDiff.irrefl_witness_ne h.2 h.1)

/-- One admitted merger erases irreducibility
(`PrimDiff.merger_erases`) while leaving the asserted irreflexive
witness untouched. -/
theorem nimp_a_e : ∃ S : Setting, A S ∧ ¬ E S :=
  ⟨d2Merged, d2Merged_a, d2Merged_not_e⟩

theorem nimp_a_f : ∃ S : Setting, A S ∧ ¬ F S :=
  ⟨d2Bare, d2Bare_a, d2Bare_not_f⟩

/-! ## Matrix row Bs (source: symmetric axis) -/

theorem imp_bs_w : ∀ S : Setting, Bs S → W S := fun _ h => h.1.1

theorem imp_bs_a : ∀ S : Setting, Bs S → A S := fun _ h => h.1

/-- Countermodel at minimum carrier size three (see
`cotrans_auto_on_two`): the symmetrized edge on three points is
symmetric and irreflexive but not cotransitive at the third point. -/
theorem nimp_bs_bc : ∃ S : Setting, Bs S ∧ ¬ Bc S :=
  ⟨triSym, triSym_bs, triSym_not_bc⟩

/-- OPEN cell Bs → Bl. -/
def open_cell_bs_bl : String :=
  "OPEN: no internal countermodel exists (every decidable relation is located, located_of_decidable); underivability of Located from the candidate laws is metatheoretic; Located is admitted as separate data"

theorem nimp_bs_c : ∃ S : Setting, Bs S ∧ ¬ C S :=
  ⟨s2Bare, s2Bare_bs, s2Bare_not_c⟩

theorem imp_bs_d : ∀ S : Setting, Bs S → D S := fun S h =>
  imp_a_d S h.1

theorem nimp_bs_e : ∃ S : Setting, Bs S ∧ ¬ E S :=
  ⟨s2Merged, s2Merged_bs, s2Merged_not_e⟩

theorem nimp_bs_f : ∃ S : Setting, Bs S ∧ ¬ F S :=
  ⟨s2Bare, s2Bare_bs, s2Bare_not_f⟩

/-! ## Matrix row Bc (source: cotransitive axis) -/

theorem imp_bc_w : ∀ S : Setting, Bc S → W S := fun _ h => h.1.1

theorem imp_bc_a : ∀ S : Setting, Bc S → A S := fun _ h => h.1

/-- The oriented two-element difference is cotransitive
(`cotrans_auto_on_two`) but not symmetric. -/
theorem nimp_bc_bs : ∃ S : Setting, Bc S ∧ ¬ Bs S :=
  ⟨d2Bare, d2Bare_bc, d2Bare_not_bs⟩

/-- OPEN cell Bc → Bl. -/
def open_cell_bc_bl : String :=
  "OPEN: no internal countermodel exists (every decidable relation is located, located_of_decidable); underivability of Located from the candidate laws is metatheoretic; Located is admitted as separate data"

theorem nimp_bc_c : ∃ S : Setting, Bc S ∧ ¬ C S :=
  ⟨d2Bare, d2Bare_bc, d2Bare_not_c⟩

theorem imp_bc_d : ∀ S : Setting, Bc S → D S := fun S h =>
  imp_a_d S h.1

theorem nimp_bc_e : ∃ S : Setting, Bc S ∧ ¬ E S :=
  ⟨d2Merged, d2Merged_bc, d2Merged_not_e⟩

theorem nimp_bc_f : ∃ S : Setting, Bc S ∧ ¬ F S :=
  ⟨d2Bare, d2Bare_bc, d2Bare_not_f⟩

/-! ## Matrix row Bl (source: located axis)

Cells from Bl are all decidable normally: the sources are concrete
located models. -/

theorem imp_bl_w : ∀ S : Setting, Bl S → W S := fun _ h => h.1.1

theorem imp_bl_a : ∀ S : Setting, Bl S → A S := fun _ h => h.1

/-- The oriented two-element difference is located but not symmetric. -/
theorem nimp_bl_bs : ∃ S : Setting, Bl S ∧ ¬ Bs S :=
  ⟨d2Bare, d2Bare_bl, d2Bare_not_bs⟩

/-- The oriented three-point edge is located (decidable) but not
cotransitive. -/
theorem nimp_bl_bc : ∃ S : Setting, Bl S ∧ ¬ Bc S :=
  ⟨tri, tri_bl, tri_not_bc⟩

theorem nimp_bl_c : ∃ S : Setting, Bl S ∧ ¬ C S :=
  ⟨d2Bare, d2Bare_bl, d2Bare_not_c⟩

theorem imp_bl_d : ∀ S : Setting, Bl S → D S := fun S h =>
  imp_a_d S h.1

theorem nimp_bl_e : ∃ S : Setting, Bl S ∧ ¬ E S :=
  ⟨d2Merged, d2Merged_bl, d2Merged_not_e⟩

theorem nimp_bl_f : ∃ S : Setting, Bl S ∧ ¬ F S :=
  ⟨d2Bare, d2Bare_bl, d2Bare_not_f⟩

/-! ## Matrix row C (source: witnessed non-identification)

C is fact plus demand without irreflexivity, so the one-point
self-difference with universal protection defeats every law-bearing
target. -/

theorem imp_c_w : ∀ S : Setting, C S → W S := fun _ h => h.1

/-- Witnessed and demanded, yet the endpoints coincide: demand does not
create irreflexivity. -/
theorem nimp_c_a : ∃ S : Setting, C S ∧ ¬ A S :=
  ⟨unitFull, unitFull_c, unitFull_not_a⟩

theorem nimp_c_bs : ∃ S : Setting, C S ∧ ¬ Bs S :=
  ⟨unitFull, unitFull_c, not_bs_of_not_a unitFull_not_a⟩

theorem nimp_c_bc : ∃ S : Setting, C S ∧ ¬ Bc S :=
  ⟨unitFull, unitFull_c, not_bc_of_not_a unitFull_not_a⟩

/-- Countermodel on the A-conjunct of Bl: the protected one-point
self-difference is located but not irreflexive. -/
theorem nimp_c_bl : ∃ S : Setting, C S ∧ ¬ Bl S :=
  ⟨unitFull, unitFull_c, not_bl_of_not_a unitFull_not_a⟩

/-- Witnessed and demanded, yet the endpoints coincide: demand does not
create endpoint inequality. -/
theorem nimp_c_d : ∃ S : Setting, C S ∧ ¬ D S :=
  ⟨unitFull, unitFull_c, unitFull_not_d⟩

theorem nimp_c_e : ∃ S : Setting, C S ∧ ¬ E S :=
  ⟨unitFull, unitFull_c, unitFull_not_e⟩

/-- F requires irreflexivity, which the one-point model refutes. -/
theorem nimp_c_f : ∃ S : Setting, C S ∧ ¬ F S :=
  ⟨unitFull, unitFull_c, not_f_of_not_a unitFull_not_a⟩

/-! ## Matrix row D (source: non-factorization through the point)

Metatheoretic inequality supplies no object-language datum: with the
relation empty every witnessed candidate fails, and one admitted merger
defeats irreducibility. -/

theorem nimp_d_w : ∃ S : Setting, D S ∧ ¬ W S :=
  ⟨boolEmpty, boolEmpty_d, boolEmpty_not_w⟩

theorem nimp_d_a : ∃ S : Setting, D S ∧ ¬ A S :=
  ⟨boolEmpty, boolEmpty_d, boolEmpty_not_a⟩

theorem nimp_d_bs : ∃ S : Setting, D S ∧ ¬ Bs S :=
  ⟨boolEmpty, boolEmpty_d, not_bs_of_not_a boolEmpty_not_a⟩

theorem nimp_d_bc : ∃ S : Setting, D S ∧ ¬ Bc S :=
  ⟨boolEmpty, boolEmpty_d, not_bc_of_not_a boolEmpty_not_a⟩

/-- Countermodel on the A-conjunct of Bl: the empty relation is located
(realized by the constant-false function) but hosts no witness. -/
theorem nimp_d_bl : ∃ S : Setting, D S ∧ ¬ Bl S :=
  ⟨boolEmpty, boolEmpty_d, not_bl_of_not_a boolEmpty_not_a⟩

theorem nimp_d_c : ∃ S : Setting, D S ∧ ¬ C S :=
  ⟨boolEmpty, boolEmpty_d, boolEmpty_not_c⟩

/-- Distinct endpoints with an admitted merger: inequality survives
outside the object language while the admitted family erases
irreducibility (`PrimDiff.merger_erases`). -/
theorem nimp_d_e : ∃ S : Setting, D S ∧ ¬ E S :=
  ⟨boolEmptyMerged, boolEmptyMerged_d, boolEmptyMerged_not_e⟩

theorem nimp_d_f : ∃ S : Setting, D S ∧ ¬ F S :=
  ⟨boolEmpty, boolEmpty_d, not_f_of_not_a boolEmpty_not_a⟩

/-! ## Matrix row E (source: irreducibility under the admitted family)

E constrains only the endpoints and the admitted family; it asserts
nothing in the relation. -/

theorem nimp_e_w : ∃ S : Setting, E S ∧ ¬ W S :=
  ⟨boolEmpty, boolEmpty_e, boolEmpty_not_w⟩

theorem nimp_e_a : ∃ S : Setting, E S ∧ ¬ A S :=
  ⟨boolEmpty, boolEmpty_e, boolEmpty_not_a⟩

theorem nimp_e_bs : ∃ S : Setting, E S ∧ ¬ Bs S :=
  ⟨boolEmpty, boolEmpty_e, not_bs_of_not_a boolEmpty_not_a⟩

theorem nimp_e_bc : ∃ S : Setting, E S ∧ ¬ Bc S :=
  ⟨boolEmpty, boolEmpty_e, not_bc_of_not_a boolEmpty_not_a⟩

/-- Countermodel on the A-conjunct of Bl: irreducibility without any
asserted witness. -/
theorem nimp_e_bl : ∃ S : Setting, E S ∧ ¬ Bl S :=
  ⟨boolEmpty, boolEmpty_e, not_bl_of_not_a boolEmpty_not_a⟩

theorem nimp_e_c : ∃ S : Setting, E S ∧ ¬ C S :=
  ⟨boolEmpty, boolEmpty_e, boolEmpty_not_c⟩

/-- Irreducibility instantiated at the identity (which lies in every
closure, `PrimDiff.Clos.id`) gives endpoint inequality. -/
theorem imp_e_d : ∀ S : Setting, E S → D S := fun S h =>
  (D_iff_ne S).mpr (h id PrimDiff.Clos.id)

theorem nimp_e_f : ∃ S : Setting, E S ∧ ¬ F S :=
  ⟨boolEmpty, boolEmpty_e, not_f_of_not_a boolEmpty_not_a⟩

/-! ## Matrix row F (source: protected retained primitive difference) -/

theorem imp_f_w : ∀ S : Setting, F S → W S := fun _ h => h.1.1

theorem imp_f_a : ∀ S : Setting, F S → A S := fun _ h => h.1

/-- Retention and protection do not create symmetry. -/
theorem nimp_f_bs : ∃ S : Setting, F S ∧ ¬ Bs S :=
  ⟨d2Protected, d2Protected_f, d2Protected_not_bs⟩

/-- Retention and protection do not create cotransitivity; minimum
carrier size three (see `cotrans_auto_on_two`). -/
theorem nimp_f_bc : ∃ S : Setting, F S ∧ ¬ Bc S :=
  ⟨triProtected, triProtected_f, triProtected_not_bc⟩

/-- OPEN cell F → Bl. -/
def open_cell_f_bl : String :=
  "OPEN: no internal countermodel exists (every decidable relation is located, located_of_decidable); underivability of Located from the candidate laws is metatheoretic; Located is admitted as separate data"

theorem imp_f_c : ∀ S : Setting, F S → C S := fun _ h =>
  ⟨h.1.1, h.2.2⟩

theorem imp_f_d : ∀ S : Setting, F S → D S := fun S h =>
  imp_a_d S h.1

/-- Retention and protection do not create irreducibility: one admitted
merger still erases the difference. -/
theorem nimp_f_e : ∃ S : Setting, F S ∧ ¬ E S :=
  ⟨d2ProtectedMerged, d2ProtectedMerged_f, d2ProtectedMerged_not_e⟩

/-! ## Scoped conditional equivalence (outside the 72 cells)

E is evaluated at `S.Ops` as given in every matrix cell above; the
following labeled conditional equivalence is not a matrix cell. -/

/-- Conditional scope: when the admitted family is empty,
irreducibility (PD-E) coincides with non-factorization (PD-D)
(`PrimDiff.irred_empty_iff_ne`). -/
theorem e_empty_iff_d : ∀ S : Setting,
    S.Ops = (fun _ => False) → (E S ↔ D S) := by
  intro S h
  unfold E
  rw [h]
  exact (PrimDiff.irred_empty_iff_ne S.a S.b).trans (D_iff_ne S).symm

/-! ## Fidelity precursors: protection and retention are demands, not
facts -/

/-- Protection is a demand, not a fact: an A-model exists with the
protected store empty.  No witnessed law produces the deontic datum. -/
theorem prot_not_from_witness : ∃ S : Setting, A S ∧ ¬ S.prot S.a S.b :=
  ⟨d2Bare, d2Bare_a, fun h => h⟩

/-- Retention is a demand, not a fact: an A-model exists with the
retention store empty. -/
theorem ret_not_from_witness : ∃ S : Setting, A S ∧ ¬ S.ret S.a S.b :=
  ⟨d2Bare, d2Bare_a, fun h => h⟩

/-- PD-F carries no observation data: the signature has no observation
field at all, and F does not read the admitted operation family, so F
is invariant under replacing `Ops`.  F depends only on the fragment
(r, a, b, ret, prot): it is a fact-plus-demand package, not yet an
obstruction, because obstruction requires an observation or collapse
event against which the demand is tested. -/
theorem f_ops_irrelevant : ∀ S : Setting, ∀ O' : (S.X → S.X) → Prop,
    F { S with Ops := O' } ↔ F S := fun _ _ => Iff.rfl

/-! ## Two-element classification at the Setting level -/

/-- Every Setting on `Bool` with designated endpoints `false`, `true`,
a pointwise-decidable relation, and the PD-A laws has `r = PrimDiff.D2`
or `r = PrimDiff.S2` (restatement of
`PrimDiff.bool_irrefl_witness_classification`). -/
theorem bool_class (r : Bool → Bool → Prop)
    [∀ x y, Decidable (r x y)]
    (ret prot : Bool → Bool → Prop) (Ops : (Bool → Bool) → Prop)
    (h : A { X := Bool, r := r, a := false, b := true,
             ret := ret, prot := prot, Ops := Ops }) :
    r = PrimDiff.D2 ∨ r = PrimDiff.S2 :=
  PrimDiff.bool_irrefl_witness_classification r h.2 h.1

/-! ## Machine-checkable matrix export -/

/-- The 72 ordered cells with status tags, literal, for mechanical
cross-checking against the theorem names in this file:
"IMPLIES" ↔ `imp_<src>_<tgt>`, "COUNTERMODEL" ↔ `nimp_<src>_<tgt>`,
"OPEN_LOCATED" ↔ `open_cell_<src>_bl`. -/
def matrixCells : List (String × String × String) := [
  ("W", "A", "COUNTERMODEL"),
  ("W", "Bs", "COUNTERMODEL"),
  ("W", "Bc", "COUNTERMODEL"),
  ("W", "Bl", "COUNTERMODEL"),
  ("W", "C", "COUNTERMODEL"),
  ("W", "D", "COUNTERMODEL"),
  ("W", "E", "COUNTERMODEL"),
  ("W", "F", "COUNTERMODEL"),
  ("A", "W", "IMPLIES"),
  ("A", "Bs", "COUNTERMODEL"),
  ("A", "Bc", "COUNTERMODEL"),
  ("A", "Bl", "OPEN_LOCATED"),
  ("A", "C", "COUNTERMODEL"),
  ("A", "D", "IMPLIES"),
  ("A", "E", "COUNTERMODEL"),
  ("A", "F", "COUNTERMODEL"),
  ("Bs", "W", "IMPLIES"),
  ("Bs", "A", "IMPLIES"),
  ("Bs", "Bc", "COUNTERMODEL"),
  ("Bs", "Bl", "OPEN_LOCATED"),
  ("Bs", "C", "COUNTERMODEL"),
  ("Bs", "D", "IMPLIES"),
  ("Bs", "E", "COUNTERMODEL"),
  ("Bs", "F", "COUNTERMODEL"),
  ("Bc", "W", "IMPLIES"),
  ("Bc", "A", "IMPLIES"),
  ("Bc", "Bs", "COUNTERMODEL"),
  ("Bc", "Bl", "OPEN_LOCATED"),
  ("Bc", "C", "COUNTERMODEL"),
  ("Bc", "D", "IMPLIES"),
  ("Bc", "E", "COUNTERMODEL"),
  ("Bc", "F", "COUNTERMODEL"),
  ("Bl", "W", "IMPLIES"),
  ("Bl", "A", "IMPLIES"),
  ("Bl", "Bs", "COUNTERMODEL"),
  ("Bl", "Bc", "COUNTERMODEL"),
  ("Bl", "C", "COUNTERMODEL"),
  ("Bl", "D", "IMPLIES"),
  ("Bl", "E", "COUNTERMODEL"),
  ("Bl", "F", "COUNTERMODEL"),
  ("C", "W", "IMPLIES"),
  ("C", "A", "COUNTERMODEL"),
  ("C", "Bs", "COUNTERMODEL"),
  ("C", "Bc", "COUNTERMODEL"),
  ("C", "Bl", "COUNTERMODEL"),
  ("C", "D", "COUNTERMODEL"),
  ("C", "E", "COUNTERMODEL"),
  ("C", "F", "COUNTERMODEL"),
  ("D", "W", "COUNTERMODEL"),
  ("D", "A", "COUNTERMODEL"),
  ("D", "Bs", "COUNTERMODEL"),
  ("D", "Bc", "COUNTERMODEL"),
  ("D", "Bl", "COUNTERMODEL"),
  ("D", "C", "COUNTERMODEL"),
  ("D", "E", "COUNTERMODEL"),
  ("D", "F", "COUNTERMODEL"),
  ("E", "W", "COUNTERMODEL"),
  ("E", "A", "COUNTERMODEL"),
  ("E", "Bs", "COUNTERMODEL"),
  ("E", "Bc", "COUNTERMODEL"),
  ("E", "Bl", "COUNTERMODEL"),
  ("E", "C", "COUNTERMODEL"),
  ("E", "D", "IMPLIES"),
  ("E", "F", "COUNTERMODEL"),
  ("F", "W", "IMPLIES"),
  ("F", "A", "IMPLIES"),
  ("F", "Bs", "COUNTERMODEL"),
  ("F", "Bc", "COUNTERMODEL"),
  ("F", "Bl", "OPEN_LOCATED"),
  ("F", "C", "IMPLIES"),
  ("F", "D", "IMPLIES"),
  ("F", "E", "COUNTERMODEL")
]

theorem matrixCells_length : matrixCells.length = 72 := rfl

end PrimitiveCore
