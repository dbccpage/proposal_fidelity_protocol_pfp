"""Check migration-map coverage and byte custody, not behavioral Rust parity.

AuthorityEffect: None. Run with ``python -m
omega_engine_pfp.infrastructure.migration_fitness``.

``--current-python`` separately checks recorded relocation provenance and
current static distributed ownership. Later canonical edits do not repin the
introduction blobs. Neither scope establishes native or behavioral parity.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from importlib.util import resolve_name
from pathlib import Path, PurePosixPath
from typing import Iterable

MAP_SCHEMA = "omega.symbol-game.rust-migration-map.v1"
PACKAGE = "omega_engine_pfp/"
DEFAULT_MAP = PACKAGE + "documentation/rust_migration/file_map.json"
DEFAULT_MANIFEST = PACKAGE + "migration_manifest.json"
MANIFEST_SCHEMA = "omega.symbol-game.migration-manifest.v2"
# The relocated pilot corpus makes the complete map about 15 MB.
MAX_MAP_BYTES = 16 * 1024 * 1024
MAX_SOURCE_BYTES = 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
REVISION = re.compile(r"[0-9a-f]{40}\Z")
PYTHON_OWNERS = {"PFP": "omega_engine_pfp/", "Woland": "omega_engine_woland/"}
RETIRED_PYTHON_ROOTS = (
    "omega_engine_education.pfp", "omega_engine_education.pilots", "omega_engine_symbol_game"
)
CURRENT_PYTHON_SCOPE = "static Python ownership and immutable migration provenance only"
HISTORICAL_SNAPSHOT_PARTS = frozenset({"source_snapshot", "frozen_sources", "baseline_bytes"})
HISTORICAL_PYTHON_PREFIXES = ("omega_engine_pfp/infrastructure/tower_evidence/level_engine/v1/",)
CURRENT_PYTHON_LIMITS = (
    "Static tracked Python selected by pyproject package discovery or explicit package data; source_snapshot, frozen_sources, baseline_bytes and level-engine v1 evidence are historical snapshots.",
    "Computed dynamic imports, undistributed host scripts and actual installed-wheel behavior are not established.",
    "No dynamic route closure, native parity, behavioral equivalence or full migration completion is asserted.",
)
NATIVE_OWNER_STATUSES = frozenset(
    {"native-owner", "native-implemented", "native-parity-established", "native-delegated"}
)


@dataclass(frozen=True)
class MigrationFinding:
    code: str
    path: str
    detail: str


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _bounded_bytes(path: Path, limit: int) -> bytes:
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("file exceeds inspection byte limit")
    return raw


def _repository_path(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("expected a nonempty repository-relative POSIX path")
    relative = PurePosixPath(value)
    if relative.is_absolute() or any(part in {".", ".."} for part in value.split("/")):
        raise ValueError("path must not be absolute or contain dot segments")
    if any(not part for part in value.split("/")) or ":" in value:
        raise ValueError("path must have canonical repository-relative segments")
    path = root / relative
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError) as error:
        raise ValueError("path cannot be resolved") from error
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("path escapes the repository through a symlink")
    return path


def tracked_symbol_game_paths(root: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "omega_engine_pfp"],
        cwd=root,
        capture_output=True,
        check=True,
        timeout=30,
    )
    return tuple(path.decode("utf-8") for path in result.stdout.split(b"\0") if path)


def check_file_map(
    root: Path,
    map_path: Path | None = None,
    *,
    tracked_paths: Iterable[str] | None = None,
) -> tuple[MigrationFinding, ...]:
    """Refuse missing/duplicate rows, stale source bytes and absent native targets.

    ``tracked_paths`` is an explicit inventory injection for tests. Production
    uses the Git index, including staged new paths. Rust targets must be file
    paths; a ``::symbol`` suffix is retained as descriptive scope only and is
    not proof that the symbol implements equivalent behavior.
    """
    root = root.resolve()
    map_path = map_path or root / DEFAULT_MAP
    findings: list[MigrationFinding] = []
    try:
        raw = _bounded_bytes(map_path, MAX_MAP_BYTES)
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError("UTF-8 BOM is forbidden")
        document = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
        if not isinstance(document, dict) or document.get("schema_version") != MAP_SCHEMA:
            raise ValueError("unknown migration-map schema")
        rows = document.get("files")
        if not isinstance(rows, list) or not rows:
            raise ValueError("files must be a nonempty array")
        inventory = set(tracked_symbol_game_paths(root) if tracked_paths is None else tracked_paths)
        if not inventory or any(
            not isinstance(path, str) or not path.startswith(PACKAGE) for path in inventory
        ):
            raise ValueError("tracked inventory must be nonempty and scoped to Symbol Game")
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as error:
        return (MigrationFinding("MAP_UNAVAILABLE", str(map_path), str(error)),)

    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            findings.append(MigrationFinding("BAD_ROW", str(index), "expected an object"))
            continue
        source = row.get("path")
        try:
            source_path = _repository_path(root, source)
            if not source.startswith(PACKAGE):
                raise ValueError("source must be inside Symbol Game")
        except ValueError as error:
            findings.append(MigrationFinding("BAD_SOURCE_PATH", str(source), str(error)))
            continue
        if source in seen:
            findings.append(MigrationFinding("DUPLICATE_SOURCE", source, "multiple map rows"))
        seen.add(source)
        if source not in inventory:
            findings.append(MigrationFinding("UNTRACKED_SOURCE", source, "not in Git inventory"))
        if not source_path.is_file():
            findings.append(MigrationFinding("SOURCE_MISSING", source, "source is not a file"))
        for field in ("status", "action"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                findings.append(
                    MigrationFinding("BAD_ROW_FIELD", source, f"{field} must be a nonempty string")
                )
        digest = row.get("source_sha256")
        if digest is not None or source != DEFAULT_MAP:
            if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
                findings.append(
                    MigrationFinding("BAD_SOURCE_DIGEST", source, "expected lowercase SHA-256")
                )
            elif source_path.is_file():
                try:
                    actual = hashlib.sha256(
                        _bounded_bytes(source_path, MAX_SOURCE_BYTES)
                    ).hexdigest()
                    if actual != digest:
                        findings.append(
                            MigrationFinding(
                                "SOURCE_CHANGED", source, "source bytes differ from reviewed map"
                            )
                        )
                except (OSError, ValueError) as error:
                    findings.append(MigrationFinding("SOURCE_UNAVAILABLE", source, str(error)))
        targets = row.get("rust_targets")
        if not isinstance(targets, list):
            findings.append(
                MigrationFinding("BAD_TARGETS", source, "rust_targets must be an array")
            )
            continue
        if (
            isinstance(row.get("status"), str)
            and row["status"] in NATIVE_OWNER_STATUSES
            and not targets
        ):
            findings.append(
                MigrationFinding(
                    "NATIVE_OWNER_MISSING", source, "native owner status requires a target file"
                )
            )
        for target in targets:
            try:
                if not isinstance(target, str):
                    raise ValueError("target must be a file path string")
                target_path_text = target.split("::", 1)[0]
                target_path = _repository_path(root, target_path_text)
                if not target_path_text.startswith("omega_engine/crates_rs/"):
                    raise ValueError("native owner must be in crates_rs")
                if not target_path.is_file():
                    raise ValueError("native target file does not exist")
            except ValueError as error:
                findings.append(MigrationFinding("BAD_RUST_TARGET", source, f"{target}: {error}"))
    for missing in sorted(inventory - seen, key=lambda value: value.encode("utf-8")):
        findings.append(MigrationFinding("UNMAPPED_SOURCE", missing, "tracked file has no map row"))
    return tuple(findings)


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, check=True, timeout=30
    ).stdout


def _blob(root: Path, revision: str, path: str) -> bytes:
    identity = f"{revision}:{path}"
    if int(_git(root, "cat-file", "-s", identity)) > MAX_SOURCE_BYTES:
        raise ValueError("historical source exceeds inspection byte limit")
    return _git(root, "cat-file", "blob", identity)


def _ancestor(root: Path, earlier: str, later: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", earlier, later],
        cwd=root,
        capture_output=True,
        timeout=30,
    )
    if result.returncode not in (0, 1):
        raise subprocess.CalledProcessError(result.returncode, result.args, stderr=result.stderr)
    return result.returncode == 0


def _package_policy(root: Path) -> tuple[list[str], list[str], set[str]]:
    try:
        import tomllib
    except ImportError:  # Python 3.10 retains the default gate without this optional parser.
        import tomli as tomllib
    project = tomllib.loads(_bounded_bytes(root / "pyproject.toml", MAX_SOURCE_BYTES).decode())
    policy = project["tool"]["setuptools"]["packages"]["find"]
    if policy.get("where", ["."]) != ["."] or policy.get("namespaces", True) is not True:
        raise ValueError("current Python scope requires root-based namespace package discovery")
    include, exclude = policy.get("include", ["*"]), policy.get("exclude", [])
    if any(
        type(items) is not list or any(type(x) is not str for x in items)
        for items in (include, exclude)
    ):
        raise ValueError("invalid setuptools package include/exclude patterns")
    # Some retained public pilots live below a tests namespace. Setuptools ships
    # their explicitly declared Python data even though package discovery omits
    # tests. Inspect those bytes too, without including the surrounding estate.
    config = project["tool"]["setuptools"]
    data_sources: set[str] = set()
    for package, patterns in config.get("package-data", {}).items():
        if not _package_eligible(package.replace(".", "/") + "/__init__.py", (include, exclude, set())):
            continue
        base = root / package.replace(".", "/")
        omitted = config.get("exclude-package-data", {})
        exclusions = omitted.get("*", []) + omitted.get(package, [])
        for pattern in patterns:
            for path in base.glob(pattern):
                if path.is_file() and path.suffix == ".py" and not any(
                    fnmatch.fnmatchcase(path.relative_to(base).as_posix(), p) for p in exclusions
                ):
                    data_sources.add(path.relative_to(root).as_posix())
    return include, exclude, data_sources


def _package_eligible(path: str, policy: tuple[list[str], list[str], set[str]]) -> bool:
    package = ".".join(PurePosixPath(path).parts[:-1])
    include, exclude, data_sources = policy
    return path in data_sources or (
        bool(package)
        and any(fnmatch.fnmatchcase(package, p) for p in include)
        and not any(fnmatch.fnmatchcase(package, p) for p in exclude)
    )


def _static_imports(source: str, path: str) -> set[str]:
    """Resolve declared imports and literal importlib calls; never execute the source."""
    tree = ast.parse(source)
    package = ".".join(PurePosixPath(path).parts[:-1])
    names: set[str] = set()
    # Conservatively retain declared possibilities: later rebinding cannot erase
    # an earlier literal call. This remains static inspection, not execution.
    aliases: dict[str, set[str]] = {"__import__": {"__import__"}}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
                aliases.setdefault(alias.asname or alias.name.split(".")[0], set()).add(
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom):
            base = (
                resolve_name("." * node.level + (node.module or ""), package)
                if node.level
                else (node.module or "")
            )
            names.add(base)
            for alias in node.names:
                full = f"{base}.{alias.name}"
                names.add(full)
                aliases.setdefault(alias.asname or alias.name, set()).add(full)

    def qualified(node: ast.AST) -> set[str]:
        if isinstance(node, ast.Name):
            return aliases.get(node.id, {node.id})
        if isinstance(node, ast.Attribute):
            return {f"{base}.{node.attr}" for base in qualified(node.value)}
        return set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    aliases.setdefault(target.id, set()).update(qualified(node.value))
        elif isinstance(node, ast.Call) and qualified(node.func).intersection(
            {
                "importlib.import_module",
                "__import__",
            }
        ):
            target = (
                node.args[0]
                if node.args
                else next((item.value for item in node.keywords if item.arg == "name"), None)
            )
            if isinstance(target, ast.Constant) and type(target.value) is str:
                name = target.value
                if name.startswith("."):
                    context = (
                        node.args[1]
                        if len(node.args) > 1
                        else next(
                            (item.value for item in node.keywords if item.arg == "package"), None
                        )
                    )
                    if not isinstance(context, ast.Constant) or type(context.value) is not str:
                        continue  # Computed context is outside this declared static scope.
                    name = resolve_name(name, context.value)
                names.add(name)
    return names


def check_current_python_ownership(
    root: Path, manifest_path: Path | None = None
) -> tuple[MigrationFinding, ...]:
    """Check declared moves against immutable Git history and current static owners.

    A canonical owner may evolve after introduction. Its current bytes are NOT
    compared with the historical destination digest. Installed behavior, dynamic
    dispatch, native parity and complete architectural migration remain separate.
    """
    root = root.resolve()
    manifest_path = manifest_path or root / DEFAULT_MANIFEST
    try:
        document = json.loads(
            _bounded_bytes(manifest_path, MAX_MAP_BYTES).decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
        if type(document) is not dict or document.get("schema_version") != MANIFEST_SCHEMA:
            raise ValueError("unknown migration manifest schema")
        rows = document.get("current_python_source_dispositions")
        if type(rows) is not list or not rows:
            raise ValueError("current source dispositions must be nonempty")
        policy = _package_policy(root)
    except (OSError, UnicodeError, ValueError, KeyError, ImportError) as error:
        return (
            MigrationFinding("CURRENT_DISPOSITIONS_UNAVAILABLE", str(manifest_path), str(error)),
        )
    try:
        inventory = set(_git(root, "ls-files", "-z").decode("utf-8").split("\0")) - {""}
        head = _git(root, "rev-parse", "HEAD").decode().strip()
    except (OSError, UnicodeError, subprocess.SubprocessError) as error:
        return (MigrationFinding("PROVENANCE_HISTORY_UNAVAILABLE", "", str(error)),)
    findings: list[MigrationFinding] = []
    sources: set[str] = set()
    destinations: set[str] = set()
    retired = set(RETIRED_PYTHON_ROOTS)
    known_revisions: set[str] = set()
    known_ancestry: set[tuple[str, str]] = set()
    for name in RETIRED_PYTHON_ROOTS:
        path = name.replace(".", "/")
        if (root / path).exists() or any(item.startswith(path + "/") for item in inventory):
            findings.append(
                MigrationFinding(
                    "RETIRED_SOURCE_PRESENT", path, "retired Python application package remains"
                )
            )
    for row in rows:
        try:
            if type(row) is not dict:
                raise ValueError("disposition must be an object")
            source, destination = row["source"], row["destination"]
            old, current = _repository_path(root, source), _repository_path(root, destination)
            if (
                not source.endswith(".py")
                or not destination.endswith(".py")
                or source == destination
            ):
                raise ValueError("move must name distinct Python source/destination files")
            retired.add(source[:-3].replace("/", ".").removesuffix(".__init__"))
            for value, seen, code in (
                (source, sources, "DUPLICATE_SOURCE"),
                (destination, destinations, "DUPLICATE_DESTINATION"),
            ):
                if value.casefold() in seen:
                    findings.append(
                        MigrationFinding(code, value, "duplicate or case-disguised move")
                    )
                seen.add(value.casefold())
            owner = PYTHON_OWNERS.get(row.get("owner"))
            if owner is None or not destination.startswith(owner):
                findings.append(
                    MigrationFinding(
                        "CURRENT_OWNER_INVALID",
                        destination,
                        "explicit owner must match canonical PFP/Woland prefix",
                    )
                )
            if current.resolve().relative_to(root).as_posix() != destination:
                findings.append(
                    MigrationFinding(
                        "CURRENT_OWNER_INVALID",
                        destination,
                        "destination resolves to a different owner path",
                    )
                )
            if old.exists() or old.with_suffix("").is_dir() or source in inventory:
                findings.append(
                    MigrationFinding("RETIRED_SOURCE_PRESENT", source, "old active module remains")
                )
            if destination not in inventory:
                findings.append(
                    MigrationFinding(
                        "CURRENT_DESTINATION_UNTRACKED",
                        destination,
                        "canonical destination is not Git tracked",
                    )
                )
            if not current.is_file():
                findings.append(
                    MigrationFinding("CURRENT_DESTINATION_MISSING", destination, "owner is absent")
                )
            if not _package_eligible(destination, policy):
                findings.append(
                    MigrationFinding(
                        "CURRENT_DESTINATION_UNPACKAGED",
                        destination,
                        "owner is outside current setuptools package discovery",
                    )
                )
            if (HISTORICAL_SNAPSHOT_PARTS.intersection(PurePosixPath(destination).parts)
                or destination.startswith(HISTORICAL_PYTHON_PREFIXES)):
                findings.append(
                    MigrationFinding(
                        "CURRENT_OWNER_INVALID",
                        destination,
                        "historical snapshot cannot be the current active owner",
                    )
                )
            original, introduction = row["original_revision"], row["destination_revision"]
            for revision in (original, introduction):
                if type(revision) is not str or REVISION.fullmatch(revision) is None:
                    raise ValueError("provenance requires immutable full Git commit IDs")
                if revision not in known_revisions:
                    if _git(root, "cat-file", "-t", revision).strip() != b"commit":
                        raise ValueError("provenance revision is not a commit")
                    known_revisions.add(revision)
            ancestors_valid = True
            for pair in ((original, introduction), (introduction, head)):
                if pair not in known_ancestry:
                    if not _ancestor(root, *pair):
                        ancestors_valid = False
                        break
                    known_ancestry.add(pair)
            if not ancestors_valid:
                findings.append(
                    MigrationFinding(
                        "PROVENANCE_ANCESTRY_INVALID",
                        source,
                        "source/introduction/current ancestry does not hold",
                    )
                )
                continue
            if (
                _git(root, "ls-tree", "--name-only", introduction, "--", source).strip()
                or _git(root, "ls-tree", "--name-only", original, "--", destination).strip()
            ):
                findings.append(
                    MigrationFinding(
                        "PROVENANCE_MOVE_INVALID",
                        source,
                        "introduction did not retire the old owner or destination already existed",
                    )
                )
            for revision, path, field in (
                (original, source, "original_source_sha256"),
                (introduction, destination, "destination_sha256"),
            ):
                expected = row[field]
                if type(expected) is not str or SHA256.fullmatch(expected) is None:
                    raise ValueError("provenance requires lowercase SHA-256 digests")
                if hashlib.sha256(_blob(root, revision, path)).hexdigest() != expected:
                    findings.append(
                        MigrationFinding(
                            "PROVENANCE_DIGEST_MISMATCH",
                            path,
                            f"{field} differs from immutable Git blob",
                        )
                    )
        except (OSError, UnicodeError, subprocess.SubprocessError) as error:
            findings.append(
                MigrationFinding(
                    "PROVENANCE_HISTORY_UNAVAILABLE", str(row.get("source", "")), str(error)
                )
            )
        except (ValueError, KeyError, TypeError) as error:
            findings.append(MigrationFinding("BAD_CURRENT_DISPOSITION", str(row), str(error)))
    for path in sorted(inventory):
        if not path.endswith(".py") or not _package_eligible(path, policy):
            continue
        if (HISTORICAL_SNAPSHOT_PARTS.intersection(PurePosixPath(path).parts)
            or path.startswith(HISTORICAL_PYTHON_PREFIXES)):
            continue
        try:
            imports = _static_imports(
                _bounded_bytes(_repository_path(root, path), MAX_SOURCE_BYTES).decode("utf-8-sig"),
                path,
            )
            for name in sorted(imports):
                if any(name == old or name.startswith(old + ".") for old in retired):
                    findings.append(MigrationFinding("RETIRED_IMPORT", path, name))
        except (OSError, UnicodeError, ValueError, SyntaxError, ImportError) as error:
            findings.append(MigrationFinding("CURRENT_IMPORT_SOURCE_UNAVAILABLE", path, str(error)))
    return tuple(findings)


def _find_repository() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            return parent
    raise ValueError("no Git repository contains this gate")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--map", type=Path)
    parser.add_argument("--current-python", action="store_true", help=CURRENT_PYTHON_SCOPE)
    parser.add_argument("--manifest", type=Path, help="current Python source-dispositions manifest")
    args = parser.parse_args(argv)
    if (args.current_python and args.map) or (args.manifest and not args.current_python):
        parser.error("--map and --current-python/--manifest are separate scopes")
    try:
        root = args.repo_root or _find_repository()
        findings = (
            check_current_python_ownership(root, args.manifest)
            if args.current_python
            else check_file_map(root, args.map)
        )
    except (OSError, ValueError) as error:
        findings = (MigrationFinding("MAP_UNAVAILABLE", "", str(error)),)
    result = {
        "authority_effect": "None",
        "scope": CURRENT_PYTHON_SCOPE if args.current_python else "inventory and byte custody only",
        "status": "REFUSED" if findings else "PASS",
        "findings": [asdict(finding) for finding in findings],
    }
    if args.current_python:
        result["limitations"] = list(CURRENT_PYTHON_LIMITS)
    print(json.dumps(result, sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
