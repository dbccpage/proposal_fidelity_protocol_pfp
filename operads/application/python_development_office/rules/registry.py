"""Central registry for AST and Architecture rules."""

from __future__ import annotations

from omega_engine_operads.application.python_development_office.rules.base import (
    ArchitectureRule,
    AstRule,
    BaseRule,
)


class RuleRegistry:
    """Registry maintaining active AST and Architecture rules."""

    def __init__(self) -> None:
        self._ast_rules: list[AstRule] = []
        self._arch_rules: list[ArchitectureRule] = []

    def register(self, rule: BaseRule) -> None:
        if isinstance(rule, AstRule):
            self._ast_rules.append(rule)
        elif isinstance(rule, ArchitectureRule):
            self._arch_rules.append(rule)

    @property
    def ast_rules(self) -> tuple[AstRule, ...]:
        return tuple(self._ast_rules)

    @property
    def architecture_rules(self) -> tuple[ArchitectureRule, ...]:
        return tuple(self._arch_rules)

    @classmethod
    def create_default(cls) -> RuleRegistry:
        """Instantiate registry populated with all standard pitfall and architecture rules."""
        from omega_engine_operads.application.python_development_office.rules.clean_arch import (
            CleanArchitectureDependencyRule,
        )
        from omega_engine_operads.application.python_development_office.rules.ddd import (
            DomainMustNotImportFrameworkRule,
        )
        from omega_engine_operads.application.python_development_office.rules.mvc import (
            ThinControllerRule,
        )
        from omega_engine_operads.application.python_development_office.rules.python_pitfalls import (
            ALL_PITFALL_RULES,
        )

        reg = cls()
        for rule_cls in ALL_PITFALL_RULES:
            reg.register(rule_cls())

        reg.register(CleanArchitectureDependencyRule())
        reg.register(DomainMustNotImportFrameworkRule())
        reg.register(ThinControllerRule())

        return reg
