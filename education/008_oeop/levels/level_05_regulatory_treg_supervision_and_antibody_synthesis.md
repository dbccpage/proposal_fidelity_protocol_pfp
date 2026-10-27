---
documentation_contract: symbol-game-documentation/v1
title: "OEWAS Level 05: Regulatory Treg Supervision and Autoimmune Protection"
kind: mathematical-reference
level: 5
status: active
maturity: production
claim_status: verified
authority_effect: "None"
source_paths:
  - operads/domain/operad/treg.py
  - education/documentation/9_workflows_agents_skills_was_multicategories_and_operads/atlas/13_spec_polarized_operad_and_anti_skills.md
last_verified: 2026-10-01
---

# OEWAS Level 05: Regulatory Treg Supervision & Autoimmune Protection

**AuthorityEffect:** None. Complete mathematical and architectural reference for the Regulatory T-Cell (`Treg`) supervisor, autoimmune toxicity index $T$, tolerance threshold $\tau = 40\%$, and `OperadTregReceipt`; no operational authorization is conferred.

---

## 1. Executive Intuition: The Autoimmune Failure Mode

In multi-agent systems equipped with adversarial red teams and inhibitory anti-skills, a dangerous pathology frequently emerges: **autoimmune execution paralysis**.

When anti-skills become too aggressive or overly broad, they begin flagging benign, working code as violations. If these anti-skills act as blocking gates, the development workflow grinds to a halt:
- Every proposed PR is rejected by an over-sensitive linter.
- Developers and agents waste 100% of their compute attempting to satisfy conflicting, tautological constraints.
- The system collapses into self-inflicted deadlock.

In mammalian biology, **Regulatory T-cells (Tregs)** actively monitor the immune response and suppress autoreactive effector T-cells before they destroy healthy tissue. In the Sentinel Engine, this regulatory function is performed by the **Operad Treg Supervisor**.

---

## 2. Mathematical Model: Toxicity Index and Tolerance Threshold

The Treg supervisor models suppression reliability using exact rational arithmetic ($\mathbb{Q}$):

1. **Total Suppressions ($N_{\mathrm{suppressed}}$):**
   The total number of times an anti-skill has intervened to block or refuse an operation.
2. **Confirmed Danger ($N_{\mathrm{danger}}$):**
   The number of times the blocked artifact was empirically confirmed to contain a true defect (e.g. verified by test failure or compiler crash).
3. **Unconfirmed Suppressions ($U$):**
   The number of times an operation was blocked without verified defect evidence:
   $$U = N_{\mathrm{suppressed}} - N_{\mathrm{danger}}$$
4. **Autoimmune Toxicity Index ($T$):**
   The proportion of unconfirmed, spurious suppressions:
   $$\boxed{T = \frac{U}{N_{\mathrm{suppressed}}} = \frac{N_{\mathrm{suppressed}} - N_{\mathrm{danger}}}{N_{\mathrm{suppressed}}} \in \mathbb{Q} \cap [0, 1]}$$
5. **Tolerance Threshold ($\tau$):**
   The maximum permissible false-suppression rate, set to:
   $$\tau = \frac{2}{5} = 40\%$$
6. **Sample Floor ($N_{\min}$):**
   To avoid premature downgrading from small sample sizes, no action is taken until at least $N_{\min} = 3$ suppressions have been observed:
   $$N_{\mathrm{suppressed}} \ge N_{\min} = 3$$

> [!NOTE]
> **Why the Sample Floor is Mandatory:** If an anti-skill triggers on its very first trial and that suppression is unconfirmed, its raw ratio is $T = 1/1 = 100\%$. Without a sample floor, every newly introduced gate would be instantly demoted on its first false alarm. Requiring $N_{\mathrm{suppressed}} \ge 3$ ensures statistical stability.

---

## 3. Code Implementation Walkthrough: `treg.py`

The supervisor lives in [`operads/domain/operad/treg.py`](../../../../operads/domain/operad/treg.py):

