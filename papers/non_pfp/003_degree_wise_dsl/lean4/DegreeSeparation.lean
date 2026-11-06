/-!
# Degree-Wise Obstruction Calculus and Symbolic DSL (Paper FOC-006)

Lean 4 Formalization: Graded complexes on C3, coboundary nilpotency (d1 ∘ d0 = 0),
the declared Gamma2 readout gate, projection contracts, and local-green/global-red
(LGGR) non-factorization theorems.

AuthorityEffect: None.
-/

namespace PaperFOC006

-- 1. Graded cochains on C3 (discrete triangle)
abbrev C0C3 := Int × Int × Int
abbrev C1C3 := Int × Int × Int
abbrev C2C3 := Int

/-- Discrete exterior coboundary d0: C^0 -> C^1 on C3. -/
def c3d0 : (Int × Int × Int) → (Int × Int × Int)
  | (f0, f1, f2) => (f1 - f0, f2 - f1, f0 - f2)

/-- Discrete exterior coboundary d1: C^1 -> C^2 on C3 with attached 2-cell. -/
def c3d1 : (Int × Int × Int) → Int
  | (h0, h1, h2) => h0 + h1 + h2

/-- Coboundary nilpotency: d1 ∘ d0 = 0 identically on C3. -/
theorem c3_d1_d0_zero (f : Int × Int × Int) : c3d1 (c3d0 f) = 0 := by
  obtain ⟨f0, f1, f2⟩ := f
  dsimp [c3d1, c3d0]
  omega

-- 2. Degree Model and Gated Readout
structure DegreeModel where
  c1 : C1C3
  hasTwoCell : Bool
  deriving DecidableEq, Repr

def HasGamma2Readout (m : DegreeModel) : Prop :=
  m.hasTwoCell = true

instance (m : DegreeModel) : Decidable (HasGamma2Readout m) :=
  inferInstanceAs (Decidable (m.hasTwoCell = true))

/-- The declared Gamma2 readout gate: missing 2-cell yields undefined (none), not zero. -/
def gamma2? (m : DegreeModel) : Option Nat :=
  if m.hasTwoCell then some (Int.natAbs (c3d1 m.c1)) else none

-- 3. DSL State and Acceptance Authority Gate
structure DSLState where
  hasEval : Bool
  diagnosticConstructible : Bool
  acceptanceAuthorizedRaw : Bool
  deriving DecidableEq, Repr

def diagnosticConstructible (s : DSLState) : Bool :=
  s.diagnosticConstructible

def acceptanceAuthorized (s : DSLState) : Bool :=
  s.hasEval && s.acceptanceAuthorizedRaw

theorem no_eval_no_acceptance (s : DSLState) (h : s.hasEval = false) :
    acceptanceAuthorized s = false := by
  dsimp [acceptanceAuthorized]
  simp [h]

-- 4. Declared Projection Contracts
structure DeclaredProjection where
  proj : C1C3 → C1C3
  idempotent : ∀ c, proj (proj c) = proj c
  kills_exact : ∀ f, proj (c3d0 f) = (0, 0, 0)

theorem declaredProjection_idempotent (P : DeclaredProjection) (c : C1C3) :
    P.proj (P.proj c) = P.proj c :=
  P.idempotent c

theorem declaredProjection_kills_exact (P : DeclaredProjection) (f : C0C3) :
    P.proj (c3d0 f) = (0, 0, 0) :=
  P.kills_exact f

-- 5. Concrete Replay Instances (C3)
def c3GraphOnly : DegreeModel :=
  { c1 := (1, 0, 0), hasTwoCell := false }

def c3WithTwoCell : DegreeModel :=
  { c1 := (1, 0, 0), hasTwoCell := true }

def typedDiagnosticNoEval : DSLState :=
  { hasEval := false, diagnosticConstructible := true, acceptanceAuthorizedRaw := false }

def typedDiagnosticWithEval : DSLState :=
  { hasEval := true, diagnosticConstructible := true, acceptanceAuthorizedRaw := true }

-- Readout evaluations
theorem gamma2_graphOnly_undefined : gamma2? c3GraphOnly = none := rfl

theorem gamma2_withTwoCell_one : gamma2? c3WithTwoCell = some 1 := rfl

theorem withTwoCell_has_gamma2_readout : HasGamma2Readout c3WithTwoCell := rfl

