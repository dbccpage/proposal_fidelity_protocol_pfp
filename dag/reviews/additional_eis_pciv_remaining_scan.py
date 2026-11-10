"""Whole-file structural inventory; explicitly not a human full-reading receipt."""
import ast,collections,hashlib,json,re,sys
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
scope=json.loads((HERE/'additional_eis_pciv_remaining_scope.json').read_text())['files']
rows=[]
for item in scope:
 p=ROOT/item['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==item['sha256'],item['path']
 text=raw.decode('utf-8');r=dict(path=item['path'],sha256=item['sha256'],lines=len(text.splitlines()),automated_only=True)
 if p.suffix=='.py':
  tree=ast.parse(text);r['docstring']=ast.get_docstring(tree);r['imports']=[ast.unparse(n) for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
  r['functions']=[]
  for n in ast.walk(tree):
   if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
   selected=[]
   for a in ast.walk(n):
    if isinstance(a,ast.Assert):selected.append(dict(lines=[a.lineno,a.end_lineno],source=ast.unparse(a)))
    elif isinstance(a,ast.Call) and isinstance(a.func,ast.Attribute) and a.func.attr.startswith('assert'):
     selected.append(dict(lines=[a.lineno,a.end_lineno],source=ast.unparse(a)))
    elif isinstance(a,ast.With):
     for c in a.items:
      if 'raises(' in ast.unparse(c.context_expr):selected.append(dict(lines=[c.context_expr.lineno,c.context_expr.end_lineno],source=ast.unparse(c.context_expr)))
   r['functions'].append(dict(name=n.name,lines=[n.lineno,n.end_lineno],docstring=ast.get_docstring(n),assertions=selected,calls=sorted({ast.unparse(c.func) for c in ast.walk(n) if isinstance(c,ast.Call)})))
  r['risk_calls']=[dict(line=n.lineno,call=ast.unparse(n.func)) for n in ast.walk(tree) if isinstance(n,ast.Call) and any(x in ast.unparse(n.func) for x in ('read_','write_','open','connect','invoke','run','glob','loads','dump','exec','compile'))]
 elif p.suffix in ('.json','.yaml','.ipynb'):
  duplicates=[]
  def pairs(ps):
   out={}
   for k,v in ps:
    if k in out:duplicates.append(k)
    out[k]=v
   return out
  data=yaml.safe_load(text) if p.suffix=='.yaml' else json.loads(text,object_pairs_hook=pairs)
  r['duplicate_json_keys']=duplicates;r['top_keys']=list(data) if isinstance(data,dict) else None
  r['data']=data
 elif p.suffix=='.md':
  r['headings']=[dict(line=i,text=s) for i,s in enumerate(text.splitlines(),1) if s.startswith('#')]
  r['claims']=[dict(line=i,text=s) for i,s in enumerate(text.splitlines(),1) if re.search(r'proof|guarantee|exact|not |bounded|future|fixture|kernel|admi|learn|residual|rust|measure|durab|persistence|score|converg|open|test',s,re.I)]
 else:r['text']=text
 rows.append(r)
(HERE/'additional_eis_pciv_remaining_scan.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Scanned',len(rows),'public pinned files; structural scan is not a full source-reading receipt.')
if len(sys.argv)>1:
 for r in rows:
  if r['path'].startswith(sys.argv[1]) and r['path'].endswith('.py'):
   print('\nFILE',r['path'],r['docstring'])
   for f in r['functions']:
    print('FUNCTION',f['name'],f['lines'],f['docstring'] or '')
    for a in f['assertions']:print(a['lines'],a['source'])
