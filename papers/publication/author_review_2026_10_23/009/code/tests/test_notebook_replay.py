"""Changed-output and error controls for the notebook replay comparison."""
import importlib.util
from copy import deepcopy
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "paper009_replay", Path(__file__).resolve().parents[2] / "tools" / "replay_notebook.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture():
    return {"cells": [{
        "cell_type": "code", "source": "print(1)", "execution_count": 1,
        "outputs": [{"output_type": "stream", "name": "stdout", "text": "1\\n"}],
    }]}


def test_matching_replay_is_accepted():
    original = fixture()
    assert MODULE.compare_code_outputs(original, deepcopy(original)) == []


def test_changed_value_fails_comparison():
    original, changed = fixture(), fixture()
    changed["cells"][0]["outputs"][0]["text"] = "2\\n"
    assert MODULE.compare_code_outputs(original, changed) == ["cell 0: outputs differ"]


def test_source_change_and_missing_cell_fail():
    original, changed = fixture(), fixture()
    changed["cells"][0]["source"] = "print(2)"
    assert "cell 0: source or position changed" in MODULE.compare_code_outputs(original, changed)
    assert MODULE.compare_code_outputs(original, {"cells": []}) == ["code-cell count changed"]


def test_error_output_cannot_pass_even_if_stored():
    original = fixture()
    original["cells"][0]["outputs"] = [{"output_type": "error", "ename": "ValueError"}]
    assert "cell 0: execution error" in MODULE.compare_code_outputs(original, deepcopy(original))


def test_stale_execution_count_fails():
    original, changed = fixture(), fixture()
    changed["cells"][0]["execution_count"] = None
    assert "cell 0: execution count differs" in MODULE.compare_code_outputs(original, changed)


def test_fresh_process_exposes_a_wrong_stored_result(tmp_path):
    cell = MODULE.nbformat.v4.new_code_cell("print(1)")
    cell.execution_count = 1
    cell.outputs = [MODULE.nbformat.v4.new_output("stream", name="stdout", text="2\n")]
    notebook = MODULE.nbformat.v4.new_notebook(cells=[cell])
    path = tmp_path / "wrong-output.ipynb"
    MODULE.nbformat.write(notebook, path)
    report = MODULE.replay(path)
    assert report["status"] == "FAIL"
    assert report["errors"] == ["cell 0: outputs differ"]


def test_fresh_process_keeps_assertions_enabled(tmp_path, monkeypatch):
    cell = MODULE.nbformat.v4.new_code_cell("assert False")
    cell.execution_count = 1
    notebook = MODULE.nbformat.v4.new_notebook(cells=[cell])
    path = tmp_path / "failed-assertion.ipynb"
    MODULE.nbformat.write(notebook, path)
    monkeypatch.setenv("PYTHONOPTIMIZE", "1")
    report = MODULE.replay(path)
    assert report["status"] == "FAIL"
    assert "cell 0: execution error" in report["errors"]
