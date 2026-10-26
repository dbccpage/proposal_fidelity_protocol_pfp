from __future__ import annotations

import pytest

from omega_engine_pfp.documentation_integrity import configuration
from omega_engine_pfp.documentation_integrity.domain import IntegrityError
from omega_engine_pfp.domain.documentation_integrity.policies import is_document_relative_path


@pytest.mark.parametrize(
    "candidate",
    ("../escape.md", "/absolute.md", "C:\\absolute.md", "a/../../escape.md", "a//b.md"),
)
def test_destination_policy_rejects_traversal_and_absolute_paths(candidate: str) -> None:
    assert not is_document_relative_path(candidate)


def test_control_json_has_a_bounded_read_budget(tmp_path, monkeypatch) -> None:
    payload = tmp_path / "oversized.json"
    payload.write_text('{"value":"too large"}', encoding="utf-8")
    monkeypatch.setattr(configuration, "MAX_CONTROL_BYTES", 4)
    with pytest.raises(IntegrityError, match="exceeds"):
        configuration.load_json(payload)
