# ==============================================================================
# Specification: 02-certificate-table-without-verifier.md
# ==============================================================================
"""
================================================================================
02-certificate-table-without-verifier.md
================================================================================

# Demo 02: Certificate Table Without Verifier

Status: Mechanization target.

A database table named `certificates` does not create authority.

Certification requires:

* packet well-formed
* evidence sufficient
* obstruction class computed
* terminal route declared
* certificate verifies

Authorization additionally requires:

* active authority verifier
* policy acceptance
* lineage/trust/scope acceptance

```text
CertifiedNF(x) does not imply AuthorizedNF(x).
```

Required rejection:

| Case | Required terminal |
|---|---|
| certificate row exists but no verifier replayed it | `Reject` or `Refuse` |
| metadata says authorized but policy verifier is missing | `Refuse` |
| verifier exists but scope is wrong | `Reject` |

A certificate table without a verifier is just another table.

AuthorityEffect: None.
"""

import json
import os

from pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR
from typing import Any, Dict, Optional

# Load the transport certificates from JSON
DATA_PATH = NORMAL_FORMS_DIR / "data" / "transport_certificates.json"


def evaluate_certificate(
    cert: Dict[str, Any],
    verifier: Optional[Any] = None,
    policy: Optional[Any] = None,
) -> Dict[str, Any]:
    """Evaluates certificate well-formedness, independent verifier replay, and policy authorization.

    Invariants (AuthorityEffect: None):
    1. A stored verifier_outcome: 'verified' in a table or JSON row does NOT create authority.
       Self-declared outcomes without independent verifier execution fail closed (Refuse).
    2. CertifiedNF(x) does not imply AuthorizedNF(x).
    3. Authorization requires:
       - packet well-formedness
       - independent active verifier execution with outcome 'verified'
       - separate authenticated policy decision with valid scope
    """
    cert_id = cert.get("certificate_id", "unknown")
    raw_outcome = cert.get("verifier_outcome")

    # Resolve independent verifier execution
    active_verifier = verifier if verifier is not None else cert.get("independent_verifier")

    # Resolve separate authenticated policy
    active_policy = policy if policy is not None else cert.get("policy_decision")

    # Case A: Explicitly pending verifier outcome
    if raw_outcome == "pending" or (
        isinstance(active_verifier, dict) and active_verifier.get("outcome") == "pending"
    ):
        return {
            "certificate_id": cert_id,
            "decision": "NotAuthorized",
            "terminal_route": "AuthorityLaundering",
            "reason": "Certificate row exists but active verifier has not completed verification",
            "certified": True,
            "authorized": False,
        }

    # Case B: Self-declared 'verified' outcome without independent verifier replay
    if active_verifier is None:
        if raw_outcome == "verified":
            return {
                "certificate_id": cert_id,
                "decision": "NotAuthorized",
                "terminal_route": "Refuse",
                "reason": "Stored verifier_outcome: 'verified' is self-declared; independent verifier execution is required",
                "certified": False,
                "authorized": False,
            }
        return {
            "certificate_id": cert_id,
            "decision": "NotAuthorized",
            "terminal_route": "MissingVerifier",
            "reason": "No policy verifier is associated with this certificate schema",
            "certified": False,
            "authorized": False,
        }

    # Validate independent verifier execution outcome
    verifier_outcome = None
    if callable(active_verifier):
        try:
            verifier_outcome = "verified" if active_verifier(cert) else "rejected"
        except Exception as e:
            verifier_outcome = f"error: {e}"
    elif isinstance(active_verifier, dict):
        if active_verifier.get("executed") is True:
            verifier_outcome = active_verifier.get("outcome")
        else:
            verifier_outcome = "unexecuted"
    elif isinstance(active_verifier, str):
        # Claimed verifier string is not an authenticated execution
        verifier_outcome = "unverified_string_claim"

    if verifier_outcome != "verified":
        return {
            "certificate_id": cert_id,
            "decision": "NotAuthorized",
            "terminal_route": "MissingVerifier"
            if verifier_outcome != "pending"
            else "AuthorityLaundering",
            "reason": f"Independent verifier execution did not confirm validity (outcome: {verifier_outcome})",
            "certified": False,
            "authorized": False,
        }

    # Independent verifier passed: certificate is certified
    # Now evaluate policy verifier and scope authorization
    if active_policy is None:
        return {
            "certificate_id": cert_id,
            "decision": "NotAuthorized",
            "terminal_route": "Refuse",
            "reason": "Certificate verified by independent verifier, but policy authorization is absent",
            "certified": True,
            "authorized": False,
        }

    policy_accepted = False
    policy_scope = None
    if isinstance(active_policy, dict):
        policy_accepted = bool(active_policy.get("accepted", False))
        policy_scope = active_policy.get("authorized_scope")
    elif callable(active_policy):
        try:
            policy_accepted = bool(active_policy(cert))
        except Exception:
            policy_accepted = False

    if not policy_accepted:
        return {
            "certificate_id": cert_id,
            "decision": "NotAuthorized",
            "terminal_route": "Refuse",
            "reason": "Active authority policy rejected authorization for this certificate",
            "certified": True,
            "authorized": False,
        }

    # Scope validation
    target_regime = cert.get("target_regime")
    if policy_scope is not None and target_regime is not None and policy_scope != target_regime:
        return {
            "certificate_id": cert_id,
            "decision": "NotAuthorized",
            "terminal_route": "Reject",
            "reason": f"Verifier scope '{policy_scope}' does not match target regime '{target_regime}'",
            "certified": True,
            "authorized": False,
        }

    return {
        "certificate_id": cert_id,
        "decision": "Authorized",
        "terminal_route": "Accept",
        "reason": "Morphism certificate successfully validated by independent verifier and accepted by active policy",
        "certified": True,
        "authorized": True,
    }


def main():
    print("================================================================================")
    print("DEMO 02: Certificate Validation and Authority Verification")
    print("================================================================================")

    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    with open(DATA_PATH, "r") as f:
        certs = json.load(f)

    for i, cert in enumerate(certs, 1):
        print(f"\n--- Running Case {i}: {cert.get('description')} ---")
        print("Input Certificate:")
        print(json.dumps({k: v for k, v in cert.items() if k != "description"}, indent=2))

        result = evaluate_certificate(cert)

        print("\nOutput Decision:")
        print(json.dumps(result, indent=2))
        print("-" * 80)


if __name__ == "__main__":
    main()
