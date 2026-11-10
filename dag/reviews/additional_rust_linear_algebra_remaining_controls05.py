"""Independent finite polynomial/centralizer controls; no original modules imported."""
import hashlib
import itertools
import json
from pathlib import Path

def matrices(n, q):
    for flat in itertools.product(range(q), repeat=n*n):
        yield [list(flat[i*n:(i+1)*n]) for i in range(n)]

def ident(n):
    return [[int(i == j) for j in range(n)] for i in range(n)]

def mm(a, b, q):
    n = len(a)
    return [[sum(a[i][k]*b[k][j] for k in range(n)) % q for j in range(n)] for i in range(n)]

def peval(c, a, q):
    n = len(a)
    out = [[0]*n for _ in range(n)]
    for coef in reversed(c):
        out = mm(out, a, q)
        for i in range(n):
            out[i][i] = (out[i][i]+coef) % q
    return out

def zero(a):
    return all(v == 0 for row in a for v in row)

def berkowitz(a, q):
    n = len(a)
    poly = [1]
    for k in reversed(range(n)):
        s = n-k
        toe = [1, -a[k][k] % q]
        v = [a[k+1+i][k] for i in range(s-1)]
        for j in range(s-1):
            toe.append(-sum(a[k][k+1+i]*v[i] for i in range(s-1)) % q)
            if j+1 < s-1:
                v = [sum(a[k+1+i][k+1+h]*v[h] for h in range(s-1)) % q for i in range(s-1)]
        poly = [sum(toe[i-j]*poly[j] for j in range(min(s, i+1))) % q for i in range(s+1)]
    return poly[::-1]

def pmul(a, b, q):
    out = [0]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] = (out[i+j]+x*y) % q
    return out

def determinant_polynomial(a, q):
    n = len(a)
    out = [0]*(n+1)
    for perm in itertools.permutations(range(n)):
        sign = (-1)**sum(perm[i] > perm[j] for i in range(n) for j in range(i+1, n))
        term = [sign]
        for i, j in enumerate(perm):
            factor = [-a[i][j] % q, 1] if i == j else [-a[i][j] % q]
            term = pmul(term, factor, q)
        for i, x in enumerate(term):
            out[i] = (out[i]+x) % q
    return out

def rref(a, cols, q):
    a = [row[:] for row in a]
    pivot = []
    for col in range(cols):
        row = next((r for r in range(len(pivot), len(a)) if a[r][col]), None)
        if row is None:
            continue
        at = len(pivot)
        a[row], a[at] = a[at], a[row]
        inv = pow(a[at][col], -1, q)
        a[at] = [x*inv % q for x in a[at]]
        for r in range(len(a)):
            if r != at:
                factor = a[r][col]
                a[r] = [(x-factor*y) % q for x, y in zip(a[r], a[at])]
        pivot.append(col)
    return a, pivot

def minpoly(a, q):
    n = len(a)
    if not n:
        return [1]
    current = ident(n)
    cols = [sum(current, [])]
    for k in range(1, n+1):
        current = mm(current, a, q)
        flat = sum(current, [])
        rows = [[c[r] for c in cols]+[flat[r]] for r in range(n*n)]
        rr, pivots = rref(rows, k+1, q)
        if k not in pivots:
            return [-rr[i][k] % q for i in range(k)]+[1]
        cols.append(flat)
    raise AssertionError('Cayley-Hamilton dependency missing')

def exhaustive_minpoly(a, q):
    for k in range(len(a)+1):
        found = [list(c)+[1] for c in itertools.product(range(q), repeat=k) if zero(peval(list(c)+[1], a, q))]
        if found:
            assert len(found) == 1
            return found[0]
    raise AssertionError('No monic annihilator')

