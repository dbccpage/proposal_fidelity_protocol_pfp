"""Independent exact finite controls; no project/native imports or execution."""
from fractions import Fraction
from itertools import permutations, product
from pathlib import Path
import hashlib
import json
import random


def det_expansion(a):
    n = len(a)
    total = 0
    for p in permutations(range(n)):
        inversions = sum(p[i] > p[j] for i in range(n) for j in range(i + 1, n))
        term = (-1) ** inversions
        for i, j in enumerate(p):
            term *= a[i][j]
        total += term
    return total


def bareiss_model(a):
    """Source algorithm, with extra assertions exposing exact-division premises."""
    n = len(a)
    if any(len(row) != n for row in a):
        return 'shape_refusal'
    if not n:
        return 1
    a = [list(row) for row in a]
    sign, previous = 1, 1
    for k in range(n - 1):
        if not a[k][k]:
            p = next((i for i in range(k + 1, n) if a[i][k]), None)
            if p is None:
                return 0
            a[k], a[p] = a[p], a[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                numerator = a[i][j] * a[k][k] - a[i][k] * a[k][j]
                assert previous and numerator % previous == 0
                a[i][j] = numerator // previous
        previous = a[k][k]
    return sign * a[-1][-1]


def pfaffian_expansion(a):
    if not a:
        return Fraction(1)
    total = Fraction(0)
    for j in range(1, len(a)):
        rest = [i for i in range(1, len(a)) if i != j]
        total += (-1) ** (j + 1) * a[0][j] * pfaffian_expansion([[a[i][k] for k in rest] for i in rest])
    return total


def pfaffian_model(a):
    n = len(a)
    if any(len(row) != n for row in a) or n % 2 or n > 128:
        return 'shape_refusal'
    if any(a[i][i] != 0 for i in range(n)) or any(a[i][j] != -a[j][i] for i in range(n) for j in range(i + 1, n)):
        return 'alternation_refusal'
    a = [list(map(Fraction, row)) for row in a]
    value = Fraction(1)
    for k in range(0, n, 2):
        p = next((j for j in range(k + 1, n) if a[k][j]), None)
        if p is None:
            return Fraction(0)
        if p != k + 1:
            for row in a:
                row[k + 1], row[p] = row[p], row[k + 1]
            a[k + 1], a[p] = a[p], a[k + 1]
            value = -value
        inverse = 1 / a[k][k + 1]
        value *= a[k][k + 1]
        for i in range(k + 2, n):
            for j in range(i + 1, n):
                correction = (a[k][i] * a[k + 1][j] - a[k][j] * a[k + 1][i]) * inverse
                a[i][j] -= correction
                a[j][i] = -a[i][j]
    return value


def alternating(n, entries):
    a = [[0] * n for _ in range(n)]
    at = iter(entries)
    for i in range(n):
        for j in range(i + 1, n):
            a[i][j] = next(at)
            a[j][i] = -a[i][j]
    return a


def main():
    adj_cases = 0
    for a, b, c, d in product(range(-2, 3), repeat=4):
        determinant = a * d - b * c
        observed = (a * d - b * c, -a * b + b * a, c * d - d * c, -c * b + d * a)
        assert observed == (determinant, 0, 0, determinant)
        adj_cases += 1
    det_cases = 0
    for n in range(4):
        for entries in product((-1, 0, 1), repeat=n * n):
            a = [list(entries[i * n:(i + 1) * n]) for i in range(n)]
            assert bareiss_model(a) == det_expansion(a)
            det_cases += 1
    rng = random.Random(20261110)
    for _ in range(128):
        a = [[rng.randint(-5, 5) for _ in range(4)] for _ in range(4)]
        assert bareiss_model(a) == det_expansion(a)
    assert bareiss_model([[1, 2]]) == 'shape_refusal'
    pf_cases = 0
    for n in (0, 2, 4):
        for entries in product((-1, 0, 1), repeat=n * (n - 1) // 2):
            a = alternating(n, entries)
            p = pfaffian_model(a)
            assert p == pfaffian_expansion(a) and p * p == det_expansion(a)
            pf_cases += 1
    for _ in range(128):
        a = alternating(6, [rng.randint(-3, 3) for _ in range(15)])
        p = pfaffian_model(a)
        assert p == pfaffian_expansion(a) and p * p == det_expansion(a)
    assert pfaffian_model([[0]]) == 'shape_refusal'
    assert pfaffian_model([[1, 0], [0, 0]]) == 'alternation_refusal'
    assert pfaffian_model([[0, 1], [1, 0]]) == 'alternation_refusal'
    out = {
        'status': 'finite_controls_pass',
        'controls': [
            {'id': 'RLA-P01', 'rule': '2x2 adjugate identity', 'cases': adj_cases,
             'limits': 'Exact integer identity model; source checked i128 intermediates and i64 output have separate representability premises.'},
            {'id': 'RLA-P02', 'rule': 'Bareiss algorithm versus independent permutation expansion',
             'exhaustive_matrices_dimensions_0_to_3_entries_minus1_0_1': det_cases,
             'deterministic_random_4x4_cases': 128, 'all_divisions_exact': True,
             'ragged_shape_refused': True},
            {'id': 'RLA-P03', 'rule': 'Paired Pfaffian elimination versus independent matching expansion and determinant square',
             'exhaustive_alternating_dimensions_0_2_4_entries_minus1_0_1': pf_cases,
             'deterministic_random_6x6_cases': 128, 'odd_nonzero_diagonal_and_nonskew_refusals': True,
             'field': 'rationals'},
        ],
        'limits': ['Independent exact Python source models and different finite reference formulas; no original Rust execution.',
                   'Finite checks are not a proof for all dimensions, all trait implementations, overflow behavior or dependency correctness.',
                   'No private benchmark content, provider calls or native builds.'],
    }
    p = Path(__file__).with_suffix('.json')
    out['helper_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    p.write_text(json.dumps(out, indent=2) + '\n', encoding='utf8')
    print(json.dumps(out))


if __name__ == '__main__':
    main()
