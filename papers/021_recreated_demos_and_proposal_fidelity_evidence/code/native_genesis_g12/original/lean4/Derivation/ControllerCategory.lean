import Derivation.PrimitivePassage

/-!
# The controller category and the initiality test

Stage VII of the contact-and-passage run.  The sealed six-toggle
constitution family answered minimality *inside a declared 64-member
class of guard toggles* (`Initiality.unique_compliant`, whose own
scope note restricts the claim to that class and probe battery).
This module widens the comparison class along a genuinely different
axis: **variable event grammars**.  A controller enables or disables
each of the ten event kinds of the passage dynamics wholesale and
interprets every enabled event by the sealed passage step.  The class
has 1024 members, completely enumerated (`allKinds_length`,
`allKinds_complete` — "complete" carries exactly this proof).

Results, with exact scope:

* the all-on controller executes exactly the sealed step
  (`interpK_full`);
* the two-rule response universe is supported by exactly the three
  response kinds (`refineCol`, `addCol`, `setBudget`): every live
  controller executes the funded extension block at the concrete
  obstructed funded state `OBST5` and resolves the obstruction
  (`tworule_executable_of_live`, generic over all 128 live members),
  and switching any one response kind off alone kills the resolution
  path on a state where that kind is load-bearing — three
  countermodels over declared finite batteries
  (`dead_without_addcol`, `dead_without_budget`,
  `dead_without_refine`);
* **non-uniqueness** (`live_census`, `nonrefuse_agree`,
  `refuse_distinguishes`): the live set has 128 members; the all-on
  controller and its refusal-free variant agree on every refusal-free
  event at every state, yet differ at a certified obstruction on a
  refuse event.  Probe-style compliance in this broad class does not
  pin a unique controller; the sealed six-toggle uniqueness is
  class-relative, exactly as its scope note states;
* **the category**: objects are controllers, morphisms are
  simulations — state maps commuting with the interpreted step.
  Identity, composition, and the category laws are proved (`comp_id`,
  `id_comp`, `comp_assoc`, via `sim_ext`).  Refusal erasure is a
  genuine non-identity morphism from the all-on controller to its
  refusal-free variant (`eraseSim`);
* **initiality is refuted** (`no_initial_ctrl`,
  `no_initial_live_ctrl`): every constant map to a halted state is a
  simulation between any two controllers (`constSim`), because the
  terminal is absorbing (`PrimitivePassage.step_halted`).  Two
  distinct halted states give two distinct simulations from every
  source into the all-on controller, so *no* object has the
  unique-morphism property — while every ordered pair of objects is
  connected (`every_pair_connected`).  Morphism existence is trivial
  in this category; the whole content of the initiality question
  lives in uniqueness, and uniqueness fails everywhere
  (`sims_never_unique`);
* **the strict refinement and its exact boundary**: `StrictSim`
  demands genesis preservation and preservation of the non-halted
  flag.  The constant collapses are excluded (`const_not_strict`);
  identity and refusal erasure survive (`idStrict`, `eraseStrict`).
  Global uniqueness *still* fails: a bidirectionally step-invariant
  predicate that is false at genesis — a duplicated occurrence store,
  unreachable because admission dedups (`reachable_no_dup`) —
  parameterizes a second strict simulation (`twistStrict`,
  `strict_not_unique`).  The exact boundary is proved on the other
  side: any two genesis-preserving simulations agree on every state
  replayed from genesis (`genesis_sims_agree_on_reachable`,
  `strict_agree_on_reachable`).  Uniqueness of the erasure morphism
  is a property of the reachable orbit, not of the raw state space;
  a further refinement (morphisms of reachable-state restrictions)
  is the recorded boundary, not claimed here.
-/

namespace ControllerCategory

open PrimitivePassage

/- The class enumeration has 1024 members; kernel evaluation of its
length and filters recurses once per member. -/
set_option maxRecDepth 8192

/-! ## The comparison class: variable event grammars -/

/-- A controller: one enable bit per event kind of the passage
dynamics.  A data family, completely enumerated below. -/
structure KindDesc where
  kAdmitOcc : Bool
  kAdmitWit : Bool
  kProtect : Bool
  kDeclareObs : Bool
  kRefineCol : Bool
  kAddCol : Bool
  kRefuse : Bool
  kSetBudget : Bool
  kSetLicense : Bool
  kHalt : Bool
deriving Repr, DecidableEq

