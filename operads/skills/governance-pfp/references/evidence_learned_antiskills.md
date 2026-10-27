# Evidence-Learned Anti-Skills & Verification Gaps

AuthorityEffect: None.

This document records the empirical anti-skills, defect patterns, and operational verification gaps mined from production mutation runs (`symbol_game_mutation_20260903.md`), Strict QA gate receipts (`software_qa_receipt_m5.md`), and W1 hardware gating measurements (`w1_gating_measurements_20260805.md`, `w1_signature_capability_20260806.md`).

---

## 1. Concrete Production Mutation Catalogue (M01–M23)

Replaying the 23-mutant catalogue surfaced 10 critical anti-patterns across runtime, domain, and verification layers:

### Anti-Skill 1: Rule-Set Payload Shuffling (`RULE_SET_PAYLOAD_SHUFFLING`, M01)
- **Defect Pattern:** A producer reorders rules in its payload, which alters the presentation digest and silently downgrades verification from a pinned presentation to `SELF_CONSISTENT_ONLY`.
- **Operational Defense:** Runtime must sort rules unstably before hashing (`rules.sort_unstable()`), ensuring the digest names the mathematical system rather than the wire serialization order.

### Anti-Skill 2: Sealed Receipt Deserialization (`SEALED_RECEIPT_DESERIALIZATION`, M04)
- **Defect Pattern:** Allowing serde or serializers to deserialize sealed execution records (such as `RoundRecord`) enables an untrusted model to forge a receipt with an arbitrary `canonical_digest`.
- **Operational Defense:** Sealed receipts must derive `Serialize` only, never `Deserialize`. Model-authored receipts cannot be re-constituted from wire bytes; receipts must be minted solely by the host execution kernel.

### Anti-Skill 3: Producer Carrier Self-Elevation (`PRODUCER_CARRIER_SELF_ELEVATION`, M05, M08, M09)
- **Defect Pattern:** A producer defines or widens its own carrier to achieve `Terminal.PASS` without binding to the host's pinned carrier; or default carrier authorship defaults upward to `HOST`.
- **Operational Defense:** Runs evaluated against a producer-authored carrier are capped at `SELF_CONSISTENT_ONLY`. Only a run re-derived against a host-authored, digest-pinned carrier may reach `Terminal.PASS`. Default carrier authority must default downward to `PRODUCER`.

### Anti-Skill 4: Whitewashing Unchecked Rows (`UNCHECKED_ROW_WHITEWASHING`, M07)
- **Defect Pattern:** A run with rows the host decider never checked reports `SELF_CONSISTENT_ONLY`, claiming mathematical consistency over uninspected claims.
- **Operational Defense:** Any uncheckable row or open residual forbids self-consistency and must return typed `UNCHECKABLE` or `NEEDS_EVIDENCE`.

### Anti-Skill 5: Case-Insensitive Op & Symbol Injection (`CASE_INSENSITIVITY_INJECTION`, M10, M22)
- **Defect Pattern:** Matching op names or carrier symbols case-insensitively expands the accepted vocabulary, allowing `prove x` or `Alpha` to match `PROVE` or `alpha` while breaking case-sensitive group and signature definitions.
- **Operational Defense:** Vocabulary and symbol checks must be exact, case-sensitive ordinal string matches.

### Anti-Skill 6: Truncating Remainder in Cyclic Groups (`TRUNCATING_REMAINDER_CONFUSION`, M11)
- **Defect Pattern:** Relying on C-family truncating division or non-mathematical modulo yields negative residues (e.g. `-17 mod 5 = -2`), contradicting cyclic group $\mathbb{Z}/n\mathbb{Z}$ semantics.
- **Operational Defense:** Modular reduction must compute the least non-negative residue: `host_value = lhs % modulus` in Python or `((lhs % m) + m) % m` in C/Rust, asserting $0 \le r < m$.

### Anti-Skill 7: Modulo Division by Zero Escaping (`MODULO_ZERO_DIV_ESCAPE`, M12, M13)
- **Defect Pattern:** Evaluating `17 mod 0` raises `ZeroDivisionError`, crashing the evaluation pipeline instead of returning a typed verdict.
- **Operational Defense:** A crash is an implementation defect, not a terminal verdict. Non-positive moduli ($m \le 0$) must return typed `RowOutcome.REFUSED` with refusal code `REFUSAL_STATEMENT_ILL_FORMED`.

