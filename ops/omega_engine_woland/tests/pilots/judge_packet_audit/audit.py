"""Orchestrates the judge-packet audit over a repository checkout.

For each challenge package the audit writes one canonical JSON record
(``packages/<ID>.json``) and one file of raw per-call outcomes
(``outcomes/<ID>.jsonl``); ``summary.json`` aggregates them. Run metadata
that varies between runs (timings, tool versions, the audited tree's git
state) goes to ``run_info.json`` so that the other files are byte-stable for
a given checkout.

This is a measurement harness for judge packets. It evaluates no model
output and calls no provider.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from omega_engine_woland.tests.pilots.judge_packet_audit import canonical
from omega_engine_woland.tests.pilots.judge_packet_audit import custody
from omega_engine_woland.tests.pilots.judge_packet_audit import execution
from omega_engine_woland.tests.pilots.judge_packet_audit import layout
from omega_engine_woland.tests.pilots.judge_packet_audit import leakage
from omega_engine_woland.tests.pilots.judge_packet_audit import mutation_inventory
from omega_engine_woland.tests.pilots.judge_packet_audit import responders
from omega_engine_woland.tests.pilots.judge_packet_audit import semantic
from omega_engine_woland.tests.pilots.judge_packet_audit import special_checks
from omega_engine_woland.tests.pilots.judge_packet_audit import summaries
from omega_engine_woland.tests.pilots.judge_packet_audit import worker
from omega_engine_woland.tests.pilots.judge_packet_audit import static_analysis as sa

HARNESS_VERSION = "1.0.0"
MESSAGE_LIMIT = 160
OUTCOME_CODES = {
    "ACCEPT": "A",
    "REJECT": "R",
    "EXCEPTION": "E",
    "TIMEOUT": "T",
    "UNINTERPRETABLE": "U",
    "HARD_TIMEOUT": "W",
    "WORKER_CRASH": "W",
    "MISSING": "M",
    "NOT_RUN": "M",
}


def _load_example(base: Path, record: dict[str, Any]) -> tuple[Any, Any]:
    data = json.loads((base / record["path"]).read_text(encoding="utf-8"))

    def pick(key: str | None) -> Any:
        if key is None:
            return None
        return data if key == layout.SELF else data.get(key)

    return pick(record["input_key"]), pick(record["output_key"])


def _job_base(
    repo_root: Path, pkg_dir: Path, desc: dict[str, Any], options: argparse.Namespace
) -> dict[str, Any]:
    # Both roots are on the path, as the packages' own scoring scripts arrange:
    # absolute imports resolve through the repository root and top-level
    # ``judge_packet`` / ``reference_solver`` imports through the package root.
    roots = [str(repo_root), str(pkg_dir)]
    sys_path = roots if desc["import_style"] == "absolute" else roots[::-1]
    return {
        "repo_root": str(repo_root),
        "package_dir": str(pkg_dir),
        "sys_path": sys_path,
        "import_prefix": desc["import_prefix"],
        "checkers": desc["checkers"],
        "gate": desc["gate"],
        "solver": desc["solver"],
        "cases": [{"path": c["path"], "index": c["index"]} for c in desc["cases"]],
        "unwrap_input": desc["unwrap_input"],
        "call_timeout_s": options.call_timeout,
        "solver_timeout_s": options.solver_timeout,
    }


def _vocab_files(pkg_dir: Path, rel_dotted: str, desc: dict[str, Any]) -> list[Path]:
    modules = [c["module"] for c in desc["checkers"]]
    if desc["gate"].get("module"):
        modules.append(desc["gate"]["module"])
    closure = sa.internal_closure(modules, pkg_dir, rel_dotted, ("reference_solver",))
    names = set(closure)
    for records in closure.values():
        for record in records:
            target, _ = sa.imported_target(record, pkg_dir)
            if target == "reference_solver" or target.startswith("reference_solver."):
                names.add(target)
    return [p for p in (sa.module_file(pkg_dir, n) for n in sorted(names)) if p is not None]


def _dependence(pkg_dir: Path, rel_dotted: str, desc: dict[str, Any]) -> dict[str, Any]:
    checker_modules = [c["module"] for c in desc["checkers"]]
    per_checker = {}
    texts = {}
    for spec in desc["checkers"]:
        others = [m for m in checker_modules if m != spec["module"]]
        per_checker[spec["role"]] = sa.checker_dependence(
            pkg_dir, rel_dotted, spec["module"], others
        )
        path = sa.module_file(pkg_dir, spec["module"])
        texts[spec["role"]] = path.read_text(encoding="utf-8") if path else ""
    ref_dir = pkg_dir / "reference_solver"
    ref_text = ""
    if ref_dir.is_dir():
        ref_text = "\n".join(
            p.read_text(encoding="utf-8")
            for p in sorted(ref_dir.rglob("*.py"))
            if "__pycache__" not in p.parts
        )
    similarity: dict[str, Any] = {}
    roles = [c["role"] for c in desc["checkers"]]
    for i, a in enumerate(roles):
        for b in roles[i + 1 :]:
            shared_ab, total_a = sa.shared_line_fraction(texts[a], texts[b])
            shared_ba, total_b = sa.shared_line_fraction(texts[b], texts[a])
            similarity[f"{a}~{b}"] = {
                "a_lines_in_b": canonical.ratio(shared_ab, total_a),
                "b_lines_in_a": canonical.ratio(shared_ba, total_b),
                "a_nontrivial_lines": total_a,
                "b_nontrivial_lines": total_b,
            }
        shared, total = sa.shared_line_fraction(texts[a], ref_text)
        similarity[f"{a}~reference_solver"] = {
            "a_lines_in_b": canonical.ratio(shared, total),
            "a_nontrivial_lines": total,
        }
    return {
        "per_checker": per_checker,
        "similarity": similarity,
        "checkers_share_one_module": len(set(checker_modules)) < len(checker_modules),
    }


def _row_calls(calls: dict[str, Any] | None) -> dict[str, Any]:
    if not calls:
        return {}
    return {
        role: [rec.get("outcome"), (rec.get("message") or "")[:MESSAGE_LIMIT]]
        for role, rec in calls.items()
    }


def _examples(
    pkg_dir: Path, desc: dict[str, Any]
) -> tuple[list[tuple[str, Any, bool]], list[tuple[str, Any]]]:
    """Example inputs with a flag for whether an answer ships with them, and example outputs.

    An answer ships when the example file holds one, when a sibling
    ``<name>_expected.json`` exists, or when the theme's ``answers.jsonl``
    holds a line with the example's identifier.
    """
    examples: list[tuple[str, Any, bool]] = []
    outputs: list[tuple[str, Any]] = []
    theme_answer_ids = _answer_ids(pkg_dir.parent / "answers.jsonl")
    for ex in desc["examples"]:
        ex_input, ex_output = _load_example(pkg_dir, ex)
        if ex_input is not None:
            ships = ex_output is not None or ex.get("answer_file") is not None
            examples.append((ex["path"], ex_input, ships))
        if ex_output is not None:
            outputs.append((ex["path"], ex_output))
    for ex in desc["theme_examples"]:
        ex_input, ex_output = _load_example(pkg_dir.parent, ex)
        if ex_input is not None:
            ident = (
                ex_input.get("id") or ex_input.get("case_id")
                if isinstance(ex_input, dict)
                else None
            )
            ships = (
                ex_output is not None
                or ex.get("answer_file") is not None
                or ident in theme_answer_ids
            )
            examples.append((f"../{ex['path']}", ex_input, ships))
    return examples, outputs


def _answer_ids(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if isinstance(row, dict):
                ident = row.get("id") or row.get("case_id")
                if isinstance(ident, str):
                    ids.add(ident)
    return ids


SHARD_KEYS = {"reference": "cases", "responders": "items", "mutations": "mutations"}


def _run(
    job: dict[str, Any], n_items: int, pkg_dir: Path, options: argparse.Namespace
) -> execution.JobResult:
    """Runs a job, split into contiguous shards run in parallel when it is large.

    Items are independent, so sharding changes only wall time: each shard's
    record indices are shifted back to the job's item numbering.
    """
    work = Path(options.work_dir)
    shards = max(1, int(getattr(options, "shards", 1)))

    def launch(part: dict[str, Any], count: int) -> execution.JobResult:
        return execution.run_job(
            part,
            count,
            cwd=pkg_dir,
            intelligence_root=work / "intelligence_root",
            scratch_dir=work / "jobs",
            wall_timeout_s=options.wall_timeout,
        )

    key = SHARD_KEYS.get(job["mode"])
    if key is None or shards == 1 or n_items < 2 * shards:
        return launch(job, n_items)
    size = -(-n_items // shards)
    bounds = [(lo, min(lo + size, n_items)) for lo in range(0, n_items, size)]
    with ThreadPoolExecutor(max_workers=len(bounds)) as pool:
        parts = list(
            pool.map(
                lambda b: launch(dict(job, **{key: job[key][b[0] : b[1]]}), b[1] - b[0]), bounds
            )
        )
    merged = execution.JobResult()
    for (lo, _hi), part in zip(bounds, parts):
        merged.launches += part.launches
        if part.import_error and merged.import_error is None:
            merged.import_error = part.import_error
        for index, rec in part.records.items():
            merged.records[lo + index] = dict(rec, i=lo + index)
        for crash in part.crashes:
            merged.crashes.append(dict(crash, item=lo + crash["item"]))
    return merged


def audit_package(
    repo_root: Path, pkg_dir: Path, options: argparse.Namespace
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    desc = layout.build_descriptor(repo_root, pkg_dir)
    rel_dotted = ".".join(pkg_dir.relative_to(layout.challenges_root(repo_root)).parts)
    record: dict[str, Any] = {
        "package_id": desc["package_id"],
        "descriptor": desc,
        "harness_version": HARNESS_VERSION,
    }
    vocab_files = _vocab_files(pkg_dir, rel_dotted, desc)
    vocab = sa.vocabulary(vocab_files)
    vocab["source_files"] = [p.relative_to(pkg_dir).as_posix() for p in vocab_files]
    record["vocabulary"] = vocab
    record["dependence"] = _dependence(pkg_dir, rel_dotted, desc)
    manifest = custody.manifest_replay(pkg_dir)
    record["custody"] = {
        "manifest": manifest,
        "records": custody.record_replay(pkg_dir, manifest),
        "commitment_timing": custody.commitment_timing(repo_root, pkg_dir, options.git),
    }
    record["mutation_inventory"] = mutation_inventory.inventory(
        pkg_dir, desc["mutations"], desc["mutation_dir_other_files"]
    )
    cases = worker.load_cases(
        str(pkg_dir),
        [{"path": c["path"], "index": c["index"]} for c in desc["cases"]],
        desc["unwrap_input"],
    )
    examples, example_outputs = _examples(pkg_dir, desc)

    references: list[dict[str, Any]] = [{} for _ in cases]
    reference_calls: list[dict[str, Any] | None] = [None for _ in cases]
    variant_calls: list[dict[str, Any]] = [{} for _ in cases]
    notes: list[str] = []
    strategies: list[dict[str, Any]] = []
    responder_records: dict[int, dict[str, Any]] = {}
    responder_failure = "NOT_RUN"
    mutation_records: dict[int, dict[str, Any]] = {}
    items: list[list[int]] = []
    runnable = bool(desc["checkers"]) and not options.skip_execution
    if not desc["checkers"]:
        notes.append("no checker functions discovered; execution skipped")
    if runnable:
        base = _job_base(repo_root, pkg_dir, desc, options)
        if desc["solver"] is None:
            notes.append("no reference solver; reference and type-confusion responders skipped")
        else:
            res = _run(dict(base, mode="reference"), len(cases), pkg_dir, options)
            if res.import_error:
                notes.append(f"reference pass import error: {res.import_error}")
                record["reference_import_error"] = res.import_error
            for index, rec in res.records.items():
                if "worker_failure" in rec:
                    references[index] = {"outcome": rec["worker_failure"]}
                    continue
                references[index] = rec.get("solver", {})
                reference_calls[index] = rec.get("reference")
                variant_calls[index] = rec.get("variants", {})
            if res.crashes:
                notes.append(f"reference pass worker failures: {len(res.crashes)}")
                record["worker_failures_reference"] = res.crashes
        answer_id_key = _answer_id_key(references, example_outputs, cases)
        strategies = responders.build_strategies(
            answer_id_key=answer_id_key,
            vocab=vocab,
            references=references,
            example_outputs=example_outputs,
        )
        strategies += responders.case_derived_strategies(desc["package_id"], cases, answer_id_key)
        strategies += semantic.semantic_strategies(desc["package_id"], cases, references)
        items = [
            [ci, si]
            for ci in range(len(cases))
            for si, strategy in enumerate(strategies)
            if strategy.get("per_case") is None or strategy["per_case"][ci] is not None
        ]
        res = _run(
            dict(base, mode="responders", responders=strategies, items=items),
            len(items),
            pkg_dir,
            options,
        )
        responder_records = res.records
        if res.import_error:
            notes.append(f"responder pass import error: {res.import_error}")
        else:
            responder_failure = "MISSING"
        if res.crashes:
            notes.append(f"responder pass worker failures: {len(res.crashes)}")
            record["worker_failures_responders"] = res.crashes[:20]
        if desc["mutations"]:
            res = _run(
                dict(base, mode="mutations", mutations=desc["mutations"]),
                len(desc["mutations"]),
                pkg_dir,
                options,
            )
            mutation_records = res.records
            if res.import_error:
                notes.append(f"mutation pass import error: {res.import_error}")
    else:
        answer_id_key = _answer_id_key(references, example_outputs, cases)

    rows: list[dict[str, Any]] = []
    for index, (ci, si) in enumerate(items):
        rec = responder_records.get(index)
        calls = rec.get("calls") if rec else None
        failure = rec.get("worker_failure", responder_failure) if rec else responder_failure
        rows.append(
            {
                "kind": "responder",
                "case": desc["cases"][ci]["key"],
                "responder": strategies[si]["id"],
                "family": strategies[si]["family"],
                "calls": _row_calls(calls) if calls else {"gate": [failure, ""]},
            }
        )
    for index, case_desc in enumerate(desc["cases"]):
        ref = references[index]
        rows.append(
            {
                "kind": "reference",
                "case": case_desc["key"],
                "solver": {
                    k: ref.get(k)
                    for k in ("outcome", "shape", "status", "exact_json", "sha256", "message")
                    if k in ref
                },
                "calls": _row_calls(reference_calls[index]),
            }
        )
        for kind, var in sorted(variant_calls[index].items()):
            rows.append(
                {
                    "kind": "type_confusion",
                    "case": case_desc["key"],
                    "responder": kind,
                    "replacements": var.get("replacements"),
                    "calls": _row_calls(var.get("calls")),
                }
            )
    for index, entry in enumerate(desc["mutations"]):
        rec = mutation_records.get(index)
        if rec is None:
            continue
        calls = rec.get("calls")
        rows.append(
            {
                "kind": "mutation",
                "case": entry["key"],
                "calls": _row_calls(calls)
                if calls
                else {"gate": [rec.get("worker_failure", "MISSING"), ""]},
            }
        )
    record["strategies"] = strategies
    record["answer_id_key"] = answer_id_key
    record["reference_statuses"] = dict(
        sorted(
            Counter(
                str(r.get("status")) for r in references if r.get("outcome") == "RETURNED"
            ).items()
        )
    )
    record["execution_notes"] = notes
    record["leakage"] = _leakage(pkg_dir, desc, cases, references, examples)
    record["summary"] = summaries.summarize(desc, rows, strategies)
    record["summary"]["template_accepted_where_reference_differs"] = _template_vs_reference(
        desc, cases, references, rows, strategies
    )
    verdicts = [r.get("verdict") for r in record["custody"]["records"] if r.get("verdict")]
    record["receipts"] = {
        "verdicts": sorted(verdicts),
        "pass_to_master": sum(1 for v in verdicts if v == "PASS_TO_MASTER"),
    }
    return record, rows


def _template_vs_reference(
    desc: dict[str, Any],
    cases: list[Any],
    references: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    strategies: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Cases where the gate accepts both the reference answer and a different fixed answer.

    For a problem with a unique answer (a count, a polynomial, an invariant)
    this shows the gate accepting a wrong answer; for a problem with many
    valid certificates it may be benign. The list is for case-by-case review.
    Only references whose JSON form is exact are compared.
    """
    index = {c["key"]: i for i, c in enumerate(desc["cases"])}
    templates = {s["id"]: s.get("template") for s in strategies}
    ref_ok = {
        r["case"]
        for r in rows
        if r["kind"] == "reference" and summaries.outcome(r["calls"], "gate") == "ACCEPT"
    }
    out = []
    for row in rows:
        if row["kind"] != "responder" or row["family"] not in summaries.TEMPLATE_FAMILIES:
            continue
        if not summaries.is_non_refusal_answer(templates[row["responder"]]):
            continue
        if row["case"] not in ref_ok or summaries.outcome(row["calls"], "gate") != "ACCEPT":
            continue
        ci = index[row["case"]]
        ref = references[ci]
        if not ref.get("exact_json") or not ref.get("sha256"):
            continue
        answer = worker.instantiate(templates[row["responder"]], cases[ci])
        text = json.dumps(answer, sort_keys=True, ensure_ascii=False)
        if canonical.sha256_bytes(text.encode("utf-8")) != ref["sha256"]:
            out.append({"case": row["case"], "strategy": row["responder"]})
    return out


