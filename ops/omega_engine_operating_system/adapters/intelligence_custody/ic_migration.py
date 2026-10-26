"""Recoverable copy/verify/activate of intelligence bytes under the OEOS lease.

No delete, locator rewrite, archive repack, database repair or automatic quiescing.
All direct writers must be stopped by the operator in addition to the cooperative
OEOS lease. SQLite sidecars require checkpoint/close before inventorying.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
import uuid
from dataclasses import InitVar, asdict, dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

from omega_engine_governance.domain.intelligence_community import AgencyCode

from .ic_routing import (
    CONTROL,
    ROUTING_PROFILE,
    IcMigrationRefusal,
    _bound_inventory,
    historical_snapshot_path,
    historical_ic_relative_path,
    ic_relative_path,
    json_bytes,
    parse_json,
    path_casefold,
    read_activation,
    relative_parts,
    safe_path,
)

LOCK = CONTROL + "/checkout-writer.lock"
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_HEAD = re.compile(r"[0-9a-f]{40}\Z")


def _hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@dataclass(frozen=True, slots=True)
class InventoryFile:
    source: str
    destination: str
    sha256: str
    size: int
    kind: str = "regular_file"
    historical: InitVar[bool] = False

    def __post_init__(self, historical: bool):
        if (
            self.kind != "regular_file"
            or type(self.size) is not int
            or not 0 <= self.size <= 2**63 - 1
            or type(self.sha256) is not str
            or not _DIGEST.fullmatch(self.sha256)
        ):
            raise IcMigrationRefusal("INVENTORY_INVALID", "invalid file metadata")
        allowed = {ic_relative_path(self.source)}
        if historical is True:
            allowed.add(historical_ic_relative_path(self.source))
        if type(historical) is not bool or self.destination not in allowed or self.source == LOCK:
            raise IcMigrationRefusal("INVENTORY_INVALID", "route or control anchor differs")


@dataclass(frozen=True, slots=True)
class MigrationInventory:
    repository_root: str
    repository: str
    source_revision: str
    files: tuple[InventoryFile, ...]
    directories: tuple[str, ...]
    destination_baseline: tuple[tuple[str, str, int], ...]
    schema: str = "omega.ic.inventory.v1"
    routing_profile: str = ROUTING_PROFILE
    authority_effect: str = "None"
    historical: InitVar[bool] = False

    def __post_init__(self, historical: bool = False):
        if (
            self.schema != "omega.ic.inventory.v1"
            or self.routing_profile != ROUTING_PROFILE
            or self.authority_effect != "None"
            or type(self.source_revision) is not str
            or not _HEAD.fullmatch(self.source_revision)
            or type(self.repository) is not str
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repository)
            or type(self.repository_root) is not str
            # Historical metadata can originate on another OS. The recorded
            # root is not opened here; apply() separately binds the local root.
            or not (
                PurePosixPath(self.repository_root).is_absolute()
                or PureWindowsPath(self.repository_root).is_absolute()
            )
        ):
            raise IcMigrationRefusal("INVENTORY_INVALID", "identity/schema differs")
        if type(self.files) is not tuple or any(
            type(row) is not InventoryFile for row in self.files
        ):
            raise IcMigrationRefusal("INVENTORY_INVALID", "file rows differ")
        names = [row.source for row in self.files]
        destinations = [row.destination for row in self.files]
        if len(set(names)) != len(names) or len(set(destinations)) != len(destinations):
            raise IcMigrationRefusal("INVENTORY_INVALID", "duplicate inventory paths")
        if type(self.directories) is not tuple:
            raise IcMigrationRefusal("INVENTORY_INVALID", "directory rows differ")
        all_paths = names + list(self.directories)
        targets = destinations + [ic_relative_path(p) for p in self.directories]
        for group in (all_paths, targets):
            if len({path_casefold(p) for p in group}) != len(group):
                raise IcMigrationRefusal("CASE_COLLISION", "ambiguous paths")
        self._validate_baseline(historical=historical)

    def _validate_baseline(self, historical: bool = False):
        if type(self.destination_baseline) is not tuple:
            raise IcMigrationRefusal("INVENTORY_INVALID", "baseline rows differ")
        baseline_names = []
        for row in self.destination_baseline:
            if type(row) is not tuple or len(row) != 3:
                raise IcMigrationRefusal("INVENTORY_INVALID", "baseline row differs")
            path, digest, size = row
            parts = relative_parts(path)
            if (
                len(parts) < 3
                or parts[0] != "_ic"
                or parts[1] not in {agency.value for agency in AgencyCode}
                or path.startswith(CONTROL + "/")
                or type(digest) is not str
                or not _DIGEST.fullmatch(digest)
                or type(size) is not int
                or not 0 <= size <= 2**63 - 1
            ):
                raise IcMigrationRefusal("INVENTORY_INVALID", "baseline metadata differs")
            baseline_names.append(path_casefold(path))
        if not historical and len(set(baseline_names)) != len(baseline_names):
            raise IcMigrationRefusal("CASE_COLLISION", "baseline paths collide")

    @property
    def bytes(self) -> bytes:
        return json_bytes(asdict(self))

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.bytes).hexdigest()

    @classmethod
    def from_bytes(cls, raw: bytes, *, historical: bool = False):
        data = parse_json(raw)
        expected = {
            "repository_root",
            "repository",
            "source_revision",
            "files",
            "directories",
            "destination_baseline",
            "schema",
            "routing_profile",
            "authority_effect",
        }
        if set(data) != expected:
            raise IcMigrationRefusal("INVENTORY_INVALID", "inventory fields differ")
        if any(
            type(data[key]) is not list for key in ("files", "directories", "destination_baseline")
        ):
            raise IcMigrationRefusal("INVENTORY_INVALID", "arrays required")
        if any(
            type(row) is not dict or set(row) != {"source", "destination", "sha256", "size", "kind"}
            for row in data["files"]
        ):
            raise IcMigrationRefusal("INVENTORY_INVALID", "file row fields differ")
        try:
            data["files"] = tuple(InventoryFile(**row, historical=historical) for row in data["files"])
            data["directories"] = tuple(data["directories"])
            data["destination_baseline"] = tuple(tuple(row) for row in data["destination_baseline"])
            result = cls(**data, historical=historical)
        except (TypeError, KeyError) as exc:
            raise IcMigrationRefusal("INVENTORY_INVALID", "inventory rows malformed") from exc
        if result.bytes != raw:
            raise IcMigrationRefusal("INVENTORY_INVALID", "noncanonical inventory bytes")
        return result


@dataclass(frozen=True, slots=True)
class MigrationReceipt:
    state: str
    inventory_sha256: str
    files_verified: int
    bytes_verified: int
    authority_effect: str = "None"


def _scan(repo: Path, prefix: str, *, source: bool):
    root = safe_path(repo, prefix)
    files, directories = [], []
    if not root.exists():
        return files, directories

    def unavailable(error):
        raise IcMigrationRefusal("INVENTORY_SCAN_UNAVAILABLE", str(error)) from error

    for directory, subdirs, leaves in os.walk(root, followlinks=False, onerror=unavailable):
        current = Path(directory)
        relative = current.relative_to(repo).as_posix()
        safe_path(repo, relative)
        for name in sorted(subdirs):
            child = (current / name).relative_to(repo).as_posix()
            safe_path(repo, child)
            if child == CONTROL:
                continue
            if source:
                directories.append(child)
        subdirs[:] = sorted(
            name for name in subdirs if (current / name).relative_to(repo).as_posix() != CONTROL
        )
        files.extend(_scan_leaves(repo, current, leaves, source=source))
    all_paths = [row[0] for row in files] + directories
    if len({path_casefold(path) for path in all_paths}) != len(all_paths):
        raise IcMigrationRefusal("CASE_COLLISION", "filesystem paths collide")
    return sorted(files), sorted(directories)


def _scan_leaves(repo: Path, current: Path, leaves, *, source: bool):
    files = []
    for name in sorted(leaves):
        path = current / name
        relative = path.relative_to(repo).as_posix()
        if relative == LOCK:
            continue
        safe_path(repo, relative)
        stat = path.stat()
        if not path.is_file() or stat.st_nlink != 1:
            raise IcMigrationRefusal("FILE_KIND_REFUSED", relative)
        if source and (name.endswith("-wal") or name.endswith("-shm")):
            raise IcMigrationRefusal("SQLITE_NOT_QUIESCED", relative)
        files.append((relative, _hash(path), stat.st_size))
    return files


class IcMigration:
    def __init__(self, repository_root: Path, lease_manager):
        self.root = repository_root.absolute()
        if lease_manager.repository_root != self.root:
            raise IcMigrationRefusal("LEASE_IDENTITY_MISMATCH", "lease root differs")
        self.lease = lease_manager

    @staticmethod
    def _quiesced(value):
        if value is not True:
            raise IcMigrationRefusal(
                "WRITERS_NOT_QUIESCED", "stop all producers and close SQLite first"
            )

    def plan(self, repository: str, head_sha: str, *, quiesced: bool) -> MigrationInventory:
        self._quiesced(quiesced)
        with self.lease.claim_migration(repository, head_sha) as guard:
            guard.assert_held()
            if read_activation(self.root) is not None:
                raise IcMigrationRefusal("ALREADY_ACTIVATED", "use the retained inventory")
            sources, directories = _scan(self.root, "_intelligence", source=True)
            if not sources:
                raise IcMigrationRefusal("EMPTY_INVENTORY", "no legacy bytes to migrate")
            baseline, _ = _scan(self.root, "_ic", source=False)
            inventory = MigrationInventory(
                str(self.root),
                repository,
                head_sha,
                tuple(
                    InventoryFile(path, ic_relative_path(path), digest, size)
                    for path, digest, size in sources
                ),
                tuple(directories),
                tuple(baseline),
            )
            self._verify_source(inventory)
            guard.assert_held()
            return inventory

    def _verify_source(self, inventory):
        actual, directories = _scan(self.root, "_intelligence", source=True)
        expected = sorted((row.source, row.sha256, row.size) for row in inventory.files)
        if actual != expected or tuple(directories) != inventory.directories:
            raise IcMigrationRefusal("SOURCE_CHANGED", "source inventory no longer matches")

    def _atomic(self, relative: str, raw: bytes):
        destination = safe_path(self.root, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        safe_path(self.root, relative)
        temporary = destination.with_name(destination.name + ".tmp-" + uuid.uuid4().hex)
        try:
            with temporary.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            safe_path(self.root, relative)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)

    def _copy_file(self, source: Path, destination: Path):
        safe_path(self.root, source.relative_to(self.root).as_posix())
        safe_path(self.root, destination.relative_to(self.root).as_posix())
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Interrupted-process partials remain in the non-authoritative control
        # staging area, never among destination payloads. Resume rechecks the
        # frozen source and recopy; it neither trusts nor silently adopts a part.
        temporary = safe_path(self.root, CONTROL + "/staging/" + uuid.uuid4().hex + ".part")
        temporary.parent.mkdir(parents=True, exist_ok=True)
        try:
            with source.open("rb") as incoming, temporary.open("xb") as outgoing:
                shutil.copyfileobj(incoming, outgoing)
                outgoing.flush()
                os.fsync(outgoing.fileno())
            safe_path(self.root, destination.relative_to(self.root).as_posix())
            # Under the shared lease and explicit all-producer quiescence.
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)

    def _verify_destinations(self, inventory):
        actual, _ = _scan(self.root, "_ic", source=False)
        expected = {path: (digest, size) for path, digest, size in inventory.destination_baseline}
        for row in inventory.files:
            if row.destination in expected and expected[row.destination] != (row.sha256, row.size):
                raise IcMigrationRefusal("DESTINATION_CONFLICT", row.destination)
            expected[row.destination] = (row.sha256, row.size)
        if {path: (digest, size) for path, digest, size in actual} != expected:
            raise IcMigrationRefusal(
                "DESTINATION_CHANGED", "unverified or uninventoried destination bytes"
            )

    def apply(
        self, inventory: MigrationInventory, *, expected_digest: str, quiesced: bool
    ) -> MigrationReceipt:
        self._quiesced(quiesced)
        if type(inventory) is not MigrationInventory or inventory.digest != expected_digest:
            raise IcMigrationRefusal("INVENTORY_DIGEST_MISMATCH", "explicit pin differs")
        if inventory.repository_root != str(self.root):
            raise IcMigrationRefusal("INVENTORY_IDENTITY_MISMATCH", "foreign repository root")
        with self.lease.claim_migration(inventory.repository, inventory.source_revision) as guard:
            guard.assert_held()
            active = read_activation(self.root)
            if active is not None:
                if active["inventory_sha256"] != inventory.digest:
                    raise IcMigrationRefusal("INVENTORY_DIGEST_MISMATCH", "different activation")
                # New runtime writes are allowed after activation. No recopy/re-pin.
                return MigrationReceipt(
                    "ACTIVATED",
                    inventory.digest,
                    len(inventory.files),
                    sum(row.size for row in inventory.files),
                )
            self._verify_source(inventory)
            stored = safe_path(self.root, CONTROL + "/inventory.json")
            if stored.exists() and stored.read_bytes() != inventory.bytes:
                raise IcMigrationRefusal(
                    "INVENTORY_DIGEST_MISMATCH", "different interrupted inventory"
                )
            self._atomic(CONTROL + "/inventory.json", inventory.bytes)

            def state(value):
                guard.assert_held()
                self._atomic(
                    CONTROL + "/state.json",
                    json_bytes(
                        {
                            "state": value,
                            "inventory_sha256": inventory.digest,
                            "authority_effect": "None",
                        }
                    ),
                )

            state("PLANNED")
            for directory in inventory.directories:
                safe_path(self.root, ic_relative_path(directory)).mkdir(parents=True, exist_ok=True)
            for row in inventory.files:
                guard.assert_held()
                self._copy_inventory_row(row)
            state("COPIED")
            self._verify_source(inventory)
            self._verify_destinations(inventory)
            state("VERIFIED")
            guard.assert_held()
            activation = {
                "schema": "omega.ic.activation.v1",
                "state": "ACTIVATED",
                "authority_effect": "None",
                "repository_root": str(self.root),
                "source_revision": inventory.source_revision,
                "inventory_sha256": inventory.digest,
            }
            # The activation marker is the sole migration-status publication point.
            # No fallible journal update follows a successful custody publication.
            self._atomic(CONTROL + "/activation.json", json_bytes(activation))
            return MigrationReceipt(
                "ACTIVATED",
                inventory.digest,
                len(inventory.files),
                sum(row.size for row in inventory.files),
            )

    def _copy_inventory_row(self, row):
        source = safe_path(self.root, row.source)
        destination = safe_path(self.root, row.destination)
        if _hash(source) != row.sha256 or source.stat().st_size != row.size:
            raise IcMigrationRefusal("SOURCE_CHANGED", row.source)
        if destination.exists():
            if (
                not destination.is_file()
                or _hash(destination) != row.sha256
                or destination.stat().st_size != row.size
            ):
                raise IcMigrationRefusal("DESTINATION_CONFLICT", row.destination)
        else:
            self._copy_file(source, destination)

    def resolve_historical(self, origin: str, *, inventory_digest: str, sha256: str) -> bytes:
        inventory = _bound_inventory(self.root)
        if inventory is None or inventory.digest != inventory_digest:
            raise IcMigrationRefusal(
                "HISTORICAL_BINDING_MISMATCH", "explicit inventory pin required"
            )
        row = next((row for row in inventory.files if row.source == origin), None)
        if row is None or row.sha256 != sha256:
            raise IcMigrationRefusal(
                "HISTORICAL_BINDING_MISMATCH", "original locator/hash not in inventory"
            )
        found = False
        for relative in (origin, row.destination, historical_snapshot_path(origin)):
            path = safe_path(self.root, relative)
            try:
                raw = path.read_bytes()
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise IcMigrationRefusal("HISTORICAL_BYTES_UNAVAILABLE", origin) from exc
            found = True
            if len(raw) == row.size and hashlib.sha256(raw).hexdigest() == sha256:
                return raw
        raise IcMigrationRefusal(
            "HISTORICAL_BYTES_MISMATCH" if found else "HISTORICAL_BYTES_UNAVAILABLE", origin
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "apply", "resolve"))
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--repository", default="dbccpage/the_symbol_game")
    parser.add_argument("--head-sha")
    parser.add_argument(
        "--quiesced",
        action="store_true",
        help="operator assertion: all producers stopped and SQLite closed",
    )
    parser.add_argument("--inventory-sha256")
    parser.add_argument("--origin")
    parser.add_argument("--sha256")
    args = parser.parse_args(argv)
    from omega_engine_operating_system.application import CheckoutLeaseRefusal
    from omega_engine_operating_system.infrastructure.checkout_lease import CheckoutLeaseManager

    engine = IcMigration(
        args.repo_root,
        CheckoutLeaseManager(args.repo_root, state_root=args.repo_root / "_ic/odni/oeos_control"),
    )
    try:
        if args.action == "plan":
            inventory = engine.plan(args.repository, args.head_sha, quiesced=args.quiesced)
            # Never overwrite an operator's reviewed external inventory.
            with args.inventory.open("xb") as stream:
                stream.write(inventory.bytes)
            print(
                json_bytes(
                    {
                        "inventory_sha256": inventory.digest,
                        "files": len(inventory.files),
                        "state": "PLANNED",
                    }
                ).decode(),
                end="",
            )
        elif args.action == "apply":
            inventory = MigrationInventory.from_bytes(args.inventory.read_bytes())
            print(
                json_bytes(
                    asdict(
                        engine.apply(
                            inventory, expected_digest=args.inventory_sha256, quiesced=args.quiesced
                        )
                    )
                ).decode(),
                end="",
            )
        else:
            raw = engine.resolve_historical(
                args.origin, inventory_digest=args.inventory_sha256, sha256=args.sha256
            )
            sys.stdout.buffer.write(raw)
    except (IcMigrationRefusal, CheckoutLeaseRefusal) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
