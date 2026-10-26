# STATUS: rung three -- the first-demand index over an arbitrary run

`AuthorityEffect: None`.  Counts in this file are dated 2026-09-23.  A
receipt is not a proof; a pin proves only that a source did not move; a
gate is proved by the defect it fails on, and every injection this rung
ran is recorded in `research/second/MANUAL.md` with its observed failure.

## The question, and where it came from

The sibling rung's leftover L-2, quoted verbatim in `CLAIM_LEDGER.md`
from a pinned span: the first-demand index over an arbitrary run.  The
seed's next-rung rule selects it, because it extends the census of
challenge five at the row for succession and because the parallel track
recorded the count of declared inputs at two with no reduction proved.

**Deviation from the plan's execution list, recorded.**  Item four of
`research/second/PLAN.md`, pinned here as a span, assigns the engine of
the seed's challenge three to this ordinal.  The seed's next-rung rule --
which the plan's own item six defers to -- selects L-2.  This rung
follows the rule and NOT the list; the engine is undone, is named as
leftover X-5 below, and nothing of it is started here.  `PLAN.md` is not
edited: a plan committed before substantive work is not rewritten to
match what happened.

## Source policy, declared before the first compile

RECONSTRUCTION, with a pin note per file.  `PROMPT.md`, frozen before any
Lean was built, says which parts are reconstructed and which are native.
The sealed package is not a Lake dependency of any research tree of this
repository, so the sealed kernel slice and the sibling rung's stake and
inertia slice are reproduced verbatim, each under a blob pin and span
pins, and each compared declaration by declaration against the pinned
blobs AT THE SNAPSHOT by `test_reconstruction.py`: 75 shared
declarations, all identical after comments, namespace lines and `open`
lines are stripped and whitespace is normalized.

**One extension to a hand-copied verifier, recorded.**
`test_reconstruction.py` is a hand copy of the sibling's.  Its normalizer
here also strips `open` lines, for the same declared reason it strips
namespace lines: this reconstruction flattens the sibling's four
namespaces into one, so an `open ... in` that precedes a declaration
there is absent here.  Without the extension one declaration
(`labelled_cases`) compared unequal for a reason that was not a drift.
The sibling copy still carries the narrower normalizer; the estate
records that a repair in one copy stays live in the others until carried
by hand, and this is an extension rather than a repair.

## What is proved, what is computed, what is open

**Proved in Lean** (87 theorems in the package, 44 of them
reconstructions; axioms within `{propext, Quot.sound}` for every one,
with no `Classical.choice` anywhere):

- the index is unique, with no decidability hypothesis;
- all six event kinds preserve well-formedness, so every prefix of every
  history from a well-formed base reaches a well-formed regime;
- a first count that is a successor never consumes a demand-inert event
  last;
- from the empty base no count below two is a first count;
- under the free stake no count is ever a first count;
- a decidable predicate with a witness has a least witness, by bounded
  upward search with no classical extraction;
- two countermodels: no function of the reached regime returns the index,
  and a demand can cease.

**Computed** over the declared rectangle -- three bases, seven stakes,
every sequence of at most four declared events: 577 sequences from the
empty base, 3928 from reading L, 14293 from reading F; every node
replayed from its base; two independently written index procedures
agreeing at every base, stake and sequence; the earliest counts, the
index distributions, the colliding regimes and the cessation kinds.

**Open, named and priced** (X-1 to X-6 below).  In particular EXISTENCE
of a first count is conditional on a decision for the demand predicate,
which this rung does not build.

## The frozen predictions, scored

Ten computational rows, scored mechanically by `run_index.py` and
recorded in `receipts/index.json`:

