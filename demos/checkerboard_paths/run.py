"""Quiz12: bounded exact null-lattice paths and assigned corner-weight sums."""
import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

PILOT_ID = "pilot_0000043"
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID
# Facts each computed answer must show, transcribed from the original worksheet's source-row table.
SOURCE_FACTS = {
    "P12.1": {"data": {"total_paths": 1, "corner_histogram": [1, 0, 0], "amplitude": ["1", "0"]}},
    "P12.2": {"data": {"total_paths": 2, "corner_histogram": [0, 2], "amplitude": ["0", "2"]}},
    "P12.3": {"data": {"refusal": "ref<1>"}},
    "P12.4": {"data": {"refusal": "ref<4>", "claim": "continuous_dirac_spinor_invariance"}},
    "DRILL12.1": {"data": {"point": [0, 0]}},
    "DRILL12.2": {"data": {"direction": "R"}},
    "DRILL12.3": {"data": {"direction": "L"}},
    "DRILL12.4": {"data": {"refusal": "ref<1>"}},
    "DRILL12.5": {"data": {"corners": 2}},
    "DRILL12.6": {"data": {"total_paths": 2, "amplitude": ["0", "0"]}},
    "DRILL12.7": {"data": {"refusal": "ref<4>", "claim": "continuous_spinor_field"}}}
MAX_BYTES = 131072
MAX_STEPS = 32
SOURCE_VOCABULARY = ("pt<t,x>", "step<r>", "step<l>", "path<step1<>step2<>...>",
                     "corner<path,c_int>", "amp<c_int,eps,m>", "kernel<p0,pN,sum_amp>",
                     "ref<1>", "ref<3>", "ref<4>")


class InvalidInput(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidInput(message)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Exact object fields required")


def json_value(value, depth=0):
    require(depth <= 16, "JSON depth bound")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        require(abs(value) <= 10**18, "JSON integer bound")
    elif type(value) is str:
        require(len(value) <= 2048 and all(32 <= ord(c) < 127 for c in value), "Bounded printable ASCII required")
    elif type(value) is list:
        require(len(value) <= 256, "List bound")
        for item in value:
            json_value(item, depth + 1)
    elif type(value) is dict:
        require(len(value) <= 64, "Object bound")
        for key, item in value.items():
            require(type(key) is str, "String keys required")
            json_value(key, depth + 1)
            json_value(item, depth + 1)
    else:
        raise InvalidInput("Unsupported JSON value; no floating-point numbers")


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(encoded(value))


def clone(value):
    return json.loads(encoded(value))


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, "Bounded bytes required")
    def bad_constant(_):
        raise InvalidInput("Non-finite JSON number")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs, parse_constant=bad_constant)


def rational(value):
    require(type(value) is str and re.fullmatch(r"-?(0|[1-9][0-9]{0,6})(/[1-9][0-9]{0,6})?", value) is not None,
            "Canonical rational string required")
    result = Fraction(value)
    require(abs(result.numerator) <= 1000000 and result.denominator <= 1000000, "Rational bound")
    require(str(result) == value, "Unreduced or noncanonical rational")
    return result


def integer(value, lower, upper, label):
    require(type(value) is int and lower <= value <= upper, label)
    return value


def point(value):
    require(type(value) is list and len(value) == 2, "Point is [t,x]")
    return tuple(integer(v, -1000000, 1000000, "Coordinate bound") for v in value)


def parameters(request):
    epsilon, mass = rational(request["epsilon"]), rational(request["mass"])
    require(epsilon > 0, "Positive epsilon required")
    return epsilon * mass


def direction(start, end):
    if end[0] - start[0] != 1 or abs(end[1] - start[1]) != 1:
        return None
    return "R" if end[1] > start[1] else "L"


def corners(directions):
    return sum(a != b for a, b in zip(directions, directions[1:], strict=False))


