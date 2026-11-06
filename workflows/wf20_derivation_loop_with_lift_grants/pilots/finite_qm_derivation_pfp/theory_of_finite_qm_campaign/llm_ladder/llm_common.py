"""Shared helpers for the PFP LLM ladder: secrets, redaction, canonical bytes, atomic files.

AuthorityEffect: None. Nothing here accepts a theorem.

Credential discovery is ported (with attribution) from the_symbol_game
omega_engine_woland/infrastructure/providers/credential_source.py: an explicit .env path, then the
process environment, then the .env at the checkout root, then the .env of the main checkout when
running in a linked git worktree. Only those files are read, nothing walks parent directories,
nothing is written to os.environ, and a value is never placed in a log, a receipt or an error.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ENV_FILE_NAME = '.env'
SECRET_NAMES = ('ANTHROPIC_API_KEY', 'OPENROUTER_API_KEY', 'GROQ_API_KEY', 'CEREBRAS_API_KEY', 'NVIDIA_API_KEY')
CONFIG_NAMES = ('OPENROUTER_MODEL', 'ANOMALON_LLM_PROVIDER', 'OEARS_OLLAMA_HOST')
REDACTED = '[REDACTED]'

# Key-shaped strings. Tests build their fixtures at run time so no literal match is ever committed.
KEY_PATTERNS = {
    'anthropic': re.compile(r'sk-ant-[A-Za-z0-9_\-]{16,}'),
    'openrouter': re.compile(r'sk-or-[A-Za-z0-9_\-]{16,}'),
    'groq': re.compile(r'gsk_[A-Za-z0-9]{16,}'),
    'cerebras': re.compile(r'csk-[A-Za-z0-9]{16,}'),
    'nvidia': re.compile(r'nvapi-[A-Za-z0-9_\-]{16,}'),
    'openai_style': re.compile(r'\bsk-[A-Za-z0-9]{32,}'),
    'bearer_header': re.compile(r'(?i)authorization["\']?\s*[:=]\s*["\']?bearer\s+[A-Za-z0-9._\-]{20,}'),
    'x_api_key_header': re.compile(r'(?i)x-api-key["\']?\s*[:=]\s*["\']?[A-Za-z0-9._\-]{20,}'),
}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def iso_week(when: datetime | None = None) -> str:
    year, week, _ = (when or datetime.now(timezone.utc)).isocalendar()
    return '%04d-W%02d' % (year, week)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode('utf-8'))


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + '\n').encode('utf-8')


def atomic_write(path, data: bytes) -> None:
    """Write via a temp file in the same directory and replace; LF bytes only."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=str(path.parent), prefix='.tmp-', suffix='.part')
    try:
        with os.fdopen(handle, 'wb') as stream:
            stream.write(data)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def write_new(path, data: bytes) -> None:
    """Create a file; sealed evidence is never overwritten."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


class FileLock:
    """Advisory lock by exclusive creation of a sidecar file; stale locks expire."""

    def __init__(self, path, timeout=30.0, stale=120.0):
        self.path = Path(str(path) + '.lock')
        self.timeout, self.stale = timeout, stale
        self._held = False

    def __enter__(self):
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                descriptor = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(descriptor, str(os.getpid()).encode())
                os.close(descriptor)
                self._held = True
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > self.stale:
                        self.path.unlink()
                        continue
                except OSError:
                    pass
                if time.monotonic() > deadline:
                    raise TimeoutError('ledger lock busy: ' + self.path.name)
                time.sleep(0.05)

    def __exit__(self, *exc):
        if self._held:
            try:
                self.path.unlink()
            except OSError:
                pass
            self._held = False


# --------------------------------------------------------------------------- credentials
def parse_env_text(text: str) -> dict:
    """KEY=VALUE lines; comments and blanks skipped; one pair of quotes removed. No expansion."""
    out = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        if line.startswith('export '):
            line = line[len('export '):]
        key, _, value = line.partition('=')
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
            value = value[1:-1]
        out[key.strip()] = value
    return out


def main_checkout_root(checkout: Path, marker: Path):
    """Root of the main checkout when `checkout` is a linked worktree (read from git pointer files)."""
    try:
        if marker.is_dir():
            return checkout
        text = marker.read_text(encoding='utf-8').strip()
        if not text.startswith('gitdir:'):
            return None
        gitdir = Path(text[len('gitdir:'):].strip())
        if not gitdir.is_absolute():
            gitdir = marker.parent / gitdir
        gitdir = gitdir.resolve()
        pointer = gitdir / 'commondir'
        if not pointer.is_file():
            return None
        common = (gitdir / pointer.read_text(encoding='utf-8').strip()).resolve()
    except OSError:
        return None
    return common.parent if common.name == '.git' else None


def env_file_candidates(start: Path | None = None) -> list:
    """The only files discovery may read: this checkout's .env, then the main checkout's .env."""
    start = Path(start or ROOT).resolve()
    for directory in (start, *start.parents):
        marker = directory / '.git'
        if marker.exists():
            found = [directory / ENV_FILE_NAME]
            main = main_checkout_root(directory, marker)
            if main is not None and main != directory:
                found.append(main / ENV_FILE_NAME)
            # a worktree nested in another worktree: also follow the outer checkout's pointer
            outer = None
            for parent in directory.parents:
                if (parent / '.git').exists():
                    outer = parent
                    break
            if outer is not None:
                root = main_checkout_root(outer, outer / '.git')
                for candidate in (outer, root):
                    if candidate is not None and (candidate / ENV_FILE_NAME) not in found:
                        found.append(candidate / ENV_FILE_NAME)
            return found
    return []


def load_env(names=SECRET_NAMES + CONFIG_NAMES, *, environ=None, env_file=None, root=None) -> dict:
    """Resolve named variables. Values only ever live in the returned dict (never in os.environ)."""
    resolved = {}
    env = os.environ if environ is None else environ
    files = [Path(env_file)] if env_file else []
    if environ is None:
        files += env_file_candidates(root)
    parsed = []
    for path in files:
        if path.is_file():
            try:
                parsed.append(parse_env_text(path.read_bytes().decode('utf-8-sig')))
            except (OSError, UnicodeDecodeError):
                continue
    for name in names:
        value = ''
        if parsed and env_file:
            value = (parsed[0].get(name) or '').strip()
        value = value or (env.get(name) or '').strip()
        if not value:
            for table in parsed:
                value = (table.get(name) or '').strip()
                if value:
                    break
        if value:
            resolved[name] = value
    return resolved


# --------------------------------------------------------------------------- redaction
class Redactor:
    """Replaces known secret values and any key-shaped string. Safe to call on any text."""

    def __init__(self, secrets=()):
        self._secrets = sorted({s for s in secrets if isinstance(s, str) and len(s) >= 8}, key=len, reverse=True)

    def add(self, *values):
        self.__init__(list(self._secrets) + [v for v in values if v])

    def redact(self, text) -> str:
        if text is None:
            return ''
        text = text if isinstance(text, str) else str(text)
        for secret in self._secrets:
            if secret in text:
                text = text.replace(secret, REDACTED)
        for pattern in KEY_PATTERNS.values():
            text = pattern.sub(REDACTED, text)
        return text

    def redact_obj(self, value):
        if isinstance(value, str):
            return self.redact(value)
        if isinstance(value, dict):
            return {self.redact(k) if isinstance(k, str) else k: self.redact_obj(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.redact_obj(v) for v in value]
        return value


def scan_text_for_keys(text: str, secrets=()) -> list:
    """Names of key-shaped patterns (and known secret values) found in text. Never returns the match."""
    found = []
    for name, pattern in KEY_PATTERNS.items():
        if pattern.search(text):
            found.append(name)
    for secret in secrets:
        if isinstance(secret, str) and len(secret) >= 8 and secret in text:
            found.append('known_secret_value')
    return found


def scan_paths_for_keys(paths, secrets=(), max_bytes=8_000_000) -> list:
    """[(path, [pattern names])] for files that contain a key-shaped string or a known secret value."""
    hits = []
    for path in paths:
        path = Path(path)
        try:
            if not path.is_file() or path.stat().st_size > max_bytes:
                continue
            text = path.read_bytes().decode('utf-8', errors='replace')
        except OSError:
            continue
        names = scan_text_for_keys(text, secrets)
        if names:
            hits.append((str(path), sorted(set(names))))
    return hits
