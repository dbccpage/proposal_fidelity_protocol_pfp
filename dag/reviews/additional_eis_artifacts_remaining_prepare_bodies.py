"""Lossless parsed-body/template material for the two continuing reviews."""
from pathlib import Path
import collections,difflib,hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_eis_artifacts_remaining'
def h(b):return hashlib.sha256(b).hexdigest()
s=json.loads(Path(str(P)+'_scope.json').read_bytes())['files']
def read(i):
 b=(R/s[i]['path']).read_bytes();assert h(b)==s[i]['sha256'];return b,json.loads(b)
catalog_raw,catalog=read(104);a=catalog['antibodies'];checks=json.loads(Path(str(P)+'_catalog_checks.json').read_bytes())
root_transfers=[];remaining=dict(a)
for c in checks['root_comparisons']:
 if not c['catalog_present']:continue
 raw,base=read(c['index']);ident=c['id']
 if a[ident]['failure_class']=='general_obstruction':continue
 reconstructed=dict(base)
 for key,d in (c['delta'] or {}).items():
  if key not in a[ident]:reconstructed.pop(key,None)
  else:reconstructed[key]=d['catalog']
 assert reconstructed==a[ident]
 root_transfers.append({'catalog_id':ident,'base_path':s[c['index']]['path'],'base_sha256':h(raw),'base_full_read_ledger':'dag/reviews/additional_eis_artifacts_remaining_read_ledger.json','delta':c['delta'],'delta_display':'complete ROOT DIFFERENCES output from inspect.py catalog; no omitted differences','equality_checked':True})
 remaining.pop(ident)
groups=collections.defaultdict(list)
for k,v in remaining.items():groups[(v['failure_class'],tuple(v.keys()))].append((k,v))
lines=[];descriptors=[]
for groupno,(g,items) in enumerate(groups.items()):
 cls,keys=g
 derived={}
 if cls=='general_obstruction':
  derived={'description':['Custom obstruction defect: ','target_pattern'],'negative_fixture':['Failing specimen: ','target_pattern'],'positive_fixture':['Repaired invariant for ','target_pattern']}
  assert all(all(v[k]==prefix+v[field] for k,(prefix,field) in derived.items()) for _,v in items)
 constant={k:items[0][1][k] for k in keys if k not in derived and all(v[k]==items[0][1][k] for _,v in items)}
 variable=[k for k in keys if k not in derived and k not in constant and k!='antibody_id']
 descriptor={'group':groupno,'failure_class':cls,'count':len(items),'original_field_order':list(keys),'constant_fields':constant,'derived_fields':derived,'row_fields':['catalog_key_and_antibody_id']+variable}
 descriptors.append(descriptor);lines.append(json.dumps({'template':descriptor},ensure_ascii=False))
 for ident,v in items:
  assert ident==v['antibody_id'];row=[ident]+[v[k] for k in variable]
  rebuilt={**constant,'antibody_id':ident,**dict(zip(variable,row[1:]))}
  for k,(prefix,field) in derived.items():rebuilt[k]=prefix+rebuilt[field]
  assert rebuilt==v
  lines.append(json.dumps({'group':groupno,'values':row},ensure_ascii=False))
residual_path=Path(str(P)+'_catalog_residuals.jsonl');residual_path.write_text('\n'.join(lines)+'\n',encoding='utf8')
manifest={'source':s[104],'method':'Full-read root bases plus completely displayed field deltas; remaining parsed record bodies reconstructed from explicit constant/derived template and EVERY residual field value. Reading ledger must cover all residual lines before semantic full-body credit. Raw formatting is custody-pinned, not separately re-displayed.','root_transfers':root_transfers,'root_transfer_count':len(root_transfers),'residual_records':len(remaining),'residual_artifact':str(residual_path.relative_to(R)).replace('\\','/'),'residual_sha256':h(residual_path.read_bytes()),'residual_lines':len(lines),'templates':descriptors,'metadata_outside_antibodies':{k:v for k,v in catalog.items() if k!='antibodies'}}

log_raw,log=read(144);rawlines=log_raw.decode().splitlines();texts={}
for n in (221,240,478):
 text=json.loads('{'+rawlines[n-1].rstrip(',')+'}')['output_utf8'];texts[n]=text
base=texts[221];base_path=Path(str(P)+'_warning_base221.txt');base_path.write_text(base,encoding='utf8',newline='')
log_manifest={'source':s[144],'base_raw_line':221,'base_decoded_sha256':h(base.encode()),'base_artifact':str(base_path.relative_to(R)).replace('\\','/'),'base_characters':len(base),'deltas':[],'method':'Lossless JSON-string decode; exact decoded base plus all replacement spans reconstructs each remaining output_utf8 string. No log execution or authenticity claim.'}
for n in (240,478):
 target=texts[n];base_lines=base.splitlines(keepends=True);target_lines=target.splitlines(keepends=True);sm=difflib.SequenceMatcher(None,base_lines,target_lines,autojunk=False);deltas=[]
 for tag,i,j,k,l in sm.get_opcodes():
  if tag!='equal':deltas.append({'base_char_start':sum(map(len,base_lines[:i])),'base_char_end':sum(map(len,base_lines[:j])),'replacement':''.join(target_lines[k:l])})
 rebuilt=base
 for d in reversed(deltas):rebuilt=rebuilt[:d['base_char_start']]+d['replacement']+rebuilt[d['base_char_end']:]
 assert rebuilt==target
 dp=Path(str(P)+f'_warning_delta{n}.json');dp.write_text(json.dumps(deltas,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 log_manifest['deltas'].append({'raw_line':n,'decoded_sha256':h(target.encode()),'delta_artifact':str(dp.relative_to(R)).replace('\\','/'),'delta_sha256':h(dp.read_bytes()),'delta_spans':len(deltas),'replacement_chars':sum(len(x['replacement']) for x in deltas),'reconstruction_equal':True})
Path(str(P)+'_body_transfer_manifest.json').write_text(json.dumps({'catalog':manifest,'warning_logs':log_manifest},indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print(json.dumps({'catalog_root_transfers':len(root_transfers),'catalog_residual_records':len(remaining),'catalog_residual_lines':len(lines),'catalog_residual_bytes':residual_path.stat().st_size,'template_groups':len(groups),'warning_base_chars':len(base),'warning_deltas':log_manifest['deltas']},indent=2))
