import sys,json,collections
sys.dont_write_bytecode=True
import additional_paper_011_history_formal_receipts_audit as a
def shape(x,depth=0):
    if isinstance(x,dict):
        if len(x)>80:return {'object_entries':len(x),'sample':{k:shape(v,depth+1) for k,v in list(x.items())[:2]}}
        if depth>=2:return {'object_entries':len(x),'keys':list(x)[:14]}
        return {k:shape(v,depth+1) for k,v in x.items()}
    if isinstance(x,list):return {'list_length':len(x),'sample':[shape(v,depth+1) for v in x[:2]]}
    if isinstance(x,str) and len(x)>220:return x[:220]+'...'
    return x
if len(sys.argv)>1:
    r=a.row(sys.argv[1]);x=json.loads((a.ROOT/r['path']).read_text(encoding='utf-8-sig'));print(json.dumps(shape(x),indent=2))
else:
    groups=collections.defaultdict(list)
    for r in a.read('_scope.json')['files']:
        if not r['path'].endswith('.json'):continue
        x=json.loads((a.ROOT/r['path']).read_text(encoding='utf-8-sig'));key=('hash_map',) if isinstance(x,dict) and len(x)>80 else tuple(x) if isinstance(x,dict) else ('array',)
        groups[key].append(r['path'].split('/history_recovery/')[1])
    for k,v in groups.items():print(len(v),v[:3],str(k)[:1600])