poly_cases = minimal_cases = 0
for q, ns in [(2, range(4)), (3, range(3)), (6, range(3))]:
    for n in ns:
        for a in matrices(n, q):
            char = berkowitz(a, q)
            assert char == determinant_polynomial(a, q)
            assert zero(peval(char, a, q))
            poly_cases += 1
            if q in (2, 3):
                assert minpoly(a, q) == exhaustive_minpoly(a, q)
                minimal_cases += 1

centralizer_cases = membership_checks = 0
for q in (2, 3):
    carrier = list(matrices(2, q))
    families = [()]+[(a,) for a in carrier]
    if q == 2:
        families += list(itertools.product(carrier, repeat=2))
    for family in families:
        rows = []
        for g in family:
            for i, j in itertools.product(range(2), repeat=2):
                rows.append([((g[l][j] if i == k else 0)-(g[i][k] if j == l else 0)) % q for k, l in itertools.product(range(2), repeat=2)])
        reduced, pivots = rref(rows, 4, q)
        free = [i for i in range(4) if i not in pivots]
        basis = []
        for f in free:
            v = [int(i == f) for i in range(4)]
            for r, c in enumerate(pivots):
                v[c] = -reduced[r][f] % q
            basis.append(v)
        span = {tuple(sum(c*v[i] for c, v in zip(coefs, basis)) % q for i in range(4)) for coefs in itertools.product(range(q), repeat=len(basis))}
        direct = {tuple(sum(x, [])) for x in carrier if all(mm(x, g, q) == mm(g, x, q) for g in family)}
        assert span == direct and len(span) == q**len(basis)
        centralizer_cases += 1
        membership_checks += len(carrier)

# Literal "rings of any kind" is wider than commutative rings. Use M2(F2)
# coefficient blocks a=E12,d=E21 in the diagonal2x2 block matrix.
a = [[0, 1], [0, 0]]
d = [[0, 0], [1, 0]]
ad, da = mm(a, d, 2), mm(d, a, 2)
comm = [[(ad[i][j]-da[i][j]) % 2 for j in range(2)] for i in range(2)]
assert comm == ident(2)
# Source recurrence returns constant ad, linear -(a+d), monic1;
# its Horner evaluation at the first diagonal entry is ad-da.
linear = [[-(a[i][j]+d[i][j]) % 2 for j in range(2)] for i in range(2)]
value = mm([[ (a[i][j]+linear[i][j]) % 2 for j in range(2)] for i in range(2)], a, 2)
value = [[(value[i][j]+ad[i][j]) % 2 for j in range(2)] for i in range(2)]
assert value == comm and not zero(value)

out = {
    'status': 'finite_controls_pass',
    'controls': [
        {'id': 'RLA-P16', 'rule': 'Berkowitz versus permutation determinant polynomials and Cayley-Hamilton; Krylov minimality versus exhaustive monic search', 'characteristic_cases': poly_cases, 'minimal_cases': minimal_cases, 'limits': 'All matrices through n=3 over F2 and through n=2 over F3 and Z/6; minimality only on F2/F3. Independent exact models, not retained Rust execution.'},
        {'id': 'RLA-P17', 'rule': 'Row-major commutator kernel spans exactly the direct finite centralizer', 'families': centralizer_cases, 'candidate_membership_checks': membership_checks, 'limits': 'Empty and singleton2x2 families over F2/F3, and all ordered pairs over F2; direct multiplication independently compared with full kernel span. No native execution or arbitrary-dimension proof.'},
        {'id': 'RLA-P18', 'rule': 'Noncommutative coefficient ring invalidates unrestricted ring wording', 'ring': '2x2 matrices over F2', 'a': a, 'd': d, 'first_diagonal_polynomial_value': value, 'limits': 'Exact finite counterexample to literal rings-of-any-kind extension, not to the lawful commutative-field contract or the commutative Z/6 example.'}
    ],
    'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'limits': ['Independent audit controls only; original/native/provider/private benchmark not executed.']
}
Path(__file__).with_suffix('.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf8')
print(json.dumps(out, indent=2))
