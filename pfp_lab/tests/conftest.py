"""Shared test configuration: Hypothesis profiles and the Paper 005 oracle.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:conftest:v1

``HYPOTHESIS_PROFILE=mutation`` lowers example counts so the mutation campaign
can run the suite once per mutant; the default profile is the full run.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest
from hypothesis import HealthCheck, settings

REPO_ROOT = Path(__file__).resolve().parents[2]
ORACLE_PATH = REPO_ROOT / "papers" / "005_pfp_practitioners_field_manual" / "code" / "l1_symbol_game_governor.py"

settings.register_profile("default", max_examples=200, deadline=None)
settings.register_profile(
    "mutation",
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))


@pytest.fixture(scope="session")
def oracle() -> ModuleType:
    """The unmodified Paper 005 governor, loaded by path as an independent oracle.

    Its optional native calculator is selected by an environment variable that
    ends in ``_FUNCTIONAL_GRAPH_BIN``; every such variable is removed so the
    oracle uses its exact Python enumeration.
    """
    if not ORACLE_PATH.is_file():
        pytest.fail(f"Paper 005 oracle not found at {ORACLE_PATH}")
    for name in [key for key in os.environ if key.endswith("_FUNCTIONAL_GRAPH_BIN")]:
        del os.environ[name]
    spec = importlib.util.spec_from_file_location("paper005_governor_oracle", ORACLE_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("cannot load the Paper 005 oracle")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
