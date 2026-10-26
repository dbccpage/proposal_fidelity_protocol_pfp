"""Decomposed 50 canonical Python pitfall rules implemented as modular AstRules."""

from __future__ import annotations

import ast

from python_development_office.use_cases.ast_utils import (
    get_decorator_names,
    has_len_call_in_args,
)
from python_development_office.use_cases.rules.base import (
    AstRule,
    RuleContext,
)

BUILTIN_SHADOW_NAMES = frozenset(
    {
        "list",
        "dict",
        "str",
        "sum",
        "max",
        "min",
        "int",
        "len",
        "type",
        "set",
        "map",
        "filter",
        "id",
        "all",
        "any",
        "input",
        "open",
        "range",
        "dir",
        "bytes",
        "tuple",
        "bool",
        "float",
        "format",
    }
)

MUTATING_METHODS = frozenset(
    {"sort", "reverse", "append", "extend", "insert", "pop", "remove", "clear"}
)


# --- 1. Arguments & Mutation ---


class MutableDefaultRule(AstRule):
    rule_id = 1
    rule_code = "MUTABLE_DEFAULT_ARG"
    default_message = "Mutable default argument in function declaration"
    default_remediation = (
        "Use None as default and initialize inside function (e.g. `items = items or []`)"
    )

    def check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, context: RuleContext
    ) -> None:
        all_defaults = list(node.args.defaults) + list(node.args.kw_defaults)
        for default in all_defaults:
            if default is None:
                continue
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                context.make_finding(
                    default,
                    self,
                    f"Mutable literal default argument in function '{node.name}'",
                )
            elif isinstance(default, ast.Call) and isinstance(default.func, ast.Name):
                if default.func.id in ("list", "dict", "set"):
                    context.make_finding(
                        default,
                        self,
                        f"Mutable constructor default argument in function '{node.name}'",
                    )


class MutatingMethodAssignmentRule(AstRule):
    rule_id = 17
    rule_code = "MUTATING_METHOD_ASSIGNMENT"
    default_message = "Assigning return value of in-place mutating method (returns None)"
    default_remediation = (
        "Call method without assignment or use non-mutating alternative (e.g. sorted())"
    )

    def check_assign(self, node: ast.Assign, context: RuleContext) -> None:
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
            if node.value.func.attr in MUTATING_METHODS:
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and isinstance(node.value.func.value, ast.Name)
                        and target.id == node.value.func.value.id
                    ):
                        context.make_finding(
                            node,
                            self,
                            f"Assigning return value of mutating method '{node.value.func.attr}()' on '{target.id}'",
                        )


class ListConcatAugAssignRule(AstRule):
    rule_id = 16
    rule_code = "LIST_CONCAT_AUGASSIGN"
    default_message = "List concatenation via `+= [item]` allocates unnecessary intermediate list"
    default_remediation = "Use `.append(item)` or `.extend(...)` instead"

    def check_aug_assign(self, node: ast.AugAssign, context: RuleContext) -> None:
        if isinstance(node.op, ast.Add) and isinstance(node.value, ast.List):
            context.make_finding(node, self)


class ChainedAssignmentRule(AstRule):
    rule_id = 32
    rule_code = "MUTABLE_CHAIN_ASSIGNMENT"
    default_message = "Chained assignment of mutable collection shares identical reference"
    default_remediation = "Initialize targets separately or use `.copy()`"

    def check_assign(self, node: ast.Assign, context: RuleContext) -> None:
        if len(node.targets) > 1 and isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
            context.make_finding(node, self)


class MutableClassAttributeRule(AstRule):
    rule_id = 34
    rule_code = "MUTABLE_CLASS_ATTRIBUTE"
    default_message = "Mutable class attribute declared in class body"
    default_remediation = "Initialize mutable collection inside `__init__()` on self"

    def check_class(self, node: ast.ClassDef, context: RuleContext) -> None:
        for item in node.body:
            if isinstance(item, ast.Assign) and isinstance(
                item.value, (ast.List, ast.Dict, ast.Set)
            ):
                context.make_finding(item, self, f"Mutable class attribute in class '{node.name}'")


# --- 2. Identity, Equality & Types ---


