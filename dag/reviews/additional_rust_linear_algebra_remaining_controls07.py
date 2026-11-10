"""Exact independent congruence/LDL certificate controls, no retained code imports."""
from fractions import Fraction as Q
import hashlib
import itertools
import json
from pathlib import Path

def ident(n):
    return [[Q(i == j) for j in range(n)] for i in range(n)]

def transpose(a):
    return [list(x) for x in zip(*a)]

def mm(a, b):
    return [[sum((x*y for x, y in zip(row, col)), Q(0)) for col in transpose(b)] for row in a]

def determinant(a):
    n = len(a)
    total = Q(0)
    for perm in itertools.permutations(range(n)):
        term = Q((-1)**sum(perm[i] > perm[j] for i in range(n) for j in range(i+1, n)))
        for i, j in enumerate(perm):
            term *= a[i][j]
        total += term
    return total

def principal_psd(a):
    n = len(a)
    return all(determinant([[a[i][j] for j in subset] for i in subset]) >= 0 for k in range(1, n+1) for subset in itertools.combinations(range(n), k))

def congruence(a):
    n = len(a)
    m, s = [r[:] for r in a], ident(n)
    def apply(e):
        nonlocal m, s
        m = mm(mm(transpose(e), m), e)
        s = mm(s, e)
    for k in range(n):
        if not m[k][k]:
            found = next((i for i in range(k+1, n) if m[i][i]), None)
            if found is None:
                off = next(((i, j) for i in range(k, n) for j in range(i+1, n) if m[i][j]), None)
                if off is None:
                    break
                found, j = off
                e = ident(n)
                e[j][found] = 1/m[found][j]
                apply(e)
            e = ident(n)
            e[k], e[found] = e[found], e[k]
            apply(e)
        for j in range(k+1, n):
            if m[k][j]:
                e = ident(n)
                e[k][j] = -m[k][j]/m[k][k]
                apply(e)
    assert mm(mm(transpose(s), a), s) == m
    assert all(m[i][j] == 0 for i in range(n) for j in range(n) if i != j)
    assert abs(determinant(s)) == 1
    return [m[i][i] for i in range(n)]

def ldl(a):
    n = len(a)
    l, d = ident(n), [Q(0)]*n
    def coupling(i, j):
        return sum((l[i][k]*d[k]*l[j][k] for k in range(j)), Q(0))
    def lift(w):
        v = [Q(0)]*n
        for i in reversed(range(n)):
            v[i] = w[i]-sum((l[k][i]*v[k] for k in range(i+1, n)), Q(0))
        return v
    for j in range(n):
        d[j] = a[j][j]-coupling(j, j)
        if d[j] < 0:
            w = [Q(i == j) for i in range(n)]
            return False, lift(w), 'negative'
        if d[j] == 0:
            for i in range(j+1, n):
                off = a[i][j]-coupling(i, j)
                if off:
                    diag = a[i][i]-coupling(i, i)
                    w = [Q(0)]*n
                    w[j], w[i] = -(diag+1)/(2*off), Q(1)
                    return False, lift(w), 'zero_nonzero_column'
        else:
            for i in range(j+1, n):
                l[i][j] = (a[i][j]-coupling(i, j))/d[j]
    diagonal = [[d[i] if i == j else Q(0) for j in range(n)] for i in range(n)]
    assert mm(mm(l, diagonal), transpose(l)) == a
    return True, None, 'positive_semidefinite'

cases = 0
branches = {}
for n in range(4):
    positions = list(itertools.combinations_with_replacement(range(n), 2))
    for values in itertools.product((-1, 0, 1), repeat=len(positions)):
        a = [[Q(0)]*n for _ in range(n)]
        for (i, j), v in zip(positions, values):
            a[i][j] = a[j][i] = Q(v)
        diag = congruence(a)
        accepted, witness, kind = ldl(a)
        assert accepted == principal_psd(a) == all(x >= 0 for x in diag)
        if witness is not None:
            value = sum((witness[i]*a[i][j]*witness[j] for i in range(n) for j in range(n)), Q(0))
            assert value < 0
            if kind == 'zero_nonzero_column':
                assert value == -1
        branches[kind] = branches.get(kind, 0)+1
        cases += 1

out = {'status': 'finite_controls_pass', 'controls': [
    {'id': 'RLA-P21', 'rule': 'Congruence certificate replay, unit determinant, LDL outcomes and negative witnesses against all-principal-minor PSD oracle', 'symmetric_matrices': cases, 'branches': branches, 'limits': 'Every symmetric rational matrix of dimension0..3 with entries -1,0,1. Congruence model uses complete elementary matrix products; all certificates replay against the intact input. Independent models, not native execution or generic Hermitian proof.'}
], 'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'limits': ['No original/native/provider/private benchmark execution.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf8')
print(json.dumps(out, indent=2))
