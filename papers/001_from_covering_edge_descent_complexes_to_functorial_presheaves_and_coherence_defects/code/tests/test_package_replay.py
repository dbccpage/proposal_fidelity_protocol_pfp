"""Exercise fresh notebook execution and refusal of stale claim evidence."""

import importlib.util
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('po001_verify_package', ROOT / 'scripts/verify_package.py')
assert spec is not None and spec.loader is not None
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


@pytest.mark.parametrize('cwd', [ROOT, ROOT / 'jupyter_notebooks'])
def test_notebook_assertions_in_fresh_python_process_from_both_directories(cwd):
    result = verifier.replay_notebook(cwd)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize('mutation', ['missing_test', 'stale_tex'])
def test_stale_evidence_or_reader_source_is_rejected(tmp_path, mutation):
    # Use a complete isolated package, then mutate one evidence association.
    shutil.copytree(ROOT, tmp_path, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache', 'build'))
    if mutation == 'missing_test':
        target = tmp_path / 'code/tests/test_review_boundaries.py'
        target.write_text(target.read_text().replace(
            'def test_master_normal_form_requires_commuting_cover_paths(',
            'def renamed_refusal_test('))
        assert any('missing evidence test:' in error and 'requires_commuting_cover_paths' in error
                   for error in verifier.check_evidence(tmp_path))
    else:
        target = tmp_path / 'covering_edge_descent.tex'
        target.write_text(target.read_text().replace('Canonical Markdown SHA256:', 'Stale Markdown SHA256:'))
        assert any('TeX source digest differs' in error for error in verifier.check_evidence(tmp_path))
