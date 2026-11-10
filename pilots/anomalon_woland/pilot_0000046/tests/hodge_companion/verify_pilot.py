"""Fresh, isolated canonical relocation verification with append-only evidence."""
import argparse
import ast
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from itertools import combinations
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import traceback
from types import ModuleType
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parents[2]
PILOTS = HERE.parent
ROOT = next(p for p in HERE.parents if (p / "omega_engine_woland").is_dir())
CORE = PILOTS / "pilot_0000042"
CORE_TEST = CORE / "tests/hodge/test_quiz11_hodge.py"
OWN_TEST = HERE / "tests/hodge_companion/test_pilot_0000046_hodge_companion.py"
OUTPUT = PILOTS / "pilot_output/pilot_0000046"
REVIEWED = HERE / "reviewed_snapshot"
CORE_SHA = "256fe853bfa391b42ad3ebbff41501752fb2568bffdc746b470acd07e5638073"
CORE_TEST_SHA = "79daeceda2ff1c2e934efb934a6aa6a6ece4e96dd222d8d91575bc84a841d614"
OLD_RUN_SHA = "354de7dbdf76e5cbff55a291154db2fd88d9dba68c4fe5e771bc9d2b21440a22"
OLD_TEST_SHA = "a1b2e779e9823707889d5e6473aeb158c033a233ec69fb064e10fed698d8130e"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True).encode("ascii") + b"\n"
    with path.open("xb") as stream:
        stream.write(raw)


def module(path, raw=None):
    m = ModuleType("pilot21_relocation_check")
    m.__file__ = str(path)
    exec(compile(path.read_bytes() if raw is None else raw, str(path), "exec"), m.__dict__)
    return m


def relocation():
    original = (REVIEWED / "run.py.txt").read_bytes()
    assert sha(original) == OLD_RUN_SHA
    replacements = (
        ('"""Offline candidate: strict weighted graph intake and exact simplex complement."""',
         '"""Pilot 000021: strict weighted graph intake and exact simplex complement."""'),
        ('CANDIDATE_ID = "hodge_companion_candidate"', 'PILOT_ID = "pilot_0000046"'),
        ('OUTPUT_ROOT = Path(__file__).resolve().parent / "output"',
         'OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "pilot_output" / PILOT_ID'),
        ('receipt = {"candidate_id": CANDIDATE_ID,', 'receipt = {"pilot_id": PILOT_ID,'),
    )
    expected = original.decode("utf-8")
    for old, new in replacements:
        assert expected.count(old) == 1
        expected = expected.replace(old, new, 1)
    actual = (HERE / "run.py").read_text(encoding="utf-8")
    assert actual == expected, "Production changes exceed the four declared identity/output substitutions"
    old_tests = (REVIEWED / "test_companion.py.txt").read_bytes()
    assert sha(old_tests) == OLD_TEST_SHA
    expected_test = old_tests.decode("utf-8").replace(
        'HERE = Path(__file__).resolve().parents[1]', 'HERE = Path(__file__).resolve().parents[2]', 1).replace(
        'spec_from_file_location("hodge_companion", RUNNER)',
        'spec_from_file_location("pilot_0000046_hodge_companion", RUNNER)', 1)
    assert OWN_TEST.read_text(encoding="utf-8") == expected_test
    functions = [node.name for node in ast.parse(actual).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))]
    assert functions == [node.name for node in ast.parse(original).body if isinstance(node, (ast.FunctionDef, ast.ClassDef))]
    assert sha((CORE / "run.py").read_bytes()) == CORE_SHA
    assert sha(CORE_TEST.read_bytes()) == CORE_TEST_SHA
    historical = read(REVIEWED / "source_inventory.json")["sources"]
    for i, row in enumerate(historical, 1):
        suffix = ".md" if i <= 3 else ".py.txt"
        snapshot = HERE / "sources" / f"S{i}{suffix}"
        assert sha(snapshot.read_bytes()) == row["sha256"]
        assert snapshot.read_bytes() == (ROOT / row["path"]).read_bytes()
    for path in HERE.rglob("*.py"):
        assert path.stem not in sys.stdlib_module_names, path
        calls = [node for node in ast.walk(ast.parse(path.read_bytes())) if isinstance(node, ast.Call)]
        assert not any(ast.unparse(node.func) == "sys.path.insert" for node in calls), path
    return {"old_runner_sha256": OLD_RUN_SHA, "new_runner_sha256": sha((HERE / "run.py").read_bytes()),
            "production_substitutions": [{"old": a, "new": b} for a, b in replacements],
            "test_substitutions": 2, "dependency_sha256": CORE_SHA, "dependency_tests_sha256": CORE_TEST_SHA,
            "historical_source_snapshots": len(historical), "module_shadow_scan": "PASS"}


