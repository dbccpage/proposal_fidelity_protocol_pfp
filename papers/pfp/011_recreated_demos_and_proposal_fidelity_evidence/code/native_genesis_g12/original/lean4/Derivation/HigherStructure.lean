import Derivation.PrimitivePassage

/-!
# Earliest higher structure: the first graph and the first simplices

Stage IX of the contact-and-passage run.  Everything here is built
*after* the passage is complete, from the passage state alone plus
separately declared additions — and every declaration is named as
one.

Contents:

1. **The growth of the first graph.**  A deterministic driver
   (`growHist`) iterates the passage: each round admits one new
   occurrence and one witnessed difference to its predecessor,
   protects it, and — because the declared observation is blind to
   the new pair — produces an active obstruction whose accepted
   response is structure creation (a new observation column).  The
   invariant record of the grown state is characterized at every
   stage (`graphAt_spec`), so the first graph — the path graph on
   the admitted occurrences — grows lawfully at every horizon, and
   the process responsible for each created column is the recorded
   obstruction of that round (`round_creation_record`).

2. **What is forced and what is admitted.**  A witnessed binary
   relation *is* a directed graph presentation (carrier plus binary
   store) — identity, not force.  Nothing higher is forced: the
   grown state contains no 2-cell data at all, and two distinct
   boundary conventions are equally compatible with the same graph
   (`boundary_not_forced`), so simplicial structure above dimension
   one enters only by declaration.

3. **The 0-, 1-, 2-, 3-simplices, with creation records.**  A
   declared cell calculus (`CEvent`, `cstep`) whose guards encode
   the ladder invariant: a `k+1`-cell can be admitted exactly over a
   complete, unfilled boundary of `k`-cells — the same
   obstruction-shape at every dimension (an unfilled parallel
   boundary), resolved the same way (create the filling structure).
   The four-vertex demonstration complex is grown from the
   passage-grown graph, every admission guarded, and the boundary
   guard is proved load-bearing.

4. **Named invariants**, computed on the declared complex:
   * the *ladder invariant* — the recurrence of the two-rule shape
     at every dimension (boundary-complete-and-unfilled is the
     dimension-`k` obstruction; the `k+1`-cell is its structural
     response);
   * the *occurrence alternation number* `altNum` — the alternating
     sum of cell counts, which the declared boundary calculus turns
     into a stage-invariant of the growth;
   * the *cut census* — the number of maximal faithful two-block
     observations of the grown carrier (the observer branching
     count from the presentation category).
   With the declared integer coefficients and boundary maps, the
   composite boundary vanishes on every cell of the demonstration
   complex (`d2_zero_triangles`, `d2_zero_tet`) — a theorem only
   AFTER the declarations; the non-forcing countermodel shows the
   declarations carry real content.
-/

namespace HigherStructure

open PrimitivePassage

/-! ## 1. The growth driver: the first graph -/

/-- Round `k` of the growth: round 0 admits the first occurrence;
round 1 admits the second, the first witnessed difference, its
protection, the observation, and — responding to the first
obstruction — the first column; round `k+2` repeats the pattern one
level up. -/
def growBlock : Nat → List PEvent
  | 0 => [.admitOcc 0]
  | 1 => [.admitOcc 1, .assertWit 0 1, .admitWit 0 1, .protect 0 1,
          .declareObs, .setBudget 1, .addCol [0]]
  | k + 2 => [.admitOcc (k + 2), .assertWit (k + 1) (k + 2),
              .admitWit (k + 1) (k + 2), .protect (k + 1) (k + 2),
              .setBudget 1, .addCol [k + 1]]

def growHist : Nat → List PEvent
  | 0 => growBlock 0
  | k + 1 => growHist k ++ growBlock (k + 1)

/-- The grown state at stage `k`. -/
def graphAt (k : Nat) : PState := replayP (growHist k) genesisP

/-- The characterized record of the grown state, stage `k + 1`:
occurrences `0..k+1` (the 0-cells), witnessed pairs `(i, i+1)` (the
1-cells: the path graph), protection on every edge, one observation
column per resolved obstruction, budget spent, live. -/
def pathState (k : Nat) : PState :=
  { occ := List.range (k + 2),
    asserted := (List.range (k + 1)).map (fun i => (i, i + 1)),
    wit := (List.range (k + 1)).map (fun i => (i, i + 1)),
    prot := (List.range (k + 1)).map (fun i => (i, i + 1)),
    obs := some ((List.range (k + 1)).map (fun i => [i])),
    budget := 0, licensed := true, refusals := [], halted := false }

/-! ### Guard facts for the induction -/

theorem grow_fresh (m : Nat) : ¬ (m + 2 ∈ List.range (m + 2)) := by
  intro h
  exact absurd (List.mem_range.mp h) (by omega)