| row | value | verdict |
|---|---|---|
| I-12 | L 3928, F 14293 | HIT |
| I-13 | 577 sequences from the empty base | HIT |
| I-14 | earliest two for five stakes, four for `total_same`, absent for `free` | HIT |
| I-15 | earliest zero for five stakes at both readings, two for `total_same`, absent for `free` | HIT |
| I-16 | 0 procedure disagreements | HIT |
| I-17 | 0 inert-last-event violations | HIT |
| I-18 | cessation kinds exactly `AdmitInst`, `AdmitRuleAll` | HIT |
| I-19 | index set exactly two, three, four | HIT |
| I-20 | 21 colliding regimes | HIT |
| I-21 | 0 replay mismatches, reach agrees at every base, receipt byte-identical | HIT |

Eleven Lean rows (I-1 to I-11) and three gate rows (I-22 to I-24) are
scored where their evidence lives and are marked so in the receipt rather
than omitted: I-1, I-2, I-7 and I-23 by `test_census.py`; I-3 to I-6 and
I-8 to I-11 and I-22 by `verify_lean.py` and the committed axiom log;
I-24 by the measured time below.  Each is met.  I-X, the extrapolation,
is PENDING and is scored by the first later rung that declares a
responder.

### The census prediction, and its eight misses

`PREDICTIONS.md` named 25 Lean targets and a class for each, frozen
before the compile.  All 25 exist.  Scored mechanically by
`test_census.py`: **17 hits, 8 misses**, and **19 further native
declarations** were written that the frozen list did not name.

Every one of the eight misses is a DEMOTION, and seven of them are the
same mistake: the prediction called a target CONTENT when its proof turned
out to be an assembly of neighbours or a two-line corollary.

| target | predicted | recorded | why |
|---|---|---|---|
| `replayE_append` | CONTENT | RECONSTRUCTION | it is the SEALED estate's own theorem; the work was already done, and the prediction did not know it |
| `wf_stateAt` | CONTENT | THIN | one line from `wf_replayE`, which carries the induction |
| `data_le_stateAt` | CONTENT | THIN | three lines from `data_le_replay` |
| `no_index_below_two_from_the_empty_base` | CONTENT | THIN | a corollary of `data_le_stateAt` and `demand_needs_two_data` |
| `index_is_not_a_function_of_the_reached_regime` | CONTENT | DEFINITION | an existential assembled from three theorems proved elsewhere |
| `no_state_function_gives_the_index` | CONTENT | THIN | three lines from the two index computations |
| `demand_can_cease` | CONTENT | DEFINITION | an existential assembled from four neighbours |
| `first_demand_index` | CONTENT | DEFINITION | a six-clause conjunction, each clause applied by name |

**What the misses say.**  The content of this rung sits in fewer places
than the prediction expected: in `stateAt_succ`, `first_demand_unique`,
`wf_step_any`, `wf_replayE`, `data_of_step`, `data_le_replay`,
`first_demand_follows_a_changing_event`, `least_witness_from`,
`first_demand_exists_when_a_demand_is_decidable`, and in the three
`index_of_*` computations and `separated_has_no_demand` that the
countermodels rest on.  The headline statements are assemblies of those,
and the census says so rather than counting them twice.  The census is
total over the package and is checked in both directions, so a later
silent promotion is visible.

## Leftovers, named and priced, executed nowhere

- **X-1, the decision procedure for a demand at a regime.**  Whether a
  regime carries a demand is a statement over the sealed context type.
  The well-formed contexts of a fixed regime are finitely many -- the
  form is bounded by the form list, the slot count by the form's arity,
  and each slot by the data count -- so the enumeration exists.  Building
  it in Lean and proving it complete would discharge the hypothesis of
  `first_demand_exists_when_a_demand_is_decidable` and make the Python
  rectangle and the Lean statements the same object.  Price: one moderate
  rung, mostly the completeness induction over the slot list.
- **X-2, the first count under a run that is generated rather than
  enumerated.**  Every count here is read off a history supplied from
  outside.  What a responder would do to the count is the subject of the
  frozen extrapolation I-X and is not touched.  Price: a rung, and it
  needs the engine of X-5 first.