### Anti-Skill 8: Unanchored Regex Semantic Bleed (`UNANCHORED_REGEX_SEMANTIC_BLEED`, M15)
- **Defect Pattern:** Omitting terminal anchors (`$`) in grammar regexes allows arbitrary trailing text to validate based on a valid arithmetic prefix (e.g. `REDUCE 17 mod 5 = 2 and pigs fly`).
- **Operational Defense:** All parser patterns must be strictly anchored at both ends (`^...$`).

### Anti-Skill 9: Masking Contradictions as Blind Spots (`CONTRADICTION_MASKED_AS_BLIND_SPOT`, M16)
- **Defect Pattern:** When an arithmetic claim disagrees with the host decider, reporting it as an `UNCHECKABLE` blind spot keeps the hallucination count at zero, generating a misleading clean bill of health.
- **Operational Defense:** If a statement form is decidable and the claimed value differs from the host value, it must be returned as `RowOutcome.CONTRADICTED`.

### Anti-Skill 10: Raw Unicode Glyph Console Crash (`RAW_GLYPH_TERMINAL_CRASH`, M23)
- **Defect Pattern:** Emitting raw mathematical Unicode glyphs directly to stdout on Windows terminals running code page cp1252 causes `UnicodeEncodeError`, turning an execution finding into an unhandled crash.
- **Operational Defense:** Terminal and console printers must serialize through ASCII symbol names or use UTF-8 streams with explicit error handling (`errors="replace"` or encoded character representations).

### Anti-Skill 11: Ghost Stage Elevation (`GHOST_STAGE_ELEVATION`, M24)
- **Defect Pattern:** Titling candidate mathematical realizations with non-existent Genesis stage numbers (e.g. `(Realizes S(18))`) or using $R(S(n))$ / stage-indexed survivor symbols ($s_{18}^{\mathrm{hodge}}$) when Genesis core derivations currently terminate at $S(6)$.
- **Operational Defense:** Candidate models must be titled without $S(n)$ numbers, bridged from $S(6)$ (`candidate_bridge_from: "S(6)"`), declared with `realizes: null`, and denoted with candidate naming ($R_{\mathrm{name}}^{\mathrm{candidate}}(S(6)), s^{\mathrm{name}}$).

### Anti-Skill 12: Fixed-Degree Spectral Distribution Confusion (`SPECTRAL_DISTRIBUTION_CONFUSION`, M25)
- **Defect Pattern:** Asserting that the spectral shadow of a fixed-degree regular graph converges to a Wigner semicircle distribution.
- **Operational Defense:** For fixed-degree $d$-regular graphs ($d \ge 3$), the asymptotic limiting adjacency spectral density is the Kesten–McKay distribution $\rho_d(\lambda) = \frac{d\sqrt{4(d-1)-\lambda^2}}{2\pi(d^2-\lambda^2)}$ on $|\lambda| \le 2\sqrt{d-1}$. Never cite the Wigner semicircle distribution for fixed-degree regular graphs.

### Anti-Skill 13: Unconditional Ramanujan Bound Overclaim (`UNCONDITIONAL_RAMANUJAN_OVERCLAIM`, M26)
- **Defect Pattern:** Stating unconditionally that finite regular graphs satisfy the Ramanujan bound $|\lambda| \le 2\sqrt{q}$.
- **Operational Defense:** Qualify that the Ramanujan bound holds conditionally only for graphs within the Ramanujan class.

### Anti-Skill 14: Infinite Colimit Sequence Presupposition (`INFINITE_COLIMIT_PRESUPPOSITION`, M27)
- **Defect Pattern:** Presupposing an infinite sequence $S(0), S(1), \dots$ or defining $MSS_\infty = \operatorname{Ind-lim} S(n)$ before Genesis has derived those stages.
- **Operational Defense:** Model unbounded symbolic systems as a filtered diagram of admitted finite presentations and candidate extensions $\{P_i, \phi_{ij}\}_{i \in I}$, using injective structure-preserving transition maps.