theorem grow_wit_not_mem (m : Nat) :
    ¬ ((m + 1, m + 2) ∈ (List.range (m + 1)).map
      (fun i => (i, i + 1))) := by
  intro h
  obtain ⟨i, hi, heq⟩ := List.mem_map.mp h
  have h1 : i = m + 1 := congrArg Prod.fst heq
  have h2 : i < m + 1 := List.mem_range.mp hi
  omega

theorem grow_col_not_mem (m : Nat) :
    ¬ (([m + 1] : List Nat) ∈ (List.range (m + 1)).map
      (fun i => ([i] : List Nat))) := by
  intro h
  obtain ⟨i, hi, heq⟩ := List.mem_map.mp h
  have h1 : i = m + 1 := by
    have := congrArg (fun l : List Nat => l.headD 0) heq
    simpa using this
  have h2 : i < m + 1 := List.mem_range.mp hi
  omega

/-- Old singleton columns are blind to the new adjacent pair. -/
theorem grow_cols_blind (m : Nat) {c : List Nat}
    (hc : c ∈ (List.range (m + 1)).map (fun i => ([i] : List Nat))) :
    sepCol c (m + 1) (m + 2) = false := by
  obtain ⟨i, hi, heq⟩ := List.mem_map.mp hc
  have h2 : i < m + 1 := List.mem_range.mp hi
  subst heq
  unfold sepCol
  rw [decide_eq_false (by
        intro h
        have := List.mem_singleton.mp h
        omega),
      decide_eq_false (by
        intro h
        have := List.mem_singleton.mp h
        omega)]
  rfl

/-- The new singleton column separates the new pair. -/
theorem grow_col_separates (m : Nat) :
    sepCol [m + 1] (m + 1) (m + 2) = true := by
  unfold sepCol
  rw [decide_eq_true (List.mem_singleton.mpr rfl),
      decide_eq_false (by
        intro h
        have := List.mem_singleton.mp h
        omega)]
  rfl

/-- Adjacent-pair separation by the matching column: pair `(i, i+1)`
is separated by column `[i]`. -/
theorem grow_pair_separated (i : Nat) :
    sepCol [i] i (i + 1) = true := by
  unfold sepCol
  rw [decide_eq_true (List.mem_singleton.mpr rfl),
      decide_eq_false (by
        intro h
        have := List.mem_singleton.mp h
        omega)]
  rfl

/-- The declared observation of stage `m` is blind to the new pair:
its zero relation holds on `(m+1, m+2)`. -/
theorem grow_zero (m : Nat) :
    zeroP ((List.range (m + 1)).map (fun i => [i]))
      (m + 1) (m + 2) = true := by
  unfold zeroP sepP
  have hany : ((List.range (m + 1)).map (fun i => ([i] : List Nat))).any
      (fun c => sepCol c (m + 1) (m + 2)) = false := by
    cases h : ((List.range (m + 1)).map
        (fun i => ([i] : List Nat))).any
        (fun c => sepCol c (m + 1) (m + 2)) with
    | false => rfl
    | true =>
        obtain ⟨c, hc, hp⟩ := List.any_eq_true.mp h
        rw [grow_cols_blind m hc] at hp
        exact Bool.noConfusion hp
  rw [hany]
  rfl

/-! ### Step helpers with explicit guards -/

theorem pstep_admit {s : PState} {t : Nat} (hh : s.halted = false)
    (h : ¬ t ∈ s.occ) :
    step s (.admitOcc t) = { s with occ := s.occ ++ [t] } := by
  simp only [step, hh]
  rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
      if_neg h]

theorem pstep_assert {s : PState} {i j : Nat} (hh : s.halted = false)
    (hg : (wfPair s i j && !(decide ((i, j) ∈ s.asserted)))
      = true) :
    step s (.assertWit i j)
      = { s with asserted := s.asserted ++ [(i, j)] } := by
  simp only [step, hh]
  rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
      if_pos hg]

theorem pstep_wit {s : PState} {i j : Nat} (hh : s.halted = false)
    (hg : (wfPair s i j && (decide ((i, j) ∈ s.asserted))
      && !(decide ((i, j) ∈ s.wit))) = true) :
    step s (.admitWit i j) = { s with wit := s.wit ++ [(i, j)] } := by
  simp only [step, hh]
  rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
      if_pos hg]

theorem pstep_prot {s : PState} {i j : Nat} (hh : s.halted = false)
    (hg : ((decide ((i, j) ∈ s.wit))
      && !(decide ((i, j) ∈ s.prot))) = true) :
    step s (.protect i j) = { s with prot := s.prot ++ [(i, j)] } := by
  simp only [step, hh]
  rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
      if_pos hg]

