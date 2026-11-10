"""Bound source equality and artifact inventory; this is not reading credit."""
from pathlib import Path
import difflib
import hashlib
import json
import zipfile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'dag/reviews'
OUT = REV/'paper_005_support_inspection'
OUT.mkdir(exist_ok=True)
PREFIX = 'papers/pfp/005_pfp_practitioners_field_manual/'
scope = json.loads((REV/'additional_paper_005_support_scope.json').read_text())
pins = {x['path']:x for x in scope['files']}
for row in scope['files']:
    assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest() == row['sha256']
base_report = json.loads((REV/'additional_paper_003_support.json').read_text())
base_prefix = 'papers/pfp/003_pfp_host_admitted_failure_detectors/'
base_rows = {x['path']:x for x in base_report['file_reviews']}
common = []
for rel in ['LICENSE','LICENSE-CODE','code/deposit_paths.py','scripts/build_deposit_zip.py',
            'scripts/regen_sha256sums.py','tools/rebuild_release.py','verify_deposit.py']:
    source, base = PREFIX+rel,base_prefix+rel
    raw, old = (ROOT/source).read_bytes(),(ROOT/base).read_bytes()
    row = base_rows[base]
    assert row['full_source_read'] and hashlib.sha256(old).hexdigest() == row['sha256']
    delta = list(difflib.unified_diff(old.decode('utf-8-sig').splitlines(),raw.decode('utf-8-sig').splitlines(),fromfile=base,tofile=source,lineterm=''))
    common.append({'path':source,'sha256':pins[source]['sha256'],'base_path':base,
        'base_report':'dag/reviews/additional_paper_003_support.json','base_assessment':row['assessment'],
        'byte_equal':raw==old,'full_text_delta':delta})
(OUT/'shared_source_comparisons.json').write_text(json.dumps(common,indent=2)+'\n',encoding='utf-8')
pdfs = []
for row in scope['files']:
    if not row['path'].endswith('.pdf'): continue
    reader = PdfReader(ROOT/row['path'])
    index = len(pdfs)
    text = '\n\n'.join(f'PAGE {i+1}\n'+(p.extract_text() or '') for i,p in enumerate(reader.pages))
    (OUT/f'pdf_{index:02d}_text.txt').write_text(text,encoding='utf-8')
    pdfs.append({'pdf':row['path'],'sha256':row['sha256'],'pages':len(reader.pages)})
(OUT/'pdf_inventory.json').write_text(json.dumps(pdfs,indent=2)+'\n',encoding='utf-8')
zip_row = next(x for x in scope['files'] if x['path'].endswith('.zip'))
with zipfile.ZipFile(ROOT/zip_row['path']) as archive:
    members = []
    for item in archive.infolist():
        if item.is_dir(): continue
        data = archive.read(item)
        members.append({'name':item.filename,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(OUT/'archive_inventory.json').write_text(json.dumps({'archive':zip_row,'members':members,'limit':'Inventory only; no full archive-member review asserted.'},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'common':common,'pdfs':pdfs,'archive_members':len(members)},indent=2))
