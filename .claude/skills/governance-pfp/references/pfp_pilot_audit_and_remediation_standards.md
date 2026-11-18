# PFP Pilot Audit Findings, Vulnerability Vectors & Remediation Standards

**AuthorityEffect:** None.  
**Governing Context:** `pfp`, `operations`
**Reference Commit:** `df84a59644c2a6837756273ccedd7b1233525407` (Audit Date: October 10, 2026)

---

## 1. Audit Scope & Executive Summary

A comprehensive census and forensic audit was conducted across the active pilot estate at commit `df84a596`:
- **Reviewed Identities:** 338 registered or related entries across active 5-artifact results (75), migration register (57), additional top-level specifications (26), Demo 4 challenges (143), legacy demos (22), and foundational registers (5).
- **Python Corpus:** 1,260 tracked Python files under `pilots/` (including 886 files outside test directories).
- **Probing Suite:** 39 focused unit tests and 9 targeted offline probes (P01–P09).

### Core Audit Verdict
> The pilots do not meet qualification criteria. Historical runs cannot establish model problem-solving performance due to systematic answer leakage in the runner, permissive type coercions, unverified cache reuse, incomplete replay catalogs, and unsafe cost accounting.

---

## 2. Ten Primary Vulnerability Vectors (F01–F10)

| Finding ID | Severity | Failure Mode | Root Cause in Codebase | Remediation Gate |
|:---|:---|:---|:---|:---|
| **F01** | P1 (Critical) | **Answer Leakage in Prompts** | `live_evaluator.py:255` appends answer examples (`answer: 3`, prime lists, determinants) directly into prompts; 26 seeds (`pilot_00049`–`00074`) encode `output` identical to expected answers. | Zero Answer Disclosure Gate: 0 answer tokens in prompt payloads. |
| **F02** | P1 (Critical) | **Permissive Grading & Type Coercion** | `extract_and_evaluate` coerces values with `int()`/`bool()`, accepting `3.9` as `3`, truncated primes, and `true` as `1`. Unregistered checkers pass via generic fallback. | Malformed Response Refusal Gate: fractional or untyped values evaluate to `REFUSED`. |
| **F03** | P1 (Critical) | **Unsafe Cost Accounting & Retry Undercounting** | Missing `usage.cost` defaults to zero; multi-attempt retries are recorded as single calls; matrix runners bypass pre-dispatch reservations. | Fail-Closed Budget Gate: missing cost halts with `UNRECONCILED_COST`. |
| **F04** | P1 (Critical) | **Stored Answer Bypasses of Domain Gates** | 26 `PFP-DEMO-*` checkers compare outputs to stored answers instead of computing real cochains, coboundaries, holonomy, or dual witnesses. | Domain Evaluator Gate: candidate potential vectors and dual witnesses required. |
| **F05** | P1 (Critical) | **Tampered Cache Acceptance** | `live_evaluator.py:363` trusts cached mode/status flags; modifying raw answers to `999` still returns cached `ACCEPTED`. Stored responses cite different models from specs. | Cryptographic Replay Gate: raw byte SHA-256 mismatch invalidates cache. |
| **F06** | P2 (Major) | **Duplicated Orchestration Across Pilots** | 23 repeated helper AST groups (atomic writes, digest calculations, budget gates) duplicated across pilot files; 18 files make direct HTTP calls. | Deduplication Gate: shared infrastructure consolidated into PFP application. |
| **F07** | P1 (Critical) | **Incomplete Replay Catalogs & Broken Paths** | `no_llm_catalog.yaml` and `llm_catalog.yaml` absent from estate; CLI startup fails trying to load absent pre-relocation documentation paths. | Catalog Recovery Gate: canonical catalogs generated and registered. |
| **F08** | P1 (Critical) | **Synthetic Pass Rows & Presence Flags** | Track 09 suite emits literal `PASSED` rows from constant dictionaries without evaluator execution; presence flags (`scored`) treated as measurements. | Empirical Measurement Gate: all statuses derived from verified machine receipts. |
| **F09** | P2 (Major) | **Cost Policy Divergence & Unidentified Models** | Budgets range from $0.10 to $5/arm; exploratory unidentified models (`stealth/space-bunny-alpha`) used in runners. | Model Confinement Gate: strictly confined to eligible free-tier / sub-$0.005 OpenRouter routes. |
| **F10/F12** | P2 (Major) | **Permutation Conflation with Independent Trials** | Check-only permutations reusing a single model call reported as independent model experiments. | Permutation Decoupling Gate: single-call variations labeled `PERMUTATION_EVALUATION`. |

---

## 3. The 5-Workstream Preflight Remediation Roadmap

1. **Workstream 1: Ground-Truth Isolation & Seed Sanitization**
   - Refactor prompt assembly in `live_evaluator.py` to eliminate answer schema examples.
   - Sanitize `seed.yaml` files for `pilot_00049` through `pilot_00074` removing pre-populated `output` blocks.
   - Bind `PFP-DEMO-*` checkers to sovereign mathematical verifiers.
2. **Workstream 2: Strict SPK-001 Schema Enforcement & Type Purity**
   - Implement fail-closed Pydantic V2 schema validation on all model responses.
   - Refuse fractional numbers (`3.9`), coerced booleans (`true` for `1`), and untyped structures with `INVALID_RESPONSE_FORMAT`.
   - Unknown checker IDs fail closed with `UNREGISTERED_CHECKER_ID`.
3. **Workstream 3: Fail-Closed Cost Accounting & Retry Recording**
   - Enforce pre-dispatch budget reservations in durable SQLite WAL ledger.
   - Monotonic attempt sequence numbering; halt and lock reservation on missing cost metadata (`UNRECONCILED_COST`).
   - Confine model routes to eligible free-tier or sub-$0.005 OpenRouter candidates.
4. **Workstream 4: Cryptographic Cache Integrity & Replay Manifests**
   - Author `ReplayManifestV1` binding prompt SHA-256, raw response SHA-256, decoding config, checker source digest, and receipt.
   - Replay mode must re-execute checkers on raw bytes; tampered bytes trigger `RECEIPT_DIGEST_MISMATCH`.
   - Excise synthetic pass generators; require genuine evaluator receipts for all tracks.
5. **Workstream 5: Architecture Deduplication & Missing Catalog Recovery**
   - Consolidate repeated AST utility functions into `pfp/infrastructure/helpers/`.
   - Generate and register canonical `no_llm_catalog.yaml` and `llm_catalog.yaml`.
   - Demarcate `PERMUTATION_EVALUATION` from `INDEPENDENT_MODEL_TRIAL`.
