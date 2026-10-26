"""Domain Invariants for the Grammar Bounded Context."""

from __future__ import annotations

import hashlib
import json
from itertools import product

from omega_engine_pfp.domain.mssn_research.grammar.spectral_geometry import (
    LiftGoal,
    LiftNecessityCertificate,
)
from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Ok, Refusal, Result
from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import (
    ContentDigest,
    StageLevel,
)

from ..packets.value_objects import RefusalCode
from .errors import (
    GrammarDomainError,
    LiftNecessityError,
)


def _subsets(items):
    return tuple(
        tuple(item for index, item in enumerate(items) if mask & (1 << index))
        for mask in range(1 << len(items))
    )


def _encode_relation(configuration) -> str:
    return "R={" + ",".join(f"({left},{right})" for left, right in configuration) + "}"


def _irreflexive(configuration) -> bool:
    return bool(configuration) and all(left != right for left, right in configuration)


def _distinct_path(configuration, mode: str) -> bool:
    if not all(left != right for left, right in configuration):
        return False
    relation = set(configuration)
    vertices = {vertex for edge in configuration for vertex in edge}
    return any(
        _path_matches(relation, a, b, c, mode) for a in vertices for b in vertices for c in vertices
    )


def _path_matches(relation, a, b, c, mode: str) -> bool:
    if len({a, b, c}) != 3 or (a, b) not in relation or (b, c) not in relation:
        return False
    if mode == "cycle":
        return (c, a) in relation
    if mode == "gap":
        return (a, c) not in relation
    return True


def _stage_one_policy(goal: LiftGoal):
    policies = {
        LiftGoal.IRREFLEXIVE_WITNESSED_RELATION: (
            _irreflexive,
            "OBSTRUCTION_NONE_SATISFIES_STAGE_ONE",
        ),
        LiftGoal.DIRECTED_PATH_COMPOSITION: (
            lambda config: _distinct_path(config, "path"),
            "OBSTRUCTION_PIGEONHOLE_PATH_LENGTH_TWO",
        ),
        LiftGoal.DIRECTED_CYCLE_THREE: (
            lambda config: _distinct_path(config, "cycle"),
            "OBSTRUCTION_CYCLE_LENGTH_THREE_CARRIER_COLLAPSE",
        ),
        LiftGoal.TRANSITIVE_CLOSURE_GAP: (
            lambda config: _distinct_path(config, "gap"),
            "OBSTRUCTION_TRANSITIVE_GAP_CARRIER_COLLAPSE",
        ),
    }
    try:
        return policies[goal]
    except KeyError as exc:
        raise ValueError(f"unsupported stage one lift goal: {goal}") from exc


def _stage_zero_lift_replay(goal: LiftGoal) -> dict:
    """Enumerate the two declared source configurations and finite target space.

    Relation goals range over every relation on the singleton source carrier.
    Name generation ranges over every subset of the singleton source alphabet.
    Stage one uses the two named elements 0,1 (or <0>,<1>). The certificate
    format admits the first resolving target in this fixed enumeration order.
    This is a bounded model, not a search over arbitrary stage interpretations.
    """
    source, target, satisfies, encode, obstruction = _stage_zero_policy(goal)

    source_rows = [
        {"configuration": encode(configuration), "satisfies_goal": satisfies(configuration)}
        for configuration in source
    ]
    target_rows = [
        {"configuration": encode(configuration), "satisfies_goal": satisfies(configuration)}
        for configuration in target
    ]
    witness = next(row["configuration"] for row in target_rows if row["satisfies_goal"])
    return {
        "schema": "mssn.stage-zero-lift-replay.v2",
        "source_stage": 0,
        "target_stage": 1,
        "goal": goal.value,
        "carrier_size_source": 1,
        "carrier_size_target": 2,
        "source_configurations": source_rows,
        "target_configurations": target_rows,
        "surviving_obstruction_code": obstruction,
        "target_resolution_witness": witness,
    }


def _stage_zero_policy(goal: LiftGoal):
    if goal in (LiftGoal.BARE_ASSERTION, LiftGoal.IRREFLEXIVE_WITNESSED_RELATION):
        source = _subsets(tuple(product(range(1), repeat=2)))
        target = _subsets(tuple(product(range(2), repeat=2)))

        def satisfies(configuration):
            return bool(configuration) and (
                goal == LiftGoal.BARE_ASSERTION
                or all(left != right for left, right in configuration)
            )

        return (
            source,
            target,
            satisfies,
            _encode_relation,
            "OBSTRUCTION_SUBSINGLETON_DIAGONAL_SELF_RELATION",
        )
    if goal == LiftGoal.DISTINCT_NAME_GENERATION:
        source = _subsets(("<>",))
        target = _subsets(("<0>", "<1>"))

        def satisfies(configuration):
            return len(set(configuration)) >= 2

        def encode(configuration):
            return "GEN={" + ",".join(configuration) + "}"

        return source, target, satisfies, encode, "OBSTRUCTION_STAGE0_SYNTACTIC_COLLAPSE"
    raise ValueError("unsupported finite lift goal")


