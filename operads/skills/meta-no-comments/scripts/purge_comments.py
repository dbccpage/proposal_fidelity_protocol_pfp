from __future__ import annotations

import io
import os
import re
import sys
import tokenize
from pathlib import Path
from typing import Sequence

DOC_EXTENSIONS = {
    ".md",
    ".rst",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".jsonl",
    ".csv",
    ".xml",
    ".html",
    ".tex",
}
CODE_EXTENSIONS = {".py", ".rs", ".cpp", ".c", ".h", ".hpp", ".js", ".ts"}


def is_test_file(path: Path) -> bool:
    name = path.name.lower()
    return name.startswith("test") or name.startswith("tests")


def is_doc_file(path: Path) -> bool:
    return path.suffix.lower() in DOC_EXTENSIONS or path.name.lower() in {
        "readme",
        "license",
        "changelog",
    }


def purge_python_comments(source: str) -> str:
    reader = io.StringIO(source).readline
    tokens = tokenize.generate_tokens(reader)
    cleaned_tokens: list[tuple[int, str]] = []

    for toktype, tokval, _, _, _ in tokens:
        if toktype == tokenize.COMMENT:
            continue
        cleaned_tokens.append((toktype, tokval))

    return tokenize.untokenize(cleaned_tokens)


def purge_rust_cpp_comments(source: str) -> str:
    source = re.sub(r"/\*[\s\S]*?\*/", "", source)
    lines = source.splitlines()
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        if "//" in line:
            in_quote = False
            cut_idx = -1
            for i, char in enumerate(line):
                if char == '"' and (i == 0 or line[i - 1] != "\\"):
                    in_quote = not in_quote
                elif not in_quote and line[i : i + 2] == "//":
                    cut_idx = i
                    break
            if cut_idx != -1:
                line = line[:cut_idx].rstrip()
        cleaned.append(line)
    return "\n".join(cleaned) + ("\n" if source.endswith("\n") else "")


def purge_comments_from_file(file_path: Path) -> bool:
    if not file_path.is_file():
        return False
    if is_doc_file(file_path) or is_test_file(file_path):
        return False
    ext = file_path.suffix.lower()
    if ext not in CODE_EXTENSIONS:
        return False

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # Unreadable or not UTF-8. Never rewrite a file we could not read whole.
        return False

    if ext == ".py":
        try:
            new_content = purge_python_comments(content)
        except (SyntaxError, tokenize.TokenError, ValueError):
            # tokenize refuses malformed or truncated source. Leaving the file
            # untouched is the only safe outcome: a partial untokenize would
            # silently corrupt it.
            return False
    elif ext in (".rs", ".cpp", ".c", ".h", ".hpp"):
        new_content = purge_rust_cpp_comments(content)
    else:
        return False

    if new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def purge_target(path_str: str) -> int:
    target = Path(path_str)
    count = 0
    if target.is_file():
        if purge_comments_from_file(target):
            count += 1
    elif target.is_dir():
        for root, _, files in os.walk(target):
            for file in files:
                file_path = Path(root) / file
                if purge_comments_from_file(file_path):
                    count += 1
    return count


def main(argv: Sequence[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: purge_comments.py <file_or_dir1> [file_or_dir2 ...]")
        sys.exit(1)

    total_purged = 0
    for arg in args:
        total_purged += purge_target(arg)

    print(f"Purged comments from {total_purged} code file(s).")


if __name__ == "__main__":
    main()
