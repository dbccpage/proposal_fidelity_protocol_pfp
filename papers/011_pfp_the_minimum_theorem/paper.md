# PFP shape, review findings, and the next test campaign

Reviewed source: `5e049cdea667d80cece90f72b9d407e6acddf31d` (2026-10-05 UTC).  
Status: finite derivation, reproduced review findings, and proposed tests.  
AuthorityEffect: None. GenesisEffect: None. Production readiness: NOT ESTABLISHED.

The strongest defensible shape of PFP is a typed graph of proposals and checked transformations that preserve the distinctions required by a declared task. Model stages search for candidates, witnesses, repairs and counterexamples. The host owns admission, independent replay and any permission to act. A representation is useful only relative to the questions it preserves; a completed stage sequence supplies no missing evidence.

This review produces two execution specifications, not records of new model runs:

- Demo 001, rounds 26–100: harden the existing calculus family and its execution boundaries.
- Demo 002, rounds 1–100: extend the existing finite-codec exercise into a direct test of query preservation, composition and custody.

The second family comes from the controller's identity/collision example and SG-07 in the stage-driven catalog. It does not introduce a new engine architecture. `DEMO001/R026` and `DEMO002/R001` are campaign identifiers; they do not rename the older PFP25, PFP50 or SG catalogs.

---

## 1. What the current demo actually establishes

The Demo 001 index correctly identifies rounds 1–2 as hand-built/dry-run artifacts. The canonical `rounds_03_20/round_*/live_runs/receipt.json` paths contain 18 records: 17 with provider generation IDs and one host-only Stage 5 record. Copies under a model name and `round_NN_receipt.json` are aliases, not additional trials. This review inspected deposited records; it did not independently verify provider billing or repeat those calls.

The exact reference checker has ten passing local self-test fixtures. Its substantive distinction is useful: an endpoint difference of 50 does not establish that a submitted polynomial differentiates to the original integrand. The canonical round-17 receipt rejects the submitted witness for that reason. That rejection is a successful detection, not a solved episode.

Some catalog prose has drifted from the canonical receipts: round 14's root receipt counts six candidates, while the directory catalog says seven; round 5's root Space Bunny receipt is `invalid_witness`, while the catalog describes Space Bunny acceptance. Historical/model-specific observations must be identified by their own artifacts rather than combined into a single favorable result.

Only rounds 1–20 are present under `demo_001` at the reviewed commit. Rounds 21–25 are not observed on this main revision. The requested continuation starts at 26 without inventing their results or treating them as dependencies. Record any separately supplied 21–25 run IDs before incorporating their evidence.

The separate staged implementation report reports broader local SG fixtures and explicitly incomplete live coverage. Those reported counts are neither fresh measurements by this review nor executions of these 175 proposed rounds.

---

## 2. Reproduced blockers before scaling

These findings apply to the standalone Demo 001 runner, not automatically to every PFP execution path. The shared stage pipeline calls schema parsing and stage semantic validation, preserves candidate routing and uses host-owned evaluation. Reuse that path through its existing ports; do not copy the demo runner into another permissive production path.

