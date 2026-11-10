"""Keep certificate mathematics, prior replay, artifact custody and usage separate."""
from collections import Counter
from fractions import Fraction as Q
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; REV=ROOT/'dag/reviews'
PREFIX='additional_challenges_051_059_artifacts'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
prior_path=REV/'additional_challenges_051_059.json'
assert sha(prior_path)=='580e0dadca0ce5561f597c1e58b896e0e8adaf24bead64da27c960cb641082ba'
prior=load(prior_path);scope=load(REV/(PREFIX+'_scope.json'));selected=load(REV/(PREFIX+'_selected.json'))
frozen={r['path']:r for r in scope['files']};full={r['path'] for r in selected}
auto={r['path']:(i,r) for i,r in enumerate(prior['automated_reviews'])}
assert set(frozen)==set(auto) and len(auto)==1138 and len(full)==23
for r in prior['file_reviews']:assert sha(ROOT/r['path'])==r['sha256']
for p,r in frozen.items():assert sha(ROOT/p)==r['sha256']==auto[p][1]['sha256']
def public(name):
    paths=[p for p in full if p.endswith('/'+name)];assert len(paths)==1
    return load(ROOT/paths[0])

controls=[]
lp_results=[]
for name,x,y in [('case_11_base_opt_1x1.json',[Q(3)],[Q(4,5)]),
                 ('case_01_base_opt_degen_2d_vertex.json',[Q(2),Q(2)],[Q(2),Q(0),Q(0),Q(0)])]:
    d=public(name);A=[[Q(z) for z in row] for row in d['A']];b=list(map(Q,d['b']));c=list(map(Q,d['c']))
    assert all(z>=0 for z in x+y)
    assert all(sum(a*z for a,z in zip(row,x))<=rhs for row,rhs in zip(A,b))
    assert all(sum(A[i][j]*y[i] for i in range(len(y)))>=c[j] for j in range(len(x)))
    primal=sum(a*z for a,z in zip(c,x));dual=sum(a*z for a,z in zip(b,y));assert primal==dual
    lp_results.append({'case':name,'x':list(map(str,x)),'y':list(map(str,y)),'objective':str(primal)})
controls.append({'id':'CAG-P01','observed':lp_results,'limit':'Exact primal/dual inequalities and weak-duality equality for two supplied LPs; no optimizer completeness claim.'})
flow_case=public('c052_h01_base_layered_4x3.json')
capacity={(u,v):int(c) for u,v,c in flow_case['arcs']};flows=dict.fromkeys(capacity,0)
for route,amount in [([0,1,5,8,11,13],11),([0,2,6,9,12,13],12),([0,3,4,9,10,13],13)]:
    for u,v in zip(route,route[1:]):flows[u,v]+=amount
assert all(0<=flows[e]<=c for e,c in capacity.items())
balance=[sum(f for (u,v),f in flows.items() if v==i)-sum(f for (u,v),f in flows.items() if u==i) for i in range(flow_case['n'])]
assert balance==[-36]+[0]*12+[36]
cut_capacity=sum(c for (u,v),c in capacity.items() if u==0 and v!=0);assert cut_capacity==36
controls.append({'id':'CAG-P02','observed':{'value':36,'flow':[[u,v,f] for (u,v),f in flows.items()],'cut':[0],'cut_capacity':cut_capacity},
 'limit':'Feasible flow and equal cut on the supplied14-vertex graph; no source optimizer or general capacity parser invoked. The separate empty-arc fixture has value0.'})
assert Q(public('c053_h01_base_scaled_identity_1x1.json')['matrix'][0][0])*Q(1,3)==1
assert Q(public('c054_b01_1x1_consistent.json')['A'][0][0])*3==Q(public('c054_b01_1x1_consistent.json')['b'][0])
assert Q(public('c055_b01_1x1.json')['cost'][0][0])==10
controls.append({'id':'CAG-P03','observed':{'inverse_1x1':'1/3','determinant':'3','linear_solution':'3','assignment_value':'10','assignment_dual':['10','0']},
 'limit':'Elementary exact certificates for the three supplied1x1 examples; empty-dimensional input acceptance is a separate contract choice.'})
empty=public('c056_b01_empty_language.json');assert empty['regex']=='#'
words=[w for n in range(7) for w in itertools.product(empty['alphabet'],repeat=n)]
assert len(words)==127
controls.append({'id':'CAG-P04','observed':{'states':1,'accepting_states':[],'transition':'self-loop for each declared letter','finite_word_controls':len(words)},
 'limit':'Under the admitted #=empty-language convention, a one-state rejecting DFA remains rejecting for every word by induction; parser correspondence is not checked here.'})
