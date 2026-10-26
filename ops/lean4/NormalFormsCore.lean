/-!
  Relational Normal Forms and BQNF under Genesis Principles
  AuthorityEffect: None
  Gate: Lean 4 (version 4.34.0)
-/

set_option linter.unusedVariables false

namespace NormalForms

/-- Attribute token -/
def Attribute := String
deriving Repr, DecidableEq

/-- Heading: a finite set of distinct attributes -/
structure Heading where
  attrs : List Attribute
  deriving Repr

/-- Functional Dependency: X → Y -/
structure FunctionalDependency where
  det : List Attribute -- Determinant X
  dep : List Attribute -- Dependent Y
  deriving Repr

/-- Candidate Key: a minimal determinant of the entire heading -/
structure CandidateKey where
  key_attrs : List Attribute
  deriving Repr

/-- Classical normal-form tags.
    Membership lives in the YAML contracts. These comments name the same tests. -/
inductive NormalFormLevel where
  | NF0  -- raw carrier; fails the four-pillar test
  | NF1  -- scalar domains and a declared candidate key (Codd 1970)
  | NF2  -- no non-prime attribute depends on a proper subset of a candidate key
  | NF3  -- every non-trivial X → A has X a superkey or A prime
  | EKNF -- every elementary FD X → A has X a superkey or A on an elementary key
  | BCNF -- every non-trivial FD has a superkey determinant
  | NF4  -- every non-trivial multivalued dependency has a superkey determinant
  | ETNF -- every implied non-trivial join dependency has a superkey component
  | NF5  -- every implied join dependency is implied by the candidate keys
  | NF6  -- every join dependency is trivial
  | DKNF -- every constraint follows from domains and keys; unrestricted membership is undecidable
  | BQNF -- change boundary; exact defects repair, missing extremum witnesses recompute
  deriving Repr, DecidableEq

/-- Boyce-Codd checker. The input list contains non-trivial functional dependencies.
    A dependency whose right side sits inside its left side is not an input.
    Compliance means every determinant in the list is a superkey. -/
def is_bcnf_compliant (is_superkey : List Attribute → Bool) (fds : List FunctionalDependency) : Bool :=
  fds.all (fun fd => is_superkey fd.det)

/-- Third-normal-form checker for non-trivial dependencies X → Y.
    Compliance means each determinant is a superkey, or every attribute of Y is prime.
    That is Zaniolo's condition. -/
def is_3nf_compliant (is_superkey : List Attribute → Bool) (is_prime : Attribute → Bool) (fds : List FunctionalDependency) : Bool :=
  fds.all (fun fd => is_superkey fd.det || fd.dep.all is_prime)

/-- A list that passes the Boyce-Codd checker also passes the third-normal-form checker. -/
theorem bcnf_implies_3nf (is_superkey : List Attribute → Bool) (is_prime : Attribute → Bool) (fds : List FunctionalDependency) :
    is_bcnf_compliant is_superkey fds = true → is_3nf_compliant is_superkey is_prime fds = true := by
  intro h_bcnf
  unfold is_bcnf_compliant at h_bcnf
  unfold is_3nf_compliant
  rw [List.all_eq_true] at h_bcnf ⊢
  intro fd h_in
  have h_det := h_bcnf fd h_in
  simp [h_det]

/-- One body against one ternary join dependency.
    shell2 is the join of the three binary projections.
    fill2 is the admitted body.
    Equal cardinality means this body obeys this join dependency.
    Fifth normal form is a different statement: every join dependency implied
    by the schema constraints is implied by the candidate keys. -/
structure TernaryJoinInstanceWitness where
  shell2_cardinality : Nat
  fill2_cardinality : Nat
  body_obeys_join_dependency : Bool := shell2_cardinality == fill2_cardinality

/-- BQNF (Boundary-Quotient Normal Form) Exactness Structure:
    Governs data in motion under Change Data Capture (CDC).
    Defect ω ∈ C^1.
    Exact repair α ∈ C^0 such that ω = d^0 α.
    Terminal route is Repair if exact repair exists, otherwise Invalidate. -/
