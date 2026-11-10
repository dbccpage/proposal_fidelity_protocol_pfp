"""Bounded structural/custody review of five historical JSON datasets; no providers."""
import ast
import hashlib
import json
import math
import re
import sys
from collections import Counter, deque
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
PAPER = ROOT / 'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence'
HIST = PAPER / 'docs/history_recovery'
def sha(b): return hashlib.sha256(b).hexdigest()
def obj(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def read(name): return json.loads((HIST/name).read_text(encoding='utf-8'))
def local(rel, base=PAPER):
    p=(base/rel).resolve()
    assert p.is_relative_to(ROOT.resolve()) and p.is_file(), rel
    return p
def binding(rel, expected, base=PAPER):
    p=local(rel,base); b=p.read_bytes(); lf=b.replace(b'\r\n',b'\n')
    return {'path':p.relative_to(ROOT).as_posix(),'expected_sha256':expected,'current_sha256':sha(b),
            'raw_match':sha(b)==expected,'lf_match':sha(lf)==expected,'raw_bytes':len(b),'lf_bytes':len(lf)}
def ids(rows):
    got=[x['challenge_id'] for x in rows]
    assert sorted(got)==[f'G{i:02d}' for i in range(1,26)]
    return got

out={'scope':'Bounded validation of all declared rows and byte bindings. Not full nested proof/source review, external Git lookup or provider billing replay.',
     'python_version':sys.version,'external_repository_accesses':0,'provider_calls':0,'source_mutations':0}
manifest=read('recovery_manifest.json')
assert manifest['file_count']==len(manifest['entries'])==28
assert sum(x['byte_count'] for x in manifest['entries'])==manifest['total_bytes']==324333
assert len({x['recovered_relative_path'] for x in manifest['entries']})==28
bindings=[]
for x in manifest['entries']:
    r=binding(x['recovered_relative_path'],x['sha256']); b=local(x['recovered_relative_path']).read_bytes()
    r.update(git_blob_raw_match=obj(b)==x['git_blob'],git_blob_lf_match=obj(b.replace(b'\r\n',b'\n'))==x['git_blob'],
             recorded_bytes=x['byte_count'],declared_source_commit_matches=x['source_commit']==manifest['source_commit'])
    bindings.append(r)
out['recovery_manifest']={'rows':28,'bindings':bindings,'raw_matches':sum(x['raw_match'] for x in bindings),
                          'lf_matches':sum(x['lf_match'] for x in bindings),'git_lf_matches':sum(x['git_blob_lf_match'] for x in bindings)}

master=read('recovered_sources/results/genesis_master_report.json'); rows=master['results']; ids(rows)
assert master['total_challenges']==len(rows)==master['budget_summary']['total_calls']==25
meta=[x['metadata'] for x in rows]
assert all(type(m[k]) is int and m[k]>=0 for m in meta for k in ['in_tokens','out_tokens'])
assert all(math.isfinite(m[k]) and m[k]>=0 for m in meta for k in ['cost','latency'])
total=sum((Decimal(str(m['cost'])) for m in meta),Decimal(0))
fixed=sum((Decimal(m['in_tokens'])*Decimal('.12')+Decimal(m['out_tokens'])*Decimal('.30') for m in meta),Decimal(0))/Decimal(1000000)
checked=[x for x in rows if x['relation']=='CHECKED']
lean=Counter('absent' if not x['lean_verification']['present'] else 'compiled' if x['lean_verification']['compiles'] else 'timeout' if 'timed out' in str(x['lean_verification'].get('error','')) else 'failed' for x in checked)
out['master_report']={'rows':25,'relations':dict(Counter(x['relation'] for x in rows)),
                      'statuses':dict(Counter(x['status'] for x in rows)), 'checked_lean':dict(lean),
                      'all_artifact_verified':all(x['artifact_verification']['verified'] is True for x in rows),
                      'reported_total':master['total_cost_usd'],'sum_recorded_cost_decimal':str(total),
                      'historical_fixed_tariff_recalculation':str(fixed),'tariff_sum_exact_decimal_matches':total==fixed,
                      'tariff_sum_absolute_difference':str(abs(total-fixed)),
                      'tariff_sum_matches_within_1e_minus_15_usd':abs(total-fixed)<Decimal('1e-15'),
                      'tokens':{k:sum(m[k] for m in meta) for k in ['in_tokens','out_tokens']},
                      'sum_reported_latency_seconds':sum(m['latency'] for m in meta),
                      'raw_response_or_proof_fields_retained':sorted({k for x in rows for k in x if k in {'raw_response','lean_code','proof','provider_response'}}),
                      'limit':'Numerical agreement with the harness tariff is not provider-billed spend or validation of the reported claims.'}

replay=read('genesis_replay.json'); ids(replay['rows']); mr={x['challenge_id']:x for x in rows}
specbindings=[]; sections=[]; controls=[]
for x in replay['rows']:
    old=mr[x['challenge_id']]
    assert old['relation']==x['historical_relation_label'] and old['status']==x['historical_status_label']
    assert old['lean_verification']==x['historical_lean_metadata']
    assert x['mathematical_certificate_replayed'] is False and x['positive_obligation_satisfied'] is False
    specbindings.append(binding(x['spec_path'],x['spec_sha256']))
    lines=local(x['spec_path']).read_text(encoding='utf-8').splitlines()
    for key in ['formal_problem','output_contract','capability_gate']:
        s=x[key]; a=s['start_line']; b=s['end_line']; snippet='\n'.join(lines[a-1:b])
        # Historical record offsets include the heading; text excludes headings/blank margins.
        sections.append({'challenge_id':x['challenge_id'],'section':key,'range_in_bounds':1<=a<=b<=len(lines),
                         'text_present_in_current_source':s['text'] in '\n'.join(lines),
                         'text_present_in_recorded_range':s['text'] in snippet})
    assert len(x['controls'])==3
    for c in x['controls']:
        assert sha(c['actual_input_utf8'].encode())==c['input_sha256']
        assert c['actual_artifact_verifier_output']['verified'] is True and c['incorrect_verification_reproduced'] is True
        controls.append({'challenge_id':x['challenge_id'],'control':c['control'],'input_sha256':c['input_sha256']})
assert len(controls)==replay['artifact_mutations_replayed']==replay['incorrect_artifact_verifications_reproduced']==75
assert dict(Counter(x['relation'] for x in rows))==replay['historical_claim_label_census']
journal=replay['source_journal']; harness=local('docs/history_recovery/recovered_sources/run_genesis_suite.py'); src=harness.read_text(encoding='utf-8')
defs={n.name:n for n in ast.parse(src).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
astbindings=[]
for d in journal['selected_definitions']:
    n=defs[d['name']]
    astbindings.append({'name':d['name'],'range_matches':(n.lineno,n.end_lineno)==(d['start_line'],d['end_line']),
                        'ast_dump_sha256':sha(ast.dump(n,include_attributes=False).encode()),'recorded_ast_sha256':d['ast_sha256']})
out['genesis_replay']={'rows':25,'input_controls_verified':75,'spec_bindings':specbindings,'section_checks':sections,
                       'ast_bindings':astbindings,'all_positive_obligations_still_false':True,
                       'harness_binding':binding('docs/history_recovery/recovered_sources/run_genesis_suite.py',journal['harness_sha256']),
                       'master_binding':binding('docs/history_recovery/recovered_sources/results/genesis_master_report.json',replay['historical_report_sha256']),
                       'manifest_binding':binding('docs/history_recovery/recovery_manifest.json',replay['recovery_manifest_sha256']),
                       'reported_raw_response_retained':replay['historical_raw_response_bytes_retained'],
                       'reported_proof_retained':replay['historical_lean_snippet_bytes_retained']}

avail=read('external_pin_availability.json'); ids(avail['source_specifications']); sr={x['challenge_id']:x for x in avail['source_specifications']}
repos=[]; anchors=[]
for r in avail['repositories']:
    assert len(r['rows'])==r['literal_unique_reference_paths']==len({x['reference_path'] for x in r['rows']})
    pins={x['role']:x for x in r['pins']}; counts=Counter(); statuses=Counter()
    for x in r['rows']:
        assert len(x['at_pins'])==len(pins)
        for p in x['at_pins']:
            assert p['path']==x['reference_path'] and p['commit']==pins[p['pin_role']]['commit']
            statuses[(p['pin_role'],p['status'])]+=1
            if p['status'].startswith('AVAILABLE_'): counts[p['pin_role']]+=1
            if p['kind']=='blob':
                assert re.fullmatch('[0-9a-f]{64}',p['source_file_sha256']) and re.fullmatch('[0-9a-f]{40}',p['object_id'])
                assert type(p['raw_byte_count']) is int and p['raw_byte_count']>=0 and p['raw_git_blob_rehash_matches'] is True
        for s in x['reference_sites']:
            f=sr[s['challenge_id']]; ls=local(f['path']).read_text(encoding='utf-8').splitlines()
            anchors.append({'challenge_id':s['challenge_id'],'literal':s['literal'],'source_line':s['source_line'],
                            'line_contains_literal':1<=s['source_line']<=len(ls) and s['literal'] in ls[s['source_line']-1],
                            'source_digest_agrees_with_spec_row':s['spec_sha256']==f['raw_sha256']})
    assert dict(counts)==r['available_reference_paths_by_pin']
    repos.append({'repository_id':r['repository_id'],'reference_paths':len(r['rows']),
                  'pin_path_checks':sum(statuses.values()),'statuses':{a+':'+b:n for (a,b),n in statuses.items()}})
out['external_availability']={'repositories':repos,'spec_bindings':[binding(x['path'],x['raw_sha256']) for x in sr.values()],
                              'anchor_checks':anchors,'limit':'Internal consistency and local specification bindings only; no external object read or proof certification.'}

demo=read('demo10_input_location_accounting.json'); assert len(demo['entries'])==6
demo_rows=[]
for x in demo['entries']:
    old=x['current_source_path']; assert old.startswith('education/')
    moved='pilots/'+old
    assert re.fullmatch('[0-9a-f]{64}',x['current_worktree_raw_sha256'])
    assert re.fullmatch('[0-9a-f]{40}',x['current_git_blob'])
    candidates=[p for p in [old,moved] if (ROOT/p).is_file()]
    r=binding(candidates[0],x['current_worktree_raw_sha256'],ROOT) if candidates else {'raw_match':None,'lf_match':None,'status':'historical_source_not_bound_in_current_repo'}
    r.update(recorded_git_blob=x['current_git_blob'],
             historical_and_recorded_current_blob_match=x['historical_git_blob']==x['current_git_blob'],
             original_path_exists=(ROOT/old).exists(),possible_relocation_path=moved,possible_relocation_exists=(ROOT/moved).exists(),
             historical_and_recorded_current_bytes_match=x['historical_git_raw_sha256']==x['current_worktree_raw_sha256'],
             historical_and_recorded_current_sizes_match=x['historical_git_byte_count']==x['current_worktree_byte_count'])
    demo_rows.append(r)
out['demo10_locations']={'entries':demo_rows,'limit':'Six historical location/binding declarations checked for internal agreement. Referenced source paths absent from current repository; external source Git objects and checker semantics not reexecuted. Not evidence of migration loss.'}

# A valid restricted path stays an upper bound even when an unrestricted shortcut exists.
def shortest(edges):
    todo=deque([('s',0)]); seen={'s'}
    while todo:
        a,d=todo.popleft()
        if a=='t':return d
        for b in edges.get(a,[]):
            if b not in seen:seen.add(b);todo.append((b,d+1))
restricted={'s':['a'],'a':['b'],'b':['t']}
unrestricted={**restricted,'s':['a','x'],'x':['t']}
out['g22_upper_bound_control']={'restricted_shortest':shortest(restricted),'global_shortest':shortest(unrestricted),
                               'upper_bound_valid':shortest(unrestricted)<=shortest(restricted),'equality':False}
assert out['g22_upper_bound_control']['upper_bound_valid']
(REV/'additional_paper_011_history_context_data.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest_raw_matches':out['recovery_manifest']['raw_matches'],'manifest_lf_matches':out['recovery_manifest']['lf_matches'],
                  'historical_master':out['master_report'],'replay_sections':len(sections),
                  'sections_present':sum(x['text_present_in_current_source'] for x in sections),
                  'external_anchor_checks':len(anchors),'anchors_at_declared_line':sum(x['line_contains_literal'] for x in anchors),
                  'demo_local_raw_matches':sum(x['raw_match'] is True for x in demo_rows),'demo_unbound_paths':sum(x['raw_match'] is None for x in demo_rows)}))
