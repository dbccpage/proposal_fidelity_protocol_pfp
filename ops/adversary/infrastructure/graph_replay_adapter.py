"""Production intelligence replay with explicit source custody anchors.

Persisted runs require the externally retained receipt SHA. Same-run mining
pins freshly produced event bytes before replay. Neither path trusts verdict
flags, self-reported zero measurements, or caller-authored source events.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from operations.domain.rop.result import Ok, Refusal, Result
from adversary.domain.evidence import CandidateCheckV1, CheckerVerdict, sha256_ref
from adversary.domain.graph_task import GraphCandidateEvaluationV1, GraphTaskV1, read_json
from adversary.domain.intelligence_mining import (
    MiningObservationV1,
    ReplayedMiningEvidenceV1,
    canonical_bytes,
)
from adversary.infrastructure.graph_adapter import (
    GraphCandidateChecker,
    NativeGraphEvaluator,
    refusal,
)
from adversary.infrastructure.native import DefaultNativeOperationPort
from adversary.use_cases.intelligence_miner import mine_intelligence
from adversary.use_cases.persistence import LEGACY_DDA_TAPE, recompute_receipt_id
from adversary.use_cases.run_graph import source_event


@dataclass(frozen=True, slots=True)
class GraphReplaySource:
    candidate_bytes: bytes
    event_bytes: bytes
    checker_receipt_bytes: bytes
    native_evidence_bytes: bytes
    challenge_bytes: bytes = b""


class GraphSourceCustody:
    def __init__(self, task: GraphTaskV1, sources: tuple[GraphReplaySource, ...]) -> None:
        self.task = task
        self.sources = MappingProxyType(
            {sha256_ref(source.event_bytes): source for source in sources}
        )
        self._task_anchor = task.to_bytes()
        self._source_anchors = tuple(self.sources.items())

    def verify_snapshot(self) -> None:
        if (
            self.task.to_bytes() != self._task_anchor
            or tuple(self.sources.items()) != self._source_anchors
        ):
            raise ValueError("source custody snapshot changed")

    def authenticate(self, observation: MiningObservationV1) -> GraphReplaySource:
        self.verify_snapshot()
        source = self.sources.get(observation.source_event_ref)
        if (
            source is None
            or source.event_bytes != observation.source_event_bytes
            or source.candidate_bytes != observation.candidate_bytes
            or self.task.to_bytes() != observation.carrier_bytes
        ):
            raise ValueError(
                "source event, candidate or carrier bytes do not match the custody anchor"
            )
        event = read_json(source.event_bytes)
        if event.get("challenge_ref") != (
            sha256_ref(source.challenge_bytes) if source.challenge_bytes else None
        ):
            raise ValueError("source challenge bytes do not match their custody digest")
        if (
            event["task_ref"] != observation.carrier_ref
            or event["candidate_ref"] != observation.subject_ref
            or event["trigger"] != observation.trigger
            or event["failure_class"] != observation.failure_class
            or event["target_pattern"] != observation.target_pattern
            or event["checker_receipt_ref"] != sha256_ref(source.checker_receipt_bytes)
            or event["native_evidence_ref"]
            != (sha256_ref(source.native_evidence_bytes) if source.native_evidence_bytes else None)
        ):
            raise ValueError("source event fields contradict their retained evidence bytes")
        return source

    def observations(self) -> tuple[MiningObservationV1, ...]:
        observations = []
        for _, source in sorted(self.sources.items()):
            event = read_json(source.event_bytes)
            if event["trigger"] not in {
                "EXACT_REPAIR",
                "STRUCTURAL_DEFECT",
                "DEFECT_HUNTER_REFUTATION",
                "FALSE_GREEN",
            }:
                continue
            observations.append(
                MiningObservationV1(
                    sha256_ref(source.candidate_bytes),
                    source.candidate_bytes,
                    self.task.to_bytes(),
                    source.event_bytes,
                    event["trigger"],
                    event["failure_class"],
                    event["target_pattern"],
                )
            )
        return tuple(observations)


class PersistedGraphCustody(GraphSourceCustody):
    """Check historical layouts and fresh single-DDC bundles against their pin."""

    def __init__(self, directory: Path | str, receipt_ref: str) -> None:
        self.directory, self.receipt_ref = Path(directory), receipt_ref
        task, sources = self._load()
        super().__init__(task, sources)

    def _load(self) -> tuple[GraphTaskV1, tuple[GraphReplaySource, ...]]:
        folder = self.directory
        expected_names = {"receipt.json", "novella.md", "ddc.jsonl", "summary.json"}
        fresh_names = {"receipt.json", "uns.md", "ddc.jsonl", "summary.json", "uts.jsonl"}

        def redirected(path: Path) -> bool:
            info = path.stat(follow_symlinks=False)
            return path.is_symlink() or bool(
                getattr(info, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            )

        if redirected(folder):
            raise ValueError("graph run directory must not be redirected")
        names = {path.name for path in folder.iterdir()}
        # MAM is an optional, separately digest-bound projection of current v2
        # bundles. The native verifier below validates its files and receipts.
        has_mam = "mam" in names
        if has_mam:
            if redirected(folder / "mam") or not (folder / "mam").is_dir():
                raise ValueError("MAM must be a plain directory")
            names = names - {"mam"}
            if names != fresh_names:
                raise ValueError("MAM requires the current canonical graph bundle")
        legacy = LEGACY_DDA_TAPE in names
        retained = expected_names | {LEGACY_DDA_TAPE} if legacy else expected_names
        legacy_only = (expected_names - {"ddc.jsonl"}) | {LEGACY_DDA_TAPE}
        if names not in (retained, retained | {"uts.jsonl"}, fresh_names, legacy_only):
            raise ValueError("graph run must contain the versioned canonical files")
        expected_names = names
        if any(
            redirected(folder / name) or not (folder / name).is_file() for name in expected_names
        ):
            raise ValueError("custody files must be regular files")
        raw = (folder / "receipt.json").read_bytes()
        if sha256_ref(raw) != self.receipt_ref:
            raise ValueError("externally pinned receipt bytes changed")
        receipt = read_json(raw)
        version = receipt.get("bundle_schema_version")
        fresh = version == "core.adversary.reported-run-bundle.v2"
        reported = version in ("core.adversary.reported-run-bundle.v1", "core.adversary.reported-run-bundle.v2")
        if fresh != (names == fresh_names):
            raise ValueError("graph bundle layout/schema disagree")
        if reported != ("uts.jsonl" in names):
            raise ValueError("reported graph bundle schema/files disagree")
        if reported:
            from adversary.infrastructure.native import value

            value("verify_reported_bundle", run_dir=str(folder))
        if (
            receipt.get("schema_version") != "core.adversary.graph-run-receipt.v1"
            or receipt.get("authority_effect") != "None"
        ):
            raise ValueError("graph receipt header refused")
        digests = [("uns.md", "uns_sha256"), ("ddc.jsonl", "ddc_sha256"),
                   ("summary.json", "summary_sha256"), ("uts.jsonl", "uts_sha256")] if fresh else [
            ("novella.md", "novella_sha256"), ("summary.json", "summary_sha256")]
        if not fresh:
            if "ddc.jsonl" in names:
                digests.append(("ddc.jsonl", "ddc_sha256"))
            if legacy:
                digests.append((LEGACY_DDA_TAPE, "dda_actions_sha256"))
        for name, field in digests:
            if sha256_ref((folder / name).read_bytes())[7:] != receipt[field]:
                raise ValueError(f"custody digest mismatch: {name}")
        if legacy and "ddc.jsonl" in names and (folder / "ddc.jsonl").read_bytes() != (folder / LEGACY_DDA_TAPE).read_bytes():
            raise ValueError("DDC and DDA tape bytes diverge")
        summary = read_json((folder / "summary.json").read_bytes(), 16_777_216)
        if (
            summary.get("receipt_id") != receipt["receipt_id"]
            or recompute_receipt_id(folder, native_support=DefaultNativeOperationPort()) != receipt["receipt_id"]
        ):
            raise ValueError("content-addressed run identity changed")
        task = GraphTaskV1.from_bytes(bytes.fromhex(summary["task_hex"]))
        if task.task_ref != summary["task_ref"] or task.task_ref != receipt["task_ref"]:
            raise ValueError("persisted graph task was substituted")
        result = summary["result"]
        if result["task_ref"] != task.task_ref:
            raise ValueError("result names a different task")
        from adversary.use_cases.persistence import run_tape_path

        tape = run_tape_path(folder).read_bytes()
        head = None
        payloads = []
        for sequence, line in enumerate(tape.splitlines()):
            row = read_json(line)
            material = json.dumps(
                {"sequence": sequence, "parent_sha256": head, "payload": row["payload"]},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            digest = hashlib.sha256(material).hexdigest()
            if (
                row["sequence"] != sequence
                or row["parent_sha256"] != head
                or row["record_sha256"] != digest
            ):
                raise ValueError("source-event tape chain changed")
            head = digest
            payloads.append(canonical_bytes(row["payload"]))
        if head != receipt.get("ddc_head_sha256" if fresh else "dda_head_sha256"):
            raise ValueError("source-event tape tip changed")
        events = tuple(bytes.fromhex(row["event_hex"]) for row in result["source_events"])
        if list(events) != payloads or any(
            sha256_ref(raw) != row["event_ref"]
            for raw, row in zip(events, result["source_events"], strict=True)
        ):
            raise ValueError("summary substituted source-event bytes")
        evaluations = {
            row["candidate_ref"]: row
            for row in (result["original_diagnosis"], *result["candidate_evaluations"])
        }
        challenges = {
            sha256_ref(canonical_bytes(row)): canonical_bytes(row) for row in result["challenges"]
        }
        sources = []
        for raw in events:
            event = read_json(raw)
            row = evaluations[event["candidate_ref"]]
            candidate = bytes.fromhex(row["candidate_hex"])
            checker = bytes.fromhex(row["check"]["checker_receipt_hex"])
            native = bytes.fromhex(row["native_evidence_hex"])
            if sha256_ref(candidate) != row["candidate_ref"] or row["native_evidence_ref"] != (
                sha256_ref(native) if native else None
            ):
                raise ValueError("candidate or certificate digest changed")
            sources.append(
                GraphReplaySource(
                    candidate, raw, checker, native, challenges.get(event.get("challenge_ref"), b"")
                )
            )
        return task, tuple(sources)

    def verify_snapshot(self) -> None:
        super().verify_snapshot()
        # Recheck the pin before replay and after every mutable native subprocess.
        task, sources = self._load()
        if task != self.task or {sha256_ref(s.event_bytes): s for s in sources} != self.sources:
            raise ValueError("persisted custody anchors changed")


class GraphIntelligenceReplayAdapter:
    def __init__(
        self,
        custody: GraphSourceCustody,
        evaluator: NativeGraphEvaluator,
        checker: GraphCandidateChecker | None = None,
    ) -> None:
        self.custody = custody
        self.evaluator = NativeGraphEvaluator(evaluator.host, custody_check=custody.verify_snapshot)
        self.checker = checker or GraphCandidateChecker()

    def replay(self, observation: MiningObservationV1) -> Result[ReplayedMiningEvidenceV1, Refusal]:
        try:
            source = self.custody.authenticate(observation)
            check = self.checker.check(self.custody.task, observation.candidate_bytes)
            if check.checker_receipt_bytes != source.checker_receipt_bytes:
                return refusal(
                    "MINING_CHECK_REPLAY_MISMATCH",
                    "stored permission/fidelity check was not reproduced",
                )
            binding = {
                "observation_ref": observation.observation_ref,
                "candidate_content_sha256": observation.subject_ref,
                "carrier_context_sha256": observation.carrier_ref,
                "source_event_sha256": observation.source_event_ref,
            }
            payload = {
                **read_json(check.checker_receipt_bytes),
                **binding,
                "trigger": observation.trigger,
                "failure_class": observation.failure_class,
                "target_pattern": observation.target_pattern,
            }
            if observation.trigger == "DEFECT_HUNTER_REFUTATION":
                if check.verdict is not CheckerVerdict.ACCEPTED or not source.challenge_bytes:
                    return refusal(
                        "MINING_CHALLENGE_MISSING",
                        "native refutation requires its permitted candidate and actual challenge bytes",
                    )
                scored = self.evaluator.replay(
                    self.custody.task, observation.candidate_bytes, source.native_evidence_bytes
                )
                if scored.is_err:
                    return scored
                proof = read_json(source.challenge_bytes)
                challenge_bytes = bytes.fromhex(proof["turn"]["output_hex"])
                challenge = read_json(challenge_bytes)
                expected_class, expected_pattern = (
                    ("GRAPH_INCONSISTENT", "declared_graph_exactness")
                    if challenge["obligation"] == "CONSISTENCY"
                    else ("GRAPH_OBSERVER_BLIND_SPOT", "declared_edge_residual_coverage")
                )
                replay = self.evaluator.challenge(
                    self.custody.task, scored.unwrap(), challenge_bytes
                )
                if (
                    replay.is_err
                    or read_json(replay.unwrap()) != proof["replay"]
                    or read_json(replay.unwrap()).get("result", {}).get("valid") is not True
                    or observation.failure_class != expected_class
                    or observation.target_pattern != expected_pattern
                ):
                    return refusal(
                        "MINING_CHALLENGE_NOT_REPRODUCED",
                        "candidate-bound counterexample was not reproduced by Rust",
                    )
                payload.update(
                    verdict="REJECTED",
                    checker_id="core.graph-native-challenge.v1",
                    reason="Native counterexample reproduced on the declared candidate and carrier.",
                    certificate_hex=source.native_evidence_bytes.hex(),
                    challenge_hex=source.challenge_bytes.hex(),
                )
                raw = canonical_bytes(payload)
                bound = CandidateCheckV1(
                    CheckerVerdict.REJECTED,
                    check.candidate_id,
                    observation.subject_ref,
                    payload["checker_id"],
                    sha256_ref(raw),
                    raw,
                    payload["reason"],
                )
                return Ok(ReplayedMiningEvidenceV1(observation.observation_ref, bound))
            raw = canonical_bytes(payload)
            bound_check = CandidateCheckV1(
                check.verdict,
                check.candidate_id,
                check.candidate_content_sha256,
                check.checker_id,
                sha256_ref(raw),
                raw,
                check.reason,
            )
            if observation.trigger != "EXACT_REPAIR":
                if check.verdict is not CheckerVerdict.REJECTED or source.native_evidence_bytes:
                    return refusal(
                        "MINING_DEFECT_NOT_REPRODUCED",
                        "independent graph checker did not reproduce a typed structural defect",
                    )
                return Ok(ReplayedMiningEvidenceV1(observation.observation_ref, bound_check))
            scored = self.evaluator.replay(
                self.custody.task, observation.candidate_bytes, source.native_evidence_bytes
            )
            if scored.is_err:
                return scored
            evaluation = scored.unwrap()
            if not evaluation.verified_repair:
                return refusal(
                    "MINING_REPAIR_NOT_REPRODUCED",
                    "native joint zero and sound observer coverage were not reproduced",
                )
            native = read_json(source.native_evidence_bytes)["evaluation"]["result"]
            lggr = self.evaluator.invoke("lggr_soundness", native["coverage_request"])
            if lggr.is_err:
                return lggr
            if (
                lggr.unwrap()["result"] != native["observer_coverage"]
                or lggr.unwrap()["result"].get("sound") is not True
            ):
                return refusal(
                    "MINING_LGGR_REPLAY_MISMATCH",
                    "declared observer maps did not reproduce sound coverage",
                )
            measurement = {
                **binding,
                **evaluation.measurement.to_dict(),
                "certificate_hex": source.native_evidence_bytes.hex(),
                "certificate_sha256": sha256_ref(source.native_evidence_bytes),
            }
            # Positive rank evidence retains the complete maps and replay report; no fictitious vector.
            witness = canonical_bytes(
                {
                    "task_ref": observation.carrier_ref,
                    "candidate_ref": observation.subject_ref,
                    "graph_input_digest": native["input_digest"],
                    "request": native["coverage_request"],
                    "replay": lggr.unwrap(),
                }
            )
            joint = canonical_bytes(
                {
                    **binding,
                    "status": "CERTIFIED",
                    "witness_hex": witness.hex(),
                    "witness_sha256": sha256_ref(witness),
                    "authority_effect": "None",
                }
            )
            return Ok(
                ReplayedMiningEvidenceV1(
                    observation.observation_ref,
                    bound_check,
                    evaluation.measurement,
                    canonical_bytes(measurement),
                    joint,
                )
            )
        except (ValueError, TypeError, KeyError, OSError, UnicodeDecodeError) as exc:
            return refusal("MINING_SOURCE_CUSTODY_REFUSED", str(exc))


class GraphLearningAdapter:
    def __init__(self, evaluator: NativeGraphEvaluator, recurrence_threshold: int = 2) -> None:
        self.evaluator, self.recurrence_threshold = evaluator, recurrence_threshold

    def harvest(
        self,
        task: GraphTaskV1,
        evaluations: tuple[GraphCandidateEvaluationV1, ...],
        source_events: tuple[bytes, ...],
        challenges: tuple[bytes, ...] = (),
    ) -> bytes:
        sources = []
        proofs = {sha256_ref(raw): raw for raw in challenges}
        for item, raw in zip(evaluations, source_events, strict=True):
            challenge = proofs.get(read_json(raw).get("challenge_ref"), b"")
            if source_event(task, item, challenge) != raw:
                raise ValueError("graph learning source event changed before custody pinning")
            sources.append(
                GraphReplaySource(
                    item.candidate_bytes,
                    raw,
                    item.check.checker_receipt_bytes,
                    item.native_evidence_bytes,
                    challenge,
                )
            )
        custody = GraphSourceCustody(task, tuple(sources))
        replay = GraphIntelligenceReplayAdapter(custody, self.evaluator)
        harvest = mine_intelligence(
            custody.observations(),
            replay_port=replay,
            recurrence_threshold=self.recurrence_threshold,
            native_support=DefaultNativeOperationPort(),
        )
        return canonical_bytes(harvest.to_dict())
