# Operations governance domain audit

Completed **164/164 full source bodies**, **10,427 lines**, **377,900 bytes**. All original scope pins remain unchanged. **6 claims, 18 findings, 20 independent finite controls**. No partial/bounded reading credit and no original function/module execution.

The finite controls are standalone source-correspondent reconstructions, not retained test-suite or production runs. They establish the stated small witnesses only. Canonical codecs and explicit finite state predicates contribute reusable mechanisms; declaring a receipt, stage, owner, or authority label does not establish the corresponding external event.

## Reusable mechanisms

### OGD-C01: Strict bootstrap is a substantive closed codec and byte-binding mechanism.

The bootstrap owner implements closed frozen schemas, exact authority-null/boolean/integer admission, normalized Unicode and paths, sorted unique control coverage, exact T0 identity population, canonical domain-separated JSON hashes, duplicate/float/nonfinite refusal, re-encoding equality, explicit currency checks, and binding of supplied evidence/schema/policy/T0 bytes. These mechanisms are materially stronger than label-only records elsewhere in the same package.

Reuse: Retain canonical record codec + explicit byte binding + injected currency check as separate workflow stages; carry admitted provenance and task-specific control adequacy separately.

Limits: Source reasoning, not a fresh Pydantic/runtime run or a proof that controls are effective. Byte bindings authenticate consistency of supplied material, not actual human identity. Large integer and ordering-of-size-check limitations remain in the file assessment.

Evidence: `ops/governance/domain/swarm_control/bootstrap_v1.py`:65–160; `ops/governance/domain/swarm_control/bootstrap_v1.py`:304–326; `ops/governance/domain/swarm_control/bootstrap_v1.py`:396–425; `ops/governance/domain/swarm_control/bootstrap_v1.py`:433–561; `ops/governance/domain/swarm_control/bootstrap_v1.py`:606–649; `ops/governance/domain/swarm_control/bootstrap_v1.py`:691–772; `ops/governance/domain/swarm_control/bootstrap_v1.py`:788–879

### OGD-C02: Finite event and result mechanisms have precise conditional algebraic meanings.

AggregateRoot requires the next version; EventStream requires only a larger version. Journal reduction checks a finite seven-state transition relation with packet-local monotone sequences. Hash-chain replay detects local content/ordering inconsistency; Ok/Err implement conventional result branching under typed pure callbacks. These are finite state and consistency mechanisms rather than proofs of operational authorization.

Reuse: Reuse explicit state transitions and local transcript consistency, while keeping actual lease/review/human predicates as independent prerequisites.

Limits: Exact line ranges are limited to these full owners; transition-specific authorization and external authenticated roots are not supplied by the state labels or hash chain. Arbitrary Python callback effects are outside result-law reasoning.

Evidence: `ops/governance/domain/shared_kernel/entities/aggregate_root.py`:1–51; `ops/governance/domain/shared_kernel/events/event_stream.py`:1–32; `ops/governance/domain/shared_kernel/result/err.py`:1–44; `ops/governance/domain/shared_kernel/result/ok.py`:1–44; `ops/governance/domain/swarm_control/event_tape.py`:1–96; `ops/governance/domain/swarm_control/journal_reducer.py`:1–62

### OGD-C03: Required evidence aggregation preserves explicit non-success states.

aggregate_required admits an exact list/tuple of 1..10000 exact EvidenceStatus values and returns PASS only if every item is the PASS enum. The ordinary STRICT measurement policy refuses every provenance except MEASURED, including injected and skipped values. Rebinding conservatively marks outstanding obligations stale and never itself claims ready-to-land.

Reuse: Retain nonempty explicit required-status conjunction and stale-evidence invalidation, bound to a separately frozen required-obligation population.

Limits: Empty required-measurement mappings are not populated by this function, and provenance strings remain caller declarations. The narrower chaos scenario helper is not equivalent to the general STRICT checker.

Evidence: `ops/governance/domain/swarm_control/evidence_status.py`:13–37; `ops/governance/domain/swarm_control/dev_vs_strict.py`:33–53; `ops/governance/domain/swarm_control/rebind_after_merge.py`:1–69

### OGD-C04: Council tallying explicitly remains advisory.

The council bridge validates electorates/votes and uses exact Fraction threshold arithmetic, while verify_council_resolution explicitly refuses to establish authority. PrincipalEvidence likewise states its syntax-only role for an injected verifier. This is an appropriate separation of tally/data shape from authorization.

Reuse: Reuse finite advisory vote tally as advisory evidence, never as an implicit execution capability.

Limits: No configured trusted verifier, cryptographic validation, or authorized human action was demonstrated. QuorumThreshold alone is weaker than the bridge revalidation.

Evidence: `ops/governance/domain/swarm_control/council_bridge.py`:36–73; `ops/governance/domain/swarm_control/council_bridge.py`:87–167; `ops/governance/domain/swarm_control/council_bridge.py`:170–207; `ops/governance/domain/swarm_control/principal_evidence_v1.py`:1–74

### OGD-C05: Candidate and post-await bindings support conditional stale-state detection.

Candidate identity includes repository, PR, base/head/merge-base, tree/blobs, path-set, policy and evaluator labels; construction/revalidation rederive the digest. Post-await comparison distinguishes head drift and other binding drift. Review pinning and postmerge census are narrower equality/nonmembership predicates over observations supplied by callers.

Reuse: Use observation acquisition, binding, await, fresh reacquisition, and equality comparison as distinct stages; preserve the exact task/repository/head and measurement provenance.

Limits: No Git or remote observations were made; copied policy/evaluator labels and fallback tree/blob observations are not evidence of freshness. Runtime type/deep-freeze and tree-only path-set gaps remain explicit.

Evidence: `ops/governance/domain/swarm_control/candidate_binding.py`:36–107; `ops/governance/domain/swarm_control/candidate_binding.py`:124–209; `ops/governance/domain/swarm_control/post_await_revalidate.py`:21–57; `ops/governance/domain/swarm_control/review_worktree_pin.py`:1–21; `ops/governance/domain/swarm_control/postmerge_closure_census.py`:41–68

### OGD-C06: Current transport and content witnesses improve their declared finite predicates.

Transport now refuses absent content digests for byte claims and reports same-path/same-digest NOT_APPLICABLE. Postmerge content comparison checks expected and extra observed paths, and its digest binds both maps. On the admitted string-map domain, the independent 81-pair control agrees with exact map equality.

Reuse: Retain measured mutation-shape classification and exact map comparison under canonical typed digests, independently observed bytes and immutable evidence storage.

Limits: The 81-pair reconstruction is finite independent arithmetic, not an execution of original functions. VERIFIED remains relative to supplied digest labels; malformed present values and mutable maps require additional admission.

Evidence: `ops/governance/domain/swarm_control/universal_transport_receipt.py`:97–160; `ops/governance/domain/swarm_control/postmerge_content_witness.py`:50–106

## Findings

### OGD-F01: Mutation manifest framing admits an exact prehash ambiguity.

The path/action/old/new/content sequence is NUL-delimited, but RepoPath admits NUL and CREATE leaves old digest unrestricted. Distinct records (path a\0CREATE, old empty) and (path a, old CREATE\0), with the same CREATE action and valid new/content digests, encode byte-for-byte identically. This defeats canonical record identity before SHA-256; no cryptographic collision is needed.

Limits: A constructor-level witness; real filesystem NUL refusal can block later I/O. No filesystem mutation or historical receipt failure was shown. This is analogous to, but a distinct owner from, prior OAR-F11.

Next action: Reject separators/control characters in every admitted field or use an injective length-prefixed/closed canonical encoding; enforce unused-field emptiness and recheck the full structured record.

Evidence: `ops/governance/domain/shared_kernel/value_objects/mutation_item_v1.py`:35–61; `ops/governance/domain/shared_kernel/value_objects/mutation_manifest_v1.py`:16–29; `ops/governance/domain/shared_kernel/value_objects/path.py`:23–41

Independent controls: OGD-T02, OGD-T03

### OGD-F02: N1 lease verification does not bind the presented grant to stored scope and expiry.

Verification compares ID, owner, epoch and only a lower-fence condition, then checks the presented expiry. A same-ID/owner/epoch record with a larger fence and later expiry passes after the stored grant expired; expanded path/resource/worktree scope is never compared. The independent finite control makes that difference explicit. Grant/revoke keys also precede Identifier normalization.

Limits: No original registry or real authority boundary executed. External unforgeable issuance/opaque handles could prevent presented-record substitution, but are not established in this owner. In-memory data are not durable atomic fencing.

Next action: Verify exact stored lease identity and all scope/time fields, reject any unexpected fence, normalize keys before registration, and bind effect execution to durable atomic current-grant checks.

Evidence: `ops/governance/domain/swarm_control/n1_lease.py`:44–79; `ops/governance/domain/swarm_control/n1_lease_registry.py`:33–83; `ops/governance/domain/swarm_control/n1_lease_registry.py`:96–119

Independent controls: OGD-T06

### OGD-F03: N10 admission can exceed its ceiling when candidate IDs repeat.

Conflict admission counts dictionary keys. The skeleton stores each accepted write set by candidate ID but appends every accepted record. Twenty repeated-ID disjoint-path records pass a ceiling of two while the map contains one key. Exact string overlap also admits parent/child directory path sets unless the population is restricted to canonical leaf files.

Limits: Only the admission fragment was reconstructed. No retained skeleton, random license issuance, Git or concurrent execution was run. Distinct identities and file-only write sets are sufficient additional preconditions for these particular controls.

Next action: Require unique candidate identities before admission; count actual active work records; define whether scopes are canonical files or hierarchical regions and use the appropriate overlap relation.

