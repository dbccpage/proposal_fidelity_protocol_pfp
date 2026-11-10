"""Read-only full-population checks on scoped historical data, not semantic proof."""
import collections, fractions, gzip, hashlib, json, pathlib, re
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_application_remaining';prep=json.loads((H/(P+'_preparation.json')).read_text())['files']; out={};data={}
IDS=[9,12,14,17,19,21,22,24,29,31,33,35,48]
def sha(b):return hashlib.sha256(b).hexdigest()
def load(i):
 b=(R/prep[i]['path']).read_bytes();assert sha(b)==prep[i]['sha256'];d=gzip.decompress(b)if prep[i]['path'].endswith('.gz')else b
 return [json.loads(l)for l in d.splitlines()]if '.jsonl'in prep[i]['path']else json.loads(d)
def count(rows,key):return dict(collections.Counter(str(x.get(key))for x in rows))
def unique(rows,key):return len(rows)==len({str(x[key])for x in rows})
for i in IDS:
 x=load(i);data[i]=x;out[str(i)]={'path':prep[i]['path'],'sha256':prep[i]['sha256'],'decoded_lines_scanned':prep[i]['lines'],'full_source_read':False,'semantic_credit':'bounded_data_population_only'}
 r=x.get('records',x)if isinstance(x,dict)else x
 if isinstance(x,dict):out[str(i)]['top_keys']=list(x);out[str(i)]['audit_mode']=x.get('audit_mode');out[str(i)]['base_commit']=x.get('base_commit')
 # Every nested source pin and range is inventoried, not opened or trusted.
 pins=[];ranges=[];bad=[]
 def walk(v,loc='$'):
  if isinstance(v,dict):
   if isinstance(v.get('path'),str) and any(k in v for k in ('sha256','source_sha256')):
    h=v.get('sha256',v.get('source_sha256'));pins.append({'location':loc,'path':v['path'],'sha256':h})
    if not isinstance(h,str)or not re.fullmatch('[0-9a-f]{64}',h):bad.append([loc,'hash_shape'])
   if 'line_start'in v and 'line_end'in v:
    a,b=v['line_start'],v['line_end'];ranges.append([loc,a,b]);
    if type(a)is not int or type(b)is not int or not(1<=a<=b):bad.append([loc,'range_shape',a,b])
   for k,z in v.items():walk(z,loc+'/'+str(k))
  elif isinstance(v,list):
   for j,z in enumerate(v):walk(z,loc+'/'+str(j))
 walk(x);groups=collections.defaultdict(set)
 for pin in pins:groups[pin['path']].add(str(pin['sha256']))
 out[str(i)]['nested_source_pin_count']=len(pins);out[str(i)]['distinct_source_paths']=len(groups);out[str(i)]['conflicting_path_hashes']={k:sorted(v)for k,v in groups.items()if len(v)>1};out[str(i)]['nested_range_count']=len(ranges);out[str(i)]['malformed_pin_or_range']=bad
 if i==9:
  out['9'].update(rows=len(r),unique_item_family_pairs=len({(q['item_id'],q['family'])for q in r})==len(r),families=count(r,'family'),roles=count(r,'role'),answer_correct=count(r,'answer_correct'),detectors={k:count([z[k]for z in r],'status')for k in r[0]if k.startswith('D')})
 if i==17:
  m=r['modules'];out['17'].update(modules=len(m),unique_paths=unique(m,'path'),static_test_functions=sum(z['test_count']for z in m),static_assertions=sum(z['assert_count']for z in m),execution=count(m,'execution_status'),collection=count(m,'collection_verified'),reported_summary=r['summary'])
 if i==19:out['19'].update(antibodies=len(r['antibodies']),unique_ids=unique(r['antibodies'],'id'),coverage=count(r['antibodies'],'coverage_status'),guard_equivalence=count(r['antibodies'],'runtime_guard_equivalence'))
 if i==21:out['21'].update(census_counts={k:len(r[k])for k in ['curriculum','pilots','adversary_modules','antibodies']},curriculum_files=sum(t['file_count']for t in r['curriculum']),pilot_ids=list(sorted(t['id']for t in r['pilots'])),materialization=count(r['pilots'],'materialization'),execution_flags={k:count(r[k],'executed_now')for k in ['curriculum','pilots','adversary_modules','antibodies']},reported_summary=r['summary'])
 if i in [22,24]:
  key='files'if i==22 else'file_inventory';tracks=r['tracks'];out[str(i)].update(tracks=[{'id':t.get('track',t.get('id')),'files':len(t[key]),'unique_paths':unique(t[key],'path'),'bytes':sum(q['bytes']for q in t[key])}for t in tracks],file_count=sum(len(t[key])for t in tracks))
 if i==29:out['29'].update(actual_populations={k:len(r[k])for k in ['yaml_files','python_modules','native_owner_inventory']},reported_census=r['census'],evidence_rows=len(r['evidence']),proposal_status=r['proposal_status'])
 if i==31:out['31'].update(pilots=len(r['pilots']),pilot_numbers=[z['pilot_number']for z in r['pilots']],model_verdict_rows=len(r['model_receipt_rows']),verdicts=count(r['model_receipt_rows'],'verdict'),file_digest_census=len(r['file_digest_census']),reported_summary=r['summary'])
 if i==33:out['33'].update(rows=len(r['rows']),requested_ids=r['requested_ids'],directory_status=count(r['rows'],'directory_status'),reported_summary=r['summary'])
 if i==48:out['48'].update(rows=len(r['files']),unique_paths=unique(r['files'],'path'),statuses=count(r['files'],'status'),review_partitions=count(r['files'],'review_partition'),review_depth=count(r['files'],'review_depth'),native_target_references=sum(len(q.get('rust_targets',[]))for q in r['files']))
