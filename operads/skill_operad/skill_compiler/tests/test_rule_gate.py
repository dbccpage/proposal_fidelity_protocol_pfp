"""Rule gate: every check has a negative control on a synthetic four-host fixture.

AuthorityEffect: None.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from operads.skill_operad.skill_compiler import rule_gate, rule_scope

HOSTS = (".agents", ".claude", ".codex", ".grok")
DOCS = ("GEMINI.md", ".agents/AGENTS.md", ".claude/AGENTS.md", ".codex/AGENTS.md", ".grok/AGENTS.md")
RULE_A = (
    "# Rule: Alpha (`RULE_ALPHA_001`)\n\n"
    "**AuthorityEffect:** None.\n\n"
    "See [beta](../beta/rl_beta.md).\n"
)
RULE_B = "# Rule: Beta\n\n**AuthorityEffect:** None.\n\nMentions `RULE_ALPHA_001` in passing.\n"
GATE_SOURCE = "def enforce_alpha() -> bool:\n    return True\n"


def _registry() -> dict:
    return {
        "schema_version": "core.oewas.rules_registry.v1",
        "authority_effect": "None",
        "rules_root": "rules",
        "host_roots": list(HOSTS),
        "size_ceiling_bytes": 12000,
        "register_documents": list(DOCS),
        "taxonomy": ["alpha", "beta"],
        "rules": [
            {
                "path": "alpha/rl_alpha.md",
                "topic": "Alpha",
                "skills": ["governance-host-parity"],
                "summary": "Alpha summary.",
                "invariants": [
                    {
                        "id": "RULE_ALPHA_001",
                        "status": "ENFORCED",
                        "enforced_by": "tools/alpha_gate.py::enforce_alpha",
                    }
                ],
            },
            {
                "path": "beta/rl_beta.md",
                "topic": "Beta",
                "skills": [],
                "summary": "Beta summary.",
                "invariants": [],
            },
        ],
        "external_sources": [],
    }


def _write_rule(root: Path, relative: str, text: str, hosts: tuple[str, ...] = HOSTS) -> None:
    for host in hosts:
        path = root / host / "rules" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def _save_registry(root: Path, registry: dict) -> Path:
    path = root / "rules_registry.yaml"
    path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    return path


def _write_docs(root: Path, registry: dict) -> None:
    text = (
        "# Doc\n\n"
        f"{rule_gate.REGISTER_HEADING}\n\nIntro.\n\n"
        + rule_gate.render_register_table(registry)
        + "\n## Next\n"
    )
    for document in DOCS:
        path = root / document
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


@pytest.fixture()
def tree(tmp_path: Path) -> tuple[Path, Path]:
    registry = _registry()
    _write_rule(tmp_path, "alpha/rl_alpha.md", RULE_A)
    _write_rule(tmp_path, "beta/rl_beta.md", RULE_B)
    gate = tmp_path / "tools" / "alpha_gate.py"
    gate.parent.mkdir()
    gate.write_text(GATE_SOURCE, encoding="utf-8")
    _write_docs(tmp_path, registry)
    return tmp_path, _save_registry(tmp_path, registry)


def _codes(root: Path, registry_path: Path) -> set[str]:
    return {finding.code for finding in rule_gate.run_gate(root, registry_path).findings}


def test_clean_fixture_passes_and_counts_statuses(tree: tuple[Path, Path]) -> None:
    report = rule_gate.run_gate(*tree)
    assert report.findings == ()
    assert report.passed is True
    assert report.rule_count == 2
    assert dict(report.status_counts) == {"ENFORCED": 1}


def test_unregistered_and_missing_rule_files(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    _write_rule(root, "beta/rl_gamma.md", "# Gamma\n\n**AuthorityEffect:** None.\n")
    (root / ".agents" / "rules" / "beta" / "rl_beta.md").unlink()
    codes = _codes(root, registry_path)
    assert {"R1_UNREGISTERED", "R1_MISSING_FILE"} <= codes


def test_oversize_rule_is_refused(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    _write_rule(root, "beta/rl_beta.md", RULE_B + "x" * 12001)
    assert "R2_OVERSIZE" in _codes(root, registry_path)


def test_header_bom_and_filename_hygiene(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    _write_rule(root, "beta/rl_beta.md", "# Beta without header\n")
    for host in HOSTS:
        path = root / host / "rules" / "alpha" / "rl_alpha.md"
        path.write_bytes(b"\xef\xbb\xbf" + RULE_A.encode("utf-8"))
    _write_rule(root, "beta/RL_Upper.md", "# U\n\n**AuthorityEffect:** None.\n")
    codes = _codes(root, registry_path)
    assert {"R3_HEADER", "R3_BOM", "R3_FILENAME"} <= codes


def test_host_absolute_and_broken_links_are_refused(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    _write_rule(
        root,
        "beta/rl_beta.md",
        RULE_B + "[abs](file:///c:/x.md) [gone](missing.md)\n```\n[fenced](nowhere.md)\n```\n",
    )
    findings = rule_gate.run_gate(root, registry_path).findings
    codes = [finding.code for finding in findings]
    assert "R4_HOST_ABSOLUTE_LINK" in codes
    broken = [finding.message for finding in findings if finding.code == "R4_BROKEN_LINK"]
    assert broken == ["link target 'missing.md'"]


def test_folder_outside_taxonomy_is_refused(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    (root / ".agents" / "rules" / "loose").mkdir()
    assert "R5_TAXONOMY" in _codes(root, registry_path)


def test_dangling_enforced_by_symbol_and_file(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    registry = _registry()
    registry["rules"][0]["invariants"][0]["enforced_by"] = "tools/alpha_gate.py::no_such_check"
    assert "R6_ENFORCED_BY" in _codes(root, _save_registry(root, registry))
    registry["rules"][0]["invariants"][0]["enforced_by"] = "tools/absent.py"
    assert "R6_ENFORCED_BY" in _codes(root, _save_registry(root, registry))


def test_status_vocabulary_and_partial_scope(tree: tuple[Path, Path]) -> None:
    root, _ = tree
    registry = _registry()
    registry["rules"][0]["invariants"][0]["status"] = "PARTIAL"
    assert "R6_SCOPE" in _codes(root, _save_registry(root, registry))
    registry["rules"][0]["invariants"][0]["status"] = "CANDIDATE"
    assert "R6_STATUS" in _codes(root, _save_registry(root, registry))
    registry["rules"][0]["invariants"][0]["status"] = "MOSTLY"
    assert "R6_STATUS" in _codes(root, _save_registry(root, registry))


def test_invariant_ownership_is_total_and_unique(tree: tuple[Path, Path]) -> None:
    root, _ = tree
    _write_rule(root, "beta/rl_beta.md", RULE_B + "And `RULE_ORPHAN_001`.\n")
    registry = _registry()
    registry["rules"][1]["invariants"] = [{"id": "RULE_ALPHA_001", "status": "CANDIDATE"}]
    codes = _codes(root, _save_registry(root, registry))
    assert {"R6_UNOWNED", "R6_DUPLICATE_OWNER"} <= codes
    registry = _registry()
    registry["rules"][1]["invariants"] = [{"id": "RULE_ABSENT_001", "status": "CANDIDATE"}]
    assert "R6_NOT_IN_OWNER" in _codes(root, _save_registry(root, registry))


def test_host_drift_and_missing_mirror(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    (root / ".grok" / "rules" / "beta" / "rl_beta.md").write_text(RULE_B + "drift\n", encoding="utf-8")
    (root / ".codex" / "rules" / "alpha" / "rl_alpha.md").unlink()
    codes = _codes(root, registry_path)
    assert {"R7_HOST_DRIFT", "R7_HOST_MISSING"} <= codes


def test_register_documents_must_match_and_write_register_repairs(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    registry = _registry()
    registry["rules"][1]["topic"] = "Beta renamed"
    registry_path = _save_registry(root, registry)
    assert "R8_REGISTER_TABLE" in _codes(root, registry_path)
    written = rule_gate.write_register(root, rule_gate.load_registry(registry_path))
    assert written == list(DOCS)
    assert _codes(root, registry_path) == set()
    (root / ".codex" / "AGENTS.md").write_text("# drift\n", encoding="utf-8")
    assert {"R8_REGISTER_DRIFT", "R8_REGISTER_TABLE"} <= _codes(root, registry_path)


def test_malformed_registry_is_refused(tree: tuple[Path, Path]) -> None:
    root, _ = tree
    registry = _registry()
    registry["authority_effect"] = "Granted"
    with pytest.raises(rule_gate.RegistryError):
        rule_gate.run_gate(root, _save_registry(root, registry))
    registry = _registry()
    registry["rules"].append(dict(registry["rules"][0]))
    with pytest.raises(rule_gate.RegistryError):
        rule_gate.run_gate(root, _save_registry(root, registry))


def test_main_exit_codes(tree: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    root, registry_path = tree
    assert rule_gate.main(["--repo-root", str(root), "--registry", str(registry_path)]) == 0
    shutil.rmtree(root / ".grok" / "rules" / "beta")
    assert rule_gate.main(["--repo-root", str(root), "--registry", str(registry_path)]) == 1
    bad = root / "bad.yaml"
    bad.write_text("- not a mapping\n", encoding="utf-8")
    assert rule_gate.main(["--repo-root", str(root), "--registry", str(bad)]) == 2
    assert "REFUSED" in capsys.readouterr().out


def test_repository_rule_trees_match_the_register() -> None:
    root = rule_gate.repo_root_from(Path(__file__).resolve())
    report = rule_gate.run_gate(root)
    assert [finding.render() for finding in report.findings] == []
    assert report.rule_count >= 31


def test_extra_register_row_is_refused(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    for document in DOCS:
        path = root / document
        text = path.read_text(encoding="utf-8")
        table = rule_gate.render_register_table(_registry())
        stale = text.replace(table, table + "| **Stale** | gone | | x |\n")
        assert stale != text
        path.write_text(stale, encoding="utf-8", newline="\n")
    assert "R8_REGISTER_TABLE" in _codes(root, registry_path)


def test_non_utf8_register_document_is_a_finding(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    for document in DOCS:
        path = root / document
        path.write_bytes(path.read_bytes() + b"\x93")
    assert "R8_REGISTER_ENCODING" in _codes(root, registry_path)


def test_malformed_nested_entries_are_refused_not_crashed(tree: tuple[Path, Path]) -> None:
    root, _ = tree
    registry = _registry()
    registry["rules"][0]["invariants"] = ["RULE_ALPHA_001"]
    registry_path = _save_registry(root, registry)
    with pytest.raises(rule_gate.RegistryError):
        rule_gate.run_gate(root, registry_path)
    assert rule_gate.main(["--repo-root", str(root), "--registry", str(registry_path)]) == 2
    registry = _registry()
    registry["external_sources"] = [{"invariants": []}]
    with pytest.raises(rule_gate.RegistryError):
        rule_gate.run_gate(root, _save_registry(root, registry))


def test_write_register_keeps_text_after_a_table_without_blank_line(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    table = rule_gate.render_register_table(_registry())
    for document in DOCS:
        (root / document).write_text(
            f"{rule_gate.REGISTER_HEADING}\n\n{table}Trailing prose.\n## Next\n",
            encoding="utf-8",
            newline="\n",
        )
    registry = _registry()
    registry["rules"][1]["topic"] = "Beta renamed"
    registry_path = _save_registry(root, registry)
    rule_gate.write_register(root, rule_gate.load_registry(registry_path))
    text = (root / "GEMINI.md").read_text(encoding="utf-8")
    assert "Trailing prose.\n## Next\n" in text
    assert "Beta renamed" in text
    assert _codes(root, registry_path) == set()


def test_wrong_case_link_is_refused(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    _write_rule(root, "beta/rl_beta.md", RULE_B + "[wrong case](../alpha/RL_Alpha.md)\n")
    assert "R4_BROKEN_LINK" in _codes(root, registry_path)


def test_external_sources_share_the_owner_map(tree: tuple[Path, Path]) -> None:
    root, _ = tree
    source = root / "registry" / "rule-extra.md"
    source.parent.mkdir()
    source.write_text("AGT-EXTRA-0001\n", encoding="utf-8")
    registry = _registry()
    registry["external_sources"] = [
        {
            "path": "registry/rule-extra.md",
            "invariants": [{"id": "AGT-EXTRA-0001", "status": "CANDIDATE"}],
        }
    ]
    _write_rule(root, "beta/rl_beta.md", RULE_B + "See `AGT-EXTRA-0001`.\n")
    assert _codes(root, _save_registry(root, registry)) == set()
    registry["external_sources"].append(
        {
            "path": "registry/rule-extra.md",
            "invariants": [{"id": "AGT-EXTRA-0001", "status": "CANDIDATE"}],
        }
    )
    assert "R6_DUPLICATE_OWNER" in _codes(root, _save_registry(root, registry))
    registry = _registry()
    registry["external_sources"] = [
        {
            "path": "registry/rule-extra.md",
            "invariants": [{"id": "not-an-id", "status": "CANDIDATE"}],
        }
    ]
    assert "R6_ID" in _codes(root, _save_registry(root, registry))


def test_links_inside_indented_or_quoted_fences_are_ignored(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    _write_rule(
        root,
        "beta/rl_beta.md",
        RULE_B
        + "- item\n\n  ```\n  [x](nowhere.md)\n  ```\n\n> ````md\n> [y](file:///c:/z.md)\n> ````\n",
    )
    assert _codes(root, registry_path) == set()


def _scope(registry_path: Path, load_paths: list[str], ceiling: int | None = None) -> dict:
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["rules"][1]["load_paths"] = load_paths
    if ceiling is not None:
        registry["always_loaded_ceiling_bytes"] = ceiling
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    return registry


def test_write_scope_adds_frontmatter_that_the_gate_accepts(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    registry = _scope(registry_path, ["tools/**"])
    written = rule_scope.write_frontmatter(root, registry)
    assert len(written) == len(HOSTS)
    text = (root / ".claude" / "rules" / "beta" / "rl_beta.md").read_text(encoding="utf-8")
    assert text.startswith('---\npaths:\n  - "tools/**"\n---\n\n# Rule: Beta')
    report = rule_gate.run_gate(root, registry_path)
    assert report.findings == ()
    assert report.always_loaded_bytes == len(RULE_A.encode("utf-8"))


def test_frontmatter_drift_is_refused(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    _write_rule(root, "beta/rl_beta.md", rule_scope.render_frontmatter(["tools/**"], RULE_B))
    assert "R9_SCOPE_DRIFT" in _codes(root, registry_path)


def test_dead_glob_is_refused(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    registry = _scope(registry_path, ["no_such_dir/**"])
    rule_scope.write_frontmatter(root, registry)
    assert "R9_DEAD_GLOB" in _codes(root, registry_path)


def test_always_loaded_budget_is_refused(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    _scope(registry_path, [], ceiling=10)
    assert "R9_ALWAYS_LOADED_BUDGET" in _codes(root, registry_path)


@pytest.mark.parametrize(
    "frontmatter",
    ["paths: {not: a-list}", "paths:\n  - 1\n  - tools/**", "- a bare list, not a mapping"],
)
def test_malformed_frontmatter_is_a_finding(tree: tuple[Path, Path], frontmatter: str) -> None:
    root, registry_path = tree
    _write_rule(root, "beta/rl_beta.md", f"---\n{frontmatter}\n---\n\n" + RULE_B)
    assert "R9_FRONTMATTER" in _codes(root, registry_path)


def test_size_ceiling_ignores_frontmatter(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    body = RULE_B + "x" * (12000 - len(RULE_B.encode("utf-8")))
    registry = _scope(registry_path, ["tools/**"])
    _write_rule(root, "beta/rl_beta.md", body)
    rule_scope.write_frontmatter(root, registry)
    assert "R2_OVERSIZE" not in _codes(root, registry_path)
    _write_rule(root, "beta/rl_beta.md", body + "x")
    rule_scope.write_frontmatter(root, registry)
    assert "R2_OVERSIZE" in _codes(root, registry_path)


def test_write_scope_keeps_other_frontmatter_keys(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    _write_rule(root, "beta/rl_beta.md", "---\ntitle: beta\nversion: 2.0.1\n---\n\n" + RULE_B)
    rule_scope.write_frontmatter(root, _scope(registry_path, ["tools/**"]))
    text = (root / ".agents" / "rules" / "beta" / "rl_beta.md").read_text(encoding="utf-8")
    assert text.startswith('---\ntitle: beta\nversion: 2.0.1\npaths:\n  - "tools/**"\n---\n\n# Rule: Beta')
    assert _codes(root, registry_path) == set()
    rule_scope.write_frontmatter(root, _scope(registry_path, []))
    text = (root / ".agents" / "rules" / "beta" / "rl_beta.md").read_text(encoding="utf-8")
    assert text.startswith("---\ntitle: beta\nversion: 2.0.1\n---\n\n# Rule: Beta")
    assert _codes(root, registry_path) == set()


def test_always_loaded_budget_counts_the_body_not_the_frontmatter(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    _write_rule(root, "beta/rl_beta.md", "---\ntitle: beta\n---\n\n" + RULE_B)
    report = rule_gate.run_gate(root, registry_path)
    assert report.findings == ()
    assert report.always_loaded_bytes == len((RULE_A + RULE_B).encode("utf-8"))


def test_comma_separated_paths_string_reads_as_the_host_reads_it(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    _scope(registry_path, ["tools/**", "tools/*.py"])
    _write_rule(root, "beta/rl_beta.md", '---\npaths: "tools/**, tools/*.py"\n---\n\n' + RULE_B)
    assert _codes(root, registry_path) == set()


@pytest.mark.parametrize(
    ("glob", "path", "expected"),
    [
        ("**/*.py", "a.py", True),
        ("**/*.py", "x/y/a.py", True),
        ("*.md", "x/a.md", False),
        ("tools/**", "tools/a/b.py", True),
        ("tools/*.{py,pyi}", "tools/a.pyi", True),
        ("tools/*.{py,pyi}", "tools/a.pyc", False),
        ("{a,b}/{c,d}/*.py", "b/c/x.py", True),
        ("tools/[ab]*.py", "tools/alpha.py", True),
        ("tools/[!ab]*.py", "tools/alpha.py", False),
        ("tools/x{y.py", "tools/x{y.py", True),
        ("photos [2024/**", "photos [2024/a.jpg", False),
        ("photos \\[2024/**", "photos [2024/a.jpg", True),
    ],
)
def test_glob_regex_follows_the_host_dialect(glob: str, path: str, expected: bool) -> None:
    assert (rule_scope.glob_regex(glob).match(path) is not None) is expected


def test_brace_glob_is_alive_not_dead(tree: tuple[Path, Path]) -> None:
    root, registry_path = tree
    rule_scope.write_frontmatter(root, _scope(registry_path, ["tools/*.{py,pyi}"]))
    assert _codes(root, registry_path) == set()


def test_tracked_files_walks_a_root_that_is_not_its_own_repository(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "a.py").write_text("", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "a.pyc").write_text("", encoding="utf-8")
    assert rule_scope.tracked_files(tmp_path) == ["pkg/a.py"]
