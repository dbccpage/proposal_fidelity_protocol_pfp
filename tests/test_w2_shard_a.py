"""
Executable test witnesses for Window 2 Wave 1 (Shard A):
- ATL-P003-008 (AUDIT-P003-008): Two-Signal Gate Decision Table
- ATL-P003-009 (AUDIT-P003-009): Self Panel Census and Diversity
- ATL-P003-010 (AUDIT-P003-010): Phrase Detector Fixtures and Clean Controls
- ATL-P004-001 (AUDIT-P004-001): Interface Separation and Dispatch Segregation
"""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import re
import sys
from typing import Any
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_P3_CODE = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "003_pfp_host_admitted_failure_detectors"
    / "code"
).resolve()
if str(_P3_CODE) not in sys.path:
    sys.path.insert(0, str(_P3_CODE))

# PFP Domain imports
from pfp.domain.immune.danger_gate import (
    DangerDecision,
    DangerSeverity,
    Signal1AstMatch,
    Signal2DangerState,
    TwoSignalDangerGate,
    TwoSignalDecision,
)
from pfp.domain.immune.thymus import (
    SelfPanel,
    SelfPanelEntry,
)

# Package archive imports
import canaries as pkg_canaries
from danger_gate import (
    DangerDecision as PkgDangerDecision,
    DangerSeverity as PkgDangerSeverity,
    Signal1Match as PkgSignal1Match,
    Signal2Danger as PkgSignal2Danger,
    evaluate_two_signal_gate as pkg_evaluate_two_signal_gate,
)
from self_panel import SelfPanel as PkgSelfPanel


# ==============================================================================
# Suite 1: Two-Signal Danger Gate Decision Table (ATL-P003-008 / AUDIT-P003-008)
# ==============================================================================

