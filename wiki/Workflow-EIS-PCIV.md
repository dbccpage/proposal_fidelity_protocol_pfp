# EIS Two-Signal & PCIV Operational-Quotient Workflows (`eis_two_signal_charpoly_v1`, `pciv_quotient_obligation_v1`)

- **DAG Nodes:** `EXECUTABLE:eis_two_signal_charpoly_v1`, `EXECUTABLE:pciv_quotient_obligation_v1`
- **Specification:** `dag/benchmark/eis_pciv_workflows.py`
- **Runner Integration:** `dag/benchmark/reference_runner.py`
- **Supporting Modules:** `eis/use_cases/two_signal_regulation.py`, `pciv/use_cases/transitive_immunity.py`, `pciv/infrastructure/verified_projection.py`, `dag/benchmark/source_custody.py`
- **Prepared Unexecuted Campaign:** `dag/benchmark/eis_pciv_pilot_20261110/manifest.json` (`qm-eis-pciv-pilot-20261111`, 5 arms, `500,000` microUSD ceiling, `100,000` microUSD per run)
- **Retrospective Blind Corpus Evaluation:** `dag/benchmark/eis_pciv_historical_evaluation.json` (`24` historical runs, `USD 0.055614` settled historical spend, `0` new live dispatches)

---

## 1. Mathematical & Architectural Scope

### `eis_two_signal_charpoly_v1` (2-Stage EIS Matzinger Two-Signal Workflow)

