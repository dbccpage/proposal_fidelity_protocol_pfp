#!/usr/bin/env python3
"""Hash-chained DDC trace emission with explicit residual semantics.

**AuthorityEffect:** None. A trace records what a runner did. It is not
evidence that the runner was right, and no tape here discharges a residual.

Canonical Discrete Deformation Calculus (DDC) 8-letter operational alphabet:
    A_DDC = {E, R, C, I, Λ, D, M, T}
under the Nine-Layer CODA Stack invariants.
"""

from __future__ import annotations

import enum
import hashlib
import json
import math
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType, TracebackType
from typing import Any

from typing_extensions import Self

__all__ = [
    "DDCTapeDFA",
    "DDCTapeValidationError",
    "DdcDialect",
    "DdcLetter",
    "DDATapeDFA",
    "DDATapeValidationError",
    "DdaDialect",
    "DdaLetter",
    "TraceLogger",
    "_get_default_trace_dir",
]


# --- alphabet and dialects ---------------------------------------------------


class DdcLetter(str, enum.Enum):
    """OE-010 operational alphabet A_DDC = {E, R, C, I, Λ, D, M, T}."""

    E = "E"  # Exact Repair
    R = "R"  # Residual Projection
    C = "C"  # Context Exposure
    I = "I"  # Integration
    LAMBDA = "Λ"  # Structural Lift
    D = "D"  # Descent
    M = "M"  # Typed Refusal
    T = "T"  # Terminalization


class DdcDialect(str, enum.Enum):
    LEGACY_V1 = "legacy-v1"
    OEARS_V1 = "oears-v1"
    EXPERIMENTAL_Z_V1 = "experimental-z-v1"


# --- tape grammar ------------------------------------------------------------


class DDCTapeValidationError(ValueError):
    """Raised when a DDC tape violates grammar or terminal absorption rules."""