network=[(0,1),(2,3),(0,2),(1,3),(1,2)]
def apply_network(values):
    values=list(values)
    for i,j in network:values[i],values[j]=min(values[i],values[j]),max(values[i],values[j])
    return values
for values in itertools.product((0,1),repeat=4):assert apply_network(values)==sorted(values)
for values in itertools.permutations(range(4)):assert apply_network(values)==sorted(values)
sort_case=public('c057_case_01.json');assert sort_case=={'case_id':'c057_case_01','n':4,'k':5,'prefix':[],'forbidden':[]}
controls.append({'id':'CAG-P05','observed':{'network':network,'binary_inputs':16,'distinct_rank_permutations':24},
 'limit':'Sorting witness with five comparators; no lower-bound/minimal-length result or synthesis completeness.'})
bit=public('c058_b01_xor_sub.json');assert bit['width']==8 and bit['target_len']==1
for x,y in itertools.product(range(256),repeat=2):assert ((x|y)-(x&y))%256==x^y
controls.append({'id':'CAG-P06','observed':{'input_pairs':65536,'replacement':'xor x y','instructions':1},
 'limit':'Exhaustive equivalence at width8 for the supplied or/and/sub expression; no endorsement of sampled width64 verification.'})
sql=public('c059_b01_where_distinct.json')
def distinct(a,b):
    if a is None or b is None:return (a is None)!=(b is None)
    return a!=b
tables=[[[r['id'],r['f_val']] for r in db['facts'] if distinct(r['g_verdict'],r['l_prod'])] for db in sql['test_databases']]
assert tables==[[[2,None],[4,300],[5,None]],[],[]]
controls.append({'id':'CAG-P07','observed':{'projected_rows_by_database':tables},
 'limit':'Direct NULL-aware integer predicate evaluation on these three finite tables only; no SQL engine, parser or universal query-equivalence claim.'})
nonfinite=[]
for path in full:
    if path.endswith(('mut_41_network_contains_nan.json','mut_42_network_contains_inf.json')):
        found=[];json.loads((ROOT/path).read_text(),parse_constant=lambda s:found.append(s));assert len(found)==1
        nonfinite.append({'path':path,'nonstandard_token':found[0]})
assert {x['nonstandard_token'] for x in nonfinite}=={'NaN','Infinity'}
controls.append({'id':'CAG-P08','observed':nonfinite,'limit':'These two malformed wire-index fixtures contain nonstandard JSON number tokens; Python parser acceptance is not strict JSON validity.'})
ledger=public('case_id_ledger.json');assert len(ledger)==len(set(ledger.values()))==64
base=next(ROOT/p for p in full if p.endswith('/case_id_ledger.json')).parent/'cases'
assert all((base/(v+'.json')).is_file() for v in ledger.values())
controls.append({'id':'CAG-P09','observed':{'distinct_identifier_pairs':64,'target_files_exist':64},
 'limit':'Filename correspondence only; old descriptive identifiers are not independent case truth or a repaired mutation generator.'})
(REV/(PREFIX+'_controls.json')).write_text(json.dumps({'controls':controls,'source_pins':selected},indent=2)+'\n')

