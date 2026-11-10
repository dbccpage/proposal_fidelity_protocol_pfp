import hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics'
def get(s,default):
 p=H/(P+s);return json.loads(p.read_text())if p.exists()else default
s=get('_scope.json',{});notes=get('_notes.json',{});extra=get('_supplement.json',{})
templates={x['path']:x for x in get('_template_receipts.json',[])}
rows=[]
for x in s['files']:
 assert hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256']
 rows.append({'path':x['path'],'sha256':x['sha256'],'full_source_read':x['path']in notes,'reviewed_lines':[[1,x['lines']]]if x['path']in notes else[],'assessment':notes.get(x['path'],'Pending substantive review; inventory/hash/emission does not supply semantic reading.')})
 if x['path'] in templates and x['path'] in notes:
  t=templates[x['path']];rows[-1]['source_read_method']={'kind':'complete semantic body and all differences with previously read shared segments','receipt':P+'_template_receipts.json','canonical_path':t['canonical_path'],'canonical_sha256':t['canonical_sha256'],'reconstruction_sha256':t['reconstruction_sha256']}
d={'source_commit':s['source_commit'],'status':'complete'if len(notes)==len(rows)else'in_progress','scope':{'files':len(rows),'lines':sum(x['lines']for x in s['files']),'bytes':sum(x['bytes']for x in s['files']),'full_source_reads':len(notes),'pending':len(rows)-len(notes)},'claims':extra.get('claims',[]),'findings':extra.get('findings',[]),'validation':extra.get('validation',[]),'file_reviews':rows,'remaining_work':[x for x in s['files']if x['path']not in notes]}
(H/(P+'.json')).write_text(json.dumps(d,indent=2)+'\n');(H/(P+'.md')).write_text(f"# Rust quantum physics audit — {d['status']}\n\nPinned8050 source, {len(notes)}/{len(rows)} full source reads. Exact source hashes, per-file assessments, claim dependencies, findings and remaining scope are in the JSON. Inventory and emissions are not semantic review. Physical premises, supplied finite encodings, exact witnesses, floating diagnostics and proof labels are assessed separately. No original edits, private benchmark/seed/key, provider or download access.\n")
print(json.dumps(d['scope']))