| ID / priority | Evidence at the reviewed source | Consequence | Required regression |
|---|---|---|---|
| F01 / high | `run_host_replay` falls back to the nested proposal when `decode_stage4` returns no mathematical receipt. An envelope containing only `candidate.proposal` gets `invalid_extraction`, then `checked_accept` from the fallback. | A correct inner witness launders a rejected outer contract. The extraction failure is not retained in the emitted evaluation. | D001/26: preserve the refusal and make zero downstream checker calls; paired complete, routed extraction passes. |
| F02 / high | `topology_fields(11, …)` checks length and ordered IDs. A two-node cycle P0→P1→P0 is marked `checked_accept`. `_family_of_four` checks only count and membership of P2/P3. | IDs and counts do not establish roots, parent existence, acyclicity, batch semantics or execution dependencies. | D001/56–60 and D002/26–30. |
| F03 / high | `p1_member_from({})` fabricates a default P1; `lineage_summary({})` reports stages 1–7 completed. Cached round receipts are loaded without validating the complete current source/profile/checker lineage. | Missing dependencies can become invented input or completion evidence. | D001/28–29, 58, 91–93. |
| F04 / high | `call_spec` puts the schema in the prompt but does not validate returned JSON against it. `parse_strict` converts failure into an ordinary dictionary; count-based handlers then continue. | Parsing, schema validity and stage admission are conflated. | D001/27, 46–50; route through existing schema/semantic validators. |
| F05 / medium | The calculus checker accepts a counting problem with `points: "12"`, `values: ["1","2"]`, claimed value `"3"` and its matching input digest. | Iteration over a string supplies two points despite the required array shape. Digests bind malformed data too. | D001/30, 36–45: validate the host problem independently before arithmetic. |
| F06 / medium | `dispatch_model_round` strips raw content, `call_spec` drops the raw/normalized distinction, and `save_round_output` overwrites round/model paths. A direct-call exception triggers another provider path; that direct path sets cost to 0. | The runner cannot establish immutable raw-byte custody, one-attempt billing, or complete history from those records alone. | D001/86–95; append attempts and track unknown costs explicitly. |
| F07 / medium | The round catalog, Mode 14 prose and antibody headings sometimes describe hand-built or observed artifacts as empirical/verified results. | Status prose can overstate the evidence it summarizes. | Bind every assertion to artifact type and immutable identity; D001/100, D002/99–100. |

### Offline reproduction

Run this from the repository root. It imports no provider and writes only to a temporary directory. It records the current failures; these are not desired acceptance outcomes.

```python
import contextlib, io, json, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path("ow/omega_engine_pfp_v0.2/demo_001/rounds_03_20/code").resolve()))
import calculus_reference_check as c
import run_live_round as r
problems, fixtures = c.fixtures()
malformed = {"candidate": {"proposal": json.dumps(fixtures[0][2])}}
print(c.decode_stage4(problems["real"], malformed)["status"])
with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
    replay = r.run_host_replay(Path(tmp), malformed)
print(replay["mathematical_receipt"]["status"])
family = {"members": [{"prompt_id": "P0", "parents": ["P1"]},
                      {"prompt_id": "P1", "parents": ["P0"]}]}
check = r.topology_fields(11, lambda members, ids: len(members) == 2 and ids == ["P0", "P1"])
print(check(family, SimpleNamespace(model="offline_probe"))["host_assessment"]["status"])
print(r.lineage_summary({})["stages_completed"])
print(r.p1_member_from({})["prompt_id"])
p = dict(problems["counting_half_open"], points="12")
w = {"profile_id": c.COUNTING, "input_sha256": c.canonical_sha(p),
     "method": "complete_enumeration", "values": ["1", "2"], "claimed_value": "3"}
print(c.check(p, w)["status"])
```

Observed output: `invalid_extraction`, `checked_accept`, `checked_accept`, `[1,2,3,4,5,6,7]`, `P1`, `checked_accept`. No runtime fixes are claimed by these planning documents.

Reproduction environment: Python 3.12.14; the command above exits 0 because it records observations rather than asserting the desired future behavior. Tested scope is the two imported standalone modules and their fixtures at the reviewed commit. The reference self-tests were also run with `python ow/omega_engine_pfp_v0.2/demo_001/rounds_03_20/code/calculus_reference_check.py self-test` under Python 3.12.14, exit 0: all ten fixture expectations matched. Those ten cases do not cover the malformed-host and outer-contract failures above.

### Theoretical minimum and an inspected mutation target

| Obligation | Concrete witness / target |
|---|---|
| INVARIANT | A checked result concerns the original admitted query and eligible candidate; every representation fiber preserves the protected observation. |
| BREAK | B merges a,b under source identity; a held Stage 3 candidate reaches Stage 4; an invalid outer extraction is bypassed. |
| WITNESS | Retain the separating source pair, the exact held candidate/audit, or the malformed extraction plus the observed fallback receipt. Include the corresponding valid query/route/envelope control. |
| MUTATION | Remove `EXTRACTION_NOT_AUDIT_ADMITTED`'s guard from an in-memory copy of `python/domain/stage_semantic.py::validate_stage`. D001/49 and D002/32 must detect the resulting false admission. This is an existing runtime source target, not a fabricated mock success. |

