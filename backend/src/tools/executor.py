"""
Internal tools for executing Bash commands, PowerShell commands, and Python scripts.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator
from langchain_core.tools import tool

_MAX_TIMEOUT = 300          # 5 minutes hard cap
_MAX_OUTPUT_BYTES = 10 * 1024 * 1024  # 10 MB output cap
_BASH_BLACKLIST = ["rm -rf /", "mkfs", ":(){:|:&};:", "dd if=/dev/zero"]
_PWSH_BLACKLIST  = ["Remove-Item -Recurse -Force /", "Format-Volume", "Clear-Disk"]


def _check_blacklist(command: str, blacklist: List[str]) -> Optional[str]:
    lower = command.lower()
    for pattern in blacklist:
        if pattern.lower() in lower:
            return f"Refused: command matches dangerous pattern '{pattern}'."
    return None


def _run(
    args: List[str],
    cwd: Optional[str],
    timeout: int,
    env: Optional[dict] = None,
) -> Dict[str, Any]:
    """Shared subprocess runner. Returns a normalised result dict."""
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
        stdout = proc.stdout[:_MAX_OUTPUT_BYTES] if proc.stdout else ""
        stderr = proc.stderr[:_MAX_OUTPUT_BYTES] if proc.stderr else ""
        truncated = len(proc.stdout or "") > _MAX_OUTPUT_BYTES or len(proc.stderr or "") > _MAX_OUTPUT_BYTES
        return {
            "success": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "truncated": truncated,
            "error": None if proc.returncode == 0 else f"Process exited with code {proc.returncode}.",
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "return_code": None, "stdout": "", "stderr": "",
                "truncated": False, "error": f"Timed out after {timeout}s."}
    except FileNotFoundError as e:
        return {"success": False, "return_code": None, "stdout": "", "stderr": "",
                "truncated": False, "error": f"Executable not found: {e}"}
    except Exception as e:
        return {"success": False, "return_code": None, "stdout": "", "stderr": "",
                "truncated": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class BashArgs(BaseModel):
    command: str = Field(..., min_length=1, description="The Bash command to execute.")
    working_directory: Optional[str] = Field(None, description="Directory to run the command in.")
    timeout: int = Field(60, ge=1, le=_MAX_TIMEOUT, description=f"Timeout in seconds (1–{_MAX_TIMEOUT}).")
    environment: Optional[Dict[str, str]] = Field(None, description="Extra environment variables to inject.")

    @field_validator("command")
    @classmethod
    def check_blacklist(cls, v: str) -> str:
        err = _check_blacklist(v, _BASH_BLACKLIST)
        if err:
            raise ValueError(err)
        return v

    @field_validator("working_directory")
    @classmethod
    def validate_cwd(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not Path(v).is_dir():
            raise ValueError(f"working_directory does not exist: '{v}'")
        return v


class PowerShellArgs(BaseModel):
    command: str = Field(..., min_length=1, description="The PowerShell command or script block to execute.")
    working_directory: Optional[str] = Field(None, description="Directory to run the command in.")
    timeout: int = Field(60, ge=1, le=_MAX_TIMEOUT, description=f"Timeout in seconds (1–{_MAX_TIMEOUT}).")
    environment: Optional[Dict[str, str]] = Field(None, description="Extra environment variables to inject.")

    @field_validator("command")
    @classmethod
    def check_blacklist(cls, v: str) -> str:
        err = _check_blacklist(v, _PWSH_BLACKLIST)
        if err:
            raise ValueError(err)
        return v

    @field_validator("working_directory")
    @classmethod
    def validate_cwd(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not Path(v).is_dir():
            raise ValueError(f"working_directory does not exist: '{v}'")
        return v


class PythonScriptArgs(BaseModel):
    script: str = Field(..., min_length=1, description="Python source code to execute as a script.")
    working_directory: Optional[str] = Field(None, description="Directory to run the script in.")
    timeout: int = Field(60, ge=1, le=_MAX_TIMEOUT, description=f"Timeout in seconds (1–{_MAX_TIMEOUT}).")
    requirements: Optional[List[str]] = Field(None, description="Pip packages to install before running.")
    environment: Optional[Dict[str, str]] = Field(None, description="Extra environment variables to inject.")

    @field_validator("requirements")
    @classmethod
    def validate_requirements(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            for pkg in v:
                if not pkg.strip():
                    raise ValueError("requirements list contains an empty string.")
                # Block direct URL installs and path traversal
                if pkg.startswith(("http://", "https://", "git+", "/"," ..", "~")):
                    raise ValueError(f"Unsafe requirement '{pkg}'. Only PyPI package names are allowed.")
        return v

    @field_validator("working_directory")
    @classmethod
    def validate_cwd(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not Path(v).is_dir():
            raise ValueError(f"working_directory does not exist: '{v}'")
        return v


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool("execute_bash", args_schema=BashArgs)
def execute_bash(
    command: str,
    working_directory: Optional[str] = None,
    timeout: int = 60,
    environment: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Execute a Bash command and return stdout, stderr, and the return code.

    Runs via the system Bash binary. On Windows this requires WSL or Git Bash
    to be on PATH. Dangerous patterns (e.g. rm -rf /) are blocked at validation.
    Output is capped at 10 MB to prevent memory issues.
    """
    bash = "bash"
    env = {**os.environ, **(environment or {})}
    return _run([bash, "-c", command], cwd=working_directory, timeout=timeout, env=env)