/-- Whether the controller enables an event, read off its kind. -/
def enabled (d : KindDesc) : PEvent → Bool
  | .admitOcc _ => d.kAdmitOcc
  -- The assertion event is supply-side grammar, present in every
  -- controller of the declared class: the class toggles the ten
  -- response/administrative kinds, not the supply of differences.
  | .assertWit _ _ => true
  | .admitWit _ _ => d.kAdmitWit
  | .protect _ _ => d.kProtect
  | .declareObs => d.kDeclareObs
  | .refineCol _ _ => d.kRefineCol
  | .addCol _ => d.kAddCol
  | .refuse _ _ => d.kRefuse
  | .setBudget _ => d.kSetBudget
  | .setLicense _ => d.kSetLicense
  | .halt => d.kHalt

/-- The controlled interpreter: enabled events execute the sealed
passage step, disabled events are inert.  The step itself is never
modified — the class varies the grammar, not the dynamics. -/
def interpK (d : KindDesc) (s : PState) (e : PEvent) : PState :=
  if enabled d e then step s e else s

def replayK (d : KindDesc) (h : List PEvent) (s : PState) : PState :=
  h.foldl (interpK d) s

def bools : List Bool := [false, true]

/-- The declared comparison class, fully enumerated. -/
def allKinds : List KindDesc :=
  bools.flatMap fun a => bools.flatMap fun b => bools.flatMap fun c =>
    bools.flatMap fun d => bools.flatMap fun e => bools.flatMap fun f =>
      bools.flatMap fun g => bools.flatMap fun h =>
        bools.flatMap fun i => bools.map fun j =>
          ⟨a, b, c, d, e, f, g, h, i, j⟩

theorem allKinds_length : allKinds.length = 1024 := by decide

theorem mem_bools (b : Bool) : b ∈ bools := by cases b <;> decide

/-- The enumeration is complete: every describable controller is a
member.  "Complete" is used with exactly this proof. -/
theorem allKinds_complete (d : KindDesc) : d ∈ allKinds := by
  obtain ⟨a, b, c, d0, e, f, g, h, i, j⟩ := d
  refine List.mem_flatMap.mpr ⟨a, mem_bools a, ?_⟩
  refine List.mem_flatMap.mpr ⟨b, mem_bools b, ?_⟩
  refine List.mem_flatMap.mpr ⟨c, mem_bools c, ?_⟩
  refine List.mem_flatMap.mpr ⟨d0, mem_bools d0, ?_⟩
  refine List.mem_flatMap.mpr ⟨e, mem_bools e, ?_⟩
  refine List.mem_flatMap.mpr ⟨f, mem_bools f, ?_⟩
  refine List.mem_flatMap.mpr ⟨g, mem_bools g, ?_⟩
  refine List.mem_flatMap.mpr ⟨h, mem_bools h, ?_⟩
  refine List.mem_flatMap.mpr ⟨i, mem_bools i, ?_⟩
  exact List.mem_map.mpr ⟨j, mem_bools j, rfl⟩

/-- The all-on controller. -/
def fullK : KindDesc :=
  ⟨true, true, true, true, true, true, true, true, true, true⟩

/-- The all-on controller executes exactly the sealed step. -/
theorem interpK_full (s : PState) (e : PEvent) :
    interpK fullK s e = step s e := by
  cases e <;> rfl

/-! ## Two-rule support in the broad class -/

/-- Syntactic support for the two-rule response universe: both
response executors and the funding kind are enabled. -/
def ResponseLiveB (d : KindDesc) : Bool :=
  d.kRefineCol && d.kAddCol && d.kSetBudget

def ResponseLive (d : KindDesc) : Prop := ResponseLiveB d = true

/-- The live census: exactly 128 of the 1024 controllers support the
two-rule response universe.  Exhaustive over the declared class. -/
theorem live_census : (allKinds.filter ResponseLiveB).length = 128 := by
  decide

theorem fullK_live : ResponseLiveB fullK = true := by decide

/-- The concrete obstructed funded state. -/
def OBST5 : PState :=
  { occ := [0, 1], asserted := [(0, 1), (1, 0)], wit := [(0, 1)],
    prot := [(0, 1)], obs := some [],
    budget := 5, licensed := true, refusals := [], halted := false }

theorem obst5_certified : obstP OBST5 0 1 = true := by decide

