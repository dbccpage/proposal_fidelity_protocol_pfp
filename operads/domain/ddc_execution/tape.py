"""DDC tape receipt and request DTOs independent of persistence."""

from dataclasses import asdict, dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class OperadCompositionReceipt:
    tape_path: str
    run_id: str
    step_count: int
    tape_str: str
    hash_chain_valid: bool
    ddc_laws_valid: bool
    law_violations: tuple[str, ...]
    initial_phi1: str | None
    initial_gamma2: str | None
    terminal_phi1: str | None
    terminal_gamma2: str | None
    initial_residual: str | None
    terminal_residual: str | None
    residual_delta: str | None
    residual_effect: str
    morphism_count: int
    authority_effect: str = "None"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["law_violations"] = list(self.law_violations)
        return value


@dataclass(frozen=True)
class ParseDdcTapeRequest:
    source: str | Sequence[dict[str, Any]]
    output_receipt_path: str | None = None
    persist_evidence: bool = True
    evidence_vault_dir: str | None = None


@dataclass(frozen=True)
class ParseDdcTapeResponse:
    receipt: OperadCompositionReceipt
    evidence_path: str | None = None
    status: str = "SUCCESS"
