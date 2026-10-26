"""Antibody Battery, AntiMorphisms, and Code Invariants.

Dual operator to forward operations:
  Antibody : (Code x EvidenceReceipt) -> Witness | StrengthenedResidual
AuthorityEffect: None.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

from .evidence import ConcreteWitness, Residual, Witness


@dataclass(frozen=True)
class AntiMorphism:
    """An anti-morphism / antibody that attempts to kill or challenge candidate code/states."""
    name: str
    source_colors: Tuple[str, ...]
    killer: Callable[[Any, Any], Optional[Witness]]

    def apply(self, candidate: Any, context: Any = None) -> Tuple[Optional[Witness], Residual]:
        witness = self.killer(candidate, context)
        if witness is not None and getattr(witness, "kills", lambda c: True)(candidate):
            return witness, Residual(
                claims=(),
                unverified=(witness.describe(),),
                risk_score=1.0,
            )
        return None, Residual(
            claims=(f"survived {self.name}",),
            unverified=(),
            risk_score=0.1,
        )


class ASTPatternVisitor(ast.NodeVisitor):
    """AST visitor that checks for canonical Python pitfalls and leakages."""

    def __init__(self) -> None:
        self.witnesses: List[ConcreteWitness] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_defaults(node)
        self._check_public_signature_types(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_defaults(node)
        self._check_public_signature_types(node)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.witnesses.append(
                ConcreteWitness(
                    kind="BARE_EXCEPT",
                    description="Bare except: clause detected (catches and risks swallowing BaseException)",
                    location=f"line {node.lineno}",
                )
            )
        if len(node.body) == 1:
            first = node.body[0]
            if isinstance(first, ast.Pass) or (isinstance(first, ast.Return) and first.value is None):
                self.witnesses.append(
                    ConcreteWitness(
                        kind="SWALLOWED_EXCEPTION",
                        description="Exception handler swallows exception with pass/return None",
                        location=f"line {node.lineno}",
                    )
                )
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Is, ast.IsNot)):
                if isinstance(comparator, ast.Constant):
                    if comparator.value not in (None, True, False, Ellipsis):
                        self.witnesses.append(
                            ConcreteWitness(
                                kind="LITERAL_IS_COMPARISON",
                                description=f"Literal identity comparison `is {comparator.value!r}` (use `==`)",
                                location=f"line {node.lineno}",
                            )
                        )
                if isinstance(node.left, ast.Constant):
                    if node.left.value not in (None, True, False, Ellipsis):
                        self.witnesses.append(
                            ConcreteWitness(
                                kind="LITERAL_IS_COMPARISON",
                                description=f"Literal identity comparison `{node.left.value!r} is ...` (use `==`)",
                                location=f"line {node.lineno}",
                            )
                        )

        if isinstance(node.left, ast.Call):
            func = node.left.func
            if isinstance(func, ast.Name) and func.id == "type":
                for op in node.ops:
                    if isinstance(op, (ast.Eq, ast.NotEq)):
                        self.witnesses.append(
                            ConcreteWitness(
                                kind="TYPE_EQUALITY_CHECK",
                                description="Direct `type(x) == T` comparison detected (use `isinstance(x, T)`)",
                                location=f"line {node.lineno}",
                            )
                        )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == "*":
                self.witnesses.append(
                    ConcreteWitness(
                        kind="STAR_IMPORT",
                        description=f"Star import `from {node.module} import *` pollutes namespace",
                        location=f"line {node.lineno}",
                    )
                )
        self.generic_visit(node)

    def _check_defaults(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for default in node.args.defaults + [d for d in node.args.kw_defaults if d is not None]:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.witnesses.append(
                    ConcreteWitness(
                        kind="MUTABLE_DEFAULT_ARGUMENT",
                        description=f"Mutable default argument in function '{node.name}'",
                        location=f"line {node.lineno}",
                    )
                )

    def _check_public_signature_types(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if not node.name.startswith("_"):
            for arg in node.args.args + node.args.kwonlyargs:
                if arg.annotation and self._is_any_annotation(arg.annotation):
                    self.witnesses.append(
                        ConcreteWitness(
                            kind="ANY_ON_PUBLIC_SURFACE",
                            description=f"Public parameter '{arg.arg}' in '{node.name}' annotated with `Any`",
                            location=f"line {node.lineno}",
                        )
                    )
            if node.returns and self._is_any_annotation(node.returns):
                self.witnesses.append(
                    ConcreteWitness(
                        kind="ANY_ON_PUBLIC_SURFACE",
                        description=f"Public function '{node.name}' return annotated with `Any`",
                        location=f"line {node.lineno}",
                    )
                )

    def _is_any_annotation(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name) and node.id == "Any":
            return True
        if isinstance(node, ast.Attribute) and node.attr == "Any":
            return True
        return False


def scan_source_for_pitfalls(source: str) -> List[ConcreteWitness]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [
            ConcreteWitness(
                kind="SYNTAX_ERROR",
                description=f"Source syntax error: {exc}",
                location=f"line {exc.lineno}",
            )
        ]
    visitor = ASTPatternVisitor()
    visitor.visit(tree)
    return visitor.witnesses


def make_ast_pattern_antibody(name: str = "ASTStaticAntiPatternAntibody") -> AntiMorphism:
    def killer(candidate: object, context: object = None) -> Optional[Witness]:
        source = candidate if isinstance(candidate, str) else str(candidate)
        witnesses = scan_source_for_pitfalls(source)
        return witnesses[0] if witnesses else None

    return AntiMorphism(name=name, source_colors=("Code",), killer=killer)


def pullback_antibody(
    op: Any,
    antibody: AntiMorphism,
    name: Optional[str] = None,
) -> AntiMorphism:
    pb_name = name or f"pullback({getattr(op, 'name', 'op')}* {antibody.name})"

    def killer(candidate_args: object, context: object = None) -> Optional[Witness]:
        try:
            if isinstance(candidate_args, tuple) and hasattr(op, "arity") and op.arity > 1:
                output, _ = op(*candidate_args)
            else:
                output, _ = op(candidate_args)
        except Exception as exc:
            return ConcreteWitness(
                kind="PULLBACK_EXECUTION_CRASH",
                description=f"Forward operation {getattr(op, 'name', 'op')} raised during pullback: {exc}",
            )
        witness, _ = antibody.apply(output, context)
        return witness

    return AntiMorphism(
        name=pb_name,
        source_colors=getattr(op, "source_colors", ("Code",)),
        killer=killer,
    )
