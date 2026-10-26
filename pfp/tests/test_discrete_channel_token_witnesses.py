"""Discrete witnesses and the source inventory of tolerance syntax.

A discrete token witness is a sealed guard token or dispatch on the event
class. The inventory observes ``tol`` / ``channel_tol`` syntax and float
fields; a match does not establish that the containing operation admits a
channel. Some current operations explicitly refuse approximate admission.

The ledger pins the source paths and code this scanner reads. Line numbers
remain diagnostics, so inserting comments does not change site identity.
Adding or deleting a scanned site without editing the ledger fails this file.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from omega_engine_pfp.domain.events.events import TurnExecutedEvent
from omega_engine_pfp.domain.exceptions import CanonicalizationError
from omega_engine_pfp.domain.packet_codec import PacketCodec
from omega_engine_pfp.infrastructure.events.event_bus import InMemoryEventBus

_TOL_PARAM = re.compile(r"\btol\s*:\s*f(?:64|32)\b")
_TOL_COMPARE = re.compile(r"(?:>=|<=|>|<)\s*tol\b|\btol\s*(?:>=|<=|>|<)")
_CHANNEL_TOL_SITE = re.compile(r"\bchannel_tol\s*:\s*f(?:64|32)\b|config\.channel_tol\b")
_CONTINUOUS_EVENT_FIELDS = frozenset({"purity", "l1_obstruction", "efficiency"})


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root not found")


def _rust_code_lines(text: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    in_block = False
    for number, line in enumerate(text.splitlines(), start=1):
        if in_block:
            if "*/" not in line:
                continue
            in_block = False
            line = line.split("*/", 1)[1]
        while "/*" in line:
            before, _, after = line.partition("/*")
            if "*/" not in after:
                in_block = True
                line = before
                break
            line = before + after.split("*/", 1)[1]
        code = line.split("//", 1)[0]
        if code.strip():
            rows.append((number, code))
    return rows


def _annotation_names_float(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "float"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _annotation_names_float(node.left) or _annotation_names_float(node.right)
    return False


def _float_threshold_sites() -> list[str]:
    root = _repo_root()
    found: list[str] = []
    tolerance_files = (
        "omega_engine/crates_rs/omega_quantum_physics/src/quantum_channel.rs",
        "omega_engine/crates_rs/omega_quantum_physics/src/kraus_operators.rs",
    )
    for relative in tolerance_files:
        for number, code in _rust_code_lines((root / relative).read_text(encoding="utf-8")):
            if _TOL_PARAM.search(code) or _TOL_COMPARE.search(code):
                found.append(f"{relative}:{number}: {code.strip()}")

    density = "omega_engine/crates_rs/omega_linear_algebra/src/linear_algebra/density.rs"
    for number, code in _rust_code_lines((root / density).read_text(encoding="utf-8")):
        if _CHANNEL_TOL_SITE.search(code):
            found.append(f"{density}:{number}: {code.strip()}")

    woland = root / "omega_engine_woland/stage/domain/quantum/density_matrix.py"
    tree = ast.parse(woland.read_text(encoding="utf-8"), filename=str(woland))
    for node in ast.walk(tree):
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        if node.target.id == "channel_tol" and _annotation_names_float(node.annotation):
            found.append(
                "omega_engine_woland/stage/domain/quantum/density_matrix.py:"
                f"{node.lineno}: channel_tol annotated float"
            )

    events = root / "omega_engine_pfp/domain/events/events.py"
    event_tree = ast.parse(events.read_text(encoding="utf-8"), filename=str(events))
    for node in ast.walk(event_tree):
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        if (
            node.target.id in _CONTINUOUS_EVENT_FIELDS
            and _annotation_names_float(node.annotation)
        ):
            found.append(
                "omega_engine_pfp/domain/events/events.py:"
                f"{node.lineno}: {node.target.id} annotated float"
            )
    return found


def test_packet_codec_refuses_a_float_payload() -> None:
    with pytest.raises(CanonicalizationError, match="float values are forbidden"):
        PacketCodec.seal({"score": 0.5}, "turn")


def test_event_bus_dispatches_on_the_event_class() -> None:
    bus = InMemoryEventBus()
    seen: list[str] = []
    bus.subscribe(TurnExecutedEvent, lambda event: seen.append(type(event).__name__))
    bus.publish(TurnExecutedEvent(task_id="t", verdict="EXACT"))
    assert seen == ["TurnExecutedEvent"]


def test_discrete_token_witnesses_remain_on_authority_and_event_dispatch() -> None:
    root = _repo_root()
    authority = (root / "omega_engine/crates_rs/omega_types/src/authority.rs").read_text(
        encoding="utf-8"
    )
    bus = (
        root / "omega_engine_pfp/infrastructure/events/event_bus.py"
    ).read_text(encoding="utf-8")
    assert "pub struct IsAuth" in authority
    assert "fn decide(" in authority
    assert "type(event)" in bus
    assert '#[serde(try_from = "RawIsAuth")]' in authority


def test_exact_channel_admission_does_not_compare_an_f64_tolerance() -> None:
    root = _repo_root()
    relative = "omega_engine/crates_rs/omega_quantum_physics/src/exact_channel.rs"
    text = (root / relative).read_text(encoding="utf-8")
    code = "\n".join(line for _, line in _rust_code_lines(text))
    assert "tol: f64" not in code
    assert "channel_tol" not in code
    assert "NotTracePreserving" in text


_FLOAT_THRESHOLD_SYNTAX_SITES = (
    "omega_engine/crates_rs/omega_quantum_physics/src/quantum_channel.rs:92: tol: f64,",
    "omega_engine/crates_rs/omega_quantum_physics/src/quantum_channel.rs:94: "
    "if !tol.is_finite() || tol < 0.0 {",
    "omega_engine/crates_rs/omega_quantum_physics/src/quantum_channel.rs:99: "
    "if !residual.is_finite() || residual > tol {",
    "omega_engine/crates_rs/omega_quantum_physics/src/quantum_channel.rs:224: "
    "pub fn validate(&self, tol: f64) -> Result<(), ChannelError> {",
    "omega_engine/crates_rs/omega_quantum_physics/src/quantum_channel.rs:225: "
    "if !tol.is_finite() || tol < 0.0 {",
    "omega_engine/crates_rs/omega_quantum_physics/src/quantum_channel.rs:229: "
    "if !residual.is_finite() || residual > tol {",
    "omega_engine/crates_rs/omega_quantum_physics/src/kraus_operators.rs:205: "
    "pub fn is_trace_preserving(&self, tol: f64) -> bool {",
    "omega_engine/crates_rs/omega_quantum_physics/src/kraus_operators.rs:206: "
    "tol.is_finite() && tol >= 0.0 && self.completeness_residual() == 0.0",
    "omega_engine/crates_rs/omega_linear_algebra/src/linear_algebra/density.rs:18: "
    "channel_tol: f64,",
    "omega_engine/crates_rs/omega_linear_algebra/src/linear_algebra/density.rs:45: "
    "channel_tol: f64,",
    "omega_engine_woland/stage/domain/quantum/density_matrix.py:28: channel_tol annotated float",
    "omega_engine_pfp/domain/events/events.py:37: purity annotated float",
    "omega_engine_pfp/domain/events/events.py:38: l1_obstruction annotated float",
    "omega_engine_pfp/domain/events/events.py:55: efficiency annotated float",
)


def test_float_threshold_source_inventory_stays_pinned() -> None:
    sites = tuple(_float_threshold_sites())
    assert tuple(map(_site_identity, sites)) == tuple(
        map(_site_identity, _FLOAT_THRESHOLD_SYNTAX_SITES)
    )


def _site_identity(site: str) -> tuple[str, str]:
    path, number, code = site.split(":", 2)
    assert number.isdecimal()
    return path, code.lstrip()


def test_float_inventory_tolerates_comments_but_detects_added_admission(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = _repo_root()
    baseline = tuple(map(_site_identity, _float_threshold_sites()))
    for relative in {path for path, _ in baseline}:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        comment = "// relocated line\n" if target.suffix == ".rs" else "# relocated line\n"
        target.write_text(comment + (root / relative).read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setitem(globals(), "_repo_root", lambda: tmp_path)
    assert tuple(map(_site_identity, _float_threshold_sites())) == baseline
    channel = tmp_path / "omega_engine/crates_rs/omega_quantum_physics/src/quantum_channel.rs"
    with channel.open("a", encoding="utf-8") as stream:
        stream.write("\nfn added_admission(tol: f64) -> bool {\n    1.0 < tol\n}\n")
    changed = tuple(map(_site_identity, _float_threshold_sites()))
    assert changed != baseline
    assert any("added_admission" in code for _, code in changed)
