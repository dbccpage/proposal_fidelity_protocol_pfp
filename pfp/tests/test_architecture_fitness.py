"""Architectural fitness for the Symbol Game package.

`EPIC-OE-SYMGAM-009` is the epic sprints 021, 023 and 024 each deferred work to.
Three of its five criteria are architectural rules over Python source and are
enforced here. The other two describe a PyO3 extension that does not exist, and
that is pinned below, so the deferral fails loudly rather than rotting.

This gate used to live in `projects/ms_majorana/code/tests/unit/`,
where it could not be collected: a stale shadow copy of this package was on
`sys.path` there. It now lives beside the package it measures.

Some `domain/` modules import `pathlib`, which criterion 4 forbids. They are
recorded by identity in a shrink-only ratchet (`architecture_baseline.json`).
Seam import sites other than `ffi.py` are recorded the same way, each with a
reason, in `SEAM_IMPORT_ALLOWLIST`.
"""

from __future__ import annotations

import ast
import json
import pathlib

import pytest

import pfp
from pfp.infrastructure.architecture_fitness import (
    BASELINE_SCHEMA,
    EXEC_CALLER_ALLOWLIST,
    SEAM_IMPORT_ALLOWLIST,
    FitnessError,
    Offence,
    domain_module_count,
    domain_offences,
    dotenv_importers,
    exec_callers,
    exec_violations,
    format_report,
    imported_names,
    load_baseline,
    ratchet_violations,
    raw_gateway_constructors,
    render_baseline,
    sanctioned_gateway_factory_builds_one,
    seam_importers,
    seam_violations,
    stage_runtime_modules,
)


def _repository_root() -> pathlib.Path:
    """The directory holding the imported package, never a shadow copy.

    Resolving from the imported module rather than from this file is the point:
    the old gate found *a* baseline by walking up, and a copy of the package on
    `sys.path` made it measure something other than the code under test.
    """
    package = pathlib.Path(pfp.__file__).resolve().parent
    here = pathlib.Path(__file__).resolve()
    assert here.is_relative_to(package), (
        f"the gate at {here} measures a different package than the one imported "
        f"from {package}"
    )
    return package.parent


REPO_ROOT = _repository_root()
BASELINE_PATH = (
    REPO_ROOT
    / "pfp"
    / "infrastructure"
    / "architecture_baseline.json"
)


# --------------------------------------------------------------------------
# Criterion 1 -- one import site for the seam
# --------------------------------------------------------------------------


def test_seam_import_sites_are_ffi_plus_the_explicit_allowlist():
    importers = seam_importers(REPO_ROOT)
    assert seam_violations(importers) == (), importers


def test_every_allowlisted_seam_importer_states_a_reason():
    for module, reason in SEAM_IMPORT_ALLOWLIST.items():
        assert module.startswith("pfp/")
        assert "/tests/" not in module
        assert isinstance(reason, str) and len(reason) > 20, module


def test_a_new_seam_importer_fails_the_allowlist():
    grown = seam_importers(REPO_ROOT) + (
        "pfp/use_cases/newcomer.py",
    )
    problems = seam_violations(grown)
    assert any("newcomer.py" in p and "outside the allowlist" in p for p in problems)


def test_a_cleaned_seam_importer_must_leave_the_allowlist():
    allowlist = {"pfp/use_cases/gone.py": "a reason long enough"}
    problems = seam_violations(("pfp/ffi.py",), allowlist)
    assert any("gone.py" in p and "remove its allowlist entry" in p for p in problems)