theorem pstep_budget {s : PState} (n : Nat) (hh : s.halted = false) :
    step s (.setBudget n) = { s with budget := n } := by
  simp only [step, hh]
  rw [if_neg (fun hc : false = true => Bool.noConfusion hc)]

theorem pstep_addCol {s : PState} {c : List Nat}
    {cols : List (List Nat)} (hh : s.halted = false)
    (hobs : s.obs = some cols)
    (hg : (colOk s c && s.licensed && decide (0 < s.budget))
      = true) :
    step s (.addCol c) =
      { s with obs := some (cols ++ [c]),
               budget := s.budget - 1 } := by
  simp only [step, hh]
  rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
      if_pos hg, hobs]

theorem colOk_some {s : PState} {cols : List (List Nat)}
    (h : s.obs = some cols) (c : List Nat) :
    colOk s c = (c.all (fun p => decide (p < s.occ.length))
      && !(decide (c ∈ cols))
      && (s.prot.any (fun r => obstP s r.1 r.2
          && sepCol c r.1 r.2))) := by
  unfold colOk
  rw [h]

/-! ### The round, characterized: obstruction, response, resolution -/

/-- Stage inside round `m + 2` after occurrence admission. -/
def g1 (m : Nat) : PState :=
  { occ := List.range (m + 2) ++ [m + 2],
    asserted := (List.range (m + 1)).map (fun i => (i, i + 1)),
    wit := (List.range (m + 1)).map (fun i => (i, i + 1)),
    prot := (List.range (m + 1)).map (fun i => (i, i + 1)),
    obs := some ((List.range (m + 1)).map (fun i => [i])),
    budget := 0, licensed := true, refusals := [], halted := false }

/-- Stage after witness assertion (supplied, not yet retained). -/
def gA (m : Nat) : PState :=
  { g1 m with
    asserted := (List.range (m + 1)).map (fun i => (i, i + 1))
      ++ [(m + 1, m + 2)] }

/-- Stage after witness retention. -/
def g2 (m : Nat) : PState :=
  { gA m with
    wit := (List.range (m + 1)).map (fun i => (i, i + 1))
      ++ [(m + 1, m + 2)] }

/-- The state reached inside round `m + 2` after admission,
retention, protection, and funding — but before the structural
response: the round's active obstruction is in force here. -/
def preCol (m : Nat) : PState :=
  { occ := List.range (m + 2) ++ [m + 2],
    asserted := (List.range (m + 1)).map (fun i => (i, i + 1))
      ++ [(m + 1, m + 2)],
    wit := (List.range (m + 1)).map (fun i => (i, i + 1))
      ++ [(m + 1, m + 2)],
    prot := (List.range (m + 1)).map (fun i => (i, i + 1))
      ++ [(m + 1, m + 2)],
    obs := some ((List.range (m + 1)).map (fun i => [i])),
    budget := 1, licensed := true, refusals := [], halted := false }

theorem grow_len (m : Nat) :
    (List.range (m + 2) ++ [m + 2]).length = m + 3 := by
  simp [List.length_append, List.length_range]

/-- Stage after protection (budget not yet funded). -/
def g3 (m : Nat) : PState :=
  { occ := List.range (m + 2) ++ [m + 2],
    asserted := (List.range (m + 1)).map (fun i => (i, i + 1))
      ++ [(m + 1, m + 2)],
    wit := (List.range (m + 1)).map (fun i => (i, i + 1))
      ++ [(m + 1, m + 2)],
    prot := (List.range (m + 1)).map (fun i => (i, i + 1))
      ++ [(m + 1, m + 2)],
    obs := some ((List.range (m + 1)).map (fun i => [i])),
    budget := 0, licensed := true, refusals := [], halted := false }

theorem assert_guard (m : Nat) :
    (wfPair (g1 m) (m + 1) (m + 2)
      && !(decide ((m + 1, m + 2) ∈ (g1 m).asserted))) = true := by
  show (((m + 1 : Nat) != (m + 2))
      && decide (m + 1 < (List.range (m + 2) ++ [m + 2]).length)
      && decide (m + 2 < (List.range (m + 2) ++ [m + 2]).length)
      && !(decide ((m + 1, m + 2) ∈ (List.range (m + 1)).map
            (fun i => (i, i + 1))))) = true
  rw [grow_len]
  simp only [Bool.and_eq_true, Bool.not_eq_true',
    decide_eq_false_iff_not]
  exact ⟨⟨⟨bne_iff_ne.mpr (by omega),
    decide_eq_true (by omega)⟩, decide_eq_true (by omega)⟩,
    grow_wit_not_mem m⟩