### Anti-Skill 15: Layer-2 Authority Leak in Cycle Breaking (`CYCLE_BREAK_AUTHORITY_LEAK`, M28)
- **Defect Pattern:** Using `ACTION_FORCE_LIFT` in a Layer-2 mathematical realization to license or force a Genesis core lift, violating `AuthorityEffect: None` and `GenesisEffect: None`.
- **Operational Defense:** Use `ACTION_REQUEST_LIFT` which emits an inert candidate proposal requiring independent host authorization.

### Anti-Skill 16: Unordered Bare Holonomy Bianchi Identity (`UNORDERED_HOLONOMY_BIANCHI`, M29)
- **Defect Pattern:** Presenting a bare unordered product of rotation matrices $\prod_{t \subset c} R_t = I$ as a universal discrete Bianchi identity without dual loop orientation, base-simplex parallel transport, or triangulation scope.
- **Operational Defense:** Formulate the discrete Bianchi identity with an explicit dual loop $\partial c^*$, parallel transport $\mathcal{P}_k$ to a base 4-simplex $\sigma_0^4$, path-ordered multiplication $\vec{\prod}$, and scope exactness to declared minimal closed triangulations.

### Anti-Skill 17: Mock-Only Pilot Theater Disguised as Model Verification (`MOCK_PILOT_THEATER_OVERCLAIM`, M30)
- **Defect Pattern:** Generating directories of "pilots" containing Python validator scripts, mock inputs, and schemas that forbid provider calls (`provider_calls: Annotated[StrictInt, ge=0, le=0] = 0`), marking them `LIVE TRIAL PENDING` while reporting the suite as verified.
- **Harm:** Creates the illusion of empirical protocol validation while testing nothing about actual model behavior, prompt fidelity, dialect parsing, or failure modes.
- **Operational Defense:** Every pilot must either execute live micro-budget model dispatches (< $0.001) with authentic provider receipts in `live_runs/`, or be explicitly labeled as an internal unit test under `tests/unit/`, never a PFP pilot.

---

## 2. Multi-Format Receipt Desynchronization Anti-Pattern

Emitting JSON and Markdown receipts from independent, decoupled runs causes counts to desynchronize silently (e.g. Markdown claiming 18/18 while JSON recorded 23 mutants and a survivor).

**Operational Defense:**
- Multi-format receipts (JSON and Markdown) must be generated by the exact same execution instance during the same process lifetime.
- Both files must carry identical timestamps, commit hashes, mutant counts, and SHA-256 cross-receipt digests.

---

## 3. Five-Field Mutation Custody Standard

Per `techne-mutation-evidence-custody`, every mutation claim must provide five fields to count as evidence:

1. **Target:** Specific file path weakened.
2. **Anchor:** Exact text replaced (must match uniquely; 0 or >1 matches is a setup failure).
3. **Applied:** Exact replacement string applied.
4. **Failures:** Specific test nodes that failed by name.
5. **Restore:** Byte-identical restore proof verified by digest or empty diff.
---

## 2. PFP Pilot Estate Audit Defect Patterns (Anti-Skills 13–22)

Mined from the comprehensive audit review of 338 registered entries and 1,260 pilot files at `df84a596` (October 10, 2026):

### Anti-Skill 13: Prompt-Injected Schema Hints (`PROMPT_INJECTED_SCHEMA_HINTS`, F01)
- **Defect Pattern:** The runner serializes answer examples (`answer: 3`, complete prime lists, determinants, verdicts) into participant prompt schemas, or seeds (`pilot_00049`–`pilot_00074`) pre-populate expected outcome fields directly into input objects.
- **Operational Defense:** Participant prompts must be assembled strictly from task input data and answer-free SPK-001 schemas. Expected answers must never be accessible during prompt compilation (`RULE_PFP_ZERO_ANSWER_LEAKAGE_001`).

### Anti-Skill 14: Permissive Grading Coercion (`PERMISSIVE_GRADING_COERCION`, F02)
- **Defect Pattern:** Grading routines apply loose coercions (`int()`, `bool()`), accepting fractional values (`3.9` as `3`), truncated lists, or coerced booleans (`true` as `1`). Bare JSON without outer SPK-001 wrappers passes through generic fallbacks, and the runner synthesizes unearned model assertions.
- **Operational Defense:** Enforce fail-closed Pydantic V2 schema validation on all model responses before evaluating answers. Fractional numbers, coerced types, and bare payloads evaluate fail-closed to `REFUSED` (`INVALID_RESPONSE_FORMAT`).

