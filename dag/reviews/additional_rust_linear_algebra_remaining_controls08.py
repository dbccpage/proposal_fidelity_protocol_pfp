"""Independent exact controls for scalar checks, interpolation, Bareiss and jets."""
from fractions import Fraction as Q
import hashlib
import itertools as it
import json
from pathlib import Path

def gauss(a, b, n):
    rows = [list(row)+[v] for row, v in zip(a, b)]
    pivots = []
    for c in range(n):
        k = len(pivots)
        r = next((r for r in range(k, len(rows)) if rows[r][c]), None)
        if r is None:
            continue
        rows[k], rows[r] = rows[r], rows[k]
        scale = rows[k][c]
        rows[k] = [x/scale for x in rows[k]]
        for r in range(len(rows)):
            if r != k:
                v = rows[r][c]
                rows[r] = [x-v*y for x, y in zip(rows[r], rows[k])]
        pivots.append(c)
    if any(row[-1] for row in rows[len(pivots):]):
        return None
    x = [Q(0)]*n
    for r, c in enumerate(pivots):
        x[c] = rows[r][-1]
    return x

divisions = 0
def exactdiv(a, b):
    global divisions
    assert b and a % b == 0
    divisions += 1
    return a//b

def bareiss(a, b, n):
    rows = []
    for row, v in zip(a, b):
        raw = list(row)+[v]
        scale = 1
        for q in raw:
            scale *= q.denominator
        rows.append([exactdiv(scale, q.denominator)*q.numerator for q in raw])
    pivots, previous = [], 1
    for c in range(n):
        k = len(pivots)
        r = next((r for r in range(k, len(rows)) if rows[r][c]), None)
        if r is None:
            continue
        rows[k], rows[r] = rows[r], rows[k]
        pivot = rows[k][c]
        for r in range(k+1, len(rows)):
            for j in range(c+1, n+1):
                rows[r][j] = exactdiv(pivot*rows[r][j]-rows[r][c]*rows[k][j], previous)
            rows[r][c] = 0
        pivots.append(c)
        previous = pivot
    if any(row[-1] for row in rows[len(pivots):]):
        return None
    x = [Q(0)]*n
    for r, c in reversed(list(enumerate(pivots))):
        x[c] = (Q(rows[r][-1])-sum((rows[r][j]*x[j] for j in range(c+1, n)), Q(0)))/rows[r][c]
    assert [sum((v*w for v, w in zip(row, x)), Q(0)) for row in a] == b
    return x

systems = consistent = 0
for m, n in it.product(range(3), repeat=2):
    for flat in it.product((Q(-1), Q(0), Q(1, 2)), repeat=m*n):
        a = [list(flat[r*n:(r+1)*n]) for r in range(m)]
        for rhs in it.product((Q(-1), Q(0), Q(1)), repeat=m):
            b = list(rhs)
            value = bareiss(a, b, n)
            assert value == gauss(a, b, n)
            systems += 1
            consistent += value is not None
for m, n in [(2, 3), (3, 2), (4, 4)]:
    for seed in range(20):
        a = [[Q((seed+7*r+11*c+3*r*c) % 9-4, (r+c) % 3+1) for c in range(n)] for r in range(m)]
        b = [Q((seed+5*r) % 7-3, r % 3+1) for r in range(m)]
        value = bareiss(a, b, n)
        assert value == gauss(a, b, n)
        systems += 1
        consistent += value is not None

def interval_scale(pair, k):
    a, b = [k*x for x in pair]
    return min(a, b), max(a, b)

def interval_add(a, b):
    return a[0]+b[0], a[1]+b[1]

def neville(nodes, samples, at, interval=False):
    work, out = [], []
    for j, v in enumerate(samples):
        work.append(v)
        for i in reversed(range(j)):
            a, b, den = at-nodes[i], nodes[j]-at, nodes[j]-nodes[i]
            if interval:
                work[i] = interval_scale(interval_add(interval_scale(work[i+1], a), interval_scale(work[i], b)), 1/den)
            else:
                work[i] = (a*work[i+1]+b*work[i])/den
        out.append(work[0])
    return out