```python
class OperadTregSupervisor:
    """Supervises operadic anti-skill operations to prevent autoimmune execution lock."""

    def __init__(
        self,
        tau_threshold: Fraction = Fraction(2, 5),
        min_suppressions: int = 3,
    ) -> None:
        self.tau_threshold = tau_threshold
        self.min_suppressions = min_suppressions
        self._suppressed_counts: dict[str, int] = {}
        self._danger_counts: dict[str, int] = {}
        self._downgraded_operations: set[str] = set()

    def record_operation_step(
        self,
        operation_name: str,
        suppressed: bool,
        danger_confirmed: bool,
    ) -> OperadTregReceipt | None:
        """Record an operation step and check whether autoimmune toxicity threshold is exceeded."""
        self._suppressed_counts[operation_name] = (
            self._suppressed_counts.get(operation_name, 0) + (1 if suppressed else 0)
        )
        self._danger_counts[operation_name] = (
            self._danger_counts.get(operation_name, 0) + (1 if (suppressed and danger_confirmed) else 0)
        )

        total_suppressed = self._suppressed_counts[operation_name]
        if total_suppressed < self.min_suppressions:
            return None

        unconfirmed = total_suppressed - self._danger_counts[operation_name]
        toxicity = Fraction(unconfirmed, total_suppressed)

        if toxicity > self.tau_threshold and operation_name not in self._downgraded_operations:
            self._downgraded_operations.add(operation_name)
            treg_id = f"TREG-OP-{hashlib.sha256(f'{operation_name}:{toxicity}'.encode()).hexdigest()[:12]}"
            reason = (
                f"Operad anti-skill {operation_name} toxicity {toxicity} strictly exceeds threshold {self.tau_threshold}. "
                "Authority downgraded from BLOCKING_GATE to DIAGNOSTIC_ONLY."
            )
            receipt_body = {
                "authority_effect": "None",
                "downgraded_authority": "DIAGNOSTIC_ONLY",
                "reason": reason,
                "target_operation": operation_name,
                "tau_threshold": str(self.tau_threshold),
                "toxicity_index": str(toxicity),
                "treg_id": treg_id,
            }
            canonical_bytes = json.dumps(receipt_body, sort_keys=True, separators=(",", ":")).encode("utf-8")
            receipt_hash = hashlib.sha256(canonical_bytes).hexdigest()
            return OperadTregReceipt(
                treg_id=treg_id,
                target_operation=operation_name,
                downgraded_authority="DIAGNOSTIC_ONLY",
                toxicity_index=toxicity,
                tau_threshold=self.tau_threshold,
                reason=reason,
                receipt_hash=receipt_hash,
            )
        return None
```

---

## 4. The `OperadTregReceipt` Value Object

When an operation exceeds the tolerance threshold $\tau$, the supervisor synthesizes an immutable cryptographic receipt:

```python
@dataclass(frozen=True, slots=True)
class OperadTregReceipt:
    """Receipt emitted when an operadic anti-skill is downgraded."""
    treg_id: str
    target_operation: str
    downgraded_authority: str
    toxicity_index: Fraction
    tau_threshold: Fraction
    reason: str
    receipt_hash: str
    authority_effect: str = "None"
```

### The Downgrade Effect: `BLOCKING_GATE` $\to$ `DIAGNOSTIC_ONLY`

- **Before Downgrade:** The anti-skill acts as a `BLOCKING_GATE`. If it trips, the entire pipeline aborts with a typed refusal.
- **After Downgrade:** The anti-skill is demoted to `DIAGNOSTIC_ONLY`. Its findings are recorded in audit ledgers as advisory warnings, but it can no longer block workflow execution.

---

## 5. Concrete Scenario: Quarantining an Over-Aggressive Linter

1. An agent introduces a strict anti-skill `anti-redundant-import`.
2. Over 3 pull requests, the anti-skill blocks all 3 PRs ($N_{\mathrm{suppressed}} = 3$).
3. Human/oracle review checks the code:
   - Case 1: True defect (unused import that broke a circular dependency). Danger confirmed ($N_{\mathrm{danger}} = 1$).
   - Case 2: False positive (import required for Sphinx type annotations). Danger unconfirmed.
   - Case 3: False positive (re-export in `__init__.py`). Danger unconfirmed.
4. The supervisor computes:
   $$U = 3 - 1 = 2 \implies T = \frac{2}{3} \approx 66.7\%$$
5. Because $T = \frac{2}{3} > \tau = \frac{2}{5}$ and $N \ge 3$, the supervisor automatically emits `OperadTregReceipt` and downgrades `anti-redundant-import` to `DIAGNOSTIC_ONLY`.
6. Normal development unblocks immediately without human panic.

---

## 6. Verification and Local Unit Tests

To verify Treg supervisor functionality and mathematical fractions locally:

```powershell
# Retired: OEWAS tests/unit/test_operad_treg_supervisor.py has no successor file under operads.
```

### The Level 05 Governance Invariants
- **INV-05-01 (Exact Rational Fractions):** Toxicity $T$ and threshold $\tau$ must be computed using `fractions.Fraction`; floating-point math is strictly forbidden.
- **INV-05-02 (Sample Floor Enforcement):** No operation may be downgraded with fewer than $N_{\min} = 3$ observed suppressions.
- **INV-05-03 (Diagnostic Demotion):** Downgrading demotes authority to `DIAGNOSTIC_ONLY`; it does not delete the anti-skill from historical audit custody.
- **INV-05-04 (Authority Ceiling):** All Treg receipts enforce `authority_effect: "None"`.
