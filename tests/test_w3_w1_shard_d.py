"""Executable test witnesses for Window 3 Wave 1 (Shard D - Paper 006):
- ATL-P006-006 (AUDIT-P006-006): Full-File Replacement via Temporary Path
- ATL-P006-007 (AUDIT-P006-007): RFC 8785 Scope and Float Rejection Fence
- ATL-P006-008 (AUDIT-P006-008): Caller-Supplied Refusal Evidence Custody
- ATL-P006-009 (AUDIT-P006-009): Detector Regex Refusal and Central Tolerance Kill Condition

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
import sys
from fractions import Fraction
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

if str(_REPO_ROOT / "ops") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "ops"))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ruff: noqa: E402
from pfp.domain.entities.cemetery_entry import TailReceipt
from pfp.domain.exceptions import (
    CanonicalizationError,
    LedgerIntegrityError,
)
from pfp.domain.immune.clonal_selection import (
    ClonalCandidate,
    ClonalSelectionEngine,
    KillConditionReceipt,
    KillConditionRefusal,
)
from pfp.domain.immune.thymus import SelfPanel
from pfp.infrastructure.persistence.cemetery_sink import (
    FLOAT_TAG,
    GENESIS_DIGEST,
    HEADER_SCHEMA,
    RECEIPT_SCHEMA,
    CemeterySink,
    _canonical_json_bytes,
    _refuse_floats,
    _sanitize_for_cemetery,
)

# ============================================================================
# 1. ATL-P006-006 / AUDIT-P006-006: Full-File Replacement via Temporary Path
# ============================================================================


class TestFullFileReplacementViaTemporaryPath:
    """Witnesses that CemeterySink._write_file writes to a temporary path

    and replaces the target file via os.replace.
    """

    def test_write_file_uses_temporary_path_and_replaces_target(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Observe that _write_file writes to file_path.with_suffix('.tmp') before os.replace."""
        ledger_path = tmp_path / "cemetery.jsonl"
        expected_tmp = ledger_path.with_suffix(".tmp")
        observed_calls: list[tuple[Path, Path, bytes]] = []

        real_replace = os.replace

        def tracking_replace(src: str | Path, dst: str | Path) -> None:
            s_path = Path(src)
            d_path = Path(dst)
            if s_path.name.endswith(".tmp"):
                content = s_path.read_bytes()
                observed_calls.append((s_path, d_path, content))
            real_replace(src, dst)

        monkeypatch.setattr(os, "replace", tracking_replace)

        sink = CemeterySink(ledger_path)
        assert len(observed_calls) == 1
        src_init, dst_init, init_bytes = observed_calls[0]
        assert src_init == expected_tmp
        assert dst_init == ledger_path
        assert b"HEADER" in init_bytes

        # Record a refusal and observe the replacement on update
        sink.record_refusal(
            turn_envelope={"turn_id": "TURN-001", "session": "s1"},
            refusal_reason="COCHAIN_DEFECT_OBSERVED",
            prompt_parameters={"tau": 3},
            cochain_projection={"c0": "1/2"},
        )

        assert len(observed_calls) == 2
        src_turn, dst_turn, turn_bytes = observed_calls[1]
        assert src_turn == expected_tmp
        assert dst_turn == ledger_path
        lines = turn_bytes.decode("utf-8").strip().split("\n")
        assert len(lines) == 2  # Line 0 Header + Line 1 Entry
        assert "COCHAIN_DEFECT_OBSERVED" in lines[1]

    def test_target_file_contains_consistent_header_and_entries(self, tmp_path: Path) -> None:
        """Verify target file maintains consistent line 0 count and head digest."""
        ledger_path = tmp_path / "ledger_check.jsonl"
        sink = CemeterySink(ledger_path)
        assert sink.tail_digest() == GENESIS_DIGEST

        for i in range(3):
            sink.record_refusal(
                turn_envelope={"turn_index": i},
                refusal_reason=f"REASON_{i}",
                prompt_parameters={"step": i + 1},
                cochain_projection={"residual": f"{i}/3"},
            )

        content = ledger_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(content) == 4  # 1 header + 3 entries

        header = json.loads(content[0])
        assert header["record_type"] == "HEADER"
        assert header["entry_count"] == 3
        assert header["head_digest"] == sink.tail_digest()
        assert header["schema"] == HEADER_SCHEMA

        # Receipt test verifying schema constant
        receipt = sink.emit_tail_receipt()
        assert isinstance(receipt, TailReceipt)
        assert receipt.schema == RECEIPT_SCHEMA
        assert receipt.entry_count == 3

    def test_temporary_path_does_not_linger_after_write(self, tmp_path: Path) -> None:
        """Verify no lingering .tmp file exists after normal write execution."""
        ledger_path = tmp_path / "clean_ledger.jsonl"
        sink = CemeterySink(ledger_path)
        tmp_file = ledger_path.with_suffix(".tmp")
        assert not tmp_file.exists()

        sink.record_refusal(
            turn_envelope={"turn": 1},
            refusal_reason="SAMPLE_REFUSAL",
        )
        assert not tmp_file.exists()
        assert ledger_path.exists()

    def test_write_failure_preserves_prior_target_state(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Simulate failure during os.replace to verify previous file is untouched."""
        ledger_path = tmp_path / "fault_test.jsonl"
        sink = CemeterySink(ledger_path)
        sink.record_refusal(
            turn_envelope={"step": 1},
            refusal_reason="INITIAL_COMMITTED_REFUSAL",
        )
        prior_content = ledger_path.read_bytes()

        def failing_replace(src: str | Path, dst: str | Path) -> None:
            raise OSError("Injected filesystem replacement failure")

        monkeypatch.setattr(os, "replace", failing_replace)

        with pytest.raises(OSError, match="Injected filesystem replacement failure"):
            sink.record_refusal(
                turn_envelope={"step": 2},
                refusal_reason="FAILING_TURN",
            )

        # Prior file remains intact on disk
        assert ledger_path.read_bytes() == prior_content

        # Reloading sink from disk recovers valid 1-entry state
        monkeypatch.undo()
        reloaded = CemeterySink(ledger_path)
        assert len(reloaded.get_entries()) == 1
        assert reloaded.get_entries()[0].refusal_reason == "INITIAL_COMMITTED_REFUSAL"

    def test_exact_integer_and_string_representation_without_floats(self, tmp_path: Path) -> None:
        """Verify that written file contains exact integer and string values without floats."""
        ledger_path = tmp_path / "exact_types.jsonl"
        sink = CemeterySink(ledger_path)
        sink.record_refusal(
            turn_envelope={"dim": 4},
            refusal_reason="EXACT_FRACTION_TEST",
            prompt_parameters={"p": 2},
            cochain_projection={"exact_ratio": Fraction(3, 7)},
        )

        raw_lines = ledger_path.read_text(encoding="utf-8").strip().split("\n")
        entry = json.loads(raw_lines[1])
        assert entry["cochain_projection"]["exact_ratio"] == "3/7"
        assert isinstance(entry["entry_index"], int)
        assert isinstance(entry["prompt_parameters"]["p"], int)

        # Verify no float numbers exist in JSON payload using json.loads float parser hook
        for line in raw_lines:
            json.loads(
                line,
                parse_float=lambda x: pytest.fail(f"Unexpected floating-point token in ledger line: {x}"),
            )


# ============================================================================
# 2. ATL-P006-007 / AUDIT-P006-007: RFC 8785 Scope and Float Rejection Fence
# ============================================================================


class TestRfc8785ScopeAndFloatRejection:
    """Witnesses that CemeterySink uses an internal profile rather than RFC 8785

    and rejects binary floats with CanonicalizationError.
    """

    def test_canonical_json_bytes_refuses_float_with_canonicalization_error(self) -> None:
        """_canonical_json_bytes raises CanonicalizationError when float is encountered."""
        with pytest.raises(CanonicalizationError, match="float .* is not admitted"):
            _canonical_json_bytes({"weight": 1.25})

        with pytest.raises(CanonicalizationError, match="float .* is not admitted"):
            _canonical_json_bytes([1, 2, [3, 4.0]])

        with pytest.raises(CanonicalizationError, match="float .* is not admitted"):
            _canonical_json_bytes({"nested": {"deep": {"value": 0.0}}})

        # Direct test on _refuse_floats
        with pytest.raises(CanonicalizationError, match="float .* is not admitted"):
            _refuse_floats(0.5)

    def test_canonical_json_bytes_refuses_nan_and_inf(self) -> None:
        """_canonical_json_bytes raises CanonicalizationError on float('nan') and inf."""
        with pytest.raises(CanonicalizationError, match="float .* is not admitted"):
            _canonical_json_bytes({"nan_val": float("nan")})

        with pytest.raises(CanonicalizationError, match="float .* is not admitted"):
            _canonical_json_bytes({"inf_val": float("inf")})

        with pytest.raises(CanonicalizationError, match="float .* is not admitted"):
            _canonical_json_bytes({"neg_inf": float("-inf")})

    def test_sanitize_for_cemetery_preserves_float_as_tagged_hex_dict(self) -> None:
        """_sanitize_for_cemetery converts floats to {'$float_hex': float.hex()}."""
        val = 2.5
        sanitized = _sanitize_for_cemetery(val)
        assert sanitized == {FLOAT_TAG: val.hex()}

        # Verify complex structure sanitization
        data = {"score": 0.125, "fractions": [Fraction(1, 3)], "int_val": 42}
        res = _sanitize_for_cemetery(data)
        assert res["score"] == {FLOAT_TAG: (0.125).hex()}
        assert res["fractions"] == ["1/3"]
        assert res["int_val"] == 42

    def test_compact_separators_and_key_sorting(self) -> None:
        """Verify sorted keys and absence of whitespace separators."""
        unordered = {"z": 1, "a": 2, "m": {"y": 10, "b": 20}}
        result_bytes = _canonical_json_bytes(unordered)
        assert result_bytes == b'{"a":2,"m":{"b":20,"y":10},"z":1}'
        assert b" " not in result_bytes

    def test_utf8_non_ascii_preservation_without_escaping(self) -> None:
        """Verify non-ASCII unicode text is serialized directly as UTF-8 without escape codes."""
        payload = {"omega": "\u03a9", "symbol": "alpha_\u03b1"}
        result_bytes = _canonical_json_bytes(payload)
        # Must not contain escaped sequences like \u03a9
        assert b"\\u" not in result_bytes
        decoded = result_bytes.decode("utf-8")
        assert "\u03a9" in decoded
        assert "alpha_\u03b1" in decoded


# ============================================================================
# 3. ATL-P006-008 / AUDIT-P006-008: Caller-Supplied Refusal Evidence Custody
# ============================================================================


class TestCallerSuppliedRefusalEvidenceCustody:
    """Witnesses that CemeterySink records caller-supplied cochain and refusal fields

    verbatim without evaluating domain validity or mathematical truth.
    """

    def test_record_refusal_stores_cochain_projection_verbatim(self, tmp_path: Path) -> None:
        """Cochain projection mappings are stored as supplied by the caller."""
        sink = CemeterySink(tmp_path / "custody.jsonl")
        cochain = {
            "c0_norm": "3/2",
            "d_omega": "-1/4",
            "boundary_verified": "false",
            "dimension": 5,
        }
        entry = sink.record_refusal(
            turn_envelope={"turn_num": 10},
            refusal_reason="CALLER_DECLARED_DEFECT",
            cochain_projection=cochain,
        )
        assert entry.cochain_projection == cochain
        assert entry.refusal_reason == "CALLER_DECLARED_DEFECT"

    def test_record_refusal_accepts_unverified_refusal_reason(self, tmp_path: Path) -> None:
        """Sink accepts arbitrary caller refusal string without evaluation."""
        sink = CemeterySink(tmp_path / "arbitrary.jsonl")
        arbitrary_reason = "UNCHECKED_REFUSAL_STRING_ASSERTING_CONTRADICTORY_COCHAIN"
        contradictory_cochain = {"d1_d0": "NOT_ZERO_CONTRADICTION"}

        entry = sink.record_refusal(
            turn_envelope={"caller": "test_agent"},
            refusal_reason=arbitrary_reason,
            cochain_projection=contradictory_cochain,
        )
        assert entry.refusal_reason == arbitrary_reason
        assert entry.cochain_projection == contradictory_cochain
        assert sink.verify_integrity() is True

    def test_record_refusal_binds_caller_fields_into_entry_digest(self, tmp_path: Path) -> None:
        """Different caller refusal reasons or projections yield distinct entry digests."""
        sink1 = CemeterySink(tmp_path / "sink1.jsonl")
        sink2 = CemeterySink(tmp_path / "sink2.jsonl")

        e1 = sink1.record_refusal(
            turn_envelope={"turn": 1},
            refusal_reason="REASON_A",
            cochain_projection={"c": "1"},
        )
        e2 = sink2.record_refusal(
            turn_envelope={"turn": 1},
            refusal_reason="REASON_B",
            cochain_projection={"c": "1"},
        )
        assert e1.entry_digest != e2.entry_digest

    def test_tampered_stored_cochain_fails_integrity_verification(self, tmp_path: Path) -> None:
        """Modifying a stored cochain field in the file triggers LedgerIntegrityError."""
        ledger_path = tmp_path / "tamper_test.jsonl"
        sink = CemeterySink(ledger_path)
        sink.record_refusal(
            turn_envelope={"turn": 1},
            refusal_reason="ORIGINAL_REASON",
            cochain_projection={"vector": "1/2"},
        )
        assert sink.verify_integrity() is True

        # Tamper with the cochain_projection in the written file
        lines = ledger_path.read_text(encoding="utf-8").strip().split("\n")
        entry_dict = json.loads(lines[1])
        entry_dict["cochain_projection"]["vector"] = "999/1"  # Alter coordinate
        lines[1] = json.dumps(entry_dict, sort_keys=True, separators=(",", ":"))
        ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Reopening the sink detects bit-flip / record tampering during cold-load verification
        with pytest.raises(LedgerIntegrityError, match="Bit-flip or record tampering detected"):
            CemeterySink(ledger_path)


# ============================================================================
# 4. ATL-P006-009 / AUDIT-P006-009: Detector Regex Refusal and Kill Condition
# ============================================================================


class TestDetectorRegexRefusalAndKillCondition:
    """Witnesses that ClonalSelectionEngine.check_kill_condition maps invalid regex

    patterns to KillConditionRefusal and self-panel matches to KillConditionReceipt.
    """

    @pytest.fixture
    def benign_self_panel(self) -> SelfPanel:
        """Construct a controlled SelfPanel with known baseline samples."""
        samples = [
            "AuthorityEffect: None",
            "exact rational duality gap is zero",
            "bounded finite complex with exact coboundary",
            "fractions.Fraction(1, 2) is exact",
            "clean architecture inward dependency verified",
        ]
        return SelfPanel.from_strings(samples)

    @pytest.fixture
    def parent_rule(self) -> ClonalCandidate:
        """Construct a valid active parent detector candidate."""
        return ClonalCandidate(
            rule_id="RULE-PARENT-001",
            target_epitope="UNRESTRICTED_SOLVER_CLAIM",
            match_pattern=r"unrestricted\s+polynomial\s+solution",
            generation=1,
            affinity_score=Fraction(1, 1),
            half_life_runs=10,
            runs_idle=0,
            is_active=True,
        )

    def test_invalid_regex_returns_typed_refusal_without_raising(
        self, parent_rule: ClonalCandidate, benign_self_panel: SelfPanel
    ) -> None:
        """An uncompilable regex pattern returns (False, KillConditionRefusal)."""
        invalid_clone = ClonalSelectionEngine.mutate_rule(
            parent=parent_rule,
            new_pattern=r"broken_pattern([a-z",  # Missing closing bracket
            clone_id="CLONE-INVALID-REGEX",
        )

        is_killed, result = ClonalSelectionEngine.check_kill_condition(
            clone=invalid_clone,
            parent=parent_rule,
            self_panel=benign_self_panel,
        )

        assert is_killed is False
        assert isinstance(result, KillConditionRefusal)
        assert result.code == "INVALID_MATCH_PATTERN"
        assert result.clone_id == "CLONE-INVALID-REGEX"
        assert result.parent_id == parent_rule.rule_id
        assert result.authority_effect == "None"
        assert "Invalid regular expression syntax" in result.reason

    def test_invalid_regex_does_not_purge_parent_lineage(
        self, parent_rule: ClonalCandidate, benign_self_panel: SelfPanel
    ) -> None:
        """Invalid pattern does not destroy parent lineage; parent remains active."""
        invalid_clone = ClonalSelectionEngine.mutate_rule(
            parent=parent_rule,
            new_pattern=r"*+unbounded_qualifier",  # Invalid regex syntax
            clone_id="CLONE-BAD-QUALIFIER",
        )

        is_killed, refusal = ClonalSelectionEngine.check_kill_condition(
            clone=invalid_clone,
            parent=parent_rule,
            self_panel=benign_self_panel,
        )
        assert is_killed is False
        assert isinstance(refusal, KillConditionRefusal)
        assert parent_rule.is_active is True
        assert parent_rule.affinity_score == Fraction(1, 1)

    def test_self_panel_match_emits_purged_receipt(
        self, parent_rule: ClonalCandidate, benign_self_panel: SelfPanel
    ) -> None:
        """A pattern matching the benign self-panel triggers parent-child kill condition."""
        # Mutate to match sample: 'exact rational duality gap is zero'
        self_reactive_clone = ClonalSelectionEngine.mutate_rule(
            parent=parent_rule,
            new_pattern=r"duality\s+gap\s+is\s+zero",
            clone_id="CLONE-SELF-REACTIVE",
        )

        is_killed, receipt = ClonalSelectionEngine.check_kill_condition(
            clone=self_reactive_clone,
            parent=parent_rule,
            self_panel=benign_self_panel,
        )

        assert is_killed is True
        assert isinstance(receipt, KillConditionReceipt)
        assert receipt.status == "PURGED_SELF_REACTIVE"
        assert receipt.clone_id == "CLONE-SELF-REACTIVE"
        assert receipt.parent_id == parent_rule.rule_id
        assert receipt.authority_effect == "None"
        assert len(receipt.canonical_hash) == 64
        assert receipt.violating_sample_id.startswith("SP-MOCK-")

    def test_clean_pattern_passes_without_kill_condition(
        self, parent_rule: ClonalCandidate, benign_self_panel: SelfPanel
    ) -> None:
        """A clean pattern matching external defects returns (False, None)."""
        clean_clone = ClonalSelectionEngine.mutate_rule(
            parent=parent_rule,
            new_pattern=r"hallucinated_sign_free_meron_solution",
            clone_id="CLONE-CLEAN-DEFECT",
        )

        is_killed, result = ClonalSelectionEngine.check_kill_condition(
            clone=clean_clone,
            parent=parent_rule,
            self_panel=benign_self_panel,
        )
        assert is_killed is False
        assert result is None

    def test_rust_native_thymus_gate_parity(self) -> None:
        """Verify parity alignment with Rust native ThymusGate source contract."""
        rust_source = (_REPO_ROOT / "code" / "rust" / "core_epistemic_immune_system" / "src" / "thymus.rs").read_text(
            encoding="utf-8"
        )
        # Check that InvalidPattern and SelfReactive are defined in Rust
        assert "InvalidPattern" in rust_source
        assert "SelfReactive" in rust_source
        assert "Survived" in rust_source
        assert "AuthorityEffect: None" in rust_source