theorem gamma2_readout_requires_twoCell (m : DegreeModel) :
    HasGamma2Readout m → m.hasTwoCell = true := id

theorem no_twoCell_blocks_gamma2_readout (m : DegreeModel) (h : m.hasTwoCell = false) :
    ¬ HasGamma2Readout m := by
  intro hR
  have hr := gamma2_readout_requires_twoCell m hR
  rw [h] at hr
  contradiction

theorem graphOnly_has_no_gamma2_readout : ¬ HasGamma2Readout c3GraphOnly := by
  decide

theorem graphOnly_gamma2_not_zero_readout : gamma2? c3GraphOnly ≠ some 0 := by
  decide

/-- Integer ℓ¹ length of a 1-cochain on the triangle. -/
def c1L1 (x : C1C3) : Nat :=
  Int.natAbs x.1 + Int.natAbs x.2.1 + Int.natAbs x.2.2

/-- Difference of two 1-cochains. -/
def c1Sub (x y : C1C3) : C1C3 :=
  (x.1 - y.1, x.2.1 - y.2.1, x.2.2 - y.2.2)

private theorem c3_residual_sums_to_one (f0 f1 f2 : Int) :
    (1 - (f1 - f0)) + ((0 - (f2 - f1)) + (0 - (f0 - f2))) = 1 := by
  omega

private theorem c3_phi1_lower (f : C0C3) :
    1 ≤ c1L1 (c1Sub (1, 0, 0) (c3d0 f)) := by
  obtain ⟨f0, f1, f2⟩ := f
  dsimp only [c1L1, c1Sub, c3d0]
  rw [Nat.add_assoc]
  have hsum := c3_residual_sums_to_one f0 f1 f2
  have hle :=
    Int.natAbs_add_le (1 - (f1 - f0)) ((0 - (f2 - f1)) + (0 - (f0 - f2)))
  have hle2 := Int.natAbs_add_le (0 - (f2 - f1)) (0 - (f0 - f2))
  have hright :
      Int.natAbs ((1 - (f1 - f0)) + ((0 - (f2 - f1)) + (0 - (f0 - f2))))
        ≤ Int.natAbs (1 - (f1 - f0))
          + (Int.natAbs (0 - (f2 - f1)) + Int.natAbs (0 - (f0 - f2))) :=
    Nat.le_trans hle (Nat.add_le_add_left hle2 (Int.natAbs (1 - (f1 - f0))))
  rw [hsum] at hright
  rw [show Int.natAbs (1 : Int) = 1 by decide] at hright
  exact hright

private theorem c3_phi1_attained :
    c1L1 (c1Sub (1, 0, 0) (c3d0 (0, 0, 0))) = 1 := by
  decide

/-- Integer C3 degree separation. The distance from (1, 0, 0) to the image of
d0 is 1, that distance ignores the 2-cell flag, a missing 2-cell has no Gamma2
readout, and the attached 2-cell has Gamma2 1. General degree and real-valued
minimization are outside this theorem. -/
theorem c3_degree_separation_instance :
    (∃ f : C0C3, c1L1 (c1Sub (1, 0, 0) (c3d0 f)) = 1) ∧
    (∀ f : C0C3, 1 ≤ c1L1 (c1Sub (1, 0, 0) (c3d0 f))) ∧
    (∀ f : C0C3,
      c1L1 (c1Sub c3GraphOnly.c1 (c3d0 f)) =
        c1L1 (c1Sub c3WithTwoCell.c1 (c3d0 f))) ∧
    gamma2? c3GraphOnly = none ∧
    gamma2? c3WithTwoCell = some 1 ∧
    Int.natAbs (c3d1 (1, 0, 0)) = 1 := by
  refine ⟨⟨(0, 0, 0), c3_phi1_attained⟩, c3_phi1_lower, ?_, gamma2_graphOnly_undefined,
    gamma2_withTwoCell_one, ?_⟩
  · intro _f
    rfl
  · decide

-- 6. Squared-Aggregate Sign Collision (L2 failure mode)
def squaredAggregate (c : C1C3) : Int :=
  c.1 * c.1 + c.2.1 * c.2.1 + c.2.2 * c.2.2

def colWitness1 : C1C3 := (1, -1, 0)
def colWitness2 : C1C3 := (1, 1, 0)

theorem squaredAggregate_sign_collision_distinct :
    colWitness1 ≠ colWitness2 := by
  intro h
  injection h with h1 h23
  injection h23 with h2 h3
  revert h2
  decide