inductive BQNFTerminalRoute where
  | Preserve
  | Repair
  | Invalidate
  | Recompute
  | Serialize
  | Refuse
  deriving Repr, DecidableEq

structure BQNFState where
  has_defect : Bool
  is_exact_boundary : Bool -- ω = d^0 α
  coboundary_closed : Bool  -- d^1 ω = 0
  deriving Repr

def bqnf_terminal_routing (s : BQNFState) : BQNFTerminalRoute :=
  if !s.has_defect then
    BQNFTerminalRoute.Preserve
  else if s.is_exact_boundary then
    BQNFTerminalRoute.Repair
  else if s.coboundary_closed then
    BQNFTerminalRoute.Invalidate
  else
    BQNFTerminalRoute.Refuse

/-- THEOREM: Zero defect preserves state without repair or invalidation -/
theorem bqnf_zero_defect_preserves (is_exact : Bool) (is_closed : Bool) :
    bqnf_terminal_routing { has_defect := false, is_exact_boundary := is_exact, coboundary_closed := is_closed } = BQNFTerminalRoute.Preserve := by
  rfl

/-- THEOREM: An exact defect (ω = d^0 α) always routes to deterministic Repair -/
theorem bqnf_exact_defect_repairs (is_closed : Bool) :
    bqnf_terminal_routing { has_defect := true, is_exact_boundary := true, coboundary_closed := is_closed } = BQNFTerminalRoute.Repair := by
  rfl

/-- Non-invertible aggregate types (e.g. MIN, MAX) -/
inductive NonInvertibleAggregateKind where
  | Min
  | Max
  deriving Repr, DecidableEq

/-- Priority Queue Cochain status for non-invertible aggregate maintenance -/
structure PriorityQueueCochain where
  has_elements : Bool
  top_is_extremum : Bool := true
  deriving Repr

/-- Deletion event on an aggregate relvar containing non-invertible extrema -/
structure NonInvertibleDeletionEvent where
  deleted_is_extremum : Bool
  cochain : Option PriorityQueueCochain
  deriving Repr

/-- Protocol for non-invertible aggregate repair under CDC deletion:
    1. If the deleted element was not the extremum (non-destructive deletion),
       the defect is trivially exact: Route to Repair (extremum preserved).
    2. If the deleted element was the extremum (destructive deletion):
       a. If an auxiliary priority queue cochain is available and non-empty,
          the next extremum is resolved via cochain potential: Route to Repair.
       b. If no cochain is available or cochain is exhausted,
          the defect is non-exact ([ω] ≠ 0): Route to Recompute (bounded fallback). -/
def non_invertible_aggregate_repair_routing (event : NonInvertibleDeletionEvent) : BQNFTerminalRoute :=
  if !event.deleted_is_extremum then
    BQNFTerminalRoute.Repair
  else
    match event.cochain with
    | some pq =>
      if pq.has_elements then
        BQNFTerminalRoute.Repair
      else
        BQNFTerminalRoute.Recompute
    | none =>
      BQNFTerminalRoute.Recompute

/-- THEOREM: Non-destructive deletion (deleted element ≠ extremum) preserves extremum with exact Repair -/
theorem non_destructive_deletion_preserves_extremum (cochain : Option PriorityQueueCochain) :
    non_invertible_aggregate_repair_routing { deleted_is_extremum := false, cochain := cochain } = BQNFTerminalRoute.Repair := by
  rfl

/-- THEOREM: Destructive deletion with an active priority queue cochain yields exact cochain Repair -/
theorem destructive_deletion_with_cochain_repairs :
    non_invertible_aggregate_repair_routing { deleted_is_extremum := true, cochain := some { has_elements := true, top_is_extremum := true } } = BQNFTerminalRoute.Repair := by
  rfl

/-- THEOREM: Destructive deletion without a priority queue cochain forces bounded Recompute -/
theorem destructive_deletion_without_cochain_forces_recompute :
    non_invertible_aggregate_repair_routing { deleted_is_extremum := true, cochain := none } = BQNFTerminalRoute.Recompute := by
  rfl

/-- THEOREM: Destructive deletion with exhausted cochain forces bounded Recompute -/
theorem destructive_deletion_with_exhausted_cochain_forces_recompute :
    non_invertible_aggregate_repair_routing { deleted_is_extremum := true, cochain := some { has_elements := false, top_is_extremum := true } } = BQNFTerminalRoute.Recompute := by
  rfl

