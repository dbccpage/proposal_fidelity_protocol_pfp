"""Unit tests for Clean Architecture, DDD, and MVC architecture rules."""

from __future__ import annotations

import unittest
from pathlib import Path

from operads.application.python_development_office.project import (
    ProjectScanner,
)
from operads.application.python_development_office.rules.clean_arch import (
    CleanArchitectureDependencyRule,
)
from operads.application.python_development_office.rules.ddd import (
    DomainMustNotImportFrameworkRule,
)
from operads.application.python_development_office.rules.mvc import (
    ThinControllerRule,
    ViewDoesNotImportOrmRule,
)
from operads.domain.python_development_office import (
    ArchitectureConfig,
    DependencyException,
    ImportedSymbol,
    ModuleInfo,
)
from operads.infrastructure.python_development_office.config import (
    load_config,
)
from operads.infrastructure.python_development_office.source_repository import (
    FileSystemSourceRepository,
)


class TestArchitectureRules(unittest.TestCase):
    def setUp(self) -> None:
        self.config = ArchitectureConfig()

    def test_clean_architecture_inversion_detected(self) -> None:
        domain_mod = ModuleInfo(
            path="src/domain/entities.py",
            package="src.domain.entities",
            layer="domain",
            imports={"src.infrastructure.db_repo"},
            imported_symbols=[
                ImportedSymbol(
                    module="src.infrastructure.db_repo",
                    name="SqlRepository",
                    alias=None,
                    lineno=5,
                )
            ],
        )
        infra_mod = ModuleInfo(
            path="src/infrastructure/db_repo.py",
            package="src.infrastructure.db_repo",
            layer="infrastructure",
            imports=set(),
            imported_symbols=[],
        )

        rule = CleanArchitectureDependencyRule()
        graph = {domain_mod.package: domain_mod, infra_mod.package: infra_mod}
        findings = rule.check_project([domain_mod, infra_mod], graph, self.config)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_code, "CLEAN_DEPENDENCY_INVERSION")
        self.assertIn("Layer 'domain'", findings[0].message)

    def test_clean_architecture_exception_is_exact_and_rationale_bearing(self) -> None:
        consumer_name = "example.use_cases.search"
        provider_name = "example.infrastructure.external_search"
        config = ArchitectureConfig(
            dependency_exceptions=(
                DependencyException(
                    consumer=consumer_name,
                    provider=provider_name,
                    rationale="Temporary concrete adapter pending an injected port.",
                    owner="python-development-office",
                ),
            )
        )
        consumer = ModuleInfo(
            path="example/use_cases/search.py",
            package=consumer_name,
            layer="use_cases",
            imports={provider_name},
            imported_symbols=[
                ImportedSymbol(
                    module=provider_name,
                    name="search",
                    alias=None,
                    lineno=5,
                )
            ],
        )
        provider = ModuleInfo(
            path="example/infrastructure/external_search.py",
            package=provider_name,
            layer="infrastructure",
            imports=set(),
            imported_symbols=[],
        )
        rule = CleanArchitectureDependencyRule()
        graph = {consumer.package: consumer, provider.package: provider}

        self.assertEqual(rule.check_project([consumer, provider], graph, config), [])

        near_miss = ModuleInfo(
            path=consumer.path,
            package=consumer.package,
            layer=consumer.layer,
            imports={f"{provider_name}.other"},
            imported_symbols=[
                ImportedSymbol(
                    module=f"{provider_name}.other",
                    name="search",
                    alias=None,
                    lineno=5,
                )
            ],
        )
        findings = rule.check_project([near_miss, provider], graph, config)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_code, "CLEAN_DEPENDENCY_INVERSION")

    def test_dependency_exception_requires_complete_unique_debt_records(self) -> None:
        with self.assertRaisesRegex(ValueError, "rationale"):
            DependencyException(
                consumer="example.use_cases.search",
                provider="example.infrastructure.search",
                rationale=" ",
                owner="python-development-office",
            )

        exception = DependencyException(
            consumer="example.use_cases.search",
            provider="example.infrastructure.search",
            rationale="Temporary direct adapter dependency.",
            owner="python-development-office",
        )
        with self.assertRaisesRegex(ValueError, "unique consumer/provider"):
            ArchitectureConfig(dependency_exceptions=(exception, exception))

    def test_config_loader_parses_exact_dependency_exception_records(
        self,
    ) -> None:
        import json
        import tempfile

        record = {
            "consumer": "example.use_cases.search",
            "provider": "example.infrastructure.search",
            "rationale": "Temporary direct adapter dependency.",
            "owner": "python-development-office",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "architecture.json"
            config_path.write_text(
                json.dumps({"dependency_exceptions": [record]}),
                encoding="utf-8",
            )
            loaded = load_config(config_path)

        self.assertEqual(
            loaded.dependency_exceptions,
            (DependencyException(**record),),
        )

    def test_explicit_malformed_config_refuses_instead_of_loading_defaults(
        self,
    ) -> None:
        import tempfile

        malformed_payloads = (
            "{not json",
            '{"dependency_exceptions": [{"consumer": "only-one-field"}]}',
            (
                '{"dependency_exceptions": [{"consumer": "c", '
                '"provider": "p", "rationale": "", "owner": "o"}]}'
            ),
            (
                '{"dependency_exceptions": ['
                '{"consumer": "c", "provider": "p", "rationale": "r", '
                '"owner": "o"}, '
                '{"consumer": "c", "provider": "p", "rationale": "r2", '
                '"owner": "o2"}]}'
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            for index, payload in enumerate(malformed_payloads):
                config_path = Path(temp_dir) / f"invalid-{index}.json"
                config_path.write_text(payload, encoding="utf-8")
                with self.subTest(payload=payload):
                    with self.assertRaisesRegex(ValueError, "invalid architecture config"):
                        load_config(config_path)

    def test_production_tree_has_no_unregistered_clean_architecture_edges(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        scanner = ProjectScanner(
            ArchitectureConfig(),
            project_root=repository_root,
            sources=FileSystemSourceRepository(),
        )
        targets = ["operations"]
        relocated = {
            "operads": (
                "domain/python_development_office", "application/python_development_office",
                "infrastructure/python_development_office", "controllers/python_development_office_controller.py",
                "frontend/cli/python_dev_cli.py", "domain/autopoiesis", "application/autopoiesis",
                "infrastructure/autopoiesis", "domain/skill_garden", "application/skill_garden",
                "infrastructure/skill_garden", "domain/ddc_execution", "application/ddc_execution",
                "infrastructure/ddc_execution", "application/queries/validate_workflows.py",
                "infrastructure/bootstrap.py",
            ),
            "governance": (
                "domain/actor_corpus", "use_cases/actor_corpus", "infrastructure/actor_corpus",
            ),
            "pciv": (
                "domain/intelligence_metabolism", "use_cases/intelligence_metabolism",
                "infrastructure/intelligence_metabolism",
            ),
            "adversary": (
                "domain/residual_algebra", "use_cases/scenes", "use_cases/research_swarm",
                "infrastructure/dialogue", "infrastructure/scenes", "infrastructure/research_swarm",
            ),
        }
        for package, paths in relocated.items():
            for path in paths:
                target = f"{package}/{path}"
                self.assertTrue((repository_root / target).exists(), target)
                targets.append(target)
        result = scanner.scan(targets, arch_only=True)
        unregistered = [
            finding
            for finding in result.findings
            if finding.rule_code == "CLEAN_DEPENDENCY_INVERSION"
        ]
        self.assertEqual(unregistered, [])
        live_import_pairs = {
            (module.package, imported.module)
            for module in scanner.modules
            if not module.is_test
            for imported in module.imported_symbols
        }
        registered_pairs = {
            (exception.consumer, exception.provider)
            for exception in scanner.config.dependency_exceptions
        }
        self.assertEqual(registered_pairs - live_import_pairs, set())

    def test_ddd_domain_purity_detected(self) -> None:
        domain_mod = ModuleInfo(
            path="src/domain/user.py",
            package="src.domain.user",
            layer="domain",
            imports={"sqlalchemy.orm"},
            imported_symbols=[
                ImportedSymbol(
                    module="sqlalchemy.orm",
                    name="declarative_base",
                    alias=None,
                    lineno=3,
                )
            ],
        )

        rule = DomainMustNotImportFrameworkRule()
        graph = {domain_mod.package: domain_mod}
        findings = rule.check_project([domain_mod], graph, self.config)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_code, "DDD_DOMAIN_IMPURE")
        self.assertIn("sqlalchemy", findings[0].message)

    def test_mvc_fat_controller_detected(self) -> None:
        controller_mod = ModuleInfo(
            path="src/controllers/order_controller.py",
            package="src.controllers.order_controller",
            layer="presentation",
            imports=set(),
            imported_symbols=[],
            loc=650,
        )

        rule = ThinControllerRule()
        graph = {controller_mod.package: controller_mod}
        findings = rule.check_project([controller_mod], graph, self.config)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_code, "MVC_FAT_CONTROLLER")

    def test_mvc_view_direct_orm_detected(self) -> None:
        view_mod = ModuleInfo(
            path="src/views/order_view.py",
            package="src.views.order_view",
            layer="presentation",
            imports={"sqlalchemy"},
            imported_symbols=[
                ImportedSymbol(
                    module="sqlalchemy",
                    name="select",
                    alias=None,
                    lineno=4,
                )
            ],
        )

        rule = ViewDoesNotImportOrmRule()
        graph = {view_mod.package: view_mod}
        findings = rule.check_project([view_mod], graph, self.config)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_code, "MVC_VIEW_DIRECT_ORM")


if __name__ == "__main__":
    unittest.main()
