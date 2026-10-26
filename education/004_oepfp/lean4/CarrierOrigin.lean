/-!
# PFP v0.2: Carrier Origin and ProtoSupport Formalization in Lean 4

Formalization of the Carrier-First vs. Difference-First vs. ProtoSupport Trilemma,
the 7 irreducible obligations of ProtoSupport, and the constructive boundary
nilpotency invariant (d1 ∘ d0 = 0).
-/

namespace SymbolGame.V02

/-- The Carrier Origin Trilemma classification. -/
inductive CarrierOriginStatus where
  | CarrierFirst : CarrierOriginStatus
  | DifferenceFirst : CarrierOriginStatus
  | ProtoSupportResolved : CarrierOriginStatus
  deriving DecidableEq, Repr

/-- The seven irreducible obligations of ProtoSupport. -/
structure ProtoSupport where
  has_support : Bool
  has_addressability : Bool
  has_distinguishability : Bool
  has_orientation : Bool
  has_boundary_capacity : Bool
  has_witnessability : Bool
  has_markability : Bool
  deriving DecidableEq, Repr

/-- A carrier is fully supported if and only if all 7 obligations hold. -/
def ProtoSupport.is_fully_supported (ps : ProtoSupport) : Bool :=
  ps.has_support &&
  ps.has_addressability &&
  ps.has_distinguishability &&
  ps.has_orientation &&
  ps.has_boundary_capacity &&
  ps.has_witnessability &&
  ps.has_markability

/-- Terminal classification of proposals in PFP v0.2. -/
inductive TerminalStatus where
  | Exact : TerminalStatus
  | StabilizedSurvivor : TerminalStatus
  | OpenObstruction : TerminalStatus
  | Refused : TerminalStatus
  deriving DecidableEq, Repr

/-- Exact typed refusal codes. Missing maps or ungrounded carriers fail closed. -/
inductive RefusalCode where
  | MapUndefined : RefusalCode
  | CarrierRegress : RefusalCode
  | NilpotencyBroken : RefusalCode
  | DualityGapNonzero : RefusalCode
  deriving DecidableEq, Repr

/-- A 1-simplex (directed edge) between two addressable loci. -/
structure Simplex1 (V : Type) where
  src : V
  tgt : V
  distinct : src ≠ tgt

/--
Theorem: A non-degenerate 1-simplex requires distinct endpoints.
A difference-first claim without distinguishability cannot inhabit Simplex1.
-/
theorem no_difference_without_distinguishability (V : Type) (src tgt : V) (h : src = tgt) :
    ¬ ∃ (e : Simplex1 V), e.src = src ∧ e.tgt = tgt := by
  intro ⟨e, h_src, h_tgt⟩
  have h_eq : e.src = e.tgt := by
    rw [h_src, h_tgt, h]
  exact e.distinct h_eq

/--
Constructive Nilpotency Preservation:
If d1 ∘ d0 = 0, then for any 0-cochain alpha, d1 (d0 alpha) = 0.
-/
theorem nilpotency_composition {α β γ : Type} [Zero γ]
    (d0 : α → β) (d1 : β → γ) (h_nil : ∀ x, d1 (d0 x) = 0) (a : α) :
    d1 (d0 a) = 0 :=
  h_nil a

end SymbolGame.V02
