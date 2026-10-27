"""Candidate-bound adapter to the existing native exact cochain certificate checker.

This checks the cochain task only. It derives no Hilbert/Born/tensor import.
AuthorityEffect: None.
"""

import json
from fractions import Fraction

from pfp.domain.cochain import CochainRefusal
from pfp.ffi import (
    evaluate_prompt_cochain_disposition as evaluate_prompt_cochain,
)

CHECKER_ID = "finite-qm-native-cochain-v1"


def rational(value):
    if (
        type(value) is not dict
        or set(value) != {"num", "den"}
        or type(value["num"]) is not int
        or type(value["den"]) is not int
        or value["den"] <= 0
    ):
        raise ValueError("EXACT_RATIONAL_REQUIRED")
    result = Fraction(value["num"], value["den"])
    if result.numerator != value["num"] or result.denominator != value["den"]:
        raise ValueError("REDUCED_RATIONAL_REQUIRED")
    return result


class NativeCochainJudge:
    def __init__(self, host):
        self.host = host
        self.receipts = []

    def __call__(self, case, answer):
        carrier = json.loads(case["prompt"])["operad_slots"]["slot_m1_layer0_ambient_carrier"]
        if carrier["coefficient_ring"] != "Q":
            return False, "COEFFICIENT_RING_MISMATCH"
        data = carrier["public_input"]
        try:
            potential = [rational(x) for x in answer["potential"]]
            dual = [rational(x) for x in answer["dual_witness"]]
            phi, gamma = rational(answer["phi1"]), rational(answer["gamma2"])
        except (KeyError, TypeError, ValueError):
            return False, "INVALID_EXACT_CERTIFICATE"
        disposition = evaluate_prompt_cochain(
            complex=data["complex"],
            cochain=data["cochain"],
            primal_potential=potential,
            dual_witness=dual,
            host=self.host,
        )
        self.receipts.append(disposition.receipt)
        if isinstance(disposition, CochainRefusal):
            if (
                disposition.reason
                in {
                    "HOST_ERROR",
                    "UNRECOGNIZED_DISPOSITION",
                    "MALFORMED_NATIVE_REPLY",
                }
                or "raw_refusal" in disposition.receipt
            ):
                raise RuntimeError("NATIVE_CHECK_UNAVAILABLE:" + disposition.reason)
            return False, "NATIVE_CERTIFICATE_REFUSED:" + disposition.reason
        return (
            phi == disposition.phi1 and gamma == disposition.gamma2,
            "NATIVE_CERTIFICATE_CHECKED_ON_SUPPLIED_COMPLEX",
        )
