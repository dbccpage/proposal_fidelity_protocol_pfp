"""Paper Review Mining, Digestion, and Obstruction Extraction Pipeline.

Scrapes paper review directories and receipts under _ic/inr/omega_paper_reviews/,
extracts verified accomplishments and failure obstructions into typed records,
writes the canonical single JSON-L digest stream (paper_reviews_digest.jsonl),
and farms extracted defect obstructions into candidate antibodies in OEEIS.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from omega_engine_epistemic_immune_system.domain.pharmacy_seeder import PharmacySeeder
from omega_engine_epistemic_immune_system.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
)
from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route
from omega_engine_woland.domain.intelligence_digestion.paper_review_models import (
    AccomplishmentItem,
    AccomplishmentKind,
    FailureObstructionItem,
    ObstructionKind,
    PaperReviewDigestRecord,
    RecordType,
    ReviewStatus,
    ReviewSummary,
    Severity,
)

DIGEST_SCHEMA_VERSION = "omega.intelligence.paper-review-digest.v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_str(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _make_id(prefix: str, content: str) -> str:
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{h}"


class PaperReviewMiner:
    """Scrapes paper reviews, produces canonical typed JSON-L, and farms obstructions."""

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        if repo_root is not None:
            self.repo_root = Path(repo_root).resolve()
        else:
            self.repo_root = Path(__file__).resolve().parents[3]
        self.reviews_root = self.repo_root / canonical_intelligence_route("_intelligence/omega_paper_reviews")
        self.seeder = PharmacySeeder(
            self.repo_root,
            byte_writer=filesystem_byte_writer,
            byte_source=filesystem_catalog_bytes,
        )

    def scrape_swarm_receipt_file(self, file_path: Path) -> Optional[PaperReviewDigestRecord]:
        """Parses standalone swarm review receipt JSON files (e.g. omega.swarm_self_review.v1)."""
        try:
            d = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            return None

        paper_id = d.get("paper_id") or file_path.stem.replace("_swarm_receipt", "")
        raw_status = d.get("overall_status") or d.get("status") or "UNKNOWN"
        try:
            status = ReviewStatus(raw_status)
        except ValueError:
            status = ReviewStatus.UNKNOWN

        stages = d.get("stages")
        if stages is None:
            return None

        accomplished: List[AccomplishmentItem] = []
        failures: List[FailureObstructionItem] = []

        for s in stages:
            s_name = s.get("stage_name", f"stage_{s.get('stage_index', 0)}")
            s_status = s.get("status", "UNKNOWN")
            scope = f"{paper_id}:{s_name}"

            if s_status == "PASS":
                accomplished.append(
                    AccomplishmentItem(
                        item_id=_make_id("acc_stg", f"{file_path.name}:{s_name}"),
                        kind=AccomplishmentKind.STAGE_PASSED,
                        scope=scope,
                        details=f"Stage '{s_name}' executed cleanly with PASS status.",
                        evidence_ref=d.get("paper_path"),
                    )
                )
            elif s_status in ("BLOCKED", "FAIL"):
                failures.append(
                    FailureObstructionItem(
                        item_id=_make_id("obs_stg", f"{file_path.name}:{s_name}:{s_status}"),
                        kind=ObstructionKind.BLOCKED_STAGE if s_status == "BLOCKED" else ObstructionKind.FAILED_STAGE,
                        stage_or_phase=s_name,
                        severity=Severity.P0 if s_status == "BLOCKED" else Severity.P1,
                        description=f"Stage '{s_name}' failed to pass: marked as {s_status}.",
                        remediation_route=f"python -m omega_engine_research_papers.use_cases.paper_edition.cli rebuild --paper-id {paper_id}",
                    )
                )

            for err in s.get("errors", []):
                clean_err = _clean_str(err)
                gate_code = None
                code_m = re.match(r"^\[?([A-Z0-9_-]+)\]?\s*:", clean_err)
                if code_m:
                    gate_code = code_m.group(1)

                failures.append(
                    FailureObstructionItem(
                        item_id=_make_id("obs_err", f"{file_path.name}:{s_name}:{clean_err}"),
                        kind=ObstructionKind.BLOCKED_GATE if gate_code else ObstructionKind.GENERAL_OBSTRUCTION,
                        gate_code=gate_code,
                        stage_or_phase=s_name,
                        severity=Severity.P1,
                        description=clean_err,
                        negative_fixture=clean_err,
                    )
                )

            for warn in s.get("warnings", []):
                clean_w = _clean_str(warn)
                kind = ObstructionKind.GENERAL_OBSTRUCTION
                if "Restricted word" in clean_w:
                    kind = ObstructionKind.RESTRICTED_WORD
                elif "missing" in clean_w.lower():
                    kind = ObstructionKind.MISSING_SECTION
                elif "citation" in clean_w.lower() or "unfollowable" in clean_w.lower():
                    kind = ObstructionKind.CITATION_DEFECT

                failures.append(
                    FailureObstructionItem(
                        item_id=_make_id("obs_wrn", f"{file_path.name}:{s_name}:{clean_w}"),
                        kind=kind,
                        stage_or_phase=s_name,
                        severity=Severity.P2,
                        description=clean_w,
                        negative_fixture=clean_w,
                    )
                )

        raw_summary = d.get("summary", {})
        summary = ReviewSummary(
            stages_run=raw_summary.get("stages_run", len(stages)),
            stages_passed=raw_summary.get("stages_passed", sum(1 for s in stages if s.get("status") == "PASS")),
            stages_blocked=raw_summary.get("stages_blocked", sum(1 for s in stages if s.get("status") == "BLOCKED")),
            total_errors=raw_summary.get("total_errors", len([f for f in failures if f.severity in (Severity.P0, Severity.P1)])),
            total_warnings=raw_summary.get("total_warnings", len([f for f in failures if f.severity in (Severity.P2, Severity.P3)])),
            verdict=raw_summary.get("verdict", raw_status),
        )

        record_id = f"rev_rec_{file_path.stem}"
        return PaperReviewDigestRecord(
            record_id=record_id,
            review_source=file_path.relative_to(self.repo_root).as_posix(),
            paper_id=paper_id,
            record_type=RecordType.SWARM_REVIEW,
            status=status,
            timestamp_utc=d.get("timestamp_utc", _now()),
            accomplished=accomplished,
            failures=failures,
            summary=summary,
            artifacts_examined=[file_path.name],
        )

    def scrape_markdown_review_file(self, file_path: Path) -> Optional[PaperReviewDigestRecord]:
        """Parses standalone executive markdown republication review reports."""
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        paper_id = file_path.stem.replace("_republication_review", "").replace("_review", "")

        status = ReviewStatus.UNKNOWN
        if "PASSED" in text or "CLEARED" in text:
            status = ReviewStatus.PASS
        elif "BLOCKED" in text or "NOT READY" in text:
            status = ReviewStatus.BLOCKED
        elif "NEEDS_REVISION" in text or "REVISION REQUIRED" in text:
            status = ReviewStatus.NEEDS_REVISION

        accomplished: List[AccomplishmentItem] = []
        failures: List[FailureObstructionItem] = []

        # Extract findings from table or text
        for m in re.finditer(r"\|\s*\*\*([A-Z0-9_-]+)\*\*\s*\|\s*([^|]+)\|", text):
            gate, val = m.group(1), _clean_str(m.group(2))
            if "PASS" in val or "CLEARED" in val:
                accomplished.append(
                    AccomplishmentItem(
                        item_id=_make_id("acc_md_gate", f"{file_path.name}:{gate}:{val}"),
                        kind=AccomplishmentKind.GATE_CLEARED,
                        scope=f"{paper_id}:{gate}",
                        details=f"Gate {gate}: {val}",
                    )
                )
            elif any(w in val for w in ("FAIL", "BLOCKED", "NOT_VERIFIED", "OPEN", "MISSING")):
                failures.append(
                    FailureObstructionItem(
                        item_id=_make_id("obs_md_gate", f"{file_path.name}:{gate}:{val}"),
                        kind=ObstructionKind.BLOCKED_GATE,
                        gate_code=gate,
                        stage_or_phase="executive_review",
                        severity=Severity.P0 if "BLOCKED" in val or "FAIL" in val else Severity.P1,
                        description=f"Gate {gate} unsatisfied: {val}",
                        negative_fixture=val,
                    )
                )

        # Check explicitly missing or blocker lines
        for line in text.splitlines():
            s = line.strip()
            if s.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
                cleaned = re.sub(r"^[-*\d.]+\s*", "", s).strip()
                if any(k in cleaned.lower() for w in ["blocker", "missing", "unverified", "divergence", "contradictory"] if (k := w)):
                    if len(cleaned) > 15:
                        failures.append(
                            FailureObstructionItem(
                                item_id=_make_id("obs_md_line", f"{file_path.name}:{cleaned}"),
                                kind=ObstructionKind.PACKAGING_DEFECT if "package" in cleaned.lower() or "manifest" in cleaned.lower() else ObstructionKind.GENERAL_OBSTRUCTION,
                                stage_or_phase="packaging_and_integrity",
                                severity=Severity.P1,
                                description=cleaned,
                                negative_fixture=cleaned,
                            )
                        )

        # Check unit tests passed / coverage mentions
        coverage_m = re.search(r"(\d+)\s+passing unit tests.*?(\d+\.\d+)%\s+.*?coverage", text, re.IGNORECASE)
        if coverage_m:
            accomplished.append(
                AccomplishmentItem(
                    item_id=_make_id("acc_cov", f"{file_path.name}:coverage"),
                    kind=AccomplishmentKind.COVERAGE_ACHIEVED,
                    scope=f"{paper_id}:tests",
                    details=f"{coverage_m.group(1)} passing unit tests with {coverage_m.group(2)}% coverage",
                )
            )

        summary = ReviewSummary(
            stages_run=len(accomplished) + len(failures),
            stages_passed=len(accomplished),
            stages_blocked=len(failures),
            total_errors=len(failures),
            total_warnings=0,
            verdict="PASS" if status == ReviewStatus.PASS else "BLOCKED_GATES_PRESENT",
        )

        record_id = f"rev_rec_{file_path.stem}"
        return PaperReviewDigestRecord(
            record_id=record_id,
            review_source=file_path.relative_to(self.repo_root).as_posix(),
            paper_id=paper_id,
            record_type=RecordType.MONOGRAPH_AUDIT,
            status=status,
            timestamp_utc=_now(),
            accomplished=accomplished,
            failures=failures,
            summary=summary,
            artifacts_examined=[file_path.name],
        )

    def scrape_paper_subdirectory(self, paper_dir: Path, parent_run_name: str) -> Optional[PaperReviewDigestRecord]:
        """Parses a scoped paper directory within a multi-paper review run."""
        paper_id = paper_dir.name
        run_all_receipt = paper_dir / "run_all_receipt.json"
        if not run_all_receipt.exists():
            run_all_receipt = paper_dir / "run_all.json"

        gate_receipt = paper_dir / "republication_gate_receipt.json"
        if not gate_receipt.exists():
            gate_receipt = paper_dir / "republication.json"

        swarm_receipt = paper_dir / "swarm_deliberation_receipt.json"
        stages_receipt = paper_dir / "stages_receipt.json"

        if not any(f.exists() for f in (run_all_receipt, gate_receipt, swarm_receipt, stages_receipt)):
            return None

        status = ReviewStatus.UNKNOWN
        accomplished: List[AccomplishmentItem] = []
        failures: List[FailureObstructionItem] = []
        stages_run = 0
        stages_passed = 0
        stages_blocked = 0

        # 1. Parse run_all_receipt
        if run_all_receipt.exists():
            try:
                data = json.loads(run_all_receipt.read_text(encoding="utf-8", errors="ignore"))
                raw_st = data.get("overall_status") or "UNKNOWN"
                if raw_st in ReviewStatus.__members__:
                    status = ReviewStatus(raw_st)

                sum_d = data.get("summary", {})
                stages_run += sum_d.get("stages_run", 0)
                stages_passed += sum_d.get("stages_passed", 0)
                stages_blocked += sum_d.get("stages_blocked", 0)

                for stg in data.get("stages", []):
                    s_name = stg.get("stage_name", "stage")
                    st = stg.get("status")
                    if st == "PASS":
                        accomplished.append(
                            AccomplishmentItem(
                                item_id=_make_id("acc_sub", f"{paper_dir.name}:{s_name}"),
                                kind=AccomplishmentKind.STAGE_PASSED,
                                scope=f"{paper_id}:{s_name}",
                                details=f"Stage '{s_name}' executed cleanly.",
                            )
                        )
                    elif st in ("BLOCKED", "FAIL"):
                        failures.append(
                            FailureObstructionItem(
                                item_id=_make_id("obs_sub", f"{paper_dir.name}:{s_name}:{st}"),
                                kind=ObstructionKind.BLOCKED_STAGE if st == "BLOCKED" else ObstructionKind.FAILED_STAGE,
                                stage_or_phase=s_name,
                                severity=Severity.P0 if st == "BLOCKED" else Severity.P1,
                                description=f"Stage '{s_name}' failed with status {st}.",
                            )
                        )
                    for err in stg.get("errors", []):
                        failures.append(
                            FailureObstructionItem(
                                item_id=_make_id("obs_sub_err", f"{paper_dir.name}:{s_name}:{err}"),
                                kind=ObstructionKind.GENERAL_OBSTRUCTION,
                                stage_or_phase=s_name,
                                severity=Severity.P1,
                                description=_clean_str(err),
                                negative_fixture=err,
                            )
                        )
            except Exception:
                pass

        # 2. Parse republication_gate_receipt
        if gate_receipt.exists():
            try:
                gate_data = json.loads(gate_receipt.read_text(encoding="utf-8", errors="ignore"))
                g_status = gate_data.get("status")
                if g_status == "BLOCKED":
                    status = ReviewStatus.BLOCKED

                for err in gate_data.get("errors", []):
                    gate_code = None
                    code_m = re.match(r"^([A-Z0-9]+)\s+NOT_VERIFIED:\s*(.*)", err)
                    if code_m:
                        gate_code = code_m.group(1)
                        desc = code_m.group(2)
                    else:
                        desc = err

                    failures.append(
                        FailureObstructionItem(
                            item_id=_make_id("obs_gate", f"{paper_dir.name}:{gate_code}:{desc}"),
                            kind=ObstructionKind.BLOCKED_GATE if gate_code else ObstructionKind.GENERAL_OBSTRUCTION,
                            gate_code=gate_code,
                            stage_or_phase="republication_gate",
                            severity=Severity.P1,
                            description=f"Republication gate requirement unsatisfied: {desc}",
                            negative_fixture=err,
                            remediation_route=f"python -m omega_engine_research_papers.use_cases.paper_edition.cli rebuild --paper-path {paper_id}",
                        )
                    )
            except Exception:
                pass

        # 3. Parse stages_receipt (e.g. 20261005_lggr_v)
        if stages_receipt.exists():
            try:
                stg_data = json.loads(stages_receipt.read_text(encoding="utf-8", errors="ignore"))
                for s_key, s_val in stg_data.items():
                    if isinstance(s_val, dict):
                        st = s_val.get("status")
                        stages_run += 1
                        if st == "PASS":
                            stages_passed += 1
                            accomplished.append(
                                AccomplishmentItem(
                                    item_id=_make_id("acc_lggr", f"{paper_dir.name}:{s_key}"),
                                    kind=AccomplishmentKind.STAGE_PASSED,
                                    scope=f"{paper_id}:{s_key}",
                                    details=f"Stage {s_key} verified cleanly.",
                                )
                            )
                        else:
                            stages_blocked += 1
                            failures.append(
                                FailureObstructionItem(
                                    item_id=_make_id("obs_lggr", f"{paper_dir.name}:{s_key}:{st}"),
                                    kind=ObstructionKind.BLOCKED_STAGE,
                                    stage_or_phase=s_key,
                                    severity=Severity.P1,
                                    description=f"Stage {s_key} blocked/failed with status {st}.",
                                    negative_fixture=json.dumps(s_val),
                                )
                            )
            except Exception:
                pass

        # 4. Swarm deliberation receipt
        if swarm_receipt.exists():
            try:
                sw_data = json.loads(swarm_receipt.read_text(encoding="utf-8", errors="ignore"))
                sw_status = sw_data.get("status") or sw_data.get("overall_status")
                if sw_status:
                    if sw_status == "CONSENSUS_REACHED":
                        accomplished.append(
                            AccomplishmentItem(
                                item_id=_make_id("acc_sw", f"{paper_dir.name}:consensus"),
                                kind=AccomplishmentKind.GATE_CLEARED,
                                scope=f"{paper_id}:deliberation",
                                details="Swarm deliberation reached formal consensus.",
                            )
                        )
            except Exception:
                pass

        summary = ReviewSummary(
            stages_run=stages_run or (len(accomplished) + len(failures)),
            stages_passed=stages_passed or len(accomplished),
            stages_blocked=stages_blocked or len(failures),
            total_errors=len(failures),
            total_warnings=0,
            verdict="PASS" if status == ReviewStatus.PASS else ("BLOCKED" if status == ReviewStatus.BLOCKED else "EVALUATED"),
        )

        record_id = f"rev_rec_{parent_run_name}_{paper_id}"
        return PaperReviewDigestRecord(
            record_id=record_id,
            review_source=paper_dir.relative_to(self.repo_root).as_posix(),
            paper_id=paper_id,
            record_type=RecordType.GATE_EXECUTION,
            status=ReviewStatus.BLOCKED if failures else status,
            timestamp_utc=_now(),
            accomplished=accomplished,
            failures=failures,
            summary=summary,
            artifacts_examined=[p.name for p in paper_dir.glob("*.json")],
        )

    def scrape_run_directory(self, run_dir: Path) -> List[PaperReviewDigestRecord]:
        """Scrapes an entire review run directory, which may contain single or multiple papers."""
        records: List[PaperReviewDigestRecord] = []

        # Check for child paper directories
        child_dirs = [d for d in sorted(run_dir.iterdir()) if d.is_dir()]
        for cdir in child_dirs:
            rec = self.scrape_paper_subdirectory(cdir, run_dir.name)
            if rec:
                records.append(rec)

        # If child directories produced records, return them
        if records:
            return records

        # Otherwise, treat the run_dir itself as a single review object
        single_rec = self.scrape_paper_subdirectory(run_dir, run_dir.name)
        if single_rec:
            records.append(single_rec)
            return records

        # Special cases: certificate / bounded continuation directories (e.g. 2026-10-06_glm_d, 2026-10-06_pr555_followup)
        cert_receipt = run_dir / "independent_certificate_receipt.json"
        if not cert_receipt.exists():
            cert_receipt = run_dir / "python_certificate_build_receipt.json"

        if cert_receipt.exists():
            try:
                cd = json.loads(cert_receipt.read_text(encoding="utf-8", errors="ignore"))
                if cd.get("status", cd.get("overall_status")) != "PASS":
                    raise ValueError("certificate receipt has no explicit passing disposition")
                checks = cd.get("checks", {})
                accomplished = [
                    AccomplishmentItem(
                        item_id=_make_id("acc_cert", f"{run_dir.name}:certificate"),
                        kind=AccomplishmentKind.THEOREMS_VERIFIED,
                        scope=f"{run_dir.name}:continuation",
                        details=f"Native certificate verified: {checks.get('decoder_replays', 'verified')} decoder replays, {checks.get('states', 'complete')} states.",
                        evidence_ref=cd.get("certificate_sha256"),
                    )
                ]
                summary = ReviewSummary(
                    stages_run=1,
                    stages_passed=1,
                    stages_blocked=0,
                    total_errors=0,
                    total_warnings=0,
                    verdict="CERTIFICATE_VERIFIED",
                )
                records.append(
                    PaperReviewDigestRecord(
                        record_id=f"rev_rec_{run_dir.name}",
                        review_source=run_dir.relative_to(self.repo_root).as_posix(),
                        paper_id=run_dir.name,
                        record_type=RecordType.FUTURE_CERTIFICATE,
                        status=ReviewStatus.PASS,
                        timestamp_utc=_now(),
                        accomplished=accomplished,
                        failures=[],
                        summary=summary,
                        artifacts_examined=[p.name for p in run_dir.glob("*.json")],
                    )
                )
                return records
            except Exception:
                pass

        # OMC reports only (e.g. 2026-10-06_wdp_r1)
        omc_reports = list(run_dir.glob("omc_report*.jsonl"))
        if omc_reports:
            accomplished = []
            failures = []
            for omc in omc_reports:
                for line in omc.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if not line.strip():
                        continue
                    try:
                        ld = json.loads(line)
                        cid = ld.get("check_id") or ld.get("name") or "check"
                        st = ld.get("status")
                        if st == "PASS":
                            accomplished.append(
                                AccomplishmentItem(
                                    item_id=_make_id("acc_omc", f"{run_dir.name}:{cid}"),
                                    kind=AccomplishmentKind.GATE_CLEARED,
                                    scope=f"{run_dir.name}:{cid}",
                                    details=f"OMC gate check passed: {cid}",
                                )
                            )
                        else:
                            failures.append(
                                FailureObstructionItem(
                                    item_id=_make_id("obs_omc", f"{run_dir.name}:{cid}:{st}"),
                                    kind=ObstructionKind.BLOCKED_GATE,
                                    gate_code=cid,
                                    stage_or_phase="omc_operad_report",
                                    severity=Severity.P1,
                                    description=ld.get("message") or ld.get("defect") or f"Gate {cid} failed",
                                    negative_fixture=json.dumps(ld),
                                )
                            )
                    except Exception:
                        pass
            summary = ReviewSummary(
                stages_run=len(accomplished) + len(failures),
                stages_passed=len(accomplished),
                stages_blocked=len(failures),
                total_errors=len(failures),
                total_warnings=0,
                verdict="FAIL" if failures else "PASS",
            )
            records.append(
                PaperReviewDigestRecord(
                    record_id=f"rev_rec_{run_dir.name}",
                    review_source=run_dir.relative_to(self.repo_root).as_posix(),
                    paper_id=run_dir.name,
                    record_type=RecordType.GATE_EXECUTION,
                    status=ReviewStatus.FAIL if failures else ReviewStatus.PASS,
                    timestamp_utc=_now(),
                    accomplished=accomplished,
                    failures=failures,
                    summary=summary,
                    artifacts_examined=[p.name for p in run_dir.glob("*.jsonl")],
                )
            )
            return records

        return records

    def scrape_all(self, source_dir: Optional[Path] = None) -> List[PaperReviewDigestRecord]:
        """Scrapes all top-level review directories and files."""
        root = source_dir if source_dir is not None else self.reviews_root
        all_records: List[PaperReviewDigestRecord] = []

        if not root.is_dir():
            return all_records

        # 1. Scrape top-level JSON receipts
        for jf in sorted(root.glob("*_receipt.json")):
            rec = self.scrape_swarm_receipt_file(jf)
            if rec:
                all_records.append(rec)

        # 2. Scrape top-level Markdown republication reviews
        for mf in sorted(root.glob("*_review.md")):
            rec = self.scrape_markdown_review_file(mf)
            if rec:
                all_records.append(rec)

        # 3. Scrape run directories
        for entry in sorted(root.iterdir()):
            if entry.is_dir() and entry.name != "data_types":
                recs = self.scrape_run_directory(entry)
                all_records.extend(recs)

        # Deduplicate records by record_id
        unique: Dict[str, PaperReviewDigestRecord] = {}
        for r in all_records:
            unique[r.record_id] = r

        return list(unique.values())

    def write_digest_jsonl(self, records: List[PaperReviewDigestRecord], output_path: Path) -> int:
        """Serializes records into a single JSON-L file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [r.to_json_line() for r in records]
        content = "\n".join(lines) + ("\n" if lines else "")
        output_path.write_text(content, encoding="utf-8")
        return len(lines)

    def farm_obstructions(
        self, records: List[PaperReviewDigestRecord], batch_limit: int = 5
    ) -> Dict[str, Any]:
        """Collects unique failure obstructions and farms candidate antibodies into OEEIS."""
        total_farmed = 0
        total_preserved = 0
        total_refused = 0

        for r in records:
            if not r.failures:
                continue

            # Select distinct, substantive defect patterns
            defect_patterns = []
            for f in r.failures:
                # Format a clean, informative defect description
                desc = f.description.strip()
                if len(desc) > 15 and not desc.startswith("{") and not desc.startswith("Output:"):
                    defect_patterns.append(desc)

            # Limit per record to prevent flood
            distinct_defects = sorted(dict.fromkeys(defect_patterns))[:batch_limit]
            if distinct_defects:
                farmed = self.seeder.farm_antibodies_from_defects(
                    distinct_defects,
                    run_id=r.record_id,
                    task_id=f"paper_review:{r.paper_id}",
                )
                total_farmed += len(farmed)
                total_preserved += len(self.seeder.preserved_judged)
                total_refused += len(self.seeder.refused_retired)

        return {
            "farmed_antibodies_count": total_farmed,
            "preserved_judged_count": total_preserved,
            "refused_retired_count": total_refused,
        }

    def ingest_single_receipt(
        self,
        receipt_path: Path,
        output_jsonl: Optional[Path] = None,
        farm: bool = True,
    ) -> Dict[str, Any]:
        """Ingests a single review receipt directly, appends/updates digest JSON-L, and farms defects."""
        dest = output_jsonl or (self.reviews_root / "paper_reviews_digest.jsonl")
        receipt_p = Path(receipt_path).resolve()
        if not receipt_p.is_file():
            return {
                "status": "FAIL",
                "reason": f"Receipt file not found at {receipt_p}",
            }

        rec: Optional[PaperReviewDigestRecord] = None
        if receipt_p.suffix == ".json":
            rec = self.scrape_swarm_receipt_file(receipt_p)
            if not rec:
                rec = self.scrape_paper_subdirectory(receipt_p.parent, receipt_p.parent.name)
            if not rec:
                # Direct JSON receipt fallback
                try:
                    d = json.loads(receipt_p.read_text(encoding="utf-8", errors="ignore"))
                    pid = d.get("paper_id") or receipt_p.stem
                    raw_st = d.get("status") or d.get("overall_status") or "UNKNOWN"
                    try:
                        st = ReviewStatus(raw_st)
                    except ValueError:
                        st = ReviewStatus.UNKNOWN

                    acc = []
                    fail = []
                    for s in d.get("stages", []):
                        s_name = s.get("stage_name", "stage")
                        if s.get("status") == "PASS":
                            acc.append(
                                AccomplishmentItem(
                                    item_id=_make_id("acc_stg", f"{receipt_p.name}:{s_name}"),
                                    kind=AccomplishmentKind.STAGE_PASSED,
                                    scope=f"{pid}:{s_name}",
                                    details=f"Stage {s_name} passed cleanly.",
                                )
                            )
                        else:
                            fail.append(
                                FailureObstructionItem(
                                    item_id=_make_id("obs_stg", f"{receipt_p.name}:{s_name}:{s.get('status')}"),
                                    kind=ObstructionKind.BLOCKED_STAGE,
                                    stage_or_phase=s_name,
                                    severity=Severity.P1,
                                    description=f"Stage {s_name} blocked/failed.",
                                )
                            )
                        for err in s.get("errors", []):
                            fail.append(
                                FailureObstructionItem(
                                    item_id=_make_id("obs_err", f"{receipt_p.name}:{s_name}:{err}"),
                                    kind=ObstructionKind.GENERAL_OBSTRUCTION,
                                    stage_or_phase=s_name,
                                    severity=Severity.P1,
                                    description=_clean_str(err),
                                    negative_fixture=err,
                                )
                            )
                    for err in d.get("errors", []):
                        clean_err = _clean_str(err)
                        gate_code = None
                        code_m = re.match(r"^\[?([A-Z0-9_-]+)\]?(?:\s+[A-Z_]+)?\s*:", clean_err)
                        if code_m:
                            gate_code = code_m.group(1)
                        fail.append(
                            FailureObstructionItem(
                                item_id=_make_id("obs_top_err", f"{receipt_p.name}:{err}"),
                                kind=ObstructionKind.BLOCKED_GATE if gate_code else ObstructionKind.GENERAL_OBSTRUCTION,
                                gate_code=gate_code,
                                stage_or_phase=d.get("stage_name", "review"),
                                severity=Severity.P1,
                                description=clean_err,
                                negative_fixture=err,
                            )
                        )
                    for warn in d.get("warnings", []):
                        clean_w = _clean_str(warn)
                        fail.append(
                            FailureObstructionItem(
                                item_id=_make_id("obs_top_wrn", f"{receipt_p.name}:{warn}"),
                                kind=ObstructionKind.GENERAL_OBSTRUCTION,
                                stage_or_phase=d.get("stage_name", "review"),
                                severity=Severity.P2,
                                description=clean_w,
                                negative_fixture=warn,
                            )
                        )
                    if d.get("stage_name") and (st == ReviewStatus.PASS or (raw_st == "PASS" and not fail)):
                        acc.append(
                            AccomplishmentItem(
                                item_id=_make_id("acc_stg", f"{receipt_p.name}:{d.get('stage_name')}"),
                                kind=AccomplishmentKind.STAGE_PASSED,
                                scope=f"{pid}:{d.get('stage_name')}",
                                details=f"Stage '{d.get('stage_name')}' passed cleanly.",
                            )
                        )

                    sum_d = d.get("summary", {})
                    rec = PaperReviewDigestRecord(
                        record_id=f"rev_rec_{receipt_p.stem}",
                        review_source=receipt_p.relative_to(self.repo_root).as_posix() if receipt_p.is_relative_to(self.repo_root) else receipt_p.name,
                        paper_id=pid,
                        record_type=RecordType.GATE_EXECUTION,
                        status=st if st != ReviewStatus.UNKNOWN else (ReviewStatus.PASS if not fail else ReviewStatus.BLOCKED),
                        timestamp_utc=d.get("timestamp_utc", _now()),
                        accomplished=acc,
                        failures=fail,
                        summary=ReviewSummary(
                            stages_run=sum_d.get("stages_run", len(acc) + len(fail)),
                            stages_passed=sum_d.get("stages_passed", len(acc)),
                            stages_blocked=sum_d.get("stages_blocked", len(fail)),
                            total_errors=sum_d.get("total_errors", len(fail)),
                            total_warnings=sum_d.get("total_warnings", 0),
                            verdict=sum_d.get("verdict", raw_st),
                        ),
                        artifacts_examined=[receipt_p.name],
                    )
                except Exception:
                    pass
        elif receipt_p.suffix == ".md":
            rec = self.scrape_markdown_review_file(receipt_p)

        if not rec:
            return {
                "status": "FAIL",
                "reason": f"Unable to parse review receipt from {receipt_p.name}",
            }

        # Update or append to JSON-L
        dest.parent.mkdir(parents=True, exist_ok=True)
        existing_records: Dict[str, PaperReviewDigestRecord] = {}
        if dest.is_file():
            for line in dest.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        r = PaperReviewDigestRecord.from_json_line(line)
                        existing_records[r.record_id] = r
                    except Exception:
                        pass

        existing_records[rec.record_id] = rec
        self.write_digest_jsonl(list(existing_records.values()), dest)

        # Farm candidate antibodies
        antibody_stats: Dict[str, Any] = {}
        if farm:
            antibody_stats = self.farm_obstructions([rec])

        return {
            "status": "PASS",
            "record_id": rec.record_id,
            "paper_id": rec.paper_id,
            "review_status": rec.status.value,
            "accomplishments_count": len(rec.accomplished),
            "failures_count": len(rec.failures),
            "output_jsonl": dest.relative_to(self.repo_root).as_posix() if dest.is_relative_to(self.repo_root) else str(dest),
            "antibody_farming": antibody_stats,
        }

    def run_pipeline(
        self,
        source_dir: Optional[Path] = None,
        output_jsonl: Optional[Path] = None,
        farm: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """End-to-end pipeline: scrape, write digest JSON-L, and farm candidate antibodies."""
        src = source_dir or self.reviews_root
        dest = output_jsonl or (self.reviews_root / "paper_reviews_digest.jsonl")

        records = self.scrape_all(src)
        total_accomplishments = sum(len(r.accomplished) for r in records)
        total_failures = sum(len(r.failures) for r in records)

        antibody_stats: Dict[str, Any] = {}
        if farm and not dry_run:
            antibody_stats = self.farm_obstructions(records)

        lines_written = 0
        if not dry_run:
            lines_written = self.write_digest_jsonl(records, dest)

        return {
            "schema_version": DIGEST_SCHEMA_VERSION,
            "authority_effect": "None",
            "executed_at_utc": _now(),
            "dry_run": dry_run,
            "total_records": len(records),
            "total_accomplishments": total_accomplishments,
            "total_failures": total_failures,
            "lines_written": lines_written,
            "output_jsonl": dest.relative_to(self.repo_root).as_posix() if not dry_run else None,
            "antibody_farming": antibody_stats,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Omega Engine Paper Review Mining & Digestion Tool")
    parser.add_argument("--repo-root", type=Path, default=None, help="Repository root path")
    parser.add_argument("--source-dir", type=Path, default=None, help="Source paper reviews directory")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON-L file path")
    parser.add_argument("--farm", action="store_true", help="Farm candidate antibodies into OEEIS")
    parser.add_argument("--dry-run", action="store_true", help="Perform extraction without writing to disk")
    args = parser.parse_args()

    miner = PaperReviewMiner(args.repo_root)
    result = miner.run_pipeline(
        source_dir=args.source_dir,
        output_jsonl=args.output,
        farm=args.farm,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