- **X-3, the index up to the implemented isomorphism.**  The rectangle
  counts sequences, not classes: two histories that differ by a renaming
  of presentation tokens are two nodes.  Whether the first count is an
  invariant of the isomorphism class is neither proved nor computed here.
  Price: small, and the sealed `iso.py` is the tool.
- **X-4, the safety of the seventeen omitted declarations.**  The
  reconstructions carry the slice the theorems need; seventeen
  declarations of the pinned sources are omitted, pinned by name, and
  mentioned nowhere in the reconstructions.  That they are not NEEDED is
  read by hand.  Price: small.
- **X-5, the engine of the seed's challenge three.**  The plan's item
  four, and the sibling stake rung's own first leftover.  Not started
  here in any direction.
- **X-6, the other eleven rows of the challenge-five census.**  Two-ness,
  observational classes, duration, adjacency, reach, invariants,
  irreversibility, symmetry, branching, exhaustion and recurrence.  This
  rung decides one row and claims nothing about the rest.

## Gates and timing

Measured on this machine, 2026-09-23, serially:

| gate | command | measured |
|---|---|---|
| pins, spans, frozen texts | `python research/second_index/verify_pins.py` | 4.5 s |
| tests under coverage (133 tests) | `python -m coverage run -m unittest discover -s . -p "test_*.py"` | 138.2 s |
| coverage gate | `python -m coverage json -q; python check_coverage.py` | 1.2 s |
| receipt comparison | `python run_index.py --check` | 13.9 s |
| strict typing | `python -m mypy` | 1.5 s |
| clean Lean build and axiom audit | `python verify_lean.py` | 61.4 s |

Grouped measured time **220.7 seconds**, inside the fifteen-minute
per-rung ceiling the seed sets.  Each row is one wall-clock measurement
on this machine, taken serially with nothing else running; a second
measurement of the same command differs, and the ceiling is what the
number is for.  The Lean row is a CLEAN build: `lake clean` then a full
rebuild, then the compiled-environment census.  Coverage over the declared measured set
(`index.py`, `run_index.py`, `verify_pins.py`): **line 98.98%, branch
95.79%**, both above the 95% floor.  The two exclusions and their reasons
are declared in `check_coverage.py`.

These are local receipts.  Hosted CI is permanently disabled by author
decision; the workflow is the written contract and its steps are run
here.  A green gate is not a proof of anything but that the gate did not
fire.

**How they were run, exactly.**  `python ci/run_gates.py --job research
--step "rung 3"` is the documented way to run a registered step, and it
refused: the machine-wide lock `19L57G1-run_gates.lock` was held by
another run, and two runs cannot overlap on one machine.  The lock was
left alone.  Each registered command was therefore run directly, from the
rung's own directory, in the order the contract lists them, and the
measurements above are those runs.  `python ci/run_gates.py --list`
enumerates all four registered steps of this rung -- three in the
research job and one in the lean job -- so the contract parses as
written; that the runner would EXECUTE them was not observed here, and
this paragraph is the receipt of that limit rather than a claim past
it.

## A defect found live, and repaired

`index.py` consumes the sibling rung read-only through its public
functions.  The sibling module protects ITSELF from being shadowed by
putting its own directory at the front of the import path when it is
imported -- so doing the same for this tree BEFORE that import does not
last.  Under `unittest discover` the loader then imported the SIBLING's
`test_pins` instead of this rung's and refused with an import error
naming the wrong directory.  The repair is to put this tree back at the
front AFTER the sibling import, and the reason is written at the place it
is done.  The sibling's own note records the shallower version of the
same defect; this is the deeper one.

## An observation about the prose census, recorded

The first probe for the watched-term injection used the term the sibling
rung's injection record names, and it did not fire: that term is not in
the current watched population, and a term drawn from the current list
was used instead.  A probe must be chosen from the list as it stands, not
from a record of what it once held.  Nothing here says why the population
moved, and this rung did not regenerate the pin.

