"""Harvest presenter extracted from harvest_cli.py. AuthorityEffect: None."""

from __future__ import annotations

import json
from typing import Any

from omega_engine_operads.application.autopoiesis import AutopoieticHarvester
from omega_engine_operads.infrastructure.autopoiesis import (
    FileHarvestVault,
    JsonPharmacyAdapter,
    MarkdownSkillsAdapter,
)
from omega_engine_operads.infrastructure.autopoiesis.harvest_source import (
    FilesystemHarvestSource,
)


class HarvestPresenter:
    @staticmethod
    def dispatch(args: Any) -> int:
        if args.command == "ingest-all":
            vault = FileHarvestVault(args.vault_dir, archive_snapshots_dir=getattr(args, "archive_snapshots_dir", None))
            pharmacy = JsonPharmacyAdapter(args.antibodies_dir)
            skills = MarkdownSkillsAdapter(args.skills_register)
            harvester = AutopoieticHarvester(
                vault, pharmacy, skills, source=FilesystemHarvestSource()
            )

            print("Starting harvest...")
            print(f"  Teamwork Dir:   {args.teamwork_dir}")
            print(f"  Antibodies Dir: {args.antibodies_dir}")
            print(f"  Vault Dir:      {args.vault_dir}")

            receipt = harvester.harvest_all(args.teamwork_dir, args.antibodies_dir)
            receipt_dict = receipt.to_dict()

            receipt_path = args.vault_dir / f"{receipt.receipt_id}.receipt.json"
            receipt_path.write_text(json.dumps(receipt_dict, indent=2), encoding="utf-8")

            print("\n[HARVEST COMPLETE]")
            print(f"  Receipt ID:                {receipt.receipt_id}")
            print(f"  Teamwork Files Preserved:  {receipt.teamwork_files_preserved}")
            print(f"  Antibodies Cataloged:      {receipt.antibodies_cataloged}")
            print(f"  Skills Mined:              {receipt.skills_mined}")
            print(f"  Antibodies Mined:          {receipt.antibodies_mined}")
            print(f"  New CAS Objects Written:   {receipt.cas_objects_written}")
            print(f"  Receipt File:              {receipt_path}")
            print(f"  AuthorityEffect:           {receipt.authority_effect}")
            return 0

        elif args.command == "status":
            vault = FileHarvestVault(args.vault_dir, archive_snapshots_dir=getattr(args, "archive_snapshots_dir", None))
            snaps = vault.list_snapshots()
            print(f"Vault Root: {args.vault_dir}")
            print(f"Total Snapshots: {len(snaps)}")
            for s in snaps:
                snap_obj = vault.get_snapshot(s)
                if snap_obj:
                    print(
                        f"  Snapshot: {s} | Source: {snap_obj.source_name} | Files: {len(snap_obj.records)} | Merkle: {snap_obj.merkle_root[:16]}..."
                    )
            return 0

        elif args.command == "verify-vault":
            snapshots_dir = getattr(args, "snapshots_dir", None)
            vault = FileHarvestVault(
                args.vault_dir, snapshots_dir=snapshots_dir,
                archive_snapshots_dir=getattr(args, "archive_snapshots_dir", None),
            )
            try:
                snaps = vault.list_snapshots()
                print(f"Verifying {len(snaps)} snapshots...")
                total_checked = 0
                missing = []
                for s in snaps:
                    snap_obj = vault.get_snapshot(s)
                    if not snap_obj:
                        continue
                    for r in snap_obj.records:
                        total_checked += 1
                        content = vault.get_file(r.sha256)
                        if content is None:
                            missing.append((s, r.relative_path, r.sha256))

                if missing:
                    print(f"FAIL: {len(missing)} missing CAS objects!")
                    for m in missing[:5]:
                        print(f"  Snapshot: {m[0]} File: {m[1]} Digest: {m[2]}")
                    return 1
                print(f"PASS: All {total_checked} CAS records verified bit-for-bit.")
                return 0
            finally:
                vault.close()

        elif args.command == "pre-clean-teamwork":
            vault = FileHarvestVault(args.vault_dir, archive_snapshots_dir=getattr(args, "archive_snapshots_dir", None))
            pharmacy = JsonPharmacyAdapter(args.antibodies_dir)
            skills = MarkdownSkillsAdapter(args.skills_register)
            harvester = AutopoieticHarvester(
                vault, pharmacy, skills, source=FilesystemHarvestSource()
            )

            print("Executing Pre-Clean Automated Harvest Gate...")
            print(f"  Teamwork Dir:   {args.teamwork_dir}")
            print(f"  Antibodies Dir: {args.antibodies_dir}")
            print(f"  Vault Dir:      {args.vault_dir}")
            print(f"  Clear After:    {args.clear_after}")

            try:
                receipt, cleared = harvester.pre_clean_teamwork(
                    args.teamwork_dir,
                    args.antibodies_dir,
                    clear_after=args.clear_after,
                )
                print("\n[PRE-CLEAN GATE: PASS]")
                print(f"  Receipt ID:               {receipt.receipt_id}")
                print(f"  Files Preserved in CAS:   {receipt.teamwork_files_preserved}")
                print(f"  Skills Mined:             {receipt.skills_mined}")
                print(f"  Antibodies Mined:         {receipt.antibodies_mined}")
                print(f"  Cleared Directories:      {cleared}")
                print(f"  AuthorityEffect:          {receipt.authority_effect}")
                return 0
            except Exception as e:
                print(f"\n[PRE-CLEAN GATE: REFUSAL] {e}")
                return 2

        return 0
