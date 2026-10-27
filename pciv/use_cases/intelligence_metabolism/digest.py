"""Daily Intelligence Digest generator (U02).

Aggregates mined records and renders claim-disciplined summaries.
AuthorityEffect: None (const).
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Sequence

from pciv.domain.intelligence_metabolism.models import MinedRecordV1


class DailyDigestGenerator:
    """Renders claim-disciplined daily digests from mined intelligence records."""

    def __init__(self, records: Sequence[MinedRecordV1]) -> None:
        self.records = records

    def compute_summary_statistics(self) -> dict[str, int]:
        source_counts = Counter(r.source_id for r in self.records)
        type_counts = Counter(r.record_type for r in self.records)
        return {
            "total_records": len(self.records),
            "total_sources": len(source_counts),
            **{f"source_{k}": v for k, v in source_counts.items()},
            **{f"type_{k}": v for k, v in type_counts.items()},
        }

    def render_markdown(self, date_stamp: str | None = None) -> str:
        date_str = date_stamp or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stats = self.compute_summary_statistics()

        lines = [
            f"# Daily Intelligence Metabolism Digest — {date_str}",
            "",
            "**AuthorityEffect**: None",
            "",
            "## 1. Mined Corpus Volume",
            "",
            f"- Total records mined: `{stats['total_records']}`",
            f"- Active sources: `{stats['total_sources']}`",
            "",
            "### Records by Source",
            "| Source ID | Count |",
            "|---|---|",
        ]

        source_items = sorted(
            [(k[7:], v) for k, v in stats.items() if k.startswith("source_")],
            key=lambda x: x[0],
        )
        for s_id, count in source_items:
            lines.append(f"| `{s_id}` | {count} |")

        lines.extend(
            [
                "",
                "## 2. Claim Discipline Evaluation",
                "",
                "### What this supports:",
                "- Systematic, read-only extraction of verified SHA-256 bound records across active run folders and traces.",
                "- Accurate provenance tracing linking records to physical file offsets and content digests.",
                "",
                "### What this does not support:",
                "- Autonomous truth certification or promotion of candidate skills/tactics.",
                "- In-place mutation of past run receipts or historical trace ledgers.",
                "",
                "### Narrowest defensible claim:",
                f"Under the declared local fixtures, {stats['total_records']} provenance-bound records were successfully indexed with intact cryptographic hashes.",
                "",
                "### Next test needed:",
                "Multi-source n-gram motif distillation into candidate SkillOperand proposals with automated Thymus filtering.",
                "",
            ]
        )

        return "\n".join(lines)
