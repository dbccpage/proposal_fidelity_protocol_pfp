"""Synthetic retirement review. Never invokes Apply or touches imported pilots."""
from pathlib import Path
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "dag/pilot_triage"
FILES = ["prepare_retirement.py", "retirement_custody.py", "apply_retirement.ps1", "build_catalog.py"]
SOURCE = {name: (HERE / name).read_bytes() for name in FILES}
PWSH = shutil.which("pwsh")
assert PWSH, "PowerShell executable unavailable"

def sha(data): return hashlib.sha256(data).hexdigest()
def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
def load(name, root):
    spec = importlib.util.spec_from_loader("review_" + name, loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(HERE / name)
    exec(compile(SOURCE[name], str(HERE / name), "exec"), module.__dict__)
    module.ROOT = root
    module.TRIAGE = root / "dag/pilot_triage"
    module.DAG = root / "dag"
    return module

def fixture(root):
    triage = root / "dag/pilot_triage"
    triage.mkdir(parents=True)
    folder = root / "pilots/anomalon_woland/pilot_0000999"
    folder.mkdir(parents=True)
    entries = []
    for name in ("README.md", "spec.yaml"):
        data = ("public synthetic fixture " + name + "\n").encode()
        (folder / name).write_bytes(data)
        entries.append({"path": "pilot_0000999/" + name, "bytes": len(data), "sha256": sha(data),
                        "source_git_tracked": False, "source_git_blob": None})
    archive_path = root / "recovery.zip"
    with zipfile.ZipFile(archive_path, "w") as z:
        for row in entries:
            z.write(root / "pilots/anomalon_woland" / row["path"], row["path"])
        z.writestr("_migration_manifest.json", json.dumps({"directories": ["pilot_0000999"], "entries": entries}))
    p = {"id": "pilot_0000999", "path": "pilots/anomalon_woland/pilot_0000999", "verdict": "stub_candidate",
         "rationale": "synthetic planned stub", "report": "dag/pilot_triage/numbered_999_999.json",
         "contribution": "synthetic plan", "mathematical_basis": "none", "reusable_mechanism_name": "none",
         "next_action": "retain lesson", "qm_seed_transfer": {"protected_qm_seed_read": False},
         "workflow_mapping": [], "source_evidence": [{"path": "pilots/anomalon_woland/" + entries[0]["path"], "sha256": entries[0]["sha256"], "lines": [1,1]}]}
    write(triage / "numbered_999_999.json", {"pilots": [p]})
    write(triage / "catalog.json", {"initially_assessed": 1, "numbered_pilots": 1, "pilots": [p]})
    write(root / "dag/migrations/anomalon_pilots_move.json", {"destination_relative_path": "pilots/anomalon_woland", "directories": ["pilot_0000999"], "entries": entries})
    write(root / "dag/migrations/pilot_recovery_archive.json", {"original_custody_drift": [], "archive_current_sha256_mismatches": [],
          "archive_path": str(archive_path), "archive_sha256": sha(archive_path.read_bytes()), "archive_bytes": archive_path.stat().st_size})
    return p, folder

def prepare(root):
    module = load("prepare_retirement.py", root)
    with contextlib.redirect_stdout(io.StringIO()): module.main()

def preflight(root):
    text = SOURCE["apply_retirement.ps1"].decode("utf-8")
    old = "$taskRepo = '" + str(ROOT) + "'"
    assert text.count(old) == 1
    text = text.replace(old, "$taskRepo = '" + str(root).replace("'", "''") + "'")
    script = root / "review_preflight.ps1"
    script.write_text(text, encoding="utf-8")
    result = subprocess.run([PWSH, "-NoProfile", "-File", str(script)], capture_output=True, text=True, timeout=60)
    return {"exit_code": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}

results = []
with tempfile.TemporaryDirectory(prefix="retirement_review_fixture_", dir=HERE) as tmp:
    workspace = Path(tmp).resolve()
    assert workspace.is_relative_to(HERE.resolve())
    root = workspace / "baseline"
    fixture(root)
    prepare(root)
    result = preflight(root)
    assert result["exit_code"] == 0, result
    results.append({"id": "baseline_preflight", "observed": result})

    root = workspace / "stale"
    p, folder = fixture(root)
    p["verdict"] = "retain_mechanism"
    write(root / p["report"], {"pilots": [p]})
    try:
        prepare(root)
        results.append({"id": "stale_catalog", "accepted": True})
    except ValueError as error:
        results.append({"id": "stale_catalog", "accepted": False, "error": str(error)})

    for kind in ("file_ads", "directory_ads", "unknown_file", "unknown_empty_directory"):
        root = workspace / kind
        p, folder = fixture(root)
        if kind == "file_ads":
            Path(str(folder / "README.md") + ":unarchived_review_payload").write_bytes(b"not in zip\n")
        elif kind == "directory_ads":
            Path(str(folder) + ":unarchived_review_payload").write_bytes(b"directory data not in zip\n")
        elif kind == "unknown_file":
            (folder / "unmanifested.txt").write_text("not in zip", encoding="utf-8")
        else:
            (folder / "unmanifested_empty").mkdir()
        try:
            prepare(root)
            results.append({"id": kind, "preparer_accepted": True, "preflight": preflight(root)})
        except Exception as error:
            results.append({"id": kind, "preparer_accepted": False, "error": type(error).__name__ + ": " + str(error)})

    root = workspace / "junction"
    p, folder = fixture(root)
    prepare(root)
    external = workspace / "junction_destination"
    external.mkdir()
    junction = folder / "linked_directory"
    result = subprocess.run([PWSH, "-NoProfile", "-Command", "New-Item -ItemType Junction -Path '" + str(junction) + "' -Target '" + str(external) + "' | Out-Null"], capture_output=True, text=True, timeout=30)
    if result.returncode:
        results.append({"id": "junction_descendant", "status": "fixture_creation_blocked", "stderr": result.stderr.strip()})
    else:
        result = preflight(root)
        assert result["exit_code"] != 0 and "Linked pilot descendant" in result["stderr"], result
        results.append({"id": "junction_descendant", "preflight": result})
        assert junction.parent.resolve().is_relative_to(workspace)
        junction.rmdir()  # Removes this synthetic junction only; target is preserved.
        assert external.exists()

    for kind in ("report_verdict_drift", "path_escape", "default_stream_drift", "archive_drift"):
        root = workspace / kind
        p, folder = fixture(root)
        prepare(root)
        plan_path = root / "dag/pilot_triage/retirement_plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if kind == "report_verdict_drift":
            p["verdict"] = "retain_mechanism"
            write(root / p["report"], {"pilots": [p]})
            plan["pilots"][0]["report_sha256"] = sha((root / p["report"]).read_bytes())
            write(plan_path, plan)
        elif kind == "path_escape":
            p["path"] = "pilots/anomalon_woland/../outside"
            plan["pilots"][0]["path"] = p["path"]
            write(root / p["report"], {"pilots": [p]})
            plan["pilots"][0]["report_sha256"] = sha((root / p["report"]).read_bytes())
            write(plan_path, plan)
        elif kind == "default_stream_drift":
            (folder / "README.md").write_bytes(b"changed")
        else:
            with (root / "recovery.zip").open("ab") as stream: stream.write(b"unregistered change")
        result = preflight(root)
        assert result["exit_code"] != 0, (kind, result)
        results.append({"id": kind, "preflight": result})

    root = workspace / "partial"
    p, folder = fixture(root)
    prepare(root)
    plan_bytes = (root / "dag/pilot_triage/retirement_plan.json").read_bytes()
    receipt = {"status": "applying", "plan_sha256": sha(plan_bytes), "removed": [],
               "removal_intent": {"id": p["id"], "path": p["path"]}}
    write(root / "dag/pilot_triage/retirement_receipt.json", receipt)
    vanished = folder / "README.md"
    assert vanished.resolve().is_relative_to(workspace)
    vanished.unlink()  # Synthetic partial removal; never the production Apply path.
    module = load("retirement_custody.py", root)
    store = module.EvidenceStore()
    results.append({"id": "partial_intent_evidence", "status": store.status(p["id"]),
                    "archived_bytes": store.read(p["path"] + "/README.md").decode(),
                    "live_bytes": store.read(p["path"] + "/spec.yaml").decode()})
    store.close()
    builder = load("build_catalog.py", root)
    builder.EvidenceStore = module.EvidenceStore
    with contextlib.redirect_stdout(io.StringIO()): builder.main()
    rebuilt = json.loads((root / "dag/pilot_triage/catalog.json").read_text(encoding="utf-8"))
    assert rebuilt["source_pins_verified"] == 1 and rebuilt["pilots"][0]["deletion_status"] == "removal_incomplete_archive_available"
    results.append({"id": "partial_catalog_rebuild", "source_pins_verified": rebuilt["source_pins_verified"], "status": rebuilt["pilots"][0]["deletion_status"]})
    remaining = folder / "spec.yaml"
    assert remaining.resolve().is_relative_to(workspace)
    remaining.unlink()
    assert folder.resolve().is_relative_to(workspace)
    folder.rmdir()
    receipt.update(status="complete", removal_intent=None, removed=[{"id": p["id"], "path": p["path"]}])
    write(root / "dag/pilot_triage/retirement_receipt.json", receipt)
    with contextlib.redirect_stdout(io.StringIO()): builder.main()
    rebuilt = json.loads((root / "dag/pilot_triage/catalog.json").read_text(encoding="utf-8"))
    assert rebuilt["retired_numbered_pilots"] == 1 and rebuilt["source_pins_verified"] == 1
    results.append({"id": "completed_catalog_rebuild", "source_pins_verified": rebuilt["source_pins_verified"], "status": rebuilt["pilots"][0]["deletion_status"]})
    (root / "dag/pilot_triage/retained_lessons.json").write_text("corrupted retained lessons\n", encoding="utf-8")
    try:
        store = module.EvidenceStore()
        store.read(p["path"] + "/README.md")
        store.close()
        results.append({"id": "lesson_drift_after_intent", "accepted": True})
    except Exception as error:
        results.append({"id": "lesson_drift_after_intent", "accepted": False, "error": str(error)})

out = {"source_sha256": {name: sha(raw) for name, raw in SOURCE.items()}, "production_apply_invoked": False,
       "production_corpus_mutations": 0, "synthetic_workspace_removed": True, "results": results}
(HERE / "retirement_review_probe_results.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, indent=2))
