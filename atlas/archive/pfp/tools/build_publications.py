"""Build source-bound PFP paper packages with installed Pandoc and XeLaTeX.

This command makes no network calls and runs no research tests. It compiles only
changed TeX; an existing PDF is reused only with a matching TeX and PDF digest.
With ``--deposit`` it also writes each package's standalone ``paper.tex`` and
``paper.pdf``: links to sibling papers point to the series on GitHub, other
repository links stay pinned to the catalog's source baseline, and the PDF is
compiled with three XeLaTeX passes that must report no overfull lines.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

SERIES = Path(__file__).resolve().parents[1]
REPO = (next((p for p in SERIES.parents if (p / ".git").exists()), None) or SERIES.parents[4])
PUB = SERIES / "publication"
SOURCE_FORMAT = "markdown+tex_math_single_backslash+tex_math_dollars"
GITHUB = "https://github.com/dbccpage/the_symbol_game"
SERIES_REF = "main"
TITLE_BLOCK = r"""\makeatletter
\begin{center}
{\LARGE \@title\par}
\vspace{0.8em}
{\normalsize \@author\par}
\vspace{0.5em}
{\small \@date\par}
\end{center}
\makeatother"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, text: str | None = None, cwd: Path = SERIES) -> str:
    result = subprocess.run(command, input=text, cwd=cwd, capture_output=True,
                            text=True, encoding="utf-8", errors="strict", timeout=180, check=False)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\n{result.stdout[-6000:]}\n{result.stderr[-3000:]}")
    return result.stdout


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def package_dirs(series: Path, entry: dict) -> list[Path]:
    """Resolve a catalog entry to its package directory.

    A numeric id globs ``<id>_*``. ``package_dir`` pins one directory name when
    the shelf prefix and the catalog id have diverged. The pin is a single
    path segment, so it cannot leave the collection directory.
    """
    pinned = entry.get("package_dir")
    if pinned is None:
        return list(series.glob(entry["id"] + "_*"))
    if type(pinned) is not str or pinned != Path(pinned).name or pinned in {".", ".."}:
        raise ValueError(f"Invalid package_dir for {entry['id']}")
    folder = series / pinned
    return [folder] if folder.is_dir() else []


def publications(catalog: dict) -> list[dict]:
    result = []
    for entry in catalog["publications"]:
        if entry["id"] not in {f"{i:03}" for i in range(0, 100)}:
            raise ValueError("Unknown publication identifier")
        matches = package_dirs(SERIES, entry)
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one package for {entry['id']}")
        folder = matches[0]
        source = folder / "paper.md"
        ledgers = list(folder.glob("*claim_ledger.md"))
        if not source.is_file() or len(ledgers) != 1:
            raise ValueError(f"Missing or ambiguous manuscript/ledger in {folder}")
        result.append(dict(entry, source=source, ledger=ledgers[0]))
    return result