class LiteralIdentityRule(AstRule):
    rule_id = 2
    rule_code = "IS_WITH_LITERAL"
    default_message = "Identity comparison ('is') used with literal value"
    default_remediation = "Use equality operator '==' or '!=' instead of 'is'"

    def check_compare(self, node: ast.Compare, context: RuleContext) -> None:
        for op, right in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Is, ast.IsNot)):
                for side in (node.left, right):
                    if isinstance(side, ast.Constant):
                        if isinstance(side.value, bool):
                            context.make_finding(
                                node,
                                ExplicitBooleanComparisonRule(),
                                f"Identity comparison with boolean constant {side.value}",
                                "Use truthiness check `if flag:` directly",
                            )
                        elif isinstance(side.value, (int, str, bytes, float)):
                            context.make_finding(
                                node,
                                self,
                                f"Identity comparison ('is') used with literal value {side.value!r}",
                            )


class NoneEqualityRule(AstRule):
    rule_id = 7
    rule_code = "EQUALITY_WITH_NONE"
    default_message = "Comparison '== None' used instead of identity check"
    default_remediation = "Use `is None` or `is not None` for None comparisons"

    def check_compare(self, node: ast.Compare, context: RuleContext) -> None:
        for op, right in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Eq, ast.NotEq)):
                for side in (node.left, right):
                    if isinstance(side, ast.Constant) and side.value is None:
                        op_str = "==" if isinstance(op, ast.Eq) else "!="
                        rec_str = "is None" if isinstance(op, ast.Eq) else "is not None"
                        context.make_finding(
                            node,
                            self,
                            f"Comparison '{op_str} None' used instead of identity check",
                            f"Use `{rec_str}` for None comparisons",
                        )


class ExplicitBooleanComparisonRule(AstRule):
    rule_id = 38
    rule_code = "EXPLICIT_BOOLEAN_COMPARISON"
    default_message = "Comparison with boolean constant is redundant"
    default_remediation = "Use `if x:` or `if not x:` directly"

    def check_compare(self, node: ast.Compare, context: RuleContext) -> None:
        for op, right in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Eq, ast.NotEq)):
                for side in (node.left, right):
                    if isinstance(side, ast.Constant) and isinstance(side.value, bool):
                        context.make_finding(
                            node,
                            self,
                            f"Comparison '== {side.value}' is redundant",
                            "Use `if x:` or `if not x:` directly",
                        )


class TypeCheckRule(AstRule):
    rule_id = 9
    rule_code = "TYPE_EQUALITY_CHECK"
    default_message = "Exact `type(x) == T` used instead of `isinstance()`"
    default_remediation = "Use `isinstance(x, T)` to support polymorphism and subclasses"

    def check_compare(self, node: ast.Compare, context: RuleContext) -> None:
        if isinstance(node.left, ast.Call) and isinstance(node.left.func, ast.Name):
            if node.left.func.id == "type":
                for op in node.ops:
                    if isinstance(op, (ast.Eq, ast.Is)):
                        context.make_finding(node, self)


class DictKeysMembershipRule(AstRule):
    rule_id = 26
    rule_code = "DICT_KEYS_MEMBERSHIP"
    default_message = "Unnecessary `.keys()` call in membership test"
    default_remediation = "Check membership directly with `key in dict`"

    def check_compare(self, node: ast.Compare, context: RuleContext) -> None:
        for op, right in zip(node.ops, node.comparators):
            if isinstance(op, (ast.In, ast.NotIn)):
                if isinstance(right, ast.Call) and isinstance(right.func, ast.Attribute):
                    if right.func.attr == "keys":
                        context.make_finding(node, self)


# --- 3. Scope, Resources & Exception Hygiene ---


class BuiltinShadowingRule(AstRule):
    rule_id = 8
    rule_code = "BUILTIN_SHADOWING"
    default_message = "Variable name shadows Python built-in"
    default_remediation = "Rename variable to avoid shadowing built-in name"

    def check_assign(self, node: ast.Assign, context: RuleContext) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in BUILTIN_SHADOW_NAMES:
                context.make_finding(
                    node,
                    self,
                    f"Variable name '{target.id}' shadows Python built-in",
                    f"Rename variable to avoid shadowing built-in `{target.id}`",
                )


class WildcardImportRule(AstRule):
    rule_id = 12
    rule_code = "WILDCARD_IMPORT"
    default_message = "Wildcard import pollutes namespace"
    default_remediation = "Import specific symbols or import the module namespace directly"

    def check_import_from(self, node: ast.ImportFrom, context: RuleContext) -> None:
        if any(alias.name == "*" for alias in node.names):
            context.make_finding(
                node,
                self,
                f"Wildcard import `from {node.module} import *` pollutes namespace",
            )


