"""Pure admission policy for the packaged autopoietic immune demo.

Pharmacy detection and screen execution stay outside this module.
AuthorityEffect: None.
"""

from __future__ import annotations

import json

from omega_engine_pfp.domain.demos import refuse_model_functionals

DEMO_ID = "demo_4e_cogsci_autopoiesis"
SCOPE = (
    "24 pharmacology controls and OEEIS two-signal/thymus/idle-counter/quarantine "
    "fixture probes; Signal 2 from host payload checks only"
)
CONTROL_COUNT = 12
# The pharmacy matcher parses what it screens, so its self panel is a clean
# candidate document, not prose.
PHARMACY_SELF_FIXTURES = (
    '{"objections": [], "proposed_claim_deltas": [], "public_rationale": '
    '"clean finite candidate", "schema_version": "candidate-move/v1"}',
)
REPLY_SELF_FIXTURES = (
    "candidate contains data and needs a host check",
    "unknown with no promotion",
)
REPLY_RULE_ID = "mssn-self-certification"
REPLY_EPITOPE = "model-verdict"
REPLY_PATTERN = r"verified|phi1|gamma2|certified"


class DemoRefusal(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


def require_cardinality(positive: int, negative: int) -> None:
    if type(positive) is not int or type(negative) is not int:
        raise DemoRefusal("FIXTURE_CARDINALITY")
    if positive != CONTROL_COUNT or negative != CONTROL_COUNT:
        raise DemoRefusal("FIXTURE_CARDINALITY", f"{positive}+{negative}")


def require_control(
    case_id: str,
    *,
    positive: bool,
    finding_classes: tuple[str, ...],
    target_class: str | None,
) -> None:
    """Positive controls must name their target class; negative controls must be clean."""
    if type(positive) is not bool:
        raise DemoRefusal("SCENARIO_CHECK_FAILED", case_id)
    if positive:
        if type(target_class) is not str or target_class not in finding_classes:
            raise DemoRefusal("SCENARIO_CHECK_FAILED", case_id)
        return
    if target_class is not None or finding_classes:
        raise DemoRefusal("SCENARIO_CHECK_FAILED", case_id)


def model_reply_defects(raw: str) -> int:
    """1 when the reply is not JSON or carries a model functional or authority label.

    A prose occurrence of those words is not a claim. Only refuse_model_functionals
    on parsed keys counts, matching the packaged immune screen.
    """
    if type(raw) is not str:
        raise DemoRefusal("SCENARIO_FIXTURE_REPLIES")
    try:
        parsed = json.loads(raw)
        refuse_model_functionals(parsed)
    except ValueError:
        return 1
    return 0
