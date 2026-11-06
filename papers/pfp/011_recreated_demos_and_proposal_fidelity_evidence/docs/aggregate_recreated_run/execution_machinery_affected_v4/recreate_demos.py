"""Pinned, offline recreation machinery for PAPER 011; no solver is implemented here.

The retained algorithms run in bounded child processes. Import relocation is
receipt-visible. Native evidence and preserved Python algorithms have different
evidence grades, and missing inputs/checkers are explicit unresolved obligations.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.abc
import importlib.util
import inspect
import io
import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

SCHEMA = "paper011.recreated-run.v1"
OLD_PREFIX = "projects.mssn_sn_symgam"
LOCAL_PREFIX = "paper011_source"
ENGINE_ROOTS = (
    "engine/kernel",
    "pfp",
    "eis",
    "providers",
    "adversary",
    "operating_system",
)
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", "target", "node_modules", ".git"}
MUTATION_ANSWER_KEYS = (
    "corrupted_result",
    "corrupted_output",
    "corrupted_answer",
    "corrupted_ans",
    "corrupted_solution",
    "mutated_result",
    "mutated_answer",
    "mutated_output",
    "certificate",
    "candidate",
    "answer",
    "result",
)


class ReplayError(ValueError):
    """A custody failure or unavailable explicit capability."""


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReplayError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def load(raw: bytes) -> object:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ReplayError("BOM_REFUSED")
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ReplayError("NONFINITE_JSON")),
    )


def regular(path: Path, directory: bool = False) -> None:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(
        stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400
    ):
        raise ReplayError("REDIRECTED_ENTRY")
    if not (stat.S_ISDIR if directory else stat.S_ISREG)(info.st_mode):
        raise ReplayError("NONREGULAR_ENTRY")


def source_files(root: Path) -> dict[str, str]:
    regular(root, True)
    found = {}

    def visit(folder: Path) -> None:
        regular(folder, True)
        for child in sorted(folder.iterdir(), key=lambda p: p.name.encode("utf-8")):
            if child.name in EXCLUDED_PARTS:
                continue
            regular(child, child.is_dir())
            if child.is_dir():
                visit(child)
            else:
                found[child.relative_to(root).as_posix()] = digest(child.read_bytes())

    visit(root)
    return found


def local_module(name: str, filename: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ReplayError("LOCAL_MODULE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_catalog(source: Path) -> dict:
    return local_module("paper011_demo_catalog", "demo_catalog.py").build_catalog(source)


def engine_lock(
    engine: Path,
    source_head: str,
    native: Path,
    functional: Path | None,
    verifiers: dict[str, Path] | None = None,
    build_receipt: Path | None = None,
) -> dict:
    head = subprocess.run(
        ["git", "-C", str(engine), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    if head != source_head:
        raise ReplayError("ENGINE_HEAD_MISMATCH")
    raw = subprocess.run(
        ["git", "-C", str(engine), "ls-files", "-z", "--", *ENGINE_ROOTS],
        check=True,
        capture_output=True,
    ).stdout
    paths = sorted(
        {p.decode("utf-8") for p in raw.split(b"\0") if p}, key=lambda p: p.encode("utf-8")
    )
    files = {}
    for path in paths:
        candidate = engine / path
        regular(candidate)
        files[path] = digest(candidate.read_bytes())
    regular(native)
    binaries = {
        "symbol_game": {"path": str(native.resolve()), "sha256": digest(native.read_bytes())}
    }
    if functional:
        regular(functional)
        binaries["graph_functional"] = {
            "path": str(functional.resolve()),
            "sha256": digest(functional.read_bytes()),
        }
    for name, path in (verifiers or {}).items():
        if name not in {"verify_phi2", "verify_phi3", "verify_phi4", "verify_wall_functionals"}:
            raise ReplayError("UNKNOWN_NATIVE_VERIFIER")
        regular(path)
        binaries[name] = {"path": str(path.resolve()), "sha256": digest(path.read_bytes())}
    provenance = None
    if build_receipt is not None:
        regular(build_receipt)
        raw_receipt = build_receipt.read_bytes()
        build = load(raw_receipt)
        declared = {entry["name"]: entry["sha256"] for entry in build["binaries"]}
        if (
            build.get("source_git_head") != source_head
            or build.get("native_tracked_diff_exit") != 0
            or any(command.get("exit_code") != 0 for command in build["commands"])
            or any(
                declared.get(Path(entry["path"]).name) != entry["sha256"]
                for entry in binaries.values()
            )
        ):
            raise ReplayError("NATIVE_BUILD_RECEIPT_MISMATCH")
        provenance = {"path": str(build_receipt.resolve()), "sha256": digest(raw_receipt)}
    return {
        "schema_version": "paper011.engine-capability.v1",
        "source_git_head": source_head,
        "engine_root": str(engine.resolve()),
        "files": files,
        "binaries": binaries,
        "source_to_binary_provenance": "BYTE_BOUND_BUILD_RECEIPT"
        if provenance
        else "CALLER_BUILD_RECEIPT_REQUIRED",
        "build_receipt": provenance,
        "python": {"executable": str(Path(sys.executable).resolve()), "version": sys.version},
        "authority_effect": "None",
    }


def verify_runtime_environment(lock: dict, *, full_runtime: bool) -> None:
    binding = lock.get("runtime_environment")
    if binding is None:
        return
    if binding.get("schema_version") != "paper011.runtime-environment.v1":
        raise ReplayError("RUNTIME_ENVIRONMENT_SCHEMA_MISMATCH")
    for stem in ("profile", "verifier"):
        path = Path(binding[stem + "_path"])
        regular(path)
        if digest(path.read_bytes()) != binding[stem + "_sha256"]:
            raise ReplayError("RUNTIME_ENVIRONMENT_BYTES_CHANGED")
    profile = load(Path(binding["profile_path"]).read_bytes())
    if profile.get("schema_version") != binding["schema_version"]:
        raise ReplayError("RUNTIME_ENVIRONMENT_SCHEMA_MISMATCH")
    if full_runtime:
        import types

        path = Path(binding["verifier_path"])
        module = types.ModuleType("paper011_runtime_environment_verifier")
        module.__file__ = str(path)
        exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
        if module.verify(profile).get("status") != "DECLARED_RUNTIME_FILES_UNCHANGED":
            raise ReplayError("RUNTIME_ENVIRONMENT_VERIFICATION_FAILED")


def verify_engine(lock: dict, *, full_runtime: bool = True) -> Path:
    if lock.get("schema_version") != "paper011.engine-capability.v1" or not lock.get("files"):
        raise ReplayError("ENGINE_CAPABILITY_MISSING")
    engine = Path(lock["engine_root"])
    regular(engine, True)
    verified_directories = {engine}
    for relative, expected in lock["files"].items():
        if (
            type(relative) is not str
            or ":" in relative
            or "\\" in relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))
        ):
            raise ReplayError("ENGINE_PATH_ESCAPE")
        path = engine
        for part in relative.split("/")[:-1]:
            path /= part
            if path not in verified_directories:
                regular(path, True)
                verified_directories.add(path)
        path /= relative.split("/")[-1]
        regular(path)
        if digest(path.read_bytes()) != expected:
            raise ReplayError("ENGINE_BYTES_CHANGED: " + relative)
    for row in lock["binaries"].values():
        binary = Path(row["path"])
        regular(binary)
        if digest(binary.read_bytes()) != row["sha256"]:
            raise ReplayError("NATIVE_BYTES_CHANGED")
    if lock.get("build_receipt"):
        row = lock["build_receipt"]
        regular(Path(row["path"]))
        if digest(Path(row["path"]).read_bytes()) != row["sha256"]:
            raise ReplayError("NATIVE_BUILD_RECEIPT_CHANGED")
    verify_runtime_environment(lock, full_runtime=full_runtime)
    return engine


def relocate_source(
    raw: bytes, filename: str, engine_root: str | None = None
) -> tuple[bytes, list[dict]]:
    """Change import routing and remove obsolete bootstrap/main, never math nodes."""
    tree = ast.parse(raw, filename=filename)
    changes = []

    def bootstrap(node: ast.AST) -> bool:
        return isinstance(node, (ast.For, ast.If, ast.Expr)) and any(
            isinstance(child, ast.Attribute)
            and child.attr == "path"
            and isinstance(child.value, ast.Name)
            and child.value.id == "sys"
            for child in ast.walk(node)
        )

    retained = []
    for node in tree.body:
        if (
            engine_root is not None
            and Path(filename).name == "demos_runner.py"
            and isinstance(node, ast.FunctionDef)
            and node.name == "repo_root"
        ):
            node.body = [
                ast.Return(ast.Call(ast.Name("Path", ast.Load()), [ast.Constant(engine_root)], []))
            ]
            changes.append(
                {
                    "kind": "BIND_EXPLICIT_ENGINE_ROOT",
                    "line": node.lineno,
                    "engine_root": engine_root,
                }
            )
        if bootstrap(node):
            changes.append({"kind": "REMOVE_OBSOLETE_SYS_PATH_BOOTSTRAP", "line": node.lineno})
            continue
        if isinstance(node, ast.If) and any(
            isinstance(n, ast.Name) and n.id == "__name__" for n in ast.walk(node.test)
        ):
            changes.append({"kind": "REMOVE_SCRIPT_MAIN", "line": node.lineno})
            continue
        retained.append(node)
    tree.body = retained
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            parts = Path(filename).parts
            if "challenges" in parts:
                index = parts.index("challenges")
                prefix = ".".join((LOCAL_PREFIX, *parts[index : index + 3]))
                if node.module.split(".")[0] in {"reference_solver", "judge_packet"}:
                    before = node.module
                    node.module = prefix + "." + before
                    changes.append(
                        {
                            "kind": "BIND_PACKAGE_LOCAL_IMPORT",
                            "line": node.lineno,
                            "before": before,
                            "after": node.module,
                        }
                    )
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and (node.module == OLD_PREFIX or node.module.startswith(OLD_PREFIX + "."))
        ):
            before = node.module
            node.module = LOCAL_PREFIX + node.module[len(OLD_PREFIX) :]
            changes.append(
                {
                    "kind": "RELOCATE_IMPORT",
                    "line": node.lineno,
                    "before": before,
                    "after": node.module,
                }
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == OLD_PREFIX or alias.name.startswith(OLD_PREFIX + "."):
                    if not alias.asname:
                        raise ReplayError("UNALIASED_IMPORT_RELOCATION_REQUIRES_REVIEW")
                    before = alias.name
                    alias.name = LOCAL_PREFIX + alias.name[len(OLD_PREFIX) :]
                    changes.append(
                        {
                            "kind": "RELOCATE_IMPORT",
                            "line": node.lineno,
                            "before": before,
                            "after": alias.name,
                        }
                    )
    transformed = (ast.unparse(ast.fix_missing_locations(tree)) + "\n").encode("utf-8")
    return transformed, changes


class SourceLoader(importlib.abc.Loader):
    def __init__(self, path: Path, root: Path, journal: list):
        self.path, self.root, self.journal = path, root, journal

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        regular(self.path)
        original = self.path.read_bytes()
        transformed, changes = relocate_source(
            original, str(self.path), os.environ.get("PAPER011_ENGINE_ROOT")
        )
        self.journal.append(
            {
                "path": self.path.relative_to(self.root).as_posix(),
                "source_sha256": digest(original),
                "transformed_sha256": digest(transformed),
                "allowed_changes": changes,
            }
        )
        module.__file__ = str(self.path)
        exec(compile(transformed, str(self.path), "exec"), module.__dict__)


class SourceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, root: Path, journal: list):
        self.root, self.journal = root, journal

    def find_spec(self, fullname, path=None, target=None):
        if fullname != LOCAL_PREFIX and not fullname.startswith(LOCAL_PREFIX + "."):
            return None
        relative = fullname.removeprefix(LOCAL_PREFIX).lstrip(".")
        base = self.root.joinpath(*relative.split(".")) if relative else self.root
        if base.is_dir():
            initial = base / "__init__.py"
            if initial.is_file():
                return importlib.util.spec_from_file_location(
                    fullname,
                    initial,
                    loader=SourceLoader(initial, self.root, self.journal),
                    submodule_search_locations=[str(base)],
                )
            spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
            spec.submodule_search_locations = [str(base)]
            return spec
        filename = base.with_suffix(".py")
        if filename.is_file():
            return importlib.util.spec_from_file_location(
                fullname, filename, loader=SourceLoader(filename, self.root, self.journal)
            )
        return None


def lean_work_files(cwd: str | Path | None) -> dict:
    """Bind the original wrapper's temporary proof, judge and imported module."""
    if cwd is None:
        return {}
    folder = Path(cwd)
    regular(folder, True)
    bindings = {}
    for name in ("Submission.lean", "Judge.lean", "Submission.olean"):
        path = folder / name
        if path.exists():
            regular(path)
            raw = path.read_bytes()
            bindings[name] = {"sha256": digest(raw), "bytes_hex": raw.hex()}
    return bindings


