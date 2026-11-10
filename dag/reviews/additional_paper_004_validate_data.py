"""All-row arithmetic and exact JSON delta checks for retained receipts."""
import collections,hashlib,json,re,zipfile
from fractions import Fraction
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; P='additional_paper_004'
PKG=ROOT/'papers/pfp/004_pfp_native_verification_and_evidence_custody'
load=lambda n:json.loads((PKG/n).read_text())
results={}
x=load('code/chordal_fuzz_repair_benchmark_receipt.json');r=x['results'];v=[Fraction(a['phi1_before']) for a in r]
results['chordal']={'rows':len(r),'seeds_exact_0_99':sorted(a['seed'] for a in r)==list(range(100)),'all_2tree_dimensions':all(a['num_edges']==2*a['num_vertices']-3 and a['cycle_rank']==a['num_edges']-a['num_vertices']+1 for a in r),'all_post_zero_and_admitted':all(Fraction(a['phi1_after'])==0 and a['governor_admitted'] for a in r),'mean':str(sum(v)/len(v)),'upper_middle':str(sorted(v)[len(v)//2]),'ordinary_median':str((sorted(v)[49]+sorted(v)[50])/2),'max':str(max(v)),'reported_mean_matches':str(sum(v)/len(v))==x['mean_phi1_before']}
x=load('code/l1_sparsity_benchmark_receipt.json');r=x['results_by_task'];a=sum(z['token_count_dense'] for z in r);b=sum(z['token_count_sparse'] for z in r)
results['sparsity']={'rows':len(r),'unique_task_ids':len(set(z['task_id'] for z in r)),'dense_tokens':a,'sparse_tokens':b,'mean_dense':a/len(r),'mean_sparse':b/len(r),'compression':round(a/b,2),'reduction_percent':round(100*(a-b)/a,2),'all_dense_false_sparse_true':all(not z['host_replay_dense_passed'] and z['host_replay_sparse_passed'] for z in r),'limits':'Recomputed aggregate arithmetic only; rows originate in authored templates with expected-token acceptance.'}
x=load('code/topology50_benchmark_receipt.json');r=x['results'];passed=sum(z['governed_success'] for z in r);accepted=sum(z['governed_accepted'] for z in r);proposed=sum(z['governed_proposals'] for z in r)
results['topology']={'rows':len(r),'ids_exact_1_50':sorted(z['theorem_id'] for z in r)==list(range(1,51)),'governed_solved':passed,'ungoverned_solved':sum(z['ungoverned_success'] for z in r),'accepted':accepted,'proposed':proposed,'aggregate_verification_rate':round(accepted/proposed,4),'all_accounting_balanced':all(z['governed_accepted']+z['governed_retractions']==z['governed_proposals'] for z in r),'limits':'Timing and hardcoded Lean version not independently verified; simulated goal removal is not theorem checking.'}
x=load('docs/historical_native_run/004_republication_gate_receipt.json');d=x['details'];r=d['checks']
results['republication']={'checks':len(r),'unique_ids':len(set(z['id'] for z in r)),'counts':dict(collections.Counter(z['status'] for z in r)),'recorded_evidence_count':len(d['recorded_evidence']),'snapshot_file_count':len(d['files']),'status':d['status'],'full_check_semantic_rows':[{'id':z['id'],'method':z['method'],'requirement':z['requirement'],'status':z['status'],'detail':z['detail']} for z in r]}
with zipfile.ZipFile(next(PKG.glob('*.zip'))) as z:
    name='docs/historical_native_run/004_republication_gate_receipt.json';old=z.read(PKG.name+'/'+name).decode();current=(PKG/name).read_text()
    results['republication_delta']={'complete_text_equal_after_omega_to_core':old.replace('omega','core')==current,'rule':'literal omega -> core applied to historical complete text; no value omitted','old_sha256':hashlib.sha256(z.read(PKG.name+'/'+name)).hexdigest()}
    manifests=[]
    for name in ['MANIFEST.sha256','SHA256SUMS']:
        pairs=lambda text:{p:h for h,p in (line.split('  ',1) for line in text.splitlines() if line and not line.startswith('#'))}
        a=pairs(z.read(PKG.name+'/'+name).decode());b=pairs((PKG/name).read_text());mapped={p.replace('_lev_landau_','_lev_examiner_').replace('_pfp_landau_companion.pdf','_pfp_examiner_companion.pdf'):h for p,h in a.items()}
        manifests.append({'name':name,'old_count':len(a),'current_count':len(b),'same_paths_after_explicit_rename':set(mapped)==set(b),'changed_digest_paths':[p for p in b if mapped.get(p)!=b[p]]})
    results['manifest_delta']=manifests
for name in ['axiom_report.txt','full_axiom_report.txt']:
    text=(PKG/'lean4'/name).read_text();lines=[line for line in text.splitlines() if line.startswith("'")];names=[line.split("'",2)[1] for line in lines];ax=collections.Counter()
    for line in lines:
        if 'depends on axioms:' in line:ax.update(x.strip() for x in line.split('[',1)[1].rstrip(']').split(','))
    results[name]={'rows':len(lines),'unique_names':len(set(names)),'axiom_occurrences':dict(ax),'unapproved':sorted(set(ax)-{'propext','Quot.sound','Classical.choice'})}
(HERE/(P+'_data_validation.json')).write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in results.items() if k!='republication'},indent=2))
print(json.dumps({k:v for k,v in results['republication'].items() if k!='full_check_semantic_rows'}))
