# level_engine: the Mode E level engine

AuthorityEffect: None. Nothing here is in force except what `RULINGS.md` records.

This is the external level engine of the MSS-N reach plan (plan round P1,
stream E; design `research/19L57G1_H3V7N5QF/_brainstorm/W2-C02_level_engine.md`).
It pins 19L57G1 read-only and answers supplied challenges on its sealed
grammar. It emits layer-1 records and the checker-input bundles for this
repository's target checkers. It never writes a reach grade.

## History

Round E0 was built in a local-only repository at
`C:\Users\a343o\source\repos\level_engine` (head `bedd057`), then moved here by
the author's ruling of 2026-09-25 (`RULINGS.md`). That repository holds E0's
commit history. The gate's `freeze` step checks E0's freeze order there
(`HISTORY.json`): predictions, then specs, then records. Later rounds freeze
inside this repository.

## Run (from this directory)

```powershell
python tools/vendor.py          # clone 19L57G1 into vendor/ at the pin (or verify it)
python gate.py                  # every gate step; each prints its own exit code
python tools/inject.py          # the injection panel (needs a clean tree)
python run_bootstrap.py         # rebuild bundles/ and bindings/generated/
python tools/lean_gen.py        # regenerate the Lean certificates and the axiom-report module
lake build                      # build the Lean package (core Lean 4.33, no Mathlib)
python tools/lean_audit.py      # census and axiom policy; --write refreshes lean/axioms.txt
python tools/lift_check.py      # certify record_reading's two steps against lifts/record_reading/expect.json
python tools/reach_replay.py    # replay the level records through the receiving side; --dry-run writes nothing
```

The ladder table is read with `git show` at the pinned commit, from the
repository that contains this directory. The root `pytest.ini` ignores
`research/`; this directory carries its own `pyproject.toml`, so run the tools
from here.

## Layers

| layer | contents | vocabulary | ports in Mode I |
| --- | --- | --- | --- |
| `engine/` | exact arithmetic (Python, and Lean in `engine/lean/ExactRat`), encoding, typed kinds, fixed claims, search, stage contract, level runner, reading-ladder mirror and lift certifier, hygiene, pre-flight | native only (count-only scan, zero hits) | yes |
| `lifts/` | proposed stage changes on a carrier's own ladder, the pre-registered extension class, frozen expectations | native only (same scan) | yes |
| `lean/` | the generated axiom-report module and the committed report `axioms.txt` | native only | yes |
| `payload/<id>/` | restatement, fixtures, mutation, compile step, frozen expectations | native only (same scan) | yes |
| `outward/` | the receiving side's record shapes (bundle, loss ledger, certificate, lift certificate, probe battery, `reach-receipt/1` level records) | outside schema names | no |
| `bindings/` | level numbers, ladder row digests, fixture-role map, adapters to target checkers, generated certificates, register entries, checker inputs, record stubs, lift records, grade table | outside names allowed | no |
| `bundles/` | layer-1 bundles, challenge evidence, loss ledgers, content-addressed | no level numbers | no |

## Outcome at the current pin (19L57G1 `535fb553`)

Computed; see `bindings/generated/grade_table.json`.

| level | challenge | answer type | status | native clauses | notes |
| --- | --- | --- | --- | --- | --- |
| 000 | `bare_inscription` | A | EXPECTED | 0 of 1 | the byte clause is apparatus (not coverage, D3); supply is inert; sealed Lean cited |
| 001 | `first_separation` | D | EXPECTED | 1 of 3 | reproduces the sealed minima (L 3 / F 5 classes under mu1, 1 / 1 under mu2); supplied, not native |
| 002 | `edge_endpoints` | D | EXPECTED | 3 of 3 | the own negative is refused by sealed admission |
| 003 | `cell_faces` | D | EXPECTED | 5 of 5 | the own negative is refused by sealed admission; a missing side is never added |
| 004 | `cell_orientation` | D | EXPECTED | 14 of 14 | the sign choice is a witness (`unique_class`, 2 literal); three cells on one side have no witness |
| 005 | `distance_form` | M | EXPECTED | 4 of 6 | the value clauses stay decoded (CAP-SUPPLIED), hosted not native; since E0.5 each is decided by the kernel on every evaluated fixture (15 certificates) |

Since round P2, every row is replayed at R1 by its checker of record. See
the Round P2 section below. Round P3 adds 007, 008, 010, 018, 019 and 021
through the engine, and 011 and 016 as replays of sealed evidence; see the
Round P3 section.

## Alignment with the reach checker (`research/mssn_sn_tower/code/python/reach/`)

- **Done:** intake refuses hollow payloads by the reach rules (no datum
  anywhere; a verdict-named key anywhere; every datum a boolean). Each
  checker-input bundle runs the reach probe battery through the harness
  intake, and carries `expected_outcome` in the `PASS` / `REFUSED` vocabulary.