def configure_worker(source: Path, lock: dict, journal: list, output: Path | None = None) -> None:
    import shutil

    original_which = shutil.which

    def pinned_which(command, *args, **kwargs):
        if str(command).casefold() in {"lean", "lean.exe"}:
            declared = lock["binaries"].get("lean")
            return declared["path"] if declared else None
        return original_which(command, *args, **kwargs)

    shutil.which = pinned_which

    def blocked(*args, **kwargs):
        raise ReplayError("NETWORK_DISABLED_FOR_SOURCE_RECREATION")

    original_socket_type = socket.socket

    class BlockedSocket(original_socket_type):
        def __init__(self, *args, **kwargs):
            blocked(*args, **kwargs)

    socket.socket = BlockedSocket
    socket.create_connection = blocked
    socket.getaddrinfo = blocked
    real_run = subprocess.run

    def no_implicit_build(command, *args, **kwargs):
        if (
            isinstance(command, (list, tuple))
            and command
            and Path(str(command[0])).stem.casefold() in {"cargo", "rustc"}
        ):
            if "--bin" not in command:
                raise ReplayError("IMPLICIT_NATIVE_BUILD_REFUSED")
            name = command[command.index("--bin") + 1]
            key = {"solve_graph_phi1": "graph_functional", "core_symbol_game": "symbol_game"}.get(
                name, name
            )
            native = lock["binaries"].get(key)
            if native is None:
                raise ReplayError("PINNED_NATIVE_VERIFIER_UNAVAILABLE: " + name)
            journal.append(
                {
                    "kind": "EXPLICIT_NATIVE_TRANSPORT_REBINDING",
                    "original_command": list(command),
                    "binary_name": name,
                    "binary_sha256": native["sha256"],
                }
            )
            command = [
                native["path"],
                *(command[command.index("--") + 1 :] if "--" in command else []),
            ]
        native = next(
            (
                row
                for row in lock["binaries"].values()
                if isinstance(command, (list, tuple)) and command and str(command[0]) == row["path"]
            ),
            None,
        )
        if native and digest(Path(native["path"]).read_bytes()) != native["sha256"]:
            raise ReplayError("NATIVE_BYTES_CHANGED")
        native_key = next((key for key, value in lock["binaries"].items() if value is native), None)
        work_before = lean_work_files(kwargs.get("cwd")) if native_key == "lean" else {}
        native_kwargs = dict(kwargs)
        text_mode = bool(
            kwargs.get("text")
            or kwargs.get("universal_newlines")
            or kwargs.get("encoding") is not None
            or kwargs.get("errors") is not None
        )
        encoding = errors = None
        if native and text_mode:
            encoding = kwargs.get("encoding") or subprocess._text_encoding()
            errors = kwargs.get("errors") or "strict"
            if native_kwargs.get("input") is not None:
                native_kwargs["input"] = native_kwargs["input"].encode(encoding, errors)
            native_kwargs["text"] = False
            for key in ("encoding", "errors", "universal_newlines"):
                native_kwargs.pop(key, None)
        observed = real_run(command, *args, **(native_kwargs if native else kwargs))
        raw_stdout = observed.stdout
        raw_stderr = observed.stderr
        if native and text_mode:

            def decode_view(raw):
                return (
                    raw.decode(encoding, errors).replace("\r\n", "\n").replace("\r", "\n")
                    if raw is not None
                    else None
                )

            result = subprocess.CompletedProcess(
                observed.args, observed.returncode, decode_view(raw_stdout), decode_view(raw_stderr)
            )
        else:
            result = observed
        if native:
            if digest(Path(native["path"]).read_bytes()) != native["sha256"]:
                raise ReplayError("NATIVE_BYTES_CHANGED_AFTER_CALL")
            work_after = lean_work_files(kwargs.get("cwd")) if native_key == "lean" else {}
            if any(
                name.endswith(".lean") and work_after.get(name) != binding
                for name, binding in work_before.items()
            ):
                raise ReplayError("LEAN_INPUT_BYTES_CHANGED_DURING_CALL")
            if output:
                request = native_kwargs.get("input", b"") or b""
                response = raw_stdout or b""
                error = raw_stderr or b""
                with (output / "native_transport_calls.jsonl").open("ab") as stream:
                    stream.write(
                        canonical(
                            {
                                "binary_sha256": native["sha256"],
                                "binary_key": native_key,
                                "command": [str(item) for item in command],
                                "cwd": str(Path(kwargs["cwd"]).absolute())
                                if kwargs.get("cwd") is not None
                                else None,
                                "work_files_before": work_before,
                                "work_files_after": work_after,
                                "stdio_capture": "RAW_SUBPROCESS_BYTES",
                                "source_text_view": {
                                    "encoding": encoding,
                                    "errors": errors,
                                    "newline_normalization": "SUBPROCESS_UNIVERSAL_NEWLINES",
                                }
                                if text_mode
                                else None,
                                "request_bytes_hex": request.hex(),
                                "stdout_bytes_hex": response.hex(),
                                "stderr_bytes_hex": error.hex(),
                                "process_exit": result.returncode,
                            }
                        )
                        + b"\n"
                    )
        return result

    subprocess.run = no_implicit_build
    sys.meta_path.insert(0, SourceFinder(source, journal))
    os.environ["CORE_SYMBOL_GAME_HOST"] = lock["binaries"]["symbol_game"]["path"]
    os.environ["PAPER011_ENGINE_ROOT"] = lock["engine_root"]
    functional = lock["binaries"].get("graph_functional")
    if functional:
        os.environ["CORE_FUNCTIONAL_GRAPH_BIN"] = functional["path"]
        os.environ["CORE_FUNCTIONAL_GRAPH_SHA256"] = functional["sha256"]


