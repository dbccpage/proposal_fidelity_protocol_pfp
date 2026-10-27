"""AST validation for test sensitivity and anti-tautology enforcement. AuthorityEffect: None."""

from __future__ import annotations

import ast


def is_literal_node(node: ast.AST) -> bool:
    """Check if an AST node evaluates directly to a literal/constant."""
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(is_literal_node(elt) for elt in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            (k is None or is_literal_node(k)) and is_literal_node(v)
            for k, v in zip(node.keys, node.values)
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.operand, ast.Constant):
        return True
    if isinstance(node, ast.BinOp):
        return is_literal_node(node.left) and is_literal_node(node.right)
    return False


def find_tautological_assertions(source_code: str, filename: str = "<source>") -> list[str]:
    """Scan Python test source for literal tautologies and empty exception blocks."""
    issues: list[str] = []
    try:
        tree = ast.parse(source_code, filename=filename)
    except SyntaxError as err:
        return [f"{filename}:{err.lineno}: SyntaxError: {err.msg}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            test = node.test
            # Case 1: assert <literal> (e.g. assert True, assert 1)
            if isinstance(test, ast.Constant):
                issues.append(
                    f"{filename}:{node.lineno}: Tautological assertion of constant {test.value!r}"
                )
            # Case 2: assert <literal> <op> <literal> (e.g. assert 10 <= 32)
            elif isinstance(test, ast.Compare):
                if is_literal_node(test.left) and all(is_literal_node(c) for c in test.comparators):
                    issues.append(
                        f"{filename}:{node.lineno}: Tautological literal comparison in assert"
                    )
        elif isinstance(node, ast.With):
            # Case 3: with pytest.raises(...): raise Exception(...) without calling target code
            for item in node.items:
                ctx_expr = item.context_expr
                if isinstance(ctx_expr, ast.Call):
                    func_name = ""
                    if isinstance(ctx_expr.func, ast.Attribute):
                        func_name = ctx_expr.func.attr
                    elif isinstance(ctx_expr.func, ast.Name):
                        func_name = ctx_expr.func.id
                    if func_name == "raises":
                        statements = [s for s in node.body if not isinstance(s, ast.Pass)]
                        if len(statements) == 1 and isinstance(statements[0], ast.Raise):
                            issues.append(
                                f"{filename}:{node.lineno}: Self-certifying pytest.raises block with direct manual raise and no target execution"
                            )

    return issues