1. **Stage 1 (`charpoly_propose`, max `1,500` output tokens):** Requests the monic characteristic polynomial $\det(\lambda I - H(J, \Delta, K))$ over $\mathbb{Q}[J, \Delta, K]$ against the public affine Hamiltonian matrices.
2. **Inter-Stage EIS Two-Signal Gate (`evaluate_eis_charpoly_stage`):**
   - **Thymic Central Tolerance (`ThymusGate` + `NormalizedMatcher`):** Screens candidate surface detectors against `ThymusSelfPanelBuilder` so benign rational formatting quirks (`"2/2"`, `"+4/2"`, `"-4/1"`, explicit `"+0"` terms, permuted monomials, Markdown code fences) reduce value-preservingly via `charpoly_wire` (`disposition = "DIAGNOSTIC_NORMALIZED"` or `"TOLERATED"`) without triggering autoimmune refusal.
   - **Host Danger Signal (`Signal2Danger` from `observer_id = "HOST"`) & Guard Activation Custody:** Enforces signal independence (`TwoSignalRegulatorV1`, refusing `TWO_SIGNAL_COLLAPSE` if Signal 2 originates from `"MODEL"` or overlaps Signal 1's locus). Malformed payloads (`MALFORMED_PAYLOAD`) or polynomials refuted on the exact 125-point Cartesian grid $\{-2, -1, 0, 1, 2\}^3$ (`REPLAY_FAILURE`) halt execution (`status = "eis_two_signal_refused"`) before Stage 2 is billed. In `two_signal_regulation.py`, `HostHealthReceiptV1` is explicitly scoped as a declared record unless issued and authenticated via `HostHealthAuthority` (in-process HMAC-SHA256 + single-use nonce refusing forged, altered, foreign, or replayed records with `HOST_HEALTH_UNVERIFIED`), `Ab09_CHSHBoundRange` enforces only the physical Tsirelson range $|S| \le 2\sqrt{2}$ (reporting LHV $|S| \le 2$ and Bell violation $|S| > 2$ without refusing physical mixed states such as $S = 0$), and `source_custody.py` pins the 72-file runtime import closure across `eis/`, `pciv/`, `operads/`, and `ops/` so regulation changes invalidate stale workflow manifests before dispatch.
3. **Stage 2 (`solve`, max `14,500` output tokens):** Receives the unchanged `seed_prompt.txt` bytes plus the normalized intermediate polynomial context (`final_answer_certified: False`) to synthesize all five requested QM sections.
4. **OpenRouter Upper-Quote Reservation (`deepseek/deepseek-v3.2 @ atlas-cloud/fp8`):** `43,169 + 48,109 = 91,278 <= 100,000` microUSD whole-run ceiling.

### `pciv_quotient_obligation_v1` (1-Stage PCIV Operational-Quotient Workflow)

1. **Pre-Dispatch Operational Quotient (`OperationalWorkflowQuotientV1`):** Validates stage port-colour compatibility (`Seed -> Wire -> Answer`), collapses adjacent idempotent duplicate stages (`6` candidates reduced to `4` canonical normal-form representatives) while keeping noncommuting stage orders (`normalize -> check` vs `check -> normalize`) distinct, and computes `PopulationPolicyV1` 60/30/10 (`Front` / `Unmeasured` / `Baseline`) reserve quotas.
2. **Protected-Span Byte Fencing (`ProtectedSpanEvolutionV1`):** Verifies byte-for-byte preservation of `dag/benchmark/seed_prompt.txt` (`SHA-256: 9941ab91...`) across governed header evolution, refusing any overlapping span mutation (`PROTECTED_SPAN_VIOLATION`).
3. **Single-Call Synthesis (`solve`, max `16,000` output tokens):** Matched 16,000-token ceiling against public-seed obligations only (`48,679 <= 100,000` microUSD upper quote).

---

## 2. Offline Validation & Retrospective 24-Run Blind Corpus Findings

- **Offline Unit, Challenger & Mutation Verification:** Verified across `eis/tests/unit/`, `pciv/tests/unit/test_transitive_immunity_and_projection.py`, `dag/benchmark/test_eis_pciv_workflows.py`, `dag/benchmark/test_source_custody.py`, `dag/benchmark/test_evaluate_eis_pciv_corpus.py`, and Categories `0–22` of `dag/benchmark/attack_mutation_registry.py` (`73/73` in-scope adversarial mutations killed across `83` fixtures, `7/7` positive controls accepted, `2` out-of-predicate semantic survivors and `1` unresolved degeneracy case explicitly retained).
- **Retrospective Blind Corpus Audit (`dag/benchmark/eis_pciv_historical_evaluation.json`):**
  - On `qm-charpoly-20261110:qm_charpoly_checked_v1:000` Call 000, `charpoly_wire` reduces all `/1` denominators (`"-4/1"`, `"-16/1"`, `"4/1"`, `"8/1"`, `"16/1"`) that caused `RATIONAL_NONCANONICAL` and exposes the underlying mathematical defect (`NONMONIC_LEADING_COEFFICIENT`), while Call 001 exhausted `2,400` tokens on non-JSON prose.
  - Conflict-graph MIS (`ObservationSupportPolicyV1`) promotes 4 cross-model defect classes (`support_count >= 3`) to `Provisional` while collapsing single-scaffold failure clusters to `Candidate` (`support_count <= 2`).
  - **Negative / Boundary Finding on Coarse Public Prose Watchers:** Unnormalized prose regexes exhibit LaTeX false rejections (`0/24` passing `10/10`), and at the highest observed blind tier (`7/10`), two short `gpt-4o-mini` runs (`4/100` post-hoc) collide in the same public-watcher fiber as `qm-model-repaired-20261110:direct:000` (`83/100` post-hoc), causing blind cost-Pareto selection to prefer the cheaper `4/100` run.

---

## 3. Claim Hygiene & Explicit Limitations

1. **What this supports:** In offline tests and retrospective replay over the 24 frozen historical receipts, Thymic value-preserving normalization over structured wires eliminates `/1` syntax refusals without masking non-monic polynomial errors, fixed-point lineage taint and hash-chained crash replay remediate `SYS-PCIV-008` and `SYS-PCIV-009`, and coarse unnormalized prose watchers suffer measurable split-fibre accuracy collisions (`4/100` vs `83/100`).
2. **What this does not support:** Any live accuracy, cost, or latency improvement of `eis_two_signal_charpoly_v1` or `pciv_quotient_obligation_v1` over `coverage_first_direct_v1` (live campaign `qm-eis-pciv-pilot-20261111` is prepared and unexecuted), any certification of downstream QM derivations (`final_answer_certified` is `False`), or any general multi-task transfer claim (`F-RES-09`).
3. **Narrowest defensible claim:** Under the declared assumptions on the frozen single-seed benchmark, EIS two-signal wire regulation and PCIV operational quotienting / lineage custody are executable within the `100,000` microUSD per-run cap and address documented syntax-autoimmunity, single-pass taint, and unverified-projection failure modes in offline and retrospective checks without certifying final prose answers.
4. **Next test needed:** Authorize and execute the 5-arm paired campaign `dag/benchmark/eis_pciv_pilot_20261110/manifest.json` (`<= USD 0.50` cap) followed by a multi-seed held-out split with multiplicity correction (`F-RES-09`).
