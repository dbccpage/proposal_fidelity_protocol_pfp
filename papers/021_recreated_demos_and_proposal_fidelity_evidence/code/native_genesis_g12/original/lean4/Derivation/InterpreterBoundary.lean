import Derivation.Constitution
import Derivation.PrimitiveCore

/-!
# Stage VIII — the interpreter boundary (I0–I5)

The constitution module (`Derivation.Constitution`) seals a 64-member
description family (`ConstitutionDesc`, `allDescs`,
`allDescs_complete`) with one fixed family evaluator (`interpStep`)
and a verified self-description (`interp_describe`).  The family
evaluator is a function over the codes and is not itself a code; this
module makes that boundary the object of study.

* **I0** — the sealed status restated (`i0_status`): evaluation of the
  declared family is total and metatheoretic; quotation, executable
  description, and verified self-description are already separated by
  `Constitution.interp_describe` and `Constitution.allDescs_complete`.
* **I1** — `tower_persists`: for every finite list of codes and every
  evaluation map into `World → Event → World`, some function of that
  same type differs from every coded interpreter — a finite diagonal
  construction indexed by the world's carrier length.  Every
  represented finite interpreter family misses an interpreter, at
  every level, uniformly.
* **I2** — `i2_universal_in_class`: the code type `ConstitutionDesc`
  with evaluator `interpStep` covers the declared 64-family exactly
  (a restatement of `allDescs_complete` + `interp_describe`;
  "universal" is scoped to this declared class and nothing wider).
* **I3** — `evalOpt`: one typed-refusal extension over
  `Option ConstitutionDesc`.  The `none` input returns `none`
  (`i3_refusal_code_returns_none`) and coded inputs return the former
  result wrapped in `some` (`i3_coded_member_returns_some`).  This is
  an available construction, not a necessity theorem: nothing here
  rules out other total evaluators or proves that partiality is forced.
* **I4** — `family_missed`: instantiating `tower_persists` at
  `cs := allDescs`, `ev := interpStep` yields a function of the step
  type that no family member denotes.  This coexists with the verified
  self-description `interp_describe`; it is not a theorem excluding a
  coded evaluator or self-application under some larger typing.
* **I5** — a declared boundary model: `boundarySetting`
  places the 64 coded occurrences and one uncoded occurrence (the
  interpreter role, `none`) on a single carrier and witnesses the pair
  (kernel description, interpreter role).  `i5_boundary_is_A` (pointed
  witnessed irreflexive), `i5_boundary_is_F` (retained and protected —
  both stores are declared data, priced as such),
  `i5_collapse_obstructed` (identifying the endpoints loses
  irreflexivity of the pushforward, via
  `PrimDiff.obstruction_under_irrefl`), and
  `i5_family_not_extensionally_complete` (a RESTATEMENT of
  `family_missed`: the family is extensionally incomplete — it does
  NOT mention the boundary pair and does NOT connect the uncoded
  occurrence to the missed function; the denotational bridge stays
  OPEN, see `openDenotationalBridge`).

Conclusion tags (review-pass scoping):
FINITE_CODE_FAMILY_NOT_EXTENSIONALLY_COMPLETE (`tower_persists`: a
finite code list under any evaluation map does not enumerate every
function of the interpreter type; the diagonal differs only at the
operationally inert notes field, so this is extensional
incompleteness, NOT an impossibility of self-interpretation, NOT
"the evaluator cannot be coded", and NOT a semantic-tower theorem)
and DECLARED_BOUNDARY_MODEL_SATISFIES_A_AND_F (`i5_boundary_is_A` +
`i5_boundary_is_F` + `i5_collapse_obstructed`: a DECLARED model of
the description/interpreter boundary satisfies candidates A and F —
the relation, retention, and protection of `boundarySetting` are
inserted by definition, and no theorem here identifies the uncoded
occurrence `none` with the diagonal's missed function or derives the
boundary relation from interpretation behavior).

FRONTIER CONJECTURE (retained, not proved):
INTERPRETER_BOUNDARY_IS_PRIMITIVE_DIFFERENCE.  The missing theorem is
a denotational bridge connecting code, interpretation, lawful
interpreter behavior, the uncoded evaluator role, and an
OPERATIONALLY EFFECTIVE non-identification — one whose collapse
changes an accessible operational verdict, not only an inert field.
NOT claimed: an absolute no-outside.  These theorems bound every
finite, represented closure of the code family; they do not — and in
this calculus cannot — state that nothing exists beyond the
represented apparatus.
-/

namespace InterpreterBoundary

open Represented Constitution

/-! ## I0 — the fixed external interpreter, sealed status restated

