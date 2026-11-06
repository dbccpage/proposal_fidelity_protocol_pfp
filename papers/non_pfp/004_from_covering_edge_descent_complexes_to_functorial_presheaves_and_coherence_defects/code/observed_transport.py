"""Independent SymPy controls for the five connected PO-001 derivations.

The Python quotient selects independent original question rows, whereas Rust
uses RREF rows. The reports have the same kernel, not necessarily the same
coordinates. Exact tests and proofs specify the comparison. No physical
availability or native history interpretation follows from these matrices.
"""

from dataclasses import dataclass, field
from fractions import Fraction as Q

from certified_geometry import deficit, dihedral
from sympy import ImmutableMatrix as M
from sympy import eye, sqrt, zeros


def matrix(value, bound=32):
    value = M(value)
    if not 1 <= value.rows <= bound or not 1 <= value.cols <= bound:
        raise ValueError("nonempty bounded matrix required")
    if any(
        x.is_Rational is not True
        or abs(int(x.p)).bit_length() > 1024
        or int(x.q).bit_length() > 1024
        for x in value
    ):
        raise ValueError("bounded exact rational entries required")
    return value


@dataclass(frozen=True)
class LinearReport:
    questions: M
    basis: M = field(init=False)
    section: M = field(init=False)
    decoder: M = field(init=False)
    kernel: M = field(init=False)

    def __post_init__(self):
        q = matrix(self.questions)
        columns = q.T.columnspace()
        b = M.vstack(*(v.T for v in columns)) if columns else M(0, q.cols, [])
        if b.rows:
            _, pivots = b.rref()
            s = zeros(q.cols, b.rows)
            minor_inverse = b[:, list(pivots)].inv()
            for i, p in enumerate(pivots):
                s[p, :] = minor_inverse[i, :]
            s = M(s)
        else:
            s = M(q.cols, 0, [])
        decoder = q * s
        kernel = eye(q.cols) - s * b
        if b * s != eye(b.rows) or decoder * b != q or b * kernel != zeros(b.rows, q.cols):
            raise ValueError("quotient replay failed")
        for key, value in (
            ("questions", q),
            ("basis", b),
            ("section", s),
            ("decoder", decoder),
            ("kernel", kernel),
        ):
            object.__setattr__(self, key, M(value))

    def descend(self, target, operator):
        t = matrix(operator)
        if t.shape != (target.questions.cols, self.questions.cols):
            raise ValueError("endpoint shape mismatch")
        observed = target.basis * t
        if observed * self.kernel != zeros(target.basis.rows, self.questions.cols):
            raise ValueError("visible kernel leakage")
        d = observed * self.section
        if d * self.basis != observed:
            raise ValueError("descent replay failed")
        return M(d)


@dataclass(frozen=True)
class ObservedObject:
    identifier: str
    quotient: LinearReport


@dataclass(frozen=True)
class Arrow:
    source: ObservedObject
    target: ObservedObject
    operator: M
    report: M = field(init=False)

    def __post_init__(self):
        t = matrix(self.operator)
        d = self.source.quotient.descend(self.target.quotient, t)
        object.__setattr__(self, "operator", t)
        object.__setattr__(self, "report", d)

    @classmethod
    def identity(cls, obj):
        return cls(obj, obj, eye(obj.quotient.questions.cols))

    def after(self, earlier):
        if earlier.target != self.source:
            raise ValueError("carrier identity mismatch")
        return Arrow(earlier.source, self.target, self.operator * earlier.operator)


@dataclass(frozen=True)
class Cell:
    source: Arrow
    target: Arrow
    difference: M = field(init=False)

    def __post_init__(self):
        f, g = self.source, self.target
        if f.source != g.source or f.target != g.target:
            raise ValueError("2-cell endpoints differ")
        difference = g.operator - f.operator
        if f.target.quotient.questions * difference != zeros(
            f.target.quotient.questions.rows, f.source.quotient.questions.cols
        ):
            raise ValueError("visible comparison")
        object.__setattr__(self, "difference", difference)

    def then(self, later):
        if self.target != later.source:
            raise ValueError("vertical boundary mismatch")
        return Cell(self.source, later.target)

    def horizontal_after(self, earlier):
        return Cell(self.source.after(earlier.source), self.target.after(earlier.target))


