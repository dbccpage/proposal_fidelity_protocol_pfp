import ast
import hashlib
import importlib
import importlib.util
import io
import itertools
import json
import os
import runpy
import subprocess
import sys
import zipfile
from decimal import Decimal, localcontext
from fractions import Fraction
from math import gcd
from pathlib import Path

import pytest

PACKAGE = Path(os.environ.get("PFP_SN09_UNDER_TEST", Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location("sn09_under_test", PACKAGE / "__init__.py")
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
n = importlib.import_module("sn09_under_test.numeric_packets")
r = importlib.import_module("sn09_under_test.run")
CONTROLS = json.loads((Path(__file__).resolve().parents[1] / "controls.json").read_bytes())


def leaf(tag):
    return {"tag": str(tag), "children": []}


def rational(sign="pos", numerator=51, denominator=2):
    return {"tag": "rat", "children": [leaf(sign), leaf(numerator), leaf(denominator)]}


def good_replies(cost="0"):
    return (r.Reply(r.encoded(rational()), cost), r.Reply(b'{"wire":"<rat<pos><51><2>>"}', cost))


@pytest.mark.parametrize("control", CONTROLS, ids=[row["id"] for row in CONTROLS])
def test_twenty_original_controls(control):
    raw = control["input"].encode()
    if control["id"].startswith("NOISE"):
        for profile in n.PROFILES:
            with pytest.raises(ValueError):
                n.parse(raw, profile)
    else:
        profile = n.HAG if control["id"] == "CLEAN-02" else n.LEGACY
        assert n.serialize(n.parse(raw, profile), profile) == raw
        with pytest.raises(ValueError):
            n.parse(raw, n.LEGACY if profile == n.HAG else n.HAG)


def test_source_control_bytes_and_historical_contradiction():
    root = Path(__file__).resolve().parents[1] / "evidence"
    manifest = json.loads((root / "manifest.json").read_bytes())
    assert manifest["source_commit"] == "2653895c8e7382e9657c0c0cabe93b8c1f99599a"
    archive = (root / manifest["archive"]).read_bytes()
    assert len(archive) == manifest["archive_bytes"]
    assert hashlib.sha256(archive).hexdigest() == manifest["archive_sha256"]
    assert (
        manifest["archive_sha256"]
        == "6859afe672cee08ccb15845eeb83f846623b5c9c2de70dc155fafb9a2771d413"
    )
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        assert set(bundle.namelist()) == {row["member"] for row in manifest["members"]}
        snapshots = {}
        for row in manifest["members"]:
            raw = bundle.read(row["member"])
            assert len(raw) == row["bytes"]
            assert hashlib.sha256(raw).hexdigest() == row["sha256"]
            assert (
                hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                == row["git_blob"]
            )
            snapshots[row["member"]] = raw
    inventory = json.loads(snapshots["sources.json"])
    assert len(inventory["sources"]) == 9
    for row in inventory["sources"]:
        assert hashlib.sha256(snapshots["sources/" + row["snapshot"]]).hexdigest() == row["sha256"]
    source = ast.parse(
        snapshots["sources/run_adversarial_machine_gate_benchmark.py"].decode("utf-8")
    )
    original = next(
        ast.literal_eval(node.value)
        for node in source.body
        if isinstance(node, ast.AnnAssign) and node.target.id == "NOISY_INPUT_BENCHMARK_MATRIX"
    )
    assert CONTROLS == [{"id": row["id"], "input": row["input"]} for row in original]
    raw = json.loads(snapshots["sources/raw_response.txt"])
    assert "untrusted_output" not in raw
    receipt = json.loads(snapshots["sources/receipt_demo_sn_09.json"])
    assert receipt["gate_result"]["passed"] is True


def test_independent_fraction_grid_and_sum_oracle():
    # Independent construction: neither the production serializer nor value() builds the oracle.
    for numerator, denominator, sign in itertools.product(range(15), range(1, 15), ("pos", "neg")):
        should_accept = gcd(numerator, denominator) == 1 and (numerator != 0 or sign == "pos")
        for profile in n.PROFILES:
            head = "<rat>" if profile == n.LEGACY else "rat"
            raw = f"<{head}<{sign}><{numerator}><{denominator}>>".encode()
            if should_accept:
                result = n.parse(raw, profile)
                assert n.value(result) == Fraction(
                    numerator * (1 if sign == "pos" else -1), denominator
                )
                assert n.to_data(result) == rational(sign, numerator, denominator)
            else:
                with pytest.raises(ValueError, match="NONCANONICAL_RATIONAL"):
                    n.parse(raw, profile)
    for integers in itertools.product(range(2), repeat=6):
        for profile in n.PROFILES:
            head = "<sum6>" if profile == n.LEGACY else "sum6"
            raw = ("<" + head + "".join(f"<{v}>" for v in integers) + ">").encode()
            assert n.value(n.parse(raw, profile)) == sum(integers)


@pytest.mark.parametrize(
    "raw",
    [
        b"<a><b>",
        b"<a>b",
        b"<<sum6><1>>",
        b"<<rat><pos><51>>",
        b"<>",
        b"<rat>",
        b"<pos>",
        b"<00>",
        b"<01>",
        b"<1000000001>",
        b"<11111111111>",
        b"<<rat><pos><0><2>>",
        b"<<rat><neg><0><1>>",
        b"<<rat><pos><1><0>>",
        b"<<rat><neg><2><4>>",
        b"<<rat><plus><1><2>>",
        b"<<rat><pos<1>><1><2>>",
        b"<<<rat><pos><1><2>><1>>",
        b"<<><1>>",
        b"<<0>>",
        b"<1><2>",
        b"<1>a",
        b"<1",
        b"",
        b"1",
        b">",
        b"\xff",
        b"<1>\x00",
        b"<" * 33 + b">" * 33,
    ],
)
def test_structural_and_canonical_refusals(raw):
    with pytest.raises(ValueError):
        n.parse(raw, n.LEGACY)


def test_valid_zero_integer_limit_nested_sum_and_depth():
    assert n.value(n.parse(b"<<rat><pos><0><1>>", n.LEGACY)) == 0
    assert n.value(n.parse(b"<1000000000>", n.LEGACY)) == 10**9
    for profile in n.PROFILES:
        tree = n.from_data(rational())
        for _ in range(28):
            tree = n.Node("sum6", (tree,) + (n.Node("0"),) * 5)
        wire = n.serialize(tree, profile)
        assert n.value(n.parse(wire, profile)) == Fraction(51, 2)
    tree = n.Node("0")
    for _ in range(31):
        tree = n.Node("sum6", (tree,) + (n.Node("0"),) * 5)
    assert n.parse(n.serialize(tree, n.HAG), n.HAG) == tree
    tree = n.Node("sum6", (tree,) + (n.Node("0"),) * 5)
    with pytest.raises(ValueError, match="TREE_LIMIT"):
        n.from_data(n.to_data(tree))
    with pytest.raises(ValueError, match="WIRE_TREE_LIMIT"):
        n.parse(n.serialize(tree, n.HAG), n.HAG)


def test_size_packet_and_json_limits():
    for raw in (None, "<1>", b"a" * 4097):
        with pytest.raises(ValueError, match="WIRE_SIZE_OR_TYPE"):
            n.parse(raw, n.LEGACY)
    with pytest.raises(ValueError, match="WIRE_TREE_LIMIT"):
        n.parse(b"<<sum6>" + b"<0>" * 511 + b">", n.LEGACY)
    data = leaf(0)
    for _ in range(4):
        data = {"tag": "sum6", "children": [data] * 6}
    with pytest.raises(ValueError, match="TREE_LIMIT"):
        n.from_data(data)
    for raw in (None, "{}", b" " * 65537):
        with pytest.raises(ValueError, match="JSON_SIZE_OR_TYPE"):
            n.json_read(raw)
    for raw in (b"\xff", b"{", b"[]{}", b"[" * 30000 + b"]" * 30000):
        with pytest.raises(ValueError, match="INVALID_JSON"):
            n.json_read(raw)
    with pytest.raises(ValueError, match="DUPLICATE_JSON_KEY"):
        n.json_read(b'{"tag":"0","tag":"1","children":[]}')


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {},
        {"tag": "1", "children": [], "pass": True},
        {"tag": True, "children": []},
        {"tag": "", "children": []},
        {"tag": "A", "children": []},
        {"tag": "1", "children": ()},
        {"tag": "sum6", "children": [leaf(1)] * 7},
        {"tag": "sum6", "children": [leaf(1)] * 5},
        rational("pos", "01", 2),
        {"tag": "rat", "children": [{"tag": "sum6", "children": [leaf(0)] * 6}, leaf(1), leaf(2)]},
        {
            "tag": "rat",
            "children": [leaf("pos"), {"tag": "sum6", "children": [leaf(0)] * 6}, leaf(2)],
        },
    ],
)
def test_draft_schema_and_types(data):
    with pytest.raises(ValueError):
        n.from_data(data)


