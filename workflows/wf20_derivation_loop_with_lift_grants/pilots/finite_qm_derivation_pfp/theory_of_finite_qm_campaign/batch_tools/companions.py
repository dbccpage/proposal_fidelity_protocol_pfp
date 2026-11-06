"""Companion records for live code a batch adds or edits, in the current consolidated layout.

Each subject X gets X.contract.score.yaml (one combined document with contract and scoring
history, written through scripts/contract_scores.write_legacy so old receipt names stay logical
aliases) and X.<ext>.doc.yaml. Engineering grades stay unassessed under SCORING.md 1.4: no
completed score token is invented. Frozen custody snapshots receive no companion.
"""
from __future__ import annotations

import ast
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import json_bytes, load_json, load_module, load_yaml, replace_bytes, sha, yaml_bytes  # noqa: E402
from stages import Batch  # noqa: E402

SUFFIXES = ('.py', '.rs', '.lean')
RUN_FILES = ('check_candidate.py', 'format_certificate.py', 'semantic_mutants.py')


def symbols_of(path: Path):
    text = path.read_text(encoding='utf-8')
    if path.suffix == '.py':
        return [n.name for n in ast.parse(text).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if path.suffix == '.rs':
        return re.findall(r'^pub (?:fn|mod|struct|enum) (\w+)', text, re.M)
    return re.findall(r'^(?:theorem|def|lean_lib|package) (\w+)', text, re.M)


def default_subjects(batch: Batch):
    ctx = batch.ctx
    found = []
    for task in batch.tasks():
        run = batch.run(task)
        found += [run / n for n in RUN_FILES if (run / n).is_file()]
        profile_path = run / 'p0/profile.json'
        if profile_path.is_file():
            for name in load_json(profile_path)['production_sources']:
                if name.endswith(SUFFIXES) and not name.startswith('dag/results/'):
                    found.append(ctx.root / name)
    found += [p for p in sorted((batch.dir / 'specs').glob('*')) if p.suffix in SUFFIXES] if (batch.dir / 'specs').is_dir() else []
    extra = batch.dir / 'companions.json'
    if extra.is_file():
        found += [ctx.root / s for s in load_json(extra).get('subjects', [])]
    return sorted(set(found))


def current_source_sha(scores, path: Path):
    combined = scores.canonical_path(Path(str(path) + '.contract.yaml'))
    if not combined.is_file():
        return None
    document = load_json(combined)
    return (document.get('contract') or {}).get('source_sha256')


def write_companions(batch: Batch, subjects=None):
    ctx = batch.ctx
    scores = load_module('pfp_contract_scores', ctx.root / 'scripts/contract_scores.py')
    levels = load_json(batch.dir / 'companions.json').get('levels', {}) if (batch.dir / 'companions.json').is_file() else {}
    evidence = ctx.rel(batch.dir / 'README.md')
    records = []
    for path in subjects or default_subjects(batch):
        rel = ctx.rel(path)
        digest = sha(path)
        level = levels.get(rel) or ('L2' if path.name in RUN_FILES or 'batches' in path.parts else 'L1')
        shared = {'schema_id': 'finite-qm.code-companion.v1', 'subject': rel, 'source_sha256': digest, 'authority_effect': 'None'}
        boundaries = ['No full refined-carrier operad or blanket original-target closure.',
                      'No production panic-freedom or arbitrary unreviewed-input contract is inferred for finite replay helpers.']
        contract = dict(shared, contract_urn='urn:finite-qm:pfp:%s:%s' % (batch.selection['batch_id'], hashlib.sha256(rel.encode()).hexdigest()[:20]),
                        symbols=symbols_of(path),
                        owned_invariants=['Only the literal definitions and declared bounded replay contract of this source are claimed.',
                                          'Source bytes and actual stage/native receipts are retained; source labels and policy flags do not admit a mathematical or physical target.'],
                        boundaries=boundaries, evidence=[evidence])
        score = dict(shared, rubric='SCORING.md v2.0.0 section1.4', capability_level=level, engineering_grade=None, composite_score=None,
                     assessment_status='incomplete_no_completed_score_token',
                     gates={g: {'grade': None, 'status': 'formal_scoring_not_performed'} for g in ('G1', 'G2', 'G3', 'G4', 'G5')},
                     refusal_reason=('A complete five-gate engineering-grade assessment was not performed. Native/kernel/custody receipts support '
                                     'their stated bounded scopes and do not justify an invented grade.'), evidence=[evidence])
        doc = dict(shared, purpose='Batch checker, wire formatter, semantic-mutant hook or production source; not a physical or proof-authority service.',
                   design={'profile': 'Exact or symbolic on reviewed carriers; any binary64 use is diagnostic only.',
                           'frozen_sources': 'Historical input/construction/source snapshots are immutable custody assets and receive no documentary backfill.'},
                   boundaries=boundaries, evidence=[evidence])
        if current_source_sha(scores, path) != digest:
            scores.write_legacy(Path(str(path) + '.contract.yaml'), yaml_bytes(contract))
            scores.write_legacy(Path(str(path) + '.score.yaml'), yaml_bytes(score))
        doc_path = Path(str(path) + '.doc.yaml')
        if not doc_path.is_file() or (load_yaml(doc_path) or {}).get('source_sha256') != digest:
            replace_bytes(doc_path, yaml_bytes(doc))
        combined = scores.canonical_path(Path(str(path) + '.contract.yaml'))
        records.append({'subject': rel, 'sha256': digest, 'capability_level': level, 'engineering_grade': None,
                        'companions': [ctx.rel(combined), ctx.rel(doc_path)]})
    out = batch.dir / 'review/companion_records.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    replace_bytes(out, json_bytes({
        'scope': 'Live newly added/edited production and replay code only. Frozen source copies remain custody assets; no repository-wide legacy companion audit is claimed.',
        'layout': 'X.contract.score.yaml (combined contract and scoring history) plus X.<ext>.doc.yaml',
        'records': records, 'subjects': len(records), 'companions': 2 * len(records), 'no_completed_grade_tokens': True}))
    return {'live_subjects': len(records), 'companions': 2 * len(records), 'all_engineering_grades': None}
