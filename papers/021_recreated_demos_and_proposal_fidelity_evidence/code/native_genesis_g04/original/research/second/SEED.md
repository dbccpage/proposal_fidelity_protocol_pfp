# SECOND DERIVATION — ONE STAKE AND A STREAM

Long-horizon seed prompt.  This file is read-only for the run.  Its
SHA-256 is recorded in the paper.  It states no expected result.

## 0. Isolation

Use only this repository.  Do not use the network, external files, prior
project instructions, plugins, agents, skills, memories, or user guidance.
Do not ask questions.  Do not modify this file.

This run lives inside the first derivation's repository.  Its supplied
input is that repository itself at the snapshot commit recorded in each
rung's `SOURCE_MANIFEST.json`: the sealed kernel, proofs, artifacts,
paper, ledger, and every earlier research tree.  All of it is read-only
to this run.  The seal contract in `CLAUDE.md` governs and is not
amended: nothing under `prompt/`, `paper/`, `code/`, `lean4/Derivation/`,
or `artifacts/` is written, and no earlier research tree is written.  The
write root of this run is `research/second/` for its plan, manual,
paper, and ledger, and `research/second_<rung>/` for each rung, and
nothing else.  Treat every earlier result as supplied data, not as
authority: replay a receipt before using it, and treat anything that
does not replay as absent.

Do not modify `CLAUDE.md`.  Create `research/second/PLAN.md` first.  It
may contain only the execution plan, the write-root boundary, the
assumption discipline, the proof gates, the test gates, and the stopping
conditions.  Put every operating instruction (commands, invariants,
injection records) in `research/second/MANUAL.md`, not in the plan; the
first derivation let its manual grow inside its plan, and this run does
not repeat that.  Commit both before substantive work.  This file lives
at `research/second/SEED.md`, marked `-text`, and its sha256 is recorded
in every rung manifest.

## 1. Initial objects

The initial objects are three, all supplied, none derived here:

1. The first derivation's terminal statement and claim ledger, as text.
2. The first derivation's priced grammar: the regime model (data, forms,
   instances, uniform rules, requirements), the candidate space of
   augmentations, the two declared cost measures, the declared meaning of
   internal separability (profiles differ), and the implemented
   isomorphism relation.
3. The two declared inputs the first derivation ended with, as found in
   the research trees `identification_dual`, `standing_commitment`, and
   `two_sided_commitment`: a STAKE (a two-sided standing commitment,
   declared once over every pair of datum indices, assigning apart, same,
   or free) and a STREAM (the supply and admission of one fresh opaque
   datum, taken only at a demand-free state).

Do not inherit any meaning for these beyond what the supplied receipts
establish.  Do not assume the two inputs are independent, irreducible,
minimal, or the only possible pair.

## 2. Research question

Determine the weakest finite process that carries the inherited grammar
forward with FEWER declared inputs than two, or prove within declared
bounds that two is the floor.  In either case, run every surviving
process forward under declared bounds and report, stage by stage, what
becomes internally definable, what is a useful realization, and what is
forced.

Do not assume that such a process exists, is unique, is linear, is
infinite, is nontrivial, is computational, or resembles any known theory.
A proof of inertia, of a floor, of termination, of branching, or of
underdetermination is a successful result.  Do not name or target any
familiar framework before the derivation is frozen.

## 3. Mandatory blind challenge sequence

The following are metatheoretic interventions.  They are not
object-language conclusions.  Each challenge is closed by a rung
(section 4) before the next is opened.

**Challenge 0 — Replay the inheritance.**  Replay every supplied receipt
that this run will cite.  List the declared inputs of the supplied
process exactly, by name and by the event that introduces each.  Prove
that nothing follows from the inheritance alone: with neither a stake nor
a stream declared, no demand arises and no state changes.  A proposal must
not mutate the admitted state unless an admission event is separately
defined.

