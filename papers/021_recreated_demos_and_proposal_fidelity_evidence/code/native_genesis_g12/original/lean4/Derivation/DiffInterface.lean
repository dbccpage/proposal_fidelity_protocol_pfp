/-!
# A native primitive-difference interface

Externally imposed challenge (caller request, 2026-08-12): a
self-contained theorem package exposing the pipeline

    reflection certificate → retained/protected zero-pair
      → active obstruction → map-saturated closure step
      or separately represented extension proposal.

Everything here is built from core Lean only; nothing is assumed about
any downstream consumer.  An independent adapter mapping these native
definitions into other types is the caller's evidence, out of scope
here by design.

Discipline carried over from the development: the three obstruction
conditions (retained / observer-zero / protected) are separate
predicates, never conflated; proposals are data, never applied;
equivalence is proved before any quotient is constructed; the abstract
demand carrier is a predicate, so closure does not choose a preferred
representative; and every countermodel is a concrete finite instance.
-/

namespace DiffInterface

variable {X X' R V : Type}

/-! ## The typed difference operation

`δ : X → X → R` with `Zero : R → Prop`.  The equivalence laws are
*fields*: an observer is admitted only together with its proofs. -/

structure DiffObs (X R : Type) where
  delta : X → X → R
  Zero : R → Prop
  zero_refl : ∀ x, Zero (delta x x)
  zero_symm : ∀ {x y}, Zero (delta x y) → Zero (delta y x)
  zero_trans : ∀ {x y z},
    Zero (delta x y) → Zero (delta y z) → Zero (delta x z)

/-- `ZeroRel x y` iff the observer's difference value is zero. -/
def ZeroRel (O : DiffObs X R) (x y : X) : Prop := O.Zero (O.delta x y)

/-- The equivalence proof — established *before* any quotient below. -/
theorem zeroRel_equivalence (O : DiffObs X R) :
    Equivalence (ZeroRel O) :=
  ⟨fun x => O.zero_refl x, fun h => O.zero_symm h,
   fun h1 h2 => O.zero_trans h1 h2⟩

/-- Kernel observers: the difference value of a view `v : X → V` is
the ordered pair of views, zero exactly on view-equality.  The
equivalence laws come for free — every concrete observer below is a
kernel observer. -/
def kernelObs (view : X → V) : DiffObs X (V × V) where
  delta x y := (view x, view y)
  Zero p := p.1 = p.2
  zero_refl _ := rfl
  zero_symm h := h.symm
  zero_trans h1 h2 := h1.trans h2

theorem kernel_zeroRel (view : X → V) (x y : X) :
    ZeroRel (kernelObs view) x y ↔ view x = view y := Iff.rfl

/-! ## The quotient — constructed only downstream of the equivalence

`ObsQuotient` needs the `Setoid`, which needs `zeroRel_equivalence`:
the ordering discipline is enforced by the dependency itself. -/

def obsSetoid (O : DiffObs X R) : Setoid X :=
  ⟨ZeroRel O, zeroRel_equivalence O⟩

def ObsQuotient (O : DiffObs X R) : Type := Quotient (obsSetoid O)

def ObsQuotient.mk (O : DiffObs X R) (x : X) : ObsQuotient O :=
  Quotient.mk (obsSetoid O) x

/-- The quotient identifies exactly the zero-pairs (soundness half). -/
theorem obsQuotient_eq_of_zero (O : DiffObs X R) {x y : X}
    (h : ZeroRel O x y) : ObsQuotient.mk O x = ObsQuotient.mk O y :=
  Quotient.sound h

/-! ## Stages and the three separated conditions

A stage carries a liveness designation, a retention relation, a
protection relation (`guarded` — "protected" is a reserved word; a
guarded pair is one that must eventually be distinguished), and an
observer.  The three predicates are independent fields; no coherence
between them is assumed.  The blocking lemmas below isolate each
necessary conjunct; the concrete countermodels later focus on examples
where protection is absent. -/

structure Stage (X R : Type) where
  live : X → Prop
  retained : X → X → Prop
  guarded : X → X → Prop
  obs : DiffObs X R

/-- An active obstruction is exactly the conjunction of the three
separated conditions: the pair is retained, the current observer does
not distinguish it, and it is protected. -/
def ActiveObstruction (S : Stage X R) (x y : X) : Prop :=
  S.retained x y ∧ ZeroRel S.obs x y ∧ S.guarded x y

/-- Same carrier, same result type, new observer. -/
def Stage.withObs (S : Stage X R) (O : DiffObs X R) : Stage X R :=
  { S with obs := O }

/-! Independence of the three conditions: dropping any one blocks the
conjunction.  (Used by the countermodels.) -/

theorem no_guard_no_obstruction (S : Stage X R)
    (h : ∀ x y, ¬ S.guarded x y) : ∀ x y, ¬ ActiveObstruction S x y :=
  fun x y ⟨_, _, hg⟩ => h x y hg

theorem unretained_not_active (S : Stage X R) (x y : X)
    (h : ¬ S.retained x y) : ¬ ActiveObstruction S x y :=
  fun ⟨hr, _, _⟩ => h hr

theorem distinguished_not_active (S : Stage X R) (x y : X)
    (h : ¬ ZeroRel S.obs x y) : ¬ ActiveObstruction S x y :=
  fun ⟨_, hz, _⟩ => h hz

/-! ## Bare reflection, factored

The step is a bundle of declared data: an old-to-new embedding with a
retraction, a point outside the image of every old live point, a
declared parent, preservation
of old structure (zero-pairs preserved *and reflected* on the old live
region; retention and protection preserved), and the retained,
protected parent/new pair that the pre-closure observer considers
zero. -/

structure BareReflection (S : Stage X R) (S' : Stage X' R) where
  embed : X → X'
  retract : X' → X
  retract_embed : ∀ x, retract (embed x) = x
  fresh : X'
  fresh_live : S'.live fresh
  fresh_from_live_image : ∀ x, S.live x → embed x ≠ fresh
  parent : X
  parent_live : S.live parent
  live_embed : ∀ x, S.live x → S'.live (embed x)
  zero_preserved : ∀ x y, S.live x → S.live y →
    (ZeroRel S.obs x y ↔ ZeroRel S'.obs (embed x) (embed y))
  retained_embed : ∀ x y, S.retained x y →
    S'.retained (embed x) (embed y)
  guarded_embed : ∀ x y, S.guarded x y → S'.guarded (embed x) (embed y)
  pair_retained : S'.retained (embed parent) fresh
  pair_guarded : S'.guarded (embed parent) fresh
  pair_zero : ZeroRel S'.obs (embed parent) fresh

/-- A bare-reflection certificate includes an active obstruction on its
declared parent/new pair.  The conclusion uses the certificate's three
pair fields; it is not derived from freshness alone. -/
theorem bare_reflection_certifies_active_obstruction
    {S : Stage X R} {S' : Stage X' R} (B : BareReflection S S') :
    B.embed B.parent ≠ B.fresh ∧
      ActiveObstruction S' (B.embed B.parent) B.fresh :=
  ⟨B.fresh_from_live_image _ B.parent_live,
   B.pair_retained, B.pair_zero, B.pair_guarded⟩

/-! ## Observer refinement -/

/-- `O₂` refines `O₁`: strictly fewer identifications are permitted —
every zero-pair of the refined observer was already zero before. -/
def Refines (O₂ O₁ : DiffObs X R) : Prop :=
  ∀ x y, ZeroRel O₂ x y → ZeroRel O₁ x y

/-- Refinement preserves every old distinction (the contrapositive,
stated explicitly because it is the load-bearing direction). -/
theorem refines_preserves_distinctions {O₂ O₁ : DiffObs X R}
    (h : Refines O₂ O₁) :
    ∀ x y, ¬ ZeroRel O₁ x y → ¬ ZeroRel O₂ x y :=
  fun x y h1 h2 => h1 (h x y h2)

/-! ## Preserving maps, map-saturated demands, closure steps

Demands are an abstract predicate `D : X → X → Prop`, so the closure
interface does not select a preferred representative.  Map saturation
requires closure under exchange and under every declared map.  These
maps preserve the named stage structure; no inverse or composition law
is assumed. -/

structure StageMaps (S : Stage X R) where
  maps : List (X → X)
  id_mem : (fun x => x) ∈ maps
  live_pres : ∀ g ∈ maps, ∀ x, S.live x → S.live (g x)
  retained_pres : ∀ g ∈ maps, ∀ x y,
    S.retained x y → S.retained (g x) (g y)
  guarded_pres : ∀ g ∈ maps, ∀ x y,
    S.guarded x y → S.guarded (g x) (g y)
  zero_pres : ∀ g ∈ maps, ∀ x y, S.live x → S.live y →
    ZeroRel S.obs x y → ZeroRel S.obs (g x) (g y)

def MapSaturated {S : Stage X R} (G : StageMaps S)
    (D : X → X → Prop) : Prop :=
  (∀ x y, D x y → D y x) ∧
    (∀ g ∈ G.maps, ∀ x y, D x y → D (g x) (g y))

/-- A same-carrier closure step: it discharges a map-saturated set of
demands, all of which are active obstructions, by an observer
refinement over the *same* carrier and the *same* result type. -/
structure ClosureStep (S : Stage X R) (G : StageMaps S) where
  D : X → X → Prop
  demands_active : ∀ x y, D x y → ActiveObstruction S x y
  demand_offdiag : ∀ x y, D x y → x ≠ y
  map_saturated : MapSaturated G D
  obs' : DiffObs X R
  refines : Refines obs' S.obs
  discharges : ∀ x y, D x y → x ≠ y → ¬ ZeroRel obs' x y

def ClosureStep.apply {S : Stage X R} {G : StageMaps S}
    (C : ClosureStep S G) : Stage X R := S.withObs C.obs'

/-- Closure preserves every old distinction. -/
theorem closure_preserves_old_distinctions {S : Stage X R}
    {G : StageMaps S} (C : ClosureStep S G) :
    ∀ x y, ¬ ZeroRel S.obs x y → ¬ ZeroRel C.apply.obs x y :=
  refines_preserves_distinctions C.refines

/-- Every demanded pair is off-diagonal by construction and stops being
an active obstruction. -/
theorem closure_kills_demanded {S : Stage X R} {G : StageMaps S}
    (C : ClosureStep S G) (x y : X) (hD : C.D x y) :
    ¬ ActiveObstruction C.apply x y :=
  fun ⟨_, hz, _⟩ => C.discharges x y hD (C.demand_offdiag x y hD) hz

/-- Closure creates no new active obstruction: activity after a step
pulls back to activity before it.  Together with discharge, this is an
ingredient of a decrease proof; finiteness and a removed active pair are
separate obligations, discharged for the concrete measure below. -/
theorem closure_adds_no_obstruction {S : Stage X R} {G : StageMaps S}
    (C : ClosureStep S G) (x y : X) :
    ActiveObstruction C.apply x y → ActiveObstruction S x y :=
  fun ⟨hr, hz, hg⟩ => ⟨hr, C.refines x y hz, hg⟩

/-! ## Extension proposals — data, never transitions

The interface can represent a request for a new carrier point or new
observer structure as a proposal.  Constructing one changes no stage;
authorization and proposal selection are separate acts this package
never performs. -/

inductive RequestKind where
  | carrierPoint
  | observerStructure
deriving Repr, DecidableEq

structure ExtensionProposal (X R : Type) where
  kind : RequestKind
  demanded : X → X → Prop

inductive ClosureOutcome (S : Stage X R) (G : StageMaps S) where
  | step (C : ClosureStep S G)
  | propose (p : ExtensionProposal X R)

/-! ## The fuel driver and its termination -/

inductive RunResult (σ P : Type) where
  | closed (s : σ)
  | proposal (s : σ) (p : P)
  | outOfFuel (s : σ)

def drive {σ P : Type} (next : σ → Option (σ ⊕ P)) :
    Nat → σ → RunResult σ P
  | 0, s => .outOfFuel s
  | fuel + 1, s =>
      match next s with
      | none => .closed s
      | some (.inl s') => drive next fuel s'
      | some (.inr p) => .proposal s p

/-- **Fuel termination.**  If every same-carrier step strictly
decreases a declared finite measure, then fuel exceeding the initial
measure never runs out: the driver reaches `closed` or `proposal`. -/
theorem drive_terminates {σ P : Type} (next : σ → Option (σ ⊕ P))
    (μ : σ → Nat)
    (hdec : ∀ s s', next s = some (.inl s') → μ s' < μ s) :
    ∀ fuel s, μ s < fuel →
      (∃ s', drive next fuel s = .closed s') ∨
        (∃ s' p, drive next fuel s = .proposal s' p) := by
  intro fuel
  induction fuel with
  | zero => intro s h; exact absurd h (Nat.not_lt_zero _)
  | succ f ih =>
      intro s h
      cases hn : next s with
      | none => exact Or.inl ⟨s, by simp [drive, hn]⟩
      | some v =>
          cases v with
          | inl s' =>
              have hd := hdec s s' hn
              have := ih s' (by omega)
              simpa [drive, hn] using this
          | inr p => exact Or.inr ⟨s, p, by simp [drive, hn]⟩

/-! ## The concrete realization: the reflective tower

Carrier `Nat`; result type `Nat × Nat`; the observer is the kernel of
the horizon-capped rank view `min · h`.  A closed stage at size `s`
has horizon `s - 1` (every live point has its own rank); reflection
adds a fresh point the *stale* observer cannot tell from its declared
parent; closure re-synchronizes the horizon over the full demand
predicate — uniformly, with no preferred pair chosen. -/

def cview (h i : Nat) : Nat := min i h

def mkStage (s h : Nat) : Stage Nat (Nat × Nat) where
  live i := i < s
  retained i j := i < s ∧ j < s
  guarded i j := i < s ∧ j < s ∧ i ≠ j
  obs := kernelObs (cview h)

/-- Distinctions persist under horizon growth: the capped ranks of a
lower horizon factor through any higher one. -/
theorem cview_distinct_mono {h h' i j : Nat} (hh : h ≤ h')
    (hne : cview h i ≠ cview h j) : cview h' i ≠ cview h' j := by
  intro he
  apply hne
  show min i h = min j h
  have he' : min i h' = min j h' := he
  omega

/-- A closed tower stage has no active obstruction: with horizon
`s - 1`, live ranks are injective. -/
theorem tower_closed (s : Nat) (x y : Nat)
    (h : ActiveObstruction (mkStage s (s - 1)) x y) : False := by
  obtain ⟨⟨hx, hy⟩, hz, _, _, hne⟩ := h
  have hv : min x (s - 1) = min y (s - 1) := hz
  omega

/-- The bare reflection step of the tower: identity embedding and
retraction, fresh point `n + 1`, declared parent `n`, stale observer
(horizon still `n`). -/
def towerReflection (n : Nat) :
    BareReflection (mkStage (n + 1) n) (mkStage (n + 2) n) where
  embed := fun x => x
  retract := fun x => x
  retract_embed _ := rfl
  fresh := n + 1
  fresh_live := by show n + 1 < n + 2; omega
  fresh_from_live_image := fun x hx => by
    have hx' : x < n + 1 := hx
    show x ≠ n + 1
    omega
  parent := n
  parent_live := by show n < n + 1; omega
  live_embed := fun x hx => by
    have hx' : x < n + 1 := hx
    show x < n + 2
    omega
  zero_preserved := fun x y _ _ => Iff.rfl
  retained_embed := fun x y ⟨hx, hy⟩ =>
    ⟨by show x < n + 2; omega, by show y < n + 2; omega⟩
  guarded_embed := fun x y ⟨hx, hy, hne⟩ =>
    ⟨by show x < n + 2; omega, by show y < n + 2; omega, hne⟩
  pair_retained :=
    ⟨by show n < n + 2; omega, by show n + 1 < n + 2; omega⟩
  pair_guarded :=
    ⟨by show n < n + 2; omega, by show n + 1 < n + 2; omega,
     by show n ≠ n + 1; omega⟩
  pair_zero := by
    show min n n = min (n + 1) n
    omega

/-- The tower's certificate instantiates the abstract theorem: an
active obstruction on a parent/new pair outside the old live image. -/
theorem tower_obstruction (n : Nat) :
    (n : Nat) ≠ n + 1 ∧ ActiveObstruction (mkStage (n + 2) n) n (n + 1) :=
  bare_reflection_certifies_active_obstruction (towerReflection n)

/-- A declared relation-preserving map of the pre-closure stage.  On
the live region it exchanges the two rank-collided top points. -/
def swapTop (n x : Nat) : Nat := if x < n then x else 2 * n + 1 - x

theorem swapTop_view (n x : Nat) (hx : x < n + 2) :
    cview n (swapTop n x) = cview n x := by
  unfold swapTop cview
  split <;> omega

theorem swapTop_live_inj (n x y : Nat) (hx : x < n + 2) (hy : y < n + 2)
    (h : swapTop n x = swapTop n y) : x = y := by
  unfold swapTop at h
  split at h <;> split at h <;> omega

def towerMaps (n : Nat) : StageMaps (mkStage (n + 2) n) where
  maps := [fun x => x, swapTop n]
  id_mem := List.mem_cons_self
  live_pres := by
    intro g hg x hx
    rcases List.mem_cons.mp hg with rfl | hg'
    · exact hx
    · rcases List.mem_cons.mp hg' with rfl | h0
      · have : x < n + 2 := hx
        show swapTop n x < n + 2
        unfold swapTop
        split <;> omega
      · cases h0
  retained_pres := by
    intro g hg x y hxy
    obtain ⟨hx, hy⟩ := hxy
    rcases List.mem_cons.mp hg with rfl | hg'
    · exact ⟨hx, hy⟩
    · rcases List.mem_cons.mp hg' with rfl | h0
      · constructor <;> (unfold swapTop; split <;> omega)
      · cases h0
  guarded_pres := by
    intro g hg x y hxy
    obtain ⟨hx, hy, hne⟩ := hxy
    rcases List.mem_cons.mp hg with rfl | hg'
    · exact ⟨hx, hy, hne⟩
    · rcases List.mem_cons.mp hg' with rfl | h0
      · refine ⟨?_, ?_, ?_⟩
        · unfold swapTop; split <;> omega
        · unfold swapTop; split <;> omega
        · intro he
          exact hne (swapTop_live_inj n x y hx hy he)
      · cases h0
  zero_pres := by
    intro g hg x y hx hy hz
    rcases List.mem_cons.mp hg with rfl | hg'
    · exact hz
    · rcases List.mem_cons.mp hg' with rfl | h0
      · have hx' : x < n + 2 := hx
        have hy' : y < n + 2 := hy
        show cview n (swapTop n x) = cview n (swapTop n y)
        rw [swapTop_view n x hx', swapTop_view n y hy']
        exact hz
      · cases h0

/-- The map-saturated demand predicate for the tower's obstruction:
both orientations of the collided pair. -/
def towerDemand (n : Nat) (x y : Nat) : Prop :=
  (x = n ∧ y = n + 1) ∨ (x = n + 1 ∧ y = n)

/-- The closure step of the tower: refine the observer to the new
horizon uniformly over the full demand predicate. -/
def towerClosure (n : Nat) :
    ClosureStep (mkStage (n + 2) n) (towerMaps n) where
  D := towerDemand n
  demands_active := by
    intro x y hD
    rcases hD with ⟨hx, hy⟩ | ⟨hx, hy⟩ <;> rw [hx, hy]
    · exact ⟨⟨by omega, by omega⟩,
        by show min n n = min (n+1) n; omega,
        by omega, by omega, by omega⟩
    · exact ⟨⟨by omega, by omega⟩,
        by show min (n+1) n = min n n; omega,
        by omega, by omega, by omega⟩
  demand_offdiag := by
    intro x y hD
    rcases hD with ⟨hx, hy⟩ | ⟨hx, hy⟩ <;> omega
  map_saturated := by
    constructor
    · intro x y hD
      rcases hD with ⟨hx, hy⟩ | ⟨hx, hy⟩
      · exact Or.inr ⟨hy, hx⟩
      · exact Or.inl ⟨hy, hx⟩
    · intro g hg x y hD
      rcases List.mem_cons.mp hg with rfl | hg'
      · exact hD
      · rcases List.mem_cons.mp hg' with rfl | h0
        · rcases hD with ⟨hx, hy⟩ | ⟨hx, hy⟩ <;> rw [hx, hy]
          · right
            constructor <;> (unfold swapTop; split <;> omega)
          · left
            constructor <;> (unfold swapTop; split <;> omega)
        · cases h0
  obs' := kernelObs (cview (n + 1))
  refines := by
    intro x y hz
    show min x n = min y n
    have h' : min x (n + 1) = min y (n + 1) := hz
    omega
  discharges := by
    intro x y hD _ hz
    have h' : min x (n + 1) = min y (n + 1) := hz
    rcases hD with ⟨hx, hy⟩ | ⟨hx, hy⟩ <;> omega

/-- The successor step composes exactly: applying the closure step to
the reflected stage is the next closed stage, definitionally. -/
theorem tower_step_composes (n : Nat) :
    (towerClosure n).apply = mkStage (n + 2) (n + 1) := rfl

/-- A uniform successor-step witness: for every index there is a bare
reflection and a map-saturated closure step whose application is the
next closed stage.  This theorem is pointwise; it does not construct a
trace object or prove a separate finite-prefix induction theorem. -/
theorem tower_successor_step (n : Nat) :
    ∃ (_ : BareReflection (mkStage (n + 1) n) (mkStage (n + 2) n))
      (C : ClosureStep (mkStage (n + 2) n) (towerMaps n)),
      C.apply = mkStage (n + 2) (n + 1) :=
  ⟨towerReflection n, towerClosure n, rfl⟩

/-! ## The declared finite measure and fuel termination, concretely -/

def activePairs (s h : Nat) : List (Nat × Nat) :=
  (List.range s).flatMap fun i =>
    ((List.range s).filter fun j =>
      i != j && (min i h == min j h)).map fun j => (i, j)

theorem mem_activePairs {s h i j : Nat} :
    (i, j) ∈ activePairs s h ↔
      i < s ∧ j < s ∧ i ≠ j ∧ min i h = min j h := by
  constructor
  · intro hm
    simp only [activePairs, List.mem_flatMap, List.mem_map,
               List.mem_filter, List.mem_range] at hm
    obtain ⟨a, ha, b, ⟨hb, hab⟩, heq⟩ := hm
    injection heq with h1 h2
    subst h1; subst h2
    simp only [Bool.and_eq_true, bne_iff_ne, beq_iff_eq] at hab
    exact ⟨ha, hb, hab.1, hab.2⟩
  · intro ⟨hi, hj, hne, hv⟩
    simp only [activePairs, List.mem_flatMap, List.mem_map,
               List.mem_filter, List.mem_range]
    refine ⟨i, hi, j, ⟨hj, ?_⟩, rfl⟩
    simp only [Bool.and_eq_true, bne_iff_ne, beq_iff_eq]
    exact ⟨hne, hv⟩

/-- The declared measure: the number of retained, protected,
observer-zero ordered pairs on the live region. -/
def measureC (s h : Nat) : Nat := (activePairs s h).length

/-- The measure characterizes activity in the concrete stages. -/
theorem mem_activePairs_iff_active {s h i j : Nat} (hne : i ≠ j) :
    (i, j) ∈ activePairs s h ↔
      ActiveObstruction (mkStage s h) i j := by
  rw [mem_activePairs]
  constructor
  · intro ⟨hi, hj, hne', hv⟩
    exact ⟨⟨hi, hj⟩, hv, hi, hj, hne'⟩
  · intro ⟨⟨hi, hj⟩, hz, _⟩
    exact ⟨hi, hj, hne, hz⟩

/-- A stage at full horizon is measure-zero (closed). -/
theorem closed_measure_zero (s : Nat) : measureC s (s - 1) = 0 := by
  unfold measureC
  have hnil : activePairs s (s - 1) = [] := by
    cases hp : activePairs s (s - 1) with
    | nil => rfl
    | cons p l =>
        exfalso
        have hm : p ∈ activePairs s (s - 1) := by
          rw [hp]; exact List.mem_cons_self
        obtain ⟨i, j⟩ := p
        rw [mem_activePairs] at hm
        obtain ⟨hi, hj, hne, hv⟩ := hm
        omega
  rw [hnil]
  rfl

/-- The pre-closure stage has positive measure: the reflected pair is
in it. -/
theorem preclose_measure_pos (n : Nat) : 0 < measureC (n + 2) n := by
  have hm : (n, n + 1) ∈ activePairs (n + 2) n :=
    mem_activePairs.mpr ⟨by omega, by omega, by omega, by omega⟩
  have hne := List.ne_nil_of_mem hm
  unfold measureC
  cases hp : activePairs (n + 2) n with
  | nil => exact absurd hp hne
  | cons a l => simp

/-- Concrete finite evidence for the tower demand predicate.  Unlike
the abstract predicate interface, this enumerator is a list so its
cardinality can be checked. -/
def towerDemandList (n : Nat) : List (Nat × Nat) :=
  [(n, n + 1), (n + 1, n)]

theorem tower_demand_characterized (n x y : Nat) :
    towerDemand n x y ↔ (x, y) ∈ towerDemandList n := by
  unfold towerDemand towerDemandList
  constructor
  · intro h
    rcases h with ⟨hx, hy⟩ | ⟨hx, hy⟩ <;> rw [hx, hy]
    · exact List.mem_cons_self
    · exact List.mem_cons_of_mem _ List.mem_cons_self
  · intro h
    rcases List.mem_cons.mp h with heq | h'
    · injection heq with h1 h2
      exact Or.inl ⟨h1, h2⟩
    · rcases List.mem_cons.mp h' with heq | h0
      · injection heq with h1 h2
        exact Or.inr ⟨h1, h2⟩
      · cases h0

theorem tower_demand_bound (n : Nat) : (towerDemandList n).length = 2 :=
  rfl

/-- The concrete driver: close if no active pair remains, else one
same-carrier re-synchronization.  (This family never needs an
extension — its result type has room at every horizon; the family that
has no closed view in its declared grammar is below.) -/
def towerNext (st : Nat × Nat) :
    Option ((Nat × Nat) ⊕ ExtensionProposal Nat (Nat × Nat)) :=
  if activePairs st.1 st.2 = [] then none
  else some (.inl (st.1, st.1 - 1))

theorem towerNext_decrease (st st' : Nat × Nat)
    (h : towerNext st = some (.inl st')) :
    measureC st'.1 st'.2 < measureC st.1 st.2 := by
  unfold towerNext at h
  split at h
  · cases h
  · rename_i hne
    cases h
    show measureC st.1 (st.1 - 1) < measureC st.1 st.2
    rw [closed_measure_zero]
    unfold measureC
    cases hp : activePairs st.1 st.2 with
    | nil => exact absurd hp hne
    | cons a l => simp

/-- **Fuel termination, concretely**: with fuel exceeding the declared
measure, the tower driver reaches `closed` or `proposal` — via the
strict decrease and the generic driver theorem. -/
theorem tower_fuel_terminates (s h fuel : Nat)
    (hfuel : measureC s h < fuel) :
    (∃ st, drive towerNext fuel (s, h) = .closed st) ∨
      (∃ st p, drive towerNext fuel (s, h) = .proposal st p) :=
  drive_terminates towerNext (fun st => measureC st.1 st.2)
    towerNext_decrease fuel (s, h) hfuel

/-! ## A bounded observer grammar with no closed view

Three protected points, observers drawn from the Boolean-view grammar.
Whatever view is chosen — including any refinement chosen later — two
points collide, so no view in this grammar closes the stage.  A proposal
requesting new observer structure is defined below as available data;
no theorem here derives a decision procedure that must select it. -/

theorem bool_view_pigeonhole (view : Nat → Bool) :
    view 0 = view 1 ∨ view 0 = view 2 ∨ view 1 = view 2 := by
  cases h0 : view 0 <;> cases h1 : view 1 <;> cases h2 : view 2 <;>
    decide

def bStage (view : Nat → Bool) : Stage Nat (Bool × Bool) where
  live i := i < 3
  retained i j := i < 3 ∧ j < 3
  guarded i j := i < 3 ∧ j < 3 ∧ i ≠ j
  obs := kernelObs view

/-- Every Boolean-view observer leaves an active obstruction among
three protected points. -/
theorem bool_grammar_obstruction (view : Nat → Bool) :
    ∃ x y, x ≠ y ∧ ActiveObstruction (bStage view) x y := by
  rcases bool_view_pigeonhole view with h | h | h
  · exact ⟨0, 1, by omega,
      ⟨by omega, by omega⟩, h, by omega, by omega, by omega⟩
  · exact ⟨0, 2, by omega,
      ⟨by omega, by omega⟩, h, by omega, by omega, by omega⟩
  · exact ⟨1, 2, by omega,
      ⟨by omega, by omega⟩, h, by omega, by omega, by omega⟩

/-- No Boolean view in the declared grammar closes the family. -/
theorem no_bool_view_is_closed (view : Nat → Bool) :
    ∃ x y, x ≠ y ∧ ActiveObstruction (bStage view) x y :=
  bool_grammar_obstruction view

/-- An available proposal for this family: a request for new observer
structure carrying the undischarged demand set.  Data only — no stage
is constructed from it here, and no decision theorem forces its use. -/
def boolProposal (view' : Nat → Bool) :
    ExtensionProposal Nat (Bool × Bool) :=
  { kind := .observerStructure
    demanded := fun x y =>
      x < 3 ∧ y < 3 ∧ x ≠ y ∧ ZeroRel (kernelObs view') x y }

/-! ## Countermodels

Each names a feature that does **not**, by itself, produce
observer-visible difference.  Each accompanying stage is unprotected,
and the theorem explicitly verifies that its displayed pair is not an
active obstruction.  All are concrete finite instances. -/

/-- **Freshness alone.**  The tower's new point `1` (outside the live
image of the size-1 stage) is observer-zero with its parent under the stale
horizon; with protection removed, it is not an active obstruction
either. -/
def freshUnguarded : Stage Nat (Nat × Nat) :=
  { mkStage 2 0 with guarded := fun _ _ => False }

theorem cm_freshness :
    ((0 : Nat) ≠ 1) ∧ ZeroRel (mkStage 2 0).obs 0 1 ∧
      ¬ ActiveObstruction freshUnguarded 0 1 :=
  ⟨by decide, by show cview 0 0 = cview 0 1; decide,
   no_guard_no_obstruction _ (fun _ _ h => h) 0 1⟩

/-- **Tagging alone.**  A presence tag carried by both points: the
kernel observer of the tag bit sees zero, and without protection there
is no obstruction. -/
def tagView (i : Nat) : Bool := decide (0 < i)

def tagStage : Stage Nat (Bool × Bool) :=
  { live := fun i => i < 3
    retained := fun i j => i < 3 ∧ j < 3
    guarded := fun _ _ => False
    obs := kernelObs tagView }

theorem cm_tagging :
    tagView 1 = true ∧ tagView 2 = true ∧ ((1 : Nat) ≠ 2) ∧
      ZeroRel tagStage.obs 1 2 ∧ ¬ ActiveObstruction tagStage 1 2 :=
  ⟨by decide, by decide, by decide,
   by show tagView 1 = tagView 2; decide,
   no_guard_no_obstruction _ (fun _ _ h => h) 1 2⟩

/-- **An edge alone.**  Under a symmetric incidence view, both
endpoints of the single edge look identical: an admitted relation
instance does not by itself separate (or orient) its endpoints. -/
def edgeView (i : Nat) : Bool :=
  [((0 : Nat), (1 : Nat))].any fun e => e.1 == i || e.2 == i

def edgeStage : Stage Nat (Bool × Bool) where
  live i := i < 2
  retained i j := i < 2 ∧ j < 2
  guarded := fun _ _ => False
  obs := kernelObs edgeView

theorem cm_edge :
    edgeView 0 = true ∧ edgeView 1 = true ∧ ((0 : Nat) ≠ 1) ∧
      ZeroRel edgeStage.obs 0 1 ∧ ¬ ActiveObstruction edgeStage 0 1 := by
  refine ⟨by decide, by decide, by decide, ?_,
    no_guard_no_obstruction _ (fun _ _ h => h) 0 1⟩
  show edgeView 0 = edgeView 1
  decide

/-- **A new hash alone.**  An injective label external to the observer (here
the identity) that the observer does not read: distinct hashes, zero
difference. -/
def hashStage : Stage Nat (Unit × Unit) where
  live i := i < 2
  retained i j := i < 2 ∧ j < 2
  guarded := fun _ _ => False
  obs := kernelObs (fun _ : Nat => ())

theorem cm_hash :
    (∀ i j : Nat, (fun x => x) i = (fun x => x) j → i = j) ∧
      ((0 : Nat) ≠ 1) ∧
      ZeroRel hashStage.obs 0 1 ∧ ¬ ActiveObstruction hashStage 0 1 :=
  ⟨fun _ _ h => h, by decide, rfl,
   no_guard_no_obstruction _ (fun _ _ h => h) 0 1⟩

/-- **Repetition alone.**  Two occurrence indices presenting one token:
the token view collapses them; occurrence multiplicity is invisible to
a presence-grade observer. -/
def tokenOf : Nat → Unit := fun _ => ()

def repetitionStage : Stage Nat (Unit × Unit) where
  live i := i < 2
  retained i j := i < 2 ∧ j < 2
  guarded := fun _ _ => False
  obs := kernelObs tokenOf

theorem cm_repetition :
    tokenOf 0 = tokenOf 1 ∧ ((0 : Nat) ≠ 1) ∧
      ZeroRel repetitionStage.obs 0 1 ∧
      ¬ ActiveObstruction repetitionStage 0 1 :=
  ⟨rfl, by decide, rfl,
   no_guard_no_obstruction _ (fun _ _ h => h) 0 1⟩

end DiffInterface
