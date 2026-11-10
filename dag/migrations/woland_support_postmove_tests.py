"""Focused actual-source post-move validation; offline existing native binaries only."""
from __future__ import annotations

import collections
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
PREFIX = "woland_support_postmove_tests"
PFP = HERE.parents[1]
ANOMALON = PFP.parent / "anomalon"
RELEASE = (ANOMALON / "omega_engine/crates_rs/target/release").resolve()
SELECTED = [
    "omega_engine_woland/tests/research/test_harness_contracts.py",
    "omega_engine_woland/tests/research/test_harness_execution.py",
    "omega_engine_woland/tests/research/test_harness_review_regressions.py",
    "omega_engine_woland/tests/research/test_harness_corpus_boundary.py",
    "omega_engine_woland/tests/providers/test_harness_anthropic_budget.py",
    "omega_engine_woland/tests/test_ddc_code_repair.py",
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    os.environ["OMEGA_CREDENTIAL_DISCOVERY"] = "off"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    # No inherited provider credentials are needed for fixture transports.
    for key in tuple(os.environ):
        if "API_KEY" in key.upper() or key.upper().endswith(("_TOKEN", "_SECRET")):
            os.environ.pop(key, None)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ANOMALON))
    platform.node = lambda: "offline-postmove-validation"
    native = {}
    children = collections.Counter()
    refused_network = []
    source_hashes = {path: sha(ANOMALON / path) for path in SELECTED}
    patch = json.loads((HERE / "woland_support_consumer_patch.json").read_text(encoding="utf-8"))
    for row in patch["changes"]:
        if row["repository"] == "anomalon" and row["after"] is not None:
            source_hashes[row["path"]] = sha(ANOMALON / row["path"])
            assert source_hashes[row["path"]] == row["after_sha256"], row["path"]

    def audit(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "os.system"}:
            refused_network.append(event)
            raise RuntimeError("OFFLINE_POSTMOVE_FORBIDS:" + event)
    sys.addaudithook(audit)
    original_popen = subprocess.Popen
    temporary_root = None

    class LocalPopen(original_popen):
        def __init__(self, args, *positional, **kwargs):
            if kwargs.get("shell") or not isinstance(args, (list, tuple)) or not args:
                raise RuntimeError("UNEXPECTED_PROCESS_SHAPE")
            executable = Path(str(args[0]))
            resolved = executable.resolve()
            cwd = Path(kwargs.get("cwd") or Path.cwd()).resolve()
            scoped_cwd = temporary_root is not None and cwd.is_relative_to(temporary_root)
            category = None
            if resolved.parent == RELEASE and resolved.suffix.lower() == ".exe" and resolved.is_file():
                category = "existing_native:" + resolved.name
                native.setdefault(str(resolved), sha(resolved))
            elif executable.name.lower() in {"git", "git.exe"}:
                if "init" in args and temporary_root is not None and Path(args[-1]).resolve().is_relative_to(temporary_root):
                    category = "temporary_git_init"
                elif "apply" in args and scoped_cwd:
                    category = "temporary_git_apply"
            elif resolved == Path(sys.executable).resolve() and scoped_cwd and list(args[1:2]) == ["check.py"]:
                category = "test_owned_python_check"
            elif executable.name == "absent-executable" and scoped_cwd and not resolved.exists():
                category = "expected_missing_test_executable"
            if category is None:
                raise RuntimeError("UNEXPECTED_PROCESS:" + str(args))
            children[category] += 1
            super().__init__(args, *positional, **kwargs)

    subprocess.Popen = LocalPopen
    import pytest
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=PREFIX + "_", dir=HERE) as temporary:
        temporary_root = Path(temporary).resolve()
        assert temporary_root.parent == HERE and temporary_root.name.startswith(PREFIX + "_")
        config = temporary_root / "pytest.ini"
        config.write_text("[pytest]\n", encoding="utf-8")
        # The original guard test only uses these path/digest attributes before
        # refusing. Invoke that exact function without initializing a Windows runner.
        guards = temporary_root / "test_windows_guard_without_runtime.py"
        guards.write_text('''from pathlib import Path
from types import SimpleNamespace
import pytest
from omega_engine_woland.tests.research.test_windows_harness import test_windows_paid_entrypoints_refuse_before_provider_construction as original_guard

@pytest.mark.parametrize("command,extra", [("run", []), ("resume", []), ("preflight", ["--live"])])
def test_actual_windows_guard(tmp_path, monkeypatch, command, extra):
    runner = SimpleNamespace(runtime=tmp_path / "never-opened-runtime", sha256="0" * 64)
    original_guard(runner, tmp_path, monkeypatch, command, extra)
''', encoding="utf-8")
        result = pytest.main([
            "-q", "--noconftest", "-p", "no:cacheprovider", "-c", str(config),
            "--basetemp", str(temporary_root / "pytest-tmp"),
            "--junitxml", str(HERE / (PREFIX + ".xml")),
            *[str(ANOMALON / path) for path in SELECTED], str(guards),
        ])
    subprocess.Popen = original_popen
    elapsed = time.monotonic() - started
    suite = ET.parse(HERE / (PREFIX + ".xml")).getroot().find("testsuite")
    unchanged = all(sha(ANOMALON / path) == expected for path, expected in source_hashes.items())
    unchanged_native = all(sha(path) == expected for path, expected in native.items())
    receipt = {
        "mode": "actual applied source, no source overlay; isolated pytest configuration",
        "base_commit": patch["anomalon_source_commit"],
        "applied_change_hashes_match": True,
        "python": sys.version, "executable": sys.executable,
        "exit_code": int(result), "elapsed_seconds": elapsed,
        "pytest": dict(suite.attrib), "selected": SELECTED,
        "windows_guard": "3 parametrizations of original source test called with inert path/digest attributes; Windows runner setup/execution was not tested",
        "source_sha256": source_hashes, "sources_unchanged_after_tests": unchanged,
        "existing_native_sha256": native, "native_bytes_unchanged": unchanged_native,
        "child_process_counts": dict(children), "blocked_network_events": refused_network,
        "credential_discovery": "off; inherited API-key/token/secret environment entries removed without logging values",
        "limitations": [
            "Focused offline suites only; provider calls use fixtures, with parent-process socket/DNS calls refused.",
            "Child processes restricted to existing release native executables, temporary git init/apply, test-owned check.py and intentional absent check; no rebuilds.",
            "No actual Windows isolation runner, live provider, historical archive, relocated solver calibration or full repository suite was exercised here.",
        ],
    }
    (HERE / (PREFIX + ".json")).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"exit_code": int(result), "tests": suite.attrib, "unchanged_sources": unchanged, "unchanged_native": unchanged_native}))
    return int(result) or int(not unchanged or not unchanged_native)


if __name__ == "__main__":
    raise SystemExit(main())
