"""Adversarial Stress-Test Harness for C021 Budget Gate & Cost Governance.

Challenger 2 (Milestone 3 - C021 Q40-R Stabilizer Challenge).
Empirically stress-tests budget_gate.py and SG-CP v1 cost governance rules against:
1. Hard ceiling enforcement:
   - Initializing BudgetGate with ceiling > $0.25 (e.g. 250,001 uUSD, 1,000,000 uUSD) -> BudgetCeilingExceededError.
   - Initializing with float inputs (0.250001, 1.00) -> TypeError / ValueError.
   - Initializing with ceiling == $0.25 (250,000 uUSD) -> Admitted.
2. Fail-closed pre-call checks & zero-spend invariant:
   - Single quote exceeding ceiling -> BudgetExceeded raised before execution.
   - Spent remains exactly 0 (or unchanged) after pre-call failure.
   - Accumulated spend approaching and exceeding ceiling -> pre-call halt.
   - Strict target (< $0.05) vs hard ceiling (<= $0.25) boundary checks.
3. Model parameter ceilings & registry governance:
   - 70B exact open-weights admitted (e.g. Llama-3.3-70B, Llama-3.1-70B, Nemotron-70B).
   - < 70B open-weights admitted (e.g. Qwen-2.5-32B, Qwen-2.5-7B, Llama-3.1-8B, Qwen-0.5B).
   - 70.1B rejected fail-closed (synthetic 70.1B spec).
   - 72B rejected fail-closed (Qwen-2.5-72B).
   - 141B MoE rejected fail-closed (Mixtral-8x22B total parameters count).
   - 400B MoE rejected fail-closed (Llama-4-Maverick 400B total / 17B active).
   - 671B MoE rejected fail-closed (DeepSeek-R1 671B total / 37B active).
   - Unknown size / undisclosed / closed-weights rejected (Gemini Flash, GPT-4o-mini, Claude Sonnet).
   - Unregistered models rejected fail-closed.
4. allow_fallbacks=True strict refusal:
   - allow_fallbacks=True in validate_model -> FallbackNotAllowedError.
   - allow_fallbacks=True in quote_and_charge_pre_call -> FallbackNotAllowedError.
   - Non-boolean and non-False values (1, "true", None, 0) -> FallbackNotAllowedError.
5. Edge cases, negative budgets, zero ceilings, currency mismatches:
   - Negative ceiling / target -> ValueError.
   - Zero ceiling -> fails closed with ValueError.
   - Negative tokens / negative projected costs -> ValueError.
   - Currency mismatch (float USD, strings, booleans as ints) -> ValueError.
   - Edge-case token counts (0 tokens, 1B tokens, 2^60 tokens).
6. Malformed accounting dicts & conservation laws:
   - Schema adherence to SG-CP v1 (§3).
   - Conservation law: spent + remaining == limit.
   - Adversarial validator detecting corruptions (drift, negative spend, contradictory flags).

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from typing import Any, Mapping

import pytest
from projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.budget_gate import (
    FALLBACK_NOT_ALLOWED,
    BudgetCeilingExceededError,
    BudgetGate,
    FallbackNotAllowedError,
)

from adversary.domain.providers.model_registry import (
    ModelNotAllowed,
    ModelNotRegistered,
    ModelParameterCeilingRefused,
    ModelRegistry,
    ModelSpecV1,
)
from adversary.domain.providers.types import (
    BudgetExceeded,
    Provider,
)


def validate_sg_cp_v1_accounting_dict(acct: Mapping[str, Any]) -> tuple[bool, str]:
    """Independent oracle validating that an accounting dictionary obeys SG-CP v1 rules."""
    required_keys = {
        "budget_ceiling_usd",
        "budget_target_usd",
        "total_billed_cost_usd",
        "spent_microusd",
        "remaining_microusd",
        "within_budget",
        "within_target",
        "model_parameter_ceiling",
        "allow_fallbacks",
        "authority_effect",
    }
    missing = required_keys - set(acct.keys())
    if missing:
        return False, f"Missing required keys: {sorted(missing)}"

    # 1. Type assertions
    if type(acct["budget_ceiling_usd"]) not in (float, int) or acct["budget_ceiling_usd"] < 0:
        return False, f"Invalid budget_ceiling_usd: {acct['budget_ceiling_usd']}"
    if type(acct["budget_target_usd"]) not in (float, int) or acct["budget_target_usd"] < 0:
        return False, f"Invalid budget_target_usd: {acct['budget_target_usd']}"
    if type(acct["total_billed_cost_usd"]) not in (float, int) or acct["total_billed_cost_usd"] < 0:
        return False, f"Invalid total_billed_cost_usd: {acct['total_billed_cost_usd']}"
    if type(acct["spent_microusd"]) is not int or acct["spent_microusd"] < 0:
        return False, f"Invalid spent_microusd: {acct['spent_microusd']}"
    if type(acct["remaining_microusd"]) is not int or acct["remaining_microusd"] < 0:
        return False, f"Invalid remaining_microusd: {acct['remaining_microusd']}"
    if type(acct["within_budget"]) is not bool:
        return False, f"Invalid within_budget: {acct['within_budget']}"
    if type(acct["within_target"]) is not bool:
        return False, f"Invalid within_target: {acct['within_target']}"
    if type(acct["model_parameter_ceiling"]) is not str:
        return False, f"Invalid model_parameter_ceiling: {acct['model_parameter_ceiling']}"
    if type(acct["allow_fallbacks"]) is not bool:
        return False, f"Invalid allow_fallbacks: {acct['allow_fallbacks']}"
    if acct["authority_effect"] != "None":
        return False, f"Invalid authority_effect: {acct['authority_effect']}"

    # 2. SG-CP v1 Hard Ceiling Law: budget_ceiling_usd <= 0.25
    if acct["budget_ceiling_usd"] > 0.25 + 1e-9:
        return False, f"budget_ceiling_usd {acct['budget_ceiling_usd']} exceeds $0.25 ceiling"

    # 3. Model parameter ceiling: must be exactly "70B"
    if acct["model_parameter_ceiling"] != "70B":
        return False, f"model_parameter_ceiling {acct['model_parameter_ceiling']} != '70B'"

    # 4. Fallback mandate: must be False
    if acct["allow_fallbacks"] is not False:
        return False, f"allow_fallbacks must be False, got {acct['allow_fallbacks']}"

    # 5. Exact Conservation Law: spent + remaining == ceiling in micro-USD
    ceiling_microusd = int(round(acct["budget_ceiling_usd"] * 1_000_000))
    if acct["spent_microusd"] + acct["remaining_microusd"] != ceiling_microusd:
        return False, (
            f"Conservation violated: spent ({acct['spent_microusd']}) + "
            f"remaining ({acct['remaining_microusd']}) != ceiling ({ceiling_microusd})"
        )

    # 6. Currency parity: total_billed_cost_usd must match spent_microusd / 1M
    expected_usd = round(acct["spent_microusd"] / 1_000_000, 6)
    if abs(acct["total_billed_cost_usd"] - expected_usd) > 1e-5:
        return False, (
            f"Cost drift: total_billed_cost_usd ({acct['total_billed_cost_usd']}) != "
            f"spent_microusd / 1M ({expected_usd})"
        )

    # 7. Logical consistency of within_budget flag
    if acct["within_budget"] != (acct["spent_microusd"] <= ceiling_microusd):
        return False, "within_budget flag contradicts spent vs ceiling"

    # 8. Logical consistency of within_target flag
    target_microusd = int(round(acct["budget_target_usd"] * 1_000_000))
    if acct["within_target"] != (acct["spent_microusd"] < target_microusd):
        return False, "within_target flag contradicts spent vs target (< $0.05)"

    return True, "VALID"


class TestAdversarialBudgetGate(unittest.TestCase):
    """Empirical adversarial test harness for budget_gate.py."""

    # =========================================================================
    # Family 1: Hard Ceiling Enforcement
    # =========================================================================

    def test_ceiling_exceeded_by_one_microusd(self) -> None:
        """Attempting to declare ceiling $0.250001 (250,001 uUSD) must fail with BudgetCeilingExceededError."""
        with pytest.raises(BudgetCeilingExceededError) as exc_info:
            BudgetGate(ceiling_microusd=250_001)
        self.assertIn("exceeds hard challenge ceiling", str(exc_info.value))

    def test_ceiling_exceeded_one_dollar(self) -> None:
        """Attempting to declare ceiling $1.00 (1,000,000 uUSD) must fail with BudgetCeilingExceededError."""
        with pytest.raises(BudgetCeilingExceededError) as exc_info:
            BudgetGate(ceiling_microusd=1_000_000)
        self.assertIn("exceeds hard challenge ceiling", str(exc_info.value))

    def test_ceiling_exceeded_fifty_cents(self) -> None:
        """Attempting to declare ceiling $0.50 (500,000 uUSD - T2 default) must fail under C021 $0.25 cap."""
        with pytest.raises(BudgetCeilingExceededError) as exc_info:
            BudgetGate(ceiling_microusd=500_000)
        self.assertIn("exceeds hard challenge ceiling", str(exc_info.value))

    def test_ceiling_exact_hard_limit(self) -> None:
        """Initializing with exactly $0.25 (250,000 uUSD) must succeed."""
        gate = BudgetGate(ceiling_microusd=250_000)
        self.assertEqual(gate.limit_microusd, 250_000)
        self.assertEqual(gate.target_microusd, 50_000)
        acct = gate.to_accounting_dict()
        self.assertEqual(acct["budget_ceiling_usd"], 0.25)
        self.assertEqual(acct["within_budget"], True)

    def test_ceiling_below_hard_limit(self) -> None:
        """Initializing with ceiling below $0.25 (e.g. 100,000 uUSD) must succeed."""
        gate = BudgetGate(ceiling_microusd=100_000)
        self.assertEqual(gate.limit_microusd, 100_000)
        self.assertEqual(gate.target_microusd, 50_000)
        acct = gate.to_accounting_dict()
        self.assertEqual(acct["budget_ceiling_usd"], 0.10)

    def test_ceiling_target_greater_than_ceiling_rejected(self) -> None:
        """Initializing with target > ceiling must fail with ValueError."""
        with pytest.raises(ValueError) as exc_info:
            BudgetGate(ceiling_microusd=40_000, target_microusd=50_000)
        self.assertIn("cannot exceed ceiling", str(exc_info.value))

    def test_ceiling_target_auto_capping(self) -> None:
        """If ceiling < target (e.g. 30,000 uUSD) and target is None, target is auto-capped to ceiling."""
        gate = BudgetGate(ceiling_microusd=30_000)
        self.assertEqual(gate.limit_microusd, 30_000)
        self.assertEqual(gate.target_microusd, 30_000)
        acct = gate.to_accounting_dict()
        self.assertEqual(acct["budget_target_usd"], 0.03)

    # =========================================================================
    # Family 2: Fail-Closed Pre-Call Checks & Zero Spend Invariant
    # =========================================================================

    def test_pre_call_single_request_exceeds_ceiling_zero_spend(self) -> None:
        """Simulate request costing > $0.25: confirm BudgetExceeded raised and spend remains 0."""
        gate = BudgetGate()
        self.assertEqual(gate.spent_microusd, 0)
        self.assertEqual(gate.remaining_microusd, 250_000)

        # 3,000,000 input tokens on Llama-3.3-70B costs 300,000 uUSD ($0.30 > $0.25)
        with pytest.raises(BudgetExceeded) as exc_info:
            gate.quote_and_charge_pre_call(
                Provider.OPENROUTER,
                "meta-llama/llama-3.3-70b-instruct",
                input_tokens=3_000_000,
                max_output_tokens=100,
            )

        # CRITICAL ASSERTION: Zero spend occurred prior to execution
        self.assertEqual(
            gate.spent_microusd, 0, "Spend was mutated despite pre-call budget rejection!"
        )
        self.assertEqual(gate.remaining_microusd, 250_000)
        self.assertEqual(gate.spent_usd, 0.0)
        self.assertGreater(exc_info.value.requested, 250_000)
        self.assertEqual(exc_info.value.limit, 250_000)

    def test_pre_call_accumulated_spend_triggers_halt(self) -> None:
        """Accumulate valid charges; verify subsequent exceeding call halts fail-closed without mutating spend."""
        gate = BudgetGate()

        # Call 1: 500,000 input tokens = 50,000 uUSD ($0.05)
        receipt1 = gate.quote_and_charge_pre_call(
            Provider.OPENROUTER,
            "meta-llama/llama-3.3-70b-instruct",
            input_tokens=500_000,
            max_output_tokens=0,
        )
        self.assertEqual(receipt1.cost_microusd, 50_000)
        self.assertEqual(gate.spent_microusd, 50_000)
        self.assertEqual(gate.remaining_microusd, 200_000)

        # Call 2: 1,500,000 input tokens = 150,000 uUSD ($0.15)
        receipt2 = gate.quote_and_charge_pre_call(
            Provider.OPENROUTER,
            "meta-llama/llama-3.3-70b-instruct",
            input_tokens=1_500_000,
            max_output_tokens=0,
        )
        self.assertEqual(receipt2.cost_microusd, 150_000)
        self.assertEqual(gate.spent_microusd, 200_000)
        self.assertEqual(gate.remaining_microusd, 50_000)

        # Call 3: 600,000 input tokens = 60,000 uUSD. 200k + 60k = 260k > 250k ceiling.
        with pytest.raises(BudgetExceeded):
            gate.quote_and_charge_pre_call(
                Provider.OPENROUTER,
                "meta-llama/llama-3.3-70b-instruct",
                input_tokens=600_000,
                max_output_tokens=0,
            )

        # Spend must freeze at 200,000 uUSD; call 3 rejected without charge
        self.assertEqual(gate.spent_microusd, 200_000)
        self.assertEqual(gate.remaining_microusd, 50_000)

    def test_pre_call_direct_check_exceeds(self) -> None:
        """pre_call_check raises BudgetExceeded when projected cost exceeds limit."""
        gate = BudgetGate(ceiling_microusd=100_000)
        gate.pre_call_check(100_000)  # Exact boundary: allowed
        with pytest.raises(BudgetExceeded) as exc_info:
            gate.pre_call_check(100_001)
        self.assertEqual(exc_info.value.requested, 100_001)
        self.assertEqual(exc_info.value.limit, 100_000)
        self.assertEqual(gate.spent_microusd, 0)

    def test_target_boundary_strict_inequality(self) -> None:
        """Target threshold requires strictly less than $0.05 (< 50,000 uUSD)."""
        gate = BudgetGate()
        self.assertTrue(gate.is_within_target)

        # Exactly at target limit (50,000 uUSD) -> is_within_target must be False
        gate.quote_and_charge_pre_call(
            Provider.OPENROUTER,
            "meta-llama/llama-3.3-70b-instruct",
            input_tokens=500_000,
            max_output_tokens=0,
        )
        self.assertEqual(gate.spent_microusd, 50_000)
        self.assertFalse(
            gate.is_within_target, "is_within_target must be False when spent == target"
        )
        self.assertTrue(gate.is_within_hard_ceiling)

    # =========================================================================
    # Family 3: Model Parameter Ceilings & Model Registry Governance
    # =========================================================================

    def test_model_70b_exact_admitted(self) -> None:
        """All 70B open-weights models in registry must be admitted."""
        gate = BudgetGate()
        admitted_models = [
            (Provider.OPENROUTER, "meta-llama/llama-3.3-70b-instruct"),
            (Provider.OPENROUTER, "meta-llama/llama-3.1-70b-instruct"),
            (Provider.OPENROUTER, "deepseek/deepseek-r1-distill-llama-70b"),
            (Provider.NVIDIA, "meta/llama-3.3-70b-instruct"),
            (Provider.NVIDIA, "nvidia/llama-3.1-nemotron-70b-instruct"),
        ]
        for prov, model in admitted_models:
            spec = gate.validate_model(prov, model)
            self.assertEqual(spec.total_parameters, 70_000_000_000)
            self.assertTrue(spec.open_weights)

    def test_model_under_70b_admitted(self) -> None:
        """Models below 70B open weights must be admitted."""
        gate = BudgetGate()
        smaller_models = [
            (Provider.OPENROUTER, "qwen/qwen-2.5-coder-32b-instruct", 32_000_000_000),
            (Provider.OPENROUTER, "qwen/qwen-2.5-7b-instruct", 7_000_000_000),
            (Provider.OPENROUTER, "meta-llama/llama-3.1-8b-instruct", 8_000_000_000),
            (Provider.OPENROUTER, "google/gemma-3-27b-it", 27_000_000_000),
            (Provider.OPENROUTER, "mistralai/mistral-small-24b-instruct-2501", 24_000_000_000),
            (Provider.LOCAL, "qwen2.5:0.5b", 500_000_000),
        ]
        for prov, model, expected_params in smaller_models:
            spec = gate.validate_model(prov, model)
            self.assertEqual(spec.total_parameters, expected_params)
            self.assertTrue(spec.open_weights)

    def test_model_70_1b_rejected(self) -> None:
        """Model with 70.1B parameters (70,100,000,000) must be rejected fail-closed."""
        spec_70_1b = ModelSpecV1(
            Provider.OPENROUTER,
            "synthetic/model-70.1b",
            total_parameters=70_100_000_000,
            open_weights=True,
            architecture="dense",
            source="Test synthetic spec",
        )
        custom_registry = ModelRegistry([spec_70_1b])
        gate = BudgetGate(registry=custom_registry)

        with pytest.raises(ModelParameterCeilingRefused) as exc_info:
            gate.validate_model(Provider.OPENROUTER, "synthetic/model-70.1b")
        self.assertEqual(exc_info.value.code, "MODEL_OVER_PARAMETER_CEILING")
        self.assertIn("70100000000 > 70000000000", str(exc_info.value))

    def test_model_72b_rejected(self) -> None:
        """Qwen-2.5-72B (72B parameters) must be rejected fail-closed."""
        gate = BudgetGate()
        with pytest.raises(ModelParameterCeilingRefused) as exc_info:
            gate.validate_model(Provider.OPENROUTER, "qwen/qwen-2.5-72b-instruct")
        self.assertEqual(exc_info.value.code, "MODEL_OVER_PARAMETER_CEILING")
        self.assertIn("72000000000 > 70000000000", str(exc_info.value))

    def test_model_141b_moe_rejected(self) -> None:
        """Mixtral 8x22B (141B total parameters, 39B active) must be rejected fail-closed under total parameter rule."""
        gate = BudgetGate()
        with pytest.raises(ModelParameterCeilingRefused) as exc_info:
            gate.validate_model(Provider.OPENROUTER, "mistralai/mixtral-8x22b-instruct")
        self.assertEqual(exc_info.value.code, "MODEL_OVER_PARAMETER_CEILING")
        self.assertIn("141000000000 > 70000000000", str(exc_info.value))

    def test_model_400b_moe_rejected(self) -> None:
        """Llama 4 Maverick (400B total, 17B active) must be rejected fail-closed under total parameter rule."""
        gate = BudgetGate()
        with pytest.raises(ModelParameterCeilingRefused) as exc_info:
            gate.validate_model(
                Provider.OPENROUTER, "meta-llama/llama-4-maverick-17b-128e-instruct"
            )
        self.assertEqual(exc_info.value.code, "MODEL_OVER_PARAMETER_CEILING")

    def test_model_671b_moe_rejected(self) -> None:
        """DeepSeek-R1 (671B total, 37B active) must be rejected fail-closed."""
        gate = BudgetGate()
        with pytest.raises(ModelParameterCeilingRefused) as exc_info:
            gate.validate_model(Provider.NVIDIA, "deepseek-ai/deepseek-r1")
        self.assertEqual(exc_info.value.code, "MODEL_OVER_PARAMETER_CEILING")
        self.assertIn("671000000000 > 70000000000", str(exc_info.value))

    def test_model_undisclosed_closed_weights_rejected(self) -> None:
        """Closed-weights or undisclosed parameter models must be rejected fail-closed."""
        gate = BudgetGate()
        closed_models = [
            (Provider.OPENROUTER, "google/gemini-2.5-flash"),
            (Provider.OPENROUTER, "google/gemini-2.5-pro"),
            (Provider.OPENROUTER, "openai/gpt-4o-mini"),
            (Provider.ANTHROPIC, "claude-sonnet-4-20250514"),
            (Provider.OPENAI, "gpt-4o-mini"),
            (Provider.GROK, "grok-2-latest"),
            (Provider.DEEPSEEK, "deepseek-v4-flash"),
            (Provider.GEMINI, "gemini-2.5-flash"),
        ]
        for prov, model in closed_models:
            with pytest.raises(ModelParameterCeilingRefused) as exc_info:
                gate.validate_model(prov, model)
            self.assertEqual(exc_info.value.code, "MODEL_SIZE_UNDISCLOSED")

    def test_model_unregistered_rejected(self) -> None:
        """Unregistered model must raise ModelNotRegistered fail-closed."""
        gate = BudgetGate()
        with pytest.raises(ModelNotRegistered) as exc_info:
            gate.validate_model(Provider.OPENROUTER, "unknown-publisher/unknown-model-999b")
        self.assertEqual(exc_info.value.code, "MODEL_NOT_REGISTERED")

    def test_model_non_open_weights_under_70b_rejected(self) -> None:
        """A model <= 70B but with open_weights=False must be rejected fail-closed."""
        spec_closed = ModelSpecV1(
            Provider.OPENROUTER,
            "proprietary/model-30b",
            total_parameters=30_000_000_000,
            open_weights=False,
            architecture="dense",
            source="Vendor proprietary binary",
        )
        custom_registry = ModelRegistry([spec_closed])
        gate = BudgetGate(registry=custom_registry)

        with pytest.raises(ModelParameterCeilingRefused) as exc_info:
            gate.validate_model(Provider.OPENROUTER, "proprietary/model-30b")
        self.assertEqual(exc_info.value.code, "MODEL_NOT_OPEN_WEIGHTS")

    # =========================================================================
    # Family 4: allow_fallbacks=True Strict Refusal
    # =========================================================================

    def test_allow_fallbacks_true_validate_model_rejected(self) -> None:
        """validate_model with allow_fallbacks=True must raise FallbackNotAllowedError fail-closed."""
        gate = BudgetGate()
        with pytest.raises(FallbackNotAllowedError) as exc_info:
            gate.validate_model(
                Provider.OPENROUTER,
                "meta-llama/llama-3.3-70b-instruct",
                allow_fallbacks=True,
            )
        self.assertEqual(exc_info.value.code, FALLBACK_NOT_ALLOWED)
        self.assertIn("mandates allow_fallbacks: false", str(exc_info.value))

    def test_allow_fallbacks_true_quote_and_charge_rejected(self) -> None:
        """quote_and_charge_pre_call with allow_fallbacks=True must raise FallbackNotAllowedError before pricing/execution."""
        gate = BudgetGate()
        with pytest.raises(FallbackNotAllowedError):
            gate.quote_and_charge_pre_call(
                Provider.OPENROUTER,
                "meta-llama/llama-3.3-70b-instruct",
                input_tokens=100,
                max_output_tokens=100,
                allow_fallbacks=True,
            )
        self.assertEqual(gate.spent_microusd, 0)

    def test_allow_fallbacks_non_boolean_truthy_rejected(self) -> None:
        """Non-boolean truthy values (e.g. 1, 'true', [True]) must fail with FallbackNotAllowedError."""
        gate = BudgetGate()
        for truthy in (1, "true", [True], {"fallback": True}):
            with pytest.raises(FallbackNotAllowedError):
                gate.validate_model(
                    Provider.OPENROUTER,
                    "meta-llama/llama-3.3-70b-instruct",
                    allow_fallbacks=truthy,  # type: ignore[arg-type]
                )

    def test_allow_fallbacks_falsy_non_false_rejected(self) -> None:
        """Non-False falsy values (None, 0, '') must fail fail-closed; only exact literal False is permitted."""
        gate = BudgetGate()
        for falsy in (None, 0, "", ()):
            with pytest.raises(FallbackNotAllowedError):
                gate.validate_model(
                    Provider.OPENROUTER,
                    "meta-llama/llama-3.3-70b-instruct",
                    allow_fallbacks=falsy,  # type: ignore[arg-type]
                )

    # =========================================================================
    # Family 5: Negative Budgets, Zero Ceilings, Currency & Type Mismatches
    # =========================================================================

    def test_negative_ceiling_microusd(self) -> None:
        """Negative ceiling must raise ValueError fail-closed."""
        for bad_ceiling in (-1, -100, -250_000):
            with pytest.raises(ValueError):
                BudgetGate(ceiling_microusd=bad_ceiling)

    def test_negative_target_microusd(self) -> None:
        """Negative target must raise ValueError fail-closed."""
        for bad_target in (-1, -50_000):
            with pytest.raises(ValueError):
                BudgetGate(ceiling_microusd=100_000, target_microusd=bad_target)

    def test_zero_ceiling_microusd_fails_closed(self) -> None:
        """Initializing BudgetGate with ceiling 0 must fail closed with ValueError (positive target required)."""
        with pytest.raises(ValueError) as exc_info:
            BudgetGate(ceiling_microusd=0)
        self.assertIn("target_microusd must be a positive integer", str(exc_info.value))

    def test_zero_target_microusd_fails_closed(self) -> None:
        """Initializing BudgetGate with target 0 must fail closed with ValueError."""
        with pytest.raises(ValueError):
            BudgetGate(ceiling_microusd=100_000, target_microusd=0)

    def test_negative_projected_cost_rejected(self) -> None:
        """Negative projected costs must raise ValueError."""
        gate = BudgetGate()
        for bad_cost in (-1, -10_000):
            with pytest.raises(ValueError):
                gate.pre_call_check(bad_cost)

    def test_negative_token_counts_rejected(self) -> None:
        """Negative input or output tokens must raise ValueError fail-closed."""
        gate = BudgetGate()
        with pytest.raises(ValueError):
            gate.quote_and_charge_pre_call(
                Provider.OPENROUTER,
                "meta-llama/llama-3.3-70b-instruct",
                input_tokens=-1,
                max_output_tokens=100,
            )
        with pytest.raises(ValueError):
            gate.quote_and_charge_pre_call(
                Provider.OPENROUTER,
                "meta-llama/llama-3.3-70b-instruct",
                input_tokens=100,
                max_output_tokens=-1,
            )

    def test_currency_mismatch_float_rejected(self) -> None:
        """Passing float currency (e.g. 0.25 USD) where int micro-USD is required must fail with ValueError."""
        for bad_float in (0.25, 0.250001, 1.00, 0.05):
            with pytest.raises(ValueError):
                BudgetGate(ceiling_microusd=bad_float)  # type: ignore[arg-type]

    def test_currency_mismatch_string_rejected(self) -> None:
        """Passing string currency with symbols ('$0.25', '250000 uUSD') must fail with ValueError."""
        for bad_str in ("$0.25", "0.25 USD", "250000 uUSD", "€0.25"):
            with pytest.raises(ValueError):
                BudgetGate(ceiling_microusd=bad_str)  # type: ignore[arg-type]

    def test_boolean_type_confusion_rejected(self) -> None:
        """Passing boolean True/False for integer parameters must be rejected fail-closed (clean arch type guard)."""
        gate = BudgetGate()
        # Ceiling
        with pytest.raises(ValueError):
            BudgetGate(ceiling_microusd=True)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            BudgetGate(ceiling_microusd=False)  # type: ignore[arg-type]
        # Pre-call check
        with pytest.raises(ValueError):
            gate.pre_call_check(True)  # type: ignore[arg-type]
        # Tokens
        with pytest.raises(ValueError):
            gate.quote_and_charge_pre_call(
                Provider.OPENROUTER,
                "meta-llama/llama-3.3-70b-instruct",
                input_tokens=True,  # type: ignore[arg-type]
                max_output_tokens=100,
            )
        with pytest.raises(ValueError):
            gate.quote_and_charge_pre_call(
                Provider.OPENROUTER,
                "meta-llama/llama-3.3-70b-instruct",
                input_tokens=100,
                max_output_tokens=False,  # type: ignore[arg-type]
            )

    # =========================================================================
    # Family 6: Edge-Case Token Counts & Pricing Quotes
    # =========================================================================

    def test_zero_input_and_zero_output_tokens(self) -> None:
        """0 input and 0 output tokens must result in $0.00 charge without error."""
        gate = BudgetGate()
        receipt = gate.quote_and_charge_pre_call(
            Provider.OPENROUTER,
            "meta-llama/llama-3.3-70b-instruct",
            input_tokens=0,
            max_output_tokens=0,
        )
        self.assertEqual(receipt.cost_microusd, 0)
        self.assertEqual(gate.spent_microusd, 0)

    def test_zero_input_nonzero_output_tokens(self) -> None:
        """0 input and 1,000 output tokens quotes only output leg."""
        gate = BudgetGate()
        # Output rate for Llama-3.3-70B: 320,000 uUSD / Mtok. 1,000 tokens = 320 uUSD.
        receipt = gate.quote_and_charge_pre_call(
            Provider.OPENROUTER,
            "meta-llama/llama-3.3-70b-instruct",
            input_tokens=0,
            max_output_tokens=1_000,
        )
        self.assertEqual(receipt.cost_microusd, 320)
        self.assertEqual(gate.spent_microusd, 320)

    def test_nonzero_input_zero_output_tokens(self) -> None:
        """1,000 input and 0 output tokens quotes only input leg."""
        gate = BudgetGate()
        # Input rate for Llama-3.3-70B: 100,000 uUSD / Mtok. 1,000 tokens = 100 uUSD.
        receipt = gate.quote_and_charge_pre_call(
            Provider.OPENROUTER,
            "meta-llama/llama-3.3-70b-instruct",
            input_tokens=1_000,
            max_output_tokens=0,
        )
        self.assertEqual(receipt.cost_microusd, 100)
        self.assertEqual(gate.spent_microusd, 100)

    def test_extreme_token_counts_billion(self) -> None:
        """1 billion input tokens quotes $100,000; raises BudgetExceeded fail-closed."""
        gate = BudgetGate()
        with pytest.raises(BudgetExceeded):
            gate.quote_and_charge_pre_call(
                Provider.OPENROUTER,
                "meta-llama/llama-3.3-70b-instruct",
                input_tokens=1_000_000_000,
                max_output_tokens=1_000,
            )
        self.assertEqual(gate.spent_microusd, 0)

    def test_extreme_token_counts_64bit_overflow_safety(self) -> None:
        """2^60 input tokens in Python arbitrary-precision int quotes huge cost and halts fail-closed."""
        gate = BudgetGate()
        with pytest.raises(BudgetExceeded):
            gate.quote_and_charge_pre_call(
                Provider.OPENROUTER,
                "meta-llama/llama-3.3-70b-instruct",
                input_tokens=2**60,
                max_output_tokens=100,
            )
        self.assertEqual(gate.spent_microusd, 0)

    def test_invalid_token_types_rejected(self) -> None:
        """Float, string, None, or dict token counts must raise ValueError fail-closed."""
        gate = BudgetGate()
        bad_types = [100.5, "1000", None, [100], {"tokens": 100}]
        for bad in bad_types:
            with pytest.raises((ValueError, TypeError)):
                gate.quote_and_charge_pre_call(
                    Provider.OPENROUTER,
                    "meta-llama/llama-3.3-70b-instruct",
                    input_tokens=bad,  # type: ignore[arg-type]
                    max_output_tokens=100,
                )

    # =========================================================================
    # Family 7: Accounting Dict & SG-CP v1 Cost Governance Conformance
    # =========================================================================

    def test_accounting_dict_valid_under_oracle(self) -> None:
        """BudgetGate.to_accounting_dict() must pass the independent SG-CP v1 oracle at all phases."""
        gate = BudgetGate()
        valid, msg = validate_sg_cp_v1_accounting_dict(gate.to_accounting_dict())
        self.assertTrue(valid, f"Initial accounting dict failed oracle: {msg}")

        # After a valid charge of $0.01
        gate.quote_and_charge_pre_call(
            Provider.OPENROUTER,
            "meta-llama/llama-3.3-70b-instruct",
            input_tokens=100_000,
            max_output_tokens=0,
        )
        valid, msg = validate_sg_cp_v1_accounting_dict(gate.to_accounting_dict())
        self.assertTrue(valid, f"Post-charge accounting dict failed oracle: {msg}")

    def test_adversarial_accounting_dict_validator_catches_corruptions(self) -> None:
        """Verify that the independent oracle detects and rejects corrupted accounting dictionaries."""
        base_gate = BudgetGate()
        clean = base_gate.to_accounting_dict()

        # Corruption A: ceiling > 0.25
        corrupt_a = dict(clean)
        corrupt_a["budget_ceiling_usd"] = 0.50
        corrupt_a["remaining_microusd"] = 500_000
        ok, msg = validate_sg_cp_v1_accounting_dict(corrupt_a)
        self.assertFalse(ok)
        self.assertIn("exceeds $0.25 ceiling", msg)

        # Corruption B: allow_fallbacks is True
        corrupt_b = dict(clean)
        corrupt_b["allow_fallbacks"] = True
        ok, msg = validate_sg_cp_v1_accounting_dict(corrupt_b)
        self.assertFalse(ok)
        self.assertIn("allow_fallbacks must be False", msg)

        # Corruption C: model parameter ceiling != "70B"
        corrupt_c = dict(clean)
        corrupt_c["model_parameter_ceiling"] = "72B"
        ok, msg = validate_sg_cp_v1_accounting_dict(corrupt_c)
        self.assertFalse(ok)
        self.assertIn("model_parameter_ceiling", msg)

        # Corruption D: Conservation law violated (spent + remaining != ceiling)
        corrupt_d = dict(clean)
        corrupt_d["remaining_microusd"] = 200_000  # 0 + 200k != 250k
        ok, msg = validate_sg_cp_v1_accounting_dict(corrupt_d)
        self.assertFalse(ok)
        self.assertIn("Conservation violated", msg)

        # Corruption E: Cost drift (total_billed_cost_usd doesn't match spent_microusd)
        corrupt_e = dict(clean)
        corrupt_e["total_billed_cost_usd"] = 0.15  # but spent_microusd is 0
        ok, msg = validate_sg_cp_v1_accounting_dict(corrupt_e)
        self.assertFalse(ok)
        self.assertIn("Cost drift", msg)

        # Corruption F: within_budget flag contradicts spend
        corrupt_f = dict(clean)
        corrupt_f["within_budget"] = False  # spent is 0 <= 250k, so False is contradictory
        ok, msg = validate_sg_cp_v1_accounting_dict(corrupt_f)
        self.assertFalse(ok)
        self.assertIn("within_budget flag contradicts", msg)

        # Corruption G: Negative spend
        corrupt_g = dict(clean)
        corrupt_g["spent_microusd"] = -500
        ok, msg = validate_sg_cp_v1_accounting_dict(corrupt_g)
        self.assertFalse(ok)
        self.assertIn("Invalid spent_microusd", msg)

        # Corruption H: AuthorityEffect != None
        corrupt_h = dict(clean)
        corrupt_h["authority_effect"] = "FullProductionSignoff"
        ok, msg = validate_sg_cp_v1_accounting_dict(corrupt_h)
        self.assertFalse(ok)
        self.assertIn("Invalid authority_effect", msg)

    # =========================================================================
    # Family 8: Saturation, Pricing Table Seams, Provider Types, and Serialization
    # =========================================================================

    def test_exact_saturation_at_ceiling_boundary(self) -> None:
        """Spend exactly 250,000 uUSD ($0.25); verify remaining is 0 and next 1 uUSD charge fails fail-closed."""
        gate = BudgetGate()
        # 2,500,000 input tokens on Llama-3.3-70B = 250,000 uUSD
        receipt = gate.quote_and_charge_pre_call(
            Provider.OPENROUTER,
            "meta-llama/llama-3.3-70b-instruct",
            input_tokens=2_500_000,
            max_output_tokens=0,
        )
        self.assertEqual(receipt.cost_microusd, 250_000)
        self.assertEqual(gate.spent_microusd, 250_000)
        self.assertEqual(gate.remaining_microusd, 0)
        self.assertEqual(gate.spent_usd, 0.25)
        self.assertTrue(gate.is_within_hard_ceiling)
        self.assertFalse(gate.is_within_target)

        # Attempting any non-zero charge must raise BudgetExceeded
        with pytest.raises(BudgetExceeded) as exc_info:
            gate.pre_call_check(1)
        self.assertEqual(exc_info.value.requested, 250_001)
        self.assertEqual(exc_info.value.limit, 250_000)
        self.assertEqual(gate.spent_microusd, 250_000)

    def test_model_missing_from_price_table_raises_pricing_unavailable(self) -> None:
        """If an admitted model has no pricing observation in PriceTable, fails fail-closed with zero spend."""
        gate = BudgetGate()
        # meta-llama/llama-3.1-70b-instruct is admitted in ModelRegistry, but not in PriceTable
        with pytest.raises(ModelNotAllowed):
            gate.quote_and_charge_pre_call(
                Provider.OPENROUTER,
                "meta-llama/llama-3.1-70b-instruct",
                input_tokens=100,
                max_output_tokens=100,
            )
        self.assertEqual(gate.spent_microusd, 0)

    def test_zero_cost_model_charge(self) -> None:
        """Models with (0, 0) pricing (e.g. NVIDIA hosted llama-3.3-70b) charge 0 uUSD and preserve budget."""
        gate = BudgetGate()
        receipt = gate.quote_and_charge_pre_call(
            Provider.NVIDIA,
            "meta/llama-3.3-70b-instruct",
            input_tokens=50_000,
            max_output_tokens=2_000,
        )
        self.assertEqual(receipt.cost_microusd, 0)
        self.assertEqual(gate.spent_microusd, 0)
        self.assertEqual(gate.remaining_microusd, 250_000)

    def test_invalid_provider_types_and_values(self) -> None:
        """Invalid provider values (unknown string, int, None) fail with ValueError/TypeError."""
        gate = BudgetGate()
        # Invalid string
        with pytest.raises(ValueError):
            gate.validate_model("unsupported_provider", "meta-llama/llama-3.3-70b-instruct")
        # Invalid types
        for bad_p in (123, None, ["openrouter"]):
            with pytest.raises(TypeError):
                gate.validate_model(bad_p, "meta-llama/llama-3.3-70b-instruct")  # type: ignore[arg-type]

    def test_target_microusd_cannot_exceed_ceiling(self) -> None:
        """target_microusd > ceiling_microusd must raise ValueError fail-closed."""
        with pytest.raises(ValueError):
            BudgetGate(ceiling_microusd=200_000, target_microusd=200_001)

    def test_spent_usd_micro_precision_rounding(self) -> None:
        """spent_usd must accurately reflect fractional USD down to 6 decimal places (micro-USD precision)."""
        gate = BudgetGate()
        # Zero cost
        self.assertEqual(gate.spent_usd, 0.0)

        # Direct charge simulation via controller
        gate.controller._spent = 1
        self.assertEqual(gate.spent_usd, 0.000001)
        gate.controller._spent = 50_000
        self.assertEqual(gate.spent_usd, 0.05)
        gate.controller._spent = 250_000
        self.assertEqual(gate.spent_usd, 0.25)

    def test_accounting_dict_canonical_json_serializable(self) -> None:
        """Accounting dictionary must be strictly serializable to canonical RFC 8785 JSON without loss."""
        import json

        gate = BudgetGate()
        acct = gate.to_accounting_dict()
        serialized = json.dumps(acct, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        deserialized = json.loads(serialized)
        self.assertEqual(acct, deserialized)


if __name__ == "__main__":
    unittest.main()
