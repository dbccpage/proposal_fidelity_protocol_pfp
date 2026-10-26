# Genesis Claim Hygiene, Evidence Taxonomy & PFP Standards

AuthorityEffect: None.

This reference formalizes evidential stratification, domain falsifiers, and Proposal Fidelity Protocol (PFP) late-stage standards.

## 1. Four Evidential Strata (Mandatory Labeling)

Every formal claim, theorem citation, and implementation excerpt must be tagged with exactly one grade:

1. **`NATIVE SEALED`:** Mechanized and proved in sealed core pin (`sealed-derivation-v1` at `3100c4e`) over native carriers (`Basic.Regime`, `stepE`, `min_responses`).
2. **`SEALED SUPPLEMENTARY`:** Inside sealed repo, but distinct calculus or analogue (`PrimitivePassage`, `TraceAlgebra`, `Represented`, `ObsDescent`). Never conflate with native stepping.
3. **`POST-SEAL THEOREM`:** Rigorous Lean 4 theorem landing after sealed tag (`Rounds.lean`, `MinimalityF.lean`). Must cite actual baseline commit.
4. **`FINITE COMPUTATION / TESTED`:** Executable Python code or combinatorial replay (`iso.py`, `candidates.py`). Carries no general proof; declare finite bounds.

## 2. Five Prohibited Derivation Anti-Patterns

1. **Fictitious Files / Identifiers:** Never cite nonexistent files (`Supply.lean`, `AdmitDatum.lean`) or invented functions (`step_supply`, `find_minimal_responses`).
2. **Analogy Elevation:** Countermodels (e.g. `incomplete_search_false_alarm`) prove false alarms in truncated search; they do not prove abstract theorems over general spaces.
3. **Evidence Epoch Mixing:** Never combine sealed pin counts with post-seal theorem censuses.
4. **Serialization Hype:** Deterministic `json.dumps(sort_keys=True)` mitigates drift; never call it RFC 8785 JCS or claim "total immunity".
5. **Open Soundness Demarcation:** If an algorithm lacks a general Lean proof (e.g. `CL-ISO-SOUND` for `iso.canonical`), mark it **OPEN**; do not inflate finite tests.

## 3. Universal Board Carrier & Evaluator Decoupling

The Symbol Game board state is the discrete 5-tuple:
$$\mathcal{S} = (\mathcal{C}, \mathcal{A}, \mathcal{H}, \mathcal{I}, \mathcal{B})$$
($\mathcal{C}$ = Carrier, $\mathcal{A}$ = Active State, $\mathcal{H}$ = History Trace, $\mathcal{I}$ = Invariants, $\mathcal{B}$ = Budget).

- **Anti-Pattern (Forced Cohomology):** Cohomology formulas ($\Phi_1 = \|[c]\|, \Xi = \Phi_1 + \Gamma_2$) apply only to carriers with declared chain complexes ($C^0 \to C^1 \to C^2$).
- **Prohibited Smuggling:** Never inject cochain formulas or Hodge projections into non-cochain domains (SLSA provenance, JSON-Schema gates, task routing, compiler bisimulations).
- **Dedicated Evaluators:** Non-cochain arenas use typed evaluators: `SchemaValidation`, `ProvenanceCheck`, `CapabilityCheck`, `SimulationCheck`, `MutationCheck`.

## 4. PFP Invariants: Receipts & Capability Gating

1. **6-Tuple Tool Call Receipt (Level 84):** Syntactic validity does not prove correct execution. Tool rows require the verified receipt:
   $$(\text{tool\_id},\; \text{schema\_digest},\; \text{argument\_digest},\; \text{execution\_id},\; \text{result\_digest},\; \text{exit\_status})$$
2. **Capability Gating (Level 85):** Multi-agent routing requires:
   $$\operatorname{scope}_{\rm delegated} \subseteq \operatorname{scope}_{\rm principal}, \qquad \operatorname{required}(task) \subseteq \operatorname{capabilities}(agent)$$

## 5. Automated Claim Hygiene Scanner & Four-Pillar Schema

All bout runners, benchmarks, and summaries must enforce:
1. **Forbidden Words (Zero-Tolerance):** `proves`, `guarantees`, `mathematically verifies`, `fundamentally`, `true intelligence`, `impossible`, `universal`, `flawless`, `perfectly`, `clearly`, `obviously`, `simply`, `merely`, `weaponized`.
2. **Four-Pillar Summary Contract:**
   - `supports`: Scoped empirical or finite verification findings.
   - `what_it_does_not_support`: Explicit boundaries and non-claims.
   - `narrowest_defensible_claim`: Minimal exact statement justified by receipts.
   - `next_test_needed`: Subsequent falsification or stress test required.