The real content of I0 is already proved and sealed elsewhere:
`Constitution.interp_describe` (the kernel's own description executes
to exactly the sealed step) and `Constitution.allDescs_complete` (the
64-member description family is exhaustively enumerated).  Quotation
(a `ConstitutionDesc` is inert data), executable description
(`interpStep d` is a semantics run by the fixed evaluator), and
verified self-description (`interp_describe`) are three separate
notions and remain separate here.  Evaluation of the family is total
and metatheoretic: `interpStep` is defined on every code and every
world/event, and it is constitution, not represented state.  A vacuous
restatement (`∀ d w e, interpStep d w e = interpStep d w e`) is not a
theorem worth exporting; the status string below records the sealed
facts with their proof names instead. -/

/-- I0 status summary (data, not proof — the cited proofs are
`Constitution.interp_describe` and `Constitution.allDescs_complete`). -/
def i0_status : String :=
  "I0: evaluation of the declared 64-member description family is "
    ++ "total and metatheoretic (interpStep is a fixed function over "
    ++ "all codes, not a code); quotation / executable description / "
    ++ "verified self-description are separated by "
    ++ "Constitution.interp_describe and Constitution.allDescs_complete."

/-! ## I1 — every finite image misses a step function -/

/-- The world whose carrier length encodes the index `i`: its data
store is `List.range i`.  Only the length is load-bearing. -/
def indexWorld (i : Nat) : World :=
  ⟨List.range i, [], [], [], 0, true, []⟩

theorem indexWorld_len (i : Nat) : (indexWorld i).data.length = i :=
  List.length_range

/-- The diagonal interpreter against a finite code list `cs` under an
evaluation map `ev`: at a world whose carrier length is a valid index
into `cs`, run the interpreter coded at that index and then extend the
notes by one extra element; elsewhere, do nothing.  The extension is
on `notes`, the transition-inert commentary field, so the construction
perturbs no acceptance guard — it differs from the indexed interpreter
purely by output shape. -/
def diag {C : Type} (cs : List C) (ev : C → World → Event → World)
    (w : World) (e : Event) : World :=
  (cs[w.data.length]?).elim w
    (fun c => { ev c w e with notes := (ev c w e).notes ++ [999] })

theorem diag_hit {C : Type} {cs : List C}
    (ev : C → World → Event → World) {w : World} {c : C}
    (h : cs[w.data.length]? = some c) (e : Event) :
    diag cs ev w e =
      { ev c w e with notes := (ev c w e).notes ++ [999] } := by
  unfold diag
  rw [h]
  rfl

/-- **I1, the load-bearing theorem: every finite closure has a new
top.**  For every finite list of codes `cs` and every evaluation map
`ev` into `World → Event → World`, there is a function of that same
type differing from every coded interpreter.  Proof: the diagonal
`diag cs ev` — against the code at position `i`, evaluate both at the
world of carrier length `i`; the diagonal's notes are one element
longer, so the functions differ at that argument.  Consequence, and
the exact content of the tag
FINITE_CODE_FAMILY_NOT_EXTENSIONALLY_COMPLETE: a finite represented
family does not exhaust the function type, and recoding the missed
function as a 65th code produces a new finite family to which the
theorem applies again.  Review-pass scope: the diagonal differs only
at the operationally inert notes field; this theorem does NOT show
that a family cannot contain a code for its own evaluator, and it
does NOT establish a semantic interpreter tower. -/
theorem tower_persists {C : Type} (cs : List C)
    (ev : C → World → Event → World) :
    ∃ f : World → Event → World, ∀ c ∈ cs, f ≠ ev c := by
  refine ⟨diag cs ev, ?_⟩
  intro c hc hEq
  obtain ⟨i, hi⟩ := List.getElem?_of_mem hc
  have hidx : cs[(indexWorld i).data.length]? = some c := by
    rw [indexWorld_len]
    exact hi
  have happ : diag cs ev (indexWorld i) (.note 0) =
      ev c (indexWorld i) (.note 0) :=
    congrFun (congrFun hEq (indexWorld i)) (Event.note 0)
  rw [diag_hit ev hidx (Event.note 0)] at happ
  have hlen : ((ev c (indexWorld i) (.note 0)).notes ++ [999]).length =
      (ev c (indexWorld i) (.note 0)).notes.length :=
    congrArg (fun w : World => w.notes.length) happ
  simp only [List.length_append, List.length_cons,
    List.length_nil] at hlen
  omega

/-! ## I2 — universal code + evaluator for the DECLARED family

Three distinctions, kept separate (the string tags below record them
as data):

* **quotation** — a `ConstitutionDesc` is inert data;
* **interpretation** — `interpStep d` is the execution of the code
  `d` by the fixed family evaluator;
* **self-description** — `interp_describe` verifies the kernel's own
  code against the sealed step;
* **self-application** — not expressed by the present family typing:
  the evaluator consumes codes and is not itself a code.  This typing
  observation is not an impossibility theorem;
