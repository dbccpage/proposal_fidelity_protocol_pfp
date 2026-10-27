"""Exact local checks used by the mode trials.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction


def solve_linear(rows: list[list[int]]) -> list[Fraction] | None:
    matrix = [list(map(Fraction, row)) for row in rows]
    unknown_count = len(matrix[0]) - 1
    pivot_row = 0
    pivots: list[int] = []
    for col in range(unknown_count):
        selected = next((r for r in range(pivot_row, len(matrix)) if matrix[r][col] != 0), None)
        if selected is None:
            continue
        matrix[pivot_row], matrix[selected] = matrix[selected], matrix[pivot_row]
        pivot = matrix[pivot_row][col]
        matrix[pivot_row] = [value / pivot for value in matrix[pivot_row]]
        for row_index in range(len(matrix)):
            if row_index == pivot_row or matrix[row_index][col] == 0:
                continue
            factor = matrix[row_index][col]
            matrix[row_index] = [
                matrix[row_index][col_index] - factor * matrix[pivot_row][col_index]
                for col_index in range(unknown_count + 1)
            ]
        pivots.append(col)
        pivot_row += 1
    for row in matrix[pivot_row:]:
        if row[-1] != 0:
            return None
    if len(pivots) != unknown_count:
        return None
    solution = [Fraction(0) for _ in range(unknown_count)]
    for row_index, col in enumerate(pivots):
        solution[col] = matrix[row_index][-1]
    return solution


def components(vertex_count: int, edges: list[list[int]]) -> int:
    parent = list(range(vertex_count))

    def find(vertex: int) -> int:
        while parent[vertex] != vertex:
            parent[vertex] = parent[parent[vertex]]
            vertex = parent[vertex]
        return vertex

    for left, right in edges:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left
    return len({find(vertex) for vertex in range(vertex_count)})


def cycle_rank(vertex_count: int, edges: list[list[int]]) -> int:
    return len(edges) - vertex_count + components(vertex_count, edges)


def edge_set(edges: list[list[int]]) -> set[tuple[int, int]]:
    return {tuple(sorted(edge)) for edge in edges}


def is_bridge(vertex_count: int, edges: list[list[int]], left: int, right: int) -> bool:
    target = tuple(sorted((left, right)))
    if target not in edge_set(edges) or components(vertex_count, edges) != 1:
        return False
    remaining = [edge for edge in edges if tuple(sorted(edge)) != target]
    return components(vertex_count, remaining) > 1


def triangle_area_numerator(squared_a: int, squared_b: int, squared_c: int) -> int:
    """16 * area^2 for a triangle with those squared side lengths."""
    return (
        2 * squared_a * squared_b
        + 2 * squared_a * squared_c
        + 2 * squared_b * squared_c
        - squared_a * squared_a
        - squared_b * squared_b
        - squared_c * squared_c
    )


def project(rows: list[dict], columns: tuple[str, ...]) -> list[tuple]:
    return sorted({tuple(row[column] for column in columns) for row in rows})


def join(left: list[tuple], left_cols: tuple[str, ...], right: list[tuple], right_cols: tuple[str, ...]) -> list[dict]:
    shared = [column for column in left_cols if column in right_cols]
    joined: list[dict] = []
    for left_row in left:
        left_map = dict(zip(left_cols, left_row, strict=True))
        for right_row in right:
            right_map = dict(zip(right_cols, right_row, strict=True))
            if all(left_map[column] == right_map[column] for column in shared):
                joined.append({**left_map, **right_map})
    return joined
