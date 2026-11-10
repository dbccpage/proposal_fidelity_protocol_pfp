"""Verify every reviewed historical member from pinned bases and full diff."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dag/reviews'
NAME = '003_pfp_host_admitted_failure_detectors'
PREFIX = 'papers/pfp/' + NAME + '/'
scope = json.loads((OUT / 'additional_paper_003_support_scope.json').read_text())
pins = {r['path']:r['sha256'] for r in scope['files']}
custody = json.loads((OUT / 'additional_paper_003_custody.json').read_text())
diff_path = OUT / 'paper_003_support_inspection/archive_complete_text_diffs.txt'
diff = diff_path.read_text(encoding='utf-8')
sections = {}
for section in re.split(r'(?m)(?=^--- archive/)', diff):
    if not section.strip():
        continue
    lines = section.splitlines()
    sections[lines[0][len('--- archive/'):]] = (lines[1][len('+++ current/'):], lines[2:])

def normalize(raw):
    return raw.decode('utf-8').replace('\r\n','\n').replace('\r','\n')

def reverse_diff(current, rows):
    source = current.splitlines()
    result, pos, i = [], 0, 0
    while i < len(rows):
        if not rows[i].startswith('@@'):
            assert rows[i] == '', rows[i]
            i += 1
            continue
        match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', rows[i])
        assert match, rows[i]
        start = int(match[3]) - 1
        assert start >= pos
        result.extend(source[pos:start])
        pos = start
        i += 1
        old_count = new_count = 0
        while i < len(rows) and not rows[i].startswith('@@'):
            line = rows[i]
            i += 1
            if line == '':
                continue
            assert line[0] in ' +-'
            if line[0] in ' +':
                assert source[pos] == line[1:]
                pos += 1
                new_count += 1
            if line[0] in ' -':
                result.append(line[1:])
                old_count += 1
        assert old_count == int(match[2] or 1) and new_count == int(match[4] or 1)
    result.extend(source[pos:])
    return '\n'.join(result) + ('\n' if current.endswith('\n') else '')

for path,digest in pins.items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
archive_path = PREFIX + NAME + '_2026-10-02.zip'
members, bindings = [], []
with zipfile.ZipFile(ROOT/archive_path) as archive:
    assert archive.testzip() is None
    names = archive.namelist()
    assert len(names) == len(set(names))
    assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in names)
    assert {r['member'] for r in custody['archive_members']} == {n for n in names if not n.endswith('/')}
    for item in custody['archive_members']:
        old = archive.read(item['member'])
        current = (ROOT/item['current_path']).read_bytes()
        assert hashlib.sha256(old).hexdigest() == item['sha256']
        assert hashlib.sha256(current).hexdigest() == item['current_sha256']
        method = 'exact_bytes'
        if old != current:
            before, after = normalize(old), normalize(current)
            method = 'universal_LF_equal'
            if before != after:
                relative = item['member'][len(NAME)+1:]
                new, hunks = sections[relative]
                assert PREFIX + new == item['current_path']
                assert reverse_diff(after,hunks) == before, relative
                method = 'complete_reviewed_diff_reconstructed'
        members.append({**item,'verified_review_transfer': method})
    for name in ('MANIFEST.sha256','SHA256SUMS'):
        for line in archive.read(NAME+'/'+name).decode().splitlines():
            digest, relative = line.split(None,1)
            relative = relative.lstrip('* ')
            assert hashlib.sha256(archive.read(NAME+'/'+relative)).hexdigest() == digest
            bindings.append({'manifest':name,'member':relative,'sha256':digest})
assert len(sections) == sum(m['verified_review_transfer'] == 'complete_reviewed_diff_reconstructed' for m in members)
result = {'status':'all_bindings_and_reconstructions_passed','source_scope_rehashed':len(pins),
    'archive':archive_path,'archive_sha256':pins[archive_path],'members':members,
    'embedded_bindings':len(bindings),'diff_sections':len(sections),
    'diff_sha256':hashlib.sha256(diff_path.read_bytes()).hexdigest(),
    'diff_joined_lines':len(diff.splitlines()),'diff_sum_section_lines':sum(r.get('complete_difference_lines',0) for r in members),
    'long_json_difference_receipt':'dag/reviews/paper_003_support_inspection/archive_long_line_changes.json',
    'limits':'Custody and exact reviewed-base reconstruction, not proof of historical execution or compression-parser security.'}
(OUT/'additional_paper_003_archive_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k != 'members'}))
