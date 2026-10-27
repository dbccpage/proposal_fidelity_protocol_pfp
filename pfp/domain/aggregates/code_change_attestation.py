"""Finite source/checker bindings, without a signature or authority claim."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field

from ..exceptions import CanonicalizationError
from ..validation import _require_digest, _require_stable_id

CHECK_SCHEMA = "core.pfp.source-bound-code-change-check.v1"
RESULT_SCHEMA = "core.pfp.source-bound-code-change-result.v1"
CHECKER_ID = "native-code-change-gates-v1"

# Source statements motivate the local experiment. They do not prove it sound.
# Each tuple is (pinned local source, source SHA, assumption, local observation, limit).
SOURCE_ASSUMPTIONS = (
    (
        "03_multi_agent_debate/07_learning_to_give_checkable_answers_with_prover-ver.md",
        "57a9522f54e1eac6de325c972af9ab3e248f69d0a36cd4263dc0418e2d045af8",
        "The verifier is trusted independently of an untrusted prover's message.",
        "Host configuration authorizes exact native checker bytes; model claims are ignored.",
        "No trained game, equilibrium, completeness or general soundness result is transferred.",
    ),
    (
        "07_reasoning_and_interpretability/10_stemming_hallucination_in_language_models_using_a.md",
        "17f2776a6ab5c9e7a2ea28b7d07826368b5d5255f16f0dac4ab89750d40e8a48",
        "An oracle evaluates claims against a fixed knowledge/constraint basis.",
        "Native gates evaluate frozen patch syntax, owned paths and protected paths.",
        "No knowledge graph, SHACL, factual truth, patch applicability or semantic correctness is proved.",
    ),
)


def protocol_bytes(value: object) -> bytes:
    """Named wire profile: sorted UTF-8 JSON, no floats in these value objects."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


ASSUMPTIONS_SHA256 = hashlib.sha256(protocol_bytes(SOURCE_ASSUMPTIONS)).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceBoundCheckRequestV1:
    run_id: str
    attempt_id: str
    attempt_index: int
    packet_id: str
    candidate_id: str
    patch_sha256: str
    source_revision: str
    source_sha256: str
    checker_id: str
    assumptions_sha256: str
    schema_version: str = field(default=CHECK_SCHEMA, init=False)
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        for name in ("run_id", "attempt_id", "checker_id"):
            _require_stable_id(getattr(self, name), name)
        # Index 32 can describe the next, exhausted slot; execution admits at most 32.
        if type(self.attempt_index) is not int or not 0 <= self.attempt_index <= 32:
            raise CanonicalizationError("attempt_index must be an integer in 0..32")
        for name in (
            "packet_id",
            "candidate_id",
            "patch_sha256",
            "source_sha256",
            "assumptions_sha256",
        ):
            _require_digest(getattr(self, name), name)
        if (
            type(self.source_revision) is not str
            or len(self.source_revision) != 40
            or any(ch not in "0123456789abcdef" for ch in self.source_revision)
        ):
            raise CanonicalizationError("source_revision must be a frozen lowercase Git commit ID")
        if self.authority_effect != "None":
            raise CanonicalizationError("checker requests have AuthorityEffect None")

    @property
    def request_sha256(self) -> str:
        return hashlib.sha256(protocol_bytes(asdict(self))).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceBoundCheckResultV1:
    request: SourceBoundCheckRequestV1
    checker_sha256: str
    trust_policy_sha256: str
    diagnostic_status: str
    evidence_json: bytes
    refusal_codes: tuple[str, ...] = ()
    authorization_status: str = "HOST_CONFIGURED_CHECKER"
    residual_obligations: tuple[str, ...] = (
        "Finite gates do not establish patch applicability or program correctness.",
        "Host configuration and local executable custody are trusted; no signature is claimed.",
        "External merge/promotion authority remains separate.",
    )
    next_action: str = "Review finite diagnostics and unresolved obligations."
    schema_version: str = field(default=RESULT_SCHEMA, init=False)
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.request) is not SourceBoundCheckRequestV1:
            raise CanonicalizationError("result requires the exact typed request")
        _require_digest(self.checker_sha256, "checker_sha256")
        _require_digest(self.trust_policy_sha256, "trust_policy_sha256")
        if self.diagnostic_status not in {"PASS", "FAIL", "REFUSED"}:
            raise CanonicalizationError("unsupported finite diagnostic status")
        if type(self.evidence_json) is not bytes or not self.evidence_json:
            raise CanonicalizationError("exact nonempty native evidence bytes are required")
        if (
            self.authorization_status != "HOST_CONFIGURED_CHECKER"
            or self.authority_effect != "None"
        ):
            raise CanonicalizationError(
                "checker admission never grants execution/promotion authority"
            )
        for values in (self.refusal_codes, self.residual_obligations):
            if type(values) is not tuple or any(
                type(value) is not str or not value for value in values
            ):
                raise CanonicalizationError(
                    "result codes and obligations must be immutable text tuples"
                )
        if self.diagnostic_status == "PASS" and self.refusal_codes:
            raise CanonicalizationError("PASS cannot erase a native refusal")

    @property
    def evidence_sha256(self) -> str:
        return hashlib.sha256(self.evidence_json).hexdigest()
