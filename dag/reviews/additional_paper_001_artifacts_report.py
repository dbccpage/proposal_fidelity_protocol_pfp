"""Render the manually assessed Paper 001 artifact audit; original files read only."""
import json
from pathlib import Path
from hashlib import sha256

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / "dag/reviews"
BASE = "papers/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/"
support = json.loads((REV / "additional_paper_001_support.json").read_text())
checks = json.loads((REV / "additional_paper_001_artifact_checks.json").read_text())
primary = json.loads((REV / "papers_audit.json").read_text())
primary_file = next(x for x in primary["files"] if x["path"] == BASE + "paper.md")
primary_paper = next(x for x in primary["papers"] if x["primary_manuscript"] == BASE + "paper.md")

assessments = {
"MANIFEST.sha256": "All 95 digest/path entries read. Unique confined paths form the intended historical payload inventory. Fresh raw check finds 52 mismatches to the current tree; 20 remain after text-only LF normalization. The archived counterpart binds all 95 archived payloads. This is byte custody, not validation of mathematical claims or historical execution.",
"SHA256SUMS": "All 96 entries read, including MANIFEST.sha256 and the same 95 payload entries. Fresh raw check finds 53 current-tree mismatches; 21 remain after text-only LF normalization. All 96 archived bindings pass. The manifest is not self-hashed, and archive integrity does not make the current edition validated.",
"code/rust/Cargo.lock": "Entire lock read: format 4, 107 packages, 91 registry entries with syntactically valid checksums and 16 local package entries. Every declared dependency resolves to one listed lock entry. The local core_* graph and thin pfp_exact_graph wrapper differ from the old standalone Cargo receipts. Local entries do not pin source bytes, and the current Cargo.toml dependency path is broken as recorded by the parent. No Cargo run, registry authentication or third-party source audit is inferred.",
"docs/release_validation_2026_10_01.json": "Complete historical validation receipt read: seven Python batches total 64 stated passes, four Lean steps including a 151-declaration census, six notebook/cwd checks and eight native unit tests. Test-source hashes are explicit, but some current inputs differ. Its stdout names a former in-package Rust library no longer present in this adapter. It records no live provider experiment or external deposit. Paths, including text inside stdout, were rewritten relative to the ZIP; preserve the earlier edition and label this as an edited historical transcription.",
"docs/release_validation_2026_10_02.json": "Complete candidate receipt read: eight selected tests, PDF compilation, 151 listed local Lean declarations at v4.34.0-rc1 and explicit source hashes. No notebook execution is claimed here, and older notebook receipts are expressly historical. Candidate asset hashes differ from later PDF/text editions; historical pass counts do not validate the current v4.35.0 pin. Archive comparison identifies path-only edits in cwd/commands/hash keys, not new executions.",
"docs/release_validation_2026_10_02_continued_review.json": "Complete targeted follow-on receipt read. Nine named tests, four-cell ordinary Python replay and demos have explicit narrow scope. It discloses pytest 8.3.5 versus declared >=9.0.3, no native/Lean run and no K8 cap execution. The contract-validator command exits zero while its scope lists missing evidence_required and schema defects: process success must not become contract validity. Executed hashes and conceptual baseline are explicitly distinct; paths were later rewritten relative to the ZIP.",
"docs/release_validation_2026_10_02_review_repairs.json": "Complete historical review receipt read. It distinguishes 73 package tests, 32 exact directed-cycle checks, 96 floating LP comparisons at 1e-8, mock native responses, failed long-path Cargo run and successful deleted short-target run, narrow Lean census and six notebook/cwd executions. Neither the short-target binary nor K8-cap execution is retained. Dirty-worktree hashes bind only named files and current edition differs. This is useful provenance with stated limits, not a fresh execution or authentication of deleted logs.",
"results/demo2_r1_stoquastic_1790206738.jsonl": "Zero-byte retained artifact explicitly inspected. It supplies no trial, response, token count or classification evidence; its emptiness does not establish why a historical attempt produced no records.",
"results/demo2_r1_stoquastic_1790206756.jsonl": "All ten historical JSONL records, prompts and raw responses read. The run only asserts ten of twelve listed matrix entries; phi1 drops from sentinel 999 to zero after the first off-diagonal entry, and no VERIFY occurs. The partial host-state proxy is not an independently certified full-matrix classification. Token totals are reported metadata only. Useful regression example for complete-input and terminal-certificate admission.",
"results/demo2_r1_stoquastic_1790206807.jsonl": "All six records read. After four diagonals and one off-diagonal assertion, host text prematurely says all off-diagonals were classified and directs immediate VERIFY. The identity witness then claims Xi(x)!=x and sign reversal while receiving ExactCancellation. The explicit singleton identity countercontrol refutes the fixed-point-free assertion. Positivity and cancellation are distinct routes; this historical admission is not a valid four-law cancellation certificate.",
"results/demo2_r2_freefermion_1790207127.jsonl": "Zero-byte retained artifact explicitly inspected. No trial or mathematical conclusion is present, and no cause for the empty output is inferred.",
"results/demo2_r2_freefermion_1790207175.jsonl": "The complete one-record batched trace is read. Its proposed 0<->1, 2<->3 swap is involutive but fails the claimed chain symmetry because edge 1-2 maps to absent 0-3. Prose says signs are preserved, not reversed, and supplies no determinant matrix or path-weight pairing. Historical ExactCancellation is unsupported as a four-law certificate; this says nothing against a separately established representation-specific free-fermion calculation.",
"results/demo2_r3_attractive_hubbard_1790207676.jsonl": "All twelve records and full repeated raw strings read. Every stored result is ParseFailure; later responses are visibly truncated, with embedded unescaped newlines in earlier proof strings. The first response also emits multiple fenced objects rather than one aggregate. The trace demonstrates a failed parser interaction, not physical obstruction or successful cancellation; no parser version or complete cost record is available here.",
"results/demo2_r3_attractive_hubbard_1790207968.jsonl": "Complete one-record multi-block proposal read. Six term assertions and a particle-hole prose witness receive historical ExactCancellation. The four laws are asserted in words without host-weight enumeration or determinant hypotheses. This is useful as a negative certificate-admission example, not independent proof of the physical classification. The apparent earlier/later parser change is not reconstructed from this record alone.",
"results/demo2_r4_repulsive_hubbard_1790207568.jsonl": "Complete one-record trace read. OPEN_SIGN_OBSTRUCTION is admitted on a general U>0/NP-hardness narrative, with no checked witness for the supplied dimer and no declared path carrier. Failure to find a cancellation map and a general complexity claim do not prove instance-specific nonexistence. Retain as historical evidence of overbroad admission.",
"results/demo2_r5_chatgpt_frustrated_triangular.jsonl": "Both full records read. First requests the missing carrier, ensemble, weights and gauge domain. After the host supplies the integrated 64-state thermal carrier at fixed beta=1/4, t=1, U=2, the response gives the negative -exp(-1)/384 path and disjoint magnitude bounds for all length classes. That narrow argument corresponds to the parent's source-reviewed/executed exact Fock checker. The raw record itself neither authenticates model identity nor proves a general sign-problem obstruction; its reported admission is kept separate from the independent finite check.",
"results/demo2_r5_deepseek_frustrated_triangular.jsonl": "Complete single record read. It promotes non-bipartiteness and failed alternating gauge to absence of every sign-reversing involution, and adds half filling that was not declared in the prompt. Historical admitted status does not supply the missing carrier/weight proof. Contrast is useful for teaching scope admission; no model-performance comparison follows from one differently assisted record.",
"results/demo2_r5_frustrated_triangular_1790208154.jsonl": "Both complete records read. A term-reversal mapping over equal negative hopping coefficients is not a signed path pairing. The host refuses it using an overbroad geometric obstruction narrative, then tells the proposer which terminal to emit. The second record parrots that narrative and is admitted without a concrete obstruction witness. The sequence measures response to supplied feedback, not independent discovery or a general theorem.",
"results/demo2_r7_adversarial_debate_1790210039.jsonl": "All ten complete paired records, including duplicated raw/parsed text, read. Six old positive labels, four negative labels, eight CHALLENGE and two CONCUR yield TP=6, FP=2, TN=2, FN=0 against historical labels only. All raw adversary_caught_am fields are true, including CONCUR rows. Exact finite controls expose a five-cycle rotation that is not involutive, a reflected fixed site and a nonbijective Kagome map; prose often overextends odd-cycle or NP-hardness claims. Parent current replay refuses all ten proposals. No independently labeled physical truth, randomization, cost accounting or evidence of general improvement is supplied.",
"results/demo2_r7_adversarial_debate_receipt.json": "Entire 162-line derived receipt read. Its ten trial fields agree with raw rows; exact recomputation confirms precision 3/4, recall 1 and accuracy 4/5 relative to historical labels. It correctly labels the experiment an offline trace replay and reports ten current refusals rather than ten proven obstructions. Stored source_trace_sha256 matches archived/LF-normalized trace bytes, not current CRLF bytes; exact edition must be specified. Model names are reported provenance, not externally authenticated.",
"results/receipt.json": "Complete byte equality to the fully read demo2_r7_adversarial_debate_receipt.json is freshly verified; all ten trial assessments and the historical-label-only arithmetic apply. This duplicate is not an independent experiment or replication.",
"results/review_validation.json": "Complete historical receipt read. Two batches state 52 passes, an 80-instance seeded numerical HiGHS comparison, narrow Lean build, demos and notebook runs; explicit limits exclude full monorepo tests, live calls and an unavailable swarm/AutoP receipt. The stored source hashes belong to an older research/papers edition. Matching current/LF hashes establish surviving bytes only; mismatches do not refute older runs. The archive delta rewrites one outside-package operations path; that outside file was not inspected in this slice.",
}
assert len(assessments) == 22
reviews = []
for pin in checks["pins"]:
    rel = pin["path"][len(BASE):]
    if rel.endswith(".zip"):
        assessment = "All 97 logical members have complete content dispositions through explicitly reviewed current bases and full byte equality, text-only LF equality, or reading every difference. All eight PDFs and the figure are exactly equal to reviewed current bytes. All 22 text deltas were read in full (1,321 displayed diff lines), and reverse-hunk application reconstructs every archived normalized text exactly. CRC, unique confined inventory and all 191 embedded manifest bindings pass. This is complete logical-content review with a bounded container check, not ZIP-parser security review, historical execution authentication or publication certification."
        method = "Complete logical-member reading by explicit verified base transfer plus all differences; bounded ZIP inventory, CRC and manifest checks"
    else:
        assessment = assessments[rel]
        method = "Complete original text displayed and substantively read" if rel != "results/receipt.json" else "Fully read identical receipt base plus fresh whole-byte equality"
    row = {"path": pin["path"], "sha256": pin["sha256"], "full_source_read": True,
           "reviewed_lines": [[1, pin["lines"]]] if pin["lines"] else [],
           "assessment": assessment, "review_method": method}
    if rel.endswith(".zip"):
        row.update({"logical_member_review_complete": True, "reviewed_members": 97,
                    "binary_object_internals_reviewed": False, "artifact_check_scope": "bounded CRC/inventory/hash checks"})
    if rel == "results/receipt.json":
        row["base_path"] = BASE + "results/demo2_r7_adversarial_debate_receipt.json"
    reviews.append(row)

