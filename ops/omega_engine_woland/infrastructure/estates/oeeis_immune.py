"""OEEIS pharmacy as the Woland immune port.

Composting farms bout blockers into the pharmacy as CANDIDATE antibodies; nothing here
admits one. Guidance reads recorded admission status; learned blocking additionally
requires explicit external state, independently observed danger and verified health.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from omega_engine_epistemic_immune_system.domain.external_admission import AdmissionError
from omega_engine_epistemic_immune_system.domain.guard_activation import (
    ActivationRefusal,
    DetectorHitRefV1,
    GuardActivationReceiptV1,
)
from omega_engine_epistemic_immune_system.domain.pharmacy_catalog import (
    PharmacyCatalogRepository,
)
from omega_engine_epistemic_immune_system.domain.pharmacy_models import Antibody, PharmacyStatus
from omega_engine_epistemic_immune_system.domain.pharmacy_seeder import PharmacySeeder
from omega_engine_epistemic_immune_system.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
)
from omega_engine_epistemic_immune_system.domain.ports import DangerSensor
from omega_engine_epistemic_immune_system.domain.safe_pattern import (
    UnsafePatternRefusal,
    compile_safe_pattern,
)
from omega_engine_epistemic_immune_system.domain.thymus import ThymusGate
from omega_engine_epistemic_immune_system.domain.value_objects import DetectorRule
from omega_engine_epistemic_immune_system.use_cases.admitted_antibody_query import (
    admitted_antibodies,
)
from omega_engine_epistemic_immune_system.use_cases.guard_activation import (
    GuardStatePort,
    HostHealthPort,
    activate_learned_guard,
    subject_digest,
)
from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import (
    intelligence_path,
    safe_path,
)
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from omega_engine_woland.domain.estate_ports import AdmittedGuidanceV1
from omega_engine_woland.domain.evidence import CandidateCheckV1, CheckerVerdict, sha256_ref
from omega_engine_woland.domain.ports import CandidateCheckerPort
from omega_engine_woland.domain.specialization import PortName

from .probe_support import observed, refusal, run_probe

_LOCUS = "omega_engine_woland.infrastructure.estates.oeeis_immune"
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
    diagnostic_violations: tuple[AntibodyViolationV1, ...] = ()
    diagnostic_errors: tuple[str, ...] = ()
    activation_receipts: tuple[GuardActivationReceiptV1, ...] = ()
    guard_coverage_verified: bool = False


class OeeisImmuneAdapter:
    estate = EstateName.OEEIS
    port = PortName.IMMUNE_ANTIBODIES
    adapter_id = "oeeis.pharmacy_seeder"

    def __init__(
        self,
        repo_root: Path,
        *,
        guard_bindings: Callable[[str, bytes], tuple[GuardStatePort, HostHealthPort]] | None = None,
        danger_sensor: DangerSensor | None = None,
        profile_digest: str | None = None,
        subject_scope: str = "",
        required_guard_ids: tuple[str, ...] = (),
    ) -> None:
        if type(required_guard_ids) is not tuple or any(
            type(value) is not str or not value.strip() for value in required_guard_ids
        ):
            raise ValueError("required guard identities must be a tuple of nonempty strings")
        if len(set(required_guard_ids)) != len(required_guard_ids):
            raise ValueError("required guard identities must be unique")
        self.repo_root = Path(repo_root)
        self.guard_bindings = guard_bindings
        self.danger_sensor = danger_sensor
        self.profile_digest = profile_digest
        self.subject_scope = subject_scope
        self._required_guard_ids = required_guard_ids

    @property
    def required_guard_ids(self) -> tuple[str, ...]:
        """Composition-owned coverage; untrusted YAML cannot retire these identities."""
        return self._required_guard_ids

    def record_candidates(
        self, defects: Sequence[str], *, run_id: str, task_id: str
    ) -> Result[tuple[str, ...], Refusal]:
        try:
            if not all(type(value) is str and value.strip() for value in (run_id, task_id)):
                raise ValueError("nonempty run/task identities are required")
            if isinstance(defects, (str, bytes)):
                raise ValueError("defects must be a sequence of strings")
            defect_batch = tuple(defects)
            if any(type(value) is not str for value in defect_batch):
                raise ValueError("defects must be a sequence of strings")
            # Resolve both destinations before the repository creates any directory.
            catalog_file = intelligence_path(
                self.repo_root, "_intelligence/antibodies/pharmacy_catalog.json"
            )
            telemetry_dir = intelligence_path(
                self.repo_root, "_intelligence/archive/telemetry/antibodies"
            )
            repository = PharmacyCatalogRepository(
                self.repo_root,
                catalog_file=catalog_file,
                telemetry_dir=telemetry_dir,
                byte_writer=filesystem_byte_writer,
                byte_source=filesystem_catalog_bytes,
            )
            seeder = PharmacySeeder(repository=repository)
            farmed = seeder.farm_antibodies_from_defects(
                defect_batch, run_id=run_id, task_id=task_id
            )
            self._verify_candidate_readback(seeder.repository, farmed, run_id, task_id)
        except (OSError, TypeError, ValueError) as exc:
            return Err(refusal("OEEIS_COMPOST_FAILED", exc, _LOCUS))
        return Ok(tuple(antibody.antibody_id for antibody in farmed))

    @staticmethod
    def _verify_candidate_source(antibody: Antibody, run_id: str, task_id: str) -> None:
        evidence = hashlib.sha256(
            f"{antibody.antibody_id}:{antibody.target_pattern}:{run_id}:{task_id}".encode("utf-8")
        ).hexdigest()
        if (
            antibody.pharmacy_status != PharmacyStatus.CANDIDATE.value
            or antibody.authority_effect != "None"
            or antibody.source_run_id != run_id
            or antibody.source_task_id != task_id
            or antibody.evidence_sha256 != evidence
        ):
            raise ValueError("farmed candidate does not bind this run/task evidence")

    @classmethod
    def _verify_candidate_readback(
        cls,
        repository: PharmacyCatalogRepository,
        farmed: Sequence[Antibody],
        run_id: str,
        task_id: str,
    ) -> None:
        if not farmed:
            return
        entries = repository.load_catalog().get("antibodies", {})
        # Repeated observations share an id; the final record has the latest count.
        records = {antibody.antibody_id: antibody for antibody in farmed}
        for antibody in records.values():
            cls._verify_candidate_source(antibody, run_id, task_id)
            expected = antibody.to_dict()
            if entries.get(antibody.antibody_id) != expected:
                raise ValueError("candidate catalog readback differs from the farmed record")
            payload = repository.candidates_dir / f"{antibody.antibody_id}.json"
            expected_bytes = json.dumps(expected, indent=2).encode("utf-8")
            if (
                hashlib.sha256(payload.read_bytes()).digest()
                != hashlib.sha256(expected_bytes).digest()
            ):
                raise ValueError("candidate payload readback differs from the farmed bytes")

    @staticmethod
    def admitted_regression_antibodies(
        catalog: Mapping[str, Any],
    ) -> Result[tuple[Antibody, ...], Refusal]:
        """Use the pharmacy's existing human-admission policy for regression screens."""
        try:
            entries = catalog.get("antibodies", {})
            if not isinstance(entries, Mapping) or any(
                not isinstance(row, Mapping) for row in entries.values()
            ):
                raise ValueError("pharmacy antibody entries must be objects")
            query = admitted_antibodies(catalog)
            if query.malformed_ids:
                raise ValueError("malformed admitted antibodies: " + ", ".join(query.malformed_ids))
            return Ok(query.admitted)
        except (TypeError, ValueError) as exc:
            return Err(refusal("OEEIS_CATALOG_UNREADABLE", exc, _LOCUS))

    def admitted_guidance(self) -> Result[AdmittedGuidanceV1, Refusal]:
        # Read the catalog file directly: constructing the repository creates directories.
        try:
            catalog_file = safe_path(
                self.repo_root,
                "omega_engine_epistemic_immune_system/antibodies/pharmacy_catalog.json",
            )
            if not catalog_file.exists():
                catalog_file = intelligence_path(
                    self.repo_root, "_intelligence/antibodies/pharmacy_catalog.json"
                )
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
        selected = self.admitted_regression_antibodies(catalog)
        if isinstance(selected, Err):
            return selected
        return Ok(
            AdmittedGuidanceV1(
                lines=tuple(f"{ab.antibody_id}: {ab.description}" for ab in selected.value),
                malformed_ids=(),
            )
        )

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        def body() -> ConnectionReceiptV1:
            root = Path(scratch_root)
            farmed = OeeisImmuneAdapter(root).record_candidates(
                (_PROBE_DEFECT,), run_id="connection-probe", task_id="connection-probe"
            )
            if isinstance(farmed, Err):
                return disconnected(self.estate, self.port, self.adapter_id, str(farmed.error))
            if len(farmed.value) != 1:
                return disconnected(self.estate, self.port, self.adapter_id, "no candidate farmed")
            catalog_file = intelligence_path(root, "_intelligence/antibodies/pharmacy_catalog.json")
            catalog = json.loads(catalog_file.read_bytes())
            entry = catalog.get("antibodies", {}).get(farmed.value[0])
            if not entry or entry.get("pharmacy_status") != PharmacyStatus.CANDIDATE.value:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "farmed antibody not read back"
                )
            if admitted_antibodies(catalog).admitted:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "a candidate read as admitted"
                )
            return observed(
                self.estate,
                self.port,
                self.adapter_id,
                catalog_file.read_bytes(),
                "farmed one CANDIDATE, read it back, admitted query returned none",
            )

        return run_probe(self.estate, self.port, self.adapter_id, body)

    @staticmethod
    def _yaml_spec(raw: bytes) -> dict[str, Any]:
        """Decode operative fields without duplicate-key or type coercion."""

        class UniqueLoader(yaml.SafeLoader):
            pass

        def unique(loader, node):
            result = {}
            for key, value in loader.construct_pairs(node):
                if type(key) is not str or key in result:
                    raise ValueError("antibody YAML keys must be unique strings")
                result[key] = value
            return result

        UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique)
        spec = yaml.load(raw.decode("utf-8", errors="strict"), Loader=UniqueLoader)
        if type(spec) is not dict or spec.get("schema_version") != "omega.immune.antibody-spec.v1":
            raise ValueError("unsupported antibody specification")
        if any(
            type(spec.get(key)) is not str or not spec[key]
            for key in ("antibody_id", "target_pattern")
        ):
            raise ValueError("antibody id and pattern must be nonempty strings")
        for key in ("failure_class", "action", "severity", "canonical_name"):
            if key in spec and type(spec[key]) is not str:
                raise ValueError(f"antibody {key} must be a string")
        if spec.get("authority_effect") != "None":
            raise ValueError("antibody specification carries authority")
        if spec.get("pharmacy_status", "candidate") not in {
            "candidate",
            "admitted",
            "rejected",
            "retired",
        }:
            raise ValueError("unknown pharmacy status")
        return spec

    def validate_candidate_against_yaml_specs(
        self,
        candidate_bytes: bytes,
        *,
        specs_dir: Path | None = None,
        self_panel: Sequence[str] | None = None,
    ) -> Result[AdmittedAntibodyEvaluationV1, Refusal]:
        """Screen diagnostics; only externally admitted, healthy guards may veto.

        The composition-supplied binding callback must open the existing admission
        state and health verifier for this exact specification's raw bytes. YAML
        status, self tolerance and caller context supply no admission capability.
        Composition must name every required guard. An empty expected set is inert;
        a missing, duplicate or changed required specification refuses coverage.
        """
        resolved_specs = (
            Path(specs_dir)
            if specs_dir is not None
            else self.repo_root / "omega_engine_epistemic_immune_system/antibodies/specs"
        )
        if not resolved_specs.is_dir():
            return Err(
                Refusal(
                    "OEEIS_SPECS_DIR_NOT_FOUND",
                    f"Specification directory not found: {resolved_specs}",
                    _LOCUS,
                )
            )
        configured = (
            self.guard_bindings is not None
            and self.danger_sensor is not None
            and type(self.profile_digest) is str
            and re.fullmatch(r"sha256:[0-9a-f]{64}", self.profile_digest) is not None
            and type(self.subject_scope) is str
            and bool(self.subject_scope)
            and bool(self.required_guard_ids)
        )
        screened: list[str] = []
        violations: list[AntibodyViolationV1] = []
        diagnostics: list[AntibodyViolationV1] = []
        errors: list[str] = []
        activations: list[GuardActivationReceiptV1] = []
        held = False
        try:
            if type(candidate_bytes) is not bytes:
                raise TypeError("candidate content must be exact bytes")
            text = candidate_bytes.decode("utf-8", errors="strict")
            panel = tuple(self_panel) if self_panel is not None else DEFAULT_SELF_PANEL
            thymus = ThymusGate(self_panel=panel)
            identities: set[str] = set()
            specs: list[tuple[dict[str, Any], bytes]] = []
            for path in sorted(resolved_specs.glob("*.yaml"), key=lambda item: item.name):
                raw = path.read_bytes()
                spec = self._yaml_spec(raw)
                spec_id = spec["antibody_id"]
                if spec_id in identities:
                    raise ValueError("duplicate antibody identity")
                identities.add(spec_id)
                specs.append((spec, raw))
            missing = set(self.required_guard_ids) - identities
            if missing:
                raise ValueError("missing required guards: " + ", ".join(sorted(missing)))
            for spec, raw in specs:
                spec_id = spec["antibody_id"]
                status = spec.get("pharmacy_status", "candidate")
                required = spec_id in self.required_guard_ids
                if not required and status in {"rejected", "retired"}:
                    continue
                # Verify required raw bytes before trusting any YAML status or pattern.
                if required and configured:
                    state, health = self.guard_bindings(spec_id, raw)
                    if not all(
                        callable(getattr(state, name, None))
                        for name in ("is_externally_admitted", "is_suspended")
                    ) or not callable(getattr(health, "require_healthy", None)):
                        raise TypeError("guard bindings must supply state and host-health ports")
                    if status != "admitted":
                        raise ValueError("required guard metadata is not admitted")
                try:
                    pattern = compile_safe_pattern(spec["target_pattern"])
                except UnsafePatternRefusal as exc:
                    if required and configured:
                        raise
                    errors.append(f"{spec_id}: {exc.code}")
                    held = held or required
                    continue
                matches = tuple(pattern.finditer(text))
                findings = tuple(
                    AntibodyViolationV1(
                        antibody_id=spec_id,
                        failure_class=spec.get("failure_class", "unknown"),
                        action=spec.get("action", "repair"),
                        severity=spec.get("severity", "P0"),
                        matched_text=match.group(0),
                    )
                    for match in matches
                )
                if not required or not configured:
                    diagnostics.extend(findings)
                    held = held or required
                    continue
                admitted = state.is_externally_admitted(spec_id, self.subject_scope)
                suspended = state.is_suspended(spec_id, self.subject_scope)
                if type(admitted) is not bool or type(suspended) is not bool:
                    raise TypeError("guard state must return exact booleans")
                if not admitted or suspended:
                    held = True
                    diagnostics.extend(findings)
                    continue
                tolerance = thymus.evaluate_rule(
                    DetectorRule(spec_id, spec_id, spec["target_pattern"])
                )
                if not tolerance.is_admitted:
                    return Err(refusal("THYMIC_AUTOIMMUNE_VIOLATION", tolerance.rationale, _LOCUS))
                # Even a clean candidate needs a fresh, subject-bound health observation.
                health.require_healthy(
                    spec_id, self.subject_scope, subject_digest(text), self.profile_digest
                )
                screened.append(spec_id)
                if matches:
                    hit = DetectorHitRefV1(
                        hit_id=sha256_ref(
                            json.dumps(
                                {
                                    "spec_id": spec_id,
                                    "rule_digest": sha256_ref(raw),
                                    "subject_id": subject_digest(text),
                                    "match": matches[0].group(0),
                                },
                                sort_keys=True,
                            ).encode()
                        ),
                        spec_id=spec_id,
                        failure_code=spec.get("failure_class", "guard_match"),
                        subject_id=subject_digest(text),
                    )
                    try:
                        activation = activate_learned_guard(
                            self.profile_digest,
                            spec_id,
                            hit,
                            text,
                            subject_scope=self.subject_scope,
                            sensor=self.danger_sensor,
                            guard_state=state,
                            host_health=health,
                            disposition="REFUSE",
                        )
                    except ActivationRefusal as exc:
                        if exc.code == "NO_DANGER_SIGNAL":
                            diagnostics.extend(findings)
                            continue
                        raise
                    activations.append(activation)
                    violations.extend(findings)
        except (
            OSError,
            TypeError,
            ValueError,
            yaml.YAMLError,
            AdmissionError,
            ActivationRefusal,
        ) as exc:
            return Err(refusal("OEEIS_GUARD_UNVERIFIED", exc, _LOCUS))
        return Ok(
            AdmittedAntibodyEvaluationV1(
                is_valid=not violations,
                antibodies_screened=tuple(screened),
                violations=tuple(violations),
                self_tolerance_certified=bool(screened),
                diagnostic_violations=tuple(diagnostics),
                diagnostic_errors=tuple(errors),
                activation_receipts=tuple(activations),
                guard_coverage_verified=configured
                and set(screened) == set(self.required_guard_ids)
                and not held,
            )
        )

    def as_candidate_checker(
        self,
        *,
        specs_dir: Path | None = None,
        self_panel: Sequence[str] | None = None,
        checker_id: str = "oeeis.thymus_gate",
        challenge_checker: CandidateCheckerPort | None = None,
    ) -> ThymusGatedCandidateChecker:
        return ThymusGatedCandidateChecker(
            self,
            specs_dir=specs_dir,
            self_panel=self_panel,
            checker_id=checker_id,
            challenge_checker=challenge_checker,
        )