@pytest.mark.parametrize("profile", [None, "auto", "mss-boundary-v1", True, {}, []])
def test_no_implicit_profile(profile):
    with pytest.raises(ValueError, match="UNKNOWN_PROFILE"):
        n.parse(b"<1>", profile)


def test_two_calls_in_order_bound_to_task_and_raw_bytes(tmp_path):
    replies = (
        r.Reply(b"\r\n" + json.dumps(rational(), indent=2).encode() + b"\n"),
        r.Reply(b'\n { "wire" : "<rat<pos><51><2>>" } \r\n'),
    )
    provider = r.ScriptedProvider(replies)
    result = r.execute(r.default_task(), provider, tmp_path / "run")
    assert result["status"] == "ACCEPTED" and result["value"] == "51/2"
    assert result["stages_accepted"] == ["draft", "transcode"]
    assert result["scripted_provider_calls"] == 2 and result["model_calls"] == 0
    assert result["cost_usd"] == "0" and result["live_model_status"] == "NOT_RUN"
    first, second = map(json.loads, provider.calls)
    assert first["stage"] == "draft" and second["stage"] == "transcode"
    assert first["task_sha256"] == second["task_sha256"] == r.sha(r.default_task())
    assert second["draft"] == rational() and second["target_profile"] == n.HAG
    output = tmp_path / "run"
    assert (output / "draft.response.bin").read_bytes() == replies[0].raw
    assert (output / "transcode.response.bin").read_bytes() == replies[1].raw
    assert (output / "wire.bin").read_bytes() == b"<rat<pos><51><2>>"
    for name, digest in result["artifact_sha256"].items():
        assert r.sha((output / name).read_bytes()) == digest
    for name, path in (
        ("run.py", r.__file__),
        ("numeric_packets.py", n.__file__),
        ("budget_ledger.py", r.budget_ledger.__file__),
    ):
        assert result["code_sha256"][name] == r.sha(Path(path).read_bytes())
    assert json.loads((output / "receipt.json").read_bytes()) == result


