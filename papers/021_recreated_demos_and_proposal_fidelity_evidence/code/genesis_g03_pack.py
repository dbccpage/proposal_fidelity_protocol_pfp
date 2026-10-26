"""Deterministic lossless representation of every local G03 evidence byte."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import tarfile
import zlib
from pathlib import Path, PurePosixPath

PAPER = Path(__file__).resolve().parent.parent
AREA = PAPER / "docs/history_recovery/g03"
ARCHIVE = AREA / "evidence.tar.gz"
MANIFEST = AREA / "archive_manifest.json"
REPRESENTATION_FILES = {"evidence.tar.gz", "archive_manifest.json", "pack_process.json", "pack_stdout.txt", "pack_stderr.txt"}


def evidence_paths(root: Path) -> list[Path]:
    # Exclusions name only top-level representation files. Nested evidence with
    # the same basename remains part of the complete raw population.
    return sorted((path for path in root.rglob("*") if path.is_file()
                   and path.relative_to(root).as_posix() not in REPRESENTATION_FILES),
                  key=lambda path: path.relative_to(root).as_posix().encode("utf8"))


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def check_member_name(name: str) -> str:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or str(path) != name or ":" in name:
        raise ValueError("UNSAFE_G03_ARCHIVE_MEMBER")
    return name


def verify() -> dict:
    manifest = json.loads(MANIFEST.read_bytes())
    if manifest["schema"] != "paper011.g03-lossless-representation.v1":
        raise ValueError("G03_ARCHIVE_SCHEMA_CHANGED")
    if manifest["path_order"] != "relative POSIX paths, UTF-8 byte ordinal":
        raise ValueError("G03_ARCHIVE_PATH_ORDER_CHANGED")
    paths = [row["path"] for row in manifest["entries"]]
    if paths != sorted(paths, key=lambda path: path.encode("utf8")):
        raise ValueError("G03_ARCHIVE_PATH_ORDER_CHANGED")
    if manifest["packer"] != {"path": "code/genesis_g03_pack.py", "sha256": digest(Path(__file__))}:
        raise ValueError("G03_PACKER_SOURCE_CHANGED")
    if manifest["excluded_representation_metadata"] != sorted(REPRESENTATION_FILES, key=lambda name: name.encode("utf8")):
        raise ValueError("G03_ARCHIVE_EXCLUSIONS_CHANGED")
    if ARCHIVE.stat().st_size != manifest["archive_bytes"] or digest(ARCHIVE) != manifest["archive_sha256"]:
        raise ValueError("G03_COMPRESSED_BYTES_CHANGED")
    expected = {row["path"]: row for row in manifest["entries"]}
    if len(expected) != len(manifest["entries"]):
        raise ValueError("DUPLICATED_G03_ARCHIVE_MEMBER")
    seen = set()
    actual_paths = []
    with tarfile.open(ARCHIVE, "r|gz") as archive:
        for member in archive:
            name = check_member_name(member.name)
            if name in seen or name not in expected or not member.isfile() or member.size != expected[name]["raw_bytes"]:
                raise ValueError("G03_ARCHIVE_MEMBER_POPULATION_OR_TYPE_CHANGED")
            seen.add(name)
            actual_paths.append(name)
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("MISSING_G03_ARCHIVE_MEMBER_BYTES")
            result = hashlib.sha256()
            count = 0
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                count += len(chunk)
                result.update(chunk)
            if count != expected[name]["raw_bytes"] or result.hexdigest() != expected[name]["raw_sha256"]:
                raise ValueError("G03_DECOMPRESSION_IDENTITY_CHANGED")
    if seen != set(expected):
        raise ValueError("MISSING_G03_ARCHIVE_MEMBERS")
    if actual_paths != paths:
        raise ValueError("G03_ARCHIVE_MEMBER_ORDER_CHANGED")
    return manifest


def pack() -> dict:
    paths = evidence_paths(AREA)
    if any(path.is_symlink() for path in paths):
        raise ValueError("REDIRECTED_G03_EVIDENCE")
    if not (AREA / "receipt.json").is_file() or not (AREA / "completion_receipt.json").is_file():
        raise ValueError("G03_CUSTODY_MUST_CLOSE_BEFORE_COMPRESSION")
    entries = [{"path": check_member_name(path.relative_to(AREA).as_posix()),
                "raw_bytes": path.stat().st_size, "raw_sha256": digest(path)} for path in paths]
    with ARCHIVE.open("wb") as output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=output, compresslevel=9, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.USTAR_FORMAT) as archive:
                for path, row in zip(paths, entries):
                    info = tarfile.TarInfo(row["path"])
                    info.size, info.mode, info.mtime = row["raw_bytes"], 0o644, 0
                    info.uid, info.gid, info.uname, info.gname = 0, 0, "", ""
                    with path.open("rb") as stream:
                        archive.addfile(info, stream)
    manifest = {"schema": "paper011.g03-lossless-representation.v1", "AuthorityEffect": "None",
                "archive": "evidence.tar.gz", "archive_bytes": ARCHIVE.stat().st_size, "archive_sha256": digest(ARCHIVE),
                "raw_total_bytes": sum(row["raw_bytes"] for row in entries), "entries": entries,
                "path_order": "relative POSIX paths, UTF-8 byte ordinal",
                "packer": {"path": "code/genesis_g03_pack.py", "sha256": digest(Path(__file__))},
                "tar_format": "USTAR", "member_metadata": "regular files, mode 0644, uid/gid0, empty uname/gname, mtime0",
                "gzip": {"level": 9, "mtime": 0, "filename": "", "runtime_zlib": zlib.ZLIB_RUNTIME_VERSION},
                "excluded_representation_metadata": sorted(REPRESENTATION_FILES, key=lambda name: name.encode("utf8")),
                "raw_run_files_deleted": False, "all_available_g03_evidence_bytes_included": True,
                "scope": "Lossless representation of local G03 evidence, including complete populations and fields. Source and binary dependencies elsewhere in the paper remain separately declared; this archive alone is not the complete standalone release."}
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf8", newline="\n")
    verify()
    for path, row in zip(paths, entries):
        if path.stat().st_size != row["raw_bytes"] or digest(path) != row["raw_sha256"]:
            raise ValueError("RAW_G03_BYTES_CHANGED_DURING_PACKING")
    return {"archive_sha256": manifest["archive_sha256"], "archive_bytes": manifest["archive_bytes"],
            "raw_total_bytes": manifest["raw_total_bytes"], "members": len(entries), "manifest_sha256": digest(MANIFEST)}


def unpack(destination: Path) -> dict:
    # Verify the entire compressed and decompressed population before writing.
    manifest = verify()
    root = destination.resolve()
    workspace = PAPER.parents[3]
    if not root.is_relative_to(workspace):
        raise ValueError("UNPACK_DESTINATION_OUTSIDE_DECLARED_WORKSPACE")
    expected = {row["path"]: row for row in manifest["entries"]}
    with tarfile.open(ARCHIVE, "r|gz") as archive:
        for member in archive:
            relative = check_member_name(member.name)
            target = root / relative
            if not target.resolve().is_relative_to(root) or any(parent.is_symlink() for parent in (target, *target.parents)):
                raise ValueError("REDIRECTED_G03_UNPACK_DESTINATION")
            if target.exists():
                if not target.is_file() or digest(target) != expected[relative]["raw_sha256"]:
                    raise ValueError("REFUSE_OVERWRITE_OF_DIFFERENT_G03_BYTES")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("MISSING_G03_ARCHIVE_MEMBER_BYTES")
            with target.open("xb") as output:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    output.write(chunk)
    for row in manifest["entries"]:
        target = root / row["path"]
        if target.stat().st_size != row["raw_bytes"] or digest(target) != row["raw_sha256"]:
            raise ValueError("G03_UNPACK_IDENTITY_CHANGED")
    return {"destination": str(root), "members": len(expected), "exact_raw_bytes_restored": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("pack", "verify", "unpack"))
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    result = pack() if args.action == "pack" else verify() if args.action == "verify" else unpack(args.destination)
    if args.action == "verify":
        result = {"archive_sha256": result["archive_sha256"], "members": len(result["entries"]), "exact_decompression_identity": True}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
