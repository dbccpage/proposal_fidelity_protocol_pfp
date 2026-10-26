"""Byte-bound external review and append-only prompt custody.

The host must inject an authenticating verifier. Generated status, rank, fitness,
and a receipt-shaped string alone cannot change custody. AuthorityEffect: None.
"""

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from ..domain.models import CustodyTier, PromptGenomeV1, PromptViewV1


@dataclass(frozen=True)
class PromptReviewReceiptV1:
    decision_id: str
    prompt_id: str
    actor_id: str
    outcome: CustodyTier
    scope: tuple[str, ...]
    external_receipt: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.scope) is not tuple or any(type(item) is not str or not item for item in self.scope):
            raise ValueError("REVIEW_SCOPE_INVALID")

    def signed_bytes(self) -> bytes:
        """Stable decision payload; the external signature is excluded."""
        fields = asdict(self)
        del fields["external_receipt"]
        return json.dumps(fields, sort_keys=True, separators=(",", ":")).encode("utf-8")


class PromptReviewVerifier(Protocol):
    def verify(self, receipt: PromptReviewReceiptV1) -> bool:
        """Authenticate the issuer, signature, decision, and permitted scope."""
        ...


@dataclass(frozen=True)
class ApprovedPromptV1:
    prompt_id: str
    decision_id: str
    scope: tuple[str, ...]
    ledger_revision: int
    authority_effect: str = "None"


