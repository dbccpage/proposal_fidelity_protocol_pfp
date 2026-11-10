"""Check audit custody/counts after substantive reads; never infer review from parsing."""
from collections import Counter
from hashlib import sha256
import json
import re
import subprocess

import additional_native_systems_03_helper as h


def main():
    data = h.load()
    prior_paths = [h.REPORT.with_name(n) for n in
                   ("additional_native_systems.json", "additional_native_systems_02.json")]
    prior = [json.loads(p.read_text(encoding="utf-8")) for p in prior_paths]
    reports = prior + [data]
    assert len(data["file_reviews"]) == 99
    assert all(row["full_source_read"] and row["assessment"] for row in data["file_reviews"])
    assert all(r["source_commit"] == h.COMMIT for r in reports)
    actual_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=h.ROOT, text=True).strip()
    assert actual_head == h.COMMIT
    full_rows = [row for report in reports for row in report["file_reviews"] if row["full_source_read"]]
    occurrences = Counter(row["path"] for row in full_rows)
    assert len(full_rows) == 153 and len(occurrences) == 153
    assert all(count == 1 for count in occurrences.values())
    assert set(occurrences) == {row["path"] for row in prior[0]["file_reviews"]}

    refs = "".join(h.COMMIT + ":" + row["path"] + "\n" for row in full_rows)
    batch = subprocess.run(["git", "cat-file", "--batch"], cwd=h.ROOT,
                           input=refs.encode("utf-8"), capture_output=True, check=True).stdout
    position = 0
    checkout_crlf = []
    blob_hashes = {}
    for row in full_rows:
        end = batch.index(b"\n", position)
        _oid, kind, size = batch[position:end].split()
        assert kind == b"blob"
        position = end + 1
        blob = batch[position:position + int(size)]
        position += int(size)
        assert batch[position:position + 1] == b"\n"
        position += 1
        worktree = (h.ROOT / row["path"]).read_bytes()
        assert sha256(worktree).hexdigest() == row["sha256"], row["path"]
        if worktree != blob:
            assert worktree.replace(b"\r\n", b"\n") == blob.replace(b"\r\n", b"\n"), row["path"]
            checkout_crlf.append(row["path"])
        blob_hashes[row["path"]] = sha256(blob).hexdigest()
    assert position == len(batch)

    corrections = next((v.get("physical_line_count_corrections", []) for v in data["validation"]
                        if v["id"] == "NATIVE03-VALIDATION-004"), [])
    for row in data["file_reviews"]:
        content = (h.ROOT / row["path"]).read_bytes()
        physical_lines = content.count(b"\n") + int(bool(content) and not content.endswith(b"\n"))
        if row["line_count"] != physical_lines:
            corrections.append({"path": row["path"], "previous_count": row["line_count"],
                                "physical_lf_count": physical_lines})
        row["line_count"] = physical_lines
        row["reviewed_lines"] = [[1, physical_lines]]
        row["git_blob_sha256"] = blob_hashes[row["path"]]

    additions = [
        {
            "id": "NATIVE03-FIXTURES-010",
            "claim": "The complete immune guard fixture specifies 216 finite stub-port outcomes: danger/quorum substitution precedence and workflow-report transformation. It supplies no independent measurement of detector or quorum adequacy.",
            "evidence": [
                "code/rust/tests/core_operads/fixtures/python_immune_guards_v1.json:1-109",
                "code/rust/tests/core_operads/fixtures/python_immune_guards_v1.json:8941-9040",
                "code/rust/tests/core_operads/fixtures/python_immune_guards_v1.json:16953-17054",
                "code/rust/tests/core_operads/fixtures/python_immune_guards_v1.json:19572-19727",
                "code/rust/tests/core_operads/fixtures/python_immune_guards_v1.json:22067-22207"
            ],
            "dependencies": ["stub response supplied by fixture", "host-port implementation", "structural substitution implementation", "separate fresh test execution"],
            "limitations": ["84 danger and 84 quorum vectors cover seven index forms, two output colours and six port outcomes; 48 workflow vectors cover policy/prior-finding combinations.", "No real sensor evidence or arithmetic quorum is evaluated by the stub.", "HIGH severity is fixed; CRITICAL quarantine behavior and varied allosteric thresholds are not covered.", "Source inspection is distinct from rerunning parity tests."]
        },
        {
            "id": "NATIVE03-FIXTURES-011",
            "claim": "The fully inspected frozen parity corpus records finite serialization, metadata, lexical-detection and structural-composition contracts; it does not establish general semantic repair, causal independence, authenticated authority or universal operad laws.",
            "evidence": [
                "code/rust/tests/core_operads/fixtures/python_planar_v1.json:1-6478",
                "code/rust/tests/core_operads/fixtures/python_workflow_v1.json:1-1399",
                "code/rust/tests/core_epistemic_immune_system/fixtures/python_independence_v1.json:1-1750"
            ],
            "dependencies": ["historical Python oracle and encoding profile", "trusted host evidence and declared measurement semantics", "appropriate equivalence relation on operation records"],
            "limitations": ["A successful signature comparison is weaker than workflow validity or correct execution.", "Distinct source labels and disjoint spans are structural checks, not a statistical or causal independence proof.", "Display names retain composition bracketing; complete record equality must not be substituted for an explicitly chosen operadic quotient.", "Per-file assessments retain individual fixture and test limits; no current live cross-runtime equivalence theorem is claimed."]
        }
    ]
    # Resolve the two shorter fixture names against the already-reviewed inventory.
    all_paths = set(occurrences)
    for claim in additions:
        for index, evidence in enumerate(claim["evidence"]):
            path, lines = evidence.rsplit(":", 1)
            if path not in all_paths:
                basename = path.rsplit("/", 1)[-1]
                candidates = [p for p in all_paths if p.endswith("/" + basename)]
                assert len(candidates) == 1, (path, candidates)
                claim["evidence"][index] = candidates[0] + ":" + lines
    addition_ids = {claim["id"] for claim in additions}
    data["claims"] = [claim for claim in data["claims"] if claim["id"] not in addition_ids] + additions
    evidence_count = 0
    for group in ("claims", "findings"):
        for item in data[group]:
            for evidence in item["evidence"]:
                match = re.fullmatch(r"(.+):(\d+)(?:-(\d+))?", evidence)
                assert match, evidence
                path, start, end = match.groups()
                content = (h.ROOT / path).read_bytes()
                lines = content.count(b"\n") + int(bool(content) and not content.endswith(b"\n"))
                assert 1 <= int(start) <= int(end or start) <= lines, evidence
                evidence_count += 1
    for claim in data["claims"]:
        claim["limitations"] = [x.replace("Source read in this pass; no fresh test run yet.",
                                         "Source fully read in this pass; this kernel suite was not rerun.")
                                for x in claim["limitations"]]
    data["validation"] = [x for x in data["validation"] if x["id"] != "NATIVE03-VALIDATION-004"]
    data["validation"].append({
        "id": "NATIVE03-VALIDATION-004", "kind": "audit_custody_and_coverage_consistency",
        "command": ".venv\\Scripts\\python.exe -X utf8 dag/reviews/additional_native_systems_03_finalize.py",
        "result": "99 new full-source assessments; 153 distinct cumulative full-source assessments; zero unread in the original 153-file scope. All working-byte SHA256 values match their reports; all 153 source files match pinned Git blobs modulo CRLF checkout normalization only.",
        "source_commit": h.COMMIT, "checkout_crlf_file_count": len(checkout_crlf),
        "status": "completed", "exit_code": 0, "valid_evidence_references": evidence_count,
        "physical_line_count_corrections": corrections,
        "limitations": ["Consistency/hash verification does not itself constitute semantic review.", "Literal U+2028 and U+0085 inside JSON strings are not physical LF source lines; both affected source strings were reread without splitting/eliding those characters.", "Scoped source-reading completion does not mean tests all pass or mathematical/scientific claims are proved."]
    })
    independence = next(row for row in data["file_reviews"] if row["path"].endswith("/python_independence_v1.json"))
    independence["assessment"] = independence["assessment"].replace(
        "Literal U+2028/U+E0001 case was reread after correcting display splitting; no source changed.",
        "Literal U+2028/U+E0001 and U+0085 cases were reread after correcting display splitting; the file has 1,750 physical LF-delimited lines, not 1,752 Unicode splitlines segments. No source changed.")
    data["status"] = "complete_scoped_source_review"
    data["method"] = (
        "All 99 files received complete source inspection and an individual substantive assessment; "
        "the preceding two reports account for the other 54 distinct files. Hashing/parsing was not promoted "
        "to semantic review. Large pretty-printed JSON fixtures were read in consecutive source chunks with "
        "only indentation and external newlines compacted: every key, value, numeric lexeme, digest and "
        "string remained visible. Literal U+2028 was preserved with LF-only chunking. Source hashes identify "
        "working bytes; git_blob_sha256 additionally identifies pinned Git content for these 99 files. "
        "Generated capacity wrappers were inspected but do not certify their enclosing algorithms. "
        "All conclusions are implementation checks, bounded counterexamples or explicit proof obligations; "
        "no incoming pilots or private benchmark content was inspected."
    )
    data["remaining_work"] = {
        "unread_paths": [],
        "scoped_source_review": "complete for the 153 files inherited from additional_native_systems.json",
        "repair_backlog": [finding["id"] for finding in data["findings"]],
        "proof_and_empirical_obligations": [
            "Authenticate replay/admission custody at owning boundaries; define which supplied metadata remains trusted input.",
            "Prove operadic laws over explicitly chosen term equivalence and executable semantics where claimed; do not infer Koszul/homology properties from names or inventories.",
            "Specify validated rational/integer domains and overflow/refusal behavior, including public DTO bypasses.",
            "Measure detector accuracy and independent-source adequacy on governed held-out material through authorized owners; none was accessed in this audit.",
            "Separate finite selection/fitness/scalar descent from semantic improvement, convergence and autonomy claims.",
            "Address prior broad-test compile/failure outcomes recorded in additional_native_systems.json and additional_native_systems_02.json before any passing-suite claim.",
            "The parent-owned broader repository audit and its non-native unread backlog remain open."
        ]
    }
    h.save(data)
    print(json.dumps({"coverage": data["coverage"], "claims": len(data["claims"]),
                      "findings": len(data["findings"]), "checkout_crlf_files": len(checkout_crlf),
                      "line_corrections": corrections}, indent=2))


if __name__ == "__main__":
    main()
