"""Authenticate each independently versioned research checker before execution.

The release pin authenticates the registry; the registry authenticates each
checker and fixture. This is release integrity, not protection from a writer who
can replace the installed package and its pins together.
"""

from __future__ import annotations

import builtins
import types
from importlib.resources import files

from pfp.domain.demos import DemoRefusal
from pfp.infrastructure.demos.canonical import digest, load

from .checkers.assemble import assemble_checker_source, preamble_bytes
from .pins import PREAMBLE_SHA256, REGISTRY_SHA256

PACKAGE = "pfp.infrastructure.adapters.mssn_research"


def resource(path: str) -> bytes:
    if any(p in ("", ".", "..") for p in path.split("/")) or "\\" in path or ":" in path:
        raise DemoRefusal("INVALID_RESOURCE_PATH", path)
    return files(PACKAGE).joinpath(path).read_bytes()


def registry() -> dict:
    data = resource("registry.json")
    if digest(data) != REGISTRY_SHA256:
        raise DemoRefusal("CHECKER_REGISTRY_DIGEST_MISMATCH")
    result = load(data)
    if [r["level"] for r in result["checkers"]] != list(range(101)):
        raise DemoRefusal("CHECKER_REGISTRY_LEVELS")
    return result


def entry(level: int) -> dict:
    if type(level) is not int or not 0 <= level <= 100:
        raise DemoRefusal("UNKNOWN_LEVEL", str(level))
    record = registry()["checkers"][level]
    if record["path"] != f"checkers/stage_{level:03d}.py":
        raise DemoRefusal("CHECKER_REGISTRY_ENTRY_MISMATCH")
    return record


def fixture(level: int) -> dict:
    record = entry(level)
    data = resource(record["fixture_path"])
    if digest(data) != record["fixture_sha256"]:
        raise DemoRefusal("FIXTURE_DIGEST_MISMATCH")
    result = load(data)
    if result["level"] != level:
        raise DemoRefusal("FIXTURE_LEVEL_MISMATCH")
    return result


def _import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name not in {
        "re",
        "fractions",
        "hashlib",
        "json",
        "itertools",
        "math",
        "collections",
        "functools",
    }:
        raise DemoRefusal("RESEARCH_CHECKER_IMPORT_REFUSED", name)
    return builtins.__import__(name, globals, locals, fromlist, level)


def checker(level: int):
    record = entry(level)
    data = resource(record["path"])
    if digest(data) != record["sha256"]:
        raise DemoRefusal("CHECKER_DIGEST_MISMATCH", str(level))
    preamble = preamble_bytes()
    if digest(preamble) != PREAMBLE_SHA256:
        raise DemoRefusal("CHECKER_PREAMBLE_DIGEST_MISMATCH", str(level))
    namespace = types.ModuleType(f"mssn_stage_{level:03d}")
    allowed = dict(vars(builtins), __import__=_import)
    for name in ("open", "eval", "exec", "compile", "input", "breakpoint"):
        allowed.pop(name, None)
    namespace.__dict__["__builtins__"] = allowed
    source = assemble_checker_source(data)
    exec(compile(source, record["path"], "exec"), namespace.__dict__)
    if namespace.STAGE != level or namespace.ROW_SHA256 != record["row_sha256"]:
        raise DemoRefusal("CHECKER_OBLIGATION_MISMATCH", str(level))
    if [list(c) for c in namespace.CLAUSES] != record["clauses"]:
        raise DemoRefusal("CHECKER_CLAUSE_MISMATCH", str(level))
    return namespace
