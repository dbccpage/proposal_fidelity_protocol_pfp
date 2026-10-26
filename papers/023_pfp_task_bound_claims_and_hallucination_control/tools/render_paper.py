#!/usr/bin/env python3
"""Build Paper 023's TeX and PDF with Pandoc and the deposited preamble."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def escaped(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "$": r"\$",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def render(pandoc: str, xelatex: str) -> None:
    manuscript = (ROOT / "paper.md").read_text(encoding="utf-8")
    title_match = re.search(r"^# (.+)$", manuscript, re.M)
    title = title_match.group(1) if title_match else "PFP: Task-bound claims and the scope of hallucination control"
    author_match = re.search(r"\*\*Author:\*\*\s*(.+)$", manuscript, re.M)
    author = author_match.group(1).strip() if author_match else "Jeremy H. Carroll"
    date_match = re.search(r"\*\*Date:\*\*\s*(.+)$", manuscript, re.M)
    date_val = date_match.group(1).strip() if date_match else "2026-10-05"
    version_match = re.search(r"\*\*Version:\*\*\s*(.+)$", manuscript, re.M)
    ver = version_match.group(1).strip() if version_match else "0.1.0"
    date_str = f"{date_val} (v{ver})"

    # Split body at "## Abstract"
    if "## Abstract" in manuscript:
        body_source = "## Abstract\n\n" + manuscript.split("## Abstract", 1)[1].lstrip()
    else:
        body_source = manuscript

    environment = dict(os.environ)
    environment["SOURCE_DATE_EPOCH"] = "1790899200"
    with tempfile.TemporaryDirectory(prefix="paper023-render-") as directory:
        build = Path(directory)
        (build / "body.md").write_text(body_source, encoding="utf-8")
        subprocess.run(
            [
                pandoc,
                "--from",
                "markdown+tex_math_single_backslash",
                "--to",
                "latex",
                "--listings",
                "--lua-filter",
                str(ROOT / "tools" / "latex_inline_code.lua"),
                "body.md",
                "-o",
                "body.tex",
            ],
            cwd=build,
            check=True,
        )
        preamble = (ROOT / "tools" / "paper_preamble.tex").read_text(encoding="utf-8")
        heading = (
            "\n\\title{" + escaped(title) + "}\n\\author{" + escaped(author) + "}\n"
            "\\date{" + escaped(date_str) + "}\n\\begin{document}\n"
            "\\makeatletter\n\\begin{center}\n"
            "{\\LARGE \\@title\\par}\n\\vspace{0.8em}\n"
            "{\\normalsize \\@author\\par}\n\\vspace{0.5em}\n"
            "{\\small \\@date\\par}\n\\end{center}\n\\makeatother\n"
        )
        tex = (
            preamble
            + heading
            + (build / "body.tex").read_text(encoding="utf-8")
            + "\n\\end{document}\n"
        )
        (build / "paper.tex").write_text(tex, encoding="utf-8")
        for _ in range(3):
            completed = subprocess.run(
                [xelatex, "-interaction=nonstopmode", "-halt-on-error", "paper.tex"],
                cwd=build,
                env=environment,
                text=True,
                capture_output=True,
                timeout=120,
                check=False,
            )
            if completed.returncode:
                raise RuntimeError(completed.stdout[-6000:] + completed.stderr)
        log = (build / "paper.log").read_text(errors="replace")
        serious = [
            line for line in log.splitlines() if "Overfull \\hbox" in line or "Missing character" in line
        ]
        if serious:
            raise RuntimeError("layout diagnostics: " + "\n".join(serious))
        (ROOT / "paper.tex").write_text(tex, encoding="utf-8")
        (ROOT / "paper.pdf").write_bytes((build / "paper.pdf").read_bytes())
        print("PASS: paper.tex and paper.pdf rebuilt; no overfull or missing-character warnings")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pandoc", default="pandoc")
    parser.add_argument("--xelatex", default="xelatex")
    args = parser.parse_args()
    render(args.pandoc, args.xelatex)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
