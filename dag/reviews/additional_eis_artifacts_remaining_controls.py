"""Independent finite/data controls. Never imports or executes retained programs."""
from pathlib import Path
import ast, collections, hashlib, json, math, re
from fractions import Fraction
import yaml

ROOT = Path(__file__).resolve().parents[2]
PREFIX = ROOT / 'dag/reviews/additional_eis_artifacts_remaining'
def sha(b): return hashlib.sha256(b).hexdigest()
scope_bytes = Path(str(PREFIX) + '_scope.json').read_bytes()
assert sha(scope_bytes) == '57383045b5b17029d822a586201987b6ada589d0e8a82138efdf1d0fd44ffa60'
rows = json.loads(scope_bytes)['files']
objects, raw = {}, {}
for i, row in enumerate(rows):
    b = (ROOT / row['path']).read_bytes()
    assert sha(b) == row['sha256']
    raw[i] = b
    objects[i] = json.loads(b) if row['path'].endswith('.json') else yaml.safe_load(b)

controls = []
def record(ident, question, result, indices, ceiling):
    controls.append({'id': ident, 'question': question, 'result': result,
                     'sources': [{'path': rows[i]['path'], 'sha256': rows[i]['sha256']} for i in indices],
                     'ceiling': ceiling, 'execution': 'fresh standalone Python metadata/arithmetic; no repository imports or runners'})

fixture_checks = []
for i in range(58):
    o = objects[i]
    pattern = o.get('target_pattern')
    if not pattern or 'negative_fixture' not in o or 'positive_fixture' not in o: continue
    assert len(pattern) < 1500 and max(len(o['negative_fixture']), len(o['positive_fixture'])) < 10000
    outcomes = {}
    for name, flags in [('default', 0), ('IGNORECASE_DOTALL', re.IGNORECASE | re.DOTALL)]:
        try:
            p = re.compile(pattern, flags)
            outcomes[name] = {'bad_hit': bool(p.search(o['negative_fixture'])), 'good_hit': bool(p.search(o['positive_fixture']))}
        except re.error as exc:
            outcomes[name] = {'compile_error': str(exc)}
    fixture_checks.append({'index': i, 'path': rows[i]['path'], 'outcomes': outcomes})
fixture_summary = {flag: dict(collections.Counter(
    'compile_error' if 'compile_error' in r['outcomes'][flag] else
    ('bad_hit=' + str(r['outcomes'][flag]['bad_hit']) + ',good_hit=' + str(r['outcomes'][flag]['good_hit']))
    for r in fixture_checks)) for flag in ('default', 'IGNORECASE_DOTALL')}
record('EA-T01', 'Do the 58 fully read root JSON target patterns distinguish their supplied bad/good strings?',
       {'population': len(fixture_checks), 'summary': fixture_summary, 'rows': fixture_checks}, list(range(58)),
       'Python re only with two explicitly declared flag profiles. These are lexical fixture checks, not production guard activation, semantic truth or detector efficacy.')

zero_cochain = {(0,1): Fraction(0), (1,2): Fraction(0), (2,0): Fraction(0)}
for (a,b), v in list(zero_cochain.items()): zero_cochain[b,a] = -v
assert all(zero_cochain[a,b] == -zero_cochain[b,a] for a,b in zero_cochain)
circulation = sum(zero_cochain[a,b] for a,b in [(0,1),(1,2),(2,0)])
record('EA-T02', 'Does antisymmetry alone force a strictly positive triangle circulation?',
       {'cochain': [[a,b,str(v)] for (a,b),v in zero_cochain.items()], 'circulation': str(circulation), 'positive': circulation > 0}, [1,59],
       'Counterexample to entailment from the displayed invariant alone, not disproof of the original pilot value under additional data.')
record('EA-T03', 'Does d squared zero alone force the declared positive spectral floor?',
       {'chain_groups': 'Q in degrees 0,1,2', 'd0': [[0]], 'd1': [[0]], 'd1_d0': [[0]], 'degree1_laplacian': [[0]], 'least_eigenvalue': 0, 'claimed_lower_bound': '31/800'}, [17,67],
       'Exact zero-map finite complex; no additional acyclicity/coercivity assumptions. Not a spectral computation on the historical pilot complex.')
