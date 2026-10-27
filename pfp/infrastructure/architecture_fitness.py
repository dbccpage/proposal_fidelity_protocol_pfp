"""Architectural fitness rules for the Symbol Game package.

`EPIC-OE-SYMGAM-009` states five acceptance criteria. Three of them are
architectural rules over Python source and can be enforced today:

* **Criterion 1** -- exactly one module imports the native seam, mirroring
  `RULE_FFI_SEAM_ISOLATION_001`.
* **Criterion 4** -- no module under `domain/` imports the extension, the
  filesystem, or a process.
* **Criterion 5** -- superseded implementations in `stages/` refuse on call
  rather than silently serving results the native path would produce
  differently.

The other two -- typed native failures across the full panic/abort/truncation
matrix, and a measured sub-15us dispatch overhead -- describe a **PyO3 extension
that does not exist**, and cannot be built without infrastructure this
repository deliberately lacks. The measurements are in the sprint's discovery
witness; the short version is that `core_symbol_game_runtime` declares no
`[lib]` section, so it produces no `cdylib`, and there is no `pyproject.toml`,
`setup.py` or `setup.cfg` anywhere in the tree.

# What was measured, and why it is a ratchet rather than a repair

**Some modules under `domain/` import `pathlib`.** The measured set and the
module count are in `architecture_baseline.json`; this docstring does not repeat
the figures, because a hand-kept count here went stale once already.

Criterion 4 names the filesystem, and `pathlib` is the filesystem. Rewriting
domain aggregates to take paths as arguments is a real refactor with real risk.

So the offenders are recorded by **identity**, and the ratchet enforces three
things: a new offender fails, a listed module that acquires a *second* forbidden
import fails, and a listed module that has been cleaned fails until its entry is
removed. The last is what makes it a ratchet rather than a permanent exemption.

Criterion 1 is enforced the same way: `ffi.py` plus `SEAM_IMPORT_ALLOWLIST`,
each entry with its reason, shrink-only.

# What is deliberately not checked

Doc comments. An earlier grep for the native module's name matched two `domain/`
modules that merely *mention* `core_symbol_game_runtime` in prose describing
what they mirror. Import analysis is done over the AST, so a module is an
offender only when it actually imports something.

`AuthorityEffect: None`. Measuring an import graph is not certifying an
architecture.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path

BASELINE_SCHEMA = "core.symgam.architecture_baseline.v1"

PACKAGE = Path("pfp")
DOMAIN = PACKAGE / "domain"
SEAM_MODULE = PACKAGE / "ffi.py"
PACKET_SCHEMAS = PACKAGE / "packet_schemas"

# Modules a domain layer may not reach for. The criterion names three families;
# these are their concrete Python spellings.
FORBIDDEN_IN_DOMAIN = frozenset(
    {
        # the filesystem
        "pathlib",
        "os",
        "shutil",
        "tempfile",
        "glob",
        "io",
        # a process
        "subprocess",
        "multiprocessing",
        "signal",
        # the network, which is a process boundary by another name
        "socket",
        "http",
        "urllib",
        "requests",
        # a database
        "sqlite3",
    }
)

# Names that would indicate the native extension itself.
NATIVE_MARKERS = ("core_symbol_game_runtime", "_core_symbol_game")

# Non-test modules other than `ffi.py` that import the seam, each with the reason
# it is tolerated. Shrink-only: a new importer fails `seam_violations`, and a
# listed module that stops importing the seam fails until its entry is removed.
SEAM_IMPORT_ALLOWLIST: dict[str, str] = {
    "pfp/infrastructure/challenge_execution.py": (
        "existing finite campaign consumer binds Q40 verifier evidence and binary "
        "digest through the canonical application host; no process spawning is duplicated"
    ),
    "pfp/infrastructure/code_change_checker.py": (
        "existing source/candidate-bound code-change adapter checks the host-pinned "
        "binary and delegates proposal, submission and gate operations to the PFP "
        "host; OEOS owns process launch and transport"
    ),
    "pfp/infrastructure/normal_forms/qm_classical.py": (
        "existing QM/classical adapter delegates experiment and certificate checks "
        "to the canonical OEOS invoke_runtime seam, retaining complete outcomes "
        "without a Python solver or process-launch fallback"
    ),
    "pfp/infrastructure/seat_transport/anthropic_messages.py": (
        "existing provider transport adapter forwards bounded Messages dispatch to "
        "the OEOS native host, which owns budget refusal, execution and raw output custody"
    ),
    "pfp/infrastructure/seat_transport/routing.py": (
        "existing seat-routing adapter invokes exact native routing/accounting "
        "operations through OEOS; it does not implement another process launcher"
    ),
    "pfp/infrastructure/adapters/reply_control_adapter.py": (
        "infrastructure implementation of ReplyControlPort; forwards the complete "
        "native parser/residual outcome through the canonical OEOS process seam"
    ),
    "pfp/entrypoints/cli/host_cli.py": (
        "presentation composition root replacing former raw symgam process spawn; "
        "preserves classifier/detector bytes while OEOS owns process control"
    ),
    "pfp/infrastructure/sandbox/local_process_sandbox.py": (
        "infrastructure adapter behind ProcessSandboxPort; uses the canonical "
        "OEOS RustSandboxHost transport and never launches submitted code in Python"
    ),
    "pfp/infrastructure/adapters/decode_controls/local_hf_mechanism.py": (
        "infrastructure adapter behind DecodeControlPort; simulates attention distractor "
        "key masking and token intervention via native host"
    ),
    "pfp/infrastructure/adapters/decode_controls/vllm_decode_adapter.py": (
        "infrastructure adapter behind DecodeControlPort; formats structured JSON schema, "
        "GBNF grammar, and logit bias controls via native host"
    ),
    "pfp/infrastructure/adapters/exact_rust_adapter.py": (
        "infrastructure adapter behind the exact linear-algebra, homology and "
        "holonomy ports; it is the port implementation, so it may hold the host"
    ),
    "pfp/infrastructure/adapters/lake_sandbox_adapter.py": (
        "infrastructure adapter behind LeanVerifierPort; executes sandboxed Lean 4 "
        "builds and axiom audits via host invoke"
    ),
    "pfp/infrastructure/adapters/rust_cohomology_adapter.py": (
        "infrastructure adapter behind CohomologySolverPort; it is the port "
        "implementation, so it may hold the host"
    ),
    "pfp/infrastructure/adapters/scoring_rust.py": (
        "infrastructure adapter behind ScoringPort; delegates scoring "
        "and prompt-frontier execution to the canonical native host"
    ),
    "pfp/infrastructure/adapters/mssn_research/sign_switching.py": (
        "native sign-gauge transport adapter; delegates complete coefficient "
        "and cycle-witness verification to the holonomy owner"
    ),
    "pfp/infrastructure/adapters/stabilizer_rust_adapter.py": (
        "infrastructure adapter behind StabilizerPort; delegates finite quantum "
        "stabilizer solving to native Rust host"
    ),
}

# Modules permitted to call raw exec() or eval(). Shrink-only ratchet.
EXEC_CALLER_ALLOWLIST: dict[str, str] = {
    "pfp/infrastructure/adapters/mssn_research/loader.py": (
        "loads internally pinned research checker modules from SHA-256 authenticated resources"
    ),
    "pfp/infrastructure/tower_research/reach/targets.py": (
        "loads internally pinned tower checker modules from SHA-256 authenticated resources"
    ),
}

# Exact existing composition sites, not whole-module constructor exemptions.
# Trace factories own fixture confinement. The accounted factory owns explicit
# OpenRouter financial policy and continuing run budgets; it is not a fixture API.
GATEWAY_FACTORY_MODULE = "pfp/infrastructure/trace/gateway_factories.py"
ACCOUNTED_GATEWAY_FACTORY_MODULE = "pfp/infrastructure/estimated_gateway.py"
GATEWAY_CONSTRUCTION_SITES = {
    GATEWAY_FACTORY_MODULE: (("_confined_gateway", "OearsLlmGateway"),),
    ACCOUNTED_GATEWAY_FACTORY_MODULE: (
        ("create_accounted_openrouter_gateway", "OearsLlmGateway.builtin"),
        ("create_accounted_openrouter_gateway", "unbudgeted_gateway"),
    ),
}
RAW_GATEWAY_NAME = "OearsLlmGateway"
RAW_GATEWAY_MODULES = (
    "adversary.infrastructure.providers.gateway",
    "adversary.infrastructure.providers.gateway",
)


class FitnessError(RuntimeError):
    """A typed refusal naming what the analyzer would not do."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class Offence:
    """One module importing something its layer may not."""

    module: str
    imports: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.module:
            raise FitnessError("BAD_OFFENCE", "an offence needs a module path")
        if not self.imports:
            raise FitnessError(
                "EMPTY_OFFENCE",
                f"{self.module} is recorded with no forbidden import; an empty "
                f"offence matches everything and would read as agreeing",
            )


