"""Controllers for the Adversary Swarm engine.

AuthorityEffect: None.
"""

from __future__ import annotations

from operations.domain.rop.result import Err, Refusal, Result
from governance.domain.ingress.limits import IngressRefusal

from ..domain.graph_ports import GraphRunReferenceV1
from ..domain.graph_task import GraphTaskV1
from ..domain.models import AdversaryBoutOutcomeV1, AdversaryBoutRequestV1
from ..domain.specialization import SwarmTypeV1
from ..use_cases.bout_service import AdversarySwarmService

_LOCUS = "adversary.controllers.adversary_controller"


class AdversarySwarmController:
    """Public controller for executing Adversary 7-Act bouts.

    The service is injected; build the production one with
    ``adversary.runtime.build_adversary_service``. Invalid input is a
    typed refusal, never an escaping exception.
    """

    def __init__(self, service: AdversarySwarmService) -> None:
        self.service = service

    def run_bout(
        self,
        task_key: str,
        objective: str,
        fixture_mode: bool = True,
        request_external_admission: bool = False,
        max_rounds: int = 4,
        swarm_type: SwarmTypeV1 | str = SwarmTypeV1.OPEN_TOPIC,
    ) -> Result[AdversaryBoutOutcomeV1, Refusal]:
        try:
            st = SwarmTypeV1.from_str(swarm_type)
            request = AdversaryBoutRequestV1(
                task_key=task_key,
                objective=objective,
                max_rounds=max_rounds,
                fixture_mode=fixture_mode,
                request_external_admission=request_external_admission,
                swarm_type=st,
            )
        except IngressRefusal as refusal:
            return Err(Refusal(refusal.receipt.refusal_code, str(refusal), _LOCUS))
        except (TypeError, ValueError) as exc:
            return Err(Refusal("ADVERSARY_REQUEST_INVALID", str(exc), _LOCUS))
        return self.service.execute_bout(request)

    def run_graph(self, task: GraphTaskV1, mode: str) -> Result[GraphRunReferenceV1, Refusal]:
        return self.service.run_graph(task, mode)


__all__ = ["AdversarySwarmController"]
