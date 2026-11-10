"""Freeze/read only Paper 007 originals; write this audit's own receipts."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P = 'additional_paper_007_support'
BASE = 'papers/pfp/007_pfp_executable_lessons_and_evidence_boundaries/'
OUT = HERE / 'paper_007_support_inspection'
def sha(b): return hashlib.sha256(b).hexdigest()
def write(s, x): (HERE / (P + s)).write_text(json.dumps(x, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
def load(s): return json.loads((HERE / (P+s)).read_text(encoding='utf-8'))

def freeze():
    inv = json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf-8'))
    cov = json.loads((HERE/'coverage.json').read_text(encoding='utf-8'))
    bypath = {x['path']:x for x in cov['files']}
    files, excluded = [], []
    for row in inv['files']:
        if not row['path'].startswith(BASE): continue
        raw = (ROOT/row['path']).read_bytes()
        assert sha(raw) == row['sha256'], row['path']
        item = {'path':row['path'], 'sha256':row['sha256'], 'bytes':len(raw), 'coverage_at_freeze':bypath[row['path']]['substantive_status']}
        try: item['lines'] = len(raw.decode('utf-8').splitlines())
        except UnicodeDecodeError: item['lines'] = None
        if item['coverage_at_freeze']=='full_text_source_review_recorded':
            item['prior_reading_receipts']=bypath[row['path']]['reading_receipts'];excluded.append(item)
        else: files.append(item)
    assert not (HERE/(P+'_scope.json')).exists()
    write('_scope.json', {'source_commit':inv['local_head'], 'inventory_path':'dag/file_inventory.json', 'inventory_sha256':sha((ROOT/'dag/file_inventory.json').read_bytes()), 'coverage_sha256_at_freeze':sha((HERE/'coverage.json').read_bytes()), 'files':files, 'excluded_prior_full_reads':excluded})
    print(json.dumps({'files':len(files),'excluded':len(excluded),'bytes':sum(x['bytes'] for x in files),'text_lines':sum(x['lines'] or 0 for x in files)}))
    for x in files: print(x['path'].removeprefix(BASE),x['lines'],x['bytes'])

def read(args):
    scope=load('_scope.json'); rows={x['path']:x for x in scope['files']+scope['excluded_prior_full_reads']}
    ledger=load('_read_ledger.json') if (HERE/(P+'_read_ledger.json')).exists() else []
    for arg in args:
        name,sep,range_text=arg.partition('::');path=BASE+name;raw=(ROOT/path).read_bytes();assert sha(raw)==rows[path]['sha256']
        lines=raw.decode('utf-8').splitlines();a,b=map(int,range_text.split('-')) if sep else (1,len(lines))
        assert (a==1 and b==0) or 1<=a<=b<=len(lines)
        print('FILE',path,'SHA256',sha(raw),'LINES',len(lines))
        for n in range(a,b+1):print(f'{n}: {lines[n-1]}')
        ledger.append({'path':path,'sha256':sha(raw),'source_lines':len(lines),'reviewed_lines':[[a,b]] if b else [],'output_truncated':False})
    write('_read_ledger.json',ledger)

if __name__=='__main__':
    if sys.argv[1]=='freeze': freeze()
    elif sys.argv[1]=='read': read(sys.argv[2:])
    else: raise SystemExit('unknown mode')
