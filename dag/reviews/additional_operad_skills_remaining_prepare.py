"""Freeze metadata and reading support; no semantic credit from parsing."""
import ast,collections,hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';s=json.loads((H/(P+'_scope.json')).read_text());rows=[];groups=collections.defaultdict(list)
for i,f in enumerate(s['files']):
 b=(R/f['path']).read_bytes();assert len(b)==f['size_bytes']and hashlib.sha256(b).hexdigest()==f['sha256'];t=b.decode('utf-8-sig');row={'index':i,'path':f['path'],'sha256':f['sha256'],'bytes':len(b),'lines':len(t.splitlines())};groups[f['sha256']].append(i)
 if f['path'].endswith('.py'):
  try:
   tree=ast.parse(t);row['top_nodes']=[{'kind':type(n).__name__,'name':getattr(n,'name',''),'lines':[n.lineno,n.end_lineno]}for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
  except SyntaxError as e:row['syntax_error']=str(e)
 rows.append(row)
(H/(P+'_preparation.json')).write_text(json.dumps({'source_commit':s['source_commit'],'files':rows,'exact_duplicate_groups':[v for v in groups.values()if len(v)>1],'semantic_credit':False},indent=2)+'\n');print(json.dumps({'files':len(rows),'bytes':sum(x['bytes']for x in rows),'lines':sum(x['lines']for x in rows),'exact_duplicate_groups':[v for v in groups.values()if len(v)>1],'extensions':dict(collections.Counter(pathlib.Path(x['path']).suffix for x in rows))}))
