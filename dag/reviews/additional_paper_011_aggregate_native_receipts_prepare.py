"""Read-only frozen-population inventory; parsing is not full semantic review."""
import collections, hashlib, json
from pathlib import Path
H=Path(__file__).resolve().parent; R=H.parents[1]
P='additional_paper_011_aggregate_native_receipts'
scope_path=H/(P+'_scope.json'); scope=json.loads(scope_path.read_text(encoding='utf-8'))
rows=[]; groups=collections.defaultdict(list)
for entry in scope['files']:
    p=entry['path']; raw=(R/p).read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    assert sha==entry['sha256'] and len(raw)==entry['bytes'],p
    rel=p.split('/docs/',1)[1]; group=rel.split('/')[0]
    row={**entry,'relative':rel,'group':group}
    try:
        text=raw.decode('utf-8'); row['lines']=len(text.splitlines());row['utf8']=True
    except UnicodeDecodeError: row['utf8']=False;text=None
    if text is not None and p.endswith(('.json','.jsonl')):
        try:
            value=json.loads(text) if p.endswith('.json') else [json.loads(l) for l in text.splitlines() if l.strip()]
            row['parsed_type']=type(value).__name__
            row['top_keys']=list(value) if isinstance(value,dict) else None
            row['records']=len(value) if isinstance(value,list) else None
            if isinstance(value,list):row['record_key_counts']=dict(collections.Counter('|'.join(sorted(x)) if isinstance(x,dict) else type(x).__name__ for x in value))
        except Exception as e:row['parse_error']=str(e)
    rows.append(row);groups[group].append(row)
result={'scope_sha256':hashlib.sha256(scope_path.read_bytes()).hexdigest(),'source_commit':scope['source_commit'],'files':rows,'summary':{'files':len(rows),'bytes':sum(x['bytes'] for x in rows),'extensions':dict(collections.Counter(Path(x['path']).suffix for x in rows)),'groups':{g:{'files':len(v),'bytes':sum(x['bytes'] for x in v),'lines':sum(x.get('lines',0) for x in v)} for g,v in groups.items()}}}
(H/(P+'_preparation.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result['summary'],indent=2))
for group,rs in groups.items():
    print('\nGROUP',group)
    for r in rs:print(r['relative'],r['bytes'],r.get('lines'),r.get('records'),r.get('top_keys',[]))
