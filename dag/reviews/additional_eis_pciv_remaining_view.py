"""Emit bounded structural views; preserve their weaker review status."""
import json,sys
from pathlib import Path
HERE=Path(__file__).parent
rows=json.loads((HERE/'additional_eis_pciv_remaining_scan.json').read_text(encoding='utf-8'))
prefix,start,count=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
mode=sys.argv[4] if len(sys.argv)>4 else 'auto'
rows=[r for r in rows if r['path'].startswith(prefix)]
if mode=='tests':rows=[r for r in rows if r['path'].endswith('.py') and '/tests/' in r['path'] and not r['path'].endswith('__init__.py')]
if mode=='docs':rows=[r for r in rows if r['path'].endswith('.md')]
if mode=='data':rows=[r for r in rows if 'data' in r]
seen_path=HERE/'additional_eis_pciv_remaining_views.json'
seen=json.loads(seen_path.read_text()) if seen_path.exists() else []
for r in rows[start:start+count]:
 print('FILE',r['path'],'TOTAL',r['lines'])
 ranges=[]
 if mode=='tests':
  print('DOC',r['docstring']);print('IMPORTS','; '.join(r['imports']))
  for f in r['functions']:
   print('FUNCTION',f['name'],f['lines'],f['docstring'] or '')
   for a in f['assertions']:print(a['lines'],a['source']);ranges.append(a['lines'])
  method='all_test_assertion_and_raises_AST_view_imports_function_inventory_not_full_body'
 elif mode=='docs':
  emitted={x['line']:x['text'] for x in r['headings']+r['claims']}
  for line,text in sorted(emitted.items()):print(str(line)+': '+text);ranges.append([line,line])
  method='selected_documentation_claim_lines_not_full_body'
 else:
  print(json.dumps(r.get('data',r),ensure_ascii=False,separators=(',',':')))
  method='complete_parsed_value_view_not_raw_text' if 'data' in r else 'structural_metadata_view'
 seen.append(dict(path=r['path'],sha256=r['sha256'],method=method,reviewed_lines=ranges,full_source_read=False))
seen_path.write_text(json.dumps(seen,indent=2)+'\n',encoding='utf-8')
print('RANGE',start,min(start+count,len(rows)),'OF',len(rows))