theorem squaredAggregate_sign_collision :
    squaredAggregate colWitness1 = squaredAggregate colWitness2 ∧
    c3d1 colWitness1 ≠ c3d1 colWitness2 := by
  decide

-- Helper algebraic lemmas for triple differences
theorem triple_sub_self (x0 x1 x2 : Int) : (x0 - x0, x1 - x1, x2 - x2) = (0, 0, 0) := by
  have h0 : x0 - x0 = 0 := by omega
  have h1 : x1 - x1 = 0 := by omega
  have h2 : x2 - x2 = 0 := by omega
  rw [h0, h1, h2]

theorem triple_symm (x0 x1 x2 y0 y1 y2 : Int)
    (h : (x0 - y0, x1 - y1, x2 - y2) = (0, 0, 0)) :
    (y0 - x0, y1 - x1, y2 - x2) = (0, 0, 0) := by
  injection h with h0 h12
  injection h12 with h1 h2
  have e0 : y0 - x0 = 0 := by omega
  have e1 : y1 - x1 = 0 := by omega
  have e2 : y2 - x2 = 0 := by omega
  rw [e0, e1, e2]

theorem triple_trans (x0 x1 x2 y0 y1 y2 z0 z1 z2 : Int)
    (h1 : (x0 - y0, x1 - y1, x2 - y2) = (0, 0, 0))
    (h2 : (y0 - z0, y1 - z1, y2 - z2) = (0, 0, 0)) :
    (x0 - z0, x1 - z1, x2 - z2) = (0, 0, 0) := by
  injection h1 with h10 h112
  injection h112 with h11 h12
  injection h2 with h20 h212
  injection h212 with h21 h22
  have e0 : x0 - z0 = 0 := by omega
  have e1 : x1 - z1 = 0 := by omega
  have e2 : x2 - z2 = 0 := by omega
  rw [e0, e1, e2]

theorem bool_beq_refl (b : Bool) : (b == b) = true := by
  cases b <;> rfl

theorem bool_beq_symm {b1 b2 : Bool} (h : (b1 == b2) = true) : (b2 == b1) = true := by
  cases b1 <;> cases b2 <;> first | rfl | contradiction

theorem bool_beq_trans {b1 b2 b3 : Bool} (h1 : (b1 == b2) = true) (h2 : (b2 == b3) = true) : (b1 == b3) = true := by
  cases b1 <;> cases b2 <;> cases b3 <;> first | rfl | contradiction

-- 7. Primitive Difference Kernel and LGGR Non-Factorization Theorems
structure PrimitiveDifference (α : Type) (β : Type) where
  δ : α → α → β
  Zero : β → Prop
  zero_refl : ∀ x, Zero (δ x x)
  zero_symm : ∀ x y, Zero (δ x y) → Zero (δ y x)
  zero_trans : ∀ x y z, Zero (δ x y) → Zero (δ y z) → Zero (δ x z)

namespace PrimitiveDifference

def ZeroRel (P : PrimitiveDifference α β) (x y : α) : Prop :=
  P.Zero (P.δ x y)

def zeroSetoid (P : PrimitiveDifference α β) : Setoid α where
  r := P.ZeroRel
  iseqv := {
    refl := P.zero_refl
    symm := fun h => P.zero_symm _ _ h
    trans := fun h1 h2 => P.zero_trans _ _ _ h1 h2
  }

def ResidualQuotient (P : PrimitiveDifference α β) : Type :=
  Quotient (zeroSetoid P)

/-- Forget an arbitrary context coordinate. The local relation and the global
readout are functions of the underlying carrier only. -/
def contextExtensionPD {Ctx α β : Type}
    (P : PaperFOC006.PrimitiveDifference α β) :
    PaperFOC006.PrimitiveDifference (Ctx × α) β where
  δ x y := P.δ x.2 y.2
  Zero := P.Zero
  zero_refl x := P.zero_refl x.2
  zero_symm x y h := P.zero_symm x.2 y.2 h
  zero_trans x y z h1 h2 := P.zero_trans x.2 y.2 z.2 h1 h2