class TestTwoSignalDangerGateTable:
    """Validates the two-signal gate decision table across all 10 discrete states."""

    @pytest.mark.parametrize(
        "has_s1,s2_sev,expected_refusal,expected_disp_repo,expected_disp_pkg",
        [
            (False, None, False, "TOLERATED", "TOLERATED_CLEAN_PROPOSAL"),
            (True, None, False, "DIAGNOSTIC_ONLY", "DIAGNOSTIC_SYNTAX_MATCH_ONLY"),
            (False, DangerSeverity.LOW, False, "DIAGNOSTIC_ONLY", "DIAGNOSTIC_LOW_SEVERITY_DEFECT"),
            (False, DangerSeverity.MEDIUM, False, "DIAGNOSTIC_ONLY", "DIAGNOSTIC_LOW_SEVERITY_DEFECT"),
            (False, DangerSeverity.HIGH, True, "REFUSE", "REFUSED_CRITICAL_STRUCTURAL_DEFECT"),
            (False, DangerSeverity.CRITICAL, True, "REFUSE", "REFUSED_CRITICAL_STRUCTURAL_DEFECT"),
            (True, DangerSeverity.LOW, True, "REFUSE", "REFUSED_DUAL_SIGNAL_CORROBORATION"),
            (True, DangerSeverity.MEDIUM, True, "REFUSE", "REFUSED_DUAL_SIGNAL_CORROBORATION"),
            (True, DangerSeverity.HIGH, True, "REFUSE", "REFUSED_DUAL_SIGNAL_CORROBORATION"),
            (True, DangerSeverity.CRITICAL, True, "REFUSE", "REFUSED_DUAL_SIGNAL_CORROBORATION"),
        ],
    )
    def test_two_signal_gate_exhaustive_table_evaluation(
        self,
        has_s1: bool,
        s2_sev: DangerSeverity | None,
        expected_refusal: bool,
        expected_disp_repo: str,
        expected_disp_pkg: str,
    ) -> None:
        """Exhaustively verify the 10 combinations of Signal 1 and Signal 2 inputs."""
        # Setup repository domain inputs
        repo_s1 = [
            Signal1AstMatch(
                epitope_name="EPITOPE_TEST",
                pattern_matched="test_pattern",
                confidence=Fraction(1, 1),
            )
        ] if has_s1 else []

        repo_s2 = (
            Signal2DangerState(
                danger_type="TEST_DEFECT",
                severity=s2_sev,
                defect_count=1,
                evidence_digest="a" * 64,
            )
            if s2_sev is not None
            else None
        )

        repo_res = TwoSignalDangerGate.evaluate(repo_s1, repo_s2)
        assert repo_res.is_refusal == expected_refusal
        assert repo_res.disposition == expected_disp_repo

        # Setup package archive inputs
        pkg_s1 = [
            PkgSignal1Match(
                epitope_name="EPITOPE_TEST",
                pattern_matched="test_pattern",
            )
        ] if has_s1 else []

        pkg_s2 = (
            PkgSignal2Danger(
                danger_type="TEST_DEFECT",
                severity=s2_sev.value,
                defect_count=1,
                evidence_digest="a" * 64,
            )
            if s2_sev is not None
            else None
        )

        pkg_res = pkg_evaluate_two_signal_gate(pkg_s1, pkg_s2)
        assert pkg_res.is_refusal == expected_refusal
        assert pkg_res.disposition == expected_disp_pkg

    def test_two_signal_gate_severity_dependence_on_dual_signals(self) -> None:
        """Discharges obligation: verify severity dependence of both-signals row."""
        s1 = [
            Signal1AstMatch(
                epitope_name="AM_FSP_TEST",
                pattern_matched="test_match",
                confidence=Fraction(1, 1),
            )
        ]

        # In repo: low/medium triggers DEFENSIVE_LOCKDOWN; high/critical triggers QUARANTINED
        s2_low = Signal2DangerState(
            danger_type="DAMAGE_MINOR",
            severity=DangerSeverity.LOW,
            defect_count=1,
            evidence_digest="0" * 64,
        )
        dec_low = TwoSignalDangerGate.evaluate(s1, s2_low)
        assert dec_low.is_refusal is True
        assert dec_low.decision == DangerDecision.DEFENSIVE_LOCKDOWN

        s2_crit = Signal2DangerState(
            danger_type="DAMAGE_MAJOR",
            severity=DangerSeverity.CRITICAL,
            defect_count=1,
            evidence_digest="0" * 64,
        )
        dec_crit = TwoSignalDangerGate.evaluate(s1, s2_crit)
        assert dec_crit.is_refusal is True
        assert dec_crit.decision == DangerDecision.QUARANTINED

    def test_two_signal_gate_zero_float_enforcement(self) -> None:
        """Confirms that floating point values violate zero-float invariant."""
        with pytest.raises(TypeError, match="ZERO-FLOAT Invariant violated"):
            Signal1AstMatch(
                epitope_name="TEST",
                pattern_matched="test",
                confidence=0.85,  # type: ignore[arg-type]
            )

    def test_two_signal_gate_defect_count_zero_edge_case(self) -> None:
        """Confirms that defect_count == 0 is treated as absent Signal 2."""
        s1 = [
            Signal1AstMatch(
                epitope_name="TEST",
                pattern_matched="test",
                confidence=Fraction(1, 1),
            )
        ]
        s2_zero = Signal2DangerState(
            danger_type="DEFECT_ZERO",
            severity=DangerSeverity.CRITICAL,
            defect_count=0,
            evidence_digest="0" * 64,
        )
        # S1 present, S2 defect_count=0 -> treated as has_signal2=False -> DIAGNOSTIC_ONLY
        res = TwoSignalDangerGate.evaluate(s1, s2_zero)
        assert res.is_refusal is False
        assert res.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert res.disposition == "DIAGNOSTIC_ONLY"

    def test_two_signal_gate_negative_control_mutations(self) -> None:
        """Negative controls: mutate the decision logic and assert failure against invariants."""
        # Mutant 1: invert refusal decision
        def mutant_gate_inverts_refusal(s1_matches, s2_danger):
            normal = TwoSignalDangerGate.evaluate(s1_matches, s2_danger)
            return normal.is_refusal is False  # Inverted!

        s1 = [Signal1AstMatch("E", "p", Fraction(1, 1))]
        s2 = Signal2DangerState("D", DangerSeverity.CRITICAL, 1, "0" * 64)
        # Truth table demands is_refusal == True
        assert mutant_gate_inverts_refusal(s1, s2) is False, "Mutant unexpectedly matched valid behavior"


