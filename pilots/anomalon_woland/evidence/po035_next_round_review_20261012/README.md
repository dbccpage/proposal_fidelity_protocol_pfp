# PO035 final-prompt review and next-round goals

AuthorityEffect: None. Review complete. The neutral/guidance screen below remains
**PLANNED**. The subsequent user-requested scratchpad, temperature and logit
comparisons are [complete](../po035_experiments_20261012/README.md): 15 test runs,
40 calls, no accepted finite certificate. Five head-intervention cases are defined
but execution is unavailable in this environment.

Three Codex agents independently reviewed all five frozen `reviewed-v4` prompt
containers, their actual system/user strings, and the recorded failures. The next
goal is to improve single-shot results on the same substantive tasks with a cheap
model. Preserve the original seeds and independent judges. Correct the shared
prompt contract before measuring the effect of procedural guidance.

The source revision is `5452a476dd88d05d19de60c3ea7e6607ac14ede0`.
[review_receipt.json](review_receipt.json) pins the five containers and evidence;
[round_contract.yaml](round_contract.yaml) defines the proposed bounded experiment.
This review supersedes the earlier recommendation to dispatch frozen v4 unchanged;
all earlier prompt bytes, verdicts and raw replies remain historical evidence.

## What the evidence establishes

The [completed campaign](../po035_derivations_20261012_v2/README.md) made 25 calls:
three packets passed schema/identity validation, zero finite witnesses passed, and
no analytical derivation was certified. The other 22 packets failed JSON, schema
or identity checks. There have been **zero unchanged trials of the five frozen
final prompts**; the expanded comparisons used corrected, versioned prompts built
from the same seeds and unchanged independent judges.

Every historical reply has `finish_reason=stop`; none has `length`. Completions
ranged from 879 to 2417 tokens, averaging 1651.36. Raising the 2500-token output
ceiling has no current evidential justification. Pilot 201 averaged 2342.8 tokens,
so directing output toward the derivation rather than repeated learning metadata
is a useful hypothesis to test. These observations do not prove that prompt size
caused the failures.

## Required corrections before another call

1. **Resolve the system/user conflict.** The system forbids importing continuous
   physics and differential geometry without a mapping from the 38 primitives.
   User-level licenses do not override it. Create a versioned system-scope PO035
   variant that identifies the finite carriers and explicitly permits named
   external analytical assumptions as conditional premises. Preserve the base
   template and hash both it and the rendered variant. Do not claim those premises
   were derived from the symbol grammar. Use this same variant in both arms.
2. **Supply missing problem input and authoritative clarifications.** Pilot 201
   needs a pinned excerpt containing all eight stages of paper section 5, labeled
   disputed claims to repair. Pilot 202's seed calls `d1*d0=0` "exactness"; a
   versioned clarification must call it the complex identity. Keep the original
   seed verbatim, and place clarifications outside untrusted candidate guidance.
   Resolve the task-specific notation issues listed below identically in both arms.
3. **Make this a fresh single shot.** Remove the instruction to revisit a previous
   loop: all five final contexts have a null previous proposal. Generate a new
   prompt ID and one strict SPK response, with no old reply, feedback or loop ID in
   the model-visible context. Preserve the full schema and fixture predicates.
4. **Use task-scoped licenses.** Historical carried grants are irrelevant or
   incomplete: 201 lacks `FIBER_CONNECTION`, 202 lacks `INTRINSIC_METRIC`, and 203
   lacks `OPERATIONAL_POLICY`. Supply the declared licenses before dispatch in
   both arms; archive historical grant chains outside the wire payload. Permission
   to assume a hypothesis never changes a fixture or establishes that hypothesis.