def test_numeric_equality_does_not_replace_tree_binding(tmp_path):
    original = {"tag": "sum6", "children": [leaf(1)] * 6}
    other = {"tag": "sum6", "children": [leaf(6)] + [leaf(0)] * 5}
    assert n.value(n.from_data(original)) == n.value(n.from_data(other))
    task = r.encoded(
        {
            "source_profile": n.LEGACY,
            "target_profile": n.HAG,
            "source_wire": "<<sum6><1><1><1><1><1><1>>",
        }
    )
    bad_draft = r.ScriptedProvider((r.Reply(r.encoded(other)),))
    result = r.execute(task, bad_draft, tmp_path / "draft")
    assert result["error_code"] == "DRAFT_STRUCTURE_MISMATCH" and len(bad_draft.calls) == 1
    bad_wire = r.ScriptedProvider(
        (r.Reply(r.encoded(original)), r.Reply(b'{"wire":"<sum6<6><0><0><0><0><0>>"}'))
    )
    result = r.execute(task, bad_wire, tmp_path / "wire")
    assert result["error_code"] == "WIRE_STRUCTURE_MISMATCH" and result["status"] == "REJECTED"


@pytest.mark.parametrize(
    "raw",
    [
        b"null",
        b"false",
        b"{}",
        b"{",
        b'{"should_continue":false}',
        b'{"derived_under_policy":"SPK-001","pass":true}',
        b'{"tag":"0","children":[],"tag":"1"}',
        r.encoded(rational(numerator=1)),
    ],
)
def test_bad_draft_halts_and_is_still_charged_in_simulation(raw, tmp_path):
    provider = r.ScriptedProvider((r.Reply(raw, "0.005"),))
    result = r.execute(r.default_task(), provider, tmp_path / "run")
    assert result["status"] == "REJECTED" and result["error_code"]
    assert len(provider.calls) == 1 and result["stages_accepted"] == []
    assert Decimal(result["simulated_billing"]["settled_usd"]) == Decimal(".005")
    assert (tmp_path / "run/draft.response.bin").read_bytes() == raw


