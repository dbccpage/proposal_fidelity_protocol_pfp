"""Additional finite catalog predicates; uses the existing native replay host."""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
from itertools import combinations, product
from pathlib import Path
import os
import subprocess

import sympy as sp


def genesis_replay(command: str) -> dict:
    from pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    root = Path(__file__).resolve().parents[3]
    configured = os.environ.get("CORE_GENESIS_REPLAY_BINARY")
    binary = Path(configured) if configured else root / "engine/crates_rs/target/debug/genesis_replay.exe"
    if not binary.is_file():
        raise SeedCheckFailure("NATIVE_GENESIS_REPLAY_UNAVAILABLE: build the existing genesis_replay binary")
    try:
        result = subprocess.run([str(binary)], input=command + "\n", text=True,
                                capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SeedCheckFailure("NATIVE_GENESIS_REPLAY_UNAVAILABLE: " + type(exc).__name__) from exc
    if result.returncode:
        return dict(status="REFUSED", error=result.stderr.strip())
    fields = result.stdout.strip().split("|")
    if len(fields) != 3:
        raise SeedCheckFailure("NATIVE_GENESIS_PROTOCOL_MISMATCH")
    return dict(status="ACCEPTED", portable_key=fields[0], contexts=int(fields[1]),
                observations=fields[2].split(",") if fields[2] else [])


def native_expected(seed_id: str) -> dict:
    from pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    source = Path(__file__).resolve().parents[3] / "engine/crates_rs/core_ooutwire_primitives/src/bin/genesis_replay.rs"
    try:
        source_digest = sha256(source.read_bytes()).hexdigest()
    except OSError as exc:
        raise SeedCheckFailure("NATIVE_GENESIS_SOURCE_UNAVAILABLE: " + type(exc).__name__) from exc
    if seed_id == "DEMO-N00":
        before, after = genesis_replay("events:"), genesis_replay("events:S:61")
        if before != after or before["observations"]:
            raise SeedCheckFailure("NATIVE_SUPPLY_INERTNESS_FAILED")
        return dict(source_sha256=source_digest, before=before, after=after,
                    inscription="<>", admitted_data=[], forced_successors=[])
    if seed_id == "DEMO-N01":
        bare = genesis_replay("events:S:61")
        admitted = genesis_replay("events:S:61;D:61")
        renamed = genesis_replay("events:S:7a;D:7a")
        if admitted != renamed or admitted["contexts"] != 0 or len(admitted["observations"]) != 1:
            raise SeedCheckFailure("NATIVE_RENAMING_OR_CARRIER_FAILED")
        return dict(source_sha256=source_digest, bare=bare, admitted=admitted, renamed=renamed,
                    form_count=0, instance_count=0, rule_count=0)
    events = ["D:61", "D:62", "S:61", "S:61", "F:1", "I:0:0"]
    states = [genesis_replay("events:" + ";".join(events[:i])) for i in range(len(events) + 1)]
    reversed_result = genesis_replay("events:D:61;D:62;I:0:0;F:1")
    if any(s["status"] != "ACCEPTED" for s in states) or reversed_result["status"] != "REFUSED":
        raise SeedCheckFailure("NATIVE_ORDER_CONTROL_FAILED")
    parent = sha256(b"genesis").hexdigest()
    tape = []
    for index, event in enumerate(events):
        digest = sha256((parent + "\n" + event).encode()).hexdigest()
        tape.append(dict(index=index, event=event, parent=parent, occurrence_digest=digest))
        parent = digest
    return dict(source_sha256=source_digest, tape=tape, states=states, reversed=reversed_result,
                bounded_prefix=states[:4], required_transition_count=6,
                completed_transition_count=3, bounded_terminal="UNKNOWN")


def core_expected(number: int) -> dict:
    from pfp.infrastructure.pilot_runners.seed_checks import boundary
    from pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    if number == 3:
        import importlib.util
        grammar = Path(__file__).resolve().parents[3] / "education/documentation/003_oemssn/grammar/mssn.ebnf"
        try:
            raw = grammar.read_bytes()
        except OSError as exc:
            raise SeedCheckFailure("GRAMMAR_SOURCE_UNAVAILABLE: " + type(exc).__name__) from exc
        recognizer = grammar.parents[2] / "004_oepfp/grammar/check_grammars.py"
        if not recognizer.is_file():
            raise SeedCheckFailure("GRAMMAR_RECOGNIZER_UNAVAILABLE")
        spec = importlib.util.spec_from_file_location("pfp_source_grammar_recognizer",recognizer)
        if spec is None or spec.loader is None:
            raise SeedCheckFailure("GRAMMAR_RECOGNIZER_UNAVAILABLE")
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        parser=module.Grammar(raw.decode("utf-8"))
        actual=[parser.accepts(name,"a0") for name in ("glyph_path","label_path","suffix_path")]
        if actual != [False,True,True]:
            raise SeedCheckFailure("GRAMMAR_PROFILE_RESULTS_CHANGED")
        productions = {}
        for name in ("glyph_path", "label_path", "suffix_path"):
            line = next((line for line in raw.decode("utf-8").splitlines() if line.strip().startswith(name + " ")), None)
            if line is None:
                raise SeedCheckFailure("GRAMMAR_PRODUCTION_UNAVAILABLE: " + name)
            productions[name] = line
        return dict(raw_source="a0", grammar_sha256=sha256(raw).hexdigest(), productions=productions,
                    experiments=dict(glyph_path={"status": "REFUSED", "reason": "MISSING_DIRECTION"},
                                     label_path={"status": "ACCEPTED", "word": "a0"},
                                     suffix_path={"status": "ACCEPTED", "label": "a", "suffix": "0"}),
                    vertex_identity="DECLARATION_REQUIRED", numeric_interpretation="DECLARATION_REQUIRED")
    if number == 11:
        bases = [list(combinations("abcd", degree + 1)) for degree in range(4)]
        sigma = dict(zip("abcd", "bcad"))
        matrices = []
        for basis in bases:
            matrix = sp.zeros(len(basis))
            for col, simplex in enumerate(basis):
                image = [sigma[v] for v in simplex]
                sign = (-1) ** sum(image[i] > image[j] for i in range(len(image)) for j in range(i+1, len(image)))
                matrix[basis.index(tuple(sorted(image))), col] = sign
            matrices.append(matrix)
        boundaries = [sp.Matrix(boundary(bases[k], bases[k-1])) for k in range(1, 4)]
        squares = [(boundaries[k-1]*matrices[k] - matrices[k-1]*boundaries[k-1]).tolist() for k in range(1, 4)]
        return dict(boundaries=[b.tolist() for b in boundaries], transported_basis_maps=[m.tolist() for m in matrices],
                    chain_map_defects=squares, double_boundaries=[(boundaries[k-1]*boundaries[k]).tolist() for k in (1,2)],
                    edge_counterexample={"source": ["a", "c"], "target": ["a", "b"], "sign": -1},
                    transformed_face={"source": ["a", "c", "d"], "target": ["a", "b", "d"], "sign": -1},
                    claim="EQUIVARIANT_COORDINATES_NOT_FIXED_COORDINATES")
    if number == 16:
        words = ["".join(w) for n in range(6) for w in product("ab", repeat=n)]
        traces = []
        for word in words:
            current, steps = word, []
            while True:
                position = next((i for i in range(len(current)-1) if current[i] == current[i+1]), None)
                if position is None:
                    break
                after = current[:position] + current[position+1:]
                steps.append(dict(before=current, position=position, rule=current[position]*2+"=>"+current[position],
                                  after=after, measure_before=len(current), measure_after=len(after)))
                current = after
            traces.append(dict(source=word, steps=steps, normal_form=current))
        overlaps = []
        for letter in "ab":
            source = letter * 3
            overlaps.append(dict(source=source, first_positions=[0,1], branches=[letter*2]*2, join=letter))
        tuples = list(product((0,1), repeat=3))
        rows = []
        def fd(relation, left, right):
            return all(any(a[i] != b[i] for i in left) or all(a[i] == b[i] for i in right)
                       for a in relation for b in relation)
        for mask in range(256):
            relation = [row for i,row in enumerate(tuples) if mask & (1 << i)]
            if not fd(relation,(0,1),(2,)) or not fd(relation,(2,),(1,)):
                continue
            bc = sorted({(b,c) for a,b,c in relation})
            ac = sorted({(a,c) for a,b,c in relation})
            join = sorted({(a,b,c) for a,c in ac for b,d in bc if c == d})
            if join != relation:
                raise SeedCheckFailure("RELATIONAL_JOIN_CONTROL_FAILED")
            rows.append(dict(relation=[list(r) for r in relation], bc=[list(r) for r in bc],
                             ac=[list(r) for r in ac], join=[list(r) for r in join]))
        # The two projections permit this join, which violates AB->C.
        return dict(string_profile="positioned-aa-bb", traces=traces, critical_overlaps=overlaps,
                    termination_measure="word_length", relational_profile="set_relation_binary_domains",
                    admissible_relations=rows, component_keys={"BC": ["C"], "AC": ["A","C"]},
                    dependency_counterexample=[[0,0,0],[0,0,1]],
                    preserved_dependencies=["C->B"], unpreserved_dependencies=["AB->C"],
                    finite_scope="binary attribute domains; words of length at most five",
                    universal_relational_claim="SEPARATE_PROOF_OBLIGATION")
    raise SeedCheckFailure("UNKNOWN_CORE_SEED")


def hodge_check(payload: dict) -> dict:
    from pfp.infrastructure.pilot_runners.seed_checks import compare
    from pfp.infrastructure.pilot_runners.seed_checks import vector
    from pfp.infrastructure.pilot_runners.seed_checks import wire
    from pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    if set(payload) != {"potential", "harmonic", "face_potential", "d0_adjoint", "d1_adjoint", "comparison"}:
        raise SeedCheckFailure("HODGE_WITNESS_FIELDS")
    d0 = sp.Matrix([[-1,1,0],[-1,0,1],[0,-1,1]])
    d1, m1 = sp.Matrix([[1,-1,1]]), sp.diag(1,2,3)
    a0, a1 = d0.T*m1, m1.inv()*d1.T*2
    p, h, q = (sp.Matrix(vector(payload[k], n)) for k,n in (("potential",3),("harmonic",3),("face_potential",1)))
    compare(payload["d0_adjoint"], [[Fraction(v) for v in row] for row in a0.tolist()])
    compare(payload["d1_adjoint"], [[Fraction(v) for v in row] for row in a1.tolist()])
    compare(payload["comparison"], "ORTHOGONAL_L2_IS_NOT_WEIGHTED_L1")
    parts = [d0*p,h,a1*q]
    if sum(parts,sp.zeros(3,1)) != sp.Matrix([1,4,2]) or d1*h != sp.zeros(1,1) or a0*h != sp.zeros(3,1):
        raise SeedCheckFailure("HODGE_RECONSTRUCTION_OR_HARMONIC_FAILED")
    pairings = [(parts[i].T*m1*parts[j])[0] for i,j in combinations(range(3),2)]
    if any(pairings):
        raise SeedCheckFailure("HODGE_ORTHOGONALITY_FAILED")
    return wire(dict(parts=[[Fraction(v) for v in part] for part in parts], orthogonality=[Fraction(v) for v in pairings]))


def channel_check(payload: dict) -> dict:
    from pfp.infrastructure.pilot_runners.seed_checks import compare
    from pfp.infrastructure.pilot_runners.seed_checks import rational
    from pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    from pfp.infrastructure.pilot_runners.seed_checks import wire
    required = {"kraus", "density", "marginal_first", "marginal_second", "output", "remote_after", "branch_index", "branch_probability", "branch_remote", "factor_order"}
    if set(payload) != required:
        raise SeedCheckFailure("CHANNEL_WITNESS_FIELDS")
    def matrix(rows, n):
        if type(rows) is not list or len(rows) != n or any(type(r) is not list or len(r) != n for r in rows):
            raise SeedCheckFailure("CHANNEL_MATRIX_SHAPE")
        values = []
        for row in rows:
            vals = []
            for z in row:
                if type(z) is not list or len(z) != 2:
                    raise SeedCheckFailure("GAUSSIAN_RATIONAL_PAIR_REQUIRED")
                vals.append(sp.Rational(rational(z[0]))+sp.I*sp.Rational(rational(z[1])))
            values.append(vals)
        return sp.Matrix(values)
    def encoded(m):
        return [[[Fraction(sp.re(z)),Fraction(sp.im(z))] for z in row] for row in m.tolist()]
    def remote(m):
        return sp.Matrix(2,2,lambda i,j:sum(m[2*a+i,2*a+j] for a in range(2)))
    if type(payload["kraus"]) is not list or not 1 <= len(payload["kraus"]) <= 8:
        raise SeedCheckFailure("KRAUS_POPULATION")
    ks = [matrix(k,2) for k in payload["kraus"]]
    if sum((k.H*k for k in ks),sp.zeros(2)) != sp.eye(2):
        raise SeedCheckFailure("CHANNEL_NOT_TRACE_PRESERVING")
    v=sp.Matrix([1,0,0,1]); rho=v*v.H/2
    branches=[sp.kronecker_product(k,sp.eye(2))*rho*sp.kronecker_product(k.H,sp.eye(2)) for k in ks]
    output=sum(branches,sp.zeros(4))
    index=payload["branch_index"]
    if type(index) is not int or not 0 <= index < len(ks):
        raise SeedCheckFailure("BRANCH_INDEX_INVALID")
    probability=sp.trace(branches[index])
    conditioned=encoded(remote(branches[index])/probability) if probability else "ZERO_BRANCH_REFUSED"
    expected=dict(density=encoded(rho), marginal_first=encoded(sp.eye(2)/2), marginal_second=encoded(sp.eye(2)/2),
                  output=encoded(output), remote_after=encoded(remote(output)), branch_probability=Fraction(probability),
                  branch_remote=conditioned, factor_order=["00","01","10","11"])
    compare({k:payload[k] for k in expected},expected)
    if remote(output) != sp.eye(2)/2:
        raise SeedCheckFailure("REMOTE_MARGINAL_CHANGED")
    return wire(expected)
