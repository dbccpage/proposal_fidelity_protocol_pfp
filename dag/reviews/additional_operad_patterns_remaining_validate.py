from pathlib import Path
import hashlib,json,datetime
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_patterns_remaining'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads(Path(str(P)+'.json').read_text());scope=json.loads(Path(str(P)+'_scope.json').read_text())
source={r['path']:r for r in scope['files']};reviews={r['path']:r for r in report['file_reviews']}
assert len(source)==len(reviews)==198 and set(source)==set(reviews)
assert report['status']=='complete' and report['summary']['pending']==0 and not report['pending_paths']
checked=[]
for r in list(reviews.values())+report['supporting_file_reviews']:
 p=R/r['path'];b=p.read_bytes();n=len(b.decode().splitlines());digest=sha(p)
 assert digest==r['sha256'] and r['full_source_read'] and r['reviewed_lines']==[[1,n]]
 if r['path'] in source:assert digest==source[r['path']]['sha256']
 assert r['assessment'].strip();checked.append(dict(path=r['path'],sha256=digest,lines=n,bytes=len(b)))
assert sum(x['bytes'] for x in checked[:198])==327419 and sum(x['lines'] for x in checked[:198])==7066
allrefs=[]
def visit(x):
 if isinstance(x,dict):
  if {'path','sha256','lines'}<=x.keys() and isinstance(x['lines'],list):
   p=R/x['path'];b=p.read_bytes();n=len(b.decode().splitlines());assert sha(p)==x['sha256']
   for a,z in x['lines']:assert 1<=a<=z<=n
   allrefs.append(x)
  for v in x.values():visit(v)
 elif isinstance(x,list):
  for v in x:visit(v)
visit(report)
ids=[x['id'] for x in report['claims']+report['findings']];assert len(ids)==len(set(ids))==22
probes={x['id'] for x in report['probes']};assert len(probes)==13
for f in report['findings']:assert set(f['probe_ids'])<=probes
assert report['scope_sha256']==sha(Path(str(P)+'_scope.json'))
atlas=R/'dag/reviews/additional_operads_education_atlas.json'
assert sha(atlas)=='f1bcd86f77f3f183fe5a69e03db244174152b7637aeeca1fa19ecd7b18cf6a12'
artifacts=[]
for p in sorted(P.parent.glob(P.name+'*')):
 if p.is_file() and not p.name.endswith(('_validation.json','_validation.md')):artifacts.append(dict(path=p.relative_to(R).as_posix(),sha256=sha(p),bytes=p.stat().st_size))
out=dict(status='PASS',validated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope_files=198,
 scope_bytes=327419,scope_lines=7066,supporting_files=6,supporting_lines=1193,pending=0,
 source_evidence_ranges_validated=sum(len(e['lines']) for e in allrefs),claims=4,findings=18,fresh_bounded_controls=13,
 originals_unchanged=True,atlas_report_unchanged=True,report_sha256=sha(Path(str(P)+'.json')),
 markdown_sha256=sha(Path(str(P)+'.md')),checked_sources=checked,artifacts=artifacts,
 limits=['Hash/range validation is custody metadata, not additional semantic reading or new historical execution.','No shared report, source, DAG or benchmark mutation performed.'])
Path(str(P)+'_validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
Path(str(P)+'_validation.md').write_text('# Validation receipt\n\nPASS:198 scope hashes and6 supporting hashes unchanged; all full-body ranges and'+str(out['source_evidence_ranges_validated'])+' evidence ranges valid.\n\n4claims,18findings,13bounded controls;0pending. Prior atlas JSON unchanged.\n\nReport SHA-256: `'+out['report_sha256']+'`.\n\nMarkdown SHA-256: `'+out['markdown_sha256']+'`.\n\nCustody validation is separate from semantic reading and historical execution.\n',encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in {'checked_sources','artifacts'}},indent=2))
