"""Graph task turns through the existing accounted PFP provider boundary.

Generation constraints are requested, not attested. Actual UTF-8 replies are
retained and independently validated by Rust. Offline responses require
explicit fixture_mode. AuthorityEffect: None.
"""

from __future__ import annotations

import base64
import json
from dataclasses import asdict
from hashlib import sha256
from typing import Any, Protocol
from uuid import uuid4

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_pfp.domain.ports.decode_control_port import DecodeControlReceiptV2
from omega_engine_woland.domain.evidence import canonical_rational, parse_exact_rational
from omega_engine_woland.domain.graph_task import GraphCandidateEvaluationV1, GraphTaskV1, read_json
from omega_engine_woland.domain.estate_ports import AntiSkillGatePort
from omega_engine_woland.domain.instruction_ingress import (
    InstructionIngressReceiptV1,
    instruction_request_digest,
)
from omega_engine_woland.domain.intelligence_mining import canonical_bytes
from omega_engine_woland.domain.models import WolandBoutRequestV1
from omega_engine_woland.domain.ports import InstructionIngressPort
from omega_engine_woland.domain.providers.types import CandidateRequest, DecodingParamsV1, Provider
from omega_engine_woland.infrastructure.prompt_geometry import PROFILE, SCHEMA, observe_text


class GraphEvaluator(Protocol):
    def invoke(self, action: str, payload: dict) -> Result: ...


def refusal(code: str, message: str):
    from omega_engine_operations.domain.rop.result import Err
    return Err(Refusal(code, message, "omega_engine_providers.graph"))


def graph_instruction_request(
    task: GraphTaskV1, mode: str, provider: str, model: str
) -> WolandBoutRequestV1:
    """The stable graph request an operator admits before configuring live ingress.

    The task reference binds the entire declaration, including finite budgets.
    Display names need not satisfy the narrower bout task-key grammar.
    """
    if type(task) is not GraphTaskV1 or mode not in {"diagnose", "repair"}:
        raise ValueError("GRAPH_REQUEST_INVALID: exact task and diagnose|repair required")
    if provider != Provider.OPENROUTER.value or type(model) is not str or not model.strip():
        raise ValueError("GRAPH_PROVIDER_MODE_MISMATCH: explicit OpenRouter model required")
    return WolandBoutRequestV1(
        objective="Execute the declared finite graph task through independent graph checkers.",
        task_key="graph:" + task.task_ref.removeprefix("sha256:"),
        max_rounds=max(1, task.critique_rounds),
        fixture_mode=False,
        compute_budget=max(1, task.max_candidates),
        carrier_context={"graph_task_ref": task.task_ref, "graph_mode": mode,
                         "provider": provider, "model": model},
    )


