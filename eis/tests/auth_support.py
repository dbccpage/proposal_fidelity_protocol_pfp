"""Independent Python Ed25519 signer for explicitly synthetic EIS fixtures.

These fixed keys are public test data, never an operator trust configuration.
The signing profile is implemented here independently of the Rust encoder.
"""

import hashlib
import json
from copy import deepcopy

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from omega_engine_epistemic_immune_system.infrastructure.authenticated_custody import (
    NativeAttestationVerifier,
    SignedHostHealth,
)

SCHEMA = "omega.eis.signed-attestation.v1"
PROFILE = "sha256:" + "b" * 64
CONTENT = json.dumps({"verified": True, "phi1": "0"}, sort_keys=True)
RULE = b"fixture guard rule version 1"
NOW = 100
KEYS = {
    name: Ed25519PrivateKey.from_private_bytes(bytes([seed]) * 32)
    for name, seed in (("operator", 7), ("health-host", 8), ("test-runner", 9))
}


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def binding():
    return {
        "spec_id": "spec_alpha",
        "scope": "scope_one",
        "rule_digest": digest(RULE),
        "source_digest": digest(b"fixture source manifest"),
        "subject_digest": digest(RULE),
        "context_digest": PROFILE,
    }


def policy():
    return {
        "schema_version": "omega.eis.trust-policy.v1",
        "trust_domain": "synthetic-fixture-only",
        "keys": [
            {
                "issuer": name,
                "key_id": name + "-1",
                "public_key_hex": key.public_key()
                .public_bytes(Encoding.Raw, PublicFormat.Raw)
                .hex(),
                "purposes": [
                    {
                        "operator": "admission",
                        "health-host": "health",
                        "test-runner": "observation",
                    }[name]
                ],
                "scopes": ["scope_one"],
                "not_before": 10,
                "not_after": 1000,
                "max_lifetime_seconds": 100,
                "revoked": False,
                "observer_source_digest": None
                if name == "operator"
                else digest(b"fixture observer code"),
            }
            for name, key in KEYS.items()
        ],
    }


def signing_bytes(a):
    b = a["binding"]
    fields = [
        SCHEMA,
        a["trust_domain"],
        a["purpose"],
        a["issuer"],
        a["key_id"],
        a["event_id"],
        [
            b["spec_id"],
            b["scope"],
            b["rule_digest"],
            b["source_digest"],
            b["subject_digest"],
            b["context_digest"],
        ],
        a["issued_at"],
        a["expires_at"],
        a["outcome"],
        a["previous_event"],
        a["evidence_digest"],
    ]
    return json.dumps(fields, separators=(",", ":"), ensure_ascii=False).encode()


def signed(
    purpose="admission",
    outcome="ADMIT",
    event="decision-1",
    *,
    expected=None,
    issued=NOW,
    previous=None,
    raw=None,
):
    expected = binding() if expected is None else deepcopy(expected)
    issuer = {"admission": "operator", "health": "health-host", "observation": "test-runner"}[
        purpose
    ]
    if raw is None:
        raw = (
            b"synthetic operator decision"
            if purpose == "admission"
            else json.dumps(
                {
                    "schema_version": "omega.eis.observed-evidence.v1",
                    "observer_id": issuer,
                    "run_id": event,
                    "subject_digest": expected["subject_digest"],
                    "source_digest": digest(b"fixture observer code"),
                    "outcome": outcome,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        )
    a = {
        "schema_version": SCHEMA,
        "trust_domain": "synthetic-fixture-only",
        "purpose": purpose,
        "issuer": issuer,
        "key_id": issuer + "-1",
        "event_id": event,
        "binding": expected,
        "issued_at": issued,
        "expires_at": issued + 50,
        "outcome": outcome,
        "previous_event": previous,
        "evidence_digest": digest(raw),
    }
    a["signature_hex"] = KEYS[issuer].sign(signing_bytes(a)).hex()
    return {"attestation": a, "evidence_hex": raw.hex()}


def health(*, content=CONTENT, outcome="HEALTHY", clock=lambda: NOW):
    report = signed(
        "health",
        outcome,
        "health-1",
        expected={**binding(), "subject_digest": digest(content.encode())},
    )
    return SignedHostHealth(
        NativeAttestationVerifier(policy(), clock=clock), binding(), lambda: report
    )