# Raw call/trace joins, exact historical accounting, and factual summary consistency.
calls=data[12];traces=data[14];callmap={(x['item_id'],x['call']):x for x in calls};issues=[];cost=fractions.Fraction();usage=collections.Counter();primary=[x for x in traces if x['call']==0]
for n,t in enumerate(traces,1):
 c=callmap.get((t['item_id'],t['call']))
 if c is None:issues.append([n,'missing_call']);continue
 for name in ['request','response']:
  actual=sha(c[name].encode());expected=c[name+'_sha256']
  if actual!=expected or t[name+'_sha256']!=expected:issues.append([n,name+'_digest'])
 response=json.loads(c['response']);request=json.loads(c['request'])
 for key in ['input_tokens','output_tokens']:
  v=response.get('usage',{}).get(key)
  if v!=t[key]:issues.append([n,key+'_mismatch'])
  if type(t[key])is not int or t[key]<0:issues.append([n,key+'_invalid'])
  usage[key]+=t[key]
 if response.get('stop_reason')!=t['stop_reason']:issues.append([n,'stop_reason'])
 if request.get('max_tokens')!=1200:issues.append([n,'max_tokens'])
 cost+=fractions.Fraction(t['cost_usd'])
summary=load(13)
checks={'calls':len(calls),'traces':len(traces),'unique_call_keys':len(callmap)==len(calls),'unique_trace_keys':len({(t['item_id'],t['call'])for t in traces})==len(traces),'item_call_sets':dict(collections.Counter(str(sorted(t['call']for t in traces if t['item_id']==item))for item in {t['item_id']for t in traces})),'join_digest_usage_issues':issues,'usage_totals':dict(usage),'summed_recorded_cost':str(cost),'summary_cost_equal':cost==fractions.Fraction(summary['spent_usd']),'primary_rows':len(primary),'primary_failure':sum(t['failure']for t in primary),'primary_schema_invalid':sum(not t['schema_valid']for t in primary),'primary_max_tokens':sum(t['stop_reason']=='max_tokens'for t in primary),'all_stop_reasons':count(traces,'stop_reason'),'primary_stop_reasons':count(primary,'stop_reason'),'primary_by_detector':{d:{status:dict(collections.Counter('failure'if t['failure']else'success'for t in primary if t[d]['status']==status))for status in sorted({t[d]['status']for t in primary})}for d in ['d2','d3','d4']},'limits':'No fresh grading/model response/bootstrap, vendor authentication or invoice validation; exact sums of historical declared charges only.'}
out['12']['call_trace_checks']=checks;out['14']['call_trace_check_artifact']='same receipt:12.call_trace_checks'
# Compare source manifests against original inventory METADATA, never open arbitrary cited paths.
inventory=json.loads((R/'dag/file_inventory.json').read_text())['files'];inv={z['path']:z for z in inventory};ipins={z['path']:z['sha256']for z in prep}
for i,key in [(35,'sources'),(35,'artifacts'),(48,'files')]:
 rows=data[i][key];results=[]
 for row in rows:
  path=row['path'];expected=row.get('source_sha256',row.get('sha256'));observed=ipins.get(path,inv.get(path,{}).get('sha256'));results.append({'path':path,'expected':expected,'observed_inventory_sha256':observed,'status':'absent_original_inventory'if observed is None else'match'if expected==observed else'different_original_inventory'})
 out[str(i)][key+'_inventory_comparison']={'counts':count(results,'status'),'rows':results,'limit':'Original inventory metadata comparison only; older source snapshots, removed owners and relocation require original Git/archive resolution. Not a data-loss verdict.'}
