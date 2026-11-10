"""Read-only PDF extraction and archive inventory for introductory paper support."""
import hashlib
import json
from pathlib import Path
import zipfile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'papers/pfp/000_pfp_introduction'
OUT = Path(__file__).with_name('paper_000_support_inspection')
OUT.mkdir(exist_ok=True)
rows = []
for index, path in enumerate(sorted(PACKAGE.rglob('*.pdf'))):
    reader = PdfReader(path)
    texts = [page.extract_text(extraction_mode='layout') or '' for page in reader.pages]
    target = OUT / f'pdf_{index:02d}.txt'
    target.write_text('\n'.join(f'\n--- PAGE {n + 1} ---\n{text}' for n, text in enumerate(texts)), encoding='utf-8')
    row = {'pdf': path.relative_to(ROOT).as_posix(), 'pages': len(texts),
           'text_lines': len(target.read_text(encoding='utf-8').splitlines()),
           'extraction': target.relative_to(ROOT).as_posix(),
           'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    rows.append(row)
    print(json.dumps(row))
(OUT / 'pdf_inventory.json').write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')
for path in PACKAGE.rglob('*.zip'):
    with zipfile.ZipFile(path) as archive:
        print('ARCHIVE', path.name, 'members', len(archive.infolist()), 'crc_failure', archive.testzip())
        for item in archive.infolist():
            print(item.filename, item.file_size)
print('TEX_LINES', len((PACKAGE / 'paper.tex').read_text().splitlines()))
notebook = json.loads((PACKAGE / 'jupyter_notebooks/000_from_marks_to_returned_packets.ipynb').read_text())
print('NOTEBOOK_CELLS', len(notebook['cells']))
print('NOTEBOOK_SOURCE_LINES', sum(len(''.join(cell['source']).splitlines()) for cell in notebook['cells']))
