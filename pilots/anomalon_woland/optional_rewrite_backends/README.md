# Optional Julia and DSPy demonstrations

These two demonstrations answer a small engineering question before V1.0RC:
does an existing library help us express a checked transformation without
changing the ordinary PFP interface? Neither library is a default application
dependency. No LLM provider is called by either demonstration.

The production pilot remains Python with its existing PFP boundary. Julia is
an independent reference exercise; DSPy is an optional Signature/Predict seam
exercise. Their fixtures do not measure model quality, token savings or cost.

## Julia: an attributed graph and one explicit DPO rewrite

The [demo](julia/demo.jl) uses actual Catlab ACSets and AlgebraicRewriting DPO
operations, pinned in [Project.toml](julia/Project.toml). A registered rule
replaces one wrong edge attribute while preserving its endpoint potentials.
An independent judge then checks every edge against the exact rational
potential difference. The demo also rejects an unregistered rule and a
natural explicit match that violates the DPO dangling condition.

The graph is checked by attributes and an oriented endpoint multiset, because
categorical constructions can reorder the internal vertex and edge indices.
The fixture's four distinct potentials serve as unique endpoint labels. A
coherently rebound graph with equal potentials/counts and an exact gradient
still fails this topology comparison. This is a check of that finite fixture;
no general graph-isomorphism algorithm, automatic match search, confluence
result or physical cochain theorem is claimed.

Install a separate Julia 1.11 runtime and use an isolated depot. From the
repository root in PowerShell:

```powershell
$env:JULIA_DEPOT_PATH = Join-Path (Get-Location) 'target/optional_rewrite_demos/julia_depot'
$env:JULIA_PKG_PRECOMPILE_AUTO = '0'
julia --startup-file=no --project=omega_engine_woland/tests/pilots/optional_rewrite_backends/julia -e 'using Pkg; Pkg.instantiate(;allow_autoprecomp=false)'
julia --startup-file=no --project=omega_engine_woland/tests/pilots/optional_rewrite_backends/julia omega_engine_woland/tests/pilots/optional_rewrite_backends/julia/demo.jl
```

Reference API: [AlgebraicRewriting full demo](https://algebraicjulia.github.io/AlgebraicRewriting.jl/dev/generated/full_demo/).
The DPO checked explicit-match API uses `rewrite_match(rule, match; check=true)`.
For attributes, this demo supplies an explicit `ACSetCategory(VarACSetCat(...))`
to every transformation, rule and rewrite; the inferred fixed-type category
produced an actual `id_condition(::Nothing, ::Nothing)` method refusal in the
first run. Exact edgewise arithmetic remains a separate host check.

The corrected demo actually completed all 13 assertions with Julia exit code
0 in 381.125 seconds, including the first cached-library compilation, using
Julia 1.11.7, AlgebraicRewriting 0.5.0 and Catlab 0.17.6. Its retained raw
stdout/stderr and source snapshots are bound in the task's
`optional_demos/julia_execution_v004.json` receipt. This is a successful finite
fixture, not a hot-runtime benchmark. The earlier unpublished-version refusal,
fixed-attribute category error, 420-second uncached timeout and Windows cache
access refusal remain explicit failed observations. The timeout's raw streams
were not retained by the old helper; that custody limit is recorded, and the
final helper writes streams directly to files. Its later console-rendering
error occurred after Julia exited 0 and the native receipt was saved; the
helper's UTF-8 console encoding is now explicit.

## DSPy: a typed prediction through the existing PFP boundary

The [demo](dspy/demo.py) uses DSPy 3.0.4 `Signature`, `Predict`, `Adapter` and
`BaseLM`. Its custom adapter creates a normal PFP task turn and passes exactly
that prepared system/user conversation through the LM boundary. Raw fixture
bytes reach PFP's strict checker and an independent exact seed comparison
before DSPy can parse a prediction. The typed proposal contains only a preserved
seed and the single registered selector `pfp.optional.typed-proposal.v001`.
The host resolves its fixed instruction; an unknown selector is rejected.
The output-contract change is named `optional-dspy-seed-rewrite-v002`, with
checker `exact-seed-and-template-v002`. Earlier prose-output replies and their
source bytes remain historical receipts. Receipt hashes are derived by the host.

The fixture LM has no provider implementation. Unprepared calls, modified
signatures, few-shot examples, decoding overrides, retries and multiple
generations are refused. DSPy's permissive JSON repair and fallback adapters
are not used. This is one local prediction with an explicit `OFFLINE_FIXTURE`
label, not an optimizer, model trial or claim of general prose equivalence.

Use a disposable virtualenv rather than installing into `.venv`:

```powershell
uv --cache-dir target/optional_rewrite_demos/uv_cache venv --python .venv/Scripts/python.exe target/optional_rewrite_demos/dspy_venv
uv --cache-dir target/optional_rewrite_demos/uv_cache pip install --python target/optional_rewrite_demos/dspy_venv/Scripts/python.exe -r omega_engine_woland/tests/pilots/optional_rewrite_backends/dspy/requirements.txt
$env:PYTHONPATH = (Get-Location).Path
$env:DSPY_CACHEDIR = Join-Path (Get-Location) 'target/optional_rewrite_demos/dspy_cache'
$env:LITELLM_LOCAL_MODEL_COST_MAP = 'True'
$env:PYTHONIOENCODING = 'utf-8'
target/optional_rewrite_demos/dspy_venv/Scripts/python.exe -m omega_engine_woland.tests.pilots.optional_rewrite_backends.dspy.demo
```

The local cost map flag prevents LiteLLM from fetching price metadata during
import. It does not provide billing evidence. No live route is enabled; adding
one later requires the existing PFP provider port, run-wide reservation ledger
and $0.05 cap, including retries. Unobserved billing must stay unobserved.

The [14 focused controls](dspy/test_demo.py) check raw envelope custody, replay,
exact seed comparison, malformed JSON, extra fields, wrong types and bindings,
and the no-retry/no-bypass conditions. They skip explicitly when DSPy is absent.
Install pytest separately in the disposable environment to run only this file
with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and a writable external `--basetemp`.

Reference APIs: [DSPy custom LM documentation](https://github.com/stanfordnlp/dspy/blob/3.0.4/docs/docs/learn/programming/language_models.md),
[pinned BaseLM source](https://github.com/stanfordnlp/dspy/blob/3.0.4/dspy/clients/base_lm.py).
The pinned [JSONAdapter source](https://github.com/stanfordnlp/dspy/blob/3.0.4/dspy/adapters/json_adapter.py)
contains repair and fallback paths, which explains the strict adapter choice.

The observed disposable environment contains 86 installed distributions,
including pytest and its tools. The original 13 prose-output seam controls
passed there; the tightened 14 selector-output controls also passed. Their fresh
execution has separate versioned receipts. The demo observed zero socket connection
attempts, including during import. This dependency footprint is one reason to
keep the SDK optional before V1.0RC. The exact observed versions and raw fixture
reply are retained in the task's `optional_demos` receipts, with no provider
billing or model performance claim.

## Adoption decision

Keep both optional for V1.0RC. Revisit Julia if broader attributed schemas make
the current restricted graph implementation costly to maintain. Revisit DSPy
only after a bounded, matched model experiment demonstrates enough benefit to
justify its dependency and optimization complexity. These demonstrations
establish executable integration, not that either library improves PFP results.
