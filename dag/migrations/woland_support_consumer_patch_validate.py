"""Run focused offline tests against an in-memory patch; never alter source trees."""
from __future__ import annotations

import importlib.abc
import importlib.util
import json
import os
import platform
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PREFIX = "woland_support_consumer_patch"
PFP = HERE.parents[1]
ANOMALON = PFP.parent / "anomalon"
REPORT = json.loads((HERE / (PREFIX + ".json")).read_text(encoding="utf-8"))
SOURCES = {
    row["path"][:-3].replace("/", "."): row
    for row in REPORT["changes"]
    if row["repository"] == "anomalon" and row["after"] is not None and row["path"].endswith(".py")
}


class PatchedSource(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in SOURCES:
            return importlib.util.spec_from_loader(fullname, self)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        row = SOURCES[module.__name__]
        module.__file__ = str(ANOMALON / row["path"])
        exec(compile(row["after"], module.__file__, "exec"), module.__dict__)


def main():
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ANOMALON))
    sys.meta_path.insert(0, PatchedSource())
    # Avoid Windows platform metadata spawning `cmd /c ver` in JUnit output.
    platform.node = lambda: "offline-validation"
    # Fail closed if an unexpected test attempts real network/process/native work.
    def audit(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"}:
            raise RuntimeError("OFFLINE_VALIDATION_FORBIDS:" + event)
    sys.addaudithook(audit)
    import pytest

    with tempfile.TemporaryDirectory(prefix=PREFIX + "_", dir=HERE) as temporary:
        temporary = Path(temporary).resolve()
        assert temporary.parent == HERE and temporary.name.startswith(PREFIX + "_")
        config = temporary / "pytest.ini"
        config.write_text("[pytest]\n", encoding="utf-8")
        boundary = temporary / "test_harness_corpus_boundary.py"
        boundary.write_text(SOURCES["omega_engine_woland.tests.research.test_harness_corpus_boundary"]["after"], encoding="utf-8")
        selected = [
            "omega_engine_woland/tests/research/test_harness_contracts.py::test_candidate_allowlist_and_exact_types",
            "omega_engine_woland/tests/research/test_harness_contracts.py::test_partition_counts_and_answer_free_projection",
            "omega_engine_woland/tests/research/test_harness_contracts.py::test_output_schema_and_diagnosis_are_checked",
            "omega_engine_woland/tests/providers/test_harness_anthropic_budget.py::test_missing_cache_or_boolean_usage_is_never_zero_cost",
        ]
        result = pytest.main([
            "-q", "--noconftest", "-p", "no:cacheprovider", "-c", str(config),
            "--basetemp", str(temporary / "pytest-tmp"),
            "--junitxml", str(HERE / (PREFIX + "_validation.xml")),
            *[str(ANOMALON / path) for path in selected], str(boundary),
        ])
    (HERE / (PREFIX + "_validation.json")).write_text(json.dumps({
        "python": sys.version, "executable": sys.executable, "exit_code": int(result),
        "mode": "in-memory patch overlay; original tests and dependencies remain read only",
        "selected_existing_tests": selected,
        "new_test": "omega_engine_woland/tests/research/test_harness_corpus_boundary.py",
        "network_process_guard": "audit hook rejected socket.connect/getaddrinfo, subprocess.Popen, os.system",
        "source_manifest_limit": "Tests hash original source checkout, not overlay bytes; parent must rerun after applying for final binding validation.",
    }, indent=2) + "\n", encoding="utf-8")
    return int(result)


if __name__ == "__main__":
    raise SystemExit(main())