@pytest.mark.parametrize(
    "raw",
    [
        b"null",
        b"[]",
        b'{"wire":false}',
        b'{"wire":"<1>","pass":true}',
        b'{"wire":"<<rat><pos><51><2>>"}',
        b'{"wire":"<rat<pos><51><2>> "}',
        b'{"wire":"<1>"}',
        b'{"wire":"<rat<pos><51><2>>","wire":"<1>"}',
        b'{"wire":"\\u00e9"}',
        b'{"wire":"\\ud800"}',
    ],
)
def test_bad_transcode_is_not_repaired(raw, tmp_path):
    provider = r.ScriptedProvider((good_replies()[0], r.Reply(raw, "0.005")))
    result = r.execute(r.default_task(), provider, tmp_path / "run")
    assert result["status"] == "REJECTED" and result["error_code"]
    assert result["stages_accepted"] == ["draft"] and len(provider.calls) == 2
    assert Decimal(result["simulated_billing"]["settled_usd"]) == Decimal(".005")
    assert (tmp_path / "run/transcode.response.bin").read_bytes() == raw


@pytest.mark.parametrize(
    "task",
    [
        None,
        [],
        {},
        {"source_profile": n.LEGACY, "target_profile": "auto", "source_wire": "<1>"},
        {"source_profile": n.LEGACY, "target_profile": n.HAG, "source_wire": True},
        {"source_profile": n.LEGACY, "target_profile": n.HAG, "source_wire": "é"},
    ],
)
def test_invalid_host_task_makes_no_provider_call(task, tmp_path):
    provider = r.ScriptedProvider(())
    result = r.execute(r.encoded(task), provider, tmp_path / "run")
    assert result["status"] == "REJECTED" and provider.calls == []
    assert result["simulated_billing"]["request_count"] == 0


def test_shared_exact_cap_and_over_cap(tmp_path):
    result = r.execute(
        r.default_task(), r.ScriptedProvider(good_replies(".005")), tmp_path / "exact"
    )
    assert result["status"] == "ACCEPTED"
    assert Decimal(result["simulated_billing"]["settled_usd"]) == Decimal(".010")
    provider = r.ScriptedProvider(good_replies(".006"), reservations=(".006", ".005"))
    result = r.execute(r.default_task(), provider, tmp_path / "over")
    assert result["status"] == "REFUSED" and result["error_code"] == "BUDGET_RESERVATION_REFUSED"
    assert len(provider.calls) == 1 and result["simulated_billing"]["request_count"] == 1


@pytest.mark.parametrize(
    "token",
    [
        "0.0050000000000000000000000000000000000001",
        "1e9999999",
        "0.0000000001",
        "1000000",
        "1E-3",
        0.005,
        True,
    ],
)
def test_bounded_money_tokens_prevent_decimal_rounding_or_overflow(token, tmp_path):
    provider = r.ScriptedProvider(good_replies(), reservations=(token, ".005"))
    result = r.execute(r.default_task(), provider, tmp_path / "reservation")
    assert result["status"] == "REFUSED" and result["error_code"] == "INVALID_RESERVATION_TOKEN"
    assert not provider.calls
    provider = r.ScriptedProvider((r.Reply(r.encoded(rational()), token),))
    result = r.execute(r.default_task(), provider, tmp_path / "billing")
    assert result["status"] == "UNRESOLVED" and result["error_code"] == "BILLING_UNKNOWN"
    assert result["simulated_billing"]["held_usd"] == "0.005"