/-- Maximum of a finite list of natural numbers (0 on empty list) -/
def maxL : List Nat → Nat
  | [] => 0
  | x :: xs => Nat.max x (maxL xs)

/-- Erase the first occurrence of value v from a list of natural numbers -/
def eraseFirst (v : Nat) : List Nat → List Nat
  | [] => []
  | x :: xs => if x == v then xs else x :: eraseFirst v xs

/-- Destructive deletion of the current maximum element from a dataset -/
def eraseMax (xs : List Nat) : List Nat :=
  eraseFirst (maxL xs) xs

/-- 2-cochain normalizer N_2(xs) = (max(xs), max(eraseMax(xs))) tracking (extremum, runner_up) -/
def extremum2Cochain (xs : List Nat) : Nat × Nat :=
  (maxL xs, maxL (eraseMax xs))

/-- Quotient transition operator on the 2-cochain representation after deleting the maximum -/
def deleteMaxCochain (c : Nat × Nat) : Nat :=
  c.2

/-- THEOREM: Scalar maximum alone fails quotient descent under destructive deletion.
    Witness: xs = [10, 9] and ys = [10, 2] share maxL = 10, but after deleting the maximum
    their post-deletion maxima diverge (9 ≠ 2). -/
theorem scalar_max_fails_quotient_descent :
    ∃ (xs ys : List Nat), maxL xs = maxL ys ∧ maxL (eraseMax xs) ≠ maxL (eraseMax ys) := by
  refine ⟨[10, 9], [10, 2], ?_, ?_⟩
  · decide
  · decide

/-- THEOREM: Equipping datasets with the 2-cochain normalizer extremum2Cochain = (max, runner_up)
    satisfies the normalization commutative square (maxL ∘ eraseMax = deleteMaxCochain ∘ extremum2Cochain),
    preserves quotient descent of the post-deletion extremum across equivalent datasets, and
    routes active priority-queue cochains deterministically to Repair. -/
theorem extremum_cochain_quotient_descent (xs ys : List Nat)
    (pq1 pq2 : PriorityQueueCochain)
    (h_equiv : extremum2Cochain xs = extremum2Cochain ys)
    (h1 : pq1.has_elements = true) (h2 : pq2.has_elements = true) :
    maxL (eraseMax xs) = deleteMaxCochain (extremum2Cochain xs) ∧
    maxL (eraseMax xs) = maxL (eraseMax ys) ∧
    non_invertible_aggregate_repair_routing { deleted_is_extremum := true, cochain := some pq1 } = BQNFTerminalRoute.Repair ∧
    non_invertible_aggregate_repair_routing { deleted_is_extremum := true, cochain := some pq2 } = BQNFTerminalRoute.Repair := by
  refine ⟨rfl, ?_, ?_, ?_⟩
  · have h_snd := congrArg Prod.snd h_equiv
    simpa [extremum2Cochain] using h_snd
  · simp [non_invertible_aggregate_repair_routing, h1]
  · simp [non_invertible_aggregate_repair_routing, h2]

/-- Higher-order quantile sketch cochain status with declared epsilon tolerance -/
structure QuantileSketchCochain where
  count : Nat
  error_bound_scaled : Nat  -- e.g. integer basis points: |estimated - true| * 10000
  tolerance_scaled : Nat    -- epsilon * 10000
  deriving Repr

/-- Streaming deletion event on a quantile-tracked relvar -/
structure QuantileDeletionEvent where
  sketch : Option QuantileSketchCochain
  deriving Repr

/-- Protocol for epsilon-BQNF quantile sketch repair routing:
    1. If no sketch cochain is available or sketch is empty (count = 0),
       the defect cannot be estimated: Route to Recompute.
    2. If sketch is available and error_bound_scaled <= tolerance_scaled:
       the defect cochain lies within the declared quotient tolerance ball [ω] ∈ B_ε(0):
       Route to Repair.
    3. If error_bound_scaled > tolerance_scaled:
       the approximation defect breaches the quotient tolerance:
       Route to Recompute (bounded fallback recomputation). -/
