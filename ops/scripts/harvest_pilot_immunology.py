#!/usr/bin/env python3
"""Publish reviewed pilot detector candidates; never admit or mine filenames.

Definitions and finite controls are data. Existing historical rules and patterns
remain unchanged. This entrypoint does not claim to scan all pilot directories.
The former 22-row registry is retained in Git revision
370a629351e8d2c130bcc136799258b4914cc587 and its published pilot/antibody/pattern
files. New harvesting requires an explicit candidate packet with executable
controls; historical registry membership does not grant admission.
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eis.domain.pharmacy_catalog import PharmacyCatalogRepository
from eis.domain.pharmacy_models import Antibody
from eis.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
    release_publication_marker,
)
from eis.domain.pharmacy_search import rule_content_bytes, rule_content_sha256

DEFAULT_DEFINITIONS = Path("eis/antibodies/definitions/pilot035_candidates.json")


def load_candidates(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    packet = json.loads(path.read_text(encoding="utf-8"))
    if packet.get("schema_version") != "core.pharmacy.pilot-candidates.v1":
        raise ValueError("PILOT_CANDIDATE_SCHEMA_UNSUPPORTED")
    records = packet["candidates"]
    if not isinstance(records, list) or not records:
        raise ValueError("PILOT_CANDIDATES_REQUIRED")
    for record in records:
        if record.get("pharmacy_status") != "candidate" or record.get("admission"):
            raise ValueError("PHARMACY_CANDIDATE_REQUIRED")
        if rule_content_sha256(record) != record.get("rule_sha256"):
            raise ValueError("PILOT_RULE_DIGEST_MISMATCH")
        if not record["antibody_id"].endswith(record["rule_sha256"][:12]):
            raise ValueError("PILOT_REVISION_ID_UNBOUND")
        detector = re.compile(record["target_pattern"])
        controls = record["controls"]
        harmful = controls["must_match"]
        benign = controls["must_not_match"]
        if not harmful or not benign:
            raise ValueError("PILOT_DUAL_CONTROLS_REQUIRED")
        if any(not detector.search(item) for item in harmful) or any(detector.search(item) for item in benign):
            raise ValueError("PILOT_FIXTURE_POLARITY_MISMATCH")
        if record["negative_fixture"] not in harmful or record["positive_fixture"] not in benign:
            raise ValueError("PILOT_PRIMARY_FIXTURES_NOT_CONTROLLED")
    return packet, records


def admission_packet(packet: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Review requests use the existing external-admission request bindings."""
    source_digest = hashlib.sha256(
        json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    requests = []
    for record in records:
        digest = "sha256:" + record["rule_sha256"]
        requests.append({
            "antibody_id": record["antibody_id"],
            "rule_bytes_utf8": rule_content_bytes(record).decode("utf-8"),
            "scope": packet["admission_scope"],
            "fixture_check": "PYTHON_REGEX_DUAL_CONTROLS_PASSED",
            "observation_kind": "fixture_reproduction",
            "controls": record["controls"],
            "request": {
                "schema_version": "core.pharmacy.external-admission-request.v1",
                "candidate_digest": digest,
                "producer_system": "eis",
                "source_manifest_digest": "sha256:" + source_digest,
                "positive_fixture_digest": "sha256:" + hashlib.sha256(record["positive_fixture"].encode()).hexdigest(),
                "negative_fixture_digest": "sha256:" + hashlib.sha256(record["negative_fixture"].encode()).hexdigest(),
                "status": "CANDIDATE", "authority_effect": "None",
            },
            "human_decision": None,
            "assessment": "PENDING_EXISTING_NATIVE_ELIGIBILITY_AND_HUMAN_ADMISSION",
        })
    return {"status": "PENDING_ADMISSION", "authority_effect": "None", "requests": requests}


def harvest_and_publish(
    repo_root: Path = REPO_ROOT, *, definitions_file: Path | None = None,
    request_path: Path | None = None,
) -> dict[str, Any]:
    definitions = definitions_file or repo_root / DEFAULT_DEFINITIONS
    packet, definitions_records = load_candidates(definitions)
    records = []
    for definition in definitions_records:
        record = Antibody.farm(**{key: definition[key] for key in (
            "antibody_id", "failure_class", "target_pattern", "constraint_type", "operatorizability",
            "action", "severity", "description", "negative_fixture", "positive_fixture",
        )}, evidence_sha256=definition["rule_sha256"]).to_dict()
        record.update(definition)
        records.append(record)
    repository = PharmacyCatalogRepository(
        repo_root,
        telemetry_dir=repo_root / "eis/antibodies/candidates",
        byte_writer=filesystem_byte_writer,
        byte_source=filesystem_catalog_bytes,
    )
    source = hashlib.sha256(json.dumps(
        packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
    decision = repository.publish_candidates(records, observation_id="fixture-reproduction:" + source)
    release_publication_marker(decision.marker_path)
    changed = list(decision.changed)
    request = admission_packet(packet, definitions_records)
    if request_path is not None:
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    current = repository.load_catalog()["antibodies"]
    pending = any(current[r["antibody_id"]]["pharmacy_status"] == "candidate" for r in records)
    return {"changed_ids": changed, "candidate_ids": [r["antibody_id"] for r in records],
            "admission_status": "PENDING_ADMISSION" if pending else "EXISTING_JUDGEMENTS_PRESERVED",
            "authority_effect": "None"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--definitions", type=Path)
    parser.add_argument("--admission-request", type=Path)
    parser.add_argument("--repair-projections", action="store_true")
    args = parser.parse_args()
    if args.repair_projections:
        release_publication_marker(PharmacyCatalogRepository(
            args.repo_root,
            byte_writer=filesystem_byte_writer,
            byte_source=filesystem_catalog_bytes,
        ).repair_projections())
        print(json.dumps({"status": "PROJECTIONS_REBUILT_FROM_CATALOG"}))
    else:
        print(json.dumps(harvest_and_publish(args.repo_root, definitions_file=args.definitions,
                                            request_path=args.admission_request)))


if __name__ == "__main__":
    main()
