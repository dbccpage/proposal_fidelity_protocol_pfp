#!/usr/bin/env python3
"""Hook compiler: renders ``operads/hooks/hooks.json`` from the rule register.

A hook is the run-time half of a rule. Each entry in the register's ``hooks`` section names
its event, tool matcher, script, and the invariants it enforces. The compiler checks that
every one of those invariants is ENFORCED or PARTIAL with an ``enforced_by`` inside
``operads/hooks/``, and that every invariant enforced inside ``operads/hooks/`` is listed by a
hook, so a check cannot sit in a hook script without a rule, or a rule claim a hook that is
not registered.

AuthorityEffect: None. Reads the register; only ``--write`` writes ``hooks.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "yaml" / "rules_registry.yaml"
HOOKS_JSON = "operads/hooks/hooks.json"
HOOKS_ROOT = "operads/hooks/"
RUNNER = "py -3.12"
ACTIVE = frozenset({"ENFORCED", "PARTIAL"})
EVENTS = ("PreToolUse", "PostToolUse")
HEADER = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "version": "1.0",
    "description": (
        "Generated from operads/skill_operad/yaml/rules_registry.yaml by "
        "python -m operads.skill_operad.skill_compiler.hook_compiler --write. Do not edit."
    ),
}


@dataclass(frozen=True)
class HookFinding:
    code: str
    path: str
    message: str

    def render(self) -> str:
        return f"[{self.code}] {self.path}: {self.message}"


def _hook_entries(registry: dict) -> list[dict]:
    hooks = registry.get("hooks", [])
    if type(hooks) is not list or not all(type(h) is dict for h in hooks):
        raise ValueError("register field 'hooks' must be a list of mappings")
    for hook in hooks:
        for field in ("event", "matcher", "script", "description"):
            if type(hook.get(field)) is not str or not hook[field]:
                raise ValueError(f"hook field {field!r} must be a non-empty string")
        if hook["event"] not in EVENTS:
            raise ValueError(f"hook event {hook['event']!r} is not one of {EVENTS}")
        enforces = hook.get("enforces")
        if type(enforces) is not list or not enforces or not all(type(i) is str for i in enforces):
            raise ValueError(f"{hook['script']}: enforces must be a non-empty list of invariant ids")
    return hooks


def render_hooks(registry: dict) -> dict:
    """The hooks.json document, grouped by event in register order."""
    grouped: dict[str, list[dict]] = {}
    for hook in _hook_entries(registry):
        grouped.setdefault(hook["event"], []).append(
            {
                "matcher": hook["matcher"],
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{RUNNER} {hook['script']}",
                        "description": hook["description"],
                        "enforces": list(hook["enforces"]),
                    }
                ],
            }
        )
    return {**HEADER, "hooks": {event: grouped[event] for event in EVENTS if event in grouped}}


def render_text(registry: dict) -> str:
    return json.dumps(render_hooks(registry), indent=2, ensure_ascii=False) + "\n"


def _invariants(registry: dict) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for entry in [*registry.get("rules", []), *registry.get("external_sources", [])]:
        for invariant in entry.get("invariants", []):
            found[invariant["id"]] = invariant
    return found


def check_hooks(repo_root: Path, registry: dict) -> list[HookFinding]:
    findings: list[HookFinding] = []
    try:
        hooks = _hook_entries(registry)
    except ValueError as exc:
        return [HookFinding("R10_HOOK_SPEC", "rules_registry.yaml", str(exc))]
    invariants = _invariants(registry)
    listed: set[str] = set()
    for hook in hooks:
        if not (repo_root / hook["script"]).is_file():
            findings.append(HookFinding("R10_HOOK_SCRIPT", hook["script"], "script does not exist"))
        for identifier in hook["enforces"]:
            listed.add(identifier)
            invariant = invariants.get(identifier)
            if invariant is None:
                findings.append(HookFinding("R10_HOOK_RULE", hook["script"], f"{identifier} is not registered"))
            elif invariant["status"] not in ACTIVE:
                findings.append(
                    HookFinding("R10_HOOK_RULE", hook["script"], f"{identifier} is {invariant['status']}")
                )
            elif not str(invariant.get("enforced_by", "")).startswith(HOOKS_ROOT):
                findings.append(
                    HookFinding("R10_HOOK_RULE", hook["script"], f"{identifier} is not enforced under {HOOKS_ROOT}")
                )
    for identifier, invariant in sorted(invariants.items()):
        in_hooks = str(invariant.get("enforced_by", "")).startswith(HOOKS_ROOT)
        if in_hooks and invariant["status"] in ACTIVE and identifier not in listed:
            findings.append(HookFinding("R10_HOOK_UNLISTED", identifier, "enforced in a hook script no hook lists"))
    expected = render_text(registry)
    for relative in hooks_json_paths(repo_root, registry):
        try:
            current = (repo_root / relative).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        except (OSError, UnicodeDecodeError):
            current = None
        if current != expected:
            findings.append(HookFinding("R10_HOOKS_DRIFT", relative, "differs from the register; run --write"))
    return findings


def hooks_json_paths(repo_root: Path, registry: dict) -> list[str]:
    """The canonical hooks.json and the copy in each host root that has a hooks folder."""
    hosts = [f"{host}/hooks/hooks.json" for host in registry.get("host_roots", [])]
    return [HOOKS_JSON, *(path for path in hosts if (repo_root / path).parent.is_dir())]


def write_hooks(repo_root: Path, registry: dict) -> None:
    text = render_text(registry)
    for relative in hooks_json_paths(repo_root, registry):
        (repo_root / relative).write_text(text, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--write", action="store_true", help="write hooks.json, then check")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    registry = yaml.safe_load(Path(args.registry).read_text(encoding="utf-8"))
    if args.write:
        write_hooks(root, registry)
        print(f"wrote {', '.join(hooks_json_paths(root, registry))}")
    findings = check_hooks(root, registry)
    for finding in findings:
        print(f"  {finding.render()}")
    print("FAIL" if findings else "PASS: hooks.json matches the register.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
