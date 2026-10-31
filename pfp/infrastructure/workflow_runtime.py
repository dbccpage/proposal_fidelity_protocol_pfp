"""Shared single-response workflow custody, accounted dispatch and CLI."""

from __future__ import annotations

import argparse
import base64
import json
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

from pfp.domain.pfp_ingress import MAX_REPLY_BYTES, strict_json
from pfp.infrastructure.adapters.pfp_campaign import canonical, digest, write_new
from pfp.infrastructure.task_turn import PreparedTaskTurn

_PREPARED_FILES = (
    "task.json",
    "prepared.json",
    "system_prompt.txt",
    "user_prompt.txt",
    "response_schema.json",
)
_CHECKED_FILES = (*_PREPARED_FILES, "preparation_manifest.json", "response.raw", "receipt.json")


def source_bytes(name: str) -> bytes:
    """Resolve installed source resources; never depend on a monorepo checkout."""
    parts = name.split("/")
    if len(parts) < 2 or parts[0] not in {"pfp", "adversary", "operations"} or any(
        not part or part in {".", ".."} or "\\" in part or ":" in part for part in parts
    ):
        raise ValueError("WORKFLOW_SOURCE_PATH_INVALID")
    return files(parts[0]).joinpath(*parts[1:]).read_bytes()