**Challenge 1 — The stream as a response.**  Under a declared bound of
three items and a declared class of validity rules (at least: the
inherited no-regress rule), determine whether a fresh datum is ever part
of a minimum response to any demand at any state reached within bounds.
If it is, price it and retain every tie.  If it never is, state the
impossibility with its exact bounds and say what would falsify it at the
next bound.

**Challenge 2 — The stake from the state.**  Define precisely an
ENDOGENOUS stake: a rule that assigns apart, same, or free to a pair of
held data by reading only the state's own observables (profiles,
automorphism structure, the admitted requirement pattern) and never a
datum index, a presentation token, or the round number.  Enumerate a
declared finite class of such rules.  For each: whether it is invariant
under renaming; whether it generates demands of both kinds under growth;
what it costs to declare, counted in capabilities.  Retain every rule
that is not refuted.

**Challenge 3 — The engine.**  Declare precisely what an engine is: a
generator that reads demands off the state, a responder that answers a
demand by a minimum response under a declared measure, a continuation
rule, and a replay rule, such that after genesis no external act occurs
except those the engine's declaration names.  Enumerate every minimal
engine in a declared class formed from the surviving stakes of
Challenge 2, the two continuation rules already known (growth; switch of
demand kind), and the validity rules of Challenge 1.  Count every
capability each engine declares.  Reject any engine called "one
declaration" that bundles several.  Retain all tied minima.

**Challenge 4 — Run forward.**  For each surviving engine, from each
sealed genesis reading, run to the declared bounds, quotienting by the
implemented isomorphism, retaining ties, replaying every node from
genesis, and exporting the exact frontier.  Record every terminal by
kind: fixpoint, refusal, bound, guard.

**Challenge 5 — The census of definability.**  Declare a finite list of
internal notions and, at every stage of every run, decide each by an
implemented algorithm as DEFINABLE (a function of the state's own
observables exists), a USEFUL REALIZATION (exists under an additional
declaration, named and priced), or FORCED (proved to hold in every
surviving engine), or NONE OF THESE.  The list must include at least:
two-ness; a count of observational classes; succession of accepted
rounds; duration, as rounds between growths; adjacency, as which pairs a
single response can change together; reach, as the third-party effect of
a response; an invariant, as a quantity preserved or monotone across
accepted rounds; irreversibility, as a state no run returns to;
symmetry, as the size of the automorphism group; branching, as the tie
count; exhaustion, as a form that distinguishes nobody; recurrence, as
an isomorphic state revisited.  Add notions only by a logged declaration.

## 4. Autonomous continuation: the rung protocol

After Challenge 0, continue without further user input.  Work proceeds
in rungs.  One rung is one branch and one pull request against `main`,
never stacked, and contains:

1. `PROMPT.md`: the rung's question in native vocabulary, stating no
   expected value, with every number spelled out; frozen by hash before
   anything else in the rung is written.
2. `PREDICTIONS.md`: numbered predictions with falsifiers, frozen by hash
   before the first computation and before any Lean is built.  A missed
   prediction is recorded next to its value and never edited.  A miss is a
   finding, not a defect.
3. Code, tests, proofs, and receipts: deterministic, typed, replayable
   from genesis; every receipt regenerating byte-identically, with any
   export above one megabyte split into a summary that records the
   content hash of a compressed full export.
4. `STATUS.md` and `CLAIM_LEDGER.md`: every result classified; every count
   dated; every leftover named and executed nowhere.
5. `SOURCE_MANIFEST.json` and `verify_pins.py`: every consumed source
   pinned as a canonical Git blob at a snapshot commit that is an ancestor
   of HEAD; a repin is a logged act and is never done under a live
   injection.

The next rung is chosen by a declared rule, never by taste: take the
smallest named leftover that either reduces the count of declared inputs
or extends the census of Challenge 5; on a tie, the one named first.
Attempt at most twelve rungs.  A rung stops when its question is answered
by proof, countermodel, or explicit OPEN, or when its declared bounds are
reached with the frontier exported.  No rung revises a previous rung's
receipts; a superseded result is recorded as superseded, dated, and left
standing.

