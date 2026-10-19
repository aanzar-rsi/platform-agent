"""
Internal tools for file I/O operations, file search, and directory management.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from langchain_core.tools import tool

# Safety limits
_MAX_READ_BYTES = 50 * 1024 * 1024       # 50 MB
_MAX_WRITE_BYTES = 50 * 1024 * 1024      # 50 MB
_MAX_SEARCH_BYTES = 100 * 1024 * 1024    # 100 MB (streamed)
_MAX_SEARCH_RESULTS = 500
_MAX_LINE_LENGTH = 10_000
_ALLOWED_ENCODINGS = {"utf-8", "utf-16", "latin-1", "ascii", "utf-8-sig"}
_ALLOWED_TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".jsonl", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".env", ".log", ".xml", ".html",
    ".htm", ".css", ".js", ".ts", ".py", ".sh", ".bat", ".ps1",
    ".java", ".c", ".cpp", ".h", ".rs", ".go", ".rb", ".php",
    ".swift", ".kt", ".r", ".sql", ".tf", ".tsx", ".jsx",
}


def _resolve_text_file(file_path: str) -> tuple[Optional[Path], Optional[str]]:
    """Resolve and validate a path points to a readable text file. Returns (path, error)."""
    try:
        path = Path(file_path).resolve()
    except Exception as e:
        return None, f"Invalid path: {e}"

    if not path.exists():
        return None, f"File not found: '{file_path}'"
    if not path.is_file():
        return None, f"Path is not a file: '{file_path}'"
    if path.suffix.lower() not in _ALLOWED_TEXT_EXTENSIONS:
        return None, (
            f"Unsupported file type '{path.suffix}'. "
            f"Only text-based files are allowed: {', '.join(sorted(_ALLOWED_TEXT_EXTENSIONS))}"
        )
    return path, None


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ReadFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to the file to read (absolute or relative).")
    encoding: str = Field("utf-8", description="File encoding. One of: utf-8, utf-16, latin-1, ascii, utf-8-sig.")
    max_lines: Optional[int] = Field(None, ge=1, description="Maximum number of lines to read.")
    start_line: Optional[int] = Field(None, ge=1, description="1-indexed line to start reading from.")
    end_line: Optional[int] = Field(None, ge=1, description="1-indexed line to stop reading at (inclusive).")

    @field_validator("encoding")
    @classmethod
    def validate_encoding(cls, v: str) -> str:
        if v not in _ALLOWED_ENCODINGS:
            raise ValueError(f"Unsupported encoding '{v}'. Must be one of: {', '.join(sorted(_ALLOWED_ENCODINGS))}")
        return v

    @model_validator(mode="after")
    def validate_line_range(self) -> "ReadFileArgs":
        if self.start_line and self.end_line and self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line.")
        return self


class EditFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to the file to edit.")
    old_string: str = Field(..., min_length=1, description="Exact text to find. Must match whitespace, indentation, and newlines perfectly.")
    new_string: str = Field(..., description="Replacement text. Pass an empty string to delete old_string.")
    encoding: str = Field("utf-8", description="File encoding. One of: utf-8, utf-16, latin-1, ascii, utf-8-sig.")
    replace_all: bool = Field(False, description="If True, replace every occurrence. If False (default), fail when old_string appears more than once.")

    @field_validator("encoding")
    @classmethod
    def validate_encoding(cls, v: str) -> str:
        if v not in _ALLOWED_ENCODINGS:
            raise ValueError(f"Unsupported encoding '{v}'. Must be one of: {', '.join(sorted(_ALLOWED_ENCODINGS))}")
        return v


class SearchFileArgs(BaseModel):
    file_path: str = Field(..., description="Path to the file to search.")
    pattern: str = Field(..., min_length=1, description="Regex pattern or literal string to search for.")
    mode: Literal["regex", "literal"] = Field("regex", description="'regex' for regular expressions, 'literal' for plain-text matching.")
    case_sensitive: bool = Field(True, description="Whether matching is case-sensitive.")
    context_lines: int = Field(0, ge=0, le=50, description="Lines to show before and after each match (like grep -C).")
    max_results: int = Field(100, ge=1, le=_MAX_SEARCH_RESULTS, description=f"Max matches to return (1–{_MAX_SEARCH_RESULTS}).")
    encoding: str = Field("utf-8", description="File encoding. One of: utf-8, utf-16, latin-1, ascii, utf-8-sig.")

    @field_validator("encoding")
    @classmethod
    def validate_encoding(cls, v: str) -> str:
        if v not in _ALLOWED_ENCODINGS:
            raise ValueError(f"Unsupported encoding '{v}'. Must be one of: {', '.join(sorted(_ALLOWED_ENCODINGS))}")
        return v


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool("read_file", args_schema=ReadFileArgs)
def read_file(
    file_path: str,
    encoding: str = "utf-8",
    max_lines: Optional[int] = None,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> Dict[str, Any]:
    """Read content from a text-based file.

    Supports optional line-range slicing via start_line/end_line and a hard 50 MB
    size cap to prevent memory issues. For very large files use start_line/end_line
    to read sections, or use search_file to find specific content.
    """
    path, err = _resolve_text_file(file_path)
    if err:
        return {"success": False, "content": None, "error": err, "file_path": file_path}

    file_size = path.stat().st_size
    if file_size > _MAX_READ_BYTES:
        return {
            "success": False,
            "content": None,
            "error": (
                f"File is too large to read fully ({file_size / 1e6:.1f} MB, max {_MAX_READ_BYTES // 1_000_000} MB). "
                "Use start_line/end_line to read a specific range, or use search_file."
            ),
            "file_path": str(path),
            "file_size": file_size,
        }

    try:
        with open(path, "r", encoding=encoding, errors="replace") as f:
            all_lines = f.readlines()

        total_lines = len(all_lines)
        s = (start_line - 1) if start_line else 0
        e = end_line if end_line else total_lines
        selected = all_lines[s:e]
        if max_lines is not None:
            selected = selected[:max_lines]

        return {
            "success": True,
            "content": "".join(selected),
            "lines": len(selected),
            "total_lines": total_lines,
            "file_path": str(path),
            "file_size": file_size,
            "encoding": encoding,
            "error": None,
        }

    except Exception as e:
        return {"success": False, "content": None, "error": f"Error reading file: {e}", "file_path": str(path)}


@tool("edit_file", args_schema=EditFileArgs)
def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    encoding: str = "utf-8",
    replace_all: bool = False,
) -> Dict[str, Any]:
    """Make targeted edits to a text file by replacing an exact string match.

    Finds old_string in the file and replaces it with new_string. By default refuses
    to edit if old_string appears more than once (ambiguous); set replace_all=True to
    replace every occurrence. The match must be exact — whitespace, indentation, and
    line endings must match perfectly. Writes atomically via a temp file so the
    original is never corrupted on a crash.
    """
    path, err = _resolve_text_file(file_path)
    if err:
        return {"success": False, "file_path": file_path, "replacements_made": 0, "error": err}

    file_size = path.stat().st_size
    if file_size > _MAX_WRITE_BYTES:
        return {
            "success": False,
            "file_path": str(path),
            "replacements_made": 0,
            "error": f"File is too large ({file_size / 1e6:.1f} MB, max {_MAX_WRITE_BYTES // 1_000_000} MB).",
        }

    try:
        with open(path, "r", encoding=encoding, errors="replace") as f:
            content = f.read()
    except Exception as e:
        return {"success": False, "file_path": str(path), "replacements_made": 0, "error": f"Error reading file: {e}"}

    # Guard against the resulting file growing too large
    delta = len(new_string.encode(encoding, errors="replace")) - len(old_string.encode(encoding, errors="replace"))
    if file_size + delta > _MAX_WRITE_BYTES:
        return {
            "success": False,
            "file_path": str(path),
            "replacements_made": 0,
            "error": f"Resulting file would be too large ({(file_size + delta) / 1e6:.1f} MB, max {_MAX_WRITE_BYTES // 1_000_000} MB).",
        }

    count = content.count(old_string)
    if count == 0:
        return {
            "success": False,
            "file_path": str(path),
            "replacements_made": 0,
            "error": (
                "old_string was not found in the file. "
                "Ensure whitespace, indentation, and line endings match exactly."
            ),
        }
    if count > 1 and not replace_all:
        return {
            "success": False,
            "file_path": str(path),
            "replacements_made": 0,
            "error": (
                f"old_string appears {count} times. "
                "Add more surrounding context to make it unique, or set replace_all=True."
            ),
        }

    updated = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding=encoding) as f:
            f.write(updated)
        tmp_path.replace(path)
    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        return {"success": False, "file_path": str(path), "replacements_made": 0, "error": f"Error writing file: {e}"}

    return {
        "success": True,
        "file_path": str(path),
        "replacements_made": count if replace_all else 1,
        "error": None,
    }


@tool("search_file", args_schema=SearchFileArgs)
def search_file(
    file_path: str,
    pattern: str,
    mode: str = "regex",
    case_sensitive: bool = True,
    context_lines: int = 0,
    max_results: int = 100,
    encoding: str = "utf-8",
) -> Dict[str, Any]:
    """Search a text file for lines matching a pattern or literal string.

    Streams the file line-by-line so memory usage stays flat regardless of file size
    (up to the 100 MB safety cap). Use mode='literal' for plain-text searches and
    mode='regex' for full regular expression power. context_lines works like grep -C.
    """
    path, err = _resolve_text_file(file_path)
    if err:
        return {"success": False, "matches": [], "total_matches": 0, "error": err, "file_path": file_path}

    file_size = path.stat().st_size
    if file_size > _MAX_SEARCH_BYTES:
        return {
            "success": False,
            "matches": [],
            "total_matches": 0,
            "error": f"File is too large to search ({file_size / 1e6:.1f} MB, max {_MAX_SEARCH_BYTES // 1_000_000} MB).",
            "file_path": str(path),
        }

    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        compiled = re.compile(re.escape(pattern) if mode == "literal" else pattern, flags)
    except re.error as e:
        return {"success": False, "matches": [], "total_matches": 0, "error": f"Invalid regex pattern: {e}", "file_path": str(path)}

    try:
        all_lines: List[str] = []
        with open(path, "r", encoding=encoding, errors="replace") as f:
            for raw in f:
                if len(raw) > _MAX_LINE_LENGTH:
                    all_lines.append(raw[:_MAX_LINE_LENGTH] + "...[line truncated]\n")
                else:
                    all_lines.append(raw)

        match_indices = [i for i, line in enumerate(all_lines) if compiled.search(line)]
        total_matches = len(match_indices)
        truncated = total_matches > max_results

        matches = []
        for idx in match_indices[:max_results]:
            matches.append({
                "line_number": idx + 1,
                "line": all_lines[idx].rstrip("\n"),
                "context_before": [all_lines[j].rstrip("\n") for j in range(max(0, idx - context_lines), idx)],
                "context_after": [all_lines[j].rstrip("\n") for j in range(idx + 1, min(len(all_lines), idx + context_lines + 1))],
            })

        return {
            "success": True,
            "matches": matches,
            "total_matches": total_matches,
            "truncated": truncated,
            "truncated_at": max_results if truncated else None,
            "file_path": str(path),
            "file_size": file_size,
            "error": None,
        }

    except Exception as e:
        return {"success": False, "matches": [], "total_matches": 0, "error": f"Error searching file: {e}", "file_path": str(path)}


if __name__ == "__main__":
    test_file = "main.py"

    print("Reading file:")
    print(read_file.invoke({"file_path": test_file}))

    print("\nSearching file:")
    print(search_file.invoke({"file_path": test_file, "pattern": "test", "mode": "literal", "context_lines": 2}))
