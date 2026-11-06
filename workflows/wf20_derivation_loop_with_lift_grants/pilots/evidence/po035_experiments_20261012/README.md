# PO035 scratchpad, temperature and logit trials

AuthorityEffect: None. Available trials **COMPLETE**; attention-head execution
**UNAVAILABLE**. No new learning item is admitted automatically.

Fifteen paired test runs made **40 OpenRouter calls**, using **198952 total
provider tokens** and **17035 microusd (USD 0.017035)** of accounted cost. Every
run stayed within its shared USD 0.05, 120000-token and 180-second caps. All calls
settled; there are no unresolved holds. Zero final packets passed the unchanged
finite certificate predicates. This is a negative result on five demanding PO035
tasks, not a general limit on PFP or scratchpads.

[results.json](results.json) contains per-run/stage outcomes. The
[experiment matrix](experiment_matrix.yaml) preserves the specifications written
before dispatch; its PLANNED labels are not measured statuses. Five additional
head-intervention cases have explicit unavailable responses and zero generations.
The earlier [neutral/guidance proposal](../po035_next_round_review_20261012/README.md)
was not separately dispatched.

## Comparisons and outcomes

Each comparison covers pilots 199 through 203. All arms use the original seed,
the PFP template, strict typed output, task-scoped licenses, compact procedural
hints and independent original judges. The versioned system extension permits
explicit conditional analytical assumptions. Pilot 201 receives the missing
eight-stage source excerpt; pilot 202 receives the complex-identity clarification.
Expected fixture answers and reviewer solution equations are excluded from the
participant prompts. Earlier prompt/evidence bytes remain historical evidence.

| Comparison | Calls | Schema-valid final packets | Accepted finite packets | Tokens | Accounted USD |
|:--|--:|:--|:--|--:|--:|
| Single shot versus draft/audit/final workpad bundle | 20 | Control 1/5; staged final 0/5 | 0/5 in each arm | 97755 | 0 |
| Temperature 0 versus 0.7 | 10 | T0 0/5; T0.7 2/5 | 0/5 in each arm | 55015 | 0 |
| Empty logit bias versus format-only soft bias | 10 | Control 0/5; biased 2/5 | 0/5 in each arm | 46182 | 0.017035 |
| Actual attention-head intervention | 0 | Unavailable | Unavailable | 0 | 0 |

**Scratchpad:** the free `nvidia/nemotron-3.5-lightning:free` route made a stateless
2500-output-token control, then a separate 1000-token public draft, 1000-token
public audit and 2500-token final. Only schema-valid treatment work records were
carried forward; control replies never entered the treatment. These are explicit
public work products, not requests for private reasoning. Eight of ten workpads
hit their output ceiling and were truncated; only one workpad passed its schema.
The staged finals did not improve the finite outcome. This compares a three-call
bundle with a one-call control, so it does not isolate scratchpad format or measure
single-shot improvement. The workpad contract was too demanding for the chosen
1000-token allowance on most cases; this does not establish that more rounds help
or that scratchpads inherently fail.

**Temperature:** the same free route received matched stateless requests at 0
and 0.7, with paired seeds and 2500 output tokens. One T0.7 reply was truncated.
The two additional schema-valid packets were mathematically incorrect. Five tasks,
one sample per arm and fixed T0-first order do not identify a best temperature.

**Logit bias:** `qwen/qwen-2.5-72b-instruct` was requested through the sole eligible
DeepInfra FP8 endpoint with fallback disabled and required parameters. Both arms
used temperature 0.7 and the same seed; the control sent an empty bias map to keep
endpoint eligibility matched. The variant assigned -5 to token IDs 63, 13874 and
73594, which are standalone one-, two- and three-backtick tokens in the retained
tokenizer. No answer digits or mathematical values were targeted. This is limited
soft format steering, not a JSON grammar: compound tokens can still contain
backticks, and fenced replies still occurred. Parameter transmission is recorded;
internal provider enforcement is not attested. The paired order was fixed with
control first, so syntax gains are descriptive, not a reliability estimate.

