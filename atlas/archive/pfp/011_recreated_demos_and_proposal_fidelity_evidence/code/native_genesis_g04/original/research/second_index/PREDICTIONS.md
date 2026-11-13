# PREDICTIONS: rung three -- the first-demand index over an arbitrary run

`AuthorityEffect: None`.  Frozen by sha256 before the first computation
and before any Lean of this rung is built.  Scored mechanically by
`run_index.py` for the computational rows and by `test_census.py` for the
census rows.  A missed prediction is recorded next to its value and never
edited.  A miss is a finding, not a defect.

Each prediction carries a falsifier and an explicit FORCED / NOT FORCED
label.  FORCED means the outcome follows from definitions already fixed
before this rung, so a hit evidences the ordering of the work and not
insight.  NOT FORCED means the run could have come out the other way.

## Declared before the compile: the FW-DEF census this rung commits to

The census below is a prediction, not a report.  Four classes, as the
sibling rung uses them: RECONSTRUCTION (reproduced verbatim under a pin,
not this rung's work); DEFINITION (true by unfolding, by `rfl`, by a
projection, by one rewrite, or by pure case exhaustion); THIN (one
genuine step, or a direct corollary of a neighbour); CONTENT (everything
else).

Predicted DEFINITION:

- `stateAt_zero`
- `free_stake_has_no_index`
- `quiet_before_the_index`
- `shared_regime_of_two_histories`

Predicted THIN:

- `stateAt_full`
- `replayE_singleton`
- `data_le_step`
- `demand_needs_two_data`
- `no_demand_of_data_le_one`
- `first_demand_zero_iff_base_carries_one`
- `inert_run_carries_no_index`

Predicted CONTENT:

- `replayE_append`
- `stateAt_succ`
- `first_demand_unique`
- `wf_step_any`
- `wf_stateAt`
- `data_le_replay`
- `data_le_stateAt`
- `no_index_below_two_from_the_empty_base`
- `first_demand_follows_a_changing_event`
- `first_demand_exists_when_a_demand_is_decidable`
- `index_is_not_a_function_of_the_reached_regime`
- `no_state_function_gives_the_index`
- `demand_can_cease`
- `first_demand_index`

The names above are the ones this rung commits to before Lean has run.  A
name that changes, a target promoted or demoted between classes, or a
declaration added beyond this list is visible in the committed census and
is recorded in `STATUS.md` as unpredicted work.

## Stage one -- the prefix reading

- **I-1** (FORCED).  `stateAt_zero` is at the level of a definition: the
  prefix of length zero replays to the base by `rfl`.
  Falsifier: it needing an argument beyond unfolding.
- **I-2** (NOT FORCED).  `replayE_append` and `stateAt_succ` are PROVED:
  a prefix one longer replays as the shorter prefix followed by the one
  event the index counts last, for every history and every index below
  the history's length.
  Falsifier: either OPEN, or either provable only under a hypothesis on
  the event.

## Stage two -- the index over an arbitrary run

- **I-3** (NOT FORCED).  `first_demand_unique` is PROVED with no
  decidability hypothesis and no hypothesis on the events of the history:
  for one base, one history and one stake, at most one count is a first
  count.
  Falsifier: OPEN, or a proof carrying a decidability hypothesis, or two
  distinct first counts for one base, history and stake.
- **I-4** (NOT FORCED).  `wf_step_any` is PROVED for all six event kinds:
  every kind of the grammar carries a well-formed regime to a well-formed
  regime whenever the grammar admits the step at all.  Hence
  `wf_stateAt`: every prefix of every history from a well-formed base
  reaches a well-formed regime.
  Falsifier: any kind needing an extra hypothesis, or a well-formed
  regime and an admitted step reaching an ill-formed regime.
- **I-5** (NOT FORCED).  `first_demand_follows_a_changing_event` is
  PROVED: from a well-formed base, when the first count is a successor,
  the event the prefix consumes last is NOT one of the three demand-inert
  kinds the sibling rung proved inert.
  Falsifier: OPEN, or a well-formed base and a history whose first count
  is a successor consuming a supply, an imposition or a form admission
  last.
