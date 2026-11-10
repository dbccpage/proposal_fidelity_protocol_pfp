"""Record independent source review and bounded non-destructive retirement probes."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "dag/pilot_triage"

def sha(raw): return hashlib.sha256(raw).hexdigest()
def read(name): return json.loads((HERE / name).read_text(encoding="utf-8"))
def evidence(name, start=None, end=None):
    raw = (HERE / name).read_bytes()
    lines = raw.count(b"\n") + int(bool(raw) and not raw.endswith(b"\n"))
    return {"path": "dag/pilot_triage/" + name, "sha256": sha(raw), "reviewed_lines": [start or 1, end or lines]}
def anchor(name, text):
    lines = (HERE / name).read_text(encoding="utf-8").split("\n")
    return next(i for i, line in enumerate(lines, 1) if text in line)

probes = read("retirement_review_probe_results.json")
for name, digest in probes["source_sha256"].items():
    assert sha((HERE / name).read_bytes()) == digest, "source changed after probes: " + name
plan_bytes = (HERE / "retirement_plan.json").read_bytes()
plan = json.loads(plan_bytes)
assert sha(plan_bytes) == "d8f65f855521f0f4b94fefc9afe6fc1e0f2be490cda51ea6884007f5847eb74d"
assert plan["pilot_count"] == 138 and plan["file_count"] == 3146
lessons_bytes = (ROOT / plan["lessons_path"]).read_bytes()
assert sha(lessons_bytes) == plan["lessons_sha256"]
lesson_ids = [item["id"] for item in json.loads(lessons_bytes)["lessons"]]
assert len(set(lesson_ids)) == len(lesson_ids) == 138
assert set(lesson_ids) == {p["id"] for p in plan["pilots"]}
reports = {}
for item in plan["pilots"]:
    if item["report"] not in reports:
        raw = (ROOT / item["report"]).read_bytes()
        reports[item["report"]] = (sha(raw), json.loads(raw))
    digest, report = reports[item["report"]]
    assert digest == item["report_sha256"]
    matches = [p for p in report["pilots"] if p["id"] == item["id"]]
    assert len(matches) == 1 and all(matches[0][k] == item[k] for k in ("path", "verdict", "rationale"))
archive_path = Path(plan["recovery_archive"]["archive_path"])
assert archive_path.stat().st_size == plan["recovery_archive"]["archive_bytes"]
assert sha(archive_path.read_bytes()) == plan["recovery_archive"]["archive_sha256"]

findings = [
 {"id": "RETIRE-01", "initial_severity": "high", "status": "resolved_in_reviewed_source",
  "issue": "A stale catalog verdict could select a pilot whose freshly hashed report now recommended retention.",
  "resolution": "Preparation compares the complete retained row fields with the uniquely matching current report row; PowerShell independently checks report digest and id/path/verdict/rationale before removal.",
  "evidence": [evidence("prepare_retirement.py", anchor("prepare_retirement.py", "report_bytes ="), anchor("prepare_retirement.py", "Catalog does not match")), evidence("apply_retirement.ps1", anchor("apply_retirement.ps1", "$taskReportPath ="), anchor("apply_retirement.ps1", "Plan does not match current reviewed verdict"))],
  "probes": ["stale_catalog", "report_verdict_drift"]},
 {"id": "RETIRE-02", "initial_severity": "high", "status": "resolved_for_process_interruption_with_recorded_intent",
  "issue": "Removal originally preceded the receipt record; partial deletion or a process interruption could leave missing files unavailable to the archive evidence reader.",
  "resolution": "The script records a single removal_intent before Remove-Item, then atomically replaces it with the completed row. EvidenceStore permits exact manifest/hash-checked archive fallback for explicit incomplete intent while preserving live evidence and incomplete status.",
  "evidence": [evidence("apply_retirement.ps1", anchor("apply_retirement.ps1", "$taskReceipt =")), evidence("retirement_custody.py", anchor("retirement_custody.py", "intent = receipt.get"))],
  "probes": ["partial_intent_evidence", "partial_catalog_rebuild", "completed_catalog_rebuild"],
  "limit": "No production deletion, abrupt process kill or power-loss fault injection was executed. The script intentionally refuses a second Apply after a receipt exists; recovery/resumption requires inspection."},
 {"id": "RETIRE-03", "initial_severity": "high", "status": "resolved_in_powershell_removal_boundary",
  "issue": "Unarchived NTFS alternate data streams on files or the selected directory passed normal byte/hash/ZIP checks and would be discarded by recursive removal.",
  "resolution": "PowerShell checks the target and every descendant for non-default streams in both preflight and the immediately-before-removal Test-CurrentPilot call. Preparation alone does not check streams and explicitly requires that PowerShell boundary.",
  "evidence": [evidence("apply_retirement.ps1", anchor("apply_retirement.ps1", "$taskAllItems ="), anchor("apply_retirement.ps1", "$taskCurrentDirs =")), evidence("prepare_retirement.py", anchor("prepare_retirement.py", "removal_preflight_requirement"), anchor("prepare_retirement.py", "removal_preflight_requirement"))],
  "probes": ["file_ads", "directory_ads"]},
 {"id": "RETIRE-04", "initial_severity": "medium", "status": "resolved_in_reviewed_source",
  "issue": "Unknown empty directories were outside the file-only census and would silently disappear.",
  "resolution": "Preparation compares exact directory sets; PowerShell compares current descendants with the original directory inventory embedded in the hash-pinned recovery ZIP.",
  "evidence": [evidence("prepare_retirement.py", anchor("prepare_retirement.py", "directories ="), anchor("prepare_retirement.py", "Unknown or missing directories")), evidence("apply_retirement.ps1", anchor("apply_retirement.ps1", "$taskCurrentDirs ="), anchor("apply_retirement.ps1", "Directory structure differs"))],
  "probes": ["unknown_empty_directory"]},
 {"id": "RETIRE-05", "initial_severity": "medium", "status": "resolved_in_reviewed_source",
  "issue": "After removal intent, EvidenceStore originally accepted corruption of the retained-lessons file while advertising preserved_mechanism pointers.",
  "resolution": "EvidenceStore checks the frozen lesson path, SHA-256 and exact unique lesson-to-plan identifier bijection before accepting any receipt.",
  "evidence": [evidence("retirement_custody.py", anchor("retirement_custody.py", "if plan['lessons_path']"), anchor("retirement_custody.py", "Preserved lesson identifiers"))],
  "probes": ["lesson_drift_after_intent"]},
]

assessments = {
"prepare_retirement.py": "Complete source reviewed: selects only stub/trivial verdicts, binds current report fields, requires exact files/directories and current/archive bytes, retains lessons and freezes the plan. It cannot authorize removal without PowerShell checks.",
"retirement_custody.py": "Complete source reviewed: binds receipt to plan and lessons, distinguishes completed versus explicitly incomplete pilots, verifies archive hash and individual entry bytes, and rejects unreceipted missing evidence or escaped paths.",
"apply_retirement.ps1": "Complete source reviewed: defaults to no removal; pins fixed roots, exact numbered-child paths, report decisions, file/dir inventory and archive; rejects reparse points and alternate streams; rechecks each pilot before literal-path recursive removal and records intent/completion.",
"build_catalog.py": "Complete source reviewed: evidence hashes flow through EvidenceStore and remain checked against migration/source inventory; archived and incomplete pilot status propagate while initial triage stays distinct from whole-directory substantive review.",
}
file_reviews = []
for name, assessment in assessments.items():
    file_reviews.append({**evidence(name), "full_source_read": True, "assessment": assessment})

report = {
 "schema": "pfp.retirement-infrastructure-review.v1", "status": "bounded_review_pass_after_fixes",
 "conclusion": "No unresolved blocking defect found in the reviewed hashes for a quiescent current Windows checkout using the PowerShell preflight/removal boundary. This is bounded source and synthetic-fixture evidence, not execution authorization or a universal filesystem safety proof.",
 "base_source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
 "reviewed_artifacts_are_working_tree_sources": True,
 "scope": "prepare_retirement.py, retirement_custody.py, apply_retirement.ps1 and build_catalog.py; all four fully read, current plan/lesson/report pins independently checked, synthetic Windows fixtures only.",
 "file_reviews": file_reviews, "findings": findings, "unresolved_blocking_findings": [],
 "plan_review": {"path": "dag/pilot_triage/retirement_plan.json", "sha256": sha(plan_bytes), "pilot_count": 138, "file_count": 3146, "bytes": plan["bytes"],
                 "reports_bound": len(reports), "lesson_id_bijection_checked": True,
                 "archive_path": str(archive_path), "archive_sha256": plan["recovery_archive"]["archive_sha256"], "archive_bytes": plan["recovery_archive"]["archive_bytes"],
                 "whole_archive_hash_independently_rechecked": True, "archive_entry_bytes_preflight": "Parent reports real Windows preflight passed for all 138 folders / 3146 files; this reviewer did not repeat that entire production entry scan."},
 "validation": {"synthetic_results": "dag/pilot_triage/retirement_review_probe_results.json", "synthetic_results_sha256": sha((HERE / "retirement_review_probe_results.json").read_bytes()),
                "controls_exercised": 14, "fixture_creation_blocked": 1, "production_apply_invoked": False, "production_corpus_mutations": 0,
                "checks": probes["results"]},
 "residual_limits_and_followups": [
   "Quiescence is an execution precondition: the script rechecks immediately before removal but does not lock every source inode/directory against concurrent writers or link substitution. Stop readers/writers before Apply; no hostile concurrency proof is claimed.",
   "The junction fixture could not be created (New-Item: Access is denied), so link rejection is source-reviewed plus the parent's production scan, not a fresh injected-junction test.",
   "The receipt replacement is atomic at the filename level in the source, but no power-loss/disk-flush guarantee or crash fault-injection test was established. The full pinned recovery archive remains necessary for manual recovery.",
   "After any receipt exists, Apply intentionally refuses rerun. An incomplete operation should be inspected and restored/resumed through an explicit recovery procedure; automatic restart was not implemented or claimed.",
   "The 77,421,556-byte archive is outside the repository at an absolute local visualization path. It must be retained and transferred with its SHA for another checkout/machine to rebuild archived evidence; Git alone does not carry these bytes.",
   "The review validates eligibility against existing triage decisions, not the scientific quality of every retired file. Original report semantic-coverage limits remain in force; no candidate verdict is upgraded to mathematical evidence.",
   "No model/provider calls, protected benchmark or private answer-key reads, production Apply, source fixes or corpus deletions were performed by this reviewer. Parent made the infrastructure repairs."
 ]}
(HERE / "retirement_review.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(HERE / "retirement_review.md").write_text("""# Retirement infrastructure review

