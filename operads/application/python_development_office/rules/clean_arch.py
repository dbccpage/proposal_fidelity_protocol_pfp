"""Clean Architecture dependency inversion and boundary rules."""

from __future__ import annotations

from typing import Sequence

from omega_engine_operads.application.python_development_office.rules.base import (
    ArchitectureRule,
)
from omega_engine_operads.domain.python_development_office import (
    AntipatternFinding,
    ArchitectureConfig,
    ModuleInfo,
    RuleCategory,
)


class CleanArchitectureDependencyRule(ArchitectureRule):
    """Enforces inward dependency direction (Clean Architecture Dependency Inversion)."""

    rule_id = 101
    rule_code = "CLEAN_DEPENDENCY_INVERSION"
    category = RuleCategory.CLEAN_ARCH
    default_message = "Clean Architecture layer dependency violation"
    default_remediation = (
        "Invert dependency using interfaces/abstract ports so outer layers depend on inner layers"
    )

    def check_project(
        self,
        modules: Sequence[ModuleInfo],
        module_graph: dict[str, ModuleInfo],
        config: ArchitectureConfig,
    ) -> list[AntipatternFinding]:
        findings: list[AntipatternFinding] = []
        allowed = config.allowed_dependencies
        registered_exceptions = {
            (exception.consumer, exception.provider) for exception in config.dependency_exceptions
        }

        for module in modules:
            if module.is_test or not module.layer:
                continue

            allowed_targets = set(allowed.get(module.layer, ()))
            seen_provider_modules: set[str] = set()

            for imp_symbol in module.imported_symbols:
                if imp_symbol.module in seen_provider_modules:
                    continue
                seen_provider_modules.add(imp_symbol.module)
                target_mod = module_graph.get(imp_symbol.module)
                if not target_mod or not target_mod.layer:
                    target_layer = self._resolve_layer(imp_symbol.module, config)
                else:
                    target_layer = target_mod.layer

                if target_layer is None or target_layer == module.layer:
                    continue

                if (module.package, imp_symbol.module) in registered_exceptions:
                    continue

                if target_layer not in allowed_targets:
                    findings.append(
                        AntipatternFinding(
                            path=str(module.path),
                            line=imp_symbol.lineno,
                            column=0,
                            rule_id=self.rule_id,
                            rule_code=self.rule_code,
                            category=self.category.value,
                            message=(
                                f"Layer '{module.layer}' ({module.package}) illegally imports "
                                f"outer layer '{target_layer}' ({imp_symbol.module})"
                            ),
                            remediation=(
                                f"Layer '{module.layer}' can only import layers {sorted(allowed_targets)}. "
                                f"Define an abstract boundary/interface in '{module.layer}' instead."
                            ),
                            severity="error",
                        )
                    )

        return findings

    def _resolve_layer(self, module_name: str, config: ArchitectureConfig) -> str | None:
        parts = module_name.split(".")
        for layer_name, patterns in config.layers.items():
            for pattern in patterns:
                if pattern in parts:
                    return layer_name
        return None
