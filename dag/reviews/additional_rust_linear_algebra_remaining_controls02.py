"""Independent rational controls for reduction, PSD and witness boundaries."""
from fractions import Fraction as Q
from itertools import combinations, permutations, product
from pathlib import Path
import hashlib
import json


def det(a):
    n = len(a)
    result = Q(0)
    for p in permutations(range(n)):
        value = Q((-1) ** sum(p[i] > p[j] for i in range(n) for j in range(i + 1, n)))
        for i, j in enumerate(p):
            value *= a[i][j]
        result += value
    return result


def minor_rank(a, cols):
    for n in range(min(len(a), cols), 0, -1):
        for rr in combinations(range(len(a)), n):
            for cc in combinations(range(cols), n):
                if det([[a[i][j] for j in cc] for i in rr]):
                    return n
    return 0


def rref(a, cols):
    m = [list(map(Q, row)) for row in a]
    pivots = []
    for col in range(cols):
        row = len(pivots)
        pivot = next((i for i in range(row, len(m)) if m[i][col]), None)
        if pivot is None:
            continue
        m[row], m[pivot] = m[pivot], m[row]
        value = m[row][col]
        m[row] = [x / value for x in m[row]]
        for i in range(len(m)):
            if i != row:
                factor = m[i][col]
                m[i] = [x - factor * y for x, y in zip(m[i], m[row])]
        pivots.append(col)
        if len(pivots) == len(m):
            break
    return m, pivots


def kernel(a, cols):
    reduced, pivots = rref(a, cols)
    basis = []
    for free in set(range(cols)) - set(pivots):
        v = [Q(0)] * cols
        v[free] = 1
        for row, p in enumerate(pivots):
            v[p] = -reduced[row][free]
        basis.append(v)
    return basis


def mv(a, x):
    return [sum((u * v for u, v in zip(row, x)), Q(0)) for row in a]


def ldlt(a):
    n = len(a)
    l = [[Q(i == j) for j in range(n)] for i in range(n)]
    d = [Q(0)] * n
    for j in range(n):
        d[j] = a[j][j] - sum(l[j][k] ** 2 * d[k] for k in range(j))
        if d[j] < 0:
            return l, d, False
        residual = [a[i][j] - sum(l[i][k] * l[j][k] * d[k] for k in range(j)) for i in range(j + 1, n)]
        if not d[j]:
            if any(residual):
                return l, d, False
        else:
            for i, value in zip(range(j + 1, n), residual):
                l[i][j] = value / d[j]
    return l, d, True


def all_principal_minors_nonnegative(a):
    return all(det([[a[i][j] for j in subset] for i in subset]) >= 0
               for n in range(1, len(a) + 1) for subset in combinations(range(len(a)), n))


def rank_nullity_admission(pivots, rank, basis, columns):
    return (len(pivots) == rank and all(0 <= p < columns for p in pivots)
            and all(x < y for x, y in zip(pivots, pivots[1:]))
            and rank + len(basis) == columns)


def main():
    reductions = memberships = 0
    for rows, cols in ((0, 0), (0, 2), (2, 0), (1, 2), (2, 1), (2, 2), (2, 3)):
        for data in product((-1, 0, 1), repeat=rows * cols):
            a = [[Q(data[i * cols + j]) for j in range(cols)] for i in range(rows)]
            reduced, pivots = rref(a, cols)
            assert len(pivots) == minor_rank(a, cols)
            basis = kernel(a, cols)
            assert len(basis) + len(pivots) == cols
            assert all(not any(mv(a, v)) for v in basis)
            stacked = [[v[i] for v in basis] for i in range(cols)]
            assert minor_rank(stacked, len(basis)) == len(basis)
            image = [[a[i][j] for j in pivots] for i in range(rows)]
            assert minor_rank(image, len(pivots)) == len(pivots)
            reductions += 1
            if rows == cols == 2:
                for t in product((-1, 0, 1), repeat=rows):
                    aug = [row + [Q(t[i])] for i, row in enumerate(a)]
                    ar, ap = rref(aug, cols + 1)
                    member = len(ap) == len(pivots)
                    assert member == (minor_rank(aug, cols + 1) == minor_rank(a, cols))
                    if member:
                        potential = [Q(0)] * cols
                        for i, j in enumerate(ap):
                            if j < cols:
                                potential[j] = ar[i][cols]
                        assert mv(a, potential) == list(t)
                    memberships += 1
    psd_cases = successful_factorizations = 0
    for n in (1, 2, 3):
        for entries in product((-1, 0, 1), repeat=n * (n + 1) // 2):
            a = [[Q(0)] * n for _ in range(n)]
            values = iter(entries)
            for i in range(n):
                for j in range(i, n):
                    a[i][j] = a[j][i] = Q(next(values))
            l, d, psd = ldlt(a)
            assert psd == all_principal_minors_nonnegative(a)
            if psd:
                assert all(sum(l[i][k] * d[k] * l[j][k] for k in range(n)) == a[i][j]
                           for i in range(n) for j in range(n))
                successful_factorizations += 1
            psd_cases += 1
    a, b = [[Q(1), Q(0)]], [[Q(0), Q(1)]]
    _, pivots = rref(a, 2)
    wrong_basis = kernel(b, 2)
    assert rank_nullity_admission(pivots, 1, wrong_basis, 2)
    assert mv(a, wrong_basis[0]) == [1]
    assert rank_nullity_admission([0], 1, kernel([[Q(0), Q(0)]], 2), 3)
    declared = [[Q(1), Q(0)], [Q(1), Q(0)]]
    assert len(declared) == 2 and minor_rank(declared, 2) == 1
    out = {'status': 'finite_controls_pass', 'controls': [
        {'id': 'RLA-P04', 'rule': 'Exact reduction/image/kernel models versus independent minor rank',
         'matrices': reductions, 'membership_cases': memberships,
         'limits': 'Finite rational source models; rank reference uses determinant minors, not the reduction algorithm.'},
        {'id': 'RLA-P05', 'rule': 'PSD LDLT model versus all principal minors',
         'symmetric_matrices': psd_cases, 'successful_full_factorizations_replayed': successful_factorizations,
         'limits': 'Rational symmetric input, sizes1..3; negative paths return partial factors, not a complete inertia decomposition.'},
        {'id': 'RLA-P06', 'rule': 'RankNullity count admission accepts mixed source witnesses',
         'matrix_a': [[1, 0]], 'matrix_b': [[0, 1]], 'supplied_kernel_of_b': [[1, 0]],
         'accepted_count_census': [1, 1, 2], 'a_times_supplied_vector': [1],
         'also_accepts_columns3_for_rank1_of_a_1x1_and_kernel_of_zero_1x2': True,
         'limits': 'Independent exact model of public constructor outputs and count predicate, not a native run. Rank-nullity theorem itself is not refuted; missing common-source binding is exposed.'},
        {'id': 'RLA-P07', 'rule': 'ExactRepairSpace declared basis count is not matrix rank',
         'basis': [[1, 0], [1, 0]], 'stored_rank_by_with_basis': 2, 'actual_rank': 1,
         'limits': 'Public metadata constructor only; this does not bypass private ExactRepair residual checking.'},
    ], 'limits': ['No original modules, native tools, private benchmark or providers executed.'],
        'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    Path(__file__).with_suffix('.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf8')
    print(json.dumps(out))


if __name__ == '__main__':
    main()
