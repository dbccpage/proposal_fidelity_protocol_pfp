"""Thymic Negative Selection Gate for Central Tolerance.

Forrest & Hofmeyr (1994) Negative Selection Algorithm (NSA) applied to candidate detector rules.
Filters candidate anti-skills and detector rules against a sealed Self Panel of verified clean
code, proofs, and prompt fixtures. Any candidate detector matching healthy self tissue triggers
apoptosis (immediate purge) and emits an ApoptosisReceipt with status PURGED_SELF_REACTIVE.

Zero outward dependencies. Zero floating-point arithmetic.
Exact-type equality enforced on all Value Objects.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterator, Sequence

_SYNTHETIC_TRAILER = re.compile(r"\s*-- index \d+ hash_mod_\d+\s*$")


@dataclass(frozen=True, slots=True)
class SelfPanelEntry:
    """An individual verified clean fixture in the Epistemic Self Panel."""

    entry_id: str
    category: str
    content: str
    content_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.entry_id, str) or not self.entry_id.strip():
            raise ValueError("entry_id must be a non-empty string")
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError("category must be a non-empty string")
        if not isinstance(self.content, str):
            raise TypeError("content must be a string")
        if not isinstance(self.content_sha256, str) or len(self.content_sha256) != 64:
            raise ValueError("content_sha256 must be a 64-character hex string")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SelfPanelEntry)
        return (
            self.entry_id == other.entry_id
            and self.category == other.category
            and self.content == other.content
            and self.content_sha256 == other.content_sha256
        )

    def __hash__(self) -> int:
        return hash((type(self), self.entry_id, self.category, self.content_sha256))


@dataclass(frozen=True, slots=True)
class SelfPanel:
    """Sealed immutable corpus of verified clean reference fixtures."""

    entries: tuple[SelfPanelEntry, ...]
    fixture_count: int
    sealed_sha256: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple):
            raise TypeError("entries must be a tuple of SelfPanelEntry")
        if not isinstance(self.fixture_count, int) or self.fixture_count < 1:
            raise ValueError("fixture_count must be positive integer >= 1")
        if len(self.entries) != self.fixture_count:
            raise ValueError(f"entries length {len(self.entries)} does not match fixture_count {self.fixture_count}")
        if not isinstance(self.sealed_sha256, str) or len(self.sealed_sha256) != 64:
            raise ValueError("sealed_sha256 must be 64-character hex string")
        if self.authority_effect != "None":
            raise ValueError("authority_effect must be 'None'")

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Iterator[SelfPanelEntry]:
        return iter(self.entries)

    def __getitem__(self, index: int) -> SelfPanelEntry:
        return self.entries[index]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SelfPanel)
        return (
            self.entries == other.entries
            and self.fixture_count == other.fixture_count
            and self.sealed_sha256 == other.sealed_sha256
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((type(self), self.sealed_sha256, self.fixture_count))

    @staticmethod
    def base_content(content: str) -> str:
        """Content with the synthetic ``-- index NNN hash_mod_M`` trailer removed."""
        return _SYNTHETIC_TRAILER.sub("", content)

    def distinct_base_contents(self) -> frozenset[str]:
        """Distinct fixture contents once synthetic trailers are ignored.

        The entry count overstates the panel's diversity when many entries differ
        only by a generated trailer; this is the count that measures it.
        """
        return frozenset(self.base_content(entry.content) for entry in self.entries)

    @classmethod
    def load_canonical(cls, path: Path | str | None = None) -> SelfPanel:
        """Load the canonical 1,000-sample sealed SelfPanel from disk."""
        if path is None:
            path = Path(__file__).parent / "self_panel.json"
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Canonical self-panel file not found: {p}")

        raw_bytes = p.read_bytes()
        data = json.loads(raw_bytes.decode("utf-8"))

        entry_objs: list[SelfPanelEntry] = []
        for raw_entry in data["entries"]:
            entry_objs.append(
                SelfPanelEntry(
                    entry_id=raw_entry["entry_id"],
                    category=raw_entry["category"],
                    content=raw_entry["content"],
                    content_sha256=raw_entry["content_sha256"],
                )
            )

        entries_tuple = tuple(entry_objs)
        return cls(
            entries=entries_tuple,
            fixture_count=len(entries_tuple),
            sealed_sha256=data.get("sealed_sha256", hashlib.sha256(raw_bytes).hexdigest()),
            authority_effect="None",
        )

    @classmethod
    def from_strings(cls, strings: Sequence[str]) -> SelfPanel:
        """Construct a lightweight SelfPanel from arbitrary strings (for testing)."""
        entry_objs: list[SelfPanelEntry] = []
        for idx, text in enumerate(strings):
            c_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
            entry_objs.append(
                SelfPanelEntry(
                    entry_id=f"SP-MOCK-{idx+1:04d}",
                    category="mock_fixture",
                    content=text,
                    content_sha256=c_sha,
                )
            )
        entries_tuple = tuple(entry_objs)
        payload = {
            "entries": [{"entry_id": e.entry_id, "content_sha256": e.content_sha256} for e in entries_tuple],
            "fixture_count": len(entries_tuple),
        }
        canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        sealed_digest = hashlib.sha256(canonical_bytes).hexdigest()
        return cls(
            entries=entries_tuple,
            fixture_count=len(entries_tuple),
            sealed_sha256=sealed_digest,
            authority_effect="None",
        )


@dataclass(frozen=True, slots=True)
class ApoptosisReceipt:
    """Cryptographic evidence receipt emitted when a candidate detector is purged for self-reactivity."""

    receipt_id: str
    rule_id: str
    violating_sample_id: str
    violating_sample_digest: str
    status: str = "PURGED_SELF_REACTIVE"
    canonical_hash: str = ""
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.receipt_id, str) or not self.receipt_id.strip():
            raise ValueError("receipt_id must be a non-empty string")
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id must be a non-empty string")
        if not isinstance(self.violating_sample_id, str):
            raise TypeError("violating_sample_id must be a string")
        if not isinstance(self.violating_sample_digest, str):
            raise TypeError("violating_sample_digest must be a string")
        if self.status != "PURGED_SELF_REACTIVE":
            raise ValueError("status must be 'PURGED_SELF_REACTIVE'")
        if self.authority_effect != "None":
            raise ValueError("authority_effect must be 'None'")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ApoptosisReceipt)
        return (
            self.receipt_id == other.receipt_id
            and self.rule_id == other.rule_id
            and self.violating_sample_id == other.violating_sample_id
            and self.violating_sample_digest == other.violating_sample_digest
            and self.status == other.status
            and self.canonical_hash == other.canonical_hash
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.receipt_id,
            self.rule_id,
            self.violating_sample_id,
            self.violating_sample_digest,
            self.status,
            self.canonical_hash,
            self.authority_effect,
        ))

    @classmethod
    def create(
        cls,
        rule_id: str,
        violating_sample_id: str,
        violating_sample_digest: str,
        receipt_id: str = "",
    ) -> ApoptosisReceipt:
        """Create an ApoptosisReceipt sealed with RFC 8785 canonical hash."""
        if not receipt_id:
            h_seed = hashlib.sha256(f"{rule_id}:{violating_sample_id}:{violating_sample_digest}".encode("utf-8")).hexdigest()
            receipt_id = f"APOP-{h_seed[:12]}"

        body = {
            "authority_effect": "None",
            "receipt_id": receipt_id,
            "rule_id": rule_id,
            "status": "PURGED_SELF_REACTIVE",
            "violating_sample_digest": violating_sample_digest,
            "violating_sample_id": violating_sample_id,
        }
        canonical_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()

        return cls(
            receipt_id=receipt_id,
            rule_id=rule_id,
            violating_sample_id=violating_sample_id,
            violating_sample_digest=violating_sample_digest,
            status="PURGED_SELF_REACTIVE",
            canonical_hash=canonical_hash,
            authority_effect="None",
        )


@dataclass(frozen=True, slots=True)
class ThymusSelectionResult:
    """Exact-type result from Thymic Central Tolerance evaluation."""

    rule_id: str
    is_admitted: bool
    self_fixtures_tested: int
    autoimmune_violations: int
    first_violating_sample: str | None
    rationale: str
    apoptosis_receipt: ApoptosisReceipt | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id must be non-empty string")
        if not isinstance(self.is_admitted, bool):
            raise TypeError("is_admitted must be a boolean")
        if not isinstance(self.self_fixtures_tested, int) or self.self_fixtures_tested < 0:
            raise ValueError("self_fixtures_tested must be non-negative int")
        if not isinstance(self.autoimmune_violations, int) or self.autoimmune_violations < 0:
            raise ValueError("autoimmune_violations must be non-negative int")
        if self.first_violating_sample is not None and not isinstance(self.first_violating_sample, str):
            raise TypeError("first_violating_sample must be string or None")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be non-empty string")
        if self.apoptosis_receipt is not None and not isinstance(self.apoptosis_receipt, ApoptosisReceipt):
            raise TypeError("apoptosis_receipt must be ApoptosisReceipt or None")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ThymusSelectionResult)
        return (
            self.rule_id == other.rule_id
            and self.is_admitted is other.is_admitted
            and self.self_fixtures_tested == other.self_fixtures_tested
            and self.autoimmune_violations == other.autoimmune_violations
            and self.first_violating_sample == other.first_violating_sample
            and self.rationale == other.rationale
            and self.apoptosis_receipt == other.apoptosis_receipt
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.rule_id,
            self.is_admitted,
            self.self_fixtures_tested,
            self.autoimmune_violations,
            self.first_violating_sample,
            self.rationale,
            self.apoptosis_receipt,
        ))


class ThymusGate:
    """Central tolerance filter rejecting detectors that cross-react with self fixtures."""

    def __init__(
        self,
        self_panel: SelfPanel | Sequence[str] | Sequence[SelfPanelEntry] | Path | str | None = None,
    ) -> None:
        if self_panel is None:
            self._panel = SelfPanel.load_canonical()
        elif isinstance(self_panel, SelfPanel):
            self._panel = self_panel
        elif isinstance(self_panel, (Path, str)):
            self._panel = SelfPanel.load_canonical(self_panel)
        elif isinstance(self_panel, Sequence):
            if not self_panel:
                raise ValueError("self_panel must contain at least one clean reference fixture")
            if isinstance(self_panel[0], SelfPanelEntry):
                entries_tuple = tuple(self_panel)  # type: ignore
                c_bytes = json.dumps([e.entry_id for e in entries_tuple], sort_keys=True).encode("utf-8")
                self._panel = SelfPanel(
                    entries=entries_tuple,
                    fixture_count=len(entries_tuple),
                    sealed_sha256=hashlib.sha256(c_bytes).hexdigest(),
                    authority_effect="None",
                )
            else:
                self._panel = SelfPanel.from_strings(self_panel)  # type: ignore
        else:
            raise TypeError(f"Invalid self_panel specification: {type(self_panel).__name__}")

    @property
    def fixture_count(self) -> int:
        return self._panel.fixture_count

    @property
    def self_panel(self) -> SelfPanel:
        return self._panel

    def evaluate_rule(self, rule: Any) -> ThymusSelectionResult:
        """Test candidate detector rule against all self-panel reference fixtures."""
        rule_id = getattr(rule, "rule_id", str(rule))
        match_pattern = getattr(rule, "match_pattern", getattr(rule, "pattern", str(rule)))

        try:
            pattern = re.compile(match_pattern, re.IGNORECASE)
        except re.error as err:
            return ThymusSelectionResult(
                rule_id=rule_id,
                is_admitted=False,
                self_fixtures_tested=0,
                autoimmune_violations=0,
                first_violating_sample=None,
                rationale=f"Invalid regular expression syntax: {err}",
            )

        violations = 0
        first_violation: str | None = None
        violating_sample_id = ""
        violating_sample_digest = ""

        for entry in self._panel:
            if pattern.search(entry.content):
                violations += 1
                if first_violation is None:
                    first_violation = entry.content[:120]
                    violating_sample_id = entry.entry_id
                    violating_sample_digest = entry.content_sha256

        if violations > 0:
            receipt = ApoptosisReceipt.create(
                rule_id=rule_id,
                violating_sample_id=violating_sample_id,
                violating_sample_digest=violating_sample_digest,
            )
            return ThymusSelectionResult(
                rule_id=rule_id,
                is_admitted=False,
                self_fixtures_tested=self._panel.fixture_count,
                autoimmune_violations=violations,
                first_violating_sample=first_violation,
                rationale=(
                    f"Autoimmune apoptosis: candidate detector {rule_id} triggered on {violations} "
                    f"healthy self fixture(s) out of {self._panel.fixture_count}. Purged with status PURGED_SELF_REACTIVE."
                ),
                apoptosis_receipt=receipt,
            )

        return ThymusSelectionResult(
            rule_id=rule_id,
            is_admitted=True,
            self_fixtures_tested=self._panel.fixture_count,
            autoimmune_violations=0,
            first_violating_sample=None,
            rationale=(
                f"Self-tolerance certified: candidate detector {rule_id} exhibited zero cross-reactivity "
                f"across all {self._panel.fixture_count} verified self fixtures."
            ),
            apoptosis_receipt=None,
        )
