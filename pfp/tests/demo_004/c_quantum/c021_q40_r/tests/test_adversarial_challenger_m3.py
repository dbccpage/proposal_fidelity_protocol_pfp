"""Adversarial Stress-Test Harness for Milestone 3 Governance and Commit-Reveal.

Challenger 1 (Milestone 3 - C021 Q40-R Stabilizer Challenge).
Empirically stress-tests commit_reveal_runner.py and adversary_gate.py against:
1. Manifest and Case File Tampering:
   - Modification of bytes in judge_packet/manifest.json (timestamp, counts, file hashes).
   - Modification of bytes in individual judge case files (semantic changes vs syntax corruption).
   - Audits whether Phase 3 detects individual case file tampering or silently evaluates tampered cases.
2. Solver Tampering:
   - Modification of bytes in reference_solver/solver.py after freeze record generation.
   - Modification of bytes in reference_solver/pauli.py after freeze record generation.
   - Modification of bytes in reference_solver/ddc_tracer.py after freeze record generation.
   - Deletion of solver files after freeze record generation.
3. Out-of-Order Protocol Execution:
   - Invocation of Phase 2 (Solver Freeze) without Phase 1 (Judge Commitment).
   - Invocation of Phase 3 (Reveal and Score) without Phase 1 and Phase 2.
   - Invocation of Phase 3 with Phase 1 present but Phase 2 missing.
   - Invocation of Phase 3 with Phase 2 present but Phase 1 missing.
4. Collision Protection in adversary_gate.py:
   - Persisting run bundle to existing task_key in _intelligence/_adversary/runs/.
   - Persisting run bundle to existing run_id in _intelligence/symbol_game/runs/.
   - Direct persist_single_bundle invocation against existing target directory.
   - Verifying existing run bundles remain byte-for-byte intact upon collision rejection.
   - Verifying no temporary directories are leaked upon collision rejection.
5. StructureBench Reverse Write Order Protocol:
   - Post-hoc alteration of novella.md breaks receipt.json cryptographic binding.
   - Post-hoc alteration of dda_actions.jsonl breaks receipt.json cryptographic binding.
   - Post-hoc alteration of dda_actions.jsonl breaks internal DDC sequential hash-chain tape.
   - Post-hoc alteration of summary.json breaks receipt.json cryptographic binding.
   - Verification that scoring_receipt.json cryptographically binds receipt.json digest.
6. Error Handling & Clean Halting vs Unhandled Crashes:
   - Audit of exception hierarchy (ValueError, RuntimeError, RunFolderExistsError, FileNotFoundError).
   - Detection of unhandled json.decoder.JSONDecodeError on malformed case files.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.commit_reveal_runner import (
    CommitRevealRunner,
    sha256_of_file,
)
from projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.governance.adversary_gate import (
    RUN_FOLDER_EXISTS,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    RunFolderExistsError,
    AdversaryGate,
    persist_single_bundle,
)


def _setup_isolated_challenge(tmp_path: Path) -> tuple[Path, CommitRevealRunner]:
    """Helper to create a fully isolated challenge copy for destructive testing."""
    src_challenge = Path(__file__).resolve().parent.parent
    dest_challenge = tmp_path / "c021_q40_r"
    shutil.copytree(
        src_challenge, dest_challenge, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )
    runner = CommitRevealRunner(challenge_root=dest_challenge, intelligence_repo_root=tmp_path)
    return dest_challenge, runner


# ============================================================================
# Suite 1: Manifest & Case File Tampering
# ============================================================================


class TestManifestAndCaseTampering:
    """Adversarial suite for judge packet manifest and case file tampering."""

    def test_manifest_tampering_modified_utc_timestamp_halts(self, tmp_path: Path) -> None:
        """Modifying a single byte in manifest.json metadata must cause Phase 3 to halt."""
        dest_challenge, runner = _setup_isolated_challenge(tmp_path)
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        manifest_file = dest_challenge / "judge_packet" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data["created_utc"] = "2026-09-27T02:50:01Z"  # 1 character altered
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        with pytest.raises(ValueError, match="Judge manifest SHA-256 mismatch"):
            runner.run_phase3_reveal_and_score(task_key="test_tamper_manifest_utc")

    def test_manifest_tampering_modified_file_entry_sha256_halts(self, tmp_path: Path) -> None:
        """Modifying a single file digest inside manifest.json must cause Phase 3 to halt."""
        dest_challenge, runner = _setup_isolated_challenge(tmp_path)
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        manifest_file = dest_challenge / "judge_packet" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        # Flip first character of first file's sha256
        old_sha = manifest_data["files"][0]["sha256"]
        new_sha = ("0" if old_sha[0] != "0" else "1") + old_sha[1:]
        manifest_data["files"][0]["sha256"] = new_sha
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        with pytest.raises(ValueError, match="Judge manifest SHA-256 mismatch"):
            runner.run_phase3_reveal_and_score(task_key="test_tamper_manifest_sha")

    def test_manifest_tampering_truncated_manifest_halts(self, tmp_path: Path) -> None:
        """Truncating the last byte of manifest.json must cause Phase 3 to halt."""
        dest_challenge, runner = _setup_isolated_challenge(tmp_path)
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        manifest_file = dest_challenge / "judge_packet" / "manifest.json"
        data = manifest_file.read_bytes()
        manifest_file.write_bytes(data[:-1])  # Drop trailing byte

        with pytest.raises(ValueError, match="Judge manifest SHA-256 mismatch"):
            runner.run_phase3_reveal_and_score(task_key="test_tamper_manifest_trunc")

    def test_case_file_tampering_semantic_modification_audit(self, tmp_path: Path) -> None:
        """EMPIRICAL AUDIT: Tests whether modifying a case file without updating manifest.json is detected.

        Adversary alters case_01.json terms to a different valid Hamiltonian after Phase 1 and 2.
        If Phase 3 does not verify case files against manifest_data['files'], this tampering
        slips through completely undetected!
        """
        dest_challenge, runner = _setup_isolated_challenge(tmp_path)
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        case_file = dest_challenge / "judge_packet" / "cases" / "base" / "case_01.json"
        original_bytes = case_file.read_bytes()
        case_data = json.loads(original_bytes.decode("utf-8"))

        # Adversarially modify term weight from [1, 1] to [99, 1]
        case_data["terms"][0]["w"] = [99, 1]
        tampered_bytes = json.dumps(case_data, indent=2).encode("utf-8")
        case_file.write_bytes(tampered_bytes)

        # Confirm case file SHA-256 is changed on disk
        assert (
            hashlib.sha256(tampered_bytes).hexdigest() != hashlib.sha256(original_bytes).hexdigest()
        )

        # Check manifest.json SHA-256 is unchanged
        manifest_file = dest_challenge / "judge_packet" / "manifest.json"
        commit_file = dest_challenge / "commitments" / "c021_q40_r_judge_commitment.json"
        commit_data = json.loads(commit_file.read_text(encoding="utf-8"))
        assert sha256_of_file(manifest_file) == commit_data["manifest_sha256"]

        # Run Phase 3: Observe that Phase 3 catches the modified case file and halts fail-closed
        with pytest.raises(
            ValueError, match=r"Judge file cases/base/case_01\.json was modified or corrupted"
        ):
            runner.run_phase3_reveal_and_score(task_key="test_tamper_case_semantic")

    def test_case_file_tampering_syntax_corruption_audit(self, tmp_path: Path) -> None:
        """EMPIRICAL AUDIT: Tests behavior when a byte in a case file is corrupted into invalid JSON.

        Verifies that malformed JSON in a committed case file is caught cleanly as a domain
        integrity failure (ValueError) rather than an unhandled json.decoder.JSONDecodeError.
        """
        dest_challenge, runner = _setup_isolated_challenge(tmp_path)

        case_file = dest_challenge / "judge_packet" / "cases" / "base" / "case_01.json"
        raw = bytearray(case_file.read_bytes())
        raw[0] = ord(b"X")
        case_file.write_bytes(raw)
        new_case_sha = hashlib.sha256(raw).hexdigest()

        # Update manifest to match the corrupted file's digest so file hash verification passes
        manifest_file = dest_challenge / "judge_packet" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        for f in manifest_data["files"]:
            if f["path"] == "cases/base/case_01.json":
                f["sha256"] = new_case_sha
                break
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        # Confirm it raises domain integrity ValueError rather than unhandled JSONDecodeError
        with pytest.raises(ValueError, match=r"Corrupted judge case file case_01\.json:"):
            runner.run_phase3_reveal_and_score(task_key="test_tamper_case_syntax")

    def test_case_file_deletion_after_commitment_halts(self, tmp_path: Path) -> None:
        """Deleting a committed judge case file after Phase 1 must raise FileNotFoundError."""
        dest_challenge, runner = _setup_isolated_challenge(tmp_path)
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        case_file = dest_challenge / "judge_packet" / "cases" / "base" / "case_01.json"
        case_file.unlink()

        with pytest.raises(
            FileNotFoundError, match=r"Committed judge file not found: cases/base/case_01\.json"
        ):
            runner.run_phase3_reveal_and_score(task_key="test_tamper_delete_case")

    def test_case_file_unicode_decode_corruption_halts(self, tmp_path: Path) -> None:
        """Verifies that non-UTF-8 bytes in a case file raise a domain integrity ValueError."""
        dest_challenge, runner = _setup_isolated_challenge(tmp_path)

        case_file = dest_challenge / "judge_packet" / "cases" / "base" / "case_01.json"
        bad_bytes = b"\xff\xfe\x00\x00"  # Invalid UTF-8 sequence
        case_file.write_bytes(bad_bytes)
        new_case_sha = hashlib.sha256(bad_bytes).hexdigest()

        manifest_file = dest_challenge / "judge_packet" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        for f in manifest_data["files"]:
            if f["path"] == "cases/base/case_01.json":
                f["sha256"] = new_case_sha
                break
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        with pytest.raises(ValueError, match=r"Corrupted judge case file case_01\.json:"):
            runner.run_phase3_reveal_and_score(task_key="test_tamper_case_unicode")


# ============================================================================
# Suite 2: Solver Tampering
# ============================================================================


class TestSolverTampering:
    """Adversarial suite testing detection of post-freeze solver modifications."""

    @pytest.mark.parametrize(
        "target_rel_path",
        [
            "reference_solver/solver.py",
            "reference_solver/pauli.py",
            "reference_solver/ddc_tracer.py",
        ],
    )
    def test_solver_file_byte_modification_halts(
        self, tmp_path: Path, target_rel_path: str
    ) -> None:
        """Modifying 1 byte in any frozen solver file must cause Phase 3 to halt."""
        dest_challenge, runner = _setup_isolated_challenge(tmp_path)
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        target_file = dest_challenge / target_rel_path
        content = target_file.read_text(encoding="utf-8")
        target_file.write_text(content + " ", encoding="utf-8")  # Append single space byte

        with pytest.raises(
            ValueError, match=f"Solver file {target_rel_path} was modified after freeze"
        ):
            runner.run_phase3_reveal_and_score(task_key=f"test_tamper_{target_file.stem}")

    def test_solver_file_deletion_after_freeze_halts(self, tmp_path: Path) -> None:
        """Deleting a frozen solver file after freeze must cause Phase 3 to halt fail-closed."""
        dest_challenge, runner = _setup_isolated_challenge(tmp_path)
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()

        solver_file = dest_challenge / "reference_solver" / "solver.py"
        solver_file.unlink()

        with pytest.raises(FileNotFoundError):
            runner.run_phase3_reveal_and_score(task_key="test_tamper_delete_solver")


# ============================================================================
# Suite 3: Out-of-Order Protocol Execution
# ============================================================================


class TestOutOfOrderExecution:
    """Adversarial suite verifying fail-closed enforcement of protocol sequence."""

    def test_phase2_without_phase1_halts_fail_closed(self, tmp_path: Path) -> None:
        """Attempting Phase 2 without Phase 1 must raise RuntimeError."""
        dest_challenge = tmp_path / "c021_q40_r"
        (dest_challenge / "commitments").mkdir(parents=True)
        runner = CommitRevealRunner(challenge_root=dest_challenge, intelligence_repo_root=tmp_path)

        with pytest.raises(RuntimeError, match="Phase 1 judge commitment must precede Phase 2"):
            runner.run_phase2_freeze_record()

    def test_phase3_without_commitments_halts_fail_closed(self, tmp_path: Path) -> None:
        """Attempting Phase 3 without any prior commitments must raise RuntimeError."""
        dest_challenge = tmp_path / "c021_q40_r"
        (dest_challenge / "commitments").mkdir(parents=True)
        runner = CommitRevealRunner(challenge_root=dest_challenge, intelligence_repo_root=tmp_path)

        with pytest.raises(
            RuntimeError, match="Both judge commitment and solver freeze record must exist"
        ):
            runner.run_phase3_reveal_and_score()

    def test_phase3_with_phase1_only_halts_fail_closed(self, tmp_path: Path) -> None:
        """Attempting Phase 3 with Phase 1 present but Phase 2 missing must raise RuntimeError."""
        dest_challenge = tmp_path / "c021_q40_r"
        commitments_dir = dest_challenge / "commitments"
        commitments_dir.mkdir(parents=True)
        (commitments_dir / "c021_q40_r_judge_commitment.json").write_text("{}", encoding="utf-8")

        runner = CommitRevealRunner(challenge_root=dest_challenge, intelligence_repo_root=tmp_path)

        with pytest.raises(
            RuntimeError, match="Both judge commitment and solver freeze record must exist"
        ):
            runner.run_phase3_reveal_and_score()

    def test_phase3_with_phase2_only_halts_fail_closed(self, tmp_path: Path) -> None:
        """Attempting Phase 3 with Phase 2 present but Phase 1 missing must raise RuntimeError."""
        dest_challenge = tmp_path / "c021_q40_r"
        commitments_dir = dest_challenge / "commitments"
        commitments_dir.mkdir(parents=True)
        (commitments_dir / "c021_q40_r_freeze_record.json").write_text("{}", encoding="utf-8")

        runner = CommitRevealRunner(challenge_root=dest_challenge, intelligence_repo_root=tmp_path)

        with pytest.raises(
            RuntimeError, match="Both judge commitment and solver freeze record must exist"
        ):
            runner.run_phase3_reveal_and_score()


# ============================================================================
# Suite 4: Collision Protection in adversary_gate.py
# ============================================================================


class TestAdversaryGateCollisionProtection:
    """Adversarial suite verifying RUN_FOLDER_EXISTS collision protection."""

    def test_adversary_gate_task_key_collision_raises(self, tmp_path: Path) -> None:
        """Attempting to persist a bundle when the Adversary task directory exists must fail."""
        gate = AdversaryGate(base_repo_root=tmp_path)
        cases = [{"case_id": "c1", "verdict": "PASS", "agreement": True}]
        claim = {
            "supports": "s",
            "does_not_support": "d",
            "narrowest_defensible_claim": "n",
            "next_test_needed": "t",
        }

        # Run 1 succeeds
        gate.evaluate_and_persist(
            task_key="collision_test_task",
            run_id="run_id_001",
            case_results=cases,
            claim_hygiene=claim,
        )

        # Run 2 with same task_key but different run_id must raise RunFolderExistsError
        with pytest.raises(RunFolderExistsError) as exc_info:
            gate.evaluate_and_persist(
                task_key="collision_test_task",
                run_id="run_id_002",
                case_results=cases,
                claim_hygiene=claim,
            )
        assert exc_info.value.code == RUN_FOLDER_EXISTS
        assert "Adversary run directory already exists" in str(exc_info.value)

    def test_adversary_gate_run_id_collision_raises(self, tmp_path: Path) -> None:
        """Attempting to persist a bundle when the Symbol Game run directory exists must fail."""
        gate = AdversaryGate(base_repo_root=tmp_path)
        cases = [{"case_id": "c1", "verdict": "PASS", "agreement": True}]
        claim = {
            "supports": "s",
            "does_not_support": "d",
            "narrowest_defensible_claim": "n",
            "next_test_needed": "t",
        }

        # Run 1 succeeds
        gate.evaluate_and_persist(
            task_key="task_key_001",
            run_id="collision_test_run",
            case_results=cases,
            claim_hygiene=claim,
        )

        # Run 2 with different task_key but same run_id must raise RunFolderExistsError
        with pytest.raises(RunFolderExistsError) as exc_info:
            gate.evaluate_and_persist(
                task_key="task_key_002",
                run_id="collision_test_run",
                case_results=cases,
                claim_hygiene=claim,
            )
        assert exc_info.value.code == RUN_FOLDER_EXISTS
        assert "Symbol Game run directory already exists" in str(exc_info.value)

    def test_persist_single_bundle_collision_raises(self, tmp_path: Path) -> None:
        """Direct persist_single_bundle call against an existing directory must raise RunFolderExistsError."""
        target_dir = tmp_path / "direct_bundle"
        target_dir.mkdir(parents=True)

        with pytest.raises(RunFolderExistsError) as exc_info:
            persist_single_bundle(
                target_dir=target_dir,
                novella_md="# Novella",
                dda_steps=[],
                summary_data={},
                receipt_data={},
            )
        assert exc_info.value.code == RUN_FOLDER_EXISTS

    def test_collision_leaves_existing_files_intact(self, tmp_path: Path) -> None:
        """Assert that an aborted collision attempt leaves pre-existing bundle files untouched."""
        gate = AdversaryGate(base_repo_root=tmp_path)
        cases = [{"case_id": "c1", "verdict": "PASS", "agreement": True}]
        claim = {
            "supports": "s",
            "does_not_support": "d",
            "narrowest_defensible_claim": "n",
            "next_test_needed": "t",
        }

        _, path_adversary, _, _ = gate.evaluate_and_persist(
            task_key="intact_check_task",
            run_id="intact_check_run",
            case_results=cases,
            claim_hygiene=claim,
        )

        # Snapshot receipts
        receipt_before = (path_adversary / "receipt.json").read_bytes()
        novella_before = (path_adversary / "novella.md").read_bytes()

        # Trigger collision
        with pytest.raises(RunFolderExistsError):
            gate.evaluate_and_persist(
                task_key="intact_check_task",
                run_id="intact_diff_run",
                case_results=cases,
                claim_hygiene=claim,
            )

        # Assert no corruption or truncation occurred
        assert (path_adversary / "receipt.json").read_bytes() == receipt_before
        assert (path_adversary / "novella.md").read_bytes() == novella_before

    def test_no_temp_directory_leakage_on_collision(self, tmp_path: Path) -> None:
        """Verifies that no hidden temporary directories (.task_key.*) remain in the parent."""
        runs_parent = tmp_path / "_intelligence" / "_adversary" / "runs"
        gate = AdversaryGate(base_repo_root=tmp_path)
        cases = [{"case_id": "c1", "verdict": "PASS", "agreement": True}]
        claim = {
            "supports": "s",
            "does_not_support": "d",
            "narrowest_defensible_claim": "n",
            "next_test_needed": "t",
        }

        gate.evaluate_and_persist(
            task_key="leak_test",
            run_id="leak_test_run",
            case_results=cases,
            claim_hygiene=claim,
        )

        with pytest.raises(RunFolderExistsError):
            gate.evaluate_and_persist(
                task_key="leak_test",
                run_id="leak_diff_run",
                case_results=cases,
                claim_hygiene=claim,
            )

        # Assert only the committed directory exists, no temporary directories
        dir_names = [p.name for p in runs_parent.iterdir() if p.is_dir()]
        assert dir_names == ["leak_test"], f"Found lingering temporary directories: {dir_names}"


# ============================================================================
# Suite 5: StructureBench Reverse Write Order Binding
# ============================================================================


class TestStructureBenchReverseWriteOrder:
    """Adversarial suite verifying StructureBench reverse write order digest integrity."""

    def test_altering_novella_breaks_receipt_binding(self, tmp_path: Path) -> None:
        """Altering novella.md post-hoc must invalidate the digest stored in receipt.json."""
        gate = AdversaryGate(base_repo_root=tmp_path)
        cases = [{"case_id": "c1", "verdict": "PASS", "agreement": True}]
        claim = {
            "supports": "s",
            "does_not_support": "d",
            "narrowest_defensible_claim": "n",
            "next_test_needed": "t",
        }

        _, path_adversary, _, digests = gate.evaluate_and_persist(
            task_key="reverse_order_novella",
            run_id="reverse_order_novella_run",
            case_results=cases,
            claim_hygiene=claim,
        )

        novella_file = path_adversary / "novella.md"
        receipt_file = path_adversary / "receipt.json"
        receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))

        # Verify initial binding matches
        assert sha256_of_file(novella_file) == receipt_data["novella_sha256"]

        # Tamper novella.md
        novella_file.write_text(
            novella_file.read_text(encoding="utf-8") + "\n# Malicious Append\n", encoding="utf-8"
        )

        # Verify binding is broken
        recomputed_sha = sha256_of_file(novella_file)
        assert recomputed_sha != receipt_data["novella_sha256"]

    def test_altering_dda_actions_breaks_receipt_binding(self, tmp_path: Path) -> None:
        """Altering dda_actions.jsonl post-hoc must invalidate the digest stored in receipt.json."""
        gate = AdversaryGate(base_repo_root=tmp_path)
        cases = [{"case_id": "c1", "verdict": "PASS", "agreement": True}]
        claim = {
            "supports": "s",
            "does_not_support": "d",
            "narrowest_defensible_claim": "n",
            "next_test_needed": "t",
        }

        _, path_adversary, _, digests = gate.evaluate_and_persist(
            task_key="reverse_order_dda",
            run_id="reverse_order_dda_run",
            case_results=cases,
            claim_hygiene=claim,
        )

        dda_file = path_adversary / "dda_actions.jsonl"
        receipt_file = path_adversary / "receipt.json"
        receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))

        # Tamper dda_actions.jsonl
        lines = dda_file.read_text(encoding="utf-8").splitlines()
        rec0 = json.loads(lines[0])
        rec0["payload"]["action"] = "maliciously_altered_action"
        lines[0] = json.dumps(rec0)
        dda_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Verify binding is broken
        recomputed_sha = sha256_of_file(dda_file)
        assert recomputed_sha != receipt_data["dda_actions_sha256"]

    def test_altering_dda_actions_breaks_sequential_hash_chain(self, tmp_path: Path) -> None:
        """Altering any intermediate event in dda_actions.jsonl breaks the hash-chain tape.

        Counterexample (old tape): eight rows whose metadata were constants such as
        "verified": True. The tape now holds three rows of measured values.
        """
        gate = AdversaryGate(base_repo_root=tmp_path)
        cases = [{"case_id": "c1", "verdict": "PASS", "agreement": True}]
        claim = {
            "supports": "s",
            "does_not_support": "d",
            "narrowest_defensible_claim": "n",
            "next_test_needed": "t",
        }

        _, path_adversary, _, _ = gate.evaluate_and_persist(
            task_key="hash_chain_test",
            run_id="hash_chain_run",
            case_results=cases,
            claim_hygiene=claim,
        )

        dda_file = path_adversary / "dda_actions.jsonl"
        lines = dda_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 3  # intake, scoring, label: measured values only
        assert (
            json.loads(lines[2])["payload"]["metadata"]["label"]
            == TERMINAL_REFERENCE_SELF_CONSISTENT
        )

        # Verify uncorrupted tape integrity
        running_parent: str | None = None
        for line in lines:
            rec = json.loads(line)
            assert rec["parent_sha256"] == running_parent
            payload = rec["payload"]
            sorted_payload = {
                k: payload[k] for k in sorted(payload.keys(), key=lambda s: s.encode("utf-8"))
            }
            material = json.dumps(
                {
                    "payload": sorted_payload,
                    "parent_sha256": running_parent,
                    "sequence": rec["sequence"],
                },
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            assert hashlib.sha256(material).hexdigest() == rec["record_sha256"]
            running_parent = rec["record_sha256"]

        # Tamper step 2
        tampered_rec = json.loads(lines[2])
        tampered_rec["payload"]["metadata"]["tampered"] = True
        lines[2] = json.dumps(tampered_rec)

        # Verify that checking step 2's hash fails
        rec2 = json.loads(lines[2])
        p2 = rec2["payload"]
        sp2 = {k: p2[k] for k in sorted(p2.keys(), key=lambda s: s.encode("utf-8"))}
        mat2 = json.dumps(
            {"payload": sp2, "parent_sha256": rec2["parent_sha256"], "sequence": rec2["sequence"]},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        assert hashlib.sha256(mat2).hexdigest() != rec2["record_sha256"]

    def test_altering_summary_breaks_receipt_binding(self, tmp_path: Path) -> None:
        """Altering summary.json post-hoc must invalidate the digest stored in receipt.json."""
        gate = AdversaryGate(base_repo_root=tmp_path)
        cases = [{"case_id": "c1", "verdict": "PASS", "agreement": True}]
        claim = {
            "supports": "s",
            "does_not_support": "d",
            "narrowest_defensible_claim": "n",
            "next_test_needed": "t",
        }

        _, path_adversary, _, _ = gate.evaluate_and_persist(
            task_key="reverse_order_summary",
            run_id="reverse_order_summary_run",
            case_results=cases,
            claim_hygiene=claim,
        )

        summary_file = path_adversary / "summary.json"
        receipt_file = path_adversary / "receipt.json"
        receipt_data = json.loads(receipt_file.read_text(encoding="utf-8"))

        # Tamper summary.json
        summary_data = json.loads(summary_file.read_text(encoding="utf-8"))
        summary_data["total_cases_passed"] = 999
        summary_file.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")

        assert sha256_of_file(summary_file) != receipt_data["summary_sha256"]

    def test_scoring_receipt_binds_receipt_sha256(self, tmp_path: Path) -> None:
        """Phase 3 scoring receipt must bind receipt_sha256 of the Adversary bundle."""
        dest_challenge, runner = _setup_isolated_challenge(tmp_path)
        runner.run_phase1_judge_commitment()
        runner.run_phase2_freeze_record()
        scoring_receipt = runner.run_phase3_reveal_and_score(task_key="test_scoring_binds_receipt")

        adversary_info = scoring_receipt["adversary_reality_gate"]
        adversary_dir = Path(adversary_info["adversary_run_folder"])
        receipt_file = adversary_dir / "receipt.json"

        assert receipt_file.exists()
        actual_receipt_sha = sha256_of_file(receipt_file)
        assert actual_receipt_sha == adversary_info["receipt_sha256"]
