"""
Internal tools package for the agent.
"""

from .now import get_current_datetime_info
from .sys_info import system_info
from .file_io import read_file, edit_file, search_file
from .decomposer import decompose_query
from .web_search import web_search
from .executor import (
    execute_bash,
    execute_powershell,
    execute_python_script,
)

INTERNAL_TOOLS = [
    # Time
    get_current_datetime_info,
    # System info
    system_info,
    # File I/O
    read_file,
    edit_file,
    search_file,
    # Web
    web_search,
    # Query analysis
    decompose_query,
    # Execution
    execute_bash,
    execute_powershell,
    execute_python_script,
]

INTERNAL_TOOL_NAMES = [
    t.name if hasattr(t, "name") else t.__name__
    for t in INTERNAL_TOOLS
]

TIME_TOOLS         = [get_current_datetime_info]
SYSTEM_TOOLS       = [system_info]
FILE_IO_TOOLS      = [read_file, edit_file, search_file]
WEB_TOOLS          = [web_search]
QUERY_TOOLS        = [decompose_query]
EXECUTION_TOOLS    = [execute_bash, execute_powershell, execute_python_script]

__all__ = [
    # Lists
    "INTERNAL_TOOLS",
    "INTERNAL_TOOL_NAMES",
    "TIME_TOOLS",
    "SYSTEM_TOOLS",
    "FILE_IO_TOOLS",
    "WEB_TOOLS",
    "QUERY_TOOLS",
    "EXECUTION_TOOLS",
    # Individual tools
    "get_current_datetime_info",
    "system_info",
    "read_file",
    "edit_file",
    "search_file",
    "web_search",
    "decompose_query",
    "execute_bash",
    "execute_powershell",
    "execute_python_script",
]
