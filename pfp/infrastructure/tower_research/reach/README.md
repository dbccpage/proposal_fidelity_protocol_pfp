# Reach ledger (receiving side)

**AuthorityEffect:** `None`. A row is evidence, never authorization. Nothing here
activates, promotes, or admits anything.

This directory holds the reach ledger that `research/mssn_sn_tower/_archive/source_inputs_2026_09_25/19L57G1_H3V7N5QF_direct/08_governance_and_framing.md` §4
specifies. Its code is in `omega_engine_pfp/infrastructure/tower_research/reach/`, following the
layout in W2-C05 §4.1.

## Today's numbers (computed, not typed)

| carrier | C(100) | D | D_native | A |
|---|---|---|---|---|
| 19L57G1 | 12 | 0 | 0 | 1 |
| 19L57G1+harness | 12 | 0 | 0 | 0 |
| H3V7N5QF | 0 | 0 | 0 | 0 |
| H3V7N5QF+harness | 0 | 0 | 0 | 0 |
| the_symbol_game (own rows, C = T less A) | 80 | 0 | 0 | 21 |

T(100) = 101: the target checkers of record for stages 0-21 (round P2),
22-46 (round P3), 47-73 (round P4) and 74-100 (round P5) are registered and
gated, so T(021) = 22, T(046) = 47, T(073) = 74 and T(100) = 101. Ruling D4
(2026-09-25, adopted) classes levels 012, 017 and 082-100 as apparatus: their
checkers are registered with `"provenance": "apparatus"`, count in T and in the
symbol game's A (21), and never in its C (80 = 20 + 25 + 27 + 8 by band). Each
of those levels still needs an object-language witness before it can count in
C. The table above repeats `derived/numbers.json`. That file is the source, and it is
regenerated from `ledger.jsonl` and `registry/checkers.json`. An absent row
means NONE.

The twenty-five 19L57G1 rows (levels 000-011, 013-019, 021, 029, 032, 035,
036 and 043) are the level engine's Mode E records, replayed by
`symbol-game level-engine reach replay` against the checkers of record. Their carrier commit is a harness commit of this repository, which
`carriers.json` declares as 19L57G1's `harness_host`: the receiving side's own
context resolves it after any clone of 19L57G1, and a 19L57G1 commit never
resolves here. Level 000 is apparatus (A), never C. Levels 000, 001, 006, 009, 011,
013-017, 029, 032 and 043 are the engine's replayed sealed evidence
(`repo_content`); the other twelve are harness computation
(`19L57G1+harness`). Levels 012 and 020 are blocked by the embargo; 022,
023, 027, 041 and 044 are blocked because their named witness is not sealed
or has nothing to replay it (`omega_engine_pfp/infrastructure/tower_research/level_engine/bindings/qlevels.json`). C is counted per key and never
summed.

## Files

| path | what | written by |
|---|---|---|
| `registry/stage_registry.json` | the stage table pin (`e28f49ab`, `3cdcabe4…`) and one row digest per level. No table text is copied. | code (`registry --write`) |
| `registry/carriers.json` | carriers, parts, allowed axioms, and the standing loss entries each transport must book | hand; changes by review |
| `registry/checkers.json` | target checkers of record: id, level, path, sha256, commit, gated step; from stage 22 also the declared input class; `"provenance": "apparatus"` on the ruling-D4 levels (012, 017, 082-100). Stages 0-100, gated step `target-checkers`. | hand; one entry per merged checker |
| `receipts/<carrier>/<level>/<sha256>.json` | stored receipts, each named by its digest | `check --store`, or the level engine's replay |
| `ledger.jsonl` | one line per (carrier, level) row | code (`ledger --write`) |
| `derived/numbers.json` | T, C, C by band, D, D_native, A | code (`ledger --write`) |
| `INJECTIONS.md` | the checker's own injection record | hand |

## Commands (from the repository root)

```powershell
python research/mssn_sn_tower/ci/run_reach_gates.py              # every reach step, with a table
symbol-game level-engine --workspace . reach ledger-check
symbol-game level-engine --workspace . reach replay --clone 19L57G1=C:/path/to/19L57G1
```

The runner checks the preserved registry and ledger against regeneration. A
number edited by hand therefore fails. The package replay commands read v1
history; they do not store new v1 records or overwrite receiving-side evidence.

## The record and the receipt (`reach-receipt/1`)

A producer submits a **level record**. It contains:

- the carrier's pinned sources;
- the target checker's pin;
- the claimed clauses, each with its exact refusal code;
- the fixtures.

The record carries **no verdict**. Any `grade`, `terminal`, `outcome`,
`verdict`, `computed` or similar field is refused with `RR-PRODUCER-VERDICT`.
The checker replays everything and emits the **receipt**: the record plus a
`computed` block. The block holds the observations, refusals, caps, grades
R/E/P/B, the terminal and the status ceiling. `verify_receipt` deletes that
block, recomputes it, and refuses any difference.

**The 4-fixture rule.** Every record carries four kinds of fixture, all replayed
by the pinned target checker:

- a **positive**, which must be byte-equal to a pinned carrier source;
- the level's **own negative**. It is bound to the row digest and must equal the
  checker's own `OWN_NEGATIVE`;
- a **near-miss**;
- a **decisive mutation** per claimed clause (bite). The mutation must be a
  single edit of its positive repair and be refused with the clause's exact code,
  while the repair passes.