theorem wit_guard (m : Nat) :
    (wfPair (gA m) (m + 1) (m + 2)
      && (decide ((m + 1, m + 2) ∈ (gA m).asserted))
      && !(decide ((m + 1, m + 2) ∈ (gA m).wit))) = true := by
  show (((m + 1 : Nat) != (m + 2))
      && decide (m + 1 < (List.range (m + 2) ++ [m + 2]).length)
      && decide (m + 2 < (List.range (m + 2) ++ [m + 2]).length)
      && (decide ((m + 1, m + 2) ∈ (List.range (m + 1)).map
            (fun i => (i, i + 1)) ++ [(m + 1, m + 2)]))
      && !(decide ((m + 1, m + 2) ∈ (List.range (m + 1)).map
            (fun i => (i, i + 1))))) = true
  rw [grow_len]
  simp only [Bool.and_eq_true, Bool.not_eq_true',
    decide_eq_false_iff_not]
  exact ⟨⟨⟨⟨bne_iff_ne.mpr (by omega),
    decide_eq_true (by omega)⟩, decide_eq_true (by omega)⟩,
    decide_eq_true
      (List.mem_append.mpr (Or.inr List.mem_cons_self))⟩,
    grow_wit_not_mem m⟩

theorem prot_guard (m : Nat) :
    ((decide ((m + 1, m + 2) ∈ (g2 m).wit))
      && !(decide ((m + 1, m + 2) ∈ (g2 m).prot))) = true := by
  show ((decide ((m + 1, m + 2) ∈ (List.range (m + 1)).map
        (fun i => (i, i + 1)) ++ [(m + 1, m + 2)]))
    && !(decide ((m + 1, m + 2) ∈ (List.range (m + 1)).map
        (fun i => (i, i + 1))))) = true
  simp only [Bool.and_eq_true, Bool.not_eq_true',
    decide_eq_false_iff_not]
  exact ⟨decide_eq_true
    (List.mem_append.mpr (Or.inr List.mem_cons_self)),
    grow_wit_not_mem m⟩

/-- The first five events of round `m + 2` land on `preCol m`:
the graph data (occurrence, asserted difference, retention,
protection) is SUPPLIED by the driver here — the obstruction below
creates only the observation column. -/
theorem reach_preCol (m : Nat) :
    replayP [.admitOcc (m + 2), .assertWit (m + 1) (m + 2),
             .admitWit (m + 1) (m + 2), .protect (m + 1) (m + 2),
             .setBudget 1]
      (pathState m) = preCol m := by
  show step (step (step (step (step (pathState m)
    (.admitOcc (m + 2))) (.assertWit (m + 1) (m + 2)))
    (.admitWit (m + 1) (m + 2))) (.protect (m + 1) (m + 2)))
      (.setBudget 1) = preCol m
  have h1 : step (pathState m) (.admitOcc (m + 2)) = g1 m := by
    rw [pstep_admit rfl (by exact grow_fresh m)]
    rfl
  rw [h1]
  have hA : step (g1 m) (.assertWit (m + 1) (m + 2)) = gA m := by
    rw [pstep_assert rfl (assert_guard m)]
    rfl
  rw [hA]
  have h2 : step (gA m) (.admitWit (m + 1) (m + 2)) = g2 m := by
    rw [pstep_wit rfl (wit_guard m)]
    rfl
  rw [h2]
  have h3 : step (g2 m) (.protect (m + 1) (m + 2)) = g3 m := by
    rw [pstep_prot rfl (prot_guard m)]
    rfl
  rw [h3]
  rw [pstep_budget 1 rfl]
  rfl

/-- **The round's obstruction**: at `preCol m` the newly retained,
protected pair is actively obstructed — the declared observation is
blind to it. -/
theorem round_obstruction (m : Nat) :
    obstP (preCol m) (m + 1) (m + 2) = true := by
  rw [obst_agrees_when_declared (preCol m)
      ((List.range (m + 1)).map (fun i => [i])) rfl]
  simp only [preCol, Bool.and_eq_true]
  exact ⟨⟨decide_eq_true
      (List.mem_append.mpr (Or.inr List.mem_cons_self)),
    decide_eq_true
      (List.mem_append.mpr (Or.inr List.mem_cons_self))⟩,
    grow_zero m⟩

/-- **The round's response family is nonempty** — the two-rule
theorem instantiated at the growth driver's obstruction: structure
creation is available. -/
theorem round_two_rule (m : Nat) :
    [m + 1] ∈ extensionProposals (preCol m) (m + 1) (m + 2) := by
  apply extension_always_available (preCol m) (m + 1) (m + 2)
    (round_obstruction m) (by omega)
  · show m + 1 < (List.range (m + 2) ++ [m + 2]).length
    rw [grow_len]
    omega
  · exact List.mem_append.mpr (Or.inr List.mem_cons_self)

