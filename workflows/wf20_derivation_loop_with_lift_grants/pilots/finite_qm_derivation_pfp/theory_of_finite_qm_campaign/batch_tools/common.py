"""Shared helpers for the reusable PFP batch toolkit.

Nothing here accepts a theorem, calls a provider or touches the network. A batch is a folder
dag/results/batches/<batch_id>/ plus per-node run folders dag/results/<NODE>/runs/<run_id>/.
The repository root is found from this file or from PFP_ROOT/--root; no machine path is
hard-coded, and the Lean version is read from lean4/lean-toolchain, never named in code.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parents[2]
LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
BATCH_SCHEMA = 'finite-qm.ordered-batch.v1'
STAGES = ('P0_MINE_OPERAD', 'P1_DERIVE', 'P2_VERIFY', 'P3_REPAIR', 'P4_CHALLENGE', 'P5_RECORD')
# next_test strings that carry no obligation of their own (plan item 8). A real one names the unpaid bridge.
BOILERPLATE_NEXT_TEST = re.compile(
    r'^\s*(?:challenge every output coordinate and strict custody/type boundary, then address the explicit unpaid '
    r'mathematical bridge\.?|n/?a|none|todo|tbd|next test|run more tests\.?)\s*$', re.I)


class DiskSpaceError(RuntimeError):
    """Raised before a native build when the volume cannot hold it (an earlier batch hit errno 28)."""


def sha(data) -> str:
    return hashlib.sha256(data if isinstance(data, bytes) else Path(data).read_bytes()).hexdigest()


def load_json(path) -> object:
    return json.loads(Path(path).read_bytes())


def load_yaml(path_or_bytes):
    data = path_or_bytes if isinstance(path_or_bytes, bytes) else Path(path_or_bytes).read_bytes()
    return yaml.load(data, Loader=LOADER)


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def yaml_bytes(value) -> bytes:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100).encode('utf-8')


def save(path, value):
    """Write a JSON artifact; sealed evidence is never overwritten."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError('Refusing overwrite: ' + str(path))
    path.write_bytes(json_bytes(value))


def yaml_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError('Refusing overwrite: ' + str(path))
    path.write_bytes(yaml_bytes(value))


def replace_bytes(path, data: bytes):
    """Atomic replace for canonical files that are meant to change (operad records, the index)."""
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(data)
    os.replace(temporary, path)


def utc_stamp(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).strftime('%Y%m%dT%H%M%SZ')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------ context
class Ctx:
    """One repository tree (the real one, or a temporary copy under test)."""

    def __init__(self, root=None):
        root = Path(root or os.environ.get('PFP_ROOT') or DEFAULT_ROOT).resolve()
        if not (root / 'dag/pfp/prepare_stage.py').is_file():
            raise ValueError('Not a PFP tree (dag/pfp/prepare_stage.py missing): ' + str(root))
        self.root = root
        self._prepare = None

    @property
    def prepare(self):
        if self._prepare is None:
            self._prepare = load_module('pfp_prepare_stage_' + hashlib.sha1(str(self.root).encode()).hexdigest()[:8],
                                        self.root / 'dag/pfp/prepare_stage.py')
        return self._prepare

    @property
    def batches(self) -> Path:
        return self.root / 'dag/results/batches'

    @property
    def index_path(self) -> Path:
        return self.root / 'dag/operads/index.json'

    def index(self):
        return load_json(self.index_path)

    def rel(self, path) -> str:
        return Path(path).resolve().relative_to(self.root).as_posix()

    def batch_dir(self, batch) -> Path:
        path = Path(batch)
        if path.is_absolute():
            return path.resolve()
        for base in (Path.cwd(), self.root, self.batches):
            if (base / path).is_dir():
                return (base / path).resolve()
        raise ValueError('No such batch folder: %s (looked in the working directory, the root and %s)' % (batch, self.batches))

    def custody(self):
        """The sealed filename-custody object when this tree has one; None in a minimal tree."""
        if not (self.root / 'dag/pfp/filename_custody.json').is_file():
            return None
        sys.path.insert(0, str(self.root / 'dag/pfp'))
        try:
            from custody import Custody
            return Custody(self.root)
        finally:
            sys.path.pop(0)

    def git(self, *args, check=True) -> str:
        try:
            result = subprocess.run(['git', *args], cwd=self.root, capture_output=True, text=True)
        except OSError:
            return ''
        if check and result.returncode:
            raise ValueError('git ' + ' '.join(args) + ' failed: ' + result.stderr.strip())
        return result.stdout.strip() if not result.returncode else ''


# ------------------------------------------------------------------ toolchain
def lean_toolchain(ctx: Ctx) -> str:
    """The version named by lean4/lean-toolchain, e.g. 'v4.35.0'. Never hard-coded elsewhere."""
    path = ctx.root / 'lean4/lean-toolchain'
    if not path.is_file():
        raise ValueError('lean4/lean-toolchain missing: the Lean version is read from it')
    match = re.search(r'v?(\d+\.\d+\.\d+(?:-rc\d+)?)', path.read_text(encoding='utf-8'))
    if not match:
        raise ValueError('lean4/lean-toolchain names no version')
    return 'v' + match.group(1)


def check_lean_version(ctx: Ctx, reported: str) -> bool:
    """True when `lean --version` output names the toolchain version."""
    return lean_toolchain(ctx)[1:] in reported


