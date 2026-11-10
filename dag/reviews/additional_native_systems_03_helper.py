"""Audit ledger maintenance only; never infers semantic review from parsing.

Human/agent assessments must be supplied after source inspection. This script
records them, checks source custody, and regenerates checkpoint counts.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).with_name("additional_native_systems_03.json")
COMMIT = "8050c66900899771766f33e8f5fdd200b7dd9120"


def load():
    if REPORT.exists():
        return json.loads(REPORT.read_text(encoding="utf-8"))
    old = json.loads(REPORT.with_name("additional_native_systems_02.json").read_text(encoding="utf-8"))
    rows = [dict(x) for x in old["file_reviews"] if not x["full_source_read"]]
    return dict(schema="pfp.additional-native-systems-audit.v1", source_commit=COMMIT,
                status="in_progress", claims=[], findings=[], validation=[], file_reviews=rows,
                remaining_work={}, method="Every source line must be inspected before a full-read assessment. Hashing/parsing does not count as substantive review. Generated capacity wrappers are inspected but do not certify the enclosing algorithm. No incoming pilots or private benchmark content is in scope.")


def save(data):
    rows = data["file_reviews"]
    unread = [x["path"] for x in rows if not x["full_source_read"]]
    data["remaining_work"]["unread_paths"] = unread
    data["coverage"] = dict(this_phase_scope=99, new_full_files=99-len(unread),
                            new_full_lines=sum(x["line_count"] for x in rows if x["full_source_read"]),
                            cumulative_full_files=153-len(unread), total_scope=153, unread_files=len(unread))
    REPORT.write_text(json.dumps(data, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    coverage=data["coverage"]
    summary=["# Additional native systems audit — phase 03", "",
             f"Pinned source: `{COMMIT}`. Status: **{data['status']}**.", "",
             f"This phase: **{coverage['new_full_files']}/99 files**, **{coverage['new_full_lines']} lines** fully read. Cumulative native coverage: **{coverage['cumulative_full_files']}/153**. **{len(unread)} remain unread**.", "",
             data["method"], "", "The JSON contains exact hashes, reviewed ranges, per-file assessments and the complete unread backlog. Tests are not claimed rerun merely because their source was read.", ""]
    for finding in data["findings"]:
        summary.append(f"- **{finding['id']}: {finding['title']}** — {finding.get('observation','')}")
    summary.extend(["", "The sealing finding concerns the kernel public constructor. No cryptographic forgery or deployed-host bypass was demonstrated.", "", "Validation: twelve public synthetic counterexamples reproduced in two fresh Rust probe runs; one focused existing test passed (37 filtered out). The JSON records the corrected overflow control and the disproved protected-span suspicion. Earlier broad runs and their failures remain in the preceding reports; they were not silently rerun or upgraded.", ""])
    summary.extend(["No production fixes, paid calls, private benchmark access or imported-pilot review occurred. " +
                    ("The scoped native source review remains active until the unread list is empty." if unread else
                     "The 153-file native source review is complete. The broader repository audit, repairs, universal proofs and empirical adequacy obligations remain open."), ""])
    REPORT.with_suffix('.md').write_text('\n'.join(summary),encoding='utf-8')


def record(assessments):
    data=load()
    index={x["path"]:x for x in data["file_reviews"]}
    for path, assessment in assessments.items():
        row=index[path]
        content=(ROOT/path).read_bytes()
        assert hashlib.sha256(content).hexdigest()==row["sha256"], path
        row.update(full_source_read=True, reviewed_lines=[[1,row["line_count"]]], assessment=assessment)
    save(data)
    return data["coverage"]


def display_json_source(path, start=1, count=1000):
    """Display EVERY lexical token; remove only indentation/newlines outside strings.

    For these pretty-printed JSON fixtures every quoted string is on one source
    line. This is a reading aid, not a parse or coverage assertion. Line groups
    remain mapped to original source; no keys/values/digests are elided.
    """
    # splitlines() would split legal literal U+2028 inside JSON strings.
    source=(ROOT/path).read_text(encoding="utf-8")
    lines=source.split('\n')
    if lines and lines[-1]=='':
        lines.pop()
    for offset in range(start-1, min(len(lines), start-1+count), 100):
        end=min(offset+100, len(lines), start-1+count)
        print(f"LINES {offset+1}-{end}: "+''.join(line.strip(' \t\r') for line in lines[offset:end]))


if __name__ == "__main__":
    save(load())
    print(json.dumps(load()["coverage"], indent=2))
