"""Bounded schema-specific data assessment, deliberately no full-source credit."""
import sys,json,re,hashlib,itertools,collections,ast
from fractions import Fraction
sys.dont_write_bytecode=True
import additional_pfp_adapters_audit as a
root=a.ROOT/'pfp/infrastructure/adapters/mssn_research'
def load(p):
    def pairs(xs):
        out={}
        for k,v in xs:
            if k in out:raise ValueError('duplicate key')
            out[k]=v
        return out
    return json.loads(p.read_text(encoding='utf-8-sig'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))
def check(rule,**details):return {'rule':rule,'status':'observed',**details}
registry=load(root/'registry.json');reg={r['level']:r for r in registry['checkers']}
results=[];summary=collections.Counter();mismatches=[]
for row in a.read('_scope.json')['files']:
    if not row['path'].endswith('.json'):continue
    p=a.ROOT/row['path'];assert a.sha(p)==row['sha256'];x=load(p)
    checks=[{'rule':'strict_json_parse','status':'parsed','top_keys':sorted(x),'duplicate_keys':False,'nonfinite_literals':False}]
    assessment=''
    if p.name=='registry.json':
        ns={};exec(compile((root/'pins.py').read_text(),str(root/'pins.py'),'exec'),ns)
        pairs=[]
        for r in x['checkers']:
            assert r['path']==f"checkers/stage_{r['level']:03}.py" and r['fixture_path']==f"fixtures/mss-{r['level']:03}.json"
            pairs.append(a.sha(root/r['path'])==r['sha256'] and a.sha(root/r['fixture_path'])==r['fixture_sha256'])
        checks.append(check('release_and_registry_pins',registry_matches=a.sha(p)==ns['REGISTRY_SHA256'],preamble_matches=a.sha(root/'checkers/preamble.py')==ns['PREAMBLE_SHA256'],levels_exact=[r['level'] for r in x['checkers']]==list(range(101)),checker_fixture_pairs=len(pairs),all_pairs_match=all(pairs),authority=x.get('AuthorityEffect'),grade=x.get('grade')))
        assessment='Release/checker/fixture byte bindings and complete level index checked. Declared row pins and clauses are metadata; no original external stage table or sealed source accessed. A jointly replaceable release pin does not establish external authenticity or theorem correctness.'
    elif p.name=='catalog.json':
        ids=[r['scenario']['scenario_id'] for r in x['scenarios']];links=[];bad_links=[]
        for r in x['scenarios']:
            target=(root/r['fixture_path']).resolve();assert target.is_relative_to((root/'fixtures').resolve())
            actual=a.sha(target);links.append(actual==r['fixture_sha256'])
            if actual!=r['fixture_sha256']:bad_links.append({'scenario_id':r['scenario']['scenario_id'],'fixture_path':r['fixture_path'],'declared_sha256':r['fixture_sha256'],'actual_sha256':actual})
        checks.append(check('catalog_fixture_bindings',scenarios=len(ids),unique_ids=len(set(ids)),all_fixture_hashes_match=all(links),mismatches=bad_links,registered_challenges=x['registered_challenges'],implementation_path_counts={k:len(v) for k,v in x['implementation'].items()}))
        assessment='Parsed catalog references, scenario ids and all fixture digests. One cohomology fixture digest is stale; exact mismatch is retained in checks. Implementation paths and challenge registration are inventory declarations, not proof that native kernels ran, mathematical coverage is complete, or scenario labels are correct.'
    elif re.fullmatch(r'mss-\d{3}\.json',p.name):
        n=int(p.stem[4:]);r=reg[n];ns={'__name__':'audit_fixture_'+str(n)}
        for sp in (root/'checkers/preamble.py',root/r['path']):exec(compile(sp.read_text(encoding='utf8'),str(sp),'exec'),ns)
        assert x['level']==n and ns['STAGE']==n
        ids=[];outcomes=[]
        for c in x['cases']:
            ids.append(c['id']);got=list(ns['check'](c['payload']));match=got==c['expected'];outcomes.append({'case_id':c['id'],'expected':c['expected'],'actual':got,'matches':match})
            summary['stage_cases']+=1
            if not match:mismatches.append({'path':row['path'],'case_id':c['id'],'actual':got,'expected':c['expected']})
        checks.append(check('stage_fixture_shape_and_pin',level=n,cases=len(ids),unique_case_ids=len(set(ids)),fixture_pin_matches=a.sha(p)==r['fixture_sha256'],checker_pin_matches=a.sha(root/r['path'])==r['sha256'],clauses_match=[list(c) for c in ns['CLAUSES']]==r['clauses'],row_binding_matches=ns['ROW_SHA256']==r['row_sha256']))
        checks.append(check('retained_case_replay',all_match=all(z['matches'] for z in outcomes),outcomes=outcomes))
        assessment='Parsed every retained case and replayed its payload through the unchanged already-read Python checker plus preamble, isolated from unavailable package imports. Agreement is regression consistency with supplied expected labels, not independent mathematical validation. Separate authored countercontrols and source assessments constrain each checker claim.'
    elif 'cases' in x:
        cs=x['cases'];ids=[c.get('id',c.get('case_id')) for c in cs]
        checks.append(check('case_collection',count=len(cs),unique_ids=len(set(ids)),case_key_variants=[list(z) for z in sorted({tuple(sorted(c)) for c in cs})]))
        if p.name=='demo_q40_quantum_solver.json':
            controls=[c for c in cs if c['is_control']];base={c['case_id'] for c in cs if not c['is_control']}
            checks.append(check('pauli_shapes_and_control_references',declared_total_matches=x['total_cases']==len(cs),declared_base_matches=x['base_cases_count']==len(base),declared_controls_matches=x['controls_count']==len(controls),control_links_resolve=all(c['base_case_id'] in base for c in controls),terms_valid=all(type(c['num_qubits']) is int and c['num_qubits']>0 and all(len(t['pauli'])==c['num_qubits'] and set(t['pauli'])<=set('IXYZ') and t['target_sign'] in (-1,1) and Fraction(t['weight'])>=0 for t in c['terms']) for c in cs)))
            assessment='Parsed 40 Pauli-term fixtures and structural control links. No Hamiltonian optimization, frustration lower bound, native result or physics claim was recomputed.'
        elif x.get('kind')=='sign-gauge':
            checks.append(check('independent_finite_diagonal_gauge',cases=[{'id':c['id'],'declared':c['expected'],'exists_nonpositive_offdiagonal_gauge':any(all(g[i]*g[j]*Fraction(c['matrix'][i][j])<=0 for i in range(len(g)) for j in range(i)) for g in itertools.product((-1,1),repeat=len(c['matrix'])))} for c in cs]))
            assessment='Parsed symmetric rational matrices and independently exhausted all diagonal +/-1 gauges in the fixed basis. This bounded gauge criterion does not certify arbitrary basis changes, QMC algorithms or a general sign-problem solution.'
        elif x.get('kind')=='cohomology':
            checks.append(check('cohomology_case_index',challenge_counts=dict(collections.Counter(c['challenge'] for c in cs)),declared_controls=[c['case_id'] for c in cs if '_ctrl_' in c['case_id']]))
            assessment='Parsed heterogeneous C011-C020 payload and control schema variants. Values/claim labels remain producer-supplied; no native cohomology, SNF, Hodge, persistence or spectral-sequence calculation invoked. Malformed controls are deliberately retained, not silently repaired.'
        else:
            checks.append(check('graph_case_references',cases=[{'id':c['id'],'vertices_unique':len(c['vertices'])==len(set(c['vertices'])),'edge_endpoints_resolve':all(e[0] in c['vertices'] and e[1] in c['vertices'] for e in c['edges']),'before_after_rows':[len(c['before']),len(c['after'])],'rational_edge_values_parse':all(isinstance(Fraction(e[2]),Fraction) for e in c['edges'])} for c in cs]))
            assessment='Parsed finite graph and before/after fixtures, endpoint references and rational values. Named functional values require the separately pinned native implementation and are not newly computed by this data assessment.'
    elif 'wire_turns' in x:
        turns=x['wire_turns'];lat=x['lattice'];dimension_keys=[k for k in ('lx','ly','lz','lt','l0','l1','l2','l3') if k in lat];dims=[lat[k] for k in dimension_keys];assert dims;product=1
        for d in dims:product*=d
        checks.append(check('meron_wire_fixture_structure',turns=len(turns),turns_sequential=[t['turn'] for t in turns]==list(range(1,len(turns)+1)),wire_fields_strings=all(type(t['input_wire']) is str and type(t['expected_response_wire']) is str for t in turns),dimension_keys=dimension_keys,lattice_site_count_matches=lat.get('sites')==product,declared_results={k:v for k,v in x.items() if k.startswith('expected_')}))
        assessment='Parsed scripted wire exchanges, lattice dimensions and expected result fields. Expected cancellation/partition/linking/neutrality numbers are fixture ground truth, not independent Hamiltonian, cluster, topology or gauge derivations. No native adapter, model or benchmark executed.'
    elif p.name=='demo_genesis_crosswalk.json':
        checks.append(check('crosswalk_byte_pin',source_hash_matches=a.sha(root/'genesis_crosswalk.md')==x['source_sha256'],stage_pin=x['stage_pin'],wording_regexes_compile=all(isinstance(re.compile(s),re.Pattern) for s in x['forbidden_patterns']),patterns=len(x['forbidden_patterns'])))
        assessment='Checked compendium digest and compilability of wording patterns only. Lexical hygiene and anchors cannot validate mathematics or claims about sealed external work; those sources were not followed.'
    elif p.name=='assert_edge.json':
        checks.append(check('assert_edge_fields',move_type=x['move_type'],edge_string=type(x['edge']) is str,rational_parses=isinstance(Fraction(x['value']),Fraction)))
        assessment='Parsed one exact rational asserted edge move. No declared graph is supplied here to establish endpoint existence or cochain consistency.'
    elif p.name=='triangle-descent.json':
        checks.append(check('graph_fixture',vertices=len(x['vertices']),edges=len(x['edges']),endpoints_resolve=all(e[0] in x['vertices'] and e[1] in x['vertices'] for e in x['edges']),rational_values_parse=all(isinstance(Fraction(e[2]),Fraction) for e in x['edges'])))
        assessment='Parsed triangle references and exact edge values. Before/after arrays are supplied demonstration data; no named functional descent or native computation certified.'
    elif x.get('kind')=='immune':
        checks.append(check('immune_fixture_strings',reply_count=len(x.get('replies',[])),immune_reply_count=len(x.get('immune_replies',[])),all_reply_strings=all(type(s) is str for s in x.get('replies',[])+x.get('immune_replies',[]))))
        assessment='Parsed bounded adversarial/control response strings; claims inside these examples are test content, not endorsed scientific findings. No detector efficacy, learning or model outcome inferred.'
    elif x.get('kind')=='meron-benchmark':
        checks.append(check('benchmark_configuration',expected_models=len(x['expected_models']),minimum_validity= str(Fraction(x['min_few_shot_validity'])),prompt_stage=x['prompt_stage']))
        assessment='Parsed expected-model list and threshold configuration only. No model, private benchmark records, credentials, seed/answer or provider was accessed; configuration does not establish benchmark performance.'
    else:
        checks.append(check('declarative_demo_selector',kind=x.get('kind'),scope_present=type(x.get('scope')) is str,illustration_promotable=x.get('data',{}).get('promotable') if isinstance(x.get('data'),dict) else None))
        assessment='Parsed declarative demo kind/scope and optional illustration flags. Selector/description-only artifact provides no execution, theorem, authority or coverage certificate.'
    results.append({'path':row['path'],'sha256':row['sha256'],'full_source_read':False,'reviewed_lines':[],'assessment_kind':'bounded_schema_specific_data_assessment','assessment':assessment,'checks':checks})
a.write('_automated.json',results);a.write('_data_summary.json',{'files':len(results),'stage_cases':summary['stage_cases'],'retained_case_mismatches':mismatches,'limits':'Data parsing/replay is not full source reading or independent mathematical proof.'});a.report()
print(json.dumps({'files':len(results),'stage_cases':summary['stage_cases'],'retained_case_mismatches':mismatches}))