The following isolated guard experiment checks the actual source function and its in-memory mutant. It does not edit production files or exercise the whole pipeline. Python 3.12.14, exit 0; observed original: `held=False, eligible=True` and guard_removed: `held=True, eligible=True`. Thus a regression asserting rejection of a held route detects this mutation while retaining useful acceptance. The broader campaign mutations remain planned.

```python
from pathlib import Path
path = Path("ow/omega_engine_pfp_v0.2/python/domain/stage_semantic.py")
source = path.read_text(encoding="utf-8")
guard = ('        if reply["candidate_id"] not in ids:\n'
         '            raise ValueError("EXTRACTION_NOT_AUDIT_ADMITTED")\n')
assert source.count(guard) == 1
demo = {"id": "DEMO002_TEST", "profile": "finite_test", "seed": "a b c"}
reply = {"demo_id": demo["id"], "derived_under_policy": "SPK-001",
         "stage": 4, "authority_effect": "None", "coefficient_profile": demo["profile"],
         "candidate_id": "B", "missing_fields": [], "source_quotes": ["a"]}
for name, code, expected_held in (("original", source, False),
                                ("guard_removed", source.replace(guard, ""), True)):
    namespace = {}
    exec(compile(code, str(path), "exec"), namespace)
    results = []
    for route in ("hold", "extract"):
        prior = {"stage_3": {"audits": [{"candidate_id": "B", "routing": route}]}}
        try:
            namespace["validate_stage"](demo, 4, reply, prior)
            results.append(True)
        except ValueError as error:
            assert str(error) == "EXTRACTION_NOT_AUDIT_ADMITTED"
            results.append(False)
    assert results == [expected_held, True]
    print(f"{name}: held={results[0]}, eligible={results[1]}")
```

---

## 3. PFP-Shape-01: task-relative fidelity and checked composition

### Declared objects

Let $X$ be a finite, nonempty host-declared set of admitted source objects or interpretations. Let $Q = (q_1,\dots,q_k): X \to Y$ be the tuple of protected task queries, and let $e: X \to Z$ be a total proposed encoding on $X$. $Y$ may contain tuples, exact values, or complete answer sets; it need not force a single answer when the task admits ties. The host must supply decidable equality for the observations being compared.

Finiteness makes the following checks enumerable. It does not establish that $X$ exhausts the meanings of arbitrary natural language. Source extraction, the choice of $X$, query adequacy and admission remain explicit obligations.

### A. Exact static criterion [PROVED]

There exists a decoder of the protected observations, $d: e(X) \to Y$, satisfying

$$d(e(x)) = Q(x)\quad\text{for all }x\in X$$

if and only if

$$e(x)=e(x')\quad\Longrightarrow\quad Q(x)=Q(x')\quad\text{for all }x,x'\in X.$$

*Derivation.* Necessity follows by applying $d$ to equal encodings. For sufficiency, define $d(z) = Q(x)$ for any $x$ with $e(x)=z$. The implication makes this definition independent of the chosen representative. The decoder is needed only on the attained image $e(X)$; no value is invented for unattained codes.

This is the standard factorization-through-a-quotient argument, written here in PFP terms. No novelty in that elementary result is claimed.

*Consequences.*

