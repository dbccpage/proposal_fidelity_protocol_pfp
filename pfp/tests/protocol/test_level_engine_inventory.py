"""Canonical ownership and history boundaries for the education source inventory."""

from pathlib import Path

from education.scripts import verify_system_integration as inventory


def test_inventory_keeps_relocated_sources_and_v1_history(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    monkeypatch.setattr(inventory, "DEST", tmp_path / "education/generated")
    historical = inventory.HISTORICAL_LEVEL_ENGINE_ROOT + "bundles/old.json"
    runtime = "pfp/infrastructure/tower_research/level_engine/runner.py"
    inputs = {
        "research/example.md": "reading\n",
        runtime: "def classify(): return 'finite'\n",
        historical: "{}\n",
        "operations/use_cases/level_engine/lean_build.py": "def build(): pass\n",
        "governance/contracts/level_engine/v2/PINS.json": "{}\n",
        "lean4/research_programs/level_engine/Certificate.lean": "import ExactRat\n",
    }
    for relative, content in inputs.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    manifest = {"lessons": [{"path": "lesson.ipynb", "sources": [runtime, historical]}]}
    result = inventory.make_inventory(manifest)
    records = {record["path"]: record for record in result["files"]}
    assert set(records) == set(inputs)
    assert records[runtime]["owner"] == "pfp"
    assert records[runtime]["classification"] == "lab-backed"
    assert records[historical]["classification"] == "historical"
    assert {record["owner"] for record in records.values()} == {
        "research",
        "pfp",
        "operations",
        "governance",
        "lean4",
    }
    assert result["schema"] == "mssn.education.research-inventory.v2"
    # A second generation never inventories its own output.
    assert set(record["path"] for record in inventory.make_inventory(manifest)["files"]) == set(
        inputs
    )


def test_inventory_excludes_runtime_caches_and_vendor_copies(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    paths = [
        "research/current.py",
        "research/__pycache__/current.pyc",
        "research/vendor/external.py",
        "research/.git/config",
        "research/.lake/build/Certificate.olean",
    ]
    for relative in paths:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"sample")
    assert [path.relative_to(tmp_path).as_posix() for path in inventory.research_files()] == [
        "research/current.py"
    ]
