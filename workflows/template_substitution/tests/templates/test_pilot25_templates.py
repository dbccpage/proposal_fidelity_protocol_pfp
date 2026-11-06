import importlib.util
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import types

import pytest
from pydantic import ValidationError

SOURCE = Path(__file__).resolve().parents[2] / "run.py"
SPEC = importlib.util.spec_from_file_location("pilot25_under_test", SOURCE)
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


def expected(template, question, data):
    rows = ["Question: " + question + "\n", "Data: " + data + "\n"]
    return "".join(rows if template == "question_first" else rows[::-1])


@pytest.mark.parametrize("template", ["question_first", "data_first"])
@pytest.mark.parametrize("question,data", [
    ("What?", "plain data"),
    ("Q", "before ${question} and ${data}"),
    ("${data}?", "plain data"),
    ("  α?\n", ' \t{"literal":"${unknown}","cash":"$${data}"}\n猫  '),
], ids=["ordinary", "data-placeholder", "question-placeholder", "literal-unicode-whitespace"])
def test_exact_one_pass_and_baseline(template, question, data):
    result = m.render({"template": template, "question": question, "data": data})
    assert result.rendered == expected(template, question, data)
    assert result.sequential == expected(template, question, data.replace("${question}", question))
    assert result.differs == ("${question}" in data)
    assert result.utf8_bytes == len(result.rendered.encode("utf-8"))
    assert result.codepoints == len(result.rendered) and result.provider_calls == 0


@pytest.mark.parametrize("field,value", [("question", ""), ("question", "x" * 513), ("data", "x" * 2049),
                                         ("data", 42), ("template", "other"), ("extra", True)],
                         ids=["empty", "question-bound", "data-bound", "strict-string", "template", "unknown-field"])
def test_request_refusals(field, value):
    value_dict = m.default_job()
    value_dict[field] = value
    with pytest.raises(ValidationError):
        m.render(value_dict)


@pytest.mark.parametrize("kind", ["default", "valid", "invalid", "missing", "oversize"])
def test_main(kind, tmp_path, capsys):
    args = []
    if kind != "default":
        path = tmp_path / "request.json"
        if kind != "missing":
            raw = (SOURCE.parent / "examples/request.json").read_bytes() if kind == "valid" else b"!" if kind == "invalid" else b" " * 16385
            path.write_bytes(raw)
        args = ["--input", str(path)]
    code = m.main(args)
    record = json.loads(capsys.readouterr().out)
    if kind in ("default", "valid"):
        assert code == 0 and record["differs"] is True
        assert "${question}" in record["rendered"] and "${question}" not in record["sequential"]
    else:
        assert code == 2 and record["status"] == "INVALID" and record["reason"]


def test_actual_default_cli():
    result = subprocess.run([sys.executable, "-B", str(SOURCE)], capture_output=True, check=False,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    assert result.returncode == 0 and not result.stderr
    assert json.loads(result.stdout) == {
        "rendered": "Question: Return the literal data.\nData: The data contains ${question}; do not expand it.\n",
        "sequential": "Question: Return the literal data.\nData: The data contains Return the literal data.; do not expand it.\n",
        "differs": True, "utf8_bytes": 90, "codepoints": 90, "provider_calls": 0}


def oracle(module):
    for template in ("question_first", "data_first"):
        result = module.render({"template": template, "question": "Q", "data": " \t猫 ${question}\n "})
        text = expected(template, "Q", " \t猫 ${question}\n ")
        assert result.rendered == text
        assert result.utf8_bytes == len(text.encode("utf-8"))


@pytest.mark.parametrize("old,new", [
    ("rendered = Template(template).substitute(question=job.question, data=job.data)", "rendered = sequential"),
    ("data=job.data)", "data=job.data.strip())"),
    ("template = TEMPLATES[job.template]", 'template = TEMPLATES["question_first"]'),
    ('utf8_bytes=len(rendered.encode("utf-8"))', "utf8_bytes=len(rendered)"),
], ids=["sequential-rewrite", "strip-data", "ignore-template", "byte-count"])
def test_compiled_semantic_mutants(old, new):
    source = SOURCE.read_text(encoding="utf-8")
    assert source.count(old) == 1
    mutant = types.ModuleType("pilot25_mutant")
    sys.modules[mutant.__name__] = mutant
    exec(compile(source.replace(old, new), "pilot25_mutant.py", "exec"), mutant.__dict__)
    with pytest.raises(AssertionError):
        oracle(mutant)


def test_script_entry(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(SOURCE)])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(SOURCE), run_name="__main__")
    assert caught.value.code == 0 and isinstance(json.loads(capsys.readouterr().out), dict)


def test_duplicate_json_keys_are_refused(tmp_path, capsys):
    path = tmp_path / "request.json"
    path.write_bytes(b'{"template":"question_first","question":"Q","data":"a","data":"b"}')
    assert m.main(["--input", str(path)]) == 2
    assert "Duplicate JSON key: data" in json.loads(capsys.readouterr().out)["reason"]
