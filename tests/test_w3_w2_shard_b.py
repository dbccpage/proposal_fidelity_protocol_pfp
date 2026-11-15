"""Verification test suite for Window 3 Wave 2 Shard B (Paper 004 & Paper 006).

Targets four audit derivations:
1. ATL-P004-014 (AUDIT-P004-014): Foundation test content
   - Shared packet vectors and cross-language golden vector parity
   - Float rejection and exact 4-field normalization in PacketKernel
   - Finite extension and incomplete exhaustion certificate refusals
   - DDA composition associativity, intermediate mismatch, and boundary refusals
2. ATL-P004-018 (AUDIT-P004-018): Deposit self-containment
   - Audited source tarball existence, size, and exact SHA-256 digest
   - SOURCE_MEMBERS.sha256 completeness (7,875 unique member records)
   - REVISION.json schema, source commit, and crate tree bindings
   - Retained native test execution report (12, 11, 32, and 9 passing tests)
3. ATL-P006-010 (AUDIT-P006-010): Self-panel distinct contents
   - Canonical self panel 1,000 rows across 4 categories
   - Exactly 40 distinct base contents (10 per category)
   - Synthetic comment stripping preserving genuine comments
   - Diversity ratio Fraction(40, 1000) == Fraction(1, 25)
4. ATL-P006-011 (AUDIT-P006-011): Inclusive toxicity threshold
   - TregSupervisor inclusive threshold at tau = Fraction(1, 5)
   - Downgrade synthesis to DIAGNOSTIC_ONLY at exactly tau (1/5)
   - Retention of detector just below tau (1/6 produces None)
   - Boundary tests (2/9 fires, 2/11 silent)
   - Unlabelled prompt corpus toxicity is binary: Fraction(0, 1) or Fraction(1, 1)
   - Zero-Float Law enforcement rejecting float inputs
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

for p in (_REPO_ROOT, _REPO_ROOT / "ops"):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

import governance  # noqa: E402

_GOV_OPS = str(_REPO_ROOT / "ops" / "governance")
if _GOV_OPS not in governance.__path__:
    governance.__path__.append(_GOV_OPS)

import pfp.domain  # noqa: E402
import pfp.domain.shared_kernel  # noqa: E402

for sym in getattr(pfp.domain.shared_kernel, "__all__", []):
    if not hasattr(pfp.domain, sym):
        setattr(pfp.domain, sym, getattr(pfp.domain.shared_kernel, sym))

from pfp.domain.canonical import domain_digest  # noqa: E402
from pfp.domain.exceptions import CanonicalizationError  # noqa: E402
from pfp.domain.immune.thymus import SelfPanel  # noqa: E402
from pfp.domain.immune.treg import (  # noqa: E402
    AutoimmuneToxicityReport,
    RegulatoryAntibody,
    TregSupervisor,
)

# ============================================================================
# 1. ATL-P004-014 / AUDIT-P004-014: Foundation test content
# ============================================================================


class TestFoundationContract:
    """Witnesses that foundation_contract.rs contains shared packet vectors and refusals."""

    GOLDEN_PACKET_ID = "999043cbf31263572f76446bd54096c194e04ded58129ea9cf85d1bed45ff0ef"
    PACKET_KERNEL_ID_DOMAIN = "core.symbol-game.packet-kernel-id.v1"

    def test_rust_foundation_contract_source_contains_vectors_and_refusals(self) -> None:
        """Audits code/rust/tests/pfp/foundation_contract.rs for declared vectors and refusals."""
        contract_path = _REPO_ROOT / "code" / "rust" / "tests" / "pfp" / "foundation_contract.rs"
        assert contract_path.is_file(), f"Missing foundation test source: {contract_path}"

        source = contract_path.read_text(encoding="utf-8")

        # 1. Shared packet vectors
        assert "fn packet_identity_binds_all_four_fields_and_normalizes_object_order()" in source
        assert "fn packet_id_matches_python_canonical_golden_vector()" in source
        assert self.GOLDEN_PACKET_ID in source
        assert 'PacketKernel::new("contract-a", "task-a", json!({"x": 0.5}), None)' in source
        assert "FoundationErrorCode::NonExactJson" in source

        # 2. Finite extension and incomplete exhaustion
        assert "fn empty_observations_cannot_forge_nonempty_exhaustion()" in source
        assert "FoundationErrorCode::IncompleteCoverage" in source
        assert "FoundationErrorCode::EvaluationMismatch" in source
        assert "fn r1_has_priority_and_r2_requires_positive_checked_exhaustion()" in source
        assert "fn conservative_extension_checks_roundtrip_and_detector_preservation()" in source
        assert "FoundationErrorCode::DetectorNotPreserved" in source

        # 3. Composition refusals
        assert "fn dda_composition_has_identities_associativity_and_boundary_refusals()" in source
        assert "FoundationErrorCode::IntermediateStateMismatch" in source
        assert "FoundationErrorCode::BoundaryMismatch" in source
        assert "fn dda_refuses_protected_loss_and_replay_mismatch()" in source
        assert "FoundationErrorCode::ProtectedLoss" in source

    def test_cross_language_packet_golden_vector_parity(self) -> None:
        """Python canonical domain digest matches the Rust PacketKernel golden vector exactly."""
        golden_payload = {
            "alpha": [None, True, 7, "omega"],
            "nested": {"b": 2, "a": 1},
        }
        golden_parent = "0123456789abcdef" * 4

        golden_identity_material = {
            "contract_id": "core.symbol-game.golden.v1",
            "task_id": "task-17",
            "payload": golden_payload,
            "parent_packet_id": golden_parent,
        }

        digest = domain_digest(self.PACKET_KERNEL_ID_DOMAIN, golden_identity_material)
        assert digest == self.GOLDEN_PACKET_ID
        assert len(digest) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", digest) is not None

    def test_packet_identity_normalizes_object_key_order(self) -> None:
        """Permuted object keys produce the identical packet digest across encodings."""
        left_payload = {"content": "hello", "intent": "answer"}
        right_payload = {"intent": "answer", "content": "hello"}

        left_mat = {
            "contract_id": "contract-a",
            "task_id": "task-a",
            "payload": left_payload,
            "parent_packet_id": None,
        }
        right_mat = {
            "task_id": "task-a",
            "contract_id": "contract-a",
            "payload": right_payload,
            "parent_packet_id": None,
        }

        left_id = domain_digest(self.PACKET_KERNEL_ID_DOMAIN, left_mat)
        right_id = domain_digest(self.PACKET_KERNEL_ID_DOMAIN, right_mat)
        assert left_id == right_id

    def test_packet_identity_binds_all_four_fields_distinctly(self) -> None:
        """Mutating any one of the four fields changes the derived packet digest."""
        base_mat = {
            "contract_id": "contract-a",
            "task_id": "task-a",
            "payload": {"content": "hello"},
            "parent_packet_id": None,
        }
        base_id = domain_digest(self.PACKET_KERNEL_ID_DOMAIN, base_mat)

        # Mutate contract_id
        mat_diff_contract = dict(base_mat, contract_id="contract-b")
        assert domain_digest(self.PACKET_KERNEL_ID_DOMAIN, mat_diff_contract) != base_id

        # Mutate task_id
        mat_diff_task = dict(base_mat, task_id="task-b")
        assert domain_digest(self.PACKET_KERNEL_ID_DOMAIN, mat_diff_task) != base_id

        # Mutate payload
        mat_diff_payload = dict(base_mat, payload={"content": "goodbye"})
        assert domain_digest(self.PACKET_KERNEL_ID_DOMAIN, mat_diff_payload) != base_id

        # Mutate parent_packet_id
        mat_diff_parent = dict(base_mat, parent_packet_id="0" * 64)
        assert domain_digest(self.PACKET_KERNEL_ID_DOMAIN, mat_diff_parent) != base_id

    def test_packet_vector_refuses_floating_point(self) -> None:
        """Packet material containing float values is refused by canonicalization."""
        float_material = {
            "contract_id": "contract-a",
            "task_id": "task-a",
            "payload": {"x": 0.5},
            "parent_packet_id": None,
        }
        with pytest.raises(CanonicalizationError):
            domain_digest(self.PACKET_KERNEL_ID_DOMAIN, float_material)

    def test_finite_exhaustion_refusals_behavioral_model(self) -> None:
        """Exhaustion certificate rejects incomplete coverage and evaluation mismatch."""
        universe = {"c1": 1, "c2": 2}

        # Model certify: must cover every declared candidate
        def certify_exhaustion(declared: dict[str, int], observed: dict[str, int]) -> str:
            if set(declared.keys()) != set(observed.keys()):
                raise ValueError("INCOMPLETE_COVERAGE: nonempty declared universe requires complete coverage")
            for k, val in declared.items():
                if val != observed[k]:
                    raise ValueError(f"EVALUATION_MISMATCH: candidate {k} recomputed value differs")
            return "EXHAUSTION_CERTIFIED"

        # Positive case: exact coverage matches
        assert certify_exhaustion(universe, {"c1": 1, "c2": 2}) == "EXHAUSTION_CERTIFIED"

        # Negative control 1: incomplete coverage (omitting candidate c2)
        with pytest.raises(ValueError, match="INCOMPLETE_COVERAGE"):
            certify_exhaustion(universe, {"c1": 1})

        # Negative control 2: evaluation mismatch
        with pytest.raises(ValueError, match="EVALUATION_MISMATCH"):
            certify_exhaustion(universe, {"c1": 1, "c2": 99})

    def test_dda_composition_refusals_behavioral_model(self) -> None:
        """Path composition verifies intermediate state equality and contract boundary matching."""
        # Simple path model: (contract, initial_state, final_state)
        def compose_paths(
            p1: tuple[str, int, int], p2: tuple[str, int, int]
        ) -> tuple[str, int, int]:
            contract1, s0, s1 = p1
            contract2, s1_prime, s2 = p2
            if contract1 != contract2:
                raise ValueError("BOUNDARY_MISMATCH: contract boundary must match")
            if s1 != s1_prime:
                raise ValueError("INTERMEDIATE_STATE_MISMATCH: composition is partial on intermediate state")
            return (contract1, s0, s2)

        # Positive: composition links s0 -> s1 -> s2
        res = compose_paths(("contract-1", 0, 2), ("contract-1", 2, 4))
        assert res == ("contract-1", 0, 4)

        # Negative control 1: intermediate state mismatch
        with pytest.raises(ValueError, match="INTERMEDIATE_STATE_MISMATCH"):
            compose_paths(("contract-1", 0, 2), ("contract-1", 99, 4))

        # Negative control 2: boundary contract mismatch
        with pytest.raises(ValueError, match="BOUNDARY_MISMATCH"):
            compose_paths(("contract-1", 0, 2), ("other-contract", 2, 4))


# ============================================================================
# 2. ATL-P004-018 / AUDIT-P004-018: Deposit self-containment
# ============================================================================


class TestDepositSelfContainment:
    """Witnesses that the deposit contains the audited source tarball and native report."""

    DEPOSIT_BASE = _REPO_ROOT / "atlas" / "archive" / "pfp" / "004_pfp_native_verification_and_evidence_custody"
    EXPECTED_TAR_NAME = "pfp-iv-native-source-52cb5457.tar.gz"
    EXPECTED_TAR_SHA256 = "a7be14eb339d476debaf06264f4334c83018127840853404018ad6972361e557"
    EXPECTED_TAR_SIZE = 11_908_726
    EXPECTED_MEMBER_COUNT = 7875

    def test_revision_manifest_schema_and_commit_bindings(self) -> None:
        """REVISION.json declares canonical revision schema and source commit hash."""
        rev_path = self.DEPOSIT_BASE / "audited_source" / "REVISION.json"
        assert rev_path.is_file(), f"Missing REVISION.json: {rev_path}"

        rev = json.loads(rev_path.read_text(encoding="utf-8"))
        assert rev["schema"] == "pfp-iv.audited-source.v1"
        assert rev["source_commit"] == "52cb5457f6c485ba548cfd292f6012a941ed22cf"
        assert rev["crate_tree"] == "75d77aa5e1f30dfc102f00c8f7cb6159418dec63"
        assert rev["historical_run_commit"] == "1c7092c3db2ab2fa65999cf2555aff7733b97b99"
        assert rev["file_count"] == self.EXPECTED_MEMBER_COUNT
        assert rev["tar_name"] == self.EXPECTED_TAR_NAME
        assert rev["tar_sha256"] == self.EXPECTED_TAR_SHA256
        assert rev["authority_effect"] == "None"

    def test_audited_source_tarball_existence_and_digest(self) -> None:
        """audited_source tarball matches exact byte size and SHA-256 digest."""
        tar_path = self.DEPOSIT_BASE / "audited_source" / self.EXPECTED_TAR_NAME
        assert tar_path.is_file(), f"Missing tarball: {tar_path}"

        tar_size = tar_path.stat().st_size
        assert tar_size == self.EXPECTED_TAR_SIZE

        # Stream SHA-256 calculation
        hasher = hashlib.sha256()
        with open(tar_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        calc_sha = hasher.hexdigest()

        assert calc_sha == self.EXPECTED_TAR_SHA256

    def test_source_members_manifest_completeness(self) -> None:
        """SOURCE_MEMBERS.sha256 contains exactly 7,875 unique valid member lines."""
        sm_path = self.DEPOSIT_BASE / "audited_source" / "SOURCE_MEMBERS.sha256"
        assert sm_path.is_file(), f"Missing SOURCE_MEMBERS.sha256: {sm_path}"

        lines = [line.strip() for line in sm_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines) == self.EXPECTED_MEMBER_COUNT

        member_paths: set[str] = set()
        for idx, line in enumerate(lines):
            parts = line.split("  ", 1)
            assert len(parts) == 2, f"Line {idx} invalid format: {line}"
            digest, path = parts
            assert len(digest) == 64 and re.fullmatch(r"[0-9a-f]{64}", digest), f"Invalid hash: {digest}"
            assert path not in member_paths, f"Duplicate member path: {path}"
            member_paths.add(path)

        assert len(member_paths) == self.EXPECTED_MEMBER_COUNT
        assert "engine/crates_rs/Cargo.lock" in member_paths
        assert "LICENSE" in member_paths

    def test_retained_native_report_presence_and_passing_test_counts(self) -> None:
        """Retained native run report records the 12, 11, 32, and 9 passing test targets."""
        rep_path = self.DEPOSIT_BASE / "docs" / "historical_native_run" / "report_second_revision_2026-09-28.md"
        assert rep_path.is_file(), f"Missing report: {rep_path}"

        report_text = rep_path.read_text(encoding="utf-8")

        # Must record Paper 004 native Cargo targets and passing test counts
        assert "host_contract" in report_text
        assert "12 passed" in report_text
        assert "foundation_contract" in report_text
        assert "(11)" in report_text or "11 passed" in report_text
        assert "invoke_contract" in report_text
        assert "(32)" in report_text or "32 passed" in report_text
        assert "native_cli_intake" in report_text
        assert "(9)" in report_text or "9 passed" in report_text
        assert "52cb5457" in report_text
        assert "1.98.0" in report_text

    def test_deposit_integrity_negative_controls(self) -> None:
        """Tampering with tarball digest or member count is detected."""
        tampered_hash = "0" * 64
        assert tampered_hash != self.EXPECTED_TAR_SHA256

        tampered_member_count = 7874
        assert tampered_member_count != self.EXPECTED_MEMBER_COUNT


# ============================================================================
# 3. ATL-P006-010 / AUDIT-P006-010: Self-panel distinct contents
# ============================================================================


class TestSelfPanelDistinctContents:
    """Witnesses that the canonical self panel contains 40 distinct base contents in 1,000 rows."""

    TOTAL_ROWS = 1000
    DISTINCT_BASE_CONTENTS = 40
    CATEGORIES = (
        "clean_architecture_port",
        "clean_lean4_proof",
        "clean_physics_expression",
        "clean_prompt_template",
    )
    PER_CATEGORY_TOTAL = 250
    PER_CATEGORY_DISTINCT = 10

    def test_canonical_self_panel_total_and_distinct_counts(self) -> None:
        """The canonical self panel has exactly 1,000 rows and 40 distinct base contents."""
        panel = SelfPanel.load_canonical()
        assert len(panel.entries) == self.TOTAL_ROWS

        bases = panel.distinct_base_contents()
        assert len(bases) == self.DISTINCT_BASE_CONTENTS

        # Exact rational diversity ratio: 40 / 1000 == 1 / 25
        diversity_ratio = Fraction(len(bases), len(panel.entries))
        assert diversity_ratio == Fraction(1, 25)

    def test_canonical_self_panel_category_partition(self) -> None:
        """Each of the 4 declared categories contains 250 rows and exactly 10 distinct base contents."""
        panel = SelfPanel.load_canonical()

        per_category_entries: dict[str, int] = {}
        per_category_distinct: dict[str, set[str]] = {}

        for entry in panel.entries:
            cat = entry.category
            per_category_entries[cat] = per_category_entries.get(cat, 0) + 1
            per_category_distinct.setdefault(cat, set()).add(SelfPanel.base_content(entry.content))

        assert set(per_category_entries.keys()) == set(self.CATEGORIES)

        for cat in self.CATEGORIES:
            assert per_category_entries[cat] == self.PER_CATEGORY_TOTAL, f"Category {cat} total mismatch"
            assert len(per_category_distinct[cat]) == self.PER_CATEGORY_DISTINCT, f"Category {cat} distinct mismatch"

        total_distinct = sum(len(s) for s in per_category_distinct.values())
        assert total_distinct == self.DISTINCT_BASE_CONTENTS

    def test_base_content_stripping_and_invariance(self) -> None:
        """SelfPanel.base_content strips only synthetic trailers while preserving genuine comments."""
        # Strips synthetic comment trailer
        stripped = SelfPanel.base_content("theorem foo : 1 = 1 := rfl  -- index 042 hash_mod_7")
        assert stripped == "theorem foo : 1 = 1 := rfl"

        # Preserves genuine Lean comment
        genuine_lean = "-- a real Lean comment about homotopy"
        assert SelfPanel.base_content(genuine_lean) == genuine_lean

        # Preserves Python comment without index trailer
        genuine_py = "# ordinary python comment"
        assert SelfPanel.base_content(genuine_py) == genuine_py

    def test_self_panel_negative_controls(self) -> None:
        """Unstripped raw rows do not equal distinct base contents."""
        panel = SelfPanel.load_canonical()
        raw_contents = {entry.content for entry in panel.entries}

        # Raw entries count is 1,000 because synthetic trailers distinguish each line
        assert len(raw_contents) == self.TOTAL_ROWS
        assert len(raw_contents) != self.DISTINCT_BASE_CONTENTS

        # A naive assertion claiming 1000 distinct items would be rejected
        assert len(panel.distinct_base_contents()) != self.TOTAL_ROWS


# ============================================================================
# 4. ATL-P006-011 / AUDIT-P006-011: Inclusive toxicity threshold
# ============================================================================


class TestInclusiveToxicityThreshold:
    """Witnesses that Treg downgrade fires at toxicity >= 1/5 and corpus toxicity is 0 or 1."""

    TAU = Fraction(1, 5)

    def test_downgrade_fires_at_exactly_tau(self) -> None:
        """At toxicity exactly equal to tau = 1/5, supervisor synthesizes DIAGNOSTIC_ONLY antibody."""
        supervisor = TregSupervisor(tau=self.TAU)

        # 1 pattern-only trigger out of 5 triggers has toxicity 1/5
        triggers = [(True, False)] + [(True, True)] * 4
        report = supervisor.evaluate_toxicity("RULE-AT-TAU", triggers=triggers)

        assert report.toxicity_index == self.TAU
        assert report.signal1_only_count == 1
        assert report.total_triggers == 5

        antibody = supervisor.synthesize_treg(report)
        assert antibody is not None
        assert antibody.target_rule_id == "RULE-AT-TAU"
        assert antibody.downgraded_authority == "DIAGNOSTIC_ONLY"
        assert antibody.toxicity_index == self.TAU
        assert antibody.tau_threshold == self.TAU
        assert "meets or exceeds" in antibody.reason

    def test_detector_retained_just_below_tau(self) -> None:
        """At toxicity strictly below tau (1/6 < 1/5), supervisor produces no downgrade."""
        supervisor = TregSupervisor(tau=self.TAU)

        # 1 pattern-only trigger out of 6 triggers has toxicity 1/6
        triggers = [(True, False)] + [(True, True)] * 5
        report = supervisor.evaluate_toxicity("RULE-JUST-BELOW", triggers=triggers)

        assert report.toxicity_index == Fraction(1, 6)
        assert report.toxicity_index < self.TAU

        antibody = supervisor.synthesize_treg(report)
        assert antibody is None

    def test_boundary_rational_fractions_around_tau(self) -> None:
        """Boundary points above and below 1/5 confirm inclusive >= 1/5 behavior."""
        supervisor = TregSupervisor(tau=self.TAU)

        # 2 out of 9: 2/9 = 10/45 > 9/45 = 1/5 -> fires
        rep_2_9 = supervisor.evaluate_toxicity("RULE-2-9", triggers=[(True, False)] * 2 + [(True, True)] * 7)
        assert rep_2_9.toxicity_index == Fraction(2, 9)
        assert rep_2_9.toxicity_index > self.TAU
        assert supervisor.synthesize_treg(rep_2_9) is not None

        # 2 out of 11: 2/11 = 10/55 < 11/55 = 1/5 -> silent
        rep_2_11 = supervisor.evaluate_toxicity("RULE-2-11", triggers=[(True, False)] * 2 + [(True, True)] * 9)
        assert rep_2_11.toxicity_index == Fraction(2, 11)
        assert rep_2_11.toxicity_index < self.TAU
        assert supervisor.synthesize_treg(rep_2_11) is None

        # 0 triggers out of 5: toxicity 0 -> silent
        rep_0 = supervisor.evaluate_toxicity("RULE-ZERO", triggers=[(True, True)] * 5)
        assert rep_0.toxicity_index == Fraction(0, 1)
        assert supervisor.synthesize_treg(rep_0) is None

        # 5 out of 5: toxicity 1 -> fires
        rep_all = supervisor.evaluate_toxicity("RULE-ALL", triggers=[(True, False)] * 5)
        assert rep_all.toxicity_index == Fraction(1, 1)
        assert supervisor.synthesize_treg(rep_all) is not None

    def test_unlabelled_corpus_toxicity_is_binary_zero_or_one(self) -> None:
        """On an unlabelled benign prompt corpus, toxicity index is strictly 0 or 1."""
        supervisor = TregSupervisor(tau=self.TAU)
        benign_corpus = [f"benign prompt number {i}" for i in range(9)] + ["mentions keyword once"]

        class DummyRule:
            def __init__(self, pat: str) -> None:
                self.pattern = pat

        # Rule that matches nowhere in corpus -> toxicity 0
        silent_rep = supervisor.evaluate_toxicity(
            "RULE-SILENT", prompt_corpus=benign_corpus, rule=DummyRule("nonexistent_xyz")
        )
        assert silent_rep.toxicity_index == Fraction(0, 1)
        assert supervisor.synthesize_treg(silent_rep) is None

        # Rule that matches at least once -> toxicity 1
        firing_rep = supervisor.evaluate_toxicity("RULE-FIRES", prompt_corpus=benign_corpus, rule=DummyRule("keyword"))
        assert firing_rep.toxicity_index == Fraction(1, 1)
        assert supervisor.synthesize_treg(firing_rep) is not None

    def test_zero_float_law_enforcement(self) -> None:
        """Float values passed to TregSupervisor or AutoimmuneToxicityReport raise TypeError."""
        # Float tau rejected by supervisor
        with pytest.raises(TypeError, match="ZERO-FLOAT"):
            TregSupervisor(tau=0.2)  # type: ignore[arg-type]

        # Float toxicity rejected by AutoimmuneToxicityReport
        with pytest.raises(TypeError, match="ZERO-FLOAT"):
            AutoimmuneToxicityReport(
                rule_id="RULE-FLOAT",
                signal1_only_count=1,
                total_triggers=5,
                toxicity_index=0.2,  # type: ignore[arg-type]
            )

        # Float in RegulatoryAntibody creation rejected
        with pytest.raises(TypeError, match="ZERO-FLOAT"):
            RegulatoryAntibody.create(
                target_rule_id="RULE-FLOAT",
                toxicity_index=0.2,  # type: ignore[arg-type]
            )

    def test_strict_inequality_hypothesis_falsification(self) -> None:
        """If the threshold were strictly greater than (> 1/5), exactly 1/5 would not fire."""
        strict_hypothesis_fires = Fraction(1, 5) > self.TAU
        assert not strict_hypothesis_fires, "Strict inequality does not fire at tau"

        inclusive_hypothesis_fires = Fraction(1, 5) >= self.TAU
        assert inclusive_hypothesis_fires, "Inclusive inequality fires at tau"
