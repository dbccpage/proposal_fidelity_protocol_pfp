"""Versioned IC storage routes; activation is a custody binding, not authority.

OMEGA_INTELLIGENCE_ROOT continues to name a repository, not a storage directory.
All active paths use _ic. Checkout-local metadata only binds historical custody.
"""

from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

from omega_engine_governance.domain.intelligence_community import (
    canonical_intelligence_route,
)

ROUTING_PROFILE = "omega.ic.routes.v1"
CONTROL = "_ic/odni/migration"
HISTORY = "_ic/odni/migrations/oewas007"
SNAPSHOT = "_ic/nara/historical/oewas007"
CASEFOLD_SHA256 = "9f569ad94b262a0f7143fe7636f79a7df03c53d8c5dc7d030cdbc263fc723946"

_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_HEAD = re.compile(r"[0-9a-f]{40}\Z")
_RESERVED = re.compile(r"(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?\Z", re.I)


class IcMigrationRefusal(ValueError):
    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


def json_bytes(value: object) -> bytes:
    """IC v1 profile: ASCII escaped, sorted keys, compact Python JSON plus LF.

    This named integer/string-only profile is not RFC 8785 or JSON-LD.
    """
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def parse_json(raw: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise IcMigrationRefusal("METADATA_INVALID", "duplicate JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, UnicodeError) as exc:
        raise IcMigrationRefusal("METADATA_INVALID", "invalid JSON") from exc
    if type(value) is not dict:
        raise IcMigrationRefusal("METADATA_INVALID", "object required")
    return value


@lru_cache(maxsize=1)
def _casefold_table():
    try:
        raw = (
            files("omega_engine_governance").joinpath("anomalon_councils/documentation/ic_casefold_v15_1.json").read_bytes()
        )
        if hashlib.sha256(raw).hexdigest() != CASEFOLD_SHA256:
            raise IcMigrationRefusal("CASEFOLD_RESOURCE_INVALID", "resource digest differs")
        table = parse_json(raw)
        if (
            set(table) != {"schema", "unicode_version", "producer", "mappings"}
            or table["schema"] != "omega.ic.casefold.v1"
            or table["unicode_version"] != "15.1.0"
            or type(table["mappings"]) is not dict
        ):
            raise IcMigrationRefusal("CASEFOLD_RESOURCE_INVALID", "resource profile differs")
        return table["mappings"]
    except OSError as exc:
        raise IcMigrationRefusal(
            "CASEFOLD_RESOURCE_UNAVAILABLE", "pinned Unicode table missing"
        ) from exc


def path_casefold(value: str) -> str:
    """Pinned Unicode 15.1 fold shared with native validation; no ambient fallback."""
    table = _casefold_table()
    return "".join(table.get(str(ord(char)), char) for char in value)


def historical_snapshot_path(origin: str) -> str:
    parts = relative_parts(origin)
    if len(parts) < 2 or parts[0] != "_intelligence":
        raise IcMigrationRefusal("UNSAFE_PATH", "historical locator required")
    return "/".join((SNAPSHOT, *parts[1:]))


def relative_parts(relative: str) -> tuple[str, ...]:
    if type(relative) is not str or not relative or "\\" in relative:
        raise IcMigrationRefusal("UNSAFE_PATH", "relative POSIX path required")
    parts = tuple(relative.split("/"))
    if any(
        not part
        or part in {".", ".."}
        or ":" in part
        or any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in part)
        or part[-1] in " ."
        or _RESERVED.fullmatch(part)
        for part in parts
    ):
        raise IcMigrationRefusal("UNSAFE_PATH", relative)
    return parts


def safe_path(repo_root: Path, relative: str) -> Path:
    """Reject existing ancestor junctions before performing any filesystem writes.

    Cooperative writer exclusion is required; this is not an OS sandbox against
    an attacker replacing directories concurrently with this check.
    """
    root = repo_root.absolute()
    result = root
    for component in ("", *relative_parts(relative)):
        if component:
            result = result / component
        try:
            stat = result.lstat()
        except FileNotFoundError:
            continue
        if result.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
            raise IcMigrationRefusal("REPARSE_REFUSED", str(result))
    return result


def ic_relative_path(legacy_relative: str) -> str:
    parts = relative_parts(legacy_relative)
    if len(parts) < 2 or parts[0] != "_intelligence":
        raise IcMigrationRefusal("UNSAFE_PATH", "legacy intelligence locator required")
    return canonical_intelligence_route(legacy_relative)


def historical_ic_relative_path(legacy_relative: str) -> str:
    """Original OEWAS-007 Woland layout, for byte-checked historical reads only."""
    parts = relative_parts(legacy_relative)
    current = ic_relative_path(legacy_relative)
    if parts[1] == "_woland":
        return "/".join(("_ic", "darpa", "woland", *parts[2:]))
    return current


def read_activation(repo_root: Path) -> dict | None:
    activation = safe_path(repo_root, CONTROL + "/activation.json")
    if not activation.exists():
        return None
    try:
        record = parse_json(activation.read_bytes())
        expected = {
            "schema",
            "state",
            "authority_effect",
            "repository_root",
            "source_revision",
            "inventory_sha256",
        }
        if (
            set(record) != expected
            or record["schema"] != "omega.ic.activation.v1"
            or record["state"] != "ACTIVATED"
            or record["authority_effect"] != "None"
            or record["repository_root"] != str(repo_root.absolute())
            or type(record["source_revision"]) is not str
            or not _HEAD.fullmatch(record["source_revision"])
            or type(record["inventory_sha256"]) is not str
            or not _DIGEST.fullmatch(record["inventory_sha256"])
        ):
            raise IcMigrationRefusal("ACTIVATION_INVALID", "activation fields differ")
        raw = safe_path(repo_root, CONTROL + "/inventory.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != record["inventory_sha256"]:
            raise IcMigrationRefusal("ACTIVATION_INVALID", "inventory digest differs")
        from .ic_migration import MigrationInventory

        MigrationInventory.from_bytes(raw)
        inventory = parse_json(raw)
        if (
            inventory.get("schema") != "omega.ic.inventory.v1"
            or inventory.get("routing_profile") != ROUTING_PROFILE
            or inventory.get("repository_root") != record["repository_root"]
            or inventory.get("source_revision") != record["source_revision"]
        ):
            raise IcMigrationRefusal("ACTIVATION_INVALID", "inventory identity differs")
        return record
    except OSError as exc:
        raise IcMigrationRefusal("ACTIVATION_INVALID", "activation resources unavailable") from exc


def intelligence_path(repo_root: Path, legacy_relative: str) -> Path:
    destination = ic_relative_path(legacy_relative)
    read_activation(repo_root)  # Existing invalid custody metadata must not be ignored.
    return safe_path(repo_root, destination)


def _bound_inventory(repo_root: Path):
    # Lazy import keeps the route policy usable by the executor without a cycle.
    from .ic_migration import MigrationInventory

    active = read_activation(repo_root)
    if active is not None:
        return MigrationInventory.from_bytes(
            safe_path(repo_root, CONTROL + "/inventory.json").read_bytes(), historical=True
        )
    receipt_path = safe_path(repo_root, HISTORY + "/receipt.json")
    if not receipt_path.exists():
        return None
    try:
        receipt = parse_json(receipt_path.read_bytes())
        if (
            set(receipt)
            != {"schema", "repository", "source_revision", "inventory_sha256", "authority_effect"}
            or receipt["schema"] != "omega.ic.portable_history.v1"
            or receipt["authority_effect"] != "None"
        ):
            raise IcMigrationRefusal(
                "HISTORICAL_BINDING_MISMATCH", "portable history fields differ"
            )
        raw = safe_path(repo_root, HISTORY + "/inventory.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != receipt["inventory_sha256"]:
            raise IcMigrationRefusal(
                "HISTORICAL_BINDING_MISMATCH", "portable inventory digest differs"
            )
        inventory = MigrationInventory.from_bytes(raw, historical=True)
        if (
            inventory.repository != receipt["repository"]
            or inventory.source_revision != receipt["source_revision"]
        ):
            raise IcMigrationRefusal(
                "HISTORICAL_BINDING_MISMATCH", "portable source identity differs"
            )
        return inventory
    except OSError as exc:
        raise IcMigrationRefusal(
            "HISTORICAL_BYTES_UNAVAILABLE", "portable binding unavailable"
        ) from exc


def _verify_bound_directory(repo_root: Path, inventory, origin: str) -> Path:
    from .ic_migration import _scan

    expected = sorted(
        (row.source[len(origin) + 1 :], row.sha256, row.size)
        for row in inventory.files
        if row.source.startswith(origin + "/")
    )
    for relative in dict.fromkeys((ic_relative_path(origin),
            historical_ic_relative_path(origin), historical_snapshot_path(origin))):
        path = safe_path(repo_root, relative)
        if path.is_dir():
            actual, _ = _scan(repo_root.absolute(), relative, source=False)
            remapped = sorted(
                (name[len(relative) + 1 :], digest, size) for name, digest, size in actual
            )
            if remapped == expected:
                return path
    raise IcMigrationRefusal("HISTORICAL_BYTES_MISMATCH", origin)


def intelligence_source_locator(repo_root: Path, path: Path) -> str:
    """Keep pre-cutover source/work identities for inventoried historical bundles.

    New canonical outputs retain new canonical locators. Mapping is explicit and
    byte-checked; it does not rewrite old database rows or receipt bodies.
    """
    try:
        relative = path.absolute().relative_to(repo_root.absolute()).as_posix()
    except ValueError as exc:
        raise IcMigrationRefusal("UNSAFE_PATH", "source outside repository") from exc
    safe_path(repo_root, relative)
    inventory = _bound_inventory(repo_root)
    if inventory is not None:
        for origin in inventory.directories:
            if relative in (ic_relative_path(origin), historical_ic_relative_path(origin),
                            historical_snapshot_path(origin)):
                if _verify_bound_directory(repo_root, inventory, origin) != path:
                    raise IcMigrationRefusal("HISTORICAL_BYTES_MISMATCH", origin)
                return origin
    return relative


def resolve_source_directory(repo_root: Path, locator: str) -> Path:
    """Resolve an old pending source through its bound map only if it is absent."""
    original = safe_path(repo_root, locator)
    if original.is_dir():
        return original
    inventory = _bound_inventory(repo_root)
    if inventory is None or locator not in inventory.directories:
        raise IcMigrationRefusal("HISTORICAL_BYTES_UNAVAILABLE", locator)
    return _verify_bound_directory(repo_root, inventory, locator)


def resolve_historical_path(repo_root: Path, origin: str) -> Path:
    """Navigate a frozen old locator through its inventory without rewriting it.

    Internal checksum consistency is not authentication or source admission.
    """
    inventory = _bound_inventory(repo_root)
    if inventory is None:
        raise IcMigrationRefusal("HISTORICAL_BINDING_MISMATCH", "no historical inventory")
    row = next((row for row in inventory.files if row.source == origin), None)
    if row is None:
        raise IcMigrationRefusal("HISTORICAL_BINDING_MISMATCH", "locator not inventoried")
    found = False
    for relative in dict.fromkeys((origin, row.destination, ic_relative_path(origin),
                                  historical_snapshot_path(origin))):
        path = safe_path(repo_root, relative)
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise IcMigrationRefusal("HISTORICAL_BYTES_UNAVAILABLE", origin) from exc
        found = True
        if len(raw) == row.size and hashlib.sha256(raw).hexdigest() == row.sha256:
            return path
    raise IcMigrationRefusal(
        "HISTORICAL_BYTES_MISMATCH" if found else "HISTORICAL_BYTES_UNAVAILABLE", origin
    )
