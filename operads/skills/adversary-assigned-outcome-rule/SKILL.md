---
name: adversary-assigned-outcome-rule
description: "Count all assigned task outcomes."
metadata:
  core-arity: "1"
  core-contract: "operads/catalog/contracts/v1/lessons/adversary-assigned-outcome-rule.json"
  core-contracts-digest: "sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3"
  core-generated: "oewas.typed-capability.v1"
  core-kind: "rule"
  core-residual: "unknown"
  core-source-colours: "[\"Code\"]"
  core-target-colour: "Audit"
---

# adversary-assigned-outcome-rule

Generated guidance; edit the canonical typed contract and instruction resource.

# Review procedure

Before reporting a success rate, state the assigned unit, eligibility population, all terminal counts and retry policy. Check that every assigned allowed task remains in the primary denominator. Preserve conditional rates only with their narrower label.

## Digested lesson

Source: `_ic/nara/historical/oewas007/research/inputs/pfp_second_pass_20261008/integration_evidence.md` @ `32454fda2b42454792f6d49ec22e7304a4e30ba6` (sha256:0b9987b888e3b0202d3c571b583d543b48e26e47d39df6108cce3a5c2750f778).

Source excerpt (evidence to inspect):

```text
One solved + 99 allowed-task valid refusals yields S/(S+F)=100% but S/N=1%.
```

**Failed Claim:** Success among success/failure judgments is success among all assigned allowed tasks.

**Counterexample:** With one solved task and 99 allowed-task refusals, conditional success is 100% while assigned-task success is 1%.

**Cause:** Refusal, unknown and infrastructure outcomes disappeared from the conditional denominator.

**Correction:** Use solved / prespecified assigned allowed tasks as the primary success rate; retain refusal, unknown and infrastructure strata and keep retries under their original assignment.

**Verification:** Read historical integration finding D2 and its exact arithmetic example. This digest does not rerun the old native probes or assert that current scoring code still has the reported defect.

**Applicability:** Benchmark, pilot and Adversary campaign reports claiming task-success rates.

**Exceptions:** A conditional success/failure rate is legitimate when explicitly labelled supplementary. Refusal-required tasks need their own declared success contract and population.

## Guidance contract

**Trigger:** Before publishing a task-success summary

**Predicate:** Primary success denominator includes every prespecified assigned allowed task exactly once, with all terminal strata retained.

**Response:** Repair the denominator or label the report incomplete; do not invent missing outcomes.

Ordered signature: `(candidate: Code) -> result: Audit`.

Contracts: `sha256:b001073b031beccde6ad42883e2af5fc4efa04d205c7648b4f029f1c33ce50a3`.

Source admission: `Unadmitted`. AuthorityEffect: None.
This on-demand instruction package does not install an ambient rule, execute a detector or activate an antibody.
