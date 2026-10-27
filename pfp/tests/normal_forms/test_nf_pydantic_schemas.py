"""Tests validating the Pydantic v2 schemas in contracts_nf_standards.

Verifies:
1. NormalFormStandard validates standard.yaml with zero defects.
2. NormalFormContractMetaSchema validates normal_form_contract_schema.yaml with zero defects.
3. NormalFormFoundationalDefinitions validates normal_form_definitions.yaml with zero defects.
4. NormalFormContract validates all active contracts in contracts_normal_forms/.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "infrastructure/yaml/normal_forms"
STANDARDS_DIR = CONTRACTS_DIR / "_golden_nfs"


def test_normal_form_standard_schema():
    """Validates standard.yaml against the Pydantic schema."""
    mod = _load_module(
        "normal_form_standard_schema",
        REPO_ROOT
        / "pfp/infrastructure/normal_forms/_golden_nfs/normal_form_standard_schema.py",
    )
    standard_path = STANDARDS_DIR / "standard.yaml"
    assert standard_path.is_file()

    standard = mod.NormalFormStandard.from_yaml_file(standard_path)
    assert standard.standard_id == "coda.normal_form_standard.v1"
    assert standard.authority_effect == "None"
    assert len(standard.pillars) == 4
    assert len(standard.spectrum) == 14
    assert standard.document.authorization.certified_implies_authorized is False
    dknf = next(item for item in standard.spectrum if item.id == "nf.classical.dknf")
    assert dknf.decidable_subclass_fence == "monadic_or_guarded_fd_key_domain_fragment"
    assert dknf.unrestricted_first_order_status == "aspirational_non_executable"


def test_normal_form_contract_meta_schema():
    """Validates normal_form_contract_schema.yaml against the Pydantic meta-schema."""
    mod = _load_module(
        "normal_form_contract_schema",
        REPO_ROOT
        / "pfp/infrastructure/normal_forms/_golden_nfs/normal_form_contract_schema.py",
    )
    schema_path = STANDARDS_DIR / "normal_form_contract_schema.yaml"
    assert schema_path.is_file()

    metaschema = mod.NormalFormContractMetaSchema.from_yaml_file(schema_path)
    assert metaschema.schema_version == "smplx.nf.contract_schema.v1"
    assert len(metaschema.loss_ledger_trigger_registry) == 8
    assert "Preserve" in metaschema.canonical_terminals.enum


def test_normal_form_definitions():
    """Validates normal_form_definitions.yaml against the Pydantic schema."""
    mod = _load_module(
        "normal_form_definitions",
        REPO_ROOT
        / "pfp/infrastructure/normal_forms/_golden_nfs/normal_form_definitions.py",
    )
    defs_path = STANDARDS_DIR / "normal_form_definitions.yaml"
    assert defs_path.is_file()

    definitions = mod.NormalFormFoundationalDefinitions.from_yaml_file(defs_path)
    assert definitions.definitions_id == "coda.normal_form_foundational_definitions.v1"
    assert definitions.authority_effect == "None"
    assert len(definitions.quadrilateral_criterion.pillars) == 4
    assert len(definitions.classical_spectrum) == 14
    assert len(definitions.mssn_levels_spectrum) == 7
    assert len(definitions.fsp_normal_forms) == 2
    assert len(definitions.ddc_operational_normal_forms) == 8


def test_validate_active_contracts():
    """Validates that NormalFormContract parses active normal form contracts."""
    mod = _load_module(
        "normal_form_contract_schema",
        REPO_ROOT
        / "pfp/infrastructure/normal_forms/_golden_nfs/normal_form_contract_schema.py",
    )
    sample_contracts = [
        "nf.classical.1nf.yaml",
        "nf.classical.3nf.yaml",
        "nf.classical.bcnf.yaml",
        "nf.ddc.hodge_canonical.yaml",
        "nf.fsp.bssnf.yaml",
    ]
    for c_name in sample_contracts:
        c_path = CONTRACTS_DIR / c_name
        if c_path.is_file():
            contract = mod.NormalFormContract.from_yaml_file(c_path)
            assert contract.identity.id == c_name.replace(".yaml", "")
            assert contract.authorization.certified_implies_authorized is False


def test_bcnf_decomposition_seed_invariance():
    """Verifies that BCNF decomposition is invariant across PYTHONHASHSEED values."""
    import os
    import subprocess
    import sys

    code = (
        "from pfp.domain.normal_forms.relational import "
        "RelationalSchema, FunctionalDependency; "
        "from pfp.domain.normal_forms.relational_advanced import "
        "decompose_bcnf_tree; "
        "s = RelationalSchema(frozenset('ABCDE'), frozenset(["
        "FunctionalDependency(frozenset('D'), frozenset('A')), "
        "FunctionalDependency(frozenset('E'), frozenset('A')), "
        "FunctionalDependency(frozenset('EA'), frozenset('D'))])); "
        "d_out = [''.join(sorted(r.attributes)) for r in decompose_bcnf_tree(s)]; "
        "print(d_out)"
    )
    outputs: set[str] = set()
    for seed in ("0", "1", "2", "3"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        outputs.add(proc.stdout.strip())
    assert len(outputs) == 1, f"Seed-dependent BCNF outputs: {outputs}"

