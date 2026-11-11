"""Compile an industry ``AGENTS.md`` (or ``.cursorrules``) + ``skills/*/SKILL.md``
directory into candidate ``TypedOp`` skills and candidate ``DetectorRule`` guards.

Recognised inputs:

* rule file: bullet lines (``- `` or ``* ``) are prose rules. A bullet that
  contains ``deny: `<regex>``` is also a machine guard: the regex becomes a
  candidate ``DetectorRule`` (it still has to pass thymus screening and the
  bounded-regex admission of ``eis.domain.safe_pattern``).
* ``SKILL.md``: optional ``---`` front matter with ``name:`` / ``description:``,
  then the body. ``deny:`` bullets inside a skill become guards too.

The importer does not judge relevance or correctness. Prose rules become
uncertified obligations: nothing here checks that a model obeys them.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from . import REPO_ROOT  # noqa: F401
from .fidelity import sha256_hex
from .operad_pipe import TypedOp
from eis.domain.safe_pattern import UnsafePatternRefusal, compile_safe_pattern
from eis.domain.value_objects import DetectorRule

_DENY = re.compile(r'deny:\s*`([^`]+)`')
_BULLET = re.compile(r'^\s*[-*]\s+(.*\S)\s*$')


def estimate_tokens(text: str) -> int:
    """Declared estimate: ceil(UTF-8 bytes / 4). Not a tokenizer."""
    return -(-len(text.encode('utf-8')) // 4)


def normalized_digest(text: str) -> str:
    """Digest of the body with whitespace collapsed and case folded."""
    return sha256_hex(' '.join(text.split()).casefold())


@dataclass(frozen=True)
class ImportedSkill:
    name: str
    description: str
    body: str
    path: str

    @property
    def text(self) -> str:
        return f'## Skill: {self.name}\n{self.description}\n\n{self.body.strip()}\n'

    def as_op(self) -> TypedOp:
        return TypedOp(op_id=f'skill:{self.name}', input_colour='Contract', output_colour='Contract',
                       kind='context', prompt_digest=normalized_digest(self.body),
                       cost_tokens=estimate_tokens(self.text), idempotent_key=normalized_digest(self.body))


@dataclass
class ImportedStack:
    rules_text: str
    prose_rules: list[str]
    guards: list[DetectorRule]
    refused_guards: list[dict]
    skills: list[ImportedSkill]


def _guards(text: str, source: str, refused: list[dict]) -> list[DetectorRule]:
    out = []
    for n, pattern in enumerate(_DENY.findall(text), 1):
        rule_id = f'{source}:deny:{n}'
        try:
            compile_safe_pattern(pattern)
        except UnsafePatternRefusal as err:
            refused.append({'rule_id': rule_id, 'pattern': pattern, 'code': err.code})
            continue
        out.append(DetectorRule(rule_id=rule_id, target_epitope=source, match_pattern=pattern))
    return out


def parse_skill(path: Path) -> ImportedSkill:
    raw = path.read_text(encoding='utf-8')
    meta, body = {}, raw
    if raw.startswith('---\n'):
        head, _, body = raw[4:].partition('\n---\n')
        for line in head.splitlines():
            key, sep, value = line.partition(':')
            if sep:
                meta[key.strip()] = value.strip()
    return ImportedSkill(meta.get('name', path.parent.name), meta.get('description', ''), body, path.as_posix())


def import_stack(root: Path) -> ImportedStack:
    root = Path(root)
    rule_file = next((root / n for n in ('AGENTS.md', '.cursorrules') if (root / n).is_file()), None)
    rules_text = rule_file.read_text(encoding='utf-8') if rule_file else ''
    refused: list[dict] = []
    prose = [m.group(1) for line in rules_text.splitlines() if (m := _BULLET.match(line))]
    guards = _guards(rules_text, 'AGENTS', refused)
    skills = [parse_skill(p) for p in sorted((root / 'skills').glob('*/SKILL.md'))]
    for skill in skills:
        guards += _guards(skill.body, f'skill:{skill.name}', refused)
    return ImportedStack(rules_text, prose, guards, refused, skills)
