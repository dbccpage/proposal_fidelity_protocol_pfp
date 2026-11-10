"""Fresh, scoped pilot22 delivery replay; retains raw subprocess evidence."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from pydantic import BaseModel, ConfigDict, Field
import yaml


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class FilePin(Record):
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bytes: int = Field(ge=0)


class Command(Record):
    argv: list[str]
    cwd: str
    returncode: int
    stdout_sha256: str
    stderr_sha256: str


class Contract(Record):
    new_tests: int = Field(ge=1)
    new_mutations: int = Field(ge=1)
    frozen_runner_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Replay(Record):
    pilot_id: str
    attempt: str
    root: str
    source_pins: list[FilePin]
    commands: list[Command]
    tests: int
    new_tests: int
    dependency_tests: int
    mutations: dict[str, int]
    coverage_percent: float
    module_coverage: dict[str, float]
    excluded_lines: int
    equivalent_positive_cases: int
    changed_answer_rejected: bool
    default_output: str
    default_result_sha256: str
    provider_calls: int
    cost_usd: str


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def retain(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else json.dumps(value, indent=2, sort_keys=True).encode() + b"\n"
    with path.open("xb") as stream:
        stream.write(raw)


def twin(path, record):
    value = record.model_dump(mode="json")
    retain(path.with_suffix(".json"), value)
    raw = yaml.safe_dump(value, sort_keys=True).encode()
    assert type(record).model_validate(yaml.safe_load(raw)) == record
    retain(path.with_suffix(".yaml"), raw)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("attempt")
    args = parser.parse_args()
    assert args.attempt.isalnum() and sys.version_info[:2] == (3, 12)
    pilot = Path(__file__).resolve().parents[2]
    assert pilot.name == "pilot_0000047"
    root = next(p for p in pilot.parents if (p / "omega_engine_education").is_dir())
    output_root = pilot.parent / "pilot_output" / pilot.name
    output = output_root / ("verification_" + args.attempt)
    output.mkdir(parents=True, exist_ok=False)
    frozen = pilot / "reviewed_snapshot/run.py"
    contract_path = pilot / "reviewed_snapshot/delivery_contract.json"
    contract = Contract.model_validate(read(contract_path))
    assert contract == Contract.model_validate(yaml.safe_load(contract_path.with_suffix(".yaml").read_bytes()))
    assert sha(frozen.read_bytes()) == contract.frozen_runner_sha256
    code = pilot / "run.py"
    new_test = pilot / "tests/typed_engine/test_new001_typed_engine.py"
    dep21 = pilot.parent / "pilot_0000046"
    dep17 = pilot.parent / "pilot_0000042"
    tests = [new_test, dep21 / "tests/hodge_companion/test_pilot_0000046_hodge_companion.py",
             dep17 / "tests/hodge/test_quiz11_hodge.py"]
    sources = [code, *tests, dep21 / "run.py", dep17 / "run.py", frozen,
               pilot / "coverage.ini", pilot / "pytest.ini", contract_path, Path(__file__).resolve()]
    pins = []
    for index, path in enumerate(sources):
        raw = path.read_bytes()
        pins.append(FilePin(path=path.relative_to(root).as_posix(), sha256=sha(raw), bytes=len(raw)))
        retain(output / "sources" / f"{index}_{path.name}", raw)
    scratch = Path(tempfile.mkdtemp(prefix="p22delivery_"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               COVERAGE_FILE=str(output / ".coverage"),
               TYPED_ENGINE_MUTATION_REPORT=str(output / "new_mutations.json"),
               HODGE_MUTATION_REPORT=str(output / "pilot21_mutations.json"),
               PFP_MUTATION_REPORT=str(output / "pilot17_mutations.json"))
    commands = []

    def execute(argv):
        index = len(commands)
        retain(output / f"argv_{index}.json", argv)
        result = subprocess.run(argv, cwd=root, env=env, capture_output=True, check=False)
        retain(output / f"stdout_{index}.bin", result.stdout)
        retain(output / f"stderr_{index}.bin", result.stderr)
        command = Command(argv=argv, cwd=str(root), returncode=result.returncode,
                          stdout_sha256=sha(result.stdout), stderr_sha256=sha(result.stderr))
        twin(output / f"command_{index}", command)
        commands.append(command)
        return result

    execute([sys.executable, "-B", "-m", "coverage", "run", "--rcfile", str(pilot / "coverage.ini"),
             "-m", "pytest", "-q", "-c", str(pilot / "pytest.ini"), "--basetemp", str(scratch / "pytest"),
             "--junitxml", str(output / "junit.xml"), *map(str, tests)])
    execute([sys.executable, "-B", "-m", "coverage", "json", "--rcfile", str(pilot / "coverage.ini"),
             "-o", str(output / "coverage.json")])
    default = execute([sys.executable, "-B", str(code)])
    for path in sorted(scratch.rglob("*")):
        if path.is_symlink() or path.is_junction():
            continue
        if path.is_file():
            dest = output / "scratch" / path.relative_to(scratch)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
    assert all(c.returncode == 0 for c in commands), "See retained failed commands"
    for pin in pins:
        raw = (root / pin.path).read_bytes()
        assert len(raw) == pin.bytes and sha(raw) == pin.sha256, pin.path
    suites = list(ET.parse(output / "junit.xml").getroot())
    count = sum(int(s.attrib["tests"]) for s in suites)
    assert count == contract.new_tests + 243
    assert all(int(s.attrib[k]) == 0 for s in suites for k in ("errors", "failures", "skipped"))
    coverage = read(output / "coverage.json")
    expected_modules = {p.resolve() for p in (code, dep21 / "run.py", dep17 / "run.py")}
    assert {(root / p).resolve() for p in coverage["files"]} == expected_modules
    percentages = {p: r["summary"]["percent_covered"] for p, r in coverage["files"].items()}
    assert all(v >= 95 for v in percentages.values()) and coverage["totals"]["excluded_lines"] == 0
    mutations = {}
    for name, expected, target in (("new_mutations", contract.new_mutations, code), ("pilot21_mutations", 17, dep21 / "run.py"),
                                   ("pilot17_mutations", 18, dep17 / "run.py")):
        data = read(output / (name + ".json"))
        assert data["count"] == len(data["mutations"]) == expected
        for row in data["mutations"]:
            assert row["compiled"] and row.get("killed", row.get("caught"))
            assert row["source_sha256"] == sha(target.read_bytes())
        mutations[name] = expected
    before = module(frozen, "pilot22_frozen_equivalence")
    after = module(code, "pilot22_delivered_equivalence")
    equivalences = 0
    for prefix, suffix, indent in (("", "", None), ("\u03a9\r\n", "\n", 2), ("Packet:\n", "END", 0)):
        for cochain in (["1", "2", "3"], ["0", "0", "0"], ["-2/3", "5/7", "3"]):
            request = before.dependency()[0].demo_request()
            request["cochain"] = cochain
            left, right = before.build_graph(request), after.build_graph(request)
            a, b = before.reframe(left, prefix, suffix, indent), after.reframe(right, prefix, suffix, indent)
            assert before.encoded(a) == after.encoded(b)
            assert before.evaluate({"kind": "check_transport", "transport": a.model_dump()}) == after.evaluate({"kind": "check_transport", "transport": b.model_dump()})
            equivalences += 1
    for m in (before, after):
        left = m.demo_job().transport.domain
        request = left.request.payload.model_dump()
        request["cochain"] = ["1", "2", "4"]
        right = m.build_graph(request)
        assert left.document.summary == right.document.summary
        try:
            m.checked_transport(m.proposal(left, right))
        except ValueError as error:
            assert str(error) == "Protected executable query changed"
        else:
            raise AssertionError("Changed answer was accepted")
    folder = Path(json.loads(default.stdout)["output"])
    assert folder.parent == output_root
    receipt = after.Receipt.model_validate(read(folder / "receipt.json"))
    assert receipt.experiment == "pilot_0000047" and receipt.code_sha256 == sha(code.read_bytes())
    assert receipt == after.Receipt.model_validate(yaml.safe_load((folder / "receipt.yaml").read_bytes()))
    assert (folder / "stdout.txt").read_bytes() == default.stdout
    for name, expected in receipt.artifact_sha256.model_dump(by_alias=True).items():
        assert sha((folder / name).read_bytes()) == expected
    report = after.PreservedReport.model_validate(read(folder / "result.json"))
    assert report.model_dump() == before.evaluate(before.demo_job())
    replay = Replay(pilot_id=pilot.name, attempt=args.attempt, root=str(root), source_pins=pins,
                    commands=commands, tests=count, new_tests=contract.new_tests, dependency_tests=243, mutations=mutations,
                    coverage_percent=coverage["totals"]["percent_covered"], module_coverage=percentages,
                    excluded_lines=0, equivalent_positive_cases=equivalences, changed_answer_rejected=True,
                    default_output=folder.relative_to(root).as_posix(), default_result_sha256=sha((folder / "result.json").read_bytes()),
                    provider_calls=0, cost_usd="0")
    twin(output / "replay", replay)
    print(replay.model_dump_json())


if __name__ == "__main__":
    main()