class ExceptionHygieneRule(AstRule):
    rule_id = 5
    rule_code = "BROAD_EXCEPTION_CATCH"
    default_message = "Catching overly broad exception"
    default_remediation = "Catch narrow domain exception classes whenever possible"

    def check_except(self, node: ast.ExceptHandler, context: RuleContext) -> None:
        if node.type is None:
            context.make_finding(
                node,
                self,
                "Bare `except:` catches SystemExit and KeyboardInterrupt",
                "Catch specific exception types or `except Exception:`",
            )
        elif isinstance(node.type, ast.Name) and node.type.id in (
            "Exception",
            "BaseException",
        ):
            is_swallowed = len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
            if is_swallowed:
                context.make_finding(
                    node,
                    self,
                    f"Empty `{node.type.id}: pass` silently swallows failures",
                    "Log the error, handle the specific condition, or re-raise",
                )
            else:
                context.make_finding(
                    node,
                    self,
                    f"Catching overly broad `{node.type.id}`",
                    "Catch narrow domain exception classes whenever possible",
                )


class RaiseStringLiteralRule(AstRule):
    rule_id = 29
    rule_code = "RAISE_STRING_LITERAL"
    default_message = "Raising string literal is invalid Python 3 exception syntax"
    default_remediation = "Raise an instance of Exception (e.g. `raise ValueError('...')`)"

    def check_raise(self, node: ast.Raise, context: RuleContext) -> None:
        if node.exc and isinstance(node.exc, ast.Constant) and isinstance(node.exc.value, str):
            context.make_finding(node, self)


class GlobalDeclarationRule(AstRule):
    rule_id = 31
    rule_code = "EXCESSIVE_GLOBAL"
    default_message = "Excessive global variable declarations in function"
    default_remediation = "Refactor state to a class or return state tuples/dataclasses"

    def check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, context: RuleContext
    ) -> None:
        global_nodes = [stmt for stmt in node.body if isinstance(stmt, ast.Global)]
        total = sum(len(g.names) for g in global_nodes)
        if total >= 3:
            context.make_finding(
                node,
                self,
                f"Function '{node.name}' declares {total} global variables",
            )


# --- 4. Iteration & Control Flow ---


class RangeLenIndexingRule(AstRule):
    rule_id = 23
    rule_code = "RANGE_LEN_INDEXING"
    default_message = (
        "Iterating via `range(len(...))` or `range(0, len(...))` instead of direct iteration"
    )
    default_remediation = "Iterate directly `for item in collection:` or use `enumerate()`"

    def check_for(self, node: ast.For, context: RuleContext) -> None:
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == "range" and has_len_call_in_args(node.iter):
                context.make_finding(node, self)


# --- 5. Class & OOP Design ---


class MissingSuperInitRule(AstRule):
    rule_id = 33
    rule_code = "MISSING_SUPER_INIT"
    default_message = "Subclass `__init__` does not call `super().__init__()`"
    default_remediation = "Add `super().__init__(...)` call in child `__init__`"

    def check_class(self, node: ast.ClassDef, context: RuleContext) -> None:
        if node.bases:
            for item in node.body:
                if (
                    isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and item.name == "__init__"
                ):
                    has_super = any(
                        isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Attribute)
                        and isinstance(call.func.value, ast.Call)
                        and isinstance(call.func.value.func, ast.Name)
                        and call.func.value.func.id == "super"
                        for call in ast.walk(item)
                    )
                    is_pass = not item.body or (
                        len(item.body) == 1 and isinstance(item.body[0], ast.Pass)
                    )
                    if not has_super and not is_pass:
                        context.make_finding(
                            item,
                            self,
                            f"Subclass '{node.name}.__init__' does not call super().__init__()",
                        )


class MissingSelfRule(AstRule):
    rule_id = 43
    rule_code = "MISSING_SELF_ARGUMENT"
    default_message = "Instance method has no 'self' parameter"
    default_remediation = (
        "Add 'self' as first parameter or mark method with @staticmethod/@classmethod"
    )

    def check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, context: RuleContext
    ) -> None:
        if context.current_class_name:
            dec_names = get_decorator_names(node)
            if "staticmethod" not in dec_names and "classmethod" not in dec_names:
                if not node.args.args and not node.args.posonlyargs:
                    context.make_finding(
                        node,
                        self,
                        f"Instance method '{node.name}' in class '{context.current_class_name}' has no 'self' parameter",
                    )