def observed_compositors(connection, questions):
    c = connection.carrier
    if connection.degree != 1 or len(questions) != len(c.dimensions):
        raise ValueError("complete degree-one system required")
    objects = tuple(ObservedObject(str(x), LinearReport(q)) for x, q in enumerate(questions))
    if any(o.quotient.questions.cols != d for o, d in zip(objects, c.dimensions)):
        raise ValueError("fiber dimensions differ")
    arrows = {(x, z): Arrow(objects[z], objects[x], m) for (x, z), m in connection.values.items()}
    arrows.update({(x, x): Arrow.identity(o) for x, o in enumerate(objects)})
    cells = {
        (x, y, z): Cell(arrows[x, y].after(arrows[y, z]), arrows[x, z]) for x, y, z in c.chains(2)
    }
    return arrows, cells


def block_lift(carrier, x, z, operator):
    m = matrix(operator)
    if not 0 <= x < len(carrier.dimensions) or not 0 <= z < len(carrier.dimensions):
        raise ValueError("invalid corner")
    if m.shape != (carrier.dimensions[x], carrier.dimensions[z]):
        raise ValueError("invalid corner shape")
    out = zeros(sum(carrier.dimensions))
    row, col = sum(carrier.dimensions[:x]), sum(carrier.dimensions[:z])
    out[row : row + m.rows, col : col + m.cols] = m
    return M(out)


def l1_norm(m):
    return max((sum(abs(m[i, j]) for i in range(m.rows)) for j in range(m.cols)), default=0)


def path_product(path, dimension):
    result = eye(dimension)
    for m in path:
        result = m * result
    return M(result)


def path_error(first, second):
    if not 1 <= len(first) <= 16 or len(first) != len(second):
        raise ValueError("matching path lengths in 1..16 required")
    a, b = tuple(matrix(m, 16) for m in first), tuple(matrix(m, 16) for m in second)
    if any(
        x.shape != y.shape or (i and a[i - 1].rows != x.cols) for i, (x, y) in enumerate(zip(a, b))
    ):
        raise ValueError("path endpoints differ")
    residual = path_product(a, a[0].cols) - path_product(b, b[0].cols)
    terms, bound = [], 0
    for i in range(len(a)):
        prefix = path_product(a[i + 1 :], a[i].rows)
        suffix = path_product(b[:i], a[0].cols)
        local = a[i] - b[i]
        terms.append(prefix * local * suffix)
        bound += l1_norm(prefix) * l1_norm(local) * l1_norm(suffix)
    if sum(terms, zeros(residual.rows, residual.cols)) != residual or l1_norm(residual) > bound:
        raise ValueError("telescoping replay failed")
    return M(residual), tuple(terms), bound


def metric_holonomy(hinge, cycle, edges, eps):
    bounds = deficit(hinge, cycle, edges, eps)
    links, rotations = [], []
    for i in range(len(cycle)):
        ids = hinge + (cycle[i], cycle[(i + 1) % len(cycle)])
        squared = [
            [Q(0) if a == b else edges[tuple(sorted((ids[a], ids[b])))] for b in range(5)]
            for a in range(5)
        ]
        _, (aa, bb, ab) = dihedral(squared, eps)
        c = sqrt(M([ab * ab / (aa * bb)])[0]) * (-1 if ab < 0 else 1)
        s = sqrt(1 - c * c)
        if c.is_Rational is not True or s.is_Rational is not True or s <= 0:
            raise ValueError("outside rational rotation class")
        m = eye(4)
        m[2:, 2:] = M([[c, s], [-s, c]])
        links.append(M(m))
        rotations.append((c, s))
    return tuple(links), tuple(rotations), path_product(links, 4), bounds


def gauge_loop(links, frames, base):
    if len(frames) != len(links) or not 0 <= base < len(links):
        raise ValueError("frame/basepoint profile")
    f = tuple(matrix(m, 4) for m in frames)
    if any(m.shape != (4, 4) or m.T * m != eye(4) or m.det() != 1 for m in f):
        raise ValueError("SO4 frame required")
    transformed = tuple(f[(i + 1) % len(f)] * h * f[i].T for i, h in enumerate(links))
    order = tuple((base + i) % len(links) for i in range(len(links)))
    result = path_product([transformed[i] for i in order], 4)
    if result != f[base] * path_product([links[i] for i in order], 4) * f[base].T:
        raise ValueError("gauge replay failed")
    return result