/-- **The round's resolution**: executing the structural response
lands exactly on the next characterized state. -/
theorem round_resolution (m : Nat) :
    step (preCol m) (.addCol [m + 1]) = pathState (m + 1) := by
  have hcolok : colOk (preCol m) [m + 1] = true := by
    rw [colOk_some rfl]
    have hall : (([m + 1] : List Nat).all
        (fun p => decide (p < (preCol m).occ.length))) = true := by
      show (decide (m + 1 < (List.range (m + 2) ++ [m + 2]).length)
        && true) = true
      rw [grow_len, decide_eq_true (show m + 1 < m + 3 by omega)]
      rfl
    have hany : ((preCol m).prot.any
        (fun r => obstP (preCol m) r.1 r.2
          && sepCol [m + 1] r.1 r.2)) = true := by
      apply List.any_eq_true.mpr
      refine ⟨(m + 1, m + 2),
        List.mem_append.mpr (Or.inr List.mem_cons_self), ?_⟩
      show (obstP (preCol m) (m + 1) (m + 2)
        && sepCol [m + 1] (m + 1) (m + 2)) = true
      rw [round_obstruction m, grow_col_separates m]
      rfl
    rw [hall, hany,
      decide_eq_false (show ¬ (([m + 1] : List Nat) ∈
        (List.range (m + 1)).map (fun i => ([i] : List Nat)))
        from grow_col_not_mem m)]
    rfl
  have hguard : (colOk (preCol m) [m + 1] && (preCol m).licensed
      && decide (0 < (preCol m).budget)) = true := by
    rw [hcolok]
    rfl
  rw [pstep_addCol rfl rfl hguard]
  show ({ occ := List.range (m + 2) ++ [m + 2],
          asserted := (List.range (m + 1)).map (fun i => (i, i + 1))
            ++ [(m + 1, m + 2)],
          wit := (List.range (m + 1)).map (fun i => (i, i + 1))
            ++ [(m + 1, m + 2)],
          prot := (List.range (m + 1)).map (fun i => (i, i + 1))
            ++ [(m + 1, m + 2)],
          obs := some ((List.range (m + 1)).map (fun i => [i])
            ++ [[m + 1]]),
          budget := 0, licensed := true, refusals := [],
          halted := false } : PState) = pathState (m + 1)
  unfold pathState
  rw [show List.range (m + 2) ++ [m + 2] = List.range (m + 3) from
        (List.range_succ).symm,
      show (List.range (m + 1)).map (fun i => (i, i + 1))
          ++ [(m + 1, m + 2)]
          = (List.range (m + 2)).map (fun i => (i, i + 1)) from by
        rw [(List.range_succ :
              List.range (m + 2) = List.range (m + 1) ++ [m + 1]),
            List.map_append]
        rfl,
      show (List.range (m + 1)).map (fun i => ([i] : List Nat))
          ++ [[m + 1]]
          = (List.range (m + 2)).map (fun i => ([i] : List Nat))
          from by
        rw [(List.range_succ :
              List.range (m + 2) = List.range (m + 1) ++ [m + 1]),
            List.map_append]
        rfl]

/-- The creation record: the last event of every round from round 2
on is the structural response itself — each observation column is
the recorded, replayable resolution of that round's obstruction. -/
theorem round_creation_record (m : Nat) :
    (growBlock (m + 2)).getLast? = some (.addCol [m + 1]) := rfl

/-- **The growth of the first graph, characterized at every stage.**
The grown state at stage `k + 1` is exactly the path graph on
`k + 2` occurrences with per-edge protection and one observation
column per resolved obstruction. -/
theorem graphAt_spec (k : Nat) : graphAt (k + 1) = pathState k := by
  induction k with
  | zero => decide
  | succ m ih =>
      show replayP (growHist (m + 1) ++ growBlock (m + 2)) genesisP
        = pathState (m + 1)
      rw [replay_append]
      show replayP (growBlock (m + 2)) (graphAt (m + 1))
        = pathState (m + 1)
      rw [ih]
      show step (replayP [.admitOcc (m + 2),
        .assertWit (m + 1) (m + 2), .admitWit (m + 1) (m + 2),
        .protect (m + 1) (m + 2), .setBudget 1] (pathState m))
        (.addCol [m + 1])
        = pathState (m + 1)
      rw [reach_preCol m, round_resolution m]

/-- The first graph grows without bound: one new occurrence
(0-cell) and one new witnessed edge (1-cell) per round. -/
theorem graph_growth (k : Nat) :
    (graphAt (k + 1)).occ.length = k + 2 ∧
    (graphAt (k + 1)).wit.length = k + 1 := by
  rw [graphAt_spec]
  constructor
  · show (List.range (k + 2)).length = k + 2
    exact List.length_range
  · show ((List.range (k + 1)).map (fun i => (i, i + 1))).length
      = k + 1
    rw [List.length_map]
    exact List.length_range

