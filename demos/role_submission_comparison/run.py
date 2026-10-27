"""Quiz10: frozen role submissions, literal comparison and a separate finite check.

NO_LLM. No arbitrary-prose evaluator, independent-reasoning or action-authority claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

PILOT_ID = "pilot_0000035"
MAX_BYTES = 65536
TAGS = ("STANDARD", "IMPORTED", "DERIVED", "CONDITIONAL", "INTERPRETIVE", "CONJECTURE", "Q-HELD", "REFUSED")
STANCES = ("support", "oppose", "undecided")
COMPARE_FIELDS = ("tag", "stance", "observations", "revision")
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID
# (protocol_status, claim_status) for each source item, as stated in the original worksheet.
EXPECTED_OUTCOMES = {
    "P10.1": ("RECORDED", "UNVERIFIED"), "P10.2": ("RECORDED", "UNVERIFIED"),
    "P10.3": ("REFUSED", "UNVERIFIED"), "P10.4": ("RECORDED", "UNVERIFIED"),
    "DRILL10.1": ("RECORDED", "UNVERIFIED"), "DRILL10.2": ("RECORDED", "UNVERIFIED"),
    "DRILL10.3": ("REFUSED", "UNVERIFIED"), "DRILL10.4": ("RECORDED", "UNVERIFIED"),
    "DRILL10.5": ("REFUSED", "CHECKED")}


class InvalidInput(ValueError):
    """The submitted data does not satisfy this pilot's declared contract."""


def require(value, reason):
    if not value:
        raise InvalidInput(reason)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Unexpected fields")


def text(value, limit=2048):
    require(type(value) is str and 0 < len(value) <= limit, "Bounded nonempty text required")


def identifier(value):
    require(type(value) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,47}", value) is not None, "Invalid identifier")


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(encoded(value))


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, "Bounded raw bytes required")
    def reject_constant(_):
        raise InvalidInput("Non-finite JSON number")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs, parse_constant=reject_constant)


def validate_task(task):
    fields(task, ("claim_id", "proposition", "requirements", "supplied"))
    identifier(task["claim_id"])
    proposition = task["proposition"]
    require(type(proposition) is dict, "Proposition object required")
    if proposition.get("kind") == "integer_le":
        fields(proposition, ("kind", "left", "right"))
        for side in ("left", "right"):
            values = proposition[side]
            require(type(values) is list and 1 <= len(values) <= 16, "Bounded operand list required")
            require(all(type(x) is int and abs(x) <= 10**6 for x in values), "Bounded exact integers required")
        require(task["requirements"] == [] and task["supplied"] == {}, "Finite check has no external premises")
    else:
        fields(proposition, ("kind", "text"))
        require(proposition["kind"] == "opaque", "Unsupported proposition kind")
        text(proposition["text"])
    required = task["requirements"]
    require(type(required) is list and len(required) <= 16, "Bounded requirement list required")
    for name in required:
        identifier(name)
    require(len(set(required)) == len(required), "Duplicate requirement")
    supplied = task["supplied"]
    require(type(supplied) is dict and set(supplied) <= set(required), "Unrequested supplied field")
    for content in supplied.values():
        text(content)


def validate_role(task, proposal, role):
    fields(proposal, ("role", "task_sha256", "tag", "stance", "observations", "revision"))
    require(proposal["role"] == role, "Wrong or duplicated role")
    require(proposal["task_sha256"] == digest(task), "Proposal belongs to another task")
    require(proposal["tag"] in TAGS, "Unknown contextual tag")
    require(proposal["stance"] in STANCES, "Unknown proposed stance")
    observations = proposal["observations"]
    require(type(observations) is list and len(observations) <= 16, "Bounded observations required")
    for observation in observations:
        text(observation)
    if proposal["revision"] is not None:
        validate_task(proposal["revision"])


def freeze(task, red, green):
    validate_task(task)
    validate_role(task, red, "red")
    validate_role(task, green, "green")
    raw = encoded({"task": task, "red": red, "green": green})
    require(len(raw) <= MAX_BYTES, "Frozen input exceeds byte limit")
    return raw


