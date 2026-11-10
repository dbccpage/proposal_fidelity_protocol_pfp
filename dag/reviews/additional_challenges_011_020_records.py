"""Offline remaining JSONL answers and C017 historical-report audit."""
import copy, hashlib, importlib, json, socket, sys
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'dag/reviews/additional_challenges_011_020'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
def deny(*a,**k):raise RuntimeError('NETWORK_FORBIDDEN')
socket.create_connection=deny;socket.socket.connect=deny
inventory=json.loads((ROOT/'dag/file_inventory.json').read_text())['files']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(s):
    duplicates=[]
    def hook(pairs):
        out={}
        for k,v in pairs:
            if k in out:duplicates.append(k)
            out[k]=v
        return out
    return json.loads(s,object_pairs_hook=hook),duplicates
def evaluate(family,c,s):
    try:
        r=importlib.import_module(f'{family}.judge_packet.checkers.dual_evaluator').evaluate_dual(copy.deepcopy(c),copy.deepcopy(s))
        return {'verdict':'PASS' if r[0] else 'FAIL','reason':r[1],'details':r[2]} if isinstance(r,tuple) else r
    except Exception as e:return {'verdict':'EXCEPTION','exception_type':type(e).__name__,'exception':str(e)}
records=[]
for n in range(11,15):
    family=next((ROOT/'workflows/tasks/certified_challenges').glob(f'c{n:03}_*')).name
    base=ROOT/'workflows/tasks/certified_challenges'/family
    p=base/'participant_packet/answers.jsonl'
    examples={}
    for row in inventory:
        if row['path'].startswith(base.relative_to(ROOT).as_posix()+'/participant_packet/examples/') and row['path'].endswith('.json'):
            d=json.loads((ROOT/row['path']).read_text());case=d.get('input',d)
            examples.setdefault(case.get('id'),[]).append((row['path'],case))
    lines=[];seen=set()
    for number,text in enumerate(p.read_text().splitlines(),1):
        cert,duplicates=parse(text);key=cert.get('id');matches=examples.get(key,[])
        rec={'line':number,'answer_id':key,'duplicate_keys':duplicates,'duplicate_answer_id':key in seen}
        seen.add(key)
        if len(matches)!=1:rec.update(status='unresolved_case_identity',match_count=len(matches))
        else:
            path,c=matches[0];r=evaluate(family,c,cert)
            rec.update(case_path=path,case_sha256=digest(ROOT/path),checker_result=r,status='answer_verified' if r.get('verdict')=='PASS' else 'answer_failed')
        lines.append(rec)
    records.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'checks':['jsonl_parse','duplicate_keys_per_line','unique_answer_ids','unique_pinned_example_id_binding','owner_dual_checker_each_retained_answer'],'status':'answers_verified' if all(r['status']=='answer_verified' and not r['duplicate_keys'] and not r['duplicate_answer_id'] for r in lines) else 'answer_record_failure','line_reviews':lines,'evidence_ceiling':'Retained answer certificates for bound public examples only; no inference/model provenance or universal proof.'})

