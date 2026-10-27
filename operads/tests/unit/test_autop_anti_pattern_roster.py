"""OEAUTOP calls every anti-pattern skill, including the Lean 4 hunter."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ORCHESTRATOR = REPO / "operads" / "skills" / "auto-oe-autop" / "scripts" / "orchestrate_autop.py"
LEAN_AUDITOR = (
    REPO
    / "operads"
    / "skills"
    / "techne-code-lean4-anti-patterns"
    / "scripts"
    / "lean4_anti_pattern_auditor.py"
)
RUST_AUDITOR = (
    REPO
    / "operads"
    / "skills"
    / "techne-code-rust-anti-patterns"
    / "scripts"
    / "rust_anti_pattern_auditor.py"
)
LINT = REPO / "operads" / "skills" / "auto-anti-pattern-lint" / "scripts" / "anti_pattern_lint.py"
CATALOG_SLOTS = (
    "autop",
    "html",
    "javascript",
    "json",
    "lean4",
    "manim",
    "markdown",
    "python",
    "rust",
    "sql",
    "svg",
)
REQUIRED_SKILLS = (
    "auto-anti-pattern-lint",
    "auto-code-anti-pattern-hunter",
    "techne-code-lean4-anti-patterns",
    "techne-code-python-anti-patterns",
    "techne-code-rust-anti-patterns",
    "techne-code-sql-anti-patterns",
)

STUB = """import sys
from pathlib import Path
args = sys.argv
for flag in ("--report-out", "--output"):
    if flag in args:
        dest = Path(args[args.index(flag) + 1])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("{}", encoding="utf-8")