def header_fields(text: str) -> tuple[str, str | None, str | None]:
    """Return the manuscript title, author line, and version/date line."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("# "))
    rest = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if stripped.startswith(("## ", "</div>", "Code baseline")):
            break
        if stripped:
            rest.append(stripped.rstrip("\\").strip())
    return lines[start][2:].strip(), (rest[0] if rest else None), (rest[1] if len(rest) > 1 else None)


def github_url(local: Path, ref: str, fragment: str) -> str:
    kind = "tree" if local.is_dir() else "blob"
    path = quote(local.relative_to(REPO).as_posix(), safe="/")
    return f"{GITHUB}/{kind}/{ref}/{path}" + ("#" + fragment if fragment else "")


def exists_in_git(local: Path, ref: str) -> bool:
    if not local.is_relative_to(REPO):
        return False
    rel = local.relative_to(REPO).as_posix()
    res = subprocess.run(["git", "cat-file", "-e", f"{ref}:{rel}"], cwd=REPO, capture_output=True)
    return res.returncode == 0


def rewrite_links(ast: dict, source: Path, output: Path, mapping: dict[Path, Path], base: str) -> dict:
    def walk(node):
        if isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, dict):
            if node.get("t") in ("Link", "Image"):
                target = node["c"][-1][0]
                parsed = urlsplit(target)
                if not parsed.scheme and parsed.path and not target.startswith("//"):
                    local = (source.parent / unquote(parsed.path)).resolve()
                    if local in mapping:
                        destination = mapping[local]
                        rewritten = Path(os.path.relpath(destination, output.parent)).as_posix()
                        fragment = "#" + parsed.fragment if parsed.fragment and destination.suffix != ".pdf" else ""
                        node["c"][-1][0] = rewritten + fragment
                    elif (local.exists() and local.is_relative_to(REPO)) or exists_in_git(local, base):
                        node["c"][-1][0] = github_url(local, base, parsed.fragment)
                    else:
                        raise ValueError(f"Unresolved source link in {source.name}: {target}")
            for value in node.values():
                walk(value)
    walk(ast)
    return ast


def rewrite_deposit_links(ast: dict, source: Path, base: str) -> dict:
    """Links for a standalone deposit: series files on the series branch, evidence pinned."""
    package = source.parent

    def walk(node):
        if isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, dict):
            if node.get("t") in ("Link", "Image"):
                target = node["c"][-1][0]
                parsed = urlsplit(target)
                if not parsed.scheme and parsed.path and not target.startswith("//"):
                    local = (package / unquote(parsed.path)).resolve()
                    ref = SERIES_REF if local.is_relative_to(SERIES) else base
                    if not ((local.exists() and local.is_relative_to(REPO)) or exists_in_git(local, ref)):
                        raise ValueError(f"Unresolved source link in {source.name}: {target}")
                    if node["t"] == "Image" and local.is_relative_to(package):
                        node["c"][-1][0] = local.relative_to(package).as_posix()
                    else:
                        node["c"][-1][0] = github_url(local, ref, parsed.fragment)
            for value in node.values():
                walk(value)
    walk(ast)
    return ast


LEAN_NAME = re.compile(r"([A-Za-z0-9_./-]*\.lean)([.,;:)]*)")


def wrap_inline_paths(node) -> None:
    if isinstance(node, list):
        for value in node:
            wrap_inline_paths(value)
    elif isinstance(node, dict):
        if node.get("t") in ("Code", "Str"):
            token = node["c"][1] if node["t"] == "Code" else node["c"]
            identifier = node.get("t") == "Code" or any(char in token for char in "/_.") or re.fullmatch(r"[a-fA-F0-9]{32,}", token)
            lean = LEAN_NAME.fullmatch(token)
            if lean:
                # Lean file names stay whole, so extracted PDF text names the real file.
                node.update(t="RawInline", c=["latex", r"\mbox{\nolinkurl{" + lean.group(1) + "}}" + lean.group(2)])
            elif len(token) > 12 and identifier and re.fullmatch(r"[A-Za-z0-9_./:+()=-]+", token):
                node.update(t="RawInline", c=["latex", r"\nolinkurl{" + token + "}"])
        elif node.get("t") == "Math":
            kind, formula = node["c"]
            if kind["t"] == "DisplayMath" or len(formula) > 140:
                node.update(t="RawInline", c=["latex", "\n\\begin{center}\\PfpDisplayMath{" + formula + "}\\end{center}\n"])
            else:
                node["c"][1] = formula.replace(",", r",\allowbreak ")
        for value in node.values():
            wrap_inline_paths(value)


def render_tex(pandoc: str, ast: dict, header: Path, title: str, author: str, date: str, base: str) -> str:
    body_start = next((i for i, block in enumerate(ast["blocks"])
                       if block.get("t") == "Header" and block["c"][0] == 2), None)
    if body_start is not None:
        ast["blocks"] = ast["blocks"][body_start:]
    source_identity = {"t": "Para", "c": [
        {"t": "Strong", "c": [{"t": "Str", "c": "Code baseline:"}]},
        {"t": "Space"}, {"t": "Code", "c": [["", [], []], base]},
    ]}
    ast["blocks"].insert(0, source_identity)
    wrap_inline_paths(ast)
    tex = run([pandoc, "-f", "json", "-t", "latex", "--standalone", "--listings", "--include-in-header", str(header),
               "-V", "geometry:margin=25mm", "-V", "fontsize:11pt", "-V", "colorlinks:true",
               "-M", "title=" + title, "-M", "author=" + author, "-M", "date=" + date], text=json.dumps(ast))
    # Pandoc rounds fractional column widths up (e.g. seven times 0.1429),
    # creating avoidable table overflow. Keep each rounded width just below it.
    tex = re.sub(r"\\real\{(0\.\d+)\}", lambda m: r"\real{" + f"{max(0.0001, float(m[1]) - 0.0001):.4f}" + "}", tex)
    tex = re.sub(r"\\begin\{longtable\}.*?\\end\{longtable\}",
                 lambda m: "\\begingroup\\begin{landscape}\\small\n" + m[0] + "\n\\end{landscape}\\endgroup" if m[0].split(r"\toprule")[0].count(r"\real{") >= 6 else m[0], tex, flags=re.S)
    return tex.replace(r"\maketitle", TITLE_BLOCK)


def compile_pdf(latex: str, tex: Path, pdf: Path) -> str:
    """Three XeLaTeX passes in a scratch directory; refuse overfull lines."""
    with tempfile.TemporaryDirectory(prefix="pfp-tex-") as scratch:
        logs = [run([latex, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error",
                     f"-output-directory={scratch}", tex.name], cwd=tex.parent) for _ in range(3)]
        log = "\n".join(logs)
        if "Missing character" in log:
            missing = [line for line in log.splitlines() if "Missing character" in line]
            raise RuntimeError(f"{tex}: missing glyphs: {missing[:5]}")
        if "Overfull \\hbox" in log:
            lines = [line for line in log.splitlines() if "Overfull \\hbox" in line]
            raise RuntimeError(f"{tex}: {len(lines)} overfull line warning(s): {lines[:5]}")
        shutil.copyfile(Path(scratch) / (tex.stem + ".pdf"), pdf)
    return log


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pandoc", default=shutil.which("pandoc"))
    parser.add_argument("--latex", "--pdflatex", dest="latex", default=shutil.which("xelatex"),
                        help="XeLaTeX executable (the deposit review gate recompiles with XeLaTeX)")
    parser.add_argument("--pdf", action="store_true", help="compile the collection PDFs under publication/")
    parser.add_argument("--deposit", action="store_true", help="write and compile each package's paper.tex/paper.pdf")
    parser.add_argument("--only", default="", help="comma-separated publication identifiers to build")
    parser.add_argument("--author-review", action="store_true", help="build the separate current author-review catalog without changing deposited artifacts")
    args = parser.parse_args()
    if not args.pandoc or ((args.pdf or args.deposit) and not args.latex):
        parser.error("supply installed Pandoc and, for --pdf/--deposit, a XeLaTeX executable path")
    catalog_path = SERIES / "publication_catalog.json"
    catalog_bytes = catalog_path.read_bytes()
    catalog = json.loads(catalog_bytes)
    global PUB
    if args.author_review:
        if args.deposit:
            parser.error("author-review builds cannot overwrite deposited package renderings")
        catalog = {**catalog, "publications": catalog["author_review_publications"], "status": "author-review; not deposited"}
        PUB = SERIES / "publication" / "author_review_2026_10_23"
    entries = publications(catalog)
    selected = {value.strip() for value in args.only.split(",") if value.strip()}
    sources = [e[key] for e in entries for key in ("source", "ledger")]
    sources += list((SERIES / "tools").glob("*.py")) + [SERIES / "tools/publication_header.tex", SERIES / "publication_catalog.json"]
    sources += [p for p in (SERIES / "verification").rglob("*") if p.is_file()]
    snapshots = {p: p.read_bytes() for p in sources}
    snapshots[catalog_path] = catalog_bytes
    before = {p: hashlib.sha256(data).hexdigest() for p, data in snapshots.items()}
    mapping = {e["source"].resolve(): PUB / e["id"] / "paper.pdf" for e in entries}
    mapping.update({(e["source"].parent / "README.md").resolve(): PUB / e["id"] / "README.md" for e in entries})
    mapping.update({e["ledger"].resolve(): PUB / e["id"] / "claim_ledger.md" for e in entries})
    support = []
    if args.author_review:
        excluded_names = {"paper.md", "paper.tex", "paper.pdf", "README.md", "MANIFEST.sha256", "SHA256SUMS", "build_receipt.json"}
        for entry in entries:
            for path in entry["source"].parent.rglob("*"):
                if not path.is_file() or path.suffix in {".zip", ".pyc", ".log"} or any(part in {"__pycache__", ".pytest_cache", ".lake"} for part in path.parts):
                    continue
                relative = path.relative_to(entry["source"].parent)
                if len(relative.parts) == 1 and (path.name in excluded_names or path == entry["ledger"]):
                    continue
                destination = PUB / entry["id"] / relative
                support.append((path, destination))
                mapping[path.resolve()] = destination
    for folder in (SERIES / "verification", SERIES / "tools"):
        if folder.exists():
            mapping.update({p.resolve(): p for p in folder.rglob("*") if p.is_file()})
    generated = []
    for source, destination in support:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        generated.append(destination)
    header = PUB / "tex_header.tex"
    write(header, snapshots[SERIES / "tools/publication_header.tex"].decode("utf-8"))
    generated.append(header)
    tools = {"pandoc": run([args.pandoc, "--version"]).splitlines()[0]}
    if args.pdf or args.deposit:
        tools["latex"] = run([args.latex, "--version"]).splitlines()[0]
    for entry in entries:
        number, source = entry["id"], entry["source"]
        if selected and number not in selected:
            continue
        # Deposit evidence is current package content, often added after the
        # historical code baseline. Keep its links beside the canonical package.
        entry_mapping = dict(mapping)
        for path in source.parent.rglob("*"):
            if path.is_file() and path.resolve().is_relative_to(source.parent.resolve()):
                entry_mapping.setdefault(path.resolve(), path)
        # A paper whose evidence postdates the collection baseline pins its own commit.
        base = entry.get("source_base", catalog["source_base"])
        bundle = PUB / number
        bundle.mkdir(parents=True, exist_ok=True)
        text = snapshots[source].decode("utf-8")
        title, author, meta = header_fields(text)
        author = author or catalog["author"]
        date = meta or f"{catalog['date']} — {entry['kind']} — author review"
        for src, name, original in [(source, "paper.md", "source.md"), (entry["ledger"], "claim_ledger.md", "claim_ledger.source.md")]:
            (bundle / original).write_bytes(snapshots[src])
            export_ast = json.loads(run([args.pandoc, "-f", SOURCE_FORMAT, "-t", "json"], text=snapshots[src].decode("utf-8")))
            export_ast = rewrite_links(export_ast, src, bundle / name, entry_mapping, base)
            rendered = run([args.pandoc, "-f", "json", "-t", SOURCE_FORMAT, "--wrap=auto"], text=json.dumps(export_ast))
            # Pandoc pads multiline-table cells; that padding is not content.
            rendered = "\n".join(line.rstrip() for line in rendered.splitlines()) + "\n"
            write(bundle / name, rendered)
            generated.extend([bundle / name, bundle / original])
        ast = rewrite_links(json.loads(run([args.pandoc, "-f", SOURCE_FORMAT, "-t", "json"], text=text)),
                            source, bundle / "paper.pdf", entry_mapping, base)
        write(bundle / "paper.tex", render_tex(args.pandoc, ast, header, title, author, date, base))
        generated.append(bundle / "paper.tex")
        receipt_path = bundle / "build_receipt.json"
        prior = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {}
        identity = {"source_sha256": before[source], "tex_sha256": sha(bundle / "paper.tex"), "ledger_sha256": before[entry["ledger"]], "markdown_sha256": sha(bundle / "paper.md"), "ledger_markdown_sha256": sha(bundle / "claim_ledger.md")}
        pdf = bundle / "paper.pdf"
        reusable = pdf.exists() and prior.get("tex_sha256") == identity["tex_sha256"] and prior.get("pdf_sha256") == sha(pdf)
        compiled_now = False
        if args.pdf and not reusable:
            write(bundle / "compile.log", compile_pdf(args.latex, bundle / "paper.tex", pdf))
            reusable, compiled_now = True, True
        if reusable:
            receipt = {**identity, "source_base": base, "source_path": source.relative_to(SERIES).as_posix(), "ledger_path": entry["ledger"].relative_to(SERIES).as_posix(), "pdf_sha256": sha(pdf), "compile_tools": tools if compiled_now else prior.get("compile_tools", prior.get("tools", {})), "render_tools": tools, "status": "compiled" if compiled_now else "reused_identical_tex"}
            write(receipt_path, json.dumps(receipt, sort_keys=True, indent=2) + "\n")
            generated.extend([pdf, receipt_path])
        write(bundle / "README.md", f"# {title}\n\nThis author-review package contains the standalone PDF and LaTeX, a linked\nMarkdown rendering (`paper.md`), and its claim ledger. `source.md` and\n`claim_ledger.source.md` preserve the exact repository Markdown bytes and retain\ntheir original repository-relative links. Use the linked renderings for reading.\n\nCode baseline: {base}. Revised source path:\n`{source.relative_to(REPO).as_posix()}`.\n\nBuild identities are in `build_receipt.json`; the collection manifest records\nall inputs and outputs. Related revised papers link to sibling packages; code\nand historical evidence link to the pinned repository. No deposit, DOI, or\nacceptance is claimed.\n")
        generated.append(bundle / "README.md")
        if args.author_review and (bundle / "verify_deposit.py").is_file():
            from refresh_draft_manifests import refresh
            ledger_alias = bundle / "paper_claim_ledger.md"
            ledger_alias.write_bytes(snapshots[entry["ledger"]])
            generated.append(ledger_alias)
            generated.extend(refresh(bundle))
        if args.deposit:
            deposit_ast = rewrite_deposit_links(json.loads(run([args.pandoc, "-f", SOURCE_FORMAT, "-t", "json"], text=text)), source, base)
            deposit_tex = source.with_suffix(".tex")
            write(deposit_tex, render_tex(args.pandoc, deposit_ast, header, title, author, date, base))
            compile_pdf(args.latex, deposit_tex, source.with_suffix(".pdf"))
        print(f"{number}: standalone source built; PDF {'current' if reusable else 'not built for this input'}"
              + ("; deposit TeX/PDF compiled" if args.deposit else ""), flush=True)
    if before != {p: sha(p) for p in sources}:
        raise RuntimeError("Source changed during build; rerun after edits finish")
    manifest_path = PUB / "manifest.json"
    prior_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() and selected else {}
    outputs = {**prior_manifest.get("outputs", {}), **{p.relative_to(SERIES).as_posix(): sha(p) for p in sorted(set(generated))}}
    manifest = {"schema": "pfp.publication-collection.v1", "source_base": catalog["source_base"], "status": catalog["status"], "tools": tools, "inputs": {p.relative_to(SERIES).as_posix(): digest for p, digest in sorted(before.items())}, "outputs": dict(sorted(outputs.items()))}
    write(manifest_path, json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