def grid_polynomial(x): return math.prod(x-j for j in range(5))
assert all(grid_polynomial(x) == 0 for x in range(5)) and grid_polynomial(5) == 120
record('EA-T04', 'Does evaluation on a five-point-per-coordinate grid establish a polynomial identity without degree bounds?',
       {'polynomial': 'P(x,y,z,w)=x(x-1)(x-2)(x-3)(x-4)', 'grid': '{0,1,2,3,4}^4', 'grid_points': 625, 'all_grid_values_zero': all(grid_polynomial(x)==0 for x in range(5)), 'P_at_5_0_0_0': grid_polynomial(5)}, [34,80],
       'Shows need for degree/ideal certificates. It does not refute a separately supplied Positivstellensatz identity, which these declarations do not contain.')
carrier = set(range(8)); base = set(); extras = {0,2,4}
record('EA-T05', 'Can extra equations make a genuinely empty base solution set nonempty?',
       {'finite_carrier': sorted(carrier), 'base_solutions': sorted(base), 'extra_solutions': sorted(extras), 'intersection': sorted(base & extras)}, [42,81],
       'Elementary intersection control: if the premise is established, emptiness is preserved. The historical base emptiness is not verified here.')

specs = {objects[i]['spec_id']: objects[i] for i in (135,137,139)}
def predicate(spec, subject):
    results = []
    for a in spec['predicate']['atoms']:
        f = a['fields']
        if a['operator'] == 'VALUE_IN': result = subject[f[0]] in a['values']
        elif a['operator'] == 'EQUAL_FIELDS': result = subject[f[0]] == subject[f[1]]
        elif a['operator'] == 'NOT_SUBSET_FIELDS': result = not set(subject[f[0]]).issubset(subject[f[1]])
        else: raise ValueError(a['operator'])
        results.append(result)
    assert spec['predicate']['mode'] == 'ALL'
    return all(results)
truth_cases = []
for case in objects[133]['cases']:
    got = predicate(specs[case['spec_id']], case['subject'])
    assert got == case['expected_hit']
    truth_cases.append({'case_id': case['case_id'], 'observed': got, 'expected': case['expected_hit']})
overclaim = dict(objects[133]['cases'][1]['subject']); overclaim['claim_mode'] = 'BOUNDED'
self_claim = dict(objects[133]['cases'][3]['subject']); self_claim['claim_mode'] = 'BOUNDED'
approved = dict(objects[133]['cases'][5]['subject']); approved['approval_reference'] = 'independent-approved-event-placeholder'
record('EA-T06', 'What do the three v2 finite predicates actually evaluate?',
       {'six_cases': truth_cases, 'bounded_scope_mismatch_hit': predicate(specs['truth-bounded-as-unrestricted'],overclaim), 'same_identity_bounded_mode_hit': predicate(specs['truth-model-self-certification'],self_claim), 'proposal_merge_with_nonempty_approval_reference_hit': predicate(specs['truth-proposal-authority-collapse'],approved)}, [133,135,137,139],
       'Independent interpreter of the displayed ALL atoms on admitted fixture shapes; no host implementation reproduction or semantic claim-scope/identity/approval authentication.')

digest_shapes = []
for i in list(range(58)) + [96,97]:
    for key, value in objects[i].items():
        if key == 'evidence_sha256' and isinstance(value,str):
            if not re.fullmatch('[0-9a-f]{64}',value): digest_shapes.append({'index': i, 'field': key, 'value': value, 'length': len(value)})
record('EA-T07','Do reviewed root evidence_sha256 fields all have raw SHA-256 hex shape?', digest_shapes, list(range(58))+[96,97],
       'Shape only: a 64-hex string does not establish any binding or authenticity; unusual lengths are not a claim of fabrication.')

native_values = set(objects[101]['native_class_codes'].values())
native_disagreements = [{'class': k,'declared_is_native': v['is_native'],'present_in_native_codes': k in native_values} for k,v in objects[100]['failure_classes'].items() if v['is_native'] != (k in native_values)]
record('EA-T08','Do native flags agree with the adjacent native mapping declaration?', native_disagreements,[100,101],
       'Cross-declaration consistency only; runtime behavior remains governed by separately reviewed owners.')

def walk(value, path='$'):
    if isinstance(value,dict):
        yield path,value
        for k,v in value.items(): yield from walk(v,path+'.'+k)
    elif isinstance(value,list):
        for n,v in enumerate(value): yield from walk(v,path+f'[{n}]')