Evidence: `ops/governance/domain/swarm_control/conflict_graph_admission.py`:71–130; `ops/governance/domain/swarm_control/swarm_n10_skeleton.py`:65–78

Independent controls: OGD-T07, OGD-T08

### OGD-F04: Qualification scenarios supply their own observations and stage completion labels.

N1 appends lease/binding/landing/disposal/pruning states without the corresponding effects, using fixed epochs and expected blobs as default observations. N2 issues a refreshed license after a comment asserting fresh evidence without running a checker. N4 records counters without asserting expected scenario outcomes. N10 fabricates head strings, defaults missing observations to promises, and returns is_successful=True even for no admitted candidates. Receipt digests omit much of the input/content population.

Limits: Useful synthetic choreography remains; N10 explicitly disclaims full production DoD. These files are separate from prior OAR-F21 qualification DTOs and OAR-F23 scheduler fixtures. No historical outcome is inferred false merely because this source is a harness.

Next action: Label the results as synthetic predicate scenarios; make observations mandatory for operational qualification; bind every receipt to input/candidate/checker/content population and enforce explicit success criteria.

Evidence: `ops/governance/domain/swarm_control/qualification_n1_engine.py`:54–134; `ops/governance/domain/swarm_control/qualification_n2_engine.py`:58–140; `ops/governance/domain/swarm_control/qualification_n4_engine.py`:41–100; `ops/governance/domain/swarm_control/swarm_n10_skeleton.py`:80–121

Independent controls: source review only

### OGD-F05: Postmerge content comparison collapses missing keys and null expected values.

The expected loop compares observed.get(path) with expected_oid. Expected {a: None} versus observed {} yields no mismatch, and the reverse extra-path loop is empty. The independent finite model confirms equality on all 81 pairs of two-path string maps but exhibits this admitted-runtime counterexample outside the annotation.

Limits: String-valued maps preserve the intended finite relation; this is a missing runtime admission check, not a counterexample within that mathematical domain. No actual landed tree was observed.

Next action: Require canonical nonempty digest strings and explicit key membership; preserve exact whole-map equality and immutable stored observations.

Evidence: `ops/governance/domain/swarm_control/postmerge_content_witness.py`:50–78

Independent controls: OGD-T09

### OGD-F06: Declared repository-relative paths and producer routes are not confinement boundaries.

RepoPath accepts drive-colon, leading-backslash and NUL forms after normalization. canonical_repo_path silently erases leading slash and excess parent components, and path_is_under mishandles the POSIX root prefix. Producer routing interpolates an unvalidated filename. Actual canonicalize_path is filesystem/platform-dependent with a fallback, so it cannot be substituted for a purely lexical proof or atomic effect confinement.

Limits: No real path escaped or filesystem write occurred. The POSIX root observation is a portability gap; this checkout is Windows. Path-prefix guards can remain useful under explicit canonical base and no-race assumptions.

Next action: Separate syntax admission, canonical relative identity, and checked effect-root confinement; reject absolute/drive/parent/control forms before normalization and bind file operations to the admitted root.

Evidence: `ops/governance/domain/shared_kernel/value_objects/path.py`:23–41; `ops/governance/domain/swarm_control/path_canon.py`:14–62; `ops/governance/domain/intelligence_community.py`:328–355; `ops/governance/domain/swarm_control/main_readonly.py`:1–39

Independent controls: OGD-T03, OGD-T16

### OGD-F07: Byte ceilings do not bound empty-message work or guarantee stream termination.

Both streaming ingress loops make refusal depend on accumulated bytes. Arbitrarily many empty chunks/messages leave that measure unchanged. A finite control consumes 10001 messages at a one-byte ceiling. The statement that an endless stream is abandoned needs a byte-progress assumption or an independent step/deadline bound.

Limits: Memory/hash-prefix ceilings remain meaningful. No infinite stream was run; externally supplied receive/iterator latency and cleanup are also outside the byte proof.

Next action: Add independently enforced message/iteration/deadline/cancellation budgets and preserve a receipt that distinguishes byte overflow from no-progress refusal.

Evidence: `ops/governance/domain/ingress/limits.py`:239–268; `ops/governance/domain/ingress/http_boundary.py`:145–182

Independent controls: OGD-T01

### OGD-F08: CAS license checks are local predicates, with missing finite-time admission.

NaN expiry passes the >= expiration check. Validation checks expected-head equality and expiry only; it neither authenticates/rederives the license ID nor checks candidate identity, not-before, single-use or an atomic Git compare-and-swap. A randomized default nonce is a real current improvement but does not supply those authority properties.

Limits: No token generator, Git command or mutex was executed. A trusted caller may supply missing premises; this owner alone is not a reusable execution capability. The in-memory mutex does not establish prior worker fencing after recovery.

Next action: Admit finite time values, bind all license semantics, and enforce issue/revocation/one-use/current-head checks atomically at the actual effect boundary.

Evidence: `ops/governance/domain/swarm_control/cas_land_license.py`:28–29; `ops/governance/domain/swarm_control/cas_land_license.py`:55–107; `ops/governance/domain/swarm_control/merge_mutex.py`:73–146

Independent controls: OGD-T05

### OGD-F09: Identity construction permits evidence before execution despite the builder invariant.

with_evidence rejects an uncreated execution slot. The constructor independently accepts either a reference or NotYetCreated for execution and evidence, and the parser delegates to that constructor, leaving the evidence-created/execution-uncreated combination admitted. This is an entry-point invariant mismatch within an otherwise strict closed codec.

Limits: The control abstracts correctly typed domain/slot references into created/uncreated Booleans. No forged signature or actual execution was claimed.

Next action: Enforce the cross-slot invariant in the common constructor/parser boundary, then retain the same guard in transition helpers.

Evidence: `ops/governance/domain/swarm_control/identity_links_v1.py`:74–123; `ops/governance/domain/swarm_control/identity_links_v1.py`:259–309

Independent controls: OGD-T11

### OGD-F10: WorkPacket mapping validation is weaker than a closed work-scope contract.

The mapping path accepts empty individual path strings, overlapping write/forbidden declarations, arbitrary nonempty base labels and ignored schema/unknown keys. Direct WorkPacket construction validates only exact class and authority effect, bypassing even required-label and nonempty-write checks. This is a shape adapter unless stronger preconditions are explicit.

Limits: No actual work was scheduled. WorkPacket correctly canonicalizes authority enum by identity, unlike two other label objects; this finding does not claim authority escalation.

Next action: Use one closed constructor for both entry points, validate schema/digests/canonical unique paths and cross-field scope exclusions, then bind the packet to the admission policy.

Evidence: `ops/governance/domain/swarm_control/work_packet_v1.py`:15–46; `ops/governance/domain/swarm_control/work_packet_v1.py`:64–114

Independent controls: OGD-T19

### OGD-F11: Frozen wrappers and copied mapping proxies do not deeply freeze evidence.

CandidateBinding copies only the outer blob map while accepting unvalidated value types. A nested list mutation crosses the proxy boundary. Postmerge witnesses and reconciled results similarly retain mutable dictionaries. Self-hash revalidation can detect some later mutation, but unconditionally trusting a frozen record or stale ID cannot.

Limits: The specific nested-list example violates intended string annotations, so exact runtime type admission can close it without arbitrary deep copying. No complete service exploit is inferred.

Next action: Admit exact immutable scalar/container types; copy/freeze entire admitted evidence; revalidate the bound digest at consumption boundaries.

Evidence: `ops/governance/domain/swarm_control/candidate_binding.py`:26–33; `ops/governance/domain/swarm_control/candidate_binding.py`:124–148; `ops/governance/domain/swarm_control/postmerge_content_witness.py`:14–22; `ops/governance/domain/swarm_control/postmerge_content_witness.py`:98–106; `ops/governance/domain/swarm_control/exact_blob_reconciliation.py`:1–105

Independent controls: OGD-T10

### OGD-F12: Path leases can overwrite active scope or skip conflict checks by caller-selected stacking.

A disjoint regrant under the same packet ID replaces the stored prior scope. stacked_under skips every overlap/resource check against the named lease without proving a relationship. The table has no expiry, fencing or concurrency control.

Limits: The finite model fixes canonical disjoint paths and does not call filesystem resolution. Legitimate explicit stacking can be a useful policy, but its authorization/lineage is external here.

Next action: Reject duplicate active IDs or perform an explicitly authorized atomic scope extension; validate stacking lineage and bind active ownership to an actual fencing mechanism.

Evidence: `ops/governance/domain/swarm_control/path_lease_registry.py`:32–69

Independent controls: OGD-T12

### OGD-F13: Git hygiene admits broad staging through a pathspec delimiter.

The policy refuses broad options before -- but accepts any nonempty path list after it, including git add -- . . Attached -Cfoo is not consumed as a global option and can bypass recognition of a protected subcommand. The policy is a token heuristic rather than a complete Git command admission grammar.

Limits: No Git commands executed. The direct argv witness is independent of shell parsing; broader shell wrapping remains outside this helper.

Next action: Use a closed admitted command grammar and explicit path population, including broad pathspec semantics and supported global-option forms; reject unrecognized Git forms rather than defaulting to allow.

Evidence: `ops/governance/domain/swarm_control/git_hygiene_policy.py`:63–83; `ops/governance/domain/swarm_control/git_hygiene_policy.py`:86–119

Independent controls: OGD-T13

### OGD-F14: Recovery action tags disagree with the UNBACKED_PR action description.

UNBACKED_PR now produces an action rather than silently disappearing, but the action_type is RELEASE_ORPHAN_LEASE while target and description refer to closing/rebinding a PR. A tag-driven consumer would receive the wrong action category.

Limits: The owner produces a dry-run plan only; no executor was reviewed or run, and no PR or lease was changed. The current improvement over silent dropping is preserved.

