"""Act IV regression screen against buried headstones and pharmacy antibodies.

An unreadable headstone or catalog is a refusal. The screen does not skip the
bad record and continue, and it does not treat antibody text as a regular expression.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.stage.domain import (
    CandidateProposalV1,
    CemeteryHeadstoneV1,
    strict_json_loads,
)

_LOCUS = "omega_engine_woland.use_cases.cemetery_regression"


def _refuse(code: str, message: str) -> Err[Refusal]:
    return Err(Refusal(code, message, _LOCUS))


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _pattern_of(antibody: Any) -> list[str]:
    patterns: list[str] = []
    if isinstance(antibody, dict):
        target = antibody.get("target_pattern", "") or antibody.get("failure_pattern", "")
        failure_class = antibody.get("failure_class", "")
    else:
        target = getattr(antibody, "target_pattern", "") or getattr(antibody, "failure_pattern", "")
        failure_class = getattr(antibody, "failure_class", "")
    if isinstance(target, str) and target:
        patterns.append(target)
    if isinstance(failure_class, str) and failure_class:
        patterns.append(failure_class)
    return patterns


def _antibody_id(antibody: Any) -> str:
    if isinstance(antibody, dict):
        return str(antibody.get("antibody_id", "") or "unknown")
    return str(getattr(antibody, "antibody_id", "") or "unknown")


AdmittedAntibodyReader = Callable[[Mapping[str, Any]], Result[tuple[Any, ...], Refusal]]


def _validate_catalog(payload: Any) -> dict[str, Any]:
    if type(payload) is not dict or type(payload.get("antibodies")) is not dict:
        raise ValueError("catalog and antibodies must be objects")
    for antibody_id, row in payload["antibodies"].items():
        if type(row) is not dict or type(antibody_id) is not str or not antibody_id:
            raise ValueError("antibody entries require nonempty string identities and objects")
        if row.get("antibody_id") != antibody_id:
            raise ValueError("antibody identity differs from catalog key")
        if row.get("pharmacy_status") not in (None, "candidate", "admitted", "rejected", "retired"):
            raise ValueError("unknown pharmacy status")
        if row.get("authority_effect", "None") != "None":
            raise ValueError("antibody carries an unsupported authority effect")
        if any(
            type(row[key]) is not str
            for key in ("target_pattern", "failure_pattern", "failure_class")
            if key in row
        ):
            raise ValueError("antibody patterns must be strings")
    return payload


def _read_catalog(path: Path) -> Result[dict[str, Any], Refusal]:
    try:
        return Ok(_validate_catalog(strict_json_loads(path.read_bytes())))
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        return _refuse(
            "ANTIBODY_CATALOG_UNREADABLE", f"Unreadable pharmacy catalog at {path}: {exc}"
        )


def _select_admitted(
    catalog: Mapping[str, Any],
    reader: AdmittedAntibodyReader | None,
) -> Result[tuple[Any, ...], Refusal]:
    rows = catalog["antibodies"].values()
    if not any(row.get("pharmacy_status") == "admitted" for row in rows):
        return Ok(())
    if reader is None:
        return _refuse(
            "ANTIBODY_ADMISSION_POLICY_UNAVAILABLE",
            "admitted pharmacy rows need the existing OEEIS admission reader",
        )
    try:
        selected = reader(catalog)
        if isinstance(selected, Err):
            return selected
        if not isinstance(selected, Ok):
            raise TypeError("admission reader returned no typed result")
        if any(
            getattr(row, "pharmacy_status", None) != "admitted"
            or getattr(row, "authority_effect", None) != "None"
            for row in selected.value
        ):
            raise ValueError("admission reader returned a non-admitted antibody")
        return Ok(tuple(selected.value))
    except Exception as exc:
        return _refuse("ANTIBODY_CATALOG_UNREADABLE", str(exc))


def _store_catalog(store: Any) -> Result[dict[str, Any], Refusal]:
    try:
        loaded = store.load_antibodies("")
        if isinstance(loaded, Err):
            return loaded
        if not isinstance(loaded, Ok):
            raise TypeError("antibody store returned no typed result")
        entries: dict[str, Any] = {}
        for item in loaded.value:
            row = dict(item) if isinstance(item, Mapping) else item.to_dict()
            antibody_id = row.get("antibody_id")
            if antibody_id in entries and entries[antibody_id] != row:
                raise ValueError("conflicting antibody identity")
            entries[antibody_id] = row
        return Ok(_validate_catalog({"antibodies": entries}))
    except Exception as exc:
        return _refuse("ANTIBODY_CATALOG_UNREADABLE", str(exc))


def _known_antibodies(
    rt: Any, store: Any, repo_root: Path | str | None, reader: AdmittedAntibodyReader | None
) -> Result[tuple[Any, ...], Refusal]:
    catalogs: list[Mapping[str, Any]] = []
    if store is not None and hasattr(store, "load_antibodies"):
        stored = _store_catalog(store)
        if isinstance(stored, Err):
            return stored
        catalogs.append(stored.value)
    directories: list[Path] = []
    if repo_root:
        canonical = Path(repo_root) / "_ic/cdc/antibodies"
        directories.append(
            canonical
            if (canonical / "pharmacy_catalog.json").exists()
            else Path(repo_root) / "omega_engine_epistemic_immune_system/antibodies"
        )
    output_dir = getattr(rt, "operational_output_dir", None) if rt else None
    if output_dir:
        directories.extend(
            (Path(output_dir).parent / "antibodies", Path(output_dir) / "antibodies")
        )
    for directory in dict.fromkeys(directories):
        path = directory / "pharmacy_catalog.json"
        if not path.exists():
            continue
        loaded = _read_catalog(path)
        if isinstance(loaded, Err):
            return loaded
        catalogs.append(loaded.value)
    admitted: list[Any] = []
    for catalog in catalogs:
        selected = _select_admitted(catalog, reader)
        if isinstance(selected, Err):
            return selected
        admitted.extend(selected.value)
    return Ok(tuple(admitted))


def _known_headstones(sink: Any) -> Result[tuple[CemeteryHeadstoneV1, ...], Refusal]:
    try:
        if sink is None:
            return Ok(())
        if hasattr(sink, "load_headstones"):
            loaded = sink.load_headstones()
            if isinstance(loaded, Err):
                return loaded
            if not isinstance(loaded, Ok):
                raise TypeError("cemetery returned no typed result")
            rows = tuple(loaded.value)
        else:
            rows = tuple(getattr(sink, "headstones", ()))
        if any(type(row) is not CemeteryHeadstoneV1 for row in rows):
            raise TypeError("cemetery contains an invalid headstone")
        return Ok(rows)
    except Exception as exc:
        return _refuse("CEMETERY_LOAD_FAILED", str(exc))


def _screen_headstones(
    candidate: CandidateProposalV1, digest: str, headstones: Sequence[CemeteryHeadstoneV1]
) -> Result[None, Refusal]:
    for headstone in headstones:
        buried_digest = headstone.candidate_payload_sha256 or ""
        digest_match = bool(buried_digest and digest) and buried_digest.removeprefix(
            "sha256:"
        ) == digest.removeprefix("sha256:")
        evidence_match = bool(digest) and digest in headstone.evidence_refs
        if digest_match or evidence_match or headstone.candidate_id == candidate.candidate_id:
            return _refuse(
                "REGRESSION_AGAINST_CEMETERY_REFUSED",
                f"Candidate '{candidate.candidate_id}' matches headstone '{headstone.headstone_id}' (cause: {headstone.cause_of_death}).",
            )
    return Ok(None)


def _screen_antibodies(
    candidate: CandidateProposalV1, text: str, antibodies: Sequence[Any]
) -> Result[None, Refusal]:
    if not text:
        return Ok(None)
    for antibody in antibodies:
        for pattern in _pattern_of(antibody):
            if pattern in text:
                return _refuse(
                    "REGRESSION_AGAINST_ANTIBODY_REFUSED",
                    f"Candidate '{candidate.candidate_id}' matches admitted antibody '{_antibody_id(antibody)}' (pattern: {pattern}).",
                )
    return Ok(None)


def screen_known_regressions(
    rt: Any,
    candidates: Sequence[CandidateProposalV1],
    candidate_payloads: Mapping[str, bytes] | None,
    *,
    cemetery: Any | None = None,
    antibody_store: Any | None = None,
    repo_root: Path | str | None = None,
    ablation_flags: Mapping[str, bool] | None = None,
    admitted_antibody_reader: AdmittedAntibodyReader | None = None,
) -> Result[None, Refusal]:
    """Screen exact buried candidates and human-admitted pharmacy patterns only.

    ARMED, ACTIVE and candidate sighting metadata never substitutes for pharmacy
    admission. The composition root injects the existing OEEIS admission reader.
    """
    if (ablation_flags and ablation_flags.get("no_cemetery_defense")) or not candidates:
        return Ok(None)
    emitters = getattr(rt, "emitters", None) if rt else None
    cemetery_sink = cemetery if cemetery is not None else getattr(emitters, "cemetery", None)
    antibody_sink = (
        antibody_store if antibody_store is not None else getattr(emitters, "antibodies", None)
    )
    headstones = _known_headstones(cemetery_sink)
    if isinstance(headstones, Err):
        return headstones
    antibodies = _known_antibodies(rt, antibody_sink, repo_root, admitted_antibody_reader)
    if isinstance(antibodies, Err):
        return antibodies
    payloads = candidate_payloads or {}
    for candidate in candidates:
        payload = payloads.get(candidate.candidate_id)
        digest = (
            _digest(payload)
            if payload is not None
            else (candidate.artifact_refs[0] if candidate.artifact_refs else "")
        )
        text = payload.decode("utf-8", errors="replace") if payload is not None else ""
        buried = _screen_headstones(candidate, digest, headstones.value)
        if isinstance(buried, Err):
            return buried
        screened = _screen_antibodies(candidate, text, antibodies.value)
        if isinstance(screened, Err):
            return screened
    return Ok(None)


def ingest_falsified_candidate(
    candidate: CandidateProposalV1,
    candidate_payload: bytes,
    cause_of_death: str,
    killing_seat_id: str,
    scene_id: str = "scene_fugu_rejection",
    run_key: str = "fugu_v2_loop",
    round_index: int = 0,
    evidence_refs: Sequence[str] = (),
    cemetery_sink: Any | None = None,
) -> Result[CemeteryHeadstoneV1, Refusal]:
    """Ingest a failed candidate proposal directly into an immutable CemeteryHeadstoneV1 record.

    Fails closed if the candidate_id, cause_of_death, or payload digest is missing.
    """
    if not candidate.candidate_id:
        return _refuse("CANDIDATE_ID_EMPTY", "Cannot bury a candidate without a candidate_id")
    if not cause_of_death.strip():
        return _refuse(
            "CAUSE_OF_DEATH_EMPTY", "Cemetery headstone requires an explicit cause of death"
        )

    payload_digest = (
        _digest(candidate_payload)
        if candidate_payload
        else (candidate.artifact_refs[0] if candidate.artifact_refs else "")
    )
    if not payload_digest:
        return _refuse(
            "PAYLOAD_DIGEST_EMPTY", "Cannot record headstone without candidate payload or digest"
        )

    all_evidence = tuple(list(evidence_refs) + [payload_digest])
    headstone = CemeteryHeadstoneV1(
        candidate_id=candidate.candidate_id,
        run_key=run_key,
        scene_id=scene_id,
        cause_of_death=cause_of_death,
        killing_seat_id=killing_seat_id,
        evidence_refs=all_evidence,
        candidate_payload_sha256=payload_digest,
        round_index=round_index,
    )

    if cemetery_sink is not None:
        if hasattr(cemetery_sink, "record_headstone"):
            record_res = cemetery_sink.record_headstone(headstone)
            if hasattr(record_res, "is_err") and record_res.is_err:
                return Err(record_res.unwrap_err())
        elif hasattr(cemetery_sink, "headstones") and isinstance(cemetery_sink.headstones, list):
            cemetery_sink.headstones.append(headstone)

    return Ok(headstone)


def distill_pharmacy_antibody(
    headstone: CemeteryHeadstoneV1,
    failure_pattern: str,
    failure_class: str = "REGRESSION_DEFECT",
    antibody_id: str | None = None,
) -> Result[dict[str, Any], Refusal]:
    """Synthesize an inactive pharmacy candidate from a buried cemetery headstone.

    Fails closed if the failure pattern is empty.
    """
    if not failure_pattern.strip():
        return _refuse(
            "FAILURE_PATTERN_EMPTY", "Cannot distill an antibody with an empty failure pattern"
        )

    ab_id = (
        antibody_id
        or f"ab_{headstone.candidate_id}_{hashlib.sha256(failure_pattern.encode()).hexdigest()[:8]}"
    )
    antibody_record: dict[str, Any] = {
        "antibody_id": ab_id,
        "failure_class": failure_class,
        "target_pattern": failure_pattern,
        "source_headstone_id": headstone.headstone_id,
        "killing_seat_id": headstone.killing_seat_id,
        "cause_of_death": headstone.cause_of_death,
        "status": "PENDING",
        "pharmacy_status": "candidate",
        "authority_effect": "None",
        "constraint_type": "ProjectOut",
        "operatorizability": "repairable",
        "action": "repair",
        "severity": "P1",
        "description": headstone.cause_of_death,
        "negative_fixture": "",
        "positive_fixture": "",
        "evidence_sha256": hashlib.sha256(
            f"{headstone.headstone_id}:{failure_pattern}".encode("utf-8")
        ).hexdigest(),
        "source_run_id": headstone.run_key,
        "source_task_id": "",
    }
    return Ok(antibody_record)


def append_antibody_to_catalog(
    catalog_path: Path, antibody: dict[str, Any]
) -> Result[None, Refusal]:
    """Atomically store a candidate; preserve corrupt bytes and judged records.

    Admission belongs to the pharmacy's separate human admission path. This
    helper cannot promote a status or replace an admitted/rejected/retired row.
    """
    temporary: Path | None = None
    try:
        catalog_path = Path(catalog_path)
        if "_intelligence" in catalog_path.parts:
            raise ValueError("active pharmacy writes require the canonical _ic route")
        antibody_id = antibody.get("antibody_id")
        _validate_catalog({"antibodies": {antibody_id: antibody}})
        if antibody.get("pharmacy_status") != "candidate":
            raise ValueError("distillation may persist candidate status only")
        payload = (
            _validate_catalog(strict_json_loads(catalog_path.read_bytes()))
            if catalog_path.exists()
            else {"antibodies": {}, "authority_effect": "None"}
        )
        prior = payload["antibodies"].get(antibody_id)
        if prior is not None and prior.get("pharmacy_status") not in (None, "candidate"):
            raise ValueError("cannot overwrite a judged pharmacy record")
        payload["antibodies"][antibody_id] = dict(antibody)
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(
            prefix=f".{catalog_path.name}.", suffix=".tmp", dir=catalog_path.parent
        )
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write((json.dumps(payload, indent=2) + "\n").encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        if catalog_path.exists():
            shutil.copy2(catalog_path, catalog_path.with_suffix(".json.bak"))
        temporary.replace(catalog_path)
        return Ok(None)
    except (OSError, TypeError, ValueError, AttributeError) as exc:
        return _refuse(
            "ANTIBODY_CATALOG_WRITE_ERROR",
            f"Cannot update pharmacy catalog at {catalog_path}: {exc}",
        )
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass  # A leftover temporary file must not hide the typed write result.
