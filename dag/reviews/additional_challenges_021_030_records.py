"""Replay every pinned retained JSONL answer with explicit identity and time bounds."""
import copy, hashlib, importlib, json, socket, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'dag/reviews/additional_challenges_021_030'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
def deny(*a,**k):raise RuntimeError('NETWORK_FORBIDDEN')
socket.create_connection=socket.socket.connect=socket.socket.connect_ex=deny
def parse(s):
    duplicates=[]
    def hook(pairs):
        d={}
        for k,v in pairs:
            if k in d:duplicates.append(k)
            d[k]=v
        return d
    return json.loads(s,object_pairs_hook=hook),duplicates
def worker():
    cpath,apath,line=sys.argv[2:];case=json.loads((ROOT/cpath).read_text());case=case.get('input',case)
    answer=json.loads((ROOT/apath).read_text().splitlines()[int(line)-1]);family=Path(cpath).parts[3]
    try:
        r=importlib.import_module(f'{family}.judge_packet.checkers.dual_evaluator').evaluate_dual(copy.deepcopy(case),answer)
        print(json.dumps({'verdict':'PASS' if r[0] else 'FAIL','reason':r[1],'details':r[2]} if isinstance(r,tuple) else r))
    except Exception as e:print(json.dumps({'verdict':'EXCEPTION','exception':f'{type(e).__name__}: {e}'}))
def main():
    if len(sys.argv)>1 and sys.argv[1]=='worker':worker();return
    inventory=json.loads((ROOT/'dag/file_inventory.json').read_text())['files'];records=[]
    for n in range(21,31):
        prefix=f'workflows/tasks/certified_challenges/c{n:03}_'
        group=[r for r in inventory if r['path'].startswith(prefix)]
        paths=[r for r in group if r['path'].endswith('.jsonl')]
        examples={}
        for r in group:
            if '/participant_packet/examples/' in r['path'] and r['path'].endswith('.json'):
                case=json.loads((ROOT/r['path']).read_text());case=case.get('input',case)
                examples.setdefault(case.get('case_id',case.get('id')),[]).append(r)
        interpreter=str(ROOT/'.venv/Scripts/python.exe') if n not in (23,24,25) else r'C:\Users\a343o\AppData\Roaming\uv\python\cpython-3.12.12-windows-x86_64-none\python.exe'
        for pin in paths:
            p=ROOT/pin['path'];lines=[];seen=set()
            for number,txt in enumerate(p.read_text().splitlines(),1):
                answer,duplicates=parse(txt);key=answer.get('id');matches=examples.get(key,[])
                rec={'line':number,'answer_id':key,'duplicate_keys':duplicates,'duplicate_answer_id':key in seen};seen.add(key)
                if len(matches)!=1:rec.update(status='unresolved_case_identity',match_count=len(matches))
                else:
                    c=matches[0];rec.update(case_path=c['path'],case_sha256=hashlib.sha256((ROOT/c['path']).read_bytes()).hexdigest())
                    try:
                        run=subprocess.run([interpreter,'-B','-X','utf8',__file__,'worker',c['path'],pin['path'],str(number)],cwd=ROOT,capture_output=True,text=True,encoding='utf8',timeout=20)
                        result=json.loads(run.stdout);s='answer_verified' if result.get('verdict')=='PASS' else 'answer_failed_or_disagreed'
                        if 'IndependentVerificationUnavailable' in json.dumps(result):s='independent_verification_unavailable'
                        elif 'CHECKER_EXCEPTION' in json.dumps(result) or result.get('verdict')=='EXCEPTION':s='checker_exception'
                        rec.update(status=s,checker_result=result)
                    except subprocess.TimeoutExpired:rec.update(status='timeout',timeout_seconds=20)
                    except Exception as e:rec.update(status='harness_error',exception=f'{type(e).__name__}: {e}')
                lines.append(rec)
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            records.append(dict(path=pin['path'],sha256=digest,inventory_sha256=pin['sha256'],inventory_raw_hash_match=digest==pin['sha256'],full_source_read=False,checks=['jsonl_parse','duplicate_keys_every_line','unique_answer_ids','unique_pinned_example_identity','owner_dual_checker_every_retained_answer_20s_bound'],status='answers_verified' if all(r['status']=='answer_verified' and not r['duplicate_keys'] and not r['duplicate_answer_id'] for r in lines) else 'answers_have_bounded_issues',line_reviews=lines,evidence_ceiling='Certificates bound to these pinned public example cases; no live model/provider/billing evidence or population generalization.'))
    with Path(str(P)+'_records_automated.jsonl').open('w',encoding='utf8',newline='\n') as out:
        for r in records:out.write(json.dumps(r)+'\n')
    print(json.dumps([{'path':r['path'],'status':r['status'],'lines':len(r['line_reviews']),'issues':[x for x in r['line_reviews'] if x['status']!='answer_verified']} for r in records],indent=2))
if __name__=='__main__':main()
