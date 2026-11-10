"""Replay the pinned, zero-call author-review archive independently of current main."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import site
import stat
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "omega_engine_atlas/015_pfp/publication/author_review_2026_10_23/pfp_harness_author_review_2026-10-23.zip"
ARCHIVE_SHA256 = "83bd2f2d6452ea0a63edd915305f6290c98b00de99b975e3e01d7bf3321a9e7d"
PACKAGE = "pfp_harness_author_review"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def member_path(name: str) -> PurePosixPath:
    parts = name.split("/")
    reserved = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.I)
    if (
        len(parts) < 2
        or parts[0] != PACKAGE
        or any(p in {"", ".", ".."} or p.endswith((".", " ")) or reserved.match(p) for p in parts)
        or any(c in name for c in '\\:<>"|?*')
        or any(ord(c) < 32 for c in name)
    ):
        raise ValueError("UNSAFE_ARCHIVE_MEMBER")
    return PurePosixPath(name)


def extract(archive: Path, destination: Path, expected: str) -> Path:
    """Authenticate before extracting or executing; require a fresh regular directory."""
    archive = archive.absolute()
    for component in (archive, *archive.parents):
        info = component.lstat()
        if (
            stat.S_ISLNK(info.st_mode)
            or getattr(info, "st_file_attributes", 0) & 0x400
            or (component == archive and not stat.S_ISREG(info.st_mode))
        ):
            raise ValueError("NONREGULAR_ARCHIVE_PATH")
    raw = archive.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("ARCHIVE_DIGEST_MISMATCH")
    destination = destination.absolute()
    for parent in (destination, *destination.parents):
        if parent.exists() or parent.is_symlink():
            info = parent.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise ValueError("LINKED_EXTRACTION_PATH")
    if destination.exists():
        raise ValueError("EXTRACTION_DESTINATION_EXISTS")
    # Extraction consumes the exact authenticated bytes, never a reopened path.
    with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
        members = zipped.infolist()
        names = set()
        total = 0
        for item in members:
            member_path(item.orig_filename)
            if item.orig_filename != item.filename:
                raise ValueError("UNSAFE_ARCHIVE_MEMBER")
            mode = item.external_attr >> 16
            if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                raise ValueError("NONREGULAR_ARCHIVE_MEMBER")
            folded = item.filename.casefold()
            if folded in names:
                raise ValueError("DUPLICATE_ARCHIVE_MEMBER")
            names.add(folded)
            total += item.file_size
        if len(members) > 4000 or total > 100_000_000:
            raise ValueError("ARCHIVE_SIZE_BOUND")
        destination.mkdir(parents=True, exist_ok=False)
        for item in members:
            target = destination.joinpath(*member_path(item.filename).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                output.write(zipped.read(item))
    return destination / PACKAGE


CHILD = r'''
import json, pathlib, runpy, sys
package = pathlib.Path(sys.argv[1])
sys.path.extend(json.loads(sys.argv[2]))
def offline(event, args):
    if event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"}:
        raise RuntimeError("OFFLINE_REPLAY_EXTERNAL_EXECUTION_REFUSED: " + event)
sys.addaudithook(offline)
verifier = runpy.run_path(str(package / "tools/rebuild_release.py"))
errors = verifier["validate"](package)
if errors:
    raise ValueError(errors)
try:
    runpy.run_path(str(package / "replay_offline.py"), run_name="__main__")
except SystemExit as result:
    if result.code not in (None, 0):
        raise
errors = verifier["validate"](package)
if errors:
    raise ValueError(errors)
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New directory outside historical packages")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.error("Python 3.12 is required")
    output = args.output.absolute()
    package = extract(ARCHIVE, output, ARCHIVE_SHA256)
    shutil.copyfile(ARCHIVE, package / ARCHIVE.name)
    dependencies = sorted({p for p in [*site.getsitepackages(), site.getusersitepackages()] if Path(p).is_dir()})
    env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
    env["OMEGA_CREDENTIAL_DISCOVERY"] = "off"
    failure = None
    exit_code = None
    stdout = stderr = ""
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-S", "-B", "-c", CHILD, str(package), json.dumps(dependencies)],
            cwd=package, env=env, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=300, check=False,
        )
        exit_code, stdout, stderr = result.returncode, result.stdout, result.stderr
        if exit_code != 0:
            failure = "REPLAY_FAILED"
    except subprocess.TimeoutExpired as error:
        failure = "REPLAY_TIMEOUT"
        stdout, stderr = error.stdout or "", error.stderr or ""
    except OSError as error:
        failure = "REPLAY_START_FAILED"
        stderr = type(error).__name__
    for name, content in (("replay.stdout.txt", stdout), ("replay.stderr.txt", stderr)):
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        (output / name).write_text(content, encoding="utf-8")
    receipt = {
        "schema": "woland.frozen-review-replay.v1", "archive_sha256": ARCHIVE_SHA256,
        "python": sys.version, "exit_code": exit_code,
        "dependency_directories": dependencies, "fresh_dependency_installation": "NOT_TESTED",
        "platform": sys.platform, "linux_testing": "OUT_OF_SCOPE", "paid_campaign": "DEFERRED",
        "execution": "isolated Python; credential-free environment; socket and child-process audit refusal",
    }
    if failure is None:
        try:
            report = json.loads((package / "repository/omega_engine_woland/documentation/harness_evolution/campaign/report.json").read_text())
            zero_fields = ("independent_provider_calls", "assigned_trials", "spent_microusd", "held_microusd")
            if report["status"] != "NOT_RUN" or any(type(report[k]) is not int or report[k] != 0 for k in zero_fields):
                raise ValueError("NOT_THE_FROZEN_ZERO_CALL_REPORT")
            receipt["campaign"] = report
        except (OSError, ValueError, KeyError, TypeError):
            failure = "REPLAY_REPORT_INVALID"
    receipt.update(status="PASS" if failure is None else "FAIL", failure=failure)
    (output / "replay_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "receipt": str(output / "replay_receipt.json")}))
    return 0 if failure is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
