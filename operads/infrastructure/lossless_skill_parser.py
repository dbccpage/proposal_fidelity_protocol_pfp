"""Split a skill document without transforming it.

`EPIC-OE-OEWAS-002` names that split `SkillBytePartition`. The four spans are
the partition. `render` concatenates them. There is no `LosslessSkillParser`
class and no YAML AST.

`parse_skill_frontmatter` in `fs_reader.py` is the reading parser and is
deliberately lossy: it returns a mapping, which discards key order, comments,
indentation style, quoting, blank lines, the body, and the file's line endings.
That is correct for asking "what does this skill declare" and unusable for
anything that writes a skill back.

This parser is lossless by *construction* rather than by care. It never
transforms; it only records where the boundaries are and keeps every byte on one
side or the other. `render()` concatenates the parts in order, so
`render(parse(x)) == x` holds because there is no step at which a byte could
change -- not because a round-trip was tested afterwards and happened to agree.

The distinction matters. A parser that reconstructs from a model is lossless
only for the cases someone thought to test; a parser that partitions is lossless
for every input it accepts, including the ones nobody anticipated. The test suite
still runs the whole estate through it, because "by construction" is a claim and
110 real files are evidence.

Line endings are recorded but never normalised. This repository is LF-only, and
a writer that silently converted CRLF would dirty a file it was asked to edit --
the defect sprint 005 found in the macro generator and sprint 002 found in the
cognitive-warfare gate, twice over.

`AuthorityEffect: None`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

FENCE = b"---"


class LosslessParseError(RuntimeError):
    """A typed refusal naming what could not be partitioned."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class LosslessSkillDocument:
    """A skill document held as its parts, in order, unmodified.

    Every field is raw bytes taken from the source. Concatenating them in
    declaration order reproduces the input, and there is no other operation --
    so losslessness is a property of the shape rather than of the care taken.
    """

    open_fence: bytes
    frontmatter: bytes
    close_fence: bytes
    body: bytes

    def render(self) -> bytes:
        """Reassemble. Equal to the input bytes for any document this parsed."""
        return self.open_fence + self.frontmatter + self.close_fence + self.body

    @property
    def newline(self) -> bytes:
        """The line ending this document actually uses, recorded not normalised."""
        return b"\r\n" if b"\r\n" in self.open_fence else b"\n"

    @property
    def frontmatter_text(self) -> str:
        return self.frontmatter.decode("utf-8")

    def frontmatter_mapping(self) -> dict[str, Any]:
        """The lossy reading view, kept separate from the lossless bytes.

        Callers that want to *understand* the frontmatter use this. Callers that
        want to *write the file back* use `render` and never touch it, so a
        mapping round trip can never be mistaken for a document round trip.
        """
        try:
            data = yaml.safe_load(self.frontmatter_text)
        except yaml.YAMLError as exc:
            raise LosslessParseError(
                "MALFORMED_YAML", f"frontmatter is not valid YAML: {exc}"
            ) from exc
        return data if isinstance(data, dict) else {}

    @property
    def frontmatter_keys(self) -> tuple[str, ...]:
        """Declared keys in source order.

        `frontmatter_mapping()` loses order on some YAML loaders and gives no
        signal about duplicates. Reading the lines keeps both.
        """
        keys: list[str] = []
        for raw_line in self.frontmatter_text.splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if raw_line[:1] in {" ", "\t", "-"}:
                continue
            key, separator, _ = raw_line.partition(":")
            if separator:
                keys.append(key.strip())
        return tuple(keys)


def parse_bytes(raw: bytes) -> LosslessSkillDocument:
    """Partition a skill document. Nothing is decoded, normalised or rewritten."""
    if type(raw) is not bytes:
        raise LosslessParseError("NOT_BYTES", "a lossless parse needs the raw bytes")
    if not raw.startswith(FENCE):
        raise LosslessParseError(
            "NO_FRONTMATTER",
            "skill document has no frontmatter block; a skill that declares no "
            "signature must not be given a defaulted one",
        )

    # The opening fence runs to the end of its line, keeping whatever line
    # ending the file uses.
    first_break = raw.find(b"\n")
    if first_break == -1:
        raise LosslessParseError(
            "UNTERMINATED_FENCE", "the opening fence has no line ending"
        )
    open_fence = raw[: first_break + 1]
    remainder = raw[first_break + 1 :]

    # The closing fence is the next line that is exactly `---`, with either
    # line ending, at column zero.
    index = 0
    while True:
        line_break = remainder.find(b"\n", index)
        line = remainder[index : line_break + 1 if line_break != -1 else len(remainder)]
        if line.rstrip(b"\r\n") == FENCE:
            close_start = index
            close_end = line_break + 1 if line_break != -1 else len(remainder)
            return LosslessSkillDocument(
                open_fence=open_fence,
                frontmatter=remainder[:close_start],
                close_fence=remainder[close_start:close_end],
                body=remainder[close_end:],
            )
        if line_break == -1:
            raise LosslessParseError(
                "UNTERMINATED_FENCE",
                "frontmatter block is never closed by a --- line",
            )
        index = line_break + 1


def parse_path(path: Path) -> LosslessSkillDocument:
    """Read a skill document in binary. Text mode would translate line endings."""
    target = Path(path)
    if not target.is_file():
        raise LosslessParseError("MISSING", f"skill document is missing: {target}")
    return parse_bytes(target.read_bytes())


@dataclass(frozen=True, slots=True)
class SkillBytePartition:
    """The named byte partition of one skill document.

    Not a YAML AST and not a host mirror. Newlines stay as they arrived.
    """

    open_fence: bytes
    frontmatter: bytes
    close_fence: bytes
    body: bytes

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SkillBytePartition)
        return (
            self.open_fence == other.open_fence
            and self.frontmatter == other.frontmatter
            and self.close_fence == other.close_fence
            and self.body == other.body
        )

    def __hash__(self) -> int:
        return hash(
            (type(self), self.open_fence, self.frontmatter, self.close_fence, self.body)
        )

    def render(self) -> bytes:
        """Concatenate the four spans. No decoding and no newline rewrite."""
        return self.open_fence + self.frontmatter + self.close_fence + self.body

    @classmethod
    def from_bytes(cls, raw: bytes) -> SkillBytePartition:
        """Partition accepted bytes. Refuse a split that does not render back."""
        document = parse_bytes(raw)
        partition = cls(
            open_fence=document.open_fence,
            frontmatter=document.frontmatter,
            close_fence=document.close_fence,
            body=document.body,
        )
        rendered = partition.render()
        if rendered != raw:
            raise LosslessParseError(
                "PARTITION_NOT_LOSSLESS",
                "partition render differs from the accepted input",
            )
        return partition

    @classmethod
    def from_path(cls, path: Path) -> SkillBytePartition:
        """Partition a file read in binary so text mode cannot rewrite newlines."""
        target = Path(path)
        if not target.is_file():
            raise LosslessParseError("MISSING", f"skill document is missing: {target}")
        return cls.from_bytes(target.read_bytes())


def round_trips(path: Path) -> bool:
    """Whether parsing and rendering reproduces the file byte for byte."""
    target = Path(path)
    return parse_path(target).render() == target.read_bytes()


__all__ = [
    "FENCE",
    "LosslessParseError",
    "LosslessSkillDocument",
    "SkillBytePartition",
    "parse_bytes",
    "parse_path",
    "round_trips",
]
