"""Application use case orchestrating the 7-Act Woland Swarm bout.

Woland is the single point of entry that renders the final verdict on a
Symbol Game answer, so the verdict is computed only from bound, exact evidence:
the carrier measurement (exact rationals behind a verified certificate) and the
challenge checker's verdict bound to the candidate bytes and the checker
receipt digest. Narrative, keywords and thresholds decide nothing.

This module is a use case. It never imports the composition root; runtimes,
scorers, checkers and the intelligence root are injected (see
``omega_engine_woland.runtime.build_woland_service``). A missing collaborator is
a typed refusal or an honest ``NOT_MEASURED``, never a silent default.

Origin: omega_engine_woland.use_cases.bout_service.
A recorded bout is a proposal and does not claim external admission.
AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from collections.abc import Callable, Mapping
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from omega_engine_governance.domain.ingress.limits import (
    MAX_ADMITTED_TEXT_BYTES,
    REFUSAL_TEXT_TOO_LARGE,
    check_text_bytes,
)
from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.estate_ports import AntiSkillDecisionV1, AntiSkillGatePort
from omega_engine_woland.domain.intelligence_digestion import IntelligenceCollectionPort
from omega_engine_woland.domain.native import NativeOperationPort
from omega_engine_woland.stage.application.emission import (
    build_intelligence_event,
    emit_event,
)
from omega_engine_woland.stage.application.run_swarm import SwarmRuntimeV1
from omega_engine_woland.stage.application.scheduler import finish_bout
from omega_engine_woland.stage.domain import (
    SwarmProfileV1,
    WorkPacketV1,
)

from ..domain.bout_journal import (
    BOUT_STARTED,
    BOUT_TERMINAL,
    TERMINAL_COMPLETED,
    TERMINAL_INTERRUPTED,
    TERMINAL_REFUSED,
    TERMINAL_UNEXPECTED_EXCEPTION,
    BoutJournalEntryV1,
    BoutJournalPort,
)
from ..domain.evidence import ObstructionMeasurementV1, canonical_rational, parse_exact_rational
from ..domain.graph_ports import GraphExecutionPort, GraphRunReferenceV1
from ..domain.graph_task import GraphTaskV1
from ..domain.instruction_ingress import (
    InstructionIngressReceiptV1,
    instruction_request_digest,
)
from ..domain.models import (
    WolandBoutOutcomeV1,
    WolandBoutReceiptV1,
    WolandBoutRequestV1,
)
from ..domain.ports import (
    CandidateCheckerPort,
    CochainScoringPort,
    InstructionIngressPort,
    LearningCompletionPort,
    NativeBoutExecutionPort,
    NullCochainScoringAdapter,
)
from ..domain.specialization import SwarmTypeV1
from ..render.render_novella import render_7act_novella
from .act_helpers import (
    execute_act1_carrier_framing,
    execute_act2_obstruction_identification,
    execute_act3_candidate_proposal_generation,
    execute_act3_epistemic_sieve,
    execute_act4_gauge_break,
    execute_act4_sandbox_verification,
    execute_act5_independent_witness,
    execute_act6_residual_ledger,
    execute_act7_authorization_gate,
    execute_act7_crystallization,
    execute_candidate_checks,
)
from .anti_skill_predispatch import require_candidate_clear, require_pre_dispatch_clear
from .cemetery_regression import AdmittedAntibodyReader
from .governance_dispatch import (
    resolve_governance_bundle,
    verify_governance_bundle,
)
from .persistence import (
    ddc_trace_digest,
    persist_bout_run_folder,
    run_directory_name,
)
from .persistence import (
    reported_receipt_id as content_addressed_receipt_id,
)
from .seat_custody import RecordingSeatPort

_LOCUS = "omega_engine_woland.use_cases.bout_service"


def _host_must_accept(
    rt: SwarmRuntimeV1, request_body: dict[str, Any]
) -> Result[None, Refusal]:
    """Keep the host Result. Only an Ok body whose status is ACCEPTED continues."""
    if rt.host is None:
        return Err(
            Refusal(
                "HOST_PORT_MISSING",
                "no HostPortV1 is bound",
                _LOCUS,
            )
        )
    host_result = rt.host.execute_host_request(
        json.dumps(request_body, sort_keys=True).encode("utf-8")
    )
    if isinstance(host_result, Err):
        return host_result
    body_bytes = getattr(host_result, "value", None)
    if type(body_bytes) is not bytes:
        return Err(Refusal("HOST_REQUEST_REFUSED", "host body was not bytes", _LOCUS))
    try:
        parsed = json.loads(body_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return Err(Refusal("HOST_REQUEST_REFUSED", "host body was not JSON", _LOCUS))
    status = parsed.get("status") if type(parsed) is dict else None
    if status != "ACCEPTED":
        return Err(
            Refusal("HOST_REQUEST_REFUSED", "host status is not ACCEPTED", _LOCUS)
        )
    return Ok(None)
REFUSAL_BUNDLE_SCHEMA = "omega.woland.refusal-bundle.v1"

IntelligenceRootResolver = Callable[[], Result[Path, Refusal]]


def _digest(data: str | bytes) -> str:
    """Produce a prefixed SHA-256 hex digest from string or bytes."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _carrier_state_digest(network: Any, cochain: Mapping[Any, Any]) -> str:
    """Bind the active carrier and exact cochain, including transported lift data."""
    data = {
        "nodes": list(network.nodes),
        "edges": [list(edge) for edge in network.edges],
        "faces": [list(face) for face in network.faces],
        "tetrahedra": [list(cell) for cell in network.tetrahedra],
        "four_simplices": [list(cell) for cell in network.four_simplices],
        "cochains": [
            [list(edge), canonical_rational(parse_exact_rational(cochain.get(edge, 0)))]
            for edge in network.edges
        ],
    }
    return _digest(json.dumps(data, sort_keys=True, separators=(",", ":")))


def _collect_dda_steps(emitters: Any) -> list[Any]:
    """Safely extract recorded DDC/DDA steps from the emitter suite.

    The ``recorded_steps`` attribute lives on the concrete
    ``DiscreteDeformationCalculusDdcSink`` / ``DiscreteDeformationAlgebraDdaSink`` adapter,
    not on the protocol. This helper encapsulates duck-typed access so callers
    don't need a three-level null-guard chain.
    """
    sink = getattr(emitters, "ddc", None) or getattr(emitters, "dda", None) if emitters else None
    if sink and hasattr(sink, "recorded_steps"):
        return list(sink.recorded_steps)
    return []


_collect_ddc_steps = _collect_dda_steps


def _regge_spacetime_declared(carrier_ctx: Mapping[str, Any] | None) -> bool:
    return bool(carrier_ctx and carrier_ctx.get("regge_spacetime"))


def _higher_complex_declared(network: Any, carrier_ctx: Mapping[str, Any] | None) -> bool:
    return bool(
        getattr(network, "tetrahedra", ())
        or getattr(network, "four_simplices", ())
        or _regge_spacetime_declared(carrier_ctx)
    )


def _capture_regge_deficits(
    scoring_adapter: Any,
    network: Any,
    cochain: Any,
    carrier_ctx: Mapping[str, Any] | None,
) -> Result[Mapping[str, Any], Refusal] | None:
    """Score a declared higher complex. A failure is a refusal, not a zero deficit."""
    regge_declared = _regge_spacetime_declared(carrier_ctx)
    if not _higher_complex_declared(network, carrier_ctx):
        return None
    if regge_declared and not getattr(network, "tetrahedra", ()):
        # An empty complex "converges" trivially; a Regge declaration without
        # tetrahedra is therefore refused, never measured as closed.
        return Err(
            Refusal(
                code="REGGE_DEFICIT_UNAVAILABLE",
                message="regge_spacetime is declared but the carrier has no tetrahedra",
                locus=_LOCUS,
            )
        )
    if scoring_adapter is None or not hasattr(scoring_adapter, "compute_regge_spacetime_deficits"):
        return Err(
            Refusal(
                code="REGGE_DEFICIT_UNAVAILABLE",
                message="a higher complex is declared but the scorer cannot measure Regge deficits",
                locus=_LOCUS,
            )
        )
    try:
        info = scoring_adapter.compute_regge_spacetime_deficits(network, cochain)
    except Exception as exc:
        return Err(
            Refusal(
                code="REGGE_DEFICIT_UNAVAILABLE",
                message=f"Regge deficit computation failed on a declared complex: {exc}",
                locus=_LOCUS,
            )
        )
    if not isinstance(info, Mapping):
        return Err(
            Refusal(
                code="REGGE_DEFICIT_UNAVAILABLE",
                message="Regge deficit computation returned no deficit map",
                locus=_LOCUS,
            )
        )
    return Ok(info)


def _lift_lowered_obstruction(
    before: ObstructionMeasurementV1, after: ObstructionMeasurementV1
) -> bool:
    """True when a lifted carrier measures lower than the carrier it was lifted from.

    A transported cochain cannot lower Phi1 or Gamma2, so this can only happen
    if a lift or a scorer replaced data. It is refused, never accepted.
    """
    if not (before.is_measured and after.is_measured):
        return False
    return bool(after.phi1 < before.phi1 or after.gamma2 < before.gamma2)


