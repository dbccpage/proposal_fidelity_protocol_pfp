---
kind: law
authority_effect: None
status: live
owner: techne-council
---
# Enforcement Gate Pattern (single source of truth)

Applied by `nomos-law-contract-manager`, `techne-code-principal-architect`,
`auto-obstruction-hunter`, and `meta-law-contract-enforcer`. The required
`.agents/`, `.claude/`, `.codex/`, and `.grok/` host mirrors are admitted copies.
Do not create an independent inline or out-of-band copy; that is
`DUPLICATE_RULE`.

## The failure this exists to catch

A declaration nothing enforces. The originating 2026-08-26 run reported this
snapshot:

| layer | declared | unenforced |
| --- | ---: | ---: |
| Rust traits | 259 | 109 have methods and no implementor |
| math contracts with a `rust_binding` | 172 | 113 state obligations nothing exercises |
| generated contract images | 412 | 2 mocks were the only law bindings |
| `rust_file_contract` `file:` fields | 63 | 57 pointed at paths that did not exist |
| skills in `.agents/skills` | 145 | 22 are provisional with zero contractive runs |

These figures are context, not output of the gates named below. They require an
independent corpus replay before reuse as current estate facts. Every reported
case looked finished. A contract binding a renamed module, a trait declaring
five methods with no implementor, and a skill declaring an operation with no
evidence are the same defect wearing different syntax.

## The gate

A gate reads a declaration and checks the code against it. Two working instances:

- `omega_engine/crates_rs/tests/omega_contracts/rust_file_contract_gate.rs` --
  `forbidden_substrings`, `required_substrings`, and `required_tests` checked
  against the bound source.
- `omega_engine/crates_rs/tests/omega_contracts/math_contract_gate.rs` -- module
  resolution, declared symbols, and `rust_binding.required_tests` for
  `omega.contract.v1`.

## The four rules

**1. The baseline may only shrink, and it stores findings, not a count.**

A count lets one violation silently replace another. Store the finding text
verbatim, fail on anything new, and fail equally when a listed entry stops
reproducing -- otherwise a fixed problem sits in the file looking like work
still to do. `math_contract_baseline.txt` went 157 to 85 under this rule with
zero substitutions.

**2. Assert reach, not just absence of findings.**

A gate that resolves nothing passes trivially. Both gates assert they reached
their corpus (`enforced * 10 >= seen * 9`, `bound > 100`). Before that check
existed, 57 of 63 file contracts resolved to nothing and the gate was green.

**3. Prose obligations need a named discharge or an explicit open status.**

`negative_tests` reading "add/sub of unequal shapes must be rejected" states an
obligation and checks nothing. `rust_binding.required_tests` names the test that
discharges it. If an obligation has no mechanical discharge, record it as an
explicit open obligation with an owner or disposition; do not omit it from the
ledger. A named gap is honest evidence. An unnamed gap is invisible debt. See
`math/basic_matrix.contract.yaml` and `math/density_matrix.contract.yaml`, then
verify the current obligation-to-test mapping rather than relying on historical
counts.

**4. Do not ban a word that appears in the account of its own absence.**

`forbidden_substrings` is a substring match with no notion of context. Banning
`tolerance` fired on a comment explaining why there is no tolerance; `HashMap`
fired on a comment explaining why a `BTreeMap` is used; `pub payload` fired on
the unsealed draft struct whose fields are public by design. Each time the gate
was right and the ban was wrong. Prefer a structural check. If a substring
check is unavoidable, narrow it to the construct actually forbidden. Preserve
useful source commentary; never delete explanatory context solely to make a
substring gate pass. Contract `laws` may carry additional rationale but are not
a substitute for readable source.

## Auditing a gate's output

Parse the structured file; do not pattern-match it. Auditing this corpus with
regex windows produced three confident wrong numbers in one sitting: 98 phantom
missing tests from a window bleeding across YAML sections, `Ca` and `Autho`
reported as dropped symbols from a truncated list, and four tests called
assertion-free because a 700-character window cut before the assertion. All three
would have condemned correct work.

## Authority

A green gate is `AuthorityEffect: None`. It establishes that declarations and
code agree, never that either is right.
