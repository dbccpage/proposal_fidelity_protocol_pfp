"""
Custody checks for the two vendored modules, native_functional.py and
l1_symbol_game_governor.py.

Each vendored file starts with a header naming its source path, commit, and the
SHA-256 of the source bytes. The header check always runs. The comparison check
needs a checkout of the source repository with Git and the named commits: it
reads each source blob with `git cat-file -p`, confirms the recorded SHA-256, and
confirms that the vendored module differs from the source only by the changes
its header lists. The documented behavioural patches (the governor's
step_cut completeness check for review finding R008-04, compute_phi1
no longer replacing native errors with a Python answer, and the declared
ASSERT/CUT/VERIFY boundary patches from the v0.1 publication review) are excluded from that
comparison and checked for separately. Outside such a checkout the comparison
skips and says why.
"""

import ast
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
FIELD = re.compile(
    r"^# (vendored-from-path|vendored-from-commit|vendored-from-sha256"
    r"|baseline-commit|baseline-sha256): (\S+)$",
    re.M,
)
ADAPTER_PATH = "providers.adapters.native_functional"
BOOTSTRAP_NAMES = {"_find_repo_root", "_REPO_ROOT"}
VENDORED = {
    "native_functional.py": {
        "removed_imports": set(),
        "removed_names": set(),
        "renamed_modules": {},
        "patched_methods": set(),
        "patched_functions": set(),
    },
    "l1_symbol_game_governor.py": {
        "removed_imports": {("import", "sys", None), ("from", "pathlib", "Path", None)},
        "removed_names": BOOTSTRAP_NAMES,
        "renamed_modules": {ADAPTER_PATH: "native_functional"},
        "patched_methods": {
            ("L1SymbolGameGovernor", "step_assert"),
            ("L1SymbolGameGovernor", "step_cut"),
            ("L1SymbolGameGovernor", "step_verify"),
        },
        "patched_functions": {"compute_phi1"},
    },
}


def _header(name: str) -> dict:
    return dict(FIELD.findall((CODE / name).read_text(encoding="utf-8")))


def _mentions(node: ast.AST, names: set) -> bool:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
        return True
    return any(isinstance(sub, ast.Name) and sub.id in names for sub in ast.walk(node))


def _normalized(source: str, spec: dict, original: bool, skip_patched: bool = True):
    """Return (top-level imports, labelled dumps of other top-level statements)."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in spec["renamed_modules"]:
            node.module = spec["renamed_modules"][node.module]
    imports, body = set(), []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.update(("import", alias.name, alias.asname) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.update(
                ("from", node.module, alias.name, alias.asname) for alias in node.names
            )
        elif original and _mentions(node, spec["removed_names"]):
            continue
        elif (
            skip_patched
            and isinstance(node, ast.FunctionDef)
            and node.name in spec["patched_functions"]
        ):
            continue
        else:
            if isinstance(node, ast.ClassDef):
                skip = {m for cls, m in spec["patched_methods"] if cls == node.name}
                node.body = [
                    stmt for stmt in node.body
                    if not (isinstance(stmt, ast.FunctionDef) and stmt.name in skip)
                ]
            body.append((getattr(node, "name", type(node).__name__), ast.dump(node)))
    if original:
        imports -= spec["removed_imports"]
    return imports, body


def _repository_root():
    for parent in CODE.parents:
        if (parent / ".git").exists():
            return parent
    return None


def _source_blob(commit: str, path: str) -> bytes:
    root = _repository_root()
    if root is None:
        pytest.skip("comparison needs a checkout of the source repository; none contains this package")
    git = shutil.which("git")
    if git is None:
        pytest.skip("comparison needs git on PATH")
    result = subprocess.run(
        [git, "cat-file", "-p", f"{commit}:{path}"],
        cwd=root,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"source blob {commit[:12]}:{path} is not available in this checkout")
    return result.stdout


@pytest.mark.parametrize("name", sorted(VENDORED))
def test_vendored_header_is_complete(name):
    fields = _header(name)
    assert fields["vendored-from-path"].endswith(".py")
    assert re.fullmatch(r"[0-9a-f]{40}", fields["vendored-from-commit"])
    assert re.fullmatch(r"[0-9a-f]{64}", fields["vendored-from-sha256"])
    if name == "l1_symbol_game_governor.py":
        assert fields["baseline-commit"] == "52cb5457f6c485ba548cfd292f6012a941ed22cf"
        assert re.fullmatch(r"[0-9a-f]{64}", fields["baseline-sha256"])
    else:
        assert fields["vendored-from-commit"] == "52cb5457f6c485ba548cfd292f6012a941ed22cf"


@pytest.mark.parametrize("name", sorted(VENDORED))
def test_vendored_copy_matches_recorded_source(name):
    fields, spec = _header(name), VENDORED[name]
    blob = _source_blob(fields["vendored-from-commit"], fields["vendored-from-path"])
    assert hashlib.sha256(blob).hexdigest() == fields["vendored-from-sha256"]
    source = _normalized(blob.decode("utf-8"), spec, original=True)
    vendored = _normalized((CODE / name).read_text(encoding="utf-8"), spec, original=False)
    assert vendored == source


def test_governor_differs_from_baseline_only_in_compute_phi1():
    fields, spec = _header("l1_symbol_game_governor.py"), VENDORED["l1_symbol_game_governor.py"]
    later = _source_blob(fields["vendored-from-commit"], fields["vendored-from-path"])
    baseline = _source_blob(fields["baseline-commit"], fields["vendored-from-path"])
    assert hashlib.sha256(baseline).hexdigest() == fields["baseline-sha256"]
    later_imports, later_body = _normalized(later.decode("utf-8"), spec, original=True, skip_patched=False)
    base_imports, base_body = _normalized(baseline.decode("utf-8"), spec, original=True, skip_patched=False)
    assert later_imports == base_imports
    assert len(later_body) == len(base_body)
    changed = [new[0] for old, new in zip(base_body, later_body) if old != new]
    assert changed == ["compute_phi1"]


def _method(source: str, cls: str, name: str) -> ast.FunctionDef:
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for stmt in node.body:
                if isinstance(stmt, ast.FunctionDef) and stmt.name == name:
                    return stmt
    raise AssertionError(f"{cls}.{name} not found")


def _strings(node: ast.AST) -> set:
    return {n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def test_vendored_step_cut_carries_the_completeness_check():
    """The documented local patch (review finding R008-04) is present."""
    vendored = _method(
        (CODE / "l1_symbol_game_governor.py").read_text(encoding="utf-8"),
        "L1SymbolGameGovernor",
        "step_cut",
    )
    assert "IncompleteProposal" in _strings(vendored)


def test_recorded_source_step_cut_lacks_the_completeness_check():
    """The patch is local: the recorded source commit predates it."""
    fields = _header("l1_symbol_game_governor.py")
    source = _source_blob(fields["vendored-from-commit"], fields["vendored-from-path"])
    original = _method(source.decode("utf-8"), "L1SymbolGameGovernor", "step_cut")
    assert "IncompleteProposal" not in _strings(original)


def test_vendored_compute_phi1_has_no_exception_handler():
    """The documented local patch: native errors are never replaced by a Python answer."""
    tree = ast.parse((CODE / "l1_symbol_game_governor.py").read_text(encoding="utf-8"))
    function = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "compute_phi1"
    )
    assert not [node for node in ast.walk(function) if isinstance(node, ast.ExceptHandler)]
