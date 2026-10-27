"""End-to-end runs of the audit over synthetic packages.

Counterexamples the harness must detect:

- a refuse-all responder that passes both checkers on an in-scope case
  (``c901_escape``) must be reported as a refusal escape, while the same
  responder must fail every in-scope case of the sound package
  (``c902_sound``);
- a checker that calls the reference solver must be classed ANSWER_KEY;
- a Boolean or float in place of an int must be reported when a checker
  accepts it;
- a manifest digest computed over CRLF bytes must be classed CRLF;
- a checker that never returns must yield a TIMEOUT for that case only.
"""

from __future__ import annotations

import json
from pathlib import Path

from adversary.tests.pilots.judge_packet_audit import audit, canonical
from pfp.tests.judge_audit import fake_packages as fp


def _run(
    tmp_path: Path,
    packages: list[str],
    call_timeout: int = 20,
    shards: int = 1,
    out_name: str = "out",
) -> Path:
    out = tmp_path / out_name
    code = audit.run(
        [
            "--repo-root",
            str(tmp_path / "repo"),
            "--out",
            str(out),
            "--work-dir",
            str(tmp_path / "work"),
            "--packages",
            *packages,
            "--call-timeout",
            str(call_timeout),
            "--wall-timeout",
            "300",
            "--shards",
            str(shards),
        ]
    )
    assert code == 0
    return out


def _package(out: Path, pid: str) -> dict:
    return canonical.read_json_gz(out / "packages" / f"{pid}.json.gz")


def test_refuse_all_escape_is_detected_and_sound_package_is_clean(tmp_path: Path) -> None:
    root = fp.repo(tmp_path / "repo")
    fp.light_package(root, "c901_escape", fp.ESCAPE_EXACT, fp.INDEPENDENT_ESCAPE)
    fp.light_package(root, "c902_sound", fp.SOUND_EXACT, fp.INDEPENDENT_SOUND)
    out = _run(tmp_path, ["C901", "C902"])
    escape = _package(out, "C901")["summary"]
    sound = _package(out, "C902")["summary"]
    assert escape["reference_gate_accept"] == 4 and sound["reference_gate_accept"] == 4
    assert escape["solvable_cases"] == 3 and sound["solvable_cases"] == 3
    # refuse-all responder must pass on every in-scope case of the escape package
    assert escape["refusal"]["union_on_solvable"] == 3
    assert escape["refusal"]["best_fixed_on_solvable"]["count"] == 3
    assert escape["refusal"]["best_fixed_on_solvable"]["strategy"].startswith(
        "refuse:UNKNOWN:code="
    )
    # ... and must fail every in-scope case of the sound package
    assert sound["refusal"]["union_on_solvable"] == 0
    assert sound["refusal"]["best_fixed_overall"]["count"] == 1
    # the unlisted-code control never passes a closed enum
    control = escape["per_strategy"]["refuse:UNKNOWN:code=JUDGE_AUDIT_UNLISTED_CODE"]
    assert control["exact_accept"] == 0
    # boolean or float in place of an int
    assert escape["type_confusion"]["float_for_int"]["gate_accept"] == 3
    assert sound["type_confusion"]["float_for_int"]["gate_accept"] == 0
    # mutation replay and inventory
    record = _package(out, "C901")
    assert record["mutation_inventory"]["entries"] == 2
    assert record["mutation_inventory"]["distinct_case_answer_pairs"] == 1
    assert escape["mutation_replay"]["gate_accept"] == 0
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["totals"]["packages_refusal_accepted_on_a_solvable_case"] == 1
    outcomes = canonical.read_jsonl_gz(out / "outcomes" / "C901.jsonl.gz")
    assert outcomes[0]["roles"] == ["gate", "exact", "independent"]
    assert all(isinstance(row, list) for row in outcomes[1:])


