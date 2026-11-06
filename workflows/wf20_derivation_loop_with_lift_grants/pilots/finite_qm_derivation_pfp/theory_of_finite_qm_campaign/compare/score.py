"""Score the Fable-versus-swarm comparison by verifier verdicts only, blinded, with cost per accepted result.

    python -I -X utf8 dag/pfp/compare/score.py                         # read the receipts on disk; whatever needs Lean/cargo/pytest is marked "unverified"
    python -I -X utf8 dag/pfp/compare/score.py --run-verifiers          # also run Lean 4.35.0, pytest and cargo as subprocesses (slow, needs disk; see README.md)
    python -I -X utf8 dag/pfp/compare/score.py --reverify-o             # re-check every operad entry of the scored attempts against a rebuilt clean room (local, no Lean)
    python -I -X utf8 dag/pfp/compare/score.py --unblind                # add the arm-resolved table, costs and the pre-registered decision

What counts (protocol.md section 5). An accepted result is one of
  L  a Lean source accepted by Lean 4.35.0: exit 0, no error, no sorry, and #print axioms limited to propext, Classical.choice, Quot.sound;
  W  a Rust or Python witness whose test or script passes;
  O  a host-verified operad entry (declaration exists where cited, exact arithmetic) of an attempt that the ladder policy accepted.
No prose, no model self-assessment and no human review enters a verdict. A unit that could not be checked is "unverified", never accepted.
Cost per accepted result divides ALL spend of the arm (failed attempts, abstentions, prompts with nothing accepted) by accepted units.

Without --run-verifiers nothing is executed: Arm F units carry the verdict their receipts record (labelled with the evidence level), swarm
Lean skeletons stay unverified, and the decision rule reports INDICATIVE, never SUPPORTS.

AuthorityEffect: None.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))  # dag/pfp, so that the package `llm_ladder` imports under `python -I`
sys.dont_write_bytecode = True

import yaml  # noqa: E402

from compare_common import (LEAN_VERSION, REPO, SHORT_ROOT, STANDARD_AXIOMS, CompareError, build_cleanroom, cleanroom_dir, compare_run_dirs,  # noqa: E402
                            free_space_gb, git, item_sha256, json_bytes, load_cohort, protocol_sha256, selected_items, seeded_memory, sha256_bytes)

LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
CLASSES = ('O', 'L', 'W')
S_CAN_REACH = {'O': True, 'L': True, 'W': False}   # Arm S is P0 only: Lean only through lemma skeletons; no Rust/Python witnesses
MARGIN_PROMPTS = 1          # non-inferiority margin: the swarm may lose at most this many prompts net
REFUTE_NET_PROMPTS = 3      # net loss that refutes outright
SIGN_TEST_ALPHA = 0.05
COST_RATIO_MAX = 0.10       # swarm cost per accepted prompt must be at most this fraction of Fable's
MIN_ELIGIBLE = 6            # fewer eligible prompts than this: INCONCLUSIVE whatever the counts
TIE_COST_REL = 0.01


# --------------------------------------------------------------------------- small utilities
def load_json(path: Path):
    try:
        return json.loads(Path(path).read_bytes().decode('utf-8'))
    except (OSError, ValueError):
        return None


def file_sha256(path: Path) -> str | None:
    try:
        return sha256_bytes(Path(path).read_bytes())
    except OSError:
        return None


def tail(text: str, lines: int = 12) -> str:
    return '\n'.join(text.strip().splitlines()[-lines:])


def sign_test_p(b: int, c: int) -> float:
    """One-sided exact binomial P(X >= b) for X ~ Bin(b + c, 1/2): the chance of a net loss at least this large if the arms were equal."""
    n = b + c
    return sum(math.comb(n, k) for k in range(b, n + 1)) / 2 ** n if n else 1.0


def wilson(successes: int, n: int, z: float = 1.96):
    if n == 0:
        return None
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]


def blind_label(protocol_sha: str, node: str, arm_group: str) -> str:
    """Deterministic, per-prompt coin: which of 'X'/'Y' is the swarm. arm_group is 'S' or 'F'."""
    flip = int(sha256_bytes((protocol_sha + '|blind|' + node).encode('utf-8'))[:2], 16) & 1
    return ('X' if (arm_group == 'S') != bool(flip) else 'Y')


# --------------------------------------------------------------------------- verifiers (subprocess; only with --run-verifiers)
class Verifiers:
    def __init__(self, args):
        self.args = args
        self.enabled = args.run_verifiers
        self.lean_project = Path(args.lean_project)
        self.lake = args.lake or shutil.which('lake') or str(Path.home() / '.elan' / 'bin' / 'lake')
        self._lean_ok = None
        self.log = []

    def _run(self, argv, cwd, timeout, env=None):
        started = time.monotonic()
        try:
            proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, env=env)
            out = {'argv': [str(a) for a in argv], 'exit_code': proc.returncode, 'stdout': proc.stdout or '', 'stderr': proc.stderr or ''}
        except subprocess.TimeoutExpired:
            out = {'argv': [str(a) for a in argv], 'exit_code': None, 'timeout_s': timeout, 'stdout': '', 'stderr': ''}
        except OSError as error:
            out = {'argv': [str(a) for a in argv], 'exit_code': None, 'error': type(error).__name__, 'stdout': '', 'stderr': ''}
        out['seconds'] = round(time.monotonic() - started, 1)
        self.log.append({k: (v if k not in ('stdout', 'stderr') else tail(v)) for k, v in out.items()})
        return out

    # ---- Lean
    def lean_ready(self):
        if self._lean_ok is not None:
            return self._lean_ok
        if not self.enabled or self.args.skip_lean:
            self._lean_ok = (False, 'Lean verifiers not requested (--run-verifiers) or skipped')
            return self._lean_ok
        if not self.lean_project.is_dir():
            self._lean_ok = (False, 'lean project %s not found; pass --lean-project (a checkout whose lean4/ has the Mathlib v4.35.0 build)' % self.lean_project)
            return self._lean_ok
        out = self._run([self.lake, 'env', 'lean', '--version'], self.lean_project, 120)
        text = out['stdout'] + out['stderr']
        self._lean_ok = (LEAN_VERSION in text, ('lean --version in %s: %s' % (self.lean_project, text.strip()[:80])) if text.strip() else 'lake/lean did not answer')
        if not self._lean_ok[0]:
            self._lean_ok = (False, 'Lean %s required, found: %s' % (LEAN_VERSION, self._lean_ok[1]))
        return self._lean_ok

    @staticmethod
    def declarations(source: str) -> list:
        from llm_ladder.verify import DeclIndex
        private = {m.group(1) for m in re.finditer(r'^(?:@\[[^\]]*\]\s*)*(?:(?:protected|noncomputable|partial|unsafe)\s+)*private\s+'
                                                    r'(?:(?:protected|noncomputable|partial|unsafe)\s+)*(?:theorem|lemma|def|abbrev)\s+([^\s:({\[]+)', source, re.M)}
        names = []
        for decl in DeclIndex(REPO)._scan_lean(source):
            if decl['kind'] in ('theorem', 'lemma', 'def', 'abbrev') and decl['name'] not in private and not decl['name'].startswith('_'):
                names.append(decl['full'])
        seen, out = set(), []
        for n in names:
            if n not in seen:
                seen.add(n)
                out.append(n)
        return out

    def parse_axioms(self, text: str, expected: list):
        printed = {}
        for match in re.finditer(r"'([^']+)' depends on axioms: \[([^\]]*)\]", text):
            printed[match.group(1)] = [a.strip() for a in match.group(2).split(',') if a.strip()]
        for match in re.finditer(r"'([^']+)' does not depend on any axioms", text):
            printed[match.group(1)] = []
        bad = {n: a for n, a in printed.items() if not set(a) <= set(STANDARD_AXIOMS)}
        missing = [n for n in expected if n not in printed]
        return printed, bad, missing

    def lean_module(self, module: str, relpath: str):
        """lake build <Module> in the project, then #print axioms for every declaration through an import probe."""
        ok, why = self.lean_ready()
        if not ok:
            return {'status': 'unverified', 'reason': why}
        source_path = self.lean_project.parent / relpath if (self.lean_project.parent / relpath).is_file() else self.lean_project / Path(relpath).name
        if not source_path.is_file():
            return {'status': 'unverified', 'reason': 'source %s not present in the lean project' % relpath}
        source = source_path.read_bytes().decode('utf-8', 'replace').replace('\r\n', '\n')
        build = self._run([self.lake, 'build', '+' + module], self.lean_project, self.args.lean_timeout_s)
        out = build['stdout'] + build['stderr']
        if build['exit_code'] is None:
            return {'status': 'unverified', 'reason': 'lake build did not finish (%s)' % (build.get('timeout_s') or build.get('error')), 'seconds': build['seconds']}
        if re.search(r'unknown (?:package|target|module)|no such (?:target|module)|invalid target', out, re.I) and build['exit_code'] != 0:
            return {'status': 'unverified', 'reason': 'module %s is not a target of this lake workspace (not registered or not present in this checkout)' % module, 'tail': tail(out)}
        if build['exit_code'] != 0 or re.search(r'\berror\b', out) or re.search(r"declaration uses 'sorry'|\bsorry\b", out):
            return {'status': 'rejected', 'reason': 'lake build failed or reported sorry/error', 'tail': tail(out), 'seconds': build['seconds']}
        names = self.declarations(source)
        probe_dir = Path(tempfile.mkdtemp(prefix='fvs-probe-'))
        try:
            probe = probe_dir / 'Probe.lean'
            probe.write_bytes(('import %s\n' % module + '\n'.join('#print axioms %s' % n for n in names) + '\n').encode('utf-8'))
            run = self._run([self.lake, 'env', 'lean', str(probe)], self.lean_project, self.args.lean_timeout_s)
        finally:
            shutil.rmtree(probe_dir, ignore_errors=True)
        text = run['stdout'] + run['stderr']
        printed, bad, missing = self.parse_axioms(text, names)
        if run['exit_code'] != 0 or bad or 'sorryAx' in text:
            return {'status': 'rejected', 'reason': 'axiom probe failed or non-standard axioms', 'nonstandard': bad, 'tail': tail(text), 'seconds': build['seconds'] + run['seconds']}
        if missing:
            return {'status': 'unverified', 'reason': '%d of %d declarations printed no axioms line (e.g. %s)' % (len(missing), len(names), missing[0]),
                    'printed': len(printed), 'seconds': build['seconds'] + run['seconds']}
        return {'status': 'accepted', 'declarations': len(names), 'axiom_lines': len(printed), 'lean_version': LEAN_VERSION,
                'seconds': round(build['seconds'] + run['seconds'], 1)}

    def lean_snippet(self, text: str):
        ok, why = self.lean_ready()
        if not ok:
            return {'status': 'unverified', 'reason': why}
        names = re.findall(r"^(?:theorem|lemma)\s+([A-Za-z_][\w.']*)", text, re.M)
        if not names:
            return {'status': 'rejected', 'reason': 'no theorem or lemma in the skeleton'}
        if re.search(r'\b(sorry|admit)\b|^\s*axiom\b', text, re.M):
            return {'status': 'rejected', 'reason': 'sorry, admit or axiom in the skeleton'}
        scratch = Path(tempfile.mkdtemp(prefix='fvs-snip-'))
        try:
            path = scratch / 'Snippet.lean'
            path.write_bytes((text.replace('\r\n', '\n') + '\n' + '\n'.join('#print axioms %s' % n for n in names) + '\n').encode('utf-8'))
            run = self._run([self.lake, 'env', 'lean', str(path)], self.lean_project, self.args.lean_timeout_s)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        out = run['stdout'] + run['stderr']
        if run['exit_code'] is None:
            return {'status': 'unverified', 'reason': 'lean did not finish'}
        printed, bad, missing = self.parse_axioms(out, names)
        if run['exit_code'] != 0 or re.search(r'\berror\b', out) or bad or missing or 'sorryAx' in out:
            return {'status': 'rejected', 'reason': 'does not compile with standard axioms', 'tail': tail(out)}
        return {'status': 'accepted', 'declarations': len(names), 'lean_version': LEAN_VERSION, 'seconds': run['seconds']}

    # ---- pytest, cargo, scripts
    def pytest(self, tests_file: str):
        if not self.enabled or self.args.skip_python:
            return {'status': 'unverified', 'reason': 'Python verifiers not requested (--run-verifiers) or skipped'}
        path = REPO / tests_file
        if not path.is_file():
            return {'status': 'unverified', 'reason': '%s not found' % tests_file}
        rel = path.relative_to(REPO / 'code' / 'python').as_posix() if str(path).startswith(str(REPO / 'code' / 'python')) else str(path)
        run = self._run([sys.executable, '-m', 'pytest', rel, '-q'], REPO / 'code' / 'python', self.args.test_timeout_s)
        out = run['stdout'] + run['stderr']
        match = re.search(r'(\d+) passed', out)
        if run['exit_code'] == 0 and match and int(match.group(1)) > 0:
            return {'status': 'accepted', 'passed': int(match.group(1)), 'seconds': run['seconds']}
        if run['exit_code'] is None:
            return {'status': 'unverified', 'reason': 'pytest did not finish'}
        return {'status': 'rejected', 'reason': 'pytest exit %s' % run['exit_code'], 'tail': tail(out)}

    def script(self, relpath: str, marker: str):
        if not self.enabled or self.args.skip_python:
            return {'status': 'unverified', 'reason': 'Python verifiers not requested (--run-verifiers) or skipped'}
        path = REPO / relpath
        if not path.is_file():
            return {'status': 'unverified', 'reason': '%s not found' % relpath}
        run = self._run([sys.executable, str(path)], path.parent, self.args.test_timeout_s)
        out = run['stdout'] + run['stderr']
        if run['exit_code'] == 0 and marker in out:
            return {'status': 'accepted', 'marker': marker, 'seconds': run['seconds']}
        return {'status': 'unverified' if run['exit_code'] is None else 'rejected', 'reason': 'exit %s, marker present: %s' % (run['exit_code'], marker in out), 'tail': tail(out)}

    def cargo(self, cargo_filter: str):
        if not self.enabled or self.args.skip_cargo:
            return {'status': 'unverified', 'reason': 'cargo verifiers not requested (--run-verifiers) or skipped'}
        target = Path(self.args.cargo_target)
        if len(str(target)) > 40:
            return {'status': 'unverified', 'reason': 'cargo target path %s is longer than 40 characters (Windows MAX_PATH); pass a short --cargo-target' % target}
        if free_space_gb(target) < self.args.min_free_gb_cargo:
            return {'status': 'unverified', 'reason': 'only %.1f GB free for the cargo target (need %.0f); free disk or pass --cargo-target' % (free_space_gb(target), self.args.min_free_gb_cargo)}
        env = dict(os.environ, CARGO_TARGET_DIR=str(target), CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0', CARGO_INCREMENTAL='0')
        run = self._run(['cargo', 'test', '--lib', cargo_filter], REPO / 'code' / 'rust', self.args.test_timeout_s, env=env)
        out = run['stdout'] + run['stderr']
        if not self.args.keep_cargo_target and target.exists():
            shutil.rmtree(target, ignore_errors=True)
        match = re.search(r'test result: ok\. (\d+) passed; 0 failed', out)
        if run['exit_code'] == 0 and match and int(match.group(1)) > 0:
            return {'status': 'accepted', 'passed': int(match.group(1)), 'seconds': run['seconds']}
        if run['exit_code'] is None:
            return {'status': 'unverified', 'reason': 'cargo did not finish'}
        return {'status': 'rejected', 'reason': 'cargo exit %s' % run['exit_code'], 'tail': tail(out)}


# --------------------------------------------------------------------------- Arm F (reuse) units
def f_reuse_units(item: dict, verifiers: Verifiers) -> list:
    out = []
    for unit in (item.get('arm_f') or {}).get('units', []):
        cls, recorded = unit['class'], unit['on_disk_verdict']
        row = {'unit_id': unit['unit_id'], 'class': cls, 'kind': unit.get('kind'), 'recorded_verdict': recorded, 'evidence': unit.get('evidence_kind'),
               'toolchain_in_receipt': unit.get('receipt_toolchain'), 'verifier_run': None}
        verdict, level = 'unverified', 'receipt'
        if cls == 'L' and unit.get('module'):
            if verifiers.enabled:
                run = verifiers.lean_module(Path(unit['module']).stem, unit.get('lean4_copy') or unit['module'])
                row['verifier_run'] = run
                if run['status'] in ('accepted', 'rejected'):
                    verdict, level = run['status'], 're-run now (Lean %s)' % LEAN_VERSION
            if row['verifier_run'] is None or row['verifier_run']['status'] == 'unverified':
                if recorded == 'accepted' and unit.get('receipt_toolchain') == LEAN_VERSION:
                    verdict, level = 'accepted', 'sealed receipt (Lean %s)' % LEAN_VERSION
                elif recorded == 'rejected':
                    verdict, level = 'rejected', 'sealed receipt'
                else:
                    verdict = 'unverified'
                    level = 'receipt records %s under toolchain %s; not Lean %s' % (recorded, unit.get('receipt_toolchain') or 'unrecorded', LEAN_VERSION)
        elif cls == 'W':
            run = None
            if verifiers.enabled:
                if unit.get('kind') == 'python_tests' and unit.get('tests_file'):
                    run = verifiers.pytest(unit['tests_file'])
                elif unit.get('kind') == 'rust_tests' and unit.get('cargo_filter'):
                    run = verifiers.cargo(unit['cargo_filter'])
                elif unit.get('kind') == 'python_script_receipt':
                    run = verifiers.script(unit['script'], unit['success_marker'])
            row['verifier_run'] = run
            if run and run['status'] in ('accepted', 'rejected'):
                verdict, level = run['status'], 're-run now'
            else:
                verdict = 'unverified'
                level = 'recorded: %s (%s)' % (recorded, unit.get('evidence'))
        elif cls == 'O':
            verdict = {'accepted': 'accepted', 'rejected': 'rejected'}.get(recorded, 'unverified')
            level = 'host check recorded in ladder_receipt.json' if unit.get('kind') == 'ladder_p0_attempt' else 'no host verdict on disk'
            if unit.get('kind') == 'ladder_p0_attempt':
                row['entries'] = {'verified': unit['verified_entries'], 'refused': unit['refused_claims']}
        row['verdict'], row['evidence_level'] = verdict, level
        # as-recorded view, generous to Fable: any 'accepted' on disk counts, whatever the toolchain or evidence kind
        row['as_recorded_accepted'] = recorded == 'accepted'
        out.append(row)
    return out


def expand_o_units(units: list) -> list:
    """A recorded ladder attempt stands for its verified entries; Arm S and fresh Arm F are counted entry by entry, so Arm F is too."""
    out = []
    for unit in units:
        if unit['class'] == 'O' and unit.get('entries') and unit['verdict'] == 'accepted':
            for i in range(unit['entries']['verified']):
                copy = dict(unit, unit_id='%s#%d' % (unit['unit_id'], i + 1))
                if i:
                    copy.pop('entries')  # claim counts are carried once, by the first copy
                out.append(copy)
        else:
            out.append(unit)
    return out


# --------------------------------------------------------------------------- ladder-run arms (S and fresh F)
def find_run(node: str, suffix: str, log: list):
    runs = compare_run_dirs(node, suffix)
    if not runs:
        return None
    if len(runs) > 1:
        log.append('%s: %d %s runs; the earliest is scored (protocol: first run counts), the others are listed' % (node, len(runs), suffix))
    return runs[0]


def attempt_delta(run: Path, aid: str) -> dict:
    path = run / 'p0' / 'attempts' / aid / 'operad_delta.yaml'
    if path.is_file():
        return yaml.load(path.read_bytes(), Loader=LOADER) or {}
    return {}


# Amendment A1 (amendment_a1.md): --exclude-numeric drops numeric claims from the O count; the as-registered score is the default.
EXCLUDED_KINDS: set = set()


def delta_entries(delta: dict) -> list:
    rows = []
    for key, kind in (('add_or_refine_generators', 'generator'), ('add_or_refine_relations', 'relation'), ('checked_compositions', 'composition'),
                      ('verified_numeric_claims', 'numeric'), ('verified_lemma_statements', 'lemma')):
        if kind in EXCLUDED_KINDS:
            continue
        for entry in delta.get(key) or []:
            ident = entry.get('id') or '%s>%s' % (entry.get('outer_operation'), entry.get('inner_operation')) if isinstance(entry, dict) else str(entry)
            rows.append({'kind': kind, 'id': ident})
    return rows


def reverify_attempt(item: dict, run: Path, aid: str, workdir: Path):
    """Replay one stored answer through the host verifier against a rebuilt clean room (no network, no Lean)."""
    from llm_ladder.packets import P0_SCHEMA, load_row
    from llm_ladder.verify import DeclIndex, Verifier
    response = load_json(run / 'p0' / 'attempts' / aid / 'response.json')
    if not isinstance(response, dict) or response == {'parsed': None}:
        return None
    root = cleanroom_dir(item, 'score', workdir)
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    build_cleanroom(item['arm_s']['freeze_commit'], root, exclude=tuple(item['arm_s']['exclude_paths']))
    try:
        seeded_memory(root, None, set())
        _, row = load_row(root, item['node_id'])
        collection = yaml.load((root / row['operad_collection']).read_bytes(), Loader=LOADER)
        report = Verifier(root, index=DeclIndex(root), run_lean=False).verify_p0(response, P0_SCHEMA, target_statement=collection['target']['source_statement'])
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return report


def ladder_arm(item: dict, run: Path, group: str, args, verifiers: Verifiers, workdir: Path) -> dict:
    receipt = load_json(run / 'ladder_receipt.json') or {}
    compare = load_json(run / ('compare_%s_receipt.json' % ('swarm' if group == 'S' else 'fable'))) or {}
    summary = receipt.get('summary', {})
    attempts = summary.get('attempts', [])
    # accepted_partial (ladder after #164) is an answered attempt; it is not `accepted`, so it earns no units under §5.3
    answered = [a for a in attempts if a.get('status') in ('accepted', 'accepted_partial', 'rejected')]
    infra = [a for a in attempts if a.get('status') == 'infra_error']
    status = summary.get('status')
    scored_aid = summary.get('accepted_attempt') or None
    units, notes = [], []
    if scored_aid:
        aid_row = next(a for a in attempts if a['attempt_id'] == scored_aid)
        entries = delta_entries(attempt_delta(run, scored_aid))
        verified_counts = (aid_row['verified_total'], aid_row['failures_total'])
        if args.reverify_o:
            report = reverify_attempt(item, run, scored_aid, workdir)
            if report is not None:
                verified_counts = (report.verified_total(), report.failure_total())
                entries = [{'kind': kind[:-1] if kind.endswith('s') else kind,
                            'id': str(e.get('id') or '%s>%s' % (e.get('outer'), e.get('inner')))} for kind, rows in report.verified.items() for e in rows
                           if (kind[:-1] if kind.endswith('s') else kind) not in EXCLUDED_KINDS]
                notes.append('operad entries re-verified against a rebuilt clean room: %d verified, %d refused (recorded: %d / %d)' % (
                    verified_counts[0], verified_counts[1], aid_row['verified_total'], aid_row['failures_total']))
        for e in entries:
            units.append({'unit_id': '%s::%s::%s' % (run.name, e['kind'], e['id']), 'class': 'O', 'kind': e['kind'], 'verdict': 'accepted',
                          'evidence_level': 'host verifier (%s)' % ('re-run now' if args.reverify_o else 'recorded at run time'), 'recorded_verdict': 'accepted',
                          'as_recorded_accepted': True, 'verifier_run': None})
        # Lean skeletons the model said it proved: the only route to an L unit at P0
        response = load_json(run / 'p0' / 'attempts' / scored_aid / 'response.json') or {}
        for lemma in (response.get('lemmas') or []) if isinstance(response, dict) else []:
            if lemma.get('claims_proved') and lemma.get('lean_skeleton', '').strip():
                run_result = verifiers.lean_snippet(lemma['lean_skeleton'])
                units.append({'unit_id': '%s::lemma::%s' % (run.name, lemma.get('id')), 'class': 'L', 'kind': 'lean_snippet',
                              'verdict': run_result['status'], 'recorded_verdict': 'not_recorded', 'as_recorded_accepted': False,
                              'evidence_level': 're-run now (Lean %s)' % LEAN_VERSION if run_result['status'] != 'unverified' else run_result.get('reason', ''),
                              'verifier_run': run_result, 'note': 'snippet-level: not the target theorem'})
    else:
        best = next((a for a in attempts if a['attempt_id'] == summary.get('best_attempt')), None)
        if best:
            units.append({'unit_id': '%s::policy_rejected' % run.name, 'class': 'O', 'kind': 'attempt', 'verdict': 'rejected',
                          'evidence_level': 'ladder policy (verified %d, refused %d)' % (best['verified_total'], best['failures_total']),
                          'recorded_verdict': 'rejected', 'as_recorded_accepted': False, 'verifier_run': None})
    if scored_aid:
        outcome = 'ACCEPTED'
    elif status == 'accepted_partial':
        outcome = 'PARTIAL_NOT_ACCEPTED'
    elif status == 'skipped_ungroundable':
        outcome = 'SKIPPED_UNGROUNDABLE'
    elif status == 'blocked_abstained' or (answered and all(a.get('abstained') for a in answered)):
        outcome = 'ABSTAINED'
    elif status == 'budget_refused':
        outcome = 'BUDGET_STOPPED'
    elif answered:
        outcome = 'FAILED'
    elif infra:
        outcome = 'INFRA_FAILURE'
    else:
        outcome = 'NOT_RUN'
    verified = sum(a.get('verified_total', 0) for a in answered)
    refused = sum(a.get('failures_total', 0) for a in answered)
    return {'run': run.relative_to(REPO).as_posix(), 'outcome': outcome, 'units': units, 'notes': notes,
            'spend_usd': summary.get('spend_usd', 0.0), 'cost_status': 'recorded_rated' if receipt else 'unrecorded',
            'calls': compare.get('provider_calls_reserved_this_prompt'), 'seconds': compare.get('wallclock_s_measured'),
            'answered_attempts': len(answered), 'infra_errors': len(infra), 'verified_claims': verified, 'refused_claims': refused,
            'refusal_by_class': summary.get('hallucinations_by_class', {}), 'models_answered': sorted({a['model'] for a in answered}),
            'packet_bytes_sha256': (compare.get('packet') or {}).get('packet_bytes_sha256'), 'stop_reason': summary.get('stop_reason')}


# --------------------------------------------------------------------------- cost
def arm_f_cost(item: dict, overrides: dict):
    cost = (item.get('arm_f') or {}).get('cost') or {}
    if item['node_id'] in overrides:
        row = overrides[item['node_id']]
        return float(row['usd']), 'user_override: ' + str(row.get('basis', 'unspecified'))
    if cost.get('status') == 'recorded_rated':
        return float(cost['recorded_usd']), 'recorded_rated'
    lower = (cost.get('recorded_usd') or 0.0) + (cost.get('estimate_lower_bound_usd_unrecorded_runs') or 0.0)
    if lower:
        return round(lower, 4), 'LOWER_BOUND (committed artifact bytes only; true cost is higher)'
    return None, 'unrecorded'


# --------------------------------------------------------------------------- aggregation and decision
def accepted_in_class(arm: dict | None, cls: str, strict: bool) -> int:
    if not arm:
        return 0
    return sum(1 for u in arm['units'] if u['class'] == cls and (u['verdict'] == 'accepted' if strict else u.get('as_recorded_accepted')))


def has_class(arm: dict | None, cls: str) -> bool:
    """True when the arm has at least one unit of this class with a verdict (strict or recorded): the prompt is eligible for that class."""
    return bool(arm) and any(u['class'] == cls and (u['verdict'] in ('accepted', 'rejected') or u.get('recorded_verdict') in ('accepted', 'rejected'))
                             for u in arm['units'])


def prompt_accept(arm: dict | None, cls: str, strict: bool) -> bool:
    return accepted_in_class(arm, cls, strict) > 0


def aggregate(rows: list, key: str, strict: bool) -> dict:
    out = {'prompts': 0, 'spend_usd': 0.0, 'spend_known_prompts': 0, 'outcomes': collections.Counter(), 'verified_claims': 0, 'refused_claims': 0,
           'by_class': {c: {'accepted': 0, 'rejected': 0, 'unverified': 0, 'prompts_accepted': 0} for c in CLASSES}, 'lower_bound_cost_prompts': 0}
    for row in rows:
        arm = row.get(key)
        if not arm:
            continue
        out['prompts'] += 1
        out['outcomes'][arm['outcome']] += 1
        if arm.get('spend_usd') is not None:
            out['spend_usd'] += arm['spend_usd']
            out['spend_known_prompts'] += 1
        if 'LOWER_BOUND' in str(arm.get('cost_basis', '')):
            out['lower_bound_cost_prompts'] += 1
        out['verified_claims'] += arm.get('verified_claims', 0)
        out['refused_claims'] += arm.get('refused_claims', 0)
        for cls in CLASSES:
            for u in arm['units']:
                if u['class'] != cls:
                    continue
                if strict:
                    out['by_class'][cls][u['verdict'] if u['verdict'] in ('accepted', 'rejected') else 'unverified'] += 1
                else:
                    out['by_class'][cls]['accepted' if u.get('as_recorded_accepted') else ('rejected' if u.get('recorded_verdict') == 'rejected' else 'unverified')] += 1
            if prompt_accept(arm, cls, strict):
                out['by_class'][cls]['prompts_accepted'] += 1
    answered_claims = out['verified_claims'] + out['refused_claims']
    out['refused_claim_rate'] = round(out['refused_claims'] / answered_claims, 4) if answered_claims else None
    out['outcomes'] = dict(out['outcomes'])
    for cls in CLASSES:
        n = out['by_class'][cls]['accepted']
        out['by_class'][cls]['cost_per_accepted_unit_usd'] = round(out['spend_usd'] / n, 6) if n and out['spend_known_prompts'] == out['prompts'] else None
    accepted_prompts = sum(1 for row in rows if row.get(key) and any(prompt_accept(row[key], c, strict) for c in CLASSES))
    out['prompts_with_any_accepted'] = accepted_prompts
    out['cost_per_accepted_prompt_usd'] = round(out['spend_usd'] / accepted_prompts, 6) if accepted_prompts and out['spend_known_prompts'] == out['prompts'] else None
    out['spend_usd'] = round(out['spend_usd'], 6)
    return out


def completeness(rows: list, keys) -> dict:
    total = unverified = 0
    for row in rows:
        for key in keys:
            arm = row.get(key)
            for u in (arm or {}).get('units', []):
                total += 1
                unverified += u['verdict'] == 'unverified'
    return {'units': total, 'unverified': unverified, 'complete': total > 0 and unverified == 0}


def decide(cls: str, pairs: list, s_cost: float | None, f_cost: float | None, f_cost_basis: str, complete: bool, label: str) -> dict:
    """pairs: [(node, S_accepts, F_accepts)] for eligible prompts."""
    n = len(pairs)
    b = sum(1 for _, s, f in pairs if f and not s)   # Fable accepted, swarm not
    c = sum(1 for _, s, f in pairs if s and not f)   # swarm accepted, Fable not
    ties = n - b - c
    result = {'comparison': label, 'class': cls, 'eligible_prompts': n, 'fable_only': b, 'swarm_only': c, 'ties': ties,
              'swarm_accept_rate': round(sum(1 for _, s, _f in pairs if s) / n, 3) if n else None,
              'fable_accept_rate': round(sum(1 for _, _s, f in pairs if f) / n, 3) if n else None,
              'swarm_accept_wilson95': wilson(sum(1 for _, s, _f in pairs if s), n), 'fable_accept_wilson95': wilson(sum(1 for _, _s, f in pairs if f), n),
              'net_loss_prompts': b - c, 'sign_test_p_swarm_worse': round(sign_test_p(b, c), 4) if b > c else None}
    if not S_CAN_REACH[cls]:
        result.update(verdict='NOT_TESTABLE_AT_P0', reason='Arm S is P0 only and cannot produce a %s unit; stages P1-P5 are not wired.' % ('Rust/Python witness' if cls == 'W' else cls))
        return result
    if n < MIN_ELIGIBLE:
        result.update(verdict='INCONCLUSIVE', reason='%d eligible prompts, fewer than the pre-registered minimum of %d (the fresh-Fable arm is what raises n).' % (n, MIN_ELIGIBLE))
        return result
    net = b - c
    quality = 'pass' if net <= MARGIN_PROMPTS else ('fail' if net >= REFUTE_NET_PROMPTS or (result['sign_test_p_swarm_worse'] or 1) <= SIGN_TEST_ALPHA else 'borderline')
    if s_cost is None or f_cost is None:
        cost = 'not_evaluable'
        ratio = None
    elif f_cost == 0 and s_cost == 0:
        cost, ratio = 'tie', 1.0
    elif f_cost == 0:
        cost, ratio = 'fail', None
    else:
        ratio = round(s_cost / f_cost, 4)
        cost = 'tie' if abs(ratio - 1) <= TIE_COST_REL else ('pass' if ratio <= COST_RATIO_MAX else 'fail')
    result.update(quality_leg=quality, cost_leg=cost, swarm_over_fable_cost_ratio=ratio, fable_cost_basis=f_cost_basis)
    if quality == 'fail':
        verdict = 'REFUTES'
    elif quality == 'borderline':
        verdict = 'INCONCLUSIVE'
    elif cost == 'fail':
        verdict = 'REFUTES_ON_COST'
    elif cost == 'not_evaluable':
        verdict = 'QUALITY_ONLY_COST_NOT_EVALUABLE'
    else:
        verdict = 'SUPPORTS'
    if not complete and verdict in ('SUPPORTS', 'QUALITY_ONLY_COST_NOT_EVALUABLE'):
        verdict = 'INDICATIVE_' + verdict + '_UNVERIFIED_UNITS_REMAIN'
    result['verdict'] = verdict
    return result


# --------------------------------------------------------------------------- report
def unit_counts(arm: dict | None, strict: bool = True) -> dict:
    out = {c: {'accepted': 0, 'rejected': 0, 'unverified': 0} for c in CLASSES}
    for u in (arm or {}).get('units', []):
        out[u['class']][u['verdict'] if u['verdict'] in ('accepted', 'rejected') else 'unverified'] += 1
    return out


def fmt_counts(counts: dict) -> str:
    return ' '.join('%s %d/%d/%d' % (c, counts[c]['accepted'], counts[c]['rejected'], counts[c]['unverified']) for c in CLASSES)


def blind_outcome(outcome: str) -> str:
    """Outcome words that exist for one arm only (the reuse arm's) would unblind the table; fold them into the common vocabulary."""
    return {'ACCEPTED_ON_DISK_UNVERIFIED_NOW': 'UNVERIFIED', 'NOT_RECORDED': 'UNVERIFIED', 'INFRA_FAILURE': 'FAILED', 'BUDGET_STOPPED': 'FAILED',
            'NOT_RUN': 'NONE'}.get(outcome, outcome)


def render_blinded(rows: list, protocol_sha: str) -> str:
    lines = ['# Blinded score table (verifier verdicts only)', '',
             'Columns X and Y are two anonymised arms; the assignment is a per-prompt coin fixed by the protocol hash and is not shown here.',
             'Counts are accepted/rejected/unverified units per class: O operad entry, L Lean file, W Rust or Python witness. Cost is withheld until `--unblind`.', '',
             '| stratum | prompt | X outcome | X units | Y outcome | Y units |', '|---|---|---|---|---|---|']
    for row in rows:
        cells = {}
        for group, arms in (('S', ['S']), ('F', ['F_fresh', 'F_reuse'])):
            arm = next((row[a] for a in arms if row.get(a)), None)
            cells[blind_label(protocol_sha, row['node_id'], group)] = (blind_outcome(arm['outcome']) if arm else 'NONE', fmt_counts(unit_counts(arm)) if arm else '-')
        lines.append('| %s | %s | %s | %s | %s | %s |' % (row['stratum'], row['node_id'], *cells.get('X', ('NONE', '-')), *cells.get('Y', ('NONE', '-'))))
    return '\n'.join(lines) + '\n'


def render_report(result: dict) -> str:
    out = ['# Fable versus swarm: score report', '',
           'AuthorityEffect: None. Verifier verdicts only. Protocol sha256 `%s`; cohort base commit `%s`.' % (result['protocol_sha256'][:16], result['cohort_base_commit'][:12]), '',
           '**Mode:** verifiers re-run = %s; operad entries re-verified = %s; verification complete = %s (%d of %d units unverified).' % (
               result['flags']['run_verifiers'], result['flags']['reverify_o'], result['completeness']['complete'],
               result['completeness']['unverified'], result['completeness']['units']), '']
    if not result['unblinded']:
        out += ['The arm-resolved table, costs and decision are withheld. Re-run with `--unblind` after reading the blinded table.', '']
        return '\n'.join(out)
    out += ['## Decision (pre-registered rule, protocol.md section 8)', '', '| comparison | class | eligible | Fable-only | swarm-only | ties | quality | cost | ratio | verdict |', '|---|---|---|---|---|---|---|---|---|---|']
    for d in result['decisions']:
        out.append('| %s | %s | %d | %d | %d | %d | %s | %s | %s | **%s** |' % (d['comparison'], d['class'], d['eligible_prompts'], d['fable_only'], d['swarm_only'], d['ties'],
                                                                         d.get('quality_leg', '-'), d.get('cost_leg', '-'), d.get('swarm_over_fable_cost_ratio', '-'), d['verdict']))
    out += ['', '## Aggregates per arm (strict = verified now or by sealed receipt at Lean %s; as-recorded = every verdict a receipt claims, any toolchain, self-reports included)' % LEAN_VERSION, '']
    for name, agg in result['aggregates'].items():
        out.append('### %s' % name)
        out.append('prompts %d, outcomes %s, spend USD %s (%s), refused-claim rate %s' % (
            agg['strict']['prompts'], agg['strict']['outcomes'], agg['strict']['spend_usd'], result['cost_notes'].get(name, ''), agg['strict']['refused_claim_rate']))
        for view in ('strict', 'as_recorded'):
            a = agg[view]
            out.append('- %s: ' % view + '; '.join('%s accepted %d / rejected %d / unverified %d (prompts accepted %d)' % (
                c, a['by_class'][c]['accepted'], a['by_class'][c]['rejected'], a['by_class'][c]['unverified'], a['by_class'][c]['prompts_accepted']) for c in CLASSES))
        out.append('- cost per accepted prompt (strict): %s; per accepted unit: %s' % (agg['strict']['cost_per_accepted_prompt_usd'],
                                                                                         {c: agg['strict']['by_class'][c]['cost_per_accepted_unit_usd'] for c in CLASSES}))
        out.append('')
    out += ['## Per prompt', '', '| stratum | prompt | arm | outcome | O a/r/u | L a/r/u | W a/r/u | spend USD | basis |', '|---|---|---|---|---|---|---|---|---|']
    for row in result['rows']:
        for key in ('S', 'F_fresh', 'F_reuse'):
            arm = row.get(key)
            if not arm:
                continue
            counts = unit_counts(arm)
            out.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (row['stratum'], row['node_id'], key, arm['outcome'], *('%d/%d/%d' % (counts[c]['accepted'], counts[c]['rejected'], counts[c]['unverified']) for c in CLASSES),
                                                                         arm.get('spend_usd'), arm.get('cost_basis', '')))
    if result['notes']:
        out += ['', '## Notes', ''] + ['- ' + n for n in result['notes']]
    return '\n'.join(out) + '\n'


