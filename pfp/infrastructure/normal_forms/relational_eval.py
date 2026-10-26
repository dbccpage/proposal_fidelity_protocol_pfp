"""0NF flattening and the 5NF instance join witness.

AuthorityEffect: None.
"""

from __future__ import annotations

import sqlite3
from typing import Any


def normalize_0nf_to_1nf(
    conn: sqlite3.Connection,
    raw_records: list[tuple[int, str, str]],
) -> list[dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM student_records_0nf;")
    cursor.execute("DELETE FROM student_enrollments_1nf;")
    for student_id, name, courses_csv in raw_records:
        cursor.execute(
            "INSERT INTO student_records_0nf VALUES (?, ?, ?);",
            (student_id, name, courses_csv),
        )
    cursor.execute("SELECT student_id, student_name, course_list_csv FROM student_records_0nf;")
    flattened: list[dict[str, Any]] = []
    for row in cursor.fetchall():
        courses = [course.strip() for course in row["course_list_csv"].split(",") if course.strip()]
        for course in courses:
            cursor.execute(
                "INSERT INTO student_enrollments_1nf VALUES (?, ?, ?, ?, ?, ?);",
                (
                    row["student_id"],
                    row["student_name"],
                    course,
                    f"Title of {course}",
                    101,
                    "Hall 302",
                ),
            )
            flattened.append(
                {
                    "student_id": row["student_id"],
                    "student_name": row["student_name"],
                    "course_code": course,
                }
            )
    conn.commit()
    return flattened


def evaluate_5nf_project_join_integrity(
    conn: sqlite3.Connection,
    fill2_tuples: list[tuple[str, str, str]],
) -> dict[str, Any]:
    """Instance witness for one ternary join. schema_in_5nf stays None."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM consulting_fill2;")
    for consultant, company, product in fill2_tuples:
        cursor.execute(
            "INSERT INTO consulting_fill2 VALUES (?, ?, ?);",
            (consultant, company, product),
        )
    conn.commit()
    cursor.execute("SELECT COUNT(*) AS fill_count FROM consulting_fill2;")
    fill_count = cursor.fetchone()["fill_count"]
    cursor.execute("SELECT COUNT(*) AS shell_count FROM consulting_shell2;")
    shell_count = cursor.fetchone()["shell_count"]
    cursor.execute("SELECT * FROM consulting_spurious_tuples;")
    spurious = [dict(row) for row in cursor.fetchall()]
    body_obeys = len(spurious) == 0 and shell_count == fill_count
    return {
        "fill2_count": fill_count,
        "shell2_count": shell_count,
        "spurious_tuples_count": len(spurious),
        "spurious_tuples": spurious,
        "instance_obeys_declared_ternary_join": body_obeys,
        "schema_in_5nf": None,
        "is_5nf_compliant": body_obeys,
    }
