import Derivation.PrimDiff
import Derivation.PrimitiveCore

/-!
# The passage through Primitive Difference

Stage VI of the contact-and-passage run.  A minimal, self-contained
dynamics carrying exactly the passage chain, written here in the names
of the objects this development actually constructs:

  asserted witness → retained witness → faithful presentation →
  declared observation → observer zero → guarded collapse →
  active obstruction → complete response menu →
  repair family | extension family → licensing and budget →
  replay → re-evaluation → refusal record | terminal →
  represented next family

with one status per arrow (theorem, declaration, or false without
extra hypotheses), necessity countermodels, and the P1–P8 theorems.

## Provenance of the station names

The thirteen arrows and their station labels were SUPPLIED, not
derived.  `prompt/ultra_prompt_pr12.md` lines 453-471 give the chain
verbatim, under the instruction "construct the exact passage".  They
are an EXTERNALLY IMPOSED CHALLENGE in the sense of the assumption
discipline, and nothing below treats the carving as derived.

The labels above are this file's own object names; the supplied labels
are retained beside them in `paper/primitive_difference_passage.md` so
that the two vocabularies stay distinguishable rather than merging.

Two supplied station names were ever adopted as Lean identifiers --
`ZeroRel` and `ActiveObstruction`, both defined in
`Derivation.DiffInterface`, the first already classified native.  The
remaining twelve appear in this development only as prose.  One
supplied word was refused on contact: the chain says "protected",
while the stage field is and remains `guarded`.

The single deliberate refinement over the sealed `Completion.obstC`:
observation here is an `Option` — `none` is *pre-observational*, not
"an observer that sees nothing".  Active obstruction is written with
three factors and PROVED equal to the product of four TOTAL gates
(retained, protected, observation declared, observer-zero on the
pair; `obstP_factors`), no one of which follows from the other three
(`gate_zero_independent`, `gate_declared_independent`,
`gate_protection_independent`, `gate_retention_independent`).

The `none => false` branch of `obstP` is a DECLARED_POLICY, not a
derived necessity: `obst_requires_observation` unfolds that branch
and proves nothing about whether it had to be chosen.  The rival
reading — treat `none` as an observation declaring no columns — is
named (`obstEmptyObs`), and the two readings are proved to agree on
every declared state (`obst_policies_agree_when_declared`) and to
differ at one named pre-observational state
(`obst_policies_differ`).  The relation to the sealed
three-condition predicate is proved separately
(`obst_agrees_when_declared`, `obst_diverges_when_undeclared`).
No complete characterization of every undeclared state on which the
two policies differ is claimed.

Naming discipline: "forced", "complete", "exhaustive" appear only
with a proof over a declared finite universe.  Refusal is a record;
the terminal is absorbing; proposal is not execution.
-/

namespace PrimitivePassage

/-! ## State and events

Every notion the passage separates is a separate field.  Positions in
`occ` are occurrence identities (0-cells); `wit` is the retained
positive witness store (1-cells); `prot` is the protected-demand
store; `obs` is the declared observation, `none` before any observer
is admitted. -/

structure PState where
  occ : List Nat
  asserted : List (Nat × Nat)
  wit : List (Nat × Nat)
  prot : List (Nat × Nat)
  obs : Option (List (List Nat))
  budget : Nat
  licensed : Bool
  refusals : List (Nat × Nat)
  halted : Bool
deriving Repr, DecidableEq

def genesisP : PState :=
  { occ := [], asserted := [], wit := [], prot := [], obs := none,
    budget := 0, licensed := true, refusals := [], halted := false }

inductive PEvent where
  | admitOcc (t : Nat)
  | assertWit (i j : Nat)
  | admitWit (i j : Nat)
  | protect (i j : Nat)
  | declareObs
  | refineCol (v : List Nat) (p : Nat)
  | addCol (c : List Nat)
  | refuse (i j : Nat)
  | setBudget (n : Nat)
  | setLicense (b : Bool)
  | halt
deriving Repr, DecidableEq

/-! ## Observation semantics -/

/-- One column separates two occurrence positions. -/
def sepCol (c : List Nat) (i j : Nat) : Bool :=
  (decide (i ∈ c)) != (decide (j ∈ c))

/-- Observer separation, only meaningful under a declared
observation. -/
def sepP (cols : List (List Nat)) (i j : Nat) : Bool :=
  cols.any (fun c => sepCol c i j)

/-- The zero relation of a declared observation: no declared column
separates.  Defined only on the declared side — a pre-observational
state has no zero relation at all. -/
def zeroP (cols : List (List Nat)) (i j : Nat) : Bool :=
  !sepP cols i j

theorem zeroP_cons (c : List Nat) (rest : List (List Nat))
    (i j : Nat) :
    zeroP (c :: rest) i j = ((!sepCol c i j) && zeroP rest i j) := by
  unfold zeroP sepP
  simp [List.any_cons, Bool.not_or]

/-! ## Active obstruction: three written factors, four proved gates -/

/-- Active obstruction: the pair is retained, protected, an
observation IS declared, and the declared observation does not
separate the pair.

As written below this is a product of THREE factors: membership in
`wit`, membership in `prot`, and one factor reading `obs` that
answers `false` before any observation is declared
(`obstP_strict_factors`).  `obstP_factors` proves it EQUAL to the
product of four TOTAL gates, and the four `gate_*_independent`
theorems prove that none of those gates follows from the other
three.  Cite the two together, never `obstP_factors` alone: any
`Bool` splits as `true && c`, so the factorization by itself is
near-definitional and it is the independence theorems that make the
four-way reading non-trivial.  Neither statement claims that four is
the only possible decomposition of this predicate. -/
def obstP (s : PState) (i j : Nat) : Bool :=
  (decide ((i, j) ∈ s.wit)) && (decide ((i, j) ∈ s.prot))
    && (match s.obs with
        | none => false
        | some cols => zeroP cols i j)

/-! ### The four gates

Four TOTAL `Bool` functions of the state.  `retainedP` reads `wit`,
`protectedP` reads `prot`, and `declaredP` and `zeroDeclP` BOTH read
`obs` — which is exactly why they are not jointly free
(`obs_gates_not_both_false`).  `zeroDeclP` must answer on
pre-observational states, where there is no zero relation to consult
at all; it answers `true` there.  That value is a DECLARED
CONVENTION (vacuous truth), exhibited by `undeclared_gates` and
priced by `obs_gates_not_both_false`.  It is not a claim that a
pre-observational state carries a blind observer:
`obst_requires_observation` shows the convention can never make
anything obstructed. -/

/-- Gate 1: the pair is retained. -/
def retainedP (s : PState) (i j : Nat) : Bool :=
  decide ((i, j) ∈ s.wit)

/-- Gate 2: the pair carries a protected demand. -/
def protectedP (s : PState) (i j : Nat) : Bool :=
  decide ((i, j) ∈ s.prot)

/-- Gate 3: an observation is declared. -/
def declaredP (s : PState) : Bool :=
  match s.obs with
  | none => false
  | some _ => true

