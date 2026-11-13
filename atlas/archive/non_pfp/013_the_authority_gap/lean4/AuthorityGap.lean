/-!
Finite content of the three proved rows in The Authority Gap.

CLM-005-007. Local acceptance does not imply global acceptance.
The hidden-bit census has four locally green compositions and two global
rejections, so the negative gluing count is half the local-green count.
The unconditional global rejection has equal counts, so the ratio is 1.

CLM-005-010. On the natural numbers, backlog `(rG - rV) * t` is positive
whenever verification is strictly slower than generation and the duration
is positive. The zero-stock share identity is the cross-multiplication
`3 t * 10 = (7 t + 3 t) * 3`.

CLM-005-011. An authorized exact claim is refuted by this rule when descent
was not executed or the residual is not exact. A scoped claim, one that does
not claim exactness, is not refuted by the residual clause of this rule.
-/

structure GluingEval where
  localGreen : Bool
  globalRed : Bool
  deriving DecidableEq, Repr

def countLocal (xs : List GluingEval) : Nat :=
  xs.foldl (fun n e => n + if e.localGreen then 1 else 0) 0

def countDefect (xs : List GluingEval) : Nat :=
  xs.foldl (fun n e => n + if e.localGreen && e.globalRed then 1 else 0) 0

/-- Hidden bit `H` and action `B`, each in `{0,1}`. Local evaluators accept
every composition. The global evaluator rejects when `B ≠ H`. -/
def hiddenBit : List GluingEval :=
  [⟨true, false⟩, ⟨true, true⟩, ⟨true, true⟩, ⟨true, false⟩]

/-- Both local evaluators accept and the global evaluator rejects. -/
def alwaysGlobalRed : List GluingEval :=
  [⟨true, true⟩, ⟨true, true⟩]

theorem hidden_bit_counts : countDefect hiddenBit = 2 ∧ countLocal hiddenBit = 4 := by
  decide

theorem hidden_bit_half : countDefect hiddenBit * 2 = countLocal hiddenBit := by
  decide

theorem hidden_bit_positive : 0 < countDefect hiddenBit := by
  decide

theorem local_green_does_not_imply_global :
    (∀ e ∈ hiddenBit, e.localGreen = true) ∧ ∃ e, e ∈ hiddenBit ∧ e.globalRed = true := by
  decide

theorem unconditional_red_ratio :
    countDefect alwaysGlobalRed = countLocal alwaysGlobalRed ∧ countLocal alwaysGlobalRed = 2 := by
  decide

def backlog (rateGeneration rateVerification duration : Nat) : Nat :=
  (rateGeneration - rateVerification) * duration

theorem backlog_example : backlog 50 10 12 = 480 := by
  decide

theorem manuscript_backlog_step : backlog 10 3 1 = 7 := by
  decide

theorem backlog_positive
    (rateGeneration rateVerification duration : Nat)
    (slower : rateVerification < rateGeneration)
    (positiveDuration : 0 < duration) :
    0 < backlog rateGeneration rateVerification duration := by
  unfold backlog
  exact Nat.mul_pos (Nat.sub_pos_of_lt slower) positiveDuration

theorem verified_share (t : Nat) : (3 * t) * 10 = ((7 * t) + (3 * t)) * 3 := by
  have hsum : (7 * t) + (3 * t) = 10 * t := by
    simpa using (Nat.add_mul 7 3 t).symm
  rw [hsum]
  simp [Nat.mul_comm, Nat.mul_left_comm, Nat.mul_assoc]

structure ExactClaim where
  authorized : Bool
  descentExecuted : Bool
  claimsExact : Bool
  residualExact : Bool
  deriving DecidableEq, Repr

/-- Red direction of the exactness-fraud rule. Scoped authorization is the
case `claimsExact = false`, which this residual clause does not refute. -/
def exactnessFraud (claim : ExactClaim) : Bool :=
  claim.authorized &&
    (!claim.descentExecuted || (claim.claimsExact && !claim.residualExact))

theorem missing_descent_is_refuted :
    exactnessFraud
        { authorized := true
          descentExecuted := false
          claimsExact := true
          residualExact := true } = true := by
  decide

theorem nonzero_residual_is_refuted :
    exactnessFraud
        { authorized := true
          descentExecuted := true
          claimsExact := true
          residualExact := false } = true := by
  decide

theorem scoped_residual_is_outside_this_rule :
    exactnessFraud
        { authorized := true
          descentExecuted := true
          claimsExact := false
          residualExact := false } = false := by
  decide

/-- Example 3.4: only the hidden-bit-zero trial is locally accepted;
    neither accepted trial fails globally. Both trials share one boundary. -/
def restrictedAcceptance : List GluingEval :=
  [⟨true, false⟩, ⟨false, true⟩]

theorem restricted_acceptance_zero_defect :
    countDefect restrictedAcceptance = 0 ∧ countLocal restrictedAcceptance = 1 := by
  decide

/-- The varying global acceptance bit cannot be recovered from a constant
    Unit boundary, even though its locally accepted subpopulation is sound. -/
theorem global_evaluation_does_not_factor :
    ¬ ∃ f : Unit → Bool, ∀ h : Bool, f () = !h := by
  intro ⟨f, h⟩
  have hfalse := h false
  have htrue := h true
  simp only [Bool.not_false] at hfalse
  simp only [Bool.not_true] at htrue
  rw [hfalse] at htrue
  cases htrue