output_hashes = []
for path,o in walk(objects[144]):
    if 'output_utf8' in o and 'output_sha256' in o:
        text=o['output_utf8']; profiles = {'utf8':sha(text.encode()),'LF':sha(text.replace('\r\n','\n').replace('\r','\n').encode()),'CRLF':sha(text.replace('\r\n','\n').replace('\r','\n').replace('\n','\r\n').encode())}
        output_hashes.append({'json_path': path,'expected':o['output_sha256'],'profiles':profiles,'exact_match': profiles['utf8']==o['output_sha256'],'bytes':len(text.encode())})
qa_links = []
for qi,vi in [(141,142),(143,144)]:
    text=raw[qi].decode(); obj=objects[qi]
    profiles={'raw':sha(raw[qi]),'LF':sha(text.replace('\r\n','\n').replace('\r','\n').encode()),'CRLF':sha(text.replace('\r\n','\n').replace('\r','\n').replace('\n','\r\n').encode())}
    qa_links.append({'qa_path':rows[qi]['path'],'validation_path':rows[vi]['path'],'expected':objects[vi]['qa_receipt_sha256'],'profiles':profiles,'matched_profiles':[k for k,v in profiles.items() if v==objects[vi]['qa_receipt_sha256']]})
record('EA-T09','Which retained output and QA links match exact current-byte profiles?',
       {'output_pairs':len(output_hashes),'exact_output_matches':sum(x['exact_match'] for x in output_hashes),'exact_output_mismatches':sum(not x['exact_match'] for x in output_hashes),'output_rows':output_hashes,'qa_links':qa_links},[141,142,143,144],
       'Reconciles prior EPR13. No historical raw archive or normalization ledger available; profile mismatch is not proof of a false original execution, and speculative profiles are not an authoritative canonicalization contract.')

historical = {}
for i in (141,142,143,144):
    o=objects[i]; item={'status':o['status']}
    if 'records' in o:
        key='exit_code' if i==142 else 'exit_status'
        item['records']=len(o['records']);item['record_exit_counts']=dict(collections.Counter(x[key] for x in o['records']))
        item['retained_obligations']=len(o['retained_obligations'])
        item['mutation_digest_restoration']=[{'id':x.get('id',x.get('mutant_id')),'same_before_restored':x.get('before_sha256',x.get('digest_before'))==x.get('restored_sha256',x.get('digest_restored')),'different_mutated':x.get('before_sha256',x.get('digest_before'))!=x.get('mutated_sha256',x.get('digest_mutated'))} for x in o['mutations']]
    else:
        item['red_green_transitions']=[{'id':x['mutant_id'],'same_before_restored':x['digest_before']==x['digest_restored'],'different_mutated':x['digest_before']!=x['digest_mutated'],'booleans':[x['baseline_passed'],x['mutated_failed'],x['restored_passed']]} for x in o['red_green_transitions']]
    historical[str(i)]=item
o=objects[145]
historical['145']={'count':len(o),'all_mutant_nonzero':all(x['mutant_exit']!=0 for x in o),'all_restored_zero':all(x['restored_exit']==0 for x in o),'all_detected_true':all(x['detected'] for x in o),'attribute_error_mutants':[x['id'] for x in o if any('AttributeError' in line for line in x['mutant_tail'])]}
record('EA-T10','Are stored status/count/restoration/mutation declarations internally consistent?', historical,[141,142,143,144,145],
       'Fresh accounting of historical claims only; nonzero exit is not necessarily semantic detection, digest equalities do not authenticate execution, and no test or mutation was rerun.')

ast.parse(objects[47]['negative_fixture'])
perm=[1,2,3,4,0]; inversions=sum(perm[i]>perm[j] for i in range(5) for j in range(i+1,5))
record('EA-T11','Recheck prior valid-Python and C5 finite findings without executing source.',
       {'negative_fixture_python_ast_valid':True,'five_cycle':perm,'inversions':inversions,'permutation_sign':(-1)**inversions},[47,102],
       'Reconciles EPR07 and EPR05 rather than introducing duplicate findings. AST parse does not execute the snippet; parity does not validate any physics theorem.')

out={'schema_version':1,'scope_sha256':sha(scope_bytes),'execution_policy':'Read scope only, YAML/JSON parse, Python re on bounded reviewed strings, AST parse and finite arithmetic. No repository imports, source writes, retained program execution, native binaries, providers or network.','controls':controls,'independent_control_count':len(controls),'parse_population':len(objects)}
Path(str(PREFIX)+'_controls.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print(json.dumps({'controls':len(controls),'parsed':len(objects),'regex_summary':fixture_summary,'native_disagreements':native_disagreements,'output_mismatches':sum(not x['exact_match'] for x in output_hashes),'qa_links':qa_links,'historical':historical},indent=2))
