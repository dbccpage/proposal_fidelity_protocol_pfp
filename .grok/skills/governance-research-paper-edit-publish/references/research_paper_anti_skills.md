# Research Paper Anti-Pattern Catalog & Enforcing Python Rules

**AuthorityEffect:** None.  
**Implementation:** `research_papers.domain.rules`  
**Automated Execution:** `py -3.12 -m research_papers.use_cases.paper_review.cli gates --paper-path <path>`

This catalog indexes legacy paper review anti-patterns and maps them directly to their active, fully-typed enforcing Python classes.

---

## Catalog of Enforced Anti-Patterns

| Anti-Pattern ID | Anti-Pattern Description | Enforcing Python Rule Class |
|---|---|---|
| `ANTI-BROKEN-CITATIONS` | LaTeX `\cite{...}` missing matching `\bibitem` | `CitationBijectionRule` |
| `ANTI-PANDOC-MAKETITLE` | Pandoc-generated `\maketitle` breaking header layout | `NoMaketitleRule` |
| `ANTI-EMPTY-TOC` | Generated empty or unpopulated `\tableofcontents` | `NoTableOfContentsRule` |
| `ANTI-OVERFULL-HBOX-TABLE` | Wide tables overflowing portrait margins | `LandscapeTableRule` |
| `ANTI-MISSING-PDF` | Missing, empty, or unextractable compiled PDF | `PdfExistsAndRenderableRule` |
| `ANTI-NONCANONICAL-NOTEBOOK` | Notebooks with legacy or non-canonical prefixes | `NotebookCanonicalNamingRule` |
| `ANTI-HARDCODED-USER-PATHS` | Hardcoded local user directories in notebooks | `NotebookNoUserPathsRule` |
| `ANTI-DIRTY-NOTEBOOK-EXEC` | Empty execution counts or unhandled tracebacks | `NotebookExecutionCleanlinessRule` |
| `ANTI-TEST-LOCATION-ESCAPE` | Test files placed outside `code/tests/` | `PythonTestLocationRule` |
| `ANTI-GLOBAL-MYPY-IGNORE` | Global `ignore_missing_imports = true` | `StrictMypyConfigRule` |
| `ANTI-NBCLIENT-IN-PYTEST` | Pytest invoking headless notebook clients | `NoNotebookClientsInPytestRule` |
| `ANTI-MISSING-LAKEFILE` | Missing `lakefile.lean` or `lakefile.toml` | `LeanLakeConfigRule` |
| `ANTI-UNPINNED-TOOLCHAIN` | Unpinned or platform-tagged Lean toolchain | `LeanToolchainPinnedRule` |
| `ANTI-LEAN-SORRY-ESCAPES` | Formal proofs containing `sorry` or `admit` | `LeanNoEscapeHatchesRule` |
| `ANTI-UNAPPROVED-AXIOMS` | Axiom census referencing unauthorized axioms | `LeanAxiomReportRule` |
| `ANTI-TREE-INVERTIBILITY-DEFECT` | Cochain surjectivity on trees without invertible maps | `TreeInvertibilityHypothesisRule` |
| `ANTI-INCONSISTENT-MARGIN-NORM` | Singular-value margins on non-Euclidean norms | `NormConsistentMarginRule` |
| `ANTI-UNBOUNDED-GLOBAL-SCOPE` | Local nodes asserting global trace-norm state | `SimulationGlobalMeasurementScopeRule` |
| `ANTI-ASYMMETRIC-ORIGIN-EVAL` | Polynomial evaluators where $P(0) \neq 0$ | `NonlinearEvaluatorZeroOriginRule` |
| `ANTI-DIAGNOSTIC-AS-OBSTRUCTION`| Conflating continuous heuristics with exact invariants | `DiagnosticDistinctionRule` |
| `ANTI-UNVERIFIED-PASS-CLAIM` | Claiming pass on undetermined boundary cases | `AuditUndeterminedReportingRule` |
| `ANTI-UNBOUNDED-HYPE-WORDS` | Unanchored hype verbs in mathematical prose | `ClaimHygieneBannedWordsRule` |
| `ANTI-UNTRACKED-PACKAGE-FILES` | Files missing from `MANIFEST.sha256` / `SHA256SUMS` | `ManifestBijectionRule` |
| `ANTI-WIN32-PATH-OVERFLOW` | File paths exceeding 250 characters | `WindowsMaxPathRule` |
| `ANTI-FORBIDDEN-DIRECTORIES` | Forbidden directories (`dist/`, `evidence/`, `rt/`) | `RestrictedDirectoryStructureRule` |
| `ANTI-INTERNAL-REVIEW-SLOP` | Internal LLM dossiers polluting public packages | `NoInternalReviewDossiersRule` |
| `ANTI-MD004-ASTERISK-LIST-STYLE` | Asterisk unordered list style violating MD004 or suppressing markdownlint | `MarkdownUnorderedListStyleRule` |
| `ANTI-UNVERIFIED-RELEASE-SCRIPT` | Deposit missing executable rebuild or verify script | `ReleaseVerificationScriptRule` |
| `ANTI-TEX-PDF-DESYNC` | LaTeX source modified without reconciling rendered PDF artifacts | `TexPdfRenderConsistencyRule` |
| `ANTI-MISSING-DUAL-WITNESS` | Coboundary exactness asserted without dual cochain certificates | `DualWitnessCertificateRule` |
