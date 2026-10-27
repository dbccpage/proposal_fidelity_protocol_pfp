"""DDC Operad presenter extracted from ddc_operad_cli.py. AuthorityEffect: None."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from operads.application.ddc_execution.parse_ddc_tape_use_case import (
    ParseDdcTapeRequest,
)
from operads.infrastructure.ddc_execution.ddc_tape import (
    WorkflowDdcTapeParser,
    build_parse_ddc_tape_use_case,
)


class DdcOperadPresenter:
    @staticmethod
    def cmd_parse(args: argparse.Namespace) -> int:
        source_path = Path(args.tape)
        use_case = build_parse_ddc_tape_use_case()
        req = ParseDdcTapeRequest(
            source=str(source_path),
            output_receipt_path=args.output_receipt,
            persist_evidence=bool(args.output_receipt or args.persist),
        )
        result = use_case.execute(req)
        if result.is_err:
            refusal = result.error
            print(
                f"[-] DDC Tape Parsing REFUSED: {refusal.code} - {refusal.message}", file=sys.stderr
            )
            return 1

        resp = result.unwrap()
        receipt = resp.receipt

        print("================================================================================")
        print("  DDC TAPE TO COLORED OPERAD COMPOSITION RECEIPT")
        print("================================================================================")
        print(f"Tape Path       : {receipt.tape_path}")
        print(f"Run ID          : {receipt.run_id}")
        print(f"Rune Sequence   : {receipt.tape_str}")
        print(f"Step Count      : {receipt.step_count}")
        print(f"Morphisms       : {receipt.morphism_count}")
        print(f"Hash Chain Valid: {receipt.hash_chain_valid}")
        print(f"DDC Laws Valid  : {receipt.ddc_laws_valid}")
        print(
            f"Initial Residual: {receipt.initial_residual} (Phi1={receipt.initial_phi1}, Gamma2={receipt.initial_gamma2})"
        )
        print(
            f"Terminal Residual: {receipt.terminal_residual} (Phi1={receipt.terminal_phi1}, Gamma2={receipt.terminal_gamma2})"
        )
        print(f"Residual Delta  : {receipt.residual_delta}")
        print(f"Residual Effect : {receipt.residual_effect}")

        if receipt.law_violations:
            print("\nLaw Violations Detected:")
            for v in receipt.law_violations:
                print(f"  - {v}")

        if resp.evidence_path:
            print(f"\n[+] Evidence receipt saved: {resp.evidence_path}")

        print("================================================================================")
        return 0 if receipt.ddc_laws_valid else 2

    @staticmethod
    def cmd_compress(args: argparse.Namespace) -> int:
        source_path = Path(args.tape)
        parser = WorkflowDdcTapeParser()
        res = parser.compress(
            str(source_path),
            skill_id=args.skill_id,
            skill_name=args.skill_name,
            apply_changes=args.apply_changes,
            claimed_residual_effect=args.claimed_residual,
        )
        if res.is_err:
            refusal = res.error
            print(
                f"[-] Operadic Compression REFUSED: {refusal.code} - {refusal.message}",
                file=sys.stderr,
            )
            return 1

        outcome = res.unwrap()
        print("[+] Operadic Compression Complete:")
        print(f"    Skill ID        : {outcome['skill_id']}")
        print(f"    Residual Effect : {outcome['residual_effect']}")
        print(f"    Signature Path  : {outcome['signature_path']}")
        return 0
