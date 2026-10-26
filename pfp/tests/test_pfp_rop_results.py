"""Unit tests for Railway-Oriented Programming (ROP) Result monad in PFP.

Tests:
  - Result.ok and Result.err
  - unwrap, unwrap_err, unwrap_or
  - map, map_err, and_then
  - refuse_if guard
  - collect_results
  - Equality and value/error properties

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest

from omega_engine_pfp.domain.kernel.result import (
    DomainError,
    EvaluationVerdict,
    GenesisCycleVerdict,
    RefusalCode,
    Result,
    TerminalStatus,
    collect_results,
    refuse_if,
)


class TestPfpRopResults(unittest.TestCase):
    """Test pure functional monadic behavior of Result[T, E]."""

    def test_ok_monad_laws(self) -> None:
        res = Result.ok(42)
        self.assertTrue(res.is_ok)
        self.assertFalse(res.is_err)
        self.assertEqual(res.value, 42)
        self.assertEqual(res.unwrap(), 42)
        self.assertEqual(res.unwrap_or(0), 42)

        # Map
        mapped = res.map(lambda x: x * 2)
        self.assertEqual(mapped.unwrap(), 84)

        # And_then
        chained = res.and_then(lambda x: Result.ok(f"val_{x}"))
        self.assertEqual(chained.unwrap(), "val_42")

    def test_err_monad_laws(self) -> None:
        err = DomainError(code=RefusalCode.POLICY_VIOLATION, message="Policy failed")
        res = Result.err(err)
        self.assertFalse(res.is_ok)
        self.assertTrue(res.is_err)
        self.assertEqual(res.error, err)
        self.assertEqual(res.unwrap_err(), err)
        self.assertEqual(res.unwrap_or(100), 100)

        with self.assertRaises(ValueError):
            res.unwrap()

        # Map skips error
        mapped = res.map(lambda x: x * 2)
        self.assertTrue(mapped.is_err)
        self.assertEqual(mapped.unwrap_err(), err)

        # Map_err
        mapped_err = res.map_err(lambda e: DomainError(code=e.code, message="Wrapped: " + e.message))
        self.assertEqual(mapped_err.unwrap_err().message, "Wrapped: Policy failed")

    def test_refuse_if_guard(self) -> None:
        good = refuse_if(False, RefusalCode.GATE_REJECTED, "Gate failed")
        self.assertTrue(good.is_ok)

        bad = refuse_if(True, RefusalCode.GATE_REJECTED, "Gate failed")
        self.assertTrue(bad.is_err)
        self.assertEqual(bad.unwrap_err().code, RefusalCode.GATE_REJECTED)

    def test_collect_results(self) -> None:
        all_ok = [Result.ok(1), Result.ok(2), Result.ok(3)]
        collected = collect_results(all_ok)
        self.assertTrue(collected.is_ok)
        self.assertEqual(collected.unwrap(), (1, 2, 3))

        has_err = [
            Result.ok(1),
            Result.err(DomainError(code=RefusalCode.NILPOTENCY_BROKEN, message="Non-zero boundary")),
            Result.ok(3),
        ]
        collected_err = collect_results(has_err)
        self.assertTrue(collected_err.is_err)
        self.assertEqual(collected_err.unwrap_err().code, RefusalCode.NILPOTENCY_BROKEN)


if __name__ == "__main__":
    unittest.main()
