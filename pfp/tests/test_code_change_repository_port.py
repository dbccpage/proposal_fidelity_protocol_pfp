"""The controller's persistence calls, against a real implementation of the port.

`ICodeChangeRepository` had two problems that only show up when something
actually implements it.

First, it declared `save_gate_receipt` against
`domain.entities.gate_receipt.GateReceiptV1` -- a type carrying `gate_name`,
`disposition`, `message`, `retained_metrics` and `authority_effect`, with **no**
`packet_id`, `candidate_id` or `evidence_sha256`. It is structurally incapable
of naming the candidate it describes, so the port promised to persist a receipt
that could never be bound to anything, while every receipt the controller
produces is the aggregate one. A store built to the declared signature would
have had to discard the bindings to fit.

Second, a rival untyped `ICodeChangeRepository` (`save`/`find_by_id` over `Any`)
sat in `ports/ports.py`. It had no direct consumer and has been deleted.

Nothing in the tree implements this port, which is why neither defect had
surfaced. `RecordingCodeChangeRepository` below is a **test double proving the
port is satisfiable** -- not a production repository implementation. It stores in
memory, has no durability, and exists to exercise the controller's persistence
calls. Production persistence remains unwritten and is separately scoped.

The persistence *schedule* is asserted, not just the calls: a run root may only
be saved once one exists. The previous controller saved a run root at proposal
time, persisting a record of an evaluation that had not happened and carrying a
`terminal_status` no evaluator had assigned.

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from omega_engine_pfp.controllers.code_change_controller import (
    CodeChangeController,
)
from omega_engine_pfp.domain.aggregates.code_change_run_root import (
    CodeChangePatchArtifactV1,
    CodeChangeRunRootV1,
    GateReceiptV1,
)
from omega_engine_pfp.domain.ports import ICodeChangeRepository

OWNED = "src/x.py"
PROTECTED = "README.md"


def _diff(path: str) -> str:
    return f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1,1 @@\n+x = 1\n"


class RecordingCodeChangeRepository:
    """A test double satisfying `ICodeChangeRepository`. Not a production store.

    In-memory, no durability, no atomicity. Its purpose is to prove the corrected
    port is satisfiable and to observe the controller's persistence calls; it
    records call order as well as content, because the order is the part that
    regressed -- persistence of a run root before one existed.
    """

    def __init__(self) -> None:
        self.run_roots: list[CodeChangeRunRootV1] = []
        self.patches: dict[str, CodeChangePatchArtifactV1] = {}
        self.receipts: list[GateReceiptV1] = []
        self.calls: list[str] = []

    def save_run_root(self, run_root: CodeChangeRunRootV1) -> None:
        self.calls.append("save_run_root")
        self.run_roots.append(run_root)

    def get_run_root(self, run_root_id: str) -> CodeChangeRunRootV1 | None:
        for root in self.run_roots:
            if root.task_packet_id == run_root_id:
                return root
        return None

    def save_patch_artifact(self, patch: CodeChangePatchArtifactV1) -> None:
        self.calls.append("save_patch_artifact")
        self.patches[patch.patch_id] = patch

    def get_patch_artifact(self, patch_id: str) -> CodeChangePatchArtifactV1 | None:
        return self.patches.get(patch_id)

    def save_gate_receipt(self, receipt: GateReceiptV1) -> None:
        self.calls.append("save_gate_receipt")
        self.receipts.append(receipt)


@pytest.fixture()
def repo() -> RecordingCodeChangeRepository:
    return RecordingCodeChangeRepository()


@pytest.fixture()
def controller(repo: RecordingCodeChangeRepository) -> CodeChangeController:
    return CodeChangeController(repository=repo)


def test_the_recording_store_satisfies_the_declared_port(repo):
    """Structural conformance, asserted before anything relies on it.

    `ICodeChangeRepository` is a plain `Protocol`, so this checks the surface it
    declares rather than calling `isinstance`. If a method is added to the port
    without an implementation here, this fails rather than the wiring tests
    failing for an unrelated-looking reason.
    """
    required = [
        name for name in vars(ICodeChangeRepository) if not name.startswith("_")
    ]
    assert required, "the port must declare something"
    for name in required:
        assert callable(getattr(repo, name, None)), f"{name} is not implemented"


def test_no_run_root_is_persisted_before_one_exists(controller, repo):
    """The schedule regression.

    A run root is the result of `evaluate_code_change_candidate`. Saving one at
    proposal or submit time persists an evaluation that has not happened.
    """
    session = controller.create_proposal(
        task_id="task-persist",
        objective="persist correctly",
        base_revision="a" * 40,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
    )
    assert repo.calls == [], "creating a proposal evaluates nothing"

    session, bound = controller.submit_patch(
        session=session, producer_id="model-worker", patch_text=_diff(OWNED)
    )
    assert repo.calls == ["save_patch_artifact"]
    assert "save_run_root" not in repo.calls
    assert repo.run_roots == []


def test_the_full_lifecycle_persists_each_artifact_once(controller, repo):
    session = controller.create_proposal(
        task_id="task-persist",
        objective="persist correctly",
        base_revision="a" * 40,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
    )
    session, bound = controller.submit_patch(
        session=session, producer_id="model-worker", patch_text=_diff(OWNED)
    )
    receipts = controller.evaluate_patch_gates(session=session, bound=bound)
    run_root = controller.finalize_run(
        session=session, bound=bound, gate_receipts=receipts
    )

    assert repo.calls == [
        "save_patch_artifact",
        "save_gate_receipt",
        "save_gate_receipt",
        "save_gate_receipt",
        "save_run_root",
    ]
    assert repo.get_patch_artifact(bound.patch.patch_id) is bound.patch
    assert repo.get_run_root(run_root.task_packet_id) is run_root


def test_persisted_receipts_carry_the_bindings_the_entity_type_lacks(controller, repo):
    """The type correction, asserted by the fields it makes available.

    Under the old declaration a store could only have been written against a
    receipt with no `packet_id` and no `candidate_id`. These assertions are the
    ones that would have been impossible to write.
    """
    session = controller.create_proposal(
        task_id="task-persist",
        objective="persist correctly",
        base_revision="a" * 40,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
    )
    session, bound = controller.submit_patch(
        session=session, producer_id="model-worker", patch_text=_diff(OWNED)
    )
    controller.evaluate_patch_gates(session=session, bound=bound)

    assert len(repo.receipts) == 3
    for receipt in repo.receipts:
        assert isinstance(receipt, GateReceiptV1)
        assert receipt.packet_id == session.packet_id
        assert receipt.candidate_id == bound.candidate.candidate_id
        assert len(receipt.evidence_sha256) == 64


def test_a_refused_evaluation_persists_no_evaluation_artifacts(controller, repo):
    """Refusal must not leave a partial trail of *evaluation* artifacts.

    Scoped deliberately. The already-submitted patch stays persisted, and should:
    it was legitimately bound and admitted before the refused evaluation, and
    discarding it would lose a real artifact over an unrelated later failure.
    What must not survive is a partial set of gate receipts -- two of three --
    describing an evaluation that was refused.

    The fence runs to completion before the first receipt is built, so the store
    sees no receipt at all rather than a truncated run.

    This asserts the *use case* writes nothing further on refusal. It says
    nothing about durability if the repository itself fails midway through the
    per-receipt save loop, which is not atomic. Atomic batch publication is a
    separate durability concern and is not addressed here.
    """
    from omega_engine_pfp.domain import CanonicalizationError
    from omega_engine_pfp.use_cases.code_change import BoundCandidate

    session = controller.create_proposal(
        task_id="task-persist",
        objective="persist correctly",
        base_revision="a" * 40,
        owned_paths=(OWNED,),
        protected_paths=(PROTECTED,),
    )
    session, bound = controller.submit_patch(
        session=session, producer_id="model-worker", patch_text=_diff(OWNED)
    )
    assert repo.calls == ["save_patch_artifact"]
    repo.calls.clear()

    swapped = BoundCandidate(
        candidate=bound.candidate, patch=bound.patch, patch_bytes=b"different\n"
    )
    with pytest.raises(CanonicalizationError):
        controller.evaluate_patch_gates(session=session, bound=swapped)

    assert repo.calls == [], "a refused evaluation writes no evaluation artifacts"
    assert repo.receipts == []
    assert repo.run_roots == []
    # The legitimately submitted patch is still there, and that is correct.
    assert repo.get_patch_artifact(bound.patch.patch_id) is bound.patch
