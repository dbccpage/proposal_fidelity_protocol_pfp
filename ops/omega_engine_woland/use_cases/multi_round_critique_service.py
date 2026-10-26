"""Multi-round critique loop service with live model proposals and external diff oracle.

Coordinates:
1. Candidate code proposal generation from model (live LLM or scripted protocol).
2. Unified diff computation against base module.
3. External Diff Oracle inspection (AST check, invariant check, isolated test runner).
4. Rejection and burial of failing candidates in the Cemetery ledger.
5. Multi-round repair transition (<= 3) with counterexample feedback.
6. Acceptance of repaired candidates and canonical evidence landing under _ic/.

AuthorityEffect: None.
"""

from __future__ import annotations

import base64
import datetime
import difflib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPromptTemplate, PfpTaskPrompt
from omega_engine_pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase
from omega_engine_pfp.use_cases.pfp_proposal import CheckPfpTaskTurnUseCase
from omega_engine_woland.domain.evidence import (
    CheckerVerdict,
    sha256_ref,
)
from omega_engine_woland.domain.native import NativeOperationPort
from omega_engine_woland.domain.ports import (
    CandidateCheckerPort,
    NullCandidateCheckerAdapter,
)
from omega_engine_woland.stage.domain import (
    CemeteryHeadstoneV1,
)
from omega_engine_woland.use_cases.persistence import (
    _reported_projection,
    content_addressed_receipt_id,
    run_directory_name,
)

_LOCUS = "omega_engine_woland.use_cases.multi_round_critique_service"


def _completion_bytes(reply_text: str) -> tuple[bytes, str]:
    """UTF-8 completion bytes, or surrogatepass when the text is not Unicode."""
    try:
        return reply_text.encode("utf-8"), "utf-8"
    except UnicodeEncodeError:
        return reply_text.encode("utf-8", errors="surrogatepass"), "utf-8-surrogatepass"


