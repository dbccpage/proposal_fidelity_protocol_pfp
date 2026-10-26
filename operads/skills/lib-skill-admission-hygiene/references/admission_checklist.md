# Skill Admission Checklist

## Identity

- [ ] Directory name == frontmatter `name` ext
- [ ] Description has triggers and anti-triggers
- [ ] `version` present and bumped on behavior change
- [ ] `authority_effect_ceiling: None` ext

## Governance

- [ ] Constraints section links `_shared/constraints.md` ext
- [ ] No self-certification / promotion language
- [ ] No git-gate bypass instructions
- [ ] Mirrored to `.claude/skills`, `.codex/skills`, `.agents/skills` (identical bytes)

## Security

- [ ] No hardcoded secrets
- [ ] Network calls documented
- [ ] Untrusted data handling stated if network I/O
- [ ] No silent `curl | sh` ext

## Quality

- [ ] Related Skills section accurate
- [ ] Output schema / receipt shape documented
- [ ] Minimal tests named under `omega_engine_py/tests_mvp/` ext

## Provenance

- [ ] External inspiration cited as pattern-only (if any)
- [ ] No bulk third-party skill dump

## Human gate

- [ ] Operator sign-off recorded
- [ ] `admission: admitted` only after sign-off

Clean scan ≠ admitted. AuthorityEffect always None.
