"""Build Paper 002's .tex and .pdf from canonical Markdown.

AuthorityEffect: None. Rendering the manuscript is not evidence for any claim
in it, and a clean LaTeX run certifies nothing about the mathematics.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PAPER_MD = PACKAGE_ROOT / "l1_native_cohomology.md"
PREAMBLE = PACKAGE_ROOT / "scripts" / "obstruction-preamble.tex"
TEX_OUT = PACKAGE_ROOT / "l1_native_cohomology.tex"
PDF_OUT = PACKAGE_ROOT / "l1_native_cohomology.pdf"

SOURCE_EPOCH = 1788825600


def need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise SystemExit(f"BLOCKED: {tool} not found on PATH")
    return path


def build_tex(destination: Path) -> Path:
    pandoc = need("pandoc")
    cmd = [
        pandoc, str(PAPER_MD),
        "--from", "markdown+tex_math_dollars+tex_math_single_backslash+pipe_tables+raw_tex"
                  "+backtick_code_blocks+fenced_code_attributes",
        "--to", "latex",
        "--standalone",
        "--pdf-engine", "xelatex",
        "--include-in-header", str(PREAMBLE),
        "--highlight-style", "kate",
        "--wrap", "preserve",
        "-V", "geometry:margin=1in",
        "-V", "linkcolor=RoyalBlue",
        "-o", str(destination),
    ]
    run = subprocess.run(cmd, cwd=PACKAGE_ROOT, capture_output=True, timeout=1800)
    err = run.stderr.decode("utf-8", errors="replace")
    if run.returncode != 0:
        raise SystemExit("pandoc failed:\n"
                         + run.stdout.decode("utf-8", errors="replace")
                         + err)
    for line in err.strip().splitlines()[:10]:
        if line.strip():
            print(f"    pandoc: {line}")

    destination.write_bytes(
        destination.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    )
    return destination


def build_pdf(tex: Path, destination: Path) -> Path:
    xelatex = need("xelatex")
    env = dict(os.environ)
    env["SOURCE_DATE_EPOCH"] = str(SOURCE_EPOCH)
    env["FORCE_SOURCE_DATE"] = "1"
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        work = tmp / tex.name
        shutil.copyfile(tex, work)
        for index in (1, 2, 3):
            run = subprocess.run(
                [xelatex, "-interaction=nonstopmode", "-halt-on-error",
                 "-file-line-error", work.name],
                cwd=tmp, capture_output=True, timeout=1800, env=env)
            if run.returncode != 0:
                log = (tmp / (work.stem + ".log"))
                tail = ""
                if log.exists():
                    tail = "\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-40:])
                output = (run.stdout + run.stderr).decode("utf-8", errors="replace")
                raise SystemExit(f"xelatex pass {index} failed:\n{output}\n{tail}")
            log_text = (tmp / (work.stem + ".log")).read_text(
                encoding="utf-8", errors="replace"
            )
            missing = [line for line in log_text.splitlines() if "Missing character:" in line]
            if missing:
                raise SystemExit("xelatex missing glyphs:\n" + "\n".join(missing))
        # Retain diagnostics for the local build; .log is excluded from the deposit.
        shutil.copyfile(tmp / (tex.stem + ".log"), destination.with_suffix(".log"))
        shutil.copyfile(tmp / (tex.stem + ".pdf"), destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tex-only", action="store_true")
    args = parser.parse_args()

    print(f"Building .tex: {TEX_OUT}")
    build_tex(TEX_OUT)
    if args.tex_only:
        return

    print(f"Building .pdf: {PDF_OUT}")
    build_pdf(TEX_OUT, PDF_OUT)
    print("Build complete.")


if __name__ == "__main__":
    main()
