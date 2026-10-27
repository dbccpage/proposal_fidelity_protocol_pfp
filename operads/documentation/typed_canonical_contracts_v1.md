# Typed canonical instruction contracts v1

AuthorityEffect: None. Remaining work: [EPIC-OE-OEWAS-011 R1](../../product_planning_office/plans/epics/oewas/epic_oe_oewas_011_consolidated_residual_plan.md#r1-canonical-contracts-and-markdown-compatibility). The bounded pair is implemented and locally exercised; acceptance is limited to the pinned [integration verification receipt](../receipts/typed_contracts_20261010/verification.json) and [independent controls](../receipts/typed_contracts_20261010/independent/review.json). Full scope remains held.

## Frontmatter and declaration boundary

The Markdown parser reuses the existing catalog's frontmatter recognition:
a document-initial `---` line, a matching standalone closing `---`, and a
valid YAML mapping with unique string keys. Accepted metadata remains prose,
including fenced examples inside YAML block scalars. An unclosed or malformed
example in metadata cannot swallow or invalidate the real body declarations.
Only the scan start changes; physical UTF-8 spans and raw source bytes retain
the original header and LF/CRLF/CR line endings.

| Carrier | Existing owner and meaning |
| --- | --- |
| Canonical typed JSON | The typed compiler validates pinned resources and produces typed operations plus IDE Markdown. |
| Legacy/generated frontmatter | The capability catalog validates metadata. Header fields and examples do not create V3 operations or grant admission. |
| V3 body fences | The Markdown parser extracts explicit body declarations with its existing typed errors and Unadmitted lifecycle. |

This general Markdown port does not require frontmatter. Missing, malformed,
duplicate-key or nonmapping candidate headers retain ordinary Markdown parsing;
the catalog's strict metadata refusals are unchanged. A successful Markdown parse
does not certify frontmatter validity. A valid mapping at byte zero is treated
as metadata by this explicit compatibility convention, even when it resembles
Markdown between thematic breaks. Later separators cannot start a header.
Header-only edits change the raw digest; only actual body declarations contribute
to the V3 semantic digest. The
[public boundary controls](../tests/unit/test_frontmatter_declaration_boundary.py)
and existing filesystem/parser/SQLite ingress test cover this finite slice;
mixed-package catalog consumption is described below. Actual IDE activation
remains a separate observation.

Verify physical reconstruction at the parser port. The current
[SQLite catalog payload](../infrastructure/storage/sqlite_unit_of_work.py)
retains document identity and raw/semantic digests, with typed catalog content;
it omits the original Markdown and leaf nodes. Persistence controls should
compare the stored raw digest with the retained source bytes. Test each
representation at its actual public boundary before extending a storage contract.

## V3 declaration fences

The existing `LosslessMarkdownParserAdapter` recognizes fences using
the fence rules in [CommonMark 0.31.2 section 4.5](https://spec.commonmark.org/0.31.2/#fenced-code-blocks):
backticks or tildes (at least three), zero to three leading spaces, and a closer
using the same marker with at least the opener's length. Only spaces and tabs
may follow a closer. LF, CRLF and CR line endings are supported without rewriting
source bytes. The info string trims spaces/tabs; backtick-fence info cannot
contain a backtick. Typed declaration dispatch still requires the exact V3 name.

For example, this indented tilde block declares the same unadmitted operation
as the original triple-backtick spelling:

````markdown
  ~~~~oewas.operation.v3
  operation_id: example:audit
  inputs: []
  ~~~~~
````

Body interpretation removes up to the opener's indentation from each line,
including partial four-column tabs. Raw digests and half-open leaf spans address
the original UTF-8 bytes. For compatibility, closed `code_fence.content` omits
the final body/closer separator and the closing line ending remains in following
prose. Reconstruct bytes from source slices, not concatenated interpreted bodies.

Ordinary fences keep their contents literal, shielding apparent declarations;
an ordinary unclosed fence extends to EOF. An unclosed **OEWAS declaration**
instead returns `UNCLOSED_OEWAS_FENCE` with its opener's file/line locus. Invalid
YAML and field shapes retain the existing typed refusals. No declaration grants
its own admission. Sibling H2→H3→H2 headings remain ordinary prose.

The adapter also tracks nested bullet/ordered list items and blockquotes using
[CommonMark container rules](https://spec.commonmark.org/0.31.2/#container-blocks).
Container prefixes are removed from interpreted bodies, including tab padding;
physical spans include the original prefixes. Fenced content requires actual
container continuation, even though paragraphs can have lazy continuations.
Leaving the container ends an ordinary fence; an unclosed declaration refuses
at its opener. A sibling or outer closer cannot close an inner declaration.

[HTML block rules](https://spec.commonmark.org/0.31.2/#html-blocks) shield
fence-looking text in all seven categories. Raw `pre`/`script`/`style`/`textarea`
blocks, comments, processing instructions, declarations and CDATA stop on their
first terminator line. Block tags and complete standalone tags stop at a blank
line. A nested HTML-looking start cannot change that end condition. HTML also
ends at its container boundary; same-line terminators allow parsing to resume
on the following line. Complete standalone tags cannot interrupt a paragraph.

This is block-context handling for declaration fences, not an HTML renderer,
sanitizer or full inline Markdown parser. General CommonMark conformance is not
claimed. The public controls live in
[`test_container_html_declaration_fences.py`](../tests/unit/test_container_html_declaration_fences.py) and
[`test_commonmark_declaration_fences.py`](../tests/unit/test_commonmark_declaration_fences.py).
Peer counterexamples and their benign controls are retained in
[`test_commonmark_block_context_regressions.py`](../tests/unit/test_commonmark_block_context_regressions.py).

When extending declaration syntax, scan ordinary fences before interpreting
typed blocks: a declaration-looking line inside a foreign-language or longer
fence is literal content. Pair each newly accepted spelling with an invalid
closer and an ordinary-block shielding control. Check both normalized semantic
identity and exact source-slice reconstruction; either check alone misses a
different failure. This lesson is scoped to the adapter's fence layer above.

For container changes, distinguish a new list item from a lazy paragraph:
the number-one restriction on interrupting a paragraph does not exclude later
ordered items or a changed list delimiter after leaving an item. For HTML,
apply ASCII case matching to grammar tokens while allowing the Unicode values
permitted by the attribute grammar; broad `re.I` and `\s` can hide valid
declarations or expose literal ones. The fourteen peer regression controls above
pair these counterexamples with benign cases. They supplement the original
frozen checker; they do not establish general CommonMark conformance.

## Digested guidance extension

The same strict wire and compiler also accept `rule`, `helpful_pattern`,
`anti_pattern` and `antibody` entries in `catalog/contracts/v1/lessons/*.json`.
Each entry carries the existing lesson concepts: source/revision, failed claim,
counterexample, cause, correction, verification state, applicability and
exceptions. The source is a byte-bound repository resource, and its quoted
excerpt must actually occur in the resolved source. This validates attribution
and custody; it does not certify the lesson's interpretation or historical tests.

The first four entries reuse existing owners rather than migrating the estate:

| Kind | Canonical entry | Existing owner |
| --- | --- | --- |
| Rule | [Complete typed answer](../catalog/contracts/v1/lessons/adversary-typed-answer-rule.json) | `.agents/rules/engineering/rl_python_contracts_and_runtime_invariants.md` |
| Helpful pattern | [Strict input refusal](../catalog/contracts/v1/lessons/adversary-strict-input-pattern.json) | `HP_PY_013_strict_input_typed_refusal.md` |
| Anti-pattern | [Silent input coercion](../catalog/contracts/v1/lessons/adversary-silent-coercion-antipattern.json) | `AP_PY_013_silent_input_schema_coercion.md` |
| Antibody | [Prompt-attached coercion review](../catalog/contracts/v1/lessons/adversary-input-coercion-antibody.json) | `ab_silent_input_schema_coercion`, still candidate |

Rule contracts separate trigger, predicate and response. Helpful patterns state
conditions, construction and an example; anti-patterns state failure, witness
and repair. These fields and the lesson's exceptions appear in both generated
Markdown and typed instruction operands. The original two audit documents remain
in `bundle.documents` for existing callers; select new instructions from
`bundle.guidance_documents` or `bundle.all_documents`. Pass only the documents
participating in the chosen plan; unused-source refusal remains enforced.

Antibodies bind a named prompt URI, exact prompt bytes, the existing antibody ID,
an epitope, a required independent danger signal, and harmful/benign examples.
Compilation checks literal epitope separation in those examples and returns
existing `PromptTreeNode`/`AntibodyBinding` objects in `bundle.prompt_attachments`.
The prompt body is included in the generated instructions. This finite text
control is not a semantic code detector. Generation neither changes the pharmacy
nor supplies admission or the independent danger signal; the existing OEEIS
admission and two-signal evaluator still own activation.

Run the same commands from the repository root:

```text
python -m operads.infrastructure.typed_contract_compiler --repo-root . --write
python -m operads.infrastructure.typed_contract_compiler --repo-root . --check
```

The compiler discovers the original pair plus the selected canonical lessons
directory, rejects duplicate IDs, missing/cyclic dependencies and invalid source
bindings, and projects all selected packages through the existing host writer.
Each IDE receives an on-demand `skills/<id>/SKILL.md` adapter with standard
frontmatter and typed-kind metadata. A generated rule package does not become an
automatically loaded host rule. Existing ambient rules and host-maintained files
remain with their owners. The projector still refuses conflicting bytes; review
and reconcile an old generated file explicitly before regenerating it.

For example, invoke `/adversary-input-coercion-antibody` in an IDE to read its bound
review prompt and controls against the actual candidate. This is useful review
guidance, not an activated detector. Use the generated strict-input pattern to
carry its construction and exceptions into the next worker brief.

Stage reviewed canonical sources and generated entrypoints before rebuilding
the existing capability catalog. Its Git inventory also covers repository
resources, while entrypoint discovery remains restricted to canonical agents
and skills. Untracked lesson sources do not become trusted catalog resources.
There is no second catalog, arbitrary source-selected executor or new runtime.

### Catalog consumption and retired lesson evidence

`CompileCatalogHandler` uses the existing estate-source port to distinguish a
generated typed package from ordinary Markdown. For a generated package, the
filesystem adapter obtains the matching operation from
`compile_typed_contracts().all_documents` and verifies the generated entrypoint
and catalog resources. It does not reparse generated prose as an operation-free
Markdown document. Ordinary Markdown and V3 fences still use the lossless parser;
older estate-source implementations retain their default Markdown path.
Adversary's signed route reader also selects `all_documents`, including digested
rules, patterns and prompt-attached candidate antibodies.

A missing historical lesson source under
`_ic/nara/historical/oewas007/research/` may resolve from its exact forty-digit
`lesson.source_revision` through the existing Git reader. Its pinned byte length,
SHA-256 and literal excerpt must still match. This does not recreate the deleted
intelligence file. A modified resident source refuses instead of falling back to
older bytes. Missing history, an unbound path, a current instruction or a fixture
does not acquire a permissive historical fallback.

The repair lesson is concrete: a generated carrier must resolve back to its
canonical typed operation at the catalog consumer. Successful Markdown parsing
alone cannot establish that the operation survived. Pair that consumer control
with a changed generated file and a missing historical-source control; retain
the exact source pins and refuse unavailable history.

### Source retirement and projection consumption

V3 source declarations may restrict an operation to `Retired`; they cannot grant
themselves admission. An optional `replacement_operation_id` is meaningful only
on a retired operation. Omitting it preserves existing operation content hashes.
The projection carries source and operation pins plus retirement/replacement
metadata. The existing signed Adversary ingress replays that projection against
current sources and includes its bytes in the candidate plan binding.

Retired access refuses before provider work. A replacement must exist, remain
nonretired and preserve the exact ordered input/output contracts. Rewriting a
projection or transplanting its old signature does not authorize replacement
bytes. Development signing controls exercise this boundary; they do not install
an independently managed admission key or establish that every IDE loaded it.
Python replays declaration and replacement-interface semantics. Native admission
verifies the signed projection bytes, fresh raw source hashes, content pins and
selected retirement records; it does not independently parse Markdown semantics.

### Corpus-guidance selections

The continued digestion adds these source-bound entries to the same catalog:

| Entry | Concrete lesson | Retained source |
| --- | --- | --- |
| [Assigned outcome rule](../catalog/contracts/v1/lessons/adversary-assigned-outcome-rule.json) | One solve and 99 refusals is 1% assigned-task success; keep conditional rates separately labelled. | PFP integration evidence, D2 |
| [Free information pattern](../catalog/contracts/v1/lessons/adversary-free-information-pattern.json) | Check the admitted initial fiber before scheduling another query. | Calibration R1 mathematical finding, corrected in R2 |
| [Parser work anti-pattern](../catalog/contracts/v1/lessons/adversary-parser-work-antipattern.json) | A short exponent string can perform costly arithmetic before post-construction bounds. | Calibration R1 code finding and R2 correction |
| [Parser work antibody](../catalog/contracts/v1/lessons/adversary-parser-work-antibody.json) | Bind the exact-parser review prompt, harmful constructor ordering and a benign admitted-input control. | Calibration R2 code repair review |
| [Proof scope rule](../catalog/contracts/v1/lessons/adversary-proof-scope-rule.json) | Separate formal scope, quantitative margins and qualitative consequences. | Initially Calibration R2; refined from the Meron R4 scope correction below |
| [Scoped reuse pattern](../catalog/contracts/v1/lessons/adversary-scoped-reuse-pattern.json) | Recheck changed dependencies; retain unchanged evidence at its original scope and date. | Calibration R2 code review |
| [Stale-task antibody](../catalog/contracts/v1/lessons/adversary-stale-task-antibody.json) | A fixed `d=1` guard rejects a valid `d=2` solution; check the current task and exact carrier before reuse. | Recursive-reentry assignment, with fresh nine-element finite controls |

These entries quote actual retained source bytes. Their historical tests and
mathematical findings are not new execution results. In particular, the parser
finding was repaired in the retained successor; the lesson does not assert a
current defect. Its prompt attachment remains a candidate with no pharmacy
admission. Corpus indexing and these selected reads do not close unread sources,
opaque artifacts or open research obligations; those sources remain retained.

The recursive-reentry packet is an assignment, not a completed theorem. The
stale-task entry records a fresh finite enumeration of its nine-pair carriers,
the changed-task rejection and same-task/parameterized benign controls. This
establishes that particular witness, not general re-entry, coverage or budget
preservation. The other newly read pilot matrix/requirements and LP-checker
packets retain their declared execution and certificate limits; no new pilot
run or formal proof follows from their prose.

The main-branch pattern relocation is reconciled in the original entries:
anti-pattern owners now live in `.agents/patterns/anti/`, helpful owners in
`.agents/patterns/helpful/`. Their current bytes and the edited antibody spec are
rebound together after checking the original excerpt. Historical source bytes
and receipts are preserved; retired directories are not recreated.

### Meron corpus batch

The first Meron bounded read covered twelve retained files (80,840 bytes) under
`_ic/darpa/research/briefs/`: `2026-10-07_meron_thermo_mission.json`,
`meron_r2_stage2.json`, `meron_r2_stage5_checks.json`,
`meron_r2_stage6_critic.json`, `meron_r2_stage7_critic.json`,
`meron_r2_stage8.json`, `meron_thermo_checks_round3_20261007.json`,
`meron_r6_stage7_critic.json`, `meron_r6_stage8.json`,
`meron_thermo_checks_round6_20261007.json`,
`meron_thermo_lean_receipt_20261007.json` and
`meron_thermo_verification_policy.json`. The earlier indexing ledger remains
historical navigation; it is not changed into a full-review claim.

| Typed guidance | Finding and correction | Limit |
| --- | --- | --- |
| [Proof premise rule](../catalog/contracts/v1/lessons/adversary-proof-premise-rule.json) | R2-OBJ-03 omitted `mu>=0` from the public bound; B1 carries it into the claim and input contract, and the R6 report confirms the restriction. | Later repair is source-reported. Excluded inputs do not refute a correctly restricted claim. |
| [Check sensitivity pattern](../catalog/contracts/v1/lessons/adversary-check-sensitivity-pattern.json) | R6-CX-01 changes K while retaining checked bond terms; require their semantic binding and a mutation through the actual consumer. | The full lift check already catches it. F1 is a proposed standalone-check repair, not completed work here. |

R2 numerical attacks report observations far below loose bounds, finite
truncation and some shared builders. Preserve those limitations instead of
converting `NO_COUNTEREXAMPLE_FOUND` into verification. The policy explicitly
limits `*_written` PASS to artifact/check obligations. Later retained evidence
reports standalone Lean compilation of eighteen arithmetic theorems; that
supersedes the mission's uncompiled status at its historical scope and still
does not formalize the analysis. No Meron, Lean or provider execution is claimed
by this digest. Strict positivity on the residual interval remains open.

Both new entries use the existing compiler, candidate-plan port and four-host
projector. Their listing descriptions stay short enough for the existing
32,000-byte ceiling, and the neighboring lesson descriptions stay intact.
The intervening round-3 through round-5 review selection is now covered below.
The earlier selection and the remaining corpus are retained unchanged.

### Meron round-3 through round-5 review refinements

Read all twelve review/check files (108,340 bytes): for each round 3, 4 and 5,
`meron_rN_stage6_critic.json`, `meron_rN_stage7_critic.json`,
`meron_rN_stage8.json` and `meron_thermo_checks_roundN_20261007.json` under the
same briefs directory. Eleven are newly substantive selections; the round-3 raw
check was reread from the prior batch. Selected round-6 proof-review and raw
source-control fields were inspected as successor evidence, alongside the
previously read round-6 repair disposition. This is not a full round-6 review.

| Amended existing entry | Decisive review correction | Scope retained |
| --- | --- | --- |
| Proof premise rule | R3-OBJ-04 finds the weighted embedding range still absent from a structured claim after the display repair. | Check every affected projection; the sup rate and weighted embedding retain their different valid domains. R4/R5 report repair. |
| Check sensitivity pattern | R4-CX-01 passes pair checks but fails a three-bond word; R5-CX-01 passes the bond repair with a parity-dressed auxiliary source. | Justify composition and source support; test each consumed role and assembly. R6 reports source repair, but F1 K binding remains proposed; the full lift already catches K mutation. |
| Proof scope rule | R4-OBJ-06 separates the stronger margin through theta_* from positivity of the same lower bound up to 2*theta_*. | Do not turn a certificate endpoint into a false/open qualitative claim, or a zero lower bound into a zero true value. |

Fresh exact `Fraction` arithmetic confirms the implication of the **reported**
bound: for `c=25070366400/2537` and `theta_*=2537/100281465600=1/(4c)`,
`1/2-c*theta` equals `1/4`, `1/8` and `0` at `theta_*`, `3*theta_*/2` and
`2*theta_*`, respectively; `2*theta_*<1/288`. This does not verify the analytic
premise or formalize the model. The positive intermediate interval follows
conditionally; the zero endpoint leaves actual positivity unresolved.

The packets also distinguish value-equal serialization from byte-identical
replay: R4 retains a formatter mismatch, while R5 reports its repair. Historical
counts, finite word probes and imported analytic premises keep their limits.
No Meron checker, Lean build or provider run is newly executed here, and no
historical defect is asserted to persist in current model code.

These refinements amend three existing entries, preserve the thirteen guidance
operands and three candidate prompt attachments, and regenerate the same fifteen
IDE packages. The existing Adversary and digestion owners carry the corrections.
Their optional [staged prompt/scratchpad template](../../.agents/skills/adversary-digests/references/review_to_structure.md#optional-staged-prompt-and-scratchpad)
uses current `TeamworkAction`/`TeamworkObservation` fields and temporary metadata;
it adds no runtime schema, automatic metadata forwarding or performance claim.

### Meron stages 1 through 5 follow-up

Read all fifteen retained round-3 through round-5 derivation/proposal/check packets
(158,537 bytes). Reuse the existing check-sensitivity pattern and proof-scope rule:
identify raw-byte versus controller canonical-content digest profiles before
comparison, and inspect each PASS predicate. Written-argument and table-presence
checks leave imported analytic premises open. R3's stale compilation labels and
R4's narrower qualitative window remain historical; R5 reports their corrections.
The source excerpts bind this read, not the truth of the proposed analysis.

Generate the same fifteen IDE packages; no new lesson owner, framework or
concurrency is added. All fifteen source files remain byte-identical. Meron,
Lean and provider execution were not rerun. Round-6 derivation inputs remain
outside this read; the whole corpus is not certified.

## Original pair: decision and existing ports

The sections below retain the original pair's design and historical validation;
the digested guidance extension above adds four instruction kinds to that compiler.

Add two versioned canonical sources: [claim audit](../catalog/contracts/v1/adversary_claim_audit.json) and [scope falsifier](../catalog/contracts/v1/adversary_scope_falsifier.json), with [claim-audit instructions](../catalog/contracts/v1/instructions/adversary_claim_audit.md), [falsifier instructions](../catalog/contracts/v1/instructions/adversary_scope_falsifier.md) and the [fixture bank](../catalog/contracts/v1/scope_falsifier_fixtures.json). Their repository root is `operads/catalog/contracts/v1`. Compile them through [compile_typed_contracts(repo_root)](../infrastructure/typed_contract_compiler.py) into existing typed domain objects and generated IDE packages. These instruction-package contracts do not replace the canonical `core.contract.v2` governance estate or the existing capability inventory.

[CapabilityCatalogV1](../domain/capability_catalog_v1.py) remains the catalog type and canonical encode/decode boundary. [OperationV3](../domain/entities/operation_v3.py) remains the ordered-port operation type; [candidate-plan compilation](../application/adversary_candidate_plan.py) remains the composition boundary. [AntiSkillSpecV2](../domain/anti_skills/anti_skill_v2.py) and [evaluate_antiskill_fixture_bank](../application/anti_skill/anti_skill_v2.py) provide the closed predicate and offline execution. The new strict wire model adapts to these types; it does not create a parallel registry, evaluator or admission authority.

The compiled pair's catalog is scoped to these two packages. Full estate discovery still belongs to the [tracked-inventory catalog compiler](../infrastructure/capability_catalog_compiler.py); a two-entry projection must not overwrite its full inventory. The existing estate compiler recognizes generated metadata, freshly compiles the pair and requires its resource paths in the tracked inventory; drift or untracked sources refuse. Existing HTTP/IDE Pydantic DTOs are transport/view models, not canonical semantic contracts.

## Bounded package and authority contract

| Package | Kind implemented here | Finite behavior | Authority ceiling |
| --- | --- | --- | --- |
| `adversary-claim-audit` | skill | Declared ordered inputs, instruction body and finding output, composable through the existing candidate-plan port | Declaration-only, UNBOUND catalog executor and Unadmitted plan |
| `adversary-scope-falsifier` | anti_skill | Exactly ALL(single NOT_SUBSET_FIELDS(claim_scope, evidence_scope), no values) detects scope overclaim on valid typed subjects; finite positive/negative fixtures | PROPOSED detector, offline execution only, runtime enforcement false |

The [strict Pydantic union](../contracts/typed_capabilities_v1.py) exports [typed_capability.schema.json](../catalog/contracts/v1/typed_capability.schema.json). Its `oewas.sorted-ascii-json.v1` profile uses sorted keys, compact separators, ASCII escaping, no NaN and exactly one trailing LF; input bytes must match. This is not RFC 8785. Schema/version, fields and types are closed. Duplicate constructed keys, including decoded escapes, must refuse before value selection. Relative body paths must stay inside the selected package source boundary; body content is bound by an independently recomputed digest. No source text may select an arbitrary executor, provider, approval or active detector registry. A compiled operand span identifies the JSON instruction ResourceRef object; the external body has its own byte hash. This is reference provenance, not a claim that body text occurs inside JSON. Compiler and wire source bytes are also included in the aggregate contracts binding.

The [host projector](../../operations/use_cases/packaging/project_typed_contracts.py) generates `skills/<id>/SKILL.md` for the two IDs under `.agents`, `.claude`, `.codex` and `.grok`. Output includes standard name/description frontmatter, declared signature, source binding and instructions. Repeated generation must be deterministic; changed or host-owned content must refuse rather than be overwritten. Existing `adversary` packages and other host-maintained files remain outside the generated path set. Preflight conflicts cause no writes. There is no cross-file transaction: an I/O error or concurrent change during creation may leave a partial projection, so callers must serialize directory ownership and verify all outputs. A changed generated file also refuses; automatic replacement/upgrades require a separate reviewed policy.

A generated package is discoverable instruction text, not proof of host execution. The implemented [verify_typed_contract_admission helper](../application/typed_contract_audit.py) freshly audits and selects the typed plan, then reuses [signed Adversary instruction admission](../application/adversary_instruction_admission.py) with an independently supplied signature and exact plan/source/body bindings. Targeted tests exercise this instruction-custody path and subject/source/fixture/signature refusals; ephemeral test signatures do not supply production operator approval, detector activation or Adversary dispatch. The compiler must not mint that signature or approval. The legacy Python anti-skill admission verifier is retired, and Rust `core.eis.anti_skill.v2` is a different schema from the closed-predicate Python spec. Neither supplies missing detector activation. Fixture success never creates an antibody or production license. [audit_typed_contracts](../application/typed_contract_audit.py) freshly compiles sources, replays fixtures and evaluates the real subject; its receipt stays Unadmitted with runtime activation HOLD. A caller may supply an externally retained expected contracts digest for replay custody. CLEAN means only that the configured finite predicate did not match that typed subject.

The CLI normalizes its repository root to an absolute Path before projection; a separate real relative-root RED/GREEN control covers that boundary. The CLI exposes the following explicit modes; these commands are usage examples, not execution evidence:

```text
python -m operads.infrastructure.typed_contract_compiler --repo-root . --show-schema
python -m operads.infrastructure.typed_contract_compiler --repo-root . --write
python -m operads.infrastructure.typed_contract_compiler --repo-root . --check
python -m operads.infrastructure.typed_contract_compiler --repo-root . --audit-subject subject.json
```

## Taxonomy and implementation boundary

| Term | Meaning in this design | v1 treatment |
| --- | --- | --- |
| Rule | Ambient invariant or prohibition with a stated enforcement port | Typed trigger/predicate/response; generated on-demand guidance, no ambient enforcement |
| Skill | On-demand procedure with typed ordered ports and instruction source | Implemented package kind for claim audit |
| Anti-skill | Typed defect predicate with evidence bindings and fixture obligations | Implemented package kind for scope falsification; PROPOSED |
| Antibody | Prompt-bound candidate reference; admission and activation are separate | Typed prompt/two-signal binding with harmful and benign examples; no self-admission |
| Helpful pattern | Reusable positive construction with conditions and examples | Typed conditions/construction/example and generated guidance |
| Anti-pattern | Named failure description with a witness or falsifier | Typed failure/witness/repair; descriptive text is not a detector |
| Workflow | Ordered composition or DAG of existing capabilities and budgets | Existing plan ports reused; new canonical workflow schema deferred |
| Agent | Role, permitted capabilities and independently bounded authority | Existing agent/catalog references reused; new canonical agent schema deferred |

These distinctions prevent naming a narrative warning an executable guard or a successful fixture an admitted antibody. The two packages do not migrate existing rules, workflows, agents or the complete skill garden.

## Prior art and local synthesis

Primary sources were read on 2026-10-10 for the following concept mapping. This is a design inference from their published descriptions, not a reproduction of their experiments. No listed work establishes one universal format spanning this repository's taxonomy; the JSON package envelope and domain integration are our synthesis, with novelty unestablished.

| Primary source and inspected version | Borrowed concept | Local synthesis and unimplemented boundary |
| --- | --- | --- |
| [AgentSpec, arXiv v3](https://arxiv.org/abs/2503.18666v3) | Rules separate a trigger, predicate and enforcement response. | Keep detector predicates distinct from invocation and disposition. This slice does not implement AgentSpec's DSL or general runtime hooks. |
| [Progent, arXiv v3](https://arxiv.org/abs/2504.11703v3) | Privilege policies constrain tool names/arguments; narrowing and expansion receive different treatment. | Reuse explicit allowed effects and existing narrowing controls. No SMT policy generator, tool-argument firewall or new approval service is implemented here. |
| [CaMeL, arXiv v2](https://arxiv.org/abs/2503.18813v2) | Trusted control is separated from untrusted retrieved data, with policy checks on tool flows. | Treat model text as data/proposals; only a validated contract enters the compiler. This is not CaMeL isolation, capability tracking or a proof of injection resistance. |
| [DSPy, arXiv v1](https://arxiv.org/abs/2310.03714v1) | Declarative modules and graph composition separate program structure from prompt text. | Use ordered signatures and separate instruction bodies. No optimizer, learned prompt selection or DSPy runtime is introduced. |
| [Agent Skills specification](https://agentskills.io/specification) | Host package uses a directory with YAML-frontmatter `SKILL.md` and optional resources. | Generate host packaging from typed sources. Host compatibility/discovery is distinct from enforcement; experimental allowed-tools metadata is not execution authority. |

Agent Skills is a packaging specification, not a research paper. The other sources describe different systems and scopes. Their reported benchmark results are not measurements of these Adversary packages and are not adopted as performance claims.

## Finite experiment and negative controls

Freeze the two source contracts, instruction bytes, compiler/domain implementation and fixture bank by SHA-256 before acceptance. Use temporary roots and no provider/network calls. The independent oracle is exact source/output bytes, ordered ports, catalog canonical round trip, and hand-labelled scope-membership outcomes; a compiler-generated digest alone cannot verify its own preimage.

| Experiment | Positive/recovery control | Negative/transplant control | Recorded result |
| --- | --- | --- | --- |
| Strict ingress | Exact valid pair compiles; corrected malformed package can retry | Duplicate/escaped key, unknown kind/field, coercible wrong type, missing body, path escape | Exact refusal code/detail or typed output; no coercion |
| Body and catalog binding | Independently hash body and round-trip existing catalog | Changed body, foreign source/digest, reordered ports | Binding refusal or expected digest/order difference |
| Offline scope detector | Bounded claim and overclaim fixtures in distinct contexts | Equal scopes, empty-claim subject refusal, unrelated context and changed implementation/spec/fixture digest | Per-case expected versus actual match/disposition; exact fixture denominator |
| Host packaging | Identical repeat and byte-identical active-host outputs | Tampered generated output, conflicting host-owned file and unrelated Adversary sentinel | Determinism, typed conflict and unchanged protected bytes |
| Optional signed consumption | Independently supplied signed admission at existing port | Wrong signer, source snapshot or ordered body digest | Existing verifier result; missing signature leaves this path held |

The independent controls found and retained real catalog-resource and instruction-encoding RED failures before the bounded GREEN repairs. Keep observing a real public-port RED before each new minimal GREEN repair; already-GREEN controls document reuse. Then bypass a relevant production ingress/body/ownership guard, require the corresponding test to fail, restore exact bytes, and replay the named controls. Keep one-to-three test files per batch and at most three repair attempts. The epic contains exact candidate paths and commands; actual receipt must add versions, exit codes, raw output and source/test/mutation/restoration hashes.

Independent review replayed 50 tests in three named compiler/catalog files with stable source/input pins after final catalog/CLI/format refactors and five additional frozen strict semantic controls. Earlier 45-test phases remain retained with their own exact pins. Earlier mutation/restoration receipts retain their tested source pins; they are not silently repinned to later refactors. Separately, two existing AST architecture methods fail on a disposable pinned-base reconstruction; [baseline evidence](../receipts/typed_contracts_20261010/independent/baseline_architecture.json) binds the test and offending unchanged sources. These remain owned OEWAS domain defects, not a clean gate claim.

Finite acceptance establishes only these named packages under pinned local conditions. It does not establish natural-language claim truth, general precision/recall, malicious Python isolation, provider behavior, power-loss safety, host behavioral parity, full estate migration, production admission, mathematical equivalence or research novelty. Those residuals remain with the owners listed in the epic.
