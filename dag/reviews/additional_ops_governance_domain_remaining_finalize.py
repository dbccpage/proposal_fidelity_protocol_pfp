"""Add source-grounded conclusions to the complete source-reading receipt."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_ops_governance_domain_remaining'
def h(b):return hashlib.sha256(b).hexdigest()
def load(s):return json.loads(Path(str(P)+s).read_bytes())
scope=load('_scope.json');report=load('.json');controls=load('_controls.json')
assert report['summary']['full_source_reads']==164 and report['summary']['pending']==0
def ev(i,a,z):
 row=scope['files'][i];b=(R/row['path']).read_bytes()
 assert h(b)==row['sha256'] and 1<=a<=z<=len(b.decode('utf8').splitlines())
 return {'path':row['path'],'sha256':row['sha256'],'lines':[a,z]}
claims=[];findings=[]
def claim(title,assessment,refs,limits,reuse):
 claims.append({'id':f'OGD-C{len(claims)+1:02d}','title':title,'assessment':assessment,'source_evidence':[ev(*r) for r in refs],'evidence_kind':'full source-semantic review; no original execution','limits':limits,'workflow_reuse':reuse})
def finding(title,assessment,refs,tests,limits,action,priority='P2'):
 findings.append({'id':f'OGD-F{len(findings)+1:02d}','title':title,'assessment':assessment,'priority':priority,'source_evidence':[ev(*r) for r in refs],'independent_controls':[f'OGD-T{n:02d}' for n in tests],'limits':limits,'next_action':action})

claim('Strict bootstrap is a substantive closed codec and byte-binding mechanism.',
 'The bootstrap owner implements closed frozen schemas, exact authority-null/boolean/integer admission, normalized Unicode and paths, sorted unique control coverage, exact T0 identity population, canonical domain-separated JSON hashes, duplicate/float/nonfinite refusal, re-encoding equality, explicit currency checks, and binding of supplied evidence/schema/policy/T0 bytes. These mechanisms are materially stronger than label-only records elsewhere in the same package.',
 [(50,65,160),(50,304,326),(50,396,425),(50,433,561),(50,606,649),(50,691,772),(50,788,879)],
 'Source reasoning, not a fresh Pydantic/runtime run or a proof that controls are effective. Byte bindings authenticate consistency of supplied material, not actual human identity. Large integer and ordering-of-size-check limitations remain in the file assessment.',
 'Retain canonical record codec + explicit byte binding + injected currency check as separate workflow stages; carry admitted provenance and task-specific control adequacy separately.')
claim('Finite event and result mechanisms have precise conditional algebraic meanings.',
 'AggregateRoot requires the next version; EventStream requires only a larger version. Journal reduction checks a finite seven-state transition relation with packet-local monotone sequences. Hash-chain replay detects local content/ordering inconsistency; Ok/Err implement conventional result branching under typed pure callbacks. These are finite state and consistency mechanisms rather than proofs of operational authorization.',
 [(11,1,51),(16,1,32),(18,1,44),(19,1,44),(76,1,96),(93,1,62)],
 'Exact line ranges are limited to these full owners; transition-specific authorization and external authenticated roots are not supplied by the state labels or hash chain. Arbitrary Python callback effects are outside result-law reasoning.',
 'Reuse explicit state transitions and local transcript consistency, while keeping actual lease/review/human predicates as independent prerequisites.')
claim('Required evidence aggregation preserves explicit non-success states.',
 'aggregate_required admits an exact list/tuple of 1..10000 exact EvidenceStatus values and returns PASS only if every item is the PASS enum. The ordinary STRICT measurement policy refuses every provenance except MEASURED, including injected and skipped values. Rebinding conservatively marks outstanding obligations stale and never itself claims ready-to-land.',
 [(80,13,37),(70,33,53),(127,1,69)],
 'Empty required-measurement mappings are not populated by this function, and provenance strings remain caller declarations. The narrower chaos scenario helper is not equivalent to the general STRICT checker.',
 'Retain nonempty explicit required-status conjunction and stale-evidence invalidation, bound to a separately frozen required-obligation population.')
claim('Council tallying explicitly remains advisory.',
 'The council bridge validates electorates/votes and uses exact Fraction threshold arithmetic, while verify_council_resolution explicitly refuses to establish authority. PrincipalEvidence likewise states its syntax-only role for an injected verifier. This is an appropriate separation of tally/data shape from authorization.',
 [(60,36,73),(60,87,167),(60,170,207),(122,1,74)],
 'No configured trusted verifier, cryptographic validation, or authorized human action was demonstrated. QuorumThreshold alone is weaker than the bridge revalidation.',
 'Reuse finite advisory vote tally as advisory evidence, never as an implicit execution capability.')
claim('Candidate and post-await bindings support conditional stale-state detection.',
 'Candidate identity includes repository, PR, base/head/merge-base, tree/blobs, path-set, policy and evaluator labels; construction/revalidation rederive the digest. Post-await comparison distinguishes head drift and other binding drift. Review pinning and postmerge census are narrower equality/nonmembership predicates over observations supplied by callers.',
 [(51,36,107),(51,124,209),(119,21,57),(132,1,21),(120,41,68)],
 'No Git or remote observations were made; copied policy/evaluator labels and fallback tree/blob observations are not evidence of freshness. Runtime type/deep-freeze and tree-only path-set gaps remain explicit.',
 'Use observation acquisition, binding, await, fresh reacquisition, and equality comparison as distinct stages; preserve the exact task/repository/head and measurement provenance.')
claim('Current transport and content witnesses improve their declared finite predicates.',
 'Transport now refuses absent content digests for byte claims and reports same-path/same-digest NOT_APPLICABLE. Postmerge content comparison checks expected and extra observed paths, and its digest binds both maps. On the admitted string-map domain, the independent 81-pair control agrees with exact map equality.',
 [(146,97,160),(121,50,106)],
 'The 81-pair reconstruction is finite independent arithmetic, not an execution of original functions. VERIFIED remains relative to supplied digest labels; malformed present values and mutable maps require additional admission.',
 'Retain measured mutation-shape classification and exact map comparison under canonical typed digests, independently observed bytes and immutable evidence storage.')

finding('Mutation manifest framing admits an exact prehash ambiguity.',
 'The path/action/old/new/content sequence is NUL-delimited, but RepoPath admits NUL and CREATE leaves old digest unrestricted. Distinct records (path a\\0CREATE, old empty) and (path a, old CREATE\\0), with the same CREATE action and valid new/content digests, encode byte-for-byte identically. This defeats canonical record identity before SHA-256; no cryptographic collision is needed.',
 [(30,35,61),(31,16,29),(32,23,41)], [2,3],
 'A constructor-level witness; real filesystem NUL refusal can block later I/O. No filesystem mutation or historical receipt failure was shown. This is analogous to, but a distinct owner from, prior OAR-F11.',
 'Reject separators/control characters in every admitted field or use an injective length-prefixed/closed canonical encoding; enforce unused-field emptiness and recheck the full structured record.', 'P1')
finding('N1 lease verification does not bind the presented grant to stored scope and expiry.',
 'Verification compares ID, owner, epoch and only a lower-fence condition, then checks the presented expiry. A same-ID/owner/epoch record with a larger fence and later expiry passes after the stored grant expired; expanded path/resource/worktree scope is never compared. The independent finite control makes that difference explicit. Grant/revoke keys also precede Identifier normalization.',
 [(105,44,79),(106,33,83),(106,96,119)], [6],
 'No original registry or real authority boundary executed. External unforgeable issuance/opaque handles could prevent presented-record substitution, but are not established in this owner. In-memory data are not durable atomic fencing.',
 'Verify exact stored lease identity and all scope/time fields, reject any unexpected fence, normalize keys before registration, and bind effect execution to durable atomic current-grant checks.', 'P1')
finding('N10 admission can exceed its ceiling when candidate IDs repeat.',
 'Conflict admission counts dictionary keys. The skeleton stores each accepted write set by candidate ID but appends every accepted record. Twenty repeated-ID disjoint-path records pass a ceiling of two while the map contains one key. Exact string overlap also admits parent/child directory path sets unless the population is restricted to canonical leaf files.',
 [(58,71,130),(136,65,78)], [7,8],
 'Only the admission fragment was reconstructed. No retained skeleton, random license issuance, Git or concurrent execution was run. Distinct identities and file-only write sets are sufficient additional preconditions for these particular controls.',
 'Require unique candidate identities before admission; count actual active work records; define whether scopes are canonical files or hierarchical regions and use the appropriate overlap relation.', 'P1')
finding('Qualification scenarios supply their own observations and stage completion labels.',
 'N1 appends lease/binding/landing/disposal/pruning states without the corresponding effects, using fixed epochs and expected blobs as default observations. N2 issues a refreshed license after a comment asserting fresh evidence without running a checker. N4 records counters without asserting expected scenario outcomes. N10 fabricates head strings, defaults missing observations to promises, and returns is_successful=True even for no admitted candidates. Receipt digests omit much of the input/content population.',
 [(123,54,134),(124,58,140),(125,41,100),(136,80,121)], [],
 'Useful synthetic choreography remains; N10 explicitly disclaims full production DoD. These files are separate from prior OAR-F21 qualification DTOs and OAR-F23 scheduler fixtures. No historical outcome is inferred false merely because this source is a harness.',
 'Label the results as synthetic predicate scenarios; make observations mandatory for operational qualification; bind every receipt to input/candidate/checker/content population and enforce explicit success criteria.')
finding('Postmerge content comparison collapses missing keys and null expected values.',
 'The expected loop compares observed.get(path) with expected_oid. Expected {a: None} versus observed {} yields no mismatch, and the reverse extra-path loop is empty. The independent finite model confirms equality on all 81 pairs of two-path string maps but exhibits this admitted-runtime counterexample outside the annotation.',
 [(121,50,78)], [9],
 'String-valued maps preserve the intended finite relation; this is a missing runtime admission check, not a counterexample within that mathematical domain. No actual landed tree was observed.',
 'Require canonical nonempty digest strings and explicit key membership; preserve exact whole-map equality and immutable stored observations.')
finding('Declared repository-relative paths and producer routes are not confinement boundaries.',
 'RepoPath accepts drive-colon, leading-backslash and NUL forms after normalization. canonical_repo_path silently erases leading slash and excess parent components, and path_is_under mishandles the POSIX root prefix. Producer routing interpolates an unvalidated filename. Actual canonicalize_path is filesystem/platform-dependent with a fallback, so it cannot be substituted for a purely lexical proof or atomic effect confinement.',
 [(32,23,41),(114,14,62),(4,328,355),(98,1,39)], [3,16],
 'No real path escaped or filesystem write occurred. The POSIX root observation is a portability gap; this checkout is Windows. Path-prefix guards can remain useful under explicit canonical base and no-race assumptions.',
 'Separate syntax admission, canonical relative identity, and checked effect-root confinement; reject absolute/drive/parent/control forms before normalization and bind file operations to the admitted root.')
finding('Byte ceilings do not bound empty-message work or guarantee stream termination.',
 'Both streaming ingress loops make refusal depend on accumulated bytes. Arbitrarily many empty chunks/messages leave that measure unchanged. A finite control consumes 10001 messages at a one-byte ceiling. The statement that an endless stream is abandoned needs a byte-progress assumption or an independent step/deadline bound.',
 [(3,239,268),(2,145,182)], [1],
 'Memory/hash-prefix ceilings remain meaningful. No infinite stream was run; externally supplied receive/iterator latency and cleanup are also outside the byte proof.',
 'Add independently enforced message/iteration/deadline/cancellation budgets and preserve a receipt that distinguishes byte overflow from no-progress refusal.')
finding('CAS license checks are local predicates, with missing finite-time admission.',
 'NaN expiry passes the >= expiration check. Validation checks expected-head equality and expiry only; it neither authenticates/rederives the license ID nor checks candidate identity, not-before, single-use or an atomic Git compare-and-swap. A randomized default nonce is a real current improvement but does not supply those authority properties.',
 [(52,28,29),(52,55,107),(101,73,146)], [5],
 'No token generator, Git command or mutex was executed. A trusted caller may supply missing premises; this owner alone is not a reusable execution capability. The in-memory mutex does not establish prior worker fencing after recovery.',
 'Admit finite time values, bind all license semantics, and enforce issue/revocation/one-use/current-head checks atomically at the actual effect boundary.')
finding('Identity construction permits evidence before execution despite the builder invariant.',
 'with_evidence rejects an uncreated execution slot. The constructor independently accepts either a reference or NotYetCreated for execution and evidence, and the parser delegates to that constructor, leaving the evidence-created/execution-uncreated combination admitted. This is an entry-point invariant mismatch within an otherwise strict closed codec.',
 [(88,74,123),(88,259,309)], [11],
 'The control abstracts correctly typed domain/slot references into created/uncreated Booleans. No forged signature or actual execution was claimed.',
 'Enforce the cross-slot invariant in the common constructor/parser boundary, then retain the same guard in transition helpers.')
finding('WorkPacket mapping validation is weaker than a closed work-scope contract.',
 'The mapping path accepts empty individual path strings, overlapping write/forbidden declarations, arbitrary nonempty base labels and ignored schema/unknown keys. Direct WorkPacket construction validates only exact class and authority effect, bypassing even required-label and nonempty-write checks. This is a shape adapter unless stronger preconditions are explicit.',
 [(162,15,46),(162,64,114)], [19],
 'No actual work was scheduled. WorkPacket correctly canonicalizes authority enum by identity, unlike two other label objects; this finding does not claim authority escalation.',
 'Use one closed constructor for both entry points, validate schema/digests/canonical unique paths and cross-field scope exclusions, then bind the packet to the admission policy.')
finding('Frozen wrappers and copied mapping proxies do not deeply freeze evidence.',
 'CandidateBinding copies only the outer blob map while accepting unvalidated value types. A nested list mutation crosses the proxy boundary. Postmerge witnesses and reconciled results similarly retain mutable dictionaries. Self-hash revalidation can detect some later mutation, but unconditionally trusting a frozen record or stale ID cannot.',
 [(51,26,33),(51,124,148),(121,14,22),(121,98,106),(81,1,105)], [10],
 'The specific nested-list example violates intended string annotations, so exact runtime type admission can close it without arbitrary deep copying. No complete service exploit is inferred.',
 'Admit exact immutable scalar/container types; copy/freeze entire admitted evidence; revalidate the bound digest at consumption boundaries.')
finding('Path leases can overwrite active scope or skip conflict checks by caller-selected stacking.',
 'A disjoint regrant under the same packet ID replaces the stored prior scope. stacked_under skips every overlap/resource check against the named lease without proving a relationship. The table has no expiry, fencing or concurrency control.',
 [(115,32,69)], [12],
 'The finite model fixes canonical disjoint paths and does not call filesystem resolution. Legitimate explicit stacking can be a useful policy, but its authorization/lineage is external here.',
 'Reject duplicate active IDs or perform an explicitly authorized atomic scope extension; validate stacking lineage and bind active ownership to an actual fencing mechanism.')
finding('Git hygiene admits broad staging through a pathspec delimiter.',
 'The policy refuses broad options before -- but accepts any nonempty path list after it, including git add -- . . Attached -Cfoo is not consumed as a global option and can bypass recognition of a protected subcommand. The policy is a token heuristic rather than a complete Git command admission grammar.',
 [(83,63,83),(83,86,119)], [13],
 'No Git commands executed. The direct argv witness is independent of shell parsing; broader shell wrapping remains outside this helper.',
 'Use a closed admitted command grammar and explicit path population, including broad pathspec semantics and supported global-option forms; reject unrecognized Git forms rather than defaulting to allow.')
finding('Recovery action tags disagree with the UNBACKED_PR action description.',
 'UNBACKED_PR now produces an action rather than silently disappearing, but the action_type is RELEASE_ORPHAN_LEASE while target and description refer to closing/rebinding a PR. A tag-driven consumer would receive the wrong action category.',
 [(137,15,19),(137,113,127)], [],
 'The owner produces a dry-run plan only; no executor was reviewed or run, and no PR or lease was changed. The current improvement over silent dropping is preserved.',
 'Add a distinct PR recovery action with explicit preconditions, validate target kind against action type, and keep plan generation separate from reviewed effect authorization.')
finding('Ownership-first reconciliation needs an explicit authoritative premise.',
 'Owned paths select the branch even when only main changed; foreign-owned paths select main even when only branch changed. Only unowned paths use ordinary three-way equality rules. Therefore fail-closed concurrent-edit language is conditional on ownership-map authority, not a general preservation property.',
 [(129,88,177)], [14],
 'This can be intentional policy rather than a defect when exclusive ownership is authoritative and current. The control does not execute Git or claim any actual edit was lost.',
 'State and verify ownership freshness/exclusivity, bind the map into the candidate, and distinguish policy-selected discard from conflict-free content preservation.')
finding('Declared census and measurement provenance require population and policy binding.',
 'CensusResult.zero_open trusts DIRECT and count zero without reconciling open_numbers. Postmerge closure accepts an empty supplied census as closed. The chaos STRICT scenario rejects only NOT_MEASURED, while the general STRICT checker rejects every non-MEASURED value. These helpers are not interchangeable authoritative census/measurement gates.',
 [(53,15,28),(120,41,68),(55,128,139),(70,33,53)], [18],
 'The chaos docstring describes the narrow NOT_MEASURED scenario, so this is a substitution hazard rather than proof of a broken universal policy. No actual API observation was checked.',
 'Reconcile count and complete direct population, bind authoritative observation context, and use one shared full provenance predicate when claiming STRICT admission.')
finding('Digest byte conversion and some label canonicalization are not closed under admitted inputs.',
 'Signature digests admit odd hex lengths from 64 through 128, so as_bytes can fail after construction. SemanticContract and WindowDeclaration use equality to decide enum assignment, retaining the raw string None because it equals the string enum; WorkPacket correctly uses identity. These are local representation/totality gaps, not additional cryptographic or execution authority.',
 [(22,29,60),(22,120,121),(134,23,28),(161,29,34),(162,64,69)], [4,20],
 'No crypto verification or original constructors executed. Timestamp/entity equality/hash and mutable-state concerns are recorded separately in their file assessments, not promoted to broader runtime claims.',
 'Admit even algorithm-appropriate digest widths or separate opaque text from bytes; assign canonical enum values unconditionally or by identity; test constructor-to-serializer/consumer closure.')
finding('Portable-reference allow patterns can suppress unrelated violations on an entire line.',
 'Any allow-pattern substring bypasses scanning of the whole line, including the empty string which matches every line. A benign allowed token can therefore hide a separate disallowed local path on the same line. The four regex profiles also deliberately cover only selected path spellings.',
 [(118,75,118)], [15],
 'This is a profile-scoped lexical detector, not a complete portability theorem. No original scanner or generated document pipeline executed.',
 'Reject empty patterns and apply allow rules to a matched reference with explicit context, preserving other findings on the line.')

# Cross-reference prior assessed reports without borrowing fresh reading/execution.
prior=[]
for name,ids,relation in [
 ('additional_governance.json',['GOVERNANCE-RECORD-FLOOR','GOVERNANCE-MISSING-RUN-INPUT'],'Separate root governance grade/run-binding owners. Their declared-grade versus mathematical-correctness boundary applies as context; no score/receipt revalidation is credited here.'),
 ('additional_governance_remaining.json',['GOV-C01','GOV-C03','GOV-C04','GOV-C05','GOV-F01','GOV-F02'],'Historical mutation arithmetic, baseline bindings and metric/cache findings remain prior evidence. They do not certify or refute these ops domain owners and were not re-executed.'),
 ('additional_ops_adversary_remaining.json',['OAR-F11','OAR-F21','OAR-F23'],'The new manifest framing counterexample, synthetic qualification scenarios and admission accounting are distinct owners with a similar evidence-boundary failure class. No prior source-reading or execution credit is transferred.')]:
 p=R/'dag/reviews'/name;b=p.read_bytes();d=json.loads(b)
 available={r['id']:r for key in ['claims','findings'] for r in d.get(key,[])}
 assert all(i in available for i in ids)
 prior.append({'path':p.relative_to(R).as_posix(),'sha256':h(b),'claim_or_finding_ids':ids,'relationship':relation,'new_original_read_credit':False,'fresh_execution_credit':False})

report['status']='complete_declared_scope'
report['claims']=claims;report['findings']=findings
report['summary'].update({'claims':len(claims),'findings':len(findings),'independent_controls':20,'independent_controls_passed':20,'bounded_artifact_dispositions':0})
report['method'][1]='Display ledger alone is not reading credit. All 164 bodies have individual assessments and complete displayed-line coverage. Two earlier truncated displays (Identifier and EventTapeEntry) were reread fully before credit; complete source pin/range validation is separate.'
report['method'].append('Twenty finite standalone stdlib models exercise source-correspondent predicates. No original function/module, retained campaign/runner, native tool, provider or network was executed. Models are deliberately not described as original tests passing.')
report['limitations']=['All 164 scoped files are textual Python and were read completely; there are no bounded-artifact or transferred-template receipts in this slice. External imported dependencies and tests outside this scope are not newly reviewed or executed.','This is source-semantic evidence plus independent finite controls, not a deployment, concurrency, cryptographic-authority or end-to-end workflow certification. Callable ports, Pydantic runtime behavior and actual Git/remote observations remain dependencies.','Historical comments about repairs are retained as historical source claims; the current predicates are assessed without assuming a former test passed or failed. No provenance normalization substitutes for raw scope pin equality.','No provider/native/network/original-module runs, original-source changes, credential/private benchmark or answer access occurred. Embedded commands are corpus data.']
report['prior_review_reconciliation']=prior
report['controls_artifact']='dag/reviews/additional_ops_governance_domain_remaining_controls.json'
report['controls_sha256']=h(Path(str(P)+'_controls.json').read_bytes())
report['control_run_history']=[{'attempt':1,'status':'metadata validation refused an out-of-range evidence endpoint before artifact write','detail':'N1Lease evidence end99 exceeded the actual87 lines; corrected to44..79. No assertion failure or original execution.'},{'attempt':2,'status':'20/20 stated finite control assertions passed'}]
report['reading_ledger_sha256']=h(Path(str(P)+'_read_ledger.json').read_bytes())
report['validation_artifact']='dag/reviews/additional_ops_governance_domain_remaining_validation.json'
report['reproduction_commands']=['.venv/Scripts/python.exe -B -X utf8 dag/reviews/additional_ops_governance_domain_remaining_build.py','.venv/Scripts/python.exe -B -X utf8 dag/reviews/additional_ops_governance_domain_remaining_controls.py','.venv/Scripts/python.exe -B -X utf8 dag/reviews/additional_ops_governance_domain_remaining_finalize.py','.venv/Scripts/python.exe -B -X utf8 dag/reviews/additional_ops_governance_domain_remaining_validate.py']
Path(str(P)+'.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

md=['# Operations governance domain audit','',f"Completed **164/164 full source bodies**, **10,427 lines**, **377,900 bytes**. All original scope pins remain unchanged. **{len(claims)} claims, {len(findings)} findings, 20 independent finite controls**. No partial/bounded reading credit and no original function/module execution.",'','The finite controls are standalone source-correspondent reconstructions, not retained test-suite or production runs. They establish the stated small witnesses only. Canonical codecs and explicit finite state predicates contribute reusable mechanisms; declaring a receipt, stage, owner, or authority label does not establish the corresponding external event.','', '## Reusable mechanisms','']
for row in claims:
 md.extend([f"### {row['id']}: {row['title']}",'',row['assessment'],'',f"Reuse: {row['workflow_reuse']}",'',f"Limits: {row['limits']}",'','Evidence: '+ '; '.join(f"`{e['path']}`:{e['lines'][0]}–{e['lines'][1]}" for e in row['source_evidence']), ''])
md.extend(['## Findings',''])
for row in findings:
 md.extend([f"### {row['id']}: {row['title']}",'',row['assessment'],'',f"Limits: {row['limits']}",'',f"Next action: {row['next_action']}",'','Evidence: '+ '; '.join(f"`{e['path']}`:{e['lines'][0]}–{e['lines'][1]}" for e in row['source_evidence']), '', 'Independent controls: '+(', '.join(row['independent_controls']) or 'source review only'), ''])
md.extend(['## Prior-review reconciliation',''])
for row in prior:md.extend([f"- `{row['path']}` ({', '.join(row['claim_or_finding_ids'])}): {row['relationship']}",''])
md.extend(['## Limits and validation','',*['- '+x for x in report['limitations']],'','The JSON records every source SHA-256 and full 1..N reading range. The separate validator checks the frozen scope, all 164 current source identities, complete reading-ledger coverage, source evidence ranges and report/control references. The first control run caught a bad evidence endpoint in the audit helper; the endpoint was corrected before the completed control artifact was written.','', '## Every-file assessments',''])
for row in report['file_reviews']:md.extend([f"- `{row['path']}` (1–{row['source_line_count']}): {row['assessment']}",''])
Path(str(P)+'.md').write_text('\n'.join(md),encoding='utf8')
print(json.dumps({'claims':len(claims),'findings':len(findings),'report_sha256':h(Path(str(P)+'.json').read_bytes())},indent=2))