def trace_native_calls(output: Path) -> None:
    """Record actual OEOS native requests/responses without changing verdicts."""
    from operating_system.python.adapters.rust_host.ffi import RustSymbolGameHost

    original = RustSymbolGameHost.invoke_runtime
    tape = output / "native_calls.jsonl"

    def recorded(self, action, payload):
        result = original(self, action, payload)
        envelope = (
            result.unwrap()
            if result.is_ok
            else {
                "refusal": {
                    "code": result.unwrap_err().code,
                    "message": result.unwrap_err().message,
                }
            }
        )
        with tape.open("ab") as stream:
            stream.write(
                canonical(
                    {
                        "action": action,
                        "request": _jsonable(payload),
                        "response": _jsonable(envelope),
                    }
                )
                + b"\n"
            )
        return result

    RustSymbolGameHost.invoke_runtime = recorded


def native_demo(row: dict, source: Path, output: Path) -> dict:
    """Reuse source orchestration, with explicit current-engine case dispatch fixes."""
    import importlib

    cid = row["id"]
    if cid == "demo_cohomology_battery":
        from pfp import initialize_exact_ports
        from pfp.use_cases.mssn_sn_demos.demo_cohomology_battery.run import (
            run_cohomology_battery,
        )

        initialize_exact_ports()
        return run_cohomology_battery(
            cases_dir=source / "demos/demo_cohomology_battery/cases", output_dir=output
        )
    if cid == "demo_q40_quantum_solver":
        from pfp import initialize_exact_ports
        from pfp.infrastructure.quantum.dense_checker import (
            verify_dense_spectrum,
        )
        from pfp.use_cases.mssn_sn_demos.demo_q40_quantum_solver.run import (
            run_benchmark_40,
        )

        initialize_exact_ports()
        return run_benchmark_40(
            cases_dir=source / "demos/demo_q40_quantum_solver/cases",
            output_dir=output,
            dense_spectrum=verify_dense_spectrum,
        )
    runner = importlib.import_module(LOCAL_PREFIX + ".demos.demos_runner")
    arguments = ["--output-dir", str(output)]
    if cid in {
        "demo_4",
        "demo_6",
        "demo_7",
        "demo_8",
        "demo_9",
        "demo_11",
        "demo_12",
        "demo_symbol_tui",
    }:
        output.mkdir(parents=True, exist_ok=False)
        arguments = [
            "--output",
            str(output / ("illustration.txt" if cid == "demo_symbol_tui" else "receipt.json")),
        ]
    if cid == "demo_4e_cogsci_autopoiesis":
        arguments = ["run", cid, *arguments]
    if cid == "antimorphism_farm":
        arguments = ["run", *arguments]
    if cid == "demo_adversary_tribunal":
        arguments = ["run", cid, *arguments]
    if cid == "demo_12":
        arguments.extend(
            [
                "--catalog",
                str(
                    Path(os.environ["PAPER011_ENGINE_ROOT"])
                    / "pfp/infrastructure/adapters/mssn_research/fixtures/demo_12.json"
                ),
            ]
        )
    result = runner.DEMO_DISPATCH[cid](arguments)
    payloads = {}
    if output.exists():
        for path in sorted(output.rglob("*.json")):
            try:
                payloads[path.relative_to(output).as_posix()] = load(path.read_bytes())
            except (ValueError, UnicodeDecodeError):
                pass
    return {
        "dispatch_return": result,
        "actual_engine_payloads": payloads,
        "scope": "Current canonical engine adapters, preserved inputs; native outcomes must be inspected separately.",
    }


def phi2_dossier_recreation(
    module, folder: Path, source: Path, engine: Path, output: Path | None
) -> dict:
    """Call the retained Phi2 seam with explicit data and native evidence custody."""
    import yaml

    bindings = []
    raw = {}
    for name in ("input.yaml", "witness_valid.json", "witness_near_miss.json"):
        path = folder / name
        regular(path)
        raw[name] = path.read_bytes()
        bindings.append(
            {"source_path": path.relative_to(source).as_posix(), "sha256": digest(raw[name])}
        )
    inp = yaml.safe_load(raw["input.yaml"])
    witness = load(raw["witness_valid.json"])
    near_misses = load(raw["witness_near_miss.json"])
    if type(near_misses) is not list or len(near_misses) != 4:
        raise ReplayError("DECLARED_PHI2_NEAR_MISS_COVERAGE_MISMATCH")
    tape = output / "native_transport_calls.jsonl" if output is not None else None
    start = tape.stat().st_size if tape is not None and tape.exists() else 0
    valid = _jsonable(module.check_exact_phi2_certificate(inp, witness, engine))
    captured = tape.read_bytes()[start:] if tape is not None and tape.exists() else b""
    verified = False
    for line in captured.splitlines():
        event = load(line)
        if event.get("binary_key") == "verify_phi2" and event.get("process_exit") == 0:
            response = load(bytes.fromhex(event["stdout_bytes_hex"]))
            request = load(bytes.fromhex(event["request_bytes_hex"]))
            verified |= (
                response.get("status") == "PASS"
                and str(response.get("reported_value")) == str(valid.get("phi2_val"))
                and str(response.get("duality_gap")) == "0"
                and str(request.get("reported_value")) == str(valid.get("phi2_val"))
            )
    verified = verified and valid.get("rust_engine_coupled") == "PASS"
    rejected = []
    for candidate in near_misses:
        result = _jsonable(module.check_exact_phi2_certificate(inp, candidate, engine))
        rejected.append({"case_name": candidate.get("case_name"), "result": result})
    return {
        "function": "check_exact_phi2_certificate",
        "input_bindings": bindings,
        "engine_root_binding": str(engine),
        "resource_binding": "EXPLICIT_RETAINED_INPUTS_AND_ENGINE_ROOT",
        "native_valid_witness_verified": bool(verified),
        "valid_native_transport_sha256": digest(captured),
        "betti_scope": "DECLARED_SOURCE_METADATA_NOT_A_RANK_PROOF",
        "result": {"valid_witness_result": valid, "near_miss_results": rejected},
    }


def dossier_recreations(
    cid: str, source: Path, engine: Path, output: Path | None = None
) -> list[dict]:
    """Run preserved positive and near-miss audits in isolated writable dossiers.

    Original native transport requests use explicitly pinned verifier binaries.
    Rebinding is recorded separately and does not change the certificate wire.
    """
    import importlib
    import shutil

    folder = source / "demos" / cid
    if not folder.is_dir():
        return []
    reports = []
    for checker in sorted(folder.rglob("checker.py"), key=lambda p: p.as_posix().encode("utf-8")):
        relative = checker.relative_to(source).with_suffix("").as_posix().replace("/", ".")
        row = {
            "checker_path": checker.relative_to(source).as_posix(),
            "grade": "SOURCE_RECREATION_PYTHON",
            "native_verification": "INSPECT_ACTUAL_NATIVE_TRANSPORT_TAPE",
        }
        try:
            module = importlib.import_module(LOCAL_PREFIX + "." + relative)
            if cid == "demo_6" and callable(getattr(module, "check_exact_phi2_certificate", None)):
                audit = phi2_dossier_recreation(module, checker.parent, source, engine, output)
                row.update(
                    {
                        "status": "AUDIT_EXECUTED"
                        if audit["native_valid_witness_verified"]
                        else "NATIVE_POSITIVE_UNVERIFIED",
                        "outputs": [audit],
                    }
                )
                if not audit["native_valid_witness_verified"]:
                    row["obligation"] = (
                        "Require the actual bound verify_phi2 transport PASS; the source CERTIFIED label alone is insufficient."
                    )
                reports.append(row)
                continue
            audits = [
                function
                for name, function in vars(module).items()
                if inspect.isfunction(function)
                and function.__module__ == module.__name__
                and name.startswith("run_")
                and "audit" in name
                and not name.startswith("run_rust")
            ]
            if not audits:
                audits = [
                    function
                    for name, function in vars(module).items()
                    if inspect.isfunction(function)
                    and function.__module__ == module.__name__
                    and name.startswith("verify_dossier")
                    and "input_path" in inspect.signature(function).parameters
                ]
            if not audits:
                if callable(getattr(module, "run_standalone", None)):
                    audits = [module.run_standalone]
            if not audits:
                row.update(
                    {
                        "status": "UNRESOLVED_AUDIT_ENTRYPOINT",
                        "obligation": "Bind this retained checker to its declared input and witness signatures.",
                    }
                )
                reports.append(row)
                continue
            outputs = []
            for audit in audits:
                with tempfile.TemporaryDirectory(prefix="paper011-dossier-") as directory:
                    scratch = Path(directory) / checker.parent.name
                    shutil.copytree(
                        checker.parent, scratch, ignore=shutil.ignore_patterns("__pycache__")
                    )
                    bindings = []
                    input_root = source / "demos/inputs" / cid / checker.parent.name
                    for name in ("input.yaml", "witness_valid.json", "witness_near_miss.json"):
                        if not (scratch / name).exists() and (input_root / name).is_file():
                            regular(input_root / name)
                            raw = (input_root / name).read_bytes()
                            (scratch / name).write_bytes(raw)
                            bindings.append(
                                {
                                    "source_path": (input_root / name)
                                    .relative_to(source)
                                    .as_posix(),
                                    "sha256": digest(raw),
                                    "dossier_path": name,
                                }
                            )
                    parameters = inspect.signature(audit).parameters
                    arguments = {}
                    for name, parameter in parameters.items():
                        if name in {"dossier_dir", "directory", "root", "base_dir", "dossier_root"}:
                            arguments[name] = scratch
                        elif name in {"repo_root", "repository_root"}:
                            arguments[name] = engine
                        elif name in {
                            "input_path",
                            "valid_path",
                            "valid_witness_path",
                            "near_miss_path",
                        }:
                            arguments[name] = (
                                scratch
                                / {
                                    "input_path": "input.yaml",
                                    "valid_path": "witness_valid.json",
                                    "valid_witness_path": "witness_valid.json",
                                    "near_miss_path": "witness_near_miss.json",
                                }[name]
                            )
                        elif parameter.default is inspect.Parameter.empty:
                            raise ReplayError("UNRESOLVED_AUDIT_PARAMETER: " + name)
                    original_file = module.__file__
                    try:
                        module.__file__ = str(scratch / checker.name)
                        audit_result = _jsonable(audit(**arguments))
                    finally:
                        module.__file__ = original_file
                    outputs.append(
                        {
                            "function": audit.__name__,
                            "input_bindings": bindings,
                            "resource_binding": "TEMPORARY_COPY_OF_DECLARED_DOSSIER",
                            "result": audit_result,
                        }
                    )
            row.update({"status": "AUDIT_EXECUTED", "outputs": outputs})
        except Exception as exc:
            row.update(
                {
                    "status": "REPRODUCTION_GAP",
                    "exception": type(exc).__name__,
                    "detail": str(exc),
                    "obligation": "Resolve the retained audit's explicit input/capability contract without changing its mathematical algorithm.",
                }
            )
        reports.append(row)
    return reports