def test_answer_key_checker_and_leaks_are_reported(tmp_path: Path) -> None:
    root = fp.repo(tmp_path / "repo")
    fp.light_package(root, "c903_answer_key", fp.SOUND_EXACT, fp.INDEPENDENT_ANSWER_KEY)
    out = _run(tmp_path, ["C903"])
    record = _package(out, "C903")
    assert record["dependence"]["per_checker"]["independent"]["class"] == "ANSWER_KEY"
    assert record["dependence"]["per_checker"]["exact"]["class"] == "NO_IMPORT_DEPENDENCE"
    leak = record["leakage"]
    assert [d["case"] for d in leak["example_duplicates"]] == ["judge_packet/cases/z_base_01.json"]
    lint = leak["runner_files"]["participant_packet/runner.py"]
    kinds = {k for item in lint["prompt_interpolations"] for k in item["kinds"]}
    assert {"case_id", "case_json"} <= kinds
    assert lint["inline_cases"][0]["verdict_words"] == ["refusal"]
    infeasible = next(c for c in leak["per_case"] if c["case_id"] == "z_base_03_infeasible")
    assert infeasible["id"]["verdict_words"] == ["infeasible"]


def test_crlf_manifest_and_commitment_are_classified(tmp_path: Path) -> None:
    root = fp.repo(tmp_path / "repo")
    fp.governance_package_with_crlf_manifest(root, "c904_custody")
    out = _run(tmp_path, ["C904"])
    custody = _package(out, "C904")["custody"]
    assert custody["manifest"]["counts"]["CRLF"] == 1
    assert custody["manifest"]["counts"]["LF"] == 0
    fields = custody["records"][0]["digest_fields"]
    assert fields[0]["class"] == "MANIFEST_CRLF"


def test_hanging_checker_times_out_on_one_case_only(tmp_path: Path) -> None:
    root = fp.repo(tmp_path / "repo")
    fp.light_package(root, "c905_hang", fp.HANGING_EXACT, fp.INDEPENDENT_SOUND, examples=False)
    out = _run(tmp_path, ["C905"], call_timeout=2)
    lines = canonical.read_jsonl_gz(out / "outcomes" / "C905.jsonl.gz")
    header = lines[0]
    hang_index = header["cases"].index("judge_packet/cases/z_base_04.json")
    rows = lines[1:]
    reference = [r for r in rows if r[0] == "reference"]
    assert {r[1] for r in reference} == {0, 1, 2, 3}
    timed = [r for r in rows if r[0] == "responder" and r[1] == hang_index]
    assert timed and all(r[4][0] == "T" for r in timed)
    others = [r for r in rows if r[0] == "responder" and r[1] != hang_index]
    assert others and all(r[4][0] in ("A", "R") for r in others)


def test_package_output_on_stdout_cannot_forge_records(tmp_path: Path) -> None:
    # counterexample: a checker that prints record-shaped JSON on stdout
    root = fp.repo(tmp_path / "repo")
    fp.light_package(root, "c906_noisy", fp.NOISY_EXACT, fp.INDEPENDENT_SOUND, examples=False)
    out = _run(tmp_path, ["C906"])
    record = _package(out, "C906")
    assert "reference_import_error" not in record
    summary = record["summary"]
    assert summary["reference_gate_accept"] == 3
    assert summary["empty"]["gate_accept"] == 0
    assert summary["non_verdict_outcomes"] == {}


def test_sharded_run_writes_identical_outcomes(tmp_path: Path) -> None:
    root = fp.repo(tmp_path / "repo")
    fp.light_package(root, "c901_escape", fp.ESCAPE_EXACT, fp.INDEPENDENT_ESCAPE)
    one = _run(tmp_path, ["C901"], shards=1, out_name="one")
    three = _run(tmp_path, ["C901"], shards=3, out_name="three")
    for rel in ("outcomes/C901.jsonl.gz", "packages/C901.json.gz", "summary.json"):
        assert (one / rel).read_bytes() == (three / rel).read_bytes(), rel
