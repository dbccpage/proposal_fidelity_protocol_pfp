# Full Retinue run with consolidated output

The current IDE run `woland-clean-output-20261016` completed on 16 October 2026.
It used the existing shared Python coordinator, PFP exchange, 128-dimensional
observer, Forge preparation and full packaged Retinue. One IDE assistant supplied
the sequential model contributions; role coverage does not establish independent
agents.

The captured run used implementation commit
`4cdcdc7c7c5b8dad0488bbb33c3f8f3221cfa3cc`. Later reconciliation with main's
DDC-only intermediate format was checked separately; it does not rewrite this
capture or claim that the original dialogue exercised later source changes.

| Observed result | Value |
| --- | --- |
| Work status | `completed` |
| Required roles observed | 22 of 22 |
| Recorded actions | 33 |
| Checked IDE captures | 22, including the final Koroviev learning review |
| Original-task checks | Two actual successful executions of the same frozen checker |
| Scoped AutoP/learning finishes | One |
| Final digestion | Zero findings and zero coverage gaps |
| New repair turns | Zero |
| Woland external provider dispatches | Zero; IDE billing remains `UNOBSERVED` |
| Final DDC records | 33 observed actions and four actual retained procedure steps |
| UTS events | 37, with unique ordered identities |
| Historical byte pins checked unchanged | Five |

The read-only replay validated every captured reply against its original PFP
action, the episode ledger, original check captures, full captured narrative,
ordered UTS, single DDC tape and final file digests. Saved history and the final
summary's `source_history` agree exactly. The run completed under its declared
diagnostic policy: the last native batch retains 33 `HOLD` results for unmeasured
witnesses and two `PASS` results, with no `REFUSE`, `BLOCKED` or `DIVERTED` result.
Those diagnostics are not promoted to mathematical acceptance; the evidence
verdict remains `OPEN_RESIDUAL`.

## Retained local outputs

Canonical folder, outside the working checkout:

```text
C:\Users\a343o\source\repos\the_symbol_game\_ic\woland\runs\woland-clean-output-20261016-7b159f7b5574
```

It contains exactly `uns.md`, `uts.jsonl`, `ddc.jsonl`, `summary.json` and
`receipt.json`. Bundles written after this run also carry a `mam/` folder
(see the woland skill's run output custody reference). There is no separate `dda*` file. `ddc.jsonl` retains the action
tape once, followed by the latest sealed procedure's actual steps; it does not
concatenate repeated copies of earlier program prefixes.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `uns.md` | 1258974 | `c2b9bbf58ef8fefd31a5a69c359093a4aaf496b0abd32f0319b6e294fa4f293a` |
| `uts.jsonl` | 474634 | `a622f5d8da780e59cd2861b3cc7191b2da7c10f9b8c2ecf8b902740a1c717683` |
| `ddc.jsonl` | 77063 | `b67fa5c6012f8ab74ea78c3f374a0951286e46d7ab969cdddf01cfb3e3cdfd3d` |

Receipt identity:
`sha256:56cb84a1ae68637d577bcc4a3010314b67152cc16cf6cd161a465b30d44d534e`.
Saved exchange state:
`.scratch/woland-clean-output/teamwork.json`, SHA-256
`c4493e326475e9aff50ed6cf89f77bc25a4f652ffb11e93f322ed770a8b15138`.
Raw replies, native gate captures, admitted checker episodes and both sealed
procedure folders remain beside that exchange. These paths describe this local
demonstration; historical readers still require their retained source bytes.

The pinned native host was
`.scratch/woland-clean-output/runtime/host.exe`, SHA-256
`6bdba054bf3537aeeb1cd9099163e960cc86b82b6df148e196baed8a63ce5f64`.
The dialogue took 939.706 seconds including manual IDE reading and response
authoring; this is not an inference-speed benchmark.

## Commands and verification scope

The local run used the existing Python API callback pattern documented in
[shared teamwork](shared_teamwork.md#python-callback-in-an-embedding-host):

```powershell
.scratch/oewas012/venv/Scripts/python.exe -u -B .scratch/woland-clean-output/session.py
.scratch/oewas012/venv/Scripts/python.exe -B .scratch/woland-clean-output/audit.py
```

The two local exchange helpers are retained demonstration state, not a new public
runner. For a new task, use the existing `/woland` skill or `teamwork start`,
read each prepared system/user/schema and submit the actual bound reply as
described in the shared-teamwork guide. Fresh runs automatically use the new
output names. Read-only replay does not create a new swarm run.

The frozen original checker ran only these owning controls, with outputs in a
writable scratch directory:

```powershell
python -B -m pytest -q omega_engine_woland/tests/test_clean_output_layout.py omega_engine_woland/tests/test_teamwork_reporting.py --basetemp .scratch/woland-clean-output/pytest-acceptance
```

All twelve passed in preflight and in both admitted original-task checks. Three
selected real-native StructureBench controls also passed, including historical
duplicate-copy tampering. The focused Rust `reported_bundle_v3_tests` control
passed; its first execution encountered a Windows temp ACL failure, then passed
with the existing writable `TEMP`/`TMP` selection and no code change. The native
host was built offline with `-j 1`. No full pilot grid or whole-repository test
suite was run.

The existing AutoP finish reported no anti-pattern findings across the 53 selected
files. Useful compatibility lessons were applied to the existing digestion,
learning-intake, historical writer and structural reader owners during the build;
Bezdomny correctly reported that no additional edit was justified. Selected IDE
skill/workflow mirrors were regenerated through the existing scoped host path.
