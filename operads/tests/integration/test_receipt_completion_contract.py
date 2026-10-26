"""A copied valid prefix is internally intact and incomplete against a retained tip."""

import sqlite3

from blake3 import blake3

from omega_engine_operads.infrastructure.storage.receipt_ledger import (
    ChainStatus,
    ReceiptLedger,
)


def independent_tip(rows):
    """Compute the published v1 bytes without production digest/canonical helpers."""
    previous = "0" * 64
    for sequence, payload, prev_digest, stored_digest in rows:
        assert prev_digest == previous
        encoded = (
            b"omega.oewas.receipt_ledger.v1"
            + str(sequence).encode("ascii")
            + b"\0"
            + previous.encode("ascii")
            + b"\0"
            + payload.encode("utf-8")
        )
        previous = blake3(encoded).hexdigest()
        assert stored_digest == previous
    return previous


def test_copied_prefix_requires_externally_retained_tip_and_rejects_foreign_tip(tmp_path):
    full_path = str(tmp_path / "full.sqlite3")
    prefix_path = str(tmp_path / "prefix.sqlite3")
    foreign_path = str(tmp_path / "foreign.sqlite3")
    retained_tip = tmp_path / "retained_tip.txt"  # Outside every ledger database.
    with ReceiptLedger(full_path) as full:
        full.append({"gate": "admit", "passed": True})
        full.append({"gate": "deliver", "passed": True})
        with sqlite3.connect(full_path) as connection:
            rows = connection.execute(
                "SELECT sequence, payload, prev_digest, entry_digest FROM receipt_ledger_v1 ORDER BY sequence"
            ).fetchall()
        assert len(rows) == 2
        assert rows[0][1] == '{"gate":"admit","passed":true}'
        assert rows[1][1] == '{"gate":"deliver","passed":true}'
        pin = independent_tip(rows)
        assert pin == full.tip()
        retained_tip.write_text(pin, encoding="ascii")

    with ReceiptLedger(prefix_path):
        with sqlite3.connect(prefix_path) as connection:
            connection.execute("INSERT INTO receipt_ledger_v1 VALUES (?, ?, ?, ?)", rows[0])
    with ReceiptLedger(foreign_path) as foreign:
        foreign.append({"gate": "unrelated", "passed": True})
        foreign_pin = foreign.tip()
    with ReceiptLedger(full_path) as reopened, ReceiptLedger(prefix_path) as prefix:
        old_pin = retained_tip.read_text(encoding="ascii")
        assert reopened.complete_against(old_pin).is_complete is True
        assert prefix.verify().status is ChainStatus.INTACT
        assert prefix.tip() == independent_tip(rows[:1])
        against_old_pin = prefix.complete_against(old_pin)
        assert against_old_pin.is_complete is False
        assert against_old_pin.observed_tip != old_pin
        assert prefix.complete_against(foreign_pin).is_complete is False
        assert reopened.complete_against(foreign_pin).is_complete is False
        # A caller who replaces custody with the current prefix tip accepts it.
        assert prefix.complete_against(prefix.tip()).is_complete is True