notes={
 'case_11_base_opt_1x1.json':'Exact x=3,y=4/5 achieves matching primal/dual value12 under x>=0 and5x<=15.',
 'case_01_base_opt_degen_2d_vertex.json':'Exact x=(2,2),y=(2,0,0,0) is feasible on both sides and has equal objective8; weak duality certifies this optimum.',
 'c052_h64_poison_empty_arcs_with_unreachable.json':'The well-formed three-vertex empty-arc graph has zero flow and zero cut capacity. The filename poison does not establish invalid input.',
 'c052_h01_base_layered_4x3.json':'All33 directed arcs read. Three explicit path flows carry36 with checked capacity/conservation; source cut{0} also has capacity36. This is an exact optimum certificate.',
 'c053_h55_poison_empty_matrix.json':'Empty matrix body read. A0x0 identity/inverse/determinant convention is mathematically possible but task admission is separate; filename poison is not a proof of rejection.',
 'c053_h01_base_scaled_identity_1x1.json':'The1x1 matrix[3] has exact inverse[1/3] and determinant3. No general Bareiss theorem inferred.',
 'c054_b31_edge_empty_0x0.json':'Empty A,b encode a0x0 system under the declared convention; its empty vector satisfies all zero equations. Contract and rank-certificate behavior remain family-scoped.',
 'c054_b01_1x1_consistent.json':'3x=9 has unique rational solution3, rank1 and no nonzero homogeneous solution.',
 'c055_p08_empty_cost_list.json':'Empty assignment-cost list; empty matching/zero objective is a possible carrier convention, not proof that this task admits it.',
 'c055_b01_1x1.json':'Unique one-edge assignment has cost10; row potential10,column potential0 matches the primal and dual objectives.',
 'c056_p10_missing_alphabet_key.json':'MINIMIZE request omits its declared alphabet, so language/parser admission is incomplete regardless of the regex text.',
 'c056_b01_empty_language.json':'Under the explicit #=empty-language syntax premise, one rejecting state with both self-loops recognizes the empty language and is minimal among nonempty state carriers.',
 'c057_case_01.json':'Unconstrained four-wire, five-comparator request has the explicit network recorded in controls; all16 binary inputs and24 distinct-rank permutations sort correctly. No minimality claim.',
 'c058_p15_ops_not_list.json':'The operations field is a string instead of the required structured list; this is malformed IR, not a superoptimization challenge.',
 'c058_b01_xor_sub.json':'At width8, (x OR y)-(x AND y) equals x XOR y on all65,536 input pairs. The one-operation replacement meets target_len1 for this input.',
 'c059_p09_empty_schema.json':'Entire public case and three database bodies read. Empty schema cannot type the named users relation/protected id; populated database examples do not supply an explicit schema contract.',
 'c059_b01_where_distinct.json':'Entire schema/spec and three databases read. Explicit NULL-aware comparison yields projected rows(2,NULL),(4,300),(5,NULL) only in the first database. Finite evaluation does not prove universal SQL translation.',
 'case_id_ledger.json':'All64 historical descriptive-to-anonymous ID pairs read; targets are distinct and all current files exist. Mapping does not authenticate mathematical labels or repair stale generator filenames.',
 'mut_41_network_contains_nan.json':'Complete attack envelope read: NaN in a comparator wire index is both a nonstandard JSON token and a noninteger wire. Stored rejection text remains historical.',
 'mut_42_network_contains_inf.json':'Complete attack envelope read: Infinity in a comparator wire index is both a nonstandard JSON token and a noninteger wire. Stored rejection text remains historical.',
}
family={c['id'].split('-')[0].replace('AC','C0'):c for c in prior['claims']}
rows=[];rules=Counter();strict_bad=[]
for path,item in frozen.items():
    idx,record=auto[path]
    check=next(c for c in record['checks'] if c['rule'] not in ('json_structure','strict_json_domain'))
    strict=next(c for c in record['checks'] if c['rule']=='strict_json_domain')
    if not strict['rfc8259_number_domain']:strict_bad.append(path)
    rule=check['rule'];rules[rule]+=1;claim=family[path.split('/')[3][:4].upper()]
    if path in full:
        if path.endswith('accounting.json'):
            note='Full accounting/configuration body read. Declared USD0.50/1.00 per-arm caps and model names are historical settings, not current USD0.10 whole-run enforcement. '
            if '/c057_' in path:note+='Three aggregate run rows claim6/10,4/10,4/10 successes,34,515/6,715/6,746 tokens and0.92/0.61/0.47s mean latency. No per-call cost, outputs, timing traces or provider authentication are supplied by this file.'
            else:note+='This file contains no measured successful-run evidence.'
        else:note=notes[Path(path).name]
    elif rule=='mutation_or_case_envelope':
        note='Prior exact-byte mutation replay retained with primary/secondary results and strict JSON-domain status. Both judges rejected this stored attack in the bounded suite; this does not erase the documented counterexamples or prove universal detector adequacy.'
    elif rule=='public_case_expected_output':
        note='Prior retained expected-output and separately generated reference replays retained. Both-route acceptance is conditional on the family semantics and may include refusal; synthetic/reference outputs are not authenticated model trials.'
    elif rule=='problem_case_replay':
        note='Prior owner/reference replay and its explicitly bounded independent equations/evaluation retained for this exact input. The family claim '+claim['id']+' and documented input/coercion/soundness defects limit what acceptance establishes.'
    else:raise AssertionError((path,rule))
    rows.append({'path':path,'sha256':item['sha256'],'full_source_read':path in full,
      'reviewed_lines':[[1,len((ROOT/path).read_text(encoding='utf-8').splitlines())]] if path in full else [],
      'review_level':'full_artifact_body_with_context' if path in full else 'bounded_prior_record_with_family_limits',
      'assessment':note,'checker_limit_reference':claim['id'],
      'detail_receipt':{'path':prior_path.relative_to(ROOT).as_posix(),'sha256':sha(prior_path),'json_pointer':'/automated_reviews/'+str(idx),'prior_rule':rule,'strict_json_number_domain':strict['rfc8259_number_domain']}})
