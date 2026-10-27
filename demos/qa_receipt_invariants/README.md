# QA receipt invariants

Falsification tests for a sealed software QA receipt: the value objects
that record which tests ran, what the strict inspector found, which
mutants were killed, and a SHA-256 seal over the whole payload.

Run from the repository root (Python 3.12+, pytest):

    python -m pytest demos/qa_receipt_invariants -q

Expected: `13 passed`.

Wiki page: `wiki/Test-Qa-Receipt-Invariants.md`.