class PromptCustodyLedgerV1:
    def __init__(self, database: Path, verifier: PromptReviewVerifier) -> None:
        database.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database)
        self.connection.execute("PRAGMA synchronous=FULL")
        self.verifier = verifier
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS prompt_submissions (
                prompt_id TEXT PRIMARY KEY, producer_actor TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS prompt_genomes (
                prompt_id TEXT PRIMARY KEY, genome TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS prohibited_actors (
                prompt_id TEXT NOT NULL, actor_id TEXT NOT NULL, PRIMARY KEY(prompt_id, actor_id));
            CREATE TABLE IF NOT EXISTS prompt_decisions (
                revision INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id TEXT NOT NULL UNIQUE, prompt_id TEXT NOT NULL,
                outcome TEXT NOT NULL, receipt TEXT NOT NULL);
        """)

    def close(self) -> None:
        self.connection.close()

    def submit_candidate(
        self, genome: PromptGenomeV1, producer_actor: str, *, prohibited_actors: tuple[str, ...] = (),
    ) -> None:
        if genome.birth_custody is not CustodyTier.WILD or not producer_actor:
            raise ValueError("WILD_BIRTH_AND_PRODUCER_REQUIRED")
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            prior = self.connection.execute(
                "SELECT producer_actor FROM prompt_submissions WHERE prompt_id=?", (genome.prompt_id,),
            ).fetchone()
            if prior is not None and prior[0] != producer_actor:
                raise ValueError("PROMPT_PRODUCER_IDENTITY_CONFLICT")
            self.connection.execute(
                "INSERT OR IGNORE INTO prompt_submissions VALUES (?, ?)", (genome.prompt_id, producer_actor),
            )
            self.connection.execute(
                "INSERT OR IGNORE INTO prompt_genomes VALUES (?, ?)",
                (genome.prompt_id, json.dumps(genome.to_dict(), sort_keys=True, separators=(",", ":"))),
            )
            self.connection.executemany(
                "INSERT OR IGNORE INTO prohibited_actors VALUES (?, ?)",
                ((genome.prompt_id, actor) for actor in prohibited_actors),
            )
            if prior is None:
                self.connection.execute(
                    "INSERT INTO prompt_decisions(decision_id, prompt_id, outcome, receipt) VALUES (?, ?, ?, ?)",
                    (
                        "submission:" + genome.prompt_id, genome.prompt_id, CustodyTier.CANDIDATE.value,
                        json.dumps({"producer_actor": producer_actor, "authority_effect": "None"}, sort_keys=True),
                    ),
                )

    def genome(self, prompt_id: str) -> PromptGenomeV1:
        stored = self.connection.execute(
            "SELECT genome FROM prompt_genomes WHERE prompt_id=?", (prompt_id,),
        ).fetchone()
        if stored is None:
            raise KeyError(prompt_id)
        genome = PromptGenomeV1.from_dict(json.loads(stored[0]))
        if genome.prompt_id != prompt_id:
            raise ValueError("GENOME_IDENTITY_MISMATCH")
        return genome

    def prohibit_actor(self, prompt_id: str, actor_id: str) -> None:
        with self.connection:
            self.connection.execute("INSERT OR IGNORE INTO prohibited_actors VALUES (?, ?)", (prompt_id, actor_id))

    def view(self, genome: PromptGenomeV1, revision: int | None = None) -> PromptViewV1:
        latest = self.connection.execute("SELECT COALESCE(MAX(revision), 0) FROM prompt_decisions").fetchone()[0]
        if revision is None:
            revision = latest
        if type(revision) is not int or revision < 0 or revision > latest:
            raise ValueError("LEDGER_REVISION_UNAVAILABLE")
        decision = self.connection.execute(
            "SELECT outcome FROM prompt_decisions WHERE prompt_id=? AND revision<=? ORDER BY revision DESC LIMIT 1",
            (genome.prompt_id, revision),
        ).fetchone()
        custody = CustodyTier(decision[0]) if decision else CustodyTier.WILD
        return PromptViewV1(genome.prompt_id, revision, custody)

    def apply(self, genome: PromptGenomeV1, receipt: PromptReviewReceiptV1) -> PromptViewV1:
        if receipt.prompt_id != genome.prompt_id or receipt.authority_effect != "None":
            raise ValueError("REVIEW_SUBJECT_MISMATCH")
        if not receipt.decision_id or not receipt.actor_id or not receipt.external_receipt or self.verifier.verify(receipt) is not True:
            raise PermissionError("EXTERNAL_REVIEW_NOT_AUTHENTICATED")
        with self.connection:
            # Reserve the writer before reading custody; two simultaneous hosts
            # must not both authorize against an obsolete prior state.
            self.connection.execute("BEGIN IMMEDIATE")
            producer = self.connection.execute(
                "SELECT producer_actor FROM prompt_submissions WHERE prompt_id=?", (genome.prompt_id,),
            ).fetchone()
            if producer is None:
                raise ValueError("CANDIDATE_SUBMISSION_REQUIRED")
            if producer[0] == receipt.actor_id:
                raise PermissionError("SELF_ADMISSION_REFUSED")
            prohibited = self.connection.execute(
                "SELECT 1 FROM prohibited_actors WHERE prompt_id=? AND actor_id=?",
                (genome.prompt_id, receipt.actor_id),
            ).fetchone()
            if prohibited:
                raise PermissionError("SELF_ADMISSION_REFUSED")
            payload = json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":"))
            existing = self.connection.execute(
                "SELECT receipt FROM prompt_decisions WHERE decision_id=?", (receipt.decision_id,),
            ).fetchone()
            if existing:
                if existing[0] != payload:
                    raise ValueError("REVIEW_DECISION_IDENTITY_CONFLICT")
                return self.view(genome)
            current = self.view(genome).current_custody
            allowed = {
                CustodyTier.CANDIDATE: {CustodyTier.REVIEWED, CustodyTier.REVOKED},
                CustodyTier.REVIEWED: {CustodyTier.ADMITTED, CustodyTier.REVOKED},
                CustodyTier.ADMITTED: {CustodyTier.SUSPENDED, CustodyTier.REVOKED},
                CustodyTier.SUSPENDED: {CustodyTier.REVIEWED, CustodyTier.REVOKED},
            }
            if receipt.outcome not in allowed.get(current, set()):
                raise ValueError("PROMPT_CUSTODY_TRANSITION_REFUSED")
            if receipt.outcome is CustodyTier.ADMITTED and not receipt.scope:
                raise ValueError("ADMISSION_SCOPE_REQUIRED")
            self.connection.execute(
                "INSERT INTO prompt_decisions(decision_id, prompt_id, outcome, receipt) VALUES (?, ?, ?, ?)",
                (receipt.decision_id, genome.prompt_id, receipt.outcome.value, payload),
            )
            return self.view(genome)

    def approved(self, genome: PromptGenomeV1, requested_scope: str) -> ApprovedPromptV1:
        latest = self.connection.execute(
            "SELECT revision, outcome, receipt FROM prompt_decisions WHERE prompt_id=? ORDER BY revision DESC LIMIT 1",
            (genome.prompt_id,),
        ).fetchone()
        if latest is None or latest[1] != CustodyTier.ADMITTED.value:
            raise PermissionError("PROMPT_NOT_ADMITTED")
        payload = json.loads(latest[2])
        if type(payload["scope"]) is not list or any(type(item) is not str or not item for item in payload["scope"]):
            raise ValueError("REVIEW_SCOPE_INVALID")
        if requested_scope not in payload["scope"]:
            raise PermissionError("REFUSE_SCOPE_ESCALATION")
        return ApprovedPromptV1(genome.prompt_id, payload["decision_id"], tuple(payload["scope"]), latest[0])