def _stage_one_lift_replay(goal: LiftGoal) -> dict:
    """Enumerate the 16 declared stage-one source configurations and 512 target configurations.

    Stage 1 carrier has 2 elements {0, 1}. The source space consists of all 2^(2*2) = 16 binary relations.
    Stage 2 carrier has 3 elements {0, 1, 2}. The target space consists of all 2^(3*3) = 512 binary relations.
    Goals:
    - IRREFLEXIVE_WITNESSED_RELATION: Satisfied on source by isolated edge R = {(0, 1)}.
    - DIRECTED_PATH_COMPOSITION: Requires length-2 path through 3 distinct vertices. Exhaustively fails on source.
      Obstruction: OBSTRUCTION_PIGEONHOLE_PATH_LENGTH_TWO.
      Resolved in target by witness R = {(0, 2), (1, 0)}.
    - DIRECTED_CYCLE_THREE: Requires directed 3-cycle through 3 distinct vertices. Exhaustively fails on source.
      Obstruction: OBSTRUCTION_CYCLE_LENGTH_THREE_CARRIER_COLLAPSE.
      Resolved in target by witness R = {(0, 1), (1, 2), (2, 0)}.
    - TRANSITIVE_CLOSURE_GAP: Requires length-2 path without shortcut edge. Exhaustively fails on source.
      Obstruction: OBSTRUCTION_TRANSITIVE_GAP_CARRIER_COLLAPSE.
    """
    source_items = tuple(product(range(2), repeat=2))
    target_items = tuple(product(range(3), repeat=2))
    source = _subsets(source_items)
    target = _subsets(target_items)
    satisfies, obstruction = _stage_one_policy(goal)
    source_rows = [
        {
            "configuration": _encode_relation(configuration),
            "satisfies_goal": satisfies(configuration),
        }
        for configuration in source
    ]
    target_rows = [
        {
            "configuration": _encode_relation(configuration),
            "satisfies_goal": satisfies(configuration),
        }
        for configuration in target
    ]
    witness = next((row["configuration"] for row in target_rows if row["satisfies_goal"]), None)
    return {
        "schema": "mssn.stage-one-lift-replay.v1",
        "source_stage": 1,
        "target_stage": 2,
        "goal": goal.value,
        "carrier_size_source": 2,
        "carrier_size_target": 3,
        "source_configurations": source_rows,
        "target_configurations": target_rows,
        "surviving_obstruction_code": obstruction,
        "target_resolution_witness": witness,
    }


def _lift_replay_digest(replay: dict) -> ContentDigest:
    """Bind the enumerated domain, outcomes, obstruction, and actual target witness."""
    wire = json.dumps(replay, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return ContentDigest(hashlib.sha256(wire.encode("utf-8")).hexdigest())


def execute_bounded_lift_necessity_search(
    source_stage: StageLevel,
    goal: LiftGoal,
) -> Result[LiftNecessityCertificate, GrammarDomainError]:
    """Exhaust the declared finite model; refuse unearned or unsupported stage lifts."""
    if type(source_stage) is not StageLevel or type(goal) is not LiftGoal:
        return Refusal(
            LiftNecessityError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message="REFUSED_INVALID_LIFT_INPUT: Exact StageLevel and LiftGoal values required",
            )
        )
    if source_stage.level == 0:
        replay = _stage_zero_lift_replay(goal)
    elif source_stage.level == 1:
        replay = _stage_one_lift_replay(goal)
    else:
        return Refusal(
            LiftNecessityError(
                code=RefusalCode.NONCONSERVATIVE_LIFT,
                message=f"REFUSED_UNIMPLEMENTED_STAGE_SEARCH: Bounded necessity search for Stage {source_stage.level} not implemented",
            )
        )
    countermodel = next(
        (row for row in replay["source_configurations"] if row["satisfies_goal"]), None
    )
    if countermodel is not None:
        return Refusal(
            LiftNecessityError(
                code=RefusalCode.NONCONSERVATIVE_LIFT,
                message=f"REFUSED_LIFT_UNEARNED: Goal {goal.value} is satisfied at Stage {source_stage.level} on {replay['carrier_size_source']}-point carrier model {countermodel['configuration']}",
            )
        )
    return Ok(
        LiftNecessityCertificate(
            source_stage=source_stage,
            target_stage=StageLevel(source_stage.level + 1),
            goal=goal,
            carrier_size_source=replay["carrier_size_source"],
            carrier_size_target=replay["carrier_size_target"],
            evaluated_configurations_count=len(replay["source_configurations"]),
            surviving_obstruction_code=replay["surviving_obstruction_code"],
            exhaustion_proof_digest=_lift_replay_digest(replay),
            target_resolution_witness=replay["target_resolution_witness"],
            is_verified=True,
        )
    )