def imported_names(source: str) -> tuple[str, ...]:
    """Every module name a source file imports, from the AST.

    Over the AST rather than by text search, so a doc comment naming a module is
    not an import. That distinction is not hypothetical: a text scan of this
    package reports two `domain/` modules as native importers, and both merely
    describe in prose what they mirror.
    """
    tree = ast.parse(source)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                names.append(node.module)
            # ``from package import ffi`` imports the seam module just as
            # ``from package.ffi import Host`` does. Keep that spelling visible
            # to the confinement gate without treating every imported symbol
            # as a module.
            for alias in node.names:
                if alias.name == "ffi":
                    names.append(f"{node.module}.ffi" if node.module else "ffi")
    return tuple(names)


def _is_forbidden(name: str) -> bool:
    root = name.split(".")[0]
    return root in FORBIDDEN_IN_DOMAIN or any(
        marker in name for marker in NATIVE_MARKERS
    )


def domain_offences(repo_root: Path) -> tuple[Offence, ...]:
    """Every `domain/` module importing the filesystem, a process, or the
    extension."""
    root = repo_root / DOMAIN
    if not root.is_dir():
        raise FitnessError("DOMAIN_ABSENT", f"no domain layer at {DOMAIN}")
    offences: list[Offence] = []
    scanned = 0
    for path in sorted(root.rglob("*.py")):
        scanned += 1
        forbidden = tuple(
            sorted(
                {
                    name
                    for name in imported_names(path.read_text(encoding="utf-8"))
                    if _is_forbidden(name)
                }
            )
        )
        if forbidden:
            offences.append(
                Offence(
                    module=str(path.relative_to(repo_root)).replace("\\", "/"),
                    imports=forbidden,
                )
            )
    if scanned == 0:
        raise FitnessError(
            "DOMAIN_EMPTY", "no domain modules found; refusing to report 0 of 0"
        )
    return tuple(offences)