/-- Quiescence after every round: each protected edge is separated
by its own column — every obstruction the growth ever raised is
resolved by the structure it created. -/
theorem graphAt_quiescent (k : Nat) :
    ∀ r ∈ (graphAt (k + 1)).prot,
      obstP (graphAt (k + 1)) r.1 r.2 = false := by
  rw [graphAt_spec]
  intro r hr
  have hr' : r ∈ (List.range (k + 1)).map (fun i => (i, i + 1)) := hr
  obtain ⟨i, hi, heq⟩ := List.mem_map.mp hr'
  subst heq
  rw [obst_agrees_when_declared (pathState k)
      ((List.range (k + 1)).map (fun i => [i])) rfl]
  have hzero : zeroP ((List.range (k + 1)).map (fun i => [i]))
      i (i + 1) = false := by
    unfold zeroP sepP
    have hany : (((List.range (k + 1)).map
        (fun i => ([i] : List Nat))).any
        (fun c => sepCol c i (i + 1))) = true :=
      List.any_eq_true.mpr ⟨[i],
        List.mem_map.mpr ⟨i, hi, rfl⟩, grow_pair_separated i⟩
    rw [hany]
    rfl
  rw [hzero]
  simp

/-- The 1-complex invariant of the growth (named: the *connectivity
residue*): occurrences minus witnessed edges is 1 at every stage —
the growth never disconnects and never closes a loop. -/
theorem path_connectivity_residue (k : Nat) :
    ((graphAt (k + 1)).occ.length : Int)
      - ((graphAt (k + 1)).wit.length : Int) = 1 := by
  rw [(graph_growth k).1, (graph_growth k).2]
  omega

/-! ## 2–3. The declared cell calculus: 0-, 1-, 2-, 3-simplices

A witnessed binary relation *is* a directed graph presentation
(carrier plus binary store — identity, not force).  Everything above
dimension one is a separate declaration.  The calculus below is that
declaration, and its guards are the *ladder invariant*: a `k+1`-cell
is admissible exactly over a complete, unfilled boundary of
`k`-cells — the same obstruction shape at every dimension (an
unfilled parallel boundary), resolved the same way (create the
filling structure).  This is the passage's two-rule, recurring one
dimension up, and it is the recorded process responsible for every
cell created below. -/

structure Complex where
  c0 : List Nat
  c1 : List (Nat × Nat)
  c2 : List (Nat × Nat × Nat)
  c3 : List (Nat × Nat × Nat × Nat)
deriving Repr, DecidableEq

def emptyComplex : Complex := ⟨[], [], [], []⟩

/-- Dimension-1 horn: both endpoints present, edge absent. -/
def shell1 (C : Complex) (i j : Nat) : Bool :=
  (decide (i ∈ C.c0)) && (decide (j ∈ C.c0)) && (i != j)
    && !(decide ((i, j) ∈ C.c1))

def edgeIn (C : Complex) (i j : Nat) : Bool :=
  decide ((i, j) ∈ C.c1)

/-- Dimension-2 horn: all three boundary edges present, face
absent — two parallel edge-paths with no filler. -/
def shell2 (C : Complex) (i j k : Nat) : Bool :=
  edgeIn C i j && edgeIn C j k && edgeIn C i k
    && !(decide ((i, j, k) ∈ C.c2))

def triIn (C : Complex) (i j k : Nat) : Bool :=
  decide ((i, j, k) ∈ C.c2)

/-- Dimension-3 horn: all four boundary faces present, solid cell
absent. -/
def shell3 (C : Complex) (i j k l : Nat) : Bool :=
  triIn C j k l && triIn C i k l && triIn C i j l && triIn C i j k
    && !(decide ((i, j, k, l) ∈ C.c3))

inductive CEvent where
  | addV (v : Nat)
  | addE (i j : Nat)
  | addT (i j k : Nat)
  | addQ (i j k l : Nat)
deriving Repr, DecidableEq

/-- The declared cell step: every admission is guarded by its horn —
boundary-complete-and-unfilled, the dimension-`k` obstruction
shape. -/
def cstep (C : Complex) : CEvent → Complex
  | .addV v => if v ∈ C.c0 then C else { C with c0 := C.c0 ++ [v] }
  | .addE i j =>
      if shell1 C i j then { C with c1 := C.c1 ++ [(i, j)] } else C
  | .addT i j k =>
      if shell2 C i j k then { C with c2 := C.c2 ++ [(i, j, k)] }
      else C
  | .addQ i j k l =>
      if shell3 C i j k l then
        { C with c3 := C.c3 ++ [(i, j, k, l)] }
      else C

def creplay (h : List CEvent) (C : Complex) : Complex :=
  h.foldl cstep C