def _answer_id_key(
    references: list[dict[str, Any]], example_outputs: list[tuple[str, Any]], cases: list[Any]
) -> str | None:
    counts: Counter[str] = Counter()
    for ref in references:
        for key in ref.get("id_keys", []) or []:
            counts[key] += 1
    if not counts:
        for _path, output in example_outputs:
            if isinstance(output, dict):
                counts.update(k for k in ("id", "case_id") if k in output)
    if not counts:
        for case in cases:
            if isinstance(case, dict):
                counts.update(k for k in ("id", "case_id") if k in case)
    if not counts:
        return None
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def _leakage(
    pkg_dir: Path,
    desc: dict[str, Any],
    cases: list[Any],
    references: list[dict[str, Any]],
    examples: list[tuple[str, Any, bool]],
) -> dict[str, Any]:
    vocabulary: set[str] = set()
    for ref in references:
        vocabulary |= set(ref.get("tokens") or [])
    per_case = []
    field_names: Counter[str] = Counter()
    for index, case_desc in enumerate(desc["cases"]):
        tokens = references[index].get("tokens")
        id_leak = leakage.case_id_leak(case_desc["case_id"], cases[index], tokens)
        fields = leakage.flagged_fields(cases[index], tokens)
        field_names.update(f["field"] for f in fields)
        if (id_leak and any(id_leak.values())) or any(
            f["value_shares_answer_tokens"] or f["named_answer_field"] for f in fields
        ):
            per_case.append(
                {
                    "case": case_desc["key"],
                    "case_id": case_desc["case_id"],
                    "id": id_leak,
                    "fields": fields,
                }
            )
    duplicates = leakage.example_duplicates(
        [(c["key"], cases[i]) for i, c in enumerate(desc["cases"])], examples
    )
    runners = {}
    for rel in desc["runner_files"]:
        lint = leakage.runner_lint(
            pkg_dir / rel, vocabulary, inline_cases=layout.is_runner_named(rel)
        )
        if lint.get("prompt_interpolations") or lint.get("inline_cases") or lint.get("parse_error"):
            runners[rel] = lint
    judge_ids = {c["case_id"] for c in desc["cases"] if c["case_id"]}
    example_ids = {
        inp[k]
        for _p, inp, _h in examples
        if isinstance(inp, dict)
        for k in ("id", "case_id")
        if isinstance(inp.get(k), str)
    }
    answer_files = {}
    participant = pkg_dir / "participant_packet"
    if participant.is_dir():
        for path in sorted(participant.glob("*.jsonl")):
            answer_files[path.relative_to(pkg_dir).as_posix()] = leakage.answers_file_overlap(
                path, judge_ids, example_ids
            )
    return {
        "cases_scanned": len(desc["cases"]),
        "flagged_field_names": dict(sorted(field_names.items())),
        "per_case": per_case,
        "example_duplicates": duplicates,
        "runner_files": runners,
        "participant_answer_files": answer_files,
    }