/-- Gate 4: the declared observation does not separate the pair —
vacuously `true` before any observation is declared (DECLARED
CONVENTION; see `undeclared_gates`, `obs_gates_not_both_false`). -/
def zeroDeclP (s : PState) (i j : Nat) : Bool :=
  match s.obs with
  | none => true
  | some cols => zeroP cols i j

/-- The ALTERNATIVE convention for gate 4: `false` before any
observation is declared.  This is exactly the third factor of
`obstP` as written (`obstP_strict_factors`).  It is declared here
only so that the claim about the convention is a theorem
(`strict_gate_entails_declared`) and not a remark; no other
declaration uses it. -/
def zeroStrictP (s : PState) (i j : Nat) : Bool :=
  match s.obs with
  | none => false
  | some cols => zeroP cols i j

/-- `obstP` as written is a product of THREE factors, the third being
`zeroStrictP`.  Definitional. -/
theorem obstP_strict_factors (s : PState) (i j : Nat) :
    obstP s i j =
      (retainedP s i j && protectedP s i j && zeroStrictP s i j) :=
  rfl

/-- **The four-gate factorization.**  Active obstruction is the
product of the four total gates, at every state and every pair: an
identity of `Bool`-valued functions, not a table of examples.  Its
two directions are `obst_of_gates` and `gates_of_obst`.

By itself this is near-definitional — the gates are defined so that
it holds, and any `Bool` splits as `true && c`.  What makes the
four-way reading non-trivial is the four `gate_*_independent`
theorems.  It does NOT claim that this decomposition is the only
one, nor that the four gates are jointly free
(`obs_gates_not_both_false` refutes that). -/
theorem obstP_factors (s : PState) (i j : Nat) :
    obstP s i j =
      (retainedP s i j && protectedP s i j && declaredP s
        && zeroDeclP s i j) := by
  unfold obstP retainedP protectedP declaredP zeroDeclP
  cases s.obs <;> simp

/-- **Sufficiency, generally.**  All four gates true gives
obstruction, at every state and every pair — not at one witness. -/
theorem obst_of_gates (s : PState) (i j : Nat)
    (h1 : retainedP s i j = true) (h2 : protectedP s i j = true)
    (h3 : declaredP s = true) (h4 : zeroDeclP s i j = true) :
    obstP s i j = true := by
  rw [obstP_factors, h1, h2, h3, h4]
  rfl

/-- **Necessity of each gate, generally.**  Obstruction gives all
four gates.  Necessity is relative to THIS predicate: each gate is
necessary for `obstP`, not for any notion of obstruction. -/
theorem gates_of_obst (s : PState) (i j : Nat)
    (h : obstP s i j = true) :
    retainedP s i j = true ∧ protectedP s i j = true
      ∧ declaredP s = true ∧ zeroDeclP s i j = true := by
  rw [obstP_factors] at h
  simp only [Bool.and_eq_true] at h
  exact ⟨h.1.1.1, h.1.1.2, h.1.2, h.2⟩

/-- Obstruction depends on AT MOST three stores: two states agreeing
on `wit`, `prot` and `obs` obstruct the same pairs, whatever their
occurrences, assertions, budget, license, refusals or terminal flag.
This is what licenses "no hidden store is read".  That each of the
three IS in fact read is a separate matter, witnessed by
`obst_conditions_independent` (whose states differ from
`gateWitnessAll` in exactly `wit`, `prot` and `obs` respectively) —
not by this theorem. -/
theorem obstP_reads_three_stores (s t : PState) (i j : Nat)
    (hw : s.wit = t.wit) (hp : s.prot = t.prot)
    (ho : s.obs = t.obs) : obstP s i j = obstP t i j := by
  unfold obstP
  rw [hw, hp, ho]

/-- **The pre-observational convention, exhibited.**  Before any
observation is declared, gate 3 is false and gate 4 is vacuously
true.  The `true` is the declared convention;
`strict_gate_entails_declared` shows what it buys, and
`obs_gates_not_both_false` what it costs. -/
theorem undeclared_gates (s : PState) (i j : Nat)
    (h : s.obs = none) :
    declaredP s = false ∧ zeroDeclP s i j = true := by
  unfold declaredP zeroDeclP
  rw [h]
  exact ⟨rfl, rfl⟩

/-- **The four gates are not jointly free.**  Gates 3 and 4 both read
`obs`, and the convention makes the joint value `(false, false)`
unreachable.  The other three joint values do occur, at the
witnesses of `obst_conditions_independent` — so "exactly one of the
four joint values is unreachable" is licensed by the two theorems
TOGETHER, not by this one.  Consequently
`obst_conditions_independent` is independence in the "no gate
follows from the other three" sense only; the stronger reading —
that all sixteen gate valuations occur — is FALSE and is not claimed
here. -/
theorem obs_gates_not_both_false (s : PState) (i j : Nat) :
    (declaredP s || zeroDeclP s i j) = true := by
  unfold declaredP zeroDeclP
  cases s.obs <;> rfl

/-- **The convention is load-bearing, as a theorem.**  Under the
alternative convention (`zeroStrictP`, i.e. `none => false`) the
fourth gate ENTAILS the third, so the two could not be separately
falsified and the omission witness `gateWitnessNoDeclaration` would
be unavailable.  This is why gate 4 is defined with `none => true`
and not otherwise. -/
theorem strict_gate_entails_declared (s : PState) (i j : Nat)
    (h : zeroStrictP s i j = true) : declaredP s = true := by
  unfold zeroStrictP at h
  unfold declaredP
  revert h
  cases s.obs with
  | none => intro h; exact Bool.noConfusion h
  | some c => intro _; rfl

/-- **P1, half 1 — retention and observation are separate fields.**
States differing only in `obs` retain the same witnesses.

Exact status: definitional.  The proof term is `Iff.rfl`; `wit` and
`obs` are distinct fields of `PState`, so this records the field
separation and is true by projection.  It says retention is readable
with no observation declared; it does not say obstruction cannot
precede observation — that is the DECLARED_POLICY at `obstP`. -/
theorem wit_independent_of_obs (s : PState)
    (o : Option (List (List Nat))) (i j : Nat) :
    ((i, j) ∈ ({ s with obs := o } : PState).wit)
      ↔ ((i, j) ∈ s.wit) := Iff.rfl

/-- **P1, half 2 — the declaration gate, unfolded.**  Under the
selected semantics a pre-observational state obstructs nothing,
whatever is retained and protected.

Exact status: DECLARED_POLICY unfolding, NOT a necessity proof.  The
`none => false` branch is part of the definition of `obstP`, so this
lemma restates that branch and is true by definition; it establishes
nothing about whether the branch had to be chosen, and it is not
evidence in any argument about the choice.  That the choice has
content is a separate, proved matter: `obst_policies_differ`
exhibits a named state where this reading and the rival
empty-observer reading (`obstEmptyObs`) disagree. -/
theorem obst_requires_observation (s : PState) (i j : Nat)
    (h : s.obs = none) : obstP s i j = false := by
  unfold obstP
  rw [h]
  simp

