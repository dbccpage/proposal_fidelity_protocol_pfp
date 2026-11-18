# Detailed definition: Intelligence Community Agency Boundaries (1)

**AuthorityEffect:** None.

Parent: [Intelligence Community Agency Boundaries](../../../../../rules/architecture/rl_intelligence_community_agency_silo_prohibition.md). Load for the matching predicate, not every task.

# Architecture Rule: Intelligence Community Agency Silo Prohibition (`RL_ARCH_IC_001`)

**AuthorityEffect:** None.

## Mandate

The Intelligence Community directory (`_ic/`) represents the single centralized clearing house for all durable intelligence, run receipts, event streams, and epistemic telemetry across the engine.

Its top-level directory structure is strictly partitioned into the canonical 23 agencies modeled after the American Intelligence Community canon (`governance/_types/intelligence_community.yaml` v2.0.0):

### Tier 1 — Executive Clearinghouse
1. `odni`: Office of the Director of National Intelligence (executive narrative streams, unified trace, cross-discipline packets, briefings).

### Tier 2 — National Agencies
2. `cia`: Central Intelligence Agency (all-source external research, scholarly literature retrieval, citation graph mining).
3. `nsa`: National Security Agency (signals intelligence, cryptographic verification, host telemetry, OEOS kernels).
4. `dia`: Defense Intelligence Agency (evolutionary stress testing, defensive robustness, adversarial challenges).
5. `nro`: National Reconnaissance Office (code coverage reconnaissance, static inspection, architectural surveillance).
6. `nga`: National Geospatial-Intelligence Agency (topological mapping, OMC DAG visualizations, simplicial networks).
7. `fbi`: Federal Bureau of Investigation (forensic code analysis, internal anomaly investigations, security audit logs).
8. `inr`: Bureau of Intelligence and Research (scholarly analysis, paper review provenance, academic gate verification).
9. `nctc`: National Counterterrorism Center (threat correlation, adversarial pattern fusion, watchlist deltas).
10. `ncsc`: National Counterintelligence and Security Center (insider risk scoring, exfiltration detection, boundary attestation).
11. `ncpc`: National Counterproliferation Center (containment of self-replicating and runaway agent capability).

### Tier 3 — Departmental / Service Elements / Affiliates
12. `dea`: Drug Enforcement Administration (supply-chain tracing, poisoned dependency interdiction, seizure manifests).
13. `dhs`: Department of Homeland Security (boundary ingress filtering, untrusted input screening, prompt-injection firewall).
14. `cg`: Coast Guard Intelligence (boundary patrols, live stream interception, littoral telemetry, interdiction logging).
15. `treasury`: Department of the Treasury (financial forensics, token and cost accounting, budget anomaly detection).
16. `doe`: Department of Energy (compute substrate attestation, cluster integrity, power and thermal budget custody).
17. `army`: United States Army Intelligence and Security Command (ground-truth corpus engineering, dataset curation, terrain modeling).
18. `oni`: Office of Naval Intelligence (deep-context navigation, recursion depth sounding, long-context charting).
19. `af`: Department of the Air Force (wide-area reconnaissance sweeps, latency profiling, coverage gap detection).
20. `marines`: Marine Corps Intelligence (expeditionary first-in reconnaissance, edge deployment, expedition packaging).
21. `cdc`: Centers for Disease Control and Prevention (epistemic immune system, antibody catalogs, pathological tracking).
22. `darpa`: Defense Advanced Research Projects Agency (experimental game engines, symbol games, Adversary bouts).
23. `nara`: National Archives and Records Administration (permanent record custody, historical telemetry `_archive/`, raw `harvest/`).

## Invariants

1. **No Ad-Hoc Silos:** Creating directories at the root of `_ic/` other than the canonical 23 agencies is strictly prohibited and fails domain validation (`IntelligenceCommunity`).
2. **No Duplicate Collection:** Multiple agencies must not collect or persist duplicate telemetry; data must be collected once by the authoritative agency and cross-referenced.
3. **Typed Configuration:** The canonical agency definitions must be loaded from `governance/_types/intelligence_community.yaml` and validated by `IntelligenceCommunity`.