5. **Remove outcome disclosure and compact the wire payload.** Pilot 200's selected
   antiskill `pilot_0000200:v2:loop03:antiskill:04` says the fixture demonstrates
   balance without global conservation. Exclude that conclusion from future
   guidance, keeping its historical record. Retain only a few procedural lessons,
   with fresh alias/kind/text/authorship visible; bind aliases to historical IDs,
   receipt paths and hashes in a
   sidecar. Request one useful learning item, satisfying the existing schema,
   rather than spending output on all five kinds. Perform further mining offline.

The system string is 3716 UTF-8 bytes per final prompt. User strings are
15351-17389 bytes. Repeated guidance lineage is avoidable wire overhead; byte
measurements are in the receipt and are **not token counts**. Do not promise
token savings until new usage receipts measure them. The saved provider catalog
does not advertise grammar or `response_format` support; strict typing here means
host validation, not provider-enforced constrained decoding.

## Five goals and acceptance obligations

These are reviewer goals, not model results or participant answer keys. No expected
fixture values or reviewer-derived solution equations may enter future guidance.

| Pilot | Observed failure and common clarification | Next single-shot goal |
|:--|:--|:--|
| 199: causal refinement | Mixed lattice pitch with spacetime dilation, confused the two fixture points, and treated an upper bound as propagation evidence. Define `cone_order_preserved` as invariance of the homogeneous cone relation, not membership of the displayed point. Specify interval sign and dilate space and time with speed fixed. | Pass every original finite predicate. State uniform prefactor/decay and physical velocity/time/norm assumptions; justify suppression at a strict outside-cone margin; analyze null-boundary convergence rates; separate causal order, metric scale and isotropy. Identify any unproved scaling-limit or inside-cone claim. |
| 200: microscopic current | Incorrect matrix-vector arithmetic, stationary-state assumptions and complex/scalar shapes corrupted the balance. State that P is fixed; use H as the homogeneous reference generator for the residual-only balance, and fix the incidence/divergence sign convention. | Pass the unchanged noncommuting fixture. Derive projected residual dynamics, flux and source with a consistent local balance; determine total-density behavior from arithmetic; state sufficient conservation hypotheses separately and the estimates a continuum limit would require. |
| 201: relational spine | Missing eight-stage input, wrong fiber domains, failed transport composition and conflated identity/nonflat controls. Supply all stage definitions; declare the orientation convention consistently despite the paper's sign convention. | Pass composition, direct transport, covariant difference and identity-repair predicates. Give actual objects/morphisms/identities/composition and the construction or added premise at every stage; distinguish free paths from quotient relations, type the curvature correction and its basis behavior, and state remaining compression/higher-cell obligations. |
| 202: metric/cochain bridge | Invented witness values overrode arithmetic; quotient degree, exactness and metric deficit were conflated. State that `curvature_before/after` mean `d1*delta` and `d1*delta_prime` on the separate triangle; deficits belong in analytical prose. | Pass all exact cosine, cochain and degree predicates. Type the induced quotient map and identify its kernel; retain the intrinsic metric counterexample and symbolic deficits; distinguish the complex identity from exactness/Bianchi laws; formulate a conditional intrinsic piecewise Euclidean Levi-Civita bridge with nondegeneracy, canonical edge matching, orientation and angle branch. Do not infer it from metric compatibility alone. |
| 203: obstruction and halting | A dual failed annihilation; the matrix norm replaced the residual objective; a Boolean flag stood in for a policy. Prelicense an explicit operational policy, without implying arbitrary dynamics halt. | Pass exact primal/dual feasibility and equal-objective predicates without a tolerance shortcut. Give weak duality and finite attainment assumptions, an unbounded continuing transition system, and a separate certificate-checking transition to an absorbing terminal state. Keep physical interpretation conditional on a measurement model. |

## Bounded next experiment

Propose **at most 10 fresh provider calls in five pilot runs**: one neutral and one
filtered-guidance call for each unchanged seed. Both arms use the same corrected system variant,
problem context, clarifications, licenses, schema, judges, model route and decoding.
Only the guidance bundle and necessary unique prompt IDs differ. This isolates the
bundle's effect on this scaffold, not individual antibodies or model-versus-reviewer
authorship. Frozen v4 is an audit reference, not a third experimental arm.