def _callable(prefix: str, descriptor: dict):
    import importlib

    return getattr(
        importlib.import_module(prefix + "." + descriptor["module"]), descriptor["function"]
    )


def _jsonable(value: object) -> object:
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float:
        return {"inexact_float_repr": repr(value)}
    if type(value) is dict:
        return {str(k): _jsonable(v) for k, v in value.items()}
    if type(value) in (list, tuple):
        return [_jsonable(v) for v in value]
    return {"type": type(value).__name__, "repr": repr(value)}


def checker_accepts(value: object) -> bool | None:
    if type(value) is bool:
        return value
    if type(value) in (tuple, list) and value and type(value[0]) is bool:
        return value[0]
    if type(value) is dict:
        for key in ("valid", "passed", "accepted", "ok", "success", "verified"):
            if type(value.get(key)) is bool:
                return value[key]
        if type(value.get("verdict")) is str:
            if value["verdict"].upper() in {"PASS", "ACCEPT", "VALID", "VERIFIED"}:
                return True
            if value["verdict"].upper() in {"FAIL", "REFUSE", "REJECT", "INVALID"}:
                return False
    return None


def _case(package: Path, ref: dict):
    path = package / ref["path"]
    raw = path.read_bytes()
    if digest(raw) != ref["sha256"]:
        raise ReplayError("INPUT_DIGEST_MISMATCH")
    data = load(raw)
    if ref["index"] is not None:
        data = (data["cases"] if type(data) is dict else data)[ref["index"]]
    return data


def declared_input(row: dict, data: object) -> object:
    """C024's retained scoring/test contract passes the input envelope member."""
    if row["id"] == "C024" and type(data) is dict:
        return data.get("input", data)
    return data


def candidate_class(answer: object) -> str:
    if type(answer) is not dict:
        return "UNLABELED"
    status = answer.get("status", answer.get("verdict"))
    if status == "UNKNOWN":
        return "ABSTENTION"
    if status in {
        "REFUSED",
        "OUT_OF_SCOPE",
        "UNSUPPORTED",
        "NO_SOLUTION",
        "REFUSE",
        "NO_NATIVE_PORT",
        "UNSUPPORTED_NATIVE_PORT",
    }:
        return "TYPED_REFUSAL"
    if status in {"INCONSISTENT", "UNSAT", "UNSATISFIABLE", "INFEASIBLE"} or answer.get("kind") in {
        "DOES_NOT_EXIST",
        "NOT_ADJOINT",
        "UNSAT",
        "REFUTATION",
    }:
        return "NEGATIVE_CLAIM"
    if "verdict" in answer and "status" not in answer:
        return "CLASSIFIER_DECISION"
    return "CANDIDATE"


def supplemental_c041(row: dict, source: Path, stream, binding: dict) -> dict:
    """Check exactly two explicit proposals; leave full historical solver evidence intact."""
    path = Path(binding["path"])
    regular(path)
    raw = path.read_bytes()
    if digest(raw) != binding["sha256"]:
        raise ReplayError("SUPPLEMENTAL_PROPOSAL_BYTES_CHANGED")
    proposals = load(raw)
    if (
        row["id"] != "C041"
        or proposals.get("schema_version") != "paper011.c041-supplemental-proposals.v1"
        or type(proposals.get("rows")) is not list
        or len(proposals["rows"]) != 2
    ):
        raise ReplayError("SUPPLEMENTAL_SCOPE_MISMATCH")
    expected_ids = {"c041_base_16", "c041_ctrl_08"}
    if {entry["original_case"].get("case_id") for entry in proposals["rows"]} != expected_ids:
        raise ReplayError("SUPPLEMENTAL_TARGET_SET_MISMATCH")
    package = source / row["package"]
    by_sha = {ref["sha256"]: ref for ref in row["cases"]}
    checkers = [_callable(row["module"], entry) for entry in row["checkers"]]
    if len(checkers) != 2:
        raise ReplayError("SUPPLEMENTAL_CHECKER_CONTRACT_MISMATCH")
    accepted = controls = rejections = 0
    selected = []
    for proposal in proposals["rows"]:
        ref = by_sha.get(proposal["original_case_sha256"])
        if ref is None:
            raise ReplayError("SUPPLEMENTAL_ORIGINAL_CASE_UNBOUND")
        case = _case(package, ref)
        if (
            case != proposal["original_case"]
            or proposal["candidate"].get("case_id") != case["case_id"]
        ):
            raise ReplayError("SUPPLEMENTAL_INTERPRETATION_CHANGED")
        answer = proposal["candidate"]
        checks = [function(case, answer) for function in checkers]
        ok = all(checker_accepts(check) is True for check in checks)
        accepted += ok
        selected.append({"case_id": case["case_id"], "input": ref, "accepted": ok})
        stream.write(
            canonical(
                {
                    "supplemental": True,
                    "input": ref,
                    "case": case,
                    "answer": answer,
                    "checks": _jsonable(checks),
                    "accepted": ok,
                    "proposal_fixture_sha256": binding["sha256"],
                }
            )
            + b"\n"
        )
        stream.flush()
        for mutation in ("CORRUPTED_PROOF", "WRONG_TARGET_KIND"):
            changed = load(canonical(answer))
            if mutation == "CORRUPTED_PROOF":
                changed["proof"] = "by sorry"
            else:
                changed["kind"] = "PROOF" if answer["kind"] == "REFUTATION" else "REFUTATION"
            checks = [function(case, changed) for function in checkers]
            rejected = all(checker_accepts(check) is False for check in checks)
            controls += 1
            rejections += rejected
            stream.write(
                canonical(
                    {
                        "supplemental_control": mutation,
                        "input": ref,
                        "case": case,
                        "answer": changed,
                        "checks": _jsonable(checks),
                        "dual_rejected": rejected,
                    }
                )
                + b"\n"
            )
            stream.flush()
    if digest(path.read_bytes()) != binding["sha256"]:
        raise ReplayError("SUPPLEMENTAL_PROPOSAL_BYTES_CHANGED_AFTER_CHECK")
    return {
        "status": "SUPPLEMENTAL_PROPOSALS_CHECKED"
        if accepted == 2 and rejections == 4
        else "SUPPLEMENTAL_PROPOSAL_RESIDUAL",
        "execution_scope": "SUPPLEMENTAL_SELECTED_CANDIDATES",
        "grade": "SOURCE_CHECKER_AND_PINNED_KERNEL_PROPOSAL_CHECK",
        "proposal_binding": binding,
        "selected_targets": selected,
        "selected_case_count": 2,
        "accepted_selected_candidates": accepted,
        "supplemental_control_count": controls,
        "supplemental_dual_rejections": rejections,
        "original_catalog_case_count": len(row["cases"]),
        "original_catalog_mutation_count": len(row["mutations"]),
        "original_reference_solver_invoked": False,
        "full_source_case_execution": False,
        "full_source_mutation_execution": False,
        "original_solver_abstentions_preserved": True,
        "algorithm_independence": "SHARED_SOURCE_COMPILER_WRAPPER",
        "model_accuracy": None,
    }


