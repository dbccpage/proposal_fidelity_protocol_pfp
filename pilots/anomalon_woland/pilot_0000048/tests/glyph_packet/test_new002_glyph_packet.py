import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import runpy
import subprocess
import sys
import types

import pytest
import yaml

SOURCE = Path(__file__).resolve().parents[2] / "run.py"
spec = importlib.util.spec_from_file_location("new002_glyph_runner", SOURCE)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def qraw(task="known", coefficients=None, x=2, data=""):
    return json.dumps({"task_id": task, "role": "data", "operation": "polynomial",
                       "data": data, "coefficients": [1, 2, 3] if coefficients is None else coefficients, "x": x},
                      ensure_ascii=False, separators=(",", ":")).encode()


def packet(module=m, raw=None, alphabet=None, key=None):
    return module.encode(qraw() if raw is None else raw, list("0123456789abcdef") if alphabet is None else alphabet,
                         {"image": list(range(16)) if key is None else key})


def job(module=m, **changes):
    result = {"packet": packet(module).model_dump(), "permutations": [], "comparison": None}
    result.update(changes)
    return result


P = {"image": [1, 2, 0]+list(range(3, 16))}
Q = {"image": [1, 0]+list(range(2, 16))}


def mutation_controls(module):
    p = packet(module)
    raw = qraw()
    assert p.glyphs == raw.hex()
    assert module.decode(p) == raw
    assert module.answer(raw).polynomial_value == 17
    assert module.decode(module.act(p, P)) == raw
    assert module.act(module.act(p, P), Q) == module.act(p, module.compose(Q, P))
    assert module.act(module.act(p, P), module.inverse(P)) == p
    with pytest.raises(ValueError):
        module.permutation({"image": [0, 0]+list(range(2, 16))})
    with pytest.raises(ValueError, match="Protected answer changed"):
        module.evaluate(job(module, comparison=packet(module, qraw(coefficients=[1, 2, 4])).model_dump()))
    c = module.costs(p).model_dump()
    for dim in ("utf8_bytes", "codepoints"):
        assert sum(c[name][dim] for name in ("body_json", "alphabet_key_json", "legend_json", "framing_json")) == c["packet_json"][dim]
    defects = []
    wrong_hash = p.model_dump()
    wrong_hash["payload_sha256"] = "0"*64
    defects.append(lambda: module.decode(wrong_hash))
    wrong_task = p.model_dump()
    wrong_task["task_id"] = "foreign"
    defects.append(lambda: module.decode(wrong_task))
    ambiguous = p.model_dump()
    ambiguous["key"]["image"][1] = 0
    defects.append(lambda: module.decode(ambiguous))
    same_answer = packet(module, qraw("other"))
    defects.append(lambda: module.evaluate(job(module, comparison=same_answer.model_dump())))
    changed_answer = packet(module, qraw(coefficients=[1, 2, 4]))
    defects.append(lambda: module.evaluate(job(module, comparison=changed_answer.model_dump())))
    for test in defects:
        with pytest.raises((ValueError, TypeError)):
            test()
    r, diag = module.rejected(ValueError("x"*70000))
    assert len(r.reason) < 1200 and len(diag) == 70000
    with pytest.raises(ValueError):
        module.load(b"\xff{}", "json")
    with pytest.raises(ValueError):
        module.Receipt(runner_sha256="0"*64, input_bytes=0, input_complete=True, status="REJECTED", artifacts={}, authority_effect="None")