/-- **Two-rule executability, generic over the live controllers**: at
`OBST5` the funded extension block executes and resolves the
obstruction under every live controller.  The seven free bits are
irrelevant to the two events the block contains, so the proof is a
computation after discharging the three live bits. -/
theorem tworule_executable_of_live (d : KindDesc)
    (hlive : ResponseLiveB d = true) :
    obstP (interpK d (interpK d OBST5 (.setBudget 1)) (.addCol [0]))
      0 1 = false := by
  obtain ⟨a, b, c, d0, e, f, g, h, i, j⟩ := d
  simp only [ResponseLiveB, Bool.and_eq_true] at hlive
  obtain ⟨⟨-, hf⟩, hh⟩ := hlive
  subst hf; subst hh
  rfl

/-! ## Each response kind is load-bearing: three countermodels -/

def noAddK : KindDesc := { fullK with kAddCol := false }
def noBudgetK : KindDesc := { fullK with kSetBudget := false }
def noRefineK : KindDesc := { fullK with kRefineCol := false }

/-- The unfunded obstructed state: funding is load-bearing here. -/
def OBST0 : PState := { OBST5 with budget := 0 }

/-- The unlicensed refinable obstructed state: extension execution is
license-gated by the sealed step, so same-level refinement is the
only resolving route. -/
def LOBST : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)],
    prot := [(0, 1)],
    obs := some [[]], budget := 5, licensed := false, refusals := [],
    halted := false }

theorem obst0_certified : obstP OBST0 0 1 = true := by decide
theorem lobst_certified : obstP LOBST 0 1 = true := by decide

/-- The declared batteries are the exact driver families; each is
nonempty, so the persistence results below are not vacuous. -/
theorem battery_obst5_nonempty : nextFamilyP OBST5 ≠ [] := by decide
theorem battery_obst0_nonempty : nextFamilyP OBST0 ≠ [] := by decide
theorem battery_lobst_nonempty : nextFamilyP LOBST ≠ [] := by decide

/-- With `addCol` disabled, every block the driver emits at `OBST5`
(whose repair menu is empty, so extension is the only route) leaves
the obstruction in place. -/
theorem dead_without_addcol :
    ((nextFamilyP OBST5).all fun blk =>
      obstP (replayK noAddK blk OBST5) 0 1) = true := by decide

/-- ... and the all-on controller resolves the same state with a
battery member. -/
theorem full_resolves_obst5 :
    obstP (replayK fullK [.setBudget 1, .addCol [0]] OBST5) 0 1
      = false := by decide

/-- With `setBudget` disabled, every block the driver emits at the
unfunded obstruction leaves it in place: both response executors are
budget-gated by the sealed step. -/
theorem dead_without_budget :
    ((nextFamilyP OBST0).all fun blk =>
      obstP (replayK noBudgetK blk OBST0) 0 1) = true := by decide

theorem full_resolves_obst0 :
    obstP (replayK fullK [.setBudget 1, .addCol [0]] OBST0) 0 1
      = false := by decide

/-- With `refineCol` disabled, every block the driver emits at the
unlicensed refinable obstruction leaves it in place: the extension
blocks are emitted but their execution is license-gated, so the
repair route was the only resolving one. -/
theorem dead_without_refine :
    ((nextFamilyP LOBST).all fun blk =>
      obstP (replayK noRefineK blk LOBST) 0 1) = true := by decide

theorem full_resolves_lobst :
    obstP (replayK fullK [.refineCol [] 0] LOBST) 0 1 = false := by
  decide

/-! ## Non-uniqueness of live controllers

The live set is not a singleton (`live_census`), and it is not even
behaviorally rigid: two live members agree on every refusal-free
event at every state and differ at a certified obstruction. -/

def noRefK : KindDesc := { fullK with kRefuse := false }

theorem noRefK_live : ResponseLiveB noRefK = true := by decide
theorem noRefK_ne_fullK : noRefK ≠ fullK := by decide

def isRefuse : PEvent → Bool
  | .refuse _ _ => true
  | _ => false

/-- On every refusal-free event, at every state, the two live
controllers are behaviorally identical. -/
theorem nonrefuse_agree (s : PState) (e : PEvent)
    (h : isRefuse e = false) :
    interpK fullK s e = interpK noRefK s e := by
  cases e <;> first | rfl | exact Bool.noConfusion h

/-- At the certified obstruction they differ on a refuse event. -/
theorem refuse_distinguishes :
    interpK fullK OBST5 (.refuse 0 1)
      ≠ interpK noRefK OBST5 (.refuse 0 1) := by decide

/-! ## The controller category -/

/-- An object: a controller. -/
structure Ctrl where
  d : KindDesc

/-- A morphism: a simulation — a state map commuting with the
interpreted step. -/
structure Sim (C1 C2 : Ctrl) where
  f : PState → PState
  comm : ∀ s e, f (interpK C1.d s e) = interpK C2.d (f s) e

