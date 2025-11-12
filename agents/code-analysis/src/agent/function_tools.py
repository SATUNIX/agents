"""Function tools registered with the OpenAI Agents SDK."""

from __future__ import annotations

import fnmatch
import hashlib
import shlex
import subprocess
from pathlib import Path
from typing import Dict, List

from .sdk_imports import function_tool


def build_function_tools(config, policies, state):
    """Return a list of @function_tool callables bound to the current config."""

    def log_event(tool: str, payload: Dict, result: Dict | None = None, error: str | None = None) -> None:
        if state is None:
            return
        state.append_event(
            "tool_call",
            {
                "tool": tool,
                "payload": payload,
                "result": result,
                "error": error,
            },
        )

    def allowed_globs() -> List[str]:
        patterns: List[str] = list(policies.allowed_globs())
        for profile in config.settings.tools.values():
            patterns.extend(profile.allowed_globs or [])
        return [p for p in patterns if p]

    def blocked_globs() -> List[str]:
        patterns: List[str] = list(policies.blocked_globs())
        for profile in config.settings.tools.values():
            patterns.extend(profile.denied_globs or [])
        return [p for p in patterns if p]

    def ensure_path(path: str | Path) -> Path:
        candidate = (config.workspace / Path(path)).resolve()
        if config.workspace not in candidate.parents and candidate != config.workspace:
            raise ValueError(f"Path {candidate} escapes workspace {config.workspace}")
        rel = candidate.relative_to(config.workspace)
        rel_str = str(rel)
        if blocked_globs():
            for pattern in blocked_globs():
                if fnmatch.fnmatch(rel_str, pattern):
                    raise ValueError(f"Path {rel_str} blocked by policy {pattern}")
        allowed = allowed_globs()
        if allowed and not any(fnmatch.fnmatch(rel_str, pattern) for pattern in allowed):
            raise ValueError(f"Path {rel_str} not permitted by policy")
        return candidate

    def ensure_command(command_line: str) -> List[str]:
        args = shlex.split(command_line)
        if not args:
            raise ValueError("Empty command")
        allowed = policies.allowed_commands() or ["ls", "cat", "python", "pytest", "rg", "git", "git status"]
        for entry in allowed:
            tokens = shlex.split(entry)
            if args[: len(tokens)] == tokens:
                break
        else:
            raise ValueError(f"Command '{args[0]}' not allowed")
        if not policies.allow_network() and any(token.startswith("http") for token in args):
            raise ValueError("Network access disabled by policy")
        return args

    @function_tool(name="workspace_status", description="Summarize workspace and policy context")
    def workspace_status() -> str:
        summary = {
            "workspace": str(config.workspace),
            "policy_dir": str(config.policy_dir),
            "allow_net": policies.allow_network(),
        }
        log_event("workspace_status", {}, summary)
        return str(summary)

    @function_tool(name="workspace_read_file", description="Read a UTF-8 file inside the workspace")
    def workspace_read_file(path: str) -> str:
        file_path = ensure_path(path)
        content = file_path.read_text(encoding="utf-8")
        log_event("workspace_read_file", {"path": path}, {"bytes": len(content)})
        return content

    @function_tool(name="workspace_write_file", description="Write text to a file inside the workspace")
    def workspace_write_file(path: str, content: str) -> str:
        file_path = ensure_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        log_event("workspace_write_file", {"path": path, "bytes": len(content)})
        return f"Wrote {path} ({len(content)} bytes)"

    @function_tool(name="workspace_shell_exec", description="Execute a guarded shell command inside the workspace")
    def workspace_shell_exec(command: str, cwd: str | None = None) -> Dict[str, str]:
        args = ensure_command(command)
        working_dir = ensure_path(cwd or ".")
        proc = subprocess.run(
            args,
            cwd=working_dir,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            error = {
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "returncode": proc.returncode,
            }
            log_event("workspace_shell_exec", {"command": command}, error, error=proc.stderr)
            raise RuntimeError(proc.stderr or "Shell command failed")
        result = {"stdout": proc.stdout, "stderr": proc.stderr}
        log_event("workspace_shell_exec", {"command": command}, result)
        return result

    @function_tool(name="workspace_repo_summary", description="Summarize repository contents")
    def workspace_repo_summary(max_files: int = 200) -> Dict[str, object]:
        files: List[str] = []
        for entry in config.workspace.rglob("*"):
            if entry.is_file():
                rel = entry.relative_to(config.workspace)
                try:
                    ensure_path(rel)
                except ValueError:
                    continue
                files.append(str(rel))
                if len(files) >= max_files:
                    break
        digest = hashlib.sha256("\n".join(files).encode()).hexdigest()
        result = {"files_indexed": len(files), "digest": digest[:16], "examples": files[:10]}
        log_event("workspace_repo_summary", {"max_files": max_files}, result)
        return result

    return [workspace_status, workspace_read_file, workspace_write_file, workspace_shell_exec, workspace_repo_summary]
