#!/usr/bin/env python3
"""Check the v1.1RC reference contracts and their monograph bindings.

This checks metadata, source bytes, links and a Rust trait block's compilation.
It does not verify mathematical theorems, signatures, density positivity, DPO
confluence, or an implemented operad engine. AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit

REFERENCE_DIRECTORY = Path("pfp/fixtures/operad_specification")
MONOGRAPH = Path("pfp/documentation/oepfp_v1_1_rc_specification.md")
SPECIFICATION_SOURCE = Path("pfp/domain/operad/specification.py")
SCOPE = (
    "strict reference metadata; JSON/YAML and generated schema parity; seven artifact byte "
    "hashes; embedded Python/YAML parity; monograph local file/line links and math delimiters; "
    "Rust interface metadata compilation only"
)


class ReferenceError(ValueError):
    """A missing, ambiguous, stale, malformed, or uncompiled reference."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReferenceError(message)


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(token: str) -> None:
    raise ReferenceError(f"non-finite JSON constant: {token}")


def read_json(path: Path) -> Any:
    return json.loads(
        path.read_bytes(), object_pairs_hook=unique_object, parse_constant=reject_constant
    )


def canonical_json(value: Any) -> str:
    # Typed parity: JSON true and 1 must not compare equal through Python equality.
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def read_unique_yaml(path: Path) -> Any:
    import yaml

    class UniqueLoader(yaml.SafeLoader):
        pass

    def mapping(loader: UniqueLoader, node: Any, deep: bool = False) -> dict[str, Any]:
        loader.flatten_mapping(node)
        result: dict[str, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            require(isinstance(key, str), "YAML mapping keys must be strings")
            require(key not in result, f"duplicate YAML key: {key}")
            result[key] = loader.construct_object(value_node, deep=deep)
        return result

    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    return yaml.load(path.read_bytes(), Loader=UniqueLoader)


def repository_file(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    require(
        bool(relative)
        and not path.is_absolute()
        and "\\" not in relative
        and ":" not in path.parts[0]
        and path.as_posix() == relative
        and all(part not in {".", ".."} for part in relative.split("/")),
        f"noncanonical repository path: {relative!r}",
    )
    candidate = root.joinpath(*path.parts).resolve(strict=True)
    require(candidate.is_relative_to(root), f"path escapes repository: {relative}")
    require(candidate.is_file(), f"reference is not a file: {relative}")
    return candidate


def reference_metadata(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    import jsonschema

    from pfp.domain.operad import specification

    require(
        Path(specification.__file__).resolve() == (root / SPECIFICATION_SOURCE).resolve(),
        "ArchitectureSpec import does not belong to the selected repository root",
    )
    ArchitectureSpec = specification.ArchitectureSpec
    parse_architecture_json = specification.parse_architecture_json

    base = root / REFERENCE_DIRECTORY
    reference = base / "reference.json"
    value = read_json(reference)
    require(
        canonical_json(value) == canonical_json(read_unique_yaml(base / "reference.yaml")),
        "JSON/YAML reference fixture mismatch",
    )
    parsed = parse_architecture_json(reference.read_bytes())
    schema = read_json(base / "architecture_spec.schema.json")
    require(
        canonical_json(schema) == canonical_json(ArchitectureSpec.model_json_schema()),
        "generated ArchitectureSpec JSON schema is stale",
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)
    require(len(parsed.artifacts) == 7, "reference must bind exactly seven artifacts")
    artifacts = []
    for artifact in parsed.artifacts:
        raw = repository_file(root, artifact.path).read_bytes()
        require(len(raw) == artifact.byte_length, f"artifact byte length mismatch: {artifact.path}")
        observed = hashlib.sha256(raw).hexdigest()
        require(observed == artifact.sha256, f"artifact SHA-256 mismatch: {artifact.path}")
        artifacts.append({"path": artifact.path, "sha256": observed, "byte_length": len(raw)})
    return value, {
        "status": "PASS",
        "json_yaml_parity": "exact typed JSON values",
        "architecture_spec": "strict metadata validation only",
        "json_schema": "generated parity and Draft 2020-12 validation",
        "artifacts_checked": artifacts,
    }


def fenced_block(text: str, language: str) -> str:
    pattern = rf"^```{re.escape(language)}[ \t]*\r?\n(.*?)^```[ \t]*(?:\r?$)"
    blocks = re.findall(pattern, text, flags=re.MULTILINE | re.DOTALL)
    require(len(blocks) == 1, f"expected one fenced {language} block, found {len(blocks)}")
    return blocks[0]


def embedded_parity(root: Path, text: str) -> dict[str, Any]:
    require("<!--" not in text, "monograph contains an unresolved HTML marker/comment")
    for language, relative in [
        ("python", SPECIFICATION_SOURCE),
        ("yaml", REFERENCE_DIRECTORY / "reference.yaml"),
    ]:
        require(
            fenced_block(text, language).encode("utf-8") == (root / relative).read_bytes(),
            f"embedded {language} block differs from {relative.as_posix()}",
        )
    return {"status": "PASS", "python": "exact bytes", "yaml": "exact bytes"}


def local_links(root: Path, document: Path, text: str) -> dict[str, Any]:
    checked = 0
    line_links = 0
    for target in re.findall(r"\]\(([^)]+)\)", text):
        target = target.strip().removeprefix("<").removesuffix(">")
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        file = (document.parent / unquote(parsed.path)).resolve(strict=True)
        require(file.is_relative_to(root) and file.is_file(), f"invalid local link: {target}")
        if parsed.fragment.startswith("L"):
            fragment = re.fullmatch(r"L([1-9][0-9]*)(?:-L([1-9][0-9]*))?", parsed.fragment)
            require(fragment is not None, f"invalid line-link fragment: {target}")
            if fragment is None:
                raise ReferenceError(f"invalid line-link fragment: {target}")
            first = int(fragment[1])
            last = int(fragment[2] or fragment[1])
            require(
                1 <= first <= last <= len(file.read_bytes().splitlines()),
                f"line link is outside source: {target}",
            )
            line_links += 1
        checked += 1
    require(checked > 0, "no relative file links found; the selector may be wrong")
    return {"status": "PASS", "files_checked": checked, "line_links_checked": line_links}


def math_delimiters(text: str) -> dict[str, Any]:
    prose = re.sub(r"^```[^\n]*\n.*?^```[^\n]*$", "", text, flags=re.MULTILINE | re.DOTALL)
    prose = re.sub(r"`[^`\n]*`", "", prose)
    stack: list[str] = []
    pairs = {r"\)": r"\(", r"\]": r"\["}
    tokens = re.findall(r"(?<!\\)(?:\\[()[\]]|\${1,2})", prose)
    for token in tokens:
        if token in {r"\(", r"\["}:
            require(not stack, f"nested math delimiter: {token}")
            stack.append(token)
        elif token in pairs:
            require(bool(stack) and stack[-1] == pairs[token], f"unmatched math delimiter: {token}")
            stack.pop()
        elif stack and stack[-1] == token:
            stack.pop()
        else:
            require(not stack, f"nested math delimiter: {token}")
            stack.append(token)
    require(not stack, f"unclosed math delimiter: {stack}")
    require(bool(tokens), "no math delimiters found; the selector may be wrong")
    return {"status": "PASS", "delimiters_checked": len(tokens), "code_blocks_excluded": True}


def process(argv: list[str], root: Path, records: list[dict[str, Any]]) -> str:
    record: dict[str, Any] = {"argv": argv, "command": shlex.join(argv), "cwd": str(root)}
    records.append(record)
    try:
        completed = subprocess.run(
            argv, cwd=root, capture_output=True, text=True, check=False, timeout=30
        )
    except subprocess.TimeoutExpired as error:
        record.update(exit_code=None, status="TIMEOUT", timeout_seconds=30)
        raise ReferenceError(f"subprocess exceeded 30 seconds: {argv[0]}") from error
    except OSError as error:
        record.update(exit_code=None, status="NOT_STARTED", error=str(error))
        raise ReferenceError(f"cannot start subprocess: {argv[0]}: {error}") from error
    record.update(exit_code=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
    require(completed.returncode == 0, f"subprocess exited {completed.returncode}: {argv[0]}")
    return completed.stdout.strip()


def rust_reference(
    root: Path, text: str, rustc: str | None, records: list[dict[str, Any]]
) -> dict[str, Any]:
    require(bool(rustc), "rustc is unavailable; provide --rustc or configure PATH")
    compiler = shutil.which(rustc or "")
    require(compiler is not None, f"rustc is missing or not executable: {rustc}")
    compiler = str(Path(compiler or "").resolve(strict=True))
    version = process([compiler, "--version"], root, records)
    block = fenced_block(text, "rust").encode("utf-8")
    with tempfile.TemporaryDirectory(prefix="oepfp-reference-") as directory:
        source = Path(directory) / "reference.rs"
        output = Path(directory) / "reference.rmeta"
        source.write_bytes(block)
        process(
            [
                compiler,
                "--edition",
                "2021",
                "--crate-type",
                "lib",
                "--emit",
                "metadata",
                "--crate-name",
                "oepfp_v1_1rc_reference",
                str(source),
                "-o",
                str(output),
            ],
            root,
            records,
        )
        require(output.is_file() and output.stat().st_size > 0, "rustc emitted no metadata")
    return {
        "status": "PASS",
        "rustc": version,
        "source_sha256": hashlib.sha256(block).hexdigest(),
        "scope": "trait/reference syntax compilation only; no engine behavior checked",
    }


def versions() -> dict[str, str]:
    result = {"python": platform.python_version(), "checker": "oepfp.references.v1"}
    for package in ["pydantic", "PyYAML", "jsonschema"]:
        try:
            result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result[package] = "NOT_INSTALLED"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--rustc", default=shutil.which("rustc"))
    args = parser.parse_args(argv)
    command = list(getattr(sys, "orig_argv", [sys.executable, *sys.argv]))
    receipt: dict[str, Any] = {
        "schema_version": "oepfp.reference-check-receipt.v1",
        "scope": SCOPE,
        "authority_effect": "None",
        "mathematical_claims_verified": False,
        "tests_executed": 0,
        "argv": command,
        "command": shlex.join(command),
        "versions": versions(),
        "checks": {},
        "subprocesses": [],
    }
    try:
        root = args.repository_root.resolve(strict=True)
        require(root.is_dir(), "repository root must be a directory")
        receipt["repository_root"] = str(root)
        sys.path.insert(0, str(root))
        _, receipt["checks"]["reference_metadata"] = reference_metadata(root)
        document = root / MONOGRAPH
        text = document.read_bytes().decode("utf-8")
        receipt["checks"]["embedded_parity"] = embedded_parity(root, text)
        receipt["checks"]["relative_links"] = local_links(root, document, text)
        receipt["checks"]["math_delimiters"] = math_delimiters(text)
        receipt["checks"]["rust_interface"] = rust_reference(
            root, text, args.rustc, receipt["subprocesses"]
        )
    except Exception as error:
        receipt.update(
            status="FAIL", error_type=type(error).__name__, error=str(error), exit_code=1
        )
    else:
        receipt.update(status="PASS", exit_code=0)
    print(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False))
    return receipt["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
