"""
Internal tool for getting comprehensive system information.
"""

import os
import platform
from typing import Dict, Any
from langchain_core.tools import tool


@tool("system_info")
def system_info() -> Dict[str, Any]:
    """Return comprehensive information about the host system.

    Covers OS, CPU, memory, disk, Python runtime, and network hostname.
    Memory and disk stats require psutil; if it is not installed those
    sections are omitted rather than crashing.
    """
    result: Dict[str, Any] = {
        "success": True,
        "error": None,
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": os.sys.executable,
        },
        "cpu": {
            "processor": platform.processor(),
        },
    }

    try:
        import psutil

        # CPU
        result["cpu"].update({
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "usage_percent": psutil.cpu_percent(interval=0.1),
        })

        # Memory
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        result["memory"] = {
            "total_bytes": mem.total,
            "available_bytes": mem.available,
            "used_bytes": mem.used,
            "used_percent": mem.percent,
            "swap_total_bytes": swap.total,
            "swap_used_bytes": swap.used,
            "swap_used_percent": swap.percent,
        }

        # Disk (root / C:\ depending on OS)
        root = "C:\\" if platform.system() == "Windows" else "/"
        disk = psutil.disk_usage(root)
        result["disk"] = {
            "path": root,
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
            "used_percent": disk.percent,
        }

        # Network interfaces (names + addresses only — no traffic stats)
        addrs = psutil.net_if_addrs()
        result["network"] = {
            iface: [{"family": str(a.family), "address": a.address} for a in addr_list]
            for iface, addr_list in addrs.items()
        }

    except ImportError:
        result["error"] = "psutil not installed — CPU usage, memory, disk, and network info unavailable. Install with: pip install psutil"

    except Exception as e:
        result["error"] = f"Error collecting system info: {e}"

    return result


if __name__ == "__main__":
    import json
    print(json.dumps(system_info.invoke({}), indent=2))