def weights(nodes, at):
    out = []
    for i, node in enumerate(nodes):
        v = Q(1)
        for j, other in enumerate(nodes):
            if i != j:
                v *= (at-other)/(node-other)
        out.append(v)
    return out

interval_cases = prefix_checks = 0
strict_enclosure = None
for n in range(1, 4):
    for nodes in it.permutations(map(Q, (-1, 0, 2)), n):
        for box in it.product(((Q(-1), Q(0)), (Q(0), Q(1)), (Q(1), Q(1))), repeat=n):
            for at in map(Q, (-2, 0, 1, 3)):
                enclosure = neville(nodes, box, at, True)
                for k in range(1, n+1):
                    w = weights(nodes[:k], at)
                    extrema = [sum((a*b for a, b in zip(w, corner)), Q(0)) for corner in it.product(*box[:k])]
                    tight = (min(extrema), max(extrema))
                    calculated = (Q(0), Q(0))
                    for pair, scalar in zip(box[:k], w):
                        calculated = interval_add(calculated, interval_scale(pair, scalar))
                    assert calculated == tight
                    assert enclosure[k-1][0] <= tight[0] <= tight[1] <= enclosure[k-1][1]
                    if enclosure[k-1] != tight and strict_enclosure is None:
                        strict_enclosure = {'nodes': list(nodes[:k]), 'at': at, 'samples': list(box[:k]), 'neville': enclosure[k-1], 'tight_lagrange': tight}
                    for corner in it.product(*box[:k]):
                        assert neville(nodes[:k], corner, at)[-1] == sum((a*b for a, b in zip(w, corner)), Q(0))
                    prefix_checks += 1
                interval_cases += 1
assert strict_enclosure is not None

def zadd(a, b):
    return a[0]+b[0], a[1]+b[1]
def zmul(a, b):
    return a[0]*b[0]-a[1]*b[1], a[0]*b[1]+a[1]*b[0]
def zconj(a):
    return a[0], -a[1]
def zneg(a):
    return -a[0], -a[1]
def fixed_sign(a, defective):
    if a[1]:
        return None
    if defective and a[0] == 17:
        return 2
    return (a[0] > 0)-(a[0] < 0)
def hermitian_sample_check(samples, defective):
    sign = lambda a: fixed_sign(a, defective)
    for a in samples:
        s = sign(a)
        if (s is None) != (zconj(a) != a):
            return False
        if s is not None and (s not in (-1, 0, 1) or (s == 0) != (a == (0, 0))):
            return False
    fixed = [a for a in samples if zconj(a) == a]
    for a in fixed:
        if sign(zneg(a)) != -sign(a):
            return False
    for a, b in it.product(fixed, repeat=2):
        if sign(a) == sign(b) == 1 and (sign(zadd(a, b)) != 1 or sign(zmul(a, b)) != 1):
            return False
    for a in samples:
        s = sign(zmul(a, zconj(a)))
        if s is None or s < 0 or (s == 0) != (a == (0, 0)):
            return False
    return True

samples = [(0, 0), (1, 0), (-1, 0), (4, 1)]
assert hermitian_sample_check(samples, False)
assert hermitian_sample_check(samples, True)
assert not hermitian_sample_check(samples+[(17, 0)], True)
assert fixed_sign(zmul((4, 1), (4, -1)), True) == 2

def mm(a, b):
    return [[sum((a[i][k]*b[k][j] for k in range(2)), Q(0)) for j in range(2)] for i in range(2)]
def madd(*xs):
    return [[sum((x[i][j] for x in xs), Q(0)) for j in range(2)] for i in range(2)]
def scale(a, c):
    return [[v*c for v in row] for row in a]

