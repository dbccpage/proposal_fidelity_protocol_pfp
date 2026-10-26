"""Package demonstration 1: host phases, fuel, and atomic rollback.

Runs the package re-implementation of the host (``host_engine.py``), which is
not the repository's canonical Demo 3 host (paper Section 4.1):

1. Phase changes INTAKE -> COVERAGE -> WITNESS.
2. Each attempted batch costs one unit of fuel, which a rollback does not return.
3. A refused batch restores the prior covered elements, witness, and phase,
   while the digest chain records the refusal.
4. Repeated refusals exhaust the fuel; the host then enters TERMINAL with
   FUEL_EXHAUSTED and rejects later batches.
"""

from demo_checks import require
from host_engine import Demo3HostEngine, HostExit, HostPhase, MoveProposal


def run_demo() -> dict[str, str | bool | int]:
    print("=" * 70)
    print("DEMO 1: HOST PHASES, FUEL, AND ATOMIC ROLLBACK (package re-implementation)")
    print("=" * 70)

    engine = Demo3HostEngine("gauge_even_triangle", "T", initial_fuel=11)
    print(f"[Init] Fixture: {engine.fixture_id}, Arm: {engine.arm}")
    print(f"       Phase: {engine.state.current_phase.value}, Fuel: {engine.state.remaining_fuel}")
    print(f"       Initial Digest: {engine.state.state_digest[:16]}...")
    require(engine.state.remaining_fuel == 11, "initial fuel should be 11")

    receipt1 = engine.execute_batch([MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
    print(f"\n[Step 1] Cover Element -> Decision: {receipt1.host_decision}")
    print(f"         Phase: {engine.state.current_phase.value}, Fuel: {engine.state.remaining_fuel}")
    print(f"         Covered Elements: {engine.state.covered_elements}")
    print(f"         State Digest: {engine.state.state_digest[:16]}...")
    require(receipt1.host_decision == "ACCEPTED", "cover batch should be accepted")
    require(not receipt1.batch_rolled_back, "accepted batch should not roll back")
    require(engine.state.current_phase == HostPhase.COVERAGE, "phase should be COVERAGE")
    require(engine.state.remaining_fuel == 10, "one unit of fuel should be charged")

    print("\n[Step 2] Proposing batch: COVER_ELEMENT + ILLEGAL_POISONED_MOVE...")
    receipt2 = engine.execute_batch(
        [
            MoveProposal("COVER_ELEMENT", {"element_id": "elem_poisoned"}),
            MoveProposal("ILLEGAL_POISONED_MOVE", {}),
        ]
    )
    print(f"         Decision: {receipt2.host_decision}")
    print(f"         Rolled Back: {receipt2.batch_rolled_back}")
    print(f"         Covered Elements (restored): {engine.state.covered_elements}")
    print(f"         Fuel (attempt charged): {engine.state.remaining_fuel}")
    print(f"         Digest after refusal: {engine.state.state_digest[:16]}...")
    require(receipt2.batch_rolled_back, "poisoned batch should roll back")
    require("ILLEGAL_POISONED_MOVE" in receipt2.host_decision, "decision should name the move")
    require("elem_poisoned" not in engine.state.covered_elements, "coverage should be restored")
    require(engine.state.remaining_fuel == 9, "refused batch should still cost one unit")

    receipt3 = engine.execute_batch(
        [MoveProposal("PROPOSE_WITNESS", {"witness_type": "vertex_bits", "witness": [0, 1, 0]})]
    )
    print(f"\n[Step 3] Propose Witness -> Decision: {receipt3.host_decision}")
    print(f"         Phase: {engine.state.current_phase.value}, Fuel: {engine.state.remaining_fuel}")
    require(receipt3.host_decision == "ACCEPTED", "witness batch should be accepted")
    require(engine.state.current_phase == HostPhase.WITNESS, "phase should be WITNESS")
    require(engine.state.remaining_fuel == 8, "one unit of fuel should be charged")

    print("\n[Step 4] Proposing batch with a move after VERIFY...")
    receipt4 = engine.execute_batch(
        [
            MoveProposal("VERIFY", {}),
            MoveProposal("COVER_ELEMENT", {"element_id": "elem_trailing"}),
        ]
    )
    print(f"         Decision: {receipt4.host_decision}")
    print(f"         Rolled Back: {receipt4.batch_rolled_back}")
    print(f"         Remaining Fuel: {engine.state.remaining_fuel}")
    require(receipt4.batch_rolled_back, "batch with a move after VERIFY should roll back")
    require(receipt4.host_decision == "REJECT_MOVE_AFTER_VERIFY", "decision should be REJECT_MOVE_AFTER_VERIFY")
    require(engine.state.remaining_fuel == 7, "refused batch should still cost one unit")

    print(f"\n[Step 5] Spending the remaining fuel ({engine.state.remaining_fuel}) on refused batches...")
    initial_drain_fuel = engine.state.remaining_fuel
    for attempt in range(initial_drain_fuel):
        curr_fuel = engine.state.remaining_fuel
        refused = engine.execute_batch([MoveProposal("UNKNOWN_POISON", {})])
        require(refused.batch_rolled_back, "unknown move should roll back")
        require(engine.state.remaining_fuel == curr_fuel - 1, "each attempt should cost one unit")
        print(f"         Attempt {attempt + 1}: refusal recorded, fuel now {engine.state.remaining_fuel}")

    require(engine.state.remaining_fuel == 0, "fuel should be exhausted")
    require(engine.state.current_phase == HostPhase.TERMINAL, "phase should be TERMINAL")
    require(engine.state.terminal_exit == HostExit.FUEL_EXHAUSTED, "exit should be FUEL_EXHAUSTED")
    print("         Host reached TERMINAL with FUEL_EXHAUSTED.")

    terminal_receipt = engine.execute_batch(
        [MoveProposal("COVER_ELEMENT", {"element_id": "elem_after_term"})]
    )
    require(terminal_receipt.host_decision == "REJECT_TERMINAL_STATE", "terminal host should reject")
    print(f"         Post-exhaustion attempt rejected: {terminal_receipt.host_decision}")

    print("\n[Step 6] Single-attempt exhaustion (initial fuel = 1)...")
    single_attempt_engine = Demo3HostEngine("gauge_even_triangle", "T", initial_fuel=1)
    single_receipt = single_attempt_engine.execute_batch(
        [MoveProposal("COVER_ELEMENT", {"element_id": "elem_only"})]
    )
    require(single_receipt.host_decision == "ACCEPTED", "single batch should be accepted")
    require(single_attempt_engine.state.remaining_fuel == 0, "fuel should be 0")
    require(single_attempt_engine.state.current_phase == HostPhase.TERMINAL, "phase should be TERMINAL")
    require(
        single_attempt_engine.state.terminal_exit == HostExit.FUEL_EXHAUSTED,
        "exit should be FUEL_EXHAUSTED",
    )
    print("         Initial fuel 1: one batch executed, fuel 0, TERMINAL.")

    print("\n" + "=" * 70)
    print("DEMO 1 PASSED: phases, fuel charges, rollbacks, and exhaustion behaved as listed.")
    print("=" * 70)
    return {
        "status": "PASSED",
        "demo": "demo1_host_transactions",
        "final_fuel": engine.state.remaining_fuel,
        "chain_digest": engine.state.state_digest,
    }


if __name__ == "__main__":
    raise SystemExit(0 if run_demo()["status"] == "PASSED" else 1)
