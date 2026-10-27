"""OEEIS pharmacy as the Adversary immune port.

Composting farms bout blockers into the pharmacy as CANDIDATE antibodies; nothing here
admits one. Guidance is read only from human-admitted antibodies. This is the only Adversary
module that imports the Epistemic Immune System.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from eis.domain.pharmacy_catalog import (
    PharmacyCatalogRepository,
)
from eis.domain.pharmacy_models import PharmacyStatus
from eis.domain.pharmacy_seeder import PharmacySeeder
from eis.domain.thymus import CandidateDetector, ThymusGate
from eis.use_cases.admitted_antibody_query import (
    admitted_antibodies,
)
from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from adversary.domain.estate_ports import AdmittedGuidanceV1
from adversary.domain.evidence import CandidateCheckV1, CheckerVerdict, sha256_ref
from adversary.domain.ports import CandidateCheckerPort
from adversary.domain.specialization import PortName

from .probe_support import observed, refusal, run_probe

_LOCUS = "adversary.infrastructure.estates.oeeis_immune"
_PROBE_DEFECT = "CONNECTION_PROBE: a witness was cited without a replay hash"

DEFAULT_SELF_PANEL: tuple[str, ...] = (
    "# Clean reference fixture 1: Exact rational calculation\nfrom fractions import Fraction\nx = Fraction(1, 2)\n",
    "# Clean reference fixture 2: Bounded lattice model\ndef compute_chain(k: int) -> int:\n    return k * 2\n",
    "# Clean reference fixture 3: Hedged discrete state transition\ndef step(state: dict) -> dict:\n    return {'step': state.get('step', 0) + 1}\n",
)


@dataclass(frozen=True, slots=True)
class AntibodyViolationV1:
    antibody_id: str
    failure_class: str
    action: str
    severity: str
    matched_text: str
    authority_effect: str = "None"


@dataclass(frozen=True, slots=True)
class AdmittedAntibodyEvaluationV1:
    is_valid: bool
    antibodies_screened: tuple[str, ...]
    violations: tuple[AntibodyViolationV1, ...]
    self_tolerance_certified: bool
    authority_effect: str = "None"


class OeeisImmuneAdapter:
    estate = EstateName.OEEIS
    port = PortName.IMMUNE_ANTIBODIES
    adapter_id = "oeeis.pharmacy_seeder"

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = Path(repo_root)

    def record_candidates(
        self, defects: Sequence[str], *, run_id: str, task_id: str
    ) -> Result[tuple[str, ...], Refusal]:
        try:
            farmed = PharmacySeeder(repo_root=self.repo_root).farm_antibodies_from_defects(
                tuple(defects), run_id=run_id, task_id=task_id
            )
        except (OSError, TypeError, ValueError) as exc:
            return Err(refusal("OEEIS_COMPOST_FAILED", exc, _LOCUS))
        return Ok(tuple(antibody.antibody_id for antibody in farmed))

    def admitted_guidance(self) -> Result[AdmittedGuidanceV1, Refusal]:
        # Read the catalog file directly: constructing the repository creates directories.
        catalog_file = PharmacyCatalogRepository.catalog_path(self.repo_root)
        try:
            catalog = (
                json.loads(catalog_file.read_text(encoding="utf-8"))
                if catalog_file.is_file()
                else {}
            )
        except (OSError, ValueError) as exc:
            return Err(refusal("OEEIS_CATALOG_UNREADABLE", exc, _LOCUS))
        if not isinstance(catalog, dict):
            return Err(
                Refusal("OEEIS_CATALOG_UNREADABLE", "the pharmacy catalog is not an object", _LOCUS)
            )
        query = admitted_antibodies(catalog)
        return Ok(
            AdmittedGuidanceV1(
                lines=tuple(f"{ab.antibody_id}: {ab.description}" for ab in query.admitted),
                malformed_ids=query.malformed_ids,
            )
        )

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        def body() -> ConnectionReceiptV1:
            root = Path(scratch_root)
            farmed = PharmacySeeder(repo_root=root).farm_antibodies_from_defects(
                (_PROBE_DEFECT,), run_id="connection-probe", task_id="connection-probe"
            )
            if len(farmed) != 1:
                return disconnected(self.estate, self.port, self.adapter_id, "no candidate farmed")
            repository = PharmacyCatalogRepository(root)
            entry = repository.load_catalog().get("antibodies", {}).get(farmed[0].antibody_id)
            if not entry or entry.get("pharmacy_status") != PharmacyStatus.CANDIDATE.value:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "farmed antibody not read back"
                )
            if admitted_antibodies(repository.load_catalog()).admitted:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "a candidate read as admitted"
                )
            return observed(
                self.estate,
                self.port,
                self.adapter_id,
                repository.catalog_file.read_bytes(),
                "farmed one CANDIDATE, read it back, admitted query returned none",
            )

        return run_probe(self.estate, self.port, self.adapter_id, body)

    def validate_candidate_against_yaml_specs(
        self,
        candidate_bytes: bytes,
        *,
        specs_dir: Path | None = None,
        self_panel: Sequence[str] | None = None,
    ) -> Result[AdmittedAntibodyEvaluationV1, Refusal]:
        """Validates candidate proposal bytes against admitted YAML antibodies via ThymusGate."""
        if specs_dir is not None:
            resolved_specs = Path(specs_dir).resolve()
        else:
            resolved_specs = (
                self.repo_root / "eis" / "domain" / "specs"
            )
            if not resolved_specs.is_dir():
                resolved_specs = (
                    Path(__file__).resolve().parents[4]
                    / "eis"
                    / "domain"
                    / "specs"
                )

        if not resolved_specs.is_dir():
            return Err(
                Refusal(
                    "OEEIS_SPECS_DIR_NOT_FOUND",
                    f"Specification directory not found: {resolved_specs}",
                    _LOCUS,
                )
            )

        panel = tuple(self_panel) if self_panel is not None else DEFAULT_SELF_PANEL
        thymus = ThymusGate(self_panel=panel)

        screened: list[str] = []
        violations: list[AntibodyViolationV1] = []
        candidate_text = candidate_bytes.decode("utf-8", errors="replace")

        yaml_files = sorted(resolved_specs.glob("*.yaml"), key=lambda p: p.name)
        for yf in yaml_files:
            try:
                spec = yaml.safe_load(yf.read_text(encoding="utf-8"))
            except Exception as exc:
                return Err(refusal("OEEIS_SPEC_PARSE_FAILED", exc, _LOCUS))

            if not isinstance(spec, dict):
                continue

            ab_id = str(spec.get("antibody_id", ""))
            target_pattern = str(spec.get("target_pattern", ""))
            if not ab_id or not target_pattern:
                continue

            # 1. Thymic negative selection screening (assert zero cross-reactivity on clean self-fixtures)
            detector = CandidateDetector(pattern=target_pattern, rule_id=ab_id)
            eval_res = thymus.evaluate_candidate(detector)
            if not eval_res.self_tolerant:
                return Err(
                    Refusal(
                        "THYMIC_AUTOIMMUNE_VIOLATION",
                        f"Antibody {ab_id} cross-reacts on clean self-fixtures",
                        _LOCUS,
                    )
                )

            screened.append(ab_id)

            # 2. Screen candidate content
            matches = list(re.finditer(target_pattern, candidate_text))
            for m in matches:
                violations.append(
                    AntibodyViolationV1(
                        antibody_id=ab_id,
                        failure_class=str(spec.get("failure_class", "unknown")),
                        action=str(spec.get("action", "repair")),
                        severity=str(spec.get("severity", "P0")),
                        matched_text=m.group(0),
                    )
                )

        return Ok(
            AdmittedAntibodyEvaluationV1(
                is_valid=len(violations) == 0,
                antibodies_screened=tuple(screened),
                violations=tuple(violations),
                self_tolerance_certified=True,
            )
        )

    def as_candidate_checker(
        self,
        *,
        specs_dir: Path | None = None,
        self_panel: Sequence[str] | None = None,
        checker_id: str = "oeeis.thymus_gate",
    ) -> ThymusGatedCandidateChecker:
        return ThymusGatedCandidateChecker(
            self,
            specs_dir=specs_dir,
            self_panel=self_panel,
            checker_id=checker_id,
        )


class ThymusGatedCandidateChecker(CandidateCheckerPort):
    """CandidateCheckerPort implementation evaluating candidate bytes against admitted YAML antibodies via ThymusGate."""

    def __init__(
        self,
        adapter: OeeisImmuneAdapter,
        *,
        specs_dir: Path | None = None,
        self_panel: Sequence[str] | None = None,
        checker_id: str = "oeeis.thymus_gate",
    ) -> None:
        self.adapter = adapter
        self.specs_dir = specs_dir
        self.self_panel = self_panel
        self.checker_id = checker_id

    def check_candidate(
        self,
        *,
        run_key: str,
        objective: str,
        candidate_id: str,
        candidate_bytes: bytes,
        carrier_context: Mapping[str, Any] | None,
    ) -> Result[CandidateCheckV1, Refusal]:
        del carrier_context
        eval_res = self.adapter.validate_candidate_against_yaml_specs(
            candidate_bytes,
            specs_dir=self.specs_dir,
            self_panel=self.self_panel,
        )
        if eval_res.is_err:
            return Err(eval_res.unwrap_err())
        evaluation = eval_res.unwrap()

        receipt_payload = {
            "schema": "core.adversary.thymus_check.v1",
            "run_key": run_key,
            "objective": objective,
            "candidate_id": candidate_id,
            "is_valid": evaluation.is_valid,
            "self_tolerance_certified": evaluation.self_tolerance_certified,
            "antibodies_screened": list(evaluation.antibodies_screened),
            "violations": [
                {
                    "antibody_id": v.antibody_id,
                    "failure_class": v.failure_class,
                    "severity": v.severity,
                    "matched_text": v.matched_text,
                }
                for v in evaluation.violations
            ],
            "authority_effect": "None",
        }
        receipt_bytes = json.dumps(receipt_payload, sort_keys=True, indent=2).encode("utf-8")
        receipt_sha256 = sha256_ref(receipt_bytes)
        content_sha256 = sha256_ref(candidate_bytes)

        if evaluation.is_valid:
            return Ok(
                CandidateCheckV1(
                    verdict=CheckerVerdict.ACCEPTED,
                    candidate_id=candidate_id,
                    candidate_content_sha256=content_sha256,
                    checker_id=self.checker_id,
                    checker_receipt_sha256=receipt_sha256,
                    checker_receipt_bytes=receipt_bytes,
                    reason=f"Cleared all {len(evaluation.antibodies_screened)} admitted YAML antibodies via ThymusGate",
                )
            )
        else:
            viol_ids = ", ".join(v.antibody_id for v in evaluation.violations)
            return Ok(
                CandidateCheckV1(
                    verdict=CheckerVerdict.REJECTED,
                    candidate_id=candidate_id,
                    candidate_content_sha256=content_sha256,
                    checker_id=self.checker_id,
                    checker_receipt_sha256=receipt_sha256,
                    checker_receipt_bytes=receipt_bytes,
                    reason=f"Rejected by ThymusGate for {len(evaluation.violations)} antibody violations: {viol_ids}",
                )
            )


__all__ = [
    "OeeisImmuneAdapter",
    "ThymusGatedCandidateChecker",
    "AntibodyViolationV1",
    "AdmittedAntibodyEvaluationV1",
]