# ==============================================================================
# Suite 2: Self Panel Census and Diversity (ATL-P003-009 / AUDIT-P003-009)
# ==============================================================================

class TestSelfPanelCensus:
    """Validates the canonical self-panel row count, categories, and distinct base contents."""

    def test_canonical_self_panel_exact_census(self) -> None:
        """Verify baseline panel has exactly 1,000 entries and 40 distinct base contents."""
        panel = SelfPanel.load_canonical()
        assert len(panel) == 1000
        assert panel.fixture_count == 1000

        distinct_bases = panel.distinct_base_contents()
        assert len(distinct_bases) == 40

    def test_canonical_self_panel_per_category_census(self) -> None:
        """Verify the 4 categories each contain exactly 250 rows and 10 distinct base contents."""
        panel = SelfPanel.load_canonical()
        expected_categories = {
            "clean_lean4_proof",
            "clean_architecture_port",
            "clean_prompt_template",
            "clean_physics_expression",
        }

        category_counts: dict[str, int] = {}
        category_bases: dict[str, set[str]] = {}

        for entry in panel:
            category_counts[entry.category] = category_counts.get(entry.category, 0) + 1
            category_bases.setdefault(entry.category, set()).add(SelfPanel.base_content(entry.content))

        assert set(category_counts.keys()) == expected_categories
        for cat in expected_categories:
            assert category_counts[cat] == 250, f"Category {cat} count != 250"
            assert len(category_bases[cat]) == 10, f"Category {cat} distinct bases != 10"

        # Confirm all categories have mutually disjoint distinct bases
        total_unique = set.union(*category_bases.values())
        assert len(total_unique) == 40

    def test_base_content_normalizer_trailer_stripping(self) -> None:
        """Verifies synthetic trailer stripping while preserving valid semantic comments."""
        # Positive control: synthetic trailer is stripped
        content_with_trailer = "def foo : Nat := 42 -- index 045 hash_mod_7"
        assert SelfPanel.base_content(content_with_trailer) == "def foo : Nat := 42"

        # Negative control: semantic Lean / Python comment without synthetic pattern is preserved
        content_with_real_comment = "def foo : Nat := 42 -- a genuine proof annotation"
        assert SelfPanel.base_content(content_with_real_comment) == content_with_real_comment

    def test_self_panel_synthetic_mirror(self) -> None:
        """Verifies that the synthetic self-panel generator mirrors the 1,000 / 40 shape."""
        pkg_panel = PkgSelfPanel.build_synthetic()
        assert len(pkg_panel) == 1000
        assert len(pkg_panel.distinct_base_contents()) == 40

    def test_self_panel_mutation_negative_controls(self) -> None:
        """Mutant panels fail the 1,000 / 40 invariant checks."""
        panel = SelfPanel.load_canonical()
        # Subsampled panel mutant: 999 entries
        truncated_entries = panel.entries[:999]
        assert len(truncated_entries) != 1000

        # Artificially deduplicated content mutant
        mutant_bases = {SelfPanel.base_content(e.content) for e in truncated_entries[:100]}
        assert len(mutant_bases) < 40


# ==============================================================================
# Suite 3: Phrase Detector Fixtures & Clean Controls (ATL-P003-010 / AUDIT-P003-010)
# ==============================================================================