/-- The declared-observation refinement, exact relation to the sealed
three-condition reading: once an observation is declared, the
declaration gate is discharged and `obstP` reads as retained,
protected, and observer-zero on the declared columns.  (Gate-wise:
`declaredP` is `true` there, so `obstP_factors` collapses to the same
three.) -/
theorem obst_agrees_when_declared (s : PState)
    (cols : List (List Nat)) (h : s.obs = some cols) (i j : Nat) :
    obstP s i j =
      ((decide ((i, j) ∈ s.wit)) && (decide ((i, j) ∈ s.prot))
        && zeroP cols i j) := by
  unfold obstP
  rw [h]

/-- **Two Bool values at one pre-observational state.**  Second
conjunct: `obstP` is `false` at the state below — the same state and
the same value as the "NOT declared" row of
`obst_conditions_independent`.  First conjunct: the written-out
expression `decide ((0,1) ∈ [(0,1)]) && decide ((0,1) ∈ [(0,1)]) &&
zeroP [] 0 1` is `true`.

Exact status, METATHEORY: that the first conjunct IS the rival
empty-observer reading applied to THAT state is not checked here.
The lists are written out, not projected from the state, so the
first conjunct is a closed truth mentioning no state at all.  For
the checked comparison of the two readings — same state, both
predicates applied to it — use `obst_policies_differ` together with
`obst_policies_agree_when_declared`; this theorem is retained only
as the historical witness and is not evidence of divergence. -/
theorem obst_diverges_when_undeclared :
    (((decide (((0 : Nat), (1 : Nat)) ∈ [((0 : Nat), (1 : Nat))]))
        && (decide (((0 : Nat), (1 : Nat)) ∈ [((0 : Nat), (1 : Nat))]))
        && zeroP [] 0 1) = true) ∧
    obstP { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)],
            prot := [(0, 1)],
            obs := none, budget := 0, licensed := true,
            refusals := [], halted := false } 0 1 = false := by
  constructor
  · decide
  · decide

/-! ### The rival pre-observational reading, named and compared

The `none => false` branch of `obstP` is a DECLARED_POLICY.  The
rival policy — treat "no observation declared" as "an observation
declaring no columns", i.e. an observer that separates nothing — is
named here so that the comparison is a checked theorem about two
predicates applied to one state, not a remark. -/

/-- The rival reading of a pre-observational state. -/
def obstEmptyObs (s : PState) (i j : Nat) : Bool :=
  (decide ((i, j) ∈ s.wit)) && (decide ((i, j) ∈ s.prot))
    && (match s.obs with
        | none => zeroP [] i j
        | some cols => zeroP cols i j)

/-- Once an observation IS declared the two policies agree: the whole
difference between them lives on pre-observational states. -/
theorem obst_policies_agree_when_declared (s : PState)
    (cols : List (List Nat)) (h : s.obs = some cols) (i j : Nat) :
    obstP s i j = obstEmptyObs s i j := by
  unfold obstP obstEmptyObs
  rw [h]

/-- A pre-observational state that is retained and protected. -/
def preRetainedObstructed : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)],
    prot := [(0, 1)],
    obs := none, budget := 0, licensed := true,
    refusals := [], halted := false }

/-- **The two policies genuinely differ**, at one named state, with
both predicates applied to that same state.  This is the checked
content that `obst_diverges_when_undeclared` does not carry: the
selected semantics is a choice with consequences, and this theorem
prices it.  It does NOT show the selected branch was forced. -/
theorem obst_policies_differ :
    obstEmptyObs preRetainedObstructed 0 1 = true ∧
    obstP preRetainedObstructed 0 1 = false := by
  constructor
  · decide
  · decide

/-! ### Gate-omission witnesses

Five concrete states over two occurrences, all read at the pair
`(0, 1)`.  Each of the first four falsifies exactly one gate while
satisfying the other three; the fifth satisfies all four.  They are
named definitions so that the omission theorems can state the gate
values themselves, not only the obstruction verdict. -/

/-- Retained, protected, observation declared — and the declared
observation separates the pair, so gate 4 fails. -/
def gateWitnessNoZero : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)],
    prot := [(0, 1)],
    obs := some [[0]], budget := 0, licensed := true,
    refusals := [], halted := false }

/-- Retained, protected, vacuously zero — and no observation is
declared, so gate 3 fails. -/
def gateWitnessNoDeclaration : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)],
    prot := [(0, 1)],
    obs := none, budget := 0, licensed := true,
    refusals := [], halted := false }

/-- Retained, declared, zero — and the pair carries no protected
demand, so gate 2 fails. -/
def gateWitnessNoProtection : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)],
    prot := [],
    obs := some [], budget := 0, licensed := true,
    refusals := [], halted := false }

/-- Protected, declared, zero — and the pair is not retained, so
gate 1 fails. -/
def gateWitnessNoRetention : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [],
    prot := [(0, 1)],
    obs := some [], budget := 0, licensed := true,
    refusals := [], halted := false }

/-- All four gates. -/
def gateWitnessAll : PState :=
  { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)],
    prot := [(0, 1)],
    obs := some [], budget := 0, licensed := true,
    refusals := [], halted := false }

/-- **P5, the witness record.**  Five concrete states with all four
gate values stated at each: for every gate there is a state
satisfying the other three gates, falsifying that one, and NOT
obstructed; the fifth satisfies all four and IS obstructed, so the
four-gate conjunction is not empty.  This theorem is the table.  The
quantified consequences — that no gate follows from the other three,
and that no maximal proper subset of the gates entails obstruction —
are the four `gate_*_independent` theorems below, stated there and
not merely read off here.

Exact scope: these four gates over `PState`, at the pair `(0, 1)`.
It is NOT claimed that all sixteen gate valuations occur
(`obs_gates_not_both_false` refutes that), nor that no other
predicate could serve as an activation condition. -/
theorem obst_conditions_independent :
    -- gate 4 omitted: retained, protected, declared, but the
    -- declared observation separates the pair
    (retainedP gateWitnessNoZero 0 1 = true
      ∧ protectedP gateWitnessNoZero 0 1 = true
      ∧ declaredP gateWitnessNoZero = true
      ∧ zeroDeclP gateWitnessNoZero 0 1 = false
      ∧ obstP gateWitnessNoZero 0 1 = false) ∧
    -- gate 3 omitted: retained, protected, vacuously zero, but no
    -- observation is declared
    (retainedP gateWitnessNoDeclaration 0 1 = true
      ∧ protectedP gateWitnessNoDeclaration 0 1 = true
      ∧ declaredP gateWitnessNoDeclaration = false
      ∧ zeroDeclP gateWitnessNoDeclaration 0 1 = true
      ∧ obstP gateWitnessNoDeclaration 0 1 = false) ∧
    -- gate 2 omitted: retained, declared, zero, but not protected
    (retainedP gateWitnessNoProtection 0 1 = true
      ∧ protectedP gateWitnessNoProtection 0 1 = false
      ∧ declaredP gateWitnessNoProtection = true
      ∧ zeroDeclP gateWitnessNoProtection 0 1 = true
      ∧ obstP gateWitnessNoProtection 0 1 = false) ∧
    -- gate 1 omitted: protected, declared, zero, but not retained
    (retainedP gateWitnessNoRetention 0 1 = false
      ∧ protectedP gateWitnessNoRetention 0 1 = true
      ∧ declaredP gateWitnessNoRetention = true
      ∧ zeroDeclP gateWitnessNoRetention 0 1 = true
      ∧ obstP gateWitnessNoRetention 0 1 = false) ∧
    -- all four gates: obstructed
    (retainedP gateWitnessAll 0 1 = true
      ∧ protectedP gateWitnessAll 0 1 = true
      ∧ declaredP gateWitnessAll = true
      ∧ zeroDeclP gateWitnessAll 0 1 = true
      ∧ obstP gateWitnessAll 0 1 = true) := by
  decide