/-- **The ladder invariant, dimension 2**: a complete unfilled
boundary is the dimension-2 obstruction, and the accepted response
creates exactly the filling 2-cell — the two-rule shape, one
dimension up. -/
theorem ladder_dim2 (C : Complex) (i j k : Nat)
    (h : shell2 C i j k = true) :
    (i, j, k) ∈ (cstep C (.addT i j k)).c2 ∧
      cstep C (.addT i j k) ≠ C := by
  have hstep : cstep C (.addT i j k)
      = { C with c2 := C.c2 ++ [(i, j, k)] } := by
    simp only [cstep]
    rw [if_pos h]
  rw [hstep]
  constructor
  · exact List.mem_append.mpr (Or.inr List.mem_cons_self)
  · intro heq
    have hlen := congrArg (fun D => D.c2.length) heq
    simp only [List.length_append, List.length_cons,
      List.length_nil] at hlen
    omega

/-- **The ladder invariant, dimension 3**: same shape, one dimension
higher. -/
theorem ladder_dim3 (C : Complex) (i j k l : Nat)
    (h : shell3 C i j k l = true) :
    (i, j, k, l) ∈ (cstep C (.addQ i j k l)).c3 ∧
      cstep C (.addQ i j k l) ≠ C := by
  have hstep : cstep C (.addQ i j k l)
      = { C with c3 := C.c3 ++ [(i, j, k, l)] } := by
    simp only [cstep]
    rw [if_pos h]
  rw [hstep]
  constructor
  · exact List.mem_append.mpr (Or.inr List.mem_cons_self)
  · intro heq
    have hlen := congrArg (fun D => D.c3.length) heq
    simp only [List.length_append, List.length_cons,
      List.length_nil] at hlen
    omega

/-- The horn guard is load-bearing: filling over an incomplete
boundary is refused. -/
theorem shell_guard_load_bearing :
    cstep ⟨[0, 1, 2], [(0, 1)], [], []⟩ (.addT 0 1 2)
      = ⟨[0, 1, 2], [(0, 1)], [], []⟩ := by decide

/-! ### The four-occurrence demonstration complex -/

/-- The passage history for the complete four-vertex graph: the
grown path of stage 3, then the three chords — each a witnessed,
protected difference accepted by the passage kernel (no obstruction
arises: the grown observation already separates every chord). -/
def k4PassageHist : List PEvent :=
  growHist 3 ++
    [.assertWit 0 2, .admitWit 0 2, .protect 0 2,
     .assertWit 1 3, .admitWit 1 3, .protect 1 3,
     .assertWit 0 3, .admitWit 0 3, .protect 0 3]

/-- The passage accepts the whole K4 skeleton: six witnessed edges,
all protected, all separated (quiescent). -/
theorem k4_skeleton_from_passage :
    (replayP k4PassageHist genesisP).wit
      = [(0, 1), (1, 2), (2, 3), (0, 2), (1, 3), (0, 3)] ∧
    (replayP k4PassageHist genesisP).prot
      = [(0, 1), (1, 2), (2, 3), (0, 2), (1, 3), (0, 3)] ∧
    ((replayP k4PassageHist genesisP).prot.all
      (fun r => !obstP (replayP k4PassageHist genesisP) r.1 r.2))
      = true := by decide

/-- The declared cell log: vertices, the six passage edges, the four
triangles (each over its complete edge boundary), the solid cell
(over its complete face boundary). -/
def k4Events : List CEvent :=
  [.addV 0, .addV 1, .addV 2, .addV 3,
   .addE 0 1, .addE 1 2, .addE 2 3, .addE 0 2, .addE 1 3,
   .addE 0 3,
   .addT 0 1 2, .addT 0 1 3, .addT 0 2 3, .addT 1 2 3,
   .addQ 0 1 2 3]

def k4 : Complex := creplay k4Events emptyComplex

def k4Boundary : Complex :=
  creplay (k4Events.take 14) emptyComplex

/-- Every admission in the log fired: the full complex is exactly
the declared cells, in creation order — the replayable record of
what created each simplex. -/
theorem k4_builds :
    k4 = ⟨[0, 1, 2, 3],
          [(0, 1), (1, 2), (2, 3), (0, 2), (1, 3), (0, 3)],
          [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)],
          [(0, 1, 2, 3)]⟩ := by decide

/-- The 1-skeleton of the declared complex is exactly the
passage-grown witness store: the graph the passage built is the
graph the calculus fills. -/
theorem k4_skeleton_agrees :
    k4.c1 = (replayP k4PassageHist genesisP).wit := by decide

/-- Filling is admitted, never forced: before the last declared
event the dimension-3 horn is present and the solid cell is absent.
The horn does not fill itself. -/
theorem filling_not_forced :
    shell3 k4Boundary 0 1 2 3 = true ∧ k4Boundary.c3 = [] := by
  decide

/-! ### Named invariants of the demonstration -/

