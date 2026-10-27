"""Adversary connector to the existing exact Symbol Game C011 verifier.

AuthorityEffect: None. A checker pass concerns one pinned finite challenge.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from operations.domain.rop.result import Ok, Refusal, Result
from pfp.domain.cohomology.certificate_checker import check_certificate
from adversary.domain.evidence import CandidateCheckV1, CheckerVerdict, sha256_ref
from adversary.domain.models import SymbolGameRequestV1


class SymbolGameCandidateChecker:
    def __init__(self, request: SymbolGameRequestV1) -> None:
        if type(request) is not SymbolGameRequestV1:
            raise TypeError("an exact SymbolGameRequestV1 is required")
        self.request = request

    def check_candidate(
        self, *, run_key: str, objective: str, candidate_id: str,
        candidate_bytes: bytes, carrier_context: Mapping[str, Any] | None,
    ) -> Result[CandidateCheckV1, Refusal]:
        del objective, carrier_context
        def reject_float(value: str) -> None:
            raise ValueError("certificate float tokens are not exact rationals")

        def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON key: {key!r}")
                result[key] = value
            return result

        reason = ""
        try:
            candidate = json.loads(candidate_bytes, parse_float=reject_float, parse_constant=reject_float,
                object_pairs_hook=reject_duplicates)
            result = check_certificate(json.loads(self.request.case_json), candidate)
            accepted = result.passed and result.status == "SOLVED"
            reason = result.error or ("" if accepted else "The checker did not certify SOLVED")
        except (ValueError, TypeError, UnicodeError) as exc:
            accepted, reason = False, str(exc)
        verdict = CheckerVerdict.ACCEPTED if accepted else CheckerVerdict.REJECTED
        content_digest = sha256_ref(candidate_bytes)
        receipt = {
            "schema_version": "core.adversary.symbol-game-check.v1",
            "authority_effect": "None", "run_key": run_key,
            "candidate_id": candidate_id, "candidate_content_sha256": content_digest,
            "checker_id": self.request.checker_id, "verdict": verdict.value,
            "case_sha256": sha256_ref(self.request.case_json.encode("utf-8")),
            "case_json": self.request.case_json, "reason": reason,
        }
        raw = json.dumps(receipt, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        return Ok(CandidateCheckV1(
            verdict=verdict, candidate_id=candidate_id, candidate_content_sha256=content_digest,
            checker_id=self.request.checker_id, checker_receipt_sha256=sha256_ref(raw),
            checker_receipt_bytes=raw, reason=reason,
        ))