- **I-6** (NOT FORCED).  `no_index_below_two_from_the_empty_base` is
  PROVED: from the regime with nothing admitted, no count below two is a
  first count, for any stake and any history whatever.  The argument goes
  through `data_le_stateAt`, that a prefix of length k reaches a regime
  holding at most k data.
  Falsifier: OPEN, or a history from the empty base with a demand at
  count zero or count one.
- **I-7** (NOT FORCED).  Existence is NOT proved outright.  The committed
  `first_demand_exists_when_a_demand_is_decidable` carries an explicit
  hypothesis that carrying a demand is decidable at a regime, and this
  rung does NOT build that decision procedure for the sealed grammar: the
  finite enumeration of well-formed contexts that would build it is
  recorded as a named, priced leftover and is executed nowhere.
  Falsifier: the committed Lean proving existence with no such
  hypothesis, or building a decision procedure for separability over the
  sealed regime.
- **I-8** (FORCED).  `free_stake_has_no_index`: under the stake that
  labels every pair free, no count is a first count, at any base, along
  any history.  At the level of a definition, through the sibling's
  pinned theorem.
  Falsifier: a base, a history and a count that is a first count under
  that stake.

## Stage three -- the countermodels

- **I-9** (NOT FORCED).  `index_is_not_a_function_of_the_reached_regime`
  is PROVED by an exhibited pair of histories from the empty base that
  reach one and the same regime with first counts two and three, under
  the stake labelling every distinct pair apart.  The two counts are
  predicted to be exactly two and three.
  Falsifier: OPEN; or the exhibited counts being any other pair of
  numbers; or the statement holding only for some other base.
- **I-10** (NOT FORCED).  `no_state_function_gives_the_index` is PROVED
  in the stronger negative form: there is no function from regimes to
  numbers that returns the first count of every history reaching that
  regime.
  Falsifier: OPEN, or the negative form needing a hypothesis the
  exhibited pair does not supply.
- **I-11** (NOT FORCED).  `demand_can_cease` is PROVED by an exhibited
  history of four events from the empty base under which a demand stands
  at the prefix of length two and no demand stands at the prefix of
  length four.  The event the fourth prefix consumes last is predicted to
  be the admission of a judgment instance.
  Falsifier: OPEN; or the exhibited history needing more than four
  events; or the ceasing event being of another kind.

## Stage four -- the finite cross-check

The bases, the bound and the alphabet are frozen here and are not chosen
after seeing a count.

- **Declared bases.**  Three: the EMPTY regime, with nothing admitted;
  and the two sealed genesis readings L and F, consumed from the sealed
  engine through its public `READINGS`.
- **Declared rectangle.**  From each base, every sequence of at most four
  events of the declared alphabet, enumerated without any pruning lemma,
  through the sibling rung's public enumerator, pinned by blob: one
  supply of one declared token; one datum admission per step with a fresh
  token drawn from a declared list of five; a form admission of arity one
  and of arity two; an instance admission for every admitted form index
  and every argument tuple within the data bound; a rule admission for
  every admitted form index; and an imposition for every ordered pair of
  held data.  At most five data and at most two forms.
- **Declared stakes.**  The seven the sibling rung declares: the free
  stake, the five the two-sided tree declares, and the stake the pinned
  one-sided total commitment induces.
- **I-12** (NOT FORCED).  Replay of the sibling receipt: the rectangle
  from base L holds 3928 sequences and the rectangle from base F holds
  14293 sequences.
  Falsifier: either count differing.
- **I-13** (NOT FORCED).  The rectangle from the EMPTY base holds more
  than one hundred and fewer than three thousand sequences.
  Falsifier: a count at or below one hundred, or at or above three
  thousand.
- **I-14** (NOT FORCED).  The earliest first count over the rectangle
  from the EMPTY base is two for `total_apart`, `parity`,
  `residue_three`, `chain` and `one_sided_total`; is four for
  `total_same`; and does not exist for the free stake.
  Falsifier: any one of the seven values differing.
- **I-15** (NOT FORCED).  The earliest first count over the rectangle
  from base L and from base F is zero for `total_apart`, `parity`,
  `residue_three`, `chain` and `one_sided_total`; is two for
  `total_same`; and does not exist for the free stake.
  Falsifier: any one of the fourteen values differing.
