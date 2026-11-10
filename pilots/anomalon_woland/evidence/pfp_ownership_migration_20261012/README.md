# PFP ownership cleanup and replay

AuthorityEffect: None.

The active application no longer uses paper-number runtime packages, numbered
runner modules, a private canonical-types store, or executable Python beneath
its YAML resource directory. See the [ownership map](../../../../omega_engine_pfp/README.md).

Shared calculation/workpad contracts and exact typed agreement now belong to
`omega_engine_pfp`. Research compositions live in
`pilots/relational_spacetime`, `pilots/challenge_suite`, and
`pilots/judge_packet_audit`. Prompt version 1.0.2 is an undispatched relocation
version; it provides no evidence of better model performance.

`frozen_runtime.json` binds 59 retained source files. Most came from the captured
1.0.0 runtime; supplementary retired sources are exact bytes from commit
`789c69da144c8f668db3ad1cedfab27da4d24cd9`. Historical path names inside
`frozen_sources` describe original custody. They are data for replay and do not
provide active compatibility imports.

`retired_sources.zip` preserves the same 59 source files. Its digest and verified
entry count are recorded in `validation.json`; each extracted file matches the
source digest in `frozen_runtime.json`.

The Symbol Game frozen-replay adapter checks source hashes, stages evidence
before verified executables, empties unpinned package initializers, blocks Python
outbound socket operations, and removes its disposable scratch directory. It is
an offline replay mechanism for trusted retained sources, not an OS sandbox.

Validated profiles preserve recorded outcomes, including failures:

| Profile | Replayed evidence |
| --- | --- |
| `scratchpad-temperature-logit` | 40 recorded calls |
| `compact-three-stage` | 15 recorded calls |
| `five-final-prompts` | 25 recorded calls and five reviewed final prompts |

Run a profile from the repository root:

```powershell
.venv/Scripts/python.exe -m omega_engine_pfp.infrastructure.adapters.pfp_frozen_replay --bundle omega_engine_education/pilots/evidence/pfp_ownership_migration_20261012 --profile five-final-prompts
```

The challenge-suite snapshot tool separately accepts a clean, detached,
disposable checkout with its normal dependencies. It overlays captured sources,
including paths retired from the current application, then restores tracked
files and removes only the files it created. `--run` selects saved runs for
targeted replay. Its deletion/restoration behavior has regression coverage; this
cleanup does not claim a fresh replay of every historical challenge trial.

`validation.json` records targeted checks and their limitations. No provider
dispatch or full canonical CI was performed. Native-host tests were unavailable
because this checkout has no configured Symbol Game host executable. The combined package inventory records 12 existing public-name collisions.
Those semantic reviews and the lesson/dossier response-contract mismatch remain
explicit follow-up work; recorded schemas are not silently unified.

