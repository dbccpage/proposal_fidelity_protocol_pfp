"""Assemble the frozen offline campaign and author-review papers; never dispatch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SERIES = ROOT / "omega_engine_atlas/015_pfp"
REVIEW = SERIES / "publication/author_review_2026_10_23"
EXCLUDED = {"__pycache__", ".pytest_cache", ".ruff_cache", ".git", ".lake", "target", ".venv"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regular_path(path: Path) -> None:
    info = path.lstat()
    if (
        stat.S_ISLNK(info.st_mode)
        or getattr(info, "st_file_attributes", 0) & 0x400
        or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode))
    ):
        raise ValueError(f"NONREGULAR_PACKAGE_PATH: {path}")


def copy_tree(source: Path, target: Path) -> None:
    def fail(error):
        raise error

    regular_path(source)
    for directory, folders, filenames in os.walk(source, onerror=fail, followlinks=False):
        directory = Path(directory)
        for name in (*folders, *filenames):
            regular_path(directory / name)
        folders[:] = sorted(name for name in folders if name not in EXCLUDED)
        for name in sorted(filenames):
            path = directory / name
            if (
                name
                in {
                    ".env",
                    "package_staging_path.txt",
                    "package_verification.json",
                }
                or path.suffix in {".zip", ".pyc", ".pyo"}
                or name.endswith(".zip.sha256")
            ):
                continue
            destination = target / path.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="New, nonexistent package directory")
    args = parser.parse_args()
    package = args.destination.resolve()
    package.mkdir(parents=True, exist_ok=False)
    repository = package / "repository"
    sources = json.loads((HERE / "campaign/sources.json").read_text())
    for relative, expected in sources.items():
        source = ROOT / relative
        for parent in (source, *source.parents):
            if parent == ROOT.parent:
                break
            regular_path(parent)
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"Frozen source changed: {relative}")
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    for relative in (
        "omega_engine_woland/tests/research/test_harness_contracts.py",
        "omega_engine_woland/tests/research/test_harness_execution.py",
        "omega_engine_woland/tests/providers/test_harness_anthropic_budget.py",
        "omega_engine_woland/tests/research/test_harness_review_regressions.py",
    ):
        target = repository / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    copy_tree(HERE, repository / HERE.relative_to(ROOT))
    catalog = json.loads((SERIES / "publication_catalog.json").read_text())
    packaged_series = repository / SERIES.relative_to(ROOT)
    for entry in catalog["author_review_publications"]:
        copy_tree(SERIES / entry["package_dir"], packaged_series / entry["package_dir"])
    for name in ("tools", "verification"):
        if (SERIES / name).exists():
            copy_tree(SERIES / name, packaged_series / name)
    for name in ("README.md", "publication_catalog.json"):
        shutil.copyfile(SERIES / name, packaged_series / name)
    copy_tree(REVIEW, packaged_series / REVIEW.relative_to(SERIES))
    toolkit = ROOT / "omega_engine_atlas/_kits/paper_template/tools/rebuild_release.py"
    (package / "tools").mkdir()
    shutil.copyfile(toolkit, package / "tools/rebuild_release.py")
    toolkit_target = repository / toolkit.relative_to(ROOT)
    toolkit_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(toolkit, toolkit_target)
    for name in ("LICENSE", "LICENSE-CODE"):
        shutil.copyfile(SERIES / "029_pfp_evidence_bound_harness_evolution" / name, package / name)
    (package / "replay_offline.py").write_text(
        """from pathlib import Path
import sys
root = Path(__file__).resolve().parent / "repository"
sys.path.insert(0, str(root))
from omega_engine_woland.entrypoints.research.harness_cli import main
docs = root / "omega_engine_woland/documentation/harness_evolution"
raise SystemExit(main(["replay", "--output", str(docs / "campaign"), "--prices", str(docs / "pricing_observation.json"), "--pricing-evidence", str(docs / "pricing_evidence.json")]))
""",
        encoding="utf-8",
    )
    runtime = json.loads((HERE / "verification/runtime.json").read_text())
    (package / "observed_dependencies.txt").write_text(
        "# Observed Python 3.12 environment; fresh dependency installation was not tested.\n"
        + "".join(
            f"{name}=={version}\n" for name, version in sorted(runtime["dependencies"].items())
        ),
        encoding="utf-8",
    )
    (package / "README.md").write_text(
        """# Evidence-Bound Harness Evolution — author review

This package contains the implemented research loop, frozen offline protocol,
retained local verification, eleven revised papers and new Paper 029. It is an
author-review delivery, with no external deposit or production admission.

The campaign is NOT_RUN: zero provider calls, zero spend, zero model trials.
Linux containment testing and the paid campaign were deferred by the operator.
Focused test counts and receipts are in verification/summary.json. The 158
task-calibration cases are host fixtures, not
independent model trials. Paper 027's unavailable historical model receipts are
explicitly unverified; its finite examples were checked separately.

From this directory, with Python 3.12 and the observed dependencies installed:

```text
python replay_offline.py
python tools/rebuild_release.py . --check
```

The archive must be beside MANIFEST.sha256 for the second command's archive
comparison. The extracted source replay was checked with Python isolated mode
and an explicit path to existing installed dependencies. A fresh dependency
installation and a hermetic environment were not tested. Replay makes no network
requests. The report honestly remains NOT_RUN; checker replay is not a trial.

Read repository/omega_engine_woland/documentation/harness_evolution/README.md
for the CLI, original budget ledger, frozen source identities, admission rules,
Linux handoff and pricing refresh procedure. That directory contains campaign/
and verification/ with retained receipts and diagnostic drafts.

The PDFs, exact Markdown sources, LaTeX and build manifest are under
repository/omega_engine_atlas/015_pfp/publication/
author_review_2026_10_23/. Paper 029 is in 029/paper.pdf. The source-to-claim map
binds the supplied PDF hash and individual pages without redistributing it.

The repository directory is the frozen replay source subset, not a complete
checkout or native build workspace. Full native builds and unit-test reproduction
require the full repository at the recorded base plus this delivery's changes.
The existing Windows native binary was reused; only its identity is retained.
The current-policy baseline is a projection into the common adapter. The ignition
design is exploratory. No measured improvement, transfer or acceleration is claimed.

MANIFEST.sha256 and SHA256SUMS bind this package's files; nested historical
manifests retain their original scope. Historical release archives and deposited
identities were not updated. Licenses are supplied separately for text and code.
""",
        encoding="utf-8",
    )
    files = sorted(p for p in package.rglob("*") if p.is_file())
    (package / "MANIFEST.sha256").write_text(
        "".join(f"{digest(path)}  {path.relative_to(package).as_posix()}\n" for path in files),
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(package / "tools/rebuild_release.py"), str(package)], check=True
    )
    print(
        json.dumps(
            {"package": str(package), "frozen_source_files": len(sources), "files": len(files)}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
