"""Replay seven fully reviewed offline cells, preserving original notebook bytes."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'papers/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions'
def guard(event, args):
    if event.startswith(('socket.', 'subprocess.', 'ctypes.dlopen')) or event in {'os.system', 'os.posix_spawn', 'os.startfile'}:
        raise RuntimeError('External effect prohibited in offline notebook replay: ' + event)
sys.addaudithook(guard)
sys.dont_write_bytecode = True
os.chdir(PACKAGE)
records = []
for notebook in sorted((PACKAGE / 'jupyter_notebooks').glob('*.ipynb')):
    before = hashlib.sha256(notebook.read_bytes()).hexdigest()
    body = json.loads(notebook.read_text())
    namespace = {'__name__': '__reviewed_notebook__'}
    cells = []
    for index, cell in enumerate(body['cells']):
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source'])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(source, f'<paper001-{notebook.stem}-{index}>', 'exec'), namespace)
        historical = ''.join(''.join(o.get('text', [])) for o in cell.get('outputs', []) if o.get('output_type') == 'stream')
        cells.append({'index': index, 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                      'passed': True, 'stdout': output.getvalue(), 'stored_stdout': historical,
                      'exact_stored_stdout_match': output.getvalue() == historical})
    assert hashlib.sha256(notebook.read_bytes()).hexdigest() == before
    records.append({'path': notebook.relative_to(ROOT).as_posix(), 'sha256': before, 'cells': cells})
receipt = {'notebooks': records, 'python': sys.version,
           'execution': 'Sequential reviewed cells in ordinary Python namespaces; no Jupyter kernel/UI test.',
           'limits': ['No provider, credentials, private QM answer or native process used.',
                      'Historical stored outputs and source notebooks remain unchanged.']}
(ROOT / 'dag/reviews/additional_paper_001_notebook_check.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'code_cells_passed': sum(len(r['cells']) for r in records),
                  'stored_stdout_differences': [{'notebook': r['path'], 'cell': c['index']} for r in records for c in r['cells'] if not c['exact_stored_stdout_match']]}))
