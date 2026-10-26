"""A content-addressed, cryptographically chained receipt ledger.

`EPIC-OE-OEWAS-005` states the **Immutable Ledger Law**: past receipts and audit
entries are append-only and cryptographically chained.

`SqliteUnitOfWork` already provides WAL mode, `synchronous=FULL`, a 30-second
busy timeout, an idempotency table, and a transactional outbox. Its `events_v3`
table is append-only *by convention* -- nothing chains the rows and nothing
prevents an `UPDATE`.

So this module supplies the half that was missing, and supplies it structurally:

* Each entry carries `prev_digest`, and its own `entry_digest` is
  `BLAKE3(sequence || prev_digest || payload)`. Editing any payload breaks every
  digest after it.
* `UPDATE` and `DELETE` are refused **by SQLite triggers**, not by this class.
  A rule enforced only in the Python wrapper is enforced only for callers who go
  through the wrapper.

## What a chain cannot tell you

A hash chain shows that the entries you hold have not been altered relative to
one another. It **cannot detect that entries were removed from the end.** Delete
the last three receipts and what remains is a consistent chain.

That is a real limit, not an implementation gap, and pretending otherwise would
be the kind of overclaim this estate keeps finding. [`verify`] therefore reports
internal consistency only, and [`tip`] exists so a caller can pin the head
digest somewhere this ledger does not control. [`complete_against`] is that
comparison: the chain is complete only when `verify` is `INTACT` and the
observed tip equals the pin taken before the check. Reading `tip()` again at
check time does not pin anything. There is no capability sandbox on this path.
**Internal consistency is not proof of completeness**, and the docstrings say
so at every level.

AuthorityEffect: None. Chaining a receipt is not certifying what it records.
"""

from __future__ import annotations

import enum
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Iterator

import blake3

#: The `prev_digest` of the first entry. Not a real digest -- a declared anchor,
#: so the first entry's chaining is checked by the same rule as every other.
GENESIS_DIGEST = "0" * 64

LEDGER_SCHEMA_VERSION = "omega.oewas.receipt_ledger.v1"


class LedgerError(RuntimeError):
    """A refusal: the ledger will not do what was asked."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"LEDGER_ERROR[{code}]: {message}")
        self.code = code
        self.message = message


class ChainStatus(enum.Enum):
    """The outcome of verifying a chain.

    `INTACT` says the entries present are mutually consistent. It does **not**
    say they are all the entries that were written -- see the module docstring.
    """

    INTACT = "INTACT"
    TAMPERED = "TAMPERED"
    EMPTY = "EMPTY"


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """One receipt, and its position in the chain."""

    sequence: int
    payload: str
    prev_digest: str
    entry_digest: str


@dataclass(frozen=True, slots=True)
class ChainVerdict:
    """What verification found.

    `checked` and `total` are a pair rather than a boolean, so a chain that
    failed at entry 3 of 900 stays distinguishable from one that failed at 899.
    """

    status: ChainStatus
    checked: int
    total: int
    detail: str

    @property
    def is_intact(self) -> bool:
        return self.status is ChainStatus.INTACT


@dataclass(frozen=True, slots=True)
class ChainCompletion:
    """Whether an externally pinned tip still matches this ledger.

    `verify` can be `INTACT` on a truncated prefix. Completeness is that
    verdict plus equality with a tip the caller stored outside the database.
    """

    verdict: ChainVerdict
    pinned_tip: str
    observed_tip: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ChainCompletion)
        return (
            self.verdict == other.verdict
            and self.pinned_tip == other.pinned_tip
            and self.observed_tip == other.observed_tip
        )

    def __hash__(self) -> int:
        return hash((type(self), self.verdict, self.pinned_tip, self.observed_tip))

    @property
    def is_complete(self) -> bool:
        return (
            self.verdict.status is ChainStatus.INTACT
            and self.observed_tip == self.pinned_tip
        )


def canonical_payload(value: Any) -> str:
    """A payload's canonical text.

    Sorted keys and no incidental whitespace, so two structurally equal receipts
    hash alike and the digest is a property of the content rather than of how it
    was serialised.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def entry_digest(sequence: int, prev_digest: str, payload: str) -> str:
    """`BLAKE3(sequence || prev_digest || payload)`.

    The sequence number is inside the digest so that reordering two entries --
    which leaves every payload and link byte-identical -- still breaks the chain.
    """
    hasher = blake3.blake3()
    hasher.update(LEDGER_SCHEMA_VERSION.encode("utf-8"))
    hasher.update(str(sequence).encode("utf-8"))
    hasher.update(b"\x00")
    hasher.update(prev_digest.encode("utf-8"))
    hasher.update(b"\x00")
    hasher.update(payload.encode("utf-8"))
    return hasher.hexdigest()


