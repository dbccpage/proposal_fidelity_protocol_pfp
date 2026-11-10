# pilot_0000041 — Face activation and declared toy observables

Quiz08 rewritten as an offline executable teaching pilot. It constructs signed boundaries, checks a locally permitted state transition and keeps assigned mass/drag values separate from topology. No provider calls or paid budget.

## Run

From the repository root (Python3.12):

```powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000041/run.py
```

A completed demonstration or parsed-input evaluation creates a fresh UUID directory under `pilots/pilot_output/pilot_0000041`, retaining input bytes, computed results, a summary and SHA256 receipt. `--input path.json` checks a proposed answer; `--output-dir path` overrides the output root. A matching refusal is still `MATCH`: matching the evaluator is not execution of a requested transition. Exit codes are0 for demonstration/match,1 for mismatch/rejected schema and2 for unreadable/malformed input or output I/O failure. The built-in demonstration is recorded as `MISMATCH` and exits 1 when any exercise row lacks a fact listed for it in `SOURCE_FACTS` (transcribed from this README's source-row table). Raw parsing/byte-limit failures do not produce a retained bundle; an output I/O failure may leave an incomplete fresh directory. This runner is not a durable intake archive.

## Explicit finite contract

- A task declares3–16 vertices,3–48 oriented edges and exactly one potential oriented triangular face. Duplicate unoriented edges, undeclared endpoints and missing face edges are refused. There are no other active2-cells; additional graph edges/cycles are permitted.
- `activity_encoding = one_potential_face_binary_activity_v1` declares that integer bit0 means the face is absent from the active complex and bit1 means it is present. This is not an already-attached face with a zero numerical weight. Booleans and floats are not bits.
- State has exactly `revision`, `face_weight`, and a bounded JSON object `payload`. A pop increments the revision, changes0 to1 and preserves every payload value, including the distinction between1 and true.
- `adapter` is null, or has exactly `scheme: linear_activity_observables_v1`, `mass_scale` and `drag_scale`. Each scale is null or a canonical nonnegative rational string (for example `2/3`). An assigned value is scale times the activity bit. An absent assignment remains null, even at activity0. Source fixtures explicitly assign both scales `1/1`; alternative scales are a declared extension for counterexamples.
- Identifiers are1–32 ASCII letters/digits/underscore/dot/hyphen, starting with a letter. Integers and rational numerator/denominator magnitudes are bounded at1,000,000 (JSON payload integers at10^18). Input is bounded to131,072 bytes; strict JSON rejects duplicate keys, floats, nonfinite numbers, unknown schema fields and unsupported query kinds. Nested payloads have declared depth/size/ASCII limits in `json_value`.

### Signed construction and finite argument

For an oriented edge `[u,v]`, its boundary is `v-u`. For potential face `[a,b,c]`, the edge-chain boundary is `b = [b,c]-[a,c]+[a,b]`, translated into the declared edge orientations. Endpoint cancellation gives `B1 b = (c-b)-(c-a)+(b-a)=0`. The implementation constructs `B1` and computes the cancellation, rather than returning a stored zero.

With no active face, `C2=0` and `B2` is an explicit edge-count-by-zero matrix. The nonzero chain b is then not a boundary. With the face present, `C2=Z` and `B2=[b]`, so `B2(1)=b`. The implementation computes `B1B2` with explicit empty dimensions.

A chain c is exact in this one-potential-face complex precisely when c=0 before activation, or c=k b for an integer k after activation. One coefficient of b is±1, so a candidate k is read from that pivot and every edge is checked. Closure is a separate computation `B1 c=0`. An unrelated graph cycle can remain non-exact after this face is attached. No general homology algorithm or all-cycles-filled claim is made.

The named lock requires the unit signed chain `lock=b`, not just any closed chain or any multiple. Zero, `-b` under unchanged face orientation, and `2b` are refused. Reversing the face and its lock together with a new matching permission is a different admitted input.

### Queries, permissions and replay

The structured query always has `case_id` and `kind`:

| kind | Additional fields | Result |
|---|---|---|
| observe | none | Constructed topology, classification of the face boundary, assigned observables |
| chain | chain | Integer chain closure and one-column filling witness |
| compare | other_state | Two observations under the same carrier/adapter; mass comparison or null; no transition executed |
| pop | event_id, face_id, before_state_sha256, after, lock | Checked0-to1 transition, or unchanged state and no actual-after result |
| replay | events | Up to8 pop queries, evaluated against evolving current state; stop at first refusal |
| physics | claim | ref<3> for one of the three explicit physical claim IDs |

A pop has a separate supplied `permission` object with `permit_id`, Boolean `admitted` and `problem_sha256 = SHA256(canonical({task,query}))`. A replay supplies a parallel list of per-event permission records (or null refusals). All event and permission record shapes are validated before replay starts. Freshness/permission decisions are checked only when each event is reached, against the evolving state. Each event's grant binds the current task and that event. It does not grant authority to a whole trace or constrain neighboring events. Replay retains the successfully executed prefix on refusal; it is not an atomic transaction or rollback. Repeating the original pop against the updated state fails; even a freshly matched grant cannot turn1 into1 through this0-to1 operation.

`permission_for` constructs a local demonstration record; it is not an authenticated issuer. Digests check consistency, not principal identity, security, persistent state or cross-run one-use. Each evaluation starts from its supplied task state.

An input document has exactly `{task, query, permission, proposal}`. The proposal has `{input_sha256, answer}`; the digest binds canonical `{task,query,permission}` and the full answer is compared byte-canonically with recomputation. Input/output snapshots do not alias caller data. `submission`, `triangle_task`, `pop_query` and `answer_for` are convenience functions for building explicit inputs.

Physical IDs are `cern_higgs_boson_125_gev`, `standard_model` and `origin_of_inertial_mass_in_qft`. These typed queries return `ref<3>`, regardless of activity or observable assignment. This is not a detector for arbitrary natural-language physics claims. Permission fields are only accepted on transition queries.

## Worksheet accounting and corrections

The report retains the nine literal source rows separately: P8.1–P8.4 and DRILL8.1–DRILL8.5, with all seven historical forms. Both pop rows start from separate inactive fixtures; one is not an illicit second activation. An initially active fixture is a supplied state, not evidence that an authorized history produced it. Historical `ask<...>` / `ans<...>` strings are labels, not a general wire parser or external standard.

| Source language | Executable meaning or correction |
|---|---|
| hollow2-simplex | Unfilled triangular boundary; no active2-cell |
| weight/area0 or1 | Explicit activity bit; no measured area |
| massless flow, friction, inertial drag | Assigned toy values only; no transport or force law |
| Higgs, symmetry-breaking pop | Permitted cell activation; no specified group, dynamics or vacuum |
| L tensor F1 = Delta / lock | Signed unit filling relation; no tensor operation |
| obstruction metric proportional to area | Not adopted: no metric axioms, geometry or mass derivation supplied |

The user's existing declared-toy corrections are preserved. Rewriting corrects the remaining implications rather than giving historical labels unearned physical meaning. A present face assigned toy mass0 still bounds its boundary; a face with no assignment has undefined mass/drag. Filling the triangle does not by itself select or break a symmetry.

## Verification and limits

Repaired candidate r3:85 passing tests,21 caught compiled mutations,304/305 statements and71/72 branches covered (99.47% combined;98.61% branches), with no exclusions. `run.py` is all scoped production code and uses only the standard library; pytest and coverage are test tools. Real subprocess CLI checks supplement in-process coverage; the unmeasured line/branch is the module-entry guard exercised by those subprocesses.

Independent finite checks cover96 oriented/relabelled triangle fixtures and2,592 candidate locks,250 integer-chain cases, an unrelated-cycle counterexample, independent mass/drag assignments, state/query/permission/proposal attacks, and real CLI receipts. Mutation tests compile altered copies and require actual assertion failures while preserving original bytes. Candidate r1 retained its Windows oversized-test-name failure; r2 uses bounded names. Frozen research round1 then found that an unreachable malformed permission could escape schema validation after an earlier refusal. Its complete56-file replayable snapshot and counterexample are retained under quiz08_research/round1_snapshot. Round2 adds a separate permission-shape check, a six-variant negative regression with valid-record controls, and a compiled mutation that removes that check. Earlier84-test results are historical, not acceptance of the repaired runner. No missing input or failed run is counted as PASS.

Fresh final-location and main-checkout reports, exact hash manifest and frozen research disposition are recorded outside this primary code file in `pilots/pilot_output/pilot_0000041` and `_intelligence/research/briefs/pfp_migration/quiz08_research` / `quiz08_delivery_20261007`. The source worksheet and focused old-helper evidence are pinned there. Test isolation and claim-hygiene skills govern scoped runs and narrow language; vocabulary lint does not establish mathematical truth.

Supports: the declared finite construction and implementation behavior above. Does not support: physical Higgs, inertia, geometric area, symmetry breaking, dynamics, a metric, Genesis derivation, general homology, Lean-checked theorem, authenticated authorization or LLM competence. `authority_effect` and `genesis_effect` are None; `realizes` is null. No Rust production parity claim.

Narrowest claim: an explicitly permitted activation adds the one declared boundary column; its signed boundary acquires a unit filling witness while separately declared toy observables are evaluated. Next extension would require a new contract for multiple active faces and an actual image/rank check before claiming a previously unfilled cycle was filled. This migration is not one of the100 NEW pilots and does not make the remaining estate ready.