class StaticMethodClsRule(AstRule):
    rule_id = 35
    rule_code = "STATICMETHOD_CLS_MISUSE"
    default_message = "@staticmethod defines 'cls' argument"
    default_remediation = "Use @classmethod when class context is required"

    def check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, context: RuleContext
    ) -> None:
        dec_names = get_decorator_names(node)
        if "staticmethod" in dec_names:
            if node.args.args and node.args.args[0].arg == "cls":
                context.make_finding(
                    node,
                    self,
                    f"@staticmethod '{node.name}' defines 'cls' argument",
                )


class ComplexLambdaRule(AstRule):
    rule_id = 44
    rule_code = "COMPLEX_LAMBDA"
    default_message = "Overly complex lambda expression"
    default_remediation = "Define a named local function (`def`) for non-trivial logic"

    def check_call(self, node: ast.Call, context: RuleContext) -> None:
        if isinstance(node.func, ast.Lambda):
            if len(list(ast.walk(node.func))) > 15:
                context.make_finding(node, self)


# --- 6. Security, Runtime & Process ---


class AssertInProductionRule(AstRule):
    rule_id = 37
    rule_code = "ASSERT_AS_RUNTIME_CHECK"
    default_message = "`assert` can be disabled with Python `-O` optimization flags"
    default_remediation = "Raise explicit exceptions (e.g. ValueError) for runtime input validation"

    def check_assert(self, node: ast.Assert, context: RuleContext) -> None:
        if not context.is_test_file:
            context.make_finding(node, self)


class SubprocessShellRule(AstRule):
    rule_id = 46
    rule_code = "SUBPROCESS_SHELL_TRUE"
    default_message = "`subprocess` invoked with `shell=True`"
    default_remediation = "Pass list of argument strings and omit `shell=True`"

    def check_call(self, node: ast.Call, context: RuleContext) -> None:
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "subprocess" and node.func.attr in (
                "run",
                "Popen",
                "call",
                "check_call",
                "check_output",
            ):
                for kw in node.keywords:
                    if (
                        kw.arg == "shell"
                        and isinstance(kw.value, ast.Constant)
                        and bool(kw.value.value)
                    ):
                        context.make_finding(node, self)


class OsSystemDeprecatedRule(AstRule):
    rule_id = 48
    rule_code = "OS_SYSTEM_DEPRECATED"
    default_message = "`os.system()` is insecure and unescaped"
    default_remediation = "Use `subprocess.run([...], check=True)`"

    def check_call(self, node: ast.Call, context: RuleContext) -> None:
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == "os" and node.func.attr == "system":
                context.make_finding(node, self)


class NaiveDatetimeNowRule(AstRule):
    rule_id = 49
    rule_code = "NAIVE_DATETIME_NOW"
    default_message = "`datetime.now()` produces naive local timestamp without timezone"
    default_remediation = "Use `datetime.now(timezone.utc)`"

    def check_call(self, node: ast.Call, context: RuleContext) -> None:
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if (
                node.func.value.id == "datetime"
                and node.func.attr == "now"
                and not node.args
                and not node.keywords
            ):
                context.make_finding(node, self)


ALL_PITFALL_RULES: tuple[type[AstRule], ...] = (
    MutableDefaultRule,
    MutatingMethodAssignmentRule,
    ListConcatAugAssignRule,
    ChainedAssignmentRule,
    MutableClassAttributeRule,
    LiteralIdentityRule,
    NoneEqualityRule,
    ExplicitBooleanComparisonRule,
    TypeCheckRule,
    DictKeysMembershipRule,
    BuiltinShadowingRule,
    WildcardImportRule,
    ExceptionHygieneRule,
    RaiseStringLiteralRule,
    GlobalDeclarationRule,
    RangeLenIndexingRule,
    MissingSuperInitRule,
    MissingSelfRule,
    StaticMethodClsRule,
    ComplexLambdaRule,
    AssertInProductionRule,
    SubprocessShellRule,
    OsSystemDeprecatedRule,
    NaiveDatetimeNowRule,
)