def equivalence():
    current = module(HERE / "run.py")
    reviewed = module(HERE / "run.py", (REVIEWED / "run.py.txt").read_bytes())
    assert current.OUTPUT_ROOT == OUTPUT
    count = 0
    for n in range(5):
        vertices = tuple(str(i) for i in range(n+1))
        graph = "<>".join(f"{a}>{b}w{1+(int(a)*3+int(b))%9}" for a, b in combinations(vertices, 2)) if n else "0"
        for k in range(-1, n+1):
            size = len(list(combinations(vertices, k+1)))
            for values in ([str(int(i == 0)) for i in range(size)],
                           [str(Fraction(i-2, i+1)) for i in range(size)]):
                request = {"task_id": "relocation", "kind": "complement", "graph": graph,
                           "cutoff": n, "degree": k, "cochain": values}
                old, new = reviewed.answer_for(request), current.answer_for(request)
                assert old == new and reviewed.encoded(old) == current.encoded(new)
                assert current.evaluate(current.submission(request, old))["verdict"] == "MATCH"
                count += 1
    for cutoff in (1, 2):
        request = {"task_id": "triangle", "kind": "unweighted", "graph": "0>1w4<>0>2w9<>1>2w1",
                   "cutoff": cutoff, "degree": 1, "cochain": ["1", "2", "3"]}
        assert current.answer_for(request) == reviewed.answer_for(request)
        count += 1
    assert count == 42
    assert current.answer_for(current.demo_request()) == reviewed.answer_for(reviewed.demo_request())
    return {"query_equivalence_cases": count, "default_answer_equal": True,
            "receipt_identity_and_code_hash_change_expected": True, "default_output_root": str(OUTPUT)}


def snapshot(folder):
    pins = {}
    for path in sorted(HERE.rglob("*")):
        if path.is_file():
            raw = path.read_bytes()
            name = path.relative_to(HERE)
            write(folder / "snapshot" / name, raw)
            pins[path.relative_to(ROOT).as_posix()] = sha(raw)
    for path in (CORE / "run.py", CORE_TEST):
        raw = path.read_bytes()
        write(folder / "snapshot/dependency" / path.relative_to(CORE), raw)
        pins[path.relative_to(ROOT).as_posix()] = sha(raw)
    return pins


