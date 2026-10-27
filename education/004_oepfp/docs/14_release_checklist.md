---
documentation_contract: symbol-game-documentation/v1
title: "Repository Release Discipline & Publication Checklist"
kind: operational-contract
audience:
  - maintainers
  - release-engineers
  - coding-agents
status: active
maturity: canonical
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - education/documentation/004_oepfp/docs/14_release_checklist.md
source_revision: c419cc6beb
prerequisites: []
verification: none at the 2026-10-20 pin (the former test education/the_symbol_game/tests/test_documentation_route_canonical.py is not present)
aliases:
  - 03_oss_packaging.md
related:
  - README.md
last_verified: 2026-10-20
verification_scope: named scripts and files checked for existence only
---

# 14. Repository Release Discipline & Publication Checklist

**Document Class:** Operational Release Governance  
**AuthorityEffect:** None. Definitive pre-release gates, secret scrubbing rules, and receipt-claim bindings.

---

## 1. Pre-Release Hard Gates

No package, paper deposit, or open-source release may proceed without satisfying all six hard gates:

1. **Clean Local Build & Test Gate:**
   - The entire package builds locally without warnings or unhandled exceptions.
   - All targeted unit, regression, and property tests pass in fresh runtime environments (`COMPUTED`).
   - Zero whole-suite unconstrained test sweeps; test execution is targeted and verified.

2. **Strict Credential & Secret Scrubbing:**
   - Scan all source files, documentation, commit messages, and sample configs for API keys, tokens, bearer secrets, and local paths.
   - Assert that no `.env` or credential files are tracked in the Git index.

3. **Explicit Dual-Licensing Declarations:**
   - The repository declares explicit licenses: code components licensed under standard open-source terms (e.g. Apache-2.0); monographs, curriculum, and documentation licensed under explicit content licenses (e.g. CC-BY-4.0).
   - Ensure `LICENSE` and `NOTICE` files are present at the root and unambiguously delineate code versus prose terms.

4. **Receipt-Bound README Claims:**
   - Every headline claim, benchmark score, or capability assertion in the `README` must link directly to an immutable, reproducible evidence receipt (`SHA-256` content-addressed).
   - Numerical claims without receipt backing are strictly forbidden.

5. **Front-Loaded Honest Limitations:**
   - Ship bounded domains, finite carriers, and conjecture statuses directly in the primary `README` or documentation introduction.
   - Do not bury failure modes, unproved transfer bridges, or carrier restrictions in fine print.

6. **Ten-Minute Quickstart Verification:**
   - A newly onboarded user or agent must be able to install and execute a minimal example in under 10 minutes.
   - The quickstart must demonstrate both a **valid acceptance receipt** and an immediate **typed refusal** on a contradictory input.

---

## 2. Release Receipt Envelope Verification

Prior to tagging or publishing a release:
- Verify that working-tree bytes match the committed release manifest (`verify_release.py --check`). No tracked file named `verify_release.py` exists at the 2026-10-20 pin; use the release tool of the package being released and record its exact command.
- Verify that `SHA256SUMS` and `MANIFEST.sha256` match all tracked files bit-for-bit.
- Assert that no source files contain UTF-8 Byte Order Marks (BOM).
