"""Schema-only census of public response/execution records; no seed or private input reads."""
import collections
import hashlib
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'pilots/anomalon_woland'
rows = []
for i in range(51,102):
    folder = BASE / f'pilot_{i:07d}'
    statuses = collections.Counter()
    modes = collections.Counter()
    responses = []
    executions = []
    for p in sorted(folder.rglob('*')):
        if not p.is_file() or p.name not in ('response.yaml', 'execution.yaml'):
            continue
        raw = p.read_bytes()
        evidence = {'path': p.relative_to(ROOT).as_posix(), 'lines': [1, len(raw.decode('utf-8').splitlines())],
                    'sha256': hashlib.sha256(raw).hexdigest(), 'review_level': 'schema_fields_mechanically_inspected_not_full_text_review'}
        try:
            d = yaml.safe_load(raw)
            if not isinstance(d, dict):
                raise ValueError('record is not mapping')
        except Exception as error:
            evidence['parse_error_type'] = type(error).__name__
            responses.append(evidence)
            continue
        evidence['schema'] = d.get('schema')
        if p.name == 'execution.yaml':
            for k in ('provider_calls', 'winning_condition_executed', 'execution_limit'):
                evidence[k] = d.get(k)
            evidence['variation_count'] = len(d.get('variations', []))
            evidence['all_declared_claim_held'] = all(v.get('claim_held') is True for v in d.get('variations', []))
            executions.append(evidence)
        else:
            status = d.get('trial_status', d.get('status', 'unspecified'))
            mode = d.get('execution_mode', 'unspecified')
            statuses[str(status)] += 1
            modes[str(mode)] += 1
            evidence.update(status=status, mode=mode, explicit_provider_calls=d.get('provider_calls'),
                            has_nonempty_raw_reply=isinstance(d.get('raw_reply'), str) and bool(d['raw_reply']))
            responses.append(evidence)
    rows.append({'pilot': i, 'response_count': len(responses), 'statuses': dict(statuses), 'modes': dict(modes),
                 'nonempty_raw_reply_count': sum(bool(r.get('has_nonempty_raw_reply')) for r in responses),
                 'execution_records': executions, 'response_records': responses,
                 'python_test_files': [p.relative_to(ROOT).as_posix() for p in sorted((folder/'tests').rglob('test*.py'))]})
out = Path(__file__).with_name('numbered_051_101_census.json')
out.write_text(json.dumps(rows, indent=2)+'\n')
for r in rows:
    print(r['pilot'], r['response_count'], r['statuses'], r['modes'], 'raw', r['nonempty_raw_reply_count'],
          'offline records', [(x['provider_calls'], x['winning_condition_executed']) for x in r['execution_records']],
          'test files',len(r['python_test_files']))
