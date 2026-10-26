"""Small finite mode checks over existing domain capabilities. AuthorityEffect: None."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import permutations


EXECUTABLE_MODES = frozenset({1, 4, 5, 7, 8, 13, 19})


def _require(condition, code):
    if not condition:
        raise ValueError(code)


def _fields(value, names):
    _require(type(value) is dict and set(value) == set(names), "MODE_INPUT_FIELDS")


def _wire(value):
    if is_dataclass(value):
        return _wire(asdict(value))
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_wire(item) for item in value]
    if isinstance(value, dict):
        return {key: _wire(item) for key, item in value.items()}
    return value


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _glyph(data):
    from ..domain.tower.grammar import is_active_at_level, parse, serialize

    _fields(data, {"text", "level"})
    _require(type(data["text"]) is str and 0 < len(data["text"]) <= 4096, "GLYPH_TEXT_REQUIRED")
    _require(type(data["level"]) is int and data["level"] in (0, 1), "GLYPH_LEVEL_UNAVAILABLE")
    parsed = parse(data["text"])
    _require(serialize(parsed) == data["text"] and is_active_at_level(parsed, data["level"]), "GLYPH_ROUNDTRIP_OR_ALPHABET_FAILED")
    return dict(scope="MSS-N grammar and declared level-0/1 alphabet; no DDC trace claim", text=serialize(parsed))


def _prompt_guard(data):
    from omega_engine_operads.domain.prompt_hierarchy.evaluator import (
        DEFAULT_KEYWORD_PATTERNS, evaluate_prompt_gates,
    )
    from omega_engine_operads.domain.prompt_hierarchy.models import AntiOpBinding, PromptTreeNode, PromptUri

    _fields(data, {"prompt_uri", "anti_op", "payload", "harmful_control", "benign_control"})
    _require(data["anti_op"] in DEFAULT_KEYWORD_PATTERNS and DEFAULT_KEYWORD_PATTERNS[data["anti_op"]], "PROMPT_DETECTOR_UNAVAILABLE")
    node = PromptTreeNode(PromptUri.parse(data["prompt_uri"]), "PFP declared prompt guard",
                          anti_ops=(AntiOpBinding(data["anti_op"], "candidate", "KNOWN_PATHOLOGY"),))
    def check(text):
        _require(type(text) is str and 0 < len(text) <= 4096, "PROMPT_PAYLOAD_REQUIRED")
        return evaluate_prompt_gates(node, {"candidate": text})
    _require(check(data["harmful_control"]).status == "REFUSED" and check(data["benign_control"]).status == "PASS", "PROMPT_NEGATIVE_CONTROLS_FAILED")
    result = check(data["payload"])
    _require(result.status == "PASS", "KNOWN_PATHOLOGY")
    return dict(scope="Existing prompt-attached procedural anti-op; no empirical antibody activation",
                gate=_wire(result), instruction="Apply " + data["anti_op"] + " to this declared prompt payload.")


def _skills(data):
    from omega_engine_operads.contracts.typed_capabilities_v1 import canonical_bytes, parse_typed_capability
    from ..domain.tower.checks import check_operad_compose

    _fields(data, {"contracts", "instructions", "bindings", "root"})
    _require(type(data["contracts"]) is list and 1 <= len(data["contracts"]) <= 16, "SKILL_CONTRACTS_REQUIRED")
    _require(type(data["instructions"]) is dict and type(data["bindings"]) is list, "SKILL_RESOURCES_REQUIRED")
    wires = [parse_typed_capability(canonical_bytes(item)) for item in data["contracts"]]
    by_id = {wire.skill_id: wire for wire in wires}
    _require(len(by_id) == len(wires), "DUPLICATE_SKILL_ID")
    bodies = {}
    for wire in wires:
        body = data["instructions"].get(wire.instruction.path)
        _require(type(body) is str, "SKILL_INSTRUCTION_UNAVAILABLE")
        raw = body.encode("utf-8")
        _require(len(raw) == wire.instruction.byte_length and sha256(raw).hexdigest() == wire.instruction.sha256, "SKILL_RESOURCE_BINDING_MISMATCH")
        _require(set(wire.dependencies) <= set(by_id), "SKILL_DEPENDENCY_UNAVAILABLE")
        bodies[wire.skill_id] = body
    children, consumed = {}, set()
    for edge in data["bindings"]:
        _fields(edge, {"source", "target", "slot"})
        source, target, slot = edge["source"], edge["target"], edge["slot"]
        _require(source in by_id and target in by_id and type(slot) is int, "SKILL_BINDING_INVALID")
        _require(source not in consumed and (target, slot) not in children, "SKILL_OUTPUT_OR_SLOT_REUSED")
        consumed.add(source)
        children[target, slot] = source
    used, ordered = set(), []
    def port(value):
        return value.colour + ":" + value.wire_type
    def visit(identifier, active):
        _require(identifier in by_id and identifier not in active, "SKILL_CYCLE_OR_ROOT_INVALID")
        wire = by_id[identifier]
        signature = (tuple(port(p) for p in wire.inputs), port(wire.output))
        slots = sorted((slot for target, slot in children if target == identifier), reverse=True)
        for slot in slots:
            signature = check_operad_compose(signature, slot, visit(children[identifier, slot], active | {identifier}))
        used.add(identifier)
        ordered.append(bodies[identifier])
        return signature
    inputs, output = visit(data["root"], frozenset())
    _require(used == set(by_id), "UNUSED_SKILL_CONTRACT")
    return dict(scope="Finite typed instruction composition; Unadmitted, no execution authority",
                inputs=list(inputs), output=output, instruction="\n\n".join(ordered))


def _permutations(data):
    from ..domain.normal_forms.topology import verify_tsnf

    _fields(data, {"vertices", "edges", "faces", "table"})
    vertices = data["vertices"]
    _require(type(vertices) is list and 2 <= len(vertices) <= 5 and vertices == list(range(len(vertices))), "PERMUTATION_CARRIER_REQUIRED")
    _require(all(type(v) is int for v in vertices), "PERMUTATION_CARRIER_REQUIRED")
    edges, faces = data["edges"], data["faces"]
    for cells, arity in ((edges, 2), (faces, 3)):
        _require(type(cells) is list and all(type(c) is list and len(c) == arity and all(type(v) is int and v in vertices for v in c) for c in cells), "SIMPLEX_FIELDS")
    original = verify_tsnf(vertices, [tuple(e) for e in edges], [tuple(f) for f in faces])
    _require(original.is_tsnf, "PERMUTATION_COMPLEX_INVALID")
    table = []
    for image in permutations(vertices):
        renamed = lambda cells: sorted(tuple(sorted(image[v] for v in cell)) for cell in cells)
        checked = verify_tsnf(vertices, renamed(edges), renamed(faces))
        _require(checked.is_tsnf and checked.betti_numbers == original.betti_numbers, "PERMUTATION_BETTI_MISMATCH")
        parity = (-1) ** sum(image[i] > image[j] for i in vertices for j in vertices if i < j)
        table.append(dict(permutation=list(image), parity=parity, betti=checked.betti_numbers))
    _require(_json(data["table"]) == _json(table), "PERMUTATION_TABLE_MISMATCH")
    def swap(values, index):
        out = list(values)
        out[index], out[index+1] = out[index+1], out[index]
        return out
    for i in range(len(vertices)-2):
        _require(swap(swap(swap(vertices, i), i+1), i) == swap(swap(swap(vertices, i+1), i), i+1), "BRAID_RELATION_FAILED")
    return dict(scope="All permutations of this finite simplex complex, parity and adjacent braid relations", table=table)


def _involution(data):
    from ..domain.normal_forms.quantum_forms import verify_micnf

    _fields(data, {"sectors", "cancellation_ids", "involution_map"})
    sectors = data["sectors"]
    _require(type(sectors) is list and 0 < len(sectors) <= 256, "INVOLUTION_SECTORS_REQUIRED")
    identifiers = []
    for sector in sectors:
        _fields(sector, {"path_id", "weight", "sign"})
        _require(type(sector["path_id"]) is str and bool(sector["path_id"]), "INVOLUTION_ID_REQUIRED")
        _require(type(sector["weight"]) in (str, int) and Fraction(sector["weight"]) >= 0, "NON_EXACT_OR_NEGATIVE_WEIGHT")
        _require(type(sector["sign"]) is int and sector["sign"] in (-1, 1), "INVOLUTION_SIGN_INVALID")
        identifiers.append(sector["path_id"])
    _require(len(set(identifiers)) == len(identifiers), "DUPLICATE_INVOLUTION_SECTOR")
    _require(type(data["cancellation_ids"]) is list and len(data["cancellation_ids"]) == len(identifiers)
             and set(data["cancellation_ids"]) == set(identifiers), "INVOLUTION_COVERAGE_REQUIRED")
    _require(type(data["involution_map"]) is dict and set(data["involution_map"]) == set(identifiers), "INVOLUTION_MAP_REQUIRED")
    result = verify_micnf(sectors, data["cancellation_ids"], data["involution_map"])
    _require(result.terminal == "MeronExactCancellation", result.terminal)
    return dict(scope="Exact sign cancellation on every declared finite sector", result=_wire(result))


def _normal_forms(data):
    from ..domain.normal_forms.relational import (
        FunctionalDependency,
        RelationalSchema,
        chase_join_dependency_confluence,
        check_dependency_preservation,
        check_lossless_decomposition,
    )

    _fields(data, {"attributes", "dependencies", "components"})
    attributes = data["attributes"]
    _require(type(attributes) is list and 1 <= len(attributes) <= 6 and all(type(a) is str and a for a in attributes)
             and len(set(attributes)) == len(attributes), "RELATIONAL_ATTRIBUTES_REQUIRED")
    heading, dependencies = frozenset(attributes), []
    _require(type(data["dependencies"]) is list and 0 < len(data["dependencies"]) <= 6, "RELATIONAL_DEPENDENCIES_REQUIRED")
    for row in data["dependencies"]:
        _fields(row, {"left", "right"})
        _require(all(type(row[k]) is list and row[k] and all(type(a) is str and a in heading for a in row[k]) for k in ("left", "right")), "RELATIONAL_DEPENDENCY_INVALID")
        dependencies.append(FunctionalDependency(frozenset(row["left"]), frozenset(row["right"])))
    _require(len(set(dependencies)) == len(dependencies), "DUPLICATE_RELATIONAL_DEPENDENCY")
    components = data["components"]
    _require(type(components) is list and 2 <= len(components) <= 8 and all(type(c) is list and c and all(type(a) is str and a in heading for a in c) for c in components), "RELATIONAL_COMPONENTS_REQUIRED")
    parts = [frozenset(c) for c in components]
    _require(frozenset().union(*parts) == heading, "RELATIONAL_COVERAGE_REQUIRED")
    schema = RelationalSchema(heading, frozenset(dependencies))
    lossless, _ = check_lossless_decomposition(schema, parts)
    preserved, _ = check_dependency_preservation(schema, parts)
    confluent, orders, _ = chase_join_dependency_confluence(heading, dependencies, parts)
    _require(lossless and preserved and confluent, "LOSSY_NONCONFLUENT_OR_DEPENDENCY_LOSS")
    return dict(scope="Declared FD chase, lossless join and dependency preservation; no arbitrary-JD/6NF theorem",
                lossless=lossless, dependency_preserved=preserved, confluent=confluent, rule_orders_checked=orders)


def _distinction(data):
    from ..domain.decoding.antimorphism import ProtectedDistinction
    from ..domain.sn_tower.sn_core import S0Ground, S3Separation
    from ..domain.tower.grammar import Diff, parse

    _fields(data, {"ground", "marks"})
    _require(type(data["ground"]) is str and isinstance(parse(data["ground"]), Diff) and S0Ground().verify_inertia(), "GENESIS_GROUND_INVALID")
    marks = data["marks"]
    _require(type(marks) is list and len(marks) == 2 and all(type(m) is str and m for m in marks), "GENESIS_MARKS_REQUIRED")
    pair = ProtectedDistinction(*marks)
    _require(S3Separation().verify_separation(pair.state_a, pair.state_b), "GENESIS_DISTINCTION_COLLAPSED")
    return dict(scope="Existing finite two-mark separation model; no derivation of ontology from empty syntax",
                vertices=marks, directed_edge=[pair.state_a, pair.state_b])


def execute_mode_check(mode_id, data):
    """Run one deciding property, returning actual artifacts for the next stage prompt."""
    _require(mode_id in EXECUTABLE_MODES, "MODE_EXECUTOR_UNAVAILABLE")
    _require(type(data) is dict, "MODE_INPUT_REQUIRED")
    artifact = {1: _glyph, 4: _prompt_guard, 5: _skills, 7: _permutations,
                8: _involution, 13: _normal_forms, 19: _distinction}[mode_id](data)
    return dict(artifact, mode_id=mode_id, input_sha256=sha256(_json(data).encode("ascii")).hexdigest(), authority_effect="None")