class ThymusGatedCandidateChecker(CandidateCheckerPort):
    """An admitted immune veto around a separately supplied challenge checker."""

    def __init__(
        self,
        adapter: OeeisImmuneAdapter,
        *,
        specs_dir: Path | None = None,
        self_panel: Sequence[str] | None = None,
        checker_id: str = "oeeis.thymus_gate",
        challenge_checker: CandidateCheckerPort | None = None,
    ) -> None:
        self.adapter = adapter
        self.specs_dir = specs_dir
        self.self_panel = self_panel
        self.checker_id = checker_id
        self.challenge_checker = challenge_checker

    def check_candidate(
        self,
        *,
        run_key: str,
        objective: str,
        candidate_id: str,
        candidate_bytes: bytes,
        carrier_context: Mapping[str, Any] | None,
    ) -> Result[CandidateCheckV1, Refusal]:
        checked = self.adapter.validate_candidate_against_yaml_specs(
            candidate_bytes,
            specs_dir=self.specs_dir,
            self_panel=self.self_panel,
        )
        if isinstance(checked, Err):
            return checked
        evaluation = checked.value
        if evaluation.violations:
            receipt = json.dumps(
                {
                    "schema": "omega.woland.thymus_check.v2",
                    "run_key": run_key,
                    "objective": objective,
                    "candidate_id": candidate_id,
                    "candidate_content_sha256": sha256_ref(candidate_bytes),
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
                    "activation_receipts": [a.to_dict() for a in evaluation.activation_receipts],
                    "authority_effect": "None",
                },
                sort_keys=True,
            ).encode()
            return Ok(
                CandidateCheckV1(
                    verdict=CheckerVerdict.REJECTED,
                    candidate_id=candidate_id,
                    candidate_content_sha256=sha256_ref(candidate_bytes),
                    checker_id=self.checker_id,
                    checker_receipt_sha256=sha256_ref(receipt),
                    checker_receipt_bytes=receipt,
                    reason="Externally admitted learned guard activated on independent host danger",
                )
            )
        if not evaluation.guard_coverage_verified or self.challenge_checker is None:
            return Ok(
                CandidateCheckV1(
                    verdict=CheckerVerdict.NOT_MEASURED,
                    candidate_id=candidate_id,
                    candidate_content_sha256=sha256_ref(candidate_bytes),
                    checker_id=self.checker_id,
                    reason="Immune diagnostics cannot replace configured admission and an independent challenge checker",
                )
            )
        independent = self.challenge_checker.check_candidate(
            run_key=run_key,
            objective=objective,
            candidate_id=candidate_id,
            candidate_bytes=candidate_bytes,
            carrier_context=carrier_context,
        )
        if isinstance(independent, Err):
            return independent
        if not isinstance(independent, Ok) or not isinstance(independent.value, CandidateCheckV1):
            return Err(
                Refusal("OEEIS_CHALLENGE_CHECK_UNBOUND", "No typed independent verdict", _LOCUS)
            )
        if not independent.value.binds(candidate_id, (sha256_ref(candidate_bytes),)):
            return Err(
                Refusal(
                    "OEEIS_CHALLENGE_CHECK_UNBOUND",
                    "Independent verdict names another candidate",
                    _LOCUS,
                )
            )
        return independent


__all__ = [
    "OeeisImmuneAdapter",
    "ThymusGatedCandidateChecker",
    "AntibodyViolationV1",
    "AdmittedAntibodyEvaluationV1",
]
