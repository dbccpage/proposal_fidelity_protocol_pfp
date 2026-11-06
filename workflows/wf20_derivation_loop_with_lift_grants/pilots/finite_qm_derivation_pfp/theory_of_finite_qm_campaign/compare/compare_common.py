"""Shared helpers of the Solo-versus-swarm comparison harness.

AuthorityEffect: None. Nothing here accepts a theorem and nothing here calls a provider.

What lives here, so that the two arms and the scorer cannot drift apart:
  * the frozen protocol and cohort (load_cohort refuses to run when protocol.md no longer matches the sha256
    recorded in cohort.json);
  * the CLEAN ROOM: a source-only copy of the repository at the freeze commit of one prompt, taken with
    `git archive`, from which dag/results/** and every Arm F artifact are removed. Both arms compile the same
    packet bytes from it, and the host verifier checks claims against it, so a model can never be credited for
    (or shown) a declaration that exists only because Solo wrote it later;
  * the packet loaders (compile from the clean room, or replay the stored request of an earlier expensive
    attempt byte for byte) and the leak guard that stops a run if an Arm F marker appears in packet text;
  * the per-prompt call and wall-clock cap, implemented as a Ledger subclass so that the cap is enforced at the
    same place as the budget caps (before dispatch).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PFP = HERE.parent
REPO = HERE.parents[2]
sys.path.insert(0, str(PFP))  # dag/pfp, so that the package `model_ladder` imports under `python -I`
sys.dont_write_bytecode = True

PROTOCOL = HERE / 'protocol.md'
COHORT = HERE / 'cohort.json'
COHORT_SCHEMA_ID = 'omega.pfp.compare.cohort.v1'
STRATA = ('D', 'P', 'C')

# Models that define the expensive baseline. They are never callable from Arm S (enforced twice: tier filter and name check).
EXPENSIVE_MARKERS = ('tier1', 'solo')
ARM_S_MAX_TIER = 3          # tiers 0..3 = free, cheap Router_r, Tier3 5.5, Tier2 5.5; 4 = Tier1, 5 = Solo are never in Arm S
ARM_S_DEFAULT_MAX_TIER = 2  # the pre-registered Arm S: free, cheap, Tier3
DEFAULT_MAX_CALLS = 7       # provider calls per prompt, both arms (the default ladder is 3 + 2 + 2)
DEFAULT_WALLCLOCK_S = 1800
STANDARD_AXIOMS = ('propext', 'Classical.choice', 'Quot.sound')
LEAN_VERSION = '4.35.0'
SHORT_ROOT = Path.home() / '.fvs'  # short, because Windows MAX_PATH bites inside code/ and dag/


class CompareError(Exception):
    """A pre-registration or safety rule refused the request. Nothing was sent."""


# --------------------------------------------------------------------------- bytes and hashes
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lf_bytes(data: bytes) -> bytes:
    """The Write tool on Windows can emit CRLF; the frozen protocol is hashed as LF so that the pin is stable."""
    return data.replace(b'\r\n', b'\n')


def protocol_sha256(path: Path = PROTOCOL) -> str:
    return sha256_bytes(lf_bytes(Path(path).read_bytes()))


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + '\n').encode('utf-8')


def packet_bytes_sha256(system: str, user: str, schema: dict) -> str:
    """The identity of 'identical prompt bytes': system text, user text and the response schema that travels with them."""
    blob = system + '\n--user--\n' + user + '\n--schema--\n' + canonical_json(schema).decode('utf-8')
    return sha256_bytes(blob.encode('utf-8'))


def write_new(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


# --------------------------------------------------------------------------- git (read only)
def git(*args, check=True, cwd=REPO, binary=False):
    proc = subprocess.run(['git', *args], cwd=str(cwd), capture_output=True, check=False)
    if check and proc.returncode != 0:
        raise CompareError('git %s failed: %s' % (' '.join(args[:3]), proc.stderr.decode('utf-8', 'replace')[:200]))
    return proc.stdout if binary else proc.stdout.decode('utf-8', 'replace')


def git_show(commit: str, path: str) -> bytes | None:
    proc = subprocess.run(['git', 'show', '%s:%s' % (commit, path)], cwd=str(REPO), capture_output=True)
    return proc.stdout if proc.returncode == 0 else None


# --------------------------------------------------------------------------- cohort
def load_cohort(path: Path = COHORT, *, check_protocol: bool = True) -> dict:
    path = Path(path)
    if not path.is_file():
        raise CompareError('cohort.json is missing; run build_cohort.py first')
    cohort = json.loads(path.read_bytes().decode('utf-8'))
    if cohort.get('schema_id') != COHORT_SCHEMA_ID:
        raise CompareError('cohort.json has an unknown schema_id')
    if check_protocol:
        live = protocol_sha256()
        if live != cohort['protocol']['sha256']:
            raise CompareError('protocol.md (sha256 %s) no longer matches the pin in cohort.json (%s): the pre-registration '
                               'is frozen. Amend it only by a new, dated, separately pinned cohort.' % (live[:12], cohort['protocol']['sha256'][:12]))
    return cohort


def selected_items(cohort: dict, strata=STRATA, only=None, arm_f_only=False) -> list:
    wanted = set(only or [])
    out = []
    for item in cohort['items']:
        if item['stratum'] not in strata:
            continue
        if wanted and item['node_id'] not in wanted:
            continue
        if arm_f_only and not item.get('arm_f'):
            continue
        out.append(item)
    return out


def item_sha256(item: dict) -> str:
    return sha256_bytes(canonical_json(item))


# --------------------------------------------------------------------------- clean room
SOURCE_SUFFIXES = {
    'lean4': {'.lean'}, 'code': {'.py', '.rs', '.toml'}, 'scripts': {'.py'},
    'dag': {'.py', '.json', '.yaml', '.yml', '.md', '.tsv', '.txt', '.lean', '.rs'},
}
KEEP_NAMES = {'lean-toolchain', 'lake-manifest.json'}


def _wanted(path: str) -> bool:
    top = path.split('/', 1)[0]
    suffixes = SOURCE_SUFFIXES.get(top)
    if suffixes is None:
        return False
    name = path.rsplit('/', 1)[-1]
    if top == 'dag' and (path.startswith('dag/results/') or path == 'dag/results'):
        return False
    return os.path.splitext(name)[1] in suffixes or name in KEEP_NAMES


def _excluded(path: str, exclude: tuple) -> bool:
    return any(path == e or path.startswith(e.rstrip('/') + '/') for e in exclude)


def cleanroom_pathspecs(commit: str) -> list:
    names = git('ls-tree', '--name-only', commit, 'dag/').split()
    tops = set(git('ls-tree', '--name-only', commit).split())
    return [t for t in ('lean4', 'code', 'scripts') if t in tops] + [n for n in names if n != 'dag/results']


def build_cleanroom(commit: str, dest: Path, *, exclude=(), max_path_chars=240) -> dict:
    """Extract the source files of `commit` into `dest` (must not exist). Returns the manifest.

    Nothing under dag/results is ever extracted. `exclude` lists Arm F artifact paths that existed at the freeze commit
    and are dropped as well. Files whose extracted path would exceed `max_path_chars` are skipped and counted (Windows
    MAX_PATH); the count is part of the manifest so that the skipped set is auditable.
    """
    dest = Path(dest)
    if dest.exists():
        raise CompareError('clean-room destination exists: %s' % dest)
    dest.mkdir(parents=True)
    exclude = tuple(e.replace('\\', '/') for e in exclude)
    proc = subprocess.Popen(['git', 'archive', '--format=tar', commit, '--', *cleanroom_pathspecs(commit)],
                            cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    files, dropped, skipped_long = {}, [], []
    try:
        with tarfile.open(fileobj=proc.stdout, mode='r|') as archive:
            for member in archive:
                if not member.isfile():
                    continue
                path = member.name
                if not _wanted(path):
                    continue
                if _excluded(path, exclude):
                    dropped.append(path)
                    continue
                target = dest / path
                if len(str(target)) > max_path_chars:
                    skipped_long.append(path)
                    continue
                data = archive.extractfile(member).read()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                files[path] = sha256_bytes(data)
    finally:
        proc.stdout.close()
        stderr = proc.stderr.read().decode('utf-8', 'replace') if proc.stderr else ''
        if proc.wait() != 0:
            shutil.rmtree(dest, ignore_errors=True)
            raise CompareError('git archive failed for %s: %s' % (commit[:12], stderr[:200]))
    listing = sorted(files.items())
    return {'commit': commit, 'files': len(files), 'bytes': sum(p.stat().st_size for p in (dest / k for k, _ in listing)),
            'manifest_sha256': sha256_bytes(canonical_json(listing)), 'dropped_arm_f_paths': sorted(dropped),
            'skipped_long_paths': len(skipped_long), 'dag_results_present': (dest / 'dag' / 'results').exists()}


def scan_markers(text: str, markers) -> list:
    return sorted({m for m in markers if m and m in text})


def scan_cleanroom_for_markers(root: Path, markers, limit=40) -> list:
    """Warn-level scan: files of the clean room that mention an Arm F marker (the model never sees whole files, only @SRC lines)."""
    if not markers:
        return []
    hits = []
    for folder, dirs, names in os.walk(root):
        for name in names:
            if not name.endswith(('.lean', '.py', '.rs', '.md', '.yaml', '.json')):
                continue
            path = Path(folder) / name
            try:
                text = path.read_bytes().decode('utf-8', 'replace')
            except OSError:
                continue
            found = scan_markers(text, markers)
            if found:
                hits.append({'path': path.relative_to(root).as_posix(), 'markers': found})
                if len(hits) >= limit:
                    return hits
    return hits


def cleanroom_dir(item: dict, tag: str, base: Path | None = None) -> Path:
    base = Path(base) if base else SHORT_ROOT
    return base / ('%s-%s' % (tag, sha256_bytes(item['node_id'].encode('utf-8'))[:6]))


# --------------------------------------------------------------------------- packets
def load_stored_packet(item: dict, cleanroom: Path):
    """Replay mode (stratum P): the exact request of an earlier expensive attempt, byte for byte."""
    from model_ladder.packets import CompiledPacket, load_row
    import yaml
    replay = item['arm_s']['replay']
    path = REPO / replay['request_path']
    stored = json.loads(path.read_bytes().decode('utf-8'))
    packet = CompiledPacket(node_id=item['node_id'], stage='P0', attempt_id=stored['attempt_id'], system=stored['system_prompt'],
                            user=stored['user_prompt'], schema=stored['response_schema'], input_sha256=stored['input_sha256'],
                            meta=stored.get('meta', {}))
    _, row = load_row(cleanroom, item['node_id'])
    loader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
    packet.target_statement = yaml.load((Path(cleanroom) / row['operad_collection']).read_bytes(), Loader=loader)['target']['source_statement']
    digest = packet_bytes_sha256(packet.system, packet.user, packet.schema)
    if digest != replay['packet_bytes_sha256']:
        raise CompareError('stored packet of %s no longer matches the sha256 frozen in cohort.json' % item['node_id'])
    return packet


def make_packet_factory(item: dict, cleanroom: Path, policy: dict, index, hall):
    """(first_packet, compile_function). The function has the signature of model_ladder.packets.compile_p0 and is patched into
    the runner; in replay mode it returns the stored packet for every attempt, so that every attempt of every arm sees
    identical bytes."""
    from model_ladder import packets
    if item['arm_s']['packet_source'] == 'replay_stored_request':
        stored = load_stored_packet(item, cleanroom)
        return stored, (lambda root, node_id, **kwargs: stored)
    # The attempt id is part of the packet header and of its digest. A constant id makes the first packet of Arm S and of the
    # fresh Solo arm byte-identical; later packets differ only through the negative entries the arm's own failures produced.
    first = packets.compile_p0(cleanroom, item['node_id'], attempt_id='cmp', policy=policy, index=index, feedback=True, hallucinations=hall)

    def compile_fixed(root, node_id, **kwargs):
        kwargs['attempt_id'] = 'cmp'
        return packets.compile_p0(root, node_id, **kwargs)

    return first, compile_fixed


def assert_no_leak(packet, markers) -> None:
    found = scan_markers(packet.system + '\n' + packet.user, markers)
    if found:
        raise CompareError('Arm F markers %s appear in the packet text of %s; refusing to send it' % (found, packet.node_id))


# --------------------------------------------------------------------------- per-prompt caps
def capped_ledger_class():
    from model_ladder.budget import BudgetRefused, Ledger

    class CappedLedger(Ledger):
        """Ledger plus the per-prompt call cap and wall-clock cap of the protocol. Raised before dispatch, like the money caps."""

        def __init__(self, path, *, caps, max_calls, wallclock_s, clock=time.monotonic):
            super().__init__(path, caps=caps)
            self.max_calls, self.deadline, self._clock, self.calls = max_calls, clock() + wallclock_s, clock, 0

        def reserve(self, call_id, **kwargs):
            if self.calls >= self.max_calls:
                raise BudgetRefused('NODE_CALL_CAP', 'protocol cap of %d provider calls per prompt reached' % self.max_calls)
            if self._clock() > self.deadline:
                raise BudgetRefused('NODE_WALLCLOCK_CAP', 'protocol wall-clock cap for this prompt reached')
            super().reserve(call_id, **kwargs)
            self.calls += 1

    return CappedLedger


# --------------------------------------------------------------------------- run folders
def compare_run_dirs(node_id: str, suffix: str, root: Path = REPO) -> list:
    base = Path(root) / 'dag' / 'results' / node_id / 'runs'
    return sorted(base.glob('*_' + suffix + '*')) if base.is_dir() else []


def free_space_gb(path: Path) -> float:
    probe = Path(path)
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    return shutil.disk_usage(str(probe)).free / 1e9


# --------------------------------------------------------------------------- one prompt through the ladder (both arms)
def seeded_memory(clean_root: Path, seed: Path | None, cohort_nodes: set) -> dict:
    """Cold start by default. The freeze commit may carry a real _hallucination_index.json: it is removed.
    With a seed file, entries that mention any cohort node are dropped before the rest is copied in."""
    target = Path(clean_root) / 'dag' / 'operads' / '_hallucination_index.json'
    removed = target.is_file()
    if removed:
        target.unlink()
    kept = 0
    if seed:
        data = json.loads(Path(seed).read_bytes().decode('utf-8'))
        entries = {k: v for k, v in data['entries'].items() if not (cohort_nodes & set(v.get('nodes', [])))}
        kept = len(entries)
        data['entries'] = entries
        data['by_declaration'] = {k: [i for i in ids if i in entries] for k, ids in data['by_declaration'].items() if any(i in entries for i in ids)}
        data['by_claim_pattern'] = {k: [i for i in ids if i in entries] for k, ids in data['by_claim_pattern'].items() if any(i in entries for i in ids)}
        target.write_bytes(json_bytes(data))
    return {'freeze_index_removed': removed, 'seed_file': str(seed) if seed else None, 'seed_entries_kept': kept}


def run_ladder_item(args, item, *, arm, suffix, cohort, providers, redactor, tiers, start_tier, max_tier, allow_solo,
                    arm_spent_micro, workdir, effort_override=None) -> dict:
    """Clean room -> packet -> leak guard -> LadderRunner -> published run folder + receipt. One prompt, one arm.

    `args` must carry: ledger, provider_a_weekly_cap_usd, paid_other_weekly_cap_usd, max_calls, wallclock_s, node_cap_usd,
    arm_cap_usd, abstain_stop, seed_memory, keep_cleanroom, allow_rerun. Arm S uses tiers 0..3 with allow_solo False;
    fresh Arm F uses the single Solo tier, with the same packet bytes, caps and verifier."""
    from model_ladder import runner as runner_module
    from model_ladder.budget import usd_to_micro
    from model_ladder.config import DEFAULT_POLICY
    from model_ladder.memory import HallucinationIndex, index_path
    from model_ladder.runner import LadderRunner
    from model_ladder.verify import DeclIndex, LeanRunner, Verifier

    node = item['node_id']
    name = suffix.split('_', 1)[1]
    started = time.monotonic()
    root = cleanroom_dir(item, name, workdir)
    manifest = build_cleanroom(item['arm_s']['freeze_commit'], root, exclude=tuple(item['arm_s']['exclude_paths']))
    cache = root.parent / ('idx-' + root.name + '.json')
    try:
        memory = seeded_memory(root, Path(args.seed_memory) if args.seed_memory else None, {i['node_id'] for i in cohort['items']})
        warn_hits = scan_cleanroom_for_markers(root, item['arm_s']['leak_markers'])
        policy = dict(DEFAULT_POLICY)
        policy['abstain_stop'] = args.abstain_stop
        index = DeclIndex(root, cache_path=cache)
        hall = HallucinationIndex(index_path(root))
        packet, compile_fn = make_packet_factory(item, root, policy, index, hall)
        assert_no_leak(packet, item['arm_s']['leak_markers'])
        digest = packet_bytes_sha256(packet.system, packet.user, packet.schema)
        ledger = capped_ledger_class()(args.ledger, caps={'provider_a_weekly_usd': args.provider_a_weekly_cap_usd,
                                                           'paid_other_weekly_usd': args.paid_other_weekly_cap_usd},
                                        max_calls=args.max_calls, wallclock_s=args.wallclock_s)
        # Lean skeletons are elaborated by score.py in the real project, for both arms alike (the clean room has no Mathlib build).
        verifier = Verifier(root, index=index, lean=LeanRunner(root), run_lean=False)
        runner = LadderRunner(root, ledger=ledger, providers=providers, tiers=tiers, policy=policy, redactor=redactor, decl_index=index, verifier=verifier)
        runner_module.compile_p0 = compile_fn  # replay mode returns the stored packet for every attempt; otherwise the ladder's own compiler
        paid = any(t['family'] != 'free' for t in tiers if start_tier <= t['id'] <= max_tier)
        cap = min(usd_to_micro(args.node_cap_usd), max(0, usd_to_micro(args.arm_cap_usd) - arm_spent_micro)) if paid else 0
        summary = redactor.redact_obj(runner.run(node, stage='P0', run_cap_microusd=cap, start_tier=start_tier, max_tier=max_tier, feedback=True,
                                                 allow_solo=allow_solo, effort_override=effort_override))
        elapsed = time.monotonic() - started
        run_dir = summary.get('run_dir')
        destination = None
        if run_dir:
            source = root / run_dir
            stamp, _, rest = source.name.partition('_ladder')
            destination = REPO / 'dag' / 'results' / node / 'runs' / (stamp + '_' + suffix + rest)
            shutil.copytree(source, destination)
        receipt = {'schema_id': 'omega.pfp.compare.%s-receipt.v1' % name, 'authority_effect': 'None', 'arm': arm, 'node_id': node, 'stratum': item['stratum'],
                   'protocol_sha256': cohort['protocol']['sha256'], 'cohort_base_commit': cohort['built_from']['base_commit'], 'cohort_item_sha256': item_sha256(item),
                   'harness_commit': git('rev-parse', 'HEAD').strip(), 'freeze_commit': item['arm_s']['freeze_commit'],
                   'packet': {'source': item['arm_s']['packet_source'], 'packet_bytes_sha256': digest, 'input_sha256': packet.input_sha256,
                              'estimated_tokens': packet.estimated_tokens(), 'src_offered': packet.meta.get('src_offered'),
                              'known_neg_injected_first': packet.meta.get('known_neg_injected'), 'known_pos_injected_first': packet.meta.get('known_pos_injected')},
                   'cleanroom': {**manifest, 'memory': memory},
                   'leak_check': {'packet_text_markers_found': [], 'cleanroom_files_mentioning_markers': warn_hits,
                                  'level': 'packet text is a hard stop; clean-room file mentions are recorded as warnings'},
                   'tiers_allowed': [t['id'] for t in tiers if start_tier <= t['id'] <= max_tier],
                   'models_allowed': [c['model'] for t in tiers if start_tier <= t['id'] <= max_tier for c in t['candidates'] if c.get('enabled', True)],
                   'effort_override': effort_override, 'allow_solo': allow_solo,
                   'caps': {'max_calls': args.max_calls, 'wallclock_s': args.wallclock_s, 'node_cap_usd': args.node_cap_usd, 'arm_cap_usd': args.arm_cap_usd,
                            'abstain_stop': args.abstain_stop,
                            'ledger_weekly_caps': {'provider_a_usd': args.provider_a_weekly_cap_usd, 'paid_other_usd': args.paid_other_weekly_cap_usd}},
                   'rerun_reason': getattr(args, 'allow_rerun', None),
                   'ladder': {k: summary.get(k) for k in ('status', 'stop_reason', 'accepted_attempt', 'best_attempt', 'spend_usd', 'spend_microusd',
                                                          'totals_by_tier', 'hallucinations_by_class', 'verified')},
                   'provider_calls_reserved_this_prompt': ledger.calls, 'wallclock_s_measured': round(elapsed, 1),
                   'source_run_dir_in_cleanroom': run_dir, 'published_run_dir': destination.relative_to(REPO).as_posix() if destination else None}
        if destination:
            write_new(destination / ('compare_%s_receipt.json' % name), json_bytes(redactor.redact_obj(receipt)))
    finally:
        if not args.keep_cleanroom:
            shutil.rmtree(root, ignore_errors=True)
            if cache.exists():
                cache.unlink()
    return {'node_id': node, 'stratum': item['stratum'], 'status': summary['status'], 'stop_reason': summary['stop_reason'], 'spend_usd': summary['spend_usd'],
            'spend_microusd': summary['spend_microusd'], 'calls': ledger.calls, 'seconds': round(elapsed, 1), 'run_dir': receipt['published_run_dir']}
