"""Candidate-bound use of one existing finite research checker.

``edge_endpoints`` checks a bounded relation structure, including host-selected
protected pairs. Fixture calibration is recorded separately from the candidate
verdict. Neither result is a theorem, a new reach certificate or new authority.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from importlib.resources import files
from pathlib import Path

from omega_engine_operations.domain.level_engine_context import (
    ContextRefusal,
    LevelEngineResourcesPort,
    configure_context,
)
from omega_engine_pfp.domain.tower.level_engine import LevelEngineOutcome
from omega_engine_pfp.infrastructure.tower_evidence.level_engine import EvidenceRefusal

from .runner import ResearchLevelEngineRunner

_CHALLENGE = "edge_endpoints"
_MAX_BYTES = 65_536
_MAX_ELEMENTS = 18
_MAX_ARCS = 64
_MAX_PROTECTED = 8
_ENGINE_REQUIRED = (
    "level.py", "encoding.py", "kinds.py", "sealed.py", "regimek.py", "search.py",
    "structure.py", "components.py", "canon.py", "guards.py", "errors.py", "exact/q.py",
)


@dataclass(frozen=True)
class FiniteCandidateBinding:
    challenge_id: str
    candidate_sha256: str
    protected_pairs: tuple[tuple[int, int], ...]
    checker_sha256: str
    source_sha256: str
    fixture_set_sha256: str
    resource_sha256: str


@dataclass(frozen=True)
class FiniteCandidateCheck:
    binding: FiniteCandidateBinding
    replay: LevelEngineOutcome
    accepted: bool
    candidate_code: str
    failed_clauses: tuple[str, ...]
    authority_effect: str = field(default="None", init=False)

    @property
    def evidence_grade(self) -> str:
        return self.replay.evidence_grade


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise EvidenceRefusal("FINITE_COMPONENT_UNAVAILABLE", path.name) from exc


def _manifest(entries: dict[str, bytes]) -> str:
    document = {name: _digest(raw) for name, raw in sorted(entries.items())}
    return _digest(json.dumps(document, sort_keys=True, separators=(",", ":")).encode("ascii"))


def _inputs(challenge_id: str, candidate_bytes: bytes, protected_pairs: object) -> None:
    if challenge_id != _CHALLENGE:
        raise EvidenceRefusal("UNSUPPORTED_FINITE_CHALLENGE", "Only edge_endpoints is supported")
    if type(candidate_bytes) is not bytes or not 0 < len(candidate_bytes) <= _MAX_BYTES:
        raise EvidenceRefusal("FINITE_CANDIDATE_SIZE_OR_TYPE", "Expected 1..65536 actual bytes")
    if (
        type(protected_pairs) is not tuple or not 1 <= len(protected_pairs) <= _MAX_PROTECTED
        or any(
            type(pair) is not tuple or len(pair) != 2
            or any(type(index) is not int or not 0 <= index < _MAX_ELEMENTS for index in pair)
            or pair[0] == pair[1]
            for pair in protected_pairs
        )
    ):
        raise EvidenceRefusal("INVALID_PROTECTED_PAIRS", "Expected 1..8 host-selected index pairs")


def _checker_sources() -> dict[str, bytes]:
    operations = Path(str(files("omega_engine_operations")))
    engine = operations / "use_cases" / "level_engine" / "research_engine"
    checker = {"engine/" + name: _read(engine / name) for name in _ENGINE_REQUIRED}
    checker["domain/level_engine_context.py"] = _read(operations / "domain/level_engine_context.py")
    checker.update({"engine/" + path.relative_to(engine).as_posix(): _read(path)
                    for path in engine.rglob("*.py")})
    for name in ("finite_consumer.py", "runner.py", "context.py", "vendor_loading.py"):
        checker["consumer/" + name] = _read(Path(__file__).parent / name)
    checker["spec/edge_endpoints.py"] = _read(
        Path(__file__).parent / "payload/edge_endpoints/spec.py")
    return checker


def _vendor_sources(vendor: Path) -> dict[str, bytes]:
    """Compare consumed bytes with Git blobs, including index-hidden changes."""
    result = subprocess.run(["git", "-C", str(vendor), "ls-tree", "-rz", "HEAD", "--",
        "code/derivation", "research/partial_decide"], capture_output=True, check=False)
    if result.returncode:
        raise EvidenceRefusal("RR-PIN", "The pinned vendor tree is unavailable")
    blobs = {}
    for entry in result.stdout.split(b"\0"):
        if entry:
            metadata, name = entry.split(b"\t", 1)
            mode, kind, oid = metadata.split()
            if kind == b"blob" and mode in (b"100644", b"100755"):
                blobs[name.decode("utf-8")] = oid.decode("ascii")
    required = {"code/derivation/model.py", "code/derivation/candidates.py",
        "code/derivation/iso.py", "code/derivation/observe.py",
        "research/partial_decide/partial_decide.py"}
    names = required | {path.relative_to(vendor).as_posix()
        for root in ("code/derivation", "research/partial_decide")
        for path in (vendor / root).rglob("*.py")}
    sources = {}
    for name in sorted(names):
        raw = _read(vendor / name)
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        if blobs.get(name) != blob:
            raise EvidenceRefusal("RR-PIN", "Consumed vendor bytes differ from the pinned Git tree")
        sources["vendor/" + name] = raw
    return sources


class FiniteLevelEngineConsumer:
    """No provider calls, candidate writes, context switching or new certification."""

    def __init__(self, context: LevelEngineResourcesPort, *,
                 protected_pairs: tuple[tuple[int, int], ...] = ((0, 2),)) -> None:
        _inputs(_CHALLENGE, b"scope", protected_pairs)
        self.context = context
        self._protected_pairs = protected_pairs

    def prepare(
        self, challenge_id: str, candidate_bytes: bytes, *,
        protected_pairs: tuple[tuple[int, int], ...] | None = None,
    ) -> FiniteCandidateBinding:
        """Freeze exact candidate and checker inputs before checking, not a verdict."""
        protected_pairs = self._protected_pairs if protected_pairs is None else protected_pairs
        _inputs(challenge_id, candidate_bytes, protected_pairs)
        if protected_pairs != self._protected_pairs:
            raise EvidenceRefusal("PROTECTED_BINDING_MISMATCH", "The consumer's host obligation differs")
        try:
            vendor = self.context.require_vendor()
        except (ContextRefusal, OSError, ValueError, KeyError) as exc:
            raise EvidenceRefusal(getattr(exc, "code", "FINITE_COMPONENT_UNAVAILABLE"), str(exc)) from exc
        payload = self.context.resource("payload/edge_endpoints")
        checker = _checker_sources()
        checker_sha256 = _manifest(checker)
        if checker_sha256 != _IMPORTED_CHECKER_SHA256:
            raise EvidenceRefusal("STALE_CHECKER_PROCESS", "Start a fresh process after checker source changes")
        source = checker["spec/edge_endpoints.py"]
        if _read(payload / "spec.py") != source:
            raise EvidenceRefusal("FINITE_SOURCE_MISMATCH", "Configured spec differs from the imported checker")
        resources = {
            "governance/PINS.json": _read(self.context.governance_path("PINS.json")),
            "evidence/v2/manifest.json": _read(self.context.evidence_root / "v2/manifest.json"),
        }
        # HEAD/tree/cleanliness above are independently checked by Git. Bind the
        # actual files consumed by sealed.py too, never only the pin document.
        resources.update(_vendor_sources(vendor))
        # The selected challenge has no Lean obligations. This still binds the
        # report resource used by the existing runner's component inventory.
        try:
            resources["lean/axioms.txt"] = _read(self.context.lean_path("axioms.txt"))
        except ContextRefusal as exc:
            raise EvidenceRefusal(exc.code, str(exc)) from exc
        return FiniteCandidateBinding(
            challenge_id, _digest(candidate_bytes), protected_pairs,
            checker_sha256, _digest(source),
            _manifest({name: _read(payload / name)
                       for name in ("instance.json", "mutation.json", "expect.json")}),
            _manifest(resources),
        )

    def check(
        self, challenge_id: str, candidate_bytes: bytes, binding: FiniteCandidateBinding, *,
        protected_pairs: tuple[tuple[int, int], ...] | None = None,
    ) -> FiniteCandidateCheck:
        """Revalidate bindings, calibrate fixtures, then decide the actual candidate."""
        protected_pairs = self._protected_pairs if protected_pairs is None else protected_pairs
        if type(binding) is not FiniteCandidateBinding or challenge_id != binding.challenge_id:
            raise EvidenceRefusal("CHALLENGE_BINDING_MISMATCH", "The frozen challenge differs")
        if type(candidate_bytes) is not bytes or _digest(candidate_bytes) != binding.candidate_sha256:
            raise EvidenceRefusal("CANDIDATE_BINDING_MISMATCH", "The actual candidate bytes differ")
        if protected_pairs != binding.protected_pairs or protected_pairs != self._protected_pairs:
            raise EvidenceRefusal("PROTECTED_BINDING_MISMATCH", "The host obligation differs")
        current = self.prepare(challenge_id, candidate_bytes, protected_pairs=protected_pairs)
        for binding_field in ("checker_sha256", "source_sha256", "fixture_set_sha256", "resource_sha256"):
            if getattr(current, binding_field) != getattr(binding, binding_field):
                raise EvidenceRefusal(binding_field.removesuffix("_sha256").upper() + "_BINDING_MISMATCH",
                    "The frozen checker or resource bytes differ")
        try:
            configure_context(self.context)
            replay = ResearchLevelEngineRunner(self.context).run(challenge_id)
            if (replay.challenge_id != challenge_id or replay.authority_effect != "None"
                    or replay.evidence_grade != "RESEARCH_FIXTURE_REPLAY"):
                raise EvidenceRefusal("REPLAY_IDENTITY_MISMATCH", "Unexpected runner identity or grade")
            if replay.terminal != "FIXTURE_EXPECTATIONS_MATCHED":
                raise EvidenceRefusal(replay.terminal, "Fixture calibration is unavailable or mismatched")
            from omega_engine_operations.use_cases.level_engine.research_engine.level import (
                Fixture,
                decide_fixture,
                load_spec,
            )
            structure = _candidate_structure(candidate_bytes)
            if any(index >= structure.n() for pair in protected_pairs for index in pair):
                raise EvidenceRefusal("INVALID_FINITE_CANDIDATE", "A protected index is absent")
            verdict = decide_fixture(load_spec(challenge_id),
                Fixture("candidate", "extra", structure, protected_pairs), have=frozenset())
        except ContextRefusal as exc:
            raise EvidenceRefusal(exc.code, str(exc)) from exc
        except (ImportError, OSError) as exc:
            raise EvidenceRefusal("FINITE_COMPONENT_UNAVAILABLE", type(exc).__name__) from exc
        return FiniteCandidateCheck(binding, replay, verdict.satisfied, verdict.code, verdict.failed)

    def judge(self, case: dict, answer: object) -> tuple[bool, str]:
        """Existing PFP judge port; only the finite predicate can be accepted.

        PFP keeps original reply bytes. Its parsed answer is encoded with the
        explicit ASCII/sorted/compact JSON profile for this candidate binding.
        The judge reason retains the research grade and complete binding; PFP's
        TASK_CHECKED label does not promote that grade into a theorem.
        """
        if type(case) is not dict or case.get("challenge_id") != _CHALLENGE:
            raise EvidenceRefusal("CHALLENGE_BINDING_MISMATCH", "Expected the host endpoint challenge")
        pairs = case.get("protected_pairs")
        if type(pairs) is not list or any(type(pair) is not list for pair in pairs):
            raise EvidenceRefusal("INVALID_PROTECTED_PAIRS", "Expected host task index pairs")
        protected = tuple(tuple(pair) for pair in pairs)
        raw = json.dumps(answer, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
            allow_nan=False).encode("ascii")
        binding = self.prepare(_CHALLENGE, raw, protected_pairs=protected)
        checked = self.check(_CHALLENGE, raw, binding, protected_pairs=protected)
        return checked.accepted, json.dumps({
            "scope": "Bounded endpoint/separation predicate; not a theorem or reach certificate",
            "evidence_grade": checked.evidence_grade,
            "candidate_code": checked.candidate_code,
            "binding": asdict(binding),
        }, sort_keys=True)


def _candidate_structure(raw: bytes):
    from omega_engine_operations.use_cases.level_engine.research_engine.canon import loads
    from omega_engine_operations.use_cases.level_engine.research_engine.errors import Refusal
    from omega_engine_operations.use_cases.level_engine.research_engine.structure import from_json

    def require(condition: bool) -> None:
        if not condition:
            raise ValueError("Candidate is outside the bounded relation profile")

    try:
        value = loads(raw)
        require(type(value) is dict and set(value) == {"sorts", "symbols", "tuples", "values"})
        require(type(value["sorts"]) is list and 1 <= len(value["sorts"]) <= 2)
        for pair in value["sorts"]:
            require(type(pair) is list and len(pair) == 2 and type(pair[0]) is str
                    and pair[0] in {"node", "mark"} and type(pair[1]) is int
                    and 0 <= pair[1] <= _MAX_ELEMENTS)
        require(type(value["symbols"]) is list and value["symbols"] == [
            {"name": "arc", "sorts": ["node", "node"]}])
        require(type(value["tuples"]) is list and len(value["tuples"]) <= _MAX_ARCS)
        for pair in value["tuples"]:
            require(type(pair) is list and len(pair) == 2 and pair[0] == "arc"
                    and type(pair[1]) is list and len(pair[1]) == 2
                    and all(type(index) is int for index in pair[1]))
        require(type(value["values"]) is list and value["values"] == [])
        return from_json(value, "candidate")
    except (Refusal, ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise EvidenceRefusal("INVALID_FINITE_CANDIDATE", "Invalid exact relation structure") from exc


# Refuse newly rebound requests after a source edit under cached Python imports.
# This is process-local custody, not a persistent registry or execution framework.
_IMPORTED_CHECKER_SHA256 = _manifest(_checker_sources())
