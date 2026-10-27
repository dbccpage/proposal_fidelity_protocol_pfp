"""Preserve the implemented workflow DDC parser behind execution-domain ports."""

import json
import os
import re
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

from operating_system.adapters.intelligence_custody.ic_routing import (
    IcMigrationRefusal,
    intelligence_path,
    read_activation,
    safe_path,
)
from operating_system.adapters.intelligence_custody.intelligence_root import (
    IntelligenceRootUnresolvedError,
    resolve_intelligence_repo_root,
)
from operads.application.ddc_execution.parse_ddc_tape_use_case import (
    ParseDdcTapeUseCase,
)
from operads.domain.ddc_execution.errors import (
    OperadDomainError,
    Refusal,
)
from operads.domain.ddc_execution.tape import OperadCompositionReceipt
from operads.domain.operad.errors import Err, Ok, Result
from operads.skill_operad.ddc_operad_parser import DdcOperadParser


def _refusal(error: Any) -> Refusal:
    return Refusal(error.code, error.message, getattr(error, "locus", "ddc_execution"))


class WorkflowDdcTapeParser:
    def parse(
        self, source: str | Sequence[dict[str, Any]]
    ) -> Result[OperadCompositionReceipt, OperadDomainError]:
        result = DdcOperadParser(source).parse()
        if result.is_err:
            return Err(_refusal(result.unwrap_err()))
        return Ok(OperadCompositionReceipt(**asdict(result.unwrap())))

    def compress(self, source: str, **kwargs: Any) -> Result[dict[str, Any], OperadDomainError]:
        result = DdcOperadParser(source).compress_to_operad_signature(**kwargs)
        if result.is_err:
            return Err(_refusal(result.unwrap_err()))
        return Ok(result.unwrap())


class FileDdcReceiptStorage:
    def __init__(self, default_vault_dir: Path | str | None = None) -> None:
        self.default_vault_dir = Path(default_vault_dir) if default_vault_dir else None

    def destination(self, run_id: str, explicit: str | None, vault: str | None) -> str:
        if explicit:
            return str(explicit)
        clean_id = run_id if run_id != "unknown" else "run"
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+", clean_id) or clean_id in (".", ".."):
            raise Refusal("EVIDENCE_EXPORT_ERROR", "Invalid receipt run identifier")
        filename = f"{clean_id}_operad_receipt.json"
        if vault or self.default_vault_dir is not None:
            return str(Path(vault or self.default_vault_dir) / filename)
        try:
            root = resolve_intelligence_repo_root()
            return str(intelligence_path(root, "_intelligence/evidence/ddc_operad_receipts/" + filename))
        except (IcMigrationRefusal, IntelligenceRootUnresolvedError) as exc:
            raise Refusal(exc.code, str(exc)) from exc
        except OSError as exc:
            raise Refusal("EVIDENCE_EXPORT_ERROR", str(exc)) from exc

    def persist(
        self, receipt: OperadCompositionReceipt, path: str
    ) -> Result[str, OperadDomainError]:
        target = Path(path)
        temporary = None
        try:
            absolute = target.absolute()
            if "_ic" in absolute.parts:
                boundary = absolute.parts.index("_ic")
                root = Path(*absolute.parts[:boundary])
                read_activation(root)
                target = safe_path(root, "/".join(absolute.parts[boundary:]))
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(
                    json.dumps(receipt.to_dict(), indent=2, sort_keys=True).encode("utf-8")
                )
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
            return Ok(str(target))
        except IcMigrationRefusal as exc:
            return Err(Refusal(exc.code, str(exc)))
        except (OSError, ValueError) as exc:
            return Err(Refusal("EVIDENCE_EXPORT_ERROR", f"{target}: {exc}"))
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def build_parse_ddc_tape_use_case(
    default_vault_dir: Path | str | None = None,
) -> ParseDdcTapeUseCase:
    return ParseDdcTapeUseCase(
        parser=WorkflowDdcTapeParser(), receipts=FileDdcReceiptStorage(default_vault_dir)
    )