/-- An equal local relation and an unequal global readout still refuse a
quotient factor after an arbitrary context coordinate is attached. -/
theorem localGreenGlobalRed_context_obstruction_of_witness
    {α β γ Ctx : Type}
    (P : PaperFOC006.PrimitiveDifference α β)
    (globalReadout : α → γ)
    (a b : α)
    (ctx : Ctx)
    (hrel : P.ZeroRel a b)
    (hdiff : globalReadout a ≠ globalReadout b) :
    ¬ (∃ factor : ResidualQuotient (contextExtensionPD (Ctx := Ctx) P) → γ,
        ∀ s,
          factor (Quotient.mk (zeroSetoid (contextExtensionPD (Ctx := Ctx) P)) s) =
            globalReadout s.2) := by
  intro ⟨factor, hf⟩
  let xa : Ctx × α := (ctx, a)
  let xb : Ctx × α := (ctx, b)
  have hrelc : ZeroRel (contextExtensionPD (Ctx := Ctx) P) xa xb := hrel
  have hq :
      Quotient.mk (zeroSetoid (contextExtensionPD (Ctx := Ctx) P)) xa =
        Quotient.mk (zeroSetoid (contextExtensionPD (Ctx := Ctx) P)) xb :=
    Quotient.sound hrelc
  have heq : globalReadout a = globalReadout b := by
    rw [← hf xa, ← hf xb, hq]
  exact hdiff heq

end PrimitiveDifference

-- A. C1-Local Quotient vs Gamma2 Global Gate
def c1LocalPD : PrimitiveDifference DegreeModel C1C3 where
  δ m1 m2 := (m1.c1.1 - m2.c1.1, m1.c1.2.1 - m2.c1.2.1, m1.c1.2.2 - m2.c1.2.2)
  Zero d := d = (0, 0, 0)
  zero_refl x := by
    obtain ⟨⟨x0, x1, x2⟩, b⟩ := x
    exact triple_sub_self x0 x1 x2
  zero_symm x y h := by
    obtain ⟨⟨x0, x1, x2⟩, bx⟩ := x
    obtain ⟨⟨y0, y1, y2⟩, byy⟩ := y
    exact triple_symm x0 x1 x2 y0 y1 y2 h
  zero_trans x y z h1 h2 := by
    obtain ⟨⟨x0, x1, x2⟩, bx⟩ := x
    obtain ⟨⟨y0, y1, y2⟩, byy⟩ := y
    obtain ⟨⟨z0, z1, z2⟩, bz⟩ := z
    exact triple_trans x0 x1 x2 y0 y1 y2 z0 z1 z2 h1 h2

theorem c1_data_invariant (m : DegreeModel) : m.c1 = m.c1 := rfl

theorem c3_models_zero_related : c1LocalPD.ZeroRel c3GraphOnly c3WithTwoCell := rfl

theorem c3_models_gamma2_differs : gamma2? c3GraphOnly ≠ gamma2? c3WithTwoCell := by
  decide

theorem c1_local_green_not_gamma2_global :
    ¬ (∃ (factor : c1LocalPD.ResidualQuotient → Option Nat),
         ∀ m, factor (Quotient.mk (c1LocalPD.zeroSetoid) m) = gamma2? m) := by
  intro ⟨factor, hf⟩
  have hq : Quotient.mk (c1LocalPD.zeroSetoid) c3GraphOnly =
            Quotient.mk (c1LocalPD.zeroSetoid) c3WithTwoCell :=
    Quotient.sound c3_models_zero_related
  have heq : gamma2? c3GraphOnly = gamma2? c3WithTwoCell := by
    rw [← hf c3GraphOnly, ← hf c3WithTwoCell, hq]
  exact c3_models_gamma2_differs heq

-- B. DSL-Local Diagnostic vs Acceptance Authority Gate
def dslLocalPD : PrimitiveDifference DSLState Bool where
  δ s1 s2 := s1.diagnosticConstructible == s2.diagnosticConstructible
  Zero b := b = true
  zero_refl x := bool_beq_refl x.diagnosticConstructible
  zero_symm _ _ h := bool_beq_symm h
  zero_trans _ _ _ h1 h2 := bool_beq_trans h1 h2

theorem diagnostic_constructible_invariant (s : DSLState) :
    s.diagnosticConstructible = s.diagnosticConstructible := rfl

theorem dsl_acceptance_witness_zero_related :
    dslLocalPD.ZeroRel typedDiagnosticNoEval typedDiagnosticWithEval := rfl

