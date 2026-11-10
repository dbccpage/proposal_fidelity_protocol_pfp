"""Synthesize completed body notes and independently scoped controls; never mutate sources."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_ops_adversary_remaining'
inv=json.loads(Path(str(P)+'_inventory.json').read_text());rows=inv['files']
report=json.loads(Path(str(P)+'.json').read_text());controls=json.loads(Path(str(P)+'_controls.json').read_text())
assert len(report['file_reviews'])==307 and report['summary']['pending']==0
def ev(i,lo,hi):
 r=rows[i];assert 1<=lo<=hi<=r['lines'];return {'path':r['path'],'sha256':r['sha256'],'lines':[lo,hi]}
F=[];C=[]
def finding(title,detail,refs,next_action,control_ids=(),limits='',priority='P2'):
 F.append({'id':f'OAR-F{len(F)+1:02d}','title':title,'assessment':detail,'priority':priority,
           'source_evidence':[ev(*r) for r in refs],'independent_controls':list(control_ids),
           'limits':limits or 'Source/body review; no end-to-end native or provider execution.',
           'next_action':next_action})
def claim(title,detail,refs,limits):
 C.append({'id':f'OAR-C{len(C)+1:02d}','title':title,'assessment':detail,
           'source_evidence':[ev(*r) for r in refs],'limits':limits})

claim('Current teamwork is a bounded task-preserving state machine with distinct acceptance and learning stages.',
 'v3/v4 require a governed roster and source-bound original checker, replay actual PFP bytes, charge failed evaluations, preserve additive continuation history and reserve storage/learning/final readback. Semantic learning review can retain findings even after original-task acceptance. This is reusable orchestration, not 22 independent experts or a mathematical correctness theorem.',
 [(301,919,960),(301,2112,2185),(301,2324,2347),(301,3716,3754),(301,3804,3831),(302,63,129)],
 'Host observations remain editable reports; semantic adequacy and true independence of the operator-selected checker require separate admission. No workflow was run here.')
claim('Checked clarification and DDC reuse retain explicit NOT_SOLVED/fresh-check boundaries.',
 'Clarification checks exact candidate, objective, premises, output streams and source/checker binding, retaining unresolved advisory findings. Checked DDC reuse is a narrow registered transformation with source/target checks and exact procedure custody. Merely echoing a consumed digest proves a protocol match, not source comprehension.',
 [(301,1768,1943),(266,1,100),(266,350,481),(287,130,310),(302,297,347),(302,484,529)],
 'No task seed, private benchmark, retained DDC program or native checker was opened/executed. This establishes source contracts, not a solved external task.')
claim('The strongest custody owners preserve ambiguity rather than retrying unknown external work.',
 'ProviderCompletion durably marks Dispatched before transport and holds unknown liability; RecordingSeatPort requires a STARTED journal before invoking its inner seat; recovery emits CRASHED_UNKNOWN instead of automatically retrying. Main intelligence archive operations use prepared/terminal journals and byte seals. These are useful mechanisms with cooperative-writer and host assumptions.',
 [(289,63,132),(298,100,147),(263,1,111),(271,1,130),(271,225,370)],
 'Not every legacy path uses these owners; OAR-F06/F12/F14/F20 identify weaker alternatives. Native transaction guarantees and actual provider billing were not reproduced.')
claim('Native diagnostic references are re-read/replayed by the concrete host; their DTO summaries are not sufficient by themselves.',
 'The native gate DTO permits declared reference summaries, but the concrete teamwork host dereferences full receipts and performs replay before consumption. Typed operad application refuses Unadmitted state before effects. The current immune adapter has explicit missing/empty/invalid-spec guards stronger than its historical captured owner.',
 [(32,560,710),(181,2070,2175),(190,190,326),(105,300,485)],
 'Source-level positive controls do not certify the native binary, signature trust roots or detector completeness. Do not promote the DTO weakness into an end-to-end bypass; cache weakness OAR-F15 is separate.')
claim('Graph repair can support finite catalog optimality, while the yardstick supplies descriptive finite statistics.',
 'Graph controller rechecks candidate byte/checker identity and chooses the cheapest valid measured candidate; minimum claims require complete declared-catalog coverage. Wilson intervals and exact McNemar tails passed 102 small arithmetic cases (66 and36), and Pareto summaries use supplied success/cost/time coordinates.',
 [(296,1,150),(296,200,360),(306,230,343)],
 'No universal repair search, test independence, causal model comparison or model-performance reproduction. Incomplete/external candidates require explicit permission and population interpretation; yardstick admission gaps remain.')
claim('Dissent records and several fixture routes keep valuable explicit nonclaims.',
 'Finding dispositions retain exact original objection text and repair attempts with resolution_verified false. Scene valuation without a declared complex records NOT_MEASURED. Governing-council fixtures preserve supplied-context/script provenance; specialist service dispatch is fixture-only. These boundaries should survive consolidation.',
 [(303,10,52),(297,254,266),(268,190,320),(264,1606,1648)],
 'A bounded/HOLD outcome does not make synthetic operational claims accurate. OAR-F04 covers specialist narratives and their invented measurements separately.')

finding('Closed dependency residuals are mislabeled as exact coboundaries.',
 'The fallback computes only ||r||1 and ||d1r||1; _build_report maps ClosedResidual to COBOUNDARY_EXACT without solving d0x=r. For directed acyclic edges A->B,B->C,A->C with residual3 each, d1 is empty and Gamma2=0, but edge equations imply6=3. report.is_exact remains false, so this is a false diagnostic label rather than proven terminal admission.',
 [(224,28,56),(224,81,107),(224,173,209)],'Retain closed/exact distinction; solve the finite image-membership problem with a witness or use CLOSED_NOT_PROVEN_EXACT.',('OAC01',))
finding('Density validation admits non-positive matrices and can report negative entropy.',
 'DensityMatrixCandidate.validate only Hermitianizes and normalizes trace; zero trace becomes a different maximally mixed matrix. diag(2,-1) survives with purity5 and entropy-2 bits because negative eigenvalues are ignored. Config is unused; constructors permit negative mixture weights and return aliased arrays.',
 [(242,20,100),(242,103,121)],'Admit square finite Hermitian PSD trace-one states explicitly; distinguish projection/repair from validation and bind numerical tolerance.',('OAC02',),'Independent exact diagonal control; NumPy/native density implementation was not executed. No physical/quantum efficacy claim is supported.')
finding('Licensing proposal does not enforce its stated exact-zero target conditions.',
 'propose_token rejects phi1 only when greater than0; negative and NaN values pass with a declared exact witness. It ignores target gamma2/ret/claim, target exact-rational flag and target authority. The witness sort and optional SHA are checked, but this is a proposal token with AuthorityEffect None, not external admission.',
 [(71,24,61),(71,125,175)],'Use admitted finite exact values and the full intended target predicate before proposing; preserve the external authority ceiling.',('OAC03',))
finding('Specialist dramas retain operational success claims generated from constants.',
 'Product management preloads completed tickets/points/risk and CI-success cues. Thanatos preloads four PASS security findings, dispatched child swarms and traces-zeroed, then writes containment INTACT. No matching scans, tests, skill dispatch or deletion occur. Software-dev more honestly records skills_executed empty, yet renders structural verification and asserts exact-rational valuation from floats. Service restricts these routes to fixtures and outcomes mostly HOLD/no authority; those limits do not authenticate the printed operations.',
 [(286,210,270),(305,198,280),(305,367,455),(300,262,300),(300,514,569),(300,715,731),(264,1606,1648)],
 'Retain as explicit scripted demonstrations, label each fabricated metric/operation as fixture data, and route real task claims through actual host/checker receipts.',limits='No specialist bout or native persistence executed. No claim that the fixture service itself authorizes deployment.')
finding('Provider schema projection changes literal answer values, not only unsupported schema keywords.',
 'Recursive key stripping traverses const/enum object data. const {minimum:5,normal:7} becomes {normal:7}; enum [{pattern:"a"}] becomes [{}]. Local full-schema validation remains stronger, so the defect can force avoidable rejection or alter the provider-facing requested language rather than silently weaken final acceptance.',
 [(142,24,56)],'Traverse only schema-bearing positions and preserve instance data under const/enum; test language preservation.',('OAC09',))
finding('Research model dispatch lacks a durable in-flight transition before external send.',
 'ResearcherSwarm.dispatch reserves and permits PENDING, then sends; settlement/reconciliation happens afterward. A crash during send retains a PENDING reservation that the same method permits again. ProviderCompletion provides the contrasting Dispatched write-ahead. Dispatcher-level deduplication or stronger native reserve semantics are not established by this use-case body.',
 [(295,178,239),(289,76,90)],'Durably transition/claim dispatch before send and treat ambiguous outcomes as non-retryable until reconciliation.',('OAC13',),'AST ordering and synthetic crash model only; no provider sent, no native state transition executed.',priority='P1')
finding('Parallel blind cohort dispatch can execute and then discard observations outside the retained schedule or allowance.',
 '_collect_blind_actions gathers a contiguous blind block before results; _run_cohort submits every callback. Merge observes only the subsequently pending roles and breaks/skips when quorum, cap or other transition advances, leaving already executed replies outside run custody. The helper omits drive_teamwork executor/version gate, and future exceptions propagate before merge. Its dictionary reference helper is sequential and shallow-copies nested state, allowing callback mutation to leak between reviewers.',
 [(301,4082,4134),(301,4137,4172),(301,4217,4293)],'Admit bounded cohort dispatch up front, record every attempt/result even when not semantically consumed, enforce executor/version guards, and isolate immutable pre-cohort input.',('OAC08','OAC17'),'No executor was called. This is source control-flow analysis and finite models, not evidence of historical duplicate paid calls.',priority='P1')
finding('Run-bundle integrity verification authenticates configuration only.',
 'pack/verify_run_bundle uses a digest of preset, prompt-family versions and checker IDs. Changing objective, run_id, panel coverage or turns does not alter that digest. replay additionally validates supplied action/PFP observations, but accepts an empty or truncated valid prefix without requiring completion; this cannot establish custody of the advertised full run.',
 [(306,404,419),(301,4305,4362)],'Name the existing hash configuration_digest; separately commit the complete run body and require declared terminal/prefix status during replay.',('OAC07',))
finding('Failure-reproduction metrics can credit unrelated defects or carry claims across candidate revisions.',
 'A failed host check with no textual findings credits every queued claim; substring overlap credits overflow against "no overflow was observed". Unmatched claims become false alarms without independent refutation. candidate_reviewer_claims accumulates across build/repair because _v3_produced does not clear it, so later candidate checks can credit old claims. Panel coverage further takes maxima of two different counters.',
 [(301,1030,1085),(301,2295,2308),(301,2361,2449),(301,2452,2465)],'Keep reported/unreproduced/refuted distinct; bind each claim to candidate digest and claim-specific replay, and reset/version queues on candidate changes.',('OAC06',),'The separate finding_dispositions view correctly avoids verified-resolution claims. No measured failure-rate conclusion is drawn.')
finding('Yardstick input admission and promotion labels exceed the statistical evidence.',
 'Trial.from_dict converts nonempty "false" to True and admits negative cost/time/token fields. L3 promotion compares two caller yields without sample/custody/checker evidence; infinity promotes ADMITTED_OPERAND. Thompson uses max(1,count), not prior+count; resets its RNG each call, treats zero cost as1 and negative cost as1e-6. These are declared heuristic policies, not established Bayesian learning or admission.',
 [(306,75,96),(306,422,456),(306,477,544)],'Use strict finite typed observations; define posterior/prior and pairing policy, bind trial/checker evidence, and keep threshold output proposed until independent admission.',('OAC10','OAC12'),'Wilson/McNemar arithmetic itself passed OAC11; no actual retained trials were analyzed here.')
finding('Legacy directory custody hash has ambiguous path/content framing before mirror deletion.',
 '_dir_tree_sha256 concatenates each relative filename and raw contents without lengths or separators. A one-file tree a:"bc" and ab:"c" encode identical bytes. The same digest guards shutil.rmtree of a mirror, so hash equality need not imply equal path-to-byte populations. This is an encoding collision, not a SHA-256 collision.',
 [(272,44,50),(272,360,385)],'Use an unambiguous length-delimited or canonical manifest of path,size,content hash and compare complete populations before any retirement.',('OAC05',),'No files were created/deleted for this control.',priority='P1')
finding('Legacy harvest and lifecycle declarations are weaker than the main archive journal.',
 'Harvest can archive/move snapshots despite unreadable extraction and omits the main path-confinement/pre-post-hash/transaction journal. Corrupt secondary corpus manifests are swallowed as empty before replacement. Lifecycle request hardcodes producer_lease_active false and treats absent parser gaps as complete extraction, with empty evidence_refs for findings. In contrast, main archive operations perform journal/seal checks.',
 [(276,135,165),(276,195,285),(277,135,165),(277,315,351),(271,225,370)],'Consolidate on the reviewed main archive path; make unreadable content and unresolved producer lease explicit blockers and preserve corrupt manifests.',limits='No archive/lifecycle method executed. Parsing completeness is not semantic completeness; no historical source loss is inferred from current code alone.')
finding('Legacy paper miners can turn empty, unreadable or contradictory reports into PASS.',
 'Markdown status searches PASSED/CLEARED before BLOCKED/NOT READY and disregards chronology/negation. OMC/fallback paths can retain empty or failed parse inputs then return PASS from lack of recorded failures; OMC DTO defaults science/code checks to passing unless supplied. Some PASS declarations become THEOREMS_VERIFIED without proof replay. Newer extraction has explicit gap handling, so these older owners must not be treated as equivalent.',
 [(279,183,205),(279,480,581),(279,685,787),(20,1,95),(275,190,305)],'Require known schema, explicit observed checks and readable complete population; preserve UNKNOWN/UNREADABLE and use typed status precedence.',('OAC14',),'No source paper or retained miner executed; mathematical validity is not inferred from either PASS or parser failure.')
finding('Research event mirror checks length but not the retained prefix bytes.',
 '_mirror_events counts newlines then appends events after that count. Equal-count edited lines survive without comparison to checkpoint events; a longer mirror is refused but same-length corruption is not. Checkpoint/native event verification is a separate boundary and may still detect its own mutations.',
 [(170,128,160)],'Compare the complete canonical existing prefix and sequence before appending, or derive a sealed immutable mirror from the checkpoint.',('OAC15',))
finding('Native binary digest cache can return stale hashes after metadata-preserving mutation.',
 'The cache key is absolute path, mtime_ns and size. Different same-length bytes with preserved mtime receive the old SHA; _host uses that result in its native binary binding. This is narrower than arbitrary path replacement and does not prove a historical untrusted binary was executed.',
 [(181,89,96),(181,337,360)],'Hash actual admitted bytes at the invocation boundary or bind an immutable opened file/content-addressed binary; do not use mutable filesystem metadata as integrity identity.',('OAC16',),priority='P1')
finding('Topology serialization and the default profile constructor disagree with their own contracts.',
 'SeatRequirement.from_dict calls exact_object with unsupported allow_missing, raising TypeError before reconstruction. Optional tuple defaults subsequently conflict with list-only wire decoding. The profile scene list places adversary-gate last while SceneGraph requires lexicographically sorted IDs, so the default constructor fails admission.',
 [(246,75,108),(219,19,29),(200,171,232),(246,300,329)],'Repair codecs against round-trip laws and canonicalize profile scene order before construction; retain malformed-wire negative checks.',('OAC04',))
finding('Several adapters compute the ops directory as the repository root.',
 'parents[2] from ops/adversary/infrastructure resolves to ops, yet operad binding and prompt geometry append repository-root pfp/engine paths. Similar literal ownership assumptions affect pilot continuation and skill resolution. This prevents the intended current owners from being located in this checkout; it is not evidence that those owners are absent from the repository.',
 [(125,25,41),(125,78,98),(134,106,128),(129,1,48),(164,1,35)],'Inject/resolve the actual repository root once and test known current owner paths with read-only existence checks.',limits='Path arithmetic inspected without invoking native binaries or reading any credentials.')
finding('Diff/oracle execution can check transformed bytes while labeling the original candidate hash.',
 'The adapter hashes raw candidate bytes, decodes with replacement and writes text to the temporary source path; invalid UTF-8 and platform newline conversion can change executed bytes. The critique service also hashes UTF-8 diff text then writes it using platform text translation. The original test/base code is intentionally supplied to the proposer, so this is a public repair exercise, not a sealed independent benchmark.',
 [(98,100,240),(282,285,350)],'Use lossless strict decoding or execute exact written bytes and bind their raw hashes; preserve original and executed encodings separately.',limits='No subprocess/tests executed. Production checker source adequacy and OS sandboxing were not reproduced.')
finding('Multi-round critique trusts returned oracle verdict without rechecking candidate identity.',
 'After check_candidate, the service branches on verdict and persists returned receipt, but does not compare its candidate ID/bytes/hash to the current candidate. A stale or misbound injected checker result can therefore be recorded as accepted here. The concrete checker may bind these correctly; this is a missing use-case boundary check, not a demonstrated production native bypass. Caller extra context can also override prepared test/base/workspace keys.',
 [(282,176,200),(282,327,410)],'Check exact candidate/task/checker identity and receipt digest before consuming verdict; reserve invariant context keys.',limits='Static injected-port contract finding; no oracle or retained repair loop executed.')
finding('Default append-only DDC sink does not restore existing head or commit memory after disk success.',
 'Constructor resets sequence0/headNone even for an existing output file. record_step mutates lists/head/sequence before a fallible append; failure returns Err after in-memory advancement. Reopening can append a second genesis and failed writes can leave memory/disk divergent. The stronger genealogy store separately rereads and validates its chain; its guarantees cannot be transferred to this sink.',
 [(248,154,170),(248,182,255),(250,310,430)],'Recover/validate existing chain before append and publish state only after durable write, under a single explicit writer/lock contract.')
finding('Qualification receipts encode asserted independence and leave cross-subject bindings to callers.',
 'N1/N2/N4 receipt admission checks booleans, worker counts and evidence shapes rather than replaying independent probes. The ladder combines passing receipts without one common subject/snapshot/patch identity. Selection checks epoch ID and hard-gate sets but can miss weights/probes or duplicate gate IDs; the orchestration owner has stronger full bindings. These interfaces are useful DTOs, not sufficient qualification certificates.',
 [(197,100,162),(197,235,250),(197,290,341),(199,293,350),(209,80,210)],'Bind every receipt to exact candidate/epoch/probes/patch and use concrete independent checker evidence before qualification.',limits='No qualification or host run; stronger orchestration checks preserved rather than generalized away.')
finding('Mutable antibody/catalog state has path and stale-admission hazards.',
 'Legacy catalog/pharmacy helpers form paths from unvalidated antibody identifiers. Default antibody cache is loaded once and can miss external revocation; recording candidates can overwrite existing status. Cemetery candidate publication uses read-modify-write so atomic replace alone does not prevent overwriting a concurrent admission. Newer typed admission paths remain stronger and must not be conflated.',
 [(233,45,115),(251,1,26),(248,610,705),(265,280,425)],'Constrain IDs/paths and use versioned transactional state with revocation-aware readback; separate candidate creation from activation.')
finding('Scheduler completion and swarm echo helpers do not measure actual task progress.',
 'finish_bout derives statuses/routes from supplied completion rather than task evidence and emits changed_state1 for synthetic traversal. run_swarm helpers include a synchronous echo implementation with an infinite_timeout label whose timeout is unused. These can demonstrate choreography, but are not bounded worker execution or measured workflow success.',
 [(214,210,270),(216,1,51),(123,240,353)],'Label fixture-only scheduling and require observed per-step outputs/cost/termination evidence for real progress claims.')
finding('Request value-object equality and hashing use incompatible representations.',
 'carrier_context equality uses ordinary dict equality, where {x:1} equals {x:True}; hash converts values to strings, which differ. Nested mutable dicts also undermine stable hashes of frozen dataclasses. Equal values can have unequal hashes and later mutate under the same object identity.',
 [(30,112,124),(30,292,336)],'Choose immutable canonical typed context or make the value object unhashable; define exact equality over the same representation used for hashing.',('OAC18',))
finding('Research HTTP identity and output path fields are caller claims, not authentication or confinement.',
 'The HTTP facade accepts operator identity in requests and constructs storage/export paths from caller fields without a demonstrated authentication/confinement boundary in this owner. Native state policy checks cannot establish who supplied those fields. Treat the facade as a trusted local tool unless an outer authenticated service explicitly binds them.',
 [(88,338,450),(88,491,514),(88,971,992)],'Document trusted-local scope or add explicit authenticated identity and root-confined output paths before exposing the facade.',limits='No HTTP server/request executed; no claim of a currently internet-exposed endpoint.')
finding('The cochain CLI reads a different argument attribute from the one its parser defines.',
 'The run path accesses parsed.core while the parser defines --omega without a matching core destination. AttributeError is not caught by the surrounding ValueError handler, so the intended finite carrier path fails before evaluation.',
 [(83,429,438),(83,910,932)],'Use the declared argument destination and add a small parser-to-handler offline control.',limits='Source inspection only; CLI was not invoked because its composition can load native/provider owners.')

prior=[]
for name,ids,assessment in [
 ('systems_audit',['SYS-PCIV-003','SYS-EIS-005','SYS-EIS-006'],'Exact chain-condition checks and explicit detector/trust limitations remain distinct from the new AST-label and density counterexamples.'),
 ('additional_eis_pciv_remaining',['EPC01','EPR10'],'Reuses the established candidate/replay/activation distinctions; no EIS/PCIV tests or efficacy results are re-credited.'),
 ('additional_operad_receipts_remaining',['ORR-F03','ORR-F04','ORR-F05','ORR-F12'],'Historical empty-spec/native/pharmacy defects stay historical. Current105 is stronger; no unverified old archive or custody transform inferred.'),
 ('additional_workflow_library_remaining',['WLR-C01','WLR-F01','WLR-F02','WLR-F03'],'Task-preservation, answer leakage and budget mechanisms are contextual cross-references, not reproduced here or generalized to every Adversary adapter.'),
 ('additional_wiki_workflow_dag',['WIKI-WFD-F09','WIKI-WFD-F10'],'A design prerequisite graph does not establish executable composition or detector qualification. This source audit supplies concrete owner-level limits.'),
 ('additional_pfp_application_remaining',['PFPAPPREM-C011','PFPAPPREM-F007'],'Unsigned reports and custody timing have previously documented boundaries; this slice adds distinct Adversary owners.')]:
 q=R/'dag/reviews'/f'{name}.json'
 if q.exists():prior.append({'path':q.relative_to(R).as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'claim_or_finding_ids':ids,'assessment':assessment,'reading_credit':'targeted prior report context only; no new source or test credit'})

report.update(status='complete',claims=C,findings=F,prior_review_reconciliation=prior,
 independent_control_artifact={'path':str(P.relative_to(R))+'_controls.json','sha256':hashlib.sha256(Path(str(P)+'_controls.json').read_bytes()).hexdigest(),'summary':controls['summary']},
 reading_method='Every scoped text body displayed and semantically assessed. Truncated displays were re-read; ledger is display evidence only, paired with explicit per-file assessments. No equality-transfer or generated-template substitution was needed.',
 artifact_accounting={'python_full_bodies':304,'yaml_full_bodies':2,'json_full_bodies':1,'partial':0,'bounded_only':0,'binary_or_large_generated_data':0,'historical_json_note':'rust_budget.contract.score.json is a full-body historical grade declaration, not fresh test execution.'},
 execution_status={'fresh_controls':19,'fresh_retained_tests':0,'retained_or_native_runners_executed':0,'provider_calls':0,'paid_calls':0},
 limits=['All307 original source bytes remain unchanged. No production repairs, deletions, credential/private benchmark reads or shared coverage/DAG edits.',
 'Full reading is not proof of all behavior. Current source, source-only finite controls, declared historical grades and prior evidence remain distinct.',
 'External/native/checker/provider dependencies were not exhaustively re-reviewed or executed. Unauthenticated host reports require an explicit trust boundary.',
 'No mathematical task answer or hidden benchmark was read, solved, used as a fixture, or supplied as workflow input.',
 'Selected actionable findings are synthesized here; additional local implementation caveats remain in each file assessment and the preserved notes ledger.'])
report.pop('candidate_findings',None)
report['summary'].update(bytes=sum(r['bytes'] for r in rows),text_lines=sum(r['lines'] for r in rows),claims=len(C),findings=len(F),fresh_controls=19)
for r in report['file_reviews']:
 r['actual_execution_status']='body reviewed; no retained runner executed'
 r['source_evidence']=[{'path':r['path'],'sha256':r['sha256'],'lines':[1,r['source_line_count']]}]
Path(str(P)+'.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
md=['# Ops/adversary remaining source audit','',
 'Complete: **307/307 full bodies, 77,917 lines, 3,278,208 bytes; 0 partial, 0 bounded-only, 0 pending.** All frozen pins verified. This slice contains304 Python files,2 YAML files and1 historical JSON score declaration.',
 '',f'**{len(C)} scoped claims, {len(F)} findings,19 confined source-only controls.** No retained runners, native programs, provider calls, broad tests or private benchmark contents were used. Per-file assessment/hash/range receipts are in the companion JSON. Original sources remain unchanged.',
 '', 'The strongest reusable mechanisms are exact task/checker bindings, replayed PFP proposal custody, bounded repair/evaluation accounting, explicit unknown-outcome recovery, sealed main archive transactions, strict clarification as NOT_SOLVED and source-bound finite DDC reuse. Persona scripts, string-matching scores and proposed control graphs add no independent mathematical verifier.',
 '', '## Scoped claims','']
def md_ev(items):return '; '.join(f"`{e['path']}:{e['lines'][0]}-{e['lines'][1]}` (SHA `{e['sha256'][:16]}…`)" for e in items)
for c in C:md += [f"### {c['id']} — {c['title']}",'',c['assessment'],'',c['limits'],'',md_ev(c['source_evidence']),'']
md+=['## Findings','']
for f in F:
 md += [f"### {f['id']} [{f['priority']}] — {f['title']}",'',f['assessment'],'',f['limits'],'',f"Next: {f['next_action']}",'',md_ev(f['source_evidence'])+(' Controls: '+', '.join(f['independent_controls']) if f['independent_controls'] else ''),'']
md += ['## Independent checks and evidence limits','',
 'The19 checks distinguish extracted pure predicates from independent mathematical/control-flow countermodels. All304 Python files also parse through AST without imports. Statistical controls cover66 Wilson cases and36 exact McNemar tails; this tests arithmetic, not trials or scientific efficacy. There were no retained test-suite executions.',
 '', 'Current immune guards and concrete native-reference replay are stronger than some historical snapshots or summary DTOs. No historical archive reconstruction was assumed. Host authenticity, semantic checker adequacy, real external billing, OS isolation and native kernel correctness remain outside this fresh execution scope.',
 '', '## Prior evidence reconciliation','']
for p in prior:md += [f"- `{p['path']}` ({', '.join(p['claim_or_finding_ids'])}): {p['assessment']}",'']
md += ['## Per-file accounting','',
 'The JSON file_reviews array contains every frozen path exactly once, its full raw SHA-256, line count, complete reviewed range and substantive owner-specific assessment. The preserved notes retain lower-priority details without promoting every candidate observation to a finding. The reading ledger records displays, not automatic reading credit. Scope and originals are validated again by the separate validation helper.','']
Path(str(P)+'.md').write_text('\n'.join(md),encoding='utf8')
print(report['summary'])
