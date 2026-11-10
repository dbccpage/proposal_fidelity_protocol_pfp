"""Render existing PDFs for review; never rebuild or alter the source PDFs."""
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name('paper_000_support_inspection')
POPLER = Path(r'C:\Users\a343o\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
inventory = json.loads((OUT / 'pdf_inventory.json').read_text())
records = []
page_texts = {}
for index, record in enumerate(inventory):
    source = ROOT / record['pdf']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == record['sha256']
    folder = OUT / f'render_{index:02d}'
    folder.mkdir(exist_ok=True)
    subprocess.run([str(POPLER), '-scale-to', '1200', '-png', str(source), str(folder / 'page')], check=True, capture_output=True, timeout=90)
    pages = sorted(folder.glob('page-*.png'))
    assert len(pages) == record['pages']
    sheets = []
    for offset in range(0, len(pages), 4):
        subset = pages[offset:offset + 4]
        sheet = Image.new('RGB', (1800, 2460), 'white')
        draw = ImageDraw.Draw(sheet)
        for local, page in enumerate(subset):
            with Image.open(page) as opened:
                thumb = opened.convert('RGB')
                thumb.thumbnail((890, 1200))
            left = (local % 2) * 900
            top = (local // 2) * 1230
            draw.text((left + 15, top + 5), f'PDF {index:02d}, page {offset + local + 1}', fill='black')
            sheet.paste(thumb, (left + (900 - thumb.width) // 2, top + 25))
        target = folder / f'sheet-{offset // 4 + 1:02d}.png'
        sheet.save(target)
        sheets.append(target.relative_to(ROOT).as_posix())
    records.append({'pdf': record['pdf'], 'pages_rendered': len(pages), 'sheets': sheets})
    texts = []
    for page in PdfReader(source).pages:
        # Page numbers are printed differently by the independent and combined editions.
        lines = (page.extract_text() or '').splitlines()
        lines = [line for line in lines if not line.strip().isdecimal()]
        texts.append(''.join(''.join(lines).split()))
    page_texts[index] = texts
combined = page_texts[1]
correspondence = []
for index, start in [(2, 0), (5, 6), (3, 12), (4, 19)]:
    standalone = page_texts[index]
    equal = [text == combined[start + i] for i, text in enumerate(standalone)]
    correspondence.append({'standalone_pdf_index': index, 'companion_pages_one_based': [start + 1, start + len(standalone)], 'normalized_page_text_equal': equal})
result = {'renders': records, 'standalone_companion_correspondence': correspondence, 'normalization': 'pypdf default text extraction, remove standalone decimal page-number lines, remove whitespace only; no prose replacement', 'limits': 'Rendering and equality are inspection aids. Visual observations are recorded separately after human/model review.'}
(OUT / 'render_receipt.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'pages_rendered': sum(r['pages_rendered'] for r in records), 'text_correspondence': correspondence}))
