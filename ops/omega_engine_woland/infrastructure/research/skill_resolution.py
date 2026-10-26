"""Resolve retained stage labels to current, byte-bound skill packages."""

from hashlib import sha256
from pathlib import Path


# Stage IDs and historical receipts keep their old labels. A current invocation
# records both the requested label and the package actually read.
SKILL_SUCCESSORS = {
    'paper-redteam-dialogue': 'omega-old-man-red-team',
    'paper-improver': 'governance-research-paper-edit-publish',
    'paper-adversary': 'omega-old-man-red-team',
    'paper-proof-signoff': 'lean4-axiom-audit',
    'paper-release': 'governance-research-paper-edit-publish',
    'paper-build': 'governance-research-paper-edit-publish',
    'omega-old-man-chatgpt-red-team': 'omega-old-man-red-team',
    'research': 'lib-literature-lookup',
    'deep-research': 'lib-scientific-hypothesis-tree',
}


def resolve_skill_source(skill_id: str, *, repo_root: Path | None = None) -> dict:
    """Read the concrete current instruction; resolution is not execution."""
    import re
    if type(skill_id) is not str or re.fullmatch(r'[a-z][a-z0-9-]*', skill_id) is None:
        raise ValueError('SKILL_ID_INVALID')
    current = SKILL_SUCCESSORS.get(skill_id, skill_id)
    root = repo_root or Path(__file__).resolve().parents[3]
    path = Path('omega_engine_operads/skills') / current / 'SKILL.md'
    raw = (root / path).read_bytes()
    if len(raw) > 131072:
        raise ValueError('SKILL_SOURCE_TOO_LARGE')
    return dict(requested_skill_id=skill_id, canonical_skill_id=current,
        source_path=path.as_posix(), source_sha256=sha256(raw).hexdigest(),
        instruction=raw.decode('utf-8'), executed=False)
