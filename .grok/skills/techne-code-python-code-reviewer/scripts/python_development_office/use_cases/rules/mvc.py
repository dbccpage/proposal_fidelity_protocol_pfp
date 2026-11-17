"""Model-View-Controller (MVC) architecture and boundary rules."""

from __future__ import annotations

from typing import Sequence

from python_development_office.domain import (
    AntipatternFinding,
    ArchitectureConfig,
    ModuleInfo,
    RuleCategory,
)
from python_development_office.use_cases.rules.base import (
    ArchitectureRule,
)


class ThinControllerRule(ArchitectureRule):
    """Enforces thin controllers in MVC / Web presentation layers."""

    rule_id = 201
    rule_code = "MVC_FAT_CONTROLLER"
    category = RuleCategory.MVC
    default_message = "Controller exceeds lines-of-code threshold (Fat Controller)"
    default_remediation = (
        "Refactor business and persistence logic out of controller into use case services"
    )

    def check_project(
        self,
        modules: Sequence[ModuleInfo],
        module_graph: dict[str, ModuleInfo],
        config: ArchitectureConfig,
    ) -> list[AntipatternFinding]:
        findings: list[AntipatternFinding] = []

        for module in modules:
            if module.is_test:
                continue

            is_controller = (
                "controller" in module.package.lower() or "controllers" in module.path.parts
            )
            if is_controller and module.loc > config.max_controller_loc:
                findings.append(
                    AntipatternFinding(
                        path=str(module.path),
                        line=1,
                        column=0,
                        rule_id=self.rule_id,
                        rule_code=self.rule_code,
                        category=self.category.value,
                        message=(
                            f"Controller module '{module.package}' is {module.loc} lines long "
                            f"(exceeds maximum {config.max_controller_loc} LOC)"
                        ),
                        remediation=(
                            "Extract business validation, domain orchestration, and queries "
                            "into dedicated use case / service interactors."
                        ),
                        severity="warning",
                    )
                )

        return findings


class ViewDoesNotImportOrmRule(ArchitectureRule):
    """Enforces that Views and templates do not directly access ORM/database entities."""

    rule_id = 202
    rule_code = "MVC_VIEW_DIRECT_ORM"
    category = RuleCategory.MVC
    default_message = "View module directly imports database or ORM infrastructure"
    default_remediation = "Pass view models / DTOs from controller to view"

    def check_project(
        self,
        modules: Sequence[ModuleInfo],
        module_graph: dict[str, ModuleInfo],
        config: ArchitectureConfig,
    ) -> list[AntipatternFinding]:
        findings: list[AntipatternFinding] = []
        orm_packages = {
            "sqlalchemy",
            "django.db",
            "tortoise",
            "peewee",
            "pony",
            "psycopg2",
        }

        for module in modules:
            if module.is_test:
                continue

            is_view = "view" in module.package.lower() or "views" in module.path.parts
            if not is_view:
                continue

            for imp_symbol in module.imported_symbols:
                for orm in orm_packages:
                    if imp_symbol.module.startswith(orm):
                        findings.append(
                            AntipatternFinding(
                                path=str(module.path),
                                line=imp_symbol.lineno,
                                column=0,
                                rule_id=self.rule_id,
                                rule_code=self.rule_code,
                                category=self.category.value,
                                message=f"View module '{module.package}' directly imports ORM '{imp_symbol.module}'",
                                remediation="Views must only consume presentation DTOs or ViewModels.",
                                severity="error",
                            )
                        )

        return findings
