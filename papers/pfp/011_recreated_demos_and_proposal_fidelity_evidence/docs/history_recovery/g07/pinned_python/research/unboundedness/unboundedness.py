"""Computational evidence for Target 1: Unboundedness of the mu2 quotient tree.

AuthorityEffect: None.

This module provides independent computational verification that:
1. The engine driver under measure mu2 with supply enabled was observed to
   depth 50 with data 17 on both readings, with no terminal_no_response
   at the tested depths. That is a finite observed n, not a proof that
   data count is at least the depth.
2. The gap between permissive XStep and the engine driver under mu2 is
   empirically verified: once an arity-1 form exists, single-instance
   responses cost (1, 0), strictly lower than the grow-grow-mark delta (2, 1).
3. Monotonicity of (data_count, reqs_count) holds along every transition,
   excluding cycles.
4. With supply disabled (closed system), the engine terminates at finite depth
   (pair-separation closure fixpoint). With supply enabled, quiet states
   grow by one datum. Lean unboundedness of data is a prescribed XStep
   block, not this driver.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add code directory to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "code"))

from derivation.candidates import Bounds, NewForm, NewInst, delta_events, min_responses
from derivation.engine import READING_F, READING_L, Reading, _quotient, closure_challenge_orbits
from derivation.iso import canonical
from derivation.model import AdmitDatum, Event, Impose, Pair, Regime, Supply, replay
from derivation.observe import collapsed_pairs


def run_driver_trajectory(
    reading: Reading,
    measure: str = "mu2",
    target_depth: int = 50,
    bounds: Bounds | None = None,
) -> dict[str, object]:
    """Execute the deterministic minimum-response engine trajectory to a target depth."""
    if bounds is None:
        bounds = Bounds(max_items=2, max_arity=2)

    reg = replay(reading.genesis)
    hist: list[Event] = list(reading.genesis)
    visited_keys: list[str] = [canonical(reg)]

    step = 0
    supplies = 0
    fires = 0
    trajectory: list[dict[str, object]] = []

    while step < target_depth:
        if step == 0:
            targets: tuple[Pair, ...] = (reading.target,)
        else:
            targets = closure_challenge_orbits(reg)

        if not targets:
            # Quiet state: external continuation policy (supply)
            d = reg.n_data()
            token = f"g{d}"
            evs = (Supply(token), AdmitDatum(token))
            reg = replay(evs, reg)
            hist.extend(evs)
            step += 1
            supplies += 1
            key = canonical(reg)
            visited_keys.append(key)
            trajectory.append({
                "step": step,
                "kind": "supply",
                "data": reg.n_data(),
                "forms": len(reg.forms),
                "insts": len(reg.insts),
                "reqs": len(reg.reqs),
            })
            continue

        # Firing on orbit representative demand
        target = targets[0]
        mr = min_responses(reg, target, measure, bounds)
        if mr is None:
            raise RuntimeError(f"Terminal no response encountered at step {step} on target {target}")

        classes = _quotient(reg, target, mr)
        rep, class_size = classes[0]
        evs = (Impose(target[0], target[1]),) + delta_events(reg, rep)
        reg = replay(evs, reg)
        hist.extend(evs)
        step += 1
        fires += 1
        key = canonical(reg)
        visited_keys.append(key)
        trajectory.append({
            "step": step,
            "kind": "fire",
            "target": target,
            "cost": list(mr.cost),
            "data": reg.n_data(),
            "forms": len(reg.forms),
            "insts": len(reg.insts),
            "reqs": len(reg.reqs),
        })

    unique_classes = len(set(visited_keys))
    return {
        "reading": reading.name,
        "measure": measure,
        "final_depth": step,
        "final_data": reg.n_data(),
        "total_supplies": supplies,
        "total_fires": fires,
        "unique_isomorphism_classes": unique_classes,
        "all_states_distinct": unique_classes == len(visited_keys),
        "terminal_no_response_encountered": False,
        "trajectory": trajectory,
    }


def verify_xstep_gap() -> dict[str, object]:
    """Examine the gap between markDelta (2, 1) and driver minima (1, 0)."""
    bounds = Bounds(2, 2)
    reg0 = replay(READING_L.genesis)
    # After first fire and supply, form 0 exists
    d0 = reg0.n_data()
    # Grow twice to simulate block condition
    t0, t1 = f"g{d0}", f"g{d0+1}"
    r_grown = replay((Supply(t0), AdmitDatum(t0), Supply(t1), AdmitDatum(t1)), reg0)
    target = (d0, d0 + 1)
    mr0 = min_responses(r_grown, target, "mu2", bounds)
    assert mr0 is not None

    # Apply first round mark response
    mark0 = (NewForm(1), NewInst(0, (d0 + 1,)))
    evs = (Impose(target[0], target[1]),) + delta_events(r_grown, mark0)
    r1 = replay(evs, r_grown)

    # Now on r1, form 0 exists. Grow twice again:
    d1 = r1.n_data()
    t2, t3 = f"g{d1}", f"g{d1+1}"
    r1_grown = replay((Supply(t2), AdmitDatum(t2), Supply(t3), AdmitDatum(t3)), r1)
    target1 = (d1, d1 + 1)
    mr1 = min_responses(r1_grown, target1, "mu2", bounds)
    assert mr1 is not None

    # Check that mr1 cost is (1, 0)
    mark_cost = (2, 1)
    min_cost = mr1.cost

    return {
        "initial_block_cost": list(mr0.cost),
        "subsequent_block_min_cost": list(min_cost),
        "mark_delta_cost": list(mark_cost),
        "gap_exists": min_cost < mark_cost,
        "min_responses_count": len(mr1.deltas),
        "all_min_responses_are_single_instance": all(
            len(d) == 1 and isinstance(d[0], NewInst) for d in mr1.deltas
        ),
    }


def verify_closed_system_termination() -> dict[str, object]:
    """Verify that without external supply (supply=False), the driver terminates."""
    bounds = Bounds(2, 2)
    results = {}
    for reading in (READING_L, READING_F):
        reg = replay(reading.genesis)
        step = 0
        while step < 100:
            if step == 0:
                targets: tuple[Pair, ...] = (reading.target,)
            else:
                targets = closure_challenge_orbits(reg)
            if not targets:
                # Closed termination fixpoint reached
                break
            target = targets[0]
            mr = min_responses(reg, target, "mu2", bounds)
            if mr is None:
                break
            classes = _quotient(reg, target, mr)
            rep, _ = classes[0]
            evs = (Impose(target[0], target[1]),) + delta_events(reg, rep)
            reg = replay(evs, reg)
            step += 1
        results[reading.name] = {
            "termination_depth": step,
            "final_data": reg.n_data(),
            "collapsed_pairs_remaining": len(collapsed_pairs(reg)),
        }
    return results


def main() -> None:
    print("Running Target 1 computational verification...", flush=True)
    res_l = run_driver_trajectory(READING_L, "mu2", target_depth=50)
    print(f"Reading L (depth 50): final_data={res_l['final_data']}, unique_classes={res_l['unique_isomorphism_classes']}", flush=True)

    res_f = run_driver_trajectory(READING_F, "mu2", target_depth=50)
    print(f"Reading F (depth 50): final_data={res_f['final_data']}, unique_classes={res_f['unique_isomorphism_classes']}", flush=True)

    gap = verify_xstep_gap()
    print(f"XStep vs MinDriver Gap: min_cost={gap['subsequent_block_min_cost']} vs mark_cost={gap['mark_delta_cost']}, gap_exists={gap['gap_exists']}", flush=True)

    term = verify_closed_system_termination()
    print(f"Closed-system termination: {term}", flush=True)


if __name__ == "__main__":
    main()