base_reviews = {x["path"]: (x, "dag/reviews/additional_paper_001_support.json") for x in support["file_reviews"]}
base_reviews.update({x["path"]: (x, "dag/reviews/additional_paper_001_artifacts.json") for x in reviews if not x["path"].endswith(".zip")})
base_reviews[BASE + "paper.md"] = ({"sha256": primary_file["sha256"], "full_source_read": primary_file["review_status"] == "full-text-read", "assessment": primary_paper["assessment"]}, "dag/reviews/papers_audit.json")

delta_notes = {
"MANIFEST.sha256": "The archive retains original Landau member names; its 95 hashes all bind the archived payloads. Renamed current paths retain older digests and do not certify current edited bytes.",
"SHA256SUMS": "The archive retains original Landau names and original MANIFEST hash; all 96 original bindings pass. Current rename and text edits require separate custody.",
"_lev_landau_theoretical_minimum_quiz/00_preface_at_apartment_50.md": "All changes are source-path or fictional-role/location substitutions, including personal family labels. The graph formulas, admission boundaries and theatrical fiction assessment are unchanged. No historical-person quotation is authenticated.",
"_lev_landau_theoretical_minimum_quiz/paper001_notebook_learning_worksheet.md": "Only two Landau-to-Examiner references change. Exact examples and the exercise/answer evidence boundary are the same.",
"_lev_landau_theoretical_minimum_quiz/quiz.md": "Changes rename the fictional tribunal, location and roles. Numerical problems, proof obligations and fictional grading boundaries are unchanged.",
"_lev_landau_theoretical_minimum_quiz/study_guide.md": "Narrative names and source/native-owner paths change. The graph derivations are unchanged; the external native path remains an edition-specific reproducibility obligation.",
"code/native_functional.py": "The binary-selection variable is OMEGA_FUNCTIONAL_GRAPH_BIN in the archive, CORE_FUNCTIONAL_GRAPH_BIN now. Parsing and fallback semantics otherwise match the reviewed base; do not run this historical adapter with an assumed current environment binding.",
"code/rust/Cargo.lock": "All complete deltas are omega_* to core_* local package/dependency renames; registry pins are unchanged. Both editions require external local crate sources and neither local graph is authenticated by registry checksums.",
"code/rust/Cargo.toml": "Historical omega_solvers path changes to current core_solvers path. Both are repository-external relative dependencies for this extracted package, not standalone included implementations.",
"code/rust/README.md": "Renames canonical crates only and explicitly treats old build receipts as historical. The README itself does not prove the external paths resolve.",
"code/rust/src/bin/solve_graph_phi1.rs": "Only imported crate owner changes from omega_solvers to core_solvers; complete wrapper semantics inherit from the reviewed current base. No native execution occurred.",
"docs/references.md": "Only companion repository paths change from historical omega_engine_atlas paths to atlas paths. Mathematical content and publication assertions are unchanged; no new external authentication is inferred.",
"docs/release_validation_2026_10_01.json": "Original notebook/cwd paths and Cargo stdout path differ from the rewritten current receipt. All outcomes/counts remain the same. Preserve this archived original context separately from relocated annotations.",
"docs/release_validation_2026_10_02.json": "Original cwd, commands and companion/hash keys differ; numerical results and times do not. The archive is the exact historical edition for these fields, not a current build receipt.",
"docs/release_validation_2026_10_02_continued_review.json": "Original cwd, governance import name and companion/hash keys differ. All narrow execution limits and known validator defects remain; no new test execution follows from renamed paths.",
"docs/release_validation_2026_10_02_review_repairs.json": "Original execution directories and companion/hash keys differ; preserved failed/successful native history, numerical LP qualifications and test counts match the base. Do not treat relocated fields as authentic fresh stdout.",
"lean4/lean-toolchain": "Archive pins Lean v4.34.0-rc1, which is the version named in its historical census/build receipts; current source pins v4.35.0. Receipt transfer does not validate the new compiler.",
"paper.md": "Only native-owner and two companion-reference paths differ. All weighted graph L1 derivations and their bounded assessment transfer from the fully read primary manuscript; old paths are not evidence of current package executability.",
"paper.tex": "All deltas rename embedded GitHub/reference paths; the mathematical TeX is unchanged. Archived PDFs correspond to older bytes, and the current paths can remain stale despite string substitution.",
"paper_change_log.md": "Only role, companion and native-pharmacy owner names change in historical entries. It retains chronology and prior scope repairs; renamed historical prose is not an execution log.",
"paper_claim_ledger.md": "Three native-source owner links change; claim hypotheses, evidence distinction and no-dual-output limitation remain identical. The current path is already flagged as broken by the parent.",
"results/review_validation.json": "One outside-package operations hash key is renamed, while digest and all reported checks remain fixed. This is an edited historical receipt field; the external owner was not read here.",
}
archive_reviews = []
for m in checks["archive"]["members"]:
    base, report = base_reviews[m["current_path"]]
    assert base["full_source_read"] and base["sha256"] == m["current_sha256"]
    rel = m["member"].split("/", 1)[1]
    if m["current_raw_equal"]:
        method = "Complete byte equality to explicitly fully reviewed base"
        note = "Exact byte identity transfers the base content assessment without a new independent execution or experiment."
    elif m["current_lf_equal"]:
        method = "Complete text equality after explicit CRLF/CR-to-LF normalization; raw byte differences retained"
        note = "Every logical text character is identical after only newline normalization. The archived raw digest remains separately pinned; byte-custody claims must not silently substitute the normalized form."
    else:
        assert m["reverse_diff_reconstructs_full_archive_text"]
        method = "Fully reviewed base plus complete displayed-difference reading; exact full archived text reconstructed by reverse hunks"
        note = delta_notes[rel]
    base_assessment = base["assessment"]
    if rel == "lean4/FullCensus.lean":
        base_assessment = "Complete expanded axiom census commands inherit the pinned full-source review; the paired 159-line report is also fully reviewed in the parent report. Both concern listed local declarations and are historical, not a fresh Lean build in this slice."
    archive_reviews.append({**m, "full_source_read": True,
        "reviewed_lines": [[1, m["lines"]]] if m["lines"] else [],
        "base_review_report": report, "base_full_source_read": True, "review_method": method,
        "assessment": base_assessment + " Archive context: " + note})

