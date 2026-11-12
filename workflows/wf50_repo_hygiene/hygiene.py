"""WF50 repo hygiene: find badly named files, rename them, and fix every reference.

Three commands, run from the repository root:

    python workflows/wf50_repo_hygiene/hygiene.py survey --out plan.json
    python workflows/wf50_repo_hygiene/hygiene.py apply plan.json [--dry-run]
    python workflows/wf50_repo_hygiene/hygiene.py residue plan.json

``survey`` lists every tracked file or folder whose name breaks the rule in
naming_policy.json and proposes a snake_case name. Reviewers may edit the plan
(drop entries, change targets) before ``apply`` moves the files and rewrites
references in every tracked text file. ``residue`` reports old names that are
still mentioned anywhere, so a person or agent can fix what the rewrite could
not see (dynamic imports, prose, generated files).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
POLICY_PATH = HERE / "naming_policy.json"
GOOD = re.compile(r"^\.?[a-z0-9_]+(\.[a-z0-9_]+)*$")
RUN = re.compile(r"[A-Za-z0-9_\-./\\]+")
CODE_SUFFIXES = {".py", ".pyi", ".toml", ".cfg", ".ini", ".yml", ".yaml", ".json"}


def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def glob_match(path: str, pattern: str) -> bool:
    """Match a repo path: '*' stays inside one folder, '**/' spans any number of folders."""
    rx = ""
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            rx += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            rx += ".*"
            i += 2
        elif pattern[i] == "*":
            rx += "[^/]*"
            i += 1
        else:
            rx += re.escape(pattern[i])
            i += 1
    return re.fullmatch(rx, path) is not None


def snake(segment: str) -> str:
    """Return the snake_case form of one path segment, keeping a leading dot or underscores."""
    lead = re.match(r"^[._]*", segment).group(0)
    body = segment[len(lead):]
    parts = body.split(".")
    fixed = []
    for part in parts:
        p = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", part)
        p = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", p)
        p = re.sub(r"[^A-Za-z0-9_]+", "_", p).lower()
        trail = "__" if p.endswith("__") and part.endswith("__") else ""
        p = re.sub(r"_+", "_", p).strip("_") + trail
        fixed.append(p or "_")
    return lead + ".".join(fixed)


class Policy:
    def __init__(self, data: dict, files: list[str]):
        self.keep_basenames = set(data["keep_basenames"])
        self.keep_globs = list(data["keep_globs"])
        self.rewrite_exclude = list(data["rewrite_exclude_globs"])
        self.max_bytes = int(data["max_rewrite_bytes"])
        markers = set(data["frozen_bundle_markers"])
        self.frozen_dirs = {str(PurePosixPath(f).parent) for f in files if PurePosixPath(f).name in markers}

    def _glob(self, path: str, globs: list[str]) -> bool:
        return any(glob_match(path, g) for g in globs)

    def frozen(self, path: str) -> bool:
        parents = PurePosixPath(path).parents
        return any(str(p) in self.frozen_dirs for p in parents)

    def keep_segment(self, path: str, is_dir: bool) -> bool:
        name = PurePosixPath(path).name
        if GOOD.match(name) or (not is_dir and name in self.keep_basenames):
            return True
        if self._glob(path, self.keep_globs):
            return True
        return self.frozen(path)

    def rewritable(self, path: str) -> bool:
        return not self._glob(path, self.rewrite_exclude)


def survey(files: list[str], policy: Policy) -> dict:
    dirs = sorted({str(p) for f in files for p in PurePosixPath(f).parents if str(p) != "."})
    renames: dict[str, str] = {}
    for d in dirs:
        if not policy.keep_segment(d, True):
            renames[d] = snake(PurePosixPath(d).name)
    for f in files:
        if not policy.keep_segment(f, False):
            renames[f] = snake(PurePosixPath(f).name)

    def target(path: str) -> str:
        parts = PurePosixPath(path).parts
        out = [renames.get("/".join(parts[: i + 1]), parts[i]) for i in range(len(parts))]
        return "/".join(out)

    moves = {f: target(f) for f in files if target(f) != f}
    existing = {f.lower() for f in files if f not in moves}
    seen: dict[str, str] = {}
    collisions = []
    for old, new in sorted(moves.items()):
        key = new.lower()
        if key in existing or key in seen:
            collisions.append({"old": old, "new": new, "clashes_with": seen.get(key, new)})
        seen[key] = old
    bad = {c["old"] for c in collisions}
    by_area: dict[str, int] = defaultdict(int)
    for old in moves:
        parts = old.split("/")
        by_area["/".join(parts[:2]) if len(parts) > 2 else parts[0] if len(parts) > 1 else "(root)"] += 1
    return {
        "segment_renames": dict(sorted(renames.items())),
        "moves": {o: n for o, n in sorted(moves.items()) if o not in bad},
        "collisions": collisions,
        "counts": {"files_to_move": len(moves) - len(bad), "collisions": len(collisions)},
        "by_area": dict(sorted(by_area.items(), key=lambda kv: -kv[1])),
    }


# ---------------------------------------------------------------- reference rewriting


def build_maps(moves: dict[str, str], files: list[str]):
    """Token maps for rewriting.

    uniform: basename (or folder name) -> new name, used only when every tracked
    occurrence of that name is renamed the same way, so a bare mention is safe.
    suffix:  'parent/old_name' style path tails -> new tails, for names that are
    renamed in some places and kept in others.
    """
    seg_new: dict[str, set[str]] = defaultdict(set)
    seg_kept: set[str] = set()
    for f in files:
        old_parts = f.split("/")
        new_parts = moves.get(f, f).split("/")
        for o, n in zip(old_parts, new_parts):
            if o == n:
                seg_kept.add(o)
            else:
                seg_new[o].add(n)
    uniform = {o: next(iter(ns)) for o, ns in seg_new.items() if len(ns) == 1 and o not in seg_kept}
    for o, n in list(uniform.items()):
        if o.endswith(".md") and n.endswith(".md"):
            uniform.setdefault(o[:-3], n[:-3])
    suffix: dict[str, str] = {}
    for old, new in moves.items():
        op, np_ = old.split("/"), new.split("/")
        for k in range(2, len(op) + 1):
            suffix.setdefault("/".join(op[-k:]), "/".join(np_[-k:]))
    py_modules = {}
    for old, new in moves.items():
        if old.endswith(".py"):
            py_modules[PurePosixPath(old).stem] = PurePosixPath(new).stem
        for o, n in zip(PurePosixPath(old).parent.parts, PurePosixPath(new).parent.parts):
            if o != n:
                py_modules[o] = n
    py_modules = {o: n for o, n in py_modules.items() if o not in seg_kept or o in uniform}
    return uniform, suffix, py_modules


OPEN_CLOSE = {'"': '"', "'": "'", "`": "`", "(": ")", "[": "]", "<": ">"}


def rewrite_text(text: str, uniform, suffix, py_modules, is_code: bool) -> tuple[str, int]:
    count = 0

    def fix_run(m: re.Match) -> str:
        nonlocal count
        run = m.group(0)
        start, end = m.start(), m.end()
        before = text[start - 1] if start else ""
        after = text[end] if end < len(text) else ""
        has_sep = "/" in run or "\\" in run
        enclosed = before in OPEN_CLOSE and after == OPEN_CLOSE[before]
        norm = run.replace("\\", "/")
        sep = "\\" if "\\" in run and "/" not in run else "/"
        core = norm.rstrip(".")
        tail = norm[len(core):]
        for key in sorted((k for k in suffix if core.endswith(k)), key=len, reverse=True):
            head = core[: len(core) - len(key)]
            if head == "" or head.endswith("/"):
                new_head = "/".join(uniform.get(s, s) for s in head.split("/"))
                out = (new_head + suffix[key] + tail).replace("/", sep)
                if out != run:
                    count += 1
                return out
        segs = core.split("/")
        new_segs = []
        for seg in segs:
            if seg in uniform and ("." in seg or has_sep or enclosed):
                new_segs.append(uniform[seg])
            elif is_code and "." in seg and any(p in py_modules for p in seg.split(".")):
                new_segs.append(".".join(py_modules.get(p, p) for p in seg.split(".")))
            else:
                new_segs.append(seg)
        out = "/".join(new_segs).replace("/", sep) + tail
        if out != run:
            count += 1
        return out

    return RUN.sub(fix_run, text), count


def is_text(data: bytes) -> bool:
    return b"\0" not in data[:8192]


def move_tracked(moves: dict[str, str]) -> None:
    """Move files on disk (two steps so case-only renames work on Windows) and record them in git."""
    root = Path.cwd()
    staging = {}
    for i, (old, new) in enumerate(moves.items()):
        src = root / old
        tmp = src.with_name(f"{src.name}.wf50tmp{i}")
        os.replace(src, tmp)
        staging[tmp] = root / new
    for tmp, dst in staging.items():
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp, dst)
    for old in moves:
        d = (root / old).parent
        while d != root:
            try:
                d.rmdir()
            except OSError:
                break
            d = d.parent
    lists = HERE / ".wf50_paths"
    lists.mkdir(exist_ok=True)
    (lists / "old.txt").write_text("\n".join(moves) + "\n", encoding="utf-8")
    (lists / "new.txt").write_text("\n".join(moves.values()) + "\n", encoding="utf-8")
    subprocess.run(["git", "rm", "-q", "--cached", f"--pathspec-from-file={lists / 'old.txt'}"], check=True)
    subprocess.run(["git", "add", "-f", f"--pathspec-from-file={lists / 'new.txt'}"], check=True)
    for p in lists.iterdir():
        p.unlink()
    lists.rmdir()


def apply(plan: dict, dry_run: bool) -> dict:
    files = tracked_files()
    policy = Policy(load_policy(), files)
    moves = plan["moves"]
    uniform, suffix, py_modules = build_maps(moves, files)
    edits = {}
    for f in files:
        if not policy.rewritable(f):
            continue
        path = Path(f)
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if len(data) > policy.max_bytes or not is_text(data):
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        new_text, n = rewrite_text(text, uniform, suffix, py_modules, path.suffix in CODE_SUFFIXES)
        if n:
            edits[f] = n
            if not dry_run:
                path.write_bytes(new_text.encode("utf-8"))
    if not dry_run:
        move_tracked(moves)
    return {"files_moved": len(moves), "files_edited": len(edits), "references_rewritten": sum(edits.values()),
            "edited": edits}


def residue(plan: dict) -> dict:
    """Old names that still appear in tracked text files after apply."""
    files = tracked_files()
    policy = Policy(load_policy(), files)
    olds = {PurePosixPath(o).name for o in plan["moves"]}
    olds |= {PurePosixPath(o).name for o in plan["segment_renames"]}
    olds = {o for o in olds if len(o) > 3}
    if not olds:
        return {"hits": {}}
    pat = re.compile(r"(?<![A-Za-z0-9_\-])(" + "|".join(sorted(map(re.escape, olds), key=len, reverse=True))
                     + r")(?![A-Za-z0-9_\-])")
    hits: dict[str, list[str]] = defaultdict(list)
    for f in files:
        if not policy.rewritable(f):
            continue
        try:
            data = Path(f).read_bytes()
        except OSError:
            continue
        if len(data) > policy.max_bytes or not is_text(data):
            continue
        text = data.decode("utf-8", "replace")
        for m in pat.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            hits[m.group(1)].append(f"{f}:{line}")
    return {"names_still_mentioned": len(hits), "hits": dict(sorted(hits.items()))}


def rebaseline(paths: list[str], reason: str) -> dict:
    """Re-pin named sources in governance/baseline.json to their current bytes.

    Use it only for files this workflow moved or mechanically rewrote (paths
    and names, no behaviour), or for new WF50 tooling. It touches the listed
    paths and nothing else, unlike ``checker baseline --allow-add``.
    """
    import hashlib

    target = Path("governance/baseline.json")
    data = json.loads(target.read_text(encoding="utf-8"))
    changed = 0
    for p in paths:
        digest = hashlib.sha256(Path(p).read_bytes()).hexdigest()
        entry = data["entries"].get(p)
        if entry is None or entry["sha256"] != digest:
            data["entries"][p] = {"sha256": digest, "reason": reason}
            changed += 1
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return {"re_pinned": changed}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("survey")
    s.add_argument("--out", required=True)
    s.add_argument("--exclude", action="append", default=[], help="glob of paths to leave alone this run")
    a = sub.add_parser("apply")
    a.add_argument("plan")
    a.add_argument("--dry-run", action="store_true")
    r = sub.add_parser("residue")
    r.add_argument("plan")
    r.add_argument("--out")
    b = sub.add_parser("rebaseline", help="re-pin listed governed sources after a mechanical edit")
    b.add_argument("--reason", required=True)
    b.add_argument("paths", nargs="+")
    args = ap.parse_args(argv)

    if args.cmd == "rebaseline":
        print(json.dumps(rebaseline(args.paths, args.reason)))
        return 0

    if args.cmd == "survey":
        files = [f for f in tracked_files() if not any(glob_match(f, g) for g in args.exclude)]
        result = survey(files, Policy(load_policy(), files))
        Path(args.out).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({"counts": result["counts"], "by_area": result["by_area"]}, indent=1))
    elif args.cmd == "apply":
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        report = apply(plan, args.dry_run)
        print(json.dumps({k: v for k, v in report.items() if k != "edited"}, indent=1))
    else:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        report = residue(plan)
        if args.out:
            Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({k: (len(v) if k == "hits" else v) for k, v in report.items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
