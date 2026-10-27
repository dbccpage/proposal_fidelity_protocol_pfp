"""Read-only, fail-closed finding extraction for intelligence sources."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .digestion_models import (
    _LEGACY_DDA_TAPE,
    _NATIVE_BUNDLE_DIGESTS,
    _Extraction,
    _matches_digest,
    _read_object,
    _reject_constant,
    _unique_object,
)


@dataclass(frozen=True)
class _BundleLayout:
    receipt: Mapping[str, Any]
    digests: Mapping[str, str]
    fresh: bool
    legacy: bool


class FindingExtractionOperations:
    @staticmethod
    def _record_list(payload: Mapping[str, Any], keys: Sequence[str], gaps: list[str]) -> list[str]:
        values: list[str] = []
        for key in keys:
            value = payload.get(key, [])
            if value is None:
                continue
            if type(value) is not list:
                gaps.append(f"{key} must be a list when supplied")
                continue
            values.extend(str(item) for item in value if str(item).strip())
        return values

    @staticmethod
    def _string_list(payload: Mapping[str, Any], key: str, location: str,
                     gaps: list[str], prefix: str = "") -> list[str]:
        """Do not turn malformed structure into a plausible prose finding."""
        value = payload.get(key, [])
        if type(value) is not list:
            gaps.append(f"{location}.{key} must be a list of strings")
            return []
        result = []
        for index, item in enumerate(value):
            if type(item) is not str or not item.strip():
                gaps.append(f"{location}.{key}[{index}] must be a nonempty string")
            else:
                result.append(prefix + item.strip())
        return result

    @staticmethod
    def _schema_coverage(payload: Mapping[str, Any], supported: frozenset[str],
                         location: str, gaps: list[str]) -> None:
        for key in ("schema_version", "schema"):
            if key in payload and (type(payload[key]) is not str or payload[key] not in supported):
                gaps.append(f"UNSUPPORTED_SCHEMA:{location}.{key}:{payload[key]}")

    def _intelligence_findings(
        self, container: Mapping[str, Any], entry: str, gaps: list[str]
    ) -> list[str]:
        intelligence = container.get("intelligence")
        if intelligence is None:
            return []
        if type(intelligence) is not dict:
            gaps.append(f"{entry}.intelligence must be an object")
            return []
        gaps.extend(self._string_list(
            intelligence, "coverage_gaps", f"{entry}.intelligence", gaps,
            f"{entry}:coverage_gap:",
        ))
        return self._string_list(
            intelligence, "findings", f"{entry}.intelligence", gaps,
            f"{entry}:intelligence_finding:",
        )

    def _native_reference_gaps(
        self, metadata: Mapping[str, Any], entry: str, gaps: list[str]
    ) -> None:
        reference = metadata.get("native_gate_receipt")
        if reference is None:
            return
        reference_entry = f"{entry}.metadata.native_gate_receipt"
        if type(reference) is not dict:
            gaps.append(f"{reference_entry} must be an object")
            return
        self._schema_coverage(
            reference, frozenset({"adversary.native-gate-reference.v1"}), reference_entry, gaps,
        )
        hashes_valid = all(
            type(reference.get(key)) is str
            and len(reference[key]) == 64
            and all(character in "0123456789abcdef" for character in reference[key])
            for key in ("sha256", "receipt_sha256")
        )
        identity_valid = (
            type(reference.get("path")) is str
            and bool(reference["path"])
            and type(reference.get("scope")) is dict
            and type(reference.get("summary")) is dict
            and reference.get("authority_effect") == "None"
        )
        if not hashes_valid or not identity_valid:
            gaps.append(f"{reference_entry} has incomplete native readback identity")

    def _native_residual_findings(
        self, summary: Mapping[str, Any], entry: str, policy: object, gaps: list[str]
    ) -> list[str]:
        residuals = summary.get("residuals")
        if type(residuals) is not list:
            gaps.append(f"{entry}.residuals must be a list")
            return []
        findings: list[str] = []
        valid_states = {"HOLD", "REFUSE", "BLOCKED", "DIVERTED", "UNAVAILABLE"}
        for index, residual in enumerate(residuals):
            row = f"{entry}.residuals[{index}]"
            valid = (
                type(residual) is dict
                and type(residual.get("gate_id")) is str
                and bool(residual["gate_id"])
                and residual.get("status") in valid_states
            )
            if not valid:
                gaps.append(f"{row} is unsupported")
            elif policy == "require_pass":
                findings.append(
                    f"{row}:required_native:{residual['gate_id']}:{residual['status']}"
                )
        return findings

    def _native_summary_findings(
        self, metadata: Mapping[str, Any], entry: str, selection: object, gaps: list[str]
    ) -> list[str]:
        summary = metadata.get("native_gate_summary")
        if summary is None:
            return []
        native_entry = f"{entry}.metadata.native_gate_summary"
        if type(summary) is not dict:
            gaps.append(f"{native_entry} must be an object")
            return []
        self._schema_coverage(summary, frozenset(), native_entry, gaps)
        for key in ("required", "observed", "missing"):
            if key not in summary:
                gaps.append(f"{native_entry}.{key} is missing")
            self._string_list(summary, key, native_entry, gaps)
        diagnostics_valid = (
            type(summary.get("coverage_complete")) is bool
            and type(summary.get("all_pass")) is bool
            and type(summary.get("outcomes")) is dict
            and type(summary.get("transitions")) is list
            and summary.get("authority_effect") == "None"
        )
        if not diagnostics_valid:
            gaps.append(f"{native_entry} has incomplete native diagnostic coverage")
        policy = metadata.get(
            "native_gate_policy", selection.get("policy") if type(selection) is dict else None,
        )
        if policy not in ("diagnostic", "require_pass"):
            gaps.append(f"{native_entry}.policy is unsupported")
        return self._native_residual_findings(summary, native_entry, policy, gaps)

    def _lesson_gaps(
        self, metadata: Mapping[str, Any], entry: str, gaps: list[str]
    ) -> None:
        if "lessons" not in metadata:
            return
        lessons = metadata["lessons"]
        if type(lessons) is not list:
            gaps.append(f"{entry}.metadata.lessons must be a list")
            return
        for index, lesson in enumerate(lessons):
            lesson_entry = f"{entry}.metadata.lessons[{index}]"
            if type(lesson) is dict and lesson:
                self._schema_coverage(lesson, frozenset(), lesson_entry, gaps)
            elif type(lesson) is not str or not lesson.strip():
                gaps.append(f"{lesson_entry} must be a nonempty string or object")

    def _metadata_findings(
        self, observation: Mapping[str, Any], entry: str, selection: object, gaps: list[str]
    ) -> list[str]:
        metadata = observation.get("metadata", {})
        if type(metadata) is not dict:
            gaps.append(f"{entry}.metadata must be an object")
            return []
        self._native_reference_gaps(metadata, entry, gaps)
        findings = self._native_summary_findings(metadata, entry, selection, gaps)
        findings.extend(self._string_list(
            metadata, "learning_findings", f"{entry}.metadata", gaps,
            f"{entry}:learning_finding:",
        ))
        self._lesson_gaps(metadata, entry, gaps)
        return findings

    def _operation_findings(
        self, operations: object, entry: str, gaps: list[str]
    ) -> list[str]:
        if type(operations) is not list:
            gaps.append(f"{entry}.observed_operations must be a list")
            return []
        findings: list[str] = []
        for index, operation in enumerate(operations):
            operation_entry = f"{entry}.observed_operations[{index}]"
            if type(operation) is not dict:
                gaps.append(f"{operation_entry} must be an object")
                continue
            findings.extend(self._string_list(
                operation, "findings", operation_entry, gaps,
                f"{operation_entry}:finding:",
            ))
            blocked = operation.get("blocked", False)
            if type(blocked) is not bool:
                gaps.append(f"{operation_entry}.blocked must be a boolean")
            elif blocked:
                findings.append(f"{operation_entry}:blocked")
        return findings

    def _procedure_findings(
        self, procedure: Mapping[str, Any], entry: str, gaps: list[str]
    ) -> list[str]:
        self._schema_coverage(procedure, frozenset(), entry, gaps)
        findings = self._string_list(
            procedure, "open_findings", entry, gaps, f"{entry}:open_finding:",
        )
        status = procedure.get("stopped_status", "")
        reason = procedure.get("stopped_reason", "")
        if type(status) is not str or status not in ("", "partial", "blocked"):
            gaps.append(f"{entry}.stopped_status is unsupported")
        elif status:
            if type(reason) is not str or not reason.strip():
                gaps.append(f"{entry}.stopped_reason must explain the stop")
            findings.append(f"{entry}:stopped:{status}:{reason}")
        findings.extend(self._operation_findings(
            procedure.get("observed_operations"), entry, gaps,
        ))
        return findings

    def _program_findings(
        self, observation: Mapping[str, Any], entry: str, gaps: list[str]
    ) -> list[str]:
        program = observation.get("ddc_program")
        if program is None:
            return []
        program_entry = f"{entry}.ddc_program"
        if type(program) is not dict or type(program.get("steps")) is not list:
            gaps.append(f"{program_entry}.steps must be a list")
            return []
        self._schema_coverage(program, frozenset(), program_entry, gaps)
        findings: list[str] = []
        for index, step in enumerate(program["steps"]):
            step_entry = f"{program_entry}.steps[{index}]"
            if type(step) is not dict:
                gaps.append(f"{step_entry} must be an object")
                continue
            if "observed_procedure" not in step:
                continue
            procedure = step["observed_procedure"]
            if type(procedure) is not dict:
                gaps.append(f"{step_entry}.observed_procedure must be an object")
                continue
            findings.extend(self._procedure_findings(procedure, step_entry, gaps))
        return findings

    @staticmethod
    def _blocked_findings(
        observation: Mapping[str, Any], entry: str, gaps: list[str]
    ) -> list[str]:
        blocked = observation.get("blocked", False)
        if type(blocked) is not bool:
            gaps.append(f"{entry}.blocked must be a boolean")
            return []
        if not blocked:
            return []
        summary = observation.get("summary")
        if type(summary) is not str or not summary.strip():
            gaps.append(f"{entry}.summary must explain the blocked observation")
            return [f"{entry}:blocked"]
        return [f"{entry}:blocked:{summary.strip()}"]

    def _observation_findings(
        self, observation: object, entry: str, selection: object, gaps: list[str]
    ) -> list[str]:
        if type(observation) is not dict:
            gaps.append(f"{entry} must be an object")
            return []
        findings = self._string_list(
            observation, "findings", entry, gaps, prefix=f"{entry}:finding:",
        )
        findings.extend(self._intelligence_findings(observation, entry, gaps))
        findings.extend(self._metadata_findings(observation, entry, selection, gaps))
        findings.extend(self._program_findings(observation, entry, gaps))
        findings.extend(self._blocked_findings(observation, entry, gaps))
        return findings

    def _teamwork_findings(
        self, payload: Mapping[str, Any], location: str, gaps: list[str]
    ) -> list[str]:
        if "teamwork" not in payload:
            return []
        teamwork = payload["teamwork"]
        if type(teamwork) is not dict:
            gaps.append(f"{location}.teamwork must be an object")
            return []
        entry = f"{location}.teamwork"
        self._schema_coverage(teamwork, frozenset({
            "core.adversary.teamwork.v1", "core.adversary.teamwork.v2",
            "core.adversary.teamwork.v3", "core.adversary.teamwork.v4",
        }), entry, gaps)
        selection = teamwork.get("native_gate_check")
        if selection is not None and type(selection) is not dict:
            gaps.append(f"{entry}.native_gate_check must be an object")
        elif type(selection) is dict:
            self._schema_coverage(
                selection, frozenset({"adversary.native-gate-check.v1"}),
                f"{entry}.native_gate_check", gaps,
            )
        observations = teamwork.get("observations")
        if type(observations) is not list:
            gaps.append(f"{entry}.observations must be a list")
            return []
        findings = self._intelligence_findings(teamwork, entry, gaps)
        for index, observation in enumerate(observations):
            findings.extend(self._observation_findings(
                observation, f"{entry}.observations[{index}]", selection, gaps,
            ))
        return findings

    @staticmethod
    def _digestion_error_findings(
        record: Mapping[str, Any], gaps: list[str]
    ) -> _Extraction:
        error = record.get("error")
        if type(error) is str and error.strip():
            return _Extraction([f"digestion:error:{error.strip()}"], gaps, [])
        gaps.append("digestion.error must be a nonempty string")
        return _Extraction([], gaps, [])

    def _digestion_row_findings(
        self, record: Mapping[str, Any], key: str, gaps: list[str]
    ) -> list[str]:
        finding_key, prefix = (
            ("residuals", "residual") if key == "blocked"
            else ("defects_extracted", "observed_finding")
        )
        rows = record.get(key)
        if type(rows) is not list:
            gaps.append(f"digestion.{key} must be a list")
            return []
        findings: list[str] = []
        for index, row in enumerate(rows):
            entry = f"digestion.{key}[{index}]"
            if type(row) is not dict:
                gaps.append(f"{entry} must be an object")
                continue
            if finding_key not in row:
                gaps.append(f"{entry}.{finding_key} is missing")
            findings.extend(self._string_list(
                row, finding_key, entry, gaps, f"{entry}:{prefix}:",
            ))
            if key == "blocked":
                state = row.get("state")
                if type(state) is not str or not state.strip():
                    gaps.append(f"{entry}.state must be a nonempty string")
                else:
                    findings.append(f"{entry}:state:{state.strip()}")
        return findings

    def _digestion_receipt_findings(self, record: Mapping[str, Any]) -> _Extraction:
        """Read the existing unversioned DigestionReceipt and CLI error envelope."""
        gaps: list[str] = []
        schema = record.get("schema_version", record.get("schema"))
        supported = (
            frozenset({"core.intelligence.digestion-error.v1"})
            if schema == "core.intelligence.digestion-error.v1" else frozenset()
        )
        self._schema_coverage(record, supported, "digestion", gaps)
        if record.get("authority_effect") != "None":
            gaps.append("digestion.authority_effect must be None")
        if schema == "core.intelligence.digestion-error.v1":
            return self._digestion_error_findings(record, gaps)
        for key in ("receipt_id", "timestamp_utc"):
            if type(record.get(key)) is not str or not record[key].strip():
                gaps.append(f"digestion.{key} must be a nonempty string")
        for key in ("total_runs_examined", "total_runs_archived"):
            if type(record.get(key)) is not int or record[key] < 0:
                gaps.append(f"digestion.{key} must be a nonnegative integer")
        for key in ("errors", "warnings"):
            if key not in record:
                gaps.append(f"digestion.{key} is missing")
        findings = self._string_list(
            record, "errors", "digestion", gaps, "digestion:error:",
        )
        self._string_list(record, "warnings", "digestion", gaps)
        if type(record.get("context")) is dict:
            gaps.extend(self._string_list(
                record["context"], "coverage_gaps", "digestion.context", gaps,
            ))
        findings.extend(self._digestion_row_findings(record, "blocked", gaps))
        findings.extend(self._digestion_row_findings(record, "records", gaps))
        return _Extraction(
            sorted(dict.fromkeys(findings)), sorted(dict.fromkeys(gaps)), [],
        )

    def _extract_research_envelope_findings(self, run_dir: Path) -> _Extraction:
        envelope_path = run_dir / "research_evidence_envelope.json"
        coverage_gaps: list[str] = []
        parse_residuals: list[str] = []
        findings: list[str] = []
        try:
            payload = _read_object(envelope_path)
            self._schema_coverage(payload, frozenset({"core.research_swarm.evidence_envelope.v1"}),
                "research_envelope", coverage_gaps)
            coda = payload.get("coda_evaluation", {})
            for layer in coda.get("layer_records", []):
                defect_mass = layer.get("defect_mass")
                if str(defect_mass) not in ("0", ""):
                    diag = layer.get("diagnostic", f"Defect in layer {layer.get('layer_id')}")
                    findings.append(f"coda_layer_defect:{layer.get('layer_id')}:{diag}")
            firewall = coda.get("firewall_decision")
            if firewall and firewall != "Pass":
                findings.append(f"coda_firewall:{firewall}")
        except Exception as exc:
            parse_residuals.append(f"RESEARCH_ENVELOPE_UNREADABLE:{exc}")
        return _Extraction(sorted(dict.fromkeys(findings)), coverage_gaps, parse_residuals)

    def _research_summary_findings(
        self, path: Path, gaps: list[str]
    ) -> _Extraction:
        try:
            summary = _read_object(path)
            self._schema_coverage(summary, frozenset(), "research_summary", gaps)
        except Exception as exc:
            return _Extraction([], gaps, [f"RESEARCH_SUMMARY_UNREADABLE:{exc}"])
        findings: list[str] = []
        refusal = summary.get("oeeis_refusal")
        if refusal:
            findings.append(f"research_refusal:{refusal}")
        residuals = summary.get("residual_ids", [])
        if residuals and isinstance(residuals, list):
            findings.extend(f"research_residual:{item}" for item in residuals)
        candidates = summary.get("oeeis_candidates", [])
        if candidates and isinstance(candidates, list):
            findings.extend(f"research_candidate:{item}" for item in candidates)
        disposition = summary.get("disposition")
        if disposition and disposition != "Verified":
            findings.append(f"research_disposition:{disposition}")
        return _Extraction(findings, gaps, [])

    def _research_receipt_findings(
        self, path: Path, gaps: list[str]
    ) -> _Extraction:
        try:
            receipt = _read_object(path)
            self._schema_coverage(receipt, frozenset(), "research_receipt", gaps)
        except Exception as exc:
            return _Extraction([], gaps, [f"RESEARCH_RECEIPT_UNREADABLE:{exc}"])
        disposition = receipt.get("disposition")
        findings = (
            [f"research_disposition:{disposition}"]
            if disposition and disposition != "Verified" else []
        )
        return _Extraction(findings, gaps, [])

    def _extract_research_run_findings(self, run_dir: Path) -> _Extraction:
        gaps: list[str] = []
        summary_path = run_dir / "summary.json"
        if summary_path.is_file():
            return self._research_summary_findings(summary_path, gaps)
        receipt_path = run_dir / "receipt.json"
        if receipt_path.is_file():
            return self._research_receipt_findings(receipt_path, gaps)
        if (run_dir / "mission.json").is_file():
            return _Extraction([f"research_unfinalized_mission:{run_dir.name}"], gaps, [])
        return _Extraction([], gaps, ["RESEARCH_RUN_FILES_MISSING"])

    def _jsonl_row_findings(
        self, record: object, number: int, gaps: list[str]
    ) -> list[str]:
        if type(record) is not dict:
            gaps.append(f"JSONL_ROW_NOT_OBJECT:L{number}")
            return []
        entry = f"jsonl[L{number}]"
        self._schema_coverage(
            record, frozenset({"core.intelligence.omc-dag.v1"}), entry, gaps,
        )
        if not any(key in record for key in (
            "decisive_blockers", "natural_science_gates", "verdict",
        )):
            gaps.append(f"UNSUPPORTED_JSONL_PROFILE:L{number}")
        findings = self._string_list(
            record, "decisive_blockers", entry, gaps, "decisive_blocker:",
        )
        gates = record.get("natural_science_gates", {})
        if type(gates) is not dict:
            gaps.append(f"{entry}.natural_science_gates must be an object")
            gates = {}
        findings.extend(
            f"gate_failure:{name}:{status}" for name, status in gates.items()
            if status not in ("PASS", True)
        )
        if record.get("verdict") not in ("GO", "PASS", None):
            findings.append(f"report_verdict:{record.get('verdict')}")
        return findings

    def _extract_jsonl_findings(self, file_path: Path) -> _Extraction:
        gaps: list[str] = []
        findings: list[str] = []
        try:
            content = file_path.read_text(encoding="utf-8")
            for number, line in enumerate(content.splitlines(), 1):
                if not line.strip():
                    continue
                record = json.loads(
                    line.strip(), object_pairs_hook=_unique_object,
                    parse_constant=_reject_constant,
                )
                findings.extend(self._jsonl_row_findings(record, number, gaps))
        except Exception as exc:
            return _Extraction(findings, gaps, [f"JSONL_REPORT_UNREADABLE:{exc}"])
        return _Extraction(sorted(dict.fromkeys(findings)), gaps, [])

    def _report_profile_findings(
        self, record: Mapping[str, Any], gaps: list[str]
    ) -> _Extraction:
        self._schema_coverage(record, frozenset({
            "core.adversary.report-intake.v1", "core.adversary.learned-report.v1",
        }), "report", gaps)
        gaps.extend(self._string_list(record, "coverage_gaps", "report", gaps, ""))
        findings = self._string_list(
            record, "open_obligations", "report", gaps, "report:",
        )
        return _Extraction(findings, gaps, [])

    @staticmethod
    def _stage_findings(record: Mapping[str, Any]) -> list[str]:
        findings: list[str] = []
        for stage in record.get("stages", []):
            if stage.get("status") not in ("PASS", None):
                findings.append(
                    f"stage_failed:{stage.get('stage_name', 'stage')}:{stage.get('status')}"
                )
            findings.extend(f"stage_error:{error}" for error in stage.get("errors", []))
        return findings

    def _generic_receipt_findings(
        self, record: Mapping[str, Any], gaps: list[str]
    ) -> _Extraction:
        self._schema_coverage(record, frozenset(), "receipt", gaps)
        findings = self._string_list(
            record, "open_obligations", "receipt", gaps, "receipt:open_obligation:",
        )
        findings.extend(self._string_list(
            record, "findings", "receipt", gaps, "receipt:finding:",
        ))
        gaps.extend(self._string_list(
            record, "coverage_gaps", "receipt", gaps, "receipt:coverage_gap:",
        ))
        status = record.get("overall_status") or record.get("status")
        if status is None:
            gaps.append("UNSUPPORTED_JSON_PROFILE: requires semantic host review")
            return _Extraction(findings, gaps, [])
        if status not in ("PASS", "VERIFIED", "ACCEPTED"):
            findings.append(f"receipt_status:{status}")
        findings.extend(self._stage_findings(record))
        return _Extraction(sorted(dict.fromkeys(findings)), gaps, [])

    def _decoded_json_findings(self, record: Mapping[str, Any]) -> _Extraction:
        gaps: list[str] = []
        schema = record.get("schema_version", record.get("schema"))
        teamwork_schemas = {
            "core.adversary.teamwork.v1", "core.adversary.teamwork.v2",
            "core.adversary.teamwork.v3", "core.adversary.teamwork.v4",
        }
        if schema in teamwork_schemas:
            return _Extraction(
                self._teamwork_findings({"teamwork": record}, "run", gaps), gaps, [],
            )
        adversarial_keys = {
            "top_blocking_objections", "unresolved_objections", "must_not_silently_inherit",
            "blocking_issues", "should_decompose",
        }
        if adversarial_keys.intersection(record):
            extracted = self._extract_adversarial_report(record)
            self._schema_coverage(record, frozenset({
                "core.adversary.report-intake.v1", "core.adversary.learned-report.v1",
            }), "adversarial_report", extracted.coverage_gaps)
            return extracted
        if schema in ("core.adversary.report-intake.v1", "core.adversary.learned-report.v1"):
            return self._report_profile_findings(record, gaps)
        digestion_shape = any(
            key in record for key in ("total_runs_examined", "total_runs_archived", "blocked")
        )
        if digestion_shape or (type(schema) is str and "digestion" in schema):
            return self._digestion_receipt_findings(record)
        return self._generic_receipt_findings(record, gaps)

    def _extract_json_receipt_findings(self, file_path: Path) -> _Extraction:
        try:
            return self._decoded_json_findings(_read_object(file_path))
        except Exception as exc:
            return _Extraction([], [], [f"JSON_RECEIPT_UNREADABLE:{exc}"])

    def _extract_adversarial_report(self, record: Mapping[str, Any]) -> _Extraction:
        """Retain objections as reported claims, never as verified mathematics."""
        findings: list[str] = []
        gaps: list[str] = []
        for key in ("unresolved_objections", "must_not_silently_inherit", "blocking_issues"):
            findings.extend(self._string_list(record, key, "report", gaps, f"{key}:"))
        objections = record.get("top_blocking_objections", [])
        if type(objections) is not list:
            gaps.append("report.top_blocking_objections must be a list")
            objections = []
        for index, item in enumerate(objections):
            if not isinstance(item, dict) or not isinstance(item.get("claim_or_issue"), str):
                gaps.append(f"report.top_blocking_objections[{index}] needs claim_or_issue")
                continue
            details = [f"{key}={item[key]}" for key in (
                "severity", "claim_or_issue", "how_it_could_fail", "cheap_test",
            ) if isinstance(item.get(key), str)]
            findings.append("reported_objection:" + " | ".join(details))
        if record.get("should_decompose") is False:
            findings.append("reported_gate:" + str(record.get("feasibility_verdict", "decomposition_blocked")))
        if not findings and record.get("verdict") in ("falsified", "needs_repair"):
            findings.append("reported_verdict:" + record["verdict"])
        return _Extraction(sorted(dict.fromkeys(findings)), gaps, [])

    def _extract_markdown_review_findings(self, file_path: Path) -> _Extraction:
        coverage_gaps: list[str] = []
        parse_residuals: list[str] = []
        findings: list[str] = []
        try:
            content = file_path.read_text(encoding="utf-8")
            negative = re.compile(r"\b(?:FAIL(?:ED)?|BLOCKED|OBSTRUCTION|REJECTED|REQUEST_CHANGES|INTEGRITY VIOLATION)\b")
            for number, line in enumerate(content.splitlines(), 1):
                structured = line.lstrip().startswith(("-", "*", "|")) or re.search(
                    r"(?:gate result|verdict|status)\s*:", line, re.IGNORECASE)
                if structured and negative.search(line.upper()):
                    findings.append(f"markdown_finding:L{number}:{line.strip()}")
        except Exception as exc:
            parse_residuals.append(f"MARKDOWN_REVIEW_UNREADABLE:{exc}")
        return _Extraction(sorted(dict.fromkeys(findings)), coverage_gaps, parse_residuals)

    @staticmethod
    def _harvest_record_findings(records: object) -> list[str]:
        if type(records) is not list:
            return []
        findings: list[str] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            metadata = record.get("metadata", {})
            if isinstance(metadata, dict) and metadata.get("error"):
                findings.append(
                    f"harvest_record_error:{record.get('relative_path')}:{metadata.get('error')}"
                )
        return findings

    def _extract_harvest_snapshot_findings(self, file_path: Path) -> _Extraction:
        coverage_gaps: list[str] = []
        parse_residuals: list[str] = []
        findings: list[str] = []
        try:
            payload = _read_object(file_path)
            for req in ("snapshot_id", "source_name", "merkle_root", "records"):
                if req not in payload:
                    coverage_gaps.append(f"SNAPSHOT_KEY_MISSING:{req}")
            findings.extend(self._harvest_record_findings(payload.get("records", [])))
        except Exception as exc:
            parse_residuals.append(f"SNAPSHOT_UNREADABLE:{exc}")
        return _Extraction(sorted(dict.fromkeys(findings)), coverage_gaps, parse_residuals)

    def _file_findings(self, source: Path) -> _Extraction | None:
        if not source.is_file():
            return None
        if source.name.startswith("snap_") and source.suffix.lower() == ".json":
            return self._extract_harvest_snapshot_findings(source)
        readers = {
            ".jsonl": self._extract_jsonl_findings,
            ".json": self._extract_json_receipt_findings,
            ".md": self._extract_markdown_review_findings,
        }
        reader = readers.get(source.suffix.lower())
        return reader(source) if reader is not None else None

    def _research_directory_findings(self, source: Path) -> _Extraction | None:
        if (source / "research_evidence_envelope.json").is_file():
            return self._extract_research_envelope_findings(source)
        has_summary_only = (
            (source / "summary.json").is_file()
            and not (source / "receipt.json").is_file()
            and not any((source / name).is_file() for name in ("novella.md", "uns.md"))
        )
        if (source / "mission.json").is_file() or has_summary_only:
            return self._extract_research_run_findings(source)
        return None

    @staticmethod
    def _bundle_digests(
        run_dir: Path, receipt: Mapping[str, Any], fresh: bool
    ) -> tuple[dict[str, str], bool]:
        digests = (
            {"uns.md": "uns_sha256", "ddc.jsonl": "ddc_sha256",
             "summary.json": "summary_sha256", "uts.jsonl": "uts_sha256"}
            if fresh else dict(_NATIVE_BUNDLE_DIGESTS)
        )
        legacy = not fresh and (run_dir / _LEGACY_DDA_TAPE[0]).is_file()
        if legacy:
            digests[_LEGACY_DDA_TAPE[0]] = _LEGACY_DDA_TAPE[1]
            if not (run_dir / "ddc.jsonl").is_file() and "ddc_sha256" not in receipt:
                del digests["ddc.jsonl"]
        return digests, legacy

    def _bundle_layout(self, run_dir: Path) -> _BundleLayout | _Extraction:
        try:
            path = run_dir / "receipt.json"
            receipt = _read_object(path) if path.is_file() else {}
        except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            return _Extraction([], [], [f"RUN_BUNDLE_JSON_UNREADABLE:{exc}"])
        fresh = (
            receipt.get("bundle_schema_version") == "core.adversary.reported-run-bundle.v2"
            or (run_dir / "uns.md").is_file()
        )
        digests, legacy = self._bundle_digests(run_dir, receipt, fresh)
        missing = [
            f"RUN_BUNDLE_FILE_MISSING:{name}" for name in (*digests, "receipt.json")
            if not (run_dir / name).is_file()
        ]
        if missing:
            return _Extraction([], [], missing)
        return _BundleLayout(receipt, digests, fresh, legacy)

    def _bundle_custody_residuals(
        self, run_dir: Path, layout: _BundleLayout, receipt: Mapping[str, Any]
    ) -> list[str]:
        residuals = [
            f"CUSTODY_DIGEST_MISMATCH:{name}:{digest_key}"
            for name, digest_key in layout.digests.items()
            if not _matches_digest(receipt.get(digest_key), (run_dir / name).read_bytes())
        ]
        version = receipt.get("bundle_schema_version")
        reported = version in (
            "core.adversary.reported-run-bundle.v1", "core.adversary.reported-run-bundle.v2",
        )
        if layout.fresh != (version == "core.adversary.reported-run-bundle.v2"):
            residuals.append("BUNDLE_LAYOUT_VERSION_MISMATCH")
        if reported:
            try:
                from adversary.domain.native import value as native_value

                native_value(self._native_support, "verify_reported_bundle", run_dir=str(run_dir))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                residuals.append(f"REPORTED_BUNDLE_CUSTODY_REFUSED:{exc}")
        elif (run_dir / "uts.jsonl").exists():
            residuals.append("UTS_WITHOUT_BUNDLE_VERSION")
        legacy_tape = run_dir / _LEGACY_DDA_TAPE[0]
        if layout.legacy and (run_dir / "ddc.jsonl").is_file():
            if legacy_tape.read_bytes() != (run_dir / "ddc.jsonl").read_bytes():
                residuals.append("DDC_DDA_BYTES_DIVERGE")
        return residuals

    def _payload_findings(
        self, name: str, payload: Mapping[str, Any], reported: bool, gaps: list[str]
    ) -> list[str]:
        findings = self._string_list(
            payload, "open_obligations", name, gaps, f"{name}:open_obligation:",
        )
        findings.extend(self._teamwork_findings(payload, name, gaps))
        if reported and "source_history" in payload:
            findings.extend(self._teamwork_findings(
                {"teamwork": payload["source_history"]}, f"{name}.source_history", gaps,
            ))
        if "retained_context" in payload:
            findings.extend(self._teamwork_findings(
                {"teamwork": payload["retained_context"]}, f"{name}.retained_context", gaps,
            ))
        for key in ("measurement_status", "lggr_joint_kernel_status", "checker_verdict"):
            value = payload.get(key)
            if type(value) is str and value.upper() in {"NOT_MEASURED", "UNMEASURED"}:
                findings.append(f"{name}:{key}:{value}")
        blockers = payload.get("authorization_blockers", [])
        if blockers is not None and type(blockers) is not list:
            gaps.append(f"{name}.authorization_blockers must be a list")
        elif type(blockers) is list:
            findings.extend(
                f"{name}:authorization_blocker:{item}" for item in blockers if str(item).strip()
            )
        return findings

    def _bundle_findings(self, run_dir: Path) -> _Extraction:
        layout = self._bundle_layout(run_dir)
        if isinstance(layout, _Extraction):
            return layout
        gaps: list[str] = []
        try:
            receipt = _read_object(run_dir / "receipt.json")
            summary = _read_object(run_dir / "summary.json")
        except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            return _Extraction([], gaps, [f"RUN_BUNDLE_JSON_UNREADABLE:{exc}"])
        self._schema_coverage(receipt, frozenset({
            "core.adversary.skill-run-receipt.v1", "core.adversary.teamwork-report-receipt.v1",
            "core.adversary.bout-receipt-id.v1", "core.adversary.refusal-bundle.v1",
        }), "bundle_receipt", gaps)
        self._schema_coverage(summary, frozenset({
            "core.adversary.run-bundle.v2", "core.adversary.run-bundle.v3",
            "core.adversary.teamwork-report-summary.v1",
        }), "bundle_summary", gaps)
        expected = "core.adversary.run-bundle.v3" if layout.fresh else "core.adversary.run-bundle.v2"
        if "bundle_schema" in summary and summary["bundle_schema"] != expected:
            gaps.append(f"UNSUPPORTED_SCHEMA:bundle_summary.bundle_schema:{summary['bundle_schema']}")
        residuals = self._bundle_custody_residuals(run_dir, layout, receipt)
        findings = self._record_list(
            receipt, ("failure_modes", "defects", "errors", "unmitigated_defects"), gaps,
        )
        findings.extend(self._record_list(
            summary, ("failure_modes", "defects", "errors"), gaps,
        ))
        reported = receipt.get("bundle_schema_version") in (
            "core.adversary.reported-run-bundle.v1", "core.adversary.reported-run-bundle.v2",
        )
        findings.extend(self._payload_findings("receipt", receipt, reported, gaps))
        findings.extend(self._payload_findings("summary", summary, reported, gaps))
        return _Extraction(
            sorted(dict.fromkeys(item.strip() for item in findings if item.strip())),
            sorted(dict.fromkeys(gaps)), sorted(dict.fromkeys(residuals)),
        )

    def _extract_run_findings(self, run_dir: Path) -> _Extraction:
        source = Path(run_dir)
        file_findings = self._file_findings(source)
        if file_findings is not None:
            return file_findings
        research_findings = self._research_directory_findings(source)
        if research_findings is not None:
            return research_findings
        return self._bundle_findings(source)

    def _extract_run_defects(self, run_dir: Path) -> list[str]:
        """Compatibility view for callers that only need the declared findings."""
        return self._extract_run_findings(run_dir).findings