assert len(strict_bad)==2
evidence=[{'path':r['path'],'sha256':r['sha256']} for r in selected if Path(r['path']).name in ['case_11_base_opt_1x1.json','case_01_base_opt_degen_2d_vertex.json','c052_h01_base_layered_4x3.json','c057_case_01.json','c058_b01_xor_sub.json']]
report={'schema_version':'1.0','status':'complete_declared_bounded_artifact_dispositions_with_source_reading_limits','source_commit':scope['source_commit'],
 'scope_manifest':'dag/reviews/'+PREFIX+'_scope.json','counts':{'scope':1138,'full_body_readings':23,'bounded_prior_record_dispositions':1115,'pending_dispositions':0},
 'file_reviews':rows,'pending_paths':[],'source_body_reads_not_completed':[r['path'] for r in rows if not r['full_source_read']],
 'family_checker_limits':{k:{'prior_claim_id':v['id'],'statement':v.get('claim',v.get('statement')),'limitations':v.get('limitations',v.get('limits'))} for k,v in family.items()},
 'claims':[{'id':'CAG-C01','statement':'Selected exact certificates establish LP objectives12 and8 and max-flow value36; a five-comparator network sorts the supplied four-wire task, and the width8 OR/AND/sub expression equals XOR on all65,536 inputs. These finite checks support reusable certificate mechanisms, with no claim of generator completeness or empirical workflow advantage.',
  'source_evidence':evidence,'validation':'dag/reviews/'+PREFIX+'_controls.json'}],'findings':[],
 'limits':['23 complete bodies and1115 bounded contextual dispositions are distinct;102 previously full-read owning sources were hash-checked without execution.',
           'All9 prior claim summaries and36 finding statements consulted; detailed nested diagnostics were not all manually reread.',
           'Prior432 stored-mutant replays rejected by both routes are bounded evidence; accepted adversarial counterexamples in the prior findings remain unresolved.',
           '49 excluded previously reviewed owning files remain under their earlier reports, not duplicate new reading credit.',
           'No original source edits, native/provider execution, external database use or private benchmark access.']}
(REV/(PREFIX+'.json')).write_text(json.dumps(report,indent=2)+'\n')
(REV/(PREFIX+'_validation.json')).write_text(json.dumps({'status':'custody_and_bounded_controls_pass',**report['counts'],'owner_source_pins':102,'controls':9,
 'prior_check_rule_counts':dict(rules),'nonstandard_json_files':strict_bad,'report_sha256':sha(REV/(PREFIX+'.json')),'prior_report_sha256':sha(prior_path),
 'limits':'Pin checks and selected exact arithmetic only; no broad source-soundness or empirical benchmark certification.'},indent=2)+'\n')
(REV/(PREFIX+'.md')).write_text('# C051-C059 artifact reconciliation\n\n'
 'All1,138 artifacts have explicit dispositions:23 complete body readings and1,115 bounded prior-record assessments. The102 earlier owner readings are separately pinned;49 older reviewed sources retain their own attribution.\n\n'
 'Useful mechanisms include exact primal/dual LP equality, a feasible flow with equal cut, inverse/kernel identities and finite exhaustive bit-vector checks. Selected controls establish LP objectives12/8, flow36 and width8 XOR equivalence. These results are distinct from optimizer completeness, claimed model usage and broad workflow efficacy.\n\n'
 'The three accounting files retain historical per-arm budgets and aggregate run declarations. They are not provider-authenticated measurements. Two hostile fixtures contain literalNaN/Infinity and are explicitly outside strict JSON. No paid/native/provider run was made.\n',encoding='utf-8')
m=ROOT/'dag/swarm_manifest.json';manifest=load(m);name='dag/reviews/'+PREFIX+'.json'
if name not in manifest['completed_followup_slices']:manifest['completed_followup_slices'].append(name)
manifest['parent_active_slice']={'status':'selecting_next_scope','completed_report':name,**report['counts']};m.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'counts':report['counts'],'prior_check_rules':dict(rules),'nonstandard_json_files':len(strict_bad),'controls':len(controls)}))