class DDCTapeDFA:
    """Fail-closed validator for versioned DDC letter-calculus dialects.

    Two incompatible refusal laws exist. The dialect is therefore
    evidence carried by the tape, not an implicit global choice.
    ``experimental-z-v1`` adds ``Z·T`` for a refused or unresolved research
    target; ``Z`` never denotes a removed obstruction.
    """

    LEGACY_V1 = "legacy-v1"
    OEARS_V1 = "oears-v1"
    EXPERIMENTAL_Z_V1 = "experimental-z-v1"

    # Immutable by construction. A grammar that any caller could mutate is not
    # a grammar; `_validate` copies the alphabet before adjusting it per dialect.
    _BASE_ALPHABET = frozenset({"E", "R", "C", "I", "Λ", "D", "M", "T"})
    _EXPERIMENTAL_START = frozenset({"E", "R"})
    _NON_TERMINAL_SUCCESSORS = frozenset(
        {"E", "R", "C", "I", "Λ", "D", "Z", "T"}
    )
    _EXPERIMENTAL_TRANSITIONS = MappingProxyType(
        {
            "E": _NON_TERMINAL_SUCCESSORS,
            "R": _NON_TERMINAL_SUCCESSORS,
            "C": _NON_TERMINAL_SUCCESSORS,
            "Λ": _NON_TERMINAL_SUCCESSORS,
            "D": _NON_TERMINAL_SUCCESSORS,
            # I and Z are absorbed by T; T absorbs everything.
            "I": frozenset({"T"}),
            "Z": frozenset({"T"}),
            "T": frozenset(),
        }
    )

    @classmethod
    def tokenize(cls, tape: str) -> list[str]:
        value = tape.strip()
        if not value:
            raise DDCTapeValidationError("DDC tape cannot be empty.")

        separated = re.sub(r"[.\-\s]+", " ", value).strip()
        if " " in separated:
            tokens: list[str] = []
            for tok in separated.split():
                if tok in ("L", "Lambda"):
                    tokens.append("Λ")
                else:
                    tokens.append(tok)
            return tokens

        tokens: list[str] = []
        cursor = 0
        while cursor < len(separated):
            if separated.startswith("Lambda", cursor):
                tokens.append("Λ")
                cursor += len("Lambda")
            else:
                tok = separated[cursor]
                if tok == "L":
                    tokens.append("Λ")
                else:
                    tokens.append(tok)
                cursor += 1
        return tokens

    @classmethod
    def _validate(cls, tape: str, dialect: str, *, require_complete: bool) -> bool:
        dialect_value = getattr(dialect, "value", dialect)
        if dialect_value not in {
            cls.LEGACY_V1,
            cls.OEARS_V1,
            cls.EXPERIMENTAL_Z_V1,
        }:
            raise DDCTapeValidationError(f"Unknown DDC dialect '{dialect_value}'.")

        tokens = cls.tokenize(tape)
        alphabet = set(cls._BASE_ALPHABET)
        if dialect_value == cls.EXPERIMENTAL_Z_V1:
            alphabet.remove("M")
            alphabet.add("Z")
            if tokens[0] not in cls._EXPERIMENTAL_START:
                raise DDCTapeValidationError(
                    f"Experimental DDC tape must start with E or R, got '{tokens[0]}'."
                )
            if require_complete and tokens[-1] != "T":
                if tokens[-1] == "Z":
                    raise DDCTapeValidationError(
                        "Experimental refusal Z must be followed by T, got "
                        "'end-of-tape'."
                    )
                raise DDCTapeValidationError(
                    "Experimental DDC tape must end with terminal T."
                )

        for index, token in enumerate(tokens):
            if token not in alphabet:
                raise DDCTapeValidationError(
                    f"Invalid DDC letter '{token}' at index {index} "
                    f"for dialect {dialect_value}."
                )

            if token == "T" and index != len(tokens) - 1:
                raise DDCTapeValidationError(
                    f"T absorption rule violated: letter '{tokens[index + 1]}' "
                    "after terminal T."
                )

            if token == "M":
                if dialect_value == cls.LEGACY_V1:
                    if index < len(tokens) - 1 and tokens[index + 1] != "T":
                        raise DDCTapeValidationError(
                            "Refusal letter M must be followed by terminal T, "
                            f"got '{tokens[index + 1]}'."
                        )
                elif index != len(tokens) - 1:
                    raise DDCTapeValidationError(
                        "OEARS refusal M is terminal and cannot be followed by "
                        f"'{tokens[index + 1]}'."
                    )

            if token == "Z":
                if require_complete and index == len(tokens) - 1:
                    raise DDCTapeValidationError(
                        "Experimental refusal Z must be followed by T, got "
                        "'end-of-tape'."
                    )
                if index < len(tokens) - 1 and tokens[index + 1] != "T":
                    following = (
                        "end-of-tape" if index == len(tokens) - 1 else tokens[index + 1]
                    )
                    raise DDCTapeValidationError(
                        f"Experimental refusal Z must be followed by T, "
                        f"got '{following}'."
                    )

            if dialect_value == cls.EXPERIMENTAL_Z_V1 and index < len(tokens) - 1:
                following = tokens[index + 1]
                if following not in cls._EXPERIMENTAL_TRANSITIONS[token]:
                    raise DDCTapeValidationError(
                        f"Invalid experimental DDC transition '{token}·{following}'."
                    )

        return True

    @classmethod
    def validate_prefix(cls, tape: str, dialect: str = LEGACY_V1) -> bool:
        """Validate an incrementally emitted tape without requiring its terminus."""
        return cls._validate(tape, dialect, require_complete=False)

    @classmethod
    def validate(cls, tape: str, dialect: str = LEGACY_V1) -> bool:
        """Validate a complete tape under its declared versioned dialect."""
        return cls._validate(tape, dialect, require_complete=True)


# --- Backward compatibility aliases ---
DdaLetter = DdcLetter
DdaDialect = DdcDialect
DDATapeValidationError = DDCTapeValidationError
DDATapeDFA = DDCTapeDFA


# --- trace logger ------------------------------------------------------------


def _get_default_trace_dir() -> Path:
    trace_dir = Path(tempfile.gettempdir()) / "coda_ddc_traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    return trace_dir