def amplitude(histogram, a):
    real = imaginary = Fraction(0)
    power_real, power_imaginary = Fraction(1), Fraction(0)
    for count in histogram:
        real += count * power_real
        imaginary += count * power_imaginary
        power_real, power_imaginary = -power_imaginary * a, power_real * a
    return [str(real), str(imaginary)]


def histograms(steps, displacement):
    buckets = {key: [0] * max(1, steps) for key in ("RR", "RL", "LR", "LL")}
    if steps == 0 or abs(displacement) > steps or (steps - displacement) % 2:
        return buckets
    states = {(1, "R", "R", 0): 1, (-1, "L", "L", 0): 1}
    for _ in range(1, steps):
        following = defaultdict(int)
        for (x, first, last, count), ways in states.items():
            for new, delta in (("R", 1), ("L", -1)):
                following[x + delta, first, new, count + (new != last)] += ways
        states = following
    for (x, first, last, count), ways in states.items():
        if x == displacement:
            buckets[first + last][count] += ways
    return buckets


def kernel(request):
    start, end = point(request["start"]), point(request["end"])
    steps = integer(end[0] - start[0], 0, MAX_STEPS, "Time horizon is 0..32")
    displacement = end[1] - start[1]
    a = parameters(request)
    first, last = request["first"], request["last"]
    require(first in (None, "R", "L") and last in (None, "R", "L"), "Direction selector")
    buckets = histograms(steps, displacement)
    selected = [0] * max(1, steps)
    for key, histogram in buckets.items():
        if (first is None or key[0] == first) and (last is None or key[1] == last):
            selected = [a + b for a, b in zip(selected, histogram, strict=True)]
    empty = int(steps == 0 and displacement == 0 and first is None and last is None)
    selected[0] += empty
    return {"status": "COMPUTED", "steps": steps, "displacement": displacement,
            "corner_histogram": selected, "total_paths": sum(selected),
            "amplitude": amplitude(selected, a), "direction_histograms": buckets,
            "direction_amplitudes": {key: amplitude(value, a) for key, value in buckets.items()},
            "empty_path_count": empty, "initial_corner_counted": False}


def answer_for(request):
    json_value(request)
    require(len(encoded(request)) <= MAX_BYTES, "Input byte limit")
    require(type(request) is dict, "Request object required")
    common = ("case_id", "kind")
    kinds = {"node": ("point",), "step": ("start", "end"), "path": ("points",),
             "corners": ("directions",), "amplitude": ("corners", "epsilon", "mass"),
             "kernel": ("start", "end", "epsilon", "mass", "first", "last"), "claim": ("claim",)}
    kind = request.get("kind")
    require(type(kind) is str and kind in kinds, "Unknown query kind")
    fields(request, common + kinds[kind])
    require(type(request["case_id"]) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", request["case_id"]),
            "Bounded case identifier required")
    if kind == "node":
        data = {"status": "COMPUTED", "point": list(point(request["point"]))}
    elif kind == "step":
        move = direction(point(request["start"]), point(request["end"]))
        data = {"status": "COMPUTED", "direction": move} if move else {
            "status": "REFUSED", "refusal": "ref<1>", "reason": "Not a forward unit null step"}
    elif kind == "path":
        raw = request["points"]
        require(type(raw) is list and 1 <= len(raw) <= MAX_STEPS + 1, "Path has 1..33 vertices")
        points = tuple(point(v) for v in raw)
        moves = tuple(direction(a, b) for a, b in zip(points, points[1:], strict=False))
        invalid = [i for i, move in enumerate(moves) if move is None]
        data = {"status": "REFUSED", "refusal": "ref<1>", "invalid_step_indices": invalid} if invalid else {
            "status": "COMPUTED", "directions": list(moves), "corners": corners(moves),
            "first": moves[0] if moves else None, "last": moves[-1] if moves else None}
    elif kind == "corners":
        moves = request["directions"]
        require(type(moves) is list and len(moves) <= MAX_STEPS and all(v in ("R", "L") for v in moves),
                "At most 32 R/L directions")
        data = {"status": "COMPUTED", "corners": corners(moves),
                "first": moves[0] if moves else None, "last": moves[-1] if moves else None}
    elif kind == "amplitude":
        count = integer(request["corners"], 0, MAX_STEPS - 1, "Corner count is 0..31")
        a = parameters(request)
        data = {"status": "COMPUTED", "amplitude": amplitude([0] * count + [1], a)}
    elif kind == "kernel":
        data = kernel(request)
    else:
        claim = request["claim"]
        continuum = ("continuous_dirac_spinor_invariance", "continuous_spinor_field")
        require(claim in continuum + ("physical_mass_or_spin",), "Unknown typed claim")
        data = {"status": "REFUSED", "refusal": "ref<4>" if claim in continuum else "ref<3>",
                "claim": claim, "adapter": "UNBOUND"}
    return {"case_id": request["case_id"], "kind": kind, "data": data,
            "authority_effect": "None", "genesis_effect": "None", "realizes": None}


