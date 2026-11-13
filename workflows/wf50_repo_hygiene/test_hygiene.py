"""Checks for the WF50 rename and reference-rewrite rules."""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("wf50_hygiene", Path(__file__).with_name("hygiene.py"))
hygiene = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hygiene)


def test_snake_names():
    cases = {
        "CHALLENGE.md": "challenge.md",
        "Paper-008.md": "paper_008.md",
        "SymbolGameStateMachine_ManimCE_v0.21.0.png": "symbol_game_state_machine_manim_ce_v0.21.0.png",
        "held_out-defect-2.py": "held_out_defect_2.py",
        "SC-L067.json": "sc_l067.json",
        "L057.cert.json": "l057.cert.json",
        "__init__.py": "__init__.py",
        "_Sidebar.md": "_sidebar.md",
        ".gitattributes": ".gitattributes",
        "provider-templates": "provider_templates",
    }
    for old, new in cases.items():
        assert hygiene.snake(old) == new, old


def test_glob_star_stays_in_one_folder():
    assert hygiene.glob_match("operads/skills/auto-skill", "operads/skills/*")
    assert not hygiene.glob_match("operads/skills/auto-skill/notes-x.md", "operads/skills/*")
    assert hygiene.glob_match("a/b/c/Foo.lean", "**/*.lean")
    assert hygiene.glob_match("Foo.lean", "**/*.lean")


def test_rewrite_paths_links_and_imports():
    moves = {
        "wiki/Paper-008.md": "wiki/paper_008.md",
        "pkg/adapters/L000.py": "pkg/adapters/l000.py",
        "docs/TASK.md": "docs/task.md",
        "other/LICENSE": "other/license",
    }
    files = list(moves) + ["papers/x/LICENSE", "README.md"]
    uniform, suffix, mods = hygiene.build_maps(moves, files)
    text = (
        "see [p](Paper-008.md) and wiki/Workflow#x, run wiki/Paper-008#top\n"
        "from pkg.adapters.L000 import run\n"
        "open docs/TASK.md, TASK.md, other/LICENSE, the LICENSE file\n"
    )
    out, n = hygiene.rewrite_text(text, uniform, suffix, mods, is_code=True)
    assert "(paper_008.md)" in out
    assert "wiki/paper_008#top" in out
    assert "pkg.adapters.l000 import" in out
    assert "docs/task.md, task.md" in out
    assert "other/license" in out
    assert "the LICENSE file" in out  # kept elsewhere, so a bare mention is left alone
    assert n >= 5


def _maps(moves, extra=()):
    return hygiene.build_maps(moves, list(moves) + list(extra))


def test_escaped_text_is_left_alone():
    uniform, suffix, mods = _maps({"docs/TASK.md": "docs/task.md"})
    text = r"x = 3/7.\ny"  # an escaped newline inside YAML or JSON text
    out, n = hygiene.rewrite_text(text, uniform, suffix, mods, is_code=True)
    assert out == text
    assert n == 0


def test_md_stem_only_inside_a_path():
    uniform, suffix, mods = _maps({"docs/OWNERSHIP.md": "docs/ownership.md"})
    text = 'kind: "OWNERSHIP"\nsee docs/OWNERSHIP.md\n'
    out, n = hygiene.rewrite_text(text, uniform, suffix, mods, is_code=True)
    assert 'kind: "OWNERSHIP"' in out
    assert "see docs/ownership.md" in out
    assert n == 1


def test_md_stem_needs_its_own_parent_folder():
    uniform, suffix, mods = _maps({"wiki/EIS.md": "wiki/eis.md", "docs/CHALLENGE.md": "docs/challenge.md"})
    text = r"PFP/EIS/PCIV stack; DISPOSITION=CHALLENGE\nNEXT; see wiki/EIS#gate"
    out, n = hygiene.rewrite_text(text, uniform, suffix, mods, is_code=True)
    assert "PFP/EIS/PCIV stack" in out
    assert r"CHALLENGE\nNEXT" in out
    assert "wiki/eis#gate" in out
    assert n == 1


def test_windows_path_keeps_backslash():
    uniform, suffix, mods = _maps({"docs/TASK.md": "docs/task.md"})
    out, n = hygiene.rewrite_text(r"open docs\TASK.md now", uniform, suffix, mods, is_code=False)
    assert out == r"open docs\task.md now"
    assert n == 1


def test_tool_folder_is_not_rewritten():
    policy = hygiene.Policy(hygiene.load_policy(), [])
    assert not policy.rewritable("workflows/wf50_repo_hygiene/test_hygiene.py")
    assert policy.rewritable("workflows/wf51_other/notes.md")
