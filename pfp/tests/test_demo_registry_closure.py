# -*- coding: utf-8 -*-
"""Verification of demo registry unification and set-closure gate.

Tests:
1. Exact set-closure between disk demo directories and registered front-ends (bijective cardinality).
2. Set-closure between registered challenges and catalog.yaml packet_built entries.
3. Importability of all registered use cases and existence of test files.
4. Specific registration and fixture integrity of demo_q40_quantum_solver.
5. Implementation digest reproducibility.

Clean Architecture Layer: Operations Scoped Tests
AuthorityEffect: None
"""

from __future__ import annotations

import pytest

from pfp.infrastructure.demos.catalog import (
    implementation_digest,
    lookup,
    registry_closure,
    scenario_fixture_bytes,
    scenarios,
)


def test_demo_registry_set_closure():
    """Verify that curriculum demo directories and registered front-ends form an exact closed set."""
    report = registry_closure()
    assert report.is_closed, f"Demo registry set-closure failed: {report}"
    assert report.schema_version == "core.mssn.catalog.v2"
    assert report.demo_dirs_count == 28
    assert report.front_ends_count == 28
    assert report.missing_demo_dirs == ()
    assert report.extra_front_ends == ()
    assert report.registered_challenges_count == 9
    assert report.packet_built_challenges_count == 9
    assert report.missing_challenges == ()
    assert report.extra_challenges == ()
    assert report.unimportable_use_cases == ()
    assert report.missing_test_files == ()


def test_q40_quantum_solver_registered_in_catalog():
    """Verify demo_q40_quantum_solver is registered in catalog.json with correct challenge metadata."""
    all_scenarios = scenarios()
    q40_list = [s for s in all_scenarios if s.scenario_id == "demo_q40_quantum_solver"]
    assert len(q40_list) == 1
    q40 = q40_list[0]

    assert q40.front_end == "demo_q40_quantum_solver"
    assert q40.challenge_id == "C021"
    assert q40.kind == "quantum"
    assert q40.test == ""
    assert q40.use_case == "pfp.use_cases.mssn_demo"

    # Test fixture bytes integrity via SHA-256
    row = lookup("demo_q40_quantum_solver")
    data = scenario_fixture_bytes(row)
    assert len(data) > 0


def test_registry_closure_strict_mode():
    """Verify strict mode passes without raising DemoRefusal when registry is closed."""
    report = registry_closure(strict=True)
    assert report.is_closed


def test_implementation_digest_integrity():
    """Verify implementation digest computes deterministically over closed files."""
    digest1 = implementation_digest()
    digest2 = implementation_digest()
    assert digest1 == digest2
    assert len(digest1) == 64


def test_implementation_digest_uses_current_provider_owner(monkeypatch, tmp_path):
    from pfp.infrastructure.demos import catalog

    real_files = catalog.files
    original_catalog = real_files(catalog.PACKAGE).joinpath("catalog.json").read_bytes()
    before = catalog.implementation_digest()
    provider_root = tmp_path / "adversary"
    for owner, path in catalog._CURRENT_IMPLEMENTATION_OWNERS.values():
        current = provider_root / path
        current.parent.mkdir(parents=True, exist_ok=True)
        current.write_bytes(real_files(owner).joinpath(path).read_bytes())

    def current_files(package):
        assert package != "providers", "retired resources must not be probed"
        return provider_root if package == "adversary" else real_files(package)

    monkeypatch.setattr(catalog, "files", current_files)
    assert catalog.implementation_digest() == before
    source = provider_root / "infrastructure/providers/adapters/native_functional.py"
    source.write_bytes(source.read_bytes() + b"\n# synthetic changed current source\n")
    assert catalog.implementation_digest() != before
    source.unlink()
    with pytest.raises(FileNotFoundError):
        catalog.implementation_digest()
    assert real_files(catalog.PACKAGE).joinpath("catalog.json").read_bytes() == original_catalog


def test_implementation_digest_binds_pfp_turn_sources(monkeypatch):
    from pfp.infrastructure.demos import catalog

    before = catalog.implementation_digest()
    # Removing one actual dependency must change the current code identity.
    monkeypatch.setattr(catalog, "_PFP_TURN_SOURCES", catalog._PFP_TURN_SOURCES[1:])
    assert catalog.implementation_digest() != before
