import sys,json,re,datetime
from pathlib import Path
sys.dont_write_bytecode=True
import additional_paper_011_history_ledgers_audit as a
sc=a.scope();change,claim=sc['files'];deps=a.read('_dependencies.json');ctl=a.read('_controls.json')
def ev(which,*ranges):
 r={'change':change,'claim':claim}[which]
 return {'path':r['path'],'sha256':r['sha256'],'lines':[list(x) for x in ranges]}
def dev(name):
 r=next(x for x in deps if Path(x['path']).name==name)
 return {'path':r['path'],'sha256':r['sha256'],'lines':r['reviewed_lines']}
def item(id,title,statement,evidence,**extra):
 return {'id':id,'title':title,'statement':statement,'evidence':list(dict.fromkeys(x['path'] for x in evidence)),'source_evidence':evidence,**extra}
claims=[
 item('P011LEDGER-CL01','Declared structures are not a derivation of primitive admission',
 'The ledger explicitly assumes regimes, event-indexed replay, contexts, profiles and declared separability. Supply-no-op is a definition-relative theorem; absence of an internal forcing predicate is a language boundary, not an ontological impossibility theorem. Later graph-genesis statements show nextFamilyP cannot change the graph stores in its declared two-shape response grammar; a different growth grammar remains a separate admission. These limits rule out promoting the documents into a derivation of carriers, logic, authority, physical time or a primitive inscription.',
 [ev('claim',(13,41),(2087,2145),(3530,3545)),ev('change',(681,850))],validation_status='full_prose_scope_review; cited proof owners not freshly rebuilt'),
 item('P011LEDGER-CL02','Minimum and completion claims have several different scopes',
 'Cost-one impossibility, cost-two witnesses, finite mu1 catalogs and mu2 uniqueness under the two-item/arity-sum regime are different claims. Complete minimum-family branching additionally depends on the declared grammar, closure policy and executable orbit coverage. Fifteen exported transition steps include supply and yield only10-12 separation-response rounds; the claimed requested15 augmentation rounds were not completed. Internal index identity is not profile equality. This audit does not convert the historic executable catalogs or replay counts into an unbounded theorem.',
 [ev('claim',(181,360),(361,540),(3855,3894)),ev('change',(2551,2590))],validation_status='full_prose_scope_review; bounded-count claims retained as historical evidence'),
 item('P011LEDGER-CL03','Representation transport requires explicit commuting laws',
 'The retained erasure theorem compares two Lean semantics, not the Python source. Dataset/count/key correspondence and nontrivial form-permutation behavior remain executable or separately proved components. Thirteen transition codes are the image of a supplied one-step projection and fail right congruence under common suffixes, so they cannot substitute for raw replay states/events. A sound terminating confluent two-rule normalizer is explicitly incomplete for replay equivalence. These are reusable representation-boundary checks, not proof that every adapter preserves semantics.',
 [ev('claim',(541,720),(2264,2387),(3896,3919)),ev('change',(2551,2670))],validation_status='full_prose_scope_review; no original engine execution'),
 item('P011LEDGER-CL04','Question-relative compression and fidelity provide useful conditional mathematics',
 'Factorization through a supplied presentation is fiber constancy on the represented domain; the factor is unique only on its image. Enlarging a supplied question family splits an old class exactly when it supplies a new separator. Adequacy for every question family reduces to injectivity. The transposition construction turns a represented factorization failure into a p-preserving, q-breaking symmetry. Heterogeneous faithful descent also needs equations binding both embeddings to the translations; generated fidelity is the least equivalence containing admitted coherent steps. These constructions preserve supplied distinctions and expose failed identifications; they do not generate the initial indices, comparison demand or a preferred repair.',
 [ev('claim',(1871,1931),(2643,2715),(3359,3549))],validation_status='mathematical scope assessed from complete prose; no unexamined theorem-name proof credit'),
 item('P011LEDGER-CL05','Four-gate independence is nonentailment under a chosen convention',
 'The corrected obstruction account distinguishes three written factors from four total Boolean gates. Each omitted gate has a counterstate with the other three true, but all16 valuations do not occur because declared/zero share an observation input. The no-observation zero gate is true by convention; changing it to false removes one independence witness. Independent finite abstraction confirms12 admissible Boolean patterns and the four omission patterns, without claiming to revalidate native state realization. No-observation obstruction refusal is selected semantics rather than a forced primitive law.',
 [ev('claim',(3057,3140))],validation_status='full_prose_review_plus_finite_abstraction',control_ids=['P011LEDGER-C03']),
 item('P011LEDGER-CL06','Naturality refusals depend on the supplied arrows and fixed points',
 'Raw selection may exist while an equivariant or natural selection fails. The one-object obstruction is near-definitional once naturality means a fixed admissible pair; transport machinery and a positive four-point fixture provide its useful boundary. Heterogeneous examples still contain no cross-object arrows and assert no category. The separately consulted fixed-point selector equivalence explicitly takes an inhabitant w:W; thus the empty-carrier concern is already handled by its owner. None of these results proves arbitrary selection impossible or supplies a universal symmetry-breaking mechanism.',
 [ev('claim',(3002,3055),(3142,3293)),ev('change',(2087,2106)),dev('Breaking.lean')],validation_status='full_prose_review_plus_targeted_owner_contract'),
 item('P011LEDGER-CL07','The later G1 closure is conditional and the G4 chain claim is withdrawn',
 'For a fixed radius d and alphabet bound k independent of chain length, ViewLocal yields at most k^(2d+1) local colour patterns, and n>=k^(2d+1)+2d+2 forces a deep equal-view pair. The ledger claims horizon-free exclusion only for this class and proves radius-one profile correspondence for arbitrary chain length. It explicitly supersedes restricted T5/T6 obligations while leaving unrestricted G1/closure policy open. Clears and Fires can both hold because they are post-repair versus inherited pre-repair predicates. The455-chain G4 run is withdrawn because the engine never received the loop pair; fixed Challenge3 catalogs cannot certify a missing chain adapter.',
 [ev('claim',(3295,3357),(3551,3711),(3815,3847)),ev('change',(2329,2346))],validation_status='full_prose_scope_review; native proofs and historical runs not rerun'),
 item('P011LEDGER-CL08','Boundary and weight calculations support narrower structures than their historical titles',
 'Alternating double deletion cancels pairwise on arbitrary vertex lists; strict ascent is needed for face distinctness, not d-squared-zero. Independent controls check all127 binary-vertex lists of lengths0-6, including repetitions, and show the signless integer triangle does not cancel. This is a finite corroboration, not a fresh general Lean proof. The filler remains a declared complete-shell guard, not homology or horn filling. AltNum is correctly relabeled a stage-varying statistic. Weight-profile/sign-shadow and coordinate-square descent results do not construct Hilbert space, probability or dynamics; the earlier representation climb is explicitly refuted.',
 [ev('claim',(1621,1690),(1829,1869),(2163,2262)),ev('change',(620,625))],validation_status='full_prose_scope_review_plus_bounded_independent_control',control_ids=['P011LEDGER-C04']),
 item('P011LEDGER-CL09','Certificate labels and custody are separate from the statements they annotate',
 'The documents explicitly retract hash injectivity from a pair of mutation tests, bind axiom counts to dated runs, and distinguish a37-row status/count mirror from checking each theorem annotation. Name resolution and regex coverage are not semantic citation verification; a same-parser census can miss the same declaration on both sides. The ledger also discloses composite/missing classification fields. These are useful audit mechanisms and acknowledged limitations, not evidence that every historic receipt or body pin is currently valid.',
 [ev('claim',(1933,1953),(2444,2448),(2883,2978)),ev('change',(1871,2020),(2601,2618))],validation_status='full_prose_scope_review; no claim of universal historical custody validation'),
 item('P011LEDGER-CL10','Historical withdrawal and current stability refutation are different results',
 'The old exact stable-content claim was withdrawn using one halted full-trace counterexample and one live-unfunded restricted-fragment example. The ledger still records the live-funded converse as OPEN. Native audit P011-NATIVE-F016 separately refutes that residual using ordered protection of(1,0) and symmetric separation queried at(0,1). The existing trace-sufficiency theorem for the reversed pair yields all-traces separation for the queried pair. The initial-state control merely checks the finite facts; the all-traces argument is source-derived and no new Lean run occurred.',
 [ev('change',(721,741)),ev('claim',(1955,2028)),dev('StableContent.lean'),dev('PrimitivePassage.lean')],validation_status='historical_reconciliation_with_existing_native_finding',related_findings=['P011-NATIVE-F016'],control_ids=['P011LEDGER-C05'])
]
findings=[
 item('P011LEDGER-F01','Kernel orientation ceiling is too narrow',
 'The boundary sentence at claim ledger2822-2825 says WitnessedDiff carries no orientation beyond pointing. Its delta field can encode an arbitrary directed irreflexive relation, and ofSetting_exact recovers any decidable candidate-A relation. Two3-point kernels with the same designated endpoints(0,1), Boolean delta, Zero(v) iff v=false, and nonzero-pair sets{(0,1)} versus{(0,1),(1,2)} meet the structure fields while the latter retains a directed edge outside the designated pair. Thus absence of additional orientation is not a signature restriction. The adjoining limits on retention, protection, operations and dynamics remain accurate.',
 [ev('claim',(2717,2738),(2822,2826)),dev('ContactKernel.lean')],severity='scope_wording_error',validation_status='read_owner_contract_plus_independent_finite_counterexample',control_ids=['P011LEDGER-C02'],recommendation='Preserve the archive; in any live interpretation say no orientation law beyond the admitted data is forced, while arbitrary directed difference data can be represented.'),
 item('P011LEDGER-F02','Internal distinction is conflated with a justified choice of reading',
 'CL-READING-UNDERDETERMINATION says no internal fact separates L and F. Literally this is false: R2L contains2 data and R2F3, with different required-pair fields, and the retained finite catalogs also differ. The local boundary clarifies the intended absence of an internally justified criterion selecting an admission semantics. That underdetermination claim is not refuted by noticing the differing carrier sizes. Treat this as ambiguous overbroad wording, not a failure of both derivations or a proof that one reading is preferred.',
 [ev('claim',(708,720)),dev('Basic.lean')],severity='low_wording_ambiguity',validation_status='read_definition_plus_finite_field_comparison',control_ids=['P011LEDGER-C01'],recommendation='For a live restatement use: both admitted readings remain viable; the supplied challenge does not force a preferred admission reading.'),
 item('P011LEDGER-F03','The retained live-funded OPEN proposal is now refuted',
 'The frozen ledger explicitly leaves live-funded trace stability implying ordered protected separation open at1993-1997, after withdrawing the unrestricted converse at1955-1981. P011-NATIVE-F016 refutes this remaining proposition: protect(1,0), observe[[0]], keep budget1 and halted=false, and query(0,1). Reverse protected separation persists by the existing sufficiency theorem; separation is symmetric while protection membership is ordered. This is a reconciliation of the existing native finding, not a duplicate fresh proof or an allegation that the ledger claimed the open proposition was a theorem. The historical halted/unfunded withdrawal did not already contain this counterexample.',
 [ev('change',(721,741)),ev('claim',(1955,2028)),dev('StableContent.lean'),dev('PrimitivePassage.lean')],severity='false_open_conjecture',validation_status='existing_native_F016_reconciled_with_historical_ledger',related_findings=['P011-NATIVE-F016'],control_ids=['P011LEDGER-C05'],recommendation='Retain the archived OPEN record; current status should reference the reverse-orientation counterexample and formulate any replacement using appropriate protection closure.')
]
reconciliations=[
 {'topic':'stale G1 OPEN wording','status':'resolved_by_explicit_supersession_not_a_new_finding','source_evidence':[ev('claim',(3551,3556),(3582,3603),(3815,3847))],'assessment':'Later entries explicitly retain unrestricted questions and close only restricted T5/T6. Earlier OPEN statements are historical context, not an undisclosed current contradiction.'},
 {'topic':'AltNum invariant','status':'historical_correction_located','related_findings':['P011HIST-F01'],'source_evidence':[ev('change',(620,623)),ev('claim',(1621,1660))],'assessment':'The change log explicitly relabels the changing4,-2,2,1 quantity a statistic. The prior formal-history stale source-introduction finding must not be promoted to an unretracted ledger invariant claim.'},
 {'topic':'selector empty carrier','status':'owner_hypothesis_handles_boundary','source_evidence':[dev('Breaking.lean')],'assessment':'Owner explicitly takes w:W and explains why the forward direction needs it. No source theorem defect is claimed.'},
 {'topic':'event idempotence','status':'distinct_grammars_not_contradiction','source_evidence':[ev('claim',(2311,2339))],'assessment':'Passage step_idem is about its guarded event grammar. It does not assert idempotence of Basic NewDatum/Form append constructors.'},
 {'topic':'classification debt','status':'disclosed_historical_limit','source_evidence':[ev('claim',(3,9),(3896,3919)),ev('change',(2604,2618))],'assessment':'Eight-way single-class field promise coexists with mixed theorem/computation entries; the later log already discloses85 composite and6 unclassed entries in its then137-entry census, then140 body pins. Do not silently flatten these into uniform theorem status.'}
]
term_counts={}
for term in ['PFP','EIS','PCIV','OPERADS']:
 term_counts[term]={Path(r['path']).name:len(re.findall(r'\b'+term+r'\b',(a.ROOT/r['path']).read_text(encoding='utf-8-sig'),flags=re.I)) for r in sc['files']}