def find_tool(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    home = Path.home()
    folder = {'cargo': '.cargo/bin', 'lean': '.elan/bin', 'lake': '.elan/bin'}.get(name)
    if folder:
        for candidate in ((home / folder / name).with_suffix('.exe'), home / folder / name):
            if candidate.is_file():
                return str(candidate)
    raise ValueError('Tool not found on PATH or in its usual home folder: ' + name)


def lean_environment(ctx: Ctx) -> dict:
    libs = [ctx.root / 'lean4/.lake/build/lib/lean']
    packages = Path(os.environ.get('PFP_LEAN_PACKAGES') or ctx.root / 'lean4/.lake/packages')
    if packages.is_dir():
        libs += [p / '.lake/build/lib/lean' for p in sorted(packages.iterdir()) if (p / '.lake/build/lib/lean').is_dir()]
    return {'LEAN_PATH': os.pathsep.join(str(p) for p in libs)}


# ------------------------------------------------------------------ disk and cargo guard
def free_gb(path) -> float:
    path = Path(path)
    while not path.exists() and path != path.parent:
        path = path.parent
    return shutil.disk_usage(path).free / 2 ** 30


def disk_precheck(path, need_gb: float, label: str = 'native build'):
    """Refuse to start when the volume holding `path` has less than `need_gb` free."""
    available = free_gb(path)
    if available < need_gb:
        raise DiskSpaceError('%s needs %.1f GiB free on the volume of %s; only %.1f GiB available. '
                             'Clear a cargo target or free space first.' % (label, need_gb, path, available))
    return available


def tree_gb(path) -> float:
    total = 0
    for folder, _, names in os.walk(path):
        for name in names:
            try:
                total += os.path.getsize(os.path.join(folder, name))
            except OSError:
                pass
    return total / 2 ** 30


def default_cargo_target() -> Path:
    return Path.home() / '.pfp-ct'


def _force_remove(function, path, _):
    os.chmod(path, 0o700)
    function(path)


def cargo_target_guard(target=None, *, min_free_gb: float = 20.0, max_target_gb: float = 6.0,
                       max_path_chars: int = 40, clear: bool = True) -> dict:
    """Pick a short CARGO_TARGET_DIR, pre-clear it when large and check free space.

    Rust replays of earlier batches filled the disk (errno 28) and long Windows target paths hit
    MAX_PATH. Returns {'env': {...}, 'report': {...}}; raises DiskSpaceError if still too full.
    """
    target = Path(target or os.environ.get('CARGO_TARGET_DIR') or default_cargo_target())
    if os.name == 'nt' and len(str(target)) > max_path_chars:
        raise ValueError('CARGO_TARGET_DIR is too long for Windows paths (%d > %d): %s' % (len(str(target)), max_path_chars, target))
    size_before = tree_gb(target) if target.exists() else 0.0
    cleared = False
    if clear and target.exists() and size_before > max_target_gb:
        shutil.rmtree(target, onerror=_force_remove)
        cleared = True
    target.mkdir(parents=True, exist_ok=True)
    available = disk_precheck(target, min_free_gb, 'Rust replay')
    return {'env': {'CARGO_TARGET_DIR': str(target), 'CARGO_INCREMENTAL': '0'},
            'report': {'target': str(target), 'size_gb_before': round(size_before, 3), 'cleared': cleared,
                       'free_gb_after': round(available, 3), 'min_free_gb': min_free_gb, 'max_target_gb': max_target_gb}}


# ------------------------------------------------------------------ native calls
def native_record(folder, label, command, *, cwd, sources=(), stdin=None, env=None, tool_sources=()):
    """Run one command and retain argv, cwd, environment overrides, logs and source pins before/after."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    receipt_path = folder / (label + '_receipt.json')
    if receipt_path.exists():
        raise ValueError('Native call already recorded: ' + str(receipt_path))
    sources = list(dict.fromkeys(Path(p) for p in sources))
    tools = list(dict.fromkeys(Path(p) for p in tool_sources))
    pins = [{'path': str(p), 'sha256': sha(p)} for p in sources]
    tool_pins_before = [{'path': str(p), 'sha256': sha(p)} for p in tools]
    overrides = {'PYTHONDONTWRITEBYTECODE': '1', **(env or {})}
    started = datetime.now(timezone.utc).isoformat()
    begin = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, env=dict(os.environ, **overrides), input=stdin,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = folder / (label + '.stdout.log'), folder / (label + '.stderr.log')
    out.write_bytes(result.stdout)
    err.write_bytes(result.stderr)
    unchanged = all(sha(Path(p['path'])) == p['sha256'] for p in pins + tool_pins_before)
    receipt = {'argv': [str(c) for c in command], 'cwd': str(cwd), 'started_utc': started,
               'seconds': round(time.perf_counter() - begin, 3), 'exit_code': result.returncode,
               'environment_overrides': overrides, 'source_pins': pins, 'tool_pins': tool_pins_before, 'sources_unchanged': unchanged,
               'stdin_sha256': None if stdin is None else hashlib.sha256(stdin).hexdigest(),
               'stdout': out.name, 'stderr': err.name}
    receipt_path.write_bytes(json_bytes(receipt))
    if not unchanged:
        raise ValueError('Source mutated during native call: ' + label)
    return receipt


def require(condition, message):
    if not condition:
        raise ValueError(message)


def tool_pins(ctx: Ctx) -> list:
    """Digest of the shared toolkit and stage helper bytes a batch was produced with (informational)."""
    names = sorted((ctx.root / 'dag/pfp/batch_tools').glob('*.py'))
    names += [ctx.root / 'dag/pfp' / n for n in ('prepare_stage.py', 'custody.py', 'exact_json.py', 'validate_prompts.py')]
    return [{'path': ctx.rel(p), 'sha256': sha(p)} for p in names if p.is_file()]
