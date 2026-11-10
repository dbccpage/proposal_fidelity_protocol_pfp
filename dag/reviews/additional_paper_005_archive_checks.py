"""Exact archive-to-reviewed-base deltas, manifests and receipt consistency."""
from pathlib import Path
from collections import Counter
import difflib
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'dag/reviews'
OUT = REV/'paper_005_support_inspection'
PREFIX = 'papers/pfp/005_pfp_practitioners_field_manual/'
PACKAGE = ROOT/PREFIX
scope = json.loads((REV/'additional_paper_005_support_scope.json').read_text())
archive_pin = next(x for x in scope['files'] if x['path'].endswith('.zip'))
assert hashlib.sha256((ROOT/archive_pin['path']).read_bytes()).hexdigest() == archive_pin['sha256']
def digest(data): return hashlib.sha256(data).hexdigest()
def lf(data): return data.replace(b'\r\n',b'\n')
def map_name(name):
    return name.replace('_lev_landau_theoretical_minimum_quiz/','_lev_examiner_theoretical_minimum_quiz/').replace('005_pfp_landau_companion.pdf','005_pfp_examiner_companion.pdf')
def manifest_rows(data,fetch):
    rows = []
    for line in data.decode('utf-8-sig').splitlines():
        if not line.strip(): continue
        expected,name = line.split(None,1)
        name = name.strip().lstrip('*')
        actual = fetch(name)
        rows.append({'path':name,'expected':expected,'actual':digest(actual),'matches':digest(actual)==expected,'matches_LF':digest(lf(actual))==expected})
    assert len({x['path'] for x in rows}) == len(rows)
    return rows
with zipfile.ZipFile(ROOT/archive_pin['path']) as archive:
    members = {x.filename.split('/',1)[1]:archive.read(x) for x in archive.infolist() if not x.is_dir()}
    assert len(members) == 60
    records,rules,read_lines = [],[],[]
    for name,data in members.items():
        path = PREFIX+map_name(name)
        current = (ROOT/path).read_bytes()
        row = {'member':name,'sha256':digest(data),'current_path':path,'current_sha256':digest(current),
            'byte_equal':current==data,'LF_equal':lf(current)==lf(data),'deltas':[]}
        if name.endswith('.pdf'):
            assert current == data,name
        elif lf(current) != lf(data):
            old,new = lf(current).decode('utf-8-sig'),lf(data).decode('utf-8-sig')
            edits = []
            old_lines,new_lines = old.splitlines(keepends=True),new.splitlines(keepends=True)
            offsets = [0]
            for line in old_lines: offsets.append(offsets[-1]+len(line))
            for line_tag,la,lb,lc,ld in difflib.SequenceMatcher(None,old_lines,new_lines,autojunk=False).get_opcodes():
                if line_tag == 'equal': continue
                left,right = ''.join(old_lines[la:lb]),''.join(new_lines[lc:ld])
                prefix = 0
                while prefix < min(len(left),len(right)) and left[prefix] == right[prefix]: prefix += 1
                suffix = 0
                while suffix < min(len(left),len(right))-prefix and left[-suffix-1] == right[-suffix-1]: suffix += 1
                left = left[prefix:len(left)-suffix if suffix else None]
                right = right[prefix:len(right)-suffix if suffix else None]
                for tag,a,b,c,d in difflib.SequenceMatcher(None,left,right,autojunk=False).get_opcodes():
                    if tag == 'equal': continue
                    replacement = {'current':left[a:b],'archive':right[c:d]}
                    if replacement not in rules: rules.append(replacement)
                    edits.append({'start':offsets[la]+prefix+a,'end':offsets[la]+prefix+b,'rule':rules.index(replacement)})
            reconstructed = old
            for edit in reversed(edits):
                rule = rules[edit['rule']]
                assert reconstructed[edit['start']:edit['end']] == rule['current']
                reconstructed = reconstructed[:edit['start']]+rule['archive']+reconstructed[edit['end']:]
            assert reconstructed == new,name
            row['deltas'] = edits
        records.append(row)
    manifest = {}
    for name in ['MANIFEST.sha256','SHA256SUMS']:
        archived_rows = manifest_rows(members[name],lambda path:members[path])
        current_rows = manifest_rows((PACKAGE/name).read_bytes(),lambda path:(PACKAGE/path).read_bytes())
        manifest[name] = {'archive':archived_rows,'current':current_rows}
        assert all(x['matches'] for x in archived_rows)
    canonical = lambda obj:digest(json.dumps(obj,sort_keys=True).encode())
    integrity = []
    for location,fetch in [('archive',lambda name:members[name]),('current',lambda name:(PACKAGE/name).read_bytes())]:
        one = json.loads(fetch('code/paper_033_execution_receipt.json'))
        expected = one.pop('sha256_digest')
        integrity.append({'location':location,'receipt':'paper_033_execution_receipt','expected':expected,'computed':canonical(one),'matches':expected==canonical(one)})
        multi = json.loads(fetch('code/cross_domain_symbol_game_receipt.json'))
        for i,entry in enumerate(multi['cemetery_dag']):
            payload = dict(entry)
            expected = payload.pop('entry_hash')
            integrity.append({'location':location,'receipt':'cross_domain_cemetery','index':i,'expected':expected,'computed':canonical(payload),'matches':expected==canonical(payload),
                'chain_link_matches':entry['prev_hash'] == ('GENESIS_ROOT' if i==0 else multi['cemetery_dag'][i-1]['entry_hash'])})
    report = {'archive':archive_pin['path'],'archive_sha256':archive_pin['sha256'],'members':records,
        'rules':rules,'manifest_checks':manifest,'receipt_integrity':integrity,
        'limit':'Byte/equality/reconstruction and digest checks only. Full member reading requires a fully reviewed current base and every complete rule/context; no source changes or provider calls.'}
(REV/'additional_paper_005_archive_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
for i,rule in enumerate(rules):
    read_lines += [f'RULE {i}', 'CURRENT '+json.dumps(rule['current'],ensure_ascii=False),'ARCHIVE '+json.dumps(rule['archive'],ensure_ascii=False)]
read_lines += ['ALL_MEMBER_TRANSFORMATIONS']
for row in records:
    read_lines.append(json.dumps({k:v for k,v in row.items() if k not in {'sha256','current_sha256'}},ensure_ascii=False))
(OUT/'archive_complete_deltas.txt').write_text('\n'.join(read_lines)+'\n',encoding='utf-8')
summary = {'members':len(records),'byte_equal':sum(x['byte_equal'] for x in records),'LF_equal':sum(x['LF_equal'] for x in records),
    'changed_members':sum(bool(x['deltas']) for x in records),'unique_rules':len(rules),
    'reading_lines':len(read_lines),'reading_bytes':(OUT/'archive_complete_deltas.txt').stat().st_size,
    'manifests':{k:{'archive_entries':len(v['archive']),'current_entries':len(v['current']),
        'current_raw_mismatches':sum(not x['matches'] for x in v['current']),
        'current_LF_mismatches':sum(not x['matches_LF'] for x in v['current'])} for k,v in manifest.items()},
    'receipt_digest_matches':dict(Counter(x['location']+':'+str(x['matches']) for x in integrity))}
(OUT/'archive_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary))
