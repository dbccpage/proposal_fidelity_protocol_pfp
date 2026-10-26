"""StructureBench relational contract evaluation over a Woland bout bundle.

`EPIC-OE-OEWAS-007` asks for a `StructureBenchEvaluator` "checking syntactic and
structural AST invariants against formal contracts", under the invariant:

    Strict Structural Evidence: Claims must map to concrete StructureBench AST
    nodes; natural language consensus alone is inadmissible.

The contracts themselves are specified in
`omega_engine_woland/_design_docs/05_spec_structurebench_artifact_contracts_and_lossless_rendering.md`,
which defines three tiers over the four canonical files a bout emits
(`receipt.json`, `novella.md`, `ddc.jsonl`, `summary.json`). Run folders written
before the tape copy was retired hold the tape as `dda_actions.jsonl`; the
evaluator reads that name when it is present, so old bundles keep their verdicts:

* **C1 unary** -- each file valid on its own: strict schema, deterministically
  sorted JSON keys, UTF-8 with no byte-order mark.
* **C2 binary** -- cross-file agreement: a receipt/summary bijection on
  `task_key`, `receipt_id` and `selected_candidate_id`; a novella/action step
  bijection; and hash binding, where the receipt records the digest of each of
  the other three files.
* **C3 triplet** -- context-dependent: a `PASS_TO_MASTER` verdict obliges an
  untruncated Act VII scene, a terminal DDC step at `Phi_1 = 0, Gamma_2 = 0`,
  and a non-empty `lean4_proof_hash` in the receipt.

`persist_bout_run_folder` writes `novella.md`, then `ddc.jsonl`, then
`summary.json`, then `receipt.json`. Summary and receipt use sorted-key JSON.
The ordering check is a named Python Unicode-key ordering profile, not a claim
of RFC-8785 canonicalization. Every JSON/JSONL object must have unique keys and
finite numbers; duplicate keys,
nonfinite tokens and malformed UTF-8 are typed malformed-JSON evidence, never
last-key-wins terminal evidence.
The receipt then stores SHA-256 hex digests `novella_sha256`, `ddc_sha256`,
and `summary_sha256` of those three files. Those fields are not BLAKE3. A legacy
bundle records its tape as `dda_actions_sha256`; when such a bundle also holds
a `ddc.jsonl` copy with `ddc_sha256`, C2 checks that digest and that the two
tapes are byte-identical. `WolandBoutReceiptV1.lean4_proof_hash` is present on the bout
receipt; `bout_service` sets it to `None`. For `PASS_TO_MASTER`, a present
null or empty hash is `VIOLATED` (`lean4_proof_hash` is empty). A missing
field stays `UNVERIFIABLE`.

Each DDC step is written as ``{"payload": {...}, "parent_sha256",
"record_sha256", "sequence"}``, so `phi_1` and `gamma_2` sit under `payload`.

This module does not arbitrate a debate and does not discover skills from a
literature spine. It does not define `PolarizedDebateArbitrator` or
`CorpusGroundedDiscoveryEngine`.

A constraint whose field is absent is not a pass. A validator that treated a
missing field as satisfied would report a clean bundle for a check it did not
make.

So every constraint returns one of **four** outcomes -- `SATISFIED`,
`VIOLATED`, `UNVERIFIABLE`, `NOT_APPLICABLE` -- and only the first two are
decisions. `UNVERIFIABLE` (the evidence could not be reached, wholly or in
part) and `NOT_APPLICABLE` (the constraint's antecedent is false or its subject
is empty, so it would hold only vacuously) are never folded into either of the
others and never counted as decided. The report states all four counts, and
`is_clean()` requires every constraint to be `SATISFIED`. This is sprint 017's
rule applied at the point of design rather than discovered afterwards: a check
that does not say how much of its subject it could actually reach reports a
sample in the shape of a verdict. An earlier version reported the vacuous cases
(a non-`PASS_TO_MASTER` verdict, a bundle with no actions) as `SATISFIED`, and
checked only the files and fields that happened to be present.

`AuthorityEffect: None`. Structural conformance is not semantic soundness --
the spec's own claim-hygiene ledger says so, and this module does not exceed it.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .errors import StructureBenchError
from .pass_to_master import inspect_obligations
from .path_bundle_reader import PathBundleReader
from .ports import BundleReader
from .strict_json import (
    decode_json as _decode_json,
)
from .strict_json import (
    jsonl_key_order_findings,
)
from .strict_json import (
    keys_in_order as _keys_in_order,
)

DDC_TAPE = "ddc.jsonl"
# Tape name in run folders written before the copy was retired; read, never written.
LEGACY_DDA_TAPE = "dda_actions.jsonl"

BUNDLE_FILES = ("receipt.json", "novella.md", DDC_TAPE, "summary.json")
JSON_FILES = ("receipt.json", DDC_TAPE, "summary.json")
HASHED_FILES = ("novella.md", DDC_TAPE, "summary.json")

UTF8_BOM = b"\xef\xbb\xbf"

# The spec's section 3.1 act headers, in order. Matched by their stable prefix
# rather than the full line: the em-dash subtitle is presentation, the act
# number is the structure.
ACT_HEADERS = (
    "# Act I:",
    "# Act II:",
    "# Act III:",
    "# Act IV:",
    "# Act V:",
    "# Act VI:",
    "# Act VII:",
)

# Section 3.2, the anti-truncation law. Any of these in a rendered novella means
# the lossless guarantee was not kept.
TRUNCATION_MARKERS = (
    "... [truncated] ...",
    "[truncated]",
    "[rest of output omitted]",
    "[output omitted]",
    "... (truncated)",
)

CONSTRAINT_IDS = (
    "C1_FILES_PRESENT",
    "C1_UTF8_NO_BOM",
    "C1_JSON_PARSES",
    "C1_JSON_KEYS_SORTED",
    "C1_JSONL_ONE_OBJECT_PER_LINE",
    "C2_RECEIPT_SUMMARY_BIJECTION",
    "C2_HASH_BINDING",
    "C2_NOVELLA_ACTION_BIJECTION",
    "C3_ACT_SECTIONS_PRESENT",
    "C3_NO_TRUNCATION_MARKERS",
    "C3_PASS_TO_MASTER_OBLIGATIONS",
)

# Canonical typed terminal verdict tokens -- no float or substring matching.
VALID_TERMINAL_VERDICTS = (
    "PASS_TO_MASTER",
    "REFUSED",
    "COMPOSTED",
    "ADMITTED",
    "PROPOSED_FOR_EXTERNAL_ADMISSION",
)

# The keys the spec's receipt/summary bijection is stated over.
BIJECTION_KEYS = ("task_key", "receipt_id", "selected_candidate_id")

# Linear gate incidence over the four canonical bundle files. The tape column
# stands for `ddc.jsonl`, or for `dda_actions.jsonl` in a legacy bundle; the audit
# does not model a legacy bundle that holds both tapes.
GATE_INCIDENCE: dict[str, tuple[str, ...]] = {
    "C1_FILES_PRESENT": ("receipt.json", "novella.md", DDC_TAPE, "summary.json"),
    "C1_UTF8_NO_BOM": ("receipt.json", "novella.md", DDC_TAPE, "summary.json"),
    "C1_JSON_PARSES": ("receipt.json", "summary.json"),
    "C1_JSON_KEYS_SORTED": ("receipt.json", DDC_TAPE, "summary.json"),
    "C1_JSONL_ONE_OBJECT_PER_LINE": (DDC_TAPE,),
    "C2_RECEIPT_SUMMARY_BIJECTION": ("receipt.json", "summary.json"),
    "C2_HASH_BINDING": ("receipt.json", "novella.md", DDC_TAPE, "summary.json"),
    "C2_NOVELLA_ACTION_BIJECTION": ("novella.md", DDC_TAPE),
    "C3_ACT_SECTIONS_PRESENT": ("novella.md",),
    "C3_NO_TRUNCATION_MARKERS": ("novella.md",),
    "C3_PASS_TO_MASTER_OBLIGATIONS": (
        "receipt.json",
        "novella.md",
        DDC_TAPE,
        "summary.json",
    ),
}


@dataclass(frozen=True, slots=True)
class GateIncidenceAuditReport:
    """Outcome of exact linear gate-incidence audit calling native lggr_soundness."""

    sound: bool
    d_rank: int
    qd_rank: int
    witness: tuple[str, ...] | None
    authority_effect: str = "None"


class ConstraintOutcome(str, Enum):
    """Four outcomes; only `SATISFIED` and `VIOLATED` are decisions.

    `UNVERIFIABLE` means the evaluator could not reach the evidence -- a field
    the constraint reads does not exist in the artifact schema, or an artifact
    it reads is absent or unparseable. It is not a pass. Collapsing it into
    `SATISFIED` would report a clean bundle for a constraint nothing checked;
    collapsing it into `VIOLATED` would blame a bundle for a gap in the schema
    it was written against.

    `NOT_APPLICABLE` means the constraint was evaluated only far enough to see
    that it would hold vacuously: its antecedent is false (the verdict is not
    `PASS_TO_MASTER`) or its subject is empty (no actions). It is not a pass
    either, and it is not counted as decided.
    """

    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"
    UNVERIFIABLE = "UNVERIFIABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


DECIDED_OUTCOMES = frozenset({ConstraintOutcome.SATISFIED, ConstraintOutcome.VIOLATED})


@dataclass(frozen=True, slots=True)
class ConstraintResult:
    constraint_id: str
    outcome: ConstraintOutcome
    detail: str

    def __post_init__(self) -> None:
        if self.constraint_id not in CONSTRAINT_IDS:
            raise StructureBenchError(
                "UNKNOWN_CONSTRAINT", f"{self.constraint_id!r} is not declared"
            )
        if not self.detail:
            raise StructureBenchError(
                "EMPTY_DETAIL",
                f"{self.constraint_id} gave no reason; a verdict without a reason "
                f"cannot be acted on",
            )


@dataclass(frozen=True, slots=True)
class StructureBenchReport:
    """Every declared constraint, evaluated. Coverage stated, not implied."""

    results: tuple[ConstraintResult, ...]

    def __post_init__(self) -> None:
        seen = [result.constraint_id for result in self.results]
        if sorted(seen) != sorted(CONSTRAINT_IDS):
            missing = sorted(set(CONSTRAINT_IDS) - set(seen))
            extra = sorted(set(seen) - set(CONSTRAINT_IDS))
            raise StructureBenchError(
                "INCOMPLETE_REPORT",
                f"a report must cover every declared constraint; missing={missing} extra={extra}",
            )

    def by_outcome(self, outcome: ConstraintOutcome) -> tuple[ConstraintResult, ...]:
        return tuple(r for r in self.results if r.outcome is outcome)

    def coverage(self) -> tuple[int, int]:
        """`(decided, declared)` -- how many constraints were decided.

        Decided means `SATISFIED` or `VIOLATED`. `UNVERIFIABLE` and
        `NOT_APPLICABLE` are not decisions and are not counted.

        A pair rather than a ratio, for the same reason the skill budget census
        returns one: a percentage lets 3-of-11 and 10-of-11 round together.
        """
        decided = sum(1 for r in self.results if r.outcome in DECIDED_OUTCOMES)
        return decided, len(self.results)

    def is_clean(self) -> bool:
        """Clean means every constraint was **decided** and every one passed.

        An unverifiable constraint is not a pass. A bundle whose hash binding
        cannot be checked is not a bundle whose hash binding is sound. A
        constraint that holds only vacuously (`NOT_APPLICABLE`) is not a pass
        either.
        """
        return all(r.outcome is ConstraintOutcome.SATISFIED for r in self.results)

    def audit_gate_incidence(self, host: Any = None) -> GateIncidenceAuditReport:
        """Execute linear gate-incidence audit on this report using native lggr_soundness."""
        return audit_gate_incidence(self, host=host)

    def render(self) -> str:
        decided, declared = self.coverage()
        lines = [
            "=== STRUCTUREBENCH RELATIONAL CONTRACT REPORT ===",
            f"constraints declared : {declared}",
            f"constraints decided  : {decided}",
            f"  satisfied          : {len(self.by_outcome(ConstraintOutcome.SATISFIED))}",
            f"  violated           : {len(self.by_outcome(ConstraintOutcome.VIOLATED))}",
            f"not decided          : {declared - decided}",
            f"  unverifiable       : {len(self.by_outcome(ConstraintOutcome.UNVERIFIABLE))}",
            f"  not applicable     : {len(self.by_outcome(ConstraintOutcome.NOT_APPLICABLE))}",
            "",
        ]
        for result in self.results:
            lines.append(f"  [{result.outcome.value:14s}] {result.constraint_id}")
            lines.append(f"                 {result.detail}")
        return "\n".join(lines)


class StructureBenchEvaluator:
    """Evaluates one run directory against the declared relational contracts."""

    def __init__(
        self,
        bundle_dir: Path | str | None = None,
        *,
        bundle_reader: BundleReader | None = None,
    ) -> None:
        if bundle_dir is None and bundle_reader is None:
            raise TypeError("bundle_dir or bundle_reader is required")
        self.bundle_dir = Path(bundle_dir) if bundle_dir is not None else None
        self._bundle_reader = (
            bundle_reader if bundle_reader is not None else PathBundleReader(self.bundle_dir)
        )
        self._artifact_cache: dict[str, bytes | None] = {}
        try:
            raw_header = self._read_artifact("receipt.json")
            header = _decode_json(raw_header) if raw_header is not None else None
        except (OSError, StructureBenchError):
            header = None
        self._single_ddc = (
            isinstance(header, dict)
            and header.get("bundle_schema_version") == "omega.woland.reported-run-bundle.v2"
        )
        legacy = not self._single_ddc and self._read_artifact(LEGACY_DDA_TAPE) is not None
        self.tape = LEGACY_DDA_TAPE if legacy else DDC_TAPE
        self.tape_digest_key = "dda_actions_sha256" if legacy else "ddc_sha256"
        self.bundle_files = (
            ("receipt.json", "uns.md", DDC_TAPE, "uts.jsonl", "summary.json")
            if self._single_ddc
            else tuple(self.tape if name == DDC_TAPE else name for name in BUNDLE_FILES)
        )
        self.hashed_files = (
            ("uns.md", DDC_TAPE, "uts.jsonl", "summary.json")
            if self._single_ddc
            else tuple(self.tape if name == DDC_TAPE else name for name in HASHED_FILES)
        )

    # -- loading -------------------------------------------------------

    def _read_artifact(self, name: str) -> bytes | None:
        """Read each artifact once so every constraint sees one byte snapshot."""
        if name not in self._artifact_cache:
            self._artifact_cache[name] = self._bundle_reader.read(name)
        return self._artifact_cache[name]

    def _read(self, name: str) -> bytes | None:
        if self._single_ddc:
            name = {"novella.md": "uns.md", "dda_actions.jsonl": "ddc.jsonl"}.get(name, name)
        return self._read_artifact(name)

    def _parsed(self, name: str) -> Any:
        raw = self._read(name)
        if raw is None:
            return None
        try:
            return _decode_json(raw)
        except StructureBenchError:
            return None

    # -- C1 ------------------------------------------------------------

    def _c1_files_present(self) -> ConstraintResult:
        files = self.bundle_files
        missing = [name for name in files if self._read(name) is None]
        if missing:
            return ConstraintResult(
                "C1_FILES_PRESENT",
                ConstraintOutcome.VIOLATED,
                f"missing from the bundle: {', '.join(missing)}",
            )
        return ConstraintResult(
            "C1_FILES_PRESENT",
            ConstraintOutcome.SATISFIED,
            f"all {len(files)} canonical artifacts present",
        )

    def _c1_utf8_no_bom(self) -> ConstraintResult:
        problems = []
        unchecked = []
        files = self.bundle_files
        for name in files:
            raw = self._read(name)
            if raw is None:
                unchecked.append(name)
                continue
            if raw.startswith(UTF8_BOM):
                problems.append(f"{name} carries a byte-order mark")
                continue
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                problems.append(f"{name} is not valid UTF-8")
        if problems:
            return ConstraintResult(
                "C1_UTF8_NO_BOM", ConstraintOutcome.VIOLATED, "; ".join(problems)
            )
        if unchecked:
            return ConstraintResult(
                "C1_UTF8_NO_BOM",
                ConstraintOutcome.UNVERIFIABLE,
                f"absent, so not checked: {', '.join(unchecked)}",
            )
        return ConstraintResult(
            "C1_UTF8_NO_BOM",
            ConstraintOutcome.SATISFIED,
            "every artifact is UTF-8 with no byte-order mark",
        )

    def _c1_json_parses(self) -> ConstraintResult:
        problems = []
        for name in ("receipt.json", "summary.json"):
            raw = self._read(name)
            if raw is None:
                problems.append(f"{name} is absent")
                continue
            try:
                document = _decode_json(raw)
            except StructureBenchError as exc:
                problems.append(f"{name}: {exc}")
                continue
            if document is None:
                problems.append(f"{name} is not parseable JSON")
        if problems:
            return ConstraintResult(
                "C1_JSON_PARSES", ConstraintOutcome.VIOLATED, "; ".join(problems)
            )
        return ConstraintResult(
            "C1_JSON_PARSES",
            ConstraintOutcome.SATISFIED,
            "receipt.json and summary.json parse as JSON",
        )

    def _c1_keys_sorted(self) -> ConstraintResult:
        """Section 2.1: keys in ordinal UTF-8 byte order.

        `persist_bout_run_folder` writes `receipt.json` and `summary.json` with
        sorted JSON keys. This check reads document order after strict decoding.
        A file whose keys are not ordinal is `VIOLATED`. Dropping `sort_keys`
        on a dict built in another order is that violation.
        """
        unsorted = []
        unchecked = []
        for name in ("receipt.json", "summary.json"):
            document = self._parsed(name)
            if document is None:
                unchecked.append(f"{name} (absent or not JSON)")
                continue
            if not _keys_in_order(document):
                unsorted.append(name)
        raw = self._read(self.tape)
        if raw is None:
            unchecked.append(f"{self.tape} (absent)")
        else:
            tape_unsorted, tape_unchecked = jsonl_key_order_findings(raw, self.tape)
            unsorted.extend(tape_unsorted)
            unchecked.extend(tape_unchecked)
        if unsorted:
            return ConstraintResult(
                "C1_JSON_KEYS_SORTED",
                ConstraintOutcome.VIOLATED,
                f"keys are not in ordinal order: {', '.join(unsorted)}",
            )
        if unchecked:
            return ConstraintResult(
                "C1_JSON_KEYS_SORTED",
                ConstraintOutcome.UNVERIFIABLE,
                f"not checked: {', '.join(unchecked[:5])}",
            )
        return ConstraintResult(
            "C1_JSON_KEYS_SORTED",
            ConstraintOutcome.SATISFIED,
            "every JSON object has ordinally sorted keys",
        )

    def _c1_jsonl_shape(self) -> ConstraintResult:
        raw = self._read(self.tape)
        if raw is None:
            return ConstraintResult(
                "C1_JSONL_ONE_OBJECT_PER_LINE",
                ConstraintOutcome.VIOLATED,
                f"{self.tape} is absent",
            )
        lines = raw.splitlines()
        if not lines:
            return ConstraintResult(
                "C1_JSONL_ONE_OBJECT_PER_LINE",
                ConstraintOutcome.NOT_APPLICABLE,
                f"{self.tape} has no lines; one-object-per-line holds only vacuously",
            )
        bad = []
        for index, line in enumerate(lines, start=1):
            if not line.strip():
                bad.append(f"line {index} is blank")
                continue
            try:
                value = _decode_json(line)
            except StructureBenchError as exc:
                bad.append(f"line {index}: {exc}")
                continue
            if not isinstance(value, dict):
                bad.append(f"line {index} is not an object")
        if bad:
            return ConstraintResult(
                "C1_JSONL_ONE_OBJECT_PER_LINE",
                ConstraintOutcome.VIOLATED,
                "; ".join(bad[:5]),
            )
        return ConstraintResult(
            "C1_JSONL_ONE_OBJECT_PER_LINE",
            ConstraintOutcome.SATISFIED,
            f"{len(lines)} action lines, each one JSON object",
        )

    # -- C2 ------------------------------------------------------------

    def _c2_bijection(self) -> ConstraintResult:
        receipt = self._parsed("receipt.json")
        summary = self._parsed("summary.json")
        if not isinstance(receipt, dict) or not isinstance(summary, dict):
            return ConstraintResult(
                "C2_RECEIPT_SUMMARY_BIJECTION",
                ConstraintOutcome.UNVERIFIABLE,
                "receipt.json or summary.json is absent or not an object",
            )
        present = [key for key in BIJECTION_KEYS if key in receipt or key in summary]
        if not present:
            return ConstraintResult(
                "C2_RECEIPT_SUMMARY_BIJECTION",
                ConstraintOutcome.UNVERIFIABLE,
                f"none of {', '.join(BIJECTION_KEYS)} appears in either document; "
                f"the receipt schema the spec names was never built",
            )
        disagreeing = [key for key in present if receipt.get(key) != summary.get(key)]
        if disagreeing:
            return ConstraintResult(
                "C2_RECEIPT_SUMMARY_BIJECTION",
                ConstraintOutcome.VIOLATED,
                f"receipt and summary disagree on: {', '.join(disagreeing)}",
            )
        absent = [key for key in BIJECTION_KEYS if key not in present]
        if absent:
            return ConstraintResult(
                "C2_RECEIPT_SUMMARY_BIJECTION",
                ConstraintOutcome.UNVERIFIABLE,
                f"agree on {', '.join(present)}, but {', '.join(absent)} appears "
                f"in neither document, so the bijection on it was not checked",
            )
        return ConstraintResult(
            "C2_RECEIPT_SUMMARY_BIJECTION",
            ConstraintOutcome.SATISFIED,
            f"receipt and summary agree on {', '.join(present)}",
        )

    def _digest_key(self, name: str) -> str:
        if name == self.tape:
            return self.tape_digest_key
        return f"{name.split('.')[0]}_sha256"

    def _recorded_hashes(self, receipt: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        recorded = {name: receipt.get(self._digest_key(name)) for name in self.hashed_files}
        legacy_copy = self.tape == LEGACY_DDA_TAPE and "ddc_sha256" in receipt
        if legacy_copy:
            recorded[DDC_TAPE] = receipt["ddc_sha256"]
        return recorded, legacy_copy

    def _hash_mismatches(self, recorded: dict[str, Any]) -> list[str]:
        wrong = []
        for name, claimed in recorded.items():
            raw = self._read(name)
            if raw is None:
                wrong.append(f"{name} is absent but its digest is claimed")
                continue
            actual = hashlib.sha256(raw).hexdigest()
            if claimed is None:
                wrong.append(f"{name} has no recorded digest")
            elif str(claimed).removeprefix("sha256:") != actual:
                wrong.append(f"{name} digest does not match its bytes")
        return wrong

    def _legacy_copy_mismatch(self) -> bool:
        ddc = self._read(DDC_TAPE)
        dda = self._read(LEGACY_DDA_TAPE)
        return ddc is not None and dda is not None and ddc != dda

    def _c2_hash_binding(self) -> ConstraintResult:
        """Bind the novella, the tape and the summary to the receipt's digests.

        The tape is `ddc.jsonl` under `ddc_sha256`. A legacy bundle holds it as
        `dda_actions.jsonl` under `dda_actions_sha256`; when that bundle also holds
        a `ddc.jsonl` copy with `ddc_sha256`, the copy must bind its own bytes and
        equal the legacy tape exactly.

        Unverifiable rather than violated when the receipt carries no digest
        field at all: the bundle is not failing a check, it is being measured
        against a schema that was never built. Saying `VIOLATED` would blame the
        wrong thing, and saying `SATISFIED` would be a lie.
        """
        receipt = self._parsed("receipt.json")
        if not isinstance(receipt, dict):
            return ConstraintResult(
                "C2_HASH_BINDING",
                ConstraintOutcome.UNVERIFIABLE,
                "receipt.json is absent or not an object",
            )
        recorded, legacy_copy = self._recorded_hashes(receipt)
        if not any(recorded.values()):
            return ConstraintResult(
                "C2_HASH_BINDING",
                ConstraintOutcome.UNVERIFIABLE,
                "the receipt records no artifact digests; hash binding cannot be checked",
            )
        wrong = self._hash_mismatches(recorded)
        if legacy_copy and self._legacy_copy_mismatch():
            wrong.append("ddc.jsonl is not an exact byte copy of dda_actions.jsonl")
        if wrong:
            return ConstraintResult("C2_HASH_BINDING", ConstraintOutcome.VIOLATED, "; ".join(wrong))
        return ConstraintResult(
            "C2_HASH_BINDING",
            ConstraintOutcome.SATISFIED,
            f"the receipt binds the digests of all {len(recorded)} declared artifacts",
        )

    def _c2_novella_action_bijection(self) -> ConstraintResult:
        """Section 2.2: every action at timestamp t has a scene turn in the novella."""
        raw = self._read(self.tape)
        novella = self._read("novella.md")
        if raw is None or novella is None:
            return ConstraintResult(
                "C2_NOVELLA_ACTION_BIJECTION",
                ConstraintOutcome.UNVERIFIABLE,
                f"{self.tape} or novella.md is absent",
            )
        lines = [line for line in raw.splitlines() if line.strip()]
        if not lines:
            return ConstraintResult(
                "C2_NOVELLA_ACTION_BIJECTION",
                ConstraintOutcome.NOT_APPLICABLE,
                "no actions recorded; the bijection would hold only vacuously",
            )
        steps = []
        unreadable = 0
        for line in lines:
            try:
                steps.append(_decode_json(line))
            except StructureBenchError:
                unreadable += 1
        keyed = [step for step in steps if isinstance(step, dict) and "timestamp" in step]
        unkeyed = len(lines) - len(keyed)
        if not keyed:
            return ConstraintResult(
                "C2_NOVELLA_ACTION_BIJECTION",
                ConstraintOutcome.UNVERIFIABLE,
                f"none of {len(lines)} action lines carries a `timestamp`; the spec "
                f"keys this bijection on one",
            )
        text = novella.decode("utf-8", errors="replace")
        unmatched = [str(step["timestamp"]) for step in keyed if str(step["timestamp"]) not in text]
        if unmatched:
            return ConstraintResult(
                "C2_NOVELLA_ACTION_BIJECTION",
                ConstraintOutcome.VIOLATED,
                f"{len(unmatched)} action timestamps have no scene turn: "
                f"{', '.join(unmatched[:3])}",
            )
        if unkeyed:
            return ConstraintResult(
                "C2_NOVELLA_ACTION_BIJECTION",
                ConstraintOutcome.UNVERIFIABLE,
                f"{len(keyed)} timestamped actions appear in the novella, but "
                f"{unkeyed} of {len(lines)} action lines ({unreadable} not JSON) "
                f"carry no `timestamp` and were not checked",
            )
        return ConstraintResult(
            "C2_NOVELLA_ACTION_BIJECTION",
            ConstraintOutcome.SATISFIED,
            f"all {len(keyed)} timestamped actions appear in the novella",
        )

    # -- C3 ------------------------------------------------------------

    def _c3_act_sections(self) -> ConstraintResult:
        novella = self._read("novella.md")
        if novella is None:
            return ConstraintResult(
                "C3_ACT_SECTIONS_PRESENT",
                ConstraintOutcome.VIOLATED,
                "novella.md is absent",
            )
        text = novella.decode("utf-8", errors="replace")
        lines = [line.strip() for line in text.splitlines()]
        positions = []
        for header in ACT_HEADERS:
            act_name = header.lstrip("#").strip()
            matching = [
                idx
                for idx, line in enumerate(lines)
                if any(
                    line == f"{prefix} {act_name}" or line.startswith(f"{prefix} {act_name} ")
                    for prefix in ("#", "##")
                )
            ]
            if not matching:
                return ConstraintResult(
                    "C3_ACT_SECTIONS_PRESENT",
                    ConstraintOutcome.VIOLATED,
                    f"novella.md has no section headed {header!r}",
                )
            positions.append(matching[0])
        if positions != sorted(positions):
            return ConstraintResult(
                "C3_ACT_SECTIONS_PRESENT",
                ConstraintOutcome.VIOLATED,
                "the seven acts do not appear in order",
            )
        return ConstraintResult(
            "C3_ACT_SECTIONS_PRESENT",
            ConstraintOutcome.SATISFIED,
            f"all {len(ACT_HEADERS)} acts present and in order",
        )

    def _c3_no_truncation(self) -> ConstraintResult:
        novella = self._read("novella.md")
        if novella is None:
            return ConstraintResult(
                "C3_NO_TRUNCATION_MARKERS",
                ConstraintOutcome.VIOLATED,
                "novella.md is absent",
            )
        text = novella.decode("utf-8", errors="replace")
        found = [marker for marker in TRUNCATION_MARKERS if marker in text]
        if found:
            return ConstraintResult(
                "C3_NO_TRUNCATION_MARKERS",
                ConstraintOutcome.VIOLATED,
                f"the lossless law is broken by: {', '.join(repr(m) for m in found)}",
            )
        return ConstraintResult(
            "C3_NO_TRUNCATION_MARKERS",
            ConstraintOutcome.SATISFIED,
            "no truncation placeholder appears in the novella",
        )

    def _c3_pass_to_master(self) -> ConstraintResult:
        """Section 2.3: a PASS_TO_MASTER verdict carries three obligations."""
        summary = self._parsed("summary.json")
        if not isinstance(summary, dict):
            return ConstraintResult(
                "C3_PASS_TO_MASTER_OBLIGATIONS",
                ConstraintOutcome.UNVERIFIABLE,
                "summary.json is absent or not an object",
            )
        if "terminal_verdict" not in summary:
            return ConstraintResult(
                "C3_PASS_TO_MASTER_OBLIGATIONS",
                ConstraintOutcome.UNVERIFIABLE,
                "summary.json declares no `terminal_verdict`; the antecedent of "
                "this constraint cannot be evaluated",
            )
        verdict = summary["terminal_verdict"]
        if verdict not in VALID_TERMINAL_VERDICTS:
            return ConstraintResult(
                "C3_PASS_TO_MASTER_OBLIGATIONS",
                ConstraintOutcome.VIOLATED,
                f"terminal_verdict {verdict!r} is not a valid typed token "
                f"from {VALID_TERMINAL_VERDICTS}",
            )
        if verdict != "PASS_TO_MASTER":
            return ConstraintResult(
                "C3_PASS_TO_MASTER_OBLIGATIONS",
                ConstraintOutcome.NOT_APPLICABLE,
                f"verdict is {verdict!r}; the obligations do not attach, so nothing was checked",
            )

        findings = inspect_obligations(
            novella=self._read("novella.md"),
            tape=self._read(self.tape),
            tape_name=self.tape,
            receipt=self._parsed("receipt.json"),
        )
        if findings.unmet:
            return ConstraintResult(
                "C3_PASS_TO_MASTER_OBLIGATIONS",
                ConstraintOutcome.VIOLATED,
                "; ".join(findings.unmet),
            )
        if findings.unreachable:
            return ConstraintResult(
                "C3_PASS_TO_MASTER_OBLIGATIONS",
                ConstraintOutcome.UNVERIFIABLE,
                "; ".join(findings.unreachable),
            )
        return ConstraintResult(
            "C3_PASS_TO_MASTER_OBLIGATIONS",
            ConstraintOutcome.SATISFIED,
            "all three PASS_TO_MASTER obligations are met",
        )

    @classmethod
    def evaluate_run_folder(cls, bundle_dir: Path | str) -> StructureBenchReport:
        """Evaluate one run directory against the declared relational contracts."""
        return cls(bundle_dir).evaluate()

    def evaluate(self) -> StructureBenchReport:
        if not self._bundle_reader.is_bundle():
            location = self.bundle_dir if self.bundle_dir is not None else "injected reader"
            raise StructureBenchError("BUNDLE_ABSENT", f"no bundle directory at {location}")
        return StructureBenchReport(
            results=(
                self._c1_files_present(),
                self._c1_utf8_no_bom(),
                self._c1_json_parses(),
                self._c1_keys_sorted(),
                self._c1_jsonl_shape(),
                self._c2_bijection(),
                self._c2_hash_binding(),
                self._c2_novella_action_bijection(),
                self._c3_act_sections(),
                self._c3_no_truncation(),
                self._c3_pass_to_master(),
            )
        )

    def audit_gate_incidence(
        self, report: StructureBenchReport | None = None, host: Any = None
    ) -> GateIncidenceAuditReport:
        """Audit gate incidence of this evaluator's bundle directory."""
        if report is None:
            report = self.evaluate()
        return audit_gate_incidence(report, host=host)


