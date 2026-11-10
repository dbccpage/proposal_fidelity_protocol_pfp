"""Prepare existing public PDF for page-by-page reading; no rebuild or credit."""
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence'
OUT=ROOT/'dag/reviews/paper_011_support_inspection'
PDF=BASE/'paper.pdf'
render=OUT/'pdf_render';render.mkdir(exist_ok=True)
reader=PdfReader(PDF)
(OUT/'pdf_text.txt').write_text('\n\n'.join(f'PAGE {i+1}\n'+(p.extract_text() or '') for i,p in enumerate(reader.pages)),encoding='utf-8')
poppler=Path(r'C:\Users\a343o\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
subprocess.run([str(poppler),'-scale-to','1400','-png',str(PDF),str(render/'page')],check=True,capture_output=True,timeout=60)
pages=sorted(render.glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]))
assert len(pages)==len(reader.pages)
sheets=[]
for offset in range(0,len(pages),4):
    sheet=Image.new('RGB',(2000,2900),'white');draw=ImageDraw.Draw(sheet)
    for i,page in enumerate(pages[offset:offset+4]):
        with Image.open(page) as im:thumb=im.convert('RGB');thumb.thumbnail((990,1400))
        x,y=(i%2)*1000,(i//2)*1450
        draw.text((x+10,y+5),f'Page {offset+i+1}',fill='black')
        sheet.paste(thumb,(x+(1000-thumb.width)//2,y+25))
    dest=render/f'sheet-{offset//4+1:02d}.png';sheet.save(dest);sheets.append(dest.relative_to(ROOT).as_posix())
receipt={'pdf':PDF.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'pages':len(pages),'metadata':dict(reader.metadata or {}),'sheets':sheets,'limit':'Preparation only; no substantive reading or visual review credit.'}
(OUT/'pdf_preparation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt))