def test_independent_hex_and_known_answer():
    mutation_controls(m)
    assert m.answer(qraw(coefficients=[-2, 0, 5], x=-3)).polynomial_value == 43
    assert m.answer(qraw(coefficients=[7], x=16)).polynomial_value == 7
    maximum = m.answer(qraw(coefficients=[10000]*9, x=16)).polynomial_value
    assert maximum == 10000*((16**9-1)//15)


def test_group_laws_embedded_s3_and_three_keys():
    base = packet()
    perms = [{"image": list(p)+list(range(3, 16))} for p in itertools.permutations(range(3))]
    identity = {"image": list(range(16))}
    for p in perms:
        assert m.act(base, identity) == base
        assert m.act(m.act(base, p), m.inverse(p)) == base
        assert m.compose(identity, p) == m.permutation(p) == m.compose(p, identity)
        for r in perms:
            assert m.act(m.act(base, p), r) == m.act(base, m.compose(r, p))
            for s in perms:
                assert m.compose(s, m.compose(r, p)) == m.compose(m.compose(s, r), p)
    for key in (list(range(16)), list(range(16))[::-1], list(range(1, 16))+[0]):
        encoded = packet(key=key, alphabet=m.DEFAULT_ALPHABET)
        assert m.decode(encoded) == qraw()
        assert len(encoded.glyphs) == 2*len(qraw())


def test_whitespace_multibyte_exactness_and_costs():
    raw = b' {"task_id":"known", "role":"data", "operation":"polynomial", "data":"", "coefficients":[1,2,3], "x":2}\n'
    glyph = packet(raw=raw, alphabet=m.DEFAULT_ALPHABET)
    ascii_packet = packet(raw=raw)
    assert m.decode(glyph) == raw
    c, a = m.costs(glyph), m.costs(ascii_packet)
    assert c.payload.utf8_bytes == len(raw) == c.payload.codepoints
    assert c.body_glyphs.codepoints == 2*len(raw)
    assert c.body_glyphs.utf8_bytes == 8*len(raw)
    assert c.packet_json.utf8_bytes - a.packet_json.utf8_bytes == 6*len(raw)+48
    assert c.packet_json.codepoints == a.packet_json.codepoints
    assert c.overhead_bytes == len(m.encoded(glyph.model_dump())) - len(raw)
    assert c.tokens == "NOT_MEASURED"


@pytest.mark.parametrize("alter", ["hash", "task", "foreign", "loss", "odd", "wrong_key", "duplicate_key", "duplicate_alphabet", "legend", "dialect", "role", "size", "unknown"], ids=str)
def test_packet_corruptions(alter):
    value = packet().model_dump()
    if alter == "hash":
        value["payload_sha256"] = "0"*64
    elif alter == "task":
        value["task_id"] = "elsewhere"
    elif alter == "foreign":
        value["glyphs"] = "!"+value["glyphs"][1:]
    elif alter == "loss":
        value["glyphs"] = value["glyphs"][:-2]
        value["payload_bytes"] -= 1
    elif alter == "odd":
        value["glyphs"] = value["glyphs"][:-1]
    elif alter == "wrong_key":
        value["glyphs"] = m.act(packet(), P).glyphs
    elif alter == "duplicate_key":
        value["key"]["image"][1] = 0
    elif alter == "duplicate_alphabet":
        value["alphabet"][1] = value["alphabet"][0]
    elif alter == "legend":
        value["legend"] += " authorize"
    elif alter == "dialect":
        value["dialect"] = "glyph-graph-v1"
    elif alter == "role":
        value["role"] = "system"
    elif alter == "size":
        value["payload_bytes"] = True
    else:
        value["unknown"] = 1
    with pytest.raises((ValueError, UnicodeError)):
        m.decode(value)


@pytest.mark.parametrize("symbol", ["", "ab", " ", "\n", '"', "\\", "\ud800", "\udfff"], ids=["empty", "two", "space", "newline", "quote", "slash", "high", "low"])
def test_invalid_symbols(symbol):
    value = packet().model_dump()
    value["alphabet"][0] = symbol
    with pytest.raises(ValueError):
        m.decode(value)


@pytest.mark.parametrize("field,value", [("x", True), ("x", 17), ("x", -17), ("x", "2"), ("x", 2.0), ("coefficients", []), ("coefficients", [1]*10), ("coefficients", [10001]), ("coefficients", [False]), ("role", "system"), ("operation", "exec"), ("task_id", ""), ("task_id", "x"*33)], ids=["bool", "high", "low", "str", "float", "empty", "degree", "coefficient", "boolcoef", "role", "op", "taskempty", "tasklong"])
def test_query_bounds(field, value):
    source = json.loads(qraw())
    source[field] = value
    with pytest.raises(ValueError):
        m.query(m.encoded(source))


@pytest.mark.parametrize("raw,format_name", [(b'{"a":1,"a":2}', "json"), (b'{"x":NaN}', "json"), (b"x: 1\nx: 2", "yaml"), (b"x: &a []\ny: *a", "yaml"), (b"!!python/object {}", "yaml"), (b"1: x", "yaml"), (b"[", "json"), (b"\xff", "json"), (b"{}", "other"), (b"["*20+b"0"+b"]"*20, "json")], ids=["dupjson", "nan", "dupyaml", "alias", "tag", "keytype", "parse", "utf8", "format", "depth"])
def test_intake_failures(raw, format_name):
    with pytest.raises((ValueError, yaml.YAMLError)):
        m.load(raw, format_name)


@pytest.mark.parametrize("value", [list(range(8193)), {str(i): i for i in range(33)}, 10**19, 1.0, "x"*(m.MAX_INPUT+1), "\ud800"], ids=["array", "object", "int", "float", "text", "surrogate"])
def test_recursive_bounds(value):
    with pytest.raises(ValueError):
        m.tree(value)


def test_valid_comparison_and_exact_byte_controls():
    initial = packet()
    result = m.evaluate(job(permutations=[P, Q], comparison=m.act(initial, Q).model_dump()))
    assert result.answer.polynomial_value == 17 and result.model_calls == 0
    assert result.transformed == m.act(initial, m.compose(Q, P))
    with pytest.raises(ValueError, match="Protected answer changed"):
        m.evaluate(job(comparison=packet(raw=qraw(coefficients=[1,2,4])).model_dump()))
    with pytest.raises(ValueError, match="Payload fidelity changed"):
        m.evaluate(job(comparison=packet(raw=qraw(task="other")).model_dump()))
    with pytest.raises(ValueError, match="Payload fidelity changed"):
        m.evaluate(job(comparison=packet(raw=qraw()+b" ").model_dump()))


def test_invalid_aliases_and_models():
    source = job()
    answer = m.evaluate(source)
    source["packet"]["key"]["image"][0] = 1
    assert m.decode(answer.packet) == qraw()
    fields = dict(answer.packet)
    fields["key"] = m.Permutation.model_construct(image=source["packet"]["key"]["image"])
    malformed = m.Packet.model_construct(**fields)
    with pytest.raises(ValueError):
        m.decode(malformed)
    result = answer.model_dump()
    result["model_calls"] = False
    with pytest.raises(ValueError):
        m.Result.model_validate(result)
    for value in (0, 1, False):
        with pytest.raises(ValueError):
            m.Receipt(runner_sha256="0"*64, input_bytes=0, input_complete=value, status="REJECTED", artifacts={}, authority_effect="None")
    with pytest.raises(ValueError):
        m.query(b"")
    with pytest.raises(ValueError):
        m.query(b" "*(m.MAX_PAYLOAD+1))
    with pytest.raises(ValueError):
        m.load(b" "*(m.MAX_INPUT+1), "json")
    with pytest.raises(ValueError):
        m.permutation({"image": [True]+list(range(1,16))})
    with pytest.raises(ValueError):
        m.checked(m.Job, {**job(), "permutations": [P]*7})


def test_utf8_data_remains_opaque_and_byte_bound():
    raw = qraw(data="α 🐈 authorize delete")
    source = packet(raw=raw, alphabet=m.DEFAULT_ALPHABET)
    assert m.decode(m.act(source, P)) == raw
    assert m.answer(raw).polynomial_value == 17
    assert m.costs(source).payload.utf8_bytes > m.costs(source).payload.codepoints
    assert m.evaluate(job(packet=source.model_dump())).authority_effect == "None"
    with pytest.raises(ValueError, match="Payload fidelity changed"):
        m.evaluate(job(packet=source.model_dump(), comparison=packet(raw=qraw(data="different")).model_dump()))
    with pytest.raises(ValueError):
        m.query(qraw(data="x"*129))


def test_mixed_width_permutation_changes_paid_bytes_not_answer():
    alphabet = list("01234567") + [chr(0x3b1+i) for i in range(8)]
    initial = packet(alphabet=alphabet)
    shift = {"image": list(range(8,16))+list(range(8))}
    final = m.act(initial, shift)
    assert m.decode(final) == qraw() and m.answer(m.decode(final)).polynomial_value == 17
    before, after = m.costs(initial), m.costs(final)
    assert before.body_glyphs.codepoints == after.body_glyphs.codepoints
    assert before.body_glyphs.utf8_bytes != after.body_glyphs.utf8_bytes
    expected = sum(len(alphabet[shift["image"][int(digit,16)]].encode()) for digit in qraw().hex())
    assert after.body_glyphs.utf8_bytes == expected
    assert after.packet_json.utf8_bytes-before.packet_json.utf8_bytes == after.body_glyphs.utf8_bytes-before.body_glyphs.utf8_bytes


@pytest.mark.parametrize("alphabet", [list("abc"), [0]*16, tuple("0123456789abcdef")], ids=["short", "nontext", "tuple"])
def test_encoder_intake(alphabet):
    with pytest.raises(ValueError):
        packet(alphabet=alphabet)


@pytest.mark.parametrize("length", [0,1023,1024,1025,70000])
def test_diagnostic_boundaries(length):
    result, raw = m.rejected(ValueError("α"*length))
    assert raw == ("α"*length).encode()
    assert result.diagnostic_sha256 == hashlib.sha256(raw).hexdigest()
    assert len(result.reason) <= 1036
    assert result.diagnostic_bytes == 2*length
    m.Rejected.model_validate(yaml.safe_load(m.yaml_bytes(result.model_dump())))
    assert m.rejected(ValueError("\ud800"))[1] == b"\\ud800"


def check_bundle(folder, submitted, expected_status):
    assert (folder/"input.bin").read_bytes() == submitted
    result = json.loads((folder/"result.json").read_bytes())
    receipt = m.Receipt.model_validate(json.loads((folder/"receipt.json").read_bytes()))
    assert result["status"] == receipt.status == expected_status
    assert yaml.safe_load((folder/"result.yaml").read_bytes()) == result
    assert yaml.safe_load((folder/"receipt.yaml").read_bytes()) == receipt.model_dump()
    for name, digest in receipt.artifacts.items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == digest
    (m.Result if expected_status == "PRESERVED" else m.Rejected).model_validate(result)
    return result


@pytest.mark.parametrize("case", ["default", "json", "yaml", "small", "long", "utf8", "oversized", "wrong_answer", "same_answer"], ids=str)
def test_actual_cli(tmp_path, case):
    args = []
    if case == "default":
        submitted = m.encoded(m.default_job().model_dump())
    else:
        if case in ("json", "yaml"):
            submitted = m.encoded(job()) if case == "json" else m.yaml_bytes(job())
        elif case == "small":
            submitted = b"{}"
        elif case == "long":
            submitted = m.encoded({"x"*60000: None, "y"*60000: None})
        elif case == "utf8":
            submitted = b"\xff{}"
        elif case == "oversized":
            submitted = b"x"*(m.MAX_INPUT+1)
        else:
            proposed = packet(raw=qraw(task="other") if case == "same_answer" else qraw(coefficients=[1,2,4]))
            submitted = m.encoded(job(comparison=proposed.model_dump()))
        source = tmp_path/"submitted.bin"
        source.write_bytes(submitted)
        args = ["--input", str(source), "--format", "yaml" if case == "yaml" else "json"]
    command = [sys.executable, "-B", str(SOURCE), *args, "--output-root", str(tmp_path/"out")]
    proc = subprocess.run(command, capture_output=True, check=False)
    (tmp_path/"command.json").write_text(json.dumps(command), encoding="utf-8")
    (tmp_path/"process_stdout.bin").write_bytes(proc.stdout)
    (tmp_path/"process_stderr.bin").write_bytes(proc.stderr)
    expected = "PRESERVED" if case in ("default","json","yaml") else "REJECTED"
    assert proc.returncode == (0 if expected == "PRESERVED" else 1), proc.stderr
    status = m.Process.model_validate(json.loads(proc.stdout))
    result = check_bundle(Path(status.output), submitted, expected)
    if case == "long":
        assert result["diagnostic_bytes"] > 120000 and len(result["reason"]) < 1200
    if expected == "PRESERVED":
        assert (Path(status.output)/"payload.bin").read_bytes() == m.decode(result["packet"])


def test_inprocess_io_and_failure_paths(tmp_path, monkeypatch, capsys):
    assert m.main(["--output-root", str(tmp_path/"default")]) == 0
    result = json.loads(capsys.readouterr().out)
    check_bundle(Path(result["output"]), m.encoded(m.default_job().model_dump()), "PRESERVED")
    path = tmp_path/"bad.json"
    path.write_bytes(b"{}")
    assert m.main(["--input", str(path), "--output-root", str(tmp_path/"bad")]) == 1
    capsys.readouterr()
    assert m.main(["--input", str(tmp_path/"missing"), "--output-root", str(tmp_path/"missing_out")]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    monkeypatch.setattr(m.yaml, "safe_load", lambda value: {"wrong": 1})
    with pytest.raises(ValueError, match="YAML twin"):
        m.yaml_bytes({"right": 1})


MUTATIONS = [
    ("nibble_order", "16*nibble_for[packet.glyphs[i]] + nibble_for[packet.glyphs[i+1]]", "nibble_for[packet.glyphs[i]] + 16*nibble_for[packet.glyphs[i+1]]"),
    ("key_bijection", "sorted(value) == IDENTITY", "True"),
    ("source_hash", "len(raw) == packet.payload_bytes and sha(raw) == packet.payload_sha256", "len(raw) == packet.payload_bytes"),
    ("task_binding", "q.task_id == packet.task_id and q.role == packet.role", "True"),
    ("key_action", "[p.image[i] for i in packet.key.image]", "packet.key.image"),
    ("body_action", '"".join(substitution[ch] for ch in packet.glyphs)', "packet.glyphs"),
    ("composition_order", "[a[b[i]] for i in IDENTITY]", "[b[a[i]] for i in IDENTITY]"),
    ("inverse", "[p.index(i) for i in IDENTITY]", "IDENTITY[:]"),
    ("horner", "value*q.x + coefficient", "value + coefficient"),
    ("protected_answer", "answer(proposed) == expected", "True"),
    ("payload_fidelity", "proposed == raw", "True"),
    ("framing_cost", "len(wire)-component_bytes", "len(wire)-component_bytes-1"),
    ("diagnostic_bound", 'diagnostic.decode("utf-8")[:1024]', 'diagnostic.decode("utf-8")'),
    ("utf8", 'text = raw.decode("utf-8")', 'text = raw.decode("utf-8", errors="ignore")'),
    ("receipt_set", 'set(value) == {"input.bin", "payload.bin", "result.json", "result.yaml", "diagnostic.txt", "stdout.bin", "stderr.bin"}', "True"),
]


def test_compiled_mutations(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    mutation_controls(m)
    rows = []
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, name
        mutant = source.replace(old, new)
        path = tmp_path/(name+".py")
        path.write_text(mutant, encoding="utf-8")
        module = types.ModuleType("mutant_"+name)
        module.__file__ = str(path)
        sys.modules[module.__name__] = module
        exec(compile(mutant, str(path), "exec"), module.__dict__)
        try:
            mutation_controls(module)
        except (AssertionError, ValueError, TypeError, pytest.fail.Exception) as error:
            rows.append({"name": name, "sha256": hashlib.sha256(mutant.encode()).hexdigest(), "killed": True, "failure": type(error).__name__, "detail": str(error)[:1000]})
        else:
            pytest.fail("Mutation survived: "+name)
    (tmp_path/"mutations.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    assert len(rows) == 15


def test_script_entry(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(SOURCE), "--output-root", str(tmp_path / "runs")])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(SOURCE), run_name="__main__")
    assert caught.value.code == 0 and json.loads(capsys.readouterr().out)["status"] == "PRESERVED"
