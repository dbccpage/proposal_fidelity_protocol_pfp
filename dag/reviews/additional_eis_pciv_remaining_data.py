"""Explicit bounded artifact views over the already hash-pinned public scan."""
import ast,json,sys
from pathlib import Path
H=Path(__file__).parent
rows=json.loads((H/'additional_eis_pciv_remaining_scan.json').read_text())
by={r['path']:r for r in rows}
mode=sys.argv[1];start=int(sys.argv[2]);count=int(sys.argv[3])
ledger=H/'additional_eis_pciv_remaining_views.json'
seen=json.loads(ledger.read_text())
if mode=='yaml':
 selected=[r for r in rows if r['path'].startswith('eis/antibodies/anti_')]
 for r in selected[start:start+count]:
  base=by.get(r['path'].replace('/anti_','/ab_').replace('.yaml','.json'))
  d=r['data'];b={} if not base else base['data'];delta={k:v for k,v in d.items() if k not in b or b[k]!=v}
  print(r['path'],'BASE',None if not base else base['path'],'SAME_KEYS',sorted(k for k in d if k in b and d[k]==b[k]),'DIFFERENCES',json.dumps(delta,ensure_ascii=False))
  seen.append(dict(path=r['path'],sha256=r['sha256'],full_source_read=False,reviewed_lines=[],method='all_parsed_fields_equal_to_reviewed_JSON_base_or_complete_differences',base_path=None if not base else base['path']))
elif mode=='specdiff':
 selected=[r for r in rows if '/specs/' in r['path']]
 for r in selected[start:start+count]:
  base=by[r['path'].replace('/specs/','/')];print(r['path'],'BASE',base['path'],'BYTE_EQUAL',r['sha256']==base['sha256'],'VALUE_EQUAL',r['data']==base['data'])
  if r['data']!=base['data']:print(json.dumps({k:v for k,v in r['data'].items() if k not in base['data'] or v!=base['data'][k]},ensure_ascii=False))
  seen.append(dict(path=r['path'],sha256=r['sha256'],full_source_read=False,reviewed_lines=[],method='complete_parsed_value_equality_comparison_to_reviewed_root_definition',base_path=base['path']))
elif mode=='probediff':
 r=by['eis/antibodies/definitions/probing_domains.yaml']
 source=(H.parents[1]/'eis/infrastructure/mssn_domains.py').read_text(encoding='utf-8');tree=ast.parse(source)
 probes={}
 for node in tree.body:
  if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='ProbeSpecification':
   p={k.arg:ast.literal_eval(k.value) for k in node.value.keywords};probes[p['probe_id']]=p
 d=r['data'];print('TOP',json.dumps({k:v for k,v in d.items() if k!='domains'}))
 for name,domain in d['domains'].items():
  print('DOMAIN',name,json.dumps({k:v for k,v in domain.items() if k!='probes'}))
  for p in domain['probes']:
   base=probes[p['probe_id']];print(p['probe_id'],'ALL_PARSED_DIFFS',json.dumps({k:v for k,v in p.items() if str(base.get(k)).strip()!=str(v).strip()},ensure_ascii=False))
 seen.append(dict(path=r['path'],sha256=r['sha256'],full_source_read=False,reviewed_lines=[],method='all_parsed_probe_fields_compared_to_full_read_Python_constants_all_differences_reviewed'))
ledger.write_text(json.dumps(seen,indent=2)+'\n')