class ReceiptLedger:
    """An append-only, chained receipt ledger over SQLite.

    Opened on a path or `:memory:`. WAL and `synchronous=FULL` match the
    settings `SqliteUnitOfWork` uses, so a ledger sharing a database with it
    behaves the same way under a crash.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "ReceiptLedger":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def _init_db(self) -> None:
        if self._db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=FULL;")
        self._conn.execute("PRAGMA busy_timeout=30000;")
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS receipt_ledger_v1 (
                    sequence     INTEGER PRIMARY KEY,
                    payload      TEXT NOT NULL,
                    prev_digest  TEXT NOT NULL,
                    entry_digest TEXT NOT NULL UNIQUE
                );
                """
            )
            # Append-only, enforced by the database.
            #
            # A rule enforced only in this class is enforced only for callers who
            # come through this class. Anything holding the connection -- another
            # module, a migration, a repl -- would bypass it. SQLite refuses.
            self._conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS receipt_ledger_v1_no_update
                BEFORE UPDATE ON receipt_ledger_v1
                BEGIN
                    SELECT RAISE(ABORT, 'receipt ledger is append-only');
                END;
                """
            )
            self._conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS receipt_ledger_v1_no_delete
                BEFORE DELETE ON receipt_ledger_v1
                BEGIN
                    SELECT RAISE(ABORT, 'receipt ledger is append-only');
                END;
                """
            )

    # -- reading -----------------------------------------------------------

    def __len__(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM receipt_ledger_v1").fetchone()
        return int(row["n"])

    def entries(self) -> Iterator[LedgerEntry]:
        """Every entry, in sequence order."""
        for row in self._conn.execute(
            "SELECT sequence, payload, prev_digest, entry_digest "
            "FROM receipt_ledger_v1 ORDER BY sequence"
        ):
            yield LedgerEntry(
                sequence=int(row["sequence"]),
                payload=row["payload"],
                prev_digest=row["prev_digest"],
                entry_digest=row["entry_digest"],
            )

    def tip(self) -> str:
        """The head digest, or `GENESIS_DIGEST` when empty.

        Pin this somewhere the ledger does not control. It is the only way to
        detect that entries were removed from the end -- the chain itself cannot.
        """
        row = self._conn.execute(
            "SELECT entry_digest FROM receipt_ledger_v1 ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        return GENESIS_DIGEST if row is None else row["entry_digest"]

    # -- writing -----------------------------------------------------------

    def append(self, payload: Any) -> LedgerEntry:
        """Append one receipt and return the entry written."""
        text = canonical_payload(payload)
        sequence = len(self) + 1
        prev = self.tip()
        digest = entry_digest(sequence, prev, text)
        try:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO receipt_ledger_v1 "
                    "(sequence, payload, prev_digest, entry_digest) VALUES (?, ?, ?, ?)",
                    (sequence, text, prev, digest),
                )
        except sqlite3.IntegrityError as error:
            raise LedgerError("DUPLICATE_ENTRY", str(error)) from error
        return LedgerEntry(
            sequence=sequence, payload=text, prev_digest=prev, entry_digest=digest
        )

    # -- verifying ---------------------------------------------------------

    def verify(self) -> ChainVerdict:
        """Check every entry against its own digest and its predecessor's.

        Detects an altered payload, a broken link, a reordering, and a gap in the
        sequence. Does **not** detect entries removed from the end: see the
        module docstring and [`tip`].
        """
        total = len(self)
        if total == 0:
            return ChainVerdict(
                status=ChainStatus.EMPTY,
                checked=0,
                total=0,
                detail="the ledger holds no entries; an empty chain is not an intact one",
            )
        expected_prev = GENESIS_DIGEST
        expected_sequence = 1
        checked = 0
        for entry in self.entries():
            if entry.sequence != expected_sequence:
                return ChainVerdict(
                    status=ChainStatus.TAMPERED,
                    checked=checked,
                    total=total,
                    detail=(
                        f"sequence gap: expected {expected_sequence}, "
                        f"found {entry.sequence}"
                    ),
                )
            if entry.prev_digest != expected_prev:
                return ChainVerdict(
                    status=ChainStatus.TAMPERED,
                    checked=checked,
                    total=total,
                    detail=(
                        f"broken link at entry {entry.sequence}: prev_digest "
                        f"{entry.prev_digest[:16]}... does not match the previous "
                        f"entry's digest {expected_prev[:16]}..."
                    ),
                )
            recomputed = entry_digest(entry.sequence, entry.prev_digest, entry.payload)
            if recomputed != entry.entry_digest:
                return ChainVerdict(
                    status=ChainStatus.TAMPERED,
                    checked=checked,
                    total=total,
                    detail=(
                        f"payload altered at entry {entry.sequence}: recomputed "
                        f"{recomputed[:16]}... but the row records "
                        f"{entry.entry_digest[:16]}..."
                    ),
                )
            expected_prev = entry.entry_digest
            expected_sequence += 1
            checked += 1
        return ChainVerdict(
            status=ChainStatus.INTACT,
            checked=checked,
            total=total,
            detail=(
                f"all {checked} entries chain from genesis; internal consistency "
                f"only -- a removed tail cannot be detected without an external "
                f"anchor on tip()"
            ),
        )

    def complete_against(self, pinned_tip: str) -> ChainCompletion:
        """Judge completeness against a tip pinned outside this database.

        Does not change [`verify`]. A deleted tail still verifies as `INTACT`
        and is incomplete against the earlier pin. Passing `tip()` read at
        check time reports the prefix that remains, not the pin that was lost.
        """
        if type(pinned_tip) is not str or pinned_tip == "":
            raise LedgerError(
                "BAD_TIP",
                "an external tip pin must be a non-empty string",
            )
        return ChainCompletion(
            verdict=self.verify(),
            pinned_tip=pinned_tip,
            observed_tip=self.tip(),
        )

    def integrity_check(self) -> str:
        """SQLite's own `PRAGMA integrity_check`.

        Answers a different question from [`verify`]: whether the *database file*
        is structurally sound, not whether the *chain* is consistent. A corrupt
        page and an edited payload are different failures and are reported apart.
        """
        row = self._conn.execute("PRAGMA integrity_check;").fetchone()
        return str(row[0])
