"""Read-only severe-review inventory derived from the canonical A--I obligations.

Static checks establish their named predicates only. Semantic review and actual
execution stay NOT_VERIFIED; imported receipts never promote themselves to PASS.
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import lzma
import os
import re
import stat
import zipfile
import zlib
from collections import Counter
from pathlib import Path, PurePosixPath

import yaml

from omega_engine_research_papers.domain.rules.pandoc_build_rules import (
    describe_missing_glyphs,
    find_asterisk_list_items,
    find_md004_suppressions,
    parse_missing_glyphs,
)
from omega_engine_research_papers.use_cases.paper_iteration.paper_preflight import (
    gate_mechanism_inventory,
)

from omega_engine_research_papers.domain.models.republication_checklist import (
    get_checklist_catalog,
)

_catalog = get_checklist_catalog()
CATALOG_VERSION = _catalog.schema_version
SOURCE = _catalog.source
CATALOG = _catalog.to_catalog_tuple()
CACHES = set(_catalog.configuration.cache_directories)
MAX_FILE_BYTES = _catalog.configuration.max_file_bytes
MAX_PAYLOAD_BYTES = _catalog.configuration.max_payload_bytes
MAX_PATH_LENGTH = _catalog.configuration.max_path_length
REQUIRED_FILES = _catalog.configuration.required_files


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> str:
    if (
        not name
        or "\\" in name
        or ":" in name
        or PurePosixPath(name).is_absolute()
        or any(part in ("", ".", "..") for part in name.split("/"))
        or any(ord(char) < 32 for char in name)
    ):
        raise ValueError(f"unsafe path: {name!r}")
    return name


def regular(path: Path, directory: bool = False) -> None:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError(f"symlink or reparse point: {path}")
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise ValueError(f"nonregular path: {path}")


def snapshot(root: Path) -> dict[str, bytes]:
    regular(root, directory=True)
    files: dict[str, bytes] = {}
    total = 0

    def walk_error(error: OSError) -> None:
        raise error

    for current, directories, names in os.walk(root, followlinks=False, onerror=walk_error):
        folder = Path(current)
        for name in directories:
            regular(folder / name, directory=True)
        directories[:] = [
            name
            for name in directories
            if name not in CACHES
            and not name.endswith(".egg-info")
            and (folder / name).relative_to(root).as_posix() != "lean4/b"
        ]
        for name in names:
            path = folder / name
            regular(path)
            if name in (".coverage", ".env") or name.startswith(".coverage."):
                continue
            relative = safe_name(path.relative_to(root).as_posix())
            size = path.stat().st_size
            total += size
            if size > MAX_FILE_BYTES or total > MAX_PAYLOAD_BYTES:
                raise ValueError("snapshot byte limit exceeded; no partial PASS is permitted")
            with path.open("rb") as stream:
                data = stream.read(MAX_FILE_BYTES + 1)
            if len(data) != size:
                raise ValueError(f"file changed while reading: {relative}")
            files[relative] = data
    return dict(sorted(files.items(), key=lambda pair: pair[0].encode("utf-8")))


def identity(files: dict[str, bytes]) -> tuple[str, list[dict]]:
    rows = [
        {"path": name, "bytes": len(data), "sha256": digest(data)} for name, data in files.items()
    ]
    encoded = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return digest(encoded), rows


def checksums(data: bytes) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in data.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError("malformed checksum entry")
        checksum, name = match.groups()
        safe_name(name)
        if name in rows:
            raise ValueError(f"duplicate checksum entry: {name}")
        rows[name] = checksum
    if not rows or list(rows) != sorted(rows, key=lambda name: name.encode("utf-8")):
        raise ValueError("empty or unsorted checksum manifest")
    return rows


def _normalize(text: str) -> str:
    return "".join(char.casefold() for char in text if char.isalnum())


def _multiline(value: object) -> bool:
    return (
        isinstance(value, str)
        or isinstance(value, list)
        and all(isinstance(line, str) for line in value)
    )


def _stored_output(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    kind = value.get("output_type")
    if kind == "stream":
        return value.get("name") in ("stdout", "stderr") and _multiline(value.get("text"))
    if kind not in ("display_data", "execute_result"):
        return False
    if not isinstance(value.get("data"), dict) or not isinstance(value.get("metadata"), dict):
        return False
    return (
        kind != "execute_result"
        or type(value.get("execution_count")) is int
        and value["execution_count"] > 0
    )


def audit(root: Path, monograph: Path, evidence_path: Path | None = None) -> dict:
    root = root.absolute()
    results = {
        key: {
            "id": key,
            "channel": key[0],
            "method": method,
            "requirement": description,
            "source": SOURCE + "#required-evidence-channels",
            "status": "NOT_VERIFIED",
            "detail": f"Requires independent {method} evidence; file presence or a claimed PASS is insufficient.",
        }
        for key, method, description in CATALOG
    }

    def result(key: str, condition: bool, detail: str) -> None:
        results[key].update(status="PASS" if condition else "FAIL", detail=detail)

    try:
        files = snapshot(root)
        main = monograph.absolute().relative_to(root).as_posix()
        safe_name(main)
    except (OSError, ValueError) as error:
        result("A01", False, str(error))
        return _receipt(results, "", [], [], [str(error)])
    snapshot_sha, rows = identity(files)
    text = {
        name: data.decode("utf-8", errors="replace")
        for name, data in files.items()
        if name.endswith((".md", ".py", ".lean", ".tex", ".cff", ".toml", ".txt"))
    }
    prose = "\n".join(value for name, value in text.items() if name.endswith(".md"))
    stem = str(PurePosixPath(main).with_suffix(""))
    metadata: dict = {}
    ledgers = [name for name in files if name.endswith("_claim_ledger.md")]
    inventory = "## Mechanism inventory" in text.get(main, "") and not gate_mechanism_inventory(
        monograph, text.get(main, ""), strict=True
    )
    notebooks = [name for name in files if name.endswith(".ipynb")]
    python_files = [name for name in files if name.endswith(".py")]
    lean_files = [name for name in files if name.endswith(".lean")]
    tests = [
        name
        for name in python_files
        if name.startswith("code/") and PurePosixPath(name).name.startswith("test_")
    ]
    result(
        "A01",
        True,
        "Snapshot contains only regular files with canonical relative names; cache directories were pruned before descent.",
    )
    def _nominal_path_len(relative_name: str) -> int:
        return len(str(Path(r"C:\the_symbol_game") / relative_name))

    result(
        "A02",
        all(_nominal_path_len(name) <= MAX_PATH_LENGTH for name in files),
        f"All audited absolute paths must fit {MAX_PATH_LENGTH} characters.",
    )
    required = (main, *REQUIRED_FILES)
    missing = [name for name in required if not files.get(name)]
    result(
        "A03",
        not missing
        and (len(ledgers) == 1 or (not ledgers and inventory))
        and any(name.endswith("_change_log.md") for name in files),
        f"Missing/empty required files: {missing}; scoped inventory: {inventory}; "
        f"legacy claim ledgers: {len(ledgers)}; change log required.",
    )
    archives = [name for name in files if name.lower().endswith(".zip")]
    payload = set(files) - set(archives) - {"MANIFEST.sha256", "SHA256SUMS"}
    try:
        manifest = checksums(files["MANIFEST.sha256"])
        sums = checksums(files["SHA256SUMS"])
        result(
            "A04",
            set(manifest) == payload and set(sums) == payload | {"MANIFEST.sha256"},
            "Compared both complete file sets with the actual snapshot.",
        )
        bad = [
            name
            for table in (manifest, sums)
            for name, checksum in table.items()
            if name not in files or digest(files[name]) != checksum
        ]
        result("A05", not bad, f"Checksum mismatches or missing files: {bad}")
        result(
            "A06",
            not (set(manifest) & {"MANIFEST.sha256", "SHA256SUMS", *archives})
            and not (set(sums) & {"SHA256SUMS", *archives}),
            "No self-reference or release ZIP is checksum payload.",
        )
    except (KeyError, UnicodeError, ValueError) as error:
        for key in ("A04", "A05", "A06"):
            result(key, False, str(error))
    if not archives:
        results["A07"].update(
            status="NOT_APPLICABLE",
            detail="No outer ZIP is present; an extracted package can still verify its payload.",
        )
    else:
        try:
            if len(archives) != 1 or "/" in archives[0]:
                raise ValueError("expected at most one root release ZIP; unexpected ZIP payload")
            with zipfile.ZipFile(io.BytesIO(files[archives[0]])) as archive:
                names = archive.namelist()
                if len(names) != len(set(names)):
                    raise ValueError("duplicate ZIP member")
                members = {}
                prefixes = set()
                for info in archive.infolist():
                    safe_name(info.filename)
                    prefix, slash, member = info.filename.partition("/")
                    if (
                        not slash
                        or not member
                        or info.create_system != 3
                        or not stat.S_ISREG(info.external_attr >> 16)
                    ):
                        raise ValueError("ZIP member must be a Unix regular file below one root")
                    prefixes.add(prefix)
                    if member not in files or info.file_size != len(files[member]):
                        raise ValueError(f"unexpected ZIP member/size: {member}")
                    members[member] = archive.read(info)
                expected = {name: data for name, data in files.items() if name not in archives}
                result(
                    "A07",
                    len(prefixes) == 1 and members == expected,
                    "Compared unique regular ZIP member names, sizes and every byte with current payload.",
                )
        except (
            OSError,
            ValueError,
            RuntimeError,
            EOFError,
            zlib.error,
            lzma.LZMAError,
            zipfile.BadZipFile,
        ) as error:
            result("A07", False, str(error))
    try:
        metadata = json.loads(files["zenodo_metadata.json"])
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a JSON object")
        version, date = metadata.get("version"), metadata.get("publication_date")
        tokens = [text.get(main, ""), text.get("README.md", "")]
        consistent = isinstance(version, str) and isinstance(date, str) and bool(version and date)
        consistent = consistent and all(version in value and date in value for value in tokens)
        for name, field, expected in (
            ("CITATION.cff", "version", version),
            ("CITATION.cff", "date-released", date),
            ("pyproject.toml", "version", version),
        ):
            if name in text:
                found = re.search(rf"(?m)^{field}\s*[:=]\s*[\"\x27]?([^\"\x27\n]+)", text[name])
                consistent = consistent and found is not None and found.group(1).strip() == expected
        cff_text = text.get("CITATION.cff", "")
        if cff_text:
            cff_type_match = re.search(r"(?m)^type\s*:\s*(\S+)", cff_text)
            if cff_type_match:
                cff_type = cff_type_match.group(1).strip().strip('"').strip("'")
                consistent = consistent and (cff_type in ("software", "dataset"))
        result(
            "A08",
            bool(consistent),
            "Compared metadata version/date with manuscript, README and available citation/project versions.",
        )
    except (KeyError, UnicodeError, ValueError, TypeError, RecursionError) as error:
        result("A08", False, str(error))
        metadata = {}
    raw_pdf_text = ""
    try:
        import pymupdf

        with pymupdf.open(stream=files[stem + ".pdf"], filetype="pdf") as pdf:
            result(
                "C01",
                len(pdf) > 0 and not pdf.needs_pass,
                f"Parsed {len(pdf)} PDF pages; no visual judgment inferred.",
            )
            raw_pdf_text = " ".join(page.get_text() for page in pdf)
            pdf_text = _normalize(raw_pdf_text)
            fields = [metadata.get(key) for key in ("title", "version", "publication_date")]
            # Dehyphenate soft line breaks before searching for Lean references
            dehyphenated_pdf_text = re.sub(r"-\s*\n\s*", "", raw_pdf_text)
            pdf_lean_refs = set(re.findall(r"\b([A-Za-z0-9_]+\.lean)\b", dehyphenated_pdf_text))
            lean_filenames = {PurePosixPath(name).name for name in lean_files}
            stale_lean_refs = pdf_lean_refs - lean_filenames if lean_filenames else set()

            # Check for unexpanded alert tags in PDF text
            unexpanded_alerts = re.findall(r"\[!(?:CAUTION|NOTE|WARNING|TIP|IMPORTANT)\]", raw_pdf_text)
            # Check for authority effect in PDF text
            has_authority_effect = "authorityeffect" in _normalize(raw_pdf_text)
            # Check for conflicting versions on title page / first page of PDF text
            first_page_text = pdf[0].get_text() if len(pdf) > 0 else raw_pdf_text
            first_page_versions = set(re.findall(r"(?:version\s*[:\s—\-]+|v)(\d+\.\d+\.\d+)", first_page_text, re.IGNORECASE))
            declared_version = metadata.get("version")
            conflicting_versions = {
                v
                for v in first_page_versions
                if declared_version
                and v != declared_version
                and v != declared_version.lstrip("v")
            }

            c02_reasons = []
            if stale_lean_refs:
                c02_reasons.append(f"references nonexistent Lean files: {', '.join(sorted(stale_lean_refs))}")
            if unexpanded_alerts:
                c02_reasons.append(f"contains unexpanded markdown alert syntax: {', '.join(sorted(set(unexpanded_alerts)))}")
            if has_authority_effect:
                c02_reasons.append("contains reader-facing AuthorityEffect dialect")
            if conflicting_versions:
                c02_reasons.append(f"contains conflicting version strings: {', '.join(sorted(conflicting_versions))}")

            c02_ok = (
                all(
                    isinstance(value, str) and value and _normalize(value) in pdf_text
                    for value in fields
                )
                and not c02_reasons
            )
            c02_detail = (
                f"PDF text defect: {'; '.join(c02_reasons)}"
                if c02_reasons
                else "Compared normalized title/version/date with extracted PDF text; layout remains a review obligation."
            )
            result("C02", c02_ok, c02_detail)
    except ImportError:
        for key in ("C01", "C02"):
            results[key]["detail"] = (
                "PyMuPDF is unavailable; PDF parsing/text comparison was not run."
            )
    except (KeyError, ValueError, RuntimeError) as error:
        result("C01", False, f"PDF missing/unreadable: {error}")
    tex_source = text.get(stem + ".tex", "")
    # The text map skips .log files, so read the TeX log from the raw snapshot.
    tex_log = files.get(stem + ".log", b"").decode("utf-8", errors="replace")
    has_overfull = bool(tex_log and "Overfull \\hbox" in tex_log)

    bare_urls_found: dict[str, list[str]] = {}
    md034_disabled: list[str] = []
    asterisk_lists_found: dict[str, list[str]] = {}
    md004_disabled: list[str] = []
    for name, data in files.items():
        if name.endswith(".md"):
            content = data.decode("utf-8", errors="replace")
            if re.search(r"<!--\s*markdownlint-(?:disable|capture)[\s\S]*?\bMD034\b", content):
                md034_disabled.append(name)
            md004_hits = find_md004_suppressions(content)
            if md004_hits:
                md004_disabled.append(name)
            ast_hits = find_asterisk_list_items(content)
            if ast_hits:
                asterisk_lists_found[name] = [f"L{line}: {item[:30]}" for line, item in ast_hits[:3]]
            stripped = re.sub(r"```[\s\S]*?```", "", content)
            stripped = re.sub(r"`[^`\n]+`", "", stripped)
            stripped = re.sub(r"!\[[^\]]*\]\([^\)]+\)", "", stripped)
            stripped = re.sub(r"\[[^\]]*\]\([^\)]+\)", "", stripped)
            stripped = re.sub(r"<https?://[^>]+>", "", stripped)
            stripped = re.sub(r"^\s*\[[^\]]+\]:\s*https?://\S+", "", stripped, flags=re.M)
            bare = re.findall(r"https?://[^\s>\)]+", stripped)
            if bare:
                bare_urls_found[name] = bare[:3]
        elif PurePosixPath(name).name in (".markdownlint.json", ".markdownlint.jsonc"):
            content = data.decode("utf-8", errors="replace")
            if re.search(r'"(?:MD034|no-bare-urls)"\s*:\s*false', content):
                md034_disabled.append(name)
            if re.search(r'"(?:MD004|ul-style)"\s*:\s*false', content) or re.search(
                r'"style"\s*:\s*"(?:asterisk|consistent|sublist)"', content
            ):
                md004_disabled.append(name)

    c03_reasons = []
    if not files.get(stem + ".tex"):
        c03_reasons.append("TeX source missing")
    clean_tex = re.sub(r"(?m)%.*$", "", tex_source)
    if r"\maketitle" in clean_tex:
        c03_reasons.append(r"contains generated \maketitle block")
    if has_overfull:
        overfull_count = tex_log.count("Overfull \\hbox")
        c03_reasons.append(f"Overfull \\hbox ({overfull_count} warnings) detected in TeX log; layout clipping defect")
    missing_glyphs = parse_missing_glyphs(tex_log) if tex_log else {}
    if missing_glyphs:
        c03_reasons.append(f"TeX log reports glyphs dropped from the PDF: {describe_missing_glyphs(missing_glyphs)}")
    if bare_urls_found:
        c03_reasons.append(f"bare URLs violating MD034 in {list(bare_urls_found.keys())}")
    if md034_disabled:
        c03_reasons.append(f"MD034 disabled/ignored in {md034_disabled}")
    if asterisk_lists_found:
        c03_reasons.append(f"asterisk list style violating MD004 in {list(asterisk_lists_found.keys())} (expected dash '-')")
    if md004_disabled:
        c03_reasons.append(f"MD004 disabled/ignored in {md004_disabled}")

    c03_ok = not c03_reasons
    c03_detail = (
        f"TeX/Markdown defect: {'; '.join(c03_reasons)}"
        if c03_reasons
        else "TeX presence, title-command, missing-glyph log, and Markdown MD004/MD034 checks passed."
    )
    result(
        "C03",
        c03_ok,
        c03_detail,
    )
    ledger = text.get(ledgers[0], "") if len(ledgers) == 1 else ""
    ids = []
    in_claim_table = False
    id_col = 0
    for line in ledger.splitlines():
        if not line.startswith("|"):
            in_claim_table = False
            continue
        cells = [c.strip().strip("*") for c in line.strip("|").split("|")]
        if not cells:
            continue
        if any(c.casefold() in {"id", "claim id"} for c in cells[:2]):
            in_claim_table = True
            id_col = 0 if cells[0].casefold() in {"id", "claim id"} else 1
            continue
        if in_claim_table and len(cells) > id_col:
            target_cell = cells[id_col]
            target_link = re.fullmatch(r"\[([^\]]+)\]\([^)]+\)", target_cell)
            if target_link is not None:
                target_cell = target_link.group(1)
            if re.fullmatch(r"(?:C[0-9]+|[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)", target_cell):
                ids.append(target_cell)
    loose_dual_box = bool(
        re.search(
            r"[Dd]ual\s+box\s+constraint[^\n]*\\\|z\\\|_\\infty\s*\\le\s*\\max",
            ledger,
        )
    )
    d01_ok = bool(ids) and len(ids) == len(set(ids)) and not loose_dual_box
    d01_reasons = []
    if loose_dual_box:
        d01_reasons.append(
            "Claim ledger specifies loose uniform bound ||z||_\\infty <= max_i w_i as dual box constraint (coordinatewise |z_i| <= w_i required under nonuniform weights)."
        )
    d01_detail = (
        " ".join(d01_reasons)
        if d01_reasons
        else f"{len(ids)} ledger identifiers; checked nonempty uniqueness."
    )
    result("D01", d01_ok, d01_detail)
    if not ledgers and inventory:
        results["D01"].update(
            status="NOT_APPLICABLE",
            detail="Public claim ledgers are retired; the manuscript has a validated mechanism inventory. "
                   "Semantic claim/evidence correspondence remains independently unverified in D02 and D04.",
        )
    try:
        references = re.findall(r"(test_[A-Za-z0-9_]+\.py)::(test_[A-Za-z0-9_]+)",
                                ledger if ledgers else prose)
        missing_refs = []
        for filename, function in references:
            candidates = [name for name in tests if PurePosixPath(name).name == filename]
            if len(candidates) != 1:
                missing_refs.append(f"{filename}::{function}")
                continue
            parsed_tree = ast.parse(text[candidates[0]])
            discoverable: set[str] = set()
            for node in parsed_tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    discoverable.add(node.name)
                elif isinstance(node, ast.ClassDef) and (node.name.startswith("Test") or not node.name.startswith("test")):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            discoverable.add(item.name)
            if function not in discoverable:
                missing_refs.append(f"{filename}::{function}")
        result(
            "D03",
            not missing_refs and (bool(references) or not python_files),
            f"Unresolved pytest references: {missing_refs}; inspected {len(references)} references.",
        )
        if not references and not ledgers and inventory:
            results["D03"].update(
                status="NOT_APPLICABLE",
                detail="The manuscript makes no explicit file::test references; actual test execution remains E02.",
            )
    except (SyntaxError, ValueError, RecursionError) as error:
        result("D03", False, str(error))
    result(
        "E01",
        bool(tests) and not any(name.startswith("tests/") for name in files),
        f"{len(tests)} named test files under code/tests; no execution inferred.",
    )
    try:
        prohibited = []
        for name in tests:
            tree = ast.parse(text[name])
            for node in ast.walk(tree):
                imports = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                    if isinstance(node, ast.ImportFrom)
                    else []
                )
                if any(value.split(".")[0] in ("nbclient", "nbconvert") for value in imports):
                    prohibited.append(name)
        result(
            "E07",
            not prohibited,
            f"Direct notebook-client imports in test sources: {sorted(set(prohibited))}; dynamic imports require review.",
        )
    except (SyntaxError, ValueError, RecursionError) as error:
        result("E07", False, str(error))
    pyproject_text = text.get("pyproject.toml", "")
    blanket_mypy = False
    if "[tool.mypy]" in pyproject_text:
        mypy_sec = pyproject_text.split("[tool.mypy]", 1)[1].split("[[", 1)[0]
        if re.search(r"ignore_missing_imports\s*=\s*true", mypy_sec, re.I):
            blanket_mypy = True
    if blanket_mypy:
        result(
            "E06",
            False,
            "pyproject.toml specifies global ignore_missing_imports = true under [tool.mypy]; blanket missing-import ignoring masks broken dependencies and untyped interfaces.",
        )
    try:

        parsed = [json.loads(files[name]) for name in notebooks]
        valid = bool(parsed) and all(
            isinstance(nb, dict)
            and nb.get("nbformat") == 4
            and isinstance(nb.get("cells"), list)
            and all(
                isinstance(cell, dict)
                and cell.get("cell_type") in ("code", "markdown", "raw")
                and _multiline(cell.get("source"))
                for cell in nb["cells"]
            )
            for nb in parsed
        )
        result("F01", valid, f"Validated stored JSON structure for {len(parsed)} notebooks.")
        if valid:
            cells = [cell for nb in parsed for cell in nb["cells"] if cell["cell_type"] == "code"]
            result(
                "F02",
                bool(cells)
                and all(
                    type(cell.get("execution_count")) is int
                    and cell["execution_count"] > 0
                    and isinstance(cell.get("outputs"), list)
                    and all(_stored_output(output) for output in cell["outputs"])
                    for cell in cells
                ),
                f"Inspected {len(cells)} stored code cells; fresh execution remains unverified by this static check.",
            )
            source = "\n".join("".join(cell["source"]) for cell in cells)
            result(
                "F04",
                not re.search(r"[A-Za-z]:[\\/](?:Users|source|home)[\\/]|/(?:home|Users)/", source),
                "Searched code cells for machine-specific absolute user paths; portability still needs extraction replay.",
            )
    except (ValueError, TypeError, RecursionError) as error:
        result("F01", False, str(error))
    configurations = [
        name for name in files if PurePosixPath(name).name in ("lakefile.lean", "lakefile.toml")
    ]
    result(
        "G01",
        len(configurations) == 1
        and configurations[0] in ("lean4/lakefile.lean", "lean4/lakefile.toml"),
        f"Local Lake configurations: {configurations}",
    )
    pin = files.get("lean4/lean-toolchain", b"").decode("utf-8", errors="replace").strip()
    result(
        "G02",
        bool(
            re.fullmatch(
                r"leanprover/lean4:(?:v\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?|[0-9a-f]{40})", pin
            )
        ),
        f"Pinned toolchain: {pin!r}",
    )
    escapes = []
    for name in lean_files:
        body = re.sub(r"/\-.*?\-/", "", text[name], flags=re.S)
        body = re.sub(r"--[^\n]*", "", body)
        if re.search(r"\b(?:sorry|admit|unsafe)\b|(?m:^\s*(?:axiom|constant)\s)", body):
            escapes.append(name)
    result(
        "G03",
        bool(lean_files) and not escapes,
        f"Potential proof escape hatches: {escapes}; lexical scan is not a kernel check.",
    )
    census = text.get("lean4/axiom_report.txt", "")
    result(
        "G05",
        bool(census.strip()) and not re.search(r"windows-gnu|linux-gnu|darwin", census),
        "Checked report presence and absence of target triples; actual build/census provenance remains a separate obligation.",
    )
    doc_manifest_retired = False
    if "MANIFEST.sha256" in files:
        for doc_name in ("README.md", stem + "_change_log.md"):
            doc_text = text.get(doc_name, "")
            if re.search(r"[Rr]etired[^\n]*MANIFEST\.sha256", doc_text):
                doc_manifest_retired = True
                break
    h01_ok = (
        bool(
            re.search(
                r"\b(?:verify_deposit|pytest|lake build)\b",
                text.get("README.md", ""),
            )
        )
        and not doc_manifest_retired
    )
    h01_detail = (
        "Documentation claims MANIFEST.sha256 was retired, but MANIFEST.sha256 is present in release payload."
        if doc_manifest_retired
        else "README contains a local verification command; execution and completeness require replay."
    )
    result("H01", h01_ok, h01_detail)
    forbidden = [
        name
        for name, data in files.items()
        if name.endswith(".gitkeep")
        or any(
            word in name.lower()
            for word in ("bulgakov", "oldman", "nonclaims.md", "mutation_audit.md")
        )
        or name.split("/")[0] in ("evidence", "reconstruction_v1", "dist", "rt")
    ]
    result(
        "H05", not forbidden, f"Internal dossier/placeholder/forbidden envelope paths: {forbidden}"
    )
    creators = metadata.get("creators")
    result(
        "I01",
        all(
            isinstance(metadata.get(key), str) and metadata[key].strip()
            for key in (
                "title",
                "version",
                "publication_date",
                "description",
                "license",
                "upload_type",
            )
        )
        and isinstance(creators, list)
        and bool(creators)
        and all(
            isinstance(creator, dict)
            and isinstance(creator.get("name"), str)
            and creator["name"].strip()
            for creator in creators
        ),
        "Required identity fields and named creators exist; external record identity is not inferred.",
    )
    result(
        "I02",
        bool(files.get("LICENSE")) and (not python_files or bool(files.get("LICENSE-CODE"))),
        "License artifacts exist; no legal or external authorization judgment is inferred.",
    )
    # Absence alone cannot waive a claimed evidence channel.
    scope_text = (
        prose
        + "\n"
        + json.dumps(metadata, ensure_ascii=False)
        + "\n"
        + text.get(stem + ".tex", "")
        + "\n"
        + raw_pdf_text
    )
    scopes = [
        ("E", python_files, r"\b(?:Python|pytest|computational|executable)\b"),
        ("F", notebooks, r"\bnotebooks?\b"),
        ("G", lean_files, r"\bLean\b"),
    ]
    for channel, present, claim in scopes:
        if not present and not re.search(claim, scope_text, re.I):
            for key in results:
                if key.startswith(channel):
                    results[key].update(
                        status="NOT_APPLICABLE",
                        detail="No corresponding artifacts or explicit claims were found; this is a scoped applicability decision.",
                    )
    recorded, evidence_errors = _evidence(evidence_path, snapshot_sha, results)
    try:
        after_sha, _ = identity(snapshot(root))
        result(
            "H04",
            after_sha == snapshot_sha,
            "Recomputed complete snapshot after inspection; compared path/size/digest identity.",
        )
    except (OSError, ValueError) as error:
        result("H04", False, str(error))
    return _receipt(results, snapshot_sha, rows, recorded, evidence_errors)


def _evidence(path: Path | None, snapshot_sha: str, results: dict) -> tuple[list, list]:
    """Bind selected external evidence bytes without trusting their PASS fields."""
    if path is None:
        return [], []
    records, errors = [], []
    try:
        regular(path)
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("evidence bundle exceeds byte limit")
        with path.open("rb") as stream:
            bundle_bytes = stream.read(MAX_FILE_BYTES + 1)
        if len(bundle_bytes) > MAX_FILE_BYTES:
            raise ValueError("evidence bundle exceeds byte limit")
        bundle = json.loads(bundle_bytes)
        if (
            bundle.get("schema") != "omega.paper_review.evidence.v1"
            or bundle.get("snapshot_sha256") != snapshot_sha
        ):
            raise ValueError("evidence schema or snapshot digest mismatch")
        seen = set()
        for entry in bundle["records"]:
            key = entry["check_id"]
            relative = safe_name(entry["path"])
            if key not in results or (key, relative) in seen:
                raise ValueError("unknown or duplicate evidence record")
            seen.add((key, relative))
            target = path.parent / relative
            for parent in reversed(target.parents):
                if parent == path.parent or path.parent in parent.parents:
                    regular(parent, directory=True)
            regular(target)
            if target.stat().st_size > MAX_FILE_BYTES:
                raise ValueError("evidence file exceeds byte limit")
            with target.open("rb") as stream:
                evidence_bytes = stream.read(MAX_FILE_BYTES + 1)
            if len(evidence_bytes) > MAX_FILE_BYTES or digest(evidence_bytes) != entry["sha256"]:
                raise ValueError(f"evidence digest mismatch: {relative}")
            record = {
                "check_id": key,
                "path": str(target.absolute()),
                "sha256": entry["sha256"],
                "status": "RECORDED_PROVENANCE_ONLY",
            }
            records.append(record)
            results[key].setdefault("recorded_evidence", []).append(record)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError) as error:
        errors.append(f"Invalid external evidence: {error}")
    return records, errors


def _receipt(results: dict, snapshot_sha: str, rows: list, recorded: list, errors: list) -> dict:
    counts = dict(Counter(row["status"] for row in results.values()))
    complete = (
        all(row["status"] in ("PASS", "NOT_APPLICABLE") for row in results.values()) and not errors
    )
    return {
        "catalog_version": CATALOG_VERSION,
        "catalog_origin": "new enumeration derived from canonical A-I obligations",
        "snapshot_sha256": snapshot_sha,
        "files": rows,
        "checks": list(results.values()),
        "counts": counts,
        "recorded_evidence": recorded,
        "errors": errors,
        "status": "PASS" if complete else "BLOCKED",
        "verdict": "READY FOR ZENODO REPUBLICATION"
        if complete
        else "NOT READY FOR ZENODO REPUBLICATION",
        "authority_effect": "None",
        "limitations": [
            "Static PASS establishes only its named predicate.",
            "Imported reports and PASS fields are provenance, never independently verified execution or proof.",
            "Semantic, execution and authorization obligations need separate independent assessment.",
        ],
    }
