"""Read-only, offline Paper 001 artifact checks; writes only this audit's receipt.

No provider imports, subprocesses, credential reads, or source modifications.
The public Paper 001 traces are data, never instructions or executable code.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / "dag/reviews"
BASE = "papers/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/"
PKG = ROOT / BASE
SUPPORT = json.loads((REV / "additional_paper_001_support.json").read_text())
CUSTODY = json.loads((REV / "additional_paper_001_custody.json").read_text())
SCOPE = SUPPORT["remaining_scope"]


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def read_json(path: str):
    return json.loads((PKG / path).read_text(encoding="utf-8"))


def jsonl(path: str):
    return [json.loads(x) for x in (PKG / path).read_text(encoding="utf-8").splitlines() if x.strip()]


pins = []
for item in SCOPE:
    b = (ROOT / item["path"]).read_bytes()
    assert digest(b) == item["sha256"], item["path"]
    assert len(b) == item["bytes"], item["path"]
    pins.append({**item, "pin_matches": True, "lines": None if item["path"].endswith(".zip") else len(b.splitlines())})
for item in SUPPORT["file_reviews"]:
    assert digest((ROOT / item["path"]).read_bytes()) == item["sha256"], item["path"]
assert digest((PKG / "paper.md").read_bytes()) == "928e66a795e17f3c5bc2a9c688de3e97ee9beed85e4a548987154b857cc0d89f"

zip_path = next(x["path"] for x in SCOPE if x["path"].endswith(".zip"))
with zipfile.ZipFile(ROOT / zip_path) as z:
    assert z.testzip() is None
    names = z.namelist()
    assert len(names) == len(set(names)) == 97
    assert all(not PurePosixPath(x).is_absolute() and ".." not in PurePosixPath(x).parts for x in names)
    archived = {n: z.read(n) for n in names}
prefix = names[0].split("/")[0] + "/"
assert all(n.startswith(prefix) for n in names)

# Reconstruct every old normalized text from the reviewed current base and all
# reverse unified-diff hunks. This checks that the displayed diff omitted nothing.
diff_path = REV / "paper_001_support_inspection/archive_complete_text_diffs.txt"
diff_text = diff_path.read_text(encoding="utf-8")
sections = {}
for section in re.split(r"(?m)(?=^--- archive/)", diff_text):
    if not section.strip():
        continue
    rows = section.splitlines()
    old = rows[0][len("--- archive/"):]
    new = rows[1][len("+++ current/"):]
    sections[old] = (new, rows[2:])


def reverse_diff(current: str, rows: list[str]) -> str:
    source = current.splitlines()
    result, pos, i = [], 0, 0
    while i < len(rows):
        if not rows[i].startswith("@@"):
            assert rows[i] == "", rows[i]
            i += 1
            continue
        m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", rows[i])
        assert m, rows[i]
        start = int(m[3]) - 1
        assert start >= pos
        result.extend(source[pos:start])
        pos = start
        i += 1
        old_count = new_count = 0
        while i < len(rows) and not rows[i].startswith("@@"):
            line = rows[i]
            if line == "":
                # blank separator between file sections, not a context line
                i += 1
                continue
            if line[0] in " +":
                assert source[pos] == line[1:], (pos, source[pos], line)
                pos += 1
                new_count += 1
            if line[0] in " -":
                result.append(line[1:])
                old_count += 1
            assert line[0] in " +-", line
            i += 1
        assert old_count == int(m[2] or 1)
        assert new_count == int(m[4] or 1)
    result.extend(source[pos:])
    return "\n".join(result) + ("\n" if current.endswith("\n") else "")


members = []
custody_by_name = {x["member"]: x for x in CUSTODY["archive_members"]}
for name, data in archived.items():
    old = name[len(prefix):]
    row = custody_by_name[name]
    cur = (ROOT / row["current_path"]).read_bytes()
    assert digest(data) == row["sha256"]
    assert digest(cur) == row["current_sha256"]
    raw_equal = data == cur
    binary = old.endswith((".pdf", ".png"))
    lf_equal = None if binary else lf(data) == lf(cur)
    assert raw_equal == row["current_raw_equal"]
    assert lf_equal == row["current_lf_equal"]
    reverse_ok = None
    if not binary and not lf_equal:
        new, hunks = sections[old]
        assert row["current_path"] == BASE + new
        reconstructed = reverse_diff(lf(cur).decode("utf-8"), hunks).encode("utf-8")
        reverse_ok = reconstructed == lf(data)
        assert reverse_ok, name
    members.append({"member": name, "sha256": digest(data), "bytes": len(data),
                    "current_path": row["current_path"], "current_sha256": digest(cur),
                    "current_raw_equal": raw_equal, "current_lf_equal": lf_equal,
                    "normalized_sha256": None if binary else digest(lf(data)),
                    "lines": None if binary else len(data.splitlines()),
                    "reverse_diff_reconstructs_full_archive_text": reverse_ok})
assert len(sections) == sum(x["reverse_diff_reconstructs_full_archive_text"] is True for x in members)

manifests = []
for filename in ("MANIFEST.sha256", "SHA256SUMS"):
    for location in ("current", "archive"):
        data = (PKG / filename).read_bytes() if location == "current" else archived[prefix + filename]
        entries = []
        seen = set()
        for line in data.decode().splitlines():
            expected, rel = line.split("  ", 1)
            assert re.fullmatch(r"[a-f0-9]{64}", expected)
            assert rel not in seen
            seen.add(rel)
            assert not PurePosixPath(rel).is_absolute() and ".." not in PurePosixPath(rel).parts
            target = (PKG / rel).read_bytes() if location == "current" else archived[prefix + rel]
            normalized = target if rel.endswith((".pdf", ".png")) else lf(target)
            entries.append({"path": rel, "expected": expected, "raw_matches": digest(target) == expected,
                            "lf_matches": digest(normalized) == expected})
        manifests.append({"manifest": filename, "location": location, "entries": entries,
                          "total": len(entries), "raw_mismatches": sum(not x["raw_matches"] for x in entries),
                          "lf_mismatches": sum(not x["lf_matches"] for x in entries)})

# Dependency edges are metadata only; no Cargo execution or registry lookup.
lock = tomllib.loads((PKG / "code/rust/Cargo.lock").read_text())
packages = lock["package"]
unresolved = []
for package in packages:
    for dep in package.get("dependencies", []):
        parts = dep.split()
        matches = [p for p in packages if p["name"] == parts[0] and (len(parts) == 1 or p["version"] == parts[1])]
        if len(matches) != 1:
            unresolved.append({"package": package["name"], "dependency": dep, "matches": len(matches)})
assert not unresolved
assert all(re.fullmatch(r"[a-f0-9]{64}", p["checksum"]) for p in packages if "source" in p)

trace_rows = {}
for item in pins:
    if item["path"].endswith(".jsonl"):
        rel = item["path"][len(BASE):]
        rows = jsonl(rel)
        trace_rows[rel] = {"records": len(rows), "statuses": dict(Counter(x.get("status", x.get("terminal_state")) for x in rows)),
                           "reported_input_tokens": sum(x.get("in_tokens", 0) for x in rows),
                           "reported_output_tokens": sum(x.get("out_tokens", 0) for x in rows),
                           "token_fields_records": sum("in_tokens" in x and "out_tokens" in x for x in rows)}

debate = jsonl("results/demo2_r7_adversarial_debate_1790210039.jsonl")
receipt = read_json("results/demo2_r7_adversarial_debate_receipt.json")
assert (PKG / "results/receipt.json").read_bytes() == (PKG / "results/demo2_r7_adversarial_debate_receipt.json").read_bytes()
labels = [x["proposer_hallucination"] for x in debate]
challenge = [x["adversary_critique"]["adversary_verdict"] == "CHALLENGE" for x in debate]
tp = sum(a and b for a, b in zip(labels, challenge))
fp = sum(not a and b for a, b in zip(labels, challenge))
tn = sum(not a and not b for a, b in zip(labels, challenge))
fn = sum(a and not b for a, b in zip(labels, challenge))
assert (tp, fp, tn, fn) == (6, 2, 2, 0)
assert Fraction(tp, tp + fp) == Fraction(3, 4)
assert Fraction(tp, tp + fn) == 1
assert Fraction(tp + tn, len(debate)) == Fraction(4, 5)
for row, rec in zip(debate, receipt["trials"]):
    assert (row["lattice_key"], row["u_val"], row["proposer_hallucination"], row["adversary_critique"]["adversary_verdict"]) == (rec["lattice"], rec["U_over_t"], rec["historical_hallucination_label"], rec["adversary_verdict"])
trace_bytes = (PKG / "results/demo2_r7_adversarial_debate_1790210039.jsonl").read_bytes()
assert receipt["source_trace_sha256"] == digest(lf(trace_bytes))
assert receipt["source_trace_sha256"] != digest(trace_bytes)

# Small exact countercontrols concern assertions in public historical text only.
chain_edges = {frozenset((0, 1)), frozenset((1, 2)), frozenset((2, 3))}
swap = {0: 1, 1: 0, 2: 3, 3: 2}
mapped_middle = frozenset((swap[1], swap[2]))
assert mapped_middle not in chain_edges
cycle_map = debate[2]["proposer_move"]["xi_witness"]["mapping"]
cycle_failures = [x for x in cycle_map if cycle_map[cycle_map[x]] != x]
assert len(cycle_failures) == 5
reflection = debate[4]["proposer_move"]["xi_witness"]["mapping"]
assert reflection["site_2"] == "site_2"
bad_kagome = debate[8]["proposer_move"]["xi_witness"]["mapping"]
assert len(set(bad_kagome.values())) < len(bad_kagome)

# Compare retained receipt bindings to this edition; mismatches do not refute an
# earlier execution. Unavailable outside-package paths stay uninspected.
bindings = []
def record_binding(owner: str, field: str, path: str, expected: str):
    rel = path
    if "001_the_symbol_game/" in rel:
        rel = rel.split("001_the_symbol_game/", 1)[1]
    elif "001_the_symbol_game_discrete_cochain_retraction_and_toy_involutions/" in rel:
        rel = rel.split("001_the_symbol_game_discrete_cochain_retraction_and_toy_involutions/", 1)[1]
    rel = rel.replace("_lev_landau_theoretical_minimum_quiz/", "_lev_examiner_theoretical_minimum_quiz/")
    if (PKG / rel).is_file():
        b = (PKG / rel).read_bytes()
        normalized = b if rel.endswith((".pdf", ".png")) else lf(b)
        bindings.append({"receipt": owner, "field": field, "recorded_path": path, "current_path": BASE + rel,
                         "expected": expected, "raw_matches": digest(b) == expected, "lf_matches": digest(normalized) == expected})
    else:
        bindings.append({"receipt": owner, "field": field, "recorded_path": path, "expected": expected, "disposition": "outside_package_or_not_present; not read"})

for rel in [x["path"][len(BASE):] for x in pins if x["path"].endswith(".json") and ("/docs/" in x["path"] or x["path"].endswith("/review_validation.json"))]:
    obj = read_json(rel)
    for field in ("selected_test_input_sha256", "candidate_asset_sha256", "executed_file_sha256", "sha256"):
        for p, h in obj.get(field, {}).items():
            record_binding(rel, field, p, h)
    for p, h in obj.get("lean", {}).get("protected_source_sha256", {}).items() if isinstance(obj.get("lean"), dict) else []:
        record_binding(rel, "lean.protected_source_sha256", p, h)
    for test in obj.get("tests", []):
        if "test_source_sha256" in test:
            p = next(x for x in test["command"] if x.startswith("code/tests/"))
            record_binding(rel, "tests.test_source_sha256", p, test["test_source_sha256"])

result = {
    "source_commit": SUPPORT["source_commit"], "source_modifications": 0, "provider_calls": 0,
    "native_executions": 0, "network_calls": 0, "pins": pins,
    "support_base_pins_rechecked": len(SUPPORT["file_reviews"]),
    "archive": {"path": zip_path, "sha256": digest((ROOT / zip_path).read_bytes()),
                "crc_check": "pass", "unique_safe_members": len(members), "members": members,
                "raw_equal_members": sum(x["current_raw_equal"] for x in members),
                "lf_only_equal_members": sum(not x["current_raw_equal"] and x["current_lf_equal"] is True for x in members),
                "full_text_delta_members": len(sections), "diff_lines": len(diff_text.splitlines()),
                "diff_sha256": digest(diff_path.read_bytes()), "all_reverse_diffs_reconstruct": True},
    "manifests": manifests,
    "cargo_lock": {"format_version": lock["version"], "package_count": len(packages),
                   "registry_packages": sum("source" in p for p in packages),
                   "local_packages": [p["name"] for p in packages if "source" not in p],
                   "all_declared_dependency_edges_resolve_inside_lock": True,
                   "registry_checksum_syntax_valid": True,
                   "limit": "No registry authentication, dependency source review, Cargo build, or guarantee of local path contents."},
    "traces": trace_rows,
    "debate_receipt": {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "precision": "3/4", "recall": "1", "accuracy": "4/5",
                       "raw_caught_am_true": sum(x["adversary_caught_am"] for x in debate),
                       "duplicate_receipt_exact_equal": True, "source_hash_matches_raw": False, "source_hash_matches_lf": True,
                       "limits": "Agreement against historical labels only. Current replay statuses inherited from parent fresh replay, not reexecuted here."},
    "countercontrols": [
        {"id": "IDENTITY-HAS-FIXED-POINT", "carrier": [0], "xi": {"0": 0}, "fixed_point_free": False},
        {"id": "CHAIN-SWAP-NOT-AUTOMORPHISM", "edge": [1, 2], "image": sorted(mapped_middle), "image_is_edge": False},
        {"id": "C5-ROTATION-NOT-INVOLUTION", "failed_vertices": cycle_failures},
        {"id": "C5-REFLECTION-FIXED-POINT", "fixed_vertex": "site_2"},
        {"id": "KAGOME-PROPOSAL-NOT-BIJECTION", "image_count": len(set(bad_kagome.values())), "domain_count": len(bad_kagome)},
    ],
    "historical_receipt_bindings_to_current_edition": bindings,
    "evidence_ceiling": "Exact local artifact custody, complete diff reconstruction, source-bound historical arithmetic and elementary finite countercontrols. No historical execution authentication or general physics/model-performance conclusion."
}
(REV / "additional_paper_001_artifact_checks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"scope_pins": len(pins), "archive_members": len(members), "reverse_diff_members": len(sections), "diff_lines": len(diff_text.splitlines()), "cargo_packages": len(packages), "trace_records": sum(x["records"] for x in trace_rows.values()), "receipt_bindings": len(bindings)}, indent=2))
