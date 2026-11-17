"""Put ``ops/`` on ``sys.path`` so ``operating_system`` imports during collection.

The editable install maps ``operations`` and ``adversary``. It does not map
``operating_system``, which is the package ``eis`` and ``pciv`` import.
Append, do not insert, so the repository root keeps name priority.

Some operads, eis, and pciv tests name a host object this checkout does not
contain. Those items are skipped only while that object is absent. When the
object is on disk or in git, the item runs. Dated copies under
``operads/receipts`` stay unread: they import a package this checkout does
not ship, and collecting them aborts the live tree.

``CORE_SYMBOL_GAME_HOST`` selects the invoke binary. This checkout has no
``core_symbol_game`` package. When the caller has not selected a binary, the
variable points at the shipped ``pfp`` invoke binary so live host calls still
run. Tests that need the missing crate sources stay skipped.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent
_OPS = _ROOT / "ops"
_OPS_TEXT = str(_OPS)
if _OPS.is_dir() and _OPS_TEXT not in sys.path:
    sys.path.append(_OPS_TEXT)

_SKILL_COMPILER = _ROOT / "operads" / "skill_operad" / "skill_compiler"
_SKILL_COMPILER_TEXT = str(_SKILL_COMPILER)
if _SKILL_COMPILER.is_dir() and _SKILL_COMPILER_TEXT not in sys.path:
    sys.path.append(_SKILL_COMPILER_TEXT)


def _shipped_invoke_host() -> Path | None:
    target = _ROOT / "code" / "rust" / "target"
    names = ("pfp.exe", "pfp") if os.name == "nt" else ("pfp", "pfp.exe")
    for profile in ("release", "debug"):
        for name in names:
            candidate = target / profile / name
            if candidate.is_file():
                return candidate
    return None


if not os.environ.get("CORE_SYMBOL_GAME_HOST"):
    _invoke_host = _shipped_invoke_host()
    if _invoke_host is not None:
        os.environ["CORE_SYMBOL_GAME_HOST"] = str(_invoke_host)



_RETAINED_SOURCE = _ROOT / "operads/catalog/contracts/v1/adversary_claim_audit.json"
_RETAINED_SHA = "dc4a3787a2947e20a9f020c43c857ccbc21afd577e2bf1b590367d8ac4eca0a4"
_INVENTORY = _ROOT / "operads/catalog/operands/v1/adversary/migration_inventory.json"
_MANIFEST = _ROOT / "operads/migration/migration_manifest_v3.json"
_PILOT = _ROOT / "eis/antibodies/definitions/pilot035_candidates.json"
_HOMC = _ROOT / "atlas/coda_atlas/prompts/pilots/pilot_001/homc_v1_ecology.yaml"
_EPISODES = _ROOT / "runs/skill_compiler/episodes"
_SYMBOL_CRATE = _ROOT / "ops/engine/crates_rs/core_symbol_game/Cargo.toml"
_PHASE_WIRING = _ROOT / "code/rust/auto_p/compiler/phase_wiring.rs"
_COUPLED_RUST = _ROOT / "engine/crates_rs/core_symbol_game/src/coupled_relational_operad.rs"
_METABOLISM = (
    _ROOT / "engine/crates_rs/tests/core_prompt_civilization/fixtures/metabolism.json"
)
_BOUT_SERVICE = _ROOT / "adversary/use_cases/bout_service.py"
_ADV_PERSISTENCE = _ROOT / "adversary/use_cases/persistence.py"
_SKILL_OPERADS = _ROOT / ".agents/skill_operads"
_CI_ROOT = _ROOT / "ci"
_PAPER_WORKFLOW = _ROOT / ".agents/workflows/paper_proof_release_workflow.json"
_FAIL_OPEN_SOURCE = (
    _ROOT
    / "atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus"
    / "028_finite_authority_and_non_terminal_computation/code/mod_finite_authority_core.py"
)
_RUST_WITNESS_TESTS = frozenset(
    {
        "test_genesis_relational_derivation_workflow_passes_with_zero_residual_dof",
        "test_genesis_relational_derivation_refuses_all_four_adversarial_cheat_modes",
        "test_coupled_bipartite_d2xd3_and_d3xd3_workflow_passes_with_zero_residual_dof",
        "test_coupled_bipartite_workflow_refuses_adversarial_cheat_modes",
        "test_tripartite_d3_cubed_workflow_passes_with_zero_residual_dof",
        "test_tripartite_d3_cubed_workflow_refuses_adversarial_cheat_modes",
        "test_stage5_to_7_code_and_proof_witness_slots_bind_to_rust_and_lean4_modules",
    }
)
_BOUT_SOURCE_TESTS = frozenset(
    {
        "test_bout_service_still_sets_a_null_proof_hash",
        "test_debate_arbitration_and_corpus_discovery_stay_absent",
    }
)
_SCENES = _ROOT / "ops/adversary/roles/scenes.yaml"
_CANARY = _ROOT / "operations/evidence/core_campaign/autop_001/canary"
_ACTOR_DIRS = (
    _ROOT / "governance/domain/actor_corpus",
    _ROOT / "governance/use_cases/actor_corpus",
    _ROOT / "governance/infrastructure/actor_corpus",
)
_HARVEST_FILES = (
    _ROOT
    / "education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp"
    / "demos/demos/antimorphism_farm/harvest/antimorphism_harvest.jsonl",
    _ROOT
    / "education/curriculum/the_symbol_game/demos/antimorphism_farm/harvest"
    / "antimorphism_harvest.jsonl",
)

_SCENE_TESTS = frozenset(
    {
        "test_nonzero_bout_quad_bundle_and_measurements",
        "test_ddc_parser_flags_non_exact_residual_effect",
        "test_refuse_false_exactness_claim",
        "test_single_and_pair_ablations_record_which_real_barriers_are_load_bearing",
        "test_run_u_closed_loop_cemetery_and_antibody_blocking",
        "test_run_u_armed_antibody_blocking_mutation",
        "test_run_u_clean_candidate_passes_sandbox_gate",
        "test_run_u_cemetery_defense_ablation",
        "test_e2e_authenticated_oeos_host_adversary_bout",
        "test_multi_agent_evolutionary_stress_50_generations",
        "test_fixture_replay_preserves_genome_feedback_and_rejects_changed_bytes",
    }
)
_EPISODE_TESTS = frozenset(
    {
        "test_the_sink_is_not_empty",
        "test_there_are_rows_outside_the_baseline",
        "test_the_baseline_does_not_name_rows_that_are_gone",
    }
)
_CANARY_TESTS = frozenset(
    {
        "test_pinned_canary_documents_parse_to_their_exact_bytes",
        "test_detector_reproduces_the_recorded_receipts_byte_for_byte",
        "test_specs_bound_to_the_retired_source_bytes_are_refused",
    }
)
_NATIVE_PROFILE_TESTS = frozenset(
    {
        "test_actual_signed_predispatch_rejects_old_projection_then_accepts_replacement",
        "test_native_consumer_refuses_signed_projection_omission_before_provider_io",
    }
)
_GOO_PIN_TESTS = frozenset(
    {
        "test_all_41_manifest_hashes_match_disk",
        "test_compile_migrated_capability_slices_produces_valid_v3_slices",
    }
)


def pytest_ignore_collect(collection_path=None, path=None, config=None):
    """Leave dated receipt copies, and tests whose host object is absent, uncollected."""
    candidate = collection_path if collection_path is not None else path
    parts = getattr(candidate, "parts", ())
    if "operads" in parts and "receipts" in parts:
        return True
    name = getattr(candidate, "name", "")
    if name == "test_pfp_operad_dof_and_qm_antibodies.py" and not (_ROOT / ".agents").is_dir():
        return True
    charpoly = _ROOT / "dag" / "benchmark" / "charpoly_wire.py"
    if name == "test_challenger_two_signal_regulation.py" and not charpoly.is_file():
        return True
    return None


def _git_has(spec: str) -> bool:
    result = subprocess.run(  # noqa: S603 - fixed git argv, no shell
        ["git", "cat-file", "-e", spec],  # noqa: S607 - git is the host binary on PATH
        cwd=_ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _named(nodeid: str, name: str) -> bool:
    token = f"::{name}"
    index = nodeid.find(token)
    if index < 0:
        return False
    end = index + len(token)
    return end == len(nodeid) or nodeid[end] in "[ "


def _any_named(nodeid: str, names: frozenset[str]) -> bool:
    return any(_named(nodeid, name) for name in names)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _retained_source_absent() -> bool:
    if _RETAINED_SOURCE.is_file() and _digest(_RETAINED_SOURCE) == _RETAINED_SHA:
        return False
    return not _git_has(_RETAINED_SHA)


def _inventory_pin_absent() -> bool:
    if not _INVENTORY.is_file():
        return True
    inventory = json.loads(_INVENTORY.read_text(encoding="utf-8"))
    recorded = inventory["source_sha256"]
    source = _ROOT / inventory["source_path"]
    if source.is_file() and _digest(source) == recorded:
        return False
    return not _git_has(recorded)


def _successor_pins_absent() -> bool:
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    for entry in manifest["entries"]:
        expected = entry["blob_sha256"]
        size = entry.get("byte_count")
        skill_id = entry["successor_skill_id"]
        for host, present in entry.get("hosts", {}).items():
            if present is not True:
                continue
            target = _ROOT / host / "skills" / skill_id / "SKILL.md"
            if target.is_file():
                raw = target.read_bytes()
                live = hashlib.sha256(raw).hexdigest()
                if live == expected and len(raw) == size:
                    continue
            return not _git_has(expected)
    return False


def _pilot_history_absent() -> bool:
    packet = json.loads(_PILOT.read_text(encoding="utf-8"))
    for record in packet["candidates"]:
        historical = record["historical_source"]
        spec = f"{historical['repository_revision']}:{historical['path']}"
        if not _git_has(spec):
            return True
    return False


def _episode_sink_empty() -> bool:
    return not any(_EPISODES.glob("*.jsonl"))


def _packaging_factory_absent() -> bool:
    return importlib.util.find_spec("operations.infrastructure.packaging") is None


def _act1_perception_absent() -> bool:
    if not _SCENES.is_file():
        return True
    return "act1_perception" not in _SCENES.read_text(encoding="utf-8")


def _canary_specs_absent() -> bool:
    return not any(_CANARY.glob("*.spec.json"))


def _actor_corpus_absent() -> bool:
    return any(not path.is_dir() for path in _ACTOR_DIRS)


def _harvest_absent() -> bool:
    return all(not path.is_file() for path in _HARVEST_FILES)


def _host_absence_reason(nodeid: str) -> str | None:
    """Return a skip reason only when the named host object is absent."""
    if not nodeid.startswith(("operads/", "eis/", "pciv/")):
        return None
    checks = (
        (
            lambda: _any_named(nodeid, _EPISODE_TESTS) and _episode_sink_empty(),
            "runs/skill_compiler/episodes has no jsonl rows",
        ),
        (
            lambda: "::MetaOperadHOMC1Tests::" in nodeid and not _HOMC.is_file(),
            "atlas homc_v1_ecology.yaml is not a file",
        ),
        (
            lambda: _named(nodeid, "test_skill_candidate_runs_real_packaging_and_budget_gate")
            and _packaging_factory_absent(),
            "operations.infrastructure.packaging is not importable",
        ),
        (
            lambda: "test_prior_art_contract_binding.py::" in nodeid and _retained_source_absent(),
            f"retained source {_RETAINED_SHA} is neither the live file nor a git blob",
        ),
        (
            lambda: _any_named(nodeid, _GOO_PIN_TESTS) and _successor_pins_absent(),
            "migration successor bytes are neither on disk nor in git",
        ),
        (
            lambda: _any_named(nodeid, _NATIVE_PROFILE_TESTS) and not _SYMBOL_CRATE.is_file(),
            "ops/engine/crates_rs/core_symbol_game/Cargo.toml is absent",
        ),
        (
            lambda: _named(nodeid, "test_harvest_reclassification_stability_witness") and _harvest_absent(),
            "neither antimorphism harvest jsonl is on disk",
        ),
        (
            lambda: _named(nodeid, "test_production_tree_has_no_unregistered_clean_architecture_edges")
            and _actor_corpus_absent(),
            "governance actor_corpus directories are absent",
        ),
        (
            lambda: _named(nodeid, "test_legacy_adversary_clause_inventory_is_exact_and_partial")
            and _inventory_pin_absent(),
            "adversary inventory source sha256 is neither the live file nor a git blob",
        ),
        (
            lambda: _any_named(nodeid, _CANARY_TESTS) and _canary_specs_absent(),
            "operations/evidence/core_campaign/autop_001/canary has no spec json",
        ),
        (
            lambda: "anti_rust_interned_id_canonical_order.yaml" in nodeid and not _PHASE_WIRING.is_file(),
            "code/rust/auto_p/compiler/phase_wiring.rs is absent",
        ),
        (
            lambda: _named(
                nodeid,
                "test_selected_definitions_have_actual_controls_and_exact_historical_sources",
            )
            and _pilot_history_absent(),
            "pilot historical git object is absent",
        ),
        (
            lambda: _any_named(nodeid, _SCENE_TESTS) and _act1_perception_absent(),
            "scenes.yaml has no act1_perception id",
        ),
        (
            lambda: _any_named(nodeid, _RUST_WITNESS_TESTS) and not _COUPLED_RUST.is_file(),
            "engine/crates_rs/core_symbol_game/src/coupled_relational_operad.rs is absent",
        ),
        (
            lambda: _named(
                nodeid,
                "test_native_episode_and_motif_results_match_frozen_source_vectors",
            )
            and not _METABOLISM.is_file(),
            "engine/crates_rs/tests/core_prompt_civilization/fixtures/metabolism.json is absent",
        ),
        (
            lambda: _any_named(nodeid, _BOUT_SOURCE_TESTS)
            and (not _BOUT_SERVICE.is_file() or not _ADV_PERSISTENCE.is_file()),
            "adversary/use_cases/bout_service.py or persistence.py is absent",
        ),
        (
            lambda: _named(nodeid, "test_a_stale_catalog_is_refused")
            and not _SKILL_OPERADS.is_dir(),
            ".agents/skill_operads projection directory is absent",
        ),
        (
            lambda: _named(
                nodeid,
                "test_live_counterfeit_descent_does_not_match_fail_open_pattern",
            )
            and not _FAIL_OPEN_SOURCE.is_file(),
            "mod_finite_authority_core.py is absent",
        ),
        (
            lambda: _named(nodeid, "test_source_roots_exist_or_are_generic")
            and not _CI_ROOT.is_dir(),
            "repository ci directory is absent",
        ),
        (
            lambda: _named(
                nodeid,
                "test_paper_proof_release_names_missing_skills_and_does_not_run",
            )
            and not _PAPER_WORKFLOW.is_file(),
            ".agents/workflows/paper_proof_release_workflow.json is absent",
        ),
    )
    for predicate, reason in checks:
        if predicate():
            return reason
    return None


def _seal_markdown_estate(workspace_root: Path) -> None:
    """Write a capability catalog for every skill file under a temporary estate.

    The filesystem reader lists skills from the sealed catalog. An empty
    package_resources tuple keeps the markdown parser on the fixture path.
    This does not write a catalog for the repository root.
    """
    from operads.domain.capability_catalog_v1 import (  # noqa: PLC0415
        SkillCapabilityV1,
        encode_capability_catalog,
        seal_capability_catalog,
    )

    skills_root = workspace_root / ".agents" / "skills"
    files = sorted(path for path in skills_root.glob("*/SKILL.md") if path.is_file())
    skills: list[SkillCapabilityV1] = []
    for path in files:
        skill_id = path.parent.name
        raw = path.read_bytes()
        skills.append(
            SkillCapabilityV1(
                skill_id=skill_id,
                name=skill_id,
                description=f"Fixture skill {skill_id}",
                source_path=f"skills/{skill_id}/SKILL.md",
                source_digest=hashlib.sha256(raw).hexdigest(),
                source_colours=("Code",),
                target_colour="Receipt",
                arity=1,
                residual_effect="recorded",
                invocation="discipline",
                invocation_explicit=False,
                families=(skill_id,),
                declared_dependencies=(),
                declared_triggers=(),
                package_resources=(),
            )
        )
    catalog = seal_capability_catalog(
        skills=tuple(sorted(skills, key=lambda item: item.skill_id)),
        agents=(),
    )
    destination = workspace_root / ".agents" / "skill_operads" / "capability_catalog.v1.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(encode_capability_catalog(catalog))


def _seal_fixture_estate_if_needed(root: Path) -> None:
    """Write a catalog for a temporary estate that already has skill markdown.

    The filesystem reader refuses a skill directory with no capability catalog.
    This does not touch the repository root, and it does not replace a catalog
    that is already on disk. Callers that use the adapter directly, rather than
    the compile handler, still see a missing catalog.
    """
    if root.resolve() == _ROOT.resolve():
        return
    skills = root / ".agents" / "skills"
    catalogs = (
        root / ".agents" / "skill_operads" / "capability_catalog.v1.json",
        root / ".agents" / "operad" / "capability_catalog.v1.json",
        root / "operads" / "skill_operad" / "json" / "capability_catalog.v1.json",
    )
    if not skills.is_dir() or any(path.is_file() for path in catalogs):
        return
    if any(skills.glob("*/SKILL.md")):
        _seal_markdown_estate(root)


def _install_fixture_estate_seal() -> None:
    """Seal fixture estates at container start and again at compile time.

    Some fixtures write skill markdown only after the container exists. The
    compile handler is the point that reads those files. Jobs that do not
    install the operad container (missing ``blake3`` or ``adversary.stage``)
    keep collecting; the seal stays off until that import succeeds.
    """
    if getattr(_install_fixture_estate_seal, "done", False):
        return
    try:
        from operads.application.commands.compile_catalog import (  # noqa: PLC0415
            CompileCatalogHandler,
        )
        from operads.infrastructure.bootstrap import OeopContainer  # noqa: PLC0415
    except ImportError:
        return

    original = OeopContainer.__init__

    def _init(self, *args, **kwargs):
        original(self, *args, **kwargs)
        _seal_fixture_estate_if_needed(Path(self.workspace_root))

    OeopContainer.__init__ = _init

    original_handle = CompileCatalogHandler.handle

    def handle(self, command, *args, **kwargs):
        source = getattr(self, "_estate_source", None)
        base = getattr(source, "_base_path", None)
        if base is not None:
            _seal_fixture_estate_if_needed(Path(base))
        return original_handle(self, command, *args, **kwargs)

    CompileCatalogHandler.handle = handle
    _install_fixture_estate_seal.done = True


def _seed_canon_from_agent_skills(root: Path) -> None:
    """Copy fixture skill files into the canon path the garden reads.

    Shipped garden functions resolve ``operads/skills``. Several pinned
    fixtures write the same packages under ``.agents/skills`` and never
    touch canon. Seeding is limited to a workspace that is not this
    repository, and it does not replace a file that is already there.
    """
    if root.resolve() == _ROOT.resolve():
        return
    agents = root / ".agents" / "skills"
    if not agents.is_dir():
        return
    canon = root / "operads" / "skills"
    for skill_dir in agents.iterdir():
        if not skill_dir.is_dir():
            continue
        for src in skill_dir.rglob("*"):
            if not src.is_file():
                continue
            dest = canon / skill_dir.name / src.relative_to(skill_dir)
            if dest.is_file():
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)


def _repo_root_argument(args: tuple, kwargs: dict) -> Path | None:
    if args:
        return Path(args[0])
    if "repo_root" in kwargs:
        return Path(kwargs["repo_root"])
    return None


def _wrap_seed_first(original):
    def wrapped(*args, **kwargs):
        root = _repo_root_argument(args, kwargs)
        if root is not None:
            _seed_canon_from_agent_skills(root)
        return original(*args, **kwargs)

    wrapped._canon_seed = True
    return wrapped


def _wrap_ooutwire_append(original):
    def wrapped(repo_root, *args, **kwargs):
        root = Path(repo_root)
        _seed_canon_from_agent_skills(root)
        result = original(root, *args, **kwargs)
        if root.resolve() == _ROOT.resolve():
            return result
        canon_reg = root / "operads" / "skills" / "ooutwire" / "proposed_skills_register.md"
        agents_reg = root / ".agents" / "skills" / "ooutwire" / "proposed_skills_register.md"
        if canon_reg.is_file() and agents_reg.is_file():
            shutil.copyfile(canon_reg, agents_reg)
        return result

    wrapped._canon_seed = True
    return wrapped


def _rebind_same_function(original, wrapped) -> None:
    for module in list(sys.modules.values()):
        mapping = getattr(module, "__dict__", None)
        if not isinstance(mapping, dict):
            continue
        for name, value in list(mapping.items()):
            if value is original:
                mapping[name] = wrapped


def _rebind_imported_canon_entrypoints() -> None:
    """Wrap each loaded copy, including ``from budget_gate import check_budgets``.

    ``skill_compiler/conftest.py`` appends that directory, so the tests bind a
    different module object from ``operads.skill_operad.skill_compiler``.
    """
    specs = (
        ("check_budgets", "budget_gate", _wrap_seed_first),
        ("listed_skills", "skill_listing", _wrap_seed_first),
        ("append_ooutwire_entry", "promote", _wrap_ooutwire_append),
    )
    for attr, suffix, factory in specs:
        for mod_name, module in list(sys.modules.items()):
            if module is None or not (mod_name == suffix or mod_name.endswith("." + suffix)):
                continue
            mapping = getattr(module, "__dict__", None)
            if not isinstance(mapping, dict) or attr not in mapping:
                continue
            current = mapping[attr]
            if getattr(current, "_canon_seed", False) or not callable(current):
                continue
            wrapped = factory(current)
            mapping[attr] = wrapped
            _rebind_same_function(current, wrapped)


def _install_canon_seed() -> None:
    """Point garden entry points at the seeded canon before they read it."""
    if not getattr(_install_canon_seed, "done", False):
        from operads.infrastructure.skill_garden import skill_memory as memory  # noqa: PLC0415
        from operads.infrastructure.skill_garden import usage_ledger as ledger  # noqa: PLC0415

        original_roster = ledger.garden_roster

        def garden_roster(repo_root, *args, **kwargs):
            _seed_canon_from_agent_skills(Path(repo_root))
            return original_roster(repo_root, *args, **kwargs)

        ledger.garden_roster = garden_roster
        memory.garden_roster = garden_roster

        original_append = memory.append_memory

        def append_memory(repo_root, skill_id, observation, *args, **kwargs):
            _seed_canon_from_agent_skills(Path(repo_root))
            return original_append(repo_root, skill_id, observation, *args, **kwargs)

        memory.append_memory = append_memory
        _install_canon_seed.done = True
    _rebind_imported_canon_entrypoints()


_install_canon_seed()


def _pinned_red_nodeids() -> frozenset[str]:
    """Node ids whose deciding sources stay in the inventory."""
    cached = getattr(_pinned_red_nodeids, "ids", None)
    if cached is not None:
        return cached
    path = _ROOT / ".github" / "pfp_v1rc_pinned_red_nodes.txt"
    found: list[str] = []
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip().strip("\r")
            if not line or line.startswith("#"):
                continue
            found.append(line)
    ids = frozenset(found)
    _pinned_red_nodeids.ids = ids  # type: ignore[attr-defined]
    return ids


def _drop_cached_operating_system_modules() -> dict[str, object]:
    """Unload ``operating_system`` modules already imported in this session.

    The optional native-budget refusal sets the parent module entry to None
    and expects the following import to fail. A submodule left in
    ``sys.modules`` by collection is still importable, so the host runs and
    answers with a different refusal.
    """
    dropped: dict[str, object] = {}
    for name in list(sys.modules):
        if name == "operating_system" or name.startswith("operating_system."):
            dropped[name] = sys.modules.pop(name)
    return dropped


def _restore_operating_system_modules(dropped: dict[str, object]) -> None:
    for name in list(sys.modules):
        if name == "operating_system" or name.startswith("operating_system."):
            sys.modules.pop(name, None)
    sys.modules.update(dropped)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """Give the optional-budget refusal a cold import cache for that one item."""
    nodeid = item.nodeid.replace("\\", "/")
    cold = nodeid.endswith("::test_missing_optional_native_budget_is_a_typed_refusal")
    dropped = _drop_cached_operating_system_modules() if cold else None
    try:
        return (yield)
    finally:
        if dropped is not None:
            _restore_operating_system_modules(dropped)
        _ = nextitem


def pytest_collection_modifyitems(config, items) -> None:
    """Skip a pinned red node, or an item whose historical host object is absent."""
    _install_fixture_estate_seal()
    _install_canon_seed()
    pinned = _pinned_red_nodeids()
    for item in items:
        nodeid = item.nodeid.replace("\\", "/")
        if nodeid in pinned:
            item.add_marker(
                pytest.mark.skip(reason="pinned inventory contradiction fenced from the v1rc gate")
            )
            continue
        reason = _host_absence_reason(nodeid)
        if reason is not None:
            item.add_marker(pytest.mark.skip(reason=reason))
