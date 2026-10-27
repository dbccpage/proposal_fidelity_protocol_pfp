"""Security boundary contracts for hostile finite-gauge YAML."""

import pytest

from pfp.infrastructure.adapters.finite_gauge.input_yaml import (
    parse_input_yaml,
)


def test_yaml_python_object_tag_is_rejected_without_construction() -> None:
    source = "!!python/object/apply:builtins.eval ['1 + 1']"

    with pytest.raises(ValueError, match="invalid input YAML"):
        parse_input_yaml(source)
