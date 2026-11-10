"""Quiz14: exact intrinsic triangle-fan deficits and separate finite signed pairings."""
import argparse
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

PILOT_ID = "pilot_0000045"
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID
MAX_BYTES = 131072


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



def label(value):
    require(type(value) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", value), "Bounded label required")
    return value


def labels(value, lower, upper):
    require(type(value) is list and lower <= len(value) <= upper, "Label-list size")
    result = tuple(label(v) for v in value)
    require(len(set(result)) == len(result), "Repeated label")
    return result


def fan(value):
    fields(value, ("center", "vertices", "triangles"))
    vertices = labels(value["vertices"], 4, 13)
    center = label(value["center"])
    require(center in vertices, "Center must be declared")
    raw = value["triangles"]
    require(type(raw) is list and 3 <= len(raw) <= 12, "Fan has 3..12 triangles")
    link = {v: set() for v in vertices if v != center}
    triangles, edges = set(), set()
    for row in raw:
        triangle = labels(row, 3, 3)
        require(center in triangle and all(v in vertices for v in triangle), "Declared center-incident triangle required")
        triangle = tuple(sorted(triangle))
        require(triangle not in triangles, "Repeated triangle")
        triangles.add(triangle)
        edges.update(combinations(triangle, 2))
        a, b = (v for v in triangle if v != center)
        link[a].add(b)
        link[b].add(a)
    require(all(len(neighbors) == 2 for neighbors in link.values()), "Interior link must have degree two")
    reached, pending = set(), [min(link)]
    while pending:
        v = pending.pop()
        if v not in reached:
            reached.add(v)
            pending.extend(link[v] - reached)
    require(reached == set(link), "Interior link must be one connected cycle")
    count = len(triangles)
    angles = [Fraction(1, 6)] * count
    angle_sum = sum(angles, Fraction(0))
    deficit = Fraction(1) - angle_sum
    boundary_turns = {v: Fraction(1, 6) for v in sorted(link)}
    euler = len(vertices) - len(edges) + count
    total_turn = deficit + sum(boundary_turns.values(), Fraction(0))
    return {"center": center, "vertices": sorted(vertices),
            "triangles": [list(t) for t in sorted(triangles)], "edges": [list(e) for e in sorted(edges)],
            "center_link_edges": [list(e) for e in sorted({tuple(sorted((a, b))) for a in link for b in link[a]})],
            "center_is_interior": True, "triangle_count": count,
            "metric": "intrinsic_equilateral_unit_edges", "angle_units": "2*pi",
            "center_angles": [str(a) for a in angles], "angle_sum": str(angle_sum), "deficit": str(deficit),
            "deficit_pi_multiple": str(2 * deficit),
            "classification": "flat" if deficit == 0 else "curved",
            "deficit_sign": "zero" if deficit == 0 else "positive" if deficit > 0 else "negative",
            "f_vector": [len(vertices), len(edges), count], "euler": euler,
            "boundary_turns": {v: str(a) for v, a in boundary_turns.items()},
            "total_normalized_turn": str(total_turn), "gauss_bonnet_residual": str(total_turn - euler)}


def pairing(value):
    require(type(value) is list and len(value) <= 12, "At most twelve pairs")
    pair_ids, member_ids, rows = set(), set(), []
    positive_total = negative_total = Fraction(0)
    signed_count = 0
    for pair in value:
        fields(pair, ("pair_id", "positive", "negative"))
        pair_id = label(pair["pair_id"])
        require(pair_id not in pair_ids, "Repeated pair identifier")
        pair_ids.add(pair_id)
        members = []
        for role, expected_sign in (("positive", 1), ("negative", -1)):
            member = pair[role]
            fields(member, ("member_id", "sign", "weight"))
            member_id = label(member["member_id"])
            require(member_id not in member_ids, "Repeated member identifier")
            member_ids.add(member_id)
            sign = integer(member["sign"], -1, 1, "Integer sign required")
            require(sign == expected_sign, "Member sign does not match its role")
            weight = rational(member["weight"])
            require(weight >= 0, "Nonnegative weight required")
            members.append((member_id, sign, weight))
            signed_count += sign
        positive, negative = members
        positive_total += positive[2]
        negative_total += negative[2]
        rows.append({"pair_id": pair_id, "positive_id": positive[0], "negative_id": negative[0],
                     "positive_weight": str(positive[2]), "negative_weight": str(negative[2]),
                     "contribution": str(positive[1] * positive[2] + negative[1] * negative[2])})
    return {"pairs": sorted(rows, key=lambda row: row["pair_id"]), "pair_count": len(rows),
            "positive_count": len(rows), "negative_count": len(rows), "member_count": len(member_ids),
            "signed_count": signed_count, "positive_weight_total": str(positive_total),
            "negative_weight_total": str(negative_total), "weighted_total": str(positive_total - negative_total),
            "all_pairwise_weights_equal": all(row["positive_weight"] == row["negative_weight"] for row in rows),
            "interpretation": "declared_finite_signed_weights_only"}


def answer_for(request):
    json_value(request)
    require(len(encoded(request)) <= MAX_BYTES, "Input byte limit")
    require(type(request) is dict, "Request object required")
    kinds = {"fan": ("fan",), "pairing": ("pairs",), "physical_claim": ("pairs", "claim")}
    kind = request.get("kind")
    require(type(kind) is str and kind in kinds, "Unknown query kind")
    fields(request, ("case_id", "kind") + kinds[kind])
    require(type(request["case_id"]) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", request["case_id"]),
            "Bounded case identifier required")
    if kind == "fan":
        data = {"status": "COMPUTED", "fan": fan(request["fan"])}
    elif kind == "pairing":
        data = {"status": "COMPUTED", "pairing": pairing(request["pairs"])}
    else:
        require(request["claim"] == "regge4d_susy_from_pairs", "Unknown typed physical claim")
        finite = pairing(request["pairs"])
        data = {"status": "REFUSED", "refusal": "ref<3>", "claim": request["claim"],
                "finite_pairing": finite, "adapter": "UNBOUND",
                "missing_witnesses": ["4D metric and dihedral angles", "represented supercharge algebra and checked relations",
                                      "physical mode energies and a vacuum model"]}
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




def fan_request(case="fan", size=6):
    rim = [f"v{i}" for i in range(size)]
    return {"case_id": case, "kind": "fan", "fan": {"center": "c", "vertices": ["c"] + rim,
            "triangles": [["c", rim[i], rim[(i + 1) % size]] for i in range(size)]}}


def pairing_request(case="pairs", size=11, last_negative="1"):
    return {"case_id": case, "kind": "pairing", "pairs": [
        {"pair_id": f"pair{i}", "positive": {"member_id": f"p{i}", "sign": 1, "weight": "1"},
         "negative": {"member_id": f"n{i}", "sign": -1, "weight": last_negative if i == size - 1 else "1"}}
        for i in range(size)]}


def exercise_report():
    physical = pairing_request("P14.4")
    physical.update(kind="physical_claim", claim="regge4d_susy_from_pairs")
    prose = ("Eleven declared pairs each carry one +1 and one -1 toy unit. The signed count is\n"
             "0. Now give the negative unit in the last pair weight 2 while every other weight\n"
             "remains 1. What is the weighted total?")
    fixtures = [
        ("P14.1", "packet_label", "ask<deficit<fan2d,faces<6>>>",
         "ans<deficit<rat<0,1>>,flat,ae0>", fan_request("P14.1", 6)),
        ("P14.2", "packet_label", "ask<deficit<fan2d,faces<5>>>",
         "ans<deficit<rat<1,6>>,curved,ae0>", fan_request("P14.2", 5)),
        ("P14.3", "prose", prose, "ans<pair_count<11>,signed_count<0>,weighted_total<minus1>>",
         pairing_request("P14.3", last_negative="2")),
        ("P14.4", "packet_label", "ask<derive<regge4d,susy,from<pair_count<11>>>>", "ref<3>", physical)]
    fractional = pairing_request("fractional", 2)
    for pair, a, b in zip(fractional["pairs"], ("1/3", "1/2"), ("1/4", "2/3"), strict=True):
        pair["positive"]["weight"], pair["negative"]["weight"] = a, b
    cross = pairing_request("cross_cancellation", 2)
    cross["pairs"][0]["positive"]["weight"] = "2"
    cross["pairs"][1]["negative"]["weight"] = "2"
    controls = [fan_request("positive", 3), fan_request("negative", 7), fan_request("maximum", 12),
                pairing_request("empty", 0), pairing_request("equal", 11), fractional, cross]
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM",
            "exercises": [{"id": name, "source_prompt_kind": prompt_kind, "source_prompt": prompt,
                           "source_answer": answer, "request": request, "computed_answer": answer_for(request)}
                          for name, prompt_kind, prompt, answer, request in fixtures],
            "controls": [answer_for(request) for request in controls],
            "source_notation": "HISTORICAL_LABELS_NOT_A_WIRE_PARSER", "source_drills": 0, "source_registry": None,
            "authority_effect": "None", "genesis_effect": "None", "realizes": None}


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw), raw


def write_run(output, report, raw_input, status):
    folder = output / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": raw_input, "result.json": encoded(report),
                 "summary.md": (f"# {PILOT_ID}\n\n{status}: exact finite triangle fans and signed pairing sums.\n"
                                "No 4D geometry, physical supersymmetry, vacuum or Genesis derivation claim.\n").encode()}
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
            raw, report, status = encoded({"kind": "built_in_exercises"}), exercise_report(), "DEMONSTRATED"
        folder = write_run(args.output_dir, report, raw, status)
    except (ValueError, TypeError, OSError, RecursionError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": status, "output": str(folder.resolve())}, ensure_ascii=True))
    return 1 if status in ("MISMATCH", "REJECTED") else 0


if __name__ == "__main__":
    sys.exit(main())
