"""Package auditor executing Stage Omega Canonical Severe Zenodo Republication Gate.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
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
from typing import Any, Dict, List, Optional, Set, Tuple

from ...domain.models.republication_checklist import (
    CATALOG_ORIGIN,
    CATALOG_VERSION,
    REPUBLICATION_CATALOG,
    RepublicationCheckItem,
    RepublicationGateReceipt,
)
from ...domain.rules.pandoc_build_rules import (
    describe_missing_glyphs,
    find_asterisk_list_items,
    find_md004_suppressions,
    parse_missing_glyphs,
)
from .utils import (
    MAX_FILE_BYTES,
    SOURCE_REF,
    _checksums,
    _digest,
    _identity,
    _normalize,
    _regular,
    _safe_name,
    _snapshot,
    _stored_output,
    resolve_paper_paths,
)


def audit_paper_package(
        paper_dir: Path | str,
        monograph_path: Optional[Path | str] = None,
        evidence_path: Optional[Path | str] = None,
    ) -> RepublicationGateReceipt:
        """Execute Stage Ω Canonical Severe Zenodo Republication Gate on disk bytes."""
        root, monograph = (
            resolve_paper_paths(paper_dir)
            if monograph_path is None
            else (Path(paper_dir).resolve(), Path(monograph_path).resolve())
        )
        root = root.absolute()
        ev_path = Path(evidence_path).resolve() if evidence_path else None

        results: Dict[str, Dict[str, Any]] = {
            key: {
                "id": key,
                "channel": key[0],
                "method": method,
                "requirement": description,
                "source": SOURCE_REF + "#required-evidence-channels",
                "status": "NOT_VERIFIED",
                "detail": f"Requires independent {method} evidence; file presence or a claimed PASS is insufficient.",
            }
            for key, method, description in REPUBLICATION_CATALOG
        }

        def set_result(key: str, condition: bool, detail: str) -> None:
            results[key].update(status="PASS" if condition else "FAIL", detail=detail)

        try:
            files = _snapshot(root)
            main = monograph.absolute().relative_to(root).as_posix()
            _safe_name(main)
        except (OSError, ValueError) as error:
            set_result("A01", False, str(error))
            receipt_errs = [str(error)]
            items = [RepublicationCheckItem(**v) for v in results.values()]
            counts = dict(Counter(it.status for it in items))
            return RepublicationGateReceipt(
                catalog_version=CATALOG_VERSION,
                catalog_origin=CATALOG_ORIGIN,
                snapshot_sha256="",
                paper_path=str(root),
                monograph_path=str(monograph),
                files=[],
                checks=items,
                counts=counts,
                recorded_evidence=[],
                errors=receipt_errs,
                status="BLOCKED",
                verdict="NOT READY FOR ZENODO REPUBLICATION",
                authority_effect="None",
            )

        snapshot_sha, rows = _identity(files)
        text = {
            name: data.decode("utf-8", errors="replace")
            for name, data in files.items()
            if name.endswith((".md", ".py", ".lean", ".tex", ".cff", ".toml", ".txt"))
        }
        prose = "\n".join(value for name, value in text.items() if name.endswith(".md"))
        stem = str(PurePosixPath(main).with_suffix(""))
        metadata: Dict[str, Any] = {}
        ledgers = [name for name in files if name.endswith("_claim_ledger.md")]
        notebooks = [name for name in files if name.endswith(".ipynb")]
        python_files = [name for name in files if name.endswith(".py")]
        lean_files = [name for name in files if name.endswith(".lean")]
        tests = [
            name
            for name in python_files
            if name.startswith("code/tests/") and PurePosixPath(name).name.startswith("test_")
        ]

        # A01: Regular files & safe names
        set_result(
            "A01",
            True,
            "Snapshot contains only regular files with canonical relative names; cache directories were pruned before descent.",
        )

        # A02: Win32 MAX_PATH depth <= 250
        def _nominal_path_len(relative_name: str) -> int:
            return len(str(Path(r"C:\the_symbol_game") / relative_name))

        set_result(
            "A02",
            all(_nominal_path_len(name) <= 250 for name in files),
            "All audited absolute paths must fit 250 characters.",
        )

        # A03: Canonical manuscript & release companions exist
        required = (
            main,
            "README.md",
            "LICENSE",
            "MANIFEST.sha256",
            "SHA256SUMS",
            "zenodo_metadata.json",
        )
        missing = [name for name in required if not files.get(name)]
        set_result(
            "A03",
            not missing
            and len(ledgers) == 1
            and any(name.endswith("_change_log.md") for name in files),
            f"Missing/empty required files: {missing}; claim ledgers: {len(ledgers)}; change log required.",
        )

        # A04 - A06: Manifest two-way agreement and checksum verification
        archives = [name for name in files if name.lower().endswith(".zip")]
        payload = set(files) - set(archives) - {"MANIFEST.sha256", "SHA256SUMS"}
        try:
            manifest = _checksums(files["MANIFEST.sha256"])
            sums = _checksums(files["SHA256SUMS"])
            set_result(
                "A04",
                set(manifest) == payload and set(sums) == payload | {"MANIFEST.sha256"},
                "Compared both complete file sets with the actual snapshot.",
            )
            bad = [
                name
                for table in (manifest, sums)
                for name, checksum in table.items()
                if name not in files or _digest(files[name]) != checksum
            ]
            set_result("A05", not bad, f"Checksum mismatches or missing files: {bad}")
            set_result(
                "A06",
                not (set(manifest) & {"MANIFEST.sha256", "SHA256SUMS", *archives})
                and not (set(sums) & {"SHA256SUMS", *archives}),
                "No self-reference or release ZIP is checksum payload.",
            )
        except (KeyError, UnicodeError, ValueError) as error:
            for key in ("A04", "A05", "A06"):
                set_result(key, False, str(error))

        # A07: ZIP members are unique regular files below one root
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
                        _safe_name(info.filename)
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
                    set_result(
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
                set_result("A07", False, str(error))

        # A08: Declared release version & date agreement
        try:
            metadata = json.loads(files["zenodo_metadata.json"])
            if not isinstance(metadata, dict):
                raise ValueError("metadata must be a JSON object")
            v_raw, d_raw = metadata.get("version"), metadata.get("publication_date")
            if isinstance(v_raw, str) and isinstance(d_raw, str) and v_raw and d_raw:
                version: str = v_raw
                date: str = d_raw
                tokens = [text.get(main, ""), text.get("README.md", "")]
                consistent = all(version in value and date in value for value in tokens)
                for name, field, expected_val in (
                    ("CITATION.cff", "version", version),
                    ("CITATION.cff", "date-released", date),
                    ("pyproject.toml", "version", version),
                ):
                    if name in text:
                        found = re.search(rf"(?m)^{field}\s*[:=]\s*[\"\x27]?([^\"\x27\n]+)", text[name])
                        consistent = consistent and found is not None and found.group(1).strip() == expected_val
            else:
                consistent = False
            cff_text = text.get("CITATION.cff", "")
            if cff_text:
                cff_type_match = re.search(r"(?m)^type\s*:\s*(\S+)", cff_text)
                if cff_type_match:
                    cff_type = cff_type_match.group(1).strip().strip('"').strip("'")
                    consistent = consistent and (cff_type in ("software", "dataset"))
            set_result(
                "A08",
                bool(consistent),
                "Compared metadata version/date with manuscript, README and available citation/project versions.",
            )
        except (KeyError, UnicodeError, ValueError, TypeError, RecursionError) as error:
            set_result("A08", False, str(error))
            metadata = {}

        # C01 - C02: PDF text parsing & hygiene checks
        raw_pdf_text = ""
        try:
            import pymupdf  # type: ignore

            with pymupdf.open(stream=files[stem + ".pdf"], filetype="pdf") as pdf:
                set_result(
                    "C01",
                    len(pdf) > 0 and not pdf.needs_pass,
                    f"Parsed {len(pdf)} PDF pages; no visual judgment inferred.",
                )
                raw_pdf_text = " ".join(page.get_text() for page in pdf)
                pdf_text = _normalize(raw_pdf_text)
                fields = [metadata.get(k) for k in ("title", "version", "publication_date")]
                pdf_lean_refs = set(re.findall(r"\b([A-Za-z0-9_]+\.lean)\b", raw_pdf_text))
                lean_filenames = {PurePosixPath(n).name for n in lean_files}
                stale_lean_refs = pdf_lean_refs - lean_filenames if lean_filenames else set()

                unexpanded_alerts = re.findall(r"\[!(?:CAUTION|NOTE|WARNING|TIP|IMPORTANT)\]", raw_pdf_text)
                has_authority_effect = "authorityeffect" in _normalize(raw_pdf_text)
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

                c02_reasons: List[str] = []
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
                set_result("C02", c02_ok, c02_detail)
        except ImportError:
            for key in ("C01", "C02"):
                results[key]["detail"] = "PyMuPDF is unavailable; PDF parsing/text comparison was not run."
        except (KeyError, ValueError, RuntimeError) as error:
            set_result("C01", False, f"PDF missing/unreadable: {error}")

        # C03: TeX source, maketitle, overfull hbox, missing glyphs, and MD034 bare URLs
        tex_source = text.get(stem + ".tex", "")
        # The text map skips .log files, so read the TeX log from the raw snapshot.
        tex_log = files.get(stem + ".log", b"").decode("utf-8", errors="replace")
        has_overfull = bool(tex_log and "Overfull \\hbox" in tex_log)

        bare_urls_found: Dict[str, List[str]] = {}
        md034_disabled: List[str] = []
        asterisk_lists_found: Dict[str, List[str]] = {}
        md004_disabled: List[str] = []
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

        c03_reasons: List[str] = []
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

        set_result(
            "C03",
            not c03_reasons,
            f"TeX/Markdown defect: {'; '.join(c03_reasons)}"
            if c03_reasons
            else "TeX presence, title-command, missing-glyph log, and Markdown MD004/MD034 checks passed.",
        )

        # D01: Claim ledger uniqueness and dual box constraint
        ledger = text.get(ledgers[0], "") if len(ledgers) == 1 else ""
        ids = re.findall(r"^\|\s*(?:\d+\s*\|\s*)?([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\s*\|", ledger, re.M)
        loose_dual_box = bool(
            re.search(
                r"[Dd]ual\s+box\s+constraint[^\n]*\\\|z\\\|_\\infty\s*\\le\s*\\max",
                ledger,
            )
        )
        set_result(
            "D01",
            bool(ids) and len(ids) == len(set(ids)) and not loose_dual_box,
            "Claim ledger specifies loose uniform bound ||z||_\\infty <= max_i w_i as dual box constraint (coordinatewise |z_i| <= w_i required under nonuniform weights)."
            if loose_dual_box
            else f"{len(ids)} ledger identifiers; checked nonempty uniqueness.",
        )

        # D03: Explicit pytest references in ledger resolve to AST functions
        try:
            references = re.findall(r"(test_[A-Za-z0-9_]+\.py)::(test_[A-Za-z0-9_]+)", ledger)
            missing_refs = []
            for filename, function in references:
                candidates = [name for name in tests if PurePosixPath(name).name == filename]
                if len(candidates) != 1 or not any(
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function
                    for node in ast.parse(text[candidates[0]]).body
                ):
                    missing_refs.append(f"{filename}::{function}")
            set_result(
                "D03",
                not missing_refs and (bool(references) or not python_files),
                f"Unresolved pytest references: {missing_refs}; inspected {len(references)} references.",
            )
        except (SyntaxError, ValueError, RecursionError) as error:
            set_result("D03", False, str(error))

        # E01: Python tests under code/tests/
        set_result(
            "E01",
            bool(tests) and not any(name.startswith("tests/") for name in files),
            f"{len(tests)} named test files under code/tests; no execution inferred.",
        )

        # E06: Mypy strictness (no blanket ignore_missing_imports)
        pyproject_text = text.get("pyproject.toml", "")
        blanket_mypy = False
        if "[tool.mypy]" in pyproject_text:
            mypy_sec = pyproject_text.split("[tool.mypy]", 1)[1].split("[[", 1)[0]
            if re.search(r"ignore_missing_imports\s*=\s*true", mypy_sec, re.I):
                blanket_mypy = True
        if blanket_mypy:
            set_result(
                "E06",
                False,
                "pyproject.toml specifies global ignore_missing_imports = true under [tool.mypy]; blanket missing-import ignoring masks broken dependencies and untyped interfaces.",
            )

        # E07: Direct notebook-client imports in pytest sources
        try:
            prohibited: List[str] = []
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
                    if any(val.split(".")[0] in ("nbclient", "nbconvert") for val in imports):
                        prohibited.append(name)
            set_result(
                "E07",
                not prohibited,
                f"Direct notebook-client imports in test sources: {sorted(set(prohibited))}; dynamic imports require review.",
            )
        except (SyntaxError, ValueError, RecursionError) as error:
            set_result("E07", False, str(error))

        # F01, F02, F04: Stored Notebook checks
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
            set_result("F01", valid, f"Validated stored JSON structure for {len(parsed)} notebooks.")
            if valid:
                cells = [cell for nb in parsed for cell in nb["cells"] if cell["cell_type"] == "code"]
                set_result(
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
                set_result(
                    "F04",
                    not re.search(r"[A-Za-z]:[\\/](?:Users|source|home)[\\/]|/(?:home|Users)/", source),
                    "Searched code cells for machine-specific absolute user paths; portability still needs extraction replay.",
                )
        except (ValueError, TypeError, RecursionError) as error:
            set_result("F01", False, str(error))

        # G01: Lean Lake configuration
        configurations = [
            name for name in files if PurePosixPath(name).name in ("lakefile.lean", "lakefile.toml")
        ]
        set_result(
            "G01",
            len(configurations) == 1
            and configurations[0] in ("lean4/lakefile.lean", "lean4/lakefile.toml"),
            f"Local Lake configurations: {configurations}",
        )

        # G02: Pinned Lean toolchain
        pin = files.get("lean4/lean-toolchain", b"").decode("utf-8", errors="replace").strip()
        set_result(
            "G02",
            bool(
                re.fullmatch(
                    r"leanprover/lean4:(?:v\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?|[0-9a-f]{40})", pin
                )
            ),
            f"Pinned toolchain: {pin!r}",
        )

        # G03: Lean proof escape hatches
        escapes: List[str] = []
        for name in lean_files:
            body = re.sub(r"/\-.*?\-/", "", text[name], flags=re.S)
            body = re.sub(r"--[^\n]*", "", body)
            if re.search(r"\b(?:sorry|admit|unsafe)\b|(?m:^\s*(?:axiom|constant)\s)", body):
                escapes.append(name)
        set_result(
            "G03",
            bool(lean_files) and not escapes,
            f"Potential proof escape hatches: {escapes}; lexical scan is not a kernel check.",
        )

        # G05: Lean axiom report
        census = text.get("lean4/axiom_report.txt", "")
        set_result(
            "G05",
            bool(census.strip()) and not re.search(r"windows-gnu|linux-gnu|darwin", census),
            "Checked report presence and absence of target triples; actual build/census provenance remains a separate obligation.",
        )

        # H01: README instructions and no retired manifest contradiction
        doc_manifest_retired = False
        if "MANIFEST.sha256" in files:
            for doc_name in ("README.md", stem + "_change_log.md"):
                doc_text = text.get(doc_name, "")
                if re.search(r"[Rr]etired[^\n]*MANIFEST\.sha256", doc_text):
                    doc_manifest_retired = True
                    break
        set_result(
            "H01",
            bool(
                re.search(
                    r"\b(?:verify_deposit|pytest|lake build)\b",
                    text.get("README.md", ""),
                )
            )
            and not doc_manifest_retired,
            "Documentation claims MANIFEST.sha256 was retired, but MANIFEST.sha256 is present in release payload."
            if doc_manifest_retired
            else "README contains a local verification command; execution and completeness require replay.",
        )

        # H05: Payload excludes empty placeholders, LLM dossiers, and forbidden paths
        forbidden = [
            name
            for name in files
            if name.endswith(".gitkeep")
            or any(
                word in name.lower()
                for word in ("bulgakov", "oldman", "nonclaims.md", "mutation_audit.md")
            )
            or name.split("/")[0] in ("evidence", "reconstruction_v1", "dist", "rt")
        ]
        set_result("H05", not forbidden, f"Internal dossier/placeholder/forbidden envelope paths: {forbidden}")

        # I01: Publication metadata fields & creators
        creators = metadata.get("creators")
        set_result(
            "I01",
            all(
                isinstance(metadata.get(k), str) and metadata[k].strip()
                for k in (
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

        # I02: License artifacts exist
        set_result(
            "I02",
            bool(files.get("LICENSE")) and (not python_files or bool(files.get("LICENSE-CODE"))),
            "License artifacts exist; no legal or external authorization judgment is inferred.",
        )

        # Scoped applicability for channels without corresponding artifacts
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

        # External evidence binding
        recorded_evidence: List[Dict[str, Any]] = []
        evidence_errors: List[str] = []
        if ev_path is not None:
            try:
                _regular(ev_path)
                if ev_path.stat().st_size > MAX_FILE_BYTES:
                    raise ValueError("evidence bundle exceeds byte limit")
                bundle = json.loads(ev_path.read_text(encoding="utf-8"))
                if (
                    bundle.get("schema") != "omega.paper_review.evidence.v1"
                    or bundle.get("snapshot_sha256") != snapshot_sha
                ):
                    raise ValueError("evidence schema or snapshot digest mismatch")
                seen: Set[Tuple[str, str]] = set()
                for entry in bundle.get("records", []):
                    k = entry["check_id"]
                    rel = _safe_name(entry["path"])
                    if k not in results or (k, rel) in seen:
                        raise ValueError("unknown or duplicate evidence record")
                    seen.add((k, rel))
                    target = ev_path.parent / rel
                    for parent in reversed(target.parents):
                        if parent == ev_path.parent or ev_path.parent in parent.parents:
                            _regular(parent, directory=True)
                    _regular(target)
                    data_bytes = target.read_bytes()
                    if _digest(data_bytes) != entry["sha256"]:
                        raise ValueError(f"evidence digest mismatch: {rel}")
                    rec = {
                        "check_id": k,
                        "path": str(target.absolute()),
                        "sha256": entry["sha256"],
                        "status": "RECORDED_PROVENANCE_ONLY",
                    }
                    recorded_evidence.append(rec)
                    results[k].setdefault("recorded_evidence", []).append(rec)
            except Exception as exc:
                evidence_errors.append(f"Invalid external evidence: {exc}")

        # H04: Release bytes unchanged during audit
        try:
            after_sha, _ = _identity(_snapshot(root))
            set_result(
                "H04",
                after_sha == snapshot_sha,
                "Recomputed complete snapshot after inspection; compared path/size/digest identity.",
            )
        except (OSError, ValueError) as error:
            set_result("H04", False, str(error))

        # Build final receipt
        check_items = [RepublicationCheckItem(**v) for v in results.values()]
        counts = dict(Counter(it.status for it in check_items))
        errors: List[str] = list(evidence_errors)
        errors.extend(
            f"{it.id} {it.status}: {it.requirement}"
            for it in check_items
            if it.status not in ("PASS", "NOT_APPLICABLE")
        )

        is_complete = all(it.status in ("PASS", "NOT_APPLICABLE") for it in check_items) and not errors

        return RepublicationGateReceipt(
            catalog_version=CATALOG_VERSION,
            catalog_origin=CATALOG_ORIGIN,
            snapshot_sha256=snapshot_sha,
            paper_path=str(root),
            monograph_path=str(monograph),
            files=rows,
            checks=check_items,
            counts=counts,
            recorded_evidence=recorded_evidence,
            errors=errors,
            status="PASS" if is_complete else "BLOCKED",
            verdict="READY FOR ZENODO REPUBLICATION" if is_complete else "NOT READY FOR ZENODO REPUBLICATION",
            authority_effect="None",
        )

