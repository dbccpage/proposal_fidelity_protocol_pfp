"""A supplied patch and fixed local commands in a fresh working copy.

This is working-copy isolation, not an OS security sandbox. Commands are trusted,
host-selected argv vectors, without a shell. No provider client or publisher is
configured; hosts must choose offline checks. Check success is finite evidence,
not a theorem, and the original source is never patched by the runner.
"""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
from pathlib import Path

from omega_engine_operads.application.queries.validate_workflows import ValidateWorkflowsHandler
from omega_engine_operads.application.typed_workflow_compiler import compile_typed_workflow
from omega_engine_operads.contracts.ddc_code_repair_v1 import (
    EXECUTOR_METHODS,
    CheckObservationV1,
    CodeRepairRequestV1,
    RepairRefusalV1,
    RepairStateV1,
    RepairTerminalV1,
    assess,
    canonical,
    relative_file,
    sha256,
)
from omega_engine_operads.domain.value_objects.content_digest import ContentDigest
from omega_engine_operads.infrastructure.ddc_code_repair import EFFECTS, load_code_repair_family
from omega_engine_operads.skill_operad.resolver.native_runtime import run_native
from omega_engine_operations.domain.rop.result import Err
from omega_engine_woland.domain.estate_ports import PromptGenealogyPort
from omega_engine_woland.domain.evidence import CandidateCheckV1
from omega_engine_woland.domain.ports import CandidateCheckerPort, LearningCompletionPort


class RepairFailure(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _local_process_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_NAMESPACE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG",
        "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
        "PYTHONPYCACHEPREFIX", "PYTHONOPTIMIZE",
    ):
        environment.pop(name, None)
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                       PYTHONDONTWRITEBYTECODE="1")
    return environment


def _no_links(path: Path) -> None:
    for part in (path, *path.parents):
        if not part.exists() and not part.is_symlink():
            continue
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise RepairFailure("SOURCE_LINK_REFUSED", str(part))


