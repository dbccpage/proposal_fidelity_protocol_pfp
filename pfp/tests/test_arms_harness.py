"""Tests for matched arms harness and exact rational McNemar statistics (U08).

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from pfp.entrypoints.cli.challenge_commands import (
    cmd_challenge_run_arms,
    mcnemar_exact_rational,
)
from pfp.entrypoints.cli.parser import build_parser


def test_exact_rational_mcnemar_values():
    # Invariant from U08:
    # mcnemar_exact(3, 0) == 1/4
    # mcnemar_exact(10, 2) == 79/2048
    # mcnemar_exact(0, 0) == 1
    assert mcnemar_exact_rational(3, 0) == Fraction(1, 4)
    assert mcnemar_exact_rational(10, 2) == Fraction(79, 2048)
    assert mcnemar_exact_rational(0, 0) == Fraction(1, 1)

    # Mutation kill: omitting factor 2 gives 1/8 instead of 1/4
    p = mcnemar_exact_rational(3, 0)
    assert p.numerator == 1
    assert p.denominator == 4


def test_cli_matched_arms_passes(tmp_path: Path):
    arms_file = tmp_path / "arms.json"
    arms = [
        {
            "arm_id": "arm_a",
            "model_id": "meta-llama/llama-3.3-70b-instruct",
            "temperature_str": "0.0",
            "max_tokens": 4096,
            "budget_micro_usd": 50000,
            "specification_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "intervention_name": "baseline",
            "authority_effect": "None",
        },
        {
            "arm_id": "arm_b",
            "model_id": "meta-llama/llama-3.3-70b-instruct",
            "temperature_str": "0.0",
            "max_tokens": 4096,
            "budget_micro_usd": 50000,
            "specification_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "intervention_name": "hieroglyphic_prompt",
            "authority_effect": "None",
        },
    ]
    arms_file.write_text(json.dumps(arms), encoding="utf-8")

    outcomes_file = tmp_path / "outcomes.json"
    # 3 discordant pairs: arm_a=True, arm_b=False (b=3, c=0)
    outcomes = [
        {"arm_a": True, "arm_b": False},
        {"arm_a": True, "arm_b": False},
        {"arm_a": True, "arm_b": False},
        {"arm_a": True, "arm_b": True},
    ]
    outcomes_file.write_text(json.dumps(outcomes), encoding="utf-8")

    out_file = tmp_path / "report.json"

    parser = build_parser()
    args = parser.parse_args([
        "challenge",
        "run-arms",
        "--arms-spec",
        str(arms_file),
        "--outcomes",
        str(outcomes_file),
        "--output",
        str(out_file),
    ])

    ret = args.func(args)
    assert ret == 0

    report = json.loads(out_file.read_text(encoding="utf-8"))
    assert report["matched"] is True
    assert report["mcnemar"]["b"] == 3
    assert report["mcnemar"]["c"] == 0
    assert report["mcnemar"]["p_value_exact"] == "1/4"
    assert report["authority_effect"] == "None"


def test_cli_divergent_arm_fails(tmp_path: Path):
    arms_file = tmp_path / "arms_divergent.json"
    arms = [
        {
            "arm_id": "arm_a",
            "model_id": "meta-llama/llama-3.3-70b-instruct",
            "temperature_str": "0.0",
            "max_tokens": 4096,
            "budget_micro_usd": 50000,
            "specification_hash": "hash_a",
            "intervention_name": "baseline",
            "authority_effect": "None",
        },
        {
            "arm_id": "arm_b",
            "model_id": "qwen/qwen-2.5-7b-instruct",  # Model divergence!
            "temperature_str": "0.0",
            "max_tokens": 4096,
            "budget_micro_usd": 50000,
            "specification_hash": "hash_a",
            "intervention_name": "hieroglyphic_prompt",
            "authority_effect": "None",
        },
    ]
    arms_file.write_text(json.dumps(arms), encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args([
        "challenge",
        "run-arms",
        "--arms-spec",
        str(arms_file),
    ])

    with pytest.raises(ValueError, match="ARM_MISMATCH"):
        args.func(args)
