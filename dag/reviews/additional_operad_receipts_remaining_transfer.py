from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_receipts_remaining'
rows=json.loads(Path(str(P)+'_inventory.json').read_text())['files'];p=Path(str(P)+'_notes.json');d=json.loads(p.read_text());notes=d['assessments'];bases={}
for r in rows:
 if str(r['index']) in notes and notes[str(r['index'])].get('full_source_read',True):bases.setdefault(r['sha256'],r)
added=[]
for r in rows:
 k=str(r['index']);b=bases.get(r['sha256'])
 if k in notes or not b:continue
 assert (R/r['path']).read_bytes()==(R/b['path']).read_bytes()
 context=('Captured observed-red input: a retained pre-repair state, not a fresh passing implementation.' if '/observed_red_inputs/' in r['path'] else 'Captured refused-manifest input: kept as refused-state custody, not accepted current production.' if '/refused_manifest_inputs/' in r['path'] else 'Predecessor capture: prior state retained for provenance, not renewed implementation evidence.' if '/predecessor_inputs/' in r['path'] else 'Repeated campaign-local custody policy or captured source; identical bytes do not establish independent execution.')
 notes[k]=dict(assessment=context+' Exact complete-body equality with reviewed '+b['path']+'. '+notes[str(b['index'])]['assessment'],base_index=b['index'],base_sha256=b['sha256'],reading_method='exact byte equality to fully reviewed base plus explicit capture-context assessment',review_level='full_source_via_exact_reviewed_base_with_context')
 added.append([r['index'],b['index']])
p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8');print(json.dumps(added))
