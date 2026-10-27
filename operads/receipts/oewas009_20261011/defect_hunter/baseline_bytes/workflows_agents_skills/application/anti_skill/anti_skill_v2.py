"""Evaluate and load executable anti-skills without granting authority.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, TypeVar

from operations.domain.rop.result import Err, Ok, Refusal, Result

from ...domain.anti_skills.anti_skill_v2 import (
    AntiSkillActivationProfileV1,
    AntiSkillCaseResultV1,
    AntiSkillEvaluationReceiptV2,
    AntiSkillFixtureBankV1,
    AntiSkillHitV1,
    AntiSkillSpecV2,
    AntiSkillSubjectV1,
    VerifiedAntiSkillRegistryV1,
    canonical_json_bytes,
)
from ...domain.anti_skills.json_wire import loads_strict_json

_T = TypeVar("_T")


def anti_skill_v2_implementation_digest() -> str:
    """Bind the exact predicate/evaluator source bytes in a stable order."""

    root = Path(__file__).resolve().parents[2]
    domain_path = root / "domain" / "anti_skills" / "anti_skill_v2.py"
    if not domain_path.exists():
        domain_path = root / "domain" / "anti_skill" / "anti_skill_v2.py"
    files = (
        domain_path,
        root / "application" / "anti_skill" / "anti_skill_v2.py",
    )
    digest = hashlib.sha256()
    for path in files:
        raw = path.read_bytes()
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return "sha256:" + digest.hexdigest()


def _canonical_reparse(raw: bytes, parser: Any, label: str) -> Any:
    if type(raw) is not bytes:
        raise TypeError(f"{label} bytes must be exact bytes")
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError(f"{label} exceeds the 2 MiB limit")
    decoded = raw.decode("utf-8", errors="strict")
    value = loads_strict_json(decoded)
    parsed = parser(value)
    if canonical_json_bytes(parsed.to_dict()) != raw:
        raise ValueError(f"{label} is not strict canonical UTF-8 JSON")
    return parsed


def parse_antiskill_spec_v2(raw: bytes) -> Result[AntiSkillSpecV2, Refusal]:
    try:
        return Ok(_canonical_reparse(raw, AntiSkillSpecV2.from_dict, "anti-skill spec"))
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return Err(Refusal("ANTISKILL_SPEC_REFUSED", str(exc), "anti-skill-spec-v2"))


def parse_antiskill_fixture_bank_v1(
    raw: bytes,
) -> Result[AntiSkillFixtureBankV1, Refusal]:
    try:
        return Ok(
            _canonical_reparse(
                raw,
                AntiSkillFixtureBankV1.from_dict,
                "anti-skill fixture bank",
            )
        )
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return Err(
            Refusal("ANTISKILL_FIXTURE_REFUSED", str(exc), "anti-skill-fixtures-v1")
        )


def parse_antiskill_evaluation_receipt_v2(
    raw: bytes,
) -> Result[AntiSkillEvaluationReceiptV2, Refusal]:
    try:
        return Ok(
            _canonical_reparse(
                raw,
                AntiSkillEvaluationReceiptV2.from_dict,
                "anti-skill evaluation receipt",
            )
        )
    except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return Err(
            Refusal(
                "ANTISKILL_RECEIPT_REFUSED",
                str(exc),
                "anti-skill-evaluation-receipt-v2",
            )
        )


def evaluate_antiskill_fixture_bank(
    specs: Iterable[AntiSkillSpecV2],
    bank: AntiSkillFixtureBankV1,
) -> Result[tuple[AntiSkillEvaluationReceiptV2, ...], Refusal]:
    """Replay every positive and negative control exactly once per case."""

    try:
        if type(bank) is not AntiSkillFixtureBankV1:
            raise TypeError("fixture bank must be exact AntiSkillFixtureBankV1")
        parsed_specs = tuple(specs)
        if not parsed_specs or any(
            type(spec) is not AntiSkillSpecV2 for spec in parsed_specs
        ):
            raise TypeError(
                "specs must be a nonempty sequence of exact AntiSkillSpecV2"
            )
        if len(parsed_specs) != len({spec.spec_id for spec in parsed_specs}):
            raise ValueError("spec ids must be unique")
        implementation_digest = anti_skill_v2_implementation_digest()
        if any(
            spec.implementation_digest != implementation_digest for spec in parsed_specs
        ):
            raise ValueError(
                "spec does not bind the current predicate implementation bytes"
            )
        case_spec_ids = {case.spec_id for case in bank.cases}
        if case_spec_ids != {spec.spec_id for spec in parsed_specs}:
            raise ValueError("fixture bank and selected spec ids differ")

        receipts: list[AntiSkillEvaluationReceiptV2] = []
        for spec in sorted(parsed_specs, key=lambda item: item.spec_id):
            cases = tuple(case for case in bank.cases if case.spec_id == spec.spec_id)
            positives = tuple(case for case in cases if case.expected_hit)
            negatives = tuple(case for case in cases if case.negative_control)
            if not positives or not negatives:
                raise ValueError(
                    f"spec {spec.spec_id} requires positive and negative controls"
                )
            contexts = tuple(sorted({case.context_key for case in cases}))
            if len(contexts) < 2:
                raise ValueError(f"spec {spec.spec_id} lacks independent contexts")
            results = tuple(
                AntiSkillCaseResultV1(
                    case_id=case.case_id,
                    case_digest=case.case_digest,
                    expected_hit=case.expected_hit,
                    observed_hit=spec.predicate.matches(case.subject),
                    negative_control=case.negative_control,
                    passed=(spec.predicate.matches(case.subject) == case.expected_hit),
                )
                for case in cases
            )
            receipts.append(
                AntiSkillEvaluationReceiptV2(
                    spec_digest=spec.spec_digest,
                    fixture_bank_id=bank.bank_id,
                    implementation_digest=implementation_digest,
                    case_results=results,
                    context_keys=contexts,
                    outcome=(
                        "COMPUTED_PASS"
                        if all(result.passed for result in results)
                        else "COMPUTED_FAIL"
                    ),
                )
            )
        return Ok(tuple(receipts))
    except (TypeError, ValueError) as exc:
        return Err(Refusal("ANTISKILL_EVALUATION_REFUSED", str(exc), "anti-skill-v2"))


@dataclass(frozen=True, slots=True)
class ActiveAntiSkillRuntimeV1:
    """Profile-scoped pure detector runtime over an externally verified registry."""

    registry: VerifiedAntiSkillRegistryV1
    profile: AntiSkillActivationProfileV1

    def __post_init__(self) -> None:
        if type(self.registry) is not VerifiedAntiSkillRegistryV1:
            raise TypeError("registry must be exact VerifiedAntiSkillRegistryV1")
        if type(self.profile) is not AntiSkillActivationProfileV1:
            raise TypeError("profile must be exact AntiSkillActivationProfileV1")
        if self.profile.registry_id != self.registry.registry_id:
            raise ValueError("activation profile registry binding differs")
        registry_ids = {spec.spec_id for spec in self.registry.specs}
        if not set(self.profile.active_spec_ids).issubset(registry_ids):
            raise ValueError("activation profile names an unverified spec")

    def evaluate(self, subject: AntiSkillSubjectV1) -> tuple[AntiSkillHitV1, ...]:
        if type(subject) is not AntiSkillSubjectV1:
            raise TypeError("runtime subject must be exact AntiSkillSubjectV1")
        if not set(subject.claim_scope).intersection(self.profile.subject_scopes):
            return ()
        active = set(self.profile.active_spec_ids)
        return tuple(
            AntiSkillHitV1(
                spec_id=spec.spec_id,
                failure_code=spec.failure_code,
                disposition=spec.disposition,
                subject_id=subject.subject_id,
                protected_fields=spec.protected_fields,
            )
            for spec in self.registry.specs
            if spec.spec_id in active and spec.predicate.matches(subject)
        )


def load_antiskill_activation_profile(
    registry: VerifiedAntiSkillRegistryV1,
    profile: AntiSkillActivationProfileV1,
) -> Result[ActiveAntiSkillRuntimeV1, Refusal]:
    try:
        return Ok(ActiveAntiSkillRuntimeV1(registry=registry, profile=profile))
    except (TypeError, ValueError) as exc:
        return Err(
            Refusal("ANTISKILL_ACTIVATION_REFUSED", str(exc), "anti-skill-profile")
        )


__all__ = [
    "ActiveAntiSkillRuntimeV1",
    "anti_skill_v2_implementation_digest",
    "evaluate_antiskill_fixture_bank",
    "load_antiskill_activation_profile",
    "parse_antiskill_evaluation_receipt_v2",
    "parse_antiskill_fixture_bank_v1",
    "parse_antiskill_spec_v2",
]
