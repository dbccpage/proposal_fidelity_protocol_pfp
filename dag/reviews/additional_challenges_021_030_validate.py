"""Read-only offline certificate audit; outputs are confined to this review prefix."""
from __future__ import annotations
import copy, hashlib, importlib, json, socket, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFIX = ROOT / 'dag/reviews/additional_challenges_021_030'
FAMILY_ROOT = ROOT / 'workflows/tasks/certified_challenges'
sys.path.insert(0, str(FAMILY_ROOT))
sys.dont_write_bytecode = True

def deny_network(*args, **kwargs):
    raise RuntimeError('NETWORK_FORBIDDEN_IN_OFFLINE_AUDIT')
socket.create_connection = deny_network
socket.socket.connect = deny_network
socket.socket.connect_ex = deny_network

def duplicate_free(p):
    duplicates=[]
    def pairs(values):
        d={}
        for k,v in values:
            if k in d: duplicates.append(k)
            d[k]=v
        return d
    d=json.loads(p.read_text(encoding='utf-8-sig'), object_pairs_hook=pairs)
    return d,duplicates

def evaluate(n, family, case, certificate):
    if n in range(21,31):
        result = importlib.import_module(f'{family}.judge_packet.checkers.dual_evaluator').evaluate_dual(copy.deepcopy(case), copy.deepcopy(certificate))
        if isinstance(result, tuple):
            return {'verdict':'PASS' if result[0] else 'FAIL','reason':result[1],'details':result[2]}
        return result
    raise NotImplementedError(f'Family C{n:03} owners not yet reviewed')

def validate_record(path):
    p=ROOT/path; family=p.relative_to(FAMILY_ROOT).parts[0]; n=int(family[1:4])
    d,duplicates=duplicate_free(p)
    result={'checks':['json_parse','duplicate_keys'], 'duplicate_keys':duplicates}
    if duplicates:
        result.update(status='duplicate_keys',evidence_ceiling='Ambiguous JSON object; no certificate admission.')
        return result
    if '/mutation_suite/' in path:
        case=d.get('case',d.get('input_case'))
        cert=d.get('corrupted_result',d.get('corrupted_output',d.get('certificate',d.get('candidate',d.get('answer',d.get('mutated_answer',d.get('result')))))))
        result['checks'].append('owner_dual_checker_mutant')
        verdict=evaluate(n,family,case,cert)
        result.update(status='mutation_rejected' if verdict.get('verdict')=='FAIL' else 'mutation_survived_or_disagreed',checker_result=verdict,evidence_ceiling='This retained mutation only; rejection is not universal soundness.')
        if 'CHECKER_EXCEPTION' in json.dumps(verdict):
            result.update(status='checker_exception_caught',evidence_ceiling='Owner caught an exception; no mathematical rejection demonstrated.')
    elif '/cases/' in path or '/examples/' in path:
        case=d.get('input',d)
        owner='synthesis' if n==23 else 'solver'
        solve=importlib.import_module(f'{family}.reference_solver.{owner}').solve
        cert=solve(copy.deepcopy(case))
        if isinstance(cert,tuple): cert=cert[0]
        verdict=evaluate(n,family,case,cert)
        result['checks'] += ['reference_solver','owner_dual_checker_generated_certificate']
        result.update(status='case_certificate_verified' if verdict.get('verdict')=='PASS' else 'case_certificate_failed_or_disagreed',solver_status=cert.get('status'),checker_result=verdict,generated_certificate_sha256=hashlib.sha256(json.dumps(cert,sort_keys=True,separators=(',',':')).encode()).hexdigest(),evidence_ceiling='Finite case recomputation under reviewed implementations; does not certify population generalization.')
        if 'expected_output' in d:
            expected=evaluate(n,family,case,d['expected_output'])
            result['checks'].append('owner_dual_checker_retained_expected_output')
            result.update(expected_checker_result=expected,expected_equals_generated=cert==d['expected_output'])
            if expected.get('verdict')!='PASS': result['status']='retained_expected_output_failed'
    elif p.name=='accounting.json':
        result.update(status='accounting_template_only',evidence_ceiling='Configuration/template, not evidence of live calls or costs.')
        if isinstance(d.get('calls'),list) and not d['calls']:
            result['checks'].append('empty_call_totals')
            result['zero_totals_consistent']=all(d.get(k,0)==0 for k in ('total_billed_cost_usd','total_tokens_in','total_tokens_out'))
    elif p.name=='manifest.json':
        result.update(status='manifest_custody_only',evidence_ceiling='Previously audited custody metadata; content hash does not establish mathematical validity.')
    else:
        result.update(status='pending_schema_owner',evidence_ceiling='JSON syntax only; schema semantics not yet reviewed.')
    return result

def main():
    if sys.argv[1]=='worker':
        try: print(json.dumps(validate_record(sys.argv[2]),ensure_ascii=True))
        except Exception as exc: print(json.dumps({'status':'checker_or_solver_exception','exception_type':type(exc).__name__,'exception':str(exc),'checks':['json_parse','owner_execution_attempt'],'evidence_ceiling':'Execution exception; no validity conclusion.'}))
        return
    n=int(sys.argv[1]); rows=json.loads((ROOT/'dag/file_inventory.json').read_text())['files']
    rows=[r for r in rows if r['path'].startswith(f'workflows/tasks/certified_challenges/c{n:03}_') and Path(r['path']).suffix=='.json']
    dest=Path(str(PREFIX)+f'_c{n:03}_automated.jsonl')
    from collections import Counter
    counts=Counter()
    with dest.open('w',encoding='utf-8',newline='\n') as output:
        for r in rows:
            start=time.monotonic(); raw=(ROOT/r['path']).read_bytes()
            rec={'path':r['path'],'sha256':hashlib.sha256(raw).hexdigest(),'inventory_sha256':r['sha256'],'full_source_read':False}
            rec['inventory_raw_hash_match']=rec['sha256']==r['sha256']
            try:
                run=subprocess.run([sys.executable,'-B','-X','utf8',__file__,'worker',r['path']],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=20)
                rec.update(json.loads(run.stdout))
                if run.stderr:rec['stderr']=run.stderr[-2000:]
            except subprocess.TimeoutExpired:
                rec.update(status='timeout',checks=['bounded_owner_execution_attempt'],timeout_seconds=20,evidence_ceiling='Time limit, not rejection or counterexample.')
            except Exception as exc:
                rec.update(status='audit_harness_error',exception=f'{type(exc).__name__}: {exc}')
            rec['elapsed_seconds']=round(time.monotonic()-start,6)
            counts[rec['status']]+=1; output.write(json.dumps(rec,ensure_ascii=True)+'\n');output.flush()
    print(json.dumps({'family':n,'files':len(rows),'counts':dict(counts),'ledger':dest.relative_to(ROOT).as_posix()}))

if __name__=='__main__':main()
