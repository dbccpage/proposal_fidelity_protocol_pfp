"""Exact rational certificate replays and scalar-budget composition witnesses."""
from fractions import Fraction as Q
import hashlib
import itertools
import json
from pathlib import Path

def transpose(a):
    return [list(x) for x in zip(*a)]

def mm(a, b):
    return [[sum((x*y for x, y in zip(row, col)), Q(0)) for col in transpose(b)] for row in a]

def rref(a):
    a = [row[:] for row in a]
    pivots = []
    for c in range(len(a[0])):
        at = len(pivots)
        r = next((i for i in range(at, len(a)) if a[i][c]), None)
        if r is None:
            continue
        a[at], a[r] = a[r], a[at]
        pivot = a[at][c]
        a[at] = [v/pivot for v in a[at]]
        for i in range(len(a)):
            if i != at:
                factor = a[i][c]
                a[i] = [v-factor*w for v, w in zip(a[i], a[at])]
        pivots.append(c)
    return a, pivots

def inverse(a):
    n = len(a)
    rows = [row+[Q(i == j) for j in range(n)] for i, row in enumerate(a)]
    rr, pivots = rref(rows)
    assert pivots[:n] == list(range(n))
    return [row[n:] for row in rr]

def pseudoinverse(a):
    m, n = len(a), len(a[0])
    rr, pivots = rref(a)
    rank = len(pivots)
    if not rank:
        return [[Q(0)]*m for _ in range(n)], rank
    left = [[row[c] for c in pivots] for row in a]
    right = rr[:rank]
    assert mm(left, right) == a
    lt, rt = transpose(left), transpose(right)
    value = mm(mm(rt, inverse(mm(right, rt))), mm(inverse(mm(lt, left)), lt))
    return value, rank

cases = 0
ranks = {}
tampered_refusals = 0
for m, n in [(1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (3, 2)]:
    for flat in itertools.product((-1, 0, 1), repeat=m*n):
        a = [[Q(flat[i*n+j]) for j in range(n)] for i in range(m)]
        p, rank = pseudoinverse(a)
        ap, pa = mm(a, p), mm(p, a)
        assert mm(ap, a) == a and mm(pa, p) == p
        assert transpose(ap) == ap and transpose(pa) == pa
        # Replaying four equations against the intact input is an independent
        # mathematical oracle; a deliberately changed result must be rejected.
        bad = [row[:] for row in p]
        bad[0][0] += 1
        ab, ba = mm(a, bad), mm(bad, a)
        accepted = mm(ab, a) == a and mm(ba, bad) == bad and transpose(ab) == ab and transpose(ba) == ba
        assert not accepted
        tampered_refusals += 1
        cases += 1
        ranks[str(rank)] = ranks.get(str(rank), 0)+1

# Source-correspondent one-dimensional arithmetic call counts. These are
# finite models of actual branches, not multiplication of worst-case budgets.
calls = 0
def add(a, b):
    global calls
    calls += 1
    return a+b
def sub(a, b):
    global calls
    calls += 1
    return a-b
def mul(a, b):
    global calls
    calls += 1
    return a*b
def multiply_one(a, b, cap):
    assert 2 <= cap
    return add(0, mul(a, b)) if a else 0

cap = 4
assert 2*1+2*1*1*1 <= cap  # system preflight
equation = sub(add(0, 1), 1)
assert equation == 0
assert 1*(2*1*1+1+1) <= cap  # zero-row reduction preflight
# Zero system has no pivot arithmetic, kernel basis [1].
assert 4*1*1*1 <= cap  # replay preflight
assert multiply_one(1, 1, cap) == multiply_one(1, 1, cap)
commutant_calls = calls
assert commutant_calls == 6 > cap

calls = 0
cap = 2
cp = multiply_one(1, 1, cap)
pc = multiply_one(1, 1, cap)
assert multiply_one(cp, 1, cap) == 1
assert multiply_one(pc, 1, cap) == 1
# Identity conjugation of a rational does not invoke the counted operations.
penrose_calls = calls
assert penrose_calls == 8 > cap

out = {'status': 'finite_controls_pass', 'controls': [
    {'id': 'RLA-P19', 'rule': 'Exact rational full-rank factorization and all four Penrose identities, with tampered-result rejection', 'matrices': cases, 'rank_distribution': ranks, 'tampered_refusals': tampered_refusals, 'limits': 'All entries -1,0,1 in shapes1x1,1x2,2x1,2x2,2x3,3x2. Independent Fraction models; not native execution, arbitrary-field proof or HermitianOrdered admission validation.'},
    {'id': 'RLA-P20', 'rule': 'Separately reset scalar-call limits do not bound the composite call', 'commutant': {'n': 1, 'generator': [[1]], 'max_scalar_ops': 4, 'actual_modeled_calls': commutant_calls}, 'standalone_penrose_verifier': {'matrix': [[1]], 'proposed_inverse': [[1]], 'max_scalar_ops': 2, 'actual_modeled_calls': penrose_calls}, 'limits': 'Tiny source-correspondent branch model. The top-level pseudoinverse constructor has its own conservative whole-call preflight; this witness concerns the standalone verifier and commutant-basis function.'}
], 'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'limits': ['Original modules, Cargo/native/provider/private benchmark not executed.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf8')
print(json.dumps(out, indent=2))
