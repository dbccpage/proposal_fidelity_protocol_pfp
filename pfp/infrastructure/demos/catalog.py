"""Explicit, resource-backed MSS-N scenario catalog. AuthorityEffect: None."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from omega_engine_pfp.domain.demos import DemoRefusal, Scenario

from .canonical import canonical, digest, load

PACKAGE = "omega_engine_pfp.infrastructure.adapters.mssn_research"

# The retained catalog describes the original layout. Current execution reads
# explicit successor owners; historical receipts still need their pinned code.
_CURRENT_IMPLEMENTATION_OWNERS = {
    ("omega_engine_providers", "adapters/native_functional.py"):
        ("omega_engine_woland", "infrastructure/providers/adapters/native_functional.py"),
    ("omega_engine_providers", "infrastructure/openai_compat.py"):
        ("omega_engine_woland", "infrastructure/providers/openai_compat.py"),
}
# Retained MSSN module entries can have several current defining sources.
# This table names those sources explicitly; missing successor bytes are fatal.
_CURRENT_MSSN_SOURCE_PROJECTION = {
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/grammar/entities.py"): (
        "domain/mssn_research/grammar/entities.py",
    ),
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/grammar/errors.py"): (
        "domain/mssn_research/grammar/errors.py",
    ),
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/grammar/invariants.py"): (
        "domain/mssn_research/grammar/authority_policies.py",
        "domain/mssn_research/grammar/foundational_policies.py",
        "domain/mssn_research/grammar/lift_policies.py",
        "domain/mssn_research/grammar/quantifier_policies.py",
        "domain/mssn_research/grammar/rewriting_policies.py",
        "domain/mssn_research/grammar/spectral_policies.py",
    ),
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/grammar/repository.py"): (
        "domain/mssn_research/grammar/ports.py",
        "infrastructure/adapters/mssn_research/contracts/grammar/ledger_codec.py",
        "infrastructure/adapters/mssn_research/contracts/grammar/ledger_repository.py",
    ),
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/grammar/value_objects.py"): (
        "domain/mssn_research/grammar/authority.py",
        "domain/mssn_research/grammar/exact_structures.py",
        "domain/mssn_research/grammar/lexical.py",
        "domain/mssn_research/grammar/quantification.py",
        "domain/mssn_research/grammar/rewriting.py",
        "domain/mssn_research/grammar/spectral_geometry.py",
    ),
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/packets/entities.py"): (
        "domain/mssn_research/packets/entities.py",
    ),
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/packets/errors.py"): (
        "domain/mssn_research/packets/errors.py",
    ),
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/packets/invariants.py"): (
        "domain/mssn_research/packets/invariants.py",
    ),
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/packets/value_objects.py"): (
        "domain/mssn_research/packets/parser.py",
        "domain/mssn_research/packets/value_objects.py",
    ),
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/shared_kernel/__init__.py"): (
        "domain/mssn_research/shared_kernel/__init__.py",
    ),
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/shared_kernel/result.py"): (
        "domain/mssn_research/shared_kernel/result.py",
    ),
    ("omega_engine_pfp", "infrastructure/adapters/mssn_research/contracts/shared_kernel/value_objects.py"): (
        "domain/mssn_research/shared_kernel/value_objects.py",
    ),
}
_CURRENT_MSSN_PACKAGE_SOURCES = (
    "domain/mssn_research/__init__.py",
    "domain/mssn_research/grammar/__init__.py",
    "domain/mssn_research/packets/__init__.py",
)
_PFP_TURN_SOURCES = (
    "domain/contracts/pfp_runtime.py",
    "infrastructure/estimated_gateway.py",
    "infrastructure/pilot_matrix.py",
    "infrastructure/task_turn.py",
    "use_cases/pfp_prompt.py",
    "use_cases/pfp_proposal.py",
)


def catalog_data():
    return load(files(PACKAGE).joinpath("catalog.json").read_bytes())


def scenarios():
    return tuple(Scenario(**row["scenario"]) for row in catalog_data()["scenarios"])


def lookup(scenario_id):
    for row in catalog_data()["scenarios"]:
        if row["scenario"]["scenario_id"] == scenario_id:
            return row
    raise DemoRefusal("UNKNOWN_SCENARIO", scenario_id)


def scenario_fixture_bytes(row):
    """Return the exact catalog-pinned bytes before any JSON normalization."""
    data = files(PACKAGE).joinpath(row["fixture_path"]).read_bytes()
    if digest(data) != row["fixture_sha256"]:
        raise DemoRefusal("SCENARIO_FIXTURE_DIGEST_MISMATCH")
    return data


def scenario_fixture(row):
    return load(scenario_fixture_bytes(row))


def implementation_digest():
    # Bind the code actually used by this release, independently of a receipt's
    # declared version. Every source path is a package-relative, closed entry.
    manifest = catalog_data()["implementation"]
    found = {"catalog.json": digest(files(PACKAGE).joinpath("catalog.json").read_bytes())}
    for package, paths in manifest.items():
        for path in paths:
            projected = _CURRENT_MSSN_SOURCE_PROJECTION.get((package, path))
            sources = (
                tuple((package, current) for current in projected)
                if projected is not None
                else (_CURRENT_IMPLEMENTATION_OWNERS.get((package, path), (package, path)),)
            )
            for owner, current in sources:
                found[owner + "/" + current] = digest(files(owner).joinpath(current).read_bytes())
    for path in (*_PFP_TURN_SOURCES, *_CURRENT_MSSN_PACKAGE_SOURCES):
        found["omega_engine_pfp/" + path] = digest(files("omega_engine_pfp").joinpath(path).read_bytes())

    return digest(canonical(found))


@dataclass(frozen=True)
class RegistryClosureReport:
    is_closed: bool
    schema_version: str
    demo_dirs_count: int
    front_ends_count: int
    registered_challenges_count: int
    packet_built_challenges_count: int
    missing_demo_dirs: tuple[str, ...]
    extra_front_ends: tuple[str, ...]
    missing_challenges: tuple[str, ...]
    extra_challenges: tuple[str, ...]
    unimportable_use_cases: tuple[str, ...]
    missing_test_files: tuple[str, ...]


def resolve_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "omega_engine_education").is_dir() and (parent / "omega_engine_pfp").is_dir():
            return parent
    return current.parents[4]


def registry_closure(repo_root: Path | None = None, strict: bool = False) -> RegistryClosureReport:
    """Evaluate set-closure between curriculum demo folders, registered front ends, and packet-built challenges."""
    root = repo_root or resolve_repo_root()
    data = catalog_data()
    schema_ver = data.get("schema", "")

    # 1. Demo directories on disk vs front_end entries in catalog
    demos_dir = root / "omega_engine_education" / "documentation" / "3_the_symbol_game_proposal_fidelity_protocol_pfp" / "demos" / "demos"
    if not demos_dir.is_dir():
        demos_dir = root / "omega_engine_education" / "documentation" / "030_the_symbol_game_proposal_fidelity_protocol_pfp" / "demos" / "demos"
    if not demos_dir.is_dir():
        demos_dir = root / "omega_engine_education" / "curriculum" / "the_symbol_game" / "demos"
    disk_demo_dirs = set()
    if demos_dir.is_dir():
        disk_demo_dirs = {
            p.name for p in demos_dir.iterdir()
            if p.is_dir() and not p.name.startswith("__") and p.name != "inputs"
        }

    front_ends = {
        s["scenario"]["front_end"]
        for s in data.get("scenarios", [])
        if "front_end" in s.get("scenario", {}) and s["scenario"]["front_end"]
    }

    missing_dirs = tuple(sorted(disk_demo_dirs - front_ends))
    extra_front_ends = tuple(sorted(front_ends - disk_demo_dirs))

    # 2. Registered challenges in catalog.json vs packet_built entries in catalog.yaml
    catalog_yaml_path = root / "omega_engine_education" / "documentation" / "3_the_symbol_game_proposal_fidelity_protocol_pfp" / "demos" / "challenges" / "catalog.yaml"
    if not catalog_yaml_path.is_file():
        catalog_yaml_path = root / "omega_engine_education" / "documentation" / "030_the_symbol_game_proposal_fidelity_protocol_pfp" / "demos" / "challenges" / "catalog.yaml"
    if not catalog_yaml_path.is_file():
        catalog_yaml_path = root / "omega_engine_education" / "curriculum" / "the_symbol_game" / "challenges" / "catalog.yaml"
    packet_built_challenges = set()
    if catalog_yaml_path.is_file():
        try:
            import yaml
            with open(catalog_yaml_path, "r", encoding="utf-8") as f:
                c_yaml = yaml.safe_load(f)
            packet_built_challenges = {
                c["id"] for c in c_yaml.get("challenges", [])
                if c.get("status") == "packet_built"
            }
        except Exception:
            pass

    registered_challenges = set(data.get("registered_challenges", []))
    missing_challenges = tuple(sorted(packet_built_challenges - registered_challenges))
    extra_challenges = tuple(sorted(registered_challenges - packet_built_challenges))

    # 3. Use cases importability & test file existence
    unimportable = []
    missing_tests = []
    import importlib

    for row in data.get("scenarios", []):
        sc = row.get("scenario", {})
        if "use_case" in sc and sc["use_case"]:
            uc_target = sc["use_case"]
            mod_name = uc_target[:-4] if uc_target.endswith(".run") else uc_target
            try:
                importlib.import_module(mod_name)
            except Exception as e:
                unimportable.append(f"{sc.get('scenario_id')}: {mod_name} ({e})")

        if "test" in sc and sc["test"]:
            test_rel = sc["test"]
            test_file = root / test_rel
            if not test_file.is_file():
                missing_tests.append(f"{sc.get('scenario_id')}: {test_rel}")

    unimportable_tuple = tuple(sorted(unimportable))
    missing_tests_tuple = tuple(sorted(missing_tests))

    is_closed = (
        schema_ver == "omega.mssn.catalog.v2"
        and not missing_dirs
        and not extra_front_ends
        and not missing_challenges
        and not extra_challenges
        and not unimportable_tuple
        and not missing_tests_tuple
        and len(disk_demo_dirs) == len(front_ends)
        and len(disk_demo_dirs) > 0
    )

    report = RegistryClosureReport(
        is_closed=is_closed,
        schema_version=schema_ver,
        demo_dirs_count=len(disk_demo_dirs),
        front_ends_count=len(front_ends),
        registered_challenges_count=len(registered_challenges),
        packet_built_challenges_count=len(packet_built_challenges),
        missing_demo_dirs=missing_dirs,
        extra_front_ends=extra_front_ends,
        missing_challenges=missing_challenges,
        extra_challenges=extra_challenges,
        unimportable_use_cases=unimportable_tuple,
        missing_test_files=missing_tests_tuple,
    )

    if strict and not is_closed:
        raise DemoRefusal("DEMO_REGISTRY_NOT_CLOSED", str(report))

    return report