def domain_module_count(repo_root: Path) -> int:
    return len(list((repo_root / DOMAIN).rglob("*.py")))


def seam_importers(repo_root: Path) -> tuple[str, ...]:
    """Non-test modules importing the FFI seam.

    Criterion 1 wants exactly one import site. Tests are excluded because a test
    that exercises the seam is not a second place *deciding* how to reach it --
    which is what `RULE_FFI_SEAM_ISOLATION_001` is about.
    """
    root = repo_root / PACKAGE
    if not root.is_dir():
        raise FitnessError("PACKAGE_ABSENT", f"no package at {PACKAGE}")
    importers: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if "tests" in path.parts:
            continue
        names = imported_names(path.read_text(encoding="utf-8"))
        if any(
            name.endswith("pfp.ffi")
            or name == "ffi"
            or name.endswith(".ffi")
            or any(marker in name for marker in NATIVE_MARKERS)
            for name in names
        ):
            importers.append(str(path.relative_to(repo_root)).replace("\\", "/"))
    return tuple(importers)


def seam_violations(
    importers: tuple[str, ...], allowlist: dict[str, str] | None = None
) -> tuple[str, ...]:
    """Compare seam importers to `ffi.py` plus the explicit allowlist.

    Empty means it holds. Like the domain ratchet, it is identity-keyed and
    shrink-only: an importer that is neither `ffi.py` nor listed fails, and a
    listed module that no longer imports the seam fails until it is removed.
    """
    allowed = SEAM_IMPORT_ALLOWLIST if allowlist is None else allowlist
    seam = str(SEAM_MODULE).replace("\\", "/")
    problems: list[str] = []
    if seam not in importers:
        problems.append(f"{seam}: the seam module no longer reaches the native host")
    for module in importers:
        if module != seam and module not in allowed:
            problems.append(f"{module}: new seam import site outside the allowlist")
    for module in sorted(allowed):
        if module not in importers:
            problems.append(
                f"{module}: no longer imports the seam; remove its allowlist entry"
            )
    return tuple(problems)