Next action: Add a distinct PR recovery action with explicit preconditions, validate target kind against action type, and keep plan generation separate from reviewed effect authorization.

Evidence: `ops/governance/domain/swarm_control/swarm_recovery_playbook.py`:15–19; `ops/governance/domain/swarm_control/swarm_recovery_playbook.py`:113–127

Independent controls: source review only

### OGD-F15: Ownership-first reconciliation needs an explicit authoritative premise.

Owned paths select the branch even when only main changed; foreign-owned paths select main even when only branch changed. Only unowned paths use ordinary three-way equality rules. Therefore fail-closed concurrent-edit language is conditional on ownership-map authority, not a general preservation property.

Limits: This can be intentional policy rather than a defect when exclusive ownership is authoritative and current. The control does not execute Git or claim any actual edit was lost.

Next action: State and verify ownership freshness/exclusivity, bind the map into the candidate, and distinguish policy-selected discard from conflict-free content preservation.

Evidence: `ops/governance/domain/swarm_control/reconciliation_classifier.py`:88–177

Independent controls: OGD-T14

### OGD-F16: Declared census and measurement provenance require population and policy binding.

CensusResult.zero_open trusts DIRECT and count zero without reconciling open_numbers. Postmerge closure accepts an empty supplied census as closed. The chaos STRICT scenario rejects only NOT_MEASURED, while the general STRICT checker rejects every non-MEASURED value. These helpers are not interchangeable authoritative census/measurement gates.

Limits: The chaos docstring describes the narrow NOT_MEASURED scenario, so this is a substitution hazard rather than proof of a broken universal policy. No actual API observation was checked.

Next action: Reconcile count and complete direct population, bind authoritative observation context, and use one shared full provenance predicate when claiming STRICT admission.

Evidence: `ops/governance/domain/swarm_control/census_result.py`:15–28; `ops/governance/domain/swarm_control/postmerge_closure_census.py`:41–68; `ops/governance/domain/swarm_control/chaos_falsifiers.py`:128–139; `ops/governance/domain/swarm_control/dev_vs_strict.py`:33–53

Independent controls: OGD-T18

### OGD-F17: Digest byte conversion and some label canonicalization are not closed under admitted inputs.

Signature digests admit odd hex lengths from 64 through 128, so as_bytes can fail after construction. SemanticContract and WindowDeclaration use equality to decide enum assignment, retaining the raw string None because it equals the string enum; WorkPacket correctly uses identity. These are local representation/totality gaps, not additional cryptographic or execution authority.

Limits: No crypto verification or original constructors executed. Timestamp/entity equality/hash and mutable-state concerns are recorded separately in their file assessments, not promoted to broader runtime claims.

Next action: Admit even algorithm-appropriate digest widths or separate opaque text from bytes; assign canonical enum values unconditionally or by identity; test constructor-to-serializer/consumer closure.

Evidence: `ops/governance/domain/shared_kernel/value_objects/digest.py`:29–60; `ops/governance/domain/shared_kernel/value_objects/digest.py`:120–121; `ops/governance/domain/swarm_control/semantic_contract.py`:23–28; `ops/governance/domain/swarm_control/window_declaration.py`:29–34; `ops/governance/domain/swarm_control/work_packet_v1.py`:64–69

Independent controls: OGD-T04, OGD-T20

### OGD-F18: Portable-reference allow patterns can suppress unrelated violations on an entire line.

Any allow-pattern substring bypasses scanning of the whole line, including the empty string which matches every line. A benign allowed token can therefore hide a separate disallowed local path on the same line. The four regex profiles also deliberately cover only selected path spellings.

Limits: This is a profile-scoped lexical detector, not a complete portability theorem. No original scanner or generated document pipeline executed.

Next action: Reject empty patterns and apply allow rules to a matched reference with explicit context, preserving other findings on the line.

Evidence: `ops/governance/domain/swarm_control/portable_reference_scanner.py`:75–118

Independent controls: OGD-T15

## Prior-review reconciliation

- `dag/reviews/additional_governance.json` (GOVERNANCE-RECORD-FLOOR, GOVERNANCE-MISSING-RUN-INPUT): Separate root governance grade/run-binding owners. Their declared-grade versus mathematical-correctness boundary applies as context; no score/receipt revalidation is credited here.

- `dag/reviews/additional_governance_remaining.json` (GOV-C01, GOV-C03, GOV-C04, GOV-C05, GOV-F01, GOV-F02): Historical mutation arithmetic, baseline bindings and metric/cache findings remain prior evidence. They do not certify or refute these ops domain owners and were not re-executed.

- `dag/reviews/additional_ops_adversary_remaining.json` (OAR-F11, OAR-F21, OAR-F23): The new manifest framing counterexample, synthetic qualification scenarios and admission accounting are distinct owners with a similar evidence-boundary failure class. No prior source-reading or execution credit is transferred.

## Limits and validation

- All 164 scoped files are textual Python and were read completely; there are no bounded-artifact or transferred-template receipts in this slice. External imported dependencies and tests outside this scope are not newly reviewed or executed.
- This is source-semantic evidence plus independent finite controls, not a deployment, concurrency, cryptographic-authority or end-to-end workflow certification. Callable ports, Pydantic runtime behavior and actual Git/remote observations remain dependencies.
- Historical comments about repairs are retained as historical source claims; the current predicates are assessed without assuming a former test passed or failed. No provenance normalization substitutes for raw scope pin equality.
- No provider/native/network/original-module runs, original-source changes, credential/private benchmark or answer access occurred. Embedded commands are corpus data.

The JSON records every source SHA-256 and full 1..N reading range. The separate validator checks the frozen scope, all 164 current source identities, complete reading-ledger coverage, source evidence ranges and report/control references. The first control run caught a bad evidence endpoint in the audit helper; the endpoint was corrected before the completed control artifact was written.

## Every-file assessments

- `ops/governance/domain/__init__.py` (1–49): Domain facade re-exports shared-kernel identity, event, command, mutation and temporal types. No additional invariant or mathematical mechanism is implemented here; import-time dependency behavior is delegated to the shared-kernel owners.

- `ops/governance/domain/ingress/__init__.py` (1–45): Ingress facade exposes byte ceilings, refusal vocabulary and bounded input/reply helpers. It contributes API routing only; exported constants do not themselves enforce the ceilings at every application boundary.

- `ops/governance/domain/ingress/http_boundary.py` (1–182): Full HTTP boundary read. Narrow loopback peer/host/scheme and same-origin predicates reject duplicate security headers, proxy evidence and ambiguous framing; the docstring correctly separates loopback from authentication. Actual body bytes are capped at limit+1 and duplicate JSON keys/deep recursion become typed refusals before framework parsing. Malformed ordinary JSON is deliberately left to the framework. Supplied ASGI envelope types and a nonnegative integer limit are preconditions rather than checked schemas. Repeated empty more_body messages have no byte-progress or iteration ceiling, so the byte/memory bound is not a total-work or termination guarantee. No receive port was called.

- `ops/governance/domain/ingress/limits.py` (1–314): Full byte-limit owner read. UTF-8 prefix slicing bounds encoding and hashing by the configured byte ceiling, including a first-decisive overflow versus invalid-surrogate distinction; stream readers stop after observing limit+1 bytes and close supplied iterators. Prefix hashes honestly cover only observed bytes. Endless empty chunks can still consume unbounded iterations, and iterator-close behavior is supplied externally; byte bounds do not prove time/cost/cancellation guarantees. OversizeReceipt checks numeric inequalities and authority label but does not validate exact integer types or digest shape. Direct callers must supply valid limits and stream chunk types. No retained stream/provider code executed.

- `ops/governance/domain/intelligence_community.py` (1–360): Full agency-domain model read. Useful finite membership checks admit exactly23 foundational agencies or those23 plus DOD, reject extra record fields, reject duplicate YAML keys and require unique declared artifact producers. These are local schema/routing policies, not real-world authority or capability proof. Nested agencies remain mutable as documented, so construction checks are not perpetual invariants. route_produced_artifact directly interpolates filename and artifact class without traversal/canonical-path validation; an admitted class plus ../../ filename can escape the intended logical folder. Legacy routing rejects dot/colon/backslash components but contains a shadowed duplicate _adversary dictionary key and a separate overriding special case. DOD fallback records are synthesized outside the stored producer census. No YAML loader or filesystem-loading method executed.

- `ops/governance/domain/shared_kernel/__init__.py` (1–57): Full shared-kernel lazy facade read, including every export and target mapping. Cached import-by-name preserves a narrow public surface and postpones loading, but adds no runtime validation or semantic law. Unknown names raise AttributeError; referenced owners are assessed separately.

- `ops/governance/domain/shared_kernel/commands/__init__.py` (1–32): Complete command-package lazy export map read. It routes Command, CommandStatus and CommandVerdict and caches imports. This is packaging machinery rather than command admission or an authorization mechanism.

- `ops/governance/domain/shared_kernel/commands/command.py` (1–16): Frozen command intent record carries command ID, issue time and issuer ID. ABC has no abstract methods here, and dataclass type annotations do not enforce identifier kinds or issuer authentication at construction. Useful message shape, no command execution or grant.

- `ops/governance/domain/shared_kernel/commands/command_status.py` (1–10): Four explicit command outcome tags ACCEPTED/REJECTED/DEFERRED/REFUSED provide vocabulary. The enum does not decide outcomes or distinguish authorization from correctness without its consumer policy.

- `ops/governance/domain/shared_kernel/commands/command_verdict.py` (1–17): Frozen command verdict joins command ID, status, detail and optional evidence digest. No constructor checks bind digest contents to a command or require evidence for acceptance; strongly typed is a static annotation claim, not runtime certification.