family='c017_nonabelian_lattice_holonomy';base=ROOT/'workflows/tasks/certified_challenges'/family
mapping={'pois_01_s3_commutator_trap':'poisoned/pois_01.json','base_01_s3_open_nonflat':'base/base_01.json','base_02_s3_open_puregauge':'base/base_02.json','base_03_s3_periodic_torus':'base/base_03.json','base_13_q8_open_nonflat':'base/base_13.json'}
reports={}
for p in sorted((base/'results').glob('*report.json')):
    d,duplicates=parse(p.read_text());entries=[];cost=Decimal(0);rates={}
    for i,r in enumerate(d['cases_evaluated']):
        cpath=base/'judge_packet/cases'/mapping[r['case_id']]
        case=json.loads(cpath.read_text());s=importlib.import_module(f'{family}.reference_solver.solver').solve(case)[0]
        variants={k:r[k] for k in ('baseline','immune_assisted') if k in r} or {'arm':r}
        for arm,entry in variants.items():
            meta=entry['meta'];cost+=Decimal(str(meta['cost']))
            rr={'record_index':i,'arm':arm,'case_id':r['case_id'],'case_path':cpath.relative_to(ROOT).as_posix(),'case_sha256':digest(cpath),'retained_passed':entry['passed'],'expected_verdict_matches_current_reference':r['expected_verdict']==s.get('verdict'),'cost_usd_recorded':str(meta['cost']),'token_fields_nonnegative_integers':all(type(meta[k]) is int and meta[k]>=0 for k in ('in_tokens','out_tokens')),'latency_nonnegative':type(meta['latency']) in (int,float) and meta['latency']>=0}
            rates.setdefault(arm,[0,0]);rates[arm][0]+=entry['passed'] is True;rates[arm][1]+=1
            if 'solution' in entry:
                check=evaluate(family,case,entry['solution'])
                rr.update(checker_result=check,current_pass_matches_retained=entry['passed']==(check.get('verdict')=='PASS'),status='historical_solution_replayed')
            else:rr.update(status='historical_answer_not_retained',limitation='Verdict and old rejection text do not reconstruct a full certificate; cannot rescore missing raw answer.')
            entries.append(rr)
    delta=Decimal(str(d['total_cost_usd']))-cost
    rec={'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'checks':['json_parse','duplicate_keys','recorded_cost_sum_decimal','nonnegative_token_latency_fields','retained_solution_current_dual_replay_when_present','recorded_pass_counts'],'status':'historical_report_bounded_replay','duplicate_keys':duplicates,'reported_dry_run':d['dry_run'],'model_label':d['model'],'cost_sum_usd':str(cost),'reported_total_usd':str(d['total_cost_usd']),'total_minus_sum':str(delta),'cost_sum_consistent_with_float_roundoff':abs(delta)<=Decimal('1e-15'),'recorded_pass_rates':{k:f'{v[0]}/{v[1]}' for k,v in rates.items()},'record_reviews':entries,'evidence_ceiling':'Historical artifact says dry_run=false; retained solutions can be rescored, but no provider generation ID, signed bill, raw response or request provenance is established here. Zero recorded cost is not proof of a free call.'}
    reports[p.name]=(d,rec);records.append(rec)

receipt_to_report={'receipt.json':'immune_transfer_report.json','receipt_arm5.json':'arm5_hybrid_report.json','receipt_arm5_stealth_space_bunny_alpha.json':'arm5_stealth_space_bunny_alpha_report.json','receipt_arm6_stealth_space_bunny_alpha.json':'arm6_stealth_space_bunny_alpha_report.json'}
for filename,reportname in receipt_to_report.items():
    p=base/'results'/filename;d,duplicates=parse(p.read_text());report,rr=reports[reportname];rp=base/'results'/reportname
    candidates={'raw_report_bytes':rp.read_bytes(),'LF_report_bytes':rp.read_bytes().replace(b'\r\n',b'\n'),'sorted_json_default_separators':json.dumps(report,sort_keys=True).encode(),'sorted_json_indent2':json.dumps(report,sort_keys=True,indent=2).encode()}
    hash_matches=[k for k,v in candidates.items() if hashlib.sha256(v).hexdigest()==d['sha256']]
    rate_keys={'baseline_pass_rate':'baseline','immune_pass_rate':'immune_assisted','arm5_pass_rate':'arm','arm6_pass_rate':'arm'}
    records.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'checks':['json_parse','duplicate_keys','receipt_report_cost_reconciliation','receipt_recorded_pass_rates','explicit_hash_convention_candidates'],'status':'historical_receipt_bounded_reconciliation','duplicate_keys':duplicates,'report_path':rr['path'],'report_sha256':rr['sha256'],'cost_matches_report':Decimal(str(d['total_spent_usd']))==Decimal(str(report['total_cost_usd'])),'pass_rates_match_report':{k:v==rr['recorded_pass_rates'][rate_keys[k]] for k,v in d.items() if k in rate_keys},'declared_digest':d['sha256'],'matching_report_digest_conventions':hash_matches,'producer_hash_convention_status':'unresolved: shared eval_epistemic_immune_transfer.py owner absent from checkout and pinned family inventory; candidate equality is observational, not an inferred normative convention','status_scope':d.get('status_scope','not_declared'),'evidence_ceiling':'Receipt PASS is at most retained harness completion; pass-rate fields may be partial, and billing/provider authenticity is not certified.'})

with Path(str(P)+'_records_automated.jsonl').open('w',encoding='utf-8',newline='\n') as f:
    for r in records:
        r['full_source_read']=False
        f.write(json.dumps(r)+'\n')
print(json.dumps({'files':len(records),'answers':[{ 'path':r['path'],'status':r['status'],'lines':len(r.get('line_reviews',[]))} for r in records[:4]],'reports':[{'path':r['path'],'rates':r.get('recorded_pass_rates'),'hash_matches':r.get('matching_report_digest_conventions'),'cost_match':r.get('cost_sum_consistent_with_float_roundoff'),'rescoring_changes':sum(x.get('current_pass_matches_retained') is False for x in r.get('record_reviews',[]))} for r in records[4:]]}))