- A violating pair $(x,x')$ is a finite, independently replayable fidelity obstruction. Refinement or refusal is required for that protected query. Good syntax cannot remove the obstruction.
- Full source reconstruction is the special case $Q(x)=x$. It requires injectivity. Query preservation may permit a coarser encoding, but it does not authorize changing an identity-preserving contract into a query-only contract.
- The unique coarsest task-sufficient partition groups exactly equal $Q$ values. Thus any sufficient representation needs at least $|Q(X)|$ attained codes; encoding by $Q$ attains this lower bound. Alphabet size alone says nothing about bit length or runtime cost.
- Adding a protected query can split previously adequate classes. Adequacy must be rechecked under the new query set.
- Starting with $b$ partition blocks on fixed $X$, any process that only splits blocks makes at most $|X|-b$ strict refinements. This does not bound model calls, repeated non-refining proposals, or changes to $X$.
- *Demo 002 witness.* Take $X=\{a,b,c\}$, $e(a)=e(b)=x$, $e(c)=z$. Under byte identity, $(a,b)$ witnesses failure. Under the separately admitted query $q(a)=q(b)=0$, $q(c)=1$, the same encoding preserves $q$ with $d(x)=0, d(z)=1$. Adding the query "is the source $a$?" makes it inadequate again. Both acceptance and refusal depend on the bound query contract.
- *Demo 001 interpretation.* A representation that erases the declared real/counting profile can identify tasks whose results are 50 and 55. It cannot recover both requested observations. This does not imply that the original English calculus sentence is ill-typed: ordinary calculus conventions yield 50. SPK-001 separately requires explicit declarations. Domain, measure, endpoints and protected claims must remain bound throughout a transformation.

### B. Pipeline preservation [PROVED under the stated equations]

For a finite admitted path of partial maps $f_i: X_{i-1} \rightharpoonup X_i$, require each evaluated input to lie in the declared domain and require

$$Q_i(f_i(x))=Q_{i-1}(x).$$

Then the composite preserves the original protected observations. This follows by substituting the equations successively. In a dependency DAG, induction in topological order gives the same statement only when joins check the shared context and reconcile their protected observations. Two locally valid branches about different problems do not compose by sharing a schema or equal scalar.

A changed carrier, policy, query, mode capability or interpretation starts a separately admitted context with its own comparison obligation. It is not an unannounced edge in this theorem. A partial map's failure remains failure unless a new input/candidate is explicitly submitted.

### C. Host acceptance [CONDITIONAL]

Suppose the implementation also enforces all of the following:

1. Bind the actual source, problem, candidate, profile, policy, checker version and dependency artifacts; resolve referenced content, not just digest-shaped strings.
2. Check every used edge/domain/join obligation and all stage prerequisites. Rejected outer contracts cannot be bypassed by rechecking an inner payload.
3. Use an independent checker $V$ whose acceptance is sound for the declared mathematical relation on that bound input and witness.
4. Keep proposal, checked evidence and action authorization in separate host-owned states. Any consequential action requires a separate applicable host permission.

Then a terminal checked result is sound for the original admitted task under those assumptions, regardless of which proposer or proposal-generating mode produced its witness. Substitution of the path-preservation equations transfers $V$'s conclusion to the original task; the authority-state rule supplies no model-created permission.

The current demo does not discharge these implementation premises: F01–F06 are concrete gaps. This theorem also does not establish checker completeness, eventual solution, optimal search, unbiased admission, natural-language adequacy, physical truth, or production reliability. A system that refuses everything can satisfy a no-false-acceptance condition while being useless. Valid controls and useful completion rates must therefore be measured separately.

The WDP Appendix S addresses a richer finite progress/game model. This derivation does not import its optimal-cost, trap or dynamic quotient claims. Preserving a static query is insufficient to preserve future enabled actions, successor observations, winning regions or costs; those need additional transition-level contracts.

*Related work added during this review.* Main advanced to `0d55379635a98d0e2895fc5d89251b7205ba571f` without changing the reviewed PFP subtree. Its finite observation supplement uses the same fiber-constancy criterion and adds explicitly priced measurements. Its faithful representation supplement adds accepted-witness transport, forward coverage and fair-search assumptions. Reuse those scoped results where their hypotheses match. This review read those supplements but did not rerun their evidence or Lean modules. In particular, the reported use of `Classical.choice` in an augmentation proof is outside Mode 09's current whitelist; do not treat every WDP proof as an automatically admitted Mode 09 certificate.

---

## 4. Stages and modes: the obligations that matter

The controller declares eight stages, including a host-only Stage 5. A round is an experimental unit; it is not a new stage number.

| Stage | Required distinction | Acceptance work |
|---|---|---|
| 1 admission proposal | finite syntax/equality versus intended interpretation | Host checks supplied declarations; missing declarations block dependent execution. |
| 2 ideation | diversity versus renamed copies | 5–7 distinct IDs/statements, a refutation/weakening and two mechanically checkable routes; these remain proposals. |
| 3 audit | original claim versus repaired claim | Cover each original candidate once; validate quoted source and routing. |
| 4 extraction | typed payload versus a new problem | Preserve admitted candidate/profile; explicit missing fields, no silent replacement. |
| 5 evaluation | independently replayed witness versus expected answer | No LLM call. Preserve extraction failures and actual checker exceptions distinctly. |
| 6 adversarial | challenge proposal versus verified refutation | Bind original target and replay each challenge independently. |
| 7 countermodel | refinement versus changed claim | Validate challenge index and target; minimality needs a declared ordering and smaller-case census. |
| 8 evidence plan | summary/next-seed proposal versus completed execution | Derive status from actual receipts. Diagnostic-only continuation cannot certify a failed lineage. |

The twenty mode contracts describe capability requirements. Their names and `fail_closed: true` fields do not establish implementations. The new plans give every mode an explicit test, including a typed unavailable result when the capability is absent.

| Mode | Review boundary / required correction in an implementation | Primary planned rounds |
|---|---|---|
| 01 glyphs | Select a named grammar; replay DDC states separately. Eight letters alone are not a transition checker. | D002/36, 46–50 |
| 02 envelopes | Check content and custody as well as digest shape; retain raw and normalized artifacts separately. | D001/54–55; D002/36–40 |
| 03 steering | A prose grammar instruction is not a logit mask, KV hook or attention intervention. Demand backend capability evidence. | D002/51–55 |
| 04 antibodies | A matched pattern is not a sound rejection predicate for every matching case; include scoped valid controls and transfer conditions. | D001/66–68; D002/56–59 |
| 05 skills | Type/arity/DAG checks and extensional behavior of the actual composition; declared associativity is not a run. | D002/61–65 |
| 06 scratchpad | Request public certificates/intermediate artifacts. Do not claim visibility into unavailable private model reasoning. | D001/80; D002/54 |
| 07 symmetry | Declare each group action and transport all inputs/queries. Permutation parity alone does not force every observable's sign. | D001/72; D002/66–68 |
| 08 involutions | Enumerate the declared finite map, fixed points, magnitudes and signs; no conclusion about undeclared physical sectors. | D002/69–70 |
| 09 Lean | Target statement, compiled source/dependencies and axiom census all bind. The current whitelist is `{propext, Quot.sound}`; changes need a new contract. | D002/71 |
| 10 cemetery | Pin checker/policy and compare stable verdict evidence, not timestamps. A checker correction may legitimately reverse a historical false refusal. | D001/69–70; D002/60 |
| 11 tribunal | Traversing gates cannot substitute for checker evidence; scoped refusal is a legitimate test result. | D001/84; D002/76 |
| 12 geometry | Dimension-correct volume, incidence and angle semantics are independent obligations. | D002/72 |
| 13 normal forms | Bounded saturation does not establish termination/confluence for arbitrary rules or a unique 6NF with every dependency preserved. | D002/81–83 |
| 14 refusal | Preserve problem/candidate state; append a refusal record. Literal immutability of every ledger would prevent recording the refusal. Mode prose must not relabel hand-built round 1 as empirical. | D001/26–30; D002/49 |
| 15 interface | Render actual receipt status and bound state; a display is not another authority source. | D001/81; D002/84 |
| 16 perturbation | Define a measurable finite boundary invariant and perturbation distribution. Ten trials are not a general cognition result. | D001/82; D002/85 |
| 17 consensus | Independent receipts, target identity and contradiction handling; votes alone give no evidence upgrade. | D001/83; D002/77–78 |
| 18 MUB | Exact algebraic fixture or capability refusal; approximate orthogonality and a finite trial do not settle the full dimension-six problem. | D002/73 |
| 19 first cut | Treat this as an explicitly declared realization exercise. The contract's "ungrounded void" and marked pair cannot silently import extra Genesis primitives. | D001/85; D002/74–75 |
| 20 debate | Mechanized witness evidence and bounded continuation; neither eloquence nor majority is a checker. | D002/79–80 |

No $20\times 8$ Cartesian matrix is claimed. Mode/stage incompatibilities are themselves recorded; they are not patched with invented semantics.

---

## 5. The path beyond one million tests

Planned first expansion: 1,200,000 distinct offline cases. Executed by this change: zero campaign cases. The small review probes above are separate and must not be relabeled as campaign execution. These budgets are allocation targets, not a claim that all required generators or adapters exist.

| Family | Planned cases | Generator and independent expected relation |
|---|---|---|
| Demo 001 exact mathematics | 400,000 | Canonical rational polynomials of integrand degree 0–7, rational endpoints and explicit integer sets of size $\le 100$; constants, endpoint swaps, derivative-preserving shifts and witness mutations. Compare coefficient differentiation and a separately implemented termwise integration/enumeration oracle. |
| Demo 002 finite query/codec maps | 250,000 | Enumerate small carriers, total/partial maps, partitions and protected-query tuples; exhaust bounded small classes, then use frozen seeded selections for sizes 5–6. Check every fiber or retain an explicit separating pair. |
| Packet/grammar/type controls | 200,000 | Valid serialized artifacts paired with duplicate-key, scalar/array, Unicode, framing, rational-canonicality and size mutations. Expected results come from the named grammar/type contract. |
| Stage and ancestry handoffs | 150,000 | Small acyclic DAGs plus controlled cycle, missing-parent, stale-reference, candidate-transplant, routing and join mutations. Independent graph/context oracle; zero dispatch when prerequisites fail. |
| Mode, adapter and antibody scope | 100,000 | Compatible mode/profile combinations, transfer controls, query-changing adapters and known-good survivors. Missing capability is counted as blocked coverage, not a successful mathematical verification. |
| Storage and concurrency faults | 75,000 | Controlled interruption at each durable-write boundary, duplicate delivery, stale reads, cancellation and competing append operations. Compare committed state with an independent operation ledger. |
| Provider envelope simulations | 25,000 | Stubbed provider outputs: truncation, null/empty content, bad usage, timeout after possible dispatch, response-ID collision and incomplete billing. No paid requests in this allocation. |
| **Total planned** | **1,200,000** | **Report executed, unique, passed, failed and blocked counts separately.** |

Each instantiated case needs `(round_id, family, generator_version, semantic_input, mutation, expected_relation, oracle_version)` and a stable content identity. Repeated aliases, retries, renamed IDs and copied receipts do not increase the unique-case count. Stochastic repeats may measure variability, but have their own replicate count. Deduplicate after the declared semantic normalization, retaining exact bytes where bytes are the tested property.

Each rejection family needs valid controls; each passing family needs targeted invalid controls. Track false accepts, false refusals, unsupported-capability rates, checker exceptions, replay disagreement, detection by fault class, and resource use. Mutation operators themselves need checks: a labeled "invalid" mutant may still be valid. Reduce unexpected failures and preserve them; do not train only on a fixed answer key.

Separate generator-development cases, held-out structural families and live evaluation. Pair baseline and PFP on the same admitted task and checker, recording policy refusals independently from mathematical errors. The 50/55 policy comparison is not evidence that ordinary calculus failed.

A million correlated tests supplies no distribution-free production guarantee. Under a separately justified independent identically distributed sampling model, zero observed failures gives the usual one-sided 95% bound $1-0.05^{1/N}$ on that distribution's failure probability. That bound does not apply automatically to mutation corpora, shared checkers or adaptive adversaries.

### Progression and stopping

1. Close F01–F06 with failing-before/passing-after regressions and paired valid controls. Bind the shared execution path before expanding the standalone campaign.
2. Run deterministic fixtures and independent replay; test the checker itself with deliberately wrong oracles and altered expectations.
3. Expand offline generators in bounded batches. A missing required implementation is `BLOCKED`; a safety regression stops the affected lane.
4. Run a small separately authorized live canary with a declared cost reservation, capability record and unknown-cost handling. These plans authorize no provider spending.
5. Add stress and deployment-environment trials only after functional/custody checks are stable. Timeouts, cancellations and resumes are first-class outcomes.
6. At the final rounds, produce a release decision packet with remaining obligations, deployment scope and rollback evidence. Test volume, `should_continue: true`, and model-written reports cannot authorize `PROD`.

Implementation work should preserve the existing thin Python orchestration and native mathematical owners. Finite educational enumerations are reference oracles, not a new competing production solver. Use the existing PFP ports and the Woland/Woland path where already integrated; verify that route rather than claiming it from a folder name.
