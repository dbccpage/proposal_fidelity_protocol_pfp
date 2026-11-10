"""Quiz 16: exact checks on one declared three-vertex binary cycle.

This is a finite educational experiment, not the engine's general solver.
No network calls. A checked proposal does not authorize applying a repair.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from uuid import uuid4

PILOT_ID = "pilot_0000026"
EDGE_IDS = ("ab", "bc", "ca")
CASE_IDS = ("quiz16.1", "quiz16.2", "quiz16.3", "quiz16.4")
MAX_INPUT_BYTES = 65536


class InvalidInput(ValueError):
    """The submitted object does not match this pilot's finite contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidInput(message)


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def bit(value: object) -> bool:
    return type(value) is int and value in (0, 1)


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise InvalidInput(f"Non-finite JSON number: {value}")


def read_document(path: Path) -> tuple[object, bytes]:
    with path.open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    require(len(raw) <= MAX_INPUT_BYTES, "JSON document exceeds the 65536-byte limit")
    value = json.loads(
        raw.decode("utf-8"), object_pairs_hook=unique_object, parse_constant=reject_constant
    )
    return value, raw


@dataclass(frozen=True)
class Edge:
    edge_id: str
    source: str
    target: str
    rhs: int


@dataclass(frozen=True)
class Problem:
    vertices: tuple[str, ...]
    edges: tuple[Edge, ...]

    def __post_init__(self) -> None:
        require(type(self.vertices) is tuple and len(self.vertices) == 3, "Need three vertices")
        require(
            all(type(v) is str and v and v.strip() == v for v in self.vertices),
            "Vertex labels must be nonempty strings without surrounding whitespace",
        )
        require(len(set(self.vertices)) == 3, "Vertex labels must be distinct")
        require(type(self.edges) is tuple and len(self.edges) == 3, "Need all three edges")
        require(all(type(e) is Edge for e in self.edges), "Edges must be typed")
        require(all(type(e.edge_id) is str for e in self.edges), "Edge identities must be strings")
        require(
            sorted(e.edge_id for e in self.edges) == sorted(EDGE_IDS),
            "Checked edge identities must equal the declared identities exactly",
        )
        pairs = dict(zip(
            EDGE_IDS, zip(self.vertices, self.vertices[1:] + self.vertices[:1], strict=True), strict=True
        ))
        for edge in self.edges:
            require(
                (edge.source, edge.target) == pairs[edge.edge_id],
                "An edge endpoint differs from the declared oriented cycle",
            )
            require(bit(edge.rhs), "Every right-hand side must be the integer 0 or 1")

    def payload(self) -> dict:
        return {
            "vertices": list(self.vertices),
            "edges": [
                {"edge_id": e.edge_id, "source": e.source, "target": e.target, "rhs": e.rhs}
                for e in sorted(self.edges, key=lambda edge: EDGE_IDS.index(edge.edge_id))
            ],
        }


def parse_problem(value: object) -> Problem:
    require(type(value) is dict and set(value) == {"vertices", "edges"}, "Problem fields differ")
    require(type(value["vertices"]) is list, "vertices must be an array")
    require(type(value["edges"]) is list, "edges must be an array")
    edges = []
    for row in value["edges"]:
        require(
            type(row) is dict and set(row) == {"edge_id", "source", "target", "rhs"},
            "Edge fields differ",
        )
        require(type(row["edge_id"]) is str, "edge_id must be a string")
        edges.append(Edge(**row))
    return Problem(tuple(value["vertices"]), tuple(edges))


def default_problem() -> Problem:
    return Problem(
        ("a", "b", "c"),
        (Edge("ab", "a", "b", 1), Edge("bc", "b", "c", 1), Edge("ca", "c", "a", 1)),
    )


def assignment_valid(problem: Problem, values: dict[str, int]) -> bool:
    require(type(values) is dict and set(values) == set(problem.vertices), "Assignment variables differ")
    require(all(bit(v) for v in values.values()), "Assignment values must be integer bits")
    return all(
        values[edge.source] ^ values[edge.target] == edge.rhs
        for edge in problem.edges
    )


def solutions(problem: Problem, pin: dict[str, int] | None = None) -> list[dict[str, int]]:
    if pin is None:
        pin = {}
    require(type(pin) is dict and set(pin) <= set(problem.vertices), "Pin variables differ")
    require(all(bit(v) for v in pin.values()), "Pin values must be integer bits")
    found = []
    for vector in product((0, 1), repeat=3):
        assignment = dict(zip(problem.vertices, vector, strict=True))
        if assignment_valid(problem, assignment) and all(assignment[k] == v for k, v in pin.items()):
            found.append(assignment)
    return found


def cycle_sum(problem: Problem) -> int:
    return sum(edge.rhs for edge in problem.edges) % 2


def relabel(problem: Problem, labels: dict[str, str]) -> Problem:
    require(type(labels) is dict and set(labels) == set(problem.vertices), "Relabeling domain differs")
    return Problem(
        tuple(labels[v] for v in problem.vertices),
        tuple(Edge(e.edge_id, labels[e.source], labels[e.target], e.rhs) for e in problem.edges),
    )


