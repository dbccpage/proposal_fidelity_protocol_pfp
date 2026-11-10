"""Frozen original inventory and bounded read helper for Paper 004."""
import hashlib
import json
import sys
import tarfile
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = "additional_paper_004"
SOURCE = "papers/pfp/004_pfp_native_verification_and_evidence_custody/"
OUT = HERE / (PREFIX + "_inspection")
OUT.mkdir(exist_ok=True)

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def freeze():
    inventory = json.loads((ROOT / "dag/file_inventory.json").read_text(encoding="utf-8"))
    coverage = json.loads((HERE / "coverage.json").read_text(encoding="utf-8"))
    statuses = {r["path"]: r for r in coverage["files"]}
    files, excluded = [], []
    for row in inventory["files"]:
        if not row["path"].startswith(SOURCE):
            continue
        raw = (ROOT / row["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["sha256"], row["path"]
        item = {"path": row["path"], "sha256": row["sha256"], "bytes": len(raw),
                "coverage_at_freeze": statuses[row["path"]]["substantive_status"]}
        if item["coverage_at_freeze"] == "full_text_source_review_recorded":
            item["prior_reading_receipts"] = statuses[row["path"]]["reading_receipts"]
            excluded.append(item)
        else:
            try:
                item["lines"] = len(raw.decode("utf-8").splitlines())
            except UnicodeDecodeError:
                item["lines"] = None
            files.append(item)
    target = HERE / (PREFIX + "_support_scope.json")
    assert not target.exists(), "Do not replace the frozen scope"
    result = {"source_commit": inventory["local_head"], "inventory_path": "dag/file_inventory.json",
              "inventory_sha256": hashlib.sha256((ROOT / "dag/file_inventory.json").read_bytes()).hexdigest(),
              "coverage_sha256_at_freeze": hashlib.sha256((HERE / "coverage.json").read_bytes()).hexdigest(),
              "files": files, "excluded_prior_full_reads": excluded}
    write(target, result)
    print(json.dumps({"frozen": len(files), "excluded_full": len(excluded), "bytes": sum(r["bytes"] for r in files), "text_lines": sum(r["lines"] or 0 for r in files)}))

def read(names):
    scope = json.loads((HERE / (PREFIX + "_support_scope.json")).read_text(encoding="utf-8"))
    allowed = {r["path"]: r for r in scope["files"] + scope["excluded_prior_full_reads"]}
    ledger_path = HERE / (PREFIX + "_read_ledger.json")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
    for arg in names:
        name, sep, ranges = arg.partition("::")
        path = SOURCE + name
        raw = (ROOT / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == allowed[path]["sha256"]
        lines = raw.decode("utf-8").splitlines()
        start, end = map(int, ranges.split("-")) if sep else (1, len(lines))
        assert (start == 1 and end == 0) or 1 <= start <= end <= len(lines)
        print("\nFILE", path, "SHA256", allowed[path]["sha256"], "LINES", len(lines))
        for n in range(start, end + 1): print(f"{n}: {lines[n-1]}")
        ledger.append({"path": path, "sha256": allowed[path]["sha256"], "reviewed_lines": [[start,end]] if end else [], "source_lines": len(lines), "output_truncated": False})
    write(ledger_path, ledger)

def archives():
    result = []
    for path in sorted((ROOT / SOURCE).rglob("*")):
        if not path.is_file() or not (path.name.endswith(".zip") or path.name.endswith(".tar.gz")):
            continue
        if path.name.endswith(".zip"):
            with zipfile.ZipFile(path) as z:
                members = [{"name": m.filename, "bytes": m.file_size, "compressed_bytes": m.compress_size, "is_dir": m.is_dir()} for m in z.infolist()]
        else:
            with tarfile.open(path, "r:gz") as t:
                members = [{"name": m.name, "bytes": m.size, "is_file": m.isfile(), "is_link": m.issym() or m.islnk()} for m in t.getmembers()]
        item = {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "members": members}
        result.append(item)
        print(json.dumps({"archive": item["path"], "members": len(members), "bytes": sum(m["bytes"] for m in members), "top_roots": dict(Counter('/'.join(m['name'].split('/')[:3]) for m in members)), "extensions": dict(Counter(Path(m['name']).suffix for m in members))}))
    write(OUT / "archive_inventory.json", result)

if __name__ == "__main__":
    if sys.argv[1] == "freeze": freeze()
    elif sys.argv[1] == "read": read(sys.argv[2:])
    elif sys.argv[1] == "archives": archives()
    else: raise SystemExit("unknown command")