findings = [
{"id": "PAPER001-ARTIFACT-HISTORICAL-FALSE-ADMISSIONS", "severity": "historical_evidence_limit",
 "statement": "The stoquastic transcript admits an identity witness while its prose claims fixed-point freedom. The free-chain transcript admits a swap claimed to preserve the chain even though edge 1-2 maps to absent 0-3. These exact counterexamples show why historical ExactCancellation labels cannot serve as independent certificate truth. Preserve traces as regression evidence and keep current route-specific checking separate.",
 "evidence": [BASE + "results/demo2_r1_stoquastic_1790206807.jsonl", BASE + "results/demo2_r2_freefermion_1790207175.jsonl"], "validation": "dag/reviews/additional_paper_001_artifact_checks.json"},
{"id": "PAPER001-ARTIFACT-HISTORICAL-RECEIPT-REWRITES", "severity": "provenance_gap",
 "statement": "All four docs validation receipts differ from ZIP originals in recorded execution paths; the October 1 receipt changes a path inside stdout. The current versions are edited historical transcriptions, not byte-identical original receipts. Preserve archived bytes and state path translations separately before relying on those fields as exact historical evidence. This does not establish fabricated executions.",
 "evidence": [BASE + "docs/release_validation_2026_10_01.json", BASE + "docs/release_validation_2026_10_02.json", BASE + "docs/release_validation_2026_10_02_continued_review.json", BASE + "docs/release_validation_2026_10_02_review_repairs.json"], "validation": "dag/reviews/paper_001_support_inspection/archive_complete_text_diffs.txt"},
{"id": "PAPER001-ARTIFACT-RAW-DETECTION-FIELD", "severity": "historical_metric_limit",
 "statement": "The raw debate sets adversary_caught_am=true in all ten rows, including both CONCUR rows. It cannot be counted as ten true detections. The derived receipt correctly uses historical labels and CHALLENGE/CONCUR to obtain TP=6, FP=2, TN=2, FN=0, precision 3/4, recall 1 and accuracy 4/5. Those metrics are label agreement, not physical correctness or general model benefit.",
 "evidence": [BASE + "results/demo2_r7_adversarial_debate_1790210039.jsonl", BASE + "results/demo2_r7_adversarial_debate_receipt.json"], "validation": "dag/reviews/additional_paper_001_artifact_checks.json"},
{"id": "PAPER001-ARTIFACT-TRACE-BYTE-BINDING", "severity": "edition_binding_gap",
 "statement": "Both equal debate receipts store the archived/LF trace digest 329e2922..., whereas the current CRLF trace digest is c050cf43.... The logical records are equal after newline normalization, but an exact-byte replay claim must name the archive edition or explicitly state the normalization. Do not rewrite the historical digest to imply a historical run over new bytes.",
 "evidence": [BASE + "results/demo2_r7_adversarial_debate_receipt.json", BASE + "results/receipt.json", BASE + "results/demo2_r7_adversarial_debate_1790210039.jsonl"], "validation": "dag/reviews/additional_paper_001_artifact_checks.json"},
]