def build_gate_incidence_matrix() -> tuple[tuple[str, ...], tuple[str, ...], list[list[str]]]:
    """Build the exact rational linear gate-incidence matrix D (gates x artifacts).

    Returns (CONSTRAINT_IDS, BUNDLE_FILES, rows_as_exact_strings).
    """
    rows = []
    for g in CONSTRAINT_IDS:
        rows.append(["1" if f in GATE_INCIDENCE.get(g, ()) else "0" for f in BUNDLE_FILES])
    return CONSTRAINT_IDS, BUNDLE_FILES, rows


def audit_gate_incidence(
    report: StructureBenchReport | None = None,
    host: Any = None,
) -> GateIncidenceAuditReport:
    """Audit linear gate incidence using exact LGGR V soundness check rank(Q·D) = rank(D).

    D is the 11x4 gate-artifact incidence matrix over Q.
    Q is the 11x11 diagonal observation projector: Q_ii = 1 if gate i was decided
    (SATISFIED or VIOLATED), and 0 if it was not (UNVERIFIABLE or NOT_APPLICABLE),
    or all 1s if report is None.

    Soundness holds iff rank(Q·D) = rank(D). When soundness fails, returns an unsoundness
    witness vector v with D v != 0 and Q D v = 0.
    """
    if host is None:
        from omega_engine_pfp.ffi import get_default_host

        host = get_default_host()

    _, _, d_matrix = build_gate_incidence_matrix()
    dim_gates = len(CONSTRAINT_IDS)

    # Build Q matrix (dim_gates x dim_gates)
    q_matrix = [["0"] * dim_gates for _ in range(dim_gates)]
    if report is None:
        for i in range(dim_gates):
            q_matrix[i][i] = "1"
    else:
        decided_ids = {r.constraint_id for r in report.results if r.outcome in DECIDED_OUTCOMES}
        for i, cid in enumerate(CONSTRAINT_IDS):
            if cid in decided_ids:
                q_matrix[i][i] = "1"

    outcome = host.lggr_soundness(d_matrix, q_matrix)
    if not outcome.is_ok:
        refusal = outcome.unwrap_err()
        raise StructureBenchError("LGGR_SOUNDNESS_FAILED", f"lggr_soundness FFI refused: {refusal}")

    raw_result = outcome.unwrap()["result"]
    witness = tuple(raw_result["witness"]) if raw_result.get("witness") is not None else None
    return GateIncidenceAuditReport(
        sound=bool(raw_result["sound"]),
        d_rank=int(raw_result["d_rank"]),
        qd_rank=int(raw_result["qd_rank"]),
        witness=witness,
        authority_effect=str(raw_result.get("authority_effect", "None")),
    )


def evaluate_bundle(bundle_dir: Path | str) -> StructureBenchReport:
    return StructureBenchEvaluator(bundle_dir).evaluate()


__all__ = [
    "ACT_HEADERS",
    "BIJECTION_KEYS",
    "BUNDLE_FILES",
    "DDC_TAPE",
    "CONSTRAINT_IDS",
    "GATE_INCIDENCE",
    "GateIncidenceAuditReport",
    "HASHED_FILES",
    "LEGACY_DDA_TAPE",
    "TRUNCATION_MARKERS",
    "VALID_TERMINAL_VERDICTS",
    "ConstraintOutcome",
    "ConstraintResult",
    "StructureBenchError",
    "StructureBenchEvaluator",
    "StructureBenchReport",
    "audit_gate_incidence",
    "build_gate_incidence_matrix",
    "evaluate_bundle",
]