@pytest.mark.parametrize("module", [
    "pfp/infrastructure/code_change_checker.py",
    "pfp/infrastructure/normal_forms/qm_classical.py",
])
def test_reviewed_native_adapters_remain_exact_shrink_only_entries(module):
    importers = seam_importers(REPO_ROOT)
    assert module in importers and module in SEAM_IMPORT_ALLOWLIST
    unregistered = dict(SEAM_IMPORT_ALLOWLIST)
    unregistered.pop(module)
    assert f"{module}: new seam import site outside the allowlist" in seam_violations(
        importers, unregistered
    )
    removed = tuple(path for path in importers if path != module)
    assert f"{module}: no longer imports the seam; remove its allowlist entry" in seam_violations(
        removed
    )
    sibling = module.removesuffix(".py") + "_unreviewed.py"
    assert f"{sibling}: new seam import site outside the allowlist" in seam_violations(
        (*importers, sibling)
    )


def test_the_seam_module_is_the_one_that_reaches_it():
    # Not merely "one importer" -- the *right* one. A count-only assertion
    # would pass if the seam moved into a random module.
    assert "pfp/ffi.py" in seam_importers(REPO_ROOT)
    problems = seam_violations(("pfp/infrastructure/x.py",), {})
    assert any("no longer reaches the native host" in p for p in problems)


def test_the_seam_delegates_host_location_rather_than_duplicating_it():
    # `RULE_FFI_SEAM_ISOLATION_001`: one module decides where the host lives.
    source = (REPO_ROOT / "pfp" / "ffi.py").read_text(
        encoding="utf-8"
    )
    assert "locate_host_binary" in source
    assert "operating_system" in source


# --------------------------------------------------------------------------
# Criterion 4 -- the domain layer imports nothing native, filesystem or process
# --------------------------------------------------------------------------


def test_the_domain_layer_is_scanned_in_full():
    scanned = domain_module_count(REPO_ROOT)
    assert scanned >= 90, f"only {scanned} domain modules found; the scan is wrong"


def test_the_measured_domain_offences_are_exactly_the_recorded_ones():
    assert (
        ratchet_violations(domain_offences(REPO_ROOT), load_baseline(BASELINE_PATH))
        == ()
    )


def test_every_current_offence_is_the_filesystem():
    # The finding, stated precisely: no domain module reaches for a process or
    # the extension. Every offence is `pathlib`.
    offences = domain_offences(REPO_ROOT)
    assert offences, "the fixture must have offences, or the ratchet is vacuous"
    for offence in offences:
        assert offence.imports == ("pathlib",), (
            f"{offence.module} imports {offence.imports}, not just the filesystem"
        )


def test_no_domain_module_imports_a_process_or_the_extension():
    for offence in domain_offences(REPO_ROOT):
        for name in offence.imports:
            assert name not in {"subprocess", "multiprocessing", "socket"}
            assert "core_symbol_game_runtime" not in name


def test_most_of_the_domain_layer_is_already_clean():
    # Coverage stated as a pair, per sprint 017: 12 of 100 is a very different
    # report from 12 of 13.
    scanned = domain_module_count(REPO_ROOT)
    offending = len(domain_offences(REPO_ROOT))
    assert offending < scanned
    assert offending * 4 < scanned, f"{offending} of {scanned} is not a tail"


# --------------------------------------------------------------------------
# Import analysis is over the AST, not the text
# --------------------------------------------------------------------------


def test_a_doc_comment_naming_a_module_is_not_an_import():
    # A text scan reports two domain modules as native importers; both merely
    # describe in prose what they mirror. This is why the analyzer parses.
    source = '"""Mirrors core_symbol_game_runtime::rational."""\nimport json\n'
    assert imported_names(source) == ("json",)


def test_both_import_forms_are_seen():
    source = "import os\nfrom pathlib import Path\nfrom . import sibling\n"
    names = imported_names(source)
    assert "os" in names
    assert "pathlib" in names


def test_a_relative_import_with_no_module_is_not_a_crash():
    assert imported_names("from . import thing\n") == ()


def test_a_submodule_import_is_attributed_to_its_root(tmp_path):
    """`import os.path` must count as importing `os`.

    The first version of this test performed the split *itself* and asserted
    the result was forbidden — which exercises the test's own arithmetic, not
    the analyzer's. A mutation removing the split from the analyzer survived it.
    This drives the real scan instead.
    """
    domain = tmp_path / "pfp" / "domain"
    domain.mkdir(parents=True)
    (domain / "deep.py").write_text("import os.path\n", encoding="utf-8")
    (offence,) = domain_offences(tmp_path)
    assert offence.module.endswith("deep.py")
    assert offence.imports == ("os.path",)


