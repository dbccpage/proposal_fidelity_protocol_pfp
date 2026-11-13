"""Synthesize the completed source ledger; audit outputs only."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_rust_adversary_remaining'
def h(b):return hashlib.sha256(b).hexdigest()
def load(s):return json.loads(Path(str(P)+s).read_bytes())
scope=load('_scope.json');S=scope['files'];out=load('_checkpoint099.json.snapshot')
assert out['summary']['full_source_reads']==99 and out['summary']['pending']==0
def ev(i,a,z):
 r=S[i];b=(R/r['path']).read_bytes();assert h(b)==r['sha256'];assert 1<=a<=z<=len(b.decode('utf8').splitlines())
 return {'path':r['path'],'sha256':r['sha256'],'lines':[a,z]}
claims=[];findings=[]
def claim(title,text,evidence,limits,reuse,tests=()):
 claims.append({'id':f'RAD-C{len(claims)+1:02d}','title':title,'assessment':text,'source_evidence':[ev(*e) for e in evidence],'evidence_kind':'full source-semantic reading plus explicitly named independent finite controls; no original execution','independent_controls':list(tests),'limits':limits,'workflow_reuse':reuse})
def finding(title,text,evidence,limits,action,tests=(),priority='P2'):
 findings.append({'id':f'RAD-F{len(findings)+1:02d}','title':title,'assessment':text,'priority':priority,'source_evidence':[ev(*e) for e in evidence],'independent_controls':list(tests),'limits':limits,'next_action':action})

claim('Exact finite predicates are real mechanisms, conditional on admitted encodings.',
 'Primary gates check declared rational matrix dimensions and d1*d0=0, L1 primal/dual feasibility and equality, and lexicographic tie witnesses. Valuation receipts recompute bounded integer weighted residual totals and disposition. run_swarm additionally binds candidate, epoch, ordered probes and weights, and binds the packet epoch at entry. This runtime closes the standalone zero-weight/epoch mismatch concern.',
 [(40,365,435),(40,593,727),(82,1,152),(94,61,90),(94,415,430)],
 'No native predicate, LP solver, tie verifier or task checker ran. Supplied matrices must still represent the intended carrier/task; a supplied independently_recomputed boolean is not an independent run.',
 'Reuse frozen task encoding plus independently recomputed finite residual/certificate checks and explicit candidate/epoch binding. Preserve the distinction between verifying a finite certificate and establishing the encoding.',('RA-T08','RA-T09'))
claim('The active PFP gateway contains substantive reservation and recovery checks.',
 'PfpSeatGateway reserves the full configured output allowance before send, records reservation and settlement delta, validates matching settlement terms, and blocks later sends on unresolved outcomes. It checks nonnegative receipt costs/usage and binds replay provider bytes. These mechanisms are stronger than the separate legacy gateway and than treating an idempotency-key string alone as exactly-once dispatch.',
 [(39,54,200),(39,227,355),(39,357,404),(39,449,600)],
 'Source reasoning only. Ledger append is not a demonstrated multiprocess atomic reservation transaction; estimates need a valid upper-bound policy, and actual overruns may already have occurred before refusal. No provider/ledger run.',
 'Use the active reserved/unknown/settled state machine for bounded paid experiments, with one dispatcher or an independently enforced atomic lease and reconciliation policy.')
claim('Canonical records and exact prefix comparison provide useful local custody.',
 'The stage codec closes record fields, normalizes semantic Unicode identity, validates selected bounds and binds record digests. complete_bout compares the entire retained DDC prefix before slicing appended steps. This is stronger than an equal-line-count mirror check.',
 [(77,1,256),(13,114,159),(92,1,324)],
 'NFC identity is a declared semantic quotient, not raw-byte identity. Receipt replay uses the same scheduler and supplied results; consistent replay does not prove model calls or truthful task outcomes. External strict-JSON/JCS dependencies were not newly fully read.',
 'Retain exact candidate/request/output hashes and prefix equality as custody stages, while reporting checker truth and transport evidence separately.',('RA-T14',))
claim('The deterministic scheduler supplies finite choreography under explicit premises.',
 'N=1 composition checks definition/profile/graph/catalog bindings, required operations and declared independent-seat agent disjointness. Unit-cost steps, maximum total steps, dry rounds and visit limits provide bounded choreography for validated inputs. Topology validation closes identifiers and endpoints.',
 [(95,14,161),(95,177,211),(95,246,364),(97,151,267)],
 'Units are not dollars/tokens; distinct agent IDs are not independent control or providers. Allowed-status, completion and progress limitations are RAD-F05/F06. Finite terminal labels do not certify objective completion.',
 'Reuse deterministic budgeted orchestration as a controller around real task-specific checkers; keep workflow completion and accepted answer verdict separate.')
claim('The synthetic diagnostic is a constructed numerical example, with an appropriate nonauthority label.',
 'The adapter forms a mixture of normalized real-vector outer products, applies explicit dimension/spectral policies, and labels outputs DETERMINISTIC_SYNTHETIC_DIAGNOSTIC. Positive mixtures of normalized outer products have a conditional PSD/trace-one foundation. Arithmetic failures become unavailable reports.',
 [(96,1,144),(80,1,58),(87,1,118),(88,1,1001)],
 'No RNG, eigensolver or NumPy conformance run. Full table reading and census are not a proof of upstream identity or distribution quality. These are text-seeded synthetic states, not physical QM observations, truth scores or evidence of model efficacy.',
 'Use only as an explicitly synthetic reproducibility/diagnostic example; do not use its quantum-labelled coordinates as a benchmark acceptance oracle.',('RA-T13',))
claim('Research checkpoints preserve declared state consistency under a trusted-host boundary.',
 'Mission/ledger/candidate digest, contiguous event sequence, reservation key-set and occurrence count checks are meaningful local consistency controls. The owner explicitly states that its unkeyed state digest does not authenticate a caller who recomputes it.',
 [(66,964,1066),(56,1,384),(58,1,143)],
 'Resume does not replay every transition/payload or establish terminal truth. Successful host checks and evidence references remain supplied observations. Source-only review does not replace OS isolation or actual checker execution.',
 'Use checkpoints for crash recovery within a trusted controller; obtain task truth from separately bound checker outputs and do not promote restored terminal labels into proof.')

finding('DDC step-chain hashes omit metrics and timestamps.',
 'The step hash input contains class/carrier/witness/receipt labels but excludes phi_1, gamma_2 and timestamp. Two admitted steps with identical included fields and different metrics therefore have the same prehash input and head while producing different metric histories. State hashes also hash class labels rather than state bytes.',
 [(79,519,595),(78,1,52)],
 'An omitted-field projection, not a SHA collision or a demonstrated historical tampering event. A separate immutable full receipt may supply the missing binding, but this head alone does not.',
 'Before using the tape head to bind evaluator results, hash the complete canonical step including metrics and time/policy semantics or explicitly bind a separately checked full-step digest.',('RA-T01',),'P1')
finding('Compensation heads bind branch ID and count rather than branch contents.',
 'record_compensation_branch checks authority and nonempty class labels, but the hash record includes only branch_id and step_count alongside chain metadata. Different branch tapes of the same length can share a head in separate histories; branch DFA validity is not checked here.',
 [(79,717,779)],
 'Duplicate IDs within one evaluator are refused. The finite counterexample concerns two histories and does not claim a hash collision.',
 'Bind the complete ordered compensation steps and run the intended dialect/adjacency checks before treating a compensation head as evidence of the branch.',('RA-T02',),'P1')
finding('OEARS terminal refusal conflicts with complete-tape admission.',
 'The OEARS M rule permits no following token, while complete validation requires the final token T for every dialect. M is a valid refusal prefix, M is incomplete, and M T is rejected. Thus no completed OEARS tape can contain that terminal refusal.',
 [(79,133,166),(79,236,276),(79,785,813)],
 'Exact contradiction in the inspected rules; no Rust execution. Legacy M T semantics differ and are not covered by this counterexample.',
 'Choose one explicit OEARS completion rule for refusal and align complete validation, terminalized state, replay and tests with it.',('RA-T03',),'P1')
finding('Exact per-step metrics do not guarantee exact bounded window arithmetic.',
 'Metrics are reduced to Rational64 individually, then sliding-window sum/mean uses unchecked Rational64 additions. Two individually representable i64-max integer metrics already require an unrepresentable sum. Missing metrics also enter history as zero, which conflates unavailable and measured zero for these summaries.',
 [(79,497,517),(79,578,645)],
 'Exact arithmetic representability control only. Compiled dependency overflow behavior was not run; the report does not choose panic or wrap as the observed result.',
 'Use arbitrary-precision accumulation or checked arithmetic with an explicit refusal, and retain unavailable metrics as unavailable.',('RA-T04',),'P1')
finding('Scheduler status and completion are not enforced task outcomes.',
 'SceneSpec validates allowed_result_statuses, but scheduler.advance checks scene identity without checking membership in that set or assigned producer identity. A terminal scene becomes COMPLETED for any non-stop status: with allowed PASS and empty stop list, an incoming HOLD becomes COMPLETED. Continuation halt similarly marks any nonempty history COMPLETED. complete_bout uses a fixed PASS/changed_state=1 completion input for traversal.',
 [(97,82,115),(95,246,270),(95,309,343),(94,33,58),(13,421,483)],
 'These are choreography labels; they may intentionally mean run termination. They must not be consumed as accepted-task evidence. Stronger receipt bindings elsewhere do not change this transition predicate.',
 'Enforce declared scene/producer admission and separate terminated, halted, exhausted and task-accepted states in executable experiment accounting.',('RA-T06',),'P1')
finding('Residual worsening can reset the no-progress counter.',
 'run_swarm sets refined_residual=1 whenever post_residual differs from pre_residual. For residual1 to2, delta is positive and status HOLD, but progressed is true and scheduler dry_rounds resets. The oscillation detector also receives that positive progress signal.',
 [(94,138,159),(94,183,207),(95,325,331),(93,1,66)],
 'Total step/unit and visit bounds remain; this is a stagnation semantics defect rather than an infinite-loop claim.',
 'Define progress against a task-preserving ordered residual or a separately checked refinement relation; record mere change independently.',('RA-T07',),'P1')
finding('PASS_TO_MASTER publication checks verdict without binding the current task/candidate.',
 'skill_run parses a checker receipt and requires Accepted for PASS_TO_MASTER, but does not compare its candidate content digest/optional candidate ID with the current task, objective or selected candidate. The checker parser itself supplies those identity fields; publication retains them without establishing the relationship.',
 [(74,187,215),(74,267,317),(74,375,394),(19,90,163)],
 'No forged receipt or filesystem publication was executed. This is the standalone writer boundary; a correctly binding caller can supply the missing assurance.',
 'Require an exact task/candidate/checker-policy binding and successful task-specific receipt validation before publishing an accepted answer.',('RA-T11',),'P1')
finding('Nested dialectic budgets are local copies, not a conserved experiment budget.',
 'AdversaryMachine.nest opens a child with the unchanged parent remaining budget. Two children of a100 budget can each spend60 under their local checks. This is valid local accounting but exceeds a shared100 experiment cap.',
 [(17,166,194),(17,282,309)],
 'The separate active PFP gateway has reservation/recovery mechanisms (RAD-C02); this finding must not be generalized to that ledger. No provider spend occurred.',
 'Document local budget scope or reserve each child allocation from one shared controller before any live dispatch.',('RA-T05',))
finding('Generic boundary trailers do not establish production qualification.',
 'Sixty-nine complete matching trailers instantiate the same bounded-count mechanism after nominal origin/claim/identifier substitutions. Their tests exercise count admission rather than the enclosing carrier, scheduler or provider algorithm. Other trailers construct Ok/Err directly. Mutation-accounting comments therefore cannot establish the claimed production mutation campaign from these bodies.',
 [(1,71,187),(17,952,1074),(96,146,162),(86,122,137)],
 'All distinct owner prefixes and every template residual were reviewed. This does not imply all meaningful tests elsewhere are absent; separately referenced test targets were not run or granted reading credit.',
 'Keep finite count tests as count tests. Qualify actual workflow predicates using bound negative controls and real task failures; do not use trailer counts as experiment success evidence.')
finding('Response-schema numeric semantics need an explicit dialect contract.',
 'The local integer type admits values representable through as_i64/as_u64, and number equality compares rendered strings. Mathematical1 and1.0 can therefore differ, and larger exact integers are outside that integer predicate. Regex and local-ref handling are also a deliberately restricted implementation.',
 [(64,338,361),(64,472,512)],
 'No external schema validator or serde runtime was invoked. This is a concrete language-boundary review, not a claim of whole-standard conformance failure.',
 'Freeze the supported numeric/ref/regex dialect for provider outputs and test equivalent numeric encodings against it; avoid presenting the subset as interchangeable with every schema evaluator.',('RA-T12',))
finding('Carrier and matrix admission do not establish the intended topology automatically.',
 'Public Network::new checks edge endpoints but accepts faces without their boundary. The JSON parser is stronger. Separately, primary gates verify declared matrix algebra without reconstructing incidence matrices from the supplied carrier. Thus algebraic witness acceptance needs an explicit encoding relation to the intended complex/task.',
 [(9,124,149),(9,721,762),(40,365,435),(40,688,727)],
 'The direct constructor witness does not bypass the stronger JSON parser. Valid declared matrices can support a correct finite theorem even when their application interpretation remains unproved.',
 'Centralize validated complex construction and bind/recompute oriented incidence matrices from that carrier before using cohomology or LP certificates as task evidence.',('RA-T09','RA-T10'))

prior=R/'dag/reviews/additional_ops_adversary_remaining.json';pb=prior.read_bytes()
assert h(pb)=='caecb3f4bd44905896516a0c56c485747f146eefd877fa70a8426521bd8a73f0'
reconciliation=[
 {'prior_ids':['OAR-F06'],'assessment':'PFP gateway now reviewed here has explicit reservation/unknown/settled accounting; the prior finding concerns the separate Python researcher dispatch path. Do not equate those owners or claim the Python crash window is repaired.'},
 {'prior_ids':['OAR-F14'],'assessment':'Rust complete_bout compares an exact DDC prefix. This is a different owner/buffer from the Python event mirror that only counts lines; stronger Rust behavior does not retroactively repair the mirror.'},
 {'prior_ids':['OAR-F21'],'assessment':'Rust local valuation receipt alone leaves epoch semantics external, but run_swarm compares candidate/epoch/probes/weights. This preserves the earlier distinction between a local DTO and its stronger orchestration boundary.'},
 {'prior_ids':['OAR-F23'],'assessment':'Fixed completion inputs persist in native complete_bout; the deterministic scheduler is real bounded choreography, while task acceptance remains a separate checker result.'}
]
out.update(status='complete_declared_scope',claims=claims,findings=findings,
 controls_artifact='dag/reviews/additional_rust_adversary_remaining_controls.json',
 controls_sha256=h(Path(str(P)+'_controls.json').read_bytes()),
 prior_report={'path':'dag/reviews/additional_ops_adversary_remaining.json','sha256':h(pb),'relationship':'Prior reviewed findings consulted, not newly executed and no new reading credit for linked original Python files.','reconciliation':reconciliation},
 limitations=[
 'All 99 frozen source bodies are covered: 33 directly and 66 by complete owner prefix plus exact pinned template and all residuals. No partial/bounded/pending scoped file remains. Full source reading does not constitute a proof of every table value or external dependency.',
 'Fresh execution is limited to 14 standalone standard-library finite controls. No original modules/functions, native/Cargo/tests, retained provider runners, credentials, network or private benchmark were accessed/executed.',
 'Cargo explicit external test targets, included YAML/JCS/strict-JSON/runtime helpers, linear-algebra/eigensolver owners and OS/native implementations were not newly fully read in this slice. Prior source reviews remain separate evidence; includes/imports confer no credit.',
 'No live performance, scientific utility, paid-spend bound under arbitrary concurrency or deployment isolation claim is made. Historical comments and stored outcomes are not fresh tests.',
 'Only this audit prefix was written. No production repair or source change was made. This scope is frozen; no new scope was started.'
 ])
out['summary'].update(partial_source_reads=0,bounded_dispositions=0,claims=len(claims),findings=len(findings),independent_controls=14,original_source_edits=0)
out['reading_ledger_sha256']=h(Path(str(P)+'_read_ledger.json').read_bytes())
out['completion_reading_snapshot']={'path':'dag/reviews/additional_rust_adversary_remaining_checkpoint099.json.snapshot','sha256':h(Path(str(P)+'_checkpoint099.json.snapshot').read_bytes()),'role':'Preserved source-reading checkpoint before synthesis; not a second active DAG report.'}
out['repair_priorities']=[
 'For a concrete experiment, first bind accepted checker receipts to exact task/candidate/policy and keep task acceptance separate from scheduler completion (RAD-F05/F07).',
 'If DDC metrics/compensation are used as decision evidence, repair complete-step binding, refusal completion and checked accumulation (RAD-F01..F04).',
 'Use frozen positive-weight epoch binding already present; make progress mean checked improvement/refinement, not mere change (RAD-C01/RAD-F06).',
 'Route paid work through one actual reservation/unknown/settled controller; copied nested budgets and agent-ID labels are insufficient global controls (RAD-C02/RAD-F08).'
]
for name in ['_notes.json','_controls.py','_template_transfers.json']:
 out.setdefault('audit_inputs',[]).append({'path':'dag/reviews/'+P.name+name,'sha256':h(Path(str(P)+name).read_bytes())})
Path(str(P)+'.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
md=['# Rust adversary source review','',
 'Completed 99/99 frozen paths, 1,602,171 bytes and 45,350 lines: 33 direct full bodies plus 66 complete owner-prefix/exact-template/all-residual transfers. Zero partial, bounded or pending scoped files. Fourteen independent finite controls passed; no original/native/provider code ran.','',
 'This report identifies reusable execution checks and concrete boundaries. It does not establish model performance, task success, physical QM results or production qualification. Full file assessments remain below; the repair priorities focus on executable workflow behavior.','',
 '## Immediate workflow implications','']
md.extend('- '+x for x in out['repair_priorities'])
for kind,rows in [('Supported contributions',claims),('Findings',findings)]:
 md.extend(['','## '+kind,''])
 for r in rows:
  md.extend([f"### {r['id']}: {r['title']}",'',r['assessment'],'','Limits: '+r['limits'],'',('Reuse: '+r['workflow_reuse']) if 'workflow_reuse' in r else 'Next action: '+r['next_action'],'',
   'Evidence: '+ '; '.join(f"`{e['path']}:{e['lines'][0]}–{e['lines'][1]}`" for e in r['source_evidence'])+'.',''])
md.extend(['## Prior evidence reconciliation',''])
for r in reconciliation:md.extend([', '.join(r['prior_ids'])+': '+r['assessment'],''])
md.extend(['## Coverage and limits',''])
md.extend('- '+x for x in out['limitations'])
md.extend(['','## Per-file assessments',''])
for r in out['file_reviews']:
 md.extend([f"### {r['path']}",'',f"SHA256 `{r['sha256']}`; complete lines 1–{r['source_line_count']}; {r['review_level']}.",'',r['assessment'],''])
Path(str(P)+'.md').write_text('\n'.join(md),encoding='utf8')
print(json.dumps({'claims':len(claims),'findings':len(findings),'report_sha256':h(Path(str(P)+'.json').read_bytes())}))