def check_lift_necessity_certificate(
    cert: LiftNecessityCertificate,
) -> Result[bool, GrammarDomainError]:
    """Replay the supported finite model and bind every admitted evidence field.

    A supplied verification flag or digest is not evidence of a supported search.
    Higher stages and noncanonical target representations are refused.
    """
    shape = _check_lift_certificate_shape(cert)
    if shape.is_err():
        return shape
    replay = (
        _stage_zero_lift_replay(cert.goal)
        if cert.source_stage.level == 0
        else _stage_one_lift_replay(cert.goal)
    )
    if any(row["satisfies_goal"] for row in replay["source_configurations"]):
        return Refusal(
            LiftNecessityError(
                code=RefusalCode.NONCONSERVATIVE_LIFT,
                message=f"REFUSED_LIFT_UNEARNED: Goal {cert.goal.value} has a stage-{cert.source_stage.level} countermodel",
            )
        )
    evidence = _check_lift_evidence(cert, replay)
    if evidence.is_err():
        return evidence
    if not cert.is_verified:
        return Refusal(
            LiftNecessityError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message="REFUSED_UNVERIFIED_CERTIFICATE: Certificate is not marked verified",
            )
        )

    return Ok(True)


def _lift_refusal(message: str, code: RefusalCode = RefusalCode.HOST_VERIFICATION_REQUIRED):
    return Refusal(LiftNecessityError(code=code, message=message))


def _check_lift_certificate_shape(cert) -> Result[bool, GrammarDomainError]:
    if type(cert) is not LiftNecessityCertificate:
        return _lift_refusal(
            "REFUSED_INVALID_CERTIFICATE_TYPE: Exact LiftNecessityCertificate required"
        )
    if cert.source_stage.level not in (0, 1):
        return _lift_refusal(
            "REFUSED_UNIMPLEMENTED_STAGE_SEARCH: REFUSED_UNIMPLEMENTED_STAGE_VERIFICATION: "
            f"Bounded necessity verification for Stage {cert.source_stage.level} not implemented",
            RefusalCode.NONCONSERVATIVE_LIFT,
        )
    if cert.target_stage.level != cert.source_stage.level + 1:
        return _lift_refusal(
            f"REFUSED_STAGE_STEP: Certificate target stage {cert.target_stage.level} "
            f"!= source stage {cert.source_stage.level} + 1",
            RefusalCode.NONCONSERVATIVE_LIFT,
        )
    if cert.carrier_size_target <= cert.carrier_size_source:
        return _lift_refusal(
            f"REFUSED_CARRIER_MASS: Target carrier size ({cert.carrier_size_target}) "
            f"<= source ({cert.carrier_size_source})"
        )
    expected = (1, 2) if cert.source_stage.level == 0 else (2, 3)
    if (cert.carrier_size_source, cert.carrier_size_target) != expected:
        return _lift_refusal(
            f"REFUSED_CARRIER_DOMAIN: Supported stage-{cert.source_stage.level} replay requires "
            f"carrier sizes {expected[0]} -> {expected[1]}"
        )
    return Ok(True)


def _check_lift_evidence(cert: LiftNecessityCertificate, replay: dict):
    fields = (
        (
            cert.evaluated_configurations_count,
            len(replay["source_configurations"]),
            "REFUSED_INCOMPLETE_EXHAUSTION",
        ),
        (
            cert.surviving_obstruction_code,
            replay["surviving_obstruction_code"],
            "REFUSED_OBSTRUCTION_MISMATCH",
        ),
        (
            cert.target_resolution_witness,
            replay["target_resolution_witness"],
            "REFUSED_TARGET_WITNESS: REFUSED_INVALID_TARGET_WITNESS",
        ),
        (
            cert.exhaustion_proof_digest,
            _lift_replay_digest(replay),
            "REFUSED_FORGED_EXHAUSTION_DIGEST",
        ),
    )
    mismatch = next(
        ((actual, expected, refusal) for actual, expected, refusal in fields if actual != expected),
        None,
    )
    if mismatch is None:
        return Ok(True)
    actual, expected, refusal = mismatch
    return _lift_refusal(
        f"{refusal}: Certificate field {actual!r} differs from finite replay {expected!r}"
    )
