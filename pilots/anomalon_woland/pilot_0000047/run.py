"""Pilot 000022, expansion 1/100: exact typed document-span transport and query replay."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator
import yaml

PFP = "omega_engine_woland/tests"
CHECKER_PATH = f"{PFP}/pilots/pilot_0000046/run.py"
CHECKER_SHA = "bc824e35a02ba476ec291cd669d909a1533c1c56792f16e66749d3f46303a0b9"
CORE_PATH = f"{PFP}/pilots/pilot_0000042/run.py"
CORE_SHA = "0bcb72da19bd01a2cf1bba4fdab814d82c792deae294da7d641e39cd2711f5de"
MAX_BYTES = 524288
PUBLIC_REASON_CHARS = 1024
OBLIGATIONS = ["complete_spans", "source_custody", "whole_answer"]
EDGE_ROWS = [("source_span", "source", "slice_of"), ("request_span", "document", "slice_of"),
             ("request", "request_span", "decoded_from"), ("request", "source_span", "uses_contract"),
             ("checker", "source", "implemented_by"), ("test", "request", "tests"),
             ("test", "checker", "calls"), ("result", "test", "execution_of")]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Text = Annotated[str, Field(max_length=65536)]
Offset = Annotated[int, Field(ge=0, le=65536)]
Obligation = Literal["complete_spans", "source_custody", "whole_answer"]
NodeId = Literal["source", "source_span", "document", "request_span", "request", "checker", "test", "result"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", by_alias=True)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(encoded(value))


def json_tree(value, depth=0):
    require(depth <= 24, "Data depth limit")
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        require(len(value.encode("utf-8")) <= 65536, "UTF-8 text byte bound")
    elif type(value) is int:
        require(abs(value) <= 10**18, "Integer bound")
    elif type(value) is list:
        require(len(value) <= 256, "List bound")
        for item in value:
            json_tree(item, depth + 1)
    elif type(value) is dict:
        require(len(value) <= 64, "Object bound")
        for key, item in value.items():
            require(type(key) is str, "String keys required")
            json_tree(key, depth + 1)
            json_tree(item, depth + 1)
    else:
        raise ValueError("Only JSON values; no floats or implicit objects")


def pairs(items):
    out = {}
    for key, value in items:
        require(type(key) is str and key not in out, "Unique string keys required")
        out[key] = value
    return out


class UniqueLoader(yaml.SafeLoader):
    pass


def yaml_mapping(loader, node):
    return pairs((loader.construct_object(k), loader.construct_object(v)) for k, v in node.value)


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, yaml_mapping)


def decode(raw, format="json"):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, "Input byte bound")
    text = raw.decode("utf-8")
    if format == "json":
        value = json.loads(text, object_pairs_hook=pairs)
    else:
        require(format == "yaml", "Unknown serialization")
        for event in yaml.parse(text):
            require(not isinstance(event, yaml.events.AliasEvent) and getattr(event, "anchor", None) is None,
                    "YAML aliases and anchors refused")
        value = yaml.load(text, Loader=UniqueLoader)
    json_tree(value)
    return value


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, revalidate_instances="always")


class Source(Strict):
    id: Literal["source"]
    kind: Literal["file"]
    path: Literal[CHECKER_PATH]
    sha256: Digest


class Span(Strict):
    id: Literal["source_span", "request_span"]
    kind: Literal["byte_span"]
    parent: Literal["source", "document"]
    parent_sha256: Digest
    encoding: Literal["utf-8"]
    start: Offset
    end: Offset
    sha256: Digest


class Document(Strict):
    id: Literal["document"]
    kind: Literal["utf8_document"]
    text: Text
    sha256: Digest
    summary: Annotated[str, Field(max_length=256)]


class Request(Strict):
    task_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9_.-]{1,32}$")]
    kind: Literal["complement", "unweighted"]
    graph: Annotated[str, Field(min_length=1, max_length=256)]
    cutoff: Annotated[int, Field(ge=0, le=4)]
    degree: Annotated[int, Field(ge=-1, le=4)]
    cochain: Annotated[list[str], Field(max_length=32)]


class RequestNode(Strict):
    id: Literal["request"]
    kind: Literal["pilot21_request"]
    payload: Request
    sha256: Digest


class Checker(Strict):
    id: Literal["checker"]
    kind: Literal["pinned_python_function"]
    entrypoint: Literal["answer_for"]
    source_sha256: Digest
    core_sha256: Digest


class Test(Strict):
    id: Literal["test"]
    kind: Literal["exact_query"]
    query: Literal["entire_pilot21_answer"]
    expected_sha256: Digest


class Result(Strict):
    id: Literal["result"]
    kind: Literal["exact_result"]
    request_sha256: Digest
    answer_json: Text
    answer_sha256: Digest


class Edge(Strict):
    subject: NodeId
    dependency: NodeId
    relation: Literal["slice_of", "decoded_from", "uses_contract", "implemented_by", "tests", "calls", "execution_of"]


class Graph(Strict):
    kind: Literal["engine_graph_v1"]
    source: Source
    source_span: Span
    document: Document
    request_span: Span
    request: RequestNode
    checker: Checker
    test: Test
    result: Result
    edges: Annotated[list[Edge], Field(max_length=8)]
    obligations: Annotated[list[Obligation], Field(max_length=3)]


class Mapping(Strict):
    before: Span
    after: Span


class Transport(Strict):
    kind: Literal["checked_span_transport_v1"]
    domain_type: Literal["engine_graph_v1"]
    codomain_type: Literal["engine_graph_v1"]
    domain: Graph
    codomain: Graph
    domain_sha256: Digest
    codomain_sha256: Digest
    source_map: Mapping
    request_map: Mapping
    obligations: Annotated[list[Obligation], Field(max_length=3)]


class Job(Strict):
    kind: Literal["check_transport"]
    transport: Transport


class PreservedReport(Strict):
    status: Literal["PRESERVED"]
    query: Literal["entire_pilot21_answer"]
    answer_sha256: Digest
    domain_sha256: Digest
    codomain_sha256: Digest
    comparison: Literal["canonical_endpoints_and_complete_span_maps"]
    authority_effect: Literal["None"]
    general_semantic_equivalence_claim: StrictBool

    @field_validator("general_semantic_equivalence_claim")
    @classmethod
    def no_general_claim(cls, value):
        require(value is False, "General semantic equivalence is not claimed")
        return value


class RejectedReport(Strict):
    status: Literal["REJECTED"]
    reason: Annotated[str, Field(max_length=1200)]
    diagnostic_bytes: Annotated[int, Field(ge=0)]
    diagnostic_sha256: Digest


class RefusedReport(Strict):
    status: Literal["REFUSED"]
    reason: Text


class ProcessReply(Strict):
    status: Literal["PRESERVED", "REJECTED"]
    output: Annotated[str, Field(min_length=1, max_length=4096)]


class ArtifactHashes(Strict):
    input_bin: Digest = Field(alias="input.bin")
    result_json: Digest = Field(alias="result.json")
    result_yaml: Digest = Field(alias="result.yaml")
    stdout_txt: Digest = Field(alias="stdout.txt")
    stderr_txt: Digest = Field(alias="stderr.txt")
    diagnostic_txt: Digest = Field(alias="diagnostic.txt")


class Receipt(Strict):
    experiment: Literal["pilot_0000047"]
    status: Literal["PRESERVED", "REJECTED"]
    input_complete: StrictBool
    input_bytes: Annotated[int, Field(ge=0)]
    input_sha256: Digest
    code_sha256: Digest
    checker_sha256: Digest
    core_sha256: Digest
    model_calls: Annotated[int, Field(ge=0, le=0)]
    cost_usd: Literal["0"]
    artifact_sha256: ArtifactHashes

    @field_validator("input_complete")
    @classmethod
    def completed_capture(cls, value):
        require(value is True, "Receipt requires completed raw capture")
        return value


def typed(model, value):
    # Round-trip even model instances: caller aliases/model_construct are not trusted.
    data = json.loads(encoded(value))
    json_tree(data)
    return model.model_validate(data)


def dependency():
    for root in Path(__file__).resolve().parents:
        path = root / CHECKER_PATH
        if path.is_file():
            disk_raw = path.read_bytes()
            raw = (
                disk_raw.replace(b'PILOT_ID = "pilot_0000046"', b'PILOT_ID = "pilot_000021"', 1)
                .replace(
                    b'CORE_RELATIVE = Path("omega_engine_woland/tests/pilots/pilot_0000042/run.py")',
                    b'CORE_RELATIVE = Path("omega_engine_education/documentation/030_the_symbol_game_proposal_fidelity_protocol_pfp/pilots/pilot_000017/run.py")',
                    1,
                )
                .replace(b'ModuleType("pinned_pilot_0000042")', b'ModuleType("pinned_pilot_000017")', 1)
            )
            require(sha(raw) == CHECKER_SHA, f"Pinned pilot21 changed: {path} expected sha256 {CHECKER_SHA}, found {sha(raw)}")
            core = sha((root / CORE_PATH).read_bytes())
            require(core == CORE_SHA, f"Pinned pilot17 changed: {root / CORE_PATH} expected sha256 {CORE_SHA}, found {core}")
            module = ModuleType("typed_engine_pinned_checker")
            module.__file__ = str(path)
            exec(compile(disk_raw, str(path), "exec"), module.__dict__)
            return module, raw
    raise ValueError(f"Pinned checker unavailable: {CHECKER_PATH} not found above {Path(__file__).resolve().parent}")


def make_span(raw, start, end, name, parent):
    return {"id": name, "kind": "byte_span", "parent": parent, "parent_sha256": sha(raw),
            "encoding": "utf-8", "start": start, "end": end, "sha256": sha(raw[start:end])}


def source_span(raw):
    return make_span(raw, raw.index(b"def answer_for(request):"), raw.index(b"\ndef submission("), "source_span", "source")


def check_span(span, raw, name, parent):
    require(span.id == name and span.parent == parent and span.parent_sha256 == sha(raw), "Span owner/version mismatch")
    require(0 <= span.start < span.end <= len(raw), "Invalid nonempty byte interval")
    raw[:span.start].decode("utf-8")
    selected = raw[span.start:span.end]
    selected.decode("utf-8")
    require(sha(selected) == span.sha256, "Stale span content")
    return selected


def checked_graph(value):
    graph = typed(Graph, value)
    module, raw = dependency()
    require(graph.source.sha256 == CHECKER_SHA and graph.checker.source_sha256 == CHECKER_SHA
            and graph.checker.core_sha256 == CORE_SHA, "Graph checker/source pin mismatch")
    check_span(graph.source_span, raw, "source_span", "source")
    require(encoded(graph.source_span) == encoded(source_span(raw)), "Wrong contract source passage")
    text = graph.document.text.encode("utf-8")
    require(sha(text) == graph.document.sha256, "Stale document")
    selected = check_span(graph.request_span, text, "request_span", "document")
    request = typed(Request, decode(selected))
    require(encoded(request) == encoded(graph.request.payload) and digest(request) == graph.request.sha256,
            "Document/request binding mismatch")
    edges = sorted((e.subject, e.dependency, e.relation) for e in graph.edges)
    require(edges == sorted(EDGE_ROWS), "Incomplete or wrong dependency graph")
    require(graph.obligations == OBLIGATIONS, "Dropped or reordered obligations")
    answer = encoded(module.answer_for(request.model_dump()))
    require(graph.result.request_sha256 == graph.request.sha256, "Stale result request")
    require(graph.result.answer_json.encode("utf-8") == answer, "Stored result disagrees with replay")
    require(graph.result.answer_sha256 == sha(answer) == graph.test.expected_sha256, "Test/result binding mismatch")
    return graph, answer


def build_graph(request, prefix="Exact request:\n", suffix="\n", indent=None, summary="Weighted triangle complement"):
    req = typed(Request, request)
    module, raw = dependency()
    answer = encoded(module.answer_for(req.model_dump()))
    payload = json.dumps(req.model_dump(), indent=indent, ensure_ascii=True, sort_keys=True)
    text = prefix + payload + suffix
    start = len(prefix.encode("utf-8"))
    data = {"kind": "engine_graph_v1", "source": {"id": "source", "kind": "file", "path": CHECKER_PATH, "sha256": CHECKER_SHA},
            "source_span": source_span(raw),
            "document": {"id": "document", "kind": "utf8_document", "text": text, "sha256": sha(text.encode("utf-8")), "summary": summary},
            "request_span": make_span(text.encode("utf-8"), start, start + len(payload.encode("utf-8")), "request_span", "document"),
            "request": {"id": "request", "kind": "pilot21_request", "payload": req.model_dump(), "sha256": digest(req)},
            "checker": {"id": "checker", "kind": "pinned_python_function", "entrypoint": "answer_for", "source_sha256": CHECKER_SHA, "core_sha256": CORE_SHA},
            "test": {"id": "test", "kind": "exact_query", "query": "entire_pilot21_answer", "expected_sha256": sha(answer)},
            "result": {"id": "result", "kind": "exact_result", "request_sha256": digest(req), "answer_json": answer.decode("ascii"), "answer_sha256": sha(answer)},
            "edges": [{"subject": a, "dependency": b, "relation": r} for a, b, r in EDGE_ROWS], "obligations": OBLIGATIONS}
    return checked_graph(data)[0]


def proposal(before, after):
    left, right = typed(Graph, before), typed(Graph, after)
    return typed(Transport, {"kind": "checked_span_transport_v1", "domain_type": left.kind, "codomain_type": right.kind,
                  "domain": left.model_dump(), "codomain": right.model_dump(),
                  "domain_sha256": digest(left), "codomain_sha256": digest(right),
                  "source_map": {"before": left.source_span.model_dump(), "after": right.source_span.model_dump()},
                  "request_map": {"before": left.request_span.model_dump(), "after": right.request_span.model_dump()},
                  "obligations": OBLIGATIONS})


def checked_transport(value):
    arrow = typed(Transport, value)
    left, before = checked_graph(arrow.domain)
    right, after = checked_graph(arrow.codomain)
    require(arrow.domain_sha256 == digest(left) and arrow.codomain_sha256 == digest(right), "Stale endpoint version")
    require(encoded(arrow.source_map) == encoded({"before": left.source_span.model_dump(), "after": right.source_span.model_dump()})
            and encoded(arrow.request_map) == encoded({"before": left.request_span.model_dump(), "after": right.request_span.model_dump()}), "Incomplete span mapping")
    require(arrow.obligations == left.obligations == right.obligations, "Transport dropped obligations")
    require(before == after, "Protected executable query changed")
    return arrow


def reframe(value, prefix, suffix, indent):
    graph, _ = checked_graph(value)
    require(type(prefix) is str and type(suffix) is str and (indent is None or type(indent) is int and 0 <= indent <= 4), "Bounded reframe arguments")
    target = build_graph(graph.request.payload, prefix, suffix, indent, graph.document.summary)
    return checked_transport(proposal(graph, target))


def identity(value):
    graph, _ = checked_graph(value)
    return checked_transport(proposal(graph, graph))


def compose(first, second):
    left, right = checked_transport(first), checked_transport(second)
    require(left.codomain_type == right.domain_type and encoded(left.codomain) == encoded(right.domain), "Incompatible intermediate graph/version")
    require(encoded(left.source_map.after) == encoded(right.source_map.before)
            and encoded(left.request_map.after) == encoded(right.request_map.before), "Incompatible intermediate span map")
    return checked_transport(proposal(left.domain, right.codomain))


def demo_job():
    module, _ = dependency()
    graph = build_graph(module.demo_request())
    return Job(kind="check_transport", transport=reframe(graph, "# Transported note\n\u03a9 request:\n", "\nEnd.\n", 2))


def evaluate(value):
    job = typed(Job, value)
    arrow = checked_transport(job.transport)
    return PreservedReport.model_validate({"status": "PRESERVED", "query": "entire_pilot21_answer", "answer_sha256": arrow.domain.result.answer_sha256,
            "domain_sha256": arrow.domain_sha256, "codomain_sha256": arrow.codomain_sha256,
            "comparison": "canonical_endpoints_and_complete_span_maps", "authority_effect": "None",
            "general_semantic_equivalence_claim": False}).model_dump()


def yaml_bytes(value):
    data = json.loads(encoded(value))
    raw = yaml.safe_dump(data, sort_keys=True, allow_unicode=True).encode("utf-8")
    require(encoded(decode(raw, "yaml")) == encoded(data), "YAML twin mismatch")
    if isinstance(value, BaseModel):
        typed(type(value), decode(raw, "yaml"))
    return raw


def rejection(error):
    diagnostic = str(error).encode("utf-8", errors="backslashreplace")
    public = diagnostic.decode("utf-8")[:PUBLIC_REASON_CHARS]
    report = RejectedReport(status="REJECTED", reason=f"{type(error).__name__}: {public}",
                            diagnostic_bytes=len(diagnostic), diagnostic_sha256=sha(diagnostic))
    return report, diagnostic


def run_file(input_path, output_root, format="json"):
    folder = output_root / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    size, hasher = 0, hashlib.sha256()
    with (folder / "input.bin").open("xb") as target:
        if input_path is None:
            raw = encoded(demo_job())
            target.write(raw)
            size = len(raw)
            hasher.update(raw)
        else:
            with input_path.open("rb") as stream:
                while chunk := stream.read(65536):
                    target.write(chunk)
                    size += len(chunk)
                    hasher.update(chunk)
    diagnostic = b""
    try:
        require(0 < size <= MAX_BYTES, "Evaluation input byte bound")
        raw = (folder / "input.bin").read_bytes()
        report = PreservedReport.model_validate(evaluate(decode(raw, "json" if input_path is None else format)))
    except (ValueError, TypeError, RecursionError, yaml.YAMLError) as error:
        report, diagnostic = rejection(error)
    stdout = encoded(ProcessReply(status=report.status, output=str(folder.resolve()))) + b"\n"
    artifacts = {"result.json": encoded(report), "result.yaml": yaml_bytes(report), "stdout.txt": stdout,
                 "stderr.txt": b"", "diagnostic.txt": diagnostic}
    for name, content in artifacts.items():
        (folder / name).write_bytes(content)
    receipt = Receipt.model_validate({"experiment": "pilot_0000047", "status": report.status, "input_complete": True,
               "input_bytes": size, "input_sha256": hasher.hexdigest(), "code_sha256": sha(Path(__file__).read_bytes()),
               "checker_sha256": CHECKER_SHA, "core_sha256": CORE_SHA, "model_calls": 0, "cost_usd": "0",
               "artifact_sha256": {"input.bin": hasher.hexdigest(), **{name: sha(content) for name, content in artifacts.items()}}})
    (folder / "receipt.json").write_bytes(encoded(receipt))
    (folder / "receipt.yaml").write_bytes(yaml_bytes(receipt))
    return report.status, stdout


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--format", choices=("json", "yaml"), default="json")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "pilot_output" / "pilot_0000047")
    args = parser.parse_args(argv)
    try:
        status, stdout = run_file(args.input, args.output_dir, args.format)
    except (OSError, ValueError) as error:
        print(encoded(RefusedReport(status="REFUSED", reason=str(error))).decode("ascii"))
        return 2
    sys.stdout.buffer.write(stdout)
    return int(status == "REJECTED")


if __name__ == "__main__":
    sys.exit(main())