theorem dsl_acceptance_witness_differs :
    acceptanceAuthorized typedDiagnosticNoEval ≠ acceptanceAuthorized typedDiagnosticWithEval := by
  decide

theorem diagnostic_local_green_not_acceptance_authority :
    ¬ (∃ (factor : dslLocalPD.ResidualQuotient → Bool),
         ∀ s, factor (Quotient.mk (dslLocalPD.zeroSetoid) s) = acceptanceAuthorized s) := by
  intro ⟨factor, hf⟩
  have hq : Quotient.mk (dslLocalPD.zeroSetoid) typedDiagnosticNoEval =
            Quotient.mk (dslLocalPD.zeroSetoid) typedDiagnosticWithEval :=
    Quotient.sound dsl_acceptance_witness_zero_related
  have heq : acceptanceAuthorized typedDiagnosticNoEval = acceptanceAuthorized typedDiagnosticWithEval := by
    rw [← hf typedDiagnosticNoEval, ← hf typedDiagnosticWithEval, hq]
  exact dsl_acceptance_witness_differs heq

-- C. Composite Degree-DSL State Boundary
abbrev DegreeDSLState := DegreeModel × DSLState

def compositeLocalFingerprint (s : DegreeDSLState) : C1C3 × Bool :=
  (s.1.c1, s.2.diagnosticConstructible)

def compositeGlobalGate (s : DegreeDSLState) : Option Nat × Bool :=
  (gamma2? s.1, acceptanceAuthorized s.2)

def degreeDslLocalPD : PrimitiveDifference DegreeDSLState (C1C3 × Bool) where
  δ s1 s2 :=
    ((s1.1.c1.1 - s2.1.c1.1, s1.1.c1.2.1 - s2.1.c1.2.1, s1.1.c1.2.2 - s2.1.c1.2.2),
     s1.2.diagnosticConstructible == s2.2.diagnosticConstructible)
  Zero d := d.1 = (0, 0, 0) ∧ d.2 = true
  zero_refl x := by
    obtain ⟨⟨⟨x0, x1, x2⟩, bx⟩, ⟨e1, d1, a1⟩⟩ := x
    refine ⟨triple_sub_self x0 x1 x2, bool_beq_refl d1⟩
  zero_symm x y h := by
    obtain ⟨⟨⟨x0, x1, x2⟩, bx⟩, ⟨ex, dx, ax⟩⟩ := x
    obtain ⟨⟨⟨y0, y1, y2⟩, byy⟩, ⟨ey, dy, ay⟩⟩ := y
    obtain ⟨hTrip, hBool⟩ := h
    refine ⟨triple_symm x0 x1 x2 y0 y1 y2 hTrip, bool_beq_symm hBool⟩
  zero_trans x y z h1 h2 := by
    obtain ⟨⟨⟨x0, x1, x2⟩, bx⟩, ⟨ex, dx, ax⟩⟩ := x
    obtain ⟨⟨⟨y0, y1, y2⟩, byy⟩, ⟨ey, dy, ay⟩⟩ := y
    obtain ⟨⟨⟨z0, z1, z2⟩, bz⟩, ⟨ez, dz, az⟩⟩ := z
    obtain ⟨h1Trip, h1Bool⟩ := h1
    obtain ⟨h2Trip, h2Bool⟩ := h2
    refine ⟨triple_trans x0 x1 x2 y0 y1 y2 z0 z1 z2 h1Trip h2Trip, bool_beq_trans h1Bool h2Bool⟩

theorem degreeDsl_local_fingerprint_invariant (s : DegreeDSLState) :
    compositeLocalFingerprint s = compositeLocalFingerprint s := rfl

def compWitnessA : DegreeDSLState := (c3GraphOnly, typedDiagnosticNoEval)
def compWitnessB : DegreeDSLState := (c3WithTwoCell, typedDiagnosticWithEval)

theorem degreeDsl_witness_zero_related :
    degreeDslLocalPD.ZeroRel compWitnessA compWitnessB := by
  dsimp [PrimitiveDifference.ZeroRel, degreeDslLocalPD, compWitnessA, compWitnessB,
         c3GraphOnly, c3WithTwoCell, typedDiagnosticNoEval, typedDiagnosticWithEval]
  decide

theorem degreeDsl_global_gate_differs :
    compositeGlobalGate compWitnessA ≠ compositeGlobalGate compWitnessB := by
  decide

