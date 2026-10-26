"""Capture and verify explicitly named installed replay dependencies.

No installation, credential discovery, or provider access occurs here. A profile
binds the interpreter and the distribution-declared files present on this host;
it does not claim a hermetic operating system or mathematical correctness.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import stat
import sys
from pathlib import Path

SCHEMA = "paper011.runtime-environment.v1"


def file_digest(path: Path, directories: dict | None = None) -> str:
    for candidate in (path, *path.parents):
        if candidate != path and directories is not None and candidate in directories:
            continue
        entry = candidate.lstat()
        if stat.S_ISLNK(entry.st_mode) or getattr(entry, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"REDIRECTED_RUNTIME_FILE:{candidate}")
        if candidate != path and directories is not None:
            directories[candidate] = (entry.st_dev, entry.st_ino, entry.st_mode)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f"NONREGULAR_RUNTIME_FILE:{path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(1024 * 1024):
            digest.update(data)
    return digest.hexdigest()


def snapshot(names: list[str], interpreter: Path | None = None) -> dict:
    if not names or len(set(names)) != len(names):
        raise ValueError("EMPTY_OR_DUPLICATE_DISTRIBUTION_LIST")
    # Windows App Execution Aliases are launchers, not regular interpreter files.
    # The caller must explicitly provide the real backing executable in that case.
    executable = (
        interpreter.absolute() if interpreter is not None else Path(sys.executable).absolute()
    )
    directories = {}
    executable_digest = file_digest(executable, directories)
    dependencies = []
    for requested in sorted(names, key=lambda name: name.encode("utf-8")):
        distribution = importlib.metadata.distribution(requested)
        if not distribution.files:
            raise ValueError(f"DISTRIBUTION_FILE_INVENTORY_MISSING:{requested}")
        files = []
        for entry in sorted(distribution.files, key=lambda item: str(item).encode("utf-8")):
            # Installed .pyc caches are mutable and are not source inputs. -B is
            # used by replay workers; original source/extension bytes are pinned.
            if str(entry).endswith(".pyc"):
                continue
            path = Path(distribution.locate_file(entry)).absolute()
            files.append(
                {"entry": str(entry), "path": str(path), "sha256": file_digest(path, directories)}
            )
        dependencies.append(
            {
                "requested_name": requested,
                "name": distribution.metadata["Name"],
                "version": distribution.version,
                "files": files,
            }
        )
    for directory, original_identity in directories.items():
        entry = directory.lstat()
        if (
            (entry.st_dev, entry.st_ino, entry.st_mode) != original_identity
            or stat.S_ISLNK(entry.st_mode)
            or getattr(entry, "st_file_attributes", 0) & 0x400
        ):
            raise ValueError(f"RUNTIME_DIRECTORY_DRIFT:{directory}")
    return {
        "schema_version": SCHEMA,
        "python": {
            "version": sys.version,
            "launcher": sys.executable,
            "executable": str(executable),
            "sha256": executable_digest,
        },
        "distributions": dependencies,
        "scope": "Interpreter identity and declared installed distribution files; excludes pyc caches and does not bind all operating-system or stdlib state.",
    }


def verify(profile: dict) -> dict:
    if profile.get("schema_version") != SCHEMA:
        raise ValueError("RUNTIME_PROFILE_SCHEMA_MISMATCH")
    names = [entry["requested_name"] for entry in profile["distributions"]]
    observed = snapshot(names, Path(profile["python"]["executable"]))
    if observed != profile:
        raise ValueError("RUNTIME_DEPENDENCY_DRIFT")
    return {
        "status": "DECLARED_RUNTIME_FILES_UNCHANGED",
        "distributions": len(names),
        "files": sum(len(entry["files"]) for entry in observed["distributions"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    capture = actions.add_parser("capture")
    capture.add_argument("--distribution", action="append", required=True)
    capture.add_argument("--output", type=Path, required=True)
    capture.add_argument("--interpreter", type=Path)
    check = actions.add_parser("verify")
    check.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "capture":
        result = snapshot(args.distribution, args.interpreter)
        raw = (
            json.dumps(
                result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode("utf-8")
            + b"\n"
        )
        args.output.write_bytes(raw)
        print(
            json.dumps(
                {
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "distributions": len(result["distributions"]),
                    "files": sum(len(entry["files"]) for entry in result["distributions"]),
                }
            )
        )
    else:
        profile = json.loads(args.profile.read_bytes().decode("utf-8"))
        print(json.dumps(verify(profile)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
