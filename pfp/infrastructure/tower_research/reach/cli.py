"""Installed reach context and historical replay. AuthorityEffect: None."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
from . import ledger, stage_registry
from .gates import GATED_STEPS
from .pins import GitResolver, Resolver
from .receipt import Context, verify_receipt
from .resources import reach_root


class CachedResolver:
    def __init__(self, resolver: Resolver) -> None:
        self.resolver = resolver
        self.cache: dict[tuple[str, str, str], bytes | None] = {}

    def read(self, repo: str, commit: str, path: str) -> bytes | None:
        key = (repo, commit, path)
        if key not in self.cache:
            self.cache[key] = self.resolver.read(repo, commit, path)
        return self.cache[key]


def load_context(reach_dir: Path | None = None, clones: dict[str, Path] | None = None,
                 *, repository_root: Path | None = None, version: str = "v1") -> Context:
    directory = reach_dir if reach_dir is not None else reach_root(version)
    repositories = dict(clones or {})
    if repository_root is not None:
        repositories.setdefault(ledger.TARGET_CARRIER, repository_root)
    carriers = json.loads((directory / "registry/carriers.json").read_bytes())["carriers"]
    hosts = {repo: repository_root for repo, entry in carriers.items()
             if entry.get("harness_host") == ledger.TARGET_CARRIER and repository_root is not None}
    return Context(resolver=CachedResolver(GitResolver(repositories, hosts)),
        stage_registry=json.loads((directory / "registry/stage_registry.json").read_bytes()),
        checkers=json.loads((directory / "registry/checkers.json").read_bytes())["checkers"],
        carriers=carriers, gated_steps=GATED_STEPS, level_texts=stage_registry.level_texts())


def replay(repository_root: Path, clones: dict[str, Path] | None = None) -> list[dict[str, Any]]:
    context = load_context(clones=clones, repository_root=repository_root)
    rows = []
    for path in sorted((reach_root() / "receipts").rglob("*.json")):
        result = verify_receipt(path.read_bytes(), context)
        rows.append({"path": path.relative_to(reach_root()).as_posix(),
                     "terminal": result.terminal, "codes": list(result.codes)})
    if not rows:
        raise ValueError("HISTORICAL_RECEIPTS_UNAVAILABLE")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("replay", "registry-check", "ledger-check", "registry", "ledger"))
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="read-only compatibility option for registry/ledger")
    parser.add_argument("--clone", action="append", default=[])
    args = parser.parse_args(argv)
    if args.command in {"registry", "ledger"} and not args.check:
        parser.error("historical aliases require --check; writing v1 evidence is unavailable")
    command = {"registry": "registry-check", "ledger": "ledger-check"}.get(args.command, args.command)
    if command == "registry-check":
        return int(stage_registry.build_bytes() != (reach_root() / "registry/stage_registry.json").read_bytes())
    clones = {}
    for value in args.clone:
        name, separator, path = value.partition("=")
        if not name or not separator or not path:
            parser.error("clone must be REPOSITORY=PATH")
        clones[name] = Path(path)
    rows = replay(args.workspace, clones)
    refused = [row for row in rows if row["terminal"] == "REFUSED"]
    print(json.dumps({"AuthorityEffect": "None", "receipts": len(rows), "refused": refused}, sort_keys=True))
    if refused:
        return 1
    if command == "ledger-check":
        directory = reach_root()
        data, numbers = ledger.build(directory / "receipts", load_context(clones=clones, repository_root=args.workspace))
        return int(data != (directory / "ledger.jsonl").read_bytes()
                   or numbers != (directory / "derived/numbers.json").read_bytes())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