- `ops/governance/domain/shared_kernel/entities/__init__.py` (1–9): Entity package directly exports Entity and AggregateRoot. Complete facade body read; no separate identity/versioning law is added.

- `ops/governance/domain/shared_kernel/entities/aggregate_root.py` (1–51): AggregateRoot records an event only when aggregate identity matches and event.version equals current.version.next(); append and version advancement implement a useful contiguous local event sequence. The in-memory mutable aggregate supplies neither durable optimistic compare-and-swap nor concurrent exclusion. Clearing pending events keeps the version; replay/persistence policy is external.

- `ops/governance/domain/shared_kernel/entities/entity.py` (1–28): Entity equality compares identity for compatible runtime classes and hashes class plus ID. The dataclass is mutable, so changing id after insertion into a set/dictionary can invalidate hash-container lookup; construction does not freeze identity. This is local identity plumbing, not global entity uniqueness.

- `ops/governance/domain/shared_kernel/events/__init__.py` (1–32): Full event-package lazy facade read. Three exact routes expose event, recorder protocol and stream. Import caching is ordinary packaging; no event validation occurs here.

- `ops/governance/domain/shared_kernel/events/domain_event.py` (1–21): Frozen DomainEvent stores event/aggregate IDs, event_type, occurrence time, version and payload digest. ABC has no abstract method and annotations alone do not bind payload bytes, identifier roles or timestamp ordering. Actual event emission/verification belongs to consumers.

- `ops/governance/domain/shared_kernel/events/event_recorder.py` (1–18): EventRecorder is a three-method typing Protocol for recording, listing and clearing events. Ellipsis method bodies define an interface rather than a stubbed implementation advertised as evidence. No runtime-checkable decoration or law validation is supplied.

- `ops/governance/domain/shared_kernel/events/event_stream.py` (1–32): EventStream appends same-aggregate events with strictly increasing versions, allowing gaps unlike AggregateRoot's next-version rule. Constructor accepts a supplied mutable event list without checking its initial contents, and the internal list remains mutable. Error calls pass one argument, which the now-reviewed DomainInvariantError accepts as its code; the error code therefore includes dynamic event text rather than a stable vocabulary. In-memory append-only is a disciplined-use property, not immutable storage.

- `ops/governance/domain/shared_kernel/result/__init__.py` (1–37): Result package lazy facade exposes Ok, Err and Result. Naming it a monad is supported by the later standard bind shape only under typed/pure callback assumptions; facade exports do not establish laws.

- `ops/governance/domain/shared_kernel/result/err.py` (1–44): Err propagates its error through value map/bind, maps errors explicitly and raises on value unwrap. Standard short-circuit error branch of a result algebra; arbitrary callbacks/exceptions are outside total monad-law assumptions. Frozen wrapper does not deeply freeze the error object.

- `ops/governance/domain/shared_kernel/result/ok.py` (1–44): Ok maps values, bypasses error mapping and binds by returning the callback result. This is the conventional success branch, but callback return type is not runtime-checked and callback effects/exceptions are unconstrained. Conditional mathematical laws should not be claimed for arbitrary Python functions.

- `ops/governance/domain/shared_kernel/result/result.py` (1–46): Result ABC makes six operations abstract and documents success/error map/bind semantics. It supplies an interface, not a proof of monad laws or a runtime sealed sum type; concrete Ok/Err implement the intended finite branch behavior. No original module execution.

- `ops/governance/domain/shared_kernel/value_objects/__init__.py` (1–129): Complete value-object facade read including all alias assignments, lazy target maps and blank sections. Names such as DecisionId and GitBlobOid alias Identifier/Digest rather than enforcing distinct constructor kinds; callers must select the kind explicitly. TYPE_CHECKING aliases precede the imports they name; this block was not typechecked. No new cryptographic mechanism is implemented by aliases.

- `ops/governance/domain/shared_kernel/value_objects/digest.py` (1–135): Digest checks exact string type, normalizes whitespace/case and validates length/alphabet according to kind. Git accepts40/64 hex characters; signature accepts every length64..128 including odd lengths that bytes.fromhex cannot decode. Kind itself is not checked to be DigestKind. Shape validation does not compute a digest, authenticate a signature, bind an algorithm to supplied bytes or enforce fixed signature width. Equality/hash consistently include exact runtime type and kind.

- `ops/governance/domain/shared_kernel/value_objects/digest_kind.py` (1–27): DigestKind supplies13 named domains including Git roles, identity links and AST hashes. These tags improve domain separation only where constructors/consumers enforce them; no hash computation or signature verification occurs in the enum.

- `ops/governance/domain/shared_kernel/value_objects/domain_invariant_error.py` (1–15): DomainInvariantError preserves code and optional detail and constructs a ValueError message. It admits arbitrary strings as codes; stability/nonreflection depend on callers. One-argument event-stream errors are valid constructor calls, not TypeErrors.

- `ops/governance/domain/shared_kernel/value_objects/epoch.py` (1–55): Epoch admits only exact nonnegative Python ints, rejects bool, and increments without fixed-width overflow. It is an immutable natural-number counter; monotonicity across external state updates is not enforced by the value object alone.

- `ops/governance/domain/shared_kernel/value_objects/fence_token.py` (1–59): FenceToken similarly admits exact nonnegative ints and provides successor/stale comparison. is_stale_compared_to directly compares an external int-like value without its own type admission. Issuance, exclusive ownership and atomic compare-and-swap are not established by this counter object.

- `ops/governance/domain/shared_kernel/value_objects/id_kind.py` (1–40): IdKind is a finite role vocabulary spanning decisions, packets, principals and audit identifiers. Roles are data labels, not identity authentication or capability authority.

- `ops/governance/domain/shared_kernel/value_objects/identifier.py` (1–133): Identifier admits a restricted string alphabet and1..256 characters after stripping. Role-aware factory conversion rejects an already-wrapped wrong kind, except GENERIC intentionally preserves it. Direct kind argument is unchecked, and the apparent hex special-case also accepts the entire generic alphabet, so receipts/events/tokens need not be digest-shaped or high entropy. Equality/hash include role and exact type, not external identity provenance.

- `ops/governance/domain/shared_kernel/value_objects/mutation_action.py` (1–14): MutationAction has CREATE/MODIFY/DELETE tags. This finite action vocabulary is useful only if callers refuse values outside the enum; MutationItem direct non-string action inputs need separate admission.

- `ops/governance/domain/shared_kernel/value_objects/mutation_item_v1.py` (1–78): MutationItem validates path and action-dependent digest shapes, but non-string/non-enum action objects pass through and can skip every digest requirement. Validated digests are discarded rather than stored normalized; original uppercase/whitespace spellings remain in the record. Unused fields are unrestricted, including old digest for CREATE and new/content for DELETE. This creates canonical-encoding and closed-schema gaps before any Git effect.

- `ops/governance/domain/shared_kernel/value_objects/mutation_manifest_v1.py` (1–70): Manifest rejects empty/duplicate exact paths and computes a path-sorted NUL-delimited SHA256. Tuple storage preserves input order, so permutation-equivalent mutation collections share digest but need not compare equal. Canonical serialization assumes fields cannot contain NUL; current path/unused-field admission does not enforce that assumption, enabling an exact same-byte encoding of distinct records without a cryptographic collision. No blob content or actual Git tree is verified here.

- `ops/governance/domain/shared_kernel/value_objects/path.py` (1–97): RepoPath normalizes slashes/dot segments and offers casefolded equal-or-ancestor collision tests. It rejects leading forward slash and unresolved parent escape, but accepts drive-colon paths, NUL, and leading-backslash absolute/UNC spellings after stripping leading slashes. It is not a portable filesystem containment validator. Normalizing a/../b to b also loses the original syntactic distinction; actual symlink containment remains outside scope.

- `ops/governance/domain/shared_kernel/value_objects/sequence_number.py` (1–55): SequenceNumber implements exact nonnegative-int admission and successor, structurally parallel to Epoch but with a distinct exact runtime type. Event-stream and aggregate owners choose different gap policies; the number alone does not enforce either policy.

- `ops/governance/domain/shared_kernel/value_objects/temporal.py` (1–100): UtcTimestamp normalizes its internal datetime to aware UTC but preserves raw string spelling, including offset and date-only inputs, in value/to_iso. Naive input is silently interpreted as UTC. Equality compares datetime across subclasses while hash includes concrete type, so a subclass can violate equal-implies-equal-hash. Ordering/expiration are meaningful only under the declared UTC interpretation and supplied reference; now() is ambient clock I/O, not used here.

- `ops/governance/domain/swarm_control/__init__.py` (1–420): Every420 lines of the large swarm facade read, including the full one-line export list and all lazy targets. It mainly routes APIs and eagerly imports bootstrap_v1; single-class-per-file wording does not establish Clean Architecture or absence of import effects. It adds no execution policy or proof beyond delegated owners.

- `ops/governance/domain/swarm_control/active_lease_state.py` (1–16): Frozen ActiveLeaseState stores packet ID, path/resource tuples and optional stacking parent. No validation, lease expiry, overlap detection or authority check occurs in this carrier itself.

- `ops/governance/domain/swarm_control/agent_action.py` (1–13): AgentAction is a typing union of tool call, delegation and finish. It describes the permitted static alternatives but is not a runtime parser, dispatcher or action policy.

- `ops/governance/domain/swarm_control/agent_context.py` (1–52): AgentContext validates nonempty run/task labels and nonnegative remaining_steps, copies message/artifact sequences to tuples and shallowly freezes metadata. Nested metadata values remain mutable; step count accepts non-integer comparison-compatible values. Replacement helpers produce new context but do not decrement/enforce a budget on their own.

- `ops/governance/domain/swarm_control/agent_outcome.py` (1–20): AgentOutcome is an unvalidated frozen envelope for agent/task/status/output/handoffs. Arbitrary output and nested handoff values remain a caller responsibility; status declaration does not prove task success.

