#!/usr/bin/env python3
"""Replay finite tests and check PO-001 artifact/evidence consistency.

These syntactic and computational checks do not prove manuscript claims or
replace a Lean kernel replay. Requires the declared pytest/PyYAML dependencies.
"""

from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib

import yaml

ROOT = Path(__file__).resolve().parent.parent
ALIAS = '001_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects.md'


def check_evidence(root: Path = ROOT) -> list[str]:
    """Check claim IDs/titles and every explicit Python test pointer."""
    errors: list[str] = []
    canonical = (root / 'covering_edge_descent.md').read_text(encoding='utf-8')
    if canonical != (root / ALIAS).read_text(encoding='utf-8'):
        errors.append('manuscript alias differs from canonical Markdown')
    ledger = yaml.safe_load((root / 'covering_edge_descent_claim_ledger.yaml').read_text(encoding='utf-8'))
    version = ledger['paper_identity']['canonical_version']
    project = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf-8'))['project']
    if f'*Status:* Pre-Print ({version})' not in canonical or 'v' + project['version'].rsplit('.', 1)[0] != version:
        errors.append('manuscript, claim ledger, and project versions differ')
    digest = hashlib.sha256((root / 'covering_edge_descent.md').read_bytes()).hexdigest()
    if not (root / 'covering_edge_descent.tex').read_text(encoding='utf-8').startswith(
            f'% Canonical Markdown SHA256: {digest}\n'):
        errors.append('TeX source digest differs from canonical Markdown; rebuild reader formats')
    claims = ledger['claims']
    expected = [f'PO001-C{i:02}' for i in range(1, 28)]
    if Counter(c['claim_id'] for c in claims) != Counter(expected):
        errors.append('YAML claim IDs must contain C01 through C27 exactly once')
    ledgermd = (root / 'covering_edge_descent_claim_ledger.md').read_text(encoding='utf-8')
    for name, content in [('manuscript appendix', canonical.split('## Appendix B:', 1)[-1]), ('Markdown ledger', ledgermd)]:
        rows = re.findall(r'^\| (\d+) \| (?:(PO001-C\d+) \| )?([^|]+) \|', content, flags=re.M)
        if Counter(int(i) for i, _, _ in rows) != Counter(range(1, 28)):
            errors.append(f'{name}: claim numbers must contain 1 through 27 exactly once')
        titles = {int(i): title.strip() for i, _, title in rows}
        cids = {int(i): cid.strip() for i, cid, _ in rows if cid}
        for c in claims:
            i = int(c['claim_id'][-2:])
            if i in cids and cids[i] != c['claim_id']:
                errors.append(f'{name}: claim ID mismatch for {c["claim_id"]}')
            if titles.get(i) != c['title']:
                errors.append(f'{name}: title mismatch for {c["claim_id"]}')
    checked: set[str] = set()
    for content in [canonical, ledgermd, json.dumps(ledger)]:
        for pointer in re.findall(r'(?:code/tests/)?test_[A-Za-z0-9_]+\.py::test_[A-Za-z0-9_]+', content):
            if pointer in checked:
                continue
            checked.add(pointer)
            filename, testname = pointer.split('::')
            path = root / 'code/tests' / Path(filename).name
            if not path.is_file():
                errors.append(f'missing evidence file: {pointer}')
                continue
            definitions = {n.name for n in ast.parse(path.read_text(encoding='utf-8')).body
                           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            if testname not in definitions:
                errors.append(f'missing evidence test: {pointer}')
    # Check local Markdown file links, leaving external URLs and heading-only
    # links to their own authorities. This is a file-existence check only.
    for path in root.rglob('*.md'):
        if any(p in {'.git', '.venv', 'build', '__pycache__'} for p in path.relative_to(root).parts):
            continue
        for target in re.findall(r'\]\(([^\s)]+)\)', path.read_text(encoding='utf-8')):
            if target.startswith('#') or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                continue
            filepart = target.split('#', 1)[0]
            if filepart and not (path.parent / filepart).exists():
                errors.append(f'{path.relative_to(root)}: missing local link {target}')
    return errors


def notebook_source(path: Path) -> str:
    """Extract ordinary Python cells, preserving a shared execution namespace."""
    notebook = json.loads(path.read_text(encoding='utf-8'))
    chunks = []
    for i, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            # compile() also refuses IPython magics: this replay is deliberately
            # ordinary Python, not a claim to have run a Jupyter kernel/widgets.
            compile(source, f'{path.name}:cell-{i}', 'exec')
            chunks.append(f'\n# cell {i}\n{source}\n')
    return ''.join(chunks)


def replay_notebook(cwd: Path, root: Path = ROOT) -> subprocess.CompletedProcess[str]:
    source = notebook_source(root / 'jupyter_notebooks/00_enter_po001.ipynb')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    # Do not let caller PYTHONPATH disguise an incorrect notebook root lookup.
    env.pop('PYTHONPATH', None)
    return subprocess.run([sys.executable, '-I', '-c', source], cwd=cwd,
                          env=env, text=True, capture_output=True, timeout=60)


def main() -> int:
    errors = check_evidence()
    if errors:
        for error in errors:
            print(f'FAIL: {error}')
        return 1
    print('OK: 27 claim IDs/titles, versions, manuscript alias, TeX digest, evidence tests, and local file links', flush=True)
    for cwd in [ROOT, ROOT / 'jupyter_notebooks']:
        result = replay_notebook(cwd)
        if result.returncode:
            print(result.stdout + result.stderr)
            return result.returncode
        print(f'OK: notebook ordinary-Python assertions from {cwd.name}', flush=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    for args in [[sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'],
                 [sys.executable, str(ROOT / 'scripts/regen_sha256sums.py'), '--check']]:
        result = subprocess.run(args, cwd=ROOT, env=env, check=False)
        if result.returncode:
            return result.returncode
    print('PASS: finite replay and artifact consistency; Lean not replayed', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