def compact_outcomes(record: dict[str, Any], rows: list[dict[str, Any]]) -> list[Any]:
    """Raw per-call outcomes as a header plus one compact array per row.

    Row layout: ``[kind, index, responder, [code, message_index] per role]``
    with roles in header order (``gate`` first) and ``index`` into the
    header's ``cases`` (or ``mutations`` for mutation rows). Codes: A accept,
    R reject, E exception, T timeout, U uninterpretable, W worker failure,
    M not run. A message index of -1 means no message.
    """
    desc = record["descriptor"]
    roles = ["gate"] + [c["role"] for c in desc["checkers"]]
    case_index = {c["key"]: i for i, c in enumerate(desc["cases"])}
    mutation_index = {m["key"]: i for i, m in enumerate(desc["mutations"])}
    messages: list[str] = []
    message_index: dict[str, int] = {}
    body = []
    for row in rows:
        cells = []
        for role in roles:
            value = row["calls"].get(role)
            if not value:
                cells.append(["M", -1])
                continue
            text = value[1] or ""
            idx = -1
            if text:
                if text not in message_index:
                    message_index[text] = len(messages)
                    messages.append(text)
                idx = message_index[text]
            cells.append([OUTCOME_CODES.get(value[0], "U"), idx])
        index = (
            mutation_index[row["case"]] if row["kind"] == "mutation" else case_index[row["case"]]
        )
        extra = (
            row.get("solver", {}).get("status")
            if row["kind"] == "reference"
            else row.get("responder")
        )
        body.append([row["kind"], index, extra, *cells])
    header = {
        "format": "judge_audit.outcomes.v1",
        "package_id": record["package_id"],
        "roles": roles,
        "cases": [c["key"] for c in desc["cases"]],
        "mutations": [m["key"] for m in desc["mutations"]],
        "responders": [s["id"] for s in record["strategies"]],
        "messages": messages,
    }
    return [header, *body]


