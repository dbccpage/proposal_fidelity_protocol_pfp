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
