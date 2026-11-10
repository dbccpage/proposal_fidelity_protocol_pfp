"""Exact char-range views for very long historical JSON diff lines."""
from pathlib import Path
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dag/reviews/paper_003_support_inspection'
path = OUT / 'archive_complete_text_diffs.txt'
lines = path.read_text(encoding='utf-8').splitlines()
records = []
for i,line in enumerate(lines):
    if not (571 <= i < 690) or not line.startswith('-') or line.startswith('---') or len(line) <= 500:
        continue
    assert lines[i+1].startswith('+'), i
    old, new = line[1:], lines[i+1][1:]
    edits = []
    for tag,a,b,c,d in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag != 'equal':
            edits.append({'old_range': [a,b], 'old': old[a:b], 'new': new[c:d]})
    recovered = old
    for e in reversed(edits):
        a,b = e['old_range']
        assert old[a:b] == e['old']
        recovered = recovered[:a] + e['new'] + recovered[b:]
    assert recovered == new
    records.append({'removed_diff_line': i+1, 'added_diff_line': i+2, 'all_changes': edits,
        'old_sha256': hashlib.sha256(old.encode()).hexdigest(), 'new_sha256': hashlib.sha256(new.encode()).hexdigest(),
        'reconstruction': 'exact'})
(OUT / 'archive_long_line_changes.json').write_text(json.dumps(records,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(records,ensure_ascii=False))