class CodeRepairRuntime:
    def __init__(
        self, request: CodeRepairRequestV1, source_root: Path, run_directory: Path, *,
        repo_root: Path, immune_checker: CandidateCheckerPort,
        genealogy: PromptGenealogyPort, learning: LearningCompletionPort | None = None,
        check_runner=None,
    ):
        self.request = CodeRepairRequestV1.model_validate_json(request.model_dump_json())
        self.source_root, self.run_directory = source_root.absolute(), run_directory.absolute()
        self.workspace = self.run_directory / "workspace"
        self.repo_root, self.immune_checker, self.genealogy, self.learning = repo_root, immune_checker, genealogy, learning
        self.request_digest = sha256(canonical(self.request.model_dump(mode="json")))
        self._owns_run = False
        self.check_runner = check_runner

    def _read(self, base: Path, relative: str) -> bytes:
        path = base / relative_file(relative)
        _no_links(path)
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > 2 * 1024 * 1024:
            raise RepairFailure("SOURCE_FILE_REFUSED", relative)
        return path.read_bytes()

    def _verify(self, base: Path, manifest: dict[str, str]) -> None:
        for name, expected in manifest.items():
            if hashlib.sha256(self._read(base, name)).hexdigest() != expected:
                raise RepairFailure("SOURCE_CHANGED", name)

    def _ensure_run(self) -> None:
        _no_links(self.run_directory)
        if (self.run_directory == self.source_root or self.run_directory.is_relative_to(self.source_root)
                or self.source_root.is_relative_to(self.run_directory)):
            raise RepairFailure("OUTPUT_SCOPE_REFUSED", "run directory must be outside the source tree")
        if not self._owns_run:
            if self.run_directory.exists():
                raise RepairFailure("OUTPUT_CONFLICT", str(self.run_directory))
            self.run_directory.mkdir(parents=True, exist_ok=False)
            self._owns_run = True

    def _write(self, name: str, raw: bytes) -> None:
        _no_links(self.run_directory / name)
        with (self.run_directory / name).open("xb") as stream:
            stream.write(raw)

    def _state(self, value: dict, expected: str) -> RepairStateV1:
        state = RepairStateV1.model_validate_json(canonical(value))
        if (state.phase != expected or state.run_key != self.request.run_key
                or state.candidate_id != self.request.candidate_id
                or state.request_digest != self.request_digest
                or state.source_root != str(self.source_root)):
            raise RepairFailure("STATE_BINDING_MISMATCH", expected)
        if state.refusal is None and state.source_manifest != self.request.sources:
            raise RepairFailure("STATE_BINDING_MISMATCH", "source manifest")
        return state

    def _advance(self, value, expected, phase, action, *, retain_refusal=False):
        state = self._state(value, expected)
        updates = {}
        if state.refusal is None or retain_refusal:
            try:
                updates = action(state)
            except (RepairFailure, OSError) as error:
                updates = {"refusal": RepairRefusalV1(
                    code=getattr(error, "code", "IO_UNAVAILABLE"), message=str(error)
                )}
        result = state.model_copy(update={"phase": phase, **updates})
        return RepairStateV1.model_validate_json(result.model_dump_json()).model_dump(mode="json")

    def capture(self, value):
        request = CodeRepairRequestV1.model_validate_json(canonical(value))
        if request != self.request:
            raise RepairFailure("REQUEST_BINDING_MISMATCH", "host-selected request differs")
        state = RepairStateV1(
            run_key=request.run_key, candidate_id=request.candidate_id,
            request_digest=self.request_digest, source_root=str(self.source_root), phase="captured",
        )
        try:
            raw_files = {name: self._read(self.source_root, name) for name in request.sources}
            if any(hashlib.sha256(raw).hexdigest() != request.sources[name] for name, raw in raw_files.items()):
                raise RepairFailure("SOURCE_CHANGED", "capture differs from the supplied manifest")
            self._ensure_run()
            self.workspace.mkdir()
            for name, raw in raw_files.items():
                target = self.workspace / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            initialized = subprocess.run(
                ["git", "-c", "core.longpaths=true", "-c", "init.defaultBranch=codex/ddc-local",
                 "init", "--quiet", "--template=", str(self.workspace)],
                env=_local_process_environment(), capture_output=True, timeout=20, check=False,
            )
            if initialized.returncode:
                raise RepairFailure("GIT_UNAVAILABLE", initialized.stderr.decode("utf-8", "replace"))
            self._write("request.json", canonical(request.model_dump(mode="json")))
            self._write("candidate.patch", request.candidate_patch.encode("utf-8"))
            state = state.model_copy(update={"source_manifest": dict(request.sources)})
        except (RepairFailure, OSError, subprocess.TimeoutExpired) as error:
            state = state.model_copy(update={"refusal": RepairRefusalV1(
                code=getattr(error, "code", "CAPTURE_UNAVAILABLE"), message=str(error)
            )})
        return state.model_dump(mode="json")

    def _checks(self, manifest):
        observations = []
        for check in self.request.checks:
            self._verify(self.workspace, manifest)
            try:
                result = (self.check_runner(check, self.workspace) if self.check_runner is not None else
                    subprocess.run(check.argv, cwd=self.workspace, env=_local_process_environment(), capture_output=True,
                                   timeout=check.timeout_seconds, check=False))
            except (OSError, subprocess.TimeoutExpired) as error:
                raise RepairFailure("CHECK_UNAVAILABLE", f"{check.check_id}: {error}") from error
            self._verify(self.workspace, manifest)
            observations.append(CheckObservationV1(
                check_id=check.check_id, argv=check.argv, returncode=result.returncode,
                stdout=result.stdout[:65536].decode("utf-8", "replace"),
                stderr=result.stderr[:65536].decode("utf-8", "replace"),
                stdout_sha256=sha256(result.stdout), stderr_sha256=sha256(result.stderr),
                stdout_truncated=len(result.stdout) > 65536, stderr_truncated=len(result.stderr) > 65536,
            ))
        return tuple(observations)

    def observe(self, value):
        def action(state):
            self._verify(self.source_root, state.source_manifest)
            return {"baseline": self._checks(state.source_manifest)}
        return self._advance(value, "captured", "observed", action)

    def _git_apply(self, *arguments):
        environment = _local_process_environment()
        try:
            result = subprocess.run(
                ["git", "-c", "core.longpaths=true", f"--git-dir={self.workspace / '.git'}",
                 f"--work-tree={self.workspace}", "apply", *arguments, "-"],
                cwd=self.workspace, env=environment, input=self.request.candidate_patch.encode("utf-8"),
                capture_output=True, timeout=20, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RepairFailure("PATCH_UNAVAILABLE", str(error)) from error
        if result.returncode:
            raise RepairFailure("PATCH_REFUSED", result.stderr[:4096].decode("utf-8", "replace"))
        return result.stdout

    def _patch_paths(self):
        unsupported = ("new file mode ", "deleted file mode ", "old mode ", "new mode ",
                       "rename from ", "rename to ", "copy from ", "copy to ", "GIT binary patch", "Binary files ")
        if any(line.startswith(unsupported) for line in self.request.candidate_patch.splitlines()):
            raise RepairFailure("PATCH_SCOPE_REFUSED", "only existing-file text edits are supported")
        paths = []
        raw_stat = self._git_apply("--numstat", "-z")
        try:
            for row in filter(None, raw_stat.decode("utf-8").split("\0")):
                added, deleted, path = row.split("\t", 2)
                relative_file(path)
                if added == "-" or deleted == "-" or path not in self.request.write_paths:
                    raise RepairFailure("PATCH_SCOPE_REFUSED", path)
                paths.append(path)
        except ValueError as error:
            raise RepairFailure("PATCH_SCOPE_REFUSED", str(error)) from error
        if not paths:
            raise RepairFailure("PATCH_SCOPE_REFUSED", "patch has no declared file edits")
        return tuple(sorted(set(paths)))

    def evaluate(self, value):
        def action(state):
            self._verify(self.source_root, state.source_manifest)
            if all(row.returncode == 0 for row in state.baseline):
                return {"after": state.baseline}
            self._patch_paths()
            self._git_apply("--check", "--whitespace=nowarn")
            self._git_apply("--whitespace=nowarn")
            after_manifest = {
                name: hashlib.sha256(self._read(self.workspace, name)).hexdigest()
                for name in self.request.sources
            }
            changed = tuple(name for name in after_manifest if after_manifest[name] != state.source_manifest[name])
            if not set(changed) <= set(self.request.write_paths):
                raise RepairFailure("PATCH_SCOPE_REFUSED", "patch changed a read-only source")
            return {"changed_paths": changed, "after": self._checks(after_manifest)}
        return self._advance(value, "observed", "evaluated", action)

    def incorporate(self, value):
        def action(state):
            if state.refusal is None:
                self._verify(self.source_root, state.source_manifest)
            self._ensure_run()
            residuals = []
            checked = self.immune_checker.check_candidate(
                run_key=state.run_key, objective=self.request.objective,
                candidate_id=state.candidate_id, candidate_bytes=self.request.candidate_patch.encode("utf-8"),
                carrier_context={"request_digest": state.request_digest, "source_manifest": state.source_manifest},
            )
            immune = {"run_key": state.run_key, "candidate_id": state.candidate_id}
            if isinstance(checked, Err):
                immune["refusal"] = checked.error.code
                residuals.append("IMMUNE_UNAVAILABLE")
            elif (not isinstance(checked.value, CandidateCheckV1)
                    or not checked.value.binds(state.candidate_id, (state.candidate_id,))):
                immune["refusal"] = "IMMUNE_BINDING_MISMATCH"
                residuals.append("IMMUNE_BINDING_MISMATCH")
            else:
                immune["observation"] = checked.value.to_dict()
            defects = tuple(row.check_id for row in state.after if row.returncode != 0)
            lineage = self.genealogy.record_lineage(
                "run:" + state.run_key, "candidate:" + state.run_key + ":" + state.candidate_id,
                defects, canonical({"run_key": state.run_key, "candidate_id": state.candidate_id,
                                   "request_digest": state.request_digest,
                                   "source_manifest_digest": sha256(canonical(state.source_manifest)),
                                   "outcome": assess(state)}).decode("ascii"),
            )
            lineage_id = None
            if isinstance(lineage, Err):
                residuals.append("LINEAGE_UNAVAILABLE:" + lineage.error.code)
            else:
                lineage_id = lineage.value
            result = {"immune_observation": immune, "lineage_id": lineage_id,
                      "integration_residuals": tuple(residuals)}
            evidence = state.model_copy(update=result).model_dump(mode="json")
            self._write("observations.json", canonical(evidence))
            return result
        return self._advance(value, "evaluated", "incorporated", action, retain_refusal=True)

    def disposition(self, value):
        return self._advance(value, "incorporated", "disposed", lambda state: {"outcome": assess(state)}, retain_refusal=True)

    def terminal(self, value):
        state = self._state(value, "disposed")
        if state.outcome is None:
            raise RepairFailure("TERMINAL_UNBOUND", "disposition missing")
        return RepairTerminalV1(state=state).model_dump(mode="json")

    def bindings(self):
        return {"ddc-code-repair-" + stage.lower(): getattr(self, method)
                for stage, method in EXECUTOR_METHODS}

    def run(self, *, executor_bindings=None):
        executor_digest = ContentDigest.sha256(hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        family = load_code_repair_family(self.repo_root, executor_digest=executor_digest)
        compiled = compile_typed_workflow(
            family.documents, family.workflow, validate_graph=ValidateWorkflowsHandler().handle,
            allowed_effects=EFFECTS,
        )
        native = run_native(
            family.inventory, family.wire, [self.request.model_dump(mode="json")],
            self.bindings() if executor_bindings is None else executor_bindings, {},
        )
        terminal = None if native.refusal else RepairTerminalV1.model_validate_json(canonical(native.output))
        record = {
            "schema_version": "oeop.ddc-code-repair-run.v1", "authority_effect": "None",
            "run_key": self.request.run_key, "candidate_id": self.request.candidate_id,
            "outcome": terminal.state.outcome if terminal else "REFUSED",
            "terminal": terminal.model_dump(mode="json") if terminal else None,
            "native_run": native.to_json(), "workflow_digest": compiled.workflow_digest,
            "plan_digest": compiled.plan.plan_digest, "source_bindings": compiled.plan.source_digests,
            "source_application": "NOT_PERFORMED", "mathematical_measurement": "NOT_MEASURED",
        }
        learning = {"status": "NOT_REQUESTED"}
        if self._owns_run:
            self._write("receipt.json", canonical(record))
            if self.learning is not None:
                try:
                    self.learning.completed(str(self.run_directory), outcome=record["outcome"], origin="ddc-code-repair")
                    learning = {"status": "OBSERVED"}
                except Exception as error:
                    learning = {"status": "UNAVAILABLE", "error": type(error).__name__}
        return {"execution": record, "learning_notification": learning}