def quantile_sketch_repair_routing (event : QuantileDeletionEvent) : BQNFTerminalRoute :=
  match event.sketch with
  | none => BQNFTerminalRoute.Recompute
  | some s =>
    if s.count = 0 then
      BQNFTerminalRoute.Recompute
    else if s.error_bound_scaled ≤ s.tolerance_scaled then
      BQNFTerminalRoute.Repair
    else
      BQNFTerminalRoute.Recompute

/-- THEOREM: When quantile sketch error is within declared epsilon tolerance, routes to Repair -/
theorem quantile_within_tolerance_repairs (c : Nat) (h_cnt : c > 0) (err tol : Nat) (h_err : err ≤ tol) :
    quantile_sketch_repair_routing { sketch := some { count := c, error_bound_scaled := err, tolerance_scaled := tol } } = BQNFTerminalRoute.Repair := by
  unfold quantile_sketch_repair_routing
  have hc : ¬ (c = 0) := Nat.ne_of_gt h_cnt
  simp [hc, h_err]

/-- THEOREM: When quantile sketch error exceeds declared epsilon tolerance, forces Recompute -/
theorem quantile_exceeding_tolerance_forces_recompute (c : Nat) (h_cnt : c > 0) (err tol : Nat) (h_err : err > tol) :
    quantile_sketch_repair_routing { sketch := some { count := c, error_bound_scaled := err, tolerance_scaled := tol } } = BQNFTerminalRoute.Recompute := by
  unfold quantile_sketch_repair_routing
  have hc : ¬ (c = 0) := Nat.ne_of_gt h_cnt
  have hnot : ¬ (err ≤ tol) := Nat.not_le_of_gt h_err
  simp [hc, hnot]

/-- THEOREM: Empty quantile sketch cochain forces Recompute -/
theorem empty_quantile_sketch_forces_recompute (err tol : Nat) :
    quantile_sketch_repair_routing { sketch := some { count := 0, error_bound_scaled := err, tolerance_scaled := tol } } = BQNFTerminalRoute.Recompute := by
  rfl

/-- THEOREM: Missing quantile sketch cochain forces Recompute -/
theorem missing_quantile_sketch_forces_recompute :
    quantile_sketch_repair_routing { sketch := none } = BQNFTerminalRoute.Recompute := by
  rfl

/-- Terminal route for observer-relative freshness evaluation -/

inductive FreshnessTerminalRoute where
  | Refuse
  | ConservativeInvalidate
  | RefreshRequired
  | AuthorizedFresh
  deriving Repr, DecidableEq

/-- A read packet carrying optional replica lag evidence and access scope -/
structure FreshnessPacket where
  replica_lag_seconds : Option Nat
  packet_scope : String
  deriving Repr

/-- Observer specification declaring SLA budget tolerance and authorized scopes -/
structure ObserverSpec where
  observer_id : String
  max_lag_seconds : Nat
  authorized_scopes : List String
  deriving Repr

/-- Operational step-function evaluating freshness for a declared observer.
    Matches 03-observer-relative-freshness.py:
    1. Scope access check: if packet scope is not in authorized_scopes, Refuse.
    2. Lag evidence check: if replica lag is missing/null, ConservativeInvalidate.
    3. SLA budget check: if lag ≤ max_lag, AuthorizedFresh; else RefreshRequired. -/
def evaluate_observer_freshness (obs : ObserverSpec) (pkt : FreshnessPacket) : FreshnessTerminalRoute :=
  if pkt.packet_scope ∉ obs.authorized_scopes then
    FreshnessTerminalRoute.Refuse
  else
    match pkt.replica_lag_seconds with
    | none => FreshnessTerminalRoute.ConservativeInvalidate
    | some lag =>
      if lag ≤ obs.max_lag_seconds then
        FreshnessTerminalRoute.AuthorizedFresh
      else
        FreshnessTerminalRoute.RefreshRequired

/-- Binary authorization predicate: only AuthorizedFresh grants active authorization -/
def is_freshness_authorized (route : FreshnessTerminalRoute) : Bool :=
  route == FreshnessTerminalRoute.AuthorizedFresh