automated = []
for r in reviews:
    rules = [{"rule": "Exact frozen source SHA-256 and byte count", "status": "pass"}]
    if r["path"].endswith(".zip"):
        rules += [{"rule": "97 unique confined member names and all member CRCs", "status": "pass"},
                  {"rule": "All 191 embedded manifest bindings", "status": "pass"},
                  {"rule": "43 raw-equal, 32 newline-equal, 22 complete reverse-diff member bindings", "status": "pass"}]
    elif r["path"].endswith(("MANIFEST.sha256", "SHA256SUMS")):
        rules += [{"rule": "All listed paths bind current raw bytes", "status": "fail", "detail": "Historical manifest drift; exact mismatches retained in artifact_checks.json."}]
    elif r["path"].endswith("Cargo.lock"):
        rules += [{"rule": "All 107 package nodes parse and every dependency edge resolves uniquely", "status": "pass"}]
    elif r["path"].endswith((".json", ".jsonl")):
        rules += [{"rule": "Every JSON document or nonempty JSONL row parses", "status": "pass"}]
    automated.append({"path": r["path"], "sha256": r["sha256"], "full_source_read": False,
                      "semantic_review_complete": False, "checks": rules,
                      "status": "bounded_check_failure" if any(x["status"] == "fail" for x in rules) else "bounded_checks_pass",
                      "evidence_ceiling": ["artifact_custody", "finite_structural_checks"]})

