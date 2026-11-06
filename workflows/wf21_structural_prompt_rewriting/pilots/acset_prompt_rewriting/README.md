# ACSets and DPO prompt rewriting pilot

This bounded experiment asks whether a reusable structural executor can retain
exact protected task, constraint and output bytes while attaching a hint or
symbolic encoding. It uses a fixed attributed directed-graph schema, explicit
injective matches and identity-key monic interface inclusions. This is the finite
graph fragment of ACSet/DPO rewriting; it is not a general Catlab replacement.
Julia and DSPy remain optional demonstrations. AuthorityEffect: None.

The shared executor is
[`finite_dpo.py`](../../../../omega_engine_pfp/domain/rewriting/finite_dpo.py).
It checks exact attribute/type matching, incidence naturality, identification,
dangling edges, registered rules, deterministic fresh IDs, fuel and size bounds.
It returns immutable state and named canonical JSON digests for the graph and
complete rule. It does not claim RFC 8785 serialization or search for matches.

The independent pilot judge compares the exact ordered `(source slot, role,
UTF-8 text)` query and source identity. Rebound text or reordered slots fail even
when both states and new digests are structurally valid. Structural DPO success
alone is not prompt fidelity. Hint content is untrusted and has no measured model
benefit. The existing symbolic constraint-binding compiler renders the optional
encoding, and the existing typed PFP turn wraps every rendered seed.

The [25 targeted controls](tests/test_acset_prompt_rewriting.py) include positive hint/encoding
insertion, Unicode retention, two-stage replay, fresh-ID collision handling and
PFP fixture typing; protected deletion, relabeling, coherent hostile rebinding,
source substitution, wrong match attributes, noncommuting endpoints,
identification, dangling edges, duplicate IDs, exhausted/boolean fuel,
unregistered/duplicate rules, graph/UTF-8 bounds and stale source refusal.

Run the tests from the repository root with a writable external `--basetemp`:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
.venv/Scripts/python.exe -m pytest -q omega_engine_adversary/tests/pilots/acset_prompt_rewriting/tests/test_acset_prompt_rewriting.py --basetemp <writable-owned-directory>
.venv/Scripts/python.exe -m omega_engine_adversary.tests.pilots.acset_prompt_rewriting.run
```

The standalone runner computes actual host rewrites and checks explicitly
synthetic PFP proposal fixtures for a supplied rational triangle: `a→b=3/2`,
`b→c=-7/3`, `a→c=-5/6`, with `a=0`. The closed typed answer schema permits a
potential proposal or a refusal. The runner derives its fixture coordinates with
exact fractions; the PFP shape check leaves task correctness `UNVERIFIED`.
The separate cochain pilot owns independent mathematical acceptance. This pilot
checks protected query equality, not a solver or efficacy trial. It emits
source/rule/graph/raw-reply bindings. These are offline
`FIXTURE_VERIFIED` controls, zero provider sends; no actual LLM or cost-effectiveness
claim. A later matched model trial must retain independent task checks, raw
replies and settled costs under the existing $0.05 run-wide cap.

Each operation receipt retains explicit part/link matches, starting and remaining
fuel and complete rule/source/result digests. `replay_fixture_record` reruns the
registered operation, independent query comparison and original PFP byte check;
it refuses altered receipts, public turns and raw replies. Cached statuses grant
no acceptance. Source/seed strings containing lone surrogates fail with a typed
UTF-8 refusal before source hashing.
The entire operation receipt is bound into the public PFP input digest. Raising
starting and remaining fuel together cannot preserve an old public turn or reply.