print("called")
"""


def _load_orchestrator():
    spec = importlib.util.spec_from_file_location("orchestrate_autop", ORCHESTRATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["orchestrate_autop"] = module
    spec.loader.exec_module(module)
    return module


def _skill(root: Path, name: str, *, script: bool) -> None:
    skill = root / "operads" / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
    if script:
        scripts = skill / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text(STUB, encoding="utf-8")


def test_catalog_slots_and_lean4_skill_exist() -> None:
    catalog = REPO / "operads" / "patterns"
    for name in CATALOG_SLOTS:
        assert (catalog / "anti" / name).is_dir(), f"anti/{name}"
        assert (catalog / "helpful" / name).is_dir(), f"helpful/{name}"
    assert (catalog / "anti" / "json" / "CATALOG_EMPTY.txt").is_file()
    assert (catalog / "helpful" / "json" / "CATALOG_EMPTY.txt").is_file()
    assert (
        REPO / "operads" / "skills" / "techne-code-lean4-anti-patterns" / "SKILL.md"
    ).is_file()
    module = _load_orchestrator()
    found = module.discover_anti_pattern_skills(REPO / "operads" / "skills")
    for skill_id in REQUIRED_SKILLS:
        assert skill_id in found


def test_invoke_calls_every_anti_pattern_skill_and_refuses_a_missing_lean4_hunter(tmp_path: Path) -> None:
    module = _load_orchestrator()
    for name in ("auto-anti-pattern-lint", "techne-code-lean4-anti-patterns"):
        _skill(tmp_path, name, script=True)
    _skill(tmp_path, "unrelated-helper", script=True)
    result = module.AutopStageResult(1, "episode_intake_and_antiskill_mining", "PASS")
    rows = module.invoke_anti_pattern_skills(tmp_path, result)
    called = {row["skill_id"] for row in rows}
    assert called == {"auto-anti-pattern-lint", "techne-code-lean4-anti-patterns"}
    assert result.status == "PASS"
    assert all(row["status"] == "PASS" for row in rows)

    bare = tmp_path / "bare"
    _skill(bare, "auto-anti-pattern-lint", script=True)
    refused = module.AutopStageResult(1, "episode_intake_and_antiskill_mining", "PASS")
    refused_rows = module.invoke_anti_pattern_skills(bare, refused)
    assert any(row["status"] == "MISSING_SKILL" for row in refused_rows)
    assert refused.status == "FAIL"


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_lean4_auditor_sees_sorry_and_ignores_comments(tmp_path: Path) -> None:
    source = tmp_path / "Sample.lean"
    source.write_text(
        "theorem open_goal : True := by\n"
        "  sorry\n"
        "theorem noted : True := by\n"
        "  -- sorry\n"
        "theorem hidden : True := by\n"
        "  /- sorry -/\n"
        "  trivial\n"
        "theorem thermodynamic_limit : True := by\n"
        "  trivial\n"
        "theorem thermodynamic_limit_finite_envelope : True := by\n"
        "  trivial\n",
        encoding="utf-8",
    )
    shell = tmp_path / "build.ps1"
    shell.write_text("lake build Foo\n", encoding="utf-8")
    failed = _run(LEAN_AUDITOR, "--path", str(tmp_path), "--check")
    assert failed.returncode == 1
    assert "AP_LN_001" in failed.stdout or failed.returncode == 1
    report = tmp_path / "receipt.json"
    again = _run(LEAN_AUDITOR, "--path", str(tmp_path), "--report-out", str(report))
    payload = json.loads(report.read_text(encoding="utf-8"))
    ids = [row["id"] for row in payload["findings"]]
    assert ids.count("AP_LN_001") == 1
    assert ids.count("AP_LN_002") == 1
    assert ids.count("AP_LN_003") == 1
    assert again.returncode == 0

    cached = tmp_path / "cached.ps1"
    cached.write_text("lake exe cache get\nlake build Foo\n", encoding="utf-8")
    shell.unlink()
    clean_shell = _run(LEAN_AUDITOR, "--path", str(cached), "--check")
    assert clean_shell.returncode == 0


def test_rust_auditor_requires_ord_on_derived_enum(tmp_path: Path) -> None:
    broken = tmp_path / "broken.rs"
    broken.write_text("#[derive(Debug, PartialEq)]\npub enum Color { Red }\n", encoding="utf-8")
    assert _run(RUST_AUDITOR, "--path", str(broken), "--check").returncode == 1
    sound = tmp_path / "sound.rs"
    sound.write_text(
        "#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]\npub enum Color { Red }\n",
        encoding="utf-8",
    )
    assert _run(RUST_AUDITOR, "--path", str(sound), "--check").returncode == 0


def test_catalog_lint_accepts_the_live_estate_and_rejects_a_missing_slot(tmp_path: Path) -> None:
    live = _run(LINT, "--catalog", str(REPO / "operads" / "patterns"), "--check")
    assert live.returncode == 0, live.stdout + live.stderr
    slot = tmp_path / "patterns"
    for name in CATALOG_SLOTS:
        (slot / "anti" / name).mkdir(parents=True)
        (slot / "helpful" / name).mkdir(parents=True)
    assert _run(LINT, "--catalog", str(slot), "--check").returncode == 0
    (slot / "anti" / "json").rmdir()
    assert _run(LINT, "--catalog", str(slot), "--check").returncode == 1


def test_commented_sorry_is_not_a_finding(tmp_path: Path) -> None:
    source = tmp_path / "Noted.lean"
    source.write_text("theorem noted : True := by\n  -- sorry\n  trivial\n", encoding="utf-8")
    assert _run(LEAN_AUDITOR, "--path", str(source), "--check").returncode == 0


def test_auto_anti_pattern_lint_scans_files(tmp_path: Path) -> None:
    bad_md = tmp_path / "bad.md"
    bad_md.write_text("# Doc\n\n* Bullet item with asterisk\n", encoding="utf-8")
    failed = _run(LINT, "--files", str(bad_md), "--check")
    assert failed.returncode == 1
    assert "Anti-pattern file findings: 1" in failed.stdout

    good_md = tmp_path / "good.md"
    good_md.write_text("# Doc\n\n- Bullet item with hyphen\n", encoding="utf-8")
    passed = _run(LINT, "--files", str(good_md), "--check")
    assert passed.returncode == 0
    assert "Anti-pattern file findings: 0" in passed.stdout