/-- Preorder relation on Observers:
    Observer A is more stringent than Observer B (A ⊑ B) if:
    1. A has tighter or equal SLA lag budget (A.max_lag ≤ B.max_lag)
    2. A has smaller or equal scope capability (A.scopes ⊆ B.scopes) -/
def ObserverLeq (a b : ObserverSpec) : Prop :=
  a.max_lag_seconds ≤ b.max_lag_seconds ∧
  ∀ s, s ∈ a.authorized_scopes → s ∈ b.authorized_scopes

/-- Reflexivity of Observer Poset Preorder -/
theorem observer_leq_refl (o : ObserverSpec) : ObserverLeq o o :=
  ⟨Nat.le_refl o.max_lag_seconds, fun _ hs => hs⟩

/-- Transitivity of Observer Poset Preorder -/
theorem observer_leq_trans (o1 o2 o3 : ObserverSpec) :
    ObserverLeq o1 o2 → ObserverLeq o2 o3 → ObserverLeq o1 o3 :=
  fun ⟨h1, s1⟩ ⟨h2, s2⟩ => ⟨Nat.le_trans h1 h2, fun s hs => s2 s (s1 s hs)⟩

/-- THEOREM: Scope Authorization Firewall Precedence.
    If observer lacks scope access, routing is Refuse regardless of lag value or evidence presence. -/
theorem scope_firewall_precedence (obs : ObserverSpec) (pkt : FreshnessPacket)
    (h_scope : pkt.packet_scope ∉ obs.authorized_scopes) :
    evaluate_observer_freshness obs pkt = FreshnessTerminalRoute.Refuse := by
  unfold evaluate_observer_freshness
  simp [h_scope]

/-- THEOREM: Missing Evidence Conservative Invalidation.
    If scope is authorized but lag metadata is absent (none), routing is ConservativeInvalidate
    regardless of observer SLA budget size. -/
theorem missing_evidence_conservative_invalidation (obs : ObserverSpec) (pkt : FreshnessPacket)
    (h_scope : pkt.packet_scope ∈ obs.authorized_scopes)
    (h_lag : pkt.replica_lag_seconds = none) :
    evaluate_observer_freshness obs pkt = FreshnessTerminalRoute.ConservativeInvalidate := by
  unfold evaluate_observer_freshness
  simp [h_scope, h_lag]

/-- THEOREM: SLA Budget Step-Function Routing (Fresh).
    When scope is authorized and lag is within the observer SLA budget, routes to AuthorizedFresh. -/
theorem sla_budget_step_routing_fresh (obs : ObserverSpec) (pkt : FreshnessPacket) (lag : Nat)
    (h_scope : pkt.packet_scope ∈ obs.authorized_scopes)
    (h_lag : pkt.replica_lag_seconds = some lag)
    (h_le : lag ≤ obs.max_lag_seconds) :
    evaluate_observer_freshness obs pkt = FreshnessTerminalRoute.AuthorizedFresh := by
  unfold evaluate_observer_freshness
  simp [h_scope, h_lag, h_le]

/-- THEOREM: SLA Budget Step-Function Routing (Stale).
    When scope is authorized and lag exceeds the observer SLA budget, routes to RefreshRequired. -/
theorem sla_budget_step_routing_stale (obs : ObserverSpec) (pkt : FreshnessPacket) (lag : Nat)
    (h_scope : pkt.packet_scope ∈ obs.authorized_scopes)
    (h_lag : pkt.replica_lag_seconds = some lag)
    (h_gt : ¬ (lag ≤ obs.max_lag_seconds)) :
    evaluate_observer_freshness obs pkt = FreshnessTerminalRoute.RefreshRequired := by
  unfold evaluate_observer_freshness
  simp [h_scope, h_lag, h_gt]

/-- THEOREM: Observer-Relative Monotonicity Functor.
    Authorization is monotonic with respect to the observer poset preorder:
    If a packet is authorized and fresh for a more stringent observer o1,
    it is guaranteed fresh and authorized for any more permissive observer o2 (o1 ⊑ o2). -/
