"""Export only the reviewed Git tree delta for API publication."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT.parent / 'anomalon'
plan = json.loads((HERE / 'demo_support_move_plan.json').read_text())
consumers = json.loads((HERE / 'demo_support_consumer_receipt.json').read_text())
entries = [{'path': row['source_relative_path'], 'mode': row['git_mode'], 'type': 'blob', 'sha': None}
           for row in plan['entries'] if row['source_repo'] == 'anomalon' and row['source_git_tracked']]
for row in consumers['changes']:
    if row['repository'] != 'anomalon':
        continue
    raw = (SOURCE / row['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == row['after_sha256']
    entries.append({'path': row['path'], 'mode': '100644', 'type': 'blob', 'content': raw.decode('utf-8')})
assert len(entries) == len({row['path'] for row in entries}) == 215
payload = json.dumps({'base_tree_sha': '7f588865ec9454d8e8dec275c92e4922f1abe9f1',
                     'expected_tree_sha': '67ad2961a9ea8e3360affe83d742c1ecc7d41281', 'tree_elements': entries})
chunk_size = 16000
if len(sys.argv) == 2:
    part = int(sys.argv[1])
    print(json.dumps({'part': part, 'text': payload[part * chunk_size:(part + 1) * chunk_size]}))
else:
    print(json.dumps({'chunks': (len(payload) + chunk_size - 1) // chunk_size, 'characters': len(payload),
                      'payload_sha256': hashlib.sha256(payload.encode()).hexdigest(), 'entries': len(entries)}))