/-! ### P5, the quantified form

One theorem per gate.  Each states, over ALL states and ALL pairs,
that the other three gates entail neither the omitted gate nor
obstruction.  Together they say: no gate follows from the
conjunction of the other three, and no maximal proper subset of the
four gates entails obstruction — hence no proper subset does, every
smaller subset being contained in a maximal one. -/

/-- **Gate 4 is independent.**  Witness `gateWitnessNoZero`. -/
theorem gate_zero_independent :
    (¬ (∀ (s : PState) (i j : Nat),
        retainedP s i j = true → protectedP s i j = true →
        declaredP s = true → zeroDeclP s i j = true)) ∧
    (¬ (∀ (s : PState) (i j : Nat),
        retainedP s i j = true → protectedP s i j = true →
        declaredP s = true → obstP s i j = true)) := by
  constructor
  · intro h
    exact absurd (h gateWitnessNoZero 0 1 (by decide) (by decide)
      (by decide)) (by decide)
  · intro h
    exact absurd (h gateWitnessNoZero 0 1 (by decide) (by decide)
      (by decide)) (by decide)

/-- **Gate 3 is independent.**  Witness `gateWitnessNoDeclaration`.
This clause is exactly the one the pre-observational convention buys
(`strict_gate_entails_declared`). -/
theorem gate_declared_independent :
    (¬ (∀ (s : PState) (i j : Nat),
        retainedP s i j = true → protectedP s i j = true →
        zeroDeclP s i j = true → declaredP s = true)) ∧
    (¬ (∀ (s : PState) (i j : Nat),
        retainedP s i j = true → protectedP s i j = true →
        zeroDeclP s i j = true → obstP s i j = true)) := by
  constructor
  · intro h
    exact absurd (h gateWitnessNoDeclaration 0 1 (by decide)
      (by decide) (by decide)) (by decide)
  · intro h
    exact absurd (h gateWitnessNoDeclaration 0 1 (by decide)
      (by decide) (by decide)) (by decide)

/-- **Gate 2 is independent.**  Witness `gateWitnessNoProtection`. -/
theorem gate_protection_independent :
    (¬ (∀ (s : PState) (i j : Nat),
        retainedP s i j = true → declaredP s = true →
        zeroDeclP s i j = true → protectedP s i j = true)) ∧
    (¬ (∀ (s : PState) (i j : Nat),
        retainedP s i j = true → declaredP s = true →
        zeroDeclP s i j = true → obstP s i j = true)) := by
  constructor
  · intro h
    exact absurd (h gateWitnessNoProtection 0 1 (by decide)
      (by decide) (by decide)) (by decide)
  · intro h
    exact absurd (h gateWitnessNoProtection 0 1 (by decide)
      (by decide) (by decide)) (by decide)

/-- **Gate 1 is independent.**  Witness `gateWitnessNoRetention`. -/
theorem gate_retention_independent :
    (¬ (∀ (s : PState) (i j : Nat),
        protectedP s i j = true → declaredP s = true →
        zeroDeclP s i j = true → retainedP s i j = true)) ∧
    (¬ (∀ (s : PState) (i j : Nat),
        protectedP s i j = true → declaredP s = true →
        zeroDeclP s i j = true → obstP s i j = true)) := by
  constructor
  · intro h
    exact absurd (h gateWitnessNoRetention 0 1 (by decide)
      (by decide) (by decide)) (by decide)
  · intro h
    exact absurd (h gateWitnessNoRetention 0 1 (by decide)
      (by decide) (by decide)) (by decide)

/-! ## The step function

Guards mirror the sealed kernel's discipline: dedup admission,
well-formedness at protection, certificate-bearing refusal, budget
and license gates on structure creation, absorbing terminal. -/

def wfPair (s : PState) (i j : Nat) : Bool :=
  (i != j) && (decide (i < s.occ.length))
    && (decide (j < s.occ.length))

/-- Same-level acceptance: refine an existing column by one point.
The move must discharge some obstruction and break no protected
separation (monotone preservation, as in the sealed kernel). -/
def refineOk (s : PState) (v : List Nat) (p : Nat) : Bool :=
  match s.obs with
  | none => false
  | some cols =>
      (decide (v ∈ cols)) && (decide (p < s.occ.length))
        && !(decide (p ∈ v))
        && (s.prot.any (fun r =>
              obstP s r.1 r.2
                && sepCol (p :: v) r.1 r.2))
        && (s.prot.all (fun r =>
              !sepP cols r.1 r.2 || sepP (cols.map
                (fun c => if c = v then p :: c else c)) r.1 r.2))

/-- Structure-creating acceptance: a new column, in bounds, not
already present, separating some obstructed pair. -/
def colOk (s : PState) (c : List Nat) : Bool :=
  match s.obs with
  | none => false
  | some cols =>
      c.all (fun p => decide (p < s.occ.length))
        && !(decide (c ∈ cols))
        && (s.prot.any (fun r => obstP s r.1 r.2 && sepCol c r.1 r.2))

