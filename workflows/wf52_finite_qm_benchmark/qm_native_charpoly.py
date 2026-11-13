"""Registered-public-seed Pauli input -> exact native characteristic polynomial.

Only the one declared seed digest is admitted. The caller separately verifies
the actual prompt bytes. This module reads the two pinned public owner source
files, never seed files, provider outputs, evaluators or private/reference data.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import hashlib

import hamiltonian_artifact as pauli
import native_sidecar as sidecar

HERE = Path(__file__).resolve().parent
REGISTERED_SEED_SHA256 = "9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7"
PAULI_SOURCE_SHA256 = "bf28b8371f11d2ac34256d3699a1653a2e44562e9d7b4a60e12221c750938925"
SIDECAR_SOURCE_SHA256 = "67feada49e7e73a45897c81b1353aed7251964ed43bb463767cc2434b9c0fc3c"
BASIS = ["00", "01", "10", "11"]
SEMANTICS = "H = J*(X tensor X + Y tensor Y) + Delta*(Z tensor I - I tensor Z) + K*(Z tensor Z)."


class PublicBindingError(ValueError):
    pass


def _owners_and_seed(seed_hash):
    if type(seed_hash) is not str or seed_hash != REGISTERED_SEED_SHA256:
        raise PublicBindingError("UNREGISTERED_PUBLIC_SEED")
    for module, name, expected in [(pauli, "hamiltonian_artifact.py", PAULI_SOURCE_SHA256),
                                   (sidecar, "native_sidecar.py", SIDECAR_SOURCE_SHA256)]:
        path = HERE / name
        if Path(module.__file__).resolve() != path.resolve():
            raise sidecar.Infrastructure("PUBLIC_OWNER_IMPORT_PATH_CHANGED")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise sidecar.Infrastructure("PUBLIC_OWNER_SOURCE_CHANGED:" + name)


def _checked_artifact(artifact, seed_hash):
    checked = pauli.check_artifact(sidecar.canonical(artifact).decode("ascii"), seed_hash)
    if checked["accepted"] is not True or checked["comparison_count"] != 48:
        raise PublicBindingError("PAULI_PUBLIC_INPUT_MISMATCH")
    if checked["checker_source_sha256"] != PAULI_SOURCE_SHA256 or checked["basis"] != BASIS:
        raise sidecar.Infrastructure("PAULI_RECEIPT_PROVENANCE_CHANGED")
    return checked["canonical_candidate"]


def _transport(artifact, seed_hash):
    matrices = {"constant": [["0"] * 4 for _ in range(4)]}
    for name in ["J", "Delta", "K"]:
        rows = []
        for row in artifact["coefficient_matrices"][name]:
            converted = []
            for text in row:
                # The public owner requires n/d, including 0/1 and 2/1. The
                # native profile requires Fraction's canonical 0 and 2 forms.
                q = Fraction(text)
                if f"{q.numerator}/{q.denominator}" != text:
                    raise PublicBindingError("PUBLIC_RATIONAL_ROUNDTRIP_FAILED")
                native = str(q)
                if sidecar.rational(native, bits=16) != q:
                    raise PublicBindingError("NATIVE_RATIONAL_TRANSPORT_FAILED")
                converted.append(native)
            rows.append(converted)
        matrices[name] = rows
    public = {"schema": "pfp.qm-affine-charpoly-public.v1",
              "obligation_id": "registered-qm-charpoly:" + seed_hash,
              "parameters": ["J", "Delta", "K"], "matrix_coefficients": matrices}
    sidecar.admit_public(public)
    return public


def prepare_public(seed_hash):
    """Derive and bind public matrix input; never derive characteristic coefficients."""
    _owners_and_seed(seed_hash)
    contract = pauli.public_contract(seed_hash)
    if (contract["semantics"] != SEMANTICS or contract["basis"] != BASIS or
        contract["supported_seed_sha256"] != REGISTERED_SEED_SHA256):
        raise sidecar.Infrastructure("REGISTERED_PAULI_CONVENTION_CHANGED")
    artifact = _checked_artifact(pauli.public_input_artifact(seed_hash), seed_hash)
    public = _transport(artifact, seed_hash)
    payload = {"schema": "pfp.qm-native-charpoly.public-binding.v1", "seed_sha256": seed_hash,
               "basis": BASIS.copy(), "pauli_semantics": SEMANTICS,
               "source_binding": {"pauli_checker_id": contract["checker_id"],
                   "pauli_checker_version": contract["checker_version"],
                   "pauli_source_path": "dag/benchmark/hamiltonian_artifact.py",
                   "pauli_source_sha256": PAULI_SOURCE_SHA256,
                   "sidecar_source_path": "dag/benchmark/native_sidecar.py",
                   "sidecar_source_sha256": SIDECAR_SOURCE_SHA256},
               "public_input_artifact": artifact,
               "public_artifact_sha256": sidecar.digest(artifact),
               "native_public_input": public, "native_public_input_sha256": sidecar.digest(public),
               "checks": {"pauli_compared_entries": 48, "exact_rational_roundtrips": 48,
                          "constant_zero_entries": 16},
               "authority_effect": "None"}
    return {"payload": payload, "sha256": sidecar.digest(payload)}


def _validate_packet(packet, expected, seed_hash):
    if len(sidecar.canonical(packet)) > 65_536:
        raise PublicBindingError("PUBLIC_PACKET_BYTE_LIMIT")
    sidecar.keys(packet, ["payload", "sha256"], "PUBLIC_PACKET_FIELDS")
    payload = packet["payload"]
    sidecar.keys(payload, expected["payload"], "PUBLIC_PACKET_PAYLOAD_FIELDS")
    if packet["sha256"] != sidecar.digest(payload):
        raise PublicBindingError("PUBLIC_PACKET_DIGEST_MISMATCH")
    if payload["seed_sha256"] != seed_hash:
        raise PublicBindingError("PUBLIC_PACKET_SEED_MISMATCH")
    if payload["basis"] != BASIS or payload["pauli_semantics"] != SEMANTICS:
        raise PublicBindingError("PUBLIC_BASIS_OR_CONVENTION_MISMATCH")
    artifact = _checked_artifact(payload["public_input_artifact"], seed_hash)
    transported = _transport(artifact, seed_hash)
    if payload["native_public_input"] != transported:
        raise PublicBindingError("PUBLIC_AFFINE_TRANSPORT_MISMATCH")
    # No caller-provided checksum, source identity or successful-check label is
    # authoritative. Recompute the entire packet from the registered public owner.
    if packet != expected:
        raise PublicBindingError("PUBLIC_PROVENANCE_MISMATCH")


def public_contract(seed_hash):
    """Public-only prompt integration contract: input matrices, never charpoly answers."""
    packet = prepare_public(seed_hash)
    public = packet["payload"]["native_public_input"]
    term = {"type": "object", "additionalProperties": False, "required": ["powers", "q"],
        "properties": {"powers": {"type": "array", "minItems": 3, "maxItems": 3,
            "items": {"type": "integer", "minimum": 0, "maximum": 4}},
            "q": {"type": "string", "maxLength": 42,
                  "pattern": r"^-?[1-9][0-9]*(?:/[1-9][0-9]*)?$"}}}
    properties = {"schema": {"const": "pfp.qm-affine-charpoly-candidate.v1"},
        "public_input_sha256": {"const": sidecar.digest(public)},
        "obligation_id": {"const": public["obligation_id"]},
        "answer_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "assertion_span": {"type": "array", "minItems": 2, "maxItems": 2,
                           "items": {"type": "integer", "minimum": 0, "maximum": 131072}},
        "assertion_text": {"type": "string"},
        "coefficients": {"type": "array", "minItems": 5, "maxItems": 5,
                         "items": {"type": "array", "maxItems": 125, "items": term}}}
    return {"schema": "pfp.qm-native-charpoly.contract.v1", "public_packet": packet,
            "candidate_schema": {"type": "object", "additionalProperties": False,
                "required": list(properties), "properties": properties},
            "coefficient_convention": "Ascending lambda powers; powers=[eJ,eDelta,eK]; zero polynomial=[]; unique nonzero reduced rational monomials; each rational component <=64 bits; leading coefficient=1.",
            "answer_binding": "assertion_text must equal native_sidecar.assertion_text(coefficients), at assertion_span UTF8 bytes in the exact answer whose SHA256 is supplied.",
            "verification": "One native batch over all125 points of {-2,-1,0,1,2}^3 after exact Pauli input binding and checked per-variable degree<=4.",
            "scope": "Only the registered public Hamiltonian characteristic polynomial; no projector, dynamics, or whole-task acceptance.",
            "caller_obligation": "Independently verify actual public seed bytes have the registered SHA256 before invoking this API."}


def verify(seed_hash, candidate, answer, public_packet=None):
    """Verify one closed coefficient candidate against only registered public input."""
    result = {"schema": "pfp.qm-native-charpoly.receipt.v1", "authority_effect": "None",
              "native_executed": False, "provider_calls": 0, "certified_scope": [],
              "unresolved": ["actual seed-byte verification (caller-owned)", "surrounding prose",
                             "spectrum projectors", "eigenvectors", "dynamics", "other obligations"]}
    try:
        expected = prepare_public(seed_hash)
        if public_packet is not None:
            _validate_packet(public_packet, expected, seed_hash)
        result.update(seed_sha256=seed_hash, public_packet_sha256=expected["sha256"],
                      public_binding=expected["payload"], public_input_bound=True)
        native = sidecar.verify(expected["payload"]["native_public_input"], candidate, answer)
        result.update(status=native["status"], native_executed=native["native_executed"],
                      certified_scope=native["certified_scope"], native_receipt=native)
        if "reason" in native:
            result["reason"] = native["reason"]
    except sidecar.Infrastructure as exc:
        result.update(status="INFRASTRUCTURE_REFUSAL", reason=str(exc))
    except (PublicBindingError, sidecar.Invalid, ValueError, TypeError, KeyError,
            OverflowError, RecursionError) as exc:
        result.update(status="PUBLIC_BINDING_REFUSAL", reason=str(exc))
    except OSError as exc:
        result.update(status="INFRASTRUCTURE_REFUSAL", reason=type(exc).__name__)
    return result
