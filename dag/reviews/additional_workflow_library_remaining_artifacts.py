"""Bounded whole-population artifact inspection; never source-reading credit."""
import collections,hashlib,json,re,sys,xml.etree.ElementTree as ET
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'dag/reviews/additional_workflow_library_remaining'
rows=json.loads(Path(str(P)+'_preparation.json').read_text())['files']
def strict(s):
    def pairs(xs):
        d={}
        for k,v in xs:
            if k in d:raise ValueError('duplicate key '+k)
            d[k]=v
        return d
    return json.loads(s,object_pairs_hook=pairs)
def walk(x,p=''):
    yield p,x
    if isinstance(x,dict):
        for k,v in x.items():yield from walk(v,p+'/'+str(k))
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from walk(v,p+'/'+str(i))
out=[]
for i,row in enumerate(rows):
    if row['suffix'] not in ['.json','.yaml','.raw','.xml']:continue
    b=(ROOT/row['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256']
    r={'index':i,'path':row['path'],'sha256':row['sha256'],'bytes':len(b),'full_source_read':False,'method':'whole_population_parse_and_selected_semantic_fields_no_full_body_credit'}
    try:
        if row['suffix']=='.xml':
            root=ET.fromstring(b);cases=list(root.iter('testcase'));suites=list(root.iter('testsuite'))
            outcomes=collections.Counter('failure' if c.find('failure') is not None else 'error' if c.find('error') is not None else 'skipped' if c.find('skipped') is not None else 'passed' for c in cases)
            r.update(testcase_count=len(cases),outcomes=dict(outcomes),suite_attributes=[x.attrib for x in suites],unique_case_ids=len({(c.get('classname'),c.get('name')) for c in cases}),negative_cases=[{'class':c.get('classname'),'name':c.get('name'),'kind':z.tag,'text':''.join(z.itertext())[:240]} for c in cases for z in c if z.tag in ('failure','error','skipped')])
        else:
            x=yaml.safe_load(b) if row['suffix']=='.yaml' else strict(b.decode('utf-8'))
            seq=list(walk(x));r.update(root_type=type(x).__name__,top_keys=list(x) if isinstance(x,dict) else None,top_lengths={k:len(v) for k,v in x.items() if isinstance(v,(dict,list))} if isinstance(x,dict) else {},node_count=len(seq),scalar_count=sum(not isinstance(v,(dict,list)) for _,v in seq))
            signals=collections.defaultdict(collections.Counter)
            for p,v in seq:
                k=p.rsplit('/',1)[-1]
                if k in {'status','outcome','trial_status','execution_mode','authority_effect','AuthorityEffect','checker_id','host_exact_match','kind','cost_status','attestation_mode','terminal','level','score_token'} and not isinstance(v,(dict,list)):
                    signals[k][str(v)]+=1
            r['signal_counts']={k:dict(v) for k,v in signals.items()}
            if row['contract_score']:
                c=x['contract'];s=x['score'];a=c['artifact'];ap=ROOT/a['path']
                r.update(contract_artifact=a,artifact_hash_matches=ap.is_file() and hashlib.sha256(ap.read_bytes()).hexdigest()==a['sha256'],symbols=c.get('symbols'),owned_invariants=c.get('owned_invariants'),level=s.get('level'),score_token=s.get('score_token'),mutation_accounting=s.get('mutation_accounting'),evidence=s.get('evidence'))
            elif row['suffix']=='.raw':
                a=x.get('answer') if isinstance(x,dict) else None
                r.update(envelope_keys=list(x) if isinstance(x,dict) else None,task_id=x.get('task_id') if isinstance(x,dict) else None,attempt_id=x.get('attempt_id') if isinstance(x,dict) else None,input_sha256=x.get('input_sha256') if isinstance(x,dict) else None,answer_keys=list(a) if isinstance(a,dict) else None,task_result=a.get('task_result') if isinstance(a,dict) else None,total=a.get('total') if isinstance(a,dict) else None,operation_count=len(a.get('operad_candidates',[])) if isinstance(a,dict) else None,ddc_count=len(a.get('ddc_moves',[])) if isinstance(a,dict) else None,slot_count=len(a.get('slot_report',[])) if isinstance(a,dict) else None)
                if isinstance(a,dict):
                    for field,counter in [('operad_candidates','operation_count'),('ddc_moves','ddc_count'),('slot_report','slot_count')]:
                        v=a.get(field,[]);r[field+'_type']=type(v).__name__;r[counter]=len(v) if isinstance(v,(list,dict)) else None
                    if isinstance(a.get('operad_candidates'),list):r['operation_signatures']=[{k:v for k,v in z.items() if k in ('id','arity','source_colours','target_colour')} for z in a['operad_candidates'] if isinstance(z,dict)]
            elif i in (193,225,232):
                r['top_scalar_fields']={k:v for k,v in x.items() if not isinstance(v,(dict,list))}
                r['record_shapes']={k:dict(collections.Counter(','.join(sorted(z)) if isinstance(z,dict) else type(z).__name__ for z in v)) for k,v in x.items() if isinstance(v,list)}
                r['all_record_ids']={k:[{f:z[f] for f in ('id','pilot_id','seed_id','demo_id','name','title','status','task_family','schema') if f in z} for z in v if isinstance(z,dict)] for k,v in x.items() if isinstance(v,list)}
            elif i in (149,150,184,185,186,187,188,189,204,207,216,218,220,264,266):
                r['top_scalar_fields']={k:v for k,v in x.items() if not isinstance(v,(dict,list))} if isinstance(x,dict) else {}
                r['numeric_leaf_totals']={k:sum(v for p,v in seq if p.rsplit('/',1)[-1]==k and type(v) in (int,float)) for k in ('passed','failed','failures','errors','skipped','tests','provider_calls','new_provider_calls')}
        r['parse_ok']=True
    except Exception as e:r.update(parse_ok=False,error=type(e).__name__+': '+str(e))
    out.append(r)
Path(str(P)+'_artifact_population.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,default=str)+'\n',encoding='utf-8')
for r in out:
    if r['index']<97 and not r.get('artifact_hash_matches',True):print('CONTRACT PIN MISMATCH',r['index'],r['path'])
    if r['index']>=97 and r['index'] not in range(151,184) and r['index'] not in range(194,204) and r['index'] not in range(233,258):print(json.dumps({k:v for k,v in r.items() if k in ('index','parse_ok','error','top_lengths','testcase_count','outcomes','unique_case_ids','answer_keys','task_result','total','operation_count','ddc_count','slot_count','operad_candidates_type','slot_report_type')},ensure_ascii=False))