def _resolve_output_dir(
    rt: SwarmRuntimeV1,
    output_dir: Path | str | None,
    repo_root: Path | str | None,
) -> Result[Path, Refusal]:
    if output_dir:
        return Ok(Path(output_dir))
    if rt.operational_output_dir:
        return Ok(Path(rt.operational_output_dir))
    if repo_root:
        return Ok(Path(repo_root) / canonical_intelligence_route("_intelligence/_woland"))
    return Err(
        Refusal(
            code="WOLAND_OUTPUT_ROOT_UNRESOLVED",
            message=(
                "no output_dir, runtime output directory or repository root was given; "
                "refusing to write the run folder into the working directory"
            ),
            locus=_LOCUS,
        )
    )


def execute_7act_woland_bout(
    profile: SwarmProfileV1,
    rt: SwarmRuntimeV1,
    packet: WorkPacketV1,
    *,
    carrier_context: Mapping[str, Any] | None = None,
    ablation_flags: Mapping[str, bool] | None = None,
    repo_root: Path | str | None = None,
    output_dir: Path | str | None = None,
    cochain_adapter: CochainScoringPort | None = None,
    candidate_checker: CandidateCheckerPort | None = None,
    fixture_seats: bool = True,
    learning_guidance: str = "",
    journal: BoutJournalPort | None = None,
    admitted_antibody_reader: AdmittedAntibodyReader | None = None,
    anti_skill_gate: AntiSkillGatePort | None = None,
    anti_skill_request: WolandBoutRequestV1 | None = None,
    dispatch_decision: AntiSkillDecisionV1 | None = None,
    native_support: NativeOperationPort,
) -> Result[WolandBoutReceiptV1, Refusal]:
    """Execute the complete 7-Act Woland Swarm bout.

    ``fixture_seats`` defaults to True (fail closed): a caller must declare
    live, non-fixture seats with ``fixture_seats=False`` before a bout can be
    AUTHORIZED. Canned fixture seats reach ``FIXTURE_ONLY`` at most.

    Once any seat turn has run, a refusal never loses custody: the prompts,
    raw replies, the refusal and the act reached are persisted as a refusal
    bundle (a new folder, never an overwrite), and the returned refusal names
    it in its ``refusal_bundle`` detail.

    Args:
        profile: The loaded Woland swarm profile.
        rt: A fully-composed SwarmRuntimeV1.
        packet: The work packet describing the bout objective.
        carrier_context: Optional simplicial complex nodes, edges, faces, and cochains.
        ablation_flags: Optional ablation switches for scientific experiments.
        repo_root: Optional repository root for output path resolution.
        output_dir: Optional explicit output directory (overrides repo_root).
        cochain_adapter: Scorer for the carrier; without one every carrier is NOT_MEASURED.
        candidate_checker: The challenge checker; without one every candidate is NOT_MEASURED.
        anti_skill_gate: Optional bound metadata gate for candidate stages.
        anti_skill_request: Exact request screened by that gate; neither grants admission.
        dispatch_decision: Prior CLEAR snapshot, when screening a non-fixture service request.
    """

    def _invalid_bout_args() -> Result[None, Refusal] | None:
        if profile is None or rt is None or packet is None:
            return Err(
                Refusal(
                    "INVALID_BOUT_ARGS",
                    "Missing runtime or work packet",
                    "omega_engine_woland",
                )
            )
        if rt.scheduler is None:
            return Err(
                Refusal(
                    code="WOLAND_SCHEDULER_MISSING",
                    message="A scheduler is required to execute a Woland bout",
                    locus=_LOCUS,
                )
            )
        if rt.seat_port is None:
            return Err(
                Refusal(
                    code="EXECUTION_UNAVAILABLE",
                    message="No seat executor is configured; no seat turn can run",
                    locus=_LOCUS,
                )
            )
        return None

    def _journal_refused_start(bout_id: str) -> Result[None, Refusal] | None:
        if journal is None:
            return None
        started = journal.append(
            BoutJournalEntryV1(
                bout_id=bout_id,
                kind=BOUT_STARTED,
                task_key=packet.task_key,
                detail=(
                    ("fixture_seats", str(fixture_seats)),
                    ("objective_sha256", _digest(packet.objective)),
                ),
            )
        )
        if started.is_err:
            # No write-ahead record means no bout: nothing has been called or charged.
            return Err(
                Refusal(
                    code="BOUT_JOURNAL_UNAVAILABLE",
                    message=f"the bout journal refused BOUT_STARTED: {started.unwrap_err().message}",
                    locus=_LOCUS,
                )
            )
        return None

    def _with_refusal_bundle(result, recorder, runtime, offset, progress):
        if result.is_err and recorder.turns:
            return Err(
                _persist_refusal_bundle(
                    target_output_dir,
                    packet,
                    result.unwrap_err(),
                    progress["act"],
                    recorder.turns,
                    _collect_dda_steps(runtime.emitters)[offset:],
                    native_support=native_support,
                )
            )
        return result

    def _terminal_close_detail(final, terminal_status, progress):
        if final.is_err:
            if terminal_status == TERMINAL_COMPLETED:
                terminal_status = TERMINAL_REFUSED
            refusal = final.unwrap_err()
            detail = (
                ("refusal_code", refusal.code),
                ("act_reached", progress["act"]),
                ("refusal_bundle", str(dict(refusal.details).get("refusal_bundle", ""))),
            )
        else:
            detail = (("act_reached", progress["act"]),)
        return terminal_status, detail

    def _attach_journal_residuals(final, closing, recorder):
        residual_codes = tuple(code.code for code in recorder.journal_residuals)
        if final.is_err and (closing is not None or residual_codes):
            refusal = final.unwrap_err()
            extra = tuple(("journal_residual", code) for code in residual_codes)
            if closing is not None:
                extra += (("journal_terminal_error", closing.code),)
            return Err(
                Refusal(
                    code=refusal.code,
                    message=refusal.message,
                    locus=refusal.locus,
                    details=refusal.details + extra,
                )
            )
        return final

    invalid = _invalid_bout_args()
    if invalid is not None:
        return invalid
    target = _resolve_output_dir(rt, output_dir, repo_root)
    if target.is_err:
        return Err(target.unwrap_err())
    target_output_dir = target.unwrap()

    scoring_adapter: CochainScoringPort = cochain_adapter or NullCochainScoringAdapter()
    bout_id = f"{packet.task_key}:{uuid.uuid4().hex[:12]}"
    journal_error = _journal_refused_start(bout_id)
    if journal_error is not None:
        return journal_error
    recorder = RecordingSeatPort(
        rt.seat_port,
        learning_guidance=learning_guidance,
        journal=journal,
        bout_id=bout_id,
        task_key=packet.task_key,
    )
    rt = replace(rt, seat_port=recorder)
    dda_step_offset = len(_collect_dda_steps(rt.emitters))
    progress = {"act": "SCHEDULER_START"}
    terminal_status = TERMINAL_COMPLETED
    try:
        result = _run_acts(
            rt,
            packet,
            recorder=recorder,
            progress=progress,
            target_output_dir=target_output_dir,
            repo_root=repo_root,
            dda_step_offset=dda_step_offset,
            scoring_adapter=scoring_adapter,
            candidate_checker=candidate_checker,
            carrier_context=carrier_context,
            ablation_flags=ablation_flags,
            fixture_seats=fixture_seats,
            admitted_antibody_reader=admitted_antibody_reader,
            anti_skill_gate=anti_skill_gate,
            anti_skill_request=anti_skill_request,
            dispatch_decision=dispatch_decision,
            native_support=native_support,
        )
    except Exception as exc:
        # The boundary of the bout: an unexpected exception becomes a typed
        # refusal, and the turns already run still go to the refusal bundle.
        terminal_status = TERMINAL_UNEXPECTED_EXCEPTION
        result = Err(
            Refusal(
                code="WOLAND_BOUT_UNEXPECTED_EXCEPTION",
                message=f"{type(exc).__name__}: {exc}",
                locus=_LOCUS,
                details=(("act_reached", progress["act"]),),
            )
        )
    except BaseException as exc:
        _close_journal(
            journal,
            bout_id,
            packet.task_key,
            TERMINAL_INTERRUPTED,
            (("exception", type(exc).__name__), ("act_reached", progress["act"])),
        )
        raise
    final = _with_refusal_bundle(result, recorder, rt, dda_step_offset, progress)
    terminal_status, close_detail = _terminal_close_detail(final, terminal_status, progress)
    closing = _close_journal(journal, bout_id, packet.task_key, terminal_status, close_detail)
    return _attach_journal_residuals(final, closing, recorder)


def _close_journal(
    journal: BoutJournalPort | None,
    bout_id: str,
    task_key: str,
    terminal_status: str,
    detail: tuple[tuple[str, str], ...],
) -> Refusal | None:
    """Write the one terminal record of a bout; return the typed refusal if the journal refused."""
    if journal is None:
        return None
    appended = journal.append(
        BoutJournalEntryV1(
            bout_id=bout_id,
            kind=BOUT_TERMINAL,
            task_key=task_key,
            detail=(("terminal_status", terminal_status), *detail),
        )
    )
    return appended.unwrap_err() if appended.is_err else None


