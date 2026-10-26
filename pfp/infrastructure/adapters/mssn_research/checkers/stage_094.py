"""Target checker of record for MSS-094, row 94 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 94): check both directions of handshake types. Negative
instance: connecting two output ports is rejected.

Input (closed): ``{"components": [[name, [[port, direction, type]]]],
"wires": [["component.port", "component.port"]]}`` with direction ``"in"``
or ``"out"``.

A wire joins exactly one output port to one input port carrying the same
message type; which end is the output is read from the port declarations, not
from the wire's order. A handshake between two components needs both
directions: if some wire carries messages from A to B, another must carry
messages from B to A. Each port is wired at most once.

Declared input class: finite component graphs with named ports and nominal
message types (type equality is name equality; no subtyping).

Clauses, decided in this order:

- C1 ``R094_UNKNOWN_PORT``: a wire names a component or port that is not
  declared, or wires one port twice;
- C2 ``R094_OUTPUT_TO_OUTPUT``: a wire joins two output ports (the level's
  negative);
- C3 ``R094_INPUT_TO_INPUT``: a wire joins two input ports;
- C4 ``R094_TYPE_MISMATCH``: a wire's two ports carry different types;
- C5 ``R094_ONE_WAY``: two components are wired in one direction only.
"""

STAGE = 94
ROW_SHA256 = "sha256:371cf4ebb5a835be4e74dd0bc093fdd78a55176e235d12e91ef75e3ce76cc3d3"
FIELDS = ("components", "wires")
CLAUSES = (
    ("C1", "R094_UNKNOWN_PORT"),
    ("C2", "R094_OUTPUT_TO_OUTPUT"),
    ("C3", "R094_INPUT_TO_INPUT"),
    ("C4", "R094_TYPE_MISMATCH"),
    ("C5", "R094_ONE_WAY"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "components": [
        ["client", [["req", "out", "Query"], ["resp", "in", "Answer"]]],
        ["server", [["req", "in", "Query"], ["resp", "out", "Answer"]]],
    ],
    "wires": [["client.req", "server.resp"], ["server.req", "client.resp"]],
}
OWN_NEGATIVE_CODE = "R094_OUTPUT_TO_OUTPUT"


def _decide(payload):
    ports = {}
    for component in _seq(payload["components"]):
        _seq(component, 2)
        name = _text(component[0])
        for port in _seq(component[1]):
            _seq(port, 3)
            _require(port[1] in ("in", "out"), "R_SCHEMA")
            key = name + "." + _text(port[0])
            _require(key not in ports, "R_SCHEMA")
            ports[key] = (name, port[1], _text(port[2]))
    wires = []
    for wire in _seq(payload["wires"]):
        _seq(wire, 2)
        wires.append((_text(wire[0]), _text(wire[1])))
    _require(wires, "R_SCHEMA")
    ends = [end for wire in wires for end in wire]
    _require(all(end in ports for end in ends) and len(set(ends)) == len(ends), "R094_UNKNOWN_PORT")
    for a, b in wires:
        _require(not (ports[a][1] == "out" and ports[b][1] == "out"), "R094_OUTPUT_TO_OUTPUT")
    for a, b in wires:
        _require(not (ports[a][1] == "in" and ports[b][1] == "in"), "R094_INPUT_TO_INPUT")
    for a, b in wires:
        _require(ports[a][2] == ports[b][2], "R094_TYPE_MISMATCH")
    flows = set()
    for a, b in wires:
        source, sink = (a, b) if ports[a][1] == "out" else (b, a)
        flows.add((ports[source][0], ports[sink][0]))
    for source, sink in flows:
        _require((sink, source) in flows, "R094_ONE_WAY")