def minimum_repairs(problem: Problem) -> dict:
    original = solutions(problem)
    if original:
        return {"cost": 0, "repairs": [{"changed_edges": [], "solutions": original}]}
    repairs = []
    for edge_id in EDGE_IDS:
        changed = Problem(
            problem.vertices,
            tuple(
                Edge(e.edge_id, e.source, e.target, e.rhs ^ int(e.edge_id == edge_id))
                for e in problem.edges
            ),
        )
        repairs.append({
            "changed_edges": [edge_id],
            "solutions": solutions(changed),
            "solutions_with_first_vertex_zero": solutions(changed, {problem.vertices[0]: 0}),
        })
    return {"cost": 1, "repairs": repairs}


def analyze(problem: Problem) -> dict:
    witnesses = []
    overlap_values = {v: set() for v in problem.vertices}
    for edge in sorted(problem.edges, key=lambda e: EDGE_IDS.index(e.edge_id)):
        values = {edge.source: 0, edge.target: edge.rhs}
        witnesses.append({"edge_id": edge.edge_id, "assignment": values})
        for vertex, value in values.items():
            overlap_values[vertex].add(value)
    renamed = relabel(
        problem, dict(zip(problem.vertices, problem.vertices[1:] + problem.vertices[:1], strict=True))
    )
    return {
        "pilot_id": PILOT_ID,
        "kind": "NO_LLM",
        "cost_usd": "0",
        "authority_effect": "None",
        "problem": problem.payload(),
        "problem_sha256": digest(problem.payload()),
        "checked_edge_ids": list(EDGE_IDS),
        "cases": {
            "quiz16.1": {
                "local_witnesses": witnesses,
                "conflicting_vertices": sorted(v for v, values in overlap_values.items() if len(values) > 1),
            },
            "quiz16.2": {
                "cycle_sum": cycle_sum(problem),
                "summed_lhs_coefficients": {
                    v: sum(int(e.source == v) + int(e.target == v) for e in problem.edges) % 2
                    for v in problem.vertices
                },
                "assignments_checked": 8,
                "solutions": solutions(problem),
            },
            "quiz16.3": minimum_repairs(problem),
            "quiz16.4": {
                "renamed_problem": renamed.payload(),
                "cycle_sum": cycle_sum(renamed),
                "solution_count": len(solutions(renamed)),
                "is_repair": False,
            },
        },
    }


def grade(problem: Problem, proposal: object) -> bool:
    """Compare the whole answer to host recomputation; bool is not interchangeable with int."""
    return canonical(proposal) == canonical(analyze(problem))


def write_run(
    output_root: Path, report: dict, accepted: bool | None, *,
    input_bytes: bytes | None = None, proposal_bytes: bytes | None = None,
) -> Path:
    run_dir = output_root / uuid4().hex
    run_dir.mkdir(parents=True, exist_ok=False)
    result = {"report": report, "proposal_accepted": accepted}
    original_input = input_bytes if input_bytes is not None else canonical(report["problem"]).encode("ascii")
    (run_dir / "input.json").write_bytes(original_input)
    if proposal_bytes is not None:
        (run_dir / "proposal.json").write_bytes(proposal_bytes)
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    receipt = {
        "pilot_id": PILOT_ID,
        "status": "COMPUTED" if accepted is None else ("ACCEPTED" if accepted else "REJECTED"),
        "code_sha256": code_hash,
        "result_sha256": digest(result),
        "input_sha256": hashlib.sha256(original_input).hexdigest(),
        "input_origin": "submitted" if input_bytes is not None else "default_fixture",
        "proposal_sha256": hashlib.sha256(proposal_bytes).hexdigest() if proposal_bytes is not None else None,
        "network_calls": 0,
        "cost_usd": "0",
    }
    for name, payload in (("result.json", result), ("receipt.json", receipt)):
        with (run_dir / name).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n")
    with (run_dir / "summary.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            f"# {PILOT_ID}\n\nStatus: {receipt['status']}.\n\n"
            f"Checked edges: {', '.join(report['checked_edge_ids'])}. "
            f"Global assignments: {len(report['cases']['quiz16.2']['solutions'])}. "
            f"Minimum repair cost: {report['cases']['quiz16.3']['cost']}.\n\n"
            f"Result SHA-256: {receipt['result_sha256']}.\n\n"
            "Finite fixture only. No model call or repair application.\n"
        )
    return run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON problem; defaults to the original odd cycle")
    parser.add_argument("--proposal", type=Path, help="JSON candidate report to grade against the problem")
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID,
    )
    args = parser.parse_args(argv)
    try:
        input_value, input_bytes = read_document(args.input) if args.input else (None, None)
        problem = parse_problem(input_value) if args.input else default_problem()
        report = analyze(problem)
        proposal, proposal_bytes = read_document(args.proposal) if args.proposal else (None, None)
        accepted = grade(problem, proposal) if args.proposal else None
        folder = write_run(args.output_dir, report, accepted, input_bytes=input_bytes, proposal_bytes=proposal_bytes)
    except (InvalidInput, OSError, ValueError, TypeError, RecursionError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": "COMPUTED" if accepted is None else ("ACCEPTED" if accepted else "REJECTED"), "output": str(folder)}, ensure_ascii=True))
    return 1 if accepted is False else 0


if __name__ == "__main__":
    sys.exit(main())
