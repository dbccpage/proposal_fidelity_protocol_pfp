"""Reconcile the agent's final audit without executing the audited test suite."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFIX = ROOT / 'dag/reviews/additional_pfp_tests_remaining'


def path(suffix):
    return PREFIX.with_name(PREFIX.name + suffix)


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    report = read(path('.json'))
    assert sha(path('.json')) == '95c6f4e30e8f1102014090ffe2b71a4ea9246b5d5168978a33dd29d17081bb21'
    assert report['status'] == 'complete' and report['analysis_complete']
    assert not report['repository_wide_audit_complete']
    scope = {r['path']: r for r in read(path('_scope.json'))['files']}
    index = {r['path']: r for r in read(path('_index.json'))['files']}
    original = {r['path']: r for r in read(ROOT / 'dag/file_inventory.json')['files']}
    revisions = read(path('_authorized_revisions.json'))
    full = {r['path']: r for r in report['file_reviews']}
    bounded = {r['path']: r for r in report['automated_reviews']}
    assert len(scope) == 440 and set(scope) == set(index) == set(full) | set(bounded)
    assert not set(full) & set(bounded) and len(full) == 415 and len(bounded) == 25
    assert not report['remaining_unsupported_files']
    unchanged = 0
    changed = []
    for name, row in scope.items():
        assert row['sha256'] == original[name]['sha256'] == index[name]['sha256']
        binding = {**row, **revisions.get(name, {})}
        actual = sha(ROOT / name)
        assert actual == binding.get('current_sha256', row['sha256'])
        if actual == row['sha256']:
            unchanged += 1
            original_path = ROOT / name
        else:
            assert binding.get('original_git_object')
            original_path = path(binding.get('preserved_original_suffix', '_original_consistency_teaching.py.txt'))
            assert sha(original_path) == row['sha256']
            current_ranges = full[name]['current_adapted_reads']
            current_covered = [i for x in current_ranges for i in range(x['lines'][0], x['lines'][1] + 1)]
            assert sorted(current_covered) == list(range(1, len((ROOT / name).read_text(encoding='utf-8-sig').splitlines()) + 1))
            changed.append(name)
        line_count = len(original_path.read_text(encoding='utf-8-sig').splitlines())
        assert line_count == index[name]['line_count']
        if name in full:
            item = full[name]
            assert item['full_source_read'] and item['sha256'] == row['sha256']
            covered = [i for lo, hi in item['reviewed_lines'] for i in range(lo, hi + 1)]
            assert covered == list(range(1, line_count + 1))
            if not line_count:
                assert item['empty_file_read']
        else:
            item = bounded[name]
            assert name.endswith('.json') and not item['full_source_read']
            assert item['sha256'] == row['sha256'] and item['checks']
    assert unchanged == 438 and len(changed) == 2
    evidence_ranges = 0
    for group, count in [('claims', 61), ('findings', 126), ('controls', 81)]:
        assert len(report[group]) == count
        assert len({x['id'] for x in report[group]}) == count
        for item in report[group]:
            for ev in item.get('evidence', item.get('source_evidence', [])):
                assert ev['sha256'] == scope[ev['path']]['sha256']
                lo, hi = ev['lines']
                assert 1 <= lo <= hi <= index[ev['path']]['line_count']
                evidence_ranges += 1
            for key in ('receipt', 'helper'):
                binding = item.get(key)
                if isinstance(binding, dict) and {'path', 'sha256'} <= binding.keys():
                    assert sha(ROOT / binding['path']) == binding['sha256']
    manifest = read(path('_control_artifact_manifest.json'))
    assert manifest['control_ids'] == [c['id'] for c in report['controls']]
    for binding in manifest['artifacts'] + report['final_artifact_bindings']:
        assert sha(ROOT / binding['path']) == binding['sha256']
    assert sha(path('.json')) in path('.md').read_text(encoding='utf8')
    out = {
        'status': 'parent_integration_pass',
        'report': str(path('.json').relative_to(ROOT)).replace('\\', '/'),
        'report_sha256': sha(path('.json')),
        'markdown_sha256': sha(path('.md')),
        'agent_validation_sha256': sha(path('_final_validation.json')),
        'control_artifact_manifest_sha256': sha(path('_control_artifact_manifest.json')),
        'parent_validator_sha256': sha(Path(__file__)),
        'summary': {**report['scope'], 'claims': 61, 'findings': 126, 'agent_controls': 81,
                    'parent_controls_reexecuted': 0, 'source_evidence_ranges_revalidated': evidence_ranges},
        'current_original_hash_matches': unchanged,
        'authorized_current_revisions': changed,
        'parent_review': 'Read the complete synthesis, all 61 claim statements/limits, all 126 findings/reasons/limits, all 81 control descriptions and detailed probe outcomes. Reviewed the custody validators and independently rechecked source hashes, original/current migration revisions, complete read ranges, disjoint full/bounded partitions, source evidence and all retained control/artifact pins. Requested and checked the correction to stale F035 pending wording.',
        'limits': [
            'Original source reading and control execution remain attributed to audit_challenges_041_050.',
            '25 bounded JSON dispositions are not full body reads or mathematical certification.',
            'No parent execution of original tests, native owners, archived programs or providers.',
            'Test-local counterexamples, test adequacy findings and production behavior remain separate.',
        ],
    }
    destination = ROOT / 'dag/reviews/pfp_tests_440_parent_integration.json'
    destination.write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
    print(json.dumps({'status': out['status'], 'report_sha256': out['report_sha256'],
                      'source_evidence_ranges': evidence_ranges, 'summary': out['summary']}))


if __name__ == '__main__':
    main()
