"""Bounded independent exact-field and representation controls; no Rust execution."""
from fractions import Fraction
from itertools import product
from pathlib import Path
import hashlib
import json

def reduce_grid(a, width, p):
    grid = [list(row) for row in a]
    pivots = []
    calls = 0
    for col in range(width):
        row = len(pivots)
        if row == len(grid):
            break
        found = next((i for i in range(row, len(grid)) if grid[i][col]), None)
        if found is None:
            continue
        grid[row], grid[found] = grid[found], grid[row]
        inv = pow(grid[row][col], -1, p)
        calls += 1
        for c in range(col, width):
            grid[row][c] = grid[row][c] * inv % p
            calls += 1
        for i in range(len(grid)):
            if i == row or not grid[i][col]:
                continue
            factor = grid[i][col]
            for c in range(col, width):
                grid[i][c] = (grid[i][c] - factor * grid[row][c]) % p
                calls += 2
        pivots.append(col)
    return grid, pivots, calls

def reduction_bound(m, n):
    return min(m, n) * (2 * m * n + n + 1)

def mv(a, x, p):
    return tuple(sum(v * w for v, w in zip(row, x)) % p for row in a)

def solve(a, b, p):
    m = len(a)
    n = len(a[0]) if a else 0
    grid, pivots, calls = reduce_grid([row + [v] for row, v in zip(a, b)], n + 1, p)
    assert calls <= reduction_bound(m, n + 1)
    if n in pivots:
        dual = [[a[i][j] for i in range(m)] + [0] for j in range(n)] + [list(b) + [1]]
        reduced, dp, dcalls = reduce_grid(dual, m + 1, p)
        assert m not in dp and dcalls <= reduction_bound(n + 1, m + 1)
        y = [0] * m
        for i, pivot in enumerate(dp):
            y[pivot] = reduced[i][m]
        assert all(sum(y[i] * a[i][j] for i in range(m)) % p == 0 for j in range(n))
        assert sum(v * w for v, w in zip(y, b)) % p != 0
        return False, None
    x = [0] * n
    for i, pivot in enumerate(pivots):
        x[pivot] = grid[i][n]
    assert mv(a, x, p) == tuple(b)
    kernel = []
    for free in range(n):
        if free not in pivots:
            v = [int(j == free) for j in range(n)]
            for i, pivot in enumerate(pivots):
                v[pivot] = -grid[i][free] % p
            assert mv(a, v, p) == (0,) * m
            kernel.append(v)
    return True, (x, kernel)

matrices = systems = consistent = refusals = 0
for p in (2, 3):
    vectors = list(product(range(p), repeat=2))
    for values in product(range(p), repeat=4):
        a = [list(values[:2]), list(values[2:])]
        matrices += 1
        for b in vectors:
            accepted, witness = solve(a, b, p)
            actual = {x for x in vectors if mv(a, x, p) == b}
            assert accepted == bool(actual)
            if accepted:
                x, kernel = witness
                generated = {
                    tuple((x[j] + sum(t[i] * kernel[i][j] for i in range(len(kernel)))) % p for j in range(2))
                    for t in product(range(p), repeat=len(kernel))
                }
                assert generated == actual
                consistent += 1
            else:
                refusals += 1
            systems += 1

# Mirror only the public loop/control shape, without calling source code.
def extract_row(rows, cols, index):
    out = []
    for c in range(cols):
        if index >= rows:
            raise IndexError
        out.append(0)
    return out

def extract_column(rows, cols, index):
    out = []
    for r in range(rows):
        if index >= cols:
            raise IndexError
        out.append(0)
    return out

assert extract_row(2, 0, 99) == []
assert extract_column(0, 2, 99) == []
original_shape = (0, 3)
rows = []
reconstructed_shape = (len(rows), len(rows[0]) if rows else 0)
assert reconstructed_shape == (0, 0) != original_shape

numerator, denominator = 1 << 63, 2
value = Fraction(numerator, denominator)
assert value == 1 << 62
raw_pair_fits = -(1 << 63) <= numerator < 1 << 63 and -(1 << 63) <= denominator < 1 << 63
reduced_pair_fits = -(1 << 63) <= value.numerator < 1 << 63 and 0 < value.denominator < 1 << 63
assert not raw_pair_fits and reduced_pair_fits

dependency = Path('C:/Users/a343o/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/num-rational-0.4.2/src/lib.rs')
root = Path(__file__).resolve().parents[2]
out = {
    'status': 'finite_controls_pass',
    'controls': [
        {'id': 'RLA-P13', 'rule': 'Exact-field solve and inconsistency certificates against exhaustive finite-field solution sets', 'fields': [2, 3], 'matrices': matrices, 'systems': systems, 'consistent': consistent, 'refusals': refusals, 'limits': 'Every2x2 matrix and right-hand side over F2/F3; particular-plus-kernel sets compared with exhaustive vector search. Independent model, not native execution or arbitrary-field proof.'},
        {'id': 'RLA-P14', 'rule': 'Empty-axis extraction and row-list shape loss', 'row_shape': [2, 0], 'row_index': 99, 'column_shape': [0, 2], 'column_index': 99, 'both_source_loop_models_return': [], 'row_list_original_shape': original_shape, 'row_list_reconstructed_shape': reconstructed_shape, 'limits': 'Tiny independent control-flow/shape model; no out-of-bounds native memory access is asserted.'},
        {'id': 'RLA-P15', 'rule': 'Narrowing unreduced rational checks raw pair instead of mathematical representability', 'raw': [numerator, denominator], 'reduced': [value.numerator, value.denominator], 'raw_pair_fits_i64': raw_pair_fits, 'reduced_pair_fits_i64': reduced_pair_fits, 'limits': 'Exact arithmetic plus source/dependency inspection. Canonical nonzero-denominator inputs avoid this mismatch. No native panic or conversion was executed.'}
    ],
    'dependency_evidence': {'path': str(dependency), 'sha256': hashlib.sha256(dependency.read_bytes()).hexdigest(), 'reviewed_lines': [[73, 111], [132, 166]], 'full_source_read': False, 'assessment': 'Only the raw constructor, normal constructor and reduction preconditions were inspected. new_raw preserves arbitrary numerator/denominator; new/reduce explicitly panic on zero denominator.', 'lock_path': 'code/rust/Cargo.lock', 'lock_sha256': hashlib.sha256((root / 'code/rust/Cargo.lock').read_bytes()).hexdigest(), 'lock_reviewed_lines': [[1632, 1640]], 'lock_full_source_read': False},
    'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'limits': ['No original module, native tool, provider or private benchmark executed; external dependency excerpts earn no whole-file corpus credit.']
}
Path(__file__).with_suffix('.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf8')
print(json.dumps(out, indent=2))