jet_cases = 0
for seed in range(64):
    ac = [[[Q((seed+5*i+7*j+11*k) % 7-3, k+1) for j in range(2)] for i in range(2)] for k in range(3)]
    bc = [[[Q((3*seed+7*i+2*j+5*k) % 5-2, 3-k) for j in range(2)] for i in range(2)] for k in range(3)]
    a = [ac[0], ac[1], scale(ac[2], 2)]
    b = [bc[0], bc[1], scale(bc[2], 2)]
    source = [mm(a[0], b[0]), madd(mm(a[1], b[0]), mm(a[0], b[1])), madd(mm(a[2], b[0]), scale(mm(a[1], b[1]), 2), mm(a[0], b[2]))]
    coefficients = [madd(*(mm(ac[i], bc[k-i]) for i in range(k+1))) for k in range(3)]
    assert source == [coefficients[0], coefficients[1], scale(coefficients[2], 2)]
    jet_cases += 1

# Pinned dependency addition computes the numerator sum before Ratio::new reduces.
operand = Q(3, 2)
raw_numerator = operand.numerator+operand.numerator
result = operand+operand
assert operand.numerator.bit_length() <= 2 and operand.denominator.bit_length() <= 2
assert result.numerator.bit_length() <= 2 and result.denominator.bit_length() <= 2
assert raw_numerator.bit_length() == 3
dep = Path('C:/Users/a343o/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/num-rational-0.4.2/src/lib.rs')
assert hashlib.sha256(dep.read_bytes()).hexdigest() == '6ce781e573521fb81f5ca47c1e6dab64e4eafc7f7d8e85094161fca5bb39c015'

out = {'status': 'finite_controls_pass', 'controls': [
    {'id': 'RLA-P22', 'rule': 'Hermitian sample checker accepts invalid sign2 on a computed norm', 'samples': samples, 'norm_of_4_plus_i': 17, 'defective_norm_sign': 2, 'source_predicate_accepts': True, 'adding_norm_to_samples_refuses': True, 'limits': 'All sampled values include0,1,-1 and a mixed complex value. Independent exact predicate model; universal trait satisfaction is not claimed.'},
    {'id': 'RLA-P23', 'rule': 'Neville scalar recurrence matches Lagrange; tight box image matches corners and lies inside propagated interval', 'interval_cases': interval_cases, 'prefix_checks': prefix_checks, 'strict_enclosure_example': strict_enclosure, 'limits': 'Permutations of up to3 distinct rational nodes, three interval choices and four evaluation points. No function remainder, asymptotic limit or native execution.'},
    {'id': 'RLA-P24', 'rule': 'Fraction-free row-cleared systems versus independent rational Gauss-Jordan, with original-equation replay', 'systems': systems, 'consistent': consistent, 'inconsistent': systems-consistent, 'exact_integer_divisions': divisions, 'limits': 'All0..2 shapes over a three-element rational entry set and three right-hand-side values, plus60 larger deterministic cases. No original solver or budget implementation executed.'},
    {'id': 'RLA-P25', 'rule': 'Matrix derivative jets versus independent polynomial convolution', 'jet_pairs': jet_cases, 'limits': 'Rational2x2 polynomial matrix curves. Proves neither analytic realizability of arbitrary abstract jets nor native execution.'},
    {'id': 'RLA-P26', 'rule': 'Input/result bit admission does not bound dependency arithmetic temporaries', 'max_bits': 2, 'operands': ['3/2', '3/2'], 'result': '3', 'transient_numerator': raw_numerator, 'transient_bits': raw_numerator.bit_length(), 'limits': 'Exact arithmetic plus pinned num-rational addition source; no native allocation measurement. Accepted exposed values remain within the declared bound.'}
], 'dependency_evidence': {'path': str(dep), 'sha256': hashlib.sha256(dep.read_bytes()).hexdigest(), 'reviewed_lines': [[753, 791]], 'full_source_read': False}, 'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'limits': ['Independent stdlib audit models only; original/native/provider/private benchmark not executed.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(out, indent=2, default=str)+'\n', encoding='utf8')
print(json.dumps(out, indent=2, default=str))
