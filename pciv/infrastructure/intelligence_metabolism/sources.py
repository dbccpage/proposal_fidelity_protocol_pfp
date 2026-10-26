"""Read-only data source registry and adapters for Intelligence Metabolism (U02).

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataSourceAdapter:
    """Read-only adapter for a specific intelligence source directory."""

    source_id: str
    relative_path: str
    file_pattern: str
    record_parser_kind: str  # "jsonl" or "json" or "receipt_folder"
    description: str

    def resolve_path(self, repo_root: Path) -> Path:
        return repo_root / self.relative_path


SOURCE_REGISTRY: dict[str, DataSourceAdapter] = {
    "symbol_game_runs": DataSourceAdapter(
        source_id="symbol_game_runs",
        relative_path="_ic/darpa/symbol_game/runs",
        file_pattern="**/receipt.json",
        record_parser_kind="receipt_folder",
        description="Sealed Symbol Game execution runs",
    ),
    "woland_runs": DataSourceAdapter(
        source_id="woland_runs",
        relative_path="_ic/darpa/woland/runs",
        file_pattern="**/receipt.json",
        record_parser_kind="receipt_folder",
        description="Woland dialectical bout runs and StructureBench quad bundles",
    ),
    "antibodies": DataSourceAdapter(
        source_id="antibodies",
        relative_path="_ic/cdc/antibodies",
        file_pattern="**/*.json",
        record_parser_kind="json",
        description="Defect antibodies and countermeasure receipts",
    ),
    "omc_dags": DataSourceAdapter(
        source_id="omc_dags",
        relative_path="_ic/nga/omc_dags",
        file_pattern="**/*.json",
        record_parser_kind="json",
        description="Operadic morphism composition DAGs and traces",
    ),
    "dda_traces": DataSourceAdapter(
        source_id="dda_traces",
        relative_path=".agents/dda_traces",
        file_pattern="**/*.jsonl",
        record_parser_kind="jsonl",
        description="Canonical DDC / DDA operational letter tapes and step rows",
    ),
    "bench_results": DataSourceAdapter(
        source_id="bench_results",
        relative_path="_ic/nara/legacy/bench/results",
        file_pattern="**/*.json",
        record_parser_kind="json",
        description="Benchmark and evaluation reports",
    ),
}