TREE_STATE_SCOPE = layout.CHALLENGES_REL


def _tree_state(repo_root: Path) -> str:
    """SHA-256 over every file path and its bytes under the audited challenge tree.

    ``__pycache__`` is skipped. Writers elsewhere in the same checkout, and the
    audit's own output, are outside this scope and are not compared.
    """
    digest = hashlib.sha256()
    scope = repo_root / TREE_STATE_SCOPE
    files = sorted(
        (p for p in scope.rglob("*") if p.is_file() and "__pycache__" not in p.parts),
        key=lambda p: p.relative_to(scope).as_posix().encode("utf-8"),
    )
    for path in files:
        digest.update(path.relative_to(scope).as_posix().encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return f"{len(files)}:{digest.hexdigest()}"


def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, check=False)
    return proc.stdout.decode("utf-8", errors="replace").strip()


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Judge-packet audit harness (offline, no model calls)."
    )
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--work-dir",
        required=True,
        help="scratch directory for job files and the worker intelligence root",
    )
    parser.add_argument(
        "--packages", nargs="*", default=None, help="package IDs such as C014 W10; default all"
    )
    parser.add_argument("--call-timeout", type=int, default=20)
    parser.add_argument("--solver-timeout", type=int, default=90)
    parser.add_argument("--wall-timeout", type=int, default=3600)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--shards", type=int, default=1, help="parallel workers per package pass")
    parser.add_argument("--skip-execution", action="store_true")
    parser.add_argument(
        "--git-repo", default=None, help="repository for history queries (default: the repo root)"
    )
    parser.add_argument(
        "--commit", default="HEAD", help="revision the audited tree holds (default: HEAD)"
    )
    args = argv if argv is not None else sys.argv[1:]
    options = parser.parse_args(args)
    repo_root = Path(options.repo_root).resolve()
    out = Path(options.out).resolve()
    started = time.time()
    git_repo = Path(options.git_repo).resolve() if options.git_repo else repo_root
    commit = _git(git_repo, "rev-parse", "--verify", f"{options.commit}^{{commit}}")
    if not commit:
        if options.git_repo is not None or options.commit != "HEAD":
            parser.error(f"cannot resolve {options.commit!r} in {git_repo}")
        # an unversioned tree (for example a test fixture): history queries find nothing
        commit = "UNVERSIONED"
    options.git = custody.GitRef(git_repo, commit if commit != "UNVERSIONED" else "HEAD")
    try:
        pkgs = layout.discover_packages(repo_root)
    except OSError as exc:
        parser.error(f"cannot discover current judge packages: {exc}")
    available = {layout.package_id(p) for p in pkgs} | special_checks.available_package_ids(repo_root)
    selected = available
    if options.packages is not None:
        wanted = {p.upper() for p in options.packages}
        if not wanted:
            parser.error("--packages requires at least one package ID")
        unknown = wanted - available
        if unknown:
            parser.error("unknown package IDs: " + ", ".join(sorted(unknown)))
        selected = wanted
        pkgs = [p for p in pkgs if layout.package_id(p) in wanted]
    if not selected:
        parser.error("no judge packages or special-check sources discovered")
    status_before = _tree_state(repo_root)

    def one(pkg_dir: Path) -> dict[str, Any]:
        record, rows = audit_package(repo_root, pkg_dir, options)
        canonical.write_jsonl_gz(
            out / "outcomes" / f"{record['package_id']}.jsonl.gz", compact_outcomes(record, rows)
        )
        canonical.write_json_gz(out / "packages" / f"{record['package_id']}.json.gz", record)
        print(
            f"[judge_audit] {record['package_id']}: {record['summary']['cases']} cases; {record['execution_notes']}",
            flush=True,
        )
        return record

    if options.jobs > 1:
        with ThreadPoolExecutor(max_workers=options.jobs) as pool:
            records = list(pool.map(one, pkgs))
    else:
        records = [one(p) for p in pkgs]
    # aggregate every package record on disk, so a rerun of a subset keeps the summary whole
    on_disk = sorted((out / "packages").glob("*.json.gz"), key=lambda p: p.name.encode("utf-8"))
    records = [canonical.read_json_gz(p) for p in on_disk]
    summary = summaries.aggregate(records)
    summary["special_cases"] = special_checks.special_cases(repo_root, options)
    summary["reference_values"] = special_checks.reference_value_checks(repo_root, options)
    summary["audited_head"] = commit
    summary["harness_version"] = HARNESS_VERSION
    canonical.write_json(out / "summary.json", summary)
    status_after = _tree_state(repo_root)
    info = {
        "command": subprocess.list2cmdline(
            [sys.executable, "-m", "omega_engine_woland.tests.pilots.judge_packet_audit.audit", *args]
        ),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "audited_repo": str(repo_root),
        "audited_head": summary["audited_head"],
        "git_repo": str(options.git.repo),
        "audited_tree_state_unchanged": status_before == status_after,
        "audited_tree_state_scope": f"SHA-256 over file paths and bytes under {TREE_STATE_SCOPE}",
        "audited_tree_state": status_after,
        "elapsed_seconds": str(int(time.time() - started)),
        "packages": sorted(selected),
        "harness_sources_sha256": harness_digests(),
    }
    canonical.write_json(out / "run_info.json", info)
    return 0


def harness_digests() -> dict[str, str]:
    """SHA-256 of each harness source file (LF bytes), to bind outputs to the code that made them."""
    here = Path(__file__).resolve().parent
    out = {}
    for path in sorted(here.glob("*.py")):
        out[path.name] = canonical.sha256_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
    return out


if __name__ == "__main__":
    sys.exit(run())
