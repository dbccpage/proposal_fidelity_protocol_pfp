"""Render a nomination proposal without granting archive authority."""

from __future__ import annotations

from datetime import datetime

from operads.domain.skill_garden.cull import CullReport


def render_manifest(report: CullReport, *, now: datetime) -> str:
    """The `planned_archive.md` a human reviews, approves, and commits."""
    lines = [
        "# Planned archive",
        "",
        f"**Generated:** {now.date().isoformat()}",
        "**AuthorityEffect:** `None`",
        "",
        "This file is a proposal. `archive_lane` refuses to act without an",
        "`approved_by` line below, filled in by a human who has read the table.",
        "",
        f"- roster: {report.roster_size}",
        f"- ledger span: {report.span_days:.1f} days",
        f"- nominated: {len(report.candidates)}",
        f"- exempt: {len(report.exempt)}",
        f"- within grace: {len(report.in_grace)}",
        f"- used within the window: {len(report.used_recently)}",
        "",
        "approved_by:",
        "approved_at:",
        "",
    ]
    if report.refusals:
        lines += ["## Refused", ""]
        lines += [f"- {reason}" for reason in report.refusals]
        lines += ["", "No candidates are listed, by design.", ""]
        return "\n".join(lines)

    lines += ["## Nominated", "", "| skill | last used | created |", "| --- | --- | --- |"]
    for row in report.candidates:
        lines.append(
            f"| `{row['skill_id']}` | {row['last_used'] or 'never'} | "
            f"{row['created'] or 'unknown'} |"
        )
    lines.append("")
    return "\n".join(lines)