def step (s : PState) : PEvent → PState
  | .admitOcc t =>
      if s.halted then s
      else if t ∈ s.occ then s else { s with occ := s.occ ++ [t] }
  | .assertWit i j =>
      if s.halted then s
      else if wfPair s i j && !(decide ((i, j) ∈ s.asserted)) then
        { s with asserted := s.asserted ++ [(i, j)] }
      else s
  | .admitWit i j =>
      if s.halted then s
      else if wfPair s i j && (decide ((i, j) ∈ s.asserted))
          && !(decide ((i, j) ∈ s.wit)) then
        { s with wit := s.wit ++ [(i, j)] }
      else s
  | .protect i j =>
      if s.halted then s
      else if (decide ((i, j) ∈ s.wit))
          && !(decide ((i, j) ∈ s.prot)) then
        { s with prot := s.prot ++ [(i, j)] }
      else s
  | .declareObs =>
      if s.halted then s
      else match s.obs with
        | none => { s with obs := some [] }
        | some _ => s
  | .refineCol v p =>
      if s.halted then s
      else if refineOk s v p && decide (0 < s.budget) then
        match s.obs with
        | none => s
        | some cols =>
            { s with
              obs := some (cols.map
                (fun c => if c = v then p :: c else c)),
              budget := s.budget - 1 }
      else s
  | .addCol c =>
      if s.halted then s
      else if colOk s c && s.licensed && decide (0 < s.budget) then
        match s.obs with
        | none => s
        | some cols =>
            { s with obs := some (cols ++ [c]),
                     budget := s.budget - 1 }
      else s
  | .refuse i j =>
      if s.halted then s
      else if obstP s i j && !(decide ((i, j) ∈ s.refusals)) then
        { s with refusals := s.refusals ++ [(i, j)] }
      else s
  | .setBudget n => if s.halted then s else { s with budget := n }
  | .setLicense b =>
      if s.halted then s else { s with licensed := b }
  | .halt => { s with halted := true }

def replayP (h : List PEvent) (s : PState) : PState := h.foldl step s

/-! ## Arrow statuses, proved

Each passage arrow is a theorem, a declaration (an admission event is
required, with a countermodel showing the arrow is false without it),
or false without extra hypotheses. -/

/-- **asserted witness → retained witness is a DECLARATION.**
The asserted-difference store (`assertWit`, the supplied positive
witness) and the retained store (`admitWit`) are separate fields with
separate admission events: an asserted Primitive Difference does not
retain itself.  Concrete pre-retention witness: after assertion the
asserted store carries the pair and the retained store is empty. -/
theorem assertion_not_retained :
    (replayP [.admitOcc 7, .admitOcc 8, .assertWit 0 1]
      genesisP).asserted = [(0, 1)] ∧
    (replayP [.admitOcc 7, .admitOcc 8, .assertWit 0 1]
      genesisP).wit = [] := by
  constructor
  · decide
  · decide

/-- Occurrence admission alone asserts and retains nothing. -/
theorem retention_not_free :
    (replayP [.admitOcc 7, .admitOcc 8] genesisP).asserted = [] ∧
    (replayP [.admitOcc 7, .admitOcc 8] genesisP).wit = [] := by
  constructor
  · decide
  · decide

/-- Retention requires a prior assertion: on a live state with the
pair unasserted, the retention event is inert. -/
theorem retention_requires_assertion (s : PState) (i j : Nat)
    (hh : s.halted = false) (h : ¬ ((i, j) ∈ s.asserted)) :
    step s (.admitWit i j) = s := by
  have hg : ¬ ((wfPair s i j && (decide ((i, j) ∈ s.asserted))
      && !(decide ((i, j) ∈ s.wit))) = true) := by
    intro hc
    simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
    exact h hc.1.2
  simp only [step, hh]
  rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
      if_neg hg]

/-- Retention, once admitted, is a theorem-level invariant: the
witness store is append-only under every event. -/
theorem retention_persists (s : PState) (e : PEvent) (i j : Nat)
    (h : (i, j) ∈ s.wit) : (i, j) ∈ (step s e).wit := by
  cases e <;> simp only [step] <;> repeat' split
  all_goals
    first
      | exact h
      | (simp only [List.mem_append]; exact Or.inl h)

/-- The asserted store is append-only too: assertion persists. -/
theorem assertion_persists (s : PState) (e : PEvent) (i j : Nat)
    (h : (i, j) ∈ s.asserted) : (i, j) ∈ (step s e).asserted := by
  cases e <;> simp only [step] <;> repeat' split
  all_goals
    first
      | exact h
      | (simp only [List.mem_append]; exact Or.inl h)

/-! ### Transport: the native kernel enters the passage

The composition of `PrimitiveCore` into the passage is a theorem,
not a diagram: the asserted store of a replayed state induces a
`PrimitiveCore.Setting`, the off-diagonal invariant of the assertion
guard supplies irreflexivity, and the canonical two-element kernel
reaches a pre-retention passage state realizing candidate A with the
retained store still empty. -/

/-- The setting induced by a passage state at designated
endpoints: the asserted store is the relation, the retained and
protected stores are the corresponding fields, no operations are
admitted. -/
def inducedSetting (s : PState) (a b : Nat) :
    PrimitiveCore.Setting :=
  { X := Nat,
    r := fun x y => (x, y) ∈ s.asserted,
    a := a, b := b,
    ret := fun x y => (x, y) ∈ s.wit,
    prot := fun x y => (x, y) ∈ s.prot,
    Ops := fun _ => False }

/-- The assertion guard keeps the asserted store off-diagonal:
one step preserves the invariant. -/
theorem asserted_offdiag_step (s : PState)
    (hinv : ∀ p ∈ s.asserted, p.1 ≠ p.2) (e : PEvent) :
    ∀ p ∈ (step s e).asserted, p.1 ≠ p.2 := by
  cases e <;> simp only [step] <;> repeat' split
  all_goals
    first
      | exact hinv
      | (rename_i i j hh hg
         intro p hp
         rcases List.mem_append.mp hp with hp' | hp'
         · exact hinv p hp'
         · have hij : i ≠ j := by
             simp only [Bool.and_eq_true] at hg
             have h1 := hg.1
             simp only [wfPair, Bool.and_eq_true, bne_iff_ne] at h1
             exact h1.1.1
           cases List.mem_singleton.mp hp'
           exact hij)

/-- The invariant from genesis: every replayed state has an
off-diagonal asserted store. -/
theorem asserted_offdiag (h : List PEvent) :
    ∀ p ∈ (replayP h genesisP).asserted, p.1 ≠ p.2 := by
  suffices hgen : ∀ (s : PState),
      (∀ p ∈ s.asserted, p.1 ≠ p.2) →
        ∀ p ∈ (replayP h s).asserted, p.1 ≠ p.2 by
    exact hgen genesisP (by intro p hp; cases hp)
  induction h with
  | nil => intro s hs; exact hs
  | cons e rest ih =>
      intro s hs
      exact ih (step s e) (asserted_offdiag_step s hs e)

/-- The retained store never outruns the asserted store: one step. -/
theorem retained_sub_asserted_step (s : PState)
    (hinv : ∀ p ∈ s.wit, p ∈ s.asserted) (e : PEvent) :
    ∀ p ∈ (step s e).wit, p ∈ (step s e).asserted := by
  cases e <;> simp only [step] <;> repeat' split
  all_goals
    first
      | exact hinv
      | (intro p hp
         simp only [List.mem_append]
         exact Or.inl (hinv p hp))
      | (rename_i i j hh hg
         intro p hp
         rcases List.mem_append.mp hp with hp' | hp'
         · exact hinv p hp'
         · have hmem : (i, j) ∈ s.asserted := by
             simp only [Bool.and_eq_true, decide_eq_true_eq] at hg
             exact hg.1.2
           cases List.mem_singleton.mp hp'
           exact hmem)

