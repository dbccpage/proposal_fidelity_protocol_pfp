"""The UNS emitter records only what the run produced, where it is told to.

Counterexamples from the study (``domain/bridge/symbol_game_emitter.py`` and
``use_cases/symbol_game_runner.py`` at ``30609de2c``):

* an empty evidence digest was replaced by ``sha256(f"{task_id}:{count}")``,
  a value that binds nothing the run produced;
* a run with no dialogue was given the invented line
  "Woland: The reduction is verified.";
* with no root given, the emitter created ``_intelligence/symbol_game/runs``
  under ``Path(__file__).parents[3]``, the checkout the code lives in;
* the domain opened and wrote files itself.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path

import pytest

import omega_engine_pfp
from omega_engine_pfp.domain.bridge.sbe import SBEAnalyzer
from omega_engine_pfp.domain.bridge.symbol_game_emitter import (
    UnifiedNarrativeScriptEmitter,
)
from omega_engine_pfp.domain.bridge.symbol_game_models import SymbolGameStepResult
from omega_engine_pfp.domain.bridge.symbol_game_packets import SymbolGamePacketCompiler
from omega_engine_pfp.domain.models import ObstructionScore

PACKAGE = Path(omega_engine_pfp.__file__).resolve().parent
DIGEST = "ab" * 32


class MemorySink:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def put_text(self, relative_path: str, text: str) -> str:
        self.files[relative_path] = text
        return f"memory://{relative_path}"

    def append_lines(self, relative_path, lines) -> str:
        self.files[relative_path] = self.files.get(relative_path, "") + "".join(
            line + "\n" for line in lines
        )
        return f"memory://{relative_path}"

    def read_lines(self, relative_path: str) -> tuple[str, ...]:
        return tuple(self.files.get(relative_path, "").splitlines())


class NoAntibodies:
    def farm_antibodies_from_defects(self, defects, *, run_id, task_id):
        return []


class RecordingSBE(SBEAnalyzer):
    def __init__(self) -> None:
        super().__init__()
        self.ensembles: list[list[str]] = []

    def analyze_dialogue_ensemble(self, dialogue_beats, weights=None):
        self.ensembles.append(list(dialogue_beats))
        return super().analyze_dialogue_ensemble(dialogue_beats, weights)


def _silent_run() -> tuple[object, list[SymbolGameStepResult]]:
    packet = SymbolGamePacketCompiler.compile_problem_packet(
        task_id="custody", problem_data={"title": "custody", "prompt": "p"}
    )
    score = ObstructionScore(gamma_2=Fraction(0), phi_1=Fraction(0), active_count=0)
    step = SymbolGameStepResult(
        step_index=1,
        packet=packet,
        candidate_proposal={"step": 0},
        obstruction_score=score,
        prior_score=None,
        strict_descent_passed=True,
        scene_beats=(),
        status="PASS_TO_MASTER",
        action_taken="EXACT_REPAIR",
    )
    return packet, [step]


def _emitter(sink: MemorySink, sbe: SBEAnalyzer | None = None) -> UnifiedNarrativeScriptEmitter:
    kwargs = {"artifact_sink": sink, "pharmacy_seeder": NoAntibodies()}
    if sbe is not None:
        kwargs["sbe_analyzer"] = sbe
    return UnifiedNarrativeScriptEmitter(**kwargs)


def test_no_default_root_and_no_write_at_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse_mkdir(self, *args, **kwargs):
        raise AssertionError(f"construction must not create {self}")

    monkeypatch.setattr(Path, "mkdir", refuse_mkdir)
    with pytest.raises(TypeError):
        UnifiedNarrativeScriptEmitter()


@pytest.mark.parametrize("evidence", ["", "0" * 63, "AB" * 32, None, 7])
def test_emission_refuses_a_missing_or_malformed_evidence_digest(evidence) -> None:
    sink = MemorySink()
    packet, steps = _silent_run()
    with pytest.raises(ValueError, match="EVIDENCE_DIGEST_REQUIRED"):
        _emitter(sink).emit_full_trace("custody", steps, packet, evidence_sha256=evidence)
    assert sink.files == {}


def test_silent_run_keeps_its_silence_and_its_digest() -> None:
    sink = MemorySink()
    sbe = RecordingSBE()
    packet, steps = _silent_run()
    uns, packets = _emitter(sink, sbe).emit_full_trace(
        "custody", steps, packet, evidence_sha256=DIGEST
    )
    assert sbe.ensembles and all(ensemble == [] for ensemble in sbe.ensembles)
    everything = "\n".join(sink.files.values())
    assert "Woland: The reduction is verified." not in everything
    assert "Koroviev" not in everything
    assert DIGEST in sink.files["_ic/odni/unified_oe_trace.jsonl"]
    assert uns.startswith("memory://_ic/darpa/symbol_game/runs/")
    assert packets.startswith("memory://_ic/darpa/symbol_game/runs/")
    assert "_ic/nara/legacy/unified_oe_packets.jsonl" in sink.files


def test_bridge_domain_modules_do_no_file_io() -> None:
    forbidden_calls = {"open", "mkdir", "write_text", "write_bytes", "read_text", "read_bytes"}
    for name in ("symbol_game_emitter.py", "symbol_game_packet_ledger.py", "unified_oe_trace.py"):
        tree = ast.parse((PACKAGE / "domain" / "bridge" / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = (
                    [node.module]
                    if isinstance(node, ast.ImportFrom)
                    else [a.name for a in node.names]
                )
                assert "pathlib" not in modules, f"{name} imports pathlib"
            if isinstance(node, ast.Call):
                func = node.func
                called = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                assert called not in forbidden_calls, f"{name} calls {called}()"
            if isinstance(node, ast.Attribute) and node.attr == "parents":
                raise AssertionError(f"{name} derives a root from Path(__file__).parents")


def test_runner_evidence_is_not_built_from_the_task_id_and_a_count() -> None:
    """``run_problem`` refuses before it reaches emission, so this guard reads the source."""
    source = (PACKAGE / "use_cases" / "symbol_game_runner.py").read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.JoinedStr):
            continue
        names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        assert not {"effective_task_id", "len", "step_results"} <= names, (
            "an evidence digest is built from the task id and a step count"
        )


def test_filesystem_sink_requires_an_explicit_root_and_stays_inside_it(tmp_path: Path) -> None:
    from omega_engine_pfp.infrastructure.persistence.run_artifact_sink import (
        FilesystemRunArtifactSink,
        OutputRootRequired,
    )

    for missing in (None, "", "   "):
        with pytest.raises(OutputRootRequired):
            FilesystemRunArtifactSink(missing)
    sink = FilesystemRunArtifactSink(tmp_path)
    for escape in ("../outside.txt", "/abs.txt", "a/../../b", r"a\b", "", "a//b", "a\x00b", "C:/x"):
        with pytest.raises(ValueError):
            sink.put_text(escape, "x")
    locator = sink.put_text("_ic/darpa/symbol_game/runs/r/uns.md", "line\n")
    assert Path(locator) == tmp_path / "_ic/darpa/symbol_game/runs/r/uns.md"
    sink.append_lines("_ic/odni/ledger.jsonl", ["{}", "{}"])
    assert sink.read_lines("_ic/odni/ledger.jsonl") == ("{}", "{}")
    assert (tmp_path / "_ic/odni/ledger.jsonl").read_bytes() == b"{}\n{}\n"


@pytest.mark.parametrize("operation", ["put", "append"])
def test_filesystem_sink_refuses_legacy_active_writes(tmp_path: Path, operation: str) -> None:
    from omega_engine_pfp.infrastructure.persistence.run_artifact_sink import (
        FilesystemRunArtifactSink,
    )

    sink = FilesystemRunArtifactSink(tmp_path)
    with pytest.raises(ValueError, match="LEGACY_INTELLIGENCE_WRITE_REFUSED"):
        if operation == "put":
            sink.put_text("_intelligence/old.txt", "not current")
        else:
            sink.append_lines("_intelligence/old.jsonl", ["{}"])
    assert not list(tmp_path.iterdir())


def test_filesystem_sink_can_read_retained_legacy_bytes_without_rewriting(tmp_path: Path) -> None:
    from omega_engine_pfp.infrastructure.persistence.run_artifact_sink import (
        FilesystemRunArtifactSink,
    )

    source = tmp_path / "_intelligence/retained.jsonl"
    source.parent.mkdir(parents=True)
    raw = b'{"historical":true}\n'
    source.write_bytes(raw)
    assert FilesystemRunArtifactSink(tmp_path).read_lines("_intelligence/retained.jsonl") == (
        '{"historical":true}',
    )
    assert source.read_bytes() == raw


@pytest.mark.parametrize("operation", ["put", "append"])
def test_filesystem_sink_checks_activation_each_write_then_recovers(
    tmp_path: Path,
    operation: str,
) -> None:
    from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import (
        IcMigrationRefusal,
    )
    from omega_engine_pfp.infrastructure.persistence.run_artifact_sink import (
        FilesystemRunArtifactSink,
    )

    sink = FilesystemRunArtifactSink(tmp_path)
    locator = "_ic/odni/trace.jsonl"
    target = tmp_path / locator
    target.parent.mkdir(parents=True)
    target.write_bytes(b"retained\n")
    marker = tmp_path / "_ic/odni/migration/activation.json"
    marker.parent.mkdir(parents=True)
    marker.write_bytes(b"{}")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    with pytest.raises(IcMigrationRefusal, match="ACTIVATION_INVALID"):
        if operation == "put":
            sink.put_text(locator, "recovered\n")
        else:
            sink.append_lines(locator, ["recovered"])
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
    # An explicit ordinary export is independent of IC migration metadata.
    sink.put_text("exports/report.txt", "ordinary export")
    assert (tmp_path / "exports/report.txt").read_bytes() == b"ordinary export"
    marker.unlink()
    if operation == "put":
        sink.put_text(locator, "recovered\n")
        assert target.read_bytes() == b"recovered\n"
    else:
        sink.append_lines(locator, ["recovered"])
        assert target.read_bytes() == b"retained\nrecovered\n"
    assert not (tmp_path / "_intelligence").exists()


@pytest.mark.parametrize("operation", ["put", "append"])
def test_filesystem_sink_refuses_ic_hardlink_write_then_recovers(
    tmp_path: Path,
    operation: str,
) -> None:
    from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import (
        IcMigrationRefusal,
    )
    from omega_engine_pfp.infrastructure.persistence.run_artifact_sink import (
        FilesystemRunArtifactSink,
    )

    root = tmp_path / "store"
    sink = FilesystemRunArtifactSink(root)
    locator = "_ic/odni/trace.jsonl"
    target = root / locator
    retained = b"retained\n"
    recovered = b"recovered\n" if operation == "put" else retained + b"recovered\n"

    def write() -> None:
        if operation == "put":
            sink.put_text(locator, "recovered\n")
        else:
            sink.append_lines(locator, ["recovered"])

    # The same public method successfully writes an ordinary single-linked IC file.
    sink.put_text(locator, retained.decode())
    write()
    assert target.read_bytes() == recovered
    target.write_bytes(retained)
    sentinel = tmp_path / "outside.txt"
    sentinel.write_bytes(retained)
    target.unlink()
    target.hardlink_to(sentinel)
    assert target.samefile(sentinel)
    assert target.stat().st_nlink == 2
    assert sink.read_lines(locator) == ("retained",)

    with pytest.raises(IcMigrationRefusal, match="HARDLINK_WRITE_REFUSED"):
        write()
    assert target.read_bytes() == sentinel.read_bytes() == retained
    assert target.samefile(sentinel)

    # Restore the exact retained IC bytes to a distinct file, then recover the write.
    target.unlink()
    target.write_bytes(retained)
    assert target.stat().st_nlink == sentinel.stat().st_nlink == 1
    assert not target.samefile(sentinel)
    assert target.read_bytes() == retained
    write()
    assert target.read_bytes() == recovered
    assert sentinel.read_bytes() == retained


@pytest.mark.parametrize("operation", ["put", "append"])
def test_filesystem_sink_explicit_exports_preserve_existing_hardlink_policy(
    tmp_path: Path,
    operation: str,
) -> None:
    from omega_engine_pfp.infrastructure.persistence.run_artifact_sink import (
        FilesystemRunArtifactSink,
    )

    root = tmp_path / "store"
    target = root / "exports/report.txt"
    target.parent.mkdir(parents=True)
    sentinel = tmp_path / "explicit-export.txt"
    sentinel.write_bytes(b"old\n")
    target.hardlink_to(sentinel)
    sink = FilesystemRunArtifactSink(root)
    if operation == "put":
        sink.put_text("exports/report.txt", "new\n")
        expected = b"new\n"
    else:
        sink.append_lines("exports/report.txt", ["new"])
        expected = b"old\nnew\n"
    assert target.samefile(sentinel)
    assert target.read_bytes() == sentinel.read_bytes() == expected


@pytest.mark.parametrize("operation", ["put", "append"])
@pytest.mark.parametrize(
    "relative",
    [
        "_IC/odni/trace.jsonl",
        "_Ic/odni/trace.jsonl",
        "_INTELLIGENCE/new.txt",
        "_Intelligence/new.txt",
        "_ic./odni/trace.jsonl",
        "_ic /odni/trace.jsonl",
        ".. /outside.txt",
        "exports/report.txt.",
        "exports/report.txt ",
    ],
)
def test_filesystem_sink_refuses_windows_path_aliases_before_writes_and_recovers(
    tmp_path: Path,
    operation: str,
    relative: str,
) -> None:
    from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import (
        IcMigrationRefusal,
    )
    from omega_engine_pfp.infrastructure.persistence.run_artifact_sink import (
        FilesystemRunArtifactSink,
    )

    root = tmp_path / "store"
    sink = FilesystemRunArtifactSink(root)
    canonical = "_ic/odni/trace.jsonl"
    target = root / canonical
    target.parent.mkdir(parents=True)
    retained = b"retained\n"
    sentinel = tmp_path / "outside.txt"
    sentinel.write_bytes(retained)
    target.hardlink_to(sentinel)
    marker = root / "_ic/odni/migration/activation.json"
    marker.parent.mkdir(parents=True)
    marker.write_bytes(b"{}")

    def snapshot():
        return {
            path.relative_to(tmp_path): ("file", path.read_bytes())
            if path.is_file()
            else ("dir", None)
            for path in tmp_path.rglob("*")
        }

    before = snapshot()
    with pytest.raises(IcMigrationRefusal, match="UNSAFE_PATH"):
        if operation == "put":
            sink.put_text(relative, "changed\n")
        else:
            sink.append_lines(relative, ["changed"])
    assert snapshot() == before
    assert target.samefile(sentinel)
    assert sentinel.read_bytes() == retained

    # Exact-byte recovery uses a canonical, distinct file and corrected activation.
    marker.unlink()
    target.unlink()
    target.write_bytes(retained)
    assert not target.samefile(sentinel)
    if operation == "put":
        sink.put_text(canonical, "recovered\n")
        assert target.read_bytes() == b"recovered\n"
    else:
        sink.append_lines(canonical, ["recovered"])
        assert target.read_bytes() == retained + b"recovered\n"
    assert sentinel.read_bytes() == retained
