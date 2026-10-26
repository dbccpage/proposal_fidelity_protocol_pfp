"""Finite, exact checkers with explicit boundaries of what they establish.

Scope: Tower stage validation, lift proposals, down maps, and finite algebraic checkers.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from fractions import Fraction

from omega_engine_pfp.domain.tower.registry import (
    PROPOSAL_BLOCK_SIZE,
    PROPOSAL_START,
    STAGES,
)
from omega_engine_pfp.domain.tower.wire import (
    App,
    Atom,
    Diff,
    Node,
    WireError,
    application,
    emit_wire,
    opcode_and_args,
)

FIRST_STAGE = {
    0: 1, 1: 2, 2: 2, 3: 2, 4: 2, 5: 3,
    6: 5, 7: 5, 9: 5, 10: 5, 11: 6, 12: 6,
    13: 7, 14: 7, 26: 7, 15: 8, 16: 8, 17: 8,
    18: 8, 19: 8, 29: 8, 30: 8, 31: 8,
    20: 9, 21: 10, 22: 11, 23: 12, 24: 12,
    25: 13, 37: 13, 38: 14, 39: 15,
    40: 16, 41: 17, 42: 18, 43: 19, 44: 20, 45: 21,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise WireError(message)


def validate_stage(node: Node, level: int) -> str:
    """Return STRUCTURAL_ONLY, never mathematical/empirical certification."""
    require(0 <= level <= 100, "unknown stage")
    if isinstance(node, Diff):
        return "STRUCTURAL_ONLY"
    require(level >= 1, "MSS-0 admits only <>")
    if isinstance(node, Atom):
        require(level >= 2 or re.fullmatch(r"[01]+", node.word) is not None,
                "inactive MSS-1 data atom")
        return "STRUCTURAL_ONLY"
    code, args = opcode_and_args(node)
    if code in FIRST_STAGE:
        require(level >= FIRST_STAGE[code], "opcode not admitted at this stage")
        if code == 0:
            require(len(args) == 3 and isinstance(args[0], Diff)
                    and args[1:] == (Atom("0"), Atom("1")),
                    "first up-lift shape (later stage lifts use external contract)")
        elif code == 1:
            require(len(args) == 1 and isinstance(args[0], Atom), "vertex arity")
        elif code == 2:
            require(len(args) == 2 and all(isinstance(x, Atom) for x in args), "edge arity")
        elif code == 5:
            require(bool(args) and isinstance(args[0], Atom) and re.fullmatch(r"[01]+", args[0].word) is not None, "simplex dimension")
            verts = args[1:]
            require(len(verts) == int(args[0].word, 2) + 1 and all(isinstance(x, Atom) for x in verts)
                    and len(set(verts)) == len(verts), "simplex arity or distinctness")
        return "STRUCTURAL_ONLY"
    if code >= PROPOSAL_START:
        stage_no = 22 + (code - PROPOSAL_START) // PROPOSAL_BLOCK_SIZE
        stage = STAGES[stage_no] if stage_no <= 100 else None
        require(stage is not None and code == stage.primary_opcode and level >= stage_no,
                "unknown, reserved or premature extension opcode")
        require(args == tuple(Atom(x) for x in stage.generator_ids),
                "proposed constructor requires exact stage-local generator pair")
        return "PROPOSED_STRUCTURAL_ONLY"
    raise WireError("unknown global opcode in selected grammar profile")


@dataclass(frozen=True)
class LiftReceipt:
    source_stage: int
    target_stage: int
    source_wire: str
    proposed_pair: tuple[str, str]
    authority_effect: str = "None"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.source_stage,
            self.target_stage,
            self.source_wire,
            self.proposed_pair,
            self.authority_effect,
        ) == (
            other.source_stage,
            other.target_stage,
            other.source_wire,
            other.proposed_pair,
            other.authority_effect,
        )


def propose_lift(source: Node, from_stage: int) -> LiftReceipt:
    require(0 <= from_stage < 100, "lift stage range")
    validate_stage(source, from_stage)
    stage = STAGES[from_stage + 1]
    return LiftReceipt(from_stage, stage.level, emit_wire(source), stage.generator_ids)


def down_old(source: Node, receipt: LiftReceipt) -> Node:
    """Identity on old image; new terms have a typed non-descent."""
    require(receipt.target_stage == receipt.source_stage + 1
            and receipt.source_wire == emit_wire(source)
            and receipt.proposed_pair == STAGES[receipt.target_stage].generator_ids
            and receipt.authority_effect == "None", "lift receipt mismatch")
    validate_stage(source, receipt.source_stage)
    return source


def down_new(node: Node, receipt: LiftReceipt) -> None:
    code, _ = opcode_and_args(node)
    require(receipt.target_stage >= 22 and code == STAGES[receipt.target_stage].primary_opcode,
            "not a new constructor of this stage")
    raise WireError("NON_DESCENT: new structure has no asserted old meaning")


def proposed_stage_fixture(level: int) -> App:
    require(22 <= level <= 100, "no new extension constructor assigned")
    stage = STAGES[level]
    return application(stage.primary_opcode, *(Atom(x) for x in stage.generator_ids))


def check_orbit_table(table: Node) -> bool:
    code, args = opcode_and_args(table)
    require(code == 13 and len(args) >= 2, "orbit table needs a shift and orbit")
    shift_code, shift_args = opcode_and_args(args[0])
    require(shift_code == 26 and len(shift_args) == 2
            and all(isinstance(x, Atom) and re.fullmatch(r"[01]+", x.word) for x in shift_args),
            "missing binary shift specification")
    alphabet_size, block_length = (int(x.word, 2) for x in shift_args)
    require(alphabet_size > 0 and block_length > 0, "empty shift")
    orbits = set()
    for record in args[1:]:
        rec_code, children = opcode_and_args(record)
        require(rec_code == 14 and len(children) >= 3, "orbit shape")
        period, flag, *seq = children
        require(all(isinstance(x, Atom) and re.fullmatch(r"[01]+", x.word) for x in (period, flag, *seq)),
                "binary orbit fields")
        n = int(period.word, 2)
        require(n == len(seq) and n > 0 and flag.word in ("0", "1"), "orbit period")
        require(all(int(x.word, 2) < alphabet_size for x in seq), "orbit outside alphabet")
        require(block_length == 1, "B(k,m>1) requires a transition checker")
        words = tuple(x.word for x in seq)
        primitive = not any(n % d == 0 and all(words[i] == words[i % d] for i in range(n))
                            for d in range(1, n))
        require((flag.word == "1") == primitive, "primitive flag contradicts minimal period")
        canonical = min(tuple(words[i:] + words[:i]) for i in range(n))
        require(words == canonical and canonical not in orbits, "noncanonical or duplicate orbit")
        orbits.add(canonical)
    return True


def binary_rational(node: Node) -> Fraction:
    code, fields = opcode_and_args(node)
    require(code == 18 and len(fields) == 3
            and all(isinstance(x, Atom) and re.fullmatch(r"[01]+", x.word) for x in fields),
            "rational packet shape")
    sign, num, den = (int(x.word, 2) for x in fields)
    require(sign in (0, 1) and den > 0 and math.gcd(num, den) == 1
            and not (num == 0 and sign == 1), "noncanonical signed rational")
    return Fraction(-num if sign else num, den)


def check_l1_cycle(packet: Node, input_cochain: dict[tuple[str, str], Fraction],
                   weights: dict[tuple[str, str], Fraction]) -> str:
    """Independent finite cycle checker for Level-8 fixture, given external c,w."""
    code, fields = opcode_and_args(packet)
    require(code == 16 and len(fields) == 3, "harmonic receipt shape")
    cochain_id, edge_vector, receipt = fields
    require(isinstance(cochain_id, Atom), "cochain id")
    edge_code, edge_records = opcode_and_args(edge_vector)
    require(edge_code == 3 and len(edge_records) > 0, "edge vector")
    residual = {}
    for entry in edge_records:
        entry_code, entry_args = opcode_and_args(entry)
        require(entry_code == 2 and len(entry_args) == 3
                and all(isinstance(x, Atom) for x in entry_args[:2]), "edge cochain record")
        edge = (entry_args[0].word, entry_args[1].word)
        require(edge not in residual, "duplicate edge")
        residual[edge] = binary_rational(entry_args[2])
    require(residual.keys() == input_cochain.keys() == weights.keys()
            and all(type(v) is Fraction for v in input_cochain.values())
            and all(type(v) is Fraction and v > 0 for v in weights.values()),
            "missing exact input c or positive rational weights")
    potential: dict[str, Fraction] = {}
    for start, _ in residual:
        if start in potential:
            continue
        potential[start] = Fraction()
        changed = True
        while changed:
            changed = False
            for (u, v), rv in residual.items():
                difference = input_cochain[(u, v)] - rv
                if u in potential and v not in potential:
                    potential[v] = potential[u] + difference
                    changed = True
                elif v in potential and u not in potential:
                    potential[u] = potential[v] - difference
                    changed = True
    require(all(potential[v] - potential[u] == input_cochain[(u, v)] - rv
                for (u, v), rv in residual.items()), "residual is not c minus exact coboundary")
    rcode, rargs = opcode_and_args(receipt)
    require(rcode == 17 and len(rargs) == 3, "dual receipt shape")
    primal, dual = map(binary_rational, rargs[:2])
    fcode, frecords = opcode_and_args(rargs[2])
    require(fcode == 3, "flow vector shape")
    flow = {}
    divergence: dict[str, Fraction] = {}
    for entry in frecords:
        ecode, ea = opcode_and_args(entry)
        require(ecode == 19 and len(ea) == 3
                and all(isinstance(x, Atom) for x in ea[:2]), "flow entry")
        edge = (ea[0].word, ea[1].word)
        require(edge in residual and edge not in flow, "wrong or repeated flow edge")
        flow[edge] = binary_rational(ea[2])
        u, v = edge
        divergence[u] = divergence.get(u, Fraction()) - flow[edge]
        divergence[v] = divergence.get(v, Fraction()) + flow[edge]
    require(flow.keys() == residual.keys() and all(d == 0 for d in divergence.values()),
            "flow missing edge or not divergence free")
    require(all(abs(flow[e]) <= weights[e] for e in flow), "flow violates dual capacity")
    require(primal == sum((weights[e] * abs(value) for e, value in residual.items()), Fraction())
            and dual == sum((input_cochain[e] * flow[e] for e in flow), Fraction())
            and primal == dual, "recomputed primal-dual objectives disagree")
    return "FINITE_LOCAL_CHECKED"


def reverse_graph(node: Node) -> Node:
    """A scoped anti action on the Level-2 directed graph packet fragment."""
    if isinstance(node, (Diff, Atom)):
        return node
    code, args = opcode_and_args(node)
    if code == 1 and len(args) == 1:
        return node
    if code == 2 and len(args) == 2:
        return application(2, args[1], args[0])
    if code == 3:
        return application(3, *(reverse_graph(arg) for arg in args))
    if code == 4 and len(args) == 2 and isinstance(args[0], Diff):
        return application(4, Diff(), reverse_graph(args[1]))
    raise WireError("anti action outside graph fragment must be explicitly licensed")


def oriented_edge_boundary(node: Node) -> dict[str, int]:
    code, args = opcode_and_args(node)
    require(code == 2 and len(args) == 2 and all(isinstance(x, Atom) for x in args),
            "expected directed edge")
    u, v = args
    result: dict[str, int] = {}
    result[v.word] = result.get(v.word, 0) + 1
    result[u.word] = result.get(u.word, 0) - 1
    return {k: x for k, x in result.items() if x}


RATIONAL = re.compile(r"(0|-?[1-9][0-9]*)/([1-9][0-9]*)")


def rational(s: str) -> Fraction:
    require(isinstance(s, str) and RATIONAL.fullmatch(s) is not None, "invalid exact rational")
    value = Fraction(s)
    require(s == f"{value.numerator}/{value.denominator}", "noncanonical rational")
    return value


def format_rat(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def check_markov(rows: list[list[str]]) -> tuple[tuple[Fraction, ...], ...]:
    require(bool(rows) and all(isinstance(row, list) and len(row) == len(rows) for row in rows),
            "finite square Markov kernel required")
    parsed = tuple(tuple(rational(v) for v in row) for row in rows)
    require(all(all(x >= 0 for x in row) and sum(row) == 1 for row in parsed),
            "Markov row must be a probability distribution")
    return parsed


def check_bayes(prior: list[str], likelihood: list[str]) -> tuple[str, ...]:
    require(len(prior) > 0 and len(prior) == len(likelihood), "Bayes domain mismatch")
    p, lik = tuple(map(rational, prior)), tuple(map(rational, likelihood))
    require(sum(p) == 1 and all(x >= 0 for x in p + lik), "invalid probability")
    evidence = sum(x * y for x, y in zip(p, lik))
    require(evidence > 0 and all(x <= 1 for x in lik), "zero evidence or invalid likelihood")
    return tuple(format_rat(x * y / evidence) for x, y in zip(p, lik))


def check_spin_z(amplitudes: tuple[str, str]) -> dict[str, str]:
    """Exact real-rational subdomain in fixed |up>,|down> basis only."""
    require(len(amplitudes) == 2, "spin half needs two basis components")
    a, b = map(rational, amplitudes)
    require(a * a + b * b == 1, "state is not normalized")
    return {"up": format_rat(a * a), "down": format_rat(b * b),
            "expectation_z": format_rat(a * a - b * b), "authority_effect": "None"}


def check_operad_compose(outer: tuple[tuple[str, ...], str], slot: int,
                         inner: tuple[tuple[str, ...], str]) -> tuple[tuple[str, ...], str]:
    """Typed single-slot substitution; does not claim all operad axioms."""
    inputs, output = outer
    inner_inputs, inner_output = inner
    require(0 <= slot < len(inputs) and inputs[slot] == inner_output,
            "operad slot color mismatch")
    return (inputs[:slot] + inner_inputs + inputs[slot + 1:], output)


def check_finite_reindex(fiber: dict[str, set[str]], f: dict[str, str],
                         g: dict[str, str], term: str, source: str) -> str:
    """Check a two-arrow finite reindexing table, not a general fibration."""
    require(source in f and f[source] in g, "undefined base arrow")
    require(term in fiber.get(g[f[source]], set()), "term outside target fiber")
    return g[f[source]]


def glue_finite_sections(cover: list[set[str]], sections: list[dict[str, str]]) -> dict[str, str]:
    """Function-sheaf gluing on an explicitly finite cover."""
    require(len(cover) == len(sections) and len(cover) > 0, "cover data mismatch")
    merged: dict[str, str] = {}
    for part, section in zip(cover, sections):
        require(set(section) == part, "section has wrong domain")
        for key, value in section.items():
            require(key not in merged or merged[key] == value, "overlap disagreement")
            merged[key] = value
    return merged


def encode_sparse(basis: list[str], dense: list[str]) -> str:
    require(len(basis) == len(dense) and len(set(basis)) == len(basis)
            and all(re.fullmatch(r"[a-z0-9]+", x) for x in basis), "basis mismatch")
    values = [rational(x) for x in dense]
    body = json.dumps(basis, separators=(",", ":"), ensure_ascii=True).encode("utf8")
    payload = {"basis": basis, "basis_sha256": hashlib.sha256(body).hexdigest(),
               "entries": [[name, format_rat(value)] for name, value in zip(basis, values) if value]}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def decode_sparse(encoded: str) -> list[str]:
    try:
        payload = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise WireError("malformed sparse JSON") from exc
    require(isinstance(payload, dict) and set(payload) == {"basis", "basis_sha256", "entries"},
            "invalid sparse envelope")
    basis, entries = payload["basis"], payload["entries"]
    require(isinstance(basis, list) and isinstance(entries, list)
            and len(set(basis)) == len(basis)
            and all(isinstance(x, str) and re.fullmatch(r"[a-z0-9]+", x) for x in basis),
            "invalid basis")
    body = json.dumps(basis, separators=(",", ":"), ensure_ascii=True).encode("utf8")
    require(hashlib.sha256(body).hexdigest() == payload["basis_sha256"], "basis digest mismatch")
    values = {}
    for entry in entries:
        require(isinstance(entry, list) and len(entry) == 2 and isinstance(entry[0], str)
                and entry[0] in basis and entry[0] not in values, "duplicate or unknown sparse entry")
        value = rational(entry[1])
        require(value != 0, "sparse encoding must omit zero entries")
        values[entry[0]] = value
    output = [format_rat(values.get(key, Fraction(0))) for key in basis]
    require(encode_sparse(basis, output) == encoded, "noncanonical sparse encoding")
    return output
