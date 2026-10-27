"""ArchitectureConfig domain entity for python_development_office."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DependencyException:
    """Exact, reviewable architecture debt; never a layer-wide allowance."""

    consumer: str
    provider: str
    rationale: str
    owner: str

    def __post_init__(self) -> None:
        for field_name in ("consumer", "provider", "rationale", "owner"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"DependencyException.{field_name} must be a non-empty string")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, DependencyException)
        return (
            self.consumer == other.consumer
            and self.provider == other.provider
            and self.rationale == other.rationale
            and self.owner == other.owner
        )

    def __hash__(self) -> int:
        return hash((type(self), self.consumer, self.provider, self.rationale, self.owner))


@dataclass(frozen=True)
class ArchitectureConfig:
    source_roots: tuple[str, ...] = (
        "operations",
        "engine",
        "governance",
        "src",
        "app",
    )
    layers: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "domain": ("domain", "entities", "models", "contracts"),
            "use_cases": ("use_cases", "application", "services", "interactors"),
            "infrastructure": (
                "infrastructure",
                "adapters",
                "storage",
                "persistence",
                "gateways",
            ),
            "presentation": (
                "frontend",
                "controllers",
                "views",
                "entrypoints",
                "cli",
                "web",
                "api",
            ),
        }
    )
    allowed_dependencies: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "presentation": ("use_cases", "domain", "infrastructure"),
            "infrastructure": ("use_cases", "domain"),
            "use_cases": ("domain",),
            "domain": (),
        }
    )
    dependency_exceptions: tuple[DependencyException, ...] = field(
        default_factory=lambda: (
            DependencyException(
                consumer=("operations.use_cases.verification.system_red_team.probes"),
                provider="operating_system.adapters",
                rationale=(
                    "Adversarial verification probe suite directly instantiates "
                    "in-memory foreign subsystem fixtures (adapters) to execute "
                    "security penetration tests."
                ),
                owner="python-development-office",
            ),
            DependencyException(
                consumer=("operations.use_cases.verification.system_red_team.probes"),
                provider="operating_system.entrypoints.api",
                rationale=(
                    "Adversarial verification probe suite directly instantiates "
                    "in-memory foreign subsystem API entrypoints to execute "
                    "security penetration tests."
                ),
                owner="python-development-office",
            ),
            DependencyException(
                consumer=("operations.use_cases.verification.system_red_team.probes"),
                provider="operating_system.infrastructure",
                rationale=(
                    "Adversarial verification probe suite directly instantiates "
                    "in-memory foreign subsystem task store infrastructure to execute "
                    "security penetration tests."
                ),
                owner="python-development-office",
            ),
            DependencyException(
                consumer=("operations.use_cases.verification.system_red_team.probes"),
                provider="operads.infrastructure.bootstrap",
                rationale=(
                    "Adversarial verification probe suite directly instantiates "
                    "in-memory OEWAS container infrastructure to execute "
                    "security penetration tests."
                ),
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.cicd.ddc_tape_native",
                provider="operating_system.adapters.rust_host.ffi",
                rationale="Native DDC tape runner delegates to OS FFI adapter.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.cicd.theory_fixture_suite",
                provider="operating_system.adapters.rust_host.ffi",
                rationale="Theory fixture suite delegates to OS FFI adapter.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.cicd.education_strands_gate",
                provider="education.education_app.infrastructure.strands.strand_verifier_adapter",
                rationale="CI/CD education strands gate instantiates the education strand verifier adapter.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.bind",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine bind use case consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.bootstrap",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine bootstrap consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.freeze",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine freeze consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.gate",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine gate consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.inject",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine inject consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.lean_audit",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine lean audit consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.lean_build",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine lean build consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.lean_gen",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine lean gen consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.lift_check",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine lift check consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.preflight_draft",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine preflight draft consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.reach_ledger_check",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine reach ledger check consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.reach_replay",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine reach replay consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.research_engine.components",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Research engine components consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.research_engine.hygiene",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Research engine hygiene consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.research_engine.ladder_cert",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Research engine ladder cert consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.research_engine.level",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Research engine level consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.research_engine.sealed",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Research engine sealed consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operations.use_cases.level_engine.vendor",
                provider="pfp.infrastructure.tower_research.level_engine.context",
                rationale="Level engine vendor consumes symbol game context infrastructure.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operads.application.queries.validate_workflows",
                provider="operating_system.adapters.rust_host.ffi",
                rationale="Workflow graph validation query delegates to the sovereign OS FFI adapter.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operads.infrastructure.bootstrap",
                provider="controllers.python_facade",
                rationale="OEWAS composition root container wires Python facade controller.",
                owner="python-development-office",
            ),
            DependencyException(
                consumer="operads.infrastructure.bootstrap",
                provider="controllers.router",
                rationale="OEWAS composition root container wires FastAPI router controller on demand.",
                owner="python-development-office",
            ),
        )
    )

    forbidden_frameworks_in_domain: tuple[str, ...] = (
        "fastapi",
        "flask",
        "django",
        "sqlalchemy",
        "requests",
        "httpx",
        "aiohttp",
        "click",
        "typer",
    )
    test_file_patterns: tuple[str, ...] = ("test_*.py", "*_test.py", "tests/**")
    max_controller_loc: int = 400

    def __post_init__(self) -> None:
        pairs = [
            (exception.consumer, exception.provider) for exception in self.dependency_exceptions
        ]
        if len(pairs) != len(set(pairs)):
            raise ValueError("dependency_exceptions must contain unique consumer/provider pairs")
