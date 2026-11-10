"""Persist only completed Paper 004 body assessments; pending scope stays explicit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = "additional_paper_004"
SOURCE = "papers/pfp/004_pfp_native_verification_and_evidence_custody/"
scope = json.loads((HERE / (PREFIX + "_support_scope.json")).read_text(encoding="utf-8"))
rows = {r["path"]: r for r in scope["files"]}
notes = {}
for p in sorted(HERE.glob(PREFIX + "_notes*.json")):
    notes.update(json.loads(p.read_text(encoding="utf-8")))
read = {}
for entry in json.loads((HERE / (PREFIX + "_read_ledger.json")).read_text(encoding="utf-8")):
    if entry.get("output_truncated"):
        continue
    read.setdefault(entry["path"], set()).update(n for a,b in entry["reviewed_lines"] for n in range(a,b+1))
reviews = []
for name, assessment in notes.items():
    path = SOURCE + name
    row = rows[path]
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == row["sha256"]
    assert read.get(path,set()) == set(range(1,row["lines"]+1)), path
    reviews.append({"path":path,"sha256":row["sha256"],"full_source_read":True,"reviewed_lines":[[1,row["lines"]]] if row["lines"] else [],"assessment":assessment})
remaining = [p for p in rows if p not in {r["path"] for r in reviews}]
report = {"schema_version":"1.0","status":"in_progress" if remaining else "scope_complete","source_commit":scope["source_commit"],"scope_manifest":"dag/reviews/"+PREFIX+"_support_scope.json","file_reviews":sorted(reviews,key=lambda r:r["path"]),"remaining_scope":remaining,"claims":[],"findings":[],"archive_member_dispositions":[],"validation":[],"test_summary":{"fresh_tests":0,"native_build_performed":False},"provider_calls":0,"private_answer_access":False,"limits":["Checkpoint; all pending paths remain open.","Source reading does not establish formal execution; historical receipts remain historical.","7,875-member source tar requires explicit bounded custody and claim-owner disposition; metadata inventory is not full semantic reading."]}
(HERE/(PREFIX+"_support.json")).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
(HERE/(PREFIX+"_support.md")).write_text(f"# Paper 004 support audit\n\nCheckpoint: {len(reviews)}/{len(rows)} complete source bodies; {len(remaining)} pending paths.\n\nSource bytes preserved. Historical receipts are not fresh test evidence. Archive metadata is not substantive member review.\n",encoding="utf-8")
print(json.dumps({"full_body_files":len(reviews),"scope":len(rows),"pending":len(remaining)}))
