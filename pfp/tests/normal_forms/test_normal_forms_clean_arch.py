"""Unit tests for education normal forms clean architecture modules.

AuthorityEffect: None.
"""

import unittest

from pfp.domain.normal_forms.examples import (
    order_line,
    order_line_fails_second_normal_form,
    street_journal_title,
    street_journal_title_passes_third_and_fails_boyce_codd,
    street_journal_title_split,
)
from pfp.domain.normal_forms.relational import (
    FunctionalDependency,
    RelationalSchema,
    check_2nf,
    check_3nf,
    check_bcnf,
    compute_attribute_closure,
    find_candidate_keys,
)
from pfp.infrastructure.normal_forms import (
    STANDARD_PATH,
    NormalFormsDbContext,
    NormalFormsEvaluator,
)


class TestNormalFormsCleanArch(unittest.TestCase):
    def test_domain_attribute_closure_and_keys(self):
        # Schema R(A, B, C) with A -> B, B -> C
        fds = (
            FunctionalDependency(frozenset(["A"]), frozenset(["B"])),
            FunctionalDependency(frozenset(["B"]), frozenset(["C"])),
        )
        schema = RelationalSchema(attributes=frozenset(["A", "B", "C"]), dependencies=fds)
        closure_a = compute_attribute_closure(frozenset(["A"]), fds)
        self.assertEqual(closure_a, frozenset(["A", "B", "C"]))
        find_candidate_keys(schema)
        is_2nf, _ = check_2nf(schema)
        self.assertTrue(is_2nf)
        is_3nf, _ = check_3nf(schema)
        self.assertFalse(is_3nf)  # B -> C violates 3NF (transitive)

    def test_schema_examples(self):
        schema_ol = order_line()
        keys_ol = find_candidate_keys(schema_ol)
        self.assertEqual(keys_ol, [frozenset(["OrderId", "LineNo"])])
        self.assertTrue(order_line_fails_second_normal_form())

        schema_sjt = street_journal_title()
        is_bcnf, _ = check_bcnf(schema_sjt)
        self.assertFalse(is_bcnf)
        self.assertTrue(street_journal_title_passes_third_and_fails_boyce_codd())

        lossless, preserved = street_journal_title_split()
        self.assertTrue(lossless)
        self.assertFalse(preserved)

    def test_infrastructure_evaluator_sqlite(self):
        with NormalFormsEvaluator(in_memory=True) as evaluator:
            raw_records = [
                (101, "Alice", "MATH101,PHYS101"),
                (102, "Bob", "CHEM101"),
            ]
            flat_records = evaluator.normalize_0nf_to_1nf(raw_records)
            self.assertEqual(len(flat_records), 3)
            self.assertEqual(flat_records[0]["student_id"], 101)
            self.assertEqual(flat_records[0]["course_code"], "MATH101")
            self.assertEqual(flat_records[1]["course_code"], "PHYS101")

    def test_infrastructure_db_context_and_transaction_fence(self):
        with NormalFormsDbContext(in_memory=True) as ctx:
            self.assertIsNotNone(ctx.connection)
            with ctx.transaction() as c:
                c.execute("CREATE TABLE test_tx (id INT PRIMARY KEY, val TEXT);")
                c.execute("INSERT INTO test_tx VALUES (1, 'alpha');")

            # Verify persisted
            c = ctx.cursor()
            c.execute("SELECT val FROM test_tx WHERE id = 1;")
            self.assertEqual(c.fetchone()[0], "alpha")

            # Verify rollback on exception
            with self.assertRaises(ValueError):
                with ctx.transaction() as c2:
                    c2.execute("INSERT INTO test_tx VALUES (2, 'beta');")
                    raise ValueError("Simulated failure inside transaction")

            c.execute("SELECT COUNT(*) FROM test_tx WHERE id = 2;")
            self.assertEqual(c.fetchone()[0], 0)

        # Context manager closes connection
        self.assertIsNone(ctx._conn)

    def test_evaluator_with_shared_db_context(self):
        with NormalFormsDbContext(in_memory=True) as ctx:
            with NormalFormsEvaluator(db_context=ctx) as ev:
                res = ev.normalize_0nf_to_1nf([(1, "Test", "CS101")])
                self.assertEqual(len(res), 1)

    def test_infrastructure_standard_yaml_exists(self):
        self.assertTrue(STANDARD_PATH.is_file(), f"Standard YAML missing at {STANDARD_PATH}")


if __name__ == "__main__":
    unittest.main()
