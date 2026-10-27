"""Child process for the durability crash tests. Not a test module itself.

Run as ``python crash_child.py <cut> <trace_path>``. It performs a real dispatch
and then terminates *itself* abruptly at the requested cut with ``os._exit(1)``
-- no unwinding, no ``atexit``, no buffer flush. That is the closest reachable
approximation to a power loss from inside a portable test, and it is the only way
to observe what actually survived: an in-process rewrite of a file proves nothing
about fsync, because closed-and-flushed data stays visible through the page cache
regardless.

The execution is built by ``fixture_gateway`` -- the same closed factory every
other fixture run uses -- so this measures the wiring that ships. The
``after_intent`` cut is a *declared* ``AbruptProcessExit`` in the response script
rather than a closure assigned onto the transport, because accepting arbitrary
callables is precisely the hole that let a scripted socket be sealed under a real
vendor's identity.

Cuts:

``after_intent``    dies after barrier 1 and before the response is written.
``after_encrypted_cas`` dies after the encrypted envelope is atomically committed
                        and before the trace records its reference. This is the
                        window the barrier-2 ordering exists to make safe.
``clean``           completes and seals, as a control.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from adversary.domain.providers.types import (  # noqa: E402
    CandidateRequest,
)
from operating_system.adapters.security import (  # noqa: E402
    FixtureOnlyAeadProtector,
)
from operating_system.infrastructure import (  # noqa: E402
    EncryptedArtifactCas,
)
from pfp.infrastructure.trace import (  # noqa: E402
    DURABILITY_FSYNC_LIVE,
    EVENT_RESPONSE_DURABLE,
    SCRIPTED_MODEL,
    SCRIPTED_PROVIDER,
    fixture_gateway,
    scripted_openai_payload,
)
from pfp.infrastructure.trace.provider_dispatch import (  # noqa: E402
    AbruptProcessExit,
)

REQUEST = CandidateRequest(system="crash-test system", user="crash-test user")
FIXTURE_KEY = b"symbol-game-provider-dispatch-test-key-v1"


def main() -> None:
    cut = sys.argv[1]
    trace_path = Path(sys.argv[2])

    # The socket's whole behaviour, declared up front. `after_intent` kills the
    # process from inside the transport call, which is after barrier 1 has
    # fsynced the intent and before any response can be written.
    responses = (
        [AbruptProcessExit(1)]
        if cut == "after_intent"
        else [scripted_openai_payload("crash-test reply")]
    )

    # `fsync_live` durability under a deterministic-fixture run mode: the barriers
    # are what this child exists to interrupt, and a scripted reply must not be
    # recorded as a provider call in order to get them.
    run = fixture_gateway(
        trace_path,
        responses,
        artifact_store=EncryptedArtifactCas(
            trace_path.parent / "encrypted-artifacts",
            FixtureOnlyAeadProtector(FIXTURE_KEY),
        ),
        execution_id="crash-child",
        durability=DURABILITY_FSYNC_LIVE,
    )
    trace = run.trace

    if cut == "after_encrypted_cas":
        # Die between encrypted CAS commit and the trace record carrying its ref.
        # Patched on the trace rather than declared in the script because the cut
        # is inside the durability barrier, not inside the socket.
        real_record = trace.record

        def _record(event, **fields):
            if event == EVENT_RESPONSE_DURABLE:
                os._exit(1)
            return real_record(event, **fields)

        trace.record = _record  # type: ignore[method-assign]

    run.gateway.complete(REQUEST, provider=SCRIPTED_PROVIDER, model=SCRIPTED_MODEL)
    trace.seal("DISPATCH_DONE")


if __name__ == "__main__":
    main()
