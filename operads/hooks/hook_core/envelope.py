"""Universal multi-host payload extractor for Antigravity, Claude Code, Codex, and CLI.

Distinguishes:
- CHECKED: Valid payload extracted for the expected tool/operation.
- NOT_APPLICABLE: Tool or payload is unrelated to this hook.
- INPUT_ERROR: Malformed JSON, missing required fields, or invalid field types.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ExtractedPayload:
    status: str  # "CHECKED", "NOT_APPLICABLE", "INPUT_ERROR"
    tool_name: str = ""
    command: Optional[str] = None
    target_files: List[str] = field(default_factory=list)
    cwd: Optional[str] = None
    workspace_paths: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    raw_data: Any = None


_PATCH_FILE_RE = re.compile(
    r"(?:^\*\*\*\s+(?:Update|Add|Delete)\s+File:\s*([^\r\n]+)|"
    r"^diff\s+--git\s+\S+\s+b/([^\r\n]+)|"
    r"^\+\+\+\s+b/([^\r\n]+)|"
    r"^---\s+a/([^\r\n]+))",
    re.MULTILINE,
)


def extract_files_from_patch(patch_text: str) -> List[str]:
    """Parse unified diff / patch headers to extract referenced file paths."""
    files: List[str] = []
    for match in _PATCH_FILE_RE.finditer(patch_text):
        for group in match.groups():
            if group:
                candidate = group.strip("\"' ")
                if candidate and candidate != "/dev/null" and candidate not in files:
                    files.append(candidate)
    return files


def extract_payload(
    cli_args: List[str],
    raw_stdin: str,
    expected_kind: str = "any",
) -> ExtractedPayload:
    """Parse CLI arguments or stdin payload across host environments."""
    raw_text = " ".join(cli_args).strip() if cli_args else ""
    if not raw_text:
        raw_text = raw_stdin.strip()

    if not raw_text:
        return ExtractedPayload(
            status="INPUT_ERROR",
            error_message="Empty hook input: no arguments or stdin provided",
        )

    # Check if raw_text represents a JSON payload
    if raw_text.startswith("{") or raw_text.startswith("["):
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            return ExtractedPayload(
                status="INPUT_ERROR",
                error_message=f"Malformed hook JSON payload: {exc}",
            )

        if not isinstance(data, dict):
            return ExtractedPayload(
                status="INPUT_ERROR",
                error_message="Hook payload must be a JSON object",
                raw_data=data,
            )

        if not data:
            return ExtractedPayload(
                status="INPUT_ERROR",
                error_message="Empty JSON object provided to hook",
                raw_data=data,
            )

        payload = ExtractedPayload(status="CHECKED", raw_data=data)

        # Extract workspace bounds and cwd if present at root
        if "workspacePaths" in data and isinstance(data["workspacePaths"], list):
            payload.workspace_paths = [str(p) for p in data["workspacePaths"]]
        if "cwd" in data and isinstance(data["cwd"], str):
            payload.cwd = data["cwd"]

        # 1. Antigravity format: toolCall: { name, args }
        if "toolCall" in data and isinstance(data["toolCall"], dict):
            tc = data["toolCall"]
            payload.tool_name = str(tc.get("name", ""))
            args = tc.get("args")
            if not isinstance(args, dict):
                return ExtractedPayload(
                    status="INPUT_ERROR",
                    tool_name=payload.tool_name,
                    error_message=f"Antigravity toolCall.args must be a dictionary, got {type(args).__name__}",
                    raw_data=data,
                )
            if "CommandLine" in args:
                cmd_val = args["CommandLine"]
                if not isinstance(cmd_val, str):
                    return ExtractedPayload(
                        status="INPUT_ERROR",
                        tool_name=payload.tool_name,
                        error_message=f"CommandLine must be string, got {type(cmd_val).__name__}",
                        raw_data=data,
                    )
                payload.command = cmd_val
            if "TargetFile" in args:
                payload.target_files.append(str(args["TargetFile"]))
            if "Cwd" in args and isinstance(args["Cwd"], str):
                payload.cwd = args["Cwd"]

            return _validate_payload_for_kind(payload, expected_kind)

        # 2. Claude Code / Codex format: tool_name, tool_input
        if "tool_name" in data or "tool_input" in data:
            payload.tool_name = str(data.get("tool_name", ""))
            tool_input = data.get("tool_input")
            if tool_input is None:
                tool_input = data.get("arguments") or data.get("input")

            if not isinstance(tool_input, dict):
                # If command is directly given or patch string
                if isinstance(tool_input, str):
                    if payload.tool_name == "apply_patch":
                        payload.target_files.extend(extract_files_from_patch(tool_input))
                    else:
                        payload.command = tool_input
                    return _validate_payload_for_kind(payload, expected_kind)
                return ExtractedPayload(
                    status="INPUT_ERROR",
                    tool_name=payload.tool_name,
                    error_message=f"tool_input must be a dictionary, got {type(tool_input).__name__}",
                    raw_data=data,
                )

            # Check command
            if "command" in tool_input or "CommandLine" in tool_input or "cmd" in tool_input:
                cmd_val = (
                    tool_input.get("command")
                    or tool_input.get("CommandLine")
                    or tool_input.get("cmd")
                )
                if payload.tool_name in ("Bash", "PowerShell", "run_command") and not isinstance(
                    cmd_val, str
                ):
                    return ExtractedPayload(
                        status="INPUT_ERROR",
                        tool_name=payload.tool_name,
                        error_message=f"command must be string, got {type(cmd_val).__name__}",
                        raw_data=data,
                    )
                if isinstance(cmd_val, str):
                    if payload.tool_name == "apply_patch":
                        payload.target_files.extend(extract_files_from_patch(cmd_val))
                    else:
                        payload.command = cmd_val

            # Check file paths
            for key in ("file_path", "path", "TargetFile", "target_file", "file"):
                if key in tool_input and tool_input[key]:
                    payload.target_files.append(str(tool_input[key]))
            if "files" in tool_input and isinstance(tool_input["files"], list):
                payload.target_files.extend(str(f) for f in tool_input["files"])

            return _validate_payload_for_kind(payload, expected_kind)

        # 3. Generic dictionary format fallback (including tool / arguments structure)
        args_dict = None
        for key in ("arguments", "args", "tool_input", "input"):
            if key in data and isinstance(data[key], dict):
                args_dict = data[key]
                break

        cmd_candidate = (
            data.get("command")
            or data.get("CommandLine")
            or data.get("cmd")
            or data.get("command_line")
        )
        if cmd_candidate is None and args_dict:
            cmd_candidate = (
                args_dict.get("command")
                or args_dict.get("CommandLine")
                or args_dict.get("cmd")
                or args_dict.get("command_line")
            )

        if cmd_candidate is not None:
            if not isinstance(cmd_candidate, str):
                return ExtractedPayload(
                    status="INPUT_ERROR",
                    error_message=f"command must be string, got {type(cmd_candidate).__name__}",
                    raw_data=data,
                )
            payload.command = cmd_candidate

        for key in ("file_path", "path", "TargetFile", "target_file", "file"):
            if key in data and data[key]:
                payload.target_files.append(str(data[key]))
            if args_dict and key in args_dict and args_dict[key]:
                payload.target_files.append(str(args_dict[key]))

        if "files" in data and isinstance(data["files"], list):
            payload.target_files.extend(str(f) for f in data["files"])
        if args_dict and "files" in args_dict and isinstance(args_dict["files"], list):
            payload.target_files.extend(str(f) for f in args_dict["files"])

        return _validate_payload_for_kind(payload, expected_kind)

    # Raw CLI string mode (e.g. arguments passed on command line)
    if expected_kind == "file":
        cleaned = raw_text.strip("\"' ")
        return ExtractedPayload(
            status="CHECKED",
            tool_name="cli",
            target_files=[cleaned] if cleaned else [],
            raw_data=raw_text,
        )

    # Default raw text as command
    return ExtractedPayload(
        status="CHECKED",
        tool_name="cli",
        command=raw_text,
        raw_data=raw_text,
    )


def _validate_payload_for_kind(payload: ExtractedPayload, expected_kind: str) -> ExtractedPayload:
    if expected_kind == "command":
        if payload.command is None:
            if payload.tool_name and payload.tool_name not in (
                "run_command",
                "Bash",
                "PowerShell",
                "cli",
            ):
                payload.status = "NOT_APPLICABLE"
                return payload
            payload.status = "INPUT_ERROR"
            payload.error_message = "No command found in command hook payload"
    elif expected_kind == "file":
        if not payload.target_files:
            file_tools = (
                "write_to_file",
                "replace_file_content",
                "multi_replace_file_content",
                "Write",
                "Edit",
                "EditMultipleFiles",
                "apply_patch",
                "cli",
            )
            if payload.tool_name and payload.tool_name not in file_tools:
                payload.status = "NOT_APPLICABLE"
                return payload
            payload.status = "INPUT_ERROR"
            payload.error_message = "No target file path found in file hook payload"

    return payload
