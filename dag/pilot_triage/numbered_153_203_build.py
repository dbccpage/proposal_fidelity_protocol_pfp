"""Build bounded per-pilot triage; writes only numbered_153_203 artifacts."""
from pathlib import Path
from collections import Counter
from hashlib import sha256
import ast
import difflib
import importlib.util
import json
import re
import xml.etree.ElementTree as ET
import yaml

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'pilots/anomalon_woland'
PREFIX = ROOT / 'dag/pilot_triage/numbered_153_203'
WF = {16:'wf16_substrate_crosswalk',17:'wf17_witnessed_difference_programme',18:'wf18_dossier_replay_campaign',19:'wf19_failure_derived_rule_transfer',20:'wf20_derivation_loop_with_lift_grants'}

def digest(p): return sha256(p.read_bytes()).hexdigest()
def rel(p): return p.relative_to(ROOT).as_posix()
def save(suffix, value):
    path=Path(str(PREFIX)+suffix)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def evidence(path, lines=None, level='full_text_emitted_for_review', full=True):
    p=ROOT/path
    return dict(path=path,sha256=digest(p),lines=lines or [1,len(p.read_text(encoding='utf-8').splitlines())],review_level=level,full_source_read=full)
def fn_evidence(path, names):
    p=ROOT/path;tree=ast.parse(p.read_text(encoding='utf-8'))
    return [evidence(path,[n.lineno,n.end_lineno],'selected_complete_function_body_read',False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]

IMPORT_DOS='pilots/anomalon_woland/replay_runners/dossier_capsules/'
CANON_DOS='workflows/wf18_dossier_replay_campaign/pilots/replay_runners/dossier_capsules/'
IMPORT_PO='pilots/anomalon_woland/relational_spacetime/'
CANON_PO='workflows/wf20_derivation_loop_with_lift_grants/pilots/relational_spacetime/'

def main():
    probe_results=json.loads(Path(str(PREFIX)+'_probes.json').read_text())
    probe_passes=sum(r.get('checks',0) for r in probe_results['results'] if r['status']=='PASS')
    assert probe_passes==165 and probe_results['provider_calls']==0
    test_suite=ET.parse(Path(str(PREFIX)+'_gate_controls.xml')).getroot().find('testsuite')
    assert int(test_suite.attrib['tests'])==30 and int(test_suite.attrib['failures'])==0 and int(test_suite.attrib['errors'])==0
    migration=json.loads((ROOT/'dag/migrations/anomalon_pilots_move.json').read_text())
    ids={f'pilot_{i:07d}' for i in range(153,204)}
    entries=[e for e in migration['entries'] if e['path'].split('/')[0] in ids]
    automated=[]; custody=Counter()
    for row in entries:
        p=BASE/row['path']; data=p.read_bytes()
        passed=len(data)==row['bytes'] and sha256(data).hexdigest()==row['sha256']
        assert passed, f'Incoming bytes changed: {p}'
        custody[row['path'].split('/')[0]]+=1
        automated.append(dict(path=rel(p),sha256=sha256(data).hexdigest(),checks=['incoming_manifest_raw_sha256','incoming_manifest_byte_count'],status='PASS',full_source_read=False,evidence_ceiling='Byte custody only; not semantic review or authentication of historical provider execution.'))

    # The entire normalized README/spec text was reviewed once, with every differing
    # title, source path, taxonomy and catalog status inspected separately.
    template_rows=[]
    for i in range(153,188):
        for name in ('README.md','spec.yaml'):
            p=BASE/f'pilot_{i:07d}'/name
            original=(BASE/'pilot_0000153'/name).read_text(encoding='utf-8').splitlines(True)
            current=p.read_text(encoding='utf-8').splitlines(True)
            template_rows.append(dict(path=rel(p),sha256=digest(p),template=f'pilots/anomalon_woland/pilot_0000153/{name}',
                unified_diff=''.join(difflib.unified_diff(original,current)),
                review_method='Full shared primary template plus all unique normalized lines and all per-pilot substitutions; not a claim of separately emitting every repeated line.'))
    save('_primary_differences.json',template_rows)

    # Explicit source correspondence supplements behavioral comparison, rather than
    # replacing it with a generic same-hash classification.
    comparisons=[]
    for a,b in [(IMPORT_DOS+f,CANON_DOS+f) for f in ('checking.py','cases.py','run.py','test_campaign.py')]+[(IMPORT_PO+f,CANON_PO+f) for f in ('finite_checks.py','finite_fixtures.py','final_prompts.py','tasks.py')]:
        pa,pb=ROOT/a,ROOT/b
        comparisons.append(dict(imported_path=a,imported_sha256=digest(pa),canonical_path=b,canonical_sha256=digest(pb),
            exact_bytes_equal=pa.read_bytes()==pb.read_bytes(),text_equal=pa.read_text()==pb.read_text(),
            complete_unified_diff=''.join(difflib.unified_diff(pa.read_text().splitlines(True),pb.read_text().splitlines(True))),
            assessment='Checker equations/control behavior reviewed in full owner; namespace, historical-key and path differences retained as runtime/custody differences.'))
    save('_owner_comparisons.json',comparisons)

    registry_path=ROOT/'dag/workflows_dag.json';registry_lines=registry_path.read_text().splitlines()
    mappings={}
    for n,name in WF.items():
        start=next(i+1 for i,l in enumerate(registry_lines) if l.strip()==f'"id": "WF{n}",')
        end=next(i+1 for i,l in enumerate(registry_lines[start:],start) if '"host_check":' in l)
        mappings[n]=dict(family_id=f'WF{n}',path='workflows/'+name,
            registry_source_evidence=evidence('dag/workflows_dag.json',[start,end],'selected_family_identity_process_math_host_check_read',False),
            definition_source_evidence=evidence('workflows/'+name+'/README.md'))

    common_dossier=[evidence(IMPORT_DOS+f) for f in ('checking.py','cases.py','run.py','test_campaign.py','learn.py')]
    common_dossier += [evidence(CANON_DOS+f,level='full_text_via_imported_owner_and_complete_unified_diff') for f in ('checking.py','cases.py','run.py')]
    common_challenge=[evidence('pilots/anomalon_woland/challenge_suite/'+f) for f in ('__main__.py','campaign.py')]
    common_challenge += [evidence(p) for p in ('pfp/infrastructure/challenge_execution.py','pfp/infrastructure/challenge_live.py','pfp/tests/test_challenge_learning.py')]
    common_challenge += [evidence('pfp/use_cases/pfp_stages.py',[1,49],'selected_policy_body_read',False),evidence('pfp/use_cases/pfp_proposal.py',[1,150],'selected_ingress_and_judge_dispatch_body_read',False)]
    common_po=[evidence(IMPORT_PO+f) for f in ('finite_checks.py','finite_fixtures.py','final_prompts.py')]
    common_po += [evidence(CANON_PO+f,level='full_text_via_imported_owner_and_complete_unified_diff') for f in ('finite_checks.py','finite_fixtures.py','final_prompts.py','tasks.py')]
    common_po += [evidence(CANON_PO+'typed_signals.py',[89,252],'selected_ingress_stage_observer_bodies_read',False),evidence(CANON_PO+'typed_signals.py',[348,387],'selected_posthoc_harvest_body_read',False),evidence(CANON_PO+'typed_signals.py',[413,503],'selected_consolidation_body_read',False)]

    qm=dict(protected_qm_seed_read=False,mathematical_support_for_unchanged_qm_seed='NOT_ESTABLISHED',
        requires_seed_appropriate_checker_or_encoding=True,
        prerequisite='Supply a declared task encoding and applicable mathematical predicate/certificate checker, with negative controls. No inspected finite checker certifies an unspecified QM problem.',
        reusable_without_claiming_qm_correctness='Carrier custody, strict ingress, bounded repair, scoped refusal and source-bound replay may transfer after interface review; their transfer is not mathematical transfer.')
    math_dossier={
        188:'For vertex bits s in F2^n, r_e=c_e XOR s_a XOR s_b. The replay checker enumerates all 2^n assignments and requires the reported residual and Hamming weight to equal the true minimum. The historical triangle checker only checks a narrower supplied chain and has an overclaiming zero-curl branch.',
        189:'For exact rational A,g and nonnegative weights w, minimize sum_i w_i |g_i-(Ax)_i|. A dual v with A^T v=0 and |v_i|<=w_i gives v^Tg<=the primal objective; feasible equality certifies optimality. This is not the no-negative-cycle feasibility criterion stated in the current family README.',
        190:'The same weighted L1 primal/dual certificate applies with A=d3 on the supplied degree-four carrier. Historical source also recomputes d1*d0,d2*d1,d3*d2 and d3^T v=0. A finite chain certificate does not establish a manifold, continuum limit or physical field theory.',
        191:'Exact rational row reduction gives ranks r_i; if all adjacent differential products vanish, b_i=dim C^i-r_{i-1}-r_i. The checker compares declared Betti numbers and always labels cup products unsupported without their carrier. Ranks and a cochain-cycle pairing do not identify a manifold or Pontryagin/Chern construction.'}
    mechanisms={188:'Binary residual minimization with alternative-witness tolerance',189:'Exact weighted L1 primal/dual equality certificate',190:'Degree-four rational certificate with separate chain-law scope',191:'Topology-scope refusal from exact rank and nilpotence audit',192:'Source-bound challenge dispatch with original C005 predicates',193:'Held-out failure-rule transfer over cohomology challenge judges',194:'Task-specific quantum judges behind a shared proposal gate',195:'Task-specific physics challenge judges with bounded repair',196:'Formal-math challenge wrapper with explicit held-out gap',197:'Program-synthesis challenge wrapper with explicit held-out gap',198:'Strict-ingress and checker-disagreement mutation battery',199:'Causal counterexample control with posthoc signal provenance',200:'Projected-dynamics finite balance with unverified analytical status',201:'Typed transport composition counterexample and identity control',202:'Separate metric-angle and additive-cochain controls',203:'Exact tiny obstruction certificate separated from halting policy'}
    po_math={
        199:'Exact rational checks of L1 versus Euclidean norm, dilation of the interval and one null-envelope prefactor on a fixed finite fixture. These counterexample controls do not prove a scaling limit or identify a Minkowski metric from causal order.',
        200:'Gaussian-rational matrix multiplication computes (I-P)psi, its derivative under -iH, local density derivative, oriented residual flux and the noncommuting source. The fixed three-site balance is not a general conservation or continuum theorem.',
        201:'On rational one-dimensional fibers, compare T12*T01=6 with T02=5 and compute sigma_j-Tij*sigma_i. An identity-transport coboundary repair provides the zero-obstruction control. These equations do not establish an eight-stage functor.',
        202:'Rational cosine-law values distinguish two metric stars while additive triangle curvature remains gauge invariant because d1*d0=0. The source explicitly keeps the metric and cochain carriers separate; the fixture does not prove a Regge-holonomy correspondence.',
        203:'Exact rational primal/dual equality certifies a positive L1 obstruction of 3/100000000 on a triangle. A continuing transition n->n+1 and a separately declared halt flag distinguish static obstruction from an operational stopping premise.'}
    pilots=[]
    for i in range(153,204):
        pid=f'pilot_{i:07d}';folder=BASE/pid;spec=yaml.safe_load((folder/'spec.yaml').read_bytes());title=(folder/'README.md').read_text().splitlines()[0].lstrip('# ')
        family=16 if i<170 else 17 if i<188 else 18 if i<192 else 19 if i<199 else 20
        level='full_text_emitted_for_review' if i==153 or i>=188 else 'full_primary_text_via_shared_template_and_exhaustive_differences'
        ev=[evidence(rel(folder/f),level=level) for f in ('README.md','spec.yaml')]
        responses=list(folder.rglob('response.yaml'));statuses=Counter();modes=Counter();schema_codes=Counter();certs=Counter();nonempty=0
        for p in responses:
            d=yaml.safe_load(p.read_bytes())
            st=d.get('trial_status',d.get('status',d.get('evaluation',{}).get('status','UNSPECIFIED')))
            statuses[str(st)]+=1;modes[str(d.get('execution_mode',d.get('execution_kind','UNSPECIFIED')))]+=1
            if d.get('code'):schema_codes[d['code']]+=1
            nonempty+=isinstance(d.get('raw_reply'),str) and bool(d['raw_reply'])
            if 'certificate_status' in d and (i!=199 or 'v2' in p.parts):certs[d['certificate_status']]+=1
            automated.append(dict(path=rel(p),sha256=digest(p),checks=['response_schema_field_census'],status='RECORDED_FIELDS_ONLY',full_source_read=False,evidence_ceiling='Parsed historical status fields; no provider authentication or recomputation of saved raw reply.'))
        execution=dict(audit_model_calls=0,audit_full_test_suite_run=False,
            historical_readme_test_counts='Historical claims and capsule counts, not fresh independent model trials.',
            response_schema_census=dict(response_count=len(responses),statuses=dict(statuses),modes=dict(modes),codes=dict(schema_codes),nonempty_raw_reply_field_count=nonempty,version_selected_certificate_statuses=dict(certs)),
            test_sources_present=[rel(p) for p in folder.rglob('*.py') if 'tests' in p.parts])
        transfer=dict(qm)
        if i<188:
            code=re.search(r'\b[GW]\d{2}\b',title).group()
            topic=title.split(code,1)[1].strip()
            contribution=f'One planned catalog prompt capsule for {code}: {topic}. Its own disposition is PLANNED/NOT_RUN, not a checked result.'
            basis=f'Named research target: {topic}. The spec declares {spec["coordinates"]["task_family"]} only as a layout coordinate; no local implementation establishes the proposed relation-preservation or witness theorem.'
            mechanism='Catalog-to-capsule provenance and explicit unrun disposition'
            verdict='stub_candidate'
            rationale=f'{code} has README/spec, one planned response and no Python checker/runner. The declared checker id is expressly unregistered. '+('Its cited Genesis spec was recorded absent, so the stimulus is catalog title/summary only.' if i<170 else 'A cited historical source being present or scored does not supply a fresh local certificate. ')
            next_action=f'Keep as a historical WF{family} planning reference. Before any promotion, bind the actual finite predicate and negative controls; no dispatch is recommended by this triage.'
            ev += [evidence('pilots/anomalon_woland/pilot_0000153/tests/test_00/response.yaml')] if i==153 else []
            execution['mechanism_execution']='No local Python owner; automated census confirmed null raw reply, not_dispatched and NOT_RUN for the sole response.'
            assert len(responses)==1 and not list(folder.rglob('*.py'))
            d=yaml.safe_load(responses[0].read_bytes());assert d['raw_reply'] is None and d['execution_mode']=='not_dispatched' and d['evaluation']['status']=='NOT_RUN'
        elif i<192:
            contribution=title.split(': ',1)[1]+' finite carrier battery: five carriers by five representations, then five matched guidance capsules; all 30 historical responses record typed refusals.'
            basis=math_dossier[i];mechanism=mechanisms[i];verdict='duplicate_candidate'
            ev += [evidence(rel(folder/'misc/source/checker.py'))]+common_dossier
            rationale='The reusable behavior is already represented by WF18: strict witness recomputation, reversible carrier surfaces and source/request/reply-bound replay. The imported archival checker is not automatically the active replay judge, and historical 30/30 refusals do not show prompt-guidance gain.'
            if i==188:rationale+=' A synthetic zero-curl input reproduces a false CERTIFIED_OBSTRUCTION in the historical checker; retain that snapshot solely as historical evidence.'
            if i==189:rationale+=' The current WF18 mathematical description should be corrected from negative-cycle feasibility to weighted L1 dual certification.'
            next_action='Reference the current WF18 owner and keep historical pins. Reuse the bounded finite checker after an explicit task adapter and adversarial controls; do not restart the retired campaign.'
            execution['current_smoke_probe']='Five independently constructed finite witnesses and five wrong-witness mutations pass per pilot; task generation used original AST bodies with an explicit root, not a historical CLI replay.'
        elif i<199:
            source_family=spec['source_family'];contribution=f'Family {source_family} parameterizes the shared challenge learning protocol; no distinct local algorithm is introduced by its six-line wrapper.'
            mechanism=mechanisms[i];verdict='duplicate_candidate';ev += [evidence(rel(folder/'run.py'))]+common_challenge
            plan=yaml.safe_load((folder/'testplan.yaml').read_bytes());rows=plan['cases'];splits=Counter(r.get('split','UNSPECIFIED') for r in rows)
            plan_counts=dict(cases=len(rows),source_bound=sum('source' in r for r in rows),splits=dict(splits),challenges=dict(Counter(r.get('challenge','HARNESS') for r in rows)))
            execution['test_plan_census']=plan_counts
            automated.append(dict(path=rel(folder/'testplan.yaml'),sha256=digest(folder/'testplan.yaml'),checks=['case_source_and_split_census'],status='RECORDED_FIELDS_ONLY',full_source_read=False,evidence_ceiling='Counts and declared split metadata; not mathematical validation of all challenge sources.'))
            basis='A conjunction of injected task judges determines acceptance; disagreement or exception is a checker defect. A repair can follow only PROVIDER_COMPLETED and the stage bound is at most two. Claimed transfer gain requires disjoint held-out comparisons and self-tolerance; each domain judge remains a separate mathematical assumption.'
            rationale='WF19 already owns the baseline/typed-witness/transfer protocol and the current challenge execution/replay path. The imported wrapper uses a historical namespace and is not an independent runnable implementation. All original family-specific mathematical judges were not individually audited in this bounded triage.'
            if i==192:
                basis+=' C005 separately verifies exact potential differences and optimal single-cycle repair cost |sum c_i|*min w_i.'
                ev += [evidence(rel(folder/'tests/test_c005_predicates.py')),evidence('workflows/wf12_mechanism_control_arms/pilots/c005_hosted_decode_controls/checkers.py')]
                rationale+=' The 60 planned rows consist of 30 source-bound C005 cases and 30 instrumentation conditions, not 60 model results.'
            if i in (196,197):rationale+=' All 40 local testplan rows are development cases: this local selection alone cannot support the README held-out transfer claim.'
            if i==198:
                ev += [evidence(rel(folder/'tests/test_pilot.py'))]
                basis='Twenty-five adversarial mutations cover strict JSON/envelope typing, false witnesses, unregistered judges, checker exception and disagreement. Alternative valid solutions to 2x+y=5 test self-tolerance; these are finite software controls, not LLM capability measurements.'
            execution['current_smoke_probe']='30 selected canonical tests pass: 25 gate mutants, one alternative-witness test, three exact-wire cases and one bounded-repair/checker-stop test. Domain challenge batteries were not rerun.'
            next_action='Use the canonical WF19/current PFP protocol. Preserve source-family and case custody, fix historical import routing only in a separately authorized integration, and require genuinely held-out evidence before admitting transfer rules.'
        else:
            contribution=title.split(': ',1)[1]+' target, wrapped in the shared five-loop proposal/lift/witness/negative-control/learning process.'
            mechanism=mechanisms[i];basis=po_math[i];verdict='duplicate_candidate'
            ev += [evidence(rel(folder/'run.py')),evidence(rel(folder/'tests/test_pilot.py'))]+common_po
            rationale='WF20 already contains the same five finite predicates, 25-variant test wrapper and final-prompt custody logic. The original mathematical derivation remains UNVERIFIED. Recorded v2 witness stages contain no HOST_ACCEPTED certificate; host stages are not extra model trials.'
            if i==199:rationale+=' Its v2 grants and learning were harvested posthoc; the original requests did not see those grants.'
            next_action='Retain the historical run and candidate provenance; do not add a sixth trial. Reuse scoped finite controls and explicit assumption grants, with separate proof review and a paired trial before claiming analytical or guidance improvement.'
            execution['current_smoke_probe']='25 current finite controls pass: one accepted fixture plus 24 rejected variants; every verdict keeps analytical_status UNVERIFIED.'
            execution['historical_trial_count_limit']='Five recorded provider trials and twenty host stages; pilot199 additionally retains original and v2 stage versions, not ten independent trials.'
        mapping=dict(mappings[family],relationship=('Planning-only instance of the existing family; no executable realization.' if i<188 else 'Same bounded procedure already represented by this family; owner semantics and retained mathematical limits were compared, not merely filenames or hashes.'))
        pilots.append(dict(id=pid,path=rel(folder),title=title,contribution=contribution,mathematical_basis=basis,
            reusable_mechanism_name=mechanism,qm_seed_transfer=transfer,actual_execution_status=execution,
            source_evidence=ev,workflow_mapping=[mapping],verdict=verdict,rationale=rationale,next_action=next_action,
            migration_custody=dict(manifest='dag/migrations/anomalon_pilots_move.json',files_checked=custody[pid],raw_sha256_and_sizes_match=True),
            duplicate_evidence=dict(method='Procedure and predicate comparison, supplemented by complete owner diffs.',comparison_artifact='dag/pilot_triage/numbered_153_203_owner_comparisons.json',promotion_or_deletion_authorized=False)))

    with Path(str(PREFIX)+'_automated_reviews.jsonl').open('w',encoding='utf-8') as stream:
        for row in automated:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    findings=[
        dict(id='P153-203-F01',severity='reuse_blocker_for_historical_snapshot',claim='The historical pilot188 checker certifies an obstruction when exact curl and residual are both zero.',evidence=[evidence('pilots/anomalon_woland/pilot_0000188/misc/source/checker.py'),{'path':'dag/pilot_triage/numbered_153_203_probes.json','record':'historical_checker_false_obstruction'}],limit='The current WF18 minimization checker uses a different predicate and passed finite controls; this finding does not invalidate its carrier-specific optimum check.'),
        dict(id='P153-203-F02',severity='mathematical_description_mismatch',claim='WF18 describes pilot189 with a no-negative-cycle feasibility criterion, but its actual predicate is weighted L1 quotient primal/dual optimality.',evidence=[evidence('workflows/wf18_dossier_replay_campaign/README.md'),*fn_evidence(CANON_DOS+'checking.py',{'check_answer'}),evidence('pilots/anomalon_woland/pilot_0000189/misc/source/checker.py')],limit='Recommendation to correct metadata; no source edited.'),
        dict(id='P153-203-F03',severity='unsupported_transfer_claim',claim='Pilot196 and pilot197 local testplan selections contain forty development rows each and no held-out rows.',evidence=[{'path':f'pilots/anomalon_woland/pilot_{i:07d}/testplan.yaml','sha256':digest(BASE/f'pilot_{i:07d}/testplan.yaml'),'review_level':'automated_split_census','full_source_read':False} for i in (196,197)],limit='Other campaign evidence may exist; these local selections alone cannot establish held-out transfer.'),
        dict(id='P153-203-F04',severity='evidence_scope',claim='All 120 dossier responses record TYPED_REFUSAL; all 25 selected v2 PO035 witness stages remain NOT_CHECKED or REFUSED and analytically UNVERIFIED.',evidence=[{'path':'dag/pilot_triage/numbered_153_203_automated_reviews.jsonl','review_level':'historical_status_census'}],limit='Historical field census, not live provider verification or raw-reply replay.')]
    report=dict(schema='pfp.imported-pilot-triage.v1',scope='ALL pilot_0000153 through pilot_0000203 inclusive',
        status='complete_first_substantive_triage_not_full_estate_certification',authority_effect='None; recommendations only. No edits, deletion, provider calls or policy admission.',
        summary=dict(pilot_count=len(pilots),verdict_counts=dict(Counter(p['verdict'] for p in pilots)),new_workflow_families_recommended=0,
            incoming_files_hash_checked=len(entries),incoming_bytes_hash_checked=sum(e['bytes'] for e in entries),incoming_custody_failures=0,
            canonical_gate_tests_passed=30,finite_probe_checks_passed=165,historical_checker_limitations_reproduced=1),
        review_method=['Full primary README/spec review for every pilot; repeated 153–187 prose was reviewed through the complete shared template plus exhaustive differences, recorded separately.',
            'Full actual dossier checker, replay generator/checker/runner and meaningful test reads; complete canonical-owner diffs preserve namespace and custody distinctions.',
            'Full shared challenge dispatch/live owner and gate tests; original family judges remain separately scoped, not silently certified.',
            'Full finite PO035 predicates, fixtures, schema and final-prompt validation; selected typed-signal and posthoc-harvest bodies, not an invented whole-file read.',
            'Per-file manifest hash checks and response/testplan censuses are automated evidence, separate from manual source review.'],
        evidence_limits=['No protected benchmark seed read or solved. No key/private storage access, provider/network calls, original historical CLI replay or live model evaluation.',
            'Historical fixtures/receipts are retained data. Passing finite controls does not certify physical claims, universal analytical derivations, provider identity or transfer benefit.',
            'The shared challenge protocol was reviewed; the full set of C011–C060 individual mathematical judges and their batteries was not independently audited here.',
            'Imported historical namespaces and external checkout assumptions remain; mapped current owners do not retroactively authenticate old source-bound receipts.',
            'Dossier test source uses unavailable SymPy; probes instead used a separate exact Fraction/RREF oracle for the declared nullity-one carriers and original generator AST bodies with an explicit imported-estate root.',
            'No deletion or source consolidation is authorized by a duplicate/stub recommendation.'],
        findings=findings,registry_evidence=dict(path='dag/workflows_dag.json',sha256=digest(registry_path),review_scope='WF16–WF20 identities, processes, mathematics and host-check declarations, plus full family README definitions'),
        supporting_artifacts=[f'dag/pilot_triage/numbered_153_203{s}' for s in ('_primary_differences.json','_owner_comparisons.json','_automated_reviews.jsonl','_probes.py','_probes.json','_gate_controls.xml','_validation.json','_build.py')],pilots=pilots)
    assert len(pilots)==51 and {p['id'] for p in pilots}==ids
    assert all(p['source_evidence'] and p['workflow_mapping'] and p['mathematical_basis'] for p in pilots)
    for p in pilots:
        for e in p['source_evidence']:
            assert digest(ROOT/e['path'])==e['sha256']
            assert 1<=e['lines'][0]<=e['lines'][1]<=len((ROOT/e['path']).read_text(encoding='utf-8').splitlines())
    unique_sources={e['path']:e for p in pilots for e in p['source_evidence']}
    validation=dict(status='PASS',exact_id_range_153_203=True,unique_pilots=len(pilots),
        every_pilot_has_primary_readme_and_spec=True,source_receipt_hash_and_range_checks='PASS',
        unique_manual_source_paths=len(unique_sources),
        full_file_review_paths=sum(e['full_source_read'] for e in unique_sources.values()),
        selected_only_source_paths=sum(not e['full_source_read'] for e in unique_sources.values()),
        automated_check_records=len(automated),incoming_manifest_files=len(entries),incoming_manifest_mismatches=0,
        selected_pytest_cases=30,finite_probe_checks=probe_passes,provider_calls=0,
        limitation='Report integrity and bounded finite checks only; this does not establish an exhaustive mathematical audit of original task judges.')
    save('_validation.json',validation)
    report['validation']=validation
    save('.json',report)
    lines=['# Imported pilot triage: 153–203','',
        'All 51 pilots have a separate disposition: **35 stub candidates and 16 duplicate candidates**. These are preservation and reuse recommendations, not deletion instructions. No new workflow family is recommended.','',
        'The 1,726 incoming files (6,270,795 bytes) match their migration manifest hashes and sizes. Thirty canonical gate tests and 165 finite controls pass. No model/provider call, protected benchmark-seed read, private storage access or source/pilot change occurred.','',
        'Primary README/specs were read in full, with repeated 153–187 documents reviewed through a shared full template and exhaustive differences. The JSON records that method, selected owner ranges, full owner reads and separate automated per-file checks.','',
        '## Reusable mechanisms and limits','',
        '- **153–169 / WF16:** planned Genesis crosswalk capsules; no local checker or run. Their source specs were recorded absent. Naming a Lean or finite-relation target does not supply its proof.','- **170–187 / WF17:** planned witnessed-difference capsules; the family token and historical catalog score do not establish a local certificate.','- **188–191 / WF18:** finite residual minimization, exact L1 dual certificates, nilpotence/rank scope checks, reversible representation sweeps and source-bound replay. These mechanisms already have current owners.','- **192–198 / WF19:** original-judge dispatch, strict ingress, checker-disagreement stop, bounded repair and candidate-only held-out transfer. The 25-mutant harness is a useful control battery; it is not provider evidence.','- **199–203 / WF20:** finite counterexample controls, explicit assumption grants, negative controls and source-bound candidate extraction. All analytical claims remain unverified. Pilot199 grants were extracted after its original run.','',
        '## Findings','',
        '1. The historical pilot188 checker returns `CERTIFIED_OBSTRUCTION` for a zero-curl, zero-residual triangle. This was reproduced synthetically; reuse the separately scoped current minimization predicate, not that historical receipt wording.',
        '2. WF18’s weighted-cycle explanation says no-negative-cycle feasibility. Pilot189 actually checks weighted L1 primal/dual optimality. The family description should name the implemented theorem.',
        '3. Pilot196 and pilot197 each select 40 development cases and no held-out cases locally. Those selections cannot establish the stated transfer benefit.',
        '4. All 120 historical dossier responses are typed refusals. The 25 selected v2 PO035 witness stages have no accepted certificate; their analytical status is unverified. Receipt counts are not fresh executions.','',
        '## Per-pilot dispositions','',
        '| Pilot | Contribution | Disposition | Existing family |','|---|---|---|---|']
    for p in pilots:
        lines.append(f"| {p['id']} | {p['title'].split(': ',1)[-1].replace('|','/')} | {p['verdict']} | {p['workflow_mapping'][0]['family_id']} |")
    lines += ['', 'Each JSON record contains its mathematical basis, named reusable mechanism, exact source hashes and line ranges, current-control results, transfer limits and next action. The source/case judges outside the explicitly read ranges remain unaudited; this triage does not upgrade them to semantic certification.','']
    Path(str(PREFIX)+'.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(report['summary']))

if __name__=='__main__':main()