@tool("execute_powershell", args_schema=PowerShellArgs)
def execute_powershell(
    command: str,
    working_directory: Optional[str] = None,
    timeout: int = 60,
    environment: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Execute a PowerShell command and return stdout, stderr, and the return code.

    Uses 'pwsh' (PowerShell 7+) if available, falls back to 'powershell' (Windows
    PowerShell 5). Dangerous patterns are blocked at validation. Output is capped
    at 10 MB to prevent memory issues.
    """
    # Prefer cross-platform pwsh, fall back to legacy powershell on Windows
    pwsh = "pwsh" if _find_executable("pwsh") else "powershell"
    args = [pwsh, "-NonInteractive", "-NoProfile", "-Command", command]
    env = {**os.environ, **(environment or {})}
    return _run(args, cwd=working_directory, timeout=timeout, env=env)


@tool("execute_python_script", args_schema=PythonScriptArgs)
def execute_python_script(
    script: str,
    working_directory: Optional[str] = None,
    timeout: int = 60,
    requirements: Optional[List[str]] = None,
    environment: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Execute a Python script in a subprocess and return stdout, stderr, and the return code.

    The script runs in the project virtual environment's Python interpreter when
    available, but as a separate child process so it cannot affect the agent's runtime state. If requirements
    are provided they are pip-installed into a temporary directory that is added to
    the child's PYTHONPATH — the main environment is never modified.
    Output is capped at 10 MB to prevent memory issues.
    """
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        # Install requirements into an isolated packages dir
        packages_dir = os.path.join(tmpdir, "packages")
        if requirements:
            os.makedirs(packages_dir, exist_ok=True)
            install_result = _run(
                [sys.executable, "-m", "pip", "install", "--quiet", "--target", packages_dir, *requirements],
                cwd=None,
                timeout=timeout,
            )
            if not install_result["success"]:
                return {
                    "success": False,
                    "return_code": install_result["return_code"],
                    "stdout": "",
                    "stderr": install_result["stderr"],
                    "truncated": False,
                    "error": f"Failed to install requirements: {install_result['stderr']}",
                }

        # Write the script to a temp file
        script_path = os.path.join(tmpdir, "script.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        env = {**os.environ, **(environment or {})}
        if requirements:
            existing_pythonpath = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = f"{packages_dir}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else packages_dir

        return _run([sys.executable, script_path], cwd=working_directory, timeout=timeout, env=env)


def _find_executable(name: str) -> bool:
    """Return True if `name` is findable on PATH."""
    import shutil
    return shutil.which(name) is not None


if __name__ == "__main__":
    import json

    print("=== Bash ===")
    print(json.dumps(execute_bash.invoke({"command": "echo hello from bash"}), indent=2))

    print("\n=== PowerShell ===")
    print(json.dumps(execute_powershell.invoke({"command": "Write-Output 'hello from pwsh'"}), indent=2))

    print("\n=== Python script ===")
    print(json.dumps(execute_python_script.invoke({"script": "print('hello from python')"}), indent=2))
