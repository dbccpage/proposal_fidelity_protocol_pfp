"""Assemble evidence graphs without upgrading inventory into mathematical review."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from source_revisions import followup_revisions

ROOT=Path(__file__).resolve().parents[1]
DAG=ROOT/'dag'

def read(name, default):
    p=DAG/name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def write(name, value):
    (DAG/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def normalized_claim(claim):
    """Preserve report fields while linking supported alternate receipt schemas."""
    result=dict(claim)
    if 'statement' not in result and isinstance(result.get('claim'),str):
        result['statement']=result['claim']
    if not result.get('evidence'):
        for field in ('source_evidence','source_ranges','sources'):
            citations=result.get(field)
            if isinstance(citations,list) and citations:
                result['evidence']=citations
                break
    return result


def source_version(source, citation, inventory_by_path, revisions):
    """Resolve a citation only to an inventory pin or a validated migration revision."""
    original=inventory_by_path[source]
    digest=citation.get('sha256') if isinstance(citation,dict) else None
    if digest in (None,original['sha256']):
        return 'SOURCE:'+source,original
    revision=revisions.get((source,digest))
    if revision is None:
        raise ValueError('Finding cites conflicting source pin: '+source)
    return 'SOURCE:'+source+'@'+digest,revision


def validate(nodes, edges):
    ids=[n['id'] for n in nodes]
    if len(ids)!=len(set(ids)):
        raise ValueError('duplicate node identifier')
    adj={k:[] for k in ids}; incoming=dict.fromkeys(ids,0)
    for e in edges:
        if e['from'] not in adj or e['to'] not in adj:
            raise ValueError(f'undefined edge endpoint: {e}')
        adj[e['from']].append(e['to']);incoming[e['to']]+=1
    ready=[k for k,v in incoming.items() if v==0]; count=0
    while ready:
        k=ready.pop();count+=1
        for other in adj[k]:
            incoming[other]-=1
            if incoming[other]==0: ready.append(other)
    if count!=len(ids): raise ValueError('cycle in DAG')
    return {'unique_nodes':len(ids),'edges':len(edges),'acyclic':True}

def main():
    inventory=read('file_inventory.json',{})
    systems=read('reviews/systems_audit.json',{})
    papers=read('reviews/papers_audit.json',{})
    pfp=read('reviews/pfp_audit.json',{})
    workflows=read('reviews/workflows_audit.json',{})
    coverage=read('reviews/coverage.json',{})
    timestamp=datetime.now(timezone.utc).isoformat()
    supersessions=read('reviews/report_supersessions.json',{}).get('supersessions',[])
    superseded=set()
    for entry in supersessions:
        for key in ('superseded','current'):
            path=(ROOT/entry[key]).resolve()
            if not path.is_relative_to((DAG/'reviews').resolve()) or not path.is_file():
                raise ValueError('Invalid report supersession: '+entry[key])
        superseded.add(entry['superseded'])
    additional=[]
    for path in sorted((DAG/'reviews').glob('additional_*.json')):
        if path.relative_to(ROOT).as_posix() in superseded: continue
        report=json.loads(path.read_text(encoding='utf-8'))
        # Count-only validation summaries do not contribute claims or sources.
        if isinstance(report,dict) and isinstance(report.get('file_reviews'),list): additional.append((path,report))
    benchmark_review_path = ROOT/'workflows'/'wf52_finite_qm_benchmark'/'rational_panel_review.json'
    benchmark_review = read('../workflows/wf52_finite_qm_benchmark/rational_panel_review.json', {})
    if benchmark_review:
        delta_registry=read('../workflows/wf52_finite_qm_benchmark/pilot_20261110/implementation_revisions.json',{})
        deltas={row['path']:row for row in delta_registry.get('revisions',[])}
        changed_review_sources=[]
        for row in benchmark_review['file_reviews']:
            current_hash=hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()
            if current_hash != row['sha256']:
                delta=deltas.get(row['path'],{})
                if delta_registry.get('status')!='targeted_delta_tested' or delta.get('reviewed_sha256')!=row['sha256'] or delta.get('current_sha256')!=current_hash:
                    raise ValueError('Benchmark review source pin changed without a separate delta record: ' + row['path'])
                changed_review_sources.append(delta)
        for claim in benchmark_review.get('claims', []):
            claim['source_scope'] = 'Historical benchmark review at its recorded source hashes; subsequent targeted deltas are separate and do not extend this review.'
            claim['subsequent_implementation_revisions']=changed_review_sources
        additional.append((benchmark_review_path, benchmark_review))
    common={'schema_version':'1.0','generated_at_utc':timestamp,
            'repository':'https://github.com/dbccpage/proposal_fidelity_protocol_pfp',
            'source_commit':inventory.get('local_head'),
            'status':'in_progress','scope_complete':False}
    nodes=[]; edges=[]; assumptions={}
    extra_claims=[]
    for path,report in additional:
        for claim in report.get('claims',[]):
            if isinstance(claim,dict) and 'id' in claim: extra_claims.append(normalized_claim(claim))
    for claim in systems.get('claims',[])+pfp.get('claims',[])+extra_claims:
        nodes.append({'id':claim['id'],'kind':'mathematical_or_implementation_claim',**claim})
        for dependency in claim.get('dependencies',[]):
            key='ASSUMPTION-'+hashlib.sha256(dependency.encode()).hexdigest()[:16]
            assumptions[key]={'id':key,'kind':'explicit_assumption_or_obligation','statement':dependency,
                              'status':'requires_evidence_not_discharged_by_this_edge'}
            edges.append({'from':key,'to':claim['id'],'kind':'requires'})
    nodes.extend(assumptions.values())
    for foundation in pfp.get('additional_mathematical_foundations',[]):
        nodes.append({'kind':'mathematical_foundation',**foundation})
    for paper in papers.get('papers',[]):
        nodes.append({'id':'PAPER:'+paper['path'],'kind':'paper_assessment',**paper})
    inventory_by_path={r['path']:r for r in inventory.get('files',[])}
    for row in benchmark_review.get('file_reviews', []):
        inventory_by_path[row['path']] = {'sha256':row['sha256'], 'outside_original_inventory':True}
    support_migration=read('migrations/demo_support_verification.json',{})
    source_revisions={}
    support_summary={k:support_migration.get(k) for k in ('status','moved_files','move_counts','original_bytes','source_originals_absent','all_original_recovery_hashes_verified')}
    if support_migration:
        support_summary['receipt']='dag/migrations/demo_support_verification.json'
        support_summary['interpretation']='Relocation and ownership classification only; historical results and runnable adapters need separate assessment.'
        for row in support_migration.get('locations',[]):
            if row['source_repo']=='pfp' and row['original_path'] in inventory_by_path:
                inventory_by_path[row['original_path']]['current_location']=row
        if support_migration.get('status')!='verified':
            raise ValueError('Unverified support migration')
        for row in support_migration.get('retained_source_revisions',[]):
            if row['source_repo']!='pfp' or row['path'] not in inventory_by_path:continue
            original=inventory_by_path[row['path']]
            path=(ROOT/row['path']).resolve()
            if (not path.is_relative_to(ROOT) or original['sha256']!=row['original_sha256']
                    or hashlib.sha256(path.read_bytes()).hexdigest()!=row['current_sha256']):
                raise ValueError('Migration source revision pin changed: '+row['path'])
            source_revisions[(row['path'],row['current_sha256'])]={
                'sha256':row['current_sha256'],'outside_original_inventory':True,
                'original_sha256':row['original_sha256'],
                'revision_custody':'dag/migrations/demo_support_verification.json'}
    for row in followup_revisions(ROOT, inventory_by_path):
        source_revisions[(row['path'],row['current_sha256'])]={
            'sha256':row['current_sha256'],'outside_original_inventory':True,
            'original_sha256':row['original_sha256'],
            'revision_custody':row['revision_custody']}
    source_nodes={}
    for node in list(nodes):
        for citation in node.get('evidence',[]):
            if isinstance(citation,str): source=citation.split(':',1)[0]
            elif isinstance(citation,dict): source=citation.get('path')
            else: continue
            if source not in inventory_by_path:continue
            key,record=source_version(source,citation,inventory_by_path,source_revisions)
            source_nodes[key]={'id':key,'kind':'pinned_source_file','path':source,'sha256':record['sha256'],'assessment_scope':'Evidence for the linked scoped claim; full-file review tracked separately.'}
            if record.get('outside_original_inventory'):
                source_nodes[key]['assessment_scope'] = 'New benchmark code reviewed separately; does not add coverage credit to the original inventory.'
            if record.get('revision_custody'):
                source_nodes[key].update({
                    'assessment_scope':'Authorized migration navigation revision, separately pinned from the original source; no additional original-inventory coverage.',
                    'original_sha256':record['original_sha256'],
                    'revision_custody':record['revision_custody']})
            if record.get('current_location'):
                source_nodes[key]['current_location']=record['current_location']
            edges.append({'from':key,'to':node['id'],'kind':'source_evidence_not_automatic_proof','citation':citation})
    nodes.extend(source_nodes.values())
    derivation={**common,'interpretation':'Edges are declared dependencies, not themselves proofs. Claims retain separate implementation, formal, numerical and empirical evidence grades.',
                'review_ledger':'dag/file_inventory.json',
                'coverage_at_inventory':inventory.get('counts',{}),
                'substantive_coverage':{k:coverage.get(k) for k in ['scope_files','counts','files_with_bounded_automated_assessment','all_files_substantively_reviewed']},
                'per_file_coverage_ledger':'dag/reviews/coverage.json',
                'reproduced_mathematical_counterexamples':read('reviews/mathematical_counterexamples.json',{}),
                'container_inspection':'dag/reviews/container_artifacts.json',
                'pdf_inspection':'dag/reviews/pdf_artifacts.json',
                'review_reports':['dag/reviews/pfp_audit.json','dag/reviews/systems_audit.json','dag/reviews/papers_audit.json','dag/reviews/workflows_audit.json']+[path.relative_to(ROOT).as_posix() for path,_ in additional],
                'historical_report_supersessions':supersessions,
                'demo_support_relocation':support_summary,
                'nodes':nodes,'edges':edges,
                'findings':systems.get('findings',[])+pfp.get('findings',[])+[finding for _,report in additional for finding in report.get('findings',[])],
                'remaining_work':['Complete per-file substantive audit; hashing and parsing do not satisfy this obligation.',
                                  'Complete supporting-paper artifact, reference, proof/source and reproduction assessments; all 38 primary manuscripts have a first substantive assessment.',
                                  'Audit native implementations and claimed Lean correspondence at pinned source.']}
    derivation['graph_validation']=validate(nodes,edges)
    write('derivations_dag.json',derivation)
    registry=workflows.get('registry',{})
    wnodes=[{**n,'kind':'existing_workflow_family','evaluation_status':'not_run_on_sealed_seed'} for n in registry.get('family_nodes',[])]
    for correction in read('../workflows/wf18_dossier_replay_campaign/pilots/workflow_corrections.json',{}).get('corrections',[]):
        node=next(n for n in wnodes if n['id']==correction['workflow_id'])
        source=ROOT/correction['source']
        if hashlib.sha256(source.read_bytes()).hexdigest()!=correction['source_sha256']:
            raise ValueError('Workflow mathematical correction source changed')
        values=node[correction['field']]
        if correction['declared_statement'] not in values:
            raise ValueError('Workflow declaration changed; review the correction again')
        node['declared_'+correction['field']+'_before_audit']=values
        node[correction['field']]=[correction['audited_replacement'] if value==correction['declared_statement'] else value for value in values]
        node.setdefault('audit_corrections',[]).append(correction)
    wedges=[{**e,'kind':'documented_design_dependency'} for e in registry.get('family_edges',[])]
    ideas=[]
    for p in sorted((DAG/'research').glob('research_*.json')) if (DAG/'research').exists() else []:
        ideas.append(json.loads(p.read_text(encoding='utf-8')))
    for report in ideas:
        for idea in report['ideas']:
            wnodes.append({'kind':'new_workflow_proposal','agent_number':report['agent_number'],**idea})
    catalog=read('composition_catalog.json',{})
    for candidate in catalog.get('candidates',[]):
        wnodes.append(candidate)
        for macro in candidate['macros']:
            wedges.append({'from':macro,'to':candidate['id'],'kind':'uses_mechanism_under_explicit_bridge_obligations'})
    composition_metadata={k:v for k,v in catalog.items() if k!='candidates'}
    for control, calls in [('direct',1),('self_critique',2)]:
        wnodes.append({'id':'CONTROL:'+control,'kind':'executable_benchmark_control','plan':control,
                       'implementation':'workflows/wf52_finite_qm_benchmark/reference_runner.py','max_paid_calls':calls,
                       'supported_provider':'guarded OpenRouter with exact finite campaign admission',
                       'cost_ceiling_usd':'0.10','billing_scope':'whole run; conditional on recorded provider enforcement premises',
                       'evaluation_status':'synthetic_transport_tested_not_live_evaluated',
                       'composition_scope':'Control arm outside the finite research-macro permutation grammar.'})
    # Importing these inert specifications reads only public checker source bytes;
    # it performs no provider, credential or private-evaluator access.
    sys.path.insert(0, str(ROOT/'workflows'/'wf52_finite_qm_benchmark'))
    from rational_workflows import EXPERIMENTS
    for plan, specification in EXPERIMENTS.items():
        node_id = 'EXECUTABLE:' + plan
        wnodes.append({'id':node_id,'kind':'executable_bounded_research_adaptation','plan':plan,
                       'source_idea':'R05-I02','implementation':'workflows/wf52_finite_qm_benchmark/reference_runner.py',
                       'specification':'workflows/wf52_finite_qm_benchmark/rational_workflows.py',
                       'checker':'workflows/wf52_finite_qm_benchmark/rational_panel.py',
                       'specification_sha256':hashlib.sha256(json.dumps(specification,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest(),
                       'checker_source_sha256':specification['source_pins']['rational_panel.py'],
                       'public_contract_sha256':specification['contract_sha256'],
                       'synthetic_validation':'workflows/wf52_finite_qm_benchmark/rational_panel_validation.json',
                       'independent_review':'workflows/wf52_finite_qm_benchmark/rational_panel_review.json',
                       'visibility':specification['visibility'],
                       'max_paid_calls':len(specification['stages']),
                       'max_output_tokens_total':sum(stage['max_output_tokens'] for stage in specification['stages']),
                       'cost_ceiling_usd':'0.10','billing_scope':'one serial run ledger; each next dispatch requires admission; later stages may be refused',
                       'runnable':True,'evaluated':False,
                       'evaluation_status':'synthetic_checker_and_transport_tested_not_live_evaluated',
                       'mathematical_scope':'Exact rational counterexamples to explicitly encoded real equalities under declared guards. Finite passes and semantic alignment do not certify the QM answer.',
                       'open_obligations':['analytic and matrix expressions','semantic alignment of claims to prose and seed','prerequisite queries','native PFP/EIS/OPERADS binding','model accuracy and cost benefit'],
                       'composition_scope':'Bounded adaptation and ablations outside the unimplemented macro-composition grammar.'})
        wedges.append({'from':'R05-I02','to':node_id,'kind':'bounded_executable_adaptation_with_explicit_open_obligations'})
    from hamiltonian_workflows import MATRIX_PLANS
    for plan, specification in MATRIX_PLANS.items():
        node_id='EXECUTABLE:'+plan
        wnodes.append({'id':node_id,'kind':'executable_bounded_research_adaptation','plan':plan,
                       'source_idea':'R01-I03','implementation':'workflows/wf52_finite_qm_benchmark/reference_runner.py',
                       'specification':'workflows/wf52_finite_qm_benchmark/hamiltonian_workflows.py',
                       'checker':'workflows/wf52_finite_qm_benchmark/hamiltonian_artifact.py',
                       'specification_sha256':hashlib.sha256(json.dumps(specification,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest(),
                       'source_pins':specification['source_pins'],
                       'max_paid_calls':len(specification['stages']),
                       'max_output_tokens_total':sum(stage['max_output_tokens'] for stage in specification['stages']),
                       'cost_ceiling_usd':'0.10','billing_scope':'whole run including the single optional repair; unknown liability stops dispatch',
                       'runnable':True,'evaluated':False,'evaluation_status':'synthetic_checked_awaiting_live_results',
                       'mathematical_scope':specification['scope'],
                       'checked_gate':specification['checked'],'host_matrix_control':specification['host_matrix'],
                       'repair_policy':specification['repair_policy'],
                       'independent_review':'workflows/wf52_finite_qm_benchmark/hamiltonian_workflows_review.json',
                       'open_obligations':['Final-answer correctness is not certified by intermediate acceptance','Native PFP/EIS/PCIV/OPERADS interface integration','Repeated matched-resource evidence beyond one item']})
        wedges.append({'from':'R01-I03','to':node_id,'kind':'bounded_representation_transport_adaptation_or_ablation'})
    from charpoly_workflows import CHARPOLY_PLANS
    for plan, specification in CHARPOLY_PLANS.items():
        node_id='EXECUTABLE:'+plan
        wnodes.append({'id':node_id,'kind':'executable_bounded_research_adaptation','plan':plan,
                       'source_idea':'R01-I03','implementation':'workflows/wf52_finite_qm_benchmark/reference_runner.py',
                       'specification':'workflows/wf52_finite_qm_benchmark/charpoly_workflows.py',
                       'checker':'workflows/wf52_finite_qm_benchmark/qm_native_charpoly.py',
                       'source_pins':specification['source_pins'],
                       'max_paid_calls':len(specification['stages']),
                       'max_output_tokens_total':sum(stage['max_output_tokens'] for stage in specification['stages']),
                       'cost_ceiling_usd':'0.10','billing_scope':'Whole run including optional repair and synthesis; unknown liability stops dispatch.',
                       'runnable':True,'evaluated':False,'evaluation_status':'offline_integration_tested_awaiting_live_results',
                       'mathematical_scope':specification['scope'],'checked_gate':specification['checked'],
                       'validation':'workflows/wf52_finite_qm_benchmark/charpoly_validation.xml',
                       'independent_review':'workflows/wf52_finite_qm_benchmark/charpoly_workflows_review.json',
                       'open_obligations':['Intermediate certificate does not certify final prose or whole-QM solution',
                                           'Full PFP host and EIS/PCIV/OPERADS integration',
                                           'Repeated matched-resource evidence beyond one seed']})
        wedges.append({'from':'R01-I03','to':node_id,'kind':'native_exact_arithmetic_certificate_adaptation_or_ablation'})
    from host_charpoly_workflows import HOST_CHARPOLY_PLANS
    for plan, specification in HOST_CHARPOLY_PLANS.items():
        node_id='EXECUTABLE:'+plan
        wnodes.append({'id':node_id,'kind':'executable_bounded_research_adaptation','plan':plan,
                       'source_idea':'R01-I03','implementation':'workflows/wf52_finite_qm_benchmark/reference_runner.py',
                       'specification':'workflows/wf52_finite_qm_benchmark/host_charpoly_workflows.py',
                       'checker':'workflows/wf52_finite_qm_benchmark/qm_host_charpoly.py',
                       'source_pins':specification['source_pins'],
                       'max_paid_calls':len(specification['stages']),
                       'max_output_tokens_total':sum(stage['max_output_tokens'] for stage in specification['stages']),
                       'cost_ceiling_usd':'0.10','billing_scope':'Whole run single call; unknown liability stops dispatch.',
                       'runnable':True,'evaluated':False,'evaluation_status':'offline_verified_prepared_unexecuted_campaign',
                       'mathematical_scope':specification['scope'],'checked_gate':specification['checked'],
                       'independent_review':'dag/reviews/additional_host_charpoly.json',
                       'open_obligations':['Intermediate certificate does not certify final prose or whole-QM solution',
                                           'Downstream derivations, projectors, and final answers are uncertified',
                                           'Repeated matched-resource evidence beyond one seed awaiting campaign authorization']})
        wedges.append({'from':'R01-I03','to':node_id,'kind':'host_derived_charpoly_coverage_first_adaptation'})
    from eis_pciv_workflows import EIS_PCIV_PLANS
    for plan, specification in EIS_PCIV_PLANS.items():
        node_id='EXECUTABLE:'+plan
        wnodes.append({'id':node_id,'kind':'executable_bounded_research_adaptation','plan':plan,
                       'source_idea':'R01-I03','implementation':'workflows/wf52_finite_qm_benchmark/reference_runner.py',
                       'specification':'workflows/wf52_finite_qm_benchmark/eis_pciv_workflows.py',
                       'checker':'eis/use_cases/two_signal_regulation.py' if plan=='eis_two_signal_charpoly_v1' else 'pciv/use_cases/transitive_immunity.py',
                       'source_pins':specification['source_pins'],
                       'max_paid_calls':len(specification['stages']),
                       'max_output_tokens_total':sum(stage['max_output_tokens'] for stage in specification['stages']),
                       'cost_ceiling_usd':'0.10','billing_scope':'Whole run serial ledger within 100,000 microUSD cap; unknown liability or Stage 1 two-signal refusal stops dispatch.',
                       'runnable':True,'evaluated':False,'evaluation_status':'offline_verified_prepared_unexecuted_campaign',
                       'mathematical_scope':specification['scope'],'checked_gate':specification['checked'],
                       'independent_review':'dag/reviews/additional_eis_pciv.json',
                       'open_obligations':['Intermediate certificate or pre-dispatch quotient does not certify final prose or whole-QM solution',
                                           'Coarse unnormalized prose watchers suffer split-fibre accuracy collisions; structured witnesses required',
                                           'Live 5-arm paired campaign qm-eis-pciv-pilot-20261111 and multi-seed holdout split remain unexecuted']})
        wedges.append({'from':'R01-I03','to':node_id,'kind':'eis_two_signal_or_pciv_quotient_bounded_adaptation'})
    from section_workflows import SECTION_PLANS
    for plan, specification in SECTION_PLANS.items():
        node_id='CONTROL:'+plan
        wnodes.append({'id':node_id,'kind':'executable_benchmark_control','plan':plan,
                       'implementation':'workflows/wf52_finite_qm_benchmark/reference_runner.py',
                       'specification':'workflows/wf52_finite_qm_benchmark/section_workflows.py',
                       'source_pins':specification['source_pins'],
                       'max_paid_calls':5,'max_output_tokens_total':16000,
                       'cost_ceiling_usd':'0.10','billing_scope':'One serial run ledger across five isolated calls; failures stop later dispatch.',
                       'runnable':True,'evaluated':False,'evaluation_status':'offline_tested_not_live_evaluated',
                       'mathematical_scope':specification['scope'],
                       'composition_scope':'Output-allocation control outside the research-macro grammar; no certificate-shard claim.',
                       'validation':'workflows/wf52_finite_qm_benchmark/section_validation.xml',
                       'open_obligations':['Cross-section consistency','Final-answer correctness','Matched-resource repeated comparison']})
        wedges.append({'from':'CONTROL:direct','to':node_id,'kind':'public_task_output_allocation_control'})
    live_summary=read('../workflows/wf52_finite_qm_benchmark/results_summary.json',{})
    live_rows=live_summary.get('raw_runs',[])
    for node in wnodes:
        observations=[row for row in live_rows if row['plan']==node.get('plan')]
        if observations:
            node['evaluation_status']='live_pilot_observed_not_validated_improvement'
            node['observed_run_snapshots']=observations
            node['results_source']='workflows/wf52_finite_qm_benchmark/results_summary.json'
            node['evaluated']=all(row.get('score') is not None for row in observations)
    documentation=read('wiki/workflow_documentation.json',{})
    documented={entry['node_id']:entry for entry in documentation.get('entries',[])}
    if len(documented)!=len(documentation.get('entries',[])):
        raise ValueError('Duplicate workflow documentation mapping')
    required={node['id'] for node in wnodes if node.get('runnable') is True
              or node.get('kind')=='executable_benchmark_control'
              or node.get('status')=='implemented'}
    if required-set(documented):
        raise ValueError('Implemented workflows need Wiki entries: '+str(sorted(required-set(documented))))
    if set(documented)-{node['id'] for node in wnodes}:
        raise ValueError('Wiki entry references an unknown workflow')
    for node in wnodes:
        if node['id'] not in documented: continue
        entry=documented[node['id']]
        page=(ROOT/entry['page']).resolve()
        if not page.is_relative_to((ROOT/'wiki').resolve()) or page.suffix!='.md':
            raise ValueError('Invalid workflow Wiki source path')
        if hashlib.sha256(page.read_bytes()).hexdigest()!=entry['page_sha256']:
            raise ValueError('Workflow Wiki source changed; refresh documentation mapping: '+entry['page'])
        node['wiki_documentation']=entry
    wf={**common,'benchmark':read('../workflows/wf52_finite_qm_benchmark/commitment.json',{}),
        'nodes':wnodes,'edges':wedges,
        'existing_nested_components':registry.get('component_nodes',[]),
        'existing_manifest_registry':registry.get('manifest_registry',[]),
        'recorded_setting_variations':registry.get('recorded_variations',[]),
        'demo_support_relocation':support_summary,
        'historical_result_policy':'Historical percentages and live labels are retained source assertions, not verified new outcomes or evidence of this benchmark.',
        'research_agent_reports':ideas,
        'composition_space':composition_metadata or {'status':'awaiting_enumeration'},
        'evaluation':{'status':'live_pilot_observed' if live_rows else 'not_run','seed_cases':1,'per_run_cap_usd':'0.10',
                      'observed_runs':len(live_rows),'results_source':'workflows/wf52_finite_qm_benchmark/results_summary.json',
                      'cap_scope':'aggregate all model calls, parallel branches, retries and chargeable model judges in one workflow execution',
                      'metrics':['total_money_usd','input_tokens','output_tokens','reasoning_tokens_when_reported','wall_time_seconds','sum_provider_time_seconds','accuracy_by_frozen_rubric','refusal_rate','checker_error_rate'],
                      'controls':['direct same-model baseline','equal-token baseline','equal-spend baseline','equal-time baseline','ablated mechanisms','randomized execution order','repeated provider sampling'],
                      'limits':['One seed measures within-item behavior, not generalization.',
                                'Prompt evolution on the scored seed is exploratory adaptation, not held-out transfer.',
                                'Unknown cost or timeout retains the reservation and stops dependent calls.',
                                'Model agreement and schema success are not mathematical accuracy.'],
                      'private_evaluator':'separate trusted process after outputs are frozen; no key in prompts or retrieval'},
        'executable_control_documentation':'workflows/wf52_finite_qm_benchmark/live_runner.md',
        'executable_adaptation_documentation':'workflows/wf52_finite_qm_benchmark/rational_panel.md',
        'workflow_wiki_documentation':documentation,
        'remaining_work':['Finish existing workflow/source audit','Complete ten distinct research-agent reports' if len(ideas)<10 else 'Review all ten research reports and their independent source claims','Bind remaining candidate adapters to concrete schemas/checkers; design enumeration and one bounded adaptation are not admission of the entire registry','Repair observed workflow failures and test useful mathematical checks beyond the rational-only panel','Repeat matched-resource comparisons before claiming an accuracy/cost/time advantage']}
    wf['graph_validation']=validate(wnodes,wedges)
    write('workflows_dag.json',wf)
    print(json.dumps({'derivations':derivation['graph_validation'],'workflows':wf['graph_validation'],'status':'in_progress'}))

if __name__=='__main__': main()
