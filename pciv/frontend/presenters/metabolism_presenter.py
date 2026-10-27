"""Metabolism presenter extracted from metabolism_cli.py. AuthorityEffect: None."""

from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path

from operations.domain.rop.result import Err, Refusal
from pciv.domain.intelligence_metabolism.models import (
    ObstructionEpisodeV1,
)
from pciv.infrastructure.intelligence_metabolism.miner import (
    IntelligenceMiner,
)
from pciv.infrastructure.intelligence_metabolism.native import (
    NativeMetabolismKernel,
)
from pciv.use_cases.intelligence_metabolism.digest import (
    DailyDigestGenerator,
)
from pciv.use_cases.intelligence_metabolism.episode import (
    EpisodeSegmenter,
)
from pciv.use_cases.intelligence_metabolism.motifs import MotifMiner


def resolve_repo_root(path_str: str | None) -> Path:
    if path_str:
        return Path(path_str).resolve()
    curr = Path.cwd().resolve()
    for parent in [curr, *curr.parents]:
        if (parent / ".git").exists() or (parent / "pciv").exists():
            return parent
    return curr


def _report_failures(miner: IntelligenceMiner, failures: list[Refusal] | None = None) -> int:
    for failure in miner.failures:
        print(
            f"{failure.code}: {failure.file_path}@{failure.offset}: {failure.message}",
            file=sys.stderr,
        )
    for failure in failures or []:
        print(f"{failure.code}: {failure.message}", file=sys.stderr)
    return int(bool(miner.failures or failures))


def _segment_records(
    miner: IntelligenceMiner,
) -> tuple[list[ObstructionEpisodeV1], int, list[Refusal]]:
    segmenter = EpisodeSegmenter(NativeMetabolismKernel())
    episodes: list[ObstructionEpisodeV1] = []
    failures: list[Refusal] = []
    records = list(miner.mine_source("symbol_game_runs"))
    for record in records:
        payload = record.payload
        run_id = str(payload.get("run_id") or Path(record.file_path).parent.name)
        steps = payload.get("steps") or payload.get("subturns") or []
        if isinstance(steps, list) and steps:
            result = segmenter.segment_run(run_id, steps)
            if isinstance(result, Err):
                failures.append(result.error)
            else:
                episodes.extend(result.value)
    return episodes, len(records), failures