# Scoped artifact digests plus newline-only controls.
custody=[]
for i in [8,27,45,46]:
 x=load(i)if i!=8 else None
 if i==8:
  pairs=[(str(pathlib.PurePosixPath(prep[8]['path']).parent/name),h)for h,name in (l.split()for l in (R/prep[8]['path']).read_text().splitlines())]
 elif i==27:pairs=[('pfp/documentation/oepfp_v1_1_rc_evidence/source_manifest.json',x['manifest_sha256'])]+[(q['output_artifact'],q['output_sha256'])for q in x['local_reference_tests'].values()if isinstance(q,dict)]
 else:pairs=[(k,v)for k,v in x['source_sha256'].items()if k in ipins]
 for path,h in pairs:
  if path not in ipins:continue
  b=(R/path).read_bytes();lf=b.replace(b'\r\n',b'\n');custody.append({'referrer':prep[i]['path'],'target':path,'expected':h,'observed':sha(b),'raw_match':sha(b)==h,'LF_projection_match':sha(lf)==h,'CRLF_projection_match':sha(lf.replace(b'\n',b'\r\n'))==h})
out['custody_controls']=custody
# Generated module table: compare ALL308 indexed hashes/counts with machine extraction.
lines=(R/prep[18]['path']).read_text(encoding='utf8').splitlines();table=[]
for n,line in enumerate(lines,1):
 if 355<=n<=662:
  m=re.search(r'\| (\d+)/(\d+)/(\d+) \|.*`([0-9a-f]{64})`',line);assert m,(n,line);table.append((n,*map(int,m.groups()[:3]),m.group(4)))
mods=data[17]['records']['modules'];out['18']={'path':prep[18]['path'],'sha256':prep[18]['sha256'],'table_lines':[355,662],'table_rows':len(table),'sum_test_counts':sum(t[1]for t in table),'sum_assert_counts':sum(t[2]for t in table),'hash_multiset_equal_machine_records':collections.Counter(t[4]for t in table)==collections.Counter(m['source_sha256']for m in mods),'full_source_read':False,'limit':'All narrative and selected endpoint rows read; entire generated table checked mechanically for row count, counts and hash multiset, not claimed as new semantic review of308 modules.'}
(H/(P+'_population.json')).write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'files':len(IDS),'stage_b':{k:v for k,v in checks.items()if k not in ['item_call_sets','primary_by_detector']},'custody_controls':custody,'module_table':out['18']},indent=2))