### Anti-Skill 15: Unsafe Accounting Fallback (`UNSAFE_ACCOUNTING_FALLBACK`, F03)
- **Defect Pattern:** Missing `usage.cost` metadata defaults to zero spend; multi-attempt retries are collapsed into single call counts; runners bypass pre-dispatch reservations; `:free` model suffixes are assumed to be verified billing receipts.
- **Operational Defense:** Compulsory pre-dispatch ledger holds; monotonic attempt sequence numbering; missing cost or ambiguous timeouts immediately halt dispatch and mark runs `UNRECONCILED_COST`.

### Anti-Skill 16: Stored Answer Echoing replacing Real Evaluators (`STORED_ANSWER_ECHOING_BYPASS`, F04)
- **Defect Pattern:** The 26 `PFP-DEMO-*` checkers route to a generic fallback comparing candidate outputs to `seed.expected_outcome.answer`. Echoing `phi_1: 0` earns acceptance without computing potentials, cochains, or dual circulation witnesses.
- **Operational Defense:** Every task family must bind to a genuine sovereign domain evaluator and require candidate potential vectors, cochains, or witnesses ($d_0^T w = 0, \|w\|_\infty \le 1$).

### Anti-Skill 17: Blind Cache Acceptance without Replay Binding (`BLIND_CACHE_REUSE_TAMPER`, F05)
- **Defect Pattern:** Cached results are trusted without re-evaluating raw bytes; mutating a cached raw answer still returns cached `ACCEPTED`. Stored responses cite different models from specifications.
- **Operational Defense:** Require `ReplayManifestV1` cryptographically binding prompt SHA-256, raw response SHA-256, decoding configuration, and checker source digests. Mutated raw bytes trigger `RECEIPT_DIGEST_MISMATCH`.

### Anti-Skill 18: Reusable Orchestration Scattering (`REUSABLE_ORCHESTRATION_SCATTERING`, F06)
- **Defect Pattern:** 23 repeated AST helper groups (atomic writes, digest calculations, budget gates) are duplicated across pilot directories, and 18 pilot files make direct raw HTTP calls.
- **Operational Defense:** Consolidate reusable transport, persistence, and budget accounting into `pfp/infrastructure/helpers/` while strictly keeping independent mathematical judges separate.

### Anti-Skill 19: Missing Replay Route Discovery (`MISSING_REPLAY_ROUTE_DISCOVERY`, F07)
- **Defect Pattern:** Catalog files (`no_llm_catalog.yaml`, `llm_catalog.yaml`) are missing, and CLI entrypoint imports resolve non-existent pre-relocation documentation paths.
- **Operational Defense:** Generate and register canonical catalogs; ensure all CLI entrypoints resolve through canonical package imports with zero broken documentation paths.

### Anti-Skill 20: Synthetic Pass Row Emission (`SYNTHETIC_PASS_ROW_EMISSION`, F08)
- **Defect Pattern:** Emitting literal `PASSED` statuses from constant dictionaries (as in Track 09) without executing a model or checker; treating inventory presence flags (`scored`) as empirical proof.
- **Operational Defense:** Every reported status must be backed by an executed machine receipt. Static dictionary emissions and presence flags are classified as inventory metadata, never empirical evidence.

### Anti-Skill 21: Model Budget Policy Divergence (`MODEL_BUDGET_POLICY_DIVERGENCE`, F09)
- **Defect Pattern:** Permitting broad per-arm spending ($0.10–$5/arm) or unidentified models (`stealth/space-bunny-alpha`) in governed campaigns.
- **Operational Defense:** Confine governed matrix runs to verified free-tier or sub-$0.005 OpenRouter candidates under an explicit $0 spend ceiling by default.

### Anti-Skill 22: Permutation Conflation with Independent Trials (`PERMUTATION_CONFLATION`, F10/F12)
- **Defect Pattern:** Check-only permutations or relabelings reusing a single model call are reported as independent model experiments.
- **Operational Defense:** Explicitly partition the experiment registry: single-call check variations are labeled `PERMUTATION_EVALUATION`; only independently rendered requests or fresh provider dispatches count as `INDEPENDENT_MODEL_TRIAL`.
