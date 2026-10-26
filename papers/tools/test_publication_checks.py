"""Negative controls for the collection's source/output custody and link gate."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from build_publications import package_dirs  # noqa: E402
from check_publications import (  # noqa: E402
    validate_bundle,
    validate_links,
    validate_manifest,
    validate_placeholders,
    validate_selection,
)


class PublicationCustodyTests(unittest.TestCase):
    def test_author_review_checks_its_own_manifest_and_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review = "publication/author_review_2026_10_23"
            bundle = root / review / "029"
            bundle.mkdir(parents=True)
            source = root / "source.md"
            source.write_text("original")
            exported = bundle / "paper.md"
            exported.write_text("[missing](missing.pdf)")
            manifest = {
                "inputs": {"source.md": hashlib.sha256(source.read_bytes()).hexdigest()},
                "outputs": {exported.relative_to(root).as_posix(): hashlib.sha256(exported.read_bytes()).hexdigest()},
            }
            (root / review / "manifest.json").write_text(json.dumps(manifest))
            self.assertEqual(validate_manifest(root, review), [])
            self.assertIn("Missing local link", validate_links(root, review)[0][0])
            source.write_text("changed")
            self.assertEqual(validate_manifest(root, review), ["Changed inputs: source.md"])

    def test_draft_refresh_preserves_historical_archive_and_rejects_changed_payload(self):
        import shutil

        from refresh_draft_manifests import refresh

        source = _TOOLS_DIR.parent / "003_pfp_host_admitted_failure_detectors"
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            for name in ("verify_deposit.py", "code/deposit_paths.py"):
                target = package / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / name, target)
            for name in ("paper.md", "paper_change_log.md", "paper_claim_ledger.md", "README.md", "LICENSE", "LICENSE-CODE", "pyproject.toml", "zenodo_metadata.json", "docs/descriptions.md", "docs/references.md"):
                target = package / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"Retained fixture bytes\n")
            historical = package / "historical.zip"
            historical.write_bytes(b"opaque historical archive identity")
            before = {p.name: p.read_bytes() for p in (historical, package / "zenodo_metadata.json")}
            refresh(package)
            self.assertEqual(before, {p.name: p.read_bytes() for p in (historical, package / "zenodo_metadata.json")})
            command = [sys.executable, "-B", "verify_deposit.py"]
            good = subprocess.run(command, cwd=package, capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            (package / "paper.md").write_bytes(b"substituted manuscript")
            bad = subprocess.run(command, cwd=package, capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("Hash mismatch: paper.md", bad.stdout)

    def test_changed_manuscript_and_pdf_are_detected_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "publication").mkdir()
            source, pdf = root / "paper.md", root / "paper.pdf"
            source.write_text("A scoped theorem.\n", encoding="utf-8")
            pdf.write_bytes(b"%PDF-1.7\noriginal")
            manifest = {"inputs": {"paper.md": hashlib.sha256(source.read_bytes()).hexdigest()}, "outputs": {"paper.pdf": hashlib.sha256(pdf.read_bytes()).hexdigest()}}
            (root / "publication/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(validate_manifest(root), [])
            source.write_text("An unsupported universal theorem.\n", encoding="utf-8")
            self.assertEqual(validate_manifest(root), ["Changed inputs: paper.md"])
            pdf.write_bytes(b"%PDF-1.7\nreplaced")
            self.assertEqual(len(validate_manifest(root)), 2)

    def test_same_byte_control_and_payload_parent_links_are_rejected(self):
        for selected in ("publication", "inputs"):
            with self.subTest(selected=selected), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "collection"
                (root / "publication").mkdir(parents=True)
                (root / "inputs").mkdir()
                source, pdf = root / "inputs/paper.md", root / "paper.pdf"
                source.write_bytes(b"Scoped statement")
                pdf.write_bytes(b"%PDF-1.7\nfixture")
                manifest = {
                    "inputs": {"inputs/paper.md": hashlib.sha256(source.read_bytes()).hexdigest()},
                    "outputs": {"paper.pdf": hashlib.sha256(pdf.read_bytes()).hexdigest()},
                }
                (root / "publication/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                self.assertEqual(validate_manifest(root), [])
                original, retained = root / selected, root / "retained"
                self.assertTrue(original.resolve().is_relative_to(Path(directory).resolve()))
                self.assertTrue(retained.resolve().is_relative_to(Path(directory).resolve()))
                original.rename(retained)
                if os.name == "nt":
                    def quoted(path):
                        return "'" + str(path).replace("'", "''") + "'"
                    command = f"New-Item -ItemType Junction -Path {quoted(original)} -Target {quoted(retained)} | Out-Null"
                    subprocess.run(["powershell.exe", "-NoProfile", "-Command", command], check=True, capture_output=True)
                else:
                    original.symlink_to(retained, target_is_directory=True)
                errors = validate_manifest(root)
                self.assertTrue(errors)
                self.assertTrue(any("Non-regular" in error or "escapes" in error for error in errors))

    def test_missing_exported_pdf_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "publication/001").mkdir(parents=True)
            (root / "publication/001/paper.md").write_text('[Claim](../002/paper.pdf)', encoding="utf-8")
            errors, count = validate_links(root)
            self.assertEqual(count, 1)
            self.assertIn("Missing local link", errors[0])

    def test_current_manifest_cannot_authenticate_an_older_consistent_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "publication/001"
            bundle.mkdir(parents=True)
            source, ledger = root / "canonical.md", root / "ledger.md"
            source.write_bytes(b"Revised manuscript")
            ledger.write_bytes(b"Ledger")
            receipt = {}
            outputs = {}
            for name, key, data in [
                ("source.md", "source_sha256", b"Old manuscript"),
                ("claim_ledger.source.md", "ledger_sha256", b"Ledger"),
                ("paper.md", "markdown_sha256", b"Old rendered manuscript"),
                ("claim_ledger.md", "ledger_markdown_sha256", b"Ledger"),
                ("paper.tex", "tex_sha256", b"Old TeX"),
                ("paper.pdf", "pdf_sha256", b"%PDF-1.7\nOld PDF"),
            ]:
                (bundle / name).write_bytes(data)
                receipt[key] = hashlib.sha256(data).hexdigest()
                outputs[(bundle / name).relative_to(root).as_posix()] = receipt[key]
            (bundle / "build_receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            manifest = {"inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, ledger)}, "outputs": outputs}
            (root / "publication/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(validate_manifest(root), [])
            self.assertEqual(validate_bundle(root, {"id": "001", "source": source, "ledger": ledger}, manifest), ["Bundle 001 does not match canonical source_sha256"])

    def test_empty_or_escaping_manifest_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "publication").mkdir()
            path = root / "publication/manifest.json"
            path.write_text(json.dumps({"inputs": {}, "outputs": {"../outside": "a"}}), encoding="utf-8")
            errors = validate_manifest(root)
            self.assertEqual(len(errors), 2)
            self.assertIn("Empty inputs", errors[0])
            self.assertIn("escapes", errors[1])


    def test_selection_gap_is_allowed_only_at_a_reserved_identifier(self):
        """Counterexample: 012 after 010 with 011 missing and not reserved must fail."""
        ids = [f"{i:03}" for i in range(1, 11)] + ["012"]
        self.assertTrue(validate_selection(ids, {}))
        self.assertEqual(validate_selection(ids, {"011": "omega_engine_projects/fsp/meron_sign_problem"}), [])
        self.assertTrue(validate_selection(ids, {"011": ""}))
        self.assertTrue(validate_selection(ids + ["011"], {"011": "elsewhere"}))
        self.assertTrue(validate_selection(["002", "003"], {}))
        self.assertTrue(validate_selection(["001", "001"], {}))

    def test_package_dir_pin_ignores_a_same_numbered_shelf(self):
        with tempfile.TemporaryDirectory() as directory:
            series = Path(directory)
            (series / "020_author_review").mkdir()
            pinned = series / "022_deposited_paper"
            pinned.mkdir()
            found = package_dirs(series, {"id": "020", "package_dir": "022_deposited_paper"})
            self.assertEqual(found, [pinned])
            self.assertEqual(package_dirs(series, {"id": "020"}), [series / "020_author_review"])
            with self.assertRaises(ValueError):
                package_dirs(series, {"id": "020", "package_dir": "../022_deposited_paper"})

    def test_introductory_zero_keeps_gap_checks(self):
        self.assertEqual(validate_selection(["000", "001", "002"], {}), [])
        self.assertTrue(validate_selection(["000", "002"], {}))
        self.assertTrue(validate_selection(["000", "000", "001"], {}))
    def test_placeholder_token_in_package_is_rejected(self):
        """Counterexample: any file in a catalogued package containing PLACEHOLDER must fail."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "009_test_package"
            folder.mkdir(parents=True)
            source = folder / "paper.md"
            source.write_text("Introduction with PLACEHOLDER-G marker\n", encoding="utf-8")
            entry = {"id": "009", "source": source}
            errors = validate_placeholders(root, entry)
            self.assertTrue(errors)
            self.assertTrue(any("PLACEHOLDER" in e for e in errors))

            # Clean manuscript passes
            source.write_text("Clean manuscript with commit e6fbc15cf\n", encoding="utf-8")
            build = folder / "code/rust/target/debug"
            build.mkdir(parents=True)
            (build / "dependency.rlib").write_bytes(b"PLACEHOLDER")
            self.assertEqual(validate_placeholders(root, entry), [])


if __name__ == "__main__":
    unittest.main()