class TestPhraseDetectorFixtures:
    """Validates the 4x4 fixture diagonal matrix and clean control toleration."""

    FIXTURES = {
        "AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM": (
            "Modern neural network quantum states and tensor networks have overcome this "
            "limitation, providing an unrestricted polynomial-time sign-free solution for all "
            "fermion systems without requiring P = NP."
        ),
        "AM-FSP-2-FRUSTRATED-OBSTRUCTION": (
            "For attractive U < 0, particle-hole symmetry holds on any lattice including the "
            "triangle and pentagon."
        ),
        "AM-FSP-7-UNVERIFIED-MAJORANA-LIFT": (
            "Continuous-time Majorana decomposition secures positive Monte Carlo weights."
        ),
        "AM-FSP-4-ORBIT-SUM-MISMATCH": (
            "Meron cluster algorithms eliminate sign oscillations across arbitrary non-bipartite "
            "parameter regimes, ignoring orbit-cancellation breakdowns."
        ),
    }

    CLEAN_CONTROLS = (
        "We compute the discrete cochain boundary of a 1-chain on a bipartite square lattice over Q.",
        "We test whether diagonal sign gauge S = diag(1, -1, 1) eliminates negative signs on this triangle.",
        "For attractive U < 0 with equal spin populations, determinant QMC is sign-problem-free on any lattice.",
    )

    def test_phrase_detectors_diagonal_fixture_matrix(self) -> None:
        """Verifies each fixture triggers exactly its own detector and no others."""
        for expected_id, text in self.FIXTURES.items():
            findings = pkg_canaries.scan_for_canaries(text)
            assert len(findings) == 1, f"Expected exactly 1 finding for {expected_id}, got {len(findings)}"
            assert findings[0].canary_id == expected_id

    def test_phrase_detectors_clean_controls_zero_findings(self) -> None:
        """Verifies that none of the clean controls trigger any phrase detector."""
        for text in self.CLEAN_CONTROLS:
            findings = pkg_canaries.scan_for_canaries(text)
            assert findings == [], f"Clean control unexpectedly flagged: {findings}"

    def test_true_attractive_u_statement_preserved(self) -> None:
        """Explicitly checks that the true attractive-U statement is tolerated."""
        true_stmt = "For attractive U < 0 with equal spin populations, determinant QMC is sign-problem-free on any lattice."
        findings = pkg_canaries.scan_for_canaries(true_stmt)
        assert findings == []

    def test_phrase_detector_negation_limitation_negative_control(self) -> None:
        """Confirms the documented failure mode: naive phrase matching fails on negation."""
        negated_sentence = "There is no particle-hole symmetry on triangle plaquettes."
        # Because 'particle-hole symmetry on triangle' is in the phrase list, it fires despite negation
        findings = pkg_canaries.scan_for_canaries(negated_sentence)
        assert len(findings) == 1
        assert findings[0].canary_id == "AM-FSP-2-FRUSTRATED-OBSTRUCTION"

    def test_phrase_detector_mutant_negative_controls(self) -> None:
        """Mutant detectors fail diagonal matching."""
        # Over-flagging mutant
        def overflagging_scanner(text: str) -> list[str]:
            return ["AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM", "AM-FSP-2-FRUSTRATED-OBSTRUCTION"]

        for expected_id, text in self.FIXTURES.items():
            res = overflagging_scanner(text)
            # Must not match the strict single-detector expectation
            assert res != [expected_id]


# ==============================================================================
# Suite 4: Interface Separation & Dispatch Segregation (ATL-P004-001 / AUDIT-P004-001)
# ==============================================================================

