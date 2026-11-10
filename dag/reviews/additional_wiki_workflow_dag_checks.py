"""Read-only structural checks and exact finite controls for the wiki audit.

No project imports, provider, native program, benchmark or historical run is used.
Only the own-prefix audit result is written.
"""
from pathlib import Path
import hashlib
import json
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
PREFIX = ROOT / 'dag/reviews/additional_wiki_workflow_dag'
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def bound(path):
    p = ROOT / path
    return {'path': path, 'sha256': digest(p), 'bytes': p.stat().st_size}

page = ROOT / 'wiki/Workflow-DAG.md'
text = page.read_text(encoding='utf-8')
lines = text.splitlines()
scope = json.loads(Path(str(PREFIX)+'_scope.json').read_text(encoding='utf-8'))
assert scope['files']==[{'path':'wiki/Workflow-DAG.md','sha256':digest(page),'bytes':page.stat().st_size,'coverage_at_freeze':'pending'}]
registry_path = ROOT / 'workflows/dag/workflow_dag.json'
registry = json.loads(registry_path.read_text(encoding='utf-8'))
heads = list(re.finditer(r'^## (WF\d+): ([^\n]+)$', text, re.M))
families = []
for i, h in enumerate(heads):
    end = heads[i+1].start() if i+1 < len(heads) else text.index('## Perturbations')
    body = text[h.start():end]
    status = re.search(r'\*\*Status:\*\* (.*?)\. \*\*Kind:', body).group(1)
    dep = re.search(r'\*\*Builds on:\*\* (.*?)\. \*\*Model calls', body).group(1)
    folder = re.search(r'\*\*Folder:\*\* \[`([^`]+)`\]', body).group(1)
    families.append({'id': h.group(1), 'name': h.group(2), 'lines': [text[:h.start()].count('\n')+1,text[:end].count('\n')],
                     'status': status, 'depends_on': re.findall(r'WF\d+',dep), 'folder': folder,
                     'folder_exists': (ROOT/folder).is_dir()})
mermaid = text.split('```mermaid',1)[1].split('```',1)[0]
edges = set(re.findall(r'\b(WF\d+)\s*-->\s*(WF\d+)\b', mermaid))
registry_edges = {(x['from'],x['to']) for x in registry['edges']}
prose_edges = {(p,x['id']) for x in families for p in x['depends_on']}
nodes = {x['id'] for x in families}
remaining = set(nodes); topo = []
while remaining:
    ready = sorted((n for n in remaining if not any(b==n and a in remaining for a,b in edges)),key=lambda n:int(n[2:]))
    if not ready: break
    topo += ready; remaining -= set(ready)
registry_by_id = {x['id']:x for x in registry['nodes']}
differences=[]
for x in families:
    r=registry_by_id.get(x['id'])
    if not r: differences.append({'id':x['id'],'field':'missing_registry_node'});continue
    for key in ['name','depends_on']:
        if x[key] != r[key]: differences.append({'id':x['id'],'field':key,'wiki':x[key],'registry':r[key]})
    if not x['status'].startswith(r['status']): differences.append({'id':x['id'],'field':'status','wiki':x['status'],'registry':r['status']})
links=[]
for url in re.findall(r'\]\((https://github\.com/dbccpage/proposal_fidelity_protocol_pfp/(?:tree|blob)/main/[^)]+)\)',text):
    rel=re.split(r'/(?:tree|blob)/main/',url)[1].split('#')[0]
    links.append({'url':url,'local_path':rel,'exists':(ROOT/rel).exists()})
ledger=json.loads(Path(str(PREFIX)+'_read_ledger.json').read_text(encoding='utf-8'))
read_lines=set()
for entry in ledger:
    assert entry['sha256']==digest(page)
    for a,b in entry['reviewed_lines']:read_lines.update(range(a,b+1))

# WF44: the displayed dual bound accepts a provably nonminimal residual.
B=[[-1,1,0],[0,-1,1],[1,0,-1]]
w=[2,2,2]; f=[0,3,5]; z=[2,2,2]
r=[w[i]+sum(B[i][j]*f[j] for j in range(3)) for i in range(3)]
btz=[sum(B[i][j]*z[i] for i in range(3)) for j in range(3)]
lhs=sum(wi*zi for wi,zi in zip(w,z)); norm=sum(map(abs,r))
wf44={'B':B,'w':w,'f':f,'z':z,'r':r,'B_transpose_z':btz,'dual_bound_as_written':all(abs(a)<=b for a,b in zip(z,w)),
      'displayed_equality':lhs==norm,'displayed_objective':norm,'better_feasible_f':[0,0,0],
      'better_feasible_residual':w,'true_unweighted_optimum':6,
      'optimality_proof':'Every r=w+Bf has sum 6, so ||r||_1>=6; f=0 attains 6. Displayed conditions accept objective 12.'}
