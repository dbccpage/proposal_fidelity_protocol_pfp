# Session Documentation Protocol

AuthorityEffect: None.

## 1. Objective

The `auto-docs` skill automates the extraction and preservation of operational context developed during agent pairing and coding sessions. It guarantees that:
1. Every modified or created file during a session is systematically recorded with markdown links.
2. Architecture invariants, ADR decisions, and domain modeling insights are captured in persistent markdown records under `_intelligence/documentation/sessions/`.
3. Source code is kept clean and professional by automatically hunting for and re-routing low-signal LLM comment slop to `_intelligence/documentation/`.

## 2. Session Record Format

Each session generates a timestamped document:
`_intelligence/documentation/sessions/session_<YYYYMMDD_HHMMSS>_<topic>.md`

### Required Metadata Sections:
- **Title**: `# Session Documentation Record: <Topic>`
- **Authority Banner**: `AuthorityEffect: None.`
- **Metadata**: Session timestamp (UTC), repository root, count of modified files.
- **Touched Artifacts**: Clickable markdown links (`file:///...`) with relative paths.
- **Architectural Invariants & Notes**: Observations on Clean Architecture, Four-Host Parity, and Claim Hygiene.
- **Comment Slop Audit Summary**: Count of slop comments flagged or re-routed.

## 3. Integration with `techne-comment-slop-hunter-killer`

When `auto-docs` runs:
1. It queries `git status --porcelain` to identify all files modified or added during the session.
2. It filters out forbidden surfaces (`.lake/`, `target/`, `node_modules/`, `.venv/`, `quarantine/`, `archive/`).
3. It passes the session code files to `comment_slop_router.route_file_comments()`:
   - Extracted comments are routed to `_intelligence/documentation/<module_path>.md`.
   - Low-signal comment slop is stripped from the source file.
   - Protected pragmas (`# noqa`, `# type: ignore`, `// SAFETY:`, `# Invariant:`, docstrings) are strictly preserved.

## 4. Host Isolation & Zero-Pollution Discipline

Session documentation records represent internal operational context. To prevent polluting third-party IDE environments, documentation files under `_intelligence/documentation/` must NEVER be copied or mirrored to `.claude/`, `.codex/`, or `.grok/`. `host_root_parity.py` tracks only shared governance, rules, skills, and agents.