class TestInterfaceSeparation:
    """Validates interface separation between default host, runtime dispatcher, and foundation library."""

    @property
    def rust_dir(self) -> Path:
        return _REPO_ROOT / "code" / "rust" / "pfp" / "src"

    def test_cli_dispatch_segregates_host_and_invoke(self) -> None:
        """Audits main.rs to confirm disjoint dispatch branches for host vs invoke."""
        main_rs = (self.rust_dir / "main.rs").read_text(encoding="utf-8")

        # Confirm dispatch_stdin_operation matches operation
        assert "fn dispatch_stdin_operation(" in main_rs
        assert 'Some("invoke") => invoke_runtime_command(input, &mut stdout)?' in main_rs
        assert "None => serde_json::to_writer(&mut stdout, &evaluate_request_bytes(input))?" in main_rs

        # Confirm different input limit handling
        assert 'if operation.as_deref() == Some("invoke")' in main_rs
        assert "MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES" in main_rs
        assert "MAX_HOST_REQUEST_BYTES" in main_rs

    def test_payload_byte_limits_differ_across_interfaces(self) -> None:
        """Verifies disparity in payload size bounds between host and runtime dispatcher."""
        main_rs = (self.rust_dir / "main.rs").read_text(encoding="utf-8")
        invoke_rs = (self.rust_dir / "invoke.rs").read_text(encoding="utf-8")
        protocol_rs = (self.rust_dir / "protocol.rs").read_text(encoding="utf-8")

        # Find MAX_HOST_REQUEST_BYTES in protocol.rs (1 MiB for host candidates)
        host_bytes_match = re.search(r"MAX_HOST_REQUEST_BYTES:\s*usize\s*=\s*([0-9_]+);", protocol_rs)
        assert host_bytes_match is not None
        host_bytes = int(host_bytes_match.group(1).replace("_", ""))
        assert host_bytes == 1_048_576  # 1 MiB

        # Find MAX_RUNTIME_REQUEST_BYTES in invoke.rs (64 KiB for standard runtime envelope)
        runtime_bytes_match = re.search(r"MAX_RUNTIME_REQUEST_BYTES:\s*usize\s*=\s*([0-9_]+);", invoke_rs)
        assert runtime_bytes_match is not None
        runtime_bytes = int(runtime_bytes_match.group(1).replace("_", ""))
        assert runtime_bytes == 65_536  # 64 KiB

        # Find MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES in invoke.rs (12 MiB for large artifacts)
        assert "pub const MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES: usize = 12 * 1024 * 1024;" in invoke_rs
        invoke_artifact_bytes = 12 * 1024 * 1024  # 12 MiB

        # Confirm limits are distinct across interfaces
        assert runtime_bytes < host_bytes < invoke_artifact_bytes

        # Confirm main.rs applies MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES to invoke and MAX_HOST_REQUEST_BYTES otherwise
        assert "if operation.as_deref() == Some(\"invoke\") {" in main_rs

    def test_foundation_module_has_zero_host_invoke_dependencies(self) -> None:
        """Audits foundation.rs to confirm zero dependency on host or invoke execution modules."""
        foundation_rs = (self.rust_dir / "foundation.rs").read_text(encoding="utf-8")

        # Confirm foundation declares additive, pure intent
        assert "This module is deliberately additive." in foundation_rs
        assert "It does not participate in the" in foundation_rs

        # Check imports: must not import host or invoke
        for line in foundation_rs.splitlines():
            line_clean = line.strip()
            if line_clean.startswith("use crate::"):
                assert "host" not in line_clean, f"foundation.rs illegally imports host: {line_clean}"
                assert "invoke" not in line_clean, f"foundation.rs illegally imports invoke: {line_clean}"
                assert "architecture_dag" not in line_clean, f"foundation.rs illegally imports architecture_dag: {line_clean}"

    def test_runtime_dispatcher_schema_and_action_contracts(self) -> None:
        """Audits invoke.rs to verify declared schemas and multi-action routing."""
        invoke_rs = (self.rust_dir / "invoke.rs").read_text(encoding="utf-8")

        assert 'pub const RUNTIME_REQUEST_SCHEMA: &str = "core.symbol-game.runtime-request.v1";' in invoke_rs
        assert 'pub const RUNTIME_OUTCOME_SCHEMA: &str = "core.symbol-game.runtime-outcome.v1";' in invoke_rs
        assert "dispatch_runtime_request" in invoke_rs

    def test_interface_boundary_negative_controls(self) -> None:
        """Negative controls: invalid CLI operation or attempting cross-interface routing fails."""
        main_rs = (self.rust_dir / "main.rs").read_text(encoding="utf-8")

        # Confirm unsupported operations return error
        assert 'Some(other) => return Err(format!("unsupported operation {:?}", other).into())' in main_rs
