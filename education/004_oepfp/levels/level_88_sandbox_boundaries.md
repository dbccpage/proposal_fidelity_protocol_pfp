---
documentation_contract: symbol-game-documentation/v1
title: "The Symbol Game Level 88: Process Sandbox Boundaries & System Call Fences"
kind: grammar-reference
level: 88
epoch: "Epoch VIII"
domain: "Platform Security"
game_edition: "Trans-Base Arena"
spec_status: specified
schema_status: proposed
checker_status: candidate_interface
fixture_status: not_run
runtime_status: not_implemented
authority_effect: "None"
evaluator_module: "SecurityGovernanceModule"
evaluator_contract: "SandboxPolicyContract"
reachable_terminal_statuses:
  - ExactRepair
  - StabilizedSurvivor
  - OpenObstruction
  - LiftLicenseNeeded
  - Refused
  - Invalid
source_paths:
  - education/documentation/004_oepfp/levels/meta_00_symbol_game_foundations.md
  - education/documentation/004_oepfp/levels/meta_01_symbol_game_historical_curriculum.md
  - education/documentation/004_oepfp/levels/meta_02_symbol_game_pfp.md
  - education/documentation/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md
---

# The Symbol Game Level 88: Process Sandbox Boundaries & System Call Fences

**AuthorityEffect:** None.  
**Level:** Level 88 | **Epoch:** Epoch VIII | **Domain:** Platform Security  
**Game Edition:** `Trans-Base Arena`  
**Board Carrier:** `OS process containment profiles (seccomp-bpf, Landlock, restricted namespaces, Windows app containers)`  
**Fuel Budget:** `8 turns` | **Permitted Moves:** `ASSERT, CUT, VERIFY`  
**Primary Domain Error Code:** `ERR_EXECUTION_POLICY_DEFECT`  
**Evaluator Module:** `SecurityGovernanceModule` (`SandboxPolicyContract`)  

**Source status (checked 2026-10-20 at `c419cc6beb`):** specification only. No evaluator named `SecurityGovernanceModule` or contract `SandboxPolicyContract`, no packet schema for this level and no level referee exist in source (`git grep` over `*.rs`, `*.py`, `*.lean`, `*.yaml` and `*.json`). The `REFEREE:` lines below state specified outcomes, not recorded runs, and `carrier_digest` values are placeholders, not computed digests. The terminal names follow [`CodaTerminal`](../../../../engine/crates_rs/core_state/src/coda_gtla_protocol.rs).

---

## 1. Game Board & Conceptual Arena

Level 88 establishes the Proposal Fidelity Protocol (PFP) arena for **Process Sandbox Boundaries & System Call Fences** within the Platform Security bounded context. The game operates on the formal discrete 5-tuple board state:

$$\mathcal{S}_{88} = \Big( \mathcal{C},\; \mathcal{R}_{\text{active}},\; \mathcal{D}_{\text{evaluator}},\; \mathcal{H}_{\text{trace}},\; \mathcal{I}_{\text{invariants}} \Big)$$

- **Carrier ($\mathcal{C}$):** `OS process containment profiles (seccomp-bpf, Landlock, restricted namespaces, Windows app containers)`. Pinned and immutable upon arena initialization.
- **Active State ($\mathcal{R}_{\text{active}}$):** Current assigned valuations, configurations, and candidate structures configured on the carrier.
- **Evaluator Register ($\mathcal{D}_{\text{evaluator}}$):** Instantiation of `SecurityGovernanceModule` via `SandboxPolicyContract` calculating level-specific objective defect metrics.
- **History Trace ($\mathcal{H}_{\text{trace}}$):** Specified append-only record of proposed turn vectors, referee decisions and state digests (the runtime packet sealer `core-canonical-v1` is not RFC 8785).
- **Invariants ($\mathcal{I}_{\text{invariants}}$):** Fuel ceiling ($T \le 8$), boundary protection masks, and non-mutation constraints.

### Conceptual Arena Scope
Verifying host process containment boundaries, system call whitelists, and filesystem isolation.

---

## 2. Proposer & Checker Protocol

The Proposal Fidelity Protocol separates untrusted generation from deterministic verification:

