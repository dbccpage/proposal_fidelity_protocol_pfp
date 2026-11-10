"""Freeze metadata and an explicit index; parsing does not give semantic credit."""
import ast,collections,hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';s=json.loads((H/(P+'_scope.json')).read_text());rows=[]
for i,f in enumerate(s['files']):
 raw=(R/f['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==f['sha256'];assert len(raw)==f['bytes'];row={'index':i,**f};suffix=pathlib.PurePosixPath(f['path']).suffix
 if suffix=='.jpg':row.update(kind='binary_image',lines=None)
 else:
  text=raw.decode('utf8');row.update(kind='text',lines=len(text.splitlines()))
  if suffix=='.py':
   try:
    tree=ast.parse(text);row['python_top_nodes']=[{'kind':type(n).__name__,'name':getattr(n,'name',None),'lines':[n.lineno,n.end_lineno]}for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))]
   except SyntaxError as exc:row['syntax_error']=str(exc)
 rows.append(row)
(H/(P+'_preparation.json')).write_text(json.dumps({'source_commit':s['source_commit'],'files':rows,'semantic_credit':False},indent=2)+'\n')
print(json.dumps({'files':len(rows),'bytes':sum(r['bytes']for r in rows),'text_lines':sum(r['lines']or 0 for r in rows),'extensions':dict(collections.Counter(pathlib.PurePosixPath(r['path']).suffix for r in rows))}))
