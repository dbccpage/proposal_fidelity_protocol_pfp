"""Host-configured source-bound checks through the existing native PFP port.

The caller constructs this adapter in trusted composition, outside candidate/model
input. A checksum identifies the configured executable; it is not authentication.
The OS, host configuration and absence of privileged concurrent file replacement
remain assumptions. Native syntax/path gates are finite diagnostics, not proof of
source semantics, successful patch application, safe merge or mathematical truth.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_pfp.domain.aggregates.code_change_attestation import (
    ASSUMPTIONS_SHA256,
    CHECK_SCHEMA,
    CHECKER_ID,
    SOURCE_ASSUMPTIONS,
    SourceBoundCheckRequestV1,
    SourceBoundCheckResultV1,
    protocol_bytes,
)
from omega_engine_pfp.domain.aggregates.code_change_bind import (
    assert_candidate_binds_patch,
    verify_patch_bytes,
)
from omega_engine_pfp.domain.aggregates.code_change_patch import CodeChangePatchArtifactV1
from omega_engine_pfp.domain.entities.candidate_artifact import CandidateArtifactV1
from omega_engine_pfp.domain.exceptions import CanonicalizationError
from omega_engine_pfp.domain.shared_kernel.path import is_normalized_relative_posix
from omega_engine_pfp.domain.validation import _require_digest
from omega_engine_pfp.ffi import RustSymbolGameHost
from omega_engine_pfp.use_cases.code_change import BoundCandidate, CodeChangeSession

_LOCUS = "omega_engine_pfp.infrastructure.code_change_checker"
_GATES = ("gate_ownership", "gate_protected", "gate_syntax")


def _refuse(code: str, message: str) -> Err:
    return Err(Refusal(code, message, _LOCUS))


@dataclass(frozen=True, slots=True)
class NativeCheckerTrust:
    """Trusted host input. Never deserialize this policy from a model reply."""

    binary_path: Path
    binary_sha256: str
    checker_id: str = CHECKER_ID
    request_schema: str = CHECK_SCHEMA
    assumptions_sha256: str = ASSUMPTIONS_SHA256

    def __post_init__(self) -> None:
        object.__setattr__(self, "binary_path", Path(self.binary_path).resolve())
        _require_digest(self.binary_sha256, "binary_sha256")
        if (
            self.checker_id != CHECKER_ID
            or self.request_schema != CHECK_SCHEMA
            or self.assumptions_sha256 != ASSUMPTIONS_SHA256
        ):
            raise CanonicalizationError("unsupported host checker/schema/assumption policy")


class SourceBoundCodeChangeChecker:
    """One bounded run over frozen task/source/config and existing native gates.

    The retained native task and rolling digest are the caller-held commitments
    required by native `code_change.rs`. Fresh attempts extend that same native
    root; neither candidate nor operation allowance resets on a repair. Replay
    requires a result this instance actually issued, not a caller-rehashed claim.
    Reconstructing another instance is a new host-authorized run, not continuation.
    """

    def __init__(
        self,
        *,
        session: CodeChangeSession,
        run_id: str,
        source_files: tuple[tuple[str, bytes], ...],
        trust: NativeCheckerTrust,
        max_native_calls: int | None = None,
    ) -> None:
        if type(session) is not CodeChangeSession or type(trust) is not NativeCheckerTrust:
            raise CanonicalizationError("exact host session and checker trust are required")
        if type(source_files) is not tuple or not source_files:
            raise CanonicalizationError("frozen nonempty source files are required")
        if any(
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not bytes
            for item in source_files
        ):
            raise CanonicalizationError("source files must be immutable (path, exact bytes) pairs")
        paths = tuple(path for path, _ in source_files)
        if paths != tuple(sorted(set(paths))) or any(
            not is_normalized_relative_posix(path) for path in paths
        ):
            raise CanonicalizationError("source paths must be sorted unique contained POSIX paths")
        if sum(len(data) for _, data in source_files) > 1024 * 1024:
            raise CanonicalizationError("source snapshot exceeds the finite 1 MiB limit")
        self._session = session
        self._trust = trust
        self._run_id = run_id
        self._source_files = source_files
        self._source_sha256 = hashlib.sha256(
            protocol_bytes(
                {
                    "source_revision": session.payload.source_revision,
                    "files": [
                        (path, hashlib.sha256(data).hexdigest(), len(data))
                        for path, data in source_files
                    ],
                }
            )
        ).hexdigest()
        calls = session.payload.operation_budget if max_native_calls is None else max_native_calls
        if type(calls) is not int or not 1 <= calls <= session.payload.operation_budget:
            raise CanonicalizationError("native call limit must fit the existing operation budget")
        self._max_calls = calls
        self._native_calls = 0
        self._issued: dict[str, SourceBoundCheckResultV1] = {}
        self._attempt_count = 0
        self._root: dict | None = None
        self._task_digest: str | None = None
        self._rolling_digest: str | None = None
        self._stopped = False
        self._policy_sha256 = hashlib.sha256(
            protocol_bytes(
                {
                    "checker": {**asdict(trust), "binary_path": str(trust.binary_path)},
                    "packet_id": session.packet_id,
                    "source_sha256": self._source_sha256,
                    "assumptions": SOURCE_ASSUMPTIONS,
                    "run_id": run_id,
                    "candidate_budget": session.payload.candidate_budget,
                    "native_call_budget": calls,
                }
            )
        ).hexdigest()

    @property
    def native_calls(self) -> int:
        return self._native_calls

    def prepare(self, bound: BoundCandidate, *, attempt_id: str) -> SourceBoundCheckRequestV1:
        return SourceBoundCheckRequestV1(
            run_id=self._run_id,
            attempt_id=attempt_id,
            attempt_index=self._attempt_count,
            packet_id=self._session.packet_id,
            candidate_id=bound.candidate.candidate_id,
            patch_sha256=bound.patch.patch_sha256,
            source_revision=self._session.payload.source_revision,
            source_sha256=self._source_sha256,
            checker_id=self._trust.checker_id,
            assumptions_sha256=self._trust.assumptions_sha256,
        )

    def _validate(
        self, request: SourceBoundCheckRequestV1, bound: BoundCandidate
    ) -> Refusal | None:
        if type(request) is not SourceBoundCheckRequestV1 or type(bound) is not BoundCandidate:
            return Refusal(
                "CHECKER_INPUT_MALFORMED", "exact request and bound candidate required", _LOCUS
            )
        if (
            type(bound.candidate) is not CandidateArtifactV1
            or type(bound.patch) is not CodeChangePatchArtifactV1
            or type(bound.patch_bytes) is not bytes
        ):
            return Refusal(
                "CHECKER_INPUT_MALFORMED", "typed candidate/patch and exact bytes required", _LOCUS
            )
        if request.checker_id != self._trust.checker_id:
            return Refusal(
                "CHECKER_UNKNOWN", "checker is not authorized by host configuration", _LOCUS
            )
        expected = replace(
            self.prepare(bound, attempt_id=request.attempt_id),
            attempt_index=request.attempt_index,
        )
        # Attempt freshness is checked separately; historical replay retains its index.
        if any(
            getattr(request, name) != getattr(expected, name)
            for name in (
                "run_id",
                "packet_id",
                "candidate_id",
                "patch_sha256",
                "source_revision",
                "source_sha256",
                "assumptions_sha256",
                "schema_version",
                "authority_effect",
            )
        ):
            return Refusal(
                "CHECKER_BINDING_MISMATCH", "source/task/candidate/assumptions differ", _LOCUS
            )
        try:
            verify_patch_bytes(bound.patch, bound.patch_bytes)
            assert_candidate_binds_patch(bound.candidate, bound.patch)
            if (
                bound.patch.packet_id != self._session.packet_id
                or bound.candidate.packet_id != self._session.packet_id
                or bound.patch.base_source_revision != self._session.payload.source_revision
            ):
                return Refusal(
                    "CHECKER_BINDING_MISMATCH", "candidate belongs to another source/task", _LOCUS
                )
        except (CanonicalizationError, TypeError) as exc:
            return Refusal("CHECKER_BINDING_MISMATCH", str(exc), _LOCUS)
        return None

    def _trust_refusal(self) -> Refusal | None:
        try:
            actual = hashlib.sha256(self._trust.binary_path.read_bytes()).hexdigest()
        except OSError:
            return Refusal(
                "CHECKER_UNAVAILABLE", "configured checker bytes are unavailable", _LOCUS
            )
        if actual != self._trust.binary_sha256:
            return Refusal("CHECKER_PIN_MISMATCH", "configured checker bytes changed", _LOCUS)
        return None

    def check(
        self,
        request: SourceBoundCheckRequestV1,
        bound: BoundCandidate,
    ) -> Result[SourceBoundCheckResultV1, Refusal]:
        refusal = self._validate(request, bound) or self._trust_refusal()
        if refusal:
            return Err(refusal)
        if request.attempt_id in self._issued:
            return self.replay(self._issued[request.attempt_id], request, bound)
        if request.attempt_index != self._attempt_count:
            return _refuse(
                "CHECKER_STALE_ATTEMPT", "a fresh attempt must use the next host-held index"
            )
        needed = 3 if self._root is None else 2
        if (
            self._stopped
            or self._attempt_count >= self._session.payload.candidate_budget
            or self._native_calls + needed > self._max_calls
        ):
            return _refuse(
                "CHECKER_BUDGET_EXHAUSTED", "the continuing native check budget is exhausted"
            )
        self._attempt_count += 1
        host = RustSymbolGameHost(binary_path=self._trust.binary_path)
        evidence = []

        def invoke(action, **payload):
            self._native_calls += 1
            result = getattr(host, action)(**payload)
            if isinstance(result, Err):
                evidence.append({"action": action, "transport_refusal": result.error.to_dict()})
                return None
            evidence.append({"action": action, "outcome": result.value})
            if result.value.get("success") is not True:
                return None
            return result.value.get("result")

        if self._root is None:
            root = invoke(
                "create_code_change_proposal",
                task_id="source-bound:" + self._policy_sha256,
                objective=self._session.payload.objective,
                base_revision=self._session.payload.source_revision,
                owned_paths=self._session.payload.owned_paths,
                protected_paths=self._session.payload.protected_paths,
                candidate_budget=self._session.payload.candidate_budget,
                operation_budget=self._session.payload.operation_budget,
                required_gates=_GATES,
            )
            if type(root) is dict:
                self._root = root
                self._task_digest = root.get("task_packet_sha256")
                self._rolling_digest = root.get("run_root_digest")
        submitted = None
        if self._root is not None:
            submitted = invoke(
                "submit_patch_candidate",
                run_root=self._root,
                expected_task_packet_sha256=self._task_digest,
                candidate_id=request.request_sha256,
                producer_id=bound.candidate.producer_id,
                patch_text=bound.patch_bytes.decode("utf-8"),
            )
        receipts = None
        if type(submitted) is dict:
            self._root = submitted["run_root"]
            self._rolling_digest = submitted["run_root_digest"]
            receipts = invoke(
                "evaluate_patch_gates",
                run_root=self._root,
                expected_task_packet_sha256=self._task_digest,
                expected_run_root_digest=self._rolling_digest,
                patch_artifact=submitted["patch_artifact"],
            )
        codes = ()
        status = "REFUSED"
        if (
            type(receipts) is list
            and all(type(r) is dict for r in receipts)
            and {r.get("gate_name") for r in receipts} == set(_GATES)
        ):
            if len(receipts) == len(_GATES) and all(
                r.get("patch_sha256") == request.patch_sha256
                and r.get("authority_effect") == "None"
                for r in receipts
            ):
                status = "PASS" if all(r.get("disposition") == "PASS" for r in receipts) else "FAIL"
                codes = tuple(
                    sorted(
                        {
                            r["gate_name"] + "_FAILED"
                            for r in receipts
                            if r.get("disposition") != "PASS"
                        }
                    )
                )
        if status == "REFUSED":
            codes = ("CHECKER_NATIVE_REFUSED",)
            self._stopped = True  # Unknown/native failures do not invite blind retries.
        refusal = self._trust_refusal()
        if refusal:
            status, codes, self._stopped = "REFUSED", (refusal.code,), True
        result = SourceBoundCheckResultV1(
            request=request,
            checker_sha256=self._trust.binary_sha256,
            trust_policy_sha256=self._policy_sha256,
            diagnostic_status=status,
            evidence_json=protocol_bytes(evidence),
            refusal_codes=codes,
            next_action="Review finite diagnostics."
            if status == "PASS"
            else "Retain the failed candidate; repair under the same remaining budget or stop.",
        )
        self._issued[request.attempt_id] = result
        return Ok(result)

    def replay(
        self,
        result: SourceBoundCheckResultV1,
        request: SourceBoundCheckRequestV1,
        bound: BoundCandidate,
    ) -> Result[SourceBoundCheckResultV1, Refusal]:
        refusal = self._validate(request, bound) or self._trust_refusal()
        if refusal:
            return Err(refusal)
        if type(result) is not SourceBoundCheckResultV1:
            return _refuse("CHECKER_INPUT_MALFORMED", "exact checker result required")
        if result.request != request:
            return _refuse(
                "CHECKER_STALE_ATTEMPT", "stored evidence belongs to a different attempt"
            )
        if self._issued.get(request.attempt_id) != result:
            return _refuse(
                "CHECKER_EVIDENCE_UNISSUED", "this host run did not issue the presented evidence"
            )
        return Ok(result)