def test_money_boundary_is_independent_of_ambient_decimal_context(tmp_path):
    with localcontext() as context:
        context.prec = 2
        provider = r.ScriptedProvider(
            good_replies(".005000001"), reservations=(".005000001", ".005")
        )
        result = r.execute(r.default_task(), provider, tmp_path / "over")
        assert result["status"] == "REFUSED" and len(provider.calls) == 1
        assert result["simulated_billing"]["settled_usd"] == "0.005000001"
        result = r.execute(
            r.default_task(), r.ScriptedProvider(good_replies(".005")), tmp_path / "exact"
        )
        assert (
            result["status"] == "ACCEPTED" and result["simulated_billing"]["settled_usd"] == "0.010"
        )


@pytest.mark.parametrize(
    "reply",
    [
        r.Reply(b"{}", None),
        r.Reply(b"{}", "NaN"),
        TimeoutError("never disclose this"),
        ConnectionResetError("never disclose this"),
        RuntimeError("never disclose this"),
        ValueError("never disclose this"),
        None,
        r.Reply("not bytes"),
    ],
)
def test_unknown_billing_and_timeout_hold_reservation(reply, tmp_path):
    provider = r.ScriptedProvider((reply,))
    result = r.execute(r.default_task(), provider, tmp_path / "run")
    assert result["status"] == "UNRESOLVED" and len(provider.calls) == 1
    assert result["simulated_billing"]["unknown_request_ids"] == ["draft"]
    assert Decimal(result["simulated_billing"]["held_usd"]) == Decimal(".005")
    assert "never disclose" not in json.dumps(result)
    ledger = r.budget_ledger.BudgetLedger(
        tmp_path / "run/budget.json", ".010", ".010", balance_ceiling_usd=".010"
    )
    with pytest.raises(ValueError, match="UNRESOLVED_CHARGE"):
        ledger.reserve("third", "0")


def test_exhausted_script_holds_reservation_and_defects_propagate(tmp_path):
    result = r.execute(r.default_task(), r.ScriptedProvider(()), tmp_path / "exhausted")
    assert result["status"] == "UNRESOLVED" and result["error_code"] == "IndexError"
    assert result["simulated_billing"]["unknown_request_ids"] == ["draft"]
    with pytest.raises(KeyError):
        r.execute(r.default_task(), r.ScriptedProvider((KeyError("defect"),)), tmp_path / "defect")


def test_ledger_owner_is_beside_the_pilot_independently_of_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "budget_ledger.py").write_text("raise RuntimeError('foreign owner')")
    assert Path(r.budget_ledger.__file__).resolve().parent == Path(r.__file__).resolve().parent
    result = r.execute(r.default_task(), r.ScriptedProvider(good_replies()), tmp_path / "run")
    assert result["status"] == "ACCEPTED"


def test_breach_bad_reservation_and_existing_run_cannot_reset(tmp_path):
    result = r.execute(
        r.default_task(), r.ScriptedProvider(good_replies(".006")), tmp_path / "breach"
    )
    assert (
        result["status"] == "UNRESOLVED"
        and result["error_code"] == "BILLED_COST_EXCEEDS_RESERVATION"
    )
    for index, reservations in enumerate((("bad", "0"), (), (".011", "0"))):
        provider = r.ScriptedProvider(good_replies(), reservations)
        result = r.execute(r.default_task(), provider, tmp_path / str(index))
        assert result["status"] == "REFUSED" and not provider.calls
    provider = r.ScriptedProvider(good_replies())
    with pytest.raises(FileExistsError):
        r.execute(r.default_task(), provider, tmp_path / "breach")
    assert not provider.calls
    provider.calls.append(b"previous call")
    with pytest.raises(ValueError, match="FRESH_SCRIPTED"):
        r.execute(r.default_task(), provider, tmp_path / "new")
    with pytest.raises(ValueError, match="FRESH_SCRIPTED"):
        r.execute(r.default_task(), object(), tmp_path / "new")


