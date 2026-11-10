"""Losslessly present changing trace fields; no source execution or edits."""
from pathlib import Path
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'papers/pfp/003_pfp_host_admitted_failure_detectors'
OUT = ROOT / 'dag/reviews/paper_003_support_inspection'
path = PACKAGE / 'demos/demo_3/traces/diamond_r4b_1790206003.jsonl'
rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
assert len(rows) == 12
base = rows[0]
view = ['BASE ' + json.dumps(base, ensure_ascii=False)]
for index, row in enumerate(rows[1:], 1):
    assert row.keys() == base.keys()
    changes = {}
    recovered = dict(base)
    for key, value in row.items():
        if value == base[key] and type(value) is type(base[key]):
            continue
        if isinstance(value, str) and key == 'user_turn':
            before, after = base[key].splitlines(keepends=True), value.splitlines(keepends=True)
            operations = difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes()
            edits = [{'base_lines': [i,j], 'replacement': after[k:l]}
                     for tag,i,j,k,l in operations if tag != 'equal']
            rebuilt = list(before)
            for edit in reversed(edits):
                i,j = edit['base_lines']
                rebuilt[i:j] = edit['replacement']
            assert ''.join(rebuilt) == value
            changes[key] = {'zero_based_base_line_edits': edits}
            recovered[key] = ''.join(rebuilt)
        else:
            changes[key] = value
            recovered[key] = value
    assert recovered == row
    view.append('ROW_DELTA ' + str(index) + ' ' + json.dumps(changes, ensure_ascii=False))
(OUT / 'diamond_trace_lossless_view.txt').write_text('\n'.join(view)+'\n', encoding='utf-8')
(OUT / 'diamond_trace_view_receipt.json').write_text(json.dumps({
    'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'records': len(rows), 'fully_reconstructed': True, 'first_record_complete': True,
    'remaining_records': 'All changed fields; user_turn represented by all line replacements against first record.',
    'limit': 'Preparation is not substantive reading or host replay.'},indent=2)+'\n',encoding='utf-8')
print(len('\n'.join(view)))
holonomy = [json.loads(line) for line in (PACKAGE / 'demos/demo_3/traces/holonomy3c_r2b_1790205330.jsonl').read_text(encoding='utf-8').splitlines()]
assert all(r['admission_status'] == 'pending' and r['admitted'] is False and r['phi1_before'] == r['phi1_after'] == r['gamma2'] == -1 for r in rows + holonomy)
initial, delta = [1,2,2], [-2,1,1]
assert sum(initial) == sum(a+b for a,b in zip(initial,delta)) == 5
assert abs(1+2+3) + abs(1+1+2) == 10
(OUT / 'historical_trace_arithmetic.json').write_text(json.dumps({
    'holonomy_prompt': {'initial_weights': initial, 'advertised_differential_change': delta,
        'oriented_cycle_sum_after_additive_change': 5, 'claimed_zero': False},
    'diamond_declared_cycle_sum_norm': {'initial_weights': [1,2,3,1,2], 'cycle_sums': [6,4],
        'sum_absolute_cycle_sums': 10, 'reported_after_five_assertions': 8},
    'all_fifteen_raw_records': 'pending, admitted=false, numerical host fields=-1; user prompts retain a different feedback history.',
    'limit': 'Direct arithmetic under the prompt-declared additive and cycle-sum semantics, not a replay of an unavailable historical host or proof about a different quotient metric.'},indent=2)+'\n',encoding='utf-8')
publication = json.loads((PACKAGE / 'docs/first_publication_validation_2026_10_02.json').read_text(encoding='utf-8'))
logs, log_ids, command_views = [], {}, []
for command in publication['pdf_build_commands']:
    body = dict(command)
    for key in ('stdout', 'stderr'):
        if key not in body:
            continue
        content = body[key]
        ids = []
        for line in content.splitlines(keepends=True):
            if line not in log_ids:
                log_ids[line] = len(logs)
                logs.append(line)
            ids.append(log_ids[line])
        assert ''.join(logs[i] for i in ids) == content
        body[key] = {'exact_line_ids': ids}
    command_views.append(body)
result = {'pdf_build_commands': command_views,
    'other_trailing_fields': {k:v for k,v in publication.items() if k not in ['schema','date','release_version','authority_effect','external_deposit','checkout_base','scope','tools','counts','commands','input_sha256','pdf_build_commands']},
    'unique_log_lines': logs}
(OUT / 'publication_pdf_log_view.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'unique_pdf_log_lines': len(logs), 'complete_reconstruction': True}))
