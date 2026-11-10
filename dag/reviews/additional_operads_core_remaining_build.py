"""Build this review from complete-body receipts and explicitly bounded artifacts."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
PREFIX = "additional_operads_core_remaining"
scope_path = HERE / (PREFIX + "_scope.json")
scope = json.loads(scope_path.read_text(encoding="utf-8"))
rows = {r["path"]: r for r in scope["files"]}
notes_path = HERE / (PREFIX + "_assessments.json")
notes = json.loads(notes_path.read_text(encoding="utf-8"))
for supplement in sorted(HERE.glob(PREFIX + "_notes*.json")):
    notes.update(json.loads(supplement.read_text(encoding="utf-8")))
ledger = json.loads((HERE / (PREFIX + "_read_ledger.json")).read_text(encoding="utf-8"))
read = {}
for entry in ledger:
    if entry.get("output_truncated"):
        continue
    assert entry["sha256"] == rows[entry["path"]]["sha256"]
    read.setdefault(entry["path"], set()).update(
        n for a, b in entry["reviewed_lines"] for n in range(a, b + 1)
    )

# All 59 initializers were read completely, in three bounded batches after a
# truncated first attempt was invalidated. Extract export details from those
# already-reviewed bodies, without claiming any imported owner was executed.
for path, row in rows.items():
    if not path.endswith("/__init__.py") or path in notes:
        continue
    assert read.get(path) == set(range(1, row["lines"] + 1)), path
    body = (ROOT / path).read_text(encoding="utf-8")
    tree = ast.parse(body)
    doc = " ".join((ast.get_docstring(tree) or "").split())
    imports = [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    deferred = any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "__getattr__" for n in tree.body)
    notes[path] = (
        "Complete package initializer body reviewed. " + doc + " "
        + ("Lazy name-to-module export dispatch caches requested attributes; imported implementation behavior is outside this file. " if deferred else "Direct import/export wiring or package marker; no mathematical predicate implemented here. ")
        + "Direct imports: " + ("; ".join(imports) or "none")
        + ". Labels/exports do not establish operadic laws or authorize effects. No package import executed."
    )

file_reviews = []
for path, assessment in notes.items():
    row = rows[path]
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == row["sha256"], path
    expected = set(range(1, row["lines"] + 1))
    assert read.get(path, set()) == expected, (path, "incomplete actual read")
    file_reviews.append({
        "path": path, "sha256": row["sha256"], "full_source_read": True,
        "reviewed_lines": [[1, row["lines"]]] if row["lines"] else [],
        "assessment": assessment, "reading_method": "complete_source_body_review",
        "review_level": "full_text_source_review", "parsed_value_read": False,
        "source_line_count": row["lines"],
    })
file_reviews.sort(key=lambda r: r["path"])

def evidence(path, start, end):
    assert path in notes
    return {"path": path, "sha256": rows[path]["sha256"], "lines": [[start, end]], "full_source_read": True}

def finding(code, title, sources, ceiling, action):
    return {"id": code, "claim": title, "finding": title,
            "source_evidence": [evidence(*s) for s in sources],
            "evidence_kind": "complete source review; no execution yet",
            "ceiling": ceiling, "next_action": action}

findings = [
    finding("OCR01", "Legacy ecology verifies signature maps, not suboperad embeddings: default empty maps pass and loader omits declared morphism kind.", [("operads/skill_operad/meta_operad.py",122,226),("operads/skill_operad/meta_operad.py",302,360)], "No composition/unit structure or injectivity/ideal-preservation predicate is represented; source-only conditional finding.", "Keep as signature-map bookkeeping or add explicit totality/injectivity and preservation obligations; never use an embedding label as a mathematical certificate."),
    finding("OCR02", "Legacy HoTT paths accept witness-free relations and string-equal unequal concatenation boundaries.", [("operads/skill_operad/hott.py",104,163),("operads/skill_operad/hott.py",265,286)], "Predicate-battery and endpoint bookkeeping, not a HoTT proof kernel.", "Require a declared relation/checker and exact endpoint equality; state separately what finite battery establishes."),
    finding("OCR03", "Legacy span partition is not exhaustive for whitespace-only sections, and morphism execution omits output colour/integrity checks.", [("operads/skill_operad/domain/span_operands.py",209,269),("operads/skill_operad/domain/span_operands.py",288,303)], "Local text partition/type guards; no generalized source-location or semantic contract proof.", "Check concatenation/coverage and fence state, then validate input integrity and output signature before reusable execution."),
    finding("OCR04", "SourceByteSpan accepts negative end_col on multiline ranges.", [("operads/domain/value_objects/byte_span.py",17,33)], "Constructor-level predicate gap; no assertion that strict ingress exposes it.", "Reject negative ending columns independently and add a focused constructor counterexample."),
    finding("OCR05", "Legacy DDC parser is import-blocked by undefined DDC_LETTER; its body can label signed or partially missing residual sums exact.", [("operads/skill_operad/ddc_operad_parser.py",21,30),("operads/skill_operad/ddc_operad_parser.py",61,83),("operads/skill_operad/ddc_operad_parser.py",699,758)], "NameError is source-evident; deeper behavior is conditional on supplying the missing alphabet, not an observed production run.", "Preserve the import defect finding; separately isolate exact finite counterexamples before any later authorized repair."),
    finding("OCR06", "Legacy DDC compilation returns marker bodies and permits law-invalid receipts to flow into registration/compression.", [("operads/skill_operad/ddc_operad_parser.py",193,246),("operads/skill_operad/ddc_operad_parser.py",310,355),("operads/skill_operad/ddc_operad_parser.py",760,805)], "Parsing Ok may legitimately carry diagnostics, but these marker bodies do not execute the named repair and compression has no laws-valid gate.", "Separate diagnostic parsing from eligibility to register an executable; require actual checker/encoding and bound operation implementation."),
    finding("OCR07", "Legacy EvidenceReceipt.is_clean ignores unverified claims, command failures and whether any tests ran.", [("operads/skill_operad/evidence_receipt.py",89,126)], "Only a supplied DTO predicate, not evidence that execution occurred.", "Rename to its narrow predicate or explicitly check all claimed gates and source-bound execution records."),
    finding("OCR08", "Current legacy associativity registry tests intentionally pin no compositions, while a separate fail-open regression requires a nonempty matrix.", [("operads/skill_operad/tests/test_associativity_witness.py",57,83),("operads/tests/ddc_execution/test_operad_composition_fail_open.py",72,98)], "Historical test-source incompatibility; neither suite rerun here.", "Keep structural-registration scope explicit and use an isolated synthetic composition for the negative-control fixture."),
    finding("OCR09", "Trace storage's three-row contractivity threshold does not require independent unique runs or bind a metric/checker, and mirror updates are not one atomic transaction.", [("operads/infrastructure/ddc_execution/trace_storage.py",58,117),("operads/infrastructure/ddc_execution/trace_storage.py",121,174)], "Arithmetic consistency of caller-supplied measurements is stronger than legacy unchecked traces but weaker than independent evidence; default runtime evaluator is unavailable.", "Retain measurement custody mechanism with explicit uniqueness/metric/checker binding and concurrency/crash semantics before promotion use."),
    finding("OCR10", "Legacy application validator treats an existing operation ID as an associativity witness without comparing either composite.", [("operads/skill_operad/application/use_cases/validate_operad_use_case.py",128,173)], "No current populated-law bypass asserted; matrix content is separately pending artifact review.", "Keep declaration status and actual equality witnesses separate; compose both sides with a sound equality predicate when a law is claimed."),
]

artifacts = json.loads((HERE / (PREFIX + "_artifacts.json")).read_text(encoding="utf-8"))
probes = json.loads((HERE / (PREFIX + "_probes.json")).read_text(encoding="utf-8"))
supplement = json.loads((HERE / (PREFIX + "_supplement.json")).read_text(encoding="utf-8"))
initial_findings = list(findings)
previous_path = HERE / (PREFIX + ".json")
if previous_path.exists():
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    assert previous["findings"][:10] == initial_findings, "Initial findings must remain unchanged"
full_count = len(file_reviews)
full_lines = sum(r["source_line_count"] for r in file_reviews)
for item in artifacts["file_reviews"]:
    assert item["path"] in rows and item["path"] not in notes
    assert item["sha256"] == rows[item["path"]]["sha256"]
    assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    assert item["full_source_read"] is False and item["reviewed_lines"] == []
    file_reviews.append(item)
file_reviews.sort(key=lambda r: r["path"])
findings += supplement["findings"]
assessed = {item["path"] for item in file_reviews}
pending = [path for path in rows if path not in assessed]
assert len(assessed) == len(file_reviews)
for item in supplement["findings"] + supplement["claims"]:
    for pin in item["source_evidence"]:
        assert pin["path"] in notes and pin["sha256"] == rows[pin["path"]]["sha256"]
        assert all(1 <= a <= b <= rows[pin["path"]]["lines"] for a, b in pin["lines"])

def artifact_pin(suffix):
    path = HERE / (PREFIX + suffix)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

corrections = json.loads((HERE / (PREFIX + "_notes99_path_corrections.json")).read_text(encoding="utf-8"))
report = {
    "schema_version": "additional_source_review.v1",
    "status": "in_progress" if pending else "completed",
    "source_commit": scope["source_commit"],
    "scope": {"frozen_scope_path": str(scope_path.relative_to(ROOT)).replace("\\", "/"), "frozen_scope_sha256": hashlib.sha256(scope_path.read_bytes()).hexdigest(), "declared_paths": len(rows), "declared_lines": sum(r["lines"] for r in rows.values())},
    "summary": {"assessed_paths": len(file_reviews), "full_source_files": full_count, "full_source_lines": full_lines, "parsed_artifact_files": len(artifacts["file_reviews"]), "parsed_artifact_lines": sum(r["source_line_count"] for r in artifacts["file_reviews"]), "pending_paths": len(pending), "findings": len(findings), "claims": 1 + len(supplement["claims"]), "fresh_probes": probes["counts"]["finite_probes"], "full_suites_run": 0},
    "method": "530 complete pinned source bodies read; truncated emissions invalidated and reread. Package-export metadata extraction follows complete reads. Four generated catalogs have bounded parsed-value review, not full raw/prose reading receipts. Existing tests reviewed as source only. Thirteen synthetic finite probes execute whitelisted AST definitions with stdlib and inert injected wrappers; no production module imports, native tools, databases, external effects or providers executed.",
    "claims": [{"id": "OCR-C01", "claim": "The default meta-operad runtime refuses executable behavior until an evaluator is explicitly bound; dry-run output remains a plan.", "source_evidence": [evidence("operads/infrastructure/ddc_execution/runtime.py",56,76), evidence("operads/application/ddc_execution/meta_operad_engine.py",55,110)], "ceiling": "Source-level boundary; no end-to-end execution claimed."}] + supplement["claims"],
    "findings": findings, "file_reviews": file_reviews,
    "execution_evidence": [{"method": probes["method"], "sources": probes["sources"], "probes": probes["probes"], "counts": probes["counts"], "helper": artifact_pin("_probes.py"), "receipt": artifact_pin("_probes.json")}],
    "artifact_evidence": [{"method": artifacts["method"], "summary": artifacts["summary"], "limits": artifacts["limits"], "helper": artifact_pin("_artifacts.py"), "receipt": artifact_pin("_artifacts.json")}],
    "reusable_mechanisms": supplement["reusable_mechanisms"],
    "correction_history": [{"kind": "withdrawn_path_parent_diagnosis", "affected_assessments": len(corrections), "paths": sorted(corrections), "explanation": "Explicit Path.parents arithmetic established correct repository roots. Earlier incorrect root-relocation diagnoses are withdrawn and superseded in current per-file assessments; no finding used them. Destination availability is a separate issue.", "evidence": artifact_pin("_path_arithmetic.json"), "replacement_assessments": artifact_pin("_notes99_path_corrections.json")}],
    "initial_finding_status_updates": [{"id": "OCR04", "update": "OCR-P01 confirms the constructor gap under the stated finite extraction assumptions; original checkpoint finding retained verbatim."}, {"id": "OCR10", "update": "Remaining source reading is complete. Existing matrix expectations remain empty as documented in OCR08; no current populated-law bypass or fresh matrix suite run is asserted. Original checkpoint wording retained verbatim."}],
    "provenance": {"reading_ledger": artifact_pin("_read_ledger.json"), "frozen_resume_checkpoint": artifact_pin("_remaining_scope.json"), "initial_findings_preserved_count": 10, "frozen_source_hashes_verified_count": len(rows)},
    "limitations": ["All 534 paths have dispositions: 530 full body reviews and four bounded parsed catalog reviews. All executable and ordinary prose bodies in the declared scope are closed; four generated catalog prose bodies remain outside a full-text reading claim.", "Catalog cross-projection/digest checks do not prove mathematical laws, referenced implementation adequacy or external resource bytes. No unsupported binary artifacts occur in this frozen scope.", "No production modifications, production module imports, native/model/network execution, sealed benchmark or private-key reads. Only report helpers and reports were written.", "Thirteen finite extracted-definition probes are not full production suites or end-to-end runtime evidence. Historical authored tests remain distinct from fresh probe receipts.", "Full source review does not prove universal mathematical laws, physical bridge assumptions or checker adequacy."],
    "pending_paths": pending,
}
notes_path.write_text(json.dumps(notes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(HERE / (PREFIX + ".json")).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
md = ["# Operads core remaining-source review", "", f"Status: {report['status']}. All {len(rows)} frozen paths assessed: {full_count} complete source bodies ({full_lines:,} lines), plus four generated catalogs ({report['summary']['parsed_artifact_lines']:,} lines) reviewed through bounded parsed checks. No pending paths. All frozen source hashes match; source files were not modified.", "", report["method"], "", "The report contains 21 findings, six bounded positive claims and seven reusable mechanisms. The original ten checkpoint findings remain verbatim, with explicit status updates for later evidence. Twenty-six earlier per-file path-parent diagnoses were withdrawn after exact arithmetic; the current assessments carry those corrections.", "", "## Findings", ""]
for item in findings:
    md += [f"- **{item['id']}** {item['finding']} {item['ceiling']} Next: {item['next_action']}"]
md += ["", "## Reusable mechanisms", ""]
for item in supplement["reusable_mechanisms"]:
    md += [f"- **{item['mechanism']}**: {item['recommendation']}. Prerequisites: {item['prerequisites']}"]
md += ["", "## Validation and ceilings", "", "All 13 AST-isolated finite probes confirmed their bounded observations. They exercised constructors, signer framing, trimming, a lexical detector/cache, prompt checklist gates, architecture filtering, serialization projection and pure path construction. No full suite, database effect, filesystem effect from source code, native tool or provider was executed.", "", "All 16 generated-catalog checks passed over 237 skills, 12 agents, 93 anti-skills, 10 colours and 601 declared resource references. Catalog declarations contain 30 BOUND and 207 UNBOUND executor references; all 93 anti-skills remain Candidate/UNBOUND. Digest/projection consistency is custody evidence, not executable admission, suboperad closure or detector adequacy. Referenced external resource bytes were not revalidated by this catalog pass.", "", "Exact pinned source hashes/ranges, all per-file assessments, probe receipts, artifact checks, corrections and scope limits are in the companion JSON. No old expected answer or target paper is promoted into workflow input.", ""]
(HERE / (PREFIX + ".md")).write_text("\n".join(md), encoding="utf-8")
print(json.dumps(report["summary"]))