- `ops/governance/domain/swarm_control/agent_spec.py` (1–45): AgentSpec validates required nonempty strings, positive max_steps and unique tool/capability entries, then converts sequences to tuples. It does not require an exact integer step count or string-only entries, resolve provider/tool references, or validate capabilities. It is construction configuration, not operational permission.

- `ops/governance/domain/swarm_control/aggregate_error.py` (1–12): AggregateError carries a residual string in ValueError. Useful typed error channel; no stable residual whitelist or independent aggregate predicate is implemented.

- `ops/governance/domain/swarm_control/application_receipt_v1.py` (1–184): ApplicationReceipt validates several role-specific identifiers/digest shapes and checks a NUL-delimited self-digest over declared Git states/decision/token/fence/time/effect. This is internal consistency, not proof that Git changed or a human authorized it. authority_effect is hashed but never required to be None; non-int fence inputs bypass FenceToken conversion and int() can silently coerce them. Receipt ID is excluded from the digest and controls equality, so ID uniqueness needs an external registry. These constructor boundaries remain distinct from authenticated execution.

- `ops/governance/domain/swarm_control/authority_effect_v1.py` (1–12): AuthorityEffectV1 exposes only None as an enum value. Other records accepting plain strings do not automatically inherit this restriction.

- `ops/governance/domain/swarm_control/authority_fence.py` (1–23): audit_public_type returns OUT_OF_SCOPE for missing authority_effect, otherwise delegates effect validation to WindowDeclaration. A report treating OUT_OF_SCOPE as PASS would erase the missing-field boundary; this helper itself keeps the distinction. Name is coerced to string, and no actual authority capability is examined.

- `ops/governance/domain/swarm_control/authority_fence_error.py` (1–14): AuthorityFenceError carries a residual string as ValueError. It is a refusal envelope, not an authority detector or a closed code registry.

- `ops/governance/domain/swarm_control/authority_parser.py` (1–54): Active/STOP parser rejects unknown/malformed lines and returns last STOP over active declarations. It also admits true/false and coerces non-string objects via str. A STOP line wins even over conflicting Active values; this is safe-stop precedence but differs from an unqualified claim that every conflicting duplicate is refused. No user/operator authentication is inferred from parsed text.

- `ops/governance/domain/swarm_control/await_boundary.py` (1–14): AwaitBoundary freezes one pre-await CandidateBinding reference. Actual post-await comparison/revocation is delegated elsewhere; this record alone cannot prevent a time-of-check/time-of-use change.

- `ops/governance/domain/swarm_control/binding_error.py` (1–12): BindingError is a residual-carrying ValueError used by binding checks. It does not implement binding or authenticate the residual.

- `ops/governance/domain/swarm_control/blob_read_request.py` (1–17): BlobReadRequest formats git cat-file arguments from revision/path without shell interpolation. Avoiding shell parsing is useful, but the dataclass does not itself validate rev:path ambiguity, traversal or canonical revision/path admission; safe parsing must occur before construction.

- `ops/governance/domain/swarm_control/bootstrap_v1.py` (1–895): All895 lines of strict bootstrap owner read. Strong reusable mechanism: closed frozen schemas, exact bool/int authority-null fields, normalized scalar Unicode, explicit path/identifier alphabets, sorted unique finite controls, complete coverage of declared missing automation, exact15 T0 IDs, domain-separated canonical JSON hashes, duplicate/float/nonfinite refusal and exact re-encoding equality. Expiry uses an injected UTC clock and is explicitly separate from parsing. Binding verifies supplied policy/T0/schema/evidence bytes plus expected repository/base/actor labels; labels and URI digests do not authenticate real actors or prove controls effective. Parsing bounds bytes/depth/nodes, but bCR scanning precedes byte-size rejection, object serialization materializes before size rejection, and extremely long int tokens can raise host ValueError outside the typed catch. No bootstrap script, validator model or external effect executed.

- `ops/governance/domain/swarm_control/candidate_binding.py` (1–209): Candidate binding hashes repository, PR, base/head/merge base, tree/blob map, path-set, policy and evaluator identities, rederiving on construction and comparison; useful stale-review detection. MappingProxyType protects a copied outer dictionary only, despite deep-copy wording: nested wrong-type values remain mutable because runtime value types are not validated. Bool PR, empty string tree and unvalidated digest-shaped labels are admitted. A self-consistent user-created binding is not authenticated Git state, and path-set alone correctly never permits continuity. No Git access occurred.

- `ops/governance/domain/swarm_control/cas_land_license.py` (1–107): CAS license issuer now includes a random nonce by default, improving uniqueness over fixed epoch/candidate hashes. Validation checks only expiry comparison and head equality; it does not rederive license_id, validate candidate identity, enforce single use, check issuance time or perform an atomic Git CAS. NaN expiry/current values bypass >=, and unconstrained constructors permit fabricated consistent-looking records. TTL is not included in license ID. This is a local precondition token, not an execution capability by itself; secrets generator and Git were not invoked.

- `ops/governance/domain/swarm_control/census_result.py` (1–28): CensusResult.zero_open requires DIRECT source, numeric equality open_count==0 and absent/ZERO_OPEN residual. No constructor consistency check ties count to open_numbers or validates observation_binding; a fabricated DIRECT zero with a nonempty list passes this property. This is a predicate over admitted observations, not proof of a complete remote census.

- `ops/governance/domain/swarm_control/census_source.py` (1–13): CensusSource distinguishes direct from search-derived observation. The enum is useful provenance vocabulary but cannot authenticate a direct API response or prove pagination completeness.

- `ops/governance/domain/swarm_control/chaos_falsifiers.py` (1–155): Chaos helpers are finite scenario checks, not a chaos execution framework. Head-change and PATH_ONLY/NOT_APPLICABLE cases expect specific failures. The strict-measurement helper rejects only NOT_MEASURED, unlike the general STRICT predicate which rejects INJECTED and all other non-MEASURED labels. Self-judge checks use case-sensitive substring membership on unnormalized paths, so case/backslash aliases can evade and incidental substrings can overmatch. No listed protected path or embedded instruction was executed.

- `ops/governance/domain/swarm_control/cherry_receipt.py` (1–25): CherryReceipt converts argv/stdout sequences to tuples and stores exit/head labels. It supplies no subprocess authentication or completeness guarantee; arbitrary caller-created values remain possible. Later validation checks only a finite grammar/binding subset.

- `ops/governance/domain/swarm_control/configuration_error.py` (1–12): ConfigurationError is a named SwarmRuntimeError subclass, distinguishing configuration failures in caller control flow; no validation logic is implemented here.

- `ops/governance/domain/swarm_control/conflict_graph_admission.py` (1–130): Conflict admission counts active mapping entries against N and compares exact path-string sets. This computes finite set intersection, not hierarchical/casefold/path-normalized conflict: a versus a/file and A versus a remain disjoint. Capacity is snapshot-local without atomic reservation, and ceiling/candidate IDs lack domain checks. It can be reused only after a canonical conflict relation and admitted active-set snapshot are supplied.

- `ops/governance/domain/swarm_control/context_mismatch.py` (1–12): ContextMismatch is a named runtime exception for scope routing errors. It does not compute a task-scope relation or enforce boundaries by itself.

- `ops/governance/domain/swarm_control/council_bridge.py` (1–207): Full legacy council bridge read. Correctly refuses to verify configured decisions and marks arithmetic as advisory; optional signature callback is not an authentication default. It validates vote types/unique member labels, participation bounds and optional exact electorate, then compares AYE share over all participating votes including abstentions. Fraction thresholds are exact; float thresholds intentionally retain historical float comparisons. Tally maps RATIFIED to APPROVED only in a legacy record. Distinct labels and optional signatures do not prove independent voters; no clock/verifier invoked.

- `ops/governance/domain/swarm_control/council_resolution_status.py` (1–16): Five council status tags distinguish approval, ratification, rejection, missing quorum and split status. No voting policy is encoded in the enum and advisory meanings remain with council_bridge.

- `ops/governance/domain/swarm_control/council_resolution_v1.py` (1–26): CouncilResolutionV1 is an unvalidated legacy record of votes/counts/status/identity/time and an editable-at-construction authority string. It does not ensure counts match votes. The bridge deliberately refuses this as configured-decision verification evidence.

- `ops/governance/domain/swarm_control/council_resolution_verification_result.py` (1–26): Verification-result carrier fixes advisory_only=True and authority_effect=None outside its constructor parameters. This is a useful explicit non-admission boundary, although count/status consistency still belongs to the producing function.

- `ops/governance/domain/swarm_control/council_vote_choice.py` (1–16): AYE/YES and NAY/NO are enum aliases, with ABSTAIN a third distinct choice. Tally therefore does not double-count aliases; the vocabulary contains three underlying values, not five independent choices.

- `ops/governance/domain/swarm_control/council_vote_record.py` (1–18): Council vote record stores member label, choice and optional rationale/signature/time strings. It does not validate signature, timestamp or eligibility at construction; council_bridge provides selected structural checks only.

- `ops/governance/domain/swarm_control/decision_outcome.py` (1–14): DecisionOutcome finite ACCEPT/HOLD/REJECT vocabulary. A tag is not external human authorization or proof that the requested effect is safe.

- `ops/governance/domain/swarm_control/decision_status_v1.py` (1–15): DecisionStatusV1 adds NOT_YET_CREATED to accepted/held/rejected status vocabulary. Useful lifecycle distinction; no state transition relation is implemented here.

- `ops/governance/domain/swarm_control/decision_validation_error.py` (1–12): DecisionValidationError inherits the shared code/detail refusal format. No additional predicate or constructor behavior is introduced.

