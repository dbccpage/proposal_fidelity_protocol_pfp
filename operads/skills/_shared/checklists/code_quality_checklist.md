# Code Quality Checklist

Shared code quality checklist for reviews, linting, and pre-commit checks.

## Code Review Checklist

### Quality

- [ ] Code follows project patterns and conventions
- [ ] No duplicate code that should be abstracted
- [ ] Functions are focused and not too long
- [ ] Variable names are clear and descriptive
- [ ] Comments explain "why", not "what"

### Error Handling

- [ ] Domain-specific exceptions used (not generic `Exception`)
- [ ] Exceptions include context (available options, current state)
- [ ] Pattern: `raise DomainError(f"X not found. Available: {options}")` ext
- [ ] Logging added for fallback/error scenarios

### Correctness

- [ ] Logic handles edge cases
- [ ] Error handling is appropriate
- [ ] No obvious bugs or typos
- [ ] Tests cover new functionality

### Test Quality

- [ ] Assertions are specific and falsifiable
- [ ] No `assert true`, tautological checks, or smoke-only tests counted as proof
- [ ] `.is_ok()` / `.is_err()` checks are not the whole test unless the exact error/success boundary is the contract
- [ ] `unwrap()` / `expect()` may prepare fixtures but may not be the test
- [ ] Mocks may scaffold behavior but may not certify external trust, cryptographic soundness, or oracle independence
- [ ] Tests include at least one negative/edge case for new validation logic

## Pre-commit Checklist

### Python

- [ ] `ruff check --fix && ruff format` ext
- [ ] `mypy` passes (type checking)
- [ ] Tests pass (`pytest`)
- [ ] No secrets in code

### JavaScript/TypeScript

- [ ] `npm run lint` ext
- [ ] TypeScript compiles (`npx tsc --noEmit`)
- [ ] Tests pass
- [ ] No secrets in code

### Rust

- [ ] `cargo fmt --check` ext
- [ ] `cargo clippy --all-targets --all-features -- -D warnings` ext
- [ ] `cargo test --all-targets --all-features` ext
- [ ] `cargo check --all-targets --all-features` ext
- [ ] `trybuild` compile-fail tests pass where type-state/affine APIs are claimed

### General

- [ ] Markdown linted (`npx markdownlint "**/*.md"`)
- [ ] No large files added accidentally
- [ ] No sensitive data in commits

## Feedback Categories

When providing code review feedback:

| Category | Description | Action |
| ---------- | ------------- | -------- |
| **Critical** | Must fix before merge | Blocks PR |
| **Important** | Should fix, may block | Review required |
| **Suggestion** | Nice to have | Won't block |
| **Nitpick** | Style preference | Optional |

## References

- [Project Conventions](../../../../.agents/AGENTS.md)
- [Security Checklist](./security_checklist.md)
