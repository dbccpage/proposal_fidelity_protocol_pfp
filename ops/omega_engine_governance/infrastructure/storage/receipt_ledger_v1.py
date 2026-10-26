"""A content-addressed, hash-chained receipt ledger that verifies its own store.

`EPIC-OE-OEWAS-005` asks for a `ContentAddressedReceiptLedger` "recording all
operad evaluations, gate checks, and candidate dispatches" (deliverable 3),
"automated corruption recovery and integrity verification checks
(`PRAGMA integrity_check`)" (deliverable 4), receipts that are "append-only and
cryptographically chained" (Immutable Ledger Law), and "BLAKE3-hashed execution
receipts" (acceptance criterion 3).

Four things were measured before writing any of it.

**1. `PRAGMA integrity_check` appears nowhere in this repository.** Neither
existing SQLite store runs it, so a corrupt page would be found by a failing
query rather than by a check. A ledger nobody verifies is a claim about history
rather than a record of it.

**2. Content addressing is not chaining, and the epic asks for both.** A digest
over a receipt's own content proves that *that receipt* was not edited. It says
nothing about whether a receipt was *removed*, or whether two were reordered --
every surviving row still hashes correctly. So the two properties are built
separately here: `receipt_id` is the content address, and `chain_digest` folds
each receipt into the digest of everything recorded before it. Deleting a middle
row leaves every content address intact and breaks the chain at that point,
which is exactly the tamper the content address cannot see.

**3. Append-only is enforced by the database, not by this class refraining.**
Two SQL triggers refuse `UPDATE` and `DELETE` on `receipts`. A rule that lives
only in a method nobody is obliged to call is a rule in prose. The triggers make
tampering through this connection impossible rather than merely undocumented,
and the chain catches tampering that goes around them.

**4. The estate disagrees with itself about the receipt hash.** The epic says
BLAKE3. The canonical digest helper --
`omega_engine_pfp.domain.entities.research_packets.digest_payload` -- is
SHA-256, and its validator `_require_sha256` rejects anything that is not a
SHA-256 digest. The filesystem receipt store at
`omega_engine/crates/runtime/prompt_receipt_store.py` accepts *either*
`receipt_blake3` or `receipt_sha256` with no rule saying which. This ledger
follows the epic and uses BLAKE3, and names the algorithm inside the identity
string (`blake3:...`) so that a receipt says which function produced it instead
of leaving a bare 64 hex characters to be guessed at. `test_receipt_ledger.py`
pins the disagreement so it stays visible rather than being resolved silently by
whichever module a reader happens to open first.

Two pragma divergences were measured between the estate's existing stores, and
this ledger takes the stricter setting from each:

| pragma | workflows store | governance store | here |
| --- | --- | --- | --- |
| `journal_mode` | WAL, set in Python | WAL, set in `governance_schema.sql` | WAL, asserted after setting |
| `busy_timeout` | 30000 | 5000 (Python's `connect` default, never set) | 30000 |
| `synchronous` | FULL, explicit | build default | FULL, explicit |

The `busy_timeout` gap is the one that bites: under write contention the
governance store gives up after five seconds and the workflows store waits
thirty. Neither is wrong; disagreeing silently is.

**A methodological note, recorded because it nearly became a false finding.**
Grepping the governance unit of work for `journal_mode` returns nothing, which
reads as "WAL was never enabled" -- and the module is *named* for WAL. It is in
WAL mode: `governance_schema.sql:4` sets the pragma in SQL rather than in
Python. The empirical check caught what the grep would have gotten wrong.
`effective_pragmas` exists for that reason: it reads the mode back rather than
trusting that setting it worked.

`AuthorityEffect: None`. Recording that something happened is not deciding it
was correct.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import blake3

RECEIPT_SCHEMA_V1 = "omega.oewas.receipt.v1"

# The algorithm is part of the identity string rather than something a reader
# infers from the digest length. BLAKE3 and SHA-256 both print 64 hex
# characters, so an unprefixed digest is genuinely ambiguous.
DIGEST_PREFIX = "blake3:"

# The kinds the epic names. Closed: an open vocabulary would let a caller invent
# a category and make the ledger unqueryable by kind.
RECEIPT_KINDS = frozenset(
    {"OPERAD_EVALUATION", "GATE_CHECK", "CANDIDATE_DISPATCH"}
)

# Taken from the stricter of the estate's two stores, each stated explicitly
# rather than inherited from a build default.
LEDGER_PRAGMAS = (
    ("journal_mode", "WAL"),
    ("synchronous", "FULL"),
    ("busy_timeout", "30000"),
    ("foreign_keys", "ON"),
)

# The digest an empty chain starts from. Named rather than inlined because the
# verifier and the writer must agree on it, and a literal repeated in two places
# is a literal that can drift in one.
CHAIN_GENESIS = DIGEST_PREFIX + "0" * 64

_SCHEMA = """
CREATE TABLE IF NOT EXISTS receipts (
    seq            INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id     TEXT NOT NULL UNIQUE,
    kind           TEXT NOT NULL,
    subject        TEXT NOT NULL,
    payload_json   TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    prev_digest    TEXT NOT NULL,
    chain_digest   TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS receipts_by_kind ON receipts (kind);

-- Append-only enforced by the store, not by this class declining to call
-- UPDATE. A rule only the writer honours is not a rule.
CREATE TRIGGER IF NOT EXISTS receipts_are_append_only_no_update
BEFORE UPDATE ON receipts
BEGIN
    SELECT RAISE(ABORT, 'receipts are append-only: UPDATE refused');
END;

CREATE TRIGGER IF NOT EXISTS receipts_are_append_only_no_delete
BEFORE DELETE ON receipts
BEGIN
    SELECT RAISE(ABORT, 'receipts are append-only: DELETE refused');
END;
"""


class LedgerError(RuntimeError):
    """A typed refusal naming what the ledger would not do."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(payload),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(*parts: bytes) -> str:
    """BLAKE3 over length-prefixed parts, tagged with the algorithm.

    Each part carries its own length so that concatenation is unambiguous:
    without it, `("ab", "c")` and `("a", "bc")` would produce the same digest,
    and two different receipts could share an identity.
    """
    hasher = blake3.blake3()
    for part in parts:
        hasher.update(len(part).to_bytes(8, "little"))
        hasher.update(part)
    return DIGEST_PREFIX + hasher.hexdigest()


@dataclass(frozen=True, slots=True)
class ReceiptV1:
    """One recorded event. Its identity is the digest of its own content."""

    kind: str
    subject: str
    payload: Mapping[str, Any]
    schema_version: str = RECEIPT_SCHEMA_V1
    receipt_id: str = ""

    def __post_init__(self) -> None:
        if self.kind not in RECEIPT_KINDS:
            raise LedgerError(
                "UNKNOWN_KIND",
                f"{self.kind!r} is not one of {sorted(RECEIPT_KINDS)}",
            )
        if type(self.subject) is not str or not self.subject:
            raise LedgerError("BAD_SUBJECT", "subject must be a nonempty string")
        if not isinstance(self.payload, Mapping):
            raise LedgerError("BAD_PAYLOAD", "payload must be a mapping")
        try:
            body = _canonical_bytes(self.payload)
        except (TypeError, ValueError) as exc:
            raise LedgerError(
                "UNSERIALISABLE_PAYLOAD",
                f"payload is not canonically serialisable: {exc}",
            ) from exc
        if self.schema_version != RECEIPT_SCHEMA_V1:
            raise LedgerError("SCHEMA", "unsupported receipt schema")
        expected = digest(
            self.schema_version.encode("utf-8"),
            self.kind.encode("utf-8"),
            self.subject.encode("utf-8"),
            body,
        )
        if self.receipt_id and self.receipt_id != expected:
            raise LedgerError(
                "RECEIPT_ID", "receipt_id does not match canonical content"
            )
        object.__setattr__(self, "receipt_id", expected)

    def canonical_payload(self) -> str:
        return _canonical_bytes(self.payload).decode("utf-8")


def chain_step(prev_digest: str, receipt_id: str) -> str:
    """Fold one receipt into the running chain digest.

    Kept as a free function because both the writer and the verifier must
    compute it identically; a method on the ledger would let the verifier drift
    into recomputing it a second way.
    """
    return digest(prev_digest.encode("utf-8"), receipt_id.encode("utf-8"))


class ContentAddressedReceiptLedger:
    """Append-only, hash-chained, idempotent under replay, and verifiable."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    @property
    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            # timeout is passed explicitly rather than left to the 5-second
            # default the governance store silently inherits.
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            for pragma, value in LEDGER_PRAGMAS:
                conn.execute(f"PRAGMA {pragma} = {value};")
            conn.executescript(_SCHEMA)
            self._conn = conn
        return self._conn

    def effective_pragmas(self) -> dict[str, str]:
        """What the store is actually running, read back rather than assumed.

        Setting a pragma and believing it took is how a store ends up named for
        a mode it is not in. `journal_mode` in particular refuses to change
        while a transaction is open, and returns the *current* mode rather than
        raising.
        """
        conn = self.connection
        result: dict[str, str] = {}
        for pragma, _ in LEDGER_PRAGMAS:
            row = conn.execute(f"PRAGMA {pragma}").fetchone()
            result[pragma] = str(row[0]) if row is not None else ""
        return result

    # ------------------------------------------------------------------
    # Integrity of the store itself
    # ------------------------------------------------------------------

    @staticmethod
    def problems_from_rows(rows) -> tuple[str, ...]:
        """Filter `PRAGMA integrity_check` output down to the problems.

        Extracted so it can be tested directly. SQLite has two ways of reporting
        a damaged database and they need different handling: it returns one row
        per problem for damage it can describe -- a row missing from an index,
        say -- and it *raises* `DatabaseError` for damage severe enough that it
        cannot finish the walk. Page-level corruption raises on this build, so a
        test that only corrupts a file never exercises this filter, and a
        mutation neutering it survived until a test called it directly.
        """
        return tuple(str(row[0]) for row in rows if str(row[0]) != "ok")

    def verify_integrity(self) -> tuple[str, ...]:
        """Run `PRAGMA integrity_check` and return the problems it names.

        SQLite reports a single row reading `ok` when the database is sound. An
        empty tuple therefore means verified, not unchecked -- the two are
        different states, and the caller can tell them apart because a failure
        to run raises rather than returning nothing.
        """
        try:
            rows = self.connection.execute("PRAGMA integrity_check").fetchall()
        except sqlite3.DatabaseError as exc:
            raise LedgerError(
                "INTEGRITY_CHECK_FAILED",
                f"the integrity check could not run: {exc}",
            ) from exc
        return self.problems_from_rows(rows)

    # ------------------------------------------------------------------
    # Integrity of the history
    # ------------------------------------------------------------------

    def head_digest(self) -> str:
        """The chain digest of the most recent receipt, or the genesis value."""
        row = self.connection.execute(
            "SELECT chain_digest FROM receipts ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        return CHAIN_GENESIS if row is None else str(row["chain_digest"])

    def verify_chain(self) -> tuple[str, ...]:
        """Recompute the whole chain and name every position that disagrees.

        This is the check that content addressing cannot perform. Each receipt's
        own digest still verifies after a row is deleted; the chain does not,
        because the surviving successor folded in a predecessor that is no
        longer there.
        """
        problems: list[str] = []
        previous = CHAIN_GENESIS
        rows = self.connection.execute(
            "SELECT seq, receipt_id, kind, subject, payload_json, "
            "schema_version, prev_digest, chain_digest FROM receipts "
            "ORDER BY seq ASC"
        ).fetchall()
        for row in rows:
            seq = int(row["seq"])
            if str(row["prev_digest"]) != previous:
                problems.append(
                    f"seq {seq}: prev_digest does not match the preceding entry"
                )
            recomputed_id = digest(
                str(row["schema_version"]).encode("utf-8"),
                str(row["kind"]).encode("utf-8"),
                str(row["subject"]).encode("utf-8"),
                str(row["payload_json"]).encode("utf-8"),
            )
            if recomputed_id != str(row["receipt_id"]):
                problems.append(
                    f"seq {seq}: stored content does not match its receipt_id"
                )
            expected_chain = chain_step(
                str(row["prev_digest"]), str(row["receipt_id"])
            )
            if expected_chain != str(row["chain_digest"]):
                problems.append(
                    f"seq {seq}: chain_digest is not the fold of its inputs"
                )
            previous = str(row["chain_digest"])
        return tuple(problems)

    def assert_healthy(self) -> None:
        """Refuse rather than return a verdict, for callers that cannot branch.

        Both checks run: a sound file holding a tampered history is not healthy,
        and neither is an intact history in a corrupt file.
        """
        problems = self.verify_integrity()
        if problems:
            raise LedgerError(
                "CORRUPT_STORE",
                "integrity check reported: " + "; ".join(problems[:5]),
            )
        broken = self.verify_chain()
        if broken:
            raise LedgerError(
                "CHAIN_BROKEN",
                "the receipt chain does not verify: " + "; ".join(broken[:5]),
            )

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def record(self, receipt: ReceiptV1) -> bool:
        """Append a receipt. Returns False if it was already recorded.

        Idempotent by identity rather than by a flag: the same event recorded
        twice is one row because the content address is unique. That is what
        makes replay -- the recovery path this epic asks for -- safe to run more
        than once, and it is why a replayed receipt does *not* extend the chain:
        the chain records distinct events in the order they were first seen, so
        replaying the whole log leaves the head where it was.
        """
        if type(receipt) is not ReceiptV1:
            raise LedgerError("BAD_RECEIPT", "expected an exact ReceiptV1")
        conn = self.connection
        with conn:  # one transaction, so the chain cannot fork under contention
            existing = conn.execute(
                "SELECT 1 FROM receipts WHERE receipt_id = ?",
                (receipt.receipt_id,),
            ).fetchone()
            if existing is not None:
                return False
            previous = self.head_digest()
            conn.execute(
                "INSERT INTO receipts "
                "(receipt_id, kind, subject, payload_json, schema_version, "
                " prev_digest, chain_digest) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    receipt.receipt_id,
                    receipt.kind,
                    receipt.subject,
                    receipt.canonical_payload(),
                    receipt.schema_version,
                    previous,
                    chain_step(previous, receipt.receipt_id),
                ),
            )
        return True

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def get(self, receipt_id: str) -> ReceiptV1 | None:
        row = self.connection.execute(
            "SELECT kind, subject, payload_json, schema_version FROM receipts "
            "WHERE receipt_id = ?",
            (receipt_id,),
        ).fetchone()
        if row is None:
            return None
        return ReceiptV1(
            kind=row["kind"],
            subject=row["subject"],
            payload=json.loads(row["payload_json"]),
            schema_version=row["schema_version"],
        )

    def count(self, kind: str | None = None) -> int:
        if kind is None:
            row = self.connection.execute(
                "SELECT COUNT(*) AS n FROM receipts"
            ).fetchone()
        else:
            if kind not in RECEIPT_KINDS:
                raise LedgerError("UNKNOWN_KIND", f"{kind!r} is not a receipt kind")
            row = self.connection.execute(
                "SELECT COUNT(*) AS n FROM receipts WHERE kind = ?", (kind,)
            ).fetchone()
        return int(row["n"])

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


__all__ = [
    "CHAIN_GENESIS",
    "ContentAddressedReceiptLedger",
    "DIGEST_PREFIX",
    "LEDGER_PRAGMAS",
    "LedgerError",
    "RECEIPT_KINDS",
    "RECEIPT_SCHEMA_V1",
    "ReceiptV1",
    "chain_step",
    "digest",
]
