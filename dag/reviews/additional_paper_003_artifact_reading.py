"""Prepare lossless logical reading views; preparation alone is not review."""
from pathlib import Path
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'papers/pfp/003_pfp_host_admitted_failure_detectors'
OUT = ROOT / 'dag/reviews/paper_003_support_inspection'

def unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('Duplicate object key: ' + key)
        result[key] = value
    return result

def parse(path):
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_pairs)

def delta(base, target, path=()):
    if type(base) is type(target) and isinstance(base, dict) and base.keys() == target.keys():
        return [change for key in base for change in delta(base[key], target[key], path+(key,))]
    if type(base) is type(target) and isinstance(base, list) and len(base) == len(target):
        return [change for i in range(len(base)) for change in delta(base[i], target[i], path+(i,))]
    return [] if type(base) is type(target) and base == target else [{'path': list(path), 'value': target}]

def apply(base, changes):
    result = copy.deepcopy(base)
    for change in changes:
        path = change['path']
        if not path:
            result = copy.deepcopy(change['value'])
            continue
        parent = result
        for key in path[:-1]: parent = parent[key]
        parent[path[-1]] = copy.deepcopy(change['value'])
    return result

receipt_path = PACKAGE / 'demos/demo_3/results/live_openrouter_trial_receipt.json'
receipt = parse(receipt_path)
views = {'header': {k: v for k,v in receipt.items() if k != 'trials'},
         'bases': receipt['trials'][:10], 'remaining_trial_deltas': []}
for i, trial in enumerate(receipt['trials'][10:], start=10):
    base_index = i % 10
    changes = delta(views['bases'][base_index], trial)
    assert apply(views['bases'][base_index], changes) == trial
    views['remaining_trial_deltas'].append({'trial_index': i, 'base_index': base_index, 'changes': changes})
(OUT / 'live_receipt_lossless_view.json').write_text(json.dumps(views, indent=2)+'\n', encoding='utf-8')
text = ['HEADER ' + json.dumps(views['header'], ensure_ascii=False)]
text += ['BASE_TRIAL ' + str(i) + ' ' + json.dumps(v, ensure_ascii=False) for i,v in enumerate(views['bases'])]
text += ['TRIAL_DELTA ' + json.dumps(v, ensure_ascii=False) for v in views['remaining_trial_deltas']]
(OUT / 'live_receipt_reading.txt').write_text('\n'.join(text)+'\n', encoding='utf-8')
notebook_receipts = []
for path in sorted(PACKAGE.rglob('*.ipynb')):
    nb = parse(path)
    parts = ['ROOT_METADATA ' + json.dumps({k:v for k,v in nb.items() if k != 'cells'}, ensure_ascii=False)]
    for i,cell in enumerate(nb['cells']):
        parts += ['CELL ' + str(i), 'METADATA_AND_OUTPUTS ' + json.dumps({k:v for k,v in cell.items() if k != 'source'}, ensure_ascii=False),
                  'SOURCE_START', ''.join(cell['source']), 'SOURCE_END']
    target = OUT / (path.stem + '_complete_cells.txt')
    target.write_text('\n'.join(parts)+'\n', encoding='utf-8')
    notebook_receipts.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'cells': len(nb['cells']), 'reading_view': target.relative_to(ROOT).as_posix(), 'executed': False})
report = {'live_receipt': {'source': receipt_path.relative_to(ROOT).as_posix(),
    'sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(), 'trials': len(receipt['trials']),
    'complete_bases': 10, 'exactly_reconstructed_deltas': 20, 'duplicate_keys': 0},
    'notebooks': notebook_receipts,
    'limit': 'Lossless JSON-value and source-cell view preparation only. Substantive reading and runtime validation are separate.'}
(OUT / 'artifact_reading_preparation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