theorem observer_relative_monotonicity (o1 o2 : ObserverSpec) (pkt : FreshnessPacket)
    (h_ord : ObserverLeq o1 o2)
    (h_auth : evaluate_observer_freshness o1 pkt = FreshnessTerminalRoute.AuthorizedFresh) :
    evaluate_observer_freshness o2 pkt = FreshnessTerminalRoute.AuthorizedFresh := by
  unfold evaluate_observer_freshness at h_auth ⊢
  by_cases h_sc1 : pkt.packet_scope ∉ o1.authorized_scopes
  · simp [h_sc1] at h_auth
  · simp [h_sc1] at h_auth
    have h_mem1 : pkt.packet_scope ∈ o1.authorized_scopes := by
      cases Decidable.em (pkt.packet_scope ∈ o1.authorized_scopes) with
      | inl h => exact h
      | inr h => exact False.elim (h_sc1 h)
    have h_mem2 : pkt.packet_scope ∈ o2.authorized_scopes := h_ord.2 pkt.packet_scope h_mem1
    have h_sc2 : ¬ (pkt.packet_scope ∉ o2.authorized_scopes) := fun h => h h_mem2
    simp [h_sc2]
    match h_lag : pkt.replica_lag_seconds with
    | none =>
      simp [h_lag] at h_auth
    | some lag =>
      simp [h_lag] at h_auth ⊢
      have h_le2 : lag ≤ o2.max_lag_seconds := Nat.le_trans h_auth h_ord.1
      simp [h_le2]

/-- THEOREM: Observer Relativity / Asymmetric Evaluation.
    Two observers evaluating the identical packet can resolve to distinct terminal routes
    when the packet lag falls strictly between their respective SLA thresholds. -/
theorem observer_relativity_asymmetry (o1 o2 : ObserverSpec) (pkt : FreshnessPacket) (lag : Nat)
    (h_scope1 : pkt.packet_scope ∈ o1.authorized_scopes)
    (h_scope2 : pkt.packet_scope ∈ o2.authorized_scopes)
    (h_lag : pkt.replica_lag_seconds = some lag)
    (h_stale1 : ¬ (lag ≤ o1.max_lag_seconds))
    (h_fresh2 : lag ≤ o2.max_lag_seconds) :
    evaluate_observer_freshness o1 pkt = FreshnessTerminalRoute.RefreshRequired ∧
    evaluate_observer_freshness o2 pkt = FreshnessTerminalRoute.AuthorizedFresh := by
  constructor
  · exact sla_budget_step_routing_stale o1 pkt lag h_scope1 h_lag h_stale1
  · exact sla_budget_step_routing_fresh o2 pkt lag h_scope2 h_lag h_fresh2

/-- Discrete 1-cochain over 4 edges of a directed cycle C_4 -/
structure DiscreteCycle4Cochain where
  e0 : Int
  e1 : Int
  e2 : Int
  e3 : Int
  deriving Repr, DecidableEq

/-- Discrete inner product of two 1-cochains on C_4 -/
def dotProduct4 (a b : DiscreteCycle4Cochain) : Int :=
  a.e0 * b.e0 + a.e1 * b.e1 + a.e2 * b.e2 + a.e3 * b.e3

/-- Coboundary operator d₀ mapping vertex potentials (α₀, α₁, α₂, α₃) to 1-cochain on C_4 -/
def d0_cycle4 (α0 α1 α2 α3 : Int) : DiscreteCycle4Cochain :=
  ⟨α1 - α0, α2 - α1, α3 - α2, α0 - α3⟩

/-- Harmonic cochain on C_4: constant circulation k across all 4 edges -/
def harmonic_cycle4 (k : Int) : DiscreteCycle4Cochain :=
  ⟨k, k, k, k⟩

/-- THEOREM: Discrete Hodge Orthogonal Decomposition (DHNF).
    On a discrete cycle C_4, the inner product of any exact cochain d₀(α)
    with any harmonic cochain h vanishes identically: ⟨d₀ α, h⟩ = 0. -/
