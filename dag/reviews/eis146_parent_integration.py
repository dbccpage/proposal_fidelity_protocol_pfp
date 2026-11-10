"""Independently reconstruct the EIS reading transfers; execute no source programs."""
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
P = R / 'dag/reviews/additional_eis_artifacts_remaining'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pairs(items):
    result = {}
    for key, value in items:
        assert key not in result
        result[key] = value
    return result

def read(path):
    return json.loads(path.read_bytes(), object_pairs_hook=pairs)

report_path = Path(str(P) + '.json')
report = read(report_path)
assert sha(report_path) == '127c57ac68ab1fc383dc142203c69cc725c3a9ff5599f27e79abc1c122a957bb'
manifest = read(Path(str(P) + '_body_transfer_manifest.json'))
catalog = manifest['catalog']
source = read(R / catalog['source']['path'])
assert sha(R / catalog['source']['path']) == catalog['source']['sha256']
assert {k: v for k, v in source.items() if k != 'antibodies'} == catalog['metadata_outside_antibodies']
actual = source['antibodies']
rebuilt = {}
for item in catalog['root_transfers']:
    path = R / item['base_path']
    assert sha(path) == item['base_sha256']
    base = read(path)
    key = item['catalog_id']
    expected = actual[key]
    differences = {k: {'file': base.get(k), 'catalog': expected.get(k)}
                   for k in set(base) | set(expected)
                   if (k in base) != (k in expected) or base.get(k) != expected.get(k)}
    assert differences == (item['delta'] or {})
    for k, delta in differences.items():
        if k in expected:
            base[k] = delta['catalog']
        else:
            base.pop(k, None)
    assert base == expected and key not in rebuilt
    rebuilt[key] = base
templates = {}
residual_path = R / catalog['residual_artifact']
assert sha(residual_path) == catalog['residual_sha256']
for line in residual_path.read_text(encoding='utf8').splitlines():
    row = json.loads(line, object_pairs_hook=pairs)
    if 'template' in row:
        template = row['template']
        assert template['group'] not in templates
        templates[template['group']] = template
        continue
    template = templates[row['group']]
    fields, values = template['row_fields'], row['values']
    assert len(fields) == len(values)
    key = values[0]
    rebuilt_row = dict(template['constant_fields'])
    rebuilt_row['antibody_id'] = key
    rebuilt_row.update(zip(fields[1:], values[1:]))
    for field, (prefix, dependency) in template['derived_fields'].items():
        rebuilt_row[field] = prefix + rebuilt_row[dependency]
    assert set(rebuilt_row) == set(template['original_field_order'])
    assert key not in rebuilt and rebuilt_row == actual[key]
    rebuilt[key] = rebuilt_row
assert rebuilt == actual and len(rebuilt) == 1069 and len(templates) == 11

warning = manifest['warning_logs']
path = R / warning['source']['path']
assert sha(path) == warning['source']['sha256']
read(path)  # Refuse duplicate keys anywhere in the containing JSON document.
lines = path.read_text(encoding='utf8').splitlines()
def output(line):
    return json.loads('{' + lines[line - 1].rstrip(',') + '}', object_pairs_hook=pairs)['output_utf8']
base_path = R / warning['base_artifact']
assert sha(base_path) == warning['base_decoded_sha256']
base = base_path.read_bytes().decode('utf8')
assert base == output(warning['base_raw_line'])
logs = [{'source_line': warning['base_raw_line'], 'characters': len(base)}]
for item in warning['deltas']:
    delta_path = R / item['delta_artifact']
    assert sha(delta_path) == item['delta_sha256']
    offset = 0
    chunks = []
    for span in read(delta_path):
        start, end = span['base_char_start'], span['base_char_end']
        assert offset <= start <= end <= len(base)
        chunks.extend((base[offset:start], span['replacement']))
        offset = end
    chunks.append(base[offset:])
    reconstructed = ''.join(chunks)
    assert reconstructed == output(item['raw_line'])
    assert hashlib.sha256(reconstructed.encode()).hexdigest() == item['decoded_sha256']
    logs.append({'source_line': item['raw_line'], 'characters': len(reconstructed)})

controls = read(Path(str(P) + '_controls.json'))
by_id = {x['id']: x for x in controls['controls']}
assert by_id['EA-T09']['result']['output_pairs'] == 33
assert by_id['EA-T09']['result']['exact_output_mismatches'] == 21
assert by_id['EA-T01']['result']['population'] == 54
out = {
    'status': 'PASS', 'report_sha256': sha(report_path),
    'validation_sha256': sha(Path(str(P) + '_validation.json')),
    'body_transfer_validation_sha256': sha(Path(str(P) + '_body_transfer_validation.json')),
    'catalog_exact_reconstructed_records': len(rebuilt), 'templates': len(templates),
    'root_base_transfers': len(catalog['root_transfers']), 'logs': logs,
    'parent_review': 'Reviewed all three qualified claims, eight findings, eleven control descriptions/results, transfer methodology and all batch assessment notes. Independently reconstructed all1069 catalog records and three complete decoded logs. Agent owns original semantic reading; parent does not claim to have read every original catalog record or raw escape spelling.',
    'correction': 'EA-F07 prose corrected from32 to36 hex characters to agree with unchanged EA-T07; previous final report preserved as a pinned snapshot. EA-C03 now describes full semantic reading plus historical accounting.',
    'limits': 'Custody and lossless transfer verification plus report synthesis; no original program, Rust, provider, private benchmark or historical run execution.',
    'helper_sha256': sha(Path(__file__))
}
(R / 'dag/reviews/eis146_parent_integration.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf8')
print(json.dumps(out, indent=2))
