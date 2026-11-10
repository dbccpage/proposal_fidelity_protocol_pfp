# Research 02: finite detector adequacy and scoped immunity

Status: **proposed_not_evaluated**. Three proposed workflows extend EIS with finite controls and explicit coverage gaps. None treats detector agreement, a clean report, signed custody, support count or host-health receipt as mathematical truth. No paid model calls, seed solving, answer-key access or private benchmark storage access occurred.

The public seed was hashed without reading its contents. Its SHA-256 is `9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7`. Future answer-producing calls must carry its exact UTF-8 bytes as a separate unchanged message. A detector-induction call below is deliberately seed-free. Every workflow freezes its output before separate trusted scoring, and no private score, diagnostic, label or key-derived repair hint returns to the workflow.

## Evidence and method boundary

Negative selection is established prior art: detectors are screened against self before being used to identify changes. The proposed addition is a **finite sensitivity requirement plus untouched confirmation**, not a claim of general semantic immunity. [Forrest et al., 1994](https://profsforrest.github.io/homepage/data/publications/1994-self-nonself.pdf)

Metamorphic testing supplies a way to derive related tests when full oracles are unavailable. Here its proposed use is to challenge detectors with contract-valid variants and matched defect mutations. Each transformation still requires its own justified contract; similarity of wording is insufficient. [Chen, Cheung and Yiu, HKUST-CS98-01](https://arxiv.org/abs/2002.12543)

Selective classification studies coverage versus risk. That motivates measuring withheld guidance and missing coverage alongside errors. Its theoretical guarantees are not imported into this single-seed, finite-control setting. [El-Yaniv and Wiener, 2010](https://jmlr.org/papers/v11/el-yaniv10a.html)

The local source boundaries matter:

- `eis/domain/thymus.py:145-216` tests the active rule through its actual bound matcher. Passing establishes no hit on the supplied self fixtures only.
- `eis/use_cases/guard_activation.py:66-102` obtains external custody, executes the host danger sensor, uses the native activation path and requires host health. The domain's dispositions remain `FINDING`, `HOLD` and `REFUSE`; repair routing is a proposed separate benchmark scheduler.
- `eis/domain/allostery.py:1-25` is an exact threshold over a sum. Distinct capped sensor names are not statistically independent measurements.
- `eis/domain/provisional_promotion.py:95-178` computes support from a declared conflict graph. Missing correlation information cannot be manufactured by repeated model agreement.
- `eis/use_cases/research_memory.py:18-43` already provides scoped candidate guidance, while `eis/use_cases/regulate_guard.py:30-79` bounds optional-guard regulation and protects admission boundaries. The third proposal adds transfer checks and expiry.
- `eis/documentation/oeeis_residual_obligations.md:34-56` explicitly leaves detector completeness, observer independence and population error rates open.

## Proposed workflows

| ID | New composition | Model calls | Conditional maximum reservation |
|---|---|---:|---:|
| R02-I01 | Dual-panel negative selection plus minimum finite defect coverage | 2 | USD 0.037 |
| R02-I02 | Same-subject detector and host-failure evidence route one repair | 1–2 | USD 0.045 |
| R02-I03 | Expiring diagnostic memory challenged on paired transfer controls | 1 | USD 0.0345 |

These numbers are admission examples, using at most USD 0.000001 per input token and USD 0.000005 for each billable completion/reasoning token, zero extra endpoint fees and a USD 0.01 reserve. They are not current model-price quotations. At execution, a pinned OpenRouter or direct Anthropic endpoint must fit the full reservation under verified current pricing and token semantics. OpenRouter documents separate price fields, conditional overrides and completion limits; unknown charges or uncapped reasoning cause refusal. [OpenRouter model metadata](https://openrouter.ai/docs/guides/overview/models)

Disable retries, automatic fallback and paid tools. Reserve the conditional second call before starting. Include all instructions, prior artifacts and repeated seed tokens. Unknown usage stops the run. Any metered host computation must also fit the USD 0.10 aggregate ceiling.

### R02-I01 — Dual-panel negative selection with finite defect coverage

A seed-free proposer supplies at most twelve rules in a bounded AST detector language. The host runs the actual matcher over public benign controls and contract-invalid mutations, then enumerates at most 4,096 subsets. Choose the smallest subset with zero benign hits and complete coverage of every declared calibration defect family. If no subset satisfies that finite contract, record the coverage gap.

The selected subset is frozen before confirmation. Confirmation can invalidate it but cannot select a different subset. A second model call produces the task answer using a generic diagnostic schema. The final host report distinguishes findings, uncovered families, checker errors and no findings within the panel. It never emits a global correctness verdict from detector silence.

This goes beyond the existing self-only thymus screen by making a useless detector that never fires fail the sensitivity requirement. It also prevents a broad detector from looking effective merely by flagging everything. Controls may cover stale witness bindings, omitted required premises, sort mismatches and unjustified evidence-scope promotion. Labels concern the artifact contract; a malformed proof is not automatically a false theorem.

Compare against self-only screening and a fixed checklist. Falsify the proposed advantage if untouched benign hits increase, required families remain uncovered, or the answer loses correctness/completeness beyond a preregistered tolerance. Report denominators and template-level counts; many correlated rewrites are not many independent experiments.

### R02-I02 — Subject-bound two-signal repair routing

The first call produces a typed draft. A frozen diagnostic rule identifies a possible defect class. A separate deterministic host checker must produce a public failure witness bound to the same claim and current candidate bytes. Only the conjunction, with current health, allowed research scope, no suspension and reserved budget, can schedule one local repair.

All host failures remain visible even when the detector is silent. The gate allocates repair effort; it never turns an ungated draft into an accepted answer. Model-authored danger flags, repeated evidence under another observer name, stale candidate hashes and missing host-health evidence cannot trigger repair. Mathematical signal classes outside EIS's current closed registry need an explicit versioned adapter.

Test all four detector/danger combinations and inject copied, mismatched and stale receipts. Compare with unconditional critique, detector-only repair and host-failure-only repair. If host-only routing is as effective and cheaper, the detector adds no demonstrated value. Recheck affected dependencies after a patch and retain all unresolved obligations. Structural separation does not prove statistical independence, and a local predicate pass does not prove the whole derivation.

### R02-I03 — Expiring diagnostic memory with paired transfer challenges

Each public generic memory receives a lease bound to its scope, parser, actual matcher, control grammar and expiry rule. Before reuse, the host checks a defect reproducer and nearby contract-valid controls under frozen transformations. A version change, expiry, missed reproducer or benign hit makes the entry inactive for that run. Historical entries and failure reasons remain available; production admission stays untouched.

Inject at most three active, solution-free obligations into one answer-producing call. Duplicate or inherited reports cannot boost support, and missing lineage is unknown correlation. No prior paid induction is hidden outside the budget: the initial registry is deterministic, public and independent of seed solutions or private evaluator feedback.

Compare with always-on retrieval and no memory. Measure guidance-induced errors and useful reminders together with answer coverage and abstention. Expiring every rule is not a successful immunity result. The proposal fails if stale or benign-triggering guidance reaches the model, if duplicate evidence raises an independence claim, or if withholding guidance reduces utility without improving benign preservation or correctness at comparable coverage.

## Reusable primitive and evaluation limits

The recommended primitive is **FiniteDetectorAdequacyLeaseV1**: a host-issued receipt binding detector/matcher/parser hashes, three control partitions, finite benign and defect counts, uncovered families, optional same-subject host evidence, and expiry. It deliberately has no universal correctness bit. Canonical byte digests avoid relying on the audited tolerance-equality/hash behavior of current detector value objects.

Start with host-only tests for inactive-rule vacuity, all four two-signal cases, matcher drift, stale subjects, duplicate lineage and lease expiry. Then a separately authorized one-call memory pilot provides the smallest paid experiment. The detailed typed inputs, stage instructions, baselines, falsification rules and budget formulas are in [research_02.json](research_02.json).

Development, calibration and confirmation must be fixed before induction. Repeatedly selecting on confirmation makes it development data even if it is public and unrelated to the secret key. A fresh confirmation family is then required. Repeated trials on one benchmark seed support instance-specific comparisons only; they do not establish general error rates, semantic detector completeness or durable immunity. No workflow implementation, host experiment or paid evaluation is claimed here.