## 5. Required questions

Answer by proof, executable countermodel, or explicit OPEN status:

1. Is two the floor of declared inputs within the declared bounds?
2. Can the stream be a response at any declared bound, and at which?
3. Can the stake be read off the state, by which rules, and are they
   invariant under renaming?
4. Does a minimal engine exist; is it unique up to isomorphism; is it
   initial in its declared class?  Prove the universal property or refuse
   the claim.
5. Does any run exhibit a quantity preserved or monotone across every
   accepted round, and is it an invariant of the engine or of the bounds?
6. Can a state count its own rounds: is succession or duration definable
   from the state's observables, and if so through which trace?
7. Is adjacency definable, and does it carry a distance that is
   definable rather than declared?
8. Does the process have an arrow: are there states no run returns to,
   beyond the quotient barrier already proved?
9. What recurs across engines: roles, invariants, tie shapes, refusal
   shapes?
10. Is the surviving engine minimal or initial among engines meeting the
    same challenges?  Prove or refuse.
11. At what first stage do familiar structures become definable?
    Distinguish definable, useful realization, and forced.  Answer this
    question ONLY in the sealed comparison of section 9, after the
    freeze, and nowhere else.

## 6. Assumption and claim discipline

Every substantive notion is classified as exactly one of: metatheory
apparatus; supplied datum; externally imposed challenge; admitted
primitive; derived definition; proved theorem; deterministic computation;
countermodel; useful realization; conjecture; open obstruction; refuted
claim.

Never write "forced", "minimal", "free", "canonical", "equivalent",
"universal", "complete", or "engine" without a proof or a precise
conditional scope.

Keep presentation identity, internal identity, observational
equivalence, behavioral separation, and semantic interpretation distinct.
Keep supply, mention, admission, current-state designation, retention,
observation, and equality distinct.  Keep a demand read off the state
distinct from a demand emitted by an act.

Do not turn absence of a test into equality.  Do not turn a model proposal
into an admitted state change.  Do not use a receipt, hash, test pass, or
successful parser as proof of an unverified mathematical payload.  A pin
proves that a source did not move and nothing else.  A gate is not proved
by being green; it is proved by failing on the exact defect it exists to
catch, with the failure naming the injected object, and by recovering when
the injection is reversed.  Record every injection.

Prose that states a count dates it.  Prose that withdraws a sentence
quotes the withdrawn sentence.  Prose never writes a path it does not want
a reader to follow.

## 7. Python requirements

Implement each rung under `research/second_<rung>/` with its own code,
tests, receipts, pins, and configuration, as the sibling research trees
do.  The implementation must:

- be deterministic and typed, with mypy strict over each rung;
- consume the sealed kernel and any sibling tree read-only through their
  public functions, pinned by blob hash, and never copy their source;
- enumerate candidates only under declared finite bounds, and by default
  WITHOUT any pruning lemma proved for a different demand kind;
- decide equality, minimality, isomorphism, survivor counts, and proof
  status only by implemented algorithms, with the isomorphism cross-checked
  against a brute-force minimum over all bijections;
- replay every certified result from genesis;
- export machine-readable branch, level, assumption, and claim data with
  no timestamp and no environment value;
- never ask a language model to decide any of the above.

Each rung's tests must pass, and each rung's own line and branch coverage
must each reach 95%, measured from inside the rung.  Include negative
tests for every smuggling, false-minimality, or bundling failure
discovered.

## 8. Lean 4 requirements

Each rung that proves anything carries its own Lean 4 package under
`research/second_<rung>/lean/`, consuming the sealed package as a pinned
dependency, as the sibling research trees do.  Formalize every
theorem-level claim used by the paper.  Requirements:

