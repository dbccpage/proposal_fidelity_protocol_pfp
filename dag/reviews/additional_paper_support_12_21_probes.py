"""Read-only source custody checks and isolated package-wrapper countercontrols.

No source package is modified, no compiler/provider subprocess is launched.
Synthetic fixtures are retained under dag/reviews for inspection.
"""
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_suffix('.json')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    packages = {n: next((ROOT / 'papers/pfp').glob(f'{n:03d}_*')) for n in (13, 20)}
    result = {'scope': 'Structural custody and isolated wrapper probes only; historical execution and archive-member mathematics are not certified.', 'packages': [], 'probes': []}
    for number, package in packages.items():
        item = {'number': number, 'manifests': [], 'archives': []}
        for name in ('MANIFEST.sha256', 'SHA256SUMS'):
            source = package / name
            records = []
            for line in source.read_text().splitlines():
                if not line or line.startswith('#'):
                    continue
                digest, relative = line.split('  ', 1)
                pure = PurePosixPath(relative)
                assert not pure.is_absolute() and '..' not in pure.parts
                target = package / relative
                raw = target.read_bytes() if target.is_file() else None
                try:
                    normalized = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n').encode() if raw is not None else None
                except UnicodeDecodeError:
                    normalized = None
                records.append({'path': relative, 'expected_sha256': digest,
                    'exists': target.is_file(), 'matches_raw_bytes': raw is not None and hashlib.sha256(raw).hexdigest() == digest,
                    'matches_universal_lf': normalized is not None and hashlib.sha256(normalized).hexdigest() == digest})
            item['manifests'].append({'path': source.relative_to(ROOT).as_posix(), 'records': records})
        for source in package.glob('*.zip'):
            with zipfile.ZipFile(source) as archive:
                records = []
                for info in archive.infolist():
                    data = archive.read(info)
                    pure = PurePosixPath(info.filename)
                    relative = '/'.join(pure.parts[1:])
                    target = package / relative
                    records.append({'member': info.filename, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                        'safe_posix_name': not pure.is_absolute() and '..' not in pure.parts,
                        'current_path': target.relative_to(ROOT).as_posix(), 'current_exists': target.is_file(),
                        'current_raw_equal': target.is_file() and target.read_bytes() == data,
                        'current_newline_equal': target.is_file() and target.read_bytes().replace(b'\r\n', b'\n') == data.replace(b'\r\n', b'\n')})
                item['archives'].append({'path': source.relative_to(ROOT).as_posix(), 'crc_error_member': archive.testzip(),
                    'casefold_names_unique': len({i.filename.casefold() for i in archive.infolist()}) == len(archive.infolist()), 'records': records})
        result['packages'].append(item)
    load('deposit_paths', packages[13] / 'code/deposit_paths.py')
    verifier13 = load('paper13_verifier_probe', packages[13] / 'verify_deposit.py')
    verifier20 = load('paper20_verifier_probe', packages[20] / 'verify_deposit.py')
    for number, verifier in ((13, verifier13), (20, verifier20)):
        result['probes'].append({'id': f'P{number}-current-manifest', 'errors': verifier.check_manifest(verifier.MANIFEST)})
    fixtures = Path(tempfile.mkdtemp(prefix='paper-support-controls-', dir=ROOT / 'dag/reviews')).resolve()
    assert fixtures.is_relative_to((ROOT / 'dag/reviews').resolve())
    lean = fixtures / 'census' / 'lean4'
    lean.mkdir(parents=True)
    (lean / 'lakefile.lean').write_text('-- synthetic configured package\n')
    (lean / 'Core.lean').write_text('axiom unsupported : False\n')
    verifier13.ROOT = lean.parent
    with patch.object(verifier13.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='', stderr='')) as fake:
        errors = verifier13.check_lean()
        result['probes'].append({'id': 'P13-empty-census-output', 'errors': errors, 'fake_subprocess_calls': fake.call_count,
            'interpretation': 'Wrapper accepts successful process exits with no printed declaration census. This is a fake-process control, not a Lean execution or a claim this paper contains that axiom.'})
    package20 = fixtures / 'write-manifest'
    package20.mkdir()
    (package20 / 'MANIFEST.sha256').write_text('old manifest bytes\n')
    (package20 / 'example.txt').write_text('fixed payload\n')
    verifier20.ROOT = package20
    verifier20.write_manifests()
    try:
        verifier20.read_manifest(package20, package20 / 'MANIFEST.sha256')
        error = None
    except ValueError as exc:
        error = str(exc)
    result['probes'].append({'id': 'P20-write-self-reference', 'error': error,
        'interpretation': 'The writer includes the prior MANIFEST.sha256 bytes in both newly written identical manifests; its own reader rejects the resulting circular MANIFEST entry.'})
    result['fixture_directory'] = fixtures.relative_to(ROOT).as_posix()
    OUT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'packages': len(result['packages']), 'probes': result['probes'], 'output': OUT.relative_to(ROOT).as_posix()}))


if __name__ == '__main__':
    main()