- `ops/governance/domain/swarm_control/delegate.py` (1–14): Delegate wraps a Task as a frozen action record. It does not create an agent, prove task preservation or authorize delegation; those are dispatcher/caller responsibilities.

- `ops/governance/domain/swarm_control/dev_vs_strict.py` (1–53): Mode coercion rejects unknown strings and non-string/non-enum inputs. STRICT requires every supplied status to equal MEASURED and rejects OPTIONAL_SKIP; DEV rejects only NOT_MEASURED and otherwise accepts arbitrary status labels. An empty required mapping passes vacuously, so completeness of the required obligation set must be checked by a caller. These are finite label predicates, not measurement provenance.

- `ops/governance/domain/swarm_control/direct_pr_census.py` (1–95): Direct census distinguishes adapter failure/malformed payload from zero results and refuses search-only results as terminal evidence. It delegates filtering/pagination/completeness to supplied fetch ports, coercing PR numbers with int and not validating uniqueness or state. observation.setdefault can retain a conflicting caller-supplied repository label. Search payload conversion is outside the guarded failure block. No adapter was called; an empty direct response alone cannot establish remote completeness without the port contract.

- `ops/governance/domain/swarm_control/disposal_decision.py` (1–16): DisposalDecision records may_dispose/residual/force/proof but validates none of their consistency. It is a result envelope whose authority depends on the caller and the underlying disposal predicate.

- `ops/governance/domain/swarm_control/duplicate_task.py` (1–12): DuplicateTask is an exception taxonomy leaf for repeated task IDs. This file does not maintain a registry or enforce uniqueness.

- `ops/governance/domain/swarm_control/epic_integration_id_map.py` (1–71): Canonical epic mapping hardcodes10 AUTOMATED labels for IDs67..76 and hashes their sorted JSON descriptions/test filenames. That digest certifies only this declaration list; no file existence, test execution, source hash or automation adequacy is checked. Direct registry construction can also supply an unrelated digest.

- `ops/governance/domain/swarm_control/event_journal.py` (1–33): EventJournal append enforces contiguous sequence starting at0 and exposes tuple snapshots, while its backing list remains in-memory mutable. rewrite_forbidden is a deliberately failing method, not immutable storage or authenticated history. Bool/float sequence equality is not excluded. No persistence or concurrent append exclusion is implemented.

- `ops/governance/domain/swarm_control/event_tape.py` (1–96): EventTape constructs sequential payload/entry hashes and replay rechecks integrity, exact index and previous hash from a zero genesis. Useful local hash-chain consistency; without a trusted external terminal hash it cannot detect replacing/recomputing the whole chain or truncating a valid prefix. No state-machine transition, unique event ID or timestamp monotonicity rule is checked. Default now is ambient clock behavior, not used here.

- `ops/governance/domain/swarm_control/event_tape_entry_v1.py` (1–217): Full tape-entry body reread after one truncated display. Recursively freezes JSON containers and rejects unsupported/nonfinite values, then verifies payload hash and a framed entry hash. It does not enforce exact-int seq, mapping-only payload root, closed transition vocabulary or hex previous hash beyond length. Replay integrity recomputes hashes but is not authentication; self-consistent alternative entries remain possible. Finite floats and raw timestamp spelling make this its own serialization profile, distinct from strict bootstrap canonical JSON.

- `ops/governance/domain/swarm_control/event_tape_error.py` (1–15): EventTapeError stores stable code/detail when supplied by callers. It is an integrity-refusal carrier, not a cryptographic verification implementation.

- `ops/governance/domain/swarm_control/evidence_freshness_rebind.py` (1–98): Freshness predicate conservatively invalidates reconciliation/rebase/head-string drift and only otherwise marks usable. The FRESH reason says byte-exact although the implementation merely compares supplied head labels; equal empty/untrusted labels also pass. It does not check evaluator/policy/dependency/environment changes or execute reruns. Useful invalidation policy with admitted provenance prerequisites.

- `ops/governance/domain/swarm_control/evidence_status.py` (1–37): Required-evidence aggregation is comparatively strict: exact list/tuple container, nonempty maximum10000 entries, exact EvidenceStatus enum members and all PASS. It rejects both unknown types and non-PASS states; it still cannot establish completeness of the supplied required set or authenticity of PASS evidence.

- `ops/governance/domain/swarm_control/exact_blob_reconciliation.py` (1–114): Exact-blob reconciliation computes all path keys, delegates each decision, refuses unresolved/unhandled decisions, handles deletions explicitly and marks output NOT_RERUN_AFTER_RECONCILIATION. This is a finite map merge, not a Git tree build or content verification. Returned path_blobs is a mutable dict under a frozen wrapper and stored digest is not subsequently rechecked. Ownership/conflict semantics depend on the separately read classifier.

- `ops/governance/domain/swarm_control/finish.py` (1–14): Finish wraps arbitrary output as an action signal. It does not validate success or cause execution; runtime interpretation is outside this carrier.

- `ops/governance/domain/swarm_control/git_hygiene_policy.py` (1–119): Git hygiene parses selected global options and refuses broad add without -- and explicit force worktree removal. Unknown/attached globals stop parsing and then default allow, while add -- . or broad magic pathspecs pass because post-delimiter paths are not narrowed. Shell strings use POSIX shlex with a fallback split, so this is not a universal shell command policy. It should be treated as a bounded argv lint rule, not complete command authorization.

- `ops/governance/domain/swarm_control/git_object_address.py` (1–26): parse_blob_spec refuses every input, intentionally eliminating combined rev:path input. safe_blob_read accepts separate string-coerced values but only rejects colon; empty, control, traversal and arbitrary revision labels remain unchecked. It returns a request, does not read committed bytes or authenticate the target Git object.

- `ops/governance/domain/swarm_control/human_decision_v1.py` (1–219): HumanDecision constructs role-labeled identifiers/digest shapes and stores a manifest/principal record. Validation requires ACCEPT, excludes five exact lowercased principal names, checks allowed-effect string and expiry/order. It neither verifies principal signatures/key registry nor enforces nonce entropy, one-use consumption, nonfuture issue time, repository binding, manifest correctness or authority_effect=None. These are local declared-input checks; arbitrary non-banned actor labels are not authenticated human decisions. Original model not executed.

- `ops/governance/domain/swarm_control/identity_contract_error.py` (1–12): IdentityContractError provides a code-only refusal channel. It implements no identity or byte-binding predicate.

- `ops/governance/domain/swarm_control/identity_domain_v1.py` (1–17): IdentityDomainV1 gives six distinct byte-identity domains for problem/presentation/execution/evidence/decision/application. The tags support domain-separated hashing but are not stage-execution evidence.

- `ops/governance/domain/swarm_control/identity_links_v1.py` (1–323): Identity links require exact reference/sentinel types, slot domains, future decision/application sentinels and authority None. Canonical ASCII JSON uses exact closed keys, duplicate/number refusal,4096-byte input ceiling, reserialization equality and domain-separated hashes with constant-time digest comparison. However evidence-before-execution is enforced only by with_evidence; constructor/parser allow a real evidence ref alongside execution NOT_YET_CREATED. Digest equality checks supplied bytes against a trusted expectation only if the caller authenticates that expectation. No private identity material accessed.

- `ops/governance/domain/swarm_control/identity_ref_v1.py` (1–48): IdentityRefV1 rejects subclasses, wrong enum types, malformed schema, non-lowercase/non64-hex or all-zero digests. This is a useful closed representation boundary; a nonzero digest string alone does not prove payload existence or correct schema semantics.

- `ops/governance/domain/swarm_control/identity_slot_v1.py` (1–17): IdentitySlotV1 supplies the same six labels in a distinct enum class from identity domains. Exact enum admission elsewhere prevents accidental slot/domain interchange; this file contains no lifecycle logic.

- `ops/governance/domain/swarm_control/illegal_transition.py` (1–20): IllegalTransition stores source/destination and a diagnostic string. It identifies reducer failures but neither enumerates legal edges nor protects private data reflected in detail.

- `ops/governance/domain/swarm_control/journal_event.py` (1–21): JournalEvent is an unvalidated frozen envelope with mutable nested payload and caller-supplied sequence/schema/state. Its event_type and payload are not checked by the reducer. It is not independently append-only or authenticated.

- `ops/governance/domain/swarm_control/journal_reducer.py` (1–62): Pure per-packet reducer implements a seven-state directed graph with selected backwards review edges, requiring initial ADMITTED and strictly increasing packet-local sequence. Gaps from other packets are permitted. It ignores event_type/schema/payload and does not verify transition-specific human/lease/evidence conditions; legal state labels alone cannot prove a valid merge. Other packet events are skipped entirely.

- `ops/governance/domain/swarm_control/lease_denied.py` (1–16): LeaseDenied records holder and path/resource conflicts for diagnostics. It does not compute overlap or verify the alleged holder.

- `ops/governance/domain/swarm_control/lease_error.py` (1–13): LeaseError is the shared code/detail ValueError pattern specialized by name. It provides a typed failure channel without enforcing lease semantics.

- `ops/governance/domain/swarm_control/lease_grant.py` (1–15): LeaseGrant stores packet/path/resource labels with no validation. A constructed grant is not proof of current registry ownership or expiry.

- `ops/governance/domain/swarm_control/lifecycle_status_v1.py` (1–17): LifecycleStatusV1 enumerates six declaration-to-handoff stages. No transition relation or evidence predicate connects those stages in this file.

- `ops/governance/domain/swarm_control/main_readonly.py` (1–39): Main-readonly policy resolves paths with the separately reviewed, environment-dependent path_canon helper and compares containment against the declared main root. This is a useful caller-relative path guard; Path.resolve can consult filesystem/symlinks and fallback normalization is weaker. It does not bind a subsequent operation atomically to the resolved path or authenticate write intent. No real filesystem operation was executed.

