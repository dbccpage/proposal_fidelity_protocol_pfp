"""Plain Text Representation Adapter (U25).

Encodes TurnView as human-readable Markdown text while preserving exact information equivalence.
AuthorityEffect: None.
"""
from __future__ import annotations

import re
from typing import Any

from omega_engine_pfp.domain.representation.models import TurnView
from omega_engine_pfp.domain.representation.ports import RepresentationPort


class PlainTextRepresentation(RepresentationPort):
    """Encodes TurnView into structured plain text Markdown sections."""

    @property
    def representation_id(self) -> str:
        return "PLAIN_TEXT"

    def render(self, view: TurnView) -> str:
        lines: list[str] = [
            "# Symbol Game Turn State",
            f"- Round: {view.round_seq}",
            f"- Phi1: {view.phi1}",
            f"- Gamma2: {view.gamma2}",
            f"- Prompt Regime: {view.prompt_regime}",
            f"- Authority Effect: {view.authority_effect}",
            "",
            "## Open Constraints",
        ]
        if view.open_constraints:
            for k, v in view.open_constraints:
                lines.append(f"- {k} = {v}")
        else:
            lines.append("- (none)")

        lines.extend(["", "## Decided Values"])
        if view.decided_values:
            for k, v in view.decided_values:
                lines.append(f"- {k} = {v}")
        else:
            lines.append("- (none)")

        lines.extend(["", "## Refused Moves"])
        if view.refused_moves:
            for k, v in view.refused_moves:
                lines.append(f"- {k}: {v}")
        else:
            lines.append("- (none)")

        lines.append("")
        return "\n".join(lines)

    def parse(self, rendered: str) -> TurnView:
        round_seq = 0
        phi1 = 0
        gamma2 = 0
        prompt_regime = "default"
        authority_effect = "None"

        open_constraints: list[tuple[str, str]] = []
        decided_values: list[tuple[str, int]] = []
        refused_moves: list[tuple[str, str]] = []

        current_section = "HEADER"

        for raw_line in rendered.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("## Open Constraints"):
                current_section = "CONSTRAINTS"
                continue
            elif line.startswith("## Decided Values"):
                current_section = "VALUES"
                continue
            elif line.startswith("## Refused Moves"):
                current_section = "REFUSED"
                continue
            elif line.startswith("# Symbol Game Turn State"):
                current_section = "HEADER"
                continue

            if current_section == "HEADER":
                if line.startswith("- Round:"):
                    round_seq = int(line.split(":", 1)[1].strip())
                elif line.startswith("- Phi1:"):
                    phi1 = int(line.split(":", 1)[1].strip())
                elif line.startswith("- Gamma2:"):
                    gamma2 = int(line.split(":", 1)[1].strip())
                elif line.startswith("- Prompt Regime:"):
                    prompt_regime = line.split(":", 1)[1].strip()
                elif line.startswith("- Authority Effect:"):
                    authority_effect = line.split(":", 1)[1].strip()

            elif current_section == "CONSTRAINTS":
                if line == "- (none)":
                    continue
                if line.startswith("- "):
                    payload = line[2:]
                    if "=" in payload:
                        k, v = payload.split("=", 1)
                        open_constraints.append((k.strip(), v.strip()))

            elif current_section == "VALUES":
                if line == "- (none)":
                    continue
                if line.startswith("- "):
                    payload = line[2:]
                    if "=" in payload:
                        k, v = payload.split("=", 1)
                        decided_values.append((k.strip(), int(v.strip())))

            elif current_section == "REFUSED":
                if line == "- (none)":
                    continue
                if line.startswith("- "):
                    payload = line[2:]
                    if ":" in payload:
                        k, v = payload.split(":", 1)
                        refused_moves.append((k.strip(), v.strip()))

        return TurnView(
            round_seq=round_seq,
            phi1=phi1,
            gamma2=gamma2,
            open_constraints=tuple(open_constraints),
            decided_values=tuple(decided_values),
            refused_moves=tuple(refused_moves),
            prompt_regime=prompt_regime,
            authority_effect=authority_effect,
        )