/-- From genesis: retention is always retention OF an assertion. -/
theorem retained_sub_asserted (h : List PEvent) :
    ∀ p ∈ (replayP h genesisP).wit,
      p ∈ (replayP h genesisP).asserted := by
  suffices hgen : ∀ (s : PState),
      (∀ p ∈ s.wit, p ∈ s.asserted) →
        ∀ p ∈ (replayP h s).wit, p ∈ (replayP h s).asserted by
    exact hgen genesisP (by intro p hp; cases hp)
  induction h with
  | nil => intro s hs; exact hs
  | cons e rest ih =>
      intro s hs
      exact ih (step s e) (retained_sub_asserted_step s hs e)

/-- **Transport, general form**: any replayed state whose asserted
store carries the designated pair induces a setting satisfying
candidate A — the witness from membership, irreflexivity from the
off-diagonal invariant. -/
theorem assert_transport (h : List PEvent) (a b : Nat)
    (hm : (a, b) ∈ (replayP h genesisP).asserted) :
    PrimitiveCore.A (inducedSetting (replayP h genesisP) a b) := by
  constructor
  · exact hm
  · intro x hx
    exact asserted_offdiag h (x, x) hx rfl

/-- The canonical pre-retention state: two occurrences, one asserted
difference, nothing retained. -/
def preRetained : PState :=
  replayP [.admitOcc 0, .admitOcc 1, .assertWit 0 1] genesisP

/-- **The two-element kernel enters the passage pre-retention**: the
induced setting satisfies candidate A while the retained store is
still empty — Primitive Difference is in the passage before
retention, and retention is a further priced step. -/
theorem kernel_enters_preretained :
    PrimitiveCore.A (inducedSetting preRetained 0 1) ∧
      preRetained.wit = [] := by
  constructor
  · exact assert_transport
      [.admitOcc 0, .admitOcc 1, .assertWit 0 1] 0 1 (by decide)
  · decide

/-- And retention completes from there as its own event. -/
theorem retention_completes :
    (step preRetained (.admitWit 0 1)).wit = [(0, 1)] := by decide

/-- **P2: fidelity is separate.**  Admitting a witness never creates
protection: the protection store is unchanged by witness admission,
at every state. -/
theorem witness_no_protection (s : PState) (i j : Nat) :
    (step s (.admitWit i j)).prot = s.prot := by
  simp only [step]
  repeat' split
  all_goals rfl

/-- P2 countermodel side: a retained, observed-collapsed witness with
no protection is not an obstruction. -/
theorem no_protection_no_obstruction :
    obstP { occ := [0, 1], asserted := [(0, 1)], wit := [(0, 1)],
            prot := [],
            obs := some [], budget := 9, licensed := true,
            refusals := [], halted := false } 0 1 = false := by decide

/-!
**retained witness → faithful presentation is a DECLARATION**:
faithfulness of a presentation is a demand on the presenting map, not
a fact following from retention
(`PrimDiff.const_presentation_unfaithful` is the countermodel:
constant presentations exist and lose every asserted pair).  What
protection buys is the barrier theorem: -/

/-- **P3: the faithful-presentation barrier.**  If a presentation
identifies the two endpoints, then no function of the presented image
alone separates their images — recovery data must come from outside
the quotient (here: from the retained store, which is exactly what
retention is for). -/
theorem quotient_no_recovery {X Q : Type} (q : X → Q) (a b : X)
    (hq : q a = q b) (g : Q → Q → Prop) :
    g (q a) (q b) ↔ g (q a) (q a) := by rw [hq]

/-!
**faithful presentation → declared observation is a DECLARATION** with
its own event (`declareObs`); the zero relation exists only after it
(`obst_requires_observation`).  P4 demands the ZeroRel laws before
any quotient is taken: -/

theorem sepCol_irrefl (c : List Nat) (i : Nat) :
    sepCol c i i = false := by
  unfold sepCol
  cases decide (i ∈ c) <;> rfl

theorem sepCol_symm (c : List Nat) (i j : Nat) :
    sepCol c i j = sepCol c j i := by
  unfold sepCol
  cases decide (i ∈ c) <;> cases decide (j ∈ c) <;> rfl

theorem sepCol_trans (c : List Nat) (i j k : Nat)
    (h1 : sepCol c i j = false) (h2 : sepCol c j k = false) :
    sepCol c i k = false := by
  unfold sepCol at *
  cases hi : decide (i ∈ c) <;> cases hj : decide (j ∈ c)
    <;> cases hk : decide (k ∈ c) <;> simp_all

/-- **P4: ZeroRel is reflexive** on every declared observation. -/
theorem zero_refl (cols : List (List Nat)) (i : Nat) :
    zeroP cols i i = true := by
  induction cols with
  | nil => rfl
  | cons c rest ih =>
      rw [zeroP_cons, sepCol_irrefl, ih]
      rfl

/-- **P4: ZeroRel is symmetric** on every declared observation. -/
theorem zero_symm (cols : List (List Nat)) (i j : Nat) :
    zeroP cols i j = zeroP cols j i := by
  induction cols with
  | nil => rfl
  | cons c rest ih =>
      rw [zeroP_cons, zeroP_cons, sepCol_symm, ih]