- `ops/governance/domain/swarm_control/memory_record.py` (1–18): MemoryRecord groups agent/task labels, messages and outcome without cross-field binding or deep immutability checks. It records context, not persistent trustworthy memory or evidence of successful learning.

- `ops/governance/domain/swarm_control/merge_capability.py` (1–71): Merge capability discovery explicitly preserves unavailable-adapter residuals and refuses silent substitution of requested known methods. bool(settings value) admits nonempty false-like strings as enabled, so adapter settings need exact boolean validation. A manually constructed record can make supports differ from request for unknown methods. Observation repository labels are caller-supplied and not authenticated.

- `ops/governance/domain/swarm_control/merge_mutex.py` (1–146): Merge mutex forbids automatic stale takeover and returns an explicit STALE_RECOVERED record before reacquisition; release checks active token ID and expiry. It is mutable in-memory state without thread/process atomicity or durable audit. Recovery does not establish prior worker termination/fencing, and token IDs deterministically repeat for the same holder/time/TTL. NaN time/TTL is not admitted/refused explicitly and can defeat expiry. Comments about serialization need these operational prerequisites.

- `ops/governance/domain/swarm_control/message.py` (1–36): Message validates nonempty role and string content and shallowly freezes a copied metadata map. Role is not restricted to a trusted vocabulary, name is unchecked and nested metadata remains mutable. It is a carrier, not a prompt-authority boundary or ingress byte ceiling.

- `ops/governance/domain/swarm_control/mode.py` (1–13): Mode is the two-tag DEV/STRICT vocabulary; actual provenance rules are in dev_vs_strict.

- `ops/governance/domain/swarm_control/mode_verdict.py` (1–14): ModeVerdict wraps a boolean and optional residual without consistency checks. It carries the finite predicate result but is forgeable as ordinary construction data.

- `ops/governance/domain/swarm_control/n1_lease.py` (1–87): N1Lease canonicalizes identifier roles and path/resource collections, but direct non-int epoch/fence inputs bypass value-object conversion. It does not check nonempty scope, issue-before-expiry, exact boolean killed flag or expiry. ID-based equality does not compare scope/time/owner. It is a lease record, not proof of current authority.

- `ops/governance/domain/swarm_control/n1_lease_registry.py` (1–119): Registry grants increasing fences and rejects same-worktree path/resource overlap; revocations are sticky by supplied string key, and epoch changes invalidate old leases. Verification checks owner/epoch and only rejects lower fences, then trusts the supplied lease expiry: same-ID copies with larger fence, expanded scope or extended expiry are not compared to the stored grant. Keys are stored before Identifier normalization, and resources are checked only within equal worktree labels. Durable in-memory wording overstates persistence and no atomic concurrency mechanism exists.

- `ops/governance/domain/swarm_control/no_agent_available.py` (1–12): NoAgentAvailable is a runtime error category; no agent census or routing algorithm resides here.

- `ops/governance/domain/swarm_control/nonforce_disposal.py` (1–187): Disposal checks ancestor declaration or a typed cherry receipt with zero exit, bound argv heads and nonempty +/- hex-line grammar; any plus blocks ordinary disposal. Trailing argv after the two head fields is accepted, so receipt scope is not an exact fixed command contract. Typed caller-created records do not authenticate subprocess output. force=True bypasses failed/missing evidence with a HUMAN_ONLY label but no human-auth check in this function. No deletion or Git command was run.

- `ops/governance/domain/swarm_control/not_yet_created.py` (1–19): NotYetCreated validates an exact IdentitySlot enum and separates absence from fabricated identity references. It is a useful explicit sentinel; construction does not prove historical absence outside the model.

- `ops/governance/domain/swarm_control/outcome_status.py` (1–13): OutcomeStatus contributes only COMPLETED/DELEGATED vocabulary. Enum membership does not establish completion, task correctness, or an error policy.

- `ops/governance/domain/swarm_control/packet_state.py` (1–18): PacketState names seven lifecycle stages for the separately reviewed journal reducer. The enum does not implement transitions or require stage-specific certificates.

- `ops/governance/domain/swarm_control/parse_disposition.py` (1–14): ParseDisposition supplies ACTIVE/STOP/REFUSED lexical outcomes; no parsing or authorization is implemented here.

- `ops/governance/domain/swarm_control/parse_result.py` (1–16): ParseResult is a frozen disposition/residual/value record without constructor validation. Its utility is explicit parser output packaging, not proof that the payload matches the tag.

- `ops/governance/domain/swarm_control/path_canon.py` (1–77): Path canonicalization resolves against the current working directory and filesystem with Path.resolve(strict=False), then applies platform case normalization; exceptions fall back to normpath. This is environment-dependent observation, not a purely lexical or atomic filesystem boundary. canonical_repo_path silently drops leading slash and excess parent components: ../a becomes a. Prefix containment/conflict is useful only under a shared canonical-root convention; POSIX root / yields a // prefix and fails to contain /a. No source helper was executed against the real filesystem.

- `ops/governance/domain/swarm_control/path_lease_registry.py` (1–78): PathLeaseRegistry provides an in-memory overlap table over canonicalized paths. Caller-supplied stacked_under skips checks against that lease without validating lineage, and reusing packet_id can overwrite an existing disjoint lease, losing its former scope. There is no expiry, fencing, persistence, lock, or atomic relationship with filesystem operations.

- `ops/governance/domain/swarm_control/pin_check.py` (1–15): PinCheck is an unchecked frozen ok/residual/pin_sha result. It packages a comparison result without performing comparison or establishing observed Git identity.

- `ops/governance/domain/swarm_control/policy_denied.py` (1–12): PolicyDenied is a typed exception only. Its immutable-prime-rule docstring is a policy label, not an enforced predicate in this file.

- `ops/governance/domain/swarm_control/portable_reference_scanner.py` (1–118): Portable-reference scanning applies four concrete regex families to supplied text and records every match. It is a useful bounded local-path detector, not universal portability certification: a matching allow-pattern substring suppresses the entire line, and the empty allow-pattern suppresses all lines. Drive-forward-slash and deliberately excluded hidden-directory forms remain outside this profile.

- `ops/governance/domain/swarm_control/post_await_revalidate.py` (1–57): Post-await revalidation rebuilds a candidate from supplied live head/tree/blob observations and distinguishes stale head from stale binding. Missing optional tree/blob observations fall back to the old values and policy/evaluator labels are copied, so success is conditional on caller freshness. Re-deriving path_set only from blobs can falsely stale an unchanged tree-only binding carrying an explicit path set. This is a comparison kernel, not a fresh observation service.

- `ops/governance/domain/swarm_control/postmerge_closure_census.py` (1–68): Postmerge closure census sorts/deduplicates supplied open PR numbers, rejects membership of the merged PR, and hashes the resulting declaration. Empty supplied census always closes; no authoritative fetch, pagination, repository membership, or completeness check is performed. Reusable finite nonmembership witness only under authenticated complete-census admission.

- `ops/governance/domain/swarm_control/postmerge_content_witness.py` (1–106): Postmerge content witness compares every expected blob and rejects extra observed paths, binding both maps and head/candidate labels into a digest. With string-valued maps this expresses exact finite equality. Type admission is absent: expected {a: None} and observed {} pass the .get comparison, so missing and explicitly null values collapse. Returned dicts are mutable despite the frozen wrapper. No actual Git observation is established.

- `ops/governance/domain/swarm_control/principal_evidence_v1.py` (1–74): PrincipalEvidenceV1 explicitly supplies syntax-checked references to an injected external verifier. Identifier roles, signature-digest shape, and allowed scheme labels are checked; cryptographic verification and principal trust are intentionally outside this record. Reuse as an evidence envelope only, preserving that stated boundary.

- `ops/governance/domain/swarm_control/qualification_n1_engine.py` (1–134): N1 qualification is a deterministic synthetic lifecycle harness: it appends LEASED/BOUND without obtaining a lease/binding, uses fixed epochs and promised base as observed base, records LANDED without Git mutation, defaults observed blobs to expected blobs, and appends disposal/pruning labels without performing them. It can exercise finite refusal branches, but its complete-lifecycle language is not operational end-to-end evidence. Receipt hash binds labels/states/head, not the complete content and write-scope population.

- `ops/governance/domain/swarm_control/qualification_n2_engine.py` (1–140): N2 qualification constructs two disjoint declared packets, simulates stale-head refusal and conservative rebind, then grants a fresh license after a comment asserting fresh evidence without invoking an evidence executor. Fixed epochs, local mutex, promised-as-observed blob defaults and absent Git/agent/human execution make this a finite scenario harness. The receipt digest omits the full candidate/content population; no concurrent production qualification follows.

- `ops/governance/domain/swarm_control/qualification_n4_engine.py` (1–100): N4 qualification counts supplied admissions/collisions and compares second/fourth patch-digest labels. Expected scenario outcomes are not asserted, equal empty digest strings are accepted, and the fourth admitted packet is not registered. The digest covers aggregate counters rather than the input population. Useful scenario accounting, not demonstrated four-worker isolation or enforced N4 success.

- `ops/governance/domain/swarm_control/quorum_threshold.py` (1–25): QuorumThreshold checks a 0.5-to-1 interval and positive minimum via comparisons, without exact-type or finiteness admission; NaN bypasses the interval comparisons. The already read council bridge independently revalidates thresholds, so this constructor weakness is not an end-to-end council bypass. Default 0.66 is the declared policy value, not exact two-thirds.

- `ops/governance/domain/swarm_control/rebind_after_merge.py` (1–69): Rebind-after-merge marks each active obligation stale and always returns ready_to_land=False, including unchanged heads or no obligations. This is a useful conservative invalidation record, not an actual branch rebase, evidence refresh, or land-license gate.

