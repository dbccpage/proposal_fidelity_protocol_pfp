"""Tests for Symbol Game Challenge CLI and Commit-Reveal protocol (U07).

Validates:
- Challenge build, commit, freeze, score, and status subcommands.
- Tamper detection on deliverable post-freeze.
- CheckerDefectPause invariant: checker exceptions NEVER increment cases_wrong.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from omega_engine_pfp.entrypoints.cli.parser import build_parser


@pytest.fixture
def challenge_workspace(tmp_path: Path):
    """Sets up a mock challenge directory with spec, cases, and solver."""
    ws = tmp_path / "chal_ws"
    ws.mkdir()

    # Spec
    spec_file = ws / "spec.md"
    spec_file.write_text("# Double It Challenge\nReturn input * 2.", encoding="utf-8")

    # Public cases
    public_cases = ws / "public_cases.json"
    public_cases.write_text(json.dumps([{"x": 1, "expected": 2}]), encoding="utf-8")

    # Hidden cases
    hidden_cases = ws / "hidden_cases.json"
    hidden_cases.write_text(
        json.dumps([
            {"x": 2, "expected": 4},
            {"x": 3, "expected": 6},
            {"x": 4, "expected": 8},
        ]),
        encoding="utf-8",
    )

    # Correct solver deliverable
    solver_py = ws / "solver.py"
    solver_py.write_text(
        "import sys, json\n"
        "case = json.loads(sys.argv[1])\n"
        "out = {'expected': case['x'] * 2}\n"
        "print(json.dumps(out))\n",
        encoding="utf-8",
    )

    # Flawed solver deliverable
    wrong_solver_py = ws / "wrong_solver.py"
    wrong_solver_py.write_text(
        "import sys, json\n"
        "case = json.loads(sys.argv[1])\n"
        "out = {'expected': case['x'] * 3}\n"
        "print(json.dumps(out))\n",
        encoding="utf-8",
    )

    return {
        "root": ws,
        "spec": spec_file,
        "public": public_cases,
        "hidden": hidden_cases,
        "solver": solver_py,
        "wrong_solver": wrong_solver_py,
    }


def test_challenge_build_commit_freeze_and_score_flow(challenge_workspace):
    ws = challenge_workspace
    parser = build_parser()

    # 1. Build
    build_args = parser.parse_args([
        "challenge", "build",
        "--challenge-id", "CHAL_DOUBLE",
        "--spec", str(ws["spec"]),
        "--public-cases", str(ws["public"]),
        "--hidden-cases", str(ws["hidden"]),
        "--output-dir", str(ws["root"]),
    ])
    assert build_args.func(build_args) == 0

    participant_packet = json.loads((ws["root"] / "participant_packet.json").read_text("utf-8"))
    judge_packet = json.loads((ws["root"] / "judge_packet.json").read_text("utf-8"))
    assert participant_packet["judge_commitment_hash"] == judge_packet["commitment_hash"]

    # 2. Commit
    commit_out = ws["root"] / "commitment.json"
    commit_args = parser.parse_args([
        "challenge", "commit",
        "--challenge-id", "CHAL_DOUBLE",
        "--manifest", str(ws["hidden"]),
        "--operator", "alice",
        "--output", str(commit_out),
    ])
    assert commit_args.func(commit_args) == 0
    commitment = json.loads(commit_out.read_text("utf-8"))
    assert "commitment_hash" in commitment

    # Update judge packet with canonical commitment hash
    judge_packet["commitment_hash"] = commitment["commitment_hash"]
    (ws["root"] / "judge_packet.json").write_text(json.dumps(judge_packet), "utf-8")

    # 3. Freeze solver
    freeze_out = ws["root"] / "freeze.json"
    freeze_args = parser.parse_args([
        "challenge", "freeze",
        "--challenge-id", "CHAL_DOUBLE",
        "--deliverable", str(ws["solver"]),
        "--commitment", str(commit_out),
        "--output", str(freeze_out),
    ])
    assert freeze_args.func(freeze_args) == 0
    freeze = json.loads(freeze_out.read_text("utf-8"))
    assert freeze["judge_commitment_hash"] == commitment["commitment_hash"]

    # 4. Score correct solver
    receipt_out = ws["root"] / "receipt.json"
    score_args = parser.parse_args([
        "challenge", "score",
        "--judge-packet", str(ws["root"] / "judge_packet.json"),
        "--commitment", str(commit_out),
        "--freeze", str(freeze_out),
        "--deliverable", str(ws["solver"]),
        "--output", str(receipt_out),
    ])
    assert score_args.func(score_args) == 0
    receipt = json.loads(receipt_out.read_text("utf-8"))
    assert receipt["status"] == "COMPLETED"
    assert receipt["cases_correct"] == 3
    assert receipt["cases_wrong"] == 0
    assert not receipt["checker_defect_pause"]


def test_challenge_tamper_detection(challenge_workspace):
    ws = challenge_workspace
    parser = build_parser()

    # Build & commit
    commit_out = ws["root"] / "commitment.json"
    commit_args = parser.parse_args([
        "challenge", "commit",
        "--challenge-id", "CHAL_DOUBLE",
        "--manifest", str(ws["hidden"]),
        "--output", str(commit_out),
    ])
    commit_args.func(commit_args)
    commitment = json.loads(commit_out.read_text("utf-8"))

    judge_packet = {
        "challenge_id": "CHAL_DOUBLE",
        "commitment_hash": commitment["commitment_hash"],
        "committed_at_utc": commitment["committed_at_utc"],
        "operator": commitment["operator"],
        "version": commitment["version"],
        "hidden_cases": json.loads(ws["hidden"].read_text("utf-8")),
        "checker_a_id": "chk_a",
        "checker_b_id": "chk_b",
        "authority_effect": "None",
    }
    (ws["root"] / "judge_packet.json").write_text(json.dumps(judge_packet), "utf-8")

    # Freeze original solver
    freeze_out = ws["root"] / "freeze.json"
    freeze_args = parser.parse_args([
        "challenge", "freeze",
        "--challenge-id", "CHAL_DOUBLE",
        "--deliverable", str(ws["solver"]),
        "--commitment", str(commit_out),
        "--output", str(freeze_out),
    ])
    freeze_args.func(freeze_args)

    # TAMPER: Modify solver after freeze!
    ws["solver"].write_text("print('tampered')", encoding="utf-8")

    # Score must fail prerequisite check
    score_args = parser.parse_args([
        "challenge", "score",
        "--judge-packet", str(ws["root"] / "judge_packet.json"),
        "--commitment", str(commit_out),
        "--freeze", str(freeze_out),
        "--deliverable", str(ws["solver"]),
        "--output", str(ws["root"] / "tampered_receipt.json"),
    ])
    with pytest.raises(ValueError, match="content has changed since freeze"):
        score_args.func(score_args)


def test_checker_defect_pause_invariant_never_scored_as_wrong(challenge_workspace):
    """MUTATION KILL GATE / THEORETICAL MINIMUM:

    A checker exception or disagreement MUST trigger CheckerDefectPause.
    It must NEVER be scored as Wrong (cases_wrong must stay 0).
    """
    ws = challenge_workspace
    parser = build_parser()

    commit_out = ws["root"] / "commitment.json"
    commit_args = parser.parse_args([
        "challenge", "commit",
        "--challenge-id", "CHAL_DOUBLE",
        "--manifest", str(ws["hidden"]),
        "--output", str(commit_out),
    ])
    commit_args.func(commit_args)
    commitment = json.loads(commit_out.read_text("utf-8"))

    judge_packet = {
        "challenge_id": "CHAL_DOUBLE",
        "commitment_hash": commitment["commitment_hash"],
        "committed_at_utc": commitment["committed_at_utc"],
        "operator": commitment["operator"],
        "version": commitment["version"],
        "hidden_cases": json.loads(ws["hidden"].read_text("utf-8")),
        "checker_a_id": "chk_a",
        "checker_b_id": "chk_b",
        "authority_effect": "None",
    }
    (ws["root"] / "judge_packet.json").write_text(json.dumps(judge_packet), "utf-8")

    freeze_out = ws["root"] / "freeze.json"
    freeze_args = parser.parse_args([
        "challenge", "freeze",
        "--challenge-id", "CHAL_DOUBLE",
        "--deliverable", str(ws["solver"]),
        "--commitment", str(commit_out),
        "--output", str(freeze_out),
    ])
    freeze_args.func(freeze_args)

    # Score with simulated checker fault
    receipt_out = ws["root"] / "receipt_fault.json"
    score_args = parser.parse_args([
        "challenge", "score",
        "--judge-packet", str(ws["root"] / "judge_packet.json"),
        "--commitment", str(commit_out),
        "--freeze", str(freeze_out),
        "--deliverable", str(ws["solver"]),
        "--simulate-checker-fault",
        "--output", str(receipt_out),
    ])
    assert score_args.func(score_args) == 0

    receipt = json.loads(receipt_out.read_text("utf-8"))
    assert receipt["status"] == "CHECKER_DEFECT_PAUSE"
    assert receipt["checker_defect_pause"] is True
    # CRITICAL INVARIANT: cases_wrong MUST BE 0!
    assert receipt["cases_wrong"] == 0, "Checker exceptions must NEVER be scored as Wrong!"
