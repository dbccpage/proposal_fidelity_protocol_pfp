"""Read-only actual custody checks and isolated release/renderer countercontrols."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
BASE = ROOT / 'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence'
OUT = REV / 'paper_011_support_inspection'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, BASE / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

scope = json.loads((REV / 'additional_paper_011_support_scope.json').read_text())
before = {row['path']: sha(ROOT / row['path']) for row in scope['files']}
assert before == {row['path']: row['sha256'] for row in scope['files']}
verify = load('paper011_support_verify', 'verify_deposit.py')
canonical = load('paper011_support_canonical', 'tools/rebuild_release.py')
builder = load('paper011_support_builder', 'scripts/build_deposit_zip.py')
renderer = load('paper011_support_renderer', 'tools/render_paper.py')
result = {'runtime': sys.version, 'interpreter': sys.executable,
          'scope': 'Only actual read-only custody plus synthetic packages; no original rendering/release writes, tests, Lean, providers or private answer reads.'}
result['current_manifest_errors'] = {name: verify.check_manifest(BASE / name) for name in ('MANIFEST.sha256', 'SHA256SUMS')}
result['current_canonical_errors'] = canonical.validate(BASE)

with patch.object(renderer.subprocess, 'run', side_effect=AssertionError('external process forbidden')) as run, patch.object(renderer.tempfile, 'TemporaryDirectory', side_effect=AssertionError('renderer writes forbidden')) as temporary:
    try:
        renderer.render('forbidden-pandoc', 'forbidden-xelatex')
    except StopIteration:
        result['renderer'] = {'observed': 'StopIteration at obsolete author lookup', 'subprocess_calls': run.call_count, 'temporary_directory_calls': temporary.call_count}
    else:
        raise AssertionError('Expected current author lookup failure')

with tempfile.TemporaryDirectory(prefix='release-control-', dir=OUT) as directory:
    package = Path(directory) / 'synthetic_package'
    package.mkdir()
    payload = package / 'payload.txt'
    payload.write_bytes(b'original payload\n')
    entries = [('payload.txt', sha(payload))]
    manifest = package / 'MANIFEST.sha256'
    manifest.write_bytes(canonical.render(entries))
    sums_entries = sorted(entries + [('MANIFEST.sha256', sha(manifest))])
    sums = package / 'SHA256SUMS'
    sums.write_bytes(canonical.render(sums_entries))
    archive = package / f'{package.name}_2026-10-02.zip'
    full_entries = sorted(sums_entries + [('SHA256SUMS', sha(sums))])
    canonical.build_archive(package, archive, full_entries)
    positive = canonical.validate(package)
    assert positive == []
    canonical.build_archive(package, archive, sums_entries)
    missing = canonical.validate(package)
    assert missing == []
    with zipfile.ZipFile(archive) as zipped:
        absent = f'{package.name}/SHA256SUMS' not in zipped.namelist()
    assert absent
    result['missing_archive_sums'] = {'baseline_errors': positive, 'omitted_control_errors': missing, 'SHA256SUMS_absent': absent,
                                    'limit': 'Validator accepts a synthetic canonical archive without outer checksum control although full builder includes it. Payload and inner manifest still bind; no arbitrary payload forgery.'}
    payload.write_bytes(b'mutated after admission\n')
    try:
        canonical.build_archive(package, archive, full_entries)
    except ValueError as error:
        result['canonical_mutation_control'] = {'rejected': True, 'error': str(error)}
    else:
        raise AssertionError('Canonical writer must detect stale digest')
    payload.write_bytes(b'original payload\n')
    original_sha = builder.sha256_of
    mutations = []
    def mutate_after_hash(path):
        digest = original_sha(path)
        if path == payload:
            path.write_bytes(b'mutated after admission\n')
            mutations.append(path.name)
        return digest
    with patch.object(builder, 'ROOT', package), patch.object(builder, 'sha256_of', side_effect=mutate_after_hash):
        builder.build_archive(archive, sums_entries)
    with zipfile.ZipFile(archive) as zipped:
        body = zipped.read(f'{package.name}/payload.txt')
        archived_manifest = zipped.read(f'{package.name}/MANIFEST.sha256')
    assert mutations == ['payload.txt'] and hashlib.sha256(body).hexdigest() != entries[0][1]
    assert entries[0][1].encode() in archived_manifest
    result['auxiliary_builder_mutation'] = {'mutated_paths': mutations, 'archived_payload_digest': hashlib.sha256(body).hexdigest(), 'admitted_payload_digest': entries[0][1],
        'mismatch_accepted': True, 'limit': 'Simulated concurrent mutation between hash admission and second read. Canonical writer rejects the same stale digest; not a break of hashes or arbitrary trusted-writer compromise.'}

after = {row['path']: sha(ROOT / row['path']) for row in scope['files']}
assert before == after
result['all_41_original_hashes_unchanged'] = True
path = REV / 'additional_paper_011_support_probes.json'
path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'current_manifest_error_counts': {k: len(v) for k,v in result['current_manifest_errors'].items()},
                  'canonical': result['current_canonical_errors'], 'renderer': result['renderer'],
                  'synthetic_controls': ['missing archive sums accepted', 'canonical stale digest rejected', 'auxiliary concurrent mutation mismatch accepted'],
                  'source_hashes_unchanged': True}))