def finite_check(task):
    """Actually compute the sole supported predicate, not a supplied verdict."""
    validate_task(task)
    proposition = task["proposition"]
    if proposition["kind"] != "integer_le":
        return {"status": "UNBOUND", "executed": False, "task_sha256": digest(task), "checker": None}
    left, right = sum(proposition["left"]), sum(proposition["right"])
    return {"status": "PASS" if left <= right else "FAIL", "executed": True,
            "task_sha256": digest(task), "checker": "bounded_integer_sum_le_v1",
            "left_sum": left, "right_sum": right, "margin": right - left}


def integrate(task, frozen, expected_sha256, request="record", execute_check=False):
    validate_task(task)
    require(type(execute_check) is bool, "Check switch must be boolean")
    require(request in ("record", "verified", "global_authority"), "Unknown request")
    require(type(expected_sha256) is str and re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is not None, "Frozen digest required")
    snapshot = decode(frozen)
    require(sha(frozen) == expected_sha256, "Frozen bytes changed")
    fields(snapshot, ("task", "red", "green"))
    require(encoded(snapshot["task"]) == encoded(task), "Frozen task substituted")
    require(freeze(snapshot["task"], snapshot["red"], snapshot["green"]) == frozen, "Noncanonical frozen input")
    red, green = snapshot["red"], snapshot["green"]
    same = [key for key in COMPARE_FIELDS if red[key] == green[key]]
    different = {key: {"red": red[key], "green": green[key]} for key in COMPARE_FIELDS if red[key] != green[key]}
    changes = []
    for role, submission in (("red", red), ("green", green)):
        revision = submission["revision"]
        if revision is not None:
            changes.append({"role": role, "proposed_task_sha256": digest(revision),
                            "changed_fields": [key for key in sorted(task) if task[key] != revision[key]],
                            "dropped_requirements": sorted(set(task["requirements"]) - set(revision["requirements"])),
                            "new_claim_status": "UNVERIFIED", "semantic_loss": "NOT_MEASURED"})
    check = finite_check(task) if execute_check else {"status": "NOT_RUN", "executed": False, "task_sha256": digest(task), "checker": None}
    status = {"PASS": "CHECKED", "FAIL": "CONTRADICTED"}.get(check["status"], "UNVERIFIED")
    refused = request == "global_authority" or (request == "verified" and status != "CHECKED")
    return {"pilot_id": PILOT_ID, "authority_effect": "None", "protocol_status": "REFUSED" if refused else "RECORDED",
            "refusal": "ref<2>" if refused else None, "claim_status": status, "check": check,
            "original_task_sha256": digest(task), "frozen_sha256": expected_sha256, "frozen": snapshot,
            "agreements": same, "disagreements": different, "proposal_changes": changes,
            "missing_declared_inputs": sorted(set(task["requirements"]) - set(task["supplied"])),
            "supplied_content_validated": False, "role_independence": "NOT_ESTABLISHED",
            "semantic_loss": "NOT_MEASURED", "request": request}


def role_proposal(task, role, tag="DERIVED", stance="support", revision=None, observations=None):
    return {"role": role, "task_sha256": digest(task), "tag": tag, "stance": stance,
            "observations": [] if observations is None else observations, "revision": revision}


def inequality(left, right):
    return {"claim_id": "inequality", "proposition": {"kind": "integer_le", "left": left, "right": right}, "requirements": [], "supplied": {}}


def opaque(claim_id, statement, requirements):
    return {"claim_id": claim_id, "proposition": {"kind": "opaque", "text": statement}, "requirements": requirements, "supplied": {}}


def evaluate(document):
    fields(document, ("task", "red", "green", "request", "execute_check"))
    raw = freeze(document["task"], document["red"], document["green"])
    return integrate(document["task"], raw, sha(raw), document["request"], document["execute_check"])


def example(task, request="record", execute_check=False, **green_options):
    return evaluate({"task": task, "red": role_proposal(task, "red"), "green": role_proposal(task, "green", **green_options),
                     "request": request, "execute_check": execute_check})


