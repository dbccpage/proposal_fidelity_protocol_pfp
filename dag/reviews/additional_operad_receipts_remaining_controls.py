"""Read-only, bounded artifact checks; does not import retained application code."""
from pathlib import Path
import collections,gzip,hashlib,json,re,yaml
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_receipts_remaining'
rows=json.loads(Path(str(P)+'_inventory.json').read_text())['files']; by={r['path']:r for r in rows}
def raw(i):return (R/rows[i]['path']).read_bytes()
def j(i):return json.loads(raw(i))
out={'execution_boundary':'Standard-library hashes, arithmetic, JSON/gzip and installed YAML parser only; no retained programs or native/provider calls.'}
sums=[]
for i in [335,341,432]:
 records=[]
 for line_no,line in enumerate(raw(i).decode().splitlines(),1):
  m=re.fullmatch(r'([a-f0-9]{64})  (.+)',line)
  if not m:records.append({'line':line_no,'syntax_valid':False});continue
  expected,ref=m.groups();candidates=[ref,ref.replace('workflows_agents_skills/receipts/','operads/receipts/'),(Path(rows[i]['path']).parent/ref).as_posix()]
  resolved=next((c for c in candidates if c in by),None)
  rec={'line':line_no,'declared_path':ref,'expected_sha256':expected,'current_path':resolved}
  if resolved:
   b=(R/resolved).read_bytes();lf=b.replace(b'\r\n',b'\n')
   rec['hash_matches']=[n for n,v in [('raw',b),('LF',lf),('CRLF',lf.replace(b'\n',b'\r\n'))] if hashlib.sha256(v).hexdigest()==expected]
  records.append(rec)
 counts=collections.Counter(r.get('declared_path') for r in records)
 sums.append({'index':i,'records':records,'summary':{'lines':len(records),'invalid':sum(not r.get('declared_path') for r in records),'duplicate_paths':{k:v for k,v in counts.items() if v>1},'resolved_scoped':sum(bool(r.get('current_path')) for r in records),'raw_match':sum('raw' in r.get('hash_matches',[]) for r in records),'normalized_only_match':sum(bool(r.get('hash_matches')) and 'raw' not in r['hash_matches'] for r in records)}})
out['checksum_lists']=sums
y=yaml.safe_load(raw(350));files=y['files'];locs=collections.Counter(x.get('file_location') for x in files)
out['prior_art_catalog']={'index':350,'top_keys':list(y),'declared_summary':y['summary'],'actual_rows':len(files),'row_key_shapes':dict(collections.Counter(','.join(sorted(x)) for x in files)),'scores':dict(collections.Counter(str(x.get('relevance_score')) for x in files)),'folder_counts':dict(collections.Counter(x.get('folder') for x in files)),'duplicate_locations':{k:v for k,v in locs.items() if v>1},'missing_locations':sum(not x.get('file_location') for x in files),'referenced_bodies_read':False,'sample_first':files[0],'sample_last':files[-1]}
g=gzip.decompress(raw(497));text=g.decode('utf8',errors='replace');lines=text.splitlines()
out['gzip_log']={'index':497,'uncompressed_bytes':len(g),'uncompressed_sha256':hashlib.sha256(g).hexdigest(),'lines':len(lines),'utf8_replacement_count':text.count('\ufffd'),'first_lines':[s[:350] for s in lines[:20]],'last_lines':[s[:350] for s in lines[-20:]],'error_lines':[{'line':i,'text':s[:350],'original_characters':len(s),'line_sha256':hashlib.sha256(s.encode()).hexdigest()} for i,s in enumerate(lines,1) if re.search(r'^(?:E\s|FAILED |ERROR |.*short test summary|=+.*(?:passed|failed|error))',s)][:100],'whole_text_human_read':False,'display_limit_characters_per_selected_line':350}
oracles=j(508)['digest_oracles'];out['literal_oracles']=[{'role':x['role'],'expected':x['sha256'],'actual':'sha256:'+hashlib.sha256(x['literal_utf8'].encode()).hexdigest(),'match':x['sha256']=='sha256:'+hashlib.sha256(x['literal_utf8'].encode()).hexdigest()} for x in oracles]
out['arithmetic_controls']={'overlapping_245_and_99_with_55_overlap':245+99-55,'concatenation_same_literal':'ab'+'c'=='a'+'bc','framed_sequences_distinct':json.dumps(['ab','c'])!=json.dumps(['a','bc'])}
data=json.loads(Path(str(P)+'_data_inspection.json').read_text())['files'];pins=[p for x in data for p in x.get('pins',[])];resolved=[p for p in pins if 'current_path' in p]
out['json_population']={'files':len(data),'parse_errors':[x for x in data if 'parse_error' in x],'nonfinite_files':sum(bool(x.get('nonfinite_tokens')) for x in data),'duplicate_key_files':[{'index':x['index'],'duplicates':x['duplicate_decoded_keys']} for x in data if x.get('duplicate_decoded_keys')],'pin_occurrences':len(pins),'resolved_scoped_occurrences':len(resolved),'raw_matching_occurrences':sum('raw' in p['hash_matches'] for p in resolved),'normalized_only_occurrences':sum(bool(p['hash_matches']) and 'raw' not in p['hash_matches'] for p in resolved),'unresolved_or_outside_scope_occurrences':len(pins)-len(resolved),'before_after_pairs':[{'index':x['index'],**p} for x in data for p in x.get('before_after',[])]}
Path(str(P)+'_controls.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
for key,v in out.items():
 if key=='checksum_lists':print(key,[{'index':x['index'],**x['summary']} for x in v])
 elif key=='gzip_log':print(key,{k:v for k,v in v.items() if k not in ['first_lines','last_lines','error_lines']});print('log excerpts',[(x['line'],x['text'][:300],len(x['text'])) for x in v['error_lines']]);print('tail',[(s[:250],len(s)) for s in v['last_lines']])
 elif key=='json_population':print(key,{k:v for k,v in v.items() if k not in ['duplicate_key_files','before_after_pairs']},'duplicatefiles',[x['index'] for x in v['duplicate_key_files']],'beforeafter',len(v['before_after_pairs']))
 else:print(key,json.dumps(v,ensure_ascii=False))
