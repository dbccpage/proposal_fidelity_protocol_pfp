"""Pre-flight of a node spec before P0: the independent checker, the wire formatter and the P4 mutants.

A defect in a checker found at P2 cannot be repaired by a P3 candidate edit, because the checker bytes are pinned at
P0. This module runs the same checks the later stages will run, with `exact_json.bound` stubbed (no sealed request
exists yet), so that a checker or mutant bug is fixed while nothing is sealed:

* the valid candidate data is accepted by the checker;
* every coordinate mutant and every semantic near miss is rejected, with a message that names a failed predicate;
* every semantic control is accepted and changes the data;
* the wire formatter returns one non-empty tab-separated line per output with no stray whitespace;
* the producer, if named, reproduces the candidate data exactly.

Nothing here accepts a theorem. AuthorityEffect: None.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from challenge import coordinate_mutants  # noqa: E402
from common import load_json, load_module, require  # noqa: E402
from stages import validate_spec  # noqa: E402


def preflight(ctx, task, spec_dir, spec=None):
    spec_dir = Path(spec_dir)
    spec = spec or load_json(spec_dir / (task + '.json'))
    validate_spec(spec['profile'], spec['operad_delta'])
    sys.path.insert(0, str(ctx.root / 'dag/pfp'))
    try:
        import exact_json
    finally:
        sys.path.pop(0)
    state = {'data': None}
    real_bound = exact_json.bound
    public = spec['public_input']

    def stub(request_path, candidate_path, task_id):
        return {}, {'data': state['data']}, public

    exact_json.bound = stub
    try:
        checker = load_module('preflight_checker_' + task.replace('-', '_'), spec_dir / spec['checker'])
        data = spec['candidate']['data']
        profile = spec['profile']
        state['data'] = copy.deepcopy(data)
        checker.check('request', 'candidate')
        plan = profile.get('challenge', {})
        found = coordinate_mutants(data, plan.get('ignore_paths', []), plan.get('max_coordinate_mutants'))
        accepted_mutants = []
        for name, mutate in found:
            bad = copy.deepcopy(data)
            mutate(bad)
            require(bad != data, 'No-op coordinate mutant ' + name)
            state['data'] = bad
            try:
                checker.check('request', 'candidate')
            except ValueError:
                continue
            accepted_mutants.append(name)
        require(not accepted_mutants, 'Checker accepts coordinate mutants: ' + ', '.join(accepted_mutants[:8]))
        near = controls = []
        if spec.get('semantic_mutants'):
            module = load_module('preflight_semantic_' + task.replace('-', '_'), spec_dir / spec['semantic_mutants'])
            near = list(module.semantic_mutants(copy.deepcopy(data), profile)) if hasattr(module, 'semantic_mutants') else []
            controls = list(module.semantic_controls(copy.deepcopy(data), profile)) if hasattr(module, 'semantic_controls') else []
        for item in near:
            bad = copy.deepcopy(data)
            item['mutate'](bad)
            require(bad != data, 'No-op semantic mutant ' + item['id'])
            state['data'] = bad
            try:
                checker.check('request', 'candidate')
            except ValueError:
                continue
            raise ValueError('Checker accepts semantic near miss: ' + item['id'])
        for item in controls:
            good = copy.deepcopy(data)
            item['mutate'](good)
            state['data'] = good
            try:
                checker.check('request', 'candidate')
            except ValueError as error:
                raise ValueError('Checker rejects valid semantic control %s: %s' % (item['id'], error))
        wire = load_module('preflight_wire_' + task.replace('-', '_'), spec_dir / spec['format'])
        lines = wire.lines(data)
        require(lines and all(isinstance(x, str) and x and x == x.strip() and '\n' not in x for x in lines), 'Wire lines must be non-empty single lines')
        tsv = spec['candidate'].get('public_tsv') or ''
        require(tsv.endswith('\n') or not tsv, 'public_tsv must end with a newline')
        return {'task': task, 'coordinate_mutants': len(found), 'semantic_mutants': len(near), 'semantic_controls': len(controls),
                'wire_lines': len(lines), 'public_tsv_lines': len([x for x in tsv.splitlines() if x])}
    finally:
        exact_json.bound = real_bound
