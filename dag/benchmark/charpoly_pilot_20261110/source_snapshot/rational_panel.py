"""Exact, bounded counterexample checking of model-declared rational equations.

No seed solution or evaluator enters this module. The language describes only
universal real equalities under explicit rational guards. Semantic alignment
between those declarations, the answer prose, and QM remains unverified.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import re
import time


VARIABLES = ('J', 'Delta', 'K', 't', 'beta')
OBLIGATIONS = {
    '1': 'Spectrum, spectral projectors, degeneracies and exceptional limits',
    '2': 'Time evolution, transition probability, supremum and attainment',
    '3': 'Reduced state, entropy, concurrence, CHSH and entanglement reachability',
    '4': 'Gibbs state, partition function, partial transpose and thermal entanglement',
    '5': 'Independent consistency checks and definedness',
}
LIMITS = dict(max_artifact_bytes=262144, max_claims=24, max_challenges=12,
              max_guards=8, max_ast_nodes=128, max_ast_depth=16,
              max_rational_bits=128, max_intermediate_bits=4096,
              max_exponent=8, max_steps=200000, max_seconds=10)
CONTRACT = {
    'version': 'rational-counterexample-panel-v1',
    'variables': list(VARIABLES), 'obligations': OBLIGATIONS, 'limits': LIMITS,
    'public_domain': 'J, Delta, K are real; t >= 0 and beta >= 0. Challenges assign all five variables rational values.',
    'rational_codec': 'A string n/d with reduced integer numerator, positive denominator and no leading zeros; zero is 0/1. No floats or JSON booleans.',
    'expression_grammar': {
        'constant': {'op': 'q', 'value': 'n/d'}, 'variable': {'op': 'var', 'name': 'one of the five variables'},
        'binary': {'op': 'add | sub | mul | div', 'left': 'expression', 'right': 'expression'},
        'power': {'op': 'pow', 'base': 'expression', 'exponent': 'integer 0..8'},
    },
    'guard_grammar': {'left': 'expression', 'relation': 'eq | ne | lt | le | gt | ge', 'right': 'expression'},
    'candidate_grammar': {
        'schema_version': '1.0', 'seed_sha256': 'the supplied seed hash', 'contract_sha256': 'the supplied contract hash',
        'answer_text': 'Complete derivation of ALL requested parts, including unsupported mathematics.',
        'claims': [
            {'id': 'unique ASCII identifier', 'obligation_id': '1..5', 'kind': 'forall_real_equality',
             'guards': ['zero to eight guards'], 'lhs': 'expression', 'rhs': 'expression'},
            {'id': 'unique ASCII identifier', 'obligation_id': '1..5', 'kind': 'unsupported',
             'reason': 'Explanation for a claim outside this exact language.'},
        ],
    },
    'panel_grammar': {
        'schema_version': '1.0', 'seed_sha256': 'the supplied seed hash', 'contract_sha256': 'the supplied contract hash',
        'challenges': [{'id': 'unique ASCII identifier', 'obligation_id': '1..5',
                        'assignment': {name: 'n/d' for name in VARIABLES}}],
    },
    'semantics': 'Each forall_real_equality asserts lhs=rhs at all public-domain points where every declared guard is defined and true. Expressions themselves must be defined there. A sufficient-condition antecedent belongs in guards; its failure is not a counterexample. No implicit premises are admitted.',
    'limits_of_evidence': [
        'Only exact rational substitutions are checked; finite successes never prove a universal equation.',
        'No trigonometric, exponential, logarithmic, complex, matrix, square-root or limit checker is supplied.',
        'An exact refutation concerns the encoded assertion only. Its connection to prose and the requested QM result remains OPEN.',
        'Missing, unsupported, malformed and resource-exhausted evidence never certifies an obligation.',
        'No code strings, model-issued verdicts or expected answers are accepted.',
    ],
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


CONTRACT_SHA256 = digest(CONTRACT)


class ArtifactError(ValueError):
    pass


class ResourceLimit(ValueError):
    pass


class UndefinedExpression(ValueError):
    pass


class WorkBudget:
    def __init__(self):
        self.steps = 0
        self.started = time.monotonic()

    def tick(self):
        self.steps += 1
        if self.steps > LIMITS['max_steps'] or time.monotonic() - self.started > LIMITS['max_seconds']:
            raise ResourceLimit('HOST_RESOURCE_LIMIT')


def keys(value, required):
    if type(value) is not dict or set(value) != set(required):
        raise ArtifactError('INVALID_FIELDS')


def bounded_text(value, maximum, *, nonempty=True):
    if type(value) is not str or len(value) > maximum or (nonempty and not value.strip()):
        raise ArtifactError('INVALID_TEXT')
    try:
        value.encode('utf-8')
    except UnicodeError as exc:
        raise ArtifactError('INVALID_UNICODE_TEXT') from exc
    return value


def qstr(value):
    return f'{value.numerator}/{value.denominator}'


def rational(value):
    if type(value) is not str or len(value) > 82 or re.fullmatch(r'-?(?:0|[1-9][0-9]*)/[1-9][0-9]*', value) is None:
        raise ArtifactError('INVALID_RATIONAL')
    numerator, denominator = map(int, value.split('/'))
    if max(abs(numerator).bit_length(), denominator.bit_length()) > LIMITS['max_rational_bits']:
        raise ArtifactError('RATIONAL_TOO_LARGE')
    result = Fraction(numerator, denominator)
    if qstr(result) != value:
        raise ArtifactError('NONCANONICAL_RATIONAL')
    return result


def bounded_list(value, maximum):
    if type(value) is not list or len(value) > maximum:
        raise ArtifactError('INVALID_LIST_SIZE')
    return value


def parse_json(text):
    if type(text) is not str:
        raise ArtifactError('INVALID_JSON_TEXT')
    try:
        if len(text.encode('utf-8')) > LIMITS['max_artifact_bytes']:
            raise ArtifactError('ARTIFACT_TOO_LARGE')

        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ArtifactError('DUPLICATE_JSON_KEY')
                result[key] = value
            return result

        def no_float(_):
            raise ArtifactError('FLOAT_OR_NONFINITE_JSON_NUMBER')

        return json.loads(text, object_pairs_hook=unique, parse_float=no_float, parse_constant=no_float)
    except (UnicodeError, RecursionError, json.JSONDecodeError) as exc:
        raise ArtifactError('INVALID_JSON') from exc


def expression(node, work, depth=0, count=None):
    """Validate all nodes before evaluation, including otherwise dead branches."""
    work.tick()
    if count is None:
        count = [0]
    count[0] += 1
    if count[0] > LIMITS['max_ast_nodes'] or depth > LIMITS['max_ast_depth']:
        raise ArtifactError('EXPRESSION_TOO_LARGE')
    if type(node) is not dict or type(node.get('op')) is not str:
        raise ArtifactError('INVALID_EXPRESSION')
    op = node['op']
    if op == 'q':
        keys(node, ('op', 'value')); rational(node['value'])
    elif op == 'var':
        keys(node, ('op', 'name'))
        if type(node['name']) is not str or node['name'] not in VARIABLES:
            raise ArtifactError('UNKNOWN_VARIABLE')
    elif op in ('add', 'sub', 'mul', 'div'):
        keys(node, ('op', 'left', 'right'))
        expression(node['left'], work, depth + 1, count)
        expression(node['right'], work, depth + 1, count)
    elif op == 'pow':
        keys(node, ('op', 'base', 'exponent'))
        if type(node['exponent']) is not int or not 0 <= node['exponent'] <= LIMITS['max_exponent']:
            raise ArtifactError('INVALID_EXPONENT')
        expression(node['base'], work, depth + 1, count)
    else:
        raise ArtifactError('UNSUPPORTED_EXPRESSION')


def binding(obj, seed_sha256):
    if obj['schema_version'] != '1.0' or obj['seed_sha256'] != seed_sha256 or obj['contract_sha256'] != CONTRACT_SHA256:
        raise ArtifactError('BINDING_MISMATCH')


def item_identity(item, seen):
    name = item.get('id')
    if type(name) is not str or re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,39}', name) is None or name in seen:
        raise ArtifactError('INVALID_OR_DUPLICATE_ID')
    seen.add(name)
    if type(item.get('obligation_id')) is not str or item['obligation_id'] not in OBLIGATIONS:
        raise ArtifactError('UNKNOWN_OBLIGATION')


def candidate(text, seed_sha256, work):
    obj = parse_json(text)
    keys(obj, ('schema_version', 'seed_sha256', 'contract_sha256', 'answer_text', 'claims'))
    binding(obj, seed_sha256); bounded_text(obj['answer_text'], 200000)
    seen = set()
    for claim in bounded_list(obj['claims'], LIMITS['max_claims']):
        if type(claim) is not dict:
            raise ArtifactError('INVALID_CLAIM')
        item_identity(claim, seen)
        if claim.get('kind') == 'unsupported':
            keys(claim, ('id', 'obligation_id', 'kind', 'reason'))
            bounded_text(claim['reason'], 2000)
        elif claim.get('kind') == 'forall_real_equality':
            keys(claim, ('id', 'obligation_id', 'kind', 'guards', 'lhs', 'rhs'))
            for guard in bounded_list(claim['guards'], LIMITS['max_guards']):
                keys(guard, ('left', 'relation', 'right'))
                if type(guard['relation']) is not str or guard['relation'] not in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
                    raise ArtifactError('INVALID_RELATION')
                expression(guard['left'], work); expression(guard['right'], work)
            expression(claim['lhs'], work); expression(claim['rhs'], work)
        else:
            raise ArtifactError('UNSUPPORTED_CLAIM_KIND')
    return obj


def panel(text, seed_sha256):
    obj = parse_json(text)
    keys(obj, ('schema_version', 'seed_sha256', 'contract_sha256', 'challenges'))
    binding(obj, seed_sha256)
    seen = set()
    for challenge in bounded_list(obj['challenges'], LIMITS['max_challenges']):
        keys(challenge, ('id', 'obligation_id', 'assignment')); item_identity(challenge, seen)
        keys(challenge['assignment'], VARIABLES)
        for value in challenge['assignment'].values():
            rational(value)
    return obj


def evaluate(node, point, work):
    work.tick()
    op = node['op']
    if op == 'q':
        result = rational(node['value'])
    elif op == 'var':
        result = point[node['name']]
    elif op == 'pow':
        # Definedness of the base is required even when exponent=0.
        result = evaluate(node['base'], point, work) ** node['exponent']
    else:
        left = evaluate(node['left'], point, work); right = evaluate(node['right'], point, work)
        if op == 'add': result = left + right
        elif op == 'sub': result = left - right
        elif op == 'mul': result = left * right
        else:
            if right == 0:
                raise UndefinedExpression('ZERO_DENOMINATOR')
            result = left / right
    if max(abs(result.numerator).bit_length(), result.denominator.bit_length()) > LIMITS['max_intermediate_bits']:
        raise ResourceLimit('INTERMEDIATE_TOO_LARGE')
    return result


def holds(guard, point, work):
    a = evaluate(guard['left'], point, work); b = evaluate(guard['right'], point, work)
    return {'eq': a == b, 'ne': a != b, 'lt': a < b, 'le': a <= b, 'gt': a > b, 'ge': a >= b}[guard['relation']]


def check_pair(claim, challenge, work):
    result = {'claim_id': claim['id'], 'challenge_id': challenge['id'],
              'obligation_id': claim['obligation_id'], 'assignment': challenge['assignment']}
    point = {name: rational(value) for name, value in challenge['assignment'].items()}
    if point['t'] < 0 or point['beta'] < 0:
        return {**result, 'status': 'OUTSIDE_PUBLIC_DOMAIN'}
    try:
        # Evaluate every guard before deciding applicability. An undefined guard
        # is UNKNOWN even if a different guard is false; no domain is invented.
        guards = [holds(guard, point, work) for guard in claim['guards']]
        if not all(guards):
            return {**result, 'status': 'GUARD_FALSE_NOT_A_COUNTEREXAMPLE'}
    except UndefinedExpression:
        return {**result, 'status': 'UNKNOWN_GUARD_UNDEFINED'}
    except ResourceLimit as exc:
        return {**result, 'status': 'UNKNOWN_RESOURCE_LIMIT', 'code': str(exc)}
    try:
        lhs = evaluate(claim['lhs'], point, work); rhs = evaluate(claim['rhs'], point, work)
        return {**result, 'status': 'EXACT_POINT_PASS_NOT_PROOF' if lhs == rhs else 'REFUTED_ENCODED_EQUALITY',
                'lhs': qstr(lhs), 'rhs': qstr(rhs)}
    except UndefinedExpression:
        return {**result, 'status': 'UNDEFINED_AT_ADMISSIBLE_POINT'}
    except ResourceLimit as exc:
        return {**result, 'status': 'UNKNOWN_RESOURCE_LIMIT', 'code': str(exc)}


def check_panel(candidate_text, panel_text, seed_sha256):
    def artifact_hash(text):
        if type(text) is not str:
            return None
        try:
            return hashlib.sha256(text.encode('utf-8')).hexdigest()
        except UnicodeError:
            return None

    work = WorkBudget()
    receipt = {'schema_version': '1.0', 'checker': CONTRACT['version'], 'contract_sha256': CONTRACT_SHA256,
               'seed_sha256': seed_sha256,
               'candidate_sha256': artifact_hash(candidate_text),
               'panel_sha256': artifact_hash(panel_text),
               'artifact_errors': {}, 'claims': [], 'checks': [], 'missing_obligation_ids': list(OBLIGATIONS),
               'accuracy_status': 'UNSCORED', 'all_requested_obligations_remain_uncertified': True,
               'residuals': CONTRACT['limits_of_evidence']}
    parsed = None; challenges = None
    for name, text in (('candidate', candidate_text), ('panel', panel_text)):
        if text is None:
            receipt['artifact_errors'][name] = 'MISSING_ARTIFACT'
            continue
        try:
            if name == 'candidate': parsed = candidate(text, seed_sha256, work)
            else: challenges = panel(text, seed_sha256)
        except (ArtifactError, ResourceLimit) as exc:
            receipt['artifact_errors'][name] = str(exc)
        except (ValueError, RecursionError):
            receipt['artifact_errors'][name] = 'INVALID_ARTIFACT'
    if parsed is not None:
        receipt['missing_obligation_ids'] = sorted(set(OBLIGATIONS) - {c['obligation_id'] for c in parsed['claims']})
        for claim in parsed['claims']:
            local = []
            if claim['kind'] == 'forall_real_equality' and challenges is not None:
                local = [check_pair(claim, challenge, work) for challenge in challenges['challenges']
                         if challenge['obligation_id'] == claim['obligation_id']]
            statuses = {check['status'] for check in local}
            if 'REFUTED_ENCODED_EQUALITY' in statuses: status = 'REFUTED_ENCODED_EQUALITY'
            elif 'UNDEFINED_AT_ADMISSIBLE_POINT' in statuses: status = 'DEFINEDNESS_FAILURE_IN_ENCODED_CLAIM'
            elif any(s.startswith('UNKNOWN') for s in statuses): status = 'UNKNOWN'
            elif 'EXACT_POINT_PASS_NOT_PROOF' in statuses: status = 'FINITE_CHECKS_PASSED_NOT_PROVED'
            else: status = 'OPEN_UNSUPPORTED_OR_UNTESTED'
            receipt['claims'].append({'claim_id': claim['id'], 'obligation_id': claim['obligation_id'],
                                      'status': status, 'semantic_alignment': 'OPEN'})
            receipt['checks'].extend(local)
    receipt['steps_used'] = work.steps
    receipt['host_time_seconds'] = time.monotonic() - work.started
    # Return complete prose unchanged only from a valid envelope. An invalid raw
    # response is retained by the runner, never silently repaired into JSON.
    return receipt, parsed['answer_text'] if parsed is not None else (candidate_text if receipt['candidate_sha256'] is not None else None)


def fixed_panel(seed_sha256):
    """Twelve preregistered input-only probes, with no expected solution values."""
    points = [(0, 0, 0, 0, 0), (1, 1, 1, 1, 1), (-1, 1, -1, 1, 0)]
    challenges = []
    for index, (obligation, point) in enumerate((obligation, point) for obligation in OBLIGATIONS for point in points[:2]):
        challenges.append({'id': f'fixed_{index}', 'obligation_id': obligation,
                           'assignment': {name: f'{value}/1' for name, value in zip(VARIABLES, point)}})
    for obligation in ('2', '4'):
        challenges.append({'id': f'fixed_{len(challenges)}', 'obligation_id': obligation,
                           'assignment': {name: f'{value}/1' for name, value in zip(VARIABLES, points[2])}})
    return {'schema_version': '1.0', 'seed_sha256': seed_sha256, 'contract_sha256': CONTRACT_SHA256,
            'challenges': challenges}