def _provider_wire(reply: Any) -> dict[str, Any] | None:
    """Original vendor bytes when the port supplies them, including an empty body."""
    vendor_wire = getattr(reply, "raw_reply_bytes", None)
    if type(vendor_wire) is not bytes:
        return None
    return {
        "raw_reply_base64": base64.b64encode(vendor_wire).decode("ascii"),
        "raw_reply_sha256": sha256_ref(vendor_wire),
        "raw_reply_bytes": len(vendor_wire),
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> bytes:
    raw = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    path.write_bytes(raw)
    return raw


class ModelCompletionPort(Protocol):
    """Protocol for model completion adapters."""

    def complete(self, system_prompt: str, user_prompt: str) -> Any: ...


@dataclass(frozen=True)
class RoundEvidenceV1:
    round_index: int
    candidate_id: str
    input_prompt: dict[str, Any]
    input_prompt_sha256: str
    raw_reply_text: str
    raw_reply_sha256: str
    candidate_code: str
    candidate_code_sha256: str
    patch_diff: str
    patch_diff_sha256: str
    oracle_verdict: CheckerVerdict
    oracle_reason: str
    oracle_receipt: dict[str, Any]
    oracle_receipt_sha256: str
    tokens_billed: int = 0
    cost_usd: float = 0.0
    killed: bool = False
    headstone_file: str | None = None


@dataclass(frozen=True)
class MultiRoundCritiqueOutcomeV1:
    run_key: str
    run_dir: Path
    rounds_executed: int
    surviving_candidate_id: str | None
    terminal_status: str
    manifest_path: Path
    receipt_path: Path
    cemetery_headstones: tuple[str, ...]
    total_tokens_billed: int
    total_cost_usd: float


def _extract_code_block(text: str) -> str:
    """Extract code from ```python ... ``` markdown block, or return stripped text."""
    pattern = re.compile(r"```(?:python)?\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
    match = pattern.search(text)
    if match:
        return match.group(1).rstrip() + "\n"
    return text.strip() + "\n"


class MultiRoundCritiqueService:
    """Orchestrates multi-round candidate proposals and external oracle diff audits."""

    def __init__(
        self,
        *,
        model_port: ModelCompletionPort | None = None,
        oracle: CandidateCheckerPort | None = None,
        max_rounds: int = 3,
        native_support: NativeOperationPort,
    ) -> None:
        self._native_support = native_support
        if model_port is None:
            raise ValueError("MODEL_COMPLETION_PORT_REQUIRED: inject a model completion port")
        self.model_port = model_port
        self.oracle = oracle if oracle is not None else NullCandidateCheckerAdapter()
        if type(max_rounds) is not int or not 1 <= max_rounds <= 3:
            raise ValueError("MAX_ROUNDS_MUST_BE_1_TO_3")
        self.max_rounds = max_rounds

    def execute_critique_loop(
        self,
        *,
        run_key: str,
        objective: str,
        base_file_path: Path | str,
        test_file_path: Path | str,
        workspace_dir: Path | str,
        output_dir: Path | str,
        model_name: str = "unknown_model",
        round_1_instruction: str | None = None,
        extra_carrier_context: Mapping[str, Any] | None = None,
    ) -> Result[MultiRoundCritiqueOutcomeV1, Refusal]:
        base_path = Path(base_file_path).resolve()
        test_path = Path(test_file_path).resolve()
        workspace_path = Path(workspace_dir).resolve()
        estate_root = Path(output_dir).resolve()

        if not base_path.is_file():
            return Err(Refusal(code="BASE_FILE_MISSING", message=f"Base file not found: {base_path}", locus=_LOCUS))
        if not test_path.is_file():
            return Err(Refusal(code="TEST_FILE_MISSING", message=f"Test file not found: {test_path}", locus=_LOCUS))

        run_folder = estate_root / "runs" / run_directory_name(run_key, native_support=self._native_support)
        cemetery_dir = estate_root / "cemetery"
        try:
            run_folder.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            return Err(Refusal(code="RUN_OUTPUT_EXISTS",
                message=f"Run output already exists; choose a new run key: {run_folder}", locus=_LOCUS))
        cemetery_dir.mkdir(parents=True, exist_ok=True)

        base_code = base_path.read_text(encoding="utf-8")
        base_sha256 = sha256_ref(base_code.encode("utf-8"))
        test_code = test_path.read_text(encoding="utf-8")
        test_sha256 = sha256_ref(test_code.encode("utf-8"))

        carrier_ctx: dict[str, Any] = {
            "base_file_path": str(base_path),
            "test_file_path": str(test_path),
            "workspace_dir": str(workspace_path),
            "authority_effect": "None",
        }
        if extra_carrier_context:
            carrier_ctx.update(extra_carrier_context)

        system_prompt = (
            "You are Begemot, an expert software developer operating under the Techne Council. "
            "You write clean, modular, zero-float, pure domain Python code adhering strictly to Clean Architecture. "
            "Your code must have zero floats, zero external runtime dependencies, and all methods must be completely implemented. "
            "Return the full, updated Python source code for the target module enclosed in a single ```python ... ``` block. "
            "AuthorityEffect: None."
        )

        rounds_evidence: list[RoundEvidenceV1] = []
        cemetery_headstones: list[str] = []
        surviving_id: str | None = None
        current_feedback = ""
        last_diff = ""
        total_tokens = 0
        total_cost = 0.0

        for r_idx in range(1, self.max_rounds + 1):
            cand_id = f"cand_{r_idx}"
            round_dir = run_folder / f"round_{r_idx}"
            round_dir.mkdir(parents=True, exist_ok=True)

            # Construct round prompt
            if r_idx == 1:
                instruction_text = round_1_instruction or (
                    "Provide the complete replacement implementation for the module to satisfy all tests and contracts. "
                    "Ensure exact rational arithmetic, strict type validation, zero float usage, and full edge-case coverage."
                )
                user_prompt = (
                    f"OBJECTIVE: {objective}\n\n"
                    f"BASE MODULE ({base_path.name}):\n"
                    f"```python\n{base_code}\n```\n\n"
                    f"TEST CONTRACT ({test_path.name}):\n"
                    f"```python\n{test_code}\n```\n\n"
                    f"INSTRUCTIONS:\n{instruction_text}"
                )
            else:
                user_prompt = (
                    f"OBJECTIVE: {objective}\n\n"
                    f"PREVIOUS CANDIDATE (cand_{r_idx - 1}) FAILED THE EXTERNAL ORACLE CHECKS.\n\n"
                    f"PREVIOUS DIFF:\n```diff\n{last_diff}\n```\n\n"
                    f"ORACLE DEFECT REPORT & COUNTEREXAMPLE TRACE:\n{current_feedback}\n\n"
                    f"TEST CONTRACT ({test_path.name}):\n"
                    f"```python\n{test_code}\n```\n\n"
                    "REPAIR INSTRUCTIONS:\n"
                    "Analyze the oracle test failure and counterexample above. "
                    "Produce a corrected replacement implementation that resolves the defect while preserving all invariants. "
                    "Return the full code in a ```python ... ``` block."
                )

            task = PfpTaskPrompt(f"critique:{run_key}:{cand_id}", system_prompt,
                {"prompt": user_prompt}, {"type": "string", "minLength": 1})
            prepared = PreparePfpTaskTurnUseCase().execute(
                PfpPromptTemplate(system_prompt, "[USER PROMPT]", {}), task, f"round-{r_idx}")
            prompt_payload = {
                "round_index": r_idx,
                "candidate_id": cand_id,
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "model": model_name,
                "system_prompt": prepared.system,
                "user_prompt": prepared.user,
                "pfp_task": {"challenge": task.challenge, "task_text": task.task_text,
                    "case": task.case, "answer_schema": task.answer_schema},
                "pfp_attempt_id": f"round-{r_idx}",
            }
            prompt_bytes = json.dumps(prompt_payload, indent=2, sort_keys=True).encode("utf-8")
            (round_dir / "input_prompt.json").write_bytes(prompt_bytes)
            prompt_sha256 = sha256_ref(prompt_bytes)

            # Model Completion
            try:
                reply = self.model_port.complete(prepared.system, prepared.user)
            except Exception as exc:
                return Err(Refusal(code="MODEL_COMPLETION_ERROR", message=f"Completion failed in round {r_idx}: {exc}", locus=_LOCUS))

            reply_text = getattr(reply, "content", str(reply))
            tokens_in = getattr(reply, "input_tokens", None)
            tokens_out = getattr(reply, "output_tokens", None)
            cost = getattr(reply, "cost_usd", None)
            completion_bytes, encoding = _completion_bytes(reply_text)
            raw_reply_payload = {
                "round_index": r_idx,
                "candidate_id": cand_id,
                "model": getattr(reply, "model", model_name),
                "reply_text": reply_text,
                "input_tokens": tokens_in,
                "output_tokens": tokens_out,
                "cost_usd": cost,
                "authority_effect": "None",
                "provider_wire": _provider_wire(reply),
                "accounting_state": getattr(reply, "accounting_state", None),
                "reported_cost_usd": getattr(reply, "reported_cost_usd", None),
            }
            _write_json(round_dir / "raw_reply.json", raw_reply_payload)
            pfp = CheckPfpTaskTurnUseCase().execute(task, prepared, completion_bytes)
            raw_reply_payload.update(pfp=pfp, raw_reply_encoding=encoding)
            raw_reply_bytes = _write_json(round_dir / "raw_reply.json", raw_reply_payload)
            reply_sha256 = sha256_ref(raw_reply_bytes)
            if not pfp["schema_valid"]:
                return Err(Refusal(code="PFP_" + pfp["failure_class"],
                    message=f"Round {r_idx} reply rejected; raw reply retained at {round_dir}", locus=_LOCUS))
            if type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0:
                return Err(Refusal(code="UNRECONCILED_COST",
                    message=f"Round {r_idx} cost unavailable; raw reply retained at {round_dir}", locus=_LOCUS))
            if any(type(tokens) is not int or tokens < 0 for tokens in (tokens_in, tokens_out)):
                return Err(Refusal(code="UNRECONCILED_USAGE",
                    message=f"Round {r_idx} usage unavailable; raw reply retained at {round_dir}", locus=_LOCUS))
            total_tokens += tokens_in + tokens_out
            total_cost += cost

            # Candidate code extraction and diff
            candidate_code = _extract_code_block(pfp["answer"])
            try:
                candidate_bytes = candidate_code.encode("utf-8")
            except UnicodeEncodeError:
                return Err(Refusal(code="CANDIDATE_INVALID_UNICODE",
                    message=f"Round {r_idx} candidate is not UTF-8; raw reply retained at {round_dir}", locus=_LOCUS))
            (round_dir / "candidate_edit.py").write_bytes(candidate_bytes)
            cand_sha256 = sha256_ref(candidate_bytes)

            diff_lines = list(
                difflib.unified_diff(
                    base_code.splitlines(keepends=True),
                    candidate_code.splitlines(keepends=True),
                    fromfile=f"a/{base_path.name}",
                    tofile=f"b/{base_path.name}",
                )
            )
            diff_text = "".join(diff_lines)
            (round_dir / "patch.diff").write_text(diff_text, encoding="utf-8")
            diff_sha256 = sha256_ref(diff_text.encode("utf-8"))
            last_diff = diff_text

            # Oracle Inspection
            check_res = self.oracle.check_candidate(
                run_key=run_key,
                objective=objective,
                candidate_id=cand_id,
                candidate_bytes=candidate_bytes,
                carrier_context=carrier_ctx,
            )
            if check_res.is_err:
                return Err(check_res.unwrap_err())
            check = check_res.unwrap()

            if check.verdict is CheckerVerdict.NOT_MEASURED:
                raw_reply_payload["oracle_check"] = check.to_dict()
                _write_json(round_dir / "raw_reply.json", raw_reply_payload)
                return Err(Refusal(
                    code="ORACLE_NOT_MEASURED",
                    message=f"Round {r_idx} cannot be checked: {check.reason}; candidate retained at {round_dir}",
                    locus=_LOCUS,
                ))

            oracle_receipt_dict = json.loads(check.checker_receipt_bytes.decode("utf-8"))
            (round_dir / "oracle_receipt.json").write_bytes(check.checker_receipt_bytes)
            oracle_sha256 = check.checker_receipt_sha256 or sha256_ref(check.checker_receipt_bytes)

            killed = False
            headstone_rel: str | None = None
            if check.verdict == CheckerVerdict.REJECTED:
                killed = True
                current_feedback = check.reason
                if "test_stdout_excerpt" in oracle_receipt_dict and oracle_receipt_dict["test_stdout_excerpt"]:
                    current_feedback += "\n" + oracle_receipt_dict["test_stdout_excerpt"]

                headstone_filename = f"{cand_id}_{run_key}.headstone.json"
                headstone_path = cemetery_dir / headstone_filename
                headstone = CemeteryHeadstoneV1(
                    candidate_id=cand_id,
                    run_key=run_key,
                    scene_id="act5_independent_witness",
                    cause_of_death=f"ORACLE_REJECTED: {check.reason}",
                    killing_seat_id="seat_koroviev",
                    evidence_refs=(oracle_sha256,),
                    candidate_payload_sha256=cand_sha256,
                    round_index=r_idx,
                )
                headstone_bytes = json.dumps(headstone.to_dict(), indent=2, sort_keys=True).encode("utf-8")
                headstone_path.write_bytes(headstone_bytes)
                (round_dir / "headstone.json").write_bytes(headstone_bytes)
                headstone_rel = f"cemetery/{headstone_filename}"
                cemetery_headstones.append(headstone_rel)

            rounds_evidence.append(
                RoundEvidenceV1(
                    round_index=r_idx,
                    candidate_id=cand_id,
                    input_prompt=prompt_payload,
                    input_prompt_sha256=prompt_sha256,
                    raw_reply_text=reply_text,
                    raw_reply_sha256=reply_sha256,
                    candidate_code=candidate_code,
                    candidate_code_sha256=cand_sha256,
                    patch_diff=diff_text,
                    patch_diff_sha256=diff_sha256,
                    oracle_verdict=check.verdict,
                    oracle_reason=check.reason,
                    oracle_receipt=oracle_receipt_dict,
                    oracle_receipt_sha256=oracle_sha256,
                    tokens_billed=(tokens_in + tokens_out),
                    cost_usd=cost,
                    killed=killed,
                    headstone_file=headstone_rel,
                )
            )

            if check.verdict == CheckerVerdict.ACCEPTED:
                surviving_id = cand_id
                break

        # Seal Bout Evidentiary Artifacts
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        terminal_status = "ACCEPTED" if surviving_id else "REJECTED"

        manifest_data = {
            "schema_version": "omega.woland.critique-loop-manifest.v1",
            "authority_effect": "None",
            "run_key": run_key,
            "timestamp_utc": now_iso,
            "objective": objective,
            "provider": "omega_engine_woland.infrastructure.providers.llm_gateway.LlmGateway",
            "model": model_name,
            "total_tokens_billed": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "base_file": {"path": str(base_path), "sha256": base_sha256},
            "test_file": {"path": str(test_path), "sha256": test_sha256},
            "rounds_executed": len(rounds_evidence),
            "rounds": [
                {
                    "round_index": r.round_index,
                    "candidate_id": r.candidate_id,
                    "input_prompt_sha256": r.input_prompt_sha256,
                    "raw_reply_sha256": r.raw_reply_sha256,
                    "candidate_code_sha256": r.candidate_code_sha256,
                    "patch_diff_sha256": r.patch_diff_sha256,
                    "oracle_verdict": r.oracle_verdict.value,
                    "oracle_receipt_sha256": r.oracle_receipt_sha256,
                    "killed": r.killed,
                    "headstone_file": r.headstone_file,
                }
                for r in rounds_evidence
            ],
            "cemetery_headstones": cemetery_headstones,
            "surviving_candidate_id": surviving_id,
            "terminal_status": terminal_status,
        }
        manifest_path = run_folder / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data, indent=2, sort_keys=True), encoding="utf-8")

        # Novella Script
        novella_lines = [
            f"# Dialectic Critique Bout Novella: {run_key}",
            "",
            "**AuthorityEffect:** None.",
            "",
            f"**Objective:** {objective}",
            f"**Timestamp:** {now_iso}",
            f"**Terminal Status:** {terminal_status}",
            "",
            "## Act I: Problem Framing",
            f"Base module `{base_path.name}` ({base_sha256}) submitted for Techne Council review.",
            "",
            "## Act V: Independent Witness & Oracle Critique Loop",
        ]
        for r in rounds_evidence:
            novella_lines.append(f"### Round {r.round_index} ({r.candidate_id})")
            novella_lines.append(f"- **Proposer:** Begemot (Code: {r.candidate_code_sha256})")
            novella_lines.append(f"- **Diff SHA-256:** `{r.patch_diff_sha256}`")
            novella_lines.append(f"- **Oracle Verdict:** `{r.oracle_verdict.value}`")
            novella_lines.append(f"- **Oracle Reason:** {r.oracle_reason}")
            if r.killed:
                novella_lines.append(f"- **Cemetery Headstone:** `{r.headstone_file}` (Buried by Koroviev)")
            else:
                novella_lines.append("- **Outcome:** Survives as non-blocking accepted patch.")
            novella_lines.append("")

        novella_lines.extend([
            "## Act VII: Terminal Sealing",
            f"Bout concluded after {len(rounds_evidence)} round(s). Surviving candidate: `{surviving_id}`.",
        ])
        novella_text = "\n".join(novella_lines) + "\n"
        (run_folder / "uns.md").write_text(novella_text, encoding="utf-8")

        # DDA / DDC Steps
        dda_steps: list[dict[str, Any]] = []
        for r in rounds_evidence:
            dda_steps.append({
                "letter": "P",
                "round": r.round_index,
                "candidate_id": r.candidate_id,
                "candidate_hash": r.candidate_code_sha256,
            })
            if r.killed:
                dda_steps.append({
                    "letter": "R",
                    "round": r.round_index,
                    "candidate_id": r.candidate_id,
                    "action": "KILLED_BY_ORACLE",
                    "reason": r.oracle_reason,
                })
            else:
                dda_steps.append({
                    "letter": "C",
                    "round": r.round_index,
                    "candidate_id": r.candidate_id,
                    "action": "ACCEPTED_BY_ORACLE",
                })
        (run_folder / "ddc.jsonl").write_text(
            "\n".join(json.dumps(s, sort_keys=True) for s in dda_steps) + "\n",
            encoding="utf-8",
        )

        # Run Summary
        critique_verdicts = {
            r.candidate_id: ("BLOCKING" if r.killed else "NON_BLOCKING")
            for r in rounds_evidence
        }
        summary_data = {
            "authority_effect": "None",
            "run_key": run_key,
            "objective": objective,
            "critique_rounds": len(rounds_evidence),
            "critique_verdicts": critique_verdicts,
            "selected_candidate_id": surviving_id or "",
            "is_authorized": surviving_id is not None,
            "terminal_verdict": "PASS" if surviving_id else "REJECT",
            "tokens_billed": total_tokens,
            "cost_usd": round(total_cost, 6),
        }
        (run_folder / "summary.json").write_text(
            json.dumps(summary_data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        receipt_id = content_addressed_receipt_id(novella_text, dda_steps, summary_data, native_support=self._native_support)
        uts = _reported_projection(summary_data, native_support=self._native_support)["uts_jsonl"].encode("utf-8")
        (run_folder / "uts.jsonl").write_bytes(uts)
        receipt_dict = {
            "schema_version": "omega.woland.critique-loop-receipt.v1",
            "authority_effect": "None",
            "receipt_id": receipt_id,
            "run_key": run_key,
            "timestamp_utc": now_iso,
            "status": "BOUNDED_RESIDUAL" if surviving_id else "UNAUTHORIZED_REFUSAL",
            "surviving_candidate_id": surviving_id,
            "cemetery_count": len(cemetery_headstones),
            "critique_rounds": len(rounds_evidence),
            "output_layout": "omega.woland.critique-loop-layout.v2",
            "uts_sha256": sha256_ref(uts),
        }
        receipt_path = run_folder / "receipt.json"
        receipt_path.write_text(json.dumps(receipt_dict, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        return Ok(
            MultiRoundCritiqueOutcomeV1(
                run_key=run_key,
                run_dir=run_folder,
                rounds_executed=len(rounds_evidence),
                surviving_candidate_id=surviving_id,
                terminal_status=terminal_status,
                manifest_path=manifest_path,
                receipt_path=receipt_path,
                cemetery_headstones=tuple(cemetery_headstones),
                total_tokens_billed=total_tokens,
                total_cost_usd=round(total_cost, 6),
            )
        )
