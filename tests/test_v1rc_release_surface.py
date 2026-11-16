"""Release-surface checks for the v1.0rc funnel, seams, and zero-spend replay.

AuthorityEffect: None.
"""

from __future__ import annotations

import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def test_ddc_parser_imports_canon_letters_and_refuses_unknown_colour() -> None:
    from operads.canon import DDC_LETTER
    from operads.skill_operad.ddc_operad_parser import DDC_CANONICAL_LETTERS, require_operad_colour

    assert DDC_CANONICAL_LETTERS == DDC_LETTER
    assert require_operad_colour("State").value == "State"
    with pytest.raises(ValueError, match="OPERAD_COLOUR_REFUSED"):
        require_operad_colour("NotAColour")


def test_pciv_rejects_a_mutation_with_no_gain_and_no_cost_drop() -> None:
    from pfp_core.release_surface_v1rc import pciv_strict_pareto_admits

    assert pciv_strict_pareto_admits(Fraction(1, 2), Fraction(1, 2), 10, 10, 2, 2) is False
    assert pciv_strict_pareto_admits(Fraction(1, 2), Fraction(2, 3), 10, 12, 2, 2) is True
    assert pciv_strict_pareto_admits(Fraction(1, 2), Fraction(1, 2), 10, 8, 2, 2) is True


def test_clean_self_panel_has_zero_false_refusals() -> None:
    from pfp_core.release_surface_v1rc import clean_panel_false_refusals

    assert clean_panel_false_refusals() == 0


def test_holdout_overlap_is_refused() -> None:
    from pfp_core.release_surface_v1rc import assert_holdout_disjoint

    with pytest.raises(ValueError, match="HOLDOUT_CONTAMINATION_REFUSAL"):
        assert_holdout_disjoint(("C011",), ("C011",), ("train-prompt-c011",), ("train-prompt-c011",))


def test_tier1_batch_quotients_and_rejects_at_zero_usd() -> None:
    from pfp_core.release_surface_v1rc import run_tier1_release_batch

    batch = run_tier1_release_batch(target_count=1000)
    assert batch["total_generated"] >= 1000
    assert batch["lean4_candidates"] >= 1
    assert 0 < batch["unique_quotient_classes"] < batch["total_generated"]
    assert batch["usd_reject_total"] == "0"
    assert set(batch["reject_reasons"]) == {"port_mismatch", "budget_exceeded", "self_intolerant"}
    assert "HOLDOUT_CONTAMINATION_REFUSAL" in batch["holdout_refusal"]
    assert batch["provider_calls"] == 0
    again = run_tier1_release_batch(target_count=1000)
    assert again["digest"] == batch["digest"]


def test_six_arm_receipt_keeps_the_null_and_uses_exact_fractions() -> None:
    from pfp_core.release_surface_v1rc import run_six_arm_offline_campaign

    report = run_six_arm_offline_campaign()
    paired = report["comparisons"]["arm6_minus_arm3"]
    assert paired["accuracy_delta"] == "0"
    Fraction(paired["raw_mcnemar_p"])
    Fraction(paired["holm_adjusted_p"])
    assert any("is 0" in item for item in report["null_findings"])
    assert report["false_refusal_rate"] == "0"
    assert report["provider_calls"] == 0
    for key in ("supports", "does_not_support", "narrowest_claim", "negative_controls"):
        assert report["claim_hygiene"][key]
    second = run_six_arm_offline_campaign()
    assert second["digest"] == report["digest"]


def test_showcase_replay_performs_no_provider_call() -> None:
    from pfp_core.release_surface_v1rc import replay_guest_showcase

    replay = replay_guest_showcase()
    assert replay["mode"] == "zero-spend-replay"
    assert replay["provider_calls"] == 0
    assert replay["false_refusal_rate"] == "0"


def test_showcase_markup_is_static_and_keeps_the_brand_out() -> None:
    html = (REPO / "pfp_lab" / "web" / "static" / "index.html").read_text(encoding="utf-8")
    script = (REPO / "pfp_lab" / "web" / "static" / "app.js").read_text(encoding="utf-8")
    for tab in ("lab", "funnel", "strand"):
        assert f'data-tab="{tab}"' in html
    for move in ("ASSERT", "CUT", "VERIFY", "RETRACT"):
        assert move in html
    assert "zero-spend" in html
    assert 'id="invite"' in html
    assert "require(" not in script
    assert "module.exports" not in script
    blob = (html + script).lower()
    assert "om" + "ega" not in blob


def test_v1rc_gates_pytest_runs_operads_eis_and_pciv() -> None:
    text = (REPO / ".github" / "workflows" / "pfp_v1rc_gates.yml").read_text(encoding="utf-8")
    commands = [line for line in text.splitlines() if "-m pytest" in line]
    trees = {"operads", "eis", "pciv"}
    assert any(trees <= set(command.split()) for command in commands)
    assert "The rest of eis/" not in text
    assert "historical receipt scripts" not in text


def test_editable_install_imports_pfp_core_without_a_path_hack() -> None:
    if sys.platform == "win32":
        python = REPO / ".venv" / "Scripts" / "python.exe"
    else:
        python = REPO / ".venv" / "bin" / "python"
    if not python.is_file():
        pytest.fail(f"venv python missing at {python}")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [str(python), "-B", "-X", "utf8", "-c", "import pfp_core, pfp_core.release_surface_v1rc"],
        cwd=Path.home(),
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
