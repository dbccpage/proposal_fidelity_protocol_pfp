"""Multi-format file validator for repository changed files.

Validates:
1. JSON files (syntax parsing via standard json module).
2. TOML files (syntax parsing via standard tomllib module).
3. YAML files (syntax parsing via PyYAML if available).
4. Jupyter Notebooks (structural validation of cell schemas).
5. Markdown files (detection of corrupted LaTeX escape control characters).

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Tuple

try:
    import tomllib
except ImportError:
    tomllib = None  # type: ignore

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

# Control characters excluding standard whitespace (\t, \n, \r)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def validate_json_file(file_path: Path) -> Tuple[bool, str]:
    """Validate JSON file syntax."""
    try:
        content = file_path.read_text(encoding="utf-8")
        json.loads(content)
        return True, ""
    except Exception as exc:
        return False, f"JSON syntax error in {file_path.name}: {exc}"


def validate_toml_file(file_path: Path) -> Tuple[bool, str]:
    """Validate TOML file syntax."""
    if tomllib is None:
        return True, ""
    try:
        content = file_path.read_text(encoding="utf-8")
        tomllib.loads(content)
        return True, ""
    except Exception as exc:
        return False, f"TOML syntax error in {file_path.name}: {exc}"


def validate_yaml_file(file_path: Path) -> Tuple[bool, str]:
    """Validate YAML file syntax."""
    if yaml is None:
        return True, ""
    try:
        content = file_path.read_text(encoding="utf-8")
        yaml.safe_load(content)
        return True, ""
    except Exception as exc:
        return False, f"YAML syntax error in {file_path.name}: {exc}"


def validate_notebook_file(file_path: Path) -> Tuple[bool, str]:
    """Validate notebook cell structure without executing cells."""
    try:
        content = file_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except Exception as exc:
        return False, f"Notebook JSON error in {file_path.name}: {exc}"

    if not isinstance(data, dict):
        return False, f"Notebook {file_path.name} root must be a JSON object"

    cells = data.get("cells")
    if not isinstance(cells, list):
        return False, f"Notebook {file_path.name} missing 'cells' array"

    for idx, cell in enumerate(cells):
        if not isinstance(cell, dict):
            return False, f"Notebook {file_path.name} cell {idx} is not an object"
        cell_type = cell.get("cell_type")
        if cell_type not in ("code", "markdown", "raw"):
            return False, f"Notebook {file_path.name} cell {idx} has invalid cell_type: {cell_type}"
        if "source" not in cell:
            return False, f"Notebook {file_path.name} cell {idx} missing 'source' field"

    return True, ""


def validate_markdown_escapes(file_path: Path) -> Tuple[bool, str]:
    """Detect accidental control characters resulting from damaged LaTeX escapes."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        return False, f"Cannot read Markdown file {file_path.name}: {exc}"

    matches = list(_CONTROL_CHAR_RE.finditer(content))
    if matches:
        first = matches[0]
        char_hex = hex(ord(first.group(0)))
        return (
            False,
            f"Markdown file {file_path.name} contains invalid control character {char_hex} at offset {first.start()}"
            f" (often caused by unescaped LaTeX backslashes like \\b or \\f)",
        )

    return True, ""


def validate_file_format(file_path: Path) -> Tuple[bool, str]:
    """Dispatch file format validation based on extension."""
    if not file_path.is_file():
        return True, ""

    suffix = file_path.suffix.lower()
    if suffix == ".json":
        return validate_json_file(file_path)
    if suffix == ".toml":
        return validate_toml_file(file_path)
    if suffix in (".yaml", ".yml"):
        return validate_yaml_file(file_path)
    if suffix == ".ipynb":
        return validate_notebook_file(file_path)
    if suffix in (".md", ".markdown"):
        return validate_markdown_escapes(file_path)

    return True, ""
