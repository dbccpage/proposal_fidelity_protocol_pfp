"""Tier 5 Adversarial Coverage Hardening for C021 Governance, Runner, and Commit-Reveal.

Challenger 2 (Milestone 4 - Symbol Game & Python Quantum Challenge Swarm C021).
AuthorityEffect: None.

Covers:
1. Micro-USD precision, rounding, ceiling division, and zero-dollar transactions in BudgetGate & BudgetController.
2. StructureBench reverse write order protocol, cryptographic hash binding, and file corruption detection in WolandGate.
3. CommitRevealRunner sequence state machine, manifest path traversal vulnerability auditing, missing commit files, and CLI edge cases.
4. Participant packet runner.py resilience against hostile solvers, corrupted inputs, format polymorphism, and CLI handling.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.budget_gate import (
    BudgetGate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.commit_reveal_runner import (
    CommitRevealRunner,
    sha256_of_file,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.commit_reveal_runner import (
    main as commit_reveal_main,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.woland_gate import (
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    RunFolderExistsError,
    WolandGate,
    persist_single_bundle,
    sanitize_run_key,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.participant_packet.runner import (
    canonical_json_str,
    load_cases,
    load_solver_func,
    run_cases,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.participant_packet.runner import (
    main as participant_runner_main,
)

from omega_engine_woland.domain.providers.budget import (
    BudgetController,
    PriceQuoteV1,
    PriceTable,
    _leg_cost_microusd,
    fixture_pricing_observation,
)
from omega_engine_woland.domain.providers.model_registry import (
    ModelNotAllowed,
)
from omega_engine_woland.domain.providers.types import BudgetExceeded, Provider

# ==============================================================================
# Helper functions for independent cryptographic verification
# ==============================================================================


def verify_bundle_hash_bindings(bundle_dir: Path) -> dict[str, bool]:
    """Independently verifies the 4-file StructureBench bundle hash bindings."""
    novella_file = bundle_dir / "novella.md"
    dda_file = bundle_dir / "dda_actions.jsonl"
    summary_file = bundle_dir / "summary.json"
    receipt_file = bundle_dir / "receipt.json"

    assert novella_file.exists(), f"novella.md missing in {bundle_dir}"
    assert dda_file.exists(), f"dda_actions.jsonl missing in {bundle_dir}"
    assert summary_file.exists(), f"summary.json missing in {bundle_dir}"
    assert receipt_file.exists(), f"receipt.json missing in {bundle_dir}"

    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))

    actual_novella_sha = hashlib.sha256(novella_file.read_bytes()).hexdigest()
    actual_dda_sha = hashlib.sha256(dda_file.read_bytes()).hexdigest()
    actual_summary_sha = hashlib.sha256(summary_file.read_bytes()).hexdigest()

    novella_valid = actual_novella_sha == receipt.get("novella_sha256")
    dda_valid = actual_dda_sha == receipt.get("dda_actions_sha256")
    summary_valid = actual_summary_sha == receipt.get("summary_sha256")

    # Verify DDC sequential hash-chain tape
    tape_valid = True
    expected_parent = None
    last_record_sha = None
    for line in dda_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("parent_sha256") != expected_parent:
            tape_valid = False
            break
        # Reconstruct canonical material
        payload = record["payload"]
        sorted_payload = {
            k: payload[k] for k in sorted(payload.keys(), key=lambda s: s.encode("utf-8"))
        }
        material = json.dumps(
            {
                "payload": sorted_payload,
                "parent_sha256": expected_parent,
                "sequence": record["sequence"],
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        calc_sha = hashlib.sha256(material).hexdigest()
        if calc_sha != record.get("record_sha256"):
            tape_valid = False
            break
        expected_parent = calc_sha
        last_record_sha = calc_sha

    head_valid = last_record_sha == receipt.get("dda_head_sha256")

    return {
        "novella_binding": novella_valid,
        "dda_actions_binding": dda_valid,
        "summary_binding": summary_valid,
        "dda_tape_chain": tape_valid,
        "dda_head_binding": head_valid,
        "overall_valid": novella_valid
        and dda_valid
        and summary_valid
        and tape_valid
        and head_valid,
    }


# ==============================================================================
# Suite 1: Micro-USD Precision, Rounding, and Cost Governance
# ==============================================================================


class TestTier5MicroUsdPrecisionAndRounding:
    """Adversarial stress-testing of micro-USD arithmetic, boundaries, and rounding."""

    def test_zero_ceiling_initialization_fails_closed(self) -> None:
        """Audits that BudgetGate rejects ceiling_microusd=0 (zero ceiling forbidden by positive target requirement)."""
        with pytest.raises(ValueError, match="target_microusd must be a positive integer"):
            BudgetGate(ceiling_microusd=0)

        with pytest.raises(ValueError, match="target_microusd must be a positive integer"):
            BudgetGate(ceiling_microusd=0, target_microusd=0)

        with pytest.raises(ValueError, match="target_microusd cannot exceed ceiling_microusd"):
            BudgetGate(ceiling_microusd=0, target_microusd=1)

    def test_minimal_positive_ceiling_and_target(self) -> None:
        """Verifies the minimal valid positive integer ceiling of 1 micro-USD ($0.000001)."""
        gate = BudgetGate(ceiling_microusd=1, target_microusd=1)
        assert gate.ceiling_microusd == 1
        assert gate.target_microusd == 1
        assert gate.spent_microusd == 0
        assert gate.remaining_microusd == 1

        # Pre-call check with 1 uUSD passes
        gate.pre_call_check(1)

        # Pre-call check with 2 uUSD fails-closed
        with pytest.raises(BudgetExceeded) as exc_info:
            gate.pre_call_check(2)
        assert exc_info.value.requested == 2
        assert exc_info.value.limit == 1

    def test_float_type_rejection_in_budget_initialization_and_checks(self) -> None:
        """Audits that float inputs are strictly rejected to prevent IEEE-754 precision poisoning."""
        with pytest.raises(ValueError, match="ceiling_microusd must be a non-negative integer"):
            BudgetGate(ceiling_microusd=250000.0)  # type: ignore

        with pytest.raises(ValueError, match="target_microusd must be a positive integer"):
            BudgetGate(ceiling_microusd=250000, target_microusd=50000.5)  # type: ignore

        gate = BudgetGate()
        with pytest.raises(
            ValueError, match="projected_cost_microusd must be a non-negative integer"
        ):
            gate.pre_call_check(0.05)  # type: ignore (caller passing USD float instead of micro-USD int)

        with pytest.raises(ValueError, match="input_tokens must be a non-negative integer"):
            gate.quote_and_charge_pre_call(
                Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct", input_tokens=10.5
            )  # type: ignore

    def test_fractional_microusd_ceiling_division(self) -> None:
        """Audits the exact integer ceiling division law in _leg_cost_microusd.

        Law: (tokens * price_per_mtok + MICROUSD_PER_MTOK - 1) // MICROUSD_PER_MTOK
        Any non-zero product rounds UP to at least 1 micro-USD.
        """
        # Case 1: 1 token at 1 micro-USD per Mtok = $10^-12 USD -> rounds UP to 1 uUSD ($10^-6 USD)
        assert _leg_cost_microusd(1, 1) == 1

        # Case 2: Exact integer boundary: 1,000,000 tokens at 1 uUSD per Mtok = exact 1 uUSD
        assert _leg_cost_microusd(1_000_000, 1) == 1

        # Case 3: 1,000,001 tokens at 1 uUSD per Mtok = 1.000001 uUSD -> rounds UP to 2 uUSD
        assert _leg_cost_microusd(1_000_001, 1) == 2

        # Case 4: 999,999 tokens at 1 uUSD per Mtok -> rounds UP to 1 uUSD
        assert _leg_cost_microusd(999_999, 1) == 1

        # Case 5: 0 tokens or 0 price yields exact 0
        assert _leg_cost_microusd(0, 100_000) == 0
        assert _leg_cost_microusd(100_000, 0) == 0
        assert _leg_cost_microusd(0, 0) == 0

        # Case 6: Negative values or non-integers are strictly rejected
        with pytest.raises(ValueError, match="tokens and price must be non-negative"):
            _leg_cost_microusd(-1, 100)
        with pytest.raises(ValueError, match="tokens and price must be non-negative"):
            _leg_cost_microusd(100, -1)
        with pytest.raises(TypeError, match="tokens and price must be exact integers"):
            _leg_cost_microusd(100.0, 100)  # type: ignore

    def test_zero_dollar_transaction_allowed_even_at_budget_limit(self) -> None:
        """Verifies that free models ($0.00 / 0 uUSD) succeed even when remaining budget is zero."""
        gate = BudgetGate(ceiling_microusd=100, target_microusd=50)

        # Directly simulate 100 uUSD spent (budget fully exhausted)
        fake_quote = PriceQuoteV1(
            observation=fixture_pricing_observation("test-model", 1000, 1000),
            cost_microusd=100,
        )
        gate.controller.charge("test-model", fake_quote)
        assert gate.spent_microusd == 100
        assert gate.remaining_microusd == 0

        # Pre-call check with 0 uUSD must still PASS because spent + 0 <= limit
        gate.pre_call_check(0)

        # A zero-cost charge succeeds
        zero_quote = PriceQuoteV1(
            observation=fixture_pricing_observation("free-model", 0, 0),
            cost_microusd=0,
        )
        receipt = gate.controller.charge("free-model", zero_quote)
        assert receipt.cost_microusd == 0
        assert receipt.spent_after_microusd == 100

        # But any positive charge (even 1 uUSD) fails closed
        with pytest.raises(BudgetExceeded):
            gate.pre_call_check(1)

    def test_accounting_dict_subcent_precision(self) -> None:
        """Audits precision discrepancies between spent_usd (6 decimals) and budget_ceiling_usd (4 decimals)."""
        gate = BudgetGate(ceiling_microusd=49_999, target_microusd=20_000)
        accounting = gate.to_accounting_dict()

        # Notice: 49_999 / 1_000_000 = 0.049999. Rounded to 4 decimals, it becomes 0.05!
        assert accounting["budget_ceiling_usd"] == 0.05
        assert accounting["spent_microusd"] == 0
        assert accounting["remaining_microusd"] == 49_999

        # Simulate spending 1 uUSD ($0.000001)
        fake_quote = PriceQuoteV1(
            observation=fixture_pricing_observation("micro-model", 1, 1),
            cost_microusd=1,
        )
        gate.controller.charge("micro-model", fake_quote)
        updated_accounting = gate.to_accounting_dict()
        assert updated_accounting["total_billed_cost_usd"] == 0.000001
        assert updated_accounting["spent_microusd"] == 1
        assert updated_accounting["remaining_microusd"] == 49_998
        assert updated_accounting["within_budget"] is True
        assert updated_accounting["within_target"] is True

    def test_provider_argument_validation_and_type_coercion(self) -> None:
        """Audits provider parameter validation: valid string, enum, invalid string, invalid type."""
        gate = BudgetGate()

        # Valid Provider enum
        spec1 = gate.validate_model(Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct")
        assert spec1.model_id == "meta-llama/llama-3.3-70b-instruct"

        # Valid string (case-insensitive)
        spec2 = gate.validate_model("openrouter", "meta-llama/llama-3.3-70b-instruct")
        assert spec2.model_id == "meta-llama/llama-3.3-70b-instruct"

        # Invalid string provider
        with pytest.raises(ValueError, match="is not a valid Provider"):
            gate.validate_model("unsupported_cloud_provider", "meta-llama/llama-3.3-70b-instruct")

        # Invalid type provider (e.g. integer or list)
        with pytest.raises(TypeError, match="Invalid provider: 42"):
            gate.validate_model(42, "meta-llama/llama-3.3-70b-instruct")  # type: ignore

    def test_quote_model_mismatch_in_budget_controller(self) -> None:
        """Audits that BudgetController.charge rejects quotes for a different model deployment ID."""
        controller = BudgetController(limit_microusd=1000)
        quote = PriceQuoteV1(
            observation=fixture_pricing_observation("model-A", 10, 10),
            cost_microusd=10,
        )
        with pytest.raises(ValueError, match="quote model does not match charged model"):
            controller.charge("model-B", quote)

    def test_stale_pricing_observation_raises_unavailable(self) -> None:
        """Audits that PriceTable.quote rejects stale price observations past stale_after_utc."""
        table = PriceTable.builtin()
        # Probe deep in future (year 2030) where builtin observations have expired
        with pytest.raises(ModelNotAllowed) as exc_info:
            table.quote(
                "claude-sonnet-4-20250514",
                input_tokens=100,
                output_tokens=100,
                at_utc="2030-01-01T00:00:00.000000Z",
            )
        assert "PRICE_OBSERVATION_STALE" in str(exc_info.value)


# ==============================================================================
# Suite 2: WolandGate StructureBench Protocol & Cryptographic Integrity
# ==============================================================================


class TestTier5WolandGateStructureBenchProtocol:
    """Adversarial stress-testing of WolandGate StructureBench write order and file bindings."""

    @pytest.fixture
    def temp_sink_roots(self, tmp_path: Path) -> tuple[Path, Path]:
        woland_root = tmp_path / "intel_root"
        return woland_root, tmp_path

    def test_reverse_write_order_cryptographic_seal(
        self, temp_sink_roots: tuple[Path, Path]
    ) -> None:
        """Verifies that all 4 files are generated, written in order, and cryptographically sealed."""
        repo_root, _ = temp_sink_roots
        gate = WolandGate(base_repo_root=repo_root)

        case_results = [{"verdict": "PASS", "agreement": True}]
        claim_hygiene = {
            "supports": "Stabilizer test",
            "does_not_support": "Uncertified approximations",
            "narrowest_defensible_claim": "Single case passes",
            "next_test_needed": "None",
        }

        verdict, p_woland, p_sg, digests = gate.evaluate_and_persist(
            task_key="tier5_seal_test",
            run_id="run_tier5_seal",
            case_results=case_results,
            claim_hygiene=claim_hygiene,
        )

        assert verdict == TERMINAL_REFERENCE_SELF_CONSISTENT
        assert p_woland.exists()
        assert p_sg.exists()

        # Verify cryptographic binding for both sinks
        check_w = verify_bundle_hash_bindings(p_woland)
        assert check_w["overall_valid"] is True

        check_sg = verify_bundle_hash_bindings(p_sg)
        assert check_sg["overall_valid"] is True

    def test_novella_modification_breaks_binding(self, temp_sink_roots: tuple[Path, Path]) -> None:
        """Injects 1 single byte corruption into novella.md and asserts detection."""
        repo_root, _ = temp_sink_roots
        gate = WolandGate(base_repo_root=repo_root)

        _, p_woland, _, _ = gate.evaluate_and_persist(
            task_key="novella_corrupt_test",
            run_id="run_novella_corrupt",
            case_results=[{"verdict": "PASS", "agreement": True}],
            claim_hygiene={
                "supports": "T",
                "does_not_support": "F",
                "narrowest_defensible_claim": "N",
                "next_test_needed": "X",
            },
        )

        # Tamper with novella.md
        novella_file = p_woland / "novella.md"
        content = novella_file.read_text(encoding="utf-8")
        novella_file.write_text(content + "\n<!-- malicious injection -->\n", encoding="utf-8")

        check = verify_bundle_hash_bindings(p_woland)
        assert check["novella_binding"] is False
        assert check["overall_valid"] is False

    def test_summary_verdict_tampering_breaks_binding(
        self, temp_sink_roots: tuple[Path, Path]
    ) -> None:
        """Injects a label alteration (inconsistent -> consistent) into summary.json and asserts detection."""
        repo_root, _ = temp_sink_roots
        gate = WolandGate(base_repo_root=repo_root)

        # Force a REFUSE verdict via defect_count=1
        verdict, p_woland, _, _ = gate.evaluate_and_persist(
            task_key="summary_corrupt_test",
            run_id="run_summary_corrupt",
            case_results=[{"verdict": "FAIL", "agreement": False}],
            claim_hygiene={
                "supports": "T",
                "does_not_support": "F",
                "narrowest_defensible_claim": "N",
                "next_test_needed": "X",
            },
            defect_count=1,
        )
        assert verdict == TERMINAL_REFUSE

        summary_file = p_woland / "summary.json"
        summary_data = json.loads(summary_file.read_text(encoding="utf-8"))
        assert summary_data["verdict"] == TERMINAL_REFUSE

        # Adversary attempts to forge REFERENCE_SELF_CONSISTENT in summary.json
        summary_data["verdict"] = TERMINAL_REFERENCE_SELF_CONSISTENT
        summary_file.write_text(
            json.dumps(summary_data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        check = verify_bundle_hash_bindings(p_woland)
        assert check["summary_binding"] is False
        assert check["overall_valid"] is False

    def test_dda_actions_tape_break_and_tail_truncation(
        self, temp_sink_roots: tuple[Path, Path]
    ) -> None:
        """Audits both sequential parent_sha256 tape breakage and tail truncation in dda_actions.jsonl.

        Counterexample (old tape): eight rows of constant metadata; the tape now holds three measured rows.
        """
        repo_root, _ = temp_sink_roots
        gate = WolandGate(base_repo_root=repo_root)

        _, p_woland, _, _ = gate.evaluate_and_persist(
            task_key="dda_tamper_test",
            run_id="run_dda_tamper",
            case_results=[{"verdict": "PASS", "agreement": True}],
            claim_hygiene={
                "supports": "T",
                "does_not_support": "F",
                "narrowest_defensible_claim": "N",
                "next_test_needed": "X",
            },
        )

        dda_file = p_woland / "dda_actions.jsonl"
        lines = dda_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 3  # intake, scoring, label: measured values only

        # Experiment A: Tail Truncation (remove the label row)
        truncated_lines = lines[:-1]
        dda_file.write_text("\n".join(truncated_lines) + "\n", encoding="utf-8")

        check = verify_bundle_hash_bindings(p_woland)
        assert check["dda_actions_binding"] is False
        # Even if someone forged dda_actions_sha256 in receipt.json, head check fails:
        receipt_file = p_woland / "receipt.json"
        receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))
        receipt_data["dda_actions_sha256"] = hashlib.sha256(dda_file.read_bytes()).hexdigest()
        receipt_file.write_text(
            json.dumps(receipt_data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        check2 = verify_bundle_hash_bindings(p_woland)
        assert check2["dda_actions_binding"] is True  # forged file hash matches
        assert check2["dda_head_binding"] is False  # but head record does not match!
        assert check2["overall_valid"] is False

    def test_run_key_sanitization_defense_in_depth(self) -> None:
        """Audits that sanitize_run_key neutralizes path traversals and illegal filesystem symbols."""
        assert sanitize_run_key("../../etc/passwd") == ".._.._etc_passwd"
        assert sanitize_run_key("..\\..\\windows\\system32") == ".._.._windows_system32"
        assert sanitize_run_key("task:key 1/2") == "task-key_1_2"
        assert sanitize_run_key("   ") == "c021_run"
        assert sanitize_run_key("") == "c021_run"

    def test_atomic_tempdir_cleanup_on_injected_write_error(self, tmp_path: Path) -> None:
        """An error during bundle writing leaves a failure receipt in the run folder and deletes nothing.

        Counterexample: the staging folder was rmtree'd on failure, so a failed run left no record.
        """
        target_dir = tmp_path / "failing_run"

        # Mock json.dumps to raise during summary serialization
        original_dumps = json.dumps

        def mocked_dumps(obj: Any, *args: Any, **kwargs: Any) -> str:
            if isinstance(obj, dict) and obj.get("receipt_id") == "receipt_failing_run":
                raise IOError("Injected disk failure during summary writing")
            return original_dumps(obj, *args, **kwargs)

        with patch("json.dumps", side_effect=mocked_dumps):
            with pytest.raises(IOError, match="Injected disk failure"):
                persist_single_bundle(
                    target_dir=target_dir,
                    novella_md="# Novella",
                    dda_steps=[],
                    summary_data={"receipt_id": "receipt_failing_run"},
                    receipt_data={"receipt_id": "receipt_failing_run"},
                )

        # The staged files and a failure receipt were moved into the target directory
        assert target_dir.is_dir()
        failure = json.loads((target_dir / "failure_receipt.json").read_text(encoding="utf-8"))
        assert failure["status"] == "RUN_FAILED"
        assert failure["error_type"] == "OSError"
        assert {"novella.md", "dda_actions.jsonl"} <= set(failure["files_present"])
        # No staging folder is left behind next to it
        leftovers = list(tmp_path.glob(".*"))
        assert len(leftovers) == 0

    def test_woland_gate_authority_effect_enforcement(
        self, temp_sink_roots: tuple[Path, Path]
    ) -> None:
        """Audits that WolandGate strictly forces AuthorityEffect: 'None' regardless of caller input."""
        repo_root, _ = temp_sink_roots
        gate = WolandGate(base_repo_root=repo_root)

        # The gate writes authority_effect itself; callers have no parameter to raise it

        _, p_woland, _, _ = gate.evaluate_and_persist(
            task_key="auth_effect_test",
            run_id="run_auth_effect",
            case_results=[{"verdict": "PASS", "agreement": True}],
            claim_hygiene={
                "supports": "T",
                "does_not_support": "F",
                "narrowest_defensible_claim": "N",
                "next_test_needed": "X",
            },
        )

        summary_out = json.loads((p_woland / "summary.json").read_text(encoding="utf-8"))
        receipt_out = json.loads((p_woland / "receipt.json").read_text(encoding="utf-8"))
        novella_out = (p_woland / "novella.md").read_text(encoding="utf-8")

        assert summary_out["authority_effect"] == "None"
        assert receipt_out["authority_effect"] == "None"
        assert "**AuthorityEffect**: None" in novella_out

    def test_woland_gate_empty_cases_verdict_refuse(self) -> None:
        """Audits that an empty case_results list deterministically yields TERMINAL_REFUSE."""
        gate = WolandGate()
        verdict = gate.determine_terminal_verdict([])
        assert verdict == TERMINAL_REFUSE

    def test_woland_gate_defect_overrides_closed_residual(self) -> None:
        """Audits that defect_count > 0 takes priority over has_closed_residual, forcing TERMINAL_REFUSE."""
        gate = WolandGate()
        verdict = gate.determine_terminal_verdict(
            [{"verdict": "PASS", "agreement": True}],
            defect_count=1,
            has_closed_residual=True,
        )
        assert verdict == TERMINAL_REFUSE

    def test_woland_gate_phi1_gamma2_precision_thresholds(self) -> None:
        """Defect values are exact and have no tolerance.

        Counterexample: phi1=gamma2=1e-6 (floats) passed under a 1e-6 tolerance. Only an exact zero is
        consistent; any measured non-zero Fraction is inconsistent; floats and bools are refused.
        """
        gate = WolandGate()
        cases = [{"verdict": "PASS", "agreement": True}]

        # Exact zero (or not measured) -> REFERENCE_SELF_CONSISTENT
        assert (
            gate.determine_terminal_verdict(cases, phi1=Fraction(0), gamma2=0)
            == TERMINAL_REFERENCE_SELF_CONSISTENT
        )
        assert gate.determine_terminal_verdict(cases) == TERMINAL_REFERENCE_SELF_CONSISTENT

        # Any measured non-zero value, however small -> REFERENCE_SELF_INCONSISTENT
        assert (
            gate.determine_terminal_verdict(cases, phi1=Fraction(1, 10**6), gamma2=0)
            == TERMINAL_REFUSE
        )
        assert (
            gate.determine_terminal_verdict(cases, phi1=0, gamma2=Fraction(1, 10**12))
            == TERMINAL_REFUSE
        )

        # Floats and bools are refused
        with pytest.raises(TypeError):
            gate.determine_terminal_verdict(cases, phi1=1e-6, gamma2=1e-6)
        with pytest.raises(TypeError):
            gate.determine_terminal_verdict(cases, phi1=0.0)
        with pytest.raises(TypeError):
            gate.determine_terminal_verdict(cases, gamma2=False)


# ==============================================================================
# Suite 3: CommitRevealRunner Sequence, Manifest Security, and CLI
# ==============================================================================


class TestTier5CommitRevealRunnerAdversarial:
    """Adversarial testing of CommitRevealRunner sequence guards, manifest integrity, and CLI."""

    @pytest.fixture
    def isolated_challenge_env(self, tmp_path: Path) -> Path:
        """Creates an isolated replica of the challenge structure in tmp_path."""
        challenge_root = tmp_path / "c021_challenge"
        challenge_root.mkdir()

        # Copy essential folders from real project
        real_root = Path(__file__).resolve().parents[1]

        # 1. reference_solver
        shutil.copytree(real_root / "reference_solver", challenge_root / "reference_solver")
        # 2. judge_packet
        shutil.copytree(real_root / "judge_packet", challenge_root / "judge_packet")

        (challenge_root / "commitments").mkdir()
        return challenge_root

    def test_out_of_order_phases_fail_closed(
        self, isolated_challenge_env: Path, tmp_path: Path
    ) -> None:
        """Audits strict sequence enforcement: Phase 2 without 1, Phase 3 without 1 & 2."""
        runner = CommitRevealRunner(
            challenge_root=isolated_challenge_env,
            intelligence_repo_root=tmp_path,
        )

        # Phase 2 called before Phase 1
        with pytest.raises(RuntimeError, match="Phase 1 judge commitment must precede Phase 2"):
            runner.run_phase2_freeze_record()

        # Phase 3 called before Phase 1 & 2
        with pytest.raises(
            RuntimeError, match="Both judge commitment and solver freeze record must exist"
        ):
            runner.run_phase3_reveal_and_score()

        # Execute Phase 1
        runner.run_phase1_judge_commitment()

        # Phase 3 called after Phase 1 but before Phase 2
        with pytest.raises(
            RuntimeError, match="Both judge commitment and solver freeze record must exist"
        ):
            runner.run_phase3_reveal_and_score()

    def test_missing_manifest_fails_phase1(self, isolated_challenge_env: Path) -> None:
        """Audits FileNotFoundError when judge_packet/manifest.json is absent."""
        manifest_file = isolated_challenge_env / "judge_packet" / "manifest.json"
        manifest_file.unlink()

        runner = CommitRevealRunner(challenge_root=isolated_challenge_env)
        with pytest.raises(FileNotFoundError, match="Judge manifest not found"):
            runner.run_phase1_judge_commitment()

    def test_corrupt_manifest_json_fails_phase1(self, isolated_challenge_env: Path) -> None:
        """Audits json.JSONDecodeError when manifest.json contains syntax garbage."""
        manifest_file = isolated_challenge_env / "judge_packet" / "manifest.json"
        manifest_file.write_text("{ malformed json syntax : [ missing braces", encoding="utf-8")

        runner = CommitRevealRunner(challenge_root=isolated_challenge_env)
        with pytest.raises(json.JSONDecodeError):
            runner.run_phase1_judge_commitment()

    def test_missing_solver_file_fails_phase2(self, isolated_challenge_env: Path) -> None:
        """Audits FileNotFoundError when a frozen solver file is missing."""
        runner = CommitRevealRunner(challenge_root=isolated_challenge_env)
        runner.run_phase1_judge_commitment()

        # Remove ddc_tracer.py
        tracer_file = isolated_challenge_env / "reference_solver" / "ddc_tracer.py"
        tracer_file.unlink()

        with pytest.raises(FileNotFoundError, match="Solver file not found"):
            runner.run_phase2_freeze_record()

    def test_judge_case_count_mismatch_fails_phase3(
        self, isolated_challenge_env: Path, tmp_path: Path
    ) -> None:
        """Audits ValueError when the case files on disk differ from the count the manifest declares.

        Counterexample: the expected count was a hard-coded 46; it now comes from the committed manifest.
        """
        runner = CommitRevealRunner(
            challenge_root=isolated_challenge_env,
            intelligence_repo_root=tmp_path,
        )
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        # Delete one case file
        case_01 = isolated_challenge_env / "judge_packet" / "cases" / "base" / "case_01.json"
        case_01.unlink()

        # Update manifest to match so manifest check doesn't trip first
        manifest_file = isolated_challenge_env / "judge_packet" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data["files"] = [
            f for f in manifest_data["files"] if not f["path"].endswith("case_01.json")
        ]
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        # Re-commit Phase 1 and 2 to test the count guard specifically
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        declared = manifest_data["case_counts"]["total_cases"]
        found = sum(
            len(list((isolated_challenge_env / "judge_packet" / "cases" / sub).glob("*.json")))
            for sub in ("base", "controls", "poisoned")
        )
        assert found == declared - 1
        with pytest.raises(
            ValueError, match=f"Expected exactly {declared} judge cases, found {found}"
        ):
            runner.run_phase3_reveal_and_score()

    def test_manifest_path_traversal_behavior(
        self, isolated_challenge_env: Path, tmp_path: Path
    ) -> None:
        """Audits whether CommitRevealRunner handles manifest entries with path traversal attempts."""
        runner = CommitRevealRunner(
            challenge_root=isolated_challenge_env,
            intelligence_repo_root=tmp_path,
        )

        manifest_file = isolated_challenge_env / "judge_packet" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))

        # Inject an entry referencing a file outside judge_packet
        manifest_data["files"].append(
            {
                "path": "../commitments/c021_q40_r_judge_commitment.json",
                "sha256": "0" * 64,
            }
        )
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        # Phase 1 commits whatever is in manifest
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        # In Phase 3, this path traversal attempt is caught by the containment guard
        with pytest.raises(ValueError, match="Manifest path escape detected"):
            runner.run_phase3_reveal_and_score()

    def test_cli_parsing_and_exit_codes(self) -> None:
        """Audits CLI parsing for --phase options and invalid arguments."""
        # Test invalid phase choice raises SystemExit 2
        with patch.object(sys, "argv", ["commit_reveal_runner.py", "--phase", "99"]):
            with pytest.raises(SystemExit) as exc_info:
                commit_reveal_main()
            assert exc_info.value.code == 2

    def test_cli_custom_task_key_collision_raises(
        self, isolated_challenge_env: Path, tmp_path: Path
    ) -> None:
        """Audits that supplying an already-existing custom --task-key raises RunFolderExistsError."""
        intel_root = tmp_path / "intel_cli_test"
        existing_run = intel_root / "_intelligence" / "_woland" / "runs" / "custom_collision_key"
        existing_run.mkdir(parents=True)

        runner = CommitRevealRunner(
            challenge_root=isolated_challenge_env,
            intelligence_repo_root=intel_root,
        )
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        with pytest.raises(RunFolderExistsError):
            runner.run_phase3_reveal_and_score(task_key="custom_collision_key")

    def test_unwritable_commitments_directory_raises_permission_error(
        self, isolated_challenge_env: Path
    ) -> None:
        """Audits that filesystem PermissionError on commitments writing is propagated fail-closed."""
        runner = CommitRevealRunner(challenge_root=isolated_challenge_env)

        with patch.object(
            Path, "write_bytes", side_effect=PermissionError("Permission denied: [WinError 5]")
        ):
            with pytest.raises(PermissionError, match="Permission denied"):
                runner.run_phase1_judge_commitment()

    def test_manifest_path_traversal_escapes_judge_packet_boundary(
        self, isolated_challenge_env: Path, tmp_path: Path
    ) -> None:
        """Audits that CommitRevealRunner strictly rejects manifest entries escaping judge_packet boundary.

        Verifies that rel_file.resolve().is_relative_to(judge_packet_dir.resolve()) blocks
        manifest entries attempting to traverse into parent or sibling directories.
        """
        runner = CommitRevealRunner(
            challenge_root=isolated_challenge_env,
            intelligence_repo_root=tmp_path,
        )

        # Target file outside judge_packet
        target_outside = isolated_challenge_env / "reference_solver" / "solver.py"
        real_sha = sha256_of_file(target_outside)

        manifest_file = isolated_challenge_env / "judge_packet" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))

        # Add traversal entry referencing file in reference_solver
        manifest_data["files"].append(
            {
                "path": "../reference_solver/solver.py",
                "sha256": real_sha,
            }
        )
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        # Phase 1 commits the manifest
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        # In Phase 3, this path escape is detected fail-closed
        with pytest.raises(ValueError, match="Manifest path escape detected"):
            runner.run_phase3_reveal_and_score(task_key="traversal_test_run")


# ==============================================================================
# Suite 4: Participant Packet Runner Resilience
# ==============================================================================


class TestTier5ParticipantRunnerHardening:
    """Adversarial stress-testing of participant_packet/runner.py against malformed inputs and hostile solvers."""

    def test_load_solver_nonexistent_file(self, tmp_path: Path) -> None:
        """Audits FileNotFoundError when solver path does not exist."""
        with pytest.raises(FileNotFoundError, match="Solver file not found"):
            load_solver_func(tmp_path / "non_existent_solver.py")

    def test_load_solver_missing_solve_export(self, tmp_path: Path) -> None:
        """Audits AttributeError when module does not export 'solve'."""
        bad_solver = tmp_path / "bad_solver.py"
        bad_solver.write_text("def not_solve(): pass\n", encoding="utf-8")

        with pytest.raises(AttributeError, match="does not export 'solve"):
            load_solver_func(bad_solver)

    def test_load_solver_syntax_error(self, tmp_path: Path) -> None:
        """Audits SyntaxError when solver contains unparseable code."""
        bad_syntax = tmp_path / "syntax_error.py"
        bad_syntax.write_text("def solve( : syntax error !!!\n", encoding="utf-8")

        with pytest.raises(SyntaxError):
            load_solver_func(bad_syntax)

    def test_load_cases_corrupt_json(self, tmp_path: Path) -> None:
        """Audits JSONDecodeError when cases file is syntactically invalid."""
        corrupt_cases = tmp_path / "corrupt.json"
        corrupt_cases.write_text("{ unclosed json", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            load_cases(corrupt_cases)

    def test_load_cases_polymorphism(self, tmp_path: Path) -> None:
        """Verifies load_cases handles list of cases, single case dict, case with 'input' wrapper, and jsonl."""
        # 1. List of cases
        f1 = tmp_path / "cases_list.json"
        f1.write_text(json.dumps([{"id": "c1"}, {"id": "c2"}]), encoding="utf-8")
        assert len(load_cases(f1)) == 2

        # 2. Wrapped in "input"
        f2 = tmp_path / "wrapped.json"
        f2.write_text(json.dumps({"input": {"id": "c3"}}), encoding="utf-8")
        loaded2 = load_cases(f2)
        assert len(loaded2) == 1
        assert loaded2[0]["id"] == "c3"

        # 3. JSONL with empty lines
        f3 = tmp_path / "cases.jsonl"
        f3.write_text('\n{"id": "c4"}\n\n{"input": {"id": "c5"}}\n\n', encoding="utf-8")
        loaded3 = load_cases(f3)
        assert len(loaded3) == 2
        assert loaded3[0]["id"] == "c4"
        assert loaded3[1]["id"] == "c5"

    def test_runner_catches_arbitrary_solver_crashes(self, tmp_path: Path) -> None:
        """Audits that run_cases NEVER crashes when solve() raises arbitrary exceptions.

        It must record 'status': 'UNKNOWN', 'refusal_code': 'RUNNER_SOLVER_CRASH', and continue.
        """

        def crashing_solver(case: dict[str, Any]) -> dict[str, Any]:
            case_id = case.get("id")
            if case_id == "zero_div":
                raise ZeroDivisionError("division by zero in solver")
            elif case_id == "key_error":
                raise KeyError("missing required key")
            elif case_id == "type_error":
                raise TypeError("unsupported operand")
            return {"id": case_id, "status": "SOLVED"}

        cases = [
            {"id": "zero_div"},
            {"id": "normal_1"},
            {"id": "key_error"},
            {"id": "normal_2"},
            {"id": "type_error"},
        ]

        out_file = tmp_path / "answers.jsonl"
        count = run_cases(crashing_solver, cases, out_file)
        assert count == 5

        lines = [json.loads(line) for line in out_file.read_text(encoding="utf-8").splitlines()]
        assert len(lines) == 5

        # Check crashing cases were handled cleanly
        assert lines[0]["status"] == "UNKNOWN"
        assert lines[0]["refusal_code"] == "RUNNER_SOLVER_CRASH"
        assert "division by zero" in lines[0]["error"]

        assert lines[1]["status"] == "SOLVED"

        assert lines[2]["status"] == "UNKNOWN"
        assert lines[2]["refusal_code"] == "RUNNER_SOLVER_CRASH"

        assert lines[3]["status"] == "SOLVED"

        assert lines[4]["status"] == "UNKNOWN"
        assert lines[4]["refusal_code"] == "RUNNER_SOLVER_CRASH"

    def test_run_cases_missing_id_defaults_to_unnamed_case(self, tmp_path: Path) -> None:
        """Verifies fallback to 'unnamed_case' when neither 'id' nor 'case_id' is present."""

        def crashing_solver(case: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError("crash")

        cases = [{}]
        out_file = tmp_path / "answers.jsonl"
        run_cases(crashing_solver, cases, out_file)

        line = json.loads(out_file.read_text(encoding="utf-8").strip())
        assert line["id"] == "unnamed_case"

    def test_canonical_json_rfc8785_formatting(self) -> None:
        """Verifies canonical JSON string formatting: sorted keys, no whitespace separators."""
        obj = {"z": 1, "a": 2, "m": [3, 2, 1]}
        result = canonical_json_str(obj)
        # RFC 8785: keys sorted, no spaces after colons or commas
        assert result == '{"a":2,"m":[3,2,1],"z":1}'

    def test_participant_runner_cli_integration(self, tmp_path: Path) -> None:
        """Audits participant runner CLI execution with custom --cases and --output."""
        test_case = tmp_path / "test_case.json"
        test_case.write_text(json.dumps({"id": "cli_test", "n": 1, "terms": []}), encoding="utf-8")
        out_file = tmp_path / "cli_answers.jsonl"

        cli_args = [
            "runner.py",
            "--cases",
            str(test_case),
            "--output",
            str(out_file),
        ]
        with patch.object(sys, "argv", cli_args):
            exit_code = participant_runner_main()
            assert exit_code == 0

        assert out_file.exists()
        line = json.loads(out_file.read_text(encoding="utf-8").strip())
        assert line["id"] == "cli_test"