report = {
 "schema_version": "1.0", "status": "complete_declared_paper001_artifact_slice",
 "source_commit": support["source_commit"], "scope_source": "dag/reviews/additional_paper_001_support.json:remaining_scope",
 "file_reviews": reviews, "automated_reviews": automated, "archive_member_reviews": archive_reviews,
 "claims": [
   {"id": "PAPER001-ARTIFACT-ARCHIVE-CUSTODY", "statement": "All 97 archived logical members have complete review provenance; all CRCs and 191 embedded manifest bindings pass.", "status": "checked_local_artifact_claim", "limits": "Internal custody does not authenticate the recorded execution, author identity, publication or current edition."},
   {"id": "PAPER001-ARTIFACT-DEBATE-ARITHMETIC", "statement": "The ten retained debate rows give precision 3/4, recall 1 and accuracy 4/5 against the historical label field.", "status": "exact_recomputation", "limits": "Labels are not independent physical truth; no causal improvement or cost benefit is established."}
 ],
 "findings": findings,
 "ledger": [
   {"claim_family": "mathematical graph/Fock content", "evidence": "Fully reviewed current base plus exact archive correspondence; independent checker evidence in parent's report", "admission": "Declared finite graph/rational data or fixed integrated Fock carrier", "ceiling": "No new theorem or broader representation/physics conclusion from the archive."},
   {"claim_family": "historical execution", "evidence": "Complete receipts, named versions and source-hash comparison", "admission": "Trust in the retained historical record and its stated environment", "ceiling": "No fresh Cargo/Lean/provider execution or authentication of deleted logs."},
   {"claim_family": "model/detector effectiveness", "evidence": "46 public historical records; ten paired rows and exact confusion counts", "admission": "Historical labels and supplied host feedback", "ceiling": "Regression examples and label agreement only; no unbiased model comparison or general effectiveness."},
   {"claim_family": "byte custody", "evidence": "23 exact pins, 97 CRC/member checks, 191 embedded hashes and 22 reconstructed complete deltas", "admission": "Local hash/ZIP parser and source pin", "ceiling": "Exact payload correspondence; no parser-security audit or current-manifest validity."}
 ],
 "scope_summary": {"files": 23, "complete_content_dispositions": 23, "text_or_empty_file_reads": 22,
                   "archive_containers": 1, "archive_members": 97, "raw_equal_members": 43,
                   "newline_only_equal_members": 32, "complete_text_delta_members": 22,
                   "complete_diff_lines_read": 1321, "archive_pdfs_with_exact_reviewed_base": 8,
                   "public_trace_records": 46, "empty_trace_files": 2,
                   "small_exact_countercontrols": 5, "historical_receipt_hash_bindings_checked": 123},
 "remaining_scope": [],
 "validation": ["dag/reviews/additional_paper_001_artifact_checks.py", "dag/reviews/additional_paper_001_artifact_checks.json",
                "dag/reviews/additional_paper_001_custody.json", "dag/reviews/paper_001_support_inspection/archive_complete_text_diffs.txt"],
 "evidence_ceiling": "Complete content review for this 23-file slice and all 97 logical archive members, with bounded offline structural/arithmetic checks. No full-repository audit completion, fresh native/formal build, provider experiment, authorship attribution or publication authentication.",
 "limits": [
   "The 75 support bases and primary manuscript are inherited only through explicit full-read receipts and freshly rechecked SHA-256 pins; no digest-only transfer from unread bases.",
   "Text transfers normalize only CRLF/CR to LF. Binary PDF/PNG bytes are never normalized. Every true text delta was read and exactly reconstructs archived normalized bytes.",
   "ZIP full_source_read means every logical member has a complete content disposition; compressed container internals are subject only to bounded standard-library CRC/inventory checks.",
   "All sources and historical evidence are unchanged. Only named review helpers/reports were written.",
   "No network, credentials, provider calls, native build/execution, private benchmark storage or sealed benchmark seed was accessed. Public historical trace prompts were read only as untrusted evidence.",
   "This slice neither completes the all-repository audit nor establishes model-workflow efficacy."
 ]
}
assert {x["path"] for x in reviews} == {x["path"] for x in support["remaining_scope"]}
assert len(archive_reviews) == len({x["member"] for x in archive_reviews}) == 97
for r in reviews:
    assert sha256((ROOT / r["path"]).read_bytes()).hexdigest() == r["sha256"]
