#!/usr/bin/env python3
"""Render the package manuscript with pandoc and XeLaTeX; optionally record commands.

Requires the external rendering tools, but no third-party Python package.
The record names actual outputs and tool invocations, not mathematical evidence.
"""

from __future__ import annotations

import argparse
import datetime
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

HEADER = r"""\setlength{\emergencystretch}{3em}
\usepackage{fvextra}
\DefineVerbatimEnvironment{Highlighting}{Verbatim}{breaklines,commandchars=\\\{\},fontsize=\small}
\setlength{\tabcolsep}{4pt}
"""


def render(package: Path, pandoc: str, latex: str) -> list[dict]:
    metadata = json.loads((package / "zenodo_metadata.json").read_text(encoding="utf-8"))
    source = (package / "paper.md").read_text(encoding="utf-8")
    if "</div>\n\n" not in source:
        raise ValueError("expected the manuscript's title block before its body")
    body = source.split("</div>\n\n", 1)[1].replace("\u2013", "-").replace("\u2014", "-")
    records = []
    with tempfile.TemporaryDirectory(prefix="pfp-v-render-") as temporary:
        tmp = Path(temporary)
        (tmp / "body.md").write_text(body, encoding="utf-8")
        (tmp / "header.tex").write_text(HEADER, encoding="utf-8")
        command = [
            pandoc, str(tmp / "body.md"), "--from=markdown+tex_math_single_backslash",
            "--to=latex", "--standalone", f"--metadata=title:{metadata['title']}",
            "--metadata=author:Jeremy H. Carroll",
            f"--metadata=date:{metadata['publication_date']} - Version {metadata['version']} - Practitioner guide - Publication-review candidate",
            "-V", "geometry:margin=22mm", "-V", "fontsize=11pt", "-V", "colorlinks=true",
            "--include-in-header", str(tmp / "header.tex"), "-o", str(package / "paper.tex"),
        ]
        compile_command = [latex, "-interaction=nonstopmode", "-halt-on-error", "-output-directory", str(tmp), str(package / "paper.tex")]
        for invocation in [command, compile_command, compile_command]:
            started = datetime.datetime.now(datetime.timezone.utc).isoformat()
            result = subprocess.run(invocation, cwd=package, capture_output=True, text=True, timeout=60, check=False)
            records.append({
                "command": invocation, "started_at_utc": started,
                "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
            })
            if result.returncode:
                raise RuntimeError(result.stdout[-6000:] + result.stderr[-2000:])
        log = (tmp / "paper.log").read_text(encoding="utf-8", errors="replace")
        warnings = [line for line in log.splitlines() if "Overfull" in line or "Missing character" in line]
        if warnings:
            raise RuntimeError("layout verification failed: " + "; ".join(warnings))
        shutil.copyfile(tmp / "paper.pdf", package / "paper.pdf")
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pandoc", default="pandoc")
    parser.add_argument("--latex", default="xelatex")
    parser.add_argument("--record", type=Path)
    args = parser.parse_args()
    package = Path(__file__).resolve().parents[1]
    records = render(package, args.pandoc, args.latex)
    if args.record:
        args.record.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print("OK: paper.tex and paper.pdf rendered; no overfull boxes or missing characters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