/-- Internal identity of simulations is determined by the state map:
the commutation field is a proposition. -/
theorem sim_ext {C1 C2 : Ctrl} {u v : Sim C1 C2} (h : u.f = v.f) :
    u = v := by
  cases u with
  | mk f1 c1 =>
    cases v with
    | mk f2 c2 =>
      have h' : f1 = f2 := h
      subst h'
      rfl

def idSim (C : Ctrl) : Sim C C := ⟨fun s => s, fun _ _ => rfl⟩

def compSim {A B C : Ctrl} (g : Sim B C) (u : Sim A B) : Sim A C :=
  ⟨fun s => g.f (u.f s),
   fun s e => (congrArg g.f (u.comm s e)).trans (g.comm (u.f s) e)⟩

theorem comp_id {A B : Ctrl} (u : Sim A B) :
    compSim u (idSim A) = u := sim_ext rfl

theorem id_comp {A B : Ctrl} (u : Sim A B) :
    compSim (idSim B) u = u := sim_ext rfl

theorem comp_assoc {A B C D : Ctrl} (k : Sim C D) (g : Sim B C)
    (u : Sim A B) :
    compSim (compSim k g) u = compSim k (compSim g u) := sim_ext rfl

/-! ## Refusal erasure is a morphism -/

def fullCtrl : Ctrl := ⟨fullK⟩
def noRefCtrl : Ctrl := ⟨noRefK⟩

/-- Overwrite the refusal store. -/
def setRef (rs : List (Nat × Nat)) (s : PState) : PState :=
  { s with refusals := rs }

def eraseRef : PState → PState := fun s => { s with refusals := [] }

theorem setRef_occ (rs : List (Nat × Nat)) (s : PState) :
    (setRef rs s).occ = s.occ := rfl
theorem setRef_wit (rs : List (Nat × Nat)) (s : PState) :
    (setRef rs s).wit = s.wit := rfl
theorem setRef_prot (rs : List (Nat × Nat)) (s : PState) :
    (setRef rs s).prot = s.prot := rfl
theorem setRef_obs (rs : List (Nat × Nat)) (s : PState) :
    (setRef rs s).obs = s.obs := rfl
theorem setRef_budget (rs : List (Nat × Nat)) (s : PState) :
    (setRef rs s).budget = s.budget := rfl
theorem setRef_licensed (rs : List (Nat × Nat)) (s : PState) :
    (setRef rs s).licensed = s.licensed := rfl
theorem setRef_refusals (rs : List (Nat × Nat)) (s : PState) :
    (setRef rs s).refusals = rs := rfl
theorem setRef_halted (rs : List (Nat × Nat)) (s : PState) :
    (setRef rs s).halted = s.halted := rfl

theorem wfPair_setRef (rs : List (Nat × Nat)) (s : PState)
    (i j : Nat) : wfPair (setRef rs s) i j = wfPair s i j := rfl
theorem obstP_setRef (rs : List (Nat × Nat)) (s : PState)
    (i j : Nat) : obstP (setRef rs s) i j = obstP s i j := rfl
theorem refineOk_setRef (rs : List (Nat × Nat)) (s : PState)
    (v : List Nat) (p : Nat) :
    refineOk (setRef rs s) v p = refineOk s v p := rfl
theorem colOk_setRef (rs : List (Nat × Nat)) (s : PState)
    (c : List Nat) : colOk (setRef rs s) c = colOk s c := rfl

