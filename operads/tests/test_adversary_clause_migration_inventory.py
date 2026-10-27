"""First Adversary clause extraction is source-bound and remains non-executable."""

import hashlib
import json
from pathlib import Path

import pytest

from operads.application.adversary_candidate_plan import (
    PlanNodeV01,
    PlanRefusal,
    compile_candidate_plan,
)
from operads.infrastructure.fs.adversary_operand_source import (
    read_adversary_operand_sources,
)

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "operads/catalog/operands/v1"


def test_legacy_adversary_clause_inventory_is_exact_and_partial() -> None:
    inventory = json.loads((CATALOG / "adversary/migration_inventory.json").read_text(encoding="utf-8"))
    assert inventory["schema"] == "oewas.adversary.legacy-clause-inventory.v0.1"
    assert inventory["coverage"] == "partial"
    assert inventory["authority_effect"] == "None"
    source = ROOT / inventory["source_path"]
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == inventory["source_sha256"]
    lines = raw.decode("utf-8").splitlines()
    seen: set[str] = set()
    for entry in inventory["entries"]:
        selected = entry["candidate_path"]
        assert selected not in seen
        seen.add(selected)
        assert entry["status"] == "UnboundCandidate"
        assert entry["text_relation"] == "ExactUtf8"
        assert entry["equivalence"] == "Unverified"
        start, end = entry["source_line_start"], entry["source_line_end"]
        assert 1 <= start <= end <= len(lines)
        span = "\n".join(lines[start - 1 : end])
        assert entry["source_anchor"] in span
        assert hashlib.sha256(span.encode("utf-8")).hexdigest() == entry["source_span_sha256"]
        byte_start = entry["source_byte_start"]
        byte_end = entry["source_byte_end_exclusive"]
        assert 0 <= byte_start < byte_end <= len(raw)
        exact_slice = raw[byte_start:byte_end]
        assert exact_slice == span.encode("utf-8")
        assert hashlib.sha256(exact_slice).hexdigest() == entry["source_span_sha256"]
        (document,) = read_adversary_operand_sources(ROOT, (selected,))
        assert document.operands[0].instruction_body.encode("utf-8") == exact_slice
        assert (CATALOG / selected).is_file()


@pytest.mark.parametrize(
    "selected",
    (
        "adversary/checker_receipt_required.md",
        "adversary/critic_json_only.md",
        "adversary/fixture_never_authorizes.md",
    ),
)
def test_extracted_clause_is_parseable_but_not_an_admitted_plan(selected: str) -> None:
    (document,) = read_adversary_operand_sources(ROOT, (selected,))
    operation_id = str(document.operations[0].operation_id)
    assert document.operations[0].lifecycle.admission.value == "Unadmitted"
    with pytest.raises(PlanRefusal) as caught:
        compile_candidate_plan((document,), PlanNodeV01(operation_id))
    assert caught.value.code == "OPERATION_UNBOUND"