- **I-16** (FORCED).  Over every base, every stake and every sequence of
  the rectangle, the first count computed by walking the sequence forward
  and the first count computed by the independently written second
  procedure agree; the count of disagreements is zero.
  Falsifier: one disagreement.
- **I-17** (NOT FORCED).  Over every base, every stake and every sequence
  of the rectangle whose first count is a successor, the event kind that
  count consumes last is never a supply, an imposition or a form
  admission; the count of violations is zero.
  Falsifier: one violation.  This is the rectangle's check of the theorem
  of I-5 and is not its proof.
- **I-18** (NOT FORCED).  The set of event kinds at which a demand
  standing at one prefix does not stand at the prefix one longer is
  exactly the admission of a judgment instance and the admission of a
  uniform rule, over the whole rectangle.
  Falsifier: the set containing any other kind, or missing either of the
  two, or being empty.
- **I-19** (NOT FORCED).  From the EMPTY base under `total_apart`, the
  set of first counts taken over every sequence of the rectangle that has
  one is exactly two, three and four.
  Falsifier: any other set.
- **I-20** (NOT FORCED).  From the EMPTY base under `total_apart`, at
  least one pair of sequences reaches one and the same regime with
  differing first counts; the count of such regimes is at least one.
  Falsifier: no such regime in the rectangle.
- **I-21** (FORCED).  The receipt regenerates byte-identically, every
  node of the rectangle replays from its base to the regime recorded for
  it, and the independently written second enumerator reaches exactly the
  regimes the first reaches on the declared cross-check family.
  Falsifier: a byte difference, a replay mismatch, or a regime reached by
  one enumerator and not the other.

## Stage five -- gates and the census of challenge five

- **I-22** (NOT FORCED).  Every theorem of this rung's Lean package
  depends on no axiom outside `propext` and `Quot.sound`, and the
  committed axiom log matches a fresh build report for report.
  Falsifier: any other axiom, or a difference between the log and a fresh
  build.
- **I-23** (NOT FORCED).  This rung decides exactly one row of the seed's
  challenge-five census, the row for succession, and decides it as NOT
  DEFINABLE from the state's own observables, at the stage reached, by
  the countermodel of I-10.
  Falsifier: the rung deciding no row, or deciding more than one row, or
  deciding succession in another direction.
- **I-24** (NOT FORCED).  The measured wall time of this rung's own gates
  stays under fifteen minutes, as the seed requires, and is recorded in
  `STATUS.md`.
  Falsifier: a measured time at or above fifteen minutes.

## The extrapolation

- **I-X** (NOT FORCED).  **Statement.**  Let a later rung declare a
  responder: a rule that answers a demand read off the state by a minimum
  response under one of the sealed cost measures.  The first count of a
  run driven by such a responder from the EMPTY base is not bounded above
  by any number this rung's bounds supply: for every bound the later rung
  declares on the length of a run, there is a stake among the seven
  declared here whose first count under that responder exceeds that bound
  or does not exist.

  **Why it is not forced.**  This rung bounds the first count from below
  and exhibits its dependence on the history, and says nothing about a
  run that is generated rather than enumerated.  A responder could fix
  the first count at a constant, could make it grow with the bound, or
  could remove it.  Nothing proved here settles which.

  **Scoring rule.**  Scored by the first later rung that declares a
  responder and runs it forward, and by no earlier rung.  HIT if that
  rung exhibits, at each of its declared bounds, a stake whose first
  count exceeds the bound or does not exist.  MISSED if that rung proves
  a uniform upper bound on the first count over the seven stakes declared
  here.  VACUOUS if no later rung declares a responder.  The statement is
  never rescored by this rung and is never edited.

## What this rung does not predict

Nothing about the count of declared inputs, in either direction: this
rung neither reduces it nor proves it at a floor, and its receipt records
that claim as absent.  Nothing about the other rows of the
challenge-five census beyond succession.  Nothing about the sealed
estate's standing obstructions, which this rung leaves exactly where it
found them.
