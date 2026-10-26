"""Pilot035 I/O: the pinned MUB executable owns finite answer decisions."""
from __future__ import annotations

import json
import subprocess
from hashlib import sha256
from pathlib import Path

from omega_engine_pfp.domain.pfp_ingress import strict_json

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'omega_engine_operads/data/pilots/pilot035'


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def public_task() -> dict:
    return strict_json((DATA / 'task.json').read_text(encoding='utf-8'))


def answer_schema() -> dict:
    return strict_json((DATA / 'answer.schema.json').read_text(encoding='utf-8'))


class NativeTaoChecker:
    """Explicit local binary, no implicit build, mutable pin or provider fallback."""
    def __init__(self, binary: Path, binary_sha256: str):
        self.binary = Path(binary).resolve()
        self.binary_sha256 = binary_sha256
        self._current()

    def _current(self):
        if not self.binary.is_file():
            raise ValueError('CHECKER_UNAVAILABLE: supply the MUB Tao verifier executable')
        if sha256(self.binary.read_bytes()).hexdigest() != self.binary_sha256:
            raise ValueError('CHECKER_BINARY_CHANGED')

    def check(self, answer: dict) -> dict:
        self._current()
        raw = canonical(answer)
        if len(raw) > 65536:
            raise ValueError('PILOT035_CANDIDATE_TOO_LARGE')
        try:
            result = subprocess.run([str(self.binary), '--check-stdin'], input=raw,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, shell=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError('CHECKER_UNAVAILABLE: ' + type(exc).__name__) from exc
        self._current()
        if result.returncode:
            raise ValueError('CHECKER_REFUSED: ' + result.stderr.decode('utf-8', errors='replace')[:400])
        checked = strict_json(result.stdout.decode('utf-8'))
        if (type(checked) is not dict or checked.get('schema_version') != 'omega.mub.pilot035-check.v1'
                or checked.get('candidate_sha256') != sha256(raw).hexdigest()
                or checked.get('authority_effect') != 'None'
                or checked.get('scope') != 'explicit_phase_table_only'
                or type(checked.get('accepted')) is not bool or type(checked.get('findings')) is not list
                or any(type(row) is not dict or set(row) != {'code', 'field'}
                    or any(type(row[key]) is not str or not row[key] for key in ('code', 'field'))
                    for row in checked.get('findings', []))
                or checked['accepted'] != (not checked['findings'])):
            raise ValueError('CHECKER_OUTPUT_BINDING_MISMATCH')
        return {**checked, 'checker_binary_sha256': self.binary_sha256,
                'raw_output_sha256': sha256(result.stdout).hexdigest()}

    def validate_task(self, task: dict) -> None:
        self._current()
        try:
            result = subprocess.run([str(self.binary), '--public-input'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, shell=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError('CHECKER_UNAVAILABLE: ' + type(exc).__name__) from exc
        self._current()
        if result.returncode:
            raise ValueError('CHECKER_PUBLIC_INPUT_UNAVAILABLE')
        public = strict_json(result.stdout.decode('utf-8'))
        if (type(public) is not dict or set(public) != {'matrix_id','phase_table','scope','definition','version'}
                or canonical({key:task.get(key) for key in public}) != canonical(public)):
            raise ValueError('PILOT035_NATIVE_INPUT_MISMATCH')