# --------------------------------------------------------------------------- main
def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--cohort', default=None)
    parser.add_argument('--strata', default='D,P,C')
    parser.add_argument('--only', default=None)
    parser.add_argument('--out', default=None, help='output folder (default dag/pfp/compare/scores/<UTC stamp>)')
    parser.add_argument('--run-verifiers', action='store_true', help='run Lean 4.35.0, pytest and cargo as subprocesses')
    parser.add_argument('--reverify-o', action='store_true', help='re-check operad entries of the scored attempts against a rebuilt clean room (no network, no Lean)')
    parser.add_argument('--unblind', action='store_true')
    parser.add_argument('--exclude-numeric', action='store_true', help='Amendment A1: numeric claims earn no O units (see amendment_a1.md)')
    parser.add_argument('--cost-overrides', default=None, help='JSON {node_id: {"usd": 12.3, "basis": "console session cost"}} for Arm F reuse runs with unrecorded cost')
    parser.add_argument('--lean-project', default=str(REPO / 'lean4'), help='lean4/ folder whose lake environment has the Mathlib v4.35.0 build')
    parser.add_argument('--lake', default=None)
    parser.add_argument('--lean-timeout-s', type=int, default=3600)
    parser.add_argument('--test-timeout-s', type=int, default=3600)
    parser.add_argument('--skip-lean', action='store_true')
    parser.add_argument('--skip-python', action='store_true')
    parser.add_argument('--skip-cargo', action='store_true')
    parser.add_argument('--cargo-target', default=str(Path.home() / '.pfp-ct'), help='short CARGO_TARGET_DIR (Windows MAX_PATH)')
    parser.add_argument('--keep-cargo-target', action='store_true')
    parser.add_argument('--min-free-gb-cargo', type=float, default=15.0)
    parser.add_argument('--workdir', default=str(SHORT_ROOT))
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.exclude_numeric:
        EXCLUDED_KINDS.add('numeric')
    try:
        cohort = load_cohort(args.cohort) if args.cohort else load_cohort()
        protocol_sha = cohort['protocol']['sha256']
        strata = tuple(s.strip() for s in args.strata.split(',') if s.strip())
        items = selected_items(cohort, strata, args.only.split(',') if args.only else None)
        overrides = load_json(Path(args.cost_overrides)) if args.cost_overrides else {}
        overrides = overrides or {}
        verifiers = Verifiers(args)
        workdir = Path(args.workdir)
        notes, rows = [], []
        for item in items:
            row = {'stratum': item['stratum'], 'node_id': item['node_id'], 'cohort_item_sha256': item_sha256(item), 'S': None, 'F_fresh': None, 'F_reuse': None}
            run = find_run(item['node_id'], 'compare_swarm', notes)
            row['S'] = ladder_arm(item, run, 'S', args, verifiers, workdir) if run else None
            fresh = find_run(item['node_id'], 'compare_fable', notes)
            row['F_fresh'] = ladder_arm(item, fresh, 'F', args, verifiers, workdir) if fresh else None
            if row['S']:
                row['S']['cost_basis'] = 'recorded_rated'
            if row['F_fresh']:
                row['F_fresh']['cost_basis'] = 'recorded_rated'
            if item.get('arm_f'):
                units = f_reuse_units(item, verifiers)
                usd, basis = arm_f_cost(item, overrides)
                if item['stratum'] == 'P':
                    headline = item['arm_f']['headline_attempt']
                    units = expand_o_units([u for u in units if u['unit_id'].endswith('::' + headline['attempt_id']) and headline['run'].rsplit('/', 1)[-1] in u['unit_id']])
                outcome = 'ACCEPTED' if any(u['verdict'] == 'accepted' for u in units) else (
                    'FAILED' if any(u['verdict'] == 'rejected' for u in units) else ('UNVERIFIED' if any(u['recorded_verdict'] == 'accepted' for u in units) else 'NOT_RECORDED'))
                if item['stratum'] == 'D' and outcome == 'UNVERIFIED':
                    outcome = 'ACCEPTED_ON_DISK_UNVERIFIED_NOW'
                row['F_reuse'] = {'run': [r['path'] for r in item['arm_f']['runs']], 'outcome': outcome, 'units': units, 'spend_usd': usd, 'cost_basis': basis,
                                  'calls': None, 'seconds': None, 'verified_claims': sum(u.get('entries', {}).get('verified', 0) for u in units),
                                  'refused_claims': sum(u.get('entries', {}).get('refused', 0) for u in units)}
                if item['stratum'] == 'P':   # the recorded attempt is the pre-registered paired Fable baseline for the replayed packet
                    row['F_fresh'] = row['F_fresh'] or dict(row['F_reuse'], paired_source='recorded ladder attempt, byte-identical packet replayed to Arm S')
            rows.append(row)
        # ---- aggregates
        groups = {'S': 'S', 'F_reuse': 'F_reuse', 'F_paired (fresh, or recorded P attempt)': 'F_fresh'}
        aggregates, cost_notes = {}, {}
        for name, key in groups.items():
            agg = {'strict': aggregate(rows, key, True), 'as_recorded': aggregate(rows, key, False)}
            if agg['strict']['prompts']:
                aggregates[name] = agg
                bases = collections.Counter(str((r.get(key) or {}).get('cost_basis')).split(' (')[0] for r in rows if r.get(key))
                cost_notes[name] = ', '.join('%s x%d' % kv for kv in sorted(bases.items()))
        comp = completeness(rows, ('S', 'F_reuse', 'F_fresh'))
        # ---- decisions
        decisions = []
        for cls in CLASSES:
            paired = [(r['node_id'], prompt_accept(r['S'], cls, True), prompt_accept(r['F_fresh'], cls, True)) for r in rows
                      if r['S'] and r['F_fresh'] and (has_class(r['F_fresh'], cls) or cls == 'O')]
            s_cost = sum(r['S']['spend_usd'] for r in rows if r['S'] and r['F_fresh']) / max(1, sum(1 for _, s, _f in paired if s)) if any(s for _, s, _f in paired) else None
            f_cost = sum((r['F_fresh']['spend_usd'] or 0) for r in rows if r['S'] and r['F_fresh']) / max(1, sum(1 for _, _s, f in paired if f)) if any(f for _, _s, f in paired) else None
            decisions.append(decide(cls, paired, s_cost, f_cost, 'recorded_rated', comp['complete'], 'C1 paired P0 (replayed packet / fresh Fable)'))
            outcome_pairs = [(r['node_id'], prompt_accept(r['S'], cls, True), prompt_accept(r['F_reuse'], cls, True)) for r in rows
                             if r['S'] and r['F_reuse'] and r['stratum'] == 'D' and has_class(r['F_reuse'], cls)]
            s_all = sum(r['S']['spend_usd'] for r in rows if r['S'] and r['F_reuse'] and r['stratum'] == 'D')
            f_costs = [r['F_reuse']['spend_usd'] for r in rows if r['S'] and r['F_reuse'] and r['stratum'] == 'D']
            f_known = None if any(c is None for c in f_costs) or not f_costs else sum(f_costs)
            s_cost2 = (s_all / max(1, sum(1 for _, s, _f in outcome_pairs if s))) if any(s for _, s, _f in outcome_pairs) else None
            f_cost2 = (f_known / max(1, sum(1 for _, _s, f in outcome_pairs if f))) if f_known is not None and any(f for _, _s, f in outcome_pairs) else None
            decisions.append(decide(cls, outcome_pairs, s_cost2, f_cost2, 'mixed: recorded where available, LOWER_BOUND otherwise', comp['complete'], 'C2 outcome (Fable agentic sessions, reuse)'))
        result = {'schema_id': 'omega.pfp.compare.score.v1', 'authority_effect': 'None', 'protocol_sha256': protocol_sha, 'cohort_base_commit': cohort['built_from']['base_commit'],
                  'flags': {k: getattr(args, k) for k in ('run_verifiers', 'reverify_o', 'skip_lean', 'skip_python', 'skip_cargo', 'strata', 'only', 'unblind',
                                                           'exclude_numeric')},
                  'amendments': ['A1 exclude_numeric'] if args.exclude_numeric else [],
                  'completeness': comp, 'unblinded': args.unblind, 'rows': rows, 'aggregates': aggregates, 'cost_notes': cost_notes, 'decisions': decisions, 'notes': notes,
                  'verifier_log': verifiers.log, 'harness_commit': git('rev-parse', 'HEAD').strip()}
        # ---- write
        stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        out_dir = Path(args.out) if args.out else HERE / 'scores' / (stamp + ('_A1_no_numeric' if args.exclude_numeric else ''))
        out_dir.mkdir(parents=True, exist_ok=True)
        blinded = render_blinded(rows, protocol_sha)
        (out_dir / 'blinded_table.md').write_bytes(blinded.encode('utf-8'))
        blinded_json = [{'stratum': r['stratum'], 'node_id': r['node_id'], **{blind_label(protocol_sha, r['node_id'], g): {
            'outcome': blind_outcome((next((r[a] for a in arms if r.get(a)), None) or {}).get('outcome', 'NONE')),
            'units': [{'class': u['class'], 'verdict': u['verdict']} for u in (next((r[a] for a in arms if r.get(a)), None) or {}).get('units', [])]}
            for g, arms in (('S', ['S']), ('F', ['F_fresh', 'F_reuse']))}} for r in rows]
        (out_dir / 'blinded_scores.json').write_bytes(json_bytes(blinded_json))
        inputs = {'cohort.json': file_sha256(HERE / 'cohort.json'), 'protocol.md': protocol_sha256()}
        for row in rows:
            for key in ('S', 'F_fresh'):
                if row.get(key) and row[key].get('run') and isinstance(row[key]['run'], str):
                    inputs[row[key]['run'] + '/ladder_receipt.json'] = file_sha256(REPO / row[key]['run'] / 'ladder_receipt.json')
        if args.unblind:
            (out_dir / 'report.md').write_bytes(render_report(result).encode('utf-8'))
        else:
            (out_dir / 'report_blinded.md').write_bytes(render_report(result).encode('utf-8'))
        result['inputs_sha256'] = inputs
        (out_dir / 'score_receipt.json').write_bytes(json_bytes(result if args.unblind else {k: v for k, v in result.items() if k not in ('rows', 'aggregates', 'decisions', 'cost_notes')}))
        print(blinded)
        print('wrote %s (%s)' % (out_dir.relative_to(REPO).as_posix() if out_dir.is_relative_to(REPO) else out_dir,
                                 'unblinded: report.md' if args.unblind else 'blinded: blinded_table.md, blinded_scores.json, report_blinded.md'))
        print('verification complete: %s (%d of %d units unverified)' % (comp['complete'], comp['unverified'], comp['units']))
        if args.unblind:
            for d in decisions:
                print('%-44s class %s eligible %d  F-only %d  S-only %d  -> %s' % (d['comparison'], d['class'], d['eligible_prompts'], d['fable_only'], d['swarm_only'], d['verdict']))
        return 0
    except CompareError as error:
        print('REFUSED: %s' % error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
