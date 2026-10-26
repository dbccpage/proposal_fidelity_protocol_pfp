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


@dataclass(frozen=True)
class ArchitectureConfig:
    # Retargeted for CODA. Upstream listed omega_engine_operations,
    # omega_engine and omega_engine_governance; none of those exist here.
    source_roots: tuple[str, ...] = (
        "src",
        "app",
        "scripts",
        "ci",
        "coda_atlas",
        "omega_engine_operations",
    )
    layers: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "domain": ("domain", "entities", "models", "contracts"),
            "use_cases": ("use_cases", "services", "interactors"),
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
    # Empty by default in CODA. Upstream shipped four entries, each naming an
    # omega_engine_operations module pair that does not exist in this tree —
    # carrying them would be a debt register describing a different repository.
    # Add entries here (or via --config) as real debt is found, one exact
    # consumer/provider pair at a time. A layer-wide allowance is not an
    # exception; DependencyException refuses empty fields for that reason.
    dependency_exceptions: tuple[DependencyException, ...] = ()
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
