"""Filesystem JSON/YAML adapter for BQNF fixtures.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_pfp.domain.normal_forms.fixture_ports import (
    BqnfFixtures,
    parse_bqnf_fixture_payload,
)


class JsonYamlBqnfFixtureLoader:
    """Load a fixture document from an explicitly supplied filesystem location."""

    def load(self, location: str) -> Result[BqnfFixtures, Refusal]:
        path = Path(location)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return Err(
                Refusal(
                    "BQNF_FIXTURE_READ_REFUSED",
                    f"Unable to read BQNF fixture: {exc}",
                    "bqnf.fixture.load",
                )
            )
        decoded = self._decode(path, text)
        if decoded.is_err:
            return decoded
        return parse_bqnf_fixture_payload(decoded.unwrap())

    @staticmethod
    def _decode(path: Path, text: str) -> Result[object, Refusal]:
        try:
            payload = (
                yaml.safe_load(text)
                if path.suffix.lower() in {".yaml", ".yml"}
                else json.loads(text)
            )
        except (json.JSONDecodeError, yaml.YAMLError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    "BQNF_FIXTURE_PARSE_REFUSED",
                    f"Unable to parse BQNF fixture: {exc}",
                    "bqnf.fixture.load",
                )
            )
        return Ok(payload)


__all__ = ["JsonYamlBqnfFixtureLoader"]
