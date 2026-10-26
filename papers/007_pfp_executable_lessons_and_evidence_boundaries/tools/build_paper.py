#!/usr/bin/env python3
"""Regenerate the manuscript TeX/PDF using Pandoc and XeLaTeX.

Uses the deposited TeX preamble and the Markdown body. Build intermediates and
command receipts stay in the excluded build/paper_pdf directory. Intentional
PDF/source changes require a fresh validation and rebuilt release manifests.
"""

import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
temp = root / 'build' / 'paper_pdf'
temp.mkdir(parents=True, exist_ok=True)
markdown = (root / 'paper.md').read_text()
(temp / 'body.md').write_text(markdown[markdown.index('Source audit baseline:'):])
records = []


def run(command):
    started = time.time()
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=55)
    records.append({'command': command, 'exit_code': result.returncode,
                    'elapsed_seconds': round(time.time()-started, 3),
                    'stdout': result.stdout, 'stderr': result.stderr})
    if result.returncode:
        raise RuntimeError(result.stdout[-3000:] + result.stderr[-3000:])


run(['pandoc', str(temp / 'body.md'),
     '--from=markdown+tex_math_dollars+tex_math_single_backslash', '--to=latex',
     '--listings', '--wrap=auto', '--output', str(temp / 'body.tex')])
old = (root / 'paper.tex').read_text()
marker = '\n\\makeatother\n\n'
prefix = old[:old.index(marker, old.index('\\begin{document}')) + len(marker)]
prefix = re.sub(r'\\date\{[^}]*\}', lambda _: r'\date{2026-10-02 · Version 0.1.0 · Curriculum-design preprint · First-publication review}', prefix)
prefix = prefix.replace('keepspaces=true}', 'keepspaces=true,showstringspaces=false}')
if '\\usepackage{needspace}' not in prefix:
    prefix = prefix.replace('\\usepackage{longtable,booktabs,array}',
                            '\\usepackage{longtable,booktabs,array}\n\\usepackage{needspace}')
if '\\AtBeginEnvironment{longtable}{\\small}' not in prefix:
    prefix = prefix.replace('\\begin{document}', '\\AtBeginEnvironment{longtable}{\\small}\n\\begin{document}')
body = (temp / 'body.tex').read_text()


def inline(match):
    content = match.group(1)
    if ' ' in content:
        return '\\texttt{' + content + '}'
    if len(content) > 25 or '\\_' in content or '/' in content:
        return '\\texttt{\\nolinkurl{' + content.replace('\\_', '_') + '}}'
    return match.group(0)


body = re.sub(r'\\passthrough\{\\lstinline!(.*?)!\}', inline, body)


def notebook_link(match):
    label = match.group(2).replace('\\_', '\\_\\allowbreak{}')
    return '\\href{' + match.group(1) + '}{\\texttt{' + label + '}}'


body = re.sub(r'\\href\{([^}]+)\}\{([^}]+\.ipynb)\}', notebook_link, body)


def keep_listing(match):
    lines = match.group(0).splitlines()[1:-1]
    needed = len(lines) + sum(max(0, (len(line) - 1) // 90) for line in lines) + 2
    return '\\Needspace{' + str(needed) + '\\baselineskip}\n' + match.group(0)


body = re.sub(r'\\begin\{lstlisting\}.*?\\end\{lstlisting\}', keep_listing, body, flags=re.S)


def table_widths(match):
    table = match.group(0)
    if 'Notebook' in table and 'Group' in table:
        widths = iter(('0.1500', '0.3800', '0.4700'))
        table = '\\clearpage\n' + table
        table = re.sub(r'\\real\{0\.3333\}', lambda _: '\\real{' + next(widths) + '}', table)
    return table


body = re.sub(r'\\begin\{longtable\}.*?\\end\{longtable\}', table_widths, body, flags=re.S)
(root / 'paper.tex').write_text(prefix + body + '\n\\end{document}\n')
for _ in range(2):
    run(['xelatex', '-halt-on-error', '-interaction=nonstopmode',
         '-output-directory', str(temp), str(root / 'paper.tex')])
shutil.copyfile(temp / 'paper.pdf', root / 'paper.pdf')
(temp / 'build_receipt.json').write_text(json.dumps(records, indent=2))
log = (temp / 'paper.log').read_text()
print(json.dumps({'pdf_bytes': (root / 'paper.pdf').stat().st_size,
                  'overfull_boxes': len(re.findall('Overfull', log)),
                  'missing_characters': len(re.findall('Missing character', log)),
                  'pdf_sha256': hashlib.sha256((root / 'paper.pdf').read_bytes()).hexdigest()}))