No unresolved blocking defect remains in the reviewed source hashes for the current Windows checkout, provided source writers/readers are stopped before removal. This is a bounded review, not authorization or a general filesystem-safety proof.

Five concerns found during review were repaired by the parent: stale catalog decisions, missing intent during partial removal, unarchived NTFS streams, unknown empty directories, and unchecked retained-lesson drift. Synthetic controls verify the repaired boundaries, including archive-backed catalog rebuilds after partial and completed fixture removal. No production `-Apply` was invoked.

The frozen plan remains SHA-256 `d8f65f855521f0f4b94fefc9afe6fc1e0f2be490cda51ea6884007f5847eb74d`: **138 pilots, 3,146 files, 7,116,572 bytes**. Current report pins, retained-lesson bijection and the entire recovery archive hash were independently checked. The parent reports that real Windows preflight passed for every selected file.

Fourteen synthetic controls ran; junction creation was denied, so injected-link behavior remains untested. No power-loss or concurrent-writer guarantee is claimed. A partial receipt requires explicit inspection before any resume. Preserve the external 77,421,556-byte archive: another checkout cannot reconstruct retired evidence from Git alone.

Exact source hashes/ranges, repaired findings, controls and limits are in `retirement_review.json`; the replayable fixture code is `retirement_review_probes.py`.
""", encoding="utf-8")
print(json.dumps({"status": report["status"], "source_hashes": probes["source_sha256"], "plan_sha256": sha(plan_bytes), "controls": 14, "blocked_fixture": 1, "unresolved_blockers": 0}, indent=2))
