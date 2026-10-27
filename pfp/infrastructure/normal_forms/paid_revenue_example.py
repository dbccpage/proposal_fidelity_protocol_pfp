# ==============================================================================
# Specification: 01-bqnf-orders-paid-revenue.md
# ==============================================================================
"""
================================================================================
01-bqnf-orders-paid-revenue.md
================================================================================

# Demo 01: BQNF Orders / Paid Revenue

Status: Mechanization target.

Source relation:

```sql
Orders(order_id, customer_id, status, amount, updated_at)
```

Observer:

```sql
paid_revenue_by_customer(customer_id, paid_revenue)
```

View:

```sql
SELECT customer_id, SUM(amount) AS paid_revenue
FROM Orders
WHERE status = 'paid'
GROUP BY customer_id;
```

Boundary:

```text
relations: Orders
attributes: customer_id, status, amount
predicate: status = 'paid'
group: customer_id
aggregate: SUM(amount)
```

BQNF checklist:

1. boundary declared
2. delta computable
3. quotient class computable
4. repair image declared
5. terminal route declared

Required outcomes:

| Case | Required terminal |
|---|---|
| Supported `SUM` delta with before/after status, amount, and customer evidence | `Repair` |
| Missing CDC status / missing predicate evidence | `Invalidate` |
| Unrelated column update, e.g. `updated_at` only | `Preserve` |
| `MAX` without extremum witness | `Unsupported` or `Lift` |

Non-claims:

* Does not prove source data is true.
* Does not authorize side effects.
* Does not certify representation transport.

AuthorityEffect: None.
"""

import json
import os

from pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR
from typing import Any, Dict

from pfp.domain.normal_forms.bqnf_validator import BqnfValidator

# Load the CDC events from JSON
DATA_PATH = NORMAL_FORMS_DIR / "data" / "cdc_events.json"


def evaluate_bqnf(case: Dict[str, Any]) -> Dict[str, Any]:
    return BqnfValidator.evaluate_case(case)


def main():
    print("================================================================================")
    print("DEMO 01: BQNF (Boundary Quotient Normal Form) - Change Stream Evaluation")
    print("================================================================================")

    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    with open(DATA_PATH, "r") as f:
        cases = json.load(f)

    for i, case in enumerate(cases, 1):
        print(f"\n--- Running Case {i}: {case.get('description')} ---")
        print("Input Event:")
        print(json.dumps(case.get("event"), indent=2))

        result = evaluate_bqnf(case)

        print("\nOutput Certificate:")
        print(json.dumps(result, indent=2))
        print("-" * 80)


if __name__ == "__main__":
    main()
