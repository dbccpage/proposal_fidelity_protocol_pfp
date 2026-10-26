"""AutoP Learning presenter extracted from autop_learning_cli.py. AuthorityEffect: None."""

from __future__ import annotations

import argparse
import importlib
import json
from typing import Any

from omega_engine_operads.infrastructure.autopoiesis.learning_runtime import (
    build_learning_completion,
)
from omega_engine_operads.infrastructure.autopoiesis.learning_store import (
    LearningStore,
)


class AutoPLearningPresenter:
    @staticmethod
    def execute_learning(args: Any, parser: argparse.ArgumentParser) -> int:
        root = args.repo_root.resolve()
        if args.runtime_factory:
            module, name = args.runtime_factory.split(":", 1)
            completion = getattr(importlib.import_module(module), name)(root)
        else:
            completion = build_learning_completion(root)
        if args.pending:
            print(json.dumps(completion.service.store.pending(), indent=2))
            return 0
        paths = tuple(([args.receipt] if args.receipt else []) + args.transcript)
        if args.maintenance:
            if paths:
                parser.error("maintenance does not accept learning sources")
            receipt = {
                "schema": "omega.autop.receipt.v2",
                "mode": "maintenance",
                "overall_status": "NO_CHANGE",
                "reason": "MAINTENANCE_ONLY_NO_LEARNING",
                "authority_effect": "None",
                "pending_jobs": len(completion.service.store.pending()),
            }
        else:
            receipt = completion.import_paths(paths, host=args.host, retry=args.retry)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            LearningStore(root / "runs" / "autop_learning").vault._immutable_write(
                args.output, json.dumps(receipt, indent=2).encode("utf-8")
            )
        print(json.dumps(receipt, indent=2))
        return {"FAILED": 1, "BLOCKED": 2}.get(receipt["overall_status"], 0)