assert btz==[0,0,0] and wf44['dual_bound_as_written'] and wf44['displayed_equality'] and norm==12
controls={
 'WF44_mixed_weight_certificate':wf44,
 'WF27_periodic_not_stationary':{'residuals':[1,2,3,1],'lag_three_equal':True,'last_adjacent_equal':False,'interpretation':'lag-3 recurrence does not imply a stationary residual'},
 'WF41_representative_without_class_invariance':{'carrier':[0,1],'one_class':[[0,1]],'representatives':[0],'A':[False,False],'D':[False,True],'agreement_on_representatives':True,'agreement_on_carrier':False},
 'WF18_difference_inequalities_not_equalities':{'directed_cycle_edges':[[0,1,1],[1,2,1],[2,0,1]],'cycle_weight':3,'negative_cycle':False,'inequality_potential':[0,0,0],'inequalities_valid':True,'exact_edge_differences_possible':False,'reason':'Summing three demanded differences 1 gives 3 while potentials telescope to 0.'},
 'WF4_exact_sum_agreement':{'exhaustive_values':[-1,0,1],'target':0,'agents':5,'locally_accepted_vectors':0,'local_green_global_disagreement':0},
 'WF29_soundness_and_completeness':{'valid':[0],'invalid':[1],'reject_all_accept_set':[],'sound_accept_implies_valid':True,'complete_valid_implies_accept':False},
 'zero_failure_upper_bounds':{'confidence':0.95,'assumption':'independent identically distributed Bernoulli opportunities; zero failures; one-sided exact bound','n8':1-0.05**(1/8),'n299':1-0.05**(1/299)},
}
periodic=controls['WF27_periodic_not_stationary']
periodic['lag_three_equal']=periodic['residuals'][-1]==periodic['residuals'][-4]
periodic['last_adjacent_equal']=periodic['residuals'][-1]==periodic['residuals'][-2]
assert periodic['lag_three_equal'] and not periodic['last_adjacent_equal']
representatives=controls['WF41_representative_without_class_invariance']
representatives['agreement_on_representatives']=all(representatives['A'][i]==representatives['D'][i] for i in representatives['representatives'])
representatives['agreement_on_carrier']=representatives['A']==representatives['D']
assert representatives['agreement_on_representatives'] and not representatives['agreement_on_carrier']
inequalities=controls['WF18_difference_inequalities_not_equalities']
v=inequalities['inequality_potential']
inequalities['inequalities_valid']=all(v[b]-v[a]<=c for a,b,c in inequalities['directed_cycle_edges'])
inequalities['cycle_weight']=sum(c for a,b,c in inequalities['directed_cycle_edges'])
inequalities['negative_cycle']=inequalities['cycle_weight']<0
inequalities['exact_edge_differences_possible']=inequalities['cycle_weight']==0
assert inequalities['inequalities_valid'] and not inequalities['negative_cycle'] and not inequalities['exact_edge_differences_possible']
logical=controls['WF29_soundness_and_completeness']
logical['sound_accept_implies_valid']=set(logical['reject_all_accept_set'])<=set(logical['valid'])
logical['complete_valid_implies_accept']=set(logical['valid'])<=set(logical['reject_all_accept_set'])
assert logical['sound_accept_implies_valid'] and not logical['complete_valid_implies_accept']
from itertools import product
for replies in product([-1,0,1],repeat=5):
    if all(x==0 for x in replies):
        controls['WF4_exact_sum_agreement']['locally_accepted_vectors']+=1
        controls['WF4_exact_sum_agreement']['local_green_global_disagreement']+=len(set(replies))!=1
result={'status':'complete','page':bound('wiki/Workflow-DAG.md'),'line_count':len(lines),'full_body_ledger_covers_all_lines':read_lines==set(range(1,len(lines)+1)),
 'family_count':len(families),'status_counts':dict(Counter(x['status'] for x in families)), 'families':families,
 'graph':{'registry':bound('workflows/dag/workflow_dag.json'),'edge_count':len(edges),'acyclic':not remaining,'topological_order':topo,
          'wiki_vs_registry_edges_equal':edges==registry_edges,'wiki_vs_prose_edges_equal':edges==prose_edges,
          'registry_only_edges':sorted(registry_edges-edges),'wiki_only_edges':sorted(edges-registry_edges),'node_differences':differences,
          'ceiling':'Parsed structural comparison only, no executable dispatch or semantic composition proof.'},
 'local_target_checks':{'count':len(links),'missing':[x for x in links if not x['exists']],'remote_checked':False},
 'perturbation_count':sum(line.startswith('| WF') for line in lines),'fresh_controls':controls,
 'execution_limits':'Standard-library arithmetic and static data checks only; no project/runtime/native/model/provider/private benchmark execution.'}
Path(str(PREFIX)+'_checks.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['families','fresh_controls']},indent=2))
