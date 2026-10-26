"""Retained Primitive Difference to observer-profile CEC bridge.

This module is an isolated, finite reference evaluator.  It does not replace
the Symbol Game router and it does not mint authority.  Its purpose is to make
one boundary precise:

* a retained difference exists before an observer;
* an observer induces a ``ProfileDifference`` and a zero relation;
* only a protected retained difference hidden by that observer is an active
  obstruction; and
* a declared finite controller returns a same-level repair, a typed refusal,
  or a replayable conservative-extension proposal.

No cochain, homology, zeta, or physics interpretation is assumed here.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
from itertools import combinations, permutations
from omega_engine_pfp.infrastructure.serialization import CanonicalizationError, domain_digest


AUTHORITY_EFFECT_NONE = "None"
BRIDGE_SCHEMA = "omega.symbol-game.retained-profile-cec-bridge.v1"
MAX_AUTOMORPHISM_CARRIER = 8


class BridgeError(ValueError):
    """Raised when bridge evidence is malformed or semantically invalid."""


class ClosurePolicy(str, Enum):
    """Who declares demands; neither policy is derived from collapse."""

    EXPLICIT_PROTECTED_ONLY = "EXPLICIT_PROTECTED_ONLY"
    EXTERNAL_ALL_PAIRS = "EXTERNAL_ALL_PAIRS"


class RefusalCode(str, Enum):
    NO_ACTIVE_OBSTRUCTION = "NO_ACTIVE_OBSTRUCTION"
    INCOMPLETE_SEARCH_EVIDENCE = "INCOMPLETE_SEARCH_EVIDENCE"
    NO_ADMISSIBLE_RESPONSE = "NO_ADMISSIBLE_RESPONSE"


class TerminalKind(str, Enum):
    SAME_LEVEL_REPAIR = "SameLevelRepair"
    TYPED_REFUSAL = "TypedRefusal"
    CONSERVATIVE_EXTENSION_PROPOSAL = "ConservativeExtensionProposal"


Pair = tuple[str, str]
Permutation = tuple[str, ...]


def _exact_str(value: object, label: str) -> str:
    if type(value) is not str or not value:
        raise BridgeError(f"{label} must be a non-empty exact string")
    return value


def _exact_bool(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise BridgeError(f"{label} must be an exact bool")
    return value


def _authority_is_none(value: object) -> bool:
    return type(value) is str and value == "None"


def _require_authority_none(value: object) -> None:
    if not _authority_is_none(value):
        raise BridgeError("the bridge cannot mint authority")


def _exact_string_tuple(value: object, label: str) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or not item for item in value
    ):
        raise BridgeError(f"{label} must be a tuple of non-empty exact strings")
    if len(value) != len(set(value)):
        raise BridgeError(f"{label} must not contain duplicates")
    return value


def _normalized_pair(left: str, right: str) -> Pair:
    _exact_str(left, "pair.left")
    _exact_str(right, "pair.right")
    if left == right:
        raise BridgeError("a retained or protected pair must contain two states")
    return (left, right) if left < right else (right, left)


def _exact_pair(value: object, label: str) -> Pair:
    if type(value) is not tuple or len(value) != 2:
        raise BridgeError(f"{label} must be an exact two-item tuple")
    left, right = value
    if type(left) is not str or type(right) is not str:
        raise BridgeError(f"{label} members must be exact strings")
    pair = _normalized_pair(left, right)
    if pair != value:
        raise BridgeError(f"{label} must be in canonical order")
    return pair


def _pair_tuple(value: object, label: str) -> tuple[Pair, ...]:
    if type(value) is not tuple:
        raise BridgeError(f"{label} must be an exact tuple")
    pairs = tuple(
        _exact_pair(pair, f"{label}[{index}]") for index, pair in enumerate(value)
    )
    if pairs != tuple(sorted(set(pairs))):
        raise BridgeError(f"{label} must be unique and lexicographically ordered")
    return pairs


def _closed_dataclass(value: object, expected_type: type[object]) -> bool:
    if type(value) is not expected_type:
        return False
    declared = {field.name for field in fields(expected_type)}
    state = getattr(value, "__dict__", None)
    return state is None or (type(state) is dict and set(state) == declared)


@dataclass(frozen=True, slots=True)
class RetainedDiffV1:
    """A pre-observer distinction with a replay-addressable witness."""

    left: str
    right: str
    witness_id: str

    def __post_init__(self) -> None:
        pair = _normalized_pair(self.left, self.right)
        if pair != (self.left, self.right):
            raise BridgeError("RetainedDiffV1 endpoints must be canonical")
        _exact_str(self.witness_id, "RetainedDiffV1.witness_id")

    @property
    def pair(self) -> Pair:
        return (self.left, self.right)


@dataclass(frozen=True, slots=True)
class PrimitiveCarrierV1:
    """The carrier and retained differences that precede observation."""

    carrier_id: str
    states: tuple[str, ...]
    retained_differences: tuple[RetainedDiffV1, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        _exact_str(self.carrier_id, "PrimitiveCarrierV1.carrier_id")
        states = _exact_string_tuple(self.states, "PrimitiveCarrierV1.states")
        if type(self.retained_differences) is not tuple:
            raise BridgeError("retained_differences must be an exact tuple")
        pairs: list[Pair] = []
        for item in self.retained_differences:
            if (
                type(item) is not RetainedDiffV1
                or item.left not in states
                or item.right not in states
            ):
                raise BridgeError(
                    "retained differences must be exact and carrier-scoped"
                )
            pairs.append(item.pair)
        if pairs != sorted(set(pairs)):
            raise BridgeError("retained differences must be unique and ordered")
        _require_authority_none(self.authority_effect)

    @property
    def primitive_id(self) -> str:
        return domain_digest("omega.symbol-game.primitive-carrier.v1", self)


@dataclass(frozen=True, slots=True)
class ProfileRowV1:
    state: str
    features: tuple[str, ...]

    def __post_init__(self) -> None:
        _exact_str(self.state, "ProfileRowV1.state")
        features = _exact_string_tuple(self.features, "ProfileRowV1.features")
        if features != tuple(sorted(features)):
            raise BridgeError("profile features must be sorted")


@dataclass(frozen=True, slots=True)
class TransitionRowV1:
    operation: str
    state: str
    result: str

    def __post_init__(self) -> None:
        _exact_str(self.operation, "TransitionRowV1.operation")
        _exact_str(self.state, "TransitionRowV1.state")
        _exact_str(self.result, "TransitionRowV1.result")


@dataclass(frozen=True, slots=True)
class ObserverPresentationV1:
    """A finite observer layered over a primitive carrier."""

    primitive_id: str
    signature_id: str
    signature: tuple[str, ...]
    profiles: tuple[ProfileRowV1, ...]
    transitions: tuple[TransitionRowV1, ...]
    protected_pairs: tuple[Pair, ...]
    closure_policy: ClosurePolicy = ClosurePolicy.EXPLICIT_PROTECTED_ONLY
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        _exact_str(self.primitive_id, "ObserverPresentationV1.primitive_id")
        _exact_str(self.signature_id, "ObserverPresentationV1.signature_id")
        signature = _exact_string_tuple(
            self.signature, "ObserverPresentationV1.signature"
        )
        if type(self.profiles) is not tuple or not self.profiles:
            raise BridgeError("profiles must be a non-empty exact tuple")
        states: list[str] = []
        for row in self.profiles:
            if type(row) is not ProfileRowV1:
                raise BridgeError("profiles must contain exact ProfileRowV1 values")
            if any(feature not in signature for feature in row.features):
                raise BridgeError("profile feature is outside the signature")
            states.append(row.state)
        if states != sorted(set(states)):
            raise BridgeError("profile rows must cover unique states in sorted order")
        if type(self.transitions) is not tuple or any(
            type(row) is not TransitionRowV1 for row in self.transitions
        ):
            raise BridgeError("transitions must contain exact TransitionRowV1 values")
        transition_keys = [(row.operation, row.state) for row in self.transitions]
        expected_keys = sorted(
            (operation, state) for operation in signature for state in states
        )
        if transition_keys != expected_keys:
            raise BridgeError(
                "transitions must be a sorted total signature action table"
            )
        if any(row.result not in states for row in self.transitions):
            raise BridgeError("transition result is outside the observer carrier")
        protected = _pair_tuple(self.protected_pairs, "protected_pairs")
        if any(left not in states or right not in states for left, right in protected):
            raise BridgeError("protected pair is outside the observer carrier")
        if type(self.closure_policy) is not ClosurePolicy:
            raise BridgeError("closure_policy must be an exact ClosurePolicy")
        _require_authority_none(self.authority_effect)

    @property
    def presentation_id(self) -> str:
        return domain_digest("omega.symbol-game.observer-presentation.v1", self)

    def profile(self, state: str) -> tuple[str, ...]:
        for row in self.profiles:
            if row.state == state:
                return row.features
        raise BridgeError(f"unknown profile state: {state}")

    def transition(self, operation: str, state: str) -> str:
        for row in self.transitions:
            if row.operation == operation and row.state == state:
                return row.result
        raise BridgeError(f"unknown transition: {operation} on {state}")


@dataclass(frozen=True, slots=True)
class BridgeProblemV1:
    primitive: PrimitiveCarrierV1
    observer: ObserverPresentationV1

    def __post_init__(self) -> None:
        if (
            type(self.primitive) is not PrimitiveCarrierV1
            or type(self.observer) is not ObserverPresentationV1
        ):
            raise BridgeError(
                "BridgeProblemV1 requires exact primitive and observer values"
            )
        if self.observer.primitive_id != self.primitive.primitive_id:
            raise BridgeError("observer does not bind the primitive carrier")
        if tuple(row.state for row in self.observer.profiles) != tuple(
            sorted(self.primitive.states)
        ):
            raise BridgeError(
                "observer profiles must cover the primitive carrier exactly"
            )

    @property
    def problem_id(self) -> str:
        return domain_digest("omega.symbol-game.retained-profile-problem.v1", self)


@dataclass(frozen=True, slots=True)
class ProfileDifferenceV1:
    """Observer-relative symmetric difference; never the root Primitive Difference."""

    pair: Pair
    left_only: tuple[str, ...]
    right_only: tuple[str, ...]

    def __post_init__(self) -> None:
        _exact_pair(self.pair, "ProfileDifferenceV1.pair")
        left = _exact_string_tuple(self.left_only, "ProfileDifferenceV1.left_only")
        right = _exact_string_tuple(self.right_only, "ProfileDifferenceV1.right_only")
        if left != tuple(sorted(left)) or right != tuple(sorted(right)):
            raise BridgeError("profile-difference features must be sorted")
        if set(left).intersection(right):
            raise BridgeError("profile-difference sides must be disjoint")

    @property
    def is_zero(self) -> bool:
        return not self.left_only and not self.right_only


def profile_difference(problem: BridgeProblemV1, pair: Pair) -> ProfileDifferenceV1:
    pair = _exact_pair(pair, "profile_difference.pair")
    if (
        pair[0] not in problem.primitive.states
        or pair[1] not in problem.primitive.states
    ):
        raise BridgeError("profile difference pair is outside the primitive carrier")
    left = set(problem.observer.profile(pair[0]))
    right = set(problem.observer.profile(pair[1]))
    return ProfileDifferenceV1(
        pair=pair,
        left_only=tuple(sorted(left - right)),
        right_only=tuple(sorted(right - left)),
    )


def zero_rel_r(problem: BridgeProblemV1, pair: Pair) -> bool:
    """The observer-induced zero relation."""

    return profile_difference(problem, pair).is_zero


def _retained(problem: BridgeProblemV1, pair: Pair) -> RetainedDiffV1 | None:
    for retained in problem.primitive.retained_differences:
        if retained.pair == pair:
            return retained
    return None


def declared_protected_pairs(problem: BridgeProblemV1) -> tuple[Pair, ...]:
    """Return policy-declared demands, never demands inferred from collapse alone."""

    if problem.observer.closure_policy is ClosurePolicy.EXPLICIT_PROTECTED_ONLY:
        return problem.observer.protected_pairs
    return tuple(combinations(problem.primitive.states, 2))


@dataclass(frozen=True, slots=True)
class ActiveObstructionV1:
    problem_id: str
    pair: Pair
    retained_witness_id: str
    profile_difference: ProfileDifferenceV1
    protected_by: str
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        _exact_str(self.problem_id, "ActiveObstructionV1.problem_id")
        pair = _exact_pair(self.pair, "ActiveObstructionV1.pair")
        _exact_str(
            self.retained_witness_id,
            "ActiveObstructionV1.retained_witness_id",
        )
        if (
            type(self.profile_difference) is not ProfileDifferenceV1
            or self.profile_difference.pair != pair
        ):
            raise BridgeError("active obstruction has a mismatched profile difference")
        _exact_str(self.protected_by, "ActiveObstructionV1.protected_by")
        _require_authority_none(self.authority_effect)

    @property
    def obstruction_id(self) -> str:
        return domain_digest("omega.symbol-game.active-obstruction.v1", self)


def active_obstruction_of_components(
    problem: BridgeProblemV1, pair: Pair
) -> ActiveObstructionV1 | None:
    """Replay ``RetainedDiff ∧ ZeroRel_r ∧ Protected → ActiveObstruction_r``."""

    pair = _exact_pair(pair, "active_obstruction.pair")
    retained = _retained(problem, pair)
    if retained is None or not zero_rel_r(problem, pair):
        return None
    declared = declared_protected_pairs(problem)
    if pair not in declared:
        return None
    protected_by = (
        "explicit-protected-pair"
        if pair in problem.observer.protected_pairs
        else "external-all-pairs-closure-policy"
    )
    return ActiveObstructionV1(
        problem_id=problem.problem_id,
        pair=pair,
        retained_witness_id=retained.witness_id,
        profile_difference=profile_difference(problem, pair),
        protected_by=protected_by,
    )


def active_obstructions(problem: BridgeProblemV1) -> tuple[ActiveObstructionV1, ...]:
    result = []
    for pair in declared_protected_pairs(problem):
        obstruction = active_obstruction_of_components(problem, pair)
        if obstruction is not None:
            result.append(obstruction)
    return tuple(result)


def _map_pair(pair: Pair, mapping: dict[str, str]) -> Pair:
    return _normalized_pair(mapping[pair[0]], mapping[pair[1]])


def _automorphisms(problem: BridgeProblemV1) -> tuple[Permutation, ...]:
    """Enumerate exact state automorphisms of the declared finite problem."""

    states = problem.primitive.states
    if len(states) > MAX_AUTOMORPHISM_CARRIER:
        raise BridgeError("automorphism enumeration budget exceeded")
    retained = {item.pair for item in problem.primitive.retained_differences}
    protected = set(problem.observer.protected_pairs)
    profiles = {row.state: row.features for row in problem.observer.profiles}
    accepted: list[Permutation] = []
    for image in permutations(states):
        mapping = dict(zip(states, image, strict=True))
        if {_map_pair(pair, mapping) for pair in retained} != retained:
            continue
        if {_map_pair(pair, mapping) for pair in protected} != protected:
            continue
        if any(profiles[mapping[state]] != profiles[state] for state in states):
            continue
        if any(
            mapping[problem.observer.transition(operation, state)]
            != problem.observer.transition(operation, mapping[state])
            for operation in problem.observer.signature
            for state in states
        ):
            continue
        accepted.append(tuple(image))
    return tuple(accepted)


@dataclass(frozen=True, slots=True)
class DemandOrbitV1:
    """A demand is the full automorphism orbit, never a chosen least pair."""

    problem_id: str
    members: tuple[Pair, ...]
    transports: tuple[Permutation, ...]

    def __post_init__(self) -> None:
        _exact_str(self.problem_id, "DemandOrbitV1.problem_id")
        members = _pair_tuple(self.members, "DemandOrbitV1.members")
        if not members:
            raise BridgeError("a demand orbit must contain at least one pair")
        if type(self.transports) is not tuple or not self.transports:
            raise BridgeError("a demand orbit must carry transport permutations")
        widths: set[int] = set()
        for index, transport in enumerate(self.transports):
            values = _exact_string_tuple(
                transport, f"DemandOrbitV1.transports[{index}]"
            )
            widths.add(len(values))
        if len(widths) != 1 or self.transports != tuple(sorted(set(self.transports))):
            raise BridgeError("demand orbit transports must be unique and uniform")

    @property
    def orbit_id(self) -> str:
        return domain_digest("omega.symbol-game.demand-orbit.v1", self)


def demand_orbits(problem: BridgeProblemV1) -> tuple[DemandOrbitV1, ...]:
    demands = tuple(obstruction.pair for obstruction in active_obstructions(problem))
    automorphisms = _automorphisms(problem)
    states = problem.primitive.states
    unseen = set(demands)
    result: list[DemandOrbitV1] = []
    while unseen:
        seed = min(unseen)  # ordering only; the returned value retains the whole orbit
        members: set[Pair] = set()
        transports: list[Permutation] = []
        for image in automorphisms:
            mapping = dict(zip(states, image, strict=True))
            mapped = _map_pair(seed, mapping)
            if mapped in demands:
                members.add(mapped)
                transports.append(image)
        if not members:
            raise BridgeError("automorphism orbit construction failed")
        ordered_members = tuple(sorted(members))
        unseen.difference_update(members)
        result.append(
            DemandOrbitV1(
                problem_id=problem.problem_id,
                members=ordered_members,
                transports=tuple(sorted(set(transports))),
            )
        )
    return tuple(sorted(result, key=lambda orbit: orbit.orbit_id))


def _oracle_demand_orbits(
    problem: BridgeProblemV1,
    _problem_type: type[BridgeProblemV1] = BridgeProblemV1,
    _closure_type: type[ClosurePolicy] = ClosurePolicy,
    _orbit_type: type[DemandOrbitV1] = DemandOrbitV1,
    _permutations: object = permutations,
    _combinations: object = combinations,
) -> tuple[DemandOrbitV1, ...]:
    """Second finite orbit construction with no shared semantic helpers."""

    if type(problem) is not _problem_type:
        raise BridgeError("orbit oracle requires an exact bridge problem")
    primitive = problem.primitive
    observer = problem.observer
    states = primitive.states
    if (
        type(states) is not tuple
        or len(states) > 8
        or type(observer.closure_policy) is not _closure_type
    ):
        raise BridgeError("orbit oracle rejected the declared carrier")
    profiles = {row.state: row.features for row in observer.profiles}
    retained = {(item.left, item.right) for item in primitive.retained_differences}
    explicit = set(observer.protected_pairs)
    if observer.closure_policy.value == "EXPLICIT_PROTECTED_ONLY":
        protected = explicit
    elif observer.closure_policy.value == "EXTERNAL_ALL_PAIRS":
        protected = set(_combinations(states, 2))  # type: ignore[operator]
    else:
        raise BridgeError("orbit oracle rejected the closure policy")
    demands = tuple(
        sorted(
            pair
            for pair in protected
            if pair in retained and profiles[pair[0]] == profiles[pair[1]]
        )
    )

    def mapped_pair(pair: Pair, mapping: dict[str, str]) -> Pair:
        left = mapping[pair[0]]
        right = mapping[pair[1]]
        return (left, right) if left < right else (right, left)

    automorphisms: list[Permutation] = []
    for image in _permutations(states):  # type: ignore[operator]
        mapping = dict(zip(states, image, strict=True))
        if {mapped_pair(pair, mapping) for pair in retained} != retained:
            continue
        if {mapped_pair(pair, mapping) for pair in explicit} != explicit:
            continue
        if any(profiles[mapping[state]] != profiles[state] for state in states):
            continue
        if any(
            mapping[observer.transition(operation, state)]
            != observer.transition(operation, mapping[state])
            for operation in observer.signature
            for state in states
        ):
            continue
        automorphisms.append(tuple(image))

    unseen = set(demands)
    result: list[DemandOrbitV1] = []
    while unseen:
        seed = min(unseen)
        members: set[Pair] = set()
        transports: list[Permutation] = []
        for image in automorphisms:
            mapping = dict(zip(states, image, strict=True))
            mapped = mapped_pair(seed, mapping)
            if mapped in demands:
                members.add(mapped)
                transports.append(image)
        if not members:
            raise BridgeError("orbit oracle found no transport for a demand")
        unseen.difference_update(members)
        result.append(
            _orbit_type(
                problem.problem_id,
                tuple(sorted(members)),
                tuple(sorted(set(transports))),
            )
        )
    return tuple(sorted(result, key=lambda orbit: orbit.orbit_id))


@dataclass(frozen=True, slots=True)
class StateRenamingV1:
    source_problem_id: str
    target_problem_id: str
    source_states: tuple[str, ...]
    target_states: tuple[str, ...]
    image: tuple[str, ...]

    def __post_init__(self) -> None:
        _exact_str(self.source_problem_id, "StateRenamingV1.source_problem_id")
        _exact_str(self.target_problem_id, "StateRenamingV1.target_problem_id")
        source = _exact_string_tuple(
            self.source_states, "StateRenamingV1.source_states"
        )
        target = _exact_string_tuple(
            self.target_states, "StateRenamingV1.target_states"
        )
        image = _exact_string_tuple(self.image, "StateRenamingV1.image")
        if len(source) != len(target) or set(image) != set(target):
            raise BridgeError("state renaming must be a carrier bijection")

    def mapping(self) -> dict[str, str]:
        return dict(zip(self.source_states, self.image, strict=True))


def orbit_transition_congruent(
    source: BridgeProblemV1,
    target: BridgeProblemV1,
    renaming: StateRenamingV1,
) -> bool:
    """Verify exact transport of orbit-valued demands under a renaming."""

    if (
        not _problem_replays(source)
        or not _problem_replays(target)
        or not _renaming_replays(renaming)
        or renaming.source_problem_id != source.problem_id
        or renaming.target_problem_id != target.problem_id
        or renaming.source_states != source.primitive.states
        or renaming.target_states != target.primitive.states
        or tuple(sorted(renaming.image)) != tuple(sorted(target.primitive.states))
        or source.observer.closure_policy is not target.observer.closure_policy
    ):
        return False
    mapping = renaming.mapping()
    source_profiles = {row.state: row.features for row in source.observer.profiles}
    target_profiles = {row.state: row.features for row in target.observer.profiles}
    mapped_retained = {
        _map_pair(item.pair, mapping) for item in source.primitive.retained_differences
    }
    if mapped_retained != {item.pair for item in target.primitive.retained_differences}:
        return False
    if {_map_pair(pair, mapping) for pair in source.observer.protected_pairs} != set(
        target.observer.protected_pairs
    ):
        return False
    if any(
        source_profiles[state] != target_profiles[mapping[state]]
        for state in source.primitive.states
    ):
        return False
    if source.observer.signature != target.observer.signature:
        return False
    if any(
        mapping[source.observer.transition(operation, state)]
        != target.observer.transition(operation, mapping[state])
        for operation in source.observer.signature
        for state in source.primitive.states
    ):
        return False
    mapped_orbits = {
        frozenset(_map_pair(pair, mapping) for pair in orbit.members)
        for orbit in demand_orbits(source)
    }
    target_orbits = {frozenset(orbit.members) for orbit in demand_orbits(target)}
    return mapped_orbits == target_orbits


@dataclass(frozen=True, slots=True)
class SameLevelRepairCandidateV1:
    problem_id: str
    carrier_id: str
    signature_id: str
    profiles: tuple[ProfileRowV1, ...]
    resolved_orbit_ids: tuple[str, ...]
    producer_id: str
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        _exact_str(self.problem_id, "SameLevelRepairCandidateV1.problem_id")
        _exact_str(self.carrier_id, "SameLevelRepairCandidateV1.carrier_id")
        _exact_str(self.signature_id, "SameLevelRepairCandidateV1.signature_id")
        _exact_str(self.producer_id, "SameLevelRepairCandidateV1.producer_id")
        if type(self.profiles) is not tuple or any(
            type(row) is not ProfileRowV1 for row in self.profiles
        ):
            raise BridgeError("same-level profiles must be exact ProfileRowV1 values")
        _exact_string_tuple(
            self.resolved_orbit_ids,
            "SameLevelRepairCandidateV1.resolved_orbit_ids",
        )
        _require_authority_none(self.authority_effect)

    @property
    def candidate_id(self) -> str:
        return domain_digest("omega.symbol-game.same-level-repair.v1", self)


@dataclass(frozen=True, slots=True)
class SameLevelRepair:
    candidate_ids: tuple[str, ...]
    kind: TerminalKind = TerminalKind.SAME_LEVEL_REPAIR
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(
        self,
        _terminal_type: type[TerminalKind] = TerminalKind,
    ) -> None:
        candidate_ids = _exact_string_tuple(
            self.candidate_ids, "SameLevelRepair.candidate_ids"
        )
        if not candidate_ids:
            raise BridgeError("same-level terminal result requires a candidate")
        if (
            type(self.kind) is not _terminal_type
            or self.kind is not _terminal_type.SAME_LEVEL_REPAIR
        ):
            raise BridgeError("same-level result has the wrong terminal kind")
        _require_authority_none(self.authority_effect)


@dataclass(frozen=True, slots=True)
class TypedRefusal:
    code: RefusalCode
    detail: str
    kind: TerminalKind = TerminalKind.TYPED_REFUSAL
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(
        self,
        _refusal_code_type: type[RefusalCode] = RefusalCode,
        _terminal_type: type[TerminalKind] = TerminalKind,
    ) -> None:
        if type(self.code) is not _refusal_code_type:
            raise BridgeError("TypedRefusal.code must be an exact RefusalCode")
        _exact_str(self.detail, "TypedRefusal.detail")
        if (
            type(self.kind) is not _terminal_type
            or self.kind is not _terminal_type.TYPED_REFUSAL
        ):
            raise BridgeError("typed refusal has the wrong terminal kind")
        _require_authority_none(self.authority_effect)


@dataclass(frozen=True, slots=True)
class SignatureMapRowV1:
    old: str
    new: str

    def __post_init__(self) -> None:
        _exact_str(self.old, "SignatureMapRowV1.old")
        _exact_str(self.new, "SignatureMapRowV1.new")


@dataclass(frozen=True, slots=True)
class RetractionRowV1:
    new: str
    old: str

    def __post_init__(self) -> None:
        _exact_str(self.new, "RetractionRowV1.new")
        _exact_str(self.old, "RetractionRowV1.old")


@dataclass(frozen=True, slots=True)
class StateMapRowV1:
    old: str
    new: str

    def __post_init__(self) -> None:
        _exact_str(self.old, "StateMapRowV1.old")
        _exact_str(self.new, "StateMapRowV1.new")


@dataclass(frozen=True, slots=True)
class ConservativeExtensionProposalV1:
    """A child presentation plus exact finite preservation tables."""

    parent_problem_id: str
    child_primitive: PrimitiveCarrierV1
    child_observer: ObserverPresentationV1
    state_embedding: tuple[StateMapRowV1, ...]
    state_retraction: tuple[RetractionRowV1, ...]
    signature_embedding: tuple[SignatureMapRowV1, ...]
    signature_retraction: tuple[RetractionRowV1, ...]
    resolved_orbit_ids: tuple[str, ...]
    producer_id: str
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        _exact_str(
            self.parent_problem_id,
            "ConservativeExtensionProposalV1.parent_problem_id",
        )
        if (
            type(self.child_primitive) is not PrimitiveCarrierV1
            or type(self.child_observer) is not ObserverPresentationV1
        ):
            raise BridgeError("CEC child values must have exact bridge types")
        for value, row_type, label in (
            (self.state_embedding, StateMapRowV1, "state_embedding"),
            (self.state_retraction, RetractionRowV1, "state_retraction"),
            (self.signature_embedding, SignatureMapRowV1, "signature_embedding"),
            (self.signature_retraction, RetractionRowV1, "signature_retraction"),
        ):
            if type(value) is not tuple or any(
                type(row) is not row_type for row in value
            ):
                raise BridgeError(f"{label} has a noncanonical row")
        _exact_string_tuple(
            self.resolved_orbit_ids,
            "ConservativeExtensionProposalV1.resolved_orbit_ids",
        )
        _exact_str(self.producer_id, "ConservativeExtensionProposalV1.producer_id")
        _require_authority_none(self.authority_effect)

    @property
    def proposal_id(self) -> str:
        return domain_digest(
            "omega.symbol-game.conservative-extension-proposal.v1", self
        )


@dataclass(frozen=True, slots=True)
class CECChildPacketV1:
    parent: BridgeProblemV1
    demand_orbits: tuple[DemandOrbitV1, ...]
    proposal: ConservativeExtensionProposalV1
    parent_event_id: str | None = None
    schema_version: str = BRIDGE_SCHEMA
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        if type(self.parent) is not BridgeProblemV1:
            raise BridgeError("CEC parent must be an exact BridgeProblemV1")
        if type(self.demand_orbits) is not tuple or any(
            type(orbit) is not DemandOrbitV1 for orbit in self.demand_orbits
        ):
            raise BridgeError("CEC demand orbits must be exact DemandOrbitV1 values")
        if type(self.proposal) is not ConservativeExtensionProposalV1:
            raise BridgeError("CEC proposal has the wrong runtime type")
        if self.parent_event_id is not None:
            _exact_str(self.parent_event_id, "CECChildPacketV1.parent_event_id")
        if self.schema_version != BRIDGE_SCHEMA:
            raise BridgeError("CEC child packet schema is unsupported")
        _require_authority_none(self.authority_effect)

    @property
    def packet_id(self) -> str:
        return domain_digest("omega.symbol-game.cec-child-packet.v1", self)


@dataclass(frozen=True, slots=True)
class CECChildEvaluationV1:
    packet_id: str
    accepted: bool
    checks: tuple[tuple[str, bool], ...]
    proposal_id: str
    resolved_orbit_ids: tuple[str, ...]
    replay_required: bool = True
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        _exact_str(self.packet_id, "CECChildEvaluationV1.packet_id")
        _exact_bool(self.accepted, "CECChildEvaluationV1.accepted")
        if type(self.checks) is not tuple or any(
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or type(row[1]) is not bool
            for row in self.checks
        ):
            raise BridgeError("CEC evaluation checks are not canonical")
        _exact_str(self.proposal_id, "CECChildEvaluationV1.proposal_id")
        _exact_string_tuple(
            self.resolved_orbit_ids,
            "CECChildEvaluationV1.resolved_orbit_ids",
        )
        if self.replay_required is not True:
            raise BridgeError("CEC evaluation must require replay")
        _require_authority_none(self.authority_effect)

    @property
    def receipt_id(self) -> str:
        return domain_digest("omega.symbol-game.cec-child-evaluation.v1", self)


@dataclass(frozen=True, slots=True)
class ConservativeExtensionProposal:
    evaluations: tuple[CECChildEvaluationV1, ...]
    kind: TerminalKind = TerminalKind.CONSERVATIVE_EXTENSION_PROPOSAL
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(
        self,
        _terminal_type: type[TerminalKind] = TerminalKind,
    ) -> None:
        if (
            type(self.evaluations) is not tuple
            or not self.evaluations
            or any(
                type(receipt) is not CECChildEvaluationV1 or not receipt.accepted
                for receipt in self.evaluations
            )
        ):
            raise BridgeError("CEC terminal result requires accepted exact evaluations")
        if (
            type(self.kind) is not _terminal_type
            or self.kind is not _terminal_type.CONSERVATIVE_EXTENSION_PROPOSAL
        ):
            raise BridgeError("CEC result has the wrong terminal kind")
        _require_authority_none(self.authority_effect)


@dataclass(frozen=True, slots=True)
class SearchExhaustionV1:
    same_level_declared_complete: bool
    cec_declared_complete: bool
    same_level_candidate_ids: tuple[str, ...]
    cec_packet_ids: tuple[str, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        _exact_bool(self.same_level_declared_complete, "same_level_declared_complete")
        _exact_bool(self.cec_declared_complete, "cec_declared_complete")
        _exact_string_tuple(
            self.same_level_candidate_ids,
            "SearchExhaustionV1.same_level_candidate_ids",
        )
        _exact_string_tuple(self.cec_packet_ids, "SearchExhaustionV1.cec_packet_ids")
        _require_authority_none(self.authority_effect)


TerminalOutcome = SameLevelRepair | TypedRefusal | ConservativeExtensionProposal


def _reconstructs_exactly(
    value: object,
    expected_type: type[object],
    *args: object,
    _closed: object = _closed_dataclass,
) -> bool:
    if type(value) is not expected_type or not _closed(value, expected_type):  # type: ignore[operator]
        return False
    try:
        rebuilt = expected_type(*args)
    except Exception:
        return False
    return rebuilt == value


def _primitive_replays(
    value: object,
    _primitive_type: type[PrimitiveCarrierV1] = PrimitiveCarrierV1,
    _retained_type: type[RetainedDiffV1] = RetainedDiffV1,
    _reconstruct: object = _reconstructs_exactly,
) -> bool:
    if type(value) is not _primitive_type:
        return False
    retained = value.retained_differences
    if type(retained) is not tuple or any(
        not _reconstruct(
            item,
            _retained_type,
            item.left,
            item.right,
            item.witness_id,
        )  # type: ignore[operator]
        for item in retained
    ):
        return False
    return _reconstruct(
        value,
        _primitive_type,
        value.carrier_id,
        value.states,
        retained,
        value.authority_effect,
    )  # type: ignore[operator]


def _observer_replays(
    value: object,
    _observer_type: type[ObserverPresentationV1] = ObserverPresentationV1,
    _profile_type: type[ProfileRowV1] = ProfileRowV1,
    _transition_type: type[TransitionRowV1] = TransitionRowV1,
    _reconstruct: object = _reconstructs_exactly,
) -> bool:
    if type(value) is not _observer_type:
        return False
    profiles = value.profiles
    transitions = value.transitions
    if type(profiles) is not tuple or any(
        not _reconstruct(row, _profile_type, row.state, row.features)  # type: ignore[operator]
        for row in profiles
    ):
        return False
    if type(transitions) is not tuple or any(
        not _reconstruct(  # type: ignore[operator]
            row, _transition_type, row.operation, row.state, row.result
        )
        for row in transitions
    ):
        return False
    return _reconstruct(
        value,
        _observer_type,
        value.primitive_id,
        value.signature_id,
        value.signature,
        profiles,
        transitions,
        value.protected_pairs,
        value.closure_policy,
        value.authority_effect,
    )  # type: ignore[operator]


def _problem_replays(
    value: object,
    _problem_type: type[BridgeProblemV1] = BridgeProblemV1,
    _primitive_replay: object = _primitive_replays,
    _observer_replay: object = _observer_replays,
    _reconstruct: object = _reconstructs_exactly,
) -> bool:
    if type(value) is not _problem_type:
        return False
    if not _primitive_replay(value.primitive) or not _observer_replay(value.observer):  # type: ignore[operator]
        return False
    return _reconstruct(  # type: ignore[operator]
        value, _problem_type, value.primitive, value.observer
    )


def _orbit_replays(
    value: object,
    _orbit_type: type[DemandOrbitV1] = DemandOrbitV1,
    _reconstruct: object = _reconstructs_exactly,
) -> bool:
    if type(value) is not _orbit_type:
        return False
    return _reconstruct(
        value,
        _orbit_type,
        value.problem_id,
        value.members,
        value.transports,
    )  # type: ignore[operator]


def _renaming_replays(
    value: object,
    _renaming_type: type[StateRenamingV1] = StateRenamingV1,
    _reconstruct: object = _reconstructs_exactly,
) -> bool:
    if type(value) is not _renaming_type:
        return False
    return _reconstruct(
        value,
        _renaming_type,
        value.source_problem_id,
        value.target_problem_id,
        value.source_states,
        value.target_states,
        value.image,
    )  # type: ignore[operator]


def _proposal_replays(
    value: object,
    _proposal_type: type[
        ConservativeExtensionProposalV1
    ] = ConservativeExtensionProposalV1,
    _primitive_replay: object = _primitive_replays,
    _observer_replay: object = _observer_replays,
    _state_row_type: type[StateMapRowV1] = StateMapRowV1,
    _retraction_row_type: type[RetractionRowV1] = RetractionRowV1,
    _signature_row_type: type[SignatureMapRowV1] = SignatureMapRowV1,
    _reconstruct: object = _reconstructs_exactly,
) -> bool:
    if type(value) is not _proposal_type:
        return False
    if not _primitive_replay(value.child_primitive) or not _observer_replay(  # type: ignore[operator]
        value.child_observer
    ):
        return False
    row_specs = (
        (value.state_embedding, _state_row_type, lambda row: (row.old, row.new)),
        (value.state_retraction, _retraction_row_type, lambda row: (row.new, row.old)),
        (
            value.signature_embedding,
            _signature_row_type,
            lambda row: (row.old, row.new),
        ),
        (
            value.signature_retraction,
            _retraction_row_type,
            lambda row: (row.new, row.old),
        ),
    )
    for rows, row_type, arguments in row_specs:
        if type(rows) is not tuple or any(
            not _reconstruct(row, row_type, *arguments(row))  # type: ignore[operator]
            for row in rows
        ):
            return False
    return _reconstruct(
        value,
        _proposal_type,
        value.parent_problem_id,
        value.child_primitive,
        value.child_observer,
        value.state_embedding,
        value.state_retraction,
        value.signature_embedding,
        value.signature_retraction,
        value.resolved_orbit_ids,
        value.producer_id,
        value.authority_effect,
    )  # type: ignore[operator]


def _packet_replays(
    value: object,
    _packet_type: type[CECChildPacketV1] = CECChildPacketV1,
    _problem_replay: object = _problem_replays,
    _proposal_replay: object = _proposal_replays,
    _orbit_replay: object = _orbit_replays,
    _reconstruct: object = _reconstructs_exactly,
) -> bool:
    if type(value) is not _packet_type:
        return False
    if (
        not _problem_replay(value.parent)  # type: ignore[operator]
        or not _proposal_replay(value.proposal)  # type: ignore[operator]
        or type(value.demand_orbits) is not tuple
        or any(not _orbit_replay(orbit) for orbit in value.demand_orbits)  # type: ignore[operator]
    ):
        return False
    return _reconstruct(
        value,
        _packet_type,
        value.parent,
        value.demand_orbits,
        value.proposal,
        value.parent_event_id,
        value.schema_version,
        value.authority_effect,
    )  # type: ignore[operator]


def _same_level_candidate_replays(
    value: object,
    _candidate_type: type[SameLevelRepairCandidateV1] = SameLevelRepairCandidateV1,
    _profile_type: type[ProfileRowV1] = ProfileRowV1,
    _reconstruct: object = _reconstructs_exactly,
) -> bool:
    if type(value) is not _candidate_type or type(value.profiles) is not tuple:
        return False
    if any(
        type(row) is not _profile_type
        or not _reconstruct(row, _profile_type, row.state, row.features)  # type: ignore[operator]
        for row in value.profiles
    ):
        return False
    return _reconstruct(  # type: ignore[operator]
        value,
        _candidate_type,
        value.problem_id,
        value.carrier_id,
        value.signature_id,
        value.profiles,
        value.resolved_orbit_ids,
        value.producer_id,
        value.authority_effect,
    )


def _exhaustion_replays(
    value: object,
    _exhaustion_type: type[SearchExhaustionV1] = SearchExhaustionV1,
    _reconstruct: object = _reconstructs_exactly,
) -> bool:
    if type(value) is not _exhaustion_type:
        return False
    return _reconstruct(  # type: ignore[operator]
        value,
        _exhaustion_type,
        value.same_level_declared_complete,
        value.cec_declared_complete,
        value.same_level_candidate_ids,
        value.cec_packet_ids,
        value.authority_effect,
    )


def _profiles_by_state(rows: tuple[ProfileRowV1, ...]) -> dict[str, tuple[str, ...]]:
    return {row.state: row.features for row in rows}


def validate_same_level_repair(
    problem: BridgeProblemV1,
    candidate: SameLevelRepairCandidateV1,
    orbits: tuple[DemandOrbitV1, ...],
) -> bool:
    if (
        not _problem_replays(problem)
        or not _same_level_candidate_replays(candidate)
        or type(orbits) is not tuple
        or any(not _orbit_replays(orbit) for orbit in orbits)
    ):
        return False
    if (
        candidate.problem_id != problem.problem_id
        or candidate.carrier_id != problem.primitive.carrier_id
        or candidate.signature_id != problem.observer.signature_id
        or not _authority_is_none(candidate.authority_effect)
        or type(candidate.profiles) is not tuple
        or tuple(row.state for row in candidate.profiles)
        != tuple(sorted(problem.primitive.states))
    ):
        return False
    if any(type(row) is not ProfileRowV1 for row in candidate.profiles):
        return False
    if any(
        feature not in problem.observer.signature
        for row in candidate.profiles
        for feature in row.features
    ):
        return False
    before = _profiles_by_state(problem.observer.profiles)
    after = _profiles_by_state(candidate.profiles)
    # Every old visible distinction remains visible.
    for left, right in combinations(problem.primitive.states, 2):
        if before[left] != before[right] and after[left] == after[right]:
            return False
    expected_orbits = {orbit.orbit_id for orbit in orbits}
    if set(candidate.resolved_orbit_ids) != expected_orbits:
        return False
    for orbit in orbits:
        if any(after[left] == after[right] for left, right in orbit.members):
            return False
    return True


def _oracle_validate_same_level_repair(
    problem: BridgeProblemV1,
    candidate: SameLevelRepairCandidateV1,
    orbits: tuple[DemandOrbitV1, ...],
    _problem_replay: object = _problem_replays,
    _candidate_replay: object = _same_level_candidate_replays,
    _orbit_replay: object = _orbit_replays,
    _profile_map: object = _profiles_by_state,
) -> bool:
    """Admission-local same-level replay independent of the public validator."""

    if (
        not _problem_replay(problem)  # type: ignore[operator]
        or not _candidate_replay(candidate)  # type: ignore[operator]
        or type(orbits) is not tuple
        or any(not _orbit_replay(orbit) for orbit in orbits)  # type: ignore[operator]
        or candidate.problem_id != problem.problem_id
        or candidate.carrier_id != problem.primitive.carrier_id
        or candidate.signature_id != problem.observer.signature_id
        or type(problem.primitive.authority_effect) is not str
        or problem.primitive.authority_effect != "None"
        or type(problem.observer.authority_effect) is not str
        or problem.observer.authority_effect != "None"
        or type(candidate.authority_effect) is not str
        or candidate.authority_effect != "None"
        or tuple(row.state for row in candidate.profiles)
        != tuple(sorted(problem.primitive.states))
        or any(
            feature not in problem.observer.signature
            for row in candidate.profiles
            for feature in row.features
        )
    ):
        return False
    before = _profile_map(problem.observer.profiles)  # type: ignore[operator]
    after = _profile_map(candidate.profiles)  # type: ignore[operator]
    if any(
        before[left] != before[right] and after[left] == after[right]
        for left, right in combinations(problem.primitive.states, 2)
    ):
        return False
    expected = {orbit.orbit_id for orbit in orbits}
    return (
        type(candidate.resolved_orbit_ids) is tuple
        and set(candidate.resolved_orbit_ids) == expected
        and len(candidate.resolved_orbit_ids) == len(expected)
        and all(
            after[left] != after[right]
            for orbit in orbits
            for left, right in orbit.members
        )
    )


def _cec_checks(packet: CECChildPacketV1) -> tuple[tuple[str, bool], ...]:
    parent = packet.parent
    proposal = packet.proposal
    child_problem: BridgeProblemV1 | None = None
    try:
        child_problem = BridgeProblemV1(
            proposal.child_primitive, proposal.child_observer
        )
    except (BridgeError, CanonicalizationError):
        pass
    checks: list[tuple[str, bool]] = []
    checks.append(("exact_packet_type", type(packet) is CECChildPacketV1))
    checks.append(("exact_parent_type", type(parent) is BridgeProblemV1))
    checks.append(
        ("exact_proposal_type", type(proposal) is ConservativeExtensionProposalV1)
    )
    checks.append(("packet_reconstructs", _packet_replays(packet)))
    checks.append(("parent_bound", proposal.parent_problem_id == parent.problem_id))
    checks.append(("child_well_formed", child_problem is not None))
    checks.append(
        (
            "new_ids",
            proposal.child_primitive.carrier_id != parent.primitive.carrier_id
            or proposal.child_observer.signature_id != parent.observer.signature_id,
        )
    )
    checks.append(
        (
            "authority_none",
            all(
                _authority_is_none(value)
                for value in (
                    packet.authority_effect,
                    parent.primitive.authority_effect,
                    parent.observer.authority_effect,
                    proposal.authority_effect,
                    proposal.child_primitive.authority_effect,
                    proposal.child_observer.authority_effect,
                )
            ),
        )
    )

    old_states = parent.primitive.states
    new_states = proposal.child_primitive.states
    state_map = {
        row.old: row.new
        for row in proposal.state_embedding
        if type(row) is StateMapRowV1
    }
    state_back = {
        row.new: row.old
        for row in proposal.state_retraction
        if type(row) is RetractionRowV1
    }
    state_embedding_total = (
        type(proposal.state_embedding) is tuple
        and len(state_map) == len(proposal.state_embedding) == len(old_states)
        and tuple(sorted(state_map)) == tuple(sorted(old_states))
        and len(set(state_map.values())) == len(old_states)
        and all(value in new_states for value in state_map.values())
    )
    state_retraction_total = (
        (
            type(proposal.state_retraction) is tuple
            and len(state_back) == len(proposal.state_retraction) == len(new_states)
            and tuple(sorted(state_back)) == tuple(sorted(new_states))
            and all(value in old_states for value in state_back.values())
            and all(state_back[state_map[old]] == old for old in old_states)
        )
        if state_embedding_total
        else False
    )
    checks.append(("state_embedding", state_embedding_total))
    checks.append(("state_retraction", state_retraction_total))

    old_sig = parent.observer.signature
    new_sig = proposal.child_observer.signature
    sig_map = {
        row.old: row.new
        for row in proposal.signature_embedding
        if type(row) is SignatureMapRowV1
    }
    sig_back = {
        row.new: row.old
        for row in proposal.signature_retraction
        if type(row) is RetractionRowV1
    }
    sig_embedding_total = (
        type(proposal.signature_embedding) is tuple
        and len(sig_map) == len(proposal.signature_embedding) == len(old_sig)
        and tuple(sorted(sig_map)) == tuple(sorted(old_sig))
        and len(set(sig_map.values())) == len(old_sig)
        and all(value in new_sig for value in sig_map.values())
    )
    sig_retraction_total = (
        (
            type(proposal.signature_retraction) is tuple
            and len(sig_back) == len(proposal.signature_retraction) == len(new_sig)
            and tuple(sorted(sig_back)) == tuple(sorted(new_sig))
            and all(value in old_sig for value in sig_back.values())
            and all(sig_back[sig_map[old]] == old for old in old_sig)
        )
        if sig_embedding_total
        else False
    )
    checks.append(("signature_embedding", sig_embedding_total))
    checks.append(("signature_retraction", sig_retraction_total))
    genuinely_new = (
        state_embedding_total
        and sig_embedding_total
        and (
            set(state_map.values()) != set(new_states)
            or set(sig_map.values()) != set(new_sig)
        )
    )
    checks.append(("genuinely_new_structure", genuinely_new))

    if child_problem is None or not state_embedding_total or not sig_retraction_total:
        transition_preserved = retained_preserved = protected_preserved = (
            profiles_preserved
        ) = zero_refines = False
    else:
        child_retained = {
            item.pair for item in child_problem.primitive.retained_differences
        }
        retained_preserved = all(
            _normalized_pair(state_map[item.left], state_map[item.right])
            in child_retained
            for item in parent.primitive.retained_differences
        )
        child_protected = set(declared_protected_pairs(child_problem))
        protected_preserved = all(
            _map_pair(pair, state_map) in child_protected
            for pair in declared_protected_pairs(parent)
        )
        old_profiles = _profiles_by_state(parent.observer.profiles)
        new_profiles = _profiles_by_state(child_problem.observer.profiles)
        profiles_preserved = all(
            tuple(
                sorted(
                    {sig_back[feature] for feature in new_profiles[state_map[state]]}
                )
            )
            == old_profiles[state]
            for state in old_states
        )
        transition_preserved = all(
            child_problem.observer.transition(sig_map[operation], state_map[state])
            == state_map[parent.observer.transition(operation, state)]
            for operation in old_sig
            for state in old_states
        )
        zero_refines = all(
            new_profiles[state_map[left]] != new_profiles[state_map[right]]
            or old_profiles[left] == old_profiles[right]
            for left, right in combinations(old_states, 2)
        )
    checks.append(("retained_preserved", retained_preserved))
    checks.append(("protected_preserved", protected_preserved))
    checks.append(("profiles_project_to_parent", profiles_preserved))
    checks.append(("old_transitions_commute", transition_preserved))
    checks.append(("zero_relation_refines", zero_refines))

    try:
        canonical_orbits = demand_orbits(parent)
    except (BridgeError, CanonicalizationError, TypeError, ValueError):
        canonical_orbits = ()
    orbits_canonical = packet.demand_orbits == canonical_orbits
    checks.append(("demand_orbits_canonical", orbits_canonical))
    expected_orbits = {orbit.orbit_id for orbit in canonical_orbits}
    orbit_ids_exact = (
        type(packet.demand_orbits) is tuple
        and orbits_canonical
        and all(
            type(orbit) is DemandOrbitV1 and orbit.problem_id == parent.problem_id
            for orbit in packet.demand_orbits
        )
        and set(proposal.resolved_orbit_ids) == expected_orbits
        and len(proposal.resolved_orbit_ids) == len(expected_orbits)
    )
    checks.append(("orbit_ids_exact", orbit_ids_exact))
    if child_problem is None or not state_embedding_total:
        resolves = False
    else:
        child_profiles = _profiles_by_state(child_problem.observer.profiles)
        resolves = all(
            child_profiles[state_map[left]] != child_profiles[state_map[right]]
            for orbit in packet.demand_orbits
            for left, right in orbit.members
        )
    checks.append(("all_orbit_members_resolved", resolves))
    return tuple(checks)


def evaluate_cec_child_packet(packet: CECChildPacketV1) -> CECChildEvaluationV1:
    """Independently replay every finite CEC preservation obligation."""

    if type(packet) is not CECChildPacketV1:
        raise BridgeError("CEC evaluator requires an exact CECChildPacketV1")
    try:
        checks = _cec_checks(packet)
        packet_id = packet.packet_id
        proposal_id = packet.proposal.proposal_id
        resolved_orbit_ids = packet.proposal.resolved_orbit_ids
    except Exception as error:
        raise BridgeError("CEC packet replay failed closed") from error
    return CECChildEvaluationV1(
        packet_id=packet_id,
        accepted=all(value for _, value in checks),
        checks=checks,
        proposal_id=proposal_id,
        resolved_orbit_ids=resolved_orbit_ids,
    )


def _oracle_cec_checks(
    packet: CECChildPacketV1,
    _packet_type: type[CECChildPacketV1] = CECChildPacketV1,
    _parent_type: type[BridgeProblemV1] = BridgeProblemV1,
    _proposal_type: type[
        ConservativeExtensionProposalV1
    ] = ConservativeExtensionProposalV1,
    _state_row_type: type[StateMapRowV1] = StateMapRowV1,
    _retraction_row_type: type[RetractionRowV1] = RetractionRowV1,
    _signature_row_type: type[SignatureMapRowV1] = SignatureMapRowV1,
    _demand_orbits: object = _oracle_demand_orbits,
    _declared_pairs: object = declared_protected_pairs,
    _normalize_pair: object = _normalized_pair,
    _map_declared_pair: object = _map_pair,
    _packet_replay: object = _packet_replays,
    _profile_map: object = _profiles_by_state,
) -> tuple[tuple[str, bool], ...]:
    """Admission-local semantic replay independent of the producer checker."""

    if type(packet) is not _packet_type:
        raise BridgeError("admission oracle requires the canonical packet type")
    parent = packet.parent
    proposal = packet.proposal
    if type(parent) is not _parent_type or type(proposal) is not _proposal_type:
        raise BridgeError("admission oracle requires canonical nested types")
    try:
        child = _parent_type(proposal.child_primitive, proposal.child_observer)
        canonical_orbits = _demand_orbits(parent)  # type: ignore[operator]
    except (BridgeError, CanonicalizationError, TypeError, ValueError):
        child = None
        canonical_orbits = ()
    old_states = parent.primitive.states
    new_states = proposal.child_primitive.states
    old_signature = parent.observer.signature
    new_signature = proposal.child_observer.signature
    state_embedding = {
        row.old: row.new
        for row in proposal.state_embedding
        if type(row) is _state_row_type
    }
    state_retraction = {
        row.new: row.old
        for row in proposal.state_retraction
        if type(row) is _retraction_row_type
    }
    signature_embedding = {
        row.old: row.new
        for row in proposal.signature_embedding
        if type(row) is _signature_row_type
    }
    signature_retraction = {
        row.new: row.old
        for row in proposal.signature_retraction
        if type(row) is _retraction_row_type
    }
    state_ok = (
        type(proposal.state_embedding) is tuple
        and type(proposal.state_retraction) is tuple
        and len(state_embedding) == len(proposal.state_embedding) == len(old_states)
        and set(state_embedding) == set(old_states)
        and len(set(state_embedding.values())) == len(old_states)
        and set(state_embedding.values()).issubset(new_states)
        and len(state_retraction) == len(proposal.state_retraction) == len(new_states)
        and set(state_retraction) == set(new_states)
        and set(state_retraction.values()).issubset(old_states)
        and all(
            state_retraction[state_embedding[state]] == state for state in old_states
        )
    )
    signature_ok = (
        type(proposal.signature_embedding) is tuple
        and type(proposal.signature_retraction) is tuple
        and len(signature_embedding)
        == len(proposal.signature_embedding)
        == len(old_signature)
        and set(signature_embedding) == set(old_signature)
        and len(set(signature_embedding.values())) == len(old_signature)
        and set(signature_embedding.values()).issubset(new_signature)
        and len(signature_retraction)
        == len(proposal.signature_retraction)
        == len(new_signature)
        and set(signature_retraction) == set(new_signature)
        and set(signature_retraction.values()).issubset(old_signature)
        and all(
            signature_retraction[signature_embedding[operation]] == operation
            for operation in old_signature
        )
    )
    new_structure = (
        state_ok
        and signature_ok
        and (
            set(state_embedding.values()) != set(new_states)
            or set(signature_embedding.values()) != set(new_signature)
        )
    )
    if child is None or not state_ok or not signature_ok:
        transition_ok = retained_ok = protected_ok = profile_ok = refinement_ok = (
            resolved
        ) = False
    else:
        old_profiles = _profile_map(parent.observer.profiles)  # type: ignore[operator]
        new_profiles = _profile_map(child.observer.profiles)  # type: ignore[operator]
        child_retained = {item.pair for item in child.primitive.retained_differences}
        retained_ok = all(
            _normalize_pair(state_embedding[item.left], state_embedding[item.right])  # type: ignore[operator]
            in child_retained
            for item in parent.primitive.retained_differences
        )
        child_protected = set(_declared_pairs(child))  # type: ignore[operator]
        protected_ok = all(
            _map_declared_pair(pair, state_embedding) in child_protected  # type: ignore[operator]
            for pair in _declared_pairs(parent)  # type: ignore[operator]
        )
        profile_ok = all(
            tuple(
                sorted(
                    {
                        signature_retraction[feature]
                        for feature in new_profiles[state_embedding[state]]
                    }
                )
            )
            == old_profiles[state]
            for state in old_states
        )
        transition_ok = all(
            child.observer.transition(
                signature_embedding[operation], state_embedding[state]
            )
            == state_embedding[parent.observer.transition(operation, state)]
            for operation in old_signature
            for state in old_states
        )
        refinement_ok = all(
            new_profiles[state_embedding[left]] != new_profiles[state_embedding[right]]
            or old_profiles[left] == old_profiles[right]
            for left, right in combinations(old_states, 2)
        )
        resolved = all(
            new_profiles[state_embedding[left]] != new_profiles[state_embedding[right]]
            for orbit in canonical_orbits
            for left, right in orbit.members
        )
    exact_orbits = packet.demand_orbits == canonical_orbits
    expected_orbit_ids = {orbit.orbit_id for orbit in canonical_orbits}
    orbit_ids_ok = (
        exact_orbits
        and set(proposal.resolved_orbit_ids) == expected_orbit_ids
        and len(proposal.resolved_orbit_ids) == len(expected_orbit_ids)
    )
    return (
        ("exact_packet_type", type(packet) is _packet_type),
        ("exact_parent_type", type(parent) is _parent_type),
        ("exact_proposal_type", type(proposal) is _proposal_type),
        ("packet_reconstructs", bool(_packet_replay(packet))),  # type: ignore[operator]
        ("parent_bound", proposal.parent_problem_id == parent.problem_id),
        ("child_well_formed", child is not None),
        (
            "new_ids",
            proposal.child_primitive.carrier_id != parent.primitive.carrier_id
            or proposal.child_observer.signature_id != parent.observer.signature_id,
        ),
        (
            "authority_none",
            all(
                type(value) is str and value == "None"
                for value in (
                    packet.authority_effect,
                    parent.primitive.authority_effect,
                    parent.observer.authority_effect,
                    proposal.authority_effect,
                    proposal.child_primitive.authority_effect,
                    proposal.child_observer.authority_effect,
                )
            ),
        ),
        ("state_embedding", state_ok),
        ("state_retraction", state_ok),
        ("signature_embedding", signature_ok),
        ("signature_retraction", signature_ok),
        ("genuinely_new_structure", new_structure),
        ("retained_preserved", retained_ok),
        ("protected_preserved", protected_ok),
        ("profiles_project_to_parent", profile_ok),
        ("old_transitions_commute", transition_ok),
        ("zero_relation_refines", refinement_ok),
        ("demand_orbits_canonical", exact_orbits),
        ("orbit_ids_exact", orbit_ids_ok),
        ("all_orbit_members_resolved", resolved),
    )


def _replay_cec_child_packet_impl(
    packet: CECChildPacketV1,
    receipt: CECChildEvaluationV1,
    _packet_type: type[CECChildPacketV1] = CECChildPacketV1,
    _receipt_type: type[CECChildEvaluationV1] = CECChildEvaluationV1,
    _producer_evaluate: object = evaluate_cec_child_packet,
    _admission_oracle: object = _oracle_cec_checks,
    _closed: object = _closed_dataclass,
) -> bool:
    """Require an exact receipt to equal a fresh semantic replay."""

    if type(packet) is not _packet_type or type(receipt) is not _receipt_type:
        return False
    if not _closed(packet, _packet_type) or not _closed(  # type: ignore[operator]
        receipt,
        _receipt_type,  # type: ignore[operator]
    ):
        return False
    try:
        expected = _producer_evaluate(packet)  # type: ignore[operator]
        oracle_checks = _admission_oracle(packet)  # type: ignore[operator]
    except (BridgeError, CanonicalizationError, TypeError, ValueError):
        return False
    return (
        receipt == expected
        and receipt.checks == oracle_checks
        and receipt.accepted is all(value for _, value in oracle_checks)
        and receipt.replay_required is True
        and type(receipt.authority_effect) is str
        and receipt.authority_effect == "None"
    )


def _make_replay_entrypoint(implementation: object) -> object:
    def entrypoint(packet: CECChildPacketV1, receipt: CECChildEvaluationV1) -> bool:
        return implementation(packet, receipt)  # type: ignore[operator]

    entrypoint.__name__ = "replay_cec_child_packet"
    entrypoint.__qualname__ = "replay_cec_child_packet"
    return entrypoint


replay_cec_child_packet = _make_replay_entrypoint(_replay_cec_child_packet_impl)


def _terminalize_declared_search_impl(
    problem: BridgeProblemV1,
    same_level: tuple[SameLevelRepairCandidateV1, ...],
    cec_packets: tuple[CECChildPacketV1, ...],
    exhaustion: SearchExhaustionV1,
    _orbit_builder: object = demand_orbits,
    _orbit_oracle: object = _oracle_demand_orbits,
    _same_level_validator: object = validate_same_level_repair,
    _same_level_oracle: object = _oracle_validate_same_level_repair,
    _cec_evaluator: object = evaluate_cec_child_packet,
    _cec_replay: object = replay_cec_child_packet,
    _problem_replay: object = _problem_replays,
    _candidate_replay: object = _same_level_candidate_replays,
    _exhaustion_replay: object = _exhaustion_replays,
    _same_level_result_type: type[SameLevelRepair] = SameLevelRepair,
    _refusal_result_type: type[TypedRefusal] = TypedRefusal,
    _cec_result_type: type[
        ConservativeExtensionProposal
    ] = ConservativeExtensionProposal,
    _no_active_code: RefusalCode = RefusalCode.NO_ACTIVE_OBSTRUCTION,
    _incomplete_code: RefusalCode = RefusalCode.INCOMPLETE_SEARCH_EVIDENCE,
    _no_response_code: RefusalCode = RefusalCode.NO_ADMISSIBLE_RESPONSE,
) -> TerminalOutcome:
    """Total and exclusive controller trichotomy over declared finite inputs."""

    try:
        controller_inputs_valid = (
            _problem_replay(problem)  # type: ignore[operator]
            and type(problem.primitive.authority_effect) is str
            and problem.primitive.authority_effect == "None"
            and type(problem.observer.authority_effect) is str
            and problem.observer.authority_effect == "None"
            and type(same_level) is tuple
            and all(_candidate_replay(item) for item in same_level)  # type: ignore[operator]
            and type(cec_packets) is tuple
            and type(exhaustion) is SearchExhaustionV1
            and _exhaustion_replay(exhaustion)  # type: ignore[operator]
        )
    except Exception:
        controller_inputs_valid = False
    if not controller_inputs_valid:
        return _refusal_result_type(
            _incomplete_code,
            "controller inputs failed exact replay",
        )
    try:
        orbits = _orbit_builder(problem)  # type: ignore[operator]
        oracle_orbits = _orbit_oracle(problem)  # type: ignore[operator]
    except Exception:
        return _refusal_result_type(
            _incomplete_code,
            "demand-orbit construction failed closed",
        )
    if orbits != oracle_orbits:
        return _refusal_result_type(
            _incomplete_code,
            "producer and admission demand orbits disagree",
        )
    if not orbits:
        return _refusal_result_type(
            _no_active_code, "no protected retained observer-zero demand"
        )
    try:
        valid_repairs = tuple(
            sorted(
                {
                    candidate.candidate_id
                    for candidate in same_level
                    if _same_level_validator(problem, candidate, orbits)  # type: ignore[operator]
                    and _same_level_oracle(problem, candidate, orbits)  # type: ignore[operator]
                }
            )
        )
    except Exception:
        return _refusal_result_type(
            _incomplete_code,
            "same-level validation failed closed",
        )
    if valid_repairs:
        return _same_level_result_type(valid_repairs)
    try:
        expected_same_ids = tuple(
            sorted(candidate.candidate_id for candidate in same_level)
        )
        expected_cec_ids = tuple(sorted(packet.packet_id for packet in cec_packets))
    except Exception:
        return _refusal_result_type(
            _incomplete_code,
            "candidate identity replay failed closed",
        )
    same_level_complete = (
        type(exhaustion) is SearchExhaustionV1
        and type(exhaustion.authority_effect) is str
        and exhaustion.authority_effect == "None"
        and exhaustion.same_level_declared_complete is True
        and tuple(sorted(exhaustion.same_level_candidate_ids)) == expected_same_ids
    )
    replayed_extensions: list[tuple[CECChildPacketV1, CECChildEvaluationV1]] = []
    for packet in cec_packets:
        try:
            receipt = _cec_evaluator(packet)  # type: ignore[operator]
            if receipt.accepted and _cec_replay(packet, receipt):  # type: ignore[operator]
                replayed_extensions.append((packet, receipt))
        except Exception:
            continue
    unique_replayed: list[tuple[CECChildPacketV1, CECChildEvaluationV1]] = []
    for packet, receipt in replayed_extensions:
        if not any(packet == prior for prior, _ in unique_replayed):
            unique_replayed.append((packet, receipt))
    accepted_extensions = tuple(receipt for _, receipt in unique_replayed)
    if accepted_extensions and same_level_complete:
        return _cec_result_type(accepted_extensions)
    complete = (
        same_level_complete
        and exhaustion.cec_declared_complete is True
        and tuple(sorted(exhaustion.cec_packet_ids)) == expected_cec_ids
    )
    if complete:
        return _refusal_result_type(
            _no_response_code, "declared finite repair and CEC families exhausted"
        )
    return _refusal_result_type(
        _incomplete_code, "search exhaustion was not replay-complete"
    )


def _make_terminal_entrypoint(implementation: object) -> object:
    def entrypoint(
        problem: BridgeProblemV1,
        same_level: tuple[SameLevelRepairCandidateV1, ...],
        cec_packets: tuple[CECChildPacketV1, ...],
        exhaustion: SearchExhaustionV1,
    ) -> TerminalOutcome:
        return implementation(  # type: ignore[operator]
            problem, same_level, cec_packets, exhaustion
        )

    entrypoint.__name__ = "terminalize_declared_search"
    entrypoint.__qualname__ = "terminalize_declared_search"
    return entrypoint


terminalize_declared_search = _make_terminal_entrypoint(
    _terminalize_declared_search_impl
)


def terminal_kind(outcome: TerminalOutcome) -> TerminalKind:
    """Closed exact-type eliminator used by parity tests and host adapters."""

    if type(outcome) is SameLevelRepair:
        return TerminalKind.SAME_LEVEL_REPAIR
    if type(outcome) is TypedRefusal:
        return TerminalKind.TYPED_REFUSAL
    if type(outcome) is ConservativeExtensionProposal:
        return TerminalKind.CONSERVATIVE_EXTENSION_PROPOSAL
    raise BridgeError("terminal outcome is outside the closed trichotomy")


__all__ = [
    "AUTHORITY_EFFECT_NONE",
    "ActiveObstructionV1",
    "BridgeError",
    "BridgeProblemV1",
    "CECChildEvaluationV1",
    "CECChildPacketV1",
    "ClosurePolicy",
    "ConservativeExtensionProposal",
    "ConservativeExtensionProposalV1",
    "DemandOrbitV1",
    "ObserverPresentationV1",
    "PrimitiveCarrierV1",
    "ProfileDifferenceV1",
    "ProfileRowV1",
    "RefusalCode",
    "RetainedDiffV1",
    "RetractionRowV1",
    "SameLevelRepair",
    "SameLevelRepairCandidateV1",
    "SearchExhaustionV1",
    "SignatureMapRowV1",
    "StateMapRowV1",
    "StateRenamingV1",
    "TerminalKind",
    "TransitionRowV1",
    "TypedRefusal",
    "active_obstruction_of_components",
    "active_obstructions",
    "declared_protected_pairs",
    "demand_orbits",
    "evaluate_cec_child_packet",
    "orbit_transition_congruent",
    "profile_difference",
    "replay_cec_child_packet",
    "terminal_kind",
    "terminalize_declared_search",
    "validate_same_level_repair",
    "zero_rel_r",
]
