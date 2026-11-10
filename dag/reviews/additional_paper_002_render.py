"""Render existing editions and compare complete page pixels; never rebuild PDFs."""
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name('paper_002_support_inspection')
POPLER = Path(r'C:\Users\a343o\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
inventory = json.loads((OUT / 'pdf_inventory.json').read_text())
records = []
for index, item in enumerate(inventory):
    source = ROOT / item['pdf']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == item['sha256']
    folder = OUT / f'render_{index:02d}'
    folder.mkdir(exist_ok=True)
    subprocess.run([str(POPLER), '-scale-to', '1200', '-png', str(source), str(folder / 'page')], check=True, capture_output=True, timeout=60)
    pages = sorted(folder.glob('page-*.png'), key=lambda p: int(p.stem.split('-')[-1]))
    assert len(pages) == item['pages']
    sheets, page_rows = [], []
    reader = PdfReader(source)
    for i, page in enumerate(pages):
        with Image.open(page) as im:
            rgb = im.convert('RGB')
            pixel_hash = hashlib.sha256(rgb.tobytes()).hexdigest()
            size = list(rgb.size)
        normalized = ''.join(''.join(l for l in (reader.pages[i].extract_text() or '').splitlines() if not l.strip().isdecimal()).split())
        page_rows.append({'page': i+1, 'image': page.relative_to(ROOT).as_posix(), 'pixel_sha256': pixel_hash,
                          'size': size, 'normalized_text_sha256': hashlib.sha256(normalized.encode()).hexdigest()})
    for offset in range(0, len(pages), 4):
        sheet = Image.new('RGB', (1800, 2460), 'white')
        draw = ImageDraw.Draw(sheet)
        for local, page in enumerate(pages[offset:offset+4]):
            with Image.open(page) as im:
                thumb = im.convert('RGB')
                thumb.thumbnail((890,1200))
            left, top = (local % 2)*900, (local//2)*1230
            draw.text((left+15,top+5), f'PDF {index:02d}, page {offset+local+1}',fill='black')
            sheet.paste(thumb,(left+(900-thumb.width)//2,top+25))
        target = folder / f'sheet-{offset//4+1:02d}.png'
        sheet.save(target)
        sheets.append(target.relative_to(ROOT).as_posix())
    records.append({'pdf': item['pdf'], 'index': index, 'sheets': sheets, 'pages': page_rows})
    print(json.dumps({'index': index, 'pages_rendered': len(pages)}), flush=True)
matches = []
base_pages = [(r['index'], p) for r in records[:2] for p in r['pages']]
for record in records[2:]:
    for p in record['pages']:
        exact = [{'pdf_index': i, 'page': q['page']} for i,q in base_pages if p['size'] == q['size'] and p['pixel_sha256'] == q['pixel_sha256']]
        text = [{'pdf_index': i, 'page': q['page']} for i,q in base_pages if p['normalized_text_sha256'] == q['normalized_text_sha256']]
        matches.append({'pdf_index': record['index'], 'page': p['page'], 'complete_pixel_matches': exact, 'normalized_text_matches': text})
receipt = {'renders': records, 'standalone_correspondence': matches,
           'limits': 'Render/equality aids only. Full reading and visual review are recorded separately; an unread rendered page is not substantively reviewed.'}
(OUT / 'render_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({'total_pages':sum(len(r['pages']) for r in records), 'standalone_pages':len(matches),
                  'standalone_pages_with_exact_pixel_match':sum(bool(m['complete_pixel_matches']) for m in matches)}))