def reference_challenge(row: dict, source: Path, stream) -> dict:
    if row["kind"] == "SPECIFICATION_ONLY":
        return {"status": "UNRESOLVED_SPECIFICATION", "obligation": row["obligation"]}
    if row["kind"] == "MECHANISM_RECREATION":
        return {
            "status": "MECHANISM_ADAPTER_REQUIRED",
            "implementation": row["implementation"],
            "obligation": row["obligation"],
        }
    single_gate = row.get("checker_contract") == "DECLARED_BRANCH_EVALUATOR"
    if not row["solver"] or len(row["checkers"]) < (1 if single_gate else 2) or not row["cases"]:
        return {
            "status": "UNRESOLVED_EXECUTION_CONTRACT",
            "solver": row["solver"],
            "checker_count": len(row["checkers"]),
            "case_count": len(row["cases"]),
            "obligation": "Resolve the source scoring script's exact solver/checker signatures and nonempty scored inputs.",
        }
    prefix, package = row["module"], source / row["package"]
    solver = _callable(prefix, row["solver"])
    checkers = [_callable(prefix, entry) for entry in row["checkers"]]
    counts = {
        "cases": 0,
        "both_accept": 0,
        "all_declared_accept": 0,
        "abstentions": 0,
        "mutations": 0,
        "both_reject": 0,
        "all_declared_reject": 0,
        "crashes": 0,
        "uninterpretable_checks": 0,
        "declared_mutation_records": len(row["mutations"]),
        "unbound_mutation_records": 0,
        "accepted_typed_refusals": 0,
        "accepted_non_refusal_outputs": 0,
        "accepted_negative_claims": 0,
        "accepted_classifier_decisions": 0,
        "mutation_joint_detections": 0,
        "mutation_both_accept": 0,
        "mutation_checker_disagreements": 0,
        "mutation_execution_errors": 0,
        "malformed_mutation_records": 0,
        "mutation_incomparable_records": 0,
        "source_gate_mutant_detections": 0,
    }
    status_families = {}
    for ref in row["cases"]:
        data = _case(package, ref)
        case = declared_input(row, data)
        record = {
            "input": ref,
            "case": _jsonable(case),
            "input_contract": row.get("input_contract", "DIRECT"),
        }
        counts["cases"] += 1
        try:
            if row["id"] == "C060":
                answer = solver(case["case"], case["cert"])
            else:
                answer = solver(case)
                if type(answer) is tuple and answer and type(answer[0]) is dict:
                    answer = answer[0]
            check_results = [function(case, answer) for function in checkers]
            flags = [checker_accepts(value) for value in check_results]
            abstains = type(answer) is dict and answer.get("status") == "UNKNOWN"
            status = (
                answer.get("status", answer.get("verdict", "UNLABELED"))
                if type(answer) is dict
                else "NON_OBJECT"
            )
            status_families[str(status)] = status_families.get(str(status), 0) + 1
            accepted = all(flag is True for flag in flags) and not abstains
            classification = candidate_class(answer)
            refusal = classification == "TYPED_REFUSAL"
            negative_claim = classification == "NEGATIVE_CLAIM"
            classifier = classification == "CLASSIFIER_DECISION"
            counts["accepted_typed_refusals"] += accepted and refusal
            counts["accepted_negative_claims"] += accepted and negative_claim
            counts["accepted_non_refusal_outputs"] += (
                accepted and not refusal and not negative_claim and not classifier
            )
            counts["accepted_classifier_decisions"] += accepted and classifier
            counts["abstentions"] += abstains
            counts["both_accept"] += len(flags) >= 2 and accepted
            counts["all_declared_accept"] += accepted
            counts["uninterpretable_checks"] += any(flag is None for flag in flags)
            record.update(
                {
                    "answer": _jsonable(answer),
                    "checks": _jsonable(check_results),
                    "accepted": all(flag is True for flag in flags) and not abstains,
                    "coverage_class": "ACCEPTED_TYPED_REFUSAL"
                    if accepted and refusal
                    else "SOURCE_CHECKED_NEGATIVE_CLAIM"
                    if accepted and negative_claim
                    else "SOURCE_CLASSIFIER_DECISION"
                    if accepted and classifier
                    else "SOURCE_CHECKED_CANDIDATE"
                    if accepted
                    else "REFERENCE_RESIDUAL",
                }
            )
        except Exception as exc:
            counts["crashes"] += 1
            record["error"] = {"type": type(exc).__name__, "detail": str(exc)}
        stream.write(canonical(record) + b"\n")
        stream.flush()
    for ref in row["mutations"]:
        try:
            data = _case(package, ref)
        except (ReplayError, ValueError) as exc:
            counts["malformed_mutation_records"] += 1
            stream.write(
                canonical(
                    {
                        "mutation": ref,
                        "status": "MALFORMED_SOURCE_BYTES_REFUSED",
                        "detail": str(exc),
                        "checker_calls": 0,
                    }
                )
                + b"\n"
            )
            stream.flush()
            continue
        if type(data) is not dict or not any(key in data for key in MUTATION_ANSWER_KEYS):
            counts["unbound_mutation_records"] += 1
            stream.write(
                canonical(
                    {
                        "mutation": ref,
                        "status": "UNBOUND_MUTATION_RECORD",
                        "record": _jsonable(data),
                    }
                )
                + b"\n"
            )
            continue
        case = data.get("case", data.get("input_case"))
        if case is None:
            counts["unbound_mutation_records"] += 1
            stream.write(
                canonical(
                    {"mutation": ref, "status": "UNBOUND_MUTATION_CASE", "record": _jsonable(data)}
                )
                + b"\n"
            )
            continue
        case = declared_input(row, case)
        answer = next(data[key] for key in MUTATION_ANSWER_KEYS if key in data)
        counts["mutations"] += 1
        record = {"mutation": ref, "case": _jsonable(case), "answer": _jsonable(answer)}
        try:
            check_results = [function(case, answer) for function in checkers]
            flags = [checker_accepts(value) for value in check_results]
            counts["both_reject"] += len(flags) >= 2 and all(flag is False for flag in flags)
            counts["all_declared_reject"] += all(flag is False for flag in flags)
            counts["mutation_joint_detections"] += any(flag is False for flag in flags)
            counts["mutation_both_accept"] += all(flag is True for flag in flags)
            counts["mutation_checker_disagreements"] += True in flags and False in flags
            counts["mutation_incomparable_records"] += any(flag is None for flag in flags)
            counts["uninterpretable_checks"] += any(flag is None for flag in flags)
            record.update(
                {
                    "checks": _jsonable(check_results),
                    "both_reject": all(flag is False for flag in flags),
                }
            )
        except Exception as exc:
            counts["crashes"] += 1
            counts["mutation_execution_errors"] += 1
            record["error"] = {"type": type(exc).__name__, "detail": str(exc)}
        stream.write(canonical(record) + b"\n")
        stream.flush()
    synthesis_scope = None
    if row["id"] == "C060":
        import importlib

        generator = importlib.import_module(prefix + ".judge_packet.generate_mutations")
        mutants = generator.get_mutants()
        counts["declared_mutation_records"] = len(mutants)
        retained_cases = [(_case(package, ref), ref) for ref in row["cases"]]
        for name, function in sorted(mutants.items()):
            counts["mutations"] += 1
            killed = False
            all_comparable_accepted = True
            incomparable = False
            for case, ref in retained_cases:
                record = {"checker_mutant": name, "input": ref}
                try:
                    answer = function(case["case"], case["cert"])
                    checks = [checker(case, answer) for checker in checkers]
                    flags = [checker_accepts(check) for check in checks]
                    killed = any(flag is False for flag in flags)
                    dual_rejection = all(flag is False for flag in flags)
                    disagreement = True in flags and False in flags
                    all_comparable_accepted &= all(flag is True for flag in flags)
                    incomparable |= any(flag is None for flag in flags)
                    counts["uninterpretable_checks"] += any(flag is None for flag in flags)
                    record.update(
                        {
                            "answer": _jsonable(answer),
                            "checks": _jsonable(checks),
                            "mutant_killed": killed,
                            "dual_rejection": dual_rejection,
                            "checker_disagreement": disagreement,
                        }
                    )
                except Exception as exc:
                    killed = True
                    dual_rejection = False
                    disagreement = False
                    counts["mutation_execution_errors"] += 1
                    record.update(
                        {
                            "mutant_killed": True,
                            "kill_by_exception": {"type": type(exc).__name__, "detail": str(exc)},
                        }
                    )
                stream.write(canonical(record) + b"\n")
                stream.flush()
                if killed:
                    counts["both_reject"] += dual_rejection
                    counts["all_declared_reject"] += dual_rejection
                    counts["mutation_joint_detections"] += dual_rejection or disagreement
                    counts["mutation_checker_disagreements"] += disagreement
                    break
            counts["source_gate_mutant_detections"] += killed
            counts["mutation_incomparable_records"] += incomparable
            if not killed and all_comparable_accepted:
                counts["mutation_both_accept"] += 1
        synthesis_scope = (
            "RETAINED_CLASSIFIER_AND_MUTANT_DETECTION; NO_CHECKER_SYNTHESIS_OR_MODEL_STUDY"
        )
    completed = (
        counts["cases"] == len(row["cases"])
        and not counts["crashes"]
        and not counts["uninterpretable_checks"]
    )
    mutation_complete = (
        not counts["unbound_mutation_records"]
        and not counts["malformed_mutation_records"]
        and counts["mutations"] == counts["declared_mutation_records"]
    )
    return {
        "status": "REFERENCE_SELF_CONSISTENT"
        if completed
        and counts["all_declared_accept"] == counts["cases"]
        and counts["mutations"]
        and counts["all_declared_reject"] == counts["mutations"]
        and mutation_complete
        else "REFERENCE_RESIDUAL",
        "counts": counts,
        "complete_case_execution": completed,
        "complete_mutation_execution": mutation_complete,
        "grade": "SOURCE_RECREATION_PYTHON",
        "model_accuracy": None,
        "pre_run_commitment": False,
        "algorithm_independence": "NOT_ESTABLISHED_BY_AGREEMENT",
        "declared_checker_count": len(checkers),
        "checker_contract": row.get("checker_contract", "RETAINED_CHECKER_FUNCTIONS"),
        "synthesis_scope": synthesis_scope,
        "status_families": status_families,
        "positive_computation_scope": "Typed refusals and accepted negative labels do not establish intended positive capability; inspect the retained witnesses and checkers.",
    }


