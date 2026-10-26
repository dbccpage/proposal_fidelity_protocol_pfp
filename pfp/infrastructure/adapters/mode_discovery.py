"""Infrastructure adapter for dynamic discovery of Symbol Game mode contracts.
AuthorityEffect: None.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from omega_engine_pfp.domain.modes import (
    ModeCluster,
    ModeContract,
    ModesManifest,
)


def resolve_repo_root() -> Path:
    """Finds repository root dynamically."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists() or (
            (parent / "omega_engine_pfp").is_dir()
            and (parent / "ow").is_dir()
        ):
            return parent
    return current.parents[3]


def find_modes_dir(start_path: Optional[Path] = None) -> Path:
    """Dynamically locates the top-level modes/ directory containing modes_manifest.yaml."""
    # 1. Environment variable override
    env_path = os.environ.get("SYMBOL_GAME_MODES_DIR")
    if env_path:
        p = Path(env_path).resolve()
        if (p / "modes_manifest.yaml").is_file():
            return p

    root = (start_path or resolve_repo_root()).resolve()

    # Installed resources live with the application, without requiring a checkout.
    # An explicit root remains isolated from the installed catalog so callers
    # can inspect another estate or receive a genuine missing-resource error.
    candidates = [
        root / "omega_engine_pfp" / "infrastructure" / "yaml" / "modes",
        root / "infrastructure" / "yaml" / "modes",
        root
        / "omega_engine_education"
        / "documentation"
        / "030_the_symbol_game_proposal_fidelity_protocol_pfp"
        / "modes",
        root / "ow" / "omega_engine_pfp_v0.2" / "modes",
        root / "ow" / "pfp" / "omega_engine_pfp_v0.2" / "modes",
        root / "ow" / "pfp" / "modes",
        root / "ow" / "modes",
    ]
    if start_path is None:
        candidates.insert(0, Path(__file__).resolve().parents[1] / "yaml" / "modes")

    for cand in candidates:
        if (cand / "modes_manifest.yaml").is_file():
            return cand

    # 3. Recursive directory search under ow/ if not in standard candidate list
    ow_root = root / "ow"
    if ow_root.is_dir():
        for manifest_file in ow_root.rglob("modes_manifest.yaml"):
            # Ensure it is a top-level modes folder, not nested in a legacy subfolder
            if manifest_file.parent.name == "modes":
                return manifest_file.parent

    raise FileNotFoundError(
        f"Could not dynamically discover 'modes/modes_manifest.yaml' starting from {root}. "
        f"Ensure the application mode resources are installed or set SYMBOL_GAME_MODES_DIR."
    )


def discover_modes_manifest(modes_dir: Optional[Path] = None) -> ModesManifest:
    """Loads and validates the modes_manifest.yaml from the discovered modes directory."""
    actual_dir = modes_dir or find_modes_dir()
    manifest_path = actual_dir / "modes_manifest.yaml"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    raw_clusters = data.get("clusters", {})
    clusters: Dict[str, ModeCluster] = {}
    for cid, cdata in raw_clusters.items():
        clusters[cid] = ModeCluster(
            cluster_id=cid,
            name=cdata.get("name", cid),
            mode_ids=list(cdata.get("modes", [])),
        )

    return ModesManifest(
        manifest_version=str(data.get("manifest_version", "2.0.0")),
        title=str(data.get("title", "Modes Manifest")),
        description=str(data.get("description", "")).strip(),
        clusters=clusters,
        modes=list(data.get("modes", [])),
        manifest_path=str(manifest_path),
    )


def load_mode_contract(mode_file_path: Path) -> ModeContract:
    """Loads a single mode YAML contract file into a ModeContract domain entity."""
    if not mode_file_path.is_file():
        raise FileNotFoundError(f"Mode contract file not found: {mode_file_path}")

    with open(mode_file_path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)

    return ModeContract(
        mode_id=int(doc.get("mode_id", 0)),
        name=str(doc.get("name", "")),
        cluster=str(doc.get("cluster", "")),
        authority_effect=str(doc.get("authority_effect", "None")),
        core_mechanism=str(doc.get("core_mechanism", "")),
        substrate=str(doc.get("substrate", "")),
        paper_reference=str(doc.get("paper_reference", "")),
        rules=list(doc.get("rules", [])),
        entry_preconditions=list(doc.get("entry_preconditions", [])),
        winning_condition=str(doc.get("winning_condition", "")).strip(),
        failure_modes=list(doc.get("failure_modes", [])),
        verifier_contract=dict(doc.get("verifier_contract", {})),
        file_path=str(mode_file_path),
    )


def load_all_mode_contracts(modes_dir: Optional[Path] = None) -> Dict[int, ModeContract]:
    """Dynamically loads all mode contracts declared in modes_manifest.yaml."""
    actual_dir = modes_dir or find_modes_dir()
    manifest = discover_modes_manifest(actual_dir)

    contracts: Dict[int, ModeContract] = {}
    for entry in manifest.modes:
        mid = int(entry["id"])
        filename = entry["file"]
        contract_path = actual_dir / filename
        contract = load_mode_contract(contract_path)
        contracts[mid] = contract

    return contracts


def validate_mode_catalog_closure(modes_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Audits closure between modes_manifest.yaml and mode files on disk."""
    actual_dir = modes_dir or find_modes_dir()
    manifest = discover_modes_manifest(actual_dir)

    declared_ids = {int(m["id"]) for m in manifest.modes}
    declared_files = {Path(m["file"]).as_posix() for m in manifest.modes}

    disk_files = set()
    for p in actual_dir.glob("mode_*.yaml"):
        if p.is_file() and p.name not in {"mode_models.yaml", "mode_types.yaml", "mode_catalog.yaml"}:
            disk_files.add(p.name)
    for p in actual_dir.glob("mode_*/contract.yaml"):
        if p.is_file():
            disk_files.add(p.relative_to(actual_dir).as_posix())

    missing_on_disk = sorted(declared_files - disk_files)
    extra_on_disk = sorted(disk_files - declared_files)

    loaded_contracts = load_all_mode_contracts(actual_dir)
    invalid_authority = [
        mid for mid, c in loaded_contracts.items() if c.authority_effect != "None"
    ]

    is_closed = (
        len(missing_on_disk) == 0
        and len(extra_on_disk) == 0
        and len(invalid_authority) == 0
        and len(declared_ids) == 20
    )

    return {
        "is_closed": is_closed,
        "modes_dir": str(actual_dir),
        "manifest_path": str(manifest.manifest_path),
        "total_modes_count": len(loaded_contracts),
        "declared_modes_count": len(declared_ids),
        "disk_files_count": len(disk_files),
        "missing_on_disk": missing_on_disk,
        "extra_on_disk": extra_on_disk,
        "invalid_authority_modes": invalid_authority,
    }
