"""Thin shared task-turn boundary for provider and current-IDE composition.

Transport/accounting stay with the caller. PFP owns the public prompt and checks
the actual submitted bytes. Shape-only prose is explicitly unverified.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
from pathlib import Path
import re

from pfp.domain.contracts.pfp_runtime import (
    PfpPrompt,
    PfpPromptTemplate,
    PfpTaskPrompt,
)
from pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase, task_input_sha256
from pfp.use_cases.pfp_proposal import CheckPfpTaskTurnUseCase


_UNSETTLED_ATTEMPT_STATES = frozenset({
    "CompletedCostUnknown",
    "CompletedOverEstimatedBudget",
    "CompletedOverAdmittedBudget",
    "CompletedAccountingUnavailable",
})


class PfpTurnRefusal(ValueError):
    def __init__(self, checked: dict, *, candidate=None, budget_receipt=None,
                 attempt_state: str | None = None):
        self.checked = checked
        self.candidate, self.budget_receipt = candidate, budget_receipt
        self.attempt_state = attempt_state
        self.code = attempt_state if attempt_state else "PFP_" + checked["failure_class"]
        super().__init__(self.code)


@dataclass(frozen=True)
class PreparedTaskTurn:
    task: PfpTaskPrompt
    prompt: PfpPrompt
    checker_id: str
    # Adversary adds source-bound diagnostics after preparation. They deliberately
    # remain outside the public task and its historical input digest profile.
    observation_metadata: dict = field(default_factory=dict, compare=False)

    @property
    def binding(self) -> dict:
        return dict(task_id=self.task.challenge,
            attempt_id=self.prompt.response_schema["properties"]["attempt_id"]["const"],
            input_sha256=task_input_sha256(self.task), checker_id=self.checker_id)

    def check(self, raw_reply: bytes, *, judges=(), require_checker: bool = False) -> dict:
        result = CheckPfpTaskTurnUseCase().execute(self.task, self.prompt, raw_reply,
            judges=judges, require_checker=require_checker)
        return {**result, "binding": self.binding}

    def check_completion(self, content: str, *, judges=(), require_checker: bool = False) -> dict:
        """Check decoded completion text without losing invalid Unicode custody.

        A JSON vendor envelope can contain escaped lone surrogates. They have no
        valid UTF-8 encoding: surrogatepass retains them as explicitly labelled
        invalid completion bytes, which the strict reply decoder must refuse.
        These bytes never stand in for the provider's original wire body.
        """
        try:
            raw = content.encode("utf-8")
        except UnicodeEncodeError:
            raw = content.encode("utf-8", errors="surrogatepass")
            result = self.check(raw, judges=judges, require_checker=require_checker)
            return {**result, "raw_reply_encoding": "utf-8-surrogatepass",
                "reason": "INVALID_COMPLETION_UNICODE"}
        return self.check(raw, judges=judges, require_checker=require_checker)

    def replay(self, record: dict, *, judges=(), require_checker: bool = False) -> dict:
        """Recheck retained bytes, never trust a stored verdict or call a provider."""
        if record.get("binding") != self.binding:
            raise ValueError("REPLAY_BINDING_MISMATCH")
        try:
            raw = base64.b64decode(record["raw_reply_base64"], validate=True)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("REPLAY_RAW_MISMATCH") from exc
        if sha256(raw).hexdigest() != record.get("raw_reply_sha256"):
            raise ValueError("REPLAY_RAW_MISMATCH")
        return self.check(raw, judges=judges, require_checker=require_checker)


def prepare_task_turn(*, system: str, user: str, task_id: str, attempt_id: str,
    answer_schema: dict | None = None, context: dict | None = None,
    checker_id: str = "shape-only-v1", feedback: str | None = None) -> PreparedTaskTurn:
    if type(checker_id) is not str or not checker_id.strip():
        raise ValueError("CHECKER_ID_REQUIRED")
    task = PfpTaskPrompt(task_id, system, {"prompt": user, "context": context or {}},
        answer_schema if answer_schema is not None else {"type": "string", "minLength": 1})
    prompt = PreparePfpTaskTurnUseCase().execute(
        PfpPromptTemplate(system, "[USER PROMPT]", {}), task, attempt_id, feedback=feedback)
    return PreparedTaskTurn(task, prompt, checker_id)


def complete_task_turn(gateway, request, *, task_id: str, attempt_id: str,
    provider=None, model=None, answer_schema=None, checker_id="shape-only-v1",
    judges=(), require_checker: bool = False,
    immune_store=None, lineage=None,
    model_id: str | None = None,
    scaffold_digest: str = "task_turn_v1",
    precedent_set_digest: str = "none"):
    """Compatibility facade for existing complete(request)->(candidate, receipt) ports."""
    import pfp_core.caller_feedback as cf
    from eis.domain.pharmacy_models import LearningEvidencePreimageV1
    from pciv.use_cases.custody import ensure_caller_prompt_genome
    from pciv.use_cases.immunity import resolve_civilization_immune_store

    user = request.user
    if request.messages:
        user = json.dumps([dict(role=item.role, content=item.content) for item in request.messages])
    turn = prepare_task_turn(system=request.system or "Carry out the supplied conversation task.",
        user=user, task_id=task_id, attempt_id=attempt_id,
        answer_schema=answer_schema, checker_id=checker_id)
    prompt_bytes = (turn.prompt.system + "\n" + turn.prompt.user).encode("utf-8")
    caller_lineage = (
        lineage
        if lineage is not None
        else cf.CallerLineageContextV1(
            prompt_id=ensure_caller_prompt_genome(
                prompt_bytes, {"task_id": task_id, "checker_id": checker_id}
            ).prompt_id
        )
    )
    repo_root = Path(__file__).resolve().parents[2]
    store = (
        immune_store
        if immune_store is not None
        else resolve_civilization_immune_store(None, repo_root, read_only=True)
    )
    decoding = request.decoding
    if decoding is not None and decoding.response_format is not None:
        decoding = replace(decoding, response_format={"type": "json_schema", "json_schema": {
            "name": "pfp_task_turn", "strict": True, "schema": turn.prompt.response_schema}})
    mediated = replace(request, system=turn.prompt.system, user=turn.prompt.user,
        messages=(), decoding=decoding)
    options = {key: value for key, value in dict(provider=provider, model=model).items()
        if value is not None}
    bind_action = getattr(gateway, "for_action", None)
    if callable(bind_action):
        gateway = bind_action(turn.binding["attempt_id"])
    try:
        candidate, receipt = gateway.complete(mediated, **options)
    except Exception as exc:
        refusal = _unsettled_reply_refusal(turn, exc)
        if refusal is None:
            raise
        raise refusal from exc
    checked = turn.check_completion(candidate.content, judges=judges, require_checker=require_checker)
    reply_bytes = candidate.content.encode("utf-8", errors="replace")
    host_failed = (
        (not checked["schema_valid"])
        or (checked.get("failure_class", "NONE") != "NONE")
        or (checked.get("status") == "CHECKER_DEFECT")
    )
    danger = None
    if host_failed:
        observer = checker_id if checker_id in cf.HOST_OBSERVERS else "host.public_smoke"
        checker_payload = {
            "status": checked.get("status"),
            "failure_class": checked.get("failure_class"),
            "reason": checked.get("reason", ""),
            "judges": checked.get("judges", ()),
        }
        danger_text = json.dumps(checker_payload, sort_keys=True, separators=(",", ":"))
        danger = cf.host_danger("PUBLIC_CHECK_FAILED", observer, danger_text, defects=1)
    verdict = cf.screen_caller_turn(
        cf.ImmuneScreenRequestV1(
            lineage=caller_lineage,
            prompt_utf8_bytes=prompt_bytes,
            candidate_reply_bytes=reply_bytes,
            signal2_danger=danger,
        ),
        store,
    )
    checked["immune_verdict"] = verdict.to_dict()
    checked["prompt_id"] = caller_lineage.prompt_id

    if host_failed and not store.read_only:
        judge_reasons = [
            str(item.get("reason", ""))
            for item in checked.get("judges", ())
            if isinstance(item, dict) and not item.get("accepted", True) and item.get("reason")
        ]
        failed_preds = tuple(judge_reasons) or (str(checked.get("failure_class", "TASK_FAILURE")),)
        checker_bytes = json.dumps(
            {
                "status": checked.get("status"),
                "failure_class": checked.get("failure_class"),
                "reason": checked.get("reason", ""),
                "judges": checked.get("judges", ()),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        preimage = LearningEvidencePreimageV1(
            prompt_id=caller_lineage.prompt_id,
            prompt_utf8_bytes=prompt_bytes,
            candidate_reply_bytes=reply_bytes,
            failure_class=str(checked.get("failure_class") or "TASK_TURN_FAILURE"),
            failed_predicates=failed_preds,
            checker_id=checker_id,
            checker_output_bytes=checker_bytes,
        )
        raw_pat = (judge_reasons[0] if judge_reasons else str(checked.get("reason") or checked.get("failure_class") or "TASK_FAILURE"))[:80]
        safe_pat = re.escape(raw_pat.strip() or "TASK_FAILURE")
        try:
            store.record_failure(
                lineage=caller_lineage,
                preimage=preimage,
                target_pattern=safe_pat,
                positive_fixture="HOST_ACCEPTED_CLEAN_RESPONSE",
                run_id=attempt_id,
                task_id=task_id,
                producer_actor="wild_caller",
                model_id=model_id or (str(model) if model is not None else "unknown_model"),
                scaffold_digest=scaffold_digest,
                precedent_set_digest=precedent_set_digest,
            )
        except ValueError:
            pass

    if not checked["schema_valid"] or verdict.disposition == cf.HOLD:
        raise PfpTurnRefusal(checked, candidate=candidate, budget_receipt=receipt)
    answer = checked["answer"]
    if type(answer) is str:
        candidate = replace(candidate, content=answer)
    return candidate, receipt, checked


def _unsettled_reply_refusal(turn: PreparedTaskTurn, exc: BaseException) -> PfpTurnRefusal | None:
    """Keep a charged reply when estimated accounting refuses to settle it.

    Pre-dispatch failures have no outcome and stay the caller's exception.
    """
    outcome = getattr(exc, "outcome", None)
    state = getattr(outcome, "state", None)
    if state not in _UNSETTLED_ATTEMPT_STATES:
        return None
    content = getattr(getattr(outcome, "candidate", None), "content", None)
    if type(content) is not str:
        return None
    checked = turn.check_completion(content)
    raw = getattr(outcome, "reply_bytes", None)
    if type(raw) is bytes:
        checked["provider_wire"] = dict(
            raw_reply_base64=base64.b64encode(raw).decode("ascii"),
            raw_reply_sha256=sha256(raw).hexdigest(), raw_reply_bytes=len(raw))
    checked["attempt_state"] = state
    admitted = getattr(outcome, "admitted", None)
    return PfpTurnRefusal(
        checked, candidate=getattr(outcome, "candidate", None),
        budget_receipt=getattr(admitted, "receipt", None), attempt_state=state)
