# Change Log: The Authority Gap

## 2.1.0 — 2026-10-16 (prepared edition)

Replaced the false necessity claim in former Lemma 7.1 with Proposition 3.1: zero NGD characterizes acceptance soundness on the evaluated support. Added Example 3.4, where NGD is zero but global evaluation cannot factor through the boundary. Restricted backlog accounting to sustained actual completions and distinguished cohort, window, and throughput ratios. Replaced unsupported deployment claims with explicit contracts and proof limits.

Revised mathematical scope and presentation; introduced the canonical Markdown math spine with persistent equation IDs and occurrence bindings; regenerated TeX, math-preserving text, and PDF through ordered formula checks. The build records file digests and does not assign mathematical truth. Existing public deposit identifiers are retained as prior-record references, not asserted as identifiers for this prepared edition.

## 005_the_authority_gap (Zenodo Record 20684965)

**Authority Nonclaim:** This change log records structural, theoretical, and editorial revisions. It carries no operational authority or institutional standing.

---

### 2026-10-09 — Proved rows checked in Lean 4 and Python

The three rows that remain proved are CLM-005-007, CLM-005-010, and CLM-005-011. `lean4/AuthorityGap.lean` formally mechanizes the hidden-bit and unconditional gluing counts, the positive natural-number backlog, the zero-stock share identity, and the boolean exactness-fraud rule, including the scoped-authorization boundary. `code/proved_rows.py` calls `calculate_ngd`, `calculate_backlog_accumulation`, and `evaluate_exactness_fraud_criterion` on those finite instances. `test_proved_rows_call_shipped_checkers` calls that replay. Definitions, policy rules, and operational rules are unchanged. This is not a new Zenodo deposit.

---

### Version 2.0.2 (2026-10-08)

- **Boundary Sufficiency Separation & Two-Condition Composition Lemma (§7.3, Appendix A):**
  - Formulated the rigorous distinction between **Proposal Continuation Sufficiency** ($P(\gamma_B \mid \gamma_A) = P(\gamma_B \mid b)$), **Evaluator Information Factorization** ($\Pr(E_G = 1 \mid \gamma_A, \gamma_B) = \Pr(E_G = 1 \mid b, \gamma_B)$), and **Local Evaluator Soundness & Decomposition** ($E_A \land E_B \implies E_G$).
  - Refuted the claim that evaluator information sufficiency implies local evaluator decomposition via counterexample ($E_A \equiv 1, E_B \equiv 1, E_G \equiv 0$ yields $0=0$ factorization but $100\%$ gluing defect $\mathrm{NGD} = 1.0$).
  - Formulated Lemma 7.1 (Two-Condition Composition Lemma) establishing that zero NGD requires both evaluator information factorization and local-to-global soundness.
  - Corrected Appendix A Glossary definition of Boundary Sufficiency to reflect the two distinct conditions.
- **Cumulative Verified-Share Arithmetic & Cohort vs. Window Metrics (§9.2–9.4):**
  - Corrected cumulative verified-share formula with zero initial stock from $r_V / (r_G + r_V)$ to $V(t) / (U(t) + V(t)) = r_V t / r_G t = r_V / r_G$, illustrating with rates $r_G = 10$ and $r_V = 3$ producing verified share $3/10$.
  - Formalized cumulative verified share dilution from high-trust initial conditions ($V(0) > 0, U(0) \approx 0$) toward asymptotic limit $r_V / r_G$.
  - Separated cohort eventual verification fraction $\mathrm{ACR}_{\text{cohort}} = N_{\mathcal{C}}(\text{eventually verified}) / |\mathcal{C}|$ from time-window completion ratio $\mathrm{ACR}_{\text{window}} = N_{\mathcal{W}}(\text{verified}) / N_{\mathcal{W}}(\text{proposals})$, noting that processing delays and queueing dynamics cause window counts to diverge from instantaneous throughput.
- **Packet Integrity Contract & Scoped Authorization Rules:**
  - Bound `Proposal.context` into canonical length-delimited byte records across `AuthorityPacket.compute_canonical_binding_record` and `TraceRecord.canonical_bytes`.
  - Added explicit declared rules for scoped authorizations in `Terminal`: `tolerated_unverified_scope` and `tolerated_refusal_reasons`, binding them in Layer 5 and enforcing fail-closed rejection of un-waived unverified scope or evaluator refusals.
  - Added unit test coverage for context tampering detection and scoped unverified scope/refusal waiver rules.
- **Metric Input Validation & Undefined Ratio Handling:**
  - Hardened `calculate_ngd` to reject non-boolean flags (such as string `"false"` or floats) with explicit `TypeError`.
  - Hardened `calculate_acr_rate` to reject floats (such as `.1, .3`) and non-rational inputs, enforcing exact `Fraction` arithmetic.
  - Hardened `calculate_acr` to reject floats and booleans, and return an explicit undefined state (`None`) when proposal denominator is zero ($0/0$).
