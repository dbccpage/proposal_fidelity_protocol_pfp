"""Read-only tracked education classification inventory; never imports source modules."""
import ast
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = 'education_demo_classification'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def inventory():
    paths = subprocess.check_output(['git', 'ls-files', '--', 'education'], cwd=ROOT, text=True).splitlines()
    rows = []
    cells = {}
    for path in paths:
        raw = (ROOT/path).read_bytes()
        row = {'path': path, 'sha256': digest(raw), 'bytes': len(raw), 'suffix': Path(path).suffix}
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            row['content_kind'] = 'binary_unrendered'
            rows.append(row)
            continue
        lines = text.splitlines()
        row.update(content_kind='text', line_count=len(lines), headings=[{'line': i+1, 'text': s} for i,s in enumerate(lines) if re.match(r'^#{1,6} ',s)], first_nonempty=[s for s in lines if s.strip()][:10])
        row['references'] = [{'line': i+1, 'text': s} for i,s in enumerate(lines) if re.search(r'(?:education/|_how_to_play|\.ipynb|\.py\b|\.svg\b|\.mp4\b|\.wav\b|\.mp3\b|read_text|read_bytes|open\(|__file__|sys\.path|parents\[|from (?:code|pfp|operads|eis|pciv)|import (?:code|pfp|operads|eis|pciv)|demo|pilot|receipt|benchmark|pytest|manim)',s,re.I)]
        if path.endswith('.py'):
            tree = ast.parse(text)
            row['definitions'] = [{'name': n.name, 'line': n.lineno, 'end_line': n.end_lineno, 'kind':type(n).__name__} for n in ast.walk(tree) if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))]
            row['imports'] = [ast.get_source_segment(text,n) for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
        if path.endswith('.ipynb'):
            nb=json.loads(text); row['notebook_cells']=[]
            for i,c in enumerate(nb.get('cells',[])):
                source=''.join(c.get('source',[])); h=digest(source.encode())
                cells.setdefault(h,{'source':source,'type':c.get('cell_type'),'locations':[]})['locations'].append([path,i])
                row['notebook_cells'].append({'index':i,'type':c.get('cell_type'),'source_sha256':h,'source_lines':len(source.splitlines()),'outputs':c.get('outputs',[]),'execution_count':c.get('execution_count')})
        if path.endswith('.json'):
            obj=json.loads(text); row['json_shape']={'type':type(obj).__name__,'keys':list(obj) if isinstance(obj,dict) else None,'length':len(obj) if isinstance(obj,(dict,list)) else None}
        rows.append(row)
    (HERE/(PREFIX+'_inventory.json')).write_text(json.dumps({'files':rows,'cells':cells},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('files',len(rows),'roots',dict(collections.Counter(x['path'].split('/')[1] for x in rows)))
    print('notebook cells',len(cells),'unique code cells',sum(x['type']=='code' for x in cells.values()),'code lines',sum(len(x['source'].splitlines()) for x in cells.values() if x['type']=='code'))

def read(paths):
    ledger_path=HERE/(PREFIX+'_read_ledger.json')
    ledger=json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else []
    for spec in paths:
        path,sep,span=spec.partition(':')
        assert path.startswith('education/')
        raw=(ROOT/path).read_bytes(); lines=raw.decode('utf-8-sig').splitlines()
        start,end=(map(int,span.split('-')) if sep else (1,len(lines)))
        print('\nFILE',path,'SHA256',digest(raw),'RANGE',start,end,'TOTAL',len(lines))
        print('\n'.join(f'{i+1}: {lines[i]}' for i in range(start-1,min(end,len(lines)))))
        ledger.append({'path':path,'sha256':digest(raw),'reviewed_lines':[start,end],'full_source_read':start==1 and end==len(lines)})
    ledger_path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    if sys.argv[1]=='inventory': inventory()
    elif sys.argv[1]=='read': read(sys.argv[2:])