def retain_scratch(scratch, folder):
    rows = []
    for current, dirs, files in os.walk(scratch, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(current) / name
            st = path.lstat()
            relative = path.relative_to(scratch).as_posix()
            if path.is_symlink() or getattr(st, "st_file_attributes", 0) & 0x400:
                rows.append({"path": relative, "kind": "UNFOLLOWED_LINK", "target": os.readlink(path),
                             "scope": "Alias metadata retained; target bytes have ordinary-path records when present."})
                if name in dirs:
                    dirs.remove(name)
            elif stat.S_ISREG(st.st_mode):
                raw = path.read_bytes()
                write(folder / "scratch" / relative, raw)
                rows.append({"path": relative, "kind": "REGULAR_FILE", "bytes": len(raw), "sha256": sha(raw)})
            elif not stat.S_ISDIR(st.st_mode):
                raise AssertionError(f"Unexpected scratch entry: {path}")
    write(folder / "scratch_inventory.json", {"original_root": str(scratch), "records": rows,
          "original_not_deleted": True, "link_targets_not_traversed": True})
    return {"regular_files_retained": sum(r["kind"] == "REGULAR_FILE" for r in rows),
            "link_metadata_retained": sum(r["kind"] == "UNFOLLOWED_LINK" for r in rows)}


def check_results(folder, commands, pins):
    assert all(row["exit_code"] == 0 for row in commands)
    tree = ET.fromstring((folder / "junit.xml").read_bytes())
    assert len(tree.findall(".//testcase")) == 243
    assert not any(tree.findall(".//" + tag) for tag in ("failure", "error", "skipped"))
    coverage = read(folder / "coverage.json")
    observed = {(ROOT / Path(name)).resolve() for name in coverage["files"]}
    assert observed == {(HERE / "run.py").resolve(), (CORE / "run.py").resolve()}
    assert coverage["totals"]["excluded_lines"] == 0 and coverage["totals"]["percent_covered"] >= 95
    assert all(not row["excluded_lines"] and row["summary"]["percent_covered"] >= 95 for row in coverage["files"].values())
    mutation_counts = {}
    for filename, source_path, expected, name_field, outcome in (
        ("companion_mutations.json", HERE / "run.py", 17, "name", "killed"),
        ("core_mutations.json", CORE / "run.py", 18, "mutation", "caught")):
        record = read(folder / filename)
        assert record["count"] == len(record["mutations"]) == expected
        assert len({row[name_field] for row in record["mutations"]}) == expected
        source = source_path.read_text(encoding="utf-8")
        for row in record["mutations"]:
            assert row["source_sha256"] == sha(source.encode("utf-8"))
            assert row["compiled"] is True and row[outcome] is True
            altered = source.replace(row["old"], row["new"], 1)
            assert altered != source and sha(altered.encode("utf-8")) == row["mutant_sha256"]
            if outcome == "killed":
                assert row["baseline_passed"] is True and row["failure_class"]
            else:
                assert row["baseline_status"] != row["mutant_status"]
        mutation_counts[filename] = expected
    for path, digest in pins.items():
        assert sha((ROOT / path).read_bytes()) == digest, path
    return {"tests_passed": 243, "mutations": mutation_counts,
            "coverage_combined": coverage["totals"],
            "coverage_by_module": {name: row["summary"] for name, row in coverage["files"].items()},
            "all_snapshot_pins_unchanged": True}


def command(folder, number, argv, env):
    write(folder / f"step{number}.command.json", {"argv": argv, "cwd": str(ROOT)})
    result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, check=False)
    write(folder / f"step{number}.stdout.bin", result.stdout)
    write(folder / f"step{number}.stderr.bin", result.stderr)
    row = {"command": argv, "exit_code": result.returncode,
           "stdout_sha256": sha(result.stdout), "stderr_sha256": sha(result.stderr)}
    write(folder / f"step{number}.execution.json", row)
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    return row, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("attempt")
    args = parser.parse_args()
    if re.fullmatch(r"r[1-9][0-9]*", args.attempt) is None:
        parser.error("attempt must be r1, r2, ...")
    folder = OUTPUT / ("verification_" + args.attempt)
    folder.mkdir(parents=True, exist_ok=False)
    report = {"pilot_id": "pilot_0000046", "status": "RUNNING", "attempt": args.attempt,
              "started_at": datetime.now(timezone.utc).isoformat(), "python": sys.version,
              "scope": "Canonical companion and unchanged complete core17 suites; entire two-file production closure",
              "registration": "NOT_PERFORMED", "main_delivery": "NOT_PERFORMED",
              "source_archival": "NOT_PERFORMED", "new_pilot_expansion": False,
              "model_calls": 0, "cost_usd": "0", "authority_effect": "None"}
    scratch = None
    try:
        report["relocation"] = relocation()
        report["equivalence"] = equivalence()
        pins = snapshot(folder)
        report["pins"] = pins
        scratch = Path(tempfile.mkdtemp(prefix="p21_" + args.attempt + "_"))
        assert scratch.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
        report["external_basetemp"] = str(scratch)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                   PFP_MUTATION_REPORT=str(folder / "core_mutations.json"),
                   HODGE_MUTATION_REPORT=str(folder / "companion_mutations.json"))
        write(folder / "execution_plan.json", {**report, "environment_overrides": {
            key: env[key] for key in ("PYTHONDONTWRITEBYTECODE", "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "PFP_MUTATION_REPORT", "HODGE_MUTATION_REPORT")}})
        cov = [sys.executable, "-B", "-m", "coverage"]
        rc, data = "--rcfile=" + str(HERE / "coverage.ini"), "--data-file=" + str(folder / ".coverage")
        planned = [cov + ["run", rc, data, "-m", "pytest", "-q", "-c", str(HERE / "pytest.ini"), str(OWN_TEST), str(CORE_TEST),
                           "--basetemp=" + str(scratch), "--junitxml=" + str(folder / "junit.xml")],
                   cov + ["report", rc, data], cov + ["json", rc, data, "-o", str(folder / "coverage.json")],
                   [sys.executable, "-B", str(ROOT / ".agents/skills/governance-test-isolation/scripts/check_test_isolation.py")]]
        report["commands"] = [command(folder, i, argv, env)[0] for i, argv in enumerate(planned, 1)]
        report["scratch_retention"] = retain_scratch(scratch, folder)
        report.update(check_results(folder, report["commands"], pins))
        cli_row, cli_result = command(folder, 5, [sys.executable, "-B", str(HERE / "run.py")], env)
        report["commands"].append(cli_row)
        assert cli_result.returncode == 0 and cli_result.stderr == b""
        status = json.loads(cli_result.stdout)
        assert status["status"] == "DEMONSTRATED"
        run = Path(status["output"])
        assert run.parent == OUTPUT
        receipt = read(run / "receipt.json")
        m = module(HERE / "run.py")
        assert receipt["pilot_id"] == "pilot_0000046" and "candidate_id" not in receipt
        assert receipt["code_sha256"] == report["relocation"]["new_runner_sha256"] and receipt["core_sha256"] == CORE_SHA
        assert receipt["input_complete"] is True
        raw = (run / "input.bin").read_bytes()
        assert receipt["input_sha256"] == sha(raw) and receipt["input_bytes"] == len(raw)
        assert (run / "stdout.txt").read_bytes() == cli_result.stdout
        for name, digest in receipt["artifact_sha256"].items():
            assert sha((run / name).read_bytes()) == digest
        assert read(run / "result.json") == {"verdict": "DEMONSTRATED", "answer": m.answer_for(m.demo_request())}
        report["default_cli"] = {"output": run.relative_to(ROOT).as_posix(), "receipt_sha256": sha((run / "receipt.json").read_bytes()),
                                 "result_sha256": sha((run / "result.json").read_bytes()), "status": "DEMONSTRATED"}
        assert relocation() == report["relocation"]
        assert equivalence() == report["equivalence"]
        report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAILED"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
        write(folder / "failure.txt", traceback.format_exc().encode("utf-8"))
        if scratch is not None and not (folder / "scratch_inventory.json").exists():
            try:
                report["scratch_retention"] = retain_scratch(scratch, folder)
            except Exception:
                write(folder / "scratch_retention_failure.txt", traceback.format_exc().encode("utf-8"))
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    write(folder / "verification.json", report)
    print(json.dumps({"status": report["status"], "verification": str(folder / "verification.json")}))
    return int(report["status"] != "PASS")


if __name__ == "__main__":
    sys.exit(main())