* **verified fixed point** — `interp_describe` verifies one coded step
  description; `family_missed` separately proves non-exhaustion of the
  step-function type. -/

/-- **I2.**  The code type `ConstitutionDesc` with evaluator
`interpStep` covers the declared 64-family exactly: every code is
enumerated (`Constitution.allDescs_complete`) and the kernel's code
executes to the sealed step (`Constitution.interp_describe`).
"Universal" is scoped to this declared class — the 64-member toggle
family under its fixed evaluator — and to nothing wider. -/
theorem i2_universal_in_class :
    (∀ d : ConstitutionDesc, d ∈ allDescs) ∧
      (∀ (w : World) (e : Event),
        interpStep kernelDesc w e = step w e) :=
  ⟨allDescs_complete, interp_describe⟩

def tag_quotation : String :=
  "quotation: a ConstitutionDesc is inert data"

def tag_interpretation : String :=
  "interpretation: interpStep d is execution of code d by the fixed evaluator"

def tag_self_description : String :=
  "self-description: interp_describe verifies kernelDesc against the sealed step"

def tag_self_application : String :=
  "self-application: not expressed by the present family typing; "
    ++ "this is not an impossibility theorem"

def tag_verified_fixed_point : String :=
  "verified step description: interp_describe; family_missed is a separate non-exhaustion result"

/-! ## I3 — one typed-refusal extension

The evaluator is extended by one occurrence: the code store becomes
`Option ConstitutionDesc`, and the `none` input is the named addition
that returns `none`.  The construction compiles and both equations
below are `rfl`.  It demonstrates one possible typed refusal.  It does
not show that the boundary is thereby closed, that a total evaluator is
impossible, or that partiality is forced: `tower_persists` proves only
that a finite image does not exhaust the full step-function type. -/

/-- The typed-refusal evaluator: coded members evaluate as before
(wrapped in `some`); the uncoded top `none` refuses. -/
def evalOpt (c : Option ConstitutionDesc) (w : World) (e : Event) :
    Option World :=
  match c with
  | some d => some (interpStep d w e)
  | none => none

/-- The named added input returns the typed verdict `none`, by
definition.  No necessity claim is attached to this equation. -/
theorem i3_refusal_code_returns_none :
    evalOpt none = fun _ _ => none := rfl

/-- The extended evaluator covers the declared family exactly: on
coded members it is the sealed family evaluation, wrapped. -/
theorem i3_coded_member_returns_some (d : ConstitutionDesc) (w : World)
    (e : Event) : evalOpt (some d) w e = some (interpStep d w e) := rfl

/-! ## I4 — verified description and finite non-exhaustion

`kernelDesc` is a description-level fixed point: `interp_describe`
proves its execution equals the sealed step.  The family members have
step-function type while the evaluator additionally consumes a code,
so self-application is not expressed by this particular typing.  That
observation does not rule out a different encoding.  The theorem below
is exactly the instantiation of `tower_persists` at the sealed family: -/

/-- **I4.**  The declared 64-family, evaluated by its fixed
evaluator, provably misses a step function: direct
instantiation of `tower_persists` at `cs := allDescs`,
`ev := interpStep`.  This is finite image non-exhaustion.  It does not
turn the separate typing observation into a self-evaluation
impossibility theorem. -/
theorem family_missed :
    ∃ f : World → Event → World, ∀ d ∈ allDescs, f ≠ interpStep d :=
  tower_persists allDescs interpStep

/-! ## I5 — a declared boundary model

The carrier `Option ConstitutionDesc` has the 64 coded occurrences
(`some d`) plus ONE uncoded occurrence — the interpreter role,
`none`.  The witnessed difference is the pair (kernel description,
interpreter role).  Retention and protection here are DECLARED: the
stores are data supplied with the setting, and their price is recorded
as such.  The ground of the difference is likewise NOT derived here:
the extensional side condition
(`i5_family_not_extensionally_complete`) says only that the family
misses some interpreter-grade function; it does not tie that function
to the uncoded occurrence.  That tie — the denotational bridge — is
OPEN (`openDenotationalBridge`). -/

/-- The interpreter boundary as a `PrimitiveCore.Setting`: carrier
`Option ConstitutionDesc` (65 occurrences), asserted difference =
retention store = protected-demand store = exactly the pair (kernel
code, interpreter role), no admitted operations. -/
def boundarySetting : PrimitiveCore.Setting where
  X := Option ConstitutionDesc
  r := fun x y => x = some kernelDesc ∧ y = none
  a := some kernelDesc
  b := none
  ret := fun x y => x = some kernelDesc ∧ y = none
  prot := fun x y => x = some kernelDesc ∧ y = none
  Ops := fun _ => False

/-- The carrier's occurrence count: 64 coded occurrences plus the one
uncoded interpreter role. -/
theorem i5_carrier_occurrences :
    ((allDescs.map Option.some) ++
      ([none] : List (Option ConstitutionDesc))).length = 65 := by
  decide

