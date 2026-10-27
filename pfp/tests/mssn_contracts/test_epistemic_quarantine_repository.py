"""Targeted verification tests for Epistemic Quarantine Ledger Serialization,
Filesystem Repository Adapter, Cryptographic Hash Chains, and Truncation Falsification.

Enforces:
1. RFC 8785 Canonical JSON & Byte-Level Determinism.
2. Explicit Head Record Binding (thanatos-append-only-log-truncation-auditor).
3. Tail Truncation Falsification Testing (tail removal must be rejected).
4. Hash Chain Link Integrity & Bit Tampering Detection.
5. Permanent Quarantine Law (FW-SCOPE, Stage 10 floor).
6. UTF-8 Cleanliness without BOM (\xef\xbb\xbf).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure research directory is in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_RESEARCH_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, "..", ".."))
if _RESEARCH_DIR not in sys.path:
    sys.path.insert(0, _RESEARCH_DIR)

from pfp.domain.mssn_research.grammar.entities import (
    EpistemicQuarantineLedger,
)
from pfp.domain.mssn_research.grammar.errors import (
    LedgerIntegrityError,
    LedgerSerializationError,
    LedgerTruncationError,
    ScopeBoundaryViolationError,
)
from pfp.domain.mssn_research.grammar.exact_structures import (
    DownMapObstruction,
    HostFenceAudit,
    PontryaginKillFlags,
    ProtectedDistinction,
    QuarantinedShadowPacket,
)
from pfp.domain.mssn_research.grammar.ports import (
    EpistemicQuarantineLedgerRepository,
)
from pfp.domain.mssn_research.packets.value_objects import RefusalCode
from pfp.domain.mssn_research.shared_kernel.value_objects import StageLevel
from pfp.infrastructure.adapters.mssn_research.contracts.grammar.ledger_codec import (
    deserialize_ledger_from_jsonl,
    serialize_ledger_to_jsonl,
)
from pfp.infrastructure.adapters.mssn_research.contracts.grammar.ledger_repository import (
    EpistemicQuarantineRepository,
)


class TestEpistemicQuarantineRepository(unittest.TestCase):
    """Test suite verifying serialization, round-trip determinism, and truncation audits."""

    def setUp(self) -> None:
        self.stage8 = StageLevel(8)
        self.stage9 = StageLevel(9)
        self.stage10 = StageLevel(10)

        # Build sample antimorphic model and down-map obstruction
        distinction = ProtectedDistinction(
            state_a="sector_plus",
            state_b="sector_minus",
            label="fermion_sign_parity",
        )
        self.obs1 = DownMapObstruction(
            source_stage=self.stage9,
            target_stage=self.stage8,
            obstructed_distinction=distinction,
            collapsed_target_state="sector_trivial",
            message="Down-map erases fermion sign parity",
        )
        self.packet1 = self.obs1.to_quarantined_shadow_packet(
            target_theorem="parity_obstruction_S9_to_S8"
        )

        # Build sample Pontryagin firewall kill shadow packet
        flags2 = PontryaginKillFlags(flag_pi=True)
        audit2 = HostFenceAudit.evaluate(flags2)
        self.packet2 = QuarantinedShadowPacket(
            target_theorem="pi_from_exact_q_refusal",
            assertion_flags=flags2,
            fence_audit=audit2,
            shadow_type="pontryagin_kill_firewall",
            evidence_bound="Stage10_Kill",
            raw_transcript=(
                "assertion: PI_FROM_EXACT_Q breached",
                "host_verdict: ViolatedKillFence (<0>)",
                "action: permanent quarantine commit",
            ),
        )

        # Populated ledger
        self.ledger_populated = EpistemicQuarantineLedger(
            ledger_id="ledger/test_quarantine_populated",
            stage_level=self.stage10,
            entries=(self.packet1, self.packet2),
        )

    def test_round_trip_empty_ledger_serialization(self) -> None:
        """Verify that an empty ledger serializes to a valid header and reconstructs identically."""
        empty_ledger = EpistemicQuarantineLedger(
            ledger_id="ledger/test_empty",
            stage_level=self.stage10,
            entries=(),
        )
        jsonl_str = serialize_ledger_to_jsonl(empty_ledger)
        lines = [line for line in jsonl_str.strip().split("\n") if line]

        # Must have exactly 1 record (HEADER)
        self.assertEqual(len(lines), 1)
        header = json.loads(lines[0])
        self.assertEqual(header["record_type"], "HEADER")
        self.assertEqual(header["ledger_id"], "ledger/test_empty")
        self.assertEqual(header["stage_level"], 10)
        self.assertEqual(header["entry_count"], 0)
        self.assertEqual(header["head_digest"], "genesis")

        # Deserialization round-trip
        reconstructed_res = deserialize_ledger_from_jsonl(jsonl_str)
        self.assertTrue(reconstructed_res.is_ok())
        reconstructed = reconstructed_res.unwrap()

        self.assertEqual(reconstructed, empty_ledger)
        self.assertEqual(reconstructed.entry_count, 0)

        # Byte-level determinism
        re_serialized = serialize_ledger_to_jsonl(reconstructed)
        self.assertEqual(re_serialized, jsonl_str)

    def test_round_trip_populated_ledger_serialization(self) -> None:
        """Verify that a populated ledger serializes to RFC 8785 canonical JSON-L and round-trips exactly."""
        jsonl_str = serialize_ledger_to_jsonl(self.ledger_populated)
        lines = [line for line in jsonl_str.strip().split("\n") if line]

        # Line count: 1 header + 2 entries = 3 lines
        self.assertEqual(len(lines), 3)

        # Header inspection
        header = json.loads(lines[0])
        self.assertEqual(header["record_type"], "HEADER")
        self.assertEqual(header["entry_count"], 2)
        self.assertEqual(header["schema_version"], "v1")

        # Entry inspection
        entry0 = json.loads(lines[1])
        self.assertEqual(entry0["record_type"], "ENTRY")
        self.assertEqual(entry0["entry_index"], 0)
        self.assertEqual(entry0["prev_digest"], "genesis")
        self.assertEqual(entry0["packet"]["target_theorem"], "parity_obstruction_S9_to_S8")

        entry1 = json.loads(lines[2])
        self.assertEqual(entry1["record_type"], "ENTRY")
        self.assertEqual(entry1["entry_index"], 1)
        self.assertEqual(entry1["prev_digest"], entry0["entry_digest"])
        self.assertEqual(entry1["packet"]["target_theorem"], "pi_from_exact_q_refusal")

        # Header head_digest must match last entry's digest
        self.assertEqual(header["head_digest"], entry1["entry_digest"])

        # Deserialization
        reconstructed_res = deserialize_ledger_from_jsonl(jsonl_str)
        self.assertTrue(reconstructed_res.is_ok(), f"Failed to deserialize: {reconstructed_res}")
        reconstructed = reconstructed_res.unwrap()

        self.assertEqual(reconstructed, self.ledger_populated)
        self.assertEqual(reconstructed.entry_count, 2)
        self.assertEqual(reconstructed.entries[0], self.packet1)
        self.assertEqual(reconstructed.entries[1], self.packet2)

        # Byte-for-byte exact determinism check
        self.assertEqual(serialize_ledger_to_jsonl(reconstructed), jsonl_str)

    def test_disk_fixture_determinism_and_bom_cleanliness(self) -> None:
        """Verify atomic writing, pure UTF-8 encoding (no BOM), and loading from disk fixtures."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = EpistemicQuarantineRepository(tmp_dir)
            self.assertIsInstance(repo, EpistemicQuarantineLedgerRepository)

            # Save to disk
            save_res = repo.save(self.ledger_populated)
            self.assertTrue(save_res.is_ok())
            file_path = save_res.unwrap()

            self.assertTrue(file_path.exists())
            self.assertTrue(file_path.is_file())

            # Read raw bytes directly from disk
            raw_bytes = file_path.read_bytes()
            self.assertFalse(
                raw_bytes.startswith(b"\xef\xbb\xbf"),
                "UTF-8 BOM detected in disk fixture; must be pure UTF-8 without BOM",
            )

            # Verify line endings are LF (\n)
            raw_text = raw_bytes.decode("utf-8")
            self.assertNotIn("\r\n", raw_text, "CRLF detected; must use standard LF newlines")

            # Load back through repository adapter
            load_res = repo.load(self.ledger_populated.ledger_id)
            self.assertTrue(load_res.is_ok())
            loaded_ledger = load_res.unwrap()

            self.assertEqual(loaded_ledger, self.ledger_populated)

            # Load directly via load_from_path
            path_res = repo.load_from_path(file_path)
            self.assertTrue(path_res.is_ok())
            self.assertEqual(path_res.unwrap(), self.ledger_populated)

    def test_tail_truncation_falsification_testing(self) -> None:
        """Tail Truncation Falsification Testing: removing the last entry must be rejected."""
        jsonl_str = serialize_ledger_to_jsonl(self.ledger_populated)
        lines = [line for line in jsonl_str.strip().split("\n") if line]

        # Explicitly remove the last (tail) entry (entry 1)
        truncated_lines = lines[:-1]
        truncated_jsonl = "\n".join(truncated_lines) + "\n"

        res = deserialize_ledger_from_jsonl(truncated_jsonl)
        self.assertTrue(res.is_refusal(), "Expected tail-truncated log to be refused")
        self.assertIsInstance(res.refusal, LedgerTruncationError)
        self.assertEqual(res.refusal.code, RefusalCode.HOST_VERIFICATION_REQUIRED)
        self.assertIn("Tail truncation detected", res.refusal.message)
        self.assertIn("header declared 2 entries, but found only 1", res.refusal.message)

    def test_log_extension_falsification_testing(self) -> None:
        """Log Extension Falsification: appending extra entry beyond declared head must be rejected."""
        jsonl_str = serialize_ledger_to_jsonl(self.ledger_populated)
        lines = [line for line in jsonl_str.strip().split("\n") if line]

        # Duplicate the last entry as an illicit append
        extended_lines = [*lines, lines[-1]]
        extended_jsonl = "\n".join(extended_lines) + "\n"

        res = deserialize_ledger_from_jsonl(extended_jsonl)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, LedgerTruncationError)
        self.assertIn("Log extension detected beyond declared head", res.refusal.message)

    def test_interior_payload_tampering_falsification(self) -> None:
        """Interior Record Tampering Falsification: payload mutation breaks cryptographic SHA-256 digest."""
        jsonl_str = serialize_ledger_to_jsonl(self.ledger_populated)
        lines = [line for line in jsonl_str.strip().split("\n") if line]

        # Parse entry 0, tamper with target_theorem, but keep original claimed entry_digest
        entry0_dict = json.loads(lines[1])
        entry0_dict["packet"]["target_theorem"] = "tampered_theorem_name"
        tampered_line1 = json.dumps(entry0_dict, sort_keys=True, separators=(",", ":"))

        tampered_lines = [lines[0], tampered_line1, lines[2]]
        tampered_jsonl = "\n".join(tampered_lines) + "\n"

        res = deserialize_ledger_from_jsonl(tampered_jsonl)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, LedgerIntegrityError)
        self.assertEqual(res.refusal.code, RefusalCode.HOST_VERIFICATION_REQUIRED)
        self.assertIn("Record tampering detected at entry 0", res.refusal.message)

    def test_hash_chain_prev_digest_tampering(self) -> None:
        """Hash Chain Break: altering prev_digest link breaks causal chain continuity."""
        jsonl_str = serialize_ledger_to_jsonl(self.ledger_populated)
        lines = [line for line in jsonl_str.strip().split("\n") if line]

        # Alter prev_digest on entry 1
        entry1_dict = json.loads(lines[2])
        entry1_dict["prev_digest"] = "bad_previous_digest_hash_00000000000000000000000000000000"
        # Even if someone recomputes digest for entry 1:
        tampered_line2 = json.dumps(entry1_dict, sort_keys=True, separators=(",", ":"))

        tampered_lines = [lines[0], lines[1], tampered_line2]
        tampered_jsonl = "\n".join(tampered_lines) + "\n"

        res = deserialize_ledger_from_jsonl(tampered_jsonl)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, LedgerIntegrityError)
        self.assertIn("Hash chain break at entry 1", res.refusal.message)

    def test_header_head_digest_tampering(self) -> None:
        """Head Digest Tampering: mismatch between header head_digest and chain final digest is rejected."""
        jsonl_str = serialize_ledger_to_jsonl(self.ledger_populated)
        lines = [line for line in jsonl_str.strip().split("\n") if line]

        header_dict = json.loads(lines[0])
        header_dict["head_digest"] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        tampered_header = json.dumps(header_dict, sort_keys=True, separators=(",", ":"))

        tampered_lines = [tampered_header, lines[1], lines[2]]
        tampered_jsonl = "\n".join(tampered_lines) + "\n"

        res = deserialize_ledger_from_jsonl(tampered_jsonl)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, LedgerIntegrityError)
        self.assertIn("Head digest mismatch", res.refusal.message)

    def test_header_stage_floor_enforcement(self) -> None:
        """Header Stage Floor: stage_level < 10 violates Permanent Quarantine Law (FW-SCOPE)."""
        jsonl_str = serialize_ledger_to_jsonl(self.ledger_populated)
        lines = [line for line in jsonl_str.strip().split("\n") if line]

        header_dict = json.loads(lines[0])
        header_dict["stage_level"] = 9  # Attempt illicit import to core stage
        tampered_header = json.dumps(header_dict, sort_keys=True, separators=(",", ":"))

        tampered_lines = [tampered_header, lines[1], lines[2]]
        tampered_jsonl = "\n".join(tampered_lines) + "\n"

        res = deserialize_ledger_from_jsonl(tampered_jsonl)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, ScopeBoundaryViolationError)
        self.assertEqual(res.refusal.code, RefusalCode.NONCONSERVATIVE_LIFT)
        self.assertIn("FW-SCOPE", res.refusal.message)

    def test_bom_rejection_in_disk_load(self) -> None:
        """Repository load rejects files containing UTF-8 BOM."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = EpistemicQuarantineRepository(tmp_dir)
            jsonl_str = serialize_ledger_to_jsonl(self.ledger_populated)
            bom_bytes = b"\xef\xbb\xbf" + jsonl_str.encode("utf-8")

            bom_file = Path(tmp_dir) / "bom_ledger.jsonl"
            bom_file.write_bytes(bom_bytes)

            res = repo.load_from_path(bom_file)
            self.assertTrue(res.is_refusal())
            self.assertIsInstance(res.refusal, LedgerSerializationError)
            self.assertIn("UTF-8 BOM detected", res.refusal.message)

    def test_loaded_ledger_preserves_scope_boundary_isolation(self) -> None:
        """Verify that a ledger loaded from disk strictly enforces FW-SCOPE isolation against core stages <= 9."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = EpistemicQuarantineRepository(tmp_dir)
            save_res = repo.save(self.ledger_populated)
            self.assertTrue(save_res.is_ok())

            loaded = repo.load(self.ledger_populated.ledger_id).unwrap()

            # Isolation against core stage 8 must return typed refusal
            check_s8 = loaded.verify_isolation_against_stage(self.stage8)
            self.assertTrue(check_s8.is_refusal())
            self.assertIsInstance(check_s8.refusal, ScopeBoundaryViolationError)
            self.assertIn("FW-SCOPE", check_s8.refusal.message)

            # Isolation check against Stage 10 passes
            check_s10 = loaded.verify_isolation_against_stage(self.stage10)
            self.assertTrue(check_s10.is_ok())
            self.assertTrue(check_s10.unwrap())

    def test_codec_rejects_wrong_types_and_schema_before_allocation(self) -> None:
        """Malformed boundary types and schema versions fail closed as typed refusals."""
        not_text = deserialize_ledger_from_jsonl(b"{}")  # type: ignore[arg-type]
        self.assertTrue(not_text.is_refusal())
        self.assertIsInstance(not_text.refusal, LedgerSerializationError)

        header = json.loads(serialize_ledger_to_jsonl(self.ledger_populated).splitlines()[0])
        header["stage_level"] = True
        bad_stage = deserialize_ledger_from_jsonl(json.dumps(header) + "\n")
        self.assertTrue(bad_stage.is_refusal())
        self.assertIn("integer stage_level", bad_stage.refusal.message)

        header["stage_level"] = 10
        header["schema_version"] = "v999"
        bad_schema = deserialize_ledger_from_jsonl(json.dumps(header) + "\n")
        self.assertTrue(bad_schema.is_refusal())
        self.assertIn("schema_version", bad_schema.refusal.message)

    def test_repository_confines_paths_and_avoids_identifier_collisions(self) -> None:
        """Path-like IDs are digest-addressed while arbitrary load paths are refused."""
        first = EpistemicQuarantineLedger("a/b", self.stage10)
        second = EpistemicQuarantineLedger("a\\b", self.stage10)
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as outside:
            repo = EpistemicQuarantineRepository(tmp_dir)
            first_path = repo.save(first).unwrap()
            second_path = repo.save(second).unwrap()
            self.assertNotEqual(first_path, second_path)
            self.assertEqual(repo.load("a/b").unwrap(), first)
            self.assertEqual(repo.load("a\\b").unwrap(), second)

            outside_path = Path(outside) / "escaped.jsonl"
            outside_path.write_text(serialize_ledger_to_jsonl(first), encoding="utf-8")
            refused = repo.load_from_path(outside_path)
            self.assertTrue(refused.is_refusal())
            self.assertIn("escapes", refused.refusal.message)


if __name__ == "__main__":
    unittest.main()
