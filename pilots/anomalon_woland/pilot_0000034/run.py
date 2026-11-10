"""Quiz09: tape shape, recorded-state equality and a small exact replay model.

NO_LLM. Local teaching rules, not equivalence to the broader DDC runtime.
Task permissions are supplied scope, not authenticated external authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from uuid import uuid4

PILOT_ID = "pilot_0000034"
PROFILE = "quiz09-prefix-vector-replay-v1"
MAX_BYTES = 65536
MAX_STEPS = 64
LETTERS = ("C", "R", "E", "I", "LIFT", "D", "M", "T")
REASONS = ("UNREPAIRABLE_TAIL", "MISSING_PERMISSION", "BUDGET_EXHAUSTED", "UNVERIFIED_INPUT")
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID


class InvalidInput(ValueError):
    """A proposal does not satisfy the declared local contract."""


def require(condition, message):
    if not condition:
        raise InvalidInput(message)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Unexpected fields")


def integer(value):
    require(type(value) is int and abs(value) <= 10**6, "Bounded integer required")
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def hash_value(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "Expected lowercase SHA256")
    return value


def state(value):
    fields(value, ("values", "repair_rank"))
    raw = value["values"]
    require(type(raw) is list and 1 <= len(raw) <= 8, "State needs 1..8 coordinates")
    coordinates = tuple(integer(v) for v in raw)
    rank = integer(value["repair_rank"])
    require(0 <= rank <= len(coordinates), "Repair rank outside carrier")
    return coordinates, rank


def state_document(coordinates, rank):
    return {"values": list(coordinates), "repair_rank": rank}


def measurement(value):
    coordinates, rank = state(value)
    return {"prefix_potential": list(coordinates[:rank]),
            "projected_tail": [0] * rank + list(coordinates[rank:]),
            "unrepairable_l1": sum(abs(v) for v in coordinates[rank:]),
            "total_l1": sum(abs(v) for v in coordinates)}


def valid_shape(tape):
    require(type(tape) is list and len(tape) <= MAX_STEPS, "Expected bounded event list")
    require(all(type(v) is str for v in tape), "Every label must be a string")
    if not tape or tape[0] != "C" or tape[-1] != "T":
        return False
    for index, event in enumerate(tape):
        if event not in LETTERS:
            return False
        if event == "T" and index != len(tape) - 1:
            return False
        if event == "M" and tape[index + 1] != "T":
            return False
    return True


def shape_report(wire):
    require(type(wire) is str and len(wire) <= 512, "Expected wire of at most 512 characters")
    matched = re.fullmatch(r"tape<([a-z]+(?:,[a-z]+)*)>", wire)
    accepted = False
    if matched:
        accepted = valid_shape([token.upper() for token in matched[1].split(",")])
    return {"accepted": accepted, "answer": "ans<tape<valid>>" if accepted else "ref<1>",
            "profile": "ddc-tape-shape-v1", "operation_semantics": "NOT_CHECKED"}


def compare_snapshots(before, after):
    left = state(before) if before is not None else None
    right = state(after) if after is not None else None
    if left is None or right is None:
        verdict = "UNVERIFIED"
        answer = "ans<m_invar<unverified>>"
    elif left == right:
        verdict = "EQUAL_RECORDED_STATES"
        answer = "ans<m_invar<stationary>>"
    else:
        verdict = "DIFFERENT_RECORDED_STATES"
        answer = "ref<2>"
    return {"verdict": verdict, "answer": answer, "unlogged_history": "NOT_CHECKED"}


def refusal_transition(value, reason):
    coordinates, rank = state(value)
    require(type(reason) is str and reason in REASONS, "Unknown refusal reason")
    return state_document(coordinates, rank)


def validate_problem(problem):
    fields(problem, ("profile", "initial", "permissions"))
    require(problem["profile"] == PROFILE, "Unknown replay profile")
    state(problem["initial"])
    permissions = problem["permissions"]
    require(type(permissions) is list and len(permissions) <= 32, "Expected bounded permission list")
    for permission in permissions:
        fields(permission, ("event", "before_state_sha256", "after_state_sha256"))
        require(permission["event"] in ("D", "LIFT"), "Permission for unsupported event")
        hash_value(permission["before_state_sha256"])
        hash_value(permission["after_state_sha256"])
    require(len({digest(p) for p in permissions}) == len(permissions), "Duplicate task permission")


def permission_for(event, before, after):
    return {"event": event, "before_state_sha256": digest(before), "after_state_sha256": digest(after)}


def check_permission(problem, event, before, after, submitted):
    permission = permission_for(event, before, after)
    hash_value(submitted)
    require(permission in problem["permissions"] and submitted == digest(permission), "Missing task-bound permission")


def transition(problem, before, step, previous):
    fields(step, ("event", "after", "witness"))
    event, after, witness = step["event"], step["after"], step["witness"]
    require(type(event) is str and event in LETTERS, "Unknown event")
    coordinates, rank = state(before)
    state(after)
    expected = state_document(coordinates, rank)
    observed = measurement(before)
    if event in ("C", "T"):
        fields(witness, ())
    elif event == "R":
        fields(witness, ("potential", "projected"))
        require(canonical(witness) == canonical({"potential": observed["prefix_potential"], "projected": observed["projected_tail"]}), "Residual witness mismatch")
    elif event == "E":
        fields(witness, ("potential",))
        require(canonical(witness["potential"]) == canonical(list(coordinates[:rank])), "Repair potential mismatch")
        require(observed["unrepairable_l1"] == 0, "E cannot discharge unrepairable tail")
        expected = state_document([0] * len(coordinates), rank)
    elif event == "I":
        fields(witness, ("record_sha256",))
        hash_value(witness["record_sha256"])
        require(previous is not None and witness["record_sha256"] == previous, "Integration receipt mismatch")
    elif event == "M":
        fields(witness, ("reason",))
        expected = refusal_transition(before, witness["reason"])
    elif event == "D":
        fields(witness, ("permission_sha256", "loss"))
        require(len(coordinates) > 1 and rank < len(coordinates), "D requires an unrepairable final coordinate")
        expected = state_document(coordinates[:-1], rank)
        loss = {"index": len(coordinates) - 1, "value": coordinates[-1], "before_state_sha256": digest(before)}
        require(canonical(witness["loss"]) == canonical(loss), "Loss ledger mismatch")
        check_permission(problem, event, before, expected, witness["permission_sha256"])
    else:
        fields(witness, ("permission_sha256",))
        require(rank < len(coordinates) and observed["unrepairable_l1"] > 0, "LIFT requires a nonzero unrepairable tail")
        expected = state_document(coordinates, rank + 1)
        check_permission(problem, event, before, expected, witness["permission_sha256"])
    require(state(after) == state(expected), "Proposed after-state differs from computed transition")
    return expected


def make_record(task_sha256, index, event, before, after, witness, previous):
    row = {"index": index, "event": event, "task_sha256": task_sha256,
           "before": before, "after": after, "witness": witness,
           "before_measurement": measurement(before), "after_measurement": measurement(after),
           "previous_sha256": previous, "authority_effect": "None"}
    row = json.loads(canonical(row))
    return dict(row, record_sha256=digest(row))


def replay(problem, proposal):
    validate_problem(problem)
    fields(proposal, ("steps",))
    steps = proposal["steps"]
    require(type(steps) is list and 2 <= len(steps) <= MAX_STEPS, "Expected 2..64 steps")
    for step in steps:
        fields(step, ("event", "after", "witness"))
    require(valid_shape([step["event"] for step in steps]), "Trace shape rejected")
    task_sha256 = digest(problem)
    previous = None
    current = state_document(*state(problem["initial"]))
    records, scope_changes = [], []
    for index, step in enumerate(steps):
        following = transition(problem, current, step, previous)
        record = make_record(task_sha256, index, step["event"], current, following, step["witness"], previous)
        records.append(record)
        previous = record["record_sha256"]
        if step["event"] in ("D", "LIFT"):
            scope_changes.append(index)
        current = following
    total = measurement(current)["total_l1"]
    resolution = "NOT_CLAIMED_AFTER_SCOPE_CHANGE" if scope_changes else ("REPAIRED" if total == 0 else "UNRESOLVED")
    return {"accepted": True, "profile": PROFILE, "task_sha256": task_sha256,
            "records": records, "head_sha256": previous, "length": len(records), "final": current,
            "scope_change_indices": scope_changes, "sealed_refusal": any(step["event"] == "M" for step in steps),
            "original_problem_resolution": resolution, "external_authorization": "NOT_AUTHENTICATED",
            "unlogged_history": "NOT_CHECKED", "runtime_equivalence": "NOT_CLAIMED"}


def demonstration(kind):
    require(kind in ("repair", "refusal", "descent", "lift"), "Unknown demonstration")
    current = state_document([3, 0] if kind == "repair" else [3, 2], 1)
    problem = {"profile": PROFILE, "initial": current, "permissions": []}
    if kind in ("descent", "lift"):
        after = state_document([3], 1) if kind == "descent" else state_document([3, 2], 2)
        problem["permissions"] = [permission_for("D" if kind == "descent" else "LIFT", current, after)]
    events = {"repair": ["C", "R", "E", "I", "T"], "refusal": ["C", "R", "M", "T"],
              "descent": ["C", "D", "E", "I", "T"], "lift": ["C", "R", "LIFT", "E", "I", "T"]}[kind]
    steps, previous = [], None
    for index, event in enumerate(events):
        coordinates, rank = state(current)
        after, witness = state_document(coordinates, rank), {}
        if event == "R":
            witness = {"potential": list(coordinates[:rank]), "projected": [0] * rank + list(coordinates[rank:])}
        elif event == "E":
            witness, after = {"potential": list(coordinates[:rank])}, state_document([0] * len(coordinates), rank)
        elif event == "I":
            witness = {"record_sha256": previous}
        elif event == "M":
            witness = {"reason": "UNREPAIRABLE_TAIL"}
        elif event in ("D", "LIFT"):
            after = state_document(coordinates[:-1], rank) if event == "D" else state_document(coordinates, rank + 1)
            witness = {"permission_sha256": digest(permission_for(event, current, after))}
            if event == "D":
                witness["loss"] = {"index": len(coordinates) - 1, "value": coordinates[-1], "before_state_sha256": digest(current)}
        steps.append({"event": event, "after": after, "witness": witness})
        previous = make_record(digest(problem), index, event, current, after, witness, previous)["record_sha256"]
        current = after
    return problem, {"steps": steps}


def exercise_report():
    before = state_document([3, 2], 1)
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None",
            "cases": {"P9.1": shape_report("tape<c,r,e,i,t>"),
                      "P9.2": shape_report("tape<c,r,m,e,t>"), "P9.3": shape_report("tape<c,r,t,e>"),
                      "P9.4": {"equal": compare_snapshots(before, before), "missing": compare_snapshots(before, None),
                               "different": compare_snapshots(before, state_document([3, 1], 1))}},
            "drills": {f"DRILL9.{i}": shape_report(wire) for i, wire in enumerate(
                ("tape<c,r,e,i,t>", "tape<c,r,m,t>", "tape<c,r,m,e,t>", "tape<e,c,t>", "tape<c,t,e>"), 1)},
            "demonstrations": {kind: replay(*demonstration(kind)) for kind in ("repair", "refusal", "descent", "lift")}}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate field: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise InvalidInput(f"Non-finite JSON constant: {value}")


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, "Input exceeds 64KiB")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object, parse_constant=reject_constant), raw


def evaluate(document, proposal):
    require(type(document) is dict, "Input must be an object")
    kind = document.get("kind")
    if kind == "shape":
        fields(document, ("kind", "wire"))
        require(proposal is None, "Shape mode has no proposal")
        return shape_report(document["wire"])
    if kind == "stationarity":
        fields(document, ("kind", "before", "after"))
        require(proposal is None, "Snapshot mode has no proposal")
        return compare_snapshots(document["before"], document["after"])
    require(kind == "replay", "Unknown input kind")
    fields(document, ("kind", "problem"))
    require(proposal is not None, "Replay requires a separate proposal")
    return replay(document["problem"], proposal)


def write_run(output_root, report, status, input_bytes, proposal_bytes):
    folder = output_root / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": input_bytes, "result.json": (json.dumps(report, sort_keys=True, indent=2) + "\n").encode("utf-8")}
    if proposal_bytes is not None:
        artifacts["proposal.bin"] = proposal_bytes
    artifacts["summary.md"] = (f"# {PILOT_ID}\n\nStatus: {status}. Offline local trace/snapshot/replay checks.\n\nAccepted traces do not confer authority or establish broader DDC-runtime equivalence.\n").encode("utf-8")
    for name, raw in artifacts.items():
        with (folder / name).open("xb") as stream:
            stream.write(raw)
    receipt = {"pilot_id": PILOT_ID, "status": status, "model_calls": 0, "cost_usd": "0",
               "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "artifacts": {name: hashlib.sha256(raw).hexdigest() for name, raw in artifacts.items()}}
    with (folder / "receipt.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--proposal", type=Path)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    try:
        require(args.input is not None or args.proposal is None, "Proposal requires an input")
        proposal, proposal_bytes = read_document(args.proposal) if args.proposal else (None, None)
        if args.input:
            document, input_bytes = read_document(args.input)
            try:
                report = evaluate(document, proposal)
                status = "REJECTED" if report.get("accepted") is False or report.get("verdict") == "DIFFERENT_RECORDED_STATES" else ("UNVERIFIED" if report.get("verdict") == "UNVERIFIED" else "CHECKED")
            except InvalidInput as error:
                report, status = {"accepted": False, "reason": str(error)}, "REJECTED"
        else:
            input_bytes = canonical({"kind": "built_in_exercises"}).encode("ascii")
            report, status = exercise_report(), "CHECKED"
        folder = write_run(args.output_dir, report, status, input_bytes, proposal_bytes)
    except (OSError, ValueError, TypeError, RecursionError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": status, "output": str(folder)}, ensure_ascii=True))
    return 0 if status == "CHECKED" else 1


if __name__ == "__main__":
    sys.exit(main())