(REV / "additional_paper_001_artifacts.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

md = """Paper 001's remaining 23 artifact files now have complete content dispositions, including all 97 logical ZIP members. Original sources and historical evidence are unchanged.

The archive has 43 exact-byte correspondences, 32 text correspondences differing only by newlines, and 22 files with substantive text differences. Every one of the 1,321 diff lines was read. Applying all reverse hunks reconstructs each archived text exactly. All eight PDFs and the figure equal fully reviewed current bytes; all member CRCs and 191 embedded manifest bindings pass. This is logical-content review and bounded container checking, not authentication of historical execution.

The current manifests still have 52/53 raw mismatches, with 20/21 surviving text-only LF normalization. The current lock contains 107 packages (91 registry, 16 local); all dependency edges resolve within its metadata, but local crate contents and build paths are separate obligations.

All 46 public historical trace records were read. They provide useful negative examples: an identity map admitted as fixed-point-free, a chain swap falsely described as a symmetry, and odd-cycle or complexity narratives promoted into instance-specific obstruction claims. The narrow fixed-carrier Fock argument remains supported by the separate exact checker review. None of these records establishes general model benefit or independent physical truth.

The debate receipt's arithmetic is correct against historical labels: TP=6, FP=2, TN=2, FN=0; precision 3/4, recall 1, accuracy 4/5. The raw caught-am field is true on all ten records, including both concurrences, and must not be counted as ten detections. The two equal receipts bind the archived/LF trace digest, not the current CRLF bytes. Parent replay separately refuses all ten proposals.

All four dated docs receipts were edited after the ZIP snapshot to rename recorded paths; one change occurs inside Cargo stdout. Their historical outcomes remain recorded, but current copies should be labeled as edited transcriptions. Preserve original archived fields and add relocation annotations separately. Source-hash comparisons are retained for 123 receipt bindings; changed inputs do not retroactively disprove earlier executions or validate current ones.

The JSON report lists every file and every archive member with exact pins, full-read provenance, assessment and evidence limits. Five small finite countercontrols and all custody checks ran offline. No native build, network/provider call, credential access or private benchmark read occurred. The wider repository audit remains incomplete.
"""
(REV / "additional_paper_001_artifacts.md").write_text(md, encoding="utf-8")
print(json.dumps(report["scope_summary"], indent=2))
