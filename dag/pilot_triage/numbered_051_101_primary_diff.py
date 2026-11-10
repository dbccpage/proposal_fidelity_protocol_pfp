"""Lossless full-primary review against the fully read pilot055 template."""
import difflib
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'pilots/anomalon_woland'
LEDGER = Path(__file__).with_name('numbered_051_101_reads.json')
prior = json.loads(LEDGER.read_text())
for i in range(int(sys.argv[1]),int(sys.argv[2])+1):
    for name in ('README.md','spec.yaml'):
        reference = BASE/'pilot_0000055'/name
        path = BASE/f'pilot_{i:07d}'/name
        base_raw, raw = reference.read_bytes(), path.read_bytes()
        base, current = base_raw.decode('utf-8').splitlines(keepends=True),raw.decode('utf-8').splitlines(keepends=True)
        sm = difflib.SequenceMatcher(None,base,current,autojunk=False)
        rebuilt = []
        print(f'FILE {path.relative_to(ROOT).as_posix()} SHA256 {hashlib.sha256(raw).hexdigest()} LINES {len(current)}')
        print(f'EXACT BASELINE {reference.relative_to(ROOT).as_posix()} SHA256 {hashlib.sha256(base_raw).hexdigest()}')
        for tag,a,b,c,d in sm.get_opcodes():
            if tag=='equal':
                rebuilt.extend(base[a:b])
            else:
                print(f'{tag}: baseline lines {a+1}-{b}; current lines {c+1}-{d}')
                print(''.join(f'{k+1}: {current[k]}' for k in range(c,d)),end='')
                rebuilt.extend(current[c:d])
        assert ''.join(rebuilt).encode('utf-8')==raw
        entry={'path':path.relative_to(ROOT).as_posix(),'lines':[1,len(current)],'sha256':hashlib.sha256(raw).hexdigest(),
               'review_level':'full_content_via_exact_diff_against_fully_read_primary',
               'baseline':reference.relative_to(ROOT).as_posix(),'baseline_sha256':hashlib.sha256(base_raw).hexdigest(),
               'lossless_reconstruction_verified':True}
        prior=[x for x in prior if x['path'] != entry['path']]+[entry]
LEDGER.write_text(json.dumps(prior,indent=2)+'\n')
