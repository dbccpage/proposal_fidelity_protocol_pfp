"""Bounded, byte-preserving exploratory historical import. AuthorityEffect: None."""

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from ..infrastructure.cas import ContentAddressedStorageV1
from ..domain.models import ExecutionOccurrenceV1, PromptGenomeV1
from .view_engine import PromptGenomeRegistryV1

RETIRED_PARSER_IDS = frozenset({
    "ab_syntax_error_e033d14a", "ab_syntax_error_4cb62bc5", "ab_syntax_error_bb7045c0",
})


@dataclass(frozen=True)
class BackfillReceiptV1:
    receipt_sha256: str
    genomes_created: int
    occurrences_recorded: int
    antibodies_indexed: int
    antibodies_refused: int
    residuals_recorded: list[dict[str, str]]
    receipt_kind: str = "EXPLORATORY"
    authority_effect: str = "None"


class PromptCivBackfillEngineV1:
    """Read-only inventory, or durable import with an explicit output root.

    Every imported genome defaults to dormant. A string claiming admission cannot
    authorize retrieval or enforcement. Source bytes are never modified.
    """

    def __init__(
        self, intelligence_root: Path | None = None, *, output_root: Path | None = None,
        admission_verifier: Callable[[dict, str], bool] | None = None,
        max_files: int = 1000, max_total_bytes: int = 64 * 1024 * 1024,
    ) -> None:
        self.intelligence_root = Path(intelligence_root) if intelligence_root is not None else Path(os.environ.get("OMEGA_INTELLIGENCE_ROOT", ".")) / "_ic"
        self.output_root = output_root
        if output_root is not None and output_root.resolve().is_relative_to(self.intelligence_root.resolve()):
            raise ValueError("BACKFILL_OUTPUT_MUST_NOT_BE_INSIDE_SOURCE")
        if max_files <= 0 or max_total_bytes <= 0:
            raise ValueError("BACKFILL_BUDGET_REQUIRED")
        self.max_files, self.max_total_bytes = max_files, max_total_bytes
        self.admission_verifier = admission_verifier
        self.registry = PromptGenomeRegistryV1()
        self.cas = ContentAddressedStorageV1(output_root / "cas") if output_root else None
        self.antibodies: dict[str, dict] = {}
        self.aliases: dict[str, PromptGenomeV1] = {}
        self.residuals: list[dict[str, str]] = []
        self._processed_sources: set[str] = set()
        self._refused_antibodies: set[str] = set()
        self._occurrences: set[str] = set()
        self._event_ids: set[str] = set()
        self._pending: list[tuple[dict, str]] = []
        self._historical_links: list[tuple[str, str, str]] = []
        if output_root:
            output_root.mkdir(parents=True, exist_ok=True)
            events = output_root / "backfill_events.jsonl"
            if events.exists():
                for line in events.read_text(encoding="utf-8").splitlines():
                    envelope = json.loads(line)
                    event = envelope["event"]
                    expected = hashlib.sha256(json.dumps(event, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                    if expected != envelope["event_id"]:
                        raise ValueError("BACKFILL_EVENT_IDENTITY_CONFLICT")
                    self._event_ids.add(expected)
                    payload = event["payload"]
                    if event["kind"] == "GenomeImported":
                        genome = PromptGenomeV1.from_dict(payload["genome"])
                        self.registry.register_genome(genome)
                        self.aliases[payload["source_prompt_id"]] = genome
                    elif event["kind"] == "OccurrenceImported":
                        occurrence = ExecutionOccurrenceV1(**payload)
                        self.registry.record_occurrence(occurrence)
                        self._occurrences.add(occurrence.occurrence_id)
                    elif event["kind"] == "AntibodyIndexed":
                        self.antibodies[payload["antibody_id"]] = payload
                    elif event["kind"] == "Residual":
                        self.residuals.append(payload)
                        if payload["code"] == "RETIRED_OR_PLACEHOLDER_ANTIBODY":
                            self._refused_antibodies.add(payload["subject"])

    def _residual(self, code: str, subject: str) -> None:
        value = {"code": code, "subject": subject}
        if value not in self.residuals:
            self.residuals.append(value)
            self._persist("Residual", value)

    def _persist(self, kind: str, payload: dict) -> None:
        if self.output_root is None:
            return
        raw = json.dumps({"kind": kind, "payload": payload, "authority_effect": "None"}, sort_keys=True, separators=(",", ":"))
        event_id = hashlib.sha256(raw.encode()).hexdigest()
        if event_id in self._event_ids:
            return
        with (self.output_root / "backfill_events.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps({"event_id": event_id, "event": json.loads(raw)}, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self._event_ids.add(event_id)

    def run_backfill(self) -> BackfillReceiptV1:
        total_bytes = 0
        files = sorted(
            (p for p in self.intelligence_root.rglob("*") if p.suffix in (".json", ".jsonl") and p.is_file()),
            key=lambda p: p.as_posix().encode("utf-8"),
        ) if self.intelligence_root.exists() else []
        for index, path in enumerate(files):
            if index >= self.max_files or total_bytes + path.stat().st_size > self.max_total_bytes:
                self._residual("BACKFILL_BUDGET_EXHAUSTED", path.relative_to(self.intelligence_root).as_posix())
                break
            total_bytes += path.stat().st_size
            if not path.resolve().is_relative_to(self.intelligence_root.resolve()):
                self._residual("SOURCE_PATH_ESCAPES_ROOT", str(path))
                continue
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest in self._processed_sources:
                continue
            self._processed_sources.add(digest)
            if self.cas:
                self.cas.store(raw)
            lines = raw.splitlines(keepends=True) if path.suffix == ".jsonl" else [raw]
            for line in lines:
                if not line.strip():
                    continue
                source_digest = hashlib.sha256(line).hexdigest()
                try:
                    record = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    self._residual("MALFORMED_SOURCE_RECORD", source_digest)
                    continue
                if not isinstance(record, dict):
                    self._residual("SOURCE_OBJECT_REQUIRED", source_digest)
                    continue
                self._read_record(record, source_digest)
        self._resolve_prompts()
        for parent, child, digest in self._historical_links:
            if parent not in self.aliases or child not in self.aliases:
                self._residual("UNRESOLVED_PARENT", child)
            else:
                self._persist("HistoricalRetryWitness", {
                    "parent_prompt_id": self.aliases[parent].prompt_id,
                    "child_prompt_id": self.aliases[child].prompt_id,
                    "source_sha256": digest, "relationship": "Retry",
                })
        return self._build_receipt()

    def _read_record(self, record: dict, source_digest: str) -> None:
        payload = record.get("payload")
        if isinstance(payload, dict) and payload.get("parent_run_key") and payload.get("child_run_key"):
            self._historical_links.append((
                str(payload["parent_run_key"]), str(payload["child_run_key"]), source_digest,
            ))
        antibody_id = record.get("defect_id") or record.get("antibody_id")
        if isinstance(antibody_id, str):
            if antibody_id in RETIRED_PARSER_IDS or "defect:defect:" in antibody_id or "placeholder" in antibody_id.lower():
                self._refused_antibodies.add(antibody_id)
                self._residual("RETIRED_OR_PLACEHOLDER_ANTIBODY", antibody_id)
            else:
                custody = "Candidate"
                if record.get("admitted") is True or str(record.get("status", "")).lower() in ("admitted", "active"):
                    self._residual("PHARMACY_SELF_ADMITTED", antibody_id)
                if record.get("truth_boundary_root"):
                    authenticated = self.admission_verifier and self.admission_verifier(record, source_digest) is True
                    if authenticated:
                        custody = "HumanAdmitted"
                    else:
                        self._residual("EXTERNAL_ADMISSION_MISSING", antibody_id)
                value = {"antibody_id": antibody_id, "custody": custody, "source_sha256": source_digest}
                self.antibodies[antibody_id] = value
                self._persist("AntibodyIndexed", value)
        if record.get("prompt_id"):
            self._pending.append((record, source_digest))

    def _resolve_prompts(self) -> None:
        pending = self._pending
        self._pending = []
        while pending:
            deferred = []
            progress = False
            for record, source_digest in pending:
                source_id = str(record["prompt_id"])
                text = record.get("prompt_text", record.get("prompt"))
                if not isinstance(text, str):
                    self._residual("PROMPT_BYTES_UNAVAILABLE", source_id)
                    continue
                parents = []
                unresolved = False
                for link in record.get("parents", []):
                    if not isinstance(link, dict) or link.get("relationship") not in ("Retry", "Repair", "DirectMutation") or not link.get("witness_receipt_digest"):
                        self._residual("LINEAGE_WITNESS_REQUIRED", source_id)
                        continue
                    parent_id = str(link.get("parent_id", link.get("prompt_id", "")))
                    parent = self.aliases.get(parent_id)
                    if parent is None:
                        unresolved = True
                        break
                    parents.append({
                        "prompt_id": parent.prompt_id, "generation": parent.generation,
                        "relationship": link["relationship"], "witness_receipt_digest": link["witness_receipt_digest"],
                    })
                if unresolved:
                    deferred.append((record, source_digest))
                    continue
                raw = text.encode("utf-8")
                digest = "sha256:" + hashlib.sha256(raw).hexdigest()
                if self.cas:
                    self.cas.store(raw)
                genome = PromptGenomeV1(
                    [{"packet_id": digest, "sha256": digest, "packet_kind": "prompt-artifact"}],
                    record.get("domain_model", {}), parents,
                    generation=max((p["generation"] for p in parents), default=-1) + 1,
                )
                prior = self.aliases.get(source_id)
                if prior and prior != genome:
                    self._residual("SOURCE_PROMPT_IDENTITY_CONFLICT", source_id)
                    continue
                self.aliases[source_id] = genome
                self.registry.register_genome(genome)
                self._persist("GenomeImported", {
                    "genome": genome.to_dict(), "source_sha256": source_digest,
                    "source_prompt_id": source_id,
                    "retrieval_eligibility": "Dormant",
                })
                occurrence = record.get("occurrence_id")
                if isinstance(occurrence, str) and occurrence not in self._occurrences:
                    value = ExecutionOccurrenceV1(
                        occurrence, genome.prompt_id, str(record.get("session_id", "historical")),
                        str(record.get("input_packet_id", "")), str(record.get("output_packet_id", "")),
                    )
                    self.registry.record_occurrence(value)
                    self._occurrences.add(occurrence)
                    self._persist("OccurrenceImported", asdict(value))
                progress = True
            if not progress:
                for record, _ in deferred:
                    self._residual("UNRESOLVED_PARENT", str(record["prompt_id"]))
                break
            pending = deferred

    def _build_receipt(self) -> BackfillReceiptV1:
        residuals = sorted(self.residuals, key=lambda r: (r["code"].encode(), r["subject"].encode()))
        fields = {
            "genomes_created": self.registry.total_genome_count(),
            "occurrences_recorded": len(self._occurrences),
            "antibodies_indexed": len(self.antibodies),
            "antibodies_refused": len(self._refused_antibodies),
            "residuals_recorded": residuals,
        }
        digest = hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()
        receipt = BackfillReceiptV1("sha256:" + digest, **fields)
        if self.output_root:
            (self.output_root / "backfill_receipt.json").write_text(
                json.dumps(asdict(receipt), sort_keys=True, indent=2) + "\n", encoding="utf-8",
            )
        return receipt

HistoricalBackfillEngineV1 = PromptCivBackfillEngineV1
