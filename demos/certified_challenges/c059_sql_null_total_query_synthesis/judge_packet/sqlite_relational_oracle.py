"""Judge-owned node-at-a-time relational evaluation on a PRIVATE SQLite database.

This is not the proposer's recursive SQL compiler or the second judge's Python
interpreter. Typed fixture columns flow through views (not affinity-losing
untyped materialized tables). No oracle relation is exposed to candidate SQL.
The legacy row-dictionary contract retains the first duplicate column label.
Independence here concerns proposer code, not SQLite's implementation.
"""

import sqlite3
from dataclasses import dataclass
from typing import Any


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


@dataclass(frozen=True)
class Relation:
    name: str
    columns: tuple[str, ...]
    bindings: tuple[tuple[str, ...], ...]

    def environment(self, alias: str) -> dict[str, str]:
        result = {}
        for index, keys in enumerate(self.bindings):
            for key in keys:
                result.setdefault(key, f'{alias}."c{index}"')
        return result

    def fields(self, alias: str) -> list[tuple[str, tuple[str, ...], str]]:
        return [
            (name, keys, f'{alias}."c{index}"')
            for index, (name, keys) in enumerate(zip(self.columns, self.bindings))
        ]


class SQLiteRelationalOracle:
    """Own trusted intermediate views; caller owns and closes the private connection."""

    def __init__(self, connection: sqlite3.Connection, schema: dict):
        self.connection = connection
        self.schema = schema
        self.serial = 0
        self.connection.execute('CREATE TEMP TABLE "__c059_constants" (value)')

    def _relation(self, fields, source: str, suffix: str = "", distinct: bool = False):
        self.serial += 1
        name = f"__c059_node_{self.serial}"
        columns, bindings, expressions = zip(*fields)
        projection = ", ".join(
            f'{expression} AS "c{i}"' for i, expression in enumerate(expressions)
        )
        dedup = "DISTINCT " if distinct else ""
        self.connection.execute(
            f"CREATE TEMP VIEW {_quote(name)} AS SELECT {dedup}{projection} FROM {source}{suffix}"
        )
        return Relation(name, tuple(columns), tuple(bindings))

    def _argument(self, value: Any, environment: dict[str, str]) -> str:
        if isinstance(value, dict) and "val" in value and "col" not in value:
            literal = value["val"]
            if literal is not None and type(literal) not in (str, int, float, bool):
                raise ValueError("unsupported scalar literal")
            cursor = self.connection.execute(
                'INSERT INTO "__c059_constants" VALUES (?)', (literal,)
            )
            # Unary + removes the subquery's column affinity without converting
            # its storage class. A bare untyped-column subquery is NOT equivalent
            # to a literal in comparisons with a TEXT-affinity column.
            return f'+(SELECT value FROM "__c059_constants" WHERE rowid={cursor.lastrowid})'
        key = value["col"] if isinstance(value, dict) else value
        return environment[key]

    def _predicate(self, predicate: dict, environment: dict[str, str]) -> str:
        expressions = []
        for operation, operands in predicate.items():
            if operation in ("and", "or"):
                parts = [self._predicate(item, environment) for item in operands]
                expression = (" AND " if operation == "and" else " OR ").join(parts)
            elif operation == "not":
                expression = "NOT " + self._predicate(operands, environment)
            elif operation == "coalesce":
                expression = (
                    "COALESCE("
                    + ", ".join(self._argument(item, environment) for item in operands)
                    + ")"
                )
            elif operation in ("is_null", "is_not_null"):
                expression = self._argument(operands, environment) + (
                    " IS NULL" if operation == "is_null" else " IS NOT NULL"
                )
            else:
                operator = {
                    "eq3": "=",
                    "distinct": "IS DISTINCT FROM",
                    "not_distinct": "IS NOT DISTINCT FROM",
                }[operation]
                expression = f"{self._argument(operands[0], environment)} {operator} {self._argument(operands[1], environment)}"
            expressions.append(f"({expression})")
        return "(" + (" AND ".join(expressions) or "1") + ")"

    def evaluate(self, node: Any) -> Relation:
        if isinstance(node, str):
            fields = [
                (column, (column, f"{node}.{column}"), f"b.{_quote(column)}")
                for column in self.schema[node]
            ]
            return self._relation(fields, f"main.{_quote(node)} AS b")
        operation = node["op"]
        if operation in ("join", "anti_join", "semi_join", "union_all"):
            return self._binary(node)
        source = self.evaluate(node["from"])
        environment = source.environment("s")
        fields = source.fields("s")
        source_sql = f"{_quote(source.name)} AS s"
        if operation in ("select", "project"):
            projection = node.get("project") if operation == "select" else node["columns"]
            if projection:
                fields = [(column, (column,), environment[column]) for column in projection]
            predicate = node.get("where")
            suffix = " WHERE " + self._predicate(predicate, environment) if predicate else ""
            return self._relation(fields, source_sql, suffix)
        if operation == "rename":
            mapping = node["map"]
            fields = [
                (mapping.get(name, name), (mapping.get(name, name),), expression)
                for name, _, expression in fields
            ]
        elif operation == "group":
            by = node.get("by", [])
            fields = [(column, (column,), environment[column]) for column in by]
            for name, aggregate in node.get("agg", {}).items():
                function = aggregate["func"]
                if function == "count_star":
                    expression = "COUNT(*)"
                else:
                    sql_function = {"count_col": "COUNT", "sum": "SUM", "min": "MIN", "max": "MAX"}[
                        function
                    ]
                    expression = f"{sql_function}({environment[aggregate['arg']]})"
                fields.append((name, (name,), expression))
            suffix = " GROUP BY " + ", ".join(environment[column] for column in by) if by else ""
            return self._relation(fields, source_sql, suffix)
        elif operation != "distinct":
            raise ValueError(f"unsupported operator: {operation}")
        return self._relation(fields, source_sql, distinct=operation == "distinct")

    def _binary(self, node: dict) -> Relation:
        left, right = self.evaluate(node["left"]), self.evaluate(node["right"])
        operation = node["op"]
        if operation == "union_all":
            if len(left.columns) != len(right.columns):
                raise ValueError("union arity mismatch")
            self.serial += 1
            name = f"__c059_node_{self.serial}"
            self.connection.execute(
                f"CREATE TEMP VIEW {_quote(name)} AS SELECT * FROM {_quote(left.name)} UNION ALL SELECT * FROM {_quote(right.name)}"
            )
            return Relation(name, left.columns, left.bindings)
        environment = left.environment("l")
        for key, expression in right.environment("r").items():
            environment.setdefault(key, expression)
        source_sql = f"{_quote(left.name)} AS l"
        right_sql = f"{_quote(right.name)} AS r"
        predicate = self._predicate(node.get("on", {}), environment)
        if operation == "join":
            kind = {"inner": "INNER", "left": "LEFT"}[node.get("type", "inner")]
            return self._relation(
                left.fields("l") + right.fields("r"),
                f"{source_sql} {kind} JOIN {right_sql} ON {predicate}",
            )
        if operation == "anti_join" and node.get("match", "null_safe") == "sql_not_in":
            operands = node.get("on", {}).get("eq3") or node.get("on", {}).get("not_distinct")
            if not operands:
                raise ValueError("NOT IN requires comparison keys")
            condition = f"{self._argument(operands[0], left.environment('l'))} NOT IN (SELECT {self._argument(operands[1], right.environment('r'))} FROM {right_sql})"
        else:
            negation = "NOT " if operation == "anti_join" else ""
            condition = f"{negation}EXISTS (SELECT 1 FROM {right_sql} WHERE {predicate})"
        return self._relation(left.fields("l"), source_sql, " WHERE " + condition)

    def read(self, relation: Relation) -> tuple[frozenset[str], list[dict]]:
        rows = []
        for values in self.connection.execute(f"SELECT * FROM {_quote(relation.name)}"):
            row = {}
            for name, value in zip(relation.columns, values):
                row.setdefault(name, value)
            rows.append(row)
        return frozenset(relation.columns), rows

    def preflight(
        self, spec: dict, protected: list[str]
    ) -> tuple[frozenset[str] | None, list[dict]]:
        pending, tables = [spec], []
        while pending:
            node = pending.pop()
            if isinstance(node, str):
                tables.append(node)
            elif isinstance(node, dict):
                pending.extend(node[key] for key in ("right", "left", "from") if key in node)
        for table in tables or list(self.schema):
            applicable = [column for column in protected if column in self.schema[table]]
            if applicable:
                relation = self.evaluate(table)
                condition = " OR ".join(
                    f"{expression} IS NULL"
                    for key, expression in relation.environment("s").items()
                    if key in applicable
                )
                return self.read(
                    self._relation(
                        relation.fields("s"), f"{_quote(relation.name)} AS s", " WHERE " + condition
                    )
                )
        # No protected source: only emptiness is specified, not the SELECT label.
        return None, []
