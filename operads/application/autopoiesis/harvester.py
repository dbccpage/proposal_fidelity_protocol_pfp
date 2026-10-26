"""Autopoietic Harvester Use Case.

Implements the core engine that enables the Omega Engine to "eat its own output":
- Ingests ephemeral teamwork directories and antibody files into immutable CAS storage.
- Mines recurring workflows into candidate skill proposals.
- Mines discovered failure modes into formal antibody definitions.
- Seals snapshots with Merkle roots and emits verified receipts.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import uuid4

from omega_engine_operads.domain.autopoiesis.entities import (
    HarvestReceipt,
    HarvestRecord,
    HarvestSnapshot,
    MinedAntibody,
    MinedSkillProposal,
)
from omega_engine_operads.domain.autopoiesis.ports import (
    ArtifactLocation,
    HarvestSourcePort,
    HarvestVaultPort,
    PharmacyCatalogPort,
    SkillsRegisterPort,
)


class AutopoieticHarvester:
    """Orchestrates intake, CAS archiving, pattern mining, and catalog updating."""

    def __init__(
        self,
        vault: HarvestVaultPort,
        pharmacy: PharmacyCatalogPort,
        skills_register: SkillsRegisterPort,
        *,
        source: HarvestSourcePort,
    ) -> None:
        self.vault = vault
        self.pharmacy = pharmacy
        self.skills_register = skills_register
        self.source = source

    def harvest_directory(
        self,
        source_dir: ArtifactLocation | str,
        source_name: str,
        *,
        snapshot_id: str | None = None,
    ) -> tuple[HarvestSnapshot, int]:
        """Ingests all files from source_dir into CAS storage and returns the sealed snapshot."""
        sdir = self.source.resolve(source_dir)

        ts = datetime.now(timezone.utc).isoformat()
        sid = snapshot_id or f"snap_{source_name}_{uuid4().hex}"

        records: list[HarvestRecord] = []
        new_cas_objects = 0

        for file in self.source.read_directory(sdir):
            content = file.content
            sha = hashlib.sha256(content).hexdigest()
            byte_size = len(content)
            rel_path = file.relative_path
            ftype = file.file_type

            written = self.vault.put_file(content, sha)
            if written:
                new_cas_objects += 1

            rec = HarvestRecord(
                relative_path=rel_path,
                sha256=sha,
                byte_size=byte_size,
                file_type=ftype,
            )
            records.append(rec)

        snapshot = HarvestSnapshot.create(
            snapshot_id=sid,
            source_name=source_name,
            records=records,
            created_at=ts,
        )
        self.vault.save_snapshot(snapshot)
        return snapshot, new_cas_objects

    def mine_teamwork(
        self,
        teamwork_dir: ArtifactLocation | str,
        snapshot: HarvestSnapshot,
    ) -> tuple[list[MinedSkillProposal], list[MinedAntibody]]:
        """Mines candidate skills and antibodies from teamwork artifacts."""
        skills: list[MinedSkillProposal] = []
        antibodies: list[MinedAntibody] = []

        # 1. Mine Refusal Bypass Verification Pattern
        refusal_bypass_files = [
            r.relative_path
            for r in snapshot.records
            if "refusal_bypass" in r.relative_path or "verify_refusal" in r.relative_path
        ]
        if refusal_bypass_files:
            skills.append(
                MinedSkillProposal(
                    skill_id="techne-adversarial-refusal-bypass-auditor",
                    title="Adversarial Refusal Bypass Auditor",
                    lead_council="L3_logos_techne",
                    scope="Generates hostile permutations of refusal codes and keys (refusal, refusal_code, empty, bogus) across evaluator suites asserting strictly 0 false-pass admissions.",
                    origin_agent_role="challenger",
                    confidence="HIGH",
                    source_artifacts=refusal_bypass_files,
                    suggested_checks=[
                        "verify_closed_refusal_code_rejection",
                        "verify_malformed_key_rejection",
                        "assert_zero_false_positive_rate",
                    ],
                )
            )
            antibodies.append(
                MinedAntibody(
                    antibody_id="ab_adversarial_refusal_bypass_leakage",
                    failure_class="evaluator:adversarial_refusal_bypass_leakage",
                    target_pattern="evaluator:adversarial_refusal_bypass_leakage",
                    constraint_type="RejectMalformedOrFakeRefusals",
                    operatorizability="repairable",
                    action="refuse",
                    severity="P0",
                    description="Refuses evaluators where dummy refusal codes or unexpected refusal keys evaluate to PASS.",
                    negative_fixture="Submitting {'refusal': 'INVALID_CODE'} yields {'verdict': 'PASS'}.",
                    positive_fixture="Submitting any ungrounded refusal payload yields {'verdict': 'REFUSE'}.",
                    source_file=refusal_bypass_files[0],
                    evidence_sha256=next(
                        r.sha256
                        for r in snapshot.records
                        if r.relative_path == refusal_bypass_files[0]
                    ),
                )
            )

        # 2. Mine Anti-Mock & Empty Method AST Checker Pattern
        mock_checker_files = [
            r.relative_path
            for r in snapshot.records
            if "check_facades" in r.relative_path or "anti_mock" in r.relative_path
        ]
        if mock_checker_files:
            skills.append(
                MinedSkillProposal(
                    skill_id="techne-ast-anti-mock-and-facade-auditor",
                    title="AST Anti-Mock and Facade Auditor",
                    lead_council="L3_logos_techne",
                    scope="AST static analysis scanner inspecting test files for MagicMock/patch calls and dummy stub functions (pass, return True) that masquerade as trait implementations.",
                    origin_agent_role="victory_auditor",
                    confidence="HIGH",
                    source_artifacts=mock_checker_files,
                    suggested_checks=[
                        "ast_scan_mock_imports",
                        "ast_detect_empty_pass_bodies",
                        "ast_detect_constant_return_stubs",
                    ],
                )
            )
            antibodies.append(
                MinedAntibody(
                    antibody_id="ab_vacuous_test_mock_facade",
                    failure_class="testing:vacuous_test_mock_facade",
                    target_pattern="testing:vacuous_test_mock_facade",
                    constraint_type="ForbidDummyPassAndMocksInPureTraits",
                    operatorizability="repairable",
                    action="refuse",
                    severity="P0",
                    description="Refuses tests whose target methods only return static constants or contain bare pass statements without behavioral computation.",
                    negative_fixture="def compute_invariant(self): pass",
                    positive_fixture="def compute_invariant(self): return verify_exact_homology(self)",
                    source_file=mock_checker_files[0],
                    evidence_sha256=next(
                        r.sha256
                        for r in snapshot.records
                        if r.relative_path == mock_checker_files[0]
                    ),
                )
            )

        # 3. Mine Commit-Reveal Manifest Resealer Pattern
        manifest_reseal_files = [
            r.relative_path
            for r in snapshot.records
            if "manifest" in r.relative_path
            and ("resync" in r.relative_path or "reseal" in r.relative_path)
        ]
        if manifest_reseal_files:
            skills.append(
                MinedSkillProposal(
                    skill_id="techne-commit-reveal-manifest-resealer",
                    title="Commit-Reveal Manifest Resealer",
                    lead_council="L3_logos_techne",
                    scope="Simulates commit-reveal cycles across test and judge manifests, recomputes Merkle digests from on-disk case files, and generates lossless synchronization diffs.",
                    origin_agent_role="explorer",
                    confidence="HIGH",
                    source_artifacts=manifest_reseal_files,
                    suggested_checks=[
                        "simulate_commit_reveal",
                        "recompute_merkle_roots",
                        "generate_resync_diff",
                    ],
                )
            )
            antibodies.append(
                MinedAntibody(
                    antibody_id="ab_manifest_commit_reveal_digest_divergence",
                    failure_class="manifest:commit_reveal_digest_divergence",
                    target_pattern="manifest:commit_reveal_digest_divergence",
                    constraint_type="AssertStrictOnDiskCommitmentParity",
                    operatorizability="repairable",
                    action="refuse",
                    severity="P0",
                    description="Refuses test manifests whose sealed case commitments differ from byte digests of actual test files on disk.",
                    negative_fixture="Manifest declares digest 0xABC but on-disk file yields 0xDEF.",
                    positive_fixture="Every manifest entry strictly equals hashlib.sha256(file.bytes).hexdigest().",
                    source_file=manifest_reseal_files[0],
                    evidence_sha256=next(
                        r.sha256
                        for r in snapshot.records
                        if r.relative_path == manifest_reseal_files[0]
                    ),
                )
            )

        # 4. Mine Forensic Pedagogical Triple Parity Pattern
        pedagogy_audit_files = [
            r.relative_path
            for r in snapshot.records
            if "auditor_1" in r.relative_path and "handoff.md" in r.relative_path
        ]
        if pedagogy_audit_files:
            skills.append(
                MinedSkillProposal(
                    skill_id="techne-forensic-pedagogical-parity-auditor",
                    title="Forensic Pedagogical Parity Auditor",
                    lead_council="L3_nous_panepistimion",
                    scope="Validates byte-level triple parity across lesson prose, runnable Jupyter notebooks, and video scripts, ensuring zero shape failures and zero empty learning checks.",
                    origin_agent_role="auditor",
                    confidence="HIGH",
                    source_artifacts=pedagogy_audit_files,
                    suggested_checks=[
                        "verify_lesson_notebook_prose_bijection",
                        "verify_zero_empty_stubs",
                        "verify_learning_check_solvability",
                    ],
                )
            )

        return skills, antibodies

    def harvest_all(
        self,
        teamwork_dir: ArtifactLocation | str,
        antibodies_dir: ArtifactLocation | str,
    ) -> HarvestReceipt:
        """Executes full harvest across teamwork and antibodies directories."""
        tdir = self.source.resolve(teamwork_dir)
        adir = self.source.resolve(antibodies_dir)

        ts = datetime.now(timezone.utc).isoformat()
        total_cas_objects = 0
        merkle_roots: dict[str, str] = {}

        # 1. Harvest Teamwork directory
        teamwork_snapshot, tw_cas = self.harvest_directory(tdir, "teamwork")
        total_cas_objects += tw_cas
        merkle_roots["teamwork"] = teamwork_snapshot.merkle_root

        # 2. Mine Skills & Antibodies from Teamwork
        mined_skills, mined_abs = self.mine_teamwork(tdir, teamwork_snapshot)

        # 3. Harvest Antibodies directory
        antibodies_snapshot, ab_cas = self.harvest_directory(adir, "antibodies")
        total_cas_objects += ab_cas
        merkle_roots["antibodies"] = antibodies_snapshot.merkle_root

        # 4. Ingest and merge antibodies into Pharmacy
        self.pharmacy.merge_antibodies(mined_abs)

        # 5. Append candidate skills to Register
        self.skills_register.append_skill_proposals(mined_skills)

        # 6. Collate and emit Receipt
        receipt = HarvestReceipt(
            receipt_id=f"harvest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            timestamp=ts,
            teamwork_files_preserved=len(teamwork_snapshot.records),
            antibodies_cataloged=len(antibodies_snapshot.records),
            skills_mined=len(mined_skills),
            antibodies_mined=len(mined_abs),
            cas_objects_written=total_cas_objects,
            merkle_roots=merkle_roots,
            authority_effect="None",
        )
        return receipt

    def pre_clean_teamwork(
        self,
        teamwork_dir: ArtifactLocation | str,
        antibodies_dir: ArtifactLocation | str,
        *,
        clear_after: bool = False,
    ) -> tuple[HarvestReceipt, int]:
        """Pre-clean gate: ingests and verifies all artifacts before clearing or initializing.

        Asserts bit-for-bit CAS verification before permitting any directory clearing.
        Returns (HarvestReceipt, cleared_count).
        """
        tdir = self.source.resolve(teamwork_dir)
        adir = self.source.resolve(antibodies_dir)

        receipt = self.harvest_all(tdir, adir)

        # Strict CAS verification gate
        teamwork_snapshot, _ = self.harvest_directory(tdir, "teamwork_verify_gate")
        for rec in teamwork_snapshot.records:
            stored = self.vault.get_file(rec.sha256)
            if (
                stored is None
                or len(stored) != rec.byte_size
                or hashlib.sha256(stored).hexdigest() != rec.sha256
            ):
                raise RuntimeError(
                    f"PRE_CLEAN_REFUSAL: File '{rec.relative_path}' failed CAS verification. Ingestion incomplete; clearing refused."
                )

        cleared_count = 0
        if clear_after:
            expected = {record.relative_path: record.sha256 for record in teamwork_snapshot.records}
            cleared_count = self.source.clear_verified(tdir, expected)

        return receipt, cleared_count
