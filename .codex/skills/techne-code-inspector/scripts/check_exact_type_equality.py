"""AST scanner to enforce exact-type equality guards on domain dataclasses (RULE_VO_EXACT_TYPE_EQUALITY_001)."""

import ast
import sys
from pathlib import Path


def check_directory(domain_dir: Path) -> list[str]:
    violations: list[str] = []
    for py_file in domain_dir.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except Exception as e:
            violations.append(f"{py_file}: Failed to parse AST: {e}")
            continue

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                is_dataclass = any(
                    (isinstance(d, ast.Name) and d.id == "dataclass")
                    or (isinstance(d, ast.Call) and getattr(d.func, "id", None) == "dataclass")
                    for d in node.decorator_list
                )
                if not is_dataclass:
                    continue

                eq_func = next(
                    (n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == "__eq__"),
                    None,
                )
                if eq_func is None:
                    violations.append(
                        f"{py_file.name}:{node.name} lacks explicit __eq__ exact-type guard"
                    )
                    continue

                code = ast.unparse(eq_func)
                if (
                    "type(self) is not type(other)" not in code
                    and "type(other) is not type(self)" not in code
                ):
                    violations.append(
                        f"{py_file.name}:{node.name} __eq__ does not enforce exact-type comparison"
                    )

    return violations


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    issues = check_directory(target)
    if issues:
        print("FAIL: Exact-type equality violations found:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    print("PASS: All domain dataclasses enforce exact-type equality.")
    sys.exit(0)
