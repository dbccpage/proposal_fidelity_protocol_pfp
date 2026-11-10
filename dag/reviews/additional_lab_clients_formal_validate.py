"""Check report custody, scope, uniqueness and exact evidence range bounds."""
from pathlib import Path
import hashlib
import json
from additional_lab_clients_formal_read import ROOT,SCOPE,INDEX
def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d: raise ValueError('duplicate JSON key '+k)
        d[k]=v
    return d
path=ROOT/'dag/reviews/additional_lab_clients_formal.json'
data=json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique)
rows=data['file_reviews']; assert len(rows)==102
assert len({r['path'] for r in rows})==102
assert {r['path'] for r in rows}=={r['path'] for r in SCOPE}
for row in rows:
    raw=(ROOT/row['path']).read_bytes()
    assert row['sha256']==hashlib.sha256(raw).hexdigest()==INDEX[row['path']]['sha256']
    assert row['full_source_read'] is True and row['assessment']
    count=raw.count(b'\n')+int(bool(raw) and not raw.endswith(b'\n'))
    assert row['reviewed_lines']==([1,count] if count else [])
for item in data['claims']+data['findings']:
    for e in item['evidence']:
        raw=(ROOT/e['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==e['sha256']
        assert 1<=e['lines'][0]<=e['lines'][1]<=len(raw.splitlines()),e
print('PASS:102 unique original-inventory hashes/full ranges and all evidence paths/hashes/range bounds; JSON has no duplicate keys.')
