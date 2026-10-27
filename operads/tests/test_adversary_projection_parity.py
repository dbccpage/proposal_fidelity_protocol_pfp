"""The Adversary host projections may not drift while panel v0.1 is staged.

This is byte parity, not proof that the duplicated prose is an admitted OEWAS
instruction. The long-term cutover replaces these copies with thin shims.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOSTS = (".agents", ".claude", ".codex", ".grok")
TOP_LEVEL = (
    Path("rules/swarms/rl_adversary_base_swarm_specialization.md"),
)


def _projection(host: str) -> dict[str, bytes]:
    base = ROOT / host
    skill_root = base / "skills/adversary"
    assert skill_root.is_dir(), f"{host} Adversary skill is missing"
    files = (*TOP_LEVEL, *(p.relative_to(base) for p in skill_root.rglob("*")))
    result: dict[str, bytes] = {}
    for relative in files:
        source = base / relative
        assert not source.is_symlink(), f"{host} projection has a symlink: {relative}"
        if source.is_file():
            result[relative.as_posix()] = source.read_bytes()
        elif relative in TOP_LEVEL:
            raise AssertionError(f"{host} projection is missing: {relative}")
    return result


def test_adversary_four_host_projection_bytes_match() -> None:
    canonical = _projection(HOSTS[0])
    assert "skills/adversary/SKILL.md" in canonical
    for host in HOSTS[1:]:
        assert _projection(host) == canonical, f"{host} Adversary projection drifted"
