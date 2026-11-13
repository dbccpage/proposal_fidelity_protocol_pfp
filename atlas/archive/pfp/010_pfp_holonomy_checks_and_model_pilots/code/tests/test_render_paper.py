"""Pandoc's TeX body must be read as UTF-8 before it is copied into paper.tex."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import render_paper  # noqa: E402


def test_render_keeps_section_sign_from_pandoc_body(tmp_path: Path, monkeypatch) -> None:
    """A section sign in the manuscript body survives into the emitted TeX.

    The default text encoding on this host is the ANSI code page once UTF-8
    mode is off. The check runs in that mode so a locale read is visible.
    """
    if sys.flags.utf8_mode:
        env = dict(os.environ)
        env["PYTHONUTF8"] = "0"
        completed = subprocess.run(
            [
                sys.executable, "-X", "utf8=0", "-m", "pytest",
                str(Path(__file__).resolve()), "-s", "--tb=short", "-p", "no:cacheprovider",
            ],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            check=False,
            text=True,
        )
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        assert completed.returncode == 0
        return
    package = Path(__file__).resolve().parents[2]
    root = tmp_path / "pkg"
    (root / "tools").mkdir(parents=True)
    shutil.copy(package / "tools" / "paper_preamble.tex", root / "tools" / "paper_preamble.tex")
    shutil.copy(package / "tools" / "latex_inline_code.lua", root / "tools" / "latex_inline_code.lua")
    (root / "paper.md").write_text(
        "# Holonomy checks\n\nJeremy Carroll\n\n2026-10-02\n\n</div>\n\nwhose §2 admits a loop.\n",
        encoding="utf-8",
    )
    stub = tmp_path / "xelatex.bat"
    stub.write_text(
        "@echo off\r\necho.>paper.log\r\necho.>paper.pdf\r\nexit /b 0\r\n",
        encoding="ascii",
    )
    monkeypatch.setattr(render_paper, "ROOT", root)
    render_paper.render("pandoc", str(stub))
    tex = (root / "paper.tex").read_text(encoding="utf-8")
    assert "§2" in tex
    assert "Â§" not in tex
    print("ASSERT '§2' in paper.tex")
    print("ASSERT 'Â§' not in paper.tex")