The receiving side then runs its own probes against the checker: empty object,
empty list, null, lists emptied, flags for data, verdict only, and data plus a
verdict. Each must be refused with `R_EMPTY_INPUT` or `R_VERDICT_FIELD`. A
probe equal to the positive (for example `lists_emptied` on a payload with no
list, such as level 000's packet) is marked `PROBE-IDENTICAL-TO-POSITIVE` and
recorded as `INAPPLICABLE`: refusing it would refuse the witness. An empty or
flag-only positive is refused whatever the checker says.

**Checks and codes.** `reach/codes.py` is the closed registry: 36 `RR-*` codes
across K1–K16, 15 `TC-*` transport codes, and two caps (`CAP-NAMED`,
`CAP-SELF-CONSISTENT`). Each code has one injection test that fails with that
code. For 33 of the 36 `RR-*` codes and all 15 `TC-*` codes, the refusal set is
exactly that one code. A census test refuses a code that has no injection.

**Grades.** R1 needs all of these:

- terminal `EVIDENCE_ONLY`;
- a checker of record whose gated step is in `reach/gates.py`;
- the full fixture battery;
- a valid transport certificate.

The other axes:

- E is computed: NAMED without transport, then COMPUTED, LEAN or GATED;
- P comes from the framing;
- B is `named` for supplied challenges, and `blind` only for a blind rung whose
  inputs pass the leak scan.

R2 and R3 are not issued per receipt.

## Transport (`mssn.transport-certificate.v2`)

This is one certificate with six criteria and an inline sealed loss ledger
(`mssn.loss-ledger.v2`). It is issued as `PROPOSED` / `TARGET_REPLAY_REQUIRED`.
The ledger must book each of the carrier's standing entries. For 19L57G1 these
are:

- ties (`source.cost_measure`);
- readings (`source.admission_reading`);
- bounds (`source.declared_bounds`);
- claim class;
- blindness (`source.name_blindness`), which must be `DROPPED` on a blind rung or
  ascent row.

An entry can instead be stated not applicable, with a reason. The runtime type
`omega.symgam.transport-certificate.v1` is unchanged, and submitting it as V2 is
refused.

## Not done in this round (open)

- **Target checkers exist for every stage 0-100** (`code/python/targets/`).
  Each is bound to its row by `ROW_SHA256`, recomputes its obligation, and has
  one decisive mutation per clause (423 clauses: 100 for 0-21, 95 for 22-46,
  109 for 47-73, 119 for 74-100) with a source injection per clause. Their declared input
  classes and limits are in each file's docstring (for example stage 005
  computes curvature exactly only at vertex hinges of 2-cells; stage 021 takes
  rotations as exact rational matrices in SO(4)); from stage 22 the class is
  also written in `registry/checkers.json` as `input_class`. What the band
  022-046 checkers do not decide is named there too: the transport reading of
  gluing (023), localized hom-sets (025), the groupoid reading of equivalence
  (028), derived limits (029), pages outside the reduced F2 basis (030),
  class-valued defects (032), mixed equilibria (040), and the identity of an
  external checker beyond a differing digest (046). For the band 047-073:
  mixed joined tables (056), the nonexistence of an agreeing family (058),
  any irrational ceiling on the two-party total (059), whether a global
  section exists (061), dihedral hinges in three dimensions (063; the exact
  angle table admits only equilateral triangles), any hardness claim (067 is a
  fence over five checker-decided families), arithmetic on algebraic numbers
  (069), irrational eigenvalues (070), and rates other than C / n (071) or
  C h_k on polynomial integrands (073). For the band 074-100: projection,
  equality and aggregation queries (074), views beyond one-column selection
  (075), any noise mechanism or probabilistic privacy guarantee (081),
  unforgeability (082 verifies textbook-RSA chains under a pinned toy root
  whose private exponent is published in the fixtures), tools other than the
  four pinned in 084, language understanding (090 uses a declared clause
  splitter and quantifier list), Lean rebuilding (092 is a resolution kernel;
  K11 still reads pinned axiom reports), wall-clock time (095 counts
  comparisons), intervals other than Chebyshev's (096), and whether a test
  tests its claim (100). The levels 082-100 are apparatus under ruling D4:
  their checkers decide the obligation as the row states it, and none of them
  is an object-language witness. The test fixture
  `tests/reach_fixtures/stage_002_demo.py` is still not registered and does
  not count.
- **No carrier row exists yet**, so every carrier's C is 0. The level engine
  submits records against these checkers.
- **Lift certificates are not accepted yet**, so every D is 0 by construction.
  `ledger.depth()` is implemented and tested, but it has no accepted input.
- K9 checks the lift licence's declared fields, and K10 checks finite up/down
  tables. Neither re-runs a context witness.
- K11 reads a pinned `#print axioms` report and recomputes statement digests. It
  does not rebuild Lean.
- K13 uses the framing rule of W2-C05 §2.2 in place of cross-repository git
  ancestry.
- Criterion 2 implements only `SORT_MAP`. `SIMPLICIAL` and `MATRIX_BY_GRADE`
  are refused with `TC-UNSUPPORTED-KIND`.
- Closed field sets are written in Python (`reach/schema.py`). No JSON Schema
  files are emitted.
- The checks K17–K23 from W2-C05 §4.9 are not implemented. Neither are
  withdrawal rows, promotion records or comparison rows.
- `POLICY.md` (W2-C05 §3.3) is the author's to adopt, and is not written here.
  `EMBARGO.md` needs the run's embargoed list, so it is not written either.
- `carriers.json` gives H3V7N5QF the allowed axioms `{propext, Quot.sound}`, per
  document 10 §3.2. Its Mathlib evidence therefore cannot reach LEAN until the
  author rules otherwise.