Use one eligible cheap route for the first screen. The historical route was
`nvidia/nemotron-3.5-lightning:free`; its availability and prices must be verified
again before future dispatch. Prefer verified zero price, reserving conservatively
for any paid route. Do not spend another dimension on a stronger model yet.
Keep temperature zero, the paired seed, reasoning setting and 2500 output ceiling
fixed. Counterbalance arm order, use stateless requests and retain every response.
No retry, JSON repair, feedback turn or cross-arm output is a scored single shot.

The hard ceilings remain **USD 0.05, 120000 total provider tokens and 180 seconds
per pilot run**, shared across its two arms and host stages, with no per-arm reset.
Reserve both arms before the first dispatch and give them symmetric deadline
allowances within the shared interval. Catalog discovery is separately bounded and
reported. Five proposed runs therefore have a worst-case aggregate ceiling of
USD 0.25, 600000 tokens and 900 seconds sequentially; these are not expected
charges or a claim that the whole round fits inside USD 0.05. Stop for missing
cost/usage, uncertain reservations or any cap failure. Do not increase a cap.
An undispatched or incomplete second arm is a censored pair, not model failure or
guidance loss. Report arm order, resources remaining and the reason; never retry,
reset the budget or pool budgets across tasks to complete it.

Score strict JSON/schema/identity, exact finite acceptance and analytical obligation
coverage separately. Two independent Codex reviewers, blinded to arm, judge the
analytical checklist; disagreement remains unresolved, never silently accepted.
Human/agent prose review is not a formal proof. Report syntax-only improvement as
syntax-only improvement. Record typed refusal, mathematical errors, missing
obligations, infrastructure errors and observed truncation separately. Deterministic
host checks are not extra model trials.

The desired first-screen outcome is at least two additional joint schema-plus-finite
successes among five guided tasks, no losses on tasks the neutral arm solves, and
no new critical analytical error. Report the actual analytical gains separately;
full task success additionally requires every essential obligation satisfied.
Mark each obligation satisfied conditionally, missing, critically wrong or
unresolved. A precise admission that a central requested construction is unresolved
is useful partial work, not full task success. Correctly stating the requested
limits of broader physical or continuum claims does not count as a missing result.
This is an engineering decision threshold, not statistical evidence of reliability.
Stop after ten calls regardless. A positive result would justify proposing one new
paired seed block for confirmation; repeats and a second model are separate work.

If both arms fail parsing, simplify the shared contract further. If they parse but
fail mathematics, change representation or procedural guidance while keeping the
judge strict. If guidance produces no gain, retain that negative result instead
of adding more hints or loops to the same scored attempt. Admit no new antibody,
skill or rule automatically; require preserving and failure-provoking controls on
a new task instance before any later promotion.

The additional user-requested scratchpad, temperature and mechanism test cases are
defined in [experiment_matrix.yaml](experiment_matrix.yaml). This matrix preserves
the planned specifications; measured status and outcomes are in the
[executed report](../po035_experiments_20261012/README.md) and
[results](../po035_experiments_20261012/results.json). These are separate bounded
comparisons; multi-round work is reported separately from single-shot performance.

## Review custody and local validation

- `po035_derivation_review`: task definitions, mathematical obligations and answer
  disclosure.
- `po035_closeout_review`: actual payloads, system priority, source context,
  license scope and reproducibility.
- `po035_execution_review`: failure receipts, finish reasons, budgets, matched
  design and separated outcomes.

The original review produced this report and plan. Subsequent authorized work added
versioned experiment rendering and orchestration, dispatched the available matrix,
and retained every reply. Existing templates, historical evidence and independent
judges remain unchanged. See the executed report for source pins, targeted local
validation and offline replay. No full canonical CI was run.
