#!/usr/bin/env python3
"""Resolve an episode or free-text invariant into a representation disposition.

Dispositions (operadic resolve law):
  NOISE            — discard / do not edit procedural memory
  EXISTING_OP      — patch or route to an existing skill package
  SHARED_CONTRACT  — land once in _shared / contract; skills cite
  CODE_GATE        — deterministic checker preferred over prose
  NEW_SKILL        — last resort; ooutwire only (never auto-admit)
  SKILL_PROSE      — compressive edit to existing SKILL.md (not a new package)

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    from .episode import load_episode_input
except ImportError:  # pragma: no cover - direct script execution
    from episode import load_episode_input

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

DISPOSITIONS = (
    "NOISE",
    "EXISTING_OP",
    "SHARED_CONTRACT",
    "CODE_GATE",
    "NEW_SKILL",
    "SKILL_PROSE",
)


def repo_root_from(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists() and (candidate / ".agents").is_dir():
            return candidate
    return Path.cwd().resolve()


@dataclass
class ResolveResult:
    disposition: str
    target: str = ""
    cite: str = ""
    rationale: str = ""
    skill_id: str = ""
    confidence: str = "MEDIUM"
    next_action: str = ""
    matched_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_routes(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {}
    return _load_flat_routes_without_yaml(text)


def _load_flat_routes_without_yaml(text: str) -> dict[str, Any]:
    """Parse the deliberately small routes.yaml schema without PyYAML.

    Governance cannot disappear because an optional package is missing. This is
    not a general YAML parser; unsupported structure fails closed.
    """
    route_sections = {"shared_contracts", "code_gates"}
    result: dict[str, Any] = {
        "shared_contracts": [],
        "code_gates": [],
        "noise_patterns": [],
        "new_skill_require_all": {},
    }
    section = ""
    current: dict[str, Any] | None = None
    reading_patterns = False
    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw.startswith((" ", "\t")) and stripped.endswith(":"):
            section = stripped[:-1]
            if section not in result:
                raise ValueError(f"unsupported routes section {section!r} at line {line_no}")
            current = None
            reading_patterns = False
            continue
        if section in route_sections:
            if stripped.startswith("- id:"):
                current = {"id": stripped.split(":", 1)[1].strip(), "patterns": []}
                result[section].append(current)
                reading_patterns = False
                continue
            if current is None:
                raise ValueError(f"route field without id at line {line_no}")
            if stripped == "patterns:":
                reading_patterns = True
                continue
            if reading_patterns and stripped.startswith("- "):
                current["patterns"].append(ast.literal_eval(stripped[2:].strip()))
                continue
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                current[key] = ast.literal_eval(value.strip())
                reading_patterns = False
                continue
        elif section == "noise_patterns" and stripped.startswith("- "):
            result[section].append(ast.literal_eval(stripped[2:].strip()))
            continue
        elif section == "new_skill_require_all" and ":" in stripped:
            key, value = stripped.split(":", 1)
            parsed = ast.literal_eval(value.strip())
            if not isinstance(parsed, list):
                raise ValueError(f"new-skill bucket must be a list at line {line_no}")
            result[section][key] = parsed
            continue
        raise ValueError(f"unsupported routes syntax at line {line_no}: {stripped}")
    return result


def _skill_package_names(repo_root: Path) -> set[str]:
    skills = repo_root / "operads" / "skills"
    if not skills.is_dir():
        return set()
    return {
        d.name
        for d in skills.iterdir()
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
    }


RETIRED_STANDALONE_SWARMS: tuple[str, ...] = (
    "core-cognitive-operations-swarm",
    "governing-councils-swarm",
    "project-management-swarm",
    "research-swarm",
    "software-development-swarm",
    "core-paper-review-swarm",
    "core-swarm-developer",
)


def _operad_skill_ids(repo_root: Path) -> set[str]:
    candidates = [
        repo_root / "operads" / "skill_operad" / "json" / "operad_signature.json",
    ]
    if not (candidates[0].parent.is_dir() or (repo_root / "operads/skills").is_dir()):
        candidates += [
            repo_root / ".agents" / "skill_operads" / "operad_signature.json",
            repo_root / ".agents" / "operad" / "json" / "operad_signature.json",
            repo_root / ".agents" / "operad" / "operad_signature.json",
        ]
    ids: set[str] = set(RETIRED_STANDALONE_SWARMS)
    for sig in candidates:
        if not sig.is_file():
            continue
        try:
            data = json.loads(sig.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for op in data.get("operations") or []:
            if isinstance(op, dict):
                sid = op.get("skill_id") or op.get("id") or op.get("name")
                if sid:
                    ids.add(str(sid))
    return ids



def _match_route_list(
    text: str, routes: list[dict[str, Any]], disposition: str
) -> ResolveResult | None:
    for route in routes:
        patterns = route.get("patterns") or []
        for pat in patterns:
            try:
                if re.search(pat, text, re.I):
                    return ResolveResult(
                        disposition=disposition,
                        target=str(route.get("target") or ""),
                        cite=str(route.get("cite") or ""),
                        rationale=f"Matched route {route.get('id')}: /{pat}/",
                        matched_rules=[str(route.get("id") or pat)],
                        next_action=(
                            "patch_shared"
                            if disposition == "SHARED_CONTRACT"
                            else "run_or_extend_gate"
                        ),
                    )
            except re.error:
                continue
    return None


def _looks_like_new_skill(text: str, routes: dict[str, Any]) -> bool:
    req = routes.get("new_skill_require_all") or {}
    if not req:
        return "new skill" in text.lower() and "package" in text.lower()
    buckets = 0
    for _name, words in req.items():
        if any(w.lower() in text.lower() for w in words):
            buckets += 1
    explicit = bool(
        re.search(r"\bnew\s+skill\b|\bskill\s+package\b|\bcreate\s+skill\b", text, re.I)
    )
    return explicit and buckets >= 3


def _find_existing_skill(text: str, packages: set[str], operad_ids: set[str]) -> str | None:
    # Prefer longer package names to avoid short false positives.
    for name in sorted(packages, key=len, reverse=True):
        if len(name) < 4:
            continue
        if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text, re.I):
            return name
    for sid in sorted(operad_ids, key=len, reverse=True):
        if len(sid) < 4:
            continue
        if re.search(rf"(?<![\w-]){re.escape(sid)}(?![\w-])", text, re.I):
            return sid
    return None


def resolve_text(
    repo_root: Path,
    *,
    signal: str = "",
    proposed_invariant: str = "",
    locus: str = "",
    confidence: str = "MEDIUM",
    routes_path: Path | None = None,
) -> ResolveResult:
    blob = "\n".join(
        [signal or "", proposed_invariant or "", locus or ""]
    ).strip()
    conf = (confidence or "MEDIUM").upper()
    if routes_path is not None:
        routes_file = routes_path
    else:
        routes_file = Path(__file__).resolve().parent / "routes.yaml"
        if not routes_file.is_file():
            fallback_routes = Path(__file__).resolve().parents[1] / "yaml" / "routes.yaml"
            if fallback_routes.is_file():
                routes_file = fallback_routes
    routes = _load_routes(routes_file)

    if not blob or not (proposed_invariant or signal).strip():
        return ResolveResult(
            disposition="NOISE",
            rationale="Empty signal/invariant.",
            confidence=conf,
            next_action="discard",
            matched_rules=["empty"],
        )

    for pat in routes.get("noise_patterns") or []:
        try:
            if re.search(pat, blob, re.I):
                return ResolveResult(
                    disposition="NOISE",
                    rationale=f"Matched noise pattern /{pat}/",
                    confidence=conf,
                    next_action="discard",
                    matched_rules=[f"noise:{pat}"],
                )
        except re.error:
            continue

    # Order: CODE_GATE > SHARED_CONTRACT > NEW_SKILL check > EXISTING_OP > SKILL_PROSE
    hit = _match_route_list(blob, routes.get("code_gates") or [], "CODE_GATE")
    if hit:
        hit.confidence = conf
        return hit

    hit = _match_route_list(
        blob, routes.get("shared_contracts") or [], "SHARED_CONTRACT"
    )
    if hit:
        hit.confidence = conf
        return hit

    if _looks_like_new_skill(blob, routes):
        return ResolveResult(
            disposition="NEW_SKILL",
            target="operads/skills/ooutwire/proposed_skills_register.md",
            cite="NEW_SKILL last resort → ooutwire only; never auto-admit.",
            rationale="Explicit new-skill request with multi-bucket activation signals.",
            confidence=conf,
            next_action="ooutwire_entry",
            matched_rules=["new_skill_heuristic"],
        )

    packages = _skill_package_names(repo_root)
    operad_ids = _operad_skill_ids(repo_root)
    existing = _find_existing_skill(blob, packages, operad_ids)
    if existing:
        return ResolveResult(
            disposition="EXISTING_OP",
            target=f"operads/skills/{existing}/SKILL.md",
            skill_id=existing,
            cite="Route to existing skill; compressive edit only after approval.",
            rationale=f"Referenced existing skill package/operad id: {existing}",
            confidence=conf,
            next_action="patch_skill",
            matched_rules=[f"existing:{existing}"],
        )

    # Durable preference without a clear home → SKILL_PROSE on autoskill or locus skill
    locus_skill = ""
    if locus:
        loc = locus.replace("\\", "/").strip("/")
        for part in loc.split("/"):
            if part in packages:
                locus_skill = part
                break
    target_skill = locus_skill or "autoskill"
    return ResolveResult(
        disposition="SKILL_PROSE",
        target=f"operads/skills/{target_skill}/SKILL.md",
        skill_id=target_skill,
        cite="Prefer references/ or compress; avoid additive bloat.",
        rationale="No contract/gate/new-skill match; default compressive skill prose.",
        confidence=conf,
        next_action="propose_skill_edit",
        matched_rules=["default_skill_prose"],
    )


def resolve_episode(repo_root: Path, episode: dict[str, Any]) -> ResolveResult:
    return resolve_text(
        repo_root,
        signal=str(episode.get("signal") or ""),
        proposed_invariant=str(episode.get("proposed_invariant") or ""),
        locus=str(episode.get("locus") or ""),
        confidence=str(episode.get("confidence") or "MEDIUM"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Validated core.skill_compiler.episode.input.v1 JSON file",
    )
    args = parser.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()

    try:
        result = resolve_episode(root, load_episode_input(args.file))
    except ValueError as err:
        print(json.dumps({"ok": False, "error": str(err)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
