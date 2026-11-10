"""Tracked-file structural audit. This is not full semantic source review.

Reads only assigned tracked non-dot-directory source/corpus files. Does not open
private benchmark storage or answer keys, execute corpus instructions, or solve
any benchmark. Existing human full-source review labels survive only hash match.
"""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "dag/reviews/systems_audit.json"
CLAIM_WORDS = re.compile(
    r"\b(proof|theorem|certif\w*|invariant\w*|associativ\w*|equivarian\w*|"
    r"sound\w*|complet\w*|independen\w*|contractiv\w*|admi\w*|"
    r"authorit\w*|witness\w*|refus\w*|exact\w*|residual\w*)\b", re.I
)
FENCE_WORDS = re.compile(r"\b(no|not|never|only|finite|bounded|unknown|unmeasured|provisional|outside|pending|requires?)\b", re.I)
DECLARATIONS = re.compile(
    r"^(operad_\w+|invocation|authority_effect|AuthorityEffect|status|schema_version|name|description):\s*(.*)$"
)


def source_structure(text: str) -> dict:
    tree = ast.parse(text)
    functions = []
    imports = []
    classes = []
    raises = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append({"line": node.lineno, "module": getattr(node, "module", None), "names": [a.name for a in node.names]})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({"name": node.name, "line": node.lineno, "end_line": node.end_lineno, "parameters": [a.arg for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)], "docstring": ast.get_docstring(node)})
        elif isinstance(node, ast.ClassDef):
            classes.append({"name": node.name, "line": node.lineno, "end_line": node.end_lineno, "docstring": ast.get_docstring(node)})
        elif isinstance(node, ast.Raise):
            raises.append(node.lineno)
    return {"parse": "ok", "module_docstring": ast.get_docstring(tree), "classes": classes, "functions": functions, "imports": imports, "assert_count": sum(isinstance(n, ast.Assert) for n in ast.walk(tree)), "raise_lines": raises, "test_functions": [f["name"] for f in functions if f["name"].startswith("test_")]}


def data_structure(value: object) -> dict:
    schemas, statuses, authorities, keys = Counter(), Counter(), Counter(), Counter()
    node_count = 0
    stack = [value]
    while stack:
        node = stack.pop()
        node_count += 1
        if isinstance(node, dict):
            for key, val in node.items():
                keys[str(key)] += 1
                if isinstance(val, (str, int, bool)):
                    if key in ("schema", "schema_version", "$schema"): schemas[str(val)] += 1
                    if key in ("status", "verdict", "outcome", "custody", "admission_status"): statuses[str(val)] += 1
                    if key in ("authority_effect", "AuthorityEffect"): authorities[str(val)] += 1
                stack.append(val)
        elif isinstance(node, list):
            stack.extend(node)
    return {"parse": "ok", "top_type": type(value).__name__, "top_keys": sorted(value) if isinstance(value, dict) else [], "top_items": len(value) if isinstance(value, (list, dict)) else None, "node_count": node_count, "schemas": dict(schemas), "status_counts": dict(statuses), "authority_counts": dict(authorities), "field_counts": dict(keys)}


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    previous = {r["path"]: r for r in report["files"]}
    paths = subprocess.check_output(["git", "ls-files", "eis", "pciv", "operads"], cwd=ROOT, text=True).splitlines()
    paths = [p for p in paths if not any(part.startswith(".") for part in Path(p).parts[:-1])]
    records = []
    summary = {"extensions": Counter(), "parse_errors": [], "corpus_kinds": Counter()}
    for rel in sorted(paths):
        path = ROOT / rel
        if re.search(r"(^|[/_-])(private|answer[_-]?key)([/_.-]|$)", rel, re.I):
            records.append({"path": rel, "review_level": "excluded_private_material", "content_read": False})
            continue
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        prior = previous.get(rel, {})
        full = prior.get("review_level") == "full_source_read" and prior.get("sha256") == digest
        record = {"path": rel, "bytes": len(raw), "sha256": digest, "review_level": "full_source_read" if full else "structured_content_scan", "content_read": True, "semantic_full_review": full}
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            record.update(review_level="binary_metadata_only", content_read=False, semantic_full_review=False)
            records.append(record)
            continue
        lines = text.splitlines()
        record["lines"] = len(lines)
        record["reviewed_line_ranges"] = [[1, len(lines)]] if full else []
        record["mechanically_scanned_line_ranges"] = [[1, len(lines)]]
        record["candidate_claim_lines"] = [i for i,l in enumerate(lines,1) if CLAIM_WORDS.search(l)]
        record["candidate_limit_lines"] = [i for i,l in enumerate(lines,1) if CLAIM_WORDS.search(l) and FENCE_WORDS.search(l)]
        suffix = path.suffix.lower()
        summary["extensions"][suffix] += 1
        kind = "unparsed"
        try:
            if suffix == ".py":
                record["structure"] = source_structure(text)
                kind = "tests" if "/tests/" in rel or path.name.startswith("test_") else "implementation"
            elif suffix in (".json", ".ipynb"):
                record["structure"] = data_structure(json.loads(text))
                kind = "notebook" if suffix == ".ipynb" else "receipt_data" if "/receipts/" in rel else "catalog_data"
            elif suffix == ".jsonl":
                record["structure"] = data_structure([json.loads(l) for l in lines if l.strip()])
                kind = "receipt_data"
            else:
                record["structure"] = {"headings": [{"line": i, "text": l} for i,l in enumerate(lines,1) if l.startswith("#")], "declarations": [{"line":i,"field":m.group(1),"value":m.group(2)} for i,l in enumerate(lines,1) if (m:=DECLARATIONS.match(l))]}
                kind = "skill_instruction" if "/skills/" in rel else "rule" if "/rules/" in rel else "pattern" if "/patterns/" in rel else "documentation_or_other"
            record["corpus_kind"] = kind
            summary["corpus_kinds"][kind] += 1
        except (SyntaxError, ValueError, TypeError) as exc:
            record["structure"] = {"parse": "error", "error": str(exc)}
            summary["parse_errors"].append({"path":rel,"error":str(exc)})
        if "/receipts/" in rel:
            record["evidence_ceiling"] = "Historical stored record; neither execution nor source correctness is established by parsing it."
        elif "/tests/" in rel:
            record["evidence_ceiling"] = "Test source scanned; assertions and names are not execution results or general proof."
        elif kind in ("skill_instruction", "rule", "pattern", "catalog_data"):
            record["evidence_ceiling"] = "Declared protocol, rule or catalog payload; not automatically enforced and not a mathematical proof."
        else:
            record["evidence_ceiling"] = "Full semantic review recorded separately; parsing and claim keyword extraction do not establish correctness."
        records.append(record)
    report["files"] = records
    report["coverage"] = dict(Counter(r["review_level"] for r in records))
    report["tracked_scope_counts"] = dict(Counter(r["path"].split("/")[0] for r in records))
    report["structural_scan"] = summary
    report["review_level_definitions"].update({"structured_content_scan":"All UTF-8 content mechanically read, parsed or structurally scanned; declarations/dependencies/candidate claim lines recorded. Not full semantic review.","binary_metadata_only":"Bytes read solely for identity and size; binary semantics not reviewed."})
    report["source_snapshot"].update(current_head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(), scope="Git tracked files below eis/, pciv/, operads/ excluding dot-prefixed directories; ignored caches omitted.")
    REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
    print(json.dumps({"coverage":report["coverage"],"tracked_scope_counts":report["tracked_scope_counts"],"parse_errors":summary["parse_errors"],"corpus_kinds":summary["corpus_kinds"]},indent=2))


if __name__ == "__main__":
    main()