class MetabolismPresenter:
    @staticmethod
    def cmd_index(args: argparse.Namespace) -> int:
        repo_root = resolve_repo_root(args.repo_root)
        miner = IntelligenceMiner(repo_root)
        source_filter = args.source

        if source_filter:
            if source_filter not in miner.sources:
                print(
                    f"Error: Unknown source '{source_filter}'. Available: {list(miner.sources.keys())}",
                    file=sys.stderr,
                )
                return 1
            records = list(miner.mine_source(source_filter))
        else:
            records = list(miner.mine_all())

        by_source: dict[str, int] = {}
        for r in records:
            by_source[r.source_id] = by_source.get(r.source_id, 0) + 1

        print("Intelligence Metabolism Index Summary (AuthorityEffect: None):")
        print(f"Repo root: {repo_root}")
        print(f"Total records indexed: {len(records)}")
        for s_id, count in sorted(by_source.items()):
            print(f"  - {s_id}: {count}")

        if args.output_json:
            out_path = Path(args.output_json)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            dump_data = [
                {
                    "source_id": r.source_id,
                    "file_path": r.file_path,
                    "file_sha256": r.file_sha256,
                    "offset": r.offset,
                    "record_type": r.record_type,
                    "payload": r.payload,
                    "authority_effect": r.authority_effect,
                }
                for r in records
            ]
            out_path.write_text(json.dumps(dump_data, indent=2), encoding="utf-8")
            print(f"Wrote indexed records to: {out_path}")

        return _report_failures(miner)

    @staticmethod
    def cmd_segment(args: argparse.Namespace) -> int:
        repo_root = resolve_repo_root(args.repo_root)
        miner = IntelligenceMiner(repo_root)

        episodes, run_count, failures = _segment_records(miner)

        print(f"Segmented {len(episodes)} obstruction episodes across {run_count} runs.")
        for ep in episodes[:10]:
            print(
                f"  [{ep.outcome}] run={ep.run_id} word={ep.ddc_word} phi1={ep.phi_1_before}->{ep.phi_1_after}"
            )

        if args.output_json:
            out_path = Path(args.output_json)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            dump_data = [
                {
                    "run_id": ep.run_id,
                    "start_step_hash": ep.start_step_hash,
                    "end_step_hash": ep.end_step_hash,
                    "phi_1_before": str(ep.phi_1_before),
                    "phi_1_after": str(ep.phi_1_after),
                    "gamma_2_before": str(ep.gamma_2_before),
                    "gamma_2_after": str(ep.gamma_2_after),
                    "defect_count_before": ep.defect_count_before,
                    "defect_count_after": ep.defect_count_after,
                    "ddc_word": ep.ddc_word,
                    "outcome": ep.outcome,
                    "authority_effect": ep.authority_effect,
                }
                for ep in episodes
            ]
            out_path.write_text(json.dumps(dump_data, indent=2), encoding="utf-8")
            print(f"Wrote {len(episodes)} episodes to: {out_path}")

        return _report_failures(miner, failures)

    @staticmethod
    def cmd_mine(args: argparse.Namespace) -> int:
        repo_root = resolve_repo_root(args.repo_root)
        miner = IntelligenceMiner(repo_root)

        episodes, _, failures = _segment_records(miner)
        result = MotifMiner(NativeMetabolismKernel()).mine_motifs(episodes, max_n=args.max_n)
        if isinstance(result, Err):
            return _report_failures(miner, [*failures, result.error])
        motifs = result.value

        print(f"Mined {len(motifs)} DDC n-gram motifs (n <= {args.max_n}):")
        for m in motifs[:15]:
            label_str = f" ({m.antimorphism_label})" if m.antimorphism_label else ""
            print(
                f"  motif='{m.motif}' len={m.n_gram_len} succ={m.success_count} stall={m.stall_count}{label_str}"
            )

        if args.output_json:
            out_path = Path(args.output_json)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            dump_data = [
                {
                    "motif": m.motif,
                    "n_gram_len": m.n_gram_len,
                    "success_count": m.success_count,
                    "stall_count": m.stall_count,
                    "antimorphism_label": m.antimorphism_label,
                    "evidence_runs": list(m.evidence_runs),
                    "authority_effect": m.authority_effect,
                }
                for m in motifs
            ]
            out_path.write_text(json.dumps(dump_data, indent=2), encoding="utf-8")
            print(f"Wrote {len(motifs)} motifs to: {out_path}")

        return _report_failures(miner, failures)

    @staticmethod
    def cmd_distill(args: argparse.Namespace) -> int:
        repo_root = resolve_repo_root(args.repo_root)
        miner = IntelligenceMiner(repo_root)

        episodes, _, failures = _segment_records(miner)
        result = MotifMiner(NativeMetabolismKernel()).mine_motifs(episodes, max_n=6)
        if isinstance(result, Err):
            return _report_failures(miner, [*failures, result.error])
        motifs = result.value

        out_dir = Path(
            args.output_dir
            or (repo_root / "_ic/darpa/symbol_game" / "operands" / "candidates")
        )
        out_dir.mkdir(parents=True, exist_ok=True)

        distilled_count = 0
        for m in motifs:
            if m.success_count >= 1:
                label = m.motif.lower()
                if not label or any(
                    not (c.isascii() and (c.isalnum() or c in "_-")) for c in label
                ):
                    label = sha256(m.motif.encode("utf-8")).hexdigest()
                candidate_id = f"op_candidate_{label}"
                cand_data = {
                    "operand_id": candidate_id,
                    "title": f"Learned DDC Motif {m.motif} Candidate",
                    "description": f"Candidate operand synthesized from {m.success_count} successful repair episodes",
                    "source_colour": "Open",
                    "target_colour": "Closed",
                    "ddc_motif": m.motif,
                    "status": "candidate",
                    "evidence": {
                        "success_count": m.success_count,
                        "stall_count": m.stall_count,
                        "evidence_runs": list(m.evidence_runs),
                    },
                    "authority_effect": "None",
                }
                target_file = out_dir / f"{candidate_id}.json"
                target_file.write_text(json.dumps(cand_data, indent=2), encoding="utf-8")
                distilled_count += 1

        print(f"Distilled {distilled_count} candidate operands to {out_dir}")
        return _report_failures(miner, failures)

    @staticmethod
    def cmd_digest(args: argparse.Namespace) -> int:
        repo_root = resolve_repo_root(args.repo_root)
        miner = IntelligenceMiner(repo_root)
        records = list(miner.mine_all())

        out_dir = Path(args.output_dir or (repo_root / "_ic/nara/legacy/metabolism" / "digests"))
        generator = DailyDigestGenerator(records)
        from datetime import datetime, timezone

        date_stamp = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        try:
            datetime.strptime(date_stamp, "%Y-%m-%d")
        except ValueError:
            print("METABOLISM_DATE_INVALID: date must use YYYY-MM-DD", file=sys.stderr)
            return 1
        out_dir.mkdir(parents=True, exist_ok=True)
        digest_path = out_dir / f"{date_stamp}.md"
        digest_path.write_text(
            generator.render_markdown(date_stamp), encoding="utf-8", newline="\n"
        )

        print(f"Generated daily intelligence metabolism digest at: {digest_path}")
        print(
            f"Indexed {len(records)} records across {len(generator.compute_summary_statistics())} statistics keys."
        )
        return _report_failures(miner)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="metabolism_cli",
        description="Intelligence Metabolism CLI: Mining runs, traces, and benchmark receipts (U02).",
    )
    parser.add_argument(
        "--repo-root", type=str, default=None, help="Root directory of the repository"
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_index = subparsers.add_parser(
        "index", help="Index all or specified registered intelligence sources"
    )
    p_index.add_argument("--source", type=str, default=None, help="Filter by source ID")
    p_index.add_argument(
        "--output-json", type=str, default=None, help="Write mined records to JSON file"
    )
    p_index.set_defaults(func=MetabolismPresenter.cmd_index)

    p_segment = subparsers.add_parser("segment", help="Segment runs into obstruction episodes")
    p_segment.add_argument(
        "--output-json", type=str, default=None, help="Write episodes to JSON file"
    )
    p_segment.set_defaults(func=MetabolismPresenter.cmd_segment)

    p_mine = subparsers.add_parser("mine", help="Mine DDC n-gram motifs from obstruction episodes")
    p_mine.add_argument("--max-n", type=int, default=6, help="Maximum n-gram length (default: 6)")
    p_mine.add_argument("--output-json", type=str, default=None, help="Write motifs to JSON file")
    p_mine.set_defaults(func=MetabolismPresenter.cmd_mine)

    p_distill = subparsers.add_parser(
        "distill", help="Distill candidate operand proposals from motifs"
    )
    p_distill.add_argument(
        "--output-dir", type=str, default=None, help="Output directory for candidate operands"
    )
    p_distill.set_defaults(func=MetabolismPresenter.cmd_distill)

    p_digest = subparsers.add_parser("digest", help="Generate daily metabolism digest report")
    p_digest.add_argument(
        "--output-dir", type=str, default=None, help="Output directory for daily digests"
    )
    p_digest.add_argument("--date", type=str, default=None, help="Date stamp (YYYY-MM-DD)")
    p_digest.set_defaults(func=MetabolismPresenter.cmd_digest)

    return parser


def run_metabolism_cli(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
