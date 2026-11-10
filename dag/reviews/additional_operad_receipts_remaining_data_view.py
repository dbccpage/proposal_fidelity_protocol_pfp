import json,sys,re,collections
from pathlib import Path
P=Path(__file__).with_name('additional_operad_receipts_remaining_data_inspection.json');data=json.loads(P.read_text())['files']
lo,hi=map(int,sys.argv[1:3])
for r in data:
 if not lo<=r['index']<=hi:continue
 print('\nDATA',r['index'],r['path'])
 if 'parse_error' in r:print(r['parse_error']);continue
 print('SHAPE',r['top_type'],r['top_length'],'KEYS',','.join(r['top_keys'] or []))
 vals=[(v['location'],v['value']) for v in r['status_fields'] if len(v['location'].split('/'))<5]
 print('STATUS',json.dumps(vals[:15],ensure_ascii=False))
 print('ARRAYS',[(v['location'],v['length']) for v in r['arrays'] if len(v['location'].split('/'))<=3][:12])
 prose=[v for v in r['narrative_fields'] if not re.search(r'/(?:source_pins|files|artifacts|preserved_observed_inputs|changes|epics|prior_epic_inventory|source_snapshots)/',v['location'])]
 prose=list({v['value']:v for v in prose if not re.match(r'^(?:workflows_agents_skills|operads|product_planning_office)/',v['value'])}.values())
 for v in prose[:5]:print('PROSE',v['location'],json.dumps(v['value'],ensure_ascii=False))
 if len(prose)>5:print('PROSE_REMAINDER',len(prose)-5,'not displayed; bounded disposition')
 cmds=r['command_fields'];print('COMMANDS',len(cmds),[[x for x in v['value'] if isinstance(x,str) and (x in ['pytest','cargo','build','test','check','--write','--check','--offline','--locked'] or x.endswith('.py') or '::test_' in x)][:8] for v in cmds[:1]])
 pins=r['pins'];print('CHECKS','dups',len(r['duplicate_decoded_keys']),'nonfinite',len(r['nonfinite_tokens']),'pins',len(pins),'resolved',sum('hash_matches' in p for p in pins),'raw',sum('raw' in p.get('hash_matches',[]) for p in pins),'normalized_only',sum(bool(p.get('hash_matches')) and 'raw' not in p['hash_matches'] for p in pins),'mismatch',sum('hash_matches' in p and not p['hash_matches'] for p in pins),'before_after',r['before_after'])