def _gateway_construction_sites(tree: ast.AST) -> tuple[tuple[str, str], ...]:
    """Static constructor calls and lexical owners, including import aliases.

    Conservative import bindings survive later rebindings. This is a source
    drift check, not Python data-flow analysis or an arbitrary-code sandbox.
    """
    bindings: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                bindings.setdefault(name, set()).add(alias.name if alias.asname else name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bindings.setdefault(alias.asname or alias.name, set()).add(
                    f"{node.module}.{alias.name}"
                )

    def names(node: ast.AST) -> set[str]:
        if isinstance(node, ast.Name):
            return bindings.get(node.id, {node.id})
        if isinstance(node, ast.Attribute):
            return {f"{base}.{node.attr}" for base in names(node.value)}
        return set()

    sites: list[tuple[str, str]] = []

    def visit(node: ast.AST, owner: tuple[str, ...] = ()) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Defaults, decorators and class bases execute in the outer scope.
            for field, value in ast.iter_fields(node):
                children = value if isinstance(value, list) else [value]
                for child in children:
                    if isinstance(child, ast.AST):
                        visit(child, (*owner, node.name) if field == "body" else owner)
            return
        if isinstance(node, ast.Lambda):
            visit(node.args, owner)
            visit(node.body, (*owner, "<lambda>"))
            return
        if isinstance(node, ast.Call):
            constructors = set()
            for name in names(node.func):
                short = name
                for module in RAW_GATEWAY_MODULES:
                    short = short.removeprefix(module + ".")
                if (
                    short == "unbudgeted_gateway"
                    or short == RAW_GATEWAY_NAME
                    or short.startswith(RAW_GATEWAY_NAME + ".")
                ):
                    constructors.add(short)
            sites.extend((".".join(owner), name) for name in sorted(constructors))
        for child in ast.iter_child_nodes(node):
            visit(child, owner)

    visit(tree)
    return tuple(sorted(sites))


def raw_gateway_constructors(repo_root: Path) -> tuple[str, ...]:
    """Refuse unregistered raw imports and drift in both existing factories.

    Each registered module must retain exactly its reviewed construction calls
    in the named top-level functions. A new helper in that same module is not
    exempt. Runtime accounting and fixture confinement have their own tests.
    """
    root = repo_root / PACKAGE
    if not root.is_dir():
        raise FitnessError("PACKAGE_ABSENT", f"no package at {PACKAGE}")
    offenders: set[str] = set()
    seen: set[str] = set()
    for path in sorted(root.rglob("*.py")):
        if "tests" in path.relative_to(root).parts:
            continue
        relative = path.relative_to(repo_root).as_posix()
        seen.add(relative)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        sites = _gateway_construction_sites(tree)
        if relative in GATEWAY_CONSTRUCTION_SITES:
            if sites != tuple(sorted(GATEWAY_CONSTRUCTION_SITES[relative])):
                offenders.add(relative)
            continue
        imports_it = any(
            name == module or name.startswith(module + ".")
            for name in imported_names(source)
            for module in RAW_GATEWAY_MODULES
        ) or any(
            isinstance(node, ast.ImportFrom)
            and any(
                alias.name in {RAW_GATEWAY_NAME, "unbudgeted_gateway"}
                or f"{node.module}.{alias.name}" in RAW_GATEWAY_MODULES
                for alias in node.names
            )
            for node in ast.walk(tree)
        )
        if imports_it or sites:
            offenders.add(relative)
    if not seen:
        raise FitnessError("PACKAGE_EMPTY", "no modules scanned; refusing to report 0 of 0")
    offenders.update(set(GATEWAY_CONSTRUCTION_SITES) - seen)
    return tuple(sorted(offenders))


def sanctioned_gateway_factory_builds_one(repo_root: Path) -> bool:
    """Compatibility entrypoint: positive control for every reviewed constructor."""
    for relative, expected in GATEWAY_CONSTRUCTION_SITES.items():
        path = repo_root / relative
        if not path.is_file():
            raise FitnessError("FACTORY_ABSENT", f"no sanctioned gateway factory at {relative}")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if _gateway_construction_sites(tree) != tuple(sorted(expected)):
            return False
    return True


# Current dispatch owners, not a second operation registry. These source checks
# complement actual prepare/send/check/replay controls in Adversary's owning tests.
ADVERSARY_PFP_ROUTES = {
    'adversary/infrastructure/providers/adapters/graph_task_adapter.py': {
        'GraphProviderAdapter._turn': {'complete_pilot_turn'},
    },
    'adversary/infrastructure/providers/operad_pre_miner.py': {
        'call_openrouter_miner': {'_mine_turn'},
        'run_operad_pre_miner_swarm': {'_mine_turn'},
        '_mine_turn': {'complete_pilot_turn'},
    },
    'adversary/use_cases/teamwork_pfp.py': {
        'prepare_teamwork_turn': {'prepare_task_turn'},
        'validate_teamwork_observation': {'prepare_teamwork_turn', 'check_teamwork_reply'},
    },
    'adversary/infrastructure/teamwork_remote.py': {
        'RemoteTeamworkExecutor._attempt': {'prepare_teamwork_turn', 'check_teamwork_reply'},
    },
    'adversary/infrastructure/providers/llm_gateway.py': {
        'LlmGateway.complete': {'prepare_task_turn', 'check_completion'},
    },
    'adversary/infrastructure/providers/adapters/model_backends.py': {
        'OpenRouterBackend.complete_with_receipt': {'complete_pilot_turn'},
    },
    'adversary/infrastructure/dialogue/providers.py': {
        'CallableDialogueProvider.generate': {'prepare_task_turn', 'check_completion'},
        'OpenRouterDialogueProvider.generate': {'complete_task_turn'},
    },
    'adversary/infrastructure/researcher/symbol_game_dispatch.py': {
        'SymbolGameModelDispatch.send': {'prepare_task_turn', 'check_completion'},
    },
    'adversary/infrastructure/research/stage_routes.py': {
        'run_propose_for_route': {'complete_task_turn'},
    },
    'adversary/entrypoints/research/http_api.py': {
        'create_research_router.propose': {'complete_task_turn'},
        'create_research_router.candidate': {'complete_task_turn'},
    },
    'adversary/infrastructure/typed_operad.py': {
        'TypedAdversaryOperad._prepare': {'prepare_task_turn'},
        'TypedAdversaryOperad._gauge_breaker': {'_prepare', 'check_completion'},
        'TypedAdversaryOperad._defect_hunter': {'replay'},
    },
    'adversary/use_cases/multi_round_critique_service.py': {
        'MultiRoundCritiqueService.execute_critique_loop': {
            'PreparePfpTaskTurnUseCase', 'CheckPfpTaskTurnUseCase'},
    },
    'adversary/infrastructure/live_openrouter_transport.py': {
        'LiveOpenRouterSymbolGameTransport.complete': {'task_input_sha256', 'CheckPfpTaskTurnUseCase'},
    },
    'pfp/infrastructure/pilot_matrix.py': {
        'complete_pilot_turn': {'prepare_task_turn', 'check_completion'},
    },
    'pfp/infrastructure/formal_matrix.py': {'call_openrouter': {'complete_pilot_turn'}},
    'pfp/infrastructure/synthesis_matrix.py': {'call_model': {'complete_pilot_turn'}},
}

_ADVERSARY_IO_OWNERS = {
    ('adversary/infrastructure/providers/anthropic_messages.py', 'AnthropicTransport.dispatch'),
    ('adversary/infrastructure/providers/openrouter_transport.py', '_post'),
    ('adversary/infrastructure/providers/http.py', 'post_json'),
    ('adversary/infrastructure/providers/openrouter_deadline.py', 'main'),
    ('adversary/infrastructure/providers/openrouter_experiment_deadline.py', 'main'),
    ('adversary/infrastructure/providers/openai_compat.py', 'OpenAiCompatTransport._send'),
    # These GETs observe catalog, local availability or an existing generation's bill.
    ('adversary/infrastructure/providers/ollama_local.py', '_http_get_json'),
    ('adversary/infrastructure/providers/openrouter_catalog.py', 'fetch_openrouter_catalog'),
    ('adversary/infrastructure/providers/adapters/model_backends.py', 'OpenRouterBackend.fetch_generation_cost'),
}


def adversary_pfp_route_violations(repo_root: Path) -> tuple[str, ...]:
    """Detect drift in supported routes and direct model I/O outside its owners.

    This is a bounded source gate, not arbitrary Python/Rust data-flow analysis
    or an authentication sandbox. Actual reply bindings and budget enforcement
    remain in the existing runtime ports and their independent controls.
    """
    problems: set[str] = set()
    sources = {path.relative_to(repo_root).as_posix(): path for name in
        ('domain', 'use_cases', 'infrastructure', 'entrypoints', 'controllers')
        for path in (repo_root / 'adversary' / name).rglob('*.py')}
    sources.update({name: repo_root / name for name in ADVERSARY_PFP_ROUTES})
    for relative, path in sorted(sources.items()):
        if not path.is_file():
            problems.add(f'{relative}: required PFP route owner missing')
            continue
        tree = ast.parse(path.read_text(encoding='utf-8'))
        aliases: dict[str, set[str]] = {}
        def bind(name, qualified):
            aliases.setdefault(name, set()).add(qualified)
        module = relative.removesuffix('.py').split('/')
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    bind(alias.asname or alias.name.split('.')[0], alias.name if alias.asname else alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                prefix = '.'.join(module[:-node.level]) + '.' if node.level else ''
                for alias in node.names:
                    bind(alias.asname or alias.name, prefix + (node.module or '') + '.' + alias.name)
        if relative.startswith('adversary/') and any(
                name.split('.')[0] in {'openai', 'anthropic', 'requests', 'httpx'} for names in aliases.values() for name in names):
            problems.add(f'{relative}: direct SDK/HTTP client import bypasses PFP provider composition')
        if any(name.endswith('.*') and '.providers.' in name for names in aliases.values() for name in names):
            problems.add(f'{relative}: wildcard provider imports hide the reviewed I/O boundary')
        calls: dict[str, set[str]] = {}

        def visit(node, owner=()):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Defaults and decorators run in the enclosing scope.
                for item in (*node.decorator_list, *(node.args.defaults if hasattr(node, 'args') else ())):
                    visit(item, owner)
                owner = (*owner, node.name)
                calls.setdefault('.'.join(owner), set())
            if isinstance(node, ast.Call):
                raw = ast.unparse(node.func)
                head, _, tail = raw.partition('.')
                qualified = {name + ('.' + tail if tail else '') for name in aliases.get(head, {head})}
                leaves = {name.rsplit('.', 1)[-1] for name in qualified}
                calls.setdefault('.'.join(owner), set()).update(leaves)
                direct = bool(qualified & {'urllib.request.urlopen', 'urllib.request.urlretrieve',
                    'adversary.infrastructure.providers.http.post_json',
                    'adversary.infrastructure.providers.openrouter_transport.openrouter_transport',
                    'adversary.infrastructure.providers.openai_compat.OpenAiCompatTransport',
                    'adversary.infrastructure.providers.anthropic_messages.AnthropicTransport'})
                if relative.startswith('adversary/') and direct and (
                        relative, '.'.join(owner)) not in _ADVERSARY_IO_OWNERS:
                    problems.add(f'{relative}:{".".join(owner)}: direct I/O outside the reviewed transport/metadata owner')
            children = node.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else ast.iter_child_nodes(node)
            for child in children:
                visit(child, owner)

        visit(tree)
        for owner, required in ADVERSARY_PFP_ROUTES.get(relative, {}).items():
            missing = required - calls.get(owner, set())
            if missing:
                problems.add(f'{relative}:{owner}: missing PFP hooks {sorted(missing)}')
    native = repo_root / 'engine/crates_rs/core_symbol_game/src/adversary_host.rs'
    import re
    if not native.is_file() or re.search(
            r'let\s+mut\s+live_seats\s*=\s*core_adversary::pfp_gateway::PfpSeatExecutor\s*\{',
            native.read_text(encoding='utf-8')) is None:
        problems.add('core_symbol_game/adversary_host.rs: native live seats must use PfpSeatExecutor')
    return tuple(sorted(problems))


def dotenv_importers(repo_root: Path, target_pkg: Path = PACKAGE) -> tuple[str, ...]:
    """Scan non-test modules under target_pkg to verify zero imports of dotenv or load_dotenv."""
    root = repo_root / target_pkg
    if not root.is_dir():
        raise FitnessError("PACKAGE_ABSENT", f"no package at {target_pkg}")
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if "tests" in path.parts:
            continue
        relative = str(path.relative_to(repo_root)).replace("\\", "/")
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "dotenv" or alias.name.startswith("dotenv."):
                        offenders.append(relative)
            elif isinstance(node, ast.ImportFrom):
                if node.module == "dotenv" or (node.module and node.module.startswith("dotenv.")):
                    offenders.append(relative)
                elif any(alias.name == "load_dotenv" for alias in node.names):
                    offenders.append(relative)
    return tuple(sorted(set(offenders)))


def exec_callers(repo_root: Path, target_pkg: Path = PACKAGE) -> tuple[str, ...]:
    """Scan non-test modules under target_pkg to verify zero calls to raw exec() or eval()."""
    root = repo_root / target_pkg
    if not root.is_dir():
        raise FitnessError("PACKAGE_ABSENT", f"no package at {target_pkg}")
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if "tests" in path.parts:
            continue
        relative = str(path.relative_to(repo_root)).replace("\\", "/")
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                    offenders.append(relative)
    return tuple(sorted(set(offenders)))


def exec_violations(
    callers: tuple[str, ...],
    allowlist: dict[str, str] = EXEC_CALLER_ALLOWLIST,
) -> tuple[str, ...]:
    """Compare detected exec/eval callers against the shrink-only allowlist."""
    problems: list[str] = []
    seen = set(callers)
    for caller in callers:
        if caller not in allowlist:
            problems.append(f"{caller}: calls exec() or eval() outside the allowlist")
    for allowed in sorted(allowlist):
        if allowed not in seen:
            problems.append(
                f"{allowed}: no longer calls exec() or eval(); remove its allowlist entry"
            )
    return tuple(problems)


def stage_runtime_modules(repo_root: Path) -> tuple[str, ...]:
    """Modules under `packet_schemas/` that define an **implementation**.

    Criterion 5 asks that superseded implementations in the former `stages/`
    folder refuse on call. That folder held packet and receipt schemas, not
    stages, and was renamed `packet_schemas/`; the criterion follows it.
    "Implementation" means a callable: a module defining a function or a class.

    The first version of this predicate excluded `__init__.py` and counted every
    other file, which is a proxy rather than the property. It reported zero --
    correctly, but for the wrong reason, because the package marker does hold
    code: a `pathlib` import and schema-path constants. Constants are not
    an implementation, and a test asserting the marker was *empty* failed on
    them.

    Asking whether a module defines a callable is the property criterion 5 is
    about, and it reads `__init__.py` like any other module.
    """
    root = repo_root / PACKET_SCHEMAS
    if not root.is_dir():
        raise FitnessError(
            "PACKET_SCHEMAS_ABSENT", f"no packet schema directory at {PACKET_SCHEMAS}"
        )
    implementations: list[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            for node in ast.walk(tree)
        ):
            implementations.append(
                str(path.relative_to(repo_root)).replace("\\", "/")
            )
    return tuple(implementations)


# ----------------------------------------------------------------------
# The ratchet
# ----------------------------------------------------------------------


def load_baseline(path: Path) -> dict[str, tuple[str, ...]]:
    if not path.is_file():
        raise FitnessError("BASELINE_ABSENT", f"no baseline at {path}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FitnessError("BASELINE_UNREADABLE", str(exc)) from exc
    if document.get("schema") != BASELINE_SCHEMA:
        raise FitnessError("BASELINE_SCHEMA", "unsupported baseline schema")
    entries = document.get("domain_offences")
    if not isinstance(entries, list):
        raise FitnessError("BASELINE_SCHEMA", "`domain_offences` must be a list")
    baseline: dict[str, tuple[str, ...]] = {}
    for entry in entries:
        module = entry.get("module")
        if not isinstance(module, str) or not module:
            raise FitnessError("BASELINE_SCHEMA", "an entry has no module")
        if module in baseline:
            raise FitnessError("BASELINE_DUPLICATE", f"{module} is recorded twice")
        baseline[module] = tuple(entry["imports"])
    return baseline


def ratchet_violations(
    offences: tuple[Offence, ...], baseline: dict[str, tuple[str, ...]]
) -> tuple[str, ...]:
    """Compare the measured offences to the baseline. Empty means it holds.

    Three ways to violate, and the third is what makes this a ratchet rather
    than a permanent exemption list:

    1. a module offends that the baseline does not record;
    2. a recorded module acquires a **new** forbidden import;
    3. a recorded module no longer offends -- its entry must be **removed**.
    """
    problems: list[str] = []
    current = {offence.module: offence.imports for offence in offences}

    for module, imports in sorted(current.items()):
        recorded = baseline.get(module)
        if recorded is None:
            problems.append(
                f"{module}: new domain offence importing {', '.join(imports)}"
            )
            continue
        added = sorted(set(imports) - set(recorded))
        if added:
            problems.append(f"{module}: acquired {', '.join(added)}")

    for module in sorted(baseline):
        if module not in current:
            problems.append(
                f"{module}: no longer offends; remove the entry so the ratchet "
                f"cannot slip back"
            )
    return tuple(problems)


def render_baseline(offences: tuple[Offence, ...], scanned: int) -> str:
    document = {
        "schema": BASELINE_SCHEMA,
        "note": (
            "Identity-keyed, shrink-only. A new offender fails. A listed module "
            "that acquires another forbidden import fails. A listed module that "
            "has been cleaned fails until its entry is deleted. Regenerating "
            "this file to make a check pass defeats it."
        ),
        "domain_modules_scanned": scanned,
        "domain_offences": [
            {"module": offence.module, "imports": list(offence.imports)}
            for offence in offences
        ],
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def format_report(repo_root: Path) -> str:
    offences = domain_offences(repo_root)
    scanned = domain_module_count(repo_root)
    importers = seam_importers(repo_root)
    stages = stage_runtime_modules(repo_root)
    lines = [
        "=== SYMBOL GAME ARCHITECTURE FITNESS ===",
        f"domain modules scanned  : {scanned}",
        f"domain offences         : {len(offences)}",
        f"seam import sites       : {len(importers)}",
        f"schema runtime modules  : {len(stages)}",
        "",
        "seam importers:",
    ]
    lines.extend(f"  {module}" for module in importers)
    if offences:
        lines.append("")
        lines.append("domain offences:")
        for offence in offences:
            lines.append(f"  {offence.module}: {', '.join(offence.imports)}")
    return "\n".join(lines)


__all__ = [
    "BASELINE_SCHEMA",
    "FORBIDDEN_IN_DOMAIN",
    "FitnessError",
    "Offence",
    "domain_module_count",
    "domain_offences",
    "format_report",
    "imported_names",
    "load_baseline",
    "ratchet_violations",
    "ADVERSARY_PFP_ROUTES",
    "adversary_pfp_route_violations",
    "raw_gateway_constructors",
    "sanctioned_gateway_factory_builds_one",
    "render_baseline",
    "SEAM_IMPORT_ALLOWLIST",
    "seam_importers",
    "seam_violations",
    "stage_runtime_modules",
    "dotenv_importers",
    "exec_callers",
    "EXEC_CALLER_ALLOWLIST",
    "exec_violations",
]