theorem degreeDsl_local_green_not_global_gate :
    ¬ (∃ (factor : degreeDslLocalPD.ResidualQuotient → Option Nat × Bool),
         ∀ s, factor (Quotient.mk (degreeDslLocalPD.zeroSetoid) s) = compositeGlobalGate s) := by
  intro ⟨factor, hf⟩
  have hq : Quotient.mk (degreeDslLocalPD.zeroSetoid) compWitnessA =
            Quotient.mk (degreeDslLocalPD.zeroSetoid) compWitnessB :=
    Quotient.sound degreeDsl_witness_zero_related
  have heq : compositeGlobalGate compWitnessA = compositeGlobalGate compWitnessB := by
    rw [← hf compWitnessA, ← hf compWitnessB, hq]
  exact degreeDsl_global_gate_differs heq

-- D. Context Extension Stability
structure ContextualDegreeDSLState (Context : Type) where
  context : Context
  degreeModel : DegreeModel
  dslState : DSLState

def contextualLocalFingerprint {Context : Type} (s : ContextualDegreeDSLState Context) : C1C3 × Bool :=
  (s.degreeModel.c1, s.dslState.diagnosticConstructible)

def contextualGlobalGate {Context : Type} (s : ContextualDegreeDSLState Context) : Option Nat × Bool :=
  (gamma2? s.degreeModel, acceptanceAuthorized s.dslState)

def replaceContext {C1 C2 : Type} (newContext : C2) (s : ContextualDegreeDSLState C1) : ContextualDegreeDSLState C2 where
  context := newContext
  degreeModel := s.degreeModel
  dslState := s.dslState

theorem contextual_local_fingerprint_ignores_context_replacement
    {C1 C2 : Type} (c2 : C2) (s : ContextualDegreeDSLState C1) :
    contextualLocalFingerprint (replaceContext c2 s) = contextualLocalFingerprint s := rfl

theorem contextual_global_gate_ignores_context_replacement
    {C1 C2 : Type} (c2 : C2) (s : ContextualDegreeDSLState C1) :
    contextualGlobalGate (replaceContext c2 s) = contextualGlobalGate s := rfl

def contextualWitnessA : ContextualDegreeDSLState Unit where
  context := ()
  degreeModel := c3GraphOnly
  dslState := typedDiagnosticNoEval

def contextualWitnessB : ContextualDegreeDSLState Unit where
  context := ()
  degreeModel := c3WithTwoCell
  dslState := typedDiagnosticWithEval

def contextualLocalPD : PrimitiveDifference (ContextualDegreeDSLState Unit) (C1C3 × Bool) where
  δ s1 s2 := degreeDslLocalPD.δ (s1.degreeModel, s1.dslState) (s2.degreeModel, s2.dslState)
  Zero := degreeDslLocalPD.Zero
  zero_refl x := degreeDslLocalPD.zero_refl (x.degreeModel, x.dslState)
  zero_symm x y := degreeDslLocalPD.zero_symm (x.degreeModel, x.dslState) (y.degreeModel, y.dslState)
  zero_trans x y z := degreeDslLocalPD.zero_trans (x.degreeModel, x.dslState) (y.degreeModel, y.dslState) (z.degreeModel, z.dslState)

theorem contextual_witness_zero_related :
    contextualLocalPD.ZeroRel contextualWitnessA contextualWitnessB := by
  exact degreeDsl_witness_zero_related

theorem contextual_global_gate_differs :
    contextualGlobalGate contextualWitnessA ≠ contextualGlobalGate contextualWitnessB := by
  exact degreeDsl_global_gate_differs

theorem contextual_local_green_not_global_gate :
    ¬ (∃ (factor : contextualLocalPD.ResidualQuotient → Option Nat × Bool),
         ∀ s, factor (Quotient.mk (contextualLocalPD.zeroSetoid) s) = contextualGlobalGate s) := by
  intro ⟨factor, hf⟩
  have hq : Quotient.mk (contextualLocalPD.zeroSetoid) contextualWitnessA =
            Quotient.mk (contextualLocalPD.zeroSetoid) contextualWitnessB :=
    Quotient.sound contextual_witness_zero_related
  have heq : contextualGlobalGate contextualWitnessA = contextualGlobalGate contextualWitnessB := by
    rw [← hf contextualWitnessA, ← hf contextualWitnessB, hq]
  exact contextual_global_gate_differs heq

end PaperFOC006
