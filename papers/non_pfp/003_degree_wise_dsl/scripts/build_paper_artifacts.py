"""Build Paper 009's .tex and .pdf from canonical Markdown.

Rendering the manuscript is not evidence for any claim in it, and a clean
LaTeX run certifies nothing about the mathematics.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PAPER_MD = PACKAGE_ROOT / "degree_wise_dsl.md"
PREAMBLE = PACKAGE_ROOT / "scripts" / "obstruction-preamble.tex"
TEX_OUT = PACKAGE_ROOT / "degree_wise_dsl.tex"
PDF_OUT = PACKAGE_ROOT / "degree_wise_dsl.pdf"

SOURCE_EPOCH = 1788825600


def need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise SystemExit(f"BLOCKED: {tool} not found on PATH")
    return path


def build_tex(destination: Path) -> Path:
    pandoc = need("pandoc")
    cmd = [
        pandoc,
        str(PAPER_MD),
        "--from",
        "markdown+tex_math_dollars+pipe_tables+raw_tex+backtick_code_blocks+fenced_code_attributes",
        "--to",
        "latex",
        "--standalone",
        "--pdf-engine",
        "xelatex",
        "--include-in-header",
        str(PREAMBLE),
        "--highlight-style",
        "kate",
        "--wrap",
        "preserve",
        "-V",
        "geometry:margin=1in",
        "-V",
        "linkcolor=RoyalBlue",
        "-o",
        str(destination),
    ]
    run = subprocess.run(cmd, cwd=PACKAGE_ROOT, capture_output=True, timeout=1800)
    err = run.stderr.decode("utf-8", errors="replace")
    if run.returncode != 0:
        raise SystemExit("pandoc failed:\n" + run.stdout.decode("utf-8", errors="replace") + err)
    for line in err.strip().splitlines()[:10]:
        if line.strip():
            print(f"    pandoc: {line}")

    tex_text = destination.read_text(encoding="utf-8")

    # Invariant: Zero-Line Header Block (no \maketitle, no \hrule)
    header_block = r"""\begin{center}
{\LARGE\bfseries Degree-Wise Obstruction Calculus and Symbolic DSL: Graded Cochain Complexes, Degree Separation, and Local-Global Gate Non-Factorization \par}
\vspace{0.4em}
{\large Graded Cochain Complexes, Degree Separation, and Local-Global Gate Non-Factorization \par}
\vspace{0.8em}
{\large Jeremy H. Carroll \par}
\vspace{0.3em}
{\large 2026-09-30 \par}
\vspace{0.3em}
{\large Version 2.1.0 \par}
\end{center}"""

    # Replace only the executable \maketitle in document body
    tex_text = tex_text.replace("\\begin{document}\n\\maketitle", "\\begin{document}\n" + header_block)
    tex_text = tex_text.replace("\\begin{document}\r\n\\maketitle", "\\begin{document}\n" + header_block)
    tex_text = tex_text.replace(r"% add subtitle to \maketitle", r"% add subtitle to title block")
    tex_text = tex_text.replace(r"\maketitle", "")

    # Sanitize any accidental authorityeffect tokens
    tex_text = re.sub(r"(?i)authorityeffect\s*:\s*none\.?", "", tex_text)
    tex_text = tex_text.replace(r"\textbf{AuthorityEffect}", r"\textbf{Authority status}")
    tex_text = tex_text.replace("AuthorityEffect", "Authority status")

    # Fix wide boxed math statements that cause Overfull \hbox
    wide_box1 = (
        r"\text{The obstruction calculus is a graded symbolic system in which } d_0, d_1, \pi_Z \text{ operate on distinct cochain degrees, and valid expressions must respect degree typing and } \ell^1(E; g) \text{ aggregation. Collapsing degrees or relaxing the norm destroys recoverable obstruction information.}"
    )
    wrapped_box1 = (
        r"\parbox{0.95\textwidth}{\centering The obstruction calculus is a graded symbolic system in which $d_0, d_1, \pi_Z$ operate on distinct cochain degrees, and valid expressions must respect degree typing and $\ell^1(E; g)$ aggregation. Collapsing degrees or relaxing the norm destroys recoverable obstruction information.}"
    )
    tex_text = tex_text.replace(r"\boxed{" + "\n" + wide_box1 + "\n" + r"}", r"\fbox{" + wrapped_box1 + r"}")
    tex_text = tex_text.replace(r"\boxed{" + "\r\n" + wide_box1 + "\r\n" + r"}", r"\fbox{" + wrapped_box1 + r"}")

    wide_box2 = (
        r"d_0 \text{ and } d_1 \text{ operate between distinct cochain degrees}; \pi_Z : C^1 \to C^1 \text{ is a declared degree-preserving } C^1 \text{ projection whose rewrite use requires certified idempotence and exact-killing invariants.}"
    )
    wrapped_box2 = (
        r"\parbox{0.95\textwidth}{\centering $d_0$ and $d_1$ operate between distinct cochain degrees; $\pi_Z : C^1 \to C^1$ is a declared degree-preserving $C^1$ projection whose rewrite use requires certified idempotence and exact-killing invariants.}"
    )
    tex_text = tex_text.replace(r"\boxed{" + "\n" + wide_box2 + "\n" + r"}", r"\fbox{" + wrapped_box2 + r"}")
    tex_text = tex_text.replace(r"\boxed{" + "\r\n" + wide_box2 + "\r\n" + r"}", r"\fbox{" + wrapped_box2 + r"}")

    destination.write_text(tex_text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")
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
                [
                    xelatex,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    work.name,
                ],
                cwd=tmp,
                capture_output=True,
                timeout=1800,
                env=env,
            )
            if run.returncode != 0:
                log = tmp / (work.stem + ".log")
                tail = ""
                if log.exists():
                    tail = "\n".join(
                        log.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
                    )
                raise SystemExit(f"xelatex pass {index} failed:\n{tail}")
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