def test_a_plain_stdlib_import_is_not_forbidden(tmp_path):
    # The other side: the scan must not simply report everything.
    domain = tmp_path / "pfp" / "domain"
    domain.mkdir(parents=True)
    (domain / "clean.py").write_text(
        "import json\nfrom dataclasses import dataclass\n", encoding="utf-8"
    )
    assert domain_offences(tmp_path) == ()


# --------------------------------------------------------------------------
# The ratchet
# --------------------------------------------------------------------------


def offence(module: str, *imports: str) -> Offence:
    return Offence(module=module, imports=tuple(imports))


def test_a_new_offender_fails_the_ratchet():
    baseline = load_baseline(BASELINE_PATH)
    grown = domain_offences(REPO_ROOT) + (offence("domain/newcomer.py", "subprocess"),)
    problems = ratchet_violations(grown, baseline)
    assert any("newcomer" in p and "new domain offence" in p for p in problems)


def test_a_recorded_module_acquiring_another_import_fails():
    baseline = {"m.py": ("pathlib",)}
    problems = ratchet_violations((offence("m.py", "pathlib", "subprocess"),), baseline)
    assert any("acquired subprocess" in p for p in problems)


def test_a_cleaned_module_must_be_removed_from_the_baseline():
    # What makes this a ratchet rather than a permanent exemption list.
    baseline = {"m.py": ("pathlib",)}
    problems = ratchet_violations((), baseline)
    assert any("no longer offends" in p and "remove the entry" in p for p in problems)


def test_an_unchanged_offence_passes():
    baseline = {"m.py": ("pathlib",)}
    assert ratchet_violations((offence("m.py", "pathlib"),), baseline) == ()


def test_the_ratchet_is_identity_keyed_not_count_keyed():
    # Swapping one offender for another keeps the count and must still fail.
    baseline = {"alpha.py": ("pathlib",)}
    problems = ratchet_violations((offence("beta.py", "pathlib"),), baseline)
    assert len(problems) == 2, problems
    assert any("beta.py" in p for p in problems)
    assert any("alpha.py" in p for p in problems)


def test_an_offence_with_no_imports_is_refused():
    # An empty offence matches everything and would read as agreeing.
    with pytest.raises(FitnessError) as excinfo:
        Offence(module="m.py", imports=())
    assert excinfo.value.code == "EMPTY_OFFENCE"


