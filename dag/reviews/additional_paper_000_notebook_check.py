"""Execute reviewed teaching cells without modifying the notebook or contacting providers."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'papers/pfp/000_pfp_introduction'
NOTEBOOK = PACKAGE / 'jupyter_notebooks/000_from_marks_to_returned_packets.ipynb'
before = hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest()
notebook = json.loads(NOTEBOOK.read_text(encoding='utf-8'))

def guard(event, args):
    if event.startswith(('socket.', 'subprocess.', 'ctypes.dlopen')) or event in {'os.system', 'os.posix_spawn', 'os.startfile'}:
        raise RuntimeError(f'External effect prohibited in teaching replay: {event}')

sys.addaudithook(guard)
sys.dont_write_bytecode = True
os.chdir(PACKAGE)
namespace = {'__name__': '__notebook_review__'}
outputs = []
for index, cell in enumerate(notebook['cells']):
    if cell['cell_type'] != 'code':
        continue
    source = ''.join(cell['source'])
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(source, f'<reviewed-paper000-cell-{index}>', 'exec'), namespace)
    outputs.append({'cell_index': index, 'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'stdout': output.getvalue(), 'passed': True})
assert hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest() == before
receipt = {'source': NOTEBOOK.relative_to(ROOT).as_posix(), 'sha256': before, 'working_directory': PACKAGE.relative_to(ROOT).as_posix(), 'python': sys.version, 'cells': outputs, 'all_cells_passed': True, 'execution': 'Reviewed cell bodies executed sequentially in one fresh ordinary Python process; no Jupyter kernel/UI test', 'limits': ['Eight finite teaching examples only.', 'No native build, provider calls or sealed QM benchmark access.', 'Notebook outputs, metadata and execution counts remain untouched.']}
(ROOT / 'dag/reviews/additional_paper_000_notebook_check.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'code_cells_passed': len(outputs), 'original_notebook_unchanged': True}))
