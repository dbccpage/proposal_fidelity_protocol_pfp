"""Execution composition root with an explicitly unavailable default evaluator."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from omega_engine_operads.application.ddc_execution.meta_operad_engine import (
    MetaOperadEngineUseCase,
)
from omega_engine_operads.domain.ddc_execution.errors import (
    OperadDomainError,
    Refusal,
)
from omega_engine_operads.domain.ddc_execution.execution import EvaluationOutcome
from omega_engine_operads.domain.operad.errors import Err, Result

from .registry import FileOperadRegistry
from .trace_storage import FileTraceStorage


def find_repo_root(start: Path | None = None) -> Path:
    initial = (start or Path.cwd()).resolve()
    for candidate in (initial, *initial.parents):
        if (candidate / ".git").exists() and (
            candidate / "omega_engine_operads"
        ).is_dir():
            return candidate
    raise Refusal("OPERAD_ROOT_UNAVAILABLE", f"No repository marker above {initial}")


def compute_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


class FileArtifactCustody:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def verify(self, path: str, sha256: str) -> None:
        artifact = Path(path)
        if not artifact.is_absolute():
            artifact = self.repo_root / artifact
        try:
            artifact.resolve().relative_to(self.repo_root.resolve())
            if compute_file_sha256(artifact) != sha256:
                raise ValueError("artifact digest does not match evaluator observation")
        except (OSError, ValueError) as exc:
            raise Refusal("MORPHISM_ARTIFACT_UNAVAILABLE", f"{path}: {exc}") from exc


class NullMorphismEvaluator:
    def is_bound(self, skill_id: str) -> bool:
        return False

    def evaluate(
        self, skill_id: str, inputs: Sequence[str], output_hint: str | None = None
    ) -> Result[EvaluationOutcome, OperadDomainError]:
        return Err(
            Refusal("NOT_EXECUTABLE", f"No evaluator is bound for {skill_id!r}")
        )


def build_meta_operad_engine(repo_root: Path | None = None) -> MetaOperadEngineUseCase:
    root = repo_root or find_repo_root()
    return MetaOperadEngineUseCase(
        registry=FileOperadRegistry(root),
        traces=FileTraceStorage(root),
        evaluator=NullMorphismEvaluator(),
        artifacts=FileArtifactCustody(root),
        clock=lambda: datetime.now(timezone.utc).isoformat(),
    )