/-- **P4: ZeroRel is transitive** on every declared observation:
zero means "agrees on membership in every declared column", which
composes. -/
theorem zero_trans (cols : List (List Nat)) (i j k : Nat)
    (hij : zeroP cols i j = true) (hjk : zeroP cols j k = true) :
    zeroP cols i k = true := by
  induction cols with
  | nil => rfl
  | cons c rest ih =>
      rw [zeroP_cons] at hij hjk ⊢
      simp only [Bool.and_eq_true, Bool.not_eq_true'] at hij hjk
      have h1 := sepCol_trans c i j k hij.1 hjk.1
      rw [h1, ih hij.2 hjk.2]
      rfl

/-! ## The response universe and the two-rule theorem -/

/-- The declared same-level response universe: refine any declared
column by any in-bounds point.  Finite, and complete over the
declared universe by `menu_complete`. -/
def responseMenu (s : PState) : List (List Nat × Nat) :=
  match s.obs with
  | none => []
  | some cols =>
      cols.flatMap fun v =>
        (List.range s.occ.length).map fun p => (v, p)

/-- Same-level repairs of an obstructed pair: accepted moves whose
refined observation separates the pair. -/
def repairFamily (s : PState) (i j : Nat) :
    List (List Nat × Nat) :=
  (responseMenu s).filter fun m =>
    refineOk s m.1 m.2
      && (match s.obs with
          | none => false
          | some cols =>
              sepP (cols.map
                (fun c => if c = m.1 then m.2 :: c else c)) i j)

/-- The menu is complete over the declared universe: every declared
column and every in-bounds point occur. -/
theorem menu_complete (s : PState) (cols : List (List Nat))
    (h : s.obs = some cols) (v : List Nat) (p : Nat)
    (hv : v ∈ cols) (hp : p < s.occ.length) :
    (v, p) ∈ responseMenu s := by
  unfold responseMenu
  rw [h]
  simp only [List.mem_flatMap]
  exact ⟨v, hv, by
    simp only [List.mem_map]
    exact ⟨p, List.mem_range.mpr hp, rfl⟩⟩

/-- Extension proposals for an obstructed pair: new columns from the
declared universe (the singleton columns over admitted positions)
that would separate the pair.  Proposals are records; execution is
separately gated. -/
def extensionProposals (s : PState) (i j : Nat) :
    List (List Nat) :=
  ((List.range s.occ.length).map (fun p => [p])).filter fun c =>
    colOk s c && sepCol c i j

/-- **The extension family is never empty at an obstruction** (with
in-bounds first endpoint): the singleton column on the first endpoint
always qualifies — it is fresh (a declared observation containing it
would have separated the pair), in bounds, and separating. -/
theorem extension_always_available (s : PState) (i j : Nat)
    (hobst : obstP s i j = true) (hij : i ≠ j)
    (hi : i < s.occ.length) (hprot : ((i, j) ∈ s.prot)) :
    [i] ∈ extensionProposals s i j := by
  have hsep : sepCol [i] i j = true := by
    unfold sepCol
    rw [decide_eq_true (List.mem_singleton.mpr rfl),
        decide_eq_false (by
          intro hmem
          exact hij (List.mem_singleton.mp hmem).symm)]
    rfl
  cases hcols : s.obs with
  | none =>
      rw [obst_requires_observation s i j hcols] at hobst
      cases hobst
  | some cols =>
      rw [obst_agrees_when_declared s cols hcols i j] at hobst
      simp only [Bool.and_eq_true, decide_eq_true_eq] at hobst
      obtain ⟨⟨hwit, hpr⟩, hzero⟩ := hobst
      have hsepfalse : sepP cols i j = false := by
        cases hv : sepP cols i j with
        | false => rfl
        | true =>
            unfold zeroP at hzero
            rw [hv] at hzero
            exact Bool.noConfusion hzero
      have hfresh : ¬ (([i] : List Nat) ∈ cols) := by
        intro hmem
        have : sepP cols i j = true := by
          unfold sepP
          exact List.any_eq_true.mpr ⟨[i], hmem, hsep⟩
        rw [this] at hsepfalse
        exact Bool.noConfusion hsepfalse
      have hobstij : obstP s i j = true := by
        rw [obst_agrees_when_declared s cols hcols i j,
            decide_eq_true hwit, decide_eq_true hpr, hzero]
        rfl
      have hcolok : colOk s [i] = true := by
        unfold colOk
        rw [hcols]
        show (([i] : List Nat).all
            (fun p => decide (p < s.occ.length))
          && !(decide (([i] : List Nat) ∈ cols))
          && s.prot.any
              (fun r => obstP s r.1 r.2 && sepCol [i] r.1 r.2))
          = true
        have h1 : (([i] : List Nat).all
            (fun p => decide (p < s.occ.length))) = true := by
          simp only [List.all_cons, List.all_nil, Bool.and_true]
          exact decide_eq_true hi
        have h3 : (s.prot.any
            (fun r => obstP s r.1 r.2 && sepCol [i] r.1 r.2))
            = true := by
          apply List.any_eq_true.mpr
          refine ⟨(i, j), hprot, ?_⟩
          show (obstP s i j && sepCol [i] i j) = true
          rw [hobstij, hsep]
          rfl
        rw [h1, decide_eq_false hfresh, h3]
        rfl
      unfold extensionProposals
      apply List.mem_filter.mpr
      constructor
      · simp only [List.mem_map]
        exact ⟨i, List.mem_range.mpr hi, rfl⟩
      · rw [hcolok, hsep]
        rfl

/-- **P7, the two-rule theorem.**  At an active obstruction with an
in-bounds protected pair, the response universe never runs dry:
either the same-level repair family is nonempty, or same-level
exhaustion is certified (the family is the exhaustive filter of the
complete menu, `menu_complete`) and the extension-proposal family is
nonempty.  The obstruction is forced to a response: remove it
at the same level, or create structure.  Refusal and the terminal
are separately typed records, not members of either family. -/
theorem two_rule (s : PState) (i j : Nat)
    (hobst : obstP s i j = true) (hij : i ≠ j)
    (hi : i < s.occ.length) (hprot : (i, j) ∈ s.prot) :
    repairFamily s i j ≠ [] ∨
      (repairFamily s i j = [] ∧ extensionProposals s i j ≠ []) := by
  cases hrep : repairFamily s i j with
  | cons m rest => exact Or.inl (by simp)
  | nil =>
      refine Or.inr ⟨rfl, ?_⟩
      intro hempty
      have := extension_always_available s i j hobst hij hi hprot
      rw [hempty] at this
      cases this

/-- Proposal is not execution: an unlicensed live state accepts no
column creation, whatever the proposal family contains. -/
theorem proposal_not_execution (s : PState) (c : List Nat)
    (h : s.licensed = false) (hh : s.halted = false) :
    step s (.addCol c) = s := by
  have hg : ¬ ((colOk s c && s.licensed
      && decide (0 < s.budget)) = true) := by
    intro hc
    simp only [Bool.and_eq_true] at hc
    rw [h] at hc
    exact Bool.noConfusion hc.1.2
  simp only [step, hh]
  rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
      if_neg hg]

/-- Budget gates execution the same way. -/
theorem budget_gates_execution (s : PState) (c : List Nat)
    (h : s.budget = 0) (hh : s.halted = false) :
    step s (.addCol c) = s := by
  have hg : ¬ ((colOk s c && s.licensed
      && decide (0 < s.budget)) = true) := by
    intro hc
    simp only [Bool.and_eq_true] at hc
    rw [h] at hc
    have := hc.2
    simp at this
  simp only [step, hh]
  rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
      if_neg hg]

/-! ## Refusal record and absorbing terminal, separately typed -/

/-- Refusal touches no obstruction-relevant field: it is a record,
not an action. -/
theorem refusal_object_inert (s : PState) (i j : Nat) :
    ((step s (.refuse i j)).occ = s.occ) ∧
    ((step s (.refuse i j)).wit = s.wit) ∧
    ((step s (.refuse i j)).prot = s.prot) ∧
    ((step s (.refuse i j)).obs = s.obs) ∧
    ((step s (.refuse i j)).budget = s.budget) := by
  simp only [step]
  repeat' split
  all_goals exact ⟨rfl, rfl, rfl, rfl, rfl⟩

/-- Refusal does not absorb: the halted flag is untouched. -/
theorem refusal_not_terminal (s : PState) (i j : Nat) :
    (step s (.refuse i j)).halted = s.halted := by
  simp only [step]
  repeat' split
  all_goals rfl

/-- On a halted state every event is inert. -/
theorem step_halted (t : PState) (e : PEvent)
    (h : t.halted = true) : step t e = t := by
  cases t with
  | mk occ wit prot obs budget licensed refusals halted =>
      subst h
      cases e <;> rfl

