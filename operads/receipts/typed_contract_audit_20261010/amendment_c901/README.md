# C901 extraction amendment

This amendment supersedes only the final production source/test validation bindings in the parent receipt. The original receipt and all historical logs are unchanged.

The root's final C901 check found receipt initialization complexity 12. The evaluation and hit validation block was extracted unchanged into `_validate_evidence_bindings`; every guard and its execution order is preserved. Expanding the new private-method call produces exactly the prior `__post_init__` AST, and the dataclass field AST is unchanged. Scoped Ruff F401/F841/I/C901 with maximum complexity 10 passes, as does format checking.

All 15 unchanged audit tests pass on the new source after four real production mutations are killed and exact source/test bytes restored. These amended mutations bind the final 15-test file, rather than the earlier 13-test snapshot. The task-binding mutation still receives the existing lower-level `REQUEST_MISMATCH`; it demonstrates the specified early refusal code, not a successful admission exploit.

The earlier three-file 49-test/98.5185% coverage report belongs to the pre-extraction source snapshot; this amendment ran the 15 named audit tests and scoped lint/mutations, without claiming a new coverage measurement. Parent must regenerate the newly introduced Markdown resources because the compiler deliberately binds raw application source bytes. Audit remains Unadmitted/HOLD and signed evidence remains SIGNED_INSTRUCTION_ONLY. AuthorityEffect: None. No Git mutations, provider calls, host builds or live activation were performed.