theorem hodge_orthogonal_decomposition (α0 α1 α2 α3 k : Int) :
    dotProduct4 (d0_cycle4 α0 α1 α2 α3) (harmonic_cycle4 k) = 0 := by
  dsimp [dotProduct4, d0_cycle4, harmonic_cycle4]
  have hDistrib : (α1 - α0) * k + (α2 - α1) * k + (α3 - α2) * k + (α0 - α3) * k =
      ((((α1 - α0) + (α2 - α1)) + (α3 - α2)) + (α0 - α3)) * k := by
    rw [Int.add_mul, Int.add_mul, Int.add_mul]
  rw [hDistrib]
  have hZero : (((α1 - α0) + (α2 - α1)) + (α3 - α2)) + (α0 - α3) = 0 := by omega
  rw [hZero]
  exact Int.zero_mul k

/-- Binary gauge transformation on signed Hamiltonian edges:
    Edge sign s ∈ {-1, 1}, vertex gauge bits v_src, v_dst ∈ {0, 1}.
    Transformed sign: s * (-1)^(v_src + v_dst). -/
def bssnf_gauge_transform (s : Int) (v_src v_dst : Nat) : Int :=
  s * (if (v_src + v_dst) % 2 = 1 then -1 else 1)

/-- THEOREM: Binary Sign-Switching Gauge Elimination (BSS-NF).
    For any signed edge s ∈ {-1, 1} and initial gauge v_src, choosing
    v_dst = (v_src + if s = -1 then 1 else 0) % 2 strictly eliminates the sign defect,
    yielding transformed sign +1. -/
theorem bssnf_gauge_sign_elimination (s : Int) (v_src : Nat) (hs : s = 1 ∨ s = -1) :
    let v_dst := (v_src + if s = -1 then 1 else 0) % 2
    bssnf_gauge_transform s v_src v_dst = 1 := by
  intro v_dst
  unfold bssnf_gauge_transform
  rcases hs with (rfl | rfl)
  · dsimp [v_dst]
    have hmod : (v_src + v_src % 2) % 2 = 0 := by omega
    simp [hmod]
  · dsimp [v_dst]
    have hmod : (v_src + (v_src + 1) % 2) % 2 = 1 := by omega
    simp [hmod]

/-- Meron Involution Pair: opposite signs s1 = 1, s2 = -1 and equal weight w -/
structure MeronPair where
  weight : Int
  sign1 : Int
  sign2 : Int
  h_sign1 : sign1 = 1
  h_sign2 : sign2 = -1
  deriving Repr

/-- THEOREM: Meron Involutive Cancellation (MIC-NF).
    On the uncancelled sector S₀, fixed-point-free involution pairs with equal weights
    and opposite signs algebraically cancel to zero: w * 1 + w * (-1) = 0. -/
theorem micnf_involutive_cancellation (p : MeronPair) :
    p.weight * p.sign1 + p.weight * p.sign2 = 0 := by
  have hs1 := p.h_sign1
  have hs2 := p.h_sign2
  rw [hs1, hs2]
  rw [Int.mul_one, Int.mul_neg, Int.mul_one]
  exact Int.add_right_neg p.weight

/-- Terminal route for Zero-Float LP Duality evaluation -/
inductive ZFNFTerminalRoute where
  | Preserve
  | Escalate
  deriving Repr, DecidableEq

def zfnf_duality_route (gap : Int) : ZFNFTerminalRoute :=
  if gap = 0 then ZFNFTerminalRoute.Preserve else ZFNFTerminalRoute.Escalate

/-- THEOREM: Zero-Float Rational Duality Gap Zero (ZFNF).
    At certified optimality where duality gap dualObj - primalObj = 0,
    primal objective coincides with dual objective exactly in ℚ/ℤ. -/
theorem zfnf_rational_duality_gap_zero (primalObj dualObj : Int)
    (h_gap : dualObj - primalObj = 0) :
    primalObj = dualObj := by
  omega

/-- THEOREM: Positive Duality Gap Strictly Escalates (ZFNF).
    Any positive duality gap (gap > 0) strictly routes to Escalate, never Preserve. -/
theorem zfnf_positive_gap_escalates (gap : Int) (h_pos : gap > 0) :
    zfnf_duality_route gap = ZFNFTerminalRoute.Escalate := by
  unfold zfnf_duality_route
  have h_ne : ¬ (gap = 0) := by omega
  simp [h_ne]