The [public preflight](public_preflight_sources.json),
[endpoint snapshot](qwen72_endpoints.json) and each run's retained pricing profile
record the capability and price checks. At dispatch the paid route quoted USD
0.36/M input and 0.40/M output tokens, without additional fees; the conservative
120000-token output-price bound was USD 0.048. Availability and prices are dated
observations, not promises about future calls. Catalogs were refreshed once per
experiment group and retained for its five pilots; the endpoint snapshot was shared.
The provider's parameter semantics
are documented in [OpenRouter's parameter reference](https://openrouter.ai/docs/api-reference/parameters).

## Actual head manipulation remains a separate experiment

The five specifications under [attention_head](attention_head) define a control
and ablation of a selected query head's context slice before output projection,
across prefill and decoding. Each requires numerical equivalence of the identity
hook, a nonzero original head, evidence that only the selected slice changed, and
removal of the hook afterward. Both improvement and degradation must be retained.

[local_runtime_probe.json](local_runtime_probe.json) records absent Torch and
Transformers. Cached Qwen weights alone do not provide an executable runtime.
Existing injected/mock adapters and the C001 key-position masking experiment are
not head interventions. No dependency installation, weight download, simulated
success or model call was substituted. OpenRouter's documented controls do not
expose an attention-head hook; a local implementation would need to instrument
the actual architecture, as illustrated by the model-specific interfaces in the
[Transformers GPT-2 documentation](https://huggingface.co/docs/transformers/model_doc/gpt2).
That interface is not assumed to apply unchanged to Qwen.

## Independent analytical review

Two Codex agents independently reviewed all five schema-valid final packets using
[blinded copies](blind_valid_packets.json). Copies omit arm, model and host verdict;
only the current prompt identity is redacted. Original provider bytes are untouched.
Reviewers knew the experiment design and earlier failures; writing style may also
reveal clues, so this is limited blinding. The remaining
25 final packets failed schema validation and were not given full analytical review.
Both reviewers found critical mathematical errors in every reviewed packet; prose
review is not a formal proof.

See [derivation review](derivation_agent_review.json) and
[execution review](execution_agent_review.json). These reports contain reviewer
calculations and must remain outside future participant guidance.

| Packet ID | Pilot | Agreed critical finding |
|:--|:--|:--|
| ddb2999c0858 | 199 | Two distinct fixture points were exchanged; required limiting and boundary arguments were missing. |
| bda4ed83a8d5 | 201 | Transport composition failed; the certificate contradicted the displayed cochain calculation; the eight-stage construction was missing. |
| 976d6966270f | 202 | Correct intermediate arithmetic was overwritten by unsupported normalization and values from a different carrier. |
| ed2b55be28a4 | 202 | Metric substitution, cochain quantities and degrees were incorrect; cosine differences replaced angular deficits. |
| cec995df7849 | 203 | Primal residual and dual annihilation/objective checks failed; a slogan replaced the terminal policy definition. |

Pilot 200 produced no schema-valid final in these comparisons. That is an output
contract failure, not evidence that its substantive derivation was solved or
impossible. All five task-specific mathematical goals in the earlier review remain
open. No score was repaired by weakening a predicate, changing a fixture or treating
typed refusal as full success.

## Next round's goals

1. **Shrink the public workpad.** Use a few short typed calculation records and
   open obligations, without duplicating the entire certificate before the final.
   Keep the same run caps and compare the final against a single shot. The eight
   truncated workpads motivate representation changes before more rounds or tokens.
2. **Make legal output easier to emit.** Reduce repeated metadata and clarify the
   exact row/array shapes. Where a cheap route supports it, separately test an
   actual output grammar. Keep host validation strict and record malformed output;
   format repair must not become a scored model success.
3. **Bind every certificate field to its own calculation and carrier.** Require
   named fixture inputs, matrix products and degrees to agree with the final field.
   Disallow unsupported normalization or assumptions that redefine fixed data.
   Apply this to transport, metric/cochain separation and primal/dual feasibility.
4. **Treat temperature and soft bias as secondary controls.** Neither produced
   finite success here. A later matched repeat must counterbalance order and retain
   all outcomes; do not choose a best temperature from these five tasks or launch a
   broad parameter grid. First fix the output contract and calculation consistency.
5. **Keep head testing conditional on a real verified runtime.** Execute the five
   specified cases only when actual hooks and identity controls are available.
   Pin architecture, weights, tokenizer, dtype, head/layer and activation evidence.
   Prompt emphasis or key masking cannot count as this mechanism experiment.

[learning_candidates.json](learning_candidates.json) records procedural candidates
derived from these failures, with evidence links. They are **UNADMITTED**. Before
promotion, each needs a new task instance, a correctness-preserving control and a
failure-provoking control. No fixture answer or reviewer numerical result belongs
in an antibody. No additional provider call is part of this closeout.

## Custody, budgets and replay

The source base is `5452a476dd88d05d19de60c3ea7e6607ac14ede0`. Runtime additions
were frozen before dispatch. [sources.json](sources.json) pins 23 runtime/problem
files; [source_snapshot](source_snapshot) retains their exact bytes. Existing
templates, original judges and the historical PO035 campaign were not changed.
The new experiment worker preserves decoding controls that the historical worker
did not forward. Every attempt retains prompt/request/raw reply/receipt/verdict,
negative-control results where applicable, and an SQLite budget ledger.

Each of the 15 runs shares its cap across all arms, rounds and host stages, without
reset or pooling. The largest paid run used USD 0.003869; the longest run took
99.766 seconds. Catalog discovery is separately recorded in dated public snapshots.
There were no retries, fallback calls or hidden extra samples. Of 40 finish reasons,
31 were stop and nine were length: eight workpads and one temperature variant.
There are 30 final/control packets and ten public workpads, not 40 final answers.

The retained compressed tokenizer permits offline logit-request reconstruction.
[Tokenizer custody](qwen72_tokenizer_custody.json) binds the full 7031645-byte file
to published Qwen revision `495f39366efef23836d0cfae4fbe635880d2be31` and SHA256
`c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539`.
Published tokenizer identity is checked; the hosted weight revision is not attested.

From the repository root, with the pinned source and Python dependencies present:

```powershell
.venv/Scripts/python.exe -m omega_engine_education.pilots.evidence.po035_experiments_20261012.replay
```

This uses the retained tokenizer in writable checkout scratch space. It does not
contact a provider, mock generation or change a judge. It verifies recorded sources,
requests, replies, verdicts, ledger accounting and the complete expected 15-run,
40-call inventory. Source drift or missing evidence fails closed; retained snapshots
allow recovering the original source bytes. Offline reconstruction does not promise
identical future hosted generations, even with a seed.

[replay.json](replay.json), [local_validation.json](local_validation.json) and
[closeout review](closeout_agent_review.json) record targeted verification. The 145
new scoped tests passed, as did the prior 25-call campaign's offline replay and this
40-call replay. Only targeted local checks were run; no full canonical CI or hosted
CI was started. [manifest.json](manifest.json) inventories retained evidence bytes,
excluding itself and interpreter caches.
