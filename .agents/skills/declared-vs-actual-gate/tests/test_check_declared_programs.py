"""Falsifying tests for the declared-vs-actual gate.

AuthorityEffect: None.

The gate's own SKILL.md says a pipeline that mandates a gate it does not ship
fails open every time it runs. The same applies one level down: a gate nothing
has falsified is a gate that has only ever been shown to pass the one tree its
author pointed it at. Each test below builds a tree the gate must refuse.

    python -m pytest .agents/skills/declared-vs-actual-gate/tests -q
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

GATE = Path(__file__).resolve().parents[1] / "scripts" / "check_declared_programs.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_declared_programs", GATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = _load()


def _skill(root: Path, host: str, name: str, body: str = "") -> None:
    d = root / host / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    # write_bytes, not write_text: on Windows, text mode translates "\n" to
    # "\r\n", so a fixture written with write_text is already CRLF and the
    # line-ending test below would be converting an already-converted file
    # into "\r\r\n" -- which really is different content, so the gate was
    # right and the fixture was wrong.
    (d / "SKILL.md").write_bytes(
        f'---\nname: {name}\ndescription: "t"\n---\n\n# {name}\n{body}'.encode("utf-8")
    )


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    for host in (".agents", ".claude"):
        (tmp_path / host / "skills").mkdir(parents=True)
    _skill(tmp_path, ".agents", "alpha")
    _skill(tmp_path, ".claude", "alpha")
    return tmp_path


# ---------------------------------------------------------------------------
# host discovery
# ---------------------------------------------------------------------------


def test_host_roots_come_from_the_filesystem_not_from_prose(tree: Path):
    (tree / ".newhost" / "skills").mkdir(parents=True)
    assert gate.host_roots(tree) == [".agents", ".claude", ".newhost"]


def test_a_dot_directory_without_skills_is_not_a_host(tree: Path):
    (tree / ".github" / "workflows").mkdir(parents=True)
    assert ".github" not in gate.host_roots(tree)


# ---------------------------------------------------------------------------
# check 1 -- declared programs
# ---------------------------------------------------------------------------


def test_absent_declared_program_is_blocked_never_skipped(tree: Path, monkeypatch):
    monkeypatch.setattr(gate, "DECLARED_PROGRAMS", (("someskill", "does/not/exist.py"),))
    result = gate.check_declared_programs(tree)
    assert result["verdict"] == "BLOCKED"
    assert result["blocked"] == 1


def test_present_declared_program_records_its_hash(tree: Path, monkeypatch):
    target = tree / "present.py"
    target.write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(gate, "DECLARED_PROGRAMS", (("s", "present.py"),))
    result = gate.check_declared_programs(tree)
    assert result["verdict"] == "PASS"
    assert len(result["rows"][0]["sha256"]) == 64


# ---------------------------------------------------------------------------
# check 2 -- mirror set
# ---------------------------------------------------------------------------


def test_declaring_fewer_hosts_than_exist_is_refused(tree: Path):
    _skill(tree, ".agents", "beta", "\nMirror to `.claude` and `.codex` only.\n")
    (tree / ".codex" / "skills").mkdir(parents=True)
    result = gate.check_mirror_set(tree, gate.host_roots(tree))
    assert result["verdict"] == "BLOCKED"
    assert result["rows"][0]["skill"] == "beta"


def test_a_line_naming_one_root_in_passing_is_not_a_mirror_claim(tree: Path):
    """The false positive this check actually produced on the real tree.

    `auto-review-agents` says "`.agents/agents` has inventory. Mirror roots are
    packaging projections" -- prose about mirroring that names a single root.
    Reading that as a declared mirror set refuses a skill that declared nothing.
    """
    _skill(
        tree, ".agents", "beta", "\n`.agents/agents` has inventory. Mirror roots are projections.\n"
    )
    result = gate.check_mirror_set(tree, gate.host_roots(tree))
    assert result["verdict"] == "PASS", result["rows"]


def test_declaring_every_host_passes(tree: Path):
    _skill(tree, ".agents", "beta", "\nMirror to `.agents` and `.claude`.\n")
    assert gate.check_mirror_set(tree, gate.host_roots(tree))["verdict"] == "PASS"


def test_a_mirror_claim_wrapped_across_lines_is_read_whole(tree: Path):
    """A declaration is a sentence, and sentences wrap.

    Wrapping `product-manager`'s host line to satisfy the 80
    column lint moved two of the six roots onto a continuation line that does
    not contain the word "mirror". A line-scoped reader saw four hosts and
    refused a skill that had just named all six.
    """
    _skill(tree, ".agents", "beta", "\nMirror to `.agents` and\n`.claude` from canonical.\n")
    result = gate.check_mirror_set(tree, gate.host_roots(tree))
    assert result["verdict"] == "PASS", result["rows"]


def test_a_table_is_not_one_claim(tree: Path):
    """The over-correction that paragraph scanning introduced.

    `auto-suggest-new-skills` carries a protocol table whose rows mention
    mirroring and, many rows later, name some host roots. Treating the whole
    table as a single declaration refused a skill that declares no mirror set
    anywhere.
    """
    (tree / ".codex" / "skills").mkdir(parents=True)
    _skill(
        tree,
        ".agents",
        "beta",
        "\n| Step | Note |\n| --- | --- |\n| 1 | mirror the carrier |\n"
        "| 2 | history lives in `.agents` and `.claude` |\n",
    )
    result = gate.check_mirror_set(tree, gate.host_roots(tree))
    assert result["verdict"] == "PASS", result["rows"]


def test_a_wrapped_claim_that_really_is_short_is_still_refused(tree: Path):
    """Paragraph scanning must not become a way to pass by omission."""
    (tree / ".codex" / "skills").mkdir(parents=True)
    _skill(tree, ".agents", "beta", "\nMirror to `.agents` and\n`.claude` only.\n")
    result = gate.check_mirror_set(tree, gate.host_roots(tree))
    assert result["verdict"] == "BLOCKED"
    assert result["rows"][0]["missing"] == [".codex"]


# ---------------------------------------------------------------------------
# check 3 -- parity
# ---------------------------------------------------------------------------


def test_missing_mirror_member_is_drift(tree: Path):
    _skill(tree, ".agents", "gamma")
    result = gate.check_parity(tree, gate.host_roots(tree))
    assert result["verdict"] == "BLOCKED"
    assert "gamma/SKILL.md" in result["rows"][0]["missing"]


def test_crlf_alone_is_not_drift(tree: Path):
    """The working tree is CRLF on Windows and LF in git.

    A raw byte compare would report every file as drift on one platform and
    none on the other, which would make the check mean two different things.
    """
    path = tree / ".claude" / "skills" / "alpha" / "SKILL.md"
    data = path.read_bytes()
    assert b"\r\n" not in data, "fixture must start as LF or this proves nothing"
    path.write_bytes(data.replace(b"\n", b"\r\n"))
    assert gate.check_parity(tree, gate.host_roots(tree))["verdict"] == "PASS"


def test_build_debris_is_not_content(tree: Path):
    """Running the test suite must not make the gate refuse its own tree.

    __pycache__ appears in the canonical root only, so a naive walk reports
    every deployed host as missing files nobody would ever mirror.
    """
    cache = tree / ".agents" / "skills" / "alpha" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "alpha.cpython-314.pyc").write_bytes(b"\x00compiled")
    assert gate.check_parity(tree, gate.host_roots(tree))["verdict"] == "PASS"


def test_a_single_host_makes_parity_vacuous_not_passing(tmp_path: Path):
    (tmp_path / ".agents" / "skills").mkdir(parents=True)
    result = gate.check_parity(tmp_path, [".agents"])
    assert result["verdict"] == "VACUOUS"


# ---------------------------------------------------------------------------
# check 4 -- agent licences
# ---------------------------------------------------------------------------

LICENCE = (
    "$$\\operatorname{{License}}({name}) = \\{{\\, K \\in \\mathcal{{O}} "
    "\\mid \\operatorname{{colours}}(K) \\subseteq \\{{{colours}\\}} \\,\\}}$$"
)


def _agent(root: Path, host: str, name: str, colours: str) -> None:
    d = root / host / "agents"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.md").write_bytes(
        (f"---\nname: {name}\n---\n\n" + LICENCE.format(name=name, colours=colours) + "\n").encode(
            "utf-8"
        )
    )


def test_deployed_host_holding_an_ungranted_colour_is_refused(tree: Path):
    _agent(tree, ".agents", "worker", "Code")
    _agent(tree, ".claude", "worker", "Code, State")
    result = gate.check_agent_licences(tree, gate.host_roots(tree))
    assert result["verdict"] == "BLOCKED"
    assert result["rows"][0]["ungranted"] == ["State"]


def test_incomparable_sets_that_add_a_colour_are_also_refused(tree: Path):
    """Reading only the strict-superset bucket would wave these through.

    An incomparable pair still hands the deployed host a colour canonical never
    granted; it merely drops another one at the same time.
    """
    _agent(tree, ".agents", "worker", "Code, Paper")
    _agent(tree, ".claude", "worker", "Code, State")
    result = gate.check_agent_licences(tree, gate.host_roots(tree))
    assert result["verdict"] == "BLOCKED"
    assert result["rows"][0]["direction"] == "incomparable"
    assert result["rows"][0]["ungranted"] == ["State"]


def test_a_narrower_deployed_licence_is_advisory_not_refused(tree: Path):
    _agent(tree, ".agents", "worker", "Code, State")
    _agent(tree, ".claude", "worker", "Code")
    result = gate.check_agent_licences(tree, gate.host_roots(tree))
    assert result["verdict"] == "ADVISORY"


def test_same_set_written_in_a_different_order_is_not_drift(tree: Path):
    _agent(tree, ".agents", "worker", "Code, State")
    _agent(tree, ".claude", "worker", "State, Code")
    assert gate.check_agent_licences(tree, gate.host_roots(tree))["verdict"] == "PASS"


def test_an_agent_absent_from_a_deployed_host_is_refused(tree: Path):
    _agent(tree, ".agents", "worker", "Code")
    (tree / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
    result = gate.check_agent_licences(tree, gate.host_roots(tree))
    assert result["verdict"] == "BLOCKED"
    assert result["rows"][0]["direction"] == "ABSENT"


def test_no_deployed_agents_directory_is_vacuous_not_passing(tree: Path):
    _agent(tree, ".agents", "worker", "Code")
    result = gate.check_agent_licences(tree, gate.host_roots(tree))
    assert result["verdict"] == "VACUOUS"


# ---------------------------------------------------------------------------
# end to end
# ---------------------------------------------------------------------------


def test_json_receipt_is_valid_and_carries_the_authority_ceiling(tree: Path, capsys, monkeypatch):
    monkeypatch.chdir(tree)
    monkeypatch.setattr(gate, "repo_root", lambda: tree)
    monkeypatch.setattr(gate, "DECLARED_PROGRAMS", ())
    code = gate.main(["--json"])
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["authority_effect"] == "None"
    assert receipt["verdict"] in ("PASS", "BLOCKED")
    assert code in (0, 1)


def test_gate_exits_2_when_it_cannot_run(tmp_path: Path, monkeypatch, capsys):
    """Exit 2 is a refusal, never a pass. A gate that cannot run has not passed."""
    monkeypatch.setattr(gate, "repo_root", lambda: tmp_path)
    assert gate.main([]) == 2
