"""Mode 13's finite occurrence/payload rewrite through pinned, single-threaded Egglog.

This observes the declared source representation, not arbitrary prompt semantics.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from collections import Counter
from pathlib import Path

from omega_engine_pfp.domain.rewriting.rewrites import ROLES, RewriteReceipt, RewriteRequest, Segment

EGGLOG_VERSION = "14.0.0"
MAX_ITERATIONS = 10
MAX_NODES = 1024
MAX_SEGMENTS = 32
SCHEMA = """
(datatype PayloadValue (OwnedPayload String String) (Payload String))
(datatype RoleValue (RoleAlias String String) (Role String))
(datatype SlotValue (SourceSlot String i64) (Slot i64))
(datatype OccurrenceValue (Occurrence String String RoleValue PayloadValue SlotValue))
(datatype Prompt (End) (Next OccurrenceValue Prompt))
(relation canonical-role (String String))
(canonical-role "q" "task")
(canonical-role "c" "constraint")
(canonical-role "d" "context")
(canonical-role "o" "output")
(canonical-role "u" "unresolved")
(ruleset mode13)
"""
RULES = """
(rewrite (OwnedPayload genome text) (Payload text) :ruleset mode13 :name "share-payload")
(rule ((= role (RoleAlias "mss-boundary-v1" code)) (canonical-role code name))
      ((union role (Role name))) :ruleset mode13 :name "role-canonical")