def submission(request, answer):
    request = clone(request)
    return {"request": request, "proposal": {"input_sha256": digest(request), "answer": clone(answer)}}


def evaluate(document):
    json_value(document)
    require(len(encoded(document)) <= MAX_BYTES, "Input byte limit")
    document = clone(document)
    fields(document, ("request", "proposal"))
    proposal = document["proposal"]
    fields(proposal, ("input_sha256", "answer"))
    canonical = answer_for(document["request"])
    binding_ok = type(proposal["input_sha256"]) is str and proposal["input_sha256"] == digest(document["request"])
    matches = binding_ok and encoded(proposal["answer"]) == encoded(canonical)
    return {"verdict": "MATCH" if matches else "MISMATCH", "binding_ok": binding_ok,
            "request": document["request"], "proposal": proposal, "canonical": canonical}


def kernel_request(case="kernel", steps=4, x=0, mass="1", epsilon="1", first=None, last=None):
    return {"case_id": case, "kind": "kernel", "start": [0, 0], "end": [steps, x],
            "epsilon": epsilon, "mass": mass, "first": first, "last": last}


def holds(expected, actual):
    """Every expected field occurs in ``actual`` with the same canonical value."""
    if type(expected) is dict:
        return type(actual) is dict and all(key in actual and holds(value, actual[key]) for key, value in expected.items())
    return encoded(expected) == encoded(actual)


def fact_check(case_id, answer):
    facts = SOURCE_FACTS[case_id]
    return {"source_facts": facts, "verdict": "MATCH" if holds(facts, answer) else "MISMATCH"}


def demonstration_status(report):
    """DEMONSTRATED only when every exercise row shows its stated source facts."""
    return "DEMONSTRATED" if all(row["verdict"] == "MATCH" for row in report["exercises"]) else "MISMATCH"


