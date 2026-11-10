"""Materialize manual final-answer judgments; no provider or private-key access."""
import datetime,hashlib,importlib.util,json,pathlib
H=pathlib.Path(__file__).resolve().parent;B=H.parent
spec=importlib.util.spec_from_file_location('reviewed_summary',B/'summarize_runs.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
rubric_path=H/'evaluator_rubric.json';rubric=json.loads(rubric_path.read_text());rubric_hash=hashlib.sha256(rubric_path.read_bytes()).hexdigest();assert rubric_hash=='eaeffe10123292bda1385fcf444ae0a1b75e919f40ce09391cf1be49edcdf9dc'
criteria={c['id']:c for s in rubric['sections']for c in s['criteria']};section_map={'pure_state':'pure_entanglement','thermal':'thermal_entanglement'}
# Scores/reasons are manual judgments after reading each complete frozen answer_text.
manual={
'direct':{
 'checks.conventions':(1,'Initial basis and Pauli definitions are correct, but subsequent tensor indices and Y-tensor-Y values repeatedly contradict them.','The Pauli matrices:'),
 'spectrum.block_reduction':(0,'No valid full Hamiltonian restriction or invariant-subspace reduction is completed. Earlier correct exchange fragments are repeatedly abandoned for contradictory matrices.','Wait now I'),
},
'rational_fixed_panel_v1':{
 'checks.conventions':(2,'The stated computational basis, Z signs and tensor ordering agree with the seed.','computational basis |00⟩, |01⟩, |10⟩, |11⟩'),
 'thermal.partition_function':(1,'Gives the correct defining trace expression, but never evaluates it for this Hamiltonian or counts degeneracies.','Z_β = tr(exp(−βH))'),
 'spectrum.block_reduction':(0,'A generic promise of eigenvalue decomposition is not a matrix, block reduction or derivation.','The spectral analysis uses the characteristic polynomial'),
},
'rational_blind_panel_v1':{
 'spectrum.block_reduction':(4,'Derives the correct4x4 matrix and its even/odd invariant decomposition.','H_{22} = -K + 2Δ, H_{33} = -K - 2Δ'),
 'spectrum.energies':(2,'Correct even eigenvalue K with multiplicity2 and correct2x2 quadratic setup, but loses a factor2 in the odd eigenvalues.','λ_± = [−2K ± √( (4Δ)^2 + (4J)^2 )] / 2 = −K ± √(Δ² + J²)'),
 'spectrum.projectors':(2,'Correct even projector and zero-radius odd projector appear. General odd projectors are not completed and attempted vectors use incorrect energies.','P_K = |00⟩⟨00| + |11⟩⟨11|'),
 'spectrum.coincident_energies':(1,'Recognizes the need to merge a coincident odd eigenvalue with the even doublet, but the locus4K²=J²+Delta² is wrong and the final K<=0 restriction is also wrong.','K is triple degenerate iff 4K² = J² + Δ² and K ≤ 0'),
 'spectrum.zero_radius':(2,'States the correct J=Delta=0 diagonal Hamiltonian and both doublets, and separately identifies complete degeneracy at K=0.','K is quadruple degenerate iff J = Δ = K = 0'),
 'checks.conventions':(2,'Correct Pauli conventions, basis order and full Hamiltonian matrix are explicit; later eigenvalue errors are charged to their mathematical criteria.','Conventions: hbar = k_B = 1.'),
},
'rational_visible_panel_v1':{
 'spectrum.block_reduction':(2,'Correct invariant even/odd decomposition and exchange entries, but omits the -2Delta entry on |10>.','So H = [[K, 0, 0, 0], [0, -K + 2Δ, 2J, 0], [0, 2J, -K, 0], [0, 0, 0, K]]'),
 'spectrum.energies':(2,'Correct even doublet and correct Delta=0 energy set, but the general odd eigenvalues belong to the wrong block.','When Δ = 0, J ≠ 0:'),
 'spectrum.projectors':(2,'Correct generic even projector; normalized odd-vector construction is valid only for the altered block (and correct Delta=0 subcase). J=0 basis assignments are reversed.','P_K = |00⟩⟨00| + |11⟩⟨11|'),
 'spectrum.coincident_energies':(1,'The Delta=0 crossing |J|=|K| is correctly identified. General and J=0 branches contain false claims.','Δ=0, J≠0, and |J|=|K|'),
 'spectrum.zero_radius':(0,'Incorrectly claims all eigenvalues equal K at J=Delta=0, losing the -K doublet.','When J=Δ=0: all eigenvalues = K'),
 'checks.conventions':(1,'Basis and Pauli definitions are initially correct, but J=0 eigenprojector labels swap |01> and |10>.','μ₊ = -K + 2Δ, eigenspace span{|10⟩}'),
},
'self_critique':{
 'spectrum.block_reduction':(2,'Correct parity subspaces and Delta/K diagonal terms; incorrect Y tensor Y gives a false even block and halves the odd exchange.','**Key observation**'),
 'spectrum.energies':(1,'A correct K eigenvalue and the J=0 spectral restriction survive; generic multiplicities and three claimed energies are wrong.','\\lambda_2 &= K - 2J'),
 'spectrum.projectors':(1,'Correct even rank2 projector is stated only in the J=0 subcase. General rank1 projectors are assigned to incorrect energy values and do not resolve actual spectral eigenspaces.','P_+ = |00\\rangle\\langle 00| + |11\\rangle\\langle 11|'),
 'spectrum.coincident_energies':(0,'Claims generic nondegeneracy and omits the actual always-degenerate even doublet and crossings.','Always 1 unless $ J = 0 $'),
 'spectrum.zero_radius':(1,'Correctly recovers K and -K doublets at J=Delta=0, but does not merge them into a single rank4 projector when K=0.','degeneracy 2 for $ K $, 2 for $ -K $'),
 'checks.conventions':(1,'Stated Pauli matrix and basis are correct, but the subsequent Y action has reversed signs and its tensor matrix is inconsistent with the action.','Y|0\\rangle = -i|1\\rangle'),
 'checks.decoupled_limit':(1,'Correct J=0 diagonal spectrum is explicitly checked, but no decoupled dynamics or thermal results are supplied.','**Exceptional case**: $ J = 0 $'),
}}
counterexamples={
'direct':[{'parameters':{'J':1,'Delta':0,'K':0},'reference':'H|00>=0','candidate_error':'Repeated claimed exchange matrices have a nonzero |00>-|11> coupling; late tensor indexing is unresolved.'}],
'rational_fixed_panel_v1':[{'parameters':{'J':1,'Delta':0,'K':0},'reference':'P(t)=sin²(2t)','candidate_error':'The blanket assertion that every expression is a rational function of t and beta cannot represent the requested exact dynamics/thermal functions.'}],
'rational_blind_panel_v1':[{'parameters':{'J':1,'Delta':0,'K':0},'reference_spectrum':[0,0,2,-2],'candidate_spectrum':[0,0,1,-1]},{'parameters':{'J':1,'Delta':0,'K':1},'reference':'K=1 has rank3','candidate_error':'The claimed4K²=J²+Delta² crossing test misses this.'}],
'rational_visible_panel_v1':[{'parameters':{'J':0,'Delta':1,'K':0},'reference_diagonal':[0,2,-2,0],'candidate_diagonal':[0,2,0,0]},{'parameters':{'J':0,'Delta':0,'K':1},'reference_spectrum':[1,-1,-1,1],'candidate_spectrum':[1,1,1,1]}],
'self_critique':[{'parameters':{'J':1,'Delta':0,'K':0},'reference_spectrum':[0,0,2,-2],'candidate_spectrum':[0,-2,1,-1],'reference_trace':0,'candidate_trace':-2}]
}
grades={};details={}
for name,assigned in manual.items():
 path=H/'runs'/name/'run.json';receipt,digest=mod.read_frozen_receipt(path);answer=receipt['answer_text'];rows=[];points={k:0 for k in mod.RUBRIC};deductions=[]
 for cid,c in criteria.items():
  if cid in assigned:
   awarded,reason,anchor=assigned[cid];start=answer.index(anchor);ev={'kind':'quoted_final_text','character_range_half_open':[start,start+len(anchor)],'quote':anchor}
  else:
   awarded=0;reason='No completed result or derivation for this criterion appears in the final response. The entire frozen final text was reviewed; drafts/challenges supply no credit.';ev={'kind':'whole_final_text_omission_review','character_range_half_open':[0,len(answer)],'final_tail':answer[-160:]}
  assert 0<=awarded<=c['max_points'];section=section_map.get(cid.split('.')[0],cid.split('.')[0]);points[section]+=awarded;row={'criterion_id':cid,'max_points':c['max_points'],'awarded':awarded,'deducted':c['max_points']-awarded,'reason':reason,'evidence':ev};rows.append(row)
  if row['deducted']:deductions.append({'criterion_id':cid,'points_deducted':row['deducted'],'reason':reason,'evidence':ev})
 final_calls=[c for c in receipt['calls']if c.get('response_sha256')==receipt['answer_sha256']];finishes=[c.get('finish_reason')for c in final_calls];errors=(receipt.get('host_checks')or{}).get('artifact_errors',{})
 grade={'run_id':receipt['run_id'],'run_sha256':digest,'answer_sha256':receipt['answer_sha256'],'seed_sha256':receipt['seed_sha256'],'evaluator_id':'audit_systems_independent_public_seed_v1','method':'trusted_post_freeze_mathematical_review','points':points,'deductions':deductions,'rubric_sha256':rubric_hash,'final_only':True,'total':sum(points.values()),'operational_status':{'receipt_status':receipt['status'],'host_artifact_errors':errors,'final_finish_reasons':finishes,'final_truncated':'length'in finishes,'usable_required_envelope':not bool(errors),'mathematical_raw_text_graded':True},'counterexamples':counterexamples[name]};assert mod.validate_grade(grade,receipt,digest)==grade['total'];grades[receipt['run_id']]=grade
 details[receipt['run_id']]={'run_path':str(path.relative_to(H.parent.parent.parent)).replace('\\','/'),'run_sha256':digest,'answer_sha256':receipt['answer_sha256'],'full_final_read':True,'reviewed_characters_half_open':[0,len(answer)],'criteria':rows,'total':grade['total'],'counterexamples':counterexamples[name],'operational_status':grade['operational_status']}
(H/'grades.json').write_text(json.dumps(grades,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
evidence={'schema_version':'manual_criterion_evidence_v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rubric_sha256':rubric_hash,'source_validator_sha256':hashlib.sha256((B/'summarize_runs.py').read_bytes()).hexdigest(),'method':'Independent mathematical derivation from two public sources; all five frozen final answer_text bodies read in full and graded after explicit parent freeze confirmation.','private_answer_key_access':False,'workflow_feedback':False,'exposure_note':'A metadata-inspection command accidentally expanded nested provider request/response material and was tool-truncated. No intermediate draft/challenge content was used or credited; grades depend only on the complete answer_text bodies.','section_name_adapter':section_map,'runs':details}
(H/'criterion_evidence.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
md=['# Independent post-freeze evaluation','','The five original final responses score **1, 7, 3, 13 and 8 /100** (direct, self-critique, fixed, blind and visible respectively). All were graded against the unchanged pre-output rubric. Partial readable mathematics was scored even when the JSON envelope failed. No draft or challenge received credit.','','| Workflow | Spectrum /20 | Dynamics /20 | Pure /25 | Thermal /25 | Checks /10 | Total | Final output |','|---|---:|---:|---:|---:|---:|---:|---|']
for name in ['direct','self_critique','rational_fixed_panel_v1','rational_blind_panel_v1','rational_visible_panel_v1']:
 g=next(g for g in grades.values()if ':'+name+':'in g['run_id']);v=g['points'];md.append('| '+name+' | '+' | '.join(str(v[k])for k in mod.RUBRIC)+' | '+str(g['total'])+' | '+('length-truncated'if g['operational_status']['final_truncated']else'stopped')+(' / envelope invalid'if not g['operational_status']['usable_required_envelope']else'')+' |')
md+=['','- **Direct:** repeats contradictory tensor-product calculations and truncates before obtaining the full Hamiltonian or any requested result.','- **Self-critique:** the final correction substitutes a wrong Hamiltonian. For J=1, Delta=K=0 its spectrum has trace-2, while the given Hamiltonian has trace0. It truncates in projectors; later parts are absent.','- **Fixed panel:** returns a schema-wrapped promise of a derivation, not the derivation. Only conventions and the general partition-function definition receive credit.','- **Blind panel:** gets the Hamiltonian block right, then loses a factor2 in its odd energies and propagates that error into degeneracies/eigenvectors. It truncates before dynamics.','- **Visible panel:** drops the -2Delta diagonal entry, derives the spectrum of that different block, and mishandles zero-radius degeneracy. It truncates before dynamics.','','Four final answers hit length limits; the three panel attempts also fail their required envelope. Those operational outcomes remain distinct from mathematical scores. These five one-item, one-sample results do not establish a workflow ranking, transfer or statistical advantage.','','All25 criterion scores, exact character-span evidence, deductions, counterexamples and run/answer/seed hashes are in criterion_evidence.json and grades.json. The reviewed summarize_runs.read_frozen_receipt and validate_grade checks pass for all five. The rubric uses pure_state/thermal labels; the grade adapter maps these unchanged weights to pure_entanglement/thermal_entanglement required by the summary schema.','','Provenance limitation: one attempted metadata-only inspection over-expanded nested provider request/response material. No intermediate content was used for scoring. No private answer key/storage was accessed and no evaluator correction was sent to workflow requests.','']
(H/'evaluation.md').write_text('\n'.join(md),encoding='utf-8');print(json.dumps({k:v['total']for k,v in grades.items()},indent=2))