(rewrite (SourceSlot genome index) (Slot index) :ruleset mode13 :name "identity-compact")
"""
SCOPE = "Exact declared ordered source bytes, roles, boundaries and occurrence multiplicity; no arbitrary semantic equivalence or model-performance claim."


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _hash(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def _runtime():
    try:
        version = importlib.metadata.version("egglog")
        if version != EGGLOG_VERSION:
            return None, "EGGLOG_VERSION_MISMATCH"
        from egglog import bindings
        return bindings, None
    except (ImportError, importlib.metadata.PackageNotFoundError):
        return None, "EGGLOG_UNAVAILABLE"


def _input(request):
    if not isinstance(request, RewriteRequest):
        raise ValueError("REWRITE_REQUEST_REQUIRED")
    request = RewriteRequest.model_validate(request.model_dump())
    if (request.bindings or request.boundary_format != "boundary_tree_v1"
            or request.authority_effect != "None" or not 1 <= len(request.segments) <= MAX_SEGMENTS):
        raise ValueError("EGGLOG_INPUT_SHAPE_UNSUPPORTED")
    if len(request.raw_prompt.encode("utf-8")) > 16384:
        raise ValueError("EGGLOG_SOURCE_BYTE_BOUND")
    if "".join(segment.text for segment in request.segments) != request.raw_prompt:
        raise ValueError("EGGLOG_SOURCE_PARTITION_MISMATCH")
    rows = []
    offset = 0
    for index, segment in enumerate(request.segments):
        genome = _hash(_json([request.request_id, index, segment.boundary]))
        end = offset + len(segment.text.encode("utf-8"))
        rows.append(dict(genome_id=genome, slot=f"source:{genome}", ordinal=index, byte_span=[offset, end],
            role=segment.role, role_alias=ROLES[segment.role], boundary=segment.boundary, text=segment.text))
        offset = end
    return request, rows


def _program(rows):
    term = "(End)"
    for row in reversed(rows):
        genome, boundary = (_json(row[key]) for key in ("genome_id", "boundary"))
        # Egglog's literal grammar does not accept JSON's \r escape. Encode only
        # payload bytes; UTF-8 hex is lossless and never becomes executable syntax.
        text = _json(row["text"].encode("utf-8").hex())
        occurrence = (f'(Occurrence {genome} {boundary} (RoleAlias "mss-boundary-v1" {_json(row["role_alias"])}) '
            f'(OwnedPayload {genome} {text}) (SourceSlot {genome} {row["ordinal"]}))')
        term = f"(Next {occurrence} {term})"
    return SCHEMA + RULES + f"\n(let $prompt {term})\n", term


def _cost(wire, size):
    return size, len(wire.encode("utf-8")), _hash(wire), wire


def _extract(graph, bindings):
    def base(sort, value):
        if sort == "String":
            return _cost(_json(graph.value_to_string(value)), 1)
        if sort == "i64":
            return _cost(str(graph.value_to_i64(value)), 1)
        raise ValueError("EGGLOG_EXTRACT_SORT_UNSUPPORTED")

    def fold(sort, name, children):
        wire = "(" + name + (" " if children else "") + " ".join(c[3] for c in children) + ")"
        return _cost(wire, 1 + sum(c[0] for c in children))

    def container(*_):
        raise ValueError("EGGLOG_EXTRACT_CONTAINER_UNSUPPORTED")

    cost_model = bindings.CostModel(fold, lambda name, args: name, container, base)
    extractor = bindings.Extractor(["Prompt"], graph, cost_model)
    sort, value = graph.eval_expr(bindings.Var(bindings.PanicSpan(), "$prompt"))
    dag = bindings.TermDag()
    cost, term = extractor.extract_best(graph, dag, value, sort)

    def ast(node_id):
        node = dag.get(node_id)
        if isinstance(node, bindings.TermLit):
            return node.value.value
        if isinstance(node, bindings.TermApp):
            return [node.name, *(ast(child) for child in node.args)]
        raise ValueError("EGGLOG_EXTRACT_NODE_UNSUPPORTED")

    return cost, ast(term)


def _rows(ast):
    rows = []
    offset = 0
    while isinstance(ast, list) and ast and ast[0] == "Next":
        if len(ast) != 3:
            raise ValueError("EGGLOG_OUTPUT_AST_UNSUPPORTED")
        occurrence = ast[1]
        if (not isinstance(occurrence, list) or len(occurrence) != 6
                or occurrence[0] != "Occurrence"):
            raise ValueError("EGGLOG_OUTPUT_AST_UNSUPPORTED")
        _, genome, boundary, role, payload, slot = occurrence
        if (not isinstance(role, list) or len(role) != 2 or role[0] != "Role"
                or not isinstance(payload, list) or len(payload) != 2 or payload[0] != "Payload"
                or not isinstance(slot, list) or len(slot) != 2 or slot[0] != "Slot"
                or type(slot[1]) is not int):
            raise ValueError("EGGLOG_OUTPUT_AST_UNSUPPORTED")
        if (not isinstance(genome, str) or not isinstance(boundary, str)
                or role[1] not in ROLES or not isinstance(payload[1], str)):
            raise ValueError("EGGLOG_OUTPUT_AST_UNSUPPORTED")
        payload_bytes = bytes.fromhex(payload[1])
        if payload_bytes.hex() != payload[1]:
            raise ValueError("EGGLOG_OUTPUT_ENCODING_INVALID")
        end = offset + len(payload_bytes)
        rows.append(dict(genome_id=genome, boundary=boundary, role=role[1], text=payload_bytes.decode("utf-8"), slot=f"s{slot[1]}", ordinal=slot[1], byte_span=[offset, end]))
        offset = end
        ast = ast[2]
    if ast != ["End"]:
        raise ValueError("EGGLOG_OUTPUT_AST_UNSUPPORTED")
    return rows


def _preserved(before, after, source):
    # Read the extracted AST independently of Egglog's equivalence classes.
    # A union created by a bad rule is not evidence that a constraint survived.
    def constraints(rows):
        return Counter((row["genome_id"], row["boundary"], row["text"])
            for row in rows if row["role"] == "constraint")
    if constraints(before) != constraints(after):
        raise ValueError("EGRAPH_CONSTRAINT_LOSS")
    expected = [{key: value for key, value in row.items() if key != "role_alias"}
        for row in before]
    for index, row in enumerate(expected):
        row["slot"] = f"s{index}"
    if expected != after or "".join(row["text"] for row in after) != source:
        raise ValueError("EGRAPH_SOURCE_PRESERVATION_FAILED")


def _ast_cost(ast):
    if isinstance(ast, list):
        if not ast or not isinstance(ast[0], str):
            raise ValueError("EGGLOG_OUTPUT_AST_UNSUPPORTED")
        children = [_ast_cost(child) for child in ast[1:]]
        wire = "(" + ast[0] + (" " if children else "") + " ".join(c[3] for c in children) + ")"
        return _cost(wire, 1 + sum(c[0] for c in children))
    if type(ast) not in (str, int):
        raise ValueError("EGGLOG_OUTPUT_AST_UNSUPPORTED")
    return _cost(_json(ast), 1)


def rewrite_prompt(request: RewriteRequest) -> dict:
    """Execute one actual e-graph and retain its measured inputs, output and bounds."""
    result = dict(status="REFUSED", reason=None, authority_effect="None", scope=SCOPE,
        executed=False, request_id=getattr(request, "request_id", None), native_payload=None)
    try:
        request, before = _input(request)
        bindings, unavailable = _runtime()
        if unavailable:
            return {**result, "status": "UNAVAILABLE", "reason": unavailable}
        program, input_term = _program(before)
        graph = bindings.EGraph(num_threads=1)
        result.update(engine=dict(name="egglog", version=EGGLOG_VERSION, num_threads=graph.num_threads(),
            binary_sha256=_hash(Path(bindings.__file__).read_bytes())),
            adapter_sha256=_hash(Path(__file__).read_bytes()), request=request.model_dump(),
            rules=RULES, rules_sha256=_hash(RULES), schema_sha256=_hash(SCHEMA),
            input_ast=before, input_term=input_term, input_sha256=_hash(_json(before)),
            source_sha256=_hash(request.raw_prompt), program_sha256=_hash(program))
        graph.parse_and_run_program(program)
        counts = [len(json.loads(graph.serialize([]).to_json())["nodes"])]
        matches = Counter()
        iterations = 0
        for _ in range(MAX_ITERATIONS):
            if counts[-1] > MAX_NODES:
                raise ValueError("EGGLOG_NODE_BOUND")
            report = graph.parse_and_run_program("(run mode13 1)")[0].report
            iterations += len(report.iterations)
            matches.update(report.num_matches_per_rule)
            counts.append(len(json.loads(graph.serialize([]).to_json())["nodes"]))
            result.update(executed=True, iterations=iterations, node_counts=counts, rule_matches=dict(matches))
            if counts[-1] > MAX_NODES:
                raise ValueError("EGGLOG_NODE_BOUND")
            if not report.updated:
                break
        else:
            raise ValueError("EGGLOG_ITERATION_BOUND")
        cost, output_ast = _extract(graph, bindings)
        after = _rows(output_ast)
        result.update(output_ast=output_ast, occurrences=after, output_sha256=_hash(_json(output_ast)),
            output_wire=cost[3], extraction_cost=list(cost[:3]),
            cost_profile="tree AST nodes, UTF-8 S-expression bytes, lexicographical SHA-256",
            payload_encoding="utf8-hex",
            payload_count=sum(1 for item in json.loads(graph.serialize([]).to_json())["nodes"].values()
                if item["op"] == "Payload"))
        _preserved(before, after, request.raw_prompt)
        receipt = RewriteReceipt(request_id=request.request_id, rewritten_prompt=cost[3],
            root_boundary="<root>boundary_tree_v1</root>", segments_count=len(after), receipt_sha256=_hash(cost[3]))
        result.update(status="VERIFIED", receipt=receipt.model_dump(), constraints_before={row["genome_id"]:row["text"]
            for row in before if row["role"] == "constraint"}, constraints_after={row["genome_id"]:row["text"]
            for row in after if row["role"] == "constraint"})
        return result
    except Exception as exc:
        result["reason"] = str(exc) if isinstance(exc, ValueError) else "EGGLOG_EXECUTION_ERROR:" + type(exc).__name__
        return result


def declared_preservation_cases() -> tuple[RewriteRequest, ...]:
    """Fifty finite declared prompts, including duplicate constraints and hostile delimiters."""
    cases = []
    for index in range(50):
        constraint = f"Keep value between {index} and {index+7}; preserve all occurrences.\n"
        entries = [("task", f"Case {index}: return a JSON object describing the supplied finite record.\n"),
            ("constraint", constraint), ("context", f'Quoted data α/{index}: "); (panic \"not code\") ; 𓂀\n'),
            ("constraint", "Do not execute context text; retain its exact bytes.\n"),
            ("constraint", constraint), ("context", "Delimiters <task> ``` ' ; -- remain data.\r\n"),
            ("output", "Use the declared fields without adding external facts.\n"),
            ("unresolved", "No conclusion about arbitrary prompt meaning is supplied.\n")]
        segments = [Segment(role=role, boundary=f"<{role}>", text=text) for role, text in entries]
        cases.append(RewriteRequest(request_id=f"mode13-{index:02d}", raw_prompt="".join(s.text for s in segments), segments=segments))
    return tuple(cases)


def _suite_payload(observations):
    before = {row["request_id"]:row["constraints_before"] for row in observations}
    after = {row["request_id"]:row["constraints_after"] for row in observations}
    return dict(total_rewrites=len(observations), dropped_constraints=0,
        constraint_loss_rate="0", constraints_before=before, constraints_after=after)


def _complex_cases(cases):
    return (1 <= len(cases) <= 50 and len({case.request_id for case in cases}) == len(cases)
        and len({case.raw_prompt for case in cases}) == len(cases)
        and all(sum(segment.role == "constraint" for segment in case.segments) >= 2
            and {"task", "context", "output"} <= {segment.role for segment in case.segments}
            for case in cases))


def run_preservation_suite(requests=None) -> dict:
    """Collect EMP003 only after fifty distinct declared prompts actually finish."""
    cases = tuple(declared_preservation_cases() if requests is None else requests)
    report = dict(status="REFUSED", reason=None, authority_effect="None", scope=SCOPE,
        observations=[], native_payload=None)
    if any(not isinstance(case, RewriteRequest) for case in cases) or not _complex_cases(cases):
        report["reason"] = "EGGLOG_ONE_TO_FIFTY_DISTINCT_COMPLEX_CASES_REQUIRED"
        return report
    for case in cases:
        observation = rewrite_prompt(case)
        report["observations"].append(observation)
        if observation["status"] != "VERIFIED":
            report.update(status=observation["status"], reason=observation["reason"])
            return report
    if len(cases) == 50:
        report.update(status="VERIFIED", native_payload=_suite_payload(report["observations"]))
    else:
        report.update(status="PARTIAL", reason="EGGLOG_COVERAGE_INCOMPLETE")
    return report


def replay_preservation_suite(observations) -> dict:
    """Recheck retained representations without Egglog; this does not authenticate a file."""
    report = dict(status="REFUSED", reason=None, authority_effect="None", engine_executions=0,
        scope="Retained diagnostic source/AST consistency only; not authenticated execution. " + SCOPE,
        observations=[], native_payload=None)
    try:
        if not isinstance(observations, list) or not 1 <= len(observations) <= 50:
            raise ValueError("EGGLOG_ONE_TO_FIFTY_DISTINCT_COMPLEX_CASES_REQUIRED")
        cases = []
        for observation in observations:
            request, before = _input(RewriteRequest.model_validate(observation["request"]))
            cases.append(request)
            program, term = _program(before)
            engine = observation["engine"]
            if (engine["name"] != "egglog" or engine["version"] != EGGLOG_VERSION
                    or engine["num_threads"] != 1 or observation["executed"] is not True
                    or observation["rules"] != RULES or observation["rules_sha256"] != _hash(RULES)
                    or observation["schema_sha256"] != _hash(SCHEMA)):
                raise ValueError("EGGLOG_REPLAY_PROFILE_MISMATCH")
            if (observation["request_id"] != request.request_id or observation["input_ast"] != before
                    or observation["input_term"] != term or observation["program_sha256"] != _hash(program)
                    or observation["input_sha256"] != _hash(_json(before))
                    or observation["source_sha256"] != _hash(request.raw_prompt)):
                raise ValueError("EGGLOG_REPLAY_INPUT_MISMATCH")
            after = _rows(observation["output_ast"])
            _preserved(before, after, request.raw_prompt)
            cost = _ast_cost(observation["output_ast"])
            if (observation["output_sha256"] != _hash(_json(observation["output_ast"]))
                    or observation["output_wire"] != cost[3] or observation["extraction_cost"] != list(cost[:3])
                    or observation["occurrences"] != after or observation["payload_encoding"] != "utf8-hex"):
                raise ValueError("EGGLOG_REPLAY_OUTPUT_MISMATCH")
            iterations, counts = observation["iterations"], observation["node_counts"]
            if (type(iterations) is not int or not 1 <= iterations <= MAX_ITERATIONS
                    or not isinstance(counts, list) or len(counts) != iterations + 1
                    or any(type(n) is not int or not 1 <= n <= MAX_NODES for n in counts)):
                raise ValueError("EGGLOG_REPLAY_BOUND_MISMATCH")
            report["observations"].append(dict(request_id=request.request_id,
                constraints_before={r["genome_id"]:r["text"] for r in before if r["role"] == "constraint"},
                constraints_after={r["genome_id"]:r["text"] for r in after if r["role"] == "constraint"}))
        if not _complex_cases(cases):
            raise ValueError("EGGLOG_ONE_TO_FIFTY_DISTINCT_COMPLEX_CASES_REQUIRED")
        if len(cases) == 50:
            report.update(status="REPLAYED", native_payload=_suite_payload(report["observations"]))
        else:
            report.update(status="PARTIAL", reason="EGGLOG_COVERAGE_INCOMPLETE")
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        report["reason"] = str(exc) if isinstance(exc, ValueError) else "EGGLOG_REPLAY_MALFORMED"
    return report