def test_a_duplicate_baseline_entry_is_refused(tmp_path):
    path = tmp_path / "dupe.json"
    path.write_text(
        json.dumps(
            {
                "schema": BASELINE_SCHEMA,
                "domain_offences": [
                    {"module": "m.py", "imports": ["pathlib"]},
                    {"module": "m.py", "imports": ["os"]},
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(FitnessError) as excinfo:
        load_baseline(path)
    assert excinfo.value.code == "BASELINE_DUPLICATE"


def test_a_baseline_with_the_wrong_schema_is_refused(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(
        json.dumps({"schema": "v0", "domain_offences": []}), encoding="utf-8"
    )
    with pytest.raises(FitnessError) as excinfo:
        load_baseline(path)
    assert excinfo.value.code == "BASELINE_SCHEMA"


def test_an_absent_baseline_is_refused(tmp_path):
    with pytest.raises(FitnessError) as excinfo:
        load_baseline(tmp_path / "nope.json")
    assert excinfo.value.code == "BASELINE_ABSENT"


def test_the_rendered_baseline_round_trips(tmp_path):
    offences = domain_offences(REPO_ROOT)
    path = tmp_path / "rendered.json"
    path.write_text(
        render_baseline(offences, domain_module_count(REPO_ROOT)),
        encoding="utf-8",
        newline="\n",
    )
    assert ratchet_violations(offences, load_baseline(path)) == ()


def test_the_rendered_baseline_warns_that_regenerating_it_defeats_it():
    document = json.loads(render_baseline(domain_offences(REPO_ROOT), 100))
    assert "defeats it" in document["note"]


def test_an_empty_domain_layer_is_refused_rather_than_reported_clean(tmp_path):
    (tmp_path / "pfp" / "domain").mkdir(parents=True)
    with pytest.raises(FitnessError) as excinfo:
        domain_offences(tmp_path)
    assert excinfo.value.code == "DOMAIN_EMPTY"


def test_a_missing_domain_layer_is_refused(tmp_path):
    with pytest.raises(FitnessError) as excinfo:
        domain_offences(tmp_path)
    assert excinfo.value.code == "DOMAIN_ABSENT"


# --------------------------------------------------------------------------
# Criterion 5 -- packet_schemas/ (the former stages/) has nothing to deprecate
# --------------------------------------------------------------------------


def test_stages_holds_no_runtime_implementation_to_deprecate():
    """Criterion 5's subject does not exist, and that is worth pinning.

    Deliverable 3 asks to "deprecate redundant pure-Python runtime
    implementations in `stages/`". That directory, now `packet_schemas/`,
    holds JSON schemas, a README and a package marker of path constants. If a runtime module ever lands there, this
    fails and criterion 5 acquires a subject.
    """
    modules = stage_runtime_modules(REPO_ROOT)
    assert modules == (), f"packet_schemas/ now holds runtime modules: {modules}"


def test_the_stages_marker_holds_constants_and_no_implementation():
    """`packet_schemas/__init__.py` is not empty, and does not need to be.

    It holds a `pathlib` import and the schema-path constants. A first version
    of this test asserted the marker was *empty* and failed on them — the
    assertion was about the wrong property. What criterion 5 cares about is
    whether there is an **implementation** to deprecate, so this asserts the
    marker defines no callable.
    """
    marker = REPO_ROOT / "pfp" / "packet_schemas" / "__init__.py"
    tree = ast.parse(marker.read_text(encoding="utf-8"))
    callables = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    assert callables == [], "the packet schema marker now defines a callable"

    constants = [node for node in tree.body if isinstance(node, ast.Assign)]
    assert constants, "the marker is expected to hold schema path constants"


def test_the_stage_predicate_would_detect_an_implementation(tmp_path):
    """The criterion-5 test asserts an absence, so its predicate must fire.

    Sprint 019's rule: an absence assertion needs its query demonstrated.
    """
    stages = tmp_path / "pfp" / "packet_schemas"
    stages.mkdir(parents=True)
    (stages / "__init__.py").write_text("X = 1\n", encoding="utf-8")
    (stages / "legacy_runner.py").write_text(
        "def run(packet):\n    return packet\n", encoding="utf-8"
    )
    found = stage_runtime_modules(tmp_path)
    assert found == ("pfp/packet_schemas/legacy_runner.py",)


def test_the_stage_predicate_ignores_constants(tmp_path):
    stages = tmp_path / "pfp" / "packet_schemas"
    stages.mkdir(parents=True)
    (stages / "__init__.py").write_text(
        "from pathlib import Path\nROOT = Path('.')\n", encoding="utf-8"
    )
    assert stage_runtime_modules(tmp_path) == ()


# --------------------------------------------------------------------------
# Criteria 2 and 3 -- the extension does not exist, pinned
# --------------------------------------------------------------------------


def test_the_runtime_crate_declares_no_python_extension():
    """Why criteria 2 and 3 are deferred, asserted at the source.

    A PyO3 extension needs the crate to build a `cdylib`. It declares no `[lib]`
    section at all. If one appears, this fails and the deferral is stale.
    """
    manifest = (
        REPO_ROOT
        / "engine"
        / "crates_rs"
        / "core_symbol_game_runtime"
        / "Cargo.toml"
    ).read_text(encoding="utf-8")
    assert "cdylib" not in manifest
    assert "pyo3" not in manifest


def test_no_python_packaging_declares_a_native_extension():
    """The other half of the reason, measured.

    The old assertion was that no packaging metadata exists at all. A
    setuptools `pyproject.toml` now exists at the root; what matters for
    criteria 2 and 3 is that nothing declares an extension build.
    """
    for name in ("pyproject.toml", "setup.py", "setup.cfg"):
        path = REPO_ROOT / name
        if path.exists():
            text = path.read_text(encoding="utf-8").lower()
            for marker in ("maturin", "pyo3", "setuptools-rust", "setuptools_rust", "ext_modules"):
                assert marker not in text, f"{name} declares {marker}"


def test_the_existing_seam_is_a_subprocess_not_an_extension():
    # What the estate has today, so the deferral describes a real gap rather
    # than a missing feature nobody uses.
    source = (
        REPO_ROOT / "operating_system/adapters/rust_host/ffi.py"
    ).read_text(encoding="utf-8")
    assert "subprocess.run(" in source
    assert "import core_symbol_game_runtime" not in source


def test_the_seam_converts_native_failures_to_a_typed_error():
    """Criterion 2, over the seam that exists.

    The full panic/abort/truncation matrix needs the extension. What can be
    checked now is that the subprocess seam maps its failure modes rather than
    letting them escape.
    """
    source = (
        REPO_ROOT / "operating_system/adapters/rust_host/ffi.py"
    ).read_text(encoding="utf-8")
    for handled in ("HOST_TIMEOUT", "HOST_OUTPUT_NOT_JSON", "HOST_NONZERO_EXIT"):
        assert handled in source, f"the seam does not handle {handled}"
    adapter = (REPO_ROOT / "pfp/ffi.py").read_text(
        encoding="utf-8"
    )
    assert "return self._host.invoke_runtime(action, payload)" in adapter
    assert "subprocess.run(" not in adapter
    assert "RustHostError" not in adapter


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def test_the_report_states_coverage_before_findings():
    report = format_report(REPO_ROOT)
    assert "domain modules scanned" in report
    assert "domain offences" in report
    assert "seam import sites" in report


# --------------------------------------------------------------------------
# The provider gateway has exact reviewed composition sites
# --------------------------------------------------------------------------


def test_only_the_sanctioned_factories_build_raw_gateways():
    assert raw_gateway_constructors(REPO_ROOT) == ()
    # The positive control: the rule above is quiet both when the estate is
    # clean and when the gateway has been renamed away.
    assert sanctioned_gateway_factory_builds_one(REPO_ROOT) is True


def test_no_dotenv_importers_in_symbol_game():
    assert dotenv_importers(REPO_ROOT) == ()


def test_exec_eval_callers_are_within_allowlist():
    callers = exec_callers(REPO_ROOT)
    assert exec_violations(callers) == (), callers


def test_every_allowlisted_exec_caller_states_a_reason():
    for module, reason in EXEC_CALLER_ALLOWLIST.items():
        assert module.startswith("pfp/")
        assert "/tests/" not in module
        assert isinstance(reason, str) and len(reason) > 20, module


def test_a_new_exec_caller_fails_the_allowlist():
    grown = exec_callers(REPO_ROOT) + (
        "pfp/use_cases/newcomer.py",
    )
    problems = exec_violations(grown)
    assert any("newcomer.py" in p and "outside the allowlist" in p for p in problems)



def test_module_form_ffi_import_cannot_hide_from_seam_inventory():
    names = imported_names(
        "from operating_system.adapters.rust_host import ffi as native\n"
    )
    assert "operating_system.adapters.rust_host.ffi" in names


_TRACE_FACTORY = "pfp/infrastructure/trace/gateway_factories.py"
_ACCOUNTED_FACTORY = "pfp/infrastructure/estimated_gateway.py"


def _gateway_estate(tmp_path):
    sources = {
        _TRACE_FACTORY: (
            "from adversary.infrastructure.providers.gateway import OearsLlmGateway as Raw\n"
            "def _confined_gateway():\n    return Raw()\n"
        ),
        _ACCOUNTED_FACTORY: (
            "from adversary.infrastructure.providers.gateway import OearsLlmGateway as Raw, unbudgeted_gateway as unlimited\n"
            "def create_accounted_openrouter_gateway(unbounded=False):\n"
            "    if unbounded:\n        return unlimited()\n    return Raw.builtin()\n"
            "def checks_type(value):\n    return isinstance(value, Raw)\n"
        ),
    }
    for relative, source in sources.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    return sources


def test_guard_recognizes_both_existing_composition_functions(tmp_path):
    _gateway_estate(tmp_path)
    assert raw_gateway_constructors(tmp_path) == ()
    assert sanctioned_gateway_factory_builds_one(tmp_path)


@pytest.mark.parametrize(
    "source",
    [
        "from adversary.infrastructure.providers.gateway import unbudgeted_gateway as build\nbuild()\n",
        "from adversary.infrastructure.providers import gateway as g\ng.OearsLlmGateway.builtin()\n",
        "import adversary.infrastructure.providers.gateway as g\ng.unbudgeted_gateway()\n",
        "from adversary.infrastructure.providers.gateway import *\n",
        "from adversary.infrastructure.providers import gateway as g\n",
        "from adversary.infrastructure.providers import gateway as g\n",
    ],
)
def test_raw_provider_imports_outside_composition_are_refused(tmp_path, source):
    _gateway_estate(tmp_path)
    path = tmp_path / "pfp/use_cases/bypass.py"
    path.parent.mkdir(parents=True)
    path.write_text(source, encoding="utf-8")
    assert raw_gateway_constructors(tmp_path) == ("pfp/use_cases/bypass.py",)


@pytest.mark.parametrize(
    "relative, extra",
    [
        (_ACCOUNTED_FACTORY, "def bypass():\n    return Raw.builtin()\n"),
        (_ACCOUNTED_FACTORY, "rogue = unlimited()\n"),
        (
            _ACCOUNTED_FACTORY,
            "class Bypass:\n    def create_accounted_openrouter_gateway(self):\n        return Raw.builtin()\n",
        ),
        (_TRACE_FACTORY, "def extra():\n    return Raw()\n"),
        (_TRACE_FACTORY, "def extra(value=Raw()):\n    return value\n"),
        (_ACCOUNTED_FACTORY, "extra = lambda: unlimited()\n"),
    ],
)
def test_approved_module_is_not_blanket_constructor_permission(tmp_path, relative, extra):
    sources = _gateway_estate(tmp_path)
    (tmp_path / relative).write_text(sources[relative] + extra, encoding="utf-8")
    assert raw_gateway_constructors(tmp_path) == (relative,)


@pytest.mark.parametrize(
    "relative, before, after",
    [
        (_TRACE_FACTORY, "return Raw()", "return object()"),
        (_ACCOUNTED_FACTORY, "return Raw.builtin()", "return object()"),
        (_ACCOUNTED_FACTORY, "return unlimited()", "return object()"),
    ],
)
def test_each_existing_construction_path_has_a_positive_control(tmp_path, relative, before, after):
    sources = _gateway_estate(tmp_path)
    (tmp_path / relative).write_text(sources[relative].replace(before, after), encoding="utf-8")
    assert raw_gateway_constructors(tmp_path) == (relative,)
    assert not sanctioned_gateway_factory_builds_one(tmp_path)


def test_gateway_prose_and_type_mention_without_import_are_not_construction(tmp_path):
    _gateway_estate(tmp_path)
    (tmp_path / "pfp/notes.py").write_text(
        '"""OearsLlmGateway.builtin() and unbudgeted_gateway() are guarded."""\nvalue = 1\n',
        encoding="utf-8",
    )
    assert raw_gateway_constructors(tmp_path) == ()
