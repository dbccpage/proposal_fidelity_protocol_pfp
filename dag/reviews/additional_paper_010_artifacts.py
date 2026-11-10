"""Extract existing PDF text and render pages; no source regeneration."""
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'papers/pfp/010_pfp_holonomy_checks_and_model_pilots'
OUT = ROOT/'dag/reviews/paper_010_support_inspection'
paths = [BASE/'010_paper.pdf',BASE/'010_pfp_examiner_companion.pdf']
paths += [p for p in sorted(BASE.rglob('*.pdf')) if p not in paths]
inventory = []
for i,p in enumerate(paths):
    reader = PdfReader(p)
    text = '\n\n'.join(f'PAGE {j+1}\n'+(page.extract_text() or '') for j,page in enumerate(reader.pages))
    dest = OUT/f'pdf_{i:02d}_text.txt'
    dest.write_text(text,encoding='utf-8')
    inventory.append({'pdf':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                      'pages':len(reader.pages),'text':dest.relative_to(ROOT).as_posix()})
(OUT/'pdf_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
source = ROOT/'dag/reviews/additional_paper_005_render.py'
render = ROOT/'dag/reviews/additional_paper_010_render.py'
render.write_text(source.read_text().replace('paper_005_support_inspection','paper_010_support_inspection'),encoding='utf-8')
print(json.dumps(inventory,indent=2))
