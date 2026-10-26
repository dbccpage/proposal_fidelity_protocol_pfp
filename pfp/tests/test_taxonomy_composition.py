"""Catalog injection must work in a fresh process without test import ordering."""

import subprocess
import sys


def test_non_core_catalog_family_reaches_domain_value_object():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from omega_engine_pfp.domain.value_objects.taxonomy import TaskFamilyVO; "
            "import omega_engine_pfp.infrastructure.taxonomy; "
            "assert TaskFamilyVO('causal_refinement_derivation').value == 'causal_refinement_derivation'",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