class WorkflowRuntime:
    def __init__(self, workflow):
        self.workflow = workflow
        self.source_files = (
            workflow.BASE_TEMPLATE,
            "domain/contracts/pfp_runtime.py",
            "domain/pfp_ingress.py",
            "use_cases/pfp_prompt.py",
            "use_cases/pfp_proposal.py",
            "infrastructure/task_turn.py",
            "infrastructure/adapters/pfp_campaign.py",
            "infrastructure/workflow_tasks.py",
            "infrastructure/workflow_runtime.py",
            "infrastructure/workflow_accounting.py",
            *workflow.SOURCE_FILES,
        )

    def source_identity(self) -> dict:
        root = files("pfp")
        return {
            "sources": {
                name: digest(root.joinpath(name).read_bytes()) for name in self.source_files
            },
            "dependencies": {name: version(name) for name in ("jsonschema", "PyYAML")},
        }

    def _read_json(self, path: Path) -> dict:
        value = strict_json(path.read_bytes().decode("utf-8"), max_bytes=8 * MAX_REPLY_BYTES)
        if type(value) is not dict:
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_JSON_OBJECT_REQUIRED")
        return value

    def _write_manifest(self, root: Path, name: str, members: tuple[str, ...]) -> None:
        write_new(
            root / name,
            {
                "workflow_id": self.workflow.WORKFLOW_ID,
                "version": self.workflow.VERSION,
                "files": {member: digest((root / member).read_bytes()) for member in members},
                "implementation": self.source_identity(),
            },
        )

    def _verify_manifest(self, root: Path, name: str, members: tuple[str, ...]) -> None:
        manifest = self._read_json(root / name)
        if (
            set(manifest) != {"workflow_id", "version", "files", "implementation"}
            or manifest["workflow_id"] != self.workflow.WORKFLOW_ID
            or manifest["version"] != self.workflow.VERSION
            or (type(manifest["files"]) is not dict)
            or (set(manifest["files"]) != set(members))
        ):
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_MANIFEST_INVALID")
        if manifest["implementation"] != self.source_identity():
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_IMPLEMENTATION_MISMATCH")
        if any(
            (
                digest((root / member).read_bytes()) != manifest["files"][member]
                for member in members
            )
        ):
            raise ValueError("RECEIPT_DIGEST_MISMATCH")

    def prepare_run(self, spec: dict, output: Path) -> dict:
        """Create a fresh run directory. Preparing never invokes a provider."""
        spec = self.workflow.validate_task(spec)
        turn = self.workflow.prepare_task(spec)
        prepared = dict(
            workflow_id=self.workflow.WORKFLOW_ID,
            version=self.workflow.VERSION,
            binding=turn.binding,
            prompt=turn.prompt.to_dict(),
        )
        output.mkdir(parents=True, exist_ok=False)
        write_new(output / "task.json", spec)
        write_new(output / "prepared.json", prepared)
        write_new(output / "system_prompt.txt", turn.prompt.system.encode("utf-8"))
        write_new(output / "user_prompt.txt", turn.prompt.user.encode("utf-8"))
        write_new(output / "response_schema.json", turn.prompt.response_schema)
        self._write_manifest(output, "preparation_manifest.json", _PREPARED_FILES)
        return prepared

    def _load_preparation(self, root: Path) -> tuple[dict, PreparedTaskTurn]:
        self._verify_manifest(root, "preparation_manifest.json", _PREPARED_FILES)
        spec = self.workflow.validate_task(self._read_json(root / "task.json"))
        turn = self.workflow.prepare_task(spec)
        expected = dict(
            workflow_id=self.workflow.WORKFLOW_ID,
            version=self.workflow.VERSION,
            binding=turn.binding,
            prompt=turn.prompt.to_dict(),
        )
        if self._read_json(root / "prepared.json") != expected:
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_PREPARED_PROMPT_MISMATCH")
        return (spec, turn)

    def _finish(
        self, root: Path, raw_reply: bytes, *, origin: str, provider_record: dict | None = None
    ) -> dict:
        spec, _ = self._load_preparation(root)
        write_new(root / "response.raw", raw_reply)
        checked = self.workflow.check_reply(spec, raw_reply)
        if self.workflow.COLLECTION_FILES:
            collection = self.workflow.collect_emitted(spec, raw_reply, checked)
            write_new(root / "collection.json", collection)
        receipt = dict(
            workflow_id=self.workflow.WORKFLOW_ID,
            version=self.workflow.VERSION,
            agent_count=1,
            main_stages=1,
            maximum_provider_calls=1,
            retries=0,
            origin=origin,
            check=checked,
            authority_effect="None",
        )
        if provider_record is None:
            fixture = origin == "HAND_AUTHORED_FIXTURE"
            receipt.update(
                provider_calls_in_this_command=0,
                external_provider_calls=0 if fixture else None,
                provider_cost_usd=0 if fixture else None,
            )
        else:
            write_new(root / "provider.json", provider_record)
            receipt["provider"] = provider_record
            if provider_record["accounting_state"] not in {
                "CompletedSettled",
                "CompletedPendingSettlement",
            }:
                receipt["status"] = "INFRASTRUCTURE_ERROR"
                receipt["failure_class"] = provider_record["accounting_state"]
            if provider_record["identity_error"]:
                receipt.update(
                    status="INFRASTRUCTURE_ERROR",
                    failure_class=f"{self.workflow.WORKFLOW_ID}_PROVIDER_IDENTITY_MISMATCH",
                )
        receipt.setdefault("status", checked["status"])
        receipt.setdefault("failure_class", checked["failure_class"])
        write_new(root / "receipt.json", receipt)
        members = (
            _CHECKED_FILES
            + self.workflow.COLLECTION_FILES
            + (("provider.json",) if provider_record is not None else ())
        )
        self._write_manifest(root, "receipt_manifest.json", members)
        return receipt

    def check_run(self, root: Path, reply_path: Path, *, fixture: bool = False) -> dict:
        """Check a genuine externally supplied reply; external billing is unknown."""
        if any(
            (
                (root / name).exists()
                for name in ("accounting.sqlite3", "failure.json", "provider.json")
            )
        ):
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_ACCOUNTED_RUN_NEEDS_OWN_RESPONSE")
        if type(fixture) is not bool:
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_FIXTURE_FLAG_MUST_BE_BOOLEAN")
        return self._finish(
            root,
            reply_path.read_bytes(),
            origin="HAND_AUTHORED_FIXTURE" if fixture else "EXTERNAL_CAPTURE",
        )

    def replay_run(self, root: Path) -> dict:
        """Verify manifests and recheck actual bytes without sending or writing files."""
        manifest = self._read_json(root / "receipt_manifest.json")
        member_names = manifest.get("files", {})
        members = (
            _CHECKED_FILES
            + self.workflow.COLLECTION_FILES
            + (("provider.json",) if "provider.json" in member_names else ())
        )
        self._verify_manifest(root, "receipt_manifest.json", members)
        spec, turn = self._load_preparation(root)
        receipt = self._read_json(root / "receipt.json")
        checked = turn.replay(
            receipt["check"],
            judges=self.workflow.judges_for(spec),
            require_checker=spec["checker"] != "schema_only",
        )
        if self.workflow.COLLECTION_FILES:
            checked = self.workflow.finalize_check(spec, checked)
            collection = self.workflow.collect_emitted(
                spec, (root / "response.raw").read_bytes(), checked
            )
            if canonical(collection) != canonical(self._read_json(root / "collection.json")):
                raise ValueError(f"{self.workflow.WORKFLOW_ID}_COLLECTION_REPLAY_MISMATCH")
        if (
            canonical(checked) != canonical(receipt["check"])
            or base64.b64decode(checked["raw_reply_base64"], validate=True)
            != (root / "response.raw").read_bytes()
        ):
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_REPLAY_CHECK_MISMATCH")
        provider_record = receipt.get("provider")
        status, failure = (checked["status"], checked["failure_class"])
        if provider_record is not None:
            if provider_record != self._read_json(root / "provider.json"):
                raise ValueError(f"{self.workflow.WORKFLOW_ID}_PROVIDER_RECORD_MISMATCH")
            if provider_record["accounting_state"] not in {
                "CompletedSettled",
                "CompletedPendingSettlement",
            }:
                status, failure = ("INFRASTRUCTURE_ERROR", provider_record["accounting_state"])
            if provider_record["identity_error"]:
                status, failure = (
                    "INFRASTRUCTURE_ERROR",
                    f"{self.workflow.WORKFLOW_ID}_PROVIDER_IDENTITY_MISMATCH",
                )
        if receipt["status"] != status or receipt["failure_class"] != failure:
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_REPLAY_STATUS_MISMATCH")
        return dict(
            workflow_id=self.workflow.WORKFLOW_ID,
            version=self.workflow.VERSION,
            status=status,
            failure_class=failure,
            check=checked,
            replay_verified=True,
            provider_calls_in_this_command=0,
            authority_effect="None",
        )

    def run_accounted(
        self, spec: dict, output: Path, *, gateway, model: str, max_output_tokens: int
    ) -> dict:
        """Send the prepared WF1 request once through an existing one-call gateway."""
        from operations.domain.rop.result import Err
        from pfp.infrastructure.pilot_matrix import validate_pilot_gateways
        from adversary.domain.providers.types import (
            CandidateRequest,
            DecodingParamsV1,
            Provider,
        )
        from adversary.infrastructure.providers.openai_compat import (
            build_openai_compat_body,
        )

        validate_pilot_gateways({model: gateway}, [model], max_tokens=max_output_tokens)
        limit = getattr(gateway, "limit", gateway.scope.get("limit_microusd"))
        if type(limit) is not int or not 0 < limit <= 4999:
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_BUDGET_MUST_NOT_EXCEED_4999")
        if gateway.scope["max_calls"] != 1:
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_ONE_CALL_GATEWAY_REQUIRED")
        if not output.exists():
            self.prepare_run(spec, output)
        elif any(
            (
                (output / name).exists()
                for name in ("response.raw", "receipt.json", "provider.json", "failure.json")
            )
        ):
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_RUN_ALREADY_ATTEMPTED")
        stored_spec, turn = self._load_preparation(output)
        if self.workflow.validate_task(spec) != stored_spec:
            raise ValueError(f"{self.workflow.WORKFLOW_ID}_TASK_BINDING_MISMATCH")
        request = CandidateRequest(
            turn.prompt.system,
            turn.prompt.user,
            decoding=DecodingParamsV1(
                temperature=0.0, top_p=1.0, allow_fallbacks=False, require_parameters=True
            ),
        )
        wire_request = build_openai_compat_body(
            request, model=model, max_tokens=max_output_tokens, provider=Provider.OPENROUTER
        )
        from time import perf_counter

        started = perf_counter()
        result = gateway.for_action(self.workflow.ATTEMPT_ID).complete_result(
            request, provider=Provider.OPENROUTER, model=model
        )
        elapsed = perf_counter() - started
        if isinstance(result, Err):
            failure = dict(
                workflow_id=self.workflow.WORKFLOW_ID,
                status="INFRASTRUCTURE_ERROR",
                failure_class=result.error.code,
                provider_wire=result.error.response_metadata(),
                provider_invocations=1,
                confirmed_provider_calls=None,
                authority_effect="None",
            )
            write_new(output / "failure.json", failure)
            return failure
        outcome = result.value
        candidate = outcome.candidate
        raw = candidate.content.encode("utf-8", errors="surrogatepass")
        record = dict(
            request=wire_request,
            requested_model=model,
            served_model=candidate.model,
            provider=candidate.provider,
            generation_id=candidate.generation_id,
            transport=candidate.transport,
            provider_calls=1,
            prompt_tokens=candidate.input_tokens,
            completion_tokens=candidate.output_tokens,
            cost_usd=candidate.cost_usd,
            accounting_state=outcome.state,
            accounting_binding=gateway.binding,
            identity_error=candidate.model != model or candidate.provider != "openrouter",
            raw_reply_base64=base64.b64encode(outcome.reply_bytes).decode("ascii"),
            raw_reply_sha256=digest(outcome.reply_bytes),
        )
        record["provider_elapsed_seconds"] = elapsed
        return self._finish(output, raw, origin="ACCOUNTED_PROVIDER", provider_record=record)

    def _exit_code(self, result: dict) -> int:
        if result["status"] in {"INFRASTRUCTURE_ERROR", "CHECKER_DEFECT"}:
            return 3
        return 0 if result["failure_class"] == "NONE" else 2

    def main(self, argv: list[str] | None = None) -> int:
        parser = argparse.ArgumentParser(
            description=f"{self.workflow.WORKFLOW_ID}: one agent, one typed response, one stage."
        )
        commands = parser.add_subparsers(dest="command", required=True)
        for command in ("prepare", "run"):
            entry = commands.add_parser(command)
            entry.add_argument("task", type=Path)
            entry.add_argument("--output", type=Path, required=True)
            if command == "run":
                entry.add_argument("--model", required=True)
                entry.add_argument("--max-output-tokens", type=int, required=True)
                financial = entry.add_mutually_exclusive_group(required=True)
                financial.add_argument("--max-cost-microusd", type=int)
                financial.add_argument("--max-estimated-cost-microusd", type=int)
                entry.add_argument("--env-file", type=Path)
                entry.add_argument("--timeout", type=float, default=60.0)
        entry = commands.add_parser("check")
        entry.add_argument("run", type=Path)
        entry.add_argument("reply", type=Path)
        entry.add_argument(
            "--fixture", action="store_true", help="Label a hand-authored offline control"
        )
        entry = commands.add_parser("replay")
        entry.add_argument("run", type=Path)
        args = parser.parse_args(argv)
        try:
            if args.command in {"prepare", "run"}:
                if args.command == "run":
                    limit = args.max_estimated_cost_microusd or args.max_cost_microusd
                    if type(limit) is not int or not 0 < limit <= 4999:
                        raise ValueError(f"{self.workflow.WORKFLOW_ID}_BUDGET_MUST_NOT_EXCEED_4999")
                spec = self.workflow.validate_task(self._read_json(args.task))
                prepared = self.prepare_run(spec, args.output)
                if args.command == "prepare":
                    result = dict(
                        status="PREPARED",
                        output=str(args.output),
                        provider_calls=0,
                        binding=prepared["binding"],
                        authority_effect="None",
                    )
                    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
                    return 0
                from pfp.infrastructure.workflow_accounting import (
                    create_accounted_openrouter_gateway,
                )

                try:
                    gateway = create_accounted_openrouter_gateway(
                        args.model,
                        args.max_output_tokens,
                        env_file=args.env_file,
                        max_cost_microusd=args.max_cost_microusd,
                        max_estimated_cost_microusd=args.max_estimated_cost_microusd,
                        max_calls=1,
                        accounting_path=args.output / "accounting.sqlite3",
                        run_id=f"{self.workflow.FOLDER}:" + args.output.resolve().name,
                        objective_sha256=prepared["binding"]["input_sha256"],
                        timeout=args.timeout,
                    )
                except (OSError, ValueError, RuntimeError) as exc:
                    failure = dict(
                        workflow_id=self.workflow.WORKFLOW_ID,
                        status="INFRASTRUCTURE_ERROR",
                        failure_class=str(exc),
                        provider_calls=0,
                        authority_effect="None",
                    )
                    write_new(args.output / "failure.json", failure)
                    print(json.dumps(failure, sort_keys=True))
                    return 3
                result = self.run_accounted(
                    spec,
                    args.output,
                    gateway=gateway,
                    model=args.model,
                    max_output_tokens=args.max_output_tokens,
                )
            elif args.command == "check":
                result = self.check_run(args.run, args.reply, fixture=args.fixture)
            else:
                result = self.replay_run(args.run)
            print(json.dumps(result, ensure_ascii=True, sort_keys=True))
            return self._exit_code(result)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(
                json.dumps(
                    dict(
                        workflow_id=self.workflow.WORKFLOW_ID,
                        status="REFUSED",
                        reason=str(exc),
                        authority_effect="None",
                    ),
                    sort_keys=True,
                )
            )
            return 2
