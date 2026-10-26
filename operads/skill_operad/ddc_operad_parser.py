"""DDC Tape to Colored Operad Morphism Parser.

Translates Discrete Deformation Calculus (DDC) 8-letter event tapes (ddc.jsonl)
into verified planar colored operad morphisms, enforces candidate runtime laws,
and computes exact rational residual contraction receipts.

AuthorityEffect: None.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

try:
    from .coloured_operad import Colour, ColouredOperad, Operation
    from .coloured_operad import EMPTY, ColoredOp, Residual
except (ImportError, ValueError):
    from coloured_operad import Colour, ColouredOperad, Operation  # type: ignore[no-redef]
    from coloured_operad import EMPTY, ColoredOp, Residual  # type: ignore[no-redef]

DDC_CANONICAL_LETTERS = ("E", "R", "C", "I", "Λ", "D", "M", "T")

LETTER_SYNONYMS = {
    "L": "Λ",
    "Lambda": "Λ",
    "\\Lambda": "Λ",
    "Meta": "Λ",
}

# Standard Colored Operad Sorts
SORT_STATE = "State"
SORT_PROOF = "Proof"
SORT_RECEIPT = "Receipt"
SORT_AUDIT = "Audit"
SORT_CONTRACT = "Contract"
SORT_LEDGER = "Ledger"
SORT_CODE = "Code"
SORT_PAPER = "Paper"

OPERAD_MAPPING_DEFAULTS: dict[str, tuple[tuple[str, ...], str, str]] = {
    "C": ((SORT_STATE,), SORT_STATE, "context_exposure"),
    "R": ((SORT_STATE,), SORT_RECEIPT, "residual_projection"),
    "E": ((SORT_RECEIPT, SORT_PROOF), SORT_RECEIPT, "exact_repair"),
    "M": ((SORT_RECEIPT,), SORT_AUDIT, "typed_refusal"),
    "Λ": ((SORT_RECEIPT, SORT_CONTRACT), SORT_STATE, "structural_lift"),
    "D": ((SORT_STATE,), SORT_STATE, "scale_descent"),
    "I": ((SORT_RECEIPT, SORT_LEDGER), SORT_LEDGER, "merkle_integration"),
    "T": ((SORT_LEDGER,), SORT_RECEIPT, "terminalization"),
}


def _canonical_fraction(val: Any) -> Fraction | None:
    if val is None:
        return None
    if isinstance(val, Fraction):
        return val
    if isinstance(val, (int, float)):
        return Fraction(val).limit_denominator(1_000_000)
    if isinstance(val, str):
        val = val.strip()
        if not val or val == "None":
            return None
        if "/" in val:
            parts = val.split("/")
            if len(parts) == 2:
                try:
                    return Fraction(int(parts[0]), int(parts[1]))
                except ValueError:
                    return None
        try:
            return Fraction(val)
        except ValueError:
            return None
    return None


def _format_fraction(val: Fraction | None) -> str | None:
    if val is None:
        return None
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"


def _normalize_letter(letter: str) -> str:
    cleaned = letter.strip()
    return LETTER_SYNONYMS.get(cleaned, cleaned)


@dataclass(frozen=True)
class DdcParsedStep:
    """One verified step extracted from a DDC tape record."""

    sequence: int
    letter: str
    parent_sha256: str | None
    record_sha256: str
    before_class: str
    after_class: str
    carrier_hash: str
    witness_hash: str | None
    receipt_sha256: str | None
    phi_1: Fraction | None
    gamma_2: Fraction | None
    payload: dict[str, Any]

    @property
    def total_residual(self) -> Fraction | None:
        if self.phi_1 is None and self.gamma_2 is None:
            return None
        p = self.phi_1 or Fraction(0)
        g = self.gamma_2 or Fraction(0)
        return p + g


@dataclass(frozen=True)
class DdcMorphismMapping:
    """Operadic morphism representation corresponding to a DDC transition."""

    step_index: int
    letter: str
    source_colors: tuple[str, ...]
    target_color: str
    op_name: str
    op_id: str
    residual_effect: str
    colored_op: ColoredOp


@dataclass(frozen=True)
class OperadCompositionReceipt:
    """Cryptographic audit receipt certifying DDC tape parsing into an operadic composition."""

    tape_path: str
    run_id: str
    step_count: int
    tape_str: str
    hash_chain_valid: bool
    ddc_laws_valid: bool
    law_violations: tuple[str, ...]
    initial_phi1: str | None
    initial_gamma2: str | None
    terminal_phi1: str | None
    terminal_gamma2: str | None
    initial_residual: str | None
    terminal_residual: str | None
    residual_delta: str | None
    residual_effect: str
    morphism_count: int
    authority_effect: str = "None"

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_effect": self.authority_effect,
            "ddc_laws_valid": self.ddc_laws_valid,
            "hash_chain_valid": self.hash_chain_valid,
            "initial_gamma2": self.initial_gamma2,
            "initial_phi1": self.initial_phi1,
            "initial_residual": self.initial_residual,
            "law_violations": list(self.law_violations),
            "morphism_count": self.morphism_count,
            "residual_delta": self.residual_delta,
            "residual_effect": self.residual_effect,
            "run_id": self.run_id,
            "step_count": self.step_count,
            "tape_path": self.tape_path,
            "tape_str": self.tape_str,
            "terminal_gamma2": self.terminal_gamma2,
            "terminal_phi1": self.terminal_phi1,
            "terminal_residual": self.terminal_residual,
        }


class DdcOperadParser:
    """Parses and validates DDC action tapes and compiles them to operadic multicategories."""

    def __init__(self, source: Path | str | Sequence[dict[str, Any]]) -> None:
        self.source = source
        self.steps: list[DdcParsedStep] = []
        self.morphisms: list[DdcMorphismMapping] = []
        self._tape_path_str: str = ""
        self._run_id: str = "unknown"

    def parse(self) -> Result[OperadCompositionReceipt, Refusal]:
        """Parse, validate hash chain, verify DDC laws, and generate operad morphisms."""
        records, load_err = self._load_records()
        if load_err is not None:
            return Err(load_err)

        if not records:
            return Err(
                Refusal(
                    code="EMPTY_DDC_TAPE",
                    message="DDC tape contains zero action records",
                    locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                )
            )

        # 1. Parse steps and validate hash chaining
        hash_valid, hash_err = self._parse_and_validate_hash_chain(records)
        if not hash_valid and hash_err:
            return Err(hash_err)

        # 2. Verify DDC Candidate Runtime Laws
        laws_valid, violations = self._verify_ddc_laws()

        # 3. Calculate residual contraction
        initial_phi1, initial_gamma2, term_phi1, term_gamma2, init_tot, term_tot, delta, effect = (
            self._calculate_residuals()
        )

        # 4. Generate operadic morphisms
        self._compile_morphisms()

        tape_letters = ".".join(step.letter for step in self.steps)

        receipt = OperadCompositionReceipt(
            tape_path=self._tape_path_str,
            run_id=self._run_id,
            step_count=len(self.steps),
            tape_str=tape_letters,
            hash_chain_valid=hash_valid,
            ddc_laws_valid=laws_valid,
            law_violations=tuple(violations),
            initial_phi1=_format_fraction(initial_phi1),
            initial_gamma2=_format_fraction(initial_gamma2),
            terminal_phi1=_format_fraction(term_phi1),
            terminal_gamma2=_format_fraction(term_gamma2),
            initial_residual=_format_fraction(init_tot),
            terminal_residual=_format_fraction(term_tot),
            residual_delta=_format_fraction(delta),
            residual_effect=effect,
            morphism_count=len(self.morphisms),
            authority_effect="None",
        )

        return Ok(receipt)

    def register_in_operad(self, operad: ColouredOperad) -> dict[str, Any]:
        """Registers the parsed morphisms and partial compositions into a ColouredOperad registry."""
        for sort in (SORT_STATE, SORT_PROOF, SORT_RECEIPT, SORT_AUDIT, SORT_CONTRACT, SORT_LEDGER):
            operad.add_colour(sort)

        registered_ops: list[str] = []
        for morph in self.morphisms:
            op = operad.add_operation(
                op_id=morph.op_id,
                name=f"{morph.op_name}_{morph.step_index}",
                source_colours=list(morph.source_colors),
                target_colour=morph.target_color,
                equivariant=False,
                residual_effect=morph.residual_effect,
                impl=morph.colored_op.body,
            )
            registered_ops.append(op.id)

        # Attempt adjacent chain composition if target matches source slot 0
        compositions_registered = 0
        for i in range(len(self.morphisms) - 1):
            curr_op = self.morphisms[i]
            next_op = self.morphisms[i + 1]
            if next_op.source_colors and next_op.source_colors[0] == curr_op.target_color:
                comp_res = operad.add_composition(
                    outer=next_op.op_id,
                    slot=0,
                    inner=curr_op.op_id,
                    result=f"comp_{curr_op.op_id}_{next_op.op_id}",
                )
                if comp_res.is_ok:
                    compositions_registered += 1

        return {
            "operations_registered": len(registered_ops),
            "compositions_registered": compositions_registered,
            "operation_ids": registered_ops,
        }

    def export_evidence_receipt(self, dest: Path | str) -> Result[Path, Refusal]:
        """Persists the cryptographic OperadCompositionReceipt to a JSON destination."""
        parse_res = self.parse()
        if parse_res.is_err:
            return Err(parse_res.unwrap_err())
        receipt = parse_res.unwrap()
        target_path = Path(dest)
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(
                json.dumps(receipt.to_dict(), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            return Ok(target_path)
        except OSError as exc:
            return Err(
                Refusal(
                    code="EVIDENCE_EXPORT_ERROR",
                    message=f"Failed to export evidence receipt to {dest}: {exc}",
                    locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                )
            )

    def compress_to_operad_signature(
        self,
        skill_id: str = "degree-wise-dsl",
        skill_name: str = "Degree-Wise Obstruction Calculus Specification",
        source_colours: tuple[str, ...] = ("Contract", "State"),
        target_colour: str = "Receipt",
        description: str = "Degree-wise obstruction calculus cochain contract and degree-separation witness",
        operad_dir: Path | str | None = None,
        apply_changes: bool = True,
        claimed_residual_effect: str | None = None,
        expected_residual_effect: str | None = None,
        allow_downgrade: bool = True,
    ) -> Result[dict[str, Any], Refusal]:
        """Record the verified DDC bout trace and run operadic compression to update operad_signature.json."""
        parse_res = self.parse()
        if parse_res.is_err:
            return Err(parse_res.unwrap_err())
        receipt = parse_res.unwrap()

        # Check for false exactness claim or expectation mismatch
        effective_effect = claimed_residual_effect or receipt.residual_effect
        if claimed_residual_effect == "exact" and receipt.residual_effect != "exact":
            return Err(
                Refusal(
                    code="FALSE_EXACTNESS_CLAIM",
                    message=(
                        f"Refusing false exactness claim for '{skill_id}': measured terminal "
                        f"residual is {receipt.terminal_residual} != 0 (actual measured effect is '{receipt.residual_effect}'). "
                        "An exact residual_effect requires Delta_T = 0."
                    ),
                    locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                )
            )

        if expected_residual_effect is not None and expected_residual_effect != receipt.residual_effect:
            return Err(
                Refusal(
                    code="RESIDUAL_EFFECT_MISMATCH",
                    message=(
                        f"Refusing registration for '{skill_id}': expected residual_effect '{expected_residual_effect}' "
                        f"does not match measured '{receipt.residual_effect}'."
                    ),
                    locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                )
            )

        # Locate operad directory
        here = Path(__file__).resolve().parent
        if operad_dir is not None:
            target_operad_dir = Path(operad_dir)
        elif (here / "json" / "operad_signature.json").is_file():
            target_operad_dir = here
        else:
            repo_root = here.parent.parent
            target_operad_dir = repo_root / ".agents" / "operad"

        sig_path = (
            target_operad_dir / "json" / "operad_signature.json"
            if (target_operad_dir / "json" / "operad_signature.json").is_file()
            else target_operad_dir / "operad_signature.json"
        )
        if (target_operad_dir / "json").is_dir():
            trace_path = target_operad_dir / "json" / "evidence_trace.json"
        elif (target_operad_dir / "evidence_trace.json").is_file():
            trace_path = target_operad_dir / "evidence_trace.json"
        else:
            trace_path = target_operad_dir / "json" / "evidence_trace.json"

        if not sig_path.is_file():
            return Err(
                Refusal(
                    code="OPERAD_SIGNATURE_NOT_FOUND",
                    message=f"operad_signature.json not found at {sig_path}",
                    locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                )
            )

        # 1. Update evidence_trace.json
        phi_before_val = (
            float(Fraction(receipt.initial_residual))
            if receipt.initial_residual is not None
            else 0.0
        )
        phi_after_val = (
            float(Fraction(receipt.terminal_residual))
            if receipt.terminal_residual is not None
            else 0.0
        )

        traces: list[dict[str, Any]] = []
        if trace_path.is_file():
            try:
                traces = json.loads(trace_path.read_text(encoding="utf-8"))
            except Exception:
                traces = []

        existing_match = any(
            t.get("run_id") == receipt.run_id and t.get("skill_id") == skill_id
            for t in traces
        )
        if not existing_match:
            traces.append({
                "skill_id": skill_id,
                "run_id": receipt.run_id,
                "phi_before": phi_before_val,
                "phi_after": phi_after_val,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            if apply_changes:
                trace_path.parent.mkdir(parents=True, exist_ok=True)
                trace_path.write_text(json.dumps(traces, indent=2) + "\n", encoding="utf-8")

        # 2. Ensure skill_id is declared in operad_signature.json
        sig = json.loads(sig_path.read_text(encoding="utf-8"))
        operations = sig.get("operations", [])
        found_op = next((op for op in operations if op.get("skill_id") == skill_id), None)

        if found_op is None:
            new_op = {
                "skill_id": skill_id,
                "name": skill_name,
                "arity": len(source_colours),
                "source_colours": list(source_colours),
                "target_colour": target_colour,
                "residual_effect": effective_effect,
                "description": description,
            }
            operations.append(new_op)
            sig["operations"] = operations
            if apply_changes:
                sig_path.write_text(json.dumps(sig, indent=2) + "\n", encoding="utf-8")
        else:
            if (
                found_op.get("residual_effect") == "exact"
                and effective_effect != "exact"
                and not allow_downgrade
            ):
                return Err(
                    Refusal(
                        code="FALSE_EXACTNESS_CLAIM",
                        message=(
                            f"Refusing false exactness claim for existing operation '{skill_id}': signature claims 'exact', "
                            f"but measured terminal residual is {receipt.terminal_residual} != 0 (actual effect: '{effective_effect}')."
                        ),
                        locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                    )
                )
            if found_op.get("residual_effect") != effective_effect:
                found_op["residual_effect"] = effective_effect
                if apply_changes:
                    sig_path.write_text(json.dumps(sig, indent=2) + "\n", encoding="utf-8")

        # 3. Run operadic compression
        if str(target_operad_dir) not in sys.path:
            sys.path.insert(0, str(target_operad_dir))
        try:
            from .execute_operadic_compression import run_compression
        except (ImportError, ValueError):
            from execute_operadic_compression import run_compression  # type: ignore[no-redef]

        report = run_compression(
            apply_changes=apply_changes,
            operad_dir=target_operad_dir,
        )

        return Ok({
            "receipt": receipt.to_dict(),
            "skill_id": skill_id,
            "residual_effect": receipt.residual_effect,
            "compression_report": report,
            "signature_path": str(sig_path),
        })

    # -------------------------------------------------------------------------
    # Internal Loaders & Checkers
    # -------------------------------------------------------------------------

    def _load_records(self) -> tuple[list[dict[str, Any]], Refusal | None]:
        if isinstance(self.source, (list, tuple)):
            self._tape_path_str = "<memory_sequence>"
            return [dict(item) for item in self.source], None

        if isinstance(self.source, str) and ("\n" in self.source.strip() or ("{" in self.source and not Path(self.source).exists())):
            self._tape_path_str = "<string_buffer>"
            records = []
            for line_no, line in enumerate(self.source.splitlines(), start=1):
                clean = line.strip()
                if not clean:
                    continue
                try:
                    record = json.loads(clean)
                except Exception as exc:
                    return [], Refusal(
                        code="INVALID_TAPE_LINE",
                        message=f"Line {line_no} is not a valid JSON object: {exc}",
                        locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                    )
                if not isinstance(record, dict):
                    return [], Refusal(
                        code="INVALID_TAPE_LINE",
                        message=f"Line {line_no} is not a valid JSON object",
                        locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                    )
                records.append(record)
            return records, None

        path = Path(self.source)
        if path.is_dir():
            candidates = [path / "ddc.jsonl", path / "dda_actions.jsonl"]
            found = next((c for c in candidates if c.is_file()), None)
            if not found:
                return [], Refusal(
                    code="TAPE_NOT_FOUND",
                    message=f"No ddc.jsonl or dda_actions.jsonl found in directory: {path}",
                    locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                )
            path = found

        self._tape_path_str = str(path)
        self._run_id = path.parent.name if path.parent.name else "run"

        if not path.is_file():
            return [], Refusal(
                code="TAPE_FILE_NOT_FOUND",
                message=f"DDC tape file does not exist: {path}",
                locus="omega_engine_operads.skill_operad.ddc_operad_parser",
            )

        try:
            records: list[dict[str, Any]] = []
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                clean = line.strip()
                if not clean:
                    continue
                record = json.loads(clean)
                if not isinstance(record, dict):
                    return [], Refusal(
                        code="INVALID_TAPE_LINE",
                        message=f"Line {line_no} is not a valid JSON object",
                        locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                    )
                records.append(record)
            return records, None
        except Exception as exc:
            return [], Refusal(
                code="TAPE_READ_ERROR",
                message=f"Failed to read DDC tape: {exc}",
                locus="omega_engine_operads.skill_operad.ddc_operad_parser",
            )

    def _parse_and_validate_hash_chain(
        self, records: list[dict[str, Any]]
    ) -> tuple[bool, Refusal | None]:
        self.steps = []
        expected_parent: str | None = None

        for seq, rec in enumerate(records):
            record_seq = rec.get("sequence", seq)
            parent_sha256 = rec.get("parent_sha256")
            record_sha256 = rec.get("record_sha256")
            payload = rec.get("payload", {})
            if not isinstance(payload, dict):
                return False, Refusal(
                    code="MALFORMED_PAYLOAD",
                    message=f"Step {seq} payload is not a record",
                    locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                )

            # Sequence continuity
            if record_seq != seq:
                return False, Refusal(
                    code="SEQUENCE_MISMATCH",
                    message=f"Step {seq} declared sequence={record_seq}",
                    locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                )

            # Parent hash continuity
            if parent_sha256 != expected_parent:
                return False, Refusal(
                    code="HASH_CHAIN_BROKEN",
                    message=f"Step {seq} parent_sha256={parent_sha256!r} does not match expected {expected_parent!r}",
                    locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                )

            # Verify cryptographic digest of material
            sorted_payload = {
                k: payload[k] for k in sorted(payload.keys(), key=lambda key: key.encode("utf-8"))
            }
            material = json.dumps(
                {"sequence": seq, "parent_sha256": expected_parent, "payload": sorted_payload},
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            computed_sha = hashlib.sha256(material).hexdigest()

            if record_sha256 is not None and record_sha256 != computed_sha:
                return False, Refusal(
                    code="RECORD_DIGEST_MISMATCH",
                    message=f"Step {seq} record_sha256={record_sha256} != computed {computed_sha}",
                    locus="omega_engine_operads.skill_operad.ddc_operad_parser",
                )

            raw_letter = str(payload.get("letter", "")).strip()
            norm_letter = _normalize_letter(raw_letter)

            step = DdcParsedStep(
                sequence=seq,
                letter=norm_letter,
                parent_sha256=parent_sha256,
                record_sha256=computed_sha,
                before_class=str(payload.get("before_class", "")),
                after_class=str(payload.get("after_class", "")),
                carrier_hash=str(payload.get("carrier_hash", "")),
                witness_hash=payload.get("witness_hash"),
                receipt_sha256=payload.get("receipt_sha256"),
                phi_1=_canonical_fraction(payload.get("phi_1")),
                gamma_2=_canonical_fraction(payload.get("gamma_2")),
                payload=payload,
            )
            self.steps.append(step)
            expected_parent = computed_sha

        return True, None

    def _verify_ddc_laws(self) -> tuple[bool, list[str]]:
        violations: list[str] = []
        control_state = "OPEN"

        for idx, step in enumerate(self.steps):
            # Check Alphabet
            if step.letter not in DDC_CANONICAL_LETTERS:
                violations.append(f"Step {idx}: Unknown letter '{step.letter}' not in A_DDC")

            # Law 2: Terminal Absorption
            if control_state == "TERMINALIZED":
                violations.append(
                    f"Step {idx}: TerminalAbsorbing violation — step executed after T"
                )

            # Law 3: Refusal Absorption
            if control_state == "REFUSED" and step.letter not in ("C", "Λ", "T"):
                violations.append(
                    f"Step {idx}: RefusalAbsorbing violation — letter '{step.letter}' executed in REFUSED without C/Λ"
                )

            # Update control state
            if step.letter == "T":
                control_state = "TERMINALIZED"
            elif step.letter == "M":
                control_state = "REFUSED"
            elif step.letter in ("C", "Λ") and control_state == "REFUSED":
                control_state = "OPEN"

            # Law 7: Exact Repair Monotonicity
            if step.letter == "E":
                if idx > 0:
                    prev_step = self.steps[idx - 1]
                    if (
                        prev_step.phi_1 is not None
                        and step.phi_1 is not None
                        and step.phi_1 > prev_step.phi_1
                    ):
                        violations.append(
                            f"Step {idx}: ExactRepairIncreasedPhi1 ({prev_step.phi_1} -> {step.phi_1})"
                        )
                    if (
                        prev_step.gamma_2 is not None
                        and step.gamma_2 is not None
                        and step.gamma_2 > prev_step.gamma_2
                    ):
                        violations.append(
                            f"Step {idx}: ExactRepairIncreasedGamma2 ({prev_step.gamma_2} -> {step.gamma_2})"
                        )

            # Law 8: Context Exposure is not repair
            if step.letter == "C" and idx > 0:
                prev_step = self.steps[idx - 1]
                if (
                    prev_step.carrier_hash == step.carrier_hash
                    and prev_step.total_residual is not None
                    and step.total_residual is not None
                    and step.total_residual < prev_step.total_residual
                ):
                    violations.append(
                        f"Step {idx}: ContextExposureLoweredObstruction on unchanged carrier"
                    )

        return (len(violations) == 0, violations)

    def _calculate_residuals(
        self,
    ) -> tuple[
        Fraction | None,
        Fraction | None,
        Fraction | None,
        Fraction | None,
        Fraction | None,
        Fraction | None,
        Fraction | None,
        str,
    ]:
        first_phi: Fraction | None = None
        first_gamma: Fraction | None = None
        last_phi: Fraction | None = None
        last_gamma: Fraction | None = None

        for step in self.steps:
            if first_phi is None and step.phi_1 is not None:
                first_phi = step.phi_1
            if first_gamma is None and step.gamma_2 is not None:
                first_gamma = step.gamma_2
            if step.phi_1 is not None:
                last_phi = step.phi_1
            if step.gamma_2 is not None:
                last_gamma = step.gamma_2

        init_tot: Fraction | None = None
        if first_phi is not None or first_gamma is not None:
            init_tot = (first_phi or Fraction(0)) + (first_gamma or Fraction(0))

        term_tot: Fraction | None = None
        if last_phi is not None or last_gamma is not None:
            term_tot = (last_phi or Fraction(0)) + (last_gamma or Fraction(0))

        delta: Fraction | None = None
        if init_tot is not None and term_tot is not None:
            delta = term_tot - init_tot

        effect = "unknown"
        if init_tot is not None and term_tot is not None:
            if term_tot == 0:
                effect = "exact"
            elif term_tot < init_tot:
                effect = "residual_contractive"
            elif term_tot >= init_tot and term_tot > 0:
                effect = "residual_non_contractive"
            else:
                effect = "unknown"

        return (
            first_phi,
            first_gamma,
            last_phi,
            last_gamma,
            init_tot,
            term_tot,
            delta,
            effect,
        )

    def _compile_morphisms(self) -> None:
        self.morphisms = []
        for idx, step in enumerate(self.steps):
            mapping = OPERAD_MAPPING_DEFAULTS.get(
                step.letter, ((SORT_STATE,), SORT_STATE, "unknown_op")
            )
            src_colors, tgt_color, base_name = mapping

            op_id = f"ddc_op_{step.letter.lower()}_{idx}"

            # Assess local step residual effect
            local_effect = "unknown"
            if step.letter == "E":
                local_effect = "contractive"
            elif step.letter == "T" and step.total_residual == 0:
                local_effect = "exact"

            # Synthesize lightweight executable body for the ColoredOp
            def _make_body(step_idx: int, rune: str):
                def body(*args: object) -> tuple[object, Residual]:
                    return (
                        {"step": step_idx, "rune": rune, "result": "applied"},
                        EMPTY,
                    )

                return body

            colored_op = ColoredOp(
                name=f"{base_name}_{idx}",
                source_colors=src_colors,
                target_color=tgt_color,
                residual=EMPTY,
                body=_make_body(idx, step.letter),
            )

            morph = DdcMorphismMapping(
                step_index=idx,
                letter=step.letter,
                source_colors=src_colors,
                target_color=tgt_color,
                op_name=base_name,
                op_id=op_id,
                residual_effect=local_effect,
                colored_op=colored_op,
            )
            self.morphisms.append(morph)


__all__ = [
    "DDC_CANONICAL_LETTERS",
    "DdcMorphismMapping",
    "DdcOperadParser",
    "DdcParsedStep",
    "OperadCompositionReceipt",
]