notes={
 'analysis_status':'complete_for_frozen_two_file_scope',
 'summary':'Both frozen historical prose bodies were read in full with durable per-chunk assessments:2files,375978bytes,6589lines. Three findings distinguish two wording issues from the existing native refutation of an explicitly OPEN residual. The records are strongly self-correcting and expose meaningful reusable finite/conditional mechanisms, but do not derive primitive admission or validate framework-wide implementation.',
 'claims':claims,'findings':findings,'controls':ctl['controls'],'reconciliations':reconciliations,
 'external_dependencies_consulted':deps+[{'path':'dag/reviews/additional_paper_011_native.json','sha256':a.sha(a.ROOT/'dag/reviews/additional_paper_011_native.json'),'selector':'findings[id=P011-NATIVE-F016]','status':'single_finding_parsed_and_owner_spans_consulted','full_source_read':False,'coverage_credit':'none'}],
 'framework_contribution_assessment':{
  'status':'audit_interpretation_not_a_proved_framework_integration','body_term_census':term_counts,
  'PFP':'Directly reusable patterns are separation of proposal from admitted execution, complete candidate-family retention, explicit assumptions/costs, and witness/countermodel-bound claims. The two documents do not establish the current PFP implementation or a complete end-to-end proposal-fidelity theorem.',
  'EIS':'Question-relative fibers, comparison witnesses and strict-refinement evidence can support an evidence/identity interface. The acronym is not instantiated in these bodies; no EIS theorem or deployment result is inferred.',
  'PCIV':'Source/statement/axiom bindings, independent declaration census, exact failure controls and scoped certificate statuses are reusable for contract validation. No PCIV interface or general verification theorem is defined in this two-file scope.',
  'OPERADS':'Typed transport, identity/reversal/composition closure and preservation obligations offer components for compositional reasoning. The documents explicitly withhold even category structure for some families; they do not define or verify operadic substitution, arities, unit/associativity/equivariance laws for a named OPERADS implementation.',
  'primitive_genesis_ceiling':'A supplied grammar, comparison/network, admission policy, driver or finite colouring remains an input. Least closure and conditional refusal do not derive those inputs from an inscription, nor establish a physical, ontological or authority bridge.'},
 'custody':{'scope_path':'dag/reviews/additional_paper_011_history_ledger_scope.json','scope_sha256':a.sha(a.SCOPE),'initial_reconciliation':'dag/reviews/additional_paper_011_history_ledgers_initial_reconciliation.json','read_ledger':'dag/reviews/additional_paper_011_history_ledgers_read_ledger.json','controls_path':'dag/reviews/additional_paper_011_history_ledgers_controls.json','source_file_reconciliations':ctl['source_files'],'source_edits':'none'},
 'limits':[
  'This completes only the two frozen ledger files; repository-wide and other Paper011 partitions remain outside this completion.',
  'Historical prose, author directions and governance statements were reviewed as data, never followed as current instructions.',
  'Every body line has a substantive chunk assessment, but a cited theorem/test/artifact name receives no implicit proof-body, execution or data-replay credit.',
  'Only precise dependency spans were consulted; they are not new full-file coverage. No native build or fresh Lean elaboration occurred.',
  'Independent controls ran with workspace Python3.14.2, not the pinned historical3.12 profile. No original implementation was imported or executed.',
  'The finite gate/control results do not prove the corresponding general native theorem or all-state/all-trace claim. The F016 all-traces argument is source-derived from an existing theorem and symmetric separation.',
  'Hash equality binds the two current bytes to the frozen inventory/parent scope; it does not by itself establish Git-tree membership, author attestation, original-run blindness, or the correctness of every cited historical receipt.',
  'No provider, credential, external/private benchmark, seed, key, answer, original program, archive executable or broad native build access was used.',
  'No original source, historical receipt, shared coverage/DAG/swarm manifest or parent finite report was modified.'
 ]}
