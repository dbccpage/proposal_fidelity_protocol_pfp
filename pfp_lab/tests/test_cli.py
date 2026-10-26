"""CLI contract: every command and every documented exit code.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:cli:v1
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from pfp_lab.cli.main import Exit, main
from pfp_lab.core.contracts import CORE_VERSION, MAX_JSON_BYTES, PACK_IDS


def call(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), out, err)
    return code, out.getvalue(), err.getvalue()


def write_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_run_pack_prints_table_and_writes_receipt(tmp_path: Path) -> None:
    target = tmp_path / "receipt.json"
    code, out, err = call("run", "--pack", "paper-005-worked-session", "--receipt", str(target))
    assert (code, err) == (Exit.OK, "")
    assert "step_004     CUT      no  DefectIncrease         3 -> 5" in out
    assert "final defect 6, obstruction 3" in out
    receipt = json.loads(target.read_text(encoding="utf-8"))
    assert out.rstrip().endswith(receipt["digest"])
    assert call("verify", str(target)) == (Exit.OK, f"VALID  digest {receipt['digest']}\n", "")


def test_run_file_json_output(tmp_path: Path) -> None:
    code, out, _ = call("packs", "section-repair")
    scenario = write_json(tmp_path / "s.json", json.loads(out))
    code, out, _ = call("run", str(scenario), "--json")
    assert code == Exit.OK
    assert json.loads(out)["final"]["defect"] == "0"


def test_verify_json_and_tampered_receipt(tmp_path: Path) -> None:
    target = tmp_path / "r.json"
    call("run", "--pack", "two-islands", "--receipt", str(target))
    code, out, _ = call("verify", str(target), "--json")
    assert (code, json.loads(out)["valid"]) == (Exit.OK, True)
    body = json.loads(target.read_text(encoding="utf-8"))
    body["final"]["defect"] = "1"
    forged = write_json(tmp_path / "forged.json", body)
    code, out, _ = call("verify", str(forged))
    assert code == Exit.NOT_VERIFIED
    assert out.startswith("NOT VALID")
    assert "  - digest mismatch" in out


def test_packs_listing() -> None:
    code, out, _ = call("packs")
    assert code == Exit.OK
    assert out.splitlines()[0].startswith("paper-005-worked-session       8 moves  Paper 005")
    assert len(out.splitlines()) == len(PACK_IDS)


def test_admission_failures(tmp_path: Path) -> None:
    bad = write_json(tmp_path / "bad.json", {"schema": "pfp-lab.scenario.v1", "vertices": [], "edges": [], "moves": []})
    code, _, err = call("run", str(bad))
    assert code == Exit.ADMISSION
    assert err.startswith("pfp-lab: input refused: 1 problem(s)")
    huge = tmp_path / "huge.json"
    huge.write_bytes(b" " * (MAX_JSON_BYTES + 1))
    code, _, err = call("run", str(huge))
    assert (code, "limit" in err) == (Exit.ADMISSION, True)


def test_io_and_unknown_pack_failures(tmp_path: Path) -> None:
    code, _, err = call("run", str(tmp_path / "missing.json"))
    assert (code, err.startswith("pfp-lab: cannot read")) == (Exit.IO, True)
    code, _, err = call("run", "--pack", "nope")
    assert (code, err) == (Exit.UNKNOWN_PACK, "pfp-lab: no pack named 'nope'\n")
    code, _, err = call("run", "--pack", "two-islands", "--receipt", str(tmp_path / "no" / "dir.json"))
    assert (code, err.startswith("pfp-lab: cannot write")) == (Exit.IO, True)


def test_budget_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    import pfp_lab.core.session as session

    monkeypatch.setattr(session, "DEFAULT_SEARCH_BUDGET", 2)
    monkeypatch.setattr(session.run_scenario, "__kwdefaults__", {"budget": 2})
    code, _, err = call("run", "--pack", "paper-005-worked-session")
    assert (code, err) == (Exit.BUDGET, "pfp-lab: obstruction search exceeded its step budget\n")


def test_schema_export(tmp_path: Path) -> None:
    code, out, _ = call("schema", str(tmp_path / "schemas"))
    assert code == Exit.OK
    scenario = json.loads((tmp_path / "schemas" / "scenario.v1.schema.json").read_text(encoding="utf-8"))
    assert scenario["title"] == "ScenarioIn"
    assert "schema" in scenario["properties"]
    assert out.count("wrote") == 2
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")
    code, _, err = call("schema", str(blocker / "sub"))
    assert (code, err.startswith("pfp-lab: cannot create")) == (Exit.IO, True)


def test_checked_in_schemas_match_the_models(tmp_path: Path) -> None:
    call("schema", str(tmp_path))
    checked_in = Path(__file__).resolve().parents[2] / "contracts" / "schema"
    for name in ("scenario.v1.schema.json", "receipt.v1.schema.json"):
        assert (checked_in / name).read_text(encoding="utf-8") == (tmp_path / name).read_text(encoding="utf-8")


def test_usage_errors_exit_2() -> None:
    with pytest.raises(SystemExit) as caught:
        call("run")
    assert caught.value.code == 2
    with pytest.raises(SystemExit) as version:
        call("--version")
    assert version.value.code == 0


def run_module(*argv: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pfp_lab.cli.main", *argv],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )


def test_module_entry_point_and_stdio_process() -> None:
    listed = run_module("packs")
    assert (listed.returncode, listed.stdout.splitlines()[0][:24]) == (0, "paper-005-worked-session")
    request = json.dumps({"jsonrpc": "2.0", "id": 7, "method": "lab.version"})
    served = run_module("stdio", stdin=request + "\n\n")
    assert served.returncode == 0
    assert json.loads(served.stdout) == {
        "jsonrpc": "2.0",
        "id": 7,
        "result": {"version": CORE_VERSION, "authority_effect": "None"},
    }
    assert "\r" not in served.stdout


def test_unicode_title_prints_in_utf8(tmp_path: Path) -> None:
    code, out, _ = call("packs", "section-repair")
    body = json.loads(out)
    body["title"] = "Φ₁ → 0"
    scenario = write_json(tmp_path / "u.json", body)
    finished = run_module("run", str(scenario))
    assert finished.returncode == 0
    assert finished.stdout.startswith("Φ₁ → 0")