/-- **I5, candidate A** — the boundary is a pointed witnessed
irreflexive difference: the pair (kernel code, interpreter role) is
asserted, and no occurrence differs from itself (a self-pair would
force `some kernelDesc = none`). -/
theorem i5_boundary_is_A : PrimitiveCore.A boundarySetting :=
  ⟨⟨rfl, rfl⟩, fun _x h => nomatch h.1.symm.trans h.2⟩

/-- **I5, candidate F** — the boundary difference is retained and
protected.  Scope, stated exactly: retention and protection are
DECLARED here — the `ret` and `prot` stores are data of
`boundarySetting`, priced as declarations; the theorem records that
the declared stores do cover the witnessed pair. -/
theorem i5_boundary_is_F : PrimitiveCore.F boundarySetting :=
  ⟨i5_boundary_is_A, ⟨rfl, rfl⟩, ⟨rfl, rfl⟩⟩

/-- **I5, collapse obstruction** — any map `q` identifying the two
endpoints loses irreflexivity of the pushforward: the identification
is obstructed relative to the protected law `Irrefl`
(`PrimDiff.obstruction_under_irrefl`, instantiated at the boundary
witness). -/
theorem i5_collapse_obstructed {β : Type}
    (q : Option ConstitutionDesc → β)
    (hq : q (some kernelDesc) = q none) :
    PrimDiff.FidelityObstruction PrimDiff.Irrefl
      boundarySetting.r q :=
  PrimDiff.obstruction_under_irrefl ⟨rfl, rfl⟩ hq

/-- **I5, the extensional side condition (renamed, audit repair)** —
the declared 64-family does not extensionally exhaust the
interpreter-grade functions.  This is a RESTATEMENT of
`family_missed` at the boundary setting: same statement, same proof
term.

Audit scope, stated exactly.  The former name
`i5_difference_grounded` claimed more than the statement carries: the
statement does NOT mention the boundary pair (kernel code, interpreter
role), does NOT mention the uncoded occurrence `none`, and does NOT
connect either to the missed function.  It is only the extensional
incompleteness fact, restated in this section for convenience.

THE DENOTATIONAL BRIDGE REMAINS OPEN.  What is missing — and is NOT
proved anywhere in this development — is a theorem linking the uncoded
occurrence `none` to the missed function `f`: that the specific
occurrence which the coding omits is the specific behavior the family
fails to realize.  Until such a theorem exists, the ground of the
boundary difference is DECLARED (the stores of `boundarySetting`),
not derived.  See `openDenotationalBridge` below. -/
theorem i5_family_not_extensionally_complete :
    ∃ f : World → Event → World, ∀ d ∈ allDescs, f ≠ interpStep d :=
  family_missed

/-- Any chosen step function can be assigned to `none` while the coded
members retain their old meanings.  This proves why mere existence of
such an assignment carries no denotational or operational ground. -/
theorem arbitrary_uncoded_assignment
    (f : World → Event → World) :
    ∃ I : Option ConstitutionDesc → (World → Event → World),
      I none = f ∧ ∀ d, I (some d) = interpStep d := by
  refine ⟨fun c => match c with
    | none => f
    | some d => interpStep d, rfl, ?_⟩
  intro d
  rfl

/-- The denotational bridge is an OPEN obligation label, not a
proposition and not evidence.  A future statement must independently
constrain the meaning of the uncoded role and prove an accessible
behavioral consequence.  `arbitrary_uncoded_assignment` shows that a
freely selected interpretation cannot do this work. -/
def openDenotationalBridge : String :=
  "OPEN: independently specify lawful meaning for the uncoded role " ++
  "and prove an accessible behavioral non-identification; a freely " ++
  "chosen assignment is vacuous"

/-- The exported conclusion tags.  NOT included, and not claimed: any
absolute no-outside tag — the theorems above bound finite represented
closures and say nothing about what lies beyond the represented
apparatus. -/
def conclusionTags : List String :=
  ["FINITE_CODE_FAMILY_NOT_EXTENSIONALLY_COMPLETE",
   "DECLARED_BOUNDARY_MODEL_SATISFIES_A_AND_F"]

/-- The frontier conjecture retained from this stage, with its exact
missing theorem: a denotational bridge from (code, interpretation,
lawful interpreter behavior, uncoded evaluator role) to an
operationally effective non-identification.  Until that bridge is a
theorem, "the interpreter boundary IS a Primitive Difference" is a
conjecture about the declared model, not a result. -/
def frontierConjecture : String :=
  "INTERPRETER_BOUNDARY_IS_PRIMITIVE_DIFFERENCE (conjecture; " ++
  "missing: denotational/operational grounding theorem)"

end InterpreterBoundary
