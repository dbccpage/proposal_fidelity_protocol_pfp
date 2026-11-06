#!/usr/bin/env python3
"""Build the PO-001 TeX/PDF reader formats from canonical Markdown.

Requires Pandoc and XeLaTeX with the bundled preamble's TeX packages. The
source digest embedded in the TeX is an artifact association, not proof evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    for command in ['pandoc', 'xelatex']:
        if not shutil.which(command):
            raise SystemExit(f'required reader-build tool unavailable: {command}')
    source = (ROOT / 'covering_edge_descent.md').read_bytes()
    text = source.decode('utf-8')
    title = re.search(r'^# (.+)$', text, re.M).group(1)
    date = re.search(r'^\*Date:\* (.+)$', text, re.M).group(1)
    status = re.search(r'^\*Status:\* (.+)$', text, re.M).group(1)
    digest = hashlib.sha256(source).hexdigest()
    body = text.split('---', 1)[1].lstrip()
    env = dict(os.environ, SOURCE_DATE_EPOCH='1790899200', FORCE_SOURCE_DATE='1', TZ='UTC')
    with tempfile.TemporaryDirectory(prefix='po001-reader-') as directory:
        build = Path(directory)
        (build / 'body.md').write_text(body, encoding='utf-8')
        (build / 'metadata.json').write_text(json.dumps({
            'title': title,
            'subtitle': 'Strict Functorial Completion, Coboundary-Curvature Duality, and the Finite Obstruction Boundary',
            'author': 'Jeremy H. Carroll',
            'date': f'{date} · {status}',
            'lang': 'en',
            'papersize': 'a4',
            'fontsize': '10pt',
            'colorlinks': True,
        }), encoding='utf-8')
        tex = build / 'covering_edge_descent.tex'
        subprocess.run(['pandoc', str(build / 'body.md'), '--standalone', '--to=latex',
                        '--pdf-engine=xelatex', '--metadata-file', str(build / 'metadata.json'),
                        '--include-in-header', str(ROOT / 'scripts/obstruction-preamble.tex'),
                        '--lua-filter', str(ROOT / 'scripts/wrap_code.lua'), '--output', str(tex)],
                       cwd=build, env=env, check=True)
        tex.write_text(f'% Canonical Markdown SHA256: {digest}\n' + tex.read_text(encoding='utf-8'), encoding='utf-8')
        for _ in range(2):
            result = subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', tex.name],
                                    cwd=build, env=env, text=True, capture_output=True)
            if result.returncode:
                raise SystemExit(result.stdout[-10000:] + result.stderr[-2000:])
        log = (build / 'covering_edge_descent.log').read_text(encoding='utf-8')
        # Missing glyphs silently remove content, so treat them as build failures.
        missing = [line for line in log.splitlines() if 'Missing character:' in line]
        if missing:
            raise SystemExit('\n'.join(missing))
        for line in log.splitlines():
            if 'Overfull' in line:
                print(line)
        shutil.copyfile(tex, ROOT / tex.name)
        shutil.copyfile(build / 'covering_edge_descent.pdf', ROOT / 'covering_edge_descent.pdf')
    print(f'Built TeX/PDF from Markdown SHA256 {digest}')


if __name__ == '__main__':
    main()