def mechanism_recreation(cid: str, engine: Path, capability: dict) -> dict:
    """Join the separately owned finite mechanisms without claiming empirical gates."""
    module = local_module("paper011_mechanisms", "mechanism_recreations.py")
    binding_path = (
        Path(__file__).resolve().parents[1] / "docs/mechanism_recreated_run/source_bindings.json"
    )
    binding_raw = binding_path.read_bytes()
    binding = module.load(binding_raw)
    module.verify_sources(engine, binding)
    host = capability["binaries"]["symbol_game"]
    graph = capability["binaries"]["graph_functional"]
    native = module.Native(Path(host["path"]), host["sha256"])
    phi = module.Native(Path(graph["path"]), graph["sha256"], True)
    functions = {
        "C001": lambda: module.c001(),
        "C002": lambda: module.c002(),
        "C003": lambda: module.c003(),
        "C004": lambda: module.c004(native),
        "C005": lambda: module.c005(engine, binding, phi),
        "C006": lambda: module.c006(native, phi),
        "C007": lambda: module.c007(),
        "C008": lambda: module.c008(),
        "C009": lambda: module.c009(),
        "C010": lambda: module.c010(phi),
        "demo_symbol_tui": lambda: module.symbol_tui(),
    }
    result = functions[cid]()
    result["source_bindings_sha256"] = digest(binding_raw)
    result["mechanism_code_sha256"] = digest(Path(module.__file__).read_bytes())
    module.verify_sources(engine, binding)
    return {
        "status": "FINITE_MECHANISM_REPLAY",
        "result": result,
        "empirical_result": False,
        "challenge_gate_satisfied": False,
        "grade": result.get("grade"),
        "model_accuracy": None,
    }


def demo_execution_status(current: dict, audits: list[dict]) -> str:
    """Execution is not success: preserve canonical refusals and positive gaps."""
    if current.get("status") == "REPRODUCTION_GAP":
        return "DEMO_RECREATION_RESIDUAL"
    if current.get("dispatch_return", 0) != 0:
        return "CURRENT_ENGINE_REFUSAL"
    payloads = list(current.get("actual_engine_payloads", {}).values())
    if "receipt" in current:
        payloads.append(current["receipt"])
    for payload in payloads:
        result = payload.get("result", payload) if type(payload) is dict else {}
        if result.get("code") in {"NO_NATIVE_PORT", "UNSUPPORTED_NATIVE_PORT"} or result.get(
            "status"
        ) in {"REFUSED", "TYPED_REFUSAL"}:
            return "CURRENT_ENGINE_REFUSAL"
        if result.get("verdict") == "INCOMPLETE" or result.get("status") == "UNKNOWN":
            return "DEMO_RECREATION_RESIDUAL"
    if any(audit.get("status") != "AUDIT_EXECUTED" for audit in audits):
        return "DEMO_RECREATION_RESIDUAL"
    return "DEMO_EXECUTION_RECORDED"


