"""Filesystem input for PFP models; model validation remains in the domain."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .yaml_loading import strict_yaml_load

Model = TypeVar("Model", bound=BaseModel)


def load_yaml_model(model_type: type[Model], path_or_text: str | Path) -> Model:
    """Load a UTF-8 YAML file or YAML text and validate the same domain model.

    Existing files take precedence, matching the retired path-taking model
    helpers. Long or multiline text is parsed directly rather than passed to
    the operating system as an invalid filename.
    """
    content = str(path_or_text)
    if isinstance(path_or_text, Path):
        content = path_or_text.read_text(encoding="utf-8-sig")
    elif "\n" not in content and "\r" not in content:
        path = Path(path_or_text)
        try:
            is_file = path.is_file()
        except OSError:
            is_file = False
        if is_file:
            # An admitted file read failure is I/O failure, never YAML text.
            content = path.read_text(encoding="utf-8-sig")
    data = strict_yaml_load(content.lstrip("\ufeff"))
    if not isinstance(data, dict):
        raise ValueError(
            f"YAML payload for {model_type.__name__} must be a mapping, got {type(data).__name__}"
        )
    return model_type.model_validate(data)
