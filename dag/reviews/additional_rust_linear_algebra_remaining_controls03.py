"""Independent finite exact models; no original module or native execution."""
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import hashlib
import json

def mm(a, b):
    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*b)] for row in a]

def matrix(values, n=2):
    return [list(values[i * n:(i + 1) * n]) for i in range(n)]

def identity(n):
    return [[int(i == j) for j in range(n)] for i in range(n)]

def power(a, n):
    out = identity(len(a))
    for _ in range(n):
        out = mm(out, a)
    return out

matrices = [matrix(v) for v in product((-1, 0, 1), repeat=4)]
changes = conjugacies = 0
for p in matrices:
    a, b = p[0]
    c, d = p[1]
    det = a * d - b * c
    if not det:
        continue
    inv = [[Q(d, det), Q(-b, det)], [Q(-c, det), Q(a, det)]]
    assert mm(p, inv) == mm(inv, p) == identity(2)
    changes += 1
    for op in matrices:
        transported = mm(mm(p, op), inv)
        assert mm(transported, p) == mm(p, op)
        conjugacies += 1

quotients = checked = 0
for m in matrices:
    for blocks in ([[0, 1]], [[0], [1]]):
        h = [[int(i in block) for block in blocks] for i in range(2)]
        sums = mm(m, h)
        b = [sums[block[0]] for block in blocks]
        admitted = all(sums[v] == b[i] for i, block in enumerate(blocks) for v in block)
        assert admitted == (mm(m, h) == mm(h, b))
        checked += 1
        if admitted:
            quotients += 1
            for n in range(6):
                assert mm(power(m, n), h) == mm(h, power(b, n))

roots = {}
for mask in range(512):
    graph = {(i, j) for i in range(3) for j in range(3) if mask & (1 << (3 * i + j))}
    relational_square = {(i, k) for i, j in graph for jj, k in graph if j == jj}
    a = matrix([int((i, j) in graph) for i in range(3) for j in range(3)], 3)
    numeric = mm(a, a)
    assert relational_square == {(i, j) for i in range(3) for j in range(3) if numeric[i][j] > 0}
    key = tuple(sorted(relational_square))
    roots.setdefault(key, []).append(mask)
assert sum(map(len, roots.values())) == 512

observer_pairs = invariance_checks = 0
for report in product((-1, 0, 1), repeat=2):
    for repair in product((-1, 0, 1), repeat=2):
        rd = sum(x * y for x, y in zip(report, repair))
        invariant = True
        for state in product((-1, 0, 1), repeat=2):
            for alpha in (-1, 0, 1):
                old = sum(x * y for x, y in zip(report, state))
                new = sum(report[i] * (state[i] + repair[i] * alpha) for i in range(2))
                assert new - old == rd * alpha
                invariant &= old == new
                invariance_checks += 1
        assert invariant == (rd == 0)
        observer_pairs += 1

# One-dimensional windows over F2, checked as equations independently of Rust.
windows = [(a, b) for a, b in product((0, 1), repeat=2) if a * b == 0]
maps = []
for source, target in product(windows, repeat=2):
    for f in product((0, 1), repeat=3):
        if target[0] * f[0] == f[1] * source[0] and target[1] * f[1] == f[2] * source[1]:
            maps.append((source, target, f))
compositions = fillers = 0
for source, middle, f in maps:
    for middle2, target, g in maps:
        if middle != middle2:
            continue
        composite = tuple(x * y for x, y in zip(f, g))
        assert (source, target, composite) in maps
        compositions += 1
    for source2, target2, g in maps:
        if source != source2 or middle != target2:
            continue
        for h1, h2 in product((0, 1), repeat=2):
            delta = (h1 * source[0], (middle[0] * h1 + h2 * source[1]) % 2, middle[1] * h2)
            if tuple((x - y) % 2 for x, y in zip(f, g)) == delta:
                # Degree-one cycles become target coboundary differences.
                for x in (0, 1):
                    if source[1] * x == 0:
                        assert ((f[1] - g[1]) * x - middle[0] * h1 * x) % 2 == 0
                fillers += 1

terms = 256 ** 3
assert 256 ** 2 <= 1 << 20 and terms <= 1 << 24
assert 2 * terms > 1 << 24
controls = [
    {'id': 'RLA-P08', 'rule': 'Two-sided rational basis changes and conjugacy transport', 'invertible_matrices': changes, 'operator_conjugacies': conjugacies, 'limits': 'Independent exact model on small matrices, not arbitrary scalar traits or original execution.'},
    {'id': 'RLA-P09', 'rule': 'Lumpability commutation and bounded Boolean roots', 'matrix_partition_pairs': checked, 'admitted_quotients': quotients, 'powers_checked_per_admission': 6, 'boolean_3x3_candidates': 512, 'distinct_squares': len(roots), 'limits': 'Finite checks corroborate the source induction; relational composition is the separate Boolean-square reference.'},
    {'id': 'RLA-P10', 'rule': 'R*d=0 exactly controls rational report invariance under supplied repair shifts', 'map_pairs': observer_pairs, 'shift_checks': invariance_checks, 'limits': 'Small exact model; no semantic or physical interpretation of the supplied maps.'},
    {'id': 'RLA-P11', 'rule': 'Semiring multiply budget counts dot-product terms, not individual scalar method calls', 'dimension': 256, 'admitted_terms': terms, 'declared_max_scalar_operations': 1 << 24, 'actual_add_plus_mul_calls': 2 * terms, 'limits': 'Exact loop-count calculation only; no large allocation or original execution. Per-call dot-product budget remains finite.'},
    {'id': 'RLA-P12', 'rule': 'Cochain-map composition and homotopy-induced equality on degree-one cohomology', 'scalar_windows_over_f2': len(windows), 'maps': len(maps), 'compositions': compositions, 'accepted_fillers': fillers, 'limits': 'One-dimensional F2 windows only; general theorem remains conditional on lawful ring operations and the checked equations.'}
]
out = {'status': 'finite_controls_pass', 'controls': controls, 'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'limits': ['No original sources, native tools, providers or private benchmark executed.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf8')
print(json.dumps(out, indent=2))