def test_cli_e2e_and_invalid_task(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(r, "PFP", tmp_path)
    assert r.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["scripted_provider_calls"] == 2 and Path(result["output"]).is_dir()
    invalid = tmp_path / "bad.json"
    invalid.write_bytes(b"{}")
    assert r.main(["--task", str(invalid)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["scripted_provider_calls"] == 0
    env = dict(os.environ)
    env.pop("COVERAGE_PROCESS_START", None)
    package_dir = Path(r.__file__).resolve().parent
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(package_dir.parent), env.get("PYTHONPATH")))
    )
    # Real module entry-point smoke test uses --help, which writes no run artifacts.
    completed = subprocess.run(
        [sys.executable, "-m", f"{package_dir.name}.run", "--help"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0 and "Offline two-pass" in completed.stdout
    monkeypatch.setattr(sys, "argv", ["run", "--help"])
    _module_key = "sn09_under_test.run"
    assert r.__name__ == _module_key
    _missing_module = object()
    _previous_module = sys.modules.get(_module_key, _missing_module)
    try:
        del sys.modules[_module_key]
        with pytest.raises(SystemExit) as raised:
            runpy.run_module(r.__name__, run_name="__main__")
        assert raised.value.code == 0 and "Offline two-pass" in capsys.readouterr().out
    finally:
        if _previous_module is _missing_module:
            sys.modules.pop(_module_key, None)
        else:
            sys.modules[_module_key] = _previous_module


def test_default_output_root_is_beside_the_pilot_not_the_working_directory():
    assert r.PFP.is_absolute() and r.PFP / "pilots" == Path(r.__file__).resolve().parents[1]


def test_standalone_cli_uses_only_its_local_ledger_and_fails_if_missing(tmp_path):
    root = tmp_path / "standalone"
    pilot = root / "omega_engine_woland/tests/pilots/pilot_0000033"
    pilot.mkdir(parents=True)
    for directory in (root / "omega_engine_woland", pilot.parents[1], pilot.parent):
        (directory / "__init__.py").write_bytes(b"")
    for name in ("__init__.py", "run.py", "numeric_packets.py", "budget_ledger.py"):
        (pilot / name).write_bytes((PACKAGE / name).read_bytes())
    env = dict(os.environ)
    for name in ("PYTHONPATH", "COVERAGE_PROCESS_START"):
        env.pop(name, None)
    command = [sys.executable, "-B", "-m", "omega_engine_woland.tests.pilots.pilot_0000033.run"]
    completed = subprocess.run(
        command, cwd=root, env=env, capture_output=True, text=True, timeout=60
    )
    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout)
    assert receipt["status"] == "ACCEPTED" and receipt["scripted_provider_calls"] == 2
    assert receipt["model_calls"] == 0 and receipt["cost_usd"] == "0"
    assert Path(receipt["output"]).is_relative_to(root)
    assert receipt["code_sha256"]["budget_ledger.py"] == r.sha(
        (pilot / "budget_ledger.py").read_bytes()
    )
    (pilot / "budget_ledger.py").unlink()
    (root / "budget_ledger.py").write_text("raise RuntimeError('foreign owner')")
    missing = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=60)
    assert missing.returncode != 0 and "ImportError" in missing.stderr
    assert "budget_ledger" in missing.stderr and "foreign owner" not in missing.stderr