- **Since round P2:** the checkers of record for 000–005 exist (PR #67).
  Adapters state the engine's fixtures in their inputs, and the records are
  replayed and stored (see the Round P2 section). The engine's probe battery is
  the receiving side's own `targets.probe_battery`, imported, not copied. A
  probe equal to the positive, such as level 000's `lists_emptied`, is marked
  `PROBE-IDENTICAL-TO-POSITIVE` and not run. Level 001's `lists_emptied` still
  carries a datum, so only the target's schema refuses it, and it does.

## Round E0.5: exact rationals in Lean

`engine/lean/ExactRat` is a native fraction type: an integer numerator over a
positive natural denominator. Two fractions are equal exactly when they
cross-multiply equal; `QN` is the quotient by that relation. Proved over `QN`:
the commutative-ring laws, the field law (`x * x⁻¹ = 1` for `x ≠ 0`, with
`0⁻¹ = 0`), decidable equality, and an order given by a positive cone.
Laplace determinants and leading minors are structurally recursive, so the
kernel decides them on concrete matrices. All 49 reported declarations depend
on at most `propext` and `Quot.sound`. No Mathlib is used, and no `grind`,
whose proofs depend on `Classical.choice`.

`tools/lean_gen.py` writes level 005's certificates from its fixtures. Each
certificate states the Python verdict and is re-decided by `decide`, so a
disagreement fails the build. The level runner cites each certificate with its
axioms, and names any the report lacks.

See `INJECTIONS.md` for the guards proved by injection, and `predictions/` for
the frozen and scored predictions of rounds E0 and E0.5.

## Round P2: level records (E2) and record_reading's lifts (A3)

### E2: level records for 000–005, up to replay

`outward/reach.py` builds each level's record in the receiving side's
`reach-receipt/1` shape (`research/mssn_sn_tower/code/python/reach/`, PR #58).
A record has two halves:

- **The carrier half.** It holds the ladder pins, framing (`AP` at 000, `SC`
  at 001–005), provenance, non-claims and the harness's own Lean citations.
  It also holds the loss ledger in `mssn.loss-ledger.v2`, with every standing
  entry of 19L57G1 booked: readings, claim class, cost measure, declared
  bounds and name-blindness. `run_bootstrap.py` commits this half as
  `bindings/generated/reach/L00N.stub.json`, and the gate's records step
  checks it byte for byte. It also commits `axioms.reach.txt`, which restates
  `lean/axioms.txt` line by line in the `#print axioms` form the receiving
  side parses.
- **The target half.** It needs the level's checker of record, for its pin,
  its own negative and its codes. It also needs an adapter,
  `bindings/adapters/L00N.py`, which states the engine's own fixtures in that
  checker's input schema and books in the loss ledger whatever has no image.

`python tools/reach_replay.py` completes, checks and stores the records. For
each level it:

1. completes the record at the harness commit (`HEAD`; the tree must be
   clean and `HEAD` on `origin`);
2. runs the receiving side's own `check_record` in its default context;
3. stores the receipt where its CLI stores receipts, unless the record is
   refused;
4. regenerates `ledger.jsonl` and `derived/numbers.json` with the receiving
   side's CLI, and prints the computed C.

A level with no checker of record prints `AWAITING_CHECKER`. A level with a
checker but no matching adapter prints `AWAITING_ADAPTER`.

**Replayed (round P2, after PR #67 registered the stage 0–21 checkers).** The
records were replayed at harness commit `5dcd0212`, and all six are
`EVIDENCE_ONLY` at R1. The receiving side computed these numbers; no carrier
number is typed here.

| carrier key | levels at R1 | C | A | D |
| --- | --- | --- | --- | --- |
| `19L57G1` (replayed sealed evidence) | 000 (apparatus), 001 | 1 | 1 | 0 |
| `19L57G1+harness` (harness computation) | 002, 003, 004, 005 | 4 | 0 | 0 |

The keys are never summed. Level 005 reaches E = LEAN: its positive's kernel
certificates are cited from `axioms.reach.txt`.

**What each adapter claims.** Each adapter claims only the target clauses that
the engine's own fixtures bite with a single edit:

| level | clauses bitten | booked as having no image |
| --- | --- | --- |
| 000 | interior glyph, nested packet | none |
| 001 | source omitted, generators | none |
| 002 | absent endpoint | the protected pair (dropped); the lift is the hosting lift's image of the positive, unchanged; no self-loop, so the obstruction-carrier clauses are unclaimed |
| 003 | missing subface | the `mark` sort (dropped) |
| 004 | missing edge | the sign witness (dropped); the order is the declared order of elements, a convention |
| 005 | incomplete lengths, non-positive length, indefinite Gram | the diagonal and the symmetry of the table (dropped); no hinge, so the curvature clauses are unclaimed |

**Mode E carrier convention.** Every record's carrier commit is a harness
commit in this repository, and 19L57G1 is pinned inside it (`PINS.json`). The
receiving side's `carriers.json` declares 19L57G1's `harness_host` as
`the_symbol_game`. Its resolver tries that host only after any clone of
19L57G1, and only commits in the host's history resolve there. So
`ledger --check` verifies these rows with no clone argument, and a 19L57G1
commit never resolves here. The harness commit must stay reachable: merge with
a merge commit, not a squash.

**The pipeline is also proved against a test-only draft.** `tests/reach_draft/`
holds a draft checker for level 002, in the draft schema, and its adapter.
Neither is registered. The completed record passes every receiving-side check,
capped at `SELF_CONSISTENT_ONLY`.

### A3: record_reading's two steps as residual-licensed lifts

`engine/ladder.py` mirrors `research/record_reading` from the vendored clone,
read only. A rung reads a key of fixed width: the active datum and the record
entries before it. The mirror reproduces the carrier's committed census
exactly: 10, 22 and 70 tapes, with the same breaking and unrealisable lists.

`engine/ladder_cert.py` certifies each step from a **demand**, the carrier's
own exhibit tape, which the rung below cannot write. It computes sixteen
conditions from the pinned evidence and never reads them from the proposal.
They follow document 07 §5 and C04's R2:

| condition | criterion | code |
| --- | --- | --- |
| certified survivor | R2.2 | `NO_CERTIFIED_SURVIVOR` |
| claims fixed | R2.2 | `CLAIM_FROZEN` |
| exhaustion | R2.4 | `EXHAUSTION_NOT_CLOSED` |
| context witness | R2.3 | `NO_CONTEXT_WITNESS` |
| class pre-registered | R2.5 | `CLASS_NOT_PREREGISTERED` |
| minimal, ties retained | R2.6 | `NOT_MINIMAL_OVER_A_CLASS` |
| traceable | R2.5 | `UNTRACEABLE` |
| resolved | R2.6 | `NOT_RESOLVED` |
| preserved | R2.7 | `NOT_PRESERVED` |
| rollback d(u(x)) = x | R2.8 | `RR-ROLLBACK` |
| descent | R2.8 | `RR-NON-DESCENT` |
| non-trivial, priced | R2.9 | `RR-TRIVIAL-LIFT` |
| survival accounting | R2.10 | `SILENT_DRIFT` |
| evidence only | R2.13 | `AUTHORITY_FIELD` |
| budget, typed stop | R2.11 | `BUDGET_NOT_DECREASING` |
| replay | R2.13 | `REPLAY_MISMATCH` |
| chain (over the steps) | R2.1 | `CHAIN_BROKEN` |

The extension class, rungs 0 to 2 on the observed three-point setting, was
pre-registered by digest in `predictions/FROZEN_P2.json` before the run.
Results are in `bindings/generated/lifts/record_reading.json`.

| step | demand | same-level search | context witness | minimal extension | failing |
| --- | --- | --- | --- | --- | --- |
| rung0 → rung1 | `0,1,0,0` | 64 of 64 programs, none writes it | `(0,0)` against `(1,0)`: the entry 1 back | cost 3, 2 tied minima | `non_descent` (`RR-NON-DESCENT`) |
| rung1 → rung2 | `0,1,2,0,1,0` | 262144 of 262144, none writes it | `(0,0,1)` against `(2,0,1)`: the entry 2 back | cost 5, 16 tied minima | `rollback` (`RR-ROLLBACK`), `non_descent` (`RR-NON-DESCENT`) |

**Computed D = 0.** Both steps fail R2.8 on the carrier's own down map.

- **Step 0→1.** `Record.forget` is total. d(u(x)) = x holds on all 64 old
  images, but every new term gets an old meaning; the carrier's own
  `forget_twist` exhibits that default. No term is refused.
- **Step 1→2.** The carrier defines no down map from rung2 at all.

Every other condition passes on both steps, and the chain is unbroken.

A diagnostic run swaps in the harness's partial restriction, which is
identity on the lifted image and `NON_DESCENT` on a table that reads the older
entry. With it, both steps are licensed. That map is not the carrier's, so it
enters no verdict and no depth. What would close R2.8 is a partial retraction
inside 19L57G1, which waits for Mode I. By ruling D4 these lifts are recorded,
not counted, in any case.

`python tools/lift_check.py`, the gate's `lifts` step, compares every verdict
with `lifts/record_reading/expect.json`. Injections I18 to I34 prove each
condition by a mutated lift. I35 proves the reach records' ledger booking.

**Readings the author may overrule:**

- The survivor condition reads R2.2 carrier-neutrally. The survivor is a
  demand that no program of the source rung writes, certified twice: by the
  closed enumeration, and by a dual witness replayed on the demand alone (two
  positions with one key and two successors). It is not a cochain residual,
  so the receiving side's K8 matrix check does not apply.
- Each demand is the carrier's own exhibit, supplied from its evidence.
  The steps are therefore supplied-demand lifts in the sense of ruling D4.

### Embargo

The list gains two items, and nothing on it is computed.

- `history_symmetry` is rung five's question (rung four's named next rung,
  Y-3): whether the size of the automorphism group under the implemented
  isomorphism is preserved or monotone along the events of a history, and at
  which event kinds it moves.
- `element_count_succession` is rung six's question (Z-4): whether the element
  count settles the census row for succession.

Round P3 adds two more:

- `duration_under_changing` is rung seven's question, rung six's named next
  leftover (W-1): anything about round counts, or how long a history lasts
  while its state changes, on the sealed carrier.
- `element_count_across_isomorphism` is rung seven's named next rung (Z-1),
  reserved for the derivation while the rung sequence is paused: whether two
  isomorphic regimes always have the same element count.

The pinned digest is now `15809691…`. The gate's embargo step also refuses
any engine source that names the sealed `automorphisms` or `pair_orbits`. The
ladder retains its ties as forks and computes no quotient.

## Round P3: band 000-021 (E3) and the Q-levels

### E3: six new levels through the engine

Each level is posed in native words in `payload/<id>/` and hosted as a finite
structure of at most 12 elements at the base stage. No level declares a
witness form, so each fixture's class of responses is the empty response
alone, searched and certified like any other. Relational clauses are decided
by derivability over the hosted claim; value clauses over exact rationals
outside the grammar, and, where a Lean module is listed, re-decided by the
kernel with `ExactRat` (`tools/lean_gen.py` now renders any level's own
certificate module).

| level | challenge | native clauses | Lean module | clauses the adapter claims | notes |
| --- | --- | --- | --- | --- | --- |
| 007 | `cycle_words` | 16 of 19 | none (COMPUTED) | C1-C5 | words of length two over a table of allowed steps; turn-closed rings, least lead, least span |
| 008 | `flow_certificate` | 13 of 17 | `FlowCertificate` | C1-C7 | zero gap, feasibility and price; both round trips of free pointing and forgetting; the unit's compatibility square |
| 010 | `scope_fence` | 9 of 10 | `ScopeFence` | C1-C3 | the reading and the scope are fixed by the evidence type, never by the claim |
| 018 | `three_way_split` | 9 of 12 | `ThreeWaySplit` | C1-C4 | the split is carried as values on elements, and both recomputed parts come from the complex's own incidence |
| 019 | `table_polynomial` | 8 of 11 | `TablePolynomial` | C1-C4 | the kernel recomputes `det(xI - A)` by Faddeev-LeVerrier; `809/500` leaves `-19/250000` |
| 021 | `loop_products` | 11 of 15 | `LoopProducts` | C1-C4 | the bracket of two quarter turns has signed count zero and is still open |

The arity-3 kind lift (W2-C02's E1) was not built: no level of this band
needs a witness at all, and the one ternary witness in sight, the running
product of a loop, needs more items than the three the embargo allows, so it
is computed, not searched.

### The Q-levels

`bindings/qlevels.json` registers the band's Q-levels: W2-C03's quick-win set
(a gated sealed witness exists), less the levels the engine answers itself.
Each is a replay of sealed evidence (carrier part `repo_content`, key
`19L57G1`). The bootstrap checks every cited sealed theorem against the
pinned axiom report and writes `bindings/generated/qlevels.json`.

| level | native name | status | what stands in the way |
| --- | --- | --- | --- |
| 011 | `PositionedJoin` | BOUND (`positioned_join`) | re-runs the sealed two-rule rewrite system and finds its first peak (`hha`); C2 is not claimed, since the confluent system's arms are never both empty |
| 016 | `CoherentStageChain` | BOUND (`stage_chain`) | replays the possession reading's genesis history as a chain of presentations; C2 is not claimed, since the sealed stages state no equation |
| 012 | `ReplayedEvent` | BLOCKED | growth (the branch tree) and `duration_under_changing` |
| 020 | `StalledCycle` | BLOCKED | removal (a revisit needs it) and `duration_under_changing` |
| 006, 009, 013, 014, 015, 017 | `ConservativeEmbedding`, `CarriedReversal`, `RouteReplay`, `BoundedMask`, `HostBoundVerdict`, `TaggedDigest` | BOUND since the second P3 pull request | see below |

### Replayed

`tools/reach_replay.py` replayed all fourteen records at harness commit
`c3e070dc`; every one is `EVIDENCE_ONLY` at R1. The receiving side computed:

| carrier key | levels at R1 | C | A | D |
| --- | --- | --- | --- | --- |
| `19L57G1` (replayed sealed evidence) | 000 (apparatus), 001, 011, 016 | 3 | 1 | 0 |
| `19L57G1+harness` (harness computation) | 002-005, 007, 008, 010, 018, 019, 021 | 10 | 0 | 0 |

The keys are never summed. E is LEAN at 005, 008, 010, 018, 019 and 021.
Merge with a merge commit: the stored receipts pin harness commit `c3e070dc`.

After the second P3 pull request, all twenty records are replayed at harness
commit `1040223c`:

| carrier key | levels at R1 | C | A | D |
| --- | --- | --- | --- | --- |
| `19L57G1` | 000 (apparatus), 001, 006, 009, 011, 013-017 | 9 | 1 | 0 |
| `19L57G1+harness` | 002-005, 007, 008, 010, 018, 019, 021 | 10 | 0 | 0 |

E is now LEAN at 007 as well.

### Guards added this round

- `outward/reach.py` cites each harness-built theorem from its own
  certificate module, and carries criterion 3's compatibility squares when an
  adapter states them (008 and 016 name structure maps).
- `gate.py`'s freeze step compares an imported round's files as its source
  holds them; it had failed on any payload added after E0.
- The embargo list gains `duration_under_changing` (rung seven's question)
  and `element_count_across_isomorphism` (rung seven's named next rung).
- Injections I37 to I50 prove the new guards (`INJECTIONS.md`); the
  predictions frozen in `predictions/FROZEN_P3.json` are scored in
  `predictions/P3_scoring.md`.

### The rest of the Q-levels (second P3 pull request)

The six Q-levels that were waiting for a replay now have one. Each states its
sealed witness in its stage checker's schema, re-run from the pinned clone
through the shared plumbing in `engine/replay.py`:

| level | challenge | sealed witness replayed | clauses claimed |
| --- | --- | --- | --- |
| 006 | `conservative_embedding` | the spine's validity discipline: sealed `min_responses` and `response_valid_naive` on a supplied three-datum fixture; stages as presentations with their inseparable pairs as equations | C1-C3 (the sealed stage states no arrow, so C4 and C5 are not claimed) |
| 009 | `carried_reversal` | the sealed transpose and collision on the two-point carrier; arrows are the closure of the symmetric datum | C1-C6 |
| 013 | `route_replay` | the sealed alternating boundary; the hollow triangle's boundary is the balanced witness (`d2_zero_unrestricted`) | C1-C6 |
| 014 | `bounded_mask` | the sealed truncated-search world: the obstruction claim over the whole response menu | C1-C4 |
| 015 | `host_bound_verdict` | the sealed tie counts (3 and 5) as a sum claim, accepted only through the host's verifier | C1-C4 |
| 017 | `tagged_digest` | the sealed compression instance: class counts before and after duplication, and signature words | C1-C3 |

**006's structure field.** W2-DA names `ProposalRecord`'s `retract_embed`, a
structure field. Its only instance with a reported theorem is `upProposal`,
whose embedding and retraction are the identity (the field holds by `rfl`).
It is also a growth proposal, which the embargo excludes. So it is not cited,
and 006 is replayed through the spine's validity discipline, which W2-DA also
names (cited: `Derivation.mark_progress`, `validResponse_ext`,
`validResponse_dropRules`).

**The C2 clauses of 011 and 016.**

- 016 C2 is now bitten. One stated equation in the middle stage, which the
  last stage does not keep, is refused. The replay gains the matching clause,
  `keeps_equations`.
- 011 C2 is vacuous on this carrier. It fires only when both arms are empty,
  and a single edit empties at most one arm. No peak of the stated sealed
  steps has an empty arm: the replay searches the sealed battery up to
  length 4 and records none.

**007's kernel module.** `CycleWords` re-decides `one_class`, `span_least`
and `lead_least` on every evaluated fixture. Two of its certificates depend on
no axiom at all. The restated axiom report used to write such a theorem with
a placeholder axiom, which the receiving side refused (`RR-AXIOM`); it is now
written as the receiving side parses it (I58).

Injections I51-I58 prove the new guards (`INJECTIONS.md`).

## Round P4: band 022-046, the Q-levels first

The round plan names seven Q-levels for this band: 022, 023, 029, 032, 041,
043 and 044. Each is registered in `bindings/qlevels.json` with the sealed
witness W2-DB names. Three replay that witness in the stage checker's schema;
four are blocked, each by name. 027 is registered too, for its finding.

| level | status | sealed witness replayed, or what blocks it |
| --- | --- | --- |
| 029 | BOUND (`boundary_chain`) | the sealed alternating boundary on the filled tetrahedron with a tail side; the sealed signless boundary is the refused case (C1-C4) |
| 032 | BOUND (`observed_blocks`) | the sealed observation read as a coarse map: the ledger is the collapsed pairs, and the protected pairs are the requirements (C1-C4) |
| 043 | BOUND (`granted_steps`) | the sealed represented step: each event's effect row is computed by withdrawing one capability at a time (C1-C3) |
| 022 | BLOCKED (`no_sealed_replay`) | the heterogeneous family in `PresentationNaturality` is sealed Lean with nothing to replay it, and it declares no identity or composite |
| 023 | BLOCKED (`witness_not_sealed`) | every named gluing witness is a research tree |
| 041 | BLOCKED (`witness_not_sealed`) | `dupState_unreachable` is in `conservation_ladder`, a research tree; the sealed grammar has no use-count discipline |
| 044 | BLOCKED (`witness_not_sealed`) | the contract witness is in `conservation_ladder`; the sealed existential witness has no image in interval triples |
| 027 | BLOCKED (`witness_not_sealed`) | NS-5 is in `native_structure`, a research tree. Finding: `g013_trace_calculus` inside 19L57G1 proves its interchange coherence by `rfl`, which is this level's own negative instance. It is recorded, not changed. |

The registry now names two blockers besides the embargo items:
`witness_not_sealed` and `no_sealed_replay`. Any other blocker is refused
(`UNKNOWN_BLOCKER`, I62).

Two harness levels, the band's cheapest, go under `19L57G1+harness`:

| level | challenge | native clauses | Lean module | clauses claimed |
| --- | --- | --- | --- | --- |
| 035 | `step_weights` | 3 of 5 | `StepWeights` | C1-C2 |
| 036 | `weighted_update` | 7 of 11 | `WeightedUpdate` | C1-C4 |

All twenty-five records are replayed at R1, at harness commit `c9f735dd`:

| carrier key | C | C in 000-021 | C in 022-046 | A | D |
| --- | --- | --- | --- | --- | --- |
| `19L57G1` | 12 | 9 | 3 | 1 | 0 |
| `19L57G1+harness` | 12 | 10 | 2 | 0 | 0 |

The keys are never summed. Injections I59-I64 prove this round's guards;
the predictions frozen in `predictions/FROZEN_P4.json` are scored in
`predictions/P4_scoring.md` (7 hits, no miss).

## Round P5: band 047-073, and more of band 022-046

The round plan's stream E for this band (row P5) and the band work orders
(W2-DB, W2-DC) name each level's cheapest engine route. Twenty-seven harness
levels were built, cheapest first, and none is blocked by an embargo item.
Predictions were frozen by digest first (`predictions/FROZEN_P5.json`) and are
scored in `predictions/P5_scoring.md`.

### The harness levels

Each is posed in native words in `payload/<id>/`, hosted within the 12-element
cap at the base stage, searched over the declared class (the empty response
alone: no level declares a witness form), certified by replay, and replayed at
R1 by its checker of record through `bindings/adapters/L0NN.py`. Every value
clause is re-decided by the kernel in the level's own module, with `ExactRat`
where values are rationals or pairs of rationals, and over `Nat`, `Int` and
`Bool` otherwise; every theorem depends on at most `propext` and `Quot.sound`.

| level | challenge | native clauses | Lean module | clauses claimed | not claimed, and why |
| --- | --- | --- | --- | --- | --- |
| 033 | `scale_steps` | 12 of 15 | `ScaleSteps` | C1-C4 | - |
| 038 | `same_background` | 10 of 13 | `SameBackground` | C1-C3 | - |
| 039 | `joint_payoffs` | 6 of 7 | `JointPayoffs` | C1-C3 | - |
| 040 | `stable_profiles` | 6 of 7 | `StableProfiles` | C1-C3 | - |
| 042 | `dual_endpoints` | 7 of 11 | `DualEndpoints` | C1-C4 | - |
| 044 | `witnessed_triples` | 11 of 14 | `WitnessedTriples` | C1-C4 | - |
| 047 | `mirror_pairs` | 12 of 15 | `MirrorPairs` | C2-C4 | C1: a decimal never enters; exact intake refuses it |
| 048 | `unit_rows` | 3 of 4 | `UnitRows` | C1-C2 | - |
| 049 | `named_frames` | 8 of 11 | `NamedFrames` | C1, C3-C5 | C2: the engine hosts one carrier and states no tag |
| 050 | `square_one` | 6 of 12 | `SquareOne` | C1-C6 | - |
| 051 | `split_weights` | 6 of 10 | `SplitWeights` | C1-C4 | - |
| 052 | `ordered_splits` | 11 of 16 | `OrderedSplits` | C1-C6 | - |
| 054 | `joint_rank` | 5 of 7 | `JointRank` | C1-C3 | - |
| 055 | `far_blind` | 8 of 11 | `FarBlind` | C1-C3 | - |
| 056 | `side_reduction` | 4 of 8 | `SideReduction` | C1-C4 | - |
| 057 | `size_keeping` | 7 of 9 | `SizeKeeping` | C1-C2 | - |
| 058 | `overlap_choices` | 4 of 6 | `OverlapChoices` | C1-C3 | - |
| 059 | `two_party_bound` | 9 of 14 | `TwoPartyBound` | C1-C5 | - |
| 060 | `commuting_checks` | 5 of 8 | `CommutingChecks` | C2-C4 | C1: a hosted word has one bit per site |
| 061 | `walk_transport` | 13 of 17 | `WalkTransport` | C1-C4 | - |
| 062 | `face_products` | 7 of 10 | `FaceProducts` | C2-C3 | C1: a hosted step reads a hosted link |
| 065 | `step_squares` | 20 of 20 | none (type D) | C1-C5 | - |
| 066 | `signed_totals` | 6 of 10 | `SignedTotals` | C1-C4 | - |
| 067 | `answer_keeping` | 8 of 11 | `AnswerKeeping` | C1-C4 | - |
| 068 | `outward_bounds` | 4 of 8 | `OutwardBounds` | C2-C5 | C1: a decimal, or a missing bound, is refused before the checker's schema |
| 070 | `table_roots` | 6 of 8 | `TableRoots` | C1-C3 | - |
| 072 | `rim_cochains` | 4 of 9 | `RimCochains` | C1, C2, C4, C5 | C3: every one-entry edit breaks the composite first; a near-miss shows the refusal |

"Native clauses" are the clauses carried by derivability (the probe changes
their verdict), out of all the level's clauses. Where a checker clause is not
claimed, the engine cannot state the defect it refuses, or no single edit of
the positive reaches it; the loss ledger books each.

**065 is answered natively.** All twenty of `step_squares`' clauses are
carried by derivability (the squares are closures over the map, and the round
trips too), so its computed answer type is D, not M, and it has no value clause
for the kernel to re-decide: its E stays COMPUTED.

**Shared helpers.** `payload/shared.py` holds what the new specs share: rows
of a relation, exact pairs and tables of pairs, and the text of a certificate
module. Two specs import another level's spec (`table_roots` reuses
`table_polynomial`'s polynomial clauses and Lean definitions;
`stable_profiles` reuses `joint_payoffs`' payoff reading).

### Guards added this round

- **Named sources.** A harness level's record named only its own payload
  folder, the engine and the Lean report; the P5 specs import
  `payload/shared.py`, which it did not name. `harness_sources` now adds every
  payload module a spec imports, and a test reads each spec's imports by its
  syntax tree (`UNNAMED_SOURCE`; I92).
- **The carrier part of a Q-registration.** Binding 044 through the engine made
  the bootstrap refuse with `STALE_REGISTRATION`, as predicted (G1): the
  registry read any adapter as a replay of sealed evidence. A registration now
  speaks for the replayed-evidence key only; a level is `BOUND` there when its
  binding's kernel is `replay`, and a harness record at a blocked level keeps
  the blocker and is named in `harness_record` (I93).
- **Ruling D4.** #75 registered the checkers of record for 012, 017 and
  082-100 as apparatus. The replayed record at 017 was framed as a supplied
  challenge and counted in C. Its checker decides digest binding, tag dispatch
  and decode round trips: the carrier's mechanics, with the sealed class counts
  and words riding inside as payload. So the record witnesses apparatus: a
  record at a level whose checker of record is registered as apparatus is now
  framed `AP`, and counts in A, never in C (`D4_FRAMING`; I94).

Injections I65-I91 each weaken one new level's decisive clause to the defect
it refuses; I92-I94 prove the three guards (`INJECTIONS.md`).

### The Q-levels of band 047-073

W2-DC names no sealed witness for any level of the band. Every witness it
names for its quick wins is a research tree (the p208 and p209 trees,
`natural_sections`, `convention_price`, `native_bridge`, `domain_adapters`,
`coherent_process_limits`, `native_structure`), so no level of the band
replays sealed evidence under `19L57G1`. The quick wins (055, 058-062, 065,
066, 071 and 072) are registered blocked by `witness_not_sealed`; nine of them
have a harness record under `19L57G1+harness`, which the registration names.

### Replayed

All fifty-one records are replayed at R1, at harness commit `58f98014`
(`EVIDENCE_ONLY` each):

| carrier key | C | C in 000-021 | C in 022-046 | C in 047-073 | A | D |
| --- | --- | --- | --- | --- | --- | --- |
| `19L57G1` | 11 | 8 | 3 | 0 | 2 | 0 |
| `19L57G1+harness` | 39 | 10 | 8 | 21 | 0 | 0 |

The keys are never summed. `19L57G1` falls from 12 to 11 because 017 is now
apparatus (A rises from 1 to 2: 000 and 017). E is LEAN at every new level but
065. Merge with a merge commit: the stored receipts pin harness commit
`58f98014`.

### Left open

Not attempted this round, with what stands in the way:

| level | what stands in the way |
| --- | --- |
| 022, 023, 024, 025, 026, 027, 028 | not reached this round (W2-DB rates each M, 3 agent-days); 026 and 027 fit the cap only as small instances |
| 030, 031, 064 | the instance W2-DB and W2-DC describe (a filtered complex with its pages; a pure 2-complex with test cocycles and maps; the solid cell with edge transports and four faces) does not fit the 12-element carrier cap of the base stage |
| 034, 037, 041 | not reached this round |
| 045, 046 | the checker binds SHA-256 digests (of the axioms; of evaluators); the engine hosts no digest value, so the digest clauses would be the adapter's, not the engine's |
| 053 | the engine's joined table is keyed by the pair of slots, so slot order never travels; the checker's reading and swap fields (C2, C3) would have to be invented by the adapter |
| 063, 069, 071, 073 | the all-cases claims need a certificate the kernel can re-decide (hinge angles from the exact cosine table; a Sturm chain; a Cauchy root bound; an explicit refinement depth); not built this round |

## Round P6: capabilities, the rest of 022-073, band 074-081, and apparatus witnesses

Three engine capabilities unblocked the levels P5 left open for want of them.
Thirty-two harness levels were then built, cheapest first: the nine the
capabilities unblocked, five more of 022-046, all eight of band 074-081 and
ten object-language witnesses at apparatus levels of 082-100. None is
blocked by an embargo item. Predictions were frozen by digest first
(`predictions/FROZEN_P6.json`) and are scored in `predictions/P6_scoring.md`.

### Capabilities

- **Carrier cap 18.** `MAX_CARRIER` rises from 12 to 18, the smallest cap that
  hosts the three levels the cap blocked: 031's six-vertex projective plane
  needs 18 elements (6 vertices, 10 triangles, a test cochain and a self-map),
  064's cell 15, and 030's filtered triangle fits in 10. The search stays
  bounded: `decide_k` computes the class size from the declared formula first,
  and a class beyond the evaluation budget is declared `BUDGET_UNKNOWN`
  (`class_over_budget`) without being enumerated. An enumeration that ever
  exceeds the declared count is refused (`RR-EXHAUSTION`). (I95, I96.)
- **Hosted digests.** A structure may carry exact 32-byte SHA-256 values
  (`digests`, written `sha256:<hex>`), one per element, kept through descent
  and mutation. `engine/exact/digest.py` recomputes SHA-256 over a declared
  canonical JSON serialization. Digest clauses are decided in Python and stay
  COMPUTED: there is no SHA-256 in the kernel. 045 recomputes the axiom list's
  digest; 046 compares confirmer and interpreter digests by bytes; 077 and 083
  seal states and records by content. (I97.)
- **Induction in Lean.** `ExactRat/Poly.lean` proves, by induction over the
  forward differences of a rational polynomial at the naturals, that a
  polynomial whose differences all start nonnegative at `n0` is nonnegative at
  every `n >= n0` (`nonneg_from`; strict: `pos_from`), and a halving bound for
  all depths (`halving_bound`, through `eval_reverse`). Only `propext` and
  `Quot.sound`. 071's two inequalities hold for every `n >= n0` and 073's
  estimate for every depth `k >= k0` by these theorems; failing claims are
  refuted at an exact witness. 063 and 069 are finite families (every hinge of
  a closed surface; every member of a Sturm chain at two points) decided by
  the kernel. (I98.)

### The harness levels

Each is posed in native words in `payload/<id>/`, hosted within the 18-element
cap, searched over the declared class (the empty response alone), certified by
replay, and replayed at R1 by its checker of record through
`bindings/adapters/L0NN.py`. Every checker clause is claimed at every level
below, and each is bitten by a one-edit mutation. E is the evidence grade the
replay assigns.

| level | challenge | native clauses | Lean module | E | note |
| --- | --- | --- | --- | --- | --- |
| 022 | `reindexed_fibres` | 9 of 17 | `ReindexedFibres` | LEAN | a term reindexed along an arrow lands in the wrong fibre |
| 023 | `glued_patches` | 10 of 10 | none | COMPUTED | two patches disagree on their overlap; answered natively (D) |
| 027 | `associator_tables` | 3 of 6 | `AssociatorTables` | LEAN | a table that breaks the pentagon; its class is decided exactly |
| 030 | `filtered_pages` | 4 of 11 | `FilteredPages` | LEAN | pages of a filtered complex; a page lists a cell an earlier step removed |
| 031 | `class_operations` | 5 of 11 | `ClassOperations` | LEAN | the cup square on the six-vertex projective plane (cap 18) |
| 037 | `forced_differences` | 5 of 10 | `ForcedDifferences` | LEAN | an observed correlation relabelled as the forced effect |
| 041 | `use_once_terms` | 5 of 12 | `UseOnceTerms` | LEAN | a use-once name used twice |
| 045 | `bound_axioms` | 6 of 14 | `BoundAxioms` | LEAN | axioms bound by a recomputed digest |
| 046 | `confirmed_runs` | 12 of 16 | `ConfirmedRuns` | LEAN | a run confirmed only by its own interpreter's digest |
| 063 | `hinge_deficits` | 5 of 12 | `HingeDeficits` | LEAN | every hinge of a closed surface; total deficit 2 |
| 064 | `closed_faces` | 6 of 13 | `ClosedFaces` | LEAN | face values of a solid cell (15 elements) whose ordered product does not close |
| 069 | `isolated_roots` | 3 of 8 | `IsolatedRoots` | LEAN | a Sturm chain; an interval holding two roots is not isolating |
| 071 | `rated_limits` | 4 of 12 | `RatedLimits` | LEAN | a rate bound for every n, by induction |
| 073 | `refined_sums` | 3 of 8 | `RefinedSums` | LEAN | a refinement estimate at every depth, by induction |
| 074 | `typed_queries` | 8 of 12 | none | COMPUTED | an atom binding a column its table does not have |
| 075 | `patched_views` | 9 of 18 | `PatchedViews` | LEAN | a patched view row that is not in the new table |
| 076 | `signed_cells` | 5 of 8 | `SignedCells` | LEAN | an edge ending at a cell no one declared a vertex |
| 077 | `serial_receipts` | 6 of 15 | none | COMPUTED | a write over an unfinished write; states sealed by digest |
| 078 | `ordered_log` | 4 of 8 | `OrderedLog` | LEAN | a parent that is not earlier, a clock that does not rise |
| 079 | `merge_tables` | 6 of 6 | none | COMPUTED | a merge that is not idempotent; answered natively (D) |
| 080 | `exact_grants` | 10 of 10 | none | COMPUTED | a grant not issued by the authority; answered natively (D) |
| 081 | `budgeted_releases` | 4 of 10 | `BudgetedReleases` | LEAN | a release beyond the remaining budget |

023, 079 and 080 are answered natively: every clause is carried by
derivability, so their computed answer type is D and their E stays COMPUTED.

### Apparatus levels: object-language witnesses

Ruling D4 classes the checkers of record for 082-100 as apparatus. Each of the
ten below hosts a finite instance of the level's obligation in the engine's own
terms and refuses the level's negative instance there. W2-DD (section 2.4)
calls the versions of 080-088 real object-language versions, and those of
095-099 re-readings of a procedure, whose vocabulary is supplied and
classified in the restatement. Each record is framed `AP` and counts in A
under `19L57G1+harness`, never in C.

| level | challenge | native clauses | E | the witness |
| --- | --- | --- | --- | --- |
| 083 | `lineage_pins` | 4 of 10 | COMPUTED | a lineage graph; a missing source refused natively; seals and pins by digest |
| 085 | `narrowing_handoffs` | 4 of 10 | COMPUTED | handoffs replayed in order; a rooted handoff that widens its permissions |
| 087 | `mutant_challenges` | 1 of 7 | COMPUTED | fixtures and mutants as hosted claims; a surviving mutant |
| 088 | `limited_runs` | 2 of 9 | COMPUTED | a program with its terminals; running out of fuel is never a halt |
| 089 | `composed_errors` | 3 of 9 | COMPUTED | a weighted error table; correlated sources assumed independent |
| 092 | `resolution_claims` | 4 of 11 | COMPUTED | a resolution proof replayed step by step; resolvents recomputed |
| 094 | `wired_handshakes` | 7 of 10 | COMPUTED | ports and wires; the direction and type laws carried by derivability |
| 098 | `differential_pairs` | 7 of 12 | COMPUTED | two rounding functions on hosted cases; a silent merge of a disagreement |
| 099 | `seeded_shrinks` | 1 of 8 | COMPUTED | a seeded failure and its shrink trace, replayed |
| 100 | `scoped_release` | 4 of 9 | COMPUTED | a release whose self-certification is a forbidden row |

### Guards added this round

Injections I95-I98 prove the capabilities (the cap, the declared class count,
descent of digests, the induction certificate). I99-I130 each weaken one new
level's decisive clause to the defect it refuses; the level's refused fixture,
or a near-miss, is then accepted or refused for another reason
(`INJECTIONS.md`).

The full panel found I1 silent once the declared-count guard landed: a
claim-overwrite repair was refused as `RR-EXHAUSTION` before the claims check
could name it. The claims check now runs first on every enumerated delta, and
I1 fires `CLAIM_FROZEN` again. All 130 injections fire and recover.

### Replayed

All eighty-four records are replayed at R1, at harness commit `b51f9ea1`
(`EVIDENCE_ONLY` each):

| carrier key | C | C in 000-021 | C in 022-046 | C in 047-073 | C in 074-081 | A | D |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `19L57G1` | 11 | 8 | 3 | 0 | 0 | 2 | 0 |
| `19L57G1+harness` | 61 | 10 | 17 | 26 | 8 | 10 | 0 |

The keys are never summed. `19L57G1` is unchanged: no sealed witness was
added. The harness C rises from 39 by the twenty-two object-language levels,
and its A from 0 by the ten apparatus witnesses. E is LEAN at every new
object-language level but 023, 074, 077, 079 and 080 (no value clause for the
kernel, or only digest and schedule clauses), and COMPUTED at every apparatus
level. The records of the fifty-one earlier levels were rewritten, because
they name the engine sources that changed; no verdict, fixture code or grade
moved. Merge with a merge commit: the stored receipts pin harness commit
`b51f9ea1`.

### Left open

Not attempted this round, with what stands in the way:

| level | what stands in the way |
| --- | --- |
| 024, 025, 026, 028, 034, 053 | not reached this round; 053's slot order still does not travel (P5) |
| 082, 084, 086, 090, 091, 093, 095, 096, 097 | not reached this round (apparatus by ruling D4; any record there would count in A) |

## Round P7A: research-tree witnesses (the author's ruling of 2026-09-25)

The author ruled that a witness from a 19L57G1 research tree, read only
through the vendored pinned clone, is admissible evidence for a replay under
the `19L57G1` key (`RULINGS.md`, `tree-witness`). The ruling answered the
fourteen levels then blocked by `witness_not_sealed` (it says "all 13"; the
list has fourteen, and the discrepancy is recorded there). Predictions were
frozen by digest first (`predictions/FROZEN_P7A.json`) and are scored in
`predictions/P7A_scoring.md`. 19L57G1 is repinned to `77ad2a78`, rung
nine's merge, through `35e680ec` and `ff584d44` (rung eight); no sealed path
moved, and no research-tree file the engine reads (only `CLAUDE.md`,
`research/second*`, other trees' READMEs, manifests and verifiers, `ci`,
`docs`, `.claude`, `.github` and one test).

### How a research-tree witness is recorded

- **A second record at the level.** Each admitted level already had a
  harness record (tag `L`, key `19L57G1+harness`). Its research-tree replay is
  a second record (tag `T`, key `19L57G1`): `bindings/T0NN.json` (with
  `custody` and `trees`), `bindings/adapters/T0NN.py`, and a replay spec in
  `payload/<id>/` that reads the tree through `engine.replay.tree_module` and
  `tree_json` (read only, no bytecode written into the clone; the second
  derivation's trees are refused). `tools/bind.py`'s `records()` lists both
  tags; a tree replay at a level that already replays sealed evidence is
  refused, so the two records never share a key.
- **The provenance mark.** The receiving side's grading has no mark that
  tells a research-tree witness from a sealed one (its carrier parts are
  `repo_content` and `harness_computation`; P is read from the framing). So
  every tree record books it in its loss ledger, `source.witness_custody`
  (WEAKENED: research-tree evidence, outside the seal and its gates), and in
  its non-claims. A tree record without the row is refused
  (`UNBOOKED_CUSTODY`).
- **The registry.** A registration's `witness_custody` is `sealed` or
  `research_tree`; a research-tree registration names the tree files its
  replay reads, or the files examined when it is blocked (`tree_sources`, each
  digest checked at the pin), and names nothing sealed (`MIXED_CUSTODY`).
  `witness_not_sealed` is retired: a registration that still lists it is
  refused (`RULED_ADMISSIBLE`). A tree witness outside its checker's declared
  input class is blocked by name, `tree_witness_off_class`.
- **Findings.** A registered finding is booked in the loss ledger of any
  record at its level (`source.finding.N`).

### The fourteen levels

| level | outcome | tree | the witness, or what blocks it |
| --- | --- | --- | --- |
| 023 | replayed (`observer_glue`) | `g014_observer_descent` | the tree's compatible cover (three observers over four loci), glued by the tree's own gluing; the refused case is the tree's own perturbation at a shared locus |
| 058 | replayed (`shared_labels`) | `natural_sections` | the tree's `chain_P4_r0_repres` instance and the section the tree decides exists; the named p208b valuation obstruction has no positive family and a rule outside the checker's two, so the native analogue the registry names is used; the own negative is the tree's `square_2x2_r0` |
| 059 | replayed (`row_margin`) | `p208b_contextuality_nonlocality` | the tree's four rational unit rows, total 14/5 over the local bound 2 (from the tree's sixteen strategies), margin 4/5 |
| 060 | replayed (`site_checks`) | `p209c_stabilizer_codes` | the tree's three-site code, two checks, three single-site errors with the tree's readings; the own negative is the tree's non-commuting pair |
| 061 | replayed (`walk_relabels`) | `convention_price`, `sign_slice` | a census member with six labels and non-commuting transports, relabelled by the tree's own relabelling; the own negative is the tree's recorded first witness, which moves one end only |
| 062 | replayed (`face_walk_products`) | `natural_sections` | the tree's chord square at its separating assignment, and its recorded closed walk whose product depends on order; the own negative drops the chord step |
| 065 | replayed (`register_squares`) | `native_bridge` | the tree's toggle carried into the passage by its budget register (`budget_sim`, checked against the committed receipt), claimed one way (a simulation), as the tree's own refutation requires |
| 066 | replayed (`pairing_certificates`) | `natural_sections`, `fresh_characters` | the tree's pinned sign-repair witness with its pairing; the own negative is the census row the tree's receipt records as its smallest refusal |
| 072 | replayed (`chord_square_rim`) | `natural_sections` | the tree's chord square as a two-complex: its oriented edges, two triangular faces, face sums as incidence rows, and the rim as the support of its outer-walk sum; NS-6 (squares, no rim) is not used |
| 027 | blocked, `tree_witness_off_class` | `native_structure` | NS-5 is a Lean cell calculus of swap positions; no tree holds a skeletal associator table over cyclic groups. The g013 finding stays registered for any future record |
| 041 | blocked, `tree_witness_off_class` | `conservation_ladder`, `internal_syntax_logic` | `dupState_unreachable` is a Lean reachability fact, not a typed derivation tree; the one linear calculus in Python computes its contexts from the leaves and contracts any formula |
| 044 | blocked, `tree_witness_off_class` | `conservation_ladder` | the contract is about charge along histories in the plane, not interval triples of one variable under an increment |
| 055 | blocked, `tree_witness_off_class` | `p208b_contextuality_nonlocality` | the tree holds joint weights built from four entries, but no joined row over Q(i) and no splits from which the checker recomputes them |
| 071 | blocked, `tree_witness_off_class` | `coherent_process_limits`, `limit_and_observer` | the only convergent sequence is a periodic floor count, zeros(L)/L, which no ratio of polynomials equals from any start; it is also a visit count along a changing run, next to the embargo item `duration_under_changing`, and nothing about it is computed |

Every replay decides its clauses by the tree's own code where the tree has
code for them, and books in its adapter's loss rows what the replay computes
beyond the tree (derived fields the checker needs) and what it drops (the
tree's Lean, which no record cites; the named witness when an analogue is
used). No sealed Lean is cited, so E is COMPUTED at every tree record.

### Replayed

All ninety-three records are replayed at R1, at harness commit `b85800a1`
(`EVIDENCE_ONLY` each):

| carrier key | C | C in 000-021 | C in 022-046 | C in 047-073 | C in 074-100 | A | D |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `19L57G1` | 20 | 8 | 4 | 8 | 0 | 2 | 0 |
| `19L57G1+harness` | 61 | 10 | 17 | 26 | 8 | 10 | 0 |

The keys are never summed. `19L57G1` rises from 11 by the nine research-tree
replays (023 in band 022-046; 058-062, 065, 066 and 072 in band 047-073),
each E = COMPUTED, P = supplied, B = named, with its custody booked. The
harness key is unchanged. Merge with a merge commit: the stored receipts pin
harness commit `b85800a1`. (Pull request #87 merged the round's engine at
`515c6131` without its receipts; the replay was redone on `main` after the
consolidation, at `b85800a1`.)

### Guards added this round

- `engine/replay.py`: `tree_rel`, `tree_module`, `tree_json`; `result(...,
  trees=...)` refuses sealed sources or sealed Lean in a tree replay
  (`RR-TREE`).
- `outward/reach.py`: `custody_checked` (`UNBOOKED_CUSTODY`); records, stubs,
  positives and adapters are named by tag.
- `outward/qlevels.py`: `RULED_ADMISSIBLE`, `UNKNOWN_CUSTODY`, `MIXED_CUSTODY`.
- The embargo list gains two items, pinned by digest (`db0305cb`):
  `shortest_class_matched_witnesses`, rung eight's leftover candidate Y-1
  (the shortest class-matched witnesses over stakes, from the second
  derivation's index tree), and `census_undecided_rows_x6`, rung nine's X-6
  (the undecided rows of the second derivation's census: two-ness,
  observational classes, adjacency, reach, branching and exhaustion, for its
  regimes, histories and stakes). Nothing about either is computed; no level
  of this round needs one.
- Injections I131-I144 (`INJECTIONS.md`): the custody row dropped, the
  retired blocker re-listed, a sealed source read by a tree replay, each new
  embargo item dropped, and each tree replay's decisive clause weakened to the
  defect its level refuses.

### Left open

| level | what stands in the way |
| --- | --- |
| 027, 041, 044, 055, 071 | `tree_witness_off_class`: the research-tree witness is not in the checker's declared input class (see the table above); each keeps its harness record |
| 012, 020 | embargo items (growth, removal, `duration_under_changing`), unchanged |
| 022 | `no_sealed_replay`, unchanged |
| 024, 025, 026, 028, 034, 053, 082, 084, 086, 090, 091, 093, 095, 096, 097 | not attempted in round P7A; built in round P7B below |

## Round P7B: the fifteen unattempted levels

The fifteen levels P6 left unattempted (024, 025, 026, 028, 034, 053, and the
apparatus levels 082, 084, 086, 090, 091, 093, 095, 096, 097) are built as
harness levels. Predictions were frozen by digest first
(`predictions/FROZEN_P7B.json`) and are scored in
`predictions/P7B_scoring.md`. None is blocked by an embargo item (including
the two added in round P7A), and none needs a carrier above 18 elements.

### Capabilities

- **Hosted texts.** An element may carry a text: printable ASCII of at most
  512 characters (`texts`, written `[element, "text"]`), one value kind per
  element, kept byte for byte through intake, the draft form, hosting and
  descent, and read only by decoded clauses, never by the grammar. Nine of
  the fifteen levels host names, contents or sources this way (053, 082, 084,
  086, 090, 091, 095, 096, 097). (I145.)
- **The textbook signature check.** `engine/exact/digest.signature_verifies`
  checks a signature over SHA-256 under a key `(n, e)`: `0 < s < n` and
  `s^e mod n` is the message's digest read as a natural, mod `n`. It only
  verifies. 082's positive was signed at authoring time with toy keys the
  receiving side publishes beside its checkers (`targets/fixtures.py`), and
  its restatement says so; a verification says nothing about
  unforgeability. (I146.)

Both stay COMPUTED: neither reaches the kernel.

### The harness levels

Each is posed in native words in `payload/<id>/`, hosted within 18 elements,
searched over the declared class (the empty response alone), certified by
replay, and replayed at R1 by its checker of record through
`bindings/adapters/L0NN.py`. Every checker clause is claimed at every level,
each bitten by a one-edit mutation. No Lean module was added this round, so E
is COMPUTED at every new level.

| level | challenge | native clauses | framing | the witness |
| --- | --- | --- | --- | --- |
| 024 | `recomputed_labels` | 19 of 20 | SC | a family over a four-stage order in which one stage has two below it; labels are down-sets recomputed from the restrictions; a two-valued label for a middle subfamily breaks the pullback |
| 025 | `formal_inverses` | 20 of 20 | SC | a finite category (3 objects, 8 arrows, 19 composites), a weak class closed under composition, three roofs; a roof inverting an arrow outside the class; answered natively (D) |
| 026 | `coloured_slots` | 19 of 22 | SC | a two-colour operation table truncated at arity 3 with its full table of 64 substitutions; an output substituted into a slot of another colour |
| 028 | `both_round_trips` | 22 of 27 | SC | two rational complexes, maps both ways and both homotopies; a one-sided inverse (the target round trip fails) |
| 034 | `weight_slopes` | 12 of 17 | SC | three outcome polynomials in two parameters at (1/2, 1/3), the information matrix diag(4, 9/4) recomputed with exact derivatives; a matrix with a negative direction |
| 053 | `paired_frames` | 15 of 21 | SC | two factor rows over Q(i) joined with the second factor slowest through a hosted exchange table; see below |
| 082 | `signed_chains` | 12 of 26 | AP | a three-key chain under a root the engine pins itself, scopes as texts, the artifact's digest recomputed, every signature verified; a digest with no signature |
| 084 | `rerun_calls` | 5 of 16 | AP | four calls to the four pinned tools, each rerun by the engine and its result digest recomputed; a guessed result |
| 086 | `grounded_traces` | 5 of 13 | AP | events with parents and evidence, witnesses as texts with digests; acyclicity carried by derivability over a hosted descent order; a circular dependency |
| 090 | `covered_clauses` | 9 of 17 | AP | a 63-character source split by the checker's declared splitter and word list (supplied data), spans by digest, one link or exception each; a quantified clause missing |
| 091 | `renamed_formulas` | 14 of 30 | AP | a renaming translation of a prenex formula, both evaluated on all 530 structures of the fragment (domains of 1 to 3); a quantifier swap that disagrees on the fragment |
| 093 | `compiled_branches` | 6 of 21 | AP | a loop-free source and a compiled stack program run with fuel on inputs covering both arms; a compiled branch that changes the outcome |
| 095 | `counted_runs` | 6 of 15 | AP | the two pinned sorts rerun and recounted on one input, logs by digest, the environment as texts; a speedup on an estimated basis |
| 096 | `counted_trials` | 4 of 10 | AP | five items sealed by digest, four trials, k = 3 of n = 4, the Chebyshev interval [1/4, 1] at alpha 1/4; a point estimate with no count |
| 097 | `killed_mutants` | 3 of 15 | AP | a base list, the pinned invariants and operators applied by the engine, the kill matrix recomputed; a surviving mutant |

"Native clauses" are the clauses carried by derivability, out of all the
level's clauses. Each adapter books its conventions in its loss rows (names
by place, list order by hosted index, a missing count written as null, and at
095 the fixed prefix of the checker's implementation tag, which the hygiene
scan keeps out of the hosted text).

**053's slot order now travels.** P5 and P6 left 053 open because the joined
table was keyed by the pair of slots, so the checker's reading and exchange
fields would have been the adapter's invention. Now every slot and joined
place carries its index as a hosted natural, factor order is the hosted
relation `before`, the reading the hosted relation `slowest`, and the exchange
table the hosted relation `exchange` over places. The engine computes the
product first-factor-slowest, carries it through the hosted table and
compares it with the joined row read by index. The adapter only sorts by
hosted indices. An extra fixture (`scrambled`) moves every factor, slot and
place to another element position; it is still accepted, and its adapted
checker input is identical to the positive's.

### Guards added this round

Injections I145 and I146 prove the two capabilities (texts dropped in descent;
any signature in range verifying). I147-I161 weaken the decisive clause of
each new level to the defect it exists to refuse (`INJECTIONS.md`). I97's
anchor moved with the descent line, which now keeps texts too.

### Replayed

All one hundred and eight records are replayed at R1, at harness commit
`233c1bfc` (`EVIDENCE_ONLY` each):

| carrier key | C | C in 000-021 | C in 022-046 | C in 047-073 | C in 074-100 | A | D |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `19L57G1` | 20 | 8 | 4 | 8 | 0 | 2 | 0 |
| `19L57G1+harness` | 67 | 10 | 22 | 27 | 8 | 19 | 0 |

The keys are never summed. The harness C rises from 61 by the six
object-language levels, and its A from 10 by the nine apparatus witnesses.
`19L57G1` is unchanged. Merge with a merge commit: the stored receipts pin
harness commit `233c1bfc`.

### Left open

| level | what stands in the way |
| --- | --- |
| 027, 041, 044, 055, 071 | under `19L57G1`: `tree_witness_off_class` (round P7A); each keeps its harness record |
| 012, 020 | embargo items (growth, removal, `duration_under_changing`) |
| 022 | under `19L57G1`: `no_sealed_replay`; it keeps its harness record |
| the fifteen new levels | E = LEAN would need a certificate module each; none was built this round |