- `ops/governance/domain/swarm_control/receipt_validation_error.py` (1–15): ReceiptValidationError carries code/detail for typed refusal. It implements no receipt validation or custody policy itself.

- `ops/governance/domain/swarm_control/reconciliation_classifier.py` (1–177): Three-way reconciliation is an explicit ownership-first policy. Current actor ownership always chooses branch, even when only main changed; foreign ownership always chooses main, even when only branch changed. Only unowned paths use ordinary base/branch/main equality rules and otherwise yield UNRESOLVED. This is reusable if ownership is admitted as authority, not generic conflict-free preservation. Ledger hashing sorts all declared fields but neither authenticates ownership nor rejects duplicate paths.

- `ops/governance/domain/swarm_control/revalidate_result.py` (1–16): RevalidateResult is an unchecked frozen ok/residual/live record. It carries a comparison result without independently observing or validating live state.

- `ops/governance/domain/swarm_control/review_pin.py` (1–14): ReviewPin is an unchecked PR-number/head-SHA carrier; no remote lookup or content binding is supplied.

- `ops/governance/domain/swarm_control/review_worktree_pin.py` (1–21): Review-worktree pinning rejects empty SHA and compares exact supplied head labels. It neither creates a worktree nor fetches the PR, checks tree contents, or binds review rules. Useful equality guard under a trusted observation port.

- `ops/governance/domain/swarm_control/runtime_event.py` (1–36): RuntimeEvent validates nonempty event/run/subject labels and shallow-freezes metadata. Its stated observational role is useful separation from authority, but nested metadata can mutate and the record does not authenticate the described fact.

- `ops/governance/domain/swarm_control/semantic_contract.py` (1–43): SemanticContract rejects subclasses and delegates authority-effect fencing, but its ID is unchecked and no semantic predicate is executed. Equality-based conditional normalization leaves direct string None unchanged because the string enum compares equal to that string; the factory normalizes it. No authority escalation follows because only the NONE effect is admitted.

- `ops/governance/domain/swarm_control/step_limit_exceeded.py` (1–12): StepLimitExceeded is an exception leaf; step accounting and enforcement must occur at an external caller.

- `ops/governance/domain/swarm_control/swarm_n10_skeleton.py` (1–121): N10 skeleton honestly disclaims full production DoD and runs a serial synthetic scenario with fixed epochs and fabricated head labels. Its active-write map is keyed by candidate ID: repeated IDs with disjoint paths overwrite entries, so the dictionary count can stay below n_ceiling while the admitted list grows arbitrarily. Missing per-candidate observations default to promised blobs. is_successful is always True even with zero admitted candidates. Reuse as a scenario scaffold only after unique-ID admission and explicit success criteria.

- `ops/governance/domain/swarm_control/swarm_recovery_playbook.py` (1–154): Recovery playbook is a deterministic hashed dry-run plan, not an executor. Orphan leases, detached worktrees, and head drift map to declared actions; dirty-prune planning lacks data custody checks. UNBACKED_PR is encoded with RELEASE_ORPHAN_LEASE even though its target/description concerns a PR, a semantic dispatch mismatch if a consumer trusts action_type. Unknown drift kinds are refused. No planned action was executed.

- `ops/governance/domain/swarm_control/swarm_runtime_error.py` (1–10): SwarmRuntimeError is the base exception for explicit runtime failures, with no operational semantics of its own.

- `ops/governance/domain/swarm_control/swarm_status_reconciliation.py` (1–172): Swarm status reconciliation compares supplied packet membership with lease/worktree/PR bindings, emits finite orphan/detached/unbacked records, and hashes the entire supplied mapping population. HEAD_DRIFT exists as a tag but is never detected here because no second head observation is compared. The returned snapshot discards the original binding maps, so its serialized form alone cannot reconstruct its digest. This is caller-relative accounting, not an authoritative remote census.

- `ops/governance/domain/swarm_control/swarm_task_limit_exceeded.py` (1–12): SwarmTaskLimitExceeded names a bounded-task refusal but performs no task counting itself.

- `ops/governance/domain/swarm_control/task.py` (1–37): Task validates ID, goal, and optional capability labels and shallow-freezes payload. It is an admitted work description, not policy enforcement, deep immutability, or a proof the goal is executable.

- `ops/governance/domain/swarm_control/terminal_status_v1.py` (1–13): TerminalStatusV1 explicitly names OPEN_OBSTRUCTION and REFUSED. These useful non-success labels do not implement an obstruction proof calculus.

- `ops/governance/domain/swarm_control/tool_call.py` (1–32): ToolCall validates nonempty call/tool labels and shallow-freezes arguments. Allowed-tool resolution, argument schema validation, rate/capability checks, and execution remain external; nested arguments remain mutable.

- `ops/governance/domain/swarm_control/tool_not_found.py` (1–12): ToolNotFound is an exception leaf; no tool registry or resolver exists in this file.

- `ops/governance/domain/swarm_control/tool_result.py` (1–17): ToolResult is an unchecked result envelope containing arbitrary content and an is_error flag. It does not authenticate execution or validate correlation to a tool call.

- `ops/governance/domain/swarm_control/universal_transport_receipt.py` (1–160): Universal transport classification now explicitly refuses absent digests for claims about bytes and gives same-path/same-digest NOT_APPLICABLE; relocation cannot be NOT_APPLICABLE through the constructor. This repairs the documented unmeasured-to-verified branch at the declared-record level. VERIFIED still means predicates over supplied labels: empty or malformed non-None digests pass, redirect/deletion are caller flags, and no bytes/existence/redirect semantics are observed. Direct constructor admits inconsistent VERIFIED shapes except its one locus invariant. Useful mutation-evidence classifier with an external measurement and canonical-digest admission requirement.

- `ops/governance/domain/swarm_control/unsafe_git_address.py` (1–12): UnsafeGitAddress is a ValueError with a default residual string. It supports typed refusal from the separately reviewed Git-address owner, not independent parsing.

- `ops/governance/domain/swarm_control/value_objects/__init__.py` (1–84): Compatibility export surface delegates all listed IDs, digests, paths, timestamps, fences, epochs and mutation records to the shared kernel already fully read in this scope. The complete imports and __all__ were read. No separate mathematical mechanism or stronger guarantees arise from the swarm-control namespace.

- `ops/governance/domain/swarm_control/value_objects/digest.py` (1–5): Five-line compatibility re-export of shared-kernel Digest. It retains the same lexical digest admission and its limitations; no new digest implementation.

- `ops/governance/domain/swarm_control/value_objects/digest_kind.py` (1–5): Five-line compatibility re-export of DigestKind. It adds no algorithm or constructor enforcement.

- `ops/governance/domain/swarm_control/value_objects/domain_invariant_error.py` (1–5): Five-line compatibility re-export of DomainInvariantError. It adds no validation behavior.

- `ops/governance/domain/swarm_control/value_objects/epoch.py` (1–5): Five-line compatibility re-export of Epoch. The shared-kernel exact value semantics are inherited, not independently implemented.

- `ops/governance/domain/swarm_control/value_objects/fence_token.py` (1–5): Five-line compatibility re-export of FenceToken. It adds no durable fencing authority or monotone allocator.

- `ops/governance/domain/swarm_control/value_objects/id_kind.py` (1–5): Five-line compatibility re-export of IdKind. It adds no namespace or trust policy.

- `ops/governance/domain/swarm_control/value_objects/identifier.py` (1–5): Five-line compatibility re-export of Identifier. Shared-kernel label checks remain the only implementation.

- `ops/governance/domain/swarm_control/value_objects/mutation_action.py` (1–5): Five-line compatibility re-export of MutationAction. It adds no action execution or mutation admission.

- `ops/governance/domain/swarm_control/value_objects/mutation_item_v1.py` (1–5): Five-line compatibility re-export of MutationItemV1. It retains the reviewed constructor boundary limitations and does not create a second checker.

- `ops/governance/domain/swarm_control/value_objects/mutation_manifest_v1.py` (1–6): Six-line compatibility re-export of MutationManifestV1 and compute_manifest_sha256. The same NUL-delimited preimage encoding is used; this is not an independent integrity mechanism.

- `ops/governance/domain/swarm_control/value_objects/path.py` (1–5): Five-line compatibility re-export of RepoPath and RepositoryPath. It inherits the shared lexical path admission rather than the different runtime path_canon helper.

- `ops/governance/domain/swarm_control/value_objects/temporal.py` (1–5): Five-line compatibility re-export of TimestampUtc and UtcTimestamp. No new timezone normalization or canonical serialization is introduced.

- `ops/governance/domain/swarm_control/window_declaration.py` (1–50): WindowDeclaration admits only the NONE authority effect and rejects subclasses, with exact-type equality/hash. Direct string None can remain a string because equality rather than identity decides assignment; factory creation canonicalizes. The name is unchecked and the declaration does not actually enforce a time window. It is a label fence, not scheduling or authorization.

- `ops/governance/domain/swarm_control/work_packet_v1.py` (1–114): Work-packet mapping validation requires named fields, nonempty primary labels, nonempty write-path tuple, string sequence elements and the NONE effect; it trims primary labels. It does not validate SHA shape, canonical/unique paths, write-versus-forbidden conflicts, or empty individual path strings, and ignores supplied schema/unknown fields. Direct dataclass construction checks only exact class and authority effect, bypassing those mapping checks. Thus this is an input-shape adapter, not a closed work-scope or concurrency certificate.

- `ops/governance/domain/swarm_control/work_packet_validation_error.py` (1–12): WorkPacketValidationError carries the mapping-validator residual string. It has no admission or enforcement behavior outside that error envelope.
