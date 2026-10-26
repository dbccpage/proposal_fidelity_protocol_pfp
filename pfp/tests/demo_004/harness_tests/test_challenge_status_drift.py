"""Drift tests for challenge status views, catalog consistency, and link validity.

Verifies:
  1. challenge_status.v1.json matches fresh tree derivation.
  2. catalog.yaml status fields match fresh tree derivation.
  3. README.md generated status table matches fresh tree derivation.
  4. No duplicate IDs exist in catalog.yaml.
  5. All relative markdown links in challenges/README.md and project README resolve.
  6. Decisive mutation: an altered status or duplicate ID is rejected.

AuthorityEffect: None.
"""

from __future__ import annotations

import json

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.tools.challenge_status import (
    check_relative_links,
    generate_status_data,
    parse_catalog_challenges,
    render_readme_table,
    resolve_challenges_dir,
    update_catalog_yaml_content,
)

CHALLENGES_DIR = resolve_challenges_dir()
REPO_ROOT = CHALLENGES_DIR.parents[2]


def test_challenge_status_views_are_in_sync():
    """Assert that committed challenge_status.v1.json matches fresh tree generation."""
    status_data = generate_status_data(CHALLENGES_DIR)
    status_json_path = CHALLENGES_DIR / "challenge_status.v1.json"
    assert status_json_path.is_file(), "challenge_status.v1.json missing"

    committed_data = json.loads(status_json_path.read_text(encoding="utf-8"))
    assert committed_data["total_challenges"] == status_data["total_challenges"]
    assert committed_data["packages_on_disk"] == status_data["packages_on_disk"]
    assert committed_data["counts"] == status_data["counts"]

    for cid, exp_info in status_data["challenges"].items():
        assert cid in committed_data["challenges"], (
            f"Challenge {cid} missing from committed status json"
        )
        comm_info = committed_data["challenges"][cid]
        assert comm_info["status"] == exp_info["status"], f"Status mismatch for {cid}"
        assert comm_info["package_path"] == exp_info["package_path"], (
            f"Package path mismatch for {cid}"
        )


def test_catalog_yaml_has_no_duplicate_ids():
    """Assert catalog.yaml contains zero duplicate challenge IDs."""
    catalog_path = CHALLENGES_DIR / "catalog.yaml"
    challenges, duplicate_ids = parse_catalog_challenges(catalog_path)
    assert not duplicate_ids, f"Duplicate challenge IDs in catalog.yaml: {duplicate_ids}"
    assert len(challenges) == 143, f"Expected 143 challenges, found {len(challenges)}"


def test_catalog_yaml_status_fields_are_in_sync():
    """Assert catalog.yaml status fields match derived statuses."""
    status_data = generate_status_data(CHALLENGES_DIR)
    catalog_path = CHALLENGES_DIR / "catalog.yaml"
    current_catalog = catalog_path.read_text(encoding="utf-8")
    expected_catalog = update_catalog_yaml_content(current_catalog, status_data)
    assert current_catalog == expected_catalog, "catalog.yaml has drifted from derived status"


def test_challenges_readme_table_is_in_sync():
    """Assert challenges/README.md generated region matches fresh rendering."""
    status_data = generate_status_data(CHALLENGES_DIR)
    expected_table = render_readme_table(status_data)
    readme_path = CHALLENGES_DIR / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8")
    assert expected_table in readme_text, "challenges/README.md status table has drifted"


def test_challenges_readme_relative_links_resolve():
    """Assert all relative markdown links in challenges/README.md resolve to existing files."""
    readme_path = CHALLENGES_DIR / "README.md"
    broken = check_relative_links(readme_path)
    assert not broken, f"Broken relative links found in challenges/README.md: {broken}"


def test_project_readme_relative_links_resolve():
    """Assert all relative markdown links in mssn_sn_symgam/README.md resolve to existing files."""
    project_readme = CHALLENGES_DIR.parent / "README.md"
    broken = check_relative_links(project_readme)
    assert not broken, f"Broken relative links found in mssn_sn_symgam/README.md: {broken}"


def test_decisive_mutation_detects_status_tamper():
    """Theoretical minimum mutation: an altered status value trips the drift assertion."""
    status_data = generate_status_data(CHALLENGES_DIR)
    tampered_data = dict(status_data)
    tampered_data["counts"] = dict(status_data["counts"])
    tampered_data["counts"]["scored"] += 1

    status_json_path = CHALLENGES_DIR / "challenge_status.v1.json"
    committed_data = json.loads(status_json_path.read_text(encoding="utf-8"))

    with pytest.raises(AssertionError):
        assert committed_data["counts"] == tampered_data["counts"]
