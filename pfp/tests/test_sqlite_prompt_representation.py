"""Actual SQLite roundtrip, including adversarial text that must stay data."""

import sqlite3

import pytest
from pydantic import ValidationError

from pfp.domain.prompt_representations.relational_prompt_representation import (
    RelationalPromptRepresentation,
    RelationalSpanRow,
    SqlitePromptRepresentation,
)


def representation(text):
    return SqlitePromptRepresentation(source_id="meron", source_sha256="a" * 64,
        proposal_sha256="b" * 64, spans=[RelationalSpanRow(slot="s0", role="task", text=text)])


@pytest.mark.parametrize("text", ["solve the meron sign problem inside our finite system",
    "'); DROP TABLE prompt_spans; --", "meron's \"orbit\"\nα Λ 𓂀", "left\x00right"])
def test_rendered_sql_preserves_text_and_cannot_execute_embedded_commands(text):
    prompt = representation(text)
    with sqlite3.connect(":memory:") as db:
        db.executescript(prompt.render())
        assert db.execute("SELECT slot,role,text FROM prompt_spans").fetchall() == [("s0", "task", text)]
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    assert prompt.to_envelope()["profile"] == "sqlite_strict_utf8_v2"


def test_historical_wire_and_digest_are_unchanged():
    old = RelationalPromptRepresentation(source_id="meron", source_sha256="a" * 64,
        proposal_sha256="b" * 64, spans=[RelationalSpanRow(slot="s0", role="task", text="x")])
    assert old.render() == (
        "-- Prompt Relational Normal Form (profile: sqlite_strict_text_set_v1)\n"
        "-- Source ID: meron | Hash: aaaaaaaaaaaaaaaa\n-- Occurrences and role bindings:\n"
        'INSERT INTO prompt_spans (slot, role, text) VALUES (\'s0\', \'task\', "x"::text);')
    assert old.prompt_sha256() != representation("x").prompt_sha256()


def test_table_override_and_oversize_sql_are_refused():
    with pytest.raises(ValidationError):
        SqlitePromptRepresentation(**{**representation("x").model_dump(), "table_name": "other; DROP TABLE x"})
    with pytest.raises(ValueError, match="SQL_PROMPT_BYTE_LIMIT"):
        representation("x" * 33000).render()