def outcome_row(name, result):
    expected = dict(zip(("protocol_status", "claim_status"), EXPECTED_OUTCOMES[name], strict=True))
    matches = all(result[key] == value for key, value in expected.items())
    return {"id": name, "result": result, "expected": expected, "verdict": "MATCH" if matches else "MISMATCH"}


def demonstration_status(report):
    """DEMONSTRATED only when every exercise row has its stated outcome."""
    return "DEMONSTRATED" if all(row["verdict"] == "MATCH" for row in report["exercises"]) else "MISMATCH"


def exercise_report():
    attention = opaque("attention_zeta", "We have mathematically proven that the transformer attention mechanism is identical to the continuous Riemann zeta function.",
                       ["attention_definition", "zeta_domain", "equivalence_map", "argument"])
    analogy = opaque("attention_analogy", "A possible analogy, not an established identity.", ["definitions", "correspondence"])
    born = opaque("born_rule_hilbert_lift", "born_rule_hilbert_lift (worksheet scope: discrete_weights)",
                  ["precise_lift_claim", "witness"])
    audit = evaluate({"task": attention, "red": role_proposal(attention, "red", "Q-HELD", "undecided", observations=["Definitions, map and argument have not been supplied."]),
                      "green": role_proposal(attention, "green", "CONJECTURE", "undecided", revision=analogy),
                      "request": "record", "execute_check": True})
    agreement = example(inequality([2, 3], [4, 1]), request="verified")
    tagged = example(born)
    global_request = example(inequality([2, 3], [4, 1]), request="global_authority", execute_check=True)
    rows = [outcome_row(name, result) for name, result in (
        ("P10.1", audit), ("P10.2", audit), ("P10.3", agreement), ("P10.4", tagged),
        ("DRILL10.1", audit), ("DRILL10.2", audit), ("DRILL10.3", agreement),
        ("DRILL10.4", tagged), ("DRILL10.5", global_request))]
    controls = {"checked_true": example(inequality([2, 3], [4, 1]), request="verified", execute_check=True),
                "false_consensus": example(inequality([2, 3], [4]), request="verified", execute_check=True),
                "true_despite_disagreement": example(inequality([2], [3]), execute_check=True, stance="oppose"),
                "unsupported_despite_supplied_text": None}
    supplied = json.loads(encoded(attention))
    supplied["supplied"] = {key: "A supplied assertion, not a checked witness." for key in supplied["requirements"]}
    controls["unsupported_despite_supplied_text"] = example(supplied, request="verified", execute_check=True)
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None", "exercises": rows,
            "controls": controls, "contextual_tags": list(TAGS),
            "historical_defect_labels": ["false_lift", "category_error", "authority_leak", "analogy_only"],
            "historical_label_status": "SOURCE_PROPOSALS_NOT_COMPUTED_CONCLUSIONS"}


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw), raw


def write_run(output, report, input_bytes, status):
    folder = output / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": input_bytes, "result.json": encoded(report),
                 "summary.md": (f"# {PILOT_ID}\n\n{status}: offline task-bound comparison and a separate bounded integer check.\nNo role-independence or action-authority claim.\n").encode()}
    for name, raw in artifacts.items():
        (folder / name).write_bytes(raw)
    receipt = {"pilot_id": PILOT_ID, "status": status, "model_calls": 0, "cost_usd": "0",
               "code_sha256": sha(Path(__file__).read_bytes()),
               "artifact_sha256": {name: sha(raw) for name, raw in artifacts.items()}}
    (folder / "receipt.json").write_bytes(encoded(receipt))
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Task, Red, Green, requested status and host check switch")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    try:
        if args.input:
            document, raw = read_document(args.input)
            try:
                report = evaluate(document)
                status = report["protocol_status"]
            except InvalidInput as error:
                report, status = {"reason": str(error)}, "REJECTED"
        else:
            raw = encoded({"kind": "built_in_exercises"})
            report = exercise_report()
            status = demonstration_status(report)
        folder = write_run(args.output_dir, report, raw, status)
    except (ValueError, TypeError, OSError, RecursionError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": status, "output": str(folder.resolve())}, ensure_ascii=True))
    return 1 if status in ("REJECTED", "REFUSED", "MISMATCH") else 0


if __name__ == "__main__":
    sys.exit(main())