def worker(job: dict) -> int:
    source, output = Path(job["source_root"]), Path(job["output_dir"])
    cache_prefix = Path(job["pycache_prefix"])
    regular(cache_prefix, True)
    if (
        any(cache_prefix.iterdir())
        or sys.pycache_prefix != str(cache_prefix)
        or not sys.dont_write_bytecode
    ):
        raise ReplayError("FRESH_BYTECODE_CACHE_CONFIGURATION_REQUIRED")
    (output / "execution_configuration.json").write_bytes(
        canonical(
            {
                "pycache_prefix": str(cache_prefix),
                "initial_cache_entries": [],
                "dont_write_bytecode": sys.dont_write_bytecode,
                "runtime_environment": job["capability"].get("runtime_environment"),
            }
        )
    )
    verify_runtime_environment(job["capability"], full_runtime=False)
    journal = []
    configure_worker(source, job["capability"], journal, output)
    stdout, stderr = io.StringIO(), io.StringIO()
    result = {}
    try:
        actual_runner = digest(Path(__file__).read_bytes())
        if actual_runner != job["runner_sha256"]:
            raise ReplayError("RUNNER_CHANGED_BEFORE_WORKER_LOAD")
        for path, expected in job["control_files"].items():
            if digest(Path(path).read_bytes()) != expected:
                raise ReplayError("RECREATION_CONTROL_BYTES_CHANGED")
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            trace_native_calls(output)
            if job["kind"] == "demo":
                try:
                    current = native_demo(job["row"], source, output / "engine_run")
                except Exception as exc:
                    current = {
                        "status": "REPRODUCTION_GAP",
                        "exception": type(exc).__name__,
                        "detail": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                audits = dossier_recreations(
                    job["row"]["id"], source, Path(job["capability"]["engine_root"]), output
                )
                result = {
                    "status": demo_execution_status(current, audits),
                    "current_engine": _jsonable(current),
                    "preserved_dossier_audits": audits,
                    "model_accuracy": None,
                }
            else:
                if job["row"]["id"] in {f"C{i:03d}" for i in range(1, 11)}:
                    result = mechanism_recreation(
                        job["row"]["id"], Path(job["capability"]["engine_root"]), job["capability"]
                    )
                else:
                    with (output / "evaluations.jsonl").open("wb") as stream:
                        result = (
                            supplemental_c041(job["row"], source, stream, job["proposals"])
                            if job.get("proposals") is not None
                            else reference_challenge(job["row"], source, stream)
                        )
    except BaseException as exc:
        result = {
            "status": "REPRODUCTION_GAP",
            "exception": type(exc).__name__,
            "detail": str(exc),
            "obligation": "Repair the explicit execution contract or missing capability and rerun these exact source inputs.",
        }
    (output / "stdout.txt").write_text(stdout.getvalue(), encoding="utf-8", newline="\n")
    (output / "stderr.txt").write_text(stderr.getvalue(), encoding="utf-8", newline="\n")
    (output / "worker_result.json").write_bytes(canonical(result))
    (output / "import_adaptations.json").write_bytes(canonical(journal))
    for path, expected in job["control_files"].items():
        if digest(Path(path).read_bytes()) != expected:
            raise ReplayError("RECREATION_CONTROL_BYTES_CHANGED_DURING_WORKER")
    return (
        0
        if result.get("status")
        not in {
            "REPRODUCTION_GAP",
            "UNRESOLVED_EXECUTION_CONTRACT",
            "UNRESOLVED_SPECIFICATION",
            "DEMO_RECREATION_RESIDUAL",
            "CURRENT_ENGINE_REFUSAL",
            "REFERENCE_RESIDUAL",
            "SUPPLEMENTAL_PROPOSAL_RESIDUAL",
        }
        else 2
    )


def run_one(
    source: Path,
    capability: dict,
    row: dict,
    kind: str,
    output: Path,
    timeout: int,
    *,
    batch_snapshot: dict | None = None,
    proposals: Path | None = None,
) -> dict:
    if output.exists():
        raise ReplayError("OUTPUT_DIRECTORY_OCCUPIED")
    engine = (
        verify_engine(capability) if batch_snapshot is None else Path(capability["engine_root"])
    )
    before = source_files(source) if batch_snapshot is None else batch_snapshot
    script = Path(__file__).resolve()
    control_files = {
        str(path): digest(path.read_bytes())
        for path in (
            script,
            script.with_name("demo_catalog.py"),
            script.with_name("mechanism_recreations.py"),
            script.parents[1] / "docs/mechanism_recreated_run/source_bindings.json",
        )
    }
    if proposals is not None:
        if row["id"] != "C041":
            raise ReplayError("SUPPLEMENTAL_SCOPE_MISMATCH")
        regular(proposals)
        control_files[str(proposals.resolve())] = digest(proposals.read_bytes())
    output.mkdir(parents=True, exist_ok=False)
    cache_prefix = output.resolve() / "empty_bytecode_cache"
    cache_prefix.mkdir(exist_ok=False)
    job = {
        "source_root": str(source.resolve()),
        "output_dir": str(output.resolve()),
        "capability": capability,
        "row": row,
        "kind": kind,
        "runner_sha256": control_files[str(script)],
        "control_files": control_files,
        "pycache_prefix": str(cache_prefix),
        "proposals": {
            "path": str(proposals.resolve()),
            "sha256": control_files[str(proposals.resolve())],
        }
        if proposals is not None
        else None,
    }
    job_path = output / "job.json"
    job_path.write_bytes(canonical(job))
    bootstrap = "import importlib.util,json,sys;sys.pycache_prefix=sys.argv[3];sys.dont_write_bytecode=True;p=sys.argv[1];s=importlib.util.spec_from_file_location('paper011_replay',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);sys.exit(m.worker(m.load(open(sys.argv[2],'rb').read())))"
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in {
            "PYTHONPATH",
            "PYTHONSTARTUP",
            "CORE_FUNCTIONAL_GRAPH_BIN",
            "CORE_FUNCTIONAL_GRAPH_SHA256",
            "CORE_SYMBOL_GAME_HOST",
        }
        and not any(secret in k.upper() for secret in ("API_KEY", "TOKEN", "SECRET", "PASSWORD"))
    }
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0", "PYTHONUTF8": "1"})
    try:
        process = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                bootstrap,
                str(script),
                str(job_path.resolve()),
                str(cache_prefix),
            ],
            cwd=engine,
            env=env,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        code = process.returncode
        (output / "process_stdout.txt").write_bytes(process.stdout)
        (output / "process_stderr.txt").write_bytes(process.stderr)
        result_path = output / "worker_result.json"
        result = (
            load(result_path.read_bytes())
            if result_path.is_file()
            else {"status": "WORKER_FAILURE"}
        )
    except subprocess.TimeoutExpired as exc:
        code = None
        (output / "process_stdout.txt").write_bytes(exc.stdout or b"")
        (output / "process_stderr.txt").write_bytes(exc.stderr or b"")
        result = {
            "status": "BUDGET_EXHAUSTED",
            "obligation": "Complete the remaining exact source cases within a newly declared execution budget; timeout is not rejection or completeness.",
        }
    if batch_snapshot is None:
        verify_engine(capability)
        if source_files(source) != before:
            raise ReplayError("SOURCE_MUTATED_DURING_REPLAY")
    for path, expected in control_files.items():
        if digest(Path(path).read_bytes()) != expected:
            raise ReplayError("RECREATION_CONTROL_BYTES_CHANGED_DURING_REPLAY")
    artifacts = source_files(output)
    receipt = {
        "schema_version": SCHEMA,
        "authority_effect": "None",
        "id": row["id"],
        "kind": kind,
        "source_inventory_sha256": digest(canonical(before)),
        "capability_sha256": digest(canonical(capability)),
        "runner_sha256": control_files[str(script)],
        "control_files": control_files,
        "catalog_row_sha256": digest(canonical(row)),
        "budget_seconds": timeout,
        "custody_recheck": "SINGLE_RUN_AFTER_SUBPROCESS"
        if batch_snapshot is None
        else "BATCH_FINAL_RECHECK_REQUIRED",
        "process_exit": code,
        "result": result,
        "artifacts_sha256": artifacts,
        "model_calls": 0,
        "model_accuracy": None,
        "optimality": None,
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    (output / "recreation_receipt.json").write_bytes(canonical(receipt))
    return receipt


def run_batch(
    source: Path,
    capability: dict,
    output: Path,
    timeout: int,
    ids: list[str] | None = None,
    proposals: Path | None = None,
) -> dict:
    if output.exists():
        raise ReplayError("OUTPUT_DIRECTORY_OCCUPIED")
    verify_engine(capability)
    before = source_files(source)
    catalog = build_catalog(source)
    rows = [("demo", row) for row in catalog["demos"]] + [
        ("challenge", row) for row in catalog["challenges"]
    ]
    if ids:
        if set(ids) - {row["id"] for _, row in rows}:
            raise ReplayError("UNKNOWN_RECREATION_ID")
        rows = [(kind, row) for kind, row in rows if row["id"] in ids]
    if proposals is not None and (ids is None or "C041" not in ids):
        raise ReplayError("SUPPLEMENTAL_SCOPE_MISMATCH")
    output.mkdir(parents=True, exist_ok=False)
    runs = []
    for kind, row in rows:
        receipt = run_one(
            source,
            capability,
            row,
            kind,
            output / row["id"],
            timeout,
            batch_snapshot=before,
            proposals=proposals if row["id"] == "C041" else None,
        )
        runs.append(
            {
                "id": row["id"],
                "receipt_sha256": receipt["receipt_sha256"],
                "result_status": receipt["result"].get("status"),
                "process_exit": receipt["process_exit"],
            }
        )
        print(json.dumps(runs[-1]), flush=True)
    verify_engine(capability)
    if source_files(source) != before:
        raise ReplayError("SOURCE_MUTATED_DURING_REPLAY")
    report = {
        "schema_version": "paper011.recreation-batch.v1",
        "authority_effect": "None",
        "source_inventory_sha256": digest(canonical(before)),
        "capability_sha256": digest(canonical(capability)),
        "catalog_sha256": digest(canonical(catalog)),
        "runs": runs,
        "custody_recheck": "ENTIRE_DECLARED_SOURCE_AND_ENGINE_REHASHED_AFTER_ALL_SUBPROCESSES",
        "requested_ids_complete": len(runs) == len(rows),
        "full_catalog_requested": ids is None,
        "all_demonstrations_completed": False,
        "note": "Execution census is not positive capability completion; inspect each actual result, mutation outcome and unresolved obligation.",
    }
    report["receipt_sha256"] = digest(canonical(report))
    (output / "batch_receipt.json").write_bytes(canonical(report))
    return report


def verify_receipt(output: Path) -> dict:
    raw = (output / "recreation_receipt.json").read_bytes()
    receipt = load(raw)
    if (
        type(receipt) is not dict
        or receipt.get("schema_version") != SCHEMA
        or raw != canonical(receipt)
    ):
        raise ReplayError("RECEIPT_SCHEMA_MISMATCH")
    body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    if digest(canonical(body)) != receipt["receipt_sha256"]:
        raise ReplayError("RECEIPT_DIGEST_MISMATCH")
    actual = source_files(output)
    del actual["recreation_receipt.json"]
    if actual != receipt["artifacts_sha256"]:
        raise ReplayError("RECREATION_ARTIFACT_CUSTODY_MISMATCH")
    return {
        "status": "INTEGRITY_VERIFIED",
        "id": receipt["id"],
        "evidence_scope": "Artifact custody; computational replay requires the declared capability and rerun.",
        "authority_effect": "None",
    }


def coverage_matrix(primary: Path, supplements: list[Path], output: Path) -> dict:
    """Derive outcomes from closed, byte-verified executions; never rewrite them."""
    selections = {}
    supplemental_checks = []
    closures = []
    inventory = None
    for index, folder in enumerate([primary, *supplements]):
        path = folder / "batch_receipt.json"
        raw = path.read_bytes()
        batch = load(raw)
        body = {key: value for key, value in batch.items() if key != "receipt_sha256"}
        if (
            digest(canonical(body)) != batch["receipt_sha256"]
            or batch.get("custody_recheck")
            != "ENTIRE_DECLARED_SOURCE_AND_ENGINE_REHASHED_AFTER_ALL_SUBPROCESSES"
        ):
            raise ReplayError("BATCH_CLOSURE_MISMATCH")
        if index == 0:
            if not batch.get("full_catalog_requested") or len(batch["runs"]) != 87:
                raise ReplayError("PRIMARY_CATALOG_INCOMPLETE")
            inventory = batch["source_inventory_sha256"]
        if batch["source_inventory_sha256"] != inventory:
            raise ReplayError("COVERAGE_SOURCE_IDENTITY_MISMATCH")
        closures.append(
            {
                "path": str(path.resolve()),
                "sha256": digest(raw),
                "receipt_sha256": batch["receipt_sha256"],
            }
        )
        for run in batch["runs"]:
            if index and run["id"] not in selections:
                raise ReplayError("SUPPLEMENT_ADDS_UNDECLARED_OBLIGATION")
            directory = folder / run["id"]
            verify_receipt(directory)
            receipt_raw = (directory / "recreation_receipt.json").read_bytes()
            receipt = load(receipt_raw)
            if receipt["receipt_sha256"] != run["receipt_sha256"]:
                raise ReplayError("BATCH_RUN_IDENTITY_MISMATCH")
            result = receipt["result"]
            if result.get("execution_scope") == "SUPPLEMENTAL_SELECTED_CANDIDATES":
                if run["id"] != "C041":
                    raise ReplayError("SUPPLEMENTAL_SCOPE_MISMATCH")
                supplemental_checks.append(
                    {
                        "id": run["id"],
                        "receipt_path": str((directory / "recreation_receipt.json").resolve()),
                        "receipt_bytes_sha256": digest(receipt_raw),
                        "result": result,
                        "evaluations_path": str((directory / "evaluations.jsonl").resolve()),
                        "evaluations_sha256": receipt["artifacts_sha256"].get("evaluations.jsonl"),
                        "native_transport_path": str(
                            (directory / "native_transport_calls.jsonl").resolve()
                        ),
                        "native_transport_sha256": receipt["artifacts_sha256"].get(
                            "native_transport_calls.jsonl"
                        ),
                    }
                )
                continue
            current = result.get("current_engine", {})
            audits = result.get("preserved_dossier_audits", [])
            effective_status = (
                demo_execution_status(current, audits)
                if receipt["kind"] == "demo" and "current_engine" in result
                else result.get("status")
            )
            mutation = {
                "dual_rejections": 0,
                "joint_detections": 0,
                "both_accept": 0,
                "disagreements": 0,
                "execution_errors": 0,
                "incomparable": 0,
                "malformed_bytes_refused": 0,
                "unbound_records": 0,
            }
            unresolved_cases = []
            candidate_kinds = {}
            stream = directory / "evaluations.jsonl"
            if stream.is_file():
                for line in stream.read_bytes().splitlines():
                    event = load(line)
                    if "mutation" in event or "checker_mutant" in event:
                        if "kill_by_exception" in event or "error" in event:
                            mutation["execution_errors"] += 1
                        elif event.get("status") == "MALFORMED_SOURCE_BYTES_REFUSED":
                            mutation["malformed_bytes_refused"] += 1
                        elif str(event.get("status", "")).startswith("UNBOUND_MUTATION"):
                            mutation["unbound_records"] += 1
                        elif "checks" in event:
                            flags = [checker_accepts(check) for check in event["checks"]]
                            mutation["dual_rejections"] += len(flags) >= 2 and all(
                                flag is False for flag in flags
                            )
                            mutation["joint_detections"] += any(flag is False for flag in flags)
                            mutation["disagreements"] += True in flags and False in flags
                            mutation["incomparable"] += any(flag is None for flag in flags)
                            # C060 records passing trials before a mutant's first detection.
                            mutation["both_accept"] += "checker_mutant" not in event and all(
                                flag is True for flag in flags
                            )
                    elif "input" in event:
                        classification = candidate_class(event.get("answer"))
                        candidate_kinds[classification] = candidate_kinds.get(classification, 0) + 1
                        if not event.get("accepted"):
                            unresolved_cases.append(
                                {
                                    "input": event["input"],
                                    "class": classification,
                                    "error": event.get("error"),
                                    "status": event.get("answer", {}).get("status"),
                                }
                            )
            native = []
            tape = directory / "native_transport_calls.jsonl"
            if tape.is_file():
                for line in tape.read_bytes().splitlines():
                    event = load(line)
                    try:
                        if event.get("binary_key") == "lean":
                            response = {
                                "status": "LEAN_PROCESS_COMPLETE"
                                if event["process_exit"] == 0
                                else "LEAN_PROCESS_REFUSAL"
                            }
                        else:
                            response = load(bytes.fromhex(event["stdout_bytes_hex"]))
                        status = (
                            response.get("status", response.get("success"))
                            if type(response) is dict
                            else None
                        )
                    except (ValueError, ReplayError):
                        status = "MALFORMED_NATIVE_RESPONSE"
                    native.append(
                        {
                            "binary_sha256": event["binary_sha256"],
                            "process_exit": event["process_exit"],
                            "response_status": status,
                            "stdio_capture": event.get(
                                "stdio_capture", "LEGACY_REPRESENTATION_NOT_ASSERTED_PHYSICAL_RAW"
                            ),
                        }
                    )
            obligations = []
            if result.get("obligation"):
                obligations.append(result["obligation"])
            for audit in audits:
                if audit.get("obligation"):
                    obligations.append(
                        audit["checker_path"]
                        + ": "
                        + audit["obligation"]
                        + " "
                        + audit.get("detail", "")
                    )
            for payload in current.get("actual_engine_payloads", {}).values():
                if type(payload) is dict:
                    detail = payload.get("result", payload)
                    if type(detail) is dict and detail.get("code") == "NO_NATIVE_PORT":
                        obligations.append(
                            detail.get("detail", "Bind the declared positive native port.")
                        )
            selections[run["id"]] = {
                "id": run["id"],
                "kind": receipt["kind"],
                "recorded_status": result.get("status"),
                "audited_execution_status": effective_status,
                "process_exit": receipt["process_exit"],
                "receipt_path": str((directory / "recreation_receipt.json").resolve()),
                "receipt_bytes_sha256": digest(receipt_raw),
                "runner_sha256": receipt["runner_sha256"],
                "capability_sha256": receipt["capability_sha256"],
                "counts": result.get("counts"),
                "candidate_kinds": candidate_kinds,
                "mutation_outcomes": mutation,
                "unresolved_case_inputs": unresolved_cases,
                "native_transport_outcomes": native,
                "dossier_audits": audits,
                "unperformed_obligations": obligations,
                "mechanism_empirical_gate": result.get("challenge_gate_satisfied"),
                "model_calls": 0,
                "model_accuracy": None,
            }
    matrix = {
        "schema_version": "paper011.recreation-coverage.v1",
        "authority_effect": "None",
        "source_inventory_sha256": inventory,
        "batch_closures": closures,
        "report_generator_sha256": digest(Path(__file__).read_bytes()),
        "rows": [selections[key] for key in sorted(selections)],
        "supplemental_candidate_checks": supplemental_checks,
        "declared_entries": 87,
        "all_recreations_completed": False,
        "scope": "Execution and checker outcomes only. Accepted refusals, classifier decisions, historical self-scores and an integrity pass do not establish an intended positive demonstration or an empirical model gate.",
    }
    matrix["receipt_sha256"] = digest(canonical(matrix))
    output.write_bytes(canonical(matrix))
    return matrix


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    catalog = commands.add_parser("catalog")
    catalog.add_argument("--source-root", type=Path, required=True)
    catalog.add_argument("--output", type=Path, required=True)
    lock = commands.add_parser("lock-engine")
    lock.add_argument("--engine-root", type=Path, required=True)
    lock.add_argument("--source-head", required=True)
    lock.add_argument("--native-host", type=Path, required=True)
    lock.add_argument("--functional-host", type=Path)
    lock.add_argument("--verifier-bin", action="append", default=[], metavar="NAME=PATH")
    lock.add_argument("--build-receipt", type=Path)
    lock.add_argument("--output", type=Path, required=True)
    run = commands.add_parser("run")
    run.add_argument("--source-root", type=Path, required=True)
    run.add_argument("--capability", type=Path, required=True)
    run.add_argument("--id", required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--timeout", type=int, default=60)
    run.add_argument("--proposals", type=Path)
    batch = commands.add_parser("run-batch")
    batch.add_argument("--source-root", type=Path, required=True)
    batch.add_argument("--capability", type=Path, required=True)
    batch.add_argument("--output-dir", type=Path, required=True)
    batch.add_argument("--timeout", type=int, default=60)
    batch.add_argument("--ids", nargs="+")
    batch.add_argument("--proposals", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("--run-dir", type=Path, required=True)
    coverage = commands.add_parser("coverage")
    coverage.add_argument("--primary-batch", type=Path, required=True)
    coverage.add_argument("--supplemental-batch", type=Path, action="append", default=[])
    coverage.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "catalog":
            result = build_catalog(args.source_root)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(canonical(result))
            print(
                json.dumps({"demos": len(result["demos"]), "challenges": len(result["challenges"])})
            )
            return 0
        if args.command == "lock-engine":
            verifiers = {}
            for value in args.verifier_bin:
                name, path = value.split("=", 1)
                if name in verifiers:
                    raise ReplayError("DUPLICATE_NATIVE_VERIFIER")
                verifiers[name] = Path(path)
            result = engine_lock(
                args.engine_root,
                args.source_head,
                args.native_host,
                args.functional_host,
                verifiers,
                args.build_receipt,
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(canonical(result))
            print(json.dumps({"capability_sha256": digest(canonical(result))}))
            return 0
        if args.command == "verify":
            print(json.dumps(verify_receipt(args.run_dir)))
            return 0
        if args.command == "coverage":
            result = coverage_matrix(args.primary_batch, args.supplemental_batch, args.output)
            print(
                json.dumps(
                    {"entries": len(result["rows"]), "receipt_sha256": result["receipt_sha256"]}
                )
            )
            return 0
        if not 1 <= args.timeout <= 1800:
            raise ReplayError("INVALID_EXECUTION_BUDGET")
        if args.command == "run-batch":
            result = run_batch(
                args.source_root,
                load(args.capability.read_bytes()),
                args.output_dir,
                args.timeout,
                args.ids,
                args.proposals,
            )
            return 0 if all(row["process_exit"] == 0 for row in result["runs"]) else 2
        catalog_data = build_catalog(args.source_root)
        rows = [("demo", r) for r in catalog_data["demos"]] + [
            ("challenge", r) for r in catalog_data["challenges"]
        ]
        match = next(((kind, row) for kind, row in rows if row["id"] == args.id), None)
        if match is None:
            raise ReplayError("UNKNOWN_RECREATION_ID")
        result = run_one(
            args.source_root,
            load(args.capability.read_bytes()),
            match[1],
            match[0],
            args.output_dir,
            args.timeout,
            proposals=args.proposals,
        )
        print(
            json.dumps(
                {
                    "id": args.id,
                    "result": result["result"],
                    "receipt_sha256": result["receipt_sha256"],
                }
            )
        )
        return 0 if result["process_exit"] == 0 else 2
    except (ReplayError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "REFUSED", "detail": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
