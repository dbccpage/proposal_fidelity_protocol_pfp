"""Mutation-style probes for documentation path confinement policy."""

from pfp.domain.documentation_integrity.policies import is_document_relative_path


def test_traversal_guard_kills_removed_parent_segment_check() -> None:
    def mutant_without_parent_check(value: str) -> bool:
        return bool(value and not value.startswith("/"))

    attack = "reference/../../secrets.md"
    assert mutant_without_parent_check(attack)
    assert not is_document_relative_path(attack)


def test_backslash_guard_kills_posix_only_mutant() -> None:
    def mutant_posix_only(value: str) -> bool:
        return bool(value and ".." not in value.split("/"))

    attack = "C:\\secrets.md"
    assert mutant_posix_only(attack)
    assert not is_document_relative_path(attack)
