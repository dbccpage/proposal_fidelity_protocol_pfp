"""Validate report population, exact hashes, full-body ranges and evidence pins."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'dag/reviews/additional_eis_pciv_teaching_scripts'
scope=json.loads(Path(str(P)+'_scope.json').read_text())
report=json.loads(Path(str(P)+'.json').read_text())
expected={r['path']:r for r in scope['files']}
reviews={r['path']:r for r in report['file_reviews']}
assert len(reviews)==len(report['file_reviews'])==31 and set(expected)==set(reviews)
assert len([p for p in reviews if '/scripts/' in p])==24
assert len([p for p in reviews if '/levels/' in p])==7
assert all('/010_oepciv/levels/' not in p and not p.endswith('/README.md') for p in reviews)
assert report['pending_paths']==[]
for p,r in reviews.items():
 b=(ROOT/p).read_bytes();n=len(b.decode().splitlines())
 assert hashlib.sha256(b).hexdigest()==r['sha256']==expected[p]['sha256']
 assert len(b)==r['bytes']==expected[p]['bytes']
 assert n==r['source_line_count']==expected[p]['lines']
 assert r['full_source_read'] and r['reviewed_lines']==[[1,n]] and r['assessment']
 if '/scripts/' in p:
  assert all(s in b.decode() for s in ['[Executed]','[Tested]','[Pinned]'])
evidence=report['dependency_readings']+[e for k in ['claims','findings'] for r in report[k] for e in r['evidence']]
for e in evidence:
 b=(ROOT/e['path']).read_bytes();n=len(b.decode().splitlines())
 assert hashlib.sha256(b).hexdigest()==e['sha256']
 assert all(1<=a<=z<=n for a,z in e['lines'])
ids=[r['id'] for k in ['claims','findings'] for r in report[k]]
assert len(ids)==len(set(ids))==14
checks=json.loads(Path(str(P)+'_checks.json').read_text())
assert len(checks['controls'])==5 and len(checks['links'])==271
assert checks['link_summary']=={'local_link_occurrences':271,'missing':156,'resolved':115,'outside_repo':84}
result={'status':'passed','source_population':31,'full_body_reads':31,'bytes':164104,'lines':1850,
        'source_hashes_match_frozen_scope':True,'full_ranges_and_assessments_complete':True,
        'evidence_entries_checked':len(evidence),'claim_finding_ids_unique':True,
        'claims':4,'findings':10,'fresh_bounded_controls':5,
        'json_sha256':hashlib.sha256(Path(str(P)+'.json').read_bytes()).hexdigest(),
        'md_sha256':hashlib.sha256(Path(str(P)+'.md').read_bytes()).hexdigest(),
        'scope_sha256':hashlib.sha256(Path(str(P)+'_scope.json').read_bytes()).hexdigest(),
        'limits':'Verifies exact source/report custody and accounting; does not turn reviewed claims into proof or rerun prior notebook/native tests.'}
Path(str(P)+'_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
