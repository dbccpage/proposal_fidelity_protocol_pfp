"""Lossless reading aid/custody ledger for public imported pilot catalog capsules.

No dispatch, solver, benchmark, private storage or pilot writes. A generated
diff is only a reading aid; an assessment still requires inspecting it.
"""
from pathlib import Path
import difflib
import hashlib
import json
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "pilots/anomalon_woland"
TEMPLATE = BASE / "pilot_0000102"
OUT = Path(__file__).with_name("numbered_102_152_reads.json")


def info(number):
    folder = BASE / f"pilot_{number:07d}"
    seed = yaml.safe_load((folder / "seed.yaml").read_text(encoding="utf-8"))
    spec = yaml.safe_load((folder / "spec.yaml").read_text(encoding="utf-8"))
    prompt = seed["seed_prompt"]
    readme = (folder / "README.md").read_text(encoding="utf-8")
    mine = yaml.safe_load((folder / "misc/cot_mine.yaml").read_text(encoding="utf-8"))
    catalog_id = re.search(r" — ([CG]\d+) ", readme.split("\n")[0]).group(1)
    return {
        "number": number, "pilot_id": folder.name, "prompt_id": spec["prompt_id"],
        "catalog_id": catalog_id, "title": prompt.split("\n")[0],
        "summary": re.search(r"^Catalog summary: (.*)$", prompt, re.M).group(1),
        "source_markdown": re.search(r"^Source citation: (.*)$", prompt, re.M).group(1),
        "task_family": seed["task_family"], "checker_id": spec["host_gate"]["checker_id"],
        "historical_catalog_status": re.search(r"historic catalog status (.*?);", seed["expected_outcome"]["answer"]).group(1),
        "taxonomy_statement": readme.split("\n")[17],
        "source_presence_note": prompt.split("\n")[-2],
        "spec_file_present_recorded": mine["layout_index"]["capsules"][0]["spec_file_present"],
    }


def replacements(meta):
    baseline = info(102)
    keys = ["pilot_id", "prompt_id", "catalog_id", "title", "summary", "source_markdown", "task_family", "checker_id", "taxonomy_statement", "source_presence_note"]
    pairs = {baseline[k]: meta[k] for k in keys if baseline[k] != meta[k]}
    if meta["catalog_id"] != baseline["catalog_id"]:
        pairs[baseline["catalog_id"].lower()] = meta["catalog_id"].lower()
    if meta["historical_catalog_status"] != baseline["historical_catalog_status"]:
        pairs["historic catalog status " + baseline["historical_catalog_status"]] = "historic catalog status " + meta["historical_catalog_status"]
        pairs["Historic catalog status `" + baseline["historical_catalog_status"] + "`"] = "Historic catalog status `" + meta["historical_catalog_status"] + "`"
        pairs["historic catalog status `" + baseline["historical_catalog_status"] + "`"] = "historic catalog status `" + meta["historical_catalog_status"] + "`"
    if not meta["spec_file_present_recorded"]:
        pairs["was present when this layout was written."] = "was absent when this layout was written."
        pairs["Spec file present."] = "Spec file absent."
        pairs["spec_file_present: true"] = "spec_file_present: false"
    return pairs


def inspect(start, end):
    manifest = json.loads((ROOT / "dag/migrations/anomalon_pilots_move.json").read_text(encoding="utf-8"))
    custody = {row["path"]: row for row in manifest["entries"]}
    rows = []
    for number in range(start, end + 1):
        meta = info(number)
        pairs = replacements(meta)
        print("PILOT", json.dumps(meta, ensure_ascii=False))
        print("RECONSTRUCTION", "Use the simultaneous longest-literal replacements defined in numbered_102_152_helper.replacements; all field values above are literal. Full replacement pairs are saved in reads.json.")
        pattern = re.compile("|".join(re.escape(k) for k in sorted(pairs, key=len, reverse=True))) if pairs else None
        folder = BASE / meta["pilot_id"]
        identical = []
        for path in sorted(p for p in folder.rglob("*") if p.is_file()):
            rel = path.relative_to(folder).as_posix()
            baseline_path = TEMPLATE / rel
            source_bytes = path.read_bytes()
            text = source_bytes.decode("utf-8")
            expected = baseline_path.read_bytes().decode("utf-8")
            if pattern:
                expected = pattern.sub(lambda match: pairs[match.group(0)], expected)
            delta = list(difflib.unified_diff(expected.splitlines(keepends=True), text.splitlines(keepends=True),
                                            fromfile="mapped_template/" + rel, tofile=meta["pilot_id"] + "/" + rel, n=2))
            # ndiff restore independently checks complete reconstruction, including unchanged lines.
            nd = list(difflib.ndiff(expected.splitlines(keepends=True), text.splitlines(keepends=True)))
            assert "".join(difflib.restore(nd, 2)) == text
            manifest_row = custody[path.relative_to(BASE).as_posix()]
            digest = hashlib.sha256(source_bytes).hexdigest()
            assert digest == manifest_row["sha256"], path
            if not delta:
                identical.append(rel)
            if delta:
                print("FILE", rel, "FULL_RESIDUAL_DIFF")
                print("".join(delta), end="" if delta[-1].endswith("\n") else "\n")
            rows.append({"path": path.relative_to(ROOT).as_posix(), "sha256": digest,
                         "lines": [1, source_bytes.count(b"\n") + int(bool(source_bytes) and not source_bytes.endswith(b"\n"))],
                         "source_git_tracked": manifest_row["source_git_tracked"],
                         "source_git_blob": manifest_row["source_git_blob"],
                         "template_path": baseline_path.relative_to(ROOT).as_posix(),
                         "template_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
                         "simultaneous_exact_replacements": pairs, "residual_diff": delta,
                         "reconstruction_verified": True,
                         "review_level": "emitted_lossless_template_and_full_differences_pending_assessment"})
        print("IDENTICAL_TO_MAPPED_TEMPLATE", json.dumps(identical))
    previous = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    index = {row["path"]: row for row in previous}
    index.update({row["path"]: row for row in rows})
    OUT.write_text(json.dumps(list(index.values()), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    inspect(int(sys.argv[1]), int(sys.argv[2]))
