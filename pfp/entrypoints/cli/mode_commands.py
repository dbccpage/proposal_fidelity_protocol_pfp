"""CLI commands for Symbol Game operational modes discovery and inspection.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from functools import partial
from typing import Any

from pfp.infrastructure.adapters.mode_discovery import (
    discover_modes_manifest,
    load_all_mode_contracts,
    validate_mode_catalog_closure,
)
from pfp.use_cases.modes import (
    GetModeUseCase,
    ListModesUseCase,
    ValidateModesUseCase,
)


def cmd_mode_list(args: Any) -> int:
    """Lists all canonical operational modes discovered dynamically via modes_manifest.yaml."""
    modes_dir = getattr(args, "modes_dir", None)
    cluster = getattr(args, "cluster", None)
    use_case = ListModesUseCase(
        load_manifest=partial(discover_modes_manifest, modes_dir),
        load_contracts=partial(load_all_mode_contracts, modes_dir),
    )
    res = use_case.execute(cluster_filter=cluster)

    if getattr(args, "json", False):
        print(json.dumps(res, indent=2))
        return 0

    print("=" * 75)
    print(f" {res['title']} (v{res['manifest_version']})")
    print(f" Source: {res['modes_dir']}")
    print(f" Total Modes Discovered: {res['total_count']} (Returned: {res['returned_count']})")
    print("=" * 75)
    print(f"{'ID':<4} | {'Name':<42} | {'Cluster'}")
    print("-" * 75)
    for m in res["modes"]:
        print(f"{m['mode_id']:<4} | {m['name']:<42} | {m['cluster']}")
    print("=" * 75)
    return 0


def cmd_mode_show(args: Any) -> int:
    """Shows detailed contract specification for a specific operational mode."""
    modes_dir = getattr(args, "modes_dir", None)
    mode_id = int(args.mode_id)
    use_case = GetModeUseCase(load_contracts=partial(load_all_mode_contracts, modes_dir))

    try:
        contract = use_case.execute(mode_id)
    except KeyError as e:
        print(f"Error: {e}")
        return 1

    d = contract.to_dict()
    if getattr(args, "json", False):
        print(json.dumps(d, indent=2))
        return 0

    print("=" * 75)
    print(f" MODE {contract.mode_id}: {contract.name}")
    print(f" Cluster: {contract.cluster} | Authority: {contract.authority_effect}")
    print(f" Paper  : {contract.paper_reference}")
    print("=" * 75)
    print(f"Core Mechanism:\n  {contract.core_mechanism}")
    print(f"\nSubstrate:\n  {contract.substrate}")
    print(f"\nRules ({len(contract.rules)}):")
    for r in contract.rules:
        print(f"  - {r}")
    print(f"\nWinning Condition:\n  {contract.winning_condition}")
    print(f"\nFailure Modes ({len(contract.failure_modes)}):")
    for fm in contract.failure_modes:
        print(f"  - {fm}")
    if contract.file_path:
        print(f"\nContract File:\n  {contract.file_path}")
    print("=" * 75)
    return 0


def cmd_mode_validate(args: Any) -> int:
    """Validates dynamic mode discovery and catalog closure against disk."""
    modes_dir = getattr(args, "modes_dir", None)
    use_case = ValidateModesUseCase(validate_catalog=partial(validate_mode_catalog_closure, modes_dir))
    res = use_case.execute()

    if getattr(args, "json", False):
        print(json.dumps(res, indent=2))
        return 0 if res["is_closed"] else 1

    print("=" * 75)
    print(" SYMBOL GAME OPERATIONAL MODES DISCOVERY AUDIT")
    print("=" * 75)
    print(f"Modes Directory : {res['modes_dir']}")
    print(f"Manifest Path   : {res['manifest_path']}")
    print(f"Declared Modes  : {res['declared_modes_count']}")
    print(f"Loaded Contracts: {res['total_modes_count']}")
    print(f"Disk YAML Files : {res['disk_files_count']}")
    print(f"Closure Status  : {'[PASS] CLOSED' if res['is_closed'] else '[FAIL] DEFECT DETECTED'}")

    if res["missing_on_disk"]:
        print(f"Missing on Disk : {res['missing_on_disk']}")
    if res["extra_on_disk"]:
        print(f"Extra on Disk   : {res['extra_on_disk']}")
    if res["invalid_authority_modes"]:
        print(f"Invalid Authority Modes: {res['invalid_authority_modes']}")
    print("=" * 75)
    return 0 if res["is_closed"] else 1
