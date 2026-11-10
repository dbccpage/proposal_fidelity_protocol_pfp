# Pilot 000009 — Trace shape and stationary refusal

Rewrites Quiz09 as an offline, executable exercise. No model calls or paid
transport. This is a local teaching model, not a new standard, a proof of monad
laws, or a conformance result for the wider DDC runtime.

## Run

From the repository root after relocation:

```powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000034/run.py
py -3.12 -m pytest -c omega_engine_woland/tests/pilots/pilot_0000034/pytest.ini omega_engine_woland/tests/pilots/pilot_0000034/tests --basetemp=scratch/quiz09_tests
```

The default run computes all four exercises, all five drill rows, and four
separate state-replay demonstrations. Results go to a fresh run directory under
`pilots/pilot_output/pilot_0000034`. Existing run directories are not overwritten.
The receipt hashes the exact input bytes, result and summary, plus a proposal
file when supplied. Receipt hashes check file consistency, not authorship.

`--input task.json` accepts either of these independent checks:

```json
{"kind":"shape","wire":"tape<c,r,e,i,t>"}
```

```json
{"kind":"stationarity","before":{"values":[3,2],"repair_rank":1},"after":null}
```

Replay uses `--input task.json --proposal proposal.json`. Its task is
`{"kind":"replay","problem":...}`; its separate proposal is
`{"steps":[{"event":"C","after":...,"witness":{}},...]}`. The built-in
`demonstration("repair"|"refusal"|"descent"|"lift")` function returns complete
task/proposal examples. Changing a task invalidates integration receipts.
The input task is the caller's declared scope; an LLM proposal must not replace it.

Exit 0 means the requested checks completed; exit 1 means rejected or unverified;
exit 2 means the input could not be read/decoded or output could not be stored.
Malformed JSON is refused before a receipt is created. Rejected decoded inputs
are retained. A default run contains intentional negative exercise results.

## The exercises, without the hidden claims

| Source ID | Computation | Expected result |
|---|---|---|
| P9.1 | Shape of `C R E I T` | Accept shape only |
| P9.2 | Shape of `C R M E T` | `ref<1>` |
| P9.3 | Shape of `C R T E` | `ref<1>` |
| P9.4 | Compare two complete typed states | Equal: stationary; absent: unverified; different: `ref<2>` |
| DRILL9.1 | `C R E I T` | Accept |
| DRILL9.2 | `C R M T` | Accept |
| DRILL9.3 | `C R M E T` | Reject |
| DRILL9.4 | `E C T` | Reject |
| DRILL9.5 | `C T E` | Reject |

Puzzle and drill numbering overlap in the source; these IDs preserve both.
The retained shape language is `C (C|R|E|I|LIFT|D)* M? T`.
Repeated `C` and the minimal `C T` are admitted. It is not the broader DDC
paper's refusal policy, which also allows changed context or a licensed lift
after refusal. The strict wire syntax is lowercase `tape<c,...,t>` with no
trimming, aliases, spaces or repairs. A bounded list interface accepts uppercase
labels. Maximum: 64 events, 512 wire characters, 64 KiB per JSON document.

Equal recorded endpoints do **not** rule out an unlogged path such as `0→1→0`.
The comparison checks only supplied finite states. The pure refusal transition
preserves its protected state; control and audit records change separately.
No arbitrary external runtime or LLM is being monitored here.

## The exact replay model

A protected state is an integer vector `x` of length 1–8 and a repairable prefix
length `k`, with `0 <= k <= len(x)`. Integers have absolute value at most 1,000,000;
booleans and floats are refused. State equality includes `k`, not just `x`.
The declared repair operation can subtract a prefix vector and cannot touch the
tail. `unrepairable_l1 = sum(abs(x[k:]))` is computed in this particular model;
it is not a diagnostic inferred from prose or a general DDC solver.

| Event | Executed local rule |
|---|---|
| C | Expose the unchanged protected state and its measurement |
| R | Check the prefix potential and projected tail; leave active state unchanged |
| E | Check the exact prefix witness and zero tail, then set the vector to zero |
| I | Check the immediately preceding computed record hash; leave state unchanged |
| M | Return an equal, independently allocated protected state and typed reason |
| T | Leave state unchanged and close the complete proposal |
| D | Drop the final, non-repairable coordinate; require `n>1`, task permission and exact signed loss entry |
| LIFT | Increase `k` by one without changing `x`; require a nonzero tail and task permission |

Each step's proposed after-state must equal the computed one. Shape is checked
before any replay operation. A proposal with a post-refusal or post-terminal
event is rejected as a whole. The result is not an appendable runtime session.
`M` reasons are typed declarations, not automatically verified explanations of
an external failure. `T` can seal an unresolved/refused run; it does not mean repair.

Task fields are exactly `profile`, `initial`, and `permissions`; the local profile
string is `quiz09-prefix-vector-replay-v1`. A permission is the exact event plus
SHA256 of the complete before/after states. The proposal references its hash;
the checker also requires the permission to occur in the separate task.
This is a task-allowlist check, **not cryptographic authentication of an issuer**.
The record chain binds the original task, step index, event, full states,
measurements, actual witness, and prior record. An externally retained head and
length are needed to anchor history; a self-consistent chain alone is not one.

The loss entry for D contains the dropped index, its exact signed value and the
before-state hash. LIFT may leave the remaining tail nonzero. Both moves change
the repair problem, so their subsequent zero state is explicitly **not claimed
as a solution of the original unchanged problem**.

The four canonical examples become separate runnable demonstrations: ordinary
repair, unchanged refusal, permitted descent and permitted lift. C here exposes
an existing state; LIFT changes a repair prefix. Neither is asserted to be the
DDC paper's full carrier construction. No Phi1/Gamma2, Hodge, cochain-equivalence,
external-authorization or deployment theorem is claimed.

## Verification and preserved source

Unit tests cover strict boundaries and each operation. Integration tests bind
the chain to the task, permission, loss, receipt and after-state. An independent
regular-language oracle and the archived old shape function are compared on all
299,593 tapes of length 0–6. Finite arithmetic tests enumerate vectors and ranks;
CLI tests launch a real process and recheck retained artifact hashes. Mutation
tests run syntactically valid altered implementations in isolated subprocesses.

Coverage measures all of `run.py`, including CLI and artifact writing. Only
standard-library production dependencies are used. Test counts and observed
coverage belong to the dated verification receipts, not a claim of complete
correctness or a full-estate pass.

Original worksheet bytes are retained at
`_intelligence/research/briefs/pfp_migration/quiz09_research/sources/quiz09.md`.
The five-source inventory records hashes and read coverage. It also retains the
old checker and relevant DDC parser/paper versions for the contract comparison.
The worksheet's broken old `ow/...` grammar link is replaced by the actual
`PFP/grammar/ddc_trace.ebnf` source. No shared DDC runtime was changed.
