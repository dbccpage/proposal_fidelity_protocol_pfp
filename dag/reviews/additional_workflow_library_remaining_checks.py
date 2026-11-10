"""Exact bounded data relations, with no executable historical replay."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,yaml,xml.etree.ElementTree as ET,re,statistics
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'dag/reviews/additional_workflow_library_remaining'
rows=json.loads(Path(str(P)+'_preparation.json').read_text())['files'];indexed={r['path']:r for r in rows}
def value(i):
    p=ROOT/rows[i]['path'];return yaml.safe_load(p.read_bytes()) if p.suffix=='.yaml' else json.loads(p.read_bytes())
out={}
for i in (149,150):
    x=value(i);checks=[]
    for row in x['files']:
        p='workflows/library/'+row['path'];r=indexed[p]
        checks.append({'path':p,'hash_matches':r['sha256']==row['sha256'],'bytes_match':r['bytes']==row['bytes']})
    out[str(i)]={'kind':x['kind'],'warning':x['warning'],'checks':checks,'all_match':all(c['hash_matches'] and c['bytes_match'] for c in checks)}
x=value(184);out['184']={'count':len(x['files']),'declared_count':x['retained_file_count'],'unique_original_paths':len({r['original_path'] for r in x['files']}),'declared_bytes_total':sum(r['bytes'] for r in x['files']),'hash_shape_valid':all(re.fullmatch('[0-9a-f]{64}',r['sha256']) for r in x['files']),'prior_chain':x['wf5_old_failed_miner_chain'],'original_files_reopened':False}
for i in (185,186):
    x=value(i);out[str(i)]={'owners':len(x),'grade_counts':dict(Counter(z['gate5_ceiling'] for z in x.values())),'maxima':{k:max(z[k] for z in x.values()) for k in ('ccn_max','cognitive_max','nesting_max')},'current_metrics_recomputed':False}
x=value(187);out['187']={'top_fields':{k:v for k,v in x.items() if k!='files'},'rows':len(x['files']),'first_entry':x['files'][0] if isinstance(x['files'],list) else next(iter(x['files'].items()))}
x=value(193);out['193']={'header':{k:v for k,v in x.items() if k not in ('dimensions','outcomes')},'dimension_count':len(x['dimensions']),'outcome_count':len(x['outcomes']),'dimension_shape_counts':dict(Counter(','.join(sorted(z)) for z in x['dimensions'])),'all_dimension_names':[z.get('id',z.get('name')) for z in x['dimensions']],'examples':x['dimensions'][:3],'outcomes':x['outcomes']}
x=value(204);out['204']={'source_count':len(x),'all_hash_shape':all(re.fullmatch('[0-9a-f]{64}',v) for v in x.values()),'current_source_reads':0}
x=value(207);out['207']={'header':{k:v for k,v in x.items() if k!='files'},'captured_sources':len(x['files']),'first_entry':x['files'][0] if isinstance(x['files'],list) else next(iter(x['files'].items()))}
x=value(216);out['216']={'rows':len(x),'unique_test_ids':len({(r['classname'],r['name']) for r in x}),'latest_status_counts':dict(Counter(r['latest_status'] for r in x)),'negative_rows':[r for r in x if r['latest_status']!='passed']}
for i in (208,209,210,211,212,214,217):
    s=(ROOT/rows[i]['path']).read_text(encoding='utf-8');raw_ok=True
    try:tree=ET.fromstring(s)
    except ET.ParseError as e:
        raw_ok=False;error=str(e)
        tree=ET.fromstring(s.replace('<home>','&lt;home&gt;'))
    cases=list(tree.iter('testcase'));negative=[]
    for c in cases:
        for child in c:
            if child.tag in ('failure','error','skipped'):negative.append({'class':c.get('classname'),'name':c.get('name'),'kind':child.tag,'message':child.get('message'),'body':''.join(child.itertext())})
    out[str(i)]={'raw_xml_valid':raw_ok,'parse_error':None if raw_ok else error,'inspection_only_escape_home_count':0 if raw_ok else s.count('<home>'),'testcases':len(cases),'suite_attributes':[e.attrib for e in tree.iter('testsuite')],'negative_cases':negative}
x=value(225);ps=x['pilots'];out['225']={'pilot_count':len(ps),'unique_ids':len({z['pilot_id'] for z in ps}),'execution_state_counts':dict(Counter(z.get('execution_state') for z in ps)),'expected_status_counts':dict(Counter(z['expected_outcome']['status'] for z in ps)),'expected_answer_counts':dict(Counter(str(z['expected_outcome']['answer']) for z in ps)),'base_problem':x['base_problem'],'claim_hygiene':x['claim_hygiene'],'register_keys':{k:list(x[k]) for k in x if isinstance(x[k],dict)},'finite_source_toys_not_fresh_trials':True}
x=value(232);ss=x['seeds'];entries=[]
for k,z in ss.items():
    entries.append({'key':k,'id':z['seed_id'],'title':z['title'],'collection':z['collection'],'category':z['category'],'expected_predicates':z.get('expected_predicates'),'text_equals_prompt':z['seed_text']==z['seed_prompt'],'embedded_seed_hash_matches_prompt':hashlib.sha256(z['seed_prompt'].encode()).hexdigest()==z['seed_sha256']})
out['232']={'declared':x['total_seeds'],'actual':len(ss),'folder_bijection':len(set(x['by_folder'].values()))==len(ss) and set(x['by_folder'].values())==set(ss),'collections':dict(Counter(z['collection'] for z in ss.values())),'entries':entries,'hash_matches':sum(z['embedded_seed_hash_matches_prompt'] for z in entries),'text_equals_prompt':sum(z['text_equals_prompt'] for z in entries)}
x=value(264);groups=defaultdict(list)
for z in x['measurements']:groups[(z['tokenizer_id'],z['variant'])].append(z)
out['264']={'measurement_count':len(x['measurements']),'unique_cells':len({(z['case_id'],z['tokenizer_id'],z['variant']) for z in x['measurements']}),'utf8_bytes_equals_tokens':all(z['bytes']==z['tokens'] for z in x['measurements'] if z['tokenizer_id']=='utf8-bytes'),'recomputed_means':{str(k):statistics.mean(z['tokens'] for z in v) for k,v in groups.items()},'summaries':x['summaries'],'amortization':x['amortization'],'not_provider_tokenization':True}
pop=json.loads(Path(str(P)+'_artifact_population.json').read_text());cs=[r for r in pop if 'contract_artifact' in r];raw=[r for r in pop if 98<=r['index']<=148]
out['contract_scores']={'count':len(cs),'source_hash_matches':sum(r['artifact_hash_matches'] for r in cs),'grade_counts':dict(Counter(r['score_token'] for r in cs)),'null_mutation_accounting':sum(r['mutation_accounting'] is None for r in cs)}
out['raw_captures']={'count':len(raw),'strict_json':sum(r['parse_ok'] for r in raw),'unique_sha256':len({r['sha256'] for r in raw}),'total_38_fields':sum(r.get('total')==38 or r.get('task_result')=={'total':38} for r in raw),'non_array_operads':[r['path'] for r in raw if r.get('operad_candidates_type')=='str'],'all_hash_groups':{h:[r['path'] for r in raw if r['sha256']==h] for h in {r['sha256'] for r in raw}}}
out['raw_captures']['arity_checks']=[{'path':r['path'],'id':z.get('id'),'arity':z.get('arity'),'source_colour_count':len(z['source_colours']) if isinstance(z.get('source_colours'),list) else None,'arity_matches':type(z.get('arity')) is int and isinstance(z.get('source_colours'),list) and z['arity']==len(z['source_colours'])} for r in raw for z in r.get('operation_signatures',[])]
Path(str(P)+'_data_checks.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,default=str)+'\n',encoding='utf-8')
for k,v in out.items():
    print(k,json.dumps({a:b for a,b in v.items() if a not in ('checks','all_dimension_names','outcomes','entries','negative_cases','all_hash_groups','summaries','arity_checks')},ensure_ascii=False,default=str)[:2500])
