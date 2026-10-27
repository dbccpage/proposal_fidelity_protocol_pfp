"""Provider adapters for PFP proposal and candidate generation.

Implements PfpLlmProviderPort.
Supports offline deterministic mock completions and live model integration.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from ..domain.kernel.ports import PfpLlmProviderPort
from ..domain.prompts.prompts import PromptPacket
from ..domain.stages.stages import (
    Stage1Response,
    Stage2Response,
    Stage3Response,
    Stage4Response,
    Stage6Response,
    Stage7Response,
    Stage8Response,
)


class SeedHostVerifier:
    """Concrete existing-port adapter: actual catalog checks decide model witnesses."""

    def __init__(self):
        self.evaluations = []

    def _evaluate(self, demo_id, candidate):
        from pfp.infrastructure.pilot_runners.mssn_checks import evaluate_seed_response
        result = evaluate_seed_response(demo_id,candidate)
        self.evaluations.append(result.to_dict())
        return result

    @staticmethod
    def _response(demo_id, passed, reason="", survivors=()):
        from ..domain.stages.stages import Stage5Response
        return Stage5Response(demo_id=demo_id,should_continue=passed,
                              host_verdict="PASS" if passed else "CHECKER_REFUSED: " + reason,
                              exact_checks_passed=passed,surviving_candidates=list(survivors))

    def verify(self, demo_id, prior_responses):
        extracted=prior_responses.get(4)
        if type(extracted) is not dict or type(extracted.get("candidate")) is not dict:
            return self._response(demo_id,False,"STAGE4_STRUCTURED_WITNESS_REQUIRED")
        result=self._evaluate(demo_id,extracted["candidate"])
        return self._response(demo_id,result.passed,"; ".join(result.failure_reasons),
                              [extracted["candidate_id"]] if result.passed else [])

    def verify_challenges(self, demo_id, stage, items, prior_responses):
        """Grade every witness on host facts; a wrong prediction is a discard, not a run failure."""
        from ..domain.stages.stages import ChallengeReplay, WitnessReplay, replay_outcome
        extracted = prior_responses.get(4)
        if type(extracted) is not dict or type(extracted.get("candidate")) is not dict:
            raise ValueError("STAGE4_STRUCTURED_WITNESS_REQUIRED")
        candidate = json.dumps(extracted["candidate"], sort_keys=True, ensure_ascii=False)
        witnesses = []
        for index, item in enumerate(items):
            if type(item.get("expected_accept")) is not bool or type(item.get("witness")) is not dict:
                raise ValueError(f"STAGE{stage}_WITNESS_SHAPE")
            result = self._evaluate(demo_id, item["witness"])
            if any("UNAVAILABLE" in reason for reason in result.failure_reasons):
                raise ValueError("CHALLENGE_CHECKER_UNAVAILABLE")
            same = json.dumps(item["witness"], sort_keys=True, ensure_ascii=False) == candidate
            witnesses.append(WitnessReplay(
                index=index, candidate_id=item["candidate_id"], expected_accept=item["expected_accept"],
                host_accepted=result.passed, same_as_candidate=same,
                outcome=replay_outcome(item["expected_accept"], result.passed, same),
                failure_reasons=tuple(result.failure_reasons)))
        return ChallengeReplay(demo_id=demo_id, stage=stage, witnesses=tuple(witnesses))

    def verify_refusal(self, demo_id, probe):
        from copy import deepcopy
        from hashlib import sha256
        if type(probe) is not dict or set(probe) != {"payload","expected_reason"} or type(probe["expected_reason"]) is not str:
            raise ValueError("MODE14_TYPED_PROBE_REQUIRED")
        before=deepcopy(probe)
        result=self._evaluate(demo_id,probe["payload"])
        if probe != before:
            raise ValueError("MODE14_PARTIAL_MUTATION")
        if result.passed or probe["expected_reason"] not in result.failure_reasons:
            raise ValueError("MODE14_PREDICTED_REFUSAL_NOT_OBSERVED")
        if "UNAVAILABLE" in probe["expected_reason"]:
            raise ValueError("MODE14_UNAVAILABLE_IS_NOT_A_REFUSAL_ORACLE")
        digest=sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()
        return dict(typed_refusal=probe["expected_reason"],before_digest=digest,after_digest=digest,
                    executed_mutations=0,authority_effect="None")

    def verify_mode(self, mode_id, mode_input):
        from pfp.infrastructure.pilot_runners.pfp_mode_additional_checks import (
            execute_additional_mode_check,
        )
        return execute_additional_mode_check(mode_id, mode_input)


class OfflineDeterministicPfpProvider(PfpLlmProviderPort):
    """Deterministic offline mock provider returning schema-conformant stage completions."""

    def generate_candidate(
        self,
        packet: PromptPacket,
        temperature: float = 0.0,
    ) -> str:
        stage = packet.stage
        demo_id = packet.demo_id
        if packet.response_schema and "admission_proposal" in packet.response_schema.get("properties", {}):
            return json.dumps(self._canonical_fixture(packet))
        if packet.response_schema and any(key in packet.response_schema.get("properties", {})
                                         for key in ("audits", "candidate_id", "challenges", "scoped_summary")):
            return json.dumps(self._canonical_fixture(packet))
        if packet.response_schema.get("properties", {}).get("candidates", {}).get("items", {}).get("type") == "object":
            return json.dumps(self._canonical_fixture(packet))

        if stage == 1:
            return json.dumps(Stage1Response(
                demo_id=demo_id, should_continue=True,
                admission_proposal=dict(status="admit", grammar="fixture JSON", equality_test="exact bytes",
                    coefficient_profile="declared by seed", missing_declarations=[],
                    reason="Offline shape fixture; host math remains unexecuted"),
            ).model_dump(mode="json"))
        elif stage == 2:
            return json.dumps(Stage2Response(
                demo_id=demo_id, should_continue=True,
                candidates=[dict(candidate_id=f"fixture_{i}", kind="construction",
                    statement=f"Offline candidate {i}; no mathematical acceptance", assumptions=[],
                    check_without_llm=True) for i in range(5)],
            ).model_dump(mode="json"))
        elif stage == 3:
            return json.dumps(Stage3Response(
                demo_id=demo_id, should_continue=True,
                audits=[dict(candidate_id="fixture_0", routing="extract", reasons=[],
                             source_quotes=[], imported_assumptions=[])],
            ).model_dump(mode="json"))
        elif stage == 4:
            return json.dumps(Stage4Response(
                demo_id=demo_id, should_continue=True, candidate_id="fixture_0",
                coefficient_profile="declared by seed", source_quotes=[], missing_fields=[],
                candidate={"proposal": "Offline fixture; not a mathematical certificate"},
            ).model_dump(mode="json"))
        elif stage == 6:
            return json.dumps(Stage6Response(
                demo_id=demo_id, should_continue=True, challenges=[],
            ).model_dump(mode="json"))
        elif stage == 7:
            return json.dumps(Stage7Response(
                demo_id=demo_id,
                host_replay=dict(demo_id=demo_id, stage=6, witnesses=[]),
                obstruction_indices=[], checked_count=0,
            ).model_dump(mode="json"))
        elif stage == 8:
            return json.dumps(Stage8Response(
                demo_id=demo_id, disposition="REJECT", selected_candidate_id=None, survivors=[],
                rule="STAGE5_SURVIVORS_LESS_STAGE7_OBSTRUCTIONS",
            ).model_dump(mode="json"))
        else:
            return json.dumps(
                {
                    "stage": stage,
                    "derived_under_policy": "SPK-001",
                    "authority_effect": "None",
                    "demo_id": demo_id,
                    "should_continue": True,
                }
            )

    @staticmethod
    def _canonical_fixture(packet: PromptPacket) -> dict:
        """Host fixture only; it never invents seed answers or provider evidence.

        Packet stage 1 is the admission repair turn, sent only when the seed has no declaration.
        """
        response = dict(stage=packet.stage, derived_under_policy="SPK-001", authority_effect="None",
                        demo_id=packet.demo_id, should_continue=packet.stage != 11)
        context = json.loads(packet.user)
        prior = context["prior_artifacts"]
        if packet.stage == 1:
            response["admission_proposal"] = dict(status="admit", grammar="fixture JSON",
                equality_test="exact bytes", coefficient_profile="declared by seed",
                missing_declarations=[], reason="Offline shape fixture; host math remains unexecuted")
        elif packet.stage == 2:
            response["candidates"] = [dict(candidate_id=f"fixture_{i}", kind="construction",
                statement=f"Offline candidate {i}; no mathematical acceptance", assumptions=[],
                check_without_llm=True) for i in range(5)]
        elif packet.stage == 3:
            response["audits"] = [dict(candidate_id=item["candidate_id"], routing="extract", reasons=[],
                                       source_quotes=[], imported_assumptions=[])
                                  for item in prior["2"]["candidates"]]
        elif packet.stage == 4:
            if set(packet.response_schema["properties"]["candidate"].get("properties", {})) != {"proposal"}:
                raise ValueError("OFFLINE_SEED_WITNESS_UNAVAILABLE")
            response.update(candidate_id=prior["3"]["audits"][0]["candidate_id"],
                coefficient_profile="declared by seed", source_quotes=[], missing_fields=[],
                candidate={"proposal": "Offline fixture; not a mathematical certificate"})
        elif packet.stage == 6:
            response["challenges"] = []
        elif packet.stage == 11:
            response.update(scoped_summary="Offline stage-shape exercise only",
                remaining_obligations=["independent seed witness verification"], next_seed="",
                proposed_tests=[])
        return response


class OpenRouterLiveProvider(PfpLlmProviderPort):
    """Compatibility adapter for an explicitly supplied accounted PFP gateway.

    Credentials alone cannot dispatch. There are no raw sends or automatic retries.
    The original provider name and result fields remain for existing consumers.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "deepseek/deepseek-v4.1-flash",
        *,
        gateway=None,
        task_id=None,
        max_output_tokens=512,
        max_estimated_cost_microusd=None,
        max_provider_calls=5,
        env_file=None,
    ):
        from uuid import uuid4

        self._api_key = api_key or ""
        self.default_model = default_model
        self.gateway = gateway
        self.task_id = task_id or "pilot-suite:" + uuid4().hex
        self.max_output_tokens = max_output_tokens
        self.max_estimated_cost_microusd = max_estimated_cost_microusd
        self.max_provider_calls = max_provider_calls
        self.env_file = env_file

    def preflight(
        self, model, *, max_provider_calls, max_output_tokens, max_estimated_cost_microusd=None
    ):
        """Validate explicit caller allowances before creating output or sending."""
        from .pilot_matrix import _scope, validate_pilot_gateways

        if self.default_model != model or self.max_output_tokens != max_output_tokens:
            raise ValueError("PFP_PROVIDER_SCOPE_MISMATCH")
        if self.gateway is not None:
            validate_pilot_gateways({model: self.gateway}, [model], max_tokens=max_output_tokens)
            scope = _scope(self.gateway, model, max_output_tokens)
            if scope[3] > max_provider_calls:
                raise ValueError("PFP_CALL_ALLOWANCE_CONFLICT")
            if max_estimated_cost_microusd is not None and scope[2] > max_estimated_cost_microusd:
                raise ValueError("PFP_COST_ALLOWANCE_CONFLICT")
        elif (
            type(self.max_estimated_cost_microusd) is not int
            or not 0 < self.max_estimated_cost_microusd <= 50000
        ):
            raise ValueError("PFP_ACCOUNTED_GATEWAY_REQUIRED")
        elif self.max_provider_calls > max_provider_calls or (
            max_estimated_cost_microusd is not None
            and self.max_estimated_cost_microusd > max_estimated_cost_microusd
        ):
            raise ValueError("PFP_ALLOWANCE_CONFLICT")

    def prepare_run(self, output_dir, run_id, objective_sha256):
        """Infrastructure owns the existing factory; no use-case transport import."""
        from .pilot_matrix import make_pilot_gateways

        self.task_id = run_id
        if self.gateway is None:
            self.gateway = make_pilot_gateways(
                [self.default_model],
                max_output_tokens=self.max_output_tokens,
                max_estimated_cost_microusd=self.max_estimated_cost_microusd,
                max_calls=self.max_provider_calls,
                accounting_path=output_dir / "accounting.sqlite3",
                env_file=self.env_file,
                run_id=run_id,
                objective_sha256=objective_sha256,
            )[self.default_model]

    @property
    def api_key(self) -> str:
        return self._api_key

    def generate_candidate(self, packet: PromptPacket, temperature: float = 0.0) -> str:
        result = self.dispatch_messages(
            [{"role": "user", "content": json.dumps(packet.model_dump(), sort_keys=True)}],
            model=self.default_model,
            temperature=temperature,
        )
        if not result["exchange"]["ok"]:
            raise ValueError(result["exchange"]["error"])
        return result["raw_reply"]

    def dispatch_messages(
        self,
        messages: list[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        timeout_sec: int = 90,
        max_retries: int = 4,
        *,
        attempt_id=None,
    ) -> Dict[str, Any]:
        """Exactly one accounted attempt; legacy timeout/retry args never add sends."""
        from uuid import uuid4

        from adversary.domain.providers.types import (
            CandidateRequest,
            ChatMessage,
            DecodingParamsV1,
        )

        from .adapters.pfp_campaign import micro
        from .pilot_matrix import complete_pilot_turn, validate_pilot_gateways

        target = model or self.default_model
        validate_pilot_gateways({target: self.gateway}, [target], max_tokens=self.max_output_tokens)
        attempt = attempt_id or uuid4().hex
        exchange = complete_pilot_turn(
            self.gateway,
            CandidateRequest(
                messages=tuple(ChatMessage(item["role"], item["content"]) for item in messages),
                decoding=DecodingParamsV1(temperature=temperature),
            ),
            model=target,
            task_id=self.task_id,
            attempt_id=attempt,
            max_tokens=self.max_output_tokens,
        )
        if exchange["attempt_state"] == "CompletedPendingSettlement":
            exchange = dict(
                exchange, ok=False, stop=True, error="CompletedPendingSettlement"
            )
        try:
            claim = self.gateway.action(attempt)
        except KeyError:
            claim = None
        incurred = exchange["provider_wire"] is not None or (
            claim is not None and claim["state"] != "refused_before_dispatch"
        )
        cost = exchange["usage"].get("cost") if incurred else 0.0
        # Missing token counts remain unknown; no model-priced or zero-cost guesses.
        usage = dict(exchange["usage"])
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        usage["total_tokens"] = (
            prompt + completion if prompt is not None and completion is not None else None
        )
        return dict(
            model=target,
            upstream_model=target,
            upstream_provider="openrouter",
            dispatch_id=usage.get("generation_id"),
            system_fingerprint=None,
            duration_seconds=exchange["elapsed"],
            tokens_per_second=(
                completion / exchange["elapsed"]
                if completion is not None and exchange["elapsed"]
                else None
            ),
            raw_reply=exchange["content"] or "",
            reasoning=exchange["reasoning"],
            usage=usage,
            cost=dict(
                total_cost_usd=cost, total_cost_microusd=micro(cost) if cost is not None else None
            ),
            exchange=exchange,
            cost_may_be_incurred=incurred,
        )