a.write('_notes.json',notes);a.report();report=a.read('.json')
assert report['scope']['full_source_reads']==2 and report['scope']['full_source_lines']==6589 and not report['remaining_unsupported_files']
md=['# Paper011 historical ledger review','',notes['summary'],'','Repository-wide audit remains incomplete.','',
 '| File | SHA256 | Read lines |','|---|---|---|']
for r in report['file_reviews']:md.append('| `'+r['path']+'` | `'+r['sha256']+'` |1-'+str(r['line_count'])+' |')
md+=['','The JSON report and durable read ledger retain every chunk range and its substantive assessment. Targeted dependency reads receive no extra full-file credit.','','## Findings','']
for f in findings:md+=['### '+f['id']+' — '+f['title'],'',f['statement'],'','Disposition: '+f['recommendation'],'','Evidence: '+ '; '.join('`'+e['path']+'` '+str(e['lines'])+' SHA256 `'+e['sha256']+'`' for e in f['source_evidence']), '']
md+=['## Mathematical and certificate assessment','']
for c in claims:md+=['- **'+c['id']+' — '+c['title']+'**. '+c['statement'],'']
md+=['## Reconciliations','']
for x in reconciliations:md+=['- **'+x['topic']+'**: '+x['assessment'],'']
md+=['## Reusable mechanisms and limits','']
for key in ['PFP','EIS','PCIV','OPERADS','primitive_genesis_ceiling']:md+=[key+': '+notes['framework_contribution_assessment'][key],'']
md+=['The four framework names have zero exact word occurrences in both document bodies. The mapping above is an audit interpretation, not an assertion that the documents implement those frameworks.','','## Controls and evidence ceiling','']
for c in ctl['controls']:md+=['- `'+c['id']+'`: '+c['status']+'. '+c['limit'],'']
for limit in notes['limits']:md+=['- '+limit,'']
a.file('.md').write_text('\n'.join(md)+'\n',encoding='utf8')
print(json.dumps({'scope':report['scope'],'claims':len(claims),'findings':len(findings),'controls':len(ctl['controls']),'json_sha256':a.sha(a.file('.json')),'markdown_sha256':a.sha(a.file('.md')),'framework_body_term_counts':term_counts}))
