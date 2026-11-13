"""Independent finite keyed-glyph packet experiment; no provider or authority."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Annotated, Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, field_validator
import yaml

MAX_INPUT = 262144
MAX_PAYLOAD = 4096
LEGEND = "Local nibble codec: two glyphs per byte, high nibble first; key maps nibble to alphabet index. Task and role are data, not permission."
IDENTITY = list(range(16))
DEFAULT_ALPHABET = [chr(0x13000+i) for i in range(16)]
Digest = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
Count = Annotated[StrictInt, Field(ge=0)]
Small = Annotated[StrictInt, Field(ge=-10000, le=10000)]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def tree(value, depth=0):
    require(depth <= 16, "Tree depth limit")
    if type(value) is str:
        require(len(value.encode("utf-8")) <= MAX_INPUT, "Text byte limit")
    elif type(value) is list:
        require(len(value) <= 8192, "Array limit")
        for item in value:
            tree(item, depth+1)
    elif type(value) is dict:
        require(len(value) <= 32 and all(type(k) is str for k in value), "Object keys/size")
        for key, item in value.items():
            tree(key, depth+1)
            tree(item, depth+1)
    elif type(value) is int:
        require(abs(value) <= 10**18, "Integer size limit")
    else:
        require(value is None or type(value) is bool, "JSON primitive type")


def pairs(items):
    result = {}
    for key, value in items:
        require(type(key) is str and key not in result, "Duplicate/nontext key")
        result[key] = value
    return result


class Loader(yaml.SafeLoader):
    pass


def mapping(loader, node):
    return pairs([(loader.construct_object(k), loader.construct_object(v)) for k, v in node.value])


Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def load(raw, format_name):
    require(type(raw) is bytes and len(raw) <= MAX_INPUT, "Input byte limit")
    text = raw.decode("utf-8")
    if format_name == "json":
        value = json.loads(text, object_pairs_hook=pairs)
    else:
        require(format_name == "yaml", "Unknown format")
        require(not any(isinstance(token, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken, yaml.tokens.TagToken)) for token in yaml.scan(text)), "YAML aliases/anchors/tags forbidden")
        value = yaml.load(text, Loader=Loader)
    tree(value)
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, revalidate_instances="always")


class Query(StrictModel):
    task_id: Annotated[StrictStr, Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")]
    role: Literal["data"]
    operation: Literal["polynomial"]
    data: Annotated[StrictStr, Field(max_length=128)]
    coefficients: Annotated[list[Small], Field(min_length=1, max_length=9)]
    x: Annotated[StrictInt, Field(ge=-16, le=16)]


class Permutation(StrictModel):
    image: Annotated[list[Annotated[StrictInt, Field(ge=0, le=15)]], Field(min_length=16, max_length=16)]

    @field_validator("image")
    @classmethod
    def bijective(cls, value):
        require(sorted(value) == IDENTITY, "Key/permutation must be bijective")
        return value


class Packet(StrictModel):
    dialect: Literal["local-nibble-glyph-1"]
    legend: Literal[LEGEND]
    task_id: Annotated[StrictStr, Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")]
    role: Literal["data"]
    alphabet: Annotated[list[StrictStr], Field(min_length=16, max_length=16)]
    key: Permutation
    payload_bytes: Annotated[StrictInt, Field(ge=1, le=MAX_PAYLOAD)]
    payload_sha256: Digest
    glyphs: Annotated[StrictStr, Field(min_length=2, max_length=2*MAX_PAYLOAD)]

    @field_validator("alphabet")
    @classmethod
    def symbols(cls, value):
        require(len(set(value)) == 16, "Alphabet must contain16distinct symbols")
        for symbol in value:
            require(len(symbol) == 1 and symbol.isprintable() and not symbol.isspace() and symbol not in '\\"', "One printable nonspace scalar per symbol; quote/backslash excluded")
            symbol.encode("utf-8")
        return value


class Job(StrictModel):
    packet: Packet
    permutations: Annotated[list[Permutation], Field(max_length=6)]
    comparison: Packet | None


class Answer(StrictModel):
    polynomial_value: StrictInt


class Measure(StrictModel):
    utf8_bytes: Count
    codepoints: Count


class Costs(StrictModel):
    payload: Measure
    body_glyphs: Measure
    body_json: Measure
    alphabet_key_json: Measure
    legend_json: Measure
    framing_json: Measure
    packet_json: Measure
    overhead_bytes: Count
    overhead_codepoints: Count
    tokens: Literal["NOT_MEASURED"]


class Result(StrictModel):
    status: Literal["PRESERVED"]
    packet: Packet
    transformed: Packet
    cumulative: Permutation
    payload_sha256: Digest
    answer: Answer
    before_cost: Costs
    after_cost: Costs
    authority_effect: Literal["None"]
    authentication: Literal["NOT_ESTABLISHED"]
    model_calls: Annotated[StrictInt, Field(ge=0, le=0)]
    cost_microusd: Annotated[StrictInt, Field(ge=0, le=0)]


class Rejected(StrictModel):
    status: Literal["REJECTED"]
    reason: Annotated[StrictStr, Field(max_length=1200)]
    diagnostic_bytes: Count
    diagnostic_sha256: Digest


class Receipt(StrictModel):
    runner_sha256: Digest
    input_bytes: Count
    input_complete: StrictBool
    status: Literal["PRESERVED", "REJECTED"]
    artifacts: dict[StrictStr, Digest]
    authority_effect: Literal["None"]

    @field_validator("input_complete")
    @classmethod
    def complete(cls, value):
        require(value is True, "Completed receipt requires full input")
        return value

    @field_validator("artifacts")
    @classmethod
    def files(cls, value):
        require(set(value) == {"input.bin", "payload.bin", "result.json", "result.yaml", "diagnostic.txt", "stdout.bin", "stderr.bin"}, "Exact artifact set required")
        return value


class Process(StrictModel):
    status: Literal["PRESERVED", "REJECTED", "REFUSED"]
    output: StrictStr | None
    reason: Annotated[StrictStr, Field(max_length=1200)]


def checked(model, value):
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="python")
    tree(value)
    return model.model_validate(json.loads(encoded(value)))


def query(raw):
    require(type(raw) is bytes and 1 <= len(raw) <= MAX_PAYLOAD, "Payload byte bound")
    return checked(Query, load(raw, "json"))


def answer(raw):
    q = query(raw)
    value = 0
    for coefficient in reversed(q.coefficients):
        value = value*q.x + coefficient
    return Answer(polynomial_value=value)


def permutation(value):
    return checked(Permutation, value)


def compose(after, before):
    a, b = permutation(after).image, permutation(before).image
    return Permutation(image=[a[b[i]] for i in IDENTITY])


def inverse(value):
    p = permutation(value).image
    return Permutation(image=[p.index(i) for i in IDENTITY])


def encode(raw, alphabet, key):
    q = query(raw)
    p = permutation(key)
    require(type(alphabet) is list and len(alphabet) == 16 and all(type(ch) is str for ch in alphabet), "Explicit16-symbol string list required")
    Packet.symbols(alphabet)
    body = "".join(alphabet[p.image[nibble]] for byte in raw for nibble in (byte >> 4, byte & 15))
    return checked(Packet, {"dialect": "local-nibble-glyph-1", "legend": LEGEND, "task_id": q.task_id, "role": q.role,
                           "alphabet": alphabet, "key": p.model_dump(), "payload_bytes": len(raw), "payload_sha256": sha(raw), "glyphs": body})


def decode(value):
    packet = checked(Packet, value)
    require(len(packet.glyphs) == 2*packet.payload_bytes, "Glyph count must equal twice the payload bytes")
    nibble_for = {packet.alphabet[packet.key.image[i]]: i for i in IDENTITY}
    require(all(ch in nibble_for for ch in packet.glyphs), "Foreign glyph")
    raw = bytes(16*nibble_for[packet.glyphs[i]] + nibble_for[packet.glyphs[i+1]] for i in range(0, len(packet.glyphs), 2))
    require(len(raw) == packet.payload_bytes and sha(raw) == packet.payload_sha256, "Payload length/hash mismatch")
    q = query(raw)
    require(q.task_id == packet.task_id and q.role == packet.role, "Task/role binding mismatch")
    return raw


def act(value, mapping):
    packet, p = checked(Packet, value), permutation(mapping)
    decode(packet)
    substitution = {packet.alphabet[i]: packet.alphabet[p.image[i]] for i in IDENTITY}
    result = packet.model_dump()
    result["key"] = {"image": [p.image[i] for i in packet.key.image]}
    result["glyphs"] = "".join(substitution[ch] for ch in packet.glyphs)
    return checked(Packet, result)


def measure(raw):
    return Measure(utf8_bytes=len(raw), codepoints=len(raw.decode("utf-8")))


def costs(value):
    packet = checked(Packet, value)
    raw = decode(packet)
    body = encoded(packet.glyphs)
    key = encoded(packet.alphabet) + encoded(packet.key.model_dump())
    legend = encoded(packet.legend)
    wire = encoded(packet.model_dump())
    component_bytes = len(body)+len(key)+len(legend)
    component_points = sum(len(v.decode("utf-8")) for v in (body, key, legend))
    return Costs(payload=measure(raw), body_glyphs=measure(packet.glyphs.encode()), body_json=measure(body),
                 alphabet_key_json=measure(key), legend_json=measure(legend),
                 framing_json=Measure(utf8_bytes=len(wire)-component_bytes, codepoints=len(wire.decode())-component_points),
                 packet_json=measure(wire), overhead_bytes=len(wire)-len(raw), overhead_codepoints=len(wire.decode())-len(raw.decode()), tokens="NOT_MEASURED")


def evaluate(value):
    job = checked(Job, value)
    raw = decode(job.packet)
    expected = answer(raw)
    current = job.packet
    cumulative = Permutation(image=IDENTITY[:])
    for p in job.permutations:
        current = act(current, p)
        cumulative = compose(p, cumulative)
        require(decode(current) == raw, "Permutation lost payload fidelity")
        require(answer(decode(current)) == expected, "Permutation changed protected answer")
    require(current == act(job.packet, cumulative), "Composition packet mismatch")
    if job.comparison is not None:
        proposed = decode(job.comparison)
        require(answer(proposed) == expected, "Protected answer changed")
        require(proposed == raw, "Payload fidelity changed despite equal answer")
    return Result(status="PRESERVED", packet=job.packet, transformed=current, cumulative=cumulative,
                  payload_sha256=sha(raw), answer=expected, before_cost=costs(job.packet), after_cost=costs(current),
                  authority_effect="None", authentication="NOT_ESTABLISHED", model_calls=0, cost_microusd=0)


def default_job():
    raw = b'{"task_id":"example","role":"data","operation":"polynomial","data":"","coefficients":[1,2,3],"x":2}'
    return Job(packet=encode(raw, DEFAULT_ALPHABET, {"image": IDENTITY}),
               permutations=[Permutation(image=IDENTITY[1:]+IDENTITY[:1]), Permutation(image=IDENTITY[::-1])], comparison=None)


def yaml_bytes(value):
    raw = yaml.safe_dump(value, allow_unicode=True, sort_keys=True).encode("utf-8")
    require(yaml.safe_load(raw) == value, "YAML twin mismatch")
    return raw


def rejected(error):
    diagnostic = str(error).encode("utf-8", errors="backslashreplace")
    reason = type(error).__name__ + ": " + diagnostic.decode("utf-8")[:1024]
    return Rejected(status="REJECTED", reason=reason, diagnostic_bytes=len(diagnostic), diagnostic_sha256=sha(diagnostic)), diagnostic


def run_file(input_path, output_root, format_name):
    folder = Path(output_root) / uuid.uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    total = 0
    with (folder / "input.bin").open("xb") as target:
        if input_path is None:
            raw = encoded(default_job().model_dump())
            target.write(raw)
            total = len(raw)
        else:
            with Path(input_path).open("rb") as source:
                for chunk in iter(lambda: source.read(65536), b""):
                    target.write(chunk)
                    total += len(chunk)
    payload, diagnostic = b"", b""
    try:
        require(total <= MAX_INPUT, "Input byte limit")
        job = load((folder / "input.bin").read_bytes(), "json" if input_path is None else format_name)
        result = evaluate(job)
        payload = decode(result.packet)
        exit_code = 0
    except (ValueError, TypeError, UnicodeError, yaml.YAMLError, RecursionError) as error:
        result, diagnostic = rejected(error)
        exit_code = 1
    record = result.model_dump(mode="json")
    files = {"payload.bin": payload, "result.json": encoded(record)+b"\n", "result.yaml": yaml_bytes(record),
             "diagnostic.txt": diagnostic, "stdout.bin": encoded(record)+b"\n", "stderr.bin": b""}
    for name, raw in files.items():
        (folder / name).write_bytes(raw)
    hashes = {name: sha(raw) for name, raw in files.items()}
    digest = hashlib.sha256()
    with (folder / "input.bin").open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            digest.update(chunk)
    hashes["input.bin"] = digest.hexdigest()
    receipt = Receipt(runner_sha256=sha(Path(__file__).read_bytes()), input_bytes=total, input_complete=True,
                      status=result.status, artifacts=hashes, authority_effect="None").model_dump(mode="json")
    (folder / "receipt.json").write_bytes(encoded(receipt)+b"\n")
    (folder / "receipt.yaml").write_bytes(yaml_bytes(receipt))
    return exit_code, Process(status=result.status, output=str(folder), reason="")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input")
    parser.add_argument("--format", choices=("json", "yaml"), default="json")
    parser.add_argument("--output-root", default=str(Path(__file__).resolve().parent.parent / "pilot_output" / "pilot_0000048"))
    args = parser.parse_args(argv)
    try:
        code, status = run_file(args.input, args.output_root, args.format)
    except (OSError, ValueError, TypeError) as error:
        code, status = 2, Process(status="REFUSED", output=None, reason=rejected(error)[0].reason)
    print(encoded(status.model_dump()).decode())
    return code


if __name__ == "__main__":
    sys.exit(main())
