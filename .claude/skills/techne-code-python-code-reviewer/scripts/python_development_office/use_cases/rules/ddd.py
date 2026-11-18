"""Domain-Driven Design (DDD) domain purity and boundary rules."""

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


class DomainMustNotImportFrameworkRule(ArchitectureRule):
    """Enforces that the Domain layer contains zero framework or third-party I/O dependencies."""

    rule_id = 102
    rule_code = "DDD_DOMAIN_IMPURE"
    category = RuleCategory.DDD
    default_message = "Domain entity/model imports forbidden external framework"
    default_remediation = (
        "Keep domain model pure Python/dataclasses and move framework/ORM logic to infrastructure"
    )

    def check_project(
        self,
        modules: Sequence[ModuleInfo],
        module_graph: dict[str, ModuleInfo],
        config: ArchitectureConfig,
    ) -> list[AntipatternFinding]:
        findings: list[AntipatternFinding] = []
        forbidden = set(config.forbidden_frameworks_in_domain)

        for module in modules:
            if module.is_test or module.layer != "domain":
                continue

            for imp_symbol in module.imported_symbols:
                root_pkg = imp_symbol.module.split(".")[0].lower()
                if root_pkg in forbidden:
                    findings.append(
                        AntipatternFinding(
                            path=str(module.path),
                            line=imp_symbol.lineno,
                            column=0,
                            rule_id=self.rule_id,
                            rule_code=self.rule_code,
                            category=self.category.value,
                            message=(
                                f"Domain module '{module.package}' imports forbidden framework '{root_pkg}' "
                                f"via '{imp_symbol.module}'"
                            ),
                            remediation=(
                                f"Domain layer must remain technology-agnostic. Move '{root_pkg}' usage "
                                f"to an infrastructure adapter or repository."
                            ),
                            severity="error",
                        )
                    )

        return findings