/-- The *occurrence alternation number*: the alternating sum of cell
counts. -/
def altNum (C : Complex) : Int :=
  (C.c0.length : Int) - (C.c1.length : Int)
    + (C.c2.length : Int) - (C.c3.length : Int)

/-- The alternation number along the growth: 4 after the vertices,
-2 after the edges, 2 with the four faces (the closed shell), 1
with the solid cell.  Each dimension's creation round shifts it by
the count of created cells, with alternating sign. -/
theorem altNum_stages :
    altNum (creplay (k4Events.take 4) emptyComplex) = 4 ∧
    altNum (creplay (k4Events.take 10) emptyComplex) = -2 ∧
    altNum k4Boundary = 2 ∧
    altNum k4 = 1 := by decide

/-- All two-block subsets of an occurrence list. -/
def subsetsOf : List Nat → List (List Nat)
  | [] => [[]]
  | x :: xs => subsetsOf xs ++ (subsetsOf xs).map (fun s => x :: s)

/-- The *cut census*: the number of faithful two-block observations
of a carrier that separate the designated pair — the count of
maximal-coarse observer choices (the presentation-category branching
count). -/
def cutCensus (n a b : Nat) : Nat :=
  ((subsetsOf (List.range n)).filter
    (fun A => (decide (a ∈ A)) && !(decide (b ∈ A)))).length

/-- On two occurrences the observer cut is unique; a third
occurrence doubles the census: the branching is real and grows with
the carrier. -/
theorem cut_census_growth :
    cutCensus 2 0 1 = 1 ∧ cutCensus 3 0 1 = 2 ∧
    cutCensus 4 0 1 = 4 := by decide

/-! ### The declared boundary calculus and its composite

Coefficients (integers), boundary assignments, and the vanishing of
the composite are three separate declarations/computations.  None of
them is forced by the graph: `boundary_not_forced` exhibits two
distinct boundary conventions, both compatible with the same
complex, both with vanishing composite — so the choice carries real
declared content. -/

def bd1 (e : Nat × Nat) : List (Int × Nat) :=
  [(1, e.2), (-1, e.1)]

def bd2 (t : Nat × Nat × Nat) : List (Int × (Nat × Nat)) :=
  [(1, (t.2.1, t.2.2)), (-1, (t.1, t.2.2)), (1, (t.1, t.2.1))]

/-- The opposite orientation convention. -/
def bd2' (t : Nat × Nat × Nat) : List (Int × (Nat × Nat)) :=
  [(-1, (t.2.1, t.2.2)), (1, (t.1, t.2.2)), (-1, (t.1, t.2.1))]

def bd3 (q : Nat × Nat × Nat × Nat) :
    List (Int × (Nat × Nat × Nat)) :=
  [(1, (q.2.1, q.2.2.1, q.2.2.2)), (-1, (q.1, q.2.2.1, q.2.2.2)),
   (1, (q.1, q.2.1, q.2.2.2)), (-1, (q.1, q.2.1, q.2.2.1))]

def push1 (ch : List (Int × (Nat × Nat))) : List (Int × Nat) :=
  ch.flatMap (fun p => (bd1 p.2).map (fun q => (p.1 * q.1, q.2)))

def push2 (ch : List (Int × (Nat × Nat × Nat))) :
    List (Int × (Nat × Nat)) :=
  ch.flatMap (fun p => (bd2 p.2).map (fun q => (p.1 * q.1, q.2)))

def coeffV (v : Nat) (ch : List (Int × Nat)) : Int :=
  (ch.filter (fun p => p.2 == v)).foldl (fun acc p => acc + p.1) 0

def coeffE (e : Nat × Nat) (ch : List (Int × (Nat × Nat))) : Int :=
  (ch.filter (fun p => p.2 == e)).foldl (fun acc p => acc + p.1) 0

/-- With the declared coefficients and boundaries, the composite
boundary vanishes on every declared 2-cell of the demonstration
complex. -/
theorem d2_zero_triangles :
    (k4.c2.all (fun t => k4.c0.all (fun v =>
      coeffV v (push1 (bd2 t)) == 0))) = true := by decide

/-- And on the declared 3-cell. -/
theorem d2_zero_tet :
    (k4.c1.all (fun e =>
      coeffE e (push2 (bd3 (0, 1, 2, 3))) == 0)) = true := by decide

/-- Two distinct boundary conventions, both with vanishing
composite on the same cell: the boundary assignment is a
declaration with real content, not a consequence of the graph. -/
theorem boundary_not_forced :
    bd2 (0, 1, 2) ≠ bd2' (0, 1, 2) ∧
    (k4.c0.all (fun v =>
      coeffV v (push1 (bd2 (0, 1, 2))) == 0)) = true ∧
    (k4.c0.all (fun v =>
      coeffV v (push1 (bd2' (0, 1, 2))) == 0)) = true := by decide

end HigherStructure