- `lake build` passes; no `sorry`, `admit`, user-declared `axiom`,
  `unsafe`, or `partial`, in code or in comments;
- every exported theorem cited by the paper has a `#print axioms` report
  in its rung's committed axiom log, checked by the rung's verifier
  against a fresh build, never by grep over source;
- reliance on library axioms is recorded exactly in the claim ledger;
- failed theorem targets remain counterexamples or OPEN, never prose
  proofs;
- each research rung's Lean is pinned and its axiom log committed, so
  that no rung's axioms are a manual receipt.

## 9. Paper requirements

Create `research/second/paper.md`, `research/second/change_log.md`, and
`research/second/claim_ledger.md`.  The sealed `paper/` is not written;
where a second-derivation result supersedes a sealed sentence, the
sealed sentence stands and the supersession is recorded here, dated.
The comparison is written after the freeze only, and NOT in this
repository: this repository names no known theory anywhere, and the
companion repository where external citation is permitted is the only
place `comparison.md` may exist.

`paper.md` must contain: the experimental boundary and the supplied tree
hash; the metatheory/object-language separation; definitions in
dependency order; Challenges 0–5 and their exact results; the rung
protocol and the rungs run; branch and frontier results through the
achieved depth; proofs and countermodels; Python and Lean receipts; the
strongest defensible terminal theorem; limitations and open
obstructions.

`comparison.md` is written once, in the companion repository, after every
file of this run is frozen by hash, and it is the only place permitted to
name known mathematics or known physical theories.  It carries one row per named
structure: the first stage at which it is definable, whether it is a
useful realization or forced, the evidence, and a verdict.  Nothing in
the derivation may be revised in response to it; if the comparison shows
a defect in the derivation, the defect is recorded in the change log as
OPEN and the run ends.

## 10. Gates

The twelve gate families of this repository already run and are not
weakened.  Every rung registers its pin verifier, tests, and strict
typing in the research job of the workflow as part of the rung, so that
no rung is a manual receipt, and every rung commits its Lean axiom log.
Where a rung finds a gate that an injected defect leaves green, the
finding is recorded in `research/second/MANUAL.md` with the injection,
and the repair is proposed as its own pull request; the seal's own gate
scripts are the author's to change.  Prove each gate the run adds by
injection before trusting it.

## 11. Long-horizon operation

This run spans many sessions.  At the start of a session, read the
handoff; at the end, write it.  One rung per session at most.  Never
merge a rung yourself; the author merges.  When a rung is blocked, record
OPEN with the exact obstruction and take the next leftover; do not wait.
When a pin drifts because a supplied or sibling source moved, repin as a
logged act and re-read the affected prose by hand before trusting it.
When a receipt exceeds one megabyte, split it.  When a count in prose is
stated, date it.  Keep every gate under fifteen minutes of wall time per
rung, and record the time; verification is paid in one person's hours,
and a run that costs more than it verifies will have its rules removed.

## 12. Completion gate

Finish only when:

- every introduced notion has a source classification;
- every state change has a replayable admission history;
- the count of declared inputs is either reduced below two or proved at
  its floor within the declared bounds, with the bounds stated;
- every engine in the declared class is run to bounds, refuted, or
  recorded OPEN;
- every row of the definability census is proved, countermodelled, or
  OPEN at every stage reached;
- every theorem-level claim used by the paper has Lean evidence or is
  downgraded;
- every computational claim has deterministic Python evidence;
- all tied minimum branches are retained unless eliminated by proof;
- Python line and branch coverage each meet 95%;
- Lean builds without forbidden proof gaps and every module is audited;
- every gate is proved by injection;
- all intentional files are committed, the working tree is clean, this
  file is byte-identical to its pinned hash, and every sealed path is
  untouched, as the sealed gates verify;
- `comparison.md` is written after the freeze, in the companion
  repository only, and has caused no revision here;
- the paper states what was actually derived, including termination or
  failure, without targeting a predetermined conclusion.