def _persist_refusal_bundle(
    target_output_dir: Path,
    packet: WorkPacketV1,
    refusal: Refusal,
    act_reached: str,
    seat_turns: list[dict[str, Any]],
    dda_steps: list[Any],
    *,
    native_support: NativeOperationPort,
) -> Refusal:
    """Persist what a refused bout had already produced; return the refusal naming it.

    The bundle goes to a new, content-addressed sibling folder
    ``<run>--refused-<digest>`` so an existing run folder is never touched.
    """
    record = {
        "act_reached": act_reached,
        "refusal": refusal.to_dict(),
        "seat_turns": list(seat_turns),
    }
    tag = hashlib.sha256(
        json.dumps(record, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()[:12]
    novella_md = (
        "# Refused bout\n\n"
        f"The bout `{packet.task_key}` was refused at `{act_reached}` with "
        f"`{refusal.code}`: {refusal.message}\n\n"
        f"{len(seat_turns)} seat turn(s) had run; every prompt and raw reply is in "
        "`summary.json` under `seat_turns`. Nothing here is a verdict.\n"
    )
    summary: dict[str, Any] = {
        **record,
        "authority_effect": "None",
        "is_authorized": False,
        "objective": packet.objective,
        "selected_candidate_id": "",
        "status": "REFUSED",
        "task_key": packet.task_key,
        "terminal_status": "REFUSED",
    }
    receipt_id = content_addressed_receipt_id(novella_md, dda_steps, summary, native_support=native_support)
    summary["receipt_id"] = receipt_id
    receipt = {
        "authority_effect": "None",
        "receipt_id": receipt_id,
        "refusal_code": refusal.code,
        "schema": REFUSAL_BUNDLE_SCHEMA,
        "selected_candidate_id": "",
        "status": "REFUSED",
        "task_key": packet.task_key,
    }
    folder_key = f"{run_directory_name(packet.task_key, native_support=native_support)}--refused-{tag}"
    persisted = persist_bout_run_folder(
        target_output_dir, folder_key, receipt, novella_md, dda_steps, summary
    , native_support=native_support)
    detail = (
        ("refusal_bundle", str(persisted.unwrap()))
        if persisted.is_ok
        else (
            "refusal_bundle_error",
            f"{persisted.unwrap_err().code}: {persisted.unwrap_err().message}",
        )
    )
    details = tuple(pair for pair in refusal.details if pair[0] != detail[0]) + (detail,)
    return Refusal(code=refusal.code, message=refusal.message, locus=refusal.locus, details=details)


def _refuse_unbound_candidate_screen(ctx) -> Result[None, Refusal] | None:
    gate = ctx.anti_skill_gate
    request = ctx.anti_skill_request
    if (gate is None) != (request is None) or (
        request is not None
        and (request.task_key != ctx.run_key or request.objective != ctx.objective)
    ):
        return Err(Refusal(
            "ANTI_SKILL_CANDIDATE_BINDING_INVALID",
            "candidate screening requires a gate bound to this exact task and objective",
            _LOCUS,
        ))
    return None


def _start_scheduled_bout(ctx) -> Result[None, Refusal] | None:
    try:
        ctx.state = ctx.rt.scheduler.start(ctx.run_key, ctx.packet)
    except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
        return Err(
            Refusal(
                code="WOLAND_SCHEDULER_START_REFUSED",
                message=str(exc),
                locus=_LOCUS,
            )
        )
    ctx.pkt_id = getattr(ctx.packet, "packet_id", None) or _digest(ctx.packet.task_key)
    ctx.carrier_ctx = ctx.carrier_context or getattr(ctx.packet, "carrier_context", None)
    ctx.abl_flags = ctx.ablation_flags or getattr(ctx.packet, "ablation_flags", None)
    ctx.now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    ctx.acts_narrative = []
    return None


def _act_host_start(ctx):
    accepted = _host_must_accept(
        ctx.rt,
        {
            "action": "bout_start",
            "task_key": ctx.run_key,
            "objective": ctx.objective,
            "authority_effect": "None",
        },
    )
    if isinstance(accepted, Err):
        return accepted
    return None


def _act_i_framing(ctx):
    ctx.progress["act"] = "ACT_I"
    act1_res = execute_act1_carrier_framing(
        ctx.rt,
        ctx.run_key,
        ctx.objective,
        carrier_context=ctx.carrier_ctx,
        now_utc=ctx.now_utc,
        native_support=ctx.native_support,
    )
    if act1_res.is_err:
        return Err(act1_res.unwrap_err())
    (
        ctx.carrier_network,
        ctx.initial_cochain,
        ctx.active_antibodies,
        ctx.prompt_sbe,
        ctx.act1_narrative,
    ) = act1_res.unwrap()
    ctx.acts_narrative.append(ctx.act1_narrative)
    return None


def _take_regge(ctx, network, cochain):
    regge_capture = _capture_regge_deficits(
        ctx.scoring_adapter, network, cochain, ctx.carrier_ctx
    )
    if regge_capture is None:
        return None
    if regge_capture.is_err:
        return Err(regge_capture.unwrap_err())
    regge_info = regge_capture.unwrap()
    ctx.delta2_defect = regge_info.get("xi3")
    ctx.delta3_defect = regge_info.get("xi4")
    ctx.regge_converged = regge_info.get("regge_converged")
    return None


def _act_ii_obstruction(ctx):
    ctx.progress["act"] = "ACT_II"
    act2_res = execute_act2_obstruction_identification(
        ctx.carrier_network,
        ctx.initial_cochain,
        ablation_flags=ctx.abl_flags,
        cochain_adapter=ctx.scoring_adapter,
        rt=ctx.rt,
        run_key=ctx.run_key,
        now_utc=ctx.now_utc,
    )
    if act2_res.is_err:
        return Err(act2_res.unwrap_err())
    ctx.pre_lift_measurement, act2_narrative = act2_res.unwrap()
    ctx.measurement = ctx.pre_lift_measurement
    ctx.acts_narrative.append(act2_narrative)
    ctx.delta2_defect = None
    ctx.delta3_defect = None
    ctx.regge_converged = None
    return _take_regge(ctx, ctx.carrier_network, ctx.initial_cochain)


def _candidate_payloads(candidates_data):
    return {
        item["candidate_id"]: item["content"].encode("utf-8")
        for item in candidates_data
        if item.get("candidate_id")
    }


def _screen_candidate_payloads(ctx, stage_name, pairs):
    if ctx.anti_skill_gate is None or ctx.anti_skill_request is None:
        return None
    ctx.progress["act"] = stage_name
    for candidate_id, candidate_bytes in pairs:
        screened = require_candidate_clear(
            ctx.anti_skill_gate,
            "omega_engine_woland.bout_service",
            ctx.anti_skill_request,
            stage_name,
            candidate_id,
            candidate_bytes,
            ctx.snapshot,
        )
        if isinstance(screened, Err):
            return screened
        ctx.snapshot = screened.value
        ctx.anti_skill_decisions.append(screened.value)
    return None


def _act_iii_candidates(ctx):
    ctx.progress["act"] = "ACT_III"
    act3_res = execute_act3_candidate_proposal_generation(
        ctx.rt, ctx.pkt_id, ctx.run_key, ctx.objective, now_utc=ctx.now_utc
    )
    if act3_res.is_err:
        return Err(act3_res.unwrap_err())
    ctx.candidates, ctx.candidates_data, ctx.dead_candidates, act3_narrative = act3_res.unwrap()
    ctx.acts_narrative.append(act3_narrative)
    ctx.candidate_payloads = _candidate_payloads(ctx.candidates_data)
    return _screen_candidate_payloads(
        ctx, "POST_PRODUCTION", ctx.candidate_payloads.items()
    )


def _lift_replaced_cochain(before, after):
    return Err(
        Refusal(
            code="WOLAND_LIFT_LOWERED_OBSTRUCTION",
            message=(
                "the lifted carrier measured below the carrier it was lifted from "
                f"(Phi1 {before.phi1_text()} -> {after.phi1_text()}, "
                f"Gamma2 {before.gamma2_text()} -> {after.gamma2_text()}); "
                "a lift must transport the cochain, not replace it"
            ),
            locus=_LOCUS,
        )
    )


def _measure_admissible_lift(ctx):
    carrier_ctx = ctx.carrier_ctx
    is_admissible = carrier_ctx.get("ground_truth_admissible", True) if carrier_ctx else True
    if not (ctx.gauge_break_triggered and is_admissible):
        ctx.post_lift_measurement = None
        return None
    lifted_res = execute_act2_obstruction_identification(
        ctx.lifted_network,
        ctx.updated_cochain,
        ablation_flags=ctx.abl_flags,
        cochain_adapter=ctx.scoring_adapter,
    )
    if lifted_res.is_err:
        return Err(lifted_res.unwrap_err())
    post_lift_measurement, _ignored = lifted_res.unwrap()
    ctx.post_lift_measurement = post_lift_measurement
    if _lift_lowered_obstruction(ctx.pre_lift_measurement, post_lift_measurement):
        return _lift_replaced_cochain(ctx.pre_lift_measurement, post_lift_measurement)
    ctx.measurement = post_lift_measurement
    return _take_regge(ctx, ctx.lifted_network, ctx.updated_cochain)


def _act_iv_gauge(ctx):
    ctx.progress["act"] = "ACT_IV"
    act4_res = execute_act4_gauge_break(
        ctx.rt,
        ctx.carrier_network,
        ctx.initial_cochain,
        ctx.candidates,
        ctx.candidates_data,
        ctx.measurement,
        ablation_flags=ctx.abl_flags,
        run_key=ctx.run_key,
        now_utc=ctx.now_utc,
    )
    if act4_res.is_err:
        return Err(act4_res.unwrap_err())
    (
        ctx.gauge_break_triggered,
        ctx.lifted_network,
        ctx.updated_cochain,
        ctx.asd_telemetry,
        act4_narrative,
    ) = act4_res.unwrap()
    ctx.acts_narrative.append(act4_narrative)
    return _measure_admissible_lift(ctx)


def _act_sandbox(ctx):
    ctx.progress["act"] = "SANDBOX"
    ctx.sieve_sbe, sieve_narrative = execute_act3_epistemic_sieve(
        ctx.objective, ctx.candidates, ctx.candidates_data
    )
    ctx.acts_narrative.append(sieve_narrative)
    sandbox_res = execute_act4_sandbox_verification(
        ctx.rt,
        candidates=ctx.candidates,
        candidate_payloads=ctx.candidate_payloads,
        ablation_flags=ctx.abl_flags,
        repo_root=ctx.repo_root,
        admitted_antibody_reader=ctx.admitted_antibody_reader,
    )
    if sandbox_res.is_err:
        return Err(sandbox_res.unwrap_err())
    ctx.sandbox_disposition, sandbox_narrative = sandbox_res.unwrap()
    ctx.acts_narrative.append(sandbox_narrative)
    return None


def _act_v_witness(ctx):
    ctx.progress["act"] = "ACT_V"
    act5_res = execute_act5_independent_witness(
        ctx.rt,
        ctx.run_key,
        ctx.objective,
        ctx.lifted_network,
        ctx.candidates,
        ctx.dead_candidates,
        candidate_payloads=ctx.candidate_payloads,
        ablation_flags=ctx.abl_flags,
        now_utc=ctx.now_utc,
        native_support=ctx.native_support,
    )
    if act5_res.is_err:
        return Err(act5_res.unwrap_err())
    (
        ctx.surviving_candidates,
        ctx.accumulated_dead,
        ctx.round_count,
        ctx.critiques,
        ctx.critiques_data,
        ctx.critique_verdicts,
        act5_narrative,
    ) = act5_res.unwrap()
    ctx.acts_narrative.append(act5_narrative)
    return None


def _act_checker(ctx):
    ctx.progress["act"] = "CHECKER"
    checks_res = execute_candidate_checks(
        ctx.candidate_checker,
        ctx.run_key,
        ctx.objective,
        ctx.surviving_candidates,
        ctx.candidate_payloads,
        ctx.carrier_ctx,
        rt=ctx.rt,
        measurement=ctx.measurement,
        carrier_state_hash=_carrier_state_digest(ctx.lifted_network, ctx.updated_cochain),
        now_utc=ctx.now_utc,
    )
    if checks_res.is_err:
        return Err(checks_res.unwrap_err())
    ctx.candidate_checks = checks_res.unwrap()
    return None


def _surviving_payload_pairs(ctx):
    for candidate in ctx.surviving_candidates:
        candidate_id = candidate.candidate_id
        yield candidate_id, ctx.candidate_payloads[candidate_id]


def _act_pre_selection(ctx):
    return _screen_candidate_payloads(ctx, "PRE_SELECTION", _surviving_payload_pairs(ctx))


def _act_vi_ledger(ctx):
    ctx.progress["act"] = "ACT_VI"
    act6_res = execute_act6_residual_ledger(
        ctx.rt,
        ctx.surviving_candidates,
        ctx.accumulated_dead,
        ctx.critiques,
        ctx.critique_verdicts,
        ctx.measurement,
        ablation_flags=ctx.abl_flags,
        run_key=ctx.run_key,
        now_utc=ctx.now_utc,
    )
    if act6_res.is_err:
        return Err(act6_res.unwrap_err())
    ctx.residual_ledger, ctx.antibodies_recorded, act6_narrative = act6_res.unwrap()
    ctx.acts_narrative.append(act6_narrative)
    return None


def _act_vii_gate(ctx):
    ctx.progress["act"] = "ACT_VII"
    act7_res = execute_act7_authorization_gate(
        ctx.rt,
        ctx.run_key,
        ctx.surviving_candidates,
        ctx.critiques,
        ctx.residual_ledger,
        ctx.measurement,
        candidate_checks=ctx.candidate_checks,
        carrier_context=ctx.carrier_ctx,
        ablation_flags=ctx.abl_flags,
        delta2_defect=ctx.delta2_defect,
        delta3_defect=ctx.delta3_defect,
        regge_converged=ctx.regge_converged,
        carrier_status=ctx.act1_narrative["carrier_status"],
        critique_verdicts=ctx.critique_verdicts,
        fixture_seats=ctx.fixture_seats,
        now_utc=ctx.now_utc,
    )
    if act7_res.is_err:
        return Err(act7_res.unwrap_err())
    (
        ctx.auth_status,
        ctx.selected_id,
        ctx.verdict_proposal,
        ctx.is_authorized,
        ctx.act7_narrative,
    ) = act7_res.unwrap()
    ctx.acts_narrative.append(ctx.act7_narrative)
    return None


def _terminal_verdict_name(ctx) -> str:
    if ctx.rt.request_external_admission and ctx.verdict_proposal.disposition == "SELECT":
        return "PROPOSED_FOR_EXTERNAL_ADMISSION"
    return "COMPOSTED"


def _act_crystallize(ctx):
    ctx.terminal_verdict = _terminal_verdict_name(ctx)
    cryst_res = execute_act7_crystallization(
        ctx.rt, ctx.run_key, ctx.terminal_verdict, ctx.accumulated_dead
    )
    if cryst_res.is_err:
        return Err(cryst_res.unwrap_err())
    ctx.consecration_state, cryst_narrative = cryst_res.unwrap()
    ctx.acts_narrative.append(cryst_narrative)
    return None


def _act_finish_schedule(ctx):
    finished = finish_bout(ctx.rt.scheduler, ctx.state, ctx.packet)
    if finished.is_err:
        return finished
    ctx.state = finished.unwrap()
    return None


def _joint_kernel_status(measurement) -> str:
    if measurement.is_exact_joint_zero():
        return "ZERO_ON_DECLARED_CARRIER"
    if measurement.is_measured:
        return "OPEN_RESIDUAL"
    return "NOT_MEASURED"


def _letter_tape(steps) -> str:
    return "".join(step.letter.value for step in steps if hasattr(step, "letter"))


def _objective_mentions(objective: str, run_key: str, tokens: tuple[str, ...]) -> bool:
    return any(token in objective.lower() or token in run_key.lower() for token in tokens)


def _act_governance(ctx):
    narrative = ctx.act7_narrative
    ctx.blockers = list(narrative.get("authorization_blockers", []))
    ctx.checker_verdict = narrative.get("checker_verdict", "NOT_MEASURED")
    ctx.checker_receipt_sha256 = narrative.get("checker_receipt_sha256")
    ctx.authorization_evidence = narrative.get("authorization_evidence")
    ctx.dda_steps_to_write = _collect_dda_steps(ctx.rt.emitters)[ctx.dda_step_offset:]
    ctx.ddc_hash = ddc_trace_digest(ctx.dda_steps_to_write, native_support=ctx.native_support)
    ctx.joint_kernel_status = _joint_kernel_status(ctx.measurement)
    ctx.carrier_degree = 1 if ctx.act1_narrative.get("carrier_status") == "DECLARED" else None
    ctx.letter_tape = _letter_tape(ctx.dda_steps_to_write)
    ctx.governance_bundle = resolve_governance_bundle(
        repo_root=Path(__file__).resolve().parents[2],
        task_properties={
            "objective": ctx.objective,
            "task_key": ctx.run_key,
            "letter_tape": ctx.letter_tape,
            "ddc_tape_used": bool(ctx.letter_tape),
            "coda_surfaces_claimed": _objective_mentions(
                ctx.objective, ctx.run_key, ("coda", "foc", "mur", "cs_q", "gtla")
            ),
            "python_code_changed": _objective_mentions(
                ctx.objective, ctx.run_key, ("code", "clean_arch", "refactor")
            ),
        },
    )
    gov_verif = verify_governance_bundle(ctx.governance_bundle)
    if gov_verif.is_err:
        return Err(gov_verif.unwrap_err())
    ctx.evidence_receipts = dict(narrative.get("evidence_receipts", {}))
    governance_bytes = json.dumps(
        ctx.governance_bundle, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    ctx.governance_digest = "sha256:" + hashlib.sha256(governance_bytes).hexdigest()
    ctx.evidence_receipts[ctx.governance_digest] = ctx.governance_bundle
    return None


def _compilation_gate_rows(ctx):
    rows = []
    checks = ctx.candidate_checks
    for item in ctx.candidates_data:
        candidate_id = item.get("candidate_id")
        if candidate_id in checks:
            status = checks[candidate_id].verdict.value
        else:
            status = "NOT_RUN"
        rows.append(
            {
                "capture_id": item.get("candidate_request_id", item["candidate_id"]),
                "candidate_id": item["candidate_id"],
                "status": status,
                "l1": ctx.measurement.phi1_text() or "NOT_MEASURED",
            }
        )
    return rows


def _act_novella(ctx):
    ctx.progress["act"] = "NOVELLA"
    proposal = ctx.verdict_proposal
    ctx.novella_md = render_7act_novella(
        run_key=ctx.run_key,
        objective=ctx.objective,
        prompt_sbe=ctx.prompt_sbe,
        antibodies_loaded=[antibody.to_dict() for antibody in ctx.active_antibodies],
        candidates_data=ctx.candidates_data,
        compilation_gate=_compilation_gate_rows(ctx),
        critiques_data=ctx.critiques_data,
        sieve_sbe=ctx.sieve_sbe,
        woland_sieve_text=(
            "Woland records a candidate-ranking proposal. The synthetic SBE "
            "diagnostic is not proof, verification, or authority to promote."
        ),
        margarita_checks=[
            {
                "check": "Seat-reported disposition",
                "result": f"{ctx.sandbox_disposition}; no independent safety receipt supplied",
            }
        ],
        margarita_overall="NOT_INDEPENDENTLY_VERIFIED",
        master_assessment={
            "status": ctx.auth_status,
            "authorization_evidence": ctx.authorization_evidence,
            "selected_candidate_id": proposal.selected_candidate_id,
            "frontier_candidate_ids": list(proposal.frontier_candidate_ids),
            "disposition": proposal.disposition,
            "authorization_blockers": ctx.blockers,
            "checker_verdict": ctx.checker_verdict,
            "checker_receipt_sha256": ctx.checker_receipt_sha256,
            "carrier_measurement": ctx.measurement.to_dict(),
            "evidence_refs": [*proposal.evidence_refs, ctx.governance_digest],
            "nonclaims": list(proposal.nonclaims),
            "authority_effect": proposal.authority_effect,
        },
        verdict=ctx.terminal_verdict,
        intern_checks=[
            f"{ctx.antibodies_recorded} antibody update(s) completed without a reported sink error; no independent integrity audit was run."
        ],
        mined_antibodies=[],
        consecration=ctx.consecration_state,
        now_utc=ctx.now_utc,
    )
    return None


def _act_emit_uns(ctx):
    if not ctx.rt.emitters:
        return None
    uns_event, uns_bytes = build_intelligence_event(
        ie_id=_digest(f"{ctx.run_key}:uns"),
        actor_id="actor_mythos_secretary",
        actor_kind="SWARM_CHRONICLER",
        event_kind="NARRATIVE",
        source_system="oeas.uns",
        session_id=ctx.run_key,
        payload=ctx.novella_md,
        terminal=True,
    )
    uns_emit_res = emit_event(uns_event, uns_bytes, ctx.rt.emitters)
    if uns_emit_res.is_err:
        return Err(uns_emit_res.unwrap_err())
    return None


def _summary_payload(ctx) -> dict[str, Any]:
    measurement = ctx.measurement
    proposal = ctx.verdict_proposal
    return {
        "anti_skill_decisions": [asdict(decision) for decision in ctx.anti_skill_decisions],
        "asd_telemetry": ctx.asd_telemetry,
        "authority_effect": "None",
        "authorization_blockers": ctx.blockers,
        "authorization_evidence": ctx.authorization_evidence,
        "candidate_checks": {
            cid: check.to_dict() for cid, check in sorted(ctx.candidate_checks.items())
        },
        "ddc_trace_hash": ctx.ddc_hash,
        "lggr_joint_kernel_status": ctx.joint_kernel_status,
        "carrier_degree": ctx.carrier_degree,
        "carrier_measurement": measurement.to_dict(),
        "carrier_status": ctx.act1_narrative.get("carrier_status"),
        "checker_receipt_sha256": ctx.checker_receipt_sha256,
        "checker_verdict": ctx.checker_verdict,
        "consecration_state": ctx.consecration_state,
        "critique_rounds": ctx.round_count,
        "critique_verdicts": dict(sorted(ctx.critique_verdicts.items())),
        "defect_count": measurement.defect_count,
        "disposition": proposal.disposition,
        "evidence_receipts": ctx.evidence_receipts,
        "governance_bundle": ctx.governance_bundle,
        "fixture_seats": ctx.fixture_seats is not False,
        "gamma2": measurement.gamma2_text(),
        "implicit_zero_edges": ctx.act1_narrative.get("implicit_zero_edges", 0),
        "is_authorized": ctx.is_authorized,
        "letter_tape": ctx.letter_tape,
        "measurement_status": measurement.status.value,
        "nonclaims": list(proposal.nonclaims),
        "objective": ctx.objective,
        "phi1": measurement.phi1_text(),
        "pre_lift_measurement": (
            ctx.pre_lift_measurement.to_dict() if ctx.post_lift_measurement is not None else None
        ),
        "residual_declared": ctx.residual_ledger.get("residual_declared", False)
        if ctx.residual_ledger
        else False,
        "seat_turns": list(ctx.recorder.turns),
        "selected_candidate_id": ctx.selected_id,
        "status": ctx.auth_status,
        "task_key": ctx.run_key,
        "terminal_status": ctx.state.terminal_status,
        "terminal_verdict": ctx.terminal_verdict,
    }


def _receipt_record(ctx, receipt_id: str) -> WolandBoutReceiptV1:
    measurement = ctx.measurement
    return WolandBoutReceiptV1(
        task_key=ctx.run_key,
        receipt_id=receipt_id,
        status=ctx.auth_status,
        selected_candidate_id=ctx.selected_id,
        novella_sha256="",
        ddc_sha256="",
        summary_sha256="",
        lean4_proof_hash=None,
        phi1=measurement.phi1_text(),
        gamma2=measurement.gamma2_text(),
        defect_count=measurement.defect_count,
        ablation_flags=dict(ctx.abl_flags) if ctx.abl_flags else {},
        authority_effect="None",
        final_state=ctx.state,
        selection_proposal=ctx.verdict_proposal,
        letter_tape=ctx.letter_tape,
        measurement_status=measurement.status.value,
        checker_receipt_sha256=ctx.checker_receipt_sha256,
        checker_verdict=ctx.checker_verdict,
        authorization_blockers=tuple(ctx.blockers),
        authorization_evidence=ctx.authorization_evidence,
        ddc_trace_hash=ctx.ddc_hash,
        lggr_joint_kernel_status=ctx.joint_kernel_status,
        carrier_degree=ctx.carrier_degree,
    )


def _act_persist(ctx):
    ctx.progress["act"] = "PERSIST"
    summary_data = _summary_payload(ctx)
    receipt_id = content_addressed_receipt_id(
        ctx.novella_md,
        ctx.dda_steps_to_write,
        summary_data,
        native_support=ctx.native_support,
    )
    summary_data["receipt_id"] = receipt_id
    ctx.receipt_id = receipt_id
    ctx.receipt = _receipt_record(ctx, receipt_id)
    persist_result = persist_bout_run_folder(
        ctx.target_output_dir,
        ctx.run_key,
        ctx.receipt,
        ctx.novella_md,
        ctx.dda_steps_to_write,
        summary_data,
        native_support=ctx.native_support,
    )
    if persist_result.is_err:
        return Err(persist_result.unwrap_err())
    return None


def _act_host_record(ctx):
    accepted = _host_must_accept(
        ctx.rt,
        {
            "action": "gate_authorization_record",
            "task_key": ctx.run_key,
            "receipt_id": ctx.receipt_id,
            "status": ctx.auth_status,
            "authority_effect": "None",
        },
    )
    if isinstance(accepted, Err):
        return accepted
    return None


_BOUT_ACTS = (
    _act_host_start,
    _act_i_framing,
    _act_ii_obstruction,
    _act_iii_candidates,
    _act_iv_gauge,
    _act_sandbox,
    _act_v_witness,
    _act_checker,
    _act_pre_selection,
    _act_vi_ledger,
    _act_vii_gate,
    _act_crystallize,
    _act_finish_schedule,
    _act_governance,
    _act_novella,
    _act_emit_uns,
    _act_persist,
    _act_host_record,
)


def _run_acts(
    rt: SwarmRuntimeV1,
    packet: WorkPacketV1,
    *,
    recorder: RecordingSeatPort,
    progress: dict[str, str],
    target_output_dir: Path,
    repo_root: Path | str | None,
    dda_step_offset: int,
    scoring_adapter: CochainScoringPort,
    candidate_checker: CandidateCheckerPort | None,
    carrier_context: Mapping[str, Any] | None,
    ablation_flags: Mapping[str, bool] | None,
    fixture_seats: bool,
    admitted_antibody_reader: AdmittedAntibodyReader | None,
    anti_skill_gate: AntiSkillGatePort | None,
    anti_skill_request: WolandBoutRequestV1 | None,
    dispatch_decision: AntiSkillDecisionV1 | None,
    native_support: NativeOperationPort,
) -> Result[WolandBoutReceiptV1, Refusal]:
    """The seven acts. ``progress['act']`` names the stage currently running."""
    ctx = SimpleNamespace(
        rt=rt,
        packet=packet,
        recorder=recorder,
        progress=progress,
        target_output_dir=target_output_dir,
        repo_root=repo_root,
        dda_step_offset=dda_step_offset,
        scoring_adapter=scoring_adapter,
        candidate_checker=candidate_checker,
        carrier_context=carrier_context,
        ablation_flags=ablation_flags,
        fixture_seats=fixture_seats,
        admitted_antibody_reader=admitted_antibody_reader,
        anti_skill_gate=anti_skill_gate,
        anti_skill_request=anti_skill_request,
        dispatch_decision=dispatch_decision,
        native_support=native_support,
        run_key=packet.task_key,
        objective=packet.objective,
        anti_skill_decisions=[],
        snapshot=dispatch_decision,
    )
    refused = _refuse_unbound_candidate_screen(ctx)
    if refused is not None:
        return refused
    started = _start_scheduled_bout(ctx)
    if isinstance(started, Err):
        return started
    for stage in _BOUT_ACTS:
        outcome = stage(ctx)
        if isinstance(outcome, Err):
            return outcome
    return Ok(ctx.receipt)

class WolandSwarmService:
    """Orchestrates Woland 7-Act Swarm Bouts from injected collaborators.

    ``runtime_factory`` builds the stage runtime; ``cochain_adapter`` measures
    the carrier; ``candidate_checker`` is the challenge checker;
    ``intelligence_root`` resolves where run folders go when no ``repo_root``
    is given. Use ``omega_engine_woland.runtime.build_woland_service`` for the
    production wiring.
    """

    def __init__(
        self,
        repo_root: Path | str | None = None,
        runtime_factory: Callable[..., SwarmRuntimeV1] | None = None,
        profile_loader: Callable[[], tuple[Any, ...]] | None = None,
        cochain_adapter: CochainScoringPort | None = None,
        candidate_checker: CandidateCheckerPort | None = None,
        intelligence_root: IntelligenceRootResolver | None = None,
        intelligence_path: Callable[[Path, str], Path] | None = None,
        learning_completion: LearningCompletionPort | None = None,
        intelligence_collection: IntelligenceCollectionPort | None = None,
        graph_execution: GraphExecutionPort | None = None,
        bout_journal: BoutJournalPort | None = None,
        native_execution: NativeBoutExecutionPort | None = None,
        instruction_ingress: InstructionIngressPort | None = None,
        require_instruction_ingress: bool = False,
        anti_skill_gate: AntiSkillGatePort | None = None,
        admitted_antibody_reader: AdmittedAntibodyReader | None = None,
        *,
        native_support: NativeOperationPort,
    ) -> None:
        self._native_support = native_support
        self.repo_root = Path(repo_root) if repo_root else None
        self.runtime_factory = runtime_factory
        self.profile_loader = profile_loader
        self.cochain_adapter = cochain_adapter
        self.candidate_checker = candidate_checker
        self.intelligence_root = intelligence_root
        # Standalone defaults are canonical; production also validates custody metadata.
        self.intelligence_path = intelligence_path or (
            lambda root, relative: root / canonical_intelligence_route(relative)
        )
        self.learning_completion = learning_completion
        self.intelligence_collection = intelligence_collection
        self.learning_residuals: list[Refusal] = []
        self.collection_residuals: list[Refusal] = []
        self.recovery_residuals: list[Refusal] = []
        self.journal_residuals: list[Refusal] = []
        self.graph_execution = graph_execution
        self.bout_journal = bout_journal
        self.native_execution = native_execution
        if type(require_instruction_ingress) is not bool:
            raise TypeError("require_instruction_ingress must be an exact bool")
        self.instruction_ingress = instruction_ingress
        self.require_instruction_ingress = require_instruction_ingress
        self.anti_skill_gate = anti_skill_gate
        self.admitted_antibody_reader = admitted_antibody_reader

    def run_graph(self, task: GraphTaskV1, mode: str) -> Result[GraphRunReferenceV1, Refusal]:
        """The graph entry point uses its licensed checker, never the fixed demonstration runner."""
        if self.graph_execution is None:
            return Err(
                Refusal("GRAPH_EXECUTION_UNAVAILABLE", "graph execution ports are unbound", _LOCUS)
            )
        return self.graph_execution.execute(task, mode)

    @property
    def learning_error(self) -> str | None:
        """The last learning-capture failure as ``"Type: message"``; ``None`` when there is none.

        Read-only view of ``learning_residuals``, the typed record.
        """
        if not self.learning_residuals:
            return None
        return self.learning_residuals[-1].message

    def _record_learning_residual(self, code: str, exc: BaseException) -> None:
        self.learning_residuals.append(
            Refusal(code=code, message=f"{type(exc).__name__}: {exc}", locus=_LOCUS)
        )

    def record_learning_init_failure(self, exc: BaseException) -> None:
        """The composition root reports that the learning port could not be built."""
        self._record_learning_residual("LEARNING_INIT_FAILED", exc)

    def _record_collection_residual(self, code: str, exc: BaseException) -> None:
        self.collection_residuals.append(
            Refusal(code=code, message=f"{type(exc).__name__}: {exc}", locus=_LOCUS)
        )

    def record_intelligence_collection_init_failure(self, exc: BaseException) -> None:
        """The composition root reports that durable source collection is unavailable."""
        self._record_collection_residual("INTELLIGENCE_COLLECTION_INIT_FAILED", exc)

    def record_bout_recovery_failure(self, refusal: Refusal) -> None:
        """The composition root reports that restart reconciliation could not finish."""
        self.recovery_residuals.append(refusal)

    def _notify_learning(self, directory: str, outcome: str) -> None:
        if self.intelligence_collection is None:
            if not any(
                residual.code == "INTELLIGENCE_COLLECTION_UNBOUND"
                for residual in self.collection_residuals
            ):
                self.collection_residuals.append(
                    Refusal(
                        code="INTELLIGENCE_COLLECTION_UNBOUND",
                        message="no durable intelligence collection port is configured",
                        locus=_LOCUS,
                    )
                )
        else:
            try:
                self.intelligence_collection.collect(
                    directory,
                    outcome=outcome,
                    origin="woland",
                    producer_id="omega_woland",
                )
            except Exception as exc:
                # The parent verdict is final. A failed durable handoff remains
                # a distinct obstruction instead of being relabelled as a bout
                # failure or silently dropped.
                self._record_collection_residual("INTELLIGENCE_COLLECTION_FAILED", exc)
        if self.learning_completion is not None:
            try:
                self.learning_completion.completed(directory, outcome=outcome)
            except Exception as exc:
                # Persistence and the parent's verdict are already final.
                # Surface capture failure separately, never replace that verdict.
                self._record_learning_residual("LEARNING_CAPTURE_FAILED", exc)

    def _woland_output(self, root: Path) -> Path:
        return self.intelligence_path(root, "_intelligence/_woland")

    def _resolve_repo_root(self) -> Result[Path, Refusal]:
        if self.repo_root is not None:
            return Ok(self.repo_root)
        if self.intelligence_root is not None:
            return self.intelligence_root()
        return Err(
            Refusal(
                code="WOLAND_OUTPUT_ROOT_UNRESOLVED",
                message="no repository root or intelligence-root resolver was injected",
                locus=_LOCUS,
            )
        )

    def _ingress_unbound(self, request: WolandBoutRequestV1) -> Refusal | None:
        if self.instruction_ingress is not None:
            return None
        if self.require_instruction_ingress or not request.fixture_mode:
            return Refusal(
                "INSTRUCTION_INGRESS_UNBOUND",
                "no independent instruction admission verifier is bound",
                _LOCUS,
            )
        return None

    def _receive_instruction_ingress(self, request: WolandBoutRequestV1):
        try:
            ingress = self.instruction_ingress.pre_dispatch(request)
        except Exception as exc:
            return Err(
                Refusal(
                    "INSTRUCTION_INGRESS_FAILED",
                    f"instruction admission verifier raised {type(exc).__name__}",
                    _LOCUS,
                )
            )
        if not isinstance(ingress, (Ok, Err)):
            return Err(
                Refusal(
                    "INSTRUCTION_INGRESS_INVALID",
                    "instruction ingress returned no typed decision",
                    _LOCUS,
                )
            )
        if isinstance(ingress, Err):
            return ingress
        if type(ingress.value) is not InstructionIngressReceiptV1:
            return Err(
                Refusal(
                    "INSTRUCTION_INGRESS_INVALID",
                    "instruction ingress returned no typed plan-bound receipt",
                    _LOCUS,
                )
            )
        return Ok(ingress.value)

    def _bind_instruction_plan(self, request: WolandBoutRequestV1, receipt: InstructionIngressReceiptV1):
        try:
            request_digest = instruction_request_digest(request)
        except Exception as exc:
            return Err(
                Refusal(
                    "INSTRUCTION_REQUEST_UNBINDABLE",
                    f"request binding failed with {type(exc).__name__}",
                    _LOCUS,
                )
            )
        if receipt.request_digest != request_digest:
            return Err(
                Refusal(
                    "INSTRUCTION_INGRESS_REQUEST_MISMATCH",
                    "instruction receipt does not bind the exact bout request",
                    _LOCUS,
                )
            )
        try:
            return Ok(receipt.native_instruction_plan())
        except (TypeError, ValueError):
            return Err(
                Refusal(
                    "INSTRUCTION_PLAN_PAYLOAD_INVALID",
                    "instruction receipt carries no valid canonical native plan payload",
                    _LOCUS,
                )
            )

    def _missing_plan_bytes(self, request: WolandBoutRequestV1, plan) -> Result[None, Refusal] | None:
        if not request.fixture_mode and plan is None:
            return Err(
                Refusal(
                    "INSTRUCTION_PLAN_BYTES_UNBOUND",
                    "a hash-only ingress receipt cannot authorize native execution",
                    _LOCUS,
                )
            )
        return None

    def _admit_instruction(self, request: WolandBoutRequestV1):
        unbound = self._ingress_unbound(request)
        if unbound is not None:
            return Err(unbound)
        if self.instruction_ingress is None:
            return Ok((None, None))
        received = self._receive_instruction_ingress(request)
        if isinstance(received, Err):
            return received
        bound = self._bind_instruction_plan(request, received.unwrap())
        if isinstance(bound, Err):
            return bound
        missing = self._missing_plan_bytes(request, bound.unwrap())
        if missing is not None:
            return missing
        return Ok((received.unwrap(), bound.unwrap()))

    def _python_overrides_bound(
        self,
        runtime: SwarmRuntimeV1 | None,
        profile: SwarmProfileV1 | None,
        cochain_adapter: CochainScoringPort | None,
        candidate_checker: CandidateCheckerPort | None,
    ) -> bool:
        return bool(
            runtime is not None
            or profile is not None
            or cochain_adapter is not None
            or candidate_checker is not None
            or self.candidate_checker is not None
        )

    def _native_path_selected(
        self,
        runtime: SwarmRuntimeV1 | None,
        profile: SwarmProfileV1 | None,
        cochain_adapter: CochainScoringPort | None,
        candidate_checker: CandidateCheckerPort | None,
    ) -> bool:
        if self.native_execution is None:
            return False
        return not self._python_overrides_bound(
            runtime, profile, cochain_adapter, candidate_checker
        )

    def _refuse_unconsumed_plan(self, plan, native_path: bool) -> Result[None, Refusal] | None:
        if plan is not None and not native_path:
            return Err(
                Refusal(
                    "INSTRUCTION_PLAN_CONSUMER_UNBOUND",
                    "the Python fallback does not consume a supplied instruction plan",
                    _LOCUS,
                )
            )
        return None

    def _clear_pre_dispatch(self, request: WolandBoutRequestV1, instruction_receipt):
        if request.fixture_mode:
            return None
        cleared = require_pre_dispatch_clear(
            self.anti_skill_gate,
            "omega_engine_woland.bout_service",
            request,
            instruction_receipt,
        )
        if isinstance(cleared, Err):
            return cleared
        return cleared.value

    def _fixture_use_case_type(self, request: WolandBoutRequestV1):
        if not request.fixture_mode:
            return None
        kind = getattr(request, "swarm_type", None)
        if kind in (SwarmTypeV1.SOFTWARE_DEV, "software-dev"):
            from .software_dev_bout_use_case import SoftwareDevBoutUseCase

            return SoftwareDevBoutUseCase
        if kind in (SwarmTypeV1.GOVERNING_COUNCILS, "governing-councils"):
            from .governing_councils_bout_use_case import GoverningCouncilsBoutUseCase

            return GoverningCouncilsBoutUseCase
        if kind in (SwarmTypeV1.THANATOS, "thanatos"):
            from .thanatos_bout_use_case import ThanatosBoutUseCase

            return ThanatosBoutUseCase
        if kind in (SwarmTypeV1.PRODUCT_MGMT, "product-mgmt"):
            from .product_mgmt_bout_use_case import ProductMgmtBoutUseCase

            return ProductMgmtBoutUseCase
        return None

    def _run_fixture_specialist(self, request: WolandBoutRequestV1):
        use_case_type = self._fixture_use_case_type(request)
        if use_case_type is None:
            return None
        root_dir = self._resolve_repo_root()
        repo_path = root_dir.unwrap() if root_dir.is_ok else Path.cwd()
        output_dir = self._woland_output(repo_path)
        use_case = use_case_type(repo_path, native_support=self._native_support)
        res = use_case.execute_bout(request, output_dir=output_dir)
        if res.is_err:
            return res
        outcome = res.unwrap()
        self._notify_learning(
            str(
                output_dir
                / "runs"
                / run_directory_name(request.task_key, native_support=self._native_support)
            ),
            outcome.terminal_verdict,
        )
        return Ok(outcome)

    def _prepare_learning_guidance(self, request: WolandBoutRequestV1) -> str:
        if self.learning_completion is None or request.fixture_mode:
            return ""
        try:
            return self.learning_completion.prepare(request.objective, request.task_key)
        except Exception as exc:
            self._record_learning_residual("LEARNING_PREPARE_FAILED", exc)
            return ""

    def _record_native_residuals(self, residuals) -> None:
        for residual in residuals:
            if residual.code == "BOUT_RECONCILE_INCOMPLETE":
                self.record_bout_recovery_failure(residual)
            else:
                self.journal_residuals.append(residual)

    def _notify_native_result(self, request: WolandBoutRequestV1, root, result):
        if result.is_ok:
            outcome = result.unwrap()
            source = outcome.receipt_path or outcome.working_state_path
            if source:
                self._notify_learning(str(Path(source).parent), outcome.terminal_verdict)
            else:
                self._record_learning_residual(
                    "LEARNING_SOURCE_UNAVAILABLE",
                    ValueError("No final bundle or working checkpoint was retained"),
                )
            return result
        refusal = result.unwrap_err()
        folder = dict(refusal.details).get("refusal_bundle")
        self._notify_learning(
            str(
                folder
                or self._woland_output(root.unwrap())
                / "runs"
                / run_directory_name(request.task_key, native_support=self._native_support)
            ),
            "REFUSE",
        )
        return result

    def _execute_native_path(self, request: WolandBoutRequestV1, native_instruction_plan):
        root = self._resolve_repo_root()
        if root.is_err:
            return Err(root.unwrap_err())
        guidance = self._prepare_learning_guidance(request)
        residuals = getattr(self.native_execution, "residuals", ())
        residual_count = len(residuals)
        result = self.native_execution.execute_bout(
            request,
            repo_root=root.unwrap(),
            learning_guidance=guidance,
            instruction_plan=native_instruction_plan,
        )
        self._record_native_residuals(residuals[residual_count:])
        return self._notify_native_result(request, root, result)

    def _loaded_profile(self, profile: SwarmProfileV1 | None):
        if profile is not None:
            return profile
        if self.profile_loader is not None:
            _, _, loaded, _, _ = self.profile_loader()
            return loaded
        from ..profile.profile_loader import load_woland_council_profile

        _, _, loaded, _, _ = load_woland_council_profile()
        return loaded

    def _resolved_repo_root(self, resolved_repo_root: Path | None):
        if resolved_repo_root is not None or self.intelligence_root is None:
            return Ok(resolved_repo_root)
        resolved = self._resolve_repo_root()
        if resolved.is_err:
            return Err(resolved.unwrap_err())
        return Ok(resolved.unwrap())

    def _runtime_and_output(self, request, profile, runtime, resolved_repo_root):
        if runtime is None:
            if self.runtime_factory is None:
                return Err(
                    Refusal(
                        code="EXECUTION_UNAVAILABLE",
                        message="no runtime factory is configured for this service",
                        locus=_LOCUS,
                    )
                )
            root = self._resolve_repo_root()
            if root.is_err:
                return Err(root.unwrap_err())
            resolved_repo_root = root.unwrap()
            runtime = self.runtime_factory(
                profile=profile,
                output_dir=self._woland_output(root.unwrap()),
                fixture_mode=request.fixture_mode,
                request_external_admission=request.request_external_admission,
                max_critique_rounds=request.max_rounds,
            )
        runtime = replace(
            runtime,
            max_critique_rounds=request.max_rounds,
            request_external_admission=request.request_external_admission,
        )
        if runtime.operational_output_dir:
            output_dir = Path(runtime.operational_output_dir)
        else:
            root = self._resolve_repo_root()
            if root.is_err:
                return Err(root.unwrap_err())
            resolved_repo_root = root.unwrap()
            output_dir = self._woland_output(root.unwrap())
        return Ok((runtime, output_dir, resolved_repo_root))

    def _prepare_python_runtime(self, request, profile, runtime):
        profile = self._loaded_profile(profile)
        rooted = self._resolved_repo_root(self.repo_root)
        if isinstance(rooted, Err):
            return rooted
        prepared = self._runtime_and_output(request, profile, runtime, rooted.unwrap())
        if isinstance(prepared, Err):
            return prepared
        runtime, output_dir, resolved_repo_root = prepared.unwrap()
        return Ok((profile, runtime, output_dir, resolved_repo_root))

    def _work_packet(self, request: WolandBoutRequestV1):
        try:
            return Ok(
                WorkPacketV1(
                    task_key=request.task_key,
                    scene_id="act1_perception",
                    objective=request.objective,
                    input_artifact_refs=(),
                    acceptance_criteria=("Must pass all tests",),
                    budget_units=50,
                    evaluator_epoch_id=_digest(request.task_key),
                )
            )
        except (TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="WOLAND_REQUEST_INVALID",
                    message=f"the bout request cannot form a work packet: {exc}",
                    locus=_LOCUS,
                )
            )

    def _notify_python_refusal(self, refusal: Refusal, output_dir: Path, request: WolandBoutRequestV1) -> None:
        bundle = dict(refusal.details).get("refusal_bundle")
        if bundle:
            self._notify_learning(str(bundle), "REFUSE")
            return
        self._notify_learning(
            str(
                output_dir
                / "runs"
                / run_directory_name(request.task_key, native_support=self._native_support)
            ),
            "REFUSE",
        )

    def _chosen_cochain(self, cochain_adapter: CochainScoringPort | None) -> CochainScoringPort | None:
        return cochain_adapter or self.cochain_adapter

    def _chosen_checker(self, candidate_checker: CandidateCheckerPort | None) -> CandidateCheckerPort | None:
        return candidate_checker or self.candidate_checker

    def _live_gate(self, request: WolandBoutRequestV1):
        if request.fixture_mode:
            return None
        return self.anti_skill_gate

    def _live_request(self, request: WolandBoutRequestV1):
        if request.fixture_mode:
            return None
        return request

    def _python_outcome(self, request, receipt, packet, output_dir: Path):
        selected_id = (
            receipt.selection_proposal.selected_candidate_id if receipt.selection_proposal else ""
        )
        disposition = (
            receipt.selection_proposal.disposition if receipt.selection_proposal else "COMPOSTED"
        )
        if request.request_external_admission and disposition == "SELECT":
            consecration_state = "PROPOSED_FOR_EXTERNAL_ADMISSION"
            terminal_verdict = "PROPOSED_FOR_EXTERNAL_ADMISSION"
        else:
            consecration_state = "COMPOSTED_WITH_REENTRY_GUIDANCE"
            terminal_verdict = "COMPOSTED"
        run_folder = output_dir / "runs" / run_directory_name(
            packet.task_key, native_support=self._native_support
        )
        self._notify_learning(str(run_folder), terminal_verdict)
        return Ok(
            WolandBoutOutcomeV1(
                receipt_id=receipt.receipt_id,
                selected_candidate_id=selected_id,
                disposition=disposition,
                consecration_state=consecration_state,
                terminal_verdict=terminal_verdict,
                authority_effect="None",
                task_key=packet.task_key,
                status=receipt.status,
                receipt_path=str(run_folder / "receipt.json"),
                novella_path=str(run_folder / "uns.md"),
                ddc_path=str(run_folder / "ddc.jsonl"),
                summary_path=str(run_folder / "summary.json"),
                phi1=receipt.phi1,
                gamma2=receipt.gamma2,
                defect_count=receipt.defect_count,
                residual_declared=self._residual_declared(request, receipt),
                is_authorized=receipt.status == "AUTHORIZED",
                measurement_status=receipt.measurement_status,
                checker_verdict=receipt.checker_verdict,
                checker_receipt_sha256=receipt.checker_receipt_sha256,
                authorization_blockers=receipt.authorization_blockers,
                authorization_evidence=receipt.authorization_evidence,
                swarm_type=request.swarm_type.value,
            )
        )

    def _residual_declared(self, request, receipt) -> bool:
        if receipt.status != "BOUNDED_RESIDUAL":
            return False
        if not request.ablation_flags:
            return True
        return not request.ablation_flags.get("no_residual_ledger")

    def _finish_python_bout(
        self,
        request,
        profile,
        runtime,
        cochain_adapter,
        candidate_checker,
        dispatch_decision,
    ):
        prepared = self._prepare_python_runtime(request, profile, runtime)
        if isinstance(prepared, Err):
            return prepared
        profile, runtime, output_dir, resolved_repo_root = prepared.unwrap()
        packet_result = self._work_packet(request)
        if isinstance(packet_result, Err):
            return packet_result
        packet = packet_result.unwrap()
        res = execute_7act_woland_bout(
            profile,
            runtime,
            packet,
            carrier_context=request.carrier_context,
            ablation_flags=request.ablation_flags,
            output_dir=output_dir,
            repo_root=resolved_repo_root,
            cochain_adapter=self._chosen_cochain(cochain_adapter),
            candidate_checker=self._chosen_checker(candidate_checker),
            fixture_seats=request.fixture_mode is not False,
            learning_guidance=self._prepare_learning_guidance(request),
            journal=self.bout_journal,
            admitted_antibody_reader=self.admitted_antibody_reader,
            anti_skill_gate=self._live_gate(request),
            anti_skill_request=self._live_request(request),
            dispatch_decision=dispatch_decision,
            native_support=self._native_support,
        )
        if res.is_err:
            refusal = res.unwrap_err()
            self._notify_python_refusal(refusal, output_dir, request)
            return Err(refusal)
        return self._python_outcome(request, res.unwrap(), packet, output_dir)

    def execute_bout(
        self,
        request: WolandBoutRequestV1,
        *,
        runtime: SwarmRuntimeV1 | None = None,
        profile: SwarmProfileV1 | None = None,
        cochain_adapter: CochainScoringPort | None = None,
        candidate_checker: CandidateCheckerPort | None = None,
    ) -> Result[WolandBoutOutcomeV1, Refusal]:
        """Run one bout and return its typed result, or the typed refusal that stopped it."""
        # Ceilings first, before anything is loaded, built, or charged.
        #
        # The campaign's seed defect 2 was about ordering, not about the absence
        # of a limit: `WorkPacketV1` below has always refused an objective over
        # 16 KiB, but only after a profile was read off disk and a runtime was
        # constructed. That made a text bomb cost real work and produced an
        # untyped `ValueError` from the domain instead of a named refusal.
        #
        # `WolandBoutRequestV1` now enforces the same ceiling at construction, so
        # in production this guard is redundant. It is kept because a use case
        # that trusts its caller to have validated is a use case whose ordering
        # is an accident of the call site; `test_ingress_ordering` calls it with
        # an unvalidated stand-in to prove the guard is real.
        check_text_bytes(
            request.objective,
            limit=MAX_ADMITTED_TEXT_BYTES,
            refusal_code=REFUSAL_TEXT_TOO_LARGE,
        )
        # This is the only service-level boundary shared by the native fast
        # path and Python fallback. A strict invocation cannot load a profile,
        # prepare learning guidance, or call the native host without an
        # independently bound instruction ingress verifier.
        admitted = self._admit_instruction(request)
        if isinstance(admitted, Err):
            return admitted
        instruction_receipt, native_instruction_plan = admitted.unwrap()
        native_path = self._native_path_selected(
            runtime, profile, cochain_adapter, candidate_checker
        )
        unconsumed = self._refuse_unconsumed_plan(native_instruction_plan, native_path)
        if unconsumed is not None:
            return unconsumed
        dispatched = self._clear_pre_dispatch(request, instruction_receipt)
        if isinstance(dispatched, Err):
            return dispatched
        specialist = self._run_fixture_specialist(request)
        if specialist is not None:
            return specialist
        if native_path:
            return self._execute_native_path(request, native_instruction_plan)
        return self._finish_python_bout(
            request,
            profile,
            runtime,
            cochain_adapter,
            candidate_checker,
            dispatched,
        )

def create_woland_circuit_runner(
    rt: SwarmRuntimeV1,
    *,
    carrier_context: Mapping[str, Any] | None = None,
    ablation_flags: Mapping[str, bool] | None = None,
    repo_root: Path | str | None = None,
    output_dir: Path | str | None = None,
    cochain_adapter: CochainScoringPort | None = None,
    candidate_checker: CandidateCheckerPort | None = None,
    fixture_seats: bool = True,
    admitted_antibody_reader: AdmittedAntibodyReader | None = None,
    native_support: NativeOperationPort,
) -> Callable[[Any, Any, str], Any]:
    """Create an acts_runner function bridging WolandSevenActCircuit to execute_7act_woland_bout."""
    from ..domain.circuit import WolandGateReceiptV1

    def _runner(input_packet: Any, profile: Any, run_id: str) -> WolandGateReceiptV1:
        res = execute_7act_woland_bout(
            profile,
            rt,
            input_packet,
            carrier_context=carrier_context,
            ablation_flags=ablation_flags,
            repo_root=repo_root,
            output_dir=output_dir,
            cochain_adapter=cochain_adapter,
            candidate_checker=candidate_checker,
            fixture_seats=fixture_seats,
            admitted_antibody_reader=admitted_antibody_reader,
            native_support=native_support,
        )
        if res.is_ok:
            receipt = res.unwrap()
            packet_dict = (
                input_packet.to_dict()
                if hasattr(input_packet, "to_dict")
                else {"task_key": getattr(input_packet, "task_key", run_id)}
            )
            profile_dict = (
                profile.to_dict()
                if hasattr(profile, "to_dict")
                else {"profile_name": getattr(profile, "profile_name", "woland")}
            )
            in_digest = (
                "sha256:"
                + hashlib.sha256(
                    json.dumps(packet_dict, sort_keys=True).encode("utf-8")
                ).hexdigest()
            )
            prof_digest = (
                "sha256:"
                + hashlib.sha256(
                    json.dumps(profile_dict, sort_keys=True).encode("utf-8")
                ).hexdigest()
            )
            return WolandGateReceiptV1(
                run_id=run_id,
                profile_digest=prof_digest,
                input_packet_digest=in_digest,
                output_packet_digest=receipt.receipt_id,
                gate_status=receipt.status,
                is_completed_gated_run=True,
                open_residuals=[receipt.receipt_id] if receipt.status == "BOUNDED_RESIDUAL" else [],
                authority_effect="None",
                ddc_trace_hash=receipt.ddc_trace_hash,
                lggr_joint_kernel_status=receipt.lggr_joint_kernel_status,
                coda_potential_phi1=receipt.phi1,
                coda_closure_gamma2=receipt.gamma2,
                carrier_degree=receipt.carrier_degree,
            )
        else:
            refusal = res.unwrap_err()
            return WolandGateReceiptV1(
                run_id=run_id,
                profile_digest="",
                input_packet_digest="",
                output_packet_digest="",
                gate_status="NOT_RUN",
                refusal_code=refusal.code,
                is_completed_gated_run=False,
                open_residuals=[],
                authority_effect="None",
            )

    return _runner


__all__ = ["WolandSwarmService", "create_woland_circuit_runner", "execute_7act_woland_bout"]
