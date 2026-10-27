#!/usr/bin/env python3
"""Build Paper 011's TeX and PDF with Pandoc and the deposited preamble."""

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
    title = re.search(r"^# (.+)$", manuscript, re.M).group(1)
    header = manuscript.split("</div>", 1)[0]
    author = next(line.rstrip("\\") for line in header.splitlines() if line.startswith("Bare Metal Anchor"))
    date = next(line for line in header.splitlines() if line.startswith("2026-"))
    body_source = manuscript.split("</div>", 1)[1]
    table_space = {"1": 18, "2": 20, "3": 25, "4": 16}
    body_source = re.sub(
        r"(?m)^(Table ([1-4])\. )",
        lambda match: "\\Needspace{"
        + str(table_space[match.group(2)])
        + "\\baselineskip}\n\n"
        + match.group(1),
        body_source,
    )
    environment = dict(os.environ)
    environment["SOURCE_DATE_EPOCH"] = "1790899200"
    with tempfile.TemporaryDirectory(prefix="paper011-render-") as directory:
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
            "\\date{" + escaped(date) + "}\n\\begin{document}\n"
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
        for _ in range(2):
            completed = subprocess.run(
                [xelatex, "-interaction=nonstopmode", "-halt-on-error", "paper.tex"],
                cwd=build,
                env=environment,
                text=True,
                capture_output=True,
                timeout=90,
                check=False,
            )
            if completed.returncode:
                raise RuntimeError(completed.stdout[-6000:] + completed.stderr)
        log = (build / "paper.log").read_text(errors="replace")
        serious = [
            line for line in log.splitlines() if "Overfull" in line or "Missing character" in line
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