class GraphProviderAdapter:
    def __init__(
        self,
        evaluator: GraphEvaluator,
        *,
        gateway: Any = None,
        provider: str | None = None,
        model: str | None = None,
        fixture_mode: bool = False,
        instruction_request: WolandBoutRequestV1 | None = None,
        instruction_ingress: InstructionIngressPort | None = None,
        anti_skill_gate: AntiSkillGatePort | None = None,
    ) -> None:
        if type(fixture_mode) is not bool:
            raise TypeError("fixture_mode must be an exact bool")
        if fixture_mode and gateway is not None:
            raise ValueError("fixture_mode and a configured gateway are mutually exclusive")
        if gateway is not None and not callable(getattr(gateway, "complete", None)):
            raise TypeError("configured provider gateway must expose complete")
        if gateway is not None and (not provider or not model or provider == "fixture"):
            raise ValueError("a configured gateway requires an explicit real provider and model")
        if gateway is not None:
            from omega_engine_pfp.infrastructure.pilot_matrix import validate_pilot_gateways

            if provider != Provider.OPENROUTER.value:
                raise ValueError("GRAPH_PROVIDER_MODE_MISMATCH: accounted OpenRouter required")
            validate_pilot_gateways({model: gateway}, (model,))
        admission = (instruction_request, instruction_ingress, anti_skill_gate)
        if any(item is not None for item in admission):
            if gateway is None or any(item is None for item in admission):
                raise ValueError("GRAPH_INSTRUCTION_INGRESS_UNBOUND: request and both gates required")
            if type(instruction_request) is not WolandBoutRequestV1:
                raise TypeError("instruction_request must be an exact WolandBoutRequestV1")
            if (not callable(getattr(instruction_ingress, "pre_dispatch", None))
                    or not callable(getattr(anti_skill_gate, "evaluate", None))):
                raise TypeError("graph instruction and anti-skill ports must be callable")
        self.instruction_request = instruction_request
        self.instruction_ingress, self.anti_skill_gate = instruction_ingress, anti_skill_gate
        self._instruction_digest = (
            instruction_request_digest(instruction_request) if instruction_request else None
        )
        self._instruction_mode = (
            instruction_request.carrier_context.get("graph_mode") if instruction_request else None
        )
        self.evaluator, self.gateway = evaluator, gateway
        self.provider, self.model, self.fixture_mode = provider, model, fixture_mode
        self._run_id, self._stopped = uuid4().hex, False
        self.last_turn: dict[str, Any] | None = None
        self.turn_history: list[dict[str, Any]] = []

    @staticmethod
    def _observe_exchange(task: GraphTaskV1, role: str, exchange: dict) -> dict:
        """Observe retained bytes without changing the request or its checked answer."""
        def measure(source: str | bytes, *, field: str, trust_level: str,
                    role_id: str = "graph." + role) -> dict:
            raw = source if isinstance(source, bytes) else source.encode("utf-8", errors="surrogatepass")
            try:
                return observe_text(raw, dimension=128, role_id=role_id,
                    field=field, trust_level=trust_level)
            except (ValueError, TypeError, KeyError, OSError, RuntimeError) as exc:
                return {"schema_version": SCHEMA, "profile": PROFILE, "dim": 128,
                    "source_sha256": "sha256:" + sha256(raw).hexdigest(), "source_bytes": len(raw),
                    "role_id": role_id, "field": field, "trust_level": trust_level,
                    "status": "UNAVAILABLE", "reason": str(exc), "authority_effect": "None",
                    "spans": [], "factors": [], "weights": [], "spectrum": [],
                    "entropy_bits": None, "purity": None, "effective_rank": None, "numerical_rank": None,
                    "spectrum_tolerance": 1e-10}

        reports = {"seed": measure(task.carrier.prompt, field="seed", trust_level="user-seed",
            role_id="graph.input"), "prompt_messages": []}
        for index, message in enumerate(exchange.get("request", {}).get("messages", ())):
            if not isinstance(message, dict) or not isinstance(message.get("content"), str):
                continue  # No rendered text was captured at this boundary.
            field = "pfp." + str(message.get("role", "unknown"))
            reports["prompt_messages"].append({"index": index,
                "observation": measure(message["content"], field=field,
                    trust_level="host-assembled" if message.get("role") == "system" else "mixed-source")})
        for key, capture, field, trust in (
            ("provider_wire", exchange.get("provider_wire"), "provider.raw_reply", "untrusted-provider"),
            ("reply", exchange.get("pfp"), "pfp.raw_reply", "untrusted-model"),
        ):
            if isinstance(capture, dict) and capture.get("raw_reply_base64") is not None:
                try:
                    raw = base64.b64decode(capture["raw_reply_base64"], validate=True)
                except (TypeError, ValueError):
                    reports[key] = {"status": "UNAVAILABLE", "reason": "RETAINED_CAPTURE_INVALID_BASE64",
                        "profile": PROFILE, "dim": 128, "role_id": "graph." + role,
                        "field": field, "trust_level": trust, "authority_effect": "None"}
                else:
                    reports[key] = measure(raw, field=field, trust_level=trust)
        return reports

    def _admit(self, task: GraphTaskV1) -> Result[dict, Refusal]:
        """Freshly verify selected source bytes and screen this bound dispatch."""
        from omega_engine_woland.use_cases.anti_skill_predispatch import require_pre_dispatch_clear
        from omega_engine_operads.application.woland_instruction_admission import (
            ordered_bodies_digest,
        )

        try:
            expected = graph_instruction_request(task, self._instruction_mode, self.provider, self.model)
            if (instruction_request_digest(expected) != self._instruction_digest
                    or instruction_request_digest(self.instruction_request) != self._instruction_digest):
                return refusal("GRAPH_INSTRUCTION_REQUEST_MISMATCH", "task, mode or provider binding changed")
            admitted = self.instruction_ingress.pre_dispatch(expected)
            if isinstance(admitted, Err):
                return admitted
            if not isinstance(admitted, Ok) or type(admitted.value) is not InstructionIngressReceiptV1:
                return refusal("GRAPH_INSTRUCTION_INGRESS_INVALID", "ingress returned no typed admission")
            receipt = admitted.value
            if receipt.request_digest != self._instruction_digest:
                return refusal("GRAPH_INSTRUCTION_REQUEST_MISMATCH", "admission binds a different request")
            plan = receipt.native_instruction_plan()
            if plan is None:
                return refusal("GRAPH_INSTRUCTION_PLAN_UNBOUND", "admission must include the actual instruction bodies")
            bodies = plan["ordered_operand_bodies"]
            if (type(bodies) is not list or not bodies
                    or any(type(body) is not str or not body for body in bodies)
                    or ordered_bodies_digest(tuple(bodies)) != plan["ordered_bodies_digest"]
                    or type(plan["instruction_bytes"]) is not int
                    or sum(len(body.encode("utf-8")) for body in bodies) != plan["instruction_bytes"]):
                return refusal("GRAPH_INSTRUCTION_BODY_MISMATCH", "instruction bodies differ from admitted digest or byte count")
            screened = require_pre_dispatch_clear(
                self.anti_skill_gate, "omega_engine_woland.graph", expected, receipt)
            if screened.is_err:
                return screened
            return Ok({"request_digest": receipt.request_digest,
                "admission_receipt_id": receipt.admission_receipt_id,
                "verifier_id": receipt.verifier_id, "plan": plan,
                "anti_skill_decision": asdict(screened.unwrap())})
        except Exception as exc:
            return refusal("GRAPH_INSTRUCTION_INGRESS_FAILED", f"{type(exc).__name__}: {exc}")

    def _turn(
        self,
        *,
        task: GraphTaskV1,
        role: str,
        user: dict[str, Any],
        schema: dict[str, Any],
        language: bytes,
        fixture_output: bytes,
        validation_method: str,
    ) -> Result[bytes, Refusal]:
        try:
            if self._stopped:
                return refusal("GRAPH_PROVIDER_STOPPED", "the prior turn requires review before continuation")
            metadata: dict[str, Any] = {"fixture_mode": self.fixture_mode}
            if self.instruction_request is not None:
                admitted = self._admit(task)
                if admitted.is_err:
                    self._stopped = True
                    return admitted
                metadata["instruction_ingress"] = admitted.unwrap()
            system = "Return only the requested JSON. Propose no carrier, permission or interpretation changes. Mathematical correctness is determined by independent checkers."
            if "instruction_ingress" in metadata:
                system += "\nAdmitted OEWAS instructions, in order:\n" + "\n\n".join(
                    metadata["instruction_ingress"]["plan"]["ordered_operand_bodies"])
            if validation_method == "finite-utf8.v1":
                system += " Use compact JSON with lexicographically sorted keys and no extra whitespace; rational values remain canonical strings."
            request_user, answer_schema = user, schema
            if not self.fixture_mode:
                # PFP's answer must preserve the exact inner JSON, including any
                # invalid whitespace. Re-encoding a dict would change membership.
                system += " Put the exact requested JSON text in the PFP answer string; do not reformat it."
                request_user = {**user, "output_schema": schema}
                answer_schema = {"type": "string", "minLength": 1}
                if validation_method == "finite-utf8.v1":
                    answer_schema["enum"] = [bytes.fromhex(raw).decode("utf-8")
                        for raw in read_json(language)["sentences_hex"]]
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": "graph_" + role, "strict": True, "schema": answer_schema},
            }
            request = CandidateRequest(
                system=system,
                user=canonical_bytes(request_user).decode("utf-8"),
                decoding=DecodingParamsV1(
                    response_format=response_format, allow_fallbacks=False, require_parameters=True
                ),
            )
            request_bytes = canonical_bytes(
                {
                    "role": role,
                    "task_ref": task.task_ref,
                    "provider": "fixture" if self.fixture_mode else self.provider,
                    "model": "explicit-graph-fixture" if self.fixture_mode else self.model,
                    "system": system,
                    "user": request.user,
                    "response_format": response_format,
                    "allow_fallbacks": False,
                    "require_parameters": True,
                }
            )
            if len(request_bytes) > 16384 or len(language) > 32768:
                return refusal(
                    "GRAPH_GENERATION_BYTE_CEILING",
                    "request or language exceeds the native decode validation ceiling",
                )
            if self.fixture_mode:
                output = fixture_output
            else:
                if self.gateway is None:
                    return refusal(
                        "EXECUTION_UNAVAILABLE",
                        "configure an existing provider gateway or explicit fixture_mode",
                    )
                from omega_engine_pfp.infrastructure.pilot_matrix import complete_pilot_turn

                attempt_id = f"graph:{self._run_id}:{role}:{len(self.turn_history)}"
                try:
                    exchange = complete_pilot_turn(self.gateway, request,
                        model=self.model, task_id=task.task_ref, attempt_id=attempt_id)
                except BaseException:
                    self._stopped = True
                    raise  # Existing durable accounting retains ambiguous dispatch custody.
                exchange["density"] = self._observe_exchange(task, role, exchange)
                self.last_turn = exchange
                self.turn_history.append(exchange)
                metadata.update(provider=self.provider, model=self.model, pfp_turn=exchange,
                    generation_id=exchange["usage"].get("generation_id"),
                    input_tokens=exchange["usage"].get("prompt_tokens"),
                    output_tokens=exchange["usage"].get("completion_tokens"))
                request_bytes = canonical_bytes(exchange["request"])
                if not exchange["ok"] or exchange["stop"]:
                    self._stopped = True
                    return self._unmeasured(role, request_bytes, metadata, exchange["error"])
                try:
                    output = exchange["content"].encode("utf-8")
                except UnicodeEncodeError:
                    # JSON permits an escaped lone surrogate, but graph outputs
                    # require UTF-8. Preserve its JSON spelling and original wire.
                    exchange["pfp"]["answer_json_ascii"] = json.dumps(
                        exchange["pfp"].pop("answer"), ensure_ascii=True)
                    exchange.update(content=None, ok=False, stop=True, error="GRAPH_ANSWER_UTF8_INVALID")
                    self._stopped = True
                    return self._unmeasured(role, request_bytes, metadata, exchange["error"])
                if len(request_bytes) > 16384 or len(output) > 16384:
                    self._stopped = True
                    return self._unmeasured(role, request_bytes, metadata, "GRAPH_GENERATION_BYTE_CEILING")
            if validation_method == "finite-utf8.v1":
                valid = output.hex() in read_json(language)["sentences_hex"]
            else:
                try:
                    c = read_json(output, 16384)
                    valid = (
                        type(c) is dict
                        and set(c) == {"candidate_ref", "obligation", "witness"}
                        and c["candidate_ref"] == user["candidate_ref"]
                        and type(c["witness"]) is list
                        and (
                            (c["obligation"] == "NONE" and c["witness"] == [])
                            or (
                                c["obligation"] in {"CONSISTENCY", "OBSERVER_COVERAGE"}
                                and len(c["witness"]) == len(task.edge_ids)
                                and all(
                                    type(v) is str
                                    and len(v) <= 256
                                    and canonical_rational(parse_exact_rational(v)) == v
                                    for v in c["witness"]
                                )
                            )
                        )
                    )
                except (ValueError, TypeError, KeyError, UnicodeDecodeError):
                    valid = False
            receipt = DecodeControlReceiptV2(
                request_bytes,
                output,
                language,
                "VALID" if valid else "INVALID",
                "FIXTURE" if self.fixture_mode else "PROVIDER_REQUESTED",
                validation_method=validation_method,
            )
            replay = self.evaluator.invoke("verify_decode_receipt_v2", receipt.to_dict())
            if replay.is_err:
                return Ok(
                    canonical_bytes(
                        {
                            "role": role,
                            "request_hex": request_bytes.hex(),
                            "output_hex": output.hex(),
                            "decode_receipt": receipt.to_dict(),
                            "decode_verification": replay.unwrap_err().to_dict(),
                            "validation_outcome": "NOT_MEASURED",
                            "metadata": metadata,
                            "authority_effect": "None",
                        }
                    )
                )
            verified = replay.unwrap()["result"]
            data = receipt.to_dict()
            if (
                verified.get("request_sha256") != data["request_sha256"]
                or verified.get("output_sha256") != data["output_sha256"]
                or verified.get("language_sha256") != data["language_sha256"]
                or verified.get("status") != data["validation_outcome"]
            ):
                return refusal(
                    "GRAPH_DECODE_REPLAY_MISMATCH",
                    "decode verifier did not bind actual request, language and output bytes",
                )
            return Ok(
                canonical_bytes(
                    {
                        "role": role,
                        "request_hex": request_bytes.hex(),
                        "output_hex": output.hex(),
                        "decode_receipt": data,
                        "decode_verification": replay.unwrap(),
                        "validation_outcome": receipt.validation_outcome,
                        "metadata": metadata,
                        "authority_effect": "None",
                    }
                )
            )
        except (ValueError, TypeError, KeyError, RuntimeError, OSError) as exc:
            return refusal("GRAPH_GENERATION_REFUSED", f"{type(exc).__name__}: {exc}")

    @staticmethod
    def _unmeasured(role: str, request_bytes: bytes, metadata: dict, code: str) -> Result:
        """Retain the failed exchange without offering an unchecked graph answer."""
        return Ok(canonical_bytes({"role": role, "request_hex": request_bytes.hex(),
            "output_hex": "", "decode_receipt": None,
            "decode_verification": {"code": code}, "validation_outcome": "NOT_MEASURED",
            "metadata": metadata, "authority_effect": "None"}))

    def propose(self, task: GraphTaskV1) -> Result[bytes, Refusal]:
        candidates = [task.candidate_bytes(p) for p in task.repair_catalog]
        schema = {"enum": [read_json(raw) for raw in candidates]}
        language = canonical_bytes(
            {
                "schema_version": "omega.symbol_game.finite-output-language.v1",
                "sentences_hex": [raw.hex() for raw in candidates],
            }
        )
        fixture = next(
            (raw for p, raw in zip(task.repair_catalog, candidates, strict=True) if p.edits),
            candidates[0],
        )
        return self._turn(
            task=task,
            role="proposal",
            user={
                "task": task.to_dict(),
                "instruction": "Select a catalog patch that may repair the graph.",
            },
            schema=schema,
            language=language,
            fixture_output=fixture,
            validation_method="finite-utf8.v1",
        )

    def critique(
        self, task: GraphTaskV1, evaluation: GraphCandidateEvaluationV1, round_index: int
    ) -> Result[bytes, Refusal]:
        candidate_ref = evaluation.candidate_ref
        language = canonical_bytes(
            {
                "schema_version": "omega.symbol_game.graph-challenge-language.v1",
                "candidate_ref": candidate_ref,
                "edge_count": len(task.edge_ids),
            }
        )
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["candidate_ref", "obligation", "witness"],
            "properties": {
                "candidate_ref": {"const": candidate_ref},
                "obligation": {"enum": ["CONSISTENCY", "OBSERVER_COVERAGE", "NONE"]},
                "witness": {
                    "type": "array",
                    "maxItems": len(task.edge_ids),
                    "items": {"type": "string", "maxLength": 256},
                },
            },
        }
        native = read_json(evaluation.native_evidence_bytes)["evaluation"]["result"]
        f, coverage = native["projection"]["functional_receipt"], native["observer_coverage"]
        challenge = {"candidate_ref": candidate_ref, "obligation": "NONE", "witness": []}
        if not coverage["sound"]:
            challenge.update(obligation="OBSERVER_COVERAGE", witness=coverage["witness"])
        elif f["phi1"] != "0":
            challenge.update(obligation="CONSISTENCY", witness=f["dual_witness"])
        return self._turn(
            task=task,
            role="critique",
            user={
                "task": task.to_dict(),
                "candidate_ref": candidate_ref,
                "candidate": read_json(evaluation.candidate_bytes),
                "round": round_index,
                "observed": {
                    "phi1": f["phi1"],
                    "gamma2": f["gamma2"],
                    "observer_sound": coverage["sound"],
                },
                "instruction": "Identify a violated obligation and a rational counterexample witness on this edge basis, or NONE. A claim alone is not evidence.",
            },
            schema=schema,
            language=language,
            fixture_output=canonical_bytes(challenge),
            validation_method="graph-challenge-json.v1",
        )