```text
┌──────────────────────────┐         Candidate Proposal 88        ┌──────────────────────────┐
│     Untrusted Neural     ├────────────────────────────────────────►│    Deterministic Host    │
│    Proposer (Player)     │◄────────────────────────────────────────┤      Checker (Rust)      │
└──────────────────────────┘          Typed Terminal Receipt         └────────────┬─────────────┘
                                                                                  │
                                             Emits Immutable Verification Receipt ▼
                                                                     ┌──────────────────────────┐
                                                                     │   Residual Loss Ledger   │
                                                                     │  (Zero Authority Mints)  │
                                                                     └──────────────────────────┘
```

1. **Untrusted Proposer Role:** Submits candidate move proposals formatted as typed wire envelopes. Proposer outputs carry zero ambient trust and cannot mutate board configuration directly.
2. **Deterministic Referee Role:** Specified for a native Rust referee (none is implemented for this level at the source pin); verifies carrier boundary compliance, applies permitted moves (`ASSERT, CUT, VERIFY`), evaluates `SandboxPolicyContract`, and decrements fuel.
3. **Turn Fuel & Budget:** Proposer is allotted exactly **8 turns** to resolve candidate defects or achieve an admitted stable survivor. Exhaustion without resolution triggers terminal status `OpenObstruction`.
4. **Syntax Firewall & Domain Separation:** Raw tokens are evaluated against the carrier allowlist and packet JSON schema. Any malformed syntax, schema mismatch, undeclared symbol, or carrier boundary breach is intercepted immediately by the syntax firewall and routed to terminal status `Invalid` (`ERR_CARRIER_TOKEN_INVALID` / `ERR_SCHEMA_MISMATCH`). The domain referee evaluates only structurally valid proposals; domain mathematical errors (such as `ERR_EXECUTION_POLICY_DEFECT`) are emitted exclusively by `SandboxPolicyContract`.

---

## 3. Packet Envelope & Wire Schema

Proposals at Level 88 are specified as JSON envelopes for the proposed (not yet implemented) `sg_packet_level_88` schema:

```json
{
  "schema_id": "sg_packet_level_88_platform_security",
  "task_data": {
    "level": 88,
    "epoch": "Epoch VIII",
    "domain": "Platform Security",
    "carrier_digest": "blake3:carrier_level_88..."
  },
  "protected_boundary": {
    "immutable_slots": [
      "carrier",
      "fuel_ceiling",
      "zero_relation_fences"
    ],
    "max_fuel": 8
  },
  "budget": {
    "turn_fuel_remaining": 8,
    "max_repair_ops": 3
  },
  "candidate_payload": {
    "policy_digest": "sha256:policy_sandbox_default_v1",
    "operation_type": "open_path",
    "target_path": "c:/Users/a343o/source/repos/the_symbol_game/src/x.py",
    "syscall": "NtOpenFile",
    "resource_limits": {
      "max_memory_mb": 256,
      "max_cpu_percent": 50
    },
    "sandbox_action": "Allowed"
  },
  "witness_data": {
    "replay_trace": [
      "init",
      "step_1"
    ],
    "evaluation_receipt": "blake3:receipt_level_88"
  }
}
```

### AST Representation
```rust
pub struct SandboxPolicyPayload {
    pub policy_digest: String,
    pub operation_type: String,
    pub target_path: String,
    pub syscall: String,
    pub resource_limits: ResourceLimits,
    pub sandbox_action: String,
}
```

---

## 4. Evaluator Module & Objective Metrics: SecurityGovernanceModule

Referees evaluate candidates through `SandboxPolicyContract`:

Referees audit process execution requests against containment profiles:
1. **Path Boundary Check:** Verifies that target files reside strictly within declared sandbox directory roots.
2. **Syscall Whitelist Audit:** Confirms that requested system calls are permitted by active kernel filters.
3. **Resource Bound Audit:** Validates that memory and CPU allocations do not exceed sandbox limits.
4. **Interception Assertion:** Confirms that unauthorized operations are deterministically intercepted and blocked.