def test_implementation_mutations_are_killed(tmp_path):
    mutations = [
        (
            "wire-trimming",
            "numeric_packets.py",
            '    if any(byte not in b"<>abcdefghijklmnopqrstuvwxyz0123456789" for byte in raw):',
            '    raw = raw.strip()\n    if any(byte not in b"<>abcdefghijklmnopqrstuvwxyz0123456789" for byte in raw):',
            "test_twenty_original_controls",
        ),
        (
            "canonical-envelope",
            "numeric_packets.py",
            "if serialize(checked, profile) != raw:",
            "if False:",
            "test_structural_and_canonical_refusals",
        ),
        (
            "integer-limit",
            "numeric_packets.py",
            "if value > MAX_INTEGER:",
            "if False:",
            "test_structural_and_canonical_refusals",
        ),
        (
            "reduced-rational",
            "numeric_packets.py",
            "gcd(n, d) != 1",
            "False",
            "test_independent_fraction_grid_and_sum_oracle",
        ),
        (
            "sum-arity",
            "numeric_packets.py",
            "if len(node.children) != 6:",
            "if len(node.children) > 6:",
            "test_draft_schema_and_types",
        ),
        (
            "draft-identity",
            "run.py",
            "if draft != expected:",
            "if False:",
            "test_numeric_equality_does_not_replace_tree_binding",
        ),
        (
            "wire-identity",
            "run.py",
            "if actual != expected or actual != draft:",
            "if False:",
            "test_numeric_equality_does_not_replace_tree_binding",
        ),
        (
            "shared-run-cap",
            "run.py",
            'CAP = "0.010"',
            'CAP = "0.020"',
            "test_shared_exact_cap_and_over_cap",
        ),
        (
            "unknown-to-zero",
            "run.py",
            "ledger.unresolved(stage)",
            'ledger.settle(stage, "0")',
            "test_unknown_billing_and_timeout_hold_reservation",
        ),
        (
            "raw-custody",
            "run.py",
            'save(f"{stage}.response.bin", reply.raw)',
            'save(f"{stage}.response.bin", reply.raw.strip())',
            "test_two_calls_in_order_bound_to_task_and_raw_bytes",
        ),
        (
            "ledger-exposure",
            "budget_ledger.py",
            "if exposure + amount > min(self.pilot_cap, self.campaign_cap, self.balance_ceiling):",
            "if False:",
            "test_atomic_competing_reservations",
        ),
        (
            "ledger-unknown-hold",
            "budget_ledger.py",
            'row["state"] == "UNKNOWN" and key not in self.authorized_prior_unknown_ids',
            "False and key not in self.authorized_prior_unknown_ids",
            "test_unknown_and_breach_are_persistent",
        ),
        (
            "bounded-money",
            "run.py",
            "if not money_token(reservation):",
            "if False:",
            "test_bounded_money_tokens_prevent_decimal_rounding_or_overflow",
        ),
        (
            "ambient-precision",
            "budget_ledger.py",
            "with localcontext(Context(prec=50)):\n                exposure = sum(",
            "with localcontext():\n                exposure = sum(",
            "test_direct_arithmetic_is_independent_of_decimal_context",
        ),
    ]
    report = []
    for name, filename, anchor, replacement, test in mutations:
        folder = tmp_path / name
        folder.mkdir()
        for source_name in ("__init__.py", "numeric_packets.py", "run.py", "budget_ledger.py"):
            (folder / source_name).write_bytes((PACKAGE / source_name).read_bytes())
        source_path = (
            Path(r.budget_ledger.__file__) if filename == "budget_ledger.py" else PACKAGE / filename
        )
        raw = source_path.read_bytes()
        original = raw.decode()
        assert original.count(anchor) == 1, name
        changed = original.replace(anchor, replacement, 1)
        (folder / filename).write_text(changed, encoding="utf-8")
        env = dict(os.environ, PFP_SN09_UNDER_TEST=str(folder), NO_COLOR="1")
        for variable in ("COVERAGE_PROCESS_START", "FORCE_COLOR", "PY_COLORS"):
            env.pop(variable, None)
        target = Path(__file__)
        if filename == "budget_ledger.py":
            env["PFP_SN09_BUDGET_UNDER_TEST"] = str(folder / filename)
            target = target.with_name(
                "test_sn09_budget_extra.py"
                if name == "ambient-precision"
                else "test_sn09_budget_dependency.py"
            )
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--color=no",
            str(target.resolve()) + "::" + test,
            "-c",
            str(PACKAGE / "pytest.ini"),
            "--basetemp=" + str(folder / "temp"),
        ]
        result = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
        row = {
            "id": name,
            "file": filename,
            "source_sha256": r.sha(raw),
            "mutant_sha256": r.sha((folder / filename).read_bytes()),
            "applied": True,
            "source_unchanged": source_path.read_bytes() == raw,
            "exit_code": result.returncode,
            "test": test,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        report.append(row)
    output = Path(os.environ.get("PFP_SN09_MUTATION_REPORT", tmp_path / "mutations.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for row in report:
        assert row["source_unchanged"]
        assert (
            row["exit_code"] == 1
            and "FAILED" in row["stdout"]
            and "ERROR collecting" not in row["stdout"]
        ), row
