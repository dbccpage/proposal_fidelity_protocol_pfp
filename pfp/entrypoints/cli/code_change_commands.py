"""Code Change Proposal command handlers for Symbol Game CLI presentation layer.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from dataclasses import asdict

from operating_system.adapters.security import (
    FixtureOnlyAeadProtector,
)
from operating_system.infrastructure import EncryptedArtifactCas
from pfp.domain import (
    CandidateArtifactV1,
    CodeChangePatchArtifactV1,
    CodeChangeProposalPayloadV1,
    DomainError,
    GateReceiptV1,
    PacketEnvelopeV2,
    bind_patch_bytes,
    build_code_change_proposal_envelope,
    evaluate_code_change_candidate,
    parse_code_change_proposal_envelope,
    render_code_change_run_root_markdown,
    verify_code_change_run_root,
)
from pfp.domain import (
    attach_candidate as attach_code_change_candidate,
)
from pfp.domain import (
    verify_markdown_does_not_mutate_claims as verify_code_markdown_claims,
)
from pfp.infrastructure.serialization import (
    write_content_addressed_json,
)
from pfp.infrastructure.trace import (
    TERMINAL_PATH_COMPLETE,
    TracedCodeChangeController,
    TraceRefusal,
    fixture_gateway,
    scripted_openai_payload,
)
from adversary.domain.providers.types import (
    CandidateRequest,
)

from .io_utils import _read_json, _write_json, _write_text

#: The system prompt the fixture worker is given. Fixed rather than configurable:
#: this command exists to run the deterministic path, and a prompt that can vary
#: is the first step towards a run whose inputs are not in the trace.
FIXTURE_SYSTEM_PROMPT = "you are a symbol game code-change worker"
FIXTURE_CAS_KEY = b"symbol-game-cli-fixture-only-cas-key-v1"


def cmd_code_change_check_source_bound(args: argparse.Namespace) -> int:
    """Opt-in host composition of the existing binder and finite native checker.

    Source files and executable trust come from operator options, never a model
    reply. This snapshots selected source bytes; it does not assert that Git
    attests them or that the patch applies. Replay is local to this invocation.
    """
    from pfp.domain.shared_kernel.path import is_normalized_relative_posix
    from pfp.infrastructure.code_change_checker import (
        NativeCheckerTrust,
        SourceBoundCodeChangeChecker,
    )
    from pfp.use_cases.code_change import (
        CodeChangeSession,
        SubmitPatchCandidateUseCase,
    )

    output = args.output
    if output.exists():
        print("CHECKER_OUTPUT_EXISTS: choose a new output path", file=sys.stderr)
        return 2
    checker = None
    report = {
        "schema_version": "core.pfp.source-bound-code-change-cli.v1",
        "authority_effect": "None",
        "provider_calls": 0,
        "native_calls": 0,
        "replay_check": None,
    }
    try:
        session = CodeChangeSession(envelope=PacketEnvelopeV2.from_dict(_read_json(args.packet)))
        patch_bytes = args.patch_bytes.read_bytes()
        session, bound = SubmitPatchCandidateUseCase().execute(
            session=session,
            producer_id="source-bound-cli",
            patch_text=patch_bytes.decode("utf-8"),
        )
        root = args.source_root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("source root must be a directory")
        files = []
        for relative in sorted(set(args.source_path)):
            if not is_normalized_relative_posix(relative):
                raise ValueError("source paths must be normalized relative POSIX paths")
            path = (root / relative).resolve(strict=True)
            if not path.is_relative_to(root):
                raise ValueError("source path escapes the explicit source root")
            files.append((relative, path.read_bytes()))
        report["source_files"] = [
            {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "byte_count": len(data)}
            for path, data in files
        ]
        checker = SourceBoundCodeChangeChecker(
            session=session,
            run_id=args.run_id,
            source_files=tuple(files),
            trust=NativeCheckerTrust(args.checker_binary, args.checker_sha256),
            max_native_calls=args.max_native_calls,
        )
        request = checker.prepare(bound, attempt_id=args.attempt_id)
        checked = checker.check(request, bound)
        if checked.is_err:
            report["refusal"] = checked.unwrap_err().to_dict()
            status = 2
        else:
            result = checked.unwrap()
            wire = asdict(result)
            del wire["evidence_json"]
            wire.update(
                evidence_json_base64=base64.b64encode(result.evidence_json).decode("ascii"),
                evidence_sha256=result.evidence_sha256,
                evidence_kind="canonical_decoded_native_outcomes",
            )
            report["check"] = wire
            status = 0 if result.diagnostic_status == "PASS" else 2
            if args.replay_check:
                before = checker.native_calls
                replayed = checker.replay(result, request, bound)
                report["replay_check"] = {
                    "native_calls": checker.native_calls - before,
                    "provider_calls": 0,
                    "equal": replayed.is_ok and replayed.unwrap() == result,
                }
                if replayed.is_err:
                    report["refusal"] = replayed.unwrap_err().to_dict()
                    status = 2
    except (DomainError, ValueError, OSError) as exc:
        report["refusal"] = {
            "code": "CHECKER_INPUT_MALFORMED",
            "message": str(exc),
            "locus": "pfp.entrypoints.cli.code_change_commands",
        }
        status = 2
    report["native_calls"] = 0 if checker is None else checker.native_calls
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, ensure_ascii=True, sort_keys=True, indent=2)
            stream.write("\n")
    except OSError as exc:
        print(f"CHECKER_OUTPUT_UNAVAILABLE: {exc}", file=sys.stderr)
        return 2
    return status


def cmd_code_change_run_fixture(args: argparse.Namespace) -> int:
    """Run the whole code-change path once, deterministically, under a trace.

    This is the caller the instrumented path did not have. `ExecutionTrace`,
    `fixture_gateway` and `TracedCodeChangeController` were complete, tested, and
    reachable from nothing but their own tests -- which is the same "correct code
    with no caller" defect the trace work was built to eliminate, sitting one
    level up. The other code-change commands each drive a single stage straight
    into the domain; none of them records anything.

    Nothing new is orchestrated here. The stage sequence is the one
    `test_traced_code_change.py` already proves, and the trace, gateway, scripted
    transport and durability barriers are all owned by `fixture_gateway`. The
    command's whole job is to hold them together and write down where the output
    went.

    The provider is scripted and returns the supplied patch as its reply, so the
    run is a fixture in the strict sense the trace records: `run_mode` is
    `deterministic_fixture` and `live_transport` is false. Two runs of the same
    inputs must produce the same identities, which is the property that makes the
    recorder trustworthy before any model is involved.

    **The trace is sealed only on success.** A refused stage leaves it unsealed
    on purpose: the run did not complete, and a file that derives INCOMPLETE is
    the honest record of that. The refusal itself is already in the trace --
    `TracedCodeChangeController` records it before re-raising.

    The terminal digest is printed beside the trace path because it is the only
    value an operator can carry away from the run and check the file against
    later, with `verify_trace`. Printing it anchors nothing -- a digest copied
    out of stdout into the same tree is re-signable by whoever re-signs the
    trace. It is the attachment point an anchor would bind to, and the run root
    deliberately does not carry it: a digest stored inside the artefacts the run
    produced is a witness to nothing.
    """
    patch_text = args.patch.read_text(encoding="utf-8")
    output_dir = args.output_dir
    trace_path = output_dir / "trace.jsonl"
    run_root_path = output_dir / "run_root.json"

    try:
        # One file per execution: a second run into the same directory is
        # refused rather than appended to, so the re-run is visible instead of
        # silently splicing two executions into one hash chain.
        run = fixture_gateway(
            trace_path,
            [scripted_openai_payload(patch_text)],
            artifact_store=EncryptedArtifactCas(
                output_dir / "encrypted_artifacts",
                FixtureOnlyAeadProtector(FIXTURE_CAS_KEY),
            ),
            execution_id=args.task_id,
        )
    except TraceRefusal as exc:
        sys.stderr.write(f"REFUSED: {exc}\n")
        return 2

    traced = TracedCodeChangeController(run.trace)
    try:
        session = traced.create_proposal(
            task_id=args.task_id,
            objective=args.objective,
            base_revision=args.base_revision,
            owned_paths=tuple(args.owned_path),
            protected_paths=tuple(args.protected_path),
        )
        # The scripted provider answers with the patch. Going through the gateway
        # rather than reading the file twice is the point: this is the seam a
        # real producer would occupy, and it runs the allowlist, the price table,
        # the budget and both durability barriers on the way.
        response, _receipt = run.gateway.complete(
            CandidateRequest(system=FIXTURE_SYSTEM_PROMPT, user=args.objective)
        )
        session, bound = traced.submit_patch(
            session=session,
            producer_id=args.producer_id,
            patch_text=response.content,
        )
        receipts = traced.evaluate_patch_gates(session=session, bound=bound)
        run_root = traced.finalize_run(
            session=session, bound=bound, gate_receipts=receipts
        )
    except (DomainError, TraceRefusal) as exc:
        run.trace.abandon()
        sys.stderr.write(f"REFUSED: {type(exc).__name__}: {exc}\n")
        return 2

    terminal_digest = run.trace.seal(TERMINAL_PATH_COMPLETE)
    _write_json(run_root_path, run_root.to_dict())

    sys.stdout.write(
        "code-change-run-fixture: complete\n"
        f"  execution_id    : {args.task_id}\n"
        f"  packet_id       : {session.packet_id}\n"
        f"  candidate_id    : {bound.candidate.candidate_id}\n"
        f"  terminal_status : {run_root.terminal_status}\n"
        f"  gates           : {len(receipts)}\n"
        f"  trace           : {trace_path}\n"
        f"  terminal_digest : {terminal_digest}\n"
        f"  run_root        : {run_root_path}\n"
    )
    return 0


def cmd_code_change_create_task(args: argparse.Namespace) -> int:
    payload_wire = _read_json(args.payload)
    payload = CodeChangeProposalPayloadV1.from_dict(payload_wire)
    envelope = build_code_change_proposal_envelope(
        payload,
        task_id=args.task_id,
        carrier_id=args.carrier_id,
        step_budget=args.step_budget,
    )
    if args.artifact_dir is not None:
        write_content_addressed_json(
            args.artifact_dir, "code-change-task", envelope.to_dict()
        )
    _write_json(args.output, envelope.to_dict())
    return 0


def cmd_code_change_attach_candidate(args: argparse.Namespace) -> int:
    envelope_wire = _read_json(args.packet)
    envelope = PacketEnvelopeV2.from_dict(envelope_wire)
    parse_code_change_proposal_envelope(envelope)
    patch_bytes = args.patch_bytes.read_bytes()
    touched = tuple(sorted(set(args.touched_path)))
    patch = bind_patch_bytes(
        packet_id=envelope.packet_id,
        producer_id=args.producer_id,
        base_source_revision=args.base_source_revision
        or parse_code_change_proposal_envelope(envelope).source_revision,
        patch_encoding=args.patch_encoding,
        patch_bytes=patch_bytes,
        touched_paths=touched,
        claimed_summary=args.claimed_summary,
    )
    candidate = attach_code_change_candidate(
        envelope,
        patch,
        producer_id=args.producer_id,
        claimed_terminal=args.claimed_terminal,
        claimed_valid=args.claimed_valid,
    )
    if args.artifact_dir is not None:
        write_content_addressed_json(
            args.artifact_dir, "code-change-candidate", candidate.to_dict()
        )
    _write_json(args.output, candidate.to_dict())
    return 0


def cmd_code_change_evaluate(args: argparse.Namespace) -> int:
    envelope = PacketEnvelopeV2.from_dict(_read_json(args.packet))
    candidate = CandidateArtifactV1.from_dict(_read_json(args.candidate))
    patch = CodeChangePatchArtifactV1.from_dict(_read_json(args.patch))
    gate_receipts = tuple(
        GateReceiptV1.from_dict(_read_json(p)) for p in (args.gate_receipt or [])
    )
    run_root = evaluate_code_change_candidate(
        envelope,
        candidate,
        patch,
        gate_receipts=gate_receipts,
        prior_candidate_count=args.prior_candidate_count,
        operation_count=args.operation_count,
    )
    if args.artifact_dir is not None:
        write_content_addressed_json(
            args.artifact_dir, "code-change-run-root", run_root.to_dict()
        )
    _write_json(args.output, run_root.to_dict())
    return 0


def cmd_code_change_verify_run_root(args: argparse.Namespace) -> int:
    wire = _read_json(args.run_root)
    run_root = verify_code_change_run_root(wire)
    _write_json(args.output, run_root.to_dict())
    return 0


def cmd_code_change_render_markdown(args: argparse.Namespace) -> int:
    wire = _read_json(args.run_root)
    run_root = verify_code_change_run_root(wire)
    md = render_code_change_run_root_markdown(run_root)
    verify_code_markdown_claims(md, run_root)
    _write_text(args.output, md)
    return 0
