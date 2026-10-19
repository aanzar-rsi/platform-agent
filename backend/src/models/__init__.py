
"""Top-level package for models.

This package automatically imports submodules in the models package so they are
available as attributes of the package (e.g. models.my_model).
"""

from __future__ import annotations

__all__: list[str]

try:
	# Prefer explicit version if provided by a _version module
	from ._version import __version__  # type: ignore
except Exception:
	__version__ = "0.0.0"

import pkgutil
import importlib

# Discover and import all submodules in this package, expose their names in
# __all__ so `from models import *` will import them.
_names: list[str] = []
for _finder, _name, _ispkg in pkgutil.iter_modules(__path__):
	try:
		importlib.import_module(f"{__name__}._{_name}" if _name.startswith("_") else f"{__name__}.{_name}")
	except Exception:
		# Silently skip import errors to avoid failing package import.
		pass
	else:
		_names.append(_name)

__all__ = sorted(_names)
