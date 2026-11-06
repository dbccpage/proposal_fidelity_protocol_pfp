"""Commit (and, only on explicit flags, push and open a PR for) a sealed batch.

Stages exactly the files named by manifest.json, refuses any other change in the work tree or index,
and refuses if a sealed byte changed. Push and PR are separate flags and are never implied.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_json, require, sha  # noqa: E402
from stages import Batch  # noqa: E402


def owned_paths(batch: Batch):
    manifest = load_json(batch.dir / 'manifest.json')
    for pin in manifest['files']:
        require(sha(batch.ctx.root / pin['path']) == pin['sha256'], 'Seal drift ' + pin['path'])
    return {p['path'] for p in manifest['files']} | {batch.ctx.rel(batch.dir / 'manifest.json')}


def publish(batch: Batch, message, *, trailer='', push=False, pr_title=None, remote='origin'):
    ctx = batch.ctx
    owned = owned_paths(batch)
    require(not ctx.git('diff', '--cached', '--name-only'), 'Index already holds staged changes')
    status = subprocess.run(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'], cwd=ctx.root, capture_output=True).stdout.split(b'\0')
    for entry in status:
        if entry and entry[3:].decode() not in owned:
            raise ValueError('Unowned change in the work tree: ' + entry[3:].decode())
    subprocess.run(['git', 'add', '--pathspec-from-file=-', '--pathspec-file-nul'], cwd=ctx.root, input=b'\0'.join(p.encode() for p in sorted(owned)) + b'\0', check=True)
    staged = {p for p in ctx.git('diff', '--cached', '--name-only', '-z').split('\0') if p}
    require(staged and staged <= owned, 'Staged scope differs from the manifest')
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ctx.root, check=True)
    body = message + ('\n\n' + trailer if trailer else '')
    subprocess.run(['git', 'commit', '--quiet', '-m', body], cwd=ctx.root, check=True)
    commit = ctx.git('rev-parse', 'HEAD')
    result = {'commit': commit, 'staged_files': len(staged), 'pushed': False, 'pr': None}
    if push:
        branch = ctx.git('branch', '--show-current')
        subprocess.run(['git', 'push', '--set-upstream', remote, branch], cwd=ctx.root, check=True)
        result['pushed'] = True
        if pr_title:
            body_file = batch.dir / 'review/pr_body.md'
            command = ['gh', 'pr', 'create', '--title', pr_title] + (['--body-file', str(body_file)] if body_file.is_file() else ['--body', pr_title])
            result['pr'] = subprocess.check_output(command, cwd=ctx.root, text=True).strip()
    return result