def exercise_report():
    fixtures = [
        ("P12.1", "ask<eval<kernel,p0<0,0>,pN<3,3>,m<0>>>",
         "ans<kernel<p0<0,0>,pN<3,3>,amp<1>,corners<0>>>", kernel_request("P12.1", 3, 3, "0")),
        ("P12.2", "ask<count<paths,p0<0,0>,pN<2,0>>>",
         "ans<paths<count<2>,corners<path1<1>,path2<1>>>>", kernel_request("P12.2", 2, 0)),
        ("P12.3", "ask<step<p0<0,0>,pN<1,2>>>", "ref<1>",
         {"case_id": "P12.3", "kind": "step", "start": [0, 0], "end": [1, 2]}),
        ("P12.4", "ask<claim<continuous_dirac_spinor_invariance,gamma_matrices>>", "ref<4>",
         {"case_id": "P12.4", "kind": "claim", "claim": "continuous_dirac_spinor_invariance"}),
        ("DRILL12.1", "ask<node<0,0>>", "ans<pt<0,0>>",
         {"case_id": "DRILL12.1", "kind": "node", "point": [0, 0]}),
        ("DRILL12.2", "ask<step<0_0>1_1>>", "ans<valid<step<r>>>",
         {"case_id": "DRILL12.2", "kind": "step", "start": [0, 0], "end": [1, 1]}),
        ("DRILL12.3", "ask<step<0_0>1_m1>>", "ans<valid<step<l>>>",
         {"case_id": "DRILL12.3", "kind": "step", "start": [0, 0], "end": [1, -1]}),
        ("DRILL12.4", "ask<step<0_0>1_2>>", "ref<1>",
         {"case_id": "DRILL12.4", "kind": "step", "start": [0, 0], "end": [1, 2]}),
        ("DRILL12.5", "ask<corners<r<>l<>r>>", "ans<corner<2>>",
         {"case_id": "DRILL12.5", "kind": "corners", "directions": ["R", "L", "R"]}),
        ("DRILL12.6", "ask<eval<kernel,p0<0,0>,pN<2,0>,m<0>>>", "ans<kernel<amp<0>>>",
         kernel_request("DRILL12.6", 2, 0, "0")),
        ("DRILL12.7", "ask<import<continuous_spinor_field>>", "ref<4>",
         {"case_id": "DRILL12.7", "kind": "claim", "claim": "continuous_spinor_field"})]
    controls = [
        {"case_id": "path", "kind": "path", "points": [[0, 0], [1, 1], [2, 0], [3, 1]]},
        {"case_id": "amplitude", "kind": "amplitude", "corners": 3, "epsilon": "1/2", "mass": "2"},
        {"case_id": "physics", "kind": "claim", "claim": "physical_mass_or_spin"},
        kernel_request("empty", 0, 0), kernel_request("parity", 3, 0),
        kernel_request("cancellation", 4, 0), kernel_request("direction", 4, 0, first="R", last="L")]
    rows = [{"id": name, "source_query": query, "source_answer": answer,
             "request": request, "computed_answer": answer_for(request)}
            for name, query, answer, request in fixtures]
    for row in rows:
        row.update(fact_check(row["id"], row["computed_answer"]))
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "exercises": rows,
            "controls": [answer_for(request) for request in controls],
            "source_vocabulary": list(SOURCE_VOCABULARY),
            "source_notation": "HISTORICAL_LABELS_NOT_A_GENERAL_WIRE_PARSER",
            "authority_effect": "None", "genesis_effect": "None", "realizes": None}


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw), raw


def write_run(output, report, raw_input, status):
    folder = output / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": raw_input, "result.json": encoded(report),
                 "summary.md": (f"# {PILOT_ID}\n\n{status}: exact finite corner-weight path sums.\n"
                                "No unitarity, continuum, physical or Genesis derivation claim.\n").encode()}
    for name, raw in artifacts.items():
        (folder / name).write_bytes(raw)
    receipt = {"pilot_id": PILOT_ID, "status": status, "model_calls": 0, "cost_usd": "0",
               "code_sha256": sha(Path(__file__).read_bytes()), "artifact_sha256": {name: sha(raw) for name, raw in artifacts.items()}}
    (folder / "receipt.json").write_bytes(encoded(receipt))
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    try:
        if args.input:
            document, raw = read_document(args.input)
            try:
                report = evaluate(document)
                status = report["verdict"]
            except InvalidInput as error:
                report, status = {"reason": str(error)}, "REJECTED"
        else:
            raw, report = encoded({"kind": "built_in_exercises"}), exercise_report()
            status = demonstration_status(report)
        folder = write_run(args.output_dir, report, raw, status)
    except (ValueError, TypeError, OSError, RecursionError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": status, "output": str(folder.resolve())}, ensure_ascii=True))
    return 1 if status in ("MISMATCH", "REJECTED") else 0


if __name__ == "__main__":
    sys.exit(main())


