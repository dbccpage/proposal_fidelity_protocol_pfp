"""Persist explicitly reviewed notes and findings; no automated semantic promotion."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent
P='additional_rust_functional_certifiers'
def read(s):return json.loads((HERE/(P+s)).read_text())
scope=read('_scope.json');notes=read('_notes.json');supp=read('_supplement.json')if (HERE/(P+'_supplement.json')).exists()else{}
rows=[]
for s in scope['files']:
 assert hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()==s['sha256']
 rows.append({'path':s['path'],'sha256':s['sha256'],'full_source_read':s['path']in notes,'reviewed_lines':[[1,s['lines']]]if s['path']in notes else[],'assessment':notes.get(s['path'],'Pending substantive review; inventory and emission are not semantic evidence.')})
d={'source_commit':scope['source_commit'],'status':'complete'if len(notes)==len(rows)else'in_progress','scope':{'files':len(rows),'bytes':sum(s['bytes']for s in scope['files']),'lines':sum(s['lines']for s in scope['files']),'full_source_reads':len(notes),'pending':len(rows)-len(notes)},'claims':supp.get('claims',[]),'findings':supp.get('findings',[]),'validation':supp.get('validation',[]),'file_reviews':rows,'remaining_work':[s for s in scope['files']if s['path']not in notes]}
(HERE/(P+'.json')).write_text(json.dumps(d,indent=2)+'\n')
(HERE/(P+'.md')).write_text(f"# Rust functional and certifier audit — {d['status']}\n\nPinned source8050c66900899771766f33e8f5fdd200b7dd9120. Frozen scope64 original files (50 crate files,14 shared tests/fixtures),31,002 lines. {len(notes)} full source reads; {len(rows)-len(notes)} pending. Per-file hashes, assessments and remaining paths are in the JSON.\n\nExact Phi1 primal-dual checks, generic LP certificates, floating diagnostics and authority metadata are distinct evidence classes. The form verifier assumes a full supplied generating family; it does not discover or bind an intended external carrier. No original source edits, provider calls or private benchmark access. This is a continuing checkpoint until all64 files are reviewed.\n")
print(json.dumps(d['scope']))