## Terminal scope

- `INDEX_DEFINED` -- DEFINITION, `stateAt`, `HasDemand`, `IsFirstDemand`.
- `INDEX_UNIQUE` -- PROVED_THEOREM, every base, history and stake.
- `INDEX_FOLLOWS_A_CHANGING_EVENT` -- PROVED_THEOREM, well-formed base only.
- `INDEX_BOUNDED_BELOW` -- THIN, the empty base only.
- `INDEX_EXISTS` -- PROVED_THEOREM, CONDITIONAL on a decision not built here.
- `INDEX_NOT_A_STATE_FUNCTION` -- COUNTERMODEL, the empty base and the apart-labelling stake.
- `DEMAND_CAN_CEASE` -- COUNTERMODEL, one exhibited four-event history.
- `RECTANGLE_MEASURED` -- FINITE_COMPUTATION, the frozen rectangle only.
- `CENSUS_SUCCESSION_DECIDED` -- COUNTERMODEL, one row of eleven.
- `INPUT_COUNT_UNCHANGED` -- RECORDED, value two, no proof of a floor, no reduction.
- `OBSTRUCTIONS_UNTOUCHED` -- RECORDED.

```yaml
steps_completed: [Reconstruct, Index, Countermodels, Rectangle, Census, Register]
write_root: research/second_index/
snapshot: 110fededbeb63efd839287d3a4eda7a62aee4d97
sealed_paths_touched: []
shared_files_touched:
  - .github/workflows/verify.yml (append only)
  - research/second/MANUAL.md (append only)
  - research/README.md (generated view)
  - docs/index/pins.md (generated view)
  - docs/lean_build_order.md (generated view)
  - ci/tree_custody_pin.json (generated view)
census_pin_regenerated: false
prompt_sha256: 8487d72e4f3840b89ca86b379c1b2a4b1cce9649075cfea4753366a9405fdcc3
predictions_sha256: 410c6ff9d17d449f0fbe03e09e6433f3756939615bb7dbab0a44e34f0c59cba3
bases: [EMPTY, L, F]
stakes: [free, total_apart, total_same, parity, residue_three, chain, one_sided_total]
sequences: {EMPTY: 577, L: 3928, F: 14293}
lean_theorems: {total: 87, reconstruction: 44, content: 16, thin: 14, definition: 13}
predictions_scored: {hit: 10, missed: 0, elsewhere: 14, pending: 1}
census_prediction_scored: {named: 25, hit: 17, missed: 8, unpredicted_native: 19}
input_count: {value: 2, proof: none, sentence: "This rung neither reduces the count of declared inputs nor proves it at a floor."}
census_rows_decided: [succession]
gate_time_seconds: 220.7
authority_effect: None
final_state: true
```

## The next rung, named so it cannot be smuggled in later

The seed's rule takes the smallest named leftover that EITHER reduces the
count of declared inputs OR extends the census of challenge five, and on
a tie the one named first.  Applied to the six leftovers above:

| leftover | reduces the input count | extends the census | eligible |
|---|---|---|---|
| X-1 decision procedure | no | no | no |
| X-2 count under a generated run | no | not until X-5 exists | no |
| X-3 index up to the implemented isomorphism | no | yes | yes |
| X-4 safety of the omissions | no | no | no |
| X-5 the engine | no | no | no |
| X-6 the eleven undecided rows | no | yes | yes |

Two are eligible and X-3 is much the smaller, so there is no tie to
break: the next rung is **X-3, the index up to the implemented
isomorphism** -- whether the first count is an invariant of the
isomorphism class, which is a second reading of the census row for
succession and bears on the row for symmetry.

X-1 is not eligible on the plain reading of the rule -- the declared
inputs are the stake and the stream, and X-1 touches neither -- so it is
recorded here as the leftover a later rung should take, and not taken
now.  Nothing of any leftover is started here.