/-- The sealed step reads the refusal store only on refuse events:
on every other event, overwriting the refusal store commutes with the
step. -/
theorem setRef_step_comm (rs : List (Nat × Nat)) (s : PState)
    (e : PEvent) (h : isRefuse e = false) :
    setRef rs (step s e) = step (setRef rs s) e := by
  by_cases hh : s.halted = true
  · rw [step_halted s e hh, step_halted (setRef rs s) e hh] <;> rfl
  · have hh' : ¬((setRef rs s).halted = true) := hh
    cases e with
    | admitOcc t =>
        simp only [step]
        rw [if_neg hh, if_neg hh']
        by_cases hm : t ∈ s.occ
        · have hm' : t ∈ (setRef rs s).occ := hm
          rw [if_pos hm, if_pos hm'] <;> rfl
        · have hm' : ¬(t ∈ (setRef rs s).occ) := hm
          rw [if_neg hm, if_neg hm'] <;> rfl
    | assertWit i j =>
        simp only [step]
        rw [if_neg hh, if_neg hh']
        by_cases hg : (wfPair s i j
            && !decide ((i, j) ∈ s.asserted)) = true
        · have hg' : (wfPair (setRef rs s) i j
              && !decide ((i, j) ∈ (setRef rs s).asserted))
              = true := hg
          rw [if_pos hg, if_pos hg'] <;> rfl
        · have hg' : ¬((wfPair (setRef rs s) i j
              && !decide ((i, j) ∈ (setRef rs s).asserted))
              = true) := hg
          rw [if_neg hg, if_neg hg'] <;> rfl
    | admitWit i j =>
        simp only [step]
        rw [if_neg hh, if_neg hh']
        by_cases hg : (wfPair s i j
            && decide ((i, j) ∈ s.asserted)
            && !decide ((i, j) ∈ s.wit)) = true
        · have hg' : (wfPair (setRef rs s) i j
              && decide ((i, j) ∈ (setRef rs s).asserted)
              && !decide ((i, j) ∈ (setRef rs s).wit)) = true := hg
          rw [if_pos hg, if_pos hg'] <;> rfl
        · have hg' : ¬((wfPair (setRef rs s) i j
              && decide ((i, j) ∈ (setRef rs s).asserted)
              && !decide ((i, j) ∈ (setRef rs s).wit)) = true) := hg
          rw [if_neg hg, if_neg hg'] <;> rfl
    | protect i j =>
        simp only [step]
        rw [if_neg hh, if_neg hh']
        by_cases hg : (decide ((i, j) ∈ s.wit)
            && !decide ((i, j) ∈ s.prot)) = true
        · have hg' : (decide ((i, j) ∈ (setRef rs s).wit)
              && !decide ((i, j) ∈ (setRef rs s).prot)) = true := hg
          rw [if_pos hg, if_pos hg'] <;> rfl
        · have hg' : ¬((decide ((i, j) ∈ (setRef rs s).wit)
              && !decide ((i, j) ∈ (setRef rs s).prot)) = true) := hg
          rw [if_neg hg, if_neg hg'] <;> rfl
    | declareObs =>
        simp only [step]
        rw [if_neg hh, if_neg hh', setRef_obs]
        cases s.obs <;> rfl
    | refineCol v p =>
        simp only [step]
        rw [if_neg hh, if_neg hh']
        by_cases hg : (refineOk s v p && decide (0 < s.budget)) = true
        · have hg' : (refineOk (setRef rs s) v p
              && decide (0 < (setRef rs s).budget)) = true := hg
          rw [if_pos hg, if_pos hg', setRef_obs]
          cases s.obs <;> rfl
        · have hg' : ¬((refineOk (setRef rs s) v p
              && decide (0 < (setRef rs s).budget)) = true) := hg
          rw [if_neg hg, if_neg hg'] <;> rfl
    | addCol c =>
        simp only [step]
        rw [if_neg hh, if_neg hh']
        by_cases hg : (colOk s c && s.licensed
            && decide (0 < s.budget)) = true
        · have hg' : (colOk (setRef rs s) c && (setRef rs s).licensed
              && decide (0 < (setRef rs s).budget)) = true := hg
          rw [if_pos hg, if_pos hg', setRef_obs]
          cases s.obs <;> rfl
        · have hg' : ¬((colOk (setRef rs s) c
              && (setRef rs s).licensed
              && decide (0 < (setRef rs s).budget)) = true) := hg
          rw [if_neg hg, if_neg hg'] <;> rfl
    | refuse i j => exact Bool.noConfusion h
    | setBudget n =>
        simp only [step]
        rw [if_neg hh, if_neg hh'] <;> rfl
    | setLicense b =>
        simp only [step]
        rw [if_neg hh, if_neg hh'] <;> rfl
    | halt => rfl

/-- Refusal erasure: a simulation from the all-on controller to the
refusal-free controller.  On refuse events the target is inert and
erasure absorbs the source's record; on every other event the step
never reads the refusal store (`setRef_step_comm`). -/
def eraseSim : Sim fullCtrl noRefCtrl where
  f := eraseRef
  comm := by
    intro s e
    cases e with
    | admitOcc t => exact setRef_step_comm [] s (.admitOcc t) rfl
    | assertWit i j =>
        exact setRef_step_comm [] s (.assertWit i j) rfl
    | admitWit i j => exact setRef_step_comm [] s (.admitWit i j) rfl
    | protect i j => exact setRef_step_comm [] s (.protect i j) rfl
    | declareObs => exact setRef_step_comm [] s .declareObs rfl
    | refineCol v p =>
        exact setRef_step_comm [] s (.refineCol v p) rfl
    | addCol c => exact setRef_step_comm [] s (.addCol c) rfl
    | refuse i j =>
        show eraseRef (step s (.refuse i j)) = eraseRef s
        simp only [step]
        repeat' split
        all_goals rfl
    | setBudget n => exact setRef_step_comm [] s (.setBudget n) rfl
    | setLicense b =>
        exact setRef_step_comm [] s (.setLicense b) rfl
    | halt => exact setRef_step_comm [] s .halt rfl

theorem erase_sim : ∃ u : Sim fullCtrl noRefCtrl, u.f = eraseRef :=
  ⟨eraseSim, rfl⟩

/-- Erasure is not the identity map on states. -/
theorem eraseRef_not_id :
    eraseRef { OBST5 with refusals := [(0, 1)] }
      ≠ { OBST5 with refusals := [(0, 1)] } := by decide

/-! ## Initiality refuted by constant simulations -/

def HALTED0 : PState := { genesisP with halted := true }
def HALTED1 : PState := { genesisP with occ := [0], halted := true }

theorem halted0_ne_halted1 : HALTED0 ≠ HALTED1 := by decide

/-- Every constant map to a halted state is a simulation between any
two controllers: the terminal is absorbing, so the target side is
inert whatever the event and whatever the grammar. -/
def constSim (C T : Ctrl) (t : PState) (ht : t.halted = true) :
    Sim C T where
  f := fun _ => t
  comm := by
    intro s e
    show t = interpK T.d t e
    unfold interpK
    split
    · exact (step_halted t e ht).symm
    · rfl

theorem const_sims_distinct (C T : Ctrl) :
    constSim C T HALTED0 rfl ≠ constSim C T HALTED1 rfl := by
  intro hEq
  have hf : HALTED0 = HALTED1 :=
    congrArg (fun u : Sim C T => u.f genesisP) hEq
  exact halted0_ne_halted1 hf

/-- Two distinct endo-simulations on the all-on controller: identity
and the constant collapse to a halted state. -/
theorem two_endo_sims :
    constSim fullCtrl fullCtrl HALTED0 rfl ≠ idSim fullCtrl := by
  intro hEq
  have hf : HALTED0 = genesisP :=
    congrArg (fun u : Sim fullCtrl fullCtrl => u.f genesisP) hEq
  exact absurd hf (by decide)

/-- Morphism existence is trivial: every ordered pair of controllers
is connected by a constant simulation. -/
theorem every_pair_connected (C T : Ctrl) : Nonempty (Sim C T) :=
  ⟨constSim C T HALTED0 rfl⟩

/-- Uniqueness fails between every ordered pair. -/
theorem sims_never_unique (C T : Ctrl) : ∃ u v : Sim C T, u ≠ v :=
  ⟨constSim C T HALTED0 rfl, constSim C T HALTED1 rfl,
    const_sims_distinct C T⟩

/-- Initiality of a controller: a unique simulation to every
target. -/
def InitialCtrl (C : Ctrl) : Prop :=
  ∀ T : Ctrl, ∃ u : Sim C T, ∀ v : Sim C T, v = u

/-- **No controller is initial**: the two constant simulations into
the all-on controller kill uniqueness from every source. -/
theorem no_initial_ctrl : ¬ ∃ C : Ctrl, InitialCtrl C := by
  intro hex
  obtain ⟨C, hC⟩ := hex
  obtain ⟨u, hu⟩ := hC fullCtrl
  exact const_sims_distinct C fullCtrl
    ((hu (constSim C fullCtrl HALTED0 rfl)).trans
      (hu (constSim C fullCtrl HALTED1 rfl)).symm)

/-- The refutation restricted to the live subcategory: the target
used is itself live, so restricting objects to two-rule-supporting
controllers does not restore initiality. -/
theorem no_initial_live_ctrl :
    ¬ ∃ C : Ctrl, ResponseLiveB C.d = true ∧
      ∀ T : Ctrl, ResponseLiveB T.d = true →
        ∃ u : Sim C T, ∀ v : Sim C T, v = u := by
  intro hex
  obtain ⟨C, -, hC⟩ := hex
  obtain ⟨u, hu⟩ := hC fullCtrl fullK_live
  exact const_sims_distinct C fullCtrl
    ((hu (constSim C fullCtrl HALTED0 rfl)).trans
      (hu (constSim C fullCtrl HALTED1 rfl)).symm)

/-! ## The strict refinement: genesis- and liveness-preserving

The raw simulation category is too floppy for initiality: constants
to halted states connect everything.  The refinement demands genesis
preservation and preservation of the non-halted flag.  Constants are
excluded, identity and erasure survive — and global uniqueness still
fails, for a reason worth exact scope: a bidirectionally
step-invariant predicate false at genesis parameterizes distinct
strict simulations that agree on the whole reachable orbit. -/

structure StrictSim (C1 C2 : Ctrl) extends Sim C1 C2 where
  gen : toSim.f genesisP = genesisP
  live : ∀ s, s.halted = false → (toSim.f s).halted = false

/-- Constant collapses are excluded by liveness preservation. -/
theorem const_not_strict {C T : Ctrl} (t : PState)
    (ht : t.halted = true) (u : StrictSim C T) :
    u.toSim.f ≠ (fun _ => t) := by
  intro hEq
  have hl : (u.toSim.f genesisP).halted = false := u.live genesisP rfl
  rw [hEq] at hl
  have hl' : t.halted = false := hl
  rw [ht] at hl'
  exact Bool.noConfusion hl'

def idStrict (C : Ctrl) : StrictSim C C :=
  ⟨idSim C, rfl, fun _ h => h⟩

def eraseStrict : StrictSim fullCtrl noRefCtrl :=
  ⟨eraseSim, rfl, fun _ h => h⟩

/-! ### The invariant twist: a second strict simulation -/

/-- Some element of the list recurs. -/
def hasDup : List Nat → Bool
  | [] => false
  | x :: xs => (decide (x ∈ xs)) || hasDup xs

theorem hasDup_append_fresh (l : List Nat) (t : Nat) (h : ¬ t ∈ l) :
    hasDup (l ++ [t]) = hasDup l := by
  induction l with
  | nil => rfl
  | cons x xs ih =>
      have hx : ¬ t ∈ xs := fun hm => h (List.mem_cons_of_mem x hm)
      have hxt : ¬ (x = t) := fun he =>
        h (List.mem_cons.mpr (Or.inl he.symm))
      show ((decide (x ∈ xs ++ [t])) || hasDup (xs ++ [t]))
          = ((decide (x ∈ xs)) || hasDup xs)
      rw [ih hx]
      have hmem : (x ∈ xs ++ [t]) ↔ (x ∈ xs) := by
        constructor
        · intro hm
          cases List.mem_append.mp hm with
          | inl h1 => exact h1
          | inr h2 => exact absurd (List.mem_singleton.mp h2) hxt
        · intro hm
          exact List.mem_append.mpr (Or.inl hm)
      rw [decide_eq_decide.mpr hmem]

/-- Occurrence-store duplication is bidirectionally step-invariant:
admission dedups, and nothing removes occurrences. -/
theorem hasDup_step (s : PState) (e : PEvent) :
    hasDup (step s e).occ = hasDup s.occ := by
  cases e <;> simp only [step] <;> repeat' split
  all_goals
    first
    | rfl
    | exact hasDup_append_fresh s.occ _ (by assumption)

/-- A step-invariant refusal store: empty on duplicate-free
occurrence stores, one junk record otherwise. -/
def twistRef (s : PState) : List (Nat × Nat) :=
  if hasDup s.occ then [(0, 0)] else []

def twistF : PState → PState := fun s => setRef (twistRef s) s

theorem twistRef_step (s : PState) (e : PEvent) :
    twistRef (step s e) = twistRef s := by
  simp only [twistRef, hasDup_step]

theorem twist_step_comm (s : PState) (e : PEvent)
    (h : isRefuse e = false) :
    twistF (step s e) = step (twistF s) e := by
  show setRef (twistRef (step s e)) (step s e)
    = step (setRef (twistRef s) s) e
  rw [twistRef_step]
  exact setRef_step_comm (twistRef s) s e h

def twistSim : Sim fullCtrl noRefCtrl where
  f := twistF
  comm := by
    intro s e
    cases e with
    | admitOcc t => exact twist_step_comm s (.admitOcc t) rfl
    | assertWit i j => exact twist_step_comm s (.assertWit i j) rfl
    | admitWit i j => exact twist_step_comm s (.admitWit i j) rfl
    | protect i j => exact twist_step_comm s (.protect i j) rfl
    | declareObs => exact twist_step_comm s .declareObs rfl
    | refineCol v p => exact twist_step_comm s (.refineCol v p) rfl
    | addCol c => exact twist_step_comm s (.addCol c) rfl
    | refuse i j =>
        show twistF (step s (.refuse i j)) = twistF s
        simp only [step]
        repeat' split
        all_goals rfl
    | setBudget n => exact twist_step_comm s (.setBudget n) rfl
    | setLicense b => exact twist_step_comm s (.setLicense b) rfl
    | halt => exact twist_step_comm s .halt rfl

def twistStrict : StrictSim fullCtrl noRefCtrl :=
  ⟨twistSim, rfl, fun _ h => h⟩

/-- A duplicated occurrence store: representable, but unreachable —
admission dedups (`reachable_no_dup`). -/
def DUPSTATE : PState :=
  { occ := [5, 5], asserted := [], wit := [], prot := [], obs := none,
    budget := 0, licensed := true, refusals := [(3, 4)],
    halted := false }

theorem twist_ne_erase_at_dup :
    twistF DUPSTATE ≠ eraseRef DUPSTATE := by decide

/-- **Global uniqueness fails even among strict simulations**: the
invariant twist and refusal erasure are distinct strict simulations
between the same pair of live controllers. -/
theorem strict_not_unique :
    ∃ u v : StrictSim fullCtrl noRefCtrl, u ≠ v := by
  refine ⟨twistStrict, eraseStrict, ?_⟩
  intro hEq
  exact twist_ne_erase_at_dup
    (congrArg (fun u : StrictSim fullCtrl noRefCtrl =>
      u.toSim.f DUPSTATE) hEq)

/-! ### The exact boundary: uniqueness on the reachable orbit -/

theorem replay_hasDup (h : List PEvent) (s : PState) :
    hasDup (replayP h s).occ = hasDup s.occ := by
  induction h generalizing s with
  | nil => rfl
  | cons e rest ih =>
      show hasDup (replayP rest (step s e)).occ = hasDup s.occ
      rw [ih (step s e), hasDup_step]

/-- Reachable states have duplicate-free occurrence stores. -/
theorem reachable_no_dup (h : List PEvent) :
    hasDup (replayP h genesisP).occ = false :=
  replay_hasDup h genesisP

theorem twist_eq_erase_of_no_dup (s : PState)
    (hd : hasDup s.occ = false) : twistF s = eraseRef s := by
  show setRef (twistRef s) s = eraseRef s
  unfold twistRef
  rw [hd]
  rfl

/-- On the replay orbit of genesis, the twist IS erasure: the two
strict simulations differ only off the orbit. -/
theorem twist_erase_agree_reachable (h : List PEvent) :
    twistF (replayP h genesisP) = eraseRef (replayP h genesisP) :=
  twist_eq_erase_of_no_dup _ (reachable_no_dup h)

/-- Every simulation out of the all-on controller is pinned along
replay: its value on a replayed state is the controlled replay of
its value on the start state. -/
theorem sim_pinned (u : Sim fullCtrl noRefCtrl) (hist : List PEvent)
    (s : PState) :
    u.f (replayP hist s)
      = List.foldl (interpK noRefCtrl.d) (u.f s) hist := by
  induction hist generalizing s with
  | nil => rfl
  | cons e rest ih =>
      show u.f (replayP rest (step s e))
        = List.foldl (interpK noRefCtrl.d)
            (interpK noRefCtrl.d (u.f s) e) rest
      rw [ih (step s e)]
      have hc : u.f (step s e) = interpK noRefCtrl.d (u.f s) e := by
        have h0 := u.comm s e
        rw [show interpK fullCtrl.d s e = step s e from
          interpK_full s e] at h0
        exact h0
      rw [hc]

/-- **Uniqueness on the replay orbit**: any two genesis-preserving
simulations from the all-on controller to the refusal-free
controller agree on every state replayed from genesis.  Together
with `strict_not_unique` this is the exact boundary: uniqueness of
the erasure morphism is a property of the reachable orbit, and fails
on the raw state space. -/
theorem genesis_sims_agree_on_reachable
    (u v : Sim fullCtrl noRefCtrl)
    (hu : u.f genesisP = genesisP) (hv : v.f genesisP = genesisP)
    (hist : List PEvent) :
    u.f (replayP hist genesisP) = v.f (replayP hist genesisP) := by
  rw [sim_pinned u hist genesisP, sim_pinned v hist genesisP, hu, hv]

theorem strict_agree_on_reachable
    (u v : StrictSim fullCtrl noRefCtrl) (hist : List PEvent) :
    u.toSim.f (replayP hist genesisP)
      = v.toSim.f (replayP hist genesisP) :=
  genesis_sims_agree_on_reachable u.toSim v.toSim u.gen v.gen hist

end ControllerCategory