/-- The terminal is absorbing: after `halt`, every event is inert. -/
theorem terminal_absorbing (s : PState) (e : PEvent) :
    step (step s .halt) e = step s .halt :=
  step_halted _ _ rfl

/-! ## P8: the operational no-outside schema -/

/-- Same represented state, same event, same successor: the step is
a function of represented data alone (the operational no-outside
form; the absolute form quantifies over unrepresented differences
and is not formulable here — not claimed). -/
theorem no_outside_operational (s t : PState) (e : PEvent)
    (h : s = t) : step s e = step t e := by rw [h]

/-- Replay determinism from genesis: the passage state is a function
of its represented history alone. -/
theorem replay_deterministic (h1 h2 : List PEvent) (heq : h1 = h2) :
    replayP h1 genesisP = replayP h2 genesisP := by rw [heq]

/-- Replay composes: history is append-transparent. -/
theorem replay_append (h1 h2 : List PEvent) (s : PState) :
    replayP (h1 ++ h2) s = replayP h2 (replayP h1 s) := by
  simp [replayP, List.foldl_append]

/-! ## Re-evaluation: the executed response resolves the obstruction -/

/-- Executing an accepted extension column that separates the pair
kills the obstruction: remeasurement after structure creation
returns non-obstructed.  (The witnessing column enters the declared
observation, so the zero relation no longer holds on the pair.) -/
theorem extension_resolves (s : PState) (c : List Nat) (i j : Nat)
    (cols : List (List Nat)) (hcols : s.obs = some cols)
    (hok : colOk s c = true) (hsep : sepCol c i j = true)
    (hlic : s.licensed = true) (hbud : 0 < s.budget)
    (hh : s.halted = false) :
    obstP (step s (.addCol c)) i j = false := by
  have hguard : (colOk s c && s.licensed
      && decide (0 < s.budget)) = true := by
    rw [hok, hlic, decide_eq_true hbud]
    rfl
  have hstep : step s (.addCol c) =
      { s with obs := some (cols ++ [c]),
               budget := s.budget - 1 } := by
    simp only [step, hh]
    rw [if_neg (fun hc : false = true => Bool.noConfusion hc),
        if_pos hguard, hcols]
  rw [hstep]
  rw [obst_agrees_when_declared _ (cols ++ [c]) rfl i j]
  have hnew : zeroP (cols ++ [c]) i j = false := by
    unfold zeroP sepP
    have : ((cols ++ [c]).any fun d => sepCol d i j) = true :=
      List.any_eq_true.mpr ⟨c, by simp, hsep⟩
    rw [this]
    rfl
  rw [hnew]
  simp

/-! ## Represented next family: the policy-driven closure family

The passage's last arrow: the next-event family is computed from the
represented state by a fixed interpreter — repair blocks for every
same-level repair of every obstructed protected pair, extension
blocks (funded and executed as separate events) for every proposal.
The generator's silence on quiescent states is a represented verdict
(`nextFamilyP_stop`); at an obstruction the family is provably
nonempty (`nextFamilyP_nonempty`).  The iteration of this family by
a driver remains metatheoretic, exactly as in the sealed
constitution — stated, not laundered. -/

def obstructedPairs (s : PState) : List (Nat × Nat) :=
  s.prot.filter (fun r => obstP s r.1 r.2)

def nextFamilyP (s : PState) : List (List PEvent) :=
  (obstructedPairs s).flatMap fun r =>
    (repairFamily s r.1 r.2).map
        (fun m => [PEvent.refineCol m.1 m.2])
      ++ (extensionProposals s r.1 r.2).map
          (fun c => [PEvent.setBudget 1, PEvent.addCol c])

/-- The stop outcome is represented: with no obstructed protected
pair the family is empty — silence is a verdict, not an exception. -/
theorem nextFamilyP_stop (s : PState)
    (hq : ∀ r ∈ s.prot, obstP s r.1 r.2 = false) :
    nextFamilyP s = [] := by
  unfold nextFamilyP obstructedPairs
  have hgen : ∀ (l : List (Nat × Nat)),
      (∀ r ∈ l, obstP s r.1 r.2 = false) →
        l.filter (fun r => obstP s r.1 r.2) = [] := by
    intro l hl
    induction l with
    | nil => rfl
    | cons r rest ih =>
        rw [List.filter_cons, hl r List.mem_cons_self,
          if_neg (fun hc : false = true => Bool.noConfusion hc)]
        exact ih (fun x hx => hl x (List.mem_cons_of_mem r hx))
  rw [hgen s.prot hq]
  rfl

/-- At an active obstruction the family is provably nonempty: the
always-available extension proposal contributes its funded block. -/
theorem nextFamilyP_nonempty (s : PState) (i j : Nat)
    (hobst : obstP s i j = true) (hij : i ≠ j)
    (hi : i < s.occ.length) (hprot : (i, j) ∈ s.prot) :
    [PEvent.setBudget 1, PEvent.addCol [i]] ∈ nextFamilyP s := by
  unfold nextFamilyP obstructedPairs
  apply List.mem_flatMap.mpr
  refine ⟨(i, j), ?_, ?_⟩
  · apply List.mem_filter.mpr
    exact ⟨hprot, hobst⟩
  · apply List.mem_append.mpr
    right
    apply List.mem_map.mpr
    exact ⟨[i],
      extension_always_available s i j hobst hij hi hprot, rfl⟩

/-- Completeness, repair side: every accepted separating same-level
move on an obstructed protected pair appears in the family as its
own block. -/
theorem nextFamilyP_complete_repair (s : PState) (i j : Nat)
    (m : List Nat × Nat) (hobst : obstP s i j = true)
    (hprot : (i, j) ∈ s.prot) (hm : m ∈ repairFamily s i j) :
    [PEvent.refineCol m.1 m.2] ∈ nextFamilyP s := by
  unfold nextFamilyP obstructedPairs
  apply List.mem_flatMap.mpr
  refine ⟨(i, j), List.mem_filter.mpr ⟨hprot, hobst⟩, ?_⟩
  apply List.mem_append.mpr
  left
  exact List.mem_map.mpr ⟨m, hm, rfl⟩

/-- Completeness, extension side: every proposal on an obstructed
protected pair appears as its own funded block. -/
theorem nextFamilyP_complete_ext (s : PState) (i j : Nat)
    (c : List Nat) (hobst : obstP s i j = true)
    (hprot : (i, j) ∈ s.prot)
    (hc : c ∈ extensionProposals s i j) :
    [PEvent.setBudget 1, PEvent.addCol c] ∈ nextFamilyP s := by
  unfold nextFamilyP obstructedPairs
  apply List.mem_flatMap.mpr
  refine ⟨(i, j), List.mem_filter.mpr ⟨hprot, hobst⟩, ?_⟩
  apply List.mem_append.mpr
  right
  exact List.mem_map.mpr ⟨c, hc, rfl⟩

end PrimitivePassage