def _step_hash(record: dict[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key != "step_hash"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _default_effect(letter: str) -> str:
    return {
        "C": "context_exposed",
        "R": "residual_carried",
        "E": "obstruction_eliminated",
        "I": "integration",
        "Λ": "structure_added",
        "Lambda": "structure_added",
        "L": "structure_added",
        "D": "descent",
        "M": "refusal",
        "Z": "refusal",
        "T": "terminalization",
    }.get(letter, "unclassified")


class TraceLogger:
    """Append-only JSONL logger for replayable letter-calculus experiments.

    ``experimental-z-v1`` is deliberately non-canonical. In that dialect a
    refused or still-unresolved target is recorded as ``Z·T`` and retains its
    residual. It is never counted as an obstruction removal.
    """

    def __init__(
        self,
        runner_id: str,
        campaign_name: str = "",
        trace_dir: Path | None = None,
        dialect: DdcDialect | DdaDialect | str = DdcDialect.LEGACY_V1,
        auto_lifecycle: bool = True,
    ) -> None:
        self.runner_id = runner_id
        self.campaign_name = campaign_name or runner_id
        self.trace_dir = Path(trace_dir) if trace_dir else _get_default_trace_dir()
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.dialect = (
            dialect.value if hasattr(dialect, "value") else str(dialect)
        )
        self.auto_lifecycle = auto_lifecycle
        self.run_id = uuid.uuid4().hex[:12]
        safe_runner = (
            re.sub(r"[^A-Za-z0-9_.-]+", "_", self.runner_id).strip("_") or "runner"
        )
        self.jsonl_path = (
            self.trace_dir / f"{safe_runner}_{self.run_id}_ddc_trace.jsonl"
        )
        self._last_hash: str | None = None
        self._step_counter = 0
        self._finalized = False
        self.steps: list[dict[str, Any]] = []

    @property
    def tape(self) -> list[str]:
        return [str(step["letter"]) for step in self.steps]

    def __enter__(self) -> Self:
        if self.auto_lifecycle:
            start_letter = (
                DdcLetter.R
                if self.dialect == DdcDialect.EXPERIMENTAL_Z_V1.value
                else DdcLetter.C
            )
            self.record_step(
                letter=start_letter,
                action_name=f"start:{self.runner_id}",
                input_state=f"INITIAL_EXPOSURE:{self.runner_id}",
                output_state=f"RUNNING:{self.runner_id}",
                witness=f"WIT_START_{self.run_id}",
                effect="context_exposed",
            )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._finalized or not self.auto_lifecycle:
            return
        if exc_type is not None:
            self.refuse(
                reason=str(exc_val) or exc_type.__name__,
                input_state=f"RUNNING:{self.runner_id}",
                output_state=f"FAILED:{self.runner_id}",
                witness=f"WIT_FAIL_{self.run_id}",
            )
        else:
            self.finalize_success(
                input_state=f"RUNNING:{self.runner_id}",
                output_state=f"COMPLETED:{self.runner_id}",
                witness=f"WIT_INTEGRATE_{self.run_id}",
            )

    def record_step(
        self,
        letter: DdcLetter | DdaLetter | str,
        action_name: str,
        input_state: str,
        output_state: str,
        witness: str,
        residual_energy: float | None = None,
        refusal_reason: str | None = None,
        cochain_dim: str = "C1",
        coboundary_map: str = "d1",
        *,
        residual_before: float | None = None,
        residual_after: float | None = None,
        effect: str | None = None,
        obstruction_id: str | None = None,
        structure_delta: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._finalized:
            raise RuntimeError("Cannot append a DDC step after terminalization.")

        letter_str = letter.value if hasattr(letter, "value") else str(letter)
        after = residual_after if residual_after is not None else residual_energy
        energy = 0.0 if after is None else float(after)
        effect_value = effect or _default_effect(letter_str)
        if letter_str == "Z":
            if self.dialect != DdcDialect.EXPERIMENTAL_Z_V1.value:
                raise ValueError("Z is only valid in the experimental-z-v1 dialect.")
            if effect_value != "refusal":
                raise ValueError("Z is a refusal and cannot carry another effect.")
            if (
                residual_before is not None
                and after is not None
                and float(residual_before) != float(after)
            ):
                raise ValueError("Z must retain the unresolved residual unchanged.")
        if letter_str == "E" and effect_value != "obstruction_eliminated":
            raise ValueError("DDC letter E requires the obstruction_eliminated effect.")
        if letter_str in {"L", "Lambda", "Λ"} and effect_value != "structure_added":
            raise ValueError("A lift letter requires the structure_added effect.")
        if effect_value == "obstruction_eliminated" and letter_str in {"M", "Z"}:
            raise ValueError("A refusal letter cannot eliminate an obstruction.")
        if effect_value == "obstruction_eliminated":
            if letter_str != "E":
                raise ValueError("Obstruction elimination requires DDC letter E.")
            if not obstruction_id:
                raise ValueError("Obstruction elimination requires an obstruction id.")
            if residual_before is None or after is None:
                raise ValueError(
                    "Obstruction elimination requires before/after residuals."
                )
            if not math.isfinite(float(residual_before)) or not math.isfinite(
                float(after)
            ):
                raise ValueError("Obstruction elimination residuals must be finite.")
            if float(after) >= float(residual_before):
                raise ValueError(
                    "Obstruction elimination requires strict residual decrease."
                )
        if effect_value == "structure_added":
            if letter_str not in {"L", "Lambda", "Λ"}:
                raise ValueError("Structure addition requires a lift letter.")
            if not structure_delta:
                raise ValueError(
                    "Structure addition requires a nonempty structure delta."
                )

        candidate_tape = ".".join([*self.tape, letter_str])
        is_terminal = letter_str == "T" or (
            letter_str == "M" and self.dialect == DdcDialect.OEARS_V1.value
        )
        if is_terminal:
            DDCTapeDFA.validate(candidate_tape, dialect=self.dialect)
        else:
            DDCTapeDFA.validate_prefix(candidate_tape, dialect=self.dialect)

        self._step_counter += 1
        delta = None
        if residual_before is not None and after is not None:
            delta = float(after) - float(residual_before)

        record: dict[str, Any] = {
            "schema_version": "omega.ddc.trace.v2",
            "ddc_dialect": self.dialect,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "runner_id": self.runner_id,
            "campaign": self.campaign_name,
            "run_id": self.run_id,
            "step_id": f"DDC_STEP_{self._step_counter:03d}",
            "letter": letter_str,
            "effect": effect_value,
            "action_name": action_name,
            "cochain_dim": cochain_dim,
            "coboundary_map": coboundary_map,
            "input_state": input_state,
            "output_state": output_state,
            "witness": witness,
            "obstruction_id": obstruction_id,
            "residual_before": residual_before,
            "residual_after": after,
            "residual_delta": delta,
            "residual_energy": energy,
            "structure_delta": structure_delta or {},
            "evidence": evidence or {},
            "refusal_reason": refusal_reason,
            "authority_effect": "None",
            "prev_step_hash": self._last_hash,
        }
        record["step_hash"] = _step_hash(record)
        self._last_hash = record["step_hash"]
        self.steps.append(record)

        with self.jsonl_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")

        if letter_str == "T" or (
            letter_str == "M" and self.dialect == DdcDialect.OEARS_V1.value
        ):
            self._finalized = True
        return record

    def finalize_success(
        self,
        input_state: str,
        output_state: str,
        witness: str,
        *,
        residual: float | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        self.record_step(
            letter=DdcLetter.I,
            action_name=f"integrate:{self.runner_id}",
            input_state=input_state,
            output_state=output_state,
            witness=witness,
            residual_before=residual,
            residual_after=residual,
            effect="integration",
            evidence=evidence,
        )
        self.record_step(
            letter=DdcLetter.T,
            action_name=f"terminalize:{self.runner_id}",
            input_state=output_state,
            output_state=f"TERMINALIZED:{self.runner_id}",
            witness=f"WIT_TERMINAL_{self.run_id}",
            residual_before=residual,
            residual_after=residual,
            effect="terminalization",
        )

    def refuse(
        self,
        reason: str,
        input_state: str,
        output_state: str,
        witness: str,
        *,
        residual: float | None = None,
        obstruction_id: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        refusal_letter = (
            "Z" if self.dialect == DdcDialect.EXPERIMENTAL_Z_V1.value else "M"
        )
        self.record_step(
            letter=refusal_letter,
            action_name=f"refuse:{self.runner_id}",
            input_state=input_state,
            output_state=output_state,
            witness=witness,
            residual_before=residual,
            residual_after=residual,
            effect="refusal",
            obstruction_id=obstruction_id,
            refusal_reason=reason,
            evidence=evidence,
        )
        if self.dialect != DdcDialect.OEARS_V1.value:
            self.record_step(
                letter=DdcLetter.T,
                action_name=f"terminalize:{self.runner_id}",
                input_state=output_state,
                output_state=f"TERMINALIZED:{self.runner_id}",
                witness=f"WIT_TERMINAL_{self.run_id}",
                residual_before=residual,
                residual_after=residual,
                effect="terminalization",
            )