/-- General 2x3 integer linear measurement operator M : ℤ³ → ℤ² -/
def observer_linear_map (m11 m12 m13 m21 m22 m23 : Int) (x y z : Int) : Int × Int :=
  (m11 * x + m12 * y + m13 * z, m21 * x + m22 * y + m23 * z)

/-- Canonical coordinate projection specialization of observer_linear_map -/
def observer_projection (x y z : Int) : Int × Int :=
  observer_linear_map 1 0 0 0 1 0 x y z

/-- THEOREM: Epistemic Quotient Kernel Invariance (EQNF).
    For any 2x3 integer linear measurement operator M and any perturbation vector
    (δx, δy, δz) lying in ker(M) (i.e. M(δx, δy, δz) = (0, 0)),
    translating the state by (δx, δy, δz) preserves the observed quotient class M(x, y, z). -/
theorem eqnf_kernel_quotient_invariance
    (m11 m12 m13 m21 m22 m23 : Int)
    (x y z δx δy δz : Int)
    (h_ker : observer_linear_map m11 m12 m13 m21 m22 m23 δx δy δz = (0, 0)) :
    observer_linear_map m11 m12 m13 m21 m22 m23 (x + δx) (y + δy) (z + δz) =
    observer_linear_map m11 m12 m13 m21 m22 m23 x y z := by
  unfold observer_linear_map at h_ker ⊢
  have h1 : m11 * δx + m12 * δy + m13 * δz = 0 := congrArg Prod.fst h_ker
  have h2 : m21 * δx + m22 * δy + m23 * δz = 0 := congrArg Prod.snd h_ker
  apply Prod.ext
  · dsimp
    rw [Int.mul_add, Int.mul_add, Int.mul_add]
    omega
  · dsimp
    rw [Int.mul_add, Int.mul_add, Int.mul_add]
    omega

/-- Tableau cell coordinate (row, column) -/
structure TableauCoord where
  row : Nat
  col : Nat
  deriving DecidableEq, Repr

/-- Predicate: A row r has all columns distinguished under equivalence relation eqv
    relative to a distinguished symbol coordinate dist c -/
def row_is_distinguished (eqv : TableauCoord → TableauCoord → Prop)
    (dist : Nat → TableauCoord) (num_cols : Nat) (r : Nat) : Prop :=
  ∀ c : Nat, c < num_cols → eqv ⟨r, c⟩ (dist c)

/-- THEOREM: Equivalence refinement preserves distinguished row.
    If partition eqv₁ is a sub-relation of eqv₂ (eqv₁ ⊆ eqv₂),
    and row r is all-distinguished under eqv₁, then row r is all-distinguished under eqv₂. -/
theorem chase_partition_refinement_preserves_distinguished_row
    (eqv1 eqv2 : TableauCoord → TableauCoord → Prop)
    (dist : Nat → TableauCoord) (num_cols r : Nat)
    (h_refine : ∀ c1 c2, eqv1 c1 c2 → eqv2 c1 c2)
    (h_dist1 : row_is_distinguished eqv1 dist num_cols r) :
    row_is_distinguished eqv2 dist num_cols r := by
  intro c hc
  exact h_refine ⟨r, c⟩ (dist c) (h_dist1 c hc)

/-- THEOREM: Chase Monotonicity Theorem (Aho-Beeri-Ullman 1979).
    If there exists an all-distinguished row under the sub-congruence eqv₁,
    then there exists an all-distinguished row under any coarser congruence eqv₂. -/
theorem chase_monotonicity_distinguished_row_exists
    (eqv1 eqv2 : TableauCoord → TableauCoord → Prop)
    (dist : Nat → TableauCoord) (num_cols : Nat)
    (h_refine : ∀ c1 c2, eqv1 c1 c2 → eqv2 c1 c2)
    (h_exists1 : ∃ r, row_is_distinguished eqv1 dist num_cols r) :
    ∃ r, row_is_distinguished eqv2 dist num_cols r := by
  rcases h_exists1 with ⟨r, hr⟩
  exact ⟨r, chase_partition_refinement_preserves_distinguished_row eqv1 eqv2 dist num_cols r h_refine hr⟩

end NormalForms