- **Deposit Integrity, Version Harmonization & Packaging:**
  - Synchronized version `2.0.2` (dated 2026-10-08) across `the_authority_gap.md`, `README.md`, `zenodo_metadata.json`, `pyproject.toml`, and claim registers.
  - Rebuilt deterministic release ZIP archive and regenerated `MANIFEST.sha256` and `SHA256SUMS`.
  - Verified deposit integrity with `verify_deposit.py --test code/tests/test_authority_gap.py` and `tools/rebuild_release.py --check`.

---

### Version 2.0.1 (2026-10-07)

- **Code License Harmonization:**
  - Standardized `LICENSE-CODE` to Apache-2.0, aligning the license file with `README.md`, `zenodo_metadata.json`, and source headers in `mod_authority_gap_core.py`.
- **Trace Custody & Canonical Binding:**
  - Replaced ambiguous string concatenation in `TraceRecord.create` with length-delimited canonical encoding (`canonical_encode_string`, `canonical_encode_sequence`) binding proposal payload and trace fields without delimiter collisions.
  - Added `compute_canonical_binding_record` and `compute_binding_hash` on `AuthorityPacket` binding all seven layers.
  - Enforced inspectable `replay_receipt` and declared institutional officer requirements for authorized terminal status.
- **Verification Scope & Refusal Accounting:**
  - Replaced broad "valid descent verified" verdict with a scoped structural consistency result (`"Structural consistency check passed under declared observer."`), reserving full verification claims for external execution and authority checks.
  - Corrected `Residual.is_exact` to require `len(refusal_reasons) == 0`.
  - Updated `calculate_ngd` to return `None` when local-green count is zero, reflecting the undefined conditional rate.
  - Added capacity validation to `calculate_acr` ensuring verified packet count cannot exceed generated proposal count.
  - Expanded pytest test suite from 7 to 12 passing unit tests covering encoding ambiguity, trace tampering, refusal reasons, undefined NGD, and ACR capacity bounds.
- **Manuscript Rate Arithmetic & Dependency Hygiene:**
  - Corrected single-verifier backlog accumulation rate in §9.3 to $1,000 - 0.1 = 999.9$ packets per minute.
  - Clarified §9.2 by distinguishing absolute backlog size $U(t)$, unverified backlog share, and cumulative verified share under explicit initial conditions.
  - Removed obsolete reference to Part III code-path re-audit in §13.2.
  - Pinned stable version identifiers (`v1.0.0`) for external monograph dependencies (Paper 000, 016, 020) across Sections 4, 7, and `docs/references.md`.
  - Harmonized `docs/lean_claim_map.md` to map all 14 claims in `the_authority_gap_claim_ledger.md` (`CLM-005-001` through `CLM-005-014`).
- **Package Synchronization:**
  - Synchronized package version to 2.0.1 across `the_authority_gap.md`, `zenodo_metadata.json`, `pyproject.toml`, `README.md`, `the_authority_gap_claim_ledger.md`, `docs/descriptions.md`, and `docs/lean_claim_map.md`.

---

### Version 2.0.0 (2026-10-07)

- **Repository Canonicalization & Clean Architecture:**
  - Canonicalized under `001_finite_obstruction_calculus/005_the_authority_gap`.
  - Harmonized with Zenodo Record `20684965` (DOI: `10.5281/zenodo.20684965`).
- **Jargon & House Language Eradication:**
  - Removed internal esoteric terminology and compliance notes.
  - Replaced internal governance headers with standard academic frontmatter and explicit nonclaims.
  - Standardized mathematical appendix terminology to Layered Mathematical Architecture ($\Omega_\partial, \Omega_{\mathbb{A}}, \Omega_\chi, \Omega_{\mathfrak{O}}, \Omega_\kappa, \Omega_{\Lambda\Omega}$).
  - Truncated internal repository development notes (Part III) from public monograph, relocating formal claim statuses into the standalone `the_authority_gap_claim_ledger.md`.
- **Claim Hygiene & Hype Prohibition:**
  - Screened entire manuscript against claim hygiene rules, replacing promotional verbs with defensible, scoped descriptions.
- **Executable Verification Code:**
  - Added reference Python package under `code/mod_authority_gap_core.py` modeling the 7-layer stack, Negative Gluing Defect ($NGD$), Authority Coverage Ratio ($ACR$), and Exactness Fraud refutation using exact rational arithmetic (`fractions.Fraction`).
  - Added comprehensive test suite under `code/tests/test_authority_gap.py` (all tests passing).
- **Package Deposit Standards:**
  - Added `pyproject.toml`, `zenodo_metadata.json`, `docs/descriptions.md`, `docs/references.md`, `README.md`, `LICENSE`, `LICENSE-CODE`, and `verify_deposit.py`.

---

### Version 1.3 (2026-06-13)

- Release candidate packaging for initial Zenodo upload (Record 20684965).
- Numbered public references, added fraud/legal analogy fences.

---

### Version 1.0 (2026-05-23)

- Initial strategic draft of the Authority Gap and Counterfeit Descent framework.