### Formal Admission Criteria
- **`ExactRepair` Admission Criterion:** Target path is within declared workspace, syscall is whitelisted in policy, resource usage is within limits, and observed action matches declared policy rules.
- **`StabilizedSurvivor` Admission Criterion:** Verified sandbox containment record recorded under zero authority.

---

## 5. Terminal Dispositions & Replayable Test Vectors

The Proposal Fidelity Protocol defines exactly eight canonical terminal statuses:

| Status Code | Canonical Definition | Reachability in Level 88 & Referee Disposition |
|:---|:---|:---|
| `ExactRepair` | Residual resolved or goal state satisfied within fuel budget. | **Reachable.** Candidate admitted; verification receipt emitted. |
| `StabilizedSurvivor` | Persistent non-erasable invariant / cocycle admitted under license. | **Reachable.** Admitted survivor recorded; zero authority minted. |
| `OpenObstruction` | Unresolved defect persists; fuel budget exhausted without resolution. | **Reachable.** Candidate held; terminal disposition recorded. |
| `OracleNeeded` | Resolution requires an external verification oracle outside this stage. | Unreached in local evaluation. |
| `LiftLicenseNeeded` | Scoped exhaustion reached; qualifies for Context Extension Calculus (CEC). | Reachable upon certified same-level exhaustion. |
| `Refused` | Domain invariant violation, forbidden move, or ungrounded operation. | **Reachable.** Immediate rejection with domain error `ERR_EXECUTION_POLICY_DEFECT`. |
| `Invalid` | Malformed syntax, JSON schema mismatch, or undeclared token/carrier breach. | **Reachable.** Intercepted at syntax firewall with `ERR_CARRIER_TOKEN_INVALID`. |
| `InfrastructureFailure` | Resource exhaustion, timeout, or host environment error. | Unreached in standard execution. Zero authority minted. |

### Replayable Test Vectors

- **Valid Minimal Candidate:**
  ```text
  PROPOSAL: {"level": 88, "carrier_match": true, "move": "ASSERT"}
  REFEREE:  ACCEPT -> Status: ExactRepair (goal state certified / defect resolved)
  ```

  **Reproducibility gap (2026-10-20):** This vector carries no operation, path or policy, so the checks in section 4 cannot be run on it; the `ExactRepair` line is a stated expectation only. The section 3 schema example also omits the sandbox root list and the syscall allowlist behind `policy_digest`, and it gives resource limits but no measured usage, so the path, syscall and resource checks cannot be completed from it. Its `target_path` is a host-specific absolute path; a repository-relative path would keep the example portable.

  **Worked check (2026-10-20):** The domain negative vector reports `sandbox_action: "Allowed"` for `C:\Windows\System32\cmd.exe`, a path outside any workspace root, so an allowed action violates the path boundary check and `Refused` follows.

- **Domain Negative Counterexample (Domain Violation):**
  ```text
  PROPOSAL: {"level": 88, "carrier_match": true, "target_path": "C:\\Windows\\System32\\cmd.exe", "sandbox_action": "Allowed"}
  REFEREE:  REFUSED -> Refusal Code: ERR_EXECUTION_POLICY_DEFECT, Status: Refused
  ```

- **Syntax / Carrier Firewall Counterexample (Syntax Violation):**
  ```text
  PROPOSAL: {"level": 88, "carrier_match": false, "injected_symbol": "Ω_UNPINNED"}
  REFEREE:  INVALID -> Refusal Code: ERR_CARRIER_TOKEN_INVALID, Status: Invalid
  ```

---

## 6. Claim Hygiene Quadrant

1. **What this supports:**
   - Verification of process filesystem containment and system call whitelisting under declared OS sandbox policies.
   - A proposed PFP packet envelope, `SandboxPolicyContract` evaluation rules, and typed referee error dispatch.
2. **What this does not support:**
   - Does not prove absolute immunity against kernel-level privilege escalation or hardware speculative execution bugs.
   - Does not grant operational authority or claim global truth for passing candidate proposals.
3. **The narrowest defensible claim:**
   - Certifies that attempted operations comply with the declared containment profile and kernel filters.
4. **Next test needed:**
   - Execute sandbox boundary violation probes against the container execution harness.
