"""Native parity and read-only partial-failure acceptance checks."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal
from omega_engine_prompt_civilization.frontend.cli.metabolism_cli import main
from omega_engine_prompt_civilization.infrastructure.intelligence_metabolism import (
    DataSourceAdapter,
    IntelligenceMiner,
    NativeMetabolismKernel,
)
from omega_engine_prompt_civilization.use_cases.intelligence_metabolism import (
    EpisodeSegmenter,
    MotifMiner,
)


def test_native_episode_and_motif_results_match_frozen_source_vectors():
    fixture = (
        Path(__file__).resolve().parents[3]
        / "omega_engine/crates_rs/tests/omega_prompt_civilization/fixtures/metabolism.json"
    )
    kernel = NativeMetabolismKernel()
    for vector in json.loads(fixture.read_text(encoding="utf-8")):
        result = kernel.execute(vector["payload"])
        assert isinstance(result, Ok), result
        assert result.value == vector["expected"]


def test_miner_keeps_healthy_records_and_actual_crlf_utf8_offsets(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    healthy_first = b'{"letter":"D","note":"\xce\xbb"}\r\n'
    broken = b"{torn\r\n"
    invalid_utf8 = b'{"letter":"M","note":"\xff"}\r\n'
    healthy_last = b'{"kind":"terminal"}\r\n'
    raw = healthy_first + broken + invalid_utf8 + healthy_last
    path = source / "trace.jsonl"
    path.write_bytes(raw)
    miner = IntelligenceMiner(
        tmp_path, {"test": DataSourceAdapter("test", "source", "*.jsonl", "jsonl", "test")}
    )
    records = list(miner.mine_all())
    assert [record.offset for record in records] == [0, len(healthy_first + broken + invalid_utf8)]
    assert [failure.offset for failure in miner.failures] == [
        len(healthy_first),
        len(healthy_first + broken),
    ]
    assert {failure.code for failure in miner.failures} == {"METABOLISM_RECORD_UNREADABLE"}
    assert {record.file_sha256 for record in records} == {hashlib.sha256(raw).hexdigest()}
    assert {failure.file_sha256 for failure in miner.failures} == {hashlib.sha256(raw).hexdigest()}
    assert path.read_bytes() == raw


def test_use_cases_preserve_typed_native_refusal():
    failure = Refusal("METABOLISM_INPUT_INVALID", "malformed input")

    class RefusingKernel:
        def execute(self, payload):
            return Err(failure)

    assert EpisodeSegmenter(RefusingKernel()).segment_run("test", []) == Err(failure)
    assert MotifMiner(RefusingKernel()).mine_motifs([]) == Err(failure)


def test_fraction_zero_preserves_source_string_zero_distinction():
    result = EpisodeSegmenter(NativeMetabolismKernel()).segment_run(
        "fraction", [{"phi_1": Fraction(0), "op": "D", "defect_count": 10**30}]
    )
    assert isinstance(result, Ok)
    episode = result.value[0]
    assert episode.phi_1_before == Fraction(0)
    assert episode.defect_count_before == 10**30
    assert episode.outcome == "Abandoned"


def test_large_episode_request_uses_bound_artifact_transport():
    run_id = "λ" * 40_000
    result = EpisodeSegmenter(NativeMetabolismKernel()).segment_run(
        run_id, [{"phi_1": "1", "op": "D"}, {"phi_1": "0", "op": "E"}]
    )
    assert isinstance(result, Ok), result
    assert result.value[0].run_id == run_id
    assert result.value[0].ddc_word == "DE"


def test_cli_reports_partial_mining_failure_and_keeps_healthy_output(tmp_path: Path, capsys):
    source = tmp_path / "_ic/nara/legacy/bench/results"
    source.mkdir(parents=True)
    (source / "good.json").write_text('{"schema":"benchmark"}', encoding="utf-8")
    (source / "broken.json").write_text("{torn", encoding="utf-8")
    output = tmp_path / "indexed.json"
    status = main(
        [
            "--repo-root",
            str(tmp_path),
            "index",
            "--source",
            "bench_results",
            "--output-json",
            str(output),
        ]
    )
    assert status == 1
    assert "METABOLISM_RECORD_UNREADABLE" in capsys.readouterr().err
    assert len(json.loads(output.read_text(encoding="utf-8"))) == 1
