"""Replay the PFP VI Section 6 example against the repository failure store.

These checks need the full repository checkout, because the example calls the
repository's ``CemeterySink``. When the package is used on its own, every test
here is skipped with that reason. Temporary ledgers are written only under
pytest's ``tmp_path``.
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from types import ModuleType

import pytest

PACKAGE = Path(__file__).resolve().parents[2]
PAPER = PACKAGE / "paper.md"
SINK_SOURCE = Path("pfp", "infrastructure", "persistence", "cemetery_sink.py")


def _repository_root() -> Path | None:
    return next((p for p in PACKAGE.parents if (p / SINK_SOURCE).is_file()), None)


REPOSITORY = _repository_root()
pytestmark = pytest.mark.skipif(
    REPOSITORY is None,
    reason=(
        "needs the full repository checkout: "
        + SINK_SOURCE.as_posix()
        + " was not found four levels above this package"
    ),
)


def _section6_block() -> str:
    text = PAPER.read_text(encoding="utf-8")
    section = text.split("\n## 6.", 1)[1].split("\n## 7.", 1)[0]
    blocks = re.findall(r"```python\n(.*?)```", section, flags=re.S)
    assert len(blocks) == 1, "Section 6 should contain exactly one Python block"
    return blocks[0]


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, object]:
    """Run the printed Section 6 block in a fresh directory; return its names."""
    assert REPOSITORY is not None
    monkeypatch.syspath_prepend(str(REPOSITORY))
    monkeypatch.chdir(tmp_path)
    namespace: dict[str, object] = {"__name__": "pfp_vi_section_6"}
    exec(compile(_section6_block(), "paper.md#section-6", "exec"), namespace)
    namespace["sink_module"] = importlib.import_module(
        "pfp.infrastructure.persistence.cemetery_sink"
    )
    namespace["errors"] = importlib.import_module("pfp.domain.exceptions")
    return namespace


def _compact(record: dict) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_section6_block_runs_as_printed(store: dict[str, object]) -> None:
    anchor = store["anchor"]
    observed = store["observed"]
    assert (anchor.entry_count, observed.entry_count) == (2, 2)
    assert observed.head_digest == anchor.head_digest


def test_changed_payload_is_rejected_on_reopen(store: dict[str, object]) -> None:
    path = Path(store["path"])
    header, first, second = path.read_text(encoding="utf-8").splitlines()
    record = json.loads(first)
    assert record["refusal_reason"] == "PROTECTED_PATH"
    record["refusal_reason"] = "PROTECTED_PATH_CHANGED"
    path.write_text("\n".join([header, _compact(record), second]) + "\n", encoding="utf-8")
    sink_module: ModuleType = store["sink_module"]
    errors: ModuleType = store["errors"]
    with pytest.raises(errors.LedgerIntegrityError):
        sink_module.CemeterySink(path)


def test_removed_final_entry_is_rejected_with_original_header(store: dict[str, object]) -> None:
    path = Path(store["path"])
    header, first, _second = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([header, first]) + "\n", encoding="utf-8")
    sink_module: ModuleType = store["sink_module"]
    errors: ModuleType = store["errors"]
    with pytest.raises(errors.LedgerTruncationError):
        sink_module.CemeterySink(path)


def test_consistent_shorter_file_passes_locally_but_not_the_anchor(
    store: dict[str, object],
) -> None:
    path = Path(store["path"])
    header, first, _second = path.read_text(encoding="utf-8").splitlines()
    rewritten = json.loads(header)
    rewritten["entry_count"] = 1
    rewritten["head_digest"] = json.loads(first)["entry_digest"]
    path.write_text("\n".join([_compact(rewritten), first]) + "\n", encoding="utf-8")
    sink_module: ModuleType = store["sink_module"]
    shorter = sink_module.CemeterySink(path).emit_tail_receipt()
    anchor = store["anchor"]
    assert shorter.entry_count == 1
    assert (shorter.entry_count, shorter.head_digest) != (anchor.entry_count, anchor.head_digest)


def test_numeric_and_string_reason_share_count_and_head(store: dict[str, object]) -> None:
    sink_module: ModuleType = store["sink_module"]
    path = Path("fresh-failure-ledger") / "normalization.jsonl"
    sink = sink_module.CemeterySink(path)
    sink.record_refusal({"task_id": "toy-2"}, "42")
    as_string = sink.emit_tail_receipt()
    header, entry = path.read_text(encoding="utf-8").splitlines()
    record = json.loads(entry)
    record["refusal_reason"] = 42
    path.write_text("\n".join([header, _compact(record)]) + "\n", encoding="utf-8")
    as_number = sink_module.CemeterySink(path).emit_tail_receipt()
    assert (as_number.entry_count, as_number.head_digest) == (
        as_string.entry_count,
        as_string.head_digest,
    )


def test_header_schema_and_genesis_are_outside_the_tail_anchor(store: dict[str, object]) -> None:
    path = Path(store["path"])
    original = path.read_bytes()
    header, first, second = original.decode("utf-8").splitlines()
    modified = json.loads(header)
    modified["schema"] = "unrecognized-schema"
    modified["genesis_timestamp"] = "different-written-clock-value"
    path.write_text("\n".join([_compact(modified), first, second]) + "\n", encoding="utf-8")
    observed = store["sink_module"].CemeterySink(path).emit_tail_receipt()
    assert observed == store["anchor"]
    assert path.read_bytes() != original


def test_json_whitespace_changes_raw_bytes_but_not_the_tail_anchor(store: dict[str, object]) -> None:
    path = Path(store["path"])
    original = path.read_bytes()
    records = [json.loads(line) for line in original.decode("utf-8").splitlines()]
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n\n", encoding="utf-8")
    observed = store["sink_module"].CemeterySink(path).emit_tail_receipt()
    assert observed == store["anchor"]
    assert path.read_bytes() != original


def test_cached_receipt_does_not_verify_changed_disk_bytes(store: dict[str, object]) -> None:
    path = Path(store["path"])
    header, first, second = path.read_text(encoding="utf-8").splitlines()
    changed = json.loads(first)
    changed["refusal_reason"] = "CHANGED_AFTER_OPEN"
    path.write_text("\n".join([header, _compact(changed), second]) + "\n", encoding="utf-8")
    assert store["sink"].emit_tail_receipt() == store["anchor"]
    with pytest.raises(store["errors"].LedgerIntegrityError):
        store["sink"].verify_integrity()


def test_failed_replace_leaves_memory_ahead_of_the_persisted_file(
    store: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = Path(store["path"])
    original = path.read_bytes()
    sink = store["sink"]

    def fail_replace(source: object, destination: object) -> None:
        raise OSError("injected replacement failure")

    with monkeypatch.context() as patch:
        patch.setattr(store["sink_module"].os, "replace", fail_replace)
        with pytest.raises(OSError, match="injected replacement failure"):
            sink.record_refusal({"task_id": "toy-write-failure"}, "NO_APPEND_ACKNOWLEDGEMENT")
    assert path.read_bytes() == original
    assert sink.emit_tail_receipt().entry_count == 3
    assert store["sink_module"].CemeterySink(path).emit_tail_receipt() == store["anchor"]
    assert sink.verify_integrity()
    assert sink.emit_tail_receipt() == store["anchor"]


def test_mutable_nested_mapping_can_invalidate_a_later_snapshot(store: dict[str, object]) -> None:
    sink = store["sink"]
    first = sink.get_entries()[0]
    first.turn_envelope["candidate"] = "changed nested mapping"
    sink.record_refusal({"task_id": "toy-nested-mutation"}, "LATER_EVENT")
    with pytest.raises(store["errors"].LedgerIntegrityError):
        store["sink_module"].CemeterySink(Path(store["path"]))


def test_valid_extension_has_a_new_head_and_the_retained_prefix(store: dict[str, object]) -> None:
    sink = store["sink"]
    anchor = store["anchor"]
    sink.record_refusal({"task_id": "toy-extension"}, "ADDITIONAL_CONSTRUCTED_REFUSAL")
    reopened = store["sink_module"].CemeterySink(Path(store["path"]))
    observed = reopened.emit_tail_receipt()
    assert observed.entry_count == anchor.entry_count + 1
    assert observed.head_digest != anchor.head_digest
    assert reopened.get_entries()[anchor.entry_count - 1].entry_digest == anchor.head_digest
